import json
import os
import platform
import subprocess
import time

import psutil
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from snapdragon_aiflow.models import ModelProfile, SystemMetrics, Workload
from snapdragon_aiflow.monitor import SystemMonitor
from snapdragon_aiflow.scheduler import AIScheduler

app = FastAPI(title="Snapdragon AIFlow")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

WORKLOADS = {
    "vision": {"label": "Vision Analysis", "type": "vision", "complexity": "high", "latency": 150},
    "speech": {"label": "Speech Recognition", "type": "audio", "complexity": "medium", "latency": 220},
    "text": {"label": "NLP / Text", "type": "text", "complexity": "medium", "latency": 260},
    "object": {"label": "Object Detection", "type": "vision", "complexity": "high", "latency": 120},
    "summarization": {"label": "Document Summarization", "type": "text", "complexity": "low", "latency": 420},
}

_battery_cache = {"value": None, "expires_at": 0.0}


def read_windows_battery():
    now = time.monotonic()
    if now < _battery_cache["expires_at"]:
        return _battery_cache["value"]
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -ClassName Win32_Battery | Select-Object -ExpandProperty EstimatedChargeRemaining -ErrorAction SilentlyContinue | Select-Object -First 1)"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        cleaned = out.strip()
        if cleaned and cleaned.isdigit():
            value = max(0, min(100, int(cleaned)))
            _battery_cache.update(value=value, expires_at=now + 30)
            return value
    except Exception:
        pass
    _battery_cache.update(value=None, expires_at=now + 30)
    return None


def read_windows_cpu_usage():
    try:
        return int(psutil.cpu_percent(interval=0.1))
    except Exception:
        return 0


def read_temperature():
    try:
        sensors = psutil.sensors_temperatures()
        readings = [entry.current for values in sensors.values() for entry in values if entry.current is not None]
        if readings:
            return int(round(max(readings))), "sensor"
    except (AttributeError, OSError):
        pass
    return None, "estimated"


def read_system_metrics_details():
    cpu_override = os.environ.get("AI_FLOW_CPU")
    battery_override = os.environ.get("AI_FLOW_BATTERY")
    temp_override = os.environ.get("AI_FLOW_TEMP")

    cpu = int(cpu_override) if cpu_override and cpu_override.isdigit() else int(psutil.cpu_percent(interval=0.1))

    if platform.system() == "Windows":
        battery = read_windows_battery()
    else:
        battery = psutil.sensors_battery().percent if psutil.sensors_battery() else None

    if battery_override and battery_override.isdigit():
        battery = int(battery_override)

    if temp_override and temp_override.isdigit():
        temperature, temperature_source = int(temp_override), "override"
    else:
        temperature, temperature_source = read_temperature()
        if temperature is None:
            temperature = max(30, min(90, int(cpu * 0.6) + 30))

    gpu = 0
    npu = 0

    if battery is None:
        battery = 68

    metrics = SystemMetrics(cpu=int(cpu), gpu=gpu, npu=npu, battery=int(battery), temperature=int(temperature))
    return metrics, temperature_source


def read_system_metrics():
    metrics, _ = read_system_metrics_details()
    return metrics


def build_workload(name: str = "Vision Analysis", workload_type: str = "vision", complexity: str = "high", latency: int = 150):
    return Workload(
        name=name,
        model=ModelProfile(
            name=workload_type,
            complexity=complexity,
            latency_budget_ms=latency,
            workload_type=workload_type,
        ),
        priority=0.92,
    )


def make_response(workload_key: str = "vision", mode: str = "balanced", source: str = "live"):
    workload_config = WORKLOADS.get(workload_key, WORKLOADS["vision"])
    metrics, temperature_source = read_system_metrics_details()
    if source == "simulation":
        metrics = SystemMetrics(cpu=24, gpu=38, npu=18, battery=71, temperature=43)
        temperature_source = "simulation"
    workload = build_workload(
        name=workload_config["label"],
        workload_type=workload_config["type"],
        complexity=workload_config["complexity"],
        latency=workload_config["latency"],
    )
    scheduler = AIScheduler(metrics)
    target = scheduler.schedule(workload, mode=mode)
    decision = scheduler.explain_decision(workload, mode=mode)
    health = SystemMonitor().summarize(metrics)
    runtime_status = "simulation profile" if source == "simulation" else "host telemetry only"
    return {
        "cpu": metrics.cpu,
        "gpu": metrics.gpu if source == "simulation" or metrics.gpu > 0 else None,
        "npu": metrics.npu if source == "simulation" or metrics.npu > 0 else None,
        "battery": metrics.battery,
        "temperature": metrics.temperature,
        "workload_name": workload.name,
        "cpu_score": decision["scores"].get("cpu", 0),
        "gpu_score": decision["scores"].get("gpu", 0),
        "npu_score": decision["scores"].get("npu", 0),
        "recommended_target": target.upper(),
        "reason": decision["reasons"][0],
        "status": f"{target.upper()} recommended/selected by scheduler",
        "mode": mode,
        "workload": workload_key,
        "source": source,
        "thermal_state": health["thermal_state"],
        "power_state": health["power_state"],
        "available_accelerators": health["available_accelerators"],
        "runtime": "Qualcomm AI Engine / QNN",
        "runtime_status": runtime_status,
        "npu_telemetry": "available" if metrics.npu > 0 else "not exposed by host",
        "temperature_source": temperature_source,
        "gpu_telemetry": "available" if metrics.gpu > 0 else "not exposed by host",
    }


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    result = make_response()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Snapdragon AIFlow",
            **result,
            "workloads": WORKLOADS,
            "selected_mode": "balanced",
            "selected_workload": "vision",
        },
    )


@app.get("/api/evaluate")
def evaluate(
    mode: str = Query("balanced"),
    workload: str = Query("vision"),
    source: str = Query("live"),
):
    if workload not in WORKLOADS:
        valid_workloads = ", ".join(sorted(WORKLOADS))
        raise HTTPException(status_code=400, detail=f"Unknown workload '{workload}'. Valid workloads: {valid_workloads}")
    result = make_response(workload_key=workload, mode=mode, source=source)
    return JSONResponse(content=result)


@app.get("/health")
def health():
    return {"status": "ok", "service": "snapdragon-aiflow"}
