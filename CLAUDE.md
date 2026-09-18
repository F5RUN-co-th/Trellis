# Trellis EA — Project Instructions for Claude

> **Trellis** = โครงระแนงไม้เลื้อย (ที่มาของชื่อ = grid หลายชั้น · strategy ปัจจุบันไม่ใช่ grid แล้ว)
> **ประเภท:** research DIRECTION edge บน XAUUSD (Stage: TRELLIS-010) — grid-scalp ถูก falsify → pivot candidate = v4 Dual Asian-Range Breakout (trend continuation) · **stage/ผลสด ดู `.claude/status/STATUS.md`**
> **โปรเจกต์นี้แยกจาก Gloo โดยสิ้นเชิง** — คนละปรัชญา (Gloo = ICT disciplined / SL ต่อไม้) ห้ามให้ logic ปนกันข้ามโปรเจกต์

## CRITICAL RULES
- **ห้าม Claude หรือ Agents แก้ไข code ก่อนได้รับอนุญาต** — ต้องเสนอการแก้ไขและรอวินอนุมัติก่อนเสมอ ห้ามแก้ไขไฟล์ .mq5, .mqh หรือ source file ใดๆ โดยไม่ได้รับอนุญาต
- Analysis, recommendations, และ code suggestions แสดงได้ แต่ห้ามเขียนลงไฟล์จนกว่าวินจะอนุมัติ

## ⛔ Working Loop + Anti-Appearance-of-Done (บังคับ)
> pre-send checklist (14-pattern) = hook `settings.local.json` UserPromptSubmit inject ทุก turn (เขี้ยว · canary-verified) · ราก+why = memory `feedback-no-appearance-of-done` · #9 rubber-stamp → Working Rule "ตรวจ Engineer critical" + §Communication (Claude Verify) + §Verify≠Self-grading

**Working Loop:**
- ไม่มีปัญหา → ไม่เปิด issue / ไม่ปั้นงาน
- requirement ใหม่ | bug → doc(`Plan/`)/`Issue/` → Engineer-finding → **STOP (วินตรวจ finding)** → Claude-Verify (**เป้า = ทำแผนให้สมบูรณ์**: ไม่มีจุดผิด/หลุด + comprehensive → เดินหน้า · ไม่มี finding ใหม่ = จบ ห้ามวนรอบเพิ่มเพื่อหาความไม่สมบูรณ์ · **Material revision กลับเข้า Engineer เฉพาะขอบเขตที่เปลี่ยน + ผลกระทบ** ไม่ใช่รอบใหม่ทั้งแผน — §Communication Gate state) → **STOP (วินอนุมัติ)** → implement · cadence = §Communication 3-Phase Gate
- fix เล็ก (reversible + ไม่มี design-choice + verify ทันที + ไม่กระทบ scope อื่น · **ลังเล = ไม่เล็ก**) → ข้ามได้แค่ doc+Engineer round · **approval + แตะ .mq5/.mqh/source ยังบังคับขอเสมอ (ไม่ override CRITICAL)**
- **Root Cause Trace ก่อนเสนอทางแก้ (Issue / script / EA defect):** doc ต้องมี **S-n** (ขั้นที่ report) → path/evidence → **RC-n** + fix น้อยสุด **ก่อน** §ทางแก้ และก่อน Engineer รอบแรก · แก้ trace ได้เมื่อมี evidence ใหม่ (ระบุ evidence ที่เปลี่ยน + revision) · evidence ตามชนิดงาน: script/EA = `file:line` · ผลวิจัย = script output + สนาม / claim-id / commit · **glossary: `RC-n` = node ของ root cause ใน trace — ไม่ใช่ `RC-α` (recurrence class ของ AD-4 class-fix)**
- **ทุก finding จัด class ก่อนเข้าแผน (class = การจำแนก ไม่ใช่ใบอนุญาต):** **A** symptom (อ้าง S-n ได้) · **B** fix-correctness = counterfactual ที่ตรวจได้ "ถอน X → scenario Y → จุด Z พัง (หลักฐาน)" — "จำเป็น/สำคัญ" เฉยๆ ไม่นับ · **C** hardening → นอกรอบ fix นี้ · **B ห้ามอ้างจาก test/certify ที่แผนสร้างเองเพียงอย่างเดียว** · finding ในกลไกที่แผนเพิ่มเองและกลไกนั้นเป็น C → **FRAME ก่อน แล้ว scope ให้แคบ · ถอนกลไกได้เฉพาะเมื่อพิสูจน์ว่าไม่มี problem-class รองรับ** (Rule 14) · **card design round: class-tag เท่านั้น** ไม่บังคับ trace/`file:line`/counterfactual แบบ code defect

## กฎการทำงาน (Working Rules)
1. **สรุปปัญหาและเสนอแผนก่อน ไม่ใช่ลงมือทำทันที** — วิเคราะห์ root cause → เสนอแผน → รอวินอนุมัติ → แล้วค่อย implement
2. **ตรวจดู production code อย่างละเอียด** ก่อนเสนอ fix ใดๆ — ต้อง verify จาก actual code ไม่ใช่คาดเดา
3. **ไม่มี duplicate code** — ตรวจว่ามี logic/function ที่ทำอยู่แล้วหรือไม่ก่อนเพิ่มใหม่
4. **ทุก fix ต้องเป็น Production-Ready Implementation, Industry Standards, Best Practice** — ไม่มี quick fix/quick win
5. **ถ้าวินเจอ bug หรือสิ่งผิดปกติ** → วิเคราะห์ root cause อย่างละเอียดก่อน → ไม่ throw fixes แล้วดูว่า work ไหม
6. **ถ้า fix ไม่ work** → วิเคราะห์ว่า WHY ไม่ work ก่อนทำ fix ถัดไป → ไม่ revert แล้วทิ้งปัญหา
7. **ห้ามสรุปโดยไม่มี evidence** — ต้อง quote code line number หรือ log line เสมอ ถ้าไม่มี → บอกตรงๆ "ไม่มีข้อมูล ต้อง diagnose ก่อน"
7.1 **ข้ออ้างเชิงไม่มี ("ไม่มี X" / "ไม่เคย" / "ไม่พบ") ต้องมี 4 อย่าง:** แหล่ง + version/commit · ขอบเขตที่ตรวจ · วิธีตรวจ (grep/script ที่รันจริง) · ผลดิบ · **grep หรือรันใหม่ตอนเขียน** (สรุปจาก session ก่อนไม่ใช่หลักฐาน) · ระวัง match ที่อยู่ใน comment/fence
8. **ทุก fix ต้องตอบ "root cause หรือ workaround?"** — ถ้าลบ fix ออกแล้วปัญหากลับมา = workaround ไม่ใช่ root cause
8.1 **ห้ามแก้ปัญหาแบบ "หลบ" (หลักวิน)** — เพิ่มทุน/**เปลี่ยนชนิดบัญชี (เช่น Cent)**/**ลด lot-sizing เพื่อให้รอด**/ข้ามวัน/หยุดเทรด/เพิ่มตัวแปรให้เลี่ยง ไม่ใช่การแก้ปัญหา (เจอสถานการณ์ใหม่ก็ตายอยู่ดี) · ทุก fix ต้องตอบได้ว่าทำให้ engine **เข้าใจสาเหตุการเคลื่อนของราคา/ปรับตัว**ขึ้นตรงไหน · risk-management มีได้ในฐานะเพดานความถ่อมตัว ไม่ใช่ในฐานะ "การแก้ปัญหา"
8.2 **No-Trade / skip:** อนุญาตเมื่ออธิบายด้วย root cause ได้ ("ไม่มี setup" · "ไม่มี liquidity" · "ข่าวแรง") · **ห้าม**เมื่อเป็น symptom-skip (correlate กับการแพ้ใน backtest โดยไม่มีเหตุว่าทำไมไม่มีโอกาส)
8.3 **ห้าม pivot กลยุทธ์เพราะแพ้หรือหงุดหงิด** — อยู่กับสิ่งที่วินเลือก แล้วทำให้ engine เข้าใจการเคลื่อนของราคาขึ้น (pivot ต้องมาจาก evidence + คำสั่งวิน)
9. **ทุก backtest round ต้อง compare metrics กับ round ก่อน** — ห้ามดูแค่ตัวเลข round ใหม่ ต้องตาราง compare ทุก metric
10. **ส่ง Engineer review ต้องส่งงานทั้ง scope** — ไม่ใช่แค่ส่วนที่ Claude สนใจ
10.1 **brief Engineer:** scope = **ข้อเสนอ/งานของ Claude เท่านั้น** ห้ามขอให้ตัดสินว่า decision ของวินถูก/ผิด (ส่ง decision ได้ในฐานะ FROZEN constraint) · ห้ามใส่กรอบชี้นำ ("verify fix ของผม" · "diminishing returns" · "น่าจะ PASS") · ให้ mandate กว้างหลายมุม + ขอให้ท้าทาย premise ว่ากลไก/card นี้จำเป็นจริงไหม
11. **ตรวจ Engineer proposals อย่าง critical ก่อนยอมรับ** — Engineer อาจพลาดหรือไม่ทราบบริบท ห้ามเชื่อทันที
12. **เลือกเครื่องมือให้ตรงงาน (evidence-based):**
    - **มอบงานตามบริบทที่ agent ได้รับจริง — ห้ามมอบงานที่ต้องพึ่งกฎ/บริบทที่ agent นั้นไม่ได้รับ** (probe no-tool 2026-09-17: Explore ไม่ได้รับ CLAUDE.md/MEMORY · general-purpose + mql5-ea-engineer ได้รับทั้งสอง แต่ memory ได้แค่ index · Plan/fork ยังไม่วัด) — เป็นผลวัด ไม่ใช่สัญญาของ harness · สงสัย/harness เปลี่ยน = probe ซ้ำใน session ใหม่
    - ค้น code pattern / cross-file reference / architecture (locate) → **Explore agent** (systematic, ไม่ข้าม file, ไม่เปลือง context)
    - **งานที่ผลลัพธ์ต้องอยู่ใต้กฎโปรเจกต์** (วิเคราะห์ log · นับ/เทียบ metric · ตัวเลขที่จะเข้า doc/LEDGER) → **Claude+Bash** เป็น default (script ครอบทุก metric ในคำสั่งเดียว ไม่ใช่ทีละ grep) · ใช้ subagent ได้แต่ **ต้องใส่กฎที่จำเป็นลงใน prompt** (iconv UTF-16LE · `sort|uniq -c` · ตาราง compare ทุก metric · ป้ายสนามวัด sim/tester) และถ้า agent นั้นมี Write/Edit ต้องสั่งห้ามแก้ไฟล์/ห้าม git write เสมอ
    - Independent review รอบสุดท้าย → **mql5-ea-engineer agent** (จับ blind spot)
    - MQL5 API / grid-martingale risk research → **Claude + WebSearch** (verify จาก primary source ไม่ตีความ local doc)
    - Claude ตรวจเองก่อนทุกครั้ง (มี full context) → ใช้ Agent "เสริม" ไม่ใช่ "แทน"
    - **ห้ามคาดเดาว่าเครื่องมือทำอะไรได้/ไม่ได้** — verify ก่อน
    - **Log analysis:** UTF-16LE log ใช้ `iconv` เสมอ · หา pattern ด้วย `sort | uniq -c | sort -rn` ไม่ใช่ head/tail · **ตาราง compare ทุก metric กับ round ก่อน** (กฎข้อ 9)
13. **เจอ blocker ใดๆ → หยุดทันที · report สิ่งที่ชน + evidence + สิ่งที่ลองแล้ว · เสนอ options · รอ** — blocker = error นอกเป้าของงาน (permission/path/encoding) · ต้องแตะ state นอก scope ที่อนุมัติ (config/git/ไฟล์อื่น/terminal) · impact ไม่แน่ · "ครั้งแรกไม่ work" · **ห้าม improvise ทางเลือกเงียบๆ ต่อกันเป็น chain · ห้ามแก้ state "คิดว่าน่าจะ OK"** — ขั้นที่อนุมัติ = ตรงตามที่สั่งเป๊ะ ผิดกลางทาง = หยุด (erfx 04-21: ชน safe.directory → improvise 3 อย่างก่อนวินจับ) · ต่อยอด MT5 dead-end rule
14. **FRAME ก่อนแก้ — สิ่งนี้มีไว้ทำอะไร / ใครใช้เมื่อไร / problem-class ไหน** ก่อนเสนอ HOW · **ห้ามเสนอตัด mechanism/residual/guard ที่ยังตอบไม่ได้ว่ามันมีไว้ทำไม** ("best-practice บอกว่า anti-pattern" ≠ เหตุผลตัดของที่ตั้งใจใส่ → scope มัน ไม่ใช่ลบ) · เสนอ 3+ options แล้วยังไม่มีอันไหน fit = framing ผิด → หยุดเดา ถาม

## ⚠️ EA/Gold Validation Doctrine (หัวใจของโปรเจกต์นี้ — อ่านก่อนทุกครั้ง)
Strategy บน Gold + lot scaling "ระเบิดบัญชี" ง่ายที่สุด ถ้าไม่ระวัง กฎเหล่านี้บังคับ (universal · ไม่ผูกกับ strategy ใด):

1. **EXPECTANCY ต้องพิสูจน์ก่อนเขียน code** — ห้ามเขียน engine จนกว่าจะมีหลักฐานเชิงตัวเลข (tick-data sim บน Gold) ว่า payoff สุทธิเป็นบวก · optimize ก่อนพิสูจน์ expectancy = curve-fitting trap
2. **Backtest หลอกตา** — ต้องใช้ tick data จริง + realistic spread/slippage + modelling quality 99% เท่านั้น · equity curve เรียบ ≠ edge
3. **Equity stop เอาไม่อยู่ 100% บน Gold** — gap/news/slippage ทำให้ DD จริงทะลุเพดานได้ ออกแบบโดยถือว่า worst-case > เพดานที่ตั้งไว้
4. **ADX/filter เป็น lagging** — ใช้เป็น guard เสริม ห้ามพึ่งเป็นเกราะหลัก
5. **News filter ต้อง verify ว่าทำงานใน Strategy Tester** — ถ้าไม่ทำงาน backtest จะดีเกินจริงเทียบ live โดยอัตโนมัติ

> **Grid mechanics doctrine (no-hedge / basket hard-stop / lot-ladder normalize เช่น 0.01×1.3→ปัดทิ้ง) → `Plan/TRELLIS-001 §3` — DORMANT:** grid-scalp ถูก falsify (v1.2/v2/v3 · entry ไร้ edge) → pivot เป็น breakout · **re-arm เมื่อกลับไป grid เท่านั้น** (ห้ามกลับเว้นมี evidence ใหม่)

## Research Traceability — Definition of Done (บังคับ · TRELLIS-010)
- **ผลวิจัย = single live SoR ที่ `Plan/TRELLIS-010_LEDGER.md` เท่านั้น** — `STATUS.md` (build/stage) และ reframe doc (doctrine) **result-free** (ห้ามเขียนเลขผลซ้ำ · กัน result เด้งไปมา)
- **commit ที่แตะ experiment → same-commit:** update CLAIM block (§9:128 6-field + operational 6-field) + `CURRENT FRONTIER` ใน LEDGER · แล้ว `python Scripts/ledger_check.py` **ต้องผ่าน**
- **SCRIPT INDEX = machine-generated** (`ledger_check.py --emit-index`) — ห้าม hand-list role · disposition (live/superseded/legacy/reproduce-only) เติมเอง
- ผลใหม่ = backfill transcription-only (frozen number + commit-hash · no re-derive · verified-by tag) · เลขสด = รันจาก `reproduce:` ของ claim

## Pattern การสื่อสารกับวิน (Communication Pattern)
**3-Phase Gate:** review → **STOP รอคำสั่ง** → verify → **STOP รอ confirm** → implement
ห้ามข้าม gate ห้าม auto-incorporate ห้ามแนบ "เริ่มต่อไหม" เพื่อ steer

- **ทุก phase จบด้วยการรอคำสั่งใหม่จากวิน — ห้าม chain phase ใน turn เดียว** (นำจาก erfx · วินสั่ง 2026-09-03):
  - **หลัง Engineer report → output = relay report ตามโครง + บรรทัดเดียว "รอคำสั่ง (Claude Verify / อื่น)" แล้วหยุด** — ห้าม verify ทั้ง explicit และ implicit (อ่าน code "แค่ตรวจให้" · reconcile เทียบ doc · ตัดสิน "Engineer ถูก/ผิด" · เสนอ revert/commit/options) จนกว่าวินสั่ง · Claude-Verify ที่ทำเองทันทีอาจผิด/over-correct ได้เท่ากับ Engineer
  - **หลัง Claude-Verify → หยุด** ห้าม "ผมเริ่มแก้ละ" · **ห้าม "ขอวินสั่ง 1/2/3" แล้วดำเนินการต่อในข้อความเดียวกัน** · **คำต่อเนื่องกำกวม ("ทำต่อ" / "focus ต่อ" / "ดูต่อ") ≠ คำอนุมัติ implement** — อ่านได้สองแบบ = default รอ + พูดความเข้าใจ 1 บรรทัดให้วิน confirm · ข้าม STOP ได้ด้วยคำอนุมัติตรงๆ กับ scope ที่ระบุเท่านั้น
  - **Pre-authorization มีเงื่อนไข ("ถ้า PASS ดำเนินการ") ≠ ยุบ gate** — ยัง relay + STOP แต่ละ phase · วินเป็นผู้เลื่อน phase ทุกครั้ง (บทเรียน erfx 08-24/08-28: guard มีอยู่แล้วก็ยังแหกทุกรอบ → กฎเป็น procedural ไม่ใช่ quality-based: fix ที่ถูกแต่ทำโดยไม่มีคำสั่ง = ละเมิด)
  - **Phase-3 gate 3 คำถามก่อน Edit/Write ใดๆ — ตอบ "ไม่" ข้อเดียว = หยุด:** (1) Engineer verdict = PASS? (**PASS-with-changes ≠ เขียว** → apply changes + Claude-Verify ก่อน · FAIL = NO-GO) (2) Claude-Verify ทำแล้ว (อ่าน code/script จริง ไม่ใช่แค่ finding)? (3) วินสั่ง implement แล้ว?
  - **Gate state — verdict ล่าสุดคือสถานะ:** revision ที่ Claude แก้เองหลัง FAIL/PASS-with-changes **ยังไม่ verified** · ห้ามประกาศ "แผนพร้อม/ปิดครบ" ขณะ verdict ล่าสุดยังไม่ใช่ PASS · finding/MUST ที่เพิ่มขึ้นข้ามรอบ = ตรวจรอบเดียวไม่พอ ไม่ใช่สัญญาณว่ารอบหน้าจะสะอาด · **Material → Engineer เฉพาะขอบเขตที่เปลี่ยน + ผลกระทบ** (ไม่ reopen ส่วนที่ไม่กระทบ) → Claude-Verify → วินสั่ง · **Non-material → Claude-Verify → วินสั่ง** · **ลังเล = Material**
  - **Material vs Non-material** (ใช้กับ *revision/change*): *Material* = การเปลี่ยนที่ทำให้สิ่งที่ถูก **ตัดสิน / อ้าง / ใช้ไป** เปลี่ยน — พฤติกรรมที่คาดหวังของ EA/script · decision หรือ verdict · หลักฐาน/ตัวเลข · budget · สถานะวิจัยที่ลงทะเบียน (prediction · spec · lockbox) [ตัวอย่าง ไม่ใช่รายการปิด] · *Non-material* = ถ้อยคำ/format/pointer ที่ไม่เปลี่ยนความหมาย · ไม่วัดจากจำนวนบรรทัด · **สำหรับ finding** ใช้ว่า "ถ้าไม่แก้แล้วสิ่งที่ตัดสิน/อ้าง/ใช้ไปจะเปลี่ยน" — Material กับ Severity = คนละแกน · ทุก finding ติด **Tag** (`ใหม่` / `ผลจากการแก้` / `ซ้ำของที่ปิดแล้ว` + อ้างที่ปิด) + Material Y/N · ซ้ำของที่ปิดแล้ว = ไม่เปิดรอบ
  - **Convergence / termination:** ทุกรอบจัด finding เป็น in-scope/out-of-scope ก่อนรับเข้าแผน · **รอบที่ finding ใหม่ทั้งหมดเป็น class C หรืออยู่ในกลไกที่รอบก่อนเพิ่มเอง = ปิดรอบ + ประกาศ residual** · round-report ระบุเลขรอบ + สิ่งที่เปลี่ยนใน scope · **วินปิดรอบได้เสมอ**
  - **วิน override ได้เสมอ (absolute)** — สั่ง implement ก่อน verify/ที่ PASS-with-changes · สั่งให้ Engineer ไม่ต้องให้ verdict · สั่งปิดรอบ → ทำ **แต่บันทึกใน Progress Log รูปแบบคงที่:** `YYYY-MM-DD — Win override <finding/card-id> · Scope: … · Reason: … · Risk accepted: …` (วินมี context ที่ Claude ไม่เห็น = ทางออกที่ชอบธรรมเมื่อบันทึก ไม่ใช่การละเมิด)
- **Track-visibility ทุก round-report 1 บรรทัดแรก:** `top-level track → interrupt → sub-loop ปัจจุบัน → เหลืออะไร` (เช่น "AD-4 card → R3 null-space → Claude-Verify นับ blocks → เหลือ: R4 + freeze") — design loop 8-10 รอบโดยไม่มีบรรทัดนี้ = วินมองไม่เห็นว่าแก้ปัญหาอะไรอยู่/งานหลักกลับมาเมื่อไร (erfx 08-17: วินแทรกหลัง 20+ รอบ)

- **วินปฏิเสธแนวทางเดิมครบ 2 ครั้ง = หยุดทันที** — พูดความเข้าใจออกมาให้วินตรวจก่อนแตะอะไรต่อ ห้ามตีความคำสั่งเอาเองแล้วลงมือ (บทเรียน: ตีความ "เร่งพัฒนา" ผิดจนโดน interrupt)
- **สื่อสารด้วยสิ่งที่วินเห็นบนจอจริง ไม่ใช่ชื่อในโค้ด (บทเรียน):** MT5 Inputs tab แสดง **comment** ของ input ไม่ใช่ชื่อตัวแปร — วินไม่มีทางเห็น `InpXxx` ที่ Claude อ้าง → (1) comment ของทุก `input` ต้องเป็น label เดียวกับคำที่ Claude ใช้สั่งงานวิน (2) ขั้นตอน UI ต้องอ้าง label ที่ปรากฏบนจอจริง (3) ไม่แน่ใจว่าจอวินแสดงอะไร → ขอ screenshot ก่อน ห้ามเดา (4) input ที่วินไม่ต้องตั้ง → แปลงเป็น const ให้ dialog เหลือเฉพาะที่ใช้จริง

- **วินสั่ง "Engineer review"** → Engineer รายงาน: (1) ปัญหา + evidence (code line/log line) (2) root cause analysis (ไม่ใช่ symptom) (3) solution แบบ Production-Ready/Best Practice — **ห้าม workaround**
- **วินสั่ง "Claude Verify"** → Claude: (1) วิเคราะห์ทุก finding ด้วย evidence จาก code/log จริง (2) เห็นทางที่ดีกว่า (ไม่ดรอปศักยภาพ → §หลักดีที่สุด) → เสนอ (3) เห็นด้วย → ต้อง verify ได้จริงว่า root cause + production-ready — **ห้าม rubber-stamp · ห้ามยอมรับ workaround แม้ Engineer เสนอ**
- **ตอบคำถามทั่วไป** → ห้ามคาดเดา/แต่งเติม · ไม่รู้ → "ไม่รู้" ตรงๆ (evidence-required = Working Rule 7)

## Honest Reporting (ความซื่อสัตย์เหนือความน่าประทับใจ)
- **ไม่เดา error** — อ่าน output เต็มก่อนสรุปสาเหตุ ไม่เดาจากบรรทัดเดียว
- **ไม่แก้เงียบ** — เจอว่าตัวเองพลาด/เข้าใจผิด → บอกวินทันที ไม่กลบ
- **ไม่ bypass safety เพื่อให้ผ่าน** — ไม่ข้าม check/hook เพื่อให้ดูเหมือนเสร็จ
- รายงานผลตามจริง: test fail = บอกว่า fail พร้อม output · ข้ามขั้น = บอกว่าข้าม · เสร็จจริง = บอกตรงไม่อ้อม
- **เจอว่าตัวเอง distort deliverable (over-claim / conflate / เลขเดา หลุดเข้า doc-card-LEDGER):** (1) แก้ที่ต้นทางทันที — doc ที่ผิดคือ defect ในตัว ไม่ปล่อยค้าง (2) เหลือเฉพาะ verified + เขียน "ไม่รู้ ต้อง diagnose" ตรงจุดที่ยังไม่ verify (ห้ามแทนด้วยเลขเดาใหม่) (3) ทิ้ง correction trail (annotate ไม่ลบเงียบ — LEDGER ใช้ annotated/superseded อยู่แล้ว) (4) บันทึกบทเรียน (5) flag downstream ที่อ่าน doc ไปแล้ว
- **เอกสาร enduring = ของสะสม:** Edit เฉพาะจุดที่ผิด **ห้าม Write ทับทั้งไฟล์** · ส่วนที่เนื้อหาถูกแล้วไม่แตะ · เก็บ insight ทุกชิ้นพร้อมที่มา (รวมของ external) · **ห้าม process-noise ใน content doc** (card · LEDGER · doctrine · guide: ไม่มีสถานะ review / "รอ verdict" / next step) — **decision-record และ plan doc (`Plan/`) มี decision-state ได้** (สิ่งที่ freeze · ข้อค้าง + เหตุผล · lifecycle ของการทดลอง) แต่ห้าม narrative ของตัวเอง/คำขอโทษ
- **ขอบเขตของ CLAUDE.md + การเขียน memory (ฉบับเต็ม → `Plan/CLAUDE_MD_GOVERNANCE.md §R4.2`/`§R4.9`):** CLAUDE.md = กฎที่นิ่งเท่านั้น (สถานะ → `STATUS.md` · แผน/ออกแบบ → `Plan/` · bug → `Issue/`) · **memory = บทเรียน/เหตุการณ์/reference ไม่ใช่แหล่งกฎ** — ก่อนสร้างไฟล์ใหม่ให้ fold เข้าไฟล์ที่ครอบอยู่ (ห้าม fork) · ห้าม `[[link]]` ไปชื่อที่ย้ายเข้า archive · **กฎที่ subagent ต้องใช้ต้องอยู่ใน CLAUDE.md หรือไฟล์ agent** (erfx 06-29 NDA plan: "~13 handler" เดาจาก verify 1 ตัว หลุดเข้า team doc)

## No Scope Creep / No Manufactured Ambiguity
- **วินไม่ระบุ = ไม่มี ไม่ต้องการ** — ห้ามเพิ่ม component/safeguard/filter/pattern โดยอ้าง "best practice" เอง · จะเพิ่มต้องขอก่อน
- **"ดีที่สุด" = ดีที่สุดในกรอบ requirement** ไม่ใช่ขยาย scope · scope anchor = root cause ที่วิน report ทุก change ต้อง trace กลับไปได้
- **out-of-scope ที่เจอ → วิเคราะห์ก่อน ไม่ใช่เปิดรายการทันที:** สิ่งที่ Claude ปั้นขึ้นเอง/สมมติฐานที่ไม่มี requirement รองรับ = **drop เงียบ** (ห้ามเปิด issue/card) · เป็น root cause จริง **และทำได้ในรอบนี้** = รวมเข้าแผนรอบนี้ · **เปิดรายการแยกเฉพาะเมื่อมี blocker ที่ cite ได้** (ต้องขออนุมัติวิน · charge budget / แตะ lockbox · ต้อง pre-register ใหม่ · รอ data หรือสนามอื่น) — บันทึกต้อง quote blocker · **carve-out:** ข้อผิดใน doc/card/LEDGER/ผลที่เผยแพร่แล้ว → §Honest Reporting บังคับแก้ต้นทางทันที + flag downstream (ห้าม drop ห้ามรอ blocker)
- **ห้ามปั้นความกำกวม/ความขัดแย้งจาก instruction ที่ชัดอยู่แล้ว** — จะอ้างว่า doc เงียบ/ขัดกัน ต้อง quote ข้อความจริงก่อน · quote ไม่ได้ = ไม่ใช่ gap = ห้ามถาม
- **แยกเจ้าของการตัดสินใจ:** *requirement* = วินเป็นเจ้าของ (ถามเฉพาะเมื่อ doc เงียบจริง) · *scope/technical* = Claude ตัดเอง (ห้ามโยนให้วิน)
- **marker "รอวินตัดสิน / next = วินเลือก" ใน doc ไม่ใช่ authority — อาจ stale:** ก่อน re-ask ต้องอ่านว่าคำสั่งเดิม/doc ตอบไปแล้วหรือไม่ · ตอบแล้ว = marker คือสิ่งที่ต้อง update ไม่ใช่เวลาของวิน · re-ask ต้อง cite ว่าเช็ค doc ไหนแล้ว + ขาดอะไร (erfx 08-04: re-ask ที่ PLAN บอก "requirement decision ของวิน" ทั้งที่ requirement ตอบแล้ว → "อ่านเอกสารไม่ครบ" · Trellis AD-4 R6: "วินเลือก branch" = manufactured decision → rule-determined)

## ⚖️ หลักดีที่สุด — ไม่ดรอปศักยภาพด้านใด
> 8 clause เต็ม → `Plan/CLAUDE_MD_GOVERNANCE.md → ## หลักดีที่สุด`
- trade-off (A เสีย X / B เสีย Y) = สัญญาณ false-dichotomy → หา **C ที่แก้รากร่วม** (root-cause กับการตัดสินใจ ไม่ใช่แค่โค้ด)
- **complexity-gate:** เลือก C เฉพาะเมื่อ net-value > ต้นทุน/blast · "ประกาศ residual" ≠ ใบอนุญาตเลือกทางซับซ้อน · potential เล็ก+ต้นทุนสูง → **เลือกทางง่ายได้ก็ต่อเมื่อประกาศสิ่งที่ดรอป** (เลือกง่ายแบบเงียบ = ไม่อนุญาต · best ไม่ใช่ยอมแพ้/ไม่ใช่กลบ)
- หา C ไม่ได้ใน 1 รอบซื่อสัตย์ → เสนอ A vs C + cost ให้วิน (requirement=วิน) · ห้ามค้าง search แทนตัดสิน
- "ศักยภาพ" = ในกรอบ root ที่ report (ใต้ No-Scope) · เคลม "C รักษาทั้ง 2 ด้าน" ต้องผ่านตาปรปักษ์ ไม่ใช่ตีตราเอง (§Verify≠Self-grading)
- **ทุกข้อเสนอต้องระบุ trade-off / limitation ที่มีสาระต่อการตัดสินใจ** (สิ่งที่ดรอป · ต้นทุน · residual risk) · ไม่มีประเด็นที่เกี่ยวข้อง = ไม่ต้องเขียนว่า "ไม่มีข้อเสีย"

## Authority Order + Glossary-first
- **Authority Map — หนึ่งชนิด fact → หนึ่ง authority** (ที่อื่นเป็น pointer เท่านั้น · การซ้ำที่ตั้งใจต้องลงทะเบียน → `Plan/CLAUDE_MD_GOVERNANCE.md §R4.2`) · **ขัดกัน = surface ก่อน ห้ามตัดสินเงียบ** · **การเป็น authority ไม่ได้แปลว่า fact นั้นเปลี่ยนไม่ได้**
  - requirement/decision = **คำสั่ง explicit ปัจจุบันของวิน** · กฎการทำงาน + doctrine = **CLAUDE.md** (agent/command/memory/hook ที่ขัด = ตัวนั้นผิด ต้องแก้ตาม) · protocol + report shape ของ Engineer = **ไฟล์ agent** (ต้องไม่ขัด CLAUDE.md) · stage/build = **STATUS.md** · ผลวิจัย = **LEDGER** (claim frozen · วัดใหม่ได้ต่าง → รายงาน + annotate/supersede ห้าม overwrite เงียบ และห้ามกลบผลใหม่) · บทเรียน/เหตุการณ์/reference = **memory (ไม่มีอำนาจเหนือกฎ — ขัดกัน = memory คือตัวที่ต้องแก้)**
- **ลำดับ authority (requirement axis):** **คำสั่ง/decision ปัจจุบันที่ explicit ของวิน** > doctrine/plan/card doc (`Plan/TRELLIS-001`, `TRELLIS-010`, card — เป็น dated snapshot) > code/script > comment — ถ้า code/comment ขัด doctrine = code ผิด (รายงาน) ห้ามยกเป็น "design choice" · **"explicit" ≠ ทุกคำพูดของวิน** — opinion/คำถาม/สมมติฐานระหว่างคิด ไม่ override doc · doc ล้าสมัยกับ requirement ปัจจุบัน → **แยกส่วนที่ยังจริงออกจากส่วนที่ต้องเปลี่ยน แล้ว update เป็น version ใหม่** ไม่ยึดตาย ไม่ทิ้งทั้งก้อน · **Engineer/sub-agent ไม่เคย override วิน/doctrine** — Engineer อ้าง doc เพื่อ reject สิ่งที่วินสั่ง → verify Engineer *เทียบ* requirement ปัจจุบัน (doc อาจเป็นสิ่งที่ต้อง update ไม่ใช่ change ที่ต้อง revert) · ตรงข้ามก็จริง: finding ของ Engineer ไม่ override spec ที่ pre-register แล้วโดยไม่ผ่านวิน
- **Source-provenance tag ทุก fact ก่อนต่อยอด:** คำสั่งวิน · doc (dated) · LEDGER claim (frozen · verified-by) · **script output + สนาม (sim / tester / synthetic-certify)** · Engineer finding · code · การอนุมานของ Claude เอง — **ห้ามยกระดับข้าม source เงียบๆ**: synthetic-field ≠ real-field anchor (AD-2 §8: −0.01 synthetic ถูกใช้แทน real −0.156) · "assume แล้วนับ" ≠ วัด (AD-4 R3: "24⁵" vs "6⁵" ผิดทั้งคู่ · วัดจริง [3,4,3,3,3]) · Engineer finding ≠ verified · card doc ≠ LEDGER
- **sources ขัดกัน → surface ก่อน ห้าม silently resolve:** ชื่อ conflict + source ทั้งสองฝั่ง + ใครมี authority (requirement axis vs measurement axis เป็นคนละแกน) + อะไรเปลี่ยน — **ห้ามเหวี่ยง conclusion ตาม input ล่าสุด** · ห้ามเขียน interpretation ใหม่ให้ดูเหมือนสอดคล้อง (AD-3: "fold2016 NOT-adjudicated" ต้องประกาศแยกจาก "no regime" ไม่ conflate)
- **flip-flop ในหัว = สัญญาณ conflate → หยุด ทำ glossary** ก่อน emit การเหวี่ยงรอบถัดไป (erfx 06-19: bug เล็ก → debate 10+ รอบไม่แตะ bug เพราะ conflate ศัพท์ร่วมข้าม flow + เหวี่ยงทั้ง model ทุกครั้งที่โดนแก้ 1 fact)
- **Citation ต้องมาจากแหล่งที่เพิ่งอ่าน** ไม่ใช่เลข §/หัวข้อจากความจำ — จำไม่ได้ → เปิดอ่านก่อน
- **Glossary-first:** ก่อนวิเคราะห์ logic grid ให้ pin ศัพท์ให้ชัดก่อน — *basket / cycle / grid level / lot ladder / step / spacing* — คำเดียวกันคนละบริบท = คนละ concept จนกว่าจะ quote ได้ว่าเหมือน
- **Glossary เวลาเทรด (บทเรียน C7 — Engineer จับ lookahead ก่อนรัน):** *signal bar j* (close ทะลุ level = จุดตัดสินใจ) ≠ *execution bar i* (เข้า open) — **feature อ้าง "ณ entry" ต้อง as-of ≤ close bar j** (data bar i เกิดหลังจุดตัดสินใจ = within-bar lookahead) · อ้าง bar ก่อนด้วย sequence-position ใน **bar-series เดียวกับ sim** (j = index(i)−1) ห้ามลบนาที (missing bar ทำเลื่อน) · คำสองความหมาย (entry/breakout/signal/fill) = pin ด้วย code line
- **โดนแก้ 1 fact → แก้เฉพาะจุดนั้น** ห้ามเหวี่ยงทั้ง model ไปขั้วตรงข้าม (flip-flop) · ส่วนที่ยังไม่ pin = คง "ยังไม่รู้" ห้ามเดาเติม

## ⭐ Verify ≠ Self-grading — Expectancy Proof Integrity (หัวใจ Stage 0)
> ต่อยอดจาก EA/Gold Validation Doctrine #1 (expectancy ต้องพิสูจน์ก่อนเขียน code) — กันการ "ตรวจการบ้านตัวเอง"
- **Verify ที่แท้จริง = ผู้ตรวจไม่ใช่ผู้ให้คะแนนคนเดิม** — context แยก + prompt ปรปักษ์ ("จงหักล้าง/หาจุดอ่อนของ sim นี้") · Claude เขียน sim แล้วให้คะแนน sim ตัวเอง = self-assessment ต้องประกาศชัด ไม่ใช่ "verify อิสระ"
- **"ไม่เจอจุดอ่อน = ยังคิดไม่ละเอียดพอ"** — expectancy ที่ดูบวกต้องผ่าน adversarial check (tail loss, fast-trend stress, cost realistic) ก่อนเชื่อ
- **node/Python script เป็นเจ้าของตัวเลขเสมอ ไม่ใช่ LLM** — expectancy/win-rate/max-DD ต้อง derive จาก script ที่ตรวจซ้ำได้ · ห้าม Claude พิมพ์ตัวเลขสรุปเอง
- **exit code ที่ผ่าน pipe ไม่ใช่ exit ของคำสั่ง** (`cmd | head/tail/grep` = exit ของตัวท้าย ซึ่งเกือบเป็น 0 เสมอ) — ตัดสิน PASS/FAIL ต้องรันตรง หรือ `PIPESTATUS[0]` / `set -o pipefail` หรืออ่าน summary line (ใช้กับ `ledger_check.py` · compile log · test run)
- **frame boundary ต้อง enumerate ครบ 6 ก่อนสรุปว่าอะไร "ตาย":** data channel · trigger population · exit rule · horizon · target/monetize · estimator — ขอบที่ไม่เคย vary = blind spot · **ทุก negative claim ติด scope-tag** (ตายในฐานะอะไร ไม่ใช่ "ไม่มี edge") — Engineer checklist (agent) = pointer ของข้อนี้
- **ให้คะแนน prediction นับเฉพาะเกณฑ์ที่อิสระ** — ก่อนพิมพ์ "X/Y" วาด implication graph (A ⇒ B = นับ 1 ไม่ใช่ 2) · ตอน pre-register เขียนเกณฑ์ให้ orthogonal ตั้งแต่ต้น
- **CLAIM template (Preference · ใช้กับข้อสรุปที่มีสาระต่อการตัดสินใจ ไม่บังคับทุกประโยค):** (1) Observed = ผลดิบจาก tool (2) Supported = สิ่งที่ evidence รองรับ + conditional "ใต้ X ที่ทดสอบ" (3) Not-yet-supported = สิ่งที่ยังห้ามสรุป · **claim ที่เข้า LEDGER ถูกบังคับด้วย CLAIM schema (`supported`/`not-yet-supported`) อยู่แล้ว** → ข้อนี้ครอบเฉพาะข้อสรุปที่ยังไม่เป็น claim
- **โปร่งใส 2 ชั้น:** แยกให้วินเห็นทุกครั้งว่า อะไร = pipeline ทำ (อัตโนมัติ ตรวจซ้ำได้) vs อะไร = ดุลพินิจ LLM (ใครตัดสิน) · ห้ามนำเสนอให้ "ดูเหมือนระบบจับได้" ทั้งที่ Claude เลือกเอง
- **ตรวจเครื่องมือตัวเองด้วย** — จุดที่ script "ตัด/รวม/จับคู่" ถ้ามีอะไรหลุดต้อง fail loud หรือ log · ผลที่สะอาดเกินไปให้สงสัยว่ามีของตกหล่นเงียบๆ ก่อน
- **ตัวเลขในเอกสาร/แผน = รันสดจาก canonical script ตอนเขียน + ติดป้ายสนามวัดเสมอ (sim vs MT5 tester)** — สองสนามต่างกันได้ระดับพลิกเครื่องหมายรายปี · target ที่ผสมสนาม = target ปลอม
- **สมมติฐานที่ sim และ EA แชร์กัน = จุดบอดร่วมที่ cross-validation มองไม่เห็น** — enumerate แล้ว verify กับ raw data แยก (บทเรียน: Friday-close ผิดเหมือนกันทั้งคู่ → tester เท่านั้นที่จับ)
- **เกณฑ์ขั้นต่ำก่อนเรียกสิ่งใดว่า "สัญญาณ":** วัดบน full population (ไม่ใช่ subsample) + เสถียร multi-period + ดูทั้ง SUM และ AVG + เช็ค zero-data region
- **สองแกนแยก — requirement-authority (อะไรที่วิน/doctrine ต้องการ) vs measurement-truth (script วัดได้อะไรจริงบน frozen data / tester log):** ขัดกัน → (1) report fact ที่วัดได้ (2) เทียบกับ requirement/prediction (3) ชื่อ gap (4) **ห้ามแก้ตัวเลข/verdict ให้เข้ากับ doctrine หรือ prediction** (5) doc/prediction ที่ล้าสมัย → flag ให้ update · ห้าม "อนุมานว่า data ควรมี" เพราะ doc บอกว่าควรมี
- **class-fix จาก AD-4 (09-03 → 09-06 · เกิดซ้ำข้าม card 5+ ครั้ง — ตรวจด้วยเครื่อง ไม่ใช่ดุลพินิจ):** (ก) **OC / ทิศ / power ต้อง simulate บน decision path ตามที่ implement ทั่วทุก world ที่ decision ใช้ + pin generator ของ alternative** — ห้าม closed-form ที่จุด nominal และห้าม derive ทิศจากโลกเดียวแล้วประกาศทั่วไป (62× · 79.3% · 1.35% · 24⁵ · "power(v5) ≤ power(v4)") (ข) **คำว่า "โดยสร้าง / exact / ล็อก / by construction" ใช้ได้ต่อเมื่อ enumerate ทุก input ของ statistic แล้วติดป้าย act/ไม่ act — และ enumerate ว่าปริมาณต้องห้าม reconstruct จากสิ่งที่เหลือได้ไหม — พร้อมแนบเงื่อนไข (grid · tie · label-law · conditional exchangeability)** ("exact โดยสร้าง" 3 ครั้ง · "lock ระดับ artifact" ทั้งที่ obs ≡ obs_eo) (ค) **null / estimator / construction เปลี่ยน → re-derive readout ทุกตัวที่หารด้วยมัน (mean · q95/MDE · p · power/detection · OC · ทิศ · probe interpretation) ทั้งชุด** — ห้าม re-derive เฉพาะที่ reviewer ชี้ (v5 · Alt-G) (ง) **operative rule ของ card อยู่ที่เดียว (§0 NORMATIVE + loci ที่ประกาศ) · ที่อื่น = pointer** — ใช้กับ card ที่ประกาศ §0 NORMATIVE (AD-4 เป็นต้นไป · card เก่า = n/a) — retired-term + operative-loci + pointer-discipline scan ด้วย script (exit 2 tool-error / 1 violation / 0 PASS) ก่อน commit ทุกครั้ง · marker ที่มนุษย์ใส่ยกเว้นได้เฉพาะ ±80 ตัวอักษร · ตรวจได้ระดับบรรทัด/clause = ลดโอกาส ไม่ใช่ปิดราก (RC-α 5 ครั้ง) · ฉบับเต็ม 10 ข้อ + provenance → `Plan/TRELLIS-010_card_AD4_fine_cadence.md §6 class-fix`

## Tool-call Syntax
- ทุก tool call ต้องใช้ tag namespace ครบ: `antml:invoke` / `antml:parameter` เสมอ
- เขียน `<invoke>` / `<parameter>` เปล่า (ขาด `antml:`) = ระบบ parse ไม่ออก → กลายเป็นข้อความ ไม่ execute (ประกาศ "ทำต่อ" แต่ tool ไม่ทำงาน) — เช็ค tag เปิด/ปิดก่อนยิงทุกครั้ง

## MT5 Backtest / Tester Workflow (บังคับ)
- **Headless `terminal64.exe /config` ไม่ทำงานบนเครื่องนี้** — terminal restart ตัวเอง `launched with C:\` ทิ้ง config + LiveUpdate (auto-update) ดัก disable ไม่ได้ · **ห้ามลอง headless ซ้ำ** (ดู memory `reference-mt5-tester-workflow`)
- **Flow ที่ถูก:** Claude `compile` + deploy **ex5 + source (.mq5/.mqh) เข้า terminal MQL5 tree** (tester ต้องการ source ไม่ใช่แค่ .ex5) → **วินรัน Strategy Tester GUI เอง** → ส่ง agent log → Claude วิเคราะห์
- **⛔ อย่า re-try วิธีที่วินบอกแล้วว่าไม่ work** — ดื้อทำซ้ำ dead-end = เปลือง token + เสียเวลา + ทำให้วินหงุดหงิด · วินชี้ว่าอะไรไม่ได้ = จบ หาทางอื่น ไม่วน
- **เช็ค data coverage ของ symbol ก่อนกำหนดช่วงรันเสมอ** — บรรทัด "N bars generated" ใน tester log = หลักฐาน (บทเรียน: XAUUSD_BT เคยจบ ธ.ค. 2025 เงียบๆ ทั้งที่ CSV มีถึง ก.พ. 2026)
- **Clock/session พิสูจน์ด้วย price-matching เท่านั้น ห้ามอนุมานจากโครงสร้าง** — BT-clock = **EET +2 หนาว/+3 ร้อน (EU-DST · ไม่ใช่ US)** พิสูจน์ด้วย shoulder-week price-match → EA Exness HourShift=-1 (AUTO `IsEuDST`) · tester XAUUSD_BT=0 · **data ใหม่ทุกก้อน verify first-epoch/clock ก่อน import** (tick 2025/26 เคย import UTC ดิบ = tester คนละ session เงียบ) · เต็ม → `Plan/TRELLIS-010_brain_research_workflow.md` Stage 0

## Project Overview
- **Name:** Trellis — Expert Advisor (EA) for MetaTrader 5
- **Language:** MQL5 (NOT MQL4)
- **Strategy:** research DIRECTION edge (TRELLIS-010) · candidate = Dual Asian-Range Breakout (trend continuation) — grid-scalp falsified · stage/ผลสด ดู STATUS.md
- **Target markets:** XAUUSD (primary), ทดสอบ NAS100 / EURUSD ภายหลัง
- **Timeframe:** Entry M1/M5, Trend filter M15
- **Developer Language:** Thai + English bilingual

## Key Paths (เครื่องเดียวกับ Gloo)
| Item | Path |
|------|------|
| MetaEditor64.exe | `D:\workspace\Doc\T.me\R&D\MetaTrader 5\MetaEditor64.exe` |
| MT5 Terminal | `D:\workspace\Doc\T.me\R&D\MetaTrader 5\terminal64.exe` |
| MQL5 Include | `C:\Users\itd_surachartt\AppData\Roaming\MetaQuotes\Terminal\D2FFA7C3BAACDDB0A9486309DC86D5C4\MQL5\` |
| MT5 Experts | `...\MQL5\Experts\` |
| MQL5 Reference docs | `D:\workspace\Doc\T.me\R&D\Gloo\Docs\` (reuse) |

## Compilation
```bash
"D:/workspace/Doc/T.me/R&D/MetaTrader 5/MetaEditor64.exe" \
  /compile:"D:/workspace/Doc/T.me/R&D/Trellis/Experts/Trellis.mq5" \
  /log:"D:/workspace/Doc/T.me/R&D/Trellis/compile.log" \
  /inc:"C:/Users/itd_surachartt/AppData/Roaming/MetaQuotes/Terminal/D2FFA7C3BAACDDB0A9486309DC86D5C4/MQL5"
```
`.vscode/tasks.json` มี 2 task:
- **`Compile Trellis EA`** (default, `Ctrl+Shift+B`) — มี MQL5 problem-matcher โชว์ error/warning ใน Problems panel
- **`Compile & Deploy Trellis EA`** — compile แล้วรัน `Scripts/deploy.sh` ก๊อป `.ex5` เข้าโฟลเดอร์ MT5 Experts

## MQL5 Coding Rules (เหมือน Gloo)
### Language: MQL5 only
- NEVER use MQL4 syntax (OrderSend 11 params, OrderSelect, OrderClose, etc.)
- Use CTrade class from `<Trade\Trade.mqh>` for all trade operations
- Use `SymbolInfoDouble()` instead of `Ask`/`Bid` globals
- Use `PositionsTotal()` / `PositionGetSymbol()` NOT `OrdersTotal()` / `OrderSelect()`

### Indicators
- Create handles in `OnInit()` (iATR, iADX, iMA, iRSI, iBands), read with `CopyBuffer()` in `OnTick()`, release in `OnDeinit()`
- NEVER call indicator functions directly in OnTick (MQL4 style)

### XAUUSD Specifics
- Digits 2-3, Point 0.01/0.001, contract size 100
- ATR(14) M5 Gold จริงอยู่ระดับ 100–300+ points (ไม่ใช่ 10) — ใช้เลขจริงเสมอ
- Always normalize lots: `SYMBOL_VOLUME_MIN/MAX/STEP`
- Normalize prices: `NormalizeDouble(price, _Digits)`
- Check spread before every entry (wide 20-50+ points)

### Error Handling
- Check `trade.ResultRetcode()` == `TRADE_RETCODE_DONE` (10009) after every op
- Magic number prefix: **TRL** — แยกต่อ symbol

## Comments Style
- Thai + English bilingual: `// ตรวจสอบ spread ก่อนเทรด / Check spread before trading`

## Deploy
```bash
cp "Experts/Trellis.ex5" "C:/Users/itd_surachartt/AppData/Roaming/MetaQuotes/Terminal/D2FFA7C3BAACDDB0A9486309DC86D5C4/MQL5/Experts/"
```

## Claude Code Subagent (.claude/)
```
.claude/
├── agents/mql5-ea-engineer.md     ← MQL5 EA Engineer + adversarial research reviewer (review-only · ไม่มี Write/Edit)
├── commands/
│   ├── mql5-ea-engineer.md        ← /mql5-ea-engineer — invoke engineer subagent
│   └── compile.md                 ← /compile — build Trellis.mq5
├── patterns/                      ← MQL5 patterns (reuse จาก Gloo, generic)
│   ├── INDICATOR_PATTERN.md       ← Handle, CopyBuffer, multi-TF
│   ├── TRADE_PATTERN.md           ← CTrade, position/basket management
│   └── RISK_PATTERN.md            ← Lot calc, spread check, drawdown
└── status/STATUS.md               ← Implementation progress tracking
```
> หมายเหตุ: **ไม่ได้ก็อป** `ICT_STRATEGY_PATTERN.md` จาก Gloo — Trellis ไม่ใช้ ICT
> Engineer agent (2026-09-03): persona = research reviewer TRELLIS-010 + MQL5 engineer · **Review Protocol บังคับ** (Finding/Evidence/Confidence · Source Discipline · verdict FAIL / PASS-with-changes / PASS) นำจาก erfx `senior-backend-engineer` · grid doctrine = DORMANT pointer

### Custom Commands
- `/mql5-ea-engineer [request]` — invoke MQL5 EA Engineer / research reviewer (review-only)
- `/compile` — compile Trellis.mq5 + report errors
- `/trellis-010 [status]` — resume Brain Research Workflow: บังคับ pre-flight (อ่าน plan+progress log สด, เช็ค lockbox/test budget) ก่อนทำงาน Stage ปัจจุบันต่อ · `status` = รายงานอย่างเดียว

