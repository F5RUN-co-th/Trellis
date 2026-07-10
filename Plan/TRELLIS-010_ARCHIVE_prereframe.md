# TRELLIS-010 — Pre-Reframe Narrative ARCHIVE (FROZEN SNAPSHOT)

> **FROZEN · ครั้งเดียว · lint/DoD EXEMPT.** เนื้อหา = narrative ก่อน OFFENSIVE REFRAME (2026-07-07) ย้ายจาก `STATUS.md` เพื่อให้ STATUS เหลือ build/stage · ผลปัจจุบัน (current-frame) อยู่ `TRELLIS-010_LEDGER.md`
> **ไม่ใช่ live SoR** — เลขในนี้เป็นบันทึกประวัติ (ปีแพ้ H0/clock-bug/v4-build/TRELLIS-007-008-DIAG/Stage-0) · current-frame ที่พึ่งเลขเหล่านี้ → ดู LEDGER `## CARRIED-FORWARD`
> snapshot timestamp เดิม STATUS: 2026-07-04 00:45 (+ session 07-05..07 pre-reframe entries)

---

## Stage 0 + H0 Hypothesis-Elimination (pre-reframe · 2026-07-04..07)

- **Gate 0:** v4f alignment 145/145+11/11 · p95|ΔR|=0.00 · skip-set mirror-cap ตรง 19/19 · 2025 gap −19.4
- **Acid @1000 PASS:** 74 ไม้ +216.1 (จบ 1216) DD 64.5 ไม่มี HALT · alignment 73/73 · 2026 n=0 ตามดีไซน์ — ทุนน้อยรอดเอง +21.6%
- **Issue-1 sim fix (`ea_catchup`):** sim ทำเหมือน EA จริง (validated: v4f_25 common 149/149 flips 0 drift +0.14/ไม้) → BASELINE H0: ปีแพ้ 7 ปี (2012/14/17/18/19/22/23) รวม −185.4 · TOTAL 15.5y +1,087.6 (WF) · EA ถือข้ามคืนจริง ~10 วัน/ปี = design Q เปิด
- **ความรู้ผูกพัน:** sim-optimism high-vol ~−1.2/ไม้ (tester=authority) · RED FLAG: real-tick 2026 capped@3000 = −$9.3 cap กลืน edge ปี vol สูง
- **H0 deliverable 1 (07-04):** regime dataset 2012–2020 + completeness gate (`h0_features.py`+`h0_join_pnl.py` → `Research/h0/*.csv` 2,317 วัน) — Engineer PASS-with-changes 7 · CRIT-2: ปีแพ้ใน search window = 5 ปี −135.2 · reconciliation ปิดเป๊ะ +532.8
- **Card #1 (rv_pct250) = FALSIFIED (07-04)** — T_raw p=0.093 / T_within p=0.225 · วัน low-vol ในปีแพ้กลับกำไร (2012 B1 +1.27 vs B3 −3.41) · budget 1/40
- **Card #2 (trend-range slope_pct250) = FALSIFIED (07-04)** — T ติดลบทั้งสาม (p≈0.97 ทิศตรงข้าม) · FLAG=วันทำเงินหลัก (+432.3) UP-extreme=ขาดทุน (−160.7) · budget 2/40
- **Batch #3–5 (range_exp/gap_ratio/aw_ratio) = FALSIFIED (07-04)** — budget 5/40
- **⭐ H0 CONCLUDED:** ตัวแปรเดี่ยว 5 ตัวครบ space ไม่มีตัวไหนแก้ปีแพ้ · "brain ต้องชนะ −135.2" พิสูจน์แล้ว · gate สถิตย์พลิกปีแพ้เป็นบวกได้ (C3 −135→+228) แต่ฆ่าปีชนะ → ต้อง conditional behavior
- **STAGE B (07-05):** pipeline EchoSeven (`stageb_pipeline.py`) · 26 claims → T-CARD 16 / PARKED 9 / REJECTED 1 · `Research/STAGE_B_HARVEST.md`
- **Gate B (07-05):** Engineer PASS-with-changes ×3 · Wave-1: C7 tick-participation > C6 poke/sweep > C9 DC-state · C8 ตัด (lookahead)
- **Card C7 (breakout participation) = FALSIFIED (07-05)** — Engineer จับ v1 lookahead → v2 · T ดิบ +0.27 หายใต้ controls · budget 6/40 · commits 423ea87/9e35e65
- **Card C6 (poke) = FALSIFIED (07-05)** — p 0.26-0.34 · P3(a) losers −135→−55 แต่ (b)(c) ตก · budget 7/40
- **Card C9 (overshoot exhaustion) = FALSIFIED (07-05)** — โปรไฟล์แข็งสุด (T_bsz +0.918 p=0.0455 · p_family 0.105) ตกเฉพาะ (a) 32%<50% · SE-leak ป้าย · budget 8/40
- **Gate C (07-05):** poke ⊥ overshoot (−0.081) · interaction SPENT∧POKED −0.581/ไม้ (n=103) · Engineer CONFIRM-with-changes
- **D-0.5 ceiling gate (07-05):** SKIP-only เพดาน 32.4%/9.5% < §0 = documented-dead (`brain_v1_ceiling.py`) · commit 2c9fd13
- **WS-3 lever #10 DEAD (07-05):** ทุก config ทำปีแพ้แย่ลง (−135→−200) · trail = ผู้ปกป้องปีแพ้ · `brain_v1_run.py` regressions 1,487/1,487 exact (R-precision root fix) · commit 9197794
- **Lever #7 time-stop FAIL (07-05):** CS+PF ช่วยปีแพ้ 41.2% (<50%) · #7 FULLY-FREE DEAD (07-07): loseImp 75.3% · BINDING=pooled · exit-axis ปิดสนิท (reshaping cap ~577-598 < 692.6) · gate bug M1/M2 fix
- **C10 (market-structure) = FALSIFIED (07-07, budget 9/40)** — ALIGNED +0.380 > OPPOSED +0.015 แต่ underpowered (p 0.26-0.32) · MS ไม่เพิ่มข้อมูลเกิน feature เดิม · commit 9db2e36

## Clock Bug (pre-reframe Stage 0 · re-baseline tester)
- **Root cause:** tick 2025+2026 ใน XAUUSD_BT = UTC+0 ดิบ (generator ไม่ shift) ขณะ 2011–24 ถูก → tester 2025/26 test คนละ session
- **เลขที่ตาย:** tester 2025 −169 / v4d 2026 +330 / aggregate 38 เดือน +318 = artifact · drift จริงหลัง align −0.03..−0.25/ไม้
- **BT-clock = EET กฎ EU-DST** (last Sun Mar/Oct) — "US-DST" ผิด (price-match shoulder week ชี้ EU) · EA `IsEuDST` แก้+deploy
- **HOLDOUT Exness = +$511.8 PF1.54 maxDD320** (`holdout_exness.py`) — เดิม +802.5/PF2.24 มาจากกฎ US ผิด · ห้ามเลือกกฎจาก P&L
- เลขไม่ปน: sim 15.5y / WF OOS +$876 (sim) / tester 2023-24 +157 (clock ถูก align 170/170)

## v4.00 "Dual Asian-Range Breakout" build history (pre-reframe · carried → LEDGER CLAIM-0012)
- Pivot grid-scalp (falsified) → trend-continuation · offline M1 15.5y (`asian_bo_sim.py` pessimistic fills)
- Logic: LONG = M1 close แรกทะลุ Asian-high(01–08) ช่วง 08–20 + close>EMA2880 + slope>0.1% · SHORT mirror · stop=ขอบ Asian ตรงข้าม (cap 1×R) · trail arm 1×R dist 0.75×R · EOD 23:00 · 1 เทรด/วัน · 0.01 lot
- ผล sim: 2011 +87 · 2012–20 +40 · 2022 +8 · 2023–24 +155 · 2025–26 +431 → ≈+$722/15.5y · worst −$146 (2012)
- EA `Trellis.mq5` v4.00 Engineer GO-with-fixes → B2/B3/B4 แก้ครบ · compile 0/0 · **Engineer NO-GO ในฐานะ proven edge** (bootstrap CI95=[−518,+2008] P(≤0)=12.9% กระจุก 2023-26)
- Canonical `dual_asian_sim.py` · Anchored WF OOS 2015-26 +$785.6 PF1.11 → weekend-HALT fix +$876 P(≤0)7.6% · MT5 v4_2324 PASS (+155 vs sim +137)

## Phase B / TRELLIS-007 / TRELLIS-008 / DIAG (pre-reframe grid work)
- **Phase B entry search:** scalp-TP architecture falsified สมบูรณ์ · Platform calibrate 100% (`entry_platform.py`) · k=0 landing ที่ 0 หลัง cost · FE median entry = 2× TP cap → นำสู่ v4
- **TRELLIS-007 Phase A (07-03) FAIL §5.2:** v3 pooled −$1,949 vs v2 −$1,904 · thousand-cuts −$3,318→−$3,757 (1.50×) · G1 กลไกสมบูรณ์แต่ $delta≈0 · root: expectancy/basket ติดลบจาก entry ไร้ edge (fade ทุก 1-ATR)
- **TRELLIS-007 v3.00:** E1 depth-falsify (cap 4) · G1 re-entry guard · X1 RequestClose · validation 10 รอบ · `diag_analyze.py`
- **TRELLIS-DIAG (07-03):** per-basket diagnostic (MFE/MAE · entry context · loss/exit-reason) · `TrellisDiag.mqh` · neutrality net = −24.5%

## Stage 0 EA-build roadmap (TRELLIS-003 · superseded by reframe → research)
> reframe เปลี่ยนจาก EA-build เป็น research (direction edge) — roadmap นี้ frozen ประวัติ
- **Stage 0 (Python expectancy) inconclusive** → Win pivot (2026-06-28): EA จริง + MT5 99% real-tick
- Roadmap: 0 Expectancy✅→1 EA arch⏳→2 MQL5 modules→3 99%-tick BT→4 robustness
- Modules: Risk Controller ✅ Phase-1 VERIFIED · Main ✅ skeleton · Lot/Basket/Grid/Entry ⬜
- Locked (TRELLIS-002 §10): flat lot 0.01 · one-at-a-time basket · TP=$/R · swap-free · no hedge recovery
- Blockers รอวิน: account model · basket hard-stop · basket TP · daily DD/equity stop% · max levels+spacing · starting balance
- Knowledge artifacts Stage 0: layer0_meanrev_pregate / layer1_null_test / layer2_real_data / layer2b_bar_null / grid_sim / Research/*.json / GRID_MARTINGALE_INDUSTRY_RESEARCH.md
- Risk-cap C_MAX_RISK_FRAC=2%: ข้ามวันที่ 1×R>2% equity · $1,000 รอดทุกยุค sim · self-regulating
