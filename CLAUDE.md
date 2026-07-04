# Trellis EA — Project Instructions for Claude

> **Trellis** = โครงระแนงไม้เลื้อย — grid หลายชั้นที่ราคาไต่ผ่าน
> **ประเภท:** Aggressive Grid Scalper (adaptive grid + scalping exit + hard risk control)
> **โปรเจกต์นี้แยกจาก Gloo โดยสิ้นเชิง** — คนละปรัชญา (Gloo = ICT disciplined / SL ต่อไม้; Trellis = grid recovery / basket exit) ห้ามให้ logic ปนกันข้ามโปรเจกต์

## CRITICAL RULES
- **ห้าม Claude หรือ Agents แก้ไข code ก่อนได้รับอนุญาต** — ต้องเสนอการแก้ไขและรอวินอนุมัติก่อนเสมอ ห้ามแก้ไขไฟล์ .mq5, .mqh หรือ source file ใดๆ โดยไม่ได้รับอนุญาต
- Analysis, recommendations, และ code suggestions แสดงได้ แต่ห้ามเขียนลงไฟล์จนกว่าวินจะอนุมัติ

## กฎการทำงาน (Working Rules)
1. **สรุปปัญหาและเสนอแผนก่อน ไม่ใช่ลงมือทำทันที** — วิเคราะห์ root cause → เสนอแผน → รอวินอนุมัติ → แล้วค่อย implement
2. **ตรวจดู production code อย่างละเอียด** ก่อนเสนอ fix ใดๆ — ต้อง verify จาก actual code ไม่ใช่คาดเดา
3. **ไม่มี duplicate code** — ตรวจว่ามี logic/function ที่ทำอยู่แล้วหรือไม่ก่อนเพิ่มใหม่
4. **ทุก fix ต้องเป็น Production-Ready Implementation, Industry Standards, Best Practice** — ไม่มี quick fix/quick win
5. **ถ้าวินเจอ bug หรือสิ่งผิดปกติ** → วิเคราะห์ root cause อย่างละเอียดก่อน → ไม่ throw fixes แล้วดูว่า work ไหม
6. **ถ้า fix ไม่ work** → วิเคราะห์ว่า WHY ไม่ work ก่อนทำ fix ถัดไป → ไม่ revert แล้วทิ้งปัญหา
7. **ห้ามสรุปโดยไม่มี evidence** — ต้อง quote code line number หรือ log line เสมอ ถ้าไม่มี → บอกตรงๆ "ไม่มีข้อมูล ต้อง diagnose ก่อน"
8. **ทุก fix ต้องตอบ "root cause หรือ workaround?"** — ถ้าลบ fix ออกแล้วปัญหากลับมา = workaround ไม่ใช่ root cause
8.1 **ห้ามแก้ปัญหาแบบ "หลบ" (หลักวิน 2026-07-03)** — เพิ่มทุน/ข้ามวัน/หยุดเทรด/เพิ่มตัวแปรให้เลี่ยง ไม่ใช่การแก้ปัญหา (เจอสถานการณ์ใหม่ก็ตายอยู่ดี) · ทุก fix ต้องตอบได้ว่าทำให้ engine **เข้าใจสาเหตุการเคลื่อนของราคา/ปรับตัว**ขึ้นตรงไหน · risk-management มีได้ในฐานะเพดานความถ่อมตัว ไม่ใช่ในฐานะ "การแก้ปัญหา"
9. **ทุก backtest round ต้อง compare metrics กับ round ก่อน** — ห้ามดูแค่ตัวเลข round ใหม่ ต้องตาราง compare ทุก metric
10. **ส่ง Engineer review ต้องส่งงานทั้ง scope** — ไม่ใช่แค่ส่วนที่ Claude สนใจ
11. **ตรวจ Engineer proposals อย่าง critical ก่อนยอมรับ** — Engineer อาจพลาดหรือไม่ทราบบริบท ห้ามเชื่อทันที
12. **เลือกเครื่องมือให้ตรงงาน (evidence-based):**
    - ค้น code pattern / cross-file reference / architecture → **Explore agent** (systematic, ไม่ข้าม file, ไม่เปลือง context)
    - วิเคราะห์ backtest log / expectancy-sim output (count/compare/aggregate) → **Explore agent** หรือ Claude+Bash — เขียน script ครอบทุก metric ในคำสั่งเดียว ไม่ใช่ทีละ grep
    - Independent review รอบสุดท้าย → **mql5-ea-engineer agent** (จับ blind spot)
    - MQL5 API / grid-martingale risk research → **Claude + WebSearch** (verify จาก primary source ไม่ตีความ local doc)
    - Claude ตรวจเองก่อนทุกครั้ง (มี full context) → ใช้ Agent "เสริม" ไม่ใช่ "แทน"
    - **ห้ามคาดเดาว่าเครื่องมือทำอะไรได้/ไม่ได้** — verify ก่อน
    - **Log analysis:** UTF-16LE log ใช้ `iconv` เสมอ · หา pattern ด้วย `sort | uniq -c | sort -rn` ไม่ใช่ head/tail · **ตาราง compare ทุก metric กับ round ก่อน** (กฎข้อ 9)

## ⚠️ GRID-SPECIFIC DOCTRINE (หัวใจของโปรเจกต์นี้ — อ่านก่อนทุกครั้ง)
Grid + lot scaling เป็น strategy ที่ "ระเบิดบัญชี" ง่ายที่สุด ถ้าไม่ระวัง กฎเหล่านี้บังคับ:

1. **EXPECTANCY ต้องพิสูจน์ก่อนเขียน code** — ห้ามเขียน grid engine จนกว่าจะมีหลักฐานเชิงตัวเลข (tick-data sim บน Gold) ว่า payoff สุทธิเป็นบวก การ optimize ก่อนพิสูจน์ expectancy = curve-fitting trap
2. **ห้าม Hedge Recovery** — การเปิดไม้สวนกลบ basket ที่ขาดทุน = workaround (ลบออกแล้วปัญหากลับมา) คุม drawdown ด้วย **basket hard-stop** (ปิดทั้ง basket ที่ -X%) เท่านั้น
3. **ทุกไม้ grid ต้องมี basket-level risk cap** — ไม่มีสถานการณ์ที่ basket เปิดค้างไม่มีเพดานขาดทุน
4. **Lot ต้อง normalize ด้วย SYMBOL_VOLUME_STEP เสมอ** — ที่ StartLot=0.01 ตัวคูณ <1.5 จะถูกปัดทิ้งใน 2-3 ไม้แรก (0.01×1.3=0.013→0.01) ต้อง verify lot ladder จริงหลัง normalize
5. **Backtest grid หลอกตา** — ต้องใช้ tick data จริง + realistic spread/slippage + modelling quality 99% เท่านั้น equity curve เรียบ ≠ edge
6. **Equity stop เอาไม่อยู่ 100% บน Gold** — gap/news/slippage ทำให้ DD จริงทะลุเพดานได้ ออกแบบโดยถือว่า worst-case > เพดานที่ตั้งไว้
7. **ADX/filter เป็น lagging** — ใช้เป็น guard เสริม ห้ามพึ่งเป็นเกราะหลัก
8. **News filter ต้อง verify ว่าทำงานใน Strategy Tester** — ถ้าไม่ทำงาน backtest จะดีเกินจริงเทียบ live โดยอัตโนมัติ

## Pattern การสื่อสารกับวิน (Communication Pattern)
**3-Phase Gate:** review → **STOP รอคำสั่ง** → verify → **STOP รอ confirm** → implement
ห้ามข้าม gate ห้าม auto-incorporate ห้ามแนบ "เริ่มต่อไหม" เพื่อ steer

- **วินปฏิเสธแนวทางเดิมครบ 2 ครั้ง = หยุดทันที** — พูดความเข้าใจออกมาให้วินตรวจก่อนแตะอะไรต่อ ห้ามตีความคำสั่งเอาเองแล้วลงมือ (บทเรียน 2026-07-03: ตีความ "เร่งพัฒนา" ผิดจนโดน interrupt)
- **สื่อสารด้วยสิ่งที่วินเห็นบนจอจริง ไม่ใช่ชื่อในโค้ด (บทเรียน 2026-07-03):** MT5 Inputs tab แสดง **comment** ของ input ไม่ใช่ชื่อตัวแปร — วินไม่มีทางเห็น `InpXxx` ที่ Claude อ้าง → (1) comment ของทุก `input` ต้องเป็น label เดียวกับคำที่ Claude ใช้สั่งงานวิน (2) ขั้นตอน UI ต้องอ้าง label ที่ปรากฏบนจอจริง (3) ไม่แน่ใจว่าจอวินแสดงอะไร → ขอ screenshot ก่อน ห้ามเดา (4) input ที่วินไม่ต้องตั้ง → แปลงเป็น const ให้ dialog เหลือเฉพาะที่ใช้จริง

- **วินสั่ง "Engineer review"** → Engineer รายงาน: (1) ปัญหา + evidence (code line/log line) (2) root cause analysis (ไม่ใช่ symptom) (3) solution แบบ Production-Ready/Best Practice — **ห้าม workaround**
- **วินสั่ง "Claude Verify"** → Claude: (1) วิเคราะห์ทุก finding ด้วย evidence จาก code/log จริง (2) เห็นทางที่ดีกว่า (ไม่ดรอปศักยภาพ) → เสนอ (3) เห็นด้วย → ต้อง verify ได้จริงว่า root cause + production-ready — **ห้าม rubber-stamp · ห้ามยอมรับ workaround แม้ Engineer เสนอ**
- **ตอบคำถามทั่วไป** → ห้ามคาดเดา/แต่งเติม · ไม่รู้ → "ไม่รู้" ตรงๆ · ทุกคำตอบต้องมี evidence ถ้าไม่มี → "ไม่มีข้อมูล ต้อง diagnose ก่อน"

## Honest Reporting (ความซื่อสัตย์เหนือความน่าประทับใจ)
- **ไม่เดา error** — อ่าน output เต็มก่อนสรุปสาเหตุ ไม่เดาจากบรรทัดเดียว
- **ไม่แก้เงียบ** — เจอว่าตัวเองพลาด/เข้าใจผิด → บอกวินทันที ไม่กลบ
- **ไม่ bypass safety เพื่อให้ผ่าน** — ไม่ข้าม check/hook เพื่อให้ดูเหมือนเสร็จ
- รายงานผลตามจริง: test fail = บอกว่า fail พร้อม output · ข้ามขั้น = บอกว่าข้าม · เสร็จจริง = บอกตรงไม่อ้อม

## No Scope Creep / No Manufactured Ambiguity
- **วินไม่ระบุ = ไม่มี ไม่ต้องการ** — ห้ามเพิ่ม component/safeguard/filter/pattern โดยอ้าง "best practice" เอง · จะเพิ่มต้องขอก่อน
- **"ดีที่สุด" = ดีที่สุดในกรอบ requirement** ไม่ใช่ขยาย scope · scope anchor = root cause ที่วิน report ทุก change ต้อง trace กลับไปได้
- **out-of-scope ที่เจอ → log เป็น issue แยก** ไม่ทิ้งเงียบ ไม่ลากเข้าแผนปัจจุบัน
- **ห้ามปั้นความกำกวม/ความขัดแย้งจาก instruction ที่ชัดอยู่แล้ว** — จะอ้างว่า doc เงียบ/ขัดกัน ต้อง quote ข้อความจริงก่อน · quote ไม่ได้ = ไม่ใช่ gap = ห้ามถาม
- **แยกเจ้าของการตัดสินใจ:** *requirement* = วินเป็นเจ้าของ (ถามเฉพาะเมื่อ doc เงียบจริง) · *scope/technical* = Claude ตัดเอง (ห้ามโยนให้วิน)

## Authority Order + Glossary-first
- **ลำดับ authority:** doctrine doc (`Plan/TRELLIS-001`) > code > comment — ถ้า code/comment ขัด doctrine = code ผิด (รายงาน) ห้ามยกเป็น "design choice"
- **Citation ต้องมาจากแหล่งที่เพิ่งอ่าน** ไม่ใช่เลข §/หัวข้อจากความจำ — จำไม่ได้ → เปิดอ่านก่อน
- **Glossary-first:** ก่อนวิเคราะห์ logic grid ให้ pin ศัพท์ให้ชัดก่อน — *basket / cycle / grid level / lot ladder / step / spacing* — คำเดียวกันคนละบริบท = คนละ concept จนกว่าจะ quote ได้ว่าเหมือน
- **Glossary เวลาเทรด (บทเรียน C7 2026-07-05 — Engineer จับ lookahead ก่อนรัน):** *signal bar j* (บาร์ที่ close ทะลุ level — จุดตัดสินใจ = close ของ j) ≠ *execution bar i* (เข้าที่ open ของ i · runner เก็บ timestamp = `t[i]`) — **feature ใดอ้าง "ณ เวลา entry" ต้อง as-of ≤ close ของ bar j เท่านั้น** (data ของ bar i เกิดหลังจุดตัดสินใจ = within-bar lookahead) · อ้าง bar ก่อนหน้าด้วย **sequence-position ใน bar-series เดียวกับ sim** (j = index(i)−1) ห้ามลบนาทีเลขคณิต (missing bar ทำเลื่อน) · คำที่มีสองความหมายเชิงเวลา (entry/breakout/signal/fill) = pin ด้วย code line ก่อนใช้เป็น as-of
- **โดนแก้ 1 fact → แก้เฉพาะจุดนั้น** ห้ามเหวี่ยงทั้ง model ไปขั้วตรงข้าม (flip-flop) · ส่วนที่ยังไม่ pin = คง "ยังไม่รู้" ห้ามเดาเติม

## ⭐ Verify ≠ Self-grading — Expectancy Proof Integrity (หัวใจ Stage 0)
> ต่อยอดจาก Grid Doctrine #1 (expectancy ต้องพิสูจน์ก่อนเขียน code) — กันการ "ตรวจการบ้านตัวเอง"
- **Verify ที่แท้จริง = ผู้ตรวจไม่ใช่ผู้ให้คะแนนคนเดิม** — context แยก + prompt ปรปักษ์ ("จงหักล้าง/หาจุดอ่อนของ sim นี้") · Claude เขียน sim แล้วให้คะแนน sim ตัวเอง = self-assessment ต้องประกาศชัด ไม่ใช่ "verify อิสระ"
- **"ไม่เจอจุดอ่อน = ยังคิดไม่ละเอียดพอ"** — expectancy ที่ดูบวกต้องผ่าน adversarial check (tail loss, fast-trend stress, cost realistic) ก่อนเชื่อ
- **node/Python script เป็นเจ้าของตัวเลขเสมอ ไม่ใช่ LLM** — expectancy/win-rate/max-DD ต้อง derive จาก script ที่ตรวจซ้ำได้ · ห้าม Claude พิมพ์ตัวเลขสรุปเอง
- **โปร่งใส 2 ชั้น:** แยกให้วินเห็นทุกครั้งว่า อะไร = pipeline ทำ (อัตโนมัติ ตรวจซ้ำได้) vs อะไร = ดุลพินิจ LLM (ใครตัดสิน) · ห้ามนำเสนอให้ "ดูเหมือนระบบจับได้" ทั้งที่ Claude เลือกเอง
- **ตรวจเครื่องมือตัวเองด้วย** — จุดที่ script "ตัด/รวม/จับคู่" ถ้ามีอะไรหลุดต้อง fail loud หรือ log · ผลที่สะอาดเกินไปให้สงสัยว่ามีของตกหล่นเงียบๆ ก่อน
- **ตัวเลขในเอกสาร/แผน = รันสดจาก canonical script ตอนเขียน + ติดป้ายสนามวัดเสมอ (sim vs MT5 tester)** — สองสนามต่างกันได้ระดับพลิกเครื่องหมายรายปี (บทเรียน 2026-07-03: 2025 sim +207 / tester −169) · target ที่ผสมสนาม = target ปลอม
- **สมมติฐานที่ sim และ EA แชร์กัน = จุดบอดร่วมที่ cross-validation มองไม่เห็น** — enumerate แล้ว verify กับ raw data แยก (บทเรียน: Friday-close ผิดเหมือนกันทั้งคู่ → tester เท่านั้นที่จับ)
- **เกณฑ์ขั้นต่ำก่อนเรียกสิ่งใดว่า "สัญญาณ":** วัดบน full population (ไม่ใช่ subsample) + เสถียร multi-period + ดูทั้ง SUM และ AVG + เช็ค zero-data region

## Tool-call Syntax
- ทุก tool call ต้องใช้ tag namespace ครบ: `antml:invoke` / `antml:parameter` เสมอ
- เขียน `<invoke>` / `<parameter>` เปล่า (ขาด `antml:`) = ระบบ parse ไม่ออก → กลายเป็นข้อความ ไม่ execute (ประกาศ "ทำต่อ" แต่ tool ไม่ทำงาน) — เช็ค tag เปิด/ปิดก่อนยิงทุกครั้ง

## MT5 Backtest / Tester Workflow (บังคับ — บทเรียน 2026-06-29)
- **Headless `terminal64.exe /config` ไม่ทำงานบนเครื่องนี้** — terminal restart ตัวเอง `launched with C:\` ทิ้ง config + LiveUpdate (auto-update) ดัก disable ไม่ได้ · **ห้ามลอง headless ซ้ำ** (ดู memory `reference-mt5-tester-workflow`)
- **Flow ที่ถูก:** Claude `compile` + deploy **ex5 + source (.mq5/.mqh) เข้า terminal MQL5 tree** (tester ต้องการ source ไม่ใช่แค่ .ex5) → **วินรัน Strategy Tester GUI เอง** → ส่ง agent log → Claude วิเคราะห์
- **⛔ อย่า re-try วิธีที่วินบอกแล้วว่าไม่ work** — ดื้อทำซ้ำ dead-end = เปลือง token + เสียเวลา + ทำให้วินหงุดหงิด · วินชี้ว่าอะไรไม่ได้ = จบ หาทางอื่น ไม่วน
- **เช็ค data coverage ของ symbol ก่อนกำหนดช่วงรันเสมอ** — บรรทัด "N bars generated" ใน tester log = หลักฐาน (บทเรียน: XAUUSD_BT เคยจบ ธ.ค. 2025 เงียบๆ ทั้งที่ CSV มีถึง ก.พ. 2026)
- **Clock/session พิสูจน์ด้วย price-matching เท่านั้น ห้ามอนุมานจากโครงสร้าง** — ข้อเท็จจริงที่พิสูจน์แล้ว (แก้ 2026-07-03 เย็น หลัง price-match shoulder weeks): BT-clock (Dukascopy-converted) เทียบ UTC = **+2 หนาว/+3 ร้อน ตามกฎ EU-DST (last Sun Mar/Oct) — ไม่ใช่ US-DST** (ก.พ./ฤดูร้อนสองกฎให้ค่าเท่ากัน แยกไม่ได้ — จุดตัดสิน = shoulder weeks) → EA บน Exness ใช้ HourShift=-1 (AUTO, `IsEuDST`) · tester XAUUSD_BT ใช้ 0 · **บทเรียน: tick 2025/26 เคยถูก import เป็น UTC ดิบ → tester test คนละ session ทั้งปีแบบเงียบ — data ใหม่ทุกก้อนต้อง verify first-epoch/clock ก่อน import** (TRELLIS-010 Stage 0)

## Project Overview
- **Name:** Trellis — Expert Advisor (EA) for MetaTrader 5
- **Language:** MQL5 (NOT MQL4)
- **Strategy:** Adaptive Grid Scalper — initial pullback entry → ATR-based grid → basket TP → hard risk control
- **Target markets:** XAUUSD (primary), ทดสอบ NAS100 / EURUSD ภายหลัง
- **Timeframe:** Entry M1/M5, Trend filter M15
- **Developer Language:** Thai + English bilingual

## Project Structure
```
Trellis/
├── CLAUDE.md              ← (this file) instructions for Claude
├── README.md              ← project overview + current status
├── .vscode/
│   ├── tasks.json         ← Ctrl+Shift+B to compile Trellis.mq5
│   └── settings.json      ← MQL5 → C++ syntax highlighting
├── Experts/
│   └── Trellis.mq5        ← main EA source (ยังไม่สร้าง — รอพิสูจน์ expectancy ก่อน)
├── Include/
│   └── *.mqh              ← header files (grid engine, risk, basket)
├── Scripts/
│   ├── deploy.sh          ← copy .ex5 to MT5
│   └── *.py               ← expectancy sim / data tools
├── Docs/                  ← MQL5 reference (reuse จาก ../Gloo/Docs)
├── Research/              ← grid/martingale risk research
├── Plan/                  ← design docs (TRELLIS-XXX)
└── Issue/                 ← bug/analysis logs
```

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
├── agents/mql5-ea-engineer.md     ← MQL5 EA Engineer persona (grid scalper / XAUUSD)
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
> Engineer agent ปรับเป็น **grid doctrine** แล้ว (ตัด ICT, ใส่กฎ grid 8 ข้อ + anti-pattern เพิ่ม)

### Custom Commands
- `/mql5-ea-engineer [request]` — invoke MQL5 EA Engineer (grid specialist)
- `/compile` — compile Trellis.mq5 + report errors
- `/trellis-010 [status]` — resume Brain Research Workflow: บังคับ pre-flight (อ่าน plan+progress log สด, เช็ค lockbox/test budget) ก่อนทำงาน Stage ปัจจุบันต่อ · `status` = รายงานอย่างเดียว

