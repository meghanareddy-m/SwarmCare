import pytest

from agents.swarm_agents import Bid, ResourceOfferAgent, reserve_units
from algorithms.decentralized import make_decentralized_allocator
from algorithms.fuzzy_baseline import fuzzy_allocate
from experiments.runner import list_scenarios, run_simulation, scenario_path
from simulation.hospital import HospitalSimulator
from tests.helpers import make_scenario


class P:
    def __init__(self, pid, severity): self.patient_id, self.severity = pid, severity


def test_agent_grants_highest_priority_bids_first():
    agent = ResourceOfferAgent("icu", remaining=1)
    won, permanent, outranked = agent.evaluate([Bid(P("a", 0.9), 0.4), Bid(P("b", 0.9), 0.9)])
    assert [b.patient.patient_id for b in won] == ["b"]
    assert [b.patient.patient_id for b in outranked] == ["a"]
    assert permanent == []
    assert agent.messages_received == 2


def test_agent_with_no_stock_refuses_permanently():
    won, permanent, outranked = ResourceOfferAgent("o2", remaining=0).evaluate([Bid(P("a", 0.9), 1.0)])
    assert won == [] and outranked == [] and len(permanent) == 1


def test_reserve_policy_blocks_low_severity_only():
    agent = ResourceOfferAgent("o2", remaining=2, reserve=2, reserve_min_severity=0.6)
    won, permanent, _ = agent.evaluate([Bid(P("low", 0.3), 0.9), Bid(P("high", 0.8), 0.1)])
    assert [b.patient.patient_id for b in won] == ["high"]
    assert [b.patient.patient_id for b in permanent] == ["low"]


def test_reserve_units():
    assert reserve_units(100, 0.1) == 10
    assert reserve_units(7, 0.1) == 1
    assert reserve_units(50, 0) == 0


@pytest.mark.parametrize("scenario", list_scenarios())
def test_without_reserve_it_reproduces_centralized_fuzzy(scenario):
    """Sanity check of the protocol: same local priorities + same constraints
    give the same outcome as the centralized fuzzy sort."""
    path = scenario_path(scenario)
    fuzzy = run_simulation(path, fuzzy_allocate)
    dec = run_simulation(path, make_decentralized_allocator())
    assert dec["fitness"] == fuzzy["fitness"]
    assert dec["conflicts"] == fuzzy["conflicts"]
    assert dec["completed"] == fuzzy["completed"]
    assert dec["messages"] > 0


def test_negotiation_never_double_books_a_doctor(tmp_path):
    path = make_scenario(tmp_path, [(f"P{i}", 0.5, False, False, 0, 3) for i in range(6)],
                         doctors=2, ward=10)
    sim = HospitalSimulator(path)
    stats = make_decentralized_allocator()(sim)
    assert stats["treated"] == 2
    assert stats["resource_conflicts"] == 4
    assert sorted(p.assigned_doctor for p in sim.treatment_patients()) == ["D1", "D2"]


def test_patient_needing_scarce_resource_does_not_block_others(tmp_path):
    # X needs a ventilator (none free); Y should still be admitted.
    path = make_scenario(tmp_path, [("X", 0.9, False, True, 0, 3), ("Y", 0.3, False, False, 0, 3)],
                         doctors=2, icu=2, ventilators=0)
    sim = HospitalSimulator(path)
    make_decentralized_allocator()(sim)
    assert {p.patient_id for p in sim.treatment_patients()} == {"Y"}


def test_oxygen_reserve_defers_low_severity_when_stock_is_low(tmp_path):
    path = make_scenario(tmp_path, [("low", 0.3, True, False, 0, 3), ("high", 0.7, True, False, 0, 3)],
                         doctors=2, oxygen=2)
    sim = HospitalSimulator(path)
    alloc = make_decentralized_allocator(oxygen_reserve_fraction=1.0, oxygen_reserve_min_severity=0.5)
    alloc(sim)
    assert {p.patient_id for p in sim.treatment_patients()} == {"high"}


def test_no_waiting_patients_returns_zero_stats(tmp_path):
    path = make_scenario(tmp_path, [("A", 0.5, False, False, 10, 2)])
    sim = HospitalSimulator(path)
    assert make_decentralized_allocator()(sim)["treated"] == 0
