"""Card AD-4 — fine-cadence quarterly refit · design v5 + Alt-G/Alt-2 (card §0 NORMATIVE N1-N13 · SPEC_SHA ท้ายไฟล์)
Spec: Plan/TRELLIS-010_card_AD4_fine_cadence.md (commit spec = freeze N11) · claim ยังไม่จอง
null (§0 N1) = C1-full circular shift s ∈ {0..m−1} ของ payoff-tuple (rl,rs,pL,pS) บน prefix rows · global ทุก fold พร้อมกัน (Alt-G)
  · annual arm refit ทุก fold ต่อ draw (Alt-2 · ไม่มี dispatch cache/refit) · statistic S1_rot operative + S1_evalorig descriptive (§0 N8)
eligibility (§0 N2) = KS⁺ integer-lattice: ineligible ⟺ ks_units > KS_T_UNITS·100 · α*_dec (§0 N3) = min(q05 pooled N=400 ของ null ของ main, .05)
contingency (§0 N5) mechanical · rule R6 (§0 N4 verbatim ของวิน) · gates RG1-RG15 (§4-v4 = SSOT) · worlds/N (§0 N6 ห้ามลด)
⛔ certify v1 (ad4_cert_out/ · f99031e) = KNOWN-DEFECT (card §6.1 · F1 null-retention 27.8% · F2 calib-world ≠ H0 · F4 FAIL-loud ไม่ implement)
  · code ของ v1 = checkout f99031e (card §7.1 :148) · ไฟล์นี้หลัง commit spec = v1 code + pin block เท่านั้น (decision path ยังเป็น v1 จนขั้น 2 implement)
ขั้น 2 implement (ขอวินตาม CRITICAL · scope ไฟล์นี้ + tp1_card.py return_w): s1_quart(w, perms, segs, rotate_payoff, annual_fn=refit_annual)
  · mode_regress RG1-RG15 · cert_chunk newline="\n" · cert_report_v2 · governance: SEARCH 2012-2020 · lockbox/guard ไม่แตะ · quarterly บน real payoff = main เท่านั้น
modes: regress / cert_stable k0 k1 / cert_power [cell_i] / cert_report / main
"""
import sys, time, os
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")
from ad1_card import AD1, synth_stable_world
from ad2_card import AD2, as_ad2
from tp1_card import fit_predict
from direction_at_real_exit import _rng

PERM_ROOT = 20260723         # seed root ใหม่ (ประกาศ)
ALPHA_NOM = 0.05
B_LABEL = 40                 # block-size ของ label-perm = R/feature-ACF template [AD-1:76 · declared drop]
B_PERM, B_ESC = 1000, 5000
CERT_N = 200
CERT_N_POWER = 50            # [R3 ≥50]
B0_CAL = 99
# power cells [v3 §3.5]: (pos_q, rho) — pos 1=Q2start 2=Q3 3=Q4 + bracket (1, 0.20)
POWER_CELLS = ((1, 0.10), (2, 0.10), (3, 0.10), (1, 0.15), (2, 0.15), (3, 0.15), (1, 0.20))
CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ad4_cert_out")
FROZEN_CERT = {}             # pin หลัง certify + วินสั่ง freeze-commit — main ปฏิเสธรันจนกว่า pin


class AD4(AD2):
    # ---------- segments ----------
    def fold_seg(self, te):
        """คืน (te_idx, q, prefix_idx) — quartile = n//4 · remainder→Q4 [R4-D]"""
        te_idx = np.where(te)[0]
        q = len(te_idx) // 4
        return te_idx, q, te_idx[:3 * q]

    def s1_quart(self, w, perms=None, K_unused=None):
        """S1 = mean over Q2-Q4 rows ของ (pay_quarterly − pay_annual) · perms = π ต่อ fold (null)
        label-perm: rl_arr/rs_arr copy → prefix rows ใช้ label(π(i)) [คู่ index เดียวกัน — assert §4]"""
        la = []
        for i, (Y, tr, te) in enumerate(w.folds):
            te_idx, q, prefix_idx = self.fold_seg(te)
            rl_arr, rs_arr = w.rl, w.rs
            if perms is not None:
                order = perms[i]
                rl_arr = w.rl.copy(); rs_arr = w.rs.copy()
                rl_arr[prefix_idx] = w.rl[prefix_idx[order]]
                rs_arr[prefix_idx] = w.rs[prefix_idx[order]]
            for s in (1, 2, 3):                          # Q2..Q4 (Q1 = structural zero — excluded estimand)
                seg = te_idx[s * q: (s + 1) * q] if s < 3 else te_idx[3 * q:]
                cutoff = w.dayix[seg[0]] - w.Nemb
                trm = w.dayix < cutoff                    # expanding + prefix · embargo dayix [FB-3]
                segm = np.zeros(w.n, bool); segm[seg] = True
                dp = fit_predict(w.X, w.keep_all, trm, segm, rl_arr[trm], rs_arr[trm], w.dd)
                payQ = np.where(dp == 1, w.pL[segm], w.pS[segm])
                pos = {v: k for k, v in enumerate(te_idx)}
                sl = [pos[r] for r in seg]
                payA = w.PAY_EXP_LIN[i][sl]
                la.append(payQ - payA)
        return float(np.concatenate(la).mean())

    def label_perms(self, rng):
        """π ต่อ fold: block-permutation บน prefix positions (blocks ละ B_LABEL · remainder block ท้าย)"""
        out = []
        for (Y, tr, te) in self.folds:
            te_idx, q, prefix_idx = self.fold_seg(te)
            m = len(prefix_idx)
            nblk = m // B_LABEL + (1 if m % B_LABEL else 0)
            blocks = [np.arange(k * B_LABEL, min((k + 1) * B_LABEL, m)) for k in range(nblk)]
            out.append(np.concatenate([blocks[j] for j in rng.permutation(nblk)]))
        return out

    def p_one(self, w, tag, B0=B0_CAL):
        rng = _rng(tag, PERM_ROOT)
        obs = self.s1_quart(w)
        null = np.array([self.s1_quart(w, self.label_perms(rng)) for _ in range(B0)])
        p = (1 + int((null >= obs).sum())) / (len(null) + 1)
        return obs, p, float(null.mean()), float(np.quantile(null, 0.95))


def as_ad4(world):
    w = AD4.__new__(AD4)
    w.__dict__.update(world.__dict__)
    return w


def intra_flip_world(ad, rng, pos_q=1, rho=0.10, nsig=4):
    """INTRA-YEAR-FLIP: ปี 2012-2015 stable(+) · ปี 2016-2020 sign flips ที่ quartile boundary pos_q
    (1=Q2start · 2=Q3 · 3=Q4) ภายในปีนั้น — โลกที่ fine-cadence ควรช่วย (truth known)"""
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
    w = AD4.__new__(AD4)
    w.__dict__.update(ad.__dict__)
    w.rl, w.rs = y / 2.0, -y / 2.0
    w.pL, w.pS = y / 2.0, -y / 2.0
    w.d, w.wt = y, np.abs(y)
    w.dd = np.where(rng.random(ad.n) < 0.5, 1, -1)
    return w


# ================================ modes ================================
def mode_regress(ad):
    """identity/machinery — real-side = identity-zero เท่านั้น · operative = synthetic"""
    ad.build_exp_caches(gbm=False)
    # (1) Q1 ≡ annual structural (โครงสร้าง: estimand ตัด Q1 → ตรวจว่า cutoff Q1 == fold cutoff)
    for i, (Y, tr, te) in enumerate(ad.folds):
        te_idx, q, _ = ad.fold_seg(te)
        assert ad.dayix[te_idx[0]] == ad.dayix[np.where(te)[0]].min(), f"fold {Y} Q1-start ≠ te-start"
    print("[regress-1] Q1-start ≡ te-start ทุก fold ✓ (Q1 identity = โครงสร้าง — estimand ตัด Q1 แล้ว)")
    # (2) label-perm identity π=id ≡ obs bit-exact (synthetic)
    w = as_ad4(synth_stable_world(ad, _rng("ad4_reg", PERM_ROOT)))
    w.build_exp_caches(gbm=False)
    v0 = ad.s1_quart(w)
    id_perms = [np.arange(len(ad.fold_seg(te)[2])) for (Y, tr, te) in ad.folds]
    v1 = ad.s1_quart(w, id_perms)
    print(f"[regress-2] label-perm(π=identity) − obs = {v1 - v0:+.6e} (ต้อง 0 เป๊ะ)")
    assert v1 == v0, "identity-π ไม่ inert!"
    # (3) volume/coverage parity โครงสร้าง: perm ไม่แตะ X · train mask เดิม (นับ)
    perms = ad.label_perms(_rng("ad4_reg_p", PERM_ROOT))
    for i, (Y, tr, te) in enumerate(ad.folds):
        te_idx, q, prefix_idx = ad.fold_seg(te)
        assert len(perms[i]) == len(prefix_idx), "π size ≠ prefix"
        assert sorted(perms[i]) == list(range(len(prefix_idx))), "π ไม่ใช่ bijection!"
    print("[regress-3] π = bijection บน prefix ทุก fold ✓ (X untouched by construction — label copy เท่านั้น)")
    # (4) blocks/null-space (measured — ตรง doc)
    for i, (Y, tr, te) in enumerate(ad.folds):
        m = len(ad.fold_seg(te)[2])
        nblk = m // B_LABEL + (1 if m % B_LABEL else 0)
        print(f"  fold {Y}: prefix {m} → blocks {nblk}")
    # (5) operative exercise บน synthetic (ค่าไม่ใช่ผลจริง)
    print(f"[regress-5] synthetic STABLE S1_quart = {v0:+.4f} (สนามซ้อม) · p_one 1 draw:")
    obs, p, nm, q95 = ad.p_one(w, "ad4_reg_pone", B0=19)
    print(f"  obs={obs:+.4f} p={p:.2f} null-mean={nm:+.4f} (B0=19 smoke)")
    print("[regress] PASS ทั้งหมด")


def cert_stable_chunk(ad, k0, k1):
    os.makedirs(CERT_DIR, exist_ok=True)
    path = os.path.join(CERT_DIR, "stable.csv")
    with open(path, "a") as f:
        for k in range(k0, k1):
            w = as_ad4(synth_stable_world(ad, _rng(f"ad4_cert_s_{k}", PERM_ROOT)))
            w.build_exp_caches(gbm=False)
            obs, p, nm, q95 = ad.p_one(w, f"ad4_certp_{k}")
            f.write(f"{k},{p:.6f},{nm:.6f}\n"); f.flush()
            if (k + 1) % 10 == 0:
                print(f"  [STABLE] {k+1} done", flush=True)
    print(f"[cert_stable] {k0}..{k1-1} → {path}")


def cert_power_cell(ad, ci, k0, k1):
    pos_q, rho = POWER_CELLS[ci]
    os.makedirs(CERT_DIR, exist_ok=True)
    path = os.path.join(CERT_DIR, f"power_{ci}.csv")
    with open(path, "a") as f:
        for k in range(k0, k1):
            w = as_ad4(intra_flip_world(ad, _rng(f"ad4_pw_{ci}_{k}", PERM_ROOT), pos_q=pos_q, rho=rho))
            w.build_exp_caches(gbm=False)
            obs, p, nm, q95 = ad.p_one(w, f"ad4_pwp_{ci}_{k}")
            f.write(f"{k},{p:.6f}\n"); f.flush()
    print(f"[cert_power] cell {ci} (pos_q={pos_q}, rho={rho}) draws {k0}..{k1-1} → {path}")


def cert_report():
    rows = [l.strip().split(",") for l in open(os.path.join(CERT_DIR, "stable.csv"))]
    ks = {int(r[0]): (float(r[1]), float(r[2])) for r in rows}
    assert sorted(ks) == list(range(len(ks))), "stable draws ไม่ต่อเนื่อง"
    ps = np.array([ks[k][0] for k in sorted(ks)])[:CERT_N]
    nms = np.array([ks[k][1] for k in sorted(ks)])[:CERT_N]
    q05 = float(np.quantile(ps, 0.05)); a_dec = min(q05, ALPHA_NOM)
    print(f"[STABLE] N={len(ps)} · q05={q05:.3f} → α*_dec=min(q05,{ALPHA_NOM})={a_dec:.3f} · "
          f"FPR@dec <:{(ps < a_dec).mean()*100:.1f}% ≤:{(ps <= a_dec).mean()*100:.1f}% · "
          f"null-mean เฉลี่ย={nms.mean():+.4f} · p-deciles={[round(float(x),2) for x in np.quantile(ps,[.1,.5,.9])]}")
    det = {}
    for ci, (pos_q, rho) in enumerate(POWER_CELLS):
        path = os.path.join(CERT_DIR, f"power_{ci}.csv")
        if not os.path.exists(path):
            print(f"  cell {ci} (pos{pos_q}, ρ{rho}): ยังไม่รัน"); continue
        pv = np.array([float(l.split(",")[1]) for l in open(path)])[:CERT_N_POWER]
        det[ci] = float((pv < a_dec).mean())
        print(f"  power cell {ci} (Q{pos_q+1}-start-flip, ρ={rho}): N={len(pv)} · det(p<α*_dec)={det[ci]*100:.1f}%")
    if len(det) == len(POWER_CELLS):
        mx = max(det.values())
        branch = "FREE-KILL (structural — budget-exempt)" if mx < a_dec else "ESTIMATION (+1 ⇒ 7/40 ที่ main)"
        print(f"\n[BRANCH — rule-determined R6 · ไม่มี human-choice] empirical max detection = {mx*100:.1f}% "
              f"{'<' if mx < a_dec else '≥'} α*_dec {a_dec:.3f} → **{branch}**")
        print(f"[trend descriptive @earliest-flip] ρ0.10:{det.get(0,0)*100:.0f}% ρ0.15:{det.get(3,0)*100:.0f}% "
              f"ρ0.20:{det.get(6,0)*100:.0f}%")
        print("[certify] → pin FROZEN_CERT + report ต่อวิน → วินสั่ง freeze-commit ก่อน main")


def mode_main(ad):
    if not FROZEN_CERT:
        raise SystemExit("⛔ freeze gate: ต้อง certify → pin FROZEN_CERT + วินสั่ง commit ก่อนรัน main")
    raise SystemExit("main: implement หลัง freeze (pattern AD-2 — estimation-primary + branch assert)")


# ---- pin block (commit spec · card §7(11)(12)(12b) · §0 N2 · N11 freeze · วินสั่ง apply 2026-09-09) ----
SPEC_SHA    = "6b373c55a2c08f0d7973f61e3584f02c1b062251301484044d0b0553d309d9d9"              # sha256(LF-normalized card ณ commit spec) · seal/check = Scripts/pin_ad4.py (--seal/--check) · verify = card_scan.py --require-pin · ห้ามเขียนกลับลง card
KS_T_UNITS  = 23                     # eng16_ks.py part A · N=400 · B=200,000 · seed 20260903 · integer-lattice (t = 23/400)
KS_ACHIEVED = 0.0475                 # achieved false-flag @t · integer convention · atom ที่ t = 1.26%
RG14_TAGS   = tuple(f"ad4_rg14_w{k}" for k in range(50))   # §7(12b) W=50 · world = synth_stable_world(ad, _rng(tag, PERM_ROOT), rho=.10, nsig=4)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "regress"
    ad = AD4.__new__(AD4)
    AD1.__init__(ad)
    print("[AD4] fine-cadence — pre-freeze: quarterly-on-real ⛔ (identity/synthetic เท่านั้น) · b_label=40 [AD-1:76]")
    if mode == "regress":
        mode_regress(ad)
    elif mode == "cert_stable":
        cert_stable_chunk(ad, int(sys.argv[2]), int(sys.argv[3]))
    elif mode == "cert_power":
        cert_power_cell(ad, int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    elif mode == "cert_report":
        cert_report()
    elif mode == "main":
        mode_main(ad)
    else:
        raise SystemExit(f"unknown mode {mode}")

