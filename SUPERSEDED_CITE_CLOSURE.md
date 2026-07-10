# Superseded-Cite Closure — Correction Plan (working draft · UNVERIFIED)

> **สถานะ:** Engineer review 07-10 = **PASS-with-changes** (2 mandatory ด้านล่าง · Claude verified ทั้งคู่กับ code จริง) → implement ได้ตามเงื่อนไข Win
> **verify-as-I-go บังคับ:** หลังทุก edit รัน `python Scripts/ledger_check.py` (PASS) + `--self-test` (ALL PASS)

## 0.5 Engineer review outcome (07-10 · adversarial · context แยก)
- **MAJOR-1 (mandatory):** ตำแหน่งแทรก check (i) "~:148" ผิด — `head` assign ครั้งแรก `:153` ใน block (h) → NameError · **แก้: แทรกหลัง block (h) (:160) reuse `head`**
- **MAJOR-2 (mandatory):** F1 ไม่มี regression guard — `fx_vi` ใช้ status "superseded" เพียว fire (h) ทั้ง predicate เก่า/ใหม่ · revert substring → self-test ยัง ALL PASS เงียบ · **แก้: `run_case` เพิ่ม negative-assert mode + fixture (ix)** — frontier cite `[CLAIM-0001]` bare + status `terminal (…superseded-by-CLAIM-0001)` → assert `(h)` **ไม่** fire
- **MINOR-3 (รับ):** `SUP_TGT` เพิ่ม `re.I` (gate เช็คบน lowered แต่ SUP_TGT parse raw)
- **MINOR-5 (รับ):** bump CLAIM-0011 correction-lineage (+1 รอบ closure) ใน edit ชุดเดียวกัน
- **MINOR-6 (รับ):** `mkdir Plan/done` ก่อน move (_TEMP untracked → mv ธรรมดา)
- **MINOR-1 (framing):** bug F1 = latent ไม่ใช่ active (CLAIM-0002 ไม่ถูก cite ใน head · validator ปัจจุบัน PASS) — fix ยังถูกต้อง (defensive)
- **Engineer ยืนยัน:** trace (i) บน frontier จริง pass clean · F2 count-census ครบ (ไม่มี live copy หลุด) · `_TEMP` ref เดียว = `ledger_check.py:5` · move .md ไม่กระทบ check ใด
- **out-of-scope ใหม่ (log แยก · ไม่ fold):** status-leading-token invariant (root ของ MINOR-2/4 — status เป็น free-text ทุก non-live test เป็น heuristic)

---

## 0. ปัญหา (root)
LEDGER `## CURRENT FRONTIER` cite claim เป็นหลักฐานของ verdict. Claim บางตัว status ≠ live (superseded/DEAD). cite ไม่สม่ำเสมอ (บาง arrow บาง bare) → คนตาม frontier เจอหลักฐานที่ถูก supersede โดยไม่รู้.
**ชั้นลึก:** arrow `→target` = denormalized copy ของ `status:` field (SSOT) → ต้องมี **sync strategy** (validate) ไม่งั้น = redundancy-without-sync = bad design.

## 1. Decision (Win)
**Option A = validate arrow-target (read-only).** เหตุ A > C (auto-emit): arrow ฝังใน hand-authored table cell → C ต้อง mutate in-place (blast-radius) · A read-only ไม่แตะ narrative. A > skip: skip = denorm-without-sync. check(i) = **TRUE invariant** (§6 ban เฉพาะ FALSE-invariant currency).

---

## 2. Closure spec (7 items · ทุก edit ระบุ file:line)

### F1 — fix substring→startswith predicate `Scripts/ledger_check.py:158`
```python
# ปัจจุบัน (BUG): any(k in st for k in NONLIVE)  → CLAIM-0002 "terminal (…superseded-by-CLAIM-0002)" false-flag non-live
# แก้เป็น:
if st.startswith(NONLIVE):        # leading-token · str.startswith รับ tuple · st ผ่าน .lower() แล้ว(:157) · field strip แล้ว(:90) → ไม่ต้อง .strip()
```
> ห้ามใช้ `.strip()` (redundant · field strip ที่ :90 แล้ว)

### Check (i) — arrow-target consistency (เพิ่มหลัง block (h) :160 — reuse `head` ที่ assign :153 · **ห้ามแทรกก่อน :153 = NameError** [MAJOR-1])
```python
# (i) [arrow-target consistency · TRUE invariant] superseded cite ที่มี →target ต้องตรง status-target
SUP_TGT = re.compile(r"superseded(?:→|-by-)CLAIM-(\d{4})")   # จับทั้ง 2 spelling
for br in re.findall(r"\[CLAIM-\d{4}[^\]]*\]", head):
    if "=live" in br or "·mag" in br:            # ⚠ fact-level human-review → skip FIRST (guard-then-continue · ก่อน per-cid)
        continue
    for cid in CLAIMID_RE.findall(br):
        st_raw = claims.get(cid, {}).get("status", "")
        if not st_raw.strip().lower().startswith("superseded"):   # ⚠ superseded-ONLY (ไม่ใช่ is_nonlive · กัน [CLAIM-0008 DEAD] false-positive)
            continue
        stgt = SUP_TGT.search(st_raw)             # parse บน raw (มี CLAIM ตัวใหญ่) ไม่ใช่ lowered
        cm = re.search(r"→(\d{4})", br)           # cite arrow-target
        if not cm:
            fail(f"(i) {cid} superseded แต่ cite ไม่มี arrow-target: `{br}`")
        elif stgt and cm.group(1) != stgt.group(1):
            fail(f"(i) {cid} cite →{cm.group(1)} แต่ status →{stgt.group(1)} — แก้เป็น →{stgt.group(1)}")   # actionable error
```
**Trace บน frontier ปัจจุบัน (ต้อง pass clean):** `[CLAIM-0005→0010]`✓(0010 terminal→skip) · `[CLAIM-0007→0009]`×4✓ · `[CLAIM-0007·mag=live]`→skip(=live) · `[CLAIM-0008 DEAD]`→skip(not superseded) · `[CLAIM-0004]`/`[CLAIM-0010]`→skip(live).

### Fixture (vii)+(viii)+(ix) — check(i) 2 branch + F1 regression guard (`run_case` = 1 assert/fixture)
- **(vii)** frontier cite `[CLAIM-0001→9999]` · CLAIM-0001 status `superseded→CLAIM-0001` (self-ref กัน (e) dangling) → expect `(i)` mismatch fire
- **(viii)** frontier cite `[CLAIM-0001→]` (empty) · status superseded → expect `(i)` empty-arrow fire
- **(ix) [MAJOR-2 regression guard]** frontier cite `[CLAIM-0001]` bare · status `terminal (v2 superseded-by-CLAIM-0001)` (self-ref) → expect `(h)` **ไม่ fire** (negative-assert) — ใต้ substring เก่าจะ fire = จับ revert ได้
- **`run_case` เพิ่ม param `expect_present=True`** — `hit = any(...)` เมื่อ True · `not any(...)` เมื่อ False
> count จะเป็น derived (F2) → ไม่ hardcode "N fixture" ที่ไหน

### Doc note — ใน check region (comment)
- (P4) `status:` field **ต้อง lead ด้วย disposition token** (สมมติฐานของ startswith · "re-measured, superseded→…" จะ false-negative)
- (F3) check (h)/(i) scan เฉพาะ **bracketed** `[CLAIM-…]` · unbracketed slip (rare · convention = bracketed)

### F2 — derive-from-runtime + enumeration-free (doctrine "script owns the number")
**(a) `--self-test` print count (golden แยก · derived):** ใน `self_test()` ก่อน return —
```python
n_gold = sum(1 for d,_,_ in passed if d.startswith("golden"))
print(f"self-test: {len(passed)-n_gold} fixtures + {n_gold} golden")
```
**(b) strip count/range จากทุก prose copy (7 ตำแหน่ง):**
| file:line | ปัจจุบัน (stale) | แก้เป็น |
|---|---|---|
| `ledger_check.py:11` | "รัน 5 fixture + golden" | "รัน self-test (fixtures + golden · ดู output)" — no number |
| `LEDGER:86` | "--self-test 5-fixture+golden" | "--self-test (fixtures+golden)" — no number |
| `LEDGER:243` (CLAIM-0011 observed) | "7 check a-g · self-test 5-fixture + golden ผ่าน" | "validate + --emit-index · ast import-scan robust · **self-test + golden ALL PASS**" — **no count, no range** (a-i encode count → drift) |
| `STATUS:29` | "7 check a-g · 5 self-test + golden · LEDGER=SoR · ARCHIVE=frozen" | name + `[CLAIM-0011]` pointer + minimal role — **ลบ count + ลบ "LEDGER=SoR·ARCHIVE=frozen" (ซ้ำ preamble STATUS:5)** |
| `ledger_check.py:13-15` | docstring check-list a-h | **add `(i)`** → check-DOC (single home · co-located · ไม่ใช่ count-copy) |
> **check-count SSOT = docstring check-list เท่านั้น** (co-located · 10 รอบไม่ drift) · **ไม่ทำ registry** (docstring ไม่ drift มีแค่ copies ที่ drift → registry = over-engineer/lateral-move) · fixture-count = --self-test derived

### Finding 6 — repoint dangling _TEMP spec-pointer + retire _TEMP (same commit)
- `ledger_check.py:5` = "(spec: _TEMP_TRACEABILITY_PLAN.md ...)" = **ref เดียวใน repo ที่ชี้ _TEMP** · retire _TEMP → orphan · stale แม้เก็บ (_TEMP:3 "ยังไม่ build" แต่ build แล้ว)
- **แก้ `:5`** → "(spec: Plan/TRELLIS-010_LEDGER.md CLAIM-0011 · existence+consistency · fail-loud)"
- **move** `_TEMP_TRACEABILITY_PLAN.md` → `Plan/done/` (ไม่ delete · §7:129-133 = frozen correction-history ที่ CLAIM-0011 lineage compress ไม่ครบ)

---

## 3. Implementation order + verify-as-I-go
1. F1 (`:158`) → รัน `ledger_check` (PASS) + `--self-test` (ALL PASS)
2. check (i) + SUP_TGT → รัน `ledger_check` (PASS · trace clean) + `--self-test`
3. fixture (vii)+(viii) + docstring `(i)` → `--self-test` (ALL PASS · fixtures นับเพิ่ม)
4. F2 count-print + strip 7 copies + doc note → `ledger_check` (PASS) + `--self-test`
5. Finding 6: repoint `:5` + move _TEMP → `Plan/done/` → `ledger_check` (PASS)
6. **grep ยืนยัน 0 count-copy เหลือ** + `git status` (uncommitted) → รายงานวิน (ไม่ commit จนวินสั่ง)

## 4. Out-of-scope (log แยก · ไม่ fold)
- check (b)/(e) ไม่มี fixture (pre-existing)
- check (h) re-split head `:153` แม้ parse_ledger คำนวณ `:93` แล้ว (pre-existing minor)
- unbracketed-cite `[CLAIM-…]` boundary (documented · convention = bracketed)
