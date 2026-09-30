def calculate_fitness(metrics):
    """
    Overall pandemic hospital coordination fitness.

    Higher = better.

    Objectives:
        Critical coverage        40%
        Treatment / throughput   25%
        Resource utilization     15%

    Penalties:
        Waiting time             10%
        Resource conflicts       10%
    """

    waiting_normalized = min(
        metrics["average_waiting_time"] / 20.0,
        1.0
    )

    fitness = (

        0.40
        * metrics["critical_coverage"]

        + 0.25
        * metrics["treatment_rate"]

        + 0.15
        * metrics["resource_utilization"]

        - 0.10
        * waiting_normalized

        - 0.10
        * metrics["conflict_rate"]
    )

    return round(
        fitness,
        4
    )