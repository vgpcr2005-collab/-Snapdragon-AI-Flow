from dataclasses import dataclass


@dataclass
class SystemMetrics:
    cpu: int = 0
    gpu: int = 0
    npu: int = 0
    battery: int | None = None
    temperature: int | None = None


@dataclass
class ModelProfile:
    name: str
    complexity: str
    latency_budget_ms: int
    workload_type: str


@dataclass
class Workload:
    name: str
    model: ModelProfile
    priority: float = 0.5
