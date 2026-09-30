def priority_score(patient):
    """
    Baseline priority rule.

    Higher severity gets priority.
    Waiting time provides a small secondary effect.
    """

    normalized_wait = min(
        patient.waiting_time / 20.0,
        1.0
    )

    return (
        0.8 * patient.severity
        + 0.2 * normalized_wait
    )


def greedy_allocate(simulator):
    """
    Attempt 1: deterministic greedy allocation.

    Patients are sorted by priority and resources are
    allocated if ALL required resources are available.

    Unlike the original version, patients now remain
    in treatment for several simulation ticks.
    """

    patients = sorted(
        simulator.active_patients(),
        key=priority_score,
        reverse=True
    )

    # --------------------------------------------------
    # Calculate currently occupied resources
    # --------------------------------------------------

    occupied_icu = sum(
        1
        for p in simulator.treatment_patients()
        if p.assigned_bed == "ICU"
    )

    occupied_ward = sum(
        1
        for p in simulator.treatment_patients()
        if p.assigned_bed == "WARD"
    )

    occupied_oxygen = sum(
        1
        for p in simulator.treatment_patients()
        if p.oxygen_required
    )

    occupied_ventilators = sum(
        1
        for p in simulator.treatment_patients()
        if p.ventilator_required
    )

    icu_available = max(
        0,
        simulator.icu_beds - occupied_icu
    )

    ward_available = max(
        0,
        simulator.ward_beds - occupied_ward
    )

    oxygen_available = max(
        0,
        simulator.oxygen - occupied_oxygen
    )

    ventilators_available = max(
        0,
        simulator.ventilators - occupied_ventilators
    )

    available_doctors = [
        doctor
        for doctor in simulator.doctors
        if doctor.available
        and doctor.current_load == 0
    ]

    treated = []
    conflicts = 0

    # --------------------------------------------------
    # Allocate patients
    # --------------------------------------------------

    for patient in patients:

        needs_icu = patient.severity >= 0.80
        needs_oxygen = patient.oxygen_required
        needs_ventilator = patient.ventilator_required

        # ----------------------------------------------
        # Find doctor
        # ----------------------------------------------

        doctor = next(
            (
                d
                for d in available_doctors
                if d.current_load < d.capacity
            ),
            None
        )

        if doctor is None:
            conflicts += 1
            continue

        # ----------------------------------------------
        # Check bed
        # ----------------------------------------------

        if needs_icu:

            if icu_available <= 0:
                conflicts += 1
                continue

        else:

            if ward_available <= 0:
                conflicts += 1
                continue

        # ----------------------------------------------
        # Check oxygen
        # ----------------------------------------------

        if needs_oxygen and oxygen_available <= 0:
            conflicts += 1
            continue

        # ----------------------------------------------
        # Check ventilator
        # ----------------------------------------------

        if needs_ventilator and ventilators_available <= 0:
            conflicts += 1
            continue

        # ==================================================
        # COMMIT ALLOCATION
        # ==================================================

        doctor.current_load += 1

        patient.assigned_doctor = doctor.doctor_id

        patient.treated = True

        patient.remaining_service = (
            patient.service_duration
        )

        # ----------------------------------------------
        # Bed
        # ----------------------------------------------

        if needs_icu:

            icu_available -= 1

            patient.assigned_bed = "ICU"

            simulator.total_icu_used += 1

        else:

            ward_available -= 1

            patient.assigned_bed = "WARD"

            simulator.total_ward_used += 1

        # ----------------------------------------------
        # Oxygen
        # ----------------------------------------------

        if needs_oxygen:

            oxygen_available -= 1

            simulator.total_oxygen_used += 1

        # ----------------------------------------------
        # Ventilator
        # ----------------------------------------------

        if needs_ventilator:

            ventilators_available -= 1

            simulator.total_ventilator_used += 1

        treated.append(patient)

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    simulator.total_conflicts += conflicts

    simulator.total_assignments += len(treated)

    return {

        "treated":
            len(treated),

        "critical_treated":
            sum(
                p.severity >= 0.80
                for p in treated
            ),

        "resource_conflicts":
            conflicts,

        "icu_used":
            simulator.icu_beds
            - icu_available,

        "ward_used":
            simulator.ward_beds
            - ward_available,

        "oxygen_used":
            simulator.oxygen
            - oxygen_available,

        "ventilators_used":
            simulator.ventilators
            - ventilators_available
    }