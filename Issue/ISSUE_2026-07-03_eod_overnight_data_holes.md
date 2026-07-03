# ISSUE 2026-07-03 — EOD 23:00 ไม่ fire ช่วง DST-shoulder/วันหยุด + Dukascopy data holes

**สถานะ:** Issue 1 = **PARTIALLY RESOLVED 2026-07-04** (sim-side fixed) · Issue 2 = OPEN (งาน Stage A)
- ✅ **sim-side (C1):** `stage0_join.run_detailed(ea_catchup=True)` mirror `Trellis.mq5:279` แล้ว —
  validated เทียบ EA จริง v4f_25: common 149/149, flips 0, drift +0.144/ไม้ · baseline H0 ใหม่รันจากสนามนี้
- ⏳ **ยังเปิด (design question):** ตัว EA เอง**ยังถือข้ามคืนจริง** ~10+ วัน/ปี (catch-up ปิดวันถัดไป = กิน
  overnight gap เต็มๆ ระหว่างนั้น) — จะแก้ EOD ให้ปิดก่อนตลาดปิดจริง (NY-anchored) หรือยอมรับ risk
  = การเปลี่ยนระบบ ต้อง sim 15.5 ปี + WF ใหม่ · รอวินจัดคิว
**พบโดย:** invariant check ใน `Scripts/stage0_join.py` (self_check) — Engineer review LOW-6 → Claude implement

## Issue 1 — "ไม่มีไม้ข้ามคืนโดยโครงสร้าง" (TRELLIS-009 §2) เป็นเท็จช่วง shoulder weeks + วันหยุด US

**Evidence (จาก script, sim 2023–2026, 20 ไม้ถือข้ามคืน):**
- Cluster ตรงช่วง DST-shoulder เป๊ะ: มี.ค. 2023 ×3 · 1–2 พ.ย. 2023 ×2 · มี.ค. 2025 ×5 · 27 ต.ค. 2025 ×1
- วันหยุด US: Presidents' Day 2023-02-20 · MLK 2024-01-15, 2025-01-20 · Good Friday 2024-03-28 (ถือ 4 วัน!) · Christmas 2024-12-24 · Labor Day 2025-09-01
- ไม้ที่ยาวสุด: 2023-11-23 → 11-27 (4 วัน, Thanksgiving) · 2024-03-28 → 04-01 (4 วัน)

**กลไก (root cause ไม่ใช่ symptom):** ตลาดทองปิดตาม NY 17:00 · BT-clock = EET กฎ EU →
ช่วงที่ US DST on แต่ EU off (~2+1 สัปดาห์/ปี: ~9–30 มี.ค. + ~26 ต.ค.–2 พ.ย.) NY close 21:00 UTC
= **22:59 BT** → ไม่มี bar/tick ชั่วโมง 23 → เงื่อนไข EOD `hour >= 23` ไม่เกิด ทั้ง sim
(`dual_asian_sim.py:71`) และ EA (C_EOD บน BT-clock) → ถือข้ามคืนจนโดน stop/EOD วันถัดไป
วันหยุด US ปิดเร็ว (13:00 ET) = เคสเดียวกัน

**ผลกระทบ (แก้ 2026-07-04 หลัง Gate 0 v4f — claim "สมมาตร" เดิมถูก falsify):**
overnight/weekend gap risk ที่ design อ้างว่าตัดทิ้งแล้ว ยังมีจริง ~10+ วัน/ปี · และมัน
**ASYMMETRIC ระหว่าง sim กับ EA** (Engineer จับได้จาก v4f + Claude verify ด้วย attribution):
- EA: catch-up ปิดไม้ค้างที่ tick แรกของวันใหม่ (`Trellis.mq5:279`) → วันนั้น**เข้าไม้ใหม่ได้**
- sim: ถือถึง stop/EOD 23:00 ของวันถัดไป → วันนั้น**เข้าไม้ใหม่ไม่ได้** (single position)
- Quantified บน v4f_25 (2025): drift จากวัน hold-entry 8 วัน = **−$90.8** + tester-only
  re-entries 4 วัน (01-21, 03-18, 03-28, 09-02 — ทุกวันคือ exit-day ของ hold) = **+$48.0**
→ sim ไม่ mirror EA จริง ~12 วัน/ปี · การ reconcile sim ให้ตรง EA catch-up = งาน stage ถัดไป
(ห้ามแก้กลาง Gate — จะทำลาย canonical equivalence ที่ verify แล้ว)
กระทบเพิ่ม: (1) ความถูกต้องของ claim §2 (2) live จะถือข้ามคืนวันเหล่านี้จริง (กิน overnight gap)

**แนวทางแก้ที่เป็น root cause (รอวินสั่ง — ห้าม quick fix):** EOD ต้องนิยามจาก "ใกล้ปิดตลาดจริง"
ไม่ใช่ชั่วโมงตายตัวบน BT-clock — เช่น EOD = 22:45 BT ช่วง shoulder/holiday-aware หรือผูกกับ
NY-close โดยตรง (ตลาดปิด NY 17:00 เสมอ) · ต้อง sim ซ้ำทั้ง 15.5 ปี + WF ก่อน adopt
(เปลี่ยน exit timing = เปลี่ยนระบบ)

## Issue 2 — Dukascopy M1/tick data holes (คุณภาพ data ต้นทาง)

**Evidence:** `XAUUSD_M1_2023.csv` — 2023-11-15 12:59 → 2023-11-17 07:00 (**หาย 42 ชม.
กลางสัปดาห์ปกติ**) + 17 พ.ย. รูย่อย 07:59→18:00, 18:59→23:00 · (สแกนเต็มทุกปียังไม่ทำ —
ต้องทำก่อน Stage A ใช้ day-level dataset)

**ผลกระทบ:** วันที่มีรู = day_facts/MFE-MAE เพี้ยนเงียบๆ ถ้าไม่ flag · Stage A (A1 day dissect)
ต้องมี gap detector + exclude/flag วันที่ data ไม่ครบ

## โยงกลับ
- พบระหว่าง: TRELLIS-010 Stage 0 (clock-bug investigation) — ดู Progress Log ใน Plan/TRELLIS-010
- เครื่องมือที่จับได้: `Scripts/stage0_join.py` self_check invariants (fail-loud ตาม CLAUDE.md
  "ตรวจเครื่องมือตัวเองด้วย")
