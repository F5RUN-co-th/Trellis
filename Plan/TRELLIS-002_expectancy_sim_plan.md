# TRELLIS-002 — Stage 0 Expectancy Sim Plan

**เวอร์ชัน:** v2 (2026-06-27)
**สถานะ:** DRAFT — รอวินตัดสิน §10 Open Decisions ก่อน implement
**ขึ้นกับ:** [`TRELLIS-001_design_doctrine.md`](TRELLIS-001_design_doctrine.md) §4 + §5
**Doctrine ที่บังคับ:** Grid Doctrine #1 (พิสูจน์ expectancy ก่อนเขียน code) · #3 (basket loss cap) · #4 (normalize lot) · #6 (worst-case ทะลุเพดาน) · CLAUDE.md "Verify ≠ Self-grading"
**ที่มา v2:** ผ่าน Engineer review 2 รอบ + Claude Verify (findings C1–C4, H1–H6, M1–M4 verified เป็น root cause) — ดู Changelog ท้ายไฟล์

---

## 1. เป้าหมาย (วัดผลได้)
ตอบด้วย **ตัวเลขจริง** ว่า payoff structure ของ Trellis grid บน XAUUSD มี **net expectancy เป็นบวกหลังหัก cost จริงหรือไม่** — ถ้าไม่ → **ไม่เขียน EA**

คำถามแกน (TRELLIS-001 §2.3): win-rate × small-win **>** loss-rate × catastrophic-loss หรือไม่ (หลัง cost จริง)

---

## 2. Data Source (verified — ไม่ต้องดึงใหม่)
- ใช้ **raw `Gloo/Data/XAUUSD_YYYY_ticks.csv` 2011–2026** (6-col tab, UTC, มี **Bid+Ask** → spread จริงต่อ tick)
- รายละเอียด + caveats: memory `project-tick-data-xauusd` + `Gloo/Data/DATA_QUALITY_REPORT.md`
- **Caveats ที่ sim ต้อง handle:** CRLF line ending · spread=0.00 มีได้ (ต้อง floor) · Last/Volume=0 (ไม่ใช้)
- **⚠️ Dukascopy = ECN-tight** — spread ดิบ optimistic เทียบ retail Gold broker จริง → §3 cost_model ต้อง floor + markup (H3)
- **Non-stationarity:** microstructure 2011 ต่างจาก 2026 มาก → report expectancy แยก sub-period ด้วย ไม่ใช่ตัวเลขรวมตัวเดียว (M4)

---

## 3. Engine Architecture & Execution Model (Python — ยังไม่เขียน รออนุมัติ)

### 3.1 Modules
| Module | หน้าที่ |
|--------|---------|
| `loader` | stream tick (handle CRLF), parse `Date+Time → epoch_ms`, yield (ts, bid, ask) — ไม่โหลดทั้งปีเข้า RAM |
| `indicators` | ATR จาก **M1 closed bars** (reuse `XAUUSD_M1_YYYY.csv` ที่ precompute แล้ว) — **closed-bar เท่านั้น กัน look-ahead** (M1) |
| `basket_engine` | lifecycle ตาม §3.2 |
| `cost_model` | ตาม §3.3 |
| `metrics` | รวมผลทุก cycle → expectancy, distribution, tail, ruin → **export JSON/CSV** |
| `report` | สรุปตาราง (script คำนวณ — ห้าม LLM พิมพ์เลขเอง) |

### 3.2 basket_engine — Fill & Close convention (ต้องระบุชัด — C2)
- **Entry = limit fill** ที่ระดับ grid: BUY fill เมื่อ Ask ≤ level, SELL fill เมื่อ Bid ≥ level (limit ไม่มี adverse slippage)
- **Mark-to-market floating PnL:** BUY → Bid, SELL → Ask
- **Basket close = market, cross spread** (ปิด BUY ที่ Bid, SELL ที่ Ask)
- **Hard-stop overshoot (Doctrine #6):** เมื่อ Σ ≤ −X trigger → ปิดที่ tick **ถัดไป** + slippage buffer ไม่ใช่ราคา trigger เป๊ะ → ให้ tail loss ทะลุเพดานได้จริง
- **Gap-through fill:** ถ้า tick กระโดดข้ามหลาย level (gap/weekend) → fill ที่ **gap-open (realistic)** ไม่ใช่ที่ level (optimistic)
- **Lot normalize 0.01 step ใน engine** (Doctrine #4) — sim จำลอง rounding นี้ ไม่งั้น lot ladder หลอก (T1)

### 3.3 cost_model
- **Spread จริงต่อ tick** จาก Bid/Ask + **floor** ขั้นต่ำ (กัน spread=0) + **broker markup** (แปลง Dukascopy → broker เป้าหมาย) (H3)
- **Slippage asymmetric by fill-type** (C2): limit entry = 0 adverse, market/hard-stop close = negative slippage เสมอ (มากขึ้นตอน fast-trend)
- **Swap:** ต่อ lot ต่อ night (long/short rate แยก) + **triple ทุกพุธ** + rollover @ 00:00 **EET (DST-aware)** (H2) — Gold swap ติดลบหนัก = ต้นทุนหลักของ basket ที่ค้าง
- **Commission** ต่อ lot ต่อ side

### 3.4 ⚠️ Engine Invariant ที่ต้อง pin ก่อน build (H6)
**Basket เดียว (one-at-a-time) หรือ concurrent (re-entry ขณะ basket เดิม underwater)?** — เป็น **architecture invariant** ไม่ใช่ param เปลี่ยนโครง `basket_engine` เอง · ถ้า concurrent → §6 ruin/equity-DD ต้อง **aggregate ข้าม basket ที่เปิดพร้อมกัน** ไม่ใช่ per-basket (ไม่งั้น exposure จริง > sim) → **§10 รอวินตัดสิน**

---

## 4. Layered Falsification Funnel (โครงหลัก — แทน "sweep แล้วหาจุดบวก")
แต่ละชั้น **falsify ได้** เรียง cheap→expensive ตัดจบไอเดียแย่ก่อนลงทุน build:

| ชั้น | ทำอะไร | Falsify (ถ้า fail → จบ) |
|---|---|---|
| **0. Model-free pre-gate** | วัด mean-reversion ของ series เอง **entry-agnostic, multi-scale**: Variance Ratio (Lo-MacKinlay) / Hurst exponent ข้ามหลาย horizon + เทียบ oscillation capture vs **cost hurdle** (spread+comm+swap/รอบ) | VR≥1 / Hurst≥0.5 (trending) หรือ capture < cost → grid ลบแน่ ไม่ต้อง build engine |
| **1. Null-data calibration (3-way)** | feed synthetic เข้า engine: **driftless GBM → expectancy ≤ −cost** · **pure-trend → ลบหนัก** · **OU mean-revert → บวก** | GBM ให้บวก = bug/look-ahead/cost รั่ว · OU ให้ลบ = engine ไม่มี power เห็น edge → หยุดแก้ engine |
| **2. Random-entry baseline + entry edge** | grid + **random entry** เป็น control → แล้วทดสอบว่า entry signal (conditional drift หลัง pullback) **ชนะ random อย่างมีนัย** | pullback ไม่ชนะ random → signal ไม่มี edge จบ |
| **3. Realistic execution** | รันด้วย §3.2/§3.3 เต็ม (limit-entry/market-close/cross-spread/asym-slippage/overshoot/gap + swap triple-Wed EET + spread floor+markup) | expectancy ลบหลัง cost จริง → จบ |
| **4. Honest statistics** | block bootstrap (Politis-White block length) + EVT/GPD tail + ruin path-based | gate §8 ไม่ผ่าน |
| **5. Single-shot OOS confirm** | freeze config จาก IS → เปิด OOS 2022–26 **ครั้งเดียว** | OOS ไม่ยืนยัน → ไม่ generalize จบ |

---

## 5. OOS & Anti-Overfit Protocol (C1)
- **Split lock ก่อนเห็นผลใดๆ:** In-Sample = 2011–2021 · Out-of-Sample = 2022–2026 (ครอบ rally 2024–25 = ศัตรูร้ายสุดของ grid → hardest test ถูก hold out)
- **Select config บน IS เท่านั้น** → freeze 1 config → ทดสอบ OOS **ครั้งเดียว** (no peeking, no selection on OOS)
- **ลด sweep dimension ให้เล็กสุด** — fix structural params (entry family, lot ladder) ด้วยหลักการก่อน เหลือ sweep แค่ k × levels (≤ ~12 combinations)
- **SPA = conditional backstop:** ถ้าทำตามวินัยข้างบน → OOS มี hypothesis เดียว → ไม่มี multiple-testing → SPA ไม่จำเป็น · **ถ้าละเมิดวินัย** (peek/select-on-OOS/sweep OOS) → White's Reality Check / Hansen SPA / deflated metric **บังคับทันที**
- **Pre-register pass threshold (§8) เป็นลายลักษณ์อักษรก่อนรัน**

---

## 6. Metrics ที่ต้องวัด (ต่อ config — script เป็นเจ้าของเลข)
- **Expectancy / cycle** (หลัง cost) + **bootstrap CI** ← ตัวชี้ขาด
- Win-rate · avg win · avg loss · **avg & max basket loss (tail)** · distribution (ดู fat tail)
- **MAE / MFE ต่อ basket** (ความลึกก่อน TP — informs hard-stop) (H5)
- Risk-adjusted: expectancy / max-basket-loss, MAR/Calmar บน equity curve
- **Ruin probability** (block bootstrap + path-based, ไม่ใช่ IID resample) (C3)
- Max DD + DD duration / time-to-recovery · time-in-basket
- รายงาน **แยก sub-period** (M4) ไม่ใช่ aggregate ตัวเดียว

---

## 7. Stress Scenarios (บังคับ — grid ตายตอน trend แรง)
- **2013 เม.ย.** Gold flash crash (−$200/2 วัน)
- **2020 มี.ค.** COVID (spread พุ่ง $17.48)
- **2024–2025** rally +35% / +73% (trend ยาว)
- **Weekend gap** (Fri-close → Mon-open ทะลุ hard-stop) (H4)
- **Worst N rolling windows ที่ engine หาเอง** (กัน selection bias จากเลือกช่วงด้วยมือ) (L2)
- cost sensitivity: spread ×1.5/×2, slippage ×1.5
- **Report ทุก stress window แยก ไม่ว่าตกฝั่ง IS หรือ OOS** (ไม่ให้ split บัง stress)

---

## 8. Pass / Fail Gate
**ผ่าน (→ Stage 1) เมื่อครบทุกข้อ:**
1. **Bootstrap CI lower-bound ของ expectancy > 0** (ไม่ใช่ point estimate — fat tail ทำ SE สูง) หลัง cost จริง
2. รอด cost sensitivity (spread×1.5 + slippage×1.5)
3. Risk-adjusted ผ่านเกณฑ์ (expectancy/max-basket-loss หรือ MAR)
4. Ruin probability (block bootstrap) ไม่เกินเพดานที่วินรับได้
5. ยืนยันบน **OOS single-shot** + ไม่พังใน stress windows

**ไม่ผ่าน → ไม่เขียน EA** (Doctrine #1) — บันทึกผลเป็นหลักฐาน

> เกณฑ์ตัวเลขเป๊ะ (expectancy ขั้นต่ำ, ruin เพดาน, MAR ขั้นต่ำ) = 🔴 รอวินกำหนด (§10) — **pre-register ก่อนรัน**

---

## 9. Verify-Independence Protocol (CLAUDE.md §Verify — บังคับ)
- ตัวเลขทั้งหมด **derive จาก script** ที่ตรวจซ้ำได้ — Claude ห้ามพิมพ์ expectancy/win-rate เอง
- **Null-data 3-way calibration (§4 ชั้น 1)** = sanity test ว่า engine ไม่ bias บวก + มี power เห็น edge ทั้งสองทิศ
- **Block length data-driven** (Politis-White automatic) หรือ sensitivity ข้ามหลาย length — ห้ามเลือกมั่ว
- **EVT threshold** via mean-excess plot + report **CI กว้างอย่างซื่อสัตย์** (catastrophe จริงมีแค่ ~3–4 เหตุการณ์ → tail sample เล็ก)
- ก่อนเชื่อผล "expectancy บวก" → **adversarial review อิสระ** (context แยก, prompt "หักล้างว่า sim bias บวกตรงไหน": look-ahead, fill assumption, cost ต่ำเกิน, survivorship)
- แยกให้วินเห็น: อะไร script คำนวณ (auto) vs อะไรเป็นสมมุติฐานที่ Claude ตั้ง (judgment)

---

## 10. Open Decisions
> evidence: Engineer review + [`../Research/GRID_MARTINGALE_INDUSTRY_RESEARCH.md`](../Research/GRID_MARTINGALE_INDUSTRY_RESEARCH.md)

**✅ ตัดสินแล้ว (วินเห็นด้วย 2026-06-28, evidence-backed):**
- **#2 Lot scaling = flat 0.01 ก่อน** → fixed-add → geo (แยก study StartLot ใหญ่) · เหตุ: money-management เปลี่ยน sign expectancy ไม่ได้ → พิสูจน์ edge บนโครงเสี่ยงน้อยก่อน (Doctrine #1)
- **#3 Basket TP unit (sim) = $/R-multiple** (invariant ต่อ balance) · live EA ค่อยใช้ %balance (product decision แยก)
- **#7 Concurrent = one-at-a-time** สำหรับ Stage 0 · เหตุ: XAU correlation 1.0 → concurrent = leverage stacking ไม่ใช่ diversify

**🔴 ยังรอวิน (risk appetite / broker — requirement-owner):**
1. [ ] **Entry rule** ที่จะทดสอบ (pullback แบบไหน) — ชุดเล็ก {random baseline + 1 MR-pullback} อย่าขยาย (กัน curve-fit)
4. [ ] **Basket hard-stop เพดานหายนะ:** กี่ % ต่อ cycle (nominal ต่ำกว่าเพดานเผื่อ overshoot) — sweep แล้วส่ง expectancy-vs-ruin frontier ให้วินเลือก
5. [ ] **Pass threshold:** expectancy CI-lower>0 (+margin) · ruin เพดาน · (MAR รอง) — pre-register
6. [ ] **Account:** balance/leverage/commission + **swap จริงของ broker = gate** (H2)

> Claude/Engineer ตัดได้ (technical): OOS split, bootstrap method, fill convention, null-test design, perf approach

---

## 11. Deliverables (เมื่ออนุมัติ)
- `Trellis/Scripts/*.py` (modules §3.1)
- output: JSON/CSV ผลต่อ config + ตารางสรุป → `Trellis/Research/` หรือ `Issue/`
- **NOT in scope:** เขียน EA `.mq5` · optimization หา param สวยๆ (= curve-fitting trap, Doctrine #1)

## 12. ขั้นถัดไป
**(C)** เริ่ม §4 ชั้น 0 (model-free VR/Hurst pre-gate) ได้เลย — ไม่ต้องรอ §10 และ falsify ได้ทันทีว่าควรเดินต่อไหม · ขนานกับ **(B)** วินตอบ §10 (อย่างน้อย 1–4 + 7) → ผมเสนอ module design ละเอียด → review → เขียน Python

---

## Changelog
- **v2.1 (2026-06-28):** lock §10 #2 (flat 0.01 ก่อน) · #3 ($/R unit) · #7 (one-at-a-time) — evidence-backed (industry research + Engineer); #1/#4/#5/#6 ยังรอวิน. เพิ่ม `Research/GRID_MARTINGALE_INDUSTRY_RESEARCH.md`.
- **v2 (2026-06-27):** เพิ่ม Layered Falsification Funnel (§4) เป็นโครงหลัก · OOS & Anti-overfit protocol (§5) · fill/close + asym-slippage + swap-EET + spread-markup (§3.2/3.3) · engine invariant H6 (§3.4) · null-data 3-way + block-bootstrap + EVT (§9) · gate = CI lower-bound + risk-adjusted + cost-sensitivity (§8) · weekend-gap + worst-N stress (§7) · MAE/MFE + sub-period (§6) · H6 เข้า open decisions (§10). ที่มา: Engineer review 2 รอบ + Claude Verify.
- **v1 (2026-06-27):** ฉบับแรก (ขยายจาก TRELLIS-001 §4)
