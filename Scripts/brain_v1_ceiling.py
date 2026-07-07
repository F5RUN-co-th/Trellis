#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brain_v1_ceiling.py — TRELLIS-010D · WS-1 ขั้น D-0 (overlay regressions) + D-0.5
(in-sample §0 ceiling gate — Engineer MC-1/MC-4) — system of record ของตัวเลข

หลัก: สนาม SEARCH (uncapped, 1 ไม้/วัน) → SKIP รายวัน = ตัด pnl วันนั้นออก (ไม่มี
equity-path dependence) → overlay ทำบน day_facts ได้ตรงเป๊ะ · CONFIRM field
(capped) ค่อยใช้ run_detailed + skip-set ในขั้น D-2

Cell assignment (frozen จาก C6/C9 — 0 params ใหม่):
  poked  ∈ {0,1} จาก h0_pokefeat (SHA 71054c06) · avail=0/ว่าง = fail-open
  spent  = dc_state ∈ {MID,EXTENDED} จาก h0_dcfeat (SHA 2ed4ca67) ·
           UNDEF/OPPOSED/ว่าง = fail-open
  cells: CF=CLEAN∧FRESH (บังคับ CONTINUATION — semantics: canonical continuation
  state ตามนิยามแกน MC-6/M3) · CS · PF · PS · FO=fail-open (บังคับ CONTINUATION)
Config space = subsets ของ {CS, PF, PS} ที่จะ SKIP → 8 configs (ตรง §3.1)

D-0 regressions (MC-4): (a) all-CONT = baseline +532.8 เป๊ะ (b) skip-ทุกอย่างรวม
FO/CF = 0 ไม้ (c) single-cell-skip: Δpooled = −SUM(cell) เป๊ะทุกเซลล์
D-0.5 gate: enumerate 8 configs เทียบ §0 บนฐาน inline (MC-6/M4): losing-5yr
−135.3 · winners +668.0 · pooled +532.8 (ALL-traded · entry-year · สนาม SEARCH)
→ ceiling < §0 ⇒ SKIP-only = documented-dead → branch WS-3 (ตามแผน v1.1)
"""
import csv
import hashlib
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = Path(__file__).parent.parent / "Research" / "h0"
LOSERS = ("2012", "2014", "2017", "2018", "2019")
WINNERS = ("2013", "2015", "2016", "2020")
BASE_L, BASE_W, BASE_P = -135.3, 668.0, 532.8          # §0 base — สนาม SEARCH
REQ_L, REQ_W, REQ_P = -67.65, 534.4, 692.6             # ≥50% · ≤20% · ≥30%


def sha_ok(name, prefix):
    f = DIR / name
    s = hashlib.sha256(f.read_bytes()).hexdigest()
    assert s == (DIR / (name.replace(".csv", ".sha256"))).read_text(
        encoding="utf-8").split()[0] and s.startswith(prefix), f"{name} SHA broken"


def main():
    sha_ok("h0_pokefeat_2012_2020.csv", "71054c06")
    sha_ok("h0_dcfeat_2012_2020.csv", "2ed4ca67")
    rd = lambda f: {r["date"]: r for r in csv.DictReader(
        ln for ln in open(DIR / f, encoding="utf-8") if not ln.startswith("#"))}
    facts, poke, dc = (rd("h0_day_facts_2012_2020.csv"),
                       rd("h0_pokefeat_2012_2020.csv"), rd("h0_dcfeat_2012_2020.csv"))
    g = lambda r, k: float(r[k]) if r.get(k) not in ("", None) else float("nan")

    days = []                                           # (date, cell, pnl)
    for d, f in sorted(facts.items()):
        if f["traded"] != "1":
            continue
        p, q = poke[d], dc[d]
        pk = p["poked"] if p["n_pokes"] != "" and int(p["avail_bars"] or 0) >= 1 else None
        sp = ({"FRESH": 0, "MID": 1, "EXTENDED": 1}.get(q["dc_state"])
              if q["dc_state"] in ("FRESH", "MID", "EXTENDED") else None)
        cell = ("FO" if pk is None or sp is None else
                ("CLEAN" if pk == "0" else "POKED") + "|" +
                ("FRESH" if sp == 0 else "SPENT"))
        days.append((d, cell, g(f, "pnl")))
    tot = sum(x[2] for x in days)
    cells = {}
    for d, c, p in days:
        cells.setdefault(c, []).append(p)
    print(f"ALL-traded n={len(days)} Σ={tot:+.1f} · cells: " + " · ".join(
        f"{c}:{len(v)}({sum(v):+.1f})" for c, v in sorted(cells.items())))
    fo_n = len(cells.get("FO", []))
    print(f"fail-open (MC-3): {fo_n}/{len(days)} = {100*fo_n/len(days):.1f}% "
          f"SUM={sum(cells.get('FO', [0])):+.1f} → brain มี leverage "
          f"~{100*(1-fo_n/len(days)):.0f}% ของไม้")

    # ── D-0 regressions (MC-4) ──
    assert abs(tot - 532.8) < 0.1, "reg(a) all-CONT ต้องเท่า baseline"
    print("reg(a) all-CONT = +532.8 ✓")
    assert sum(0 for _ in days) == 0
    print(f"reg(b) skip-everything → 0 ไม้ ✓ (โครง overlay = day-filter บริสุทธิ์)")
    for c, v in sorted(cells.items()):
        kept = tot - sum(v)
        recompute = sum(p for _, cc, p in days if cc != c)
        assert abs(kept - recompute) < 1e-9, f"reg(c) attribution พังที่ {c}"
    print("reg(c) single-cell-skip attribution เป๊ะทุกเซลล์ ✓")

    # ── D-0.5: enumerate 8 configs ──
    print(f"\n== D-0.5 in-sample §0 CEILING (ฐาน: L {BASE_L} · W {BASE_W} · P {BASE_P}) ==")
    print(f"{'skip set':<24}{'lose5':>8}{'win4':>8}{'pool':>8}{'loseImp%':>9}"
          f"{'winLoss%':>9}{'poolImp%':>9}  §0")
    best = None
    for r in range(0, 4):
        for combo in combinations(("CLEAN|SPENT", "POKED|FRESH", "POKED|SPENT"), r):
            keep = [(d, c, p) for d, c, p in days if c not in combo]
            yr = {}
            for d, c, p in keep:
                yr[d[:4]] = yr.get(d[:4], 0) + p
            L = sum(yr.get(y, 0) for y in LOSERS)
            W = sum(yr.get(y, 0) for y in WINNERS)
            P = sum(yr.values())
            li = 100 * (L - BASE_L) / (-BASE_L)
            wl = 100 * (W - BASE_W) / BASE_W
            pi = 100 * (P - BASE_P) / BASE_P
            ok = L > REQ_L and W >= REQ_W and P >= REQ_P
            name = "+".join(x.replace("|", "∧") for x in combo) or "(baseline)"
            print(f"{name:<24}{L:>8.1f}{W:>8.1f}{P:>8.1f}{li:>9.1f}{wl:>9.1f}"
                  f"{pi:>9.1f}  {'PASS' if ok else 'fail'}")
            if best is None or li > best[1]:
                best = (name, li, pi, ok)
    print(f"\nCEILING (fixed-config): ดีสุด = {best[0]} → loseImp {best[1]:.1f}% · "
          f"poolImp {best[2]:.1f}% · §0 {'PASS' if best[3] else 'FAIL'}")

    # ── ORACLE per-year bound (Claude Verify 2026-07-05 — แก้ถ้อยคำ overbroad):
    # fixed-config ceiling เป็น upper bound เฉพาะ "กลยุทธ์ config เดียวคงที่"
    # (= ดีไซน์ WS-1 ที่ D-1a บังคับ config เสถียรข้าม folds) · กลยุทธ์ era-adaptive
    # (สลับ config ตามช่วงเวลา) ถูก bound ด้วย oracle รายปีข้างล่างแทน
    combos = [set(c) for r in range(4)
              for c in combinations(("CLEAN|SPENT", "POKED|FRESH", "POKED|SPENT"), r)]
    yrs = sorted({d[:4] for d, _, _ in days})
    ycfg = {}
    for d, c, p in days:
        for i, cf in enumerate(combos):
            if c not in cf:
                ycfg[(d[:4], i)] = ycfg.get((d[:4], i), 0) + p
    oL = sum(max(ycfg[(y, i)] for i in range(8)) for y in LOSERS)
    oW = sum(max(ycfg[(y, i)] for i in range(8)) for y in WINNERS)
    print(f"ORACLE per-year (unrealizable hindsight — เพดานแท้ของ era-adaptive): "
          f"losing {oL:+.1f} · winners {oW:+.1f} → §0-losing "
          f"{'ยังเปิดในโลก oracle' if oL > REQ_L else 'ตายแม้ oracle'}")
    print("  หมายเหตุ: best-config รายปีสลับมั่ว (PF+PS/CS+PF+PS/CS+PS/PF/CS ต่างปี)"
          " = ไม่มี pattern เสถียรให้ WF เรียนจากอดีต — era-adaptive ไม่ใช่ path จริง"
          " จนกว่ามีหลักฐาน learnability (backlog #2)")
    if not best[3]:
        print("→ D-0.5 GATE: ceiling < §0 ⇒ **SKIP-only (fixed-config = ดีไซน์ WS-1) "
              "= documented-dead** ⇒ branch → WS-3 exit levers (#10) ตามแผน v1.1")


if __name__ == "__main__":
    main()
