"""Pinned results of Attempts 1-3 on S1-S5 (seed 42).

If the simulation model or an algorithm is changed on purpose, regenerate these
numbers and document why in CHANGELOG.md. An accidental change fails here.
"""

import pytest

from experiments.runner import get_allocator, run_simulation, scenario_path

EXPECTED = {
    "S1_normal/baseline": [
        0.6207,
        98,
        30
    ],
    "S1_normal/fuzzy": [
        0.6214,
        96,
        30
    ],
    "S1_normal/pso": [
        0.6243,
        88,
        30
    ],
    "S2_patient_surge/baseline": [
        0.6826,
        431,
        80
    ],
    "S2_patient_surge/fuzzy": [
        0.6826,
        430,
        80
    ],
    "S2_patient_surge/pso": [
        0.6838,
        418,
        80
    ],
    "S3_icu_shortage/baseline": [
        0.6387,
        553,
        60
    ],
    "S3_icu_shortage/fuzzy": [
        0.6393,
        547,
        60
    ],
    "S3_icu_shortage/pso": [
        0.6443,
        498,
        60
    ],
    "S4_oxygen_shortage/baseline": [
        0.6999,
        281,
        70
    ],
    "S4_oxygen_shortage/fuzzy": [
        0.6999,
        281,
        70
    ],
    "S4_oxygen_shortage/pso": [
        0.7014,
        269,
        70
    ],
    "S5_pandemic_crisis/baseline": [
        0.7307,
        159,
        100
    ],
    "S5_pandemic_crisis/fuzzy": [
        0.7305,
        160,
        100
    ],
    "S5_pandemic_crisis/pso": [
        0.7307,
        159,
        100
    ]
}


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_original_algorithms_match_pinned_results(key):
    scenario, algorithm = key.split("/")
    result = run_simulation(scenario_path(scenario), get_allocator(algorithm, 42))
    fitness, conflicts, assignments = EXPECTED[key]
    assert result["fitness"] == pytest.approx(fitness, abs=1e-4)
    assert result["conflicts"] == conflicts
    assert result["assignments"] == assignments
