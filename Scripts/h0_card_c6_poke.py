#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_card_c6_poke.py — TRELLIS-010 Stage C · Card C6/H6 "Pre-break poke" (budget 7/40)
ฉบับผนวก Engineer mandatory ครบ: C6-a (ผลบวกโผล่เฉพาะ 30-recency descriptive ขณะ
60-primary FAIL ≠ pass — เป็น card ใหม่ +budget) · C6-b (eh-tercile cuts fix ex-ante
9.48/12.52 จาก PRIMARY) · C6-d (SHA assert + kit regression) · C6-e (rel_tick-tercile
stratified = required-report) · C6-c (full-window avail≥60 replication sensitivity)

MECHANISM (Osler T-STRONG ×2): TP orders กระจุก*ที่* level → poke (เจาะแล้วปิดกลับเข้า
ภายใน 60 นาทีก่อน signal close) = reversal flow ทำงานอยู่ → break ตามมาเจอ flow ต้าน
⭐ PREDICTION: T = mean(pnl|CLEAN) − mean(pnl|POKED) > 0 · one-tailed · T<0 = FAIL
ห้าม flip (sign-flip risk disclose แล้ว: reading ตรงข้าม "level-tested-แนวแข็ง" มีจริง)
PRIMARY: traded ∧ ok ∧ prev_ok=1 ∧ avail_bars ≥ 1 (n=1,324 · POKED/CLEAN ~547/777)
EVIDENCE: T_within ∧ T_joint (rv×rexp×year) ∧ T_ehr (eh-tercile 9.48/12.52 ×year)
ทุกตัว >0, p<.05 ใต้ rotation null · p_family = max
P3: gate skip-POKED — deployable (รู้ ณ close ของ j) · budget → 7/40 เมื่อรัน
สนามวัด SIM SEARCH (MED-1) · คาดการณ์ตรง Gate B: static filter อาจผ่าน T ตก P3
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
POKE = DIR / "h0_pokefeat_2012_2020.csv"
POKE_SHA = DIR / "h0_pokefeat_2012_2020.sha256"
TICK = DIR / "h0_tickfeat_2012_2020.csv"
RV_AVG = {"B1": 0.539, "B2": -0.591, "B3": 1.291}
SP_AVG = {"UP": -0.352, "FLAT": 0.996, "DN": 0.564}
RE_AVG = {"CON": 0.695, "EXP": 0.037}
GA_AVG = {"LARGE": 1.060, "SMALL": 0.210}
EH_CUT = (9.48, 12.52)                     # C6-b: fix ex-ante จาก PRIMARY


def main():
    sha = hashlib.sha256(POKE.read_bytes()).hexdigest()
    assert sha == POKE_SHA.read_text(encoding="utf-8").split()[0]
    assert sha.startswith("71054c06"), "ต้องเป็น pokefeat frozen v1 เท่านั้น (C6-d)"
    rows, traded = load_facts()
    regression_card1(rows)
    with open(POKE, encoding="utf-8") as f:
        poke = {r["date"]: r for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#"))}
    with open(TICK, encoding="utf-8") as f:
        tick = {r["date"]: r for r in csv.DictReader(
            ln for ln in f if not ln.startswith("#"))}

    prim = [r for r in rows if r["traded"] == "1" and r["status"] == "ok"
            and r["prev_ok"] == "1" and poke[r["date"]]["n_pokes"] != ""
            and int(poke[r["date"]]["avail_bars"]) >= 1]
    prim.sort(key=lambda r: r["date"])
    pk = np.array([int(poke[r["date"]]["poked"]) for r in prim])
    npk = np.array([int(poke[r["date"]]["n_pokes"]) for r in prim])
    n30 = np.array([int(poke[r["date"]]["n_pokes_30"]) for r in prim])
    av = np.array([int(poke[r["date"]]["avail_bars"]) for r in prim])
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
    rts = np.array([fv(tick[r["date"]], "rel_tick_sig") for r in prim])

    rvb = np.where(rv < RLO, "B1", np.where(rv >= RHI, "B3", "B2"))
    spb = np.where(sp < RLO, "DN", np.where(sp >= RHI, "UP", "FLAT"))
    reb = np.where(re_ < 1.0, "CON", "EXP")
    gab = np.where(gr >= 0.05, "LARGE", "SMALL")
    ehb = np.where(eh < EH_CUT[0], "E", np.where(eh >= EH_CUT[1], "L", "M"))
    resid = year_demean(pnl, yr)
    cj = np.array([f"{a}|{b}|{c}" for a, b, c in zip(rvb, reb, yr)])
    cmj = {c: pnl[cj == c].mean() for c in np.unique(cj)}
    jres = pnl - np.array([cmj[c] for c in cj])
    ce = np.array([f"{a}|{c}" for a, c in zip(ehb, yr)])
    cme = {c: pnl[ce == c].mean() for c in np.unique(ce)}
    eres = pnl - np.array([cme[c] for c in ce])
    print(f"PRIMARY n={len(prim)} · POKED={int(pk.sum())} CLEAN={int((1-pk).sum())}")

    def groups(vals):
        return vals == 0, vals == 1            # (CLEAN=hi ตาม prediction, POKED=lo)

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
                         T(eres, hi, lo), T(pnl, hi, lo) - imp_T(hi, lo)])

    obs, p, nrot = rotation_pvalues(pk, stat)
    ci = bootstrap_ci(pk, [pnl, resid, jres, eres],
                      lambda vv, a, b, c, d: (np.array([T(a, *groups(vv)), T(b, *groups(vv)),
                                                        T(c, *groups(vv)), T(d, *groups(vv))])
                                              if groups(vv)[0].any() and groups(vv)[1].any()
                                              else np.array([np.nan] * 4)))
    hi, lo = groups(pk)
    print(f"\n═══ EVIDENCE (rotations={nrot}) ═══")
    print(f"  CLEAN n={hi.sum():>4} SUM={pnl[hi].sum():+8.1f} AVG={pnl[hi].mean():+.3f}")
    print(f"  POKED n={lo.sum():>4} SUM={pnl[lo].sum():+8.1f} AVG={pnl[lo].mean():+.3f}")
    for i, nm in enumerate(["T_raw", "T_within", "T_joint", "T_ehr", "T_adj(desc)"]):
        ci_txt = f" CI95=[{ci[0, i]:+.2f},{ci[1, i]:+.2f}]" if i < 4 else ""
        print(f"  {nm:<12}= {obs[i]:+.3f} p={p[i]:.4f}{ci_txt}")
    ev = all(obs[i] > 0 and p[i] < 0.05 for i in (1, 2, 3))
    print(f"  P1 (T_raw): {'PASS' if obs[0] > 0 and p[0] < 0.05 else 'FAIL'} · "
          f"EVIDENCE (within∧joint∧ehr): {'PASS' if ev else 'FAIL'} · "
          f"p_family={max(p[1], p[2], p[3]):.4f}")
    print(f"  CONS SUM(POKED)={pnl[lo].sum():+.1f} → "
          f"{'consistent' if pnl[lo].sum() < 0 else 'INCONSISTENT'} [non-evidence]")

    print("\n═══ descriptive (C6-a/c/e + recency + dose) ═══")
    p30 = n30 >= 1
    print(f"  30-recency contrast: T_raw={T(pnl, p30 == 0, p30 == 1):+.3f} "
          f"[C6-a: บวกที่นี่ขณะ primary FAIL ≠ pass — card ใหม่เท่านั้น]")
    m60 = av >= 60
    h6, l6 = hi & m60, lo & m60
    print(f"  full-window (avail≥60, n={int(m60.sum())}): "
          f"T_raw={T(pnl, h6, l6):+.3f} T_within={T(resid, h6, l6):+.3f} [C6-c]")
    for lab, m in (("0", npk == 0), ("1", npk == 1), ("2+", npk >= 2)):
        print(f"  dose n_pokes={lab}: n={int(m.sum()):>4} AVG={pnl[m].mean():+.3f}")
    fr = np.isfinite(rts)
    tq1, tq2 = np.nanpercentile(rts, [100 / 3, 200 / 3])
    for lab, m in (("lowT", rts < tq1), ("midT", (rts >= tq1) & (rts < tq2)),
                   ("highT", rts >= tq2)):
        mm = m & fr
        t = T(pnl, hi & mm, lo & mm) if (hi & mm).any() and (lo & mm).any() else np.nan
        print(f"  rel_tick {lab}: T={t:+.3f} (n={int((lo&mm).sum())}/{int((hi&mm).sum())}) "
              f"[C6-e required]")

    print("\n═══ per-year within sign (PS) ═══")
    good = wgood = 0
    for y in sorted(np.unique(yr)):
        m = yr == y
        t = T(pnl, m & hi, m & lo) if (m & hi).any() and (m & lo).any() else np.nan
        s = np.isfinite(t) and t > 0
        good += s
        wgood += s and y in WINNERS
        print(f"  {y}: nC={int((m&hi).sum()):>3} nP={int((m&lo).sum()):>3} T={t:+7.3f} "
              f"[{'+' if s else '-'}]")
    print(f"  PS: {good}/9 (≥6) · winners {wgood}/4 (≥3) → "
          f"{'PASS' if good >= 6 and wgood >= 3 else 'FAIL'}")

    print("\n═══ P3 GATE skip-POKED (deployable) ═══")

    def skip(r):
        q = poke[r["date"]]
        return q["poked"] != "" and q["poked"] == "1"

    P3 = gate_report(traded, skip, "skip-POKED")
    print(f"\n═══ OUTCOME: evidence={'✓' if ev else '✗'} · P3={'✓' if P3 else '✗'} · "
          f"budget 7/40 ═══")


if __name__ == "__main__":
    main()
