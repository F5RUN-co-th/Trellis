# Trellis — Implementation Status

**Last updated:** 2026-09-09

> **build/stage เท่านั้น · ไม่มี result-metric** (ผลทั้งหมด → `Plan/TRELLIS-010_LEDGER.md` keyed by Claim-ID) · doctrine/mechanism → `Plan/TRELLIS-010_v3_offensive_reframe.md` · narrative ก่อน reframe → `Plan/TRELLIS-010_ARCHIVE_prereframe.md`
> DoD (CLAUDE.md): commit ที่แตะ experiment → update CLAIM block + FRONTIER · `python Scripts/ledger_check.py` ต้องผ่าน

## Current Stage — TRELLIS-010 v3 Offensive Reframe (research: DIRECTION edge)
- **frame:** หา additive DIRECTION edge (root = engine edge ไม่ใช่ capital) · เป้า: $100 รอด + กำไรมาก + เข้าทุกโอกาส
- **สถานะล่าสุด (09-03):** **Card AD-4 fine-cadence — certify v1 = KNOWN-DEFECT (Engineer execution-review R1/R2 + Claude-Verify ×2: F1 null-retention 27.8% · F2 calib-world ≠ H0 · F7 main stub) → วินอนุมัติ B′: บันทึก v1 (card §6.1/§7.1) · ไม่ pin · ไม่จอง claim · ไม่ charge → design v4 (C1 circular-shift null + triple H0-cal/redundancy-probe/H1 + §1 non-redundant) → design v5 + Alt-G/Alt-2 · deep review 23 รอบ (09-08/09) — **สถานะสด = แถว pipeline AD-4 + Blockers ด้านล่าง** [E13 รอบ 21 · ~~รอ Engineer R7~~ stale]** — แผน = `Plan/TRELLIS-010_card_AD4_fine_cadence.md` · script `Scripts/ad4_card.py` (`FROZEN_CERT` ว่าง) · **pre-approved (Win 09-03): outcome v2 ทั้ง ESTIMATION (7/40) / FREE-KILL (exempt) · rule R6 ตัวอักษรเดิม** · ก่อนหน้า: AD-3 = STAGE-A KILL instrument-infeasible L1 budget-exempt [CLAIM-0021] · budget คง **6/40** family v3 · **adaptive frontier ปิด 3 แกน (smooth AD-1 · recency AD-2 · detector AD-3) — แกน 4 fine-cadence รอ A/B** · residual คง: fold2016 NOT-adjudicated · P≈3.5 underpowered · MONO · aperiodic
- **หมายเหตุ governance (09-03):** session 07-24/25 จบโดยไม่ต่อท้าย Progress Log/STATUS (ละเมิดกฎปิด session `/trellis-010`) → AD-4 อยู่เป็น untracked file 40 วัน · STATUS นี้เคยค้าง "AD-3" + Blockers ค้าง 07-11 → แก้ 09-03 · **Gate 0 clock-fix = ปิดแล้ว 07-04 (Engineer PASS-conditional · Progress Log)** — ไม่ใช่ blocker ของ tester/demo
- **frontier + open/eliminated hypotheses:** LEDGER `## CURRENT FRONTIER`

## Research pipeline (✅ = จบ · ▶ = active — **status word อยู่ LEDGER ที่เดียว** · ดูสด = `/ledger status`)
| ขั้น | pipeline | Claim |
|---|---|---|
| Measurement foundation (edge-bar/opportunity) | ✅ | CLAIM-0001 |
| Opportunity-Unit v4 FROZEN protocol | ✅ | CLAIM-0002 |
| fade (behavior-space) | ✅ | CLAIM-0003 |
| Discovery (additive opportunity) | ▶ | CLAIM-0004 |
| Direction Predictor v0 (linear) | ✅ | CLAIM-0005 |
| Direction Predictor v1 (leaky) | ✅ | CLAIM-0006 |
| in-hand direction gates (trade_R label) | ✅ | CLAIM-0007 |
| spread channel | ✅ | CLAIM-0008 |
| Test B (direction load-bearing at real exit) | ✅ | CLAIM-0009 |
| **direction-at-real-exit** | ✅ | CLAIM-0010 |
| v4 Dual-Asian (carried candidate) | ▶ | CLAIM-0012 |
| opportunity validation + magnitude arm (3-population · day-mean · at-trigger wall · demote +0.66) | ✅ | CLAIM-0004 · CLAIM-0013 · CLAIM-0014 |
| TP-1 tick-price nested-incremental (card 1/40 family v3 · Engineer execution-review + integrity hardening) | ✅ | CLAIM-0015 |
| TP-2 inference completion (card 2/40 · calibration-checked residual-perm · KILL · execution-review PASS) | ✅ | CLAIM-0016 |
| ES-1 event-stream DC multi-scale (card 3/40 · calib S1+S2 · KILL · execution-review PASS) | ✅ | CLAIM-0017 |
| ES-2 tick-DC event-stream (card 4/40 · overlap-audit 100% · calib · KILL · execution-review PASS) | ✅ | CLAIM-0018 |
| AD-1 adaptive/rolling (card 5/40 · STAGE-1 NO-DETECT readout · RFLIP sweep · foreknowledge-disclosed · execution-review PASS) | ✅ | CLAIM-0019 |
| AD-2 rolling-recency (card 6/40 · confirmatory KILL · clean freeze-commit · certify N=200 · estimation-first · execution-review PASS) | ✅ | CLAIM-0020 |
| AD-3 regime-detector (STAGE-A KILL instrument-infeasible · SNR wall · budget-exempt · R4 corrected) | ✅ | CLAIM-0021 |
| AD-4 fine-cadence quarterly expanding refit (design R1-R6 · certify v1 known-defect · **B′ → design v5 + Alt-G global rotation (§0 NORMATIVE N1-N13 · payoff-tuple rotation ทุก fold · dual statistic · KS⁺) · deep review 23 รอบ · Alt-2 refit ทุก fold · รอบ 23 apply แล้ว (pin block `ad4_card.py` = docstring v5 + SPEC_SHA/KS_T_UNITS/KS_ACHIEVED/RG14_TAGS · E15 ปิด (Engineer เห็นตรงกัน · วินสั่ง apply หลังเห็น patch) · (K) fail-closed · N10 docstring · tooling v15/v10) · Engineer commit-readiness review รอบ 24 = PASS-with-changes → apply แล้ว (deps +return_w · `pin_ad4.py` · pin block ก่อน `__main__`) · ค้าง: commit spec (รอวินสั่ง · `--require-pin` PASS) → certify v2**) | ▶ | (ยังไม่จอง claim) |

## Tooling / Governance
- **Research Traceability System** [CLAIM-0011] — `Scripts/ledger_check.py` (validate + `--emit-index` + `--self-test`)
- run: `python Scripts/ledger_check.py` (validate) · `--emit-index` (regen SCRIPT INDEX skeleton) · `--self-test`
- **2026-09-03 (Win สั่ง):** นำวินัยจาก erfx.be เข้า Trellis — CLAUDE.md (phase STOP/relay-only · Phase-3 gate · provenance · surface-conflict · stale-marker · blocker-stop · FRAME) + Engineer agent **Review Protocol บังคับ + review-only (ถอด Write/Edit)** + hook signals · ต้นทาง → memory `reference-erfx-discipline-source`

## Blockers / รอ Win
- **AD-4 = B′ (ตัดสินแล้ว 09-03) · design v5 + Alt-G global rotation + Alt-2 refit ทุก fold หลัง deep review 23 รอบ (09-09)** — ค้าง: commit spec (รอวินสั่ง · pin block `ad4_card.py` sealed · `card_scan.py --require-pin` PASS · SPEC_SHA + `git hash-object` อยู่ใน LEDGER FRONTIER + commit message) → N11 freeze window → ขั้น 2 implement (ขอวิน · `tp1_card.py` asset 7 claim) → Claude-Verify → **วินรับทราบ Alt-G +8.6 CPU-h (A-1) / +23.2 เต็ม · OC bracket 1.35-14.9% · envelope §7.1 = technical decision บันทึกแล้ว (Rec-8 คง · influence-concentration adopt) · class-fix เข้า CLAUDE.md = วินอนุมัติ 09-06 (fold 4 ประโยค · uncommitted) · **rule (k) `ledger_check.py` = วินมอบ technical 09-08 → Claude adopt → apply แล้ว (self-test ALL PASS (count = `--self-test` output) · proof-of-fire) · ไม่มีของวินค้าง**** → commit spec (ก่อนรัน v2 · same-commit sync LEDGER/Progress Log) · ขั้น 2 แก้ script scope 16 ข้อ (ขอวินตาม CRITICAL) · ขั้น 3 certify v2 3,080 draws ≈ 7-10 ชม. (Alt-G +33% fits · A-1 staging PRIMARY ก่อน ≈3-4 ชม. (34.8 CPU-h) + RG14 2.7 CPU-h (W=50) · synthetic exempt) · ขั้น 4a/4b ตาม rule R6
- **Stage E demo v4** — plan §E: 2 บัญชี demo แยก · HourShift=-1 · verify Friday close · ไม่มี blocker เชิง clock (Gate 0 ปิด 07-04) · residual ที่รู้: C1 overnight-hold asymmetric · C2 sim-optimism haircut ~1.2/ไม้ high-vol
- **Stage-F decision** (ของ Win — memory 07-12 "ครอบคลุมก่อน") — options สด → LEDGER FRONTIER
- **doc stale ที่แก้แล้ว 09-03:** STATUS สถานะ/Blockers · LEDGER CLAIM-0012 วงเล็บ "clock-fix รอ Gate 0" · Progress Log entry AD-4

## EA / Modules (pre-reframe TRELLIS-003 build — frozen · ดู ARCHIVE)
- reframe เปลี่ยน focus เป็น research · EA-build roadmap/modules/locked-decisions/blockers เดิม → `ARCHIVE_prereframe.md`
