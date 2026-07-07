#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_card_c9_dc.py — TRELLIS-010 Stage C · Card C9/H9 "Overshoot exhaustion" (budget 8/40)
Option A (วินสั่งรัน: "ไม่ควรทิ้ง อย่างน้อยได้พิสูจน์+บทเรียน+ความรู้") · ผนวก SE mandatory
ครบ: M1 (T_ehr เข้า conjunction เป็น leg 4 — cells eh-half จริง 6-18/ปี ไม่ใช่ 1-8 ·
ลบ reading rule) · M2 (assert SHA tickfeat แหล่ง rjR) · M3 (PRIMARY pin 859/565/294 ·
group จาก column dc_state ห้าม re-threshold) · M4 (primary=os_units · os_canon
agreement: conjunction verdict ต่างกัน = INCONCLUSIVE ไม่ใช่ pass)

⚠ GOVERNANCE DISCLOSURE: SE plan-review เปิดดู coarse conditional P&L (FRESH/SPENT
avg + AM/PM) ละเมิดข้อห้าม pre-empt — เกิด**หลัง** prediction ถูก freeze (kill-gate-2
entry) · การแก้หลัง leak ทั้งหมดเป็น tightening-only (เพิ่ม leg/assert — conjunction
มีแต่แข็งขึ้น) → pre-registration ของ prediction ยังยืน แต่ผลใบนี้ติดป้าย leak ถาวร

⭐ PREDICTION (frozen ก่อน leak): T = mean(FRESH os<1δ) − mean(SPENT os≥1δ) > 0
one-tailed · T<0 = FAIL ห้าม flip · δ=0.5×asian_width · window 08:00→close(j)
EVIDENCE = T_within ∧ T_joint(rv×rexp×yr) ∧ T_bsz(rjR-terc×yr) ∧ T_ehr(eh-half@11.90×yr)
· p_family = max 4 legs · PS ≥6/9 + winners ≥3/4 · P3 skip-SPENT (fail-open
UNDEF/OPPOSED) · outcome matrix เดิม

INTERPRETATION GUIDE (ประกาศก่อนรัน — เจตนา "บทเรียน+ความรู้"):
 (i) ตายเฉพาะ T_bsz → "os = bar-size proxy" corroborate C7 เชิงกลไก
 (ii) ตายทั้งแผง → overshoot-exhaustion เท็จบนสนามนี้
 (iii) ผ่านทั้ง 4 legs + os_canon agree → candidate มี caveat power (SPENT 23-42/ปี)
      ต้อง replicate ก่อนเชื่อ · canon disagree → INCONCLUSIVE
 (iv) ทุก branch = ความรู้ บันทึก ไม่ tune ไม่ flip
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from h0_cardkit import (LO as RLO, HI as RHI, WINNERS, bootstrap_ci, fv, gate_report,
                        load_facts, regression_card1, rotation_pvalues, year_demean)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent.parent / "Research" / "h0"
DC = DIR / "h0_dcfeat_2012_2020.csv"
DC_SHA = DIR / "h0_dcfeat_2012_2020.sha256"
TICK = DIR / "h0_tickfeat_2012_2020.csv"
TICK_SHA = DIR / "h0_tickfeat_2012_2020.sha256"
RV_AVG = {"B1": 0.539, "B2": -0.591, "B3": 1.291}
SP_AVG = {"UP": -0.352, "FLAT": 0.996, "DN": 0.564}
RE_AVG = {"CON": 0.695, "EXP": 0.037}
GA_AVG = {"LARGE": 1.060, "SMALL": 0.210}
EH_MED = 11.90                                   # M1: pin ex-ante จาก PRIMARY
ALIGNED = ("FRESH", "MID", "EXTENDED")


def main():
    sha_dc = hashlib.sha256(DC.read_bytes()).hexdigest()
    assert sha_dc == DC_SHA.read_text(encoding="utf-8").split()[0]
    assert sha_dc.startswith("2ed4ca67"), "ต้อง dcfeat v2 (+os_canon) เท่านั้น"
    sha_tk = hashlib.sha256(TICK.read_bytes()).hexdigest()
    assert sha_tk == TICK_SHA.read_text(encoding="utf-8").split()[0]
    assert sha_tk.startswith("69170d93"), "M2: rjR ต้องมาจาก tickfeat v2 signal-bar"
    rows, traded = load_facts()
    regression_card1(rows)
    with open(DC, encoding="utf-8") as f:
        dc = {r["date"]: r for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#"))}
    with open(TICK, encoding="utf-8") as f:
        tick = {r["date"]: r for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#"))}

    prim = [r for r in rows if r["traded"] == "1" and r["status"] == "ok"
            and r["prev_ok"] == "1" and dc[r["date"]]["dc_state"] in ALIGNED]
    prim.sort(key=lambda r: r["date"])
    st = np.array([dc[r["date"]]["dc_state"] for r in prim])
    stc = np.array([dc[r["date"]]["dc_state_canon"] for r in prim])
    osu = np.array([fv(dc[r["date"]], "os_units") for r in prim])
    spent = (st != "FRESH").astype(int)
    spent_c = (stc != "FRESH").astype(int)
    rjr = np.array([fv(tick[r["date"]], "rjR") for r in prim])
    assert np.isfinite(rjr).all(), "M2: rjR ต้อง finite ครบ PRIMARY — abort"
    pnl = np.array([fv(r, "pnl") for r in prim])
    yr = np.array([r["date"][:4] for r in prim])
    eh = np.array([int(r["entry_time"][:2]) + int(r["entry_time"][3:5]) / 60
                   for r in prim])
    rv = np.array([fv(r, "rv_pct250") for r in prim])
    sp = np.array([fv(r, "slope_pct250") for r in prim])
    re_ = np.array([fv(r, "range_exp") for r in prim])
    og = np.array([fv(r, "overnight_gap") for r in prim])
    pv = np.array([fv(r, "prev_range") for r in prim])
    gr = np.abs(og) / np.where(pv > 0, pv, np.nan)
    # M3 reconcile — เลขต้องตรงที่ pin ไม่งั้นมี filter หลุด
    assert len(prim) == 859 and int(spent.sum()) == 294, \
        f"PRIMARY ไม่ตรง pin 859/294: {len(prim)}/{int(spent.sum())}"
    print(f"PRIMARY n={len(prim)} FRESH={int((spent==0).sum())} SPENT={int(spent.sum())} ✓pin")

    rvb = np.where(rv < RLO, "B1", np.where(rv >= RHI, "B3", "B2"))
    spb = np.where(sp < RLO, "DN", np.where(sp >= RHI, "UP", "FLAT"))
    reb = np.where(re_ < 1.0, "CON", "EXP")
    gab = np.where(gr >= 0.05, "LARGE", "SMALL")
    q1, q2 = np.nanpercentile(rjr, [100 / 3, 200 / 3])
    bsb = np.where(rjr < q1, "S", np.where(rjr >= q2, "L", "M"))
    ehb = np.where(eh < EH_MED, "AM", "PM")
    resid = year_demean(pnl, yr)

    def cell_res(labels):
        key = np.array([f"{a}|{y}" for a, y in zip(labels, yr)])
        cm = {c: pnl[key == c].mean() for c in np.unique(key)}
        return pnl - np.array([cm[c] for c in key])

    jres = cell_res(np.array([f"{a}|{b}" for a, b in zip(rvb, reb)]))
    bres = cell_res(bsb)
    eres = cell_res(ehb)

    def T(arr, sp_vec):
        return arr[sp_vec == 0].mean() - arr[sp_vec == 1].mean()

    def imp_T(sp_vec):
        hi, lo = sp_vec == 0, sp_vec == 1
        s = sum((np.mean(rvb[hi] == b) - np.mean(rvb[lo] == b)) * RV_AVG[b] for b in RV_AVG)
        s += sum((np.mean(spb[hi] == b) - np.mean(spb[lo] == b)) * SP_AVG[b] for b in SP_AVG)
        s += sum((np.mean(reb[hi] == b) - np.mean(reb[lo] == b)) * RE_AVG[b] for b in RE_AVG)
        s += sum((np.mean(gab[hi] == b) - np.mean(gab[lo] == b)) * GA_AVG[b] for b in GA_AVG)
        return s

    def stat_for(sp_vec):
        if not ((sp_vec == 0).any() and (sp_vec == 1).any()):
            return np.array([np.nan] * 6)
        return np.array([T(pnl, sp_vec), T(resid, sp_vec), T(jres, sp_vec),
                         T(bres, sp_vec), T(eres, sp_vec),
                         T(pnl, sp_vec) - imp_T(sp_vec)])

    obs, p, nrot = rotation_pvalues(spent, stat_for)
    ci = bootstrap_ci(spent, [pnl, resid, jres, bres, eres],
                      lambda v, a, b, c, d, e: (np.array([T(a, v), T(b, v), T(c, v),
                                                          T(d, v), T(e, v)])
                                                if (v == 0).any() and (v == 1).any()
                                                else np.array([np.nan] * 5)))
    names = ["T_raw", "T_within", "T_joint", "T_bsz", "T_ehr", "T_adj(desc)"]
    print(f"\n═══ EVIDENCE (rotations={nrot}) ═══")
    for lab, m in (("FRESH", spent == 0), ("SPENT", spent == 1)):
        print(f"  {lab} n={int(m.sum()):>4} SUM={pnl[m].sum():+8.1f} AVG={pnl[m].mean():+.3f}")
    for i, nm in enumerate(names):
        ci_txt = f" CI95=[{ci[0, i]:+.2f},{ci[1, i]:+.2f}]" if i < 5 else ""
        print(f"  {nm:<12}= {obs[i]:+.3f} p={p[i]:.4f}{ci_txt}")
    legs = (1, 2, 3, 4)                          # M1: conjunction 4 legs
    ev = all(obs[i] > 0 and p[i] < 0.05 for i in legs)
    print(f"  P1 (T_raw): {'PASS' if obs[0] > 0 and p[0] < 0.05 else 'FAIL'} · "
          f"EVIDENCE (within∧joint∧bsz∧ehr): {'PASS' if ev else 'FAIL'} · "
          f"p_family={max(p[i] for i in legs):.4f}")
    print(f"  CONS SUM(SPENT)={pnl[spent==1].sum():+.1f} → "
          f"{'consistent' if pnl[spent==1].sum() < 0 else 'INCONSISTENT'} [non-evidence]")

    # M4: os_canon agreement (conjunction เดียวกันบน canon groups)
    obs_c, p_c, _ = rotation_pvalues(spent_c, stat_for)
    ev_c = all(obs_c[i] > 0 and p_c[i] < 0.05 for i in legs)
    agree = ev == ev_c
    print(f"\n═══ M4 os_canon agreement ═══")
    print(f"  canon: FRESH={int((spent_c==0).sum())}/SPENT={int((spent_c==1).sum())} "
          f"(flips {int((spent!=spent_c).sum())}) · evidence={'PASS' if ev_c else 'FAIL'} "
          f"→ {'AGREE' if agree else '⚠ DISAGREE → INCONCLUSIVE ไม่ใช่ pass'}")

    print("\n═══ descriptive (required) ═══")
    print(f"  morning(AM<{EH_MED})-SPENT/ปี:", " ".join(
        f"{y}:{int(((ehb=='AM')&(spent==1)&(yr==str(y))).sum())}" for y in range(2012, 2021)))
    m = np.isfinite(osu)
    print(f"  corr(os_units, pnl) = {np.corrcoef(osu[m], pnl[m])[0,1]:+.3f}")
    for cut in (0.75, 1.5):
        sv = (osu >= cut).astype(int)
        print(f"  sens cut {cut}: T_raw={T(pnl, sv):+.3f} (SPENT n={int(sv.sum())})")
    neg = osu < 0
    print(f"  FRESH split [R3]: os<0 n={int(neg.sum())} AVG={pnl[neg].mean():+.3f} · "
          f"0≤os<1 n={int(((spent==0)&~neg).sum())} AVG={pnl[(spent==0)&~neg].mean():+.3f}")
    und = [r for r in rows if r["traded"] == "1" and dc[r["date"]]["dc_state"] == "UNDEF"]
    opp = [r for r in rows if r["traded"] == "1" and dc[r["date"]]["dc_state"] == "OPPOSED"]
    print(f"  UNDEF n={len(und)} AVG={np.mean([fv(r,'pnl') for r in und]):+.3f} · "
          f"OPPOSED n={len(opp)} AVG={np.mean([fv(r,'pnl') for r in opp]):+.3f} [report แยก]")

    print("\n═══ per-year within sign (PS) ═══")
    good = wgood = 0
    for y in sorted(np.unique(yr)):
        my = yr == y
        f_, s_ = my & (spent == 0), my & (spent == 1)
        t = pnl[f_].mean() - pnl[s_].mean() if f_.any() and s_.any() else np.nan
        s = np.isfinite(t) and t > 0
        good += s
        wgood += s and y in WINNERS
        print(f"  {y}: nF={int(f_.sum()):>3} nS={int(s_.sum()):>3} T={t:+7.3f} "
              f"[{'+' if s else '-'}]")
    print(f"  PS: {good}/9 (≥6) · winners {wgood}/4 (≥3) → "
          f"{'PASS' if good >= 6 and wgood >= 3 else 'FAIL'}")

    print("\n═══ P3 GATE skip-SPENT (fail-open UNDEF/OPPOSED — R2) ═══")

    def skip(r):
        return dc[r["date"]]["dc_state"] in ("MID", "EXTENDED")

    P3 = gate_report(traded, skip, "skip-SPENT")
    print(f"\n═══ OUTCOME: evidence={'✓' if ev else '✗'} · canon-{'agree' if agree else 'DISAGREE'}"
          f" · P3={'✓' if P3 else '✗'} · budget 8/40 ═══")


if __name__ == "__main__":
    main()
