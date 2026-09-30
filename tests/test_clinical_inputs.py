"""Item 9: SpO2 and age as optional fuzzy inputs, and a diagnostics queue."""
import pytest

from agents.entities import PatientAgent
from algorithms.baseline import greedy_allocate
from algorithms.fuzzy_baseline import fuzzy_allocate
from algorithms.fuzzy_priority import fuzzy_priority
from experiments.runner import get_allocator, run_simulation, scenario_path
from simulation.hospital import HospitalSimulator
from tests.helpers import make_scenario


def patient(severity=0.6, **kw):
    return PatientAgent("p", severity, kw.pop("oxygen", False), False, 0, **kw)


# ------------------------------------------------------------ fuzzy inputs

def test_missing_age_and_spo2_leave_priority_unchanged():
    base = patient(0.6)
    assert base.age is None and base.spo2 is None
    # same value as a patient object that has no such attributes at all
    class Legacy:
        severity, waiting_time, oxygen_required = 0.6, 0, False
    assert fuzzy_priority(base) == fuzzy_priority(Legacy())


def test_low_spo2_raises_priority():
    assert fuzzy_priority(patient(0.4, spo2=84.0)) > fuzzy_priority(patient(0.4))
    assert fuzzy_priority(patient(0.4, spo2=84.0)) > fuzzy_priority(patient(0.4, spo2=98.0))


def test_normal_spo2_does_not_change_priority():
    # the SpO2 rule has zero activation at or above 94 %
    assert fuzzy_priority(patient(0.6, spo2=97.0)) == fuzzy_priority(patient(0.6))


def test_high_age_raises_priority_for_medium_severity_only():
    assert fuzzy_priority(patient(0.6, age=85)) > fuzzy_priority(patient(0.6))
    assert fuzzy_priority(patient(0.6, age=30)) == fuzzy_priority(patient(0.6))
    assert fuzzy_priority(patient(0.95, age=85)) == fuzzy_priority(patient(0.95))


def test_priority_stays_in_unit_interval_with_all_inputs():
    for sev in (0.0, 0.3, 0.6, 0.95, 1.0):
        for spo2 in (None, 70.0, 90.0, 99.0):
            for age in (None, 20, 75, 100):
                assert 0.0 <= fuzzy_priority(patient(sev, spo2=spo2, age=age)) <= 1.0


def test_simulator_loads_optional_fields(tmp_path):
    path = make_scenario(tmp_path, [("A", 0.5, False, False, 0, 2), ("B", 0.5, False, False, 0, 2)],
                         extras={"A": {"age": 81, "spo2": 86.5}})
    sim = HospitalSimulator(path)
    a, b = sim.patients
    assert (a.age, a.spo2) == (81, 86.5) and (b.age, b.spo2) == (None, None)


def test_fuzzy_allocator_admits_hypoxic_patient_first(tmp_path):
    # one doctor; identical severity; only B is hypoxic -> B goes first under fuzzy, A under greedy tie order
    path = make_scenario(tmp_path, [("A", 0.4, False, False, 0, 3), ("B", 0.4, False, False, 0, 3)],
                         doctors=1, extras={"B": {"spo2": 82.0}})
    sim = HospitalSimulator(path)
    fuzzy_allocate(sim)
    assert [p.patient_id for p in sim.treatment_patients()] == ["B"]


# -------------------------------------------------------- diagnostics queue

def diag_scenario(tmp_path, patients, extras, diagnostics=None, **kw):
    return make_scenario(tmp_path, patients, extras=extras, diagnostics=diagnostics or {"CT": 1}, **kw)


def test_patient_needing_diagnostic_is_not_active_until_done(tmp_path):
    path = diag_scenario(tmp_path, [("A", 0.5, False, False, 0, 2)],
                         {"A": {"diagnostic": "CT", "diagnostic_duration": 2}})
    sim = HospitalSimulator(path)
    assert sim.active_patients() == [] and len(sim.diagnostic_queue()) == 1
    sim.step()                        # diagnostic started and 1 of 2 ticks done
    assert sim.active_patients() == []
    sim.step()                        # done at the end of the 2nd tick
    assert [p.patient_id for p in sim.active_patients()] == ["A"]
    assert sim.diagnostic_queue() == []


def test_patient_without_diagnostic_is_unaffected(tmp_path):
    path = diag_scenario(tmp_path, [("A", 0.5, False, False, 0, 2), ("B", 0.5, False, False, 0, 2)],
                         {"B": {"diagnostic": "CT"}})
    sim = HospitalSimulator(path)
    assert [p.patient_id for p in sim.active_patients()] == ["A"]


def test_diagnostic_capacity_serves_most_severe_first_one_at_a_time(tmp_path):
    path = diag_scenario(tmp_path, [("low", 0.3, False, False, 0, 1), ("high", 0.9, False, False, 0, 1)],
                         {"low": {"diagnostic": "CT"}, "high": {"diagnostic": "CT"}}, doctors=2)
    sim = HospitalSimulator(path)
    sim.step()
    assert [p.patient_id for p in sim.active_patients()] == ["high"]
    sim.step()
    assert {p.patient_id for p in sim.active_patients()} == {"high", "low"}


def test_modalities_are_independent(tmp_path):
    path = diag_scenario(tmp_path, [("a", 0.5, False, False, 0, 1), ("b", 0.5, False, False, 0, 1)],
                         {"a": {"diagnostic": "CT"}, "b": {"diagnostic": "LAB"}},
                         diagnostics={"CT": 1, "LAB": 1}, doctors=2)
    sim = HospitalSimulator(path)
    sim.step()
    assert {p.patient_id for p in sim.active_patients()} == {"a", "b"}


def test_waiting_time_includes_time_in_diagnostics(tmp_path):
    path = diag_scenario(tmp_path, [("A", 0.5, False, False, 0, 1)],
                         {"A": {"diagnostic": "CT", "diagnostic_duration": 3}}, ticks=10)
    sim = HospitalSimulator(path)
    for _ in range(3):
        sim.step()
    assert sim.patients[0].waiting_time == 3


def test_unknown_or_zero_capacity_modality_is_rejected(tmp_path):
    path = diag_scenario(tmp_path, [("A", 0.5, False, False, 0, 1)], {"A": {"diagnostic": "MRI"}})
    with pytest.raises(ValueError, match="MRI"):
        HospitalSimulator(path)
    path = diag_scenario(tmp_path, [("A", 0.5, False, False, 0, 1)], {"A": {"diagnostic": "CT"}},
                         diagnostics={"CT": 0}, name="T_zero")
    with pytest.raises(ValueError):
        HospitalSimulator(path)


def test_state_summary_reports_diagnostic_queue(tmp_path):
    path = diag_scenario(tmp_path, [("A", 0.5, False, False, 0, 1)], {"A": {"diagnostic": "CT"}})
    assert HospitalSimulator(path).state_summary()["diagnostic_queue"] == 1


def test_diagnostics_delay_admission_end_to_end(tmp_path):
    without = make_scenario(tmp_path, [("A", 0.5, False, False, 0, 2)], ticks=12, name="T_a")
    with_diag = diag_scenario(tmp_path, [("A", 0.5, False, False, 0, 2)],
                              {"A": {"diagnostic": "CT", "diagnostic_duration": 3}}, ticks=12, name="T_b")
    r0 = run_simulation(without, get_allocator("baseline"))
    r1 = run_simulation(with_diag, get_allocator("baseline"))
    assert r0["completed"] == r1["completed"] == 1
    assert r1["metrics"]["average_waiting_time"] == r0["metrics"]["average_waiting_time"] + 3
    assert max(t["diagnostic_queue"] for t in r1["timeline"]) == 1


@pytest.mark.parametrize("algorithm", ["baseline", "fuzzy", "pso", "decentralized"])
def test_s8_clinical_scenario_runs_with_every_algorithm(algorithm):
    r = run_simulation(scenario_path("S8"), get_allocator(algorithm))
    assert r["completed"] == r["total_patients"] == 40
    assert max(t["diagnostic_queue"] for t in r["timeline"]) > 1  # the queue is actually exercised
