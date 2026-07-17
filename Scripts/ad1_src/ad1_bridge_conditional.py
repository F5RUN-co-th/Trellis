"""R5 adversarial — bridge CONDITIONAL cell test.
freeze-blocking claim = "ไม่มี gap invisible-แต่-exploitable" ต้องการ P(Δdecay>ε | gate=PERSISTENT),
ไม่ใช่ marginal (scenario-mean Δdecay กับ %PERSIST แยกกัน) ที่ ad1_exploit_calib.py รายงาน.
ตรงจุดเสี่ยง: s=2.0 มี PERSIST-leak 9% — Δdecay ของ 9% นั้นไม่เคยถูกตรวจแยก.
ที่นี่ pool ทุก sim ข้ามทุก scenario → 2×2: gate∈{PERSIST,STG2} × Δdecay∈{≤ε,>ε}.
เพิ่ม s∈{1.5} เพื่อ sample transition band (1,2) ที่ original bracket ข้าม.
governance: อ่านเฉพาะ feat+yr (import จาก exploit_calib logic) — P&L untouched.
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
print(f"real-X: n={len(X_all)} blocks={[len(b) for b in blocks]}")


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
        bp = ols_w(Xtr, ytr); bd = ols_w(Xtr, ytr, LAM ** lag); br = ols_w(Xtr[-300:], ytr[-300:])
        Xt = np.c_[np.ones(len(Xb[t])), Xb[t]]; yt = ys[t]
        cc = lambda b: float(np.corrcoef(Xt @ b, yt)[0, 1])
        out.append((cc(bp), cc(bd), cc(br)))
    return np.array(out).mean(0)


# thresholds root=20260717 (ตาม exploit_calib default)
def noise_thr(root=20260717, ndraw=1000):
    st = []
    for s in range(ndraw):
        _, rh = gen_y("NOISE", 0.0, np.random.default_rng([root, 0, 0, s]))
        st.append(gate_stats(rh))
    st = np.array(st)
    return (float(np.quantile(st[:, 0], 0.975)), float(np.quantile(np.abs(st[:, 1]), 0.975)),
            float(np.quantile(-st[:, 1], 0.99)))


print("\n[NOISE thresholds @ 1000 draws — R5 stability check vs doc 0.176-0.203]")
t_bar, t_slope, t_flip = noise_thr(ndraw=1000)
print(f"  t_bar={t_bar:.4f} t_slope={t_slope:.4f} t_flip={t_flip:.4f}")


def rule(cbar, slope):
    if cbar < t_bar:
        if slope < -t_flip: return "FLIP"
        if abs(slope) <= t_slope: return "NOISE"
        return "AMBIG"
    if slope < -t_slope: return "MONO"
    if abs(slope) <= t_slope: return "STABLE"
    return "AMBIG"


# PERSISTENT→STOP per DESIGN doc = STABLE (Σ-bleed) + MONO (absorbed declared residual)
STOP = {"STABLE", "MONO", "NOISE"}   # NOISE→STOP (NO-DETECT) · STABLE/MONO→STOP (PERSISTENT)
PERSIST_STOP = {"STABLE", "MONO"}    # ตัว claim: gate อ่านว่า "มี relationship แต่ stationary/invisible" → STOP


def rng_for(scen, rho, s, root=20260718):
    tag = zlib.crc32(str(scen).encode()) & 0xffff
    return np.random.default_rng([root, tag, int(rho * 100), s])


for rho in (0.10, 0.15):
    print(f"\n===== rho={rho} · ε from NOISE q97.5 · CONDITIONAL cell test =====")
    eps_pool = None
    # หา ε ก่อน (NOISE Δdecay q97.5)
    dl_noise = []
    for s in range(NSIM):
        ys, _ = gen_y("NOISE", 0.0, rng_for("NOISE", 0.0, s))
        sk = skills(ys); dl_noise.append(sk[1] - sk[0])
    eps = float(np.quantile(dl_noise, 0.975))
    print(f"  ε(decay)={eps:+.4f}")
    # pool ทุก scenario · เก็บ per-sim (pred, dl)
    all_pred, all_dl, all_s, all_cb, all_sl = [], [], [], [], []
    for scen in (0.0, 0.5, 1.0, 1.5, 2.0, 4.0, "FLIP"):
        for s in range(NSIM):
            rng = rng_for(scen, rho, s)
            ys, rh = gen_y(scen, rho, rng)
            c, m = gate_stats(rh); sk = skills(ys)
            all_pred.append(rule(c, m)); all_dl.append(sk[1] - sk[0]); all_s.append(scen)
            all_cb.append(c); all_sl.append(m)
    all_pred, all_dl, all_s = np.array(all_pred), np.array(all_dl), np.array(all_s)
    all_cb, all_sl = np.array(all_cb), np.array(all_sl)
    persist = np.isin(all_pred, list(PERSIST_STOP))
    exploit = all_dl > eps
    # 2×2 pooled
    print(f"  POOLED 2x2 (all rotations · N={len(all_pred)}):")
    print(f"    PERSIST&exploit(>ε)  = {np.sum(persist & exploit):3d}  <-- FALSE-STOP-ON-EXPLOITABLE cell (ต้อง ~0)")
    print(f"    PERSIST&safe(≤ε)     = {np.sum(persist & ~exploit):3d}")
    print(f"    STG2&exploit         = {np.sum(~persist & exploit):3d}")
    print(f"    STG2&safe            = {np.sum(~persist & ~exploit):3d}")
    if persist.sum() > 0:
        print(f"    mean Δdecay | PERSIST = {all_dl[persist].mean():+.4f} · max = {all_dl[persist].max():+.4f}")
    # STABLE-only cell (code MONO→STG2 reading)
    stable = all_pred == "STABLE"
    print(f"  STABLE-only (code MONO→STG2 reading): STABLE&>ε = {np.sum(stable & exploit):3d} / STABLE-total {stable.sum():3d}")
    # per-scenario conditional (เพ่ง transition band) + c̄/slope + STABLE vs MONO split
    print(f"  per-scenario: c̄ slope · %STABLE %MONO · mean|STAB max|STAB · #STAB&>ε")
    for scen in (0.0, 0.5, 1.0, 1.5, 2.0, 4.0, "FLIP"):
        m = np.array([str(x) == str(scen) for x in all_s])
        sm = stable[m]; dm = all_dl[m]; mono_m = (all_pred[m] == "MONO")
        nm = f"s={scen}" if not isinstance(scen, str) else scen
        cb_m, sl_m = all_cb[m].mean(), all_sl[m].mean()
        if sm.sum() > 0:
            print(f"    {nm:<7} c̄={cb_m:+.3f} sl={sl_m:+.4f} · %STAB={sm.mean()*100:5.1f}% %MONO={mono_m.mean()*100:4.1f}% · "
                  f"mean|S={dm[sm].mean():+.4f} max|S={dm[sm].max():+.4f} #S&>ε={np.sum(sm & (dm>eps))}")
        else:
            print(f"    {nm:<7} c̄={cb_m:+.3f} sl={sl_m:+.4f} · %STAB={sm.mean()*100:5.1f}% %MONO={mono_m.mean()*100:4.1f}% · (no STABLE)")
