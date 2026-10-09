# Sta Live

Experimental branch for a **Mantra 10-team / 500-credit** live-auction decision engine.

The first milestone deliberately contains **no production web automation**. It implements and stress-tests the strategic brain offline before any FantaLab page adapter is connected.

## Core principles

1. **Titolarità first.** Multirole value never compensates for a structurally low probability of starting.
2. **Durability correction.** Injury-prone profiles are discounted.
3. **Dynamic scarcity.** The ceiling rises when acceptable alternatives in a required cluster disappear.
4. **Opponent pressure.** Remaining credits and unmet clusters of opponents affect the live ceiling, but only inside bounded limits.
5. **Market adaptation.** Observed auction price/market-value ratios adapt future ceilings with hard bounds.
6. **Budget guard.** The engine cannot spend credits needed to finish the roster.
7. **Price support (disturbo) with accidental-win safety.** The engine may raise a materially underpriced high-value player even when not a primary target, but only to a price at which acquiring the player would still be acceptable.
8. **Fail closed.** If later browser-state parsing is stale, contradictory, or incomplete, the executor must PASS rather than bid.

## Architecture target

`FantaLab visible UI -> local adapter -> Auction Brain -> dynamic ceiling -> deterministic executor`

The AI supervisor sits above the deterministic executor: it may update player clusters, strategic priorities and state interpretation, but it may not bypass hard ceilings or budget guards.

## Current modules

- `sta_live/auction_brain.py`: valuation, scarcity, opponent pressure, price support, fail-safe budget logic.
- `sta_live/plan_manager.py`: formation/strategy fallback when a required cluster becomes unattainable.
- `sta_live/simulator.py`: offline stochastic auction simulator.
- `sta_live/sample_data.py`: synthetic Mantra-style test pool.
- `tests/test_auction_brain.py`: invariants, plan-switch tests and Monte Carlo smoke tests.

## Validation performed

- 11 unit/integration tests: PASS.
- Python compile check: PASS.
- 20,000 randomized auction states: 0 unsafe bids beyond roster-completion reserve.
- Offline Monte Carlo comparison with/without price-support: no budget violations; price-support raises materially underpriced players while staying under accidental-win-safe caps.

## Next milestone

Build a read-only FantaLab DOM adapter against captured/sanitized page fixtures, then a dry-run executor that logs `BID/PASS` without clicking. Enable real clicks only after fixture tests and a supervised rehearsal.
