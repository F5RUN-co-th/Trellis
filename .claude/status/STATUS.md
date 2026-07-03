# Trellis — Implementation Status

**Last updated:** 2026-07-04 00:45

## ✅ GATE 0 ปิดแล้ว (PASS conditional — Engineer verdict, ดู TRELLIS-010 Progress Log)
- **Clock bug ปิดเด็ดขาด:** v4f alignment 145/145 + 11/11 · p95|ΔR| = 0.00 · skip-set (mirror-cap@3000) ตรง 7/7+12/12 · 2025 gap −19.4 · 137 วันปกติ drift +0.17/ไม้
- **ความรู้ใหม่ที่ผูกทุก stage ถัดไป:** (1) overnight-hold **asymmetric** sim vs EA ~12 วัน/ปี (Issue doc แก้แล้ว) (2) **sim-optimism ยุค high-vol ~−1.2/ไม้** — เลข sim ยุค 2026 ต้อง re-validate real-tick ก่อน quote (3) **RED FLAG: real-tick 2026 capped@3000 = −$9.3** — cap กลืน edge ปี vol สูง (survival-vs-edge tension = โจทย์ stage ถัดไป)
- **Next: acid test `v4e_full` deposit 1000** (pred: 2025 n=75/+208.2/DD101 · 2026 n=0 โดยดีไซน์) → แล้วเริ่ม TRELLIS-010 Stage H0

## 🔴 TRELLIS-010 Stage 0: เจอ CLOCK BUG — เลข tester 2025/2026 และ holdout เดิมถูก re-baseline
- **Root cause (พิสูจน์ครบ ดู Plan/TRELLIS-010 Progress Log):** tick 2025+2026 ใน XAUUSD_BT เป็น **UTC+0 ดิบ** (generator `ticks_to_mt5ticks.py` ไม่ shift + rename `_eet_`) ขณะ 2011–24 ถูก → tester 2025/26 test คนละ session
- **เลขที่ตาย:** tester 2025 **−169** / v4d 2026 **+330** / aggregate 38 เดือน **+318** = artifact ใช้ไม่ได้ · "tracking noise ±$5/ไม้" = ผิด — drift จริงหลัง clock align = **−0.03..−0.25/ไม้ ทุกปี** (sim↔tester แนบกว่าที่เคยเชื่อมาก)
- **BT-clock = EET กฎ EU-DST** (last Sun Mar/Oct) — ที่เคยประกาศ "US-DST" ผิด (ก.พ.+ฤดูร้อนแยกกฎไม่ได้ · price-match shoulder week ชี้ EU) → **EA `IsEuDST` แก้+deploy 16:06** (tester HourShift=0 ไม่กระทบ)
- **HOLDOUT Exness แก้เลขเป็น +$511.8 PF 1.54 maxDD 320** (`Scripts/holdout_exness.py` — commit แล้ว, reproduce ได้) — เลขเดิม +802.5/PF2.24 มาจากกฎ US ผิด ช่วง shoulder มี.ค. (+340→+50) · **ห้ามเลือกกฎจาก P&L** — กฎมาจาก ground truth data · ยังบวกทุกเดือน = mirror/edge ยังยืน แต่เจียมลง
- **สถานะ fix:** ไฟล์ EET ถูก copy เข้า MQL5\Files แล้ว ✓ · `ImportCustomTicks` v1.10 (pre-flight + clean whole-range delete ตามคำสั่งวิน) compile+deploy ✓ · generator แก้+พิสูจน์ SHA256 ตรงไฟล์ดี ✓ · **รอวิน: re-import 2025-2026 + rerun tester `v4f_25`/`v4f_2601` → Gate 0**
- **เลื่อน:** acid test `v4e_full` + demo forward — รอ Gate 0 ผ่านก่อน (ไม่งั้นรันบน data ผิด clock)
- เลขที่**ไม่**ปนเปื้อน: sim 15.5 ปี / WF OOS +$876 (สนาม sim) / tester 2023-24 +157 (clock ถูก, align 170/170)

## Risk-cap (C_MAX_RISK_FRAC=2%) — deploy 12:00 (ยังอยู่ รอ acid test หลัง Gate 0)
- ข้ามวันที่ 1×R > 2% equity — $1,000 อยู่รอดทุกยุคใน sim (2025-26: bal 1208 เทรด 75 ข้าม 100) · self-regulating: พอร์ตโต→เพดานขยาย
- Cross-check สองแหล่งผ่าน (Δ median $0.33 ≈ spread) · `Scripts/ExportM1.mq5` = เครื่องมือดึง data broker (Dukascopy 503 อยู่)

## ★ Active: Trellis v4.00 "Dual Asian-Range Breakout" — implemented + deployed รอ MT5 confirm
**Pivot จาก grid-scalp (falsified) → trend-continuation** — พิสูจน์ offline บน M1 จริง 15.5 ปี (Scripts/asian_bo_sim.py, pessimistic fills):
- **Logic:** LONG = M1 close แรกของวันทะลุ Asian-high(01–08 server) ช่วง 08–20 + close>EMA2880 + slope 1 วัน >0.1% ราคา · SHORT = mirror (ศูนย์ param ใหม่) · stop = ขอบ Asian ตรงข้าม (SL จริง, cap 1×R) · trail arm 1×R dist 0.75×R · EOD 23:00 · 1 เทรด/วัน · 0.01 lot
- **ผล sim (0.01 lot):** 2011 +87 · 2012–20 +40 · 2022 +8 · 2023–24 +155 · 2025–26 +431 → **รวม ≈ +$722/15.5ปี · worst year −$146 (2012) · PF ปี trend 1.1–1.6**
- **Integrity ที่ประกาศ:** dual ไม่มี holdout เหลือ — ค้ำด้วย mirror-no-new-param + 15 ปี + รอ MT5 real-tick / demo forward เป็นด่านจริง
- ลำดับพิสูจน์กลางคืน: k=0 MR = artifact (16k signals จริง แพ้ cost) → edge screen 2 รอบ (MR ตายทุก bucket, cost $0.40 = ผนัง) → Asian BO IS plateau → OOS 25-26 +851/22 −160 → slope filter → decade check → short mirror
- EA: `Trellis.mq5` v4.00 (single position, TrellisRisk+TrellisDiag เดิม, SL server-side, reason `eod`/`sl-exit`) — **ผ่าน Engineer review (GO-with-fixes) → แก้ครบ B2 (range-tracking/IsNewBar) B3 (EOD catch-up = flat ก่อน weekend โครงสร้าง) B4 (persist state) → compile 0/0 deploy 05:00**
- **Engineer verdict evidence: NO-GO ในฐานะ proven edge** — Claude verify เห็นด้วย: bootstrap CI95=[−518,+2008] P(≤0)=12.9% · กำไรกระจุก 2023-26 · dual ไม่มี OOS เหลือ → สถานะที่ถูกต้อง = "candidate มีหลักฐานเบื้องต้น + ระบบทดสอบครบ" ไม่ใช่ "edge พิสูจน์แล้ว"
- **Canonical script:** `Scripts/dual_asian_sim.py` (reproduce ทุกตัวเลข + sensitivity + bootstrap) — ตัวเลข v4 ทั้งหมดต้องมาจากไฟล์นี้เท่านั้น
- **★ Anchored walk-forward ผ่านแล้ว (05:15):** OOS 2015-2026 **+$785.6 PF 1.11** · selection เสถียร 11/12 ปี เลือก `CAP1.0/D1.0/SLOPE0.0005/dual` · positive skew (แพ้เล็กชนะใหญ่ ไม่มีปีหายนะ) · P(≤0)=10.4% · EA อัปเดตเป็น WF config + deploy แล้ว
- **MT5 confirm รอบแรก (09:49):** v4_2324 **PASS** (+$155 vs sim +$137, n ตรง) · v4_2526 **จับบั๊ก weekend-HALT** (ศุกร์ปิดเร็ว→ถือข้าม weekend→reject 10 ticks→HALT) → **fix: Friday-flat 20:00 + retry 100 + sim mirror** → rerun: WF ดีขึ้น **+$876 P(≤0)=7.6%** · deploy 10:03 (ดู TRELLIS-009 §8)
- **งานถัดไป:** (1) วินรันซ้ำ 2 รอบ tag `v4b_2324` (คาด **~+$176 / ~338**) + `v4b_2526` (คาด **~+$367 / ~175**) — ±ครึ่ง = ผ่าน (2) demo forward ≥1 เดือน · MT5 = code-fidelity ไม่ใช่หลักฐาน edge

## Done คืนนี้: Phase B ค้น entry สำหรับ grid → ผล = สถาปัตยกรรม scalp-TP ถูก falsify สมบูรณ์
Platform calibrate 100% (entry_platform.py) · k=0 discriminator จริงแต่ landing ที่ 0 หลัง cost · FE median ของ entry ดี = 2× ของ TP cap → นำไปสู่ v4

## ผล TRELLIS-007 Phase A (2026-07-03): **FAIL ตามเกณฑ์ §5.2** — exit engineering ถูก falsify เชิงประจักษ์
- v3 pooled −$1,949 vs v2 −$1,904 (แย่ลงเล็กน้อย) · HALT 8/8 เท่าเดิม (แค่ช้าลง: อยู่รอด 8–18 วัน vs 4–23)
- **Thousand-cuts ยืนยันเชิงตัวเลข:** deep-tail −$3,318 (205 baskets) → depth-falsify −$3,757 (**308 cuts = 1.50×** — Engineer ทำนาย breakeven ที่ 1.48×)
- **G1 ทำงานเชิงกลไกสมบูรณ์** (same-dir ≤3นาที: 45-48 → **0**, rate 94-96%→44-46%) แต่ **$ delta ≈ 0** (A/B: +0.1/+0.3) — เปลี่ยนเส้นทางเงิน ไม่เปลี่ยนผลรวม
- ที่ดีขึ้นจริง: hard-stop tail −$1,601→−$110.6 · avgL −10.81→−7.41 · worst cut −32.8 · max levels = 4 เป๊ะ
- **Root cause:** expectancy ต่อ basket ติดลบจาก entry ไร้ edge (fade ทุก 1-ATR deviation) — exit ทำได้แค่ reshape distribution · ทุก window ลงไปชนพื้น HALT −25% เหมือนกันหมด
- **ทางที่เหลือตาม doc §3/§6:** Phase B entry brain (TRELLIS-008 — extended diag features) · ห้าม tune param วน — รอวินสั่ง

## Done: TRELLIS-007 v3.00 implement + validation 10 รอบ
- Doc: `Plan/TRELLIS-007_smart_exit_grid.md` v3 — ผ่าน Engineer review 2 รอบ (รอบ 2 อิสระ: PASS with mandatory changes → เติมครบ) + Claude Verify (ตัวเลข 2 ชั้น)
- Implement แล้ว: **E1** depth-falsify (cap 4 ไม้, guard ก่อนเปิดไม้ 5, return ทันที) · **G1** re-entry guard (state ใน CTrellisRisk `m_blocked_dir` persist+tester-clear, unblock = close[1] ข้าม ema[1] ทุก new bar, arm ใน transition ก่อน TryEntry, single-slot overwrite) · **X1** RequestClose ปิด same-tick
- Compile 0/0 ✅ deploy ex5+source ✅ · `diag_analyze.py` รู้จัก reason `depth-falsify` แล้ว
- **วินรัน:** 8 windows เดิม tag `v3_66q1`..`v3_67q4` + A/B `InpUseReentryGuard=false` 2 windows (tag `v3ng_66q3`,`v3ng_67q3`) — settings อื่นเดิมทุกค่า
- เกณฑ์ผ่าน (doc §5): pooled ดีขึ้น + ≥6/8 + worst ไม่แย่ลง >10% + deep-tail ไม่ย้ายถัง + churn ไม่เพิ่ม · G1 ตัดสินจาก (E1+G1)−(E1) เท่านั้น
- ⚠️ 8 windows = in-sample · True OOS (2022/2025) ห้ามแตะจน freeze
- Out-of-scope logged: weekend-gap guard ไม่มี (pre-existing, Doctrine #6) · diag last-tick label cosmetic

## Done: TRELLIS-DIAG (ขั้น 1 — วินอนุมัติ 2026-07-03)
Per-basket diagnostic log บน grid v2 (v2.01, non-behavioral) — ตอบ: (Q1) losers เคยใกล้ breakeven ไหม (MFE/MAE) · (Q2) entry context ชนะ vs แพ้ · (Q3) loss ต่อ exit reason
- `Include/TrellisDiag.mqh` ✅ ใหม่ · `TrellisRisk.mqh` +CloseReason accessor · `Trellis.mq5` hooks · `Scripts/diag_analyze.py` ✅ (tested กับ synthetic CSV)
- Compile 0/0 ✅ · deployed ex5+source เข้า MQL5 tree ✅
- **รอวินรัน tester** (setting+ช่วงเดิมของ v2 round, `InpDiagTag="v2r1"`) → CSV ที่ `Terminal\Common\Files\Trellis_diag_770001_v2r1.csv`
- เกณฑ์ neutrality: net ต้องตรงรอบ v2 เดิม (−24.5%) — เพี้ยน = diag แตะพฤติกรรม ต้องหยุดสอบสวน
- ถัดไป: ขั้น 2 = TRELLIS-007 design จากข้อมูล (entry brain + loss-side) — รออนุมัติแยก
- Issue แยก (out-of-scope): `Scripts/deploy.sh` ก๊อปแค่ .ex5 ไม่ก๊อป source ที่ tester ต้องใช้

## Current Stage
**Stage 1–2 — EA Design & Build** (pivot จาก Stage 0)

Stage 0 (Python expectancy proof) จบแบบ **inconclusive** — bracket คร่อม 0, Python sim ชน fidelity ceiling.
วินตัดสิน (2026-06-28): เขียน EA จริง + พิสูจน์ใน **MT5 Strategy Tester 99% real-tick** (authoritative กว่า).
เป้าหมาย: **"generate profit + อยู่รอด"** · **survival-first** design.
→ ดู `Plan/TRELLIS-003_EA_implementation_plan.md`

## Roadmap
| Stage | งาน | สถานะ |
|-------|------|--------|
| 0 | Expectancy proof (Python sim) | ✅ จบ (inconclusive → pivot) |
| 1 | EA architecture + Risk Controller | ⏳ รออนุมัติ TRELLIS-003 |
| 2 | MQL5 modules (Risk/Lot/Basket/Grid/Entry) | ⬜ |
| 3 | MT5 99%-tick backtest (XAUUSD_BT, IS/OOS + stress) | ⬜ |
| 4 | Robustness (walk-forward, ไม่ใช่ optimize เปล่า) | ⬜ |

## Modules (planned — TRELLIS-003 §2-3)
| Module | File | สถานะ |
|--------|------|--------|
| Risk Controller | `Include/TrellisRisk.mqh` | ✅ Phase 1 — **functional VERIFIED บน XAUUSD_BT real-tick** (hard-stop/CLOSING/equity-delta/peak-DD HWM ยิงจริง) + แก้ bug consec-lock (reset/วัน) |
| Lot | `Include/TrellisLot.mqh` | ⬜ (NormalizeLot อยู่ใน main ชั่วคราว) |
| Basket Manager | `Include/TrellisBasket.mqh` | ⬜ |
| Grid Engine | `Include/TrellisGrid.mqh` | ⬜ |
| Entry | `Include/TrellisEntry.mqh` | ⬜ |
| Main | `Experts/Trellis.mq5` | ✅ Phase 1 skeleton (OnInit/OnTick/OnDeinit + debug harness, compile 0/0) |

## Locked decisions (TRELLIS-002 §10)
flat lot 0.01 · one-at-a-time basket · TP = $/R unit · Exness swap-free · no hedge recovery

## Blockers — รอวิน (TRELLIS-003 §8)
account model (Standard/Raw) · basket hard-stop เพดาน · basket TP · daily DD + equity stop % · max levels + spacing k · entry detail · starting balance

## Knowledge artifacts (Stage 0 — เก็บไว้)
`Scripts/layer0_meanrev_pregate.py` · `layer1_null_test.py` · `layer2_real_data.py` · `layer2b_bar_null.py` · `grid_sim.py` · `Research/*.json` · `Research/GRID_MARTINGALE_INDUSTRY_RESEARCH.md`
