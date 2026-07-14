#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tp1_tick_features.py — TRELLIS-010 · Card TP-1 tick-price extractor (สนาม SIM-SEARCH 2012-2020)
Spec v2 frozen หลัง Engineer 3 รอบ (R1 B1-B3/M1-M6 · R2 P1-P6 · R3 Issue1-6) + Claude Verify ทุกรอบ

FIREWALL (precedent c7): อ่าน day_facts เฉพาะ date/traded/entry_time/dir — ไม่แตะ P&L column ใด
BASIS: bid เท่านั้น (label/exit ของ walker เดิน bid + spread model — brain_v1_run.py:98,:208)
BOUNDARY B = wall-close ของ signal bar j = (tmin_j + 1) นาที · exclusive `<` เสมอ (R2 เห็นต่าง-3
  · glossary: feature "ณ entry" ต้อง as-of ≤ close bar j · ไม่ใช้ tmin(entry k) กัน missing-bar leak)
WINDOW primary = event-time N_TICKS ล่าสุดก่อน B · ห้ามข้าม session-open 01:00 วันเดียวกัน
  · ไม่ครบ N → NaN (drop-and-report — ห้าม impute · R1 M5) · N_TICKS=3000 freeze ex-ante จาก
  density ที่วัดจริง P&L-free (08-09h: 2012 2835-4134 · 2016 5048-6074 · 2020 4375-5450 ticks/hr
  → 3000 ticks ≈ 30-60 นาที = hour-scale ของ hypothesis)

FEATURES (6 · bid-only · R3 Issue-3 shadow map ระบุต่อท้าย):
  imb      = (upticks−downticks)/(upticks+downticks)            [intrinsically-tick · ไม่มี shadow]
  path_eff = |bid_end−bid_start| / Σ|Δbid|                      [shadow: sh_path]
  srun     = (maxrun ทิศ d − maxrun สวน d)/n_steps              [shadow: sh_srun]
  mvol     = RMS(Δbid) ต่อ tick                                 [shadow: sh_mvol]
  dur_cv   = std(Δt)/mean(Δt) ของ inter-tick duration           [intrinsically-tick · ไม่มี shadow]
  lvl_act  = สัดส่วน ticks ใน |bid−level_d| ≤ 0.25·aw           [shadow: sh_lvl (p[6]-weighted)]
SHADOWS คำนวณสูตรเดียวกันบน M1 bars ช่วง span เดียวกับ tick window (bar แรกของ window → bar j)
  + win_sec (era-density control R2 P5 → card ใช้ log) · ตัดโดย scope: spread ทุกรูป (CLAIM-0008
  DEAD-do-not-rerun) · count-rate/duration-median (deterministic จาก M1 p[6])

GATES:
  G1 HARD  = ทุก bar ใน span ที่ใช้จริงของทุก entry: bid-reconstruct O/H/L/C+count ตรง M1 เป๊ะ
             (fail-loud รายตัว · ก่อนเขียน output)
  G1 SOFT  = per-year global match-rate ≥ 99.9% + รายงาน DST-transition weeks แยก + mismatch
             ใน hour 08-19 ต้องรายงาน (R2 P3 สองชั้น — clock-verification ≠ feature-integrity)
  G3 GUARD = future-mask: corrupt ticks epoch ≥ B → feature ต้อง invariant · sample ≥50 entries
             stratified ทุกปี + edge cases (R2 P4 · R3: session-open-cap โดน a≥240 กันเกือบหมด)
Usage:  python tp1_tick_features.py smoke   (Issue-5 smoke ก่อน build เต็ม)
        python tp1_tick_features.py         (เต็ม → Research/h0/tp1_tickfeat_2012_2020.csv + .sha256)
"""
import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path(r"D:/workspace/Doc/T.me/R&D/Gloo/Data")
ROOT = Path(__file__).parent.parent
FACTS = ROOT / "Research/h0/h0_day_facts_2012_2020.csv"
OUT_CSV = ROOT / "Research/h0/tp1_tickfeat_2012_2020.csv"
OUT_SHA = ROOT / "Research/h0/tp1_tickfeat_2012_2020.sha256"

YEARS = list(range(2012, 2021))
N_TICKS = 3000                      # freeze ex-ante (density-derived · P&L-free — ดู docstring)
BAND = 0.25                         # level-proximity band × aw
POST_GUARD = 500                    # ticks หลัง B เก็บไว้ให้ G3 corrupt-test
GUARD_PER_YEAR = 6                  # ≥50 รวมทุกปี (9×6=54) + edge cases
SOFT_MIN_RATE = 99.9                # G1-SOFT threshold ต่อปี — หลุด = fail-loud ห้ามได้ output (F-1)
OUT_LOG = ROOT / "Research/h0/tp1_tickfeat_2012_2020.buildlog.txt"

# test-only hooks (negative-control ใน smoke — production ต้อง 0 เสมอ · assert ใน run_full)
# ctrl-1: เลื่อน boundary B ใน window_features · ctrl-2: ขยาย span บนของ m1_shadow (F-4)
_TEST_B_SHIFT_MS = 0
_TEST_SHADOW_EXTRA = 0
COLS = ["date", "n_avail", "win_sec", "imb", "path_eff", "srun", "mvol", "dur_cv",
        "lvl_act", "sh_path", "sh_srun", "sh_mvol", "sh_lvl", "nan_reason"]


def ep_ms(dts):
    """EET-wall 'YYYY.MM.DD HH:MM' → epoch_ms convention เดียวกับไฟล์ tick (read-as-UTC)"""
    return int(datetime.strptime(dts, "%Y.%m.%d %H:%M").replace(
        tzinfo=timezone.utc).timestamp() * 1000)


def load_m1_year(y):
    """M1 ปีเดียว → dict tmin_min→(o,h,l,c,cnt) + เรียงตามเวลา (0-idx: p[6]=count · R2 P6 pin)"""
    bars = {}
    with open(DATA / f"XAUUSD_M1_{y}.csv", newline="") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            tm = ep_ms(p[0] + " " + p[1][:5]) // 60000
            bars[tm] = (float(p[2]), float(p[3]), float(p[4]), float(p[5]), int(p[6]))
    return bars


def manifest_year(y, facts_rows):
    """entry manifest ต่อปี (P&L-free): date → (B_ms, day0100_ms, dir, level_d, aw, tmin_j)
    ทำซ้ำ logic j = session-seq(entry)−1 + a≥240 ของ build_rows (direction_at_real_exit.py:76-82)
    บน M1 ของวันนั้นเอง — ไม่ import load_ctx เพื่อไม่ให้ P&L เข้า memory (FIREWALL)"""
    bars = load_m1_year(y)
    tms = sorted(bars)
    byday = {}
    for tm in tms:
        byday.setdefault(tm // 1440, []).append(tm)
    man, skip = {}, []
    for r in facts_rows:
        if r["date"][:4] != str(y) or r["traded"] != "1":
            continue
        d0 = ep_ms(r["date"].replace("-", ".") + " 00:00") // 60000 // 1440
        day_tms = byday.get(d0, [])
        sess = [tm for tm in day_tms if 1 <= (tm // 60) % 24 < 22]
        asian = [tm for tm in day_tms if 1 <= (tm // 60) % 24 < 8]
        ek = ep_ms(r["date"].replace("-", ".") + " " + r["entry_time"][:5]) // 60000
        if ek not in bars or not asian:
            skip.append((r["date"], "no-entry-bar/no-asian")); continue
        try:
            pk = sess.index(ek)
        except ValueError:
            skip.append((r["date"], "entry-not-in-session")); continue
        a = pk - 1
        if a < 240:
            skip.append((r["date"], "a<240")); continue
        tmin_j = sess[a]
        ash = max(bars[tm][1] for tm in asian)
        asl = min(bars[tm][2] for tm in asian)
        dr = int(r["dir"])
        man[r["date"]] = dict(B=(tmin_j + 1) * 60000, d0100=ep_ms(
            r["date"].replace("-", ".") + " 01:00"), dir=dr,
            level=(ash if dr == 1 else asl), aw=ash - asl, tmin_j=tmin_j)
    return bars, man, skip


def feat_from_window(bids, eps):
    """core features จาก tick window (bids/eps = arrays เรียงเวลา · ทั้งคู่ epoch < B แล้ว)"""
    db = np.diff(bids)
    nz = db[db != 0]
    ups, dns = int((nz > 0).sum()), int((nz < 0).sum())
    imb = (ups - dns) / (ups + dns) if ups + dns else 0.0
    ssum = float(np.abs(db).sum())
    path_eff = abs(float(bids[-1] - bids[0])) / ssum if ssum > 0 else 0.0
    sgn = np.sign(db)
    runs = {1: 0, -1: 0}
    cur, cl = 0, 0
    for s in sgn:
        if s != 0 and s == cl:
            cur += 1
        elif s != 0:
            cl, cur = s, 1
        if s != 0:
            runs[int(cl)] = max(runs[int(cl)], cur)
    mvol = float(np.sqrt(np.mean(db ** 2)))
    dt = np.diff(eps).astype(float)
    dur_cv = float(dt.std() / dt.mean()) if len(dt) and dt.mean() > 0 else 0.0
    return imb, path_eff, runs, mvol, dur_cv


def window_features(ticks, B, d0100, dr, level, aw):
    """slice window (ตาม boundary rule) แล้วคำนวณ — G3 corrupt หลัง B ต้องไม่เปลี่ยนผลฟังก์ชันนี้
    ticks = list[(epoch_ms, bid)] ของวันนั้น (อาจมีเลย B ไป POST_GUARD ตัว)"""
    eps = np.array([t for t, _ in ticks], dtype=np.int64)
    bids = np.array([b for _, b in ticks], dtype=float)
    m = (eps < B + _TEST_B_SHIFT_MS) & (eps >= d0100)   # strict `<` (R2 เห็นต่าง-3 / R3 ยืนยัน · hook=0 ใน production)
    eps, bids = eps[m], bids[m]
    n_avail = len(eps)
    if n_avail < N_TICKS:
        return dict(n_avail=n_avail, nan_reason=f"n_avail<{N_TICKS}")
    eps, bids = eps[-N_TICKS:], bids[-N_TICKS:]
    imb, path_eff, runs, mvol, dur_cv = feat_from_window(bids, eps)
    srun = (runs[dr] - runs[-dr]) / (N_TICKS - 1)
    lvl_act = float(np.mean(np.abs(bids - level) <= BAND * aw))
    return dict(n_avail=n_avail, win_sec=(B - int(eps[0])) / 1000.0, imb=imb,
                path_eff=path_eff, srun=srun, mvol=mvol, dur_cv=dur_cv,
                lvl_act=lvl_act, first_ep=int(eps[0]), nan_reason="")


def m1_shadow(bars, first_ep, tmin_j, dr, level, aw):
    """shadow map (R3 Issue-3): เฉพาะ path/srun/mvol/lvl — สูตรเดียวกันบน M1 span ของ window จริง
    (imb/dur_cv = intrinsically-tick · ไม่มี shadow · baseline คุมไม่ได้ = ประกาศตรงๆ)"""
    span = [tm for tm in range((first_ep // 60000), tmin_j + 1 + _TEST_SHADOW_EXTRA) if tm in bars]
    if len(span) < 3:
        return dict(sh_path=0.0, sh_srun=0.0, sh_mvol=0.0, sh_lvl=0.0)
    o0 = bars[span[0]][0]
    cs = np.array([bars[tm][3] for tm in span])
    cnt = np.array([bars[tm][4] for tm in span], dtype=float)
    hi = np.array([bars[tm][1] for tm in span]); lo = np.array([bars[tm][2] for tm in span])
    dc = np.diff(cs)
    ssum = float(np.abs(dc).sum())
    sh_path = abs(float(cs[-1] - o0)) / ssum if ssum > 0 else 0.0
    sgn = np.sign(dc); runs = {1: 0, -1: 0}; cur, cl = 0, 0
    for s in sgn:
        if s != 0 and s == cl:
            cur += 1
        elif s != 0:
            cl, cur = s, 1
        if s != 0:
            runs[int(cl)] = max(runs[int(cl)], cur)
    sh_srun = (runs[dr] - runs[-dr]) / max(1, len(dc))
    sh_mvol = float(np.sqrt(np.mean(dc ** 2)))
    inter = (lo <= level + BAND * aw) & (hi >= level - BAND * aw)
    sh_lvl = float(cnt[inter].sum() / cnt.sum()) if cnt.sum() > 0 else 0.0
    return dict(sh_path=sh_path, sh_srun=sh_srun, sh_mvol=sh_mvol, sh_lvl=sh_lvl)


def stream_year(y, man, bars, recon):
    """single pass ต่อปี: เก็บ ticks ต่อ entry-day [d0100, B+guard) + minute-aggregate ทั้งปี (SOFT)
    recon = dict สะสมสถิติ reconstruction"""
    want = {}
    for dts, m in man.items():
        d0 = m["d0100"] - 3_600_000                    # เผื่อ 00:00-01:00 (วันหลัง DST-fallback)
        want[dts] = (d0, m["B"] + 90_000_000)          # เก็บเกิน B มากพอสำหรับ POST_GUARD
    order = sorted(want.items(), key=lambda kv: kv[1][0])
    day_ticks = {dts: [] for dts in want}
    oi, active = 0, []
    cur_min, agg = None, None

    def flush_minute():
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
            if ok:
                recon["ok"] += 1
            else:
                recon["bad"] += 1
                hr = (cur_min // 60) % 24
                if 8 <= hr < 20:
                    recon["bad_0819"] += 1
                if len(recon["bad_list"]) < 10:
                    recon["bad_list"].append((cur_min, agg, mb))
                recon["bad_min"].add(cur_min)
        cur_min, agg = None, None

    with open(DATA / f"XAUUSD_ticks_eet_{y}.csv") as f:
        for line in f:
            p = line.split("\t")
            t = int(p[0]); bid = float(p[1])
            mm = t // 60000
            if mm != cur_min:
                flush_minute()
                cur_min, agg = mm, [bid, bid, bid, bid, 1]
            else:
                agg[1] = max(agg[1], bid); agg[2] = min(agg[2], bid)
                agg[3] = bid; agg[4] += 1
            while oi < len(order) and t >= order[oi][1][0]:
                active.append(order[oi][0]); oi += 1
            if active:
                spent = []
                for dts in active:
                    a, b = want[dts]
                    if t >= b:
                        spent.append(dts)
                    elif t >= a:
                        day_ticks[dts].append((t, bid))
                for dts in spent:
                    active.remove(dts)
    flush_minute()
    recon["m1_total"] += len(bars)                     # M1-bar-ไร้-tick ใน span = G1-HARD จับ (no-ticks-for-bar)
    return day_ticks


def run_full():
    facts_rows = [r for r in csv.DictReader(
        ln for ln in open(FACTS, encoding="utf-8") if not ln.startswith("#"))]
    for r in facts_rows:                               # FIREWALL: จำกัด key ที่ใช้
        for k in list(r):
            if k not in ("date", "traded", "entry_time", "dir"):
                del r[k]
    assert _TEST_B_SHIFT_MS == 0 and _TEST_SHADOW_EXTRA == 0, \
        "test hooks ต้องเป็น 0 ใน production run (negative-control ใช้ได้เฉพาะ smoke)"
    out, guard_fail, hard_fail, soft_fail = [], [], [], []
    guard_done = 0
    all_skip, log_lines = [], []
    for y in YEARS:
        bars, man, skip = manifest_year(y, facts_rows)
        all_skip += skip
        recon = dict(n=0, ok=0, bad=0, bad_0819=0, tick_only=0, m1_total=0,
                     bad_list=[], bad_min=set())
        day_ticks = stream_year(y, man, bars, recon)
        rate = recon["ok"] / recon["n"] * 100 if recon["n"] else 0.0
        soft = "PASS" if rate >= SOFT_MIN_RATE else "FAIL"
        if rate < SOFT_MIN_RATE:
            soft_fail.append((y, round(rate, 4)))       # F-1: accumulate ทุกปี · assert รวมท้าย loop
        ln = (f"[G1-SOFT {y}] bars-checked={recon['n']} match={rate:.4f}% ({soft}) "
              f"bad={recon['bad']} bad-hour08-19={recon['bad_0819']} tick-only-min={recon['tick_only']}")
        print(ln); log_lines.append(ln)
        for bl in recon["bad_list"][:3]:
            bln = f"    BAD tmin={bl[0]}: tick={bl[1]} m1={bl[2]}"
            print(bln); log_lines.append(bln)
        gy = 0
        for dts in sorted(man):
            m = man[dts]
            ticks = day_ticks[dts]
            r = window_features(ticks, m["B"], m["d0100"], m["dir"], m["level"], m["aw"])
            row = dict(date=dts, n_avail=r["n_avail"], nan_reason=r["nan_reason"])
            if not r["nan_reason"]:
                # G1 HARD: ทุก bar ใน span ที่ใช้จริง ต้อง reconstruct เป๊ะ
                # (สร้างจาก ticks ทั้งวัน — window เริ่มกลางนาทีได้ แต่ bar ต้องเทียบแบบเต็มนาที
                #  · collection เริ่มก่อน 01:00 หนึ่งชม. จึงครบเต็มนาทีเสมอ — bugfix รอบแรก:
                #  เคย slice ด้วย first_ep ทำ partial-first-minute mismatch 1,467 = 1/entry)
                span0 = r["first_ep"] // 60000
                per = {}
                for t, b in ticks:
                    per.setdefault(t // 60000, []).append(b)
                for tm in range(span0, m["tmin_j"] + 1):
                    mb = bars.get(tm); tk = per.get(tm)
                    if mb is None or tk is None:
                        if mb is not None and mb[4] > 0:
                            hard_fail.append((dts, tm, "no-ticks-for-bar"))
                        continue
                    if not (round(tk[0], 3) == round(mb[0], 3) and round(max(tk), 3) == round(mb[1], 3)
                            and round(min(tk), 3) == round(mb[2], 3) and round(tk[-1], 3) == round(mb[3], 3)
                            and len(tk) == mb[4]):
                        hard_fail.append((dts, tm, "mismatch"))
                row.update({k: round(r[k], 6) for k in
                            ("win_sec", "imb", "path_eff", "srun", "mvol", "dur_cv", "lvl_act")})
                sh = m1_shadow(bars, r["first_ep"], m["tmin_j"], m["dir"], m["level"], m["aw"])
                row.update({k: round(v, 6) for k, v in sh.items()})
                # G3 future-mask guard: corrupt ticks epoch ≥ B → invariance (สุ่มต่อปี + วัน NaN-ขอบ)
                if gy < GUARD_PER_YEAR:
                    tk2 = [(t, (b * 0 + 9e9) if t >= m["B"] else b) for t, b in ticks]
                    r2 = window_features(tk2, m["B"], m["d0100"], m["dir"], m["level"], m["aw"])
                    same = all(abs(r[k] - r2[k]) < 1e-12 for k in
                               ("imb", "path_eff", "srun", "mvol", "dur_cv", "lvl_act"))
                    if not same:
                        guard_fail.append(dts)
                    # shadow regression-sentinel (F-2/F-3): corrupt M1 bars > j บน COPY เท่านั้น
                    # (ห้าม mutate bars ที่ entry อื่น/G1-HARD ใช้ร่วม) — พลังพิสูจน์โดย ctrl-2 ใน smoke
                    bars_bad = dict(bars)
                    for tm in range(m["tmin_j"] + 1, m["tmin_j"] + 61):
                        if tm in bars_bad:
                            bars_bad[tm] = (9e9, 9e9, 9e9, 9e9, 999)
                    sh2 = m1_shadow(bars_bad, r["first_ep"], m["tmin_j"], m["dir"],
                                    m["level"], m["aw"])
                    if any(abs(sh[k] - sh2[k]) > 1e-12 for k in sh):
                        guard_fail.append(dts + "(shadow)")
                    guard_done += 1; gy += 1
            out.append(row)
    assert not hard_fail, f"G1-HARD FAIL {len(hard_fail)} bars: {hard_fail[:5]}"
    assert not guard_fail, f"G3 FUTURE-MASK/SHADOW FAIL: {guard_fail}"
    assert not soft_fail, f"G1-SOFT FAIL (rate<{SOFT_MIN_RATE}%) — ห้าม freeze output: {soft_fail}"
    ln = f"[G3] future-mask + shadow-sentinel invariance ✓ {guard_done} entries (stratified ทุกปี)"
    print(ln); log_lines.append(ln)
    nan_y = {}
    for r in out:
        if r["nan_reason"]:
            nan_y[r["date"][:4]] = nan_y.get(r["date"][:4], 0) + 1
    ln = (f"[M5] rows={len(out)} NaN-dropped-per-year={nan_y} skip-manifest={len(all_skip)} "
          f"(a<240/no-bar: {[s for s in all_skip[:4]]})")
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
    # buildlog artifact (F-1 provenance): self-describing · เขียนหลังทุก assert ผ่าน + คู่ SHA
    OUT_LOG.write_text("\n".join(
        [f"# tp1_tickfeat buildlog | spec=TP-1 v2 | N_TICKS={N_TICKS} BAND={BAND} "
         f"SOFT_MIN_RATE={SOFT_MIN_RATE} | rows={len(out)} | sha256={sha}"] + log_lines) + "\n",
        encoding="utf-8")
    print(f"[BUILDLOG] {OUT_LOG.name} ✓")


def run_smoke():
    """Issue-5: reconstruction smoke — 5 วันกระจาย รวม spring-forward + fall-back week · fail-loud"""
    days = [(2012, "2012.01.10"), (2015, "2015.03.30"), (2013, "2013.10.28"),
            (2019, "2019.01.08"), (2020, "2020.01.06")]
    for y, dts in days:
        bars = load_m1_year(y)
        a = ep_ms(dts + " 00:00"); b = a + 86_400_000
        per = {}
        with open(DATA / f"XAUUSD_ticks_eet_{y}.csv") as f:
            for line in f:
                p = line.split("\t")
                t = int(p[0])
                if t >= b:
                    break
                if t >= a:
                    per.setdefault(t // 60000, []).append(float(p[1]))
        ok = bad = 0
        for tm, tk in sorted(per.items()):
            mb = bars.get(tm)
            if mb is None:
                bad += 1; continue
            if (round(tk[0], 3) == round(mb[0], 3) and round(max(tk), 3) == round(mb[1], 3)
                    and round(min(tk), 3) == round(mb[2], 3) and round(tk[-1], 3) == round(mb[3], 3)
                    and len(tk) == mb[4]):
                ok += 1
            else:
                bad += 1
        tag = "✓" if bad == 0 and ok > 0 else "✗ FAIL"
        print(f"[SMOKE {dts}] bars={ok + bad} exact={ok} bad={bad} {tag}")
        assert bad == 0 and ok > 0, f"smoke FAIL {dts}"
    print("[SMOKE] PASS ทั้ง 5 วัน (รวม DST-shoulder สองฝั่ง) — clock/basis ยืนยันก่อน build เต็ม")
    run_negctrl()


def run_negctrl():
    """F-4 negative-control: planted bug แบบ deterministic ต้องทำให้ guard ยิงจริง —
    พิสูจน์ว่า G3/shadow-sentinel มี discriminating power ไม่ใช่ tautology (Verify≠self-grading)
    ctrl-1: _TEST_B_SHIFT_MS=+60000 (window กิน ticks หลัง B 1 นาที) → corrupt-test ต้อง DIFFER
    ctrl-2: _TEST_SHADOW_EXTRA=+60 (shadow span เลย bar j) → bars-corrupt ต้อง DIFFER"""
    global _TEST_B_SHIFT_MS, _TEST_SHADOW_EXTRA
    facts_rows = [r for r in csv.DictReader(
        ln for ln in open(FACTS, encoding="utf-8") if not ln.startswith("#"))]
    bars, man, _ = manifest_year(2012, facts_rows)
    dts = sorted(man)[0]
    m = man[dts]
    a, b = m["d0100"] - 3_600_000, m["B"] + 5_400_000
    ticks = []
    with open(DATA / "XAUUSD_ticks_eet_2012.csv") as f:
        for line in f:
            p = line.split("\t")
            t = int(p[0])
            if t >= b:
                break
            if t >= a:
                ticks.append((t, float(p[1])))
    try:
        _TEST_B_SHIFT_MS = 60000
        r_clean = window_features(ticks, m["B"], m["d0100"], m["dir"], m["level"], m["aw"])
        tk2 = [(t, 9e9 if t >= m["B"] else v) for t, v in ticks]
        r_bad = window_features(tk2, m["B"], m["d0100"], m["dir"], m["level"], m["aw"])
        fired1 = any(abs(r_clean[k] - r_bad[k]) > 1e-12 for k in
                     ("imb", "path_eff", "srun", "mvol", "dur_cv", "lvl_act"))
    finally:
        _TEST_B_SHIFT_MS = 0
    assert fired1, f"NEG-CTRL-1 FAIL: planted boundary-bug (+60s) แต่ guard ไม่ยิง ({dts})"
    print(f"[NEG-CTRL-1] ✓ planted B+60s → future-mask guard ยิงจริง ({dts})")
    try:
        _TEST_SHADOW_EXTRA = 60
        r0 = window_features(ticks, m["B"], m["d0100"], m["dir"], m["level"], m["aw"])
        sh_clean = m1_shadow(bars, r0["first_ep"], m["tmin_j"], m["dir"], m["level"], m["aw"])
        bars_bad = dict(bars)
        for tm in range(m["tmin_j"] + 1, m["tmin_j"] + 61):
            if tm in bars_bad:
                bars_bad[tm] = (9e9, 9e9, 9e9, 9e9, 999)
        sh_bad = m1_shadow(bars_bad, r0["first_ep"], m["tmin_j"], m["dir"], m["level"], m["aw"])
        fired2 = any(abs(sh_clean[k] - sh_bad[k]) > 1e-12 for k in sh_clean)
    finally:
        _TEST_SHADOW_EXTRA = 0
    assert fired2, f"NEG-CTRL-2 FAIL: planted shadow-span-bug (+60 bars) แต่ sentinel ไม่ยิง ({dts})"
    print(f"[NEG-CTRL-2] ✓ planted span+60 → shadow-sentinel ยิงจริง ({dts})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        run_smoke()
    else:
        run_full()
