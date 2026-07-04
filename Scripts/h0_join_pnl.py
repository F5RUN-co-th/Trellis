#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
h0_join_pnl.py — TRELLIS-010 Stage H0 deliverable 1b: แนบ per-day P&L (สนาม SEARCH)
เข้า features ที่ freeze แล้ว → h0_day_facts_2012_2020.csv

ลำดับ firewall (Engineer HIGH-6): h0_features.py สร้าง features (ไม่มี P&L) + SHA256 ก่อน
→ ไฟล์นี้ verify SHA256 ว่า features ไม่ถูกแตะ แล้วจึงแนบ P&L ในไฟล์ output แยก

สนามวัด: SIM SEARCH field = run_detailed(**DEPLOY_CFG, deposit=None, ea_catchup=True)
  บน 2011(warmup)+2012–2020 — uncapped flat 0.01 (MED-1: cap = deployment layer ·
  ผลดีบนสนามนี้ห้ามเรียก edge จนผ่าน capped+real-tick tester confirm)

Integrity (Engineer mandatory):
- CRIT-1: ส่ง **DEPLOY_CFG เท่านั้น + runtime assert D=1.0/SLOPE=0.0005 (กันกับดัก
  default D=0.75/SLOPE=0.001 ของ run_detailed ที่จะ label ผิดทั้งชุดแบบเงียบ)
- CRIT-2: baseline ในหน้าต่าง search = 5 ปีแพ้ (2012/14/17/18/19) −135.2 — 2022/2023
  อยู่นอกหน้าต่าง = confirm-only ห้ามใช้เกณฑ์ %ดีขึ้นจากฐาน −185.4 กับ search window
- MED-7: reconciliation ปิดเป๊ะ — Σ(P&L ทุกวันใน output) == sim total · วัน flag ไม่ drop
  P&L (เก็บพร้อม status) · ไม้ถือข้ามวัน (คร่อม hole/weekend-anomaly) flag cross_day=1
- R-match: R ของทุกไม้ต้องเท่า asian_width ของ features เป๊ะ (สอง pipeline อ่าน data
  เดียวกัน — ไม่เท่า = เครื่องมือพัง abort)

Usage: python h0_join_pnl.py   → Research/h0/h0_day_facts_2012_2020.csv
"""
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dual_asian_sim import load_full, year_start_index
from stage0_join import DEPLOY_CFG, run_detailed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

YEARS = list(range(2011, 2021))
OUT_DIR = Path(__file__).parent.parent / "Research" / "h0"
FEAT_CSV = OUT_DIR / "h0_features_2012_2020.csv"
FEAT_SHA = OUT_DIR / "h0_features_2012_2020.sha256"
OUT_CSV = OUT_DIR / "h0_day_facts_2012_2020.csv"

PNL_COLS = ["traded", "pnl", "reason", "dir", "R", "exit_date", "cross_day"]


def main():
    # CRIT-1: config assertion — fail loud ถ้า canonical/DEPLOY_CFG ถูกแก้วันหน้า
    assert DEPLOY_CFG["D"] == 1.0 and DEPLOY_CFG["SLOPE"] == 0.0005, \
        f"DEPLOY_CFG ไม่ใช่ WF config ที่ deploy: {DEPLOY_CFG}"
    assert DEPLOY_CFG["CAPR"] == 1.0 and DEPLOY_CFG["EMA_P"] == 2880

    # firewall check: features ต้องถูก freeze ก่อนและไม่ถูกแตะ
    sha_now = hashlib.sha256(FEAT_CSV.read_bytes()).hexdigest()
    sha_ref = FEAT_SHA.read_text(encoding="utf-8").split()[0]
    assert sha_now == sha_ref, "features CSV ถูกแก้หลัง freeze — firewall broken, abort"
    print(f"firewall OK: features SHA256 = {sha_now[:16]}…")

    # สนาม search: uncapped + ea_catchup (baseline H0)
    m1 = load_full(YEARS)
    trades, skips = run_detailed(m1, year_start_index(m1, 2012), **DEPLOY_CFG,
                                 deposit=None, ea_catchup=True)
    assert skips == [], "uncapped run ต้องไม่มี skip"
    total = float(sum(x[5] for x in trades))
    print(f"sim search field: n={len(trades)} total={total:+.1f} "
          f"(config={DEPLOY_CFG} ea_catchup=True uncapped)")

    # per entry-date (unique โดย design: traded-set 1 เทรด/วัน)
    by_date = {}
    for et, xt, d, ent, ex, pnl, reason, R in trades:
        k = str(et)[:10]
        assert k not in by_date, f"entry date ซ้ำ {k} — ผิด design 1 เทรด/วัน"
        by_date[k] = dict(pnl=float(pnl), reason=reason, dir=int(d), R=float(R),
                          exit_date=str(xt)[:10],
                          cross_day=1 if str(xt)[:10] != k else 0)

    # อ่าน features (ข้าม header comment บรรทัดแรก)
    with open(FEAT_CSV, encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    rdr = csv.DictReader(lines)
    feat_rows = list(rdr)
    feat_cols = rdr.fieldnames
    feat_dates = {r["date"] for r in feat_rows}

    # ทุกไม้ต้องมี row ใน features — ไม่มี = data/pipeline ไม่ตรงกัน abort
    orphan = [k for k in by_date if k not in feat_dates]
    assert not orphan, f"trade ไม่มี features row: {orphan}"

    # join + R-match + reconciliation
    joined_sum = 0.0
    n_traded = 0
    rmax = 0.0
    out_rows = []
    for r in feat_rows:
        tr = by_date.get(r["date"])
        if tr:
            aw = float(r["asian_width"]) if r["asian_width"] else np.nan
            dr = abs(tr["R"] - aw)
            rmax = max(rmax, dr)
            assert dr < 1e-6, f"R mismatch {r['date']}: trade R={tr['R']} vs asian_width={aw}"
            row = dict(r, traded=1, pnl=f"{tr['pnl']:.6g}", reason=tr["reason"],
                       dir=tr["dir"], R=f"{tr['R']:.6g}", exit_date=tr["exit_date"],
                       cross_day=tr["cross_day"])
            joined_sum += tr["pnl"]
            n_traded += 1
        else:
            row = dict(r, traded=0, pnl="", reason="", dir="", R="", exit_date="",
                       cross_day="")
        out_rows.append(row)
    assert n_traded == len(by_date) == len(trades)
    assert abs(joined_sum - total) < 1e-6, \
        f"reconciliation ไม่ปิด: joined {joined_sum:+.2f} vs sim {total:+.2f}"
    print(f"reconciliation OK: joined Σ={joined_sum:+.1f} == sim total ทุกไม้เข้าบัญชี · "
          f"R-match max|Δ|={rmax:.2e}")

    # ---- สรุป (ตัวเลขจาก script — LLM ห้ามพิมพ์เอง) ----
    def agg(rows_subset, label):
        p = [float(r["pnl"]) for r in rows_subset if r["traded"] == 1 and r["pnl"] != ""]
        print(f"  {label:<28} days={len(rows_subset):>5} traded={len(p):>5} "
              f"pnl={sum(p):+9.1f}")

    print("\n== per status (P&L ของวัน flag ไม่หาย — MED-7) ==")
    for st in ("ok", "short", "hole"):
        agg([r for r in out_rows if r["status"] == st], st)
    cross = [r for r in out_rows if r.get("cross_day") == 1]
    print(f"  cross_day holds (artifact flag)  n={len(cross)} "
          f"pnl={sum(float(r['pnl']) for r in cross):+.1f}")

    print("\n== per year (สนาม SEARCH: sim+catchup uncapped WF) ==")
    yrs = {}
    for r in out_rows:
        if r["traded"] == 1:
            yrs.setdefault(r["date"][:4], []).append(float(r["pnl"]))
    losers = {}
    for y in sorted(yrs):
        s = sum(yrs[y])
        if s < 0:
            losers[y] = s
        print(f"  {y}: {s:+8.1f}  (n={len(yrs[y])})")
    print(f"\nCRIT-2 baseline หน้าต่าง search: ปีแพ้ {sorted(losers)} "
          f"รวม {sum(losers.values()):+.1f} — 2022/2023 อยู่นอก window = confirm-only")

    # ---- write ----
    all_cols = list(feat_cols) + PNL_COLS
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        f.write(f"# h0_day_facts v1 | field=SIM-SEARCH uncapped flat0.01 ea_catchup "
                f"cfg={DEPLOY_CFG} | features_sha256={sha_now} | "
                f"MED-1: ห้ามเรียก edge จากสนามนี้จนผ่าน capped+real-tick confirm\n")
        w = csv.DictWriter(f, fieldnames=all_cols)
        w.writeheader()
        for r in out_rows:
            w.writerow(r)
    print(f"\nwrote {OUT_CSV}  rows={len(out_rows)}")


if __name__ == "__main__":
    main()
