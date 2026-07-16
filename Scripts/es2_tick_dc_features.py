#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
es2_tick_dc_features.py — TRELLIS-010 · Card ES-2 extractor: tick-DC event-stream features
Spec v2 frozen หลัง Engineer 3 รอบ (R1 B-1/B-2/M-1..4 · R2 M-A..D + asym-degeneracy discovery ·
R3 PASS-with-changes P1-P4 implement-time) + Claude-Verify ทุกรอบ · card = `es2_card.py` (CLAIM-0018)

FIREWALL: อ่าน day_facts ผ่าน manifest (date/traded/entry_time/dir เท่านั้น — tp1 pattern) · ไม่แตะ P&L
BASIS: bid ticks เท่านั้น · window [01:00, B) · B = (tmin_j+1)·60000 = wall-close ของ signal bar j
  (strict `<` · as-of glossary · proven ใน TP-1)
FEATURES (8 · δ ∈ {0.1, 0.25, 0.5}×aw — คงชุด ES-1 · ไม่มี named pathology จาก occupancy dump
  [n_dc med 71/13/4 · UNDEF 0.0% ทุก scale · single-mode 0/1.1/16.4%]):
  dc_align_δ = mode×d ×3 · dc_os_δ = overshoot/δ ×3 (0-encode UNDEF)
  **tshare@0.1** = (wall-time up-mode − down-mode)/(B−d0100) ×d — แทน slot dc_asym ของ ES-1 แบบ 1:1
    [asym = degenerate-by-construction: alternation ⇒ |up−dn|≤1 — discovery 07-15 · tshare วัดมิติ
    event-imbalance ครั้งแรก · anchor @0.1 = evidence-based (corr(dur) 0.301<0.487 · richest events ·
    tick↔M1 corr 0.12 = มิติใหม่สุด) · declared occupancy-guided contamination]
  **dur_wall@0.25** = (B − epoch(last DC event))/(B−d0100) — wall-time (Q3 · divergence จาก
    tick-count 0.025 declared) · 0 ถ้า UNDEF
  + DIAGNOSTIC cols (non-gating): n_dc ต่อ scale · dur_tick@0.25 (P4 shadow) · n_ticks
GUARDS:
  G1-SOFT: per-minute bid reconstruction vs M1 ≥99.9%/ปี (accumulate-then-assert · TP-1 proven 100%)
  slice-discipline check (54 stratified — corruption ≥B ถูก slice ตัดโดยโครงสร้าง · ตามป้าย ES-1 M2:
    **no-lookahead power = smoke NEG-CTRL boundary-read** [_TEST_B_SHIFT_MS ทำ dissect กิน tick
    หลัง B → features ต้องเปลี่ยน — R3 P2])
  UNDEF assert ==0 exact (วัดจริง 0.0%) + encoding ครบทุก feature = 0 · assert up+dn==n_dc
OUTPUT: frozen CSV + .sha256 + buildlog (pattern tp1/es1) · population-overlap audit ขั้นสุดท้าย
  อยู่ที่ es2_card (join กับ ES-1 population — P1)
⚠ SIM-SEARCH เท่านั้น · lockbox/guard ไม่แตะ
Usage: python es2_tick_dc_features.py smoke | python es2_tick_dc_features.py
"""
import csv
import hashlib
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from tp1_tick_features import manifest_year, FACTS, DATA

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
OUT_CSV = ROOT / "Research/h0/es2_tickdc_2012_2020.csv"
OUT_SHA = ROOT / "Research/h0/es2_tickdc_2012_2020.sha256"
OUT_LOG = ROOT / "Research/h0/es2_tickdc_2012_2020.buildlog.txt"
SCALES = [0.1, 0.25, 0.5]
SOFT_MIN_RATE = 99.9
POST_GUARD_MS = 120_000              # เก็บ ticks เกิน B ไว้ให้ slice-discipline check + NEG-CTRL
GUARD_PER_YEAR = 6
COLS = ["date", "n_ticks", "al_010", "al_025", "al_050", "os_010", "os_025", "os_050",
        "tshare_010", "dur_wall_025", "n_dc_010", "n_dc_025", "n_dc_050", "dur_tick_025"]

# test-only hook (NEG-CTRL boundary-read · smoke เท่านั้น — production assert ==0)
_TEST_B_SHIFT_MS = 0


def dissect_seg(vals, delta):
    """classic DC dissection — mirror es1_card.dissect (mode/hi/lo/dcc logic เป๊ะ · single-pass)
    + segment events (idx, new_mode) · assert alternation-consistency ที่ caller"""
    mode, n_dc, up_dc, down_dc = 0, 0, 0, 0
    hi = lo = vals[0]
    dcc = np.nan
    ev = []
    for i, c in enumerate(vals):
        if mode == 0:
            hi, lo = max(hi, c), min(lo, c)
            if c >= lo + delta:
                mode, dcc, hi = 1, c, c; n_dc += 1; up_dc += 1; ev.append((i, 1))
            elif c <= hi - delta:
                mode, dcc, lo = -1, c, c; n_dc += 1; down_dc += 1; ev.append((i, -1))
        elif mode == 1:
            hi = max(hi, c)
            if c <= hi - delta:
                mode, dcc, lo = -1, c, c; n_dc += 1; down_dc += 1; ev.append((i, -1))
        else:
            lo = min(lo, c)
            if c >= lo + delta:
                mode, dcc, hi = 1, c, c; n_dc += 1; up_dc += 1; ev.append((i, 1))
    assert up_dc + down_dc == n_dc, "DC decomposition broken"
    os_u = 0.0 if mode == 0 else ((vals[-1] - dcc) / delta if mode == 1 else (dcc - vals[-1]) / delta)
    return mode, os_u, n_dc, ev


def es2_features(eps, bids, B, d0100, d, aw):
    """8 features + diagnostics จาก tick arrays ของวันนั้น (อาจมี ticks เกิน B — slice ที่นี่)
    _TEST_B_SHIFT_MS = planted boundary-read bug (smoke NEG-CTRL เท่านั้น)"""
    Bx = B + _TEST_B_SHIFT_MS
    m = (eps < Bx) & (eps >= d0100)
    e, b = eps[m], bids[m]
    span = B - d0100
    out = {"n_ticks": int(len(b))}
    undef = 0
    for s, tag in zip(SCALES, ("010", "025", "050")):
        mode, os_u, n_dc, ev = dissect_seg(b.tolist(), s * aw)
        if mode == 0:
            undef += 1
        out[f"al_{tag}"] = float(mode * d)
        out[f"os_{tag}"] = float(os_u)
        out[f"n_dc_{tag}"] = int(n_dc)
        if s == 0.1:
            t_up = t_dn = 0.0
            for k, (idx, md) in enumerate(ev):
                t_end = int(e[ev[k + 1][0]]) if k + 1 < len(ev) else B
                seg = t_end - int(e[idx])
                if md == 1:
                    t_up += seg
                else:
                    t_dn += seg
            out["tshare_010"] = float(((t_up - t_dn) / span) * d) if ev else 0.0
        if s == 0.25:
            if ev:
                li = ev[-1][0]
                out["dur_wall_025"] = float((B - int(e[li])) / span)
                out["dur_tick_025"] = float((len(b) - 1 - li) / max(1, len(b) - 1))
            else:
                out["dur_wall_025"] = 0.0
                out["dur_tick_025"] = 0.0
    return out, undef


def stream_year(y, man, bars, recon):
    """single pass: เก็บ ticks ต่อ entry-day [d0100, B+guard) + minute-agg ทั้งปี (G1-SOFT)"""
    want = sorted(man.items(), key=lambda kv: kv[1]["d0100"])
    ticks = {dts: ([], []) for dts in man}
    oi, active = 0, []
    cur_min, agg = None, None

    def flush():
        nonlocal cur_min, agg
        if cur_min is None:
            return
        mb = bars.get(cur_min)
        if mb is None:
            recon["tick_only"] += 1
        else:
            ok = (round(agg[0], 3) == round(mb[0], 3) and round(agg[1], 3) == round(mb[1], 3)
                  and round(agg[2], 3) == round(mb[2], 3) and round(agg[3], 3) == round(mb[3], 3)
                  and agg[4] == mb[4])
            recon["n"] += 1
            recon["ok" if ok else "bad"] += 1

    with open(DATA / f"XAUUSD_ticks_eet_{y}.csv") as f:
        for line in f:
            p = line.split("\t", 2)
            t = int(p[0]); bid = float(p[1])
            mm = t // 60000
            if mm != cur_min:
                flush()
                cur_min, agg = mm, [bid, bid, bid, bid, 1]
            else:
                agg[1] = max(agg[1], bid); agg[2] = min(agg[2], bid)
                agg[3] = bid; agg[4] += 1
            while oi < len(want) and t >= want[oi][1]["d0100"]:
                active.append(want[oi][0]); oi += 1
            if active:
                done = []
                for dts in active:
                    m = man[dts]
                    if t >= m["B"] + POST_GUARD_MS:
                        done.append(dts)
                    elif t >= m["d0100"]:
                        e, b = ticks[dts]
                        e.append(t); b.append(bid)
                for dts in done:
                    active.remove(dts)
    flush()
    return ticks


def run_full():
    assert _TEST_B_SHIFT_MS == 0, "test hook ต้อง 0 ใน production"
    facts_rows = [r for r in csv.DictReader(
        ln for ln in open(FACTS, encoding="utf-8") if not ln.startswith("#"))]
    out, log_lines, soft_fail, guard_fail = [], [], [], []
    undef_total, guard_done = 0, 0
    t0 = time.time()
    for y in range(2012, 2021):
        bars, man, skip = manifest_year(y, facts_rows)
        recon = dict(n=0, ok=0, bad=0, tick_only=0)
        ticks = stream_year(y, man, bars, recon)
        rate = recon["ok"] / recon["n"] * 100 if recon["n"] else 0.0
        if rate < SOFT_MIN_RATE:
            soft_fail.append((y, round(rate, 4)))
        ln = (f"[G1-SOFT {y}] bars={recon['n']} match={rate:.4f}% bad={recon['bad']} "
              f"tick-only={recon['tick_only']} · {time.time() - t0:.0f}s")
        print(ln, flush=True); log_lines.append(ln)
        gy = 0
        for dts in sorted(man):
            m = man[dts]
            e, b = ticks[dts]
            if len(b) < 100 or m["aw"] <= 0:
                out.append(dict(date=dts, n_ticks=len(b)))   # NaN-row (report ที่ card join)
                continue
            eps = np.array(e, dtype=np.int64); bids = np.array(b, dtype=float)
            feats, undef = es2_features(eps, bids, m["B"], m["d0100"], m["dir"], m["aw"])
            undef_total += undef
            row = dict(date=dts)
            row.update({k: (round(v, 6) if isinstance(v, float) else v) for k, v in feats.items()})
            # slice-discipline check (ป้ายตาม ES-1 M2 — power จริง = smoke NEG-CTRL)
            if gy < GUARD_PER_YEAR:
                bids_bad = bids.copy()
                bids_bad[eps >= m["B"]] = 9e9
                f2, _ = es2_features(eps, bids_bad, m["B"], m["d0100"], m["dir"], m["aw"])
                if any(abs(feats[k] - f2[k]) > 1e-12 for k in feats if isinstance(feats[k], float)):
                    guard_fail.append(dts)
                guard_done += 1; gy += 1
            out.append(row)
    assert undef_total == 0, f"UNDEF != 0 ({undef_total}) — ต่างจากที่ freeze · STOP"
    assert not guard_fail, f"SLICE-DISCIPLINE FAIL: {guard_fail}"
    assert not soft_fail, f"G1-SOFT FAIL (<{SOFT_MIN_RATE}%): {soft_fail}"
    ln = f"[GUARDS] UNDEF==0 ✓ · slice-discipline ✓ {guard_done} (power = smoke NEG-CTRL)"
    print(ln); log_lines.append(ln)
    n_ok = sum(1 for r in out if "al_010" in r)
    ln = f"[ROWS] total={len(out)} feature-complete={n_ok} nan-rows={len(out) - n_ok}"
    print(ln); log_lines.append(ln)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in COLS})
    sha = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()
    OUT_SHA.write_text(sha)
    ln = f"[FROZEN] {OUT_CSV.name} rows={len(out)} sha256={sha[:16]}…"
    print(ln); log_lines.append(ln)
    OUT_LOG.write_text("\n".join(
        [f"# es2_tickdc buildlog | spec ES-2 v2 | δ={SCALES} SOFT_MIN={SOFT_MIN_RATE} | "
         f"rows={len(out)} | sha256={sha}"] + log_lines) + "\n", encoding="utf-8")
    print(f"[BUILDLOG] {OUT_LOG.name} ✓")


def smoke():
    """NEG-CTRL boundary-read (R3 P2): planted _TEST_B_SHIFT_MS=+60000 → dissect กิน ticks
    หลัง B จริง → features ต้องเปลี่ยน (พิสูจน์ power ไม่ใช่ tautology)"""
    global _TEST_B_SHIFT_MS
    facts_rows = [r for r in csv.DictReader(
        ln for ln in open(FACTS, encoding="utf-8") if not ln.startswith("#"))]
    bars, man, _ = manifest_year(2012, facts_rows)
    dts = sorted(man)[0]
    m = man[dts]
    e, b = [], []
    with open(DATA / "XAUUSD_ticks_eet_2012.csv") as f:
        for line in f:
            p = line.split("\t", 2)
            t = int(p[0])
            if t >= m["B"] + POST_GUARD_MS:
                break
            if t >= m["d0100"]:
                e.append(t); b.append(float(p[1]))
    eps = np.array(e, dtype=np.int64); bids = np.array(b, dtype=float)
    f_ok, _u = es2_features(eps, bids, m["B"], m["d0100"], m["dir"], m["aw"])
    try:
        _TEST_B_SHIFT_MS = 60_000
        f_bug, _u = es2_features(eps, bids, m["B"], m["d0100"], m["dir"], m["aw"])
    finally:
        _TEST_B_SHIFT_MS = 0
    fired = any(abs(f_ok[k] - f_bug[k]) > 1e-12 for k in f_ok if isinstance(f_ok[k], float))
    assert fired, "NEG-CTRL FAIL: planted B+60s แต่ features ไม่เปลี่ยน — guard ไม่มี power"
    print(f"[NEG-CTRL] ✓ planted boundary-read B+60s → tick-DC features เปลี่ยนจริง ({dts} · "
          f"n_ticks {f_ok['n_ticks']}→{f_bug['n_ticks']})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        smoke()
    else:
        run_full()
