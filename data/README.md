# Synthetic SwarmCare benchmark

All data are synthetic and reproducible with random seed 42. These files are simulation benchmarks,
not clinical datasets.

Each JSON contains hospital capacities, synthetic patient attributes (severity, oxygen/ventilator need,
arrival time, service duration), dynamic perturbation events and the simulation horizon (ticks).

| Scenario | Purpose |
|---|---|
| S1_normal | reference load, no events |
| S2_patient_surge | 50 additional arrivals at t=20 |
| S3_icu_shortage | ICU beds removed at t=25 |
| S4_oxygen_shortage | oxygen reduced at t=30 |
| S5_pandemic_crisis | combined surge, doctor loss, oxygen cut, ventilator failure, ICU loss |
| S6_resource_stress | oxygen/ventilator-bound stress test (`generate_stress_scenario.py`) |
| S7_reserve_stress | designed case: oxygen exhausted by early moderate patients before critical ones arrive (`generate_reserve_scenario.py`) |
| S8_clinical_inputs | patients with `age`, `spo2` and a CT/XRAY/LAB `diagnostic` (`generate_clinical_scenario.py`) |

`update_durations.py` assigns severity-dependent service durations to S1–S5 (already applied; re-running it
rewrites those files). `diagnostics` capacities are consumed by the simulator's diagnostics queue only for patients that declare a
`diagnostic` (S8). Optional patient fields: `age`, `spo2`, `diagnostic`, `diagnostic_duration`.
