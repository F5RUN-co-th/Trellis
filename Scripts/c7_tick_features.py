#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
c7_tick_features.py — TRELLIS-010 Stage C · Card C7 infra **v2** (แก้ตาม Engineer
BLOCKING-1/2: v1 วัด bar i = execution bar → ticks เกิดหลัง entry = within-bar
lookahead + วัดผิด bar จาก hypothesis · frozen v1 SHA f1bdba72… = โมฆะสำหรับ H7)

v2: วัดบน **SIGNAL BAR j** (บาร์ที่ close ทะลุ Asian level — bar ก่อน entry ใน
bar-sequence เดียวกับที่ sim ใช้: j = index(entry_bar) − 1 แบบ sequence-position
ไม่ใช่ลบ 1 นาทีเลขคณิต จึงปลอด missing-bar shift) → feature รู้ค่า ณ close ของ j
ก่อน entry ที่ open ของ i = ไม่มี lookahead + P3 gate deployable จริง

FIREWALL: อ่าน day_facts เฉพาะ date/status/traded/entry_time (no P&L) · R-scale
สำหรับ confound control อ่านจาก h0_features (ไฟล์ P&L-free): asian_width

Features (as-of close ของ bar j · baseline rolling past-only):
| column          | นิยาม |
|-----------------|-------|
| tick_sig        | tick-count ของ signal bar j |
| rel_tick_sig    | tick_sig / median(tick ของ minute-of-day ของ j บน trailing
|                 | 60 ok-days, ≥30 obs) |
| rjR             | (high_j − low_j) / asian_width — ขนาดบาร์ทะลุเทียบ R (Engineer
|                 | MANDATORY-3: bar-size confound control · corr(tick_j,range_j) raw +0.444) |
| asian_ticks / rel_tick_asian / tick_cov_asian — เหมือน v1 (สะอาดอยู่แล้ว as-of 08:00) |

Sparse-era / ok-days-only baseline / settlement note: เหมือน v1 (ดู Progress Log)
Usage: python c7_tick_features.py → Research/h0/h0_tickfeat_2012_2020.csv + .sha256 (v2)
"""
import csv
import hashlib
import sys
from collections import deque
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(r"D:/workspace/Doc/T.me/R&D/Gloo/Data")
ROOT = Path(__file__).parent.parent
FACTS = ROOT / "Research/h0/h0_day_facts_2012_2020.csv"
FEAT = ROOT / "Research/h0/h0_features_2012_2020.csv"
OUT_CSV = ROOT / "Research/h0/h0_tickfeat_2012_2020.csv"
OUT_SHA = ROOT / "Research/h0/h0_tickfeat_2012_2020.sha256"

YEARS = list(range(2011, 2021))
ROLL_D, MIN_OBS = 60, 30

COLS = ["date", "tick_sig", "rel_tick_sig", "rjR", "asian_ticks", "rel_tick_asian",
        "tick_cov_asian", "base_obs_sig"]


def load_m1_ticks():
    """t, h, l, tick — sequence เดียวกับ sim (อ่านไฟล์เรียงปี ไม่แตะ close/open/P&L)"""
    t, hh, ll, v = [], [], [], []
    for y in YEARS:
        with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                t.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
                hh.append(float(p[3]))
                ll.append(float(p[4]))
                v.append(float(p[6]))
    return np.array(t), np.array(hh), np.array(ll), np.array(v)


def main():
    with open(FACTS, encoding="utf-8") as f:
        rows = [{k: r[k] for k in ("date", "status", "traded", "entry_time")}
                for r in csv.DictReader(ln for ln in f if not ln.startswith("#"))]
    day_meta = {r["date"]: r for r in rows}
    with open(FEAT, encoding="utf-8") as f:
        aw_of = {r["date"]: (float(r["asian_width"]) if r["asian_width"] else np.nan)
                 for r in csv.DictReader(ln for ln in f if not ln.startswith("#"))}

    t, h, l, v = load_m1_ticks()
    pos = {str(x): k for k, x in enumerate(t)}
    tmin = t.astype("datetime64[m]").astype(np.int64)
    day_idx = (tmin // 1440).astype(int)
    hour = (tmin // 60) % 24
    uniq, fidx = np.unique(day_idx, return_index=True)
    bounds = list(zip(uniq.tolist(), fidx.tolist(), np.r_[fidx[1:], len(t)].tolist()))

    minute_hist = {}
    asian_hist = deque(maxlen=ROLL_D)
    out = []
    cov_year = {}
    n_sig = n_rel = 0
    for d_idx, i0, i1 in bounds:
        dts = str(np.datetime64(int(d_idx), "D"))
        am = (hour[i0:i1] >= 1) & (hour[i0:i1] < 8)
        asian_ticks = float(v[i0:i1][am].sum())
        cov = int(am.sum()) / 420.0
        meta = day_meta.get(dts)
        status = meta["status"] if meta else ("warmup" if dts < "2012" else "absent")

        if meta:
            base_a = np.median(asian_hist) if len(asian_hist) >= MIN_OBS else np.nan
            rel_a = asian_ticks / base_a if np.isfinite(base_a) and base_a > 0 else np.nan
            ts = rel_s = rjr = np.nan
            nobs = 0
            if meta["traded"] == "1" and meta["entry_time"]:
                k = pos.get(dts + "T" + meta["entry_time"])
                # SIGNAL BAR j = ตำแหน่งก่อนหน้าใน sequence (นิยามเดียวกับ sim j=i-1)
                if k is not None and k > 0 and str(t[k - 1])[:10] == dts:
                    j = k - 1
                    ts = v[j]
                    n_sig += 1
                    aw = aw_of.get(dts, np.nan)
                    rjr = (h[j] - l[j]) / aw if np.isfinite(aw) and aw > 0 else np.nan
                    mod = int(tmin[j] % 1440)
                    hist = minute_hist.get(mod)
                    if hist is not None and len(hist) >= MIN_OBS:
                        base = np.median(hist)
                        nobs = len(hist)
                        if base > 0:
                            rel_s = ts / base
                            n_rel += 1
            out.append([dts, ts, rel_s, rjr, asian_ticks, rel_a, round(cov, 3), nobs])
            cov_year.setdefault(dts[:4], []).append(cov)

        if status == "ok" or (dts < "2012" and status == "warmup"):
            asian_hist.append(asian_ticks)
            for jj in range(i0, i1):
                mod = int(tmin[jj] % 1440)
                minute_hist.setdefault(mod, deque(maxlen=ROLL_D)).append(float(v[jj]))

    print("== v2 (signal bar j) · sparse-era coverage ==")
    for y in sorted(cov_year):
        print(f"  {y}: mean={np.mean(cov_year[y]):.3f}")
    print(f"days out={len(out)} · signal bar matched={n_sig} · rel_tick_sig={n_rel}")

    def fmt(x):
        return "" if isinstance(x, float) and not np.isfinite(x) else (
            f"{x:.6g}" if isinstance(x, float) else str(x))

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        f.write(f"# h0_tickfeat v2 (SIGNAL BAR j — Engineer BLOCKING-1 fix; v1 f1bdba72 "
                f"โมฆะ) | ROLL_D={ROLL_D} MIN_OBS={MIN_OBS} | Dukascopy M1 col6 | "
                f"baseline ok-days past-only | reads day_facts date/status/traded/"
                f"entry_time + h0_features asian_width ONLY (no P&L)\n")
        w = csv.writer(f)
        w.writerow(COLS)
        for r in out:
            w.writerow([fmt(x) for x in r])
    sha = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
    OUT_SHA.write_text(f"{sha}  {OUT_CSV.name}\n", encoding="utf-8")
    print(f"wrote {OUT_CSV} rows={len(out)}\nSHA256 v2 = {sha} (frozen)")


if __name__ == "__main__":
    main()
