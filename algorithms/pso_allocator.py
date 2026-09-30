from algorithms.common import allocate_in_order
from algorithms.pso import PatientPSO

DEFAULT_PSO_PARAMS = {
    "swarm_size": 12,
    "iterations": 15,
    "inertia": 0.7,
    "cognitive": 1.4,
    "social": 1.4,
}


def make_pso_allocator(base_seed=42, **overrides):
    """Return an allocation function that runs PSO every tick.

    The PSO seed of a tick is ``base_seed + simulator.time`` so that a whole
    simulation is reproducible for a given ``base_seed`` while different ticks
    still explore different random swarms.
    """
    params = {**DEFAULT_PSO_PARAMS, **overrides}

    def allocate(simulator):
        patients = simulator.active_patients()
        if not patients:
            return {"treated": 0, "critical_treated": 0, "resource_conflicts": 0}

        pso = PatientPSO(seed=base_seed + simulator.time, **params)
        order, pso_result = pso.optimize(patients, simulator)

        stats = allocate_in_order(simulator, order)
        stats["pso_fitness"] = pso_result["best_fitness"]
        stats["pso_iterations"] = pso_result["iterations"]
        stats["convergence"] = pso_result["convergence"]
        return stats

    return allocate


def pso_allocate(simulator):
    """Attempt 3 with the default parameters and seed 42."""
    return make_pso_allocator()(simulator)
