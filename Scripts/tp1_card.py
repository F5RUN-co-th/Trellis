#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tp1_card.py — TRELLIS-010 · Card TP-1: tick-price direction-at-real-exit (NESTED INCREMENTAL)
Spec v2 frozen (Engineer 3 รอบ: R1 B1-B3/M1-M6 · R2 P1-P6 · R3 Issue1-6 — PASS-with-changes ผนวกครบ)
budget = card 1/40 ของ family ใหม่ v3-reframe (Win ประกาศนับใหม่ 2026-07-13 · family เก่าปิด 9/40)

═══ PRE-REGISTRATION (ประกาศก่อนรัน · R3 Issue-6) ═══
CLAIM-id จอง: CLAIM-0015
HYPOTHESIS: sub-minute bid tick-price sequence มี additive direction signal ที่ real EA exit
  เหนือ baseline = [19-feat OHLC (CLAIM-0010 ฆ่า seed-robust) + M1-shadow ของ tick features
  + log(win_sec) era-control] — ยิง invalidated-by ของ CLAIM-0010 ตรงๆ
DESIGN: Model A = baseline(24) · Model B = baseline+tick(30) · ทั้งคู่ผ่าน pipeline 0010 เดิมเป๊ะ
  (sign_gate train-only per-fold · fit_signedR · expanding-WF+embargo · day-clustered CI · 9 seeds)
  · primary = linear joint-nested aggregate lift (B−A) — ไม่มี FWE (aggregate เดียว) · per-feature
  = DIAGNOSTIC เท่านั้น · GBM nested (hyperparams A/B เหมือนกันเป๊ะ) = confirmatory
VERDICT RULES (R3 Issue-1 asymmetric):
  PASS  = lift CI-lower(day) > 0 ครบ 9/9 seeds ∧ perm-p < .05 (linear primary)
  KILL  = [lift ≤ 0 ทุก seed ∨ ไม่มี seed CI-lower>0] ∧ GBM เงื่อนไขเดียวกัน ∧ FORCED-IN
          (tick บังคับเข้า fit · baseline gate ปกติ) ก็ไม่มี seed CI-lower>0
  INCONCLUSIVE(gate-limited) = gated ไม่ผ่านแต่ FORCED-IN มี seed CI-lower>0
  อื่นๆ = NOT-PASS (รายละเอียดในตาราง) · in-sample ทุกชนิด = DIAGNOSTIC (กัน gate1-trap)
PERM-NULL (R2 P2 รันจริง · R3 Issue-2): permute tick-block rows ใน train ต่อ fold (one-entry-per-day
  verified — row-perm = day-perm) · re-gate เฉพาะ tick block (baseline gate/standardize cache —
  invariant ต่อ tick-perm) · refit B · lift vs cached A · B_PERM=1000 · single seed 20260708
  (decouple จาก 9-seed sweep) · GBM-perm B=300 = DIAGNOSTIC
SCOPE-OF-DEATH (ถ้า KILL): 6 tick-price features (imb/path_eff/srun/mvol/dur_cv/lvl_act ·
  bid-only · event-time N=3000) · linear+GBM · ที่ real walk-exit บน SEARCH 2012-2020 —
  ไม่ใช่ tick-price ทั้งแนว · ไม่ใช่ proven-zero · ไม่ใช่ event-stream representation อื่น
LEDGER edits ทั้งสอง branch เตรียมแล้ว: PASS → frontier tick-price = candidate CI-backed ·
  KILL → frontier tick-price = eliminated (scope ตามบน) · field-tag[SIM-SEARCH]
⚠ FIELD = SIM-SEARCH 2012-2020 เท่านั้น · lockbox 2024-26 + guard 2021-23 ไม่ถูกแตะ
Usage: python tp1_card.py
"""
import csv
import hashlib
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx
from direction_at_real_exit import build_rows, sign_gate, _rng, TEST_YEARS
from direction_predictor import fit_signedR, day_ci

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
FEAT_CSV = ROOT / "Research/h0/tp1_tickfeat_2012_2020.csv"
FEAT_SHA = ROOT / "Research/h0/tp1_tickfeat_2012_2020.sha256"
TICK_COLS = ["imb", "path_eff", "srun", "mvol", "dur_cv", "lvl_act"]
SHADOW_COLS = ["sh_path", "sh_srun", "sh_mvol", "sh_lvl"]
SEEDS = [20260708, 1, 2, 42, 123, 999, 99999, 20260709, 7]   # ชุดเดียวกับ CLAIM-0010
B_PERM, B_PERM_GBM = 1000, 300
PERM_ROOT = 20260708


def load_joined():
    sha = hashlib.sha256(FEAT_CSV.read_bytes()).hexdigest()
    assert sha == FEAT_SHA.read_text().strip(), "tp1_tickfeat SHA mismatch — frozen input เปลี่ยน"
    tp1 = {r["date"]: r for r in csv.DictReader(open(FEAT_CSV, encoding="utf-8"))}
    ctx = load_ctx()
    rows = build_rows(ctx)                              # GUARD 1/2 ของ 0010 รันในตัว
    uniq = np.unique(ctx["day"])
    dts_of = {jx: str(np.datetime64(int(di), "D")) for jx, di in enumerate(uniq.tolist())}
    kept, drop_nan, drop_missing = [], {}, 0
    for r in rows:
        t = tp1.get(dts_of[r["dayix"]])
        if t is None:
            drop_missing += 1
            continue
        if t["nan_reason"]:
            y = t["date"][:4]; drop_nan[y] = drop_nan.get(y, 0) + 1
            continue
        r["tick"] = [float(t[c]) for c in TICK_COLS]
        r["shadow"] = [float(t[c]) for c in SHADOW_COLS] + [float(np.log(float(t["win_sec"])))]
        kept.append(r)
    print(f"[JOIN] rows={len(rows)} kept={len(kept)} nan-dropped={drop_nan} "
          f"missing-manifest={drop_missing} (A/B ใช้ population เดียวกัน = แฟร์ · M5 report)")
    return kept


def arrays(rows):
    Xb = np.array([list(r["feat"]) + r["shadow"] for r in rows], float)   # 19+4+1 = 24
    Xt = np.array([r["tick"] for r in rows], float)                       # 6
    pL = np.array([r["pL"] for r in rows]); pS = np.array([r["pS"] for r in rows])
    Rv = np.array([r["R"] for r in rows]); dd = np.array([r["d"] for r in rows])
    yr = np.array([r["yr"] for r in rows]); dayix = np.array([r["dayix"] for r in rows])
    rl, rs = pL / Rv, pS / Rv
    Nemb = max(r["hold"] for r in rows)
    return Xb, Xt, pL, pS, dd, yr, dayix, rl, rs, Nemb


def folds(yr, dayix, Nemb):
    out = []
    for Y in TEST_YEARS:
        te = yr == Y
        if te.sum() < 50:
            continue
        tr = np.array([int(y) < int(Y) for y in yr]) & (dayix < dayix[te].min() - Nemb)
        if tr.sum() < 300:
            continue
        out.append((Y, tr, te))
    return out


def fit_predict(X, keep, tr, te, rlt, rst, dd):
    """mirror wf ของ 0010 (:152-159) เป๊ะ — abstain (keep==0) → baseline dir (v4)"""
    if keep.sum() == 0:
        return dd[te]
    mu, sd = X[tr][:, keep].mean(0), X[tr][:, keep].std(0) + 1e-9
    Xs = np.c_[np.ones(len(X)), (X[:, keep] - mu) / sd]
    w = fit_signedR(Xs[tr], rlt, rst)
    p = 1.0 / (1.0 + np.exp(-np.clip(Xs @ w, -30, 30)))
    return np.where(p >= 0.5, 1, -1)[te]


def payoff(dp, pL, pS, te):
    return np.where(dp == 1, pL[te], pS[te])


def wf_nested(Xb, Xt, pL, pS, dd, rl, rs, fold_list, root, forced=False):
    """Model A (baseline 24) vs Model B (baseline+tick 30) — lift ต่อ test row
    forced=True: tick block บังคับเข้า fit (gate bypass เฉพาะ tick · R3 Issue-1 KILL guard)"""
    Xall = np.hstack([Xb, Xt])
    la, da = [], []
    for Y, tr, te in fold_list:
        rlt, rst = rl[tr], rs[tr]
        pay_tr = rlt - rst
        kA = sign_gate(Xb[tr], pay_tr, DAYS_G[tr], _rng(f"gA_{Y}", root))
        if forced:
            kB = np.r_[kA, np.ones(Xt.shape[1], bool)]     # base = gate ของ A · tick = forced
        else:
            kB = sign_gate(Xall[tr], pay_tr, DAYS_G[tr], _rng(f"gB_{Y}", root))
        dpA = fit_predict(Xb, kA, tr, te, rlt, rst, dd)
        dpB = fit_predict(Xall, kB, tr, te, rlt, rst, dd)
        la.append(payoff(dpB, pL, pS, te) - payoff(dpA, pL, pS, te))
        da.append(DAYS_G[te])
    return np.concatenate(la), np.concatenate(da)


def perm_null(Xb, Xt, pL, pS, dd, rl, rs, fold_list, obs_agg):
    """R2 P2 + R3 Issue-2: permute tick rows ใน train · re-gate เฉพาะ tick (sign_gate ตรงๆ —
    semantics เดียวกับ observed) · baseline gate + Model A cache · single seed · B_PERM"""
    Xall = np.hstack([Xb, Xt])
    cache = []
    for Y, tr, te in fold_list:
        rlt, rst = rl[tr], rs[tr]
        pay_tr = rlt - rst
        kB_obs = sign_gate(Xall[tr], pay_tr, DAYS_G[tr], _rng(f"gB_{Y}", PERM_ROOT))
        kA = sign_gate(Xb[tr], pay_tr, DAYS_G[tr], _rng(f"gA_{Y}", PERM_ROOT))
        dpA = fit_predict(Xb, kA, tr, te, rlt, rst, dd)
        payA = payoff(dpA, pL, pS, te)
        cache.append((Y, tr, te, rlt, rst, pay_tr, kB_obs[:Xb.shape[1]], payA))
    rng = _rng("permmaster", PERM_ROOT)
    null = np.empty(B_PERM)
    t0 = time.time()
    for b in range(B_PERM):
        lifts, ns = 0.0, 0
        for Y, tr, te, rlt, rst, pay_tr, kB_base, payA in cache:
            idx = rng.permutation(tr.sum())
            Xtp = Xt[tr][idx]                              # permute tick block ใน train
            kT = sign_gate(Xtp, pay_tr, DAYS_G[tr], _rng(f"pg_{Y}_{b}", PERM_ROOT))
            Xall_p = Xall.copy()
            Xall_p[tr, Xb.shape[1]:] = Xtp                 # test-side tick คงเดิม (fit เท่านั้นที่ null)
            kB = np.r_[kB_base, kT]
            dpB = fit_predict(Xall_p, kB, tr, te, rlt, rst, dd)
            lift = payoff(dpB, pL, pS, te) - payA
            lifts += lift.sum(); ns += len(lift)
        null[b] = lifts / ns
        if b in (9, 99):
            print(f"    [perm] {b + 1}/{B_PERM} · {time.time() - t0:.0f}s elapsed", flush=True)
    p = (1 + int((null >= obs_agg).sum())) / (B_PERM + 1)
    return p, null


def gbm_nested(Xb, Xt, pL, pS, dd, rl, rs, fold_list, s):
    """GBM A/B hyperparams เหมือนกันเป๊ะ (R3 Issue-4) — mirror gbm_eval ของ 0010 (:192-194)"""
    from lightgbm import LGBMClassifier
    Xall = np.hstack([Xb, Xt])
    la, da = [], []
    for Y, tr, te in fold_list:
        yt = ((rl - rs)[tr] >= 0).astype(int); wt = np.abs((rl - rs)[tr])
        kw = dict(max_depth=3, n_estimators=150, learning_rate=0.05,
                  min_child_samples=max(20, int(tr.sum()) // 20),
                  colsample_bytree=0.8, verbose=-1, random_state=s)
        gA = LGBMClassifier(**kw).fit(Xb[tr], yt, sample_weight=wt)
        gB = LGBMClassifier(**kw).fit(Xall[tr], yt, sample_weight=wt)
        dpA = np.where(gA.predict(Xb[te]) == 1, 1, -1)
        dpB = np.where(gB.predict(Xall[te]) == 1, 1, -1)
        la.append(payoff(dpB, pL, pS, te) - payoff(dpA, pL, pS, te))
        da.append(DAYS_G[te])
    return np.concatenate(la), np.concatenate(da)


def main():
    global DAYS_G
    rows = load_joined()
    Xb, Xt, pL, pS, dd, yr, dayix, rl, rs, Nemb = arrays(rows)
    DAYS_G = dayix
    fold_list = folds(yr, dayix, Nemb)
    print(f"[SETUP] n={len(rows)} folds={[f[0] for f in fold_list]} embargo={Nemb}d "
          f"baseline=24 cols (19 FEATS + 4 shadows + log_winsec) tick=6 cols")
    print("⚠ FIELD = SIM-SEARCH 2012-2020 · lockbox/guard ไม่แตะ · in-sample = DIAGNOSTIC เท่านั้น\n")

    res = {}
    for tag, forced in (("GATED", False), ("FORCED-IN", True)):
        aggs, los = [], []
        for s in SEEDS:
            lift, days = wf_nested(Xb, Xt, pL, pS, dd, rl, rs, fold_list, s, forced)
            lo, _hi = day_ci(lift, days, _rng(f"ci_{tag}", s))
            aggs.append(float(lift.mean())); los.append(float(lo))
        res[tag] = (aggs, los)
        print(f"[LINEAR {tag}] agg min {min(aggs):+.4f} max {max(aggs):+.4f} $/ไม้ · "
              f"CI-lower min {min(los):+.4f} max {max(los):+.4f} · "
              f"seeds CI-lower>0 = {sum(1 for l in los if l > 0)}/9")

    g_aggs, g_los = [], []
    for s in SEEDS:
        gl, gd = gbm_nested(Xb, Xt, pL, pS, dd, rl, rs, fold_list, s)
        glo, _ = day_ci(gl, gd, _rng("gci", s))
        g_aggs.append(float(gl.mean())); g_los.append(float(glo))
    print(f"[GBM nested · confirmatory] agg min {min(g_aggs):+.4f} max {max(g_aggs):+.4f} · "
          f"CI-lower min {min(g_los):+.4f} · seeds CI-lower>0 = {sum(1 for l in g_los if l > 0)}/9")

    obs_lift, obs_days = wf_nested(Xb, Xt, pL, pS, dd, rl, rs, fold_list, PERM_ROOT, False)
    obs_agg = float(obs_lift.mean())
    print(f"\n[PERM-NULL linear · B={B_PERM} · seed {PERM_ROOT}] observed agg = {obs_agg:+.4f} …",
          flush=True)
    p_perm, null = perm_null(Xb, Xt, pL, pS, dd, rl, rs, fold_list, obs_agg)
    print(f"  perm-p (one-sided ≥obs) = {p_perm:.4f} · null mean {null.mean():+.4f} "
          f"p95 {np.percentile(null, 95):+.4f}")

    aggs, los = res["GATED"]; f_aggs, f_los = res["FORCED-IN"]
    pass_lin = all(l > 0 for l in los) and p_perm < 0.05
    kill_lin = all(a <= 0 for a in aggs) or not any(l > 0 for l in los)
    kill_gbm = all(a <= 0 for a in g_aggs) or not any(l > 0 for l in g_los)
    forced_pos = any(l > 0 for l in f_los)
    if pass_lin:
        verdict = "PASS — tick-price additive signal CI-backed (9/9 + perm)"
    elif kill_lin and kill_gbm and not forced_pos:
        verdict = ("KILL — no additive tick-price signal (gated ∧ GBM ∧ forced-in สอดคล้อง) · "
                   "scope-of-death ตาม PRE-REGISTRATION")
    elif forced_pos:
        verdict = "INCONCLUSIVE (gate-limited) — forced-in มี seed CI-positive แต่ gated ไม่ผ่าน"
    else:
        verdict = "NOT-PASS — ดูตาราง (ไม่เข้าเงื่อนไข KILL เต็มรูป)"
    print(f"\n[VERDICT · pipeline-owned] {verdict}")
    print(f"  [DIAG] per-feature train-corr / shadows = DIAGNOSTIC — ไม่ใช้ตัดสิน (กัน gate1-trap)")
    print(f"  ⚠ SEARCH 2012-2020 · WF≠true-OOS · KILL scope = features ชุดนี้ ไม่ใช่ tick-price ทั้งแนว")


if __name__ == "__main__":
    DAYS_G = None
    main()
