#!/usr/bin/env python3
"""
walk_forward.py — Anchored walk-forward ของ Trellis v4 (Engineer A-fix-1)

Protocol (ประกาศก่อนรัน — ห้ามแก้หลังเห็นผล):
- Config grid 24 ตัว: CAPR{0.75,1.0} × D{0.5,0.75,1.0} × SLOPE{0.0005,0.001} × short{on,off}
  (A=1.0, EMA_P=2880 freeze — sensitivity แสดงว่าแบน/ทิศเดียว)
- ทุกปี Y = 2015..2026: เลือก config ที่ trailing NET สูงสุดบน 2012..Y-1 (expanding/anchored)
  tie-break: PF สูงกว่า → เทรดปี Y ด้วย config นั้น
- ตัวชี้วัด: ผลรวม OOS ปีต่อปี (ทุกปีเป็น out-of-sample ของการเลือก)
- Benchmark: (a) config กลาง fix ตลอด (CAPR1.0 D0.75 SLOPE0.001 short-on)
             (b) median ของทุก config ต่อปี (วัดว่า selection เพิ่มค่าไหม)

รัน: python walk_forward.py            (เต็ม ~30-40 นาที)
     python walk_forward.py smoke      (2 configs 2021-22 — เช็คก่อน)
"""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dual_asian_sim import load_full, run, year_start_index

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

GRID = [dict(CAPR=cap, A=1.0, D=d, SLOPE=s, EMA_P=2880, allow_short=sh)
        for cap in (0.75, 1.0) for d in (0.5, 0.75, 1.0)
        for s in (0.0005, 0.001) for sh in (True, False)]
BASE = dict(CAPR=1.0, A=1.0, D=0.75, SLOPE=0.001, EMA_P=2880, allow_short=True)


def trade_table(m1, start, cfg):
    """เทรดทั้ง span ครั้งเดียว -> list (year, pnl)"""
    tr = run(m1, start, **cfg)
    return [(int(str(x[0])[:4]), x[1]) for x in tr]


def year_net(table, y0, y1):
    p = [x[1] for x in table if y0 <= x[0] <= y1]
    return (float(np.sum(p)), len(p))


def pf(table, y0, y1):
    p = np.array([x[1] for x in table if y0 <= x[0] <= y1])
    if len(p) == 0:
        return 0.0
    w = p[p > 0].sum(); l = -p[p <= 0].sum()
    return w / max(l, 1e-9)


def main(smoke=False):
    years = list(range(2011, 2027))
    print(f"loading M1 {years[0]}-{years[-1]} ...", flush=True)
    t0 = time.time()
    m1 = load_full(years)
    start = year_start_index(m1, 2012)
    print(f"loaded {len(m1['c'])} bars in {time.time()-t0:.0f}s", flush=True)

    grid = GRID[:2] if smoke else GRID
    tables = []
    for k, cfg in enumerate(grid):
        t1 = time.time()
        tables.append(trade_table(m1, start, cfg))
        print(f"config {k+1}/{len(grid)} {cfg['CAPR']}/{cfg['D']}/{cfg['SLOPE']}/"
              f"{'S' if cfg['allow_short'] else 'L'} done {time.time()-t1:.0f}s "
              f"(total {year_net(tables[-1], 2012, 2026)[0]:+.0f})", flush=True)
    base_table = trade_table(m1, start, BASE)

    print("\n== ANCHORED WALK-FORWARD (เลือกจากอดีตเท่านั้น เทรดปีถัดไป) ==")
    print(f"{'Y':>5} {'chosen (CAP/D/SLOPE/side)':<28} {'trainNet':>9} {'OOS net':>9} {'n':>4} {'cum':>9}")
    cum = 0.0
    oos_trades = []
    yearly = []
    for Y in range(2015, 2027):
        scores = []
        for cfg, tb in zip(grid, tables):
            net_tr, _ = year_net(tb, 2012, Y - 1)
            scores.append((net_tr, pf(tb, 2012, Y - 1)))
        best = max(range(len(grid)), key=lambda k: (scores[k][0], scores[k][1]))
        oos, n = year_net(tables[best], Y, Y)
        cum += oos
        oos_trades += [x[1] for x in tables[best] if x[0] == Y]
        cfg = grid[best]
        label = f"{cfg['CAPR']}/{cfg['D']}/{cfg['SLOPE']}/{'dual' if cfg['allow_short'] else 'long'}"
        print(f"{Y:>5} {label:<28} {scores[best][0]:>+9.0f} {oos:>+9.1f} {n:>4} {cum:>+9.1f}")
        yearly.append(oos)

    p = np.array(oos_trades)
    w = p[p > 0]
    print(f"\nWF OOS 2015-2026: n={len(p)} net={p.sum():+.1f} "
          f"wr={100*len(w)/len(p):.1f}% PF={w.sum()/max(-(p[p<=0]).sum(),1e-9):.2f}")
    print(f"ปีบวก {sum(1 for y in yearly if y > 0)}/{len(yearly)} · worst {min(yearly):+.1f} · best {max(yearly):+.1f}")
    rng = np.random.default_rng(23)
    boots = np.array([rng.choice(p, len(p), True).sum() for _ in range(10000)])
    print(f"bootstrap WF-OOS: CI95=[{np.percentile(boots,2.5):+.0f},{np.percentile(boots,97.5):+.0f}] "
          f"P(<=0)={100*(boots<=0).mean():.1f}%")

    print("\n== benchmarks ==")
    bnet, bn = year_net(base_table, 2015, 2026)
    print(f"fix base ตลอด:          {bnet:+.1f} (n={bn})")
    med = [float(np.median([year_net(tb, Y, Y)[0] for tb in tables])) for Y in range(2015, 2027)]
    print(f"median config ต่อปี:     {np.sum(med):+.1f}")


if __name__ == "__main__":
    main(smoke=(len(sys.argv) > 1 and sys.argv[1] == "smoke"))
