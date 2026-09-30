# Changelog

## Unreleased

### Added (engineering / audit round 2)
- `agents/swarm_agents.py`: pooled `ResourceOfferAgent` split into `DoctorPoolAgent`, `ICUAgent`, `WardAgent`,
  `OxygenAgent`, `VentilatorAgent` (+ `build_resource_agents`); base class kept; reserve-refusal counter.
- `evaluation/metrics.py`: `icu_saturation`, `recovery_time`, `bottleneck`, `latency_budget`,
  `critical_patient_outcomes`, `calculate_extended_metrics` (timeline based; fitness inputs unchanged).
- `experiments/runner.py`: per-tick `timeline` and `decisions` records, extended metrics in every result, new CSV/MD columns;
  `--latency-budget-ms` and `--dashboard` CLI options.
- `experiments/dashboard.py`: single-file `results/dashboard.html` (inline SVG/JS, no dependencies): queue over time,
  utilization per resource, shock markers, agent decisions, metric cards.
- `experiments/scaling.py`: patient-count x PSO-budget scaling study (`results/scaling.*`).
- `experiments/reserve_policy.py`: centralized vs decentralized reserve experiment (`results/reserve_policy.*`).
- Optional `age` / `spo2` fuzzy inputs (rules 8-9, silent when absent) and a minimal diagnostics queue
  (`diagnostic`, `diagnostic_duration`; `HospitalSimulator.diagnostic_queue()`).
- Scenarios S7_reserve_stress and S8_clinical_inputs with generators.
- 84 new tests (189 total).

### Changed (engineering / audit round 2)
- `waiting_time` now counts every arrived, untreated patient (this includes the diagnostics queue); identical to the
  old rule for scenarios without diagnostics (regression pins unchanged).
- Decentralized default policy: `oxygen_reserve_fraction` is now 0.0. The code had 0.10 while README/ARCHITECTURE/RESULTS
  stated the reserve was off. Outcomes (fitness, conflicts, completions) are identical on all scenarios; only the
  message counts changed (e.g. S6: 10 939 -> 12 312) because refused patients no longer withdraw early.

### Added (earlier)
- Attempt 4: decentralized contract-net style negotiation (`algorithms/decentralized.py`,
  `agents/swarm_agents.py`) with optional local reserve policy for oxygen/ventilators.
- `algorithms/common.py`: shared admission mechanics (removes ~400 duplicated lines).
- `experiments/` benchmark harness (multi-seed PSO, latency, message counts, CSV/JSON/Markdown output, optional plots).
- Command-line interface in `main.py` (`--scenario`, `--all`, `--algorithms`, `--pso-seeds`, `--seed`, `--output`, `--plots`).
- Scenario S6_resource_stress and its generator (`data/generate_stress_scenario.py`).
- 80 new tests (105 total at that point): invariants for every algorithm×scenario, regression pins, decentralized protocol, runner, CLI, metrics/fitness.
- `docs/ARCHITECTURE.md`, `docs/RESULTS.md`, `pyproject.toml`, `Makefile`, CI workflow, `requirements-dev.txt`.

### Changed
- `main.py` defaults to S5_pandemic_crisis (previously hard-coded to S3) and reports all four attempts.
- `pso_allocator.make_pso_allocator(base_seed, ...)` allows seeded multi-run studies; `pso_allocate` behaves as before.
- README rewritten (was truncated); scope limits and unimplemented components are stated explicitly.
- `.env.example` now lists only variables that the code reads.
- Line endings normalized to LF.

### Verified
- Results of Attempts 1–3 on S1–S5 are bit-for-bit identical before and after the refactor.
