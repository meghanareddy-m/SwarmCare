"""Item 8: reserve-policy experiment (centralized vs decentralized on critical patients)."""
import json

from experiments.reserve_policy import (main, render_markdown, run_reserve_experiment, verdict,
                                        write_outputs)


def _row(scenario, policy, kind, crit, non=1.0, fit=0.5):
    return {"scenario": scenario, "policy": policy, "kind": kind, "fitness": fit,
            "critical_mean_wait": crit, "critical_max_wait": 1, "noncritical_mean_wait": non,
            "critical_completed": "1/1", "completed": "2/2", "reserve_blocked": 0}


def test_verdict_is_computed_from_the_rows_not_assumed():
    rows = [_row("A", "centralized greedy", "centralized", 3.0),
            _row("A", "centralized fuzzy", "centralized", 2.0),
            _row("A", "reserve 10%", "reserve", 1.0),
            _row("B", "centralized greedy", "centralized", 1.0),
            _row("B", "reserve 10%", "reserve", 1.5)]
    va, vb = verdict(rows)
    assert va["decentralized_better_on_critical"] and va["critical_wait_centralized"] == 2.0
    assert not vb["decentralized_better_on_critical"]
    md = render_markdown(rows, [va, vb])
    assert "beats centralized on critical waiting" in md and "no benefit" in md


def test_verdict_tie_is_not_a_win():
    rows = [_row("A", "centralized greedy", "centralized", 2.0), _row("A", "reserve", "reserve", 2.0)]
    assert verdict(rows)[0]["decentralized_better_on_critical"] is False


def test_designed_scenario_shows_the_tradeoff_and_natural_one_does_not():
    rows = run_reserve_experiment(("S6", "S7"), fractions=(0.4,))
    s6, s7 = verdict(rows)
    # S7 (designed): reserve cuts critical waiting ...
    assert s7["decentralized_better_on_critical"]
    assert s7["critical_wait_reserve"] < s7["critical_wait_centralized"]
    # ... but at a price for everybody else and for overall fitness.
    assert s7["noncritical_wait_reserve"] > s7["noncritical_wait_centralized"]
    assert s7["fitness_reserve"] < s7["fitness_centralized"]
    # S6 (natural oxygen-bound stress): no real benefit (difference below 0.1 tick or worse).
    assert s6["critical_wait_reserve"] > s6["critical_wait_centralized"] - 0.1


def test_reserve_off_equals_centralized_fuzzy():
    rows = run_reserve_experiment(("S7",), fractions=())
    fuzzy = next(r for r in rows if r["policy"] == "centralized fuzzy")
    dec = next(r for r in rows if r["policy"] == "decentralized, reserve off")
    for key in ("fitness", "critical_mean_wait", "noncritical_mean_wait", "completed"):
        assert fuzzy[key] == dec[key]
    assert dec["reserve_blocked"] == 0


def test_reserve_refusals_are_recorded_when_policy_is_on():
    rows = run_reserve_experiment(("S7",), fractions=(0.3,))
    assert next(r for r in rows if r["kind"] == "reserve")["reserve_blocked"] > 0


def test_outputs_and_cli(tmp_path):
    rows = run_reserve_experiment(("S7",), fractions=(0.3,))
    paths = write_outputs(rows, verdict(rows), tmp_path)
    assert all(p.exists() for p in paths)
    assert json.loads((tmp_path / "reserve_policy.json").read_text())["verdict"][0]["scenario"] == "S7_reserve_stress"
    assert main(["--scenarios", "S7", "--output", str(tmp_path / "cli")]) == 0
    assert (tmp_path / "cli" / "reserve_policy.md").exists()
