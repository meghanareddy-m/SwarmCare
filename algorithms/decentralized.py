"""Attempt 4: decentralized multi-agent negotiation (contract-net style).

There is no central sort of the waiting list. In every tick:

1. Each waiting patient agent computes its OWN priority (fuzzy logic on
   severity, waiting time, oxygen need) and sends bids to the resource agents
   it needs (doctor pool, ICU or ward beds, oxygen, ventilators).
2. Each resource agent independently grants its free units to the best bids it
   received (tentative grants) and, optionally, protects a reserve for severe
   patients when its stock is low.
3. A patient that received ALL grants commits; a patient that was refused for
   good withdraws (one conflict); a patient that was only outranked bids again
   next round. Rounds repeat until nothing changes or ``max_rounds`` is hit.

Admission constraints are the same as in the other attempts (see
``algorithms.common``), so the comparison is on equal terms. The negotiation
is executed synchronously inside one process: it is a simulation of a
decentralized protocol, not a distributed deployment.
"""

from agents.swarm_agents import Bid, build_resource_agents
from algorithms.common import available_resources, free_doctors, needs_icu
from algorithms.fuzzy_priority import fuzzy_priority

DEFAULT_POLICY = {
    "max_rounds": 8,
    "oxygen_reserve_fraction": 0.0,      # reserve policy is OFF by default
    "oxygen_reserve_min_severity": 0.50,
    "ventilator_reserve_fraction": 0.0,
    "ventilator_reserve_min_severity": 0.0,
}


def make_decentralized_allocator(**overrides):
    """Build the allocation function with a given local-policy configuration."""
    policy = {**DEFAULT_POLICY, **overrides}

    def allocate(simulator):
        patients = simulator.active_patients()
        if not patients:
            return {"treated": 0, "critical_treated": 0, "resource_conflicts": 0,
                    "messages": 0, "rounds": 0}

        free = available_resources(simulator)
        idle_doctors = free_doctors(simulator)
        initial = simulator.config["hospital"]

        agents = build_resource_agents(free, len(idle_doctors), initial, policy)

        # Local decision: every patient computes its own priority.
        priority = {p.patient_id: fuzzy_priority(p) for p in patients}
        pending = list(patients)
        treated = []
        messages = 0
        rounds = 0

        while pending and rounds < policy["max_rounds"]:
            rounds += 1
            inbox = {name: [] for name in agents}
            needs = {}
            for p in pending:
                wanted = ["doctor", "icu" if needs_icu(p) else "ward"]
                if p.oxygen_required:
                    wanted.append("oxygen")
                if p.ventilator_required:
                    wanted.append("ventilators")
                needs[p.patient_id] = wanted
                for name in wanted:
                    inbox[name].append(Bid(p, priority[p.patient_id]))
                    messages += 1

            granted = {}   # patient_id -> set of resource names granted
            refused = set()  # patients permanently refused this tick
            for name, agent in agents.items():
                won, permanent, _outranked = agent.evaluate(inbox[name])
                messages += len(won) + len(permanent)  # reply messages
                for bid in won:
                    granted.setdefault(bid.patient.patient_id, set()).add(name)
                for bid in permanent:
                    refused.add(bid.patient.patient_id)

            still_pending = []
            for p in pending:
                pid = p.patient_id
                if pid in refused:
                    continue  # withdraws -> counted as one conflict below
                if granted.get(pid, set()) >= set(needs[pid]):
                    doctor = idle_doctors.pop(0)
                    _commit(simulator, p, doctor, needs[pid], agents)
                    treated.append(p)
                    messages += len(needs[pid])  # commit messages
                else:
                    still_pending.append(p)

            if len(still_pending) == len(pending):
                pending = still_pending
                break  # no progress this round
            pending = still_pending

        conflicts = len(patients) - len(treated)
        simulator.total_conflicts += conflicts
        simulator.total_assignments += len(treated)
        return {
            "treated": len(treated),
            "critical_treated": sum(needs_icu(p) for p in treated),
            "resource_conflicts": conflicts,
            "messages": messages,
            "rounds": rounds,
            "agent_messages": {n: a.messages_received for n, a in agents.items()},
            "reserve_blocked": sum(a.reserve_blocked for a in agents.values()),
        }

    return allocate


def _commit(simulator, patient, doctor, wanted, agents):
    for name in wanted:
        agents[name].commit()
    doctor.current_load += 1
    patient.assigned_doctor = doctor.doctor_id
    patient.treated = True
    patient.remaining_service = patient.service_duration
    if needs_icu(patient):
        patient.assigned_bed = "ICU"
        simulator.total_icu_used += 1
    else:
        patient.assigned_bed = "WARD"
        simulator.total_ward_used += 1
    if patient.oxygen_required:
        simulator.total_oxygen_used += 1
    if patient.ventilator_required:
        simulator.total_ventilator_used += 1


def decentralized_allocate(simulator):
    """Attempt 4 with the default local policy."""
    return make_decentralized_allocator()(simulator)
