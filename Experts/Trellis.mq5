//+------------------------------------------------------------------+
//|  Trellis.mq5                                                     |
//|  v4.00 — Dual Asian-Range Breakout (trend continuation, M1)      |
//|  อ้างอิง: Scripts/asian_bo_sim.py + edge_screen2.py (2026-07-03) |
//|                                                                  |
//|  LONG : M1 close แรกของวันทะลุ Asian High (01:00-07:59 server)   |
//|         ช่วง 08:00-19:59 + close > EMA(2880) + slope EMA 1 วัน   |
//|         > +0.1% ของราคา                                          |
//|  SHORT: mirror (ทะลุ Asian Low + regime ลง) — ศูนย์ param ใหม่    |
//|  Stop : ขอบ Asian ฝั่งตรงข้าม (cap 1×R จาก entry) — SL จริงบน server |
//|  Trail: กำไร ≥ 1×R → เลื่อน SL ตาม best close − 0.75×R (per bar)  |
//|  Exit : 23:00 server = ปิดวัน · 1 เทรด/วัน · 1 position เท่านั้น   |
//|  Risk : CTrellisRisk เดิมทั้งชุด (hard-stop/daily/total-DD = backstop) |
//+------------------------------------------------------------------+
#property copyright "Trellis"
#property version   "4.00"
#property strict

#include <Trade\Trade.mqh>
#include "..\Include\TrellisRisk.mqh"
#include "..\Include\TrellisDiag.mqh"

//+------------------------------------------------------------------+
//| Inputs — เฉพาะที่ต้องตั้งจริง (กฎ: จอวินเห็น comment ไม่ใช่ชื่อตัวแปร) |
//+------------------------------------------------------------------+
input group "=== Trellis v4 Validation ==="
input string InpDiagTag          = "v4_run1";  // DiagTag = ชื่อรอบ (เปลี่ยนทุกรอบ)
input bool   InpAllowShort       = true;       // AllowShort = เปิดฝั่ง SHORT mirror
input int    InpHourShift        = 0;          // HourShift: tester XAUUSD_BT = 0 · Exness live/demo = -1 (AUTO: UTC+0 -> BT-clock ตาม EU DST)

//--- strategy constants — ค่าที่ anchored walk-forward เลือก (Scripts/walk_forward.py
//    เลือก config นี้ 11/12 ปี, train 2012-2026) — ห้ามแก้มือ ต้องผ่าน WF protocol เท่านั้น
const int    C_EMA_PERIOD      = 2880;    // EMA regime (~2 วัน M1)
const int    C_SLOPE_BARS      = 1440;    // slope lookback (~1 วัน)
const double C_SLOPE_MIN_FRAC  = 0.0005;  // slope ขั้นต่ำ = 0.05% ของราคา/วัน (WF-selected)
const double C_CAP_R           = 1.0;     // stop ไม่เกิน 1×R จาก entry
const double C_TRAIL_ARM_R     = 1.0;     // เริ่ม trail เมื่อกำไร ≥ 1×R
const double C_TRAIL_DIST_R    = 1.0;     // ระยะ trail = 1×R จาก best close (WF-selected)
const double C_MAX_RISK_FRAC   = 0.02;    // risk-cap: ข้ามวันที่ 1×R > 2% ของ equity (survival-first บนทุนเล็ก — วินสั่ง 2026-07-03)
const int    C_ASIA_H0 = 1, C_ASIA_H1 = 8;      // Asian range window (server)
const int    C_ENTRY_H0 = 8, C_ENTRY_H1 = 20;   // entry window
const int    C_EOD_HOUR = 23;                    // ปิดวัน (จ.-พฤ.)
const int    C_EOD_FRI  = 20;                    // ศุกร์ปิด 20:00 — ตลาดบางศุกร์ปิดเร็วสุด 20:xx (จาก data 2012-24) ห้ามถือข้าม weekend

//--- risk constants (v2/v3 เดิม — scale-invariant % of balance)
const double InpBasketHardStopPct = 5.0;
const double InpDailyDDPct        = 5.0;
const double InpEquityStopPct     = 8.0;
const double InpMaxTotalDDPct     = 25.0;
const double InpMinMarginLevel    = 300.0;
const int    InpMaxSpreadPoints   = 200;
const int    InpMaxCloseRetry     = 100;  // 10 เดิมบางไป — ตลาด reopen reject ได้หลายวินาที (บทเรียน halt-escalate 2025.03.23)
const int    InpMaxConsecLosses   = 0;
const double InpStartLot          = 0.01;
const bool   InpDiagEnabled       = true;
const long   InpMagic             = 770001;

//--- globals -------------------------------------------------------
CTrade        g_trade;
CTrellisRisk  g_risk;
CTrellisDiag  g_diag;
int           g_ema      = INVALID_HANDLE;
datetime      g_lastbar  = 0;
ENUM_TRL_STATE g_prev    = TRL_IDLE;
// Asian range ของวันปัจจุบัน / current-day Asian range
int           g_day      = -1;      // วัน (server) ที่กำลัง track
double        g_ash      = 0.0, g_asl = 0.0;
bool          g_as_ok    = false;
int           g_traded_day = -1;    // วันสุดท้ายที่เข้าไม้แล้ว (1 เทรด/วัน)
// position management (persist ผ่าน GV — restart กลาง position ต้องไม่เสีย trail/day-guard)
int           g_dir      = 0;
double        g_R        = 0.0;
double        g_best     = 0.0;     // best close ระหว่างถือ (trail)
double        g_entry    = 0.0;
string        g_gp       = "";      // GV prefix (pattern เดียวกับ CTrellisRisk)

void SaveState()
  {
   GlobalVariableSet(g_gp + "dir",   (double)g_dir);
   GlobalVariableSet(g_gp + "R",     g_R);
   GlobalVariableSet(g_gp + "best",  g_best);
   GlobalVariableSet(g_gp + "entry", g_entry);
   GlobalVariableSet(g_gp + "tday",  (double)g_traded_day);
  }

void LoadState()
  {
   if(GlobalVariableCheck(g_gp + "dir"))   g_dir        = (int)GlobalVariableGet(g_gp + "dir");
   if(GlobalVariableCheck(g_gp + "R"))     g_R          = GlobalVariableGet(g_gp + "R");
   if(GlobalVariableCheck(g_gp + "best"))  g_best       = GlobalVariableGet(g_gp + "best");
   if(GlobalVariableCheck(g_gp + "entry")) g_entry      = GlobalVariableGet(g_gp + "entry");
   if(GlobalVariableCheck(g_gp + "tday"))  g_traded_day = (int)GlobalVariableGet(g_gp + "tday");
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   g_trade.SetExpertMagicNumber(InpMagic);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   g_trade.SetAsyncMode(false);

   g_ema = iMA(_Symbol, PERIOD_M1, C_EMA_PERIOD, 0, MODE_EMA, PRICE_CLOSE);
   if(g_ema == INVALID_HANDLE) { Print("Trellis: EMA handle FAILED"); return INIT_FAILED; }

   if(!g_risk.Init(GetPointer(g_trade), _Symbol, InpMagic,
                   InpBasketHardStopPct, InpDailyDDPct, InpEquityStopPct,
                   InpMinMarginLevel, InpMaxSpreadPoints, InpMaxCloseRetry,
                   InpMaxConsecLosses, InpMaxTotalDDPct))
      return INIT_FAILED;
   g_risk.Reconstruct();

   if(!g_diag.Init(InpMagic, InpDiagTag, InpDiagEnabled))
      return INIT_FAILED;

   // strategy state: persist/restore (B4) + tester-clear ต่อ pass (pattern CTrellisRisk)
   g_gp = StringFormat("TRL4_%s_%I64d_", _Symbol, InpMagic);
   if(MQLInfoInteger(MQL_TESTER) || MQLInfoInteger(MQL_OPTIMIZATION))
      GlobalVariablesDeleteAll(g_gp);
   LoadState();
   if(g_risk.Positions() == 0) { g_dir = 0; g_R = 0.0; g_best = 0.0; g_entry = 0.0; SaveState(); }

   PrintFormat("Trellis v4 (Dual Asian BO) init | %s magic=%I64d short=%s",
               _Symbol, InpMagic, InpAllowShort ? "on" : "off");
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   if(g_ema != INVALID_HANDLE) IndicatorRelease(g_ema);
   g_diag.Deinit();
   g_risk.Deinit();
  }

//+------------------------------------------------------------------+
void OnTick()
  {
   g_risk.OnTick();
   ENUM_TRL_STATE st = g_risk.State();

   // position จบชีวิต -> diag row + reset (pattern v3)
   if((g_prev == TRL_GRID || g_prev == TRL_CLOSING) && st != TRL_GRID && st != TRL_CLOSING)
     {
      string reason = g_risk.CloseReason();
      if(reason == "") reason = "sl-exit";               // ปิดโดย server SL (stop เริ่มต้น/trail)
      if(g_risk.Positions() > 0) reason = "halt-escalate:" + reason;
      g_diag.OnClose(reason);
      g_dir = 0; g_R = 0.0; g_best = 0.0; g_entry = 0.0;
      SaveState();
     }
   g_prev = st;

   // B2: consume IsNewBar จุดเดียว + track range ทุก new bar โดยไม่ขึ้นกับ spread/state
   bool newbar = IsNewBar();
   if(newbar) UpdateAsianRange();

   // SL จริงอยู่บน server — ถ้าโดน SL position หายเอง risk จะ transition ให้
   if(st == TRL_GRID && g_risk.Positions() > 0)
     {
      g_diag.OnTickUpdate(g_risk.BasketProfit());
      ManagePosition(newbar);
     }
   else if(st == TRL_IDLE && newbar && g_risk.SpreadOK())
      TryEntry();
  }

//+------------------------------------------------------------------+
//| track Asian range จาก closed bars + reset ข้ามวัน                 |
//+------------------------------------------------------------------+
// EU DST: last Sunday Mar -> last Sunday Oct — BT-clock = EET แท้ (พิสูจน์ price-match
// shoulder weeks, TRELLIS-010 Stage 0: M1 bar 2025.03.17 00:00 = raw 2025.03.16 22:00 UTC)
// ขอบเขตระดับวันพอ: จุดสลับจริง 01:00 UTC วันอาทิตย์ = ตลาดทองปิด ไม่มี tick คร่อม
bool IsEuDST(datetime t)
  {
   MqlDateTime dt;
   TimeToStruct(t, dt);
   datetime mar31 = StringToTime(StringFormat("%04d.03.31", dt.year));
   MqlDateTime m; TimeToStruct(mar31, m);
   datetime marLastSun = mar31 - (datetime)(m.day_of_week * 86400);
   datetime oct31 = StringToTime(StringFormat("%04d.10.31", dt.year));
   MqlDateTime oc; TimeToStruct(oct31, oc);
   datetime octLastSun = oct31 - (datetime)(oc.day_of_week * 86400);
   return (t >= marLastSun && t < octLastSun);
  }

// แปลงเวลา broker -> BT-clock (session ทั้งหมด calibrate บน BT-clock: UTC+2 หนาว / UTC+3 ร้อน กฎ EU)
// InpHourShift: 0 = broker เป็น BT-clock แล้ว (tester) · -1 = AUTO สำหรับ broker UTC+0 (Exness) · อื่นๆ = fix
datetime ToBT(datetime t)
  {
   int sh = InpHourShift;
   if(sh == -1) sh = IsEuDST(t) ? 3 : 2;
   return t + (datetime)(sh * 3600);
  }

void UpdateAsianRange()
  {
   datetime bt = ToBT(iTime(_Symbol, PERIOD_M1, 1));   // closed bar (BT-clock)
   MqlDateTime dt;
   TimeToStruct(bt, dt);
   int d = (int)((long)bt / 86400);
   if(d != g_day) { g_day = d; g_as_ok = false; g_ash = 0.0; g_asl = 0.0; }
   if(dt.hour >= C_ASIA_H0 && dt.hour < C_ASIA_H1)
     {
      double hi = iHigh(_Symbol, PERIOD_M1, 1), lo = iLow(_Symbol, PERIOD_M1, 1);
      if(!g_as_ok) { g_ash = hi; g_asl = lo; g_as_ok = true; }
      else         { g_ash = MathMax(g_ash, hi); g_asl = MathMin(g_asl, lo); }
     }
  }

//+------------------------------------------------------------------+
//| Entry: first close ทะลุขอบ Asian + regime EMA slope               |
//+------------------------------------------------------------------+
void TryEntry()
  {
   if(!g_as_ok || g_ash <= g_asl) return;
   if(g_day == g_traded_day) return;                       // 1 เทรด/วัน

   MqlDateTime dt;
   TimeToStruct(ToBT(iTime(_Symbol, PERIOD_M1, 1)), dt);
   if(dt.hour < C_ENTRY_H0 || dt.hour >= C_ENTRY_H1) return;

   double c1 = iClose(_Symbol, PERIOD_M1, 1);
   double c2 = iClose(_Symbol, PERIOD_M1, 2);

   // EMA ที่ closed bar + slope ~1 วัน / EMA at closed bar + 1-day slope
   double e_now[], e_old[];
   if(CopyBuffer(g_ema, 0, 1, 1, e_now) < 1) return;
   if(CopyBuffer(g_ema, 0, 1 + C_SLOPE_BARS, 1, e_old) < 1) return;
   double slope = e_now[0] - e_old[0];

   int dir = 0;
   if(c1 > g_ash && c2 <= g_ash &&
      c1 > e_now[0] && slope > C_SLOPE_MIN_FRAC * c1)
      dir = 1;
   else if(InpAllowShort && c1 < g_asl && c2 >= g_asl &&
           c1 < e_now[0] && slope < -C_SLOPE_MIN_FRAC * c1)
      dir = -1;
   if(dir == 0) return;

   double R    = g_ash - g_asl;
   // Risk-cap: 0.01 lot gold = $1 P&L ต่อ $1 -> risk ที่ stop ~= 1xR (USD) · เกินเพดาน %equity = ไม่เทรดวันนี้
   if(R > C_MAX_RISK_FRAC * AccountInfoDouble(ACCOUNT_EQUITY)) return;
   double bid  = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask  = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double lot  = NormalizeLot(InpStartLot);
   double px   = (dir == 1 ? ask : bid);
   double sl   = (dir == 1 ? MathMax(g_asl, px - C_CAP_R * R)
                           : MathMin(g_ash, px + C_CAP_R * R));
   sl = NormalizeDouble(sl, _Digits);
   double eq_before = AccountInfoDouble(ACCOUNT_EQUITY);

   bool ok = (dir == 1 ? g_trade.Buy(lot, _Symbol, px, sl, 0, "TRL4-long")
                       : g_trade.Sell(lot, _Symbol, px, sl, 0, "TRL4-short"));
   if(!ok || g_trade.ResultRetcode() != TRADE_RETCODE_DONE)
     {
      PrintFormat("TRL4: entry fail retcode=%d", g_trade.ResultRetcode());
      return;
     }
   g_dir = dir; g_R = R; g_entry = px; g_best = px;
   g_traded_day = g_day;
   SaveState();
   g_risk.OnBasketOpened(eq_before);
   // diag: ใช้ช่อง atr เก็บ R (range) · dev=slope/price · er=-1 (n/a)
   g_diag.OnOpen(dir, -1.0, slope / c1 * 1000.0, R,
                 (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD), lot, eq_before);
  }

//+------------------------------------------------------------------+
//| Manage: EOD close + trail SL (per new bar, จาก best close)        |
//+------------------------------------------------------------------+
void ManagePosition(bool newbar)
  {
   // B3+Fri: ปิดเมื่อถึง EOD (ศุกร์ 20:00, วันอื่น 23:00) หรือข้ามวันไปแล้ว (tick หาย/gap)
   datetime now_bt = ToBT(TimeCurrent());
   MqlDateTime dt;
   TimeToStruct(now_bt, dt);
   int today = (int)((long)now_bt / 86400);
   int eod_h = (dt.day_of_week == 5 ? C_EOD_FRI : C_EOD_HOUR);
   if(dt.hour >= eod_h || (g_traded_day > 0 && today != g_traded_day))
     {
      g_risk.RequestClose("eod");
      return;
     }
   if(!newbar) return;
   // restart กลาง position ที่ state หายจริงๆ (GV โดนลบ): SL server + EOD ยังคุ้มครองครบ
   if(g_dir == 0 || g_R <= 0.0) return;

   double c1 = iClose(_Symbol, PERIOD_M1, 1);
   g_best = (g_dir == 1 ? MathMax(g_best, c1) : MathMin(g_best, c1));
   SaveState();
   double fav = (g_dir == 1 ? g_best - g_entry : g_entry - g_best);
   if(fav < C_TRAIL_ARM_R * g_R) return;

   double new_sl = (g_dir == 1 ? g_best - C_TRAIL_DIST_R * g_R
                               : g_best + C_TRAIL_DIST_R * g_R);
   new_sl = NormalizeDouble(new_sl, _Digits);

   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != InpMagic) continue;
      double cur_sl = PositionGetDouble(POSITION_SL);
      bool better = (g_dir == 1 ? new_sl > cur_sl + _Point : new_sl < cur_sl - _Point);
      if(better && !g_trade.PositionModify(tk, new_sl, 0.0))
         PrintFormat("TRL4: trail modify fail retcode=%d", g_trade.ResultRetcode());
     }
  }

//+------------------------------------------------------------------+
bool IsNewBar()
  {
   datetime t = iTime(_Symbol, PERIOD_M1, 0);
   if(t != g_lastbar) { g_lastbar = t; return true; }
   return false;
  }

//+------------------------------------------------------------------+
double NormalizeLot(double lot)
  {
   double vmin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double vstep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(vstep <= 0.0) vstep = 0.01;
   lot = MathFloor(lot / vstep) * vstep;
   if(lot < vmin) lot = vmin;
   if(lot > vmax) lot = vmax;
   return NormalizeDouble(lot, 2);
  }
//+------------------------------------------------------------------+
