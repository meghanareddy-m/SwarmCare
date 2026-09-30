"""Scaling study: patient count x PSO budget.

For each patient count a synthetic scenario is generated (seeded, fixed
hospital, arrivals spread over the first 60 ticks) and run with the greedy
baseline, fuzzy priority, decentralized negotiation and PSO with several
budgets (``swarm_size x iterations`` = evaluations per decision). The hospital
does NOT grow with the patient count, so larger counts mean heavier congestion
as well as a larger decision problem; results mix both effects.

Reported per run: fitness, waiting of critical patients, decision latency
(machine dependent), total runtime, messages. A log-log slope of mean decision
latency against patient count summarises how each method scales.

Run:  python -m experiments.scaling --output results
"""

import argparse
import csv
import json
import math
import random
import statistics
import tempfile
from pathlib import Path

from algorithms.decentralized import make_decentralized_allocator
from algorithms.baseline import greedy_allocate
from algorithms.fuzzy_baseline import fuzzy_allocate
from algorithms.pso_allocator import make_pso_allocator
from experiments.runner import run_simulation

DEFAULT_COUNTS = (25, 50, 100, 200, 400)
DEFAULT_BUDGETS = ((6, 8), (12, 15), (24, 30))  # (swarm_size, iterations); (12, 15) = default
HOSPITAL = {"doctors": 14, "icu_beds": 8, "ward_beds": 30, "oxygen_units": 40,
            "ventilators": 10, "diagnostics": {"CT": 2, "XRAY": 2, "LAB": 3}}
TICKS = 80
ARRIVAL_WINDOW = 60


def make_synthetic_scenario(n_patients, seed=42, ticks=TICKS):
    """Scenario dict with ``n_patients`` patients (same generator family as S6)."""
    rng = random.Random(seed)
    patients = []
    for _ in range(n_patients):
        severity = round(rng.choices(
            [rng.uniform(0.2, 0.5), rng.uniform(0.5, 0.8), rng.uniform(0.8, 1.0)],
            weights=[0.4, 0.4, 0.2])[0], 2)
        critical = severity >= 0.80
        patients.append({
            "severity": severity,
            "oxygen_required": rng.random() < (0.7 if severity >= 0.5 else 0.3),
            "ventilator_required": critical and rng.random() < 0.4,
            "arrival_time": rng.randint(0, ARRIVAL_WINDOW - 1),
            "service_duration": rng.randint(4, 6) if critical else rng.randint(2, 4),
        })
    patients.sort(key=lambda p: p["arrival_time"])
    for i, p in enumerate(patients, 1):
        p["patient_id"] = f"P{i:04d}"
    return {
        "scenario_id": f"SCALE_{n_patients}",
        "description": f"Synthetic scaling scenario with {n_patients} patients.",
        "hospital": dict(HOSPITAL), "simulation": {"ticks": ticks}, "events": [],
        "patients": patients,
    }


def _row(n, algorithm, budget, runs):
    """Aggregate one or several runs of the same configuration."""
    def mean(key, sub=None):
        vals = [(r[key][sub] if sub else r[key]) for r in runs]
        return statistics.mean(vals)
    return {
        "patients": n, "algorithm": algorithm,
        "swarm_size": budget[0] if budget else None,
        "iterations": budget[1] if budget else None,
        "evals_per_decision": budget[0] * budget[1] if budget else None,
        "runs": len(runs),
        "fitness": mean("fitness"),
        "fitness_std": statistics.pstdev([r["fitness"] for r in runs]) if len(runs) > 1 else 0.0,
        "critical_mean_wait": mean("critical", "critical_mean_wait"),
        "completed_share": statistics.mean(r["completed"] / r["total_patients"] for r in runs),
        "mean_tick_latency_ms": mean("mean_tick_latency_ms"),
        "max_tick_latency_ms": max(r["max_tick_latency_ms"] for r in runs),
        "runtime_s": mean("runtime_s"),
        "messages": mean("messages"),
    }


def run_scaling(counts=DEFAULT_COUNTS, budgets=DEFAULT_BUDGETS, pso_seeds=1, base_seed=42):
    """Return one row per (patient count, algorithm/budget)."""
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for n in counts:
            path = Path(tmp) / f"scale_{n}.json"
            path.write_text(json.dumps(make_synthetic_scenario(n, base_seed)))
            for name, allocator in (("baseline", greedy_allocate), ("fuzzy", fuzzy_allocate),
                                    ("decentralized", make_decentralized_allocator())):
                rows.append(_row(n, name, None, [run_simulation(path, allocator)]))
            for swarm, iters in budgets:
                runs = [run_simulation(path, make_pso_allocator(
                    base_seed=base_seed + i, swarm_size=swarm, iterations=iters))
                    for i in range(pso_seeds)]
                rows.append(_row(n, "pso", (swarm, iters), runs))
    return rows


def config_label(row):
    if row["algorithm"] != "pso":
        return row["algorithm"]
    return f"pso {row['swarm_size']}x{row['iterations']}"


def latency_exponents(rows):
    """Least-squares slope of log(mean latency) on log(patients) per configuration.

    ~0 means latency is insensitive to the patient count, ~1 roughly linear.
    Needs at least two patient counts; returns {} otherwise.
    """
    out = {}
    for label in dict.fromkeys(config_label(r) for r in rows):
        pts = [(math.log(r["patients"]), math.log(max(r["mean_tick_latency_ms"], 1e-9)))
               for r in rows if config_label(r) == label]
        if len({x for x, _ in pts}) < 2:
            continue
        mx = statistics.mean(x for x, _ in pts)
        my = statistics.mean(y for _, y in pts)
        out[label] = (sum((x - mx) * (y - my) for x, y in pts)
                      / sum((x - mx) ** 2 for x, _ in pts))
    return out


def render_markdown(rows, pso_seeds):
    exps = latency_exponents(rows)
    lines = [
        "# Scaling study", "",
        f"Fixed hospital ({HOSPITAL['doctors']} doctors, {HOSPITAL['icu_beds']} ICU, {HOSPITAL['ward_beds']} ward, "
        f"{HOSPITAL['oxygen_units']} O2, {HOSPITAL['ventilators']} ventilators), {TICKS} ticks, arrivals in the first "
        f"{ARRIVAL_WINDOW}. More patients therefore means heavier congestion *and* a bigger decision problem. "
        f"PSO rows average {pso_seeds} seed(s). Latency is wall-clock on the machine that ran the study.", "",
        "| Patients | Configuration | Evals/decision | Fitness | Critical mean wait | Completed | "
        "Mean tick latency (ms) | Max tick latency (ms) | Runtime (s) | Messages |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        evals = r["evals_per_decision"] if r["evals_per_decision"] else "-"
        lines.append(
            f"| {r['patients']} | {config_label(r)} | {evals} | {r['fitness']:.4f} | "
            f"{r['critical_mean_wait']:.2f} | {r['completed_share']:.0%} | {r['mean_tick_latency_ms']:.3f} | "
            f"{r['max_tick_latency_ms']:.3f} | {r['runtime_s']:.2f} | {r['messages']:.0f} |")
    if exps:
        lines += ["", "## Latency growth (log-log slope of mean decision latency vs patient count)", "",
                  "| Configuration | Slope |", "|---|---|"]
        lines += [f"| {k} | {v:.2f} |" for k, v in exps.items()]
    return "\n".join(lines) + "\n"


def write_outputs(rows, output_dir, pso_seeds):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "scaling.json").write_text(json.dumps(
        {"pso_seeds": pso_seeds, "latency_exponents": latency_exponents(rows), "rows": rows}, indent=2))
    with open(out / "scaling.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / "scaling.md").write_text(render_markdown(rows, pso_seeds))
    return [out / "scaling.json", out / "scaling.csv", out / "scaling.md"]


def main(argv=None):
    p = argparse.ArgumentParser(description="SwarmCare scaling study")
    p.add_argument("--counts", nargs="+", type=int, default=list(DEFAULT_COUNTS))
    p.add_argument("--budgets", nargs="+", default=[f"{s}x{i}" for s, i in DEFAULT_BUDGETS],
                   help="PSO budgets as SWARMxITERATIONS, e.g. 12x15")
    p.add_argument("--pso-seeds", type=int, default=1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", default="results")
    args = p.parse_args(argv)
    budgets = [tuple(int(x) for x in b.lower().split("x")) for b in args.budgets]
    rows = run_scaling(args.counts, budgets, args.pso_seeds, args.seed)
    for path in write_outputs(rows, args.output, args.pso_seeds):
        print(f"wrote {path}")
    print(render_markdown(rows, args.pso_seeds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
