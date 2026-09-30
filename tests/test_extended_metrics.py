"""Item 5: icu_saturation, recovery_time, bottleneck, latency budget (+ critical outcomes)."""
import pytest

from algorithms.baseline import greedy_allocate
from evaluation.metrics import (DEFAULT_LATENCY_BUDGET_MS, RESOURCES, bottleneck,
                                calculate_extended_metrics, critical_patient_outcomes,
                                icu_saturation, latency_budget, recovery_time)
from experiments.runner import get_allocator, run_simulation, scenario_path
from simulation.hospital import HospitalSimulator
from tests.helpers import make_scenario


def tick(time, queue=0, queue_after=None, events=(), **used_cap):
    """Timeline entry; every resource defaults to 0 used of 10."""
    t = {"time": time, "queue": queue, "queue_after": queue if queue_after is None else queue_after,
         "events": list(events)}
    for r in RESOURCES:
        t[f"{r}_used"], t[f"{r}_cap"] = 0, 10
    for key, value in used_cap.items():
        t[key] = value
    return t


# ------------------------------------------------------------ icu_saturation

def test_icu_saturation_share_peak_and_queue():
    tl = [tick(0, icu_used=10), tick(1, icu_used=5), tick(2, icu_used=10, queue_after=3), tick(3, icu_used=0)]
    m = icu_saturation(tl)
    assert m["saturation"] == pytest.approx(0.5)
    assert m["peak_utilization"] == pytest.approx(1.0)
    assert m["saturated_with_queue"] == pytest.approx(0.25)


def test_icu_with_zero_capacity_counts_as_saturated_and_is_not_a_division_error():
    tl = [tick(0, icu_used=0, icu_cap=0), tick(1, icu_used=4, icu_cap=8)]
    m = icu_saturation(tl)
    assert m["saturation"] == pytest.approx(0.5)
    assert m["peak_utilization"] == pytest.approx(0.5)


def test_icu_saturation_empty_timeline():
    assert icu_saturation([]) == {"saturation": 0.0, "peak_utilization": 0.0, "saturated_with_queue": 0.0}


# ------------------------------------------------------------- recovery_time

EVENT = {"type": "oxygen_reduction", "time": 2}


def test_recovery_time_counts_ticks_until_queue_returns_to_reference():
    q = [1, 1, 5, 4, 3, 1, 0, 0]  # shock at index 2, reference = queue[1] = 1
    tl = [tick(i, queue=v, events=[EVENT] if i == 2 else []) for i, v in enumerate(q)]
    out = recovery_time(tl)
    assert out["shocks"] == [{"time": 2, "type": "oxygen_reduction", "pre_queue": 1,
                              "peak_queue": 5, "recovery_ticks": 3}]
    assert out["mean_recovery"] == 3 and out["unrecovered"] == 0


def test_recovery_time_zero_when_queue_never_rises():
    tl = [tick(i, queue=v, events=[EVENT] if i == 2 else []) for i, v in enumerate([3, 3, 3, 2, 2])]
    assert recovery_time(tl)["shocks"][0]["recovery_ticks"] == 0


def test_recovery_time_none_when_queue_never_returns():
    tl = [tick(i, queue=v, events=[EVENT] if i == 1 else []) for i, v in enumerate([0, 5, 6, 7, 7])]
    out = recovery_time(tl)
    assert out["shocks"][0]["recovery_ticks"] is None
    assert out["mean_recovery"] is None and out["unrecovered"] == 1


def test_recovery_time_without_events():
    out = recovery_time([tick(0), tick(1)])
    assert out == {"shocks": [], "mean_recovery": None, "unrecovered": 0}


def test_recovery_time_event_on_first_tick_uses_zero_reference():
    tl = [tick(i, queue=v, events=[EVENT] if i == 0 else []) for i, v in enumerate([4, 2, 0, 0])]
    assert recovery_time(tl)["shocks"][0]["recovery_ticks"] == 2


# ---------------------------------------------------------------- bottleneck

def test_bottleneck_picks_most_often_saturated_resource_during_queueing():
    tl = [tick(0, queue_after=2, doctors_used=10, oxygen_used=10),
          tick(1, queue_after=1, doctors_used=10),
          tick(2, queue_after=0, icu_used=10, ward_used=10)]  # no queue -> ignored
    b = bottleneck(tl)
    assert b["resource"] == "doctors"
    assert b["shares"]["doctors"] == 1.0 and b["shares"]["oxygen"] == 0.5 and b["shares"]["icu"] == 0.0
    assert b["ticks_with_queue"] == 2


def test_bottleneck_none_without_queue():
    b = bottleneck([tick(0), tick(1)])
    assert b["resource"] is None and b["ticks_with_queue"] == 0
    assert set(b["shares"]) == set(RESOURCES)


def test_bottleneck_ties_break_in_resource_order():
    tl = [tick(0, queue_after=1, doctors_used=10, icu_used=10)]
    assert bottleneck(tl)["resource"] == "doctors"


# ------------------------------------------------------------ latency budget

def test_latency_budget_shares_and_percentile():
    lat = [0.001] * 19 + [0.2]  # 19 x 1 ms and one 200 ms outlier
    m = latency_budget(lat, budget_ms=50)
    assert m["within_budget"] == pytest.approx(0.95) and m["violations"] == 1
    assert m["max_ms"] == pytest.approx(200) and m["mean_ms"] == pytest.approx(10.95)
    assert m["p95_ms"] == pytest.approx(200) and m["meets_budget"] is False


def test_latency_budget_met_when_p95_inside():
    m = latency_budget([0.002] * 100, budget_ms=5)
    assert m["meets_budget"] is True and m["within_budget"] == 1.0


def test_latency_budget_empty_and_invalid():
    assert latency_budget([])["meets_budget"] is True
    assert latency_budget([])["budget_ms"] == DEFAULT_LATENCY_BUDGET_MS
    with pytest.raises(ValueError):
        latency_budget([0.001], budget_ms=0)


# -------------------------------------------------------- critical outcomes

def test_critical_patient_outcomes(tmp_path):
    path = make_scenario(tmp_path, [("C", 0.9, False, False, 0, 3), ("D", 0.95, False, False, 0, 3),
                                    ("N", 0.3, False, False, 0, 1)], doctors=1, icu=1, ticks=15)
    sim = HospitalSimulator(path)
    while sim.time < sim.max_ticks:
        sim.apply_events(); greedy_allocate(sim); sim.step()
    c = critical_patient_outcomes(sim)
    assert c["critical_count"] == 2 and c["critical_completed"] == 2
    assert c["critical_max_wait"] == 3 and c["critical_mean_wait"] == pytest.approx(1.5)
    assert c["noncritical_mean_wait"] == pytest.approx(6.0)


# ------------------------------------------------------ runner integration

@pytest.mark.parametrize("algorithm", ["baseline", "decentralized"])
def test_run_simulation_records_timeline_and_extended_metrics(algorithm):
    r = run_simulation(scenario_path("S5"), get_allocator(algorithm))
    tl = r["timeline"]
    assert len(tl) == 80 and [t["time"] for t in tl] == list(range(80))
    assert [t["queue"] for t in tl] == r["queue_length"]
    assert sorted(e["time"] for t in tl for e in t["events"]) == [25, 40, 50, 60, 70]
    for t in tl:  # occupancy consistent with capacity unless a shock removed capacity
        assert 0 <= t["queue_after"] <= t["queue"]
    ext = r["extended"]
    assert set(ext) == {"icu_saturation", "recovery_time", "bottleneck", "latency_budget"}
    assert ext["bottleneck"]["resource"] == "doctors"  # S5: doctors bind (docs/RESULTS.md)
    assert len(ext["recovery_time"]["shocks"]) == 5
    assert ext["latency_budget"]["budget_ms"] == DEFAULT_LATENCY_BUDGET_MS
    assert len(r["decisions"]) == 80
    assert sum(len(d["admitted"]) for d in r["decisions"]) == r["assignments"]


def test_decisions_report_deferred_patients_and_agent_messages():
    r = run_simulation(scenario_path("S1"), get_allocator("decentralized"))
    first = r["decisions"][0]
    assert first["deferred"] == first["queue"] - len(first["admitted"]) > 0
    assert first["messages"] > 0 and first["rounds"] >= 1


def test_extended_metrics_do_not_change_fitness_inputs():
    """calculate_final_metrics still exposes exactly the original seven metrics."""
    r = run_simulation(scenario_path("S1"), get_allocator("baseline"))
    assert set(r["metrics"]) == {"treatment_rate", "critical_coverage", "average_waiting_time",
                                 "conflict_rate", "resource_utilization", "resource_wastage",
                                 "throughput"}


def test_calculate_extended_metrics_bundle():
    out = calculate_extended_metrics([tick(0, icu_used=10)], [0.001], budget_ms=10)
    assert out["icu_saturation"]["saturation"] == 1.0
    assert out["latency_budget"]["budget_ms"] == 10
