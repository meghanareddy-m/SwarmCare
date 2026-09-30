def calculate_final_metrics(simulator):

    arrived = [
        patient
        for patient in simulator.patients
        if patient.arrival_time < simulator.max_ticks
    ]

    completed = [
        patient
        for patient in arrived
        if patient.completed
    ]

    critical = [
        patient
        for patient in arrived
        if patient.severity >= 0.80
    ]

    critical_completed = [
        patient
        for patient in critical
        if patient.completed
    ]

    # --------------------------------------------------
    # Treatment rate
    # --------------------------------------------------

    treatment_rate = (
        len(completed)
        / max(len(arrived), 1)
    )

    # --------------------------------------------------
    # Critical coverage
    # --------------------------------------------------

    critical_coverage = (
        len(critical_completed)
        / max(len(critical), 1)
    )

    # --------------------------------------------------
    # Waiting time
    # --------------------------------------------------

    average_waiting_time = (
        sum(
            patient.waiting_time
            for patient in arrived
        )
        / max(len(arrived), 1)
    )

    # --------------------------------------------------
    # Conflict rate
    #
    # Normalize conflicts against the number of
    # allocation attempts rather than simply capping
    # everything at 1.0.
    # --------------------------------------------------

    total_attempts = (
        simulator.total_assignments
        + simulator.total_conflicts
    )

    conflict_rate = (
        simulator.total_conflicts
        / max(total_attempts, 1)
    )

    # --------------------------------------------------
    # Resource utilization
    # --------------------------------------------------

    initial = simulator.config["hospital"]

    total_capacity = (

        initial["icu_beds"]

        + initial["ward_beds"]

        + initial["oxygen_units"]

        + initial["ventilators"]
    )

    total_used = (

        simulator.total_icu_used

        + simulator.total_ward_used

        + simulator.total_oxygen_used

        + simulator.total_ventilator_used
    )

    resource_utilization = min(

        total_used
        / max(total_capacity, 1),

        1.0
    )

    resource_wastage = (
        1.0
        - resource_utilization
    )

    # --------------------------------------------------
    # Normalized throughput
    #
    # We normalize against the maximum number of
    # patients that could theoretically be completed.
    # --------------------------------------------------

    throughput = min(

        len(completed)
        / max(
            len(arrived),
            1
        ),

        1.0
    )

    return {

        "treatment_rate":
            treatment_rate,

        "critical_coverage":
            critical_coverage,

        "average_waiting_time":
            average_waiting_time,

        "conflict_rate":
            conflict_rate,

        "resource_utilization":
            resource_utilization,

        "resource_wastage":
            resource_wastage,

        "throughput":
            throughput
    }