# /trellis-010 — Resume Brain Research Workflow (TRELLIS-010)

คำสั่งนี้คือ **พิธีเปิดงานบังคับ** ของ workflow วิจัยสมอง — แผนตัวจริง/สถานะจริงอยู่ใน `Plan/TRELLIS-010_brain_research_workflow.md` เท่านั้น (ห้าม duplicate ที่นี่)

## Pre-flight (บังคับ — ทำครบก่อนแตะงานใดๆ)

1. **อ่านสด (ห้ามใช้ความจำ):**
   - `Plan/TRELLIS-010_brain_research_workflow.md` ทั้งไฟล์ **รวม Progress Log ท้ายไฟล์**
   - `.claude/status/STATUS.md`
   - `CLAUDE.md` §⭐ Verify≠Self-grading + §กฎการทำงาน 8/8.1
2. **รายงานสถานะก่อนเริ่ม:** ตอนนี้อยู่ Stage ไหน · Gate ล่าสุดผ่าน/ค้างอะไร · test budget ใช้ไป N/40 · lockbox 2024–26 ยังสะอาดไหม
3. **Guardrails ที่ห้ามละเมิดตลอดการทำงาน:**
   - ทุก hypothesis: **ประกาศ prediction ก่อนรัน** · ผล falsify = บันทึกเป็นผลงาน
   - ทุกตัวเลขที่เขียนลงเอกสาร: รันสดจาก script + ติดป้ายสนามวัด (sim/tester)
   - lockbox 2024–26: ห้าม signal/threshold selection · ศึกษา execution-fidelity ได้ (Stage 0)
   - ทุก test ที่รัน: +1 เข้า budget ใน Progress Log ทันที
4. **ทำเฉพาะ Stage ปัจจุบัน** — ถึง Gate → Engineer adversarial review → Claude Verify → **หยุดรอวิน**

## จบ session ทุกครั้ง

ต่อท้าย Progress Log: Stage/งานที่ทำ · tests ที่ใช้ (สะสม N/40) · findings รวมที่ถูก falsify · สิ่งที่ต้องทำต่อ — ให้ session ถัดไปอ่านแล้วทำต่อได้โดยไม่ตีความ
**บันทึกผลเป็น claim เข้า LEDGER → ใช้ `/ledger`** (คำสั่งนี้ = รัน experiment ใต้ budget/lockbox · `/ledger` = บันทึก/ปิด/แก้ claim)

## Argument (ถ้ามี)

- `status` — รายงานสถานะ (ข้อ 2) อย่างเดียว ไม่เริ่มงาน
- ว่าง — pre-flight แล้วทำงาน Stage ปัจจุบันต่อ
