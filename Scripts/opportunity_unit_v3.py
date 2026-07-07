#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opportunity_unit_v3.py — TRELLIS-010 v3 · Opportunity Unit v3 (measurement artifact)
FROZEN SPECIFICATION (Engineer FAIL + ChatGPT×2 + Claude Verify — สังเคราะห์ 5 คำถาม):

  Q1 NORMALIZER — ไม่ pin สมมติ · candidate ต้องผ่าน 3 เกณฑ์ (ChatGPT: ATR=candidate ไม่ใช่
     conclusion) → script เลือกเอง: (a) account-scaled median≈$5.4 (§1 min-lot R) ·
     (b) strategy-independent (ไม่ผูก param v4 · Asian-width = ตก) · (c) regime-stable
     (year-CV ต่ำ) · **daily-range (v2) ตก a (median $16.6=2.87×)**
  Q2 LABEL — realizable-MFE/R **ต่อเนื่อง** (stop-aware 1R adverse-first) · **ไม่ฝัง 2R
     threshold** (ChatGPT: 2R=success ไม่ใช่ opportunity · gradient 1.5R→2R หาย 2,570 opp) ·
     derive threshold ภายหลัง (report coverage ที่ 1/1.5/2R)
  Q3 TRIGGERABILITY — event นับเป็น "discoverable" ก็ต่อเมื่อมี **strategy-neutral trigger**
     ณ decision-time (Donchian-break / prior-day-break / range-expansion) · oracle v2 ตอบ
     "best entry" (ทุก bar = origin · line78) ไม่ใช่ "discoverable" → วัด residual-MFE จาก
     จุด trigger (ChatGPT: MFE 3R แต่ trigger มาหลัง move 90% = discoverability ต่ำ)
  Q4 COVERAGE — event-overlap จริง (v4 hold-interval [entry,exit] คร่อม [origin,reach] +
     dir ตรง) ไม่ใช่ day-level presence (Engineer F3 · overstate) · exit-bar จาก exit-locator
     (mirror walk() + assert pnl==facts = ไม่ silent-diverge)
  Q5 DIFFICULTY DECOMP — แยก **Magnitude · Triggerability · Direction** (ChatGPT) → ตอบได้ว่า
     ความยาก = "ไม่มีโอกาส" (low-mag) / "หาไม่เจอ" (mag สูง trig ต่ำ) / "เดาทิศผิด" (trig ได้
     dir-agree ต่ำ) = PnL decomp Opportunity×Direction×Execution ระดับ measurement

⚠ stop-aware + trigger = co-required (Claude แก้ ChatGPT: กรองคนละ unrealism) · oracle =
labeling instrument วัด gap **ห้ามใช้เป็น prediction target** (§9 guardrail) · field=SEARCH
cost-excluded บน magnitude (opportunity=market-structure) · trigger/coverage เป็น ex-ante
DoF pin ex-ante (ให้ Engineer review): floor=1.0R (event min = cost-clearing · ≠ success) ·
  H=360m · Donchian W=60 · range-exp k=1.0 · normalizer criteria (median 4-8 · CV report)
Usage: python opportunity_unit_v3.py
"""
import csv
import sys
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, PT, SLIP_IN, SLIP_STOP, CAPR, A, D_TRAIL

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ATR_N = 14
H = 360             # forward horizon (min)
FLOOR = 1.0         # event minimum MFE/R (cost-clearing · ไม่ใช่ success-target)
W_DON = 60          # Donchian trigger lookback (min)
K_EXP = 1.0         # range-expansion trigger: bar TR > k*R
ACCT_LO, ACCT_HI = 4.0, 8.0   # account-scale criterion ($ at min-lot · §1 median $5.43)
BIG = 10 ** 9


# ══ Q4: v4 exit-locator (mirror walk() :143-179 · trail_on,no-TS) — returns exit-bar ══
# walk() ไม่คืน exit-index · locator นี้ mirror + regression assert pnl==facts (CH-1 pattern
# · fail-loud ไม่ silent-diverge) → ได้ [entry,exit] interval สำหรับ event-overlap coverage
def v4_exit(ctx, k, d, ent, stop0, R):
    o, h, l, c, sp = ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["sp"]
    hour, day, dow = ctx["hour"], ctx["day"], ctx["dow"]
    n = len(o)
    stop, best, edy, q = stop0, ent, day[k], k + 1
    while q < n:
        if day[q] != edy:
            gap = (o[q] <= stop) if d == 1 else (o[q] >= stop)
            if gap:
                px = o[q] - SLIP_STOP * d
                ex = px if d == 1 else px + sp[q] * PT
                return q, ((ex - ent) * d if d == 1 else (ent - ex))
            ex = o[q] if d == 1 else o[q] + sp[q] * PT
            return q, ((ex - ent) if d == 1 else (ent - ex))
        hit = l[q] <= stop if d == 1 else h[q] >= stop
        if hit:
            px = (min(stop, o[q]) if d == 1 else max(stop, o[q])) - SLIP_STOP * d
            ex = px if d == 1 else px + sp[q] * PT
            return q, ((ex - ent) * d if d == 1 else (ent - ex))
        if hour[q] >= (20 if dow[q] == 5 else 23):
            ex = c[q] if d == 1 else c[q] + sp[q] * PT
            return q, ((ex - ent) if d == 1 else (ent - ex))
        best = max(best, c[q]) if d == 1 else min(best, c[q])
        fav = (best - ent) if d == 1 else (ent - best)
        if fav >= A * R:
            ns = best - D_TRAIL * R if d == 1 else best + D_TRAIL * R
            stop = max(stop, ns) if d == 1 else min(stop, ns)
        q += 1
    return n - 1, np.nan


# ══ Q2: continuous realizable-MFE per origin (stop-aware 1R adverse-first) ══
def day_events(h, l, c, R, floor=FLOOR):
    """คืน disjoint events (origin, reach, dir, mfe_R) · mfe = max favorable ก่อนโดน 1R stop
    (adverse-first → conservative) · reach = bar ที่ favorable peak · event = mfe_R ≥ floor"""
    m = len(c)
    rsk = R
    cand = []
    for d in (1, -1):
        stopped = np.zeros(m, bool)
        favmax = np.zeros(m)
        peak = np.zeros(m, np.int64)
        for dj in range(1, min(H, m)):
            idx = np.arange(m - dj)
            p = idx + dj
            act = ~stopped[idx]
            if d == 1:
                fav = h[p] - c[idx]
                adv = c[idx] - l[p]
            else:
                fav = c[idx] - l[p]
                adv = h[p] - c[idx]
            newstop = act & (adv >= rsk)               # adverse-first: bar นี้ชน stop
            upd = act & ~newstop & (fav > favmax[idx])  # credit favorable เฉพาะ bar ที่ไม่ stop
            uidx = idx[upd]
            favmax[uidx] = fav[upd]
            peak[uidx] = dj
            stopped[idx[newstop]] = True
            if stopped.all():
                break
        mfe = favmax / R
        for i in np.where(mfe >= floor)[0]:
            cand.append((int(i), int(i + peak[i]), d, float(mfe[i])))
    cand.sort(key=lambda x: x[1])                       # earliest-end greedy = max disjoint
    last, sel = -1, []
    for o, r, d, mr in cand:
        if o > last:
            sel.append((o, r, d, mr))
            last = r
    return sel


# ══ Q3: strategy-neutral trigger vocabulary (ex-ante · direction-symmetric) ══
def day_triggers(oo, hh, ll, cc, pdh, pdl, R, W=W_DON, kexp=K_EXP):
    """คืน (long_trig, short_trig, comps) per bar = OR ของ Donchian-break · prior-day-break ·
    range-expansion · strategy-neutral (ไม่ใช่ trigger ของ v4) · comps = fire-count ต่อ source
    (วินิจฉัยว่า trigger vacuous ไหม — ถ้าตัวใดยิงเกือบทุก bar = discoverability ปลอม)"""
    m = len(cc)
    lt = np.zeros(m, bool)
    st = np.zeros(m, bool)
    don = np.zeros(m, bool)
    pdr = np.zeros(m, bool)
    exp = np.zeros(m, bool)
    if m > W:                                           # Donchian: close ทะลุ prior-W extreme
        rmax = sliding_window_view(hh, W).max(1)        # window [i,i+W)
        rmin = sliding_window_view(ll, W).min(1)
        dl = cc[W:] > rmax[:m - W]
        ds = cc[W:] < rmin[:m - W]
        lt[W:] |= dl
        st[W:] |= ds
        don[W:] = dl | ds
    if pdh is not None:                                 # prior-day range break (prev TRADING day)
        pl, ps = cc > pdh, cc < pdl
        lt |= pl
        st |= ps
        pdr = pl | ps
    tr = hh - ll                                        # range expansion
    up = cc > oo
    el, es = (tr > kexp * R) & up, (tr > kexp * R) & ~up
    lt |= el
    st |= es
    exp = el | es
    return lt, st, (int(don.sum()), int(pdr.sum()), int(exp.sum()), m)


def residual_mfe(h, l, c, t, d, R):
    """realizable-MFE (R) จาก decision-time trigger bar t (entry=c[t] · 1R stop adverse-first)"""
    m = len(c)
    fav = 0.0
    for q in range(t + 1, min(t + H, m)):
        if d == 1:
            if c[t] - l[q] >= R:
                break
            fav = max(fav, h[q] - c[t])
        else:
            if h[q] - c[t] >= R:
                break
            fav = max(fav, c[t] - l[q])
    return fav / R


def main():
    ctx = load_ctx()
    day, o, h, l, c, hour = (ctx["day"], ctx["o"], ctx["h"], ctx["l"],
                             ctx["c"], ctx["hour"])
    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(h)]
    dhi = {di: float(h[i0:i1].max()) for di, i0, i1 in zip(uniq, fidx, bnd)}
    dlo = {di: float(l[i0:i1].min()) for di, i0, i1 in zip(uniq, fidx, bnd)}

    # ── Q1: build normalizer candidates (ex-ante daily R) ──
    daily_hist, hourly_hist = [], []
    cand_R = {"daily": {}, "daily_3": {}, "hourly": {}, "asian": {}}
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), bnd.tolist()):
        dts = str(np.datetime64(int(di), "D"))
        # ex-ante ATR ของ prior N วัน (คิดก่อน append วันนี้)
        Rd = float(np.mean(daily_hist[-ATR_N:])) if len(daily_hist) >= ATR_N else np.nan
        Rh = float(np.mean(hourly_hist[-ATR_N:])) if len(hourly_hist) >= ATR_N else np.nan
        # วันนี้: daily range + mean hourly range (สำหรับ append)
        drng = dhi[di] - dlo[di]
        hh, ll, hr = h[i0:i1], l[i0:i1], hour[i0:i1]
        hrs = np.unique(hr)
        mhr = float(np.mean([hh[hr == u].max() - ll[hr == u].min() for u in hrs])) if len(hrs) else np.nan
        daily_hist.append(drng)
        hourly_hist.append(mhr)
        if dts[:4] < "2012" or not np.isfinite(Rd):
            continue
        cand_R["daily"][dts] = Rd
        cand_R["daily_3"][dts] = Rd / 3.0
        cand_R["hourly"][dts] = Rh
        aw = ctx["lv"].get(dts)
        cand_R["asian"][dts] = (aw[0] - aw[1]) if aw else np.nan

    print("=== Opportunity Unit v3 · FROZEN SPEC · field=SEARCH ===")
    print("\n[Q1] NORMALIZER SELECTION (ChatGPT: candidate ต้องผ่าน 3 เกณฑ์ · script เลือก):")
    print(f"  {'candidate':<10}{'median$':>9}{'mean$':>8}{'yearCV':>8}  {'acct-scale':>11}"
          f"{'strat-indep':>12}  verdict")
    indep = {"daily": True, "daily_3": True, "hourly": True, "asian": False}
    stats = {}
    for name, dR in cand_R.items():
        vals = np.array([v for v in dR.values() if np.isfinite(v)])
        med, mean = float(np.median(vals)), float(vals.mean())
        yr = {}
        for dts, v in dR.items():
            if np.isfinite(v):
                yr.setdefault(dts[:4], []).append(v)
        ymed = np.array([np.median(vs) for vs in yr.values()])
        cv = float(ymed.std() / ymed.mean())
        acct = ACCT_LO <= med <= ACCT_HI
        ok = acct and indep[name]
        stats[name] = dict(med=med, cv=cv, acct=acct, indep=indep[name], ok=ok)
        print(f"  {name:<10}{med:>9.2f}{mean:>8.2f}{cv:>8.3f}  {'PASS' if acct else 'FAIL':>11}"
              f"{'yes' if indep[name] else 'NO':>12}  {'eligible' if ok else '—'}")
    eligible = {n: s for n, s in stats.items() if s["ok"]}
    winner = min(eligible, key=lambda n: eligible[n]["cv"]) if eligible else None
    print(f"  → eligible (acct-scale ∧ strat-indep) = {list(eligible)} · "
          f"SELECT min-CV = **{winner}** (regime-stable ที่สุด)")
    if winner is None:
        print("  ⚠ ไม่มี candidate ผ่าน — ต้องขยาย vocabulary")
        return

    # ── Q2/Q3/Q5: events + triggerability + difficulty บน normalizer ที่เลือก ──
    Rsel = cand_R[winner]
    v4 = {dts: (int(f["dir"]), f["entry_time"]) for dts, f in ctx["facts"].items()
          if f["traded"] == "1"}
    hold = {}                                           # date -> (entry_bar, exit_bar, dir)
    mism = 0
    for dts, (d, et) in v4.items():
        k = ctx["pos"][dts + "T" + et]
        ash, asl = ctx["lv"][dts]
        R = ash - asl
        ent = (o[k] + ctx["sp"][k] * PT + SLIP_IN) if d == 1 else (o[k] - SLIP_IN)
        stop0 = max(asl, ent - CAPR * R) if d == 1 else min(ash, ent + CAPR * R)
        xb, pnl = v4_exit(ctx, k, d, ent, stop0, R)
        if not (np.isfinite(pnl) and abs(pnl - float(ctx["facts"][dts]["pnl"])) < 2e-3):
            mism += 1
        hold[dts] = (k, xb, d)
    assert mism == 0, f"exit-locator FAIL: {mism} ไม้ pnl≠facts (silent-diverge จาก walk)"
    print(f"\n[Q4] exit-locator regression: pnl==facts.pnl {len(hold)}/{len(hold)} ✓ "
          f"(mirror walk() · no silent-diverge)")

    events = []
    trig_ct = [0, 0, 0, 0]                              # Donchian, prior-day, range-exp, bars
    uniq_l, fidx_l, bnd_l = uniq.tolist(), fidx.tolist(), bnd.tolist()
    for j, (di, i0, i1) in enumerate(zip(uniq_l, fidx_l, bnd_l)):
        dts = str(np.datetime64(int(di), "D"))
        if dts not in Rsel or not np.isfinite(Rsel[dts]) or Rsel[dts] <= 0:
            continue
        R = Rsel[dts]
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22)
        gi = np.arange(i0, i1)[m]
        oo, hh, ll, cc = o[gi], h[gi], l[gi], c[gi]
        if len(cc) < 30:
            continue
        prev_di = uniq_l[j - 1] if j > 0 else None       # previous TRADING day (ไม่ใช่ calendar−1)
        pdh = dhi.get(prev_di) if prev_di is not None else None
        pdl = dlo.get(prev_di) if prev_di is not None else None
        sel = day_events(hh, ll, cc, R)
        if not sel:
            continue
        lt, st, comps = day_triggers(oo, hh, ll, cc, pdh, pdl, R)
        for z in range(4):
            trig_ct[z] += comps[z]
        eb, xb, vdir = hold.get(dts, (None, None, 0))
        for org, rch, d, mr in sel:
            # Q3 triggerability: earliest same-dir trigger ใน [org, rch]
            tsig = lt if d == 1 else st
            tw = np.where(tsig[org:rch + 1])[0]
            if len(tw):
                t = org + int(tw[0])
                resid = residual_mfe(hh, ll, cc, t, d, R)
                lag = t - org
                trigd = True
            else:
                t, resid, lag, trigd = -1, 0.0, -1, False
            # Q5 direction: earliest trigger (any dir) ใน [org,rch] → ชี้ทิศถูกไหม
            anyt = np.where((lt | st)[org:rch + 1])[0]
            if len(anyt):
                ta = org + int(anyt[0])
                tdir = 1 if lt[ta] and not st[ta] else (-1 if st[ta] and not lt[ta] else 0)
                dir_agree = (tdir == d) if tdir != 0 else None   # 0 = ambiguous (both)
            else:
                dir_agree = None
            # Q4 coverage: v4 hold-interval overlap + dir
            covered = (vdir == d and eb is not None
                       and eb <= gi[rch] and xb >= gi[org])
            events.append(dict(
                date=dts, yr=dts[:4], dir=d, mfe=mr,
                trigd=trigd, resid=resid, discover=(resid / mr if mr > 0 else 0.0),
                lag=lag, dir_agree=dir_agree, covered=covered))

    ev = events
    n = len(ev)
    mfe = np.array([e["mfe"] for e in ev])
    print(f"\n[Q2] MAGNITUDE — realizable-MFE/R distribution (normalizer={winner} · n={n} events):")
    print(f"  median={np.median(mfe):.2f}R p75={np.percentile(mfe,75):.2f}R "
          f"p90={np.percentile(mfe,90):.2f}R max={mfe.max():.2f}R")
    for thr in (1.0, 1.5, 2.0, 3.0):
        print(f"    ≥{thr:.1f}R: {int((mfe>=thr).sum()):>5} events "
              f"({100*(mfe>=thr).mean():.0f}%)  ← threshold = derived post-hoc ไม่ฝังใน def")

    trigd = np.array([e["trigd"] for e in ev])
    disc = np.array([e["discover"] for e in ev])
    print(f"\n[Q3] TRIGGERABILITY — discoverable ด้วย strategy-neutral trigger?:")
    bars_t = max(trig_ct[3], 1)
    print(f"  per-trigger fire-rate (self-diagnostic · vacuous ถ้าใกล้ 100%): "
          f"Donchian{W_DON}={100*trig_ct[0]/bars_t:.1f}% prior-day={100*trig_ct[1]/bars_t:.1f}% "
          f"range-exp={100*trig_ct[2]/bars_t:.1f}% ของ bars")
    print(f"  triggered (มี same-dir trigger ใน [origin,reach]) = {int(trigd.sum())}/{n} "
          f"= {100*trigd.mean():.0f}%")
    dt = disc[trigd]
    print(f"  discoverability = residual-MFE/full-MFE (จาก trigger): median={np.median(dt):.2f} "
          f"→ {100*(dt>=0.5).mean():.0f}% ยังเหลือ ≥50% ของ move ตอน detect ได้")
    lags = np.array([e["lag"] for e in ev if e["trigd"]])
    print(f"  trigger lag (bars origin→trigger): median={int(np.median(lags))}m "
          f"(สูง = trigger มาช้า = discoverability ต่ำ)")

    print(f"\n[Q5] DIFFICULTY DECOMPOSITION — ความยากอยู่ที่ไหน (3 แกนแยกกัน):")
    hi = mfe >= 1.5                                     # opportunity ที่คุ้มค่า
    not_trig = hi & ~trigd
    trig_hi = hi & trigd
    da = np.array([1 if e["dir_agree"] else (0 if e["dir_agree"] is False else -1) for e in ev])
    agree = trig_hi & (da == 1)
    disag = trig_hi & (da == 0)
    print(f"  บน opp คุ้มค่า (MFE≥1.5R · n={int(hi.sum())}):")
    print(f"    · 'ไม่มีโอกาส'  = low-mag population (MFE<1.5R) = {int((~hi).sum())}/{n}")
    print(f"    · 'หาไม่เจอ'    = MFE≥1.5R แต่ไม่ triggerable = {int(not_trig.sum())} "
          f"({100*not_trig.sum()/max(hi.sum(),1):.0f}% ของ opp คุ้มค่า)")
    print(f"    · 'เดาทิศผิด'   = triggerable แต่ trigger ชี้ผิดทิศ = {int(disag.sum())} "
          f"vs ชี้ถูก {int(agree.sum())} "
          f"(dir-accuracy={100*agree.sum()/max(agree.sum()+disag.sum(),1):.0f}%)")

    cov = np.array([e["covered"] for e in ev])
    print(f"\n[Q4] COVERAGE (event-overlap จริง · additive population):")
    print(f"  v4 covered (hold-interval คร่อม + dir ตรง) = {int(cov.sum())}/{n} = "
          f"{100*cov.mean():.0f}%")
    gap_hi = hi & ~cov & trigd
    print(f"  ADDITIVE GAP (MFE≥1.5R ∧ triggerable ∧ v4-ไม่ covered) = {int(gap_hi.sum())} "
          f"= population ของ direction-predictor (discoverable + คุ้มค่า + v4 พลาด)")
    print(f"\n  per-year (event ∧ additive-gap MFE≥1.5R triggerable):")
    for y in range(2012, 2021):
        ym = np.array([e["yr"] == str(y) for e in ev])
        if ym.any():
            print(f"    {y}: events={int(ym.sum()):>4} · gap={int((ym & gap_hi).sum()):>3}")

    print(f"\n⚠ v3 = measurement artifact (freeze ก่อน predictor) · oracle=labeling ห้าม train เป็น target ·"
          f" cost-excluded บน magnitude · trigger vocabulary = {['Donchian'+str(W_DON),'prior-day','range-exp']} "
          f"(กว้าง strategy-neutral · ถ้าแคบไป → หาไม่เจอ overstated · Engineer review)")


if __name__ == "__main__":
    main()
