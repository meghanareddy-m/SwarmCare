import json
import random
from pathlib import Path
random.seed(42)
scenario_folder = Path("data/scenarios")
for scenario_file in scenario_folder.glob("*.json"):
    with open(scenario_file, "r") as file:
        data = json.load(file)
    for patient in data["patients"]:
        severity = patient["severity"]
        if severity >= 0.80:
            patient["service_duration"] = random.randint(5, 7)
        elif severity >= 0.50:
            patient["service_duration"] = random.randint(3, 5)
        else:
            patient["service_duration"] = random.randint(2, 4)
    with open(scenario_file, "w") as file:
        json.dump(data, file, indent=2)
    print(f"Updated {scenario_file.name}")