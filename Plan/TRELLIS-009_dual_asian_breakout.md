# TRELLIS-009 — Trellis v4 "Dual Asian-Range Breakout" (trend continuation, M1)

**วันที่:** 2026-07-03 (night session — วินมอบ full autonomy 04:29, deadline 07:00)
**สถานะ:** IMPLEMENTED v4.00 + deployed — รอ MT5 real-tick confirm + demo forward
**แทนที่:** สถาปัตยกรรม grid-scalp (TRELLIS-001..007) ซึ่งถูก **falsify เชิงประจักษ์ครบวงจร**

---

## 1. ทำไมถึงมาที่นี่ (บันทึกการ falsify — ห้ามเดินซ้ำ)

| สมมติฐาน | ผลพิสูจน์ | หลักฐาน |
|---|---|---|
| MR grid scalp (v1.2–v3) | ตาย — HALT ทุก config | 18 MT5 runs, 4,070 baskets |
| Exit engineering กู้ MR ได้ | ตาย — เงินย้ายถัง ไม่หาย (1.50× cuts) | v3 A/B 10 runs |
| Entry k=0 กู้ scalp ได้ | ตาย — 16k signals จริง, gross≈0, cost กิน | mr_sim.py 48 configs |
| MR มี edge ที่ horizon ใดๆ บน M1 | ตาย — ทุก bucket แพ้ cost hurdle $0.40 | edge_screen.py 703k bars |
| **Trend continuation หลัง Asian BO** | **รอด — เดียวที่ข้าม cost + stable** | edge_screen2 + asian_bo_sim |

**บทเรียนแกน:** cost $0.40/round-trip บังคับให้เล่นเกม move ใหญ่ (หลาย $) — scalp TP เล็กบน M1 ไม่มีทางคุ้มโครงสร้าง

## 2. ระบบ (ทุกค่าคงที่มาจาก sim plateau — ไม่ใช่ optimize ยอดแหลม)

- **LONG:** M1 close แรกของวันทะลุ **Asian High** (01:00–07:59 server) ในหน้าต่าง 08:00–19:59 + `close > EMA(2880)` + `slope EMA 1440 bars > +0.1% ของราคา`
- **SHORT:** mirror สมบูรณ์ (Asian Low + regime ลง) — **ศูนย์ parameter ใหม่**
- **Stop:** ขอบ Asian ฝั่งตรงข้าม, cap 1×R จาก entry (R = ความสูง Asian range) — **SL จริงบน server** (กัน gap ดีกว่า virtual stop ของ v2/v3)
- **Trail:** กำไร ≥ 1×R → SL = best close ∓ 0.75×R (เลื่อนต่อ bar ปิด)
- **EOD:** ปิด 23:00 server ทุกวัน → **ไม่มีไม้ข้ามคืน/ข้าม weekend โดยโครงสร้าง**
- 1 เทรด/วัน · single position · flat 0.01 lot · risk armor v2 ทั้งชุดคง (backstop)

## 3. หลักฐาน (Scripts/asian_bo_sim.py — pessimistic fills: stop-first, gap-at-open, spread จริง/บาร์ + slip)

| ช่วง | บทบาท | Net (0.01 lot) | หมายเหตุ |
|---|---|---|---|
| 2023–24 | IS (design) | +$155 dual / +$213 long | plateau กว้าง CAP1.0×A0.75-1.0×D0.75 |
| 2025–26 | **OOS แท้ (แตะครั้งเดียว)** | **+$431 dual / +$851 long** | PF 1.57, ทุก quarter บวก, ทน cost ×1.5 |
| 2022 | OOS → กลายเป็น design ของ slope filter | +$8 dual | จาก −160 (ก่อน filter+mirror) |
| 2012–2020 | validation (9 ปี) | +$40 dual | จาก −195 long-only · worst 2012 −146 |
| 2011 | validation | +$87 dual | PF 1.12 |
| **รวม ~15.5 ปี** | | **≈ +$722** | **~+4.7%/ปี บน $1,000 fix lot · ไม่มีปีหายนะ** |

## 4. ⚠️ Integrity disclosure (อ่านก่อนเชื่อ)

1. **Dual (short mirror) ไม่มี holdout เหลือ** — ตัดสินใจเพิ่ม short หลังเห็นข้อมูลทุกปี · ที่ค้ำ: mirror ไม่มี param ใหม่แม้แต่ตัวเดียว + ยืน 15 ปี · **ด่านจริง = MT5 real-tick + demo forward**
2. ระบบเป็น **regime-conditional**: จ่ายหนักปี trend (2025 +674 long) เสมอตัวปี flat — ไม่ใช่เครื่องพิมพ์เงินรายเดือน ต้องมองรายปี
3. Sim = bar-level M1 (ไม่ใช่ tick) — pessimistic rules ชดเชย แต่ MT5 99% tick คือ authority · slope threshold 0.1% เลือกจาก 2021–24 (relative จึง scale ข้ามยุคได้)
4. เลข 2011–2020 มาจาก spread column ของ data เก่า (avg 31–46pt — สมจริง)
5. **Window sensitivity ผ่าน:** เลื่อน Asian window ±1 ชม. (00–07/01–08/02–09) × 3 ยุค = **บวกทั้ง 9 ช่อง** (+34..+852) — edge ไม่ knife-edge บน timezone/DST
6. **Param sensitivity (2012–2020, คนละยุคกับ IS):** 10/14 ช่องรอบ base เป็นบวก, base ไม่ใช่ peak (D=1.0 +160, SLOPE=0.0005 +242 ดีกว่า) → ไม่ใช่ spike-fit · แกนไว: CAPR ≥1.25 ติดลบ (−60/−84) — cap stop ที่ 1×R หรือแน่นกว่า สำคัญ · decade เก่าอ่อนทุก config = edge เป็นของยุคปัจจุบันจริง
7. **Bootstrap 10k (2011–2026, 2,127 เทรด):** mean +$725 · **CI95 = [−518, +2008] · P(รวม≤0) = 12.9%** — ยังไม่ statistically significant · นี่คือเหตุที่ต้อง walk-forward + demo forward ก่อนเรียกว่า edge

## 5. Validation ถัดไป (วินรัน — เบา: 2 รอบพอ)

1. **MT5 GUI:** XAUUSD_BT · **M1** · real-tick · $1000 · v4 defaults → รอบ 1: `2023.01.01–2024.12.31` (เทียบ sim +155) · รอบ 2: `2025.01.01–สุดข้อมูล` (เทียบ +431 scale)
2. เกณฑ์: ทิศทาง/ขนาดสอดคล้อง sim (±ครึ่งหนึ่ง ยอมรับได้ — fills ต่าง) · exit-reason กระจาย sl-exit/eod สมเหตุผล · **ห้าม tune ถ้าเพี้ยน — diagnose ก่อน**
3. ผ่าน → demo forward ≥ 1 เดือน ก่อนคุยเงินจริง

## 6. Engineer adversarial review (05:00) + Claude Verify — บันทึกตรงไปตรงมา

**Verdict Engineer: (A) Evidence = NO-GO ในฐานะ "edge ที่พิสูจน์แล้ว" · (B) EA = GO-with-fixes**

| Finding | Verify | การจัดการ |
|---|---|---|
| [HIGH] script ของ logic จริง (slope+mirror) ไม่อยู่ใน repo | ✅ จริง | **แก้แล้ว:** `Scripts/dual_asian_sim.py` (canonical) — reproduce ทุกตัวเลขตรง |
| [HIGH] dual ไม่มี OOS เหลือ + peek-then-patch 2 ครั้ง (slope หลังเห็น 2022, mirror หลังเห็น 2012-20) + กำไรกระจุก 2023-26 (+586 จาก +733) | ✅ จริง | ยอมรับเต็ม: **bootstrap 10k: CI95=[−518,+2008], P(รวม≤0)=12.9% — ยังไม่ significant** · walk-forward แบบ anchored = งานถัดไปที่บังคับก่อนเชื่อว่าเป็น edge |
| [MED] "2011-2020" จริงๆ คือ 2012-2020 (2011=warmup) | ✅ จริง | แก้ label แล้ว · รัน 2011 แยก (Feb+): +$99 PF 1.14 |
| [MED→HIGH] timezone/DST ระหว่าง CSV กับ tester ไม่ verify | **แย้งบางส่วน:** calibration 1,576 จุด (ม.ค.+ก.ค. 2023-24 = ทั้ง winter/summer) ตรง 100% ระดับนาที → CSV clock = tester clock ในช่วง confirm run แน่นอน · 2011-2020 ยังไม่ verify (sim-only, รับความเสี่ยงไว้ใน CI แล้ว) |
| [MED] B2 range-tracking โดน spread gate กิน / B3 EOD ไม่มี catch-up (เสี่ยงค้างข้าม weekend) / B4 strategy state ไม่ persist | ✅ จริงทั้ง 3 | **แก้ครบ + compile 0/0 deploy 05:00** — EOD catch-up ทำให้ flat-before-weekend เป็นโครงสร้าง |
| [LOW] cost stress ไม่คูณ stop-slip / spread gate คนละ object กับ sim / diag fields repurposed | ✅ จริง | canonical script คูณ stop-slip แล้ว · อีก 2 ข้อบันทึกไว้ (ไม่ block) |
| Risk: hard-stop 5% ชนะ structural SL กรณี R>$50 — precedence ถูก · risk layer ไม่ถูก exercise ที่ 0.01 lot | ✅ | ห้ามอ่าน "ไม่ trigger" = "validated" — ต้อง stress แยกก่อนขยาย lot |

**การอ่านผลที่ถูกต้อง (สำคัญที่สุด):** MT5 confirm run = **code-fidelity check** (EA ตรง sim ไหม) — **ไม่ใช่** หลักฐาน edge (data ชุดเดียวกับที่ design = circular) · edge จริงต้องมาจาก (1) anchored walk-forward (2) demo forward เท่านั้น

## 7. ★ Anchored Walk-Forward (Scripts/walk_forward.py — หลักฐานชี้ขาด, 05:15)

Protocol ประกาศก่อนรัน: grid 24 configs · ทุกปี 2015–2026 เลือก config จาก trailing net บน 2012..Y-1 (expanding) · เทรดปี Y ที่ไม่เคยเห็น

- **WF OOS 12 ปี: +$785.6 · PF 1.11 · n=1,810 · ปีบวก 6/12 แต่ positive skew ชัด (แพ้เล็ก −11..−67, ชนะใหญ่ +65..+238) · ไม่มีปีหายนะ**
- Selection เสถียร: เลือก `CAP1.0/D1.0/SLOPE0.0005/dual` **11/12 ปี** → กระบวนการเชิงกลเลือกดีกว่ามือ (+786 vs fix-base +738 vs median-config +497)
- bootstrap WF-OOS: CI95=[−449,+2040], **P(≤0)=10.4%** — ยังไม่ขาด 95% → ด่านสุดท้าย = demo forward
- **EA อัปเดตเป็น WF-selected config แล้ว** (`C_TRAIL_DIST_R=1.0`, `C_SLOPE_MIN_FRAC=0.0005`) — compile 0/0, deployed
- ความคาดหวังใหม่สำหรับ MT5 confirm: 2023–24 ≈ **+$137 / ~337 เทรด** (2023 −1.7, 2024 +138.3) · 2025–26 ≈ **+$437 / ~175 เทรด**

## 8. MT5 confirm รอบแรก + บั๊ก weekend ที่ tester จับได้ (09:49–10:03)

- **v4_2324: PASS** — MT5 n=340/net +$154.7 vs sim n=337/+$136.6 (Δ+13%) รายปีตรง pattern → **EA ตรง sim ยืนยัน**
- **v4_2526: จับบั๊กจริงได้** — ไม้ SHORT เปิดศุกร์ 21 มี.ค. 2025 19:24 · ตลาดปิดเร็ว (ไม่มี tick 23:xx) → EOD ไม่ fire → ถือข้าม weekend → ตลาดเปิดอาทิตย์ 22:00 order โดน reject 10 ticks ใน 4 วิ → **escalate HALT ตาย 41 เทรด** · sim ผิดแบบเดียวกัน (ถือ weekend) จึงตรวจไม่เจอ offline — คุณค่าของชั้น tester
- **Fix (root cause):** ศุกร์ EOD = 20:00 (ก่อน earliest close 20:xx ที่พบใน data 2012–24 — flat ก่อน weekend เชิงโครงสร้าง) + `InpMaxCloseRetry` 10→100 + sim mirror กฎเดียวกัน
- **ผล rerun ทั้งระบบ:** 15.5 ปี +$694 · **WF ดีขึ้น: +$876, P(≤0)=7.6%** (weekend holds = ความเสี่ยงที่ไม่จ่าย) · WF ยังเลือก config เดิม → deploy 10:03
- **ความคาดหวังใหม่ (config ที่ deploy):** 2023–24 ≈ **+$176 / ~338 เทรด** · 2025–26 ≈ **+$367 / ~175 เทรด**

## 9. ★★ TRUE HOLDOUT + การค้นพบ timezone (10:30–11:00 — จากคำถามของวินเรื่อง data ไม่ update)

- Data Dukascopy จบ 23 ก.พ. 2026 (server เขา 503 อยู่) → วินลาก `ExportM1` บน chart **XAUUSDm (Exness live feed)** ได้ 100k bars (23 มี.ค.–3 ก.ค., เพดาน Max-bars terminal)
- **ค้นพบ CRITICAL:** Exness live = **UTC+0** แต่ XAUUSD_BT/CSV = **UTC+3** — ถ้า demo โดยไม่แก้ session จะเพี้ยน 3 ชม. = คนละกลยุทธ์! → **fix: input `InpHourShift`** (tester=0, Exness live=**3**) compile 0/0 deploy แล้ว
- **★ HOLDOUT จริง 26 มี.ค.–3 ก.ค. 2026** (ไม่มีการตัดสินใจใดเคยเห็น + คนละ data source + ทอง**ลง** 4275→4178): config ที่ deploy ได้ **+$565.0 · PF 2.34 · wr 59.5% · 37 เทรด · บวกทุกเดือนเต็ม** (เม.ย. +276, พ.ค. +133, มิ.ย. +101)
- **SHORT mirror พิสูจน์ตัวเอง:** dual +565 vs long-only +205 → shorts +~$360 ในตลาดขาลง — ตอบ finding ใหญ่สุดของ Engineer (mirror ถูกเพิ่มหลังเห็นข้อมูล) ด้วยข้อมูลที่ไม่เคยเห็นจริง
- Caveat ที่คงอยู่: n=37 เล็ก · ยุคmédio-vol สูง (R ใหญ่ → $/เทรดสูงกว่าค่าเฉลี่ย 15 ปีมาก) · single-source ไม่มี overlap cross-check (Max-bars จำกัด — ขอ re-export หลังเพิ่ม Max bars ได้)
- **Pre-demo checklist ใหม่:** ตั้ง `InpHourShift=3` บน Exness เสมอ · ตรวจ Friday-close ของ live คือ 20:59 UTC+0 = สอดคล้อง C_EOD_FRI หลัง shift ✓

## 10. ★★★ FULL HOLDOUT + DST proof (11:00–11:20 — หลังวินเพิ่ม Max bars → export เต็ม 1 ก.พ.–3 ก.ค.)

- **Timezone พิสูจน์ด้วยราคา ไม่ใช่อนุมาน:** overlap ก.พ. (2 หมื่น bars) → shift **+2 ชม.** |Δclose| median $0.33 (≈spread) ส่วน +3 คลาด $11 → ประกอบกับโครงสร้างหน้าร้อน (+3) = **offset เลื่อนตาม US DST** (BT-clock = UTC+2 หนาว/+3 ร้อน) — Engineer B1 เตือนถูกเป๊ะ · `InpHourShift` fix ค่าเดียว = ผิด 1 ชม. ~4.5 เดือน/ปี
- **Fix:** `InpHourShift = -1` = **AUTO** (broker UTC+0: คำนวณ 2/3 จากกฎ US DST ใน EA) · tester = 0 เหมือนเดิม · compile 0/0 deploy แล้ว
- **Cross-check สองแหล่งผ่าน:** Exness vs Dukascopy ก.พ. match 93.3% ของ bars, bias −$0.48, |Δ| median $0.33
- **★ FULL HOLDOUT 24 ก.พ.–3 ก.ค. 2026 (DST-aware, config ที่ deploy):** **+$802.5 · PF 2.24 · wr 61.2% · 49 เทรด · maxDD $127 · บวกทุกเดือนเต็ม** (มี.ค. +340, เม.ย. +276, พ.ค. +133, มิ.ย. +101) · ทองขาลงทั้งช่วง → **shorts ทำ +$726** = mirror พิสูจน์ตัวเองสมบูรณ์บนข้อมูล+แหล่งที่ไม่เคยเห็น
- Caveat: n=49 · ยุค vol สูง ($/เทรดสูงกว่า norm 15 ปี) · ความไม่แน่นอน ±1 ชม. ตกค้างบางฤดู (window sensitivity เคยพิสูจน์ว่าบวกทั้ง ±1 ชม. — รับได้ation)

## 11. ⚠️ CORRECTION (2026-07-03 เย็น — ผล TRELLIS-010 Stage 0, supersede §9-§10 บางส่วน)

1. **"US-DST-dependent" ใน §10 = ผิด** — proof เดิมใช้ ก.พ.+ฤดูร้อนซึ่งกฎ US/EU ให้ค่าเท่ากัน แยกไม่ได้ · price-match ที่ shoulder weeks (จุดเดียวที่กฎต่างกัน) พิสูจน์: **BT-clock = EET กฎ EU-DST** (last Sun Mar/Oct) — M1 bar `2025.03.17 00:00` open 2984.28 = raw `2025.03.16 22:00:01 UTC` bid 2984.28 (+2 ขณะ US DST active) · EA แก้เป็น `IsEuDST` แล้ว (compile+deploy 16:06)
2. **HOLDOUT +$802.5 (§10) = คำนวณด้วยกฎ US ที่ผิด + un-scripted** — `Scripts/holdout_exness.py` (commit แล้ว) reproduce เลขเดิมเป๊ะทุกตัวด้วยกฎ US (พิสูจน์ equivalence) · **เลขที่ถูกต้อง (กฎ EU): +$511.8 · PF 1.54 · wr 59.2% · 49 ไม้ · maxDD $320 · บวกทุกเดือน** — ผลต่างทั้งหมดอยู่ที่ 3 สัปดาห์ shoulder มี.ค. 2026 (+340 → +50) · **ห้ามเลือกกฎจาก P&L** — กฎมาจาก ground truth ของ data เท่านั้น (กัน signal-selection)
3. **เลข tester 2025 (−169) / v4d 2026 (+330) = artifact** — tick 2025/26 ใน XAUUSD_BT เป็น UTC+0 ดิบ (import bug) → test คนละ session · รอ re-import + rerun (`v4f_25`, `v4f_2601`) · เลข 2023-24 ไม่กระทบ (clock ถูก, entry align 170/170 กับ sim)
4. Cross-check "Δ median $0.33 ≈ spread" §10 ยังยืน (ราคา ok — ที่ผิดคือการตีความกฎ DST ของ label เวลา)

## Changelog
- v7 (2026-07-03 เย็น): §11 CORRECTION — BT-clock = EU-DST (ไม่ใช่ US) · holdout re-derive +$511.8 PF1.54 (script commit) · tester 2025/26 = clock-bug artifact รอ re-import (TRELLIS-010 Stage 0)
- v6 (2026-07-03 11:20): FULL HOLDOUT +$802.5 PF2.24 · DST-aware AUTO shift · two-source cross-check ผ่าน — **superseded by §11**
- v5 (2026-07-03 11:00): TRUE HOLDOUT +$565 PF2.34 (Exness data, ทองขาลง, shorts นำ) · ค้นพบ+แก้ timezone UTC+0 vs +3 (`InpHourShift`) · ExportM1 tool ใหม่
- v4 (2026-07-03 10:03): MT5 confirm รอบแรก — 2324 PASS / 2526 เจอ weekend-HALT bug → Friday-flat 20:00 + retry 100 + sim mirror → WF ใหม่ +$876 P(≤0)=7.6% → deploy
- v3 (2026-07-03 05:20): Anchored walk-forward ผ่าน (+$786/12ปี OOS, selection เสถียร 11/12) · EA → WF-selected config · วินสั่ง "ดำเนินการ เราต้องพิสูจน์"
- v2 (2026-07-03 05:00): Engineer review + Claude Verify + fixes B2/B3/B4 + canonical script + bootstrap CI + sensitivity (ผลใน §3/§4)
- v1 (2026-07-03): จากผลพิสูจน์กลางคืน — บันทึกทั้ง falsification chain และ evidence
