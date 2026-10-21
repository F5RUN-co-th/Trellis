# -*- coding: utf-8 -*-
"""card_scan.py v15 — (K) fail-closed + N10 docstring ad4_card + freeze-guard (รอบ 23) · v14 (J)v2 ast+value · (K) record-sha · require≥1 4 key · pointer regex · --require-pin (รอบ 22) · v13 (J) spec-pin card↔ad4_card.py · (E9) require≥1/hit-count/--freeze-counts sidecar (รอบ 21) · v12.1 importer ast · N10 retired-term + N13 operative-loci scanner ของ card AD-4 (deterministic)
exit 0 = PASS · 1 = violation · 2 = tool error · SSOT ของ PATTERNS (§0 N10/N13 อ้างมาที่นี่)"""
import io, re, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

def main():
    _args = [a for a in sys.argv[1:] if not a.startswith("--")]
    CARD = _args[0] if _args else r"D:/workspace/Doc/T.me/R&D/Trellis/Plan/TRELLIS-010_card_AD4_fine_cadence.md"
    FREEZE = "--freeze-counts" in sys.argv   # flags: --freeze-counts · --require-pin
    L = io.open(CARD, encoding="utf-8").read().split("\n")
    if not any(l.startswith("## 0.") for l in L):
        print("SCAN n/a (card ไม่มี §0 NORMATIVE — กฎ N10/N13 ใช้กับ AD-4 เป็นต้นไป)"); return 0
    def find(prefix): return next(i for i, l in enumerate(L, 1) if l.startswith(prefix))
    s0, s1 = find("## 0."), find("## 1.")
    s33, s33v4 = find("### 3.3 "), find("### 3.3-v4")
    s35, s35v4 = find("### 3.5 "), find("### 3.5-v4")
    s4, s5 = find("## 4."), find("## 5.")
    s61, s7, s8 = find("### 6.1"), find("## 7."), find("## 8.")
    cl = find("## Changelog")
    chunk = next(i for i, l in enumerate(L, 1) if l.startswith("- **chunk-file certify"))
    n4 = next(i for i, l in enumerate(L, 1) if "**gate เดียว (mechanical):**" in l)
    n10 = find("- **N10")
    loci = set(range(s0, s1)) | set(range(s4, s5)) | set(range(s7, s8)) | {chunk, n4}
    record = (set(range(s61, s7)) | set(range(s33, s33v4)) | (set(range(s35, s35v4)) - {n4})
              | {i for i, l in enumerate(L, 1) if l.startswith("- **§3.3-v4-T trail") or l.startswith("- [SUPERSEDED")})
    SEG = re.compile(r"~~|[\[(]T\d+[\])]|⟪RETIRED⟫|ตัวอักษรเดิม")

    # ---- N10 PATTERNS (SSOT) ----
    N10 = [r"SELECT", r"FPR_val gate", r"held-out", r"114 rows", r"79\.3", r"cadence=1 ≡ annual bit-exact", r"bit-exact",
           r"1\.35%(?! \(7 cells| →)", r"62×|62 เท่า", r"exact.{0,25}โดยสร้าง|by construction", r"volume-effect *:= *run-time",
           r"RG1-RG9|RG1-RG11|RG1-RG12", r"\{1\.\.m−1\}|\{1, …, m−1\}", r"leak.{0,10}วัดจริง", r"23,759,665,664",
           r"ถึง channel \(i\)", r"≈ ?0\.007", r"ดัน ESTIMATION", r"ESTIMATION ≥|98\.6", r"เว้น v5",
           r"Rec-9", r"local action", r"≈ ?94 CPU", r"0\.09%", r"DIR_EXP_LIN\[i\]\[sl\]", r"probe_iii",
           r"fold ≥2017: refit\)", r"\.5405⁷", r"\bexistence\b", r"∃\**\s*fold ≥2017", r"fold 2016 = (?:`[^`]*` )?cache|fold 2016: base ไม่มี prefix → cache", r"honor-system", r"lock ระดับ artifact", r"6-9 ชม"]
    fail = 0
    for pat in N10:
        rx = re.compile(pat)
        for i, l in enumerate(L, 1):
            if i >= cl or i == n10 or i in record: continue
            for m in rx.finditer(l):
                seg = l[max(0, m.start() - 80): m.end() + 80]
                if SEG.search(seg): continue
                fail += 1; print(f"N10 FAIL L{i} /{pat}/ :: …{l[max(0,m.start()-50):m.end()+40]}…")
    # ---- v15 N10 บน docstring ของ ad4_card.py (F23-4 รอบ 23: artifact ที่ freeze คู่ card · SSOT PATTERNS เดียวกัน + term ของ design v3/v4) ----
    import os as _os0, ast as _ast0
    _ad4p = _os0.path.join(_os0.path.dirname(_os0.path.dirname(CARD)), "Scripts", "ad4_card.py")
    _doc = _ast0.get_docstring(_ast0.parse(io.open(_ad4p, encoding="utf-8").read())) or ""
    for pat in N10 + [r"design v3\+R6", r"block-permutation", r"รอ Engineer R7", r"design v4 \("]:
        for m in re.finditer(pat, _doc):
            seg = _doc[max(0, m.start() - 80): m.end() + 80]
            if SEG.search(seg): continue
            fail += 1; print(f"N10 FAIL ad4_card.py docstring /{pat}/ :: …{_doc[max(0,m.start()-40):m.end()+40]}…")
    # ---- N13 ----
    OP_ALLOW = re.compile(r"operative = §0|\(= §0 N4\)|NON-OPERATIVE|OPERATIVE|operative-loci|operative loci|operative list = §0|ประโยค operative|เฉพาะ.{0,10}operative|บรรทัด operative|ป้าย \"operative\"|operative = RG")
    ptr = re.compile(r"§0|N\d+\b")
    for i, l in enumerate(L, 1):
        if i >= cl or i in loci or i in record: continue
        for m in re.finditer(r"\boperative\b", l):
            seg = l[max(0, m.start() - 80): m.end() + 80]
            if OP_ALLOW.search(seg) or SEG.search(seg): continue
            fail += 1; print(f"N13 FAIL L{i} ป้าย operative นอก loci :: …{seg}…")
        for m in re.finditer(r"assert|⟺", l):
            seg = l[max(0, m.start() - 80): m.end() + 80]
            if SEG.search(seg): continue
            fail += 1; print(f"N13 FAIL L{i} assert/⟺ นอก loci :: …{seg}…")
        if re.search(r"ต้อง|ห้าม|บังคับ", l) and not ptr.search(l):
            fail += 1; print(f"N13 FAIL L{i} pointer discipline (ต้อง/ห้าม/บังคับ ไม่มี §0/N) :: {l[:100]}")
    # ---- v4 (A) RG identifier check: backtick tokens ใน N7 + §4-v4 ต้องมีอยู่ใน schema string / §7 scope / code ----
    import os
    n7 = find("- **N7")
    sec7 = "\n".join(L[s7-1:s8-1])
    m_schema = re.search(r"ลำดับ = `([^`]*)`", sec7)
    schema = m_schema.group(1) if m_schema else ""
    code = ""
    for fn in ("ad4_card.py","ad1_card.py","tp1_card.py","direction_predictor.py","direction_at_real_exit.py"):
        fp = os.path.join(os.path.dirname(os.path.dirname(CARD)), "Scripts", fn)
        if not os.path.exists(fp): raise RuntimeError(f"Scripts/{fn} ไม่พบ — tool mis-config (exit 2)")
        code += io.open(fp, encoding="utf-8").read()
    hay = schema + "\n" + sec7 + "\n" + code
    rg_lines = [n7] + list(range(s4, s5))
    for i in rg_lines:
        l = L[i-1]
        if i in record: continue
        for tok in re.findall(r"`([^`]+)`", l):
            if ":" in tok or "/" in tok or ".py" in tok or re.fullmatch(r"[\d.,]+", tok): continue   # citation/path/number
            mm = re.match(r"[A-Za-z_][A-Za-z0-9_]*", tok)
            if not mm: continue
            t = mm.group(0)
            NUMPY = {"array_equal","where","concatenate","mean","quantile","float","int"}
            if len(t) <= 2 or t in NUMPY or "__" in t or tok.startswith("np.") or tok.startswith("w."): continue
            if t not in hay:
                fail += 1; print(f"IDENT FAIL L{i} `{t}` ไม่อยู่ใน schema/§7/code")
    # ---- v8 (B) cost = derive-and-compare · ทุก "X CPU-h" ต้องมี factor tag ติดกัน · draws/sec parse จาก card (Rc4) · EXPECT injective (Rc1) · range upper (Rc2) · RETIRED/EXT allowlist (Rc5) · ~~ = คู่จริง ไม่นับใน backtick (Rc3) ----
    import itertools
    def strike_spans(l):
        clean = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), l)      # ignore ~~ inside backtick
        pos = [m.start() for m in re.finditer(r"~~", clean)]
        if len(pos) % 2 == 1:
            raise RuntimeError(f"~~ เลขคี่นอก backtick ({len(pos)}) — parity ไม่ระบุ · tool error (exit 2)")
        return [(pos[k], pos[k+1]) for k in range(0, len(pos), 2)]
    def inside_strike(l, pos):
        return any(a <= pos < b for a, b in strike_spans(l))
    m1 = re.search(r"A-1 PRIMARY ([\d,]+)×82×1\.33", body_all := "\n".join(L[:cl-1]))
    m2 = re.search(r"เต็ม ([\d,]+)×82×1\.33", body_all)
    m3 = re.search(r"~(\d+) s/draw", body_all)
    if not (m1 and m2 and m3): raise RuntimeError("parse draws/sec จาก card ไม่ได้ (tool error · exit 2)")
    A1, FULL, S, F = int(m1.group(1).replace(",", "")), int(m2.group(1).replace(",", "")), float(m3.group(1)), 1.33
    if (A1, FULL, S) != (1150, 3080, 82.0): raise RuntimeError(f"draws/sec ใน card ({A1},{FULL},{S}) ≠ pinned (1150,3080,82) — spec drift (exit 2)")
    EXPECT = {"A1×1.33": A1*S*F/3600, "full×1.33": FULL*S*F/3600, "A1×0.33": A1*S*0.33/3600, "full×0.33": FULL*S*0.33/3600,
              "full×1.0": FULL*S/3600, "fold-share": A1*S*0.33/3600/5, "RG14 W=50": 50*100*0.82*(1+F)/3600, "RG14 Δ": (50-35)*100*0.82*(1+F)/3600}
    tol = lambda v: max(0.25, 0.01 * v)
    for a, b in itertools.combinations(EXPECT, 2):
        if abs(EXPECT[a] - EXPECT[b]) <= tol(EXPECT[a]) + tol(EXPECT[b]):
            raise RuntimeError(f"EXPECT ไม่ injective ที่ tol: {a} vs {b} (exit 2)")
    ALLOW_EXEMPT = {("RETIRED", "90-430"), ("RETIRED", "94"), ("RETIRED", "6.1-10.6"), ("RETIRED", "3"), ("RETIRED", "26"), ("EXT", "4.6"), ("STRUCK", "94"), ("STRUCK", "26"), ("STRUCK", "3"), ("STRUCK", "6.1-10.6"), ("STRUCK", "10.6")}
    for i, l in enumerate(L, 1):
        if i >= cl or i in record: continue
        for m in re.finditer(r"(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))? CPU-h(\[([^\]]+)\])?", l):
            val = m.group(0).split(" CPU-h")[0]
            if inside_strike(l, m.start()):
                if ("STRUCK", val) not in ALLOW_EXEMPT:
                    fail += 1; print(f"COST FAIL L{i} ~~-wrapped {val} CPU-h ไม่อยู่ใน allowlist (Rec-6 รอบ 15)")
                continue
            tag = m.group(4)
            if tag is None:
                fail += 1; print(f"COST FAIL L{i} {m.group(0)} ไม่มี factor tag [..] ติดกัน"); continue
            if tag in ("EXT", "RETIRED"):
                if (tag, val) not in ALLOW_EXEMPT:
                    fail += 1; print(f"COST FAIL L{i} [{tag}] บน {val} ไม่อยู่ใน allowlist ของ script (Rc5)")
                continue
            if tag not in EXPECT:
                fail += 1; print(f"COST FAIL L{i} tag ไม่รู้จัก [{tag}]"); continue
            exp = EXPECT[tag]
            for g in (1, 2):
                if m.group(g) is None: continue
                x = float(m.group(g))
                if abs(x - exp) > tol(exp):
                    fail += 1; print(f"COST FAIL L{i} {m.group(0)}: {x} ≠ คาด {exp:.2f} จาก tag [{tag}]")
    # ---- v9 (E) ramp contrast: parse q / Q2-Q4 / φ จาก card (fail-loud) · endpoint contrast · เทียบทุก "×N.NN-N.NN" นอก ~~ ----
    n_occ = sum(len(re.findall(r" CPU-h", l)) for i, l in enumerate(L, 1) if i < cl)
    n_rec = sum(len(re.findall(r" CPU-h", l)) for i, l in enumerate(L, 1) if i < cl and i in record)
    n_tag = sum(len(re.findall(r" CPU-h\[", l)) for i, l in enumerate(L, 1) if i < cl and i not in record)
    print(f"cost occurrences before Changelog: total={n_occ} · tagged(non-record)={n_tag} · record={n_rec} · struck/untagged={n_occ-n_tag-n_rec}")
    body = "\n".join(L[:cl-1])
    mq = re.search(r"(?<![0-9])q = \[([\d, ]+)\]", body)
    if not mq: raise RuntimeError("parse q ไม่ได้ (tool error · exit 2)")
    q = [int(v) for v in mq.group(1).split(",")]
    mQ = re.search(r"\((\d+)/(\d+)/(\d+)/(\d+)/(\d+)\)", body)
    if not mQ: raise RuntimeError("parse Q2-Q4 (n_te − q) จาก §1 ไม่ได้ (exit 2)")
    n_te = [int(mQ.group(k)) + qi for k, qi in zip(range(1, 6), q)]
    mphi = re.search(r"φ=\.(\d+)", body)
    if not mphi: raise RuntimeError("parse φ จาก card ไม่ได้ (exit 2)")
    phi = float("0." + mphi.group(1))
    contrast = [1 + (3*qi - 1)/(ni - 1) for qi, ni in zip(q, n_te)]
    lo, hi = f"{min(contrast):.2f}", f"{max(contrast):.2f}"
    print(f"ramp-contrast (endpoint · within-prefix): min={min(contrast):.3f} max={max(contrast):.3f} per-fold={[round(x,3) for x in contrast]} · n_te={n_te} · pinned text must be ×{lo}-{hi}")
    for i, l in enumerate(L, 1):
        if i >= cl or i in record: continue
        for m in re.finditer(r"×(\d\.\d\d)-(\d\.\d\d)", l):
            if inside_strike(l, m.start()): continue
            if (m.group(1), m.group(2)) != (lo, hi):
                fail += 1; print(f"CONTRAST FAIL L{i} ×{m.group(1)}-{m.group(2)} ≠ computed ×{lo}-{hi}")
    # ---- v9 (F) cross-year gap residual: index gap = n_te − 3q + 1 · 4 คู่ · φ^gap · เทียบ text ----
    gaps = [ni - 3*qi + 1 for qi, ni in zip(q, n_te)][:-1]
    glo, ghi = min(gaps), max(gaps); plo, phi_hi = f"{min(phi**g for g in gaps):.2f}", f"{max(phi**g for g in gaps):.2f}"
    print(f"cross-year gap = n_te−3q+1 = {gaps} (4 คู่) · φ={phi} · φ^gap = {[round(phi**g,3) for g in gaps]} · pinned text must be 'gap = n_te − 3q + 1 = {glo}-{ghi} แถว · φ^gap ≈ {plo}-{phi_hi}'")
    n_gap_sites = 0
    for i, l in enumerate(L, 1):
        if i >= cl or i in record: continue
        for m in re.finditer(r"gap = n_te − 3q \+ 1 = (\d+)-(\d+) แถว · φ\^gap ≈ (\d\.\d\d)-(\d\.\d\d)", l):
            n_gap_sites += 1
            if (int(m.group(1)), int(m.group(2))) != (glo, ghi) or (m.group(3), m.group(4)) != (plo, phi_hi):
                fail += 1; print(f"GAP FAIL L{i} {m.group(0)} ≠ computed")
        for m in re.finditer(r"gap = n_te ?− ?3q[^·\n]{0,20}?= ?(\d+)-(\d+)", l):
            if "+ 1" not in m.group(0) and not inside_strike(l, m.start()):
                fail += 1; print(f"GAP FAIL L{i} รูปแบบ gap ไม่ตรง site เดียว (R5 รอบ 15): {m.group(0)}")
    # ---- v9 (G) cross-file: counters/forward-pointer บนบรรทัด live (ยกเว้น dated `- **20` · CLAIM block) · claim-set ของ tp1_card จาก LEDGER ----
    rounds = [int(x) for x in re.findall(r"Engineer DEEP REVIEW รอบ (\d+)", "\n".join(L[cl-1:]))]
    latest = max(rounds) if rounds else 0
    root = os.path.dirname(os.path.dirname(CARD))
    for fn in (".claude/status/STATUS.md", "Plan/TRELLIS-010_LEDGER.md", "Plan/TRELLIS-010_brain_research_workflow.md"):
        fp = os.path.join(root, fn)
        if not os.path.exists(fp): raise RuntimeError(f"{fn} ไม่พบ (exit 2)")
        for ln, tl in enumerate(io.open(fp, encoding="utf-8").read().split("\n"), 1):
            if tl.startswith("- **20") or tl.startswith("### CLAIM-"): continue
            for mm in re.finditer(r"deep review (\d+) รอบ", tl):
                if int(mm.group(1)) != latest:
                    fail += 1; print(f"COUNTER FAIL {fn}:{ln} 'deep review {mm.group(1)} รอบ' ≠ changelog ล่าสุด {latest}")
            # gap ห้ามมีตัวเลข — กัน "ค้าง: รอรอบ 17 · Engineer review รอบ 23" ถูกกลืนโดย alternative ที่ 2 (battery v9 จับ)
            for mm in re.finditer(r"รอรอบ (\d+)|(?:ค้าง|รอ|ต่อไป)[^\n\d]{0,20}?(?:deep review|Engineer review|review)\s*รอบ\s*(\d+)", tl):
                _r = mm.group(1) or mm.group(2)
                if int(_r) != latest + 1:
                    fail += 1; print(f"POINTER FAIL {fn}:{ln} forward-pointer รอบ {_r} ≠ latest+1 = {latest+1}")
    ledger = io.open(os.path.join(root, "Plan/TRELLIS-010_LEDGER.md"), encoding="utf-8").read()
    script_claim = {m.group(1): m.group(2) for m in re.finditer(r"- `(\w+)` ::.*?EXPERIMENT=(?:live|superseded)→(CLAIM-\d{4})", ledger)}
    # v12.1 (รอบ 19): importer ของ tp1_card นับด้วย ast แบบเดียวกับ ledger_check.scan — regex เดิม self-match string literal ในไฟล์นี้หลัง ship เข้า Scripts/ (7 → 8)
    import ast as _ast
    def _imports_tp1(path):
        try: tree = _ast.parse(io.open(path, encoding="utf-8").read())
        except SyntaxError: return False
        for n in _ast.walk(tree):
            if isinstance(n, _ast.Import) and any(a.name.split(".")[0] == "tp1_card" for a in n.names): return True
            if isinstance(n, _ast.ImportFrom) and n.level == 0 and n.module and n.module.split(".")[0] == "tp1_card": return True
        return False
    importers = sorted(f[:-3] for f in os.listdir(os.path.join(root, "Scripts")) if f.endswith(".py") and f != "tp1_card.py" and _imports_tp1(os.path.join(root, "Scripts", f)))
    expected = {script_claim[s_] for s_ in importers if s_ in script_claim} | ({script_claim["tp1_card"]} if "tp1_card" in script_claim else set())
    n_claimset = 0
    for i, l in enumerate(L, 1):
        if i >= cl or i in record: continue
        for mm in re.finditer(r"dependency ของ (CLAIM-\d{4}(?:/\d{4})*)", l):
            n_claimset += 1
            ids = mm.group(1).split("/"); listed = {ids[0]} | {"CLAIM-" + x for x in ids[1:]}
            if listed != expected:
                fail += 1; print(f"CLAIM-SET FAIL L{i} listed={sorted(listed)} ≠ expected={sorted(expected)}")
        if "dependency ของ CLAIM-" in l:
            for mm in re.finditer(r"\((\d) claim", l):
                if int(mm.group(1)) != len(expected):
                    fail += 1; print(f"CLAIM-COUNT FAIL L{i} '{mm.group(0)}' ≠ {len(expected)}")
    # ---- v10 (H) duplicate-operative ใน loci: token ที่ต้องมีคำตอบเดียว — ปรากฏด้วยค่าต่างกัน = FAIL (RC-α ภายใน §0/§4/§7 · A1/A2 รอบ 16) ----
    def live_only(l, keep_backtick=False):
        l2 = l if keep_backtick else re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), l)
        spans = strike_spans(l)
        out = "".join(ch if not any(a <= k < b for a, b in spans) else " " for k, ch in enumerate(l2))
        return re.sub(r" {2,}", " ", out.replace("`", ""))
    HTOK = {
        "RG13(ข) quantifier": (r"(∀|∃)\**\s*fold ≥2017", lambda m: m.group(1)),
        "fold 2016 annual arm": (r"fold 2016 (refit ≡ cache|refit == cache|= +cache|= +DIR_EXP_LIN +cache)", lambda m: "refit≡cache" if "refit" in m.group(1) else "cache-dispatch"),
        "annual_fn default": (r"annual_fn=(\w+)[,)]", lambda m: m.group(1)),   # v6: §7(3) signature ต่อด้วย , detail/folds
        "RG10 comparator": (r"dp == (dpA_draw|DIR_EXP_LIN)", lambda m: m.group(1)),
        "R6 cell-scope": (r"(?:7 (?:POWER_CELLS|cells) \**ของ \**|rule R6 บน )(PRIMARY|null ของ main|C1-\w+|b=7)", lambda m: m.group(1)),
    }
    for name, (pat, key) in HTOK.items():
        seen = {}
        for i in sorted(loci):
            for m in re.finditer(pat, live_only(L[i-1], keep_backtick=True)):
                seen.setdefault(key(m), []).append(i)
        if len(seen) > 1:
            fail += 1; print(f"DUP-OPERATIVE FAIL [{name}] คำตอบต่างกันใน loci: {seen}")
    # ---- v11 (H′) N7 = pointer-only + raise-class: ห้ามมี assert / array_equal / operand ----
    n7l = live_only(L[n7-1], keep_backtick=True)
    bad = re.findall(r"assert|array_equal|payQ − payA|keep\.sum\(\)|p_cal|n_distinct|_rng\(|∀|∃|dpA", n7l)
    if bad:
        fail += 1; print(f"N7 FAIL (H′): N7 มี operand/assert {bad} — clause ต้องอยู่ §4-v4 เท่านั้น (A-1/A-2 รอบ 17)")
    # ---- v10 (I) derive-and-compare จาก q/n_te: prefix m · 2q · Σ(Q2-Q4)=610 · C1-restricted states m−2b+1 (b=40) · b=7 nblk ceil(m/7) · ∏m ----
    mvec = [3*qi for qi in q]; twoq = [2*qi for qi in q]; tot = sum(ni - qi for qi, ni in zip(q, n_te))
    states = [mi - 80 + 1 for mi in mvec]; nblk = [-(-mi // 7) for mi in mvec]
    prod = 1
    for mi in mvec: prod *= mi
    discard = 100 * (1 - sum(states) / sum(mvec))
    junc = [(3*qi - 1) / (mi - 1) * 100 for qi, mi in zip(q, mvec)]   # conditional s≠0 · (prefix_s−1)/(m−1) ที่ Q4 = 100 · Q2/Q3 ต่อ fold 2016 ด้านล่าง
    j2016 = ((q[0] - 1) / (mvec[0] - 1) * 100, (2*q[0] - 1) / (mvec[0] - 1) * 100)
    DER = {"prefix m": f"[{','.join(map(str,mvec))}]", "2q": f"[{','.join(map(str,twoq))}]", "610": str(tot),
           "C1-restricted states": f"[{','.join(map(str,states))}]", "nblk": f"[{','.join(map(str,nblk))}]", "∏m": f"{prod:,}", "discard%": f"{discard:.2f}%"}
    print(f"derived: {DER} · junction fold2016 Q2/Q3 (conditional s≠0) = {j2016[0]:.1f}/{j2016[1]:.1f}% · unconditional full group = {(q[0]-1)/mvec[0]*100:.1f}/{(2*q[0]-1)/mvec[0]*100:.1f}%")
    body_live = "\n".join(live_only(l) for i, l in enumerate(L, 1) if i < cl and i not in record)
    CHK = [("prefix m", r"(?<![0-9∏])m = \[([\d,]+)\]", lambda g: f"[{g}]"), ("2q", r"2q = \[([\d,]+)\]", lambda g: f"[{g}]"),
           ("610", r"= \*\*(\d{3}) แถว\*\*|= \*\*(\d{3})\*\* \(1\d\d/", lambda g: g), ("C1-restricted states", r"states/fold = \[([\d,]+)\]|\[(3\d,5\d,4\d,3\d,4\d)\]", lambda g: f"[{g}]"),
           ("nblk", r"nblk[^\[\n]{0,20}\[([\d,]+)\]|\[(1\d,1\d,1\d,1\d,1\d)\]", lambda g: f"[{g}]"), ("∏m", r"∏m(?:_i)? = ([\d,]{10,})", lambda g: g),
           ("discard%", r"ทิ้ง \*\*(\d\d\.\d\d)%\*\* ของ reference set", lambda g: f"{g}%")]
    chk_hits = {}
    for name, pat, norm in CHK:
        hits = 0
        for m in re.finditer(pat, body_live):
            got = norm(next(g for g in m.groups() if g)); hits += 1
            if got != DER[name]:
                fail += 1; print(f"DERIVED FAIL [{name}] '{m.group(0)[:40]}' ≠ computed {DER[name]}")
        chk_hits[name] = hits
        if hits == 0:
            fail += 1; print(f"DERIVED FAIL [{name}] 0 site — require-then-compare (E9 รอบ 21): anchor หาย = FAIL ไม่ใช่ ok")
    print(f"derived hits: {chk_hits}")
    # ---- v12 (I) junction% compare: conditional s≠0 (prefix_s−1)/(m−1) · unconditional full group (prefix_s−1)/m (B-1′ รอบ 18) ----
    jc = (f"{(q[0]-1)/(mvec[0]-1)*100:.1f}", f"{(2*q[0]-1)/(mvec[0]-1)*100:.1f}", str(q[0]-1), str(mvec[0]-1))
    ju = (f"{(q[0]-1)/mvec[0]*100:.1f}", f"{(2*q[0]-1)/mvec[0]*100:.1f}", f"{(mvec[0]-1)/mvec[0]*100:.1f}")
    nj = 0
    for m in re.finditer(r"Q2 ≈ (\d+\.\d)% \((\d+)/(\d+) fold 2016\) · Q3 ≈ (\d+\.\d)%", body_live):
        nj += 1
        if (m.group(1), m.group(4), m.group(2), m.group(3)) != jc:
            fail += 1; print(f"DERIVED FAIL [junction cond] '{m.group(0)}' ≠ computed Q2 {jc[0]} ({jc[2]}/{jc[3]}) · Q3 {jc[1]}")
    for m in re.finditer(r"×\(m−1\)/m → (\d+\.\d) / (\d+\.\d) / (\d+\.\d)%", body_live):
        nj += 1
        if m.groups() != ju:
            fail += 1; print(f"DERIVED FAIL [junction uncond] '{m.group(0)}' ≠ computed {'/'.join(ju)}")
    print(f"derived [junction]: sites={nj} · cond {jc[0]}/{jc[1]}/100.0 · uncond {'/'.join(ju)}")
    print(f"cross-file: latest round={latest} · tp1_card importers={len(importers)} · expected claim-set={sorted(expected)} · gap sites={n_gap_sites} · claim-set sites={n_claimset}")
    # ---- v14 (J) v2 spec-pin: ast module-level + เทียบค่ากับ authority ใน card (F-A2 รอบ 22: v13 ตรวจชื่อไม่ตรวจค่า + fail-open indent) · --require-pin ที่ commit gate ----
    import ast as _ast2, json, hashlib
    REQUIRE_PIN = "--require-pin" in sys.argv
    src_ad4 = io.open(os.path.join(root, "Scripts", "ad4_card.py"), encoding="utf-8").read()
    pins = {}
    for node in _ast2.parse(src_ad4).body:   # module-level เท่านั้น (indent = ไม่นับ)
        if isinstance(node, _ast2.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], _ast2.Name):
            nm = node.targets[0].id
            if nm in ("SPEC_SHA", "KS_T_UNITS", "KS_ACHIEVED", "RG14_TAGS"):
                try: pins[nm] = _ast2.literal_eval(node.value)
                except Exception: pins[nm] = _ast2.get_source_segment(src_ad4, node.value)
    card_lf = hashlib.sha256(io.open(CARD, "rb").read().replace(b"\r\n", b"\n")).hexdigest()
    body_txt = "\n".join(L[:cl-1])
    m_t = re.search(r"t = (\d+)/400 = 0\.\d+ \(achieved false-flag \*\*(\d+\.\d+)%\*\*", body_txt)
    m_tags = re.search(r"`RG14_TAGS = ([^`]+)`", body_txt)
    if not (m_t and m_tags): raise RuntimeError("parse authority ของ pin (N2b t/achieved · (12b) RG14_TAGS) จาก card ไม่ได้ (exit 2)")
    EXP = {"KS_T_UNITS": int(m_t.group(1)), "KS_ACHIEVED": round(float(m_t.group(2)) / 100, 6), "RG14_TAGS": m_tags.group(1).strip()}
    spec = pins.get("SPEC_SHA")
    if spec is None or spec == "PENDING":
        msg = f"spec-pin (J): SPEC_SHA = {spec or 'ไม่พบ (ต้องเป็น module-level Assign · AnnAssign/indent ไม่นับ)'} — pin ยังไม่เกิด (F1 รอบ 20) · pins มี {sorted(pins)} · sha256(LF card) ตอนนี้ = {card_lf[:16]}…"
        if REQUIRE_PIN: fail += 1; print("SPEC-PIN FAIL (J · --require-pin): " + msg)
        else: print(msg)
    else:
        jf = 0
        if spec != card_lf:
            jf += 1; print(f"SPEC-PIN FAIL (J): SPEC_SHA = {str(spec)[:16]}… ≠ sha256(LF card) = {card_lf[:16]}… — card ถูกแก้หลัง pin (N11) หรือ pin ผิด")
        for k, ev in EXP.items():
            got = pins.get(k)
            if k == "KS_ACHIEVED": ok = isinstance(got, float) and abs(got - ev) < 1e-9
            elif k == "RG14_TAGS": ok = isinstance(got, str) and re.sub(r"\s+", "", got) == re.sub(r"\s+", "", ev)
            else: ok = got == ev
            if not ok: jf += 1; print(f"SPEC-PIN FAIL (J): {k} = {got!r} ≠ authority ใน card {ev!r}")
        fail += jf
        if not jf: print(f"spec-pin (J): SPEC_SHA == sha256(LF card) {card_lf[:16]}… · KS_T_UNITS/KS_ACHIEVED/RG14_TAGS == card")
    # ---- v14 (K) §7.1 record hashes = derive-and-compare (F-A1 รอบ 22: hand-copy 18 token ผิด 1 → ย้าย §7.1 เข้า scanner-class) ----
    rec_dir = os.path.join(root, "Scripts", "ad4_cert_out")
    l148 = next((l for l in L[:cl-1] if "ณ commit ขั้น 0" in l and "f99031e" in l), None)
    l149 = next((l for l in L[:cl-1] if l.startswith("- **SHA-256 `Scripts/ad4_cert_out/`")), None)
    ntok = 0
    if os.path.isdir(rec_dir):   # ทรีนี้มี record จริง ⇒ anchor ต้องมี (F23-1 รอบ 23: fail-closed asymmetric)
        if not l149:
            fail += 1; print("RECORD-SHA FAIL (K) ad4_cert_out มีอยู่แต่บรรทัด §7.1 :149 หาย — anchor deletion (require≥1)")
        if not l148:
            fail += 1; print("RECORD-SHA FAIL (K) บรรทัด §7.1 :148 (v1 anchor) หาย")
        shas = {}
        for fn in sorted(os.listdir(rec_dir)):
            if not fn.endswith(".csv"): continue
            lf = io.open(os.path.join(rec_dir, fn), "rb").read().replace(b"\r\n", b"\n")
            shas[fn[:-4]] = (hashlib.sha256(lf).hexdigest(), hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest())
        seen = {k: [0, 0] for k in shas}; ntok = 0
        for m in re.finditer(r"(stable|power_\d) `([0-9a-f]{8})…([0-9a-f]{5,8})`", l149 or ""):
            name, pre, suf = m.groups(); ntok += 1
            if name not in shas: fail += 1; print(f"RECORD-SHA FAIL (K) `{name}` ไม่มีไฟล์ใน ad4_cert_out"); continue
            lf_h, crlf_h = shas[name]
            if lf_h.startswith(pre) and lf_h.endswith(suf): seen[name][0] += 1
            elif crlf_h.startswith(pre) and crlf_h.endswith(suf): seen[name][1] += 1
            else: fail += 1; print(f"RECORD-SHA FAIL (K) `{name}` `{pre}…{suf}` ≠ LF {lf_h[:8]}…{lf_h[-6:]} / CRLF {crlf_h[:8]}…{crlf_h[-6:]}")
        missing = [k for k, v in seen.items() if v[0] == 0 or v[1] == 0]
        if missing: fail += 1; print(f"RECORD-SHA FAIL (K) token ไม่ครบ {len(shas)} ไฟล์ × 2 convention: {missing}")
        if ntok != 2 * len(shas): fail += 1; print(f"RECORD-SHA FAIL (K) tokens={ntok} ≠ 2×files={2*len(shas)}")
        print(f"record-sha (K): tokens={ntok} · files={len(shas)} · LF+CRLF ครบทุกไฟล์={not missing}")
    else:
        print("record-sha (K): n/a (ทรีนี้ไม่มี Scripts/ad4_cert_out — card/ทรีที่ไม่มี record)")
    if l148:
        import subprocess
        # presence ของ token ไม่ผูกกับ git (F23-1 · battery mirror ไม่มี git) — value เทียบเฉพาะเมื่อ git พร้อม
        for lab in ("blob", "sha256\\(LF\\)"):
            if not re.search(lab + r" `([0-9a-f]{8})…([0-9a-f]{5,8})`", l148):
                fail += 1; print(f"RECORD-SHA FAIL (K) :148 ไม่มี token {lab} (anchor v1 หาย)")
        try:
            blob = subprocess.run(["git", "-C", root, "rev-parse", "f99031e:Scripts/ad4_card.py"], capture_output=True, text=True, check=True).stdout.strip()
            src1 = subprocess.run(["git", "-C", root, "show", "f99031e:Scripts/ad4_card.py"], capture_output=True, check=True).stdout
            sha1 = hashlib.sha256(src1.replace(b"\r\n", b"\n")).hexdigest()
            for lab, val in (("blob", blob), ("sha256\\(LF\\)", sha1)):
                mm = re.search(lab + r" `([0-9a-f]{8})…([0-9a-f]{5,8})`", l148)
                if not mm: fail += 1; print(f"RECORD-SHA FAIL (K) :148 ไม่มี token {lab}")
                elif not (val.startswith(mm.group(1)) and val.endswith(mm.group(2))): fail += 1; print(f"RECORD-SHA FAIL (K) :148 {lab} `{mm.group(1)}…{mm.group(2)}` ≠ {val[:8]}…{val[-6:]}")
            print(f"record-sha (K) v1 anchor: blob {blob[:8]}… · sha256(LF) {sha1[:8]}… ตรวจแล้ว")
        except Exception as e:
            print(f"record-sha (K) v1 anchor: n/a (git ไม่พร้อมในทรีนี้: {type(e).__name__})")
    # ---- v13 (E9) anchor counts sidecar: เครื่องมือ generate เอง (--freeze-counts) · เทียบตอน scan · ต่างจาก frozen = FAIL (regenerate ไม่แก้มือ — doctrine rule (k)) ----
    import json, hashlib
    for k_, v_ in (("gap", n_gap_sites), ("claim-set", n_claimset), ("junction", nj), ("cost-tagged", n_tag), ("record-sha", ntok)):
        if v_ == 0:
            fail += 1; print(f"ANCHOR FAIL [{k_}] 0 site — require≥1 (F-A3 รอบ 22: --freeze-counts zero-out เงียบไม่ได้)")
    counts = {"gap": n_gap_sites, "claim-set": n_claimset, "junction": nj, "cost-tagged": n_tag, "record-sha": ntok, **{f"chk:{k}": v for k, v in chk_hits.items()}}
    side = os.path.join(root, "Scripts", "card_scan_counts.json")
    if FREEZE and fail:
        print("counts NOT frozen — scan มี FAIL (F23-6 รอบ 23): แก้ก่อนแล้วค่อย --freeze-counts")
    elif FREEZE:
        io.open(side, "w", encoding="utf-8", newline="\n").write(json.dumps(counts, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
        print(f"counts frozen → {side}: {counts}")
    elif os.path.exists(side):
        frozen = json.load(io.open(side, encoding="utf-8"))
        diff = {k: (frozen.get(k), counts.get(k)) for k in sorted(set(frozen) | set(counts)) if frozen.get(k) != counts.get(k)}
        if diff:
            fail += 1; print(f"COUNTS FAIL anchor-count ≠ frozen sidecar {{key: (frozen, now)}} = {diff} — ถ้าตั้งใจแก้ card ให้รัน --freeze-counts (ห้ามแก้ json มือ)")
        else: print(f"counts == frozen sidecar ({len(counts)} keys)")
    else:
        fail += 1; print(f"COUNTS FAIL sidecar ไม่มี ({side}) — รัน --freeze-counts ก่อน commit")
    def shadow_pct(lines):
        tot = cov = 0
        for l in lines:
            tot += len(l); mask = [False]*len(l)
            for mm in SEG.finditer(l):
                for k in range(max(0, mm.start()-80), min(len(l), mm.end()+80)): mask[k] = True
            cov += sum(mask)
        return 100*cov/max(tot,1)
    n1 = find("- **N1")
    print(f"shadow ±80: body={shadow_pct(L[:cl-1]):.1f}% §0={shadow_pct(L[s0-1:s1-1]):.1f}% N1={shadow_pct([L[n1-1]]):.1f}%")
    # ---- v5 (D) line stats (emit · ไม่ pin ใน doc) ----
    import statistics
    lens = [len(l) for l in L]
    print(f"line-stats: n={len(lens)} median={statistics.median(lens):.0f} p90={sorted(lens)[int(len(lens)*0.9)]} max={max(lens)}")
    print(f"loci: §0 {s0}-{s1-1} · chunk {chunk} · N4 {n4} · §4 {s4}-{s5-1} · §7 {s7}-{s8-1} · record: v3 {s33}-{s33v4-1},{s35}-{s35v4-1} · §6.1 {s61}-{s7-1} · changelog ≥{cl}")
    print("SCAN", "FAIL" if fail else "PASS", f"({fail} hit)")
    return 1 if fail else 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        print("TOOL ERROR:", repr(e)); sys.exit(2)
