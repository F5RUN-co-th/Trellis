#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fade_dataset.py — TRELLIS-010 v3 Step 2 · EdgeDistribution + mirror-fade kill-test

สร้าง counterfactual behavior P&L ต่อ opportunity (วันเทรด v4):
  · pnl_cont = v4 continuation (walker เดิม · per-trade exact 1,487/1,487)
  · pnl_fade = **mirror**: flip direction −d · entry/stop สูตรเดียวกับ v4 (mirror edge)
    · same trail/EOD/catchup/cost — pay cost สองทาง (realistic)
join state ที่มีอยู่: dc-state (FRESH/SPENT · C9) · poke (C6) · MS (C10)

MIRROR-FADE KILL-TEST (necessary condition ก่อน mechanism-fade):
  fade ชนะ continuation บน population ที่ **signal ทำนายได้** ไหม? (ไม่ใช่ hindsight)
  · ถ้าแม้ mirror หยาบ (0 param) ยังไม่ช่วยเลยบน exhaustion-signal = mechanism-fade ก็ไม่รอด
  · ถ้าช่วย → สร้าง mechanism-fade (Step 2 ต่อ)
สนาม SEARCH · pnl_fade เป็น counterfactual (mirror = orientation · mechanism-fade = decision)
Usage: python fade_dataset.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, walk, cell_of, CAPR, PT, SLIP_IN
from dual_asian_sim import PT as _PT  # noqa

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent.parent / "Research" / "h0"


def entry_stop(ctx, k, d, ash, asl, R):
    """สูตร entry/stop เดียวกับ v4 (mirror ได้ด้วย d = ±1)"""
    if d == 1:
        ent = ctx["o"][k] + ctx["sp"][k] * PT + SLIP_IN
        stop = max(asl, ent - CAPR * R)
    else:
        ent = ctx["o"][k] - SLIP_IN
        stop = min(ash, ent + CAPR * R)
    return ent, stop


def main():
    ctx = load_ctx()
    rd = lambda f: {r["date"]: r for r in csv.DictReader(
        ln for ln in open(DIR / f, encoding="utf-8") if not ln.startswith("#"))}
    dc, poke = rd("h0_dcfeat_2012_2020.csv"), rd("h0_pokefeat_2012_2020.csv")
    ms = rd("h0_msfeat_2012_2020.csv")

    rows = []
    for dts, f in sorted(ctx["facts"].items()):
        if f["traded"] != "1":
            continue
        k = ctx["pos"][dts + "T" + f["entry_time"]]
        d = int(f["dir"])
        ash, asl = ctx["lv"][dts]
        R = ash - asl
        ent_c, stop_c = entry_stop(ctx, k, d, ash, asl, R)
        ent_f, stop_f = entry_stop(ctx, k, -d, ash, asl, R)
        pnl_c = walk(ctx, k, d, ent_c, stop_c, R)[0]
        pnl_f = walk(ctx, k, -d, ent_f, stop_f, R)[0]
        assert np.isfinite(pnl_c) and abs(pnl_c - float(f["pnl"])) < 2e-3, f"cont mismatch {dts}"
        rows.append(dict(date=dts, yr=dts[:4], pnl_c=pnl_c, pnl_f=pnl_f,
                         cell=cell_of(ctx, dts),
                         dcs=dc[dts]["dc_state"], poked=poke[dts].get("poked", ""),
                         mss=ms[dts]["ms_state"]))

    c = np.array([r["pnl_c"] for r in rows])
    ff = np.array([r["pnl_f"] for r in rows])
    print(f"EdgeDistribution n={len(rows)} · field=SEARCH")
    print(f"  pnl_cont (v4): sum={c.sum():+.1f} exp={c.mean():+.3f} WR={100*(c>0).mean():.1f}%")
    print(f"  pnl_fade (mirror): sum={ff.sum():+.1f} exp={ff.mean():+.3f} WR={100*(ff>0).mean():.1f}%")
    print(f"  corr(cont,fade)={np.corrcoef(c,ff)[0,1]:+.3f} (mirror → คาด ~−1 ลบ cost)")

    print("\n=== MIRROR-FADE KILL-TEST: fade ชนะ continuation บน population ที่ signal ทำนายได้? ===")
    def split(mask, name):
        sub_c, sub_f = c[mask], ff[mask]
        best = np.maximum(sub_c, sub_f)   # Behavior-Oracle(B): perfect cont/fade choice (≠ predictor UB)
        adv = sub_f - sub_c               # fade advantage
        print(f"  {name:22} n={mask.sum():>4} | cont={sub_c.sum():+7.1f} fade={sub_f.sum():+7.1f} "
              f"| fade−cont={adv.sum():+7.1f} | BehavOracle(B)={best.sum():+7.1f}")
    m_all = np.ones(len(rows), bool)
    split(m_all, "ALL")
    # exhaustion signals (fade candidate)
    dcs = np.array([r["dcs"] for r in rows])
    split(dcs == "FRESH", "dc FRESH (→cont)")
    split(np.isin(dcs, ["MID", "EXTENDED"]), "dc SPENT (→fade?)")
    poked = np.array([r["poked"] for r in rows])
    split(poked == "1", "POKED (→fade?)")
    cell = np.array([r["cell"] for r in rows])
    split(cell == "POKED|SPENT", "POKED∧SPENT (−0.58 cell)")
    mss = np.array([r["mss"] for r in rows])
    split(mss == "OPPOSED", "MS OPPOSED (→fade?)")

    print("\n⚠ 2 oracle แยก (ChatGPT): Oracle-A=Opportunity (opportunity_unit) · Oracle-B=Behavior (นี่)"
          "\n  fade−cont > 0 บน signal-population deployable = kill-test ผ่าน · BehavOracle(B) = UB ของ"
          " behavior-select (perfect cont/fade · ≠ predictor UB) · signal แยกไม่ได้ → mechanism-fade ไม่รอด")


if __name__ == "__main__":
    main()
