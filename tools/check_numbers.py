"""Independent re-check of every headline number (P7 provenance).

Re-streams the official coins from scratch (same seed = the same frozen run, not a new run), recounts heads per
player without using the saved tables, and reconciles the result with summary.json, counts.npz and numbers.json.
Also answers: how concentrated is the money (top 1 / top 10 / the players ahead), and what is the average without
the richest player. Writes runs/official/seed<seed>/recheck.json (+ the richest player's own flip history).

    python tools/check_numbers.py --seed 108
"""
import argparse, json, math, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sim"))
from coin import coin_stream  # noqa: E402

N, T, START = 1_000_000, 1000, 100.0
LU, LD = math.log(1.5), math.log(0.6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    a = ap.parse_args()
    run = ROOT / "runs" / "official" / f"seed{a.seed}"
    summary = json.loads((run / "summary.json").read_text())

    k = np.zeros(N, dtype=np.int32)
    for heads in coin_stream(a.seed, N, T):
        k += heads
    lw = math.log(START) + k * LU + (T - k) * LD  # log wealth of every player at flip 1,000
    w = np.exp(lw)  # smallest is ~1e-220, still a normal float64
    total = float(w.sum())
    order = np.argsort(w)[::-1]
    top = int(order[0])

    ok = []

    def same(name, x, y, rel=1e-9):
        good = abs(x - y) <= rel * max(abs(x), abs(y), 1e-300)
        ok.append(good)
        print(f"{'OK ' if good else 'BAD'} {name:44s} recount {x:.10g}  saved {y:.10g}")

    counts = np.load(run / "counts.npz")["counts"][T]
    same("k table identical", float(np.abs(np.bincount(k, minlength=T + 1) - counts).sum()), 0.0)
    s = summary["L1"][str(T)]
    same("ruined (<= $1) count", float((w <= 1.0).sum()), float(s["players_ruined"]))
    same("ahead (> $100) count", float((w > START).sum()), float(s["players_ahead"]))
    same("crowd average", total / N, s["crowd_average"], 1e-6)
    same("richest share of all money", float(w[top] / total), s["richest_share"], 1e-6)
    same("median (lower)", float(np.sort(w)[(N - 1) // 2]), s["median"], 1e-6)

    ahead = w > START
    rec = dict(
        seed=a.seed, label="recheck of the official run (re-streamed coins, not a new run)",
        all_match=all(ok),
        richest_player_index=top, richest_heads=int(k[top]), richest_dollars=float(w[top]),
        total_money=total, crowd_average=total / N,
        share_top1=float(w[order[0]] / total), share_top10=float(w[order[:10]].sum() / total),
        share_players_ahead=float(w[ahead].sum() / total), players_ahead=int(ahead.sum()),
        average_without_richest=float((total - w[top]) / (N - 1)),
        average_without_players_ahead=float(w[~ahead].sum() / (~ahead).sum()),
        money_of_all_ruined=float(w[w <= 1.0].sum()),
    )
    # the richest player's own coin history, for the visuals (same stream, read again)
    hist = np.fromiter((h[top] for h in coin_stream(a.seed, N, T)), dtype=bool, count=T)
    assert int(hist.sum()) == rec["richest_heads"]
    np.save(run / "richest_history.npy", hist)
    (run / "recheck.json").write_text(json.dumps(rec, indent=1))
    for key, v in rec.items():
        print(f"    {key:32s} {v}")
    print("ALL MATCH" if all(ok) else "MISMATCH")
    sys.exit(0 if all(ok) else 1)


if __name__ == "__main__":
    main()
