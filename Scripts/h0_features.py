#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_features.py — TRELLIS-010 Stage H0 deliverable 1a: day-level exogenous regime features
2012–2020 (search window) + data-completeness gate (เงื่อนไข MED-2)

FIREWALL (Engineer HIGH-6): ไฟล์นี้ผลิต features เท่านั้น — ไม่มีคอลัมน์ P&L ใดๆ /
  This file produces features ONLY — no P&L columns. Output frozen ด้วย SHA256 manifest
  ก่อน h0_join_pnl.py แนบ P&L ในไฟล์แยก → reviewer audit ได้ว่า threshold ใน hypothesis
  card อ้างเฉพาะ column ที่นิยามก่อนเห็น P&L (CLAUDE.md §⭐)

สนามวัด: SIM search field (Dukascopy M1 CSV, BT clock EET) — ไม่แตะ 2021+ (lockbox+guard)
Data scope (Engineer HIGH-4): load 2011 เป็น feature-warmup เท่านั้น · output rows = 2012–2020
  ตรง convention canonical (dual_asian_sim "all" mode load 2011 เป็น warmup ของ 2012–2020)

Feature spec (Engineer HIGH-5 — ทุกตัวมี as_of + normalization window · rolling past-only
เท่านั้น ห้าม full-sample percentile):
| column        | as_of        | window                     | นิยาม / definition |
|---------------|--------------|----------------------------|--------------------|
| asian_width   | 08:00 วัน D  | วัน D 01:00–07:59          | max(h)−min(l) ช่วง Asian = R ของ sim (สูตรเดียว dual_asian_sim:58-60) |
| overnight_gap | bar แรกวัน D | —                          | open(bar แรก D) − close(bar สุดท้ายวันเทรดก่อนหน้า) — signed |
| prev_range    | 00:00 วัน D  | วันเทรดก่อนหน้า            | max(h)−min(l) ทั้งวันก่อนหน้า |
| rv_prev       | 00:00 วัน D  | วันเทรดก่อนหน้า            | sqrt(Σ Δlog(close)²) M1 ของวันก่อนหน้า |
| rv_pct250     | 00:00 วัน D  | 250 ok-days ก่อนหน้า (past-only, exclude ตัวเอง) | percentile rank ของ rv_prev |
| range_exp     | 00:00 วัน D  | 20 ok-days ก่อนวันก่อนหน้า | prev_range / median(range 20 วัน) |
| slope_08      | 08:00 วัน D  | EMA_P=2880 / SLOPE_B=1440  | es[j]/c[j] ที่ bar สุดท้ายก่อน 08:00 (สูตร es เดียวกับ sim) |
| slope_pct250  | 08:00 วัน D  | 250 ok-days ก่อนหน้า (past-only) | percentile rank ของ slope_08 |
| dow           | —            | —                          | 0=Mon .. 4=Fri |

Completeness gate (Engineer HIGH-3 — สอง lens + แยก holiday ออกจาก hole · threshold มาจาก
การวัด distribution จริง ไม่ใช่ hardcode 1380 ซึ่งจะ flag 39% ของวันผิดๆ เพราะ M1 bar
หายตามธรรมชาติเมื่อนาทีนั้นไม่มี tick ในตลาดเงียบ):
  โครงสร้าง session ที่วัดได้จริง (diag 2026-07-04): ยุค 2012–2017 มี settlement bar
  ที่ hour 0 แล้วเว้น daily break ~60 นาทีก่อน session เปิด 01:00 (pattern (start_hour=0,
  dur=60) = 140/145 ของ gap≥55min ในปี 2012) → gap lens ต้องคำนวณบน SESSION bars
  (hour ≥ 1) เท่านั้น ไม่งั้น flag break ประจำวันเป็น hole ผิด 500+ วัน
  hole   = gap ≥ 60 นาทีภายใน session — data fault (bars หายเป็นบล็อกกลาง session)
  short  = session ไม่เต็ม: bar แรกของ session > 01:05 (late open เช่น Apr 2014 เปิด
           02:00) หรือ bar สุดท้าย < 22:00 (early close เช่น US holiday 20:00,
           Christmas Eve 20:45) — ไม่ใช่ hole แต่ RV/range/Asian วันนั้น bias
  nosess = มีแต่ settlement bars (hour 0) ไม่มี session เลย (เช่น Good Friday 2014)
  ok     = นอกเหนือจากนั้น (bars/วัน ต่ำเพราะตลาดเงียบ = ปกติ ไม่ flag)
  หมายเหตุ: features (rv/range) คำนวณจาก bars ทั้งวันรวม settlement bar — ตรงกับที่
  sim เห็น (sim ประมวล bar hour 0 ด้วย)
กติกา: rolling windows (rv_pct250/range_exp/slope_pct250) สะสมจาก ok-days เท่านั้น
  (กัน contamination) · window ไม่เต็ม → NaN + warmup_incomplete=1 (HIGH-4 ห้ามค่าปลอม) ·
  วันหาย midweek ทั้งวัน = ไม่มี row (ไม่มี bar) → รายงานดังใน stdout + วันถัดไปมี
  days_since_prev > 1 · ไม่มี silent drop

Usage: python h0_features.py   → Research/h0/h0_features_2012_2020.csv + .sha256 + report
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dual_asian_sim import load_full          # reuse loader (Engineer LOW-9 — ห้าม reimplement)
from entry_platform import ema

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

YEARS = list(range(2011, 2021))               # 2011 = warmup เท่านั้น (HIGH-4)
OUT_START = 2012
EMA_P, SLOPE_B = 2880, 1440                   # ต้องตรง DEPLOY_CFG (join script assert ซ้ำ)
ROLL_N, EXP_N = 250, 20                       # rolling past-only windows
HOLE_GAP_MIN = 60                             # lens 1: gap ≥ 60min ภายใน session = hole
SESS_START_MIN = 60                           # session เปิด 01:00 — bar hour 0 = settlement
SHORT_FIRST_MIN, SHORT_LAST_MIN = 65, 22 * 60   # lens 2: เปิดช้ากว่า 01:05 / ปิดก่อน 22:00

OUT_DIR = Path(__file__).parent.parent / "Research" / "h0"
OUT_CSV = OUT_DIR / "h0_features_2012_2020.csv"
OUT_SHA = OUT_DIR / "h0_features_2012_2020.sha256"

COLS = ["date", "dow", "status", "bars", "sess_bars", "max_gap_min", "first_sess_min",
        "last_sess_min", "days_since_prev", "prev_ok", "warmup_incomplete", "asian_bars",
        "asian_width", "overnight_gap", "prev_range", "rv_prev", "rv_pct250", "range_exp",
        "slope_08", "slope_pct250"]


def rank_pct(v, window):
    """percentile rank ของ v ใน window (past-only) — NaN ถ้าคำนวณไม่ได้"""
    if not np.isfinite(v) or len(window) == 0:
        return np.nan
    return 100.0 * float(np.mean(np.array(window) < v))


def fmt(v):
    if isinstance(v, float):
        return "" if not np.isfinite(v) else f"{v:.6g}"
    return str(v)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    m1 = load_full(YEARS)
    c, h, l, o, t = m1["c"], m1["h"], m1["l"], m1["o"], m1["t"]
    e = ema(c, EMA_P)
    es = np.r_[np.full(SLOPE_B, np.nan), e[SLOPE_B:] - e[:-SLOPE_B]]   # สูตรเดียว sim
    tmin = t.astype("datetime64[m]").astype(np.int64)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)
    uniq, fidx = np.unique(day, return_index=True)
    bounds = list(zip(uniq.tolist(), fidx.tolist(), np.r_[fidx[1:], len(day)].tolist()))

    # LOW-8: first-bar-hour sanity ต่อปี (จับ discontinuity แบบ 2011=00:00 vs 2012+=01:00)
    print("== first bar per year (LOW-8 sanity) ==")
    for y in YEARS:
        i = int(np.searchsorted(t, np.datetime64(f"{y}-01-01")))
        if i < len(t):
            print(f"  {y}: {t[i]}")

    rows = []
    rv_hist, rng_hist, slope_hist = [], [], []
    prev = None
    n_status = {}
    hole_days, short_days = [], []
    gap_30_60 = 0
    bars_ok = []
    for d_idx, i0, i1 in bounds:
        dts = str(np.datetime64(int(d_idx), "D"))
        year = int(dts[:4])
        iso_dow = (d_idx + 3) % 7                      # 0=Mon (1970-01-01 = Thu)
        bars = i1 - i0
        seg_min = tmin[i0:i1]
        # gap lens บน session bars (hour >= 1) เท่านั้น — bar hour 0 = settlement print
        # ก่อน daily break (วัดจริง: pattern (0,60) ครองยุค 2012-2017 — ไม่ใช่ hole)
        mod = seg_min % 1440
        sess = seg_min[mod >= SESS_START_MIN]
        sess_bars = len(sess)
        gaps = np.diff(sess) if sess_bars > 1 else np.array([0])
        max_gap = int(gaps.max()) if sess_bars > 1 else 0
        gap_30_60 += int(((gaps >= 30) & (gaps < HOLE_GAP_MIN)).sum())
        first_min = int(sess[0] % 1440) if sess_bars else -1
        last_min = int(sess[-1] % 1440) if sess_bars else -1
        if sess_bars == 0:
            status = "nosess"
            short_days.append((dts, bars, 0, 0))
        elif max_gap >= HOLE_GAP_MIN:
            status = "hole"
            hole_days.append((dts, bars, max_gap))
        elif first_min > SHORT_FIRST_MIN or last_min < SHORT_LAST_MIN:
            status = "short"
            short_days.append((dts, bars, first_min, last_min))
        else:
            status = "ok"
            bars_ok.append(bars)

        # Asian window ของวัน D (จบก่อน entry window 08–20 → ไม่มี lookahead)
        am = (hour[i0:i1] >= 1) & (hour[i0:i1] < 8)
        asian_bars = int(am.sum())
        asian_width = (float(h[i0:i1][am].max() - l[i0:i1][am].min())
                       if asian_bars else np.nan)
        # slope as-of 08:00 (bar สุดท้ายก่อนชั่วโมง 8)
        bm = np.where(hour[i0:i1] < 8)[0]
        if len(bm):
            j = i0 + int(bm[-1])
            slope_08 = float(es[j] / c[j]) if np.isfinite(es[j]) else np.nan
        else:
            slope_08 = np.nan
        # ค่าของวัน D เอง (เข้า history หลังประมวลวันนี้เสร็จ — past-only เสมอ)
        d_range = float(h[i0:i1].max() - l[i0:i1].min())
        dlc = np.diff(np.log(c[i0:i1])) if bars > 1 else np.array([])
        d_rv = float(np.sqrt((dlc ** 2).sum())) if bars > 1 else np.nan

        if prev is not None:
            overnight_gap = float(o[i0] - prev["close"])
            prev_range, rv_prev = prev["range"], prev["rv"]
            prev_ok = 1 if prev["ok"] else 0
            days_since = int(d_idx - prev["d_idx"])
        else:
            overnight_gap = prev_range = rv_prev = np.nan
            prev_ok, days_since = 0, -1

        # past-only percentile — exclude ค่าของ prev-day ตัวเองออกจาก window
        warm = 0
        rvw = (rv_hist[:-1] if prev is not None and prev["ok"] else rv_hist)[-ROLL_N:]
        if len(rvw) >= ROLL_N:
            rv_pct250 = rank_pct(rv_prev, rvw)
        else:
            rv_pct250, warm = np.nan, 1
        rgw = (rng_hist[:-1] if prev is not None and prev["ok"] else rng_hist)[-EXP_N:]
        range_exp = (float(prev_range / np.median(rgw))
                     if len(rgw) >= EXP_N and np.isfinite(prev_range) else np.nan)
        slw = slope_hist[-ROLL_N:]
        if len(slw) >= ROLL_N:
            slope_pct250 = rank_pct(slope_08, slw)
        else:
            slope_pct250, warm = np.nan, 1

        if year >= OUT_START:
            n_status[status] = n_status.get(status, 0) + 1
            rows.append([dts, iso_dow, status, bars, sess_bars, max_gap, first_min,
                         last_min, days_since, prev_ok, warm, asian_bars, asian_width,
                         overnight_gap, prev_range, rv_prev, rv_pct250, range_exp,
                         slope_08, slope_pct250])

        # update histories (ok-days เท่านั้น — HIGH-3 กัน contamination) + prev
        if status == "ok":
            if np.isfinite(d_rv):
                rv_hist.append(d_rv)
            rng_hist.append(d_range)
            if np.isfinite(slope_08):
                slope_hist.append(slope_08)
        prev = dict(close=float(c[i1 - 1]), range=d_range, rv=d_rv,
                    ok=(status == "ok"), d_idx=d_idx)

    # วันหาย midweek ทั้งวัน (ไม่มี bar → ไม่มี row) — fail-loud report
    have = {r[0] for r in rows}
    all_d = np.arange(np.datetime64(f"{OUT_START}-01-01"), np.datetime64("2021-01-01"),
                      dtype="datetime64[D]")
    wd_mask = ((all_d.astype(int) + 3) % 7) < 5
    absent = [str(d) for d in all_d[wd_mask] if str(d) not in have]

    # ---- report ----
    ba = np.array(bars_ok)
    print(f"\n== completeness report 2012-2020 (+2011 warmup ไม่อยู่ใน output) ==")
    print(f"days out: {len(rows)}  status: {n_status}")
    print(f"bars/day ok-days: median={np.median(ba):.0f} p05={np.percentile(ba,5):.0f} "
          f"p01={np.percentile(ba,1):.0f} min={ba.min()}")
    print(f"internal gaps 30-59min ทั้งชุด (info, ไม่ flag): {gap_30_60}")
    print(f"\nHOLE days ({len(hole_days)}) — gap >= {HOLE_GAP_MIN}min ภายใน session:")
    for d, b, g in hole_days:
        print(f"  {d}  bars={b:>4}  max_gap={g}min")
    print(f"\nSHORT/NOSESS days ({len(short_days)}) — session ไม่เต็ม:")
    for d, b, f0, f1 in short_days:
        print(f"  {d}  bars={b:>4}  first={f0//60:02d}:{f0%60:02d} last={f1//60:02d}:{f1%60:02d}")
    print(f"\nABSENT midweek days ไม่มี bar เลย ({len(absent)}):")
    for d in absent:
        print(f"  {d} ({'Mon Tue Wed Thu Fri'.split()[(np.datetime64(d).astype(int)+3)%7]})")
    warm_n = sum(1 for r in rows if r[9] == 1)
    print(f"\nwarmup_incomplete rows: {warm_n} (คาด 0 — 2011 มี ~259 ok-days แต่ ROLL_N=250"
          f" อาจกิน ~ต้นปี 2012 บางส่วน ถ้า >0 ดู flag ราย row)")

    # ---- write (ไม่มีคอลัมน์ P&L — firewall) ----
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        f.write(f"# h0_features v1 | EMA_P={EMA_P} SLOPE_B={SLOPE_B} ROLL_N={ROLL_N} "
                f"EXP_N={EXP_N} HOLE_GAP_MIN={HOLE_GAP_MIN} | data: Dukascopy M1 BT-clock, "
                f"2011=warmup, output 2012-2020 | NO P&L COLUMNS (firewall HIGH-6)\n")
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([fmt(v) for v in r])
    sha = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
    OUT_SHA.write_text(f"{sha}  {OUT_CSV.name}\n", encoding="utf-8")
    print(f"\nwrote {OUT_CSV}  rows={len(rows)}")
    print(f"SHA256 = {sha}  (frozen — h0_join_pnl.py จะ verify ก่อน join)")


if __name__ == "__main__":
    main()
