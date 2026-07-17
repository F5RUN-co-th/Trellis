"""Claude-Verify R6 — t_stop provenance (BLOCKING-1) + low-rho retention (MAJOR-2) + MONO fire
ทุกเลขที่จะลง doc v7 ต้องมาจาก output ของไฟล์นี้เท่านั้น — ไม่มี sweep-แล้ว-label
- stable_thr(rho_ref, p): q_p(|slope|) ใต้ synthetic-STABLE บน X จริง (1000 draws · frozen seed)
- operating points: A = q90@rho0.10 · B = q97.5@rho0.10 — emit ทุก headline ที่ทั้งสองค่า
- retention s=0 ที่ rho ∈ {0.05,0.07,0.10,0.15} ที่ทั้งสอง operating point
- MONO fire rate @s=2.0 (ข้อที่ไม่เคย reproduce เอง)
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


def gen_y(scen_s, rho, rng, want_y=True):
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
        if want_y:
            ys.append(y)
        yc = (y - y.mean()) / (y.std() + 1e-12)
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


def d_decay(ys):
    out = []
    for t in range(4, NB):
        Xtr = np.vstack(Xb[:t]); ytr = np.concatenate(ys[:t]); n = len(ytr)
        lag = np.arange(n)[::-1].astype(float)
        bp = ols_w(Xtr, ytr); bd = ols_w(Xtr, ytr, LAM ** lag)
        Xt = np.c_[np.ones(len(Xb[t])), Xb[t]]; yt = ys[t]
        out.append(float(np.corrcoef(Xt @ bd, yt)[0, 1]) - float(np.corrcoef(Xt @ bp, yt)[0, 1]))
    return float(np.mean(out))


def noise_thr(root=20260717, ndraw=1000):
    st = []
    for s in range(ndraw):
        _, rh = gen_y("NOISE", 0.0, np.random.default_rng([root, 0, 0, s]), want_y=False)
        st.append(gate_stats(rh))
    st = np.array(st)
    return (float(np.quantile(st[:, 0], 0.975)), float(np.quantile(np.abs(st[:, 1]), 0.975)),
            float(np.quantile(-st[:, 1], 0.99)))


def stable_thr(rho_ref, ndraw=1000, root=20260717):
    """q_p(|slope|) ใต้ synthetic-STABLE @rho_ref บน X จริง — เจ้าของค่า t_stop"""
    tag = zlib.crc32(b"STABTHR") & 0xffff
    sl = []
    for s in range(ndraw):
        _, rh = gen_y(0.0, rho_ref, np.random.default_rng([root, tag, int(rho_ref * 100), s]), want_y=False)
        sl.append(abs(gate_stats(rh)[1]))
    sl = np.array(sl)
    return {p: float(np.quantile(sl, p)) for p in (0.90, 0.95, 0.975)}


t_bar, t_slope, t_flip = noise_thr()
print(f"[NOISE 1000] t_bar={t_bar:.4f} t_slope={t_slope:.4f} t_flip={t_flip:.4f}")

print("\n[stable_thr — |slope| quantiles ใต้ synthetic-STABLE (1000 draws · seed frozen) — ตรวจ R6]")
Q = {}
for r in (0.05, 0.07, 0.10, 0.15):
    Q[r] = stable_thr(r)
    print(f"  rho={r}: q90={Q[r][0.90]:.4f} q95={Q[r][0.95]:.4f} q97.5={Q[r][0.975]:.4f}"
          f"  (R6 อ้าง @0.10: q90=0.0199 q97.5=0.0387 · @0.15: q90=0.0077 q97.5=0.0236)")

TS_A = Q[0.10][0.90]    # operating point A: p=0.90 @rho_ref=0.10
TS_B = Q[0.10][0.975]   # operating point B: p=0.975 @rho_ref=0.10
print(f"\n[operating points] A(q90@0.10) t_stop={TS_A:.4f} · B(q97.5@0.10) t_stop={TS_B:.4f}")


def rng_for(scen, rho, s, root=20260718):
    return np.random.default_rng([root, zlib.crc32(str(scen).encode()) & 0xffff, int(rho * 100), s])


# retention s=0 (STABLE world) ต่อ rho ต่อ operating point — gate_stats เท่านั้น
print("\n[retention: STABLE(s=0) world → PERSISTENT-STOP rate — ตรวจ R6 MAJOR-2]")
for r in (0.05, 0.07, 0.10, 0.15):
    cs, ms = [], []
    for s in range(NSIM):
        _, rh = gen_y(0.0, r, rng_for(0.0, r, s), want_y=False)
        c, m = gate_stats(rh); cs.append(c); ms.append(m)
    cs, ms = np.array(cs), np.array(ms)
    fire = np.mean(cs >= t_bar)
    retA = np.mean((cs >= t_bar) & (np.abs(ms) <= TS_A))
    retB = np.mean((cs >= t_bar) & (np.abs(ms) <= TS_B))
    print(f"  rho={r}: c̄>=t_bar {fire*100:.0f}% · ret@A {retA*100:.0f}% · ret@B {retB*100:.0f}%"
          f"  (R6 อ้าง @0.05 ret(0.02)=55%)")

# MONO fire @s=2.0 (reproduce ที่ไม่เคยทำเอง)
print("\n[MONO fire @s=2.0 — ตรวจ R5/R6]")
for r in (0.10, 0.15):
    mono = 0
    for s in range(NSIM):
        _, rh = gen_y(2.0, r, rng_for(2.0, r, s), want_y=False)
        c, m = gate_stats(rh)
        if c >= t_bar and m < -t_slope:
            mono += 1
    print(f"  rho={r}: MONO {mono}/{NSIM} = {mono/NSIM*100:.1f}%  (R5/R6 อ้าง 20.0%/27.5%)")

# headline ที่ operating point จริง (pooled 9 scenarios · ต้องใช้ Δdecay)
for rho in (0.10, 0.15):
    dl_noise = []
    for s in range(NSIM):
        ys, _ = gen_y("NOISE", 0.0, rng_for("NOISE", 0.0, s))
        dl_noise.append(d_decay(ys))
    eps = float(np.quantile(dl_noise, 0.975))
    recs = []
    for scen in (0.0, 0.5, 1.0, 1.25, 1.5, 1.75, 2.0, 4.0, "FLIP"):
        for s in range(NSIM):
            ys, rh = gen_y(scen, rho, rng_for(scen, rho, s))
            c, m = gate_stats(rh)
            recs.append((c, m, d_decay(ys)))
    cb = np.array([x[0] for x in recs]); sl = np.array([x[1] for x in recs]); dl = np.array([x[2] for x in recs])
    ex = dl > eps
    base = (cb >= t_bar) & (np.abs(sl) <= t_slope)   # v5 rule (ก่อน C'')
    print(f"\n===== rho={rho} · ε={eps:+.4f} · pooled N={len(recs)} =====")
    print(f"  v5(t_slope): falseSTOP&>ε={np.sum(base & ex)} · STOPtotal={base.sum()}")
    for nm, ts in (("A", TS_A), ("B", TS_B)):
        m_ = (cb >= t_bar) & (np.abs(sl) <= ts)
        fs = np.sum(m_ & ex)
        print(f"  point {nm} (t_stop={ts:.4f}): falseSTOP&>ε={fs} ({fs/max(m_.sum(),1)*100:.1f}% ของ STOP {m_.sum()})"
              f" · maxΔ|STOP={dl[m_].max():+.4f} ({dl[m_].max()/eps:.2f}×ε)"
              f" · reduction vs v5 = {(1 - fs/max(np.sum(base & ex),1))*100:.0f}%")
