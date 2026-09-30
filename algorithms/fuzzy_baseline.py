from algorithms.common import allocate_in_order
from algorithms.fuzzy_priority import fuzzy_priority


def fuzzy_allocate(simulator):
    """Attempt 2: fuzzy-priority allocation.

    The admission mechanism is identical to Attempt 1; only the patient
    ordering changes: severity, waiting time and oxygen requirement are fed
    through a fuzzy rule base (see ``fuzzy_priority``) to obtain a priority.
    """
    patients = sorted(simulator.active_patients(), key=fuzzy_priority, reverse=True)
    return allocate_in_order(simulator, patients)
