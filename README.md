# This bet makes money on average. It ruined 999,506 of 1 million people.

Receipts for the Tensor108 video. Everything shown in the video comes from the files here.

## The game

A fair coin. Heads: your money grows by 50 %. Tails: you lose 40 %. Every player starts with $100.
Averaged over everyone, that is +5 % per flip. One player followed over time loses about 5 % per flip
(1.5 × 0.6 = 0.9 per heads-and-tails pair). The bet is non-ergodic.

## What was run

- **1,000,000 players, 1,000 flips each**, official seed **108**; a full re-run with seed **109** is reported
  alongside (where the two differ, the video uses the weaker wording).
- Level 1: everyone bets everything. Level 2: the same coins, betting 50 %, 25 % or 10 % of their money.
  Level 3: the same coins, players pooling and splitting their money equally after every flip (pairs, groups of 10, 100).
- The simulator was checked against exact binomial maths before the official runs: **29 / 29 checks passed**
  (`runs/validation/`).
- The rules and four predictions were written and frozen **before** the official runs:
  `docs/PREREGISTRATION.md`. Prediction 2 (the crowd average peaks between flip 100 and 250) was **wrong**:
  it peaked at flip 693 (seed 108; 555 in the re-run). It is left as written.

## Files

| Path | What |
|---|---|
| `sim/coin.py` | the simulator (exact log-wealth bookkeeping; money never reaches zero in this game) |
| `tools/validate.py` | the 29 checks against exact maths |
| `tools/run_official.py` | the official runs (`--seed 108`, `--seed 109`) |
| `tools/make_numbers.py` | builds `numbers.json`: every number on screen and in the script |
| `tools/check_numbers.py` | re-streams a run's coins and re-checks the headline numbers |
| `runs/official/seed108`, `seed109` | outputs: `summary.json`, per-flip stats, the wealth distribution every flip, sample paths, the richest player's history, logs |
| `numbers.json` | the numbers used in the video, with the prediction scores |

## Reproduce

```
pip install -r requirements.txt
python tools/validate.py --seed 1        (validation seed; official seeds are never used for checks)
python tools/run_official.py --seed 108
python tools/make_numbers.py
```

## Limits

A coin in a simulation, not the stock market: no fees, no taxes, and money that can be divided forever.
It shows a mechanism, not a forecast.

## Sources

- O. Peters, "The ergodicity problem in economics", Nature Physics 15, 1216-1221 (2019)
- O. Peters & W. Klein, "Ergodicity breaking in geometric Brownian motion", PRL 110, 100603 (2013)
- J. L. Kelly Jr., "A New Interpretation of Information Rate", Bell System Technical Journal 35(4), 917-926 (1956)
- E. O. Thorp, "The Kelly criterion in blackjack, sports betting, and the stock market" (2006)
- O. Peters & A. Adamou, "An evolutionary advantage of cooperation", arXiv 1506.03414
- Critics: J. Doctor, P. Wakker & T. Wang, "Economists' views on the ergodicity problem", Nature Physics 16, 1168 (2020)

Code: MIT licence. Data: CC BY 4.0.
