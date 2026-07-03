# TRELLIS-010 — Adaptive Brain Research Workflow (สมองอ่านสถานการณ์)

**วันที่:** 2026-07-03 · **สถานะ:** แผนอนุมัติรอวินสั่งเริ่ม
**หลักการจากวิน (บังคับทั้ง workflow):** EA ต้อง**เข้าใจว่าราคาเคลื่อนเพราะอะไรแล้วปรับพฤติกรรมให้ถูกกับสถานการณ์** — ห้ามแก้ปัญหาด้วยการเพิ่มตัวแปรให้หลบ · ห้ามเล่านิทานหลังเห็นผล (ทุก hypothesis ประกาศ prediction ก่อนรัน) · ห้ามเสนอแล้วรอ — ทุก stage มี output จับต้องได้

---

## 0. นิยาม "สำเร็จ" — v2 หลัง Engineer review + Claude Verify (แยกสนามวัดชัด · reproduce ได้ 100%)

> **บทเรียน v1 (บันทึกไว้เตือน):** §0 เดิมเขียน "ปีแพ้ 5 ปี −$270" จากความจำ — script จริงบอกรวม **+$129** (2025 เป็นปีชนะบน sim!) = ผสมสนาม sim/tester มั่ว · Engineer จับได้ · ทุกเลขต่อไปนี้ reproduce จาก `dual_asian_sim.py` (สนาม sim) หรือ diag CSV จาก tester (สนาม authority) เท่านั้น

**สนาม SIM (ที่ Stage A–D ทำงาน):** ปีแพ้จริงของ config ที่ deploy = **2012, 2014, 2017, 2018, 2019, 2022, 2023 (รวม −$127.5)**
- เกณฑ์หลัก: กลุ่มนี้ดีขึ้น **≥ 50%** โดยปีชนะ sim (2011, 2013, 2015, 2016, 2020, 2021, 2024, 2025, 2026) เสียรวม **≤ 20%**
- Pooled 15.5 ปี ดีขึ้น ≥ 30% · WF OOS ดีขึ้น · worst year ไม่แย่กว่า −$150

**สนาม TESTER (authority):** 2025 แพ้เฉพาะที่นี่ (−$169 vs sim +$207) → เป็นโจทย์ของ **Stage 0** ไม่ใช่ของ brain — brain ที่ fit ใส่ target ที่มีอยู่แค่สนามเดียว = fit noise
- เกณฑ์: หลัง Stage 0 sim↔tester ต้องลู่เข้า (per-year ต่างกัน ≤ $80 หรืออธิบายได้ครบเชิงกลไก) · ด่านจบทุกเวอร์ชัน = tester + lockbox

**LOCKBOX: 2024–2026 ห้ามใช้เลือกสัญญาณ/threshold ใดๆ — แตะครั้งเดียวตอน validate จบ** · นิยามชัด: lockbox ห้าม *signal selection* แต่**ไม่ห้าม** *execution-fidelity study* (Stage 0 ศึกษา fill/participation mechanics บน 2025 ได้ — มันไม่ได้เลือกทิศ alpha) — เส้นแบ่งนี้ Engineer review ตรวจได้ทุกเมื่อ

**นิยาม "ไม่ work":** เกณฑ์ไม่ผ่านหลัง hypothesis หมด backlog → Stage F — บันทึกการ falsify ทุกใบ ไม่ tune ซาก ไม่วน

---

## Stage 0 — Sim↔Tester Reconciliation + Decision Robustness (บังคับก่อนทุกอย่าง — ผล F1)

**โจทย์:** config เดียวกัน กฎเดียวกัน — sim 2025 = +$207 แต่ tester = −$169 · จาก join v4c: drift −$4.4/ไม้ + **participation ต่างกัน 27%** (47/177 วัน เครื่องหนึ่งเข้า อีกเครื่องไม่เข้า)

1. **Decomposition ก่อนตัดสิน fix ใดๆ (re-review เงื่อนไข a — diagnose-before-fix):** สร้าง join script ที่ rerun ได้ (เลข 27%/−$4.4 ใน §เดิมเป็น un-scripted — ต้อง re-derive จาก script ที่ commit + ติดป้ายสนาม) → แยกว่า gap มาจาก (a) participation flips vs (b) per-trade fill/exit drift วัดทุกปี · หลักฐานเบื้องต้นชี้ว่า (b) อาจครอง (ไม้ร่วม drift −$571 ขณะ flips สุทธิ +$255 เข้าข้าง MT5) — **ถ้า (b) ครอง fix ต้องมุ่งที่ execution model ไม่ใช่ threshold**
2. **Hysteresis = CANDIDATE fix (ยังไม่ commit จนกว่า decomposition ชี้):** ถ้า (a) มีนัย → เงื่อนไข regime slope ต้องยืน K bars ติดกัน · **กติกาเลือก K (ล็อกไว้กัน overfit): เลือกด้วย convergence (gap ≤ $80) + character-preserved เท่านั้น — ห้ามเลือกด้วย net P&L** · "ลด whipsaw" ถ้าเกิด = side-observation ต้องพิสูจน์ OOS แยก ห้ามใช้เป็นเกณฑ์ · **ห้าม apply กับ breakout-cross โดยไม่วัด edge cost ก่อน** (เข้าช้า K bars อาจกิน right-tail ที่เป็นแหล่งกำไรทั้งระบบ — ต้องมีตาราง Δnet vs K)
3. **Re-baseline:** sim + tester รันใหม่ด้วย fix ที่ decomposition ชี้ → per-year gap ต้อง ≤ $80 · ถ้าเหลือ residual แล้วจะอ้าง "อธิบายได้เชิงกลไก" ต้อง**พิสูจน์ว่า residual ไม่ alpha-relevant** (ไม่ใช่แค่เล่ากลไก) → **baseline ใหม่คือจุดตั้งต้นของ H0/Stage A–D ทั้งหมด**

**Gate 0:** gap ปิดตามเกณฑ์ + Engineer review ยืนยันว่า hysteresis ไม่เปลี่ยน character ของระบบ (trade count/hold time/PF อยู่ใน envelope เดิม)

## Stage H0 — Simplest Hypothesis First (ผล review: ก่อนสร้าง brain ทั้งชุด)

ทดสอบว่า **ตัวแปร regime เดี่ยว exogenous** (realized-vol percentile / trend-range state ที่นิยามโดยไม่เห็น P&L) อธิบาย/แก้กลุ่มปีแพ้ sim (2012/14/17/18/19/22/23) ได้แค่ไหน — **ถ้า H0 ผ่านเกณฑ์ §0 = จบ ไม่ต้องสร้าง taxonomy+state machine** · ถ้าไม่ผ่าน = ได้ baseline ให้ brain ต้องชนะ

---

> **ลำดับใหม่ (ผล review): Stage 0 → H0 → B → A → C → D → E/F** — Stage B (external) มาก่อน A เพื่อประกาศ hypothesis ก่อนเห็น outcome ตัวเอง (ต้าน label-leakage)

## Stage A — Internal Evidence: ชำแหละวันแพ้ (data เราเอง 15 ปี) — v2: อุด label-leakage (F2)

**กฎเหล็กใหม่:** day-type ต้องนิยามจาก**ตัวแปรโครงสร้างตลาด exogenous เท่านั้น** (realized-vol percentile, range-expansion ratio, overnight gap, trend state, event-day) — **ห้ามเห็น win/loss ของ EA ตอนนิยาม type** · จากนั้นค่อยวัด conditional P&L ต่อ type · นิยาม type บน **2012–2016** → ยืนยันเสถียรภาพบน **2017–2020** ที่ไม่เคยเห็น · **Stage A ห้ามแตะ 2021–2026 (lockbox+guard)**

**คำถาม:** วันที่ระบบแพ้ ตลาด*ทำอะไรจริงๆ* หลังเราเข้า — และมันประกาศตัวล่วงหน้าด้วยอะไรที่วัดได้ realtime

| ขั้น | งาน | Output |
|---|---|---|
| A1 | สร้าง day-level dataset ทุกวันเทรด (~2,100 วัน): entry context + intraday path หลังเข้า (MFE/MAE รายชั่วโมง, hold-above-level time, retrace depth ที่ 30/60/120 นาที, กลับเข้ากรอบเมื่อไหร่, direction persistence) | `Scripts/brain/day_dissect.py` + `day_facts.csv` |
| A2 | จัดกลุ่มวันด้วย **exogenous type เท่านั้น** (จากตัวแปรใน "กฎเหล็ก" — ห้ามเห็น P&L ตอนจัด) → แล้วจึงวัด conditional P&L ต่อ type ทีหลัง | ตาราง type (exogenous) × P&L × ยุค |
| A3 | ตรวจด้วยตาจริง: sample วันแพ้หนัก 30 วัน + ชนะใหญ่ 30 วัน — บันทึกเฉพาะ observable (ห้าม narrative ปรุงแต่ง) | `Plan/TRELLIS-010_daynotes.md` |
| A4 | **Taxonomy v0** เช่น TREND-GRIND / SPIKE-REVERT / WHIPSAW / DEAD — พร้อมนิยามเชิงตัวเลขต่อ type | หัวใจของ Stage C/D |

**Gate A (ผ่านจึงไปต่อ — leakage checklist):** taxonomy ต้อง (1) จำแนกได้จากข้อมูล ณ เวลาจริงเท่านั้น — ไม่มี lookahead (2) แต่ละ type มี P&L ต่างกันจริง เสถียร ≥6/8 ช่วงเวลา (3) **type ถูกนิยามโดยไม่เห็น P&L ของ EA** — reviewer ตรวจจาก definition ว่าอ้างเฉพาะตัวแปร exogenous (4) **นิยามบน 2012–16 → P&L-separation ยังยืนบน 2017–20 ที่ไม่เคยเห็น** (5) ไม่แตะ 2021–26

## Stage B — External Knowledge Harvest (คู่ขนานกับ A — real world/community)

| แหล่ง | เก็บอะไร | เกณฑ์คัด |
|---|---|---|
| Academic (SSRN/journals) | intraday momentum & opening-range-breakout studies, session effects ทองคำ, volatility clustering, liquidation dynamics | มี methodology + ตัวเลขทดสอบได้ |
| Practitioner (MQL5 articles, ForexFactory/futures.io journals, prop-firm frameworks) | day-type frameworks, session tactics ที่มี stats จริง | **มี rule ชัด + ตัวเลข เท่านั้น** — โม้/ขายฝัน = ทิ้งทันที |
| Microstructure | signature ของ stop-run / liquidation cascade / London fix flows / CME settlement | อธิบายกลไก "ใครถูกบังคับซื้อขาย" ได้ |

**Output:** **Hypothesis cards** (H1..Hn) — 1 ใบ = claim + แหล่ง + วิธีทดสอบบน data เรา + prediction ที่ประกาศล่วงหน้า
**Gate B:** ใบที่ทดสอบบน data เราไม่ได้ = เข้า backlog Stage F ห้ามใช้ · **ห้ามเชื่อเพราะคนพูดเยอะ — external = แหล่ง hypothesis ไม่ใช่แหล่งความจริง**

## Stage C — Hypothesis Testing (ทีละใบ, pre-registered)

1. ทุกใบ: เขียน prediction ก่อนรัน (protocol เดียวกับ overshoot-test ที่ถูก falsify ไปแล้ว — นั่นคือตัวอย่างที่ถูกต้อง: ทำนาย→ทดสอบ→ตาย→ทิ้ง ไม่ฝืน)
2. ทดสอบบน **2012–2020 ก่อน** (ยาว+หลากหลาย regime) → ผู้รอดไปยืนยัน 2021–26
3. **วินัย multiple-testing v2 (F3 — enforce ได้จริง):** test budget ประกาศล่วงหน้า **≤ 40 ใบทั้ง workflow** (นับสะสมใน Progress Log ทุกใบ) · Benjamini-Hochberg correction — **family = ทั้ง 40 ใบของ workflow นี้ (family เดียว ไม่แยกต่อ stage)** · **permutation null บังคับทุกใบ** (ไม่มี "เมื่อคลุมเครือ") · search บน 2012–2020 เท่านั้น · PBO (CSCV) เป็น gate ของ WF selection
4. **Tick volume (col index 6 — verified: เป็น tick-count จริง, col 7=0, col 8=spread):** order-flow proxy ใบแรก · **caveat (F6):** เป็น activity proxy เฉพาะ feed Dukascopy → ใช้แบบ **relative/percentile ใน rolling window เท่านั้น** + ต้อง cross-feed verify กับ Exness ก่อน promote เข้า Stage D

**Gate C:** เหลือ discriminator ที่ stable ≥1 ตัว → Stage D · เหลือ 0 → ประกาศ "OHLCV ceiling ถูกพิสูจน์" → Stage F ทันที (ไม่ใช่ความล้มเหลว — คือคำตอบ)

## Stage D — Brain v1 Build

1. **Rule-based state machine ก่อน** (โปร่งใส ตรวจได้) — ไม่กระโดดไป ML จนกว่า rule จะตัน: classifier บอก day-state realtime → **พฤติกรรมต่อ state**: CONTINUATION → ตามทะลุ (v4 เดิม) · SPIKE-REVERT → **fade กลับเข้ากรอบ** (กลยุทธ์ใหม่ มี stop/exit ของตัวเอง) · DEAD → ไม่มีเหยื่อ
   **Burden of proof ของ fade (F4 — pre-registered เพราะ MR เพิ่งถูก falsify ทั้งสถาปัตยกรรม):** (a) trigger ต้องนิยามบนตัวแปรที่ orthogonal กับ horizon/deviation ที่ edge_screen sweep แล้ว (b) mean reversion-distance ของ population ที่ trigger ต้อง **≥ 3× cost $0.40** (c) ต้องผ่าน **edge_screen cost-hurdle test เดิม จำกัดเฉพาะ trigger population** ก่อน implement — ไม่ผ่านข้อใด = fade ตาย บันทึก falsify ไม่ฝืน
   **Param budget (F7):** brain ทั้งชุดเพิ่ม free parameter ได้ **≤ 6 ตัว** · classifier threshold freeze จาก Stage C (ห้าม re-optimize ใน WF) · WF เลือกได้เฉพาะ behavior-map ≤ 12 configs
2. Sim เต็ม pipeline เดิมที่พิสูจน์แล้ว: 15.5 ปี → sensitivity → **walk-forward (behavior mapping = สิ่งที่ WF เลือกได้)** → bootstrap
3. **Gate D1:** เกณฑ์ §0 + Engineer review → จึง implement MQL5
4. Tester 3 ช่วง**รวมปีแพ้** → เทียบ sim → **Gate D2:** ทิศ+ขนาดสอดคล้อง

## Stage E — Deployment & Live Proof

- **Demo คู่ขนาน สองบัญชี demo แยกกัน (F5 — ห้ามบัญชีเดียวแยก magic):** risk-cap/margin อ่าน account equity ร่วม (`Trellis.mq5` risk-cap = `AccountInfoDouble(ACCOUNT_EQUITY)`) → บัญชีเดียวจะปนเปื้อนการตัดสินใจกันเอง · v4 บัญชีหนึ่ง (เริ่มได้ทันที) v5 อีกบัญชี · ทั้งคู่ตั้ง HourShift=-1 + verify Friday close ก่อนนับแต้ม
- Weekly analysis script อัตโนมัติ + walk-forward re-selection ทุก quarter (meta-process ที่พิสูจน์ OOS แล้ว)
- เกณฑ์เลื่อนขั้นเงินจริงเล็ก: demo ≥3 เดือน + ผลอยู่ใน envelope ที่ sim ทำนาย

## Stage F — Data Escalation (เมื่อ C/D พิสูจน์ว่า OHLCV ไม่พอ)

| ข้อมูล | แหล่ง | ปลดล็อกอะไร |
|---|---|---|
| Volume delta / order flow | CME futures (paid), Rithmic/Sierra, proxy ฟรี: tick volume ที่มี + crypto gold books | แยก "flow สะสม vs liquidation" ตรงๆ |
| COT positioning | CFTC (ฟรี รายสัปดาห์) | regime layer เชิงโครงสร้าง |
| Econ calendar | ฟรีหลายแหล่ง | ตัด/ใช้ event days อย่างรู้ตัว |

→ กลับเข้า Stage C ด้วยอาวุธใหม่ — loop นี้คือ "หาความรู้เพิ่ม" ที่เป็นระบบ ไม่ใช่ยอมแพ้

---

## วินัยการทำงาน (ทุก stage)

- ตัวเลขทุกตัวจาก script ที่ rerun ได้ · prediction ก่อนรันเสมอ · การ falsify = ผลงาน บันทึกเสมอ
- Progress log ต่อท้ายไฟล์นี้ทุก stage — session ใหม่อ่านแล้วทำต่อได้ทันที (long-context continuity)
- Engineer adversarial review ที่ Gate 0, C, D1, D2 · Claude verify ทุก finding
- **เวลา: gate-driven — ไม่สัญญาจำนวนรอบ (F8)** · Gate A มี leakage checklist ต้องผ่านครบ ห้ามรีบ

## Progress Log
- 2026-07-03: v1 → Engineer review (APPROVE-with-changes, บล็อก Stage A) → Claude Verify ยืนยัน F1 ด้วย script อิสระ (ปีแพ้ 5 ปีที่อ้าง −270 จริงๆ คือ +129 — 2025 แพ้เฉพาะ tester) → **v2**: เพิ่ม Stage 0 (reconciliation + hysteresis) + H0 + ลำดับ B ก่อน A + lockbox 2024–26 + test budget 40 + fade burden + param budget 6 + สองบัญชี demo
- 2026-07-03 (บ่าย): **Engineer re-review (reviewer เดิม): เห็นด้วยให้เริ่ม Stage 0** — F1/F3–F8 RESOLVED, F2 PARTIAL → **v3**: แก้ A2+Gate A (exogenous-only + OOS split เข้า gate จริง — ปิด F2), Stage 0 reorder เป็น decomposition-ก่อน-fix (hysteresis = candidate, K เลือกด้วย convergence เท่านั้น, ห้ามแตะ cross โดยไม่วัด edge cost), §17 residual ต้องพิสูจน์ไม่ alpha-relevant, BH family = ทั้ง 40 ใบ · หลักฐานที่ทำให้ถ่อมตัว: flips สุทธิ +$255 เข้าข้าง MT5 / ไม้ร่วม drift −$571 → fix อาจต้องมุ่ง execution model
- 2026-07-03 (เย็น): **Stage 0.1 decomposition เสร็จ — root cause ของ gap 2025 คือ DATA-CLOCK BUG ไม่ใช่ execution model** · เครื่องมือ: `Scripts/stage0_join.py` (instrumented runner + self-check exact เทียบ canonical `dual_asian_sim.run` ทุกครั้งที่รัน + decomposition identity ต้องปิดเป๊ะ + ไม่มี silent trim) · ผล (rerun ได้): 2023 gap +6.4 / 2024 −25.6 (ทั้งคู่ ≤$80 ✓ ผ่านเกณฑ์อยู่แล้ว) / **2025 gap −376.8 = drift common −467.4 (132 ไม้, −3.54/ไม้) + flips +90.6 (45/177 วัน = 25%)** — แทนที่เลข un-scripted เดิม (27%/−4.4)
  - Prediction "(b) drift ครอง" → CONFIRMED แต่ขุดต่อพบชั้นลึกกว่า: **entry-minute alignment 2023 = 170/170 · 2024 = 167/168 · 2025 = 1/132** · Δentry histogram 2025 = −120min×21 / −180min×20 แยกตามฤดู **US DST เป๊ะ** → BT 2025 clock = UTC+0 ขณะ sim CSV = UTC+2/+3
  - **Reproduction test (prediction ประกาศก่อนรัน: align ≥90% · flips→1-2% · net→ใกล้ −169):** sim บน clock shift UTC+0 (`stage0_join.py shift`) → align 140/156 = 90% ✓ · flips 3% ✓ · net −255 (residual ทั้งหมดมาจาก 16 วันขอบ DST ที่ shift function หยาบ — วันที่ align จริง drift เหลือ **−0.08/ไม้**) → ยืนยัน
  - **2026 (v4d_2601) เพี้ยนเหมือนกัน:** align 0/18 · Δ −120min×6 · flip 33% → **+$330 ของ v4d = artifact เข้าข้าง tester** · สรุป: เลข tester 2025 (−169) และ 2026 (+330) ใช้เทียบ sim ไม่ได้ทั้งคู่ — narrative "tracking noise ±$5/ไม้ ไม่ใช่ bias" ใน STATUS ถูก falsify: drift แท้จริงหลัง align = −0.08..−0.25/ไม้ ทุกปี
  - **Root cause ระดับไฟล์ (พิสูจน์จาก primary source):** `MQL5/Files/XAUUSD_ticks_eet_2025.csv` (19 เม.ย.) + `_2026` (3 ก.ค. 11:46) epoch แรก = raw UTC เป๊ะ (2025-01-01 23:00 / 2026-01-01 23:00) ขณะ eet_2020–24 = +2 ✓ · ตัวการ: `Gloo/Scripts/ticks_to_mt5ticks.py` เขียน UTC โดยตั้งใจ (docstring อ้าง "MT5 handles display timezone" — สมมติฐานผิด) แล้ว rename เป็นชื่อ `_eet_` legacy → semantic เปลี่ยนแต่ชื่อเดิม
  - **ไฟล์แก้มีพร้อมแล้ว:** `Gloo/Data/XAUUSD_ticks_eet_2025.csv` (24 ก.พ.) พิสูจน์ pairwise tick July = raw+3 DST-aware ✓ · `eet_2026` (24 ก.พ.) = +2 ✓ (data จบ 23 ก.พ. ก่อน DST)
  - ข้อสังเกตใหม่ที่มีค่า (fidelity observation ไม่ใช่ signal selection): sim 2025 บน session เพี้ยน 2-3 ชม. = **−255 vs +207** — session alignment เป็นแหล่งแพ้ชนะจริงของระบบนี้
  - **Next (รอวินอนุมัติ/รัน):** (1) copy eet ฉบับถูก 2 ไฟล์ทับใน MQL5/Files (2) วินรัน `ImportCustomTicks` ปี 2025–2026 `InpDeleteFirst=true` (3) วิน rerun tester 2025 เต็มปี + 2026 ม.ค.–ก.พ. tag ใหม่ (`v4f_25`, `v4f_2601`) build เดียวกับ v4c (หรือระบุ build ให้ชัด) (4) Claude rerun `stage0_join.py` → เกณฑ์ Gate 0: align ระดับ 2023–24 + per-year |gap| ≤ $80 → Engineer adversarial review (5) แก้ `ticks_to_mt5ticks.py` + README ให้ shift ถูก (Gloo project — logged เป็น issue ข้ามโปรเจกต์) (6) อัปเดต STATUS/เอกสารที่อ้างเลข tester 2025/2026 หลัง re-baseline
  - Hysteresis (candidate fix เดิม): **ไม่ใช่ fix ที่ decomposition ชี้** — ไม่แตะ · Stage 0.2 ข้ามไป 0.3 re-baseline หลัง data fix
- 2026-07-03 (ค่ำ): **Engineer adversarial review = APPROVE-with-changes** (reproduce ทุกเลข + ปิด blind spot summer ด้วย pairwise 1 ส.ค.: buggy vs fix ต่าง 3.0 ชม. เป๊ะ, byte-size เท่ากัน = pure time-shift) · เงื่อนไข: HIGH-1 bar-rebuild ต้อง verify · HIGH-2 InpDeleteFirst scope · HIGH-3 headline +$318 ปนเปื้อน 2/4 ก้อน (WF +876 / holdout +802 / v4_2324 PASS ไม่ปนเปื้อน) · MED-4 Gate 0 ต้องดู per-season · MED-5 session-sensitivity เป็น robustness risk · LOW-6 self_check ควร assert entry_time · แก้ generator ไม่ใช่แค่ก๊อปไฟล์ (ก๊อปอย่างเดียว = workaround)
- 2026-07-03 (ค่ำ): **Claude Verify — ยกระดับ 2 finding เป็นข้อค้นพบใหม่ที่พิสูจน์แล้ว:**
  - **BT-clock = EET กฎ EU-DST ไม่ใช่ "US-DST" ตามที่ TRELLIS-009 §10/CLAUDE.md/STATUS บันทึก** — proof เดิมใช้ ก.พ.+ฤดูร้อนซึ่งสองกฎแยกไม่ได้ · หลักฐานใหม่ (shoulder weeks ที่กฎต่างกัน): (1) price-match M1 CSV bar `2025.03.17 00:00` open 2984.28 = raw tick `2025.03.16 22:00:01` bid 2984.28 → +2 ขณะ US DST active = กฎ EU (2) โครงสร้าง ต.ค.: ศุกร์ 24 ต.ค. จบ 23:59 (+3) / จันทร์ 27 ต.ค. เปิด 00:00 (+2 หลัง EU จบ 26 ต.ค.) (3) 2023/2024 M1 CSV โครงสร้างเดียวกัน (จันทร์ใน US-only window เปิด 00:00) (4) ไฟล์ tick fix: 17 มี.ค. = raw+2 (5) **reproduction ชี้ขาด (prediction ประกาศก่อน: EU-shift → align ≥95%): ผล align 153/156 = 98% (จาก 90% กฎ US) · drift −0.03/ไม้ · 16 วันขอบ DST เหลือ 3** (`stage0_join.py shift-eu`)
  - **EA live bug ยืนยันจาก code:** `Trellis.mq5:171` `IsUsDST` + `:189` — HourShift=-1 AUTO แปลง UTC→BT ด้วยกฎ US → **ผิด 1 ชม. ~5 สัปดาห์/ปี** (Mar 9-30 + Oct 26-Nov 2 โดยประมาณ) บน Exness live/demo · tester (HourShift=0) ไม่กระทบ · ต้องแก้เป็นกฎ EU ก่อน demo forward
  - **HIGH-1 ปิดด้วยหลักฐานเชิงประจักษ์:** entry ของ v4c align กับ UTC-shifted sim 98% ⇒ bars ที่ EA เห็นใน real-tick tester ถูกสร้างจาก ticks (ถ้าใช้ M1 bars ที่ import แยก (EET ถูก) entry จะ align กับ sim ปกติ) → แทน ticks ถูกแล้ว bars จะถูกตาม · MQL5 doc ทางการไม่ระบุชัด (fetch วันนี้) → คง spot-check 1 วันร้อน + 1 วัน shoulder หลัง re-import เป็น confirmation
  - **HIGH-2 ปิด:** `ImportCustomTicks.mq5:72-78` `CustomTicksDelete(symbol, delFrom, delTo)` ลบเฉพาะช่วงปี ✓ · **LOW-7 กลับข้าง:** บรรทัดแรกไฟล์ = `...455` ตามที่ Claude บันทึก (เลข 557 ของ Engineer คือบรรทัดสอง) — immaterial ทั้งคู่
  - **Gap ใหม่ที่พบ:** script คำนวณ holdout Exness +$802 **ไม่อยู่ใน repo** (ค้น Scripts/*.py ไม่มี DST-shift/holdout mode) = un-scripted number + ไม่รู้ว่าใช้กฎ DST ไหนช่วง shoulder มี.ค. 2026 (~3 สัปดาห์ใน holdout window) → ต้อง re-derive ด้วย script commit หลังแก้กฎ EU · **v4e_full acid test ที่ค้างใน STATUS ต้องเลื่อน** ไปหลัง re-import (ไม่งั้นรันบน data ผิด clock)
  - แผน fix ฉบับรวม (รอวินอนุมัติ): (A) copy 2 ไฟล์ fix → วิน re-import 2025/26 → spot-check bar time → วิน rerun `v4f_25`+`v4f_2601` → stage0_join Gate 0 (|gap|≤80 + align ระดับ 23-24 + per-season ไม่มี cluster ชั่วโมงกลม) (B) แก้ generator `ticks_to_mt5ticks.py` เป็น EET EU-DST + naming ตรง semantic + first-tick assertion (C) แก้ EA `IsUsDST`→EU rule + compile/deploy (D) แก้เอกสาร/memory ที่อ้าง US-DST + headline +$318 (E) re-derive holdout ด้วย script commit (F) self_check เพิ่ม invariant assertions (entry/exit วันเดียวกัน, entry hour 8-20)
- 2026-07-03 (16:00–17:00): **วินอนุมัติ A–F → execute แล้ว:**
  - **A1 ✓** copy `eet_2025/2026` ฉบับถูก (24 ก.พ.) เข้า MQL5\Files — verify epoch แรก = 01:00 (+2) ทั้งคู่
  - **C ✓** EA `IsUsDST`→`IsEuDST` (last Sun Mar/Oct) + comment/label — compile 0/0 deploy 16:06 (ex5+mq5+mqh)
  - **B ✓** generator `ticks_to_mt5ticks.py` เขียน EET EU-DST ตรง + ชื่อ output `_eet_` ตรง semantic + self-assertion (fail loud) — **พิสูจน์: regenerate 2026 ได้ SHA256 ตรงไฟล์ดี 24 ก.พ. ทุก byte** · README workflow อัปเดต (เลิก rename _mt5_→_eet_ · ห้ามใช้ไฟล์ _mt5_ เก่า)
  - **วินสั่งเพิ่ม (17:xx): clean re-import** — `ImportCustomTicks` v1.10: pre-flight ไฟล์ต้องครบทุกปีก่อน (ขาด = abort ไม่ลบอะไร) → **ลบทั้งช่วง Start–End รวดเดียว** → import (แทน per-year delete ที่คาบเกี่ยว) — compile 0/0 deploy 16:17
  - **F ✓** self_check เพิ่ม invariants (entry hour 08–20, dir ±1, ถือข้ามวัน = รายงานดัง >5 วัน = fail) → **จับของจริงได้ทันที 2 เรื่อง (log เป็น `Issue/ISSUE_2026-07-03_eod_overnight_data_holes.md`):** (1) **EOD 23:00 ไม่ fire ช่วง DST-shoulder + วันหยุด US** (NY close 21:00 UTC = 22:59 BT → ไม่มี bar 23) → sim+EA ถือข้ามคืนจริง 20 ไม้/4 ปี — **claim "ไม่มีไม้ข้ามคืนโดยโครงสร้าง" (TRELLIS-009 §2) เป็นเท็จบางช่วง** · สมมาตรสองสนาม ไม่กระทบ reconciliation (2) Dukascopy data hole: 2023-11-15→17 หาย 42 ชม. กลางสัปดาห์ (Stage A ต้องมี gap detector)
  - **E ✓** `Scripts/holdout_exness.py` (commit, spread unit ExportM1 = 0.001/pt → หาร 10): **กฎ US reproduce เลขเดิม +802.5/PF2.24/wr61.2/49 ไม้/รายเดือนตรง §10 เป๊ะทุกตัว = holdout เดิมใช้กฎ US ที่ผิด · เลขถูกต้อง (กฎ EU): +$511.8 · PF 1.54 · maxDD $320 · ยังบวกทุกเดือน** — ต่างทั้งหมดอยู่ shoulder มี.ค. (+340→+50) · governance: ห้ามเลือกกฎจาก P&L — กฎมาจาก ground truth data
  - **D ✓** แก้ CLAUDE.md (US→EU + บทเรียน verify clock ก่อน import) · TRELLIS-009 §11 CORRECTION + changelog v7 · STATUS.md re-baseline (เลขตาย: tester 2025 −169 / 2026 +330 / aggregate +318 / holdout +802.5 · เลขรอด: sim 15.5ปี / WF +876 / tester 23-24 +157) · memory อัปเดต
  - **2026 เพิ่มเข้า join แล้ว:** gap +169.7 = flips +205.6 ครอง (v4d: UTC clock + อาจเป็น risk-cap build) — รอ v4f_2601 ตัดสิน
- Test budget สะสม: **0/40** (Stage 0 = diagnostics/reconciliation ไม่ใช่ signal-hypothesis card — Engineer เห็นด้วย) · lockbox 2024–26 สะอาด (execution-fidelity เท่านั้น + คำเตือน governance: ห้ามยก "2025 EET = +207" เป็นหลักฐานเลือก signal)
- 2026-07-03 (17:15): **Re-import + verify ครบทุกชั้น — PASS 14/14 พร้อมรัน v4f**
  - วินรัน ImportCustomSymbol (bars 25-26: 344,412+50,259, เริ่ม 01:00 ✓) + ImportCustomTicks v1.10 (clean delete 83,478,312 = ชุดเก่า 2025+26 เป๊ะ → import 68,131,640+15,346,672 Errors=0)
  - `stage0_verify_import.py`: tick/bar count ตรง log ทุกตัว + OHLC bar↔tick ตรงทุกทศนิยม 8 นาทีคร่อมทุกฤดู DST
  - `VerifyBTClock.mq5` (v1.00→1.04): บทเรียนระหว่างทาง — (1) probe แบบ bar เดียว = อ่อน ให้ผล FAIL ปลอม ต้องใช้ **date-range CopyRates + รอ SERIES_SYNCHRONIZED** (Engineer ชี้ Claude ผิดที่ฟันธง "cache" โดยไม่มีสิทธิ์ · doc: ticks-without-bars ถูก tester ignore → คำถาม absent-vs-cache สำคัญจริง) (2) ผล definitive: **bars 2023 = 348,184 synced ✓ / warmup ธ.ค. 2024 = 28,764 ✓ — ไม่มีอะไรหาย** (3) FAIL Δ$0.05 สุดท้าย = expect ของ Claude ชี้ผิดไฟล์ — **CSV 2023 ฉบับ Gloo/Data ต่างจากฉบับ Files ~1 tick** (terminal ตรงแหล่ง import ของตัวเอง 100%; ความต่างสองฉบับถูกวัดรวมอยู่ใน drift 2023 −0.19/ไม้แล้ว — observation ไม่ block) (4) หลักฐานปิด H-cache: v4b_2324 เมื่อเช้าเทรด 2023-24 ได้ 340 ไม้ = bars เคย serve ใน tester วันเดียวกัน + ทุก op หลังจากนั้น range-scoped
  - Claude Verify รอบนี้ยัง fetch docs เพิ่ม: "If a symbol history has no minute bar but the appropriate tick data ... these ticks are ignored" (tick_generation) — ปิดปมที่ Engineer รายงานว่า doc ขัดกัน
- 2026-07-03 (18:00): **Pre-Gate-0 Engineer review = READY-with-conditions — จับรูใหญ่ก่อนรันเปล่า:** EA มี `C_MAX_RISK_FRAC=0.02` (Trellis.mq5:39,242 — deploy 12:00) แต่ sim/stage0_join ไม่มี → v4f ที่ deposit 3000 จะ confound cap เข้ากับ clock (Engineer quantify: 2026 cap ตัด 11/23 วัน → gap −74 ชิดเพดานโดยไม่เกี่ยว clock · 2025 ตัด 7 วัน) — **fix ที่ถูก: รัน v4f ที่ deposit $100,000** (lot fix 0.01 → PnL absolute ไม่เปลี่ยน · cap threshold $2,000 ≫ R max 339 → cap เป็นกลาง = วัด clock ตัวแปรเดียว) · Claude verify code จริงแล้วทุกบรรทัดที่อ้าง ✓ · Gate 0 อ่าน alignment% + drift/ไม้ เป็น primary (n เล็กของ 2026 ห้ามตัดสินจาก net เดี่ยว) · **Issue ตาม (log ไม่ลากเข้า Gate 0):** (1) mirror risk-cap+%backstops ลง dual_asian_sim ก่อน quote เลข live ที่ deposit 3000 (headline capped ≈ +189/+86 ตาม Engineer est.) (2) dual_asian_sim default D=0.75 ≠ deploy D=1.0 — กับดัก canonical ต้องแก้ default+docstring
- 2026-07-03 (ค่ำ): **วินปฏิเสธ deposit-100k เด็ดขาด (กฎ 8.1: เพิ่มทุน = กันชน ไม่ใช่การแก้ · ระบบต้องพิสูจน์ที่ทุนน้อย) → pivot เป็น MIRROR-CAP เข้า sim ที่ deposit 3000** · Engineer (instance ใหม่) ออกแบบ spec S1-S8 + G0-1..7: cascade พิสูจน์ว่าถูกกัก (flip 1 วันเลื่อน threshold ≤$1.20 < ระยะ margin วันถัดไป) · `atr_entry` ใน diag = R ตรงๆ (Trellis.mq5:264) → ได้ R-match เป็น clock-check เส้นสอง · backstops %equity ไม่ binding (SL 1×R≤$68 fire ก่อน $150 เสมอ + tripwire) · **Claude Verify: reproduce ทุกเลขด้วย script อิสระ — ตรงเป๊ะ** (n/net/skip dates/margins/worst/maxDD) + ปิด 3 ข้อสงสัยเอง (fresh-3000 ต่อ run ✓ · ไม่มี overnight-hold ชนวัน skip ✓ · ไม่มี gap-loss เกิน 1×R+5 ✓) · **Engineer final review (instance ที่สาม): PASS-with-changes** → บังคับ [A] ต่อท่อ atr_entry+R เข้า pipeline [D] ประกาศว่า tester skip-set = อนุมาน · แนะนำ [C] เฝ้า 8 overnight-holds 2025 กด G0-1 [E] เช็ค first-trade 2026 (01-02 อยู่ในชุด boundary แล้ว — ตัดสินใจไม่ pre-roll: เพิ่ม equity-path ปน) [F] **ความจริงที่วินต้องเห็น: cap@3000 กลืน edge 2026 จาก +160 เหลือ +4.3 (skip 12/23 วัน — cap ตัดวัน high-R ที่เป็นตัวทำเงิน) — โจทย์เชิงกลยุทธ์ stage ถัดไป ไม่ใช่ Gate 0**
- **Implement เสร็จ (วินสั่ง "PASS ให้ดำเนินการ"):** `stage0_join.py` — cap in-runner (S1-S4) + S5 tripwire + load_diag อ่าน atr_entry + R ใน trade tuple + R-match (G0-3) ใน decompose/report + `mode_predict` (pre-registration จาก script) + `mode_gate0` (G0 checklist + skip attribution + unambiguous subpop) · regression: self-check equivalence ยังเป๊ะ (338+175) · **เลข predict จาก in-runner ตรงกับ Engineer + replay อิสระ = ยืนยัน 3 ทาง**
- **⭐ PRE-REGISTERED PREDICTION (จาก `stage0_join.py predict` — สนาม SIM capped@3000 กฎ EU):** `v4f_25`: **n=145 net=+189.1 maxDD=281 skip 7 วัน** · `v4f_2601`: **n=11 net=+4.3 maxDD=81 skip 12 วัน** · boundary ต่างได้เฉพาะ: 2025 {04-10, 05-06, 06-13} · 2026 {01-02, 01-20, 01-22}
- 2026-07-04: **วินถาม deposit 1000 — รันเทียบสด:** 1000 → 2025 n=75/+208.2/DD101 (ตรง acid-test เดิมใน STATUS ✓) แต่ **2026 n=0 (R ต่ำสุด 57 > cap $20 — ตัดครบ 23 สัญญาณ)** = Gate 0 ปี 2026 ไม่มีไม้เทียบ · **วินเลือกทาง A: Gate 0 ที่ 3000 ก่อน (วัดครบสองปี) → ผ่านแล้วค่อย acid test 1000 (`v4e_full`)** · observation บันทึกไว้: ที่ 1000 ปี 2025 กำไรสูงกว่า 3000 (+208 vs +189 — cap กรองวัน R ใหญ่ที่ปีนั้นรวมขาดทุน) = ข้อมูลหนึ่งปี ห้ามสรุป
- 2026-07-04 (00:15): **วินรัน v4f ครบ → `stage0_join.py gate0` (สนามวัด: sim capped vs tester v4f — ตัวเลข rerun ได้ทุกค่า):**
  - **2025:** tester n=149 net +169.7 (pred 145/+189.1) · **G0-1 alignment 145/145 (100%)** · G0-1b 137/137 · **G0-3 p95|ΔR|=0.00 (R ตรงระดับ cent ทุกไม้)** · G0-5 gap −19.4 ≤80 ✓ · **G0-6/7 skip-set ตรง 7/7 วัน** · G0-4 drift −0.46/ไม้ (ขอบแถบ) — **attribution ปิดสนิท: tester-only 4 วัน (01-21/03-18/03-28/09-02) = วัน exit ของ sim overnight-holds 100% (Finding C) · drift แยกขั้ว: 8 วัน hold = −90.8 / 137 วันปกติ = +0.171/ไม้ (กลางแถบ)**
  - **2026:** tester **n=11 เป๊ะตาม prediction** net −9.3 (pred +4.3, ขอบ −5..+5 — หลุดเล็กน้อย) · **G0-1 11/11 · G0-3 p95=0.00 · G0-6/7 skip ตรง 12/12 (รวมวัน R=339) · flip 0%** · **G0-4 = −1.24/ไม้ หลุดแถบ −0.5..+0.2 อย่างเป็นทางการ** (ΣΔ −13.6/11 ไม้ · eod→eod avg −1.71 · แย่สุด −6.0 · 8/11 ติดลบ ~binomial 0.11 ไม่ significant · ไม่มี overnight hold) — ส่ง Engineer ตัดสิน "อธิบายได้เชิงกลไก+ไม่ alpha-relevant" หรือไม่
  - First-trade ทั้งสองปี = 02 ม.ค. ตรง sim ✓ ไม่มี start-shift · S5 tripwire ไม่ยิง · หมายเหตุซื่อสัตย์: clock-bug เดิมหายสนิท (alignment 100% + R exact) — residual ที่เหลือคือ (1) overnight-hold protocol divergence (Issue 1 — quantified แล้ว) (2) fill drift ยุค vol สูง
  - **Engineer adversarial verdict (reproduce ทุกเลขเอง + S2 integrity 175 ไม้ 0 mismatch): GATE 0 = PASS (conditional)** — วัตถุประสงค์ reconciliation บรรลุ: clock ปิดเด็ดขาด (p95|ΔR|=0.00, alignment 100%, diff_entry=0 สองปี) · ทุก residual attribute ครบ identity ปิด · cap mirror ซื่อตรง · G0-4 2026 หลุดแถบจริง (ไม่กลบ) แต่เป็น explained cost-residual ที่ signal/participation/R สมบูรณ์
  - **เงื่อนไข (log แล้วทั้งหมด):** **C1** Issue overnight-hold แก้จาก "สมมาตร" → **asymmetric** (EA catch-up close+re-entry vs sim hold — Issue doc แก้แล้ว 07-04) · reconcile sim→EA = งาน stage หน้า · **C2 sim-optimism bias ยุค high-vol:** label "pessimistic" เป็นเท็จในยุค spread กว้าง (2026 drift −1.24/ไม้ uniform 9/11) — เลข sim ยุค high-vol ต้องอ่านแบบมี haircut ~1.2/ไม้ · tester/real-tick = authority (ตรง doctrine เดิม) · Claude Verify ปรับขอบเขต: holdout Exness ใช้ spread จริงของ Exness (28pt median) จึงโดนบางส่วนไม่เต็ม แต่ยัง bar-level — เลขยุค 2026 ทุกตัวควร re-validate real-tick ก่อน quote เป็น edge · **C3 RED FLAG expectancy: sample real-tick high-vol เดียวที่มี (2026 capped@3000) = net −$9.3** — cap กลืน edge 2026 (uncapped +160 → capped +4.3 → real −9.3) · **Gate 0 ผ่าน ≠ capped strategy มี edge — Stage ถัดไปต้องเผชิญ tension survival-vs-edge ตรงๆ**
  - **สรุป Stage 0: ปิดแล้ว** — sim↔tester ลู่เข้า (2025 gap −19.4, 137 วันปกติ +0.17/ไม้) · baseline ใหม่สำหรับ H0/Stage A–D = **sim capped@3000 + ความรู้ asymmetry/optimism ข้างต้น** · Test budget ยังคง 0/40 · lockbox สะอาด (ทั้งหมดคือ execution-fidelity)
- **Next:** (1) วินรัน **acid test deposit 1000** (`v4e_full` 2025.01.01–2026.02.23 — ตามที่วินเลือกทาง A) — prediction จาก script: 2025 n=75 net +208.2 maxDD 101 / 2026 n=0 (cap ตัดหมด — โดยดีไซน์) · เกณฑ์: รอด+ไม่ HALT+โปรไฟล์ตรง sim (2) จากนั้นเริ่ม **Stage H0** ตามแผน
