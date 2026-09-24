# Snapdragon AIFlow

Snapdragon AIFlow is an AI-driven workload orchestration system for Snapdragon-inspired compute platforms. It predicts workload characteristics, scores execution targets, applies a selected AI operating mode, and explains why a given accelerator is chosen.

## Core flow

```text
Workload
  ↓
AI Workload Classifier
  ↓
Predict:
  • compute intensity
  • memory requirement
  • latency sensitivity
  • power sensitivity
  • parallelism
  ↓
AI Decision Engine
  ↓
Scheduler
  ↓
CPU / GPU / NPU
```

## AI modes

- Performance Mode: prioritizes minimum latency
- Battery Saver Mode: reduces energy use
- Balanced AI Mode: optimizes the performance/energy trade-off

## Advanced features

- AI workload prediction and explainable scoring
- Mode-aware scheduling logic
- Scenario simulator for what-if planning
- Workload queue support for multi-task orchestration
- Resource-aware execution reasoning

## Project structure

- `snapdragon_aiflow.models` — system and workload data structures
- `snapdragon_aiflow.classifier` — AI workload classification
- `snapdragon_aiflow.decision_engine` — scoring model for runtime decisions
- `snapdragon_aiflow.scheduler` — scheduling logic and explanation support
- `snapdragon_aiflow.simulator` — scenario-based prediction engine
- `snapdragon_aiflow.queue` — queued AI tasks
- `snapdragon_aiflow.app` — runnable demo entry point

## Quick start

```bash
python -m pytest -q
```

```bash
python -m snapdragon_aiflow.app
```

## Example

A vision workload such as object detection is predicted as:

- compute intensity: HIGH
- memory requirement: MEDIUM
- latency sensitivity: HIGH
- NPU suitability: VERY HIGH

Then the decision engine evaluates the active mode, system health, and available resources to select the optimal target.
