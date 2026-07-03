#!/usr/bin/env python3
"""
holdout_exness.py — TRELLIS-010 Stage 0 (E): re-derive FULL HOLDOUT บน Exness feed
ด้วย script ที่ commit + rerun ได้ (เลขเดิม +$802.5 ใน TRELLIS-009 §10 เป็น un-scripted)

สนามวัด: SIM (bar-M1 pessimistic, dual_asian_sim.run canonical) บน data Exness XAUUSDm
  จาก ExportM1: Common\Files\XAUUSD_M1_export.csv (UTC+0, 2026.02.01-2026.07.03)

Clock: Exness UTC+0 -> BT-clock (+2 หนาว/+3 ร้อน) — รันทั้งกฎ EU (ถูกต้อง พิสูจน์
  price-match TRELLIS-010) และกฎ US (ที่ EA/AUTO เคยใช้ก่อนแก้) เพื่อ quantify ผลต่าง
  ช่วง shoulder มี.ค. 2026 (EU เริ่ม 29 มี.ค. / US เริ่ม 8 มี.ค. — ต่างกัน 3 สัปดาห์)

Holdout window: 2026-02-24 เป็นต้นไป (Dukascopy จบ 23 ก.พ. — ไม่มี decision ใดเคยเห็นหลังนั้น)
Warmup: 1-23 ก.พ. (EMA2880+slope1440 ~3 วัน — พอ)

Usage: python holdout_exness.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dual_asian_sim import run, stats
from stage0_join import DEPLOY_CFG, dst_shift_minutes

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXPORT = Path(r"C:/Users/itd_surachartt/AppData/Roaming/MetaQuotes/Terminal/Common/Files/XAUUSD_M1_export.csv")
HOLDOUT_START = np.datetime64("2026-02-24")


def load_export():
    """โหลด ExportM1 CSV (format เดียวกับ XAUUSD_M1_YYYY.csv แต่ clock UTC+0)
    หน่วย spread: ExportM1.mq5:50 เขียน rates[].spread = point ของ symbol — XAUUSDm digits=3
    (point 0.001) ขณะ sim ใช้ convention 0.01/pt (Dukascopy 2-digit) → หาร 10
    (evidence: ค่า 160-400 = $0.16-0.40 สมจริง Exness · TRELLIS-009 §10 วัด Δ~spread = $0.33)"""
    ts, o, h, l, c, sp = [], [], [], [], [], []
    with open(EXPORT, newline="") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            ts.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
            o.append(float(p[2])); h.append(float(p[3])); l.append(float(p[4])); c.append(float(p[5]))
            sp.append(float(p[8]) / 10.0 if len(p) > 8 else 36.0)
    return dict(t=np.array(ts), o=np.array(o), h=np.array(h), l=np.array(l), c=np.array(c),
                sp=np.array(sp))


def to_bt(m1, rule):
    """UTC+0 -> BT-clock: บวก shift (dst_shift_minutes นิยามเป็น 'ลบจาก BT ได้ UTC' จึงบวกกลับ)"""
    out = dict(m1)
    out["t"] = m1["t"] + dst_shift_minutes(m1["t"], rule).astype("timedelta64[m]")
    return out


def main():
    raw = load_export()
    print(f"export: {raw['t'][0]} .. {raw['t'][-1]} UTC+0 · {len(raw['t'])} bars"
          f" · spread median {np.median(raw['sp']):.0f}pt")
    for rule, label in [("eu", "EU-DST (ถูกต้อง — ตรง EA หลังแก้)"),
                        ("us", "US-DST (กฎเดิมของ EA ก่อนแก้ — เทียบ)")]:
        m1 = to_bt(raw, rule)
        start = int(np.searchsorted(m1["t"], HOLDOUT_START))
        tr = run(m1, start, **DEPLOY_CFG)
        print(f"\n== holdout 24 ก.พ.-3 ก.ค. 2026 · clock {label} ==")
        p = stats(tr, f"holdout-{rule}")
        if len(p):
            # รายเดือน + แยกทิศไม่ได้จาก canonical tuple (ไม่มี dir) — รายเดือนพอสำหรับ re-baseline
            mon = {}
            for x in tr:
                mon.setdefault(str(x[0])[:7], []).append(x[1])
            print("    " + " ".join(f"{m}:{np.sum(v):+.0f}" for m, v in sorted(mon.items())))


if __name__ == "__main__":
    main()
