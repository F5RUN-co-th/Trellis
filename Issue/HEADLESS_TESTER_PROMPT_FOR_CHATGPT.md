# Prompt ถาม ChatGPT — MT5 Strategy Tester headless รันไม่ได้

> คัดลอกส่วนด้านล่าง (ใน ``` ``` ) ไปถาม ChatGPT

```
ผมต้องการรัน MetaTrader 5 (MT5) Strategy Tester แบบ headless/อัตโนมัติ (สั่งจาก command line ไม่แตะ GUI)
เพื่อ backtest EA แล้วอ่านผล (log/report) ด้วย script — แต่ติดปัญหาหนักมาก ขอวิธีที่ "เชื่อถือได้จริง"
พร้อมประเมินทุกข้อเสนอด้วย: เหตุผล / ข้อดี / ข้อเสีย / ข้อจำกัด / performance / คะแนน (1-5) ทุกมุมมอง

=== ENVIRONMENT ===
- Windows 11, MT5 build 5833
- ตัวติดตั้ง MT5: D:\workspace\Doc\T.me\R&D\MetaTrader 5\terminal64.exe  (เป็น copy/แยกจาก default path)
- Data folder: C:\Users\<user>\AppData\Roaming\MetaQuotes\Terminal\<HASH>\
- Broker: Exness demo, server Exness-MT5Trial17, บัญชี valid, leverage 1:2000
- Custom symbol XAUUSD_BT มี cached real-tick history (รันออฟไลน์ได้, เคยรันผ่าน GUI สำเร็จ)
- EA: Trellis.ex5 + source .mq5/.mqh deploy เข้า MQL5\Experts และ MQL5\Include แล้ว
- เรียกจาก Git Bash/script: terminal64.exe /config:tester.ini  (ini มี [Common] login + [Tester] + [TesterInputs])

=== ปัญหา (อาการจริงจาก log) ===
1. ทุกครั้งที่ launch `terminal64.exe /config:tester.ini` → terminal log ขึ้น "launched with C:\"
   (ไม่ใช่ config ที่ส่งไป) ซ้ำทุก launch → [Tester] block ไม่เคยถูกเรียก → ไม่มี report ไม่มี tester journal
2. ช่วงแรก MT5 ตามหลัง build → ทุก launch มันเด้งไป LiveUpdate (auto-update) ก่อน แล้ว restart โดยทิ้ง /config
   ("LiveUpdate start ...terminal64.exe /update", "obsolete Tester deleted")
3. แม้ update เสร็จเป็น build ล่าสุดแล้ว ("you are using the latest version") terminal ก็ยัง restart ตัวเอง
   "launched with C:\" → /config หลุดอยู่ดี
4. (แก้ไปแล้ว) เคยเจอ "Trellis.mq5 not found" → แก้โดย deploy source เข้า MQL5 tree
5. (แก้ไปแล้ว) เคยเจอ "authorization failed (Invalid account)" → แก้โดยใส่ [Common] login บัญชีที่ valid
   → login สำเร็จ ("authorized on Exness-MT5Trial17, trading enabled") แต่ login แรกช้า ~4 นาที + restart ทิ้ง config
→ สรุปอาการแกน: **terminal restart ตัวเอง "launched with C:\" แล้วทิ้ง /config ทุกครั้ง → tester ไม่รัน**

=== วิธีที่ผม (Claude) ลองแล้ว + ประเมิน ===
| # | วิธี | เหตุผล | ข้อดี | ข้อเสีย | ข้อจำกัด | ผล |
|---|------|--------|-------|---------|----------|-----|
| 1 | terminal64 /config + [Tester] | documented method | ตรงไปตรงมา | config ถูกทิ้ง | ต้องไม่มี restart มาขวาง | ❌ ไม่รัน |
| 2 | + [TesterInputs] inline | forum บอกต้องมี ไม่งั้น test ไม่ start | inputs ครบ | ไม่ช่วยถ้า config หลุด | - | ❌ ไม่รัน |
| 3 | deploy source .mq5+.mqh เข้า MQL5 | tester ต้อง compile | แก้ "mq5 not found" | - | - | ✅ แก้จุดนี้ได้ |
| 4 | block โฟลเดอร์ liveupdate (rename) | กัน auto-update ดัก | - | MT5 re-download จาก server อยู่ดี | doc บอก disable ไม่ได้จริง | ❌ ไม่ช่วย |
| 5 | [Common] Login/Password/Server | บัญชีเดิม invalid | login สำเร็จ | login แรกช้า + restart ทิ้ง config | - | ⚠️ บางส่วน |
| 6 | taskkill + relaunch + poll 5 นาที | clean slate + ใจเย็น | - | terminal ไม่ shutdown, restart ทิ้ง config | กิน performance/เวลา | ❌ ไม่รัน |

=== คะแนนของทุกวิธี (1-5; reliability=รันได้จริง, setup=ง่าย, automation=เหมาะสคริปต์, perf=เร็ว, side-effect=ผลข้างเคียงต่อ terminal น้อย) ===
ทุกวิธี reliability = 1 (ไม่รัน) เพราะติด config-drop/self-restart เหมือนกันหมด

=== สิ่งที่อยากได้จาก ChatGPT ===
ขอ **วิธีที่เชื่อถือได้จริง** ในการรัน MT5 Strategy Tester headless จาก command line บน Windows ที่
**รอด auto-update + terminal self-restart + config-drop** — พร้อมประเมินแต่ละข้อเสนอด้วย
เหตุผล / ข้อดี / ข้อเสีย / ข้อจำกัด / performance / **คะแนน (1-5) ทุกมุมมอง** (reliability, setup, automation, perf, side-effect)
และเทียบว่าดีกว่าของผมยังไง

ประเด็นที่อยากให้พิจารณา (ถ้าเกี่ยวข้อง):
- single-instance issue: ถ้ามี terminal เปิดอยู่แล้ว /config ตัวใหม่จะถูก ignore (route ไป instance เดิม) ใช่ไหม? แก้ยังไง
- /portable mode ช่วยไหม
- ควรแยก MT5 ตัว "สำหรับ test เฉพาะ" (clean copy, ปิด auto-update ด้วย firewall/permission) ไหม
- ใช้ Python package `MetaTrader5` แทน (เชื่อมต่อ terminal ที่เปิดอยู่) ทำ backtest อัตโนมัติได้ไหม
- เรียก MetaTester agent ตรงๆ ได้ไหม
- ตำแหน่ง config.ini ต้องอยู่ที่ไหน (relative vs absolute) จึงไม่ถูกทิ้ง
- "launched with C:\" เกิดจากอะไร + ทำให้ /config stick ได้ยังไง
- วิธีบังคับ terminal ไม่ให้ self-restart / ไม่ auto-update บน build ใหม่
```
