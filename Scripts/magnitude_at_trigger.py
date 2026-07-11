#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
magnitude_at_trigger.py — TRELLIS-010 · CLAIM-0014: at-trigger magnitude rank บน realizable population
[design v3: Engineer PASS (3 รอบ) · Win approve · ปิด dilution ของ CLAIM-0013]

คำถาม: GBM-straddle forecast **ณ trigger bar ของ trade จริง** (ไม่ใช่ day-mean cross-event) rank
realizable trades (both/W60 first-event · วัน v4-missed · population frozen จาก opportunity_validation) ได้ไหม

PRE-REGISTERED:
  โมเดล: GBM (gate_c_wf.gbm params) train expanding-WF บน v1-events straddle(rl+rs · Rmap-R units)
  · predict ที่ trade trigger bar (join (day, session-bar-i) — meta ของ v1 append i แล้ว · positional-safe)
  SEED-1: ทุก verdict ต้อง seed-robust — รัน 9 seeds (มาตรฐาน CLAIM-0010) บน PRIMARY ทั้งคู่
    PASS = boot-CI>0 ครบ 9/9 · FAIL-robust = 0/9 · ผสม = FRAGILE → investigate (ห้าม supersede)
  Metrics (หน่วย pin — TRAP-2): primary-A Spearman(pred, raw|pnl|) [เทียบตรง CLAIM-0013]
    · primary-B Spearman(pred, realized straddle ที่ trade bar = rl+rs ของ event ที่ join · หน่วยเดียวกับ pred)
    · secondary Spearman(pred, |pnl|/Rmap) [ประกาศ: Rmap = daily@5.43 ตัวเดียวกับ target]
  Actionability gate เดียว (MISS-1): top-20% mean signed pnl boot-CI-low > 0 · {100,50,10} = display เท่านั้น
    + monotonicity ของ curve = corroboration (ไม่ตัดสิน) · top-20 null = "not-selectable at this power"
  NULL: shuffle pred within test-year block · real > null 97.5pct (รายงานที่ทุก seed)
  CONTROL (ไม่นับ family): day-mean pred (วิธี CLAIM-0013) บน subset joined เดียวกัน — attribution
    at-trigger vs population-shift · ถ้า control เปลี่ยน sign/ผ่านบน subset = POPULATION-CONFOUNDED (ห้ามสรุป)
  Verdict tree 5 branch (อ่านคู่ control เสมอ): (1) B ตก [control ยืน] → mag ไม่ transfer at-trigger →
    supersede 0013 (วิธีคมกว่า/population แคบกว่า i≥240 · เช้ายังไม่เทส) (2) B ผ่าน + A ตก → Direction/exit
    กลืน magnitude (3) B ตก + A ผ่าน → ANOMALY investigate ห้าม supersede (4) ผ่านคู่ + top20 ไม่บวก →
    ranks-not-selectable (5) ผ่านคู่ + top20 CI+ → realizable selection (SEARCH-provisional)
  Population 3-count: trades 759 → i≥240 eligible (รายงาน hour-dist ที่หลุด) → joined (TEST_YEARS 2015-20)
field=SIM-SEARCH · lockbox/guard ไม่แตะ · ทุกเลขจาก stdout · family +1 entry (CLAIM-0014)
Usage: python magnitude_at_trigger.py
"""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx
from opportunity_validation import build_days, first_event, trig_trade, PRIMARY
from opportunity_unit_v4 import make_triggers, build_normalizers, ACCT_TARGETS
from direction_predictor_v1 import build
from gate_c_wf import gbm, TEST_YEARS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEEDS = (20260708, 1, 2, 42, 123, 999, 99999, 20260709, 7)   # มาตรฐาน CLAIM-0010
NBOOT = 1000
NPERM = 1000
QGATE = 20                                                    # single actionability gate (MISS-1)
QDISP = (100, 50, 20, 10)
MINBAR = 240                                                  # v1 feature guard (session-relative)


def boot_stat(fn, args, rng, nb=NBOOT):
    n = len(args[0])
    vals = []
    for _ in range(nb):
        pick = rng.integers(0, n, n)
        vals.append(fn(*[a[pick] for a in args]))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def sp(a, b):
    return spearmanr(a, b).correlation


def main():
    rng = np.random.default_rng(20260711)
    ctx = load_ctx()
    days = build_days(ctx)
    fam, W = PRIMARY

    # ── trades (frozen population จาก opportunity_validation) ──
    trades = []
    for dd in days:
        if not dd["missed"]:
            continue
        lt, st = make_triggers(dd["hh"], dd["ll"], dd["cc"], dd["pdh"], dd["pdl"], fam, W)
        k, d = first_event(lt, st)
        if k is None:
            continue
        pnl = trig_trade(ctx, dd["iend"], int(dd["gi"][k]), d, dd["R"])
        if np.isfinite(pnl):
            trades.append(dict(dts=dd["dts"], yr=int(dd["yr"]), k=k, pnl=pnl,
                               hr=int(ctx["hour"][dd["gi"][k]])))
    n1 = len(trades)

    # ── 3-count + hour-distribution ของที่หลุด i<240 ──
    elig = [t for t in trades if t["k"] >= MINBAR]
    drop = [t for t in trades if t["k"] < MINBAR]
    hrs, cnt = np.unique([t["hr"] for t in drop], return_counts=True)
    print("=== magnitude_at_trigger · CLAIM-0014 · field=SIM-SEARCH · lockbox/guard untouched ===")
    print(f"[3-COUNT] trades={n1} → i≥{MINBAR} eligible={len(elig)} (dropped {len(drop)} · "
          f"hour-dist: {dict(zip(hrs.tolist(), cnt.tolist()))})")

    # ── v1 events + join map ──
    X, meta = build(ctx)
    yrs_m = np.array([int(m[0]) for m in meta])
    strad_m = np.array([m[3] + m[4] for m in meta])
    uniq = np.unique(ctx["day"])
    j2d = {j: str(np.datetime64(int(uniq[j]), "D")) for j in {m[1] for m in meta}}
    ev = {(j2d[m[1]], m[5]): r for r, m in enumerate(meta)}
    Rmap = build_normalizers(ctx)[0][f"daily@{ACCT_TARGETS[0]}"]

    join = [(t, ev[(t["dts"], t["k"])]) for t in elig
            if t["yr"] in TEST_YEARS and (t["dts"], t["k"]) in ev]
    n3 = len(join)
    print(f"[JOIN] eligible∧TEST_YEARS∧v1-event = {n3} trades")
    if n3 < 30:
        print("✗ n<30 — inconclusive · STOP")
        return
    pnl = np.array([t["pnl"] for t, _ in join])
    apnl = np.abs(pnl)
    strad_t = np.array([strad_m[r] for _, r in join])          # realized straddle ณ trade bar (Rmap units)
    rnorm = np.array([Rmap[t["dts"]] for t, _ in join])
    yr_t = np.array([t["yr"] for t, _ in join])
    rows = np.array([r for _, r in join])

    # ── SEED-1: WF predictions ต่อ seed → metrics ต่อ seed ──
    print(f"\n[PRIMARY per-seed (9 seeds · SEED-1: verdict ต้อง seed-robust)]")
    print(f"  {'seed':>9}{'A=Sp(pred,|pnl|)':>20}{'CI':>20}{'B=Sp(pred,strad)':>20}{'CI':>20}"
          f"{'nullA97.5':>11}{'nullB97.5':>11}{'top20':>9}{'top20CIlo':>11}")
    passA = passB = passT = 0
    A_list, B_list = [], []
    for s in SEEDS:
        pred_all = np.full(len(meta), np.nan)
        for Y in TEST_YEARS:
            tr, te = yrs_m < Y, yrs_m == Y
            if tr.sum() < 1000 or te.sum() < 100:
                continue
            m = gbm(); m.set_params(random_state=s)
            m.fit(X[tr], strad_m[tr])
            pred_all[te] = m.predict(X[te])
        pred = pred_all[rows]
        ok = np.isfinite(pred)
        p, ap, st_, yt, pn, rn = pred[ok], apnl[ok], strad_t[ok], yr_t[ok], pnl[ok], rnorm[ok]
        A = sp(p, ap); B = sp(p, st_)
        A_list.append(A); B_list.append(B)
        Alo, Ahi = boot_stat(sp, (p, ap), rng)
        Blo, Bhi = boot_stat(sp, (p, st_), rng)
        # null: shuffle pred within test-year block
        nullA, nullB = [], []
        for _ in range(NPERM):
            ps = p.copy()
            for Y in np.unique(yt):
                mY = yt == Y
                ps[mY] = ps[mY][rng.permutation(mY.sum())]
            nullA.append(sp(ps, ap)); nullB.append(sp(ps, st_))
        nA = float(np.percentile(nullA, 97.5)); nB = float(np.percentile(nullB, 97.5))
        # actionability gate เดียว: top-20%
        selg = p >= np.percentile(p, 100 - QGATE)
        tlo, thi = boot_stat(lambda x: x.mean(), (pn[selg],), rng)
        passA += Alo > 0 and A > nA
        passB += Blo > 0 and B > nB
        passT += tlo > 0
        print(f"  {s:>9}{A:>+13.3f}{'':>7}[{Alo:+.3f},{Ahi:+.3f}]{B:>+14.3f}{'':>6}[{Blo:+.3f},{Bhi:+.3f}]"
              f"{nA:>+11.3f}{nB:>+11.3f}{pn[selg].mean():>+9.2f}{tlo:>+11.2f}")
    print(f"  → seed-band: A CI>0∧>null = {passA}/9 · B = {passB}/9 · top{QGATE} CI+ = {passT}/9 · "
          f"A median={np.median(A_list):+.3f} · B median={np.median(B_list):+.3f}")

    # ── display curve (seed แรก · corroborating เท่านั้น) ──
    s0 = SEEDS[0]
    pred_all = np.full(len(meta), np.nan)
    for Y in TEST_YEARS:
        tr, te = yrs_m < Y, yrs_m == Y
        if tr.sum() < 1000 or te.sum() < 100:
            continue
        m = gbm(); m.set_params(random_state=s0)
        m.fit(X[tr], strad_m[tr]); pred_all[te] = m.predict(X[te])
    pred = pred_all[rows]; ok = np.isfinite(pred)
    p, pn = pred[ok], pnl[ok]
    print(f"\n[DISPLAY curve seed={s0} · corroborating ไม่ตัดสิน · monotonic?]")
    means = []
    for q in QDISP:
        sel = p >= np.percentile(p, 100 - q)
        lo, hi = boot_stat(lambda x: x.mean(), (pn[sel],), rng)
        means.append(pn[sel].mean())
        print(f"  top{q:>4}%: n={int(sel.sum()):>4} mean={pn[sel].mean():+.3f} CI[{lo:+.3f},{hi:+.3f}]")
    print(f"  monotonic(100→10) = {all(means[i] <= means[i+1] for i in range(len(means)-1))}")

    # ── secondary: |pnl|/Rmap (หน่วยเดียวกับ target · ประกาศ) ──
    slo, shi = boot_stat(sp, (p, np.abs(pn) / rnorm[ok]), rng)
    print(f"\n[SECONDARY] Spearman(pred, |pnl|/Rmap) = {sp(p, np.abs(pn)/rnorm[ok]):+.3f} CI[{slo:+.3f},{shi:+.3f}]")

    # ── CONTROL (ไม่นับ family): day-mean pred (วิธี CLAIM-0013) บน subset เดียวกัน ──
    daymean = {}
    for r, m in enumerate(meta):
        if np.isfinite(pred_all[r]):
            daymean.setdefault(j2d[m[1]], []).append(pred_all[r])
    dm = np.array([np.mean(daymean.get(t["dts"], [np.nan])) for (t, _), o in zip(join, ok) if o])
    okc = np.isfinite(dm)
    cA = sp(dm[okc], np.abs(pn[okc]))
    clo, chi = boot_stat(sp, (dm[okc], np.abs(pn[okc])), rng)
    print(f"[CONTROL · day-mean (วิธี CLAIM-0013) บน subset เดียวกัน] Spearman={cA:+.3f} CI[{clo:+.3f},{chi:+.3f}]"
          f" — เทียบ CLAIM-0013 เดิม −0.012 (full 512) · control ผ่าน/พลิก sign = POPULATION-CONFOUNDED")

    print(f"\n[VERDICT · pre-registered tree — อ่านคู่ control · PASS=9/9 · FAIL-robust=0/9 · ผสม=FRAGILE]")
    print(f"  A {passA}/9 · B {passB}/9 · top{QGATE} {passT}/9 → branch = ดู docstring tree · "
          f"SEARCH-provisional เสมอ (guard/lockbox ล็อก)")


if __name__ == "__main__":
    main()
