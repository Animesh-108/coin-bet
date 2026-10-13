"""P4 tool check: the simulation must match the exact answers before any official run.

Checks V1-V8 as pre-registered in PRODUCTION_LOG.md. Validation seeds only (never 108 / 109). NOT RESULTS.
Only flips 1-10 of the crowd average are computed, so this does not preview the L1 turn point.

    python tools/validate.py --seed 1 [--players 1000000] [--flips 1000]
"""
import argparse, json, math, sys, time
from pathlib import Path

import numpy as np
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))
from coin import START, crowd_mean, log_factors, log_wealth, lone_players, pooled_players  # noqa: E402

TOL = 4.0  # standard errors
RUIN = 1.0  # dollars


def k_threshold_above(n, level, f=1.0):
    """Smallest heads count k with wealth > level."""
    lu, ld = log_factors(f)
    return math.floor((math.log(level / START) - n * ld) / (lu - ld) + 1e-12) + 1


def g_bet(f):
    lu, ld = log_factors(f)
    return 0.5 * lu + 0.5 * ld


def g_pool(K):
    return sum(binom.pmf(j, K, 0.5) * math.log((1.5 * j + 0.6 * (K - j)) / K) for j in range(K + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--players", type=int, default=1_000_000)
    ap.add_argument("--flips", type=int, default=1000)
    a = ap.parse_args()
    assert a.seed not in (108, 109), "official seeds are not for validation"
    N, T = a.players, a.flips
    horizons = [h for h in (10, 100, 365, 1000) if h <= T]
    checks = []

    def check(name, sim, exact, se):
        z = (sim - exact) / se if se > 0 else (0.0 if sim == exact else math.inf)
        ok = abs(z) <= TOL
        checks.append(dict(check=name, sim=sim, exact=exact, se=se, z=round(z, 2), ok=ok))
        print(f"{'PASS' if ok else 'FAIL'}  {name:42s} sim {sim:.6g}  exact {exact:.6g}  z {z:+.2f}")

    early_mean, snap = {}, {}

    def on_flip(n, k):
        if n <= 10:
            early_mean[n] = crowd_mean(log_wealth(k, n))
        if n in horizons:
            snap[n] = k.copy()

    t0 = time.time()
    k, _ = lone_players(a.seed, N, T, on_flip)
    t_lone = time.time() - t0

    # V1 coin fair (all N*T bits)
    p_heads = k.sum(dtype=np.int64) / (N * T)
    check("V1 heads share", p_heads, 0.5, math.sqrt(0.25 / (N * T)))

    for n in horizons:
        kn = snap[n]
        # V2 ahead: wealth > START
        ka = k_threshold_above(n, START)
        p = binom.sf(ka - 1, n, 0.5)
        check(f"V2 share ahead @{n}", float((kn >= ka).mean()), p, math.sqrt(max(p * (1 - p), 1e-12) / N))
        # V3 ruined: wealth <= RUIN
        kr = k_threshold_above(n, RUIN)
        p = binom.cdf(kr - 1, n, 0.5)
        check(f"V3 share ruined @{n}", float((kn < kr).mean()), p, math.sqrt(max(p * (1 - p), 1e-12) / N))
        # V4 median heads count within 1
        med, exact_med = float(np.median(kn)), float(binom.median(n, 0.5))
        ok = abs(med - exact_med) <= 1
        checks.append(dict(check=f"V4 median k @{n}", sim=med, exact=exact_med, ok=ok))
        print(f"{'PASS' if ok else 'FAIL'}  V4 median k @{n:<35d} sim {med}  exact {exact_med}")

    # V5 crowd average, flips 1-10
    for n in range(1, min(10, T) + 1):
        exact = START * 1.05 ** n
        se = START * math.sqrt(1.305 ** n - 1.1025 ** n) / math.sqrt(N)
        check(f"V5 crowd average @{n}", early_mean[n], exact, se)

    # V6 bet fractions: mean log growth per flip at T
    for f in (0.5, 0.25, 0.1):
        lu, ld = log_factors(f)
        g_sim = float(((log_wealth(k, T, f) - math.log(START)) / T).mean())
        check(f"V6 growth/flip f={f}", g_sim, g_bet(f), (lu - ld) / 2 / math.sqrt(T * N))

    # V7 pools + V8 pool of 1 == lone players
    t0 = time.time()
    lw1 = pooled_players(a.seed, N, T, 1)
    gap = float(np.abs(lw1 - log_wealth(k, T)).max())
    ok = gap < 1e-9
    checks.append(dict(check="V8 pool K=1 == lone", sim=gap, exact=0.0, ok=ok))
    print(f"{'PASS' if ok else 'FAIL'}  V8 pool K=1 == lone, max log gap {gap:.2e}")
    for K in (2, 10):
        lw = pooled_players(a.seed, N, T, K)
        gs = (lw - math.log(START)) / T
        check(f"V7 growth/flip pool K={K}", float(gs.mean()), g_pool(K), float(gs.std(ddof=1)) / math.sqrt(gs.size))
    t_pool = time.time() - t0

    passed = all(c["ok"] for c in checks)
    out = Path(__file__).resolve().parents[1] / "runs" / "validation"
    out.mkdir(parents=True, exist_ok=True)
    rec = dict(label="TOOL VALIDATION - NOT RESULTS", seed=a.seed, players=N, flips=T, tol_se=TOL,
               passed=passed, seconds=dict(lone=round(t_lone, 1), pools=round(t_pool, 1)), checks=checks)
    path = out / f"validate_seed{a.seed}_N{N}_T{T}.json"
    path.write_text(json.dumps(rec, indent=1, default=float))
    print(f"\n{'ALL PASS' if passed else 'FAILED'}  ({sum(c['ok'] for c in checks)}/{len(checks)})  "
          f"lone {t_lone:.1f}s  pools {t_pool:.1f}s  -> {path}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
