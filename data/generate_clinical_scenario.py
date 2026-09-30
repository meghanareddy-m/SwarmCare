"""Generate S8_clinical_inputs.json (synthetic, seed 42).

Exercises the optional clinical inputs: every patient has an ``age`` and an
``spo2`` (percent), and most need a ``diagnostic`` (CT / XRAY / LAB) before they
can be admitted. Diagnostics capacity is deliberately tight so the diagnostics
queue is visible. SpO2 is loosely coupled to severity with noise; this is a
synthetic convenience, not a clinical model.
Run from the repository root:  python data/generate_clinical_scenario.py
"""
import json
import random
from pathlib import Path

rng = random.Random(42)
patients = []
for i in range(1, 41):
    severity = round(min(1.0, max(0.1, rng.gauss(0.55, 0.22))), 2)
    spo2 = round(min(100.0, max(78.0, 99 - 16 * severity + rng.gauss(0, 2.5))), 1)
    critical = severity >= 0.80
    p = {
        "patient_id": f"P{i:03d}",
        "severity": severity,
        "age": rng.randint(25, 90),
        "spo2": spo2,
        "oxygen_required": spo2 < 93.0,
        "ventilator_required": critical and rng.random() < 0.5,
        "arrival_time": rng.randint(0, 30),
        "service_duration": rng.randint(5, 8) if critical else rng.randint(3, 6),
    }
    if rng.random() < 0.75:
        p["diagnostic"] = rng.choices(["CT", "XRAY", "LAB"], weights=[0.2, 0.4, 0.4])[0]
        p["diagnostic_duration"] = rng.randint(1, 3)
    patients.append(p)
patients.sort(key=lambda p: (p["arrival_time"], p["patient_id"]))
for i, p in enumerate(patients, 1):
    p["patient_id"] = f"P{i:03d}"

scenario = {
    "scenario_id": "S8_clinical_inputs",
    "description": "Synthetic case with age, SpO2 and a diagnostics queue (CT / XRAY / LAB).",
    "hospital": {
        "doctors": 10, "icu_beds": 4, "ward_beds": 20,
        "oxygen_units": 15, "ventilators": 3,
        "diagnostics": {"CT": 1, "XRAY": 1, "LAB": 2},
    },
    "simulation": {"ticks": 70},
    "events": [{"time": 35, "type": "doctor_unavailable", "count": 2}],
    "patients": patients,
}
Path("data/scenarios/S8_clinical_inputs.json").write_text(json.dumps(scenario, indent=2) + "\n")
print("wrote S8_clinical_inputs.json")
