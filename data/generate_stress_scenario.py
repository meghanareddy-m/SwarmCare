"""Generate S6_resource_stress.json (synthetic, seed 42).

Unlike S1-S5, doctors are plentiful here and OXYGEN / VENTILATORS are the
binding constraints, so resource-conservation policies can actually matter.
Run from the repository root:  python data/generate_stress_scenario.py
"""
import json
import random
from pathlib import Path

random.seed(42)

patients = []
for i in range(1, 91):
    severity = round(random.choices(
        [random.uniform(0.2, 0.5), random.uniform(0.5, 0.8), random.uniform(0.8, 1.0)],
        weights=[0.4, 0.4, 0.2])[0], 2)
    critical = severity >= 0.80
    patients.append({
        "patient_id": f"P{i:03d}",
        "severity": severity,
        "oxygen_required": random.random() < (0.9 if severity >= 0.5 else 0.5),
        "ventilator_required": critical and random.random() < 0.6,
        "arrival_time": random.randint(0, 15),
        "service_duration": random.randint(5, 7) if critical else random.randint(3, 5),
    })
patients.sort(key=lambda p: (p["arrival_time"], p["patient_id"]))

scenario = {
    "scenario_id": "S6_resource_stress",
    "description": "Synthetic stress test: ample doctors, scarce oxygen and ventilators.",
    "hospital": {
        "doctors": 30, "icu_beds": 10, "ward_beds": 40,
        "oxygen_units": 8, "ventilators": 3,
        "diagnostics": {"CT": 2, "XRAY": 2, "LAB": 3},
    },
    "simulation": {"ticks": 80},
    "events": [
        {"time": 12, "type": "oxygen_reduction", "percentage": 25},
        {"time": 20, "type": "ventilator_failure", "count": 1},
    ],
    "patients": patients,
}
Path("data/scenarios/S6_resource_stress.json").write_text(json.dumps(scenario, indent=2) + "\n")
print("wrote S6_resource_stress.json")
