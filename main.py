import os
import platform

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

def read_windows_battery():
    try:
        battery = psutil.sensors_battery()
        if battery is not None and battery.percent is not None:
            return round(battery.percent)
    except Exception:
        pass
    return None


def read_windows_cpu_usage():
    try:
        return round(psutil.cpu_percent(interval=1.0))
    except Exception:
        return 0


def read_temperature():
    try:
        sensors = psutil.sensors_temperatures()
        readings = [
            entry.current
            for values in sensors.values()
            for entry in values
            if entry.current is not None and 0 <= entry.current <= 125
        ]
        if readings:
            return int(round(max(readings))), "sensor"
    except (AttributeError, OSError):
        pass
    return None, "unavailable"


def read_system_metrics_details():
    cpu_override = os.environ.get("AI_FLOW_CPU")
    battery_override = os.environ.get("AI_FLOW_BATTERY")
    temp_override = os.environ.get("AI_FLOW_TEMP")

    cpu = int(cpu_override) if cpu_override and cpu_override.isdigit() else read_windows_cpu_usage()

    if platform.system() == "Windows":
        battery = read_windows_battery()
    else:
        battery_reading = psutil.sensors_battery()
        battery = round(battery_reading.percent) if battery_reading and battery_reading.percent is not None else None
    battery_source = "sensor" if battery is not None else "unavailable"

    if battery_override and battery_override.isdigit():
        battery = max(0, min(100, int(battery_override)))
        battery_source = "override"

    temperature_override = int(temp_override) if temp_override and temp_override.isdigit() else None
    if temperature_override is not None and 0 <= temperature_override <= 125:
        temperature, temperature_source = temperature_override, "override"
    else:
        temperature, temperature_source = read_temperature()

    gpu = 0
    npu = 0

    metrics = SystemMetrics(
        cpu=max(0, min(100, int(cpu))),
        gpu=gpu,
        npu=npu,
        battery=max(0, min(100, int(battery))) if battery is not None else None,
        temperature=int(temperature) if temperature is not None else None,
    )
    return metrics, temperature_source, battery_source


def read_system_metrics():
    metrics, _, _ = read_system_metrics_details()
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


def make_response(
    workload_key: str = "vision",
    mode: str = "balanced",
    source: str = "live",
    client_battery: int | None = None,
    use_client_battery: bool = False,
):
    workload_config = WORKLOADS.get(workload_key, WORKLOADS["vision"])
    metrics, temperature_source, battery_source = read_system_metrics_details()
    if source == "simulation":
        metrics = SystemMetrics(cpu=24, gpu=38, npu=18, battery=71, temperature=43)
        temperature_source = "simulation"
        battery_source = "simulation"
    elif use_client_battery:
        metrics.battery = client_battery
        battery_source = "browser" if client_battery is not None else "unavailable"
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
    alerts = []
    if metrics.temperature is not None and metrics.temperature > 80:
        alerts.append({
            "type": "thermal",
            "title": "High system temperature",
            "message": f"Temperature is {metrics.temperature}°C. Pause intensive work, close demanding apps, and let the device cool in a well-ventilated area.",
        })
    if metrics.cpu >= 90:
        alerts.append({
            "type": "overload",
            "title": "CPU usage is very high",
            "message": f"CPU usage is {metrics.cpu}%. Close apps or background tasks you are not using, then check whether usage drops.",
        })
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
        "telemetry_scope": "simulation profile" if source == "simulation" else "app server",
        "npu_telemetry": "available" if metrics.npu > 0 else "not exposed by host",
        "battery_source": battery_source,
        "temperature_source": temperature_source,
        "gpu_telemetry": "available" if metrics.gpu > 0 else "not exposed by host",
        "alerts": alerts,
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
    client_battery: int | None = Query(None, ge=0, le=100),
    use_client_battery: bool = Query(False),
):
    if workload not in WORKLOADS:
        valid_workloads = ", ".join(sorted(WORKLOADS))
        raise HTTPException(status_code=400, detail=f"Unknown workload '{workload}'. Valid workloads: {valid_workloads}")
    result = make_response(
        workload_key=workload,
        mode=mode,
        source=source,
        client_battery=client_battery,
        use_client_battery=use_client_battery,
    )
    return JSONResponse(content=result)


@app.get("/health")
def health():
    return {"status": "ok", "service": "snapdragon-aiflow"}
