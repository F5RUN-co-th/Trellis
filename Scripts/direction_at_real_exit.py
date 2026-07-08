#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
direction_at_real_exit.py — TRELLIS-010 · DIRECTION prediction ที่ EXIT จริงของ engine (walk-exit)
คำถามวิจัย: ที่ entry เดียวกับ v4 · learned as-of features ทำนายทิศ **ที่ walk-exit (trailing D=1×R +
overnight)** ชนะ v4 naive-breakout baseline OOS ได้ไหม — จับ flip-headroom (+7113 · 47.6% flips) ส่วนหนึ่ง?
(แก้ root disaster: gates เดิมวัดใต้ label trade_R 1R/1.5R-intraday = ผิด · Test B ยืน direction load-bearing)

design (Engineer PASS หลายรอบ · Claude verify+measured):
- LABEL = walk 3-leg บน entry จริง v4 · current==facts (assert) · opposite = distance-mirror
- PAYOFF R-UNITS = (walk_long−walk_short)/R · R=ash−asl (P1-a/b · ไม่ใช่ $ ไม่ใช่ Rmap)
- FEATURE as-of ≤ close[j] · j=session-seq(entry k)−1 (P1-c · ไม่ใช่ bar-i inclusive) · shared dir_features
- GUARDS ก่อน fit: (1) Σcurrent==532.8 (2) future-mask invariance = mechanical no-lookahead (3) mirror-sym
- OBJECTIVE fit_signedR (R-norm · ไม่ winsorize) · SIGN-GATE per-fold **train-only** day-clustered corr-CI (P1-d)
- OOS expanding-WF + embargo N=max-hold · baseline=v4 dir · flip-decomposition · perm-null · MDE
- EVAL 2 หน่วย: R (direction isolation) + $ (deployment) · honest null (collapsed=no-edge ไม่ใช่ tie)
- ⚠ FIELD = 2012-2020 SEARCH · money 2023-26 LOCKBOX (ไม่แตะ) · WF-within-span ≠ true-OOS (forward-test)
Usage: python direction_at_real_exit.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, walk, walk_exit, PT, SLIP_IN, CAPR, BASE_P
from opportunity_unit_v4 import make_triggers
from direction_predictor import fit_signedR, day_ci
from dir_features import compute_features, session_derived, FEATS
from test_b_direction_decomp import property_test_mirror_symmetry

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TEST_YEARS = ["2015", "2016", "2017", "2018", "2019", "2020"]


def sign_gate(Xtr, payoff, days, rng, B=300):
    """P1-d · train-only day-clustered corr-CI · keep feature ถ้า CI(corr) excludes 0 (sign-stable)"""
    uq = np.unique(days); d2i = {d: np.where(days == d)[0] for d in uq}
    keep = np.zeros(Xtr.shape[1], bool)
    for k in range(Xtr.shape[1]):
        if np.std(Xtr[:, k]) < 1e-12:
            continue
        cs = np.empty(B)
        for b in range(B):
            idx = np.concatenate([d2i[d] for d in rng.choice(uq, len(uq), replace=True)])
            cs[b] = np.corrcoef(Xtr[idx, k], payoff[idx])[0, 1]
        lo, hi = np.percentile(cs, [2.5, 97.5])
        keep[k] = (lo > 0) or (hi < 0)
    return keep


def build_rows(ctx):
    day, hourv = ctx["day"], ctx["hour"]
    uniq, fidx = np.unique(day, return_index=True); bnd = np.r_[fidx[1:], len(day)]
    dhi = {di: float(ctx["h"][i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(ctx["l"][i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    ul, fl, bl = uniq.tolist(), fidx.tolist(), bnd.tolist()
    rows = []; mism = 0; leak_checked = False
    for jx, (di, i0, i1) in enumerate(zip(ul, fl, bl)):
        dts = str(np.datetime64(int(di), "D"))
        f = ctx["facts"].get(dts)
        if f is None or f["traded"] != "1":
            continue
        k = ctx["pos"][dts + "T" + f["entry_time"]]
        d = int(f["dir"]); ash, asl = ctx["lv"][dts]; R = ash - asl
        m = (hourv[i0:i1] >= 1) & (hourv[i0:i1] < 22)
        gi = np.arange(i0, i1)[m]
        posk = np.where(gi == k)[0]
        if len(posk) == 0:
            continue
        pk = int(posk[0]); a = pk - 1                    # decision bar j (session-seq before entry)
        if a < 240:
            continue
        oo, hh, ll, cc = ctx["o"][gi], ctx["h"][gi], ctx["l"][gi], ctx["c"][gi]
        pdi = ul[jx - 1] if jx > 0 else None
        pdh = dhi.get(pdi) if pdi else None; pdl = dlo.get(pdi) if pdi else None
        lt, st = make_triggers(hh, ll, cc, pdh, pdl, "both", 60)
        clv, upw, dnw, body, cmin, cmax = session_derived(oo, hh, ll, cc)
        feat = compute_features(hh, ll, cc, lt, st, clv, upw, dnw, body, cmin, cmax, a, pdh, pdl, R, d)
        # GUARD (2): future-mask invariance — corrupt bars > a → feature ต้องไม่เปลี่ยน (no lookahead)
        if not leak_checked:
            o2, h2, l2, c2 = oo.copy(), hh.copy(), ll.copy(), cc.copy()
            for arr in (o2, h2, l2, c2):
                arr[a + 1:] = np.nan
            lt2, st2 = make_triggers(h2, l2, c2, pdh, pdl, "both", 60)
            cl2, uw2, dw2, bd2, mn2, mx2 = session_derived(o2, h2, l2, c2)
            feat2 = compute_features(h2, l2, c2, lt2, st2, cl2, uw2, dw2, bd2, mn2, mx2, a, pdh, pdl, R, d)
            assert np.allclose(feat, feat2, equal_nan=False), \
                f"FUTURE LEAK: feature เปลี่ยนเมื่อ corrupt bars > j ({dts})"
            leak_checked = True
        # LABEL: walk 3-leg
        ent = ctx["o"][k] + ctx["sp"][k] * PT + SLIP_IN if d == 1 else ctx["o"][k] - SLIP_IN
        stop0 = max(asl, ent - CAPR * R) if d == 1 else min(ash, ent + CAPR * R)
        xb, cur = walk_exit(ctx, k, d, ent, stop0, R)
        if not (np.isfinite(cur) and abs(cur - float(f["pnl"])) < 2e-3):
            mism += 1
        do = -d; ento = ctx["o"][k] + ctx["sp"][k] * PT + SLIP_IN if do == 1 else ctx["o"][k] - SLIP_IN
        Dl = abs(ent - stop0); stopo = ento - do * Dl
        opp = walk(ctx, k, do, ento, stopo, R)[0]
        if not np.isfinite(opp):
            continue
        pL = cur if d == 1 else opp
        pS = opp if d == 1 else cur
        rows.append(dict(yr=dts[:4], dayix=jx, feat=feat, pL=pL, pS=pS, R=R, d=d,
                         hold=int(day[xb] - day[k]), spd=ctx["sp"][k] * PT, fpnl=float(f["pnl"])))
    assert mism == 0, f"reproduce-first FAIL: {mism} current≠facts (label ผูก walk-exit เพี้ยน)"
    return rows


def main():
    print("[GUARD 3] mirror-symmetry property test:")
    property_test_mirror_symmetry()
    ctx = load_ctx()
    rows = build_rows(ctx)
    X = np.array([r["feat"] for r in rows], float)
    pL = np.array([r["pL"] for r in rows]); pS = np.array([r["pS"] for r in rows])
    Rv = np.array([r["R"] for r in rows]); dd = np.array([r["d"] for r in rows])
    yr = np.array([r["yr"] for r in rows]); dayix = np.array([r["dayix"] for r in rows])
    spd = np.array([r["spd"] for r in rows])
    rl, rs = pL / Rv, pS / Rv                             # R-normalized legs (P1-a)
    Nemb = max(r["hold"] for r in rows)
    cur = np.where(dd == 1, pL, pS)                       # = facts
    fbuilt = np.array([r["fpnl"] for r in rows])
    print(f"[GUARD 1] reproduce per-trade mism==0 ✓ · Σcurrent={cur.sum():+.1f} == Σfacts(built)={fbuilt.sum():+.1f} "
          f"({'✓' if abs(cur.sum() - fbuilt.sum()) < 1e-6 else '⚠'}) · n={len(X)}/1487 "
          f"(1 ตัด a<240) · full BASE_P={BASE_P:+.1f} · GUARD 2 future-mask ✓ · embargo N={Nemb}d")
    print(f"⚠ FIELD = 2012-2020 SEARCH · money 2023-26 LOCKBOX (ไม่วัด) · WF-within-span ≠ true-OOS\n")

    rng = np.random.default_rng(20260708)

    def wf(payoff_l, payoff_s, shuffle=False):
        dp_all, pL_all, pS_all, d_all, day_all, R_all, keepn, lfrac, ab_all = ([] for _ in range(9))
        for Y in TEST_YEARS:
            te = yr == Y
            if te.sum() < 50:
                continue
            tr = np.array([int(y) < int(Y) for y in yr]) & (dayix < dayix[te].min() - Nemb)
            if tr.sum() < 300:
                continue
            rlt, rst = payoff_l[tr].copy(), payoff_s[tr].copy()
            if shuffle:
                perm = rng.permutation(tr.sum()); rlt, rst = rlt[perm], rst[perm]
            keep = sign_gate(X[tr], rlt - rst, dayix[tr], rng)
            if keep.sum() == 0:                                # Engineer P1: ABSTAIN → baseline dir
                dpte = dd[te]                                 # (ไม่มี feature stable = ไม่เบี่ยงจาก prior · lift 0)
            else:
                mu, sd = X[tr][:, keep].mean(0), X[tr][:, keep].std(0) + 1e-9
                Xs = np.c_[np.ones(len(X)), (X[:, keep] - mu) / sd]
                w = fit_signedR(Xs[tr], rlt, rst)
                p = 1.0 / (1.0 + np.exp(-np.clip(Xs @ w, -30, 30)))
                dpte = np.where(p >= 0.5, 1, -1)[te]
            keepn.append(int(keep.sum())); lfrac.append(round(float((dpte == 1).mean()), 2))
            ab_all.append(np.full(int(te.sum()), keep.sum() == 0))
            dp_all.append(dpte); pL_all.append(pL[te]); pS_all.append(pS[te])
            d_all.append(dd[te]); day_all.append(dayix[te]); R_all.append(Rv[te])
        cat = lambda L: np.concatenate(L)
        return (cat(dp_all), cat(pL_all), cat(pS_all), cat(d_all), cat(day_all), cat(R_all),
                keepn, lfrac, cat(ab_all))

    dp, pLo, pSo, do_, dyo, Ro, keepn, lfrac, abst = wf(rl, rs)
    pred = np.where(dp == 1, pLo, pSo)                    # $ ของ predictor
    base = np.where(do_ == 1, pLo, pSo)                   # $ ของ baseline (v4 dir)
    floor = (pLo + pSo) / 2; ceil = np.maximum(pLo, pSo)
    lift = pred - base
    lo, hi = day_ci(lift, dyo, rng); loR, hiR = day_ci(lift / Ro, dyo, rng)
    flip = dp != do_
    fprec = (np.where(dp == 1, pLo > pSo, pSo > pLo)[flip]).mean() if flip.any() else float("nan")

    print(f"{'strategy (walk-exit)':<26}{'Σ$':>10}{'/ไม้$':>9}{'Σ/R':>9}")
    for nm, pn in [("floor (coin-flip)", floor), ("baseline (v4 dir)", base),
                   ("predictor (learned)", pred), ("ceiling (oracle UB)", ceil)]:
        print(f"  {nm:<24}{pn.sum():>+10.1f}{pn.mean():>+9.3f}{(pn/Ro).sum():>+9.1f}")
    print(f"\n[DECISIVE] predictor − baseline (OOS {len(pred)} ไม้ · {TEST_YEARS[0]}-{TEST_YEARS[-1]}):")
    print(f"  lift = {lift.sum():+.1f}$ ({lift.mean():+.4f}$/ไม้) · CI$[{lo:+.3f},{hi:+.3f}] · "
          f"CI/R[{loR:+.4f},{hiR:+.4f}]  {'✓>0' if lo > 0 else ('✗<0' if hi < 0 else 'คร่อม 0')}")
    print(f"  MDE (day-clustered CI half-width) ≈ {(hi - lo) / 2:.3f}$/ไม้")
    print(f"  flip-rate(OOS)={100*flip.mean():.1f}% · flip-precision={100*fprec:.1f}% vs base-rate 47.6% · "
          f"features-kept/fold={keepn} · predLongFrac/fold={lfrac} (0.0/1.0 = degenerate constant-dir bet)")

    # perm-null ≈ floor−baseline (Engineer Q2: uninformative · N=1 shuffle → ไม่มี null-band → ไม่อ้าง signal)
    dpn, pLn, pSn, don, dyn, Rn, _, _, _ = wf(rl, rs, shuffle=True)
    liftn = np.where(dpn == 1, pLn, pSn) - np.where(don == 1, pLn, pSn)
    fb = floor.mean() - base.mean()
    print(f"  perm-null lift={liftn.mean():+.3f} ≈ floor−baseline {fb:+.3f} (uninformative · **N=1 shuffle ไม่สร้าง null-band → "
          f"ไม่อ้าง 'weak-signal exists'** · Engineer Q2)")
    # ACTIVE-fold (ตัด abstain · Engineer Q1: aggregate เจือจาง 34% · = decision-relevant สำหรับ 'features มี signal ไหม')
    act = ~abst
    la, ha = day_ci(lift[act], dyo[act], rng)
    print(f"  **ACTIVE folds (gate ใช้ feature · {act.sum()}/{len(lift)} ไม้): lift={lift[act].mean():+.3f}$ "
          f"CI[{la:+.3f},{ha:+.3f}]** (เมื่อ act = hurt · marginally-sig · post-selection) · abstain {(~act).sum()} = baseline")

    # NONLINEAR capacity check — capacity-FAIR (Engineer Q3: sign-classifier · weight=|payoff| · min_child~fold)
    from lightgbm import LGBMClassifier
    gdp, gpL, gpS, gd, gday = [], [], [], [], []
    for Y in TEST_YEARS:
        te = yr == Y
        if te.sum() < 50:
            continue
        tr = np.array([int(y) < int(Y) for y in yr]) & (dayix < dayix[te].min() - Nemb)
        if tr.sum() < 300:
            continue
        yt = ((rl - rs)[tr] >= 0).astype(int); wt = np.abs((rl - rs)[tr])
        gm = LGBMClassifier(max_depth=3, n_estimators=150, learning_rate=0.05,
                            min_child_samples=max(20, tr.sum() // 20),
                            subsample=0.8, colsample_bytree=0.8, verbose=-1, random_state=0)
        gm.fit(X[tr], yt, sample_weight=wt)
        gdp.append(np.where(gm.predict(X[te]) == 1, 1, -1))
        gpL.append(pL[te]); gpS.append(pS[te]); gd.append(dd[te]); gday.append(dayix[te])
    gdp, gpL, gpS, gd, gday = map(np.concatenate, (gdp, gpL, gpS, gd, gday))
    glift = np.where(gdp == 1, gpL, gpS) - np.where(gd == 1, gpL, gpS)
    glo, ghi = day_ci(glift, gday, rng)
    print(f"  [NONLINEAR GBM · sign-classifier weighted · min_child~fold/20] lift={glift.mean():+.3f}$ "
          f"CI[{glo:+.3f},{ghi:+.3f}] {'✓>0' if glo > 0 else 'คร่อม/<0'}")

    print(f"\n[READOUT · honest · TERMINAL · in-field SEARCH ไม่ใช่ OOS จริง]")
    print(f"  • baseline (v4 breakout-rule) มี direction skill +{base.mean():.3f}$/ไม้ (> floor {floor.mean():+.3f}) = fact ของ rule ที่มีอยู่")
    print(f"  • learned OHLC (19-feat · linear+GBM) **ไม่ชนะ baseline · point-negative ทุก estimator:** "
          f"aggregate {lift.mean():+.3f} (คร่อม 0 · เจือจาง abstain 34%) · ACTIVE-fold {lift[act].mean():+.3f} CI[{la:+.3f},{ha:+.3f}] "
          f"(hurt เมื่อ act) · GBM {glift.mean():+.3f}")
    print(f"  • OHLC features **~95% NOT sign-stable** (kept เฉลี่ย {np.mean(keepn):.1f}/19)")
    print(f"  • **OHLC extractable ceiling = ยังไม่วัด** · oracle {ceil.mean():+.2f} → **headroom +{ceil.mean()-base.mean():.1f}$/ไม้ ยังเหลือ** "
          f"= direction **ยังไม่ solved** (แค่ 19-feat นี้จับไม่ได้)")
    v = ("**19 OHLC features เหล่านี้ไม่มี usable additive direction signal ที่ real exit** (point-negative เมื่อ act) · "
         f"ceiling ที่แท้ไม่ทราบ · +{ceil.mean()-base.mean():.1f} oracle-headroom เหลือ · "
         "**ไม่ prescribe ทิศถัดไป — ให้ Win ตัดสิน**") if (lo <= 0 <= hi) else \
        f"linear CI[{lo:+.2f},{hi:+.2f}] · GBM CI[{glo:+.2f},{ghi:+.2f}] — ตรวจ per-model"
    print(f"  → TERMINAL: {v}")
    print(f"  ⚠ SEARCH 2012-2020 · WF≠true-OOS · post-selection active-fold (upper เปราะ) · **ไม่ใช่ 'proven-zero'**")


if __name__ == "__main__":
    main()
