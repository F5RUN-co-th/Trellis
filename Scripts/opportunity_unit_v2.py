#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opportunity_unit_v2.py — TRELLIS-010 v3 · Opportunity Reference Set v2
(trigger-constrained + event-level) — แก้ 2 caveat ของ v1 (§9) ก่อน direction-predictor:
  (1) small-n: v1 unit=วัน 1 opp/ทิศ (n=31 missed∧opp) → v2 = **event-level**
      (หลาย opp/วัน · disjoint interval-scheduling) → population ใหญ่พอเป็น "signal"
  (2) hindsight: v1 oracle = geometric best-swing max(drawup,drawdown) — นับ range ที่
      1R-stop จะโดนเขี่ยทิ้งก่อนถึง target (inflate) → v2 = **STOP-AWARE realizable**:
      จาก origin (entry=close) วาง 1R stop · นับเป็น opp ก็ต่อเมื่อแตะ TARGET·R **ก่อน**
      โดน 1R stop โดยใช้ adverse-first ภายใน bar (worst-case ordering = conservative
      → นับ opp น้อยกว่า geometric = realizability LOWER bound)

3 วัตถุ (คงนิยาม §6 · v1):
  · UNIT (ex-ante decision granularity) = origin bar ใด ๆ ใน session (event-level)
  · LABEL (ex-post) = realizable-R + dir · **realizable = ผ่านด่าน 1R stop** ไม่ใช่ geometric
  · R (ex-ante) = ATR14 prior-day range (รู้ ณ session open · = v1/discovery) · TARGET=2.0R

⚠ ยังเหลือ hindsight 1 ชั้น (ตั้งใจ · honest): oracle "เลือก origin bar ถูก" ได้ =
UPPER bound → oracle นี้ = **labeling instrument** วัด coverage-gap เท่านั้น ห้ามใช้เป็น
prediction target (§9 guardrail) · ปิด hindsight ชั้นนี้ = ex-ante predictor (step ถัดไป)
conservative-by-construction: adverse-first + horizon cap H + cost-excluded → additive-gap
ที่รายงาน = ระวัง over-claim (ผลสะอาดเกินไปให้สงสัย · กฎวิน)
DoF pin ex-ante (ให้ Engineer review): TARGET=2.0 · stop=1.0R · H=360min · session hour 1-21
  · ATR_N=14 · intrabar=adverse-first · non-overlap=interval-scheduling (earliest-end greedy)
สนาม SEARCH · Usage: python opportunity_unit_v2.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TARGET = 2.0        # opportunity threshold (R-multiple) — pin ex-ante
STOPR = 1.0         # stop distance (R) — realizability constraint
H = 360             # forward horizon cap (min) — trunc = conservative (นับ opp น้อยลง)
ATR_N = 14
BIG = 10 ** 9


def day_opps(h, l, c, R):
    """disjoint stop-aware opportunities ในวัน · คืน list (origin, reach, dir)
    realizable = จาก origin (entry=close[origin]) แตะ TARGET·R ก่อนโดน 1R stop
    (adverse-first ภายใน bar เดียวกัน = stop ชนะ = conservative)"""
    m = len(c)
    tgt, rsk = TARGET * R, STOPR * R
    firsts = {}
    for d in (1, -1):
        stop_first = np.full(m, BIG, dtype=np.int64)
        targ_first = np.full(m, BIG, dtype=np.int64)
        for dj in range(1, min(H, m)):
            idx = np.arange(m - dj)
            p = idx + dj
            if d == 1:
                adv = l[p] <= c[idx] - rsk        # stop (adverse) ทิศ long
                fav = h[p] >= c[idx] + tgt        # target
            else:
                adv = h[p] >= c[idx] + rsk
                fav = l[p] <= c[idx] - tgt
            prel = stop_first[idx] == BIG          # ยังไม่โดน stop ก่อน bar นี้
            # target ผ่านก็ต่อเมื่อ: ยังไม่ stop · ไม่ adverse ใน bar นี้ (adverse-first) · ครั้งแรก
            nt = prel & fav & (~adv) & (targ_first[idx] == BIG)
            targ_first[idx[nt]] = dj
            ns = prel & adv & (stop_first[idx] == BIG)
            stop_first[idx[ns]] = dj
            if not (stop_first == BIG).any():      # ทุก origin โดน stop แล้ว → จบเร็ว
                break
        firsts[d] = targ_first

    cand = []
    for d in (1, -1):
        tf = firsts[d]
        for i in np.where(tf < BIG)[0]:
            cand.append((int(i), int(i + tf[i]), d))
    cand.sort(key=lambda x: x[1])                  # earliest-end greedy = max disjoint count
    last, sel = -1, []
    for o, r, d in cand:
        if o > last:
            sel.append((o, r, d))
            last = r
    return sel


def main():
    ctx = load_ctx()
    day, h, l, c, hour = ctx["day"], ctx["h"], ctx["l"], ctx["c"], ctx["hour"]
    v4day = {dts: int(f["dir"]) for dts, f in ctx["facts"].items() if f["traded"] == "1"}

    uniq, fidx = np.unique(day, return_index=True)
    bnd = np.r_[fidx[1:], len(h)]
    dr_hist = []
    opps, perday = [], []
    geo_opp_days = 0                                # v1-style geometric day-oracle (เทียบ deflation)
    n_days = 0
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), bnd.tolist()):
        dts = str(np.datetime64(int(di), "D"))
        R = float(np.mean(dr_hist[-ATR_N:])) if len(dr_hist) >= ATR_N else np.nan
        dr_hist.append(float(h[i0:i1].max() - l[i0:i1].min()))
        if dts[:4] < "2012" or not np.isfinite(R) or R <= 0:
            continue
        m = (hour[i0:i1] >= 1) & (hour[i0:i1] < 22)
        hh, ll, cc = h[i0:i1][m], l[i0:i1][m], c[i0:i1][m]
        if len(cc) < 30:
            continue
        n_days += 1
        # v1-style geometric oracle (hindsight · ไม่มี stop) — วัด deflation
        geo = max(float((hh - np.minimum.accumulate(ll)).max()),
                  float((np.maximum.accumulate(hh) - ll).max())) / R
        if geo >= TARGET:
            geo_opp_days += 1
        # v2 event-level stop-aware
        sel = day_opps(hh, ll, cc, R)
        perday.append(len(sel))
        v4d = v4day.get(dts, 0)
        for o, r, d in sel:
            opps.append(dict(date=dts, yr=dts[:4], dir=d,
                             covered=(v4d == d), v4=dts in v4day))

    pd = np.array(perday)
    n_opp = len(opps)
    day_has = int((pd >= 1).sum())
    print(f"=== Opportunity Reference Set v2 (trigger-constrained + event-level) · "
          f"field=SEARCH · TARGET={TARGET}R stop={STOPR}R H={H}m ===")
    print(f"UNIT = origin bar (event-level) · days={n_days} (2012-2020) · "
          f"realizable = แตะ 2R ก่อน 1R stop (adverse-first)")

    print(f"\n[A] HINDSIGHT DEFLATION (v1 geometric → v2 stop-aware · วัดว่า realizability กินไปเท่าไร):")
    print(f"  v1 geometric day-oracle: {geo_opp_days}/{n_days} = {100*geo_opp_days/n_days:.1f}% "
          f"วันมี ≥2R geometric-swing (นับ range ที่ 1R-stop อาจเขี่ยทิ้ง = inflated)")
    print(f"  v2 stop-aware day-has-opp: {day_has}/{n_days} = {100*day_has/n_days:.1f}% "
          f"วันมี ≥1 realizable opp → deflation {100*(geo_opp_days-day_has)/n_days:+.1f}pp "
          f"(hindsight ที่ถอดออก)")

    print(f"\n[B] EVENT-LEVEL SCALE (แก้ small-n · v1 คือ ~1 opp/วัน):")
    print(f"  total realizable opps = {n_opp} (event-level) · per-opp-day mean="
          f"{pd[pd>=1].mean():.2f} opp/วัน · max={int(pd.max())}/วัน")
    print(f"  วันมี ≥2 opp = {int((pd>=2).sum())} ({100*(pd>=2).sum()/n_days:.1f}%) → "
          f"event-level เพิ่ม population เหนือ day-level จริง")

    # v4 coverage @ event level (additive gap)
    cov = sum(1 for r in opps if r["covered"])
    on_v4day = sum(1 for r in opps if r["v4"])
    gap_missed = sum(1 for r in opps if not r["v4"])                    # วัน v4 ไม่เทรด
    gap_oppdir = sum(1 for r in opps if r["v4"] and not r["covered"])   # v4 เทรดแต่ผิดทิศ opp
    print(f"\n[C] v4 COVERAGE @ event-level (additive population สำหรับ direction-predictor):")
    print(f"  covered (v4 traded ∧ dir ตรง opp) = {cov}/{n_opp} = {100*cov/n_opp:.1f}%")
    print(f"  ADDITIVE GAP = {n_opp-cov}/{n_opp} = {100*(n_opp-cov)/n_opp:.1f}% แยกเป็น:")
    print(f"    · opp บนวัน v4-missed (ไม่เทรดเลย)     = {gap_missed}")
    print(f"    · opp บนวัน v4-traded แต่ผิดทิศ (opposite) = {gap_oppdir}")
    print(f"  → population ของ direction-predictor (missed∨opposite) = {n_opp-cov} "
          f"(v1 day-level เคยได้ n=31)")

    print(f"\n[D] per-year (event-level realizable opps · additive gap):")
    for y in range(2012, 2021):
        yo = [r for r in opps if r["yr"] == str(y)]
        yg = sum(1 for r in yo if not r["covered"])
        if yo:
            print(f"    {y}: opp={len(yo):>4} · additive-gap={yg:>4} "
                  f"({100*yg/len(yo):.0f}%) · covered={len(yo)-yg}")

    print(f"\n⚠ oracle v2 = tighter UPPER bound (stop-aware) แต่ยังมี hindsight 'เลือก origin ถูก' "
          f"= labeling instrument วัด gap เท่านั้น **ห้ามใช้เป็น prediction target** (§9 guardrail) · "
          f"cost-excluded + adverse-first + H-cap = conservative บน realizability · "
          f"gap นี้ = ADDRESSABLE population ยังไม่ใช่ realized edge (ต้อง ex-ante predictor)")


if __name__ == "__main__":
    main()
