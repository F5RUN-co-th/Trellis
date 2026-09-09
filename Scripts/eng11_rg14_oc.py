# -*- coding: utf-8 -*-
"""ENG11 (synthetic · toy-moment MC · no real data · no P&L):
OC ของ RG14 ตามถ้อยคำ apply รอบ 10 = 'raise เฉพาะเมื่อ CI 95% ของ paired mean ตัดทิศตรงข้าม (upper<0)'
moments = eng10/cv10_rg14.txt (rho=.1 N_worlds=200 B0=99, seed 23) — synthetic toy-field
"""


def main():
    import sys as _sys
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    import numpy as np
    from scipy import stats

    M = {"d_sd": (0.00215, 0.00228, 0.815), "d_q95": (0.00354, 0.00782, 0.690)}
    B = 200000
    rng = np.random.default_rng(20260907)

    def oc(mean, sd, W, crit, mirror=False):
        mu = -mean if mirror else mean
        x = rng.normal(mu, sd, size=(B, W))
        m = x.mean(1); s = x.std(1, ddof=1)/np.sqrt(W)
        return (m + crit*s < 0), m

    print("== RG14 raise-rule OC (Normal approx ของ world-level diffs · toy moments) ==")
    for W in (10, 20, 35, 50):
        tc = stats.t.ppf(0.975, W-1); zc = 1.959964
        row = [f"W={W:3d}"]
        flags = {}
        for k,(mn,sd,_) in M.items():
            for name, crit in (("t", tc), ("z", zc)):
                ft,_ = oc(mn, sd, W, crit, mirror=False)
                pw,_ = oc(mn, sd, W, crit, mirror=True)
                flags[(k,name)] = (ft, pw)
                row.append(f"{k}/{name}: false-trip {100*ft.mean():.3f}%  power(mirror) {100*pw.mean():.1f}%")
        print("  " + "\n       ".join(row))
        # joint: EITHER vs BOTH (independence approx across the two stats is FALSE; use same-sample coupling)
        x1 = rng.normal(M['d_sd'][0], M['d_sd'][1], size=(B,W)); x2 = rng.normal(M['d_q95'][0], M['d_q95'][1], size=(B,W))
        def flag(x, crit):
            m=x.mean(1); s=x.std(1,ddof=1)/np.sqrt(W); return m+crit*s<0
        f1,f2 = flag(x1,tc), flag(x2,tc)
        y1 = rng.normal(-M['d_sd'][0], M['d_sd'][1], size=(B,W)); y2 = rng.normal(-M['d_q95'][0], M['d_q95'][1], size=(B,W))
        g1,g2 = flag(y1,tc), flag(y2,tc)
        print(f"       EITHER(t): false-trip {100*(f1|f2).mean():.3f}%  power {100*(g1|g2).mean():.1f}%   "
              f"BOTH(t): false-trip {100*(f1&f2).mean():.4f}%  power {100*(g1&g2).mean():.1f}%")

    print("\n== 'power >=99%' ที่ card ประกาศ = P(point paired mean > 0)? ==")
    for k,(mn,sd,_) in M.items():
        for W in (7,10,20,26,27,35):
            z = mn/(sd/np.sqrt(W))
            print(f"  {k:6s} W={W:3d}: mean/SE={z:5.3f}  P(point mean>0)={100*stats.norm.cdf(z):6.2f}%  "
                  f"P(CI upper<0 | mirror, t)={100*oc(mn,sd,W,stats.t.ppf(.975,W-1),mirror=True)[0].mean():5.1f}%")



if __name__ == "__main__":
    main()
