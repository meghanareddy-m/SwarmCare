from algorithms.fuzzy_priority import fuzzy_priority


def fuzzy_allocate(simulator):
    """
    Attempt 2: fuzzy-priority allocation.

    The resource allocation mechanism remains the same
    as Attempt 1.

    The difference is the patient ordering.

    Instead of:

        fixed severity rule

    we use:

        fuzzy severity
        + waiting time
        + oxygen requirement
        -> priority
    """

    patients = sorted(
        simulator.active_patients(),
        key=fuzzy_priority,
        reverse=True
    )

    # --------------------------------------------------
    # Currently occupied resources
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
    # Allocate
    # --------------------------------------------------

    for patient in patients:

        needs_icu = patient.severity >= 0.80

        needs_oxygen = patient.oxygen_required

        needs_ventilator = (
            patient.ventilator_required
        )

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
        # Check all resources BEFORE allocation
        # ----------------------------------------------

        if needs_icu and icu_available <= 0:
            conflicts += 1
            continue

        if not needs_icu and ward_available <= 0:
            conflicts += 1
            continue

        if needs_oxygen and oxygen_available <= 0:
            conflicts += 1
            continue

        if (
            needs_ventilator
            and ventilators_available <= 0
        ):
            conflicts += 1
            continue

        # ==================================================
        # COMMIT
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