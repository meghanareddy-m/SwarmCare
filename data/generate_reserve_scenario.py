"""Generate S7_reserve_stress.json (synthetic, seed 42).

A DESIGNED stress case for the reserve-policy experiment, not a calibrated one:
moderate-severity oxygen patients arrive first and (being alone in the queue)
are admitted by every work-conserving allocator until oxygen is exhausted; a
wave of critical patients arrives afterwards. Whether holding back a few oxygen
units for severe patients pays off is exactly what the experiment measures.
Run from the repository root:  python data/generate_reserve_scenario.py
"""
import json
import random
from pathlib import Path

rng = random.Random(42)
patients = []


def add(severity, arrival, duration, vent=False):
    patients.append({
        "patient_id": f"P{len(patients) + 1:03d}",
        "severity": round(severity, 2),
        "oxygen_required": True,
        "ventilator_required": vent,
        "arrival_time": arrival,
        "service_duration": duration,
    })


for _ in range(14):                       # wave 1: moderate, long stays
    add(rng.uniform(0.30, 0.60), rng.randint(0, 3), rng.randint(14, 18))
for _ in range(7):                        # wave 2: critical, shorter stays
    add(rng.uniform(0.85, 0.98), rng.randint(6, 14), rng.randint(4, 6), vent=rng.random() < 0.5)
for _ in range(14):                       # wave 3: more moderate patients
    add(rng.uniform(0.30, 0.60), rng.randint(8, 30), rng.randint(6, 10))
patients.sort(key=lambda p: (p["arrival_time"], p["patient_id"]))
for i, p in enumerate(patients, 1):
    p["patient_id"] = f"P{i:03d}"

scenario = {
    "scenario_id": "S7_reserve_stress",
    "description": "Designed stress test: oxygen exhausted by early moderate patients before critical patients arrive.",
    "hospital": {
        "doctors": 30, "icu_beds": 6, "ward_beds": 40,
        "oxygen_units": 10, "ventilators": 6,
        "diagnostics": {"CT": 2, "XRAY": 2, "LAB": 3},
    },
    "simulation": {"ticks": 70},
    "events": [],
    "patients": patients,
}
Path("data/scenarios/S7_reserve_stress.json").write_text(json.dumps(scenario, indent=2) + "\n")
print("wrote S7_reserve_stress.json")
