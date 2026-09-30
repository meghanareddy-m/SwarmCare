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

# ======================================================================
# Extended, timeline-based metrics
#
# ``calculate_final_metrics`` above works on the end state of a run and feeds
# the fitness function; it is intentionally unchanged. The functions below need
# the per-tick ``timeline`` recorded by ``experiments.runner.run_simulation``.
# Each timeline entry is a dict with (at least):
#   time, queue (waiting before the decision), queue_after, and for every
#   resource r in RESOURCES: ``<r>_used`` and ``<r>_cap`` after the decision;
#   ``events``: list of event dicts applied at that tick.
# They are pure functions of these inputs and do not affect fitness.
# ======================================================================

RESOURCES = ("doctors", "icu", "ward", "oxygen", "ventilators")
DEFAULT_LATENCY_BUDGET_MS = 50.0


def icu_saturation(timeline):
    """How often the ICU was full.

    ``saturation``: share of ticks with ICU occupancy >= current ICU capacity
    (a capacity of 0 after a shock counts as saturated).
    ``peak_utilization``: maximum occupancy / capacity over ticks with capacity > 0.
    ``saturated_with_queue``: share of ticks that were saturated while patients
    were still waiting after the decision.
    """
    n = len(timeline)
    if n == 0:
        return {"saturation": 0.0, "peak_utilization": 0.0, "saturated_with_queue": 0.0}
    sat = [t for t in timeline if t["icu_used"] >= t["icu_cap"]]
    peak = max((t["icu_used"] / t["icu_cap"] for t in timeline if t["icu_cap"] > 0), default=0.0)
    return {
        "saturation": len(sat) / n,
        "peak_utilization": min(peak, 1.0) if peak else 0.0,
        "saturated_with_queue": sum(1 for t in sat if t["queue_after"] > 0) / n,
    }


def recovery_time(timeline):
    """Ticks the waiting queue needs to return to its pre-shock length.

    One entry per event in the timeline (``patient_surge`` included). For an
    event applied at tick ``s`` the reference is the queue length at ``s - 1``
    (0 if ``s`` is the first tick). The queue is followed from ``s``: if it never
    exceeds the reference the recovery time is 0; otherwise it is the number of
    ticks from ``s`` until the queue first drops back to the reference after its
    peak, or ``None`` if that never happens within the horizon.

    Returns ``{"shocks": [...], "mean_recovery": float|None, "unrecovered": int}``.
    Overlapping shocks are not separated: a later shock can delay recovery from
    an earlier one, which is reported as is.
    """
    queue = [t["queue"] for t in timeline]
    shocks = []
    for idx, tick in enumerate(timeline):
        for event in tick.get("events", []):
            ref = queue[idx - 1] if idx > 0 else 0
            post = queue[idx:]
            peak_at = max(range(len(post)), key=lambda j: (post[j], -j))
            if post[peak_at] <= ref:
                rec = 0
            else:
                rec = next((j for j in range(peak_at + 1, len(post)) if post[j] <= ref), None)
            shocks.append({
                "time": tick["time"], "type": event["type"],
                "pre_queue": ref, "peak_queue": post[peak_at],
                "recovery_ticks": rec,
            })
    rec_vals = [s["recovery_ticks"] for s in shocks if s["recovery_ticks"] is not None]
    return {
        "shocks": shocks,
        "mean_recovery": (sum(rec_vals) / len(rec_vals)) if rec_vals else None,
        "unrecovered": sum(1 for s in shocks if s["recovery_ticks"] is None),
    }


def bottleneck(timeline):
    """Which resource limits admissions.

    Over ticks where patients were still waiting after the decision, count how
    often each resource was saturated (used >= capacity). ``resource`` is the
    most frequently saturated one (ties broken by ``RESOURCES`` order), ``None``
    if nobody ever waited; ``shares`` maps every resource to its saturated share
    of those ticks. Saturation is a snapshot: a patient may also be blocked by
    a resource that is not full but is needed in combination with another.
    """
    waiting = [t for t in timeline if t["queue_after"] > 0]
    if not waiting:
        return {"resource": None, "shares": {r: 0.0 for r in RESOURCES}, "ticks_with_queue": 0}
    shares = {
        r: sum(1 for t in waiting if t[f"{r}_used"] >= t[f"{r}_cap"]) / len(waiting)
        for r in RESOURCES
    }
    top = max(RESOURCES, key=lambda r: (shares[r], -RESOURCES.index(r)))
    return {"resource": top, "shares": shares, "ticks_with_queue": len(waiting)}


def latency_budget(latencies_s, budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    """Compare per-decision latencies (seconds) with a budget (milliseconds).

    ``within_budget``: share of decisions at or below the budget;
    ``meets_budget``: True when the 95th percentile is within the budget.
    Latencies are wall-clock and machine dependent.
    """
    if budget_ms <= 0:
        raise ValueError("budget_ms must be positive")
    ms = sorted(1000.0 * x for x in latencies_s)
    if not ms:
        return {"budget_ms": budget_ms, "within_budget": 1.0, "violations": 0,
                "mean_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0, "meets_budget": True}
    p95 = ms[min(len(ms) - 1, int(0.95 * len(ms)))]
    return {
        "budget_ms": budget_ms,
        "within_budget": sum(1 for x in ms if x <= budget_ms) / len(ms),
        "violations": sum(1 for x in ms if x > budget_ms),
        "mean_ms": sum(ms) / len(ms),
        "p95_ms": p95,
        "max_ms": ms[-1],
        "meets_budget": p95 <= budget_ms,
    }


def critical_patient_outcomes(simulator, threshold=0.80):
    """Waiting statistics of critical patients (severity >= ``threshold``).

    Critical *coverage* saturates at 100 % in every bundled scenario, so the
    time critical patients wait is the more discriminating measure.
    """
    crit = [p for p in simulator.patients
            if p.arrival_time < simulator.max_ticks and p.severity >= threshold]
    others = [p for p in simulator.patients
              if p.arrival_time < simulator.max_ticks and p.severity < threshold]
    waits = [p.waiting_time for p in crit]
    other_waits = [p.waiting_time for p in others]
    return {
        "critical_count": len(crit),
        "critical_completed": sum(p.completed for p in crit),
        "critical_mean_wait": sum(waits) / len(waits) if waits else 0.0,
        "critical_max_wait": max(waits) if waits else 0,
        "noncritical_mean_wait": sum(other_waits) / len(other_waits) if other_waits else 0.0,
    }


def calculate_extended_metrics(timeline, latencies_s, budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    """Bundle of the four timeline metrics used by the runner and dashboard."""
    return {
        "icu_saturation": icu_saturation(timeline),
        "recovery_time": recovery_time(timeline),
        "bottleneck": bottleneck(timeline),
        "latency_budget": latency_budget(latencies_s, budget_ms),
    }
