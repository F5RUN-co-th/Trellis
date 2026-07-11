#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
direction_predictor_v1.py — TRELLIS-010 v3 · Direction Predictor v1
(v0 = honest NEGATIVE · linear OHLCV ไม่มี OOS edge · คอขวด = DIRECTION NON-STATIONARITY
mean(rl−rs) sign-flip train−0.125→OOS+0.018)

v1 = Engineer sharpening: **SIGN-STABILITY GATE ก่อน** (feature/family ต้องโชว์ conditional-
direction sign-stable train→OOS · ไม่ผ่าน = dead ไม่ว่า expressive แค่ไหน) → แล้วเพิ่ม family:
  · REGIME-proxy: ret240 · pos vs 5-day range (จับ regime ที่ทำให้ direction flip)
  · EVENT-STREAM: net trigger-pressure (long−short fires ใน 30 bar) · n-trig
  · MICROSTRUCTURE: CLV (close-location-value) · wick ratios · body — proxy ของ pressure ที่
    OHLCV มี (ไม่ใช่ order-flow = Stage-F)
  · NONLINEAR: interactions (tdir×ret · pos×slope)
objective/eval คงจาก v0 (reuse · E[signed-R] · OOS holdout · same-exit baselines · perm-null ·
day-clustered CI · ex-ante confidence-gate) — **info-theory-bounded · ไม่ Stage-F**
⚠ ถ้า sign-stability gate ล้มทุก family + OOS ยังลบ = evidence แรงขึ้นว่า OHLCV-direction ตาย
(แต่ยังต้องหลาย family/representation ก่อน Stage-F §9)
Usage: python direction_predictor_v1.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, PT, SLIP_IN, SLIP_STOP
from opportunity_unit_v4 import make_triggers, build_normalizers, ACCT_TARGETS
from direction_predictor import trade_R, fit_signedR, day_ci, TRAIN_YRS, OOS_YRS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FEATS = ["tdir", "ret5", "ret15", "ret60", "ret240", "posrange", "dist_pdh", "dist_pdl",
         "vol30", "slope60", "trigpress", "ntrig30", "clv", "clv5", "upwick", "dnwick",
         "body", "tdir_x_ret15", "pos_x_slope"]
FAM = {"base": range(0, 10), "event": [10, 11], "micro": [12, 13, 14, 15, 16], "nonlin": [17, 18]}


def build(ctx):
    day, o, h, l, c, sp, hour = (ctx["day"], ctx["o"], ctx["h"], ctx["l"], ctx["c"],
                                 ctx["sp"], ctx["hour"])
    Rmap = build_normalizers(ctx)[0][f"daily@{ACCT_TARGETS[0]}"]
    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(h)]
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    ul, fl, bl = uniq.tolist(), fidx.tolist(), bnd.tolist()
    X, meta = [], []
    for j, (di, i0, i1) in enumerate(zip(ul, fl, bl)):
        dts = str(np.datetime64(int(di), "D"))
        if dts not in Rmap or Rmap[dts] <= 0:
            continue
        R = Rmap[dts]
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22)
        gi = np.arange(i0, i1)[m]
        oo, hh, ll, cc, spd, hr = o[gi], h[gi], l[gi], c[gi], sp[gi], hour[gi]
        n = len(cc)
        if n < 250:
            continue
        pdi = ul[j - 1] if j > 0 else None
        pdh = dhi.get(pdi) if pdi else None
        pdl = dlo.get(pdi) if pdi else None
        lt, st = make_triggers(hh, ll, cc, pdh, pdl, "both", 60)
        cmin = np.minimum.accumulate(ll)
        cmax = np.maximum.accumulate(hh)
        rng_bar = np.maximum(hh - ll, 1e-9)
        clv = ((cc - ll) - (hh - cc)) / rng_bar
        upw = (hh - np.maximum(oo, cc)) / rng_bar
        dnw = (np.minimum(oo, cc) - ll) / rng_bar
        body = np.abs(cc - oo) / rng_bar
        for i in np.where(lt | st)[0]:
            if i < 240 or i > n - 5:
                continue
            tdir = 1 if (lt[i] and not st[i]) else (-1 if (st[i] and not lt[i]) else 0)
            if tdir == 0:
                continue
            cost = (spd[i] * PT + SLIP_IN + SLIP_STOP) / R
            rl = trade_R(hh, ll, cc, i, 1, R, cost)
            rs = trade_R(hh, ll, cc, i, -1, R, cost)
            dr = cmax[i] - cmin[i]
            ret15 = (cc[i] - cc[i - 15]) / R
            slope60 = (cc[i] - cc[i - 60:i + 1].mean()) / R
            pos = (cc[i] - cmin[i]) / dr if dr > 0 else 0.5
            feat = [
                tdir,
                (cc[i] - cc[i - 5]) / R, ret15, (cc[i] - cc[i - 60]) / R, (cc[i] - cc[i - 240]) / R,
                pos,
                (cc[i] - pdh) / R if pdh else 0.0, (cc[i] - pdl) / R if pdl else 0.0,
                (hh[i - 30:i + 1].max() - ll[i - 30:i + 1].min()) / R,
                slope60,
                int(lt[i - 30:i].sum()) - int(st[i - 30:i].sum()),      # net trigger pressure
                int(lt[i - 30:i].sum()) + int(st[i - 30:i].sum()),      # n-trig
                clv[i], clv[i - 5:i + 1].mean(), upw[i], dnw[i], body[i],
                tdir * ret15, pos * slope60,
            ]
            X.append(feat)
            meta.append((dts[:4], j, tdir, rl, rs, i))   # i = session-bar index (append ท้าย — ผู้บริโภคเดิม positional m[0..4] ไม่กระทบ · CLAIM-0014 join)
    return np.array(X), meta


def main():
    ctx = load_ctx()
    X, meta = build(ctx)
    yrs = np.array([m[0] for m in meta])
    days = np.array([m[1] for m in meta])
    tdir = np.array([m[2] for m in meta])
    rl = np.array([m[3] for m in meta])
    rs = np.array([m[4] for m in meta])
    d = rl - rs
    tr = np.array([y in TRAIN_YRS for y in yrs])
    te = np.array([y in OOS_YRS for y in yrs])
    print(f"=== Direction Predictor v1 · field=SEARCH · E[signed-R] · {X.shape[1]} feats ({len(X):,} pts) ===")
    print(f"train(12-17)={tr.sum():,} OOS(18-20)={te.sum():,}")

    # ── SIGN-STABILITY GATE (Engineer · ก่อนคาด OOS>0) ──
    print(f"\n[SIGN-STABILITY GATE] corr(feature, rl−rs) train vs OOS — sign เท่ากันไหม (stable=predictive)")
    print(f"  {'feature':<14}{'corr_train':>11}{'corr_OOS':>10}  stable?")
    stable = []
    for k, name in enumerate(FEATS):
        ct = np.corrcoef(X[tr, k], d[tr])[0, 1]
        co = np.corrcoef(X[te, k], d[te])[0, 1]
        ss = (ct * co > 0) and abs(ct) > 0.01 and abs(co) > 0.01
        stable.append(ss)
        flag = "✓ stable" if ss else ("flip" if ct * co < 0 else "~0")
        print(f"  {name:<14}{ct:>+11.3f}{co:>+10.3f}  {flag}")
    print(f"  → sign-stable features = {sum(stable)}/{len(FEATS)} "
          f"({[FEATS[k] for k in range(len(FEATS)) if stable[k]]})")

    # ── fit E[signed-R] · full features ──
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
    Xs = np.c_[np.ones(len(X)), (X - mu) / sd]
    rng = np.random.default_rng(20260708)

    def evalw(w, name):
        p = 1.0 / (1.0 + np.exp(-np.clip(Xs @ w, -30, 30)))
        dp = np.where(p >= 0.5, 1, -1)
        v = np.where(dp == 1, rl, rs)
        lo, hi = day_ci(v[te], days[te], rng)
        bc = max(rl[tr].mean(), rs[tr].mean())
        print(f"  {name:<26} train={v[tr].mean():+.4f}R (bc {bc:+.4f}) OOS={v[te].mean():+.4f}R "
              f"[{lo:+.4f},{hi:+.4f}]{'  ✓>0' if lo > 0 else ''}")
        return p, v

    print(f"\n[FIT E[signed-R] · OOS holdout]")
    w = fit_signedR(Xs[tr], rl[tr], rs[tr])
    p, v = evalw(w, "predictor v1 (all feats)")
    # sign-stable-only subset
    keep = [0] + [k + 1 for k in range(len(FEATS)) if stable[k]]
    if len(keep) > 1:
        ws = np.zeros(Xs.shape[1])
        ws[keep] = fit_signedR(Xs[tr][:, keep], rl[tr], rs[tr])
        evalw(ws, "predictor (stable-only)")
    # baselines
    for nm, dd in [("follow-trigger", tdir), ("always-long", np.ones(len(X), int)),
                   ("oracle-bestdir (UB)", np.where(rl >= rs, 1, -1))]:
        vb = np.where(dd == 1, rl, rs)
        lo, hi = day_ci(vb[te], days[te], rng)
        print(f"  {nm:<26} {'':>25}OOS={vb[te].mean():+.4f}R [{lo:+.4f},{hi:+.4f}]{'  ✓>0' if lo > 0 else ''}")

    # ex-ante confidence gate
    print(f"\n[DEPLOYABLE · ex-ante confidence gate] top-q% มั่นใจสุด:")
    dp = np.where(p >= 0.5, 1, -1); conf = np.abs(p - 0.5)
    vte, cte = v[te], conf[te]
    for q in (100, 20, 10, 5):
        sel = cte >= np.percentile(cte, 100 - q)
        if sel.any():
            lo, hi = day_ci(vte[sel], days[te][sel], rng)
            print(f"  top-{q:>3}%  n={int(sel.sum()):>6}  OOS={vte[sel].mean():+.4f}R [{lo:+.4f},{hi:+.4f}]"
                  f"  longFrac={dp[te][sel].mean()*0.5+0.5:.2f}")

    # permutation null
    idx = rng.permutation(int(tr.sum()))
    wp = fit_signedR(Xs[tr][idx], rl[tr], rs[tr])
    pp = 1.0 / (1.0 + np.exp(-np.clip(Xs @ wp, -30, 30)))
    vp = np.where(pp >= 0.5, 1, -1)
    vpn = np.where(vp == 1, rl, rs)
    print(f"\n  permutation-null OOS = {vpn[te].mean():+.4f}R (predictor ≈ นี่ = ไม่มีสัญญาณจริง)")
    print(f"\n⚠ v1 L0 · ถ้า OOS>0 + ชนะ naive + ≫ perm + sign-stable = candidate → OOS-per-regime + CONFIRM · "
          f"ถ้ายังลบ + gate ล้ม = OHLCV-direction อ่อนมาก (แต่ยังต้อง family/representation อื่นก่อน Stage-F)")


if __name__ == "__main__":
    main()
