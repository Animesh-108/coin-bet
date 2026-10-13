## Pre-registration (written 2026-10-11 before any run; **FROZEN 2026-10-11** on the user's yes)

Written: 2026-10-11. Code: `sim/coin.py` (game), `tools/validate.py` (tool check), `tools/run_official.py` (to write
after the freeze).

- **The game:** fair coin; heads ×1.5, tails ×0.6 on the money bet; start $100; flips in rounds, no fees, money
  infinitely divisible. One coin stream (PCG64, one row of 1 M bits per flip): player *i* sees the same coins in
  every level; only the rule changes.
- **Definitions** (after Thorp 2006, who redefines ruin as wealth below any small ε because it never hits 0):
  **ahead** = wealth > $100; **ruined** = wealth ≤ $1 (lost ≥ 99 %); **typical player** = median wealth;
  **crowd average** = mean wealth of all players.
- **Tool validation (seed 1, labelled NOT RESULTS, must pass before any official run).** Pass = every check within
  4 standard errors of the exact answer:
  - V1 coin fair: heads share of all 10⁹ bits = 0.5.
  - V2 share ahead and V3 share ruined at 10, 100, 365, 1,000 flips = exact binomial.
  - V4 median heads count within 1 of the exact binomial median at the same horizons.
  - V5 crowd average at flips 1-10 = $100 × 1.05ⁿ (SE from E[X²] = 1.305ⁿ). Only flips 1-10 are printed, so the
    validation does not preview the L1 turn point.
  - V6 bet fraction f = 0.5 / 0.25 / 0.1: mean log growth per flip at 1,000 flips = g(f) = ½ ln(1+0.5f) + ½ ln(1−0.4f).
  - V7 pools K = 2, 10: mean log growth per flip = exact Σ_j C(K,j) 2⁻ᴷ ln((1.5j + 0.6(K−j))/K).
  - V8 code check: pool size 1 gives exactly the lone-player wealth (same coins), to 1e-9 in log.
- **Levels (official seed 108; seed 109 re-run reported alongside; dev/validation seeds 1-99 never shown as
  results):**
  - **L1 The crowd:** 1,000,000 players, all-in every flip, 1,000 flips. Measures at 10 / 100 / 365 / 1,000:
    share ahead, share ruined, median; crowd-average path; the flip where the crowd average peaks; share of all
    money held by the single richest player at 1,000.
  - **L2 Bet less:** same players and coins, bet fraction f = 1, 0.5, 0.25, 0.1. Measures: median and share ahead
    at 1,000. "Best" = highest median at 1,000 (pre-stated, so share-ahead can't be cherry-picked; f = 0.1 is
    expected to have the most players ahead but a lower median, and the video says so).
  - **L3 Share:** same players and coins, all-in, money pooled and split equally after every flip, groups of
    K = 2, 10, 100 (K = 1 = L1). Measures: median per-member wealth and share ahead at 1,000.
- **My predictions (the bet slip, shown on screen):**
  1. L1 at 1,000 flips: ≥ 99.9 % ruined, ≤ 0.05 % ahead (exact: 99.96 % / 0.01 %).
  2. L1 crowd average follows $100 × 1.05ⁿ at first, peaks somewhere between flip 100 and 250, then falls (my
     estimate ~146; RESEARCH.md §1). Outside 100-250 → I say I was wrong.
  3. L2: f = 0.25 has the highest median (theory ×498); f = 0.5 ends near $100 (theory ×1, zero growth).
  4. L3: pairs still lose (theory ×0.14); groups of 10 and 100 grow (theory ×10¹⁷ and ×10²⁰).
- **What counts as a result:** the seed-108 number. If seed 109 changes a headline wording (e.g. which f is
  best, whether the turn point is inside 100-250), both are shown and the wording follows the weaker one.
- **Stop rules:** none needed (whole study ≈ minutes of CPU). Every run is kept in `runs/`, failed ones included.
- **Not tuned:** payoffs, p = 0.5, $100 start, N = 1 M, 1,000 flips, the definitions above, the f and K lists, seeds.
- **Wording rules for screen:** "in this game", "in my simulation". Never "economists were wrong for 300 years",
  never investment advice, never "the stock market is this coin". The deeper turn (cooperation, insurance) is "one
  proposed explanation" (Peters & Adamou), with the critics (Doctor, Wakker & Wang 2020) named once.
- **Title rule:** if prediction 1 holds → "This Bet Makes Money on Average. It Ruined [N] of 1 Million People."
  (N from `numbers.json`). Your "It Will Ruin Almost Everyone." stays a candidate; the horizon (1,000 flips) is said
  in the first 30 s either way.

