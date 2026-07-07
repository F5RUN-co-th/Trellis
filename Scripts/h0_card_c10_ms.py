#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_card_c10_ms.py — TRELLIS-010 Stage C · Card C10/H10 "Market-Structure alignment"
(budget 9/40) · WS-2 full card (วินเลือก full card over fold, 2026-07-07) · SE review MC-1..5

MECHANISM: v4 = breakout-continuation · เข้าไม้ทางที่ตรงกับ swing-structure ที่มีอยู่
(ALIGNED: structure UP ∧ LONG หรือ DOWN ∧ SHORT) = ตามโครงสร้าง → follow-through ดีกว่า ·
OPPOSED = ทะลุสวนโครงสร้าง = เข้าโซนที่ structure ยังไม่ confirm = fade risk
⭐ PREDICTION: T = mean(pnl|ALIGNED) − mean(pnl|OPPOSED) > 0 · one-tailed · T<0 = FAIL
ห้าม flip (reading ตรงข้าม "OPPOSED = ทะลุ level ที่ structure ยังไม่รับรอง = breakout จริง"
มีจริง — ถ้า T<0 = card ใหม่ ไม่ flip)

PRIMARY: traded ∧ ok ∧ prev_ok=1 ∧ ms_state ∈ {ALIGNED, OPPOSED} (n=660 · A360/O300)
  group = column ms_state ตรงๆ (categorical — ไม่มี re-threshold [MC-3])
  MIXED (486)/UNDEF (281) = descriptive report เท่านั้น (unconditional — ไม่ cherry-pick)
EVIDENCE = 4-leg conjunction (mirror C9): T_within ∧ T_joint (rv×rexp×year) ∧
  T_bsz (rjR-tercile×year) ∧ T_ehr (eh-tercile×year) · ทุกตัว >0 p<.05 rotation null · p_family=max
  [MC-4] honest: kill-gate corr(ALIGNED,rjR)=+0.020 / eh=−0.028 → T_bsz≈T_ehr≈T_within
  (near-collinear) → leg ที่ **bind จริง = T_within + T_joint** (2 hurdles) · bsz/ehr = conservative
  (p_family=max ทำให้ผ่านยากขึ้นเท่านั้น) ไม่ใช่ "รอด 4 controls อิสระ" (ต่างจาก C9 ที่ rjR=0.396)
P3: gate skip-OPPOSED (deployable — ms_state รู้ ณ close ของ j−1) · [MC-3] hard-pin —
  ห้ามสลับ skip-MIXED / skip-{OPPOSED∪MIXED}
DoF ex-ante [MC-2]: eh cuts (9.433,12.55) · rjR cuts (0.1107,0.2226) — literal + assert anti-drift
SHA [MC-1]: msfeat 2a4fb559 + tickfeat 69170d93 (control leg บน feature ไม่ pin = void-class)
สนามวัด SIM SEARCH (MED-1) · budget → 9/40 เมื่อรัน · BH family = ทั้ง 9 ใบ
Interpretation guide (R4): (i) ev✓+P3✓+PS✓ → 3rd axis Stage D (ต้อง collapse ≤12 cfg [MC-5]) ·
  (ii) ev✓ P3✗ → เหมือน C9/C6 signal จริง static filter ไม่พอ → material Stage D ·
  (iii) ev✗ → MS ไม่เพิ่มข้อมูลเกิน feature เดิม → C10 falsified fold nothing ·
  (iv) T<0 → structure-fade regime → falsified no-flip
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
MS = DIR / "h0_msfeat_2012_2020.csv"
MS_SHA = DIR / "h0_msfeat_2012_2020.sha256"
TICK = DIR / "h0_tickfeat_2012_2020.csv"
TICK_SHA = DIR / "h0_tickfeat_2012_2020.sha256"
EH_CUT = (9.433, 12.55)          # [MC-2] fix ex-ante จาก PRIMARY eh terciles
RJ_CUT = (0.1107, 0.2226)        # [MC-2] fix ex-ante จาก PRIMARY rjR terciles


def main():
    # [MC-1] SHA assert ทั้งสอง feature (msfeat state + tickfeat control leg = void ถ้าไม่ pin)
    sha_ms = hashlib.sha256(MS.read_bytes()).hexdigest()
    assert sha_ms == MS_SHA.read_text(encoding="utf-8").split()[0]
    assert sha_ms.startswith("2a4fb559"), "ต้องเป็น msfeat frozen เท่านั้น [MC-1]"
    sha_tk = hashlib.sha256(TICK.read_bytes()).hexdigest()
    assert sha_tk == TICK_SHA.read_text(encoding="utf-8").split()[0]
    assert sha_tk.startswith("69170d93"), "tickfeat control leg ไม่ pin = void-class [MC-1]"
    rows, traded = load_facts()
    regression_card1(rows)
    with open(MS, encoding="utf-8") as f:
        ms = {r["date"]: r for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#"))}
    with open(TICK, encoding="utf-8") as f:
        tick = {r["date"]: r for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#"))}

    prim = [r for r in rows if r["traded"] == "1" and r["status"] == "ok"
            and r["prev_ok"] == "1" and ms[r["date"]]["ms_state"] in ("ALIGNED", "OPPOSED")]
    prim.sort(key=lambda r: r["date"])
    al = np.array([1 if ms[r["date"]]["ms_state"] == "ALIGNED" else 0 for r in prim])
    pnl = np.array([fv(r, "pnl") for r in prim])
    yr = np.array([r["date"][:4] for r in prim])
    rv = np.array([fv(r, "rv_pct250") for r in prim])
    re_ = np.array([fv(r, "range_exp") for r in prim])
    rj = np.array([fv(tick[r["date"]], "rjR") for r in prim])
    eh = np.array([int(r["entry_time"][:2]) + int(r["entry_time"][3:5]) / 60 for r in prim])

    # [MC-2] assert terciles ตรง literal ภายใน tol (anti-drift — population เปลี่ยน = จับได้)
    eh_p = np.nanpercentile(eh, [100 / 3, 200 / 3])
    rj_p = np.nanpercentile(rj, [100 / 3, 200 / 3])
    assert all(abs(a - b) < 5e-3 for a, b in zip(eh_p, EH_CUT)), f"eh tercile drift {eh_p} [MC-2]"
    assert all(abs(a - b) < 5e-4 for a, b in zip(rj_p, RJ_CUT)), f"rjR tercile drift {rj_p} [MC-2]"

    rvb = np.where(rv < RLO, "B1", np.where(rv >= RHI, "B3", "B2"))
    reb = np.where(re_ < 1.0, "CON", "EXP")
    ehb = np.where(eh < EH_CUT[0], "E", np.where(eh >= EH_CUT[1], "L", "M"))
    rjb = np.where(rj < RJ_CUT[0], "lo", np.where(rj >= RJ_CUT[1], "hi", "mid"))
    resid = year_demean(pnl, yr)
    cj = np.array([f"{a}|{b}|{c}" for a, b, c in zip(rvb, reb, yr)])
    cmj = {c: pnl[cj == c].mean() for c in np.unique(cj)}
    jres = pnl - np.array([cmj[c] for c in cj])
    cb = np.array([f"{a}|{c}" for a, c in zip(rjb, yr)])
    cmb = {c: pnl[cb == c].mean() for c in np.unique(cb)}
    bres = pnl - np.array([cmb[c] for c in cb])
    ce = np.array([f"{a}|{c}" for a, c in zip(ehb, yr)])
    cme = {c: pnl[ce == c].mean() for c in np.unique(ce)}
    eres = pnl - np.array([cme[c] for c in ce])
    print(f"PRIMARY n={len(prim)} · ALIGNED={int(al.sum())} OPPOSED={int((1 - al).sum())}")

    def groups(vals):
        return vals == 1, vals == 0            # (ALIGNED=hi ตาม prediction, OPPOSED=lo)

    def T(arr, hi, lo):
        return arr[hi].mean() - arr[lo].mean()

    def stat(vals):
        hi, lo = groups(vals)
        if not (hi.any() and lo.any()):
            return np.array([np.nan] * 5)
        return np.array([T(pnl, hi, lo), T(resid, hi, lo), T(jres, hi, lo),
                         T(bres, hi, lo), T(eres, hi, lo)])

    obs, p, nrot = rotation_pvalues(al, stat)
    ci = bootstrap_ci(al, [pnl, resid, jres, bres, eres],
                      lambda vv, a, b, c, d, e: (
                          np.array([T(a, *groups(vv)), T(b, *groups(vv)), T(c, *groups(vv)),
                                    T(d, *groups(vv)), T(e, *groups(vv))])
                          if groups(vv)[0].any() and groups(vv)[1].any()
                          else np.array([np.nan] * 5)))
    hi, lo = groups(al)
    print(f"\n═══ EVIDENCE (rotations={nrot}) ═══")
    print(f"  ALIGNED n={hi.sum():>4} SUM={pnl[hi].sum():+8.1f} AVG={pnl[hi].mean():+.3f}")
    print(f"  OPPOSED n={lo.sum():>4} SUM={pnl[lo].sum():+8.1f} AVG={pnl[lo].mean():+.3f}")
    for i, nm in enumerate(["T_raw", "T_within", "T_joint", "T_bsz", "T_ehr"]):
        print(f"  {nm:<12}= {obs[i]:+.3f} p={p[i]:.4f} CI95=[{ci[0,i]:+.2f},{ci[1,i]:+.2f}]")
    ev = all(obs[i] > 0 and p[i] < 0.05 for i in (1, 2, 3, 4))
    print(f"  P1 (T_raw): {'PASS' if obs[0] > 0 and p[0] < 0.05 else 'FAIL'} · "
          f"EVIDENCE (within∧joint∧bsz∧ehr): {'PASS' if ev else 'FAIL'} · "
          f"p_family={max(p[1], p[2], p[3], p[4]):.4f}")
    print(f"  [MC-4] binding legs = T_within,T_joint (bsz/ehr near-collinear: kill-gate "
          f"corr rjR+0.020 eh−0.028) · CONS SUM(OPPOSED)={pnl[lo].sum():+.1f} → "
          f"{'consistent' if pnl[lo].sum() < 0 else 'INCONSISTENT'}")

    print("\n═══ descriptive (MIXED/UNDEF unconditional [clean-note]) ═══")
    for st in ("MIXED", "UNDEF"):
        sub = [r for r in traded if ms[r["date"]]["ms_state"] == st]
        pp = np.array([fv(r, "pnl") for r in sub])
        print(f"  {st}: n={len(sub)} SUM={pp.sum():+.1f} AVG={pp.mean():+.3f}")

    print("\n═══ per-year within sign (PS) ═══")
    good = wgood = 0
    for y in sorted(np.unique(yr)):
        m = yr == y
        t = T(pnl, m & hi, m & lo) if (m & hi).any() and (m & lo).any() else np.nan
        s = np.isfinite(t) and t > 0
        good += s
        wgood += s and y in WINNERS
        print(f"  {y}: nA={int((m&hi).sum()):>3} nO={int((m&lo).sum()):>3} T={t:+7.3f} "
              f"[{'+' if s else '-'}]")
    print(f"  PS: {good}/9 (≥6) · winners {wgood}/4 (≥3) → "
          f"{'PASS' if good >= 6 and wgood >= 3 else 'FAIL'}")

    print("\n═══ P3 GATE skip-OPPOSED (deployable · [MC-3] hard-pin) ═══")

    def skip(r):
        return ms[r["date"]]["ms_state"] == "OPPOSED"   # MIXED/UNDEF/"" → not skipped (fail-open)

    P3 = gate_report(traded, skip, "skip-OPPOSED")
    print(f"\n═══ OUTCOME: evidence={'✓' if ev else '✗'} · P3={'✓' if P3 else '✗'} · "
          f"budget 9/40 ═══")


if __name__ == "__main__":
    main()
