"""Card AD-3 — online regime-flip detector + conditional fit (CLAIM-0021 จอง)
=====================================================================================
Spec: Plan/TRELLIS-010_card_AD3_regime_detector.md **design v2** (R1-R3 PASS-with-changes absorbed)
Hypothesis: regime-flip ตรวจจับได้ ex-ante + post-flip purity กู้ lift (adjudicate fold2016 anomaly:
contiguity-variance vs era-structure — re-fire block-perm null แยกสองคำอธิบาย [§2.1])
expectation ประกาศ [§2]: คาด no-fire/KILL (slope flat · n=1 · purity-vs-quantity · anti-recency AD-2)

Detector [§3.2]: partition fold-train (ตาม order) เป็น windows ละ W trades → ρ̂_w ต่อ window
  (standardize ภายใน window) → a(j) = cos(ρ̂_j, ρ̂_{j-1}) [lagged-local ref] →
  CUSUM S_j = max(0, S_{j-1} − a_j) · fire เมื่อ S_j > h → reset · fire-pos = จุดเริ่ม window j
Conditional fit: training = rows หลัง fire ล่าสุด · segment < FLOOR=100 → fallback expanding
  (declared under-resolved) · fallback bit-identical obs/null [zero-mass symmetry]
STAGE-A (P&L-free · ไม่ charge): detcal (calibrate h ต่อ W · convention bar: detection ≥80%
  @SINGLE-FLIP ρ0.10 · FPR ≤5% per-fold · tolerance asymmetric late≤W/early≤B_EARLY=40) ·
  probe (timing + P(fire|null) + zero-fraction → size B) · certify (null-of-p re-fire N=200 →
  α*_dec=min(q05,0.05) + contiguity-verify p-uniform + zero-fraction emit)
STAGE-B/C (main ⛔ FROZEN_DET ต้อง pin + freeze-commit วินสั่งก่อน · charge +1 ⇒ 7/40):
  fire-count vs STABLE envelope (binding) → conditional S1 + re-fire null
⚠ detector ห้ามรันบน real d ก่อน freeze — ทุก pre-freeze run = synthetic y เท่านั้น (กัน free-look)
governance: SEARCH 2012-2020 · lockbox/guard ไม่แตะ · ทุกเลข emit จาก script นี้
"""
import sys, time, os
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")
from ad1_card import AD1, mode_acf, synth_stable_world
from ad2_card import AD2, as_ad2, rflip_world
from tp1_card import fit_predict
from direction_at_real_exit import _rng

PERM_ROOT = 20260722          # seed root ใหม่ (ประกาศ · แยกจาก AD-1/AD-2)
ALPHA_NOM = 0.05
RHO_CAL = 0.10                # family power-floor (AD-1)
W_GRID = (100, 150)           # operating-W candidates (ตรึงตัวเลือกก่อนรัน · เลือกด้วยเกณฑ์ pre-declared)
FLOOR_SEG = 100               # [FB-4] DoF-minimum (5×NF≈95) — 190/300 exclude fold2016 (measured 166)
B_EARLY = 40                  # [FB-2 asymmetric] fire-early tolerance = b (block/contiguity unit)
BAR_DETECT = 0.80             # convention bar (external — ประกาศก่อน detcal รัน)
BAR_FPR = 0.05                # per-fold [pin หน่วย — Claude-Verify R3]
N_CAL = 120                   # draws ต่อ archetype ใน detcal
CERT_N = 200
B0_CAL = 99
CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ad3_cert_out")
# pin หลัง detcal+certify (W/h/envelope/alpha_decision/...) — main ปฏิเสธรันจนกว่า pin + วินสั่ง commit
FROZEN_DET = {}


class AD3(AD2):
    # ---------- detector core (sequence = training rows เรียงตาม order) ----------
    def win_rho(self, Xs, ys):
        Z = (Xs - Xs.mean(0)) / (Xs.std(0) + 1e-12)
        yc = (ys - ys.mean()) / (ys.std() + 1e-12)
        return (Z * yc[:, None]).mean(0)

    def detect(self, Xseq, yseq, W, h, k=0.0):
        """คืน fire positions — **Page CUSUM มี allowance k** [R4-D1]: S = max(0, S − a − k)
        (zero-allowance = degenerate: NOISE ทำ reflected random-walk fire มั่ว — R4 measured)"""
        m = len(yseq)
        nwin = m // W
        fires, S, prev = [], 0.0, None
        for j in range(nwin):
            sl = slice(j * W, (j + 1) * W)
            r = self.win_rho(Xseq[sl], yseq[sl])
            if prev is not None:
                a = float(r @ prev / (np.linalg.norm(r) * np.linalg.norm(prev) + 1e-12))
                S = max(0.0, S - a - k)
                if S > h:
                    fires.append(j * W)      # จุดเริ่ม window ที่ยืนยัน flip
                    S = 0.0
            prev = r
        return fires

    def fold_fires(self, w, tr, order, W, h, k=0.0):
        """detector บน fold-train ของ world w (y = w.d) ตาม order · คืน fires ใน sequence-coordinate"""
        idx = np.where(tr)[0]
        pos = np.arange(len(idx)) if order is None else order
        seq = idx[np.argsort(pos)]
        return self.detect(w.X[seq], w.d[seq], W, h, k), seq

    def s1_cond(self, w, W, h, orders=None, k=0.0):
        """S1 = agg[payoff(post-fire conditional) − payoff(expanding)] · fallback expanding เมื่อ
        no-fire หรือ segment < FLOOR_SEG (bit-identical ทั้ง obs/null — symmetry)"""
        la, meta = [], []
        for i, (Y, tr, te) in enumerate(w.folds):
            fires, seq = self.fold_fires(w, tr, None if orders is None else orders[i], W, h, k)
            if fires:
                seg = seq[fires[-1]:]
                if len(seg) >= FLOOR_SEG:
                    tr2 = np.zeros_like(tr); tr2[seg] = True
                    dpB = fit_predict(w.X, w.keep_all, tr2, te, w.rl[tr2], w.rs[tr2], w.dd)
                    payB = np.where(dpB == 1, w.pL[te], w.pS[te])
                    la.append(payB - w.PAY_EXP_LIN[i])
                    meta.append((Y, len(fires), len(seg)))
                    continue
                meta.append((Y, len(fires), f"seg{len(seg)}<floor→fallback"))
            else:
                meta.append((Y, 0, "no-fire→expanding"))
            la.append(w.PAY_EXP_LIN[i] - w.PAY_EXP_LIN[i])   # exact zeros ≡ expanding (fallback/no-fire — symmetry)
        return float(np.concatenate(la).mean()), meta


def single_flip_world(ad, rng, rho=RHO_CAL, nsig=4):
    """era-analog n=1: beta สลับ sign ครั้งเดียวที่ boundary ปีสุ่ม (interior) — truth known ต่อ draw
    (สุ่ม boundary กัน bake 2014/15 [no-hardcode] · position-truth คืนเป็น trade-index ต่อ fold)"""
    years = sorted(set(ad.yr))
    bidx = int(rng.integers(2, len(years) - 1))     # boundary หลังปี index bidx-1
    perm = rng.permutation(ad.NF); fa = perm[:nsig]
    u = np.zeros(ad.NF); u[fa] = 1.0
    y = np.zeros(ad.n)
    for t, Y in enumerate(years):
        m = ad.yr == Y
        Z = (ad.X[m] - ad.X[m].mean(0)) / (ad.X[m].std(0) + 1e-12)
        sgn = 1.0 if t < bidx else -1.0
        yv = Z @ (rho * u * sgn)
        sig2 = max(1.0 - float(np.var(yv)), 0.05)
        y[m] = yv + rng.standard_normal(int(m.sum())) * np.sqrt(sig2)
    w = AD3.__new__(AD3)
    w.__dict__.update(ad.__dict__)
    w.rl, w.rs = y / 2.0, -y / 2.0
    w.pL, w.pS = y / 2.0, -y / 2.0
    w.d, w.wt = y, np.abs(y)
    w.dd = np.where(rng.random(ad.n) < 0.5, 1, -1)
    w.flip_year = years[bidx]
    return w


def as_ad3(world):
    w = AD3.__new__(AD3)
    w.__dict__.update(world.__dict__)
    return w


# ================================ STAGE-A modes ================================
K_GRID = (0.0, 0.1, 0.2, 0.3, 0.4)   # [R4-D1] Page allowance grid (ตรึงก่อนรัน)


def mode_detcal(ad):
    """[R4-corrected] grid (W,k): h = q95 ของ per-fold max-CUSUM บน **NOISE = binding null** [D2]
    → FPR ทั้งสอง archetype + detection SINGLE-FLIP (tolerance asymmetric) ต่อ cell ·
    convention bar (external): det ≥80% ∧ FPR ≤5% ทั้งคู่ · เลือก cell = detection สูงสุดที่ผ่าน bar
    (tie → W,k เล็ก — pre-declared) · envelope [D3] + RFLIP คำนวณเฉพาะ cell ที่ผ่าน"""
    res = {}
    print(f"{'W':>4} {'k':>4} {'h':>7} {'FPR_NOISE':>10} {'FPR_STABLE':>11} {'detection':>10} (bar ≥{BAR_DETECT*100:.0f}% ∧ FPR ≤{BAR_FPR*100:.0f}%)")
    for W in W_GRID:
        for kk in K_GRID:
            mx = []
            for i in range(N_CAL):
                w = as_ad3(_noise_world(ad, _rng(f"ad3_hcal_{i}", PERM_ROOT)))
                for (Y, tr, te) in ad.folds:
                    idx = np.where(tr)[0]
                    Xs, ys = w.X[idx], w.d[idx]
                    S, prev, smax = 0.0, None, 0.0
                    for j in range(len(ys) // W):
                        sl = slice(j * W, (j + 1) * W)
                        r = ad.win_rho(Xs[sl], ys[sl])
                        if prev is not None:
                            a = float(r @ prev / (np.linalg.norm(r) * np.linalg.norm(prev) + 1e-12))
                            S = max(0.0, S - a - kk); smax = max(smax, S)
                        prev = r
                    mx.append(smax)
            h = float(np.quantile(mx, 1 - BAR_FPR))

            def fpr_on(worldf, tag):
                fires_folds, tot = 0, 0
                for i in range(N_CAL):
                    w = as_ad3(worldf(ad, _rng(f"ad3_fpr_{tag}_{i}", PERM_ROOT)))
                    for (Y, tr, te) in ad.folds:
                        f, _ = ad.fold_fires(w, tr, None, W, h, kk)
                        fires_folds += (len(f) > 0); tot += 1
                return fires_folds / tot
            fpr_no = fpr_on(_noise_world, f"no{W}{kk}")
            fpr_st = fpr_on(lambda a_, r_: synth_stable_world(a_, r_), f"st{W}{kk}")

            det, early_v, late_v = 0, 0, 0
            for i in range(N_CAL):
                w = as_ad3(single_flip_world(ad, _rng(f"ad3_sf_{i}", PERM_ROOT)))
                hit = False
                for (Y, tr, te) in ad.folds:
                    idx = np.where(tr)[0]
                    truth = np.where(w.yr[idx] == w.flip_year)[0]
                    if len(truth) == 0:
                        continue
                    tpos = int(truth[0])
                    fires, _ = ad.fold_fires(w, tr, None, W, h, kk)
                    for f in fires:
                        if -B_EARLY <= (f - tpos) <= W:
                            hit = True
                        elif f < tpos - B_EARLY:
                            early_v += 1
                        else:
                            late_v += 1
                det += hit
            det_rate = det / N_CAL
            res[(W, kk)] = {"h": h, "fpr_noise": fpr_no, "fpr_stable": fpr_st, "det": det_rate,
                            "early_viol": early_v, "late_viol": late_v}
            print(f"{W:>4} {kk:>4} {h:>7.3f} {fpr_no*100:>9.1f}% {fpr_st*100:>10.1f}% {det_rate*100:>9.1f}%"
                  f"{'  <<< PASS' if (det_rate >= BAR_DETECT and fpr_no <= BAR_FPR + 1e-9 and fpr_st <= BAR_FPR + 1e-9) else ''}",
                  flush=True)
    ok = [c for c in res if res[c]["det"] >= BAR_DETECT and res[c]["fpr_noise"] <= BAR_FPR + 1e-9
          and res[c]["fpr_stable"] <= BAR_FPR + 1e-9]
    if ok:
        sel = min(ok, key=lambda c: (-res[c]["det"], c))
        W, kk = sel
        fc = []
        for i in range(N_CAL):
            w = as_ad3(_noise_world(ad, _rng(f"ad3_env_{i}", PERM_ROOT)))   # [D3] envelope บน binding null
            fc.append(sum(len(ad.fold_fires(w, tr, None, W, res[sel]["h"], kk)[0]) for (Y, tr, te) in ad.folds))
        env = float(np.quantile(fc, 0.95))
        rf = {}
        for P in (3.0, 3.5):
            d2 = sum(any(len(ad.fold_fires(as_ad3(rflip_world(ad, _rng(f"ad3_rf{P}_{i}", PERM_ROOT), P=P)),
                                           tr, None, W, res[sel]["h"], kk)[0]) > 0
                         for (Y, tr, te) in ad.folds) for i in range(60))
            rf[P] = d2 / 60
        print(f"\n[detcal SELECT] (W,k)={sel} · h={res[sel]['h']:.3f} · envelope(NOISE q95)={env:.1f} · RFLIP={rf}")
    else:
        best = max(res, key=lambda c: res[c]["det"] if res[c]["fpr_noise"] <= BAR_FPR + 1e-9 else -1)
        print(f"\n[detcal] ❌ ไม่มี (W,k) ผ่าน convention bar (det≥{BAR_DETECT*100:.0f}% ∧ FPR≤{BAR_FPR*100:.0f}%) "
              f"→ **KILL ที่ STAGE-A ฟรี** (instrument infeasible — pre-registered §3.3) · "
              f"best-at-valid-FPR = {best}: det {res[best]['det']*100:.1f}% @ FPR_NOISE {res[best]['fpr_noise']*100:.1f}%")
    return res


def _noise_world(ad, rng):
    """NOISE archetype: y = pure noise (rho=0)"""
    y = rng.standard_normal(ad.n)
    w = AD3.__new__(AD3)
    w.__dict__.update(ad.__dict__)
    w.rl, w.rs = y / 2.0, -y / 2.0
    w.pL, w.pS = y / 2.0, -y / 2.0
    w.d, w.wt = y, np.abs(y)
    w.dd = np.where(rng.random(ad.n) < 0.5, 1, -1)
    return w


def mode_probe(ad, b, W, h):
    """[M-1] timing + P(fire|null re-fire) + zero-fraction → size B (script-owned)"""
    t0 = time.time(); live = 0; N = 40
    rng = _rng("ad3_probe", PERM_ROOT)
    for k in range(N):
        w = as_ad3(synth_stable_world(ad, _rng(f"ad3_pw_{k}", PERM_ROOT)))
        w.build_exp_caches(gbm=False)
        orders = ad.perm_orders(b, rng)
        v, meta = ad.s1_cond(w, W, h, orders)
        live += (v != 0.0)
    dt = (time.time() - t0) / N
    pfire = live / N
    print(f"[probe] {N} re-fire null draws · {dt*1000:.0f} ms/draw · P(live|null) = {pfire*100:.1f}% "
          f"· zero-fraction = {(1-pfire)*100:.1f}%")
    if pfire > 0:
        B_need = int(np.ceil(100 / pfire / 100) * 100)
        print(f"[probe] live-draw floor 100 → B ≥ {B_need} (≈{B_need*dt/60:.1f} นาที/certify-draw ที่ B0={B0_CAL} → "
              f"certify {CERT_N} draws ≈ {CERT_N*B0_CAL*dt/60:.0f} นาที)")
    else:
        print("[probe] P(live)=0 ใน probe — zero-dominated สุดขั้ว · certify ต้อง report zero-fraction เป็นหลัก")


def mode_regress(ad):
    """machinery — identity + fallback symmetry + detector unit (ทั้งหมด synthetic/identity — ไม่แตะ real d)"""
    # (1) no-fire ≡ expanding — identity exact · [R4-D4] บน SYNTHETIC world เท่านั้น (real d ห้ามเข้า detector ก่อน freeze)
    ws = as_ad3(synth_stable_world(ad, _rng("ad3_reg_syn", PERM_ROOT)))
    ws.build_exp_caches(gbm=False)
    v, meta = ad.s1_cond(ws, W=W_GRID[0], h=float("inf"))
    print(f"[regress-1] S1_cond(h=∞ → no-fire ทุก fold · synthetic) = {v:+.6e} (ต้อง 0 เป๊ะ) · meta={meta}")
    assert v == 0.0, "no-fire ไม่ inert!"
    # (2) detector unit บน SINGLE-FLIP synthetic (truth known)
    w = as_ad3(single_flip_world(ad, _rng("ad3_unit", PERM_ROOT)))
    w.build_exp_caches(gbm=False)
    print(f"[regress-2] SINGLE-FLIP world (flip_year={w.flip_year}) — ตัวอย่าง fires ต่อ fold (W=100, h=2.0):")
    for (Y, tr, te) in ad.folds:
        fires, seq = ad.fold_fires(w, tr, None, 100, 2.0)
        idx = np.where(tr)[0]
        truth = np.where(w.yr[idx] == w.flip_year)[0]
        print(f"  fold {Y}: fires@{fires} · truth@{int(truth[0]) if len(truth) else 'นอก train'}")
    print("[regress] PASS (identity exact · unit-run แสดงผล — เกณฑ์จริงอยู่ detcal)")


def mode_certify(ad, b, W, h):
    """null-of-p re-fire บน STABLE N=CERT_N (chunked-persist) → α*_dec + zero-fraction + p-uniform check"""
    os.makedirs(CERT_DIR, exist_ok=True)
    path = os.path.join(CERT_DIR, f"stable_W{W}.csv")
    done = 0
    if os.path.exists(path):
        done = sum(1 for _ in open(path))
    with open(path, "a") as f:
        for k in range(done, CERT_N):
            w = as_ad3(synth_stable_world(ad, _rng(f"ad3_cert_{k}", PERM_ROOT)))
            w.build_exp_caches(gbm=False)
            obs, _ = ad.s1_cond(w, W, h)
            rng = _rng(f"ad3_certnull_{k}", PERM_ROOT)
            null = []
            for _ in range(B0_CAL):
                orders = ad.perm_orders(b, rng)
                null.append(ad.s1_cond(w, W, h, orders)[0])
            null = np.array(null)
            p = (1 + int((null >= obs).sum())) / (len(null) + 1)
            zf = float((null == 0.0).mean())
            f.write(f"{k},{p:.6f},{zf:.4f},{int(obs != 0.0)}\n"); f.flush()
            if (k + 1) % 20 == 0:
                print(f"  [certify] {k+1}/{CERT_N}", flush=True)
    rows = [l.strip().split(",") for l in open(path)]
    ps = np.array([float(r[1]) for r in rows])[:CERT_N]
    zfs = np.array([float(r[2]) for r in rows])[:CERT_N]
    obs_live = np.array([int(r[3]) for r in rows])[:CERT_N]
    q05 = float(np.quantile(ps, 0.05)); a_dec = min(q05, ALPHA_NOM)
    dec = np.quantile(ps, [0.1, 0.25, 0.5, 0.75, 0.9])
    print(f"[certify W={W}] N={len(ps)} · q05={q05:.3f} → α*_dec=min(q05,{ALPHA_NOM})={a_dec:.3f} · "
          f"FPR@dec <:{(ps < a_dec).mean()*100:.1f}% ≤:{(ps <= a_dec).mean()*100:.1f}%")
    print(f"  zero-fraction null เฉลี่ย = {zfs.mean()*100:.1f}% · obs-live = {obs_live.mean()*100:.1f}% · "
          f"p-deciles(10/25/50/75/90) = {[round(float(x),2) for x in dec]}")
    print(f"  [contiguity-verify — non-vacuous] STABLE p ต้อง ≈ uniform-เมื่อ-live/degenerate-1.0-เมื่อ-zero — "
          f"ตีความคู่ zero-fraction (mixture) · sanity: q05<0.01={'FLAG' if q05 < 0.01 else 'ok'}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "regress"
    ad = AD3.__new__(AD3)
    AD1.__init__(ad)
    print("[AD3] detector card — pre-freeze runs = synthetic เท่านั้น (real-d detector ⛔ จนกว่า freeze)")
    if mode == "regress":
        mode_regress(ad)
    elif mode == "detcal":
        mode_detcal(ad)
    elif mode == "probe":
        b = mode_acf(ad)
        W = int(sys.argv[2]); h = float(sys.argv[3])
        mode_probe(ad, b, W, h)
    elif mode == "certify":
        b = mode_acf(ad)
        W = int(sys.argv[2]); h = float(sys.argv[3])
        mode_certify(ad, b, W, h)
    elif mode == "main":
        raise SystemExit("⛔ freeze gate: FROZEN_DET ว่าง — ต้อง detcal→probe→certify→pin+วินสั่ง commit ก่อน")
    else:
        raise SystemExit(f"unknown mode {mode}")
