# Indicator Pattern (MQL5)

วิธีสร้างและใช้ indicator ใน MQL5 EA อย่างถูกต้อง

---

## Golden Rule

```
OnInit()  → สร้าง handle (iMA, iRSI, iATR, etc.)
OnTick()  → อ่านค่าด้วย CopyBuffer / CopyRates
OnDeinit() → ปล่อย handle ด้วย IndicatorRelease
```

**ห้ามเด็ดขาด:** สร้าง handle ใน OnTick() (MQL4 style)

---

## Step 1: Create Handle in OnInit()

```mql5
// === Global Variables / ตัวแปร Global ===
int g_atrHandle;     // ATR handle
int g_maFastHandle;  // Fast MA handle
int g_maSlowHandle;  // Slow MA handle

int OnInit()
{
   // สร้าง ATR handle / Create ATR handle
   g_atrHandle = iATR(_Symbol, PERIOD_M15, 14);
   if(g_atrHandle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot create ATR handle");
      return INIT_FAILED;
   }

   // สร้าง MA handles / Create MA handles
   g_maFastHandle = iMA(_Symbol, PERIOD_H4, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_maSlowHandle = iMA(_Symbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);

   if(g_maFastHandle == INVALID_HANDLE || g_maSlowHandle == INVALID_HANDLE)
   {
      Print("ERROR: Cannot create MA handles");
      return INIT_FAILED;
   }

   return INIT_SUCCEEDED;
}
```

---

## Step 2: Read Values in OnTick()

```mql5
void OnTick()
{
   // === CopyBuffer Pattern ===
   double atr[];
   ArraySetAsSeries(atr, true);  // index 0 = ล่าสุด / most recent

   if(CopyBuffer(g_atrHandle, 0, 0, 3, atr) < 3)
      return;  // ข้อมูลไม่พอ / Not enough data

   double currentATR = atr[0];   // ATR ปัจจุบัน / Current ATR
   double prevATR    = atr[1];   // ATR ก่อนหน้า / Previous ATR

   // === CopyRates Pattern (OHLC data) ===
   MqlRates rates[];
   ArraySetAsSeries(rates, true);

   if(CopyRates(_Symbol, PERIOD_M15, 0, 100, rates) < 100)
      return;

   double currentClose = rates[0].close;
   double prevHigh     = rates[1].high;
   double prevLow      = rates[1].low;
}
```

---

## Step 3: Release in OnDeinit()

```mql5
void OnDeinit(const int reason)
{
   // ปล่อย handles ทั้งหมด / Release all handles
   if(g_atrHandle != INVALID_HANDLE)  IndicatorRelease(g_atrHandle);
   if(g_maFastHandle != INVALID_HANDLE) IndicatorRelease(g_maFastHandle);
   if(g_maSlowHandle != INVALID_HANDLE) IndicatorRelease(g_maSlowHandle);
}
```

---

## Multi-Timeframe Pattern

```mql5
// === สร้าง handles สำหรับหลาย timeframe ===
int g_maH4Handle;   // H4 for bias / H4 สำหรับ bias
int g_maM15Handle;  // M15 for entry / M15 สำหรับ entry

int OnInit()
{
   g_maH4Handle  = iMA(_Symbol, PERIOD_H4, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_maM15Handle = iMA(_Symbol, PERIOD_M15, 20, 0, MODE_EMA, PRICE_CLOSE);
   return INIT_SUCCEEDED;
}

void OnTick()
{
   // อ่าน H4 MA / Read H4 MA
   double maH4[];
   ArraySetAsSeries(maH4, true);
   CopyBuffer(g_maH4Handle, 0, 0, 3, maH4);

   // อ่าน M15 MA / Read M15 MA
   double maM15[];
   ArraySetAsSeries(maM15, true);
   CopyBuffer(g_maM15Handle, 0, 0, 3, maM15);

   // H4 bias + M15 entry alignment
   bool h4Bullish  = maH4[0] > maH4[1];
   bool m15Bullish = maM15[0] > maM15[1];
}
```

---

## CopyRates for Higher TF OHLC

```mql5
// อ่าน D1 OHLC สำหรับ PDH/PDL / Read D1 OHLC for PDH/PDL
MqlRates d1[];
ArraySetAsSeries(d1, true);

if(CopyRates(_Symbol, PERIOD_D1, 0, 5, d1) >= 5)
{
   double pdh = d1[1].high;   // Previous Day High
   double pdl = d1[1].low;    // Previous Day Low
   double pwh = 0, pwl = 999999;
   for(int i = 1; i <= 5; i++)
   {
      if(d1[i].high > pwh) pwh = d1[i].high;  // Previous Week High
      if(d1[i].low < pwl)  pwl = d1[i].low;   // Previous Week Low
   }
}
```

---

## New Bar Detection Pattern

```mql5
// ตรวจจับแท่งเทียนใหม่ / Detect new bar
datetime g_lastBarTime = 0;

bool IsNewBar(ENUM_TIMEFRAMES tf = PERIOD_CURRENT)
{
   datetime barTime = iTime(_Symbol, tf, 0);
   if(barTime == g_lastBarTime)
      return false;
   g_lastBarTime = barTime;
   return true;
}

void OnTick()
{
   // วิเคราะห์เฉพาะบาร์ใหม่ / Analyze only on new bar
   if(!IsNewBar(PERIOD_M15))
   {
      // ทำแค่ position management
      ManagePositions();
      return;
   }

   // Core analysis on closed bar
   AnalyzeStructure();
   DetectFVGs();
   CheckEntry();
}
```

---

## Key Rules

| Rule | Do | Don't |
|------|-----|-------|
| Handle creation | `OnInit()` | `OnTick()` |
| Value reading | `CopyBuffer()` | Direct call `iMA()` in loop |
| Array indexing | `ArraySetAsSeries(arr, true)` | Assume index direction |
| Handle cleanup | `IndicatorRelease()` in `OnDeinit()` | Leave handles open |
| Data check | Check `CopyBuffer() >= N` | Assume data exists |
| Timeframe | Explicit `PERIOD_M15` | `PERIOD_CURRENT` for MTF |
