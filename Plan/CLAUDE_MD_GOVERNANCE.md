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

---

# R2 — CLAUDE.md consolidation pass (requirement ที่ 2 · วินสั่ง 2026-07-09)

> **สถานะ:** design draft · รอ Engineer-finding → Claude-Verify → วินอนุมัติ → implement
> **เป้าหมาย:** dup → canonical-home เดียว · **ไม่ลด reinforcement ที่ตั้งใจ** · **ไม่ไล่ตาม "สั้น" (cosmetic #10)** — วัดผลด้วย "ไม่มี concept หลุด coverage" ไม่ใช่จำนวนบรรทัด

## R2.0 Requirement (วิน)
CLAUDE.md โตแบบ accretion → `Working Rules` (list แบน 1-12) **ทับ section เฉพาะเรื่อง**ที่อยู่ถัดไป · R1 governance เพิ่ง add ทำให้ propose→gate ซ้ำเป็น **4 ที่**. จัดระเบียบ: **แต่ละ concept มี canonical home เดียว · ที่อื่น point หรือตัด** — โดย**แยก dup (รวมได้) ออกจาก reinforcement ตั้งใจ (คง)**

## R2.1 Inventory (evidence · current line หลัง R1)
| concept | ซ้ำอยู่ที่ |
|---|---|
| propose→gate / รออนุมัติ | CRITICAL:8 · Working Loop:14-17 · Rule 1:20 · 3-Phase Gate:59 = **4** |
| root-cause / ห้ามหลบ / workaround | Rule 5:24 · 6:25 · 8:27 · 8.1:28 (+ §Communication Engineer) |
| Engineer critical / full-scope | Rule 10:30 · 11:31 (+ §Communication) |
| evidence บังคับ | Rule 7:26 (+ §Honest Reporting) |

## R2.2 Proposed merges (conservative — targeted ไม่ wholesale)
1. **propose→gate 4→2:** canonical = **Working Loop** (flow ครบสุด) · **CRITICAL:8 คง** (source-ban เด็ดขาด = reinforcement) · **Rule 1 ตัด** (subsumed by Working Loop เต็ม) · **3-Phase Gate**: ย้าย "2-STOP review→STOP→verify→STOP cadence" เป็น sub-line ใน Working Loop · §Communication เก็บเฉพาะ Engineer/Verify protocol + Win-comms (จอจริง/reject-2×/InpXxx)
2. **root-cause 4→2:** รวม Rule 5+6 → 1 ข้อ ("diagnose root cause ก่อน fix · fix ไม่ work → หา WHY ก่อน ไม่ throw/ไม่ revert-ทิ้ง") · รวม Rule 8+8.1 → 1 ข้อ ("root cause vs workaround test · ห้ามหลบ — **คงตัวอย่าง 8.1: เพิ่มทุน/ข้ามวัน/หยุดเทรด/เพิ่มตัวแปรเลี่ยง**")
3. **Engineer Rule 10+11 → fold §Communication** (เจ้าของ Engineer-review/Claude-Verify protocol อยู่แล้ว) · ตัดออกจาก Working Rules list

## R2.3 KEEP — reinforcement ตั้งใจ (ห้ามรวม/ตัด)
- **CRITICAL:8** (source-edit ban · absolute)
- **Rule 8.1 substance** (หลักวิน 2026-07-03 · specific examples)
- **§Verify ≠ Self-grading ทั้ง section** (หัวใจ Stage 0)

## R2.4 DON'T merge — คนละ concept (Engineer P3/รอบ1 ยืนยันแล้ว)
- **Rule 2 (อ่าน production code ก่อน fix) ≠ §Verify (ห้าม self-grade sim)** — คนละชั้น
- **evidence (Rule 7) ≠ §Honest (honesty กว้าง)** — คง Rule 7 canonical

## R2.5 Open questions (Engineer ตอบ)
1. targeted merge (R2.2) พอ · หรือควร restructure ใหญ่ (Working Rules = **index-only** ชี้ section · detail ย้ายเข้า section ทั้งหมด)? อันไหน risk ต่ำกว่า
2. ยุบ 3-Phase Gate เข้า Working Loop → เสีย salience ของ "2-STOP" ที่ชัดไหม · หรือควรคง §แยก
3. merge ไหนใน R2.2 จริงๆ เป็น reinforcement (ต้องย้ายไป R2.3 KEEP)?
4. หลัง merge — มี concept ไหน**หลุด coverage**ไหม (checklist: propose-gate / root-cause / evidence / verify-code / Engineer / no-scope / glossary ยังครบ)?
5. R2 ควรทำ commit เดียวกับ R1 หรือแยก (R1 = guard · R2 = cleanup)?

## R2.6 Claude-Verify (post Engineer-finding · 2026-07-09)
Engineer 6 finding verify กับ CLAUDE.md จริง = **concede ทั้งหมด** (F1 label · F2 Rule11-KEEP · F3 Rule10-ไม่dup · F4 2-STOP · F5 8.1-principle · F6 :12-node). **Claude ไปลึกกว่า:**
- **หลังแก้ 5 จุด R2 แทบไม่เหลือ safe-merge:** propose-gate 4 ที่ (CRITICAL:8/Rule1/Working Loop/3-Phase) + Engineer 10/11 = **reinforcement ของวินัยที่พังบ่อยสุด ไม่ใช่ dup** → ไล่ตาม "ลดบรรทัด" = **cosmetic #10**
- **ค่าจริงของ R2 = แก้ contradiction ไม่ใช่ตัด:** `:16` Working Loop=**1-stop** ขัด `:59` 3-Phase=**2-stop** (defect จริง · session นี้ทำ 1-stop)

### R2' — revised scope (post-Verify · รอวินตัดสิน cadence)
1. **reconcile 1-stop/2-stop** ให้ตรงกัน + คง 2-STOP salience (bold · ไม่ยุบ sub-line) — **รอ D-R2**
2. **จัดกลุ่ม root-cause 5/6/8/8.1** ใต้หัวข้อเดียว **คงทุก clause + 8.1 principle** (readability · ไม่ตัด beat)
3. **ไม่แตะ Rule 1 / 10 / 11** (reinforcement · F2/F3 + propose-before-act)
4. **แยก commit จาก R1** (Q5 · R1 landed แล้ว · R2 = restructure blast-radius สูง)

### D-R2 — RESOLVED = **2-stop** (วิน 2026-07-09)
> เหตุผลวิน: 1-stop → ไม่มีการตรวจจริง/ไม่เข้ม → วินต้องสั่งตรวจซ้ำ = **ทำงาน 2 รอบ** · 2-stop คุ้มสุด
> **live rule:** requirement/bug → doc → Engineer-finding → **STOP (วินตรวจ finding)** → Claude-Verify → **STOP (วินอนุมัติ)** → implement

### R2'' — Option C (วินอนุมัติทิศทาง 2026-07-09 · ตามหลัก "ไม่ดรอปศักยภาพด้านใด")
A(reconcile only) vs B(reconcile+group+renumber) = **false trade-off** (A ดรอป consolidation · B ดรอป safety). **C แก้รากร่วม (by-number coupling) → ได้ทั้ง readability + safety:**
1. **แปลง by-number ref → by-name** (grep verified 2 จุด · ตัดความพัง renumber ถาวร · = Engineer F-G):
   - `CLAUDE.md:39` "(กฎข้อ 9)" → "(กฎ backtest-compare-metrics)"
   - `CLAUDE.md:67` "(Working Rule 7)" → "(กฎ evidence-required)"
2. **reconcile 1-stop→2-stop:** Working Loop เขียน 2-stop ชัด (Engineer-finding → **STOP วินตรวจ** → Claude-Verify → **STOP วินอนุมัติ** → implement) ให้ตรง 3-Phase Gate
3. **group root-cause 5/6/8/8.1:** ย้าย clause **verbatim** (ไม่ rewrite/บีบ) · คง 8.1 principle (engine ต้องเข้าใจสาเหตุ + risk-mgmt=เพดาน) เต็ม
4. **grep-verify (ด่านบังคับ):** ทุก clause + 8.1 principle ยังอยู่ · **0 by-number ref เหลือ** · markdown/รายการไม่พัง
5. **ไม่แตะ Rule 1/10/11** (reinforcement · F2/F3) · **แยก commit จาก R1**

**14-pattern กันได้ (แก้ราก+verify ไม่ใช่หลบ):** #5 (ลบ number-dependence → ไม่มี stale-ref ให้เกิด) · #6 (verbatim+grep → ไม่หดจากที่เคยครอบ) · #10 (correctness: by-name robust + contradiction fix ไม่ใช่ cosmetic) · #3 (เสนอก่อน) · #4 (แก้ราก ไม่ flip-flop)
**residual (ไม่ over-claim):** blast radius ใหญ่กว่า A → grep-verify ขั้น 4 = ด่านบังคับ

---

## หลักดีที่สุด — ไม่ดรอปศักยภาพด้านใด (governance principle · วิน 2026-07-09)
> ต่อยอด §Communication "Claude Verify → เห็นทางที่ดีกว่า (ไม่ดรอปศักยภาพ)" + Working Rule root-cause + No-Scope-Creep

"ดีที่สุด" = **ไม่ยอมเสียศักยภาพด้านใดเลย จนกว่าพิสูจน์ว่าเลี่ยงไม่ได้จริง** (ไม่ใช่เลือกตัวดีสุดในบรรดาที่มี):
1. **Trade-off = สัญญาณเตือน ไม่ใช่คำตอบ** — เจอ "A เสีย X / B เสีย Y" → ถือเป็น false dichotomy ก่อน (มักเสียคนละด้านของรากเดียวกัน)
2. **แก้รากร่วม = เก็บทั้ง 2 ด้าน** — หา C ที่กำจัดต้นเหตุที่บังคับให้ต้อง trade = root-cause-not-workaround ใช้กับการตัดสินใจเอง
3. **เลือกข้าง = ทางสุดท้าย + ต้องประกาศสิ่งที่เสีย** — พิสูจน์แล้วว่าไม่มี C จริง ค่อยเลือก · ห้ามกลบสิ่งที่ดรอป
4. **ห้ามยื่น trade-off เป็นคำตอบสุดท้ายโดยไม่ลองหา C ก่อน** — โยน A/B ให้วินโดยไม่หา C = ผลัก symptom-choice ให้วิน
5. **ไม่ใช่ข้ออ้างขยาย scope** — C ต้อง trace กลับ root ที่ report ได้ (ไม่งั้น = self-authorize #3)
6. **complexity-gate (เติมหลัง Engineer B#6):** เลือก C เฉพาะเมื่อ net-value > added-complexity/blast-radius ของ C เอง · **การ "ประกาศ residual" ไม่ใช่ใบอนุญาตเลือกทางซับซ้อน** · ถ้า potential ที่ C รักษา < ต้นทุน C → เลือกทางง่ายกว่า (นี่ = best ไม่ใช่ยอมแพ้)
7. **bounded-search + คืนสิทธิ์วิน (เติมหลัง B#7):** หลัง synthesis 1 รอบซื่อสัตย์ ถ้า C ต้อง rewrite เกินกรอบ/สร้าง coupling ใหม่ → เสนอ A vs C + cost ให้วินตัดสิน (requirement=วิน) · **ห้ามค้างหา C แทนการตัดสิน** (= อีกรูปของ deferred)
8. **subordinate + no self-grade (เติมหลัง B#8/B#9):** "ศักยภาพ" = ในกรอบ root/requirement ที่วิน report เท่านั้น (ใต้ No-Scope-Creep) · คำเคลม "C รักษาทั้ง 2 ด้าน" **ต้องผ่านตาปรปักษ์ (Engineer/วิน) ไม่ใช่ Claude ตีตราเอง** (§Verify≠Self-grading)

---

## R2.7 Claude-Verify รอบ 2 (post Engineer · 2026-07-09) — FINAL
Engineer 9 finding verify กับ grep จริง = **concede เกือบหมด** (A#1 scan-2-จริง-4 · A#2 slug-no-anchor · A#3 verbatim-ขัด · A#6 cross-file-stale · B#6/7/8/9). **Claude ยอมรับ:** over-claim "0 ref/ถาวร"(#2/#10) · self-grade "14-pattern กันได้"(#9) · Option C = over-engineer ใต้ธง no-drop (พิสูจน์ B#6)
- **refine Engineer (A#1):** `:12`(14-pattern)/`:90`(Doctrine) อยู่คนละ list — ไม่ break จาก C's renumber (fragility แฝง ไม่ใช่ C พลาดต้องแปลง) · แต่ "ตัดถาวร" ผมผิดอยู่ดี
- **ลึกกว่า Engineer:** anchor-tag ที่ Engineer เสนอ **ก็ตก complexity-gate (clause 6)** — เพิ่ม tag ~12 rule + fix ~15 ref เพื่อ readability nit = ไม่คุ้ม

### R2 FINAL (รอวินอนุมัติ = stop ที่ 2)
1. **ทำ step 2 เท่านั้น:** reconcile Working Loop → 2-stop ให้ตรง 3-Phase Gate (defect จริง · zero renumber · high-value)
2. **ดรอป step 1+3 (group root-cause):** complexity-gate ตัดสิน — potential เล็ก · ทุกวิธีปลอดภัย ต้นทุน>ค่า · scatter อยู่ต่อ (ไม่ใช่หลบ · เป็นดุลพินิจ evidence-based)
3. **mark GOVERNANCE:93 (R2.2 merge→1) SUPERSEDED by R2 FINAL** (A#3 doc-hygiene)
4. **แยก commit จาก R1**
> superseded: R2''(:127) by-name+group, R2.2:93 merge-5+6 → ทั้งคู่ทิ้ง (ตก complexity-gate) · เหลือ reconcile อย่างเดียว

### R3 — principle เข้า CLAUDE.md (วินสั่ง 2026-07-09)
**Claude เห็นต่าง (attach):** 8 clause เต็มใน CLAUDE.md = ยาว โหลดทุก turn → **ตก complexity-gate เอง** · เสนอ **compact essence + pointer** (แบบ R1 split: full-8 อยู่ doc · CLAUDE.md เก็บ essence)

**compact ที่จะแทรก (วางหลัง §No Scope Creep — interact กับ scope+complexity):**
```markdown
## ⚖️ หลักดีที่สุด — ไม่ดรอปศักยภาพด้านใด
> 8 clause เต็ม → `Plan/CLAUDE_MD_GOVERNANCE.md → ## หลักดีที่สุด`
- trade-off (A เสีย X / B เสีย Y) = สัญญาณ false-dichotomy → หา **C ที่แก้รากร่วม** (root-cause กับการตัดสินใจ ไม่ใช่แค่โค้ด)
- **complexity-gate:** เลือก C เฉพาะเมื่อ net-value > ต้นทุน/blast · "ประกาศ residual" ≠ ใบอนุญาตเลือกทางซับซ้อน · potential เล็ก+ต้นทุนสูง → **เลือกทางง่ายได้ก็ต่อเมื่อประกาศสิ่งที่ดรอป** (เลือกง่ายแบบเงียบ = ไม่อนุญาต · best ไม่ใช่ยอมแพ้/ไม่ใช่กลบ)
- หา C ไม่ได้ใน 1 รอบซื่อสัตย์ → เสนอ A vs C + cost ให้วิน (requirement=วิน) · ห้ามค้าง search แทนตัดสิน
- "ศักยภาพ" = ในกรอบ root ที่ report (ใต้ No-Scope) · เคลม "C รักษาทั้ง 2 ด้าน" ต้องผ่านตาปรปักษ์ ไม่ใช่ตีตราเอง (§Verify≠Self-grading)
```
> **Verify รอบ 3 (post Engineer):** B#2 คืน clause 3 **ผูกเข้า bullet complexity-gate** (license+counterweight เดินคู่ · กัน asymmetric-compression ซ้ำ) · B#1 pointer เติม section anchor · B#3 reconcile เติม cross-ref 3-Phase · **B#4 (ใหม่): §Communication:66 "(ไม่ดรอปศักยภาพ)" → เติม "→ §หลักดีที่สุด"** (single home · Rule 3) → **แตะ CLAUDE.md เป็น 3 จุด** (reconcile + compact + seed-pointer)

**R2+R3 FINAL — แตะ CLAUDE.md 2 จุด:** (a) reconcile Working Loop→2-stop (step 2) · (b) แทรก compact principle หลัง §No-Scope · แยก commit จาก R1 · **รอ Engineer + Verify + วินอนุมัติ**

---

# Concision — Implementation Plan (before/after · CLAUDE.md · post 8-round Engineer+Verify)

> เป้า: กระชับ (ตัด noise) ไม่เสียความหมาย/reinforcement · **ไฟล์เดียว: CLAUDE.md** · reconcile 2-stop = แยก (วินยังไม่ตัดสิน)

## A. ตัด process-date (คง "บทเรียน:" label + example + fact)
| line | ตัด | เก็บ |
|---|---|---|
| L12 | "2026-07-09" | "canary-verified" |
| L28 | "2026-07-03" | "(หลักวิน)" |
| L62 | "2026-07-03" | "(บทเรียน: ตีความ 'เร่งพัฒนา' ผิดจนโดน interrupt)" |
| L63 | "2026-07-03" | "(บทเรียน):" |
| L96 | ทั้ง "(บทเรียน 2026-07-03: 2025 sim +207/tester −169)" | กฎนามธรรม (เลข = bug-artifact resolved+เด้ง · caveated home ที่ LEDGER:36/workflow:141) |
| L104 | "— บทเรียน 2026-06-29" | "(บังคับ)" |
| **L97, L108** | **ไม่แตะ** | ไม่มี process-date · L108 ธ.ค.2025/ก.พ.2026 = data-coverage fact |

## B. ย่อ 2 บรรทัดยักษ์ (คง nuance ทุกตัว)
- **L86** (587ตัว): ตัด date "C7 2026-07-05" + "runner เก็บ t[i]" · **คง:** นิยาม signal-j≠exec-i · as-of ≤ close bar j · within-bar lookahead · j=index(i)−1 ใน bar-series เดียวกับ sim · (missing bar ทำเลื่อน) · pin คำสองความหมาย
- **L109** (598ตัว): ตัด "Dukascopy-converted"/"last Sun Mar/Oct"/"ก.พ.ฤดูร้อนสองกฎเท่ากัน"/date · **คง:** EET +2/+3 EU-DST(ไม่ใช่ US) · shoulder-week proof · HourShift=-1 AUTO IsEuDST · tester=0 · verify first-epoch ก่อน import · pointer → `TRELLIS-010_brain_research_workflow.md` Stage 0 (heading จริง)

## C. principle → verify (section ใหม่ + pointer)
- **L66:** "(ไม่ดรอปศักยภาพ)" → "(ไม่ดรอปศักยภาพ → §หลักดีที่สุด)"
- **แทรกหลัง L80 (ก่อน §Authority):** section "## ⚖️ หลักดีที่สุด" = copy `GOVERNANCE:176-179` **verbatim** (bold ครบ) · L174 draft ไม่ rename (อยู่ใน fence · pointer resolve L142)

## D. ไม่ merge พฤติกรรม (reinforcement)

## Net (ซื่อสัตย์)
แก้ 9 บรรทัด + section ~6 · char/noise ลดเยอะ · **line-count +~6 (ไม่ใช่ line-cut)** — วัดด้วย "ไม่มี concept หลุด" ไม่ใช่จำนวนบรรทัด
