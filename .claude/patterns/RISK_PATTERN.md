# Risk Management Pattern (MQL5 / XAUUSD)

Risk management patterns สำหรับ Gloo EA — รองรับทั้ง Fixed % และ Fixed Lot

---

## Lot Calculation: Fixed % Risk

```mql5
// คำนวณ lot จาก % risk และระยะ SL / Calculate lots from risk % and SL distance
double CalcLotsByRisk(string symbol, double riskPercent, double entryPrice, double slPrice)
{
   // จำนวนเงินที่ยอมเสีย / Risk amount in account currency
   double riskMoney = AccountInfoDouble(ACCOUNT_EQUITY) * riskPercent / 100.0;

   // ระยะ SL เป็น price distance / SL distance in price
   double slDistance = MathAbs(entryPrice - slPrice);

   // Tick value & size ของ symbol / Get tick info
   double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tickValue <= 0 || tickSize <= 0 || slDistance <= 0)
      return 0;

   // สูตรหลัก: lots = riskMoney / (slDistance / tickSize * tickValue)
   double lots = riskMoney / ((slDistance / tickSize) * tickValue);

   // ปรับให้ตรง broker limits / Normalize
   return NormalizeLots(symbol, lots);
}
```

---

## Lot Normalization

```mql5
double NormalizeLots(string symbol, double lots)
{
   double minLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   lots = MathFloor(lots / lotStep) * lotStep;  // ปัดลง / Round down
   lots = MathMax(lots, minLot);                 // ไม่ต่ำกว่า min
   lots = MathMin(lots, maxLot);                 // ไม่สูงกว่า max

   return NormalizeDouble(lots, 2);
}
```

---

## Switchable Risk Mode

```mql5
enum ENUM_RISK_MODE { RISK_FIXED_PCT, RISK_FIXED_LOT };

input ENUM_RISK_MODE InpRiskMode    = RISK_FIXED_PCT;
input double         InpRiskPercent = 1.0;     // Risk % per trade
input double         InpFixedLot    = 0.01;    // Fixed lot size

double CalculateLots(string symbol, double entryPrice, double slPrice)
{
   if(InpRiskMode == RISK_FIXED_LOT)
      return NormalizeLots(symbol, InpFixedLot);

   return CalcLotsByRisk(symbol, InpRiskPercent, entryPrice, slPrice);
}
```

---

## XAUUSD Tick Value Verification

```mql5
// ตรวจสอบค่า tick ของ XAUUSD / Verify XAUUSD tick value
void PrintGoldInfo(string symbol)
{
   Print("=== Gold Symbol Info ===");
   Print("Digits:        ", SymbolInfoInteger(symbol, SYMBOL_DIGITS));
   Print("Point:         ", SymbolInfoDouble(symbol, SYMBOL_POINT));
   Print("Tick Size:     ", SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE));
   Print("Tick Value:    ", SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE));
   Print("Contract Size: ", SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE));
   Print("Volume Min:    ", SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN));
   Print("Volume Max:    ", SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX));
   Print("Volume Step:   ", SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP));
   Print("Stops Level:   ", SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL));
   Print("Spread:        ", SymbolInfoInteger(symbol, SYMBOL_SPREAD));
}

// ตัวอย่าง XAUUSD (2-digit broker):
// Tick Size = 0.01, Tick Value = $1.00
// 1 lot, $5 move = $5 / $0.01 * $1.00 = $500
// 0.01 lot, $5 move = $5
```

---

## Pre-Trade Checks

```mql5
// ตรวจสอบทุกอย่างก่อนเปิด trade / All pre-trade validations
bool CanOpenTrade(string symbol, int magic)
{
   // 1. Spread check / ตรวจ spread
   if(!IsSpreadOK(symbol, InpMaxSpread))
   {
      Print("BLOCKED: Spread too wide");
      return false;
   }

   // 2. Max positions / ตรวจจำนวน position
   if(CountPositions(symbol, magic) >= InpMaxPositions)
   {
      Print("BLOCKED: Max positions reached");
      return false;
   }

   // 3. Daily drawdown (v1.5: equity-based, MAX(balance,equity) at day start)
   // g_startOfDayEquity = MAX(balance, equity) ตอน D1 bar change (17:00 EST = 00:00 server)
   // ใช้ equity ไม่ใช่ balance เพราะรวม floating P/L (Prop firm standard — FTMO)
   double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   double ddPct = 0;
   if(g_startOfDayEquity > 0)
      ddPct = (g_startOfDayEquity - currentEquity) / g_startOfDayEquity * 100.0;
   if(ddPct >= InpMaxDailyDD)
   {
      Print("BLOCKED: Daily DD ", DoubleToString(ddPct, 2),
            "% >= ", InpMaxDailyDD, "% (equity: ", DoubleToString(currentEquity, 2),
            " start: ", DoubleToString(g_startOfDayEquity, 2), ")");
      return false;
   }

   // 4. Trading day check / ตรวจวันเทรด
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.day_of_week == 0 || dt.day_of_week == 6)  // Weekend
   {
      Print("BLOCKED: Weekend");
      return false;
   }

   return true;
}
```

---

## Daily DD Tracking Pattern (v1.5)

```mql5
// Global state สำหรับ DD tracking / DD tracking state
double   g_startOfDayEquity = 0;   // MAX(balance, equity) ตอนเริ่มวัน
datetime g_lastD1BarTime    = 0;   // track D1 bar change

// เรียกทุก tick ก่อน trading logic / Call every tick before trading logic
void UpdateDailyEquityTracking()
{
   // ตรวจ D1 bar change = new trading day (00:00 server = 17:00 EST)
   datetime currentD1 = iTime(_Symbol, PERIOD_D1, 0);
   if(currentD1 != g_lastD1BarTime)
   {
      g_lastD1BarTime = currentD1;
      // Reset: ใช้ MAX เพราะ floating profit ค้างคืนต้องนับด้วย
      g_startOfDayEquity = MathMax(AccountInfoDouble(ACCOUNT_BALANCE),
                                   AccountInfoDouble(ACCOUNT_EQUITY));
      Print("[DD] New day reset: startEquity=", DoubleToString(g_startOfDayEquity, 2));
   }
}
```

---

## Min Risk-to-Reward Check (v1.5)

```mql5
// ตรวจ R:R ก่อนเปิด trade / Check min R:R before opening trade
// ICT: "never take less than 1:2" — ideal 1:3+
bool IsMinRiskReward(double entry, double sl, double tp, double minRR)
{
   double slDist = MathAbs(entry - sl);
   double tpDist = MathAbs(tp - entry);

   if(slDist <= 0) return false;  // ป้องกัน division by zero

   double rr = tpDist / slDist;
   if(rr < minRR)
   {
      Print("SKIP: R:R ", DoubleToString(rr, 2), " < min ", DoubleToString(minRR, 2),
            " (SL=", DoubleToString(slDist/_Point, 0), " TP=", DoubleToString(tpDist/_Point, 0), " pts)");
      return false;
   }
   return true;
}
```

---

## SL/TP Validation

```mql5
// ตรวจ stops level ของ broker / Validate SL/TP against broker stops level
bool ValidateStops(string symbol, double entryPrice, double slPrice, double tpPrice)
{
   int stopsLevel = (int)SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double point   = SymbolInfoDouble(symbol, SYMBOL_POINT);
   double minDist = stopsLevel * point;

   double slDist = MathAbs(entryPrice - slPrice);
   double tpDist = MathAbs(entryPrice - tpPrice);

   if(slDist < minDist)
   {
      Print("WARNING: SL too close. Min distance: ", minDist,
            " Current: ", slDist);
      return false;
   }

   if(tpDist < minDist)
   {
      Print("WARNING: TP too close. Min distance: ", minDist,
            " Current: ", tpDist);
      return false;
   }

   return true;
}
```

---

## Risk Summary Table

| Parameter | Default | Description |
|-----------|---------|-------------|
| Risk Mode | Fixed % | เลือกได้: Fixed % หรือ Fixed Lot |
| Risk % | 1.0% | % ของ equity ที่ยอมเสียต่อ trade |
| Fixed Lot | 0.01 | Lot คงที่ (ถ้าเลือก Fixed Lot mode) |
| Max Spread | 50 pts | ห้ามเทรดถ้า spread เกิน |
| Max Daily DD | 3.0% | หยุดเทรดถ้า DD เกิน (v1.5: equity-based, MAX(bal,eq) at day start) |
| Max Positions | 1 | จำนวน position สูงสุดพร้อมกัน |
| Slippage | 50 pts | Slippage สูงสุดที่ยอมรับ |
| Min R:R | 2.0 | v1.5: ICT min 1:2 — skip trade ถ้า TP/SL ratio ต่ำกว่า |
| Trail Step | ATR×0.5 | v1.5: min SL movement ก่อน re-adjust (~$2.50 Gold M15) |
| BE Activate | 2.0 R | v1.4: ICT 2022 standard — BE หลังกำไร 2R (was 1R) |
| Filling Mode | auto | v1.4: `SetTypeFillingBySymbol()` — ห้าม hardcode FOK |
