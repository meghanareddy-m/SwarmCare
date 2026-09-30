"""SwarmCare command line interface.

Examples
--------
    python main.py                          # S5 pandemic crisis, all four attempts
    python main.py --scenario S3            # one scenario (id prefix or file path)
    python main.py --all --pso-seeds 5      # every scenario, PSO averaged over 5 seeds
    python main.py --all --output results --plots --dashboard   # also results/dashboard.html
"""

import argparse
import os
import sys

from evaluation.metrics import DEFAULT_LATENCY_BUDGET_MS
from experiments.dashboard import write_dashboard
from experiments.plots import save_plots
from experiments.runner import (
    ALGORITHM_LABELS, DEFAULT_SCENARIO, list_scenarios, run_benchmark, write_outputs,
)

WHY = {
    "baseline": "Deterministic severity-first greedy ordering (reference).",
    "fuzzy": "Severity, waiting time and oxygen need are combined by a fuzzy rule base.",
    "pso": "Particle swarm search over patient orderings, evaluated on a virtual copy of the hospital state.",
    "decentralized": "No central sort: patient agents bid, resource agents grant locally, rounds repeat.",
}


def print_result(r):
    print()
    print("=" * 70)
    print(r["label"].upper())
    print("=" * 70)
    fit = f"{r['fitness_mean']:.4f}"
    if r["runs"] > 1:
        fit += f"  (mean of {r['runs']} seeds, std {r['fitness_std']:.4f})"
    print(f"Final Fitness      : {fit}")
    print(f"Patients Completed : {r['completed']}/{r['total_patients']}")
    print(f"Total Conflicts    : {r['conflicts']}")
    print(f"Runtime            : {r['runtime_s']:.4f} s "
          f"(mean {r['mean_tick_latency_ms']:.3f} ms / decision tick)")
    if r["messages"]:
        print(f"Agent messages     : {r['messages']}")
    print()
    for key, value in r["metrics"].items():
        print(f"{key:22s}: {value:.4f}")
    ext = r["extended"]
    ic, bn, rc, lb = (ext["icu_saturation"], ext["bottleneck"], ext["recovery_time"],
                      ext["latency_budget"])
    print(f"\nICU saturation     : {ic['saturation']:.1%} of ticks (peak utilization {ic['peak_utilization']:.0%})")
    print(f"Bottleneck         : {bn['resource'] or 'none (queue always empty)'}")
    rec = "n/a (no events)" if not rc["shocks"] else (
        f"mean {rc['mean_recovery']:.1f} ticks, {rc['unrecovered']} unrecovered"
        if rc["mean_recovery"] is not None else f"never recovered ({rc['unrecovered']} event(s))")
    print(f"Recovery time      : {rec}")
    print(f"Latency budget     : {lb['budget_ms']:g} ms -> {'met' if lb['meets_budget'] else 'EXCEEDED'} "
          f"({lb['within_budget']:.0%} of ticks within, p95 {lb['p95_ms']:.3f} ms)")
    print(f"\nHow it works: {WHY[r['algorithm']]}")
    if r["algorithm"] == "pso" and r["convergence"]:
        c = r["convergence"]
        print(f"PSO convergence (first tick): initial best {c[0]:.4f} -> final best {c[-1]:.4f} "
              f"over {len(c)} iterations")


def print_comparison(results):
    for scenario in dict.fromkeys(r["scenario"] for r in results):
        print()
        print("=" * 70)
        print(f"COMPARISON - {scenario}")
        print("=" * 70)
        for r in (r for r in results if r["scenario"] == scenario):
            imp = r["improvement_vs_baseline_pct"]
            tag = "" if imp is None else f"  ({imp:+.2f}% vs baseline)"
            print(f"{r['algorithm']:14s} fitness {r['fitness_mean']:.4f}{tag}  "
                  f"conflicts {r['conflicts']}  avg wait {r['metrics']['average_waiting_time']:.2f}")


def build_parser():
    p = argparse.ArgumentParser(description="SwarmCare synthetic hospital resource-coordination benchmark")
    p.add_argument("--scenario", default=DEFAULT_SCENARIO,
                   help="scenario id, unique prefix (e.g. S3) or path to a .json file")
    p.add_argument("--all", action="store_true", help="run every scenario in data/scenarios")
    p.add_argument("--algorithms", nargs="+", choices=list(ALGORITHM_LABELS),
                   help="subset of algorithms (default: all)")
    p.add_argument("--pso-seeds", type=int, default=1, help="number of PSO seeds to average (default 1)")
    p.add_argument("--seed", type=int, default=42, help="base random seed (default 42)")
    p.add_argument("--output", default=os.environ.get("SWARMCARE_RESULTS_DIR"),
                   help="directory for results.json/csv/md (default: none, or $SWARMCARE_RESULTS_DIR)")
    p.add_argument("--plots", action="store_true", help="also save PNG figures (needs matplotlib)")
    p.add_argument("--dashboard", action="store_true",
                   help="also write DIR/dashboard.html (single file, no dependencies; needs --output)")
    p.add_argument("--latency-budget-ms", type=float, default=DEFAULT_LATENCY_BUDGET_MS,
                   help=f"per-decision latency budget for the latency-budget metric (default {DEFAULT_LATENCY_BUDGET_MS:g})")
    p.add_argument("--quiet", action="store_true", help="only print the comparison table")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.pso_seeds < 1:
        print("--pso-seeds must be >= 1", file=sys.stderr)
        return 2
    if args.latency_budget_ms <= 0:
        print("--latency-budget-ms must be > 0", file=sys.stderr)
        return 2

    scenarios = list_scenarios() if args.all else [args.scenario]
    try:
        results = run_benchmark(scenarios, args.algorithms, args.pso_seeds, args.seed,
                                latency_budget_ms=args.latency_budget_ms)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print("=" * 70)
    print("SWARMCARE COMPUTATIONAL INTELLIGENCE EXPERIMENT (synthetic simulation)")
    print("=" * 70)
    print(f"Scenarios: {', '.join(dict.fromkeys(r['scenario'] for r in results))}")
    print(f"Base seed: {args.seed}   PSO seeds: {args.pso_seeds}")
    if not args.quiet:
        for r in results:
            print(f"\n[{r['scenario']}]", end="")
            print_result(r)
    print_comparison(results)

    if args.output:
        for path in write_outputs(results, args.output, args.pso_seeds, args.seed):
            print(f"wrote {path}")
        if args.plots:
            figs = save_plots(results, args.output)
            print(f"wrote {len(figs)} figure(s)" if figs else "matplotlib not installed; plots skipped")
        if args.dashboard:
            print(f"wrote {write_dashboard(results, os.path.join(args.output, 'dashboard.html'), args.latency_budget_ms)}")
    elif args.plots or args.dashboard:
        print("--plots and --dashboard need --output DIR", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
