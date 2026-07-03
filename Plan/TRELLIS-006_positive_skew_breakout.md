# TRELLIS-006 — Positive-Skew Session Breakout Engine

**วันที่:** 2026-06-29
**สถานะ:** DRAFT — รอ Engineer review ก่อนเขียนโค้ด
**เจ้าของ design:** Claude (own — ไม่ใช่ relay agent) · supersedes TRELLIS-005 (momentum reframe ที่ FAIL review)
**เป้าหมาย (วิน):** เอาชนะตลาด — generate profit (= อยู่รอด) ด้วย **logic ที่แข็ง** ไม่ใช่ tune/ข้ออ้าง

---

## 1. บทเรียนที่ยอมรับ (ไม่โทษตลาด)
- **EA แพ้เพราะ logic อ่อน ไม่ใช่ "ตลาดไม่มี edge":** entry = fade noise (ไม่มีพลังทำนาย), grid/TP คงที่ (negative skew) · MT5 −24.5% = หลักฐานว่า **logic นี้อ่อน → แก้ logic**
- **เลิกอ้าง Stage 0 (Python):** VR/Hurst วัดแค่ linear-autocorrelation อ่อน — **ไม่ได้พิสูจน์ว่าไม่มี edge** (nonlinear/conditional edge มองไม่เห็นด้วยเครื่องมือนั้น) · หลักฐานที่ใช้ตัดสิน = **MT5 backtest ข้ามปีเท่านั้น**

## 2. หลักการ logic ที่แข็ง (2 เสา — มีเหตุผลรองรับ ไม่ curve-fit)

### เสา A — Entry มีพลังทำนายจาก market structure จริง (ไม่ fade noise)
**Session-conditioned volatility breakout:**
- Gold เคลื่อน**แรง+มีทิศจริง**ตอน **London/NY session** (institutional liquidity/flow — documented microstructure ไม่ใช่ param ที่ fit)
- นิยาม **pre-session range** (Asian range: high/low ช่วงตลาดเงียบ) → **เข้าเมื่อ break ออกจาก range ตอน session active + volatility expansion ยืนยัน** (ATR ปัจจุบัน > ค่าเฉลี่ย ATR)
- = เข้าเมื่อ move "จริง" (range expansion ใน session ที่มี flow) ไม่ใช่ noise · **event-driven ไม่ใช่ regime-classifier ที่ lag**

### เสา B — Positive skew (พลิก geometry ที่ทำให้แพ้)
- **Stop แคบ** (opposite range side / k_sl×ATR) = **แพ้เล็ก**
- **ATR trailing** ปล่อยกำไรวิ่งตาม fat-tailed move = **ชนะใหญ่**
- **ไม่มี TP เล็กคงที่** (ตัวที่ทำ negative skew ใน v2) · กำไรมาจาก trend ที่วิ่งยาว ไม่ใช่ scalp

## 3. ทำไมนี่แก้จุดที่แพ้ (trace กลับ root cause)
| จุดแพ้เดิม | แก้ |
|---|---|
| entry fade noise | breakout ใน session + vol-confirm = move จริง |
| negative skew (TP$2/loss$20) | positive skew (stop แคบ + trail ปล่อยวิ่ง) |
| M1 scalp (random-to-MR) | **TF session: range=Asian, manage=M5/M15** (ที่ move capturable) |
| regime-classifier lag | event-driven breakout (ไม่ต้องทำนาย regime) |

## 4. Anti-curve-fit (ตรงคำสั่งวิน "ห้าม tune")
- **Low DOF — 1 สัญญาณ:** session window + range + breakout buffer + vol filter + stop/trail ATR mult (param น้อย, อิง structure ไม่ใช่ indicator soup)
- **validate plateau ข้ามปี: 2022 (range/chop) + 2023 + 2024 (trend)** — ไม่เลือกปี trend มา validate เดี่ยว (กัน circular ตาม Engineer H5)
- ไม่ optimize หา peak · ถ้ากำไรเฉพาะ param แคบ = curve-fit → ทิ้ง

## 5. โครงสร้างเทคนิค
- **TF:** Asian range (เช่น server 00:00–07:00) → breakout/manage M5 หรือ M15 (ไม่ใช่ M1)
- **Entry:** ราคา > AsianHigh + buffer (BUY) / < AsianLow − buffer (SELL) ระหว่าง session window + ATR > avgATR · 1 ครั้ง/ทิศ/วัน (กัน overtrade)
- **Stop:** อีกฝั่งของ range หรือ k_sl×ATR (แคบ)
- **Trail:** k_trail×ATR (ปล่อยวิ่ง) — อาจ break-even เมื่อกำไร ≥ 1R
- **Position:** เดี่ยว + trail ก่อน (low DOF) · pyramid-with-trend = layer ถัดไปถ้าฐานบวก (Engineer เตือน reversal wipe)
- **Risk armor v2 คงไว้:** cumulative HALT −25% + daily soft-stop + margin + reliable close + persistence
- **Grid:** ไม่ใช้ใน core นี้ (grid = negative-skew execution) · เก็บเป็น option ตลาด range ภายหลัง

## 6. Params (น้อย — owned defaults, tune หยาบเฉพาะ validate plateau)
SessionRangeStart/End · TradeSessionStart/End · BreakoutBufferATR (~0.1) · VolFilterATRratio (~1.0) · StopATR (~1.0) · TrailATR (~2.5) · MaxTradesPerDay (~2) · timezone/server-offset (pin)

## 7. ความซื่อสัตย์
- **ไม่การันตีชนะ** — แต่ logic นี้**แข็งกว่า fade-grid มาก** (entry มี structural grounding + positive skew จับ fat tail) และ**ทุกข้ออ่อนเดิม trace แล้วแก้**
- หลักฐานตัดสิน = **MT5 ข้ามปี** · ถ้าบวก robust ข้าม regime = edge จริง · ถ้าไม่ = iterate logic ต่อ (ไม่ยอมแพ้ ไม่อ้างตลาด)

## 8. Validation
วินรัน MT5 GUI · XAUUSD_BT real-tick · 2022 + 2023 + 2024 แยกปี · ดู: net, profit factor, **avg win vs avg loss (ต้อง win>loss = positive skew)**, max DD, %winning-years

## Changelog
- **v1 (2026-06-29):** positive-skew session-breakout · own by Claude · address Engineer FAIL ของ 005 (evidence-grounded structure แทน M1-momentum narrative, low-DOF, cross-regime validate, TF=session ไม่ใช่ M1)
