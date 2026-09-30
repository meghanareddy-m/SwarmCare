# SwarmCare architecture

## Layers

```
 data/scenarios/*.json ──► simulation.HospitalSimulator ◄── allocation function (one of four)
                                   │                               ▲
                                   ▼                               │
                     evaluation.metrics ──► evaluation.fitness     experiments.runner (benchmark, latency, CSV/JSON/MD)
                                                                   ▲
                                                               main.py (CLI)
```

## Simulation loop (`experiments.runner.run_simulation`)

For each tick `t = 0 … ticks-1`:

1. `apply_events()` – shocks scheduled for `t` change capacities (ICU beds, oxygen, ventilators, doctors). The runner records which events fired.
2. `allocator(simulator)` – decides which waiting patients are admitted *now*.
3. `step()` – patients in treatment consume one tick of service; finished patients are completed and
   free their doctor; the diagnostics queue advances; every arrived, untreated patient accumulates waiting time;
   time advances.

After each decision the runner stores a snapshot (queue before/after, used/capacity per resource, diagnostics
queue, events) and a decision record (admitted patients, deferred count, messages/rounds/reserve refusals). The
extended metrics (`evaluation/metrics.py`) and the dashboard read only these records.

A patient is *active* once `arrival_time <= t`, it is neither in treatment nor completed, and it has no pending
diagnostic. Patient surges are
represented purely by arrival times in the data.

## Admission rules (identical for all attempts, `algorithms/common.py`)

A patient is admitted only if **all** of the following exist at that moment:

* an idle, available doctor (capacity 1),
* an ICU bed if `severity >= 0.80`, otherwise a ward bed,
* an oxygen unit if `oxygen_required`,
* a ventilator if `ventilator_required`.

Free capacity = current capacity − units held by patients in treatment (never negative). Each patient
that cannot be admitted in a tick counts as one *conflict*.

## Agents

| Class | Module | Role |
|---|---|---|
| `PatientAgent` | `agents/entities.py` | patient state (severity, needs, waiting time, assignment) |
| `DoctorAgent` | `agents/entities.py` | doctor state (capacity, availability, load) |
| `ResourceAgent` | `agents/entities.py` | generic resource record (not used by the allocators) |
| `Bid` | `agents/swarm_agents.py` | request message: patient + locally computed priority |
| `ResourceOfferAgent` | `agents/swarm_agents.py` | base class: local owner of a pool of units; grants to best bids; optional reserve policy |
| `DoctorPoolAgent`, `ICUAgent`, `WardAgent`, `OxygenAgent`, `VentilatorAgent` | `agents/swarm_agents.py` | one specialised agent per resource, built by `build_resource_agents`; only oxygen/ventilators receive a reserve policy. Behaviour is identical to the former pooled agents |

## Attempt 4 – decentralized negotiation

Per tick, in rounds (max 8):

1. Every pending patient computes its own fuzzy priority (severity, waiting, oxygen need, and SpO₂/age when
   recorded) and sends a `Bid` to the resource agents it needs.
2. Each `ResourceOfferAgent` ranks only the bids it received and tentatively grants up to its free units.
   A bid is refused *permanently* when the agent has no units (or its reserve policy blocks the patient) and
   *for now* when the patient was merely outranked.
3. A patient holding every grant commits (agents decrement stock); a patient refused permanently withdraws
   and is counted as one conflict; outranked patients bid again next round.
4. Stop when nobody is pending or a round makes no progress.

Optional local policy: `oxygen_reserve_fraction` / `ventilator_reserve_fraction` with
`*_reserve_min_severity` — when stock falls to the reserve, only patients above the severity threshold are
served. It is **off by default** (see RESULTS.md and `results/reserve_policy.md`).

The protocol is simulated synchronously in a single process. It demonstrates decentralized decision
making (no global sort, no global view) but is not a networked or fault-tolerant deployment.

## PSO (Attempt 3)

Particle = vector in [0,1]^n (one entry per waiting patient); sorting the entries gives an admission order.
The objective is a virtual admission pass over current free capacity (`PatientPSO.evaluate_order`), rewarding
critical coverage and treatment rate and penalizing conflicts and waiting. Defaults: 12 particles,
15 iterations, inertia 0.7, cognitive = social = 1.4, velocity clamp ±0.5. The seed per tick is
`base_seed + tick`.

## Extended metrics, dashboard and experiments

* `evaluation/metrics.py`: `icu_saturation`, `recovery_time`, `bottleneck`, `latency_budget`,
  `critical_patient_outcomes` (pure functions of the recorded timeline/latencies; not part of the fitness).
* `experiments/dashboard.py`: writes one HTML file with the data embedded as JSON and drawn with inline SVG/JS.
* `experiments/scaling.py`: patient counts × PSO budgets on generated scenarios.
* `experiments/reserve_policy.py`: centralized vs decentralized (± reserve) on critical-patient waiting.

## Optional clinical inputs and diagnostics

* `age` (years) and `spo2` (percent) on a patient add fuzzy rules 8 and 9; absent values add no rules.
* `diagnostic` (`CT`/`XRAY`/`LAB`, must exist in the scenario's `diagnostics` with capacity > 0) and
  `diagnostic_duration` put the patient into `HospitalSimulator.diagnostic_queue()`. Per modality the free
  units go to the most severe waiting patients; a diagnostic of duration *d* makes the patient admissible *d*
  ticks after it starts.

## Extending

* New allocator: write `f(simulator) -> dict` that mutates the simulator through
  `algorithms.common.commit_admission` (or `allocate_in_order`), register it in
  `experiments.runner.get_allocator` and `ALGORITHM_LABELS`.
* New scenario: drop a JSON file into `data/scenarios/` (same schema as the others). The test-suite
  invariants (`tests/test_common.py`) run automatically on every scenario found.
