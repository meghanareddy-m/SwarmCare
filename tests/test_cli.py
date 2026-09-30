import main as cli


def test_cli_single_scenario_runs(capsys):
    assert cli.main(["--scenario", "S1", "--algorithms", "baseline", "fuzzy", "--quiet"]) == 0
    out = capsys.readouterr().out
    assert "COMPARISON - S1_normal" in out and "fuzzy" in out


def test_cli_writes_outputs(tmp_path, capsys):
    assert cli.main(["--scenario", "S1", "--algorithms", "baseline", "--output", str(tmp_path),
                     "--plots", "--quiet"]) == 0
    assert (tmp_path / "results.json").exists()
    assert (tmp_path / "results.md").exists()


def test_cli_rejects_unknown_scenario(capsys):
    assert cli.main(["--scenario", "S99"]) == 2
    assert "Unknown or ambiguous scenario" in capsys.readouterr().err


def test_cli_rejects_bad_seed_count(capsys):
    assert cli.main(["--pso-seeds", "0"]) == 2


def test_cli_plots_without_output_is_an_error(capsys):
    assert cli.main(["--scenario", "S1", "--plots", "--algorithms", "baseline"]) == 2


def test_cli_full_report_mentions_each_attempt(capsys):
    assert cli.main(["--scenario", "S1"]) == 0
    out = capsys.readouterr().out
    for label in ["ATTEMPT 1", "ATTEMPT 2", "ATTEMPT 3", "ATTEMPT 4"]:
        assert label in out


def test_cli_prints_extended_metrics(capsys):
    assert cli.main(["--scenario", "S5", "--algorithms", "baseline"]) == 0
    out = capsys.readouterr().out
    for label in ["ICU saturation", "Bottleneck", "Recovery time", "Latency budget"]:
        assert label in out


def test_cli_writes_dashboard(tmp_path, capsys):
    assert cli.main(["--scenario", "S1", "--algorithms", "baseline", "--output", str(tmp_path),
                     "--dashboard", "--quiet"]) == 0
    assert (tmp_path / "dashboard.html").read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_cli_dashboard_without_output_is_an_error(capsys):
    assert cli.main(["--scenario", "S1", "--algorithms", "baseline", "--dashboard"]) == 2


def test_cli_rejects_bad_latency_budget(capsys):
    assert cli.main(["--latency-budget-ms", "0"]) == 2
