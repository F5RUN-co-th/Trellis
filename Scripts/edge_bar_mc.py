#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edge_bar_mc.py — TRELLIS-010 v3 Step 1 · system-of-record ของ ruin / edge-bar
(script เป็นเจ้าของตัวเลข ไม่ใช่ LLM — CLAUDE.md Verify≠self-grading)

โจทย์ที่ตอบ: "edge (expectancy/ไม้) ต้องแรงแค่ไหน ให้ $100 flat-min-lot **รอด**"
= ruin-safe edge bar · ผูกเป้าวิน "เริ่ม $100 → อยู่รอด"

นิยาม/สนาม (ติดป้ายทุกเลข):
  · field = **SEARCH** (h0_day_facts 2012-2020, uncapped sim + ea_catchup) —
    ruin% ที่รายงาน = **LOWER BOUND** (real-tick CONFIRM แย่กว่า: gap/slippage ทะลุ
    stop + haircut ~1.2/ไม้ high-vol) → ห้ามเรียก "edge ruin-safe" จนผ่าน CONFIRM (MED-1)
  · **intra-trade MAE (DEFECT-1):** ทุกไม้จำลอง **แตะ −R intrabar ก่อน settle** (R =
    Asian-range stop = ceiling ของ MAE ใน SEARCH · winner ที่ไม่เคยแตะ −R = conservative
    over-state; loser = exact) → เช็ค ruin ที่ intrabar trough ไม่ใช่แค่ close
    (Grid Doctrine #6: ออกแบบโดยถือ worst-case > เพดาน) · verified: min-eq
    close-only $26.97 → intrabar $17.37
  · **3 metric แยกสถานะ (ChatGPT taxonomy — กันสับสนว่าเลขไหน "จริงกว่า"):** mean-shift =
    **ORIENTATION** (edge ต้อง ~ระดับไหน) · winner-scaled = **STRESS-test** (ทน shape เข้ม
    ขึ้นไหม — **ไม่ใช่ upper bound เหนือทุก shape**) · `eval_ruin(distribution)` = **DECISION**
    (Step 2 · ตัดสินจริง) → $1.25(orient) กับ $2.0-2.5(stress) ตอบคนละคำถาม
  · **block (Engineer P1 — cause แก้ให้ตรง evidence):** lag-1 autocorr = +0.010 (≈white noise ·
    **ไม่ mean-revert** ตามที่เคยเขียนผิด) · block streakier by variance · แต่ **IID ruin สูงกว่า**
    เพราะ IID concat loss-run ลึกกว่า empirical local sequencing → report **max(IID, block)** =
    robust ต่อ sign ของ autocorr · streak=11
  · **shape ≠ mean (HIGH-1):** ที่ mean เดียวกัน winner-scaled (winners×k · losers ยัง −R =
    shape "let-winners-run") ruin สูงกว่า mean-shift 3× → **gate จริง = distribution-in ไม่ใช่
    scalar** · CONFIRM = run CONFIRM distribution ผ่าน eval_ruin **ตรงๆ** (ไม่ +haircut บน SEARCH
    scalar = double-count)
  · edge-shift = คง shape/variance/R เดิม เลื่อน mean ไปเป้า (โครง risk เท่าเดิม
    edge แรงขึ้น = mean สูงขึ้น) — first-order bar; edge จริงตอนเจอ (Step 2) เอา
    distribution ตัวเองเข้า eval_ruin โดยตรง

Usage: python edge_bar_mc.py            # bar-sweep + sensitivity
       python edge_bar_mc.py <exp>      # eval ruin ที่ expectancy เดียว
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent.parent / "Research" / "h0"
FACTS = DIR / "h0_day_facts_2012_2020.csv"
START = 100.0                 # เป้าวิน (fixed · ห้ามเปลี่ยน = ไม่ใช่ตัวแปรแก้ปัญหา)
MARGIN = 1.30                 # margin-floor 0.01-lot XAUUSD lev 1:2000 (~price×100×0.01/2000)
SEED = 11
NBOOT = 20000
YEARS_DATA = 9.0              # h0 = 2012-2020


def load():
    """โหลด pnl + R (SEARCH field) + integrity check (reconciliation +532.8)"""
    with open(FACTS, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(ln for ln in f if not ln.startswith("#"))]
    tr = [(float(r["pnl"]), float(r["R"])) for r in rows if r["traded"] == "1"]
    pnl = np.array([x[0] for x in tr])
    R = np.array([x[1] for x in tr])
    assert abs(pnl.sum() - 532.8) < 0.1, f"reconciliation broken: {pnl.sum()}"
    assert (R > 0).all(), "R must be positive stop-distance"
    return pnl, R


def min_equity(pnl_seq, R_seq, start=START):
    """intrabar-−R equity path → คืน (close_min, intrabar_min) [DEFECT-1]"""
    eq = start
    cmin = imin = start
    for p, r in zip(pnl_seq, R_seq):
        t = eq - r                       # แตะ −R intrabar ก่อน settle
        if t < imin:
            imin = t
        eq += p
        if eq < cmin:
            cmin = eq
    return cmin, imin


def mean_shift(pnl, target):
    """shape เดิม เลื่อน mean → target (คง variance/tail)"""
    return pnl + (target - pnl.mean())


def winner_scaled(pnl, target):
    """[Engineer HIGH-1] winners×k ให้ mean=target · losers ยังชน −R เดิม =
    shape ที่เป้า 'กำไรมาก/let-winners-run' บ่งชี้ (adversarial floor · ruin สูงกว่า)"""
    w = pnl > 0
    k = (target * len(pnl) - pnl[~w].sum()) / pnl[w].sum()
    out = pnl.copy(); out[w] = pnl[w] * k
    return out


def _ruin(ps, R, n_trades, blk, floor, nboot=NBOOT, seed=SEED):
    """block bootstrap (blk=1 = IID) · intrabar-−R · คืน (P(≤floor), P(≤0), finals[])"""
    rng = np.random.default_rng(seed)
    n = len(ps)
    nbk = int(np.ceil(n_trades / blk))
    hf = hz = 0
    finals = []
    for _ in range(nboot):
        starts = rng.integers(0, max(1, n - blk) + 1, nbk)
        idx = np.concatenate([np.arange(s, min(s + blk, n)) for s in starts])[:n_trades]
        seq, rseq = ps[idx], R[idx]
        # intrabar-−R trough (vectorized): equity ก่อนแต่ละไม้ − R
        cum_before = START + np.concatenate(([0.0], np.cumsum(seq)[:-1]))
        imin = float((cum_before - rseq).min())
        hf += imin <= floor
        hz += imin <= 0
        finals.append(START + float(seq.sum()))
    return hf / nboot, hz / nboot, np.array(finals)


def ruin_prob(pnl, R, target_exp, n_trades, blk, floor, nboot=NBOOT, seed=SEED):
    pf, pz, fin = _ruin(mean_shift(pnl, target_exp), R, n_trades, blk, floor, nboot, seed)
    return pf, pz, float(np.median(fin))


def main():
    pnl, R = load()
    sha = hashlib.sha256(FACTS.read_bytes()).hexdigest()[:12]
    n5 = int(len(pnl) / YEARS_DATA * 5)          # ~5-year horizon
    print(f"=== edge_bar_mc · field=SEARCH (LOWER BOUND) · SHA(facts)={sha} ===")
    print(f"data: n={len(pnl)} exp/ไม้={pnl.mean():+.3f} WR={100*(pnl>0).mean():.1f}% "
          f"· horizon 5y≈{n5} ไม้ · start=${START:.0f} margin-floor=${MARGIN} · blk=20")
    cmin, imin = min_equity(pnl, R)
    print(f"historical single-ordering: close-min=${cmin:.2f} intrabar-min=${imin:.2f}\n")

    print("P(ruin≤margin) ต่อ target — headline = CONSERVATIVE corner = max(shape × block):")
    print(f"{'exp':>6}{'×v4':>5}{'mshift/blk20':>13}{'mshift/IID':>11}{'winner/IID':>12}{'CONSERV':>9}")
    bar = None
    for te in [pnl.mean(), 0.75, 1.0, 1.25, 1.5, 2.0, 2.5]:
        opt = _ruin(mean_shift(pnl, te), R, n5, 20, MARGIN)[0]     # optimistic corner
        iid = _ruin(mean_shift(pnl, te), R, n5, 1, MARGIN)[0]      # IID (block-conservative)
        wsc = _ruin(winner_scaled(pnl, te), R, n5, 1, MARGIN)[0]   # shape-conservative
        cons = max(iid, wsc)
        print(f"{te:>6.2f}{te/pnl.mean():>5.1f}{opt*100:>12.1f}%{iid*100:>10.1f}%"
              f"{wsc*100:>11.1f}%{cons*100:>8.1f}%")
        if bar is None and cons < 0.02:
            bar = te
    print(f"\n⭐ STRESS-test edge bar (winner-scaled/IID <2%, SEARCH-LB) ≈ **$2.0-2.5/ไม้ "
          f"(5.6-7.0× v4)** · boundary ~$2.0 (mean 1.99% over seeds[11,1,2,3,42] · seed-dependent)")
    print("   ORIENTATION (mshift/blk20)=~$1.25/3.5× · DECISION (Step 2)=eval_ruin(distribution จริง)")
    if bar:
        _, _, fin = _ruin(winner_scaled(pnl, bar), R, n5, 1, MARGIN)
        q = np.percentile(fin, [5, 25, 50, 75, 95])
        print(f"   final-equity percentiles @bar 5/25/50/75/95 = "
              f"${q[0]:.0f}/{q[1]:.0f}/{q[2]:.0f}/{q[3]:.0f}/{q[4]:.0f}")
    print("\n⚠ SEARCH LOWER BOUND · **gate จริง = เอา distribution ของ Step-2 เข้า eval_ruin "
          "โดยตรง** (scalar = orientation counterfactual) · threshold 2% = risk policy pre-reg "
          "· CONFIRM แย่กว่า (haircut ~1.2/ไม้)")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pnl, R = load()
        te = float(sys.argv[1])
        n5 = int(len(pnl) / YEARS_DATA * 5)
        pf, pz, mf = ruin_prob(pnl, R, te, n5, 20, MARGIN)
        print(f"exp=${te}/ไม้ (SEARCH-LB): P(ruin≤margin)={pf*100:.1f}% P(≤0)={pz*100:.1f}% "
              f"medFinal=${mf:.0f}")
    else:
        main()
