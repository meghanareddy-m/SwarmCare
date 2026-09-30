from algorithms.common import allocate_in_order


def priority_score(patient):
    """Baseline priority rule.

    Higher severity gets priority; waiting time is a small secondary factor.
    """
    normalized_wait = min(patient.waiting_time / 20.0, 1.0)
    return 0.8 * patient.severity + 0.2 * normalized_wait


def greedy_allocate(simulator):
    """Attempt 1: deterministic greedy allocation.

    Patients are sorted by ``priority_score`` and admitted when a doctor and
    ALL required resources are available. Admitted patients stay in treatment
    for ``service_duration`` ticks.
    """
    patients = sorted(simulator.active_patients(), key=priority_score, reverse=True)
    return allocate_in_order(simulator, patients)
