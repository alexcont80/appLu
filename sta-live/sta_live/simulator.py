from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Dict, List, Mapping, Sequence

from .auction_brain import (
    Action,
    AuctionState,
    ClusterRequirement,
    OpponentState,
    OurTeamState,
    Player,
    StrategyConfig,
    decide,
)


@dataclass
class SimulationResult:
    spent: int
    acquired: List[str]
    required_clusters_met: int
    total_required_clusters: int
    value_acquired: float
    price_support_bids: int
    price_support_wins: int
    invalid_states: int

    @property
    def completion_ratio(self) -> float:
        if self.total_required_clusters == 0:
            return 1.0
        return self.required_clusters_met / self.total_required_clusters


class AuctionSimulator:
    """Offline stochastic simulator. It does not connect to any website."""

    def __init__(
        self,
        players: Mapping[str, Player],
        requirements: Mapping[str, ClusterRequirement],
        budget: int = 500,
        roster_slots: int = 20,
        seed: int = 1,
        config: StrategyConfig | None = None,
    ) -> None:
        self.players = dict(players)
        self.requirements = dict(requirements)
        self.budget = budget
        self.roster_slots = roster_slots
        self.rng = Random(seed)
        self.cfg = config or StrategyConfig(budget=budget)

    def _opponents(self, n: int = 9) -> List[OpponentState]:
        clusters = set(self.requirements.keys())
        return [
            OpponentState(
                team_id=f"opp-{i+1}",
                credits=self.budget,
                missing_clusters=set(clusters),
                minimum_slots_left=self.roster_slots,
            )
            for i in range(n)
        ]

    def _opp_wtp(self, p: Player, opp: OpponentState) -> int:
        need_boost = 1.10 if p.cluster in opp.missing_clusters else 0.88
        noise = self.rng.uniform(0.72, 1.28)
        bankroll = max(1, opp.credits - max(0, opp.minimum_slots_left - 1))
        return max(1, min(int(p.market_value * need_boost * noise), bankroll))

    def run(self, order: Sequence[str] | None = None) -> SimulationResult:
        order = list(order or self.players.keys())
        our = OurTeamState(
            credits=self.budget,
            cluster_counts={},
            minimum_slots_left=self.roster_slots,
            min_credit_per_slot=1,
        )
        opponents = self._opponents()
        remaining = set(order)
        realized: List[float] = []
        acquired: List[str] = []
        price_support_bids = 0
        price_support_wins = 0
        invalid_states = 0
        spent = 0

        for pid in order:
            if pid not in remaining:
                continue
            p = self.players[pid]
            wtp = [(opp, self._opp_wtp(p, opp)) for opp in opponents]
            strongest_opp, strongest = max(wtp, key=lambda x: x[1])
            price = 1

            while True:
                next_bid = price + 1
                state = AuctionState(
                    current_player_id=pid,
                    current_price=price,
                    next_bid=next_bid,
                    remaining_player_ids=set(remaining),
                    our_team=our,
                    opponents=opponents,
                    requirements=self.requirements,
                    realized_price_ratios=list(realized),
                )
                d = decide(state, self.players, self.cfg)
                if d.ceiling > max(0, our.credits - our.minimum_slots_left):
                    invalid_states += 1

                if d.action != Action.BID:
                    final = max(price, min(strongest, max(price, next_bid)))
                    if p.market_value > 0:
                        realized.append(final / p.market_value)
                    strongest_opp.credits -= final
                    strongest_opp.roster_size += 1
                    strongest_opp.minimum_slots_left = max(0, strongest_opp.minimum_slots_left - 1)
                    strongest_opp.missing_clusters.discard(p.cluster)
                    break

                if d.mode == "PRICE_SUPPORT":
                    price_support_bids += 1

                if strongest < next_bid:
                    final = next_bid
                    our.credits -= final
                    spent += final
                    acquired.append(pid)
                    our.roster.append(pid)
                    our.cluster_counts[p.cluster] = our.cluster_counts.get(p.cluster, 0) + 1
                    our.minimum_slots_left = max(0, our.minimum_slots_left - 1)
                    if d.mode == "PRICE_SUPPORT":
                        price_support_wins += 1
                    if p.market_value > 0:
                        realized.append(final / p.market_value)
                    break

                price = next_bid
                if price >= our.credits:
                    invalid_states += 1
                    break

            remaining.discard(pid)

        met = sum(
            1
            for c, req in self.requirements.items()
            if our.cluster_counts.get(c, 0) >= req.minimum
        )
        value = sum(self.players[pid].base_value for pid in acquired)
        return SimulationResult(
            spent=spent,
            acquired=acquired,
            required_clusters_met=met,
            total_required_clusters=len(self.requirements),
            value_acquired=value,
            price_support_bids=price_support_bids,
            price_support_wins=price_support_wins,
            invalid_states=invalid_states,
        )


def run_many(
    players: Mapping[str, Player],
    requirements: Mapping[str, ClusterRequirement],
    runs: int = 250,
    seed: int = 100,
    config: StrategyConfig | None = None,
) -> Dict[str, float]:
    results: List[SimulationResult] = []
    ids = list(players.keys())
    for i in range(runs):
        r = Random(seed + i)
        order = ids[:]
        r.shuffle(order)
        sim = AuctionSimulator(players, requirements, seed=seed + i, config=config)
        results.append(sim.run(order))

    return {
        "runs": float(runs),
        "avg_spent": sum(x.spent for x in results) / runs,
        "avg_completion_ratio": sum(x.completion_ratio for x in results) / runs,
        "avg_value_acquired": sum(x.value_acquired for x in results) / runs,
        "avg_price_support_bids": sum(x.price_support_bids for x in results) / runs,
        "avg_price_support_wins": sum(x.price_support_wins for x in results) / runs,
        "invalid_states": float(sum(x.invalid_states for x in results)),
    }
