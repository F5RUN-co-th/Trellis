#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opportunity_validation.py — TRELLIS-010 · validate CLAIM-0004 (Q-A) + magnitude-rank (Q-B · claim ใหม่)
[design: Win approve 2026-07-10 · Engineer PASS-with-changes D1-D6 + A-1(FWE) + INT-1..5]

Q-A — 3-population DECOMPOSITION ของ additive opportunity บนวัน v4-missed · field SIM-SEARCH 2012-2020:
  (a) ANCHOR    outcome-blind: ทุกวัน missed ที่ trigger ยิง — report-only (base-rate · ไม่มี pass/fail)
  (b) REALIZABLE edge-test: trigger-grid ex-ante 7 config (don/pd/both × W — Q3 frozen estimand CLAIM-0002)
      PASS ต่อ config (pre-registered): trade-boot CI-low(mean pnl · Bonferroni m=7) > 0
        ∧ ปีบวก ≥6/9 (ปีไม่มีเทรด = ไม่บวก) ∧ real > 97.5pct(circular-shift null)
      รายงานทั้ง grid = จ่าย FWE เต็ม (reframe §9 "FWE caveat บน trigger-grid") · ห้าม cherry-pick
      [ประหยัด compute — pre-registered: null รันเฉพาะ config ที่ CI95-low > 0 (config อื่นตกก่อนถึง null)]
  (c) CEILING   oracle-conditioned (day-oracle ≥2R — นิยามเดิม CLAIM-0004) — descriptor ห้ามเรียก edge
  (c)−(b) = discovery headroom ที่ยังล็อกหลัง direction/discovery bottleneck (INT-1)
Q-B — magnitude rank บน population (b) primary config both/W60 (INT-2 · realizable ไม่ใช่ ceiling):
  predicted-straddle GBM 19-feat expanding-WF (machinery เดิม gate_magnitude · TEST_YEARS 2015-20)
  → day-forecast → Spearman(pred, |pnl|/R) + top-half−bottom-half separation (boot CI)
  PASS (pre-registered): Spearman boot-CI > 0 ∧ separation CI-low > 0

R = ATR14 ของ daily range (เดียวกับ discovery_probe — ต่อเนื่องกับ n=31) · entry = close trigger bar + cost
exit = mirror discovery_probe.sim_day (stop 1R · trail arm 1R dist 0.75R · EOD 23:00/ศุกร์ 20:00) · 1 เทรด/วัน
lockbox 2024-26 + guard 2021-23 ไม่แตะ · ทุกเลข = stdout script นี้ · ผลบวก = SEARCH-provisional (เพดาน L1/L2)
Usage: python opportunity_validation.py
"""
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, PT, SLIP_IN, SLIP_STOP
from opportunity_unit_v4 import make_triggers
from discovery_probe import oracle_day, ATR_N, A_ARM, D_TRAIL, DIR
import csv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GRID = (("don", 30), ("don", 60), ("don", 120), ("pd", 30),
        ("both", 30), ("both", 60), ("both", 120))            # 7 config = FWE family (pd ไม่ขึ้นกับ W)
M_FWE = len(GRID)
ALPHA = 0.05
NBOOT = 3000                                                   # trade-boot (1 เทรด/วัน = day-clustered ในตัว)
NNULL = 60                                                     # circular-shift resamples (เฉพาะ config ผ่าน CI95)
PRIMARY = ("both", 60)                                         # config หลักของ Q-B (ตาม opportunity_unit_v4)
ORACLE_TAU = 2.0                                               # day-oracle ≥2R = นิยาม opp เดิมของ CLAIM-0004
SEED = 20260710
YEARS = [str(y) for y in range(2012, 2021)]


def trig_trade(ctx, iend, q0, d, R):
    """เข้า ณ close ของ trigger bar q0 ทิศ d · exit logic = mirror discovery_probe.sim_day
    (ต่างแค่จุดเข้า: event bar แทน close-threshold) · คืน pnl หรือ nan(eof)"""
    o, h, l, c, sp = ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["sp"]
    hour, dow = ctx["hour"], ctx["dow"]
    ent = (c[q0] + sp[q0] * PT + SLIP_IN) if d == 1 else (c[q0] - SLIP_IN)
    stop = ent - R if d == 1 else ent + R
    best = ent
    for q in range(q0 + 1, iend):
        if hour[q] >= (20 if dow[q] == 5 else 23):             # eod
            ex = c[q] if d == 1 else c[q] + sp[q] * PT
            return (ex - ent) * d
        hit = l[q] <= stop if d == 1 else h[q] >= stop
        if hit:
            px = (min(stop, o[q]) if d == 1 else max(stop, o[q])) - SLIP_STOP * d
            ex = px if d == 1 else px + sp[q] * PT
            return (ex - ent) * d
        best = max(best, c[q]) if d == 1 else min(best, c[q])
        if (best - ent) * d >= A_ARM * R:
            ns = best - D_TRAIL * R if d == 1 else best + D_TRAIL * R
            stop = max(stop, ns) if d == 1 else min(stop, ns)
    return np.nan


def first_event(lt, st, shift=None):
    """index ของ event แรกที่ tdir≠0 (shift = circular-shift null) · คืน (idx, dir) หรือ (None,0)"""
    n = len(lt)
    if shift is not None and n:
        lt, st = np.roll(lt, shift % n), np.roll(st, shift % n)
    ev = np.where((lt | st) & (lt != st))[0]
    for i in ev:
        if i < n - 2:                                          # ต้องมี bar ให้เดินต่อ
            return int(i), (1 if lt[i] else -1)
    return None, 0


def build_days(ctx):
    """per-day cache: session arrays + R(ATR14 daily-range เดิมของ probe) + prior-day levels + v4 + oracle"""
    day, h, l, hour = ctx["day"], ctx["h"], ctx["l"], ctx["hour"]
    v4day = {r["date"] for r in csv.DictReader(
        ln for ln in open(DIR / "h0_day_facts_2012_2020.csv", encoding="utf-8")
        if not ln.startswith("#")) if r["traded"] == "1"}
    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(h)]
    ul, fl, bl = uniq.tolist(), fidx.tolist(), bnd.tolist()
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dr_hist, days = [], []
    prev = None
    for j, (di, i0, i1) in enumerate(zip(ul, fl, bl)):
        dts = str(np.datetime64(int(di), "D"))
        R = float(np.mean(dr_hist[-ATR_N:])) if len(dr_hist) >= ATR_N else np.nan
        dr_hist.append(dhi[di] - dlo[di])
        if prev is None or dts[:4] < "2012" or not (np.isfinite(R) and R > 0):
            prev = di
            continue
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22)
        gi = np.arange(i0, i1)[m]
        if len(gi) < 30:
            prev = di
            continue
        orcR, odir = oracle_day(ctx, i0, i1, R)
        days.append(dict(dts=dts, yr=dts[:4], gi=gi, iend=i1, R=R,
                         hh=h[gi], ll=l[gi], cc=ctx["c"][gi],
                         pdh=dhi[prev], pdl=dlo[prev],
                         missed=dts not in v4day,
                         opp=bool(np.isfinite(orcR) and orcR >= ORACLE_TAU)))
        prev = di
    return days


def boot_ci(vals, rng, lo_pct, hi_pct, nb=NBOOT):
    v = np.asarray(vals)
    mm = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(nb)]
    return float(np.percentile(mm, lo_pct)), float(np.percentile(mm, hi_pct))


def run_config(ctx, days, fam, W):
    """(a)/(c) trades บนวัน missed · คืน list ของ dict(yr, pnl, opp) — 1 เทรด/วัน"""
    out = []
    for dd in days:
        if not dd["missed"]:
            continue
        lt, st = make_triggers(dd["hh"], dd["ll"], dd["cc"], dd["pdh"], dd["pdl"], fam, W)
        k, d = first_event(lt, st)
        if k is None:
            continue
        pnl = trig_trade(ctx, dd["iend"], int(dd["gi"][k]), d, dd["R"])
        if np.isfinite(pnl):
            out.append(dict(yr=dd["yr"], dts=dd["dts"], pnl=pnl, opp=dd["opp"]))
    return out


def null_means(ctx, days, fam, W, rng, nb=NNULL):
    """circular-shift null: shift trigger mask ต่อวัน → เทรดแรกจาก mask ที่ shift → mean ต่อ resample"""
    masks = []
    for dd in days:
        if not dd["missed"]:
            continue
        lt, st = make_triggers(dd["hh"], dd["ll"], dd["cc"], dd["pdh"], dd["pdl"], fam, W)
        masks.append((dd, lt, st))
    out = []
    for _ in range(nb):
        pn = []
        for dd, lt, st in masks:
            n = len(lt)
            k, d = first_event(lt, st, shift=int(rng.integers(1, n)) if n > 2 else 1)
            if k is None:
                continue
            pnl = trig_trade(ctx, dd["iend"], int(dd["gi"][k]), d, dd["R"])
            if np.isfinite(pnl):
                pn.append(pnl)
        if pn:
            out.append(float(np.mean(pn)))
    return np.array(out)


def report_pop(tag, pnl):
    p = np.array(pnl)
    print(f"    {tag}: n={len(p)} sum={p.sum():+8.1f} mean={p.mean():+.3f} WR={100 * (p > 0).mean():.1f}%")
    return p


def main():
    rng = np.random.default_rng(SEED)
    ctx = load_ctx()
    days = build_days(ctx)
    nmiss = sum(1 for d in days if d["missed"])
    print("=== opportunity_validation · CLAIM-0004 Q-A (base/realizable/ceiling) + Q-B (magnitude rank) ===")
    print(f"field=SIM-SEARCH 2012-2020 · days={len(days)} (v4-missed={nmiss}) · R=ATR14 daily-range (probe) · "
          f"1 trade/day · lockbox/guard untouched")
    print(f"pre-registered: (b) PASS = CI-low(Bonferroni m={M_FWE}) > 0 ∧ ปีบวก ≥6/9 ∧ real>null97.5 · "
          f"(a)=anchor report-only · (c)=ceiling descriptor")
    lo_b, hi_b = 100 * (ALPHA / M_FWE / 2), 100 * (1 - ALPHA / M_FWE / 2)

    results = {}
    print(f"\n[Q-A · GRID ทั้ง {M_FWE} config — จ่าย FWE เต็ม ไม่ cherry-pick]")
    for fam, W in GRID:
        trades = run_config(ctx, days, fam, W)
        p_all = np.array([t["pnl"] for t in trades])
        p_opp = np.array([t["pnl"] for t in trades if t["opp"]])
        ylist = {y: np.array([t["pnl"] for t in trades if t["yr"] == y]) for y in YEARS}
        ypos = sum(1 for y in YEARS if len(ylist[y]) and ylist[y].mean() > 0)
        ci95 = boot_ci(p_all, rng, 2.5, 97.5) if len(p_all) > 5 else (np.nan, np.nan)
        cib = boot_ci(p_all, rng, lo_b, hi_b) if len(p_all) > 5 else (np.nan, np.nan)
        results[(fam, W)] = dict(trades=trades, p_all=p_all, p_opp=p_opp, ypos=ypos,
                                 ci95=ci95, cib=cib)
        print(f"\n  ── {fam}/W{W} ──")
        report_pop("(a) anchor  all-missed-fired (outcome-blind)", p_all)
        print(f"        CI95=[{ci95[0]:+.3f},{ci95[1]:+.3f}] · CI-Bonf(m={M_FWE})=[{cib[0]:+.3f},{cib[1]:+.3f}] · "
              f"ปีบวก {ypos}/9")
        if len(p_opp):
            report_pop("(c) ceiling missed∧oracle-opp (≥2R · ห้ามเรียก edge)", p_opp)

    # ── null เฉพาะ config ที่ CI95-low > 0 (pre-registered gate ของ null) ──
    print(f"\n[Q-A · circular-shift NULL — เฉพาะ config ที่ CI95-low>0]")
    verdicts = {}
    for (fam, W), r in results.items():
        if not (len(r["p_all"]) > 5 and r["ci95"][0] > 0):
            verdicts[(fam, W)] = "FAIL (CI95 คร่อม/ลบ)"
            continue
        nm = null_means(ctx, days, fam, W, rng)
        thr = float(np.percentile(nm, 97.5)) if len(nm) else np.nan
        sep = r["p_all"].mean() > thr
        okb = r["cib"][0] > 0
        oky = r["ypos"] >= 6
        verdicts[(fam, W)] = ("PASS" if (okb and oky and sep) else
                              f"FAIL (Bonf{'✓' if okb else '✗'} ปี{'✓' if oky else '✗'} null{'✓' if sep else '✗'})")
        print(f"  {fam}/W{W}: real={r['p_all'].mean():+.3f} · null97.5={thr:+.3f} · "
              f"sep={'✓' if sep else '✗'} → {verdicts[(fam, W)]}")
    for k, v in verdicts.items():
        if "null" not in str(v) and "PASS" not in str(v):
            print(f"  {k[0]}/W{k[1]}: {v}")

    # ── decomposition summary (INT-1) บน primary ──
    rp = results[PRIMARY]
    a_mean = rp["p_all"].mean() if len(rp["p_all"]) else np.nan
    c_mean = rp["p_opp"].mean() if len(rp["p_opp"]) else np.nan
    b_pass = [k for k, v in verdicts.items() if v == "PASS"]
    print(f"\n[DECOMPOSITION · primary {PRIMARY[0]}/W{PRIMARY[1]}] "
          f"base(a)={a_mean:+.3f} · ceiling(c)={c_mean:+.3f} · realizable(b) configs PASS = "
          f"{b_pass if b_pass else 'ไม่มี — additive ยังเป็น ceiling-only'}")

    # ── Q-B: magnitude rank บน population (b) ของ primary (INT-2) ──
    print(f"\n[Q-B · magnitude rank บน realizable population (primary {PRIMARY[0]}/W{PRIMARY[1]}) · "
          f"GBM straddle expanding-WF (machinery gate_magnitude) · TEST_YEARS]")
    from direction_predictor_v1 import build
    from gate_c_wf import gbm, TEST_YEARS
    X, meta = build(ctx)
    yrs_m = np.array([int(m[0]) for m in meta])
    jd = np.array([m[1] for m in meta])
    strad = np.array([m[3] + m[4] for m in meta])
    uniq = np.unique(ctx["day"])
    j2d = {j: str(np.datetime64(int(uniq[j]), "D")) for j in np.unique(jd)}
    daypred = {}
    for Y in TEST_YEARS:
        tr, te = yrs_m < Y, yrs_m == Y
        if tr.sum() < 1000 or te.sum() < 100:
            continue
        mdl = gbm()
        mdl.fit(X[tr], strad[tr])
        pr = mdl.predict(X[te])
        for j in np.unique(jd[te]):
            # ⚠ BLUNT PROXY (Engineer 07-11): day-mean บน v1-events ≠ forecast ณ trigger bar จริง
            #   (dilution + cross-event) → ผล null = not-detected ไม่ใช่ falsification (CLAIM-0013)
            daypred[j2d[j]] = float(pr[jd[te] == j].mean())
    tb = [(daypred[t["dts"]], t["pnl"]) for t in rp["trades"] if t["dts"] in daypred]
    if len(tb) < 30:
        print(f"  ✗ join ได้ n={len(tb)} < 30 — ไม่พอตัดสิน (coverage TEST_YEARS/population) · Q-B inconclusive")
    else:
        pred = np.array([x[0] for x in tb])
        pnl = np.array([x[1] for x in tb])
        rho = spearmanr(pred, np.abs(pnl)).correlation
        rhos = [spearmanr(*map(lambda a: a[rng.integers(0, len(pred), len(pred))], (pred, np.abs(pnl)))).correlation
                for _ in range(1000)]
        rlo, rhi = np.percentile(rhos, 2.5), np.percentile(rhos, 97.5)
        top = pnl[pred >= np.median(pred)]
        bot = pnl[pred < np.median(pred)]
        diffs = [top[rng.integers(0, len(top), len(top))].mean() - bot[rng.integers(0, len(bot), len(bot))].mean()
                 for _ in range(1000)]
        dlo, dhi = np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)
        qb = (rlo > 0) and (dlo > 0)
        print(f"  n={len(tb)} (join {len(tb)}/{len(rp['trades'])} trades · TEST_YEARS 2015-20)")
        print(f"  Spearman(pred, |pnl|) = {rho:+.3f} CI[{rlo:+.3f},{rhi:+.3f}] {'✓>0' if rlo > 0 else 'คร่อม/ลบ'}")
        print(f"  top-half − bottom-half (signed pnl) = {top.mean() - bot.mean():+.3f} CI[{dlo:+.3f},{dhi:+.3f}] "
              f"{'✓>0' if dlo > 0 else 'คร่อม/ลบ'}")
        print(f"  Q-B pre-registered verdict: {'PASS — magnitude ranks realizable trades' if qb else 'FAIL/negative'}")

    print(f"\n[CLAIM OBJECT Q-A] observed=stdout ข้างบน · supported=ใต้ trigger-grid นี้ + R/exit นี้ + SEARCH เท่านั้น"
          f" · SEARCH-provisional (เพดาน L1/L2 · guard/lockbox ล็อก) · FWE จ่ายแล้ว m={M_FWE}")


if __name__ == "__main__":
    main()
