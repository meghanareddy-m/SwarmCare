from dataclasses import dataclass
from typing import Optional

@dataclass
class PatientAgent:
    patient_id: str
    severity: float
    oxygen_required: bool
    ventilator_required: bool
    arrival_time: int
    service_duration: int = 3
    waiting_time: int = 0
    treated: bool = False
    completed: bool = False
    remaining_service: int = 0
    assigned_doctor: Optional[str] = None
    assigned_bed: Optional[str] = None


@dataclass
class DoctorAgent:
    doctor_id: str
    capacity: int = 1
    available: bool = True
    current_load: int = 0


@dataclass
class ResourceAgent:
    resource_type: str
    resource_id: str
    available: bool = True