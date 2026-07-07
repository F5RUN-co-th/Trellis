# Trellis — Implementation Status

**Last updated:** 2026-07-04 00:45

## ✅ STAGE 0 จบสมบูรณ์ (Gate 0 PASS + Acid 1000 PASS + Issue-1 sim fix) — พร้อมเริ่ม H0
- **Gate 0:** v4f alignment 145/145+11/11 · p95|ΔR|=0.00 · skip-set mirror-cap ตรง 19/19 · 2025 gap −19.4
- **Acid @1000 PASS:** 74 ไม้ +216.1 (จบ 1216) DD 64.5 ไม่มี HALT · alignment 73/73 · 2026 n=0 ตามดีไซน์ — **ทุนน้อยรอดเอง +21.6%**
- **Issue-1 sim fix (`ea_catchup`):** sim ทำเหมือน EA จริงแล้ว (validated: v4f_25 common 149/149 flips 0 drift +0.14/ไม้) → **BASELINE H0 ใหม่: ปีแพ้ 7 ปีเดิม (2012/14/17/18/19/22/23) รวม −185.4 · TOTAL 15.5y +1,087.6 (WF config)** · EA-side ยังถือข้ามคืนจริง ~10 วัน/ปี = design question เปิดอยู่ (Issue doc)
- **ความรู้ผูกพัน:** sim-optimism high-vol ~−1.2/ไม้ (tester=authority) · **RED FLAG: real-tick 2026 capped@3000 = −$9.3 — cap กลืน edge ปี vol สูง** (survival-vs-edge = โจทย์ H0/D)
- **Stage H0 deliverable 1 เสร็จ (07-04):** regime dataset 2012–2020 + completeness gate (`Scripts/h0_features.py`+`h0_join_pnl.py` → `Research/h0/*.csv` 2,317 วัน) — Engineer PASS-with-changes 7 ข้อผนวกครบ · **CRIT-2: ปีแพ้ในหน้าต่าง search = 5 ปี −135.2 (2022/23 = confirm-only นอก window)** · hole scan ครั้งแรก: hole 40 · short 107 · absent 32 · reconciliation ปิดเป๊ะ +532.8
- **Card #1 (H1: rv_pct250 เดี่ยว) = FALSIFIED ทุกข้อ (07-04)** — T_raw p=0.093 / T_within p=0.225 / gate ทำปีแพ้แย่ลง (−135.3→−219.6) · **ความรู้: วัน low-vol ในปีแพ้กลับกำไร (2012 B1 +1.27/วัน vs B3 −3.41) — year-level story ไม่ส่งลง day-level** · `Scripts/h0_card1_rv.py` · **budget 1/40**
- **Card #2 (H2: trend-range state · slope_pct250) = FALSIFIED ทุกข้อ (07-04)** — T ทั้งสามติดลบ (−0.89/−0.92/−0.95, p≈0.97 ทิศตรงข้าม) · skip-FLAT หายนะ (pooled +532.8→+63.3) · **observation ไม่ตีความ: FLAT = วันทำเงินหลัก (+432.3) / UP-extreme = ขาดทุน (−160.7), T<0 เสถียร 8/9 ปี ทุก rv stratum — data-derived ห้าม chase โดยไม่มี external mechanism** · `h0_card2_trend.py`+`h0_cardkit.py` · **budget 2/40**
- **Batch #3–5 (range_exp/gap_ratio/aw_ratio) = FALSIFIED ทั้งสาม (07-04)** — C3 T_joint p=0.128 · C4 T_within p=0.035 ผ่านเดี่ยวแต่ T_ds1 p=0.089 (control weekend ทำงาน) · C5 ทิศกลับ · **budget 5/40**
- **⭐ H0 CONCLUDED: ตัวแปรเดี่ยว 5 ตัวครบ space — ไม่มีตัวไหนแก้ปีแพ้ได้ตามเกณฑ์ · "brain ต้องชนะ −135.2" = พิสูจน์แล้ว** · ข้อค้นพบโครงสร้าง: gate สถิตย์พลิกปีแพ้เป็นบวกได้ (C3: −135→+228) แต่ฆ่าปีชนะเสมอ → ต้อง conditional behavior ไม่ใช่ filter สถิตย์
- **STAGE B จบ (07-05):** pipeline แบบ EchoSeven (`Scripts/stageb_pipeline.py` — LLM ให้ evidence, script derive tier) · 26 claims → **T-CARD 16 / PARKED 9 / REJECTED 1** (จับ quote ตัดต่อได้จริง 1 ราย) · counter-evidence ติด claim ถาวร (overnight-drift ตาย 2021 · Osler=FX 90s หน่วย bp · practitioner เลข audit ไม่ได้) · `Research/STAGE_B_HARVEST.md`
- **Gate B ผ่าน (07-05): Engineer PASS-with-changes ×3 ขอบเขต → fixes ครบ** (evidence-grade: T-STRONG 4/T-DIRECTIONAL 12 · ref-flags จับ dead refs 4 · provenance บังคับ) · **Wave-1 สรุป: C7 tick-participation > C6 poke/sweep > C9 DC-state (มี kill-gates) · C8 ตัด (lookahead)** — วินอนุมัติดำเนินการต่อ
- **Card C7 (breakout participation) = FALSIFIED (07-05)** — Engineer จับ v1 lookahead (วัด bar i แทน signal bar j) ก่อนรัน → v2 · ผล: T ดิบ +0.27 หายเกลี้ยงใต้ joint/bar-size controls (−0.02/−0.08, p≈0.5) · P3 FAIL · **budget 6/40** · commits: 423ea87/9e35e65 + งาน C7
- **Card C6 (poke) = FALSIFIED (07-05)** — ทิศถูกทั้งแผงแต่ p 0.26-0.34 · **P3(a) ผ่านเป็นใบแรก: losers −135→−55 (59%)** แต่ (b)(c) ตก · dose non-monotone (2+ pokes กลับดี) · **budget 7/40**
- **Card C9 (overshoot exhaustion) = FALSIFIED (07-05, budget 8/40)** — แต่โปรไฟล์แข็งสุดใน wave: T บวกทุก leg แข็งขึ้นใต้ controls (T_bsz +0.918 p=0.0455 ผ่านเดี่ยว · p_family 0.105) · **PS ผ่านใบแรก 6/9+4/4** · P3 pooled เป็นบวกขึ้น (+583) winners ผ่าน — ตกเฉพาะ (a) 32%<50% · ⚠ ติดป้าย SE-leak (prediction freeze ก่อน leak, การแก้ tightening-only)
- **Wave-1 ปิด + clean-room CONFIRMED ทั้งหมด** · **Gate C review จบ (07-05): Engineer CONFIRM-with-changes + Claude Verify ตรง** — ⭐ หลักฐานใหม่: **poke ⊥ overshoot (−0.081) + interaction: เซลล์ขาดทุนแท้ = SPENT∧POKED −0.581/ไม้ (n=103)** · audit ขาด: แกน exit (#7 time-stop · #10 let-winners-run ผูก RED FLAG) · แผนสุดท้าย: **Stage D first-scope = CONTINUATION vs SKIP(conjunction) + C10 MS kill-gate ขนาน (ฟรี) + defer fade + Stage F trigger-on-stall**
- **Gate C ปิดแล้ว + แผน TRELLIS-010D v1.1 + commit `2c9fd13` (07-05):** Engineer จับ H1 — **D-0.5 ceiling gate: SKIP-only เพดาน 32.4%/9.5% < §0 = documented-dead** (script `brain_v1_ceiling.py` ยืนยัน · ประหยัด WF+MQL5+GUI ทั้งเส้น) · fail-open 36.2% quantified · D-2b → skip-date-list-first
- **WS-3 lever #10 = DEAD ที่ W3-0.5 ceiling (07-05):** ทุก RUN config ทำปีแพ้แย่ลง (−135→−200 ที่ CF) ช่วยแต่ปีชนะ → **ความรู้กลับด้าน: trail คือผู้ปกป้องปีแพ้บนสนาม search — RED FLAG ต้องแยกกลไก cap-skip ≠ trail-truncation** · `brain_v1_run.py` regressions 1,487/1,487 exact (จับ+แก้ root cause R-precision) · OVERCLAIM = SE acknowledged
- **W3 verified ครบ 3 ชั้น: clean-room CONFIRMED-DEAD** (reproduce 6/6 claims · artifact diff 0/1,487) · dead-code cleaned · **commit `9197794`**
- **Lever #7 time-stop = FAIL ที่ W7-0.5 ceiling (07-05) แต่เฉียด+อ่อนโยนที่สุด:** CS+PF ช่วยปีแพ้ **41.2%** (เกณฑ์ 50%) ปีชนะแทบไม่เสีย · pooled +12.3% · kill-vector ที่ทายไว้ (winners) ไม่เกิด · CF-underwater ถูกกันออก = FAIL ไม่ล้างมลทินเต็ม (C-1 pre-registered)
- **#7 FULLY-FREE (32cfg) = DEAD ที่ W7f-0.5 (07-07):** free ทั้ง 5 เซลล์ (SE M1-M8, วินเลือก fully-free) → GATE FAIL · best CF+CS+PF **loseImp 75.3%** (restated prediction ถูก: 83.9% ของ loss ปีแพ้อยู่ใน CF) · **[Engineer P1 แก้] BINDING = pooled อย่างเดียว** (winners 577.1 PASS · ตกแค่ pooled 543.7<692.6) · FO time-stop เป็นพิษ (−120%) → **§0 pooled = edge-generation wall: reshaping (skip/exit) 3 lever ทั้งหมด cap ~577-598 < 692.6 · exit-axis ปิดสนิท** · gate bug M1/M2 แก้ + ceiling() พิมพ์ BINDING field เอง
- **C10 (H10 market-structure) = FALSIFIED ที่ budget 9/40 (07-07):** ทิศถูก ALIGNED +0.380 > OPPOSED +0.015 ทุก leg บวก แต่ underpowered (p 0.26-0.32, ไม่มี leg ถึง α) · P3 skip-OPPOSED losers −72.2 (46.6% เฉียด) pooled FAIL · **MS ไม่เพิ่มข้อมูลเกิน feature เดิม → fold nothing · Stage D คง 2 แกน (poke×overshoot)** · slope re-encoding ตัดทิ้ง (+0.041) · BH 9 ใบ ไม่มีตัวรอด
- **⛔ STOP: exit-axis ปิดสนิท (reshaping สร้าง pooled ไม่ได้ · 3 lever พิสูจน์) + C10 falsified — ทิศ Stage D = คำถาม requirement ของวิน:** §0 pooled = edge-generation problem → ทางที่เหลือ additive เท่านั้น: (a) entry/signal-axis ใหม่ (trade วันที่ v4 ข้าม) (b) sizing (ปลด flat-lot lock) (c) fade F4-deferred (d) Stage F new data · **+ คำถามลึก: §0 pooled +30% เข้มไปไหม เมื่อ config กู้ losers +75% ที่ pooled เท่าเดิมได้ (survival vs edge)** · budget 9/40 · Verify 3 ชั้น CONFIRMED ทั้งสอง · Engineer deep-review จับ P1 แก้แล้ว · commit `2ce0937` (+P1 fix รอ commit)

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
