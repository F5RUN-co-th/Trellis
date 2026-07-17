"""Card AD-1 — STAGE-1 gate structural calibration (canonical artifact A · CLAIM-0019)
=====================================================================================
Spec: Plan/TRELLIS-010_card_AD1_adaptive_rolling.md (work-order ratified 07-17 §7.3)
เจ้าของเลข calibration ทั้งหมดของ card AD-1 — merged จาก source 6 ไฟล์ใน `Scripts/ad1_src/`
(ad1_verify_struct / ad1_structural_calib / ad1_exploit_calib / ad1_bridge_conditional [R5] /
ad1_bridge_tstop / ad1_stable_thr — ผ่าน adversarial review 8+ รอบ) + ส่วนเพิ่มตาม checklist:
  [R6-M4] seed-sweep · MONO×cluster-cosine · P&L-guard programmatic · NOISE>=1000
  [R7-F2] residual-scenario-position ที่ operating point A
  [R7-F3] false-STOP report บน population เดียว (pooled 9-scenario)
  realized-corr emit (nominal-beta ≠ realized เพราะ Σ-bleed)
  [M10/C2 · reconstruction 07-17] routing/รายงานทุกจุดใช้ค่า DERIVED สด ·
  FROZEN_THR = assert-check เท่านั้น (fail-loud ถ้า drift) — ห้ามเป็น input (กัน circular-reproduce)

governance: P&L-free แท้ — โหลดเฉพาะ feature matrix + year (guard ใน load_features_only)
สนาม: SIM-SEARCH 2012-2020 · lockbox 2024-26 + guard 2021-23 ไม่ถูกแตะ
run:  python ad1_gate_calib.py           (calibration เต็ม ~10 นาที)
"""
import sys, zlib, hashlib
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")

# ---------------- frozen constants (doc §3.0/§3.2 — main() re-derive แล้ว assert) ----------------
SEED_THR = 20260717      # NOISE/STABLE threshold draws
SEED_SCEN = 20260718     # scenario sims
NDRAW_THR = 1000         # R5-B4: 150-200 draws แกว่ง ±15% → 1000
NSIM = 120               # ต่อ scenario ต่อ rho
NSIG = 4                 # signal features ต่อ archetype
H_TRADES = 480.0         # decay half-life (1 era · ex-ante)
K_ROLL = 300             # rolling secondary
P_TSTOP, RHO_REF = 0.90, 0.10   # operating point A — q90 by-choice จาก cost-asymmetry (ไม่ใช่ q97.5)
S_GRID = (0.0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 4.0, "FLIP")
RHO_GRID = (0.10, 0.15)
LAM = np.exp(-np.log(2) / H_TRADES)

# FROZEN (emit ครั้งแรก 07-16 · seed 20260717 · 1000 draws) — assert-check เท่านั้น [M10]
FROZEN_THR = {"t_bar": 0.2033, "t_slope": 0.1289, "t_flip": 0.1394, "t_stop": 0.0182}


def load_features_only():
    """P&L-guard programmatic [R6-M4]: คืนเฉพาะ X, yr — payoff ไม่ถูกถือไว้หลัง del rows"""
    from brain_v1_run import load_ctx
    from direction_at_real_exit import build_rows
    rows = build_rows(load_ctx())
    X = np.array([r["feat"] for r in rows], float)
    yr = np.array([r["yr"] for r in rows])
    payoff_keys = {"pL", "pS", "R", "fpnl"} & set(rows[0].keys())
    assert payoff_keys, "sanity: build_rows ต้องมี payoff keys (โครงสร้างเปลี่ยน = ตรวจ guard ใหม่)"
    del rows
    return X, yr


def make_blocks(X, yr):
    years = sorted(set(yr))
    blocks = [np.where(yr == Y)[0] for Y in years]
    Xb = []
    for b in blocks:
        Z = X[b]
        Xb.append((Z - Z.mean(0)) / (Z.std(0) + 1e-12))
    return years, blocks, Xb


def gate_stats(rho_hat):
    """(c̄, slope lag1-5) — generic: NB จาก shape (ad1_card ใช้ร่วม · SSOT)"""
    NB = rho_hat.shape[0]
    C = np.full((NB, NB), np.nan)
    for i in range(NB):
        for j in range(i + 1, NB):
            a, c = rho_hat[i], rho_hat[j]
            C[i, j] = a @ c / (np.linalg.norm(a) * np.linalg.norm(c) + 1e-12)
    lags = np.arange(1, NB)
    lag_c = [np.nanmean(np.diagonal(C, k)) for k in lags]
    return float(np.nanmean(C[~np.isnan(C)])), float(np.polyfit(lags[:5], lag_c[:5], 1)[0])


def rule(cbar, slope, thr):
    """SSOT routing — 6 outcome (doc §3.0) · thr ต้องส่งค่า derived เข้ามา [M10 — ไม่มี default]"""
    if cbar < thr["t_bar"]:
        if slope < -thr["t_flip"]:
            return "FLIP"
        if abs(slope) <= thr["t_slope"]:
            return "NO-DETECT"
        return "AMBIG"
    if slope < -thr["t_slope"]:
        return "MONO"
    if abs(slope) <= thr["t_stop"]:
        return "PERSISTENT"
    if abs(slope) <= thr["t_slope"]:
        return "DRIFT-SUSPECT"
    return "AMBIG"


STOP_SET = {"NO-DETECT", "PERSISTENT"}


class Calib:
    """ครอบ state (X blocks) — heavy load อยู่ในนี้เท่านั้น"""

    def __init__(self):
        self.X, self.yr = load_features_only()
        self._index()

    @classmethod
    def from_arrays(cls, X, yr):
        """[F-1 fix 07-17] สร้างจาก arrays ที่ caller โหลดแล้ว — กัน duplicate load (Working Rule 3)
        ปลอดภัยจาก P&L cross-contamination เมื่อ caller เป็น canonical B (P&L-touch) เพราะ:
        (หลัก) assert-binding provenance ใน derive_thresholds — derived ต้อง == FROZEN ที่ emit
        จาก P&L-free context (A) มิฉะนั้น crash → thresholds ถือ provenance ของ A เสมอ ·
        (รอง) derive ใช้แค่ X,yr + y สังเคราะห์ standard_normal — payoff encode ลง thresholds ไม่ได้"""
        c = cls.__new__(cls)
        c.X, c.yr = X, yr
        c._index()
        return c

    def _index(self):
        self.years, self.blocks, self.Xb = make_blocks(self.X, self.yr)
        self.NB, self.NF = len(self.years), self.X.shape[1]
        self.sha = hashlib.sha256(self.X.tobytes()).hexdigest()[:16]

    def gen_y(self, scen_s, rho, rng, want_y=True, want_realized=False):
        NB, NF = self.NB, self.NF
        perm = rng.permutation(NF); fa, fb = perm[:NSIG], perm[NSIG:2 * NSIG]
        u = np.zeros(NF); u[fa] = 1.0; v = np.zeros(NF); v[fb] = 1.0
        ys, rho_hat, realized = [], np.zeros((NB, NF)), []
        for t in range(NB):
            if scen_s == "NOISE":
                beta = np.zeros(NF)
            elif scen_s == "FLIP":
                beta = rho * u * (1 if t < 3 else -1)
            elif isinstance(scen_s, str) and scen_s.startswith("RFLIP"):
                # [STEP-3 C-exploit · M12] REPEATED-FLIP(period P บล็อก): สลับ sign ทุก P blocks
                P = float(scen_s.split("@")[1])
                beta = rho * u * (1.0 if (int(t // P) % 2 == 0) else -1.0)
            else:
                th = scen_s * (t / (NB - 1)) * (np.pi / 2)
                d = np.cos(th) * u + np.sin(th) * v
                beta = rho * d / max(np.linalg.norm(d) / np.linalg.norm(u), 1e-12)
            Z = self.Xb[t]; yv = Z @ beta
            sig2 = max(1.0 - float(np.var(yv)), 0.05)
            y = yv + rng.standard_normal(len(Z)) * np.sqrt(sig2)
            if want_y:
                ys.append(y)
            yc = (y - y.mean()) / (y.std() + 1e-12)
            rho_hat[t] = (Z * yc[:, None]).mean(0)
            if want_realized and t == 0 and scen_s not in ("NOISE",):
                realized = rho_hat[0][fa]
        return ys, rho_hat, (fa, fb, realized)

    @staticmethod
    def ols_w(Xtr, ytr, w=None):
        A = np.c_[np.ones(len(Xtr)), Xtr]
        if w is not None:
            sw = np.sqrt(w)[:, None]
            return np.linalg.lstsq(A * sw, ytr * sw[:, 0], rcond=None)[0]
        return np.linalg.lstsq(A, ytr, rcond=None)[0]

    def deltas(self, ys):
        """Δdecay, Δrolling — skill corr(pred,y) เฉลี่ย test blocks 4..8 (= 2016-2020 ตรง primary fold-set)"""
        dd, dr = [], []
        for t in range(4, self.NB):
            Xtr = np.vstack(self.Xb[:t]); ytr = np.concatenate(ys[:t]); n = len(ytr)
            lag = np.arange(n)[::-1].astype(float)
            bp = self.ols_w(Xtr, ytr)
            bd = self.ols_w(Xtr, ytr, LAM ** lag)
            br = self.ols_w(Xtr[-K_ROLL:], ytr[-K_ROLL:])
            Xt = np.c_[np.ones(len(self.Xb[t])), self.Xb[t]]; yt = ys[t]
            cc = lambda b: float(np.corrcoef(Xt @ b, yt)[0, 1])
            dd.append(cc(bd) - cc(bp)); dr.append(cc(br) - cc(bp))
        return float(np.mean(dd)), float(np.mean(dr))

    def rng_thr(self, tag, s, rho=0.0, root=SEED_THR):
        return np.random.default_rng([root, zlib.crc32(tag) & 0xffff, int(rho * 100), s])

    def rng_scen(self, scen, rho, s, root=SEED_SCEN):
        return np.random.default_rng([root, zlib.crc32(str(scen).encode()) & 0xffff, int(rho * 100), s])

    def noise_thr(self, root=SEED_THR, ndraw=NDRAW_THR):
        st = []
        for s in range(ndraw):
            _, rh, _ = self.gen_y("NOISE", 0.0, np.random.default_rng([root, 0, 0, s]), want_y=False)
            st.append(gate_stats(rh))
        st = np.array(st)
        return (float(np.quantile(st[:, 0], 0.975)), float(np.quantile(np.abs(st[:, 1]), 0.975)),
                float(np.quantile(-st[:, 1], 0.99)))

    def stable_thr(self, rho_ref, ndraw=NDRAW_THR, root=SEED_THR):
        """เจ้าของ t_stop [R6-BLOCKING-1] — q_p(|slope|) ใต้ synthetic-STABLE @rho_ref บน X จริง"""
        sl = []
        for s in range(ndraw):
            _, rh, _ = self.gen_y(0.0, rho_ref, self.rng_thr(b"STABTHR", s, rho_ref, root), want_y=False)
            sl.append(abs(gate_stats(rh)[1]))
        sl = np.array(sl)
        return {p: float(np.quantile(sl, p)) for p in (0.90, 0.95, 0.975)}

    def derive_thresholds(self):
        """[M10] derive สด → assert vs FROZEN → คืนค่า DERIVED สำหรับ routing (frozen = check เท่านั้น)"""
        t_bar, t_slope, t_flip = self.noise_thr()
        qs = self.stable_thr(RHO_REF)
        thr = {"t_bar": t_bar, "t_slope": t_slope, "t_flip": t_flip, "t_stop": qs[P_TSTOP]}
        for k in thr:
            assert abs(thr[k] - FROZEN_THR[k]) < 5e-5, \
                f"FROZEN_THR drift: {k} derived {thr[k]:.4f} != pinned {FROZEN_THR[k]}"
        return thr, qs


def main():
    from collections import Counter
    cal = Calib()
    print(f"[X] n={len(cal.X)} NF={cal.NF} blocks={[len(b) for b in cal.blocks]} sha={cal.sha} "
          f"(payoff-guard: del rows)")

    # ============ 1) thresholds: derive → assert(FROZEN) → route ด้วย derived [M10] ============
    thr, qs = cal.derive_thresholds()
    print(f"\n[FROZEN thresholds @seed {SEED_THR} · {NDRAW_THR} draws] t_bar={thr['t_bar']:.4f} "
          f"t_slope={thr['t_slope']:.4f} t_flip={thr['t_flip']:.4f} · stable_thr@rho{RHO_REF}: "
          f"q90={qs[0.90]:.4f} q95={qs[0.95]:.4f} q97.5={qs[0.975]:.4f} "
          f"→ t_stop(A · p={P_TSTOP} by-choice cost-asymmetry) = {thr['t_stop']:.4f}")
    print("  [ASSERT] derived == FROZEN_THR pinned ทั้ง 4 ✓ (routing ใช้ derived — M10)")
    print("[seed-sweep 300-draw · stability report — frozen ค่าบนเท่านั้น]")
    for root in (1, 42):
        tb, ts, tf = cal.noise_thr(root=root, ndraw=300)
        print(f"  root={root}: t_bar={tb:.4f} t_slope={ts:.4f} t_flip={tf:.4f}")

    # ============ 2) retention ต่อ rho + MONO fire + realized-corr ============
    print(f"\n[retention STABLE(s=0) → PERSISTENT-STOP · t_stop={thr['t_stop']:.4f}]")
    for r in (0.05, 0.07, 0.10, 0.15):
        outs, rls = [], []
        for s in range(NSIM):
            _, rh, (fa, fb, rl_) = cal.gen_y(0.0, r, cal.rng_scen(0.0, r, s), want_y=False, want_realized=True)
            outs.append(rule(*gate_stats(rh), thr))
            rls.append(np.mean(np.abs(rl_)))
        print(f"  rho={r}: PERSISTENT {np.mean([o == 'PERSISTENT' for o in outs])*100:.0f}% · "
              f"realized|corr|(signal-feat · nominal-beta={r}) = {np.mean(rls):.4f} · dist {dict(Counter(outs))}")

    print("\n[MONO fire @s=2.0]")
    for r in RHO_GRID:
        outs = [rule(*gate_stats(cal.gen_y(2.0, r, cal.rng_scen(2.0, r, s), want_y=False)[1]), thr)
                for s in range(NSIM)]
        print(f"  rho={r}: MONO {np.mean([o == 'MONO' for o in outs])*100:.1f}% · dist {dict(Counter(outs))}")

    print("\n[MONO(s=1.0)×cluster-cosine — detectability เทียบความ orthogonal ของ fa/fb response บน Σ จริง]")
    CORR = np.corrcoef(np.vstack(cal.Xb).T)
    for r in (0.10,):
        cos_uv, routed = [], []
        for s in range(NSIM):
            rng = cal.rng_scen(1.0, r, s)
            perm = rng.permutation(cal.NF); fa, fb = perm[:NSIG], perm[NSIG:2 * NSIG]
            ra, rb = CORR[fa].mean(0), CORR[fb].mean(0)
            cos_uv.append(float(ra @ rb / (np.linalg.norm(ra) * np.linalg.norm(rb) + 1e-12)))
            rng2 = cal.rng_scen(1.0, r, s)
            routed.append(rule(*gate_stats(cal.gen_y(1.0, r, rng2, want_y=False)[1]), thr) != "PERSISTENT")
        cos_uv, routed = np.array(cos_uv), np.array(routed)
        med = np.median(cos_uv)
        print(f"  rho={r}: routed-non-PERSISTENT | cos<med({med:.3f}) = {routed[cos_uv < med].mean()*100:.0f}% · "
              f"cos>=med = {routed[cos_uv >= med].mean()*100:.0f}% "
              f"(orthogonal-cluster กว่า = เห็น rotation ง่ายกว่าไหม)")

    # ============ 3) pooled single-population [R7-F3] + residual-position@A [R7-F2] ============
    for rho in RHO_GRID:
        dl_noise = [cal.deltas(cal.gen_y("NOISE", 0.0, cal.rng_scen("NOISE", 0.0, s))[0])[0]
                    for s in range(NSIM)]
        eps = float(np.quantile(dl_noise, 0.975))
        recs = []
        for scen in S_GRID:
            for s in range(NSIM):
                ys, rh, _ = cal.gen_y(scen, rho, cal.rng_scen(scen, rho, s))
                c, m = gate_stats(rh)
                dd, dr = cal.deltas(ys)
                recs.append((str(scen), rule(c, m, thr), dd, dr))
        scen_a = np.array([x[0] for x in recs]); out = np.array([x[1] for x in recs])
        dd = np.array([x[2] for x in recs]); dr = np.array([x[3] for x in recs])
        pers = out == "PERSISTENT"; nod = out == "NO-DETECT"; ex = dd > eps
        print(f"\n===== rho={rho} · ε(decay)={eps:+.4f} · pooled N={len(recs)} (single population) =====")
        print(f"  [regression vs frozen doc] PERSISTENT&>ε = {np.sum(pers & ex)} / PERSISTENT {pers.sum()} "
              f"({np.sum(pers & ex)/max(pers.sum(),1)*100:.1f}%) · maxΔdecay|PERSISTENT = {dd[pers].max():+.4f} "
              f"({dd[pers].max()/eps:.2f}×ε)")
        print(f"  NO-DETECT&>ε = {np.sum(nod & ex)} / NO-DETECT {nod.sum()} (declared residual แยก)")
        pos = {sc: int(np.sum(pers & ex & (scen_a == sc))) for sc in map(str, S_GRID)
               if np.sum(pers & ex & (scen_a == sc))}
        print(f"  residual-position@A (per-scenario · PERSISTENT-cell · [R7-F2]): {pos if pos else '{}'}")
        fl = scen_a == "FLIP"
        print(f"  FLIP exploitability: Δdecay={dd[fl].mean():+.4f} · Δrolling={dr[fl].mean():+.4f} "
              f"(ratio {dr[fl].mean()/max(dd[fl].mean(),1e-9):.2f}× — rolling-secondary bound §6)")
    print("\n[DONE] calibration artifact — ทุกเลขข้างบน = frozen calibration record ของ card AD-1")


def rflip_sweep():
    """[STEP-3 C-exploit · spec frozen หลัง M7 PASS-with-changes 07-17 · §9.1 pre-registered ก่อนรัน]
    RFLIP@P sweep — P_blocks ∈ {2, 2.5, 3, 3.5, 4, 6, 8} (S2: transition-resolution {2.5..4} +
    geometric spine {2,4,8} + P=6 single-flip control · เบี่ยงจาก literal-geometric = justified โดย
    M7 free-probe: phenomenon กระจุก P≈H เพราะ block-discretization)
    DECLARED นอก sweep [S5]: P<1 = sub-block beat (block-constant beta จำลองไม่ได้ · ρ̂→0 unexploitable) ·
    P>=9 = zero-flip ≡ STABLE (นอก measurable range NB=9)
    [S3] emit false-STOP ทั้ง decay และ rolling ต่อ P-cell (ε แยก arm — กัน under-state residual เงียบ)
    scope [M13]: periodic เท่านั้น · aperiodic-switch = declared residual นอก sweep"""
    from collections import Counter
    cal = Calib()
    print(f"[X] n={len(cal.X)} blocks={[len(b) for b in cal.blocks]} sha={cal.sha}")
    thr, _ = cal.derive_thresholds()
    print(f"[thr derived==FROZEN ✓] t_bar={thr['t_bar']:.4f} t_stop={thr['t_stop']:.4f}")
    P_GRID = (2.0, 2.5, 3.0, 3.5, 4.0, 6.0, 8.0)
    for rho in RHO_GRID:
        dn, rn = [], []
        for s in range(NSIM):
            ys, _, _ = cal.gen_y("NOISE", 0.0, cal.rng_scen("NOISE", 0.0, s))
            a, b = cal.deltas(ys)
            dn.append(a); rn.append(b)
        eps_d, eps_r = float(np.quantile(dn, 0.975)), float(np.quantile(rn, 0.975))
        print(f"\n===== RFLIP sweep · rho={rho} · ε_decay={eps_d:+.4f} · ε_roll={eps_r:+.4f} · NSIM={NSIM} =====")
        print(f"{'P':>4} {'flips':>5} {'%NO-DET':>8} {'%PERSIST':>9} {'%STG2':>6} "
              f"{'fsSTOP_dec':>10} {'fsSTOP_roll':>11} {'Δdec':>8} {'Δroll':>8}")
        for P in P_GRID:
            scen = f"RFLIP@{P}"
            outs, dd, dr = [], [], []
            for s in range(NSIM):
                ys, rh, _ = cal.gen_y(scen, rho, cal.rng_scen(scen, rho, s))
                outs.append(rule(*gate_stats(rh), thr))
                a, b = cal.deltas(ys)
                dd.append(a); dr.append(b)
            outs = np.array(outs); dd = np.array(dd); dr = np.array(dr)
            stop = np.isin(outs, list(STOP_SET))
            nflip = sum(1 for t in range(1, cal.NB) if int(t // P) % 2 != int((t - 1) // P) % 2)
            print(f"{P:>4} {nflip:>5} {np.mean(outs=='NO-DETECT')*100:>7.0f}% "
                  f"{np.mean(outs=='PERSISTENT')*100:>8.0f}% {np.mean(~stop)*100:>5.0f}% "
                  f"{np.mean(stop & (dd>eps_d))*100:>9.1f}% {np.mean(stop & (dr>eps_r))*100:>10.1f}% "
                  f"{dd.mean():>+8.4f} {dr.mean():>+8.4f}")
            pos = dict(Counter(outs[stop & (dr > eps_r)])) if np.any(stop & (dr > eps_r)) else {}
            if pos:
                print(f"     residual-position (STOP∧Δroll>ε · outcome-class): {pos}")
    print("\n[DONE] RFLIP sweep — periodic เท่านั้น · aperiodic + P<1 + P>=9 = declared residuals")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rflip":
        rflip_sweep()
    else:
        main()
