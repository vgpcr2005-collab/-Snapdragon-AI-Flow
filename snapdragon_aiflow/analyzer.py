from __future__ import annotations

from .models import Workload


class WorkloadAnalyzer:
    """Analyzes workload characteristics that influence target selection."""

    def analyze(self, workload: Workload) -> dict:
        model = workload.model
        complexity_weight = {"low": 1, "medium": 2, "high": 3}.get(model.complexity.lower(), 1)
        latency_pressure = 1 if model.latency_budget_ms <= 200 else 2 if model.latency_budget_ms <= 400 else 3
        priority_score = min(max(workload.priority, 0.0), 1.0)

        return {
            "name": workload.name,
            "model": model.name,
            "complexity": model.complexity,
            "complexity_weight": complexity_weight,
            "latency_budget_ms": model.latency_budget_ms,
            "latency_pressure": latency_pressure,
            "workload_type": model.workload_type,
            "priority": priority_score,
            "estimated_load": round((complexity_weight * 0.45) + (latency_pressure * 0.35) + (priority_score * 0.20), 2),
        }
