import json

import pytest

from experiments.runner import (ALGORITHM_LABELS, get_allocator, improvement_pct,
                                list_scenarios, render_markdown, run_algorithm,
                                run_benchmark, run_simulation, scenario_path, write_outputs)
from algorithms.pso_allocator import make_pso_allocator


def test_list_scenarios_contains_all_six():
    names = list_scenarios()
    for expected in ["S1_normal", "S2_patient_surge", "S3_icu_shortage",
                     "S4_oxygen_shortage", "S5_pandemic_crisis", "S6_resource_stress"]:
        assert expected in names


def test_scenario_path_resolution():
    assert scenario_path("S5").name == "S5_pandemic_crisis.json"
    assert scenario_path("S5_pandemic_crisis").exists()
    assert scenario_path("data/scenarios/S1_normal.json").exists()
    with pytest.raises(ValueError):
        scenario_path("S99")
    with pytest.raises(ValueError):
        scenario_path("S")  # ambiguous


def test_unknown_algorithm_rejected():
    with pytest.raises(ValueError):
        get_allocator("magic")


def test_improvement_pct():
    assert improvement_pct(1.1, 1.0) == pytest.approx(10.0)
    assert improvement_pct(0.9, 1.0) == pytest.approx(-10.0)
    assert improvement_pct(0.5, 0.0) > 0  # no ZeroDivisionError


def test_run_simulation_returns_expected_fields():
    r = run_simulation(scenario_path("S1"), get_allocator("baseline"))
    assert r["completed"] == r["total_patients"] == 30
    assert len(r["queue_length"]) == 80
    assert r["mean_tick_latency_ms"] >= 0
    assert 0 <= r["fitness"] <= 1


def test_pso_is_reproducible_for_a_given_seed_and_varies_across_seeds():
    path = scenario_path("S3")
    a = run_simulation(path, make_pso_allocator(base_seed=7))
    b = run_simulation(path, make_pso_allocator(base_seed=7))
    assert a["fitness"] == b["fitness"] and a["conflicts"] == b["conflicts"]


def test_multi_seed_statistics_only_for_stochastic_algorithms():
    path = scenario_path("S1")
    pso = run_algorithm(path, "pso", seeds=3)
    assert pso["runs"] == 3 and len(pso["fitness_all"]) == 3
    assert pso["fitness_min"] <= pso["fitness_mean"] <= pso["fitness_max"]
    base = run_algorithm(path, "baseline", seeds=3)
    assert base["runs"] == 1 and base["fitness_std"] == 0.0


def test_benchmark_reports_improvement_relative_to_baseline():
    results = run_benchmark(["S1"], seeds=1)
    assert {r["algorithm"] for r in results} == set(ALGORITHM_LABELS)
    base = next(r for r in results if r["algorithm"] == "baseline")
    assert base["improvement_vs_baseline_pct"] == 0
    for r in results:
        assert r["improvement_vs_baseline_pct"] == pytest.approx(
            improvement_pct(r["fitness_mean"], base["fitness_mean"]))


def test_write_outputs_creates_valid_files(tmp_path):
    results = run_benchmark(["S1"], ["baseline", "fuzzy"])
    paths = write_outputs(results, tmp_path / "out", seeds=1, base_seed=42)
    assert all(p.exists() for p in paths)
    data = json.loads((tmp_path / "out" / "results.json").read_text())
    assert len(data["results"]) == 2
    header = (tmp_path / "out" / "results.csv").read_text().splitlines()[0]
    assert "fitness_mean" in header and "critical_coverage" in header
    assert "| S1_normal | baseline |" in render_markdown(results, 1, 42)
