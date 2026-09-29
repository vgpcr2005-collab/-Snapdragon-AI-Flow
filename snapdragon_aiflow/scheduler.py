from __future__ import annotations

from dataclasses import dataclass

from .classifier import AIWorkloadClassifier
from .decision_engine import AIDecisionEngine
from .models import SystemMetrics, Workload


@dataclass
class Candidate:
    name: str
    score: float


class AIScheduler:
    def __init__(self, system_metrics: SystemMetrics):
        self.system_metrics = system_metrics
        self.classifier = AIWorkloadClassifier()
        self.decision_engine = AIDecisionEngine()

    def predict_workload(self, workload: Workload) -> dict:
        return self.classifier.predict(workload)

    def explain_decision(self, workload: Workload, mode: str = "balanced") -> dict:
        decision = self.decision_engine.score(workload, self.system_metrics, mode)
        target = decision["best_target"]
        scores = decision["scores"]
        reason = [
            f"{target.upper()} selected because it has the highest decision score ({scores[target]}).",
            f"Workload suitability contributes to the {target} path.",
            f"Battery factor: {decision['battery_factor']:.1f}",
            f"Thermal factor: {decision['thermal_factor']:.1f}",
            f"Latency factor: {decision['latency_factor']:.1f}",
        ]
        return {"target": target, "scores": scores, "reasons": reason}

    def schedule(self, workload: Workload, mode: str = "balanced") -> str:
        decision = self.decision_engine.score(workload, self.system_metrics, mode)
        return decision["best_target"]

    def _score_gpu(self, workload: Workload) -> float:
        metrics = self.system_metrics
        score = 0.0
        if metrics.gpu > 0:
            score += metrics.gpu * 0.5
        if workload.model.complexity == "high":
            score += 35
        if workload.model.workload_type in {"vision", "multimodal"}:
            score += 25
        if workload.model.latency_budget_ms <= 200:
            score += 20
        if metrics.temperature is not None and metrics.temperature > 80:
            score -= 40
        if metrics.battery is not None and metrics.battery < 15:
            score -= 20
        return score

    def _score_npu(self, workload: Workload) -> float:
        metrics = self.system_metrics
        score = 0.0
        if metrics.npu > 0:
            score += metrics.npu * 0.5
        if workload.model.complexity in {"medium", "low"}:
            score += 30
        if workload.model.workload_type in {"audio", "sensor", "edge"}:
            score += 30
        if workload.model.latency_budget_ms <= 400:
            score += 10
        if metrics.temperature is not None and metrics.temperature > 75:
            score -= 15
        if metrics.battery is not None and metrics.battery < 30:
            score += 15
        return score

    def _score_cpu(self, workload: Workload) -> float:
        metrics = self.system_metrics
        score = 10.0
        if metrics.cpu > 0:
            score += metrics.cpu * 0.3
        if workload.model.complexity == "low":
            score += 15
        if workload.model.workload_type == "text":
            score += 10
        if metrics.temperature is not None and metrics.temperature > 90:
            score -= 35
        if metrics.battery is not None and metrics.battery < 20:
            score -= 10
        return score
