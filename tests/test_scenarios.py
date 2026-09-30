from pathlib import Path

from simulation.hospital import HospitalSimulator


SCENARIO_DIR = Path("data/scenarios")


SCENARIOS = [
    "S1_normal.json",
    "S2_patient_surge.json",
    "S3_icu_shortage.json",
    "S4_oxygen_shortage.json",
    "S5_pandemic_crisis.json",
]


def test_all_declared_scenarios_exist():
    for filename in SCENARIOS:
        path = SCENARIO_DIR / filename
        assert path.exists(), f"Missing scenario: {filename}"


def test_all_scenarios_load_successfully():
    for filename in SCENARIOS:
        simulator = HospitalSimulator(
            SCENARIO_DIR / filename
        )

        assert simulator.scenario_id
        assert simulator.max_ticks > 0
        assert len(simulator.patients) > 0
        assert len(simulator.doctors) > 0


def test_all_scenarios_have_valid_resource_capacities():
    for filename in SCENARIOS:
        simulator = HospitalSimulator(
            SCENARIO_DIR / filename
        )

        assert simulator.icu_beds >= 0
        assert simulator.ward_beds >= 0
        assert simulator.oxygen >= 0
        assert simulator.ventilators >= 0


def test_all_scenarios_can_advance_simulation():
    for filename in SCENARIOS:
        simulator = HospitalSimulator(
            SCENARIO_DIR / filename
        )

        initial_time = simulator.time

        simulator.step()

        assert simulator.time == initial_time + 1


def test_all_scenarios_have_non_negative_patient_attributes():
    for filename in SCENARIOS:
        simulator = HospitalSimulator(
            SCENARIO_DIR / filename
        )

        for patient in simulator.patients:
            assert 0.0 <= patient.severity <= 1.0
            assert patient.arrival_time >= 0
            assert patient.service_duration > 0