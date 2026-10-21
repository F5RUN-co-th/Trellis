# -*- coding: utf-8 -*-
"""Card AD-4 · fixture test ของ cert_report_v2 (path ตัดสิน OPERATIVE: N5 eligibility/ordering · KS⁺ · α*_dec · rank threshold · R6 · tie-loss)
EXPERIMENT=self-test(fixture chunk สังเคราะห์ · ไม่มีข้อมูล real · ไม่ใช่ statistic · Engineer deep review 2026-09-24 ข้อเสนอที่รับ + G3/G4/G5)

ทำไมอยู่นอก CLOSURE_FILES: ทดสอบ decision path ก่อน certify v2 (~93 CPU-h) โดยไม่เปลี่ยน closure_sha → receipt regress/rg14 ยังใช้ได้
ค่าคาดหวัง = ตัวเลขที่คำนวณด้วยมือจาก order statistic ของ rank ที่สร้าง (ไม่เรียก np.quantile/helper ของ ad4_card ซ้ำ · G4)
ครอบ: eligible/INELIGIBLE (KS⁺ ขอบ = t · collapse ใน h0cal หรือ h0val · KS บน pooled ไม่ใช่ครึ่งเดียว) · ลำดับ N5 (pending · contingency · N5(0) exit 2)
      · α*_dec (cap · ต่ำกว่า cap · interpolation linear) · rank threshold · R6 strict (detection == α* → ESTIMATION) · tie-loss + scope-tag FREE-KILL
      · assert collision p_cal == p_val
ไม่ครอบ (residual): pooling-invariant assert · staging (<400 / <50) · N11 card_sha assert · h0stress stress line · readout NON-OP อื่น
ข้อจำกัด: ทดสอบตรรกะบน chunk ที่สร้างเอง ไม่ใช่ chunk จริง · assert เทียบข้อความใน output ของ cert_report_v2
รัน: PYTHONDONTWRITEBYTECODE=1 python -W error::RuntimeWarning Scripts/ad4_report_fixture.py  → exit 0 = ทุก scenario ผ่าน · exit 1 = scenario ใดล้ม
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with contextlib.redirect_stdout(io.StringIO()):
    import ad4_card as A

B1 = A.B0_CAL + 1
assert B1 == 100 and A.CERT_N == 200 and A.CERT_N_POWER == 50 and A.ALPHA_NOM == 0.05 and A.KS_T_UNITS == 23, \
    "ค่าคาดหวังด้วยมือในไฟล์นี้ผูกกับ B0=99 · N=200 · N_power=50 · α cap .05 · KS_T_UNITS=23 — ค่าเปลี่ยนต้องคำนวณใหม่"


def _header(variant, world, cell, N):
    # ฟิลด์ครบตาม pooling invariants ของ cert_report_v2 · ค่าเป็น fixture (ไม่อ้าง real)
    return {"variant": variant, "world": world, "cell": "" if cell is None else cell, "PERM_ROOT": A.PERM_ROOT, "B0": A.B0_CAL, "N": N,
            "POWER_CELLS": str(A.POWER_CELLS).replace(" ", ""), "alpha_cap": A.ALPHA_NOM, "closure_sha": "fixture", "SPEC_SHA": A.SPEC_SHA,
            "card_sha_runtime": A.SPEC_SHA, "git_head": "fixture", "dirty": 1, "n": 1, "NF": 1, "Nemb": 1, "fold_sizes": "[1]",
            "prefix_sizes": "[1]", "X_sha": "fixture", "dayix_sha": "fixture", "numpy": np.__version__, "blas": "fixture", "threads": "1",
            "field_precision": "6dp"}


def _write(root, variant, world, cell, ranks, ranks_gt=None, collapse=None):
    """ranks = rank ของ p (p = rank/(B0+1)) ต่อ draw · ranks_gt = rank ของ p_gt (default = ranks) · collapse = รหัส RG12 ต่อ draw"""
    N = len(ranks)
    ranks_gt = ranks if ranks_gt is None else ranks_gt
    collapse = [0] * N if collapse is None else collapse
    schema = A.schema_for(world); cols = schema.split(",")
    rng = np.random.default_rng(0)
    rows = []
    for k in range(N):
        r = {c: f"{0.01 * rng.normal():.6f}" for c in cols}
        r.update(k=str(k), tag=f"fx_{k}", p=f"{ranks[k] / B1:.6f}", p_gt=f"{ranks_gt[k] / B1:.6f}", p_Q4only=f"{ranks[k] / B1:.6f}",
                 n_distinct="99", n_ties="0", n_zero="0", atom_max="1", obs_zero="0", rg12_collapse=str(collapse[k]),
                 null_sd="0.010000", sd_eo="0.009000", infl_max_obs="0.100000")
        if "p_eo" in cols: r["p_eo"] = r["p"]
        rows.append(",".join(r[c] for c in cols))
    d = os.path.join(root, variant); os.makedirs(d, exist_ok=True)
    name = f"{world}_c{cell}_0_{N}.csv" if cell is not None else f"{world}_0_{N}.csv"
    with io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("# " + json.dumps(_header(variant, world, cell, N), ensure_ascii=False) + "\n# schema: " + schema + "\n" + "\n".join(rows) + "\n")


def _h0_ranks(offset):
    # 200 draws ครอบ rank 1..100 ละ 2 ครั้ง → p uniform บน grid · KS⁺ units = 0 (eligible)
    return [((k * 37 + offset) % 100) + 1 for k in range(A.CERT_N)]


def _fill(head, lo, n):
    # head + เติมที่เหลือแบบวนบน rank lo..100
    return head + [lo + (i % (101 - lo)) for i in range(n - len(head))]


def _shuffle(x, seed):
    perm = np.random.default_rng(seed).permutation(len(x))
    return [x[i] for i in perm]


def _run(root):
    """คืน (stdout, exit code) · exit None = จบปกติ"""
    A.CERT_DIR_V2 = root; A.CERT_DIR = os.path.join(root, "_no_v1")
    buf = io.StringIO(); code = None
    with contextlib.redirect_stdout(buf):
        try:
            A.cert_report_v2()
        except SystemExit as e:
            code = e.code
    return buf.getvalue(), code


def _flip_cells(root, variant, ranks_per_cell, gt_per_cell=None):
    for ci in range(len(A.POWER_CELLS)):
        _write(root, variant, "flip", ci, ranks_per_cell[ci], None if gt_per_cell is None else gt_per_cell[ci])


def main():
    fails = []
    def check(name, cond, detail=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {detail}" if detail else ""))
        if not cond: fails.append(name)
    tmp = tempfile.mkdtemp(prefix="ad4_fixture_")
    NC = len(A.POWER_CELLS)
    try:
        hc, hv = _h0_ranks(0), _h0_ranks(11)
        # ---- S1: H0 สะอาด (rank 1..100 ละ 4 ใน pooled 400) · มือ: sorted[19]=rank5 · sorted[20]=rank6 → q05 = .05+.95·.01 = .0595 → cap → α* = .05 · thr = 5
        #      flip ทุก cell: 5/50 ที่ rank 5 → detection 10% ≥ .05 → ESTIMATION
        root = os.path.join(tmp, "S1"); _write(root, "c1full", "h0cal", None, hc); _write(root, "c1full", "h0val", None, hv)
        _flip_cells(root, "c1full", [[5] * 5 + [100] * 45 for _ in range(NC)])
        out, code = _run(root)
        check("S1 exit ปกติ", code is None, f"code={code}")
        check("S1 c1full eligible (ks_units=0)", "eligibility c1full: ks_units=0 vs KS_T_UNITS·100=2300 · RG12 collapse rows=0 → eligible" in out)
        check("S1 null ของ main = c1full", "null ของ main = c1full (N5: PRIMARY eligible)" in out)
        check("S1 α*_dec = .0500 (cap)", "= 0.0595, 0.05) = 0.0500 ·" in out)
        check("S1 rank threshold = 5", "rank threshold floor(α*·(B0+1)) = 5" in out)
        check("S1 R6 = ESTIMATION (10.0% ≥ α*)", "= 10.0% ≥ α*_dec 0.0500 → **ESTIMATION" in out)
        # ---- S2: RG12 collapse 1 แถวใน h0cal ของ c1full → INELIGIBLE (N5) · c1restr ยังไม่มีผล → pending (ไม่ใช่ FAIL-loud)
        root = os.path.join(tmp, "S2"); coll = [0] * A.CERT_N; coll[5] = 3
        _write(root, "c1full", "h0cal", None, hc, collapse=coll); _write(root, "c1full", "h0val", None, hv)
        out, code = _run(root)
        check("S2 collapse (h0cal) → INELIGIBLE", "RG12 collapse rows=1 → INELIGIBLE (N5: collapse ใน H0)" in out)
        check("S2 pending (N5 order)", "null ของ main: ยังตัดสินไม่ได้" in out and code is None, f"code={code}")
        # ---- X3: collapse เฉพาะ h0val → INELIGIBLE เช่นกัน
        root = os.path.join(tmp, "X3"); coll_v = [0] * A.CERT_N; coll_v[7] = 2
        _write(root, "c1full", "h0cal", None, hc); _write(root, "c1full", "h0val", None, hv, collapse=coll_v)
        out, code = _run(root)
        check("X3 collapse (h0val) → INELIGIBLE", "RG12 collapse rows=1 → INELIGIBLE (N5: collapse ใน H0)" in out)
        # ---- S3: c1full collapse · c1restr สะอาด → null ของ main = c1restr (contingency)
        root = os.path.join(tmp, "S3")
        _write(root, "c1full", "h0cal", None, hc, collapse=coll); _write(root, "c1full", "h0val", None, hv)
        _write(root, "c1restr", "h0cal", None, hc); _write(root, "c1restr", "h0val", None, hv)
        out, code = _run(root)
        check("S3 contingency → c1restr", "null ของ main = c1restr (N5: contingency c1restr)" in out, f"code={code}")
        # ---- S4: ทุก variant ineligible → N5(0) FAIL-loud exit 2
        root = os.path.join(tmp, "S4")
        for v in A.VARIANTS:
            _write(root, v, "h0cal", None, hc, collapse=coll); _write(root, v, "h0val", None, hv)
        out, code = _run(root)
        check("S4 ทุก variant ineligible → exit 2", code == 2 and "N5(0)" in out, f"code={code}")
        # ---- X2: KS⁺ ขอบ: rank 1 ×27 + ที่เหลือวน rank 2..100 (373) · มือ: C_1 = 27 → units = 27·100 − 1·400 = 2300 = t·100 → eligible (> strict)
        p2 = _shuffle(_fill([1] * 27, 2, 400), 2)
        root = os.path.join(tmp, "X2"); _write(root, "c1full", "h0cal", None, p2[:200]); _write(root, "c1full", "h0val", None, p2[200:])
        out, code = _run(root)
        check("X2 ks_units == t·100 → eligible", "ks_units=2300 vs KS_T_UNITS·100=2300 · RG12 collapse rows=0 → eligible" in out)
        # ---- KS บน pooled ไม่ใช่ครึ่งเดียว: ครึ่งหนึ่ง rank ต่ำ (1..20) อีกครึ่ง uniform → pooled ineligible · สลับครึ่งได้ผลเดียวกัน
        low = [(k % 20) + 1 for k in range(A.CERT_N)]
        for nm, (a_, b_) in (("h0cal ต่ำ", (low, hv)), ("h0val ต่ำ", (hc, low))):
            root = os.path.join(tmp, "KS_" + nm); _write(root, "c1full", "h0cal", None, a_); _write(root, "c1full", "h0val", None, b_)
            out, code = _run(root)
            check(f"KS pooled ({nm}) → INELIGIBLE", "RG12 collapse rows=0 → INELIGIBLE" in out)
        # ---- X5: interpolation · มือ: rank ≤3 = 20 ตัว (อยู่ใน h0cal ทั้งหมด) → sorted[19]=rank3 · sorted[20]=rank4 → q05 = .03+.95·.01 = .0395 · thr = 3
        low5 = [1] * 6 + [2] * 7 + [3] * 7
        hc5 = low5 + [4 + (i % 97) for i in range(180)]; hv5 = [4 + ((i * 7) % 97) for i in range(200)]
        root = os.path.join(tmp, "X5"); _write(root, "c1full", "h0cal", None, hc5); _write(root, "c1full", "h0val", None, hv5)
        out, code = _run(root)
        check("X5 eligible", "eligibility c1full:" in out and "→ eligible" in out)
        check("X5 α*_dec = .0395 (linear)", "= 0.0395, 0.05) = 0.0395 ·" in out)
        check("X5 rank threshold = 3", "rank threshold floor(α*·(B0+1)) = 3" in out)
        # ---- X1: α* ต่ำกว่า cap + R6 strict · มือ: rank 1,2,3 ×4 + rank 4 ×10 (≤ rank4 = 22 ตัว) → sorted[19]=sorted[20]=rank4 → α* = .04 · thr = 4
        #      flip ทุก cell: 2/50 ที่ rank 4 → detection = .04 == α* → ไม่ < → ESTIMATION (tie → estimation)
        p1 = _shuffle(_fill([1] * 4 + [2] * 4 + [3] * 4 + [4] * 10, 5, 400), 1)
        root = os.path.join(tmp, "X1"); _write(root, "c1full", "h0cal", None, p1[:200]); _write(root, "c1full", "h0val", None, p1[200:])
        _flip_cells(root, "c1full", [[4] * 2 + [100] * 48 for _ in range(NC)])
        out, code = _run(root)
        check("X1 eligible", "eligibility c1full:" in out and "→ eligible" in out)
        check("X1 α*_dec = .0400 (< cap)", "= 0.0400, 0.05) = 0.0400 ·" in out)
        check("X1 detection == α* → ESTIMATION (strict)", "= 4.0% ≥ α*_dec 0.0400 → **ESTIMATION" in out)
        # ---- X4: p_cal == p_val → AssertionError (collision)
        root = os.path.join(tmp, "X4"); _write(root, "c1full", "h0cal", None, hc); _write(root, "c1full", "h0val", None, hc)
        try:
            _run(root); check("X4 p_cal == p_val → assert", False, "ไม่ raise")
        except AssertionError as e:
            check("X4 p_cal == p_val → assert", "collision" in str(e))
        # ---- S6: tie-loss · cell 0: 10 draw rank(p_gt)=5 ≤ thr=5 < rank(p)=6 (tie-loss) + 1 draw rank(p)=rank(p_gt)=5 (detect ทั้งคู่)
        #      → tie-loss 10/50 = 20% ≠ detection ใต้ p_gt 11/50 = 22% · max detection (p) = 1/50 = 2% < α* → FREE-KILL
        root = os.path.join(tmp, "S6"); _write(root, "c1full", "h0cal", None, hc); _write(root, "c1full", "h0val", None, hv)
        base = [100] * 50; gt0 = [5] * 11 + [100] * 39; p0 = [6] * 10 + [5] + [100] * 39
        _flip_cells(root, "c1full", [p0] + [base] * (NC - 1), [gt0] + [base] * (NC - 1))
        out, code = _run(root)
        check("S6 tie-loss cell 0 = 20% (det p_gt 22%)", "c0 20% (det p_gt 22%)" in out)
        check("S6 FREE-KILL (2.0% < α*) + scope-tag", "= 2.0% < α*_dec 0.0500 → **FREE-KILL (structural" in out and "max tie-loss ข้าม 7 cells = 20.0% · max detection ใต้ p_gt = 22.0%" in out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"[fixture] {'ALL PASS' if not fails else 'FAIL: ' + ', '.join(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
