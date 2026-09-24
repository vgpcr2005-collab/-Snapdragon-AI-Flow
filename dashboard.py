from __future__ import annotations


class Dashboard:
    """Builds a user-facing scheduler summary for the dashboard experience."""

    def render(self, workload_name: str, target: str, metrics: dict, analysis: dict, scores: dict | None = None, reasons: list[str] | None = None) -> dict:
        scores = scores or {"cpu": 0, "gpu": 0, "npu": 0}
        reasons = reasons or ["Workload matches the selected accelerator profile."]

        return {
            "workload": workload_name,
            "selected_target": target,
            "metrics": metrics,
            "analysis": analysis,
            "scores": scores,
            "reasons": reasons,
            "status": f"{target.upper()} recommended/selected by scheduler",
            "power_efficiency": "optimized" if target == "npu" else "balanced" if target == "gpu" else "fallback",
            "panel": {
                "title": "Snapdragon AIFlow",
                "subtitle": "Intelligent AI Workload Optimization",
                "cpu_score": scores.get("cpu", 0),
                "gpu_score": scores.get("gpu", 0),
                "npu_score": scores.get("npu", 0),
                "recommended_target": target.upper(),
                "reason": reasons[0] if reasons else "Workload matches the selected accelerator profile.",
            },
        }
