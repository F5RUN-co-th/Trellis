# /ledger — Research Claim Workflow (TRELLIS-010)

คำสั่งนี้คือ **ราง workflow บังคับ** ของงานบน LEDGER — ห้ามหลุดลำดับ ห้าม improvise
SoR = `Plan/TRELLIS-010_LEDGER.md` · validator = `Scripts/ledger_check.py` (field list ตัวจริง = `REQUIRED` ในไฟล์นั้น — ห้าม duplicate ที่นี่)

> **เขตแดนกับ `/trellis-010`:** การ**รัน experiment** อยู่ใต้ `/trellis-010` (test budget N/40 · lockbox · prediction-before-run เข้า Progress Log) — `/ledger` คือขั้น**บันทึก/ดูแล claim** หลังรันเสร็จ · ห้ามเล่ากฎการรันซ้ำที่นี่

## Pre-flight (บังคับทุกโหมด — ทำครบก่อนแตะงานใดๆ)

1. **อ่านสด (ห้ามใช้ความจำ):** `Plan/TRELLIS-010_LEDGER.md` — `## CURRENT FRONTIER` + `## CARRIED-FORWARD` + CLAIM block ที่เกี่ยวทั้ง block · **`.claude/status/STATUS.md`** (Current Stage / Blockers — งานต้องเหมาะกับ stage และไม่ทับเรื่องที่รอ Win)
2. **รัน `python Scripts/ledger_check.py`:**
   - **PASS → เริ่มได้ทุกโหมด**
   - **FAIL → เข้าได้เฉพาะ `fix` (ซ่อม) และ `status` (read-only)** — โหมดอื่น STOP รายงานวิน ห้ามทำ result-work บน ledger ที่เน่า
3. **mode↔status gate (จับการเดินโหมดผิดเชิงกลไก):**

   | โหมด | target ต้องเป็น | ไม่ตรง |
   |---|---|---|
   | `update` | `status: live` เท่านั้น | **STOP** — claim frozen แก้ผลไม่ได้ |
   | `close` | `live` (ปิดเต็มรูป) **หรือ** `frozen ∧ แก้ได้เฉพาะ lifecycle-metadata` (retroactive — ดู sub-case) | **STOP** |
   | `backfill` | claim ใหม่ หรือ live · เลข frozen + **commit-hash มีจริงใน history** | **STOP** — ไม่มี hash = ไม่ใช่ backfill |
   | `new` | ยังไม่มี claim ครอบผลนี้ (⚠ judgment ไม่ใช่ mechanical — ไม่แน่ใจ = ข้อ 4) | **STOP** — มีแล้ว = update/close |
   | `fix` | edit ไม่แตะผล/interpretation ใดๆ | เกินนั้น = โหมดอื่น |

4. **กำกวมว่าเป็นโหมดไหน** (คู่ที่เบลอบ่อย: fix↔update · backfill↔new · demote↔close) → พูดความเข้าใจ 1 บรรทัด รอวิน confirm ห้ามเดา

## Gate-tier (3 ชั้น)

- **Heavy (Engineer + 2-STOP: Engineer-finding → STOP วินตรวจ → Claude-Verify → STOP วินอนุมัติ):** `new` · `close` · `update` branch (b)
- **Light (ทำ → `ledger_check` PASS → รายงานวิน · ไม่ commit จนวินสั่ง):** `update` branch (a) · `backfill` · `fix`
- **Read-only:** `status`

## โหมด `update` — claim ที่ `status: live` มีผลรอบใหม่

**แตก 2 branch ก่อนเริ่ม — เลือกผิด = หลุด gate:**
- **(a) number-refresh** [Light]: เลขจาก `reproduce:` เปลี่ยน · interpretation เดิมทุกตัว
- **(b) interpretation-change** [Heavy]: แก้ `supported` / `not-yet-supported` / เลื่อน `evidence-level` — เลื่อน level ต้องผ่านเกณฑ์ **Evidence Promotion Protocol** (`Plan/TRELLIS-010_v3_offensive_reframe.md §9 — "EVIDENCE PROMOTION PROTOCOL"` · diversity ไม่ใช่ count) และมี Engineer ยืนยัน ไม่ใช่ Claude ตีตราเอง

| ขั้น | ทำ | ห้าม |
|---|---|---|
| 1 | รัน script จาก `reproduce:` → เลขจาก stdout เท่านั้น | ห้าม Claude พิมพ์เลขเอง |
| 2 | Edit **เฉพาะ block นั้น** ตาม branch · `correction-lineage` +1 ถ้าเป็นการแก้ | ห้ามแตะ block อื่น |
| 3 | update **FRONTIER row หรือ CARRIED-FORWARD entry** — แล้วแต่ claim ปรากฏที่ไหน (ไม่มีทั้งคู่ = tooling claim → ข้ามได้ ระบุเหตุ) | |
| 4 | `ledger_check` → PASS | |
| 5 | รายงานวิน + **ตาราง compare กับผลรอบก่อน** (Working Rule 9 · tooling ไม่มีเลข = ระบุเหตุ) | ไม่ commit จนวินสั่ง |

## โหมด `close` — ปิด claim [Heavy]

| ขั้น | ทำ | gate |
|---|---|---|
| 1 | เช็คว่าถึงจุดตัดสินจริง (เกณฑ์ pre-registered / seed-robust) — ยังไม่ถึง = **ห้ามปิด** | |
| 2 | Engineer adversarial review รอบสุดท้าย | **STOP วินตรวจ finding** |
| 3 | Claude Verify ทุก finding ด้วย evidence | **STOP วินอนุมัติ** |
| 4 | `status:` → `terminal` / `FALSIFIED` / `INCONCLUSIVE` / `DEAD-do-not-rerun` (token นำหน้า — check j) · เขียน **`scope-of-death`** ชัด (ตายแค่ไหน ไม่เกิน) · `supported` = ข้อสรุปสุดท้าย · lineage ปิดท้าย commit-hash | |
| 5 | FRONTIER row / CARRIED entry → สถานะปิด · **cite ตาม status:** `terminal` → `[CLAIM-N]` bare · `DEAD` → `[CLAIM-N DEAD]` · `FALSIFIED`/`INCONCLUSIVE` → **ห้าม bracket-cite** (check (h) ไม่มี escape — ใช้ prose ไม่มี bracket เหมือน sub-case demote) | |
| 6 | `ledger_check` PASS → รายงานวิน | commit เมื่อวินสั่ง · **หลัง commit = frozen — ผล/interpretation แก้ย้อนไม่ได้** |

**Sub-case: retroactive demote** — พบ leak/invalid ย้อนหลัง**โดยไม่มี experiment ใหม่** (precedent: CLAIM-0006 leak `v1:122` · doctrine: EVIDENCE LIFECYCLE `reframe §9 "Promote/Freeze/Demote/Retire"`) · ยังเป็น [Heavy]:
- **target `live`** → demote in-place: `status:` → `INCONCLUSIVE` + lineage บันทึกเหตุ
- **target `frozen` + มี/สร้างตัวแทนได้** → supersede-flip: `status:` → `superseded→CLAIM-ตัวแทน` (แตะแค่ status — ตัวแทนเปิดผ่านโหมด `new`)
- **target `frozen` + ไม่มีตัวแทน** → demote-in-place จำกัด **lifecycle-metadata เท่านั้น**: `status:`→`INCONCLUSIVE` · `evidence-level`→`L0` · เหตุลง `correction-lineage` — **ห้ามแตะ observed / supported / not-yet-supported** (บันทึกประวัติ frozen)
- **frontier ของ claim ที่ demote:** **reopen row** (ข้อสรุปถูก retract = hypothesis กลับ open) + บันทึก provenance เป็น **prose ไม่มี bracket** (เช่น "prev eliminated by CLAIM-0010 → retracted-leak → reopen") — ห้ามใส่ bracketed cite ของ claim ที่ demote (check (h) ไม่มี escape ให้ INCONCLUSIVE)

## โหมด `new` — เกิดงานวิจัยใหม่ [Heavy]

| ขั้น | ทำ | กลไกกันลืม |
|---|---|---|
| 0 | Working Loop เต็ม: design + **pre-register เกณฑ์ผ่าน/ตายก่อนรัน** → Engineer finding → **STOP วินตรวจ** → Claude Verify → **STOP วินอนุมัติ** · **การรันอยู่ใต้ `/trellis-010`** (budget/lockbox/prediction) | ห้ามเขียน script ก่อนอนุมัติ (CRITICAL) |
| 1 | เขียน `Scripts/<ชื่อ>.py` → รัน | ห้ามขยับเกณฑ์หลังเห็นผล |
| 2 | เปิด `### CLAIM-ใหม่` field ครบ (= `REQUIRED`) + field-tag สนามวัดเสมอ | check (c) จับ field หาย |
| 3 | FRONTIER: เพิ่ม/ปรับ row | check (d) จับ cite dangling |
| 4 | SCRIPT INDEX: `--emit-index` → เติม disposition | check (a)/(f) FAIL ถ้า script ไม่อยู่ index |
| 5 | หักล้างของเก่า: **iterate ทุก claim ที่โดน** — เก่า `status:` → `superseded→CLAIM-ใหม่` · frontier cite → `[เก่า→ใหม่]` | check (i)/(j) บังคับ arrow ตรง status |
| 6 | `ledger_check` PASS → รายงานวิน · **script + LEDGER = commit เดียว (DoD)** | commit เมื่อวินสั่ง |

## โหมด `backfill` — บันทึกเลข frozen (transcription-only) [Light]

**trigger แยกจาก `new`:** เลข**ที่ commit ไว้แล้ว** (frozen + hash) → `backfill` · ต้องรันสดตอนนี้ → `new`
เงื่อนไข (LEDGER:5): เลข frozen + **commit-hash ที่ commit แล้ว** · **ห้าม re-run/re-derive** · `verified-by[self]` · fairness field-tag ตามต้นทาง
ขั้น: transcribe เข้า block (ใหม่หรือเดิม) → FRONTIER/CARRIED ถ้ามี → `ledger_check` PASS → รายงานวิน

## โหมด `fix` — non-result edit (typo / cite/arrow ที่พัง / pointer) [Light]

- **โหมดเดียว (นอกจาก `status`) ที่เข้าได้เมื่อ `ledger_check` FAIL** — เพราะทำได้เฉพาะ non-result edit
- **ขอบเขต:** ซ่อม malformation/dangling เท่านั้น — **ย้าย arrow-target ไป claim อื่น = interpretation ไม่ใช่ fix** · structural ใหญ่ (เช่น closure ทั้งชุด) = Working Loop เต็ม
- **เงื่อนไขจบ (anti-masking · Working Rule 8):** `ledger_check` กลับเป็น **PASS** + report **ทุก FAIL ที่เจอ พร้อม root-fix ที่ทำ** (ไม่ใช่แค่ "PASS แล้ว" — ลบ cite ทิ้งให้เขียวโดยไม่วินิจฉัย = masking ห้าม) · ซ่อมแล้วยัง FAIL = STOP รายงานวิน
- **DoD-exempt:** non-result edit ไม่ trigger กฎ CLAIM+FRONTIER-same-commit

## โหมด `status` (หรือว่าง) — read-only

รายงานอย่างเดียว ไม่แก้อะไร (เข้าได้แม้ ledger FAIL): สรุป FRONTIER (open/eliminated) + CARRIED + claim ล่าสุด + ผลรันสด `ledger_check` — **dashboard สถานะ claim ตัวจริง** (ตาราง STATUS.md บอกแค่ pipeline-activity ✅/▶)
**optional reproduce-verify:** รัน `reproduce:` ของ claim เพื่อยืนยันว่ายัง reproduce ได้ (ไม่แก้อะไร) — **เลขไม่ตรง = escalate เป็น defect ทันที** ห้ามผ่านเงียบ

## Guardrails (ทุกโหมด · ตลอดการทำงาน)

- **script เป็นเจ้าของตัวเลข** — ทุกเลขรันสด + ติดป้ายสนามวัด (sim/tester) · **ยกเว้น `backfill` = transcription-only** (frozen number + committed hash · LEDGER:5)
- **แตะ experiment = update CLAIM + FRONTIER/CARRIED ใน commit เดียวกัน** (DoD · CLAUDE.md) — `fix` = exempt (non-result)
- **`ledger_check` FAIL กลางทาง = แก้ให้ PASS ก่อน report** — ห้ามรายงานทับ FAIL ห้ามปล่อยค้าง
- **ติดขั้นไหน = หยุดรายงานวินที่ขั้นนั้น** — ห้ามข้ามขั้น ห้ามสลับลำดับ ห้ามตีความเอง

> out-of-scope ที่ log ไว้ (งานแยก · ไม่ fold): check (h) escape vocabulary ไม่มี annotation สำหรับ falsified/inconclusive (latent — จำเป็นเฉพาะถ้าต้องการ bracketed cite ของ claim ที่ demote)
