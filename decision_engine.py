from __future__ import annotations


class AIDecisionEngine:
    """Scores each accelerator using workload suitability and runtime conditions."""

    def score(self, workload: object, system_metrics: object, mode: str = "balanced") -> dict:
        workload_profile = workload.model
        cpu_score = 30
        gpu_score = 30
        npu_score = 25

        if workload_profile.workload_type in {"vision", "multimodal"}:
            gpu_score += 24
            npu_score += 28
        if workload_profile.workload_type in {"audio", "sensor", "edge"}:
            npu_score += 22
        if workload_profile.complexity == "high":
            gpu_score += 16
            npu_score += 18
        if workload_profile.complexity == "low":
            cpu_score += 18

        cpu_score += system_metrics.cpu * 0.2
        gpu_score += system_metrics.gpu * 0.25
        npu_score += system_metrics.npu * 0.3

        battery_factor = max(0, 100 - system_metrics.battery)
        thermal_factor = max(0, system_metrics.temperature - 40)
        latency_factor = 100 - workload_profile.latency_budget_ms

        if mode == "performance":
            cpu_score += 10
            gpu_score += 15
            npu_score += 18
            battery_factor *= 0.5
            thermal_factor *= 0.7
        elif mode == "battery_saver":
            cpu_score -= 6
            gpu_score -= 8
            npu_score += 10
            battery_factor *= 1.5
            thermal_factor *= 0.5
        else:
            cpu_score += 4
            gpu_score += 8
            npu_score += 12

        cpu_score += max(0, 40 - battery_factor * 0.25)
        gpu_score -= thermal_factor * 0.2
        npu_score += max(0, 30 - battery_factor * 0.2)
        npu_score -= thermal_factor * 0.15
        cpu_score -= max(0, system_metrics.temperature - 75) * 0.2

        resource_contention = (system_metrics.cpu * 0.12) + (system_metrics.gpu * 0.1) + (system_metrics.npu * 0.08)
        cpu_score -= resource_contention * 0.3
        gpu_score -= resource_contention * 0.45
        npu_score -= resource_contention * 0.2

        if system_metrics.battery < 25:
            npu_score += 12
            gpu_score -= 6
        if system_metrics.temperature > 80:
            gpu_score -= 18
            npu_score -= 6

        scores = {"cpu": round(cpu_score), "gpu": round(gpu_score), "npu": round(npu_score)}
        best_target = max(scores, key=scores.get)

        return {
            "scores": scores,
            "best_target": best_target,
            "mode": mode,
            "latency_factor": latency_factor,
            "battery_factor": battery_factor,
            "thermal_factor": thermal_factor,
        }
