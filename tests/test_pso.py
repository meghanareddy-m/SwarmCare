from pathlib import Path

from simulation.hospital import HospitalSimulator
from algorithms.pso import PatientPSO


SCENARIO = Path(
    "data/scenarios/S5_pandemic_crisis.json"
)


def test_pso_empty_patient_set():
    simulator = HospitalSimulator(SCENARIO)

    pso = PatientPSO(
        swarm_size=4,
        iterations=5,
        seed=42
    )

    order, result = pso.optimize([], simulator)

    assert order == []
    assert result["best_fitness"] == 0.0
    assert result["iterations"] == 0
    assert result["convergence"] == []


def test_pso_returns_valid_patient_order():
    simulator = HospitalSimulator(SCENARIO)

    patients = simulator.active_patients()

    pso = PatientPSO(
        swarm_size=4,
        iterations=5,
        seed=42
    )

    order, result = pso.optimize(
        patients,
        simulator
    )

    assert len(order) == len(patients)

    assert {
        patient.patient_id
        for patient in order
    } == {
        patient.patient_id
        for patient in patients
    }


def test_pso_convergence_length_matches_iterations():
    simulator = HospitalSimulator(SCENARIO)

    patients = simulator.active_patients()

    iterations = 5

    pso = PatientPSO(
        swarm_size=4,
        iterations=iterations,
        seed=42
    )

    _, result = pso.optimize(
        patients,
        simulator
    )

    assert result["iterations"] == iterations
    assert len(result["convergence"]) == iterations


def test_pso_convergence_is_non_decreasing():
    simulator = HospitalSimulator(SCENARIO)

    patients = simulator.active_patients()

    pso = PatientPSO(
        swarm_size=4,
        iterations=8,
        seed=42
    )

    _, result = pso.optimize(
        patients,
        simulator
    )

    convergence = result["convergence"]

    for previous, current in zip(
        convergence,
        convergence[1:]
    ):
        assert current >= previous


def test_pso_is_reproducible_with_same_seed():
    simulator1 = HospitalSimulator(SCENARIO)
    simulator2 = HospitalSimulator(SCENARIO)

    patients1 = simulator1.active_patients()
    patients2 = simulator2.active_patients()

    pso1 = PatientPSO(
        swarm_size=4,
        iterations=5,
        seed=42
    )

    pso2 = PatientPSO(
        swarm_size=4,
        iterations=5,
        seed=42
    )

    order1, result1 = pso1.optimize(
        patients1,
        simulator1
    )

    order2, result2 = pso2.optimize(
        patients2,
        simulator2
    )

    assert [
        patient.patient_id
        for patient in order1
    ] == [
        patient.patient_id
        for patient in order2
    ]

    assert result1["best_fitness"] == result2["best_fitness"]
    assert result1["convergence"] == result2["convergence"]


def test_pso_fitness_stays_in_expected_range():
    simulator = HospitalSimulator(SCENARIO)

    patients = simulator.active_patients()

    pso = PatientPSO(
        swarm_size=4,
        iterations=5,
        seed=42
    )

    _, result = pso.optimize(
        patients,
        simulator
    )

    assert -1.0 <= result["best_fitness"] <= 1.0

    for fitness in result["convergence"]:
        assert -1.0 <= fitness <= 1.0