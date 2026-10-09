# Sta Live architecture notes

## Decision loop

For the current player the brain calculates:

- intrinsic value corrected by starting probability, durability, bonus profile and useful multirole;
- whether the player's strategic cluster is still required;
- number of acceptable alternatives left in that cluster;
- market inflation/deflation learned from completed lots;
- opponent pressure from teams that both need the cluster and retain purchasing power;
- legal/safe spend after reserving minimum credits for remaining roster slots.

The result is a **dynamic ceiling**, not a static player price.

## Strategic clusters

Players are grouped by function, not only by nominal Mantra role. Example clusters:

- `EW_PREMIUM`: at least one high-value E/W or comparable cross-line asset;
- `WA_STARTER`: at least one reliable W/A starter;
- `MC_STARTER`: at least one reliable M/C;
- `CT_STARTER`: at least one C/T with sufficient starting probability;
- `PC`: two usable centre-forwards;
- `SIDE`: at least one Dd/E or Ds/E flexible wide player;
- `DC`: minimum central-defender backbone.

When alternatives disappear, the marginal cost of losing the current player rises. If a cluster becomes unattainable, the plan manager should switch architecture rather than chase the final weak candidate at any price.

## Opponent model

For each of nine opponents maintain:

- residual credits;
- minimum roster slots still to fill;
- acquired players;
- missing strategic clusters;
- inferred ability to bid for the current player.

Opponent pressure is bounded. It can justify a modest premium but can never override the hard cap or the roster-completion reserve.

## Price-support / disturbance strategy

A non-target player may still receive bids when all conditions are met:

1. composite quality exceeds the configured threshold;
2. the next bid is materially below estimated market value;
3. our roster-completion reserve remains protected;
4. the price is below an **accidental-win-safe ceiling**;
5. winning at that ceiling would remain acceptable.

The engine therefore never raises a player to a price we would regret paying if all opponents suddenly stop.

## Execution safety contract

A future executor must enforce:

- no bid when page state is stale;
- no bid if player identity is ambiguous;
- no bid if displayed budget conflicts with internal budget;
- no bid above dynamic ceiling;
- no bid above hard player cap;
- no bid that violates roster-completion reserve;
- one click -> confirmation -> state refresh before another action;
- emergency local kill switch;
- append-only decision log.

The executor stays deterministic and fast. Strategic reasoning belongs in the brain/supervisor layer, not in the five-second click path.
