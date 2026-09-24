from __future__ import annotations

from .models import SystemMetrics


class SystemMonitor:
    """Collects health and performance metrics used by the scheduler."""

    def summarize(self, metrics: SystemMetrics) -> dict:
        return {
            "cpu": metrics.cpu,
            "gpu": metrics.gpu,
            "npu": metrics.npu,
            "battery": metrics.battery,
            "temperature": metrics.temperature,
            "thermal_state": "hot" if metrics.temperature > 80 else "warm" if metrics.temperature > 60 else "normal",
            "power_state": "low" if metrics.battery < 25 else "balanced" if metrics.battery < 70 else "high",
            "available_accelerators": [
                name for name, value in {"gpu": metrics.gpu, "npu": metrics.npu}.items() if value > 0
            ],
        }
