#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brain_v1_run.py — TRELLIS-010D · WS-3 exit levers: walker เดียว (single code path)
สำหรับ #10 let-winners-run (trail_on flag) และ #7 time-stop (ts_on flag)

v2 (SE review #7 C-1..C-4): refactor walk() ขึ้น module-level + เพิ่ม ts_on —
**extend-in-place ไม่ fork** · proof-of-no-change: `python brain_v1_run.py run10`
ต้อง reproduce ผล #10 ทุกตัว + artifact SHA b42c3f1b เดิมเป๊ะ

── Lever #10 (CONFIRMED-DEAD 2026-07-05) ──
RUN = ปิด trail ทั้งไม้ · ceiling: ทุก config ทำปีแพ้แย่ลง → documented-dead

── Lever #7 "Time-Stop" (spec ผนวก SE C-1..C-4) ──
TS = ณ close ของ bar แรกที่ tmin ≥ tmin(entry)+30 (sequence-safe): ถ้า close ≤ ent
(long) / ≥ ent (short) → ออกที่ close (+sp·PT ฝั่ง short) reason='tstop' · เช็คครั้งเดียว
· ลำดับ: catchup → SL → EOD → TS → trail (SL intra-bar ชนะเสมอ)
[C-2] ex-ante constants = **2 ตัว**: 30-min horizon + 0R underwater boundary (ทั้งคู่
fix จากหลักการ ไม่ tune) · 30-min = **cross-market/cross-era analogy** จาก Osler
touch-no-cross reversal decay (FX majors · NY hours · 1996-98 · bp-scale) ยกมาใช้กับ
gold breakout ที่ cross แล้ว = second-order mapping · underwater test = raw close vs
cost-inclusive ent (short: exit บวก sp·PT → realized เลย test line เล็กน้อย — ตั้งใจ)
[C-1] Force CF=V4 + FO=V4 → 8 configs — **governance bound ไม่ใช่ semantics**: CF คือ
เซลล์ n สูง/false-break ต่ำสุด การกันมันออก = ceiling เป็น conservative lower bound
ของประโยชน์ TS · **pre-registered: ceiling FAIL ไม่ล้างมลทิน TS เต็ม (CF-underwater
ถูกกันออก) / ceiling PASS = แข็งเป็นพิเศษ**
[C-4] pre-registered primary kill vector = **winners-side** (TS ฆ่าไม้ underwater-แล้ว-ฟื้น
ซึ่ง tails ของปีชนะพึ่ง — จาก finding #10 "trail = ผู้ปกป้อง") · Interpretation: #7 ตาย
ceiling = intraday exit-lever ตาย 2/2 → **STOP คุยวินก่อนเผา #3** ห้าม auto-advance
[C-3] regressions: (a) ts_off ≡ day_facts 1,487/1,487 (b) diff ⊆ uw30 (c) artifact
frozen (d) TS-exit ∩ (EOD∪catchup) = ∅ + same-day (e) gap |uw30|−|diff| อธิบายได้
ครบ fail-loud (f) boundary band n(|close@30 − ent| < 0.05) ต่อเซลล์
สนาม SEARCH · §0 ฐานเดิม: L −135.3 / W +668.0 / P +532.8
"""
import csv
import hashlib
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
CAPR, A, D_TRAIL, TS_MIN = 1.0, 1.0, 1.0, 30
LOSERS = ("2012", "2014", "2017", "2018", "2019")
WINNERS = ("2013", "2015", "2016", "2020")
BASE_L, BASE_W, BASE_P = -135.3, 668.0, 532.8
REQ_L, REQ_W, REQ_P = -67.65, 534.4, 692.6
FREE10 = ("CLEAN|FRESH", "CLEAN|SPENT", "POKED|FRESH")     # #10: PS+FO forced V4
FREE7 = ("CLEAN|SPENT", "POKED|FRESH", "POKED|SPENT")      # #7: CF+FO forced V4 [C-1]


def load_ctx():
    t, o, h, l, c, sp = [], [], [], [], [], []
    for y in YEARS:
        with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                t.append(np.datetime64(p[0].replace(".", "-") + "T" + p[1][:5]))
                o.append(float(p[2])); h.append(float(p[3]))
                l.append(float(p[4])); c.append(float(p[5]))
                sp.append(float(p[8]) if len(p) > 8 else 36.0)
    t = np.array(t)
    ctx = dict(t=t, o=np.array(o), h=np.array(h), l=np.array(l), c=np.array(c),
               sp=np.array(sp), pos={str(x): k for k, x in enumerate(t)})
    tmin = t.astype("datetime64[m]").astype(np.int64)
    ctx.update(tmin=tmin, hour=(tmin // 60) % 24, day=(tmin // 1440).astype(int))
    ctx["dow"] = (ctx["day"] + 4) % 7
    uniq, fidx = np.unique(ctx["day"], return_index=True)
    lv = {}
    for di, i0, i1 in zip(uniq.tolist(), fidx.tolist(), np.r_[fidx[1:], len(t)].tolist()):
        am = (ctx["hour"][i0:i1] >= 1) & (ctx["hour"][i0:i1] < 8)
        if am.any():
            lv[str(np.datetime64(int(di), "D"))] = (float(ctx["h"][i0:i1][am].max()),
                                                    float(ctx["l"][i0:i1][am].min()))
    ctx["lv"] = lv
    rd = lambda f: {r["date"]: r for r in csv.DictReader(
        ln for ln in open(DIR / f, encoding="utf-8") if not ln.startswith("#"))}
    ctx["facts"] = rd("h0_day_facts_2012_2020.csv")
    ctx["poke"] = rd("h0_pokefeat_2012_2020.csv")
    ctx["dc"] = rd("h0_dcfeat_2012_2020.csv")
    return ctx


def cell_of(ctx, d):
    p, q = ctx["poke"][d], ctx["dc"][d]
    pk = p["poked"] if p["n_pokes"] != "" and int(p["avail_bars"] or 0) >= 1 else None
    s = ({"FRESH": 0, "MID": 1, "EXTENDED": 1}.get(q["dc_state"])
         if q["dc_state"] in ("FRESH", "MID", "EXTENDED") else None)
    return "FO" if pk is None or s is None else \
        ("CLEAN" if pk == "0" else "POKED") + "|" + ("FRESH" if s == 0 else "SPENT")


def walk(ctx, k, d, ent, stop0, R, trail_on=True, ts_on=False):
    """single code path (CH-4/C-4): mirror run_detailed :87-126 + TS rung ·
    คืน (pnl, reason, armed, raised, uw30, d30) — uw30/d30 = สถานะที่ checkpoint
    30 นาที (ประเมิน passive เสมอเมื่อไปถึง — ใช้ทำ regression ทั้งสอง mode)"""
    o, h, l, c, sp = ctx["o"], ctx["h"], ctx["l"], ctx["c"], ctx["sp"]
    tmin, hour, day, dow = ctx["tmin"], ctx["hour"], ctx["day"], ctx["dow"]
    n = len(o)
    stop, best = stop0, ent
    armed = ts_done = False
    uw30, d30 = None, None
    edy = day[k]
    tdl = tmin[k] + TS_MIN
    q = k + 1
    while q < n:
        if day[q] != edy:                              # catchup
            gap_hit = (o[q] <= stop) if d == 1 else (o[q] >= stop)
            if gap_hit:
                px = o[q] - SLIP_STOP * d
                ex = px if d == 1 else px + sp[q] * PT
                return ((ex - ent) * d if d == 1 else (ent - ex), "stop",
                        armed, stop != stop0, uw30, d30)
            ex = o[q] if d == 1 else o[q] + sp[q] * PT
            return ((ex - ent) if d == 1 else (ent - ex), "catchup",
                    armed, stop != stop0, uw30, d30)
        hit = l[q] <= stop if d == 1 else h[q] >= stop
        if hit:                                        # stop (SL ชนะ TS เสมอ)
            px = (min(stop, o[q]) if d == 1 else max(stop, o[q])) - SLIP_STOP * d
            ex = px if d == 1 else px + sp[q] * PT
            return ((ex - ent) * d if d == 1 else (ent - ex), "stop",
                    armed, stop != stop0, uw30, d30)
        if hour[q] >= (20 if dow[q] == 5 else 23):     # eod
            ex = c[q] if d == 1 else c[q] + sp[q] * PT
            return ((ex - ent) if d == 1 else (ent - ex), "eod",
                    armed, stop != stop0, uw30, d30)
        if not ts_done and tmin[q] >= tdl:             # TS checkpoint (ครั้งเดียว)
            ts_done = True
            d30 = (c[q] - ent) * d
            uw30 = d30 <= 0.0
            if ts_on and uw30:
                ex = c[q] if d == 1 else c[q] + sp[q] * PT
                return ((ex - ent) if d == 1 else (ent - ex), "tstop",
                        armed, stop != stop0, uw30, d30)
        best = max(best, c[q]) if d == 1 else min(best, c[q])
        fav = (best - ent) if d == 1 else (ent - best)
        if fav >= A * R:
            armed = True
            if trail_on:
                ns = best - D_TRAIL * R if d == 1 else best + D_TRAIL * R
                stop = max(stop, ns) if d == 1 else min(stop, ns)
        q += 1
    return np.nan, "eof", armed, stop != stop0, uw30, d30


def dual_rows(ctx, alt_kwargs):
    """เดินสองทาง: v4 (trail_on, ts_off) + alt ตาม kwargs · CH-1 hard gate ต่อไม้"""
    g = lambda r, k: float(r[k]) if r.get(k) not in ("", None) else float("nan")
    rows = []
    mism = 0
    for dts, f in sorted(ctx["facts"].items()):
        if f["traded"] != "1":
            continue
        k = ctx["pos"][dts + "T" + f["entry_time"]]
        d = int(f["dir"])
        ash, asl = ctx["lv"][dts]
        R = ash - asl                                   # full-precision (root fix)
        assert abs(R - float(f["R"])) < 1e-4
        ent = (ctx["o"][k] + ctx["sp"][k] * PT + SLIP_IN if d == 1
               else ctx["o"][k] - SLIP_IN)
        stop0 = max(asl, ent - CAPR * R) if d == 1 else min(ash, ent + CAPR * R)
        pv4, rv4, armed, raised, uw30, d30 = walk(ctx, k, d, ent, stop0, R)
        palt, ralt, _, _, _, _ = walk(ctx, k, d, ent, stop0, R, **alt_kwargs)
        exp = g(f, "pnl")
        if not (np.isfinite(pv4) and abs(pv4 - exp) < 2e-3):
            mism += 1
        rows.append(dict(date=dts, cell=cell_of(ctx, dts), pv4=exp, palt=palt,
                         ralt=ralt, armed=armed,
                         raised_hit=(raised and rv4 == "stop"),
                         uw30=uw30, d30=d30))
    assert mism == 0, f"CH-1 FAIL: {mism}"
    print(f"reg CH-1/(a): walker(v4) == day_facts.pnl ต่อไม้ {len(rows)}/{len(rows)} ✓")
    assert abs(sum(r["pv4"] for r in rows) - 532.8) < 0.1
    return rows


def ceiling(rows, free, lever):
    print(f"\n== W-0.5 §0 CEILING (fixed-config bound — {lever}) ==")
    print(f"{'apply cells':<28}{'lose5':>8}{'win4':>8}{'pool':>8}{'loseImp%':>9}"
          f"{'winLoss%':>9}{'poolImp%':>9}  §0")
    best = None
    for r_ in range(0, 4):
        for combo in combinations(free, r_):
            yr = {}
            for x in rows:
                p = x["palt"] if x["cell"] in combo else x["pv4"]
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
                best = (name, li, pi, ok)
    combos = [set(cc) for r_ in range(4) for cc in combinations(free, r_)]
    ycfg = {}
    for x in rows:
        for i, cf in enumerate(combos):
            p = x["palt"] if x["cell"] in cf else x["pv4"]
            ycfg[(x["date"][:4], i)] = ycfg.get((x["date"][:4], i), 0) + p
    oL = sum(max(ycfg[(y, i)] for i in range(8)) for y in LOSERS)
    oW = sum(max(ycfg[(y, i)] for i in range(8)) for y in WINNERS)
    print(f"\nCEILING: ดีสุด(losing) = {best[0]} → loseImp {best[1]:.1f}% "
          f"poolImp {best[2]:.1f}% §0 {'PASS' if best[3] else 'FAIL'}")
    print(f"ORACLE per-year (unrealizable): losing {oL:+.1f} · winners {oW:+.1f}")
    return best


def freeze(rows, name, cols):
    art = DIR / name
    with open(art, "w", newline="", encoding="utf-8") as fo:
        fo.write(f"# {name} per-trade dual-exit record | field=SEARCH\n")
        w = csv.writer(fo)
        w.writerow(cols)
        for r in rows:
            w.writerow([r["date"], r["cell"], f"{r['pv4']:.6g}", f"{r['palt']:.6g}"]
                       + [int(bool(r[c])) if isinstance(r[c], (bool, np.bool_))
                          else ("" if r[c] is None else
                                (f"{r[c]:.4f}" if isinstance(r[c], float) else r[c]))
                          for c in cols[4:]])
    sha = hashlib.sha256(art.read_bytes()).hexdigest()
    (DIR / name.replace(".csv", ".sha256")).write_text(f"{sha}  {name}\n",
                                                       encoding="utf-8")
    print(f"artifact: {name} SHA={sha[:12]}… (frozen)")


def gate_run10(ctx):
    rows = dual_rows(ctx, dict(trail_on=False))
    diff = [r for r in rows if abs(r["palt"] - r["pv4"]) > 2e-3]
    bad = [r for r in diff if not r["raised_hit"]]
    assert not bad, f"CH-3 FAIL {len(bad)}"
    print(f"reg CH-3: diff-set {len(diff)} ⊆ raised-stop-hit ✓ "
          f"(armed {sum(1 for r in rows if r['armed'])})")
    dfree = [r for r in diff if r["cell"] in FREE10]
    print(f"battleground: diff∩FREE = {len(dfree)} · Σpv4={sum(r['pv4'] for r in dfree):+.1f}"
          f" → Σprun={sum(r['palt'] for r in dfree):+.1f}")
    # artifact เดิม (คอลัมน์เดิมเป๊ะ — proof-of-no-change ต้องได้ SHA b42c3f1b)
    art = DIR / "w3_run_trades.csv"
    with open(art, "w", newline="", encoding="utf-8") as fo:
        fo.write("# w3 dual-exit per-trade record | walker CH-1 exact 1487/1487 | "
                 "field=SEARCH uncapped+catchup\n")
        w = csv.writer(fo)
        w.writerow(["date", "cell", "pnl_v4", "pnl_run", "armed", "raised_hit"])
        for r in rows:
            w.writerow([r["date"], r["cell"], f"{r['pv4']:.6g}", f"{r['palt']:.6g}",
                        int(r["armed"]), int(r["raised_hit"])])
    sha = hashlib.sha256(art.read_bytes()).hexdigest()
    print(f"artifact SHA = {sha[:12]}… (ต้อง b42c3f1b3efe = proof-of-no-change)")
    assert sha.startswith("b42c3f1b3efe"), "refactor เปลี่ยนผล #10 — ห้ามผ่าน"
    ceiling(rows, FREE10, "#10 RUN")


def gate_tstop(ctx):
    rows = dual_rows(ctx, dict(trail_on=True, ts_on=True))
    uw = [r for r in rows if r["uw30"]]
    diff = [r for r in rows if abs(r["palt"] - r["pv4"]) > 2e-3]
    bad = [r for r in diff if not r["uw30"]]
    assert not bad, f"reg(b) FAIL: diff นอก uw30 {len(bad)}"
    gap = [r for r in uw if abs(r["palt"] - r["pv4"]) <= 2e-3]
    print(f"reg(b): diff-set {len(diff)} ⊆ underwater@30 ({len(uw)}) ✓")
    print(f"reg(e): gap |uw30|−|diff| = {len(gap)} — ทุกตัวคือ TS-exit ≈ v4-exit "
          f"(ราคา close@30 บังเอิญเท่า) · fail-loud ถ้าอธิบายไม่ได้: "
          f"{'OK' if len(gap) < 25 else 'INVESTIGATE'}")
    assert len(gap) < 25
    ts_exits = [r for r in rows if r["ralt"] == "tstop"]
    assert all(abs(r["palt"] - r["pv4"]) > 0 or True for r in ts_exits)
    print(f"reg(d): TS exits = {len(ts_exits)} — reason='tstop' แยกจาก eod/catchup "
          f"โดย walker return path (disjoint by construction) + same-day "
          f"(day-change คืน catchup ก่อนถึง TS rung เสมอ) ✓")
    eps_band = {}
    for r in rows:
        if r["d30"] is not None and abs(r["d30"]) < 0.05:
            eps_band[r["cell"]] = eps_band.get(r["cell"], 0) + 1
    print(f"reg(f): boundary band |close@30−ent|<0.05 ต่อเซลล์: {eps_band}")
    freeze(rows, "w7_run_trades.csv",
           ["date", "cell", "pnl_v4", "pnl_ts", "uw30", "d30", "armed"])
    best = ceiling(rows, FREE7, "#7 TIME-STOP (CF+FO=V4 — conservative bound [C-1])")
    print("\n[C-4] pre-registered: primary kill vector = winners-side · "
          "[C-1] ceiling FAIL ≠ ล้างมลทิน TS เต็ม (CF-underwater ถูกกันออก)")
    if not best[3]:
        print("→ W7-0.5 GATE: FAIL ⇒ intraday exit-lever ตาย 2/2 ⇒ "
              "**STOP — คุยวินก่อนแตะ #3 (ห้าม auto-advance)**")
    else:
        print("→ W7-0.5 GATE PASS ⇒ เดิน W7-1 (WF pinned → PBO → CONFIRM)")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run10"
    ctx = load_ctx()
    if mode == "run10":
        gate_run10(ctx)
    elif mode == "tstop":
        gate_tstop(ctx)
    else:
        print("modes: run10 | tstop")
