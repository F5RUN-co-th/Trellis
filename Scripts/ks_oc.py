# -*- coding: utf-8 -*-
"""SUPERSEDED READING [E1 รอบ 21] — KS+ threshold/OC ด้วย float path (F_emp − x) · ให้ P(KS+ > t) = 4.856% ≠ integer-lattice 4.74%
(atom P(KS+ = t) ≈ 1.29% ตกบน threshold · ผลต่างมาจาก float dust) · authority เดียว = eng16_ks.py (integer-lattice convention · N2)
คงไว้เพื่อ reproduce เลขที่เคยอ้างในประวัติเท่านั้น · ห้ามใช้เป็นค่า operative
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")   # F23-2 รอบ 23: reconfigure ก่อน emit ตัวแรก (invariant ของสคริปต์ชุด reproduce)
except Exception:
    pass


def main():
    print("[SUPERSEDED READING — float convention · authority = eng16_ks.py]")
    import sys as _sys
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    import numpy as np

    # ---------- (A) KS+ lattice-min threshold, N=400, null = discrete-Uniform{.01..1.00}
    def ksplus_mc(N, B, seed):
        rng = np.random.default_rng(seed)
        grid = np.arange(1,101)               # p*100
        out = np.empty(B)
        for chunk0 in range(0, B, 20000):
            b = min(20000, B-chunk0)
            s = rng.integers(1,101,size=(b,N))         # p in units of 1/100
            # F_emp(x) at x=k/100  -> count(s<=k)/N ; KS+ = max_k (count/N - k/100)
            cnt = np.zeros((b,100))
            for k in range(1,101):
                cnt[:,k-1] = (s<=k).sum(1)
            F = cnt/N
            out[chunk0:chunk0+b] = (F - grid/100.0).max(1)
        return out

    ks = ksplus_mc(400, 200000, 20260903)
    lat = np.round(ks*400).astype(int)   # lattice units of 1/400
    print("KS+ dist: min",ks.min(),"max",ks.max())
    for t_units in range(18, 30):
        t = t_units/400
        p_exceed = (ks > t).mean()
        print(f"  t={t:.4f} ({t_units}/400)  P(KS+ > t) = {p_exceed*100:.3f}%")



if __name__ == "__main__":
    main()
