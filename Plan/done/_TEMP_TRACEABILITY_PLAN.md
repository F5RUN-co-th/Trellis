# _TEMP_ Research Traceability System — Correction Plan (v-final-6)

> **สถานะ:** working plan · **ชั่วคราว** · ยังไม่ build · รอวินตัดสิน (review อีก / build / อื่น)
> **ห้าม self-certify "terminal"** — track record: plan v1→v5 FAIL ทุกรอบ + v-final เจอ 2 BLOCKER + v-final-3 เจอ DEFECT-8 (partition ซ่อน dual-role experiment) → confidence ผมไม่เชื่อถือ ต้องผ่าน review
> **ขอบเขต:** current-frame = `Plan/TRELLIS-010_v3_offensive_reframe.md` + งาน session นี้ (ไม่ใช่ทั้ง project)

---

## 0. ปัญหา (วิน 4 ข้อ) — ต้องปิดครบ

1. ไม่รู้ว่ามี research/experiment/proof อะไรบ้าง · ผล · **วิธีวัด** · **โปร่งใส/ยุติธรรมไหม**
2. ไฟล์ `.py` (~52 ไฟล์) ไม่รู้ทำอะไร + lineage
3. ผล/status **เด้งไปมา** ระหว่าง `STATUS.md` **และ** `TRELLIS-010_v3_offensive_reframe.md`
4. เจ้าของ project **ตามงาน/เห็นผลไม่ได้**

**ราก:** ไม่มี registry ผลวิจัย + doc ไม่มีเจ้าของบทบาทเดียว → ผลกระจาย commit/STATUS/plan/docstring

---

## 1. Document Architecture (single source of truth ต่อ concern)

| doc | หน้าที่ **เดียว** | หมายเหตุ |
|---|---|---|
| `Plan/TRELLIS-010_v3_offensive_reframe.md` | **DESIGN/DOCTRINE** | หลัง extract เลขออก · mechanism/lessons FROZEN + pointer → LEDGER |
| **`Plan/TRELLIS-010_LEDGER.md`** (ใหม่) | **ผลวิจัย = single LIVE SoR** | ที่เดียวที่มีเลขผลปัจจุบัน |
| **`Plan/TRELLIS-010_ARCHIVE_prereframe.md`** (ใหม่) | **pre-reframe narrative** จาก STATUS (grid/DIAG/TRELLIS-007/clock-bug) | **FROZEN snapshot** · ครั้งเดียว · lint/DoD **exempt** |
| `.claude/status/STATUS.md` | **build/stage** เท่านั้น | no result-metrics · ชี้ Claim-ID |
| `Backup/oldwork.md` | Win's **chat-backup** ของ session นี้ | **นอกสถาปัตยกรรม · ห้ามแตะ** (verified: mtime 18:38 · เนื้อ = บทสนทนา session · ไม่ใช่ pre-reframe archive · อยู่นอก repo) |

---

## 2. `LEDGER.md` — โครงสร้าง

### `## CURRENT FRONTIER` (บนสุด)
- reuse **Hypothesis-Elimination-Matrix** (`§9` · qualitative open/eliminated · **ไม่มีเลข posterior**)
- populate **สด**: direction-at-real-exit = FROZEN · next = **วินตัดสิน** (magnitude / tick-price / monetize-v4)
- `budget N/40` = **display-only** discovery-card tracker (ไม่ใช่ claim-count)
- **maintained by DoD-discipline** · **ไม่ machine-enforce currency**
  - เหตุ (DEFECT-A verified): `frontier==max(seq)` = false invariant (falsification-heavy log · 16 บรรทัด FALSIFIED/dead → newest มัก dead) · `status==open` ก็ false-fail (frozen · อาจไม่มี open claim)

### `## CARRIED-FORWARD DEPENDENCIES`
- data-artifact เท่านั้น + เลข frozen + ที่พิสูจน์: walker `brain_v1_run.py` · h0 dataset · **v4 = 1 proven behavior** (`§2`)
- **methodology** (verify-3-ชั้น/pre-register/lockbox) อยู่ **doctrine** ไม่ใช่ ledger

### `## CLAIMS`
แต่ละ claim = **labeled markdown BLOCK** (`### CLAIM-NNNN` + `- **field:**` บรรทัดต่อ field) · **ไม่ใช่ wide table** (free-text มี `|`/`·`/ไทย → พัง column) · keyed **zero-padded Claim-ID** (= ID เท่านั้น ไม่ derive frontier) · **N:M กับ script** (gate1 = 3 claim · direction = 1 claim/5 script)

**field = §9:128 Claim Object จริง (6) + operational (6):**
- **[§9:128]** `observed:` (tool output · เลข frozen) · `supported:` (conditional "ใต้ X") · `not-yet-supported:` · `evidence-level: L0|L1|L2|L3|L4` · `dependencies:` · `invalidated-by:`
- **[operational]** `kind: experiment|infra` · `status: live|superseded-by-#N|terminal|FALSIFIED|INCONCLUSIVE|DEAD-do-not-rerun` · `fairness:` (ENUM · ดูล่าง) · `correction-lineage:` (inline) · `scope-of-death:` (บังคับบน negative) · `reproduce: <command>`
- **แยก Observed vs interpretation:** เลขดิบอยู่ `observed:` (ยืนแม้ interpretation downgrade — เช่น `+17.98/−13.48` ยังจริง แต่ "DIRECTION=คอขวด" downgrade `§9:119`) · `status` govern interpretation lifecycle

**`fairness:` = FIXED ENUM (auditable ไม่ใช่ prose — prose = สิ่งที่ erode 16 รอบ session นี้):**
`field-tag[SIM-SEARCH|SIM-CONFIRM|MT5-tester|holdout] · pipeline-owned[Y|N] · null-control[none|permutation|day-block|mirror] · seed-robust[Y|N|NA] · leak-guard[Y|N|NA] · verified-by[self|Engineer|adversarial]`

**`correction-lineage:` = INLINE** `corrections N รอบ · was "X" → now "Y" · pattern <tag>` (audit: commits a26a93e..f31fd60) — **ไม่ใช่ commit-range เปล่า** (= offload/workaround)

### `## SCRIPT INDEX` — **build by ENUMERATING ทั้ง 52 ไฟล์** (ไม่ใช่ example/hand-wave)
> **[DEFECT-8 fix] TWO orthogonal roles ต่อไฟล์ (ไม่ใช่ partition 1-category):** 50/50 scripts มี `__main__` — ไฟล์ส่วนใหญ่เป็น **ทั้ง** infra (export ให้คนอื่น) **และ** experiment (มี `main()` ให้ผล). single-partition บังคับ either/or → infra-classified ที่มี `main()` หลุด cat-1 → check (e) ไม่สแกน → **ซ่อน experiment (reopen problem #1/#4)**. หลักฐาน casualty: `direction_predictor_v1` (infra ให้ 4 gate **แต่** `:102-184` main() = experiment v1 · leaky `:122` · untracked · unrecorded ใน STATUS/§9).

> **[DEFECT-10 fix] SCRIPT INDEX = MACHINE-GENERATED จาก disk-scan · ห้าม hand-freeze role-set/count ในแผนนี้.** เหตุ: v-final-5 ผม hand-patch เฉพาะไฟล์ที่ Engineer flag → พลาด 3 ไฟล์ (`gate1_mi_ceiling`/`gate_c_wf`/`test_b_direction_decomp` = dual-role) + mis-slot `grid_sim` (ASSET-only แต่ใส่ legacy) → hand-list = drift เสมอ (= workaround). **authoritative role = output ของ scan สองตัว ไม่ใช่ตัวอักษรในแผน:**
> - **ASSET** = `M` ถูก `import M`/`from M import` โดย `Scripts/*.py` อื่น (import-scan) → enforce โดย check (g)
> - **EXPERIMENT** = `M` มี `__main__` (regex-scan) → enforce โดย check (f) · disposition (live/superseded/legacy/reproduce-only) = ดุลพินิจ (validator เช็คแค่ **มี** ไม่ตัดสินว่าถูก)
> - **verified snapshot (07-09 · ILLUSTRATIVE ไม่ freeze):** DUAL(import∩main)=**12** · ASSET-only=**2** (`dir_features`,`grid_sim`) · EXP-only=38 · ORPHAN=**0** (ทุกไฟล์ถูก cover โดย (f)∨(g))

**Role A — ASSET (illustrative · authoritative = import-scan):** `brain_v1_run`(imported 15) · `entry_platform`(imported 8 · live dep ของ `dual_asian_sim` v4-canonical + `h0_features`) · `h0_cardkit`(6) · `direction_predictor_v1`(4 gate) · `opportunity_unit_v4`(§9:107) · `opportunity_unit_v3`(→v4) · `dual_asian_sim` · `stage0_join`(→holdout_exness/h0_join_pnl) · **`grid_sim`(ASSET-only · imported by layer1/2/2b · no `__main__` · STATUS:141 keep — ไม่ใช่ legacy)** · `dir_features`(ASSET-only) · `ledger_check`(tooling · ไม่ถูก import = ไม่ถูก (g) บังคับ แต่ tag ไว้)

**Role B — EXPERIMENT disposition (illustrative · authoritative = `__main__`-scan):**
- `live → Claim-ID` — gate1/gate2/gate_c/gate_magnitude/gate_spread/test_b/direction_at_real_exit
- `superseded → Claim-ID(status)` — `direction_predictor_v1`(v1 · exit=trade_R ≠ real-walk · superseded by direction_at_real_exit · INCONCLUSIVE · leak `v1:122` · verified-by:self) · `direction_predictor`(v0) · `opportunity_unit_v3`(Q1-Q5)
- `legacy → ARCHIVE_prereframe.md` (narrative-move) — mr_sim/layer0-2/edge_screen/h0_card*/c*_features/stageb_pipeline ฯลฯ · **`entry_platform`= narrative legacy(TRELLIS-008) แต่ file LIVE → ARCHIVE narrative เท่านั้น · check (g) ห้าม delete** (ไม่ใช่ prose เพียงอย่างเดียว — enforce ด้วย (g))
- `reproduce-only|self-test → justified-tag` — เช่น `dual_asian_sim`→reproduce v4 numbers

---

## 3. Validator `Scripts/ledger_check.py`
existence+consistency + `--emit-index` เท่านั้น · **<130 บรรทัด · stdlib · fail-loud** · **ไม่ตัดสิน semantics** · **ledger_check.py เอง = index: ASSET(tooling) + EXPERIMENT-disposition `self-test`** (มี `__main__`+self-test → ผ่าน (f) · ไม่ถูก import โดยใคร → ไม่ต้อง ASSET-by-(g) แต่ tag tooling ไว้ · กัน self-orphan — BLOCKER-2)
- (a) **[COVER ไม่ใช่ partition]** ทุก `Scripts/*.py` (glob `*.py` · exclude `__pycache__`/`.ex5`/`.mq5`) ปรากฏใน SCRIPT INDEX **≥1 role** (ASSET หรือ EXPERIMENT-disposition หรือทั้งคู่) — 52-count = cover check (set-referenced ⊇ set-on-disk)
- (b) ทุก `reproduce:` command resolve → script path จริง
- (c) ทุก claim block มี required field (รวม `evidence-level` + `invalidated-by`) non-empty
- (d) ทุก Claim-ID ที่ `CURRENT FRONTIER` + `CARRIED-FORWARD` อ้าง → resolve claim block จริง (ref-integrity)
- **(e) [BLOCKER-1] ทุก Claim-ID ที่ SCRIPT INDEX EXPERIMENT-role (`→ Claim-ID`) อ้าง → resolve claim block จริง** — **script→proof edge = แกน problem #2** · **[v6 PASS-hardening] resolve Claim-ID-valued field ใน claim block ด้วย** (`status: superseded-by-#N` · `dependencies:`) — กัน dangling pointer ชี้ null (Q4 · secondary ref-site ที่ (c)/(d) ไม่คลุม)
- **(f) [DEFECT-8] `__main__` completeness (mechanical · existence-only):** ทุก script ที่ไฟล์มี `__main__` guard (regex tolerant: `if\s+__name__\s*==\s*['"]__main__['"]`) → **ต้องมี EXPERIMENT-disposition** ใน INDEX (Claim-ID / superseded-Claim-ID / legacy-ARCHIVE / justified reproduce-only|self-test) · ขาด = FAIL (จับ infra ที่ซ่อน experiment) — validator เช็คแค่ **มี disposition** ไม่ตัดสิน semantics (ตรง philosophy เดิม)
- **(g) [DEFECT-9 · symmetric ของ (f)] ASSET completeness (mechanical · existence-only):** import-scan ทุกไฟล์ — ถ้า `M` ถูก `import M`/`from M import` โดย `Scripts/*.py` **อื่น** → `M` **ต้องมี ASSET role** ใน INDEX · ขาด = FAIL (จับ live dependency ที่ถูก mislabel legacy-only แล้วโดน archive/delete — casualty `entry_platform`→`dual_asian_sim` v4) — mirror ของ (f) เป๊ะ · ~8 บรรทัด stdlib
- **ไม่มี** frontier max-seq / status==open (false invariant ทั้งคู่)
- **self-test (บังคับ · 5 fixture):** (i) block field หาย → (c) FAIL · (ii) frontier/experiment-role อ้าง Claim-ID ไม่มี → (d)/(e) FAIL · (iii) script ไม่อยู่ role ไหน → (a) FAIL · (iv) `__main__` แต่ไม่มี EXPERIMENT-disposition → (f) FAIL · (v) ไฟล์ถูก import แต่ไม่มี ASSET role → (g) FAIL
- **[v6 PASS-hardening] golden-fixture (บังคับ · pin scan-logic independent of emit):** synthetic tree จิ๋ว hand-audit — known ASSET/EXP/ORPHAN membership + **exotic syntax** (no-space `if __name__=="__main__":` · multiline `from X import (...)` · dynamic `importlib`) → expected classification commit ครั้งเดียว review · หลังจากนั้น emit+validate share routine เดียวได้ (DRY) โดย logic ถูก pin กับ ground-truth อิสระ · **เหตุ:** emit+validate share scan = common-mode blind spot (guard drift ได้ แต่ไม่ guard scan-logic — doctrine "สมมติฐาน share = จุดบอดร่วม")

---

## 4. Enforcement
- **numeric-lint = WARNING เท่านั้น (heuristic ไม่ใช่ proof)** scope = `{STATUS.md · plan-doc}` · **ARCHIVE + LEDGER exempt**
  - **flag เฉพาะ RESULT-token ที่ชัด:** `$`-denominated (`[+−-]?\$?\d+` ที่เป็น P&L) · `PF \d` · `DD \d` · WR% ของผล · **[DEFECT-8 review] signed-R** `[+−-]\d+\.\d+\s*R` (จับ `−0.093R`/`+1.745R` = ผลเกือบทั้งหมดใน frame นี้เป็น R-denominated) — **ไม่ flag** doctrine-unit (unsigned R-multiple `0.3-0.46R` · ×-multiplier `5.6-7×` · threshold `<2%` · L0-L4 · config lot/oz/vN.N)
  - ⚠ **ข้อจำกัดยอมรับ:** signed-R จับได้เฉพาะ token ที่มีเครื่องหมาย → unsigned pair (`17.98/13.48`) ยังหลุด · doctrine-R ที่บังเอิญมีเครื่องหมายอาจ false-positive (WARNING เท่านั้น = ยอมรับได้) · lint = corroborating ไม่ใช่ proof → DoD-discipline + review ยังเป็นด่านหลัก
- **`CLAUDE.md` += Definition-of-Done (1 บรรทัด):** commit ที่แตะ experiment → same-commit update CLAIM block (§9:128 6 + operational) + FRONTIER · **results เขียน LEDGER เท่านั้น** (STATUS+plan-doc result-free) · `ledger_check` ผ่าน
- pre-commit hook (local · เรียก ledger_check) + **document manual-run** (hook bypassable/ไม่ version-controlled)

---

## 5. Deliverables + ลำดับ
1. **EMIT SCRIPT INDEX จาก scan (ไม่ hand-author · DEFECT-10):** `ledger_check.py --emit-index` สแกน `Scripts/*.py` → output role rows (ASSET จาก import-scan · EXPERIMENT-skeleton จาก `__main__`) · **คนเติมเฉพาะ disposition + Claim-ID** (ดุลพินิจที่ scan ทำแทนไม่ได้) ลงบน skeleton · ห้าม hand-list role-set/count
   - ⚠ **กัน self-grading (doctrine):** emit ≠ validate = คนละ invocation · validate (check a/f/g) **re-derive จาก disk สดตอน commit** เทียบกับ INDEX ที่ commit ไว้ → จับกรณีเพิ่ม/ลบ script แล้วลืม regenerate (ไม่ tautological · ถ้า generate+validate รอบเดียวกันจะ pass เปล่า — ห้าม)
2. สร้าง `ARCHIVE_prereframe.md` **ก่อน** trim STATUS: ย้าย pre-reframe narrative · frozen (order นี้กัน data-loss)
3. สร้าง `LEDGER.md`: frontier + carried-forward + **claim-authoring pass เดียว keyed by Claim-ID** (dedupe by ID · source ทั้ง STATUS/commit **และ** plan-doc §9 → ไม่มี claim ซ้ำ/หลุด)
   - claim = §9:128 6-field + operational · **backfill = transcription-only** (frozen-number + commit-hash ที่ commit แล้ว · **no re-run/re-derive · verified-by:self**)
   - **lifecycle-aware extract §9:89-142** เข้า claim นี้ (per-claim · `+17.98`=observed-live/interpretation-superseded) · §9 เหลือ doctrine frozen+pointer · **preamble:7 = append** "results→LEDGER"
4. trim `STATUS.md` → build/stage · no-result-metrics · Claim-ID pointer
5. สร้าง `Scripts/ledger_check.py` (validate + `--emit-index`) + **index มันเป็น tooling** + รัน **ต้องผ่าน** (**5 self-test fixture + golden-fixture** · §3 · fold 2 PASS-hardening: golden scan-logic + (e) dangling-pointer resolve)
6. `CLAUDE.md` += DoD line
7. **commit เดียว** (+ lint `direction_at_real_exit.py` ค้าง)

---

## 6. Non-goals (anti-cathedral)
ไม่ทำ: `claims.yaml`+generator (ไม่มี query consumer) · frontier max-seq/currency enforcement (false invariant) · dependency-graph · lifecycle-state-machine · posterior-weight · git-automation · backfill pre-reframe experiments เป็น claim · แตะ `oldwork.md`

---

## 7. Correction history (ทำให้แผนเองก็ traceable)
| ver | Engineer/Win จับ | fix |
|---|---|---|
| v1 | fork schema · free-text fair · ไม่มี validator/frontier/carried | reuse Claim Object · enum · validator · frontier · carried §2 |
| v2/3 | per-experiment key กำกวม · YAML tempting | Claim-ID N:M · reject YAML · STATUS no-result-metrics |
| v3→4 | wide-table เปราะ · budget==count ผิด (Claude จับ) | labeled-block · frontier ref (ไม่ใช่ budget) · archive frozen |
| v4→5 | **problem-3 plan-doc leg เปิด** | de-result plan-doc + :7 append |
| v5→6 | DEFECT-A max-seq false · DEFECT-B line-range extract ฉีด over-claim | drop max-seq · lifecycle extract |
| Win | **oldwork = chat-backup ไม่ใช่ archive** (Claude assert ผิด) | ถอด oldwork ออก · pre-reframe→ARCHIVE ใหม่ |
| v-final→2 | **BLOCKER-1 no-orphan ขัด no-backfill · BLOCKER-2 schema ≠ §9:128 (drop L0-L4/Invalidated-by)** + 4 | 3rd index-category · §9:128 จริง+operational · ARCHIVE exempt · frontier ref-integrity · backfill stop-clause · whitelist config |
| v-final-2→3 (review ไฟล์จริง) | **BLOCKER-1 validator ไม่เช็ค cat-1 script→claim edge (แกน problem#2) · BLOCKER-2 ledger_check self-orphan** · MED: opportunity_unit example v3ผิด(v4 canonical) · §5.1/5.3 double-source · LOW whitelist R/× · self-test ไม่ระบุ · **Claude จับ: Engineer overstate v1 (v1=infra ให้ 4 gate ไม่ใช่ orphan)** | check(e) cat-1 resolve · index ledger_check เป็น tooling · enumerate 52 ไฟล์(ไม่ example) · single claim-pass keyed-ID · lint เฉพาะ $/PF/DD (R นอก reach) · 3 self-test fixture · v1=cat-2 infra |
| v-final-3→4 (Engineer DEFECT-8 · Claude verify: **half-right — v1=infra จริง แต่ remedy "cat-2 no claim" ซ่อน experiment v1**) | **DEFECT-8 partition 1-category ซ่อน dual-role** (50/50 script มี `__main__` · v1 infra+leaky-experiment untracked/unrecorded verified: STATUS grep=0 · §9:142 flag เท่านั้น) · MED lint R-denominated หลุด · LOW label(v-final-2) ผิด | partition→**cover** · 2 orthogonal role (ASSET + EXPERIMENT-disposition) · **check(f) `__main__` completeness** · self-test 4 fixture · lint +signed-R · label แก้ · (Claude reject: Engineer "registry" ใหม่ = ศัพท์ซ้ำ → ใช้คำเดิม) |
| v-final-4→5 (Engineer DEFECT-9 · Claude verify grep: **CONFIRMED**) | **DEFECT-9 ASSET axis ไม่ enforce (mirror ของ DEFECT-8) + hint ผิด**: `entry_platform` = live ASSET (imported 8 รวม v4-canonical `dual_asian_sim`) แต่ §2:66 สั่ง archive → v4 repro พัง · hint ใส่ edge_bar_mc/brain_v1_ceiling เป็น dual-role ผิด (0 importer) · ตก 4 ไฟล์ (brain_v1_run/entry_platform/h0_cardkit/stage0_join) | **check(g) symmetric ASSET completeness** (import-scan → imported ต้องมี ASSET role) · self-test 5 fixture · ASSET derive by import-scan (§5#1) · แก้ enumeration (9 dual-role จริง · entry_platform un-archive file + narrative-only) · tolerant `__main__` regex |
| v-final-5→6 (Engineer DEFECT-10 · Claude verify import-scan สดเอง: **CONFIRMED 12≠9**) | **DEFECT-10 ผม hand-patch เฉพาะไฟล์ที่ flag แทน re-derive ทั้ง set** (= anti-pattern แผนเองห้าม §5:97): dual-role จริง **12 ไม่ใช่ 9** (ตก gate1_mi_ceiling/gate_c_wf/test_b) · `grid_sim`=ASSET-only mis-slot legacy · hand-list = drift เสมอ (workaround) | **ลบ hand-list authority ทั้งหมด** → `--emit-index` machine-generate จาก scan · แผนเก็บแค่ illustrative + snapshot(ไม่ freeze) · แก้ grid_sim→ASSET · self-grading guard (emit≠validate · validate re-derive สด commit-time) |
| v6 **Engineer PASS (build-ready)** · Claude verify: scan 3-way agree · 2 hardening ถูกจริง | non-blocking: (1) emit+validate share routine = common-mode blind spot (guard drift ได้ ไม่ guard scan-logic) (2) `status: superseded-by-#N` ใน block ไม่ถูก resolve | fold ระหว่าง build: **golden-fixture** pin scan-logic (§3) · ขยาย **(e) resolve Claim-ID-valued field ใน block** · แก้ #5 staleness 3→5+golden |

---

## 8. รอวินตัดสิน
**สถานะ:** Engineer **PASS build-ready** (v6 · หลัง FAIL 10 รอบ · scan 3-way agree) · 2 hardening fold เข้าแผนแล้ว (non-blocking · ทำระหว่าง build)
options: (1) **build ตาม §5** (ต้องวินสั่ง — สร้าง LEDGER/ARCHIVE/ledger_check + trim STATUS + CLAUDE.md DoD = แตะหลายไฟล์) · (2) review อีก · (3) ปรับ scope
⚠ **ไม่ commit จนวินสั่ง** (standing) · **ไม่ build จนวินสั่ง** (propose→wait)
