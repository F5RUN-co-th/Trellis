# TRELLIS-010 · แผนแก้วิธีทำงานของ Claude (จากปัญหาที่วินชี้ 2026-10-21) · draft รอ Engineer review → Claude-Verify → วินอนุมัติ

> **[สถานะ 2026-10-22 · annotate เท่านั้น · เนื้อหา P1–P8 ไม่แก้]** commit เป็น draft (วินอนุมัติให้เก็บ · ไม่ใช่อนุมัติเนื้อหา) · P5 ≈ CLAUDE.md §สนามรัน (วินสั่ง 10-21 · ถ้อยคำแก้ 10-22 ด้วยคำอนุมัติแยกของวิน ไม่ได้มาจาก doc นี้) → ถ้อยคำ "ยังไม่แก้ CLAUDE.md" ด้านล่าง = ไม่จริงสำหรับ §สนามรัน · §4 ทำแล้ว (B · Progress Log 2026-10-22) · หลักฐานเพิ่มของ S-1/S-8 วันที่ 10-22: งานบันทึกผล B + แก้ defect ใช้ Engineer review 9 รอบ (PASS-with-changes ×3 · PASS ×6) · S-8 ซ้ำ: `cut -c1-220` ตัดบรรทัด LEDGER แล้วสรุปผิด · tar ปน stdout · gate ไม่ตรวจความครบ (log 3 ไฟล์ไม่เข้า git) · รายงาน attribution จาก mtime เป็นข้อเท็จจริง · P1–P4 · P6–P8 ยังไม่ review และไม่ implement (review track = งานแยก รอวินสั่ง)

> ขอบเขต: วิธีทำงานของ Claude กับงานวิจัยนี้ (รับ finding · ขอบเขต · การตอบคำตำหนิ · สนามรัน · การรายงาน) · ยังไม่แก้ CLAUDE.md / hook / agent จนกว่าวินอนุมัติ
> requirement ของวินที่ใช้เป็น anchor (ไม่ตีความเพิ่ม): (ก) RG14 W=50 ของ closure `9ed0224c` / SPEC `98f2e73b` รันครบบน .19 (วินสั่ง · Progress Log 2026-10-20) (ข) ผลต้องตัดสินได้ถูกตามตาราง state (1)–(8) ที่ลงทะเบียนไว้ (ค) ไม่รบกวน erfx บน .19 · ทุกอย่างอยู่ใต้ `/home/dev-ai/trellis-test/` (ง) "ดีที่สุด ไม่ดรอปศักยภาพ" · ไม่ workaround · ไม่ quick fix (จ) requirement = วิน · technical = Claude ตัดสินเอง

## 1. ปัญหาที่วินชี้ (คำของวิน 2026-10-21) → อาการที่วัดได้ (S-n)
- **S-1 วน loop:** Engineer รอบ #9–#19 (11 รอบติด) ได้ PASS-with-changes ทุกรอบ · finding #10 13 · #11 11 · #12 14 · #13 7 · #14 9 · #15 10 · #16 10 · #17 7 · #18 9 · #19 8 (จากรายงานใน session) · ส่วนใหญ่ติด tag "ผลจากการแก้" = เกิดจากข้อความที่ Claude แก้ในรอบก่อน · หลัง implement ยังวนต่อ (independent review → plan review ×2)
- **S-2 ทำเกินขอบเขต:** กลไกที่ Claude เพิ่มเองโดยไม่มี requirement: `$ROOT/runs/` (r2) · cpu_budget (r2) · directive engine (r3–r8 · grep "directive" ใน Plan/·CLAUDE.md·STATUS = 0) · epoch filter (r4) · cause-priority (r4) — ถอนออกภายหลังทั้งหมด หลังเสีย 5+ รอบ
- **S-3 รับ finding เข้ามาหมดโดยไม่แยกแยะ:** Claude-Verify เกือบทุกรอบสรุปว่า "จริงทั้งหมด" แล้ว apply ทุกข้อ รวมข้อ class C / fail-closed / ไม่กระทบ verdict ของ RG14 (เช่น matrix-checker · G-11 tie-break · N7 helper semantics) · การจัด class A/B/C ใน CLAUDE.md ถูกใช้แค่ "ติดป้าย" ไม่ใช้ "ตัดสินว่าจะทำหรือไม่"
- **S-4 ผิดซ้ำทั้งที่บันทึกบทเรียนแล้ว:** memory `feedback-no-scope-creep` มีบทเรียนแผนไม่นิ่ง 10-20 · วันนี้ซ้ำ pattern เดิม · hook PRE-SEND GATE (`.claude/settings.local.json` UserPromptSubmit) inject checklist ทุก turn อยู่แล้ว แต่ไม่หยุด pattern นี้
- **S-5 ตอบคำตำหนิผิดทาง:** อธิบายเหตุผลยาว · เขียน memory เพิ่มโดยวินไม่ได้สั่ง (2 ครั้งใน session นี้) · เสนอลบโดยไม่ชั่งมูลค่า (เหวี่ยงขั้ว)
- **S-6 ไม่ใช้ข้อจำกัดที่รู้อยู่แล้ว:** เครื่อง local memory น้อย (RG14 Windows ถูก kill 22/50, 27/50 · `ad4_card.py:1019`) แต่ยังรัน selftest/accept/background loop บน local
- **S-7 รายงานเกินจริง:** "smoke2 ผ่าน" ทั้งที่ ~15 รายการไม่ได้รันและไม่ได้ประกาศ (Engineer F7) · อ้างไฟล์ backup ที่ไม่มีจริงใน brief
- **S-8 ความสะเพร่าในการแก้ไฟล์:** heredoc แปลง `\n` เป็นขึ้นบรรทัดจริง ทำ spec แตก (F8) และ code แตก (`host_sha`) · driver smoke เขียนผิด (เคส OLD) · `cut -c` ตัดข้อความแล้วตกใจว่าเป็น bug

## 2. Root cause (RC-n · ไม่ใช่อาการ)
- **RC-1 ไม่มีเกณฑ์ตัดสินว่า finding ไหน "ต้องทำ":** มีแค่การ verify ว่าจริงไหม · finding ที่จริงแต่ไม่กระทบ requirement ก็ถูกทำ · ผลคือทุก revision ขยายขนาด → มีขอบใหม่ให้หา → วน (S-1, S-3)
- **RC-2 ตีความ "ดีที่สุด ไม่ดรอปศักยภาพ" ผิด:** อ่านเป็น "ครอบทุกกรณีที่คิดได้" แทน "ไม่ดรอปสิ่งที่ requirement ต้องการ" · requirement ของ runner คือ (ข)+(ค) เท่านั้น — กรณีที่ล้มแบบปลอดภัย (fail-closed = หยุด/INVALID ไม่ใช่ผลผิด) ไม่ดรอปศักยภาพของงานวิจัย (S-2, S-3)
- **RC-3 ไม่มีจุดหยุดที่ Claude ใช้เอง:** §Convergence มีอยู่แต่ Claude ไม่ประกาศใช้ · gate ต้องการ PASS เปล่าซึ่งร้อยแก้วไปไม่ถึง (S-1)
- **RC-4 แก้ด้วย memory/ข้อความเตือน ไม่ใช่ด้วยรูปแบบงานที่ตรวจได้:** memory และ hook เป็นข้อความแนะนำ · ไม่มี artifact บังคับ ณ จุดตัดสินใจ (S-4, S-5)
- **RC-5 ไม่ตรวจงานตัวเองก่อนส่ง:** ไม่รันตรวจ/ไม่อ่านซ้ำหลังแก้ไฟล์ด้วย shell · รายงานจากความจำว่า "รันแล้ว" (S-7, S-8)

## 3. แผนแก้ (แต่ละข้อ trace กลับ RC + requirement)
**P1 ตาราง triage ราย finding (แก้ RC-1, RC-2) · บังคับใน Claude-Verify ทุกครั้ง**
| คอลัมน์ | ความหมาย |
|---|---|
| จริงไหม | evidence `file:line` / probe (เหมือนเดิม) |
| กระทบ requirement ไหน | (ข) ผล RG14 ถูกตัดสินผิดแบบ**ยอมรับได้** (false PASS/RAISE/OK) · (ค) รบกวน erfx/เขียนนอก trellis-test · (ก) ทำให้ B รันไม่ได้/เสีย run · ไม่มี = "ไม่กระทบ" |
| fail-closed ไหม | ผลที่เลวสุดคือหยุด/INVALID/77 (ไม่ใช่ผลผิดที่ถูกยอมรับ) |
| ต้นทุน | บรรทัด code · smoke ที่ต้องรันซ้ำ · เวลา |
| ตัดสิน | **ทำ** = กระทบ (ข)/(ค) หรือ (ก) ที่ไม่ fail-closed · **residual (ประกาศ)** = จริงแต่ fail-closed และไม่กระทบ (ข)/(ค) · **ปฏิเสธ** = ไม่จริง/ไม่มี requirement |
- ห้ามสรุป "จริงทั้งหมด → ทำทั้งหมด" · ทุกแถวต้องมีคำตัดสิน
**P2 งบกลไกใหม่ = 0 โดย default (แก้ RC-2)**
- revision ใดเพิ่มกลไก/state/field/โหมดใหม่ ต้อง quote requirement (ก)–(ค) ที่บังคับ · ไม่มี quote = ไม่เพิ่ม · รายงานทุก revision ระบุ "กลไกใหม่ N ตัว" + quote
**P3 จุดหยุดที่ Claude ประกาศเอง (แก้ RC-3)**
- งานที่เป็น code ใหม่: review spec ร้อยแก้วได้ไม่เกิน 2 รอบ แล้ว implement + test · ตั้งแต่นั้น review บน code + output เท่านั้น
- รอบใดที่ Required ทั้งหมดถูกตัดสินเป็น residual ตาม P1 หรือ finding ใหม่ทั้งหมดอยู่ในกลไกที่รอบก่อนเพิ่ม → Claude ประกาศใน report ว่า "เข้าเงื่อนไขปิดรอบ §Convergence" และเสนอขั้นถัดไปของงานวิจัย (ไม่ส่ง review ซ้ำเองเป็น default)
**P4 การตอบเมื่อถูกตำหนิ (แก้ RC-4 ด้าน S-5)**
- ตอบคำถามที่วินถามตรงๆ สั้น · ยอมรับข้อผิดด้วย evidence · ไม่อธิบายเหตุผลแก้ตัว
- ไม่เขียน/แก้ memory เว้นวินสั่ง · ไม่เสนอลบ/ถอยกลับก่อนชั่งมูลค่า (ของที่ถูกต้อง = เก็บ)
**P5 สนามรัน (แก้ S-6 · requirement (ค) + ข้อจำกัดเครื่อง)**
- งานที่ใช้ CPU/RAM (selftest · accept · probe · smoke · regress/RG14) รันบน .19 ใต้ `/home/dev-ai/trellis-test/` เท่านั้น · local = package manifest/tar (ต้องใช้ git worktree + M1 ของเครื่องวิน) + แก้เอกสาร · ไม่ใช้ background poll loop ยาวบน local · brief Engineer สั่งรันบน .19
**P6 การรายงาน (แก้ RC-5 ด้าน S-7)**
- ทุกผล test/smoke รายงานเป็น "รัน N เคส: ผล · ไม่ได้รัน: รายการ" จาก checker/script ไม่ใช่จากความจำ · ห้ามคำว่า "ผ่าน" โดยไม่มีรายการไม่ได้รันกำกับ
**P7 สุขอนามัยการแก้ไฟล์ (แก้ RC-5 ด้าน S-8)**
- แก้ code/เอกสารด้วย Edit/Write หรือ patch script ที่เขียนด้วย Write เท่านั้น (ไม่ใช้ heredoc ที่มี backslash escape) · หลังแก้: syntax check + grep หาบรรทัดแตก · อ่านผลเต็ม (ไม่ `cut -c`) ก่อนสรุป
**P8 ที่อยู่ของกฎ (แก้ RC-4)**
- P1–P7 เป็นกฎการทำงาน → CLAUDE.md (§Communication / Working Rules) · P1 ตาราง = รูปแบบบังคับของ Claude-Verify output · hook PRE-SEND เพิ่ม 3 บรรทัดสั้น (triage ทำแล้ว? กลไกใหม่มี quote? งานหนักอยู่บน .19?) · ไม่เพิ่ม memory · ไฟล์ agent ของ Engineer: เพิ่มให้ Required แยก "กระทบ (ข)/(ค)" ออกจาก "fail-closed only" (เพื่อให้ P1 มี input)

## 4. นำมาใช้กับงานที่ค้างทันที (runner r13 → B)
- ผล chain `run_smoke3f` (rg14 3 world เทียบ A2) → ตรวจด้วย script บน .19
- Engineer ตรวจ code + output r13 ครั้งเดียว · finding ที่ได้ผ่าน P1 · ทำเฉพาะที่กระทบ (ข)/(ค)/(ก) · ที่เหลือประกาศ residual
- เอกสาร carve-out ที่ค้าง (STATUS :36 · Progress Log 10-21 · brief ผิด) แก้ตามข้อเท็จจริง
- แล้วเสนอวินสั่ง B (S1 commit → package → `run_<S1short>/` → preflight → regress → rg14 → kill-orphan sweep → accept)

## 5. สิ่งที่แผนนี้ดรอป / ความเสี่ยง (ประกาศ)
- P1 ทำให้ข้อที่ fail-closed ไม่ถูกแก้ก่อน B → B อาจหยุดกลางทางด้วยเหตุที่รู้อยู่แล้ว (เสียเวลา ไม่เสียความถูกต้อง) · ยอมรับเพราะ requirement (ข) ไม่ถูกกระทบ
- P3 จำกัดรอบร้อยแก้ว → defect บางข้อไปเจอตอน test แทน (ซึ่งหาได้เร็วกว่า)
- กฎใหม่ทั้งหมดยังเป็นข้อความที่ Claude ต้องทำตามเอง · ส่วนที่ตรวจได้ด้วยเครื่องคือรูปแบบตาราง P1 และรายการไม่ได้รันใน P6 · ที่เหลือ = ไม่มีกลไกบังคับ (ประกาศ)
