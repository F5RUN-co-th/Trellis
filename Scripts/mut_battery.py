# -*- coding: utf-8 -*-
"""mutation battery v10 (รอบ 23: +(K) ลบ :149/:148/ซ่อน dir · +--require-pin ×2 · counter 23) (รอบ 22: mirror +ad4_cert_out · (K) token drift · (J) dry-run pin block ถูก/ผิด · pointer ข้อความจริง STATUS) (รอบ 21 E9: +anchor-deletion ×3 → COUNTS FAIL · copy .json sidecar · counter 21) (รอบ 19 R3: mirror tree ใน tempdir · --work <dir> · try/finally ลบ · main guard — ไม่เขียน/ไม่แก้ไฟล์ใน repo) · --root <repo> · exit 1 ถ้า MISSED
classes: cost 6 × site · parity · ~~-wrap · draws drift · contrast/q/Q2-Q4/φ/gap text · claim-set/count · retired term · STATUS counter/pointer · (H) 5 · (I) 9 · (H′) 2 · N10 2
self-test(doc-integrity tooling · battery ของ card_scan.py) — synthetic/doc only · no data · no P&L"""
import io, re, sys, subprocess, os, shutil, argparse, tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"D:/workspace/Doc/T.me/R&D/Trellis/")
    ap.add_argument("--work", default=None, help="mirror work dir (default = tempfile.mkdtemp · ลบเมื่อจบ)")
    a_ = ap.parse_args()
    R = a_.root if a_.root.endswith("/") else a_.root + "/"
    HERE = os.path.dirname(os.path.abspath(__file__)); SCAN = os.path.join(HERE, "card_scan.py")
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    own_tmp = a_.work is None
    M = a_.work or tempfile.mkdtemp(prefix="mut_battery_")
    try:
        return battery(R, SCAN, M)
    finally:
        if own_tmp: shutil.rmtree(M, ignore_errors=True)


def battery(R, SCAN, M):
    # build mirror
    for d in ("Plan", "Scripts", ".claude/status"): os.makedirs(os.path.join(M, d), exist_ok=True)
    for f in ("Plan/TRELLIS-010_card_AD4_fine_cadence.md", "Plan/TRELLIS-010_LEDGER.md", "Plan/TRELLIS-010_brain_research_workflow.md", ".claude/status/STATUS.md"):
        shutil.copy(R + f, os.path.join(M, f))
    for f in os.listdir(R + "Scripts"):
        if f.endswith(".py") or f.endswith(".json"): shutil.copy(R + "Scripts/" + f, os.path.join(M, "Scripts", f))
    os.makedirs(os.path.join(M, "Scripts", "ad4_cert_out"), exist_ok=True)
    for f in os.listdir(R + "Scripts/ad4_cert_out"):
        if f.endswith(".csv"): shutil.copy(R + "Scripts/ad4_cert_out/" + f, os.path.join(M, "Scripts", "ad4_cert_out", f))
    CARD = os.path.join(M, "Plan/TRELLIS-010_card_AD4_fine_cadence.md"); STATUS = os.path.join(M, ".claude/status/STATUS.md")
    s = io.open(CARD, encoding="utf-8").read(); L = s.split("\n"); st0 = io.open(STATUS, encoding="utf-8").read()
    cl = next(i for i, l in enumerate(L, 1) if l.startswith("## Changelog"))
    results = []

    def run(text, expect=(1, 2), flags=()):
        io.open(CARD, "w", encoding="utf-8", newline="\n").write(text)
        p = subprocess.run([sys.executable, SCAN, CARD, *flags], capture_output=True, text=True, encoding="utf-8", errors="replace")
        io.open(CARD, "w", encoding="utf-8", newline="\n").write(s)
        return p.returncode in expect, p.returncode, p.stdout

    def mut(name, text, expect=(1, 2), need=None):
        assert text != s, f"mutant ไม่เปลี่ยนข้อความ (anchor stale): {name}"
        ok, rc, out = run(text, expect)
        if ok and need and need not in out: ok = False   # ต้องถูกจับด้วย check ที่ตั้งใจ ไม่ใช่ตัวอื่น
        results.append((name, ok, rc))

    def mut_script(name, text, expect=(1, 2), need=None, flags=()):
        p = os.path.join(M, "Scripts", "ad4_card.py"); orig = io.open(p, encoding="utf-8").read()
        io.open(p, "w", encoding="utf-8", newline="\n").write(text)
        try: ok, rc, out = run(s, expect, flags)
        finally: io.open(p, "w", encoding="utf-8", newline="\n").write(orig)
        if ok and need and need not in out: ok = False
        results.append((name, ok, rc))

    def mut_status(name, a, b):
        assert st0.count(a) >= 1, a
        io.open(STATUS, "w", encoding="utf-8", newline="\n").write(st0.replace(a, b))
        try: ok, rc, out = run(s); results.append((name, ok, rc))
        finally: io.open(STATUS, "w", encoding="utf-8", newline="\n").write(st0)

    ok, rc, out = run(s, expect=(0,)); results.append(("baseline PASS", ok, rc))
    sites = []
    for i, l in enumerate(L[:cl-1], 1):
        for m in re.finditer(r"(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?) CPU-h\[([^\]]+)\]", l):
            clean = re.sub(r"`[^`]*`", lambda mm: " " * len(mm.group(0)), l)
            if clean[:m.start()].count("~~") % 2 == 1: continue
            if m.group(2) in ("RETIRED", "EXT"): continue
            sites.append((i, m.start(), m.end(), m.group(1), m.group(2)))
    TAGS = ["A1×1.33", "full×1.33", "A1×0.33", "full×0.33", "full×1.0", "fold-share", "RG14 W=50", "RG14 Δ"]
    for (ln, a, b, v, tag) in sites:
        l = L[ln-1]; other = next(t for t in TAGS if t != tag)
        for kind, rep in (("in-set", f"{'34.8' if v=='93.3' else '93.3'} CPU-h[{tag}]"), ("out-set", f"80.5 CPU-h[{tag}]"), ("strip-tag", f"{v} CPU-h"),
                          ("tag-swap", f"{v} CPU-h[{other}]"), ("range-upper", f"{v}-99.9 CPU-h[{tag}]"), ("RETIRED-on-live", f"{v} CPU-h[RETIRED]")):
            ml = L[:]; ml[ln-1] = l[:a] + rep + l[b:]; mut(f"L{ln} {v}[{tag}] {kind}", "\n".join(ml), need="COST FAIL")
    ln, a, b, v, tag = sites[0]; ml = L[:]; ml[ln-1] = L[ln-1][:a] + "~~999 CPU-h[" + tag + "]" + L[ln-1][b:]; mut("parity ~~ single", "\n".join(ml))
    mut("~~-wrap live cost 34.8", s.replace("1,150×82×1.33 ≈ **34.8 CPU-h[A1×1.33]**", "1,150×82×1.33 ≈ **~~999 CPU-h[A1×1.33]~~**", 1), need="COST FAIL")
    mut("draws 1,150→1,250", s.replace("A-1 PRIMARY 1,150×82×1.33", "A-1 PRIMARY 1,250×82×1.33", 1))
    mut("draws 3,080→3,200", s.replace("เต็ม 3,080×82×1.33", "เต็ม 3,200×82×1.33", 1))
    mut("contrast ×1.73-1.75→×1.90-1.95", s.replace("×1.73-1.75", "×1.90-1.95", 1), need="CONTRAST FAIL")
    mut("q pin 38→30", s.replace("q = [38,43,40,39,40]", "q = [30,43,40,39,40]", 1))
    mut("Q2-Q4 pin drift 117→99", s.replace("(117/131/120/119/123)", "(99/131/120/119/123)", 1))
    mut("φ pin drift .97→.60", s.replace("φ=.97 · `η ~ t(5)`", "φ=.60 · `η ~ t(5)`", 1))
    mut("gap 41-46→30-35", s.replace("gap = n_te − 3q + 1 = 41-46 แถว · φ^gap ≈ 0.25-0.29", "gap = n_te − 3q + 1 = 30-35 แถว · φ^gap ≈ 0.25-0.29", 1), need="GAP FAIL")
    mut("claim-count 7→4 in (2c)", s.replace("(7 claim · grep importers", "(4 claim · grep importers", 1), need="CLAIM-COUNT FAIL")
    mut("claim-set drop 0017 in (2c)", s.replace("dependency ของ CLAIM-0015/0016/0017/0018/0019/0020/0021 (7 claim", "dependency ของ CLAIM-0015/0016/0018/0019/0020/0021 (6 claim", 1), need="CLAIM-SET FAIL")
    mut("retired term 'by construction' in N1", s.replace("- **N1 null", "- **N1 null (by construction)", 1), need="N10 FAIL")
    mut_status("STATUS counter →8", "deep review 23 รอบ", "deep review 8 รอบ")
    mut_status("STATUS stale forward-pointer insert รอรอบ 17", "** — ค้าง: ", "** — ค้าง: รอรอบ 17 · ")
    # (H) duplicate-operative (must be caught by (H) specifically)
    mut("(J) §4 RG13(ข) ∀→∃ (retired quantifier · N10)", s.replace("∧ **∀** fold ≥2017 `w_vec` ≠ `W_EXP_LIN[i]` — ทุก fold ≥2017 base มีแถวหมุนโดย", "∧ **∃** fold ≥2017 `w_vec` ≠ `W_EXP_LIN[i]` — ทุก fold ≥2017 base มีแถวหมุนโดย", 1), need="N10 FAIL")
    mut("(H) reintroduce 'fold 2016 = DIR_EXP_LIN cache' in §4 RG10", s.replace("fold 2016 refit ≡ cache โดยโครงสร้าง —", "fold 2016 = `DIR_EXP_LIN` cache —", 1), need="DUP-OPERATIVE FAIL")
    mut("(H) annual_fn default cache in §7(3)", s.replace("rotate_payoff=True, annual_fn=refit_annual, detail=False, folds=None)` [sync (2b)", "rotate_payoff=True, annual_fn=cache_annual, detail=False, folds=None)` [sync (2b)", 1), need="DUP-OPERATIVE FAIL")
    # (H′) N7 invariant
    mut("(H′) restate assert in N7", s.replace("N7 ถือเฉพาะ **raise-class**", "N7 ถือเฉพาะ **raise-class** · RG11 `assert array_equal(where(segm)[0], seg)`", 1), need="N7 FAIL")
    # (I) derived
    mut("(I) prefix m 114→110", s.replace("m = [114,129,120,117,120]", "m = [110,129,120,117,120]", 1), need="DERIVED FAIL")
    mut("(I) 2q 76→70", s.replace("2q = [76,86,80,78,80]", "2q = [70,86,80,78,80]", 1), need="DERIVED FAIL")
    mut("(I) 610→600", s.replace("= **610 แถว**", "= **600 แถว**", 1), need="DERIVED FAIL")
    mut("(I) states 35→30", s.replace("[35,50,41,38,41]", "[30,50,41,38,41]", 1), need="DERIVED FAIL")
    mut("(I) nblk 17→15", s.replace("[17,19,18,17,18]", "[15,19,18,17,18]", 1), need="DERIVED FAIL")
    mut("(I) ∏m drift", s.replace("∏m_i = 24,776,668,800", "∏m_i = 24,776,668,000", 1), need="DERIVED FAIL")
    mut("(I) discard 65.83→65.5", s.replace("ทิ้ง **65.83%** ของ reference set", "ทิ้ง **65.50%** ของ reference set", 1), need="DERIVED FAIL")
    # v6 รอบ 18 (anchor N7 sync รอบ 19 R5)
    mut("(H′) N7 quantifier ∃ reintroduce", s.replace("RG13(ข) hard-raise (polarity + clause ที่ §4)", "RG13(ข) hard-raise (quantifier ∃ · polarity + clause ที่ §4)", 1), need="N7 FAIL")
    mut("(H) N4 cell-scope → PRIMARY (vs :74/:143 null ของ main)", s.replace("7 POWER_CELLS ของ **null ของ main**", "7 POWER_CELLS ของ **PRIMARY**", 1), need="DUP-OPERATIVE FAIL")
    mut("(H) §7 rule R6 บน PRIMARY", s.replace("rule R6 บน null ของ main (§0 N5)", "rule R6 บน PRIMARY", 1), need="DUP-OPERATIVE FAIL")
    mut("(N10) §4 header existence reintroduce", s.replace("(hard-raise / conditional-raise) — ไม่ใช่ print", "(hard / existence / conditional) — ไม่ใช่ print", 1), need="N10 FAIL")
    mut("(I) junction cond 32.7→30.7", s.replace("Q2 ≈ 32.7% (37/113 fold 2016)", "Q2 ≈ 30.7% (37/113 fold 2016)", 1), need="DERIVED FAIL")
    mut("(I) junction uncond 99.1→100.0", s.replace("→ 32.5 / 65.8 / 99.1%", "→ 32.5 / 65.8 / 100.0%", 1), need="DERIVED FAIL")
    # v8 รอบ 21 (E9): ลบ anchor → ต้องถูกจับด้วย COUNTS (sidecar) ไม่ใช่ผ่านเงียบ
    mut("(E9) delete gap pin site 1", s.replace("gap = n_te − 3q + 1 = 41-46 แถว · φ^gap ≈ 0.25-0.29", "gap (ดู scanner emit)", 1), need="COUNTS FAIL")
    mut("(E9) delete junction cond anchor", s.replace("Q2 ≈ 32.7% (37/113 fold 2016) · Q3 ≈ 66.4%", "Q2/Q3 (ดู scanner emit)", 1), need="COUNTS FAIL")
    mut("(E9) delete claim-set anchor", s.replace("dependency ของ CLAIM-0015/0016/0017/0018/0019/0020/0021 (7 claim", "dependency ของ tp1_card importers (7 claim", 1), need="COUNTS FAIL")
    mut("(E9) delete discard% anchor (CHK 0 site)", s.replace("ทิ้ง **65.83%** ของ reference set", "ทิ้ง (ดู scanner) ของ reference set", 1), need="DERIVED FAIL")
    # v9 รอบ 22
    mut_status("(F-A4) STATUS pointer รูปข้อความจริง 'Engineer review รอบ N' stale (insert)", "** — ค้าง: ", "** — ค้าง: Engineer review รอบ 17 · ")   # รอบ 23: STATUS live pointer = 'ค้าง: commit spec' ไม่มีรอบแล้ว → ทดสอบรูปประโยคจริงด้วย insert
    mut("(K) §7.1 token drift power_0 LF", s.replace("power_0 `52a4ceeb…114c23`", "power_0 `52a4ceeb…114c24`", 1), need="RECORD-SHA FAIL")
    mut("(K) ลบ token power_1 CRLF (ไม่ครบ 2 convention)", s.replace("power_1 `49a26d47…fb52a` · ", "", 1), need="RECORD-SHA FAIL")
    import hashlib
    ad4_src = io.open(os.path.join(M, "Scripts", "ad4_card.py"), encoding="utf-8").read()
    PIN = ('\n# --- pin block (battery dry-run) ---\nSPEC_SHA = "%s"\nKS_T_UNITS = 23\nKS_ACHIEVED = 0.0475\nRG14_TAGS = tuple(f"ad4_rg14_w{k}" for k in range(50, 100))\n')
    good = ad4_src + PIN % hashlib.sha256(s.encode("utf-8")).hexdigest()
    mut_script("(J) dry-run pin block ถูก → PASS + ==", good, expect=(0,), need="spec-pin (J): SPEC_SHA == sha256(LF card)")
    mut_script("(J) pin KS_T_UNITS=99", good.replace("KS_T_UNITS = 23", "KS_T_UNITS = 99", 1), need="SPEC-PIN FAIL (J): KS_T_UNITS")
    mut_script("(J) pin RG14_TAGS range(7)", good.replace("range(50, 100)", "range(7)"), need="SPEC-PIN FAIL (J): RG14_TAGS")   # replace ทุก occurrence — pin จริงมี range(50, 100) อยู่แล้ว (ast: assignment สุดท้ายชนะ)
    mut_script("(J) SPEC_SHA ปลอม", ad4_src + PIN % ("0" * 64), need="SPEC-PIN FAIL (J): SPEC_SHA")
    # v10 รอบ 23 — (K) fail-closed + --require-pin
    l149_line = next(l for l in L if l.startswith("- **SHA-256 `Scripts/ad4_cert_out/`"))
    mut("(K) ลบบรรทัด §7.1 :149 ทั้งบรรทัด", s.replace(l149_line + "\n", "", 1), need="RECORD-SHA FAIL")
    mut("(K) ลบ token v1 anchor :148", s.replace("blob `46dcd4d0…0ac776` · sha256(LF) `96f1206f…968d8e`", "blob/sha (ดู git)", 1), need="RECORD-SHA FAIL")
    rd = os.path.join(M, "Scripts", "ad4_cert_out"); os.rename(rd, rd + "_hidden")
    try: ok, rc, out = run(s); results.append(("(K) ซ่อน ad4_cert_out → require≥1/COUNTS", ok and ("ANCHOR FAIL" in out or "COUNTS FAIL" in out), rc))
    finally: os.rename(rd + "_hidden", rd)
    nopin = re.sub(r"^(SPEC_SHA|KS_T_UNITS|KS_ACHIEVED|RG14_TAGS)\s*=.*$", "", ad4_src, flags=re.M)
    mut_script("(J) --require-pin ไม่มี pin → FAIL", nopin, need="SPEC-PIN FAIL (J · --require-pin)", flags=("--require-pin",))
    mut_script("(J) --require-pin + pin ถูก → PASS", good, expect=(0,), need="spec-pin (J): SPEC_SHA == sha256(LF card)", flags=("--require-pin",))
    caught = sum(1 for _, ok, _ in results if ok); total = len(results)
    print(f"mutation battery v10 (tempdir mirror): total={total} caught={caught} missed={total-caught}")
    for name, ok, rc in results:
        if not ok: print("  MISSED", name, "rc=", rc)
    return 0 if caught == total else 1


if __name__ == "__main__":
    sys.exit(main())
