#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
es1_card.py — TRELLIS-010 · Card ES-1: intraday event-stream (DC multi-scale) direction-at-real-exit
Spec v4 frozen หลัง Engineer 4 รอบ (R1 occupancy/redundancy/calib · R2 δ-set บน ES-window จริง +
MAJOR A-C · R3 C1-C6 + two-field adjudication · R4 PASS-with-changes P1-P4) + Claude-Verify ทุกรอบ
budget = card 3/40 family v3

═══ PRE-REGISTRATION (ประกาศก่อนรัน · CLAIM-0017 จอง) ═══
HYPOTHESIS: path-dependent multi-scale state จาก DC dissection (running-extremum-since-last-DC =
  stateful scan ที่ GBM สร้างจาก point-features ไม่ได้) บน M1 session closes เดียวกัน มี additive
  direction info ที่ real walk-exit เหนือ baseline A — คือครึ่ง "M1-functional" ของ frontier แถว
  nonlinear/event-stream (positioning ตรง: recycled DC features [δ=0.5 = C9-frozen system δ] +
  real-exit label ใหม่ + multi-scale — ไม่เคลม new-family · C9/C10 ตาย day-level ใต้ h0-framework
  = คนละ label)
FEATURES (8 · จาก session closes hour 1-22 ของวันเทรด · 01:00 → close ของ signal bar j · DC def
  = classic dissection ตรง c9_dc_features.dc_state_at ที่ verify จาก arXiv 0809.1040 full text):
  δ ∈ {0.1, 0.25, 0.5}×asian_width (occupancy P&L-free: n_dc med 35/9/3 · UNDEF 0.0% ทุก scale ·
  1.0aw ตัด [single-mode 74%] · heritage: 0.5 = C9): dc_align_δ = mode×d · dc_os_δ = overshoot/δ
  + dc_asym@0.1 = (up_dc−down_dc)/n_dc (0 ถ้า n_dc=0 · ABSOLUTE convention ไม่ ×d — ตั้งใจ) ·
  dc_dur@0.25 = bars-in-current-mode/(len−1) (0 ถ้า UNDEF · denominator pinned len−1 [C3])
  [C2 DECLARED: asym@0.1/dur@0.25 = data-informed (occupancy-guided บน SEARCH เดียวกัน) =
  selection-contamination ถาวร · a-priori rationale คู่: asym ต้องการ events มากสุด→0.1 ·
  dur วัด persistence ที่ mid→0.25]
  [P2: UNDEF assert ==0 exact + encoding ครบทุก feature = 0 — วัดจริง UNDEF 0.0% · min n_dc@0.1=5
  → asserts = vacuous fail-loud guards ในประชากรปัจจุบัน (เผื่อ population เปลี่ยน) · dc_os=0
  ในประชากร = at-confirmation เสมอ (98/56/40 วัน) ไม่ใช่ undef]
REDUNDANCY DECLARATION [C1/P1 · DESCRIPTIVE-ONLY · non-gating]: dc_align vs momentum block —
  linear-effective (raw/R ตรง dir_features) R² = 0.044/0.126/0.188 · GBM-effective (5-fold OOF ·
  วัดเทียบ 5-feat momentum = lower bound ของ baseline-A-20 absorption) = 0.21-0.38 / ~0.64 / ~0.61
  (δ=0.1 fold/seed-sensitive → range · load-bearing = ranking 0.1-ต่ำสุด + GBM≫linear เสถียร 8/8)
BASELINE A [C6] = 19 dir_features + rjR (bar-j range/aw · h0_tickfeat v2 frozen SHA) = 20 cols
GATE [P3]: **S1 + S2 เท่านั้น (m=2 · α=0.025)** — S1 = median-9-seed linear FORCED-IN lift (B−A)
  null = OLS-residual-perm · S2 = median-9-seed GBM nested lift · null = GBM-projection
  residual-perm · B=1000 + escalation [α/2,2α]→5000 · diagnostics ทุกตัว (GATED-linear · redundancy
  · drop-one-scale · GBM importance · leave-max-out) = DESCRIPTIVE-ONLY นอก Bonferroni —
  **ห้ามใช้ argue signal/inclusion post-hoc · gate จริง = S1/S2 pre-registered เท่านั้น**
CALIBRATION [P4]: `calib` mode ครอบ **ทั้ง S1 และ S2** ของ card นี้เอง (ไม่ยืม log TP-2) ·
  15 H0-true draws (DGP = GBM-proj(ES|A) + shuffled resid) · B0=99 · emit FP-rate@0.05 +
  null-mean ต่อ statistic (ภาษา order-of-magnitude) · ต้องรันก่อน freeze prediction
VERDICT: PASS = S1 หรือ S2 p<0.025 → candidate (capture แยก) · KILL = ทั้งคู่ ≥0.025 → emit
  MDE/sensitivity-floor + scope-of-death: "8 DC encodings (δ∈{0.1,0.25,0.5}aw · M1 closes) ·
  linear+GBM · real walk-exit · SEARCH 2012-2020 · power-context ตามที่ emit · not-detected ≠
  falsified (CLAIM-0013) · root-cause explanation" — ไม่ใช่ event-stream ทั้งแนว · ไม่ใช่ tick-DC ·
  ไม่ใช่ proven-zero · ไม่มี middle branch
GUARDS: slice-discipline check (54 entries — corruption หลัง j ถูก slice ตัดโดยโครงสร้าง · M2) ·
  **no-lookahead power = smoke NEG-CTRL** (planted span+20 ต้องยิง) · leverage: dc_os@0.1 |z|max
  9.46sd · 13 วัน >4sd → **รายงานเป็น z-profile เท่านั้น ไม่ recompute S1 sans-max** (ตัด row
  เปลี่ยน fold-structure · M3 execution-review) · R-match assert ผูก ES กับ build_rows ทุกไม้
⚠ FIELD = SIM-SEARCH เท่านั้น · lockbox 2024-26 + guard 2021-23 ไม่แตะ
Usage: python es1_card.py smoke | python es1_card.py calib | python es1_card.py
"""
import csv
import hashlib
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tp2_inference as t2
from tp1_card import folds, fit_predict, SEEDS
from direction_at_real_exit import sign_gate, _rng, build_rows
from brain_v1_run import load_ctx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
TICKFEAT = ROOT / "Research/h0/h0_tickfeat_2012_2020.csv"
TICKSHA = ROOT / "Research/h0/h0_tickfeat_2012_2020.sha256"
SCALES = [0.1, 0.25, 0.5]
ES_COLS = ["al_010", "al_025", "al_050", "os_010", "os_025", "os_050", "asym_010", "dur_025"]
ALPHA = 0.025                        # m=2 [P3]
_TEST_SPAN_EXTRA = 0                 # test-hook negative-control (production ต้อง 0 · assert ใน main)


def dissect(closes, delta):
    """classic DC dissection — mirror c9_dc_features.dc_state_at:51-82 + track up/down flips
    คืน (mode, os_units, n_dc, up_dc, down_dc, last_ev_idx)"""
    mode, n_dc, up_dc, down_dc = 0, 0, 0, 0
    hi = lo = closes[0]
    dcc = np.nan
    last_ev = -1
    for i, c in enumerate(closes):
        if mode == 0:
            hi, lo = max(hi, c), min(lo, c)
            if c >= lo + delta:
                mode, dcc, hi = 1, c, c; n_dc += 1; up_dc += 1; last_ev = i
            elif c <= hi - delta:
                mode, dcc, lo = -1, c, c; n_dc += 1; down_dc += 1; last_ev = i
        elif mode == 1:
            hi = max(hi, c)
            if c <= hi - delta:
                mode, dcc, lo = -1, c, c; n_dc += 1; down_dc += 1; last_ev = i
        else:
            lo = min(lo, c)
            if c >= lo + delta:
                mode, dcc, hi = 1, c, c; n_dc += 1; up_dc += 1; last_ev = i
    assert up_dc + down_dc == n_dc, "DC decomposition broken (up+down != n_dc)"
    os_u = 0.0 if mode == 0 else ((closes[-1] - dcc) / delta if mode == 1 else (dcc - closes[-1]) / delta)
    return mode, os_u, n_dc, up_dc, down_dc, last_ev


def es_features(closes, d, aw):
    """8 ES features จาก session closes[0..j] (สิ้นสุด close ของ signal bar j — as-of glossary)
    negative-control (smoke): planted bug = caller ส่ง slice ที่อ่านเกิน j → features ต้องเปลี่ยน"""
    cl = closes
    out, undef = [], 0
    aux = {}
    for s in SCALES:
        mode, os_u, n_dc, up, dn, last_ev = dissect(cl, s * aw)
        if mode == 0:
            undef += 1
        aux[s] = (n_dc, up, dn, last_ev)
        out.append(float(mode * d))
    for s in SCALES:
        mode, os_u, *_ = dissect(cl, s * aw)
        out.append(float(os_u))
    n_dc, up, dn, _ = aux[0.1]
    out.append(float((up - dn) / n_dc) if n_dc > 0 else 0.0)
    _, _, _, last_ev = aux[0.25]
    out.append(float((len(cl) - 1 - last_ev) / max(1, len(cl) - 1)) if last_ev >= 0 else 0.0)
    return out, undef


def load_es():
    """build rows (label+19feat จาก 0010) + rjR + ES features — R-match assert ทุกไม้"""
    sha = hashlib.sha256(TICKFEAT.read_bytes()).hexdigest()
    assert sha == TICKSHA.read_text().split()[0], "h0_tickfeat SHA mismatch"
    rjr = {r["date"]: float(r["rjR"]) for r in csv.DictReader(
        ln for ln in open(TICKFEAT, encoding="utf-8") if not ln.startswith("#"))
        if r.get("rjR") not in (None, "",)}
    ctx = load_ctx()
    rows = build_rows(ctx)
    day, hourv = ctx["day"], ctx["hour"]
    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(day)]
    dts_of = {jx: str(np.datetime64(int(di), "D")) for jx, di in enumerate(uniq.tolist())}
    kept, undef_total, guard_done, guard_fail = [], 0, 0, []
    for r in rows:
        jx = r["dayix"]
        dts = dts_of[jx]
        i0, i1 = int(fidx[jx]), int(bnd[jx])
        m = (hourv[i0:i1] >= 1) & (hourv[i0:i1] < 22)
        gi = np.arange(i0, i1)[m]
        f = ctx["facts"][dts]
        k = ctx["pos"][dts + "T" + f["entry_time"]]
        pk = int(np.where(gi == k)[0][0])
        a = pk - 1
        ash, asl = ctx["lv"][dts]
        assert abs((ash - asl) - r["R"]) < 1e-9, f"R-match FAIL {dts}"   # ผูก ES กับ walker
        closes = ctx["c"][gi[:a + 1]].tolist()
        feats, undef = es_features(closes, r["d"], r["R"])
        undef_total += undef
        if dts not in rjr:
            continue
        r["es"] = feats
        r["rjr"] = rjr[dts]
        # ES future-mask guard (sample): corrupt closes หลัง j → ต้อง invariant (slice < j+1)
        if guard_done < 54:
            closes_bad = ctx["c"][gi[:min(len(gi), a + 31)]].copy()
            closes_bad[a + 1:] = 9e9
            f2, _ = es_features(closes_bad[:a + 1].tolist(), r["d"], r["R"])
            if any(abs(x - y) > 1e-12 for x, y in zip(feats, f2)):
                guard_fail.append(dts)
            guard_done += 1
        kept.append(r)
    assert undef_total == 0, f"UNDEF != 0 ({undef_total}) — ประชากรเปลี่ยนจากที่ freeze · STOP"
    assert not guard_fail, f"ES SLICE-DISCIPLINE FAIL: {guard_fail}"
    # [M2 execution-review]: guard นี้ = slice-discipline check (corruption หลัง j ถูก slice ตัดก่อน
    # เข้า es_features โดยโครงสร้าง) — power ของ no-lookahead พิสูจน์ที่ smoke NEG-CTRL (planted span+20)
    print(f"[ES] rows={len(kept)}/{len(rows)} (rjR-missing dropped={len(rows) - len(kept)}) · "
          f"UNDEF==0 ✓ · slice-discipline ✓ {guard_done} (no-lookahead power = smoke NEG-CTRL)")
    return kept


class ES1(t2.TP2):
    def __init__(self):                                   # override — ไม่โหลด tick ของ TP-1
        rows = load_es()
        self.Xb = np.array([list(r["feat"]) + [r["rjr"]] for r in rows], float)   # 19+rjR = 20
        self.Xt = np.array([r["es"] for r in rows], float)                        # 8 ES
        self.pL = np.array([r["pL"] for r in rows])
        self.pS = np.array([r["pS"] for r in rows])
        self.dd = np.array([r["d"] for r in rows])
        self.yr = np.array([r["yr"] for r in rows])
        self.dayix = np.array([r["dayix"] for r in rows])
        Rv = np.array([r["R"] for r in rows])
        self.rl, self.rs = self.pL / Rv, self.pS / Rv
        self.Nemb = max(r["hold"] for r in rows)
        import tp1_card as t1
        t1.DAYS_G = self.dayix
        self.folds = folds(self.yr, self.dayix, self.Nemb)
        self.n = len(rows)

    def null_run(self, stat_fn, projs, obs, tag, B0=None, escalate=True):
        """mirror t2.TP2.null_run เป๊ะ + เพิ่ม p95 ใน return (MDE/sensitivity-floor emit —
        pre-registration บังคับ · ไม่แตะ semantics: p/mean เท่าเดิม)"""
        rng = _rng(tag, t2.PERM_ROOT)
        null = []
        t0 = time.time()
        B = B0 or t2.B_PERM
        B_first = B
        b = 0
        while b < B:
            tbf = {}
            for i, (Y, tr, te) in enumerate(self.folds):
                P = projs[i]
                Xp = self.Xt.copy()
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
                    print(f"    [{tag}] p={p_now:.4f} borderline → escalate B→{t2.B_ESC}", flush=True)
                    B = t2.B_ESC
        arr = np.array(null)
        p = (1 + int((arr >= obs).sum())) / (len(arr) + 1)
        return p, float(arr.mean()), len(arr), float(np.percentile(arr, 95))


def main():
    assert _TEST_SPAN_EXTRA == 0, "test hook ต้องเป็น 0 ใน production"
    t2.ALPHA = ALPHA                                      # m=2 ของ card นี้ (declared override)
    es = ES1()
    print(f"[SETUP] n={es.n} folds={[f[0] for f in es.folds]} baseline=20 (19+rjR) ES=8 "
          f"α={ALPHA} (m=2 · gate = S1+S2 เท่านั้น [P3])")
    print("⚠ SIM-SEARCH · lockbox/guard ไม่แตะ · diagnostics ทั้งหมด = DESCRIPTIVE-ONLY non-gating\n")
    es.build_caches()
    obs_id = {i: es.Xt for i in range(len(es.folds))}
    S2_obs, s2_seeds = es.s1_gbm(obs_id)                  # S2 = GBM nested (ชื่อ method จาก tp2)
    S1_obs, s1_seeds = es.s2_forced(obs_id)               # S1 = linear forced-in
    print(f"[OBSERVED · script-owned] S1 linear-forced-median9 = {S1_obs:+.4f} "
          f"(per-seed {['%+.4f' % a for a in s1_seeds]})")
    print(f"[OBSERVED] S2 GBM-nested-median9 = {S2_obs:+.4f} "
          f"(per-seed {['%+.4f' % a for a in s2_seeds]})")

    # ---- DIAGNOSTICS (DESCRIPTIVE-ONLY · non-gating) ----
    print("\n[DIAG · non-gating] drop-one-scale (S1 observed เมื่อตัด features ของ scale นั้น):")
    Xt_full = es.Xt
    for si, s in enumerate(SCALES):
        keep = [c for c in range(8) if c not in (si, 3 + si)]
        es.Xt = Xt_full[:, keep]                 # s2_forced ใช้ self.Xt.shape[1] สร้าง mask
        v, _ = es.s2_forced({i: es.Xt for i in range(len(es.folds))})
        print(f"    drop δ={s}: S1' = {v:+.4f} (Δ {v - S1_obs:+.4f})")
    es.Xt = Xt_full
    oz = (es.Xt[:, 3] - es.Xt[:, 3].mean()) / es.Xt[:, 3].std()
    imax = int(np.argmax(np.abs(oz)))
    mask = np.ones(es.n, bool); mask[imax] = False
    print(f"[DIAG] leave-max-out (os@0.1 |z|max={abs(oz[imax]):.2f}sd · |z|>4sd = "
          f"{int((np.abs(oz) > 4).sum())} วัน): จะรายงานผ่าน per-seed sensitivity ใน review "
          f"(ตัด population กลาง pipeline เปลี่ยน folds — รายงาน z-профиль แทน)")
    s0 = SEEDS[0]
    Xall = np.hstack([es.Xb, es.Xt])
    la = []
    for i, (Y, tr, te) in enumerate(es.folds):
        rlt, rst = es.rl[tr], es.rs[tr]
        kB = sign_gate(Xall[tr], rlt - rst, es.dayix[tr], _rng(f"gB_{Y}", s0))
        dpB = fit_predict(Xall, kB, tr, te, rlt, rst, es.dd)
        la.append(np.where(dpB == 1, es.pL[te], es.pS[te]) - es.PAY_A_LIN[(s0, i)])
    print(f"[DIAG] GATED-linear lift (seed {s0}) = {np.concatenate(la).mean():+.4f} "
          f"— DESCRIPTIVE-ONLY นอก Bonferroni · ห้าม argue signal post-hoc")

    # ---- NULLS (gate จริง) ----
    print(f"\n[NULL S1 = OLS residual-perm · B={t2.B_PERM}]", flush=True)
    pj_o = es.proj_ols()
    p1, m1, b1, q1 = es.null_run(es.s2_forced, pj_o, S1_obs, "ES1_S1")
    print(f"  p(S1) = {p1:.4f} · null mean {m1:+.4f} · null-p95 {q1:+.4f} · B={b1}")
    print(f"[NULL S2 = GBM-projection residual-perm · B={t2.B_PERM}]", flush=True)
    pj_g = es.proj_gbm()
    p2, m2, b2, q2 = es.null_run(es.s1_gbm, pj_g, S2_obs, "ES1_S2")
    print(f"  p(S2) = {p2:.4f} · null mean {m2:+.4f} · null-p95 {q2:+.4f} · B={b2}")
    print(f"\n[DIAG ถาวร] null-mean: S1 {m1:+.4f} · S2 {m2:+.4f} — nested-lift point-positivity ≠ "
          f"signal (บทเรียน CLAIM-0016)")
    print(f"[MDE/sensitivity-floor emit] ต้อง observed ≳ null-p95 จึงจะ detect ที่ α นี้: "
          f"S1 floor ≈ {q1:+.4f} · S2 floor ≈ {q2:+.4f} $/ไม้ (order-of-magnitude)")
    sig = (p1 < ALPHA) or (p2 < ALPHA)
    if sig:
        v = "PASS — ES additive signal (candidate · capture = ตัดสินแยก)"
    else:
        v = ("KILL — 8 DC encodings (δ∈{0.1,0.25,0.5}aw · M1 closes) · linear+GBM · real walk-exit "
             "· SEARCH — not-detected ≠ falsified (CLAIM-0013) · ไม่ใช่ event-stream ทั้งแนว · "
             "ไม่ใช่ tick-DC · ไม่ใช่ proven-zero · sensitivity-floor ≈ null-p95 (ดู emit)")
    print(f"\n[VERDICT · pipeline-owned] {v}")
    print(f"  p: S1={p1:.4f} · S2={p2:.4f} · α={ALPHA}")


def calib():
    """[P4] calibration ครอบทั้ง S1 (linear-forced/OLS-null) และ S2 (GBM/GBM-proj-null) —
    15 H0-true draws · B0=99 · order-of-magnitude · DGP = GBM-proj(ES|A) + shuffled resid"""
    from lightgbm import LGBMRegressor
    es = ES1()
    es.build_caches()
    rng = np.random.default_rng(20260715)
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
        p1, m1, *_ = es.null_run(es.s2_forced, pjo, o1, f"cS1_{d}", B0=99, escalate=False)
        p2, m2, *_ = es.null_run(es.s1_gbm, pjg, o2, f"cS2_{d}", B0=99, escalate=False)
        res["S1"].append(p1); res["S2"].append(p2)
        print(f"  draw{d:02d}: S1 obs={o1:+.4f} p={p1:.3f} (nm {m1:+.4f}) | "
              f"S2 obs={o2:+.4f} p={p2:.3f} (nm {m2:+.4f})", flush=True)
    es.Xt = Xt_real
    for k, p in res.items():
        p = np.array(p)
        print(f"[CALIB {k}] p<0.05 = {int((p < .05).sum())}/15 (คาด ~1) · p<0.10 = "
              f"{int((p < .10).sum())}/15 · median = {np.median(p):.3f} — order-of-magnitude")


def smoke():
    """negative-control: planted span-bug (อ่านเกิน j) ต้องทำให้ future-mask ยิง"""
    es = ES1()                                            # future-mask 54 entries รันใน load_es แล้ว
    ctx = load_ctx()
    rows = build_rows(ctx)
    r = rows[0]
    day, hourv = ctx["day"], ctx["hour"]
    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(day)]
    jx = r["dayix"]
    i0, i1 = int(fidx[jx]), int(bnd[jx])
    m = (hourv[i0:i1] >= 1) & (hourv[i0:i1] < 22)
    gi = np.arange(i0, i1)[m]
    dts = str(np.datetime64(int(uniq[jx]), "D"))
    k = ctx["pos"][dts + "T" + ctx["facts"][dts]["entry_time"]]
    a = int(np.where(gi == k)[0][0]) - 1
    closes = ctx["c"][gi[:a + 1]].tolist()
    f_ok, _ = es_features(closes, r["d"], r["R"])
    bad = ctx["c"][gi[:a + 31]].copy(); bad[a + 1:] = bad[a + 1:] + 50.0
    f_bug, _ = es_features(bad[:a + 1 + 20].tolist(), r["d"], r["R"])   # planted: อ่านเกิน j 20 bars
    fired = any(abs(x - y) > 1e-12 for x, y in zip(f_ok, f_bug))
    assert fired, "NEG-CTRL FAIL: planted span+20 แต่ features ไม่เปลี่ยน — guard ไม่มี power"
    print(f"[NEG-CTRL] ✓ planted span+20 bars → ES features เปลี่ยนจริง (guard มี power) · {dts}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "smoke":
        smoke()
    elif mode == "calib":
        calib()
    else:
        main()
