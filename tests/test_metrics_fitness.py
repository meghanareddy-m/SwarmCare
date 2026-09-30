import pytest

from evaluation.fitness import calculate_fitness
from evaluation.metrics import calculate_final_metrics
from simulation.hospital import HospitalSimulator
from algorithms.baseline import greedy_allocate, priority_score
from agents.entities import DoctorAgent, PatientAgent, ResourceAgent
from tests.helpers import make_scenario


def _metrics(**over):
    m = dict(treatment_rate=1.0, critical_coverage=1.0, average_waiting_time=0.0,
             conflict_rate=0.0, resource_utilization=1.0)
    m.update(over)
    return m


def test_fitness_perfect_and_weights():
    assert calculate_fitness(_metrics()) == pytest.approx(0.80)
    assert calculate_fitness(_metrics(critical_coverage=0.0)) == pytest.approx(0.40)
    assert calculate_fitness(_metrics(conflict_rate=1.0)) == pytest.approx(0.70)


def test_fitness_waiting_penalty_saturates_at_20_ticks():
    assert calculate_fitness(_metrics(average_waiting_time=20)) == calculate_fitness(
        _metrics(average_waiting_time=500))


def test_fitness_is_monotonic_in_critical_coverage():
    assert calculate_fitness(_metrics(critical_coverage=0.9)) < calculate_fitness(_metrics())


def test_metrics_on_tiny_scenario(tmp_path):
    path = make_scenario(tmp_path, [("A", 0.9, False, False, 0, 2), ("B", 0.3, False, False, 0, 2)],
                         doctors=1, icu=1, ward=1, ticks=10)
    sim = HospitalSimulator(path)
    while sim.time < sim.max_ticks:
        sim.apply_events(); greedy_allocate(sim); sim.step()
    m = calculate_final_metrics(sim)
    assert m["treatment_rate"] == 1.0 and m["critical_coverage"] == 1.0
    assert m["average_waiting_time"] == pytest.approx(1.0)  # B waited while A was treated
    assert 0 <= m["conflict_rate"] <= 1
    assert m["resource_utilization"] + m["resource_wastage"] == pytest.approx(1.0)


def test_metrics_ignore_patients_arriving_after_horizon(tmp_path):
    path = make_scenario(tmp_path, [("A", 0.5, False, False, 0, 1), ("late", 0.9, False, False, 99, 1)],
                         ticks=10)
    sim = HospitalSimulator(path)
    while sim.time < sim.max_ticks:
        sim.apply_events(); greedy_allocate(sim); sim.step()
    assert calculate_final_metrics(sim)["treatment_rate"] == 1.0


def test_events_reduce_capacity(tmp_path):
    path = make_scenario(tmp_path, [("A", 0.5, False, False, 0, 1)], doctors=3, icu=4, oxygen=10,
                         ventilators=3,
                         events=[{"time": 0, "type": "icu_beds_removed", "count": 10},
                                 {"time": 0, "type": "oxygen_reduction", "percentage": 50},
                                 {"time": 0, "type": "ventilator_failure", "count": 2},
                                 {"time": 0, "type": "doctor_unavailable", "count": 2}])
    sim = HospitalSimulator(path)
    sim.apply_events()
    assert (sim.icu_beds, sim.oxygen, sim.ventilators) == (0, 5, 1)
    assert sum(d.available for d in sim.doctors) == 1


def test_priority_prefers_severity_then_waiting():
    a = PatientAgent("a", 0.9, False, False, 0)
    b = PatientAgent("b", 0.5, False, False, 0, waiting_time=100)
    assert priority_score(a) > priority_score(b)
    c = PatientAgent("c", 0.5, False, False, 0, waiting_time=10)
    d = PatientAgent("d", 0.5, False, False, 0, waiting_time=0)
    assert priority_score(c) > priority_score(d)


def test_entity_defaults():
    p = PatientAgent("p", 0.5, True, False, 3)
    assert not p.treated and not p.completed and p.assigned_doctor is None
    assert DoctorAgent("D1").capacity == 1 and DoctorAgent("D1").available
    assert ResourceAgent("oxygen", "O1").available
