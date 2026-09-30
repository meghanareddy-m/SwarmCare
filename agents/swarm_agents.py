"""Concrete negotiating agents for the decentralized allocator (Attempt 4).

These classes are *local decision makers*: each one sees only the requests
sent to it and its own remaining capacity. No agent has a global view of the
hospital and none sorts the full patient list.
"""

from dataclasses import dataclass, field
import math


@dataclass
class Bid:
    """A request message from a patient agent to a resource agent."""
    patient: object
    priority: float


@dataclass
class ResourceOfferAgent:
    """Local owner of one pool of interchangeable units (base class).

    Specialised as ``ICUAgent``, ``WardAgent``, ``OxygenAgent``,
    ``VentilatorAgent`` and ``DoctorPoolAgent``. The agent grants units to the highest-priority bidders it
    received. Optionally it applies a *reserve policy*: once its stock is at or
    below ``reserve`` units it only serves patients with
    ``severity >= reserve_min_severity`` (a local shortage-conservation rule).
    """

    name: str
    remaining: int
    reserve: int = 0
    reserve_min_severity: float = 0.0
    messages_received: int = 0
    reserve_blocked: int = 0  # bids refused only because of the reserve policy
    granted_ids: set = field(default_factory=set)

    def evaluate(self, bids):
        """Return ``(granted, denied_permanently, denied_for_now)``.

        ``denied_permanently``: no capacity or blocked by the reserve policy,
        so retrying in this tick is pointless.
        ``denied_for_now``: outranked this round; capacity may remain.
        """
        self.messages_received += len(bids)
        ranked = sorted(bids, key=lambda b: b.priority, reverse=True)
        granted, permanent, outranked = [], [], []
        slots = self.remaining
        for bid in ranked:
            eligible = (
                self.remaining > self.reserve
                or bid.patient.severity >= self.reserve_min_severity
            )
            if self.remaining <= 0 or not eligible:
                if self.remaining > 0 and not eligible:
                    self.reserve_blocked += 1
                permanent.append(bid)
            elif slots > 0:
                granted.append(bid)
                slots -= 1
            else:
                outranked.append(bid)
        return granted, permanent, outranked

    def commit(self):
        self.remaining -= 1


@dataclass
class DoctorPoolAgent(ResourceOfferAgent):
    """Owner of the pool of idle, available doctors (no reserve policy)."""


@dataclass
class ICUAgent(ResourceOfferAgent):
    """Local owner of free ICU beds. Serves patients with severity >= 0.80."""


@dataclass
class WardAgent(ResourceOfferAgent):
    """Local owner of free ward beds."""


@dataclass
class OxygenAgent(ResourceOfferAgent):
    """Local owner of free oxygen units; may protect a reserve for severe patients."""


@dataclass
class VentilatorAgent(ResourceOfferAgent):
    """Local owner of free ventilators; may protect a reserve for severe patients."""


def build_resource_agents(free, idle_doctors, initial, policy):
    """Create one specialised agent per resource type, keyed by resource name.

    ``free`` is ``algorithms.common.available_resources`` output, ``idle_doctors``
    a count, ``initial`` the scenario's ``hospital`` dict (reserve fractions are
    relative to the *initial* capacity) and ``policy`` the decentralized policy
    dict. With the default policy this is behaviour-identical to the former pooled
    ``ResourceOfferAgent`` construction.
    """
    return {
        "doctor": DoctorPoolAgent("doctor", idle_doctors),
        "icu": ICUAgent("icu", free["icu"]),
        "ward": WardAgent("ward", free["ward"]),
        "oxygen": OxygenAgent(
            "oxygen", free["oxygen"],
            reserve=reserve_units(initial["oxygen_units"], policy["oxygen_reserve_fraction"]),
            reserve_min_severity=policy["oxygen_reserve_min_severity"]),
        "ventilators": VentilatorAgent(
            "ventilators", free["ventilators"],
            reserve=reserve_units(initial["ventilators"], policy["ventilator_reserve_fraction"]),
            reserve_min_severity=policy["ventilator_reserve_min_severity"]),
    }


def reserve_units(capacity, fraction):
    """Units kept in reserve for high-severity patients."""
    return int(math.ceil(capacity * fraction)) if fraction > 0 else 0
