from pathlib import Path
from simulation.hospital import HospitalSimulator
SCENARIO = Path("data/scenarios/S5_pandemic_crisis.json")


def test_scenario_loads():
    simulator = HospitalSimulator(SCENARIO)
    assert simulator.scenario_id == "S5_pandemic_crisis"
    assert simulator.max_ticks == 80
    assert len(simulator.patients) > 0
    assert len(simulator.doctors) > 0


def test_initial_resources_are_valid():
    simulator = HospitalSimulator(SCENARIO)
    assert simulator.icu_beds >= 0
    assert simulator.ward_beds >= 0
    assert simulator.oxygen >= 0
    assert simulator.ventilators >= 0
    assert len(simulator.diagnostics) > 0


def test_active_patients_respect_arrival_time():
    simulator = HospitalSimulator(SCENARIO)
    simulator.time = 0
    active = simulator.active_patients()
    for patient in active:
        assert patient.arrival_time <= simulator.time
        assert not patient.treated


def test_simulation_advances():
    simulator = HospitalSimulator(SCENARIO)
    initial_time = simulator.time
    simulator.step()
    assert simulator.time == initial_time + 1


def test_patient_waiting_time_increases():
    simulator = HospitalSimulator(SCENARIO)
    simulator.time = 20
    active_before = simulator.active_patients()
    waiting_before = {
        patient.patient_id: patient.waiting_time
        for patient in active_before
    }
    simulator.step()
    for patient in simulator.active_patients():
        if patient.patient_id in waiting_before:
            assert patient.waiting_time == (
                waiting_before[patient.patient_id] + 1
            )

def test_resource_reduction_event_never_creates_negative_capacity():
    simulator = HospitalSimulator(SCENARIO)
    for _ in range(simulator.max_ticks):
        simulator.step()
        assert simulator.icu_beds >= 0
        assert simulator.ward_beds >= 0
        assert simulator.oxygen >= 0
        assert simulator.ventilators >= 0