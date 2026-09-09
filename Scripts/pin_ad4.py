# -*- coding: utf-8 -*-
"""pin_ad4.py — seal/check tool ของ pin block ใน Scripts/ad4_card.py (card AD-4 §7(11)(12)(12b) · §0 N2 · N11 freeze)
self-test(pin/seal tooling · commit spec) — synthetic/doc only · no data · no P&L

  --check   (default) คำนวณ sha256(LF-normalized card) เทียบ SPEC_SHA ใน ad4_card.py + พิมพ์ constants ที่ pin → exit 0 ตรง / 1 ไม่ตรง / 2 ไม่มี pin
  --seal    เขียน SPEC_SHA = sha256(LF card) ทับค่าเดิม (PENDING หรือ hex) · ห้ามเขียนกลับลง card (§3.5-v4 chunk bullet) · ใช้ตามลำดับปิด :91:
            บล็อกดิบรอบสุดท้าย = edit สุดท้ายของ card → --seal → card_scan.py --require-pin ต้อง PASS → ผลลง LEDGER + commit message
ประวัติ: phase 1 (docstring v5 + constants + PENDING) apply 2026-09-09 หลังวินอนุมัติ patch verbatim (Engineer รอบ 23 เห็นตรงกัน) · seal ครั้งแรก = 6b373c55…
"""
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")   # invariant: reconfigure ก่อน emit ตัวแรก (F23-2)
except Exception:
    pass
import io, os, re, hashlib, ast

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "ad4_card.py")
CARD = os.path.join(ROOT, "Plan", "TRELLIS-010_card_AD4_fine_cadence.md")
RX = re.compile(r'^(SPEC_SHA\s*=\s*")([0-9a-f]{64}|PENDING)(")', re.M)


def card_sha():
    return hashlib.sha256(io.open(CARD, "rb").read().replace(b"\r\n", b"\n")).hexdigest()


def pins(src):
    out = {}
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            nm = node.targets[0].id
            if nm in ("SPEC_SHA", "KS_T_UNITS", "KS_ACHIEVED", "RG14_TAGS"):
                try: out[nm] = ast.literal_eval(node.value)
                except Exception: out[nm] = ast.get_source_segment(src, node.value)
    return out


def main(argv):
    src = io.open(SCRIPT, encoding="utf-8").read()
    h = card_sha()
    m = RX.search(src)
    if "--seal" in argv:
        if not m:
            print("pin_ad4: ไม่พบ SPEC_SHA module-level ใน ad4_card.py — phase 1 (docstring + constants) ต้องเกิดก่อน"); return 2
        src2 = RX.sub(lambda mm: mm.group(1) + h + mm.group(3), src, count=1)
        io.open(SCRIPT, "w", encoding="utf-8", newline="\n").write(src2)
        print(f"sealed SPEC_SHA = {h}"); return 0
    p = pins(src)
    if "SPEC_SHA" not in p:
        print(f"pin_ad4 --check: ไม่มี pin (SPEC_SHA module-level) · sha256(LF card) ตอนนี้ = {h}"); return 2
    ok = p["SPEC_SHA"] == h
    print(f"pin_ad4 --check: SPEC_SHA {'==' if ok else '≠'} sha256(LF card) · script={str(p['SPEC_SHA'])[:16]}… card={h[:16]}… · KS_T_UNITS={p.get('KS_T_UNITS')} KS_ACHIEVED={p.get('KS_ACHIEVED')} RG14_TAGS={p.get('RG14_TAGS')}")
    return 0 if ok else 1


if __name__ == "__main__":
    _sys.exit(main(_sys.argv[1:]))
