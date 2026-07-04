#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stageb_pipeline.py — TRELLIS-010 Stage B: Knowledge-Harvest Pipeline
ดัดแปลงจาก EchoSeven pipeline (P0/P1 data-integrity layer + /coin-scout) —
หลักเดียวกัน: **pipeline เป็นเจ้าของการตัดสิน admissibility · LLM ให้ evidence เท่านั้น**

กลไก anti-hallucination (ย้ายจาก EchoSeven ครบ):
1. Agent คืน structured JSON ตาม SCHEMA — ไม่เขียนรายงาน/ไม่ให้คะแนนใดๆ
2. apply โหมด fail-loud: ผิด schema = reject ทั้งไฟล์ ไม่เขียนอะไร (เหมือน apply.mjs)
3. **TIER ถูก derive จากการมี/ไม่มี evidence fields ล้วนๆ** (เหมือน build.mjs derive
   qScore=Σ) — LLM ไม่มีช่องกำหนด tier/คะแนน:
     REJECTED (X)  = verifier พิสูจน์ว่า quote ไม่มีจริง / source ไม่ได้พูดตาม claim
     CARD (T)      = quote+URL + rule_formal + numbers + mechanism + ทดสอบได้จาก
                     data ที่มี + **ผ่าน adversarial verify แล้ว** (quote_found ✓)
     AWAIT-VERIFY (V) = ครบทุกอย่างแต่ยังไม่ผ่าน verify — ห้ามใช้ทำ card
     NEEDS-DATA (D)= ครบแต่ต้อง data ใหม่ (→ Stage F backlog)
     PARKED (P)    = ขาด rule/numbers/mechanism (hype filter ของ Gate B) + revisit_if
4. Verify แยก instance mandate=REFUTE + ต้อง fetch URL ซ้ำยืนยัน quote verbatim
   (ฆ่า fabricated citation) — หมายเหตุความซื่อสัตย์ (Engineer A1): script ตรวจ
   structure ของ patch ได้ แต่พิสูจน์ไม่ได้ว่า verifier เป็นคนละ context จริง —
   independence ค้ำด้วย process (orchestrator spawn แยก + provenance บังคับใน patch)
   · verify patch ใหม่ต้องมี field `verifier_provenance` (agent id/run) เพื่อ audit trail
   · การแก้เนื้อหา claim ใดๆ ผ่าน apply จะ REPLACE ทั้ง object → verification เดิมหลุด
   → กลับเป็น V-AWAIT-VERIFY อัตโนมัติ (enforce กติกา parked→promote ต้อง verify ใหม่, A4)
5. Evidence grade (Engineer A2 — กัน T-CARD ดูเท่ากันทั้งที่หลักฐานต่างชั้น):
   T-STRONG = access=full + verifier ยืนยัน numbers_match · T-DIRECTIONAL = ที่เหลือ
   (quote จริงแต่เลข audit ไม่ได้/abstract) — **ห้ามใช้เลขของ T-DIRECTIONAL เป็น prior
   เชิงตัวเลข** ใช้ได้แค่นิยาม+ทิศ
6. Referential integrity (Engineer A3): build ตรวจ id ที่ถูกอ้างในเนื้อ claim —
   อ้าง id ไม่มีจริง หรือ T-CARD พิง claim ที่ X/P = flag ดัง (anti-laundering)
7. Report สร้างจาก data เท่านั้น (generate — ห้ามแก้มือ)

Usage:
  python stageb_pipeline.py apply <file.json ...>   # validate + upsert เข้า claims.json
  python stageb_pipeline.py apply --dry <file.json> # ตรวจอย่างเดียว
  python stageb_pipeline.py build                   # derive tiers + สรุป console
  python stageb_pipeline.py report                  # สร้าง Research/STAGE_B_HARVEST.md
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB = ROOT / "Research" / "stageb" / "claims.json"
REPORT = ROOT / "Research" / "STAGE_B_HARVEST.md"

TRACKS = {"academic", "practitioner", "microstructure"}
COMPUTABLE = {"m1", "dataset", "new_data"}
DIRECTIONS = {"up", "down", "non-directional", "unknown"}
DEAD_VARS = "rv_pct250 / slope_pct250 / range_exp / gap_ratio / aw_ratio"

# ---- SCHEMA (สัญญา agent → pipeline; แบบเดียว schema.json ของ EchoSeven) ----
REQ_STR = ["id", "track", "title", "claim", "relevance", "overlap_risk"]
REQ_SOURCE = ["label", "url", "quote", "access"]      # access: full|abstract|snippet
REQ_TEST = ["computable_from", "prediction_direction", "lookahead_risk"]


def fail(msg):
    print(f"❌ REJECT: {msg}")
    sys.exit(1)


def validate(c, fname):
    for k in REQ_STR:
        if not isinstance(c.get(k), str) or not c[k].strip():
            fail(f"{fname}: field '{k}' ต้องเป็น string ไม่ว่าง")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", c["id"]):
        fail(f"{fname}: id '{c['id']}' ต้องเป็น kebab-case")
    if c["track"] not in TRACKS:
        fail(f"{fname}: track '{c['track']}' ไม่อยู่ใน {TRACKS}")
    src = c.get("source")
    if not isinstance(src, dict):
        fail(f"{fname}: ต้องมี source object")
    for k in REQ_SOURCE:
        if not isinstance(src.get(k), str) or not src[k].strip():
            fail(f"{fname}: source.{k} ต้องเป็น string ไม่ว่าง")
    if not src["url"].startswith("http"):
        fail(f"{fname}: source.url ไม่ใช่ URL: {src['url']}")
    if len(src["quote"].split()) > 80:
        fail(f"{fname}: quote ยาวเกิน 80 คำ — เอาเฉพาะประโยค load-bearing")
    td = c.get("test_design")
    if not isinstance(td, dict):
        fail(f"{fname}: ต้องมี test_design object")
    for k in REQ_TEST:
        if k not in td:
            fail(f"{fname}: test_design.{k} หาย")
    if td["computable_from"] not in COMPUTABLE:
        fail(f"{fname}: computable_from '{td['computable_from']}' ไม่อยู่ใน {COMPUTABLE}")
    if td["prediction_direction"] not in DIRECTIONS:
        fail(f"{fname}: prediction_direction ไม่อยู่ใน {DIRECTIONS}")
    # nullable evidence fields — มี/ไม่มี คือสิ่งที่ derive tier (LLM ห้ามใส่ tier เอง)
    for k in ("rule_formal", "mechanism"):
        if k in c and c[k] is not None and (not isinstance(c[k], str) or not c[k].strip()):
            fail(f"{fname}: {k} ต้องเป็น string หรือ null")
    if "numbers" in c and c["numbers"] is not None:
        n = c["numbers"]
        if not isinstance(n, dict):
            fail(f"{fname}: numbers ต้องเป็น object หรือ null")
        # effect = string (มีเลขจริง) หรือ null (แหล่งไม่ให้เลข — เก็บ metadata ได้
        # แต่ derive_tier จะนับว่า 'ไม่มีตัวเลข' → park ตาม Gate B)
        if n.get("effect") is not None and (not isinstance(n["effect"], str)
                                            or not n["effect"].strip()):
            fail(f"{fname}: numbers.effect ต้องเป็น string ไม่ว่าง หรือ null")
    if "tier" in c or "score" in c:
        fail(f"{fname}: agent ห้ามส่ง tier/score — pipeline derive เอง (anti-inflation)")
    if "verification" in c and not c.get("_is_verify_patch"):
        fail(f"{fname}: verification เพิ่มได้ผ่าน verify-patch เท่านั้น")


def validate_verify(v, fname):
    for k in ("id", "verification"):
        if k not in v:
            fail(f"{fname}: verify patch ต้องมี '{k}'")
    ver = v["verification"]
    for k in ("quote_found", "supports_claim", "numbers_match", "biggest_finding", "note",
              "verifier_provenance"):
        if k not in ver:
            fail(f"{fname}: verification.{k} หาย (provenance บังคับตั้งแต่ Engineer A1 — "
                 f"ระบุ agent/run ที่ทำ verify เพื่อ audit trail)")
    for k in ("quote_found", "supports_claim"):
        if not isinstance(ver[k], bool):
            fail(f"{fname}: verification.{k} ต้องเป็น boolean")


# domain วิชาการ/สถาบัน (mechanical จาก URL — vendor/blog ไม่มีทางได้ STRONG
# ต่อให้เลขตรงหน้าตัวเอง เพราะหน้า audit ไม่ได้)
ACADEMIC_DOMAINS = ("arxiv.org", "ideas.repec.org", "link.springer.com",
                    "faculty.georgetown.edu", "research.cbs.dk", "lbma.org.uk",
                    "researchwithrutgers.org", "pure.qub.ac.uk", "swopec.hhs.se",
                    "cmegroupclientsite.atlassian.net", "researchimpact.uwa.edu.au")


def grade(c):
    """Evidence grade (Engineer A2) — derive ล้วนๆ ไม่มีดุลพินิจ:
    T-STRONG = access=full ∧ verifier ยืนยัน numbers_match ∧ URL เป็น domain
    วิชาการ/สถาบัน · ที่เหลือ = T-DIRECTIONAL (นิยาม+ทิศเท่านั้น ห้ามใช้เลขเป็น prior)"""
    if derive_tier(c) != "T-CARD":
        return ""
    v = c.get("verification", {})
    academic = any(d in c["source"]["url"] for d in ACADEMIC_DOMAINS)
    return ("T-STRONG" if c["source"].get("access") == "full"
            and v.get("numbers_match") and academic else "T-DIRECTIONAL")


def ref_flags(db):
    """Referential integrity (Engineer A3): จับ (1) T-CARD ที่พิง claim tier X/P
    (anti-laundering) (2) การอ้าง id ที่ไม่มีจริงแต่ใกล้เคียง id จริง (dead reference)"""
    ids = set(db["claims"])
    kebab = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+){3,}")
    flags = []
    for cid, c in db["claims"].items():
        prose = " ".join(str(c.get(k, "")) for k in
                         ("claim", "mechanism", "overlap_risk", "relevance", "title"))
        for tok in sorted(set(kebab.findall(prose))):
            if tok == cid or len(tok) < 20:
                continue
            if tok in ids:
                t = derive_tier(db["claims"][tok])
                if t[0] in "XP" and derive_tier(c) == "T-CARD":
                    flags.append(f"⚠ {cid} (T-CARD) อ้างอิง {tok} [{t}] — anti-laundering")
            elif any(i in tok or tok in i for i in ids):
                flags.append(f"⚠ {cid} อ้าง id ไม่มีจริง: '{tok}' (dead reference)")
    return flags


def derive_tier(c):
    """LLM ไม่มีสิทธิ์กำหนด — derive จาก field presence + ผล verify เท่านั้น"""
    ver = c.get("verification")
    if ver and (ver["quote_found"] is False or ver["supports_claim"] is False):
        return "X-REJECTED"
    has_numbers = bool(c.get("numbers")) and bool((c["numbers"] or {}).get("effect"))
    complete = (c.get("rule_formal") and has_numbers and c.get("mechanism"))
    if complete and c["test_design"]["computable_from"] in ("m1", "dataset"):
        return "T-CARD" if (ver and ver["quote_found"] and ver["supports_claim"]) \
            else "V-AWAIT-VERIFY"
    if complete:
        return "D-NEEDS-DATA"
    return "P-PARKED"


def park_reason(c):
    missing = [k for k in ("rule_formal", "mechanism") if not c.get(k)]
    if not (c.get("numbers") and (c["numbers"] or {}).get("effect")):
        missing.append("numbers.effect")
    return f"ขาด {'/'.join(missing)}" if missing else ""


def load_db():
    if DB.exists():
        return json.loads(DB.read_text(encoding="utf-8"))
    return {"claims": {}, "meta": {"created": str(date.today())}}


def save_db(db):
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_apply(files, dry):
    db = load_db()
    for f in files:
        p = Path(f)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            fail(f"{p.name}: JSON parse ไม่ได้ — {e}")
        items = data if isinstance(data, list) else [data]
        for c in items:
            if "verification" in c and "claim" not in c:          # verify patch mode
                validate_verify(c, p.name)
                cid = c["id"]
                if cid not in db["claims"]:
                    fail(f"{p.name}: verify patch อ้าง id '{cid}' ที่ไม่มีใน DB")
                old = derive_tier(db["claims"][cid])
                db["claims"][cid]["verification"] = c["verification"]
                new = derive_tier(db["claims"][cid])
                print(f"  🔬 verify {cid}: {old} → {new} · "
                      f"finding: {c['verification']['biggest_finding'][:90]}")
            else:                                                  # harvest mode
                validate(c, p.name)
                cid = c["id"]
                mode = "update" if cid in db["claims"] else "new"
                c["applied"] = str(date.today())
                db["claims"][cid] = c
                print(f"  ✅ {mode} {cid} [{c['track']}] → {derive_tier(c)} · {c['title'][:70]}")
    if dry:
        print("(dry-run — ไม่เขียนอะไร)")
        return
    save_db(db)
    print(f"wrote {DB} · total claims = {len(db['claims'])}")


def cmd_build():
    db = load_db()
    tiers = {}
    for cid, c in sorted(db["claims"].items()):
        t = derive_tier(c)
        tiers.setdefault(t, []).append(cid)
    print(f"== Stage B build · {len(db['claims'])} claims ==")
    for t in ("T-CARD", "V-AWAIT-VERIFY", "D-NEEDS-DATA", "P-PARKED", "X-REJECTED"):
        ids = tiers.get(t, [])
        print(f"  {t:<16} {len(ids):>3}  {' '.join(ids[:8])}{' …' if len(ids) > 8 else ''}")
    strong = [cid for cid in tiers.get("T-CARD", [])
              if grade(db["claims"][cid]) == "T-STRONG"]
    direc = [cid for cid in tiers.get("T-CARD", []) if cid not in strong]
    print(f"  ├─ T-STRONG      {len(strong):>3}  {' '.join(strong)}")
    print(f"  └─ T-DIRECTIONAL {len(direc):>3}  (นิยาม+ทิศเท่านั้น ห้ามใช้เลขเป็น prior)")
    for f in ref_flags(db):
        print(f"  {f}")
    if tiers.get("V-AWAIT-VERIFY"):
        print(f"\n🔬 NEEDS INDEPENDENT-VERIFY ({len(tiers['V-AWAIT-VERIFY'])}): "
              f"{', '.join(tiers['V-AWAIT-VERIFY'])}")
    return tiers


def cmd_report():
    db = load_db()
    L = [f"# STAGE B — External Knowledge Harvest (generated {date.today()})",
         "",
         "> ไฟล์นี้ generate จาก `Research/stageb/claims.json` โดย `stageb_pipeline.py report`",
         "> — **ห้ามแก้มือ** · tier ทุกตัว derive จาก evidence fields ไม่ใช่ LLM ให้คะแนน",
         f"> Gate B: external = แหล่ง hypothesis ไม่ใช่ความจริง · overlap ต้องวัดกับตัวแปรที่ตายแล้ว ({DEAD_VARS}) ก่อน freeze card",
         ""]
    flags = ref_flags(db)
    if flags:
        L.append("## ⚠ Referential-integrity flags (Engineer A3)\n")
        L += [f"- {f}" for f in flags] + [""]
    order = [("T-CARD", "✅ CARD-READY — ผ่าน adversarial verify (พร้อมเสนอวินเป็น hypothesis card)"),
             ("V-AWAIT-VERIFY", "🔬 รอ independent verify (ห้ามใช้จนกว่าจะผ่าน)"),
             ("D-NEEDS-DATA", "📦 ต้อง data ใหม่ → Stage F backlog"),
             ("P-PARKED", "🅿 PARKED (ขาด rule/ตัวเลข/mechanism — Gate B hype filter)"),
             ("X-REJECTED", "❌ REJECTED (verifier พิสูจน์ว่าแหล่ง/quote ไม่รองรับ)")]
    for t, head in order:
        items = [(cid, c) for cid, c in sorted(db["claims"].items()) if derive_tier(c) == t]
        if not items:
            continue
        L.append(f"## {head} ({len(items)})\n")
        if t == "T-CARD":
            L.append("> **Evidence grade (Engineer A2):** T-STRONG = access:full + ตัวเลข"
                     "ยืนยันบนหน้าแหล่ง · T-DIRECTIONAL = quote จริงแต่เลข audit ไม่ได้ — "
                     "**ห้ามใช้เลขของ T-DIRECTIONAL เป็น prior เชิงตัวเลข** (นิยาม+ทิศเท่านั้น)\n")
        for cid, c in items:
            g = grade(c)
            gtxt = f"  **`{g}`**" if g else ""
            L.append(f"### `{cid}` — {c['title']}  `[{c['track']}]`{gtxt}")
            L.append(f"- **Claim:** {c['claim']}")
            L.append(f"- **Source:** [{c['source']['label']}]({c['source']['url']}) "
                     f"(access: {c['source']['access']})")
            L.append(f"- **Quote:** “{c['source']['quote']}”")
            if c.get("rule_formal"):
                L.append(f"- **Rule:** `{c['rule_formal']}`")
            if c.get("numbers"):
                n = c["numbers"]
                L.append(f"- **Numbers:** {n['effect']}"
                         + (f" · sample: {n.get('sample','—')}" if n.get('sample') else "")
                         + (f" · market: {n.get('market','—')}" if n.get('market') else ""))
            if c.get("mechanism"):
                L.append(f"- **Mechanism (ใครถูกบังคับ):** {c['mechanism']}")
            L.append(f"- **ตอบโจทย์:** {c['relevance']}")
            td = c["test_design"]
            L.append(f"- **Test:** from={td['computable_from']} · direction="
                     f"{td['prediction_direction']} · lookahead: {td['lookahead_risk']}")
            L.append(f"- **Overlap risk vs ตัวแปรที่ตาย:** {c['overlap_risk']}")
            if t == "P-PARKED":
                L.append(f"- **เหตุ park:** {park_reason(c)} · revisit-if: "
                         f"{c.get('revisit_if', 'เจอแหล่งที่มีตัวเลข')}")
            if c.get("verification"):
                v = c["verification"]
                L.append(f"- **🔬 Verify:** quote_found={v['quote_found']} · "
                         f"supports={v['supports_claim']} · numbers_match={v['numbers_match']}"
                         f" — {v['biggest_finding']}")
            L.append("")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    if args[0] == "apply":
        dry = "--dry" in args
        cmd_apply([a for a in args[1:] if a != "--dry"], dry)
    elif args[0] == "build":
        cmd_build()
    elif args[0] == "report":
        cmd_report()
    else:
        fail(f"ไม่รู้จักคำสั่ง {args[0]}")
