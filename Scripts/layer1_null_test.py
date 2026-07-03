#!/usr/bin/env python3
"""
TRELLIS Stage 0 — Layer 1: Null-data 3-way Calibration
======================================================
อ้างอิง: Plan/TRELLIS-002_expectancy_sim_plan.md §4 ชั้น 1 + §9

จุดประสงค์: ตรวจว่า basket_engine (grid_sim) "วัด edge ได้ทั้งสองทิศ" ไม่ใช่แค่ไม่ bias บวก
  - driftless GBM   → expectancy ≤ 0 (≈ −cost)   : ไม่มี look-ahead/cost รั่ว/positive bias
  - pure-trend      → expectancy ลบหนัก           : engine จับ grid-death (fade ตาย) ได้
  - OU mean-revert  → expectancy บวก               : engine มี power เห็น edge เมื่อ edge มีจริง
ถ้าผิด pattern = engine เชื่อไม่ได้ → ห้ามรันบน Gold (ตาม CLAUDE.md §Verify "ตรวจเครื่องมือตัวเอง")

Run: python layer1_null_test.py
"""
import json
import sys
from pathlib import Path

import numpy as np

from grid_sim import GridConfig, run_grid, summarize

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = Path(r"D:\workspace\Doc\T.me\R&D\Trellis\Research")
N_STEPS = 300_000
P0 = 2000.0
SEED = 7

# ใช้ ARITHMETIC process ($ คงที่) — เหมาะกับ grid spacing ที่เป็น $ คงที่
# กัน geometric ระเบิด (exp drift) ที่ทำ per-step move ใหญ่เกินจริง → overshoot หลอกตา
VOL_USD = 0.40            # std ของ move ต่อ step ($) ≈ Gold M1
TREND_DRIFT_USD = 0.05    # drift ต่อ step ($) สำหรับ pure-trend (สม่ำเสมอ ไม่ระเบิด)
OU_THETA = 0.01           # ความเร็ว mean-reversion (กลับเข้า P0)
OU_VOL_USD = 0.45         # std ของ shock ต่อ step ($) สำหรับ OU

CFG = GridConfig(
    spacing=1.5, lot=0.01, contract=100.0, max_levels=20,
    tp_usd=4.0, hardstop_usd=40.0,
    commission_per_lot_side=7.0, stop_slippage_usd=0.20,
    entry_lookback=5, entry_mode="fade",
)
SPREAD = 0.30


def gen_gbm(rng):
    """driftless arithmetic random walk ($ คงที่)."""
    return P0 + np.cumsum(rng.normal(0.0, VOL_USD, N_STEPS))


def gen_trend(rng, sign=+1):
    """pure-trend: drift $ คงที่ + noise (ไม่ระเบิด)."""
    return P0 + np.cumsum(rng.normal(sign * TREND_DRIFT_USD, VOL_USD, N_STEPS))


def gen_ou(rng):
    """OU mean-revert ใน price space รอบ P0."""
    x = np.empty(N_STEPS)
    x[0] = P0
    eps = rng.normal(0.0, OU_VOL_USD, N_STEPS)
    for t in range(1, N_STEPS):
        x[t] = x[t - 1] + OU_THETA * (P0 - x[t - 1]) + eps[t]
    return x


def run_case(name, mid):
    cyc = run_grid(mid, SPREAD, CFG)
    s = summarize(cyc)
    print(f"\n[{name}]")
    print(f"  cycles={s['n_cycles']:,}  expectancy/cycle=${s['expectancy']:+.4f}  "
          f"total=${s['total']:+,.0f}")
    print(f"  win_rate={s['win_rate']*100:.1f}%  stop_rate={s['stop_rate']*100:.1f}%  "
          f"avg_fills={s['avg_fills']:.1f}  avgW=${s['avg_win']:+.2f}  avgL=${s['avg_loss']:+.2f}")
    return s


def main():
    print("=" * 72)
    print("LAYER 1 — Null-data 3-way Calibration (validate basket_engine)")
    print(f"  cfg: spacing=${CFG.spacing} lot={CFG.lot} TP=${CFG.tp_usd} "
          f"HardStop=${CFG.hardstop_usd} spread=${SPREAD} comm=${CFG.commission_per_lot_side}/lot/side")
    print("=" * 72)
    rng = np.random.default_rng(SEED)

    res = {}
    res["gbm"] = run_case("driftless GBM  (expect ≤0 ≈ -cost)", gen_gbm(rng))
    res["trend_up"] = run_case("pure-trend UP (expect << 0)", gen_trend(rng, +1))
    res["trend_dn"] = run_case("pure-trend DN (expect << 0)", gen_trend(rng, -1))
    res["ou"] = run_case("OU mean-revert (expect > 0)", gen_ou(rng))

    # --- VERDICT ---
    gbm = res["gbm"]["expectancy"]
    tup = res["trend_up"]["expectancy"]
    tdn = res["trend_dn"]["expectancy"]
    ou = res["ou"]["expectancy"]
    trend_worst = min(tup, tdn)

    c_gbm = gbm < 0                          # ไม่ bias บวกบน driftless
    c_trend = (tup < 0) and (tdn < 0)        # fade ตายทั้งสองทิศ trend
    c_ou = ou > 0                            # มี power เห็น edge
    c_order = (ou > gbm) and (trend_worst < gbm)   # ลำดับถูก: trend < gbm < ou
    verdict = c_gbm and c_trend and c_ou and c_order

    print("\n" + "-" * 72)
    print(f"  GBM expectancy < 0           : {'OK' if c_gbm else 'FAIL'}  (${gbm:+.4f})")
    print(f"  trend both < 0               : {'OK' if c_trend else 'FAIL'}  (up ${tup:+.4f} / dn ${tdn:+.4f})")
    print(f"  OU expectancy > 0            : {'OK' if c_ou else 'FAIL'}  (${ou:+.4f})")
    print(f"  ordering trend < GBM < OU    : {'OK' if c_order else 'FAIL'}")
    print(f"\n  LAYER 1 VERDICT: {'PASS — engine วัด edge ได้ทั้งสองทิศ ไม่ bias บวก' if verdict else 'FAIL — engine เชื่อไม่ได้ ห้ามรัน Gold'}")
    print("=" * 72)

    out = {"config": CFG.__dict__, "spread": SPREAD, "seed": SEED,
           "n_steps": N_STEPS, "results": res,
           "verdict": {"gbm_neg": c_gbm, "trend_neg": c_trend, "ou_pos": c_ou,
                       "ordering": c_order, "pass": bool(verdict)}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "layer1_null_result.json").write_text(json.dumps(out, indent=2))
    print(f"saved -> {OUT / 'layer1_null_result.json'}")


if __name__ == "__main__":
    main()
