#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
c6_poke_features.py — TRELLIS-010 Stage C · Card C6 infra: pre-break poke/sweep
features (Gate B mandates C6-1/2/3 + บทเรียน C7: ทุกอย่าง as-of ≤ close ของ SIGNAL
BAR j — ไม่มีข้อมูลจาก execution bar i)

ที่มา (Stage B): osler-stop-cluster-asymmetry + osler-reversal-vs-continuation-duration
(T-STRONG ทั้งคู่): TP orders กระจุก*ที่* level → การแตะ-ไม่ผ่าน (poke) = reversal flow
ทำงาน · Osler: reversal significance ตาย <30 นาที → **window จำกัด 60 นาทีก่อน close
ของ j** (C6-2) พร้อม recency split ≤30 / 31-60 เป็น descriptive

นิยาม (pin ตาม C6-3 · ฝั่งตามทิศไม้จริง dir):
  poke  = bar ใน window ที่ **เจาะ level แต่ close กลับเข้า**: LONG: high > ash ∧
          close ≤ ash · SHORT: low < asl ∧ close ≥ asl — level fix แล้ว ณ 08:00
  blocked_cross (descriptive แยก — ไม่ใช่ poke): close ทะลุ level ใน window แต่ sim
  ไม่ได้เข้า (filter block/ยัง) — ประกาศ ex-ante ว่าไม่นับเป็น poke
  window = bars ที่ timestamp ∈ [t_j − 60min, t_j) ∧ hour ≥ 8 ∧ วันเดียวกัน
  poke_rate = n_pokes / avail_bars (C6-1: rate ไม่ใช่ raw count — คุมความยาว window
  ที่ต่างกันตอน entry เร็ว) · POKED = n_pokes ≥ 1 (contrast หลักของ card)

FIREWALL: อ่าน day_facts เฉพาะ date/status/traded/entry_time/dir (no P&L) ·
ash/asl คำนวณจาก M1 สูตรเดียวกับ sim (accumulate hour 1-7)

Output columns: date, n_pokes, poke_rate, poked, n_pokes_30 (≤30min), avail_bars,
blocked_crosses, window_min
Usage: python c6_poke_features.py → Research/h0/h0_pokefeat_2012_2020.csv + .sha256
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
OUT_CSV = ROOT / "Research/h0/h0_pokefeat_2012_2020.csv"
OUT_SHA = ROOT / "Research/h0/h0_pokefeat_2012_2020.sha256"
YEARS = list(range(2011, 2021))
WIN_MIN = 60                     # ex-ante (Osler decay <30-120min) · recency 30 desc

COLS = ["date", "n_pokes", "poke_rate", "poked", "n_pokes_30", "avail_bars",
        "blocked_crosses", "window_min"]


def main():
    with open(FACTS, encoding="utf-8") as f:
        meta = {r["date"]: r for r in
                ({k: x[k] for k in ("date", "status", "traded", "entry_time", "dir")}
                 for x in csv.DictReader(ln for ln in f if not ln.startswith("#")))}

    t, h, l, c = [], [], [], []
    for y in YEARS:
        with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                t.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
                h.append(float(p[3]))
                l.append(float(p[4]))
                c.append(float(p[5]))
    t = np.array(t); h = np.array(h); l = np.array(l); c = np.array(c)
    pos = {str(x): k for k, x in enumerate(t)}
    tmin = t.astype("datetime64[m]").astype(np.int64)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)

    # ash/asl ต่อวัน (สูตร sim: accumulate 1<=hour<8)
    uniq, fidx = np.unique(day, return_index=True)
    lv = {}
    for d_idx, i0, i1 in zip(uniq.tolist(), fidx.tolist(),
                             np.r_[fidx[1:], len(t)].tolist()):
        am = (hour[i0:i1] >= 1) & (hour[i0:i1] < 8)
        if am.any():
            lv[str(np.datetime64(int(d_idx), "D"))] = (float(h[i0:i1][am].max()),
                                                       float(l[i0:i1][am].min()))

    out = []
    for dts, m in sorted(meta.items()):
        rec = [dts, "", "", "", "", "", "", ""]
        if m["traded"] == "1" and m["entry_time"] and dts in lv:
            k = pos.get(dts + "T" + m["entry_time"])
            if k is not None and k > 0 and str(t[k - 1])[:10] == dts:
                j = k - 1                       # signal bar (decision = close ของ j)
                tj = tmin[j]
                ash, asl = lv[dts]
                d = int(m["dir"])
                npk = npk30 = avail = blocked = 0
                q = j - 1
                while q >= 0 and tmin[q] >= tj - WIN_MIN and day[q] == day[j] \
                        and hour[q] >= 8:
                    avail += 1
                    if d == 1:
                        if h[q] > ash and c[q] <= ash:
                            npk += 1
                            if tmin[q] >= tj - 30:
                                npk30 += 1
                        elif c[q] > ash:
                            blocked += 1
                    else:
                        if l[q] < asl and c[q] >= asl:
                            npk += 1
                            if tmin[q] >= tj - 30:
                                npk30 += 1
                        elif c[q] < asl:
                            blocked += 1
                    q -= 1
                wmin = int(tj - max(tmin[q + 1], tj - WIN_MIN)) if avail else 0
                rec = [dts, npk, (round(npk / avail, 4) if avail else ""),
                       int(npk >= 1), npk30, avail, blocked,
                       min(WIN_MIN, wmin if avail else 0)]
        out.append(rec)

    n_tr = sum(1 for r in out if r[1] != "")
    n_poked = sum(1 for r in out if r[3] == 1)
    n_zero_avail = sum(1 for r in out if r[1] != "" and r[5] == 0)
    print(f"traded matched={n_tr} · POKED={n_poked} ({100*n_poked/max(n_tr,1):.1f}%) · "
          f"avail_bars=0 (entry ทันที 08:0x): {n_zero_avail}")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        f.write(f"# h0_pokefeat v1 | WIN_MIN={WIN_MIN} | as-of close ของ signal bar j "
                f"(CLAUDE.md glossary เวลาเทรด) | poke=pierce-but-close-inside ฝั่ง dir | "
                f"blocked_cross แยก desc | reads day_facts date/status/traded/entry_time/"
                f"dir ONLY (no P&L)\n")
        w = csv.writer(f)
        w.writerow(COLS)
        for r in out:
            w.writerow(r)
    sha = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
    OUT_SHA.write_text(f"{sha}  {OUT_CSV.name}\n", encoding="utf-8")
    print(f"wrote {OUT_CSV}\nSHA256 = {sha} (frozen)")


if __name__ == "__main__":
    main()
