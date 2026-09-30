import json
from copy import deepcopy

from agents.entities import PatientAgent, DoctorAgent


class HospitalSimulator:
    """Discrete-time synthetic hospital environment."""

    def __init__(self, scenario_path):
        with open(scenario_path, "r") as f:
            self.config = json.load(f)

        h = self.config["hospital"]
        self.scenario_id = self.config["scenario_id"]
        self.description = self.config["description"]
        self.max_ticks = self.config["simulation"]["ticks"]

        # Current capacities. These are modified by perturbation events.
        self.icu_beds = h["icu_beds"]
        self.ward_beds = h["ward_beds"]
        self.oxygen = h["oxygen_units"]
        self.ventilators = h["ventilators"]
        self.diagnostics = deepcopy(h["diagnostics"])

        self.doctors = [
            DoctorAgent(f"D{i+1}", capacity=1)
            for i in range(h["doctors"])
        ]

        self.patients = [
            PatientAgent(
                patient_id=p["patient_id"],
                severity=p["severity"],
                oxygen_required=p["oxygen_required"],
                ventilator_required=p["ventilator_required"],
                arrival_time=p["arrival_time"],
                service_duration=p.get("service_duration", 1),
            )
            for p in self.config["patients"]
        ]
        for patient in self.patients:
            patient.completed = False
            patient.remaining_service = 0

        self.events = sorted(
            self.config.get("events", []),
            key=lambda e: e["time"]
        )
        self.event_index = 0
        self.time = 0
        self.total_conflicts = 0
        self.total_assignments = 0
        self.total_icu_used = 0
        self.total_ward_used = 0
        self.total_oxygen_used = 0
        self.total_ventilator_used = 0

    def active_patients(self):
        return [p for p in self.patients if (p.arrival_time <= self.time and not p.treated and not p.completed)]

    def treatment_patients(self):
        """Return patients currently occupying treatment resources."""
        return [
            p
            for p in self.patients
            if p.treated
        ]

    def apply_events(self):
        """Apply every event scheduled for the current tick."""
        while self.event_index < len(self.events):
            event = self.events[self.event_index]
            if event["time"] > self.time:
                break

            event_type = event["type"]

            if event_type == "icu_beds_removed":
                self.icu_beds = max(0, self.icu_beds - event["count"])

            elif event_type == "oxygen_reduction":
                self.oxygen = max(
                    0,
                    int(self.oxygen * (1 - event["percentage"] / 100))
                )

            elif event_type == "ventilator_failure":
                self.ventilators = max(
                    0,
                    self.ventilators - event["count"]
                )

            elif event_type == "doctor_unavailable":
                available = [d for d in self.doctors if d.available]
                for doctor in available[:event["count"]]:
                    doctor.available = False

            # patient_surge is represented by patient arrival_time in the data.
            self.event_index += 1

    def reset_tick_allocations(self):
        """Reset per-tick doctor loads and patient assignment labels."""
        for doctor in self.doctors:
            doctor.current_load = 0

        for patient in self.patients:
            if not patient.treated:
                patient.assigned_doctor = None
                patient.assigned_bed = None

    def step(self):
        """Advance one simulation tick."""
        self.apply_events()
        for patient in self.treatment_patients():
            patient.remaining_service -= 1
            if patient.remaining_service <= 0:
                for doctor in self.doctors:
                    if (doctor.doctor_id== patient.assigned_doctor):
                        doctor.current_load = max(0,doctor.current_load - 1)
                        break
                patient.treated = False
                patient.completed = True
                patient.assigned_doctor = None
                patient.assigned_bed = None

        for patient in self.active_patients():
            patient.waiting_time += 1
        self.time += 1

    def state_summary(self):
        active = self.active_patients()
        return {
            "time": self.time,
            "active_unserved": len(active),
            "treated": sum(p.treated for p in self.patients),
            "icu_beds": self.icu_beds,
            "ward_beds": self.ward_beds,
            "oxygen": self.oxygen,
            "ventilators": self.ventilators,
            "available_doctors": sum(d.available for d in self.doctors),
        }
