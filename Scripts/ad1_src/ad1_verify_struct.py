"""AD-1 Claude-Verify — structural numbers (P&L-free · ไม่แตะ payoff/pnl ใดๆ)
reproduce อิสระ: fold table ของ Engineer + rolling-300 composition + decay H=480 N_eff/weight-share
"""
import sys, collections
import numpy as np

sys.path.insert(0, r"D:\workspace\Doc\T.me\R&D\Trellis\Scripts")
from brain_v1_run import load_ctx
from direction_at_real_exit import build_rows, TEST_YEARS

ctx = load_ctx()
rows = build_rows(ctx)
yr = np.array([r["yr"] for r in rows])
dayix = np.array([r["dayix"] for r in rows])
Nemb = max(r["hold"] for r in rows)
assert (np.diff(dayix) >= 0).all(), "rows not time-sorted — last-K by index invalid"
print(f"n={len(rows)} Nemb={Nemb}d sorted=True")
print("trades/yr:", dict(sorted(collections.Counter(yr).items())))

lam = np.exp(-np.log(2) / 480)  # exp-decay half-life 480 trades
print(f"\n{'Y':<6}{'test_n':>7}{'expand':>8}{'roll300: yr-mix':>34}{'preflip%':>10}"
      f"{'dNeff':>7}{'d_pre15_w%':>11}{'d_oldest_w':>11}")
for Y in TEST_YEARS:
    te = yr == Y
    tr = np.array([int(y) < int(Y) for y in yr]) & (dayix < dayix[te].min() - Nemb)
    idx = np.where(tr)[0]
    last300 = idx[-300:]
    comp = dict(sorted(collections.Counter(yr[last300]).items()))
    pre15_roll = sum(v for k, v in comp.items() if int(k) < 2015) / 300.0
    k = np.arange(len(idx))[::-1].astype(float)      # lag: ใหม่สุด=0
    w = lam ** k
    neff = w.sum() ** 2 / (w * w).sum()
    pre15 = np.array([int(y) < 2015 for y in yr[idx]])
    print(f"{Y:<6}{te.sum():>7}{tr.sum():>8}{str(comp):>34}{pre15_roll*100:>9.1f}%"
          f"{neff:>7.0f}{w[pre15].sum()/w.sum()*100:>10.1f}%{w[0]:>11.3f}")

# min_child_samples ตามสูตร :193
print("\nGBM min_child_samples = max(20, n//20):")
for n in [300, 509, 675, 831, 1003, 1163, 1321]:
    print(f"  n={n}: {max(20, n // 20)}")

# fit_signedR weight=1 equivalence: /n vs /rw.sum() — พิสูจน์พีชคณิต + numeric
rng = np.random.default_rng(7)
X = rng.normal(size=(50, 4)); d = rng.normal(size=50)
p = 1 / (1 + np.exp(-X @ np.ones(4) * 0.1))
g_orig = X.T @ (d * p * (1 - p)) / len(d)
rw = np.ones(50)
g_w = X.T @ (rw * d * p * (1 - p)) / rw.sum()
print(f"\nfit_signedR weighted(rw=1) grad max|diff| = {np.abs(g_orig - g_w).max():.2e} (ต้อง 0 เป๊ะ)")
