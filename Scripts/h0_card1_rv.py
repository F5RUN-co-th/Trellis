#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_card1_rv.py — TRELLIS-010 Stage H0 · Hypothesis Card #1 (test budget 1/40)
H1: "ระบบแพ้ในวันที่ vol เมื่อวานต่ำ" — realized-vol regime เดี่ยว (rv_pct250)

ฉบับแก้ตาม Engineer review M1–M7 (PASS-with-changes) + Claude Verify ยืนยันทุกเลข
สนามวัด: SIM SEARCH (uncapped 0.01 + catchup) จาก h0_day_facts_2012_2020.csv (frozen)
— MED-1: ผลดีบนสนามนี้ห้ามเรียก edge จนผ่าน capped + real-tick tester confirm

═══ PRE-REGISTERED SPEC (freeze ก่อนรัน — ห้ามแก้หลังเห็นผล) ═══

BUCKETS [M3]: fixed rv_pct250 VALUE-bands (ไม่ใช่ tercile — กลุ่มไม่เท่ากันโดยรู้ล่วงหน้า:
  traded 610/466/409): B1=[0,33.3) B2=[33.3,66.7) B3=[66.7,100] — ค่าคงที่ ex-ante
  (ไม่ใช้ quantile ทั้งชุดซึ่งเป็น future info) · ห้าม tune — ตัวแปร/ขอบใหม่ = card ใหม่

POPULATION [M5]:
  PRIMARY  = traded ∧ status=ok ∧ prev_ok=1 ∧ rv_pct250 finite (drop-list ประกาศ: 64 วัน
             prev_ok=0 [rv จากวัน short/hole = input ปนเปื้อน] + 2 วัน rv NaN)
  SENS-A   = traded ∧ status=ok ∧ rv finite (รวม 64 กลับ — โชว์ว่าผลไม่ได้มาจาก rank ปนเปื้อน)
  GATE-POP = all traded 1,487 (deployment-like) · วัน rv NaN = fail-open (ไม่ skip)

EVIDENCE หลัก [M1/M2/M4]:
  T_raw    = mean(pnl|B3) − mean(pnl|B1) บน PRIMARY
  T_within = สถิติเดียวกันบน pnl ที่ demean รายปี (one-way FE) — แยก within-year
             discrimination (deployable) ออกจาก year-coincidence (ปฏิทินปลอมตัว)
  NULL     = circular rotation ของ rv series (เรียงตามวัน, PRIMARY) ทุก rotation ที่
             distinct (N−1 ≈ 1,347 — deterministic ไม่ใช้ seed) · รักษา autocorr (lag1
             ≈ 0.6) · one-tailed: p = fraction(T_rot ≥ T_obs) · effective DOF = year-scale
             (~5-9 regime cycles) — ประกาศตรงๆ ว่านี่คือด่านยากที่ตั้งใจ
  CI       = bootstrap 10,000 (seed=11) ของ T_raw / T_within

PREDICTIONS (ประกาศก่อนรัน · P2 ถูก demote เป็น consistency-check ไม่ใช่ evidence [M2]):
  P1  T_raw > 0 และ p_raw < 0.05                    [evidence]
  P1w T_within > 0 และ p_within < 0.05              [evidence หลัก — กัน year-confound]
  P2  SUM(pnl|B1) < 0 บน PRIMARY                    [consistency-check: near-known
      เพราะรู้อยู่แล้วว่าปี vol ต่ำ = ปีแพ้ — ไม่นับเป็นหลักฐาน]
  PS  stability: sign(T3−T1 mean, within-year) ถูกทิศ ≥6/9 ปี และ ≥3/4 ปีชนะ
      (2013/15/16/20 — cell 18-27 วัน weight ต่ำ [MED-6] จึงไม่บังคับ 4/4)
  P3  GATE (skip วัน rv_pct250 < 33.3 บน GATE-POP) รายงานครบ §0 [M6]:
      (a) 5 ปีแพ้ (−135.2) ดีขึ้น ≥50% → > −67.6   (b) 4 ปีชนะ (+668.0) เสีย ≤20% → ≥ +534.4
      (c) pooled window (+532.8) ดีขึ้น ≥30% → ≥ +692.6   (d) worst year ≥ −150
      (e) ตาราง per-losing-year (aggregate ห้ามกลบ 2018/19 ที่ vol ปกติ)

OUTCOME MATRIX [M7] (pre-commit ทุก branch):
  P1w ✓ ∧ P3 ✓  → candidate signal บนสนาม search → เสนอ confirm stage (capped+tester)
  P1w ✓ ∧ P3 ✗  → association รายวันจริงแต่ gate เดี่ยวแก้ปีแพ้ไม่พอ → H0 ไม่ผ่าน §0
                   ทาง single-variable นี้ · rv เก็บเป็น candidate feature ของ brain
  P1w ✗ ∧ P3 ✓  → year-coincidence ปลอมตัว — ไม่รับ gate (กลไกไม่ยืน = หลบ) · falsified
  P1w ✗ ∧ P3 ✗  → H1 ตาย · บันทึก falsify เป็นผลงาน
  ทุก branch: +1 budget · BH correction เมื่อ family สะสมครบ (p เข้า family 40 ใบ)

Integrity: verify SHA256 chain ของ features + reconcile Σpnl = +532.8 ก่อนคำนวณ ·
script เป็นเจ้าของตัวเลขทุกตัว · ไม่แตะ 2021+
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent.parent / "Research" / "h0"
FACTS = DIR / "h0_day_facts_2012_2020.csv"
FEAT = DIR / "h0_features_2012_2020.csv"
SHA = DIR / "h0_features_2012_2020.sha256"

LO, HI = 33.3, 66.7
LOSERS = ["2012", "2014", "2017", "2018", "2019"]
WINNERS = ["2013", "2015", "2016", "2020"]


def band(v):
    return 1 if v < LO else (3 if v >= HI else 2)


def main():
    # ---- integrity chain ----
    sha_now = hashlib.sha256(FEAT.read_bytes()).hexdigest()
    assert sha_now == SHA.read_text(encoding="utf-8").split()[0], "features firewall broken"
    with open(FACTS, encoding="utf-8") as f:
        hdr = f.readline()
        assert sha_now in hdr, "day_facts ไม่ได้ join จาก features ฉบับ frozen นี้"
        rows = list(csv.DictReader(f))
    fv = lambda r, k: float(r[k]) if r[k] not in ("", None) else np.nan
    traded = [r for r in rows if r["traded"] == "1"]
    tot = sum(fv(r, "pnl") for r in traded)
    assert abs(tot - 532.8) < 0.1, f"reconciliation broken: {tot}"
    print(f"integrity OK: sha={sha_now[:12]}… · traded n={len(traded)} Σ={tot:+.1f}")

    # ---- populations [M5] ----
    ok_tr = [r for r in traded if r["status"] == "ok"]
    prim = [r for r in ok_tr if r["prev_ok"] == "1" and np.isfinite(fv(r, "rv_pct250"))]
    sens = [r for r in ok_tr if np.isfinite(fv(r, "rv_pct250"))]
    dropped = [r["date"] for r in ok_tr if r not in prim]
    print(f"PRIMARY n={len(prim)} · SENS-A n={len(sens)} · dropped {len(dropped)} "
          f"(ประกาศใน spec: 64 prev_ok=0 + NaN)")

    prim.sort(key=lambda r: r["date"])
    rv = np.array([fv(r, "rv_pct250") for r in prim])
    pnl = np.array([fv(r, "pnl") for r in prim])
    yr = np.array([r["date"][:4] for r in prim])
    ymean = {y: pnl[yr == y].mean() for y in np.unique(yr)}
    resid = pnl - np.array([ymean[y] for y in yr])
    bands = np.array([band(v) for v in rv])

    def T(p_arr, b_arr):
        return float(p_arr[b_arr == 3].mean() - p_arr[b_arr == 1].mean())

    T_raw, T_within = T(pnl, bands), T(resid, bands)

    # ---- permutation null: ทุก distinct rotation (deterministic) ----
    n = len(rv)
    Tr_null, Tw_null = [], []
    for k in range(1, n):
        b = np.array([band(v) for v in np.r_[rv[k:], rv[:k]]])
        if (b == 1).any() and (b == 3).any():
            Tr_null.append(T(pnl, b))
            Tw_null.append(T(resid, b))
    Tr_null, Tw_null = np.array(Tr_null), np.array(Tw_null)
    p_raw = float((Tr_null >= T_raw).mean())
    p_within = float((Tw_null >= T_within).mean())

    # ---- bootstrap CI (seed=11 ตาม convention โปรเจกต์) ----
    rng = np.random.default_rng(11)
    bs_r, bs_w = [], []
    for _ in range(10000):
        i = rng.integers(0, n, n)
        b = bands[i]
        if (b == 1).any() and (b == 3).any():
            bs_r.append(T(pnl[i], b))
            bs_w.append(T(resid[i], b))
    ci_r = np.percentile(bs_r, [2.5, 97.5])
    ci_w = np.percentile(bs_w, [2.5, 97.5])

    print("\n═══ EVIDENCE (PRIMARY) ═══")
    for bi in (1, 2, 3):
        m = bands == bi
        print(f"  B{bi} n={m.sum():>4} SUM={pnl[m].sum():+8.1f} AVG={pnl[m].mean():+.3f} "
              f"AVG_within={resid[m].mean():+.3f}")
    print(f"  T_raw    = {T_raw:+.3f}  p={p_raw:.4f} (rotations={len(Tr_null)}) "
          f"CI95=[{ci_r[0]:+.2f},{ci_r[1]:+.2f}]")
    print(f"  T_within = {T_within:+.3f}  p={p_within:.4f} "
          f"CI95=[{ci_w[0]:+.2f},{ci_w[1]:+.2f}]")
    print(f"  P1  (T_raw>0, p<.05):    {'PASS' if T_raw > 0 and p_raw < 0.05 else 'FAIL'}")
    print(f"  P1w (T_within>0, p<.05): {'PASS' if T_within > 0 and p_within < 0.05 else 'FAIL'}")
    print(f"  P2 consistency (SUM B1<0): {pnl[bands==1].sum():+.1f} → "
          f"{'consistent' if pnl[bands==1].sum() < 0 else 'INCONSISTENT'} [ไม่ใช่ evidence]")

    # ---- SENS-A ----
    rv_s = np.array([fv(r, "rv_pct250") for r in sens])
    pnl_s = np.array([fv(r, "pnl") for r in sens])
    yr_s = np.array([r["date"][:4] for r in sens])
    ym_s = {y: pnl_s[yr_s == y].mean() for y in np.unique(yr_s)}
    res_s = pnl_s - np.array([ym_s[y] for y in yr_s])
    b_s = np.array([band(v) for v in rv_s])
    print(f"  SENS-A (n={len(sens)}): T_raw={T(pnl_s, b_s):+.3f} "
          f"T_within={T(res_s, b_s):+.3f}")

    # ---- stability per year [PS] ----
    print("\n═══ per-year (within-year sign of T3−T1) ═══")
    good, wgood = 0, 0
    for y in sorted(np.unique(yr)):
        m = yr == y
        b1, b3 = m & (bands == 1), m & (bands == 3)
        t = pnl[b3].mean() - pnl[b1].mean() if b1.any() and b3.any() else np.nan
        s = "+" if np.isfinite(t) and t > 0 else "-"
        good += s == "+"
        if y in WINNERS:
            wgood += s == "+"
        print(f"  {y}: n1={b1.sum():>3} n3={b3.sum():>3} B1avg={pnl[b1].mean():+7.3f} "
              f"B3avg={pnl[b3].mean():+7.3f} T={t:+7.3f} [{s}]")
    print(f"  PS: sign+ {good}/9 (ต้อง ≥6) · winners {wgood}/4 (ต้อง ≥3) → "
          f"{'PASS' if good >= 6 and wgood >= 3 else 'FAIL'}")

    # ---- P3 gate บน GATE-POP (fail-open NaN) [M6] ----
    print("\n═══ P3 GATE: skip rv_pct250 < 33.3 · GATE-POP = all traded 1,487 ═══")
    base_y, gate_y = {}, {}
    for r in traded:
        y, p = r["date"][:4], fv(r, "pnl")
        base_y[y] = base_y.get(y, 0) + p
        v = fv(r, "rv_pct250")
        keep = (not np.isfinite(v)) or v >= LO       # fail-open
        if keep:
            gate_y[y] = gate_y.get(y, 0) + p
        else:
            gate_y.setdefault(y, gate_y.get(y, 0))
    print("  year   base     gated    Δ")
    for y in sorted(base_y):
        tag = "L" if y in LOSERS else "W"
        print(f"  {y}{tag} {base_y[y]:+8.1f} {gate_y.get(y,0):+8.1f} "
              f"{gate_y.get(y,0)-base_y[y]:+7.1f}")
    bl = sum(base_y[y] for y in LOSERS)
    gl = sum(gate_y.get(y, 0) for y in LOSERS)
    bw = sum(base_y[y] for y in WINNERS)
    gw = sum(gate_y.get(y, 0) for y in WINNERS)
    bp, gp = sum(base_y.values()), sum(gate_y.values())
    worst = min(gate_y.values())
    a = gl > -67.6
    b_ = gw >= 534.4
    c = gp >= 692.6
    d = worst >= -150
    print(f"  (a) losers  {bl:+.1f} → {gl:+.1f} (ต้อง > −67.6): {'PASS' if a else 'FAIL'}")
    print(f"  (b) winners {bw:+.1f} → {gw:+.1f} (ต้อง ≥ +534.4): {'PASS' if b_ else 'FAIL'}")
    print(f"  (c) pooled  {bp:+.1f} → {gp:+.1f} (ต้อง ≥ +692.6): {'PASS' if c else 'FAIL'}")
    print(f"  (d) worst-year gated = {worst:+.1f} (ต้อง ≥ −150): {'PASS' if d else 'FAIL'}")
    print(f"  P3 = {'PASS' if a and b_ and c and d else 'FAIL'}")


if __name__ == "__main__":
    main()
