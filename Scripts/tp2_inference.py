#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tp2_inference.py — TRELLIS-010 · Card TP-2: weak-signal inference completion (tick-price arm)
Spec v2 frozen หลัง Engineer 3 รอบ (R1 B1/M1-M5 → Claude หักล้างทิศ B1 ในกรอบ linear · R2 I1-I6
→ calibration demo บังคับ · R3 PASS-with-changes: MAJOR-1 script-owned observed · MAJOR-2 ตัด
plain-perm · null-mean diagnostic · CLAIM-0015 annotation · ภาษา C-a=hedge) + Claude-Verify ทุกรอบ
budget = card 2/40 family v3

═══ PRE-REGISTRATION (ประกาศก่อนรัน · CLAIM-0016 จอง) ═══
คำถาม: lead 2 เส้นจาก TP-1/CLAIM-0015 (GBM nested point-positive 9/9 · forced-in 1/9) เป็น signal
จริงหรือ mechanical — ชี้ขาดด้วย residual-permutation inference ที่ calibration-checked
DATA: frozen เดิมทั้งหมด (tickfeat SHA 94c8e68c… · n=1486 · commit 6800f7a) — ไม่มี extraction ใหม่
STATISTICS (script emit เอง — R3 MAJOR-1 ห้าม hardcode · provisional LLM-transcribed:
  S1≈+0.1215 · S2≈−0.0742 — mismatch กับที่ emit = ต้องรายงานเป็น discovery):
  S1 = median GBM nested lift (B−A) ข้าม 9 model-seeds · protocol n_jobs=1 deterministic
  S2 = median linear FORCED-IN lift ข้าม 9 seeds — label: CONFIRMATORY-NEGATIVE
       (observed ติดลบ — ไม่ใช่ signal-path · ทำหน้าที่ KILL-confirmation · R3 I-5)
NULLS (residual-permutation ต่อ fold · train-side เท่านั้น · Freedman-Lane asymptotic —
  calibration-checked บน H0-true 20 draws [ห้ามใช้คำ exact]: NullA-OLS 1/20@0.05 median 0.625 ·
  NullB-GBMproj 1/20@0.05 median 0.505 — **both calibrate · C-a = theoretical model-match hedge**):
  S1 primary = C-a GBM-projection residual-perm · S1 secondary (รายงานคู่) = OLS-resid-perm
  S2 = OLS-resid-perm (matched linear) · plain-perm ถูกตัด (ไม่เคย calibrate กับ GBM statistic — R3 MAJOR-2)
FAMILY (enumerate ชัด · R2 I-6): m=3 = {S1-GBM-median9 · S2-forced-median9 · GATED-linear
  (TP-1 perm-p 0.8052 = สมาชิกที่ reject แล้ว)} → α = 0.05/3 = 0.0167 ต่อ statistic
  · Bonferroni ไม่แก้ null mis-calibration — calibration demo คือตัวแก้ (ทำแล้ว · --calib reproduce ได้)
  · selection-contamination ประกาศถาวร: S1 ถูกเลือกเพราะเห็น TP-1 GBM บวก
VERDICT: SIGNAL-REAL = S1(primary-null) หรือ S2 p<0.0167 → frontier open+quantified · capture=ตัดสินแยก
  KILL = ทั้งคู่ p≥0.0167 → frontier tick-price eliminated · scope-of-death: "6 tick features ·
  linear+GBM · real walk-exit · SEARCH 2012-2020 · MDE~+0.28 เหนือ null" (ไม่ใช่ tick-price ทั้งแนว ·
  ไม่ใช่ proven-zero) · CLAIM-0015 → superseded→CLAIM-0016 label "inference-completed · facts carried"
  · ไม่มี middle branch · B-escalation: p∈[α/2,2α] → ต่อ perm ถึง B=5000 (pre-registered · in-script)
DIAGNOSTIC ถาวร: null-mean elevation ≈ +0.12 = mechanical property ของ nested-lift statistic
  (H0 ก็ผลิต point-positive ได้) — กันการตีความ point-positivity เป็น signal ซ้ำ (R3 MINOR-2)
⚠ FIELD = SIM-SEARCH เท่านั้น · lockbox 2024-26 + guard 2021-23 ไม่แตะ
Usage: python tp2_inference.py           (inference เต็ม · detached แนะนำ ~2 ชม.)
       python tp2_inference.py calib     (reproduce calibration demo 20 draws — R3 promote จาก scratchpad)
"""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tp1_card as tc
from tp1_card import load_joined, arrays, folds, fit_predict, payoff, SEEDS
from direction_at_real_exit import sign_gate, _rng

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ALPHA = 0.05 / 3
B_PERM, B_ESC = 1000, 5000
PERM_ROOT = 20260714


def _kw(s, tr):
    """LightGBM params = mirror tp1_card.gbm_nested + n_jobs=1 pin (R2 m3 determinism)"""
    return dict(max_depth=3, n_estimators=150, learning_rate=0.05,
                min_child_samples=max(20, int(tr.sum()) // 20),
                colsample_bytree=0.8, verbose=-1, random_state=s, n_jobs=1)


class TP2:
    def __init__(self):
        rows = load_joined()
        (self.Xb, self.Xt, self.pL, self.pS, self.dd, self.yr,
         self.dayix, self.rl, self.rs, self.Nemb) = arrays(rows)
        tc.DAYS_G = self.dayix
        self.folds = folds(self.yr, self.dayix, self.Nemb)
        self.n = len(rows)

    # ---- caches (Model A / kA ไม่ขึ้นกับ tick — mirror tp1_card.perm_null) ----
    def build_caches(self):
        from lightgbm import LGBMClassifier
        self.PAY_A, self.KA, self.PAY_A_LIN = {}, {}, {}
        for s in SEEDS:
            for i, (Y, tr, te) in enumerate(self.folds):
                rlt, rst = self.rl[tr], self.rs[tr]
                yt = ((self.rl - self.rs)[tr] >= 0).astype(int)
                wt = np.abs((self.rl - self.rs)[tr])
                gA = LGBMClassifier(**_kw(s, tr)).fit(self.Xb[tr], yt, sample_weight=wt)
                dpA = np.where(gA.predict(self.Xb[te]) == 1, 1, -1)
                self.PAY_A[(s, i)] = np.where(dpA == 1, self.pL[te], self.pS[te])
                kA = sign_gate(self.Xb[tr], rlt - rst, self.dayix[tr], _rng(f"gA_{Y}", s))
                self.KA[(s, i)] = kA
                dpAl = fit_predict(self.Xb, kA, tr, te, rlt, rst, self.dd)
                self.PAY_A_LIN[(s, i)] = np.where(dpAl == 1, self.pL[te], self.pS[te])

    # ---- statistics (per-fold tick matrix — ให้ null ฉีด train-side perm ได้) ----
    def s1_gbm(self, tick_by_fold):
        from lightgbm import LGBMClassifier
        aggs = []
        for s in SEEDS:
            la = []
            for i, (Y, tr, te) in enumerate(self.folds):
                Xall = np.hstack([self.Xb, tick_by_fold[i]])
                yt = ((self.rl - self.rs)[tr] >= 0).astype(int)
                wt = np.abs((self.rl - self.rs)[tr])
                gB = LGBMClassifier(**_kw(s, tr)).fit(Xall[tr], yt, sample_weight=wt)
                dpB = np.where(gB.predict(Xall[te]) == 1, 1, -1)
                la.append(np.where(dpB == 1, self.pL[te], self.pS[te]) - self.PAY_A[(s, i)])
            aggs.append(float(np.concatenate(la).mean()))
        return float(np.median(aggs)), aggs

    def s2_forced(self, tick_by_fold):
        aggs = []
        for s in SEEDS:
            la = []
            for i, (Y, tr, te) in enumerate(self.folds):
                rlt, rst = self.rl[tr], self.rs[tr]
                Xall = np.hstack([self.Xb, tick_by_fold[i]])
                kB = np.r_[self.KA[(s, i)], np.ones(self.Xt.shape[1], bool)]
                dpB = fit_predict(Xall, kB, tr, te, rlt, rst, self.dd)
                la.append(np.where(dpB == 1, self.pL[te], self.pS[te]) - self.PAY_A_LIN[(s, i)])
            aggs.append(float(np.concatenate(la).mean()))
        return float(np.median(aggs)), aggs

    # ---- residual projections ต่อ fold (train-only) ----
    def proj_ols(self):
        out = {}
        for i, (Y, tr, te) in enumerate(self.folds):
            X1 = np.c_[np.ones(tr.sum()),
                       (self.Xb[tr] - self.Xb[tr].mean(0)) / (self.Xb[tr].std(0) + 1e-9)]
            X1f = np.c_[np.ones(len(self.Xb)),
                        (self.Xb - self.Xb[tr].mean(0)) / (self.Xb[tr].std(0) + 1e-9)]
            P = np.zeros_like(self.Xt)
            for j in range(self.Xt.shape[1]):
                w, *_ = np.linalg.lstsq(X1, self.Xt[tr, j], rcond=None)
                P[:, j] = X1f @ w
            out[i] = P
        return out

    def proj_gbm(self):
        from lightgbm import LGBMRegressor
        out = {}
        for i, (Y, tr, te) in enumerate(self.folds):
            P = np.zeros_like(self.Xt)
            for j in range(self.Xt.shape[1]):
                gr = LGBMRegressor(max_depth=3, n_estimators=100, learning_rate=0.1,
                                   verbose=-1, random_state=11, n_jobs=1).fit(
                    self.Xb[tr], self.Xt[tr, j])
                P[:, j] = gr.predict(self.Xb)
            out[i] = P
        return out

    def null_run(self, stat_fn, projs, obs, tag, B0=None, escalate=True):
        """residual-perm null · B-escalation in-script (pre-registered · ปิดในโหมด calib)"""
        rng = _rng(tag, PERM_ROOT)
        null = []
        t0 = time.time()
        B = B0 or B_PERM
        B_first = B
        b = 0
        while b < B:
            tbf = {}
            for i, (Y, tr, te) in enumerate(self.folds):
                P = projs[i]
                Xp = self.Xt.copy()                     # per-fold copy (fix I-4 pattern)
                rz = (self.Xt - P)[tr]
                Xp[tr] = P[tr] + rz[rng.permutation(tr.sum())]
                tbf[i] = Xp
            null.append(stat_fn(tbf)[0])
            b += 1
            if b in (10, 100, 500) or b % 1000 == 0:
                print(f"    [{tag}] {b}/{B} · {time.time() - t0:.0f}s", flush=True)
            if escalate and b == B and B == B_first:
                arr = np.array(null)
                p_now = (1 + int((arr >= obs).sum())) / (b + 1)
                if ALPHA / 2 <= p_now <= 2 * ALPHA:
                    print(f"    [{tag}] p={p_now:.4f} borderline → escalate B→{B_ESC}", flush=True)
                    B = B_ESC
        arr = np.array(null)
        p = (1 + int((arr >= obs).sum())) / (len(arr) + 1)
        return p, float(arr.mean()), len(arr)


def main():
    tp = TP2()
    print(f"[SETUP] n={tp.n} folds={[f[0] for f in tp.folds]} α={ALPHA:.4f} (m=3) "
          f"B={B_PERM} (escalate→{B_ESC} ถ้า borderline)")
    print("⚠ SIM-SEARCH · lockbox/guard ไม่แตะ · S2 = CONFIRMATORY-NEGATIVE · "
          "selection-contaminated declared\n")
    tp.build_caches()

    obs_id = {i: tp.Xt for i in range(len(tp.folds))}
    S1, s1_seeds = tp.s1_gbm(obs_id)
    S2, s2_seeds = tp.s2_forced(obs_id)
    print(f"[OBSERVED · script-owned (R3 MAJOR-1)] S1 GBM-median9 = {S1:+.4f} "
          f"(per-seed {['%+.4f' % a for a in s1_seeds]})")
    print(f"[OBSERVED] S2 forced-median9 = {S2:+.4f} (per-seed {['%+.4f' % a for a in s2_seeds]})")
    for nm, v, prov in (("S1", S1, 0.1215), ("S2", S2, -0.0742)):
        if abs(v - prov) > 5e-3:
            print(f"  ⚠ DISCOVERY: {nm} emit {v:+.4f} ≠ provisional {prov:+.4f} "
                  f"(LLM-transcribed/threading) — script-owned ชนะ · รายงานตามจริง")

    print("\n[NULL S1 primary = C-a GBM-projection residual-perm]", flush=True)
    pj_g = tp.proj_gbm()
    p1, m1, b1 = tp.null_run(tp.s1_gbm, pj_g, S1, "S1_Ca")
    print(f"  p(S1 · C-a) = {p1:.4f} · null mean {m1:+.4f} · B={b1}")
    print("[NULL S1 secondary = OLS residual-perm]", flush=True)
    pj_o = tp.proj_ols()
    p1o, m1o, b1o = tp.null_run(tp.s1_gbm, pj_o, S1, "S1_OLS")
    print(f"  p(S1 · OLS) = {p1o:.4f} · null mean {m1o:+.4f} · B={b1o}")
    print("[NULL S2 = OLS residual-perm (linear-matched)]", flush=True)
    p2, m2, b2 = tp.null_run(tp.s2_forced, pj_o, S2, "S2_OLS")
    print(f"  p(S2) = {p2:.4f} · null mean {m2:+.4f} · B={b2}")

    print(f"\n[DIAGNOSTIC ถาวร] null-mean elevation: S1-null mean = {m1:+.4f} — mechanical property "
          f"ของ nested-lift statistic (H0 ก็ให้ point-positive) · point-positivity ≠ signal")
    sig = (p1 < ALPHA) or (p2 < ALPHA)
    if sig:
        v = "SIGNAL-REAL — frontier tick-price open + quantified (capture-design = การตัดสินแยก)"
    else:
        v = ("KILL — frontier tick-price eliminated · scope: 6 features · linear+GBM · real walk-exit "
             "· SEARCH 2012-2020 (ไม่ใช่ tick-price ทั้งแนว · ไม่ใช่ proven-zero · MDE-limited) · "
             "CLAIM-0015 → superseded→CLAIM-0016 (inference-completed · facts carried)")
    print(f"\n[VERDICT · pipeline-owned] {v}")
    print(f"  p: S1(C-a)={p1:.4f} · S1(OLS x-check)={p1o:.4f} · S2={p2:.4f} · α={ALPHA:.4f}")


def calib():
    """reproduce calibration demo (R3: promote จาก scratchpad — 20 H0-true draws · B=99
    ผล frozen ที่ใช้ตัดสิน spec: NullA-OLS 1/20@.05 median .625 · NullB-GBMproj 1/20@.05 median .505)"""
    from lightgbm import LGBMRegressor
    tp = TP2()
    tp.build_caches()
    rng = np.random.default_rng(20260714)
    proj_dgp = np.zeros_like(tp.Xt)
    for j in range(tp.Xt.shape[1]):
        gr = LGBMRegressor(max_depth=3, n_estimators=100, learning_rate=0.1,
                           verbose=-1, random_state=7, n_jobs=1).fit(tp.Xb, tp.Xt[:, j])
        proj_dgp[:, j] = gr.predict(tp.Xb)
    resid_dgp = tp.Xt - proj_dgp
    Xt_real = tp.Xt
    pA_l, pB_l = [], []
    for d in range(20):
        tp.Xt = proj_dgp + resid_dgp[rng.permutation(len(resid_dgp))]
        obs, _ = tp.s1_gbm({i: tp.Xt for i in range(len(tp.folds))})
        pjA, pjB = tp.proj_ols(), tp.proj_gbm()
        pA, mA, _n = tp.null_run(tp.s1_gbm, pjA, obs, f"calibA_{d}", B0=99, escalate=False)
        pB, mB, _n = tp.null_run(tp.s1_gbm, pjB, obs, f"calibB_{d}", B0=99, escalate=False)
        pA_l.append(pA); pB_l.append(pB)
        print(f"  draw{d:02d}: obs={obs:+.4f} A p={pA:.3f} B p={pB:.3f}", flush=True)
    tp.Xt = Xt_real
    for nm, p in (("NullA-OLS", np.array(pA_l)), ("NullB-GBMproj", np.array(pB_l))):
        print(f"  {nm}: p<0.05={int((p < .05).sum())}/20 · p<0.10={int((p < .10).sum())}/20 · "
              f"median={np.median(p):.3f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "calib":
        calib()
    else:
        main()
