

def main():
    import sys as _sys
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    import numpy as np
    # Card §7(5) pin (round-12): log s_i = a_i + ln L_year + ln r_k
    #   a_i = phi a_{i-1} + sqrt(1-phi^2) eta_i ; eta = t(5)/sqrt(5/3) ; a_0 ~ N(0,1)
    #   r_k = 1 + k/(n_te-1), k=0..n_te-1 (per test year, reset)
    #   L_year in (1.0,1.15,1.3,1.45,1.6)
    NTE=[155,174,160,158,163]; PREF=[114,129,120,117,120]; PHI=.97; DF=5
    L=(1.0,1.15,1.3,1.45,1.6)
    def world(rng, use_L=True):
        n=sum(NTE); a=np.empty(n); a[0]=rng.standard_normal()
        eta=rng.standard_t(DF,size=n)/np.sqrt(DF/(DF-2))
        for i in range(1,n): a[i]=PHI*a[i-1]+np.sqrt(1-PHI**2)*eta[i]
        logr=np.concatenate([np.log(1+np.arange(m)/(m-1)) for m in NTE])
        logL=np.concatenate([np.full(m,np.log(L[j] if use_L else 1.0)) for j,m in enumerate(NTE)])
        return a+logL+logr, a
    def run(use_L, B=3000, seed=20260907):
        rng=np.random.default_rng(seed)
        sd=[];rat=[];rs=[];rsA=[];mx=[]
        contrast=[1+(3*(m//4)-1)/(m-1) for m in NTE]
        lnc=float(np.mean(np.log(contrast)))
        for _ in range(B):
            ls,a=world(rng,use_L); s=np.exp(ls)
            sd.append(ls.std(ddof=1)); rat.append(s.max()/np.median(s)); mx.append((np.abs(s).max()/s.sum()))
            rs.append(lnc/ls.std(ddof=1)); rsA.append(lnc/a.std(ddof=1))
        f=lambda v:(np.mean(v),np.percentile(v,5),np.percentile(v,50),np.percentile(v,95))
        print(f"use_L={use_L}  ln(contrast) mean={lnc:.4f}  (per fold {[round(np.log(c),4) for c in contrast]})")
        print("  sd(log sigma)   mean/p5/p50/p95 = %.3f %.3f %.3f %.3f"%f(sd))
        print("  sigma_max/med   mean/p5/p50/p95 = %.1f %.1f %.1f %.1f"%f(rat))
        print("  max share Sum s mean/p50/p95     = %.3f %.3f %.3f"%(np.mean(mx),np.median(mx),np.percentile(mx,95)))
        print("  ramp-share (/sd log sigma) mean/p5/p50/p95 = %.3f %.3f %.3f %.3f"%f(rs))
        print("  ramp-share (/sd a only)    mean/p50 = %.3f %.3f"%(np.mean(rsA),np.median(rsA)))
        print("  P(ramp-share>=0.5) = %.3f"%np.mean(np.array(rs)>=0.5))
    run(True); print(); run(False)



if __name__ == "__main__":
    main()
