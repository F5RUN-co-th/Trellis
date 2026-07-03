#!/usr/bin/env python3
"""
stage0_join.py — TRELLIS-010 Stage 0.1: Sim<->Tester decomposition (rerunnable)

โจทย์ (Plan/TRELLIS-010 §Stage 0): config เดียวกัน sim 2025 = +$207 แต่ tester = -$169
แยก gap ต่อปีเป็น (a) participation flips (วันที่เครื่องหนึ่งเข้า อีกเครื่องไม่เข้า)
vs (b) per-trade fill/exit drift (วันที่เข้าทั้งคู่ แต่ผลต่างกัน)

สนามวัด: SIM = dual_asian_sim.run (bar-M1 pessimistic, Dukascopy CSV)
         TESTER = MT5 real-tick diag CSV (authority)

Integrity:
- Instrumented runner (บันทึก entry_time/dir/px) ต้องผ่าน SELF-CHECK เทียบ canonical
  dual_asian_sim.run แบบ exact (n + pnl ทุกไม้) — ไม่ผ่าน = abort (แตะ canonical ไม่ได้
  เพราะเป็นเจ้าของตัวเลข v4 จึงใช้สำเนา instrumented + พิสูจน์ equivalence ทุกครั้งที่รัน)
- Decomposition identity ตรวจเลขปิด: gap == drift + flip_in - flip_out (ไม่ปิด = abort)
- ไม่มี silent trimming: sim trades นอก coverage ของ tester file ถูกรายงานแยก ไม่ทิ้งเงียบ

Config: WF-selected ที่ deploy จริง (TRELLIS-009 §7-8): CAPR=1.0 A=1.0 D=1.0 SLOPE=0.0005 dual

Usage: python stage0_join.py
"""
import csv
import sys
from datetime import date, datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dual_asian_sim import PT, SLIP_IN, SLIP_STOP, MAX_SPREAD_PT, load_full, run, year_start_index
from entry_platform import DIAG, ema

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# config ที่ deploy (WF-selected) — ห้ามแก้โดยไม่บันทึกใน Progress Log
DEPLOY_CFG = dict(CAPR=1.0, A=1.0, D=1.0, SLOPE=0.0005, EMA_P=2880, SLOPE_B=1440,
                  allow_short=True, spread_mult=1.0)

# tester runs ที่ใช้ (build ก่อน risk-cap 12:00 — ตรง sim: ไม่มี skip filter)
TESTER_FILES = [
    ("v4b_2324", "Trellis_diag_770001_v4b_2324.csv"),
    ("v4c_2526", "Trellis_diag_770001_v4c_2526.csv"),
    # v4d รัน 12:01 = อาจเป็น build หลัง risk-cap deploy 12:00 (deposit 3000 → cap $60)
    # participation diff ของ 2026 จึงตีความด้วยความระวัง — alignment ของ entry-minute คือหลักฐานหลัก
    ("v4d_2601", "Trellis_diag_770001_v4d_2601.csv"),
]


# ---------- instrumented sim (สำเนา run() + detail; พิสูจน์ equivalence ทุกครั้ง) ----------
def run_detailed(m1, start, CAPR=1.0, A=1.0, D=0.75, SLOPE=0.001, EMA_P=2880, SLOPE_B=1440,
                 allow_short=True, spread_mult=1.0, deposit=None, cap_frac=0.02):
    """เหมือน dual_asian_sim.run ทุกบรรทัด logic — เพิ่ม (1) บันทึก detail ต่อไม้
    (entry_time, exit_time, dir, entry_px, exit_px, pnl, reason, R)
    (2) mirror risk-cap ของ EA (Trellis.mq5:242) เมื่อ deposit ไม่ใช่ None:
        ข้ามวันที่ R > cap_frac*equity · equity = deposit + realized สะสม (EA เช็คตอน flat
        เสมอ — TryEntry เฉพาะ TRL_IDLE) · set traded ตอน skip = เทียบเท่า EA เพราะ R และ
        equity คงที่ทั้งวัน (S4) — คืน (trades, skips) เสมอ; cap ปิด → skips ว่าง"""
    c, h, l, o, sp, t = m1["c"], m1["h"], m1["l"], m1["o"], m1["sp"], m1["t"]
    e = ema(c, EMA_P)
    es = np.r_[np.full(SLOPE_B, np.nan), e[SLOPE_B:] - e[:-SLOPE_B]]
    tmin = t.astype("datetime64[m]").astype(np.int64)
    hour = (tmin // 60) % 24
    day = (tmin // 1440).astype(int)
    dow = (day + 4) % 7
    n = len(c)
    trades = []
    skips = []                      # (date, R, threshold, margin) — วันที่ cap ตัด
    equity = deposit if deposit is not None else 0.0
    pos = None
    cur_d = -1
    ash = asl = np.nan
    traded = set()
    slip_stop = SLIP_STOP * spread_mult
    for i in range(start, n):
        if day[i] != cur_d:
            cur_d = day[i]; ash = asl = np.nan
        if 1 <= hour[i] < 8:
            ash = h[i] if np.isnan(ash) else max(ash, h[i])
            asl = l[i] if np.isnan(asl) else min(asl, l[i])
        if pos is not None:
            d, ent, stop, best, R, et = pos
            hit = l[i] <= stop if d == 1 else h[i] >= stop
            if hit:
                px = (min(stop, o[i]) if d == 1 else max(stop, o[i])) - slip_stop * d
                ex = px if d == 1 else px + sp[i] * PT * spread_mult
                pnl = (ex - ent) * d if d == 1 else (ent - ex)
                trades.append((et, t[i], d, ent, ex, pnl, "stop", R))
                equity += pnl
                pos = None
                continue
            if hour[i] >= (20 if dow[i] == 5 else 23):
                ex = c[i] if d == 1 else c[i] + sp[i] * PT * spread_mult
                pnl = (ex - ent) if d == 1 else (ent - ex)
                trades.append((et, t[i], d, ent, ex, pnl, "eod", R))
                equity += pnl
                pos = None
                continue
            best = max(best, c[i]) if d == 1 else min(best, c[i])
            fav = (best - ent) if d == 1 else (ent - best)
            if fav >= A * R:
                ns = best - D * R if d == 1 else best + D * R
                stop = max(stop, ns) if d == 1 else min(stop, ns)
            pos = (d, ent, stop, best, R, et)
            continue
        if cur_d in traded or not (8 <= hour[i - 1] < 20):
            continue
        if not (np.isfinite(ash) and np.isfinite(asl)) or ash <= asl:
            continue
        j = i - 1
        if sp[j] > MAX_SPREAD_PT or not np.isfinite(es[j]):
            continue
        R = ash - asl
        long_sig = c[j] > ash and c[j - 1] <= ash and c[j] > e[j] and es[j] > SLOPE * c[j]
        short_sig = (allow_short and c[j] < asl and c[j - 1] >= asl and c[j] < e[j]
                     and es[j] < -SLOPE * c[j])
        if not (long_sig or short_sig):
            continue
        # S1/S3: risk-cap mirror — เช็คด้วย equity ก่อนเปิด (= balance เพราะ flat)
        if deposit is not None:
            thr = cap_frac * equity
            if R > thr:
                skips.append((str(t[i])[:10], R, thr, R - thr))
                traded.add(cur_d)      # S4: day-level skip (เทียบเท่า EA — R/equity คงที่ทั้งวัน)
                continue
        if long_sig:
            ent = o[i] + sp[i] * PT * spread_mult + SLIP_IN
            traded.add(cur_d)
            pos = (1, ent, max(asl, ent - CAPR * R), ent, R, t[i])
        else:
            ent = o[i] - SLIP_IN
            traded.add(cur_d)
            pos = (-1, ent, min(ash, ent + CAPR * R), ent, R, t[i])
    return trades, skips


def self_check(m1, start, cfg):
    """Instrumented (cap ปิด) ต้องเท่ากับ canonical เป๊ะ — ไม่เท่า = เครื่องมือเชื่อไม่ได้ abort (S2)"""
    canon = run(m1, start, **cfg)
    det, cap_skips = run_detailed(m1, start, **cfg)
    if cap_skips:
        raise SystemExit("SELF-CHECK FAIL: cap ปิดแต่มี skips — logic รั่ว")
    if len(canon) != len(det):
        raise SystemExit(f"SELF-CHECK FAIL: n canonical={len(canon)} instrumented={len(det)}")
    overnight = []
    for k, (cn, dt) in enumerate(zip(canon, det)):
        # canonical: (exit_time, pnl, reason) / detailed: (..., exit_time=1, pnl=5, reason=6)
        if cn[0] != dt[1] or abs(cn[1] - dt[5]) > 1e-9 or cn[2] != dt[6]:
            raise SystemExit(f"SELF-CHECK FAIL at trade {k}: canonical={cn} instrumented={dt}")
        # invariants ของ field ที่ canonical ไม่มีให้เทียบ (entry_time/dir) — Engineer LOW-6:
        # entry อยู่หน้าต่าง 08-20 · dir ±1 · ปกติปิดวันเดียวกัน (EOD) — ยกเว้นวันหยุดตลาด
        # ปิดเร็วไม่มี bar 23:00 → canonical sim ถือข้ามคืนจริง (เช่น Presidents' Day 2023-02-20)
        # = พฤติกรรมที่ต้องสะท้อน ไม่ใช่ซ่อน → นับ+รายงานดัง · เกิน 1 วัน = ผิดจริง fail
        et, xt, d = dt[0], dt[1], dt[2]
        gap_days = (np.datetime64(str(xt)[:10]) - np.datetime64(str(et)[:10])) // np.timedelta64(1, "D")
        # ถือข้ามวันเกิดได้ 2 ทางจริง: ตลาดปิดเร็ว (วันหยุด) หรือ data hole ใน CSV
        # (เช่น 2023-11-15 12:59 -> 11-17 07:00 หาย 42 ชม.) — ต้องรายงานดัง · >5 วัน = ผิดจริง
        if gap_days > 5:
            raise SystemExit(f"INVARIANT FAIL trade {k}: entry {et} / exit {xt} ห่าง {gap_days} วัน")
        if gap_days >= 1:
            overnight.append((str(et)[:16], str(xt)[:16], int(gap_days), dt[6]))
        eh = int(str(et)[11:13])
        if not (8 <= eh <= 20):
            raise SystemExit(f"INVARIANT FAIL trade {k}: entry hour {eh} นอกหน้าต่าง 08-20")
        if d not in (1, -1):
            raise SystemExit(f"INVARIANT FAIL trade {k}: dir={d}")
    print(f"  self-check PASS: instrumented == canonical ({len(canon)} trades exact) + invariants")
    if overnight:
        print(f"  !! overnight holds (ตลาดปิดเร็ว ไม่มี bar 23:00 — sim ถือข้ามคืนจริง): "
              f"{len(overnight)} ไม้: {overnight}")
    return det


# ---------- tester diag loader ----------
def load_diag(fname):
    """คืน list ของ dict ต่อไม้จาก MT5 diag CSV"""
    rows = []
    with open(DIAG / fname, newline="") as f:
        for r in csv.DictReader(f):
            ot = datetime.strptime(r["open_time"], "%Y.%m.%d %H:%M:%S")
            ct = datetime.strptime(r["close_time"], "%Y.%m.%d %H:%M:%S")
            rows.append(dict(open=ot, close=ct, dir=int(r["dir"]),
                             pnl=float(r["realized_usd"]), reason=r["exit_reason"],
                             r=float(r["atr_entry"])))   # atr_entry = R (Trellis.mq5:264)
    return rows


REASON_MAP = {"stop": "sl", "eod": "eod"}  # sim reason -> tester reason family


def tester_reason_family(reason):
    if reason.startswith("sl"):
        return "sl"
    if reason == "eod":
        return "eod"
    return reason  # risk-layer exits (max-total-DD ฯลฯ) โผล่ = ต้องเห็น ไม่กลืน


# ---------- decomposition ----------
def decompose(sim_trades, tst_trades, year):
    """gap identity: tester_net - sim_net = drift(common) + flip_in(tester-only) - flip_out(sim-only)"""
    sim_y = [x for x in sim_trades if str(x[0])[:4] == str(year)]
    tst_y = [x for x in tst_trades if x["open"].year == year]
    if not sim_y and not tst_y:
        return None
    sim_by_day = {}
    for x in sim_y:
        d = str(x[0])[:10]
        if d in sim_by_day:
            raise SystemExit(f"sim: >1 trade/day at {d} — ผิด invariant 1 เทรด/วัน")
        sim_by_day[d] = x
    tst_by_day = {}
    for x in tst_y:
        d = x["open"].strftime("%Y-%m-%d")
        if d in tst_by_day:
            raise SystemExit(f"tester: >1 trade/day at {d} — ผิด invariant 1 เทรด/วัน")
        tst_by_day[d] = x

    # coverage: tester file อาจจบก่อน sim data (เช่น BT จบ 26 ธ.ค. 2025) — รายงาน ไม่ทิ้งเงียบ
    tst_last = max(tst_by_day) if tst_by_day else None
    tst_first = min(tst_by_day) if tst_by_day else None
    sim_out_of_cov = {d: x for d, x in sim_by_day.items() if tst_last and d > tst_last}
    sim_in = {d: x for d, x in sim_by_day.items() if d not in sim_out_of_cov}

    common = sorted(set(sim_in) & set(tst_by_day))
    sim_only = sorted(set(sim_in) - set(tst_by_day))
    tst_only = sorted(set(tst_by_day) - set(sim_in))

    sim_net = sum(sim_in[d][5] for d in sim_in)
    tst_net = sum(x["pnl"] for x in tst_y)
    gap = tst_net - sim_net

    drift = sum(tst_by_day[d]["pnl"] - sim_in[d][5] for d in common)
    flip_in = sum(tst_by_day[d]["pnl"] for d in tst_only)
    flip_out = sum(sim_in[d][5] for d in sim_only)
    resid = gap - (drift + flip_in - flip_out)
    if abs(resid) > 1e-6:
        raise SystemExit(f"DECOMP IDENTITY FAIL {year}: gap={gap:.2f} != "
                         f"drift {drift:.2f} + flip_in {flip_in:.2f} - flip_out {flip_out:.2f}")

    dir_mismatch = [d for d in common if tst_by_day[d]["dir"] != sim_in[d][2]]
    # G0-3 R-match: tester atr_entry (=R) vs sim R (tuple index 7) บนวัน common
    rmatch = []
    for d in common:
        if len(sim_in[d]) > 7 and "r" in tst_by_day[d]:
            rmatch.append((d, tst_by_day[d]["r"] - sim_in[d][7]))
    # entry-time alignment: sim entry = เวลา bar เข้า (นาที) vs tester open_time
    # เข้าเวลาเดียวกัน = drift มาจาก fill/exit · เข้าคนละเวลา = drift มาจาก signal timing
    same_entry, diff_entry = [], []
    for d in common:
        sim_min = str(sim_in[d][0])[:16].replace("T", " ")
        tst_min = tst_by_day[d]["open"].strftime("%Y-%m-%d %H:%M")
        (same_entry if sim_min == tst_min else diff_entry).append(d)
    reason_pairs = {}
    for d in common:
        key = f"{REASON_MAP.get(sim_in[d][6], sim_in[d][6])}->" \
              f"{tester_reason_family(tst_by_day[d]['reason'])}"
        dr = tst_by_day[d]["pnl"] - sim_in[d][5]
        agg = reason_pairs.setdefault(key, [0, 0.0])
        agg[0] += 1
        agg[1] += dr
    top = sorted(common, key=lambda d: -abs(tst_by_day[d]["pnl"] - sim_in[d][5]))[:10]

    return dict(year=year, sim_n=len(sim_in), tst_n=len(tst_y), sim_net=sim_net,
                tst_net=tst_net, gap=gap, common=common, sim_only=sim_only,
                tst_only=tst_only, drift=drift, flip_in=flip_in, flip_out=flip_out,
                dir_mismatch=dir_mismatch, reason_pairs=reason_pairs, top=top,
                same_entry=same_entry, diff_entry=diff_entry, rmatch=rmatch,
                sim_by_day=sim_in, tst_by_day=tst_by_day, cov=(tst_first, tst_last),
                out_of_cov=sim_out_of_cov)


def report(r):
    y = r["year"]
    nu = len(set(r["common"]) | set(r["sim_only"]) | set(r["tst_only"]))
    nfl = len(r["sim_only"]) + len(r["tst_only"])
    print(f"\n===== {y} =====  [SIM=bar-M1 pessimistic | TESTER=MT5 real-tick authority]")
    print(f"  coverage tester: {r['cov'][0]} .. {r['cov'][1]}")
    if r["out_of_cov"]:
        oc_net = sum(x[5] for x in r["out_of_cov"].values())
        print(f"  !! sim trades หลัง coverage tester: {len(r['out_of_cov'])} ไม้ net {oc_net:+.1f}"
              f" (ตัดออกจาก decomposition — รายงานตรงนี้ ไม่ทิ้งเงียบ)")
    print(f"  n: sim={r['sim_n']} tester={r['tst_n']} · net: sim={r['sim_net']:+.1f}"
          f" tester={r['tst_net']:+.1f} · GAP={r['gap']:+.1f}")
    print(f"  participation: common={len(r['common'])} sim-only={len(r['sim_only'])}"
          f" tester-only={len(r['tst_only'])} · flip {nfl}/{nu} วัน = {100*nfl/max(nu,1):.0f}%")
    print(f"  DECOMP: (b) drift common     = {r['drift']:+8.1f}"
          f"  ({r['drift']/max(len(r['common']),1):+.2f}/ไม้, {len(r['common'])} ไม้)")
    print(f"          (a) flips net        = {r['flip_in']-r['flip_out']:+8.1f}"
          f"  (tester-only {r['flip_in']:+.1f} - sim-only {r['flip_out']:+.1f})")
    print(f"          identity: gap = drift + flips_net  ✓ ปิดเป๊ะ")
    if r["dir_mismatch"]:
        print(f"  dir mismatch ในวัน common: {len(r['dir_mismatch'])} วัน: {r['dir_mismatch']}")
    se, de = r["same_entry"], r["diff_entry"]
    dr_se = sum(r["tst_by_day"][d]["pnl"] - r["sim_by_day"][d][5] for d in se)
    dr_de = sum(r["tst_by_day"][d]["pnl"] - r["sim_by_day"][d][5] for d in de)
    print(f"  entry-time alignment (นาทีเดียวกัน?): same={len(se)} (ΣΔ={dr_se:+.1f},"
          f" avg {dr_se/max(len(se),1):+.2f}) · diff={len(de)} (ΣΔ={dr_de:+.1f},"
          f" avg {dr_de/max(len(de),1):+.2f})")
    if de:
        worst_de = sorted(de, key=lambda d: -abs(r["tst_by_day"][d]["pnl"] - r["sim_by_day"][d][5]))[:5]
        for d in worst_de:
            s, tt = r["sim_by_day"][d], r["tst_by_day"][d]
            print(f"    diff-entry {d}: sim {str(s[0])[11:16]} vs tester"
                  f" {tt['open'].strftime('%H:%M')}  Δ={tt['pnl']-s[5]:+.1f}")
        # histogram Δนาที (tester - sim) — offset เป็นระบบ (เช่น -120/-180) = หลักฐาน clock shift
        # (structural evidence เท่านั้น — proof จริงต้อง price-match ตามกฎ CLAUDE.md)
        from collections import Counter
        deltas = Counter()
        for d in de:
            sm = np.datetime64(str(r["sim_by_day"][d][0])[:16])
            tm = np.datetime64(r["tst_by_day"][d]["open"].strftime("%Y-%m-%dT%H:%M"))
            deltas[int((tm - sm) / np.timedelta64(1, "m"))] += 1
        top_d = deltas.most_common(6)
        print(f"  Δentry-minute histogram (tester-sim) top: "
              + " ".join(f"{k:+d}min×{v}" for k, v in top_d))
        # แยกตามเดือน เฉพาะ delta ที่เป็นชั่วโมงกลม (DST structure?)
        by_mon = {}
        for d in de:
            sm = np.datetime64(str(r["sim_by_day"][d][0])[:16])
            tm = np.datetime64(r["tst_by_day"][d]["open"].strftime("%Y-%m-%dT%H:%M"))
            dm = int((tm - sm) / np.timedelta64(1, "m"))
            if dm % 60 == 0:
                by_mon.setdefault(d[5:7], Counter())[dm // 60] += 1
        if by_mon:
            print("  ชั่วโมงกลมตามเดือน: " + " ".join(
                f"{m}:{dict(c)}" for m, c in sorted(by_mon.items())))
    if r.get("rmatch"):
        adr = sorted(abs(x[1]) for x in r["rmatch"])
        p95 = adr[int(0.95 * (len(adr) - 1))]
        worst = max(r["rmatch"], key=lambda x: abs(x[1]))
        print(f"  R-match (tester atr_entry vs sim R, n={len(adr)}): p95|dR|={p95:.2f}"
              f" max={worst[1]:+.2f} @ {worst[0]}  [G0-3: p95 < $2]")
    print("  drift ตาม exit-reason pair (sim->tester):")
    for k, (cnt, tot) in sorted(r["reason_pairs"].items(), key=lambda kv: kv[1][1]):
        print(f"    {k:<12} n={cnt:>3}  ΣΔ={tot:+8.1f}  avgΔ={tot/cnt:+6.2f}")
    print("  top-10 |drift| วัน common (sim_pnl -> tester_pnl, reason sim->tester):")
    for d in r["top"]:
        s, tt = r["sim_by_day"][d], r["tst_by_day"][d]
        print(f"    {d}  {s[5]:+7.1f} -> {tt['pnl']:+7.1f}  Δ={tt['pnl']-s[5]:+7.1f}"
              f"  [{s[6]}->{tt['reason']}] dir sim={s[2]:+d}/tst={tt['dir']:+d}")


DST_BOUNDS = {
    # DST เริ่ม/จบ ต่อปี — US: 2nd Sun Mar / 1st Sun Nov · EU: last Sun Mar / last Sun Oct
    "us": {2024: ("03-10", "11-03"), 2025: ("03-09", "11-02"), 2026: ("03-08", "11-01")},
    "eu": {2024: ("03-31", "10-27"), 2025: ("03-30", "10-26"), 2026: ("03-29", "10-25")},
}


def dst_shift_minutes(t, rule):
    """คืน array นาทีที่ต้อง 'ลบ' จาก BT-clock เพื่อได้ UTC+0: 120 หนาว / 180 ร้อน ตามกฎ DST ที่เลือก"""
    out = np.full(len(t), 120, dtype=np.int64)
    for y, (b0, b1) in DST_BOUNDS[rule].items():
        lo = np.datetime64(f"{y}-{b0}")
        hi = np.datetime64(f"{y}-{b1}")
        out[(t >= lo) & (t < hi)] = 180
    return out


def mode_shift(rule):
    """Reproduction test: sim บน clock ที่ shift เป็น UTC+0 (สมมติฐาน: BT 2025 = UTC+0)
    prediction us (ประกาศรอบแรก): alignment>=90% · flips ~1-2% · net 2025 ~ -169
    prediction eu (ประกาศรอบสอง หลัง price-match ชี้ M1 CSV = EU-DST): alignment >=95% ·
      16 วันขอบ DST ของรอบ us ต้องหายเกือบหมด"""
    print(f"== Stage 0.1b reproduction: sim on UTC+0-shifted clock ({rule.upper()}-DST) vs tester v4c_2526 ==")
    m1 = load_full([2024, 2025, 2026])
    m1 = dict(m1)
    m1["t"] = m1["t"] - dst_shift_minutes(m1["t"], rule).astype("timedelta64[m]")
    start = int(np.searchsorted(m1["t"], np.datetime64("2025-01-01")))
    sim_sh, _ = run_detailed(m1, start, **DEPLOY_CFG)   # self_check ใช้ไม่ได้กับ clock ดัดแปลง — canonical เทียบใน mode หลักแล้ว
    tst = load_diag(TESTER_FILES[1][1])
    r = decompose(sim_sh, tst, 2025)
    report(r)


def main():
    print("== TRELLIS-010 Stage 0.1 decomposition ==")
    print(f"config (deploy/WF): {DEPLOY_CFG}")
    print("\n-- sim 2023-2024 (warmup 2022) --")
    m1 = load_full([2022, 2023, 2024])
    sim_2324 = self_check(m1, year_start_index(m1, 2023), DEPLOY_CFG)
    print("-- sim 2025-2026 (warmup 2024) --")
    m1 = load_full([2024, 2025, 2026])
    sim_2526 = self_check(m1, year_start_index(m1, 2025), DEPLOY_CFG)

    tst_2324 = load_diag(TESTER_FILES[0][1])
    tst_2526 = load_diag(TESTER_FILES[1][1])
    tst_2601 = load_diag(TESTER_FILES[2][1])
    print(f"\ntester files: {TESTER_FILES[0][1]} n={len(tst_2324)}"
          f" · {TESTER_FILES[1][1]} n={len(tst_2526)}"
          f" · {TESTER_FILES[2][1]} n={len(tst_2601)}")

    results = []
    for year, sim_t, tst_t in [(2023, sim_2324, tst_2324), (2024, sim_2324, tst_2324),
                               (2025, sim_2526, tst_2526), (2026, sim_2526, tst_2601)]:
        r = decompose(sim_t, tst_t, year)
        if r:
            results.append(r)
            report(r)

    print("\n===== SUMMARY ต่อปี (สนาม: gap = TESTER - SIM) =====")
    print(f"{'year':<6}{'gap':>9}{'(b)drift':>10}{'(a)flips':>10}{'drift/ไม้':>11}{'flip%':>7}")
    for r in results:
        nu = len(set(r["common"]) | set(r["sim_only"]) | set(r["tst_only"]))
        nfl = len(r["sim_only"]) + len(r["tst_only"])
        print(f"{r['year']:<6}{r['gap']:>+9.1f}{r['drift']:>+10.1f}"
              f"{r['flip_in']-r['flip_out']:>+10.1f}"
              f"{r['drift']/max(len(r['common']),1):>+11.2f}{100*nfl/max(nu,1):>6.0f}%")
    tot_gap = sum(r["gap"] for r in results)
    tot_drift = sum(r["drift"] for r in results)
    tot_flip = sum(r["flip_in"] - r["flip_out"] for r in results)
    print(f"{'TOTAL':<6}{tot_gap:>+9.1f}{tot_drift:>+10.1f}{tot_flip:>+10.1f}")
    dom = "(b) per-trade drift" if abs(tot_drift) > abs(tot_flip) else "(a) participation flips"
    print(f"\nองค์ประกอบที่ครอง |gap| รวม: {dom}"
          f"  (|drift|={abs(tot_drift):.0f} vs |flips|={abs(tot_flip):.0f})")


# ---------- Gate 0 @ deposit 3000 (mirror-cap — ระบบจริง) ----------
GATE0_DEPOSIT = 3000.0
GATE0_RUNS = [
    # (year, sim_start, tester diag file — tag ที่วินรัน)
    (2025, "2025-01-01", "Trellis_diag_770001_v4f_25.csv"),
    (2026, "2026-01-01", "Trellis_diag_770001_v4f_2601.csv"),
]
# S6: วันเฉียดเส้น |R-threshold| < $2 — ชุดเดียวที่ participation ต่างได้ (pre-registered)
NEAR_BOUNDARY = {2025: ["2025-04-10", "2025-05-06", "2025-06-13"],
                 2026: ["2026-01-02", "2026-01-20", "2026-01-22"]}


def capped_year(m1, year, start_date):
    """รัน capped sim สำหรับ tester run แยกปี (equity เริ่ม GATE0_DEPOSIT ใหม่) + S5 tripwire"""
    start = int(np.searchsorted(m1["t"], np.datetime64(start_date)))
    trades, skips = run_detailed(m1, start, **DEPLOY_CFG, deposit=GATE0_DEPOSIT)
    trades = [x for x in trades if str(x[0])[:4] == str(year)]
    skips = [s for s in skips if s[0][:4] == str(year)]
    p = np.array([x[5] for x in trades])
    if len(p):
        if (p < -150).any():
            raise SystemExit("S5 TRIPWIRE: มีไม้ loss เกิน $150 — backstop assumption แตก ต้อง mirror backstops")
        cum = np.cumsum(p)
        if (np.maximum.accumulate(cum) - cum).max() > 750:
            raise SystemExit("S5 TRIPWIRE: cumDD เกิน $750 — max-total-DD จะ fire ใน tester")
    return trades, skips


def equity_thresholds(rows_sorted, deposit, get_pnl, get_date):
    """threshold 2%×equity ก่อนไม้แต่ละวัน — ใช้ทั้งฝั่ง sim และ tester (reconstruct)"""
    thr = {}
    eq = deposit
    for x in rows_sorted:
        thr[get_date(x)] = 0.02 * eq
        eq += get_pnl(x)
    return thr


def gate0_checks(year, r, sim_trades, sim_skips, tst, deposit):
    print(f"\n  ----- G0 checklist {year} "
          f"[tester skip-set = อนุมานจากการไม่มีไม้ — tester ไม่ log cap-skip ตรง (Finding D)] -----")
    common, same = r["common"], r["same_entry"]
    miss = len(common) - len(same)
    allow_miss = 2 if year == 2025 else 1
    print(f"  G0-1 alignment: {len(same)}/{len(common)} (miss {miss}, เกณฑ์ ≤{allow_miss})"
          f" -> {'PASS' if miss <= allow_miss else 'FAIL'}")
    # unambiguous-take subpop (S7): R ต่ำกว่า threshold ทั้งสองฝั่งเกิน $10
    sim_thr = equity_thresholds(sim_trades, deposit, lambda x: x[5], lambda x: str(x[0])[:10])
    tst_sorted = sorted(tst, key=lambda x: x["open"])
    tst_thr = equity_thresholds(tst_sorted, deposit, lambda x: x["pnl"],
                                lambda x: x["open"].strftime("%Y-%m-%d"))
    sim_by_day = {str(x[0])[:10]: x for x in sim_trades}
    unamb = [d for d in common
             if len(sim_by_day[d]) > 7 and sim_by_day[d][7] < sim_thr.get(d, 60) - 10
             and r["tst_by_day"][d].get("r", 999) < tst_thr.get(d, 60) - 10]
    un_same = [d for d in unamb if d in same]
    if unamb:
        pct = 100 * len(un_same) / len(unamb)
        print(f"  G0-1b unambiguous-take: {len(un_same)}/{len(unamb)} = {pct:.1f}%"
              f" (เกณฑ์ ≥99%) -> {'PASS' if pct >= 99 else 'FAIL'}")
    # G0-6/7 skip-set agreement
    tst_days = set(r["tst_by_day"].keys())
    print(f"  G0-6/7 skip-set (sim cap-skip {len(sim_skips)} วัน):")
    fail7 = False
    for dstr, R, thr, margin in sim_skips:
        traded_t = dstr in tst_days
        band = "pre-reg" if dstr in NEAR_BOUNDARY.get(year, []) else (
            "OK" if not traded_t else ("$2-4" if abs(margin) < 4 else "FAIL"))
        if traded_t and abs(margin) >= 4 and dstr not in NEAR_BOUNDARY.get(year, []):
            fail7 = True
        print(f"    {dstr} R={R:.1f} thr={thr:.1f} margin={margin:+.2f}"
              f" tester_traded={traded_t} [{band}]")
    # sim-only (sim เข้า tester ไม่เข้า): attribute cap-boundary vs unexplained
    for d in r["sim_only"]:
        s = r["sim_by_day"][d]
        R = s[7] if len(s) > 7 else float("nan")
        tt = tst_thr.get(d)
        att = "no-tester-thr"
        if tt is not None or True:
            # tester thr ณ วันนั้น = 2%×equity ก่อนไม้ถัดไป — ใช้ค่า thr ของวันเทรดถัดไปเป็น proxy
            att = "CAP-boundary?" if (not np.isnan(R) and tt and R > tt - 2) else "UNEXPLAINED"
        print(f"    sim-only {d}: sim R={R:.1f} -> {att}")
        if att == "UNEXPLAINED":
            fail7 = True
    print(f"  G0-7 verdict: {'FAIL — มี disagreement นอก band' if fail7 else 'PASS'}")
    print(f"  G0-5 gap={r['gap']:+.1f} ({'gate ≤$80' if year == 2025 else 'รายงานอย่างเดียว (n เล็ก)'})"
          f" · G0-4 drift/ไม้={r['drift']/max(len(common),1):+.2f} (เกณฑ์ −0.5..+0.2)")


def mode_predict():
    """Pre-registered prediction (สนาม sim capped@3000 กฎ EU) — รันสดจาก script นี้เท่านั้น"""
    print("== PRE-REGISTERED PREDICTION — Gate 0 v4f (mirror-cap, deposit 3000/run, สนาม SIM) ==")
    m1 = load_full([2024, 2025, 2026])
    for year, start_date, fname in GATE0_RUNS:
        trades, skips = capped_year(m1, year, start_date)
        p = np.array([x[5] for x in trades])
        if not len(p):
            print(f"\n  v4f {year}: no trades")
            continue
        cum = np.cumsum(p)
        dd = (np.maximum.accumulate(cum) - cum).max()
        print(f"\n  v4f {year}: n={len(p)} net={p.sum():+.1f} maxDD={dd:.1f}"
              f" worst_trade={p.min():+.1f} · cap-skip {len(skips)} วัน")
        print("  skip days: " + " ".join(f"{s[0]}(R{s[1]:.0f},m{s[3]:+.1f})" for s in skips))
        print(f"  near-boundary pre-registered (|margin|<$2 — ต่างได้เฉพาะชุดนี้): {NEAR_BOUNDARY[year]}")


def mode_gate0():
    """Gate 0 evaluation: capped sim vs tester v4f (รันหลังวินส่งผล)"""
    print("== GATE 0 EVALUATION — mirror-cap @ deposit 3000 (ระบบจริง) ==")
    m1 = load_full([2024, 2025, 2026])
    for year, start_date, fname in GATE0_RUNS:
        if not (DIAG / fname).exists():
            raise SystemExit(f"ไม่พบ {fname} — วินยังไม่รัน หรือ DiagTag ไม่ตรง")
        trades, skips = capped_year(m1, year, start_date)
        tst = load_diag(fname)
        r = decompose(trades, tst, year)
        report(r)
        gate0_checks(year, r, trades, skips, tst, GATE0_DEPOSIT)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "shift":
        mode_shift("us")
    elif arg == "shift-eu":
        mode_shift("eu")
    elif arg == "predict":
        mode_predict()
    elif arg == "gate0":
        mode_gate0()
    else:
        main()
