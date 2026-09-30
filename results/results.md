# SwarmCare benchmark results

PSO is stochastic: mean +/- std over 5 seed(s) starting at 42. Other algorithms are deterministic. Synthetic data only.

| Scenario | Algorithm | Fitness | vs baseline | Avg wait | Conflicts | Completed | Mean tick latency (ms) | Messages | ICU saturation | Bottleneck | Mean recovery (ticks) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1_normal | baseline | 0.6207 | +0.00% | 3.27 | 98 | 30/30 | 0.009 | - | 0% | doctors | - |
| S1_normal | fuzzy | 0.6214 | +0.11% | 3.20 | 96 | 30/30 | 0.013 | - | 0% | doctors | - |
| S1_normal | pso | 0.6242 +/- 0.0011 | +0.56% | 2.93 | 88 | 30/30 | 0.454 | - | 0% | doctors | - |
| S1_normal | decentralized | 0.6214 | +0.11% | 3.20 | 96 | 30/30 | 0.017 | 822 | 0% | doctors | - |
| S2_patient_surge | baseline | 0.6826 | +0.00% | 5.39 | 431 | 80/80 | 0.015 | - | 0% | doctors | 15.0 |
| S2_patient_surge | fuzzy | 0.6826 | +0.00% | 5.38 | 430 | 80/80 | 0.035 | - | 0% | doctors | 15.0 |
| S2_patient_surge | pso | 0.6839 +/- 0.0006 | +0.18% | 5.22 | 418 | 80/80 | 1.794 | - | 0% | doctors | 15.0 |
| S2_patient_surge | decentralized | 0.6826 | +0.00% | 5.38 | 430 | 80/80 | 0.053 | 3644 | 0% | doctors | 15.0 |
| S3_icu_shortage | baseline | 0.6387 | +0.00% | 9.22 | 553 | 60/60 | 0.015 | - | 6% | doctors | 0.0 |
| S3_icu_shortage | fuzzy | 0.6393 | +0.09% | 9.12 | 547 | 60/60 | 0.039 | - | 6% | doctors | 0.0 |
| S3_icu_shortage | pso | 0.6429 +/- 0.0008 | +0.65% | 8.30 | 498 | 60/60 | 1.840 | - | 2% | doctors | 0.0 |
| S3_icu_shortage | decentralized | 0.6393 | +0.09% | 9.12 | 547 | 60/60 | 0.061 | 4319 | 6% | doctors | 0.0 |
| S4_oxygen_shortage | baseline | 0.6999 | +0.00% | 4.01 | 281 | 70/70 | 0.014 | - | 0% | doctors | 10.0 |
| S4_oxygen_shortage | fuzzy | 0.6999 | +0.00% | 4.01 | 281 | 70/70 | 0.028 | - | 0% | doctors | 10.0 |
| S4_oxygen_shortage | pso | 0.7023 +/- 0.0006 | +0.34% | 3.84 | 269 | 70/70 | 1.307 | - | 0% | doctors | 10.0 |
| S4_oxygen_shortage | decentralized | 0.6999 | +0.00% | 4.01 | 281 | 70/70 | 0.038 | 2291 | 0% | doctors | 10.0 |
| S5_pandemic_crisis | baseline | 0.7307 | +0.00% | 1.59 | 159 | 100/100 | 0.015 | - | 1% | doctors | 1.0 |
| S5_pandemic_crisis | fuzzy | 0.7305 | -0.03% | 1.60 | 160 | 100/100 | 0.027 | - | 1% | doctors | 1.0 |
| S5_pandemic_crisis | pso | 0.7307 +/- 0.0001 | +0.00% | 1.59 | 159 | 100/100 | 0.843 | - | 0% | doctors | 1.0 |
| S5_pandemic_crisis | decentralized | 0.7305 | -0.03% | 1.60 | 160 | 100/100 | 0.032 | 2225 | 1% | doctors | 1.0 |
| S6_resource_stress | baseline | 0.6540 | +0.00% | 10.88 | 979 | 90/90 | 0.024 | - | 0% | oxygen | 9.0 |
| S6_resource_stress | fuzzy | 0.6536 | -0.06% | 10.96 | 986 | 90/90 | 0.070 | - | 0% | oxygen | 10.0 |
| S6_resource_stress | pso | 0.6542 +/- 0.0003 | +0.03% | 10.83 | 975 | 90/90 | 4.272 | - | 0% | oxygen | 9.0 |
| S6_resource_stress | decentralized | 0.6536 | -0.06% | 10.96 | 986 | 90/90 | 0.133 | 12312 | 0% | oxygen | 10.0 |
| S7_reserve_stress | baseline | 0.6809 | +0.00% | 6.49 | 227 | 35/35 | 0.015 | - | 6% | oxygen | - |
| S7_reserve_stress | fuzzy | 0.6805 | -0.06% | 6.54 | 229 | 35/35 | 0.033 | - | 6% | oxygen | - |
| S7_reserve_stress | pso | 0.6794 +/- 0.0009 | -0.22% | 6.86 | 240 | 35/35 | 1.686 | - | 4% | oxygen | - |
| S7_reserve_stress | decentralized | 0.6805 | -0.06% | 6.54 | 229 | 35/35 | 0.041 | 2428 | 6% | oxygen | - |
| S8_clinical_inputs | baseline | 0.7826 | +0.00% | 2.08 | 3 | 40/40 | 0.008 | - | 4% | icu | 0.0 |
| S8_clinical_inputs | fuzzy | 0.7826 | +0.00% | 2.08 | 3 | 40/40 | 0.012 | - | 4% | icu | 0.0 |
| S8_clinical_inputs | pso | 0.7826 +/- 0.0000 | +0.00% | 2.08 | 3 | 40/40 | 0.651 | - | 4% | icu | 0.0 |
| S8_clinical_inputs | decentralized | 0.7826 | +0.00% | 2.08 | 3 | 40/40 | 0.015 | 379 | 4% | icu | 0.0 |
