# TRELLIS-010D — Stage D Brain v1: Implementation Plan (ภายใต้ TRELLIS-010)

**วันที่:** 2026-07-05 · **v1.1** (ผนวก Engineer review MC-1..MC-6 — ดู changelog ท้ายไฟล์) · **สถานะ:** Engineer PASS-with-changes + Claude Verify ครบ + **D-0/D-0.5 รันแล้ว — gate ยิง: SKIP-only = documented-dead → เดิน WS-3/WS-2**
**Authority:** เอกสารนี้อยู่ใต้ `TRELLIS-010_brain_research_workflow.md` (doctrine หลัก) — ขัดกันเมื่อไหร่ TRELLIS-010 ชนะ · ทุกเลขในเอกสารนี้มาจาก script ที่ rerun ได้ + ผ่านการตรวจ ≥2 ชั้น (ระบุสนามวัดกำกับ)

---

## 1. ปัญหาที่พบ (ฐานของแผนนี้ — ทุกข้อมี evidence ใน Progress Log)

### 1.1 ปัญหาเชิงกลยุทธ์ (จากผลทดสอบ 8 ใบ, budget 8/40 — clean-room CONFIRMED ทั้งหมด)
| ปัญหา | หลักฐาน | ผลต่อแผน |
|---|---|---|
| **P-A: filter สถิตย์ตัวเดียว "ผ่านไม่ได้โดยดีไซน์"** — day-type เดียวกันแบกทั้งขาดทุนปีแพ้และกำไรปีชนะ | 8 ใบ falsified · C3 gate พลิกปีแพ้ +228 แต่ฆ่า 2020 −256 · C6 ช่วยปีแพ้ 59% แต่จ่ายปีชนะเกิน · C9 pooled +583 แต่ช่วยปีแพ้แค่ 32% | เลิกหา single-filter → **conditional behavior** (Stage D) |
| **P-B: สัญญาณมีจริงแต่อยู่ที่ conjunction ไม่ใช่ตัวแปรเดี่ยว** | poke ⊥ overshoot (corr −0.081) · เซลล์ขาดทุนแท้ = **SPENT∧POKED −0.581/ไม้ (n=103)** เล็กและเฉพาะ (สนาม search, post-hoc cell — ใช้เป็น hypothesis ไม่ใช่ selection target) | brain v1 = state grid 2 แกน |
| **P-C: RED FLAG survival-vs-edge ยังเปิด** — cap/trail กลืน edge ปี vol สูง | real-tick 2026: uncapped +160 → capped +4.3 → **−9.3** | ด่านตัดสิน = **สนาม CONFIRM (capped+real-tick)** + exit-axis rev-2 (#10) |
| **P-D: แกน exit/management = 0 การทดสอบ** ทั้งที่มี T-STRONG รองรับ | audit Gate C (#7 time-stop Osler · #9 depth · #10 let-winners-run) | workstream แยก (WS-3) |
| **P-E: era-nonstationarity โผล่ซ้ำ** (sign-flip 2012-14 vs 2015+) | C7 PS แยกยุค · discovery-regimes T-CARD | risk register + WF ต้องคร่อมยุค |

### 1.2 ปัญหาเชิงกระบวนการ (เกิดจริงใน workflow — fix ถูก institutionalize แล้ว)
| ปัญหา | fix ถาวร (ที่ไหน) |
|---|---|
| Glossary slip: entry bar i ≠ signal bar j → lookahead C7 v1 (Engineer จับก่อนรัน) | CLAUDE.md §Glossary เวลาเทรด + memory measurement-discipline |
| "มั่นใจว่ารู้แล้ว→ข้ามวัดซ้ำ" เกิดซ้ำ (เลข 1-8/ปี ที่ binning ผิด) | memory pattern + กติกา "ทุกเลขชี้ tool-call ใน session" |
| SE เปิดดู conditional P&L ระหว่าง review C9 (leak) | ป้าย leak ถาวรใน log · **prompt hardening (§7.3)** · การแก้หลัง leak ต้อง tightening-only |
| Pipeline แก้กลางทางไม่ลง log ทันที + ไม่มี git trail | commit ต่อ milestone (§7.1) · Progress-Log-ก่อน-report |
| LLM ให้คะแนน/เลือกเอง | EchoSeven pattern: script เป็นเจ้าของตัวเลข/tier ทุกจุด |

## 2. ความต้องการของวิน (requirement anchors — ห้าม scope creep เกินนี้)
1. **R1:** EA เข้าใจสาเหตุการเคลื่อนแล้วปรับพฤติกรรม — ห้ามแก้แบบหลบ (กฎ 8.1)
2. **R2:** ทุนน้อยต้องรอดเอง — พิสูจน์ที่ deposit จริง (3000/1000) ไม่ใช่เพิ่มทุนกันชน
3. **R3:** ผลทุกอย่างพิสูจน์บนสนาม CONFIRM (capped + real-tick tester) ก่อนเรียก edge (MED-1)
4. **R4:** ไม่ทิ้ง hypothesis ที่ยังให้บทเรียนได้ (precedent คำตัดสิน C9 Option A) — แต่ทุกการเผา budget ต้องมี interpretation guide ล่วงหน้า
5. **R5:** Verify ≠ self-grading — ทุกผลสำคัญผ่าน 3 ชั้น (self → data-path independent → clean-room adversarial)
6. **R6:** เกณฑ์สำเร็จ = §0 ของ TRELLIS-010 เต็ม (ปีแพ้ ≥50% · ปีชนะ ≤20% · pooled ≥30% · worst ≥ −150 · WF OOS · lockbox แตะครั้งเดียวตอน validate จบ)

## 3. WS-1 (หลัก): Stage D Brain v1 First-Scope — "CONTINUATION vs SKIP"

### 3.1 Design (frozen ex-ante)
- **Classifier (rule-based, โปร่งใส):** state grid 2 แกนจาก features ที่ freeze แล้ว
  - แกน 1: `poked` (pierce-close-inside ≤60min ก่อน close ของ j — SHA 71054c06)
  - แกน 2: `dc_state` FRESH/SPENT ที่ os=1.0δ, δ=0.5×asian_width (SHA 2ed4ca67)
  - **thresholds ทุกตัว frozen จาก Stage C — ห้าม re-optimize ใน WF (F7)**
- **Behavior set v1 (2 อย่างเท่านั้น):** CONTINUATION = v4 เดิมทุกประการ · SKIP = ไม่เข้าไม้วันนั้น
- **Config space (ประกาศ ex-ante ≤12):** mapping ของ 4 เซลล์ {CLEAN∧FRESH, CLEAN∧SPENT, POKED∧FRESH, POKED∧SPENT} → {CONTINUATION, SKIP} โดยบังคับ CLEAN∧FRESH=CONTINUATION เสมอ → 2³ = **8 configs** · **[MC-6/M3] rationale ของการบังคับ = semantics ไม่ใช่ P&L:** CLEAN∧FRESH คือ canonical continuation state ตามนิยามแกน (level ไม่ถูกทดสอบ + run ยังสด) — v4 behavior เป็น default โดยโครงสร้าง
- **[MC-3] Fail-open quantified:** UNDEF/OPPOSED/avail=0 = CONTINUATION → **538/1,487 = 36.2% ของไม้ (SUM +251.8)** — **brain มี leverage จริง ~64% ของไม้** (dc_UNDEF เป็นก้อนหลัก ~31%) · ตัวเลขนี้อยู่ใน risk register ด้วย
- **[MC-6/M5] Provenance ของหลักฐาน:** grid values ที่จุดชนวนดีไซน์ (+0.599/−0.581) มาจาก **PRIMARY (n=889)** ส่วนสนามที่ WS-1 รันจริงคือ **ALL-traded (n=949 aligned)** ที่เซลล์อ่อนลง (PS −0.398 · CS −0.032) — ประกาศไว้กันตีความผิด
- **Free parameters ใหม่: 0** (ทุก threshold สืบทอด+frozen · config เลือกโดย WF = behavior-map selection ตาม F7 ไม่ใช่ param)
- **ห้ามเด็ดขาด:** fade/SPIKE-REVERT (defer จนผ่าน F4) · เลือก config จาก in-sample P&L ที่เห็นแล้ว (−0.581 เป็น hypothesis ไม่ใช่คำตอบ) · เพิ่ม threshold/เซลล์ใหม่ (= card ใหม่ +budget)

### 3.2 Pipeline + Gates (ตามลำดับ ห้ามข้าม)
| ขั้น | งาน | เกณฑ์ผ่าน | Verify |
|---|---|---|---|
| D-0 | `brain_v1_ceiling.py` overlay day-level (สนาม SEARCH ไม่มี equity-path — skip = ตัดวัน) + **[MC-4] regression 3 ชุด:** (a) all-CONT = +532.8 เป๊ะ (b) skip-everything = 0 ไม้ (c) single-cell-skip attribution = SUM(cell) เป๊ะทุกเซลล์ | ผ่านครบ 3 | self + assert — **✅ ผ่านแล้ว 2026-07-05** |
| **D-0.5** | **[MC-1] In-sample §0 CEILING GATE:** enumerate ทั้ง 8 configs full-sample เทียบ §0 — **ceiling นี้เป็น upper bound ของ "fixed-config strategy" (= ดีไซน์ WS-1 ที่ D-1a บังคับ config เสถียรข้าม folds)** — *แก้ถ้อยคำจาก v1.1 แรกที่เขียน "ของ WF/OOS ใดๆ" ซึ่งกว้างเกิน (Claude Verify): era-adaptive/piecewise ถูก bound ด้วย oracle รายปีแทน* | ceiling ≥ §0 จึงเดิน D-1a | **✅ รันแล้ว 2026-07-05 — GATE ยิง: fixed-config ceiling ดีสุด = CS+PS: loseImp 32.4% · poolImp 9.5% < §0 → SKIP-only (WS-1 design) = documented-dead → branch WS-3** · **Oracle per-year (unrealizable): losing −10.2/winners +760.8 — §0 "เปิดในโลก hindsight" แต่ best-config รายปีสลับมั่วไร้ pattern → era-adaptive ไม่ใช่ path จนกว่ามีหลักฐาน learnability (backlog #2 trigger)** |
| D-1a | *(เดินเฉพาะเมื่อ D-0.5 ผ่าน — ปัจจุบันปิด)* **Walk-forward บนสนาม search**: **[MC-5] fold boundaries + min-n-per-cell-per-fold ต้อง pin ex-ante ใน spec ก่อนรัน** (POKED∧SPENT มี 110 ไม้ทั้งชุด — fold บางเกิน = post-hoc DoF) · เลือก config จาก OOS เท่านั้น | config เสถียร | Engineer review spec ก่อนรัน |
| D-1b | **PBO/CSCV** ของ selection (F3) | **PBO < 0.5** | script เป็นเจ้าของเลข |
| D-1c | เกณฑ์ §0 บนสนาม search: **[MC-6/M4] ฐาน inline: 5 ปีแพ้ −135.3 → ต้อง > −67.65 · ปีชนะ +668.0 → ≥ +534.4 · pooled +532.8 → ≥ +692.6 · worst ≥ −150** (ALL-traded · entry-year · ป้าย SEARCH) | ครบทุกข้อ | data-path independent re-derive |
| **Gate D1** | Engineer adversarial review ทั้งชุด | PASS | + Claude Verify |
| D-2a | **สนาม CONFIRM ชั้น 1:** capped sim @3000 + @1000 (mirror cap S1-S8 เดิม) | §0 ไม่พลิกเครื่องหมาย · ไม่ชน RED FLAG แบบเดิม | self + independent |
| D-2b | **[MC-2] สนาม CONFIRM ชั้น 2 — สองเฟส decouple decision จาก realtime logic:** **เฟส A** = sim export skip-date-list → EA อ่าน list ใน tester → พิสูจน์ P&L-equivalence ของการ skip บน capped real-tick (ราคาถูก · protocol Stage 0 เดิม · ตอบ RED FLAG ตรง) · **เฟส B** = implement realtime poke/DC ใน MQL5 **เฉพาะเมื่อเฟส A พิสูจน์ว่า skip ช่วยจริง** (Trellis.mq5 ปัจจุบันไม่มี poke/DC logic — grep verified · DC เป็น stateful algo เสี่ยง re-implementation divergence สูง — Grid Doctrine #1: ห้ามเขียน code ก่อน expectancy ผ่าน) · วินรัน GUI ≥3 ช่วงรวมปีแพ้ | ทิศ+ขนาดสอดคล้อง sim | Engineer + clean-room |
| **Gate D2** | สรุปต่อวิน: ไป Stage E (demo) / rev-2 / Stage F | วินตัดสิน | — |

### 3.3 Failure branches (ประกาศก่อน — ไม่มี branch ไหนคือ "เผาแล้วทิ้ง")
- D-1 ไม่ผ่าน §0 → เปิด **WS-3 rev-2** (เพิ่ม exit lever ทีละตัว) ก่อนตัดสิน
- rev-2 หมด lever แล้วยังไม่ผ่าน → **Stage F trigger** (OHLCV+state ceiling พิสูจน์แล้ว)
- ผ่าน search แต่พังบน CONFIRM → บันทึกเป็น sim-vs-real divergence ใหม่ → วิเคราะห์กลไก (ห้าม tune ให้ผ่าน)

## 4. WS-2 (ขนาน, ฟรี): C10 Market Structure Kill-Gate
- Feature: event-based HH/HL/BOS/MSS · **fixed-length window ไม่ผูก entry-hour** · **as-of ≤ close ของ j−1** (ตัด bar j — ปิด bar-size injection) · sequence-position เท่านั้น · DoF ทุกตัว ex-ante
- **Kill-gates ก่อนคิด budget:** corr(MS, os/dc_state) — MS-good ≈ FRESH → **kill ฟรี** · corr(MS, poked/rjR/entry_hour/5 ตัวตาย) ≤ ~0.15
- รอด kill-gates → เลือกทาง: full card (9/40, 4-leg conjunction + guide) หรือ fold เป็น state ที่ 3 ของ WS-1 rev — **เสนอวินตอนนั้น** · Stage D ไม่รอ WS-2

## 5. WS-3 (rev-2, เปิดเมื่อ WS-1 มี traction หรือ D-1 fail): Exit/Management Axis
ลำดับ lever (ทีละตัว — กัน param/PBO พัง): **#10 asymmetric exit/let-winners-run** (ผูก RED FLAG โดยตรง — cap วัน R เล็ก + ปล่อย expansion day) → **#7 time-stop** (ออกไม้ไม่ follow-through ≤30min — Osler T-STRONG) → #3 session-exit ("ถือถึง 23:00 จริงหรือ") · ทุก lever = pre-registered + Engineer review + วัดบน CONFIRM field

## 6. WS-4: Backlog Registry (ห้ามหายเงียบ — ทุกตัวมี trigger)
| # | รายการ | Trigger เปิดงาน |
|---|---|---|
| 1 | Round-number proximity (Osler เลขกลม) | WS-1 ต้องการ state เพิ่ม / WS-2 ตาย |
| 2 | Era-regime conditioning | ถ้า WF folds แสดง config พลิกข้ามยุค |
| 6 | Mechanism-hunt "FLAT ทำเงิน/UP-extreme ขาดทุน" (8/9 ปี) | Stage B mini-harvest รอบหน้า |
| 8 | Signed prior-close direction (C4 เดิม = unsigned) | wave-2 cards ถ้าเปิด |
| 9 | Penetration-depth ต่อเนื่อง | คู่ WS-2 |
| 4,5,11 | settlement window · Raschke-fixed · base-rate constraint | Stage D descriptive/design guard |

## 7. Governance & Hardening (บังคับตลอดแผน)
1. **[MC-6/L1] เสนอ commit ทุก milestone → commit เมื่อวินสั่ง** (คงกติกาเดิม — แผนนี้ไม่ commit อัตโนมัติ) · push เมื่อวินสั่ง
2. **Verification 3 ชั้น** กับทุกผลที่จะอ้างต่อ: self-assert → independent re-derive (คนละ code path) → clean-room adversarial (คนละ instance) — อย่างน้อยผลระดับ Gate ต้องครบ 3
3. **Verifier prompt hardening (บทเรียน C9-leak):** ทุก prompt ที่ห้ามแตะ P&L ต้องมี (ก) นิยามชัดว่าอะไรคือ "แตะ" พร้อมตัวอย่าง (ข) ประโยค "ถ้าจำเป็นต้องดูเพื่อวินิจฉัย ให้หยุดและรายงานก่อน" (ค) ผล review ใดที่มี leak → ป้ายถาวร + การแก้หลัง leak ต้อง tightening-only เท่านั้น
4. **Budget ledger:** 8/40 ณ วันที่เอกสารนี้ · การเผาใหม่ทุกใบอ้าง ledger + BH family เดียว · WF/behavior selection ไม่กิน budget แต่ต้องผ่าน PBO
5. **Lockbox 2021–2026:** ห้ามใช้เลือกอะไรทั้งสิ้น — แตะครั้งเดียวตอน validate จบ (หลัง Gate D2 + วินสั่ง)
6. **สนามวัดติดป้ายทุกตัวเลข:** SEARCH (uncapped sim) / CONFIRM-1 (capped sim) / CONFIRM-2 (real-tick tester) — target ผสมสนาม = target ปลอม
7. **Change control:** เบี่ยงจากเอกสารนี้ = บันทึก amendment ใน Progress Log + Engineer review ก่อนมีผล

## 8. Decision Ownership
- **วิน:** requirement/เกณฑ์ §0 · เปิด-ปิดทุก Gate (D1, D2, WS-2 full-card, WS-3 เปิด rev-2, Stage F trigger) · commit/push
- **Claude:** technical design/implement · Verify ทุก finding · Progress Log ทันทีที่เกิดเหตุ
- **Engineer (instance แยก):** adversarial review ก่อนรันทุก deliverable · clean-room หลังรันระดับ Gate

## 9. Risk Register
| Risk | Mitigation |
|---|---|
| SPENT∧POKED n=103 บาง → WF เลือกจาก noise | PBO<0.5 บังคับ + config เสถียรข้าม folds + CONFIRM field เป็นด่านจริง |
| Cap interplay (R2/P-C): skip อาจเปลี่ยนลำดับ equity → cap พฤติกรรมต่าง | D-2a รัน @3000 และ @1000 ทั้งคู่ · เทียบ skip-set กับ cap-set |
| Era-flip (P-E) | WF folds คร่อมยุค + backlog #2 trigger |
| Double-dipping ผ่าน post-hoc cells | §7 guard: behavior map ex-ante · WF เลือก behavior ไม่ใช่เซลล์ · เซลล์ใหม่ = card ใหม่ |
| MQL5 implement คลาดจาก sim (Gate D2) | ใช้ protocol Stage 0 เดิม (alignment รายไม้ + skip-set match) |

## 10. Definition of Done (v1)
Brain v1 ถือว่า "สำเร็จ" เมื่อ: ผ่าน §0 ครบบนสนาม SEARCH → ยืนบน CONFIRM-1 (ทั้งสอง deposit) → Gate D2 real-tick สอดคล้อง → Engineer + clean-room CONFIRMED → วินอนุมัติเข้า Stage E · ถือว่า "ตอบแล้วว่าไม่ work" เมื่อ failure branches (§3.3) เดินครบ — ทั้งสองทางคือ deliverable

## 11. Changelog
- **v1.1 (2026-07-05):** ผนวก Engineer review MC-1..MC-6 — เพิ่ม **D-0.5 in-sample §0 ceiling gate** (H1: เพดาน SKIP-only ที่พิสูจน์ = 32.4%/9.5% < §0 → เดินตาม v1.0 จะเผา WF+MQL5+GUI เพื่อผลที่รู้ล่วงหน้า) · D-2b → 2 เฟส skip-date-list-first (H3: Trellis.mq5 ไม่มี poke/DC logic — grep 0 hit · DC stateful เสี่ยง divergence) · quantify fail-open 36.2%/leverage 64% (H2) · D-0 regression 3 ชุด (M1) · pin WF folds ex-ante (M2) · CLEAN∧FRESH rationale = semantics (M3) · §0 base inline (M4) · PRIMARY≠ALL provenance note (M5) · commit rule = เสนอ-แล้ว-วินสั่ง (L1) · **สถานะหลังรัน D-0/D-0.5 จริง (script `brain_v1_ceiling.py` = system of record · Claude Verify ตรงตาราง Engineer ทุกแถว): SKIP-only = documented-dead → active path = WS-3 (#10 let-winners-run) + WS-2 (C10 kill-gate ขนาน)** — root cause ตาม Engineer: แผน v1.0 แปลง Gate C เชิงข้อความครบแต่ไม่ได้ตั้ง cheap falsification pre-check (pattern "มั่นใจว่ารู้แล้ว→ข้ามวัดซ้ำ" ระดับ planning)
