"""Shared allocation mechanics used by every ordering-based strategy.

The greedy baseline, the fuzzy allocator and the PSO allocator differ ONLY in
how they order the waiting patients.  The admission rules (which resources a
patient needs, how availability is computed, how conflicts are counted) are
identical and live here so that all strategies are compared on equal terms.
"""

CRITICAL_SEVERITY = 0.80


def needs_icu(patient):
    """A patient needs an ICU bed when severity >= CRITICAL_SEVERITY."""
    return patient.severity >= CRITICAL_SEVERITY


def occupied_resources(simulator):
    """Resources currently held by patients that are in treatment."""
    in_treatment = simulator.treatment_patients()
    return {
        "icu": sum(1 for p in in_treatment if p.assigned_bed == "ICU"),
        "ward": sum(1 for p in in_treatment if p.assigned_bed == "WARD"),
        "oxygen": sum(1 for p in in_treatment if p.oxygen_required),
        "ventilators": sum(1 for p in in_treatment if p.ventilator_required),
    }


def available_resources(simulator):
    """Free capacity per resource type (never negative)."""
    occ = occupied_resources(simulator)
    return {
        "icu": max(0, simulator.icu_beds - occ["icu"]),
        "ward": max(0, simulator.ward_beds - occ["ward"]),
        "oxygen": max(0, simulator.oxygen - occ["oxygen"]),
        "ventilators": max(0, simulator.ventilators - occ["ventilators"]),
    }


def free_doctors(simulator):
    """Doctors that are available and currently idle."""
    return [d for d in simulator.doctors if d.available and d.current_load == 0]


def commit_admission(simulator, patient, doctor, free):
    """Admit ``patient``: update patient/doctor state, counters and ``free``."""
    doctor.current_load += 1
    patient.assigned_doctor = doctor.doctor_id
    patient.treated = True
    patient.remaining_service = patient.service_duration

    if needs_icu(patient):
        free["icu"] -= 1
        patient.assigned_bed = "ICU"
        simulator.total_icu_used += 1
    else:
        free["ward"] -= 1
        patient.assigned_bed = "WARD"
        simulator.total_ward_used += 1

    if patient.oxygen_required:
        free["oxygen"] -= 1
        simulator.total_oxygen_used += 1

    if patient.ventilator_required:
        free["ventilators"] -= 1
        simulator.total_ventilator_used += 1


def can_admit(patient, doctor, free):
    """True if a doctor and every resource the patient needs are available."""
    if doctor is None:
        return False
    if free["icu" if needs_icu(patient) else "ward"] <= 0:
        return False
    if patient.oxygen_required and free["oxygen"] <= 0:
        return False
    if patient.ventilator_required and free["ventilators"] <= 0:
        return False
    return True


def allocate_in_order(simulator, ordered_patients):
    """Walk ``ordered_patients`` and admit each one whose needs can be met.

    Each patient that cannot be admitted counts as exactly one conflict.
    Updates simulator counters and returns a per-tick statistics dict.
    """
    free = available_resources(simulator)
    doctors = free_doctors(simulator)

    treated = []
    conflicts = 0

    for patient in ordered_patients:
        doctor = next((d for d in doctors if d.current_load < d.capacity), None)
        if not can_admit(patient, doctor, free):
            conflicts += 1
            continue
        commit_admission(simulator, patient, doctor, free)
        treated.append(patient)

    simulator.total_conflicts += conflicts
    simulator.total_assignments += len(treated)

    return {
        "treated": len(treated),
        "critical_treated": sum(needs_icu(p) for p in treated),
        "resource_conflicts": conflicts,
        "icu_used": simulator.icu_beds - free["icu"],
        "ward_used": simulator.ward_beds - free["ward"],
        "oxygen_used": simulator.oxygen - free["oxygen"],
        "ventilators_used": simulator.ventilators - free["ventilators"],
    }
