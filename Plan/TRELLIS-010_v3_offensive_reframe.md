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
- **⚠ Information-theory ceiling:** OHLC-derived feature = coordinate-transform · `I(feature;future) ≤ I(OHLC;future)` → **feature-engineering ≠ edge · เพิ่ม info ต้อง new-data** · representation (event-stream) ช่วย learnability ไม่ใช่ info
  - **[แก้ 2026-07-08 · Engineer P-B verified DPI]** ceiling bind เฉพาะ **OHLC-DERIVED** feature · tick-level price **ไม่ใช่** f(OHLC) (OHLC=g(ticks)) → DPI พลิก `I(tick;future) ≥ I(OHLC;future)` = tick-price มี **headroom เหนือ ceiling = in-hand channel ที่ต้องเทสต์ก่อน Stage-F** (ไม่ใช่ order-flow ภายนอกเท่านั้น) · empirical 07-08: tick_volume-count **0/7** · spread **dead** (de-cluster [0,0,0] · OOS +0.004R CI คร่อม 0) → **tick-price = in-hand channel สุดท้ายก่อน Stage-F**
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
- **⭐ L1 FINDINGS (impl-invariant · verified robust H×stop):** (a) opportunity มีจริง+ใหญ่ (base-rate B(1R)=59% computable) (b) discovery พอใช้ — **ทิศถูก residual ~1.6R (ไม่ late · sampling-robust ในทิศ right≫wrong) · ทิศผิด 0.18R** (c) **DIRECTION = คอขวดจริง** (ยืนยัน · ไม่ใช่ artifact เดิม) (d) naive-trigger มี directional signal เล็กแต่ CI-significant ที่ τ≥1.5 (DirAcc 51.6/52.7% > coin) = **floor 52.7% ที่ learned-predictor ต้องชนะ**
- **NEXT (Engineer-reframe · higher-leverage):** predictor objective = **OOS signed-R / expectancy-net-of-cost ไม่ใช่ classification-accuracy** (payoff asymmetric: ถูก +1.46R / ผิด −1R stop → 51% บน high-payoff subset ชนะ 55% symmetric · align เป้า "กำไร" ไม่ใช่ hit-rate) · features as-of ≤ close-j (no-leak) · valid null + OOS holdout · **clock price-match = hard gate ก่อน predictor** (session filter clock-dependent · memory 2025 sim+207/tester−169) · FWE caveat บน trigger-grid

**Direction Predictor v0 (2026-07-08 · Engineer PASS · honest NEGATIVE baseline):**
- `Scripts/direction_predictor.py`: decision-point=event-trigger · feature as-of ≤ bar (no-leak · Engineer verified) · **objective = maximize E[signed-R] โดยตรง** (∇=mean((rl−rs)p(1−p)X) · payoff-weight ในตัว · ไม่ใช่ classification) · train 12-17 / **OOS holdout 18-20** · baselines same-exit + permutation-null + day-clustered CI + **ex-ante confidence-gate curve**
- **ผล:** predictor OOS **−0.093R** ≈ follow-trigger −0.094 ≈ permutation-null −0.095 · train −0.011 vs best-constant-dir −0.017 (**features lift +0.006 = ~0 · UNDERFIT**) · confidence-gate ทุก q% ยังลบ CI คร่อม 0 · **oracle-if-direction-known +0.775R** = edge มีจริงแต่ล็อกด้วย direction
- **payoff-direction NON-STATIONARY (observed · ไม่ใช่ root ที่ยืนยัน):** mean(rl−rs) SIGN-FLIP train −0.125 → OOS +0.018 · per-year −0.25..+0.12 · **แต่ห้าม over-claim ว่า "non-stationarity = root cause"** (ChatGPT ถูก — evidence รองรับแค่ "payoff-dir non-stationary" ไม่ใช่ "คือ root")
- **linear/univariate OHLCV = ไม่มี OOS cost-clearing directional edge** · **ห้ามสรุป "ทำนายทิศไม่ได้"** (info-theory ceiling ยังไม่พิสูจน์ · nonlinear/representation/adaptivity ยังไม่ทดสอบ)

**Direction claim reconciliation (2026-07-08 · ChatGPT×2 + Engineer adjudicate · Claude over-claim ยอมรับ+downgrade):**
- **⚠ ผม over-claim** "DIRECTION = คอขวด / non-stationarity = root / GBM ไม่ช่วย / 0/19 = dead" — **downgrade ทั้งหมด** · claim ที่ defensible (L0/L1): *"ใต้ tested linear/univariate OHLCV representation + 1R/1.5R exit — ไม่มี OOS directional edge · fit ไม่ได้แม้ in-sample (+0.006R) · oracle localizes gap ไปที่ DIRECTION **สำหรับ strategy-family + exit นี้** · payoff-dir sign-flip train→OOS (cause ยังไม่ decompose)"* · **sign-stability/0-19 = DIAGNOSTIC (linear+univariate under-test) ไม่ใช่ verdict · ห้าม hard-gate/veto GBM**
- **GATE A (covariate P(X) vs concept P(Y|X) · Claude run 07-08 · ⚠ LINEAR test เท่านั้น):** LINEAR domain-classifier AUC(train/OOS)=**0.547** · reweight ปิด flip ~0% → **สนับสนุน concept-drift ใต้ representation ปัจจุบัน** · **⚠ ผม over-claim (ChatGPT ans1008 จับ):** ยัง**ไม่ใช่** "static-GBM ไม่ transfer / แก้ debate GBM" — Gate A linear **reduces prior ของ static-model ไม่ eliminate** (GBM อาจหา nonlinear region เสถียรบน feature เดิม · AUC 0.547 linear = linear แยกไม่ออก ≠ P(X) ใกล้กัน) → ต้อง **nonlinear confirm (GBM-domain-classifier AUC + Gate B in-sample nonlinear)** ก่อนสรุป
- **MDE (Engineer 6b · qualify ChatGPT):** CI half-width **~0.043R** vs required ruin-safe **~0.37-0.46R** → **null = decision-relevant *under current flat-min-lot deployment target*** (§5 bootstrap · effect เล็กกว่าอาจ deploy ได้ถ้า sizing ต่าง — ไม่ใช่ "ไร้ค่า")
- **HYPOTHESIS ELIMINATION MATRIX (ChatGPT · full causal-chain — Sampling→Label→Representation→Optimization→Population→Execution→Deployment):** eliminated=[Representation: linear-univariate OHLCV · Optimization: linear E[signed-R] fit] · **ยังเปิด**=[Representation: nonlinear/event-stream/multi-scale · Label: exit-policy อื่น (1R/1.5R conditional) · Population: opportunity-conditioned/high-τ · Optimization: adaptive/rolling (concept-drift remedy) · no-directional-info-at-all] · **static-model = prior ลด ไม่ eliminate**
- **⭐ ADD (ChatGPT ans1008 · ก่อน/คู่ Gate B):** (1) **RANK-ORDERING diagnostic** — Spearman/Kendall(prediction-score, oracle-payoff) — objective=signed-R ต้องวัด rank ไม่ใช่แค่ direction-accuracy (score เรียง opportunity ถูก = ทำเงินแม้ dir 50%) · (2) **NEGATIVE CONTROLS** — inject future-feature (pipeline รั่ว→ควรได้ edge = validate pipeline detect ได้) + randomized-label→0 · (3) **nonlinear P(X)/P(Y|X)** — GBM domain-classifier ไม่ใช่ linear เดียว
- **⭐⭐ EVIDENCE PROMOTION PROTOCOL (ChatGPT · governance · v2 = DIVERSITY ไม่ใช่ COUNT):** promotion อิง **evidence diversity / independent failure-mode** ไม่ใช่จำนวน (linear+tree > linear1+2+3 · inductive-bias ต่างกัน = evidence จริง) → L0→L1 [pass **independent failure-mode** + impl-invariant] · L1→L2 [diverse regimes/model-families + effect-size ≥ bar] · L2→L3 [OOS holdout + deflated-Sharpe] · L3→L4 [CONFIRM real-tick + lockbox] · **Stage-F ต่อเมื่อ ≥N *diverse* representations fail Gate-B**
- **HYPOTHESIS MATRIX = QUALITATIVE (Engineer P5 · ไม่มีเลข posterior):** Hypothesis | Evidence-so-far | **open/eliminated** | Decision · **ห้ามใส่เลข prior/posterior** (= LLM-judgment ในเสื้อกาวน์) · direction ของ belief พูดเชิงคุณภาพได้ ("Gate-A ลด prior static-model") ไม่ผูกตัวเลข
- **DECISION CURVE = corroborating report (Engineer D4 · ไม่ใช่ trigger):** **gating scalar เดียว = WF-lift CI** · decision-curve (payoff-monotonicity ต่อ score-bucket · bucket-n pre-register · day-clustered top−bottom CI-separation) = required corroboration · Spearman = diagnostic
- **Gate B → adaptive ต้อง gate (ChatGPT ค้าน Claude):** Gate B = Information? · **No → representation dead (จบ · ไม่ไป adaptive)** · Yes → ค่อย adaptive/regime-encoding · adaptive ≠ default-next
- **⭐⭐⭐ CLAIM OBJECT (ChatGPT ans1024 · upgrade Claim-Template → structured object · root-fix over-claim):** ทุกข้อสรุป = object 6 field — **Observed** (tool output) · **Supported** (conditional "ใต้ X") · **Not-yet-supported** · **Evidence-Level** (L0-L4) · **Dependencies** (test/rep/model/exit ที่พึ่ง) · **Invalidated-by** (evidence อะไรจะล้ม claim นี้) → evidence ใหม่มา = รู้ทันทีว่า claim ไหนโดนล้ม (queryable ไม่ใช่ prose)
- **EVIDENCE LIFECYCLE (Promote/Freeze/Demote/Retire · concept เก็บไว้ · ⏸ DEFER formalism):** งานวิจัยมี demote (เจอ leakage → กลับ L0) — เก็บเป็นหลัก ไม่สร้าง apparatus ตอนนี้ (Engineer Root-B: non-blocking)
- **❌ EVIDENCE WEIGHT numerics — DROPPED (Engineer P5):** posterior weights 0.2/0.5/0.95 = **LLM-judgment ในเสื้อกาวน์ = over-claim ในรูปแบบใหม่** (สิ่งที่ governance นี้มีไว้กัน) · flag "experimental" ไม่ลบ anchoring-hazard → **ใช้ Hypothesis-Elimination-Matrix เชิงคุณภาพ (open/eliminated) เท่านั้น · ไม่มีเลข posterior**
- **⏸ META-VALIDATION — DEFER (future · non-blocking):** ห้ามให้ governance-refinement = goalpost-moving แทน experiment (Engineer Root-B: ผมสร้าง cathedral แทนรัน MI-ceiling · หยุด refine แล้วรัน)
- **⭐ GATE B PRE-REGISTERED DECISION TABLE v2 (Engineer FAIL fix · metric = OOS/WF ไม่ใช่ in-sample · baseline carried-forward · thresholds ผูก MDE):**
  - **metric = expanding-WF signed-R lift เหนือ TRAIN-best-constant-carried-forward** (= direction ที่เลือกได้ ex-ante · ไม่ใช่ in-sample argmax ที่ contaminated โดย sign-flip) · **operative KILL-floor = design-matched random-label WF-lift CI-upper** (Engineer D3 · ~0.086R = order-of-magnitude sanity ไม่ใช่ threshold) · required ruin-safe **0.37-0.46R**
  | WF-lift 95%CI outcome | Decision |
  |---|---|
  | CI-upper < **random-label-WF floor** (~0.086R sanity) | **KILL representation** (undetectable = undeployable) |
  | CI excludes 0 แต่ point ≪ 0.37R | **INFO-not-deployable** (investigate additivity · **ห้าม imply deploy**) |
  | CI excludes 0 + survive **MTC** (Bonferroni/deflated-Sharpe over families×buckets) | **proceed Gate C** (adaptive/regime — ไม่ใช่ static) |
  | + OOS-holdout beat null + deflated-Sharpe | **promote L1** (⚠ **L1 ≠ deployable** · ยัง ~8× ต่ำกว่า ruin-safe) |
  - **in-sample = capacity-probe (MI + depth-limited tree) เท่านั้น · ห้าม gate ด้วย raw-GBM in-sample** (overfit-guaranteed) · **negative-control (random-label) = noise-floor co-report · "lift จริง" = real−random CI-separated** · report ด้วย **Claim Object + Decision Curve (corroborating · pre-register bucket-n + CI-separation)** · MTC: **Bonferroni บน lift-CI · deflated-Sharpe เฉพาะตอนรายงาน Sharpe/t-stat** (Engineer: ไม่ synonym) · **Stage-F ต่อเมื่อ ≥N diverse representations ตก KILL**
  - **⭐⭐ EXPERIMENT ORDER (Engineer Root-B · drop cathedral · run decisive first):** (0) **clock/session price-match 2012-2020** (doctrine hard-gate `dp:22` ที่ผมละเมิด — ทำก่อน KILL-authorized run) → (1) **MI-CEILING** — Kraskov k-NN I(features; **continuous (rl−rs)** ไม่ใช่ sign · magnitude-weighted = objective-aligned · Engineer D1) · calibrate random-label (bias-correct real−random) · **marginal + low-dim subset (≤6-8) · 19-d = bias-prone flag** (**ไม่ใช่ '1 เลข bound ทุก model'**) · ~0 bits หลัง bias-correct → KILL → (2) เฉพาะถ้า MI มี bits ค่อย WF-nonlinear (GBM ฯลฯ)
- **REVISED PLAN (superseded by GATE B TABLE v2 ข้างบน · Engineer D2 reconcile):** **Gate A (done · LINEAR → reduces static-prior ไม่ eliminate · ⚠ ไม่ commit concept-drift)** → **Gate B = TABLE v2 ข้างบน** (clock-match → MI-ceiling continuous-target → WF-nonlinear · metric OOS/WF ไม่ใช่ in-sample) → **Gate C static-vs-adaptive = ตัดสินโดยผล nonlinear (ห้าม pre-commit · ห้ามอ้าง 'concept-drift บอกแล้ว' = LINEAR เท่านั้น)** · fix v1 holdout-leak `v1:122` · **freeze good-eng** (signed-R obj · ex-ante gate · same-exit baseline · block-permutation-null · oracle-separate · not-Stage-F) · stopping-rule = TABLE v2

## 10. Governance
verify 3 ชั้น · expectancy-before-code · anti-curve-fit (numeric pre-register CONFIRM) · anti-flip-flop (เก็บ v4-entry) · **no-excuse** (ห้ามเปลี่ยนทุน/บัญชี/param/skip-ไม่มีเหตุผล/Stage-F-ก่อนเวลา) · ทุก decision root-cause-อธิบายได้-หรือ-reject · lockbox 2021-26
