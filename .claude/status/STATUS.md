# Trellis — Implementation Status

**Last updated:** 2026-07-09

> **build/stage เท่านั้น · ไม่มี result-metric** (ผลทั้งหมด → `Plan/TRELLIS-010_LEDGER.md` keyed by Claim-ID) · doctrine/mechanism → `Plan/TRELLIS-010_v3_offensive_reframe.md` · narrative ก่อน reframe → `Plan/TRELLIS-010_ARCHIVE_prereframe.md`
> DoD (CLAUDE.md): commit ที่แตะ experiment → update CLAIM block + FRONTIER · `python Scripts/ledger_check.py` ต้องผ่าน

## Current Stage — TRELLIS-010 v3 Offensive Reframe (research: DIRECTION edge)
- **frame:** หา additive DIRECTION edge (root = engine edge ไม่ใช่ capital) · เป้า: $100 รอด + กำไรมาก + เข้าทุกโอกาส
- **สถานะล่าสุด:** direction-at-real-exit = **FROZEN terminal** [LEDGER CLAIM-0010] · **รอ Win ตัดสิน next** (richer-OHLC / tick-price / magnitude / monetize-v4 / forward-test) — ไม่ prescribe
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

## Tooling / Governance
- **Research Traceability System** [CLAIM-0011] — `Scripts/ledger_check.py` (validate + `--emit-index` + `--self-test`)
- run: `python Scripts/ledger_check.py` (validate) · `--emit-index` (regen SCRIPT INDEX skeleton) · `--self-test`

## Blockers / รอ Win
- **next-experiment decision** — opportunity-validation verified แล้ว (Engineer 07-11) · options สด → LEDGER FRONTIER
- clock-fix Gate 0 re-import 2025-26 (pre-reframe · ARCHIVE) — ค้างก่อนหน้า reframe

## EA / Modules (pre-reframe TRELLIS-003 build — frozen · ดู ARCHIVE)
- reframe เปลี่ยน focus เป็น research · EA-build roadmap/modules/locked-decisions/blockers เดิม → `ARCHIVE_prereframe.md`
