# TRELLIS-001 — Design Doctrine & ChatGPT Proposal Review

**วันที่:** 2026-06-24
**สถานะ:** Stage 0 — Pre-code (expectancy proof)
**ที่มา:** วิเคราะห์ข้อเสนอ ChatGPT "Aggressive Grid Scalper" → ตัดสินใจสร้างโปรเจกต์แยกจาก Gloo

---

## 1. ทำไมต้องแยกจาก Gloo
Gloo = ICT/SMC disciplined (SL ต่อไม้, premium/discount filter, fixed RR) — ปรัชญา "เทรดเมื่อมี edge แล้วยอมรับการแพ้ที่จำกัด"
Trellis = grid recovery / basket exit — ปรัชญาตรงข้าม 180° (ไม่มี SL ต่อไม้, เติม+ทบล็อตเมื่อราคาสวน, ปิดทั้ง basket ที่กำไร)

→ ห้ามให้ logic ปนกัน เก็บเป็นคนละ codebase

---

## 2. บทวิเคราะห์ข้อเสนอ ChatGPT (สรุป verdict + หลักฐาน)

**Verdict:** ไม่รับตามที่เสนอ — มีข้อผิดพลาดเชิงเทคนิค/คณิตศาสตร์จริง + workaround ที่ละเมิดหลัก root-cause + ความเสี่ยง negative-expectancy ที่ถูกแต่งหน้าให้ดูปลอดภัย

### 2.1 ข้อผิดพลาดเชิงเทคนิค (เป็นจริง — ต้องแก้ก่อนนำไปใช้)
| # | ปัญหา | หลักฐาน |
|---|-------|---------|
| T1 | Lot multiplier พังเพราะ volume step rounding | StartLot 0.01 × 1.3 = 0.013 → ปัดเป็น 0.01 (step 0.01) ตัวคูณไม่มีผล 2-3 ไม้แรก |
| T2 | สูตรขัดตารางตัวเอง | "1,1.3,1.6,2.0" แต่ pow(1.3,n) = 1,1.3,1.69,2.197 |
| T3 | ATR ตัวอย่างผิด scale | เขียน "ATR=10 points" — Gold M5 จริง 100–300+ points (ผิด ~30 เท่า) |
| T4 | Unit ของ input กำกวม | GridStepATR=80 (=0.8×100?) / BasketTP=0.8 (%?) ปนกัน ไม่ production-ready |

### 2.2 Workaround (ละเมิด root-cause rule) — ตัดทิ้ง
- **Hedge Recovery (เปิด SELL กลบ BUY basket):** ไม่ลดความเสี่ยง แค่ freeze ขาดทุน + เพิ่ม spread/swap สองทาง ลบออกแล้วปัญหา (basket ติดลึก) กลับมา = workaround → **ตัดออก**
- **ADX>35 หยุดเพิ่ม grid:** ADX lagging — ยืนยัน trend หลังราคาวิ่งไปแล้ว grid ติดลึกก่อน → ใช้เป็น guard เสริมเท่านั้น ห้ามเป็นเกราะหลัก

### 2.3 ความเสี่ยงแกนกลาง — Asymmetric payoff
"เสี่ยง DD 20% เพื่อกำไร 0.8%/cycle" = ชนะถี่ทีละนิด แลกแพ้ครั้งใหญ่นานๆ ที
Gold trend แรงรายวัน (London/NY) → tail risk สูง → expectancy อาจติดลบสุทธิ
**ไม่มีจุดไหนในข้อเสนอที่พิสูจน์ว่า** win-rate × small-win > loss-rate × catastrophic-loss

### 2.4 ปัญหา validity
- Grid EA backtest หลอกตาที่สุด (equity curve เรียบ) — ต้อง tick data 99% + realistic spread/slippage
- News filter มัก **ไม่ทำงานใน Strategy Tester** → backtest ดีเกินจริง
- แหล่งอ้างอิงของ ChatGPT (Reddit/MQL5 market/Augrix) = marketing ไม่ใช่ validated edge

### 2.5 ส่วนที่ใช้ได้ (เก็บไว้)
- ATR-based dynamic spacing (ดีกว่า fixed pip สำหรับ Gold)
- Daily DD + Equity hard stop (ต้องมี — แม้เอาไม่อยู่ 100% เพราะ gap/slippage)
- Pullback entry (ไม่สุ่มกลางตลาด) — แต่ระวัง: entry เป็น mean-reversion ถ้าเดาผิด grid จะเติมสวน trend = จุดตายของ grid
- Magic per symbol, session/spread/slippage guard (มาตรฐาน reuse ได้)

---

## 3. Doctrine ที่ยึด (คัดลงใน CLAUDE.md แล้ว)
1. Expectancy ต้องพิสูจน์ก่อนเขียน code
2. ไม่มี Hedge recovery — ใช้ basket hard-stop แทน
3. ทุก basket ต้องมีเพดานขาดทุน
4. Lot ต้อง normalize ด้วย volume step เสมอ
5. Backtest ต้อง 99% tick + realistic cost
6. Equity stop ออกแบบโดยถือว่า worst-case ทะลุเพดาน
7. Filter (ADX ฯลฯ) = guard เสริมเท่านั้น
8. News filter ต้อง verify ว่าทำงานใน tester

---

## 4. Stage 0 — Expectancy Proof Plan
> รายละเอียดทั้งหมด (sim architecture, params, metrics, stress, pass/fail gate, verify protocol) ย้ายไป **[`TRELLIS-002_expectancy_sim_plan.md`](TRELLIS-002_expectancy_sim_plan.md)**

สาระย่อ: ต้องพิสูจน์ด้วยตัวเลขว่า **net expectancy เป็นบวกหลังหัก cost** บน XAUUSD **ก่อนเขียน `.mq5`** — ไม่ผ่าน → **ไม่เขียน EA** (Grid Doctrine #1, กัน curve-fitting trap)

---

## 5. Open Questions (ต้องตัดสินใจกับ user)
- [ ] Lot scaling จริงจะเอาแบบไหน — fixed-add, mild geometric (≤1.2), หรือ flat? (StartLot 0.01 ต้องคิด step rounding)
- [ ] Basket TP เป็น % balance หรือ $ คงที่?
- [ ] Basket hard-stop ที่กี่ % ต่อ cycle?
- [ ] Market แรกที่โฟกัส — XAUUSD only ก่อน แล้วค่อยขยาย?
- [ ] มี tick data Gold พร้อมใช้ไหม หรือต้องดึงใหม่?
