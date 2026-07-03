#!/usr/bin/env python3
"""
stage0_verify_import.py — TRELLIS-010 Stage 0: verify ไฟล์ bars+ticks ที่ import เข้า XAUUSD_BT
(ฝั่งไฟล์ต้นทางใน MQL5/Files — ฝั่ง terminal ใช้ Scripts/VerifyBTClock.mq5 คู่กัน)

ตรวจ:
1. Tick count ต่อไฟล์ == ตัวเลข "Read/Imported" ใน import log (68,131,640 / 15,346,672)
   + epoch เรียงไม่ย้อน + first/last label
2. M1 CSV bar count == ตัวเลข import log (344,412 / 50,259) + first/last ตรง log
3. Bar↔Tick consistency: sample หลายนาทีคร่อมทุกฤดู (หนาว/shoulder/ร้อน) —
   OHLC ของ M1 bar ต้องตรง first/max/min/last ของ bid ticks ในนาทีนั้น
Usage: python stage0_verify_import.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FILES = Path(r"C:/Users/itd_surachartt/AppData/Roaming/MetaQuotes/Terminal/D2FFA7C3BAACDDB0A9486309DC86D5C4/MQL5/Files")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# ค่าคาดหวังจาก import log 2026-07-03 16:33-16:35 (วินส่งมา)
EXPECT = {
    2025: dict(ticks=68_131_640, bars=344_412, bar_first="2025.01.02\t01:00:00", bar_last="2025.12.31\t23:58:00"),
    2026: dict(ticks=15_346_672, bars=50_259, bar_first="2026.01.02\t01:00:00", bar_last="2026.02.23\t15:59:00"),
}
# นาทีตัวอย่างตรวจ bar<->ticks (BT-clock): หนาว · shoulder มี.ค. (US-on/EU-off) · ร้อน · shoulder ต.ค. · ธ.ค.
SAMPLE_MINUTES = {
    2025: ["2025-01-15 10:30", "2025-03-17 00:00", "2025-03-20 15:00", "2025-07-08 12:00",
           "2025-10-28 09:00", "2025-12-15 20:00"],
    2026: ["2026-01-15 10:30", "2026-02-20 15:00"],
}


def label(ms):
    return EPOCH + timedelta(milliseconds=ms)


def scan_ticks(path, expect_n):
    n = 0
    prev = -1
    first = last = None
    mono_ok = True
    with open(path, "rb") as f:
        for line in f:
            ep = int(line.split(b"\t", 1)[0])
            if first is None:
                first = ep
            if ep < prev:
                mono_ok = False
            prev = ep
            n += 1
    last = prev
    ok = (n == expect_n) and mono_ok
    print(f"  ticks n={n:,} (expect {expect_n:,}) {'OK' if n == expect_n else '** MISMATCH **'}"
          f" · monotonic={'OK' if mono_ok else '** FAIL **'}"
          f" · first={label(first):%Y-%m-%d %H:%M:%S} last={label(last):%Y-%m-%d %H:%M:%S}")
    return ok


def find_ticks_in_minute(path, t0):
    """binary-seek หา ticks ในนาที [t0, t0+60s) — คืน list ของ bid"""
    lo_ms = int((t0.replace(tzinfo=timezone.utc) - EPOCH).total_seconds() * 1000)
    hi_ms = lo_ms + 60_000
    import os
    sz = os.path.getsize(path)
    lo, hi = 0, sz
    with open(path, "rb") as f:
        for _ in range(48):                      # binary search byte offset
            mid = (lo + hi) // 2
            f.seek(mid); f.readline()
            line = f.readline()
            if not line:
                hi = mid; continue
            ep = int(line.split(b"\t", 1)[0])
            if ep < lo_ms:
                lo = mid
            else:
                hi = mid
        f.seek(lo); f.readline()
        bids = []
        for line in f:
            p = line.split(b"\t")
            ep = int(p[0])
            if ep < lo_ms:
                continue
            if ep >= hi_ms:
                break
            bids.append(float(p[1]))
    return bids


def verify_year(y):
    print(f"\n===== {y} =====")
    e = EXPECT[y]
    tick_path = FILES / f"XAUUSD_ticks_eet_{y}.csv"
    m1_path = FILES / f"XAUUSD_M1_{y}.csv"

    ok = scan_ticks(tick_path, e["ticks"])

    bars = {}
    n = 0
    first = last = None
    with open(m1_path) as f:
        for line in f:
            n += 1
            key = line.split("\t")[0] + "\t" + line.split("\t")[1]
            if first is None:
                first = key
            last = key
            bars[key] = line
    bar_ok = (n == e["bars"] and first == e["bar_first"] and last == e["bar_last"])
    print(f"  bars n={n:,} (expect {e['bars']:,}) first={first.replace(chr(9),' ')} "
          f"last={last.replace(chr(9),' ')} {'OK' if bar_ok else '** MISMATCH **'}")
    ok = ok and bar_ok

    print("  bar<->ticks consistency (O/H/L/C vs first/max/min/last bid):")
    for m in SAMPLE_MINUTES[y]:
        t0 = datetime.strptime(m, "%Y-%m-%d %H:%M")
        key = t0.strftime("%Y.%m.%d\t%H:%M:00")
        if key not in bars:
            print(f"    {m}: ไม่มี bar ใน M1 CSV (ตลาดปิด/gap) — ข้าม")
            continue
        p = bars[key].rstrip("\n").split("\t")
        o, h, l, c = float(p[2]), float(p[3]), float(p[4]), float(p[5])
        bids = find_ticks_in_minute(tick_path, t0)
        if not bids:
            print(f"    {m}: bar มีแต่ tick ไม่มี ** MISMATCH **")
            ok = False
            continue
        to, th, tl, tc = bids[0], max(bids), min(bids), bids[-1]
        match = (abs(o - to) < 1e-9 and abs(h - th) < 1e-9 and abs(l - tl) < 1e-9 and abs(c - tc) < 1e-9)
        print(f"    {m}: bar O{o} H{h} L{l} C{c} · ticks({len(bids)}) O{to} H{th} L{tl} C{tc}"
              f" {'OK' if match else '** DIFF **'}")
        ok = ok and match
    return ok


if __name__ == "__main__":
    all_ok = True
    for y in (2025, 2026):
        all_ok = verify_year(y) and all_ok
    print(f"\nRESULT: {'ALL OK' if all_ok else '** พบความไม่ตรง — ดูบรรทัด MISMATCH/DIFF **'}")
