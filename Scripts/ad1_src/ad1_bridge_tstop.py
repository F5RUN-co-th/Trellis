"""Claude-Verify R5 + C''-test — (1) reproduce conditional 2×2 ของ R5 (subset s-grid เดิม เขาใช้ seed เดียวกัน)
(2) ทดสอบ C'': STOP-branch ใช้ t_stop เข้มกว่า t_slope (STOP = c̄≥t_bar ∧ |slope|≤t_stop ·
    c̄≥t_bar ∧ t_stop<|slope|≤t_slope → DRIFT-SUSPECT→STAGE-2) — ปิด false-STOP ที่ s≈1.5 ได้แค่ไหน
    แลกกับ STABLE-STOP retention เท่าไหร่ · grid ละเอียด s∈{1.25,1.75} เพิ่ม
governance: real-X + synthetic-y · อ่านเฉพาะ feat+yr — P&L untouched
"""
import sys, zlib
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")
from brain_v1_run import load_ctx
from direction_at_real_exit import build_rows

rows = build_rows(load_ctx())
X_all = np.array([r["feat"] for r in rows], float)
yr_all = np.array([r["yr"] for r in rows])
YEARS = sorted(set(yr_all))
NB, NF, NSIG, NSIM = len(YEARS), X_all.shape[1], 4, 120
blocks = [np.where(yr_all == Y)[0] for Y in YEARS]
LAGS = np.arange(1, NB)
Xb = []
for b in blocks:
    Z = X_all[b]
    Xb.append((Z - Z.mean(0)) / (Z.std(0) + 1e-12))
LAM = np.exp(-np.log(2) / 480.0)


def gen_y(scen_s, rho, rng):
    perm = rng.permutation(NF); fa, fb = perm[:NSIG], perm[NSIG:2 * NSIG]
    u = np.zeros(NF); u[fa] = 1.0; v = np.zeros(NF); v[fb] = 1.0
    ys, rho_hat = [], np.zeros((NB, NF))
    for t in range(NB):
        if scen_s == "NOISE":
            beta = np.zeros(NF)
        elif scen_s == "FLIP":
            beta = rho * u * (1 if t < 3 else -1)
        else:
            th = scen_s * (t / (NB - 1)) * (np.pi / 2)
            d = np.cos(th) * u + np.sin(th) * v
            beta = rho * d / max(np.linalg.norm(d) / np.linalg.norm(u), 1e-12)
        Z = Xb[t]; yv = Z @ beta
        sig2 = max(1.0 - float(np.var(yv)), 0.05)
        y = yv + rng.standard_normal(len(Z)) * np.sqrt(sig2)
        ys.append(y); yc = (y - y.mean()) / (y.std() + 1e-12)
        rho_hat[t] = (Z * yc[:, None]).mean(0)
    return ys, rho_hat


def gate_stats(rho_hat):
    C = np.full((NB, NB), np.nan)
    for i in range(NB):
        for j in range(i + 1, NB):
            a, c = rho_hat[i], rho_hat[j]
            C[i, j] = a @ c / (np.linalg.norm(a) * np.linalg.norm(c) + 1e-12)
    lag_c = [np.nanmean(np.diagonal(C, k)) for k in LAGS]
    return float(np.nanmean(C[~np.isnan(C)])), float(np.polyfit(LAGS[:5], lag_c[:5], 1)[0])


def ols_w(Xtr, ytr, w=None):
    A = np.c_[np.ones(len(Xtr)), Xtr]
    if w is not None:
        sw = np.sqrt(w)[:, None]
        return np.linalg.lstsq(A * sw, ytr * sw[:, 0], rcond=None)[0]
    return np.linalg.lstsq(A, ytr, rcond=None)[0]


def skills(ys):
    out = []
    for t in range(4, NB):
        Xtr = np.vstack(Xb[:t]); ytr = np.concatenate(ys[:t]); n = len(ytr)
        lag = np.arange(n)[::-1].astype(float)
        bp = ols_w(Xtr, ytr); bd = ols_w(Xtr, ytr, LAM ** lag)
        Xt = np.c_[np.ones(len(Xb[t])), Xb[t]]; yt = ys[t]
        cc = lambda b: float(np.corrcoef(Xt @ b, yt)[0, 1])
        out.append((cc(bp), cc(bd)))
    return np.array(out).mean(0)


def noise_thr(root=20260717, ndraw=1000):
    st = []
    for s in range(ndraw):
        _, rh = gen_y("NOISE", 0.0, np.random.default_rng([root, 0, 0, s]))
        st.append(gate_stats(rh))
    st = np.array(st)
    return (float(np.quantile(st[:, 0], 0.975)), float(np.quantile(np.abs(st[:, 1]), 0.975)),
            float(np.quantile(-st[:, 1], 0.99)))


t_bar, t_slope, t_flip = noise_thr()
print(f"[1000-draw thresholds] t_bar={t_bar:.4f} t_slope={t_slope:.4f} t_flip={t_flip:.4f} "
      f"(R5 อ้าง t_bar 0.2033)")


def rule_v5(c, m):
    if c < t_bar:
        if m < -t_flip: return "FLIP"
        if abs(m) <= t_slope: return "NOISE"
        return "AMBIG"
    if m < -t_slope: return "MONO"
    if abs(m) <= t_slope: return "STABLE"
    return "AMBIG"


def rng_for(scen, rho, s, root=20260718):
    return np.random.default_rng([root, zlib.crc32(str(scen).encode()) & 0xffff, int(rho * 100), s])


T_STOPS = (0.02, 0.03, 0.05)
R5_SET = {"0.0", "0.5", "1.0", "1.5", "2.0", "4.0", "FLIP"}
for rho in (0.10, 0.15):
    dl_noise = []
    for s in range(NSIM):
        ys, _ = gen_y("NOISE", 0.0, rng_for("NOISE", 0.0, s))
        sk = skills(ys); dl_noise.append(sk[1] - sk[0])
    eps = float(np.quantile(dl_noise, 0.975))
    print(f"\n===== rho={rho} · ε={eps:+.4f} =====")
    recs = []
    for scen in (0.0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 4.0, "FLIP"):
        for s in range(NSIM):
            rng = rng_for(scen, rho, s)
            ys, rh = gen_y(scen, rho, rng)
            c, m = gate_stats(rh); sk = skills(ys)
            recs.append((str(scen), c, m, sk[1] - sk[0]))
    scen_a = np.array([r[0] for r in recs]); cb = np.array([r[1] for r in recs])
    sl = np.array([r[2] for r in recs]); dl = np.array([r[3] for r in recs])
    pred = np.array([rule_v5(c, m) for c, m in zip(cb, sl)])
    ex = dl > eps
    # (1) reproduce R5: STABLE&>ε บน subset scenario เดิมของเขา
    in5 = np.isin(scen_a, list(R5_SET))
    stab = pred == "STABLE"
    print(f"  [reproduce R5 subset] STABLE&>ε = {np.sum(stab & ex & in5)} / STABLE {np.sum(stab & in5)} "
          f"({np.sum(stab & ex & in5)/max(np.sum(stab & in5),1)*100:.1f}% — R5 อ้าง 5.5%/9.5%)")
    # (2) C'' t_stop sweep — STOP = c̄≥t_bar ∧ |slope|≤t_stop
    print(f"  {'rule':<12}{'falseSTOP&>ε':>13}{'STOPtotal':>10}{'ret s=0':>9}{'ret s=0.5':>10}"
          f"{'stop@1.25':>10}{'stop@1.5':>9}{'stop@1.75':>10}")
    def report(tag, stop_mask):
        fs = np.sum(stop_mask & ex)
        ret0 = np.mean(stop_mask[scen_a == "0.0"]) * 100
        ret05 = np.mean(stop_mask[scen_a == "0.5"]) * 100
        s125 = np.mean(stop_mask[scen_a == "1.25"]) * 100
        s15 = np.mean(stop_mask[scen_a == "1.5"]) * 100
        s175 = np.mean(stop_mask[scen_a == "1.75"]) * 100
        print(f"  {tag:<12}{fs:>13}{stop_mask.sum():>10}{ret0:>8.0f}%{ret05:>9.0f}%"
              f"{s125:>9.0f}%{s15:>8.0f}%{s175:>9.0f}%")
    report("v5(t_slope)", stab)
    for ts in T_STOPS:
        report(f"t_stop={ts}", (cb >= t_bar) & (np.abs(sl) <= ts))
    # max Δ|STOP ของ rule ที่เข้มสุดที่ยังรักษา s=0
    for ts in T_STOPS:
        sm = (cb >= t_bar) & (np.abs(sl) <= ts)
        if sm.sum():
            print(f"    t_stop={ts}: mean Δ|STOP={dl[sm].mean():+.4f} · max={dl[sm].max():+.4f} · "
                  f"#>ε ต่อ scenario: " + " ".join(f"{sc}:{np.sum(sm & ex & (scen_a==sc))}"
                  for sc in ("0.0","0.5","1.0","1.25","1.5","1.75")))
