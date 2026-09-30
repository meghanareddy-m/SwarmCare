"""Item 4: pooled ResourceOfferAgent split into specialised resource agents."""
import pytest

from agents.swarm_agents import (Bid, DoctorPoolAgent, ICUAgent, OxygenAgent, ResourceOfferAgent,
                                 VentilatorAgent, WardAgent, build_resource_agents)
from algorithms.decentralized import DEFAULT_POLICY, make_decentralized_allocator
from algorithms.fuzzy_baseline import fuzzy_allocate
from experiments.runner import list_scenarios, run_simulation, scenario_path

FREE = {"icu": 3, "ward": 7, "oxygen": 40, "ventilators": 5}
INITIAL = {"oxygen_units": 100, "ventilators": 10}


def test_one_specialised_agent_per_resource():
    agents = build_resource_agents(FREE, 4, INITIAL, DEFAULT_POLICY)
    assert list(agents) == ["doctor", "icu", "ward", "oxygen", "ventilators"]
    assert isinstance(agents["doctor"], DoctorPoolAgent)
    assert isinstance(agents["icu"], ICUAgent)
    assert isinstance(agents["ward"], WardAgent)
    assert isinstance(agents["oxygen"], OxygenAgent)
    assert isinstance(agents["ventilators"], VentilatorAgent)
    assert all(isinstance(a, ResourceOfferAgent) for a in agents.values())


def test_default_policy_reproduces_former_pooled_agents_exactly():
    """Same name, stock and reserve settings as the old pooled construction."""
    agents = build_resource_agents(FREE, 4, INITIAL, DEFAULT_POLICY)
    pooled = {
        "doctor": ResourceOfferAgent("doctor", 4),
        "icu": ResourceOfferAgent("icu", 3),
        "ward": ResourceOfferAgent("ward", 7),
        "oxygen": ResourceOfferAgent("oxygen", 40, reserve=0, reserve_min_severity=0.5),
        "ventilators": ResourceOfferAgent("ventilators", 5, reserve=0, reserve_min_severity=0.0),
    }
    for name, old in pooled.items():
        new = agents[name]
        assert (new.name, new.remaining, new.reserve, new.reserve_min_severity) == \
               (old.name, old.remaining, old.reserve, old.reserve_min_severity)


def test_reserve_policy_only_reaches_oxygen_and_ventilator_agents():
    policy = {**DEFAULT_POLICY, "oxygen_reserve_fraction": 0.2, "ventilator_reserve_fraction": 0.3,
              "oxygen_reserve_min_severity": 0.6, "ventilator_reserve_min_severity": 0.7}
    agents = build_resource_agents(FREE, 4, INITIAL, policy)
    assert (agents["oxygen"].reserve, agents["oxygen"].reserve_min_severity) == (20, 0.6)
    assert (agents["ventilators"].reserve, agents["ventilators"].reserve_min_severity) == (3, 0.7)
    for name in ("doctor", "icu", "ward"):
        assert agents[name].reserve == 0


def test_specialised_agents_keep_the_bidding_behaviour():
    class P:
        def __init__(self, pid, sev): self.patient_id, self.severity = pid, sev
    agent = ICUAgent("icu", remaining=1)
    won, permanent, outranked = agent.evaluate([Bid(P("a", 0.9), 0.2), Bid(P("b", 0.9), 0.8)])
    assert [b.patient.patient_id for b in won] == ["b"]
    assert [b.patient.patient_id for b in outranked] == ["a"]
    assert permanent == []


def test_reserve_refusals_are_counted_separately_from_empty_stock():
    class P:
        def __init__(self, pid, sev): self.patient_id, self.severity = pid, sev
    agent = OxygenAgent("oxygen", remaining=2, reserve=2, reserve_min_severity=0.8)
    agent.evaluate([Bid(P("low", 0.3), 0.9), Bid(P("high", 0.9), 0.1)])
    assert agent.reserve_blocked == 1
    empty = OxygenAgent("oxygen", remaining=0)
    empty.evaluate([Bid(P("x", 0.9), 0.9)])
    assert empty.reserve_blocked == 0


def test_reserve_policy_is_off_by_default():
    assert DEFAULT_POLICY["oxygen_reserve_fraction"] == 0.0
    assert DEFAULT_POLICY["ventilator_reserve_fraction"] == 0.0


@pytest.mark.parametrize("scenario", list_scenarios())
def test_pooled_behaviour_unchanged_matches_centralized_fuzzy(scenario):
    """Regression for the split: identical outcomes to the centralized fuzzy sort."""
    path = scenario_path(scenario)
    fuzzy = run_simulation(path, fuzzy_allocate)
    dec = run_simulation(path, make_decentralized_allocator())
    assert (dec["fitness"], dec["conflicts"], dec["completed"]) == \
           (fuzzy["fitness"], fuzzy["conflicts"], fuzzy["completed"])
