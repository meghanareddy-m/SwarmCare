# Benchmark results and interpretation

Produced by `python main.py --all --pso-seeds 5 --output results --plots` (base seed 42). All data are
synthetic. Latency and message columns are from the development machine and will differ elsewhere.
Deterministic attempts (baseline, fuzzy, decentralized) are single runs; PSO is the mean over 5 seeds
(std in `results/results.md`).

| Scenario | Algorithm | Fitness | vs baseline | Avg wait | Conflicts | Completed | Mean tick latency (ms) | Messages |
|---|---|---|---|---|---|---|---|---|
| Scenario | Algorithm | Fitness | vs baseline | Avg wait | Conflicts | Completed | Mean tick latency (ms) | Messages |
| S1_normal | baseline | 0.6207 | +0.00% | 3.27 | 98 | 30/30 | 0.009 | - |
| S1_normal | fuzzy | 0.6214 | +0.11% | 3.20 | 96 | 30/30 | 0.013 | - |
| S1_normal | pso | 0.6242 +/- 0.0011 | +0.56% | 2.93 | 88 | 30/30 | 0.454 | - |
| S1_normal | decentralized | 0.6214 | +0.11% | 3.20 | 96 | 30/30 | 0.017 | 822 |
| S2_patient_surge | baseline | 0.6826 | +0.00% | 5.39 | 431 | 80/80 | 0.015 | - |
| S2_patient_surge | fuzzy | 0.6826 | +0.00% | 5.38 | 430 | 80/80 | 0.035 | - |
| S2_patient_surge | pso | 0.6839 +/- 0.0006 | +0.18% | 5.22 | 418 | 80/80 | 1.794 | - |
| S2_patient_surge | decentralized | 0.6826 | +0.00% | 5.38 | 430 | 80/80 | 0.053 | 3644 |
| S3_icu_shortage | baseline | 0.6387 | +0.00% | 9.22 | 553 | 60/60 | 0.015 | - |
| S3_icu_shortage | fuzzy | 0.6393 | +0.09% | 9.12 | 547 | 60/60 | 0.039 | - |
| S3_icu_shortage | pso | 0.6429 +/- 0.0008 | +0.65% | 8.30 | 498 | 60/60 | 1.840 | - |
| S3_icu_shortage | decentralized | 0.6393 | +0.09% | 9.12 | 547 | 60/60 | 0.061 | 4319 |
| S4_oxygen_shortage | baseline | 0.6999 | +0.00% | 4.01 | 281 | 70/70 | 0.014 | - |
| S4_oxygen_shortage | fuzzy | 0.6999 | +0.00% | 4.01 | 281 | 70/70 | 0.028 | - |
| S4_oxygen_shortage | pso | 0.7023 +/- 0.0006 | +0.34% | 3.84 | 269 | 70/70 | 1.307 | - |
| S4_oxygen_shortage | decentralized | 0.6999 | +0.00% | 4.01 | 281 | 70/70 | 0.038 | 2291 |
| S5_pandemic_crisis | baseline | 0.7307 | +0.00% | 1.59 | 159 | 100/100 | 0.015 | - |
| S5_pandemic_crisis | fuzzy | 0.7305 | -0.03% | 1.60 | 160 | 100/100 | 0.027 | - |
| S5_pandemic_crisis | pso | 0.7307 +/- 0.0001 | +0.00% | 1.59 | 159 | 100/100 | 0.843 | - |
| S5_pandemic_crisis | decentralized | 0.7305 | -0.03% | 1.60 | 160 | 100/100 | 0.032 | 2225 |
| S6_resource_stress | baseline | 0.6540 | +0.00% | 10.88 | 979 | 90/90 | 0.024 | - |
| S6_resource_stress | fuzzy | 0.6536 | -0.06% | 10.96 | 986 | 90/90 | 0.070 | - |
| S6_resource_stress | pso | 0.6542 +/- 0.0003 | +0.03% | 10.83 | 975 | 90/90 | 4.272 | - |
| S6_resource_stress | decentralized | 0.6536 | -0.06% | 10.96 | 986 | 90/90 | 0.133 | 12312 |
| S7_reserve_stress | baseline | 0.6809 | +0.00% | 6.49 | 227 | 35/35 | 0.015 | - |
| S7_reserve_stress | fuzzy | 0.6805 | -0.06% | 6.54 | 229 | 35/35 | 0.033 | - |
| S7_reserve_stress | pso | 0.6794 +/- 0.0009 | -0.22% | 6.86 | 240 | 35/35 | 1.686 | - |
| S7_reserve_stress | decentralized | 0.6805 | -0.06% | 6.54 | 229 | 35/35 | 0.041 | 2428 |
| S8_clinical_inputs | baseline | 0.7826 | +0.00% | 2.08 | 3 | 40/40 | 0.008 | - |
| S8_clinical_inputs | fuzzy | 0.7826 | +0.00% | 2.08 | 3 | 40/40 | 0.012 | - |
| S8_clinical_inputs | pso | 0.7826 +/- 0.0000 | +0.00% | 2.08 | 3 | 40/40 | 0.651 | - |
| S8_clinical_inputs | decentralized | 0.7826 | +0.00% | 2.08 | 3 | 40/40 | 0.015 | 379 |

Figures: `results/fitness_by_scenario.png`, `results/queue_<scenario>.png`, `results/pso_convergence.png`.
Interactive view: `results/dashboard.html`. Extended metrics (ICU saturation, bottleneck, mean recovery time) per run
are in `results/results.md` / `results.csv`; the latency-budget result is in `results.json`.

## Findings

1. **All strategies treat every patient within the horizon** (treatment rate and critical coverage are 1.0
   everywhere). Differences in fitness therefore come from the waiting-time and conflict penalties only.
2. **PSO is best or tied in S1–S6**, with gains of +0.00 % … +0.65 % over the baseline; on S7 it is slightly
   worse (−0.22 %). The
   gains are consistent across seeds (std ≤ 0.0011) but small; this is not evidence that PSO is superior
   in general or in a real hospital.
3. **Fuzzy priority ≈ baseline** (−0.06 % … +0.11 %). Severity already dominates both rules.
4. **Decentralized negotiation = centralized fuzzy** when the reserve policy is off (identical fitness,
   conflicts and completions in all eight scenarios; asserted in `tests/test_decentralized.py`). Local bids and
   grants therefore recover the centralized decision, with 379–12 312 messages per run as the price.
5. **Decision latency**: baseline/fuzzy/decentralized ≈ 0.01–0.13 ms per tick, PSO ≈ 0.5–4.3 ms per tick
   (it grows with the waiting-list size). All are far below the default 50 ms budget on these scenarios; the
   scaling study below shows where that stops being true.
6. **Bottleneck** (extended metric): doctors on S1–S5, oxygen on S6 and S7, ICU beds on S8. ICU saturation is
   low (0–6 % of ticks) everywhere. Mean recovery from the S2 surge is 15 ticks, from S5's five events 1 tick
   (four of the five events do not raise the queue).

## Reserve-policy experiment (`python -m experiments.reserve_policy`)

Oxygen is protected for patients with severity >= 0.80 once stock is at or below the reserve fraction. Waits in
ticks. Full output: `results/reserve_policy.md`.

| Scenario | Policy | Critical mean wait | Critical max wait | Non-critical mean wait | Fitness | Reserve refusals |
|---|---|---|---|---|---|---|
| Scenario | Policy | Critical mean wait | Critical max wait | Non-critical mean wait | Fitness | Reserve refusals |
| S6_resource_stress | centralized greedy | 2.29 | 14 | 13.49 | 0.6540 | 0 |
| S6_resource_stress | centralized fuzzy | 2.43 | 11 | 13.55 | 0.6536 | 0 |
| S6_resource_stress | decentralized, reserve off | 2.43 | 11 | 13.55 | 0.6536 | 0 |
| S6_resource_stress | decentralized, reserve 10% (severity >= 0.8) | 2.33 | 11 | 15.49 | 0.6453 | 521 |
| S6_resource_stress | decentralized, reserve 20% (severity >= 0.8) | 2.33 | 11 | 18.36 | 0.6333 | 954 |
| S6_resource_stress | decentralized, reserve 30% (severity >= 0.8) | 2.33 | 11 | 21.03 | 0.6223 | 1225 |
| S6_resource_stress | decentralized, reserve 40% (severity >= 0.8) | 2.33 | 11 | 22.42 | 0.6167 | 1241 |
| S7_reserve_stress | centralized greedy | 6.29 | 8 | 6.54 | 0.6809 | 0 |
| S7_reserve_stress | centralized fuzzy | 6.29 | 7 | 6.61 | 0.6805 | 0 |
| S7_reserve_stress | decentralized, reserve off | 6.29 | 7 | 6.61 | 0.6805 | 0 |
| S7_reserve_stress | decentralized, reserve 10% (severity >= 0.8) | 4.00 | 5 | 7.82 | 0.6771 | 118 |
| S7_reserve_stress | decentralized, reserve 20% (severity >= 0.8) | 4.00 | 5 | 8.11 | 0.6756 | 140 |
| S7_reserve_stress | decentralized, reserve 30% (severity >= 0.8) | 4.00 | 5 | 8.57 | 0.6733 | 180 |
| S7_reserve_stress | decentralized, reserve 40% (severity >= 0.8) | 0.86 | 3 | 11.89 | 0.6609 | 245 |

* **S6 (natural, oxygen-bound)**: no benefit. Critical patients wait 2.3-2.4 ticks under every policy; the reserve
  only lengthens non-critical waits (13.5 → up to 22.4) and lowers fitness (0.6536 → 0.6167).
* **S7 (designed)**: the reserve lowers critical waiting from 6.29 (greedy) to 4.00 (10-30 %) and 0.86 (40 %),
  while non-critical waiting rises from 6.5 to 11.9 and fitness falls from 0.6809 to 0.6609.

So the decentralized negotiation **with a reserve rule** beats the centralized allocators on critical waiting only
in a scenario built so that oxygen is exhausted before critical patients arrive, and it pays for it elsewhere. The
gain comes from the reserve rule (deliberate idling), not from decentralization itself; a centralized allocator
could apply the same rule (not tested). The best fraction was picked after seeing the results. Without the reserve
rule, decentralized and centralized fuzzy are identical. Earlier notes that said the reserve "lowers fitness because
critical coverage is already 100 %" remain true for the fitness; the new measure is critical waiting time.

## Scaling study (`python -m experiments.scaling`)

Fixed hospital, 25-400 patients, PSO budgets 6x8 / 12x15 / 24x30 (48 / 180 / 720 evaluations per decision), PSO
averaged over 3 seeds; full table in `results/scaling.md`.

* Up to 200 patients every method treats everyone; differences in fitness are tiny (<= 0.0011).
* At 400 patients the fixed hospital is overloaded (only 77-78 % completed in 80 ticks). PSO fitness is 0.5496-0.5522
  vs 0.5474 for the baseline and 0.5480 for fuzzy/decentralized: a small gain, **not monotone in budget** (the 6x8
  budget scored highest; the 24x30 budget scored lowest of the three). Critical mean wait under PSO was 1.1-3.6 ticks vs 0.48
  for baseline/fuzzy/decentralized, i.e. PSO was worse for critical patients at this load.
* Mean decision latency grows roughly linearly to super-linearly with patients (log-log slope 1.0 baseline, 1.3-1.5
  for the others) and linearly with the PSO budget. PSO 24x30 needs ~107 ms per decision at 400 patients (p. max
  170 ms), i.e. it exceeds a 50 ms budget, while baseline, fuzzy and decentralized stay below 1 ms.
* Latency is wall-clock on the development machine; relative ordering is more trustworthy than absolute values.

## Caveats

* One simulator model and one weighted fitness function; conclusions depend on both.
* Scenarios S6, S7 and S8 were designed by us (S6 to make oxygen bind, S7 to exhaust oxygen before critical arrivals, S8 to exercise age/SpO₂/diagnostics); they are stress tests, not calibrated cases.
* The scaling study keeps the hospital fixed, so patient count and congestion are confounded.
* The conflict metric counts each waiting patient every tick, so it mostly measures queue length.
* Historical numbers quoted in earlier notes (e.g. S5 0.7307 / 0.6207) come from different model versions;
  the values here are the current ones and are pinned by `tests/test_regression.py`.
