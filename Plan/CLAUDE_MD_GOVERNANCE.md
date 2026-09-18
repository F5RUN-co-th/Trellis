# CLAUDE.md Governance — Working Loop + Anti-Appearance-of-Done Guard

> **สถานะ: ✅ IMPLEMENTED ครบทุก requirement (R1+R2+R3+Concision · 2026-07-10)** — R1: hook UserPromptSubmit live + canary-verified (inject ยืนยันทุก turn) + CLAUDE.md Working Loop section (commit `869e668`) · R2+R3+Concision: 2-STOP reconcile + §หลักดีที่สุด compact + strip dates (commit `cfe48e4` · Engineer PASS 07-10) · doc นี้ = design history
> ~~ยังไม่แตะ `CLAUDE.md` / `settings.local.json` จนวินอนุมัติ~~ (อนุมัติ+ทำแล้ว)

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

---

# R4 — Governance upgrade: นำวินัยจาก eAuction.Lab + erfx.be เข้า Trellis (วินตัดสิน 2026-09-18 · พร้อม Engineer review)

> ขอบเขต: **CLAUDE.md · `.claude/agents/mql5-ea-engineer.md` · `.claude/commands/mql5-ea-engineer.md` · memory · ไฟล์นี้** — ไม่แตะ `.mq5/.mqh`, script, LEDGER, card
>
> **Guard (อ่านก่อนใช้ §R4 อ้างอิง):**
> 1. R4 = **implementation plan + decision record ไม่ใช่ runtime authority** · ไฟล์นี้ไม่ถูกโหลดเป็น instruction (R4.1(3))
> 2. กฎที่มีผลจริงตัดสินจาก **Authority Map (§R4.2)** — CLAUDE.md (กฎ Claude) · agent file (protocol Engineer) · STATUS (stage) · LEDGER (ผล) ไม่ใช่เอกสารแผนนี้
> 3. ข้อความใน **§R4.4 = draft สำหรับ implement ยังไม่มีผลบังคับ** จนผ่าน Engineer → Claude-Verify → วินอนุมัติ → เขียนลงไฟล์ canonical

## R4.0 Decision ที่วิน freeze (2026-09-18)
| # | Decision |
|---|---|
| W1-c | Material revision → Engineer review **เฉพาะขอบเขตที่เปลี่ยน + ผลกระทบของมัน** ไม่ reopen ส่วนที่ไม่ได้รับผลกระทบ · ปรับ `CLAUDE.md:16` ให้ไม่ขัด โดยไม่สร้าง review loop ใหม่ |
| W2-a | ข้อเสนอต้องระบุ trade-off / limitation ที่มีสาระต่อการตัดสินใจ · ไม่บังคับเขียน "ไม่มีข้อเสีย" · **แก้ agent `:41` ให้ใช้ถ้อยคำเดียวกัน** (ไม่ลงทะเบียนเป็นความต่างที่ตั้งใจ) |
| W3 | B5 = experimental control เท่านั้น ลงทะเบียนในไฟล์นี้ (trigger / scope / cost / evidence / adopt-drop) ไม่เป็นกฎบังคับ |
| B3 = (ง) | Material → Engineer · Non-material → Claude-Verify · ลังเล = Material |
| B1 = (ข) | Issue/script/EA defect → Root Cause Trace + class A/B/C · card round → class-tag เท่านั้น |
| P4 | รับ B2 · B4 · B6 · B7 · B8 (B5 = experimental) |
| M | M1 ✓ · M2a = **Preference** (ใช้เฉพาะข้อสรุปที่มีสาระ) · M2b ✓ · M3a ✓ · M3b ✓ · M4 ✓ · **M5b = ยังไม่ canonicalize** (Engineer ตรวจ semantic ก่อน) · M5c = ไม่ย้าย (ซ้อน doctrine เดิม) · M6 ✓ · M7 ✓ |
| Authority | one fact type → one authority · conflict ต้อง surface ก่อน ห้ามตัดสินเงียบ · authority ≠ ความจริงที่เปลี่ยนไม่ได้ |
| P6 | Consistency & Behavior Validation · behavior = **Behavior Observation** (non-blocking evidence) |

## R4.1 Evidence base (วัดแล้ว — ห้าม re-derive จากความจำ)

**(1) Probe บริบทของ subagent (2026-09-17 · no-tool probe · ทั้ง 3 agent รายงาน tool_uses = 0)**
ถามข้อเท็จจริงที่ grep ยืนยันตำแหน่งแล้ว: `TRL` (`CLAUDE.md:183`) · `HourShift=-1` (`:133`) · ตัวอย่างใน Rule 8.1 (`:28`) · erfx 04-21 = safe.directory (Rule 13) · EchoSeven + tick-data Gloo/Data 2011–2026 (อยู่ใน `MEMORY.md` index เท่านั้น)

| agent | บล็อก "Contents of" ที่ได้รับ | ตอบข้อเท็จจริงได้ |
|---|---|---|
| Explore | **ไม่มีเลย** | NOT IN CONTEXT ทุกข้อ |
| general-purpose | CLAUDE.md + MEMORY.md | ถูกทุกข้อ |
| mql5-ea-engineer | CLAUDE.md + MEMORY.md | ถูกทุกข้อ |

- **Supported:** Explore ไม่ได้รับกฎของโปรเจกต์ · subagent ที่ได้รับ memory ได้เฉพาะ **index** ไม่ใช่เนื้อไฟล์
- **Not-yet-supported:** รัน 1 ครั้งใน 1 session = พฤติกรรมที่วัดได้ ไม่ใช่สัญญาของ harness · ไม่ได้ทดสอบ Plan และ fork · ห้ามพึ่ง memory index เป็นช่องทางส่งกฎ

**(2) Audit memory (อ่านครบ 13 ไฟล์ `feedback-*`)**
- กฎที่อยู่ใน **memory อย่างเดียว**: M1 (บางส่วน — ดูต่อ) · M2a · M2b · M3b · M4 · M5a/M5b/M5c
- กฎที่ **canonical อยู่ที่ agent ไม่ใช่ memory**: M3a (agent `:63-64`) — memory เก็บ incident (tick_volume) · *[F22 correction 2026-09-18: เดิมจัด M3a ไว้ใต้หัว "memory อย่างเดียว" ซึ่งขัดกันเอง]*
- กฎที่มีสาระอยู่ใน **hook แล้ว**: M1 — `settings.local.json:22` ข้อ (5) "ask กำกวม/ไม่เล็ก → พูดความเข้าใจ 1 บรรทัด รอ confirm" (grep = 1) → ต้องลงทะเบียนซ้ำ ไม่ใช่สร้างบ้านที่ 3 *[F12]*
- ซ้ำกับ CLAUDE.md 5 ไฟล์: `honest-reporting` · `no-scope-creep` · `root-cause-not-workaround` · `verify-independence` · `tool-selection`
- **`measurement-discipline` ไม่ใช่ไฟล์ซ้ำ** — เป็น **บ้านเดียว** ของ M2a/M2b (ส่วนอื่นในไฟล์ประกาศเองว่าย้ายเข้า CLAUDE.md แล้ว) → action "Dup → เหลือ why + pointer" **ห้ามใช้กับไฟล์นี้แบบเหมารวม** *[F22]*
- ข้อความล้าสมัย/ผิดซ้ำกับ R1/R3: `feedback-no-scope-creep` ("log issue แยก") · `feedback-tool-selection` ("Explore วิเคราะห์ log")
- frontmatter `type: reference` ทั้งที่ชื่อไฟล์เป็น feedback: `feedback-memory-governance` · `feedback-tool-selection`

**(3) สถานะการโหลดของไฟล์นี้ (ตรวจ 2026-09-18 ตามคำสั่งวินข้อ 8)**
`grep "^@\|@\." CLAUDE.md` = ไม่มี import · ไม่มี `~/.claude/CLAUDE.md` → **ไฟล์นี้ไม่ถูกโหลดเป็น runtime instruction** เข้าถึงได้ผ่าน pointer `CLAUDE.md:95` และ agent `:121` เท่านั้น
→ **ผลต่อ M6/M7:** กฎต้องมี clause สั้นใน CLAUDE.md · ฉบับเต็มอยู่ที่ไฟล์นี้

**(4) ขนาด** — ก่อนแก้: `CLAUDE.md` = 24,626 ตัวอักษร · 213 บรรทัด
**(5) ต้นทุนที่วัดแล้ว (2026-09-18 · แทนข้อความเดิมที่เขียนว่า "ประมาณล่วงหน้าไม่ได้" — F10):** ข้อความร่างใน §R4.4 = **7,194 chars** · AM block (§R4.2) = **1,365 chars** → **gross 8,559 chars = +34.8%** ของ 24,626 (Engineer วัดช่วงแคบกว่าได้ 7,614 = 30.9% · ต่างกันที่ขอบช่วง)
- **gross ≠ net:** ยังไม่หัก (ก) เครื่องหมาย `> ` ของ blockquote ที่ไม่ลงไฟล์จริง (ข) บรรทัดที่เป็น **การแทนที่** ไม่ใช่การเพิ่ม (R1 แทน `:89` · R3 แทน `:33-34` · W1-c แก้ในบรรทัด `:16`) → **net ต้องวัดตอนร่างข้อความสุดท้าย ก่อนเสนอวินอนุมัติ**
- **complexity-gate (`CLAUDE.md:97`) ใช้แบบมีกลไก:** ทุกรายการใน §R4.3 ต้องมีช่อง cost (chars ที่เพิ่ม/แทน) + สิ่งที่ดรอปถ้าไม่ทำ · รายการที่ cost สูงและ potential เล็ก → เลือกทางที่เล็กกว่าพร้อมประกาศสิ่งที่ดรอป (ไม่เงียบ)

## R4.2 Authority Map (canonical: `CLAUDE.md` §Authority Order)
**หลัก 3 ข้อ:** (ก) หนึ่งชนิด fact → หนึ่ง authority (ข) sources ขัดกัน = surface ก่อน ห้ามตัดสินเงียบ (ค) การเป็น authority ไม่ได้แปลว่า fact นั้นเปลี่ยนไม่ได้

| ชนิด fact / คำสั่ง | Authority | เมื่อขัดกัน |
|---|---|---|
| requirement / decision | คำสั่ง explicit ปัจจุบันของวิน | ตามลำดับที่ `CLAUDE.md` §Authority (คงเดิม) |
| กฎการทำงานของ Claude + doctrine | `CLAUDE.md` | agent / command / memory / hook ที่ขัด = ตัวนั้นผิด ต้องแก้ตาม |
| protocol + report shape ของ Engineer | agent file | ต้องไม่ขัด CLAUDE.md ถ้าขัด CLAUDE.md ชนะ |
| stage / build | `.claude/status/STATUS.md` | — |
| ผลวิจัย | `Plan/TRELLIS-010_LEDGER.md` (claim frozen · verified-by) | วัดใหม่ได้ต่าง → รายงาน + annotate/supersede **ห้าม overwrite เงียบ และห้ามกลบผลใหม่** |
| บทเรียน / เหตุการณ์ / reference | memory | **ไม่มีอำนาจเหนือกฎ** ขัดกัน = memory คือตัวที่ต้องแก้ |

**ทะเบียนการซ้ำที่ตั้งใจ (ตรวจทุกครั้งที่กฎ canonical เปลี่ยน):**
| ที่ซ้ำ | ซ้ำอะไร | เหตุผล |
|---|---|---|
| hook `UserPromptSubmit` (`settings.local.json`) | pre-send checklist 14-pattern + Working Loop + gate signal | เขี้ยวที่ inject ทุก turn (R2.3 KEEP) — ต้องตรงกับ canonical |
| hook `PreToolUse` | gate ก่อน Edit/Write | เหมือนกัน |
| memory `feedback-no-appearance-of-done` | ราก + why ของ checklist | pointer จาก `CLAUDE.md:12` |
| hook `UserPromptSubmit` ข้อ (5) | สาระของ **M1** (คำกำกวม → พูดความเข้าใจ รอ confirm) | มีอยู่ก่อนแล้ว (`settings.local.json:22`) → M1 ใน CLAUDE.md = ต่อบรรทัดเดิม `:67` ไม่สร้าง bullet ใหม่ · ต้อง sync ถ้อยคำ *[F12]* |
| `commands/ledger.md` CLAIM schema (`:36`) | field `supported` / `not-yet-supported` = กลไกของ **M2a** ในงาน LEDGER | M2a ใน CLAUDE.md = **pointer ไป schema** + ระบุ scope (ข้อสรุปในแชท/doc ที่ยังไม่เป็น claim) ไม่ใช่กฎซ้ำ *[F13]* |
| agent — safety essence 1 บรรทัด | สาระของ §EA/Gold Doctrine (ไม่ใช่สำเนา 5 ข้อ) | agent ต้องไม่พึ่ง injection ล้วนสำหรับ safety · ดู R4.9 §R2-revised *[F14]* |

## R4.3 รายการงาน (Problem / Evidence / Change / Acceptance criteria)

### P1 — defect ที่ยืนยันแล้ว
| ID | Problem | Evidence | Change | Acceptance criteria |
|---|---|---|---|---|
| R1 | กฎ out-of-scope เป็นฉบับที่ต้นทาง erfx แก้ไปแล้ว 3 รอบ | `CLAUDE.md:89` · memory `feedback-no-scope-creep` | ข้อความ §R4.4 R1 | `grep "log เป็น issue แยก"` = 0 ทุกไฟล์ · กฎอยู่ 1 ที่ · memory เหลือ why + pointer |
| R2 | EA/Gold Doctrine อยู่ใน agent เป็น **สำเนาย่อที่ตัด nuance** (ไม่ใช่สำเนาตรง) | `diff` agent `:86-90` vs `CLAUDE.md:47-51` (รัน 2026-09-18) = **ต่าง 4/5 ข้อ** เช่น agent เขียน "worst-case ทะลุเพดาน" แต่ canonical เขียน "ออกแบบโดยถือว่า worst-case > เพดานที่ตั้งไว้" · cite เดิม `:85-91` ผิด (`:90` = grid pointer · `:91` = บรรทัดว่าง) — F14 | agent = **pointer + safety essence 1 บรรทัด** (ดู R4.9 §R2-revised) ไม่ใช่ทั้งสำเนาเดิมและไม่ใช่ pointer เปล่า | ข้อความ doctrine 5 ข้อฉบับเต็มอยู่ที่ CLAUDE.md ที่เดียว · agent มี essence + pointer และลงทะเบียนซ้ำที่ตั้งใจ |
| R3 | Rule 12 มอบงานวิเคราะห์ log ให้ Explore ที่ไม่ได้รับกฎ | R4.1(1) · `CLAUDE.md:33-34` · memory `feedback-tool-selection` | ข้อความ §R4.4 R3 | Rule 12 ไม่มีคำสั่งให้ Explore วิเคราะห์/นับ · memory ชี้มาที่ Rule 12 · re-probe ใน session ใหม่หลังแก้ |

### P2 — Decision → กฎ
| ID | Change | ที่วาง | Acceptance criteria |
|---|---|---|---|
| B3 | Gate state (Material → Engineer scoped · Non-material → Claude-Verify) | `CLAUDE.md:68` §Communication | แต่ละสถานะมี 1 ทางไปต่อ · agent/command เป็น pointer |
| W1-c | ปรับ `CLAUDE.md:16` ให้ชี้ Gate state | Working Loop | อ่าน `:16` คู่ `:68` ไม่ขัดกัน · ไม่มีถ้อยคำที่เปิดรอบใหม่เพื่อหาความไม่สมบูรณ์ |
| B2 | นิยาม Material + Tag ของ finding | CLAUDE.md (นิยาม) · agent (field) | นิยามอยู่ 1 ที่ · report shape มี Tag + Material |
| B1 | Root Cause Trace + class A/B/C · card = class-tag | Working Loop · agent §1 | ข้อความระบุขอบเขต card ชัด · agent ตรงกัน |

### P3 — preventive ที่รับ
| ID | Change | ที่วาง |
|---|---|---|
| B6 | ข้ออ้างเชิงไม่มี ต้องมี 4 องค์ประกอบ | Rule 7 |
| B4 | exit code ที่ผ่าน pipe ไม่ใช่ exit ของคำสั่ง | §Verify≠Self-grading |
| B7 | trade-off / limitation ที่มีสาระ (+ แก้ agent `:41`) | §หลักดีที่สุด + agent |
| B8 | กติกา brief Engineer | ต่อ Rule 10 |

### P4 — ย้ายกฎที่อยู่แค่ใน memory
| ID | ประเภท | ปลายทาง |
|---|---|---|
| M1 | Rule | CLAUDE.md §Communication |
| M2a | **Preference** | CLAUDE.md §Verify≠Self-grading — เขียนเป็น **pointer ไป CLAIM schema** (`ledger.md:36` field `supported`/`not-yet-supported`) + ระบุ scope ว่าใช้กับข้อสรุปที่ยังไม่เป็น claim *[F13]* |
| M2b | Rule | CLAUDE.md §Verify · pointer ที่ agent **`:57`** (criteria orthogonal ไม่ nested) — **ไม่ใช่ `:58` ซึ่งเป็น lockbox/guard** *[F1]* |
| M3a | Rule | CLAUDE.md §Verify (canonical) · agent **`:63-64`** = pointer — **ไม่รวม `:65` ซึ่งเป็น same-commit DoD** *[F1]* |
| M3b | Rule | ต่อ Rule 8.1 |
| M4 | Rule | CLAUDE.md clause เอกสาร enduring |
| M5a | Rule | ต่อ Rule 8.1 |
| M5b | **ค้าง** | ไม่ย้ายจน Engineer ตรวจ semantic (R4.6) |
| M5c | ไม่ย้าย | ซ้อน Doctrine #1 |
| M6 · M7 | Rule (meta) | ฉบับเต็ม = ไฟล์นี้ + clause สั้นใน CLAUDE.md (เพราะไฟล์นี้ไม่ถูกโหลด — R4.1(3)) |

**pattern ของการ fold (ห้ามให้ rationale หายตอนย้าย):** CLAUDE.md = **กฎสั้นที่ปฏิบัติได้** · memory = **why + incident ที่ทำให้เกิดกฎ** (ไม่ copy ทั้ง paragraph ขึ้น CLAUDE.md และไม่ลบ incident ออกจาก memory) · ตัวอย่างที่ต้องระวังเป็นพิเศษ: **M2b** (incident TP-1 / ES-1 / ES-2 · nested criteria 3 ครั้ง) · **M3a** (incident tick_volume = un-enumerated frame boundary) · **M4** (incident insight ที่หายจากการ Write ทับ) — ทั้งสามข้อ ถ้าเหลือแต่ประโยคกฎจะอ่านไม่ออกว่าทำไมต้องมี

### P5 — ลดสิ่งที่จะล้าสมัย
| ID | Change | Acceptance criteria |
|---|---|---|
| AM | Authority Map + ทะเบียนการซ้ำ (R4.2) | อยู่ 1 ที่ · agent/command ชี้มา |
| C6 | ตัด fact ที่ฝังใน agent `:16` (candidate / stage / วันที่) และรายชื่อ script → ชี้ตรงไป STATUS (stage) + LEDGER (ผล) | agent ไม่มี fact ของ stage/candidate · pointer ลึกชั้นเดียว |
| C7 | command ตรงกับ agent | ไม่มีข้อความขัดกัน |
| D1 | `reference-erfx-discipline-source` += รอบนี้ + แหล่ง eAuction.Lab | — |
| Dup | memory ที่ซ้ำ 6 ไฟล์ → เหลือ why + pointer · แก้ frontmatter 2 ไฟล์ | ไม่มีกฎเต็มซ้ำ CLAUDE.md |

## R4.4 ข้อความร่าง (ให้ Engineer ตรวจเนื้อ ไม่ใช่แค่โครง)

**R1 — แทน `CLAUDE.md:89`**
> - **out-of-scope ที่เจอ → วิเคราะห์ก่อน ไม่ใช่เปิดรายการทันที:** **สิ่งที่ Claude ปั้นขึ้นเอง / สมมติฐานที่ไม่มี requirement รองรับ = drop เงียบ** (ห้ามเปิด issue/card) · เป็น root cause จริง **และทำได้ในรอบนี้** = รวมเข้าแผนรอบนี้ · **เปิดรายการแยกเฉพาะเมื่อมี blocker ที่ cite ได้** (ต้องขออนุมัติวิน · ต้อง charge budget / แตะ lockbox · ต้อง pre-register ใหม่ · รอ data หรือสนามอื่น) — บันทึกต้อง quote blocker นั้น
> - **carve-out (ไม่ใช่ scope creep):** ข้อผิดใน doc / card / LEDGER / ผลที่เผยแพร่แล้ว → §Honest Reporting บังคับแก้ที่ต้นทางทันที + flag downstream **ห้าม drop และห้ามรอ blocker**

*[F5 correction: ถ้อยคำเดิม "ไม่มี requirement รองรับ = drop เงียบ" กว้างกว่าต้นทาง erfx ที่จำกัดไว้ที่ phantom ที่ Claude ปั้นเอง และเสี่ยงอ่านชน `CLAUDE.md:84`]*

**R3 — แทน `CLAUDE.md:33-34` (Rule 12 สองบรรทัดแรก)**
> - **มอบงานให้ agent ตามบริบทที่ agent ได้รับจริง — ห้ามมอบงานที่ต้องพึ่งกฎ/บริบทที่ agent นั้นไม่ได้รับ** (probe no-tool 2026-09-17: Explore ไม่ได้รับ CLAUDE.md/MEMORY · general-purpose + mql5-ea-engineer ได้รับทั้งสอง แต่ memory ได้แค่ index · Plan/fork ยังไม่วัด) · เป็นผลวัด ไม่ใช่สัญญาของ harness — เปลี่ยน harness หรือสงสัย = probe ซ้ำใน session ใหม่
>   - **งานที่ผลลัพธ์ต้องอยู่ใต้กฎโปรเจกต์ (log analysis · นับ/เทียบ metric · ตัวเลขที่จะเข้า doc/LEDGER): agent ต้องได้รับกฎนั้นใน prompt** ถ้า harness ไม่ส่งให้ (iconv UTF-16LE · `sort|uniq -c` · ตาราง compare ทุก metric · ป้ายสนามวัด sim/tester) — Explore ไม่ได้รับ CLAUDE.md จึงต้องใส่กฎใน prompt หรือใช้ agent ที่ได้รับ
>   - **ตัวเลขที่เข้า doc/LEDGER ต้องมาจาก script ที่ Claude รันซ้ำได้เอง** (§Verify script-ownership) — ข้อนี้ไม่ผูกกับตัว agent ใด
>   - **Explore เหมาะกับ locate** (ค้น file/symbol/cross-file reference) เพราะไม่ต้องใช้กฎโปรเจกต์ · **ไม่ใช่ข้ออ้างว่า Explore ทำอย่างอื่นไม่ได้** (`CLAUDE.md:38` ห้ามคาดเดา capability) — ถ้าจะจำกัด capability ต้อง probe แบบให้ใช้ tool ก่อน
>   - มอบงานวิเคราะห์ให้ agent ที่มี Write/Edit (เช่น general-purpose) ได้ **แต่ prompt ต้องสั่งห้ามแก้ไฟล์/ห้าม git write ทุกครั้ง** (review-only mandate เดียวกับ agent `:22`) · default = **Claude+Bash**
>   - subagent ที่ไม่ใช่ fork ไม่เห็นประวัติสนทนา → ใส่บริบท/ชี้ไฟล์ใน prompt เสมอ · แก้ CLAUDE.md กลาง session ไม่ refresh subagent ใน session นั้น

*[F2 correction: probe เป็น no-tool context probe = วัดการได้รับ context ไม่ได้วัด capability → ban แบบเดิมขัด `CLAUDE.md:38`]* · *[C-1: ข้อ 4 เพิ่มขึ้นเพราะร่างเดิมส่งงานไป general-purpose ที่มี Write/Edit โดยไม่กำหนดข้อจำกัด — ขอบเขตจำกัดอยู่ใน R3 เท่านั้น ไม่ยกเป็นกฎ global]*

**B3 — เพิ่มใน §Communication ต่อจาก Phase-3 gate**
> - **Gate state — verdict ล่าสุดคือสถานะ:** revision ที่ Claude แก้เองหลัง FAIL หรือ PASS-with-changes **ยังไม่ verified** · ห้ามประกาศ "แผนพร้อม/ปิดครบ" ขณะ verdict ล่าสุดยังไม่ใช่ PASS · MUST/finding ที่เพิ่มขึ้นข้ามรอบ = สัญญาณว่าตรวจรอบเดียวไม่พอ ไม่ใช่สัญญาณว่ารอบหน้าจะสะอาด
>   - **Material** → Engineer review **เฉพาะขอบเขตที่เปลี่ยน + ผลกระทบของมัน** (ไม่ reopen ส่วนที่ไม่ได้รับผลกระทบ) → Claude-Verify → วินสั่ง
>   - **Non-material** → Claude-Verify → วินสั่ง
>   - **ลังเล = Material**
>   - **Convergence / termination (กันรอบไม่จบ):** ทุกรอบจัด finding เป็น in-scope / out-of-scope ก่อนรับเข้าแผน · **รอบที่ finding ใหม่ทั้งหมดเป็น class C หรืออยู่ในกลไกที่รอบก่อนเพิ่มเอง = ปิดรอบ + ประกาศ residual** · round-report ระบุเลขรอบ + สิ่งที่เปลี่ยนใน scope · **วินปิดรอบได้เสมอ**
>   - **วิน override ได้ทุกสถานะ** (สั่ง implement ก่อน gate · สั่งให้ Engineer ไม่ต้องให้ verdict · ปิดรอบ) → ทำตาม + log ตามรูปแบบ override

*[F3 correction: ต้นทาง erfx มี `CLAUDE.md:46` out-of-scope · `:47` **Convergence guard** · `:48` Root Cause Trace ติดกัน — ร่างเดิมยก `:48` (B1) แต่ไม่ยก `:47` ทำให้ B3 + W1-c ไม่มี fixpoint อื่นนอกจาก PASS ที่ไม่มี change · บรรทัดสุดท้ายเพิ่มเพราะรอบนี้เองวินสั่ง "ไม่ต้องมี verdict" ซึ่งร่างเดิมไม่มีสถานะรองรับ]*

**W1-c — ปรับ `CLAUDE.md:16`** (แก้เฉพาะวงเล็บท้าย ไม่แตะส่วนอื่นของบรรทัด)
> …ไม่มี finding ใหม่ = จบ ห้ามวนรอบเพิ่มเพื่อหาความไม่สมบูรณ์ · **Material revision กลับเข้า Engineer เฉพาะขอบเขตที่เปลี่ยน + ผลกระทบ** (§Communication Gate state) ไม่ใช่รอบใหม่ทั้งแผน

**B2 — เพิ่มใน §Communication**
> - **Material vs Non-material — นิยามหลักใช้กับ *revision / change*:** *Material* = การเปลี่ยนที่ทำให้สิ่งที่ถูก **ตัดสิน / อ้าง / ใช้ไป** เปลี่ยน — พฤติกรรมที่คาดหวังของ EA/script · decision หรือ verdict · หลักฐาน/ตัวเลข · budget · สถานะวิจัยที่ลงทะเบียน (prediction · spec · lockbox) [ตัวอย่าง ไม่ใช่รายการปิด] · *Non-material* = ถ้อยคำ/format/pointer ที่ไม่เปลี่ยนความหมาย · **ลังเล = Material** · Material ไม่วัดจากจำนวนบรรทัดที่แก้
> - **สำหรับ finding** (ไม่ใช่การเปลี่ยน) ใช้ถ้อยคำ: *Material* = **ถ้าไม่แก้แล้วสิ่งที่ตัดสิน/อ้าง/ใช้ไปจะเปลี่ยน** · Severity = ความรุนแรงของผลถ้าเกิดจริง — **คนละแกน** ระบุได้ทั้งคู่ (high-severity + Material=N เกิดได้ เช่นข้อที่อยู่นอกขอบเขตรอบนี้)
> - finding ทุกข้อติด **Tag** (`ใหม่` / `ผลจากการแก้` / `ซ้ำของที่ปิดแล้ว` + อ้างที่ปิด) + **Material Y/N** · ซ้ำของที่ปิดแล้ว = ไม่เปิดรอบ

*[F9 correction: นิยามเดิมเขียนว่า "การเปลี่ยน…" แล้วสั่งใช้กับ finding ด้วย ซึ่ง type ไม่ตรง · และ Material vs Severity ในตาราง report shape (agent `:76`) ไม่มีนิยามความสัมพันธ์]*

**B1 — เพิ่มใน Working Loop**
> - **Root Cause Trace ก่อนเสนอทางแก้ (Issue / script / EA defect):** doc ต้องมี **S-n** (ขั้นที่ report) → path/evidence → **RC-n** + fix น้อยสุด **ก่อน** §ทางแก้ และก่อน Engineer รอบแรก · แก้ trace ได้เมื่อมี evidence ใหม่ (ระบุ evidence ที่เปลี่ยน + revision) · evidence ตามชนิดงาน: script/EA = `file:line` · ผลวิจัย = script output + สนาม / claim-id / commit
> - **ทุก finding จัด class ก่อนเข้าแผน (class = การจำแนก ไม่ใช่ใบอนุญาต):** **A** symptom (อ้าง S-n ได้) · **B** fix-correctness = counterfactual ที่ตรวจได้ "ถอน X → scenario Y → จุด Z พัง (หลักฐาน)" — "จำเป็น/สำคัญ" เฉยๆ ไม่นับ · **C** hardening → นอกรอบ fix นี้ · **B ห้ามอ้างจาก test/certify ที่แผนสร้างเองเพียงอย่างเดียว**
> - **finding ในกลไกที่แผนเพิ่มเอง และกลไกนั้นเป็น class C:** ต้อง **FRAME ก่อน** (กลไกนี้มีไว้ทำอะไร · problem-class ไหน) แล้ว **scope ให้แคบ** · **ถอนกลไกได้เฉพาะเมื่อพิสูจน์ได้ว่าไม่มี problem-class รองรับ** (Rule 14: ห้ามตัด mechanism/guard ที่ตอบไม่ได้ว่ามีไว้ทำไม — scope มัน ไม่ใช่ลบ)
> - **glossary:** `S-n` = ขั้นที่ report · `RC-n` = node ของ root cause ใน trace ฉบับนี้ — **ไม่ใช่ `RC-α`** ที่ `CLAUDE.md:122` (recurrence class ของ AD-4 class-fix) · ห้ามใช้สลับกัน
> - **card design round: class-tag เท่านั้น** ไม่บังคับ Root Cause Trace / `file:line` / counterfactual แบบ code defect

**B6 — ต่อ Rule 7**
> - **ข้ออ้างเชิงไม่มี ("ไม่มี X" / "ไม่เคย" / "ไม่พบ") ต้องมี 4 อย่าง:** แหล่ง + version/commit · ขอบเขตที่ตรวจ · วิธีตรวจ (grep/script ที่รันจริง) · ผลดิบ · **grep หรือรันใหม่ตอนเขียน** (สรุปจาก session ก่อนไม่ใช่หลักฐาน) · ระวัง match ที่อยู่ใน comment หรือ fence

**B4 — ต่อ §Verify≠Self-grading**
> - **exit code ที่ผ่าน pipe ไม่ใช่ exit ของคำสั่ง** (`cmd | head/tail/grep` = exit ของตัวท้าย ซึ่งเกือบเป็น 0 เสมอ) — ตัดสิน PASS/FAIL ต้องรันตรง หรือ `PIPESTATUS[0]` / `set -o pipefail` หรืออ่าน summary line (ใช้กับ `ledger_check.py` · compile log · test run)

**B7 — ต่อ §หลักดีที่สุด (และแทนวรรคท้ายของ agent `:41`)**
> - **ทุกข้อเสนอต้องระบุ trade-off / limitation ที่มีสาระต่อการตัดสินใจ** (สิ่งที่ดรอป · ต้นทุน · residual risk) · ไม่มีประเด็นที่เกี่ยวข้อง = ไม่ต้องเขียนว่า "ไม่มีข้อเสีย"

**B8 — ต่อ Rule 10**
> - **brief Engineer:** scope = **ข้อเสนอ/งานของ Claude เท่านั้น** ห้ามส่งคำสั่งหรือ decision ของวินไปให้ตรวจ · ห้ามใส่กรอบชี้นำ ("verify fix ของผม" · "diminishing returns" · "น่าจะ PASS") · ให้ mandate กว้างหลายมุม + ขอให้ท้าทาย premise ว่ากลไก/card นี้จำเป็นจริงไหม

**M1 — §Communication**
> - **คำต่อเนื่องกำกวม ("ทำต่อ" / "focus ต่อ" / "ดูต่อ") ≠ คำอนุมัติ implement** — ประโยคอ่านได้สองแบบ = default รอ + พูดความเข้าใจ 1 บรรทัดให้วิน confirm · ข้าม STOP ได้ด้วยคำอนุมัติตรงๆ กับ scope ที่ระบุเท่านั้น

**M2a (Preference) — §Verify≠Self-grading**
> - **CLAIM template (Preference · ใช้กับข้อสรุปที่มีสาระต่อการตัดสินใจ ไม่บังคับทุกประโยค):** (1) **Observed** = ผลดิบจาก tool output (2) **Supported** = สิ่งที่ evidence รองรับ + conditional "ใต้ X ที่ทดสอบ" (3) **Not-yet-supported** = สิ่งที่ยังห้ามสรุป · **สำหรับ claim ที่เข้า LEDGER กลไกนี้บังคับอยู่แล้วที่ CLAIM schema** (`supported` / `not-yet-supported` — `/ledger` §CLAIM) → ที่นี่ครอบเฉพาะข้อสรุปที่ยังไม่เป็น claim

**M2b — §Verify≠Self-grading**
> - **ให้คะแนน prediction นับเฉพาะเกณฑ์ที่อิสระ** — ก่อนพิมพ์ "X/Y" วาด implication graph (A ⇒ B = นับ 1 ไม่ใช่ 2) · ตอน pre-register เขียนเกณฑ์ให้ orthogonal ตั้งแต่ต้น

**M3a — §Verify≠Self-grading (canonical · agent `:63-64` → pointer · ห้ามแตะ `:65` = same-commit DoD)**
> - **frame boundary ต้อง enumerate ครบ 6 ก่อนสรุปว่าอะไร "ตาย":** data channel · trigger population · exit rule · horizon · target/monetize · estimator — ขอบที่ไม่เคย vary = blind spot · **ทุก negative claim ติด scope-tag** (ตายในฐานะอะไร ไม่ใช่ "ไม่มี edge")

**M3b — ต่อ Rule 8.1**
> · **No-Trade / skip:** อนุญาตเมื่ออธิบายด้วย root cause ได้ ("ไม่มี setup" · "ไม่มี liquidity" · "ข่าวแรง") · **ห้าม**เมื่อเป็น symptom-skip (correlate กับการแพ้ใน backtest โดยไม่มีเหตุว่าทำไมไม่มีโอกาส)

**M4 — clause ใหม่ (ใกล้ §Honest Reporting)**
> - **เอกสาร enduring = ของสะสม:** Edit เฉพาะจุดที่ผิด **ห้าม Write ทับทั้งไฟล์** · ส่วนที่เนื้อหาถูกแล้วไม่แตะ · เก็บ insight ทุกชิ้นพร้อมที่มา (รวมของ external)
> - **ไม่ใส่ process-noise — ใช้กับ content doc** (card · LEDGER · doctrine · guide): ห้ามมีสถานะ review / "รอ verdict" / next step · **decision-record และ plan doc (`Plan/`) มี decision-state ได้** (สิ่งที่ freeze แล้ว · ข้อที่ค้าง + เหตุผล · lifecycle ของการทดลอง) แต่ห้ามมี narrative ของตัวเอง/คำขอโทษ/รายงานความคืบหน้าแบบเล่าเรื่อง

*[F11 correction: ถ้อยคำเดิมทำให้ไฟล์ Plan นี้เองผิดกฎทันที — `GOVERNANCE:77` "รอ Engineer-finding" · `:162` "(รอวินอนุมัติ = stop ที่ 2)" · `:183` · R4.5 Status lifecycle ล้วนเป็น decision-state ที่จำเป็น]*

**M5a — ต่อ Rule 8.1**
> · **ห้าม pivot กลยุทธ์เพราะแพ้หรือหงุดหงิด** — อยู่กับสิ่งที่วินเลือก แล้วทำให้ engine เข้าใจการเคลื่อนของราคาขึ้น (pivot ต้องมาจาก evidence + คำสั่งวิน)

**M6M7 — clause สั้นใน CLAUDE.md (เพราะไฟล์นี้ไม่ถูกโหลด)**
> - **ขอบเขตของ CLAUDE.md + การเขียน memory (ฉบับเต็ม → `Plan/CLAUDE_MD_GOVERNANCE.md §R4.2` / `§R4.5`):** CLAUDE.md = กฎที่นิ่งเท่านั้น (สถานะ → `STATUS.md` · แผน/ออกแบบ → `Plan/` · bug → `Issue/`) · **memory = บทเรียน/เหตุการณ์/reference ไม่ใช่แหล่งกฎ** — ก่อนสร้างไฟล์ใหม่ให้ fold เข้าไฟล์ที่ครอบอยู่ (ห้าม fork) · ห้าม `[[link]]` ไปชื่อที่ย้ายเข้า archive · **กฎที่ subagent ต้องใช้ต้องอยู่ใน CLAUDE.md หรือไฟล์ agent**

**AM — §Authority Order** = ตาราง R4.2 + หลัก 3 ข้อ + pointer ไปทะเบียนการซ้ำ

## R4.5 Experimental register (W3 · B5)
| ช่อง | เนื้อหา |
|---|---|
| ชื่อ | B5 — revert-and-run สำหรับ detector claim |
| สถานะ | **Experimental · ไม่ใช่กฎบังคับ** (ห้ามอ้างเป็น MUST ใน review) |
| ขอบเขตที่ห้ามสับสน *[F23]* | ป้าย Experimental นี้ครอบ **เฉพาะวิธี revert-and-run** · **ห้ามใช้เป็นเหตุปฏิเสธกฎที่บังคับอยู่แล้ว** — `CLAUDE.md:117` "จุดที่ script ตัด/รวม/จับคู่ ต้อง fail loud หรือ log" เป็น mandatory ของ §Verify ไม่ใช่ experimental · ถ้า guard ยิงจริงได้ = หลักฐานที่รับฟังได้เสมอ |
| Status lifecycle | `Experimental` → `Observed` (ใช้จริงแล้ว ≥1 ครั้ง + บันทึก evidence) → `Adopt` (วินยกเป็นกฎ → ย้ายข้อความเข้า CLAUDE.md แล้วทะเบียนนี้ชี้ไปที่นั้น) **หรือ** `Dropped` (บันทึกเหตุผล + evidence ที่ทำให้ drop) · **ห้ามลบทะเบียน** — เปลี่ยนสถานะเท่านั้น (ประวัติต้องอ่านย้อนได้ว่าเคยทดลองอะไรและผลเป็นอย่างไร) |
| Trigger | มี claim ว่า "mechanism X จับหรือกัน failure Y ได้" (guard · assert · fail-loud · gate · check ใน script) |
| Scope | เฉพาะ claim นั้น ไม่ครอบทุก test/validation/assertion |
| วิธี | ฉีดความผิดหรือถอน fix ชั่วคราว → รัน → ต้องเห็น FAIL → คืนสภาพ · แนบ output ทั้งสองสภาพ |
| Cost | 1 รอบรัน + เสี่ยงลืมคืนสภาพ (ต้องมี marker ชัด + ตรวจ `git status` ก่อน commit) |
| Evidence ที่จะเก็บ | ครั้งที่ใช้ · เจอ detector ปลอมหรือไม่ · เวลาที่ใช้ |
| เกณฑ์ adopt / drop | หลังใช้จริงครั้งแรก: เจอ detector ปลอม → เสนอวินยกเป็นกฎ · ไม่เจอและต้นทุนสูง → drop · ผลไม่ชัด → คงสถานะ experimental |

## R4.6 ค้าง (ต้องการผลตรวจก่อนเดินต่อ)
| ID | สถานะ |
|---|---|
| M5b | **ปิดแล้ว (Engineer ตอบ + Claude-Verify ยืนยันข้อความจริง 2026-09-18)** → ผลอยู่ที่ §R4.9 §M5b-resolved · ทางที่รับ = ต่อลิสต์ตัวอย่างของ Rule 8.1 เฉพาะ *ข้อห้าม* ไม่สร้าง clause ใหม่ ไม่เข้า §Doctrine |
| ขนาด CLAUDE.md | **วัด gross แล้ว = +8,559 chars (+34.8%)** (ดู §R4.1(5)) · **net ยังไม่วัด** — ต้องวัดตอนร่างข้อความสุดท้ายก่อนเสนออนุมัติ |
| hook | ถ้า B3 หรือ M1 เปลี่ยนถ้อยคำ canonical ต้องตรวจว่าข้อความใน hook ทั้งสองยังตรงกัน (ทะเบียน R4.2) — ตรวจด้วย grep canary phrase ไม่ใช่ด้วยตา |

## R4.7 ลำดับ implement (หลังผ่าน Engineer → Claude-Verify → วินอนุมัติ)
1. `CLAUDE.md` — R1 · R3 · W1-c · B3 · B2 · B1 · B4 · B6 · B7 · B8 · M1 · M2a · M2b · M3a · M3b · M4 · M5a · M6M7 · AM
2. `.claude/agents/mql5-ea-engineer.md` — R2 (pointer + safety essence · §R4.9 §R2-revised) · B7 (`:41`) · B2 (Tag + Material) · B1 (class) · M3a (pointer ที่ `:63-64`) · M2b (pointer ที่ `:57`) · C6 (ตัด fact ที่ **จะ**ล้าสมัย — preventive · วันที่ตรวจ 2026-09-18 ยังตรงกับ LEDGER FRONTIER)
3. `.claude/commands/mql5-ea-engineer.md` — C7
4. `.claude/commands/ledger.md` — ความสัมพันธ์ Heavy/Light ↔ Material (§R4.9 §F6-resolved · **ไม่ map 1:1**) · แก้บรรทัด out-of-scope log (`:100`) ให้มี blocker ที่ cite ได้ตามกฎ R1
5. `.claude/commands/trellis-010.md` — ตรวจว่าไม่ขัดกฎใหม่ (gate state · out-of-scope) แก้เฉพาะจุดที่ขัด
6. memory — Dup 5 ไฟล์ → why + pointer (**ยกเว้น `measurement-discipline` ซึ่งเป็นบ้านเดียวของ M2a/M2b**) · ไฟล์ที่กฎย้ายออกแล้ว → เหลือ incident · frontmatter 2 ไฟล์ · D1
   - ⚠️ **สถานะ = `partial` (2026-09-18)** — ส่วน "ไฟล์ที่กฎย้ายออกแล้ว → เหลือ incident" **ยังไม่ทำ** (RS-1..RS-5 → §R4.10.1) · ห้ามอ่านข้อ 6 ว่าปิดแล้ว
7. ไฟล์นี้ — ทะเบียนการซ้ำ + experimental register + provenance table (§R4.9) + **implementation record → §R4.10**

## R4.8 Consistency & Behavior Validation (P6)
**Consistency — รันจริง แนบ output**
1. **grep ประโยคเต็มของข้อความเดิม ไม่ใช่ substring** *[F15 — เกณฑ์เดิมพังเพราะข้อความแทนที่ของ R4 เองมี substring "log เป็น issue แยก"]*
   - `grep -c "out-of-scope ที่เจอ → log เป็น issue แยก" CLAUDE.md` = **0** (ขอบเขต = `CLAUDE.md` เท่านั้น · ไฟล์ Plan/ประวัติไม่นับ)
   - `grep -c "วิเคราะห์ backtest log / expectancy-sim output (count/compare/aggregate) → \*\*Explore agent\*\*" CLAUDE.md` = **0**
   - doctrine ซ้ำ: `diff <(sed -n '86,90p' agent) <(sed -n '47,51p' CLAUDE.md)` → ต้องไม่มีสำเนา 5 ข้อใน agent (เหลือ essence 1 บรรทัด + pointer)
2. **cite-check เชิงกลไก (ปิด class ของ F1/F14-cite):** script print บรรทัดปัจจุบันของทุก `file:line` ที่อ้างใน §R4.4 / §R4.7 พร้อมข้อความ แล้วยืนยันด้วยตาว่าบทบาทตรง — **ต้องรันก่อนแตะไฟล์ทุกครั้ง** ไม่ใช่หลังแก้
   - **สถานะ R4 = `Deferred / Not Executed` (tool unavailable · วินตัดสิน 2026-09-18 — ทางเลือก A)** — project ยังไม่มีเครื่องมือที่ทำหน้าที่นี้ และการสร้าง `Scripts/cite_check.py` เป็น scope เพิ่มจาก §R4.7 → **ไม่สร้าง tooling ใหม่เพียงเพื่อให้ acceptance ผ่าน**
   - **`Deferred` ≠ `Failed`** — ไม่ใช่ผลลบของการตรวจ ไม่ใช่การละเมิด และไม่ลดสถานะของ implementation รอบนี้ · แปลว่า *ยังไม่ได้รัน เพราะเครื่องมือที่เกณฑ์เรียกร้องยังไม่มีอยู่*
   - **หลักที่ใช้ตัดสิน:** preserve capability; constrain authority — รักษาความสามารถที่จำเป็นต่อภารกิจ แต่ไม่เพิ่ม mechanism ที่ยังไม่มี evidence ว่าจำเป็น (ChatGPT analysis ที่วินแนบประกอบ 2026-09-18) · ในทางกลับกันก็**ห้ามลดคุณภาพ verification** ด้วยการเปลี่ยน manual check ให้เป็น PASS ของเกณฑ์เชิงกลไก
   - **manual cite verification (V1 + Claude-Verify) = evidence สนับสนุน implementation รอบนี้ แต่ไม่แทนเกณฑ์นี้** — ห้ามนับเป็น PASS ของข้อ 2
   - งานต่อ = **open item: Tooling track — mechanical citation/reference verification** (นอก R4 · ไม่เป็น global governance rule จนกว่าจะมี decision ใหม่)
3. ตรวจกฎซ้ำเทียบ Authority Map + ทะเบียน (ทุกกฎใน R4.4 ปรากฏที่เดียว ยกเว้นที่อยู่ในทะเบียน) · รวม **hook canary**: `grep -c "ask กำกวม" settings.local.json` และถ้อยคำ gate ใน hook ต้องตรงกับ canonical
4. วัดตัวอักษร CLAUDE.md ก่อน/หลัง (baseline 24,626 · gross ที่คาด +8,559 · รายงาน net จริง)
5. probe subagent ซ้ำใน **session ใหม่** (เทียบตาราง R4.1(1))
6. **M1–M7 ตรวจด้วย grep keyword ของ incident ไม่ใช่ดุลพินิจ** *[F16]* — ต้นทางแต่ละข้ออยู่ใน provenance table (§R4.9) · keyword ที่ต้องยังพบใน memory หลังแก้: `TP-1` / `ES-1` / `ES-2` (M2b) · `tick_volume` (M3a) · `Cent account` (M5b) · `Write ทับ` (M4) · `focus แผน` (M1)
7. ไฟล์ที่ต้องรวมในทุก scan: `CLAUDE.md` · `.claude/agents/mql5-ea-engineer.md` · `.claude/commands/{mql5-ea-engineer,ledger,trellis-010}.md` · `.claude/settings.local.json` · memory 13 ไฟล์ + `MEMORY.md`
   - **นิยามของ "memory 13 ไฟล์" (ชี้แจง 2026-09-18 · วินสั่ง):** = จำนวนไฟล์ **`feedback-*`** ที่อยู่ใน scope ของ audit รอบนี้ (§R4.1(2) "อ่านครบ 13 ไฟล์ `feedback-*`") — **ไม่ใช่** จำนวน markdown ทั้ง memory directory ซึ่งวัดได้ **23 `.md` + `MEMORY.md`** (`ls` 2026-09-18)
   - **ห้ามขยาย scope ย้อนหลัง** — ไฟล์ `project-*` (5) และ `reference-*` (4) ที่เหลือ **ไม่ได้อยู่ใน audit ของ R4 รอบนี้** ยกเว้น `reference-erfx-discipline-source` ที่เข้ามาโดย D1 (§R4.3:340)

**เกณฑ์การปิด acceptance (วินตัดสิน 2026-09-18 — แทนเงื่อนไขเดิมที่ใช้กันในรอบสนทนา "ต้องผ่านทั้ง #2 และ #5")**
> *หมายเหตุ provenance:* ถ้อยคำ "ต้องผ่านทั้ง #2 และ #5" **ไม่เคยถูกเขียนลงไฟล์นี้** (grep 2026-09-18: ไม่พบใน `Plan/CLAUDE_MD_GOVERNANCE.md`) — เป็นเงื่อนไขที่ตกลงกันในบทสนทนา ข้อนี้จึงเป็น **การเขียนเกณฑ์ลงไฟล์ครั้งแรก** ไม่ใช่การแก้ข้อความเดิม

- **Implementation record เขียนได้เมื่อ acceptance ที่ *มีเครื่องมือพร้อม* ถูก execute และผ่าน** — ไม่ต้องรอ acceptance ที่เครื่องมือยังไม่มี
- **acceptance ที่ยังไม่มี tooling → บันทึกเป็น `Deferred` พร้อมเหตุผล** และ**ไม่ถือเป็น failure ของ implementation รอบนี้**
- ห้ามปิดช่องว่างด้วยการ (ก) สร้าง tooling เฉพาะกิจเพื่อให้ checklist ครบ (ข) เปลี่ยน manual check เป็น PASS ของเกณฑ์เชิงกลไก (ค) แก้ requirement ของเกณฑ์ให้ผ่านง่ายขึ้น
- **สถานะจริงของทุกข้อต้องปรากฏใน record** — PASS ต้องมี output ที่รันจริงแนบ · Deferred ต้องระบุเครื่องมือที่ขาด · ยังไม่รัน ต้องเขียนว่ายังไม่รัน

**Behavior Observation — non-blocking**
หลังรอบ Engineer จริงรอบแรกที่ใช้กฎใหม่: บันทึก 1 บรรทัดใน Progress Log ว่ากฎข้อไหนถูกใช้ · มีการละเมิดหรือไม่ · ไม่ถือเป็น gate และไม่ใช่ข้อพิสูจน์ว่าพฤติกรรมดีขึ้น · **ผลเรียกว่า Behavior Observation ไม่ใช่ Behavior Passed**

## R4.9 Correction pass (Engineer review R1 + Claude-Verify + decision วิน 2026-09-18)

> รอบแก้เดียว (single correction pass) · แก้เฉพาะสิ่งที่ Claude-Verify ยืนยันด้วยการเปิดไฟล์จริง · **ไม่แตะ runtime file ใด** (CLAUDE.md · agent · commands · memory · hook · source)

### §F6-resolved — Heavy/Light กับ Material/Non-material = คนละมิติ (วินตัดสิน: ห้าม map 1:1)
| | Heavy / Light (`commands/ledger.md:28-29`) | Material / Non-material (R4.4 B2) |
|---|---|---|
| ตอบคำถามอะไร | **operation tier** — คำสั่งนี้เป็นชนิดที่ต้องผ่าน gate ไหน | **impact ของ revision/change** — การเปลี่ยนนี้กระทบสิ่งที่ตัดสิน/อ้าง/ใช้ไปหรือไม่ |
| ใช้เมื่อไร | ตอน **เลือก route ของ operation** (`new`/`close`/`update`/`backfill`/`fix`/`status`) | ตอน **ตัดสินว่า revision หลัง FAIL / PASS-with-changes ต้องกลับ Engineer หรือ Claude-Verify** |
| เจ้าของนิยาม | `/ledger` (canonical) | `CLAUDE.md` §Communication (canonical) |

- **ห้ามสร้าง translation rule หรือ taxonomy ชุดที่สาม** · ทั้งสองแกนใช้คู่กันได้: operation อาจเป็น Light แต่การเปลี่ยนที่มันทำอาจเป็น Material (ตัวอย่างจริงที่ Engineer ชี้: `backfill` = Light ตาม tier แต่แก้เลข frozen = Material ตาม impact) → **กรณีนั้นเดินตามกฎที่เข้มกว่าของแต่ละแกนโดยไม่ยุบแกน**: route ตาม tier ของ `/ledger` และถ้าเป็น Material ก็ต้องมี Engineer ตามเหตุของ gate state
- **จุด overlap ที่ต้องเขียนกำกับใน `/ledger` (implement stage):** `update(a)` number-refresh · `backfill` · `fix` — ระบุว่า tier ไม่ยกเลิกข้อกำหนดของ gate state และ gate state ไม่ยกเลิก tier
- **ไฟล์ที่เข้า scope consistency/acceptance เพิ่ม:** `.claude/commands/ledger.md` · `.claude/commands/trellis-010.md` (ดู §R4.7 ข้อ 4-5 และ §R4.8 ข้อ 7)
- **`ledger.md:100`** — out-of-scope ที่ log ไว้ให้เหตุผลเชิงเงื่อนไข ("latent — จำเป็นเฉพาะถ้าต้องการ…") ซึ่งไม่ใช่ blocker ที่ cite ได้ตามกฎ R1 → **แก้ตอน implement ตามลำดับ §R4.7 ข้อ 4** (รอบนี้ห้ามแตะ commands ตามคำสั่งวินข้อ 6)

### §R2-revised — agent กับ EA/Gold Doctrine (F14)
- **ผล diff จริง (2026-09-18):** agent `:86-90` ต่างจาก `CLAUDE.md:47-51` **4 ใน 5 ข้อ** — เป็นสำเนาย่อที่ตัด nuance (เช่นคำสั่ง "ออกแบบโดยถือว่า worst-case > เพดานที่ตั้งไว้" หายไป) → ข้ออ้าง "ไม่ drift จึงคงสำเนาได้" ใช้ไม่ได้ และ pointer เปล่าก็ทำให้ safety content ขึ้นกับ injection ที่ §R4.1(1) ประกาศเองว่าไม่การันตี
- **ทางที่รับ:** agent เก็บ **1 บรรทัด essence + pointer** แทนสำเนา 5 ข้อ — ร่าง:
> ## ⚠️ EA/Gold Validation Doctrine — **Gold + lot scaling ระเบิดบัญชีง่ายที่สุด · ห้ามเขียนหรือ optimize engine ก่อนพิสูจน์ expectancy บน tick data** · ฉบับเต็ม 5 ข้อ (universal) → `CLAUDE.md` §EA/Gold Validation Doctrine · grid = DORMANT → `Plan/TRELLIS-001 §3`
- ลงทะเบียนเป็นการซ้ำที่ตั้งใจ (§R4.2) + sync check ใน §R4.8 ข้อ 1

### §M5b-resolved — วินสั่งใช้ทางที่ Verify ยืนยัน
- **หลักฐาน:** `CLAUDE.md:28` ลิสต์ "เพิ่มทุน/ข้ามวัน/หยุดเทรด/เพิ่มตัวแปรให้เลี่ยง" — ไม่มี "เปลี่ยนชนิดบัญชี" และ "ลด lot-sizing" · `:44` ประกาศ Doctrine "universal · ไม่ผูกกับ strategy ใด" · `:48` Doctrine #3 "worst-case > เพดานที่ตั้งไว้"
- **สรุป:** ครึ่ง *ข้อห้าม* ใช้ได้ · ครึ่ง "sizing = derived layer ที่ engine จัดการเอง" เป็น methodological preference ของ engine family ที่ size ด้วย risk%×equity÷stop **ไม่ใช่ governance invariant** และขัด `:48` ในการอ่านตามตัวอักษร → **ห้ามวางใน §Doctrine และไม่สร้าง clause ใหม่**
- **ร่างที่จะลง (ต่อลิสต์ตัวอย่างของ Rule 8.1 เท่านั้น):**
> 8.1 … เพิ่มทุน/**เปลี่ยนชนิดบัญชี (เช่น Cent)**/**ลด lot-sizing เพื่อให้รอด**/ข้ามวัน/หยุดเทรด/เพิ่มตัวแปรให้เลี่ยง …
- "derived layer" + incident (Cent account · $100 ไม่รอด) คงอยู่ใน memory `feedback-fix-engine-not-excuses` เป็น why

### §Provenance ของ M1–M7 (F16 — ทำให้ acceptance ข้อ 6 รันได้)
| ID | ไฟล์ต้นทาง (memory) | keyword ที่ต้องยังพบหลังแก้ |
|---|---|---|
| M1 | `feedback-analyze-before-act` | `focus แผน` · `ทำต่อ` |
| M2a · M2b | `feedback-measurement-discipline` (**บ้านเดียว — ห้าม prune แบบ Dup**) | `Observed` · `TP-1` · `ES-1` · `ES-2` |
| M3a · M3b | `feedback-measurement-frame-fairness` | `tick_volume` · `symptom` |
| M4 | `feedback-doc-editing-discipline` | `Write ทับ` |
| M5a · M5b · M5c | `feedback-fix-engine-not-excuses` | `pivot` · `Cent account` |
| M6 | `feedback-claude-md-scope` | `ธรรมนูญ` |
| M7 | `feedback-memory-governance` | `fold` |

### §Open items — verified แต่ **ยังไม่ adopt รอบนี้** (วินยังไม่ freeze · ห้ามถือว่าปิด)
| ID | สาระ | สถานะ |
|---|---|---|
| F7 | relay ของ Engineer report ไม่มีข้อบังคับความครบ (`CLAUDE.md:65` ห้ามไม่ถึงการตัด/รวบ finding) → ช่อง bypass เชิงโครงสร้าง | **preventive · future consideration** — วินตัดสินไม่เพิ่มกฎรอบนี้ · **ข้อเท็จจริงที่ relay รอบนี้ครบ 24/24 ไม่ใช่หลักฐานว่าความเสี่ยงหมดไป** (เป็นพฤติกรรมครั้งเดียว ไม่ใช่กลไก) |
| F8 | ชุด Tag ขาดหมวด "ค้างจากรอบก่อน (ยังไม่ปิด)" · "ซ้ำของที่ปิดแล้ว" ไม่บังคับพิสูจน์ว่าการปิดยังยืนหลังการแก้ · เสนอ auto-Material จาก diff ที่แตะ pin/SPEC/prediction/α/budget | preventive · ไม่ adopt รอบนี้ |
| F18 | C6: ถ้าตัด fact ออกจาก agent ควรมีขั้น MUST-read (LEDGER FRONTIER + STATUS) ในไฟล์ agent เท่ากับ `command:11` เพราะการเรียกผ่าน Task ตรงๆ bypass command (รอบนี้เป็นตัวอย่าง) | preventive · ไม่ adopt รอบนี้ (C6 ยังทำตามแผนเดิม) |
| F19 | ถ้อยคำ B8 ("ห้ามส่ง decision ของวินให้ Engineer") ตามตัวอักษรห้ามสิ่งที่ brief รอบนี้ใช้ (ส่ง §R4.0 ในฐานะ FROZEN constraint) | ไม่แก้ถ้อยคำรอบนี้ — บันทึกไว้ว่าการส่ง decision ในฐานะ FROZEN ไม่ใช่การขอให้ Engineer ตัดสิน decision |
| F20 | B6 ไม่อยู่ในรายการแก้ไฟล์ agent → Engineer ไม่ถูกผูกด้วยกฎข้ออ้างเชิงไม่มี | preventive · ไม่ adopt รอบนี้ |
| C-1 | **additional verified finding (Claude-Verify):** ร่าง R3 เดิมเสนอย้ายงานวิเคราะห์ไป `general-purpose` ซึ่งมี Write/Edit/Bash เต็ม ขัดเจตนา review-only (agent `:22` ถอด Write/Edit ออกโดยเจตนา) | **แก้แล้วในร่าง R3** เป็น work-assignment rule: prompt ต้องสั่งห้ามแก้ไฟล์/ห้าม git write · default = Claude+Bash · **ขอบเขตจำกัดอยู่ใน R3 ไม่ยกเป็นกฎ global** |
| F24 | W2-a ทำให้แยกไม่ได้ระหว่าง "คิดแล้วไม่มีสาระ" กับ "ไม่ได้คิด" | **informational** — decision ของวิน ไม่ reopen |

### §Implementation shape
- **ไม่บังคับแยก 2 commit** (ข้อเสนอ Alternative ของ Engineer) — วินตัดสินว่าเป็น implementation detail ตัดสินตอน implement ถ้ามีเหตุผลจริง
- รอบนี้จบที่ **Plan correction** · ยังไม่มี user approval สำหรับ implement

### §Correction log (F1–F24 · สถานะหลังรอบนี้)
- **แก้ในแผนแล้ว:** F1 (line cites 3 จุด + P4 table) · F2 (R3 wording) · F3 (termination + override state) · F4 (B1 ผูก Rule 14) · F5 (ขอบเขต drop + carve-out) · F6 (§F6-resolved + scope ไฟล์) · F9 (Material/finding/Severity) · F10 (เลขที่วัดแล้ว + complexity-gate) · F11 (M4 scope) · F12 · F13 (ทะเบียนซ้ำ + pointer) · F14 (§R2-revised) · F15 (acceptance ประโยคเต็ม) · F16 (provenance + keyword) · F17/M5b (§M5b-resolved) · F21 (glossary RC-n) · F22 (provenance classification) · F23 (ขอบเขต B5) · C-1
- **บันทึกเป็น open item ไม่แก้รอบนี้:** F7 · F8 · F18 · F19 · F20 · F24 (informational)
- **หลักฐานที่ Claude-Verify แก้ให้ Engineer:** F14 ("ไม่ drift" → ต่าง 4/5 ข้อ) · F15 (5 hits → 4 hits ด้วย pattern เต็ม) · F10 (7,614 → 8,559 chars gross และยังไม่หัก net)

## R4.10 Implementation record (§R4.7 ข้อ 7 · วินสั่งเขียน 2026-09-18 · **ยังไม่ commit**)

> ทุกบรรทัด `PASS` ด้านล่างมี output ที่รันสดในวันที่บันทึก · เลขทุกตัว re-run ตอนเขียน ไม่ได้ยกมาจาก session ก่อน (Working Rule 7.1)
> สนามวัด = working tree ของ repo (ไม่ใช่ HEAD) · anchor HEAD = `8271163`

### ผล acceptance §R4.8 (รันสด 2026-09-18)
| # | เกณฑ์ | สถานะ | หลักฐาน (คำสั่ง → ผลดิบ) |
|---|---|---|---|
| 1 | grep ประโยคเต็มของข้อความเดิม + doctrine ไม่ซ้ำใน agent | **PASS** | `grep -cF "out-of-scope ที่เจอ → log เป็น issue แยก" CLAUDE.md` → `0` · `grep -cF "วิเคราะห์ backtest log / expectancy-sim output (count/compare/aggregate) → **Explore agent**" CLAUDE.md` → `0` · `agent:86-87` = หัวข้อ + **essence 1 บรรทัด + pointer** ไม่มีสำเนา 5 ข้อ (ตรงร่าง §R4.9 §R2-revised) |
| 2 | cite-check เชิงกลไก | **Deferred / Not Executed — tool unavailable** | ไม่มีเครื่องมือ: `ls Scripts/` ไม่มี `cite_check*` · `find . -name "cite_check*" -not -path "./.git/*"` → ไม่มีผลลัพธ์ · `git grep -n cite_check` → ไม่มีผลลัพธ์ · **ไม่ได้สร้างไฟล์ใดใน R4** (วินตัดสิน A) |
| 3 | Authority Map + ทะเบียนการซ้ำ + hook canary | **Passed partially** (ไม่ใช่ PASS) — ผ่านเฉพาะส่วนที่ตรวจเชิงกลไกได้ · ดูข้อจำกัดท้ายช่อง | canary `grep -cF "ask กำกวม" .claude/settings.local.json` → `1` · hook keys `UserPromptSubmit`=2 `PreToolUse`=2 · `PRE-SEND GATE`=1 `Working Loop`=1 · M1 wording ใน hook (`ask กำกวม/ไม่เล็ก → พูดความเข้าใจ 1 บรรทัด รอ confirm ก่อนลงมือ`)=1 · ทะเบียน 6 รายการ (§R4.2) พบครบ: pointer `feedback-no-appearance-of-done` ที่ `CLAUDE.md:12` · CLAIM schema `ledger.md:38` + pointer `CLAUDE.md:134` · agent essence `:86-87` · **ข้อจำกัดที่ต้องประกาศ:** ส่วน "ทุกกฎใน §R4.4 ปรากฏที่เดียว ยกเว้นที่อยู่ในทะเบียน" ตรวจเชิงกลไกแล้ว**เฉพาะ 6 รายการที่อยู่ในทะเบียน** — การสแกนหากฎซ้ำ *นอก* ทะเบียนยังไม่ได้ทำเชิงกลไก (เป็น class เดียวกับที่ acceptance #2 จะปิด) → **ห้ามอ่านข้อนี้ว่า "ยืนยันแล้วว่าไม่มีกฎซ้ำที่ไหนอีก"** |
| 4 | วัดตัวอักษร CLAUDE.md ก่อน/หลัง | **PASS (วัดแล้ว · เลขต่างจากที่คาด)** | `HEAD:CLAUDE.md` = **24,626 chars** (ตรง baseline ที่ประกาศไว้) · working tree = **32,366 chars** → **net +7,740 (+31.4%)** เทียบ gross ที่คาด +8,559 → **net ต่ำกว่าคาด 819 chars** |
| 5 | probe subagent ซ้ำใน session ใหม่ | **PASS** | probe 2026-09-18 session ใหม่ · 3 agent · prompt เดียวกัน · `tool_uses = 0` ทั้งสาม · Explore = ไม่มี `CLAUDE.md`/`MEMORY.md` ใน context (ตอบ NOT IN CONTEXT ทุกข้อ) · general-purpose + mql5-ea-engineer = ได้ทั้ง `CLAUDE.md` (ฉบับ working tree — ตอบ clause ใหม่ 7.1/8.1/Authority Map/Gate state ได้) + `MEMORY.md` **ระดับ index เท่านั้น** → reproduce ผล 2026-09-17 · **เป็น observation ณ วันที่วัด ไม่ใช่ platform contract** |
| 6 | M1–M7 ตรวจด้วย grep keyword (provenance §R4.9) | **PASS 13/13** | `focus แผน`=1 · `ทำต่อ`=1 · `Observed`=1 · `TP-1`=1 · `ES-1`=1 · `ES-2`=1 · `tick_volume`=1 · `symptom`=1 · `Write ทับ`=1 · `pivot`=4 · `Cent account`=1 · `ธรรมนูญ`=1 · `fold`=2 |
| 7 | ไฟล์ที่ต้องรวมในทุก scan | **PASS** | 6 ไฟล์ runtime มีครบ (`CLAUDE.md` · agent · commands ×3 · `settings.local.json`) · **ความกำกวม "memory 13 ไฟล์" = ปิดแล้ว (วินชี้ขาด 2026-09-18):** 13 = จำนวน `feedback-*` ใน scope audit §R4.1(2) **ไม่ใช่** จำนวน `.md` ทั้ง directory (วัดได้ 23 `.md` + `MEMORY.md`) → ข้อความนิยามเขียนไว้ที่ §R4.8 ข้อ 7 แล้ว · **ห้ามขยาย scope ย้อนหลังให้ 23 ไฟล์ต้องถูก audit ใน R4** |
| Behavior | Behavior Observation (non-blocking) | **ยังไม่รัน** | ต้องรอรอบ Engineer จริงรอบแรกที่ใช้กฎใหม่ · ไม่ใช่ gate |

### สรุปสถานะ R4
> **สถานะรวม = `implemented ตาม scope runtime ที่ทำแล้ว` — ไม่ใช่ `fully complete`** · §R4.7 ข้อ 6 (memory fold) = **partial** และมี residual ที่ยังไม่ทำ 5 รายการ (ลิสต์ด้านล่าง) · **ห้ามเขียนหรืออ้างว่า R4 เสร็จทั้งชุดโดยไม่มี qualifier นี้**

- **executed + ผ่าน:** #1 · #4 · #5 · #6 · #7
- **executed + ผ่านบางส่วน (ประกาศข้อจำกัด ไม่นับเป็นผ่านเต็ม):** #3 — canary + ทะเบียนซ้ำ 6/6 ผ่าน · การสแกนกฎซ้ำนอกทะเบียนยังไม่ได้ทำเชิงกลไก
- **Deferred:** #2 เท่านั้น — เหตุ = เครื่องมือที่เกณฑ์เรียกร้องยังไม่มีใน project · **ไม่ใช่ failure**
- **manual cite verification** = evidence สนับสนุน implementation รอบนี้ · **ไม่แทน** mechanical acceptance #2
- **ไม่มี `Scripts/cite_check.py` ถูกสร้างใน R4** (verified ด้วย `ls` + `find` + `git grep` ข้างบน)
- **ไม่เปิด tooling track ภายใน R4** — ยกเป็น open item แยก: *Tooling track — mechanical citation/reference verification* (ไม่เป็น global governance rule จนกว่าจะมี decision ใหม่)
- ไฟล์ที่เปลี่ยนในรอบนี้ (`git diff --numstat` เทียบ `8271163` · ins/del): `CLAUDE.md` 27/8 · `.claude/agents/mql5-ea-engineer.md` 12/15 · `.claude/commands/ledger.md` 3/1 · `.claude/commands/mql5-ea-engineer.md` 2/1 · ไฟล์นี้ 359/0 (ก่อนเพิ่ม §R4.10)
- **`.claude/status/STATUS.md` 2/2 = ไม่ใช่ R4 change** → ดู §R4.10.2
- **`.claude/commands/trellis-010.md` ไม่ถูกแก้** — ตรวจตาม §R4.7 ข้อ 5 โดย**อ่านทั้งไฟล์ (27 บรรทัด)** ไม่ใช่ grep อย่างเดียว: pre-flight/guardrails/ลำดับ `Gate → Engineer → Claude Verify → หยุดรอวิน` สอดคล้องกับ 3-Phase Gate และไม่มีถ้อยคำที่ขัดกฎใหม่ (gate state · out-of-scope) → ไม่มีจุดต้องแก้
- **§R4.7 ข้อ 6 (memory fold) = `partial`** — Dup 5 · frontmatter 2 · D1 · index ทำแล้ว · **การตัดกฎที่ย้ายเข้า `CLAUDE.md` แล้วออกจากไฟล์ต้นทางให้เหลือ incident ยังไม่ทำ** (mapping → §R4.10.1)

**Residual / open items ของ R4 (explicit · ยังไม่ทำ · ไม่ถือว่าปิด)**
| # | รายการ | ไฟล์ | กฎที่ยังค้างอยู่ 2 บ้าน |
|---|---|---|---|
| RS-1 | fold M1 → เหลือ incident | `feedback-analyze-before-act` (mtime 2026-09-03) | คำกำกวม → พูดความเข้าใจ รอ confirm |
| RS-2 | fold M3a/M3b → เหลือ incident | `feedback-measurement-frame-fairness` (2026-07-08) | measurement-frame fairness · symptom-skip |
| RS-3 | fold M4 → เหลือ incident | `feedback-doc-editing-discipline` (2026-07-07) | ห้าม Write ทับทั้งไฟล์ · accumulate |
| RS-4 | fold M5a/M5b/M5c → เหลือ incident | `feedback-fix-engine-not-excuses` (2026-07-07) | ห้ามหลบ (ทุน/บัญชี/sizing) · ห้าม pivot เพราะแพ้ |
| RS-5 | fold M6 → เหลือ incident | `feedback-claude-md-scope` (2026-06-27) | ขอบเขต CLAUDE.md |

- **ผลกระทบที่ต้องรู้:** ระหว่างที่ RS-1..RS-5 ยังค้าง กฎเหล่านี้มี 2 บ้าน (CLAUDE.md + memory) → ขัดหลัก Authority Map "หนึ่งชนิด fact → หนึ่ง authority" ที่เพิ่ง adopt · **ยังไม่ลงทะเบียนเป็นการซ้ำที่ตั้งใจ** (§R4.2) เพราะไม่ใช่การซ้ำที่ตั้งใจ แต่เป็นงานที่ยังไม่ได้ทำ
- **เหตุที่ไม่ทำในรอบ final verification:** memory = runtime file · คำสั่งวินจำกัดการแตะ runtime ไว้เฉพาะแก้ provenance/ambiguity → **รอวินตัดสิน** (ทำก่อน commit / แยกรอบ / ไม่ทำ)
- **ไฟล์ uncommitted ที่ *ไม่ใช่* R4** (mtime 2026-09-09 · AD-4 track · **ผมไม่แตะในรอบนี้**): `.claude/status/STATUS.md` · `Plan/TRELLIS-010_LEDGER.md` · `Plan/TRELLIS-010_brain_research_workflow.md` · `Scripts/ad4_card.py` · `Scripts/tp1_card.py` · `Scripts/ad4_cert_out_v2/` (untracked)
- **commit: ยังไม่ทำ** — รอวินตรวจ final diff + record นี้ก่อน

### R4.10.1 Memory audit scope + mapping (final verification วินสั่ง 2026-09-18)
**scope = 13 ไฟล์ `feedback-*` (§R4.1(2)) + `MEMORY.md` + `reference-erfx-discipline-source` (เข้ามาโดย D1)** — ไม่ใช่ 23 `.md` ทั้ง directory
*หมายเหตุ: memory directory อยู่นอก git repo → "ไฟล์ที่แก้จริง" วัดด้วย mtime (`ls -lt --time-style=long-iso` 2026-09-18) ไม่ใช่ `git diff`*

| รายการใน §R4.7 ข้อ 6 | ไฟล์ตามแผน | mtime ที่วัดได้ | ตรงกันไหม |
|---|---|---|---|
| Dup 5 → why + pointer | `feedback-honest-reporting` | 2026-09-18 11:01 | ✅ |
| | `feedback-no-scope-creep` | 2026-09-18 11:00 | ✅ |
| | `feedback-root-cause-not-workaround` | 2026-09-18 11:01 | ✅ |
| | `feedback-verify-independence` | 2026-09-18 11:01 | ✅ |
| | `feedback-tool-selection` | 2026-09-18 11:01 | ✅ |
| ยกเว้น (ห้าม prune) | `feedback-measurement-discipline` | 2026-07-16 (ไม่แตะ) | ✅ ตรงตามข้อยกเว้น §R4.1(2)/F22 |
| frontmatter 2 ไฟล์ | `feedback-memory-governance` · `feedback-tool-selection` | 09-18 11:01 ทั้งคู่ | ✅ |
| D1 (§R4.3:340) | `reference-erfx-discipline-source` | 2026-09-18 11:01 | ✅ |
| index | `MEMORY.md` | 2026-09-18 11:01 | ✅ |
| **"ไฟล์ที่กฎย้ายออกแล้ว → เหลือ incident"** | `feedback-analyze-before-act`(M1) · `feedback-measurement-frame-fairness`(M3) · `feedback-doc-editing-discipline`(M4) · `feedback-fix-engine-not-excuses`(M5) · `feedback-claude-md-scope`(M6) | 09-03 · 07-08 · 07-07 · 07-07 · 06-27 — **ไม่มีไฟล์ใดถูกแก้ในรอบนี้** | ❌ **ยังไม่ทำ** |

- **สรุป:** รายการที่ทำแล้ว = Dup 5 · frontmatter 2 · D1 · index (8 ไฟล์ mtime 2026-09-18) · **รายการที่ยังไม่ทำ = การตัดกฎที่ย้ายเข้า `CLAUDE.md` แล้วออกจากไฟล์ต้นทาง M1/M3/M4/M5/M6 ให้เหลือ incident**
- **ไม่กระทบ acceptance #6** — เกณฑ์นั้นวัด *การคงอยู่* ของ keyword (13/13 พบ) ไม่ใช่การ prune · แต่ทำให้ **§R4.7 ข้อ 6 = executed บางส่วน** ต้องบันทึกตามจริง
- **ไม่แก้ในรอบนี้** — memory = runtime file · คำสั่งวินรอบ final verification จำกัดการแตะ runtime ไว้เฉพาะการแก้ provenance/ambiguity → **ยกเป็นข้อค้างให้วินตัดสิน** (ทำก่อน commit / แยกรอบ / ไม่ทำ)

### R4.10.2 `.claude/status/STATUS.md` — provenance (final verification วินสั่ง 2026-09-18)
| คำถาม | คำตอบจาก diff จริง |
|---|---|
| แก้เพราะ R4 requirement ข้อใด | **ไม่มี** — ไม่ตรงกับ R1–R4.9 ข้อใดเลย |
| อยู่ใน scope §R4.7 ตรงไหน | **ไม่อยู่** — §R4.7 ระบุ 7 รายการ ไม่มี `STATUS.md` · §R4.8 ข้อ 7 ก็ไม่ได้ลิสต์ `STATUS.md` ใน scan scope |
| runtime state ที่ตั้งใจ หรือไฟล์ค้างจากงานอื่น | **ไฟล์ค้างจากงานอื่น = AD-4 track** — เนื้อหา 2 บรรทัดที่เปลี่ยนคือความคืบหน้า AD-4 (commit spec `8271163` · ขั้น 2 implement เสร็จ · `ad4_card.py` v2 + `tp1_card.py` return_w · regress RG1-13/15 PASS · RG7 oracle 3/3 · RG14 W=50 กำลังรัน) ลงวันที่ 09-09 — **เกิดก่อน R4 (2026-09-18)** |

- **ไม่ revert** — คำสั่งวินคือ "revert เฉพาะส่วนของรอบนี้ โดยไม่แตะงาน AD-4 เดิม" · ตรวจแล้ว **ไม่มีส่วนของรอบนี้อยู่ในไฟล์เลย** ทั้ง 2 บรรทัดเป็น AD-4 ล้วน → การ revert = ทำลาย state AD-4 ที่ยัง uncommitted (ขัดคำสั่งเดียวกัน)
- **correction ของรายงานก่อนหน้า:** turn ก่อนผมลิสต์ `STATUS.md 2/2` รวมอยู่ใต้หัว "governance changes" ซึ่ง**ผิด** — เกิดจากการ filter ด้วย path `.claude/` ไม่ใช่ด้วยที่มาของการเปลี่ยน · แก้ที่ต้นทางแล้วในรายการไฟล์ของ §R4.10
- **ผลต่อ commit:** ไฟล์นี้ไม่ควรถูกรวมใน governance commit — **การจัด commit scope = คำสั่งวิน ยังไม่ตัดสินเอง**
