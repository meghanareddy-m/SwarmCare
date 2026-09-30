from algorithms.pso import PatientPSO
def pso_allocate(simulator):
    """
    Attempt 3 allocation.
    PSO determines the ordering of waiting patients.
    The actual hospital resource allocation then follows
    that optimized ordering.
    """
    patients = simulator.active_patients()

    if not patients:

        return {
            "treated": 0,
            "critical_treated": 0,
            "resource_conflicts": 0
        }

    # --------------------------------------------------
    # Run swarm optimization
    # --------------------------------------------------

    pso = PatientPSO(
        swarm_size=12,
        iterations=15,
        inertia=0.7,
        cognitive=1.4,
        social=1.4,
        seed=42 + simulator.time
    )

    order, pso_result = pso.optimize(
        patients,
        simulator
    )
    # --------------------------------------------------
    # Current resource occupation
    # --------------------------------------------------

    occupied_icu = sum(
        1
        for patient
        in simulator.treatment_patients()
        if patient.assigned_bed == "ICU"
    )

    occupied_ward = sum(
        1
        for patient
        in simulator.treatment_patients()
        if patient.assigned_bed == "WARD"
    )

    occupied_oxygen = sum(
        1
        for patient
        in simulator.treatment_patients()
        if patient.oxygen_required
    )

    occupied_ventilators = sum(
        1
        for patient
        in simulator.treatment_patients()
        if patient.ventilator_required
    )

    icu_available = max(
        0,
        simulator.icu_beds
        - occupied_icu
    )

    ward_available = max(
        0,
        simulator.ward_beds
        - occupied_ward
    )

    oxygen_available = max(
        0,
        simulator.oxygen
        - occupied_oxygen
    )

    ventilators_available = max(
        0,
        simulator.ventilators
        - occupied_ventilators
    )

    available_doctors = [

        doctor

        for doctor
        in simulator.doctors

        if doctor.available
        and doctor.current_load == 0
    ]

    treated = []

    conflicts = 0

    # --------------------------------------------------
    # Execute optimized allocation
    # --------------------------------------------------

    for patient in order:

        doctor = next(
            (
                doctor
                for doctor
                in available_doctors
                if doctor.current_load < doctor.capacity
            ),
            None
        )

        if doctor is None:

            conflicts += 1

            continue

        needs_icu = (
            patient.severity >= 0.80
        )

        needs_oxygen = (
            patient.oxygen_required
        )

        needs_ventilator = (
            patient.ventilator_required
        )

        if needs_icu and icu_available <= 0:

            conflicts += 1

            continue

        if (
            not needs_icu
            and ward_available <= 0
        ):

            conflicts += 1

            continue

        if (
            needs_oxygen
            and oxygen_available <= 0
        ):

            conflicts += 1

            continue

        if (
            needs_ventilator
            and ventilators_available <= 0
        ):

            conflicts += 1

            continue

        # ----------------------------------------------
        # Commit
        # ----------------------------------------------

        doctor.current_load += 1

        patient.assigned_doctor = (
            doctor.doctor_id
        )

        patient.treated = True

        patient.remaining_service = (
            patient.service_duration
        )

        if needs_icu:

            icu_available -= 1

            patient.assigned_bed = "ICU"

            simulator.total_icu_used += 1

        else:

            ward_available -= 1

            patient.assigned_bed = "WARD"

            simulator.total_ward_used += 1

        if needs_oxygen:

            oxygen_available -= 1

            simulator.total_oxygen_used += 1

        if needs_ventilator:

            ventilators_available -= 1

            simulator.total_ventilator_used += 1

        treated.append(patient)

    simulator.total_conflicts += conflicts

    simulator.total_assignments += len(
        treated
    )

    return {

        "treated":
            len(treated),

        "critical_treated":
            sum(
                patient.severity >= 0.80
                for patient in treated
            ),

        "resource_conflicts":
            conflicts,

        "pso_fitness":
            pso_result["best_fitness"],

        "pso_iterations":
            pso_result["iterations"],

        "convergence":
            pso_result["convergence"]
    }