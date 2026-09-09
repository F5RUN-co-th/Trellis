# -*- coding: utf-8 -*-
"""ENG11: geometry ของ sigma-domain ตาม card §7(5) (apply rob 10) — arithmetic only, no data, no P&L.
prefix = 3q per fold (measured [114,129,120,117,120] -> q=[38,43,40,39,40])
n_fold = prefix + Q4 ; estimand Q2-Q4 = n - q = [117,131,120,119,123] (card §1)

SUPERSEDED READING [F12 รอบ 19] — geometry ของ 810-row ramp (apply รอบ 10) · contrast ×1.08-1.14 ที่พิมพ์ = ⟪RETIRED⟫ ใน card (รอบ 11 ramp อ่อน → Alt-A per-year ramp ×1.73-1.75 = r13_sigma.py) · คงไว้เพื่อ reproduce เลขที่ถูกถอนใน changelog รอบ 10-13 เท่านั้น · ห้ามใช้เป็นค่า operative
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")   # F23-2 รอบ 23: reconfigure ก่อน emit ตัวแรก (invariant ของสคริปต์ชุด reproduce)
except Exception:
    pass


def main():
    print("[SUPERSEDED READING — ดู docstring · ค่า operative = r13_sigma.py]")
    import sys as _sys
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    pref = [114,129,120,117,120]
    est  = [117,131,120,119,123]
    q    = [p//3 for p in pref]
    n    = [e + qq for e,qq in zip(est,q)]
    print("q        =", q)
    print("n_fold   =", n, " sum =", sum(n))
    print("prefix   =", pref, " sum =", sum(pref))
    print("Q4       =", [nn-p for nn,p in zip(n,pref)])
    N = sum(n)
    print(f"\nsigma domain = {N} rows, ramp linear x1 -> x2 (slope = 1/{N-1} per row)")
    off = 0
    tot_lo = tot_hi = None
    for i,(nn,p) in enumerate(zip(n,pref)):
        lo = 1 + off/(N-1); hi = 1 + (off+p-1)/(N-1)
        q4lo = 1 + (off+p)/(N-1); q4hi = 1 + (off+nn-1)/(N-1)
        print(f"  fold{2016+i}: prefix rows [{off},{off+p-1}]  ramp {lo:.4f} -> {hi:.4f}  contrast x{hi/lo:.4f}"
              f"   | Q4 ramp {q4lo:.4f} -> {q4hi:.4f}")
        off += nn
    print("\n[superseded reading] ramp x1->x2 WITHIN each prefix  -> contrast x2.0000 per fold")
    print("[round-10 reading  ] contrast per prefix = x1.08 - x1.14  (ratio of the two readings: "
          f"{2.0/ (1+ (pref[0]-1)/(N-1)):.2f}x weaker at fold2016)")

    # variance-share view: local SNR = rho^2/(rho^2+sigma^2), rho=0.10
    rho=0.10
    for i,(nn,p) in enumerate(zip(n,pref)):
        off2 = sum(n[:i])
        lo = 1 + off2/(N-1); hi = 1 + (off2+p-1)/(N-1)
        s_lo, s_hi = rho**2/(rho**2+lo**2), rho**2/(rho**2+hi**2)
        print(f"  fold{2016+i}: local SNR head {s_lo:.5f} -> tail {s_hi:.5f}   ratio {s_lo/s_hi:.4f}")



if __name__ == "__main__":
    main()
