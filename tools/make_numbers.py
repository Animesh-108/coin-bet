"""numbers.json: every number the video may show, traced to the official run files.

Headline = seed 108 (official). Seed 109 = re-run; where a headline wording depends on it, the weaker of the two
is used (pre-registration). Predictions are scored here, by the frozen rules, not by hand.

    python tools/make_numbers.py
"""
import json, math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs" / "official"


def load(seed):
    return json.loads((RUNS / f"seed{seed}" / "summary.json").read_text())


def main():
    a, b = load(108), load(109)
    src = "runs/official/seed108/summary.json"
    L1, L2, L3 = a["L1"], a["L2"], a["L3"]
    T = str(a["flips"])

    peaks = [a["L1"]["crowd_average_peak_flip"], b["L1"]["crowd_average_peak_flip"]]
    ruined = [a["L1"][T]["ruined"], b["L1"][T]["ruined"]]
    ahead = [a["L1"][T]["ahead"], b["L1"][T]["ahead"]]
    rich = [a["L1"][T]["richest_share"], b["L1"][T]["richest_share"]]

    predictions = {
        "1_ruined_at_1000_ge_99.9pct_and_ahead_le_0.05pct": all(r >= 0.999 for r in ruined) and all(x <= 0.0005 for x in ahead),
        "2_crowd_average_peak_in_100_250": all(100 <= p <= 250 for p in peaks),
        "3_quarter_best_by_median_and_half_ends_near_100": all(
            s["L2"]["best_f_by_median"] == 0.25 and abs(s["L2"]["0.5"]["median"] - 100) < 1 for s in (a, b)),
        "4_pairs_lose_groups_of_10_and_100_grow": all(
            s["L3"]["2"]["median"] < 100 and s["L3"]["10"]["median"] > 100 and s["L3"]["100"]["median"] > 100
            for s in (a, b)),
    }

    # the single richest player at 1,000 flips (from the full k table)
    c = np.load(RUNS / "seed108" / "counts.npz")["counts"][a["flips"]]
    k_top = int(np.nonzero(c)[0].max())
    top_wealth = 100 * 1.5 ** k_top * 0.6 ** (a["flips"] - k_top)

    # concentration of the money, from the independent recheck (tools/check_numbers.py)
    ra, rb = (json.loads((RUNS / f"seed{x}" / "recheck.json").read_text()) for x in (108, 109))
    assert ra["all_match"] and rb["all_match"], "run tools/check_numbers.py first; it must match"

    val = json.loads((ROOT / "runs" / "validation" / "validate_seed1_N1000000_T1000.json").read_text())
    med1000 = L1[T]["median"]
    zeros = -math.floor(math.log10(med1000)) - 1          # zeros after the decimal point before the first digit

    numbers = dict(
        _source=src, _rerun="runs/official/seed109/summary.json",
        _rule="headline = seed 108; wording follows the weaker seed where they differ",
        players=a["players"], flips=a["flips"], start_dollars=100,
        # L1 the crowd
        l1_ahead_10=L1["10"]["players_ahead"], l1_ahead_100=L1["100"]["players_ahead"],
        l1_ahead_365=L1["365"]["players_ahead"], l1_ahead_1000=L1[T]["players_ahead"],
        l1_ruined_100=L1["100"]["players_ruined"], l1_ruined_365=L1["365"]["players_ruined"],
        l1_ruined_1000=L1[T]["players_ruined"],
        l1_ruined_1000_pct=round(100 * L1[T]["ruined"], 2), l1_ruined_365_pct=round(100 * L1["365"]["ruined"], 1),
        l1_median_1000=med1000, l1_median_1000_zeros=zeros,
        validation_checks_passed=int(sum(bool(c["ok"]) for c in val["checks"])), validation_checks_total=len(val["checks"]),
        prereg_peak_lo=100, prereg_peak_hi=250,  # frozen prediction 2 (PRODUCTION_LOG pre-registration), not run data
        l1_median_10=round(L1["10"]["median"], 2), l1_median_100=round(L1["100"]["median"], 2),
        l1_crowd_average_100=round(L1["100"]["crowd_average"]), l1_crowd_average_1000=round(L1[T]["crowd_average"]),
        l1_expected_average_100=round(100 * 1.05 ** 100),
        l1_peak_flip=peaks[0], l1_peak_flip_rerun=peaks[1],
        l1_richest_share_1000_pct=round(100 * rich[0]), l1_richest_share_1000_pct_rerun=round(100 * rich[1]),
        l1_richest_heads=k_top, l1_richest_tails=a["flips"] - k_top, l1_richest_dollars=round(top_wealth),
        l1_total_money_1000=round(L1[T]["crowd_average"] * a["players"]),
        l1_top10_share_pct=round(100 * ra["share_top10"], 1), l1_top10_share_pct_rerun=round(100 * rb["share_top10"], 3),
        l1_top10_share_wording="99 %" if min(ra["share_top10"], rb["share_top10"]) >= 0.99 else "most",
        l1_average_without_richest=round(ra["average_without_richest"]),
        l1_money_of_all_ruined=round(ra["money_of_all_ruined"]), l1_money_of_all_ruined_rerun=round(rb["money_of_all_ruined"]),
        l1_crowd_average_1000_rerun=round(b["L1"][T]["crowd_average"]),
        l1_richest_share_wording="more than half" if min(rich) > 0.5 else "a large share",
        # L2 bet less
        l2_median_all_in=L2["1"]["median"], l2_median_half=round(L2["0.5"]["median"], 2),
        l2_median_quarter=round(L2["0.25"]["median"]), l2_median_tenth=round(L2["0.1"]["median"]),
        l2_ahead_quarter_pct=round(100 * L2["0.25"]["ahead"], 1), l2_ahead_tenth_pct=round(100 * L2["0.1"]["ahead"], 1),
        l2_ahead_half_pct=round(100 * L2["0.5"]["ahead"], 1), l2_ruined_half_pct=round(100 * L2["0.5"]["ruined"], 1),
        l2_best_fraction_by_median=L2["best_f_by_median"],
        # L3 share
        l3_median_pairs=round(L3["2"]["median"], 2), l3_ahead_pairs_pct=round(100 * L3["2"]["ahead"], 1),
        l3_median_10=L3["10"]["median"], l3_median_100=L3["100"]["median"],
        l3_ahead_10_pct=round(100 * L3["10"]["ahead"], 1),
        predictions=predictions,
    )
    (ROOT / "numbers.json").write_text(json.dumps(numbers, indent=1))
    for k, v in numbers.items():
        print(f"{k:38s} {v}")


if __name__ == "__main__":
    main()
