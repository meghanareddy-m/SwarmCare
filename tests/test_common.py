import pytest

from algorithms.common import (allocate_in_order, available_resources, needs_icu)
from experiments.runner import ALGORITHM_LABELS, get_allocator, list_scenarios, scenario_path
from simulation.hospital import HospitalSimulator
from tests.helpers import make_scenario


def test_needs_icu_threshold():
    class P:  # minimal stand-in
        def __init__(self, s): self.severity = s
    assert needs_icu(P(0.80)) and needs_icu(P(0.95))
    assert not needs_icu(P(0.79))


def test_allocate_in_order_respects_doctors_and_counts_conflicts(tmp_path):
    path = make_scenario(tmp_path, [
        ("A", 0.9, False, False, 0, 3), ("B", 0.85, False, False, 0, 3),
        ("C", 0.4, False, False, 0, 3)], doctors=2, icu=1, ward=5)
    sim = HospitalSimulator(path)
    stats = allocate_in_order(sim, sim.active_patients())
    # 2 doctors, 1 ICU bed: A gets ICU, B (needs ICU) conflicts, C gets ward.
    assert stats["treated"] == 2
    assert stats["resource_conflicts"] == 1
    assert sim.total_conflicts == 1 and sim.total_assignments == 2
    assert {p.patient_id for p in sim.treatment_patients()} == {"A", "C"}


def test_ventilator_and_oxygen_are_required(tmp_path):
    path = make_scenario(tmp_path, [("A", 0.5, True, True, 0, 2)],
                         oxygen=0, ventilators=1)
    sim = HospitalSimulator(path)
    assert allocate_in_order(sim, sim.active_patients())["treated"] == 0


def test_available_resources_never_negative(tmp_path):
    path = make_scenario(tmp_path, [("A", 0.9, True, True, 0, 5)], icu=1, oxygen=1)
    sim = HospitalSimulator(path)
    allocate_in_order(sim, sim.active_patients())
    sim.icu_beds = 0  # event removes capacity below current occupancy
    assert min(available_resources(sim).values()) == 0


@pytest.mark.parametrize("algorithm", list(ALGORITHM_LABELS))
@pytest.mark.parametrize("scenario", list_scenarios())
def test_no_algorithm_oversubscribes_resources(algorithm, scenario):
    """After every allocation, occupancy never exceeds capacity (unless an
    event already removed capacity below the pre-existing occupancy)."""
    sim = HospitalSimulator(scenario_path(scenario))
    allocator = get_allocator(algorithm, 42)
    while sim.time < sim.max_ticks:
        sim.apply_events()
        before = {
            "ICU": sum(p.assigned_bed == "ICU" for p in sim.treatment_patients()),
            "WARD": sum(p.assigned_bed == "WARD" for p in sim.treatment_patients()),
            "oxy": sum(p.oxygen_required for p in sim.treatment_patients()),
            "vent": sum(p.ventilator_required for p in sim.treatment_patients()),
        }
        allocator(sim)
        tp = sim.treatment_patients()
        after = {
            "ICU": sum(p.assigned_bed == "ICU" for p in tp),
            "WARD": sum(p.assigned_bed == "WARD" for p in tp),
            "oxy": sum(p.oxygen_required for p in tp),
            "vent": sum(p.ventilator_required for p in tp),
        }
        cap = {"ICU": sim.icu_beds, "WARD": sim.ward_beds, "oxy": sim.oxygen, "vent": sim.ventilators}
        for k in cap:
            assert after[k] <= max(cap[k], before[k]), (scenario, algorithm, sim.time, k)
        assert sum(d.current_load for d in sim.doctors) <= sum(d.capacity for d in sim.doctors)
        sim.step()
