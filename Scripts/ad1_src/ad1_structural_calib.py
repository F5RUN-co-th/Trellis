"""AD-1 STAGE-1 structural calibration — REAL-X + SYNTHETIC-y (P&L-free แท้)
Claude-Verify R3-M1: (1) correlated-X ทำ shape-power พังจริงไหม (R3 estimate: d' 1.2→~0.6)
(2) score decision rule (c̄, slope)-only 4-way + ambiguous ที่ v3 จะใช้จริง (ไม่มี min-pair)
(3) วัด real-structure power-floor + MIXED archetype (blind spot สามชั้น)
governance: ใช้เฉพาะ rows[i]['feat'] + 'yr' — ไม่อ่าน pL/pS/R/payoff ใดๆ
"""
import sys, zlib
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")
from brain_v1_run import load_ctx
from direction_at_real_exit import build_rows

rows = build_rows(load_ctx())
X_all = np.array([r["feat"] for r in rows], float)          # 1486 x 19 — features เท่านั้น
yr_all = np.array([r["yr"] for r in rows])
YEARS = sorted(set(yr_all))
NB, NF, NSIG, NSIM = len(YEARS), X_all.shape[1], 4, 200
blocks = [np.where(yr_all == Y)[0] for Y in YEARS]
LAGS = np.arange(1, NB)
print(f"real-X loaded: n={len(X_all)} · NF={NF} · blocks={[len(b) for b in blocks]} (P&L fields untouched)")

# standardize ภายใน block (gate จริงคำนวณ corr per-block อยู่แล้ว = scale-free)
Xb = []
for b in blocks:
    Z = X_all[b]
    Xb.append((Z - Z.mean(0)) / (Z.std(0) + 1e-12))

SCEN = ("STABLE", "MONO", "FLIP", "MIXED", "NOISE")


def betas(scen, rho, rng):
    """เลือก signal features สุ่มต่อ sim (เฉลี่ยข้าม correlation structure จริง)"""
    perm = rng.permutation(NF)
    fa, fb = perm[:NSIG], perm[NSIG:2 * NSIG]
    u = np.zeros(NF); u[fa] = 1.0
    v = np.zeros(NF); v[fb] = 1.0
    B = np.zeros((NB, NF))
    for t in range(NB):
        if scen == "STABLE":
            B[t] = rho * u
        elif scen == "MONO":
            w = t / (NB - 1)
            m = (1 - w) * u + w * v
            B[t] = rho * m / max(np.linalg.norm(m) / np.linalg.norm(u), 1e-12)
        elif scen == "FLIP":
            B[t] = rho * u * (1 if t < 3 else -1)
        elif scen == "MIXED":            # ครึ่ง stable (fa[:2]) + ครึ่ง flip (fa[2:])
            s = np.zeros(NF); s[fa[:2]] = 1.0
            f = np.zeros(NF); f[fa[2:]] = 1.0
            B[t] = rho * (s + f * (1 if t < 3 else -1))
        # NOISE: zeros
    return B


def profile(scen, rho, s):
    rng = np.random.default_rng([20260717, zlib.crc32(scen.encode()) & 0xffff, int(rho * 100), s])
    B = betas(scen, rho, rng)
    rho_hat = np.zeros((NB, NF))
    for t in range(NB):
        Z = Xb[t]
        yv = Z @ B[t]
        sig2 = max(1.0 - float(np.var(yv)), 0.05)
        y = yv + rng.standard_normal(len(Z)) * np.sqrt(sig2)
        yc = (y - y.mean()) / (y.std() + 1e-12)
        rho_hat[t] = (Z * yc[:, None]).mean(0)
    C = np.full((NB, NB), np.nan)
    for i in range(NB):
        for j in range(i + 1, NB):
            a, c = rho_hat[i], rho_hat[j]
            C[i, j] = a @ c / (np.linalg.norm(a) * np.linalg.norm(c) + 1e-12)
    lag_c = [np.nanmean(np.diagonal(C, k)) for k in LAGS]
    cbar = float(np.nanmean(C[~np.isnan(C)]))
    slope = float(np.polyfit(LAGS[:5], lag_c[:5], 1)[0])
    return cbar, slope


# ---- 1) NOISE calibration บน X จริง (threshold แบบ pre-registerable functional form) ----
noise = np.array([profile("NOISE", 0.0, s) for s in range(NSIM)])
t_bar = float(np.quantile(noise[:, 0], 0.975))
t_slope = float(np.quantile(np.abs(noise[:, 1]), 0.975))
t_flip = float(np.quantile(-noise[:, 1], 0.99))
pair_sd = float(noise[:, 0].std())
print(f"\nNOISE calib (real-X · {NSIM} sims): c̄ sd={pair_sd:.4f} (iid-19 เทียบ ~0.037) · "
      f"t_bar=q97.5(c̄)={t_bar:.4f} · t_slope=q97.5(|slope|)={t_slope:.4f} · t_flip=q99(−slope)={t_flip:.4f}")


def rule(cbar, slope):
    """(c̄, slope)-only 4-way + AMBIG→STAGE-2 — ตามที่ v3/R3 ระบุ (ไม่มี min-pair)"""
    if cbar < t_bar:
        if slope < -t_flip:
            return "FLIP"
        if abs(slope) <= t_slope:
            return "NOISE"
        return "AMBIG"
    if slope < -t_slope:
        return "MONO"
    if abs(slope) <= t_slope:
        return "STABLE"
    return "AMBIG"


TARGET = {"STABLE": "STABLE", "MONO": "MONO", "FLIP": "FLIP", "NOISE": "NOISE",
          "MIXED": None}  # MIXED ไม่มี bucket ถูกโดยนิยาม — ดูว่ามันตกไหน
for rho in (0.05, 0.10, 0.15, 0.20):
    print(f"\n===== rho={rho} (real-X · NSIG={NSIG} random features/sim) =====")
    for scen in SCEN:
        st = np.array([profile(scen, rho if scen != "NOISE" else 0.0, s) for s in range(NSIM)])
        preds = [rule(c, sl) for c, sl in st]
        from collections import Counter
        dist = Counter(preds)
        acc = dist.get(TARGET[scen], 0) / NSIM if TARGET[scen] else float("nan")
        stage2 = (dist.get("MONO", 0) + dist.get("AMBIG", 0)) / NSIM
        print(f"  {scen:<7} c̄ {st[:,0].mean():+.3f}±{st[:,0].std():.3f} · slope {st[:,1].mean():+.4f}"
              f"±{st[:,1].std():.4f} · pred {dict(dist)} · acc={acc:.2f} · →STAGE2={stage2:.2f}")
