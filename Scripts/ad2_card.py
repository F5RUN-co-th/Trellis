"""Card AD-2 — rolling-recency unconditional (CLAIM-0020 จอง)
=====================================================================================
Spec: Plan/TRELLIS-010_card_AD2_flip_detector.md **design v3** (R1 FAIL → Claude-Verify → R2/R3 PASS-with-changes)
Hypothesis: recency hard-window (rolling K=300 trades ล่าสุด) กู้ payoff lift เหนือ expanding fit
บน real signed-R — ทดสอบตรงว่าโลกจริงเป็นโลก local-regime ที่ AD-1 gate บอด (NO-DETECT class) หรือไม่
expectation ประกาศ [§2]: คาด KILL (real slope +0.0416 flat · era-flip n=1)

S1 (m=1 · decision = calibrated-α* [R4-R1]) = agg[payoff(rolling-K300 true-subset linear) − payoff(expanding linear)] $/ไม้
  implementation [R3-FB-1(a)]: index-subsetting — ส่ง tr ที่เหลือ last-K rows เข้า fit_predict เดิม
  → standardization (tp1_card.fit_predict:117 mu/sd บน X[tr]) คำนวณบน subset = true rolling-K
  (ห้าม rw=0/1 mask — standardization ยัง full-train ≠ true subset · R3 verified)
null: perm_orders (block-perm b จาก R/feature-ACF) → subset = last-K ของ permuted order (random-K blocks)
  [R3-CR-5] p ทดสอบ "recent-K ดีกว่า random-K" — PAY_EXP cancel ใน p · lift vs expanding = descriptive

modes:
  python ad2_card.py regress          — machinery: (1) K≥train ≡ expanding exact 0.0 (real · identity)
                                        (2) K<train structural + exercise บน synthetic เท่านั้น [กัน free-look]
  python ad2_card.py acf              — เลือก block-size b (reuse ad1 mode_acf · R/feature-ACF)
  python ad2_card.py calib [k0] [k1]  — H0-true calibration (STABLE world · S1 null p-dist + elevation)
  python ad2_card.py certify          — [R4] เลือก null variant ด้วย power-at-α* (STABLE N=200 ×2 + RFLIP@{3,3.5} N=30)
  python ad2_card.py main             — real run ⛔ FROZEN_CERT ต้อง pin + spec+prediction อยู่ใน commit ที่วินสั่งแล้วเท่านั้น
                                        (freeze-commit rule) · budget charge +1 ⇒ 6/40 ที่ mode นี้
governance: SEARCH 2012-2020 · lockbox 2024-26 + guard 2021-23 ไม่ถูกแตะ · ทุกเลข emit จาก script นี้
"""
import sys, time, os
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")
from ad1_card import AD1, mode_acf, synth_stable_world
from tp1_card import fit_predict
from direction_at_real_exit import _rng
from ad1_gate_calib import K_ROLL

ALPHA_NOM = 0.05             # nominal (m=1) — decision จริงใช้ calibrated-α* จาก certify [R4-R1]
B_PERM, B_ESC = 1000, 5000
PERM_ROOT = 20260721         # seed root ใหม่ของ card นี้ (ประกาศ · แยกจาก AD-1 20260719)
NDRAW_CAL = 15
B0_CAL = 99
RHO_CAL = 0.10
CERT_N_STABLE = 200          # [R4] N ≥ 200 เพื่อ α* (q05 order-stat) เสถียร
CERT_N_POWER = 30
CERT_PGRID = (3.0, 3.5)      # residual cells จริง [CLAIM-0019]
# FROZEN_CERT — pinned จาก certify 07-19 (R7 approve · เจ้าของเลข = ad2_cert_out/*.csv · re-derive ได้จาก seeds)
# power = bracket สอง comparator [R7-F1]: B0=99 มี boundary draw p==0.05 ที่ P3.0 · ที่ B=1000 (main จริง)
# p==0.05 เกิดไม่ได้ → comparator coincide · headline conservative = power_lt · main assert q05+alpha_decision
FROZEN_CERT = {"variant": "scattered", "q05": 0.06, "alpha_decision": 0.05,
               "power_lt": {3.0: 0.3333, 3.5: 0.0667}, "power_le": {3.0: 0.3667, 3.5: 0.0667}}


class AD2(AD1):
    def __init__(self):
        super().__init__()
        print("[AD2] m=1 · decision = calibrated-α* จาก certify (banner α ข้างบน = ของ AD1 loader — ไม่ใช้ใน AD-2)")

    # ---------- true-subset rolling [R3-FB-1(a)] ----------
    def tr_lastK(self, tr, order=None, K=K_ROLL):
        """เหลือเฉพาะ training rows ที่ตำแหน่ง (ตาม order) อยู่ท้ายสุด K แถว
        order = new-position ต่อ row เดิม (semantics เดียวกับ decay-null rw_for) · None = ลำดับเวลา"""
        m = int(tr.sum())
        if m <= K:
            return tr
        pos = np.arange(m) if order is None else order
        keep = pos >= (m - K)
        tr2 = np.zeros_like(tr)
        tr2[np.where(tr)[0][keep]] = True
        return tr2

    def s1_roll(self, orders=None, K=K_ROLL):
        """S1 = agg[payoff(rolling true-subset) − payoff(expanding)] · expanding cache ภายนอก"""
        la = []
        for i, (Y, tr, te) in enumerate(self.folds):
            tr2 = self.tr_lastK(tr, None if orders is None else orders[i], K)
            dpB = fit_predict(self.X, self.keep_all, tr2, te, self.rl[tr2], self.rs[tr2], self.dd)
            payB = np.where(dpB == 1, self.pL[te], self.pS[te])
            la.append(payB - self.PAY_EXP_LIN[i])
        return float(np.concatenate(la).mean())

    def s1_roll_perfold(self, K=K_ROLL):
        out = {}
        for i, (Y, tr, te) in enumerate(self.folds):
            tr2 = self.tr_lastK(tr, None, K)
            dpB = fit_predict(self.X, self.keep_all, tr2, te, self.rl[tr2], self.rs[tr2], self.dd)
            payB = np.where(dpB == 1, self.pL[te], self.pS[te])
            out[Y] = float((payB - self.PAY_EXP_LIN[i]).mean())
        return out

    # ---------- contiguous-window variant [R4] ----------
    def tr_window(self, tr, st, K=K_ROLL):
        idx = np.where(tr)[0]
        tr2 = np.zeros_like(tr)
        tr2[idx[st:st + K]] = True
        return tr2

    def s1_win(self, sts=None, K=K_ROLL):
        """S1 บน contiguous window ต่อ fold · sts=None = last-K (obs — แถวเดียวกับ s1_roll obs)"""
        la = []
        for i, (Y, tr, te) in enumerate(self.folds):
            st = (int(tr.sum()) - K) if sts is None else sts[i]
            tr2 = self.tr_window(tr, st, K)
            dpB = fit_predict(self.X, self.keep_all, tr2, te, self.rl[tr2], self.rs[tr2], self.dd)
            payB = np.where(dpB == 1, self.pL[te], self.pS[te])
            la.append(payB - self.PAY_EXP_LIN[i])
        return float(np.concatenate(la).mean())

    def null_draw(self, variant, b, rng, K=K_ROLL):
        """หนึ่ง null draw ตาม variant: scattered = last-K ของ permuted block-order · contig = window สุ่มตำแหน่ง"""
        if variant == "scattered":
            return self.s1_roll(self.perm_orders(b, rng), K)
        sts = [int(rng.integers(0, int(tr.sum()) - K + 1)) for (Y, tr, te) in self.folds]
        return self.s1_win(sts, K)

    def p_one(self, variant, b, tag, B0=B0_CAL, K=K_ROLL):
        """p ของ world นี้ (obs = last-K) ใต้ null variant — B0 draws (certify unit)"""
        rng = _rng(tag, PERM_ROOT)
        obs = self.s1_win(None, K)
        null = np.array([self.null_draw(variant, b, rng, K) for _ in range(B0)])
        return obs, (1 + int((null >= obs).sum())) / (len(null) + 1), float(null.mean())

    def null_run_orders(self, b, obs, tag, B0=None, escalate=True, K=K_ROLL,
                        variant="scattered", alpha=ALPHA_NOM):
        """mirror ad1_card.AD1.null_run · escalation band re-center รอบ alpha ที่ส่งเข้า [R4-R3]"""
        rng = _rng(tag, PERM_ROOT)
        null, t0 = [], time.time()
        B = B0 or B_PERM
        B_first, k = B, 0
        while k < B:
            null.append(self.null_draw(variant, b, rng, K))
            k += 1
            if k in (10, 100, 500) or k % 1000 == 0:
                print(f"    [{tag}] {k}/{B} · {time.time()-t0:.0f}s", flush=True)
            if escalate and k == B and B == B_first:
                arr = np.array(null)
                p_now = (1 + int((arr >= obs).sum())) / (k + 1)
                if alpha / 2 <= p_now <= 2 * alpha:
                    print(f"    [{tag}] p={p_now:.4f} borderline (band รอบ α*={alpha:.3f}) → escalate B→{B_ESC}", flush=True)
                    B = B_ESC
        arr = np.array(null)
        p = (1 + int((arr >= obs).sum())) / (len(arr) + 1)
        return p, float(arr.mean()), float(np.quantile(arr, 0.95)), len(arr)


def as_ad2(world):
    """ยก AD1-world (จาก synth_stable_world) เป็น AD2 เพื่อใช้ s1_roll/null_run_orders"""
    w = AD2.__new__(AD2)
    w.__dict__.update(world.__dict__)
    return w


def rflip_world(ad, rng, P=3.0, rho=RHO_CAL, nsig=4):
    """mirror synth_stable_world แต่ beta สลับ sign ทุก P year-blocks (RFLIP archetype — power probe)"""
    perm = rng.permutation(ad.NF); fa = perm[:nsig]
    u = np.zeros(ad.NF); u[fa] = 1.0
    y = np.zeros(ad.n)
    for t, Y in enumerate(sorted(set(ad.yr))):
        m = ad.yr == Y
        Z = (ad.X[m] - ad.X[m].mean(0)) / (ad.X[m].std(0) + 1e-12)
        sgn = 1.0 if (int(t // P) % 2 == 0) else -1.0
        yv = Z @ (rho * u * sgn)
        sig2 = max(1.0 - float(np.var(yv)), 0.05)
        y[m] = yv + rng.standard_normal(int(m.sum())) * np.sqrt(sig2)
    w = AD2.__new__(AD2)
    w.__dict__.update(ad.__dict__)
    w.rl, w.rs = y / 2.0, -y / 2.0
    w.pL, w.pS = y / 2.0, -y / 2.0
    w.d, w.wt = y, np.abs(y)
    w.dd = np.where(rng.random(ad.n) < 0.5, 1, -1)
    return w


def derive_alpha_star(ad, b, variant, N=CERT_N_STABLE, verbose=True):
    """[M10] re-derive α* เต็ม (seeds เดิม · deterministic) — ใช้ใน mode_main เพื่อ assert == FROZEN_CERT"""
    ps = []
    for k in range(N):
        w = as_ad2(synth_stable_world(ad, _rng(f"ad2_cert_s_{k}", PERM_ROOT)))
        w.build_exp_caches(gbm=False)
        _, p, _ = w.p_one(variant, b, f"cert_{variant}_s{k}")
        ps.append(p)
        if verbose and (k + 1) % 25 == 0:
            print(f"    [{variant} STABLE] {k+1}/{N}", flush=True)
    ps = np.array(ps)
    return float(np.quantile(ps, 0.05)), float((ps <= 0.05).mean()), float((ps <= 0.01).mean()), ps


CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ad2_cert_out")  # transient (untracked) — เลขทางการ re-derive ได้จาก seeds


def cert_stable_chunk(ad, b, variant, k0, k1):
    """[R4 · chunked — กัน process-kill] STABLE draws k0..k1-1 → append (k,p) ลง csv · seeds เดิมกับ derive_alpha_star"""
    os.makedirs(CERT_DIR, exist_ok=True)
    path = os.path.join(CERT_DIR, f"stable_{variant}.csv")
    with open(path, "a") as f:
        for k in range(k0, k1):
            w = as_ad2(synth_stable_world(ad, _rng(f"ad2_cert_s_{k}", PERM_ROOT)))
            w.build_exp_caches(gbm=False)
            _, p, _ = w.p_one(variant, b, f"cert_{variant}_s{k}")
            f.write(f"{k},{p:.6f}\n"); f.flush()
            if (k + 1) % 10 == 0:
                print(f"  [{variant} STABLE] {k+1} done", flush=True)
    print(f"[cert_stable] {variant} draws {k0}..{k1-1} → {path}")


def _read_stable(variant):
    path = os.path.join(CERT_DIR, f"stable_{variant}.csv")
    rows = {}
    with open(path) as f:
        for line in f:
            k, p = line.strip().split(",")
            rows[int(k)] = float(p)      # duplicate k (rerun chunk) → ค่าล่าสุดชนะ (deterministic เท่ากันอยู่แล้ว)
    ks = sorted(rows)
    assert ks == list(range(len(ks))), f"stable_{variant} draws ไม่ต่อเนื่อง: {len(ks)} rows"
    return np.array([rows[k] for k in ks])


def cert_power(ad, b, variant):
    """power บน RFLIP@CERT_PGRID — **persist raw p-values** [R5-D] (คำนวณ power ที่ threshold ใดก็ได้ใน report)"""
    path = os.path.join(CERT_DIR, f"power_{variant}.csv")
    with open(path, "w") as f:
        for P in CERT_PGRID:
            for k in range(CERT_N_POWER):
                w = rflip_world(ad, _rng(f"ad2_cert_r{P}_{k}", PERM_ROOT), P=P)
                w.build_exp_caches(gbm=False)
                _, p, _ = w.p_one(variant, b, f"cert_{variant}_r{P}_{k}")
                f.write(f"{P},{k},{p:.6f}\n"); f.flush()
            print(f"  [{variant}] RFLIP@{P} raw-p persisted {CERT_N_POWER} draws", flush=True)
    print(f"[cert_power] {variant} → {path}")


def cert_report():
    """รวมผล → q05 → **α*_decision = min(q05, ALPHA_NOM)** [R5-A cap — ห้าม liberalize · KILL-card posture]
    → FPR@decision + power@decision (จาก raw p) + SELECT (pre-declared: power-at-decision สูงกว่า)"""
    res = {}
    for variant in ("scattered", "contig"):
        ps = _read_stable(variant)[:CERT_N_STABLE]
        q05 = float(np.quantile(ps, 0.05))
        a_dec = min(q05, ALPHA_NOM)
        pw_lt, pw_le = {}, {}
        with open(os.path.join(CERT_DIR, f"power_{variant}.csv")) as f:
            rows = [line.strip().split(",") for line in f]
        for P in CERT_PGRID:
            pv = np.array([float(r[2]) for r in rows if float(r[0]) == P])
            assert len(pv) == CERT_N_POWER, f"{variant} RFLIP@{P}: {len(pv)} != {CERT_N_POWER}"
            pw_lt[P] = float((pv < a_dec).mean())    # decision-strict (conservative headline)
            pw_le[P] = float((pv <= a_dec).mean())   # Phipson-Smyth convention · B=1000 → coincide [R7-F1]
        res[variant] = {"q05": q05, "alpha_decision": a_dec,
                        "fpr_lt": float((ps < a_dec).mean()), "fpr_le": float((ps <= a_dec).mean()),
                        "fpr05": float((ps <= 0.05).mean()), "fpr01": float((ps <= 0.01).mean()),
                        "power_lt": pw_lt, "power_le": pw_le}
        flag = " ⚠ SANITY-FLAG" if (q05 < 0.01 or res[variant]["fpr05"] > 0.15) else ""
        print(f"[{variant}] N={len(ps)} · q05={q05:.3f} → α*_decision=min(q05,{ALPHA_NOM})={a_dec:.3f} · "
              f"FPR@decision <:{res[variant]['fpr_lt']*100:.1f}% ≤:{res[variant]['fpr_le']*100:.1f}% · "
              f"FPR@0.01={res[variant]['fpr01']*100:.1f}% · power bracket <:{pw_lt} ≤:{pw_le} "
              f"(B0=99 boundary artifact — B=1000 coincide){flag}")
    sel = max(("scattered", "contig"), key=lambda v: np.mean(list(res[v]["power_lt"].values())))
    print(f"\n[certify SELECT — power-at-decision (headline conservative <)] variant = {sel} · "
          f"α*_decision = {res[sel]['alpha_decision']:.3f} · power [lt, le] = "
          f"{[(res[sel]['power_lt'][P], res[sel]['power_le'][P]) for P in CERT_PGRID]}")
    print("[certify] → pin FROZEN_CERT {variant, q05, alpha_decision, power} + วินสั่ง commit ก่อนรัน main")


def mode_certify(ad, b):
    """[R4·R5] orchestrator — implementation เดียว (csv-chunked): STABLE ×2 → power raw-p ×2 → report"""
    for variant in ("scattered", "contig"):
        done = 0
        try:
            done = len(_read_stable(variant))
        except FileNotFoundError:
            pass
        if done < CERT_N_STABLE:
            cert_stable_chunk(ad, b, variant, done, CERT_N_STABLE)
    for variant in ("scattered", "contig"):
        cert_power(ad, b, variant)
    cert_report()


def mode_main(ad, b):
    """⛔ freeze-commit gate + M10: re-derive α* (seeds เดิม) → assert == FROZEN_CERT ก่อน route · charge 6/40"""
    if not FROZEN_CERT:
        raise SystemExit("⛔ freeze gate: ต้องรัน certify → pin FROZEN_CERT + วินสั่ง commit ก่อนรัน main")
    variant, q_pin, a_pin = FROZEN_CERT["variant"], FROZEN_CERT["q05"], FROZEN_CERT["alpha_decision"]
    q05, fpr05, _, _ = derive_alpha_star(ad, b, variant, verbose=False)
    assert abs(q05 - q_pin) < 1e-9, f"FROZEN_CERT drift: q05 derived {q05:.4f} != pinned {q_pin:.4f}"
    a_star = min(q05, ALPHA_NOM)     # [R5-A] cap — ห้าม liberalize เกิน nominal (KILL-card posture + y-model-risk)
    assert abs(a_star - a_pin) < 1e-9, f"FROZEN_CERT drift: α*_decision {a_star:.4f} != pinned {a_pin:.4f}"
    print(f"[thr derived==FROZEN ✓] variant={variant} q05={q05:.3f} → α*_decision=min(q05,{ALPHA_NOM})={a_star:.3f} "
          f"(FPR@0.05 diag {fpr05*100:.1f}%)")
    ad.build_exp_caches(gbm=False)
    obs = ad.s1_win(None)
    pf = ad.s1_roll_perfold()
    print(f"[obs] S1(rolling-K300 true-subset − expanding) = {obs:+.4f} $/ไม้ (descriptive vs expanding)")
    print(f"[per-fold descriptive] {pf}")
    print(f"[DIAG K=600 · not-powered] S1 = {ad.s1_roll(K=600):+.4f}")
    p, mu, q95, nB = ad.null_run_orders(b, obs, "S1null", variant=variant, alpha=a_star)
    # ===== ESTIMATION primary [O3 · R7-G1/G2/G3] =====
    print(f"[ESTIMATION primary — อ่าน point เทียบ NULL ไม่ใช่เทียบ 0 (กัน CLAIM-0016 re-commit · G1)]")
    print(f"  S1 point = {obs:+.4f} $/ไม้ · null-mean (H0 center) = {mu:+.4f} · point−null-mean = {obs - mu:+.4f}")
    print(f"  MDE/sensitivity-floor = null-q95 {q95:+.4f} $/ไม้ [R3-CR-2 · detectability floor — ไม่ใช่ SESOI · "
          f"ห้าม claim equivalence-to-zero (G2)]")
    print(f"  guard [G3 · CLAIM-0016]: point บวก + p≥α* ≠ evidence — จับได้เมื่อ point−null เกิน floor เท่านั้น")
    print(f"[S1 inference (claim เดียว m=1)] p = {p:.4f} (B={nB}) · α*_decision = {a_star:.3f} · "
          f"p = P(random-K ≥ recent-K) [R3-CR-5]")
    trig = pf.get('2016', float('nan'))
    print(f"[§6 re-open trigger — descriptive/hypothesis-generating เท่านั้น] fold2016 {trig:+.4f} vs pooled "
          f"null-q95 {q95:+.4f} → {'MET' if trig > q95 else 'not met'} (การเปิด follow-up = วินตัดสิน)")
    verdict = ("KILL (binary secondary · power-scoped: bracket 33.3-36.7%@P3.0 · 6.7%@P3.5 — P≈3.5 underpowered "
               "ไม่ถูก falsify · decision-null conservative verified N=200 FPR 4.0-4.5% + cap [R7-F2] · "
               "ไม่ใช่ proof-of-absence)") \
        if p >= a_star else "SIGNAL-CANDIDATE (→ execution-review + promotion gate — ห้ามข้ามไป monetize)"
    print(f"[VERDICT pre-registered] {verdict}")


# ================================ modes ================================
def mode_regress(ad):
    """machinery regression — ไม่ใช่ hypothesis test"""
    ad.build_exp_caches(gbm=False)
    # (1) K ≥ train ≡ expanding — real payoffs แต่ identity-zero โดย construction (ไม่เผยอะไร)
    s1_big = ad.s1_roll(K=10**9)
    print(f"[regress-1] S1(K≥train) − expanding = {s1_big:+.6e} (ต้อง 0 เป๊ะ — subset==full)")
    assert s1_big == 0.0, "K≥train ไม่ inert!"
    # (2) K<train — structural asserts + exercise บน SYNTHETIC เท่านั้น [กัน free-look ก่อน freeze]
    for i, (Y, tr, te) in enumerate(ad.folds):
        tr2 = ad.tr_lastK(tr)
        idx_all, idx_sub = np.where(tr)[0], np.where(tr2)[0]
        assert tr2.sum() == K_ROLL and np.array_equal(idx_sub, idx_all[-K_ROLL:]), f"fold {Y} subset ผิด"
        mu_f = ad.X[tr].mean(0); mu_s = ad.X[tr2].mean(0)
        d = float(np.linalg.norm(mu_f - mu_s) / (np.linalg.norm(mu_f) + 1e-12))
        print(f"  fold {Y}: subset {int(tr2.sum())}/{int(tr.sum())} = last-K ตามเวลา ✓ · d(mu full↔last300) = {d:.3f}"
              f" (≠0 = standardization บน subset ทำงานจริง — FB-1 operative)")
    w = as_ad2(synth_stable_world(ad, _rng("ad2_regress_syn", PERM_ROOT)))
    w.build_exp_caches(gbm=False)
    v = w.s1_roll()
    print(f"[regress-2] exercise K<train บน synthetic STABLE world: S1_roll = {v:+.4f} (สนามซ้อม · ไม่ใช่ผลจริง)")
    print("[regress] PASS ทั้งหมด")


def mode_calib(ad, b, k0=0, k1=NDRAW_CAL):
    print(f"[calib] H0-true draws {k0}..{k1-1} (STABLE ρ=0.10 บน X จริง) · B0={B0_CAL} · b={b} · stat=S1_roll")
    ps, nm = [], []
    for k in range(k0, k1):
        w = as_ad2(synth_stable_world(ad, _rng(f"ad2_calib_{k}", PERM_ROOT)))
        w.build_exp_caches(gbm=False)
        obs = w.s1_roll()
        p, mu, q95, nB = w.null_run_orders(b, obs, f"calS1_{k}", B0=B0_CAL, escalate=False)
        ps.append(p); nm.append(mu)
        print(f"  [S1 draw {k}] obs={obs:+.4f} p={p:.3f} null-mean={mu:+.4f}", flush=True)
    ps = np.array(ps)
    print(f"[calib S1 draws {k0}..{k1-1}] p<=0.05: {int((ps <= 0.05).sum())}/{len(ps)} · "
          f"median p = {np.median(ps):.3f} · null-mean เฉลี่ย = {np.mean(nm):+.4f} "
          f"(elevation per-statistic — ห้ามยืมข้าม)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "regress"
    ad = AD2()
    if mode == "regress":
        mode_regress(ad)
    elif mode == "acf":
        mode_acf(ad)
    elif mode == "calib":
        b = mode_acf(ad)
        k0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        k1 = int(sys.argv[3]) if len(sys.argv) > 3 else NDRAW_CAL
        mode_calib(ad, b, k0, k1)
    elif mode == "certify":
        b = mode_acf(ad)
        mode_certify(ad, b)
    elif mode == "cert_stable":
        b = mode_acf(ad)
        cert_stable_chunk(ad, b, sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif mode == "cert_power":
        b = mode_acf(ad)
        cert_power(ad, b, sys.argv[2])
    elif mode == "cert_report":
        cert_report()
    elif mode == "main":
        b = mode_acf(ad)
        mode_main(ad, b)
    else:
        raise SystemExit(f"unknown mode {mode}")
