from pathlib import Path

from simulation.hospital import HospitalSimulator
from algorithms.fuzzy_priority import triangular_membership
from algorithms.fuzzy_baseline import fuzzy_allocate


SCENARIO = Path(
    "data/scenarios/S5_pandemic_crisis.json"
)


def test_triangular_membership_stays_in_valid_range():
    values = [
        triangular_membership(0.0, 0.0, 0.5, 1.0),
        triangular_membership(0.25, 0.0, 0.5, 1.0),
        triangular_membership(0.5, 0.0, 0.5, 1.0),
        triangular_membership(0.75, 0.0, 0.5, 1.0),
        triangular_membership(1.0, 0.0, 0.5, 1.0),
    ]

    for value in values:
        assert 0.0 <= value <= 1.0


def test_fuzzy_allocation_returns_expected_fields():
    simulator = HospitalSimulator(SCENARIO)

    result = fuzzy_allocate(simulator)

    expected_fields = {
        "treated",
        "critical_treated",
        "resource_conflicts",
        "icu_used",
        "ward_used",
        "oxygen_used",
        "ventilators_used",
    }

    assert expected_fields.issubset(result.keys())


def test_fuzzy_allocation_counts_are_non_negative():
    simulator = HospitalSimulator(SCENARIO)

    result = fuzzy_allocate(simulator)

    for value in result.values():
        assert value >= 0


def test_fuzzy_allocation_never_exceeds_resources():
    simulator = HospitalSimulator(SCENARIO)

    result = fuzzy_allocate(simulator)

    assert result["icu_used"] <= simulator.icu_beds
    assert result["ward_used"] <= simulator.ward_beds
    assert result["oxygen_used"] <= simulator.oxygen
    assert result["ventilators_used"] <= simulator.ventilators