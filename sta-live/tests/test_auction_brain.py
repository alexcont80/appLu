from sta_live.auction_brain import (
    Action, AuctionState, OpponentState, OurTeamState,
    StrategyConfig, decide, dynamic_ceiling, safe_spend_limit,
)
from sta_live.sample_data import sample_players, sample_requirements
from sta_live.simulator import run_many
from sta_live.plan_manager import StrategyPlan, choose_plan


def state_for(pid, next_bid, remaining=None, credits=500, cluster_counts=None, slots=20, realized=None):
    players = sample_players()
    reqs = sample_requirements()
    return AuctionState(
        current_player_id=pid,
        current_price=max(0, next_bid - 1),
        next_bid=next_bid,
        remaining_player_ids=set(remaining or players.keys()),
        our_team=OurTeamState(
            credits=credits,
            cluster_counts=dict(cluster_counts or {}),
            minimum_slots_left=slots,
            min_credit_per_slot=1,
        ),
        opponents=[
            OpponentState("o1", 420, missing_clusters={players[pid].cluster}, minimum_slots_left=17),
            OpponentState("o2", 210, missing_clusters={players[pid].cluster}, minimum_slots_left=10),
        ],
        requirements=reqs,
        realized_price_ratios=list(realized or []),
    )


def test_titolarita_dominates_multirole():
    players = sample_players()
    c1, _ = dynamic_ceiling(state_for("ct1", 1), players["ct1"], StrategyConfig())
    c2, _ = dynamic_ceiling(state_for("ct2", 1), players["ct2"], StrategyConfig())
    assert c1 > c2 * 1.35


def test_scarcity_raises_ceiling_when_last_viable_option():
    players = sample_players()
    broad = state_for("ew3", 1, remaining=set(players.keys()))
    scarce = state_for("ew3", 1, remaining={"ew3", "pc1", "pc2", "pc3", "dc1", "dc2"})
    c1, _ = dynamic_ceiling(broad, players["ew3"], StrategyConfig())
    c2, _ = dynamic_ceiling(scarce, players["ew3"], StrategyConfig())
    assert c2 > c1


def test_requirement_already_met_reduces_ceiling():
    players = sample_players()
    c1, _ = dynamic_ceiling(state_for("wa2", 1), players["wa2"], StrategyConfig())
    c2, _ = dynamic_ceiling(state_for("wa2", 1, cluster_counts={"WA_STARTER": 1}), players["wa2"], StrategyConfig())
    assert c2 < c1


def test_never_breaks_budget_reserve():
    players = sample_players()
    s = state_for("pc1", 100, credits=30, slots=20)
    d = decide(s, players)
    assert safe_spend_limit(s.our_team) == 10
    assert d.ceiling <= 10
    assert d.action == Action.PASS


def test_market_inflation_is_bounded():
    players = sample_players()
    s = state_for("wa1", 1, realized=[2.0] * 20)
    _, diag = dynamic_ceiling(s, players["wa1"], StrategyConfig())
    assert diag["market"] <= StrategyConfig().max_market_factor


def test_price_support_bids_only_if_underpriced_and_safe():
    players = sample_players()
    d = decide(state_for("lux1", 20), players)
    assert d.action == Action.BID
    assert d.mode == "PRICE_SUPPORT"


def test_price_support_refuses_bad_accidental_win():
    players = sample_players()
    d = decide(state_for("lux1", 55), players)
    assert d.action == Action.PASS


def test_monte_carlo_has_no_invalid_budget_states():
    stats = run_many(sample_players(), sample_requirements(), runs=100, seed=77)
    assert stats["invalid_states"] == 0
    assert 0.0 <= stats["avg_completion_ratio"] <= 1.0


def test_price_support_generates_bids_in_simulation():
    stats = run_many(sample_players(), sample_requirements(), runs=50, seed=991, config=StrategyConfig(nuisance_enabled=True))
    assert stats["avg_price_support_bids"] > 0


def test_plan_switches_when_primary_cluster_becomes_impossible():
    reqs = sample_requirements()
    primary = StrategyPlan("3-4-2-1", {"EW_PREMIUM": reqs["EW_PREMIUM"], "WA_STARTER": reqs["WA_STARTER"]}, priority=1.1)
    fallback = StrategyPlan("4-2-3-1", {"WA_STARTER": reqs["WA_STARTER"], "SIDE": reqs["SIDE"]}, priority=1.0)
    s = state_for("wa1", 1, remaining={"wa1", "wa2", "wa3", "dd1", "ds1"})
    choice = choose_plan([primary, fallback], s)
    assert choice.name == "4-2-3-1"
    assert choice.feasible


def test_primary_plan_retained_when_feasible_and_preferred():
    reqs = sample_requirements()
    primary = StrategyPlan("3-4-2-1", {"EW_PREMIUM": reqs["EW_PREMIUM"], "WA_STARTER": reqs["WA_STARTER"]}, priority=1.1)
    fallback = StrategyPlan("4-2-3-1", {"WA_STARTER": reqs["WA_STARTER"], "SIDE": reqs["SIDE"]}, priority=1.0)
    choice = choose_plan([primary, fallback], state_for("wa1", 1))
    assert choice.name == "3-4-2-1"
