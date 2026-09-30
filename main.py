from pathlib import Path
import time

from simulation.hospital import HospitalSimulator

from algorithms.baseline import greedy_allocate
from algorithms.fuzzy_baseline import fuzzy_allocate

from evaluation.metrics import calculate_final_metrics
from evaluation.fitness import calculate_fitness
from algorithms.pso import PatientPSO
from algorithms.pso_allocator import pso_allocate

SCENARIO = Path(
    "data/scenarios/S3_icu_shortage.json"
)


def run_experiment(
    experiment_name,
    allocation_function
):

    simulator = HospitalSimulator(
        SCENARIO
    )

    start_time = time.perf_counter()

    fitness_history = []

    while simulator.time < simulator.max_ticks:

        simulator.apply_events()

        allocation = allocation_function(
            simulator
        )

        simulator.step()

    final_metrics = calculate_final_metrics(
        simulator
    )

    final_fitness = calculate_fitness(
        final_metrics
    )

    runtime = (
        time.perf_counter()
        - start_time
    )

    return {
        "name": experiment_name,

        "fitness":
            final_fitness,

        "runtime":
            runtime,

        "metrics":
            final_metrics,

        "treated":
            sum(
                p.completed
                for p in simulator.patients
            ),

        "conflicts":
            simulator.total_conflicts
    }


def print_result(result):

    print()
    print("=" * 70)

    print(
        result["name"]
    )

    print("=" * 70)

    print(
        f"Final Fitness      : "
        f"{result['fitness']:.4f}"
    )

    print(
        f"Patients Treated   : "
        f"{result['treated']}"
    )

    print(
        f"Total Conflicts    : "
        f"{result['conflicts']}"
    )

    print(
        f"Runtime             : "
        f"{result['runtime']:.6f} seconds"
    )

    print()

    for key, value in result[
        "metrics"
    ].items():

        print(
            f"{key:22s}: "
            f"{value:.4f}"
        )

def run_pso_experiment():

    simulator = HospitalSimulator(
        SCENARIO
    )

    pso = PatientPSO(
        swarm_size=12,
        iterations=15,
        inertia=0.7,
        cognitive=1.4,
        social=1.4,
        seed=42
    )

    start_time = time.perf_counter()
    convergence_history = []
    while simulator.time < simulator.max_ticks:
        simulator.apply_events()
        result = pso_allocate(simulator)
        if not convergence_history:
            convergence_history = result.get(
                "convergence",
                []
            )

        simulator.step()
    final_metrics = calculate_final_metrics(simulator)
    final_fitness = calculate_fitness(final_metrics)
    runtime = (time.perf_counter()- start_time)

    return {

        "name":
            "ATTEMPT 3 - PSO SWARM",

        "fitness":
            final_fitness,

        "runtime":
            runtime,

        "metrics":
            final_metrics,

        "treated":
            sum(
                p.completed
                for p in simulator.patients
            ),

        "conflicts":
            simulator.total_conflicts,

        "convergence":
            convergence_history,

        "pso_parameters": {

            "swarm_size": 12,

            "iterations": 15,

            "inertia": 0.7,

            "cognitive": 1.4,

            "social": 1.4,

            "seed": 42
        }
    }


def main():

    print("=" * 70)

    print(
        "SWARMCARE "
        "COMPUTATIONAL INTELLIGENCE EXPERIMENT"
    )

    print("=" * 70)

    print()

    print(f"Scenario: {SCENARIO.stem}")

    print(
        "Seed: 42"
    )

    print(
        "Simulation ticks: 80"
    )

    # ATTEMPT 1

    baseline_result = run_experiment(
        "ATTEMPT 1 - GREEDY BASELINE",
        greedy_allocate
    )

    print_result(
        baseline_result
    )

    print()

    print(
        "What changed and why:"
    )

    print(
        "Established a deterministic "
        "severity-first greedy baseline."
    )

    # ATTEMPT 2

    fuzzy_result = run_experiment(
        "ATTEMPT 2 - FUZZY PRIORITY",
        fuzzy_allocate
    )

    print_result(
        fuzzy_result
    )

    print()

    print(
        "What changed and why:"
    )

    print(
        "Replaced fixed severity ranking "
        "with fuzzy reasoning using severity, "
        "waiting time and oxygen requirement."
    )

        # --------------------------------------------------
    # ATTEMPT 3
    # --------------------------------------------------

    pso_result = run_pso_experiment()

    print_result(
        pso_result
    )

    print()

    print(
        "PSO Parameters:"
    )

    for key, value in pso_result[
        "pso_parameters"
    ].items():

        print(
            f"{key:15s}: {value}"
        )

    print()

    print(
        "What changed and why:"
    )

    print(
        "Replaced single-rule patient ordering "
        "with particle-swarm search over candidate "
        "allocation priorities to improve system-level "
        "resource coordination."
    )

    print()

    print(
        "PSO convergence:"
    )

    convergence = pso_result[
        "convergence"
    ]

    if convergence:

        print(
            f"Initial best: "
            f"{convergence[0]:.4f}"
        )

        print(
            f"Final best:   "
            f"{convergence[-1]:.4f}"
        )

        print(
            f"Iterations:   "
            f"{len(convergence)}"
        )

    # COMPARISON

    baseline_fitness = baseline_result["fitness"]
    fuzzy_fitness = fuzzy_result["fitness"]
    pso_fitness = pso_result["fitness"]
    fuzzy_improvement = ((fuzzy_fitness - baseline_fitness)/ max(abs(baseline_fitness), 1e-9)) * 100
    pso_improvement = ((pso_fitness - baseline_fitness)/ max(abs(baseline_fitness), 1e-9)) * 100
    print()
    print("=" * 70)
    print("ATTEMPT COMPARISON")
    print("=" * 70)
    print(f"Baseline fitness : {baseline_fitness:.4f}")
    print(f"Fuzzy fitness    : {fuzzy_fitness:.4f}")
    print(f"PSO fitness : {pso_fitness:.4f}")
    print(f"Fuzzy improvement : {fuzzy_improvement:+.2f}%")
    print(f"PSO improvement  : {pso_improvement:+.2f}%")

if __name__ == "__main__":
    main()