# ISSUE 2026-07-08 — `v4_exit` เป็น duplicate code ของ `walk()`

**สถานะ:** ✅ **RESOLVED 2026-07-08** (commit ถัดไป) · ค้นพบระหว่าง TRELLIS-010 Test-B design review (Engineer Q5, Claude verify)

## วิธีแก้ที่ทำจริง (production-ready · ไม่ใช่ workaround)
`brain_v1_run.py`: refactor เป็น **single source `_walk_core()`** คืน `(q_exit, pnl, reason, armed, raised, uw30, d30)` + 2 thin adapters:
- `walk()` = `(pnl, reason, armed, raised, uw30, d30)` — **signature เดิมไม่เปลี่ยน** → caller ทั้ง 4 (brain_v1_run/fade_dataset/exhaustion_fade/test_b) ไม่ต้องแตะ
- `walk_exit()` = `(exit_index, pnl)` — แทน `v4_exit` เดิม
`opportunity_unit_v3.py`: ลบ `def v4_exit` (สำเนา) · import + ใช้ `walk_exit` · `opportunity_unit_v4.py`: เปลี่ยนไป `walk_exit`
**verified ไม่เพี้ยน:** exit-locator regression `pnl==facts.pnl` **1487/1487 ✓** · test_b reproduce `Σcurrent==+532.8` ✓ · ทุก caller import OK
→ duplicate logic หมด · เหลือ implementation เดียว · CLAUDE.md rule 3 ผ่าน

---
### (บันทึกเดิม — ปัญหา)
**ความรุนแรง:** Low (code-quality · ไม่กระทบ correctness — มี regression-assert คุมอยู่) · แต่ละเมิด CLAUDE.md rule 3 "ไม่มี duplicate code"

## ปัญหา (evidence)
`Scripts/opportunity_unit_v3.py:57-85` `v4_exit(ctx,k,d,ent,stop0,R)` = สำเนา branch-for-branch ของ
`Scripts/brain_v1_run.py:130-180` `walk(ctx,k,d,ent,stop0,R,trail_on,ts_on)`:

| branch | walk() | v4_exit |
|---|---|---|
| catchup/gap (new-day) | :144-153 | :63-70 (เหมือน) |
| stop-hit | :154-159 | :71-75 (เหมือน) |
| EOD (Fri20/23) | :160-163 | :76-78 (เหมือน) |
| TS-checkpoint | :164-171 | **ไม่มี** |
| trail (arm A·R / dist D_TRAIL·R) | :172-178 | :79-83 (เหมือน) |
| return | `(pnl,reason,armed,raised,uw30,d30)` | `(exit_index, pnl)` |

## Root cause (ไม่ใช่ symptom)
`walk()` **ไม่คืน exit-index** (q) · `opportunity_unit` ต้องใช้ exit-index ทำ event-overlap coverage
→ แทนที่จะเพิ่ม index ใน return ของ `walk()` กลับ fork logic ทั้งก้อนเป็น `v4_exit` · regression-assert
(`opportunity_unit_v3:251-254` · `brain_v1_run:202/210 sum==532.8`) แค่ **จับ** drift ตอน runtime ไม่ **กัน**

## Solution (production-ready · ไม่ใช่ workaround)
รวมเป็น single canonical exit:
1. เพิ่ม exit-index `q` เข้า return ของ `walk()` (หรือ thin wrapper `walk_with_index()`)
2. ลบ `v4_exit` · ให้ `opportunity_unit_v3` import `walk`
3. คุมด้วย regression-assert เดิม (SHA/pnl==facts) ก่อน+หลัง refactor → ยืนยัน 1487/1487 ไม่ drift

## ทำไมเลื่อน (constraint ไม่ใช่ excuse)
- refactor แตะ canonical engine (`brain_v1_run.walk` ถือ +532.8/+876) = ต้องทำแยกอย่างระวัง มี regression gate เต็ม
- งานปัจจุบัน (Test-B) **ไม่จำเป็นต้องใช้ `v4_exit`** — import `walk()` ตรงได้เลย (ต้องการแค่ pnl=element[0]) → ไม่เพิ่ม fork ที่ 3 · dedupe จึงไม่ block Test-B
- log ไว้เพื่อไม่ทิ้งเงียบ · หยิบทำเมื่อแตะ engine รอบถัดไป
