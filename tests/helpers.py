"""Small builders for hand-made scenarios used in unit tests."""
import json


def make_scenario(tmp_path, patients, *, doctors=2, icu=1, ward=2, oxygen=2,
                  ventilators=1, events=None, ticks=20, name="T_tiny", extras=None,
                  diagnostics=None):
    data = {
        "scenario_id": name,
        "description": "unit-test scenario",
        "hospital": {"doctors": doctors, "icu_beds": icu, "ward_beds": ward,
                     "oxygen_units": oxygen, "ventilators": ventilators,
                     "diagnostics": diagnostics or {"CT": 1}},
        "simulation": {"ticks": ticks},
        "events": events or [],
        "patients": [
            {"patient_id": pid, "severity": sev, "oxygen_required": ox,
             "ventilator_required": vent, "arrival_time": arr, "service_duration": dur}
            for pid, sev, ox, vent, arr, dur in patients
        ],
        # optional per-patient extras, e.g. {"P1": {"spo2": 85, "diagnostic": "CT"}}
    }
    for patient in data["patients"]:
        patient.update((extras or {}).get(patient["patient_id"], {}))
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(data))
    return path
