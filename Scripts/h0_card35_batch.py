#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_card35_batch.py — TRELLIS-010 Stage H0 · Batch Hypothesis Cards #3–5 (budget → 5/40)
รันรวดเดียว · prediction ทั้งสามใบ freeze พร้อมกันก่อนรันใบแรก (กัน sequential contamination)
ฉบับแก้ตาม Engineer review (PASS-with-changes) + Claude Verify ยืนยันทุกเลข
สนามวัด: SIM SEARCH (uncapped+catchup) จาก h0_day_facts (frozen) — MED-1 ห้ามเรียก edge
จนผ่าน capped+real-tick confirm · หลัง batch นี้ = ประกาศ H0 concluded (วินอนุมัติ)

═══ PRE-REGISTERED SPEC ═══

โครงร่วม: PRIMARY = traded ∧ ok ∧ prev_ok=1 (1,350 — ทุก feature finite ครบ ตรวจแล้ว) ·
rotation null ทุก distinct rotation one-tailed p = frac(T_rot ≥ T_obs) · bootstrap CI 10k
seed=11 · PS within-year sign ≥6/9 + ≥3/4 ปีชนะ · P3 gate all-traded 1,487 fail-open
ครบ §0 · outcome matrix แบบ card #2 · kit regression ต่อ card #1 ต้อง PASS ก่อน ·
**BH family-40: p ต่อ card = max(p) ของ evidence conjunction (intersection-union)**

CARD #3 — H3 range_exp: CONTRACT (<1.0) vs EXPAND (≥1.0) · ค่าคงที่ธรรมชาติ 1.0
  Mechanism: Crabel NR / volatility-cycle — contraction นำ expansion → breakout ดีกว่า
  DISCLOSURE: corr กับ rv_pct250 (ตายแล้ว) = +0.429 · CONTRACT โหลด cell rvB1×FLAT 5:1
  (178/35) = สองแหล่งกำไร post-hoc ของ card #1/#2 → **[Engineer mandatory] evidence
  decisive = T_joint**: demean pnl ภายใน cell rv-band × slope-band × year (81 cells,
  min side 35 ไม่มี degeneracy) — additive T_adj ลำพังปิด interaction ไม่มิด รายงานประกอบ
  PREDICTION: P1 T_raw>0 p<.05 · EVIDENCE = T_joint>0 p<.05 ∧ T_within>0 p<.05 ·
  PS · P3 = skip EXPAND · p_family = max(p_joint, p_within)
  ถ้า T_adj ผ่านแต่ T_joint ไม่ผ่าน = vol/slope-composition leakage → ไม่รับแม้ P3 ดูดี

CARD #4 — H4 gap_ratio = |overnight_gap|/prev_range: LARGE (≥0.05) vs SMALL (<0.05)
  Mechanism: overnight repricing/imbalance → directional energy ต่อเนื่อง intraday
  DISCLOSURE: corr(gap_ratio, days_since_prev) = +0.377 — gap ใหญ่พันกับ weekend/holiday
  → **[Engineer mandatory] co-primary T_ds1**: test ซ้ำบน subset days_since_prev==1
  (n≈1,133 — overnight แท้ ตัด multi-day drift · rotation null ของ subset เอง) ·
  PS ประกาศเป็น low-power (LARGE cell ปีชนะ 16-18 วัน) — รายงานแต่ไม่ใช้ตัดสินเดี่ยว ·
  threshold-sensitivity descriptive: sign(T_raw) ที่ cut {0.03, 0.05, 0.08}
  PREDICTION: P1 T_raw>0 p<.05 · EVIDENCE = T_ds1>0 p<.05 ∧ T_within>0 p<.05 ·
  P3 = skip SMALL (tension ประกาศ: ตัด ~78% activity) · p_family = max(p_ds1, p_within)

CARD #5 — H5 aw_ratio = asian_width/prev_range: NARROW (<0.4) vs WIDE (≥0.4)
  **Outcome = R-multiple (pnl/R)** — asian_width = R identity (ตรวจแล้ว) ทดสอบใน $ =
  วัดกลไก scaling ไม่ใช่ regime · Engineer วิเคราะห์: cost-fraction ของ R เล็กกด NARROW
  = bias ต้าน prediction (conservative — ถ้าชนะคือชนะทั้ง headwind)
  Mechanism: compression ระดับ session → expansion แรงหลัง break (NR ที่ session scale)
  PREDICTION: P1 T_raw>0 p<.05 (R-multiple) · EVIDENCE = T_within>0 p<.05 ∧
  strata-consistency (sign T ตรงทิศ ≥2/3 rv-strata) · PS (R-multiple) · P3 = skip WIDE
  (วัด $) · p_family = p_within · SHOULD: T_median descriptive + sens {0.3, 0.4, 0.5}

dow: ตาราง descriptive เท่านั้น (encoding 0=Mon..4=Fri — Engineer note "ไม่มี Friday"
ตรวจแล้วผิด: Engineer ใช้ MQL convention · dow=4 map เป็น Friday จริง เช่น 2012-01-06)

Integrity: ตัวเลขทุกตัวจาก script · lockbox 2021+ ไม่แตะ · budget 2/40 → 5/40 เมื่อรัน
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from h0_cardkit import (LO, HI, WINNERS, bootstrap_ci, fv, gate_report, load_facts,
                        regression_card1, rotation_pvalues, year_demean)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RV_AVG = {"B1": 0.539, "B2": -0.591, "B3": 1.291}          # card #1 published
SP_AVG = {"UP": -0.352, "FLAT": 0.996, "DN": 0.564}        # card #2 published


def main():
    rows, traded = load_facts()
    regression_card1(rows)

    prim = [r for r in rows if r["traded"] == "1" and r["status"] == "ok"
            and r["prev_ok"] == "1"]
    prim.sort(key=lambda r: r["date"])
    pnl = np.array([fv(r, "pnl") for r in prim])
    yr = np.array([r["date"][:4] for r in prim])
    rv = np.array([fv(r, "rv_pct250") for r in prim])
    sp = np.array([fv(r, "slope_pct250") for r in prim])
    ds = np.array([fv(r, "days_since_prev") for r in prim])
    R = np.array([fv(r, "R") for r in prim])
    rvb = np.where(rv < LO, "B1", np.where(rv >= HI, "B3", "B2"))
    spb = np.where(sp < LO, "DN", np.where(sp >= HI, "UP", "FLAT"))
    resid = year_demean(pnl, yr)
    # T_joint: demean ภายใน cell rv×slope×year (Engineer mandatory card #3)
    cell = np.array([f"{a}|{b}|{c}" for a, b, c in zip(rvb, spb, yr)])
    cm = {c: pnl[cell == c].mean() for c in np.unique(cell)}
    jresid = pnl - np.array([cm[c] for c in cell])
    assert not np.isnan(pnl).any() and len(prim) == 1350
    print(f"PRIMARY n={len(prim)} · joint cells={len(cm)}")

    def T(v_out, hi, lo):
        return v_out[hi].mean() - v_out[lo].mean()

    def per_year_ps(v_out, hi, lo, label):
        good = wgood = 0
        for y in sorted(np.unique(yr)):
            m = yr == y
            t = T(v_out, m & hi, m & lo) if (m & hi).any() and (m & lo).any() else np.nan
            s = np.isfinite(t) and t > 0
            good += s
            wgood += s and y in WINNERS
        print(f"  PS[{label}]: sign+ {good}/9 · winners {wgood}/4 → "
              f"{'PASS' if good >= 6 and wgood >= 3 else 'FAIL'}")
        return good >= 6 and wgood >= 3

    def imp_T(hi, lo):
        return (sum((np.mean(rvb[hi] == b) - np.mean(rvb[lo] == b)) * RV_AVG[b]
                    for b in RV_AVG)
                + sum((np.mean(spb[hi] == s) - np.mean(spb[lo] == s)) * SP_AVG[s]
                      for s in SP_AVG))

    # ═══ CARD #3 ═══
    re_ = np.array([fv(r, "range_exp") for r in prim])

    def g3(vals):
        return vals < 1.0, vals >= 1.0                     # (CONTRACT=hi, EXPAND=lo)

    def s3(vals):
        hi, lo = g3(vals)
        if not (hi.any() and lo.any()):
            return np.array([np.nan] * 4)
        return np.array([T(pnl, hi, lo), T(resid, hi, lo),
                         T(pnl, hi, lo) - imp_T(hi, lo), T(jresid, hi, lo)])

    obs3, p3_, n3 = rotation_pvalues(re_, s3)
    ci3 = bootstrap_ci(re_, [pnl, resid, jresid],
                       lambda v, a, b, c: (np.array([T(a, *g3(v)), T(b, *g3(v)),
                                                     T(c, *g3(v))])
                                           if g3(v)[0].any() and g3(v)[1].any()
                                           else np.array([np.nan] * 3)))
    print(f"\n═══ CARD #3 range_exp (CONTRACT<1.0 vs EXPAND) · rotations={n3} ═══")
    hi, lo = g3(re_)
    print(f"  CONTRACT n={hi.sum()} SUM={pnl[hi].sum():+.1f} AVG={pnl[hi].mean():+.3f} · "
          f"EXPAND n={lo.sum()} SUM={pnl[lo].sum():+.1f} AVG={pnl[lo].mean():+.3f}")
    ci3m = {0: 0, 1: 1, 3: 2}      # map obs index → ci column (T_adj ไม่มี CI)
    for i, nm in enumerate(["T_raw", "T_within", "T_adj", "T_joint"]):
        ci_txt = (f" CI95=[{ci3[0, ci3m[i]]:+.2f},{ci3[1, ci3m[i]]:+.2f}]"
                  if i in ci3m else "")
        print(f"  {nm:<9}= {obs3[i]:+.3f} p={p3_[i]:.4f}{ci_txt}")
    ev3 = obs3[3] > 0 and p3_[3] < 0.05 and obs3[1] > 0 and p3_[1] < 0.05
    print(f"  EVIDENCE (T_joint ∧ T_within) = {'PASS' if ev3 else 'FAIL'} · "
          f"p_family = {max(p3_[3], p3_[1]):.4f}")
    per_year_ps(pnl, hi, lo, "C3 $")
    print("  P3 gate skip-EXPAND:")
    P3c3 = gate_report(traded, lambda r: (lambda v: np.isfinite(v) and v >= 1.0)(
        fv(r, "range_exp")), "skip-EXPAND")

    # ═══ CARD #4 ═══
    og = np.array([fv(r, "overnight_gap") for r in prim])
    pr = np.array([fv(r, "prev_range") for r in prim])
    gr = np.abs(og) / pr

    def g4(vals):
        return vals >= 0.05, vals < 0.05                   # (LARGE=hi, SMALL=lo)

    def s4(vals):
        hi, lo = g4(vals)
        if not (hi.any() and lo.any()):
            return np.array([np.nan] * 3)
        return np.array([T(pnl, hi, lo), T(resid, hi, lo),
                         T(pnl, hi, lo) - imp_T(hi, lo)])

    obs4, p4_, n4 = rotation_pvalues(gr, s4)
    # co-primary: subset days_since==1 (rotation null ของ subset เอง)
    m1 = ds == 1
    pnl1, res1, gr1 = pnl[m1], resid[m1], gr[m1]

    def s4d(vals):
        hi, lo = g4(vals)
        if not (hi.any() and lo.any()):
            return np.array([np.nan])
        return np.array([T(pnl1, hi, lo)])

    obs4d, p4d, n4d = rotation_pvalues(gr1, s4d)
    ci4 = bootstrap_ci(gr, [pnl, resid],
                       lambda v, a, b: (np.array([T(a, *g4(v)), T(b, *g4(v))])
                                        if g4(v)[0].any() and g4(v)[1].any()
                                        else np.array([np.nan] * 2)))
    ci4d = bootstrap_ci(gr1, [pnl1],
                        lambda v, a: (np.array([T(a, *g4(v))])
                                      if g4(v)[0].any() and g4(v)[1].any()
                                      else np.array([np.nan])))
    print(f"\n═══ CARD #4 gap_ratio (LARGE≥0.05 vs SMALL) · rotations={n4} ═══")
    hi, lo = g4(gr)
    print(f"  LARGE n={hi.sum()} SUM={pnl[hi].sum():+.1f} AVG={pnl[hi].mean():+.3f} · "
          f"SMALL n={lo.sum()} SUM={pnl[lo].sum():+.1f} AVG={pnl[lo].mean():+.3f}")
    for i, nm in enumerate(["T_raw", "T_within", "T_adj"]):
        ci_txt = (f" CI95=[{ci4[0, i]:+.2f},{ci4[1, i]:+.2f}]" if i < 2 else "")
        print(f"  {nm:<9}= {obs4[i]:+.3f} p={p4_[i]:.4f}{ci_txt}")
    print(f"  T_ds1     = {obs4d[0]:+.3f} p={p4d[0]:.4f} "
          f"CI95=[{ci4d[0, 0]:+.2f},{ci4d[1, 0]:+.2f}] (subset n={m1.sum()}, "
          f"rotations={n4d})")
    ev4 = obs4d[0] > 0 and p4d[0] < 0.05 and obs4[1] > 0 and p4_[1] < 0.05
    print(f"  EVIDENCE (T_ds1 ∧ T_within) = {'PASS' if ev4 else 'FAIL'} · "
          f"p_family = {max(p4d[0], p4_[1]):.4f}")
    per_year_ps(pnl, hi, lo, "C4 $ (LOW-POWER — ไม่ใช้ตัดสินเดี่ยว)")
    for cut in (0.03, 0.05, 0.08):
        h2, l2 = gr >= cut, gr < cut
        print(f"  sens cut {cut}: T_raw={T(pnl, h2, l2):+.3f}")
    def ratio_of(r, num_col, absval=False):
        """ratio จาก 2 คอลัมน์ frozen — NaN ถ้าคำนวณไม่ได้ (prev_range 0/หาย) = fail-open"""
        num, den = fv(r, num_col), fv(r, "prev_range")
        if not (np.isfinite(num) and np.isfinite(den)) or den <= 0:
            return float("nan")
        return abs(num) / den if absval else num / den

    print("  P3 gate skip-SMALL (tension: ตัด ~78% activity — ประกาศแล้ว):")
    P3c4 = gate_report(traded, lambda r: (lambda v: np.isfinite(v) and v < 0.05)(
        ratio_of(r, "overnight_gap", absval=True)), "skip-SMALL")

    # ═══ CARD #5 ═══
    aw = np.array([fv(r, "asian_width") for r in prim])
    ar = aw / pr
    rm = pnl / R
    rm_res = year_demean(rm, yr)

    def g5(vals):
        return vals < 0.4, vals >= 0.4                     # (NARROW=hi, WIDE=lo)

    def s5(vals):
        hi, lo = g5(vals)
        if not (hi.any() and lo.any()):
            return np.array([np.nan] * 3)
        return np.array([T(rm, hi, lo), T(rm_res, hi, lo),
                         np.median(rm[hi]) - np.median(rm[lo])])

    obs5, p5_, n5 = rotation_pvalues(ar, s5)
    ci5 = bootstrap_ci(ar, [rm, rm_res],
                       lambda v, a, b: (np.array([T(a, *g5(v)), T(b, *g5(v))])
                                        if g5(v)[0].any() and g5(v)[1].any()
                                        else np.array([np.nan] * 2)))
    print(f"\n═══ CARD #5 aw_ratio (NARROW<0.4 vs WIDE) · outcome=R-multiple · "
          f"rotations={n5} ═══")
    hi, lo = g5(ar)
    print(f"  NARROW n={hi.sum()} meanRm={rm[hi].mean():+.4f} · "
          f"WIDE n={lo.sum()} meanRm={rm[lo].mean():+.4f}")
    for i, nm in enumerate(["T_raw", "T_within", "T_median(desc)"]):
        ci_txt = (f" CI95=[{ci5[0, i]:+.3f},{ci5[1, i]:+.3f}]" if i < 2 else "")
        print(f"  {nm:<15}= {obs5[i]:+.4f} p={p5_[i]:.4f}{ci_txt}")
    strata_ok = 0
    for b in ("B1", "B2", "B3"):
        m = rvb == b
        t = T(rm, m & hi, m & lo) if (m & hi).any() and (m & lo).any() else np.nan
        strata_ok += np.isfinite(t) and t > 0
        print(f"  strata {b}: T={t:+.4f}")
    ev5 = obs5[1] > 0 and p5_[1] < 0.05 and strata_ok >= 2
    print(f"  EVIDENCE (T_within ∧ strata ≥2/3 [{strata_ok}/3]) = "
          f"{'PASS' if ev5 else 'FAIL'} · p_family = {p5_[1]:.4f}")
    per_year_ps(rm, hi, lo, "C5 R-multiple")
    for cut in (0.3, 0.4, 0.5):
        h2, l2 = ar < cut, ar >= cut
        print(f"  sens cut {cut}: T_raw(Rm)={T(rm, h2, l2):+.4f}")
    print("  P3 gate skip-WIDE (วัด $):")
    P3c5 = gate_report(traded, lambda r: (lambda v: np.isfinite(v) and v >= 0.4)(
        ratio_of(r, "asian_width")), "skip-WIDE")

    # dow descriptive (0=Mon..4=Fri)
    print("\n═══ dow descriptive (0=Mon..4=Fri — ไม่ใช่ test ไม่เผา budget) ═══")
    for d in "01234":
        m = np.array([r["dow"] == d for r in prim])
        print(f"  {'Mon Tue Wed Thu Fri'.split()[int(d)]}: n={m.sum():>3} "
              f"SUM={pnl[m].sum():+8.1f} AVG={pnl[m].mean():+.3f}")

    print(f"\n═══ BATCH OUTCOME: C3 ev={'✓' if ev3 else '✗'} P3={'✓' if P3c3 else '✗'} · "
          f"C4 ev={'✓' if ev4 else '✗'} P3={'✓' if P3c4 else '✗'} · "
          f"C5 ev={'✓' if ev5 else '✗'} P3={'✓' if P3c5 else '✗'} · budget 5/40 ═══")


if __name__ == "__main__":
    main()
