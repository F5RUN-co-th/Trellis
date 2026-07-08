#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
direction_predictor.py — TRELLIS-010 v3 · learned as-of DIRECTION predictor v0
(บน L1 opportunity-unit v4 · Engineer PASS · §9 next-step)

คำถาม: learned predictor จาก **as-of feature (≤ close bar j · no-leak)** ทำ **OOS signed-R
net-of-cost > 0** (ชนะ baselines same-exit: follow-trigger/always-long) ได้ไหม?
objective = **maximize E[signed-R] โดยตรง** (Engineer P1: ไม่ใช่ classification · payoff asymmetric
ถูก~1.6R/ผิด−1R → weight โดยธรรมชาติจาก (rl−rs) ใน gradient · align เป้า "กำไร")
⚠ P4: label ที่นี่ใช้ exit 1R-stop/1.5R-target → **คนละ label กับ '52.7% floor'** (bestdir=maxMFE
ของ opportunity_unit) = apples-to-oranges · เทียบกับ baselines same-exit เท่านั้น (ไม่อ้าง beat floor)

DECISION POINT = event-trigger bar (both/W60 edge · = จุดที่จะพิจารณาเข้า · tradeable)
LABEL (target · future OK) = ทิศที่กำไรกว่า (trade_R long vs short)
FEATURE (as-of ≤ bar i · PAST เท่านั้น · no-leak): tdir · ret5/15/60 · pos-in-range · dist-pdh ·
  vol30 · slope60 · hour — ทั้งหมดคำนวณจาก [.. i] ไม่แตะอนาคต
OUTCOME sim = enter d · stop 1R · target 1.5R · adverse-first intrabar · EOD close · −cost(spread+slip)
SPLIT = train 2012-2017 · **OOS holdout 2018-2020** (leg-c) · baselines: follow-trigger · always-long
  · oracle-bestdir (UB) · permutation-null (shuffle label → OOS→follow-trigger)
model = logistic regression (numpy · simple · anti-curve-fit) · day-clustered bootstrap CI
⚠ field=SEARCH cost-inclusive · **clock price-match ยังไม่ทำ** (pre-CONFIRM gate) · v0 = L0
Usage: python direction_predictor.py
"""
import sys
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, PT, SLIP_IN, SLIP_STOP
from opportunity_unit_v4 import make_triggers, build_normalizers, ACCT_TARGETS

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

T_TGT, STOP = 1.5, 1.0
TRAIN_YRS = {"2012", "2013", "2014", "2015", "2016", "2017"}
OOS_YRS = {"2018", "2019", "2020"}


def trade_R(hh, ll, cc, i, d, R, cost):
    """signed-R ของการเข้า dir d ณ bar i · stop 1R · target T · adverse-first · EOD close · −cost"""
    ent = cc[i]
    n = len(cc)
    for q in range(i + 1, n):
        adv = (ent - ll[q]) if d == 1 else (hh[q] - ent)
        fav = (hh[q] - ent) if d == 1 else (ent - ll[q])
        if adv >= STOP * R:
            return -STOP - cost
        if fav >= T_TGT * R:
            return T_TGT - cost
    return (cc[-1] - ent) * d / R - cost


def build_dataset(ctx):
    day, o, h, l, c, sp, hour = (ctx["day"], ctx["o"], ctx["h"], ctx["l"], ctx["c"],
                                 ctx["sp"], ctx["hour"])
    cal, _ = build_normalizers(ctx)
    Rmap = cal[f"daily@{ACCT_TARGETS[0]}"]
    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(h)]
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    ul, fl, bl = uniq.tolist(), fidx.tolist(), bnd.tolist()
    X, Y, meta = [], [], []                                   # meta: (year, dayidx, tdir, rl, rs, cost)
    for j, (di, i0, i1) in enumerate(zip(ul, fl, bl)):
        dts = str(np.datetime64(int(di), "D"))
        if dts not in Rmap or Rmap[dts] <= 0:
            continue
        R = Rmap[dts]
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22)
        gi = np.arange(i0, i1)[m]
        oo, hh, ll, cc, spd, hr = o[gi], h[gi], l[gi], c[gi], sp[gi], hour[gi]
        n = len(cc)
        if n < 90:
            continue
        pdi = ul[j - 1] if j > 0 else None
        pdh = dhi.get(pdi) if pdi else None
        pdl = dlo.get(pdi) if pdi else None
        lt, st = make_triggers(hh, ll, cc, pdh, pdl, "both", 60)
        cummin = np.minimum.accumulate(ll)
        cummax = np.maximum.accumulate(hh)
        for i in np.where(lt | st)[0]:
            if i < 60 or i > n - 5:                           # ต้องมี history 60 + room ข้างหน้า
                continue
            tdir = 1 if (lt[i] and not st[i]) else (-1 if (st[i] and not lt[i]) else 0)
            if tdir == 0:
                continue
            cost = (spd[i] * PT + SLIP_IN + SLIP_STOP) / R
            rl = trade_R(hh, ll, cc, i, 1, R, cost)
            rs = trade_R(hh, ll, cc, i, -1, R, cost)
            rng = cummax[i] - cummin[i]
            feat = [
                tdir,
                (cc[i] - cc[i - 5]) / R,
                (cc[i] - cc[i - 15]) / R,
                (cc[i] - cc[i - 60]) / R,
                (cc[i] - cummin[i]) / rng if rng > 0 else 0.5,
                (cc[i] - pdh) / R if pdh else 0.0,
                (hh[i - 30:i + 1].max() - ll[i - 30:i + 1].min()) / R,
                (cc[i] - cc[i - 60:i + 1].mean()) / R,
                (hr[i] - 11.5) / 6.5,
            ]
            X.append(feat)
            Y.append(1 if rl >= rs else 0)
            meta.append((dts[:4], j, tdir, rl, rs, cost))
    return np.array(X), np.array(Y), meta


def fit_signedR(X, rl, rs, iters=2000, lr=0.5, l2=2e-3):
    """maximize E[signed-R] = mean(p·rl + (1−p)·rs) · p=σ(Xw) · ∇ = mean((rl−rs)·p(1−p)·X)
    (Engineer P1 · objective ที่ §9 สั่ง = expected signed-R · (rl−rs) = payoff-weight ในตัว)"""
    w = np.zeros(X.shape[1]); d = rl - rs; n = len(rl)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(X @ w, -30, 30)))
        w += lr * (X.T @ (d * p * (1 - p)) / n - l2 * w)
    return w


def day_ci(vals, days, rng, nb=400):
    uniq = np.unique(days)
    d2i = {d: np.where(days == d)[0] for d in uniq}
    out = []
    for _ in range(nb):
        pick = rng.choice(uniq, len(uniq), replace=True)
        out.append(np.mean(np.concatenate([vals[d2i[d]] for d in pick])))
    return np.percentile(out, 2.5), np.percentile(out, 97.5)


def main():
    ctx = load_ctx()
    X, Y, meta = build_dataset(ctx)
    yrs = np.array([m[0] for m in meta])
    days = np.array([m[1] for m in meta])
    tdir = np.array([m[2] for m in meta])
    rl = np.array([m[3] for m in meta])
    rs = np.array([m[4] for m in meta])
    tr = np.array([y in TRAIN_YRS for y in yrs])
    te = np.array([y in OOS_YRS for y in yrs])
    print(f"=== Direction Predictor v0 · field=SEARCH · signed-R(T={T_TGT}/stop{STOP}) net-of-cost ===")
    print(f"decision-points (event-trigger both/W60) = {len(X):,} · train(12-17)={tr.sum():,} "
          f"OOS(18-20)={te.sum():,} · features={X.shape[1]} (as-of ≤ bar · no-leak)")

    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9              # standardize: train stats เท่านั้น (no leak)
    Xs = np.c_[np.ones(len(X)), (X - mu) / sd]
    w = fit_signedR(Xs[tr], rl[tr], rs[tr])                  # objective = E[signed-R] (P1)
    p = 1.0 / (1.0 + np.exp(-np.clip(Xs @ w, -30, 30)))
    dpred = np.where(p >= 0.5, 1, -1)
    conf = np.abs(p - 0.5)                                   # ex-ante confidence (สำหรับ gate · P3)

    def signed(mask, d):
        return np.where(d == 1, rl, rs)[mask]
    rng = np.random.default_rng(20260708)

    # [DIAGNOSTIC · P2 fix v2] objective-consistent: train-SR vs best-constant-direction (ไม่ใช่
    # class-acc ที่ inconsistent กับ E[signed-R] objective) · + direction non-stationarity (คอขวดจริง)
    bc = max(rl[tr].mean(), rs[tr].mean())                   # best-constant-dir train SR
    lift = signed(tr, dpred).mean() - bc
    print(f"\n[DIAGNOSTIC] train signed-R={signed(tr,dpred).mean():+.4f}R vs best-constant-dir {bc:+.4f}R "
          f"(features lift {lift:+.4f}R) · OOS={signed(te,dpred).mean():+.4f}R → "
          f"{'UNDERFIT (features เพิ่ม ~0 in-sample)' if lift < 0.01 else 'มี in-sample separability'}")
    print(f"  ⚠ DIRECTION NON-STATIONARY: train mean(rl−rs)={(rl-rs)[tr].mean():+.3f} vs OOS "
          f"{(rl-rs)[te].mean():+.3f} = **SIGN-FLIP** → payoff-direction ไม่ stationary ข้าม regime = "
          f"คอขวดจริง (v1 ต้อง sign-stability gate ก่อนคาด OOS>0)")

    # [SAME-EXIT baselines · P4] เทียบ apples-to-apples (ไม่อ้าง beat 52.7% floor = คนละ label)
    print(f"\n{'strategy (same 1R/1.5R exit)':<28}{'OOS signed-R':>15}{'95%CI (day-clust)':>25}{'WR':>7}")
    for name, d in [("predictor (E[signed-R])", dpred), ("follow-trigger (naive)", tdir),
                    ("always-long", np.ones(len(X), int)), ("oracle-bestdir (UB)", np.where(rl >= rs, 1, -1))]:
        v = signed(te, d); lo, hi = day_ci(v, days[te], rng)
        print(f"  {name:<26}{v.mean():>+13.4f}R{f'[{lo:+.4f},{hi:+.4f}]':>25}{100*(v>0).mean():>6.0f}%"
              f"{'  ✓>0' if lo > 0 else ''}")
    diff = signed(te, dpred) - signed(te, tdir); lo, hi = day_ci(diff, days[te], rng)
    print(f"  predictor − follow-trigger (paired) = {diff.mean():+.4f}R [{lo:+.4f},{hi:+.4f}] "
          f"{'✓ ชนะ naive' if lo > 0 else 'ไม่ชนะ (CI คร่อม 0)'}")

    # [DEPLOYABLE · P3] ex-ante confidence-gated curve — เทรดเฉพาะ top-q% มั่นใจสุด (gate ด้วย |p−0.5|
    # = ex-ante · ไม่ใช่ realized |rl−rs| = look-ahead) · abstain ที่เหลือ
    print(f"\n[DEPLOYABLE · ex-ante confidence gate] เทรด top-q% มั่นใจสุด (abstain ส่วนที่เหลือ):")
    print(f"  {'top-q%':>8}{'n(OOS)':>9}{'signed-R':>12}{'95%CI':>24}{'longFrac':>10}")
    vte, cte = signed(te, dpred), conf[te]
    for q in (100, 50, 20, 10, 5):
        sel = cte >= np.percentile(cte, 100 - q)
        if not sel.any():
            continue
        lo2, hi2 = day_ci(vte[sel], days[te][sel], rng)
        lf = (dpred[te][sel] == 1).mean()
        print(f"  {q:>7}%{int(sel.sum()):>9}{vte[sel].mean():>+11.4f}R{f'[{lo2:+.4f},{hi2:+.4f}]':>24}"
              f"{lf:>9.2f}{'  ⚠→long' if lf > 0.9 else ''}")

    # [PERMUTATION NULL] shuffle feature↔outcome pairing ใน train → ทำลาย signal
    idx = rng.permutation(int(tr.sum()))
    wp = fit_signedR(Xs[tr][idx], rl[tr], rs[tr])
    dp = np.where(1.0 / (1.0 + np.exp(-np.clip(Xs @ wp, -30, 30))) >= 0.5, 1, -1)
    print(f"\n  permutation-null (shuffle feature↔outcome) OOS = {signed(te, dp).mean():+.4f}R "
          f"(predictor ≈ นี่ = ไม่มีสัญญาณจริง)")
    print("\n⚠ v0 L0 · SEARCH cost-incl · clock price-match ยังไม่ทำ (pre-CONFIRM gate) · linear features ชุดแรก "
          "· OOS signed-R>0 + ชนะ naive + ≫ perm + gate ให้ positive = candidate edge → v1 (family เพิ่ม)")


if __name__ == "__main__":
    main()
