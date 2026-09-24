from __future__ import annotations

from .analyzer import WorkloadAnalyzer
from .dashboard import Dashboard
from .models import ModelProfile, SystemMetrics, Workload
from .monitor import SystemMonitor
from .scheduler import AIScheduler


class AIFlowApp:
    def __init__(self, system_metrics: SystemMetrics):
        self.system_metrics = system_metrics
        self.monitor = SystemMonitor()
        self.analyzer = WorkloadAnalyzer()
        self.scheduler = AIScheduler(system_metrics)
        self.dashboard = Dashboard()

    def process(self, workload: Workload, mode: str = "balanced") -> dict:
        analysis = self.analyzer.analyze(workload)
        metrics = self.monitor.summarize(self.system_metrics)
        target = self.scheduler.schedule(workload, mode=mode)
        explanation = self.scheduler.explain_decision(workload, mode=mode)
        return self.dashboard.render(
            workload.name,
            target,
            metrics,
            analysis,
            scores=explanation["scores"],
            reasons=explanation["reasons"],
        )

    def print_dashboard(self, workload: Workload, mode: str = "balanced") -> None:
        result = self.process(workload, mode=mode)
        print("\nAIFlow demo executed")
        print(f"Workload: {result['workload']}")
        print(f"Selected target: {result['selected_target']}")
        print(f"Status: {result['status']}")
        print(f"CPU Score: {result['scores'].get('cpu', 0)}")
        print(f"GPU Score: {result['scores'].get('gpu', 0)}")
        print(f"NPU Score: {result['scores'].get('npu', 0)}")
        print(f"Reason: {result['panel']['reason']}")


def demo():
    system_metrics = SystemMetrics(cpu=82, gpu=90, npu=72, battery=61, temperature=53)
    workload = Workload(
        name="vision-analysis",
        model=ModelProfile(name="vision-core", complexity="high", latency_budget_ms=150, workload_type="vision"),
        priority=0.92,
    )

    app = AIFlowApp(system_metrics)
    app.print_dashboard(workload, mode="balanced")


if __name__ == "__main__":
    demo()
