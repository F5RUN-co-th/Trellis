"""Card AD-1 — STAGE-1 relationship-drift gate + STAGE-2 exp-decay vs expanding (CLAIM-0019 จอง)
=====================================================================================
Spec: Plan/TRELLIS-010_card_AD1_adaptive_rolling.md **v8 FROZEN** (Engineer R8 PASS 07-16 · design loop 8 รอบ)
[reconstruction 07-17 — rebuild-from-session-record ตาม work-order ratified §7.3 STEP 1 ·
 acceptance-test = STAGE-1 output ต้องตรง run 07-16 (M8/M14)]
Hypothesis: direction signal ที่ real exit เป็น locally-stationary แต่ pooled/expanding fit หักล้างกันเอง —
recency-decay fit (H=480 trades) กู้ skill ที่ static จับไม่ได้
Representation ตรึง = 19-feat OHLC (ชุด frozen CLAIM-0010 · direction_at_real_exit.build_rows)
Machinery chain: tp1_card.folds/fit_predict(+rw) · fit_signedR(+rw · rw=None/ones bit-exact 0.00e+00)
Gate SSOT: ad1_gate_calib.gate_stats/rule/FROZEN_THR (calibrated บน X จริง · 8-round-reviewed)

STAGE-1 outcome (6 ชั้น · thresholds FROZEN):
  NO-DETECT / PERSISTENT → STOP (บันทึกตาม wording bounded-residual ใน doc)
  DRIFT-SUSPECT / SINGLE-BREAK(FLIP) / MONO / AMBIG → STAGE-2
STAGE-2 statistics (fold 2016-2020 เท่านั้น — fold 2015 ตัด pre-registered era-contrast=0):
  S1 = linear-forced: agg[payoff(decay) − payoff(expanding)] $/ไม้ (deterministic — ไม่มี seed · declared)
  S2 = GBM: median-9 agg[payoff(decay) − payoff(expanding)] $/ไม้ (sample_weight = |d|·rw)
  null = block-permutation ของลำดับ training (expanding invariant · decay re-weight ตาม permuted order)
  α = 0.025 (Bonferroni m=2) · B=1000 · escalation band [α/2, 2α] → B_ESC
  Secondary (ไม่เข้า inference): lift vs v4-baseline dir · DIAG: H-sweep/K600/per-fold/GATED keep-rate

modes:
  python ad1_card.py regress            — machinery regression (rw=ones ≡ rw=None bit-exact full-fold)
  python ad1_card.py acf                — เลือก block-size b จาก ACF ของ R(range)+features
  python ad1_card.py calib [S1|S2] [k0] [k1] — H0-true calibration (แบ่งช่วงได้)
  python ad1_card.py stage1             — gate บน real signed-R (budget ตาม work-order · prediction pre-registered)
  python ad1_card.py main               — STAGE-2 (รันเมื่อ stage1 route ต่อเท่านั้น)
governance: SEARCH 2012-2020 · lockbox 2024-26 + guard 2021-23 ไม่ถูกแตะ · ทุกเลข emit จาก script นี้
"""
import sys, time
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")
from brain_v1_run import load_ctx
from direction_at_real_exit import build_rows, sign_gate, _rng
from direction_predictor import fit_signedR
from tp1_card import folds as folds_all, fit_predict, SEEDS
from ad1_gate_calib import Calib, gate_stats, rule, H_TRADES, K_ROLL, LAM

ALPHA = 0.05 / 2            # m=2 (S1, S2)
B_PERM, B_ESC = 1000, 5000
PERM_ROOT = 20260719
B_CROSS = 200               # real-perm gate-FPR cross-check draws
CROSS_TOL = 0.20            # ±20% (doc §3.0 · log-not-switch)
NDRAW_CAL = 15
B0_CAL = 99
FOLD_MIN_YEAR = 2016        # ตัด fold 2015 pre-registered (era-contrast=0)
B_BLOCK_FLOOR, B_BLOCK_CAP = 5, 45   # b ∈ [5,45] — cap ให้ blocks/fold ≥ 15 ที่ fold เล็กสุด (675/45=15)
ACF_CUT = 0.10
H_SWEEP = (240.0, 960.0)    # DIAG descriptive (not-powered — §5)


class AD1:
    def __init__(self):
        rows = build_rows(load_ctx())
        self.X = np.array([r["feat"] for r in rows], float)
        self.pL = np.array([r["pL"] for r in rows]); self.pS = np.array([r["pS"] for r in rows])
        self.R = np.array([r["R"] for r in rows]); self.dd = np.array([r["d"] for r in rows])
        self.yr = np.array([r["yr"] for r in rows]); self.dayix = np.array([r["dayix"] for r in rows])
        self.Nemb = max(r["hold"] for r in rows)
        assert (np.diff(self.dayix) >= 0).all(), "rows ต้อง time-sorted (lag-by-position จะผิด)"
        self.rl, self.rs = self.pL / self.R, self.pS / self.R
        self.d = self.rl - self.rs
        self.wt = np.abs(self.d)
        self.n, self.NF = self.X.shape
        self.keep_all = np.ones(self.NF, bool)
        f_all = folds_all(self.yr, self.dayix, self.Nemb)
        self.folds = [f for f in f_all if int(f[0]) >= FOLD_MIN_YEAR]
        self.fold_2015 = [f for f in f_all if int(f[0]) < FOLD_MIN_YEAR]   # per-fold report เท่านั้น
        print(f"[SETUP] n={self.n} NF={self.NF} folds={[f[0] for f in self.folds]} "
              f"(ตัด {[f[0] for f in self.fold_2015]} pre-registered) Nemb={self.Nemb}d α={ALPHA:.4f}")

    # ---------- recency weights ----------
    def rw_for(self, tr, order=None):
        """rw ต่อ training row (เรียงตามลำดับเวลา หรือ order ที่ permute แล้วสำหรับ null)"""
        m = int(tr.sum())
        pos = np.arange(m) if order is None else order
        lag = (m - 1) - pos                                  # ใหม่สุด (ท้าย) = lag 0
        return LAM ** lag.astype(float)

    # ---------- STAGE-2 arms ----------
    def s1_pair(self, rw_by_fold):
        """linear-forced: agg[decay − expanding] · expanding cache ภายนอก (perm-invariant)"""
        la = []
        for i, (Y, tr, te) in enumerate(self.folds):
            rlt, rst = self.rl[tr], self.rs[tr]
            dpB = fit_predict(self.X, self.keep_all, tr, te, rlt, rst, self.dd, rw=rw_by_fold[i])
            payB = np.where(dpB == 1, self.pL[te], self.pS[te])
            la.append(payB - self.PAY_EXP_LIN[i])
        return float(np.concatenate(la).mean())

    def s2_pair(self, rw_by_fold):
        """GBM: median-9 agg[decay − expanding] · expanding cache ต่อ seed"""
        from lightgbm import LGBMClassifier
        aggs = []
        for s in SEEDS:
            la = []
            for i, (Y, tr, te) in enumerate(self.folds):
                yt = (self.d[tr] >= 0).astype(int)
                g = LGBMClassifier(max_depth=3, n_estimators=150, learning_rate=0.05,
                                   min_child_samples=max(20, int(tr.sum()) // 20),
                                   colsample_bytree=0.8, verbose=-1, random_state=s, n_jobs=1)
                g.fit(self.X[tr], yt, sample_weight=self.wt[tr] * rw_by_fold[i])
                dpB = np.where(g.predict(self.X[te]) == 1, 1, -1)
                payB = np.where(dpB == 1, self.pL[te], self.pS[te])
                la.append(payB - self.PAY_EXP_GBM[(s, i)])
            aggs.append(float(np.concatenate(la).mean()))
        return float(np.median(aggs)), aggs

    def build_exp_caches(self, gbm=True):
        """expanding arm (rw=None) — invariant ต่อ block-perm → cache ครั้งเดียว"""
        from lightgbm import LGBMClassifier
        self.PAY_EXP_LIN, self.PAY_EXP_GBM = {}, {}
        for i, (Y, tr, te) in enumerate(self.folds):
            rlt, rst = self.rl[tr], self.rs[tr]
            dpA = fit_predict(self.X, self.keep_all, tr, te, rlt, rst, self.dd)
            self.PAY_EXP_LIN[i] = np.where(dpA == 1, self.pL[te], self.pS[te])
        if gbm:
            for s in SEEDS:
                for i, (Y, tr, te) in enumerate(self.folds):
                    yt = (self.d[tr] >= 0).astype(int)
                    g = LGBMClassifier(max_depth=3, n_estimators=150, learning_rate=0.05,
                                       min_child_samples=max(20, int(tr.sum()) // 20),
                                       colsample_bytree=0.8, verbose=-1, random_state=s, n_jobs=1)
                    g.fit(self.X[tr], yt, sample_weight=self.wt[tr])
                    dpA = np.where(g.predict(self.X[te]) == 1, 1, -1)
                    self.PAY_EXP_GBM[(s, i)] = np.where(dpA == 1, self.pL[te], self.pS[te])

    # ---------- null: block-permutation ของลำดับ training ----------
    def perm_orders(self, b, rng):
        """ต่อ fold: permute ลำดับ block (ขนาด b trades ต่อเนื่อง) → order ใหม่ของ training rows"""
        out = []
        for (Y, tr, te) in self.folds:
            m = int(tr.sum())
            nblk = m // b + (1 if m % b else 0)
            blocks = [np.arange(k * b, min((k + 1) * b, m)) for k in range(nblk)]
            order = np.concatenate([blocks[j] for j in rng.permutation(nblk)])
            out.append(np.argsort(order))    # pos ของ row เดิมในลำดับใหม่
        return out

    def null_run(self, stat_fn, b, obs, tag, B0=None, escalate=True):
        rng = _rng(tag, PERM_ROOT)
        null, t0 = [], time.time()
        B = B0 or B_PERM
        B_first, k = B, 0
        while k < B:
            orders = self.perm_orders(b, rng)
            rw_perm = [self.rw_for(tr, orders[i]) for i, (Y, tr, te) in enumerate(self.folds)]
            v = stat_fn(rw_perm)
            null.append(v if np.isscalar(v) else v[0])
            k += 1
            if k in (10, 100, 500) or k % 1000 == 0:
                print(f"    [{tag}] {k}/{B} · {time.time()-t0:.0f}s", flush=True)
            if escalate and k == B and B == B_first:
                arr = np.array(null)
                p_now = (1 + int((arr >= obs).sum())) / (k + 1)
                if ALPHA / 2 <= p_now <= 2 * ALPHA:
                    print(f"    [{tag}] p={p_now:.4f} borderline → escalate B→{B_ESC}", flush=True)
                    B = B_ESC
        arr = np.array(null)
        p = (1 + int((arr >= obs).sum())) / (len(arr) + 1)
        return p, float(arr.mean()), float(np.quantile(arr, 0.95)), len(arr)

    # ---------- STAGE-1 gate ----------
    def rho_hat_real(self, dvec):
        years = sorted(set(self.yr))
        rh = np.zeros((len(years), self.NF))
        for t, Y in enumerate(years):
            m = self.yr == Y
            Z = (self.X[m] - self.X[m].mean(0)) / (self.X[m].std(0) + 1e-12)
            yc = (dvec[m] - dvec[m].mean()) / (dvec[m].std() + 1e-12)
            rh[t] = (Z * yc[:, None]).mean(0)
        return rh

    def stage1(self):
        # [F-1 fix 07-17] derive สด→assert==FROZEN ในตัว (M10 ครบ canonical B — self-guarding
        # ไม่พึ่งการรัน gate_calib ก่อน) · from_arrays = ไม่โหลด data ซ้ำ (X/yr ถืออยู่แล้ว)
        thr, _ = Calib.from_arrays(self.X, self.yr).derive_thresholds()
        print(f"[thr derived==FROZEN ✓] t_bar={thr['t_bar']:.4f} t_slope={thr['t_slope']:.4f} "
              f"t_flip={thr['t_flip']:.4f} t_stop={thr['t_stop']:.4f}")
        c, m = gate_stats(self.rho_hat_real(self.d))
        outcome = rule(c, m, thr)
        print(f"[STAGE-1] c̄={c:+.4f} slope(lag1-5)={m:+.4f} → OUTCOME = {outcome}")
        # real-perm cross-check (day-block shuffle ของ d ทั้ง sample → NOISE-analog บน X จริง + real-y marginals)
        udays, dstart = np.unique(self.dayix, return_index=True)
        groups = np.split(np.arange(self.n), dstart[1:])
        rng = _rng("ad1_cross", PERM_ROOT)
        cs = []
        for _ in range(B_CROSS):
            new_order = np.concatenate([groups[j] for j in rng.permutation(len(groups))])
            cs.append(gate_stats(self.rho_hat_real(self.d[new_order]))[0])
        q = float(np.quantile(cs, 0.975))
        dev = (q - thr["t_bar"]) / thr["t_bar"]
        flag = "OK" if abs(dev) <= CROSS_TOL else "⚠ GATE MIS-CALIBRATED (log-not-switch — execution-review ตีความ)"
        print(f"[cross-check] real-perm q97.5(c̄) = {q:.4f} vs synthetic t_bar {thr['t_bar']:.4f} "
              f"→ deviation {dev*100:+.1f}% ({flag})")
        return outcome


# ================================ modes ================================
def mode_regress(ad):
    """machinery regression — ไม่ใช่ hypothesis test (rw plumbing ต้อง inert ที่ rw=ones ทั้งสอง model class)"""
    ad.build_exp_caches(gbm=True)
    ones_by_fold = [np.ones(int(tr.sum())) for (Y, tr, te) in ad.folds]
    s1_ones = ad.s1_pair(ones_by_fold)
    print(f"[regress] S1(rw=ones) − S1(expanding) = {s1_ones:+.6e}  (ต้อง 0 เป๊ะ — bit-exact)")
    assert s1_ones == 0.0, "linear rw=ones ไม่ inert!"
    s2_ones, aggs = ad.s2_pair(ones_by_fold)
    print(f"[regress] S2(rw=ones) − S2(expanding) = {s2_ones:+.6e} · per-seed {['%.2e' % a for a in aggs]}")
    assert s2_ones == 0.0 and all(a == 0.0 for a in aggs), "GBM rw=ones ไม่ inert!"
    print(f"[regress] fold-2015 excluded = {[f[0] for f in ad.fold_2015]} · "
          f"train sizes = {[int(f[1].sum()) for f in ad.folds]} ✓")
    print("[regress] PASS ทั้งหมด")


def mode_acf(ad):
    """เลือก b — pre-registered rule: smallest lag ที่ |ACF|<0.1 ของ series ช้าสุด (R + 19 features · day-level)
    clip [5,45] (cap ให้ blocks/fold ≥15 ที่ fold เล็กสุด)"""
    udays = np.unique(ad.dayix)
    day_mean = lambda v: np.array([v[ad.dayix == dv].mean() for dv in udays])
    series = [("R", day_mean(ad.R))] + [(f"f{j}", day_mean(ad.X[:, j])) for j in range(ad.NF)]
    worst_lag, worst_name = 1, "-"
    for name, sr in series:
        s = (sr - sr.mean()) / (sr.std() + 1e-12)
        for L in range(1, 41):
            ac = float(np.mean(s[:-L] * s[L:]))
            if abs(ac) < ACF_CUT:
                if L > worst_lag:
                    worst_lag, worst_name = L, name
                break
        else:
            worst_lag, worst_name = 40, name
    b = int(np.clip(worst_lag, B_BLOCK_FLOOR, B_BLOCK_CAP))
    print(f"[acf] slowest series = {worst_name} (lag→|ACF|<{ACF_CUT} ที่ {worst_lag}) → b = {b} trades")
    for (Y, tr, te) in ad.folds:
        nb = int(tr.sum()) // b
        print(f"  fold {Y}: train {int(tr.sum())} → blocks {nb} {'✓' if nb >= 15 else '⚠ under-resolved (declare)'}")
    return b


def synth_stable_world(ad, rng, rho=0.10, nsig=4):
    """H0-true world สำหรับ calib: X จริง · d สังเคราะห์ stationary (STABLE archetype) ·
    pL=y/2 pS=−y/2 R=1 dd=random — pipeline เดียวกับของจริงทุกชั้น"""
    perm = rng.permutation(ad.NF); fa = perm[:nsig]
    u = np.zeros(ad.NF); u[fa] = 1.0
    y = np.zeros(ad.n)
    for Y in sorted(set(ad.yr)):
        m = ad.yr == Y
        Z = (ad.X[m] - ad.X[m].mean(0)) / (ad.X[m].std(0) + 1e-12)
        yv = Z @ (rho * u)
        sig2 = max(1.0 - float(np.var(yv)), 0.05)
        y[m] = yv + rng.standard_normal(int(m.sum())) * np.sqrt(sig2)
    w = AD1.__new__(AD1)
    w.__dict__.update(ad.__dict__)           # แชร์ X/yr/dayix/folds — override payoff เป็น synthetic
    w.rl, w.rs = y / 2.0, -y / 2.0
    w.pL, w.pS = y / 2.0, -y / 2.0
    w.d, w.wt = y, np.abs(y)
    w.dd = np.where(rng.random(ad.n) < 0.5, 1, -1)
    return w


def mode_calib(ad, b, stats=("S1", "S2"), k0=0, k1=NDRAW_CAL):
    print(f"[calib] H0-true draws {k0}..{k1-1} (STABLE ρ=0.10 บน X จริง) · B0={B0_CAL} · b={b} · stats={stats}")
    for stat in stats:
        ps, nm = [], []
        for k in range(k0, k1):
            w = synth_stable_world(ad, _rng(f"ad1_calib_{k}", PERM_ROOT))
            w.build_exp_caches(gbm=(stat == "S2"))
            rw0 = [w.rw_for(tr) for (Y, tr, te) in w.folds]
            if stat == "S1":
                obs = w.s1_pair(rw0)
                p, mu, q95, nB = w.null_run(w.s1_pair, b, obs, f"calS1_{k}", B0=B0_CAL, escalate=False)
            else:
                obs, _ = w.s2_pair(rw0)
                p, mu, q95, nB = w.null_run(lambda rwf: w.s2_pair(rwf)[0], b, obs,
                                            f"calS2_{k}", B0=B0_CAL, escalate=False)
            ps.append(p); nm.append(mu)
            print(f"  [{stat} draw {k}] obs={obs:+.4f} p={p:.3f} null-mean={mu:+.4f}", flush=True)
        ps = np.array(ps)
        print(f"[calib {stat} draws {k0}..{k1-1}] p<=0.05: {int((ps <= 0.05).sum())}/{len(ps)} · "
              f"median p = {np.median(ps):.3f} · null-mean เฉลี่ย = {np.mean(nm):+.4f} "
              f"(elevation per-statistic — ห้ามยืมข้าม)")


def mode_stage1(ad):
    return ad.stage1()


def mode_main(ad, b):
    ad.build_exp_caches(gbm=True)
    rw0 = [ad.rw_for(tr) for (Y, tr, te) in ad.folds]
    obs1 = ad.s1_pair(rw0)
    obs2, aggs2 = ad.s2_pair(rw0)
    print(f"[obs] S1(linear-forced · deterministic) = {obs1:+.4f} $/ไม้ · "
          f"S2(GBM median-9) = {obs2:+.4f} $/ไม้ · per-seed {['%.3f' % a for a in aggs2]}")
    # secondary + DIAG (ไม่เข้า inference)
    base = {i: np.where(ad.dd[te] == 1, ad.pL[te], ad.pS[te]) for i, (Y, tr, te) in enumerate(ad.folds)}
    la = []
    for i, (Y, tr, te) in enumerate(ad.folds):
        dpB = fit_predict(ad.X, ad.keep_all, tr, te, ad.rl[tr], ad.rs[tr], ad.dd, rw=rw0[i])
        la.append(np.where(dpB == 1, ad.pL[te], ad.pS[te]) - base[i])
    print(f"[secondary] decay-linear vs v4-baseline = {np.concatenate(la).mean():+.4f} $/ไม้ (report-only)")
    for H in H_SWEEP:
        lamH = np.exp(-np.log(2) / H)
        rwH = []
        for (Y, tr, te) in ad.folds:
            mm = int(tr.sum()); rwH.append(lamH ** ((mm - 1) - np.arange(mm)).astype(float))
        print(f"[DIAG H={H:.0f}] S1 = {ad.s1_pair(rwH):+.4f} (descriptive not-powered)")
    kr = []
    for (Y, tr, te) in ad.folds:
        k = sign_gate(ad.X[tr], ad.d[tr], ad.dayix[tr], _rng(f"ad1_gate_{Y}", PERM_ROOT))
        kr.append(int(k.sum()))
    print(f"[DIAG GATED keep-count ต่อ fold] {kr} (diagnostic เท่านั้น — primary = forced)")
    # inference
    p1, mu1, q951, nB1 = ad.null_run(ad.s1_pair, b, obs1, "S1null")
    print(f"[S1] p = {p1:.4f} (B={nB1} · null-mean {mu1:+.4f} · null-q95 {q951:+.4f}) · α={ALPHA:.4f}")
    p2, mu2, q952, nB2 = ad.null_run(lambda rwf: ad.s2_pair(rwf)[0], b, obs2, "S2null")
    print(f"[S2] p = {p2:.4f} (B={nB2} · null-mean {mu2:+.4f} · null-q95 {q952:+.4f}) · α={ALPHA:.4f}")
    verdict = "KILL" if (p1 >= ALPHA and p2 >= ALPHA) else \
        "SIGNAL-CANDIDATE (→ secondary CI + promotion gate ใน execution-review — ห้ามข้ามไป monetize)"
    print(f"[VERDICT pre-registered] {verdict} · sensitivity-floor S1 ≈ {q951:+.4f} · S2 ≈ {q952:+.4f} $/ไม้")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "regress"
    ad = AD1()
    if mode == "regress":
        mode_regress(ad)
    elif mode == "acf":
        mode_acf(ad)
    elif mode == "calib":
        b = mode_acf(ad)
        stats = (sys.argv[2],) if len(sys.argv) > 2 else ("S1", "S2")
        k0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        k1 = int(sys.argv[4]) if len(sys.argv) > 4 else NDRAW_CAL
        mode_calib(ad, b, stats, k0, k1)
    elif mode == "stage1":
        mode_stage1(ad)
    elif mode == "main":
        b = mode_acf(ad)
        mode_main(ad, b)
    else:
        raise SystemExit(f"unknown mode {mode}")
