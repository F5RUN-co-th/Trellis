# TRELLIS-005 — Adaptive Win Engine (กิน edge จริงของ Gold)

**วันที่:** 2026-06-29
**สถานะ:** DRAFT — รอ Engineer review + วินอนุมัติ
**เป้าหมาย (วิน):** **เอาชนะตลาด — generate profit (= อยู่รอด)** ด้วยทุกศาสตร์ขั้นสูง ห้ามยอมแพ้

---

## 1. Insight ที่เปลี่ยนทุกอย่าง (จาก empirical v1.2 + v2)
- v2 พิสูจน์: **survival แก้ได้** (−98%→−24.5%, hard-stop 84→4) แต่ **ยังลบ** เพราะ win($1.7) << loss($20)
- **Root cause ที่ลึกกว่า param:** เราใช้ **mean-reversion grid บน Gold ที่เป็น trending instrument** · Stage 0 วัด MR อ่อน/สั้น · **เงินอยู่ที่ trend แต่ v2 หลบ trend** = ทิ้ง edge หลักทิ้ง
- **จะชนะต้อง trade edge จริงของ Gold (momentum/trend) ไม่ใช่ฝืน fade**

## 2. แกนการชนะ — Regime-Adaptive (กินทั้ง 2 ตลาด)
แทน "fade อย่างเดียว + หลบ trend" → **EA ปรับตัวตาม regime กินทั้งคู่:**

### 2.1 TREND regime (ER สูง / ADX สูง / EMA slope ชัด)
- **เข้า WITH trend (momentum)** — breakout/pullback-continuation ตามทิศ trend
- **pyramid ตาม trend** (เติมไม้ตามทาง ไม่ใช่สวน) + **trailing stop** ปล่อยกำไรวิ่ง → **win ใหญ่** (กิน trend ของ Gold)
- ตัดเร็วเมื่อ momentum หมด (slope พลิก / structure break)

### 2.2 RANGE regime (ER ต่ำ)
- **MR grid (v2 เดิม)** — fade deviation จาก EMA, basket TP เล็ก, time-stop
- ทำงานเฉพาะที่ MR มีจริง

### 2.3 Regime classifier (ensemble — ไม่พึ่งตัวเดียว)
รวมหลายสัญญาณเป็น **confidence score** (ไม่พึ่ง lagging ตัวเดียว — Doctrine #7):
- Efficiency Ratio (trend strength) · ADX · EMA slope · ATR/Bollinger width (vol regime) · session/time-of-day (Gold เคลื่อนแรงช่วง London/NY)
- เข้าเฉพาะ score สูง (high-confidence) → กรอง noise

## 3. Advanced layers (escalate ตามผล)
| Layer | ศาสตร์ | ได้อะไร |
|---|---|---|
| **L1 Regime-adaptive** | signal processing, ensemble | กิน trend + range (แกนหลัก, MQL5-native) |
| **L2 Vol-targeting sizing** | volatility scaling | lot ปรับตาม ATR → risk คงที่ + กิน edge เต็มเมื่อมั่นใจ |
| **L3 ML directional model** | gradient-boost/NN → **ONNX (MT5 OnnxRun native)** | predict P(up/revert) จาก features → gate/direct entry · ceiling สูงสุด · ต้อง train offline แล้ว export ONNX |

## 4. คงไว้ (v2 ที่ดีแล้ว)
- Risk armor: cumulative HALT −25% + daily soft-stop + margin guard + reliable close + persistence
- Grid เป็น **execution mechanism** (เติม/ปิด basket) ใช้ได้ทั้ง 2 mode

## 5. ความซื่อสัตย์
- ไม่มีวิธีไหน "การันตี" ชนะตลาด — แต่ **trade edge จริง (trend) ให้โอกาสชนะสูงกว่าฝืน MR มาก**
- ทุก layer **ต้องพิสูจน์ IS→OOS** (กัน overfit/curve-fit — Doctrine #1,#5) · plateau robust ไม่ใช่ยอดแหลม
- ML (L3): ceiling สูงแต่ overfit ง่าย + ต้อง train offline (tool ผลิต model ที่รันใน MQL5 ผ่าน ONNX — ไม่ใช่ sim เปล่า)

## 6. ลำดับสร้าง (escalate — หยุดเมื่อบวก robust)
1. **L1 Regime-adaptive (trend + range)** — แกนหลัก เขียน MQL5 → วินรัน IS/OOS
2. ถ้ายังไม่พอ → **L2 vol-sizing**
3. ถ้ายังไม่พอ → **L3 ML/ONNX**

## 7. Validation
วินรัน MT5 GUI · XAUUSD_BT real-tick · **IS 2023 / OOS 2024** · เทียบ v2 (−24.5%) · ดู: net profit, profit factor, win/loss size, max DD, **trend-mode vs range-mode P&L แยกกัน**

## Changelog
- **v1 (2026-06-29):** reframe — กิน trend (momentum) แทนหลบ · regime-adaptive dual-mode + ensemble + (vol-sizing, ML/ONNX escalation). ที่มา: empirical v2 (win/loss asymmetry) + Stage 0 (Gold = trend ไม่ใช่ MR)
