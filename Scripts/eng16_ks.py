# -*- coding: utf-8 -*-
"""KS+ eligibility instrument ตาม card AD-4 §0 N2 — authority เดียวของ t / achieved false-flag / OC (script-owned)
v2 (รอบ 21 R1/R2 · E1/E2): (A) threshold lattice-min · **integer-lattice convention** (ไม่มี float dust — atom P(KS+ = t) ≈ 1.3%)
                            (B) OC pre-registered บน generator ที่ card pin: location-shift δ ∈ {.05,.10,.18,.25,.40} (null S1 ~ N(0,1) · obs ~ N(δ,1) · B0=99)
                                + tail-inflation P(p≤.05) ∈ {10%,20%} — MC เดียวกัน emit ตาราง flag-rate
null exact = p ~ discrete-Uniform{.01..1.00} · N=400 · B=200,000 · seed 20260903 · synthetic เท่านั้น · ไม่มี data/P&L
convention (operative · N2): C_k = #{p ≤ k/100} · ks_units = max_k (C_k·100 − k·N) ∈ ℤ · KS+ = ks_units/(100·N) · ineligible ⟺ ks_units > KS_T_UNITS·100
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np

N, B, SEED = 400, 200_000, 20260903
K = np.arange(1, 101)
DELTAS = (0.05, 0.10, 0.18, 0.25, 0.40)
TAILS = (0.10, 0.20)
B0 = 99


def ks_units_from_p_int(p_int):
    """p_int: (n, N) ints 1..100 (p×100) → ks_units (n,) integer · exact บน lattice"""
    C = (p_int[:, :, None] <= K[None, None, :]).sum(1)          # n×100 = #{p ≤ k/100}
    return (C * 100 - K[None, :] * N).max(1)


def null_units(rng, B):
    out = np.empty(B, dtype=np.int64)
    CH = 5_000
    for a in range(0, B, CH):
        b = min(a + CH, B)
        out[a:b] = ks_units_from_p_int(rng.integers(1, 101, size=(b - a, N)))
    return out


def part_a(rng):
    u = null_units(rng, B)
    print(f"[A] null exact discrete-Uniform · N={N} · B={B:,} · seed {SEED} · unit = 1/(100·N)")
    t_units = None
    for c in range(18, 30):
        p_gt = float((u > c * 100).mean())
        atom = float((u == c * 100).mean())
        flag = ""
        if p_gt <= 0.05 and t_units is None:
            t_units = c; flag = "  <== lattice-min (t เล็กสุดที่ P ≤ .05)"
        print(f"  t = {c}/{N} = {c/N:.4f}   P(KS+ > t) = {p_gt:.5f}   atom P(KS+ = t) = {atom:.5f}{flag}")
    achieved = float((u > t_units * 100).mean())
    print(f"KS_T_UNITS = {t_units}   (t = {t_units}/{N} = {t_units/N:.4f})")
    print(f"KS_ACHIEVED = {achieved:.5f}   ({achieved*100:.2f}% · integer convention · atom ที่ t = {float((u == t_units*100).mean())*100:.2f}%)")
    return t_units


def part_b(rng, t_units, B_oc=20_000):
    """OC: world = N p-values จาก permutation test (B0=99 · rank rule) ใต้ alternative ที่ card pin → flag-rate = P(ks_units > t)"""
    print(f"\n[B] OC pre-registered (§0 N2 generator) · B_oc={B_oc:,} worlds/cell · B0={B0} · N={N} · flag = ks_units > {t_units}·100")
    print("  location-shift (null S1 ~ N(0,1) · obs ~ N(δ,1) · p = (1+#{null ≥ obs})/(B0+1)):")
    for d in DELTAS:
        cnt = 0; tot = 0
        for a in range(0, B_oc, 500):
            n = min(500, B_oc - a)
            obs = rng.normal(d, 1.0, size=(n, N, 1))
            nul = rng.normal(0.0, 1.0, size=(n, N, B0))
            p_int = 1 + (nul >= obs).sum(2)                                # (1+#{null≥obs}) ∈ 1..100 = p×100
            cnt += int((ks_units_from_p_int(p_int) > t_units * 100).sum()); tot += n
        print(f"    δ = {d:.2f}: flag-rate = {100*cnt/tot:6.2f}%")
    print("  tail-inflation (p ~ mixture: mass m ที่ p ≤ .05 uniform บน {.01..05} · ที่เหลือ uniform บน {.06..1.00}):")
    for m in TAILS:
        cnt = 0; tot = 0
        for a in range(0, B_oc, 2_000):
            n = min(2_000, B_oc - a)
            low = rng.random(size=(n, N)) < m
            p_int = np.where(low, rng.integers(1, 6, size=(n, N)), rng.integers(6, 101, size=(n, N)))
            cnt += int((ks_units_from_p_int(p_int) > t_units * 100).sum()); tot += n
        print(f"    P(p≤.05) = {int(m*100)}%: flag-rate = {100*cnt/tot:6.2f}%")


def main():
    rng = np.random.default_rng(SEED)
    t_units = part_a(rng)
    part_b(rng, t_units)


if __name__ == "__main__":
    main()
