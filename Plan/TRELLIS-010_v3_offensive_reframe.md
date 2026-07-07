# TRELLIS-010 v3 — Root = Engine Edge · Constraint ≠ Excuse

**เป้าหมาย EA (วิน = authority · ไม่เปลี่ยน · ห้ามเสนออะไรขัดเป้า):**
**เริ่มทุน $100 → (1) อยู่รอด (2) ทำกำไรได้มาก (3) เข้าเทรดได้ทุกเมื่อที่เห็นโอกาส** · แก้ที่ **Root Cause ไม่ใช่ Symptom**
- **No-Trade อนุญาต**เมื่อมีเหตุผล root-cause อธิบายได้ (ไม่มี setup / no structure / ข่าวแรง) · **ห้าม** skip เพราะ backtest แพ้ (symptom) / ไม่เทรดไม่มีเหตุผล / เพิ่ม param เลี่ยง / เปลี่ยนทุน-บัญชี-lot ให้ปัญหาหาย

> เอกสารสะสม (accumulate) — เก็บ insight ดีทุกชิ้นพร้อมที่มา · ห้าม rewrite ทิ้งของเดิม · แก้ด้วย Edit เฉพาะจุด · ทุกเลข field=SIM-SEARCH flat-0.01 2012-2020 (ต้อง re-derive CONFIRM ก่อนเรียก edge)

---

## 1. ⭐ Constraint (ข้อจำกัด — ยอมรับ+ออกแบบรอบมัน) vs Excuse (ข้ออ้าง — กำจัด)
เกณฑ์: **constraint** = จริงตามธรรมชาติ (instrument/math/data) เปลี่ยนไม่ได้ → engine ทำงานภายใต้มัน · **excuse** = อ้างเพื่อลดเป้า/ไม่แก้ engine/หลบ → ห้าม

| limitation | ชนิด | หลักฐาน | engine ต้องทำ |
|---|---|---|---|
| min-lot 0.01 granularity | **CONSTRAINT** | broker fixed | sizing รอบมัน |
| 1×R ≈ 5.4% ของ $100 ที่ min-lot | **CONSTRAINT** (median R $5.43×min-lot · mean R̄ $6.7) | h0 R-dist | bootstrap ยอมรับ ~5%/ไม้ · edge ต้องแรงพอรอด |
| edge บน SEARCH ≠ ruin-safe บน LIVE (haircut ~1.2/ไม้ high-vol) | **CONSTRAINT** (sim-optimism วัดแล้ว) | log RED FLAG 2026 −9.3 | edge bar ต้อง clear บน **CONFIRM** ไม่ใช่ SEARCH |
| edge อ่อน (v4 +0.36/ไม้ WR47%) | **ROOT ต้องแก้** | max-cum-loss −$134.9 > $100 · min-eq $26.97 (SEARCH · ruin% pending `edge_bar_mc.py`) | สร้าง edge ≥ ruin-safe bar (§4) |
| pooled ceiling (reshaping conserved ≤598<692) | **CONSTRAINT** (math) | log:289,295 | ต้อง **additive** ทะลุ |
| dead-zone [$100,~$335] risk%-sizing ตาย | **CONSTRAINT** (eq<50R) | verify 07-07 | bootstrap flat-min-lot |
| order-flow ไม่มีใน OHLCV (tick=count) | **CONSTRAINT** (data) | project-tick memory | หา mechanism บน price-action ก่อน |
| **"เพิ่มทุน/min-deposit $335-1000"** | **EXCUSE** ❌ | ลดเป้า | goal $100 fixed |
| **"ใช้ Cent account"** | **EXCUSE** ❌ | เพิ่มทุนปลอมตัว | กำจัด |
| **"กำไรมากเป็นไปไม่ได้"** | **EXCUSE** ❌ | ลดความคาดหวัง | scaling+edge ทำได้ |
| **"martingale ห้าม"** (ผมตีความผิด) | **EXCUSE** ❌ | ban = loss-driven escalation เท่านั้น (`mql5-ea-engineer.md:30`,`research:22`) | adaptive sizing (risk+edge) allowed · loss-driven escalation forbidden (นิยามเชิงพฤติกรรม §5) |
| **"Stage F ตอนนี้"** | **EXCUSE** ❌ | หลบก่อน frame ถูกจนสุด | เฉพาะหลัง budget 40/40 |

## 2. Asset เก็บ (frame-independent)
Stage-0 fidelity · walker `brain_v1_run.py` (per-trade exact) · regime dataset (h0) · **v4 = 1 proven behavior** (ไม่ overclaim +876) · verify 3 ชั้น/pre-register/budget/lockbox · ความรู้ falsification

## 3. ปัญหาที่แท้ (ROOT) = Engine Edge
engine **เข้าใจว่าราคาเคลื่อนเพราะอะไร แล้วลงมือให้ถูก (ทำกำไร)** · behaviors active: CONTINUATION · FADE · [setup ที่ v4 ข้าม] · No-Trade เฉพาะอ่านออกว่าไม่มีโอกาสจริง · **"$100 ไม่รอด" = อาการ edge อ่อน ไม่ใช่ปัญหาทุน**

## 4. นิยาม "สำเร็จ" (absolute · pre-register ตัวเลข · CONFIRM field)
- **Edge bar (script-owned `edge_bar_mc.py` — intrabar-−R) · 3 metric แยกสถานะ (taxonomy):**
  - **DECISION (gate จริง):** เอา distribution ของ Step-2 เข้า `eval_ruin` โดยตรง → P(ruin≤margin)<2% ที่ max(IID, block) · **CONFIRM = run CONFIRM distribution ตรงๆ ไม่ใช่ +haircut บน SEARCH scalar (double-count)**
  - **STRESS-test:** winner-scaled/IID (shape "let-winners-run") — SEARCH-LB ≈ **$2.0-2.5/ไม้ (5.6-7×v4)** boundary ~$2.0 seed-robust (ไม่ใช่ upper bound เหนือทุก shape)
  - **ORIENTATION:** mshift/blk20 ~$1.25/3.5× · ทั้งสามตอบคนละคำถาม ไม่แข่งว่าจริงกว่า · แทน ">$0.40" ที่อ่อน
- P(ruin จาก $100 flat-min-lot) < threshold (Monte-Carlo pre-registered) · PF · total 15.5y + WF OOS + lockbox
- **MinRisk ≤ AllowedRisk gate** (ChatGPT Q1 — formal): engine ตอบก่อนเทรดว่า min-tradable-risk ≤ allowed-risk หรือไม่
- **Opportunity-capture = diagnostic** (ChatGPT Q3): Coverage = Captured / **Available (จาก ground-truth opportunity §6)** + **No-Trade-reason completeness — ทุก No-Trade ตอบ "Why?" ได้ ห้าม "Unknown"** · ไม่ใช่ pass/fail
- ห้ามผ่อนให้ผ่าน

## 5. Sizing (regime-split · edge-centric ไม่แตะทุน)
- **BOOTSTRAP ($100→~$335):** flat-min-lot (constraint บังคับ) · เทรดทุกโอกาสจริงที่ ~5%/ไม้
  - **survival = engineered edge property · ยังไม่ proven:** edge ปัจจุบัน **ไม่ ruin-safe** ที่ $100 — max-cum-loss **−$134.9 > $100** · min-equity **$26.97** · streak 11 (SEARCH · CONFIRM แย่กว่า) · **นี่คือเหตุผลว่า survival ต้องมาจาก edge ไม่ใช่ cap**
  - **survival delivered by:** ยก edge ผ่าน §4 ruin-safe bar บน **CONFIRM**, verified โดย `edge_bar_mc.py` (script เป็นเจ้าของ verdict — ไม่ใช่เลขสรุปในเอกสาร)
  - **❌ consec-loss halt ยังห้าม** (halt-เพื่อรอด = หลบ 8.1) · **❌ กฎ "No-Trade เมื่อ min-lot>2%budget"** ห้าม (99.2% = disguised skip) · เหลือแค่ margin/position-existence guard (broker physics · ต้องพิสูจน์ block โอกาสจริง = 0 ไม้)
- **COMPOUNDING (≥~$335): Adaptive Position Sizing** (นิยามเชิงพฤติกรรม code-verifiable — เลี่ยงคำ "martingale" ที่กำกวม เพราะวิชาการ = loss-driven)
  - ✅ **ALLOWED:** size จาก **predefined risk budget + measured market edge/conviction** (risk%-of-equity compounding [จำเป็นต่อ "กำไรมาก"] · conviction scaling · Kelly-fraction optional) · positions อิสระ
  - ❌ **FORBIDDEN:** size เพิ่มที่ **trigger ด้วยการขาดทุน (realized/unrealized)** = classical martingale + recovery/underwater-averaging (`research:22,33`)
  - **เกณฑ์ตรวจจากโค้ด (2 ชั้น — encode invariant ไม่ใช่ mechanism):** (i) sizing function ห้ามอ่าน prior-loss / unrealized-PnL เป็น input ที่เพิ่มขนาด (อ่านได้เฉพาะ risk%+equity+edge-signal) · (ii) **[DEFECT-2] aggregate directional exposure ห้ามเพิ่มขณะ book ทิศนั้น unrealized-negative** (อ่าน book-unrealized เป็น **VETO** ได้ ไม่ใช่ size input) — ปิด price-triggered underwater-averaging (`research:22` tail-borrow)
- **ลำดับ (Grid Doctrine #1 · `TRELLIS-002:131`):** พิสูจน์ edge บน flat ก่อน → scaling ค่อยมา (MM เปลี่ยน sign expectancy ไม่ได้)

## 6. Measurement frame — Canonical Opportunity Unit (ChatGPT Q6 crux + Engineer separation)
**คำถามฐาน (ChatGPT Q6): "1 หน่วยโอกาส" คืออะไร** — ต้องมี canonical unit ก่อน ไม่งั้นทุก metric ผูก strategy → circular · **แก้ dead-gate ด้วยแยก 3 วัตถุ (Engineer):**
- **Unit** = decision point enumerate ex-ante ด้วย price-geometry ล้วน (session-open / breakout-event นิยามจาก level) → ex-ante + strategy-independent
- **Label** = ex-post oracle/MFE (perfect-exit ในหน้าต่างถือ) — **อนาคตใช้ได้เพราะเป็น target ไม่ใช่ feature** · oracle = upper bound (`brain_v1_ceiling.py` มี) → strategy-independent
- **Predictor** = ex-ante state features (h0) as-of ≤ close j−1 → **no-leak = ข้อกำหนดของ predictor เท่านั้น**
- **Ground-truth opportunity set (ChatGPT Q3):** Market → trend/BOS/pullback/move ≥ threshold = opportunity โดยไม่สน EA เข้าไหม → วัด Coverage
- ตัดสิน behavior เป็น **opportunity-coverage** ไม่ใช่ skip-switch (measurement fairness)

## 7. FADE — root-cause mechanism (ChatGPT Q2/Q4 · ห้ามนิยามด้วย outcome)
- **ห้ามนิยาม FADE ด้วย P&L/drawdown/overshoot (= outcome ทั้งหมด)** · root = **mechanism**: impulse → **momentum-decay** → order-absorption → exhaustion → reversal · engine ต้อง detect momentum-decay ไม่ใช่ "loss เยอะ→fade"
- overshoot ยังไม่พอ — ต้องตอบ **"overshoot เกิดเพราะอะไร"** (liquidity sweep / buying-selling climax / delta divergence / range-expansion-failure) = mechanism ที่ระบุ "ใครถูกบังคับเทรด"
- **counterfactual (ChatGPT Q4):** mirror BUY→SELL **≠ fade จริง** (market ไม่ symmetric) · real fade = สร้างจากกฎ fade เอง (sweep+rejection+structure-break)
- **แต่ mirror = cheap kill-test ก่อน (Claude+Engineer):** flip ทิศบนวัน exhaustion ยังไม่ช่วย = mechanism-fade ก็ไม่รอด → ผ่านค่อยสร้าง mechanism-fade (แพง)
- **⚠️ CONSTRAINT (Claude):** mechanism ในอุดมคติ (delta/absorption) ต้อง order-flow ที่ **OHLCV ไม่มี** → หา price-action proxy ก่อน · ถ้าพิสูจน์ว่า proxy ไม่พอจริง (หลัง frame ถูก) = trigger Stage F (ไม่ใช่ก่อน)

## 8. Root-cause gate (4-leg — กัน narrative rubber-stamp)
(a) mechanism ระบุ **"ใครถูกบังคับเทรด"** · (b) prediction ก่อนเห็น conditional P&L · (c) รอด permutation-null + OOS ≥6/8 · (d) features ไม่มี P&L · ขาดข้อใด = reject

## 9. Roadmap (edge-first · Metric-before-Dataset [ChatGPT Q5] · ไม่มี capital-loop / Stage-F-escape)
1. สร้าง `Scripts/edge_bar_mc.py` (system-of-record ของ ruin/edge-bar) — **block/streak-preserving resampling** (streak=11, gold autocorrelate — IID under-estimate ruin) · $100 flat-0.01 · report **P(equity≤0) + P(equity≤margin-floor)** · **derive haircut/bar เอง ไม่ hardcode ~$2.3**
   - **[DEFECT-1] intra-trade MAE:** ทุกไม้ที่ resample ต้องจำลอง **แตะ −R intrabar ก่อน แล้วค่อย settle เป็น realized pnl** (R column มีอยู่ = max realistic MAE · ไม่ต้อง tick data) → เช็ค ruin ที่ **intrabar trough** ไม่ใช่แค่ close (Grid Doctrine #6: worst-case > เพดาน)
   - Step-1 run = **SEARCH-provisional** (CONFIRM per-trade ยังไม่มีจน §9:5) · **fail-loud ว่า ruin% = LOWER BOUND** จน real-tick CONFIRM ปิด gap/slippage
   - + นิยาม Opportunity Unit (unit/label/predictor §6) — **metric ก่อน dataset**
   - **v2 ก่อน Step-2 claim opportunity-capture:** swing/event-level unit + **trigger-constrained oracle** (realizable ไม่ใช่ hindsight) + **Difficulty dim** (oracle-2R บน trend เรียบ ≠ whipsaw · coverage% ต้อง weight difficulty)
2. สร้าง dataset ตาม metric — **`EdgeDistribution{wins, losses, pnl, R, meta}` object** (ไม่ใช่ scalar) · counterfactual behavior P&L (pnl_continuation/pnl_fade-mirror)
3. วัด edge ใต้ 4-leg gate · **DECISION = `eval_ruin(EdgeDistribution)` <2%** (ไม่ใช่ ≥scalar-bar) · mirror-fade kill-test → mechanism-fade
   - **Discovery × Execution + Error Analysis (ChatGPT · root-cause):** decompose lost-edge = **False-Opp / Missed-Opp / Wrong-Direction / Wrong-Exit / Late-Entry** → ระบุ edge หายจาก Discovery (หาโอกาสผิด) หรือ Execution (เข้า/ออกผิด) — expectancy เดี่ยว conflate สอง root ที่ fix คนละแบบ · **2 oracle: A=Opportunity · B=Behavior**
   - **Calibration:** predictor probability ต้อง calibrated (บอก 78% → เกิดจริง ~78%) ก่อน sizing/Kelly
   - **Edge-Stability per-regime:** expectancy ต่อ regime (trend/range/vol/news) ไม่ใช่รวม · edge ปี/regime เดียว ≠ engine edge (เสริม 4-leg leg-c OOS)
4. risk-control/sizing = §5 regime-split ใน EA spec
5. validate CONFIRM (capped real-tick) + lockbox แตะครั้งเดียว
- **OHLCV-exhaustion:** budget 40/40 ceiling-first ไม่มี edge ≥ bar → เฉพาะตอนนั้น Stage F

**Step-2 outcome (2026-07-07) + PIVOT: Behavior-research → Discovery-research:**
- **fade ตายทั้ง 2 construction บน v4-entry** (mirror WR12% · exhaustion-fade −0.6/ไม้ WR40% · robust 20+ DoF + 9/9 ปี · 2R ไม่พลิก · Engineer PASS) · scope = "overshoot-of-level ≠ exhaustion proxy บน OHLCV" ไม่ใช่ "fade ตายทั้งแนว" · framing: **"ภายใต้ v4 entry distribution behavior-space ไม่มี additive headroom"** = ยืน pooled-ceiling
- **⭐ bottleneck ย้าย Behavior-Optimization → DISCOVERY** (หา opportunity ที่ v4 จับไม่ได้ = additive path · opportunity_unit: v4 blind lift −2.2pp) · roadmap: Oracle-Opportunity → v4-missed → Discovery → Entry-Candidate → Behavior → Execution
- **Discovery Falsification Gate (ChatGPT · คู่ root-cause gate):** discovery mechanism ตอบ ex-ante "เจอ opportunity type ไหนที่ v4 เจอไม่ได้" + พิสูจน์ **เพิ่ม oracle-coverage (additive)** ไม่ใช่ย้าย entry ใน opportunity เดิม
- **⚠ Information-theory ceiling:** OHLC-derived feature = coordinate-transform · `I(feature;future) ≤ I(OHLC;future)` → **feature-engineering ≠ edge · เพิ่ม info ต้อง new-data (order-flow=Stage F)** · representation (event-stream) ช่วย learnability ไม่ใช่ info
- **Edge Attribution:** Loss → Discovery/Direction/Timing/Exit/Risk tree · Regime bootstrap (MC · sample within regime) · layer-architecture defer หลัง Discovery stable

**Discovery probe v0 (Momentum family) + Engineer catch (2026-07-07):**
- Claude วัด**ผิด population** (all v4-missed · 94% chop) → เกือบบันทึก "ceiling→Stage F" (escape ที่ doctrine ห้าม) · Engineer จับ → แก้: **v4-missed ∧ oracle-opportunity** → **conditioning-error fix (ไม่ใช่ sign-flip): −2.88 → +1.745 (n=31 WR54.8%)** = **Discovery NOT falsified · additive opp มีจริง · Stage-F premature**
- ⭐ **decomposition = bottleneck จริง:** dir ตรง oracle +17.98/WR100% · ผิด −13.48/WR12% → **PnL = Opportunity × DIRECTION × Execution · Opportunity ผ่าน · Direction = คอขวด** (opening-range trigger +10.18 ยืน)
- **Q5 Attribution (gate เพิ่ม):** decompose Opportunity-Recall / Direction-Accuracy / Execution-Efficiency ต่อ probe · **Q4 Orthogonality:** Discovery ห้าม overlap v4 สูง (วัด coverage-gain/MI)
- **⚠ Oracle guardrail (สำคัญ):** oracle = **labeling instrument สำหรับ eval/coverage · ไม่ใช่ realizable prediction target** · direction predictor เทรนจาก info ณ decision-time เท่านั้น (ห้าม best-hindsight-dir = conceptual hindsight-leakage)
- **H1 = mixture** (v4-missed = hard-regime + missed-opportunity ทั้งคู่ · ไม่ pure hard-regime) · info-theory wording: OHLC feature ไม่เพิ่ม info แต่อาจเพิ่ม statistical-efficiency/expressibility · scope = Momentum-family · **Stage-F ต่อเมื่อหลาย family fail** (ไม่ใช่ 1 trigger)
- **roadmap: Behavior → Discovery → Direction-Prediction** · pipeline: Oracle-Opp → Trigger → **Direction-Predictor (decision-time)** → Execution → Risk · **next: direction predictor บน missed-opp** (small-n ยังไม่ signal-bar · ต้อง trigger-constrained oracle ก่อน claim)

**Opportunity-Unit reconstruction v2→v4 (2026-07-07..08 · 6 review รอบ · ESTIMAND-FIRST · Engineer PASS):**
- **บทเรียนแกน:** ข้อสรุป**พลิก 4 ครั้งเพราะ measurement-definition ไม่ใช่ model** — (1) conditioning (all-missed vs missed∧opp) (2) risk-unit mismatch (daily-ATR $16.6 ≫ account $5.43) (3) state-vs-event trigger (DirAcc 62%↔85%) (4) outcome-conditioned population (base-rate เป็น 100% ปลอม) → **freeze PROTOCOL ไม่ freeze RESULT**
- **FROZEN PROTOCOL (`Scripts/opportunity_unit_v4.py` · estimand เขียนก่อน freeze):** Q0 enroll ทุก bar (outcome-BLIND · base-rate computable) → Q1 normalizer natural-vol calibrate→exogenous §1 target (P3-wall: ไม่มี natural indep-vol ที่ account-scale) → Q2 realizable-MFE/R distribution (ไม่ฝัง threshold) → Q3 trigger EVENT (cross-bar · forward-scan discoverability curve) → Q4 event-overlap coverage → Q5 direction decision-time · **causal chain Sampling→Magnitude→Triggerability→Direction→Execution→Risk** · nulls (circular-shift + dir-randomize) · day-clustered CI · **estimand-sensitivity gate** (H×stop perturb · headline sign/ordering survival · verified robust)
- **Evidence Ladder:** L0 artifact → L1 impl-invariant → L2 WF → L3 holdout → L4 CONFIRM real-tick → market-property · **ห้าม freeze headline** จน invariant
- **⭐ L1 FINDINGS (impl-invariant · verified robust H×stop):** (a) opportunity มีจริง+ใหญ่ (base-rate B(1R)=59% computable) (b) discovery พอใช้ — **ทิศถูก residual 1.46R (ไม่ late) · ทิศผิด 0.20R** (c) **DIRECTION = คอขวดจริง** (ยืนยัน · ไม่ใช่ artifact เดิม) (d) naive-trigger มี directional signal เล็กแต่ CI-significant ที่ τ≥1.5 (DirAcc 51.6/52.7% > coin) = **floor 52.7% ที่ learned-predictor ต้องชนะ**
- **NEXT (Engineer-reframe · higher-leverage):** predictor objective = **OOS signed-R / expectancy-net-of-cost ไม่ใช่ classification-accuracy** (payoff asymmetric: ถูก +1.46R / ผิด −1R stop → 51% บน high-payoff subset ชนะ 55% symmetric · align เป้า "กำไร" ไม่ใช่ hit-rate) · features as-of ≤ close-j (no-leak) · valid null + OOS holdout · **clock price-match = hard gate ก่อน predictor** (session filter clock-dependent · memory 2025 sim+207/tester−169) · FWE caveat บน trigger-grid

## 10. Governance
verify 3 ชั้น · expectancy-before-code · anti-curve-fit (numeric pre-register CONFIRM) · anti-flip-flop (เก็บ v4-entry) · **no-excuse** (ห้ามเปลี่ยนทุน/บัญชี/param/skip-ไม่มีเหตุผล/Stage-F-ก่อนเวลา) · ทุก decision root-cause-อธิบายได้-หรือ-reject · lockbox 2021-26
