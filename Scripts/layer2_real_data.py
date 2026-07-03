#!/usr/bin/env python3
"""
TRELLIS Stage 0 — Layer 2: Random-entry Baseline vs Pullback (real Gold)
=======================================================================
อ้างอิง: Plan/TRELLIS-002_expectancy_sim_plan.md §4 ชั้น 2

คำถาม: pullback (MR) entry ชนะ random entry อย่างมีนัยไหม? (relative test)
  - relative → resolution/cost กระทบสองขาเท่ากัน → fair แม้บน M1 OHLC
  - ถ้า pullback ไม่ชนะ random → entry signal ไม่มี edge → falsify ถูกๆ (funnel)
  + รายงาน absolute expectancy (preliminary) ด้วย cost Exness จริง

Engine: grid_sim.run_grid_bars (bar-structured, intra-bar adverse-first, conservative)
Cost: Exness Standard (commission 0, spread ~$0.30), SWAP-FREE (swap=0, วินยืนยัน)
หมายเหตุ: intra-bar = approximation จาก OHLC (adverse-first) ไม่ใช่ full tick — conservative,
          ไม่ overstate edge. full-tick = refinement ทีหลังถ้าผลคุ้มเดินต่อ.

Run: python layer2_real_data.py --quick 2024
     python layer2_real_data.py            # IS 2011-21 + OOS 2022-26
"""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from grid_sim import GridConfig, run_grid_bars, summarize

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA_DIR = Path(r"D:\workspace\Doc\T.me\R&D\Gloo\Data")
OUT = Path(r"D:\workspace\Doc\T.me\R&D\Trellis\Research")
IS_YEARS = list(range(2011, 2022))
OOS_YEARS = list(range(2022, 2027))

# Exness Standard (swap-free) — §10 #6
SPREAD = 0.30                  # $ (Exness Standard gold โดยประมาณ — verify จริง)
N_RANDOM_SEEDS = 3
LOOKBACK = 15                  # bars (นาที) สำหรับ pullback fade — กว้างพอเลี่ยง microstructure

CFG = GridConfig(
    spacing=1.5, lot=0.01, contract=100.0, max_levels=20,
    tp_usd=4.0, hardstop_usd=40.0,
    commission_per_lot_side=0.0,        # Exness Standard = commission-free
    stop_slippage_usd=0.20,
)


def load_ohlc(year):
    O, H, L, C = [], [], [], []
    path = DATA_DIR / f"XAUUSD_M1_{year}.csv"
    if not path.exists():
        print(f"  ! missing {path.name}")
        return None
    with open(path, newline="") as f:
        for ln in csv.reader(f, delimiter="\t"):
            if len(ln) < 6:
                continue
            try:
                O.append(float(ln[2])); H.append(float(ln[3]))
                L.append(float(ln[4])); C.append(float(ln[5]))
            except (ValueError, IndexError):
                continue
    return (np.array(O), np.array(H), np.array(L), np.array(C))


def run_period(years, label):
    print(f"\nLoading M1 OHLC {label} ...")
    Os, Hs, Ls, Cs = [], [], [], []
    for y in years:
        d = load_ohlc(y)
        if d is None:
            continue
        Os.append(d[0]); Hs.append(d[1]); Ls.append(d[2]); Cs.append(d[3])
    if not Cs:
        return None
    O = np.concatenate(Os); H = np.concatenate(Hs)
    L = np.concatenate(Ls); C = np.concatenate(Cs)
    print(f"  bars={C.size:,}")

    # BRACKET: optimistic (adverse-first) vs pessimistic (favor-first) intra-bar fill
    fade_opt = summarize(run_grid_bars(O, H, L, C, CFG, SPREAD, entry_mode="fade",
                                       lookback=LOOKBACK, intrabar="adverse_first"))
    fade_pess = summarize(run_grid_bars(O, H, L, C, CFG, SPREAD, entry_mode="fade",
                                        lookback=LOOKBACK, intrabar="favor_first"))
    rnd_runs = [summarize(run_grid_bars(O, H, L, C, CFG, SPREAD, entry_mode="random",
                                        lookback=LOOKBACK, rng=np.random.default_rng(1000 + s),
                                        intrabar="adverse_first")) for s in range(N_RANDOM_SEEDS)]
    rnd_exp = float(np.mean([r["expectancy"] for r in rnd_runs]))

    lo, hi = fade_pess["expectancy"], fade_opt["expectancy"]
    straddle = lo < 0 < hi
    verdict = "คร่อม 0 = UNCERTAIN" if straddle else ("บวกทั้งคู่" if lo > 0 else "ลบทั้งคู่")
    print(f"  [pullback OPTIMISTIC adverse-first] exp/cycle=${hi:+.4f}  win={fade_opt['win_rate']*100:.1f}%")
    print(f"  [pullback PESSIMISTIC favor-first ] exp/cycle=${lo:+.4f}  win={fade_pess['win_rate']*100:.1f}%")
    print(f"  [random adverse-first             ] exp/cycle=${rnd_exp:+.4f}")
    print(f"  -> pullback bracket [pess .. opt] = [${lo:+.4f} .. ${hi:+.4f}]  {verdict}")
    return {"label": label, "years": [years[0], years[-1]], "bars": int(C.size),
            "fade_optimistic": fade_opt, "fade_pessimistic": fade_pess,
            "random_mean": rnd_exp, "bracket": [lo, hi], "straddle_zero": bool(straddle)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", type=int, help="รันปีเดียว (validate)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("LAYER 2 — Pullback vs Random entry (real Gold M1, Exness Standard swap-free)")
    print(f"  cfg: spacing=${CFG.spacing} lot={CFG.lot} TP=${CFG.tp_usd} stop=${CFG.hardstop_usd} "
          f"spread=${SPREAD} comm=${CFG.commission_per_lot_side} swap=0 lookback={LOOKBACK}")
    print("=" * 72)

    blocks = []
    if args.quick:
        blocks.append(run_period([args.quick], f"YEAR-{args.quick}"))
    else:
        blocks.append(run_period(IS_YEARS, "IN-SAMPLE"))
        blocks.append(run_period(OOS_YEARS, "OUT-OF-SAMPLE"))

    out = {"config": CFG.__dict__, "spread": SPREAD, "swap": 0,
           "note": "Exness Standard swap-free; intra-bar=OHLC adverse-first approx (conservative)",
           "blocks": [b for b in blocks if b]}
    fname = "layer2_quick.json" if args.quick else "layer2_result.json"
    (OUT / fname).write_text(json.dumps(out, indent=2))
    print(f"\nsaved -> {OUT / fname}")


if __name__ == "__main__":
    main()
