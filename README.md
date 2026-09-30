# SwarmCare

## Intelligent Pandemic Hospital Resource Coordination Using Computational Intelligence

SwarmCare is a synthetic multi-agent hospital simulation designed around a pandemic surge scenario.

The system models a hospital experiencing a sudden increase in patient arrivals while simultaneously dealing with limited doctors, ICU beds, oxygen, ventilators, and diagnostic resources.

The project investigates how computational-intelligence techniques can improve patient prioritization and hospital resource allocation under dynamic environmental perturbations.

The project is designed around the intersection of:

- IEEE Engineering in Medicine and Biology Society (IEEE EMBS)
- IEEE Computational Intelligence Society (IEEE CIS)

---

# 1. Problem Statement

During a pandemic such as COVID-19, hospitals can experience sudden surges in patient arrivals.

At the same time, critical resources may become unavailable due to:

- ICU capacity exhaustion
- Doctor shortages
- Oxygen shortages
- Ventilator failures
- Other resource disruptions

Traditional fixed allocation policies can become inefficient when the hospital state changes rapidly.

SwarmCare models this problem as a dynamic resource-allocation and patient-prioritization problem.

The objective is to:

- Maximize the number of patients successfully treated
- Prioritize critically ill patients
- Minimize patient waiting time
- Minimize resource conflicts
- Improve resource utilization
- Maintain low decision latency
- Adapt to dynamic hospital perturbations

---

# 2. Computational Intelligence Approach

SwarmCare evaluates the problem progressively using three approaches.

## Attempt 1 — Greedy Baseline

A deterministic severity-first allocation strategy is used as the baseline.

Patients are prioritized primarily according to:

1. Clinical severity
2. Waiting time

The allocator checks whether all required resources are available before committing treatment.

This provides a reference point against which computational-intelligence approaches can be evaluated.

---

## Attempt 2 — Fuzzy Priority

The fixed priority rule is replaced with fuzzy-style reasoning.

The priority considers:

- Patient severity
- Waiting time
- Oxygen requirement

The purpose is to provide a more adaptive patient-prioritization mechanism than a fixed severity ranking.

---

## Attempt 3 — Particle Swarm Optimization

Particle Swarm Optimization (PSO) is introduced to search for improved patient-allocation priorities.

Each particle represents a candidate allocation-priority configuration.

The swarm evaluates candidate solutions according to the hospital simulation's resulting performance.

The current implementation uses:

| Parameter | Value |
|---|---:|
| Swarm size | 12 |
| Iterations | 15 |
| Inertia | 0.7 |
| Cognitive coefficient | 1.4 |
| Social coefficient | 1.4 |
| Random seed | 42 |

The PSO implementation records convergence information for experimental analysis.

---

# 3. Multi-Agent Representation

The simulation represents important hospital entities as agents.

## Patient Agent

A patient contains:

- Patient ID
- Severity
- Oxygen requirement
- Ventilator requirement
- Arrival time
- Service duration
- Waiting time
- Treatment status
- Completion status
- Assigned doctor
- Assigned bed

## Doctor Agent

A doctor contains:

- Doctor ID
- Treatment capacity
- Availability
- Current workload

## Resource Agent

The project also defines a generic resource-agent representation containing:

- Resource type
- Resource ID
- Availability

These representations allow the hospital environment to model interactions between patients, medical staff, and constrained resources.

---

# 4. Dynamic Pandemic Scenario

The primary benchmark is:

`S5_pandemic_crisis`

The scenario represents a combined pandemic crisis involving:

- Patient surge
- Staffing shortage
- Critical resource failures

The environment changes over simulation time.

The current synthetic scenario includes:

- Patient surge
- Doctor unavailability
- Oxygen reduction
- Ventilator failure
- ICU bed removal

This allows the allocation algorithms to be evaluated under changing resource conditions rather than only under a static hospital state.

---

# 5. Simulation Architecture

The project is organized into separate components.

```text
SwarmCare/
│
├── agents/
│   └── entities.py
│
├── algorithms/
│   ├── baseline.py
│   ├── fuzzy_baseline.py
|   ├── fuzzy_priority.py
│   ├── pso.py
│   └── pso_allocator.py
│
├── data/
│   └── scenarios/
|       └── S1_normal.json
|       └── S2_patient_surge.json
|       └── S3_icu_shortage.json
|       └── S4_oxygen_shortage.json
│       └── S5_pandemic_crisis.json
│
├── evaluation/
│   ├── fitness.py
│   └── metrics.py
│
├── simulation/
│   └── hospital.py
│
├── main.py
├── requirements.txt
└── README.md