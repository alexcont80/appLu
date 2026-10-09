from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .auction_brain import AuctionState, ClusterRequirement


@dataclass(frozen=True)
class StrategyPlan:
    name: str
    requirements: Mapping[str, ClusterRequirement]
    priority: float = 1.0


@dataclass(frozen=True)
class PlanAssessment:
    name: str
    feasible: bool
    score: float
    missing_units: int
    scarce_units: int
    reason: str


def assess_plan(plan: StrategyPlan, state: AuctionState) -> PlanAssessment:
    missing_units = 0
    scarce_units = 0
    feasibility_margin = 0

    for cluster, req in plan.requirements.items():
        have = state.our_team.cluster_counts.get(cluster, 0)
        need = max(0, req.minimum - have)
        if need == 0:
            continue
        left = sum(1 for pid in req.candidate_ids if pid in state.remaining_player_ids)
        missing_units += need
        feasibility_margin += left - need
        if left < need:
            return PlanAssessment(
                plan.name,
                False,
                -1e9,
                missing_units,
                scarce_units,
                f"cluster {cluster} requires {need} but only {left} viable candidates remain",
            )
        if left <= need + 1:
            scarce_units += need

    score = plan.priority * 100.0 + feasibility_margin * 2.0 - scarce_units * 9.0 - missing_units * 1.5
    return PlanAssessment(plan.name, True, score, missing_units, scarce_units, "feasible")


def choose_plan(plans: Sequence[StrategyPlan], state: AuctionState) -> PlanAssessment:
    assessments = [assess_plan(p, state) for p in plans]
    feasible = [a for a in assessments if a.feasible]
    if not feasible:
        return max(assessments, key=lambda a: a.score)
    return max(feasible, key=lambda a: a.score)
