# TRELLIS-003 — EA Implementation Plan (Aggressive Grid Scalper, M1)

**เวอร์ชัน:** v2.2 (2026-06-28)
**สถานะ:** DRAFT — รอวินตอบ §8 (risk appetite) ก่อนเขียน `.mq5`
**เป้าหมาย (วินกำหนด):** **"generate profit และอยู่รอดในตลาด"** บน XAUUSD M1
**ขึ้นกับ:** [`TRELLIS-001`](TRELLIS-001_design_doctrine.md) · [`TRELLIS-002`](TRELLIS-002_expectancy_sim_plan.md) (§10 locked) · `../Research/GRID_MARTINGALE_INDUSTRY_RESEARCH.md`
**ที่มา v2:** Engineer review + Claude Verify — เติมกลไก survival ที่ v1 ขาด (margin guard, state-recovery, weekend defense, equity-delta P/L, reliable close, grid-geometry↔MR-horizon)

---

## 0. บันทึกบริบท (honest)
- **Stage 0 ไม่พิสูจน์ positive expectancy** (bracket คร่อม 0). Python sim ชน fidelity ceiling
- **วินตัดสิน (2026-06-28):** ย้ายด่านพิสูจน์ไป **MT5 Strategy Tester 99% real-tick** + เขียน EA จริง
- **ความรู้ Stage 0 ที่ใช้ออกแบบ:** MR ของ Gold **อ่อน + เฉพาะ ≤30-60นาที** (long horizon ≈ random/trend) · **grid ตายตอน trend** · cost พลิกผลได้ (Exness swap-free ช่วย)
- **⚠️ ยังไม่พิสูจน์ว่าบวก → "อยู่รอด" เป็นเงื่อนไขบังคับเหนือ "กำไร"** · ห้าม live ก่อนผ่าน MT5 tester + demo

---

## 1. Success Criteria ("profit + survive")
**อยู่รอด (binding — ผ่านก่อน):**
- ไม่มี margin call / blow-up ตลอด 2011–2026 (รวม stress 2013/2020/2024-25 + weekend gaps)
- Max equity DD ≤ เพดานวิน · **min margin-level ที่แตะ ต้องห่าง stop-out** (รอดด้วย margin ไม่ใช่โชค)
- worst single-basket realized loss (รวม overshoot) ≤ nominal hard-stop × buffer
**กำไร:** net บวกหลัง cost จริง (Exness Raw) บน OOS · PF > 1 · เสถียรใน robustness grid

---

## 2. Architecture (MQL5 modular)
```
Experts/Trellis.mq5          ← main: OnInit/OnTick/OnDeinit + orchestration (§2.1)
Include/
  TrellisRisk.mqh            ← Risk Controller = KILL-SWITCH LAYER (สร้างก่อน)
  TrellisLot.mqh             ← lot + normalize volume step
  TrellisBasket.mqh          ← Basket Manager (equity-delta P/L, TP, reliable close)
  TrellisGrid.mqh            ← Grid Engine (ATR snapshot/basket, fills)
  TrellisEntry.mqh           ← Entry (pullback M1)
```
Magic prefix `TRL` ต่อ symbol · CTrade · **positions เปิดโดยไม่ตั้ง SL/TP รายไม้** (basket-managed กัน broker ปิดขาเดียว desync) · backward position loop · `SetTypeFillingBySymbol` (ไม่ hardcode FOK)

### 2.1 OnTick Orchestration (ลำดับ = survival-critical — M9)
ทุก tick ตามลำดับ:
1. update equity/DD/margin-level
2. **reconstruct/validate basket** จาก positions (C2)
3. **KILL-SWITCH ก่อนสุด:** equity-stop / daily-DD / margin-level breach → **CloseAll (retry จนแบน) + halt**
4. ถ้า basket เปิด: hard-stop → TP → trend-pause → grid-add (เช็ค margin/exposure)
5. ถ้าไม่มี basket: spread/DD/news/consecutive-loss guard → **entry (เฉพาะ new closed M1 bar)**

**State machine (❌ ไม่มี RECOVERY — กัน martingale/hedge, Doctrine #2):**
```
RECONSTRUCT (OnInit: rebuild basket จาก positions) → IDLE
IDLE → ENTRY → GRID ──(TP)──► CLOSING
                   └─(KILL: hard-stop/equity/margin)─► CLOSING
CLOSING (retry close จน CountPositions==0) → IDLE | HALT
PAUSED (daily-DD/news/spread: block entry, ยังคุม basket เปิด, auto-resume) ⟷ IDLE
HALT (equity-stop/manual: terminal, รอ reset)
```
> RECONSTRUCT/CLOSING/PAUSED = survival states (round-7 C2/H8 + DD) · "adverse-add ตอน underwater" = พฤติกรรมปกติของ GRID state (cap ด้วย levels+hard-stop) ไม่ใช่ recovery escalation

---

## 3. Modules

### 3.1 Risk Controller (TrellisRisk.mqh) — kill-switch layer อิสระ (สร้างก่อน)
ประเมิน**ก่อนสุดทุก tick**, flatten+halt ได้เองโดยไม่พึ่ง module อื่น:
- **Basket hard-stop** (Doctrine #3/#6): ปิด basket ที่ equity-delta ≤ −X · nominal ต่ำกว่าเพดานหายนะเผื่อ overshoot
- **Equity stop** (เกราะหลักที่ leverage สูง): equity ≤ −Y% → CloseAll + halt
- **Daily DD halt:** DD วันนี้ ≥ เพดาน → หยุดเปิด basket ใหม่
- **🆕 Margin guard (C1):** ก่อนทุก grid-add เช็ค `ACCOUNT_MARGIN_LEVEL` > floor (InpMinMarginLevel เช่น 300-500%) + `ACCOUNT_MARGIN_FREE` พอ — ไม่ผ่าน = ห้ามเติม (defense-in-depth; ที่ 1:2000 equity-stop เป็นหลัก)
- **🆕 State recovery (C2 + P1):** `OnInit` reconstruct basket จาก positions magic TRL · **persist risk-state** `{equity_at_basket_open, day_start_equity, consecutive_losses, halt_flag, state}` ลง **GlobalVariable (survive restart)** — counters/flag reconstruct จาก positions ไม่ได้ (restart → daily-DD baseline เพี้ยน/halt หาย/re-enable ที่ควร pause) · RECONSTRUCT อ่านกลับ + re-run kill-checks ก่อนตัดสิน IDLE
- **🆕 Weekend/gap defense (C3):** `InpFlatBeforeWeekend` ปิด basket ก่อน Fri close · + size geometry กัน Mon gap (§3.4)
- **🆕 Reliable close (H8 + P2):** = **CLOSING state ข้าม tick** (ไม่ใช่ within-tick while-loop ที่ hang OnTick ตอน requote) — แต่ละ tick พยายามปิด position ที่เหลือ 1 รอบ → `CountPositions(TRL)==0` ไป IDLE/HALT, ไม่งั้นคงอยู่ CLOSING + นับ retry → escalate HALT+alert ถ้าเกิน N
- **🆕 Basket-age + consecutive-loss breaker (M11):** `InpMaxBasketAgeBars` (ปิดถ้าแก่เกิน), `InpMaxConsecutiveLosses` (streak hard-stop = trend regime → pause ยาว)
- **Spread guard:** skip entry ถ้า spread > max
- **Trend-pause** (Doctrine #7, secondary): หยุด*เติม*เมื่อ ADX/structure ยืนยัน trend สวน — **ลดความถี่ basket ลึก ไม่ใช่เกราะหลัก**
- **News filter (CSV — H6):** import high-impact news dates (NFP/FOMC/CPI 2011-26) เข้า `MQL5\Files` filter ด้วย CSV (deterministic, ทำงานใน backtest แน่ — **ไม่พึ่ง CalendarValueHistory ที่ว่างใน tester**)

### 3.2 Lot (TrellisLot.mqh)
- **Flat StartLot 0.01** (§10 #2) · **Normalize SYMBOL_VOLUME_MIN/MAX/STEP เสมอ** (Doctrine #4/T1)

### 3.3 Basket Manager (TrellisBasket.mqh)
- **🆕 Basket P/L = equity-delta (C4):** `ACCOUNT_EQUITY − equity_at_basket_open` (one-at-a-time → สะอาด, รวม swap/commission/execution จริงอัตโนมัติ) · cross-check ด้วย `Σ POSITION_PROFIT+POSITION_SWAP`
- **Basket TP** = $/R-multiple (§10 #3) ปิดทั้ง basket เมื่อถึงเป้า (TP = limit, เคารพ freeze level)
- **One-at-a-time** (§10 #7) · **❌ ไม่มี hedge recovery** (Doctrine #2)
- ปิด basket ผ่าน reliable-close ของ Risk Controller (retry จนแบน)

### 3.4 Grid Engine (TrellisGrid.mqh) — geometry ผูก Stage 0 MR-horizon (H5)
- **Spacing = ATR(14, M5) × k** — **snapshot ตอน basket เปิด (CopyBuffer closed bar index 1), fix ตลอดอายุ basket** (M10 — ไม่ recompute per-tick กัน level เลื่อน + look-ahead)
- **🆕 Bound `max_levels × spacing` ให้ full grid อยู่ในพิสัย short-horizon MR (≤30-60นาที)** — scalp สั้น ตัดก่อนกลายเป็น deep recovery grid (ที่ต้องการ long-horizon recovery = trend regime = ตาย) · **trend defense จริง = hard-stop cut, ไม่ใช่ trend-pause**
- **🆕 Basket-risk-budget equation (design backward — แทน position-sizing แบบ SL-ต่อไม้):**
  worst-case loss ที่ grid เต็ม (flat lot, n levels, spacing s) = **triangular sum** `lot × contract × s × n(n−1)/2` + overshoot/gap
  → **invert:** จาก basket_risk_cap $R (Doctrine #3) + plausible weekend gap G → แก้หา **max_levels / spacing / StartLot** ย้อนกลับ (ไม่ใช่ตั้ง TP ก่อนแล้วหวังรอด) · link §10 #2(lot)/#3(cap)/#5(levels,spacing) + H5 (geometry ↔ MR-horizon)
- verify fill จริงก่อนนับ (M14) · เคารพ exposure/margin cap

### 3.5 Entry (TrellisEntry.mqh)
- **Pullback M1** (MR): เข้าเมื่อ deviation จาก EMA ≥ k×ATR (harvest short-horizon MR) · ไม่สุ่มกลางตลาด · spread guard ก่อนเข้า · trend filter M15 (optional)

---

## 4. Inputs (มี unit)
StartLot(0.01) · ATRPeriod/TF(14/M5) · GridSpacingK(🔴 0.8-1.5) · MaxGridLevels(🔴 ผูก MR-horizon+gap) · BasketTP($/R 🔴) · BasketHardStop(🔴 เพดาน) · DailyDDPct/EquityStopPct(🔴) · **MinMarginLevel** · **MaxBasketAgeBars** · **MaxConsecutiveLosses** · **FlatBeforeWeekend** · MaxSpreadPoints · UseTrendPause/ADX · UseNewsFilter · Magic(TRL)

---

## 5. Broker (Exness) + Cost Realism (first-class — Stage 0 พิสูจน์ cost พลิก sign)
XAUUSD Digits 2-3, contract 100oz, **swap-free** (verify holding fee) · **Validation = Raw account** (comm $3.5/lot/side — match Dukascopy tick spread, honest กว่า Standard) · เช็ค TRADE_RETCODE_DONE · เคารพ stops/freeze
- **Cost = competency แยก ไม่ใช่เชิงอรรถ:** spread floor + broker markup · commission per fill (grid มี fill เยอะ) · slippage **asymmetric** (limit entry 0 / market-close มี) · swap-free holding-fee verify · **cost sensitivity ×1.5/×2** ใน validation — เพราะ expectancy คร่อม 0 → cost arithmetic = math ที่ decision-relevant สุด

---

## 6. Validation Plan (MT5 99% real-tick — ด่านพิสูจน์)
- Symbol **XAUUSD_BT** (import real ticks 2011-26, `../../Gloo/Scripts/README_IMPORT_WORKFLOW.md`) · Modeling **"Every tick based on real ticks"**
- **Cost = Raw** (commission $3.5/lot/side + tight spread) — **ไม่ใช่ Standard comm0 บน tight tick = double-benefit (H7)**
- **IS 2011-21** (tune lite) → **OOS 2022-26 เปิดครั้งเดียว** · **Stress แยก:** 2013/2020/2024-25 + weekend gaps
- **Metrics:** net profit · max equity DD% · **min margin-level reached (near-miss)** · **worst single-basket loss รวม overshoot vs nominal (verify #6)** · basket-loss tail distribution · PF/recovery · per sub-period
- **🆕 Robustness grid (M13):** หลัง OOS รัน ±20% (spacing/hard-stop/levels) → survival+profit ต้องเสถียรในย่าน ไม่ใช่ knife-edge (เกราะ curve-fit)
- **News CSV verify** ว่า filter ทำงานจริงใน tester (Doctrine #8)

---

## 7. Phased Build (survival-first — เห็นด้วย Engineer)
1. **Skeleton + Risk Controller** (kill-switch: equity/DD/margin/state-recovery/weekend/reliable-close) — เกราะก่อน
2. Lot + Basket Manager (equity-delta P/L, TP, one-at-a-time)
3. Grid Engine (ATR snapshot/basket, geometry↔MR-horizon, fills)
4. Entry (pullback) + trend filter
5. Integrate + trend-pause + news-CSV
6. Compile → MT5 tester validation (§6)
> compile+verify ทุกเฟส · ขออนุมัติต่อเฟส (CRITICAL RULE)

---

## 8. Risk Params — %-based inputs (NON-GATING ต่อความถูกต้อง engine)
> **หลักการ (วิน 2026-06-28):** survival = property ของ **engine architecture** ไม่ใช่ค่า param/ทุน · param เป็น **% ของ balance (scale-invariant)** + engine บังคับ **risk-budget invariant** (§3.4) → engine ถูกต้องสำหรับ **ช่วง** ของค่า · ค่าจริง = **knob ที่ explore ใน validation** (§6) ไม่ใช่ prerequisite ของ Phase 1
> ⚠️ engine การันตี **survival** เท่านั้น — **profit ต้องมี edge** (Stage 0 พิสูจน์ไม่ได้) → validation ตัดสิน

**Conservative defaults (Claude ตั้ง — วินปรับ risk appetite ทีหลัง):**
| param | default (% balance) |
|---|---|
| Basket hard-stop /cycle | 5% (nominal, ต่ำกว่า catastrophe + overshoot buffer) |
| Basket TP /cycle | 0.5% (หรือ R-multiple) |
| Daily DD halt | 5% |
| Equity stop (terminal) | 12% |
| Starting balance (validation) | $1,000 (scale-invariant; ทดสอบ $100 ได้) |

> **Claude/Engineer ตัดเอง (technical):** account = **Raw** · spacing k / max-levels = derive จาก risk-budget + MR-horizon + worst-case gap · entry detail · margin-floor / basket-age / consecutive-loss defaults

---

## 9. ขั้นถัดไป
วินตอบ §8 (4 ข้อ risk appetite) → ผมเริ่มเฟส 1 (skeleton + Risk Controller kill-switch) ให้ review → อนุมัติ → เขียน `.mq5`

## Changelog
- **v2.2 (2026-06-28):** §8 reframe — risk params = %-based scale-invariant inputs + conservative defaults, **NON-GATING** ต่อความถูกต้อง engine (survival=engine architecture ไม่ใช่ค่า/ทุน; profit ต้องมี edge). ปลดล็อก Phase 1 โดยไม่ต้องรอ risk-appetite values. (วิน insight)
- **v2.1 (2026-06-28):** เพิ่ม state machine เต็ม (RECONSTRUCT/CLOSING/PAUSED≠HALT, ตัด RECOVERY) §2.1 · basket-risk-budget triangular equation §3.4 · Cost-realism เป็น first-class competency §5. ที่มา: review คำวิจารณ์ ChatGPT (Engineer round 8 + Claude Verify)
- **v2 (2026-06-28):** เติม survival mechanisms (margin guard C1, state-recovery C2, weekend defense C3, equity-delta P/L C4, reliable retry-close H8, basket-age/consecutive-loss M11) · grid geometry ↔ MR-horizon + design-backward (H5) · OnTick orchestration (M9) · ATR snapshot/basket (M10) · validation = Raw + news-CSV + near-miss/robustness metrics (H6/H7/M12/M13) · §8 เหลือเฉพาะ risk-appetite. ที่มา: Engineer review + Claude Verify
- **v1 (2026-06-28):** ฉบับแรก (pivot จาก Stage 0)
