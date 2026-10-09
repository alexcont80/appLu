from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Mapping, Optional, Set, Tuple
import math


class Action(str, Enum):
    BID = "BID"
    PASS = "PASS"


@dataclass(frozen=True)
class Player:
    player_id: str
    name: str
    roles: Tuple[str, ...]
    cluster: str
    base_value: float
    market_value: float
    titolarita: float = 1.0
    durability: float = 1.0
    multirole_score: float = 0.0
    bonus_score: float = 0.5
    hard_cap: Optional[int] = None


@dataclass
class OpponentState:
    team_id: str
    credits: int
    roster_size: int = 0
    missing_clusters: Set[str] = field(default_factory=set)
    minimum_slots_left: int = 0


@dataclass
class OurTeamState:
    credits: int
    roster: List[str] = field(default_factory=list)
    cluster_counts: Dict[str, int] = field(default_factory=dict)
    minimum_slots_left: int = 0
    min_credit_per_slot: int = 1


@dataclass(frozen=True)
class ClusterRequirement:
    cluster: str
    minimum: int
    candidate_ids: Tuple[str, ...]


@dataclass
class AuctionState:
    current_player_id: str
    current_price: int
    next_bid: int
    remaining_player_ids: Set[str]
    our_team: OurTeamState
    opponents: List[OpponentState]
    requirements: Mapping[str, ClusterRequirement]
    realized_price_ratios: List[float] = field(default_factory=list)


@dataclass(frozen=True)
class StrategyConfig:
    budget: int = 500
    nuisance_enabled: bool = True
    nuisance_quality_floor: float = 0.72
    nuisance_market_discount: float = 0.70
    nuisance_accidental_win_discount: float = 0.86
    nuisance_max_share_of_free_budget: float = 0.22
    max_market_factor: float = 1.18
    min_market_factor: float = 0.88
    max_dynamic_multiplier: float = 1.45
    min_dynamic_multiplier: float = 0.65


@dataclass(frozen=True)
class Decision:
    action: Action
    ceiling: int
    mode: str
    reason: str
    diagnostics: Mapping[str, float]


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def quality_score(p: Player) -> float:
    return _clamp(
        0.38 * p.titolarita +
        0.24 * p.durability +
        0.20 * p.bonus_score +
        0.18 * p.multirole_score,
        0.0,
        1.0,
    )


def reserve_required(team: OurTeamState) -> int:
    return max(0, team.minimum_slots_left) * max(1, team.min_credit_per_slot)


def safe_spend_limit(team: OurTeamState) -> int:
    return max(0, team.credits - reserve_required(team))


def cluster_need(state: AuctionState, cluster: str) -> int:
    req = state.requirements.get(cluster)
    if not req:
        return 0
    have = state.our_team.cluster_counts.get(cluster, 0)
    return max(0, req.minimum - have)


def eligible_candidates_left(state: AuctionState, cluster: str) -> int:
    req = state.requirements.get(cluster)
    if not req:
        return 999
    return sum(1 for pid in req.candidate_ids if pid in state.remaining_player_ids)


def scarcity_multiplier(state: AuctionState, p: Player) -> float:
    need = cluster_need(state, p.cluster)
    if need <= 0:
        return 0.88
    left = eligible_candidates_left(state, p.cluster)
    if left <= need:
        return 1.32
    ratio = left / max(1, need)
    if ratio <= 1.5:
        return 1.24
    if ratio <= 2.0:
        return 1.16
    if ratio <= 3.0:
        return 1.08
    return 1.00


def need_multiplier(state: AuctionState, p: Player) -> float:
    need = cluster_need(state, p.cluster)
    if need <= 0:
        return 0.80
    left = eligible_candidates_left(state, p.cluster)
    if left <= need:
        return 1.24
    if need >= 2:
        return 1.10
    return 1.04


def market_multiplier(state: AuctionState, cfg: StrategyConfig) -> float:
    ratios = [r for r in state.realized_price_ratios if 0.25 <= r <= 3.0]
    if not ratios:
        return 1.0
    ratios = sorted(ratios)
    if len(ratios) >= 5:
        trim = max(1, len(ratios) // 10)
        ratios = ratios[trim:-trim] or ratios
    return _clamp(sum(ratios) / len(ratios), cfg.min_market_factor, cfg.max_market_factor)


def opponent_pressure(state: AuctionState, p: Player) -> float:
    pressures: List[float] = []
    for opp in state.opponents:
        if p.cluster not in opp.missing_clusters:
            continue
        reserve = max(0, opp.minimum_slots_left)
        free = max(0, opp.credits - reserve)
        liquidity = _clamp(free / max(1.0, p.market_value), 0.0, 2.0) / 2.0
        pressures.append(liquidity)
    if not pressures:
        return 0.0
    pressures.sort(reverse=True)
    score = pressures[0]
    if len(pressures) > 1:
        score = 0.72 * score + 0.28 * pressures[1]
    return _clamp(score, 0.0, 1.0)


def opponent_multiplier(state: AuctionState, p: Player) -> float:
    return 0.98 + 0.12 * opponent_pressure(state, p)


def intrinsic_multiplier(p: Player) -> float:
    # Titolarità dominates: a multirole bench player must remain discounted.
    titular = 0.58 + 0.52 * _clamp(p.titolarita, 0.0, 1.0)
    durable = 0.68 + 0.35 * _clamp(p.durability, 0.0, 1.0)
    multi = 1.0 + 0.14 * _clamp(p.multirole_score, 0.0, 1.0)
    bonus = 0.94 + 0.12 * _clamp(p.bonus_score, 0.0, 1.0)
    return titular * durable * multi * bonus


def dynamic_ceiling(state: AuctionState, p: Player, cfg: StrategyConfig) -> Tuple[int, Dict[str, float]]:
    intr = intrinsic_multiplier(p)
    scar = scarcity_multiplier(state, p)
    need = need_multiplier(state, p)
    market = market_multiplier(state, cfg)
    opp = opponent_multiplier(state, p)
    dynamic = _clamp(scar * need * market * opp, cfg.min_dynamic_multiplier, cfg.max_dynamic_multiplier)
    raw = p.base_value * intr * dynamic
    hard = p.hard_cap if p.hard_cap is not None else math.inf
    safe = safe_spend_limit(state.our_team)
    ceiling = max(0, int(math.floor(min(raw, hard, safe))))
    return ceiling, {
        "intrinsic": intr,
        "scarcity": scar,
        "need": need,
        "market": market,
        "opponent_pressure": opponent_pressure(state, p),
        "opponent_mult": opp,
        "raw_ceiling": raw,
        "safe_spend_limit": float(safe),
    }


def nuisance_ceiling(state: AuctionState, p: Player, cfg: StrategyConfig) -> Tuple[int, Dict[str, float]]:
    """Maximum safe price-support bid.

    Every disturbance bid must still be an acceptable accidental purchase.
    """
    safe = safe_spend_limit(state.our_team)
    cap_market = p.market_value * cfg.nuisance_accidental_win_discount
    cap_budget = safe * cfg.nuisance_max_share_of_free_budget
    hard = p.hard_cap if p.hard_cap is not None else math.inf
    ceiling = int(math.floor(max(0.0, min(cap_market, cap_budget, hard, safe))))
    return ceiling, {
        "quality": quality_score(p),
        "market_discount": state.next_bid / max(1.0, p.market_value),
        "nuisance_market_cap": cap_market,
        "nuisance_budget_cap": cap_budget,
        "safe_spend_limit": float(safe),
    }


def decide(state: AuctionState, players: Mapping[str, Player], cfg: StrategyConfig = StrategyConfig()) -> Decision:
    p = players[state.current_player_id]
    ceiling, diag = dynamic_ceiling(state, p, cfg)
    prefer_price_support = cluster_need(state, p.cluster) <= 0

    if state.next_bid <= ceiling and not prefer_price_support:
        return Decision(Action.BID, ceiling, "TARGET", f"next bid {state.next_bid} <= dynamic ceiling {ceiling}", diag)

    if cfg.nuisance_enabled:
        nceil, ndiag = nuisance_ceiling(state, p, cfg)
        discounted = ndiag["market_discount"] <= cfg.nuisance_market_discount
        safe = reserve_required(state.our_team) < state.our_team.credits
        if ndiag["quality"] >= cfg.nuisance_quality_floor and discounted and safe and state.next_bid <= nceil:
            merged = dict(diag)
            merged.update({f"nuisance_{k}": v for k, v in ndiag.items()})
            return Decision(
                Action.BID,
                nceil,
                "PRICE_SUPPORT",
                "high-value player is materially underpriced; raise only within accidental-win-safe cap",
                merged,
            )

    return Decision(Action.PASS, ceiling, "PASS", f"next bid {state.next_bid} exceeds acceptable ceiling {ceiling}", diag)
