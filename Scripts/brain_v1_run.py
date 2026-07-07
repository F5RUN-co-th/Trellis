#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brain_v1_run.py — TRELLIS-010D · WS-3 lever #10 "Let-Winners-Run" · ขั้น W3-0 (dual-exit
sim + regressions) + W3-0.5 (in-sample §0 ceiling gate) — system of record

ผนวก Engineer CH-1..CH-5:
  CH-1 ใช้ DEPLOY params (CAPR=1,A=1,D=1) + regression = per-trade equality กับ
       day_facts.pnl ทั้ง 1,487 ไม้ (ไม่ใช่แค่ total)
  CH-2 armed/stop_raised เป็น flag ชัดใน walker (ไม่ใช่ pnl-sign proxy)
  CH-3 diagnostic all-free-RUN: diff-set ต้อง == {ไม้ที่ v4 ออกด้วย raised-stop}
       ∩ free-cells เป๊ะ (hard gate)
  CH-4 single code path: walker เดียว flag trail_on — SL/EOD/catchup byte-identical
       (copy-with-proof pattern เดียวกับ S2: พิสูจน์ equivalence ทุกครั้งที่รัน)
  CH-5 oracle ของ RUN คำนวณสดแยกจาก SKIP + ถ้อยคำ fixed-config-only

RUN = v4 ทุกอย่างยกเว้นปิด trail-update (mirror `stage0_join.py:120-125` ด้วย flag)
Config space: เซลล์ CF/CS/PF → {V4,RUN} · **POKED∧SPENT + fail-open = V4 บังคับ
(semantics: exhaustion pole — ไม่อิง P&L)** → 8 configs
สนาม: SEARCH (uncapped + catchup) · CONFIRM capped = ขั้น W3-1+ (ต้อง re-mirror cap)
"""
import csv
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dual_asian_sim import PT, SLIP_IN, SLIP_STOP

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(r"D:/workspace/Doc/T.me/R&D/Gloo/Data")
DIR = Path(__file__).parent.parent / "Research" / "h0"
YEARS = list(range(2011, 2021))
CAPR, A, D_TRAIL = 1.0, 1.0, 1.0                 # CH-1: DEPLOY_CFG
LOSERS = ("2012", "2014", "2017", "2018", "2019")
WINNERS = ("2013", "2015", "2016", "2020")
BASE_L, BASE_W, BASE_P = -135.3, 668.0, 532.8
REQ_L, REQ_W, REQ_P = -67.65, 534.4, 692.6
FREE = ("CLEAN|FRESH", "CLEAN|SPENT", "POKED|FRESH")


def load_m1():
    t, o, h, l, c, sp = [], [], [], [], [], []
    for y in YEARS:
        with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                t.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
                o.append(float(p[2])); h.append(float(p[3]))
                l.append(float(p[4])); c.append(float(p[5]))
                sp.append(float(p[8]) if len(p) > 8 else 36.0)
    return (np.array(t), np.array(o), np.array(h), np.array(l), np.array(c),
            np.array(sp))


def main():
    rd = lambda f: {r["date"]: r for r in csv.DictReader(
        ln for ln in open(DIR / f, encoding="utf-8") if not ln.startswith("#"))}
    facts, poke, dc = (rd("h0_day_facts_2012_2020.csv"),
                       rd("h0_pokefeat_2012_2020.csv"), rd("h0_dcfeat_2012_2020.csv"))
    g = lambda r, k: float(r[k]) if r.get(k) not in ("", None) else float("nan")

    t, o, h, l, c, sp = load_m1()
    pos = {str(x): k for k, x in enumerate(t)}
    tmin = t.astype("datetime64[m]").astype(np.int64)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)
    dow = (day + 4) % 7
    n = len(t)
    # ash/asl ต่อวัน (สูตร sim)
    uniq, fidx = np.unique(day, return_index=True)
    lv = {}
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), np.r_[fidx[1:], n].tolist()):
        am = (hour[i0:i1] >= 1) & (hour[i0:i1] < 8)
        if am.any():
            lv[str(np.datetime64(int(di), "D"))] = (float(h[i0:i1][am].max()),
                                                    float(l[i0:i1][am].min()))

    def cell_of(d):
        p, q = poke[d], dc[d]
        pk = p["poked"] if p["n_pokes"] != "" and int(p["avail_bars"] or 0) >= 1 else None
        s = ({"FRESH": 0, "MID": 1, "EXTENDED": 1}.get(q["dc_state"])
             if q["dc_state"] in ("FRESH", "MID", "EXTENDED") else None)
        return "FO" if pk is None or s is None else \
            ("CLEAN" if pk == "0" else "POKED") + "|" + ("FRESH" if s == 0 else "SPENT")

    def walk(k, d, ent, stop0, R, trail_on):
        """single code path (CH-4): mirror run_detailed :87-126 ทุกบรรทัด logic ·
        trail_on=False = ข้ามเฉพาะ trail block · คืน (pnl, reason, armed, stop_raised)"""
        stop, best = stop0, ent
        armed = False
        edy = day[k]
        q = k + 1
        while q < n:
            if day[q] != edy:                          # catchup (:90-103)
                gap_hit = (o[q] <= stop) if d == 1 else (o[q] >= stop)
                if gap_hit:
                    px = o[q] - SLIP_STOP * d
                    ex = px if d == 1 else px + sp[q] * PT
                    return ((ex - ent) * d if d == 1 else (ent - ex),
                            "stop", armed, stop != stop0)
                ex = o[q] if d == 1 else o[q] + sp[q] * PT
                return ((ex - ent) if d == 1 else (ent - ex), "catchup",
                        armed, stop != stop0)
            hit = l[q] <= stop if d == 1 else h[q] >= stop
            if hit:                                    # stop (:104-112)
                px = (min(stop, o[q]) if d == 1 else max(stop, o[q])) - SLIP_STOP * d
                ex = px if d == 1 else px + sp[q] * PT
                return ((ex - ent) * d if d == 1 else (ent - ex), "stop",
                        armed, stop != stop0)
            if hour[q] >= (20 if dow[q] == 5 else 23):  # eod (:113-119)
                ex = c[q] if d == 1 else c[q] + sp[q] * PT
                return ((ex - ent) if d == 1 else (ent - ex), "eod",
                        armed, stop != stop0)
            best = max(best, c[q]) if d == 1 else min(best, c[q])
            fav = (best - ent) if d == 1 else (ent - best)
            if fav >= A * R:
                armed = True
                if trail_on:                           # trail (:120-125) — flag เดียว
                    ns = best - D_TRAIL * R if d == 1 else best + D_TRAIL * R
                    stop = max(stop, ns) if d == 1 else min(stop, ns)
            q += 1
        return np.nan, "eof", armed, stop != stop0

    # ── W3-0: dual walk + regressions ──
    rows = []
    mism = 0
    for dts, f in sorted(facts.items()):
        if f["traded"] != "1":
            continue
        k = pos[dts + "T" + f["entry_time"]]
        d = int(f["dir"])
        ash, asl = lv[dts]
        # R full-precision จาก M1 (identity ash−asl==R พิสูจน์แล้ว) — ห้ามใช้ค่า %.6g
        # จาก day_facts: เคส 2014-12-10 stop ต่างกัน 1.4e-13 แพ้ exact-touch ที่ boundary
        R = ash - asl
        assert abs(R - float(f["R"])) < 1e-4
        ent = o[k] + sp[k] * PT + SLIP_IN if d == 1 else o[k] - SLIP_IN
        stop0 = max(asl, ent - CAPR * R) if d == 1 else min(ash, ent + CAPR * R)
        pv4, rv4, armed, raised = walk(k, d, ent, stop0, R, True)
        prun, rrun, _, _ = walk(k, d, ent, stop0, R, False)
        exp = g(f, "pnl")
        if not (np.isfinite(pv4) and abs(pv4 - exp) < 2e-3):
            mism += 1
        rows.append(dict(date=dts, cell=cell_of(dts), pv4=exp, prun=prun,
                         armed=armed, raised_hit=(raised and rv4 == "stop")))
    assert mism == 0, f"CH-1 FAIL: per-trade mismatch {mism} ไม้"
    print(f"reg CH-1: walker(trail_on) == day_facts.pnl ต่อไม้ {len(rows)}/{len(rows)} ✓")
    tot = sum(r["pv4"] for r in rows)
    assert abs(tot - 532.8) < 0.1
    diff = [r for r in rows if abs(r["prun"] - r["pv4"]) > 2e-3]
    bad = [r for r in diff if not r["raised_hit"]]
    assert not bad, f"CH-3 FAIL: diff นอก raised-stop set {len(bad)}"
    print(f"reg CH-3: diff-set {len(diff)} ไม้ ⊆ raised-stop-hit เป๊ะ ✓ "
          f"(armed ทั้งหมด {sum(1 for r in rows if r['armed'])})")
    dfree = [r for r in diff if r["cell"] in FREE]
    print(f"battleground: diff∩FREE = {len(dfree)} ไม้ · Σpv4={sum(r['pv4'] for r in dfree):+.1f} "
          f"→ Σprun={sum(r['prun'] for r in dfree):+.1f} "
          f"(Δ={sum(r['prun']-r['pv4'] for r in dfree):+.1f})")
    # audit artifact (§7 governance): per-trade dual-exit record + SHA
    import hashlib
    art = DIR / "w3_run_trades.csv"
    with open(art, "w", newline="", encoding="utf-8") as fo:
        fo.write("# w3 dual-exit per-trade record | walker CH-1 exact 1487/1487 | "
                 "field=SEARCH uncapped+catchup\n")
        w = csv.writer(fo)
        w.writerow(["date", "cell", "pnl_v4", "pnl_run", "armed", "raised_hit"])
        for r in rows:
            w.writerow([r["date"], r["cell"], f"{r['pv4']:.6g}", f"{r['prun']:.6g}",
                        int(r["armed"]), int(r["raised_hit"])])
    sha = hashlib.sha256(art.read_bytes()).hexdigest()
    (DIR / "w3_run_trades.sha256").write_text(f"{sha}  {art.name}\n", encoding="utf-8")
    print(f"artifact: {art.name} SHA={sha[:12]}… (frozen)")

    # ── W3-0.5: ceiling gate ──
    print(f"\n== W3-0.5 §0 CEILING (fixed-config bound — RUN lever) ==")
    print(f"{'RUN cells':<28}{'lose5':>8}{'win4':>8}{'pool':>8}{'loseImp%':>9}"
          f"{'winLoss%':>9}{'poolImp%':>9}  §0")
    best = None
    for r_ in range(0, 4):
        for combo in combinations(FREE, r_):
            yr = {}
            for x in rows:
                p = x["prun"] if x["cell"] in combo else x["pv4"]
                yr[x["date"][:4]] = yr.get(x["date"][:4], 0) + p
            L = sum(yr.get(y, 0) for y in LOSERS)
            W = sum(yr.get(y, 0) for y in WINNERS)
            P = sum(yr.values())
            li, wl, pi = (100 * (L - BASE_L) / (-BASE_L), 100 * (W - BASE_W) / BASE_W,
                          100 * (P - BASE_P) / BASE_P)
            ok = L > REQ_L and W >= REQ_W and P >= REQ_P
            name = "+".join(x.replace("|", "∧") for x in combo) or "(all V4)"
            print(f"{name:<28}{L:>8.1f}{W:>8.1f}{P:>8.1f}{li:>9.1f}{wl:>9.1f}"
                  f"{pi:>9.1f}  {'PASS' if ok else 'fail'}")
            if best is None or li > best[1]:
                best = (name, li, pi, ok, L, W, P)
    print(f"\nCEILING (fixed-config): ดีสุด(losing) = {best[0]} → loseImp {best[1]:.1f}% "
          f"poolImp {best[2]:.1f}% §0 {'PASS' if best[3] else 'FAIL'}")
    # CH-5: RUN oracle per-year (สดของ lever นี้)
    combos = [set(cc) for r_ in range(4) for cc in combinations(FREE, r_)]
    ycfg = {}
    for x in rows:
        for i, cf in enumerate(combos):
            p = x["prun"] if x["cell"] in cf else x["pv4"]
            ycfg[(x["date"][:4], i)] = ycfg.get((x["date"][:4], i), 0) + p
    oL = sum(max(ycfg[(y, i)] for i in range(8)) for y in LOSERS)
    oW = sum(max(ycfg[(y, i)] for i in range(8)) for y in WINNERS)
    print(f"ORACLE per-year (unrealizable · เพดาน era-adaptive): losing {oL:+.1f} · "
          f"winners {oW:+.1f}")
    if best[3]:
        print("→ W3-0.5 GATE PASS: เดิน W3-1 (WF folds pinned ex-ante → PBO → CONFIRM)")
    else:
        print("→ W3-0.5 GATE: ceiling < §0 ⇒ RUN lever (fixed-config) = documented-dead "
              "⇒ ตาม failure branch: lever ถัดไป (#7 time-stop) / ประเมิน WS-3 ต่อ")


if __name__ == "__main__":
    main()
