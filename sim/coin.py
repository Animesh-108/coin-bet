"""The +50 % / -40 % coin game for a crowd of players.

Every player starts with START dollars. Each flip, a fair coin: heads multiplies the part of the wealth that is bet
by 1.5, tails by 0.6. Betting a fraction f of current wealth gives a factor of (1 + 0.5 f) or (1 - 0.4 f).

All coins come from one stream (PCG64, one byte-packed row of N bits per flip), so player i sees the same coin
sequence in every level: only the rule changes, never the luck.

Wealth is kept as log wealth (float64); 0.6**1000 is ~1e-222, close to the float limit.
"""
import numpy as np

UP, DOWN = 1.5, 0.6
START = 100.0


def coin_stream(seed, n_players, n_flips):
    """Yield one boolean row (True = heads) per flip."""
    rng = np.random.Generator(np.random.PCG64(seed))
    n_bytes = (n_players + 7) // 8
    for _ in range(n_flips):
        bits = np.unpackbits(np.frombuffer(rng.bytes(n_bytes), dtype=np.uint8))[:n_players]
        yield bits.astype(bool)


def log_factors(f):
    return np.log1p((UP - 1) * f), np.log1p((DOWN - 1) * f)


def lone_players(seed, n_players, n_flips, on_flip=None, keep_paths=0):
    """Players who never share. Wealth depends only on the heads count k, so track k (int16).

    on_flip(n, k) is called after every flip with the heads counts of all players.
    keep_paths > 0 also returns the full heads/tails history of the first keep_paths players (for the visuals).
    """
    k = np.zeros(n_players, dtype=np.int16)
    paths = np.zeros((n_flips, keep_paths), dtype=bool) if keep_paths else None
    for n, heads in enumerate(coin_stream(seed, n_players, n_flips), start=1):
        k += heads
        if keep_paths:
            paths[n - 1] = heads[:keep_paths]
        if on_flip:
            on_flip(n, k)
    return k, paths


def log_wealth(k, n, f=1.0):
    lu, ld = log_factors(f)
    return np.log(START) + k * lu + (n - k) * ld


def pooled_players(seed, n_players, n_flips, group, on_flip=None, f=1.0):
    """Players in groups of `group`: each bets fraction f on their own coin, then the group's money is split
    equally after every flip (Peters & Adamou). Returns log wealth per group member (one value per group)."""
    assert n_players % group == 0
    lu, ld = log_factors(f)
    up, down = np.exp(lu), np.exp(ld)
    lw = np.full(n_players // group, np.log(START))
    for n, heads in enumerate(coin_stream(seed, n_players, n_flips), start=1):
        factor = np.where(heads, up, down).reshape(-1, group).mean(axis=1)
        lw += np.log(factor)
        if on_flip:
            on_flip(n, lw)
    return lw


def crowd_mean(log_w):
    """Average wealth of the crowd, computed in log space (log-sum-exp)."""
    m = log_w.max()
    return float(np.exp(m) * np.exp(log_w - m).mean())
