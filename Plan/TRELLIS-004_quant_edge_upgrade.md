# TRELLIS-004 — Quant Edge Upgrade (v2)

**เวอร์ชัน:** v2 (2026-06-29) — แก้ตาม Engineer review + Claude Verify
**สถานะ:** DRAFT — รอวินอนุมัติก่อนเขียนโค้ด
**เป้าหมาย (วิน):** **generate profit + อยู่รอด** XAUUSD M1 ด้วย quant model · implement MQL5 ตรง

---

## 1. ปัญหา + root cause (empirical)
pure grid scalper (naive fade) ระเบิด **$1000→$19.79 (−98%)** · 84 hard-stop (trend run-over) กลบ 539 small TP · **root cause:** entry ไร้ edge → เปิด grid สวน trend · + risk layer ไม่มี cumulative cap → bleed to zero

## 2. แก้ 2 แกน (root cause)
- **(A) Entry edge:** เปิด grid **เฉพาะตลาด choppy/ranging** (ไม่ trending) + **ตัด basket ที่ไม่ revert ตามเวลาคาด** (falsification)
- **(B) Survival cap:** cumulative catastrophe HALT (กัน −98% ซ้ำ) — โดย**ยังเทรดต่อเนื่อง** (ไม่ใช่หยุด 2 วัน)

---

## 3. Quant model (v2 — แก้ defect เชิงสถิติ)

### 3.1 Regime gate = Efficiency Ratio (Kaufman) — แทน AR(1) [แก้ C1]
- `ER = |p_t − p_{t−N}| / Σ|Δp_i|` บน M1 closed bars ย้อนหลัง N
- ER→1 = **trending** (net move = ผลรวม move → ไม่เข้า) · ER→0 = **choppy/ranging** (→ เข้า grid ได้)
- **gate: เข้าเฉพาะ ER < InpERMax** (เช่น 0.3-0.4)
- **ทำไมแทน AR(1):** AR(1)-on-level = Dickey-Fuller unit-root regression → OLS bias ที่ φ≈1,N=100 = −0.04 → **random walk ผ่าน gate (MR ปลอม)** · ER **unbiased, O(N), ไม่มี regression** → robust
- **เสริม (option):** rolling Variance-Ratio (มี estimator validated จาก Stage 0 — bias-corrected + hetero-robust z) เป็น cross-check

### 3.2 Adaptive mean = EMA (ยอมรับตรงๆ) หรือ 2-state Kalman (level+slope) [แก้ H3]
- Kalman 1D random-walk = EWMA เป๊ะ (มี lag เท่า EMA) → **ไม่ oversell**
- **ถ้าจะใช้ "ขั้นสูง" จริง: 2-state local-linear-trend Kalman (level + slope)** — state **slope** ให้สัญญาณ trend-onset ที่ leading กว่า → ใช้ช่วย exit (slope พุ่ง = trend มา)
- mean μ ใช้ตั้ง deviation entry

### 3.3 Entry (ใน regime ที่ผ่าน)
- gate: `ER < InpERMax` (ranging)
- signal: `dev = close − μ` · เข้าเมื่อ `|dev| ≥ InpEntryDevK × ATR` · `dir = dev<0 ? BUY : SELL` (เข้าหา mean)
- **hysteresis (M5):** เข้าเกณฑ์เข้ม / ออกเกณฑ์หลวม + smooth ER (EMA) กัน whipsaw

### 3.4 Grid + Scalp TP (เดิม)
spacing = ATR(M5)×k snapshot/basket · เติม adverse ≤ max levels · basket TP = % balance → ปิดทั้ง basket

### 3.5 Exit — Half-life time-stop (falsification) [แก้ H4 — key tail reducer]
- MR คาดว่า deviation หายใน ~half-life · **ถ้า basket เปิดเกิน InpMaxBasketBars (≈2-3× half-life ที่คาด) โดยยังไม่ปิด TP → สมมติฐาน MR ถูก falsify (= trending) → ตัด basket ทันที**
- เปลี่ยน "แพ้ใหญ่ 84 ครั้ง (รอจน hard-stop)" → "ตัดตามเวลา bounded" = attack tail + bound basket age
- เสริม: ถ้าใช้ 2-state Kalman → slope พุ่งเกินเกณฑ์ = trend-onset → ตัดเร็วขึ้น
- **ดีกว่า regime-flip exit** เพราะเป็น falsification (ไม่ lag classification)

### 3.6 Risk layer (v2 — เพิ่ม cumulative cap) [แก้ C2]
- **🆕 Cumulative catastrophe HALT:** peak-equity HWM → **terminal HALT ที่ −InpMaxTotalDDPct จาก peak (เช่น 25%)** = เพดานกัน −98% ซ้ำ · **ต่ำกว่านี้เทรดต่อเนื่องปกติ** (reconcile keep-trading + survive)
- equity-stop เบรกรายวัน (resume วันใหม่) · daily-DD · margin guard · reliable close · persistence (เดิม)

---

## 4. Modules
```
Include/TrellisQuant.mqh   ← ใหม่: Efficiency Ratio + (2-state Kalman level+slope)
Include/TrellisRisk.mqh    ← เพิ่ม cumulative-DD HALT (peak HWM) + half-life time-stop hook
Experts/Trellis.mq5        ← integrate: ER gate, deviation entry, time-stop exit
```

## 5. ความซื่อสัตย์ (honest expectation — สำคัญ)
- quant model **สกัด edge + ลด tail** ไม่ "สร้าง" edge · Stage 0: Gold MR อ่อน/สั้น/อาจ microstructure/เสื่อม OOS + barrier negative-skew
- **ประเมินตรงๆ (Engineer + Claude เห็นตรงกัน):** upgrade นี้ **ปรับ survival + ลด 84 hard-stop ได้จริง (น่าจะมาก) + กันระเบิด** · แต่ **โอกาส robust net-positive บน OOS = ต่ำถึงปานกลาง** — ให้โอกาสดีที่สุด แต่ **อย่าคาดว่าพลิกบวกแน่** · MT5 tester ตัดสิน
- ⚠️ flag (Stage 0): capturable MR (~5% ของ move) << cost → ถ้ายังไม่บวก path ถัดไปอาจต้อง **TP ใหญ่ขึ้น/เทรดน้อยลง** ไม่ใช่ scalp ถี่

## 6. Validation
วินรัน MT5 GUI · XAUUSD_BT real-tick · **เทียบ baseline v1.2 (−98%)** → ดู: final balance, **hard-stop count (84 → ?)**, max DD, win/loss size, IS/OOS

## 7. Open params
InpERMax (0.3-0.4) · InpERLookback (N) · InpMaxBasketBars (time-stop) · InpEntryDevK (×ATR) · InpMaxTotalDDPct (25%) · Kalman Q/R (ถ้า 2-state) · toggles

## 8. ขั้นถัดไป
วินอนุมัติ → เขียน TrellisQuant.mqh (ER + Kalman) + เพิ่ม cumulative HALT + time-stop ใน Risk + integrate → compile → วินรัน GUI เทียบ baseline

## Changelog
- **v2 (2026-06-29):** [C1] regime gate = Efficiency Ratio แทน AR(1)-on-level (กัน Dickey-Fuller MR-ปลอม) · [C2] เพิ่ม cumulative peak-HWM catastrophe HALT (กัน −98%, ยัง keep-trading) · [H3] Kalman = EMA หรือ 2-state level+slope (ไม่ oversell) · [H4] half-life time-stop (falsification exit) แทน regime-flip · [M5/M6] hysteresis + closed-bar + guards. ที่มา: Engineer review + Claude Verify
- **v1 (2026-06-29):** OU/AR(1) + Kalman + regime-flip (มี defect C1/C2/H3)
