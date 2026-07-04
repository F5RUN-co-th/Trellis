#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_card6_tick.py — TRELLIS-010 Stage C · Card C7/H7 "Breakout participation" (budget 6/40)
ฉบับแก้ครบตาม Engineer review (PASS-with-changes): MANDATORY-1 วัดบน SIGNAL BAR j
(tickfeat v2 SHA 69170d93 — v1 มี within-bar lookahead ถูกทิ้ง) · MANDATORY-2 evidence
ใช้ joint cell-demean ตาม precedent C3 (additive T_adj → descriptive) · MANDATORY-3
bar-size confound control (rjR corr +0.203 disclosed → T_bsz cell-demean)

สนามวัด: SIM SEARCH (uncapped+catchup, h0_day_facts) — MED-1: ผลดี ≠ edge จนผ่าน
capped+real-tick confirm · คำเตือน Gate B (สื่อสารความคาดหวังตรง): static filter มัก
"แยกผ่าน T แต่ตก P3" — ค่าจริงของตัวแปรที่รอด = วัตถุดิบ conditional behavior ใน Stage D

═══ PRE-REGISTERED SPEC (freeze ก่อนรัน) ═══
ตัวแปร: rel_tick_sig = tick(signal bar j) / median(same minute-of-day, trailing 60
ok-days) — รู้ค่า ณ close ของ j ก่อน entry ที่ open ของ i → ไม่มี lookahead + P3
gate deployable จริง
Mechanism: Osler stop-cluster (T-STRONG): break จริง = stop-flow เร่ง → participation
ผิดปกติสูงที่บาร์ทะลุ · ทิศจาก orb-stocks-in-play (T-DIRECTIONAL — ห้ามใช้เลขเป็น prior)
BANDS (ค่าคงที่: 1.0 = definitional เท่า baseline ตัวเอง · 2.0 = double):
LOW < 1.0 · MID [1.0,2.0) · HIGH ≥ 2.0 — contrast T = mean(HIGH) − mean(LOW)
POPULATION: PRIMARY = traded ∧ ok ∧ prev_ok=1 ∧ rel_tick_sig finite (HIGH 502/LOW 193)
EVIDENCE (ทุกตัว >0 และ p<.05 ใต้ rotation null ทุก distinct rotation, one-tailed):
  T_within = demean pnl รายปี
  T_joint  = demean ภายใน cell rv-band(3) × range_exp-bin(2: <1/≥1) × year
             (คุมคู่ collinear rv↔rexp +0.43 — precedent C3)
  T_bsz    = demean ภายใน cell rjR-tercile × year (rjR = range_j/R — แยก
             "participation" ออกจาก "ขนาดบาร์ทะลุ")
  p_family = max(p_within, p_joint, p_bsz)
DESCRIPTIVE (ไม่ใช่ evidence): T_raw · T_adj additive 4 ชั้น (rv+slope+rexp+gap
published AVGs) · threshold sens LOW{0.8,1.0} HIGH{1.75,2.0,2.5} · T ราย entry-hour
tercile · rel_tick_asian · MID band
PREDICTIONS: P1 T_raw>0 p<.05 · EVIDENCE ทั้งสาม · CONS SUM(LOW)<0 [non-evidence] ·
PS sign ≥6/9 + winners ≥3/4 · P3 gate skip-LOW ครบ §0 (fail-open) — deployable
OUTCOME MATRIX (แบบ card #2): evidence✓∧P3✓ → candidate → confirm stage ·
evidence✓∧P3✗ → คาดไว้แล้ว (วัตถุดิบ Stage D) · evidence✗ → falsified บันทึก ·
T<0 = FAIL one-tailed ห้าม flip · budget → 6/40
Integrity: kit regression + SHA chain (features + tickfeat v2) ก่อนคำนวณ
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
TICK = DIR / "h0_tickfeat_2012_2020.csv"
TICK_SHA = DIR / "h0_tickfeat_2012_2020.sha256"
RV_AVG = {"B1": 0.539, "B2": -0.591, "B3": 1.291}
SP_AVG = {"UP": -0.352, "FLAT": 0.996, "DN": 0.564}
RE_AVG = {"CON": 0.695, "EXP": 0.037}          # C3 published AVG/trade
GA_AVG = {"LARGE": 1.060, "SMALL": 0.210}      # C4 published
CUT_LO, CUT_HI = 1.0, 2.0


def main():
    sha = hashlib.sha256(TICK.read_bytes()).hexdigest()
    assert sha == TICK_SHA.read_text(encoding="utf-8").split()[0], "tickfeat firewall broken"
    assert sha.startswith("69170d93"), "ต้องเป็น v2 (signal bar) เท่านั้น — v1 โมฆะ"
    rows, traded = load_facts()
    regression_card1(rows)
    with open(TICK, encoding="utf-8") as f:
        tick = {r["date"]: r for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#"))}

    prim = [r for r in rows if r["traded"] == "1" and r["status"] == "ok"
            and r["prev_ok"] == "1"
            and tick[r["date"]]["rel_tick_sig"] != ""]
    prim.sort(key=lambda r: r["date"])
    v = np.array([float(tick[r["date"]]["rel_tick_sig"]) for r in prim])
    rjr = np.array([fv(tick[r["date"]], "rjR") for r in prim])
    pnl = np.array([fv(r, "pnl") for r in prim])
    yr = np.array([r["date"][:4] for r in prim])
    rv = np.array([fv(r, "rv_pct250") for r in prim])
    sp = np.array([fv(r, "slope_pct250") for r in prim])
    re_ = np.array([fv(r, "range_exp") for r in prim])
    og = np.array([fv(r, "overnight_gap") for r in prim])
    pr = np.array([fv(r, "prev_range") for r in prim])
    gr = np.abs(og) / np.where(pr > 0, pr, np.nan)
    eh = np.array([int(r["entry_time"][:2]) + int(r["entry_time"][3:5]) / 60
                   for r in prim])

    rvb = np.where(rv < RLO, "B1", np.where(rv >= RHI, "B3", "B2"))
    spb = np.where(sp < RLO, "DN", np.where(sp >= RHI, "UP", "FLAT"))
    reb = np.where(re_ < 1.0, "CON", "EXP")
    gab = np.where(gr >= 0.05, "LARGE", "SMALL")
    resid = year_demean(pnl, yr)
    # T_joint cells: rv×rexp×year (MANDATORY-2)
    cellj = np.array([f"{a}|{b}|{c}" for a, b, c in zip(rvb, reb, yr)])
    cmj = {c: pnl[cellj == c].mean() for c in np.unique(cellj)}
    jres = pnl - np.array([cmj[c] for c in cellj])
    # T_bsz cells: rjR-tercile×year (MANDATORY-3) — tercile cut จาก PRIMARY (control dim)
    q1, q2 = np.nanpercentile(rjr, [100 / 3, 200 / 3])
    bszb = np.where(rjr < q1, "S", np.where(rjr >= q2, "L", "M"))
    cellb = np.array([f"{a}|{c}" for a, c in zip(bszb, yr)])
    cmb = {c: pnl[cellb == c].mean() for c in np.unique(cellb)}
    bres = pnl - np.array([cmb[c] for c in cellb])
    print(f"PRIMARY n={len(prim)} · rjR tercile cuts {q1:.3f}/{q2:.3f} · "
          f"corr(rel,rjR)={np.corrcoef(v[np.isfinite(rjr)], rjr[np.isfinite(rjr)])[0,1]:+.3f}")

    def groups(vals):
        return vals >= CUT_HI, vals < CUT_LO

    def T(arr, hi, lo):
        return arr[hi].mean() - arr[lo].mean()

    def imp_T(hi, lo):
        s = sum((np.mean(rvb[hi] == b) - np.mean(rvb[lo] == b)) * RV_AVG[b] for b in RV_AVG)
        s += sum((np.mean(spb[hi] == b) - np.mean(spb[lo] == b)) * SP_AVG[b] for b in SP_AVG)
        s += sum((np.mean(reb[hi] == b) - np.mean(reb[lo] == b)) * RE_AVG[b] for b in RE_AVG)
        s += sum((np.mean(gab[hi] == b) - np.mean(gab[lo] == b)) * GA_AVG[b] for b in GA_AVG)
        return s

    def stat(vals):
        hi, lo = groups(vals)
        if not (hi.any() and lo.any()):
            return np.array([np.nan] * 5)
        return np.array([T(pnl, hi, lo), T(resid, hi, lo), T(jres, hi, lo),
                         T(bres, hi, lo), T(pnl, hi, lo) - imp_T(hi, lo)])

    obs, p, nrot = rotation_pvalues(v, stat)
    ci = bootstrap_ci(v, [pnl, resid, jres, bres],
                      lambda vv, a, b, c, d: (np.array([T(a, *groups(vv)), T(b, *groups(vv)),
                                                        T(c, *groups(vv)), T(d, *groups(vv))])
                                              if groups(vv)[0].any() and groups(vv)[1].any()
                                              else np.array([np.nan] * 4)))
    hi, lo = groups(v)
    mid = ~(hi | lo)
    print(f"\n═══ EVIDENCE (PRIMARY · rotations={nrot}) ═══")
    for lab, m in (("HIGH", hi), ("MID ", mid), ("LOW ", lo)):
        print(f"  {lab} n={m.sum():>4} SUM={pnl[m].sum():+8.1f} AVG={pnl[m].mean():+.3f}")
    names = ["T_raw", "T_within", "T_joint", "T_bsz", "T_adj(desc)"]
    for i, nm in enumerate(names):
        ci_txt = f" CI95=[{ci[0, i]:+.2f},{ci[1, i]:+.2f}]" if i < 4 else ""
        print(f"  {nm:<12}= {obs[i]:+.3f} p={p[i]:.4f}{ci_txt}")
    ev = all(obs[i] > 0 and p[i] < 0.05 for i in (1, 2, 3))
    print(f"  P1 (T_raw): {'PASS' if obs[0] > 0 and p[0] < 0.05 else 'FAIL'} · "
          f"EVIDENCE (within∧joint∧bsz): {'PASS' if ev else 'FAIL'} · "
          f"p_family={max(p[1], p[2], p[3]):.4f}")
    print(f"  CONS SUM(LOW)={pnl[lo].sum():+.1f} → "
          f"{'consistent' if pnl[lo].sum() < 0 else 'INCONSISTENT'} [non-evidence]")

    print("\n═══ descriptive ═══")
    for cl, ch in ((0.8, 1.75), (0.8, 2.5), (1.0, 1.75), (1.0, 2.5)):
        h2, l2 = v >= ch, v < cl
        print(f"  sens LOW<{cl}/HIGH≥{ch}: T_raw={T(pnl, h2, l2):+.3f} "
              f"(n={l2.sum()}/{h2.sum()})")
    for lab, m in (("eh<11", eh < 11), ("11-15", (eh >= 11) & (eh < 15)), ("≥15", eh >= 15)):
        h2, l2 = hi & m, lo & m
        t = T(pnl, h2, l2) if h2.any() and l2.any() else np.nan
        print(f"  entry-hour {lab}: T={t:+.3f} (n={l2.sum()}/{h2.sum()})")

    print("\n═══ per-year within sign (PS) ═══")
    good = wgood = 0
    for y in sorted(np.unique(yr)):
        m = yr == y
        t = T(pnl, m & hi, m & lo) if (m & hi).any() and (m & lo).any() else np.nan
        s = np.isfinite(t) and t > 0
        good += s
        wgood += s and y in WINNERS
        print(f"  {y}: nH={int((m&hi).sum()):>3} nL={int((m&lo).sum()):>3} T={t:+7.3f} "
              f"[{'+' if s else '-'}]")
    print(f"  PS: {good}/9 (≥6) · winners {wgood}/4 (≥3) → "
          f"{'PASS' if good >= 6 and wgood >= 3 else 'FAIL'}")

    print("\n═══ P3 GATE skip-LOW (deployable: รู้ค่า ณ close ของ j ก่อน entry) ═══")

    def skip(r):
        s = tick[r["date"]]["rel_tick_sig"]
        return s != "" and float(s) < CUT_LO

    P3 = gate_report(traded, skip, "skip-LOW")
    print(f"\n═══ OUTCOME: evidence={'✓' if ev else '✗'} · P3={'✓' if P3 else '✗'} · "
          f"budget 6/40 ═══")


if __name__ == "__main__":
    main()
