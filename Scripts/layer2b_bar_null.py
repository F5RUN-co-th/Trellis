#!/usr/bin/env python3
"""
TRELLIS Stage 0 — Layer 2b: Null-test ของ run_grid_bars (วัด V-shape artifact)
============================================================================
อ้างอิง: Engineer round-6 A-HIGH#2 · CLAUDE.md §Verify "ตรวจเครื่องมือตัวเอง"

ปัญหา: run_grid_bars (engine ที่ผลิตผล Layer 2) ไม่เคยผ่าน null-gate — Layer 1 ทดสอบ run_grid
(step engine) คนละตัว. intra-bar O→adverse→favor→C เป็น OPTIMISTIC (fill ก้นเหวแล้ว recover).

วิธีวัด artifact: สร้าง DRIFTLESS GBM แล้ว aggregate เป็น OHLC bars (มี intra-bar range สมจริง)
→ feed เข้า run_grid_bars ที่ ZERO COST → driftless ต้องได้ expectancy ≈ 0.
  ถ้า > 0  = ขนาดของ V-shape artifact (กำไรปลอมจาก intra-bar fill-then-recover)
  เทียบกับ Layer 2 +$0.92 → รู้ว่าเท่าไหร่ของ +$0.92 เป็นของปลอม.

Run: python layer2b_bar_null.py
"""
import json
import sys
from pathlib import Path

import numpy as np

from grid_sim import GridConfig, run_grid_bars, summarize

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = Path(r"D:\workspace\Doc\T.me\R&D\Trellis\Research")
N_BARS = 250_000
SUBSTEPS = 20          # tick ต่อ bar (สร้าง intra-bar range)
VOL_SUB = 0.15         # $ std ต่อ sub-step → bar range ~$1.5-2 (ใกล้ Gold M1)
P0 = 2000.0
SEED = 11
LOOKBACK = 15

CFG = GridConfig(
    spacing=1.5, lot=0.01, contract=100.0, max_levels=20,
    tp_usd=4.0, hardstop_usd=40.0,
    commission_per_lot_side=0.0, stop_slippage_usd=0.0,   # ZERO cost — แยก artifact ล้วน
)


def gen_driftless_ohlc(rng):
    """driftless arithmetic RW → OHLC bars (intra-bar range สมจริง)."""
    steps = rng.normal(0.0, VOL_SUB, N_BARS * SUBSTEPS)
    path = P0 + np.cumsum(steps)
    sub = path.reshape(N_BARS, SUBSTEPS)
    O = sub[:, 0].copy()
    C = sub[:, -1].copy()
    H = sub.max(axis=1)
    L = sub.min(axis=1)
    return O, H, L, C


def run_case(label, O, H, L, C, spread, intrabar="adverse_first"):
    fade = summarize(run_grid_bars(O, H, L, C, CFG, spread, entry_mode="fade",
                                   lookback=LOOKBACK, intrabar=intrabar))
    rng = np.random.default_rng(999)
    rnd = summarize(run_grid_bars(O, H, L, C, CFG, spread, entry_mode="random",
                                  lookback=LOOKBACK, rng=rng, intrabar=intrabar))
    print(f"\n[{label}  spread=${spread}]")
    print(f"  fade  : cycles={fade['n_cycles']:,}  exp/cycle=${fade['expectancy']:+.4f}  "
          f"win={fade['win_rate']*100:.1f}%  avgW=${fade['avg_win']:+.2f} avgL=${fade['avg_loss']:+.2f}")
    print(f"  random: cycles={rnd['n_cycles']:,}  exp/cycle=${rnd['expectancy']:+.4f}  "
          f"win={rnd['win_rate']*100:.1f}%")
    return {"fade": fade, "random": rnd, "spread": spread}


def main():
    print("=" * 72)
    print("LAYER 2b — Null-test run_grid_bars (driftless GBM-as-OHLC) → วัด V-shape artifact")
    print(f"  driftless RW: {N_BARS:,} bars × {SUBSTEPS} substeps, vol_sub=${VOL_SUB}")
    print(f"  cfg: spacing=${CFG.spacing} TP=${CFG.tp_usd} stop=${CFG.hardstop_usd} (ZERO cost)")
    print("  EXPECT (no artifact): expectancy ≈ 0  |  ถ้า > 0 = V-shape artifact")
    print("=" * 72)
    rng = np.random.default_rng(SEED)
    O, H, L, C = gen_driftless_ohlc(rng)
    print(f"  bar range: median=${np.median(H-L):.2f}  mean=${np.mean(H-L):.2f}")

    res = {}
    res["zero_cost"] = run_case("ZERO COST adverse-first (optimistic)", O, H, L, C, 0.0, "adverse_first")
    res["zero_cost_pess"] = run_case("ZERO COST favor-first (pessimistic)", O, H, L, C, 0.0, "favor_first")
    res["spread_030"] = run_case("spread $0.30 adverse-first", O, H, L, C, 0.30, "adverse_first")

    art = res["zero_cost"]["fade"]["expectancy"]
    print("\n" + "-" * 72)
    print(f"  V-shape artifact (zero-cost driftless fade): ${art:+.4f}/cycle")
    if abs(art) < 0.05:
        print("  -> artifact เล็ก (engine ~unbiased) — Layer 2 positive น่าเชื่อกว่า")
    else:
        print(f"  -> artifact ${art:+.4f} เทียบ Layer 2 IS +$0.92 → {art/0.92*100:.0f}% ของผลเป็นของปลอม")
        print("  -> run_grid_bars BIASED บน OHLC — ต้อง real-tick fill ก่อนเชื่อ absolute")
    print("=" * 72)

    OUT.mkdir(parents=True, exist_ok=True)
    out = {"config": CFG.__dict__, "n_bars": N_BARS, "vol_sub": VOL_SUB,
           "artifact_zero_cost_fade": art, "results": res}
    (OUT / "layer2b_bar_null.json").write_text(json.dumps(out, indent=2))
    print(f"saved -> {OUT / 'layer2b_bar_null.json'}")


if __name__ == "__main__":
    main()
