"""P7 official runs, exactly as frozen in PRODUCTION_LOG.md (2026-10-11).

    python tools/run_official.py --seed 108     (official)
    python tools/run_official.py --seed 109     (re-run, reported alongside)

L1 the crowd: 1,000,000 players, all-in, 1,000 flips.
L2 bet less: same players and coins, f = 1, 0.5, 0.25, 0.1 (wealth depends only on the heads count k, so L1 and L2
   come from the same full table counts[n, k] = how many players have k heads after n flips).
L3 share: same players and coins, all-in, pooled and split equally after every flip, groups of K = 2, 10, 100.

Definitions (frozen): ahead = wealth > $100; ruined = wealth <= $1; typical player = median wealth (lower median:
the smallest value with at least half the players at or below it); crowd average = mean wealth of all players.

Output: runs/official/seed<seed>/ summary.json (headline numbers), per_flip.npz (every statistic per flip),
counts.npz (the full k table), paths.npz (coin history of the first 10,000 players, for the visuals), run.log.
"""
import argparse, json, math, sys, time
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim"))
from coin import START, log_factors, lone_players, pooled_players  # noqa: E402

N, T = 1_000_000, 1000
FRACTIONS = (1.0, 0.5, 0.25, 0.1)
POOLS = (2, 10, 100)
HORIZONS = (10, 100, 365, 1000)
AHEAD, RUIN = START, 1.0
KEEP_PATHS = 10_000
KEEP_GROUPS = 1_000


def k_stats(counts_n, n, f=1.0):
    """Statistics of all players after n flips, from the count of players per heads count k (k = 0..n)."""
    k = np.arange(n + 1)
    lu, ld = log_factors(f)
    lw = math.log(START) + k * lu + (n - k) * ld
    c = counts_n[: n + 1]
    cum = np.cumsum(c)
    k_med = int(np.searchsorted(cum, N / 2))  # lower median
    nz = c > 0
    log_mean = logsumexp(lw[nz] + np.log(c[nz])) - math.log(N)
    k_max = int(k[nz].max())
    log_total = log_mean + math.log(N)
    return dict(
        median=float(math.exp(lw[k_med])),
        log_median=float(lw[k_med]),
        ahead=float(c[lw > math.log(AHEAD)].sum() / N),
        ruined=float(c[lw <= math.log(RUIN)].sum() / N),
        log_mean=float(log_mean),
        richest_share=float(math.exp(lw[k_max] - log_total)),  # one richest player's share of all money
        richest_count=int(c[k_max]),  # players tied at the top
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--dev", action="store_true", help="test the runner on a dev seed (1-99) -> runs/dev/, NOT RESULTS")
    a = ap.parse_args()
    if a.dev:
        assert 1 <= a.seed <= 99, "dev seeds are 1-99"
        out = ROOT / "runs" / "dev" / f"seed{a.seed}"
    else:
        assert a.seed in (108, 109), "official seeds are 108 (official) and 109 (re-run)"
        out = ROOT / "runs" / "official" / f"seed{a.seed}"
    out.mkdir(parents=True, exist_ok=True)
    log = open(out / "run.log", "w", encoding="utf-8")

    def say(msg):
        print(msg)
        log.write(msg + "\n")
        log.flush()

    say(f"{'DEV TEST, NOT RESULTS' if a.dev else 'OFFICIAL'} run seed {a.seed}, N {N}, T {T}, started {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # ---- L1 + L2: lone players, full k table ----
    t0 = time.time()
    counts = np.zeros((T + 1, T + 1), dtype=np.int32)
    counts[0, 0] = N

    def on_flip(n, k):
        counts[n] = np.bincount(k, minlength=T + 1)

    _, paths = lone_players(a.seed, N, T, on_flip, keep_paths=KEEP_PATHS)
    say(f"L1/L2 lone players done in {time.time() - t0:.1f}s")

    per_flip = {}
    for f in FRACTIONS:
        rows = [k_stats(counts[n], n, f) for n in range(T + 1)]
        tag = f"f{f:g}"
        for key in ("log_median", "ahead", "ruined", "log_mean", "richest_share"):
            per_flip[f"{tag}_{key}"] = np.array([r[key] for r in rows])
    l1_mean = per_flip["f1_log_mean"]
    peak = int(np.argmax(l1_mean))

    summary = dict(label="DEV TEST - NOT RESULTS" if a.dev else "OFFICIAL", seed=a.seed, players=N, flips=T, definitions=dict(ahead="> $100", ruined="<= $1",
                   median="lower median", start=START), L1={}, L2={}, L3={})
    for n in HORIZONS:
        s = k_stats(counts[n], n, 1.0)
        summary["L1"][str(n)] = dict(s, players_ahead=int(round(s["ahead"] * N)),
                                     players_ruined=int(round(s["ruined"] * N)),
                                     crowd_average=float(math.exp(s["log_mean"])))
    summary["L1"]["crowd_average_peak_flip"] = peak
    summary["L1"]["crowd_average_peak"] = float(math.exp(l1_mean[peak]))
    summary["L1"]["crowd_average_vs_expected_at_peak"] = float(math.exp(l1_mean[peak]) / (START * 1.05 ** peak))
    for f in FRACTIONS:
        s = k_stats(counts[T], T, f)
        summary["L2"][f"{f:g}"] = dict(median=s["median"], ahead=s["ahead"], ruined=s["ruined"],
                                       players_ahead=int(round(s["ahead"] * N)))
    summary["L2"]["best_f_by_median"] = max(FRACTIONS, key=lambda f: summary["L2"][f"{f:g}"]["median"])
    say(f"L1 peak of crowd average at flip {peak}; L2 best f by median {summary['L2']['best_f_by_median']}")

    # ---- L3: pools ----
    groups_kept = {}
    for K in POOLS:
        t0 = time.time()
        med, ahead, ruined, lmean = (np.zeros(T + 1) for _ in range(4))
        med[0], ahead[0], ruined[0], lmean[0] = math.log(START), 0.0, 0.0, math.log(START)
        keep = np.zeros((T + 1, min(KEEP_GROUPS, N // K)))
        keep[0] = math.log(START)

        def on_pool(n, lw):
            m = (lw.size - 1) // 2
            med[n] = np.partition(lw, m)[m]  # lower median
            ahead[n] = (lw > math.log(AHEAD)).mean()
            ruined[n] = (lw <= math.log(RUIN)).mean()
            lmean[n] = logsumexp(lw) - math.log(lw.size)
            keep[n] = lw[: keep.shape[1]]

        pooled_players(a.seed, N, T, K, on_pool)
        tag = f"pool{K}"
        per_flip[f"{tag}_log_median"], per_flip[f"{tag}_ahead"] = med, ahead
        per_flip[f"{tag}_ruined"], per_flip[f"{tag}_log_mean"] = ruined, lmean
        groups_kept[tag] = keep
        summary["L3"][str(K)] = dict(median=float(math.exp(med[T])), ahead=float(ahead[T]),
                                     ruined=float(ruined[T]), groups=N // K)
        say(f"L3 pool K={K} done in {time.time() - t0:.1f}s: median ${math.exp(med[T]):.4g}, ahead {ahead[T]:.4f}")

    np.savez_compressed(out / "per_flip.npz", **per_flip)
    np.savez_compressed(out / "counts.npz", counts=counts)
    np.savez_compressed(out / "paths.npz", heads=paths, **{f"{k}_log_wealth": v for k, v in groups_kept.items()})
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    say(f"saved to {out}, finished {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
