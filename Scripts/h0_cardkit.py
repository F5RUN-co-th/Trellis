#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_cardkit.py — TRELLIS-010 Stage H0: shared test machinery ของ hypothesis cards
(Engineer card#2 ISSUE-4: refactor ต้องมี hard-assert regression เทียบเลข published
ของ card #1 — kit เชื่อถือได้ต่อเมื่อ reproduce ของเดิมเป๊ะ · `h0_card1_rv.py` คงเดิม
เป็น immutable record ของ test ที่เผา budget ไปแล้ว — ไม่ refactor ย้อนหลัง)

หน้าที่: load+integrity chain · T statistic · rotation null (ทุก distinct rotation,
deterministic) · bootstrap CI (seed=11) · per-year table · P3 gate ครบ §0
ตัวเลขทุกตัวเป็นของ script — LLM ห้ามพิมพ์เอง
"""
import csv
import hashlib
from pathlib import Path

import numpy as np

DIR = Path(__file__).parent.parent / "Research" / "h0"
FACTS = DIR / "h0_day_facts_2012_2020.csv"
FEAT = DIR / "h0_features_2012_2020.csv"
SHA = DIR / "h0_features_2012_2020.sha256"

LO, HI = 33.3, 66.7                     # fixed ex-ante bands (card #1 convention)
LOSERS = ["2012", "2014", "2017", "2018", "2019"]
WINNERS = ["2013", "2015", "2016", "2020"]
# §0 thresholds บนหน้าต่าง search (CRIT-2 baseline — จาก h0_join_pnl reconciliation)
G_LOSER_BASE, G_LOSER_REQ = -135.3, -67.6
G_WIN_BASE, G_WIN_REQ = 668.0, 534.4
G_POOL_BASE, G_POOL_REQ = 532.8, 692.6
G_WORST_REQ = -150.0


def fv(r, k):
    return float(r[k]) if r[k] not in ("", None) else np.nan


def load_facts():
    """โหลด day_facts + ตรวจ integrity chain (firewall SHA256 + reconciliation)"""
    sha_now = hashlib.sha256(FEAT.read_bytes()).hexdigest()
    assert sha_now == SHA.read_text(encoding="utf-8").split()[0], "features firewall broken"
    with open(FACTS, encoding="utf-8") as f:
        hdr = f.readline()
        assert sha_now in hdr, "day_facts ไม่ได้มาจาก features ฉบับ frozen"
        rows = list(csv.DictReader(f))
    traded = [r for r in rows if r["traded"] == "1"]
    tot = sum(fv(r, "pnl") for r in traded)
    assert abs(tot - 532.8) < 0.1, f"reconciliation broken: {tot}"
    return rows, traded


def year_demean(pnl, yr):
    ym = {y: pnl[yr == y].mean() for y in np.unique(yr)}
    return pnl - np.array([ym[y] for y in yr])


def rotation_pvalues(vals, stat_fn):
    """ทุก distinct circular rotation (deterministic ไม่ใช้ seed) · one-tailed
    p_i = fraction(stat_rot_i >= stat_obs_i) · stat_fn คืน np.array ของสถิติ
    (คืน np.nan ทั้งชุดถ้า rotation invalid เช่นกลุ่มว่าง — ถูกข้าม)"""
    obs = np.asarray(stat_fn(vals), dtype=float)
    n = len(vals)
    nulls = []
    for k in range(1, n):
        s = np.asarray(stat_fn(np.r_[vals[k:], vals[:k]]), dtype=float)
        if np.all(np.isfinite(s)):
            nulls.append(s)
    nulls = np.array(nulls)
    p = (nulls >= obs).mean(axis=0)
    return obs, p, len(nulls)


def bootstrap_ci(vals, aux_arrays, stat_fn, n_boot=10000, seed=11):
    """resample วัน (index) พร้อมกันทุก array · คืน CI95 ต่อสถิติ"""
    n = len(vals)
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        s = np.asarray(stat_fn(vals[i], *[a[i] for a in aux_arrays]), dtype=float)
        if np.all(np.isfinite(s)):
            out.append(s)
    return np.percentile(np.array(out), [2.5, 97.5], axis=0)


def gate_report(traded, skip_fn, label):
    """P3 gate ครบทุกมิติ §0 [M6] · skip_fn(row)->bool (fail-open ต้องอยู่ใน fn)"""
    base_y, gate_y = {}, {}
    for r in traded:
        y, p = r["date"][:4], fv(r, "pnl")
        base_y[y] = base_y.get(y, 0) + p
        gate_y.setdefault(y, 0)
        if not skip_fn(r):
            gate_y[y] += p
    print(f"  year   base     gated    Δ        [{label}]")
    for y in sorted(base_y):
        tag = "L" if y in LOSERS else "W"
        print(f"  {y}{tag} {base_y[y]:+8.1f} {gate_y[y]:+8.1f} {gate_y[y]-base_y[y]:+7.1f}")
    gl = sum(gate_y[y] for y in LOSERS)
    gw = sum(gate_y[y] for y in WINNERS)
    gp = sum(gate_y.values())
    worst = min(gate_y.values())
    ok = {"a": gl > G_LOSER_REQ, "b": gw >= G_WIN_REQ, "c": gp >= G_POOL_REQ,
          "d": worst >= G_WORST_REQ}
    print(f"  (a) losers  {G_LOSER_BASE:+.1f} → {gl:+.1f} (> {G_LOSER_REQ}): "
          f"{'PASS' if ok['a'] else 'FAIL'}")
    print(f"  (b) winners {G_WIN_BASE:+.1f} → {gw:+.1f} (≥ {G_WIN_REQ}): "
          f"{'PASS' if ok['b'] else 'FAIL'}")
    print(f"  (c) pooled  {G_POOL_BASE:+.1f} → {gp:+.1f} (≥ {G_POOL_REQ}): "
          f"{'PASS' if ok['c'] else 'FAIL'}")
    print(f"  (d) worst-year gated = {worst:+.1f} (≥ {G_WORST_REQ}): "
          f"{'PASS' if ok['d'] else 'FAIL'}")
    p3 = all(ok.values())
    print(f"  P3 = {'PASS' if p3 else 'FAIL'}")
    return p3


# ═══ ISSUE-4: hard regression — kit ต้อง reproduce เลข published ของ card #1 เป๊ะ ═══
CARD1_PUBLISHED = dict(T_raw=0.752, p_raw=0.0934, T_within=0.391, p_within=0.2246,
                       sum_b1=285.7, sum_b2=-255.4, sum_b3=501.0)


def regression_card1(rows):
    """สร้าง pipeline card #1 ด้วย primitives ของ kit — เลขต้องตรง published ทุกตัว
    ไม่ตรง = kit เชื่อไม่ได้ abort (fail loud)"""
    ok_tr = [r for r in rows if r["traded"] == "1" and r["status"] == "ok"]
    prim = [r for r in ok_tr if r["prev_ok"] == "1" and np.isfinite(fv(r, "rv_pct250"))]
    prim.sort(key=lambda r: r["date"])
    rv = np.array([fv(r, "rv_pct250") for r in prim])
    pnl = np.array([fv(r, "pnl") for r in prim])
    yr = np.array([r["date"][:4] for r in prim])
    resid = year_demean(pnl, yr)

    def stat(vals):
        hi, lo = vals >= HI, vals < LO
        if not (hi.any() and lo.any()):
            return np.array([np.nan, np.nan])
        return np.array([pnl[hi].mean() - pnl[lo].mean(),
                         resid[hi].mean() - resid[lo].mean()])

    obs, p, nrot = rotation_pvalues(rv, stat)
    hi, lo, mid = rv >= HI, rv < LO, (rv >= LO) & (rv < HI)
    got = dict(T_raw=obs[0], p_raw=p[0], T_within=obs[1], p_within=p[1],
               sum_b1=pnl[lo].sum(), sum_b2=pnl[mid].sum(), sum_b3=pnl[hi].sum())
    for k, exp in CARD1_PUBLISHED.items():
        tol = 0.002 if k.startswith("p_") else (0.15 if k.startswith("sum") else 0.005)
        assert abs(got[k] - exp) <= tol, f"kit regression FAIL: {k} got {got[k]} exp {exp}"
    print(f"kit regression vs card #1 published: PASS ทุกตัว "
          f"(T_raw {got['T_raw']:+.3f} p {got['p_raw']:.4f} · "
          f"T_within {got['T_within']:+.3f} p {got['p_within']:.4f} · rotations={nrot})")


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rows, _ = load_facts()
    regression_card1(rows)
