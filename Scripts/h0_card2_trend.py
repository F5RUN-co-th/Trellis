#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_card2_trend.py — TRELLIS-010 Stage H0 · Hypothesis Card #2 (test budget 2/40)
H2: "Trend-range state" — slope_pct250 เดี่ยว

ฉบับแก้ตาม Engineer review (PASS-with-changes ISSUE-1..4) + Claude Verify ยืนยันทุกเลข
สนามวัด: SIM SEARCH (uncapped 0.01 + catchup) จาก h0_day_facts (frozen) — MED-1:
ผลดีบนสนามนี้ห้ามเรียก edge จนผ่าน capped + real-tick tester confirm

═══ PRE-REGISTERED SPEC (freeze ก่อนรัน — ห้ามแก้หลังเห็นผล) ═══

STATE: จาก slope_pct250 (percentile ของ signed slope_08 เทียบ 250 ok-days, past-only):
  UP ≥ 66.7 · DN < 33.3 · FLAT = [33.3, 66.7) — fixed bands ค่าเดิม card #1
  contrast หลัก: TREND = UP ∪ DN vs FLAT (T = mean(TREND) − mean(FLAT))
  [ISSUE-3] ตาราง 3 กลุ่ม UP/FLAT/DN (SUM+AVG+within) = descriptive pre-registered ·
  T หลักมีตัวเดียว · **T < 0 (FLAT ชนะ) = FAIL one-tailed — ห้าม flip เป็น two-tailed
  หรือ split UP/DN หา significance ทีหลัง** (ตัวแปร/contrast ใหม่ = card ใหม่ +budget)
  semantics แจ้งชัด: DN = "ขึ้นน้อยกว่า baseline 250 วัน" ในยุค bull ไม่ใช่ downtrend สัมบูรณ์

POPULATION [ISSUE-2 — ตรง convention card #1]:
  PRIMARY = ok-traded ∧ prev_ok=1 ∧ slope_pct250 finite (~1,350 — ตัด 64 วัน EMA input
  ปนเปื้อนจากวัน short/hole: slope_08 shift +0.00138 vs −0.00001 วัดแล้ว)
  SENS-A  = ok-traded ∧ finite (1,414 รวม 64 กลับ)
  GATE-POP = all traded 1,487 · fail-open NaN

EVIDENCE (3 สถิติใต้ rotation null เดียวกัน — ทุก distinct rotation, one-tailed):
  T_raw    = mean(pnl|TREND) − mean(pnl|FLAT)
  T_within = บน pnl demean รายปี (year-confound control — M1 เดิม)
  T_adj    [ISSUE-1] = T_raw − implied_T โดย implied_T = Σ_b (frac_TREND,b −
             frac_FLAT,b) × AVG_rv,b ใช้ค่า published ของ card #1 (B1 +0.539,
             B2 −0.591, B3 +1.291 บน PRIMARY 1,350) — confound ที่วัดได้ ~+0.062
             เข้าข้าง pass เพราะ FLAT กระจุก 51% ใน rv-B1 · implied_T คำนวณใหม่ทุก
             rotation (composition เปลี่ยนตาม rotation, rv band ของแต่ละวันคงที่)
  + bootstrap CI95 (10k, seed=11) ทั้งสามตัว
  + descriptive: T ภายใน rv-band strata (B1/B2/B3) — ดูว่า slope แยกวันได้ภายใน
    vol ชั้นเดียวกันไหม (ไม่ใช่ evidence gate)

PREDICTIONS (ประกาศก่อนรัน):
  P1   T_raw > 0, p < 0.05
  P1w  T_within > 0, p < 0.05         [evidence หลักตัวที่ 1]
  P1a  T_adj > 0, p_adj < 0.05        [evidence หลักตัวที่ 2 — กัน vol-composition leakage]
  CONS SUM(pnl|FLAT) < 0              [consistency-check ไม่ใช่ evidence]
  PS   within-year sign(T) + ≥6/9 ปี และ ≥3/4 ปีชนะ (2013/15/16/20)
  P3   gate skip-FLAT บน GATE-POP รายงานครบ §0 (a)(b)(c)(d) + per-losing-year
       [tension ประกาศก่อน (Engineer SHOULD): FLAT = 476/1,487 = 32% ของ activity ·
        FLAT กระจุกในวัน rv-B1 ซึ่ง card #1 พบว่าเฉลี่ยกำไร +0.539 → gate นี้เสี่ยง
        ตัดวันทำเงิน — ถ้า P3 fail ด้วยเหตุนี้ = ผลที่ประกาศล่วงหน้าแล้ว ไม่ใช่นิทานทีหลัง]

OUTCOME MATRIX (pre-commit ทุก branch · evidence = P1w ∧ P1a):
  evidence ✓ ∧ P3 ✓ → candidate signal สนาม search → เสนอ confirm stage
  evidence ✓ ∧ P3 ✗ → association จริง แต่ gate เดี่ยวไม่พอ §0 → บันทึก candidate
                       feature ของ brain · H0 ทาง single-variable นี้ไม่จบ
  evidence ✗ (ทางใดทางหนึ่ง) → H2 falsified — ถ้า P1 ผ่านแต่ P1a ไม่ผ่าน = vol
                       leakage ปลอมตัว บันทึกชัด · ไม่รับ gate แม้ P3 ดูดี
  ทุก branch: budget 2/40 · p ทั้งหมดเข้า BH family 40

Integrity: kit regression ต้อง PASS เทียบเลข published card #1 ก่อนคำนวณใดๆ (ISSUE-4)
"""
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from h0_cardkit import (LO, HI, WINNERS, bootstrap_ci, fv, gate_report, load_facts,
                        regression_card1, rotation_pvalues, year_demean)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ค่า published ของ card #1 (PRIMARY 1,350) — constants ของ T_adj [ISSUE-1]
RV_AVG = {"B1": 0.539, "B2": -0.591, "B3": 1.291}


def main():
    rows, traded = load_facts()
    regression_card1(rows)              # ISSUE-4: kit ต้องเชื่อถือได้ก่อน

    ok_tr = [r for r in rows if r["traded"] == "1" and r["status"] == "ok"]
    prim = [r for r in ok_tr if r["prev_ok"] == "1"
            and np.isfinite(fv(r, "slope_pct250"))]
    prim.sort(key=lambda r: r["date"])
    sp = np.array([fv(r, "slope_pct250") for r in prim])
    pnl = np.array([fv(r, "pnl") for r in prim])
    yr = np.array([r["date"][:4] for r in prim])
    rv = np.array([fv(r, "rv_pct250") for r in prim])
    resid = year_demean(pnl, yr)
    rvb = np.where(rv < LO, "B1", np.where(rv >= HI, "B3", "B2"))
    rv_fin = np.isfinite(rv)
    print(f"\nPRIMARY n={len(prim)} (ok ∧ prev_ok=1 ∧ slope finite) · rv NaN ใน pop: "
          f"{int((~rv_fin).sum())} (exclude จาก composition/strata, คงใน T หลัก)")

    def groups(vals):
        trend = (vals >= HI) | (vals < LO)
        return trend, ~trend            # (TREND, FLAT)

    def implied_T(vals):
        trend, flat = groups(vals)
        t, f = trend & rv_fin, flat & rv_fin
        if not (t.any() and f.any()):
            return np.nan
        return sum((np.mean(rvb[t] == b) - np.mean(rvb[f] == b)) * RV_AVG[b]
                   for b in RV_AVG)

    def stat(vals):
        trend, flat = groups(vals)
        if not (trend.any() and flat.any()):
            return np.array([np.nan] * 3)
        t_raw = pnl[trend].mean() - pnl[flat].mean()
        t_win = resid[trend].mean() - resid[flat].mean()
        return np.array([t_raw, t_win, t_raw - implied_T(vals)])

    obs, p, nrot = rotation_pvalues(sp, stat)

    def bs_stat(vals, pnl_b, resid_b, rvb_b, rvfin_b):
        trend, flat = groups(vals)
        if not (trend.any() and flat.any()):
            return np.array([np.nan] * 3)
        t, f = trend & rvfin_b, flat & rvfin_b
        imp = (sum((np.mean(rvb_b[t] == b) - np.mean(rvb_b[f] == b)) * RV_AVG[b]
                   for b in RV_AVG) if t.any() and f.any() else np.nan)
        t_raw = pnl_b[trend].mean() - pnl_b[flat].mean()
        return np.array([t_raw, resid_b[trend].mean() - resid_b[flat].mean(),
                         t_raw - imp])

    ci = bootstrap_ci(sp, [pnl, resid, rvb, rv_fin], bs_stat)

    print("\n═══ EVIDENCE (PRIMARY) ═══")
    trend, flat = groups(sp)
    up, dn = sp >= HI, sp < LO
    for lab, m in [("UP  ", up), ("FLAT", flat), ("DN  ", dn)]:
        print(f"  {lab} n={m.sum():>4} SUM={pnl[m].sum():+8.1f} AVG={pnl[m].mean():+.3f} "
              f"AVG_within={resid[m].mean():+.3f}")
    names = ["T_raw", "T_within", "T_adj"]
    for i, nm in enumerate(names):
        print(f"  {nm:<9}= {obs[i]:+.3f}  p={p[i]:.4f}  CI95=[{ci[0,i]:+.2f},{ci[1,i]:+.2f}]")
    print(f"  implied_T (vol-composition confound) = {implied_T(sp):+.3f} · rotations={nrot}")
    P1 = obs[0] > 0 and p[0] < 0.05
    P1w = obs[1] > 0 and p[1] < 0.05
    P1a = obs[2] > 0 and p[2] < 0.05
    print(f"  P1  (T_raw): {'PASS' if P1 else 'FAIL'} · P1w (within): "
          f"{'PASS' if P1w else 'FAIL'} · P1a (adj): {'PASS' if P1a else 'FAIL'}")
    print(f"  CONS SUM(FLAT)={pnl[flat].sum():+.1f} → "
          f"{'consistent' if pnl[flat].sum() < 0 else 'INCONSISTENT'} [non-evidence]")

    # SENS-A (inclusive 1,414)
    sens = [r for r in ok_tr if np.isfinite(fv(r, "slope_pct250"))]
    sens.sort(key=lambda r: r["date"])
    sp_s = np.array([fv(r, "slope_pct250") for r in sens])
    pnl_s = np.array([fv(r, "pnl") for r in sens])
    res_s = year_demean(pnl_s, np.array([r["date"][:4] for r in sens]))
    tr_s, fl_s = (sp_s >= HI) | (sp_s < LO), ~((sp_s >= HI) | (sp_s < LO))
    print(f"  SENS-A (n={len(sens)}): T_raw={pnl_s[tr_s].mean()-pnl_s[fl_s].mean():+.3f} "
          f"T_within={res_s[tr_s].mean()-res_s[fl_s].mean():+.3f}")

    # descriptive: T ภายใน rv-band strata
    print("\n═══ descriptive: TREND−FLAT ภายใน rv-band (ไม่ใช่ evidence gate) ═══")
    for b in ("B1", "B2", "B3"):
        m = rv_fin & (rvb == b)
        t, f = m & trend, m & flat
        if t.any() and f.any():
            print(f"  {b}: n_T={t.sum():>3} n_F={f.sum():>3} "
                  f"T={pnl[t].mean()-pnl[f].mean():+.3f}")

    # PS per-year
    print("\n═══ per-year within-year sign of TREND−FLAT ═══")
    good, wgood = 0, 0
    for y in sorted(np.unique(yr)):
        m = yr == y
        t, f = m & trend, m & flat
        tt = pnl[t].mean() - pnl[f].mean() if t.any() and f.any() else np.nan
        s = "+" if np.isfinite(tt) and tt > 0 else "-"
        good += s == "+"
        if y in WINNERS:
            wgood += s == "+"
        print(f"  {y}: nT={t.sum():>3} nF={f.sum():>3} T={tt:+7.3f} [{s}]")
    PS = good >= 6 and wgood >= 3
    print(f"  PS: sign+ {good}/9 (≥6) · winners {wgood}/4 (≥3) → {'PASS' if PS else 'FAIL'}")

    # P3 gate: skip FLAT (fail-open NaN)
    print("\n═══ P3 GATE: skip slope_pct250 ∈ [33.3,66.7) · GATE-POP all traded ═══")

    def skip(r):
        v = fv(r, "slope_pct250")
        return np.isfinite(v) and LO <= v < HI

    P3 = gate_report(traded, skip, "skip-FLAT")

    ev = P1w and P1a
    print(f"\n═══ OUTCOME: evidence(P1w∧P1a)={'✓' if ev else '✗'} · P3={'✓' if P3 else '✗'} ═══")


if __name__ == "__main__":
    main()
