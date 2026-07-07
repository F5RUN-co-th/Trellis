#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
c9_dc_features.py — TRELLIS-010 Stage C · Card C9 infra: Directional-Change state
ณ close ของ signal bar j (Glattfelder et al. 2011 — นิยาม verify จาก full PDF แล้ว:
"price change Δx_dc from the last high or low (extrema), in up or down mode ...
overshoot associated with the previous directional change")

DoF ทั้งหมด fix ex-ante (Engineer C9-3):
  window   = bars วันนี้ 08:00 → close ของ j (δ final ณ 08:00 · as-of glossary C7)
  δ        = 0.5 × asian_width (ค่าเดียว ผูก scale ระบบ — ไม่ sweep; ค่าอื่น = card ใหม่)
  algo     = classic DC: up mode → running max, DC-down เมื่อ close ≤ max − δ (mirror)
             เริ่ม unset จนกว่าจะมี move ≥ δ จาก extremum แรก
  os_units = (close_j − dc_confirm_price) / δ ของ mode ปัจจุบัน (ระยะ overshoot
             หน่วย δ — scaling law: avg overshoot ≈ 1δ)
  aligned  = mode ณ close ของ j ตรงทิศไม้ (long=up / short=down)

FIREWALL: อ่าน day_facts เฉพาะ date/status/traded/entry_time/dir · asian_width จาก
h0_features (P&L-free) · M1 closes เท่านั้น
Output: date, dc_mode_aligned (1/0/-1=undef), os_units, n_dc (events ใน window),
        dc_state (FRESH<1δ / MID / EXTENDED≥2δ / OPPOSED / UNDEF)
Usage: python c9_dc_features.py → Research/h0/h0_dcfeat_2012_2020.csv + .sha256
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(r"D:/workspace/Doc/T.me/R&D/Gloo/Data")
ROOT = Path(__file__).parent.parent
FACTS = ROOT / "Research/h0/h0_day_facts_2012_2020.csv"
FEAT = ROOT / "Research/h0/h0_features_2012_2020.csv"
OUT_CSV = ROOT / "Research/h0/h0_dcfeat_2012_2020.csv"
OUT_SHA = ROOT / "Research/h0/h0_dcfeat_2012_2020.sha256"
YEARS = list(range(2011, 2021))
DELTA_FRac = 0.5                     # δ = 0.5 × asian_width — ex-ante ค่าเดียว

COLS = ["date", "dc_mode_aligned", "os_units", "os_canon", "n_dc", "dc_state",
        "dc_state_canon"]


def label(os_u):
    return "FRESH" if os_u < 1.0 else ("EXTENDED" if os_u >= 2.0 else "MID")


def dc_state_at(closes, delta):
    """classic DC dissection บน closes[0..] · คืน (mode, os_units, os_canon, n_dc)
    mode: +1 up / -1 down / 0 unset · os_units = (c_last − dcc)/δ โดย dcc = close ที่
    confirm (นิยาม frozen เดิม) · os_canon = วัดจาก threshold level ตาม Glattfelder
    canonical (up: lo+δ · down: hi−δ) — v2 เพิ่มตาม SE LOW-4/M4 (sensitivity)"""
    mode, n_dc = 0, 0
    hi = lo = closes[0]
    dcc = dcc_canon = np.nan
    for c in closes:
        if mode == 0:
            hi, lo = max(hi, c), min(lo, c)
            if c >= lo + delta:
                mode, dcc, dcc_canon, hi = 1, c, lo + delta, c
                n_dc += 1
            elif c <= hi - delta:
                mode, dcc, dcc_canon, lo = -1, c, hi - delta, c
                n_dc += 1
        elif mode == 1:
            hi = max(hi, c)
            if c <= hi - delta:
                mode, dcc, dcc_canon, lo = -1, c, hi - delta, c
                n_dc += 1
        else:
            lo = min(lo, c)
            if c >= lo + delta:
                mode, dcc, dcc_canon, hi = 1, c, lo + delta, c
                n_dc += 1
    if mode == 0:
        return 0, np.nan, np.nan, 0
    if mode == 1:
        return mode, (closes[-1] - dcc) / delta, (closes[-1] - dcc_canon) / delta, n_dc
    return mode, (dcc - closes[-1]) / delta, (dcc_canon - closes[-1]) / delta, n_dc


def main():
    with open(FACTS, encoding="utf-8") as f:
        meta = {r["date"]: r for r in
                ({k: x[k] for k in ("date", "status", "traded", "entry_time", "dir")}
                 for x in csv.DictReader(ln for ln in f if not ln.startswith("#")))}
    with open(FEAT, encoding="utf-8") as f:
        aw_of = {r["date"]: (float(r["asian_width"]) if r["asian_width"] else np.nan)
                 for r in csv.DictReader(ln for ln in f if not ln.startswith("#"))}

    t, c = [], []
    for y in YEARS:
        with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                t.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
                c.append(float(p[5]))
    t = np.array(t)
    c = np.array(c)
    pos = {str(x): k for k, x in enumerate(t)}
    tmin = t.astype("datetime64[m]").astype(np.int64)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)

    out = []
    stats = {}
    for dts, m in sorted(meta.items()):
        rec = [dts, "", "", "", "", "", ""]
        if m["traded"] == "1" and m["entry_time"]:
            k = pos.get(dts + "T" + m["entry_time"])
            aw = aw_of.get(dts, np.nan)
            if k is not None and k > 0 and str(t[k - 1])[:10] == dts \
                    and np.isfinite(aw) and aw > 0:
                j = k - 1
                # window: bars วันเดียวกัน hour>=8 จนถึง j (รวม j — close ของ j คือจุดวัด)
                q0 = j
                while q0 - 1 >= 0 and day[q0 - 1] == day[j] and hour[q0 - 1] >= 8:
                    q0 -= 1
                mode, os_u, os_c, n_dc = dc_state_at(c[q0:j + 1], DELTA_FRac * aw)
                d = int(m["dir"])
                if mode == 0:
                    st = stc = "UNDEF"
                    alg = -1
                elif mode == d:
                    alg = 1
                    st, stc = label(os_u), label(os_c)
                else:
                    st = stc = "OPPOSED"
                    alg = 0
                rec = [dts, alg, (f"{os_u:.4f}" if np.isfinite(os_u) else ""),
                       (f"{os_c:.4f}" if np.isfinite(os_c) else ""), n_dc, st, stc]
                stats[st] = stats.get(st, 0) + 1
        out.append(rec)

    print(f"dc_state occupancy: {dict(sorted(stats.items()))}")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        f.write(f"# h0_dcfeat v2 (+os_canon SE M4; v1 faff68a3 superseded) | delta=0.5*asian_width ex-ante | window 08:00→close(j) "
                f"| DC def verified from arXiv 0809.1040 full text | reads day_facts "
                f"date/status/traded/entry_time/dir + h0_features asian_width ONLY\n")
        w = csv.writer(f)
        w.writerow(COLS)
        for r in out:
            w.writerow(r)
    sha = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
    OUT_SHA.write_text(f"{sha}  {OUT_CSV.name}\n", encoding="utf-8")
    print(f"wrote {OUT_CSV}\nSHA256 = {sha} (frozen)")


if __name__ == "__main__":
    main()
