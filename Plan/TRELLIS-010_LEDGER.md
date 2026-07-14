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
| Representation: **tick-price** (in-hand เหนือ OHLC-ceiling · DPI) | tickvol 0/7 [CLAIM-0007→0009] · spread dead [CLAIM-0008 DEAD] · **TP-1 nested 07-13: gated 0/9 CI-positive + perm-p 0.805 · forced-in 1/9 (+0.028) · GBM point-positive ทุก seed แต่ 0/9 CI** [CLAIM-0015] | **open (INCONCLUSIVE gate-limited — ไม่ eliminate · form เหลือ = gate ที่เห็น conditional signal / feature richer)** |
| Representation: nonlinear/event-stream/multi-scale | ยังไม่เทสที่ real exit นอกจาก GBM | **open** |
| Optimization: adaptive/rolling (concept-drift remedy) | Gate-A linear AUC 0.547 ลด static-prior [CLAIM-0007→0009] | **open** |
| Magnitude channel (label-agnostic) | in-sample MI 6/19 (**DIAGNOSTIC/overfit-floor** · de-cluster [5,1,6]) · OOS straddle-net-cost **dead** [CLAIM-0007→0009] · "+0.66 sturdier" เดิม = demoted no-artifact · day-mean not-detected [CLAIM-0013] · at-trigger ผ่าน intraday-features = **structurally blocked** [CLAIM-0014] | **open (เฉพาะ session-open form ที่ยังไม่เทส · prior บาง · priority ต่ำ)** |
| Discovery: additive opp **realizable** ด้วย ex-ante trigger | validation 07-10: ceiling ยืน (+1.5..+4 · n~30) แต่ **0/7 trigger-config FWE** · anchor ลบ [CLAIM-0004] | **open (ceiling-only — กุญแจ = ex-ante discovery ไม่ใช่ trigger เพิ่ม)** |

**FROZEN terminal (session 07-08):** direction-at-real-exit [CLAIM-0010] · **[07-10/11] opportunity-validation: ceiling ยืน (+1.5..+4 · n~30) · realizable 0/7 FWE** [CLAIM-0004] + [CLAIM-0013] · **[07-12] at-trigger = structural-wall [CLAIM-0014] + demote "+0.66" (no-artifact) → magnitude arm ปิดโดยพฤตินัย (prior บาง · form เหลือ = session-open เท่านั้น)** · **[07-13] TP-1 tick-price nested = INCONCLUSIVE gate-limited [CLAIM-0015] (budget 1/40 family v3 ใหม่ — Win ปิด family เก่า 9/40)** · **next = Win ตัดสิน** (execution-review TP-1 · gate-form ใหม่ · discovery mechanism · monetize-v4 · forward-test)

---

## CARRIED-FORWARD DEPENDENCIES
data-artifact + เลข frozen ที่ current-frame พึ่ง (methodology อยู่ doctrine ไม่ใช่ที่นี่):

- **v4 "Dual Asian-Range Breakout" = 1 proven-behavior candidate** [CLAIM-0012] — canonical `dual_asian_sim.py` (§9:107) · WF-OOS +$876 · holdout EU-corrected **+$511.8 PF1.54** · **สถานะ = candidate ไม่ใช่ proven-edge** (bootstrap P(≤0)≈7.6%)
- **h0 SEARCH dataset 2012-2020** (`Research/h0/*.csv` · +$532.8 field · reconciliation ปิดเป๊ะ) — field-tag ของ direction claims ทั้งหมด
- **walker `brain_v1_run.py`** — canonical exit (trailing 1×R + overnight) · regression 1,487/1,487 exact · imported โดย 15 scripts
- **BASELINE H0:** ปีแพ้ 7 ปี (2012/14/17/18/19/22/23) รวม −$185.4 · 15.5y +$1,087.6 (WF config · `ea_catchup`) — search-window losers = 5 ปี −$135.2
- **clock:** BT-clock = EET EU-DST · tester 2025/26 เดิม (−169/+330/+318) = artifact (UTC ดิบ) · holdout US-rule +802 = ตาย

---

## SCRIPT INDEX
> **machine-generated skeleton** จาก `ledger_check.py --emit-index` (ASSET=import-scan · EXPERIMENT=`__main__`) · disposition = เติมเอง (ดุลพินิจ) · **ห้าม hand-list role** (DEFECT-10)
> DISP ∈ live→CLAIM-NNNN | superseded→CLAIM-NNNN | legacy→ARCHIVE | reproduce-only(why) | self-test(why)

- `asian_bo_sim` :: EXPERIMENT=legacy→ARCHIVE
- `brain_v1_ceiling` :: EXPERIMENT=legacy→ARCHIVE
- `brain_v1_run` :: ASSET(imported 15) :: EXPERIMENT=reproduce-only(canonical-walker · regression 1487/1487)
- `c10_ms_features` :: EXPERIMENT=legacy→ARCHIVE
- `c6_poke_features` :: EXPERIMENT=legacy→ARCHIVE
- `c7_tick_features` :: EXPERIMENT=legacy→ARCHIVE
- `c9_dc_features` :: EXPERIMENT=legacy→ARCHIVE
- `diag_analyze` :: EXPERIMENT=legacy→ARCHIVE
- `dir_features` :: ASSET(imported 1)
- `direction_at_real_exit` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0010
- `direction_predictor` :: ASSET(imported 4) :: EXPERIMENT=superseded→CLAIM-0005
- `direction_predictor_v1` :: ASSET(imported 5) :: EXPERIMENT=superseded→CLAIM-0006
- `discovery_probe` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0004
- `opportunity_validation` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0013
- `dual_asian_sim` :: ASSET(imported 7) :: EXPERIMENT=reproduce-only(v4-canonical numbers §9:107)
- `edge_bar_mc` :: EXPERIMENT=live→CLAIM-0001
- `edge_screen` :: EXPERIMENT=legacy→ARCHIVE
- `edge_screen2` :: EXPERIMENT=legacy→ARCHIVE
- `entry_features` :: EXPERIMENT=legacy→ARCHIVE
- `entry_platform` :: ASSET(imported 8) :: EXPERIMENT=legacy→ARCHIVE
- `exhaustion_fade` :: EXPERIMENT=live→CLAIM-0003
- `fade_dataset` :: EXPERIMENT=live→CLAIM-0003
- `gate1_mi_ceiling` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0007
- `gate2_population` :: EXPERIMENT=live→CLAIM-0007
- `gate_c_wf` :: ASSET(imported 3) :: EXPERIMENT=live→CLAIM-0007
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
- `layer0_meanrev_pregate` :: EXPERIMENT=legacy→ARCHIVE
- `magnitude_at_trigger` :: EXPERIMENT=live→CLAIM-0014
- `layer1_null_test` :: EXPERIMENT=legacy→ARCHIVE
- `layer2_real_data` :: EXPERIMENT=legacy→ARCHIVE
- `layer2b_bar_null` :: EXPERIMENT=legacy→ARCHIVE
- `ledger_check` :: EXPERIMENT=self-test(traceability tooling · --self-test fixtures+golden)
- `mr_sim` :: EXPERIMENT=legacy→ARCHIVE
- `opportunity_unit` :: EXPERIMENT=live→CLAIM-0001
- `opportunity_unit_v2` :: EXPERIMENT=superseded→CLAIM-0002
- `opportunity_unit_v3` :: ASSET(imported 1) :: EXPERIMENT=superseded→CLAIM-0002
- `opportunity_unit_v4` :: ASSET(imported 4) :: EXPERIMENT=live→CLAIM-0002
- `stage0_join` :: ASSET(imported 2) :: EXPERIMENT=reproduce-only(stage0-join · carried h0)
- `stage0_verify_import` :: EXPERIMENT=legacy→ARCHIVE
- `stageb_pipeline` :: EXPERIMENT=legacy→ARCHIVE
- `test_b_direction_decomp` :: ASSET(imported 1) :: EXPERIMENT=live→CLAIM-0009
- `tp1_card` :: EXPERIMENT=live→CLAIM-0015
- `tp1_tick_features` :: EXPERIMENT=live→CLAIM-0015
- `walk_forward` :: EXPERIMENT=reproduce-only(v4 anchored-WF +876)

---

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
- **observed:** Research Traceability System — `ledger_check.py` (validate + --emit-index · ast import-scan robust · check-list = docstring SSOT) · self-test + golden ALL PASS (count = --self-test output) · LEDGER/ARCHIVE/STATUS-trim/DoD
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
- **not-yet-supported:** **"proven edge"** — Engineer NO-GO · bootstrap CI95 กว้าง · กำไรกระจุก 2023-26 · dual ไม่มี OOS เหลือ · real-tick CONFIRM ยังไม่ผ่าน (clock-fix รอ Gate 0)
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
- **observed:** Card TP-1 tick-price nested-incremental ที่ real exit (n=1486 · 6 bid tick features event-time N=3000 · baseline 24 = 19-FEATS + 4 M1-shadows + log_winsec · pre-registered ก่อนรัน) — **LINEAR GATED (primary): agg [−0.7303, +0.0821]$/ไม้ · CI-lower [−1.2278, −0.1358] · 0/9 seed CI-positive** · **perm-null B=1000 (รันจริง): observed −0.2352 · p=0.8052** (null mean −0.1172 · p95 +0.0761) · **FORCED-IN (gate-bypass tick): agg [−0.5480, +0.4190] · 1/9 seed CI-lower>0 (+0.0280 — ⚠ single-seed บางเฉียบเหนือ 0 · verdict INCONCLUSIVE ยืนบนเส้นนี้ตาม asymmetric rule ที่ pre-register)** · **GBM nested (A/B same-hyperparams): agg point บวกทุก seed [+0.0069, +0.1916] แต่ 0/9 CI-positive** · gates: G1-SOFT reconstruction 100.0000% ทุกปี (~3.15M bars · bad=0 · buildlog artifact) · G1-HARD PASS · G3 future-mask+shadow-sentinel 54 entries (power พิสูจน์ด้วย negative-control 2 planted bugs ยิงจริง) · NaN-drop 0 · tickfeat SHA 94c8e68cf8ec6649
- **supported:** ใต้ 6 features + nested protocol นี้ — **ไม่พบ additive tick-price signal ผ่าน gated pipeline** (0/9 + perm-p 0.81) · verdict ตาม pre-registered asymmetric rule = **INCONCLUSIVE (gate-limited)** — forced-in มี 1/9 seed CI-positive → **ห้ามเรียก KILL / ห้าม eliminate frontier** (univariate sign-gate อาจกด conditional signal — เงื่อนไขที่ประกาศก่อนรัน)
- **not-yet-supported:** "tick-price มี additive signal" (ไม่มีหลักฐาน CI-backed) · "tick-price ตาย" (gate-limited + GBM point-positive ทุก seed แต่ไม่ CI) · features/window/gate form อื่น · **prediction-score:** ทำนาย clean-null → ได้ INCONCLUSIVE — sub-outcome เป็น fact: aggregate −0.2352 ∈ [−0.30,+0.10] ✓ · gated 0/9 ✓ · perm>0.05 ✓ · GBM ทาย ≤0 ✗ (point บวกทุก seed) · **2/4 metric เบนเข้า weak-signal (GBM 9/9 point-positive + forced-in 1/9)** — ไม่นับเป็น "ถูก 3/4" (Engineer M-4: เกณฑ์ผิดที่ pre-register โดน forced-in ชนตามตัวอักษร)
- **evidence-level:** L1 (Engineer execution-review 07-14: reproduce ทุก inferential number + feature spot-check โค้ดอิสระ — precedent CLAIM-0014)
- **dependencies:** tp1_tick_features (frozen SHA) · tp1_card · direction_at_real_exit (build_rows/sign_gate/protocol) · brain_v1_run walker · dir_features · ticks eet 2012-2020
- **invalidated-by:** gate form ที่เห็น conditional signal (multivariate/nested-gate) ให้ผลชัดทางใดทางหนึ่ง · feature set richer · execution-review พบ defect
- **kind:** experiment
- **status:** live
- **fairness:** field-tag[SIM-SEARCH] · pipeline-owned[Y verdict จาก script] · null-control[permutation B=1000 pipeline-run · review-verify = code-audit + B=40 sanity (p 0.854 สอดคล้อง 0.805) ไม่ใช่ full re-run — ประกาศตรง] · seed-robust[Y 9-seed ทั้ง 3 branch] · leak-guard[Y G1 HARD/SOFT(assert≥99.9) + G3 future-mask+shadow-sentinel + negative-control พิสูจน์ guard power + strict boundary t(j)+60s] · verified-by[Engineer execution-review + apply-plan review 07-14]
- **correction-lineage:** corrections 2 รอบ · design ผ่าน Engineer 3 รอบก่อนรัน (R1 B1-B3/M1-M6 · R2 P1-P6 · R3 Issue1-6 — spec v2 ใน docstring tp1_card) · Claude จับ Engineer ผิด 1 (M4b Exness ticks ไม่มีจริง) · Engineer จับ Claude 2 (corr-gate → nested · perm ไม่เคยรันใน template) · G1-HARD checker bug (partial-first-minute 1,467) จับโดย fail-loud เอง แก้ก่อนมี output · **รอบ 2 (07-14 execution-review M-1..M-4 + apply-plan F-1..F-5):** integrity hardening (buildlog artifact + SOFT assert + shadow-sentinel non-mutating + negative-control) — no-behavior-change พิสูจน์ด้วย CSV SHA เท่าเดิม · prediction-score แก้จาก "3/4" เป็น framing ตรง (M-4)
- **scope-of-death:** NA (INCONCLUSIVE — ไม่มี elimination · frontier tick-price ยัง open)
- **reproduce:** python Scripts/tp1_tick_features.py ; python Scripts/tp1_card.py
