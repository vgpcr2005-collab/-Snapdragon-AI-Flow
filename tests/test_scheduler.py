from snapdragon_aiflow.models import ModelProfile, SystemMetrics, Workload
from snapdragon_aiflow.scheduler import AIScheduler
from snapdragon_aiflow.simulator import ScenarioSimulator


def test_predicts_object_detection_for_npu_execution():
    metrics = SystemMetrics(cpu=70, gpu=58, npu=87, battery=42, temperature=61)
    model = ModelProfile(name="yolo", complexity="high", latency_budget_ms=120, workload_type="vision")
    workload = Workload(name="object-detection", model=model, priority=0.9)

    scheduler = AIScheduler(metrics)
    selected = scheduler.schedule(workload, mode="balanced")

    assert selected == "npu"
    prediction = scheduler.predict_workload(workload)
    assert prediction["compute_intensity"] == "HIGH"
    assert prediction["npu_suitability"] == "VERY HIGH"


def test_battery_saver_prefers_energy_efficient_path():
    metrics = SystemMetrics(cpu=72, gpu=65, npu=80, battery=22, temperature=58)
    model = ModelProfile(name="speech", complexity="medium", latency_budget_ms=260, workload_type="audio")
    workload = Workload(name="speech-recognition", model=model, priority=0.8)

    scheduler = AIScheduler(metrics)
    selected = scheduler.schedule(workload, mode="battery_saver")

    assert selected == "npu"


def test_simulator_recommends_npu_for_cpu_heavy_low_battery_scenario():
    scenario = {
        "battery": 22,
        "cpu_load": 82,
        "gpu_load": 61,
        "temperature": 67,
        "workload": "object-detection",
        "mode": "balanced",
    }

    recommendation = ScenarioSimulator().recommend(scenario)

    assert recommendation["recommended_target"] == "npu"
    assert "Battery" in recommendation["reason"]
    assert "CPU" in recommendation["reason"]


def test_read_system_metrics_uses_env_overrides_for_live_demo_values(monkeypatch):
    monkeypatch.setenv("AI_FLOW_CPU", "9")
    monkeypatch.setenv("AI_FLOW_BATTERY", "71")
    monkeypatch.setenv("AI_FLOW_TEMP", "43")

    monkeypatch.setattr("main.platform.system", lambda: "Windows")
    monkeypatch.setattr("main.read_windows_battery", lambda: None)

    metrics = __import__("main").read_system_metrics()

    assert metrics.cpu == 9
    assert metrics.battery == 71
    assert metrics.temperature == 43
