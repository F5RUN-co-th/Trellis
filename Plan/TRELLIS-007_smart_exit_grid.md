# TRELLIS-007 — Smart-Exit Grid (AGS v3)

**วันที่:** 2026-07-03 (v2 หลัง Engineer review + Claude Verify)
**สถานะ:** รอวินอนุมัติ implement
**Scope anchor:** grid v2 ตายด้วย deep-basket run-over (−$3,318, 8/8 windows) + fade ซ้ำทิศเดิมทันทีหลังโดน run-over (71%)
**Baseline เทียบ:** v2.01 — HALT −25% ทุก window ใน 4–23 วัน

---

## 0. ปรัชญานำ (วินนิยาม 2026-07-03 — Aggressive Grid Scalper)

> **เข้าเทรดเมื่อโอกาสสูง (Aggressive Entry) · ทำกำไรสั้นแล้วออก (Scalping First) · Grid เป็นเครื่องมือบริหารตำแหน่ง ไม่ใช่เครื่องมือไล่แก้ขาดทุน · Capital Protection อยู่เหนือการทำกำไรเสมอ**

**คำชี้ขาดของวิน:** ❌ ไม่มี Hedge Recovery · ✅ คง flat lot · ✅ entry จาก data เท่านั้น (ไม่ใช้ ICT)

---

## 1. Evidence base (ทุกตัวเลขจาก script — ตรวจซ้ำแล้ว 2 ชั้น: Claude + Engineer อิสระ)

- **ข้อมูล:** `Common\Files\Trellis_diag_770001_{66q1..67q4}.csv` (1,576 baskets) · เครื่องมือ `Scripts/diag_analyze.py` + pooled scripts
- v2 baseline: winrate 75.6% · avgW +$1.90 / avgL −$10.81 · churn ~22 baskets/วัน (~58 orders/วัน) · spread cost ~**$20.7/วัน** (median spread 36 pts, 1 spread/round-trip)

| Fact | ตัวเลข | สถานะ verify |
|---|---|---|
| F1: levels 1–2 กำไร +$1,488.8 (n=965) — บวก 8/8 windows | ✅ 2 ชั้น |
| F3: levels ≥5 = −$3,317.9 (n=205, 13%) — ลบหนัก 8/8 | ✅ 2 ชั้น |
| F4: time-stop −$2,208 แยกชั้น: deep −$1,555 · mid −$595 · shallow −$58 → ก้อนใหญ่อยู่ที่ deep | ✅ 2 ชั้น |
| F5: hard-stop tail −$1,601 (n=34, avg −$47) — hard-stop คือ basket ลึก (avg **8.47** levels pooled) | ✅ 2 ชั้น (v2 เคยใช้ค่า 66q1 เดี่ยว 7.5 — แก้แล้ว) |
| **F10: หลัง basket ลึกจบ → basket ถัดไปเข้า"ทิศเดิม" 142/200 = 71%** · gap close→open: ทุกคู่ 31% ≤1 นาที (median 6.1) · เฉพาะหลัง deep **42% ≤1 นาที (median 4.3)** | ✅ 2 ชั้น (ระบุนิยามครบ) |
| **F13: same-dir follow-on ตัวถัดไปทันที (n=142): sum −$116.6, เป็น winner 75%** → มูลค่า marginal ของ G1 วัดตรงจาก v2-data ไม่ได้ (ไม่มี E1 ใน data) — **ตัดสิน G1 จาก A/B เท่านั้น ห้ามเครดิต deep-tail dollars ที่เป็นของ E1** | ✅ 2 ชั้น |
| **F14: E1 forfeit — deep winners ที่จะถูกตัดทิ้ง = 47 ตัว (+$102.9) vs deep losers 158 ตัว (−$3,420.9)** → โครงสร้าง E1 ดีกว่า E2 ชัด (E2 forfeit $472) | ✅ 2 ชั้น |
| **F11: est loss ถ้าตัดที่ trigger fill-5 ≈ $10.9/ครั้ง → ถ้า re-entry chain ทำให้โดนตัด ≥1.48 ครั้ง/trend = ประโยชน์ E1 หายหมด** → E1 เดี่ยวๆ ไม่พอ ต้องมี guard | ✅ 2 ชั้น |
| **F7-แก้ไข: ER gate "ถอดไม่ได้"** — วิเคราะห์ด้วย AVG (ไม่ใช่ SUM): ER 0.30–0.35 บวก (+$0.96/basket, บวก 6/7 windows แต่ n=31) และ **ไม่มีข้อมูล ER ≥ 0.35 เลย (gate บล็อกหมด)** → ห้ามสรุปว่า gate ไร้ผล | ✅ 2 ชั้น |
| F12: E2 (depth-scaled TP) = สุทธิ ≈ **−$16.7** (forfeit winner จริง −$471.9 vs rescue upper-bound +$455.2) — ไม่ใช่การปรับปรุง | ✅ 2 ชั้น |
| F8: ไม่มี entry feature ปัจจุบันทำนาย deep basket ได้ (P(deep) 5–17%) | ✅ |
| F9: บทเรียน — สัญญาณจาก window เดียว/bucket n เล็ก ห้ามใช้ design | ✅ |

---

## 2. การเปลี่ยนแปลง Phase A (เหลือ 1 คู่ที่แยกไม่ได้ + 1 execution fix)

### E1 — Depth-Falsification Exit (โจมตี F3+F4-deep+F5)
- **Trigger:** ก่อนเปิดไม้ที่ `InpDepthFalsify` (default **5**) — ราคาแตะระดับ fill ถัดไปแล้ว `g_levels+1 >= InpDepthFalsify` → **ไม่เปิดไม้ → ปิดทั้ง basket ทันที** reason `depth-falsify`
- Basket cap จริง = `InpDepthFalsify − 1` = 4 ไม้ (นิยามชัดกัน off-by-one — Engineer F-6)
- **ลำดับใน ManageGrid (บังคับ):** time-stop → fill loop (มี depth guard **ก่อน** Buy/Sell) → basket-TP check
- Gap หลาย spacing ใน tick เดียว: loop จะเติมถึงไม้ที่ 4 แล้วชน guard ที่ไม้ 5 → ตัด — cap ไม่ทะลุ
- **หลัง trigger ต้อง `return` ทันที** — ห้าม fall-through ไป TP check (แม้ `RequestClose` จะ no-op เองเพราะ state guard ก็ห้ามพึ่งความบังเอิญ) [review2 MED-6]

### G1 — Same-Direction Re-entry Guard (คู่บังคับของ E1 — โจมตี F10/F11)
- หลัง basket จบด้วย `depth-falsify` **หรือ `hard-stop`** (ลายเซ็น run-over เดียวกัน — F5): **บล็อก entry ทิศเดิม** จน fade thesis ถูก reset
- **Unblock spec (sign ชัดเจน — review2 HIGH-2):** ประเมิน**ทุก new bar M1 (closed bar, shift 1) โดยไม่ผูกกับการยิง signal** แล้ว latch:
  - blocked **BUY** (fade-dip โดน downtrend, close อยู่ใต้ EMA) → ปลดเมื่อ `close[1] > ema[1]`
  - blocked **SELL** (fade-rip โดน uptrend, close อยู่เหนือ EMA) → ปลดเมื่อ `close[1] < ema[1]`
  - **Sideway-unlock = intended:** ถ้า trend จบแบบ sideway EMA50 จะไหลมาหาราคาใน ~50 bars แล้ว close ข้ามเอง → guard ไม่ค้างถาวร (reset โดยไม่ต้องรอ full reversal)
- **State ownership (review2 HIGH-1):** `m_blocked_dir` เป็น field ใน `CTrellisRisk` — เข้า `PersistState()/LoadState()` ใต้ prefix `TRL_<sym>_<magic>_` → ได้ tester-clear ต่อ pass ฟรีจาก `GlobalVariablesDeleteAll` เดิม (`TrellisRisk.mqh` Init) ไม่มี GV prefix ใหม่ ไม่มี clearing logic ซ้ำ · accessor: `BlockedDir()/SetBlock()/ClearBlock()`
- **Arm ordering (review2 HIGH-3):** arm ในบล็อก transition detection ของ `OnTick` (จุดเดียวกับ diag OnClose) — capture ทิศ**ก่อน** reset `g_dir=0` · อยู่**ก่อน** dispatch ไป TryEntry เสมอ → re-entry bar ถัดไปไม่มีทางหลุด guard · reason จาก `CloseReason()` · ไม่ arm บน terminal HALT (ไม่มี entry ต่ออยู่แล้ว)
- **Single-slot = overwrite:** block ได้ทีละทิศ event ใหม่เขียนทับ (one-at-a-time basket, deep สลับทิศติดกันพบน้อย — นิยามไว้กัน ambiguity)
- ทิศตรงข้ามเข้าได้ปกติ · `InpUseReentryGuard=false` ปิดได้เพื่อ A/B
- **เหตุผล root-cause:** depth-falsify = ประกาศว่า "MR thesis ทิศนี้ผิด trend กำลังวิ่ง" → เข้า fade ทิศเดิมซ้ำทันที (71% ของกรณี) = ทำซ้ำ thesis ที่เพิ่งถูกหักล้าง — นี่คือต้นเหตุ thousand-cuts ไม่ใช่อาการ

### X1 — Same-tick Close (Engineer F-4 + Claude refinement)
- `CTrellisRisk::RequestClose()` เรียก `ClosingStep()` ต่อทันทีหลัง `EnterClosing()` — **pattern เดียวกับ kill ภายใน** (`TrellisRisk.mqh:269,277,291,293`)
- Code path เดียว ทุก exit (TP/time-stop/depth-falsify) ได้ execution เดียวกัน — ไม่ทำ special-case เฉพาะ E1 (no duplicate)
- ประกาศตรง: ข้อนี้ขยับ execution ของ baseline exits เดิมด้วย ~1 tick (ดีขึ้นสม่ำเสมอ) — บันทึกไว้ตอน compare

### ❌ ยกเลิกจาก v1 (ผล Engineer review + Claude Verify)
- **E2 depth-scaled TP** — F12: สุทธิ −$16.7 ทำลายกำไรจริง $472 แลก rescue ทฤษฎี $455 · เก็บเป็น candidate A/B หลัง Phase A ถ้าข้อมูลใหม่ชี้
- **E3 ถอด ER gate** — F7-แก้ไข: sum-vs-avg artifact + ไม่มีข้อมูล ≥0.35 · **gate คงเดิม ON @0.35 ไม่ tune** (ไม่ A/B threshold รอบนี้ — กัน curve-fit ตาม F9)

### สิ่งที่ไม่แตะ
Risk armor ทุกตัว · ER gate (ON เดิม) · entry logic เดิม · ATR spacing · flat lot 0.01 · one-at-a-time · M1 · TRELLIS-DIAG (เปิดต่อ — reason `depth-falsify` เข้า log อัตโนมัติ)

---

## 3. Phase B — Entry Brain (แยกเป็น TRELLIS-008 — ไม่อยู่ในรอบนี้)
F8: ต้องขยาย diag log เก็บ feature ใหม่ (ตำแหน่งใน range, ระยะจาก swing, แท่งทิศเดียวติดกัน, session) → วิเคราะห์ P(deep|feature) → มีตัวแยกจริงค่อยเสนอ

---

## 4. Parameters

| Input | Default | หมายเหตุ |
|---|---|---|
| `InpDepthFalsify` | 5 | plateau check 4/5/6 — ต้อง robust ทั้งช่วง ไม่เลือกยอด |
| `InpUseReentryGuard` | true | A/B off ได้เพื่อพิสูจน์ผลของ G1 แยกจาก E1 |
| เดิมทั้งหมด | คงค่า v2 | ไม่ tune |

---

## 5. Validation plan (ปรับตาม Engineer F-5)

1. **Mechanism check:** 8 windows เดิม (tag `v3_66q1`…) เทียบ v2 ทุก metric + **metric ใหม่ที่จับ thousand-cuts:**
   - จำนวน + **distribution ของ `depth-falsify` realized loss** (ไม่ใช่แค่ count)
   - **same-dir re-entry rate หลัง falsify** — baseline 71% ต้องลดชัด
   - baskets/วัน · orders/วัน · spread cost/วัน (สูตร: orders × spread$ ต่อ round-trip — **ไม่คูณ 2**)
   - **"deep-tail dollars ไม่ย้ายถัง":** Σ(depth-falsify losses + chain) ต้องน้อยกว่า −$3,318 เดิมอย่างมีนัย — แทนเกณฑ์เดิม "bucket ≥5 หด" ที่ผ่านโดย construction
2. **เกณฑ์ผ่าน Phase A (ปรับตาม review2 MED-4 — กัน false-reject + curve-fit pressure):**
   (a) ไม่ HALT ใน window ≥6/8 · (b) **pooled net ดีขึ้น + ≥6/8 windows ดีขึ้น + worst window ไม่แย่ลงกว่า v2 เกิน 10%** (ไม่เรียก 8/8 monotone) · (c) deep-tail dollars ตามนิยามใหม่ · (d) churn ไม่เพิ่ม
   **Metric บังคับเพิ่ม:** (i) forfeited-winner ของ E1 — count/$ (baseline คาด ~47 ตัว / +$102.9 — F14) (ii) G1 blocked-basket count + % would-have-winner (baseline follow-on: 75% winner, sum −$116.6 — F13) (iii) peak-equity-DD distribution เทียบ v2 (ไม่ใช่แค่ "ไม่ HALT")
3. **A/B G1 (บังคับ):** รัน `InpUseReentryGuard=false` อย่างน้อย 2 windows — **ตัดสิน G1 จากส่วนต่าง (E1+G1) − (E1-only) เท่านั้น** ห้ามเครดิต deep-tail dollars ของ E1 ให้ G1 (F13)
   · Measurement เสริม (review2 MED-5): log `bars จน close ข้าม EMA50 กลับ` หลัง depth-falsify (วัด block duration จริง — เพิ่มใน diag ได้ตอน implement)
4. **สถิติซื่อสัตย์:** 8 windows = in-sample (ใช้ design แล้ว) · **True OOS = ปี 2565 (2022) + 2568 (2025) ห้ามแตะจน design freeze** · ตัดสิน edge จาก OOS เท่านั้น
5. ตัวเลขจาก script เท่านั้น — LLM ไม่พิมพ์ตัวเลขเอง

---

## 6. ความเสี่ยง / ข้อจำกัด

- Phase A = **damage-limitation ที่ยังพิสูจน์ sign ไม่ได้** (Engineer bottom-line — ยอมรับตรงๆ): entry ยัง fade ทุก deviation · ถ้า Phase A ยังลบ → ไป Phase B (entry) ไม่ tune param วน
- est cut-loss $10.9 เป็นค่ากลาง — trend แรง/gap จะแย่กว่า (multi-fill ใน tick เดียว + slippage) · X1 ลด deferral ได้ 1 tick แต่ไม่ได้ลบ gap risk (Doctrine #6)
- G1 อาจ block โอกาสจริงบางส่วน (fade ที่สองที่ would-have-won) — วัดได้จาก A/B ข้อ 5.3
- Churn ~22 baskets/วัน + cost ~$20.7/วัน ยังสูง — Phase A ไม่แก้ข้อนี้ตรงๆ (เป็นงาน entry/Phase B)

## 7. Out-of-scope issues (log แยก ไม่ลากเข้าแผนนี้)
- **Weekend gap:** ไม่มี flat-before-weekend guard — basket ค้างข้าม weekend เจอ Monday gap ทะลุ hard-stop ได้ (Doctrine #6) · E1 cap=4 ลด exposure ลงมากแล้ว · pre-existing ตั้งแต่ v1 (review2 LOW-9) → บันทึกใน STATUS
- **Diag last-tick label:** ถ้า tester จบ tick เดียวกับ kill → row ติด `test-end` แทน reason จริง (cosmetic, pre-existing ทุก same-tick kill)
- `Scripts/deploy.sh` ก๊อปแค่ .ex5 (บันทึกไว้แล้วใน STATUS)

## Changelog
- **v3 (2026-07-03):** ผ่าน Engineer review รอบ 2 (อิสระ, fresh context) — verdict PASS with mandatory changes · เติม HIGH-1 (G1 state ใน CTrellisRisk/prefix TRL_), HIGH-2 (unblock sign spec + sideway-unlock intended), HIGH-3 (arm ordering + single-slot), MED-4 (เกณฑ์ pooled+6/8+worst-floor + forfeited-winner/G1-credit metrics), MED-6 (explicit return) · แก้เลข LOW-7 (hard-stop 8.47 pooled; gap แยกนิยาม) · เพิ่ม F13/F14 · §7 out-of-scope log
- **v2 (2026-07-03):** หลัง adversarial Engineer review + Claude Verify (ตัวเลขตรวจ 2 ชั้นอิสระ) — ตัด E2 (F12) + ยกเลิกการถอด ER gate (F7-แก้ไข: sum/avg artifact + zero-data ≥0.35) · เพิ่ม G1 re-entry guard (F10/F11) + X1 same-tick close · validation เพิ่ม chain metrics + แก้สูตร spread cost (Engineer คูณ 2 ซ้ำ — ที่ถูก ~$20.7/วัน)
- **v1 (2026-07-03):** ฉบับแรกจาก diagnostic 8-window
