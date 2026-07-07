#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exhaustion_fade.py — TRELLIS-010 v3 Step 2 · exhaustion-entry FADE (mechanism-fade v0)

mirror-fade (flip-at-breakout) ตายแล้ว (fade_dataset.py: WR 12%) — เพราะเข้าผิดจุด
(breakout ไม่ reverse ทันที) · exhaustion-fade = เข้า**หลัง overshoot ที่ DC-reversal**
(ราคายืดเกิน level แล้วเริ่มกลับ = จุดที่ mechanism reversion เกิดจริง)

MECHANISM (root-cause · ไม่ใช่ P&L): breakout ยืดเกิน level → momentum decay/exhaustion
→ reversion กลับเข้ากรอบ · เข้า fade ณ จุดที่ DC ยืนยัน reversal (ราคาหด δ จาก extreme)

DoF pin ex-ante (ก่อนรัน · ให้ Engineer review — mirror C9 frozen):
  · δ = 0.5 × asian_width (C9 frozen)
  · overshoot ≥ 1.0δ (= SPENT · C9 threshold) จึงมีสิทธิ์ fade
  · reversal trigger = close หด ≥ δ จาก extreme (DC confirm)
  · fade entry = close ของ reversal bar · dir = −breakout-dir (กลับเข้ากรอบ)
  · stop = overshoot extreme (+ SLIP) · target = level เดิม (reversion) · EOD 23:00 · 1/วัน
  · **หมายเหตุ (Engineer): fade risk ≈ retrace δ ≈ 0.5R · NOT risk-normalized กับ v4 (1R)** ·
    cost = spread+slip เหมือน v4
สนาม SEARCH · **falsify ที่ standalone fade P&L (ไม่ใช่ fade−cont ที่ inflated โดย cont-concentration)**
· scope = "overshoot-of-level ไม่ใช่ exhaustion proxy บน OHLCV" ไม่ใช่ "fade ตายทั้งแนว"
Usage: python exhaustion_fade.py
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from brain_v1_run import load_ctx, walk, cell_of, PT, SLIP_IN, SLIP_STOP

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent.parent / "Research" / "h0"
DELTA_FRAC = 0.5
OS_MIN = 1.0        # overshoot ≥ 1.0δ = SPENT


def exhaustion_trade(ctx, k, d, ash, asl, aw):
    """หา exhaustion-fade setup หลัง breakout bar k · คืน (pnl, hit) หรือ (nan, reason)"""
    o, h, l, c, sp = ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["sp"]
    hour, day, dow = ctx["hour"], ctx["day"], ctx["dow"]
    n = len(o)
    delta = DELTA_FRAC * aw
    level = ash if d == 1 else asl              # level ที่ breakout ทะลุ
    ext = c[k]                                  # extreme ของ overshoot (เริ่มที่ entry)
    overshot = False
    edy = day[k]
    q = k + 1
    while q < n and day[q] == edy:
        if hour[q] >= (20 if dow[q] == 5 else 23):
            return np.nan, "eod-no-setup"
        # อัปเดต extreme ทิศ breakout
        ext = max(ext, h[q]) if d == 1 else min(ext, l[q])
        os_now = (ext - level) * d              # overshoot beyond level (ทิศ breakout)
        if not overshot and os_now >= OS_MIN * delta:
            overshot = True
        if overshot:
            # reversal trigger: close หด ≥ δ จาก extreme (ทิศกลับ)
            retr = (ext - c[q]) * d
            if retr >= delta:
                # เข้า FADE dir = −d ณ close ของ q
                df = -d
                # entry cost convention เดียวกับ v4: long = +sp+slip (ask) · short = −slip (bid)
                entf = c[q] + sp[q] * PT + SLIP_IN if df == 1 else c[q] - SLIP_IN
                stopf = ext + SLIP_STOP if df == -1 else ext - SLIP_STOP  # stop เลย extreme
                # simulate forward: target = level (reversion) · stop · EOD
                p = q + 1
                while p < n and day[p] == edy:
                    if hour[p] >= (20 if dow[p] == 5 else 23):
                        exx = c[p] if df == 1 else c[p] + sp[p] * PT
                        return (exx - entf) * df, "eod"
                    hit_stop = (h[p] >= stopf) if df == -1 else (l[p] <= stopf)
                    if hit_stop:
                        px = (max(stopf, o[p]) if df == -1 else min(stopf, o[p]))
                        exx = px if df == 1 else px + sp[p] * PT
                        return (exx - entf) * df, "stop"
                    hit_tgt = (h[p] >= level) if df == 1 else (l[p] <= level)  # target=level ทิศ fade
                    if hit_tgt:
                        exx = level if df == 1 else level + sp[p] * PT
                        return (exx - entf) * df, "target"
                    p += 1
                return np.nan, "eof"
        q += 1
    return np.nan, "no-setup" if not overshot else "no-reversal"


def main():
    ctx = load_ctx()
    dc = {r["date"]: r for r in csv.DictReader(
        ln for ln in open(DIR / "h0_dcfeat_2012_2020.csv", encoding="utf-8")
        if not ln.startswith("#"))}
    feat = {r["date"]: r for r in csv.DictReader(
        ln for ln in open(DIR / "h0_features_2012_2020.csv", encoding="utf-8")
        if not ln.startswith("#"))}

    rows = []
    for dts, f in sorted(ctx["facts"].items()):
        if f["traded"] != "1":
            continue
        k = ctx["pos"][dts + "T" + f["entry_time"]]
        d = int(f["dir"])
        ash, asl = ctx["lv"][dts]
        aw = float(feat[dts]["asian_width"]) if feat[dts]["asian_width"] else (ash - asl)
        pnl_c = float(f["pnl"])
        pnl_x, reason = exhaustion_trade(ctx, k, d, ash, asl, aw)
        rows.append(dict(date=dts, yr=dts[:4], pnl_c=pnl_c,
                         pnl_x=pnl_x, xreason=reason,
                         dcs=dc[dts]["dc_state"], cell=cell_of(ctx, dts)))

    setup = [r for r in rows if np.isfinite(r["pnl_x"])]
    xs = np.array([r["pnl_x"] for r in setup])
    print(f"=== exhaustion-fade v0 · field=SEARCH · n_traded={len(rows)} ===")
    print(f"setup เกิด (overshoot≥1δ + reversal) = {len(setup)}/{len(rows)} = "
          f"{100*len(setup)/len(rows):.1f}% ของวันเทรด")
    from collections import Counter
    print(f"exit reasons: {dict(Counter(r['xreason'] for r in setup))}")
    print(f"pnl_exfade: sum={xs.sum():+.1f} exp={xs.mean():+.3f} WR={100*(xs>0).mean():.1f}%")
    # เทียบ continuation บนวัน setup เดียวกัน
    cc = np.array([r["pnl_c"] for r in setup])
    print(f"\nบนวัน setup เดียวกัน (n={len(setup)}):")
    print(f"  continuation (v4): sum={cc.sum():+.1f} exp={cc.mean():+.3f}")
    print(f"  exhaustion-fade  : sum={xs.sum():+.1f} exp={xs.mean():+.3f}")
    print(f"  **fade − cont = {(xs-cc).sum():+.1f}** (>0 = exhaustion-fade ชนะบน setup population)")
    # SPENT subset (C9 signal)
    sp_mask = np.array([r["dcs"] in ("MID", "EXTENDED") for r in setup])
    if sp_mask.any():
        print(f"\n  บน SPENT subset (n={sp_mask.sum()}): cont={cc[sp_mask].sum():+.1f} "
              f"fade={xs[sp_mask].sum():+.1f} fade−cont={(xs[sp_mask]-cc[sp_mask]).sum():+.1f}")
    print("\n⚠ v0 · DoF (δ/overshoot/reversal/stop/target) pin ex-ante รอ Engineer review · "
          "setup=realtime-detectable (as-of · ไม่ hindsight) · เทียบ continuation บน population เดียวกัน")


if __name__ == "__main__":
    main()
