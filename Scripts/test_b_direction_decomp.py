#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_b_direction_decomp.py — TRELLIS-010 v3 · Test B: DIRECTION decomposition ที่ EXIT จริงของ engine
คำถามวิจัย (ไม่ใช่ Stage-F gate): กำไร v4 (+532.8 บน 2012-2020) มาจาก **DIRECTION-skill** หรือ
**convex-exit × magnitude**? · "direction ตาย" (OHLC 1/19, tickvol 0/7, spread dead) เป็น label-specific
ของ `trade_R` (1R-stop/1.5R-target · intraday-EOD) ไหม — พอเปลี่ยนเป็น exit จริง (trailing arm 1×R /
dist 1×R + overnight) direction-rule ของ v4 มี skill ขึ้นมาไหม?

design (Engineer PASS · 5 review รอบ + Claude deep-verify):
- REUSE `walk()` ตรง (brain_v1_run:130-180 · canonical · ts_on=False = v4 trail-only) — ไม่ clone/refactor
- ต่อ signal จริงของ v4 (mirror dual_rows:196-198): 3 legs ผ่าน walk() ทั้งสองทิศ
    current  = walk(k, d,  ent_real, stop0_real, R)[0]     (reproduce facts.pnl · regression-assert)
    opposite = walk(k, -d, ent_opp,  stop_mirror, R)[0]    (DISTANCE-PRESERVING mirror: stop_opp =
               ent_opp − (−d)·Dl · Dl=|ent_real−stop0_real| ≤ CAPR·R · cap ติดมา · ไม่ ash-anchor)
    floor = mean(cur,opp) [no-skill] · ceiling = max(cur,opp) [oracle UB]
- readout (ทั้งหมด · honest): current−floor = v4 direction-rule skill (magnitude-weighted) ที่ exit จริง
    · ceiling−current = oracle regret (UB · oracle-biased) · per-year + day-clustered CI
- INTEGRITY: (a) reproduce-first current==facts.pnl (assert · dual_rows:202 pattern)
    (b) MIRROR-SYMMETRY property test (sp=0 · h↔l swap → long_pnl==short_pnl · discharge d-symmetry)
- ⚠ FIELD TAG: 2012-2020 **SEARCH** (v4 +532.8) · money-span 2023-26 = **LOCKBOX (ไม่วัด)** · partly
    WF-selected → in-field **mechanism decomposition** ไม่ใช่ fresh OOS · OOS จริง = forward-test เท่านั้น
Usage: python test_b_direction_decomp.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, walk, PT, SLIP_IN, SLIP_STOP, CAPR, A, D_TRAIL, TS_MIN, BASE_P
from direction_predictor import day_ci

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def _mk_ctx(o, h, l, c):
    """synthetic minimal ctx สำหรับ property test (1 วัน · hour 10 · dow จันทร์ · sp=0)"""
    n = len(o)
    return dict(o=np.array(o, float), h=np.array(h, float), l=np.array(l, float),
                c=np.array(c, float), sp=np.zeros(n),
                tmin=np.arange(n, dtype=np.int64) + 600, hour=np.full(n, 10),
                day=np.zeros(n, int), dow=np.zeros(n, int))


def property_test_mirror_symmetry():
    """Engineer Q3: sp=0 + reflect path about entry E (h↔l swap) + stop_short=2E−stop_long
    → walk(long) == walk(short) · discharge opposite-leg d-symmetry assumption"""
    E, R = 100.0, 1.0
    Dl = CAPR * R                                            # =1.0
    # long path (idx0=entry bar dummy · walk เริ่ม q=1) — arm trail ที่ bar2 · stop-hit bar3
    o = [100.0, 100.5, 100.5, 100.5]
    h = [100.0, 100.6, 101.3, 100.3]
    l = [100.0, 100.0, 100.8, 100.1]
    c = [100.0, 100.5, 101.2, 100.2]
    pnlL = walk(_mk_ctx(o, h, l, c), 0, 1, E, E - Dl, R)[0]
    # reflect about E: o'=2E−o · c'=2E−c · h'=2E−l · l'=2E−h (swap high/low)
    o2 = [2 * E - x for x in o]; c2 = [2 * E - x for x in c]
    h2 = [2 * E - x for x in l]; l2 = [2 * E - x for x in h]
    pnlS = walk(_mk_ctx(o2, h2, l2, c2), 0, -1, E, E + Dl, R)[0]
    ok = np.isfinite(pnlL) and np.isfinite(pnlS) and abs(pnlL - pnlS) < 1e-9
    print(f"[PROPERTY TEST · mirror-symmetry sp=0] long={pnlL:+.6f} short={pnlS:+.6f} "
          f"|Δ|={abs(pnlL - pnlS):.2e} → {'PASS' if ok else 'FAIL'}")
    assert ok, f"d-symmetry FAIL: long {pnlL} != short {pnlS} — opposite-leg ไม่ valid"


def main():
    property_test_mirror_symmetry()
    ctx = load_ctx()

    yrs, cur_a, opp_a = [], [], []
    mism, skip = 0, 0
    for dts, f in sorted(ctx["facts"].items()):
        if f["traded"] != "1":
            continue
        k = ctx["pos"][dts + "T" + f["entry_time"]]
        d = int(f["dir"])
        ash, asl = ctx["lv"][dts]
        R = ash - asl
        # current leg = v4 จริง (mirror dual_rows:196-198) → ต้อง == facts.pnl
        ent = (ctx["o"][k] + ctx["sp"][k] * PT + SLIP_IN) if d == 1 else (ctx["o"][k] - SLIP_IN)
        stop0 = max(asl, ent - CAPR * R) if d == 1 else min(ash, ent + CAPR * R)
        cur = walk(ctx, k, d, ent, stop0, R)[0]
        if not (np.isfinite(cur) and abs(cur - float(f["pnl"])) < 2e-3):
            mism += 1
        # opposite leg = ทิศตรงข้าม · distance-preserving mirror stop
        do = -d
        ento = (ctx["o"][k] + ctx["sp"][k] * PT + SLIP_IN) if do == 1 else (ctx["o"][k] - SLIP_IN)
        Dl = abs(ent - stop0)                                # ≤ CAPR·R (cap ติดมาจาก max/min)
        stopo = ento - do * Dl                               # do=1→below · do=−1→above
        opp = walk(ctx, k, do, ento, stopo, R)[0]
        if not np.isfinite(opp):
            skip += 1
            continue
        yrs.append(dts[:4]); cur_a.append(cur); opp_a.append(opp)

    assert mism == 0, f"reproduce-first FAIL: {mism} ไม้ current≠facts.pnl (silent-diverge)"
    yrs = np.array(yrs); cur = np.array(cur_a); opp = np.array(opp_a)
    floor = (cur + opp) / 2.0
    ceil = np.maximum(cur, opp)
    cf = cur - floor                                         # = (cur−opp)/2 = direction-rule skill
    rc = ceil - cur                                          # oracle regret (UB)
    days = np.arange(len(cur))                               # v4 = 1 เทรด/วัน → trade=day (block unit)
    rng = np.random.default_rng(20260708)

    print(f"\n=== Test B · DIRECTION decomposition ที่ exit จริง v4 (walk · trailing+overnight) ===")
    print(f"FIELD = 2012-2020 SEARCH · n_trades={len(cur)} · reproduce current==facts.pnl ✓ "
          f"(skip nan opp={skip}) · ⚠ money-span 2023-26 = LOCKBOX (ไม่วัด)")
    print(f"  reproduce-first: Σcurrent={cur.sum():+.1f} vs BASE_P={BASE_P:+.1f} "
          f"({'✓ ตรง' if abs(cur.sum() - BASE_P) < 0.5 else '⚠ ห่าง'})")

    def line(nm, v):
        lo, hi = day_ci(v, days, rng)
        return f"  {nm:<34}{v.sum():>+10.1f}{v.mean():>+9.3f}{f'[{lo:+.3f},{hi:+.3f}]':>22}{'  ✓CI>0' if lo > 0 else ('  ✗CI<0' if hi < 0 else '')}"

    print(f"\n  {'leg / metric':<34}{'ΣPnL':>10}{'/ไม้':>9}{'95%CI(day-clust /ไม้)':>22}")
    print(f"  {'floor = mean(long,short) [no-skill]':<34}{floor.sum():>+10.1f}{floor.mean():>+9.3f}")
    print(f"  {'current = v4 direction-rule':<34}{cur.sum():>+10.1f}{cur.mean():>+9.3f}")
    print(f"  {'ceiling = max(long,short) [oracle UB]':<34}{ceil.sum():>+10.1f}{ceil.mean():>+9.3f}")
    print(line("current − floor  (DIRECTION skill)", cf))
    print(line("ceiling − current (oracle regret UB)", rc))
    print(f"  WR(current>opp) = {100 * (cur > opp).mean():.1f}%  ·  WR(current>0) = {100 * (cur > 0).mean():.1f}%")

    print(f"\n  [PER-YEAR]  {'yr':<6}{'n':>5}{'floor':>9}{'current':>9}{'ceiling':>9}{'cur−floor':>11}")
    for y in sorted(set(yrs.tolist())):
        s = yrs == y
        print(f"  {'':<6}{y:<6}{int(s.sum()):>5}{floor[s].sum():>+9.1f}{cur[s].sum():>+9.1f}"
              f"{ceil[s].sum():>+9.1f}{cf[s].sum():>+11.1f}")

    lo, hi = day_ci(cf, days, rng)
    print(f"\n[READOUT · honest · in-field mechanism decomposition ไม่ใช่ OOS]")
    verdict = ("DIRECTION-rule ของ v4 มี skill ที่ exit จริง (cur−floor>0 CI-clean) → 'direction ตาย' "
               "= label-specific ของ trade_R") if lo > 0 else \
              ("แม้ exit จริง direction-rule ก็ไม่ชนะ coin-flip (cur−floor CI คร่อม/ต่ำ 0) → direction "
               "ตายจริงเหนือ label · กำไร v4 = convex-exit×magnitude") if hi < 0 or lo <= 0 else "inconclusive"
    print(f"  cur−floor = {cf.mean():+.3f}/ไม้ CI[{lo:+.3f},{hi:+.3f}] → {verdict}")
    print(f"  ⚠ SEARCH 2012-2020 · partly WF-selected · regime-transfer ไป 2023-26 ไม่รับประกัน · "
          f"OOS จริง = forward-test (ไม่ใช่ script นี้)")


if __name__ == "__main__":
    main()
