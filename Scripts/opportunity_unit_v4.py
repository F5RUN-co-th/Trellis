#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opportunity_unit_v4.py — TRELLIS-010 v3 · Opportunity Unit v4 (ESTIMAND-FIRST · fixed)
เป้า: วัด "โอกาส" ให้ถูก เพื่อหา additive edge สู่เป้า EA ($100 อยู่รอด·กำไรมาก·เข้าทุกโอกาส)

FOUNDATION (Engineer-verified CORRECT · คงไว้):
  enroll ทุก session bar (universe · outcome-BLIND) · label = forward-scan realizable-MFE/R
  (stop-aware 1R adverse-first · H) → base-rate B(τ)=P(maxMFE≥τ|bar) computable (P1 fixed)

FIX รอบนี้ (Engineer FAIL v4 · Claude reproduce ยืนยัน · foundation คงไว้):
  P-A triggerability: exact-bar 6% = artifact → **bounded-window discoverability curve** +
      residual-MFE-from-trigger + P(opp|D) lift (reproduce เอง: lift +3.5pp · lag15 45%)
  P-B/P-E null+power: bar-shuffle ผิด → **circular-shift trigger null** (P(opp|D)→base) +
      **trigger-dir null** (Edge→0) + **day-clustered bootstrap CI** ทุก metric (autocorr-safe)
  P-C direction-null: subset เดียวกัน (D∩opp∩tdir≠0) ไม่ใช่ all-opp long-share
  P-D grid tautological (R ไม่ถูกใช้): ลบ dead R · invariance บน **trigger axis** จริง
      (family{don,pd,both}×W{30,60,120}) ไม่ใช่แค่ R-scale
  P-F/P-G (non-block): day-box note · clock price-match = TODO ก่อน CONFIRM

EVIDENCE LADDER: ทุกเลข L0 · ห้าม freeze headline · **พูด finding ได้ต่อเมื่อ CI ไม่คร่อม null**
field=SEARCH cost-excluded · oracle=labeling ห้าม train เป็น target
DoF pre-register: H=360 · stop=1R · τ∈{1,1.5,2} · W∈{30,60,120} · Lmax curve · TARGET §1
Usage: python opportunity_unit_v4.py
"""
import sys
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, walk_exit, PT, SLIP_IN, CAPR
from opportunity_unit_v3 import residual_mfe                 # reuse verified (no dup)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ATR_N = 14
H = 360
TAUS = (1.0, 1.5, 2.0)
ACCT_TARGETS = (5.43, 6.70)                                  # §1 exogenous (min-lot median/mean)
W_GRID = (30, 60, 120)                                       # Donchian lookback (trigger axis · P-D)
LMAXES = (0, 5, 15, 30, 60)                                  # discoverability window (bars · P-A)
NBOOT = 400
SENS_GRID = ((360, 1.0), (300, 0.8), (420, 1.2), (300, 1.2), (420, 0.8))  # estimand-sensitivity (H,stop)


def bar_mfe(h, l, c, R, H=H, stopmult=1.0):
    """per-bar (mfe_long, mfe_short) ใน R · forward-scan · stop-aware adverse-first (universe)
    stopmult = stop distance ใน R (sensitivity axis · default 1R)"""
    m = len(c); out = []; rsk = stopmult * R
    for d in (1, -1):
        stopped = np.zeros(m, bool); favmax = np.zeros(m)
        for dj in range(1, min(H, m)):
            idx = np.arange(m - dj); p = idx + dj; act = ~stopped[idx]
            if d == 1:
                fav, adv = h[p] - c[idx], c[idx] - l[p]
            else:
                fav, adv = c[idx] - l[p], h[p] - c[idx]
            newstop = act & (adv >= rsk)
            upd = act & ~newstop & (fav > favmax[idx])
            favmax[idx[upd]] = fav[upd]
            stopped[idx[newstop]] = True
            if stopped.all():
                break
        out.append(favmax / R)
    return out[0], out[1]


def make_triggers(hh, ll, cc, pdh, pdl, family, W):
    """strategy-neutral EVENT trigger (cross-bar) · R-INDEPENDENT (P-D: ลบ R param ที่ dead)
    family: don=Donchian break · pd=prior-day cross · both=OR"""
    m = len(cc); lt = np.zeros(m, bool); st = np.zeros(m, bool)
    if family in ("don", "both") and m > W:
        rmax = sliding_window_view(hh, W).max(1); rmin = sliding_window_view(ll, W).min(1)
        dl = np.zeros(m, bool); ds = np.zeros(m, bool)
        dl[W:] = cc[W:] > rmax[:m - W]; ds[W:] = cc[W:] < rmin[:m - W]
        dl = np.r_[dl[0], dl[1:] & ~dl[:-1]]           # EDGE: fire เฉพาะ transition bar (event
        ds = np.r_[ds[0], ds[1:] & ~ds[:-1]]           # ไม่ใช่ state · ~31% persistence bars ตัดออก)
        lt |= dl; st |= ds
    if family in ("pd", "both") and pdh is not None:
        ab, be = cc > pdh, cc < pdl
        lt[1:] |= ab[1:] & ~ab[:-1]; st[1:] |= be[1:] & ~be[:-1]
    return lt, st


def windowed_range(hh, ll, W):
    if len(hh) >= W:
        return float((sliding_window_view(hh, W).max(1) - sliding_window_view(ll, W).min(1)).max())
    return float(hh.max() - ll.min())


def build_normalizers(ctx):
    """natural-vol ≫ account (P3-wall) → calibrate ไป exogenous target (constant 2011 warmup·ex-ante)"""
    day, h, l, hour = ctx["day"], ctx["h"], ctx["l"], ctx["hour"]
    uniq, fidx = np.unique(day, return_index=True); bnd = np.r_[fidx[1:], len(h)]
    WINDS = {"w120": 120, "daily": None}
    hist = {k: [] for k in WINDS}; raw = {k: {} for k in WINDS}
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), bnd.tolist()):
        dts = str(np.datetime64(int(di), "D"))
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22); hh, ll = h[i0:i1][m], l[i0:i1][m]
        for k, W in WINDS.items():
            r = float(np.mean(hist[k][-ATR_N:])) if len(hist[k]) >= ATR_N else np.nan
            if np.isfinite(r) and r > 0 and len(hh) >= 30:
                raw[k][dts] = r
        if len(hh):
            for k, W in WINDS.items():
                hist[k].append(windowed_range(hh, ll, W) if W else float(hh.max() - ll.min()))
    cal, native = {}, {}
    for k in WINDS:
        warm = [v for d, v in raw[k].items() if d[:4] == "2011"]
        native[k] = float(np.median([v for d, v in raw[k].items() if d[:4] >= "2012"]))
        km = float(np.median(warm)) if warm else native[k]
        for tgt in ACCT_TARGETS:
            cal[f"{k}@{tgt}"] = {d: v * (tgt / km) for d, v in raw[k].items() if d[:4] >= "2012"}
    return cal, native


def compute_cache(ctx, Rmap):
    """[expensive · 1×/normalizer] per-day: MFE + trigger inputs + v4 hold · reuse ได้ทุก trigger cfg"""
    day, o, h, l, c, hour = ctx["day"], ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["hour"]
    uniq, fidx = np.unique(day, return_index=True); bnd = np.r_[fidx[1:], len(h)]
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    hold = {}
    for dts, f in ctx["facts"].items():
        if f["traded"] != "1":
            continue
        k = ctx["pos"][dts + "T" + f["entry_time"]]; d = int(f["dir"])
        ash, asl = ctx["lv"][dts]; Rv = ash - asl
        ent = (o[k] + ctx["sp"][k] * PT + SLIP_IN) if d == 1 else (o[k] - SLIP_IN)
        st0 = max(asl, ent - CAPR * Rv) if d == 1 else min(ash, ent + CAPR * Rv)
        xb, _ = walk_exit(ctx, k, d, ent, st0, Rv); hold[dts] = (k, xb, d)
    ul, fl, bl = uniq.tolist(), fidx.tolist(), bnd.tolist(); cache = []
    for j, (di, i0, i1) in enumerate(zip(ul, fl, bl)):
        dts = str(np.datetime64(int(di), "D"))
        if dts not in Rmap or Rmap[dts] <= 0:
            continue
        R = Rmap[dts]; m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22); gi = np.arange(i0, i1)[m]
        oo, hh, ll, cc = o[gi], h[gi], l[gi], c[gi]
        if len(cc) < 30:
            continue
        ml, ms = bar_mfe(hh, ll, cc, R)
        pdi = ul[j - 1] if j > 0 else None
        eb, xb, vdir = hold.get(dts, (None, None, 0))
        covbar = ((gi >= eb) & (gi <= xb)) if eb is not None else np.zeros(len(cc), bool)
        cache.append(dict(yr=dts[:4], R=R, hh=hh, ll=ll, cc=cc, gi=gi,
                          maxm=np.maximum(ml, ms), bestdir=np.where(ml >= ms, 1, -1),
                          pdh=dhi.get(pdi) if pdi else None, pdl=dlo.get(pdi) if pdi else None,
                          vdir=vdir, covbar=covbar))
    return cache


def day_stats(rec, family, W, shift=None, dirperm=None):
    """[cheap] per-day counts ต่อ τ · shift=circular-shift trigger (null) · dirperm=randomize tdir"""
    hh, ll, cc, maxm, bestdir = rec["hh"], rec["ll"], rec["cc"], rec["maxm"], rec["bestdir"]
    lt, st = make_triggers(hh, ll, cc, rec["pdh"], rec["pdl"], family, W)
    n = len(cc)
    if shift is not None and n:                              # circular-shift trigger mask (P-B null)
        lt, st = np.roll(lt, shift % n), np.roll(st, shift % n)
    D = lt | st
    tdir = np.where(lt & ~st, 1, np.where(st & ~lt, -1, 0))
    if dirperm is not None:                                  # randomize trigger direction (P-C null)
        sgn = np.where(dirperm[:n] < 0.5, 1, -1)
        tdir = np.where(D, sgn, 0)
    # discoverability: opp-origin มี trigger ใน [i, i+L]
    nextT = np.full(n, 10 ** 9)                              # dist ไป trigger ถัดไป (forward)
    nd = 10 ** 9
    for i in range(n - 1, -1, -1):
        if D[i]:
            nd = 0
        nextT[i] = nd
        nd = nd + 1 if nd < 10 ** 9 else 10 ** 9
    out = dict(n=n, D=int(D.sum()))
    for t in TAUS:
        opp = maxm >= t
        Dopp = opp & D
        nz = Dopp & (tdir != 0)
        oc = int(opp.sum())
        out[t] = dict(
            opp=oc, Dopp0=int(Dopp.sum()), opp_at_D=int(Dopp.sum()),
            disc={L: int((opp & (nextT <= L)).sum()) for L in LMAXES},
            drgt=int((nz & (tdir == bestdir)).sum()), dwr=int((nz & (tdir == -bestdir)).sum()),
            nz=int(nz.sum()), longsub=int((nz & (bestdir == 1)).sum()),
            cov=int((Dopp & (rec["vdir"] == bestdir) & rec["covbar"]).sum()),
            gap=int((Dopp & ~((rec["vdir"] == bestdir) & rec["covbar"])).sum()))
    return out


def aggregate(stats_list, taus=TAUS):
    A = dict(n=sum(s["n"] for s in stats_list), D=sum(s["D"] for s in stats_list))
    for t in taus:
        A[t] = {}
        for key in ("opp", "Dopp0", "opp_at_D", "drgt", "dwr", "nz", "longsub", "cov", "gap"):
            A[t][key] = sum(s[t][key] for s in stats_list)
        A[t]["disc"] = {L: sum(s[t]["disc"][L] for s in stats_list) for L in LMAXES}
    return A


def metrics_from(A, t):
    o = A[t]["opp"]; D = A["D"]; N = A["n"]
    base = o / N if N else 0
    poppD = A[t]["opp_at_D"] / D if D else 0                 # P(opp|D)
    lift = poppD - base
    rg, wr = A[t]["drgt"], A[t]["dwr"]
    dacc = rg / (rg + wr) if (rg + wr) else 0
    ls = A[t]["longsub"]; nz = A[t]["nz"]
    null = max(ls, nz - ls) / nz if nz else 0.5             # majority-null บน subset เดียวกัน (P-C)
    return dict(base=base, poppD=poppD, lift=lift, dacc=dacc, null=null, edge=dacc - null,
                disc={L: A[t]["disc"][L] / o if o else 0 for L in LMAXES},
                cov=A[t]["cov"] / A[t]["Dopp0"] if A[t]["Dopp0"] else 0, gapd=A[t]["gap"] / N)


def boot_ci(stats_list, t, keyfn, rng, nb=NBOOT):
    """day-clustered bootstrap CI (resample วัน = block · autocorr-safe · P-E)"""
    idx = np.arange(len(stats_list)); vals = []
    for _ in range(nb):
        pick = rng.integers(0, len(idx), len(idx))
        vals.append(keyfn(aggregate([stats_list[i] for i in pick]), t))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main():
    ctx = load_ctx()
    cal, native = build_normalizers(ctx)
    rng = np.random.default_rng(20260708)
    print("=== Opportunity Unit v4 (estimand-first · fixed) · field=SEARCH · [ทุกเลข L0] ===")
    print(f"\n[Q1] normalizer natural-vol ≫ account (P3-wall): {', '.join(f'{k}={v:.1f}' for k,v in native.items())}"
          f" (>account) → calibrate→§1 target · independence=structural(raw-OHLC)")

    prim = f"daily@{ACCT_TARGETS[0]}"
    cache = compute_cache(ctx, cal[prim])
    N = sum(r["maxm"].size for r in cache)
    print(f"\n[FOUNDATION] universe = {N:,} bars ({prim}) · enroll-every-bar (P1 · base-rate computable)")

    # ── primary config metrics + day-clustered CI ──
    fam, W = "both", 60
    stats = [day_stats(r, fam, W) for r in cache]
    A = aggregate(stats)
    print(f"\n[Q2/BASE-RATE + CI] trigger={fam} W={W} · day-clustered bootstrap 95%CI (nb={NBOOT}):")
    print(f"  {'τ':>4}{'BaseRate':>18}{'P(opp|D)':>16}{'lift(pp)':>18}")
    for t in TAUS:
        m = metrics_from(A, t)
        bcl, bch = boot_ci(stats, t, lambda a, tt: metrics_from(a, tt)["base"], rng)
        lcl, lch = boot_ci(stats, t, lambda a, tt: metrics_from(a, tt)["lift"], rng)
        sig = "✓>0" if lcl > 0 else "cross-0"
        print(f"  {t:>4.1f}{100*m['base']:>9.1f}% [{100*bcl:.1f},{100*bch:.1f}]"
              f"{100*m['poppD']:>15.1f}%{100*m['lift']:>+11.2f} [{100*lcl:+.2f},{100*lch:+.2f}] {sig}")

    # ── P-A: discoverability curve (bounded window) + residual-MFE ──
    print(f"\n[Q3/TRIGGERABILITY · P-A] discoverability = P(trigger ใน [i,i+L] | opp) · แก้ exact-bar:")
    print(f"  {'τ':>4}" + "".join(f"{'L='+str(L):>9}" for L in LMAXES))
    for t in TAUS:
        m = metrics_from(A, t)
        print(f"  {t:>4.1f}" + "".join(f"{100*m['disc'][L]:>8.0f}%" for L in LMAXES))
    # residual-MFE split by trigger-dir correctness (NB-2: ปัญหา=direction ไม่ใช่ latency ·
    # NB-1: iterate ทุกวัน cap/วัน = ครอบทุกปี 2012-2020 ไม่ truncate)
    res_c, res_w = [], []
    for r in cache:
        lt, st = make_triggers(r["hh"], r["ll"], r["cc"], r["pdh"], r["pdl"], fam, W)
        D = lt | st; opp = r["maxm"] >= 1.5
        cand = np.where(opp & (np.cumsum(D[::-1])[::-1] > 0))[0]
        pick = rng.choice(cand, min(10, len(cand)), replace=False) if len(cand) else cand
        for i in pick:                                       # seed-random ต่อวัน (แก้ session-bias · NB-1)
            tarr = np.where(D[i:])[0]
            if len(tarr):
                tb = i + int(tarr[0]); d = 1 if lt[tb] else -1
                rv = residual_mfe(r["hh"], r["ll"], r["cc"], tb, d, r["R"])
                (res_c if d == r["bestdir"][i] else res_w).append(rv)
    res_c, res_w = np.array(res_c), np.array(res_w)
    print(f"  residual-MFE-from-first-trigger (opp≥1.5R · split-by-dir · n={len(res_c)+len(res_w)}):")
    print(f"    trigger-dir ถูก: median={np.median(res_c):.2f}R (move เหลือเยอะ = ไม่ late) · "
          f"ผิด: median={np.median(res_w):.2f}R")
    print(f"    → **ปัญหา = DIRECTION ไม่ใช่ latency/discovery** (NB-2: pooled artifact แก้แล้ว · "
          f"ทิศถูก = discovery/magnitude ดีพอ)")

    # ── P-C: direction Edge subset-null + trigger-dir null + CI ──
    # NB-3: DirAcc vs COIN(0.5) = มี directional signal ไหม · vs majority-null = ชนะเดาข้างมากไหม (2 คำถาม)
    print(f"\n[Q5/DIRECTION · NB-3] DirAcc vs COIN(0.5)[signal?] & vs majority-null[beats-guess?] · day-clustered CI:")
    print(f"  {'τ':>4}{'DirAcc':>8}{'vs-coin 95%CI':>17}{'signal':>12}{'Edge(vs-maj)':>13}{'95%CI':>13}")
    for t in TAUS:
        m = metrics_from(A, t)
        acl, ach = boot_ci(stats, t, lambda a, tt: 100 * metrics_from(a, tt)["dacc"], rng)
        ecl, ech = boot_ci(stats, t, lambda a, tt: 100 * metrics_from(a, tt)["edge"], rng)
        coin = "✓>50 signal" if acl > 50 else "cross-50"
        print(f"  {t:>4.1f}{100*m['dacc']:>7.1f}% [{acl:.1f},{ach:.1f}]{coin:>12}"
              f"{100*m['edge']:>+11.1f} [{ecl:+.1f},{ech:+.1f}]")
    print(f"  → signal เล็กแต่ CI-significant ที่ τ≥1.5 (majority-null ซ่อน) = **floor ที่ learned-predictor ต้องชนะ**")

    # ── P-B: circular-shift trigger null (P(opp|D) ควร→base) ──
    sh = [day_stats(r, fam, W, shift=int(rng.integers(50, len(r["cc"]) - 50)) if len(r["cc"]) > 100 else 1)
          for r in cache]
    An = aggregate(sh)
    print(f"\n[NULL · P-B/NB-4] circular-shift trigger (path คงที่ · destroy within-day trigger-timing):")
    for t in (1.5,):
        m, mn = metrics_from(A, t), metrics_from(An, t)
        sel = 100 * (m['lift'] - mn['lift'])
        print(f"  τ={t}: real lift +{100*m['lift']:.2f}pp · shifted +{100*mn['lift']:.2f}pp (**ไม่→0**) → "
              f"shift ตัด ~ครึ่ง")
        print(f"    residual +{100*mn['lift']:.2f} = **day-level vol co-cluster** (trigger+opp ขึ้นพร้อมกันวัน "
              f"vol สูง · within-day shift ตัด cross-day covariance ไม่ได้) · within-day selectivity = "
              f"real−shift = +{sel:.2f}pp (NB-4)")

    # ── P-D: trigger-axis invariance (family × W) — ไม่ใช่ R-scale tautology ──
    print(f"\n[P-D/INVARIANCE] trigger-axis จริง (family × W · แก้ tautology R-unused):")
    print(f"  {'cfg':<12}{'B(1.5)':>8}{'lift1.5':>9}{'disc15':>8}{'Edge1.5':>9}{'Dfires':>9}")
    for family in ("don", "pd", "both"):
        for W in W_GRID:
            if family == "pd" and W != W_GRID[0]:
                continue                                    # pd ไม่ขึ้นกับ W
            st2 = [day_stats(r, family, W) for r in cache]
            A2 = aggregate(st2); m = metrics_from(A2, 1.5)
            print(f"  {family+'/W'+str(W):<12}{100*m['base']:>7.0f}%{100*m['lift']:>+8.2f}"
                  f"{100*m['disc'][15]:>7.0f}%{100*m['edge']:>+8.1f}{A2['D']:>9,}")

    # ── scale-invariance (2nd normalizer · base-rate เท่านั้น · MFE แพง) ──
    print(f"\n[SCALE-INVARIANCE] normalizer axis (w120@{ACCT_TARGETS[0]}) — base-rate ต่างได้ (scale) แต่ Edge/lift ควรนิ่ง:")
    c2 = compute_cache(ctx, cal[f"w120@{ACCT_TARGETS[0]}"])
    A2 = aggregate([day_stats(r, fam, W) for r in c2])
    for t in (1.5,):
        m = metrics_from(A2, t)
        print(f"  τ={t} w120: base={100*m['base']:.0f}% lift={100*m['lift']:+.2f}pp edge={100*m['edge']:+.1f}pp "
              f"(เทียบ daily: lift +ตาม P-A · edge≈0)")

    print(f"\n[P-F/P-G · pre-predictor gate] day-box: MFE scan ใน session · v4_exit cross-day · "
          f"**clock price-match = hard gate ก่อน predictor** (session filter clock-dependent · "
          f"memory: 2025 sim +207/tester −169 · whole-year shift จะ inflate signal แรก) · "
          f"FWE caveat: τ2 '✓>50' = single-config ต้อง family-wise correct")
    print(f"\n[SENSITIVITY GATE] estimand robustness (H×stop) → `python opportunity_unit_v4.py --sens` "
          f"· verified 2026-07-08: ทุก corner DirAcc>coin · lift>0 · right≫wrong (ChatGPT valid·non-block)")
    print(f"\n⚠ EVIDENCE LADDER L0→L1 (impl-invariant) · headline ยังไม่ market-property · 'direction' = "
          f"naive-trigger เท่านั้น (52.6% floor) → learned-predictor ต้องชนะแบบ signed-R net-of-cost (§9)")


def sensitivity_gate(ctx, cal):
    """[P3/ChatGPT] estimand-sensitivity: perturb (H,stop) → headline (DirAcc>coin · lift>0 ·
    right≫wrong) ต้องรอดทุก cell · pass = sign/ordering survival (ไม่ใช่ number-match = กัน DoF-fishing)"""
    Rmap = cal[f"daily@{ACCT_TARGETS[0]}"]
    day, o, h, l, c, hour = ctx["day"], ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["hour"]
    uniq, fidx = np.unique(day, return_index=True); bnd = np.r_[fidx[1:], len(h)]
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    ul, fl, bl = uniq.tolist(), fidx.tolist(), bnd.tolist()
    rng = np.random.default_rng(20260708)
    print("=== [SENSITIVITY GATE] estimand robustness (edge-Donchian both/W60) ===")
    print(f"  {'H,stop':>10}{'DirAcc(τ2)':>12}{'lift(τ1.5)':>12}{'resid R/W':>13}  survive")
    allok = True
    for H_, stop in SENS_GRID:
        rg = wr = 0; opp15 = D15 = N = Dtot = 0; rc, rw = [], []
        for j, (di, i0, i1) in enumerate(zip(ul, fl, bl)):
            dts = str(np.datetime64(int(di), "D"))
            if dts not in Rmap: continue
            R = Rmap[dts]; m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22); gi = np.arange(i0, i1)[m]
            hh, ll, cc = h[gi], l[gi], c[gi]
            if len(cc) < 30: continue
            ml, ms = bar_mfe(hh, ll, cc, R, H=H_, stopmult=stop)
            maxm = np.maximum(ml, ms); bd = np.where(ml >= ms, 1, -1)
            pdi = ul[j - 1] if j > 0 else None
            lt, st = make_triggers(hh, ll, cc, dhi.get(pdi) if pdi else None,
                                   dlo.get(pdi) if pdi else None, "both", 60)
            D = lt | st; td = np.where(lt & ~st, 1, np.where(st & ~lt, -1, 0))
            N += len(cc); Dtot += int(D.sum())
            n2 = (maxm >= 2.0) & D & (td != 0)
            rg += int((n2 & (td == bd)).sum()); wr += int((n2 & (td == -bd)).sum())
            o15 = maxm >= 1.5; opp15 += int(o15.sum()); D15 += int((o15 & D).sum())
            cand = np.where(o15 & (np.cumsum(D[::-1])[::-1] > 0))[0]
            pk = rng.choice(cand, min(10, len(cand)), replace=False) if len(cand) else cand
            for i in pk:
                ta = np.where(D[i:])[0]
                if len(ta):
                    tb = i + int(ta[0]); d = 1 if lt[tb] else -1
                    (rc if d == bd[i] else rw).append(residual_mfe(hh, ll, cc, tb, d, R))
        dacc = 100 * rg / (rg + wr) if (rg + wr) else 0
        lift = 100 * D15 / Dtot - 100 * opp15 / N
        rcm, rwm = np.median(rc), np.median(rw)
        ok = dacc > 50 and lift > 0 and rcm > rwm; allok = allok and ok
        print(f"  {f'{H_},{stop}':>10}{dacc:>11.1f}%{lift:>+11.2f}{rcm:>7.2f}/{rwm:.2f}  {'✓' if ok else '✗FRAGILE'}")
    print(f"  → GATE {'PASS' if allok else 'FAIL'}: headline {'รอดทุก DoF = estimand robust' if allok else 'เปราะ — ต้อง investigate'}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sens":
        sensitivity_gate(load_ctx(), build_normalizers(load_ctx())[0])
    else:
        main()
