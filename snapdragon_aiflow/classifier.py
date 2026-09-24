from __future__ import annotations

from typing import Dict


class AIWorkloadClassifier:
    """Produces AI-driven workload characteristics from a model and workload description."""

    def predict(self, workload: object) -> Dict[str, str]:
        model = workload.model
        workload_type = model.workload_type.lower()
        complexity = model.complexity.lower()

        compute_intensity = "HIGH" if complexity in {"high", "complex"} or workload_type in {"vision", "multimodal"} else "MEDIUM" if complexity == "medium" else "LOW"
        memory_requirements = "HIGH" if workload_type in {"vision", "multimodal", "audio"} else "MEDIUM" if complexity == "medium" else "LOW"
        latency_sensitivity = "HIGH" if model.latency_budget_ms <= 200 else "MEDIUM" if model.latency_budget_ms <= 500 else "LOW"
        power_sensitivity = "HIGH" if workload_type in {"audio", "vision"} else "MEDIUM" if complexity == "medium" else "LOW"
        parallelism = "HIGH" if workload_type in {"vision", "multimodal"} else "MEDIUM" if complexity == "medium" else "LOW"
        npu_suitability = "VERY HIGH" if workload_type in {"vision", "audio", "sensor", "edge"} else "HIGH" if complexity in {"medium", "high"} else "MEDIUM"

        return {
            "compute_intensity": compute_intensity,
            "memory_requirement": memory_requirements,
            "latency_sensitivity": latency_sensitivity,
            "power_sensitivity": power_sensitivity,
            "parallelism": parallelism,
            "npu_suitability": npu_suitability,
        }
