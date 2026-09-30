# SwarmCare

## Intelligent Pandemic Hospital Resource Coordination Using Computational Intelligence

SwarmCare is a synthetic multi-agent hospital simulation designed to study how computational intelligence can support hospital resource coordination during pandemic-scale patient surges.

The system models a hospital experiencing sudden increases in patient arrivals while simultaneously dealing with constrained medical resources such as doctors, ICU beds, oxygen, ventilators, and diagnostic resources.

SwarmCare investigates how adaptive computational-intelligence techniques can improve patient prioritization and resource allocation when hospital conditions change dynamically.

The project sits at the intersection of:

- IEEE Engineering in Medicine and Biology Society (IEEE EMBS)
- IEEE Computational Intelligence Society (IEEE CIS)

The project also aligns with **United Nations Sustainable Development Goal 3 (SDG 3): Good Health and Well-Being**, particularly through its focus on improving the efficiency and resilience of healthcare resource coordination during large-scale health emergencies.

---

# 1. Problem Statement

During a pandemic such as COVID-19, hospitals can experience sudden surges in patient arrivals.

At the same time, critical healthcare resources may become constrained or unavailable due to:

- ICU capacity exhaustion
- Doctor shortages
- Oxygen shortages
- Ventilator failures
- Other resource disruptions

When demand changes rapidly, fixed allocation policies may become inefficient and can lead to increased waiting times, resource conflicts, and under-utilization of available capacity.

SwarmCare models this situation as a **dynamic multi-agent resource-allocation and patient-prioritization problem**.

The system aims to:

- Maximize the number of patients successfully treated
- Prioritize critically ill patients
- Minimize patient waiting time
- Minimize resource conflicts
- Improve resource utilization
- Maintain low decision latency
- Adapt to dynamic hospital perturbations

The project uses synthetic simulation rather than real patient data. It is therefore intended as a computational-intelligence research and benchmarking environment, not as a clinical decision-support system.

---

# 2. SDG 3 — Good Health and Well-Being

## Alignment with United Nations Sustainable Development Goal 3

SwarmCare aligns with:

> **SDG 3: Good Health and Well-Being**

The project contributes to SDG 3 by investigating computational methods that can improve the efficiency, responsiveness, and resilience of healthcare resource coordination during emergency situations.

### SDG 3 relevance

Large-scale health emergencies can place hospitals under severe operational pressure.

SwarmCare addresses this operational challenge by simulating how limited healthcare resources can be dynamically coordinated when patient demand changes.

The system focuses on:

| SwarmCare capability | Healthcare relevance |
|---|---|
| Patient prioritization | Helps model severity-aware treatment ordering |
| ICU allocation | Models constrained critical-care capacity |
| Oxygen allocation | Models shortages of essential respiratory resources |
| Ventilator allocation | Models critical equipment constraints |
| Doctor allocation | Models healthcare workforce limitations |
| Pandemic surge simulation | Models sudden increases in healthcare demand |
| Dynamic perturbations | Models changing emergency conditions |
| Conflict minimization | Models competition for scarce resources |
| Waiting-time minimization | Models delays in access to treatment |
| Resource utilization | Models efficient use of constrained infrastructure |

### SDG 3 impact pathway

```text
Pandemic Patient Surge
        |
        v
Increased Healthcare Demand
        |
        v
Resource Competition
        |
        v
Multi-Agent Coordination
        |
        v
Adaptive Computational Intelligence
        |
        +--------------------+
        |                    |
        v                    v
Better Prioritization   Better Allocation
        |                    |
        +---------+----------+
                  |
                  v
       Reduced Operational Delay
                  |
                  v
      More Efficient Healthcare
       Resource Coordination