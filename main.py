#!/usr/bin/env python3
"""Polymarket FAA outage attribution forecaster (polymarket-faa-attribution-02).

Reads every *.in case in $MAKEFUN_INPUT_DIR (else /input/) and writes one
/output/<id>.out per case: for each market, 240 rows x 5 quantiles
(0.05, 0.25, 0.5, 0.75, 0.95) of the Yes price at minutes at+1 .. at+240.

Method (per market, from the case's own prices only, stdlib only, no network):
  * Median: the last price (persistence). Prediction-market prices are
    near-martingales; drift estimated from the recent trend was measured to
    hurt on the practice instance, so drift is 0.
  * Spread: realized volatility of 1-minute price changes over the last
    120 minutes, shrunk by 0.50 (1-minute changes overstate true diffusion
    because microstructure noise mean-reverts), floored at 0.0005 and
    capped at 0.005 per sqrt-minute. A short window adapts when a market's
    regime changes; dead markets stay tight, jumpy markets get honest tails.
    The 0.50 shrink and 0.005 cap were tuned on this contest's practice
    instance (p00-p04, answers from the next case's prices): they beat the
    earlier 0.45 / 0.008 in every case where the cap binds, pooled
    0.303 vs 0.311, vs the house baseline's 0.393 on the same cases.
  * Quantiles: q_tau = x + z_tau * sigma * sqrt(h), z the standard normal
    quantiles (-1.644854, -0.674490, 0, 0.674490, 1.644854), clamped to
    [0, 1], non-decreasing, rounded to 6 decimals.

Deterministic: no randomness, no network, no wall-clock use; two runs on
the same case write byte-identical output. Runs in well under 8 s per case.
"""

import glob
import json
import math
import os

Z = [-1.644854, -0.674490, 0.0, 0.674490, 1.644854]
SIGMA_WIN = 120       # minutes of recent history for volatility
SIGMA_SCALE = 0.50    # shrink: 1-min changes overstate diffusion
SIGMA_FLOOR = 0.0005  # per sqrt-minute
SIGMA_CAP = 0.005     # per sqrt-minute


def _std(vals):
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))


def forecast_market(prices, horizon):
    x = prices[-1]
    diffs = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    sigma = _std(diffs[-SIGMA_WIN:]) if len(diffs) >= 2 else 0.0
    sigma = min(SIGMA_CAP, max(SIGMA_FLOOR, sigma * SIGMA_SCALE))
    sqrt_h = [math.sqrt(h) for h in range(1, horizon + 1)]
    rows = []
    for h in range(horizon):
        spread = sigma * sqrt_h[h]
        row = []
        prev = -1.0
        for z in Z:
            q = min(1.0, max(0.0, x + z * spread))
            q = max(q, prev)  # keep quantiles non-decreasing after clamping
            q = round(q, 6) + 0.0  # +0.0 avoids -0.0
            row.append(q)
            prev = q
        rows.append(row)
    return rows


def forecast_case(case):
    horizon = case["horizon_minutes"]
    return {"forecasts": [
        {"id": m["id"], "q": forecast_market(m["prices"], horizon)}
        for m in case["markets"]
    ]}


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input/")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output/")
    os.makedirs(out_dir, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(in_dir, "*.in"))):
        with open(path) as f:
            case = json.load(f)
        out = forecast_case(case)
        name = os.path.splitext(os.path.basename(path))[0] + ".out"
        with open(os.path.join(out_dir, name), "w") as f:
            json.dump(out, f, separators=(",", ":"))


if __name__ == "__main__":
    main()
