# CLAUDE.md Governance — Working Loop + Anti-Appearance-of-Done Guard

> **สถานะ:** design **v4** (post Engineer-finding รอบ 2 + Claude-Verify) · **รอวินอนุมัติ → implement (มี canary gate บังคับกลางทาง)**
> **ยังไม่แตะ `CLAUDE.md` / `settings.local.json` จนวินอนุมัติ**

---

## 0. Requirement (วินเป็นเจ้าของ)
encode 2 อย่าง กัน 14 failure pattern (`feedback-no-appearance-of-done`) + Working Loop เข้าเครื่องมือที่ถูกชั้น:
1. **Working Loop** — ไม่มีปัญหา→ไม่เปิด issue · requirement/bug→doc→Engineer→Verify→อนุมัติ→implement · งานเล็ก→ไม่สร้าง doc (ลดค่าใช้จ่าย)
2. **pre-send checklist (14-pattern)** — กัน "ทำให้ดูเหมือนเสร็จ แทนทำถูกจริง"

## 1. Root cause + ทำไม architecture นี้ (post-Verify รอบ 2)
- **premise-gap (Engineer F3 · verify แล้ว):** §Honest/§No-Scope/§Verify โหลดทุก turn**อยู่แล้ว** แต่ 14 pattern ยังเกิด → **prose ≠ เขี้ยว**. การเพิ่ม prose ชั้นที่ 6 = salience ไม่ใช่ enforcement
- **hook = เขี้ยว · PROVEN ใช้ได้บน client นี้ (in-session evidence · หักล้าง Engineer F-A):** turn ก่อนๆ ที่ Edit/Write → ระบบ inject `additionalContext` จาก `settings.local.json:10` กลับมาหา model จริง 6 ครั้ง (verbatim "GATE...") → **PreToolUse additionalContext ทำงาน ณ 2026-07-09** (Issue #15664 Dec2025 = outdated/merged) · hook เดิมครอบแค่ตอนแก้ไฟล์ ไม่ครอบ text-turn (พูด/claim)
- **วินเลือก D1(b):** เพิ่ม `UserPromptSubmit` hook (ยิงทุก user turn) → checklist มีเขี้ยว + ครอบ text-turn
- **⚠️ ความเสี่ยงเปิด (Engineer F-B · ยังไม่หักล้าง):** UserPromptSubmit `additionalContext` **พังใน VSCode/Cursor extension บน Win11** (Issue #49063 · closed-not-planned) · PreToolUse ทำงาน ≠ การันตี UserPromptSubmit (คนละ path) · env นี้ = "official CLI" (เคสที่ #49063 บอกว่าทำงาน → เสี่ยงต่ำ) **แต่ต้อง canary-verify ก่อนเชื่อ (F-C)** — pipe-test เช็คแค่ JSON valid ไม่เช็ค inject จริง
- **บทเรียน fortress (วินแก้ 2026-07-09):** แผน HMAC-fortress ตกเพราะ **ไม่ยืดหยุ่น + บังคับวินสร้าง key ทุกครั้ง** (Claude ตอนนั้นไม่เข้าใจภาระวิน) — **ไม่ใช่แค่ "หนัก"**. hook นี้ต่างสิ้นเชิง: **ภาระวิน = 0** (echo บรรทัดเดียว · ไม่มี key/state/HMAC)

## 2. Design v3 — split architecture (เขี้ยวที่ hook · doctrine ที่ CLAUDE.md · ไม่ dup)

### 2a. Hook — `settings.local.json` เพิ่ม `UserPromptSubmit` (merge · ไม่แตะ PreToolUse เดิม)
```json
"UserPromptSubmit": [
  { "hooks": [ {
    "type": "command", "shell": "bash", "timeout": 5,
    "command": "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"PRE-SEND GATE (ทุก turn): (1) act เมื่อมีคำสั่งงานชัด · teaching/ถาม=ตอบด้วยคำ ไม่รัน/ไม่แก้ (2) ห้าม ถูก/ครบ/เสร็จ/PASS ถ้าไม่มี output รันจริงแนบ · coverage=grep/run · verify crash=ยังไม่ verify (3) ไม่ over-claim/cosmetic(สั้นลง)/steer(เริ่มต่อไหม)/self-authorize scope (4) fix=เฉพาะ fact ที่โดนแก้(ไม่ flip-flop)·ไม่สร้าง bug ใหม่(แก้ให้ครบเหตุ)·scan ครบ·ไม่หดจากที่เคยครอบ (5) deliverable=คำสั่ง+ผลดิบ ไม่มี apology/process-noise/fake-jargon/ประกาศใกล้จบทั้งที่มี bug. Working Loop: requirement/bug->doc->Engineer->Verify->อนุมัติ->implement · งานเล็ก->ข้าม doc ได้ แต่ approval+แตะ source บังคับขอเสมอ · ลังเล=ไม่เล็ก\"}}'"
  } ] }
]
```
- **14-pattern coverage:** #1(1) #2/#10(3) #3/#13(3) #4/#5/#6(4) #7/#8(2) #11/#12/#14(5) = 13/14 · **#9 rubber-stamp** → คงที่ CLAUDE.md Rule 11 + §Comm:58 + §Verify:83
- **verify ก่อน implement:** ต้อง pipe-test `echo '{}' | <command>` ให้ออก JSON ถูก (bash · escape ครบ) ก่อนใส่จริง

### 2b. CLAUDE.md — section สั้น (Working Loop + pointer · ~6 บรรทัด) วางหลัง `## CRITICAL RULES`
```markdown
## ⛔ Working Loop + Anti-Appearance-of-Done (บังคับ)
> pre-send checklist (14-pattern) = hook `settings.local.json` UserPromptSubmit inject ทุก turn (เขี้ยว) · ราก+why = memory `feedback-no-appearance-of-done`

**Working Loop:**
- ไม่มีปัญหา → ไม่เปิด issue / ไม่ปั้นงาน
- requirement ใหม่ | bug → doc(`Plan/`)/`Issue/` → Engineer-finding → Claude-Verify (แผนไม่เคยสมบูรณ์) → **รอวินอนุมัติ** → implement
- fix เล็ก (reversible + ไม่มี design-choice + verify ทันที + ไม่กระทบ scope อื่น · **ลังเล = ไม่เล็ก**) → ข้ามได้แค่ doc+Engineer round · **approval + แตะ .mq5/.mqh/source ยังบังคับขอเสมอ (ไม่ override CRITICAL)**
```

## 3. ทำไม split (ไม่ใส่ checklist ทั้ง 2 ที่)
- **ไม่ dup (Engineer F2):** checklist อยู่ที่ hook ที่เดียว (เขี้ยว) · CLAUDE.md ชี้ไป ไม่ restate → ไม่ละเมิด Working Rule 3
- **แต่ละชั้นทำสิ่งที่ถนัด:** hook=enforcement (teeth+text-turn) · CLAUDE.md=Working Loop (committed doctrine ต้อง shared/persistent · hook gitignored)
- **CLAUDE.md โต ~6 ไม่ใช่ 13** (แก้ D2 net-add)
- **ข้อแลก (ซื่อสัตย์):** checklist อยู่ใน `settings.local.json` ที่ **gitignored** → clone ใหม่ไม่มี · แต่ content ไม่หาย: (a) memory `feedback-no-appearance-of-done` (ราก) (b) doc นี้ (committed) (c) CLAUDE.md pointer

## 4. การตัดสินที่ปิดแล้ว
- **D1:** ✅ hook `UserPromptSubmit` (วินเลือก) — ภาระวิน 0
- **D2:** ✅ split → CLAUDE.md +~6 (ไม่ 13)

## 5. Out-of-scope (log แยก · ไม่แตะ)
CLAUDE.md §Subagent tree (L161-173) file-map + L164/L175/L178 grid-stale

## 6. Implementation order (หลังอนุมัติ · verify-as-I-go · canary gate บังคับ)
1. **pipe-test:** `echo '{}' | bash -c '<cmd>'` → ต้องได้ JSON valid · validate ด้วย **`python -c "import sys,json;json.load(sys.stdin)"`** (ไม่มี jq บนเครื่อง — Engineer F-E)
2. merge UserPromptSubmit เข้า `settings.local.json` (read-first · ไม่แตะ PreToolUse เดิม) **พร้อม canary token** `CANARY_UPS_7f3a` ท้าย additionalContext
3. **🔴 CANARY GATE (Engineer F-C · บังคับก่อนเชื่อว่ามีเกราะ):** วิน `/hooks` reload → ส่ง prompt เปล่า 1 turn → ผมตอบว่าเห็น `CANARY_UPS_7f3a` ใน context turn นั้นไหม
   - **เห็น** = UserPromptSubmit inject จริงบน client วิน (หักล้าง F-B) → ลบ canary → ไปข้อ 4
   - **ไม่เห็น** = F-B จริง (extension bug) → **หยุด ไม่ ship เกราะปลอม** → เปลี่ยน architecture (ลอง SessionStart / หรือ prose-only + PreToolUse ที่ proven)
4. แทรก section 2b เข้า CLAUDE.md **หลัง `## CRITICAL RULES`** · อ้าง cross-ref ด้วย**ชื่อ section** (Working Rule "ตรวจ Engineer critical" · §Communication Claude-Verify · §Verify≠Self-grading) **ไม่ใช่เลขบรรทัด** (Engineer F-G · `CLAUDE.md:76` ห้ามอ้างเลขจากความจำ · แทรก section = เลขเลื่อน)
5. **F-D (หลัง canary ผ่าน · เสนอวิน):** พิจารณาย้าย UserPromptSubmit เข้า committed `.claude/settings.json` → teeth เข้า version control (clone ใหม่มีเกราะ) · **แต่ commit เฉพาะหลัง canary ยืนยัน** (commit hook ที่ inject ไม่ออก = commit no-op หลอกว่ามีเกราะ)
6. รายงานวิน (ไม่ commit จนสั่ง)

## 7. Residual gaps + costs (ซื่อสัตย์ · ไม่กลบ — Engineer F-I + token)
- **#9 rubber-stamp** อยู่ prose (Rule 11 + §Comm + §Verify) = **salience ไม่มีเขี้ยว** · encode ยาก → **ยอมรับเป็น residual gap** ไม่ใช่ "coverage ครบ 14"
- **token cost:** additionalContext ~1.1k อักษร inject **ทุก user turn ตลอดไป** — ต้นทุนจริง · ถ้าวินห่วง cost → SessionStart (inject 1 ครั้ง/session · ถูกกว่า · แต่อาจ dilute ใน session ยาว) เป็นทางเลือก
- **no heartbeat:** ถ้า client update แล้ว UserPromptSubmit พังภายหลัง = เกราะหายเงียบ · canary เป็น one-time ไม่ใช่ต่อเนื่อง (heartbeat = over-engineer · ไม่ทำ · แต่ re-canary ถ้าสงสัย)
