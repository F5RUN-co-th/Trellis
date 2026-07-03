# Trellis — Aggressive Grid Scalper EA (MT5)

> โครงระแนงไม้เลื้อย — grid หลายชั้นที่ราคาไต่ผ่าน
> โปรเจกต์แยกจาก [Gloo](../Gloo) (ICT disciplined) โดยสิ้นเชิง — คนละปรัชญา

## สถานะปัจจุบัน
**Stage 0 — Pre-code: Expectancy Proof** (ยังไม่มี source code)

เหตุผล: grid + lot scaling เป็น strategy ที่ negative-expectancy ได้ง่ายและ backtest หลอกตา
จึง **ต้องพิสูจน์ว่า payoff สุทธิเป็นบวกก่อนลงทุนเขียน code** ไม่ใช่เขียนก่อนแล้ว optimize (= curve-fitting trap)

ดูแผน + ข้อตัดสินใจทั้งหมดที่ → [`Plan/TRELLIS-001_design_doctrine.md`](Plan/TRELLIS-001_design_doctrine.md)

## Roadmap
| Stage | ชื่อ | สถานะ |
|-------|------|--------|
| 0 | Expectancy proof (tick-data sim, Gold) | ⏳ กำลังจะเริ่ม |
| 1 | EA architecture (class/module design) | ⬜ |
| 2 | MQL5 skeleton + grid engine | ⬜ |
| 3 | Backtest (99% tick, realistic spread/slippage) | ⬜ |
| 4 | Parameter robustness (ไม่ใช่ optimization เปล่า) | ⬜ |

## Core Concept (ฉบับย่อ)
1. **Entry** — pullback signal (EMA trend filter + RSI + Bollinger), ไม่สุ่มกลางตลาด
2. **Grid** — ATR-based spacing (ปรับตาม volatility) ไม่ใช่ fixed pip
3. **Lot scaling** — controlled (ไม่ใช่ martingale โหด) + normalize ด้วย volume step
4. **Exit** — basket TP (ปิดทั้งชุดเมื่อ floating profit ถึงเป้า)
5. **Risk** — **basket hard-stop + daily DD + equity stop** (❌ ไม่มี hedge recovery — เป็น workaround)

## เอกสารสำคัญ
- [`CLAUDE.md`](CLAUDE.md) — instructions + grid doctrine สำหรับ Claude
- [`Plan/TRELLIS-001_design_doctrine.md`](Plan/TRELLIS-001_design_doctrine.md) — design + การวิเคราะห์ข้อเสนอ ChatGPT + ข้อตัดสินใจ
- MQL5 reference: reuse จาก [`../Gloo/Docs`](../Gloo/Docs)

## Build
`Ctrl+Shift+B` ใน VS Code → compile `Experts/Trellis.mq5` (เมื่อมีไฟล์แล้ว)
