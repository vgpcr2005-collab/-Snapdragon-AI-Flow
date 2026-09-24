from __future__ import annotations


class ScenarioSimulator:
    """Compares a scenario against the scheduler to produce a recommendation."""

    def recommend(self, scenario: dict) -> dict:
        battery = scenario.get("battery", 50)
        cpu_load = scenario.get("cpu_load", 50)
        gpu_load = scenario.get("gpu_load", 50)
        temperature = scenario.get("temperature", 45)
        workload = scenario.get("workload", "object-detection")
        mode = scenario.get("mode", "balanced")

        score_cpu = 35 + (100 - battery) * 0.30 + cpu_load * 0.25 - temperature * 0.15
        score_gpu = 40 + (100 - gpu_load) * 0.20 + (60 - abs(temperature - 60)) * 0.10
        score_npu = 48 + (40 - battery) * 0.35 + (max(0, 100 - cpu_load)) * 0.18 - temperature * 0.12

        if "vision" in workload or "object" in workload or "image" in workload:
            score_npu += 25
            score_gpu += 12
        if "speech" in workload or "audio" in workload:
            score_npu += 18
        if mode == "battery_saver":
            score_npu += 8
            score_gpu -= 3
        elif mode == "performance":
            score_gpu += 10
            score_npu += 6

        scores = {"cpu": round(score_cpu), "gpu": round(score_gpu), "npu": round(score_npu)}
        recommended_target = max(scores, key=scores.get)
        reason = (
            "CPU heavily loaded; Battery relatively low; AI workload is NPU-compatible; "
            "NPU has available capacity."
        )

        return {
            "recommended_target": recommended_target,
            "reason": reason,
            "scores": scores,
            "scenario": {
                "battery": battery,
                "cpu_load": cpu_load,
                "gpu_load": gpu_load,
                "temperature": temperature,
                "workload": workload,
                "mode": mode,
            },
        }
