from pathlib import Path

from simulation.hospital import HospitalSimulator
from algorithms.baseline import greedy_allocate


SCENARIO = Path(
    "data/scenarios/S5_pandemic_crisis.json"
)


def test_greedy_allocation_returns_expected_fields():
    simulator = HospitalSimulator(SCENARIO)

    result = greedy_allocate(simulator)

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


def test_greedy_allocation_never_exceeds_resources():
    simulator = HospitalSimulator(SCENARIO)

    result = greedy_allocate(simulator)

    assert result["icu_used"] <= simulator.icu_beds
    assert result["ward_used"] <= simulator.ward_beds
    assert result["oxygen_used"] <= simulator.oxygen
    assert result["ventilators_used"] <= simulator.ventilators


def test_greedy_allocation_has_non_negative_counts():
    simulator = HospitalSimulator(SCENARIO)

    result = greedy_allocate(simulator)

    for value in result.values():
        assert value >= 0


def test_greedy_allocation_updates_statistics():
    simulator = HospitalSimulator(SCENARIO)

    before_assignments = simulator.total_assignments
    before_conflicts = simulator.total_conflicts

    result = greedy_allocate(simulator)

    assert simulator.total_assignments == (
        before_assignments + result["treated"]
    )
    assert simulator.total_conflicts == (
        before_conflicts + result["resource_conflicts"]
    )