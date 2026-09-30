"""Reserve-policy experiment: does holding back scarce units help critical patients?

Compares two *centralized* allocators (greedy baseline and fuzzy sort, both
work-conserving) with the decentralized negotiation, without and with a local
oxygen-reserve policy (``OxygenAgent`` only serves patients above a severity
threshold once its stock is at or below the reserve).

The verdict is computed from the measurements, never hard-coded. Read it with
two caveats that the report repeats:

* The benefit comes from the *reserve rule* (deliberate idling), not from
  decentralization as such: the rule is a local stock check that a centralized
  allocator could apply too (not tested here).
* It is a trade-off: critical patients wait less, everybody else waits more.

Run:  python -m experiments.reserve_policy --output results
"""

import argparse
import csv
import json
from pathlib import Path

from algorithms.decentralized import make_decentralized_allocator
from experiments.runner import get_allocator, run_simulation, scenario_path

DEFAULT_SCENARIOS = ("S6_resource_stress", "S7_reserve_stress")
DEFAULT_FRACTIONS = (0.1, 0.2, 0.3, 0.4)
MIN_SEVERITY = 0.80  # only critical patients may use the protected units


def policy_table(fractions=DEFAULT_FRACTIONS, min_severity=MIN_SEVERITY):
    """(label, kind, allocator_factory) rows: 2 centralized + decentralized variants."""
    rows = [
        ("centralized greedy", "centralized", lambda: get_allocator("baseline")),
        ("centralized fuzzy", "centralized", lambda: get_allocator("fuzzy")),
        ("decentralized, reserve off", "decentralized", lambda: make_decentralized_allocator()),
    ]
    for f in fractions:
        rows.append((
            f"decentralized, reserve {f:.0%} (severity >= {min_severity})", "reserve",
            lambda f=f: make_decentralized_allocator(
                oxygen_reserve_fraction=f, oxygen_reserve_min_severity=min_severity)))
    return rows


def run_reserve_experiment(scenarios=DEFAULT_SCENARIOS, fractions=DEFAULT_FRACTIONS,
                           min_severity=MIN_SEVERITY):
    """Run every policy on every scenario; one result row per (scenario, policy)."""
    rows = []
    for name in scenarios:
        path = scenario_path(name)
        for label, kind, factory in policy_table(fractions, min_severity):
            r = run_simulation(path, factory())
            c = r["critical"]
            rows.append({
                "scenario": r["scenario"], "policy": label, "kind": kind,
                "fitness": r["fitness"],
                "critical_mean_wait": c["critical_mean_wait"],
                "critical_max_wait": c["critical_max_wait"],
                "noncritical_mean_wait": c["noncritical_mean_wait"],
                "critical_completed": f"{c['critical_completed']}/{c['critical_count']}",
                "completed": f"{r['completed']}/{r['total_patients']}",
                "reserve_blocked": sum(d.get("reserve_blocked", 0) for d in r["decisions"]),
            })
    return rows


def verdict(rows):
    """Per scenario: is the best reserve policy better on critical waiting than the best centralized one?"""
    out = []
    for scenario in dict.fromkeys(r["scenario"] for r in rows):
        sc = [r for r in rows if r["scenario"] == scenario]
        central = min((r for r in sc if r["kind"] == "centralized"),
                      key=lambda r: r["critical_mean_wait"])
        reserve = min((r for r in sc if r["kind"] == "reserve"),
                      key=lambda r: (r["critical_mean_wait"], -r["fitness"]))
        out.append({
            "scenario": scenario,
            "best_centralized": central["policy"],
            "best_reserve": reserve["policy"],
            "critical_wait_centralized": central["critical_mean_wait"],
            "critical_wait_reserve": reserve["critical_mean_wait"],
            "decentralized_better_on_critical": reserve["critical_mean_wait"] < central["critical_mean_wait"],
            "noncritical_wait_centralized": central["noncritical_mean_wait"],
            "noncritical_wait_reserve": reserve["noncritical_mean_wait"],
            "fitness_centralized": central["fitness"],
            "fitness_reserve": reserve["fitness"],
        })
    return out


def render_markdown(rows, verdicts):
    lines = [
        "# Reserve-policy experiment", "",
        "Critical = severity >= 0.80. Waits are in ticks. Synthetic data; S7 is a *designed* stress case.", "",
        "| Scenario | Policy | Critical mean wait | Critical max wait | Non-critical mean wait | Fitness | Reserve refusals |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['scenario']} | {r['policy']} | {r['critical_mean_wait']:.2f} | "
                     f"{r['critical_max_wait']} | {r['noncritical_mean_wait']:.2f} | "
                     f"{r['fitness']:.4f} | {r['reserve_blocked']} |")
    lines += ["", "## Verdict (computed from the table)", ""]
    for v in verdicts:
        if v["decentralized_better_on_critical"]:
            head = (f"**{v['scenario']}**: decentralized with reserve beats centralized on critical waiting "
                    f"({v['critical_wait_reserve']:.2f} vs {v['critical_wait_centralized']:.2f} ticks) "
                    f"at a cost: non-critical wait {v['noncritical_wait_reserve']:.2f} vs "
                    f"{v['noncritical_wait_centralized']:.2f}, fitness {v['fitness_reserve']:.4f} vs "
                    f"{v['fitness_centralized']:.4f}.")
        else:
            head = (f"**{v['scenario']}**: no benefit - the best reserve policy does not beat centralized on "
                    f"critical waiting ({v['critical_wait_reserve']:.2f} vs {v['critical_wait_centralized']:.2f} ticks).")
        lines.append(f"* {head} (best reserve: {v['best_reserve']}; best centralized: {v['best_centralized']})")
    lines += ["",
              "Caveats: 'best reserve' is the best of the swept fractions (chosen after seeing the results); the gain "
              "comes from the reserve rule, not from decentralization itself (a centralized allocator could apply "
              "the same rule; not tested here); it is a trade-off, not a free improvement; and it appears only "
              "where oxygen is exhausted before critical patients arrive."]
    return "\n".join(lines) + "\n"


def write_outputs(rows, verdicts, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "reserve_policy.json").write_text(json.dumps({"rows": rows, "verdict": verdicts}, indent=2))
    with open(out / "reserve_policy.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / "reserve_policy.md").write_text(render_markdown(rows, verdicts))
    return [out / "reserve_policy.json", out / "reserve_policy.csv", out / "reserve_policy.md"]


def main(argv=None):
    p = argparse.ArgumentParser(description="SwarmCare reserve-policy experiment")
    p.add_argument("--scenarios", nargs="+", default=list(DEFAULT_SCENARIOS))
    p.add_argument("--output", default="results")
    args = p.parse_args(argv)
    rows = run_reserve_experiment(args.scenarios)
    verdicts = verdict(rows)
    for path in write_outputs(rows, verdicts, args.output):
        print(f"wrote {path}")
    print(render_markdown(rows, verdicts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
