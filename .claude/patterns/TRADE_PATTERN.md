# Trade Pattern (MQL5)

วิธี execute trade, manage positions, และ handle errors ด้วย CTrade

---

## CTrade Setup Pattern

```mql5
#include <Trade\Trade.mqh>

CTrade trade;

int OnInit()
{
   // ตั้งค่า CTrade / Configure CTrade
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippage);
   // v1.4: auto-detect filling mode — ห้าม hardcode FOK!
   // IC Markets = FOK, FxPro = IOC, Alpari = varies
   // ผิด mode = error 10030 (TRADE_RETCODE_INVALID_FILL)
   trade.SetTypeFillingBySymbol(_Symbol);    // auto-detect จาก SYMBOL_FILLING_MODE
   trade.LogLevel(LOG_LEVEL_ERRORS);         // Log errors only

   return INIT_SUCCEEDED;
}
```

---

## Buy / Sell Pattern

```mql5
// === Buy with SL/TP ===
double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
double sl  = ask - slDistance;  // SL ด้านล่าง / SL below entry
double tp  = ask + tpDistance;  // TP ด้านบน / TP above entry

sl = NormalizeDouble(sl, _Digits);
tp = NormalizeDouble(tp, _Digits);

if(trade.Buy(lots, _Symbol, ask, sl, tp, InpTradeComment))
{
   Print("BUY opened: ticket=", trade.ResultOrder(),
         " price=", trade.ResultPrice());
}
else
{
   Print("BUY failed: ", trade.ResultRetcode(),
         " - ", trade.ResultComment());
}

// === Sell with SL/TP ===
double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
double sl  = bid + slDistance;  // SL ด้านบน / SL above entry
double tp  = bid - tpDistance;  // TP ด้านล่าง / TP below entry

trade.Sell(lots, _Symbol, bid, sl, tp, InpTradeComment);
```

---

## Position Counting Pattern

```mql5
// นับ position ตาม magic number / Count positions by magic
int CountPositions(string symbol, int magic)
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)  // วนย้อนกลับ / Backward loop
   {
      if(PositionGetSymbol(i) == symbol)
         if(PositionGetInteger(POSITION_MAGIC) == magic)
            count++;
   }
   return count;
}

// นับแยกตาม type / Count by type
int CountBuyPositions(string symbol, int magic)
{
   int count = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) == symbol)
         if(PositionGetInteger(POSITION_MAGIC) == magic)
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
               count++;
   }
   return count;
}
```

---

## Spread Check Pattern

```mql5
// ตรวจ spread ก่อนเทรด / Check spread before trading
bool IsSpreadOK(string symbol, int maxSpreadPoints)
{
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double spreadPoints = (ask - bid) / SymbolInfoDouble(symbol, SYMBOL_POINT);

   if(spreadPoints > maxSpreadPoints)
   {
      Print("Spread too wide: ", spreadPoints, " > ", maxSpreadPoints);
      return false;
   }
   return true;
}
```

---

## Lot Normalization Pattern

```mql5
// ปรับ lot size ให้ถูกต้องตาม broker / Normalize lot to broker limits
double NormalizeLots(string symbol, double lots)
{
   double minLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   // ปัดลงให้ตรง step / Round down to step
   lots = MathFloor(lots / lotStep) * lotStep;

   // จำกัดขอบเขต / Clamp to min/max
   if(lots < minLot) lots = minLot;
   if(lots > maxLot) lots = maxLot;

   return NormalizeDouble(lots, 2);
}
```

---

## Break-Even Pattern

```mql5
// ย้าย SL ไป break-even เมื่อกำไรถึง threshold
// Move SL to break-even when profit reaches threshold
void MoveToBreakEven(CTrade &trade, int magic, double beActivatePrice)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != magic) continue;

      ulong  ticket    = PositionGetInteger(POSITION_TICKET);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL = PositionGetDouble(POSITION_SL);
      double currentTP = PositionGetDouble(POSITION_TP);
      long   posType   = PositionGetInteger(POSITION_TYPE);
      double bid       = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask       = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      if(posType == POSITION_TYPE_BUY)
      {
         // Buy: ถ้ากำไร >= threshold และ SL ยังต่ำกว่า entry
         if(bid >= openPrice + beActivatePrice && currentSL < openPrice)
         {
            double newSL = NormalizeDouble(openPrice + _Point, _Digits);
            trade.PositionModify(ticket, newSL, currentTP);
         }
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         // Sell: ถ้ากำไร >= threshold และ SL ยังสูงกว่า entry
         if(ask <= openPrice - beActivatePrice && currentSL > openPrice)
         {
            double newSL = NormalizeDouble(openPrice - _Point, _Digits);
            trade.PositionModify(ticket, newSL, currentTP);
         }
      }
   }
}
```

---

## Trailing Stop Pattern (ATR-Based)

```mql5
// Trailing stop ตาม ATR (v1.5: + trail step) / ATR-based trailing stop with step
// v1.5: เพิ่ม trailStep ป้องกัน micro-adjustment ที่เสีย spread ซ้ำซ้อน
// trailDist  = ATR × InpTrailATRMultiplier (default 2.0)
// trailStep  = ATR × InpTrailStepMult (default 0.5, ~$2.50 for Gold M15)
void TrailingStopATR(CTrade &trade, int magic, double atrValue,
                     double multiplier, double stepMultiplier)
{
   double trailDist = atrValue * multiplier;
   double trailStep = atrValue * stepMultiplier;  // v1.5: min SL movement

   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionGetSymbol(i) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != magic) continue;

      ulong  ticket    = PositionGetInteger(POSITION_TICKET);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double currentSL = PositionGetDouble(POSITION_SL);
      double currentTP = PositionGetDouble(POSITION_TP);
      long   posType   = PositionGetInteger(POSITION_TYPE);
      double bid       = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask       = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

      if(posType == POSITION_TYPE_BUY)
      {
         double newSL = NormalizeDouble(bid - trailDist, _Digits);
         // Trail เฉพาะถ้า SL ใหม่สูงกว่าเดิม + ขยับมากพอ (trailStep)
         if(newSL > currentSL && newSL > openPrice
            && (newSL - currentSL) >= trailStep)  // v1.5: step check
            trade.PositionModify(ticket, newSL, currentTP);
      }
      else if(posType == POSITION_TYPE_SELL)
      {
         double newSL = NormalizeDouble(ask + trailDist, _Digits);
         if(newSL < currentSL && newSL < openPrice
            && (currentSL - newSL) >= trailStep)  // v1.5: step check
            trade.PositionModify(ticket, newSL, currentTP);
      }
   }
}
```

---

## Close All Positions Pattern

```mql5
// ปิดทุก position / Close all positions
void CloseAllPositions(CTrade &trade, string symbol, int magic)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)  // ย้อนกลับเสมอ!
   {
      if(PositionGetSymbol(i) != symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != magic) continue;

      ulong ticket = PositionGetInteger(POSITION_TICKET);
      if(!trade.PositionClose(ticket))
         Print("Close failed: ticket=", ticket, " error=", trade.ResultRetcode());
   }
}
```

---

## Error Handling Checklist

| Check | Code | When |
|-------|------|------|
| Trade success | `trade.ResultRetcode() == TRADE_RETCODE_DONE` | After every trade |
| Valid lots | `lots >= SYMBOL_VOLUME_MIN` | Before trade |
| Spread OK | `spread < maxSpread` | Before entry |
| SL distance | `MathAbs(entry - sl) >= stopsLevel * _Point` | Before trade |
| Max positions | `CountPositions() < maxPos` | Before entry |
| Drawdown | `equity / balance >= threshold` | Before entry |
