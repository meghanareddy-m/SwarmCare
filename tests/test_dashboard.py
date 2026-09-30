"""Item 6: experiments/dashboard.py writes one dependency-free HTML file."""
import json
import re

from experiments.dashboard import build_dashboard_data, main, render_dashboard, write_dashboard
from experiments.runner import run_benchmark


def _results():
    return run_benchmark(["S5"], ["baseline", "decentralized"])


def _embedded(html):
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</").replace("<\\!--", "<!--"))


def test_payload_contains_series_events_decisions_and_metrics():
    data = build_dashboard_data(_results())
    run = data["runs"]["S5_pandemic_crisis"]["decentralized"]
    assert set(run["series"]) >= {"queue", "icu_used", "icu_cap", "oxygen_used", "diagnostic_queue"}
    assert all(len(v) == 80 for v in run["series"].values())
    assert [e[0] for e in run["events"]] == [25, 40, 50, 60, 70]
    assert any("oxygen_reduction 35%" == e[1] for e in run["events"])
    assert len(run["decisions"]) == 80 and run["decisions"][0]["adm"]
    assert "messages" in run["decisions"][0]          # agent messages only for the negotiating allocator
    assert "messages" not in data["runs"]["S5_pandemic_crisis"]["baseline"]["decisions"][0]
    assert set(run["extended"]) == {"icu_saturation", "recovery_time", "bottleneck", "latency_budget"}


def test_html_is_single_file_without_external_resources():
    html = render_dashboard(_results())
    assert html.startswith("<!DOCTYPE html>") and "<svg" in html
    assert not re.search(r'(src|href)\s*=\s*["\']?(https?:)?//', html)
    assert "<link" not in html and "@import" not in html and "url(http" not in html
    assert len(re.findall(r"<script\b", html)) == 2     # JSON data + inline renderer
    assert not re.search(r"\bfetch\(|XMLHttpRequest|import\(", html)
    assert "/*__DATA__*/" not in html


def test_embedded_json_round_trips_and_is_script_safe():
    html = render_dashboard(_results())
    data = _embedded(html)
    assert data["latency_budget_ms"] > 0 and "S5_pandemic_crisis" in data["runs"]
    body = re.search(r'id="data">(.*?)</script>', html, re.S).group(1)
    assert "</" not in body and "<!--" not in body


def test_data_with_closing_script_tag_cannot_break_out():
    results = _results()
    results[0]["timeline"][0]["events"] = [{"type": "</script><b>x", "time": 0}]
    html = render_dashboard(results)
    assert len(re.findall(r"</script>", html)) == 2
    assert _embedded(html)["runs"]["S5_pandemic_crisis"]["baseline"]["events"][0][1] == "</script><b>x"


def test_dashboard_has_required_panels():
    html = render_dashboard(_results())
    for needle in ("Waiting queue over time", "Resource utilization", "Agent decisions per tick",
                   "Shocks and recovery", "ICU saturation", "Latency budget", "Bottleneck", "shock"):
        assert needle in html


def test_write_dashboard_and_cli(tmp_path):
    path = write_dashboard(_results(), tmp_path / "sub" / "dashboard.html")
    assert path.exists() and path.stat().st_size > 10_000
    out = tmp_path / "cli.html"
    assert main(["--scenarios", "S1", "--algorithms", "baseline", "--output", str(out)]) == 0
    assert "S1_normal" in _embedded(out.read_text(encoding="utf-8"))["runs"]
