# Grid / Martingale — Industry & Community Research

**วันที่ค้นคว้า:** 2026-06-28
**ที่มา:** ตอบคำถามวิน "industry standard / best practice / real-world / ชุมชนทำยังไง" สำหรับ §10 Open Decisions ของ [`../Plan/TRELLIS-002_expectancy_sim_plan.md`](../Plan/TRELLIS-002_expectancy_sim_plan.md)
**วิธี:** WebSearch (verify จาก primary/community sources — ไม่ใช่ความเห็นเดียว) · numbers/claims มี source กำกับ

---

## บทสรุป (สำคัญสุด)
**3 แหล่งอิสระบอกตรงกัน** → doctrine ของ Trellis (พิสูจน์ expectancy ก่อน · ไม่ใช้ martingale recovery · basket hard-cap) **คือ convergent industry consensus ไม่ใช่ความเห็นเราคนเดียว:**

1. **Quant/position-sizing literature:** money management เปลี่ยน sign ของ expectancy ไม่ได้
2. **ชุมชน grid/martingale:** martingale = "one margin call wipes months/years"
3. **Modern EA practice 2026:** "total equity risk limit" แทน "forever grid"

---

## 1. Money Management ไม่แปลง Negative Edge เป็น Positive (quant principle)
> "Position sizing **cannot make an unprofitable strategy profitable**... It cannot turn a bad strategy into a winning one. Money management requires a **positive edge to work**; it cannot convert a losing system into a winning one."

- แหล่ง: [quantinsti — Position Sizing](https://blog.quantinsti.com/position-sizing/) · [profitsmasher](https://www.profitsmasher.com/2026/06/your-strategy-is-more-then-entry-signal.html)
- **นัยต่อ Trellis:** lot scaling (geo/martingale) เพื่อ "recover" basket ขาดทุน = **workaround** ตามนิยาม (ลบออก → ขาดทุนกลับมา · ไม่แก้ root cause [edge] แค่ซ่อน) → **ต้องพิสูจน์ edge ด้วย flat lot ก่อน** (Grid Doctrine #1)

## 2. Grid (constant) vs Martingale (scaling) — risk profile
> "Grid: position sizes คงที่ → risk เพิ่ม **linear** · Martingale: doubling → risk เพิ่ม **exponential**... one margin call can **wipe out many months or years of profits**" · grid win-rate **70–90%** แต่ trend แรง = **DD 30–50%+**

- แหล่ง: [forexeapro 2026 comparison](https://forexeapro.com/grid-trading-ea-vs-martingale-strategy-a-2026-comparison-for-algorithmic-traders/) · [forexrobotlab — FXStabilizer](https://forexrobotlab.com/fxstabilizer-ea-review/) · [bestmt4ea](https://bestmt4ea.com/risk-management-settings-for-grid-ea-explained-7-powerful-ways-to-reduce-losses/)
- "Soft martingale ×1.2–1.5" = ชุมชนเสนอเป็น "ทางสายกลาง" **แต่ยัง compound exposure ตอน underwater** → ยังเป็น tail-borrow

### ตารางเปรียบเทียบ lot scaling (หลายมุม)
| มุมมอง | flat 0.01 | fixed-add +0.01 | soft-geo ×1.2 | martingale ×2 |
|---|---|---|---|---|
| Ruin safety | 🟢 linear | 🟢 linear | 🟠 compound underwater | 🔴 exponential |
| Expectancy honesty | 🟢 isolate edge | 🟢 | 🔴 ยืม tail | 🔴 |
| 0.01 quantization (T1) | 🟢 | 🟢 exact multiple | 🔴 flat 4 ไม้แรกแล้วกระโดด | 🟠 |
| Recovery speed | 🔴 ช้า | 🟠 | 🟢 | 🟢 |
| Profit/cycle | 🔴 จิ๋ว | 🟠 | 🟢 | 🟢 |
| Community verdict | "safer/sustainable" | linear-safe | "compromise" | "ทุนหนา+รับเสี่ยงสูงเท่านั้น" |

## 3. Concurrent grids vs single
> "Diversify across uncorrelated pairs **OR limit yourself to one grid at a time**" · multiple grids ต้อง **aggregate exposure cap + correlation control** · "EUR/USD + EUR/GBP grids ทั้งคู่มี EUR exposure"

- แหล่ง: [newyorkcityservers — Grid Guide 2026](https://newyorkcityservers.com/blog/grid-trading-forex) · [smartedgetrading](https://www.smartedgetrading.net/blog/are-grid-eas-really-dangerous-or-just-poorly-designed)
- **นัยต่อ Trellis:** XAUUSD ตัวเดียว → concurrent baskets = correlation 1.0 = **leverage stacking** ไม่ใช่ diversify → **one-at-a-time สำหรับ Stage 0**

## 4. Basket exit / hard-stop — modern best practice
> "Unlike older 'forever' grids, 2026 systems implement a **'total equity risk' limit**" · "Daily Drawdown % of Balance" · "Equity Cut Loss — hard stop based on account equity" · "CHoCH cooldown — pause adding trades when confirmed trend against basket"

- แหล่ง: [newyorkcityservers](https://newyorkcityservers.com/blog/grid-trading-forex) · [bestmt4ea](https://bestmt4ea.com/risk-management-settings-for-grid-ea-explained-7-powerful-ways-to-reduce-losses/) · mql5 market EAs
- **นัยต่อ Trellis:** basket hard-cap = เกราะหลัก (ตรง Doctrine #3/#6) · "trend-pause (CHoCH)" = guard รอง (Doctrine #7 — lagging, ห้ามเป็นเกราะหลัก)

## 5. Alternative philosophy (เก็บไว้อ้างอิง)
> "Rhuva Gold EA — rejects grid/martingale **entirely**, hard SL per trade, low-drawdown profile"

- แหล่ง: [elitetrader — Rhuva Gold](https://www.elitetrader.com/et/threads/rhuva-gold-ea-eliminating-grid-martingale-flaws-in-xauusd-automation.390248/)
- = ปรัชญาฝั่งตรงข้าม (≈ Gloo: SL ต่อไม้) — Trellis เลือกฝั่ง grid โดยตั้งใจ ไม่ปนกัน

---

## Implications → §10 Decisions (evidence-backed)
| §10 | สรุปจาก evidence |
|---|---|
| #2 Lot | **flat 0.01 ก่อน** (พิสูจน์ edge) → fixed-add → geo แยก study StartLot ใหญ่ |
| #7 Concurrent | **one-at-a-time** (XAU correlation 1.0) |
| #4 Hard-stop | total-equity-cap เกราะหลัก + frontier · trend-pause = guard รอง |
| #1 Entry | entry รองเมื่อ grid mechanic ครอบงำ → ชุดเล็ก {random + 1 MR} |

## Sources (ทั้งหมด)
- https://blog.quantinsti.com/position-sizing/
- https://www.profitsmasher.com/2026/06/your-strategy-is-more-then-entry-signal.html
- https://forexeapro.com/grid-trading-ea-vs-martingale-strategy-a-2026-comparison-for-algorithmic-traders/
- https://forexrobotlab.com/fxstabilizer-ea-review/
- https://bestmt4ea.com/risk-management-settings-for-grid-ea-explained-7-powerful-ways-to-reduce-losses/
- https://newyorkcityservers.com/blog/grid-trading-forex
- https://www.smartedgetrading.net/blog/are-grid-eas-really-dangerous-or-just-poorly-designed
- https://phemex.com/academy/martingale-bot-vs-grid-bot
- https://www.elitetrader.com/et/threads/rhuva-gold-ea-eliminating-grid-martingale-flaws-in-xauusd-automation.390248/

> ⚠️ แหล่งส่วนใหญ่เป็น vendor/community blog (marketing bias ได้) — ใช้เป็น "ชุมชนคิดยังไง" + ยืนยัน quant principle (#1) ที่เป็น textbook · **ไม่ใช่ validated edge** ของ Trellis เอง (อันนั้นต้องพิสูจน์ด้วย sim Stage 0)
