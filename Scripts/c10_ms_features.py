#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
c10_ms_features.py — TRELLIS-010D · WS-2: Market-Structure state (HH/HL/LH/LL จาก
DC-swing events) + KILL-GATES ก่อนคิด budget (แผน §4 + Gate C constraints 7 ข้อ)

DoF ทั้งหมด pin ex-ante จากค่าคงที่ที่ระบบมีอยู่แล้ว (0 ตัวเลขใหม่):
  window   = **1440 นาทีย้อนหลังแบบ fixed-length** (= SLOPE_B เดิมของระบบ — horizon
             trend ที่ v4 ใช้อยู่) นับถอยจาก close ของ **bar j−1** (as-of ≤ j−1:
             ตัด bar j ทั้งแท่ง — ปิด bar-size injection ที่ฆ่า C9 · sequence-position)
  δ        = 0.5 × asian_width (ค่าเดิม C9 — frozen)
  swings   = DC dissection (algo เดียวกับ C9 ที่ clean-room ผ่านแล้ว) → จุด extremes
             ที่ยืนยันแล้ว (สลับ high/low ทุกครั้งที่ DC confirm)
  structure (ต้องมี ≥2 swing-highs + ≥2 swing-lows มิฉะนั้น UNDEF):
             UP   = last swing-high > prev ∧ last swing-low > prev  (HH∧HL)
             DOWN = mirror (LH∧LL) · MIXED = อื่นๆ
  ms_state ต่อไม้ = ALIGNED (structure ตรงทิศไม้) / OPPOSED / MIXED / UNDEF

KILL-GATES (ตายฟรี ไม่เผา budget — ตัดสินโดยเกณฑ์ที่ประกาศตรงนี้):
  K1: |corr(ALIGNED, dc FRESH/SPENT ของ C9)| — ถ้า ALIGNED ≈ FRESH (>0.4) = overshoot
      ปลอมตัว → KILL
  K2: |corr(ALIGNED, poked)| ควรต่ำ · K3: |corr(ALIGNED, rjR)| และ |corr(ALIGNED,
      entry_hour)| ≤ ~0.15 (fixed-window ต้องทำหน้าที่) · K4: vs 5 ตัวตาย ≤ ~0.15
  K5: occupancy — ALIGNED/OPPOSED ต้องมี mass พอ (per-year ไม่มี thin ระดับใช้ไม่ได้)
FIREWALL: อ่าน day_facts เฉพาะ date/status/traded/entry_time/dir — no P&L
Usage: python c10_ms_features.py → Research/h0/h0_msfeat_2012_2020.csv + kill-gate report
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
DIR = ROOT / "Research" / "h0"
YEARS = list(range(2011, 2021))
WIN_MIN = 1440                     # = SLOPE_B (ค่าคงที่เดิมของระบบ)
DELTA_FRAC = 0.5                   # = C9 frozen

COLS = ["date", "ms_structure", "ms_state", "n_swings"]


def swings_from_dc(closes, delta):
    """DC dissection → list ของ confirmed swing extremes [(kind 'H'/'L', price)]
    (extreme ของ leg ก่อนหน้า confirm เมื่อ mode สลับ — mirror algo C9)"""
    mode = 0
    hi = lo = closes[0]
    out = []
    for c in closes:
        if mode == 0:
            hi, lo = max(hi, c), min(lo, c)
            if c >= lo + delta:
                out.append(("L", lo))
                mode, hi = 1, c
            elif c <= hi - delta:
                out.append(("H", hi))
                mode, lo = -1, c
        elif mode == 1:
            hi = max(hi, c)
            if c <= hi - delta:
                out.append(("H", hi))
                mode, lo = -1, c
        else:
            lo = min(lo, c)
            if c >= lo + delta:
                out.append(("L", lo))
                mode, hi = 1, c
    return out


def structure_of(sw):
    hs = [p for k, p in sw if k == "H"]
    ls = [p for k, p in sw if k == "L"]
    if len(hs) < 2 or len(ls) < 2:
        return "UNDEF"
    if hs[-1] > hs[-2] and ls[-1] > ls[-2]:
        return "UP"
    if hs[-1] < hs[-2] and ls[-1] < ls[-2]:
        return "DOWN"
    return "MIXED"


def main():
    rd = lambda f: {r["date"]: r for r in csv.DictReader(
        ln for ln in open(DIR / f, encoding="utf-8") if not ln.startswith("#"))}
    facts = rd("h0_day_facts_2012_2020.csv")
    feat = rd("h0_features_2012_2020.csv")
    poke, dc, tick = (rd("h0_pokefeat_2012_2020.csv"), rd("h0_dcfeat_2012_2020.csv"),
                      rd("h0_tickfeat_2012_2020.csv"))
    g = lambda r, k: float(r[k]) if r.get(k) not in ("", None) else float("nan")

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

    out = []
    for dts, f in sorted(facts.items()):
        rec = [dts, "", "", ""]
        if f["traded"] == "1" and f["entry_time"]:
            k = pos.get(dts + "T" + f["entry_time"])
            aw = g(feat.get(dts, {}), "asian_width")
            if k is not None and k >= 2 and np.isfinite(aw) and aw > 0:
                jm1 = k - 2                      # bar j−1 (j = k−1 · as-of ≤ close j−1)
                q0 = int(np.searchsorted(tmin, tmin[jm1] - WIN_MIN + 1))
                sw = swings_from_dc(c[q0:jm1 + 1], DELTA_FRAC * aw)
                st = structure_of(sw)
                d = int(f["dir"])
                ms = ("UNDEF" if st == "UNDEF" else
                      "MIXED" if st == "MIXED" else
                      "ALIGNED" if (st == "UP") == (d == 1) else "OPPOSED")
                rec = [dts, st, ms, len(sw)]
        out.append(rec)

    with open(DIR / "h0_msfeat_2012_2020.csv", "w", newline="", encoding="utf-8") as f:
        f.write(f"# h0_msfeat v1 | window={WIN_MIN}min fixed (SLOPE_B) | delta=0.5*aw | "
                f"as-of close(j-1) sequence-position | swings=DC-confirmed extremes | "
                f"reads day_facts date/status/traded/entry_time/dir + features aw ONLY\n")
        w = csv.writer(f)
        w.writerow(COLS)
        for r in out:
            w.writerow(r)
    sha = hashlib.sha256((DIR / "h0_msfeat_2012_2020.csv").read_bytes()).hexdigest()
    (DIR / "h0_msfeat_2012_2020.sha256").write_text(
        f"{sha}  h0_msfeat_2012_2020.csv\n", encoding="utf-8")

    # ── KILL-GATES ──
    trows = [(x[0], x[2]) for x in out if x[2] != ""]
    ms = {d: s for d, s in trows}
    import collections
    occ = collections.Counter(s for _, s in trows)
    print(f"occupancy (K5): {dict(occ)} · SHA={sha[:12]}…")
    al = np.array([1.0 if ms[d] == "ALIGNED" else 0.0 for d, _ in trows])
    opp = np.array([1.0 if ms[d] == "OPPOSED" else 0.0 for d, _ in trows])
    ds = [d for d, _ in trows]
    fresh = np.array([1.0 if dc[d]["dc_state"] == "FRESH" else
                      (0.0 if dc[d]["dc_state"] in ("MID", "EXTENDED") else np.nan)
                      for d in ds])
    pk = np.array([g(poke[d], "poked") for d in ds])
    rjr = np.array([g(tick[d], "rjR") for d in ds])
    eh = np.array([int(facts[d]["entry_time"][:2]) + int(facts[d]["entry_time"][3:5]) / 60
                   for d in ds])
    og = np.array([g(facts[d], "overnight_gap") for d in ds])
    pv = np.array([g(facts[d], "prev_range") for d in ds])
    dead = {"rv": np.array([g(facts[d], "rv_pct250") for d in ds]),
            "slope": np.array([g(facts[d], "slope_pct250") for d in ds]),
            "rexp": np.array([g(facts[d], "range_exp") for d in ds]),
            "gapr": np.abs(og) / np.where(pv > 0, pv, np.nan),
            "awr": np.array([g(facts[d], "asian_width") for d in ds]) /
                   np.where(pv > 0, pv, np.nan)}

    def corr(a, b):
        m = np.isfinite(a) & np.isfinite(b)
        return np.corrcoef(a[m], b[m])[0, 1]

    print(f"K1 corr(ALIGNED, dc-FRESH) = {corr(al, fresh):+.3f} (kill ถ้า |r|>0.4)")
    print(f"K2 corr(ALIGNED, poked)    = {corr(al, pk):+.3f}")
    print(f"K3 corr(ALIGNED, rjR)={corr(al, rjr):+.3f} · corr(ALIGNED, eh)={corr(al, eh):+.3f} "
          f"(เกณฑ์ ≤~0.15)")
    print("K4 vs ตัวตาย: " + " ".join(f"{k}={corr(al, v):+.3f}" for k, v in dead.items()))
    print("per-year ALIGNED/OPPOSED/MIXED/UNDEF:")
    for y in range(2012, 2021):
        cc = collections.Counter(s for d, s in trows if d[:4] == str(y))
        print(f"  {y}: {cc.get('ALIGNED',0)}/{cc.get('OPPOSED',0)}/"
              f"{cc.get('MIXED',0)}/{cc.get('UNDEF',0)}")


if __name__ == "__main__":
    main()
