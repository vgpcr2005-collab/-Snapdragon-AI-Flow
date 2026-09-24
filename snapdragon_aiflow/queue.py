from __future__ import annotations

from collections import deque


class WorkloadQueue:
    """Stores pending AI tasks and assigns priority-based execution order."""

    def __init__(self):
        self._queue = deque()

    def add(self, workload):
        self._queue.append(workload)

    def next(self):
        return self._queue.popleft() if self._queue else None

    def snapshot(self):
        return [
            {"name": task.name, "priority": getattr(task, "priority", 0.5), "workload_type": task.model.workload_type}
            for task in list(self._queue)
        ]
