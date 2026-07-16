#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
es2_card.py — TRELLIS-010 · Card ES-2: tick-DC event-stream direction-at-real-exit
Spec v2 frozen หลัง Engineer 3 รอบ + Claude-Verify ทุกรอบ · budget = card 4/40 family v3

═══ PRE-REGISTRATION (ประกาศก่อนรัน · CLAIM-0018 จอง) ═══
HYPOTHESIS: DC event-stream บน **bid tick stream** (intrabar reversal structure ที่ M1 closes
  มองไม่เห็น — cross-corr tick↔M1 @0.1aw = 0.12 จาก dump) มี additive direction info ที่
  real walk-exit เหนือ baseline-20 — form สุดท้ายของ in-hand event lane (pre-registered ใน
  scope-of-death ของ CLAIM-0016/0017)
COMPARISON CLAIM [M-C]: **near-controlled กับ ES-1** (baseline-20 + gate + protocol เท่ากันเป๊ะ ·
  feature ต่าง 1 slot: asym→tshare เพราะ asym degenerate-by-construction) — ไม่เคลม resolution-ล้วน
POPULATION AUDIT [P1]: card emit overlap ของ ES-2 joined population vs ES-1 (CLAIM-0017 n=1486):
  |∩| · Jaccard · dropped-diff — overlap < 100% → เคลม downgrade เป็น "baseline-matched-on-shared-N"
  (ประกาศใน output · ห้ามเงียบ)
FEATURES: 8 tick-DC จาก `es2_tickdc_2012_2020.csv` (frozen SHA · extractor แยกไฟล์ [M-D] ·
  guards ในตัว: G1-SOFT≥99.9 · UNDEF==0 · slice-discipline + smoke NEG-CTRL boundary-read [P2])
GATE: S1 = median-9 linear FORCED-IN lift over **baseline-20** (19-feat + rjR — เท่า ES-1 เป๊ะ) ·
  null = OLS-residual-perm · S2 = median-9 GBM nested lift · null = GBM-projection residual-perm ·
  B=1000 + escalation [α/2,2α]→5000 · **m=2 α=0.025 · gate = S1+S2 เท่านั้น** · single-card
  (staged-gate ถูกตัด — R2 MAJOR-A interaction blind-spot)
CALIBRATION [P3]: `calib` mode — 15 H0-true draws ทั้ง S1/S2 บน 8 features ของ card นี้เอง
  (elevation เป็น per-feature-set — CLAIM-0016/0017) · ต้องผ่าน (~1/15@0.05) ก่อน freeze prediction
DIAGNOSTICS (DESCRIPTIVE-ONLY · non-gating · ห้าม argue signal post-hoc): nested-lift over
  baseline-28 (+8 M1-DC — resolution cross-check) · drop-one-scale · GATED-linear · redundancy
  (cross-corr tick↔M1: 0.12/0.43/0.72) · dur_tick shadow [P4] · leave-max-out = z-profile report
VERDICT: PASS = S1 หรือ S2 p<0.025 → candidate (capture แยก) · KILL = ทั้งคู่ ≥0.025 →
  scope-of-death: "8 tick-DC encodings (δ∈{0.1,0.25,0.5}aw · bid-only · classic dissection ·
  tshare/dur wall-time) · linear+GBM · real walk-exit · SEARCH 2012-2020 · sensitivity-floor
  ตาม emit · not-detected ≠ falsified (CLAIM-0013) · ไม่ใช่ event-stream ทั้งแนว · ไม่ใช่
  proven-zero" · "4 in-hand event forms tested" = FRONTIER note (ไม่ใช่ falsification [M-3])
  · ไม่มี middle branch · MDE/null-p95 emit
⚠ FIELD = SIM-SEARCH เท่านั้น · lockbox 2024-26 + guard 2021-23 ไม่แตะ
Usage: python es2_card.py calib | python es2_card.py
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tp2_inference as t2
import es1_card as e1
from tp1_card import folds, fit_predict, SEEDS
from direction_at_real_exit import sign_gate, _rng

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
ES2_CSV = ROOT / "Research/h0/es2_tickdc_2012_2020.csv"
ES2_SHA = ROOT / "Research/h0/es2_tickdc_2012_2020.sha256"
ES2_COLS = ["al_010", "al_025", "al_050", "os_010", "os_025", "os_050",
            "tshare_010", "dur_wall_025"]
ALPHA = 0.025


class ES2(e1.ES1):
    def __init__(self):                                   # override — tick-DC จาก frozen CSV
        sha = hashlib.sha256(ES2_CSV.read_bytes()).hexdigest()
        assert sha == ES2_SHA.read_text().split()[0], "es2_tickdc SHA mismatch"
        tdc = {}
        for r in csv.DictReader(open(ES2_CSV, encoding="utf-8")):
            if r.get("al_010") not in (None, ""):
                tdc[r["date"]] = [float(r[c]) for c in ES2_COLS]
        rows = e1.load_es()                               # ES-1 loader: baseline-20 + M1-DC + guards
        # join tick-DC + [P1] population-overlap audit vs ES-1 population
        es1_dates, kept = [], []
        from brain_v1_run import load_ctx
        ctx = load_ctx()
        uniq = np.unique(ctx["day"])
        dts_of = {jx: str(np.datetime64(int(di), "D")) for jx, di in enumerate(uniq.tolist())}
        for r in rows:
            dts = dts_of[r["dayix"]]
            es1_dates.append(dts)
            if dts in tdc:
                r["tdc"] = tdc[dts]
                r["date"] = dts
                kept.append(r)
        inter = len(kept); union = len(set(es1_dates) | set(tdc))
        jac = inter / union if union else 0.0
        print(f"[P1 · POPULATION AUDIT] ES-1 n={len(rows)} · ES-2 joined n={inter} · "
              f"Jaccard={jac:.4f} · dropped={sorted(set(es1_dates) - set(tdc))[:5]}")
        if inter < len(rows):
            print(f"  ⚠ overlap < 100% → เคลม downgrade: 'baseline-matched-on-shared-N' (declared)")
        else:
            print(f"  overlap 100% — near-controlled comparison ยืน (membership asserted จริง)")
        self.Xb = np.array([list(r["feat"]) + [r["rjr"]] for r in kept], float)   # 20
        self.Xm1 = np.array([r["es"] for r in kept], float)                       # 8 M1-DC (descr-28)
        self.Xt = np.array([r["tdc"] for r in kept], float)                       # 8 tick-DC
        self.pL = np.array([r["pL"] for r in kept])
        self.pS = np.array([r["pS"] for r in kept])
        self.dd = np.array([r["d"] for r in kept])
        self.yr = np.array([r["yr"] for r in kept])
        self.dayix = np.array([r["dayix"] for r in kept])
        Rv = np.array([r["R"] for r in kept])
        self.rl, self.rs = self.pL / Rv, self.pS / Rv
        self.Nemb = max(r["hold"] for r in kept)
        import tp1_card as t1
        t1.DAYS_G = self.dayix
        self.folds = folds(self.yr, self.dayix, self.Nemb)
        self.n = len(kept)


def main():
    t2.ALPHA = ALPHA
    e1.ALPHA = ALPHA
    es = ES2()
    print(f"[SETUP] n={es.n} folds={[f[0] for f in es.folds]} baseline=20 tick-DC=8 "
          f"α={ALPHA} (m=2 · gate = S1+S2 เท่านั้น)")
    print("⚠ SIM-SEARCH · lockbox/guard ไม่แตะ · diagnostics = DESCRIPTIVE-ONLY non-gating\n")
    es.build_caches()
    obs = {i: es.Xt for i in range(len(es.folds))}
    S2_obs, s2_seeds = es.s1_gbm(obs)                     # S2 = GBM nested (naming จาก tp2)
    S1_obs, s1_seeds = es.s2_forced(obs)                  # S1 = linear forced-in
    print(f"[OBSERVED · script-owned] S1 linear-forced-median9 = {S1_obs:+.4f} "
          f"(per-seed {['%+.4f' % a for a in s1_seeds]})")
    print(f"[OBSERVED] S2 GBM-nested-median9 = {S2_obs:+.4f} "
          f"(per-seed {['%+.4f' % a for a in s2_seeds]})")

    # ---- DIAGNOSTICS (DESCRIPTIVE-ONLY) ----
    Xt_full = es.Xt
    print("\n[DIAG] drop-one-scale (S1' เมื่อตัด al+os ของ scale นั้น · tshare/dur คงอยู่):")
    for si, s in enumerate([0.1, 0.25, 0.5]):
        keep = [c for c in range(8) if c not in (si, 3 + si)]
        es.Xt = Xt_full[:, keep]
        v, _ = es.s2_forced({i: es.Xt for i in range(len(es.folds))})
        print(f"    drop δ={s}: S1' = {v:+.4f} (Δ {v - S1_obs:+.4f})")
    es.Xt = Xt_full
    # baseline-28 nested (resolution cross-check): B28 = [Xb + Xm1] เป็น baseline · +tick = model B
    Xb_save = es.Xb
    es.Xb = np.hstack([Xb_save, es.Xm1])
    es.build_caches()
    S1_28, _ = es.s2_forced({i: es.Xt for i in range(len(es.folds))})
    S2_28, _ = es.s1_gbm({i: es.Xt for i in range(len(es.folds))})
    print(f"[DIAG] nested over baseline-28 (+M1-DC): S1 = {S1_28:+.4f} · S2 = {S2_28:+.4f} "
          f"(resolution-specific increment · descriptive)")
    es.Xb = Xb_save
    es.build_caches()
    oz = (Xt_full[:, 3] - Xt_full[:, 3].mean()) / Xt_full[:, 3].std()
    print(f"[DIAG] os@0.1 z-profile: |z|max={np.abs(oz).max():.2f}sd · |z|>4sd = "
          f"{int((np.abs(oz) > 4).sum())} วัน (report-only · ไม่ recompute)")
    s0 = SEEDS[0]
    Xall = np.hstack([es.Xb, es.Xt])
    la = []
    for i, (Y, tr, te) in enumerate(es.folds):
        rlt, rst = es.rl[tr], es.rs[tr]
        kB = sign_gate(Xall[tr], rlt - rst, es.dayix[tr], _rng(f"gB_{Y}", s0))
        dpB = fit_predict(Xall, kB, tr, te, rlt, rst, es.dd)
        la.append(np.where(dpB == 1, es.pL[te], es.pS[te]) - es.PAY_A_LIN[(s0, i)])
    print(f"[DIAG] GATED-linear lift (seed {s0}) = {np.concatenate(la).mean():+.4f} — non-gating")

    # ---- NULLS (gate จริง) ----
    print(f"\n[NULL S1 = OLS residual-perm · B={t2.B_PERM}]", flush=True)
    pj_o = es.proj_ols()
    p1, m1, b1, q1 = es.null_run(es.s2_forced, pj_o, S1_obs, "ES2_S1")
    print(f"  p(S1) = {p1:.4f} · null mean {m1:+.4f} · null-p95 {q1:+.4f} · B={b1}")
    print(f"[NULL S2 = GBM-projection residual-perm · B={t2.B_PERM}]", flush=True)
    pj_g = es.proj_gbm()
    p2, m2, b2, q2 = es.null_run(es.s1_gbm, pj_g, S2_obs, "ES2_S2")
    print(f"  p(S2) = {p2:.4f} · null mean {m2:+.4f} · null-p95 {q2:+.4f} · B={b2}")
    print(f"\n[DIAG ถาวร] null-mean: S1 {m1:+.4f} · S2 {m2:+.4f} — elevation per-feature-set "
          f"(CLAIM-0016/0017) · point-positivity ≠ signal")
    print(f"[MDE/sensitivity-floor emit] S1 floor ≈ {q1:+.4f} · S2 floor ≈ {q2:+.4f} $/ไม้")
    sig = (p1 < ALPHA) or (p2 < ALPHA)
    if sig:
        v = "PASS — tick-DC additive signal (candidate · capture = ตัดสินแยก)"
    else:
        v = ("KILL — 8 tick-DC encodings (δ∈{0.1,0.25,0.5}aw · bid-only · classic dissection · "
             "tshare/dur wall-time) · linear+GBM · real walk-exit · SEARCH — not-detected ≠ "
             "falsified (CLAIM-0013) · ไม่ใช่ event-stream ทั้งแนว · ไม่ใช่ proven-zero")
    print(f"\n[VERDICT · pipeline-owned] {v}")
    print(f"  p: S1={p1:.4f} · S2={p2:.4f} · α={ALPHA}")


def calib():
    """[P3] 15 H0-true draws ทั้ง S1/S2 บน 8 tick-DC ของ card นี้เอง (mirror es1_card.calib)"""
    from lightgbm import LGBMRegressor
    t2.ALPHA = ALPHA
    es = ES2()
    es.build_caches()
    rng = np.random.default_rng(20260716)
    proj_dgp = np.zeros_like(es.Xt)
    for j in range(es.Xt.shape[1]):
        gr = LGBMRegressor(max_depth=3, n_estimators=100, learning_rate=0.1,
                           verbose=-1, random_state=7, n_jobs=1).fit(es.Xb, es.Xt[:, j])
        proj_dgp[:, j] = gr.predict(es.Xb)
    resid = es.Xt - proj_dgp
    Xt_real = es.Xt
    res = {"S1": [], "S2": []}
    for d in range(15):
        es.Xt = proj_dgp + resid[rng.permutation(len(resid))]
        o1, _ = es.s2_forced({i: es.Xt for i in range(len(es.folds))})
        o2, _ = es.s1_gbm({i: es.Xt for i in range(len(es.folds))})
        pjo, pjg = es.proj_ols(), es.proj_gbm()
        p1, m1, *_ = es.null_run(es.s2_forced, pjo, o1, f"c2S1_{d}", B0=99, escalate=False)
        p2, m2, *_ = es.null_run(es.s1_gbm, pjg, o2, f"c2S2_{d}", B0=99, escalate=False)
        res["S1"].append(p1); res["S2"].append(p2)
        print(f"  draw{d:02d}: S1 obs={o1:+.4f} p={p1:.3f} (nm {m1:+.4f}) | "
              f"S2 obs={o2:+.4f} p={p2:.3f} (nm {m2:+.4f})", flush=True)
    es.Xt = Xt_real
    for k, p in res.items():
        p = np.array(p)
        print(f"[CALIB {k}] p<0.05 = {int((p < .05).sum())}/15 (คาด ~1) · p<0.10 = "
              f"{int((p < .10).sum())}/15 · median = {np.median(p):.3f} — order-of-magnitude")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "calib":
        calib()
    else:
        main()
