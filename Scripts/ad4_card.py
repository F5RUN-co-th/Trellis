"""Card AD-4 — fine-cadence quarterly refit · design v5 + Alt-G/Alt-2 (card §0 NORMATIVE N1-N13 · SPEC_SHA ท้ายไฟล์)
Spec: Plan/TRELLIS-010_card_AD4_fine_cadence.md (commit spec = freeze N11) · claim ยังไม่จอง
null (§0 N1) = C1-full circular shift s ∈ {0..m−1} ของ payoff-tuple (rl,rs,pL,pS) บน prefix rows · global ทุก fold พร้อมกัน (Alt-G)
  · annual arm refit ทุก fold ต่อ draw (Alt-2 · ไม่มี dispatch cache/refit) · statistic S1_rot operative + S1_evalorig descriptive (§0 N8)
eligibility (§0 N2) = KS⁺ integer-lattice: ineligible ⟺ ks_units > KS_T_UNITS·100 · α*_dec (§0 N3) = min(q05 pooled N=400 ของ null ของ main, .05)
contingency (§0 N5) mechanical · rule R6 (§0 N4 verbatim ของวิน) · gates RG1-RG15 (§4-v4 = SSOT) · worlds/N (§0 N6 ห้ามลด)
⛔ certify v1 (ad4_cert_out/ · f99031e) = KNOWN-DEFECT (card §6.1 · F1 null-retention 27.8% · F2 calib-world ≠ H0 · F4 FAIL-loud ไม่ implement)
  · code ของ v1 = checkout f99031e (card §7.1 :148) · oracle CSV = read-only เสมอ (RG7) · ไฟล์นี้หลัง commit spec 8271163 = ขั้น 2 implement (วินอนุมัติ 2026-09-09)
ขั้น 2 implement (§7 scope (1)-(16)): s1_quart(w, perms, segs, rotate_payoff, annual_fn=refit_annual) · refit_annual · label_perms 3 variant + legacy oracle
  · p_one schema 36/37/39 · synth_h0_world / synth_h0_stress_world · cert_chunk v2 (newline="\\n" · os.replace · header identity) · cert_report_v2 (OPERATIVE block + NON-OP)
  · mode_regress RG1-RG15 · governance: SEARCH 2012-2020 · lockbox/guard ไม่แตะ · quarterly บน real payoff = main เท่านั้น (mode_main = stub จนถึงขั้น 4a)
modes: regress [--skip-rg14] · rg14 · cert_v2 <variant> <world> [cell] k0 k1 · pilot k0 k1 · cert_report_v2 · cert_report (v1 คู่เทียบ) · main
runner: cert_v2/pilot บังคับ OPENBLAS/OMP/MKL_NUM_THREADS=1 (ตั้งก่อน import numpy)
"""
import sys, time, os, io, ast as _ast, zlib, hashlib, json, subprocess
if len(sys.argv) > 1 and sys.argv[1] in ("cert_v2", "pilot", "rg14", "regress"):
    for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[_k] = "1"
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ad1_card import AD1, synth_stable_world
from ad2_card import AD2
from tp1_card import fit_predict
from direction_at_real_exit import _rng

PERM_ROOT = 20260723         # seed root (ประกาศ · v1 เดิม · RG7 oracle ผูก)
ALPHA_NOM = 0.05
B_LABEL = 40                 # legacy block-size (v1 · RG7 oracle เท่านั้น · ไม่ใช่ production)
B_PERM, B_ESC = 1000, 5000
CERT_N = 200
CERT_N_POWER = 50            # [R3 ≥50]
B0_CAL = 99
POWER_CELLS = ((1, 0.10), (2, 0.10), (3, 0.10), (1, 0.15), (2, 0.15), (3, 0.15), (1, 0.20))
CERT_DIR = os.path.join(HERE, "ad4_cert_out")            # v1 oracle · READ-ONLY (RG7 guard)
CERT_DIR_V2 = os.path.join(HERE, "ad4_cert_out_v2")      # v2 chunks
CARD_PATH = os.path.join(os.path.dirname(HERE), "Plan", "TRELLIS-010_card_AD4_fine_cadence.md")
FROZEN_CERT = {}             # pin หลัง certify + วินสั่ง freeze-commit — main ปฏิเสธรันจนกว่า pin
VARIANTS = ("c1full", "c1restr", "blk7")                 # §7(1) · ลำดับ = ลำดับ contingency N5
VARIANT_SPEC = {"c1full": ("shift", None, "s ∈ {0..m−1} uniform (full group)"),
                "c1restr": ("shift", (40, -40), "s ∈ [40, m−40] inclusive uniform (C1-restricted)"),
                "blk7": ("block", 7, "block-permutation b=7 บน prefix positions (v5 comparator)")}
WORLDS = ("h0cal", "h0val", "h0stress", "stable", "flip", "h0pilot")
SCHEMA_BASE = ("k,tag,obs,p,null_mean,null_q95,n_distinct,n_ties,p_Q4only,S1_Q2,S1_Q3,S1_Q4,nm_eo,q95_eo,S1_Q2_eo,S1_Q3_eo,S1_Q4_eo,"
               "infl_max_obs,infl_top5_obs,infl_max_null_mean,infl_max_null_q95,null_sd,sd_eo,infl_top5_null_mean,infl_top5_null_q95,"
               "nm_Q2,nm_Q3,nm_Q4,nm_Q2_eo,nm_Q3_eo,nm_Q4_eo,S1_f2016,S1_f2017,S1_f2018,S1_f2019,S1_f2020,"
               "p_gt,n_zero,atom_max,obs_zero,rg12_collapse")                 # v6 C′: +5 (41 base) · p_gt/atom = NON-OP · rg12_collapse = N5 eligibility input
RG12_NORAISE_WORLDS = ("h0cal", "h0val", "h0stress", "h0pilot", "main")   # §0 N5 v6: collapse → flag (H0 = variant ineligible · main = ESTIMATION 0-support E-12(b)) · stable/flip/อื่น → FAIL-loud
SCHEMA_EXTRA = {"flip": ",p_eo", "stable": ",p_eo", "h0stress": ",sigma_logsd,sigma_max_over_med,ramp_share"}
CLOSURE_FILES = ("ad4_card.py", "ad1_card.py", "ad2_card.py", "tp1_card.py", "direction_predictor.py", "direction_at_real_exit.py")
L_YEAR = (1.0, 1.15, 1.3, 1.45, 1.6)                       # §7(5) cross-fold level offset 2016..2020
RG15_BASELINE_SHA = "3763a8488c6132882ed317b576be10d30b642ab92a7ddce8698647e6bee0b918"   # sha256(int64 dp) fold 2016 · synth_stable_world(_rng("ad4_rg15")) · default path ก่อนแก้ tp1_card (2026-09-09)


# ============================ identity helpers ============================
def _sha_lf(path):
    return hashlib.sha256(io.open(path, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def closure_sha():
    h = hashlib.sha256()
    for fn in CLOSURE_FILES:
        h.update(io.open(os.path.join(HERE, fn), "rb").read().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def card_sha_runtime():
    return _sha_lf(CARD_PATH)


def git_state():
    try:
        head = subprocess.run(["git", "-C", HERE, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", "Scripts", "Plan"], capture_output=True, text=True, check=True).stdout.strip())
        return head, int(dirty)
    except Exception:
        return "n/a", -1


def ks_units_int(p):
    """N2 integer-lattice: p บน grid j/100 → C_k = #{p ≤ k/100} · units = max_k (C_k·100 − k·N) ∈ ℤ · ห้าม float"""
    pj = np.rint(np.asarray(p, float) * 100).astype(np.int64)
    assert np.all(np.abs(np.asarray(p) * 100 - pj) < 1e-6), "p ไม่อยู่บน grid 1/100"
    N = len(pj); k = np.arange(1, 101)
    C = (pj[:, None] <= k[None, :]).sum(0)
    return int((C * 100 - k * N).max())


# ============================ world generators ============================
def _prefix_mask(ad):
    """แถว prefix (te_idx[:3q]) ของทุก fold · union"""
    m = np.zeros(ad.n, bool)
    for (Y, tr, te) in ad.folds:
        te_idx = np.where(te)[0]; q = len(te_idx) // 4
        m[te_idx[:3 * q]] = True
    return m


def _mk_world(ad, y, rng):
    w = AD4.__new__(AD4)
    w.__dict__.update(ad.__dict__)
    w.rl, w.rs = y / 2.0, -y / 2.0
    w.pL, w.pS = y / 2.0, -y / 2.0
    w.d, w.wt = y, np.abs(y)
    w.dd = np.where(rng.random(ad.n) < 0.5, 1, -1)
    return w


def synth_h0_world(ad, rng, rho=0.10, nsig=4, q4_relation=True, sigma=None):
    """H0-C (§3.5-v4): ปี < 2016 relation ρ (= STABLE) · test years: prefix rows labels = noise (ρ=0) · Q4 (ไม่อยู่ใน prefix) คง relation ρ
    sigma: array ต่อแถว (h0stress) คูณเฉพาะ noise term (§7(5)) · None = 1"""
    perm = rng.permutation(ad.NF); fa = perm[:nsig]
    u = np.zeros(ad.NF); u[fa] = 1.0
    pref = _prefix_mask(ad)
    tyears = {f[0] for f in ad.folds}; test_mask = np.array([y_ in tyears for y_ in ad.yr])
    y = np.zeros(ad.n)
    for Y in sorted(set(ad.yr)):
        m = ad.yr == Y
        Z = (ad.X[m] - ad.X[m].mean(0)) / (ad.X[m].std(0) + 1e-12)
        yv = Z @ (rho * u)
        kill = pref[m] if q4_relation else test_mask[m]          # q4_relation=True: prefix rows = noise · False: ทุกแถว test-year = noise (F10)
        yv = np.where(kill, 0.0, yv)
        sig2 = max(1.0 - float(np.var(Z @ (rho * u))), 0.05)      # noise scale แบบ synth_stable (จาก relation เต็ม)
        eps = rng.standard_normal(int(m.sum())) * np.sqrt(sig2)
        if sigma is not None:
            eps = eps * sigma[m]
        y[m] = yv + eps
    return _mk_world(ad, y, rng)


def stress_sigma(ad, rng, phi=0.97, df=5, ramp=2.0):
    """σ_i บนลำดับแถว test-year 2016→2020 ต่อกัน (§7(5) pin): log σ_i = a_i + ln L_year + ln r_k
    a_i = φ·a_{i−1} + √(1−φ²)·η_i · η ~ t(df)/√(df/(df−2)) · a_0 ~ N(0,1) · r_k = 1+(ramp−1)k/(n_te−1) reset ต่อปี · แถว base = 1
    คืน (sigma_full_n, sigma_logsd, sigma_max_over_med, ramp_share)"""
    years = sorted({int(f[0]) for f in ad.folds})
    idx = np.concatenate([np.where(ad.yr == str(Y))[0] if ad.yr.dtype.kind in "SU" else np.where(ad.yr == Y)[0] for Y in years])
    n = len(idx)
    a = np.empty(n); a[0] = rng.standard_normal()
    eta = rng.standard_t(df, size=n) / np.sqrt(df / (df - 2))
    c = np.sqrt(1 - phi ** 2)
    for i in range(1, n):
        a[i] = phi * a[i - 1] + c * eta[i]
    logr, logL, contrast = [], [], []
    for j, Y in enumerate(years):
        m = int((ad.yr == (str(Y) if ad.yr.dtype.kind in "SU" else Y)).sum())
        k = np.arange(m); logr.append(np.log(1 + (ramp - 1) * k / (m - 1)))
        logL.append(np.full(m, np.log(L_YEAR[j])))
        q = m // 4; contrast.append(1 + (ramp - 1) * (3 * q - 1) / (m - 1))
    ls = a + np.concatenate(logL) + np.concatenate(logr)
    sig = np.ones(ad.n); sig[idx] = np.exp(ls)
    sd = float(ls.std(ddof=1))
    return sig, sd, float(np.exp(ls).max() / np.median(np.exp(ls))), float(np.mean(np.log(contrast)) / sd)


def synth_h0_stress_world(ad, rng, phi=0.97, df=5, ramp=2.0, rho=0.10, nsig=4):
    sig, sd, ratio, share = stress_sigma(ad, rng, phi, df, ramp)
    w = synth_h0_world(ad, rng, rho=rho, nsig=nsig, q4_relation=True, sigma=sig)
    w.sigma_stats = (sd, ratio, share)
    return w


def intra_flip_world(ad, rng, pos_q=1, rho=0.10, nsig=4):
    """INTRA-YEAR-FLIP (v1 เดิม · H1 cells · POWER_CELLS ไม่แตะ)"""
    perm = rng.permutation(ad.NF); fa = perm[:nsig]
    u = np.zeros(ad.NF); u[fa] = 1.0
    y = np.zeros(ad.n)
    for Y in sorted(set(ad.yr)):
        m = ad.yr == Y
        idx = np.where(m)[0]
        Z = (ad.X[m] - ad.X[m].mean(0)) / (ad.X[m].std(0) + 1e-12)
        sgn = np.ones(len(idx))
        if int(Y) >= 2016:
            qy = len(idx) // 4
            sgn[pos_q * qy:] = -1.0
        yv = (Z @ (rho * u)) * sgn
        sig2 = max(1.0 - float(np.var(Z @ (rho * u))), 0.05)
        y[m] = yv + rng.standard_normal(len(idx)) * np.sqrt(sig2)
    return _mk_world(ad, y, rng)


# ============================ annual arm (Alt-2 · refit ทุก fold ต่อ draw) ============================
def refit_annual(w, i, rl_arr, rs_arr):
    """annual arm ของ fold i refit บน base tr (ปี < Y) ด้วย labels ที่ส่งเข้า (rotated แล้ว) → (dpA, w_vec)
    fold 2016 refit ≡ cache (base ไม่มีแถวหมุน) · RG13 = regression ของ identity นี้ · ไม่มี dispatch"""
    Y, tr, te = w.folds[i]
    assert w.keep_all.sum() > 0, "keep=zeros ที่ call-site ad4 (RG3)"
    return fit_predict(w.X, w.keep_all, tr, te, rl_arr[tr], rs_arr[tr], w.dd, return_w=True)


def _nanstat(a, kind):
    """influence summary ข้าม draw ที่ share นิยามได้ (la ≢ 0) · ไม่มีเลย = nan (v6 C′ · atom ที่ 0)"""
    a = np.asarray(a, float); a = a[~np.isnan(a)]
    if len(a) == 0: return float("nan")
    return float(a.mean()) if kind == "mean" else float(np.quantile(a, .95, method="linear"))


class RG12Collapse(RuntimeError):
    """RG12 v6: null ยุบ (sd=0 หรือทุก draw == obs) ใน world ที่ไม่อยู่ใน RG12_NORAISE_WORLDS"""


class AD4(AD2):
    # ---------- segments ----------
    def fold_seg(self, te):
        """คืน (te_idx, q, prefix_idx) — quartile = n//4 · remainder→Q4 [R4-D]"""
        te_idx = np.where(te)[0]
        q = len(te_idx) // 4
        return te_idx, q, te_idx[:3 * q]

    # ---------- caches (§7(2b) · override ใน ad4 เท่านั้น · gbm ไม่มี) ----------
    def build_exp_caches(self, gbm=False):
        """PAY_EXP_LIN (v1) + DIR_EXP_LIN[i]=dpA + W_EXP_LIN[i]=w_vec (obs s=0 + RG13 เท่านั้น) · ไม่มี GBM"""
        self.PAY_EXP_LIN, self.DIR_EXP_LIN, self.W_EXP_LIN = {}, {}, {}
        for i, (Y, tr, te) in enumerate(self.folds):
            assert self.keep_all.sum() > 0, "keep=zeros ที่ call-site ad4 (RG3)"
            dpA, wv = fit_predict(self.X, self.keep_all, tr, te, self.rl[tr], self.rs[tr], self.dd, return_w=True)
            self.DIR_EXP_LIN[i] = dpA; self.W_EXP_LIN[i] = wv
            self.PAY_EXP_LIN[i] = np.where(dpA == 1, self.pL[te], self.pS[te])

    # ---------- null: label perms ----------
    def label_perms(self, rng, variant="c1full"):
        """คืน perms ต่อ fold (list ตาม self.folds): shift variant → int s · block variant → order array (bijection บน prefix)
        legacy40 = v1 block-permutation b=40 (RG7 oracle เท่านั้น · rng stream = rng.permutation(nblk) ต่อ fold ตามลำดับ folds)"""
        out = []
        for (Y, tr, te) in self.folds:
            te_idx, q, prefix_idx = self.fold_seg(te)
            m = len(prefix_idx)
            if variant == "legacy40":
                nblk = m // B_LABEL + (1 if m % B_LABEL else 0)
                blocks = [np.arange(k * B_LABEL, min((k + 1) * B_LABEL, m)) for k in range(nblk)]
                out.append(np.concatenate([blocks[j] for j in rng.permutation(nblk)]))
                continue
            kind, par, _ = VARIANT_SPEC[variant]
            if kind == "shift":
                lo, hi = (0, m - 1) if par is None else (par[0], m + par[1])   # inclusive
                assert 0 <= lo <= hi <= m - 1, f"variant {variant}: [{lo},{hi}] ไม่ถูกต้อง m={m}"
                out.append(int(rng.integers(lo, hi + 1)))
            else:
                b = par
                nblk = m // b + (1 if m % b else 0)
                blocks = [np.arange(k * b, min((k + 1) * b, m)) for k in range(nblk)]
                out.append(np.concatenate([blocks[j] for j in rng.permutation(nblk)]))
        return out

    @staticmethod
    def perm_order(perm, m):
        """int s → circular shift order (j → (j+s) mod m) · array → ใช้ตรง (bijection)"""
        if isinstance(perm, (int, np.integer)):
            return (np.arange(m) + int(perm)) % m
        return np.asarray(perm)

    def apply_perms(self, w, perms):
        """Alt-G: apply s-vector บน copy global ของ (rl,rs,pL,pS) ครั้งเดียว · prefix ต่าง fold disjoint ตามปี"""
        rl, rs, pL, pS = w.rl.copy(), w.rs.copy(), w.pL.copy(), w.pS.copy()
        for i, (Y, tr, te) in enumerate(w.folds):
            te_idx, q, prefix_idx = self.fold_seg(te)
            order = self.perm_order(perms[i], len(prefix_idx))
            src = prefix_idx[order]
            rl[prefix_idx] = w.rl[src]; rs[prefix_idx] = w.rs[src]
            pL[prefix_idx] = w.pL[src]; pS[prefix_idx] = w.pS[src]
        return rl, rs, pL, pS

    # ---------- statistic ----------
    def s1_quart(self, w, perms=None, segs=(1, 2, 3), rotate_payoff=True, annual_fn=refit_annual, detail=False, folds=None):
        """S1 = mean over Q2-Q4 rows ของ (pay_quarterly − pay_annual) · pin: float(np.concatenate(la).mean()) · ลำดับ (fold, s ascending)
        rotate_payoff=True (production · N1): ทั้งสอง arm ประเมินด้วย payoff ที่หมุน · annual arm = annual_fn (refit ทุก fold ต่อ draw)
        rotate_payoff=False = legacy v1 path (RG7 oracle เท่านั้น): payoff ไม่หมุน · annual arm = PAY_EXP_LIN cache
        detail=True → dict(la, la_eo, seg, fold, dpA) · folds=None = ทุก fold (default · bit-identical) · folds=(i,) = เฉพาะ fold i (v6 · RG14 local arm)"""
        if perms is not None and rotate_payoff:
            rl_arr, rs_arr, pL_arr, pS_arr = self.apply_perms(w, perms)
        else:
            rl_arr, rs_arr, pL_arr, pS_arr = w.rl, w.rs, w.pL, w.pS
        la, la_eo, seg_id, fold_id, dpA_all, trm_l, sl_l, seg_l = [], [], [], [], {}, [], [], []
        for i, (Y, tr, te) in enumerate(w.folds):
            if folds is not None and i not in folds:
                continue
            te_idx, q, prefix_idx = self.fold_seg(te)
            pos = {v: k for k, v in enumerate(te_idx)}
            if perms is not None and not rotate_payoff:
                # legacy v1 (:50-54): copy สดต่อ fold · หมุน (rl,rs) เฉพาะ prefix ของ fold นี้ (local action) · payoff ไม่หมุน · annual = cache
                order = self.perm_order(perms[i], len(prefix_idx))
                rl_arr = w.rl.copy(); rs_arr = w.rs.copy()
                rl_arr[prefix_idx] = w.rl[prefix_idx[order]]; rs_arr[prefix_idx] = w.rs[prefix_idx[order]]
            if rotate_payoff:
                dpA, wv = annual_fn(w, i, rl_arr, rs_arr)
                dpA_all[i] = (dpA, wv)
            for s in segs:
                seg = te_idx[s * q:(s + 1) * q] if s < 3 else te_idx[3 * q:]
                cutoff = w.dayix[seg[0]] - w.Nemb
                trm = w.dayix < cutoff                              # expanding + prefix · embargo dayix [FB-3]
                segm = np.zeros(w.n, bool); segm[seg] = True
                assert w.keep_all.sum() > 0, "keep=zeros ที่ call-site ad4 (RG3)"
                dp = fit_predict(w.X, w.keep_all, trm, segm, rl_arr[trm], rs_arr[trm], w.dd)
                sl = [pos[r] for r in seg]
                if rotate_payoff:
                    payQ = np.where(dp == 1, pL_arr[segm], pS_arr[segm])
                    payA = np.where(dpA[sl] == 1, pL_arr[seg], pS_arr[seg])
                    payQ_eo = np.where(dp == 1, w.pL[segm], w.pS[segm])
                    payA_eo = np.where(dpA[sl] == 1, w.pL[seg], w.pS[seg])
                    la_eo.append(payQ_eo - payA_eo)
                else:
                    payQ = np.where(dp == 1, w.pL[segm], w.pS[segm])
                    payA = w.PAY_EXP_LIN[i][sl]
                la.append(payQ - payA)
                seg_id.append(s); fold_id.append(i); trm_l.append(trm); sl_l.append(sl); seg_l.append(seg)
        if detail:
            return {"la": la, "la_eo": la_eo, "seg": seg_id, "fold": fold_id, "dpA": dpA_all, "S1": float(np.concatenate(la).mean()),
                    "trm": trm_l, "sl": sl_l, "segrows": seg_l}
        return float(np.concatenate(la).mean())

    # ---------- p-value (§7(4)) ----------
    @staticmethod
    def rg12_code(null, obs, la_obs_zero):
        """RG12 v6 (C′ · §0 N7) รหัส collapse — exact equality (ไม่ใช้ float sd: ค่าคงที่ที่ B=99 ได้ sd ~1e-17 ≠ 0 [F1 Engineer 09-24])
        0 = ไม่ collapse · 1 = ทุก draw == obs ∧ la_obs ≡ 0 (Q≡A ทุกแถว) · 2 = ทุก draw == obs ∧ la_obs ≢ 0 · 3 = null ค่าเดียว ≠ obs
        · ties/atoms ธรรมชาติ (atom ที่ 0 เมื่อ dp≡dpA · Q4 ไม่หมุน) ≠ collapse — p_ge นับ ties เป็น exceedance (conservative)
        · NaN: ไม่อยู่ใน scope (input จริง finite ทั้งหมด วัด 09-24 · residual C)"""
        null = np.asarray(null, float)
        if np.all(null == obs):
            return 1 if la_obs_zero else 2
        if len(np.unique(null)) == 1:
            return 3
        return 0

    def p_one(self, w, tag, B0=B0_CAL, variant="c1full", world=None):
        """คืน dict ตาม schema (41 base + p_eo [flip/stable] + σ 3 [h0stress]) · RG12 รหัส collapse ใน p_one: world ∈ RG12_NORAISE_WORLDS → flag (คอลัมน์ rg12_collapse = รหัส 0-3) · อื่น → raise RG12Collapse"""
        rng = _rng(tag, PERM_ROOT)
        assert w.folds is self.folds, "RG8 folds identity"
        d0 = self.s1_quart(w, None, detail=True)
        obs = d0["S1"]
        nulls, nulls_eo, nseg, nseg_eo, nq4, imax, itop = [], [], [], [], [], [], []
        xh = hashlib.sha256(w.X.tobytes()).hexdigest()
        for _ in range(B0):
            perms = self.label_perms(rng, variant)
            d = self.s1_quart(w, perms, detail=True)
            nulls.append(d["S1"]); nulls_eo.append(float(np.concatenate(d["la_eo"]).mean()))
            nseg.append(_seg_means(d["la"], d["seg"])); nseg_eo.append(_seg_means(d["la_eo"], d["seg"]))
            nq4.append(nseg[-1][2])
            x = np.abs(np.concatenate(d["la"])); sx = x.sum()                # v6 C′: draw ที่ la ≡ 0 (atom ที่ 0) → share ไม่นิยาม = nan (ไม่ใช่ 0/0 warning)
            imax.append(x.max() / sx if sx > 0 else np.nan); itop.append(np.sort(x)[-5:].sum() / sx if sx > 0 else np.nan)
        assert hashlib.sha256(w.X.tobytes()).hexdigest() == xh, "RG3 X-untouched"
        null = np.array(nulls); null_eo = np.array(nulls_eo)
        u_, cnt_ = np.unique(null, return_counts=True)
        n_distinct = len(u_); n_ties = int((null == obs).sum())
        code = self.rg12_code(null, obs, not np.any(np.concatenate(d0["la"])))
        if code and world not in RG12_NORAISE_WORLDS:
            raise RG12Collapse(f"RG12 collapse รหัส {code} (§0 N5 FAIL-loud · world={world}): n_distinct={n_distinct} n_ties={n_ties} (tag {tag})")
        p = (1 + int((null >= obs).sum())) / (B0 + 1)                   # operative (ties = exceedance)
        p_gt = (1 + int((null > obs).sum())) / (B0 + 1)                 # NON-OP: tie-loss / sensitivity bound เท่านั้น
        so = _seg_means(d0["la"], d0["seg"]); so_eo = _seg_means(d0["la_eo"], d0["seg"])
        p_q4 = (1 + int((np.array(nq4) >= so[2]).sum())) / (B0 + 1)
        x0 = np.abs(np.concatenate(d0["la"]))
        fm = _fold_means(d0["la"], d0["fold"], len(w.folds))
        nseg = np.array(nseg); nseg_eo = np.array(nseg_eo)
        out = {"obs": obs, "p": p, "null_mean": float(null.mean()), "null_q95": float(np.quantile(null, .95, method="linear")),
               "n_distinct": n_distinct, "n_ties": n_ties, "p_Q4only": p_q4,
               "p_gt": p_gt, "n_zero": int((null == 0.0).sum()), "atom_max": int(cnt_.max()), "obs_zero": int(obs == 0.0), "rg12_collapse": int(code),
               "S1_Q2": so[0], "S1_Q3": so[1], "S1_Q4": so[2],
               "nm_eo": float(null_eo.mean()), "q95_eo": float(np.quantile(null_eo, .95, method="linear")),
               "S1_Q2_eo": so_eo[0], "S1_Q3_eo": so_eo[1], "S1_Q4_eo": so_eo[2],
               "infl_max_obs": float(x0.max() / x0.sum()) if x0.sum() > 0 else float("nan"), "infl_top5_obs": float(np.sort(x0)[-5:].sum() / x0.sum()) if x0.sum() > 0 else float("nan"),
               "infl_max_null_mean": _nanstat(imax, "mean"), "infl_max_null_q95": _nanstat(imax, "q95"),
               "null_sd": float(null.std(ddof=1)), "sd_eo": float(null_eo.std(ddof=1)),
               "infl_top5_null_mean": _nanstat(itop, "mean"), "infl_top5_null_q95": _nanstat(itop, "q95"),
               "nm_Q2": float(nseg[:, 0].mean()), "nm_Q3": float(nseg[:, 1].mean()), "nm_Q4": float(nseg[:, 2].mean()),
               "nm_Q2_eo": float(nseg_eo[:, 0].mean()), "nm_Q3_eo": float(nseg_eo[:, 1].mean()), "nm_Q4_eo": float(nseg_eo[:, 2].mean())}
        for j, (Y, tr, te) in enumerate(w.folds):
            out[f"S1_f{Y}"] = fm[j]
        if world in ("flip", "stable"):
            out["p_eo"] = (1 + int((null_eo >= obs).sum())) / (B0 + 1)     # obs_eo ≡ obs (N8)
        if world == "h0stress":
            out["sigma_logsd"], out["sigma_max_over_med"], out["ramp_share"] = w.sigma_stats
        return out

    def p_one_legacy(self, w, tag, B0=B0_CAL):
        """v1 path เป๊ะ (RG7 oracle · in-memory · rng stream = v1): obs · null จาก label_perms(rng,'legacy40') · rotate_payoff=False"""
        rng = _rng(tag, PERM_ROOT)
        obs = self.s1_quart(w, None, rotate_payoff=False)
        null = np.array([self.s1_quart(w, self.label_perms(rng, "legacy40"), rotate_payoff=False) for _ in range(B0)])
        p = (1 + int((null >= obs).sum())) / (len(null) + 1)
        return obs, p, float(null.mean()), float(np.quantile(null, 0.95))


def _seg_means(la, seg):
    """pooled row-level mean ต่อ segment (จากชิ้นเดิม · ห้าม mean-of-means)"""
    out = []
    for s in (1, 2, 3):
        parts = [a for a, sg in zip(la, seg) if sg == s]
        out.append(float(np.concatenate(parts).mean()) if parts else float("nan"))
    return out


def _fold_means(la, fold, nf):
    out = []
    for i in range(nf):
        parts = [a for a, f in zip(la, fold) if f == i]
        out.append(float(np.concatenate(parts).mean()) if parts else float("nan"))
    return out


def as_ad4(world):
    w = AD4.__new__(AD4)
    w.__dict__.update(world.__dict__)
    return w


# ============================ tags (RG9) ============================
def world_tag(world, cell, k):
    return f"ad4_v2_{world}_c{cell}_{k}" if cell is not None else f"ad4_v2_{world}_{k}"


def null_tag(variant, world, cell, k):
    return f"ad4_v2p_{variant}_{world}_c{cell}_{k}" if cell is not None else f"ad4_v2p_{variant}_{world}_{k}"


def tag_universe():
    """ทุก tag ของ certify v2 + pilot + oracle namespace (v1) + RG14 · ทุก mode"""
    tags = []
    for world in ("h0cal", "h0val", "h0stress", "stable"):
        for k in range(CERT_N):
            tags.append(world_tag(world, None, k))
            for v in VARIANTS:
                tags.append(null_tag(v, world, None, k))
    for ci in range(len(POWER_CELLS)):
        for k in range(CERT_N_POWER):
            tags.append(world_tag("flip", ci, k))
            for v in VARIANTS:
                tags.append(null_tag(v, "flip", ci, k))
    for k in range(30):
        tags.append(f"ad4_v2_h0pilot_{k}"); tags.append(null_tag("c1full", "h0pilot", None, k))
    for k in range(CERT_N):
        tags.append(f"ad4_cert_s_{k}"); tags.append(f"ad4_certp_{k}")
    for ci in range(len(POWER_CELLS)):
        for k in range(CERT_N_POWER):
            tags.append(f"ad4_pw_{ci}_{k}"); tags.append(f"ad4_pwp_{ci}_{k}")
    tags += list(RG14_TAGS) + [f"{t}_p" for t in RG14_TAGS] + ["ad4_reg", "ad4_reg_p", "ad4_reg_pone", "ad4_rg15", "ad4_rg13", "ad4_rg4", "ad4_h0c_reg", "ad4_stress_reg", "engrg12_stable_2", "engrg12_stable_2_p", "ad4_rg12_fix"]
    return tags


def rg9_check(verbose=True):
    tags = tag_universe()
    crcs = {zlib.crc32(t.encode()) & 0xffffffff for t in tags}
    n = len(tags)
    assert len(set(tags)) == n, "tag ซ้ำ"
    assert len(crcs) == n, f"RG9 crc32 collision: {n - len(crcs)}"
    p_birthday = 1 - np.exp(-n * (n - 1) / (2 * 2 ** 32))
    if verbose:
        print(f"[RG9] tag universe n={n} · crc32 unique ✓ · birthday P(collision)={p_birthday*100:.3f}% (emit · ไม่ pin)")
    return n, p_birthday


# ============================ structural AST assert (§7(2b) R-5) ============================
def annual_fn_ast_check(src=None):
    """call-site ของ s1_quart ที่ส่ง annual_fn ≠ refit_annual ต้องมี 1 แห่งเดียว = ใน mode_regress · ห้าม **kwargs/*args · positional ≤ 2 (w, perms)
    · def refit_annual มี 1 แห่งที่ col 0 · ห้ามผูกชื่อ refit_annual นอก def (assign/alias/import) · src=None = ไฟล์นี้ (self-test ส่ง source ที่ mutate)"""
    src = src if src is not None else io.open(os.path.abspath(__file__), encoding="utf-8").read()
    tree = _ast.parse(src)
    sites, kw_sites, rebinds, pos_sites = [], [], [], []
    def enclosing(node, stack):
        # outermost def (nested closure ภายใน mode_regress = ไม่มีตัวตนระดับ module · นับเป็น site ของ mode_regress)
        for f in stack:
            if isinstance(f, (_ast.FunctionDef, _ast.AsyncFunctionDef)): return f.name
        return "<module>"
    stack = []
    def visit(node):
        stack.append(node)
        for ch in _ast.iter_child_nodes(node):
            if isinstance(ch, _ast.Call) and isinstance(ch.func, _ast.Attribute) and ch.func.attr == "s1_quart":
                if any(k.arg is None for k in ch.keywords): kw_sites.append(enclosing(ch, stack))
                if len(ch.args) > 2 or any(isinstance(a_, _ast.Starred) for a_ in ch.args): pos_sites.append(enclosing(ch, stack))
                for k in ch.keywords:
                    if k.arg == "annual_fn" and not (isinstance(k.value, _ast.Name) and k.value.id == "refit_annual"):
                        sites.append(enclosing(ch, stack))
            if isinstance(ch, (_ast.Assign, _ast.AnnAssign, _ast.AugAssign)):
                tg = ch.targets if isinstance(ch, _ast.Assign) else [ch.target]
                if any(isinstance(t, _ast.Name) and t.id == "refit_annual" for t in tg): rebinds.append(enclosing(ch, stack))
            if isinstance(ch, (_ast.Import, _ast.ImportFrom)) and any((a_.asname or a_.name) == "refit_annual" for a_ in ch.names):
                rebinds.append(enclosing(ch, stack))
            visit(ch)
        stack.pop()
    visit(tree)
    defs = [n for n in _ast.walk(tree) if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef)) and n.name == "refit_annual"]
    assert sites == ["mode_regress"], f"annual_fn ≠ refit_annual call-site ต้องมี 1 แห่ง = mode_regress · พบ {sites}"
    assert not kw_sites, f"s1_quart call-site มี **kwargs: {kw_sites}"
    assert not pos_sites, f"s1_quart call-site positional > 2 หรือ *args: {pos_sites}"
    assert len(defs) == 1 and defs[0].col_offset == 0, f"def refit_annual ต้องมี 1 แห่งที่ module level · พบ {len(defs)}"
    assert not rebinds, f"ชื่อ refit_annual ถูก assign/alias นอก def: {rebinds}"
    return True


def ast_guard_selftest():
    """mutation self-test ของ guard (F3 execution-review): source ที่ mutate 7 ทางต้องทำให้ annual_fn_ast_check raise ทุกทาง"""
    src = io.open(os.path.abspath(__file__), encoding="utf-8").read()
    muts = [
        "\ndef _m(ad, w):\n    return ad.s1_quart(w, None, annual_fn=lambda w_, i, a, b: (w_.DIR_EXP_LIN[i], w_.W_EXP_LIN[i]))\n",
        "\ndef _m(ad, w, kw):\n    return ad.s1_quart(w, None, **kw)\n",
        "\ndef _m(ad, w, a):\n    return ad.s1_quart(w, None, (1, 2, 3), True, a)\n",
        "\ndef _m(ad, w, args):\n    return ad.s1_quart(w, *args)\n",
        "\ndef refit_annual(w, i, a, b):\n    return None\n",
        "\nrefit_annual = None\n",
        "\nfrom ad1_card import AD1 as refit_annual\n",
    ]
    for j, m in enumerate(muts):
        try:
            annual_fn_ast_check(src + m)
        except AssertionError:
            continue
        raise AssertionError(f"AST guard self-test: mutation #{j+1} ไม่ถูกจับ")
    return True


# ============================ chunk protocol (§7(6)) ============================
def header_fields(ad, variant, world, cell):
    head, dirty = git_state()
    return {"variant": variant, "world": world, "cell": "" if cell is None else cell, "PERM_ROOT": PERM_ROOT, "B0": B0_CAL,
            "N": CERT_N_POWER if world == "flip" else (30 if world == "h0pilot" else CERT_N),
            "POWER_CELLS": str(POWER_CELLS).replace(" ", ""), "alpha_cap": ALPHA_NOM,
            "closure_sha": closure_sha(), "SPEC_SHA": SPEC_SHA, "card_sha_runtime": card_sha_runtime(),
            "git_head": head, "dirty": dirty, "n": ad.n, "NF": ad.NF, "Nemb": int(ad.Nemb),
            "fold_sizes": str([int(t.sum()) for (_, _, t) in ad.folds]).replace(" ", ""),
            "prefix_sizes": str([3 * (int(t.sum()) // 4) for (_, _, t) in ad.folds]).replace(" ", ""),   # card :91 "prefix [114,…]" (F9)
            "X_sha": hashlib.sha256(ad.X.tobytes()).hexdigest(), "dayix_sha": hashlib.sha256(ad.dayix.tobytes()).hexdigest(),
            "numpy": np.__version__, "blas": "openblas", "threads": os.environ.get("OPENBLAS_NUM_THREADS", "?"), "field_precision": "6dp"}


def schema_for(world):
    return SCHEMA_BASE + SCHEMA_EXTRA.get(world, "")


def make_world(ad, world, cell, k):
    rng = _rng(world_tag(world, cell, k), PERM_ROOT)
    if world in ("h0cal", "h0val", "h0pilot"):
        return as_ad4(synth_h0_world(ad, rng))
    if world == "h0stress":
        return as_ad4(synth_h0_stress_world(ad, rng))
    if world == "stable":
        return as_ad4(synth_stable_world(ad, rng))
    if world == "flip":
        pos_q, rho = POWER_CELLS[cell]
        return as_ad4(intra_flip_world(ad, rng, pos_q=pos_q, rho=rho))
    raise ValueError(world)


def cert_chunk(ad, variant, world, cell, k0, k1):
    """chunk-file `.tmp` (newline="\\n") → os.replace · header 2 บรรทัด (# identity · # schema) · row-count assert · oracle dir ไม่ถูกเปิดเขียน"""
    assert variant in VARIANTS and world in WORLDS
    assert (world == "flip") == (cell is not None), "cell เฉพาะ world=flip"
    if world == "h0stress": assert variant == "c1full" or os.environ.get("AD4_CONTINGENCY") == variant, "h0stress = PRIMARY (+contingency variant ผ่าน AD4_CONTINGENCY)"
    hf = header_fields(ad, variant, world, cell)
    assert hf["card_sha_runtime"] == SPEC_SHA, f"N11: card_sha_runtime {hf['card_sha_runtime'][:12]} ≠ SPEC_SHA {SPEC_SHA[:12]} — card ถูกแก้หลัง commit spec · หยุด"
    annual_fn_ast_check(); rg9_check(verbose=False); require_receipt()
    d = os.path.join(CERT_DIR_V2, variant); os.makedirs(d, exist_ok=True)
    name = f"{world}_c{cell}_{k0}_{k1}.csv" if cell is not None else f"{world}_{k0}_{k1}.csv"
    path = os.path.join(d, name); tmp = path + ".tmp"
    assert not os.path.exists(path), f"chunk มีอยู่แล้ว {path} (ไม่ append · ไม่ทับ)"
    schema = schema_for(world); cols = schema.split(",")
    rows = []
    t0 = time.time()
    for k in range(k0, k1):
        w = make_world(ad, world, cell, k); w.build_exp_caches()
        r = ad.p_one(w, null_tag(variant, world, cell, k), B0=B0_CAL, variant=variant, world=world)
        vals = [str(k), null_tag(variant, world, cell, k)] + [f"{r[c]:.6f}" if isinstance(r[c], float) else str(r[c]) for c in cols[2:]]
        rows.append(",".join(vals))
        if world == "h0pilot":
            print(f"  [{variant}/h0pilot] k={k} · {time.time()-t0:.0f}s (persist เท่านั้น · ไม่พิมพ์ p/obs — RI-5)", flush=True)
        else:
            print(f"  [{variant}/{world}{'' if cell is None else '/c'+str(cell)}] k={k} p={r['p']:.2f} obs={r['obs']:+.4f} · {time.time()-t0:.0f}s", flush=True)
        if r["rg12_collapse"]:
            print(f"  ⚠ RG12 collapse รหัส {r['rg12_collapse']} · {variant}/{world} k={k} · row บันทึกตามจริง" + (" → §0 N5: variant ineligible" if world in ("h0cal", "h0val") else " (NON-OP · นับใน readout)"), flush=True)
    assert len(rows) == k1 - k0, "row-count"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f:
        hdr = "# " + json.dumps(hf, ensure_ascii=False)
        assert json.loads(hdr[2:]) == hf, "header round-trip (F1 execution-review)"
        f.write(hdr + "\n")
        f.write("# schema: " + schema + "\n")
        f.write("\n".join(rows) + "\n")
    os.replace(tmp, path)
    print(f"[cert_v2] {variant}/{world} cell={cell} draws {k0}..{k1-1} → {path} · {(time.time()-t0)/max(1,k1-k0):.1f} s/draw")


def read_chunks():
    """อ่านทุก chunk v2 → dict[(variant, world, cell)] = (header dict, schema, rows list of dict)"""
    out = {}
    if not os.path.isdir(CERT_DIR_V2): return out
    for variant in VARIANTS:                                              # เฉพาะ dir ของ variant (CERT_DIR_V2 มี rg14/ + regress_receipt.json ด้วย)
        d = os.path.join(CERT_DIR_V2, variant)
        if not os.path.isdir(d): continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".csv"): continue
            lines = io.open(os.path.join(d, fn), encoding="utf-8").read().split("\n")
            hf = json.loads(lines[0][2:])
            assert lines[1].startswith("# schema: "), fn
            schema = lines[1][len("# schema: "):]; cols = schema.split(",")
            world = hf["world"]; cell = hf["cell"] if hf["cell"] != "" else None
            key = (variant, world, cell)
            rows = [dict(zip(cols, l.split(","))) for l in lines[2:] if l.strip()]
            if key in out:
                h0, s0, r0 = out[key]
                for f_ in hf:
                    assert h0.get(f_) == hf[f_], f"header field {f_} ต่างกันภายใน series {key}: {h0.get(f_)} vs {hf[f_]}"
                assert s0 == schema, f"schema ต่างกันภายใน series {key}"
                out[key] = (h0, s0, r0 + rows)
            else:
                out[key] = (hf, schema, rows)
    for key, (hf, schema, rows) in out.items():
        ks = sorted(int(r["k"]) for r in rows)
        assert ks == list(range(len(ks))), f"continuity {key}: k ไม่ต่อเนื่อง"
        assert len(rows) <= int(hf["N"]), f"{key}: rows {len(rows)} > N {hf['N']}"
        if len(rows) < int(hf["N"]): print(f"  [staging] {key}: {len(rows)}/{hf['N']} draws (ยังไม่ครบ)")
    return out


# ============================ cert_report_v2 (§7(7)) ============================
READOUT_REGISTRY = [
    ("alpha_dec", "chunk-col"), ("eligibility_ks", "chunk-col"), ("branch_R6", "chunk-col"), ("rank_threshold", "definitional"),
    ("FPR_at_alpha_pooled", "chunk-col"), ("FPR_cal", "chunk-col"), ("FPR_val", "chunk-col"), ("rejection_at_redundant", "chunk-col"),
    ("detection_7cells", "chunk-col"), ("detection_vs_achieved_size", "chunk-col"), ("p_Q4only", "chunk-col"), ("FPR_H0_pQ4only", "chunk-col"),
    ("runtime_OC", "chunk-col"), ("max_over_21", "chunk-col"), ("power_bar", "chunk-col"), ("stress_paired", "chunk-col"),
    ("stress_KS", "chunk-col"), ("c2c5_prediction", "chunk-col"), ("comparators", "chunk-col"), ("v1_table", "path-meta"),
    ("per_fold_obs", "chunk-col"), ("per_fold_null", "declared-drop"), ("d_ACF_post_freeze", "post-freeze-real"),
    ("min_p", "definitional"), ("sd_ratio_bootstrap", "chunk-col"), ("p_eo", "chunk-col"), ("sigma_stats", "chunk-col"),
    ("influence", "chunk-col"), ("main_estimate", "main-only"), ("epoch_table", "path-meta"),
    ("tie_loss", "chunk-col"), ("ks_p_gt", "chunk-col"), ("atom_support", "chunk-col")]
SOURCES = {"chunk-col", "path-meta", "definitional", "post-freeze-real", "main-only", "declared-drop"}
REGISTRY_COLS = {"alpha_dec": ["p"], "eligibility_ks": ["p", "rg12_collapse"], "branch_R6": ["p"], "FPR_at_alpha_pooled": ["p"], "FPR_cal": ["p"], "FPR_val": ["p"],
                 "rejection_at_redundant": ["p"], "detection_7cells": ["p"], "detection_vs_achieved_size": ["p"], "p_Q4only": ["p_Q4only"],
                 "FPR_H0_pQ4only": ["p_Q4only"], "runtime_OC": ["p"], "max_over_21": ["p"], "power_bar": ["p"], "stress_paired": ["p"], "stress_KS": ["p"],
                 "c2c5_prediction": ["S1_Q2", "S1_Q3", "S1_Q4"], "comparators": ["p"], "per_fold_obs": ["S1_f2016", "S1_f2017", "S1_f2018", "S1_f2019", "S1_f2020"],
                 "sd_ratio_bootstrap": ["null_sd", "sd_eo"], "p_eo": ["p_eo"], "sigma_stats": ["sigma_logsd", "sigma_max_over_med", "ramp_share"],
                 "influence": ["infl_max_obs", "infl_top5_obs", "infl_max_null_mean", "infl_max_null_q95", "infl_top5_null_mean", "infl_top5_null_q95"],
                 "tie_loss": ["p", "p_gt"], "ks_p_gt": ["p_gt"], "atom_support": ["n_distinct", "n_ties", "n_zero", "atom_max", "obs_zero"]}


def registry_check():
    allcols = set((SCHEMA_BASE + ",p_eo,sigma_logsd,sigma_max_over_med,ramp_share").split(","))
    for name, src in READOUT_REGISTRY:
        assert src in SOURCES, f"registry {name}: source {src} ∉ enum"
        if src == "chunk-col":
            for c in REGISTRY_COLS[name]:
                assert c in allcols, f"registry {name}: column {c} ไม่อยู่ใน schema"
    return True


def _wilson_upper(x, n, z=1.959964):
    p = x / n; d = 1 + z * z / n
    return (p + z * z / (2 * n) + z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d


def cert_report_v2():
    registry_check(); annual_fn_ast_check(); rg9_check(verbose=False)
    ch = read_chunks()
    assert ch, "ไม่มี chunk v2"
    # ---- cross-series pooling invariants + epoch table ----
    inv = ("PERM_ROOT", "B0", "N", "POWER_CELLS", "alpha_cap", "SPEC_SHA", "n", "NF", "Nemb", "fold_sizes", "prefix_sizes", "X_sha", "dayix_sha")
    ref = None; epochs = {}
    for key, (hf, schema, rows) in ch.items():
        vals = {f_: hf[f_] for f_ in inv if f_ != "N"}
        if ref is None: ref = vals
        assert vals == ref, f"pooling invariant ต่างกัน {key}: {vals} vs {ref}"
        assert hf["card_sha_runtime"] == SPEC_SHA, f"N11 card_sha_runtime ≠ SPEC_SHA ใน series {key}"
        epochs.setdefault(hf["closure_sha"], []).append(key)
    def P(key, col="p"):
        return np.array([float(r[col]) for r in ch[key][2]])
    def have(v, world, cell=None): return (v, world, cell) in ch
    print("=" * 100)
    print("[OPERATIVE block · §7(7) RI-2 · null ของ main ตาม §0 N5 · เกณฑ์ = §0 N2/N3/N4]")
    elig = {}
    for v in VARIANTS:
        if not (have(v, "h0cal") and have(v, "h0val")):
            print(f"  eligibility {v}: ยังไม่มี h0cal+h0val ครบ"); continue
        pc, pv = P((v, "h0cal", None)), P((v, "h0val", None))
        pooled = np.concatenate([pc, pv])
        if len(pooled) < 2 * CERT_N:
            print(f"  eligibility {v}: pooled {len(pooled)}/400 (staging · ยังไม่ตัดสิน)"); continue
        assert not np.array_equal(pc, pv), f"RG12 collision p_cal == p_val ({v})"
        ku = ks_units_int(pooled)
        assert isinstance(ku, (int, np.integer)), "RG12 ks_units ต้องเป็น int"
        ncol = int((np.concatenate([P((v, "h0cal", None), "rg12_collapse"), P((v, "h0val", None), "rg12_collapse")]) > 0).sum())   # §0 N5 v6 · นับแถว (รหัส 1-3)
        elig[v] = (ku <= KS_T_UNITS * 100 and ncol == 0, ku, pooled)
        atoms = {a: float((np.rint(pooled * 100) <= a).mean()) for a in (1, 2, 5)}
        print(f"  eligibility {v}: ks_units={ku} vs KS_T_UNITS·100={KS_T_UNITS*100} · RG12 collapse rows={ncol} → {'eligible' if elig[v][0] else 'INELIGIBLE'}{' (N5: collapse ใน H0)' if ncol else ''} · atoms P(p≤.01/.02/.05)={atoms[1]:.3f}/{atoms[2]:.3f}/{atoms[5]:.3f}")
    main_null = None; pending = False
    for v in VARIANTS:                                   # N5 ตามลำดับ c1full → c1restr → blk7 · variant ก่อนหน้าต้องมีผลครบและ ineligible ก่อนเลื่อน (F11)
        if v not in elig: pending = True; break
        if elig[v][0]: main_null = v; break
    if main_null is None:
        if pending:
            print("  null ของ main: ยังตัดสินไม่ได้ (variant ถัดไปตามลำดับ N5 ยังไม่ครบ h0cal+h0val · A-1 staging)"); return
        print("  N5(0): ทุก variant ineligible ⇒ certify FAIL-loud · ไม่คำนวณ R6 · ไม่ charge · known-result → report วิน")
        raise SystemExit(2)
    pooled = elig[main_null][2]
    q05 = float(np.quantile(pooled, 0.05, method="linear")); a_dec = min(q05, ALPHA_NOM)
    srt = np.sort(pooled)
    thr = int(np.floor(a_dec * (B0_CAL + 1))); assert isinstance(thr, int)
    print(f"  null ของ main = {main_null} (N5: {'PRIMARY eligible' if main_null == 'c1full' else 'contingency ' + main_null})")
    print(f"  α*_dec = min(q05 pooled N=400 = {q05:.4f}, {ALPHA_NOM}) = {a_dec:.4f} · order-stat bracket #12..#29 = [{srt[11]:.3f}, {srt[28]:.3f}] · rank threshold floor(α*·(B0+1)) = {thr}")
    def tie_loss(key):
        """NON-OP (v6 C′): share draw ที่ rank(p_gt) ≤ thr < rank(p_ge) = การตัดสินที่ ties พลิก · + detection ใต้ p_gt (sensitivity bound)"""
        rg = np.rint(P(key) * (B0_CAL + 1)).astype(int); rt = np.rint(P(key, "p_gt") * (B0_CAL + 1)).astype(int)
        return float(((rt <= thr) & (rg > thr)).mean()), float((rt <= thr).mean())
    det, tl = {}, {}
    for ci in range(len(POWER_CELLS)):
        if not have(main_null, "flip", ci): continue
        pf = P((main_null, "flip", ci))
        if len(pf) < CERT_N_POWER: print(f"  [staging] cell {ci}: {len(pf)}/50"); continue
        rank = np.rint(pf * (B0_CAL + 1)).astype(int)
        det[ci] = (float((rank <= thr).mean()), float((pf < a_dec).mean()), float((pf <= a_dec).mean()))
        tl[ci] = tie_loss((main_null, "flip", ci))
    if len(det) == len(POWER_CELLS):
        mx = max(d[0] for d in det.values())
        branch = "FREE-KILL (structural — budget-exempt)" if mx < a_dec else "ESTIMATION (+1 ⇒ 7/40 ที่ main)"
        print(f"  R6 (N4 verbatim · rank rule): empirical max detection ทั่ว 7 cells ของ null ของ main = {mx*100:.1f}% {'<' if mx < a_dec else '≥'} α*_dec {a_dec:.4f} → **{branch}** · charge = {'0 (exempt)' if mx < a_dec else '+1 ⇒ 7/40'}")
        if mx < a_dec:
            print(f"  scope-tag FREE-KILL (v6 C′ · ติดคู่ verdict): max tie-loss ข้าม 7 cells = {max(t[0] for t in tl.values())*100:.1f}% · max detection ใต้ p_gt = {max(t[1] for t in tl.values())*100:.1f}% (NON-OP sensitivity bound · ไม่เปลี่ยน branch)")
    else:
        print(f"  R6: H1 cells ครบ {len(det)}/7 — branch ยังตัดสินไม่ได้")
    print("=" * 100)
    NO = "[NON-OPERATIVE readout · ไม่เข้า branch/charge/α*/p/verdict]"
    if tl:
        print(f"{NO} tie-loss ต่อ cell ({main_null} · rank rule thr={thr}): " + " · ".join(f"c{ci} {t[0]*100:.0f}% (det p_gt {t[1]*100:.0f}%)" for ci, t in tl.items()))
    for v in VARIANTS:
        if v not in elig: continue
        pc, pv, pl = P((v, "h0cal", None)), P((v, "h0val", None)), elig[v][2]
        pgt = np.concatenate([P((v, "h0cal", None), "p_gt"), P((v, "h0val", None), "p_gt")])
        tlh = np.mean([tie_loss((v, w_, None))[0] for w_ in ("h0cal", "h0val")])
        ntz = np.concatenate([P((v, w_, None), "n_ties") for w_ in ("h0cal", "h0val")]); amx = np.concatenate([P((v, w_, None), "atom_max") for w_ in ("h0cal", "h0val")])
        print(f"{NO} {v}: ties/atoms (H0 400): share(n_ties>0)={(ntz>0).mean()*100:.1f}% · median atom_max={np.median(amx):.0f} · share(obs==0)={np.concatenate([P((v, w_, None), 'obs_zero') for w_ in ('h0cal','h0val')]).mean()*100:.1f}% · "
              f"tie-loss H0={tlh*100:.1f}% · KS⁺ บน p_gt ks_units={ks_units_int(pgt)} ({'>' if ks_units_int(pgt) > KS_T_UNITS*100 else '≤'} t · sensitivity bound)")
        if have(v, "stable"):
            print(f"{NO} {v}: tie-loss STABLE={tie_loss((v, 'stable', None))[0]*100:.1f}% · share(n_ties>0)={(P((v,'stable',None),'n_ties')>0).mean()*100:.1f}%")
        print(f"{NO} {v}: FPR@α* pooled(<)={(pl < a_dec).mean()*100:.1f}% (≤)={(pl <= a_dec).mean()*100:.1f}% · FPR_cal={(pc <= a_dec).mean()*100:.1f}% · FPR_val={(pv <= a_dec).mean()*100:.1f}% · "
              f"FPR(H0, p_Q4only)={(np.concatenate([P((v,'h0cal',None),'p_Q4only'), P((v,'h0val',None),'p_Q4only')]) <= a_dec).mean()*100:.1f}% · q05={float(np.quantile(pl,.05)):.4f}")
        if have(v, "stable"):
            ps = P((v, "stable", None)); x = int((ps <= a_dec).sum())
            dps = P((v, "stable", None), "p_eo") - ps
            print(f"{NO} {v}: rejection@redundant (<)={(ps < a_dec).mean()*100:.1f}% (≤)={x/len(ps)*100:.1f}% Wilson-upper={_wilson_upper(x, len(ps))*100:.1f}% · p_eo median={np.median(P((v,'stable',None),'p_eo')):.2f} · paired Δp mean={dps.mean():+.4f} share(Δp<0)={(dps<0).mean()*100:.1f}%")
        # influence-concentration · sd-ratio paired-bootstrap · per-fold obs (N8 · §7.1 decision 2 · F8 execution-review)
        h0keys = [(v, "h0cal", None), (v, "h0val", None)]
        col = lambda c: np.concatenate([P(k_, c) for k_ in h0keys])
        print(f"{NO} {v}: influence (nanmedian ข้าม 400 H0 worlds · obs==0 → nan {int(np.isnan(col('infl_max_obs')).sum())} worlds): obs max-share={np.nanmedian(col('infl_max_obs')):.3f} top5={np.nanmedian(col('infl_top5_obs')):.3f} · null max-share mean={np.nanmedian(col('infl_max_null_mean')):.3f} q95={np.nanmedian(col('infl_max_null_q95')):.3f}")
        ratio = col("null_sd") / col("sd_eo"); brng = np.random.default_rng(20260909); bs = np.array([ratio[brng.integers(0, len(ratio), len(ratio))].mean() for _ in range(2000)])
        print(f"{NO} {v}: sd-ratio null_sd/sd_eo world-level mean={ratio.mean():.4f} · paired-bootstrap 95% CI [{np.quantile(bs,.025):.4f}, {np.quantile(bs,.975):.4f}] (B=2000 seed 20260909 · descriptive)")
        print(f"{NO} {v}: per-fold obs mean (H0 pooled): " + " · ".join(f"{c}={np.mean(col(c)):+.4f}" for c in ("S1_f2016","S1_f2017","S1_f2018","S1_f2019","S1_f2020")))
        cells = {ci: P((v, "flip", ci)) for ci in range(len(POWER_CELLS)) if have(v, "flip", ci)}
        if cells:
            s = " · ".join(f"c{ci}(Q{POWER_CELLS[ci][0]+1},ρ{POWER_CELLS[ci][1]}) <{(pf<a_dec).mean()*100:.0f}% ≤{(pf<=a_dec).mean()*100:.0f}%" for ci, pf in cells.items())
            print(f"{NO} {v}: detection 7 cells: {s}")
            ach = (pl <= a_dec).mean()
            print(f"{NO} {v}: detection vs achieved size {ach*100:.1f}%: {[round((pf<=a_dec).mean()-ach,3) for pf in cells.values()]}")
            xs = max(int((pf <= a_dec).sum()) for pf in cells.values())
            print(f"{NO} {v}: power-bar (80% @ FPR≤5% · norm AD-3): cell แข็งสุด x={xs}/50 Wilson-upper={_wilson_upper(xs,50):.3f} → {'under-powered เทียบ 80%' if xs <= 34 else 'inconclusive at N=50'}")
            dps = [P((v, "flip", ci), "p_eo") - P((v, "flip", ci), "p") for ci in cells]
            if dps:
                dpa = np.concatenate(dps)
                print(f"{NO} {v}: paired Δp = p_eo − p_rot ต่อ draw (flip 7 cells · N8): mean={dpa.mean():+.4f} · share(Δp<0)={(dpa<0).mean()*100:.1f}% · share(Δp>0)={(dpa>0).mean()*100:.1f}%")
            for ci in (2, 5):
                if ci in cells:
                    sm = [np.mean(P((v, 'flip', ci), c)) for c in ("S1_Q2", "S1_Q3", "S1_Q4")]
                    print(f"{NO} {v}: c{ci} per-segment prediction E[S1_Q2,Q3,Q4]={[round(x,4) for x in sm]} · คาด Q4<0 ∧ Q2,Q3≥0 → {'ตรง' if sm[2] < 0 and sm[0] >= 0 and sm[1] >= 0 else 'ไม่ตรง (flag)'}")
    if all(have(v, "flip", ci) for v in VARIANTS for ci in range(len(POWER_CELLS))):
        m21 = max((P((v, "flip", ci)) <= a_dec).mean() for v in VARIANTS for ci in range(len(POWER_CELLS)))
        print(f"{NO} max-over-21 (≤) = {m21*100:.1f}% (descriptive เท่านั้น · ไม่ใช่ branch)")
    r = float((elig[main_null][2] <= a_dec).mean())
    xmax = int(np.floor(a_dec * CERT_N_POWER - 1e-9))
    from math import comb
    binom_le = lambda rate: sum(comb(CERT_N_POWER, x) * rate ** x * (1 - rate) ** (CERT_N_POWER - x) for x in range(xmax + 1))
    if len(det) == len(POWER_CELLS):
        oc = float(np.prod([binom_le(det[ci][2]) for ci in range(len(POWER_CELLS))]))
        print(f"{NO} run-time OC (N12 · per-cell rate ที่วัดได้ = detection(≤) ต่อ cell {[round(det[ci][2],3) for ci in range(7)]}): P(free-KILL | rates เหล่านี้) = {oc*100:.2f}% (x≤{xmax} ทุก cell) · authoritative = run-time")
    print(f"{NO} OC reference homogeneous @achieved size {r*100:.1f}% (= ปลายล่าง bracket N12 · ไม่ใช่ per-cell): {binom_le(r)**7*100:.2f}%")
    if have(main_null, "h0stress"):
        pst = P((main_null, "h0stress", None)); pl = elig[main_null][2]
        dlt = (pst <= a_dec).mean() - (pl <= a_dec).mean()
        lab = "consistent" if abs(dlt) < 0.03 else ("inconclusive" if abs(dlt) <= 0.037 else "significant")
        ku_s = ks_units_int(pst)
        try:
            from scipy.stats import ks_2samp
            ks2 = ks_2samp(pst, pl).pvalue
        except Exception:
            ks2 = float("nan")
        sig = [np.median(P((main_null, "h0stress", None), c)) for c in ("sigma_logsd", "sigma_max_over_med", "ramp_share")]
        print(f"{NO} stress paired: FPR_stress − FPR@α*(pooled 400) = {dlt*100:+.2f}pp → {lab} (±3.70pp) · KS⁺ p_stress ks_units={ku_s} ({'>' if ku_s > KS_T_UNITS*100 else '≤'} t) · two-sample KS p={ks2:.3f} · σ median: sd(log σ)={sig[0]:.3f} max/med={sig[1]:.1f} ramp_share={sig[2]:.3f}")
    print(f"{NO} epoch table (closure_sha → series): " + " · ".join(f"{k[:10]}…: {len(v)} series" for k, v in epochs.items()))
    if os.path.exists(os.path.join(CERT_DIR, "stable.csv")):
        print(f"{NO} คู่เทียบ v1 (§7.1 · known-defect): "); cert_report_v1()
    print(f"{NO} scope-tag template (script เติมค่า): null={main_null} · α*_dec={a_dec:.4f} · KS ks_units={elig[main_null][1]} · FPR@α*={r*100:.1f}% · max det={max((d[0] for d in det.values()), default=float('nan'))*100:.1f}% · stress Δ={'n/a' if not have(main_null,'h0stress') else f'{dlt*100:+.2f}pp'} · max tie-loss(7 cells)={max((t[0] for t in tl.values()), default=float('nan'))*100:.1f}%")


# ============================ v1 oracle (read-only · RG7 guard) ============================
def cert_stable_chunk(*a, **k):
    """v1 writer ถอดออก — `Scripts/ad4_cert_out/` = oracle read-only (RG7 · E-4) · identifier คงไว้ให้ card §4 อ้างถึงได้"""
    raise RuntimeError("RG7 guard: ห้ามเขียน ad4_cert_out/ (oracle v1 read-only) — ใช้ cert_v2")


def cert_power_cell(*a, **k):
    raise RuntimeError("RG7 guard: ห้ามเขียน ad4_cert_out/ (oracle v1 read-only) — ใช้ cert_v2")


def cert_report_v1():
    rows = [l.strip().split(",") for l in io.open(os.path.join(CERT_DIR, "stable.csv"), encoding="utf-8")]
    ks = {int(r[0]): (float(r[1]), float(r[2])) for r in rows}
    ps = np.array([ks[k][0] for k in sorted(ks)])[:CERT_N]
    q05 = float(np.quantile(ps, 0.05)); a_dec = min(q05, ALPHA_NOM)
    print(f"  [v1 STABLE] N={len(ps)} · q05={q05:.3f} → α*_dec={a_dec:.3f} · rejection@dec ≤:{(ps <= a_dec).mean()*100:.1f}%")
    for ci, (pos_q, rho) in enumerate(POWER_CELLS):
        path = os.path.join(CERT_DIR, f"power_{ci}.csv")
        if not os.path.exists(path): continue
        pv = np.array([float(l.split(",")[1]) for l in io.open(path, encoding="utf-8")])[:CERT_N_POWER]
        print(f"  [v1 cell {ci}] det(<)={(pv < a_dec).mean()*100:.1f}% (≤)={(pv <= a_dec).mean()*100:.1f}%")


# ============================ mode_regress RG1-RG15 ============================
def mode_regress(ad, skip_rg14=False, only_rg14=False):
    """RG1-RG15 (§4-v4 SSOT) · synthetic เท่านั้น · ไม่มี real cache (F11)"""
    assert not hasattr(ad, "PAY_EXP_LIN"), "F11: real cache ห้ามถูกสร้างก่อน freeze"
    cs_start = closure_sha()                                             # F1: receipt ผูก closure ตอนเริ่ม
    def _rg14(ad_):
        # v6 (card §4 RG14 · 2026-09-24): comparator = v5-local จริง = หมุน 4-tuple เฉพาะ prefix ของ fold i (fold อื่น s=0) · ประเมินเฉพาะ fold i
        # annual arm = refit_annual ซึ่ง ≡ cache ใต้การหมุนแบบนี้ (base ของ fold i ไม่มีแถวหมุน) — pin เป็น regression ด้วย identity() ด้านล่าง
        # ~~v5 09-09: pair = global rotation + annual_fn=cache~~ = stale-cache path (RG13 class) ไม่ใช่ v5-local (spec defect F1/F2)
        nf = len(ad_.folds)
        def local_perms(perms, i):
            return [perms[j] if j == i else 0 for j in range(nf)]
        def local_S1(w, perms, fn=refit_annual):
            la = []
            for i in range(nf):
                d = ad_.s1_quart(w, local_perms(perms, i), annual_fn=fn, detail=True, folds=(i,))
                la += d["la"]
            return float(np.concatenate(la).mean())                 # pin expression เดียวกัน · ลำดับ (fold, s)
        def pair(w, perms):
            return ad_.s1_quart(w, perms, annual_fn=refit_annual), local_S1(w, perms)
        def identity(w, pv):
            cache_annual = lambda w_, i, rl_, rs_: (w_.DIR_EXP_LIN[i], w_.W_EXP_LIN[i])   # v5-local cache callable = closure (มีตัวตนเฉพาะที่นี่)
            for perms in pv[:3]:
                for i, (Y, tr, te) in enumerate(ad_.folds):
                    rl_, rs_, pL_, pS_ = ad_.apply_perms(w, local_perms(perms, i))
                    _, q_, pre = ad_.fold_seg(te); order = ad_.perm_order(perms[i], len(pre))
                    for a_, b_ in ((rl_, w.rl), (rs_, w.rs), (pL_, w.pL), (pS_, w.pS)):   # F4: ครบ 4-tuple
                        assert np.array_equal(a_[tr], b_[tr]), f"v5-local: base ของ fold {Y} มีแถวหมุน"
                        assert np.array_equal(a_[pre], b_[pre[order]]), f"v5-local: prefix ของ fold {Y} ไม่ถูกหมุนตาม π"   # F3: หมุนจริง
                assert local_S1(w, perms) == local_S1(w, perms, fn=cache_annual), "v5-local: refit ≢ cache (identity F2 ล้ม)"
                # F3 positive control: fold 2016 local ≡ Alt-2 (base ไม่มีแถวหมุนทั้งคู่) · ∃ fold ≥2017 ต่างกัน (Alt-2 base มี prefix หมุนของปีก่อน)
                dg = ad_.s1_quart(w, perms, detail=True)
                g_by = {i: np.concatenate([a for a, f in zip(dg["la"], dg["fold"]) if f == i]) for i in range(nf)}
                l_by = {i: np.concatenate(ad_.s1_quart(w, local_perms(perms, i), detail=True, folds=(i,))["la"]) for i in range(nf)}
                assert np.array_equal(g_by[0], l_by[0]), "positive control: fold 2016 local ≠ Alt-2"
                assert any(not np.array_equal(g_by[i], l_by[i]) for i in range(1, nf)), "positive control: ทุก fold ≥2017 local ≡ Alt-2 (แขนไม่ต่างกัน)"
            return True
        _rg14_body(ad_, pair, identity)
    annual_fn_ast_check(); ast_guard_selftest(); print("[AST] annual_fn call-site ≠ refit_annual = mode_regress เท่านั้น · positional ≤2 · ไม่มี */**args · def refit_annual 1 แห่ง · ไม่มี rebind/alias · self-test 7 mutation caught ✓")
    rg9_check()
    if only_rg14:
        _rg14(ad); return
    w = as_ad4(synth_stable_world(ad, _rng("ad4_reg", PERM_ROOT))); w.build_exp_caches()
    # RG2 trm(Q1) == tr(fold)
    for i, (Y, tr, te) in enumerate(ad.folds):
        te_idx, q, _ = ad.fold_seg(te)
        trm = ad.dayix < ad.dayix[te_idx[0]] - ad.Nemb
        assert np.array_equal(trm, tr), f"RG2 fold {Y}"
    print("[RG2] trm(Q1) ≡ tr(fold) 5/5 ✓")
    # RG1 segs=(0,) production path → payQ(s=0) == PAY_EXP_LIN[i][:q]
    d0 = ad.s1_quart(w, None, segs=(0,), detail=True)
    for i, (Y, tr, te) in enumerate(w.folds):
        te_idx, q, _ = ad.fold_seg(te)
        la_i = [a for a, f in zip(d0["la"], d0["fold"]) if f == i][0]
        assert np.array_equal(la_i, np.zeros(q)), f"RG1 fold {Y}: payQ(s=0)−payA ≠ 0"
        dpA = d0["dpA"][i][0]
        payQ0 = np.where(dpA[:q] == 1, w.pL[te_idx[:q]], w.pS[te_idx[:q]])
        assert np.array_equal(payQ0, w.PAY_EXP_LIN[i][:q]), f"RG1 fold {Y}: payQ(s=0) ≠ PAY_EXP_LIN[:q]"
    print("[RG1] segment-0 payoff identity บน production path (segs=(0,)) ทุก fold ✓")
    # RG5 identity-π ≡ obs (float equality) ทั้ง rotate_payoff=True/False
    obs_rot = ad.s1_quart(w, None, rotate_payoff=True); obs_leg = ad.s1_quart(w, None, rotate_payoff=False)
    assert obs_rot == obs_leg, "obs(s=0) ต่างกันสองแฟล็ก"
    id_shift = [0] * len(ad.folds); id_order = [np.arange(len(ad.fold_seg(te)[2])) for (_, _, te) in ad.folds]
    for perms in (id_shift, id_order):
        assert ad.s1_quart(w, perms, rotate_payoff=True) == obs_rot, "RG5 identity (rotate)"
        assert ad.s1_quart(w, perms, rotate_payoff=False) == obs_leg, "RG5 identity (legacy)"
    print(f"[RG5] identity-π ≡ obs (float equality) · rotate True/False · s=0 และ π=arange ✓ · obs={obs_rot:+.5f}")
    # RG3/RG4/RG6/RG10/RG11 บน null draw (c1full · s≠0 ทุก fold)
    rng = _rng("ad4_rg4", PERM_ROOT)
    perms = ad.label_perms(rng, "c1full")
    while any(s == 0 for s in perms): perms = ad.label_perms(rng, "c1full")
    xh = hashlib.sha256(w.X.tobytes()).hexdigest()
    rl_p, rs_p, pL_p, pS_p = ad.apply_perms(w, perms)
    for i, (Y, tr, te) in enumerate(w.folds):
        te_idx, q, prefix_idx = ad.fold_seg(te)
        order = ad.perm_order(perms[i], len(prefix_idx))
        assert sorted(order) == list(range(len(prefix_idx))), "π ไม่ใช่ bijection"
        for a, b in ((rl_p, w.rl), (rs_p, w.rs), (pL_p, w.pL), (pS_p, w.pS)):
            assert np.array_equal(a[prefix_idx], b[prefix_idx[order]]), f"RG4 4-tuple fold {Y}"
        assert np.array_equal(rs_p[prefix_idx], -rl_p[prefix_idx]), "RG4 rs == −rl (synthetic)"
    d = ad.s1_quart(w, perms, detail=True)
    for trm, sl, seg, i, s in zip(d["trm"], d["sl"], d["segrows"], d["fold"], d["seg"]):     # F12: object ที่ production ใช้จริง
        Y, tr, te = w.folds[i]; te_idx = np.where(te)[0]
        assert w.dayix[trm].max() < w.dayix[seg[0]] - w.Nemb, f"RG6 embargo fold {Y} s={s}"
        segm = np.zeros(w.n, bool); segm[seg] = True
        assert np.array_equal(te_idx[sl], seg) and np.array_equal(np.where(segm)[0], seg), "RG11 index"
    assert hashlib.sha256(w.X.tobytes()).hexdigest() == xh, "RG3 X-untouched"
    # RG10 two-arm invariant: แถวที่ dp == dpA_draw[sl] → payQ − payA == 0.0 เป๊ะ
    n10 = 0
    for i, (Y, tr, te) in enumerate(w.folds):
        te_idx, q, prefix_idx = ad.fold_seg(te); pos = {v: k for k, v in enumerate(te_idx)}
        dpA = d["dpA"][i][0]
        for s in (1, 2, 3):
            seg = te_idx[s * q:(s + 1) * q] if s < 3 else te_idx[3 * q:]
            trm = w.dayix < w.dayix[seg[0]] - w.Nemb; segm = np.zeros(w.n, bool); segm[seg] = True
            dp = fit_predict(w.X, w.keep_all, trm, segm, rl_p[trm], rs_p[trm], w.dd)
            sl = [pos[r] for r in seg]; la_i = [a for a, f, sg in zip(d["la"], d["fold"], d["seg"]) if f == i and sg == s][0]
            same = dp == dpA[sl]
            assert np.all(la_i[same] == 0.0), f"RG10 fold {Y} s={s}: arm อ่าน array คนละชุด"
            n10 += int(same.sum())
    print(f"[RG3] X-untouched ✓ · [RG4] 4-tuple π เดียวกัน + rs=−rl ✓ · [RG6] embargo ✓ · [RG10] two-arm invariant ({n10} แถว dp==dpA → Δ=0.0) ✓ · [RG11] index ✓")
    # RG13 cache/refit coherence
    w13 = as_ad4(synth_stable_world(ad, _rng("ad4_rg13", PERM_ROOT))); w13.build_exp_caches()
    for i in range(len(w13.folds)):
        dpA, wv = refit_annual(w13, i, w13.rl, w13.rs)
        assert np.array_equal(dpA, w13.DIR_EXP_LIN[i]) and np.array_equal(wv, w13.W_EXP_LIN[i]), f"RG13(ก) fold {i}"
    rl13, rs13, _, _ = ad.apply_perms(w13, perms)
    ok16 = np.array_equal(refit_annual(w13, 0, rl13, rs13)[1], w13.W_EXP_LIN[0])
    okrest = all(not np.array_equal(refit_annual(w13, i, rl13, rs13)[1], w13.W_EXP_LIN[i]) for i in range(1, len(w13.folds)))
    assert ok16 and okrest, f"RG13(ข) conjunction เท็จ: fold2016==cache {ok16} · ∀ fold≥2017 ≠ cache {okrest}"
    print("[RG13] (ก) s=0: refit ≡ cache (dpA + w_vec) ทุก fold ✓ · (ข) s≠0: fold 2016 w_vec == cache ∧ ∀ fold ≥2017 w_vec ≠ cache ✓")
    # RG15 inertness ของ tp1_card.fit_predict(return_w)
    w15 = as_ad4(synth_stable_world(ad, _rng("ad4_rg15", PERM_ROOT)))
    Y, tr, te = w15.folds[0]
    dp_def = fit_predict(w15.X, w15.keep_all, tr, te, w15.rl[tr], w15.rs[tr], w15.dd)
    dp_w, _ = fit_predict(w15.X, w15.keep_all, tr, te, w15.rl[tr], w15.rs[tr], w15.dd, return_w=True)
    assert np.array_equal(dp_def, dp_w), "RG15 return_w ไม่ inert"
    sha = hashlib.sha256(dp_def.astype(np.int64).tobytes()).hexdigest()
    assert sha == RG15_BASELINE_SHA, f"RG15 baseline sha เปลี่ยน: {sha[:16]} ≠ {RG15_BASELINE_SHA[:16]}"
    z = np.zeros(w15.NF, bool)
    assert np.array_equal(fit_predict(w15.X, z, tr, te, w15.rl[tr], w15.rs[tr], w15.dd), w15.dd[te]), "RG15 keep=zeros default ≠ dd[te]"
    try:
        fit_predict(w15.X, z, tr, te, w15.rl[tr], w15.rs[tr], w15.dd, return_w=True); raise AssertionError("RG15: keep=zeros + return_w ต้อง raise")
    except ValueError:
        pass
    print(f"[RG15] fit_predict default ≡ return_w[0] · sha256 == baseline {sha[:12]}… · keep=zeros → dd[te] · return_w+zeros → raise ✓")
    # RG12 integer-lattice + boundary
    pgrid = np.arange(1, 101) / 100
    ku = ks_units_int(np.tile(pgrid, 4)); assert isinstance(ku, int) and ku == 0
    boundary = np.concatenate([np.full(KS_T_UNITS, 0.01), pgrid.repeat(4)[:400 - KS_T_UNITS]])   # C_1 = 23+4 → units = (27·100 − 1·400) = 2300 = t·100 พอดี
    ku_b = ks_units_int(boundary)
    assert ku_b == KS_T_UNITS * 100 and not (ku_b > KS_T_UNITS * 100), f"RG12 boundary: ks_units={ku_b} ต้อง == {KS_T_UNITS*100} และจัด eligible"
    print(f"[RG12] ks_units int ✓ · boundary ks_units == KS_T_UNITS·100 = {ku_b} → eligible (> strict) ✓")
    # RG12 v6 (C′ · F8 positive control): rule-level · natural ties บน STABLE ต้องไม่ raise · collapse ที่สร้างเองต้อง raise (stable) / flag (h0)
    # E10: rule-level ที่ B0 production (99) + 19 · ตัวอย่างค้าน F1 (ค่าคงที่ ≠ obs ที่ float sd ≠ 0)
    for B_, c_, o_ in ((B0_CAL, 0.3, 0.1), (B0_CAL, 0.1, 0.2), (19, 0.1, 0.2), (9, 0.3, 0.1)):
        assert AD4.rg12_code(np.full(B_, c_), o_, False) == 3, f"RG12 rule: const {c_} ≠ obs {o_} (B={B_}) ต้อง = รหัส 3"
    assert AD4.rg12_code(np.full(B0_CAL, 0.1), 0.1, False) == 2 and AD4.rg12_code(np.full(B0_CAL, 0.0), 0.0, True) == 1, "RG12 rule: all==obs → รหัส 2 (la≢0) / 1 (la≡0)"
    assert AD4.rg12_code(np.full(B0_CAL, 0.0), 0.0, False) == 2, "RG12 rule: obs=0 จากการหักล้าง (la≢0) ต้อง = รหัส 2 ไม่ใช่ 1 (E8)"
    assert AD4.rg12_code(np.array([0.0] * 50 + list(np.linspace(-0.2, 0.3, 49))), 0.0, True) == 0, "RG12 rule: atoms + ties ธรรมชาติ ≠ collapse"
    wpc = as_ad4(synth_stable_world(ad, _rng("engrg12_stable_2", PERM_ROOT))); wpc.build_exp_caches()   # world จาก Engineer probe 09-24 (n_ties 24/99 · obs=0 · p_ge .62 p_gt .38)
    rpc = ad.p_one(wpc, "engrg12_stable_2_p", B0=B0_CAL, variant="c1full", world="stable")
    assert rpc["rg12_collapse"] == 0 and rpc["n_ties"] == 24 and rpc["obs_zero"] == 1, f"RG12 F8: natural-ties world ต่างจาก probe (n_ties={rpc['n_ties']} obs_zero={rpc['obs_zero']})"
    assert f"{rpc['p']:.2f}" == "0.62" and f"{rpc['p_gt']:.2f}" == "0.38", f"RG12 F8: p_ge/p_gt {rpc['p']:.2f}/{rpc['p_gt']:.2f} ≠ probe .62/.38"
    # F8(ค) + E14: collapse ที่สร้างผ่าน production p_one ทั้ง 3 รหัส × 3 เส้นทาง (stable raise · h0cal flag · main flag + p_ge ตามที่คำนวณ)
    wh_c = as_ad4(synth_h0_world(ad, _rng("ad4_h0c_reg", PERM_ROOT))); wh_c.build_exp_caches()
    obs_c = ad.s1_quart(wh_c, None)
    frng = _rng("ad4_rg12_fix", PERM_ROOT); fix_hi = fix_lo = None
    while fix_hi is None or fix_lo is None:                               # s-vector ตายตัว 2 ชุดคร่อม obs (E14-ii)
        pv_ = ad.label_perms(frng, "c1full"); s_ = ad.s1_quart(wh_c, pv_)
        if s_ > obs_c and fix_hi is None: fix_hi = (pv_, s_)
        if s_ < obs_c and fix_lo is None: fix_lo = (pv_, s_)
    assert fix_hi[1] != obs_c and fix_lo[1] != obs_c, "F8: S1(fixed) ต้อง ≠ obs (E14-i)"
    orig_s1 = ad.s1_quart
    cases = [(wpc, "engrg12_stable_2_p", None, 1, 1.0), (wh_c, "ad4_reg_pone", None, 2, 1.0),
             (wh_c, "ad4_reg_pone", fix_hi[0], 3, 1.0), (wh_c, "ad4_reg_pone", fix_lo[0], 3, 1 / 20)]
    try:
        for w_c, tag_c, fix_, code_x, p_x in cases:
            # fix_=None → ทุก null draw = obs (รหัส 1/2) · fix_=vector → ทุก null draw = S1(fixed) ≠ obs (รหัส 3)
            ad.s1_quart = (lambda w_, perms=None, detail=False, f_=fix_: orig_s1(w_, None if (perms is None or f_ is None) else f_, detail=detail))
            try:
                ad.p_one(w_c, tag_c, B0=19, variant="c1full", world="stable")
                raise AssertionError(f"RG12 F8: รหัส {code_x} บน stable ต้อง raise RG12Collapse")
            except RG12Collapse:
                pass
            for wd_ in ("h0cal", "main"):
                r_ = ad.p_one(w_c, tag_c, B0=19, variant="c1full", world=wd_)
                assert r_["rg12_collapse"] == code_x and abs(r_["p"] - p_x) < 1e-12, f"RG12 F8: {wd_} ได้รหัส {r_['rg12_collapse']} p={r_['p']} ≠ คาด {code_x}/{p_x}"
    finally:
        del ad.s1_quart
    print(f"[RG12] v6 C′: natural ties (engrg12_stable_2 · n_ties={rpc['n_ties']} atom_max={rpc['atom_max']} p_ge={rpc['p']:.2f} p_gt={rpc['p_gt']:.2f}) ไม่ raise ✓ · "
          f"rule B0=99/19/9 ✓ · collapse ที่สร้าง รหัส 1 (obs≡0) / 2 (obs={obs_c:+.4f}) / 3 hi ({fix_hi[1]:+.4f} → p=1) / 3 lo ({fix_lo[1]:+.4f} → p=.05): stable → raise · h0cal/main → flag + p_ge ✓")
    # RG7 v1 oracle (in-memory · legacy path · 6 ทศนิยม)
    t0 = time.time()
    pins = [("stable", 0, "0.190000", "-0.000147"), ("stable", 1, "0.040000", "0.020019"), ("flip0", 0, "0.520000", None)]
    for kind, k, p_pin, nm_pin in pins:
        if kind == "stable":
            wo = as_ad4(synth_stable_world(ad, _rng(f"ad4_cert_s_{k}", PERM_ROOT))); wo.build_exp_caches()
            obs, p, nm, q95 = ad.p_one_legacy(wo, f"ad4_certp_{k}")
        else:
            wo = as_ad4(intra_flip_world(ad, _rng(f"ad4_pw_0_{k}", PERM_ROOT), pos_q=1, rho=0.10)); wo.build_exp_caches()
            obs, p, nm, q95 = ad.p_one_legacy(wo, f"ad4_pwp_0_{k}")
        assert f"{p:.6f}" == p_pin, f"RG7 {kind} k={k}: p {p:.6f} ≠ {p_pin}"
        if nm_pin: assert f"{nm:.6f}" == nm_pin, f"RG7 {kind} k={k}: nm {nm:.6f} ≠ {nm_pin}"
        print(f"[RG7] oracle {kind} k={k}: p={p:.6f} nm={nm:.6f} ✓ ({time.time()-t0:.0f}s)")
    # H0-C / stress world smoke (โครงสร้าง) + RG12 degeneracy exercise ผ่าน p_one B0=19
    wh = as_ad4(synth_h0_world(ad, _rng("ad4_h0c_reg", PERM_ROOT))); wh.build_exp_caches()
    pref = _prefix_mask(ad)
    ws = as_ad4(synth_h0_stress_world(ad, _rng("ad4_stress_reg", PERM_ROOT)))
    print(f"[worlds] H0-C prefix rows={int(pref.sum())} (labels noise) · stress σ: sd(log σ)={ws.sigma_stats[0]:.3f} max/med={ws.sigma_stats[1]:.1f} ramp_share={ws.sigma_stats[2]:.3f}")
    r = ad.p_one(wh, "ad4_reg_pone", B0=19, variant="c1full", world="h0cal")
    print(f"[smoke] p_one(H0-C · B0=19) obs={r['obs']:+.4f} p={r['p']:.2f} null_mean={r['null_mean']:+.4f} n_distinct={r['n_distinct']} · schema keys={len(r)}")
    assert set(SCHEMA_BASE.split(",")[2:]) <= set(r), "schema base ไม่ครบ"
    if skip_rg14:
        print("[RG14] SKIPPED (--skip-rg14) — regress ยังไม่ครบ RG1-RG15 · ต้องรัน `rg14` แยก")
    else:
        _rg14(ad)
    print("[regress] RG1-RG13 · RG15 PASS" + (" · RG14 SKIPPED" if skip_rg14 else " · RG14 PASS"))
    write_receipt("regress", cs_start)


def _rg14_body(ad, pair_fn, identity=None):
    """RG14 v5-local paired prediction (§4): W=50 worlds RG14_TAGS · s-vector เดียวกันต่อ world · B0=99 · Δsd = sd(Alt-2)−sd(v5-local) · Δq95
    raise ⟺ upper 95% t-CI (df=W−1) ของ paired mean ทั้ง Δsd และ Δq95 < 0 (BOTH) · point flip = report
    (เรียกได้จาก mode_regress เท่านั้น — closure v5-local อยู่ใน mode_regress · ฟังก์ชันนี้รับ callable ผ่าน argument)"""
    from scipy.stats import t as tdist
    W = len(RG14_TAGS); dsd, dq = [], []; t0 = time.time()
    # checkpoint ต่อ world (option A 2026-09-09 · หลัง background job ถูก kill ที่ 27/50 เพราะ memory ระบบ): ค่า deterministic ต่อ tag → resume ได้ · เขียนทั้งไฟล์ผ่าน .tmp → os.replace
    ck_dir = os.path.join(CERT_DIR_V2, "rg14"); os.makedirs(ck_dir, exist_ok=True)
    ck_path = os.path.join(ck_dir, "checkpoint_v6.json")                 # v6 · ไฟล์ 09-09 (gate ผิด) = checkpoint_stalecache_0909.json (known-result)
    ck = json.load(io.open(ck_path, encoding="utf-8")) if os.path.exists(ck_path) else {}
    cs_now = closure_sha(); tagset = set(RG14_TAGS)
    for t_, e_ in ck.items():                                             # F7: resume ต้อง code เดิม + tag อยู่ในชุดที่ pin
        if t_ not in tagset or e_.get("closure_sha") != cs_now:
            raise RuntimeError(f"RG14 checkpoint {t_}: closure/tag ไม่ตรง (entry {str(e_.get('closure_sha'))[:12]} vs now {cs_now[:12]}) — ลบ checkpoint_v6.json แล้วรันใหม่")
    idchecked = False
    for wi, tag in enumerate(RG14_TAGS):
        if tag in ck:
            dsd.append(ck[tag]["dsd"]); dq.append(ck[tag]["dq95"])
            print(f"  [RG14] world {wi+1}/{W} Δsd={dsd[-1]:+.5f} Δq95={dq[-1]:+.5f} (checkpoint)", flush=True); continue
        w = as_ad4(synth_stable_world(ad, _rng(tag, PERM_ROOT), rho=0.10, nsig=4)); w.build_exp_caches()
        rng = _rng(f"{tag}_p", PERM_ROOT)
        pv = [ad.label_perms(rng, "c1full") for _ in range(B0_CAL)]
        if identity is not None and not idchecked:
            identity(w, pv); idchecked = True
            print("  [RG14] identity: v5-local base untouched ทุก fold · local-refit ≡ local-cache (3 draws) ✓", flush=True)
        pairs = [pair_fn(w, p) for p in pv]                       # pair จาก mode_regress → (S1 Alt-2, S1 v5-local)
        n_refit = np.array([a for a, _ in pairs]); n_local = np.array([b for _, b in pairs])
        for nm_, arr_ in (("Alt-2", n_refit), ("v5-local", n_local)):   # v6 C′: non-degeneracy = n_distinct ≥ 2 (exact · ไม่ใช้ float sd) · atoms ธรรมชาติ ≠ degenerate · emit · ไม่ข้าม world
            if len(np.unique(arr_)) < 2:
                raise AssertionError(f"RG14 {tag}: แขน {nm_} collapse (n_distinct=1) — FAIL-loud")
        atom = lambda a_: int(np.unique(a_, return_counts=True)[1].max())
        dsd.append(float(n_refit.std(ddof=1) - n_local.std(ddof=1)))
        dq.append(float(np.quantile(n_refit, .95, method="linear") - np.quantile(n_local, .95, method="linear")))
        ck[tag] = {"dsd": dsd[-1], "dq95": dq[-1], "sd_alt2": float(n_refit.std(ddof=1)), "sd_v5local": float(n_local.std(ddof=1)),
                   "q95_alt2": float(np.quantile(n_refit, .95, method="linear")), "q95_v5local": float(np.quantile(n_local, .95, method="linear")),
                   "nd_alt2": int(len(np.unique(n_refit))), "nd_v5local": int(len(np.unique(n_local))), "atom_alt2": atom(n_refit), "atom_v5local": atom(n_local), "closure_sha": cs_now}
        tmp = ck_path + ".tmp"
        with io.open(tmp, "w", encoding="utf-8", newline="\n") as f: json.dump(ck, f, ensure_ascii=False, indent=1)
        os.replace(tmp, ck_path)
        print(f"  [RG14] world {wi+1}/{W} Δsd={dsd[-1]:+.5f} Δq95={dq[-1]:+.5f} · distinct {ck[tag]['nd_alt2']}/{ck[tag]['nd_v5local']} atom {ck[tag]['atom_alt2']}/{ck[tag]['atom_v5local']} · {time.time()-t0:.0f}s (checkpoint {len(ck)}/{W})", flush=True)
    tc = tdist.ppf(0.975, W - 1); res = {}
    for name, arr in (("Δsd", np.array(dsd)), ("Δq95", np.array(dq))):
        m, se = arr.mean(), arr.std(ddof=1) / np.sqrt(W)
        res[name] = (m, se, tc * se, m + tc * se)
        print(f"[RG14] {name}: mean={m:+.6f} SE={se:.6f} CI±={tc*se:.6f} upper={m+tc*se:+.6f} · |mean|/SE={abs(m)/se:.2f}{' ⇒ inconclusive (report เท่านั้น)' if abs(m)/se < 2 else ''}")
    both = all(v[3] < 0 for v in res.values())
    if both:
        raise AssertionError("RG14 raise: upper t-CI ของ paired mean < 0 ทั้ง Δsd และ Δq95 (BOTH · หลักฐานค้านกลไก)")
    print("[RG14] PASS (ไม่ raise) · point flip = report เท่านั้น")
    write_receipt("rg14", cs_now)


# ============================ regress receipt (F8 · v6) ============================
RECEIPT = os.path.join(CERT_DIR_V2, "regress_receipt.json")


def write_receipt(part, cs_start):
    """part ∈ {regress, rg14} · ผูก closure_sha ที่จับตอนเริ่มรัน + SPEC_SHA (F1 v6 review) · closure เปลี่ยนระหว่างรัน = ไม่ออก receipt"""
    os.makedirs(CERT_DIR_V2, exist_ok=True)
    cs = closure_sha()
    assert cs == cs_start, f"closure เปลี่ยนระหว่างรัน ({cs_start[:12]} → {cs[:12]}) — receipt ไม่ออก · รันใหม่"
    r = json.load(io.open(RECEIPT, encoding="utf-8")) if os.path.exists(RECEIPT) else {}
    if r.get("closure_sha") != cs or r.get("SPEC_SHA") != SPEC_SHA:
        r = {"closure_sha": cs, "SPEC_SHA": SPEC_SHA, "regress": False, "rg14": False}
    r[part] = True; r[part + "_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = RECEIPT + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline="\n") as f: json.dump(r, f, ensure_ascii=False, indent=1)
    os.replace(tmp, RECEIPT)
    print(f"[receipt] {part} ✓ · closure {cs[:12]}… · SPEC_SHA {SPEC_SHA[:12]}… · regress={r['regress']} rg14={r['rg14']}")


def require_receipt():
    """cert_chunk/pilot ต้องเห็น regress RG1-RG15 PASS บน closure + SPEC_SHA เดียวกัน (card :14 N7 gates ก่อนรัน · F8)"""
    assert os.path.exists(RECEIPT), "ไม่มี regress receipt — รัน `regress --skip-rg14` และ `rg14` ให้ PASS ก่อน"
    r = json.load(io.open(RECEIPT, encoding="utf-8"))
    assert r.get("closure_sha") == closure_sha() and r.get("SPEC_SHA") == SPEC_SHA, "regress receipt ไม่ตรง code/spec ปัจจุบัน — รัน regress ใหม่"
    assert r.get("regress") and r.get("rg14"), f"regress ยังไม่ครบ: regress={r.get('regress')} rg14={r.get('rg14')}"


# ============================ pilot (§7(9)) ============================
def pilot(ad, k0, k1):
    """plumbing/timing เท่านั้น · persist chunk h0pilot (excluded จากทุกสถิติ · ห้ามลบ) · ไม่ print q05"""
    cert_chunk(ad, "c1full", "h0pilot", None, k0, k1)


def mode_main(ad):
    if not FROZEN_CERT:
        raise SystemExit("⛔ freeze gate: ต้อง certify → pin FROZEN_CERT + วินสั่ง commit ก่อนรัน main")
    annual_fn_ast_check(); rg9_check(verbose=False)
    raise SystemExit("main: implement ขั้น 4a หลัง certify v2 (pattern AD-2 — estimation-primary + branch assert)")


# ---- pin block (commit spec 8271163 → v6 re-entry 09-24: SPEC_SHA reseal ด้วย pin_ad4.py --seal · trail = Progress Log · card §7(11)(12)(12b) · §0 N2 · N11 freeze · วินสั่ง apply 2026-09-09) ----
SPEC_SHA    = "98f2e73b2202f77d29c102e27103afa57cca9ff39fd837fb11ce0ebddaf82bbb"              # sha256(LF-normalized card ณ commit spec) · seal/check = Scripts/pin_ad4.py (--seal/--check) · verify = card_scan.py --require-pin · ห้ามเขียนกลับลง card
KS_T_UNITS  = 23                     # eng16_ks.py part A · N=400 · B=200,000 · seed 20260903 · integer-lattice (t = 23/400)
KS_ACHIEVED = 0.0475                 # achieved false-flag @t · integer convention · atom ที่ t = 1.26%
RG14_TAGS   = tuple(f"ad4_rg14_w{k}" for k in range(50, 100))   # §7(12b) W=50 · v6: w50..w99 (w0..w49 ใช้กับ gate v5 แล้ว · w0..w10 เห็น contrast ที่ถูกแล้ว) · world = synth_stable_world(ad, _rng(tag, PERM_ROOT), rho=.10, nsig=4)

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    mode = sys.argv[1] if len(sys.argv) > 1 else "regress"
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    if mode == "cert_report_v2":
        cert_report_v2(); sys.exit(0)
    if mode == "cert_report":
        cert_report_v1(); sys.exit(0)
    ad = AD4.__new__(AD4)
    AD1.__init__(ad)
    print(f"[AD4] v2 · SPEC_SHA {SPEC_SHA[:12]}… · card_sha_runtime {card_sha_runtime()[:12]}… · closure {closure_sha()[:12]}… · threads={os.environ.get('OPENBLAS_NUM_THREADS','?')} · quarterly-on-real ⛔ (synthetic เท่านั้น)")
    if mode == "regress":
        mode_regress(ad, skip_rg14="--skip-rg14" in sys.argv)
    elif mode == "rg14":
        mode_regress(ad, only_rg14=True)
    elif mode == "cert_v2":
        if len(args) == 5: variant, world, cell, k0, k1 = args[0], args[1], int(args[2]), int(args[3]), int(args[4])
        else: variant, world, cell, k0, k1 = args[0], args[1], None, int(args[2]), int(args[3])
        cert_chunk(ad, variant, world, cell, k0, k1)
    elif mode == "pilot":
        pilot(ad, int(args[0]), int(args[1]))
    elif mode == "main":
        mode_main(ad)
    else:
        raise SystemExit(f"unknown mode {mode}")
