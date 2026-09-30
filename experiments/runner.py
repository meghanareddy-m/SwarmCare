"""Benchmark harness: run allocation strategies on scenarios and collect results."""

import csv
import json
import statistics
import time
from pathlib import Path

from algorithms.baseline import greedy_allocate
from algorithms.decentralized import make_decentralized_allocator
from algorithms.fuzzy_baseline import fuzzy_allocate
from algorithms.pso_allocator import make_pso_allocator
from evaluation.fitness import calculate_fitness
from algorithms.common import occupied_resources
from evaluation.metrics import (DEFAULT_LATENCY_BUDGET_MS, calculate_extended_metrics,
                                calculate_final_metrics, critical_patient_outcomes)
from simulation.hospital import HospitalSimulator

SCENARIO_DIR = Path("data/scenarios")
DEFAULT_SCENARIO = "S5_pandemic_crisis"

ALGORITHM_LABELS = {
    "baseline": "Attempt 1 - Greedy baseline",
    "fuzzy": "Attempt 2 - Fuzzy priority",
    "pso": "Attempt 3 - PSO swarm",
    "decentralized": "Attempt 4 - Decentralized negotiation",
}
STOCHASTIC = {"pso"}


def list_scenarios(directory=SCENARIO_DIR):
    """Scenario ids (file stems) sorted by name."""
    return sorted(p.stem for p in Path(directory).glob("*.json"))


def scenario_path(name, directory=SCENARIO_DIR):
    """Resolve 'S5', 'S5_pandemic_crisis' or a file path to a scenario file."""
    direct = Path(name)
    if direct.suffix == ".json" and direct.exists():
        return direct
    matches = [s for s in list_scenarios(directory) if s == name or s.startswith(name + "_")]
    if len(matches) != 1:
        raise ValueError(
            f"Unknown or ambiguous scenario '{name}'. Available: {', '.join(list_scenarios(directory))}"
        )
    return Path(directory) / f"{matches[0]}.json"


def get_allocator(algorithm, seed=42):
    if algorithm == "baseline":
        return greedy_allocate
    if algorithm == "fuzzy":
        return fuzzy_allocate
    if algorithm == "pso":
        return make_pso_allocator(base_seed=seed)
    if algorithm == "decentralized":
        return make_decentralized_allocator()
    raise ValueError(f"Unknown algorithm '{algorithm}'")


def _snapshot(simulator, queue_before, queue_after, diagnostic_queue, events):
    """Resource occupancy and capacity after one allocation decision."""
    occ = occupied_resources(simulator)
    return {
        "time": simulator.time,
        "queue": queue_before,
        "queue_after": queue_after,
        "diagnostic_queue": diagnostic_queue,
        "doctors_used": len(simulator.treatment_patients()),
        "doctors_cap": sum(d.available for d in simulator.doctors),
        "icu_used": occ["icu"], "icu_cap": simulator.icu_beds,
        "ward_used": occ["ward"], "ward_cap": simulator.ward_beds,
        "oxygen_used": occ["oxygen"], "oxygen_cap": simulator.oxygen,
        "ventilators_used": occ["ventilators"], "ventilators_cap": simulator.ventilators,
        "events": [dict(e) for e in events],
    }


def _decision(simulator, admitted, queue_before, allocation):
    """What the allocator decided this tick (algorithm independent)."""
    record = {
        "time": simulator.time,
        "queue": queue_before,
        "admitted": [
            {"id": p.patient_id, "severity": p.severity, "bed": p.assigned_bed,
             "oxygen": p.oxygen_required, "ventilator": p.ventilator_required}
            for p in admitted
        ],
        "deferred": queue_before - len(admitted),
    }
    for key in ("messages", "rounds", "reserve_blocked", "agent_messages"):
        if key in allocation:
            record[key] = allocation[key]
    return record


def run_simulation(path, allocator, latency_budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    """Run one full simulation.

    Returns final metrics, fitness, latency statistics, the per-tick
    ``timeline`` and ``decisions`` (used by the dashboard), and the extended
    metrics (ICU saturation, recovery time, bottleneck, latency budget).
    """
    simulator = HospitalSimulator(path)
    tick_latencies = []
    queue_length = []
    timeline = []
    decisions = []
    messages = 0
    convergence = []

    start = time.perf_counter()
    while simulator.time < simulator.max_ticks:
        first_event = simulator.event_index
        simulator.apply_events()
        events_now = simulator.events[first_event:simulator.event_index]
        queue_before = len(simulator.active_patients())
        queue_length.append(queue_before)
        was_treated = {p.patient_id for p in simulator.patients if p.treated}
        t0 = time.perf_counter()
        allocation = allocator(simulator)
        tick_latencies.append(time.perf_counter() - t0)
        admitted = [p for p in simulator.patients
                    if p.treated and p.patient_id not in was_treated]
        messages += allocation.get("messages", 0)
        if not convergence and allocation.get("convergence"):
            convergence = list(allocation["convergence"])
        timeline.append(_snapshot(simulator, queue_before, queue_before - len(admitted),
                                  len(simulator.diagnostic_queue()), events_now))
        decisions.append(_decision(simulator, admitted, queue_before, allocation))
        simulator.step()
    runtime = time.perf_counter() - start

    metrics = calculate_final_metrics(simulator)
    return {
        "scenario": simulator.scenario_id,
        "fitness": calculate_fitness(metrics),
        "metrics": metrics,
        "critical": critical_patient_outcomes(simulator),
        "extended": calculate_extended_metrics(timeline, tick_latencies, latency_budget_ms),
        "completed": sum(p.completed for p in simulator.patients),
        "total_patients": len(simulator.patients),
        "conflicts": simulator.total_conflicts,
        "assignments": simulator.total_assignments,
        "messages": messages,
        "runtime_s": runtime,
        "mean_tick_latency_ms": 1000 * statistics.mean(tick_latencies),
        "max_tick_latency_ms": 1000 * max(tick_latencies),
        "queue_length": queue_length,
        "timeline": timeline,
        "decisions": decisions,
        "convergence": convergence,
    }


def run_algorithm(path, algorithm, seeds=1, base_seed=42,
                  latency_budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    """Run an algorithm; stochastic ones are repeated over ``seeds`` seeds."""
    n = seeds if algorithm in STOCHASTIC else 1
    runs = [run_simulation(path, get_allocator(algorithm, base_seed + i), latency_budget_ms)
            for i in range(n)]
    fitness = [r["fitness"] for r in runs]
    summary = dict(runs[0])  # representative run (first seed) for details
    summary.update({
        "algorithm": algorithm,
        "label": ALGORITHM_LABELS[algorithm],
        "runs": n,
        "fitness_mean": statistics.mean(fitness),
        "fitness_std": statistics.pstdev(fitness) if n > 1 else 0.0,
        "fitness_min": min(fitness),
        "fitness_max": max(fitness),
        "fitness_all": fitness,
    })
    return summary


def improvement_pct(value, reference):
    """Percent change of ``value`` relative to ``reference`` (safe for ~0)."""
    return (value - reference) / max(abs(reference), 1e-9) * 100.0


def run_benchmark(scenarios, algorithms=None, seeds=1, base_seed=42, directory=SCENARIO_DIR,
                  latency_budget_ms=DEFAULT_LATENCY_BUDGET_MS):
    """Run every algorithm on every scenario; returns a list of result dicts."""
    algorithms = algorithms or list(ALGORITHM_LABELS)
    results = []
    for name in scenarios:
        path = scenario_path(name, directory)
        by_algo = [run_algorithm(path, a, seeds, base_seed, latency_budget_ms) for a in algorithms]
        ref = next((r for r in by_algo if r["algorithm"] == "baseline"), None)
        for r in by_algo:
            r["improvement_vs_baseline_pct"] = (
                improvement_pct(r["fitness_mean"], ref["fitness_mean"]) if ref else None
            )
        results.extend(by_algo)
    return results


# ---------------------------------------------------------------- output


def write_outputs(results, output_dir, seeds, base_seed):
    """Write results.json, results.csv and results.md; return their paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # timeline / decisions are large; they are consumed by experiments/dashboard.py
    compact = [{k: v for k, v in r.items() if k not in ("timeline", "decisions")}
               for r in results]
    (out / "results.json").write_text(json.dumps(
        {"pso_seeds": seeds, "base_seed": base_seed, "results": compact}, indent=2))

    columns = ["scenario", "algorithm", "runs", "fitness_mean", "fitness_std",
               "improvement_vs_baseline_pct", "completed", "total_patients", "conflicts",
               "messages", "mean_tick_latency_ms", "max_tick_latency_ms"]
    metric_cols = ["treatment_rate", "critical_coverage", "average_waiting_time",
                   "conflict_rate", "resource_utilization", "resource_wastage", "throughput"]
    extra_cols = ["icu_saturation", "icu_peak_utilization", "mean_recovery_ticks",
                  "bottleneck", "latency_within_budget", "critical_mean_wait"]
    with open(out / "results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns + metric_cols + extra_cols)
        for r in results:
            ext = r["extended"]
            writer.writerow(
                [r.get(c) for c in columns] + [r["metrics"][m] for m in metric_cols]
                + [ext["icu_saturation"]["saturation"], ext["icu_saturation"]["peak_utilization"],
                   ext["recovery_time"]["mean_recovery"], ext["bottleneck"]["resource"],
                   ext["latency_budget"]["within_budget"], r["critical"]["critical_mean_wait"]])

    (out / "results.md").write_text(render_markdown(results, seeds, base_seed))
    return [out / "results.json", out / "results.csv", out / "results.md"]


def _fmt(value):
    return "-" if value is None else f"{value:.1f}"


def render_markdown(results, seeds, base_seed):
    lines = [
        "# SwarmCare benchmark results", "",
        f"PSO is stochastic: mean +/- std over {seeds} seed(s) starting at {base_seed}. "
        "Other algorithms are deterministic. Synthetic data only.", "",
        "| Scenario | Algorithm | Fitness | vs baseline | Avg wait | Conflicts | Completed "
        "| Mean tick latency (ms) | Messages | ICU saturation | Bottleneck | Mean recovery (ticks) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        fit = f"{r['fitness_mean']:.4f}" + (f" +/- {r['fitness_std']:.4f}" if r["runs"] > 1 else "")
        imp = r.get("improvement_vs_baseline_pct")
        lines.append(
            f"| {r['scenario']} | {r['algorithm']} | {fit} | "
            f"{'n/a' if imp is None else f'{imp:+.2f}%'} | "
            f"{r['metrics']['average_waiting_time']:.2f} | {r['conflicts']} | "
            f"{r['completed']}/{r['total_patients']} | {r['mean_tick_latency_ms']:.3f} | "
            f"{r['messages'] or '-'} | "
            f"{r['extended']['icu_saturation']['saturation']:.0%} | "
            f"{r['extended']['bottleneck']['resource'] or '-'} | "
            f"{_fmt(r['extended']['recovery_time']['mean_recovery'])} |")
    return "\n".join(lines) + "\n"
