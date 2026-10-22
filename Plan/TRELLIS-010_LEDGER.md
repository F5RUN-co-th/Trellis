# TRELLIS-010 LEDGER — Research Results (single LIVE Source-of-Record)

> **ที่เดียวที่มีเลขผลปัจจุบัน.** STATUS.md = build/stage (ไม่มี result-metric) · reframe doc = doctrine/mechanism (frozen+pointer มานี่) · ARCHIVE_prereframe = narrative ก่อน reframe (frozen)
> **scope:** current-frame = offensive reframe (2026-07-07) + งาน session ถัดมา · pre-reframe → ARCHIVE
> **backfill = transcription-only** (frozen number + commit-hash ที่ commit แล้ว · no re-run/re-derive · verified-by:self) · เลขสด = รันจาก `reproduce:` ของแต่ละ claim
> **maintain:** commit ที่แตะ experiment → update CLAIM block + FRONTIER (DoD · CLAUDE.md) · `python Scripts/ledger_check.py` ต้องผ่าน

---

## CURRENT FRONTIER
Hypothesis-Elimination-Matrix (qualitative · **ไม่มีเลข posterior** · reframe §9:125) — open/eliminated ของ DIRECTION channel:
> cite convention: `[CLAIM-N]`=live/terminal · `[CLAIM-N→M]`=superseded-by-M (fact re-measured แต่ verdict มัก durable) · `[CLAIM-N DEAD]`=dead · `[CLAIM-N·mag=live]`=fact-level live ใน claim ที่ status superseded (แยก observed vs interpretation §9:128)

| Hypothesis (representation/label/pop/optim) | Evidence-so-far | สถานะ |
|---|---|---|
| Representation: **linear-univariate OHLCV** | v0 OOS +0.006R fit-fail [CLAIM-0005→0010] · marginal-MI ~0 [CLAIM-0007→0009] | **eliminated** |
| Representation: **19-feat OHLC (linear+GBM) ที่ real exit** | aggregate<0 ทุก 9 seed · ไม่มี CI-positive [CLAIM-0010] | **eliminated (seed-robust)** |
| Label: intraday `trade_R` 1R/1.5R | gates วัดผิด exit → re-measured [CLAIM-0007→0009] | **eliminated as measurement** |
| Direction มี skill ที่ **real EA exit** | v4-breakout-dir base−floor +0.582 CI-backed [CLAIM-0010] | **open (edge จริง · ceiling ยังไม่วัด)** |
| Representation: **tick-price** (in-hand เหนือ OHLC-ceiling · DPI) | tickvol 0/7 [CLAIM-0007→0009] · spread dead [CLAIM-0008 DEAD] · TP-1 nested: gated 0/9 + perm 0.805 [CLAIM-0015→0016] · **TP-2 inference-completed 07-14: p(S1·GBM-med9)=0.398 (obs +0.1215 ≈ null-elevation +0.093 — "GBM 9/9 บวก" = mechanical) · p(S2)=0.063 · ไม่มี statistic ถึง α=0.0167** [CLAIM-0016] | **eliminated (scope: 6 features · linear+GBM · real exit · MDE~+0.28 — event-stream/richer form อยู่แถว nonlinear ที่ยัง open · ไม่ใช่ proven-zero)** |
| Representation: nonlinear/event-stream/multi-scale | GBM บน 19-feat ตาย [CLAIM-0010] · ES-1: M1-DC = KILL [CLAIM-0017] · **ES-2 07-16: tick-DC = KILL** (p(S1)=0.857 [observed แย่กว่า null] · p(S2)=0.129 [เลข signal-like สุดของ event program — เหนือ null +0.15 แต่ไม่ถึง α] · baseline-28: tick เพิ่ม ~0 เหนือ M1-DC) [CLAIM-0018] | **in-hand event forms ครบ 4 (OHLC-GBM · tick-fixed-window · M1-DC · tick-DC) — ทดสอบแล้วทั้งหมด (qualitative note ไม่ใช่ falsification) · open เฉพาะ: event-functional นอก in-hand / richer nonlinear / ข้อมูลใหม่** |
| Optimization: adaptive/rolling (concept-drift remedy) | Gate-A linear AUC 0.547 ลด static-prior [CLAIM-0007→0009] · **AD-1 STAGE-1 gate = NO-DETECT readout (c̄ 0.072 « t_bar 0.203 · exploratory/foreknowledge-disclosed — ไม่ใช่ confirmatory)** · RFLIP sweep (P&L-free · §9.1 held 5/5): decay-STOP ปลอดภัย periodic ทุก P (≤1.7%) · **rolling-arm false-STOP hole P≈H = 16.7/13.3% @ρ0.10 (measured)** [CLAIM-0019] · **AD-2 rolling-recency main 07-20 = confirmatory KILL (clean freeze-commit): S1 −0.64 · point−null −0.48 · p=0.965 — recent-300 แย่กว่า random-window 96.5% (descriptive controlled) · fold2016 trigger MET+3caveats [CLAIM-0020 L1]** · **AD-3 detector 07-20 = STAGE-A KILL instrument-infeasible (Page-CUSUM corrected: detection 0% ทุก cell ที่ FPR 1.7-6.3% — SNR wall signal 0.20 < noise 0.44 · budget-exempt) [CLAIM-0021 L1] — fold2016 = NOT adjudicated (residual คง)** | **open (scoped: smooth-adaptive บน 19-feat = no-local-relationship readout [power-scoped ρ*≈0.10 · H-agnostic — ครอบทุก H · ไม่ใช่ proof-of-absence] · residual มีจริง measured = rolling/detector follow-up card justified [วินตัดสิน priority · caveat: 16.7% ค้ำ residual-existence ไม่ใช่ real-world-applicability — real slope +0.04 flat · era-flip prior n=1] · ยังไม่เทส: aperiodic / P<1 / P≥9 / ρ<0.10 [mechanism: false-STOP conservative] / fine-cadence intra-year [§6-drop] / MONO-rotation-blind [§3.0 declared · self-mitigating unproven] / representation อื่น · ไม่ใช่ proven-zero) · **AD-4 fine-cadence 09-03: certify v1 = KNOWN-DEFECT (Engineer execution-review: null retention 27.8% exact · calib-world ≠ H0 · main stub) → B′ (วินอนุมัติ): ไม่ pin/ไม่จอง/ไม่ charge · design v4 → **v5 null → Alt-G global rotation (payoff-tuple circular-shift s∈{0..m−1} ทุก fold พร้อมกัน · annual arm refit ทุก fold ต่อ draw [Alt-2] · dual statistic S1_rot/S1_evalorig · triple+stress worlds · KS⁺ eligibility · PRIMARY-fixed C1-full · RG1-RG15) หลัง Engineer deep review 23 รอบ (instance ต่างกัน · รอบ 19 (14b) PASS · รอบ 20-23 commit-readiness F1-F13/E1-E15/F-A1-A11/F23-1-8 apply แล้ว · E15 ปิดรอบ 23 (Engineer เห็นตรงกัน → วินสั่ง apply pin block หลังเห็น patch) · Engineer commit-readiness review รอบ 24 = PASS-with-changes → apply F1 deps 7 claim +return_w · F2 ship `pin_ad4.py` · F3 pin block ก่อน `__main__` · F4/F5 record) + Claude-Verify ×31 · **commit spec `8271163` 09-09 (N11 freeze) → ขั้น 2 implement 09-09: `ad4_card.py` v2 + `tp1_card.py` return_w · regress RG1-13/15 PASS · RG7 oracle 3/3 · execution-review PASS-with-changes → apply F1-F12 · RG14 pending (Progress Log 09-09)** · **RG14 raise 09-09 = spec defect §4 (comparator รันจริง = stale-cache path · ผล = ขนาด RG13 class บน geometry จริง ×1.28 sd · ไม่ใช่ falsification §6(xiii)(b)) → v6 re-entry 09-24 (วินสั่ง apply · SPEC_SHA ใหม่ใน commit message/Progress Log) → v6 C′ 09-24: RG12 ties/degeneracy = spec defect ที่สอง (null S1 ใต้ Alt-2 = mixed · RG12 เดิม abort certify ทั้งที่ p valid · Engineer probe) → RG12 collapse-only + N5 mapping + tie-loss NON-OP → C′-r2: collapse equality ตรง รหัส 0-3 · E-12(a)/(b) mechanical → C′-r3: E-12(a) ส่วนเติมเต็ม + charge ต่อตัวตน test → C′-r4: terminal state + data hash → C′-r5: phase-0 ตามเหตุการณ์ · data hash ครบ (ปิดวง card) · operative p / rule R6 ไม่เปลี่ยน** · ~~**pin sealed 09-09 (ผลรันหลัง pin — บันทึกที่นี่ + commit message เท่านั้น ห้ามเขียนกลับ card ตาม §3.5-v4 chunk bullet): `SPEC_SHA = 6b373c55a2c08f0d7973f61e3584f02c1b062251301484044d0b0553d309d9d9` (sha256 LF-normalized card) · `git hash-object card = 4b632f5c17f35392cbe3113e5bd28f52dbf2f7bc` · `card_scan.py --require-pin` → `spec-pin (J): SPEC_SHA == sha256(LF card) · KS_T_UNITS/KS_ACHIEVED/RG14_TAGS == card` · `SCAN PASS (0 hit)` · battery v10 150/150 · `KS_T_UNITS=23 · KS_ACHIEVED=0.0475 · RG14_TAGS=tuple(f"ad4_rg14_w{k}" for k in range(50))`**~~ [superseded 09-24 โดย v6 C′-r5 ด้านล่าง] · **pin ปัจจุบัน = pre-commit reseal (2026-09-24 · card แก้ pointer G1 + SPEC lineage G2 · logic ของ code ไม่เปลี่ยน): `SPEC_SHA = 98f2e73b2202f77d29c102e27103afa57cca9ff39fd837fb11ce0ebddaf82bbb` · `git hash-object card = 8532ce32f33a2eaf126c48ef3839498b5df54b10` · closure `9ed0224ca89c7d90058532f60383629b6db88e171d3d70140361fa1e384f1ace` · receipt: ~~regress + RG14 รันใหม่ (ยังไม่มี)~~ [แก้ 10-20] บน Windows: regress=True (09-24 15:54) · RG14 22/50 (job ถูก kill) → rename เป็น `regress_receipt_local_9ed0224c_rg14-22of50.json` (sha256 `8f4059b5…`) + `rg14/checkpoint_v6_local_9ed0224c_22of50.json` (`11f92be2…`) · ~~RG14 ครบชุด = รันบน .19 (Progress Log 2026-10-20)~~ [แก้ 10-22] บน .19 (S1 `958974d` · venue glibc 2.39 · runner r13): regress=True (2026-10-21 08:30:21 UTC) · rg14=True (14:05:02 UTC) · W=50 w50..w99 ตรงทุกบิตกับ r5 ทั้ง 10 field 50/50 world (ต่างเฉพาะ `closure_sha` 51d55003→9ed0224c · ตัวเลข = ชุด r5 ด้านล่าง ไม่คัดซ้ำ) · 22 world ที่ Windows รันไว้ (w50..w71) int ไม่ตรง 0/22 · max d_ulp 0 · **foreknowledge-disclosed = replication ของผลที่เห็นแล้ว 09-24 · ไม่ใช่ blind test** · ขอบเขตข้าม venue (UCRT↔glibc ตรงกัน) = path regress/RG14 เท่านั้น ไม่ครอบ main/certify · หลักยึด: closure จาก git blob `958974d` = receipt · manifest sha256 `3ee0a971…` · accept (`host19_accept.py`) STATE=PASS · archive byte-exact `Scripts/ad4_cert_out_v2/host19_958974d/` (`SHA256SUMS` 22 ไฟล์) · ยังไม่จอง claim (Progress Log 2026-10-22)** · ~~pin v6 C′-r5 = ปัจจุบัน~~ ประวัติ: **pin v6 C′-r5 (2026-09-24 · ยังไม่ commit · ผลรันหลัง pin — บันทึกที่นี่ + commit message เท่านั้น ตาม §3.5-v4 chunk bullet): `SPEC_SHA = 2c58d3b82a13707e610375687869b3f05b6ed1f8cf9a32e44ed833c6691f42ab` · `git hash-object card = 8285c83265855a47e7e451d7ac71847fe7700c96` · closure `51d55003b8ad86c3e93c417745bea0dfebd9fe466b872fbcfb002543f704e050` · `RG14_TAGS=tuple(f"ad4_rg14_w{k}" for k in range(50, 100))` · `card_scan.py --require-pin` SCAN PASS (0 hit) · battery 150/150 · receipt ~~`Scripts/ad4_cert_out_v2/regress_receipt.json`~~ [แก้ 10-20] `Scripts/ad4_cert_out_v2/regress_receipt_superseded_51d55003.json` regress=True (11:56) · rg14=True (14:38) · RG14 v6 (synthetic STABLE · W=50 · B0=99 · foreknowledge-disclosed = regression + replication · ไม่ใช่ blind test ของ card §6(xiii)(b)): Δsd mean +0.001292 SE 0.000150 upper +0.001594 · Δq95 mean +0.002326 SE 0.000468 upper +0.003266 → ไม่ raise · subset ที่ยังไม่เห็น w58-w99: lower bound Δsd +0.000945 · Δq95 +0.000962 (Engineer run 09-24) · ขนาดผล Alt-2/v5-local (Claude run จาก `rg14/checkpoint_v6.json` ของ SPEC 2c58d3b8 → archive `rg14/checkpoint_v6_r5_2c58d3b8_complete.json`): ratio-of-means sd ×1.2493 · q95 ×1.2992 · median ×1.2441 / ×1.3384 · mean-of-ratios ×1.3612 / ×1.7329 (ดึงสูงโดย q95_v5local ต่ำสุด 0.00033) → **เกินขอบบน band toy §6(xiii)(b) (+21.8% sd / +19.8% q95) ทุก estimator** · band toy ทำซ้ำไม่ได้ + card ไม่ระบุ estimator ของ band · อ่านเป็น NON-OP: null ใต้ Alt-2 กว้างกว่าที่ toy คาด → MDE floor กว้างขึ้น (ผลต่อ detection ยังไม่วัด) · ความกระจายข้าม world (Claude run): q95 ratio < 1 ใน 20% ของ world · sd ratio < 1 ใน 8% · q95 ratio สูงสุด ×10.32 (world ที่ q95_v5local = 0.00033 ดึง mean-of-ratios) · ไม่เลือก estimator เดียว (เลือกหลังเห็นข้อมูล = post-hoc)** · §0 NORMATIVE N1-N13 (+N1a glossary) · RG1-RG15 · เกณฑ์ converge (14b) วินอนุมัติ 09-07 · sha LF-normalized (R1) · rule (k) `ledger_check.py` adopt (วินมอบ technical 09-08) ~~→ Engineer review รอบ 20 → commit spec (รอวิน) → วินรับทราบ Alt-G +8.6 CPU-h (envelope §7.1 = technical decision บันทึกใน card) → commit spec → certify v2 (3,080 draws · 7-10 ชม.)~~ [process chain 09-09 · ทำแล้ว: commit spec `8271163` · สถานะปัจจุบัน = pin v6 C′-r5 ด้านบน]** · outcome pre-approved ทั้ง 2 ทาง [card §6.1/§7.1 · Progress Log 09-03 · ยังไม่มี claim]** |
| Magnitude channel (label-agnostic) | in-sample MI 6/19 (**DIAGNOSTIC/overfit-floor** · de-cluster [5,1,6]) · OOS straddle-net-cost **dead** [CLAIM-0007→0009] · "+0.66 sturdier" เดิม = demoted no-artifact · day-mean not-detected [CLAIM-0013] · at-trigger ผ่าน intraday-features = **structurally blocked** [CLAIM-0014] | **open (เฉพาะ session-open form ที่ยังไม่เทส · prior บาง · priority ต่ำ)** |
| Discovery: additive opp **realizable** ด้วย ex-ante trigger | validation 07-10: ceiling ยืน (+1.5..+4 · n~30) แต่ **0/7 trigger-config FWE** · anchor ลบ [CLAIM-0004] | **open (ceiling-only — กุญแจ = ex-ante discovery ไม่ใช่ trigger เพิ่ม)** |

**FROZEN terminal (session 07-08):** direction-at-real-exit [CLAIM-0010] · **[07-10/11] opportunity-validation: ceiling ยืน (+1.5..+4 · n~30) · realizable 0/7 FWE** [CLAIM-0004] + [CLAIM-0013] · **[07-12] at-trigger = structural-wall [CLAIM-0014] + demote "+0.66" (no-artifact) → magnitude arm ปิดโดยพฤตินัย** · **[07-13/14] tick-price arm ปิดใน scope ที่เทส: TP-1 INCONCLUSIVE gate-limited → TP-2 inference-completed = KILL [CLAIM-0016] (budget 2/40 family v3 · null-mean-elevation [run +0.093/+0.104 · calib ≈+0.12] = การค้นพบ methodology ถาวร: nested-lift point-positivity ≠ signal)** · **[07-15] ES-1 DC-multi-scale (M1) ที่ real exit = KILL [CLAIM-0017] (budget 3/40 · prediction held 2-independent+1-implied · null-mean ES เป็นลบ — elevation เป็น per-feature-set ห้ามยืมข้าม card)** · **[07-16] ES-2 tick-DC = KILL [CLAIM-0018] (budget 4/40 · population-overlap Jaccard 1.0000 = near-controlled ยืน · in-hand event forms ครบ 4 — จบ representation program ในมือ)** · **next = Win ตัดสิน** (adaptive · discovery mechanism · monetize-v4 · forward-test · Stage-F-form data ใหม่) · **[07-16/17] Win เลือก adaptive → Card AD-1: design R1-R8 → รัน STAGE-1 (07-16 เห็นผลแล้วถูกถอนตามคำสั่ง Win) → adjudication 10 รอบ → reconstruction + M8-MATCH + RFLIP sweep → record เป็น exploratory NO-DETECT readout [CLAIM-0019 · budget 5/40 family v3 — charge จาก look 07-16 · การถอน record ไม่คืน budget] → **execution-review PASS-with-changes 07-17 → L1** (F-1 stage1 self-guarding + F-2 ρ-residual applied) · rolling-arm hole P≈H measured → detector follow-up justified · next = Win ตัดสิน (**detector card** [M11 · prior อ่อน] · **fine-cadence card** [drift เร็วกว่ารายปี — มุม refit-cadence เดียวที่ยังไม่วัด (signal-residual อื่น aperiodic/P<1/ρ<0.10 = declared ยังไม่วัดเช่นกัน) · กำแพง power ~14 ไม้/เดือน < 19 feat = underdetermined บน rep ปัจจุบัน] · discovery · monetize-v4 · forward-test · Stage-F)** · **[07-20] Win เลือก recency → AD-2 confirmatory KILL [CLAIM-0020] → detector → AD-3 STAGE-A KILL [CLAIM-0021] → fine-cadence → AD-4 designed+certified 07-25 (ยังไม่ freeze/ไม่รัน · รอวิน A/B · 09-03)** · **หมายเหตุ 09-03: clock-fix Gate 0 = ปิดแล้ว 07-04 (Engineer PASS-conditional) — ข้อความ "ค้างฝั่งวิน clock-fix" ใน Progress Log 07-16 = stale**

---

## CARRIED-FORWARD DEPENDENCIES
data-artifact + เลข frozen ที่ current-frame พึ่ง (methodology อยู่ doctrine ไม่ใช่ที่นี่):

- **v4 "Dual Asian-Range Breakout" = 1 proven-behavior candidate** [CLAIM-0012] — canonical `dual_asian_sim.py` (§9:107) · WF-OOS +$876 · holdout EU-corrected **+$511.8 PF1.54** · **สถานะ = candidate ไม่ใช่ proven-edge** (bootstrap P(≤0)≈7.6%)
- **h0 SEARCH dataset 2012-2020** (`Research/h0/*.csv` · +$532.8 field · reconciliation ปิดเป๊ะ) — field-tag ของ direction claims ทั้งหมด
- **walker `brain_v1_run.py`** — canonical exit (trailing 1×R + overnight) · regression 1,487/1,487 exact · imported โดย 22 scripts (disk-count 09-08 · ~~15~~ stale [F3 รอบ 19 — site ที่ rule (k) ไม่ครอบ])
- **BASELINE H0:** ปีแพ้ 7 ปี (2012/14/17/18/19/22/23) รวม −$185.4 · 15.5y +$1,087.6 (WF config · `ea_catchup`) — search-window losers = 5 ปี −$135.2
- **clock:** BT-clock = EET EU-DST · tester 2025/26 เดิม (−169/+330/+318) = artifact (UTC ดิบ) · holdout US-rule +802 = ตาย

---

## SCRIPT INDEX
> **machine-generated skeleton** จาก `ledger_check.py --emit-index` (ASSET=import-scan · EXPERIMENT=`__main__`) · disposition = เติมเอง (ดุลพินิจ) · **ห้าม hand-list role** (DEFECT-10)
> DISP ∈ live→CLAIM-NNNN | superseded→CLAIM-NNNN | legacy→ARCHIVE | reproduce-only(why) | self-test(why)


---

- `ad1_card` :: ASSET(imported 3) :: EXPERIMENT=live→CLAIM-0019
- `ad1_gate_calib` :: ASSET(imported 2) :: EXPERIMENT=live→CLAIM-0019
- `ad2_card` :: ASSET(imported 2) :: EXPERIMENT=live→CLAIM-0020
- `ad3_card` :: EXPERIMENT=live→CLAIM-0021
- `ad4_card` :: ASSET(imported 4) :: EXPERIMENT=reproduce-only(certify v1 known-defect card §6.1 · B′ 09-03 · design v4 → certify v2 → เปลี่ยนเป็น live→claim เมื่อ freeze-commit)
- `ad4_report_fixture` :: EXPERIMENT=self-test(fixture chunk สังเคราะห์ของ cert_report_v2 · card AD-4 §7(7) · ครอบ: eligibility KS⁺ (ขอบ = t · pooled ไม่ใช่ครึ่งเดียว) + collapse h0cal/h0val · ลำดับ N5 (pending/contingency/exit 2) · α*_dec (cap/ต่ำกว่า cap/linear) · rank threshold · R6 strict · tie-loss + scope-tag · collision assert · ไม่ครอบ: pooling-invariant · staging · N11 card_sha assert · h0stress · readout NON-OP อื่น · mutation 12/12 · นอก CLOSURE_FILES)
- `asian_bo_sim` :: EXPERIMENT=legacy→ARCHIVE
- `brain_v1_ceiling` :: EXPERIMENT=legacy→ARCHIVE
- `brain_v1_run` :: ASSET(imported 22) :: EXPERIMENT=reproduce-only(canonical-walker · regression 1487/1487)
- `c10_ms_features` :: EXPERIMENT=legacy→ARCHIVE
- `c6_poke_features` :: EXPERIMENT=legacy→ARCHIVE
- `c7_tick_features` :: EXPERIMENT=legacy→ARCHIVE
- `c9_dc_features` :: EXPERIMENT=legacy→ARCHIVE
- `card_scan` :: EXPERIMENT=self-test(doc-integrity tooling · N10/N13/(A)-(I) SSOT ของ PATTERNS · card AD-4 §0 N10/N13 · รันก่อน commit)
- `diag_analyze` :: EXPERIMENT=legacy→ARCHIVE
- `dir_features` :: ASSET(imported 1)
- `direction_at_real_exit` :: ASSET(imported 9) :: EXPERIMENT=live→CLAIM-0010
- `direction_predictor` :: ASSET(imported 6) :: EXPERIMENT=superseded→CLAIM-0005
- `direction_predictor_v1` :: ASSET(imported 6) :: EXPERIMENT=superseded→CLAIM-0006
- `discovery_probe` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0004
- `dual_asian_sim` :: ASSET(imported 7) :: EXPERIMENT=reproduce-only(v4-canonical numbers §9:107)
- `edge_bar_mc` :: EXPERIMENT=live→CLAIM-0001
- `edge_screen` :: EXPERIMENT=legacy→ARCHIVE
- `edge_screen2` :: EXPERIMENT=legacy→ARCHIVE
- `eng11_rg14_oc` :: EXPERIMENT=reproduce-only(pin RG14 paired-W OC · card AD-4 §4 RG14 · synthetic toy-moment MC)
- `eng11_sigma` :: EXPERIMENT=reproduce-only(SUPERSEDED READING · 810-row ramp ×1.08-1.14 ⟪RETIRED⟫ รอบ 11 · เก็บเพื่อ reproduce เลขที่ถอนใน changelog เท่านั้น · operative = r13_sigma)
- `eng16_ks` :: EXPERIMENT=reproduce-only(pin KS⁺ t=0.0575 · card AD-4 §0 N2 · discrete-Uniform MC B=200k)
- `entry_features` :: EXPERIMENT=legacy→ARCHIVE
- `entry_platform` :: ASSET(imported 8) :: EXPERIMENT=legacy→ARCHIVE
- `es1_card` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0017
- `es2_card` :: EXPERIMENT=live→CLAIM-0018
- `es2_tick_dc_features` :: EXPERIMENT=live→CLAIM-0018
- `exhaustion_fade` :: EXPERIMENT=live→CLAIM-0003
- `fade_dataset` :: EXPERIMENT=live→CLAIM-0003
- `gate1_mi_ceiling` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0007
- `gate2_population` :: EXPERIMENT=live→CLAIM-0007
- `gate_c_wf` :: ASSET(imported 5) :: EXPERIMENT=live→CLAIM-0007
- `gate_magnitude_oos` :: EXPERIMENT=live→CLAIM-0007
- `gate_spread_mi` :: EXPERIMENT=live→CLAIM-0008
- `grid_sim` :: ASSET(imported 3)
- `h0_card1_rv` :: EXPERIMENT=legacy→ARCHIVE
- `h0_card2_trend` :: EXPERIMENT=legacy→ARCHIVE
- `h0_card35_batch` :: EXPERIMENT=legacy→ARCHIVE
- `h0_card6_tick` :: EXPERIMENT=legacy→ARCHIVE
- `h0_card_c10_ms` :: EXPERIMENT=legacy→ARCHIVE
- `h0_card_c6_poke` :: EXPERIMENT=legacy→ARCHIVE
- `h0_card_c9_dc` :: EXPERIMENT=legacy→ARCHIVE
- `h0_cardkit` :: ASSET(imported 6) :: EXPERIMENT=reproduce-only(h0-dataset kit · carried +532.8)
- `h0_features` :: EXPERIMENT=reproduce-only(h0-dataset builder · carried +532.8)
- `h0_join_pnl` :: EXPERIMENT=reproduce-only(h0 PnL-join · carried)
- `holdout_exness` :: EXPERIMENT=reproduce-only(v4 holdout +511.8 clock-corrected)
- `host19_accept` :: EXPERIMENT=self-test(จัดสถานะ run regress/RG14 บน .19 ตามตาราง state Progress Log 2026-10-20 · `--selftest` positive control + mutation ต่อ predicate · เจ้าของ verdict ของ series + report 22-world · classifier/judge = host19_state (2026-10-21) · ไม่ใช่ gate วิจัย)
- `host19_preflight` :: EXPERIMENT=self-test(ตัวตน input/env สำหรับ .19 · manifest จาก git blob ของ treeish + tar · reference จาก header_fields() · assert venue ที่วัดได้ · `venue --out` · Progress Log 2026-10-20/21)
- `host19_run` :: EXPERIMENT=self-test(supervisor ทางเข้าเดียวของ preflight/regress/RG14 บน .19 · แทน `host19_run.sh` a47b192c (superseded · ไม่อยู่ใน manifest) · smoke2 บน .19 = gate · Progress Log 2026-10-21)
- `host19_state` :: ASSET(imported 3)
- `ks_oc` :: EXPERIMENT=reproduce-only(SUPERSEDED READING · KS⁺ threshold table float-convention 4.86% · authority = eng16_ks (integer-lattice + OC) · F-A8 รอบ 22)
- `layer0_meanrev_pregate` :: EXPERIMENT=legacy→ARCHIVE
- `layer1_null_test` :: EXPERIMENT=legacy→ARCHIVE
- `layer2_real_data` :: EXPERIMENT=legacy→ARCHIVE
- `layer2b_bar_null` :: EXPERIMENT=legacy→ARCHIVE
- `ledger_check` :: EXPERIMENT=self-test(traceability tooling · --self-test fixtures+golden)
- `magnitude_at_trigger` :: EXPERIMENT=live→CLAIM-0014
- `mr_sim` :: EXPERIMENT=legacy→ARCHIVE
- `mut_battery` :: EXPERIMENT=self-test(mutation battery ของ card_scan · tempdir mirror · exit 1 ถ้า MISSED)
- `opportunity_unit` :: EXPERIMENT=live→CLAIM-0001
- `opportunity_unit_v2` :: EXPERIMENT=superseded→CLAIM-0002
- `opportunity_unit_v3` :: ASSET(imported 1) :: EXPERIMENT=superseded→CLAIM-0002
- `opportunity_unit_v4` :: ASSET(imported 6) :: EXPERIMENT=live→CLAIM-0002
- `opportunity_validation` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0013
- `pin_ad4` :: EXPERIMENT=self-test(seal/check ของ pin block ad4_card.py · card AD-4 §7(11)(12)(12b) · commit spec · F2 รอบ 24)
- `r13_sigma` :: EXPERIMENT=reproduce-only(σ-generator readout sd(log σ)/ramp-share · card AD-4 §7(5) · synthetic)
- `stage0_join` :: ASSET(imported 2) :: EXPERIMENT=reproduce-only(stage0-join · carried h0)
- `stage0_verify_import` :: EXPERIMENT=legacy→ARCHIVE
- `stageb_pipeline` :: EXPERIMENT=legacy→ARCHIVE
- `test_b_direction_decomp` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0009
- `tp1_card` :: ASSET(imported 7) :: EXPERIMENT=superseded→CLAIM-0015
- `tp1_tick_features` :: ASSET(imported 1) :: EXPERIMENT=superseded→CLAIM-0015
- `tp2_inference` :: ASSET(imported 2) :: EXPERIMENT=live→CLAIM-0016
- `walk_forward` :: EXPERIMENT=reproduce-only(v4 anchored-WF +876)

## CLAIMS

### CLAIM-0001
- **observed:** measurement foundation `edge_bar_mc.py` (ruin/edge-bar system-of-record · 3-metric: Orient $1.25 / **Stress ~5.6-7× v4** / Decision=eval_ruin) · `opportunity_unit.py` Oracle set: v4-blind lift **−2.2pp captured 47%**
- **supported:** ใต้ account-scale risk-unit + $100 ruin-target — **edge ต้องแรง ~7× v4 ให้ $100 รอด**
- **not-yet-supported:** ว่ามี construction ใดถึง ~7× ได้จริง
- **evidence-level:** L1
- **dependencies:** brain_v1_run walker · eval_ruin · account-scale risk-unit
- **invalidated-by:** ruin-model ผิด · risk-unit redefinition (เคยพลิก 4 ครั้ง §9:106)
- **kind:** experiment
- **status:** terminal
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[none] · seed-robust[NA] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 1 รอบ · Claude over-claim 2 headline (3.5×/35%) → แก้เป็น ~7×/47%
- **scope-of-death:** NA (positive-measurement)
- **reproduce:** python Scripts/edge_bar_mc.py ; python Scripts/opportunity_unit.py

### CLAIM-0002
- **observed:** Opportunity-Unit v4 FROZEN protocol (`opportunity_unit_v4.py` estimand-first) · L1: opportunity real **B(1R)=59%** · discovery ทิศถูก residual **~1.6R** ผิด 0.18R · **DIRECTION=คอขวด** ยืนยัน · naive-trigger floor **DirAcc 52.7%** (>coin CI-sig ที่ τ≥1.5)
- **supported:** ใต้ estimand ที่ freeze (PROTOCOL freeze ไม่ freeze RESULT) + H×stop sensitivity robust
- **not-yet-supported:** learned predictor ชนะ floor 52.7% (= CLAIM-0005/0010)
- **evidence-level:** L1
- **dependencies:** opportunity_unit_v4 estimand · brain_v1_run · day-clustered CI · circular-shift+dir-randomize null
- **invalidated-by:** estimand redefinition · trigger state-vs-event flip (เคยทำ DirAcc 62%↔85%)
- **kind:** experiment
- **status:** terminal (v2/v3 superseded-by-CLAIM-0002)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[permutation] · seed-robust[NA] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 6 รอบ · ข้อสรุปพลิก 4 ครั้งเพราะ measurement-definition (conditioning/risk-unit/state-event/outcome-cond)
- **scope-of-death:** NA
- **reproduce:** python Scripts/opportunity_unit_v4.py

### CLAIM-0003
- **observed:** fade ตายทั้ง 2 construction บน v4-entry — mirror **WR 12%** · exhaustion-fade **−0.6/ไม้ WR40%** robust (20+ DoF · 9/9 ปี · 2R ไม่พลิก)
- **supported:** ใต้ v4 entry distribution — "behavior-space ไม่มี additive headroom" = ยืน pooled-ceiling
- **not-yet-supported:** "fade ตายทั้งแนว" (scope = overshoot-of-level ≠ exhaustion proxy บน OHLCV)
- **evidence-level:** L1
- **dependencies:** fade_dataset · v4-entry population · brain_v1_run exit
- **invalidated-by:** exhaustion proxy อื่น (order-flow) · entry population ที่ไม่ใช่ v4
- **kind:** experiment
- **status:** FALSIFIED
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[mirror] · seed-robust[NA] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 1 รอบ · Claude แก้ too-clean bug
- **scope-of-death:** overshoot-of-level fade บน OHLCV ใต้ v4-entry (ไม่ใช่ fade ทั้งแนว · ไม่ใช่ order-flow exhaustion)
- **reproduce:** python Scripts/exhaustion_fade.py

### CLAIM-0004
- **observed:** Discovery NOT falsified — missed ∧ oracle-opportunity **+1.745 (n=31 WR54.8%)** (conditioning-error fix จาก −2.88 · ไม่ใช่ sign-flip) · decomposition: dir ตรง **+17.98/WR100%** ผิด **−13.48/WR12%** · **[07-10 validation `opportunity_validation.py` · pre-registered]** 3-population decomposition บนวัน v4-missed (826 วัน): **(a) anchor outcome-blind ลบทุก config** (both/W60 −1.482 n=759 · ช่วง −0.30..−2.75) · **(b) realizable = 0/7 trigger-config PASS** (FWE Bonferroni m=7 จ่ายเต็ม · ไม่มี config ถึง CI95-low>0) · **(c) ceiling oracle-conditioned ยืน** (pd +1.555 n=30 ≈ เดิม +1.745 · don/W120 +4.064 · both/W60 +3.662 · n~30-32 = full population ของวัน missed∧opp ทั้ง field)
- **supported:** additive opportunity **มีจริงในฐานะ oracle-CEILING เท่านั้น** (~+1.5..+4/ไม้ บน ~30 วัน/9 ปี) · **ไม่ realizable ด้วย ex-ante trigger-grid 7 config** (don/pd/both × W · FWE-paid) · base-rate วัน missed = ลบ · ยืนยัน PnL = Opportunity × DIRECTION: กุญแจ = discovery/direction ex-ante ไม่ใช่ trigger เพิ่ม
- **not-yet-supported:** realizable ด้วย mechanism นอก grid นี้ (representation/data ใหม่) · "Discovery ตายทั้งแนว" (scope = trigger-grid Momentum บน OHLC)
- **evidence-level:** L0 (validation รันแล้ว · promotion รอ Engineer adversarial round)
- **dependencies:** oracle=labeling-instrument (ไม่ใช่ target) · opportunity_unit_v4 (Q3 trigger frozen estimand) · discovery_probe · brain_v1_run
- **invalidated-by:** ex-ante rule ใดพิสูจน์ realizable CI-separated บน missed population · oracle-guardrail ละเมิด (hindsight-leak)
- **kind:** experiment
- **status:** live
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[circular-shift พร้อม · ไม่ถึงคิว (0/7 ตกก่อน) + boot-CI] · seed-robust[N single-seed 20260710] · leak-guard[Y ex-ante trigger · Engineer verified no-leak + exit-mirror exact] · verified-by[Engineer]
- **correction-lineage:** corrections 1 รอบ · Engineer จับ Claude วัดผิด population (all-missed 94% chop) เกือบสรุป ceiling→StageF · 07-10 validation: design ผ่าน Engineer 2 รอบ (D1-D6+A-1 FWE) ก่อนรัน · execution-review 07-11 Engineer PASS (Q-A ยืนทุกแกน)
- **scope-of-death:** realizable-additive ด้วย trigger-grid don/pd/both × W{30,60,120} บน SEARCH (ไม่ใช่ ceiling · ไม่ใช่ mechanism อื่น)
- **reproduce:** python Scripts/opportunity_validation.py ; python Scripts/discovery_probe.py

### CLAIM-0005
- **observed:** Direction Predictor v0 honest NEGATIVE — OOS **−0.093R** ≈ follow-trigger −0.094 ≈ perm-null −0.095 · features lift **+0.006R (~0 UNDERFIT)** · oracle-if-dir-known **+0.775R** · payoff-dir SIGN-FLIP train −0.125→OOS +0.018
- **supported:** ใต้ **linear/univariate OHLCV + 1R/1.5R exit** — ไม่มี OOS cost-clearing directional edge · fit ไม่ได้แม้ in-sample
- **not-yet-supported:** "ทำนายทิศไม่ได้" ทั่วไป (info-theory ceiling ยังไม่พิสูจน์ · nonlinear/representation/adaptive ยังไม่เทส) · "non-stationarity = root cause" (over-claim ที่ downgrade แล้ว)
- **evidence-level:** L1
- **dependencies:** direction_predictor objective=E[signed-R] · feature as-of ≤ bar · train12-17/OOS18-20 · label=trade_R
- **invalidated-by:** nonlinear/tick-representation ให้ OOS edge · exit-policy อื่น
- **kind:** experiment
- **status:** superseded→CLAIM-0010 (label trade_R ≠ real exit · re-measured)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[permutation] · seed-robust[N] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 1 รอบ · downgrade over-claim (bottleneck/non-stationary-root/GBM/0-19-dead → DIAGNOSTIC ไม่ใช่ verdict · §9:119)
- **scope-of-death:** linear/univariate OHLCV representation + intraday 1R/1.5R exit (ไม่ใช่ทุก representation/exit)
- **reproduce:** python Scripts/direction_predictor.py

### CLAIM-0006
- **observed:** Direction Predictor v1 (sign-stability gate + family-expand) — INCONCLUSIVE · **holdout-leak `direction_predictor_v1.py:122`** (เลือก stable feature จาก OOS corr แล้ว eval บน OOS เดียวกัน) · exit=`trade_R` ไม่ใช่ real-walk
- **supported:** ไม่มี claim ยืน (leaky · superseded)
- **not-yet-supported:** ผล v1 ใดๆ (leak ทำให้ optimistic)
- **evidence-level:** L0
- **dependencies:** direction_predictor_v1 build (infra ให้ 4 gate) · fit_signedR · sign-stability gate
- **invalidated-by:** leak fix แล้วผลเปลี่ยน (คาด) · real-exit label (CLAIM-0010)
- **kind:** experiment
- **status:** superseded→CLAIM-0010
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[permutation] · seed-robust[N] · leak-guard[N] · verified-by[self]
- **correction-lineage:** corrections 0 รอบ · flagged leak `v1:122` ยังไม่ fix (superseded ก่อนถึงคิว)
- **scope-of-death:** v1 sign-stability approach บน intraday trade_R (leaky · ไม่นับเป็นหลักฐาน)
- **reproduce:** python Scripts/direction_predictor_v1.py

### CLAIM-0007
- **observed:** in-hand direction-channel LEARNED features ไม่เพิ่ม OOS direction skill ใต้ label `trade_R` — OHLC sign-MI **1/19** · tickvol **0/7** · Gate-A linear domain-classifier AUC **0.547** · magnitude predictable **+0.66** (label-agnostic) **[⚠ DEMOTED 07-12: '+0.66' ไม่มี artifact ต้นทาง — รันครบ 4 source (gate1/gate_magnitude/gate_c/gate2 · script unchanged ตั้งแต่ 13cefaf + deterministic): ค่าจริง = in-sample MAGNITUDE-MI 6/19 FWE-sig (DIAGNOSTIC/overfit-floor · de-cluster [5,1,6]/19) · OOS straddle-net-cost ตาย (ทุก bucket ลบ CI-excl-0 · Spearman +0.0253)]** · MDE CI-half **~0.043R** vs ruin-safe **0.37-0.46R**
- **supported:** ใต้ intraday 1R/1.5R `trade_R` label + tested representation — learned features ไม่ add · Gate-A ลด static-model prior (**ไม่ eliminate**)
- **not-yet-supported:** "direction ตายทุก channel" (label ผิด → CLAIM-0009) · "static-GBM ไม่ transfer" (linear เท่านั้น) · tick-price (ยังไม่เทส)
- **evidence-level:** L1
- **dependencies:** gate1/gate2/gate_c/gate_magnitude · direction_predictor_v1 build · label=trade_R intraday
- **invalidated-by:** re-measure ที่ real exit (เกิดแล้ว CLAIM-0009/0010) · tick-price representation ให้ MI
- **kind:** experiment
- **status:** superseded→CLAIM-0009 (label re-measured at real exit)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[permutation] · seed-robust[N] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 2 รอบ · Engineer catch (พลาดร่วม ~16 รอบ): วัดบน trade_R ≠ real EA exit · 07-12: demote "+0.66" (no-artifact transcription จาก session 07-08 — Claude รันครบ 4 source + Engineer verify อิสระ เลขตรงกัน · แทนด้วยค่าจริง script-owned ใน observed annotation)
- **scope-of-death:** learned OHLC/tickvol features ใต้ intraday 1R/1.5R trade_R label (ไม่ใช่ real-exit · ไม่ใช่ tick-price)
- **reproduce:** python Scripts/gate1_mi_ceiling.py ; python Scripts/gate_magnitude_oos.py

### CLAIM-0008
- **observed:** spread channel DEAD — de-cluster **[0,0,0]** · OOS **+0.004R** CI คร่อม 0
- **supported:** ใต้ label trade_R + spread-as-feature — ไม่มี directional signal
- **not-yet-supported:** spread ใต้ real-exit label (ไม่ได้ re-measure · low-priority · dead ทั้ง de-cluster)
- **evidence-level:** L1
- **dependencies:** gate_spread_mi · direction_predictor build · spread channel
- **invalidated-by:** spread ที่ real-exit ให้ signal (ไม่คาด · de-cluster ตายสนิท)
- **kind:** experiment
- **status:** DEAD-do-not-rerun
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[day-block] · seed-robust[N] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 0 รอบ · committed 69fe5c1
- **scope-of-death:** spread-as-direction-feature ใต้ trade_R (de-cluster + OOS ตายทั้งคู่)
- **reproduce:** python Scripts/gate_spread_mi.py

### CLAIM-0009
- **observed:** Test B 3-leg decomposition (floor/current/ceiling บน v4-entries · import walk() ตรง) = **direction load-bearing ที่ real EA exit** · mirror-symmetry property-test ผ่าน · field 2012-2020 SEARCH +532.8
- **supported:** direction มี skill ที่ exit จริงของ engine (trailing 1×R + overnight) — "direction ตาย" ของ gates = artifact ของ label trade_R ผิด
- **not-yet-supported:** ว่า LEARNED features จับ skill นั้นได้ (= CLAIM-0010) · magnitude vs direction attribution เต็ม
- **evidence-level:** L1
- **dependencies:** test_b_direction_decomp · brain_v1_run walk() canonical exit · day-clustered CI
- **invalidated-by:** walk() exit ไม่ใช่ canonical · mirror-symmetry แตก
- **kind:** experiment
- **status:** terminal
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[mirror] · seed-robust[NA] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 5 รอบ (Engineer design review · lookahead/glossary) · commit 7bf95b7
- **scope-of-death:** NA (positive · load-bearing established)
- **reproduce:** python Scripts/test_b_direction_decomp.py

### CLAIM-0010
- **observed:** direction-at-real-exit TERMINAL (seed-robust · deterministic) — v4 breakout-dir base−floor **+0.582$/ไม้ · lower-bound>0 ทุก 9 seed (min +0.133)** · 19-feat learned (linear+GBM-fair) aggregate **<0 ทุก seed (−0.39..−0.02) · ไม่มี seed CI-excl-0-positive** · oracle **+4.98** headroom **+4.6**
- **supported:** (a) **v4 breakout-direction = edge จริง CI-backed** ที่ real exit (b) **19 OHLC features ไม่มีหลักฐาน additive direction signal** ที่ real exit (seed-robust linear+GBM)
- **not-yet-supported:** **ceiling ยังไม่วัด** (direction ยังไม่ solved · headroom +4.6 เหลือ) · **ไม่ใช่ "proven-zero"** (inconclusive-to-null ไม่ใช่ harmful) · gate descriptors (abstain 17-66%) seed-fragile ไม่ freeze
- **evidence-level:** L1
- **dependencies:** direction_at_real_exit · dir_features · brain_v1_run canonical exit · per-fold train-only sign-gate · WF+embargo · per-call-site crc32-seeded rng · GBM sweep
- **invalidated-by:** richer representation/tick-price ให้ additive CI-positive · ceiling measurement > current
- **kind:** experiment
- **status:** terminal
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[permutation] · seed-robust[Y] · leak-guard[Y] · verified-by[adversarial]
- **correction-lineage:** corrections 6 รอบ (Engineer · Claude verified ทุกครั้ง) · a26a93e fallback-artifact · b42278f perm-null+stump · 9e846b4 N=1+circular-ceiling · 8f6b8e6 baseline-no-CI · rng-defect→crc32 · single-draw→multi-seed · meta-pattern: ลบ affirmative→ใส่นุ่มแทน · frozen f31fd60 · 07-10 no-behavior-change lint (unused import FEATS + dead unpack→`_` · Engineer verified 0 refs/ตัวเลขไม่เปลี่ยน — ไม่ใช่ correction ของผล)
- **scope-of-death:** 19-feat OHLC (linear+GBM) additive-direction ที่ real exit บน SEARCH 2012-2020 (ไม่ใช่ ceiling · ไม่ใช่ tick-price · ไม่ใช่ proven-zero)
- **reproduce:** python Scripts/direction_at_real_exit.py

### CLAIM-0011
- **observed:** Research Traceability System — `ledger_check.py` (validate + --emit-index · ast import-scan robust · check-list = docstring SSOT · **+(k) imported-N == disk 2026-09-08 [AD-4 F4 รอบ 15 · วินมอบ technical] · self-test count = `--self-test` output (ห้าม pin เลข · F-A5 รอบ 22)**) · self-test + golden ALL PASS (count = --self-test output) · LEDGER/ARCHIVE/STATUS-trim/DoD
- **supported:** ปิด owner-problem 4 ข้อ (experiment-visibility/lineage/result-single-SoR/owner-audit) ด้วย mechanical enforcement 2 axis (ASSET import-scan · EXPERIMENT __main__)
- **not-yet-supported:** disposition correctness (validator existence-only · semantic mis-tag ต้อง human-review) — residual limit
- **evidence-level:** L1
- **dependencies:** ledger_check --self-test · ast · Plan/TRELLIS-010_LEDGER.md
- **invalidated-by:** scan-logic common-mode bug (golden-fixture pin) · new exotic import/main syntax
- **kind:** experiment
- **status:** live
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[none] · seed-robust[NA] · leak-guard[NA] · verified-by[Engineer]
- **correction-lineage:** corrections 12 รอบ (v1→v-final-6 · DEFECT-8/9/10 + BLOCKER · Engineer FAIL 10 → PASS · closure 07-10: F1 substring→startswith + check(i) arrow-target + F2 count-derive + fixture(ix) regression-guard — Engineer PASS-with-changes · 07-10b: check(j) status-token invariant + leading_token single-parser refactor (h)/(i) — Engineer PASS-with-changes CRITICAL-1 .get + MAJOR-1 good_claim) · Claude verify import-scan 3-way agree
- **scope-of-death:** NA (tooling · existence-check ไม่ตัดสิน semantics = known limit)
- **reproduce:** python Scripts/ledger_check.py --self-test

### CLAIM-0012
- **observed:** v4 "Dual Asian-Range Breakout" carried candidate — canonical `dual_asian_sim.py` · anchored-WF OOS 2015-26 **+$785.6 PF1.11** → weekend-HALT fix **+$876 P(≤0)7.6%** · holdout Exness EU-corrected **+$511.8 PF1.54 maxDD320**
- **supported:** candidate มีหลักฐานเบื้องต้น + ระบบทดสอบครบ (mirror-no-new-param · 15.5y)
- **not-yet-supported:** **"proven edge"** — Engineer NO-GO · bootstrap CI95 กว้าง · กำไรกระจุก 2023-26 · dual ไม่มี OOS เหลือ · real-tick CONFIRM ยังไม่ผ่าน (~~clock-fix รอ Gate 0~~ → แก้ 09-03: Gate 0 ปิดแล้ว 07-04 clock ปิดเด็ดขาด [Progress Log 07-04 · Engineer PASS-conditional] · ที่ยังไม่ผ่าน = proven-edge bar เอง: 2026 real-tick n=11 ติดลบ explained cost-residual C2 · ยังไม่มี demo/forward)
- **evidence-level:** L2
- **dependencies:** dual_asian_sim canonical · walk_forward · holdout_exness · clock EU-DST
- **invalidated-by:** real-tick tester ติดลบ · holdout เดือนใดพลิก · WF selection ไม่เสถียร
- **kind:** experiment
- **status:** live (candidate · carried-forward)
- **fairness:** field-tag[SIM-SEARCH,holdout] · pipeline-owned[Y] · null-control[none] · seed-robust[NA] · leak-guard[Y] · verified-by[Engineer]
- **correction-lineage:** corrections 1 รอบ · holdout +802 (US-rule ผิด) → +511.8 (EU ground-truth) · ห้ามเลือกกฎจาก P&L
- **scope-of-death:** NA (candidate ยังไม่ falsified · ยังไม่ proven)
- **reproduce:** python Scripts/dual_asian_sim.py

### CLAIM-0013
- **observed:** magnitude rank บน realizable population (both/W60 trades วัน v4-missed · **proxy = day-mean GBM-straddle forecast เฉลี่ยบน v1-events** · TEST_YEARS 2015-20 · n=512): **Spearman(pred, |pnl|) = −0.012 CI[−0.088,+0.086]** · top-half−bottom-half (signed pnl) **−0.629 CI[−2.720,+1.311]**
- **supported:** **ตรวจไม่พบ** ranking ใต้ proxy ทื่อ 3 ชั้น (day-mean · cross-event กับ trigger จริง · TEST_YEARS-only) — **ไม่พอสรุปว่า magnitude ไม่ transfer** (not-detected ≠ falsified · power problem ไม่ใช่ signal absence — Engineer execution-review)
- **not-yet-supported:** **event-specific/at-trigger magnitude forecast** — ผ่าน v1 intraday-features = **structurally blocked** (CLAIM-0014 · trades ตัดสิน session-open) · ต้อง session-open features ถ้าจะเทส · "magnitude ตายทั้งแนว" · in-population เดิมของ CLAIM-0007 ไม่ถูกแตะ · exit/representation อื่นยังไม่เทส
- **evidence-level:** L0
- **dependencies:** opportunity_validation · direction_predictor_v1 build · gate_c_wf gbm/TEST_YEARS · population (b) ของ CLAIM-0004 validation
- **invalidated-by:** at-trigger magnitude forecast rank ได้ CI-separated (จะ supersede not-detected นี้) · join-coverage bias พิสูจน์ได้
- **kind:** experiment
- **status:** live
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y] · null-control[bootstrap-CI เท่านั้น] · seed-robust[N] · leak-guard[Y expanding-WF] · verified-by[Engineer]
- **correction-lineage:** corrections 1 รอบ · design ผ่าน Engineer 2 รอบก่อนรัน (INT-2) · execution-review 07-11: Engineer downgrade "FAIL/ไม่ transfer" → "not-detected-under-blunt-proxy" (Claude over-claim · แก้แล้ว)
- **scope-of-death:** NA (not-detected · ไม่ใช่ falsification — ดู supported)
- **reproduce:** python Scripts/opportunity_validation.py

### CLAIM-0014
- **observed:** at-trigger magnitude บน realizable population = **โครงสร้างเทสไม่ได้ด้วย v1 features**: trades 759 → i≥240 eligible **1** (dropped 758 · hour-dist {1:87, 2:597, 3:65, 4:5, ...}) → join ∧ TEST_YEARS = **0** · fail-loud STOP ตาม pre-registration · discriminator: trade เดียวที่ k≥240 **join พบจริง** (2014-05-23/276 → True) = join-key ถูก ไม่ใช่ bug · k median=72 max=276
- **supported:** first-event ของ both/W60 บนวัน missed = **ตัดสินตอนเปิด session/ข้ามคืน** (ชม.1-3 = 749/758) ↔ v1 features ต้องการประวัติ 240 session-bars → **disjoint 98.7% เชิงโครงสร้าง** · CLAIM-0013 วัดได้เพราะ day-mean เฉลี่ยบน bars (i≥240) ที่ disjoint กับ trade bars — ไม่ใช่แค่ diluted
- **not-yet-supported:** at-trigger magnitude ด้วย **session-open features** (prior-day/overnight/first-N-bars · ไม่พึ่งประวัติ 4 ชม.) — ยังออกแบบ/เทสได้ถ้าคุ้ม (prior หลัง demote +0.66 = บางมาก · priority ต่ำ)
- **evidence-level:** L1 (discriminator reproduce อิสระ 2 ฝ่าย: Engineer + Claude เลขตรงกันทุกตัว)
- **dependencies:** magnitude_at_trigger · opportunity_validation population · direction_predictor_v1 build (meta+i) · gate_c_wf gbm/TEST_YEARS
- **invalidated-by:** session-open feature set ทำ at-trigger test ได้จริง (จะ supersede "untestable")
- **kind:** experiment
- **status:** terminal (structural-wall · ไม่ใช่ผลวัด — การวัดทำไม่ได้ใน config นี้)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y fail-loud guard] · null-control[NA ไม่ถึงการวัด] · seed-robust[NA] · leak-guard[Y] · verified-by[Engineer+Claude discriminator ตรงกัน]
- **correction-lineage:** corrections 0 รอบ · design ผ่าน Engineer 3 รอบก่อนรัน (TRAP-1/2/5 · MISS-1/2 · SEED-1) · wall review: Engineer แยกสมมติฐาน structural-vs-join-bug ด้วย evidence
- **scope-of-death:** at-trigger magnitude **เฉพาะผ่าน v1 intraday-history features** บน first-event population นี้ (ไม่ใช่ session-open features · ไม่ใช่ population อื่น)
- **reproduce:** python Scripts/magnitude_at_trigger.py

### CLAIM-0015
- **observed:** Card TP-1 tick-price nested-incremental ที่ real exit (n=1486 · 6 bid tick features event-time N=3000 · baseline 24 = 19-FEATS + 4 M1-shadows + log_winsec · pre-registered ก่อนรัน) — **LINEAR GATED (primary): agg [−0.7303, +0.0821]$/ไม้ · CI-lower [−1.2278, −0.1358] · 0/9 seed CI-positive** · **perm-null B=1000 (รันจริง): observed −0.2352 · p=0.8052** (null mean −0.1172 · p95 +0.0761) · **FORCED-IN (gate-bypass tick): agg [−0.5480, +0.4190] · 1/9 seed CI-lower>0 (+0.0280 — ⚠ single-seed บางเฉียบเหนือ 0 · verdict INCONCLUSIVE ยืนบนเส้นนี้ตาม asymmetric rule ที่ pre-register)** · **GBM nested (A/B same-hyperparams): agg point บวกทุก seed [+0.0069, +0.1916] แต่ 0/9 CI-positive [⚠ ANNOTATED 07-14 (Engineer required-edit · TP-2 calibration): H0 แท้ผลิต pattern point-positive นี้เองผ่าน null-mean elevation (TP-2 run วัดจริง +0.093/+0.104 · calib-demo ≈+0.12) — "GBM 9/9 บวก" = mechanical ไม่ใช่ weak-signal · หลักฐาน = CLAIM-0016]** · gates: G1-SOFT reconstruction 100.0000% ทุกปี (~3.15M bars · bad=0 · buildlog artifact) · G1-HARD PASS · G3 future-mask+shadow-sentinel 54 entries (power พิสูจน์ด้วย negative-control 2 planted bugs ยิงจริง) · NaN-drop 0 · tickfeat SHA 94c8e68cf8ec6649
- **supported:** ใต้ 6 features + nested protocol นี้ — **ไม่พบ additive tick-price signal ผ่าน gated pipeline** (0/9 + perm-p 0.81) · verdict ตาม pre-registered asymmetric rule = **INCONCLUSIVE (gate-limited)** — forced-in มี 1/9 seed CI-positive → **ห้ามเรียก KILL / ห้าม eliminate frontier** (univariate sign-gate อาจกด conditional signal — เงื่อนไขที่ประกาศก่อนรัน)
- **not-yet-supported:** "tick-price มี additive signal" (ไม่มีหลักฐาน CI-backed) · "tick-price ตาย" (gate-limited + GBM point-positive ทุก seed แต่ไม่ CI) · features/window/gate form อื่น · **prediction-score:** ทำนาย clean-null → ได้ INCONCLUSIVE — sub-outcome เป็น fact: aggregate −0.2352 ∈ [−0.30,+0.10] ✓ · gated 0/9 ✓ · perm>0.05 ✓ · GBM ทาย ≤0 ✗ (point บวกทุก seed) · **2/4 metric เบนเข้า weak-signal (GBM 9/9 point-positive + forced-in 1/9)** — ไม่นับเป็น "ถูก 3/4" (Engineer M-4: เกณฑ์ผิดที่ pre-register โดน forced-in ชนตามตัวอักษร)
- **evidence-level:** L1 (Engineer execution-review 07-14: reproduce ทุก inferential number + feature spot-check โค้ดอิสระ — precedent CLAIM-0014)
- **dependencies:** tp1_tick_features (frozen SHA) · tp1_card (fit_predict+return_w [AD-4 ขั้น 2 · backward-compatible kwarg · ไม่ retro-touch verdict]) · direction_at_real_exit (build_rows/sign_gate/protocol) · brain_v1_run walker · dir_features · ticks eet 2012-2020
- **invalidated-by:** gate form ที่เห็น conditional signal (multivariate/nested-gate) ให้ผลชัดทางใดทางหนึ่ง · feature set richer · execution-review พบ defect
- **kind:** experiment
- **status:** superseded→CLAIM-0016 (inference-completed · facts carried — ไม่ใช่ re-measured)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y verdict จาก script] · null-control[permutation B=1000 pipeline-run · review-verify = code-audit + B=40 sanity (p 0.854 สอดคล้อง 0.805) ไม่ใช่ full re-run — ประกาศตรง] · seed-robust[Y 9-seed ทั้ง 3 branch] · leak-guard[Y G1 HARD/SOFT(assert≥99.9) + G3 future-mask+shadow-sentinel + negative-control พิสูจน์ guard power + strict boundary t(j)+60s] · verified-by[Engineer execution-review + apply-plan review 07-14]
- **correction-lineage:** corrections 2 รอบ · design ผ่าน Engineer 3 รอบก่อนรัน (R1 B1-B3/M1-M6 · R2 P1-P6 · R3 Issue1-6 — spec v2 ใน docstring tp1_card) · Claude จับ Engineer ผิด 1 (M4b Exness ticks ไม่มีจริง) · Engineer จับ Claude 2 (corr-gate → nested · perm ไม่เคยรันใน template) · G1-HARD checker bug (partial-first-minute 1,467) จับโดย fail-loud เอง แก้ก่อนมี output · **รอบ 2 (07-14 execution-review M-1..M-4 + apply-plan F-1..F-5):** integrity hardening (buildlog artifact + SOFT assert + shadow-sentinel non-mutating + negative-control) — no-behavior-change พิสูจน์ด้วย CSV SHA เท่าเดิม · prediction-score แก้จาก "3/4" เป็น framing ตรง (M-4)
- **scope-of-death:** NA ในตัว claim นี้ (INCONCLUSIVE ถูก supersede — elimination verdict อยู่ CLAIM-0016)
- **reproduce:** python Scripts/tp1_tick_features.py ; python Scripts/tp1_card.py

### CLAIM-0016
- **observed:** TP-2 inference completion (pre-registered spec v2 · Engineer 3 รอบ · `tp2_inference.py`) — **observed script-owned: S1 GBM-median9 = +0.1215** (per-seed ตรง provisional ทุกตัว — ไม่มี threading deviation) · **S2 forced-median9 = −0.0742** · **p(S1 · primary C-a GBM-projection residual-perm · B=1000) = 0.3976** (null mean **+0.0929**) · p(S1 · OLS residual-perm cross-check) = 0.4496 (null mean +0.1039) · **p(S2 · OLS residual-perm) = 0.0629** (null mean −0.2758 · observed สูงกว่า null +0.20 แต่ไม่ถึง α) · α=0.0167 (Bonferroni m=3: {S1, S2, GATED-linear p 0.8052 จาก TP-1}) · ไม่ trigger B-escalation · **calibration ก่อนรัน (20 H0-true draws · reproduce ได้ `tp2_inference.py calib`): NullA-OLS 1/20@0.05 median 0.625 · NullB-GBMproj 1/20@0.05 median 0.505 — both calibrate · C-a = theoretical model-match hedge** · ⭐ **null-mean elevation = mechanical property ของ nested-lift statistic (run นี้วัดจริง +0.093/+0.104 · calibration-demo context ≈+0.12 — แยกสนามวัดตาม Engineer MINOR-2)**
- **supported:** **KILL ตาม pre-registration** — ไม่มี statistic ถึง α ใต้ null ที่ calibration-checked → frontier tick-price **eliminated ใน scope ที่เทส** · **"GBM point-positive 9/9" ของ CLAIM-0015 = mechanical null-elevation ไม่ใช่ weak-signal** (observed +0.1215 ≈ null mean +0.093 · p 0.40) · methodology ถาวร: nested-lift point-positivity ≠ signal
- **not-yet-supported:** tick-price representation อื่น (event-stream/multi-scale/richer features — อยู่ frontier แถว nonlinear ที่ยัง open) · population อื่น · **ไม่ใช่ proven-zero** (sensitivity floor ≈ +0.28/ไม้เหนือ null — order-of-magnitude จาก calib draw เดียว ไม่ใช่ power analysis · Engineer MINOR-1) · prediction ผม 2/3: p(S1) ∈ [0.3,0.7] ✓ (0.3976) · ไม่มี p<α ✓ · **p(S2)>0.5 ✗ (จริง 0.0629 — forced-in observed ดีกว่า null ของมัน +0.20 = เลขที่ signal-like สุดของทั้ง arm แต่ไม่ถึง α · บันทึกตรงไม่ฝัง)**
- **evidence-level:** L1 (Engineer execution-review 07-14: observed reproduce bit-exact ทุก seed · nulls B=50 sanity ตรง tail/mean · code-path audit ครบ — บาร์เดียวกับ CLAIM-0014/0015)
- **dependencies:** tp1_card machinery (build_rows/sign_gate/fit_predict/PAY-cache) (return_w [AD-4 ขั้น 2 · backward-compatible kwarg · ไม่ retro-touch verdict]) · tp1_tickfeat frozen SHA 94c8e68c · direction_at_real_exit · brain_v1_run walker · calibration demo in-script
- **invalidated-by:** richer/event-stream representation ให้ผล CI-positive ที่ยัน calibrated-null ได้ · พบ mis-calibration ของ null ภายหลัง (เกิน resolution 20 draws) · execution-review พบ defect
- **kind:** experiment
- **status:** terminal (inference-completed · ปิด INCONCLUSIVE limbo ของ CLAIM-0015)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y observed+p+verdict emit จาก script ทั้งหมด] · null-control[residual-permutation ×3 · B=1000 · calibration-checked 20 H0-true draws · plain-perm ถูกตัด (ไม่เคย calibrate กับ GBM statistic)] · seed-robust[Y statistic = median ข้าม 9 model-seeds] · leak-guard[Y inherits TP-1 gates · perm train-side เท่านั้น · selection-contamination declared (S1 ถูกเลือกหลังเห็น TP-1)] · verified-by[Engineer execution-review 07-14 — reproduce อิสระ (observed bit-exact · null sanity B=50 · p-formula back-check 63/1001) + ยืนยัน no-p-hacking (primary Ca ให้ p ต่ำกว่า = conservative ต่อ KILL · Bonferroni ทิศ conservative)]
- **correction-lineage:** corrections 0 รอบหลังรัน · design 3 รอบก่อนรัน: R1 B1 "plain-perm anti-conservative" → Claude หักล้างทิศด้วย H0-true demo (3/3 draws) · R2 จับ demo Claude circular + cross-fold bug (I-4) + runtime ผิด 10× (จริง 1.62s/eval) + บังคับ calibration · R3 audit demo = FAIR + 5 changes (script-owned observed · ตัด plain-perm · diagnostic line · CLAIM-0015 annotation · C-a=hedge language) · Claude disclose M5: tp1_card ประกาศ GBM-perm แต่ไม่เคยรัน → docstring แก้ + process-check "ทุก pre-registered test ต้อง emit หรือ mark deferred"
- **scope-of-death:** tick-price **6 features (imb/path_eff/srun/mvol/dur_cv/lvl_act · bid-only · event-time N=3000) ผ่าน linear+GBM ที่ real walk-exit บน SEARCH 2012-2020 · MDE ≈ +0.28** — ไม่ใช่ tick-price ทั้งแนว · ไม่ใช่ event-stream · ไม่ใช่ proven-zero
- **reproduce:** python Scripts/tp2_inference.py ; python Scripts/tp2_inference.py calib

### CLAIM-0017
- **observed:** Card ES-1 event-stream DC multi-scale ที่ real exit (pre-registered spec v4 · Engineer 4 รอบ · `es1_card.py` · n=1486 · 8 DC encodings δ∈{0.1,0.25,0.5}×aw บน M1 session closes 01:00→close(j) · baseline 20 = 19-feat + rjR) — **observed script-owned: S1 linear-forced-median9 = −0.1427 · S2 GBM-nested-median9 = −0.1269** · **p(S1 · OLS residual-perm B=1000) = 0.4446** (null mean −0.1603 · null-p95 +0.0665) · **p(S2 · GBM-proj residual-perm B=1000) = 0.4635** (null mean −0.1362 · null-p95 +0.0822) · α=0.025 (m=2) · ไม่ trigger escalation · **calibration ก่อนรัน (15 H0-true draws · reproduce ได้ `es1_card.py calib`): S1 0/15@0.05 median 0.510 · S2 1/15@0.05 median 0.500 — both calibrate** · gates: UNDEF==0 assert ✓ · slice-discipline 54 entries (M2: guard เชิงโครงสร้าง — **no-lookahead power = smoke NEG-CTRL planted span+20 ยิงจริง**) ✓ · R-match ผูก walker ทุกไม้ ✓ · DIAG (descriptive-only): drop-δ0.25 ทำ S1 ดีขึ้น +0.163 (scale กลาง = noise ต่อ linear) · GATED −0.1796 · leave-max-out = **z-profile report เท่านั้น ไม่ recompute** (|z|max 9.46sd · 13 วัน>4sd · ตัด row เปลี่ยน fold-structure — M3)
- **supported:** **KILL ตาม pre-registration** — observed ทั้งสองนั่งบน null-mean ของตัวเองพอดี (S1 −0.143 vs −0.160 · S2 −0.127 vs −0.136) → DC multi-scale บน M1 closes **ไม่ add direction info เหนือ baseline ที่ real exit** · root-cause explanation: dc_align redundant กับ momentum block (linear-R² 0.04-0.19 · GBM-OOF 0.21-0.64) + os/dur/asym ไม่มี information เกิน composition — ไม่ใช่แค่ p≥α · **null-mean ES เป็นลบ (ต่างจาก TP-2 ที่บวก) = elevation เป็น per-feature-set** (methodology ถาวรต่อยอด CLAIM-0016)
- **not-yet-supported:** event-stream form อื่น (tick-DC · event-functional อื่น · richer nonlinear — frontier แถว nonlinear ยัง open เฉพาะ form เหล่านั้น) · "event-stream ตายทั้งแนว" · proven-zero (**sensitivity-floor ≈ +0.07/+0.08 $/ไม้** — not-detected ≠ falsified ตาม CLAIM-0013) · **prediction held: 2-independent + 1-implied** (KILL ✓ · p∈[0.2,0.9] ทั้งคู่ ✓ [0.4446/0.4635] · "ไม่มี p<0.10" = implied โดย band-edge — Engineer M-1: เกณฑ์ nested ห้ามนับ "3/3")
- **evidence-level:** L1 (Engineer execution-review 07-15: observed bit-exact ทุก seed + feature spot-check โค้ดอิสระ deviation 0.00e+00 + dissect mirror exact + null sanity B=50 — precedent CLAIM-0014/0015/0016)
- **dependencies:** es1_card (dissect mirror c9_dc_features:51-82) · tp2_inference machinery (TP2 class/null_run/proj) · tp1_card folds/fit_predict (return_w [AD-4 ขั้น 2 · backward-compatible kwarg · ไม่ retro-touch verdict]) · direction_at_real_exit build_rows · brain_v1_run walker · h0_tickfeat rjR (frozen SHA)
- **invalidated-by:** event-form อื่นให้ผล CI-backed · calibration พบ mis-calibration ภายหลัง · execution-review พบ defect
- **kind:** experiment
- **status:** terminal (KILL scoped · ไม่มี middle branch ตาม pre-registration)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y observed+p+verdict+MDE emit จาก script] · null-control[residual-perm ×2 · B=1000 · calibration-checked 15 draws ทั้งสอง statistic ของ card เอง] · seed-robust[Y median-9] · leak-guard[Y UNDEF-assert + slice-discipline + smoke NEG-CTRL power-proven + R-match] · verified-by[Engineer execution-review 07-15 — reproduce อิสระครบ (observed bit-exact · features 0-deviation · null B=50 sanity · calib audit) ไม่พบ result-affecting defect]
- **correction-lineage:** corrections 2 รอบ (1: drop-one diag mask-width crash — แก้หลัง observed ออกแล้ว ไม่ปนเปื้อน · + 4 bug ก่อนรัน: dead hook/GATED seed/MDE emit/tickfeat header · 2: execution-review M1-M3 — prediction "3/3"→"2-independent+1-implied" [nested criteria] + relabel guard เป็น slice-discipline + leave-max-out = z-report) · design 4 รอบก่อนรัน (R2 Claude หักล้าง δ-set ของ R1 ด้วย ES-window จริง · R3 two-field adjudication + Engineer จับ "ceiling" ผิดทิศ · R4 P1-P4) · selection-contamination declared (asym@0.1/dur@0.25 = occupancy-guided)
- **scope-of-death:** **8 DC encodings (δ∈{0.1,0.25,0.5}×aw · M1 closes · classic dissection) ผ่าน linear+GBM ที่ real walk-exit บน SEARCH 2012-2020 · sensitivity-floor ≈ +0.07/+0.08** — ไม่ใช่ event-stream ทั้งแนว · ไม่ใช่ tick-DC · ไม่ใช่ proven-zero **[⚠ ANNOTATED 07-16 (ES-2 R2 discovery · Engineer-verified 20k walks · violations=0): dc_asym = degenerate-by-construction — alternation ของ classic dissection ⇒ |up−dn|≤1 ⇒ asym=±1/n_dc (≈±0.03 ที่ n_dc 35) → มิติ event-imbalance = effectively untested ใน card นี้ (scope-hole ที่ "8 encodings" ครอบไม่ถึง) · verdict KILL ไม่กระทบ (degenerate เท่ากันทั้ง observed/null = แฟร์) · tshare ของ ES-2 [CLAIM-0018] = การเทสมิตินั้นครั้งแรก]**
- **reproduce:** python Scripts/es1_card.py ; python Scripts/es1_card.py calib

### CLAIM-0018
- **observed:** Card ES-2 tick-DC event-stream ที่ real exit (pre-registered spec v2 · Engineer 3 รอบ · extractor `es2_tick_dc_features.py` + card `es2_card.py` · n=1486 · 8 encodings: al/os ×{0.1,0.25,0.5}aw + **tshare@0.1** [แทน asym ที่ degenerate — first test ของมิติ event-imbalance] + dur_wall@0.25 · บน bid ticks [01:00, B) · baseline-20) — **observed script-owned: S1 linear-forced-median9 = −0.3888 · S2 GBM-nested-median9 = +0.0002** · **p(S1 · OLS residual-perm B=1000) = 0.8571** (null mean −0.2315 · p95 −0.0067 — observed **แย่กว่า null**) · **p(S2 · GBM-proj residual-perm B=1000) = 0.1289** (null mean −0.1493 · p95 +0.0726 — observed เหนือ null +0.15 · **เลข signal-like สุดของ event program แต่ไม่ถึง α**) · α=0.025 (m=2) · **[P1] population-overlap vs CLAIM-0017: 100% · Jaccard 1.0000 — near-controlled comparison ยืนด้วย membership asserted** · calibration ก่อนรัน (15 draws · reproduce `es2_card.py calib`): S1 0/15@0.05 median 0.610 · S2 0/15 median 0.730 · gates: G1-SOFT 100.0000% ทั้ง 9 ปี · UNDEF==0 · NEG-CTRL boundary-read ยิงจริง (n_ticks 15,725→15,810) · SHA ac7ccab5 frozen+buildlog · DIAG (descriptive): nested over baseline-28 (+M1-DC): S1 −0.1616 S2 −0.0269 (**tick เพิ่ม ~0 เหนือ M1-DC**) · drop-δ0.25 ทำ S1 ดีขึ้น +0.2257 (mid-scale = noise ต่อ linear — pattern เดียวกับ ES-1) · GATED −0.2817 · os z-profile 5.87sd/5 วัน (report-only) · หมายเหตุ: numpy corrcoef RuntimeWarning ใน sign_gate bootstrap = **execution-review-verified benign** (2 events ใน 108,644 บรรทัด · ช่วง KA-cache ตอนต้น · degenerate resample → feature นับ unstable = ทิศ conservative · KA baseline-only cached เหมือนกันทุก replicate = แฟร์ทั้ง observed/null · S2 ไม่ใช้ gate)
- **supported:** **KILL ตาม pre-registration** — S1 แย่กว่า null ของตัวเอง (tick-DC เป็นภาระต่อ linear) · S2 เหนือ null แต่ p 0.13 ไม่ถึง α · root-cause: cross-corr tick↔M1 ต่ำที่ 0.1aw (0.12 = ใหม่จริง) แต่ **ความใหม่นั้นไม่มี direction information** (baseline-28 diag: increment เหนือ M1-DC ≈ 0) → **in-hand event forms ครบ 4 (OHLC-GBM · tick-fixed-window · M1-DC · tick-DC) ทดสอบแล้วทั้งหมด — จบ representation program ในมือ** (qualitative note ไม่ใช่ falsification ของ event-stream ทั้งแนว)
- **not-yet-supported:** event-functional นอก in-hand (Hawkes/volume-clock/order-flow events) · richer nonlinear · ข้อมูลใหม่ (Stage-F-form) · **ไม่ใช่ proven-zero** (S2 sensitivity-floor ≈ +0.0726 — not-detected ≠ falsified) · **prediction: held 1-independent + band 1/2** (Engineer MINOR-1: "no p<0.10" ⇒ KILL โดยตรรกะ — นับแยกไม่ได้ [pattern นับ nested ซ้ำครั้งที่ 3 — TP-1/ES-1/ES-2 · เข้า memory แล้ว] · band: S1 ✓ · **S2 ✗ 0.1289 ต่ำกว่าขอบ — declared ไม่กลบ**)
- **evidence-level:** L1 (Engineer execution-review 07-16: observed bit-exact ทุก seed · feature spot-check โค้ดอิสระ dev 4.99e-07 · null sanity B=40 · baseline-28 non-contamination พิสูจน์ 2 ทาง · warning benign-confirmed — precedent CLAIM-0015/16/17)
- **dependencies:** es2_tick_dc_features (frozen SHA ac7ccab5) · es2_card (ES2⊂ES1⊂TP2 machinery) → tp1_card fit_predict+return_w [AD-4 ขั้น 2 · backward-compatible kwarg · ไม่ retro-touch verdict] · es1_card (dissect/load_es/M1-DC สำหรับ baseline-28 diag) · tp1_tick_features manifest · brain_v1_run walker · h0_tickfeat rjR
- **invalidated-by:** event-functional นอก in-hand ให้ผล CI-backed · calibration mis-specification ภายหลัง · execution-review พบ defect
- **kind:** experiment
- **status:** terminal (KILL scoped · ไม่มี middle branch)
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y observed+p+verdict+MDE+overlap emit จาก script] · null-control[residual-perm ×2 · B=1000 · calibration 15 draws per-feature-set ของ card เอง] · seed-robust[Y median-9] · leak-guard[Y G1-SOFT 100% + UNDEF assert + slice-discipline + NEG-CTRL boundary-read power-proven + strict `<B`] · verified-by[Engineer execution-review 07-16 — reproduce ครบ (observed bit-exact · features อิสระ 4.99e-07 · null sanity · non-contamination 2 ทาง · warning benign)]
- **correction-lineage:** corrections 1 รอบ (execution-review MINOR-1: prediction "held 2/3" → "1-independent + band 1/2" — นับ nested implied ซ้ำครั้งที่ 3 ของ pattern เดิม · แก้ + memory updated) · design 3 รอบก่อนรัน (R1 B-1/B-2/M-1..4 · R2: Claude ค้นพบ asym-degeneracy + Engineer ตัด staged-gate ของ Claude [interaction blind-spot] · R3 P1-P4 implement-time) · dumps ก่อน freeze ครบ (occupancy/cross-corr/tshare — P&L-free) · selection-contamination declared (tshare@0.1/dur@0.25/δ set = occupancy-guided) · "near-controlled" claim ยืนด้วย overlap-audit (ไม่ใช่ assume)
- **scope-of-death:** **8 tick-DC encodings (δ∈{0.1,0.25,0.5}×aw · bid-only · classic dissection · tshare/dur wall-time) ผ่าน linear+GBM ที่ real walk-exit บน SEARCH 2012-2020 · sensitivity-floor ≈ −0.01/+0.07** — ไม่ใช่ event-stream ทั้งแนว · ไม่ใช่ proven-zero
- **reproduce:** python Scripts/es2_tick_dc_features.py ; python Scripts/es2_card.py ; python Scripts/es2_card.py calib

### CLAIM-0019
- **observed:** Card AD-1 STAGE-1 relationship-drift gate ที่ real exit (spec v8→work-order ratified 07-17 · design R1-R8 + adjudication 10 รอบ · `ad1_gate_calib.py` [canonical A · thresholds derive→assert==FROZEN 0.2033/0.1289/0.1394/0.0182 — M10 routing ใช้ derived] + `ad1_card.py` [canonical B · rebuild-from-session-record · **M8 acceptance: reproduce == run เดิม 07-16 MATCH ทุกค่า**] · n=1486 · 19-feat) — **c̄=+0.0717 · slope(lag1-5)=+0.0416 → NO-DETECT → STOP (binding gate — STAGE-2 ไม่รัน)** · cross-check real-perm q97.5=0.1874 vs synthetic 0.2033 = dev −7.8% OK · calib reproduce ตรงบันทึก: S1 0/15 med 0.640 nm −0.0007 · S2 1/15 med 0.640 nm −0.0012 · b=40 (R-ACF cap-limited) · machinery: fit_signedR/fit_predict rw=None/ones bit-exact 0.0 · S1/S2 rw=ones inert 0.0×9 seed · **STEP-3 RFLIP sweep (P&L-free · §9.1 pre-registered probe-informed · held 5/5 เกณฑ์ orthogonal): decay-arm false-STOP ≤1.7% ทุก P∈{2..8} blocks (bridge R4-M1 ขยายครอบ periodic — measured) · rolling-arm false-STOP hole P≈H (3/3.5): 16.7%/13.3% @ρ0.10 · 8.3%/8.3% @ρ0.15 · position = NO-DETECT class ทั้งหมด**
- **supported:** **exploratory NO-DETECT readout** — per-year feature→signed-R concordance ต่ำกว่า noise-floor ของ real data เอง (0.072 « 0.187) → smooth-adaptive (exp-decay H=480 · rolling K=300 · year-cadence) ไม่มี local relationship ให้ exploit บน 19-feat ที่ real exit · decay-primary STOP ปลอดภัยต่อ periodic-flip ทุก P ที่วัด
- **not-yet-supported:** **DISCLOSURE (บังคับอ่านคู่ verdict):** (i) STAGE-1 เคยรัน 07-16 ผู้เขียนเห็นผล · งานถูกถอนตามคำสั่ง Win — reconstruction 07-17 reproduce MATCH (ii) prediction 07-16 = **VOID ทั้ง 3 เกณฑ์** (foreknowledge + ไม่มี committed timestamp — ไม่ score) → claim นี้ = readout **ไม่ใช่ confirmatory** (iii) "reproduce-only" ในที่นี้ = deterministic re-run ของ look ที่ charge แล้ว **ไม่ใช่** LEDGER-disposition budget-exempt [C1] (iv) STAGE-2 ไม่รัน (binding gate + instrument-mismatch ต่อ residual) (v) **frontier ไม่ปิด** — residual measured: rolling-arm hole P≈H → detector/rolling follow-up card justified [M11 · +1 ⇒ 6/40 ถ้ารัน · วินตัดสิน priority] · declared นอก sweep: aperiodic · P<1 · P≥9 · phase/duty · representation อื่น · **ρ<0.10 (retention-hole region — นอก §9.1)** — mechanism: signal อ่อนลง → Δ ทั้งสอง arm เล็กลงสู่ noise-floor → false-STOP คาด ≤ ที่วัด (rolling-hole non-monotonic peak ~ρ0.10: 16.7% > 8.3%@ρ0.15 — range ที่ pre-register bracket worst case · วัดจริง = scope detector follow-up [M11]) · card-level residual นอกกรอบ sweep: fine-cadence [§6-drop] · MONO-rotation-blind [§3.0 declared] — 7-angle เต็ม = FRONTIER row adaptive · ไม่ใช่ proven-zero
- **evidence-level:** L1 (Engineer execution-review PASS-with-changes 07-17 — reproduce อิสระ 6/6 กลุ่มเลข · F-1 [stage1 derive→assert ในตัว — `Calib.from_arrays` กัน duplicate load · 3 จุด 177/188/190 · stage1 re-run เลขตรงเดิมทุกค่า] + F-2 [ρ-residual declare] applied · หมายเหตุ: L1 attest reproducibility+recording-integrity+disclosure — ไม่ใช่ confirmatory inference · S2-calib = เลขเดียวที่ reviewer ไม่ได้ re-run อิสระ (GBM-slow · trust ผ่าน S1-exact + regress GBM bit-exact))
- **dependencies:** ad1_gate_calib · ad1_card · Scripts/ad1_src/* (reconstruction source 6 ไฟล์) · fit_signedR+rw · tp1_card fit_predict+rw+return_w [AD-4 ขั้น 2 · backward-compatible kwarg · ไม่ retro-touch verdict] · direction_at_real_exit build_rows · brain_v1_run walker
- **invalidated-by:** freeze-commit (STEP 5) ไม่เกิด · detector card พิสูจน์ exploitable drift จริง
- **kind:** experiment
- **status:** live
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y ทุกเลข emit จาก script] · null-control[real-perm cross-check 200 + calib 15 draws/statistic + RFLIP ε per-arm (ε_d 0.0211 · ε_r 0.0488)] · seed-robust[NA — gate deterministic] · leak-guard[Y thresholds FROZEN ก่อน P&L + §9.1 ก่อน sweep + fold 2015 ตัด + M8 acceptance] · verified-by[engineer execution-review PASS-with-changes 07-17 (reproduce อิสระ: stage1/regress/rflip/thresholds/calib-S1 · ยกเว้น calib-S2) + Claude-Verify code-level 3 จุดขยาย]
- **correction-lineage:** design R1-R8 (R5/R6 FAIL จับ over-claim/retro-label ของ Claude) + adjudication 10 รอบหลังถอน (S3 reject · VOID · budget 5/40 · C-exploit reshape · M7 probe พลิก mechanistic note: residual อยู่ P≈H rolling ไม่ใช่ P≫H) — ทั้งหมด = card doc Changelog
- **scope-of-death:** NA (exploratory STOP-readout — ไม่ใช่ falsification · frontier ไม่ปิด)
- **reproduce:** python Scripts/ad1_gate_calib.py ; python Scripts/ad1_card.py regress ; python Scripts/ad1_card.py calib ; python Scripts/ad1_card.py stage1 ; python Scripts/ad1_gate_calib.py rflip

### CLAIM-0020
- **observed:** Card AD-2 rolling-recency unconditional — **FREEZE record (pre-registered · main ยังไม่รัน — ห้ามอ่านเป็นผล):** spec v6 (design R1 FAIL → R7 · 7 รอบ review) · primary S1 = payoff(rolling-K300 true-subset linear) − payoff(expanding) $/ไม้ folds 2016-2020 (m=1 · index-subsetting — standardization บน subset) · **certification (P&L-free · N=200/variant · `ad2_cert_out/*.csv` re-derive ได้จาก seeds): null variant = scattered (เลือกด้วย power-at-decision) · α\*_decision = min(q05 0.060, 0.05) = 0.05 [cap กัน liberalize — uncapped FPR จริง 7.0%] · FPR@decision 4.0%(<)/4.5%(≤) · power bracket [33.3, 36.7]%@RFLIP-3.0 · 6.7%@RFLIP-3.5 (headline conservative 33.3% · B0=99 boundary — B=1000 coincide)** · readout O3 estimation-first: point anchor null-mean ≈ −0.010 (ไม่ใช่ 0 — G1 กัน CLAIM-0016 re-commit) + MDE floor = null-q95 (ไม่ใช่ SESOI — ห้าม equivalence-claim)
- **supported:** **KILL — confirmatory (clean freeze-commit 999ebd9 10:38 ก่อน run 11:21 · git-verified):** main 07-20 — **S1 point = −0.6395 $/ไม้ · null-mean (run-time H0 center) = −0.1559 · point−null-mean = −0.4835 · MDE floor (null-q95) = +0.2560 · p = 0.9650 (B=1000 · escalation ไม่ trig — นอก band ถูกต้อง)** → recency (rolling-K300) ไม่กู้ lift บน real payoff ภายใน declared power · per-fold descriptive: 2016 +0.3057 · 2017 −0.1325 · 2018 −0.5036 · 2019 −0.7278 · 2020 −2.1271 (monotonic) · DIAG K600 −0.1611 · **adaptive frontier: smooth [AD-1 exploratory NO-DETECT] + recency [AD-2 confirmatory KILL] = ปิดทั้งคู่บน 19-feat ภายใน power ที่ประกาศ — ไม่ใช่ proof-of-absence**
- **not-yet-supported:** **PREDICTION SCORING (R8 — ห้าม over-claim ทั้งสองทิศ):** KILL = **confirmatory-held** (p=0.965 ≥ α*_dec 0.05 · pre-registered decision) · point-anchor = **descriptive-MISSED** — point −0.64 ≪ null-mean −0.156 (คาด ≈) · **§8 misspec 2 จุด (บทเรียน methodology ถาวร):** (a) anchor pin เลข synthetic −0.01 ข้ามสนามมาใช้กับ real (−0.156) = **cross-field number ละเมิด "ติดป้ายสนามวัด"** — ที่ถูกต้อง anchor เชิงสัญลักษณ์ "≈ run-time null-mean" (b) **nesting invalid** — p≥α* bound แค่ upper tail · point≈null-mean → p≈0.5 ไม่ใช่ 0.965 (ความพลาดร่วม Engineer-G4 + Claude accept) — คู่บทเรียน CLAIM-0016 · **anti-recency = descriptive controlled เท่านั้น:** recent-300 แย่กว่า random-window n=300 เท่ากัน 96.5% (sample-size controlled) — inferential ได้แค่ "recent < random" ไม่ใช่ "expanding คือทางถูก" (p ไม่ได้ทดสอบ vs expanding) · opposite-tail ไม่ register — two-sided = fork ห้าม [G3] · **fold2016 trigger MET (+0.3057 > pooled q95 +0.2560) + 3 caveats บังคับ:** bar หลวม (per-fold point vs pooled-q95 — variance คนละระดับ) · positive เดียวใน 5 folds · = **detector follow-up eligible ให้วินจัดลำดับ ไม่ใช่ signal detected** · declared residuals: P≈3.5 underpowered (6.7%) · y-model-risk conservative · fine-cadence/MONO/aperiodic = FRONTIER
- **evidence-level:** L1 (Engineer execution-review R8 07-20 PASS-with-changes [record wording — applied] — reproduce point/per-fold/K600 exact + integrity git-verified · Claude-Verify reproduce อิสระตรงทุกตัว · หมายเหตุ: **AD-2 L1 = confirmatory** [clean pre-registration] แข็งกว่า AD-1 L1 [exploratory])
- **dependencies:** ad2_card · ad1_card (AD1 loader/folds/caches) · ad1_gate_calib (K_ROLL/Calib) · tp1_card fit_predict+rw+return_w [AD-4 ขั้น 2 · backward-compatible kwarg · ไม่ retro-touch verdict] · direction_at_real_exit · brain_v1_run walker
- **invalidated-by:** detector follow-up (ถ้าวินเปิด) พิสูจน์ regime-conditional lift จริง · defect ใหม่ใน machinery ที่กระทบ p/point
- **kind:** experiment
- **status:** live
- **fairness:** field-tag[SIM-SEARCH 2012-2020 · lockbox/guard ไม่แตะ · null-mean anchor = run-time real-field] · pipeline-owned[Y ทุกเลข emit จาก ad2_card] · null-control[certified N=200 scattered FPR@dec 4.0-4.5% + B=1000] · seed-robust[PERM_ROOT 20260721 declared] · leak-guard[Y freeze-commit 999ebd9 ก่อน main (git-verified 10:38→11:21) + FROZEN_CERT hard-gate + M10 re-derive assert + machinery-2 synthetic-only] · verified-by[engineer execution-review R8 PASS-with-changes (reproduce exact) + Claude-Verify independent reproduce]
- **correction-lineage:** R1 FAIL detector v1 (5 blocking) → swap rolling-primary [R2/R3 — จับ mask≠subset FB-1] → calib จับ scattered-null 13.3%@n30 → certify N=200 refute alarm (4.5%) [R4/R5 — cap α* กัน liberalize FPR 7%] → O3 estimation-first + G1-G4 [R6/R7 — comparator bracket · Phipson-Smyth convention] → R8 post-run: prediction-scoring แยกส่วน + จับ §8 misspec (cross-field anchor + one-sided nesting) — ทั้งหมด = card doc Changelog
- **scope-of-death:** recency hard-window (K=300 + K=600 DIAG) บน 19-feat ที่ real exit · SEARCH 2012-2020 · power 33.3-36.7%@P3.0 / 6.7%@P3.5 — นอกนั้น = declared residuals (ไม่ใช่ falsification ของ adaptive ทั้ง axis)
- **budget:** **6/40 family v3** (charge ที่ main 07-20)
- **reproduce:** python Scripts/ad2_card.py regress ; python Scripts/ad2_card.py certify ; python Scripts/ad2_card.py cert_report ; python Scripts/ad2_card.py main

### CLAIM-0021
- **observed:** Card AD-3 online regime-flip detector — **STAGE-A KILL: instrument-infeasible (free-KILL gate pre-registered §3.3 · real d ไม่เคยเข้า detector)** · detcal corrected (Page-CUSUM allowance k∈{0,0.1,0.2,0.3,0.4} × W∈{100,150} · h = q95 per-fold max-CUSUM บน **NOISE binding-null** · N=120/archetype · synthetic-y บน real X · seed root 20260722): **FPR@h ทุก cell 1.7-6.3% (คุมได้) · detection SINGLE-FLIP @ρ0.10 = 0.0% ทั้ง 10 cells** — ไม่มี cell ผ่าน convention bar (det ≥80% ∧ FPR ≤5% — external ประกาศก่อนรัน)
- **supported:** **instrument-infeasibility (scoped):** online CUSUM-on-lagged-window-cosine @ρ0.10 · W viable {100,150} (W≥300 → windows/fold 2-4 = CUSUM degenerate) บน 19-feat — **root = SNR wall**: per-window signal-norm ρ√nsig = 0.20 < noise-norm √(NF/W) ≈ 0.44 @W=100 (cosine-noise sd≈0.23 ของ AD-1 — คำเตือน FB-1 "lethality sub-year W" ยืนด้วยเลข) · ไม่มี W ที่ SNR พอ ∧ windows พอ พร้อมกัน
- **not-yet-supported:** **fold2016 anomaly = NOT adjudicated** — ไม่มี instrument feasible มาตัดสิน contiguity-vs-regime · **ห้ามอ่านเป็น "no regime structure"** (นั่นคือ outcome ของ STAGE-B ที่ไม่เคยเกิด) → คงเป็น declared residual · richer detector families (Markov-switching/LR-changepoint) = declared residual — ชน SNR wall เดียวกันที่ ρ0.10/W เดียวกัน (complexity-gate ไม่ให้ escalate) · **เลขรอบแรก (NOISE FPR 55.8/84.2% · det 20.8/32.5%) = confounded artifact ของ D1 zero-allowance + D2 STABLE-calibration — superseded ห้าม cite** (บันทึกใน lineage)
- **evidence-level:** L1 (Engineer R4: ตั้งสมมติฐาน "premature" แล้ววัดหักล้างตัวเองด้วย corrected probe · Claude-Verify reproduce ตารางเต็ม 10 cells อิสระตรงเป๊ะ · official rerun N=120 deterministic)
- **dependencies:** ad3_card · ad1_card/ad2_card loaders (→ tp1_card fit_predict+return_w [AD-4 ขั้น 2 · backward-compatible kwarg · ไม่ retro-touch verdict]) · ad1_gate_calib · synth worlds (STABLE/NOISE/SINGLE-FLIP/RFLIP)
- **invalidated-by:** instrument ตระกูลใหม่ที่ทะลุ SNR wall ได้จริง (ต้องเปิด card ใหม่ + justification ว่าต่างเชิง information)
- **kind:** experiment
- **status:** live
- **fairness:** field-tag[SYNTHETIC-on-real-X · P&L-free — real d ไม่ถูกแตะ] · pipeline-owned[Y ทุกเลข emit จาก ad3_card detcal] · null-control[binding-null NOISE calibration + dual-archetype FPR] · seed-robust[20260722 declared] · leak-guard[Y no-real-d-before-freeze บังคับใน script + free-KILL ก่อน charge] · verified-by[engineer R4 corrected-probe + Claude-Verify full-grid reproduce]
- **correction-lineage:** design R1 (FB-1..4: cross-scale cite · self-grading bar · reconcile AD-2 · segment-floor) + R2/R3 (convention-norm bar 80%/5% · asymmetric tolerance · non-vacuous contiguity · floor=100 [fold2016 measured 166] · zero-dominated null characterization · FPR unit pin) → detcal v2-spec = KILL แต่ confounded (D1-D4) → **R4 self-refutation: corrected detector ยิ่ง infeasible ชัด (det 0% ที่ FPR คุมได้)** — ทั้งหมด = card doc Changelog
- **scope-of-death:** detector-conditional axis เฉพาะ CUSUM-lagged-cosine @ρ0.10 · W∈{100,150} · 19-feat · SEARCH 2012-2020 — ไม่ใช่ falsification ของ regime-existence
- **budget:** **exempt — 6/40 คงเดิม** (STAGE-A P&L-free ทั้งหมด · ไม่มี real-payoff look — precedent RFLIP sweep [CLAIM-0019])
- **reproduce:** python Scripts/ad3_card.py regress ; python Scripts/ad3_card.py detcal
