# Card AD-3 — Online Regime-Flip Detector (adaptive residual สุดท้าย) · design v2

> **สถานะ: ปิดที่ STAGE-A (07-20) = KILL instrument-infeasible [CLAIM-0021 L1 · budget-exempt — real d ไม่เคยถูกแตะ · freeze/STAGE-B ไม่เกิด]** — ผลทางการ = LEDGER ที่เดียว (doc นี้ = design record)
> **เป้า (วินเลือก 07-20):** ปิด residual แกนสุดท้ายของ adaptive frontier ที่วัดแล้ว — **detector-conditional axis** (rolling-hole P≈H [CLAIM-0019] + fold2016 trigger MET [CLAIM-0020])
> **expectation ประกาศตรง: คาด KILL / no-fire** (เหตุ §2) · คุณค่า = adjudicate fold2016 anomaly + ปิด detector axis ด้วยการวัด ไม่ใช่ prose · **ห้ามอ่านเป็น "น่าจะเจอ edge"**
> lineage: AD-1 smooth NO-DETECT [CLAIM-0019 L1] · AD-2 recency confirmatory KILL [CLAIM-0020 L1 · commit 1e614c7] — card นี้ = follow-up ที่ประกาศ eligible ใน CLAIM-0020

## 1. คำถามของ card (hypothesis AD-3)
ความสัมพันธ์ 19-feat → signed-R มี **discrete regime-flip ที่ตรวจจับได้ ex-ante แบบ online** และ **การ fit เฉพาะข้อมูลหลัง flip ล่าสุด (purity) กู้ payoff lift ที่ expanding/rolling จับไม่ได้** — เจาะจงกว่านั้น: ปรากฏการณ์ fold2016 (+0.31 — fold เดียวที่ rolling window คร่อม era-flip 2014/15) เป็นของจริงหรือ noise

## 2. Prior evidence (อ่านสดจาก LEDGER 07-20)
- **หนุน (อ่อน — declared):** (1) rolling-hole P≈H = 16.7% @ρ0.10 [CLAIM-0019 — residual-existence บน synthetic] (2) **fold2016 trigger MET (+0.3057 > pooled q95 +0.2560) — พร้อม 3 caveats บังคับ: bar หลวม (per-fold vs pooled-q95) · positive เดียวใน 5 folds · hypothesis-generating เท่านั้น** [CLAIM-0020] (3) fold 2016 = fold เดียวที่ purity มีความหมาย (rolling pre-flip 44.7% · 2017-2020 = 0% pure แล้ว) [AD-1 record]
- **ค้าน (แรงกว่า):** real slope flat +0.0416 · era-flip อดีต = **single transition n=1** · AD-2 aggregate = anti-recency ชัด (−0.64 · p=0.965) · purity-advantage bound = **1/5 fold** [AD-2 R2]
- **นัยของผล:** แม้ SIGNAL — value = single-fold-era phenomenon (n=1 era) → promotion path แคบ **ประกาศล่วงหน้า**

### 2.1 Reconciliation กับ AD-2 mechanism [R2-FB-3 · precise wording บังคับ]
- AD-2 **falsify เฉพาะ mean-proximity channel** (recent ไกลจาก test 4/5 folds) + ระบุ **contiguity-break เป็น null-shape driver** — AD-2 **ไม่ได้ทดสอบ "regime มี/ไม่มี"** → regime-structure = **untested = คำถามของ card นี้เอง**
- **H0 ที่แท้ของ AD-3: "fold2016 +0.31 = contiguity-variance"** (ไม่ใช่แค่ "no regime") · **คุณค่าจริงของ card = re-fire block-perm null แยกสองคำอธิบายนี้ได้ ซึ่ง AD-2 unconditional ทำไม่ได้:** block-perm รักษา within-block contiguity แต่ทำลาย era-order → contiguity-variance **รอดใน null** (ถูก subtract → p สูง) · era-structure จริง **ไม่รอด** (→ p ต่ำ)
- **เหตุ expect-KILL เพิ่ม (purity-vs-quantity [R2-FB-4]):** conditional ที่ fold2016 เทรด quantity→purity (300 ไม้ปน 44.7% → 166 pure) — AD-2 anti-recency ชี้ less-data-worse → การตัดข้อมูลอาจเสียมากกว่าที่ purity ได้
- **fold 2017-2020 = purity 100% อยู่แล้วแต่ rolling แพ้หนัก** (−0.13..−2.13) → purity per se ไม่ช่วย 4/5 folds — hypothesis เหลือช่องแคบที่ fold2016 เท่านั้น

## 3. Design (3-STAGE · pattern ที่ pass มาแล้ว + fix R1-hazards ทั้งหมด)

### 3.1 ตรึง (เหมือน AD-1/AD-2)
representation 19-feat frozen · walker/`build_rows` เดิม · d=rl−rs · SEARCH 2012-2020 · **lockbox 2024-26 + guard 2021-23 ไม่แตะ** · folds 2016-2020 (2015 excluded) · seed root ใหม่ประกาศใน script (`ad3_card.py` canonical เดียว · reuse AD1/AD2 loaders — no duplicate)

### 3.2 Instrument: online CUSUM + lagged-local reference [แก้ R1-F1 ที่ราก — S2]
- per-window ρ̂_w(t) บน window W trades (สูตร `rho_hat_real` per-window) → **alignment a(t) = cos(ρ̂_w(t), ρ̂_w(t−W))** — **lagged-local ref ไม่ใช่ expanding-prefix** [R2-FB-1 scope ตรง]: expanding-ref ยุบตัวใน repeated-flip (R1-F1 · 12.5% cells undefined @block) · lagged-ref sign-agreement 0.967 **@block-scale ρ0.10** (AD-2:81) — **safety ที่ operating-W (sub-year) = ยังไม่วัด → เป็น STAGE-A W-power pass-gate** (ห้าม cite ข้าม scale — บทเรียน CLAIM-0020 cross-field)
- **Page CUSUM มี allowance k [R4-D1 — ปิด under-spec]:** S = max(0, S − a − k) · fire เมื่อ S > h → reset · ตำแหน่ง fire = detected-flip — zero-allowance (spec v2 เดิม) = degenerate: บน NOISE ทำ reflected random-walk → fire มั่ว (measured FPR 56-84%)
- **(k, h) calibrate บน binding null = NOISE [R4-D2]** — ไม่ใช่ STABLE (null ง่ายสุด — alignment บวกกด CUSUM → h ต่ำเกิน) · bar บังคับ FPR ≤5% ทั้งสอง archetype → binding = NOISE · STAGE-B envelope อิง NOISE [R4-D3] · regress ทุกตัว = synthetic เท่านั้น [R4-D4]
- **ห้าม hardcode break 2014/15** [double-dip §6 AD-1] — จุด break ที่รู้ใช้เป็น post-hoc sanity read เท่านั้น · **ห้าม tune (W,h) ให้ reproduce เลข 16.7%/fold2016** [contamination — ผู้เขียนเห็น cell แล้ว]
- **regime-conditional fit:** training = trades หลัง detected-flip ล่าสุด ∧ อยู่ใน fold-train ∧ respect embargo Nemb [S5] · test-year **ห้าม trigger reset** (กัน within-test lookahead — glossary C7) · ไม่มี flip detected ใน fold → conditional ≡ expanding (**regression บังคับ: bit-exact 0.0**)
- **minimum post-flip segment floor = 100 trades [R2-FB-4]:** segment < 100 → fallback expanding + mark fold "under-resolved (declared)" · **เหตุจริง (โปร่งใส — ไม่ใช่แค่ 5×NF rule):** floor 190 (10×NF) และ 300 (K_ROLL precedent) จะ **exclude fold2016 เอง** — **measured: fold2016 post-flip (2015) = 166 trades = 8.7 obs/param (marginal · script-owned)** → ใช้ DoF-minimum · **ห้ามปรับ floor ให้พอดี** — ถ้า floor ใด exclude fold2016 = report design-failure ไม่ tune · STAGE-A DIAG ต้อง emit segment-size จริงต่อ fold + assert floor · **fallback ต้อง bit-identical ทั้ง obs และทุก null draw** (symmetry — assert ใน regression [R2-zero-mass])

### 3.3 STAGE-A: detector calibration (P&L-free · ไม่ charge · แก้ R1-F5/F6 — S4)
- สนาม: X จริง + y สังเคราะห์ (pattern Calib/gen_y · seed แยก) · archetypes: **NOISE** (FPR) · **STABLE** (false-alarm) · **SINGLE-FLIP** (era-analog — prior จริง n=1) · **RFLIP@{3,3.5}** (residual cells)
- **ตรึงเลขก่อน STAGE-B (derive→freeze→assert M10):** operating (W, h) + **W-power quantify** (R1-F6: กี่ windows/series · cosine-noise ที่ W นั้น + undefined-rate ที่ operating-W [FB-1]) — ทุกตัวเป็นเลขใน FROZEN_DET
- **pass-gate STAGE-A = convention-norm bar (external · ประกาศตรงนี้ ก่อนรัน — ห้าม fit กับ output [R2-FB-2 แก้ self-grading]):**
  - detection-rate ≥ **80%** บน SINGLE-FLIP @ρ0.10 (era-analog archetype · ρ0.10 = family power-floor ตั้งแต่ AD-1)
  - **FPR ≤ 5% ต่อ fold-sequence บน NOISE/STABLE** — **pin หน่วย: per-fold** (Claude-Verify R3: หน่วย FPR กำหนด zero-mass arithmetic — per-fold 5% → P(no-fire ทั้ง 5 folds) ≈ 0.95⁵ ≈ 77%)
  - **position-tolerance asymmetric [R2 value-add · cost-based แบบ t_stop]:** fire-**late** ≤ W (conservative — เสีย power ทิศเดียว) · fire-**early** ≤ b=40 (เข้มกว่า — early = ปน pre-flip = bias)
  - ไม่ผ่านบาร์ → **KILL ที่ STAGE-A ฟรี** (instrument infeasible — ไม่แตะ budget)
- **contiguity-verify (non-vacuous — บังคับผ่านก่อนยอมรับ real low-p [R2-FB-3]):** STABLE world (ใช้ real-X → contiguity structure อยู่ครบ — verified จาก `synth_stable_world` ad1_card:236-254) → detector+conditional pipeline ต้องให้ **p-distribution ≈ uniform** (contiguity-variance ถูก null subtract จริง) — assert ใน certify

### 3.4 STAGE-B: real run (แตะ P&L → **charge +1 ⇒ 7/40**)
- รัน detector บน real signed-R → flips detected + ตำแหน่ง
- **statistic pre-registered [R2-M-2]: total fire-count (รวม 5 folds) เทียบ STABLE fire-count q95 จาก STAGE-A** (envelope = เลขใน FROZEN_DET)
- **binding:** fire-count ≤ envelope → **STOP/KILL-detector** — record readout · ไม่รัน STAGE-C · fold2016 anomaly ได้คำตอบ "ไม่มี detectable regime structure" **[= STAGE-B path ที่ไม่เกิด — card ปิดที่ STAGE-A → actual: fold2016 NOT-adjudicated · ดู header/CLAIM-0021]**
- fire-count > envelope → STAGE-C · **declare [R2-zero-mass (c)]: STAGE-C ไม่ใช่ independent confirmation ของ STAGE-B** (null non-zero mass มาจาก spurious-fire เป็นหลัก) — added-value ของ STAGE-C = **conditional MAGNITUDE** เหนือ fire-count

### 3.5 STAGE-C: conditional inference (รันเฉพาะ STAGE-B ผ่าน · แก้ R1-F2 ที่ราก — S3)
- **S1 (m=1):** agg[payoff(regime-conditional linear) − payoff(expanding linear)] $/ไม้ · folds 2016-2020
- **null = re-fire ทั้ง pipeline** [S3 — post-selection ตาม standard]: ทุก replicate permute block-order (b re-derive) → **รัน detector ใหม่บน permuted sequence** → conditional fit ตาม fires ของ replicate นั้น → statistic · selection อยู่ใน resample loop → FPR ไม่ถูก under-state
- **⚠ zero-dominated mixture null [R2 — pre-registered characterization บังคับ]:** ใต้ H0 fold ที่ไม่ fire → diff = 0 เป๊ะ → null = mixture {exact-zeros (per-fold FPR 5% → ~77% ของ draws = 0 ทั้ง 5 folds), spurious-conditional values} — ไม่ใช่ smooth null แบบ AD-2 · ผลบังคับ: (1) **B ห้าม pin ลอยๆ — size จาก measured P(fire|null) ใน timing-probe** ให้ live-draws ≥ floor ที่ทำ α* เสถียร (per-fold FPR 5% → live ≈ 22.6%/draw → B=500 ให้ live ~113 — ยืนยันด้วย probe ไม่ใช่ arithmetic) (2) **certify emit zero-fraction ของ STABLE null** + sanity-flag ต่อ null-shape นี้เอง (ห้ามยืม flags AD-2 [M-3 · CLAIM-0017 per-statistic]) (3) floor-fallback bit-identical obs/null (assert §3.2) · escalation band รอบ α*_dec
- **calibrated-α*_decision = min(q05 ของ null-of-p STABLE N=200, 0.05)** [pattern AD-2 R5 — cap กัน liberalize] · certify ก่อน freeze (STAGE-A ขยายครอบ)
- **readout O3 estimation-first:** point vs **run-time null-mean (anchor เชิงสัญลักษณ์ — ห้าม pin เลขข้ามสนาม [บทเรียน CLAIM-0020])** vs MDE floor (null-q95 — ไม่ใช่ SESOI · ห้าม equivalence-claim) · per-fold descriptive · claim คง m=1

## 4. Gates / regressions (ก่อน STAGE-B)
- detector unit: SINGLE-FLIP world รู้ตำแหน่ง → detected position ตรง ± tolerance · NOISE → fire-rate ≈ FPR
- machinery: no-fire → conditional ≡ expanding **bit-exact 0.0** · flip-before-fold-start → subset ถูกต้อง (assert ตำแหน่ง)
- integrity: time-sort assert · FROZEN_DET derive→assert · P&L-guard ใน calib · **ทุก regression ที่แตะ real payoff = identity-zero เท่านั้น** (เคส operative รันบน synthetic — กัน free-look [AD-2 machinery-2])

## 5. DIAG (descriptive — ไม่เข้า verdict)
- detected positions vs era-2014/15 (post-hoc read) · CUSUM path plot-values ต่อ fold · fold2016 conditional-vs-rolling comparison (descriptive)

## 6. Declared drops + residuals
- aperiodic-general นอก scope CUSUM (duty/phase แปลก) · fine-cadence = คนละ card (FRONTIER) · Markov-switching full model — CUSUM = minimal instrument ก่อน (escalate เมื่อมีของจริง)
- **ถ้า KILL (design-time wording — เขียนไว้สำหรับ STAGE-B path):** detector axis ปิด scoped · fold2016 = adjudicated **[path นี้ไม่เกิด — actual outcome = STAGE-A instrument-infeasible → fold2016 NOT-adjudicated · SoR = CLAIM-0021]** · adaptive frontier เหลือ declared residuals (P≈3.5 underpowered · fine-cadence · MONO · aperiodic · fold2016)

## 7. Budget + governance + contamination
- charge **+1 ⇒ 7/40** ที่ STAGE-B (real-touch) · STAGE-A/certify = P&L-free
- canonical `ad3_card.py` · ทุกเลข emit จาก script · same-commit DoD (CLAIM ใหม่ + FRONTIER + ledger_check)
- freeze-commit rule บังคับ · FROZEN_DET hard-gate ใน main (pattern FROZEN_CERT)
- **[R2-M-1] timing-probe ก่อน freeze (P&L-free · synthetic):** วัด wall-time ของ re-fire null + **P(fire|null)** → size B + ประกาศ compute-budget จาก script (ไม่ใช่ prose) · chunked-persist pattern (AD-2 `cert_*_chunk` → csv) declared ล่วงหน้า
- **[R2-M-4] CONTAMINATION ประกาศ explicit (แบบ AD-1 §9):** card นี้ถูกเปิดเพราะ**เห็น fold2016 +0.31 แล้ว** (selection-prior จาก CLAIM-0020 look) · mechanism guards ที่มี: (W,h) freeze จาก synthetic-y ไม่เห็น real · re-fire null จัดการ within-run selection · budget charge เต็ม +1 · **แต่ selection-prior ระดับ card ลบไม่ได้ — ประกาศไว้อ่านคู่ผลเสมอ** (ถ้า SIGNAL ที่ fold2016 = confirm บน data ที่เลือก card จากมันเอง → promotion ต้องมี out-of-selection evidence เพิ่ม)

## 8. PREDICTION — ยังไม่เขียน
เขียนหลัง design freeze · อยู่ใน commit ที่วินสั่งก่อน STAGE-B · ทิศที่จะประกาศ: **คาด no-fire/KILL** · รูปแบบ: **1 claim one-sided-aware** — "fires ≤ envelope" (STAGE-B) หรือถ้าถึง STAGE-C: "p ≥ α*_dec" — **ห้ามผูก point-anchor แบบ two-way** [บทเรียน §8-misspec CLAIM-0020: p≥α bound แค่ upper tail]

## Changelog
**v1 (07-20):** draft แรกหลังวินเลือก detector-card — โครง 3-STAGE · CUSUM lagged-local ref [S2] · re-fire null [S3] · FROZEN_DET เลขตรึง [S4] · mask/embargo [S5] · contamination guards (no-hardcode-break · no-tune-to-cells) · O3 estimation-first + บทเรียน CLAIM-0020 ฝัง (symbolic anchor · one-sided prediction) · value-scope ประกาศ (แม้ SIGNAL = single-fold-era n=1 · promotion path แคบ)
**Engineer R1 (07-20 · instance ใหม่): PASS-with-changes — FB 4 + M 4:** FB-1 Claude cite ข้าม scale ("0.967 ≥ ทุกกรณี" — source = @block · lethality sub-year — class เดียวกับบทเรียน CLAIM-0020 ที่เพิ่งบันทึก) · FB-2 pass-gate "ตรึงจากเลข calibration รอบแรก" = self-grading vector · FB-3 ไม่ reconcile กับ AD-2 mechanism + ชี้คุณค่าจริง: re-fire null = เครื่องมือแยก contiguity-vs-regime · FB-4 ไม่มี segment-floor (estimator degeneracy) · M-1 timing-probe · M-2 STAGE-B statistic · M-3 sanity per-null-shape · M-4 contamination explicit · citation audit ผ่านหมด
**Claude-Verify R1→R2 (07-20):** CONFIRMED ทั้งหมด + refine 3: **FB-2 fix ของ Engineer เอง circular** (effect เป้า = fold2016 observed → post-hoc) → **convention-norm bar** (80%/5% @ρ0.10 — external ล้วน) · FB-3 wording precise (AD-2 falsify **mean-proximity channel** — regime untested) · FB-4 floor=100 · **Engineer R2 รับทั้ง 3 ("Claude ถูก — ผมพลาด 2 ใน 3") + จับกลับ:** FB-1 ห้าม upgrade sign-agreement → defined-rate · + value-adds: asymmetric tolerance (late≤W/early≤b — cost-based) · non-vacuous contiguity assert (real-X preserve — code-verified) · floor justification จริง (**measured: fold2016 post-flip = 166 = 8.7 obs/param** · 190/300 exclude fold2016 · ห้าม tune) · purity-vs-quantity = เหตุ expect-KILL เพิ่ม
**Implement + detcal รอบแรก (07-20):** `ad3_card.py` สร้าง · regress identity PASS · **detcal v2-spec: ไม่มี W ผ่าน bar → KILL ที่ STAGE-A ฟรี** — W=100: NOISE FPR 55.8% · det 20.8% · W=150: NOISE 84.2% · det 32.5%
**Engineer R4 + Claude-Verify (07-20): KILL valid-in-conclusion · evidence confounded → corrected:** Engineer ตั้งสมมติฐาน "premature จาก implementation" แล้ว**วัดหักล้างตัวเอง** — D1 zero-allowance CUSUM (ไม่ใช่ Page standard → NOISE random-walk) · D2 h calibrate บน STABLE (null ง่ายสุด ไม่ใช่ binding) · D3 envelope ผิด null · D4 regress แตะ real object · **corrected probe (Page k-grid × NOISE-binding h): FPR คุมได้ ≤5% แต่ detection ยุบเหลือ ≤2.5% ทุก cell** (เลข 20-33% เดิม = noise-fire บังเอิญใกล้ truth) · **Claude-Verify reproduce ตารางเต็ม 10 cells ตรงเป๊ะ** → root = **SNR wall**: signal-norm ρ√nsig=0.20 < noise-norm √(NF/W)=0.44@W100 · W≥300 → windows 2-4 = degenerate → ไม่มี W ที่ SNR พอ ∧ windows พอพร้อมกัน (FB-1 "lethality sub-year" ยืนด้วยเลข) · **มติ: แก้ D1-D4 → re-run detcal → record KILL บนเลขสะอาด · fold2016 = ยังไม่ถูก adjudicate (ห้าม conflate) · ไม่ charge budget (real d ไม่เคยแตะ)** จับ gap ใหม่ **zero-dominated re-fire null** (per-fold FPR 5% → ~77% ของ null draws = 0 เป๊ะ → mixture null · B ต้อง size จาก measured P(fire|null) · zero-fraction emit + sanity per-shape · fallback bit-identical obs/null · STAGE-C = magnitude ไม่ใช่ independent confirmation) · **Claude-Verify เพิ่ม: pin หน่วย FPR = per-fold** (หน่วยกำหนด arithmetic — 25 vs 113 live draws) · v2 = FB-1..4 + M-1..4 + value-adds + zero-mass ครบทุก §
