# FAA Outage Attribution Forecaster

Entry for make.fun competition `polymarket-faa-attribution-02`: forecast, minute
by minute and 4 hours ahead, the Yes price of every market of Polymarket's FAA
outage attribution family as five quantiles (0.05, 0.25, 0.5, 0.75, 0.95).

## Method

`main.py` (Python 3.13, standard library only, no network) reads each
`/input/<id>.in` case and writes `/output/<id>.out`. Per market, from the
case's own prices only:

- **Median: persistence.** The last price. Prediction-market prices are
  near-martingales; drift estimated from the recent trend was measured to
  hurt on the practice instance, so drift is 0.
- **Spread: realized volatility.** Standard deviation of 1-minute price
  changes over the last 120 minutes, shrunk by 0.50 (1-minute changes
  overstate true diffusion because microstructure noise mean-reverts),
  floored at 0.0005 and capped at 0.005 per sqrt-minute. A short window
  adapts when a market's regime changes; dead markets stay tight, jumpy
  markets get honest tails.
- **Quantiles:** `q_tau = x + z_tau * sigma * sqrt(h)`, with `z` the standard
  normal quantiles, clamped to [0, 1], non-decreasing, rounded to 6 decimals.

## Practice results (local)

Scored p00–p04 against the next case's prices (p05 has no next case to
answer it from):

| | pinball loss |
|---|---|
| This entry (pooled over items) | **0.303** |
| House persistence baseline, same cases | 0.393 |

The house baseline scores 0.363589 on the full 6-case practice. Per-case:
p00 0.472, p01 0.311, p02 0.337, p03 0.236, p04 0.201 (per-case means).
90% coverage 0.81–0.98. Two runs on the same cases are byte-identical;
all 6 practice cases run in ~0.45 s total, far under the 8 s per-case cap;
largest output 245 KB, under the 1 MiB cap.

## Files

- `main.py` — the entry program
- `README.md` — this file
- `LICENSE` — MIT
- `.makefun/owner.json` — payout wallet claim file
- `kit/` — the competition kit (not part of the entry)
