"""Item 7: scaling study over patient counts and PSO budgets."""
import json

import pytest

from experiments.scaling import (config_label, latency_exponents, main, make_synthetic_scenario,
                                 render_markdown, run_scaling, write_outputs)


def test_synthetic_scenario_is_deterministic_and_sized():
    a, b = make_synthetic_scenario(37, seed=1), make_synthetic_scenario(37, seed=1)
    assert a == b and len(a["patients"]) == 37
    assert make_synthetic_scenario(37, seed=2) != a
    ids = [p["patient_id"] for p in a["patients"]]
    assert len(set(ids)) == 37
    assert all(0 <= p["arrival_time"] < 60 and 0.0 <= p["severity"] <= 1.0 for p in a["patients"])


def test_run_scaling_rows_cover_every_count_and_budget():
    rows = run_scaling(counts=(10, 20), budgets=((4, 3), (8, 6)), pso_seeds=2)
    assert len(rows) == 2 * (3 + 2)
    pso = [r for r in rows if r["algorithm"] == "pso"]
    assert {r["evals_per_decision"] for r in pso} == {12, 48} and all(r["runs"] == 2 for r in pso)
    assert {config_label(r) for r in rows} == {"baseline", "fuzzy", "decentralized", "pso 4x3", "pso 8x6"}
    for r in rows:
        assert 0 < r["completed_share"] <= 1 and r["mean_tick_latency_ms"] >= 0


def test_bigger_pso_budget_costs_more_time_per_decision():
    rows = run_scaling(counts=(60,), budgets=((3, 2), (24, 30)))
    small, big = [r for r in rows if r["algorithm"] == "pso"]
    assert big["mean_tick_latency_ms"] > small["mean_tick_latency_ms"]


def test_latency_exponents_linear_and_constant():
    rows = [{"patients": n, "algorithm": "baseline", "mean_tick_latency_ms": 0.01 * n} for n in (10, 100, 1000)]
    rows += [{"patients": n, "algorithm": "fuzzy", "mean_tick_latency_ms": 5.0} for n in (10, 100, 1000)]
    exps = latency_exponents(rows)
    assert exps["baseline"] == pytest.approx(1.0) and exps["fuzzy"] == pytest.approx(0.0, abs=1e-9)
    assert latency_exponents(rows[:1]) == {}


def test_outputs_and_cli(tmp_path):
    rows = run_scaling(counts=(10, 20), budgets=((4, 3),))
    paths = write_outputs(rows, tmp_path, pso_seeds=1)
    assert all(p.exists() for p in paths)
    data = json.loads((tmp_path / "scaling.json").read_text())
    assert len(data["rows"]) == len(rows) and "pso 4x3" in data["latency_exponents"]
    assert "| 10 | pso 4x3 | 12 |" in render_markdown(rows, 1)
    out = tmp_path / "cli"
    assert main(["--counts", "10", "15", "--budgets", "3x2", "--output", str(out)]) == 0
    assert (out / "scaling.csv").exists()
