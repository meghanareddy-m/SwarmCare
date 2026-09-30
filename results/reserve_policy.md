# Reserve-policy experiment

Critical = severity >= 0.80. Waits are in ticks. Synthetic data; S7 is a *designed* stress case.

| Scenario | Policy | Critical mean wait | Critical max wait | Non-critical mean wait | Fitness | Reserve refusals |
|---|---|---|---|---|---|---|
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

## Verdict (computed from the table)

* **S6_resource_stress**: no benefit - the best reserve policy does not beat centralized on critical waiting (2.33 vs 2.29 ticks). (best reserve: decentralized, reserve 10% (severity >= 0.8); best centralized: centralized greedy)
* **S7_reserve_stress**: decentralized with reserve beats centralized on critical waiting (0.86 vs 6.29 ticks) at a cost: non-critical wait 11.89 vs 6.54, fitness 0.6609 vs 0.6809. (best reserve: decentralized, reserve 40% (severity >= 0.8); best centralized: centralized greedy)

Caveats: 'best reserve' is the best of the swept fractions (chosen after seeing the results); the gain comes from the reserve rule, not from decentralization itself (a centralized allocator could apply the same rule; not tested here); it is a trade-off, not a free improvement; and it appears only where oxygen is exhausted before critical patients arrive.
