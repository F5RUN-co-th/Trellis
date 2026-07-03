//+------------------------------------------------------------------+
//|  TrellisRisk.mqh                                                  |
//|  Trellis EA — Risk Controller (kill-switch layer)                |
//|  Phase 1 (survival-first). อ้างอิง Plan/TRELLIS-003 §2.1 + §3.1   |
//|                                                                  |
//|  v2 (fix Engineer round-10):                                     |
//|   - equity-stop = peak-equity HWM max-DD kill (HIGH#1)           |
//|   - daily-DD -> PAUSED จริง (HIGH#2) + consec-loss breaker (M3)   |
//|   - terminal flag เข้า persist set (M4) · tester GV clear (M5)    |
//|   - log retcode หลัง close fail (M6)                             |
//+------------------------------------------------------------------+
#property strict
#include <Trade\Trade.mqh>

//--- สถานะ EA / EA states (ตัด RECOVERY — กัน martingale, Doctrine #2)
enum ENUM_TRL_STATE
  {
   TRL_IDLE     = 0,   // flat, entry ได้
   TRL_GRID     = 1,   // basket เปิดอยู่
   TRL_CLOSING  = 2,   // ปิด basket (retry ข้าม tick จนแบน)
   TRL_PAUSED   = 3,   // block entry ชั่วคราว (daily-DD/consec) auto-resume วันใหม่
   TRL_HALT     = 4    // terminal (equity-stop/escalate) รอ manual reset
  };

//+------------------------------------------------------------------+
class CTrellisRisk
  {
private:
   CTrade           *m_trade;
   string            m_symbol;
   long              m_magic;

   //--- parameters (% ของ balance — scale-invariant, §8)
   double            m_hardstop_pct;
   double            m_dailydd_pct;
   double            m_equitystop_pct;   // daily soft-stop (PAUSE/วัน)
   double            m_max_total_dd;     // cumulative catastrophe HALT (% จาก all-time peak)
   double            m_min_margin_lvl;
   int               m_max_spread_pts;
   int               m_max_close_retry;
   int               m_max_consec_losses;

   //--- state (persisted — P1)
   ENUM_TRL_STATE    m_state;
   double            m_equity_basket_open; // baseline equity-delta P/L
   double            m_peak_equity;        // high-water-mark (HIGH#1)
   double            m_day_start_equity;   // baseline daily-DD
   int               m_consec_losses;
   int               m_close_retry;
   bool              m_terminal_pending;   // CLOSING เสร็จแล้วไป HALT (M4)
   datetime          m_day_stamp;
   string            m_gp;                 // GlobalVariable prefix
   string            m_close_reason;       // สาเหตุปิดล่าสุด (diagnostic log — read-only)
   int               m_blocked_dir;        // G1 re-entry guard: ทิศที่ถูกบล็อก (0=none) — TRELLIS-007

   //--- helpers ----------------------------------------------------
   double            Equity()  const { return AccountInfoDouble(ACCOUNT_EQUITY);  }
   double            Balance() const { return AccountInfoDouble(ACCOUNT_BALANCE); }

   int               CountPositions() const
     {
      int cnt = 0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         if(PositionGetTicket(i) == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
         if(PositionGetInteger(POSITION_MAGIC) != m_magic)  continue;
         cnt++;
        }
      return cnt;
     }

   double            BasketProfitSum() const
     {
      double p = 0.0;
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         if(PositionGetTicket(i) == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
         if(PositionGetInteger(POSITION_MAGIC) != m_magic)  continue;
         p += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP);
        }
      return p;
     }

   //--- basket P/L = equity-delta (C4); fallback profit-sum
   double            BasketPnL() const
     {
      if(m_equity_basket_open > 0.0) return Equity() - m_equity_basket_open;
      return BasketProfitSum();
     }

   double            SpreadPoints() const
     { return (double)SymbolInfoInteger(m_symbol, SYMBOL_SPREAD); }

   //--- persistence (P1) — ครบทุก state field รวม terminal_pending (M4)
   void              PersistState()
     {
      GlobalVariableSet(m_gp + "state",     (double)m_state);
      GlobalVariableSet(m_gp + "eq_open",   m_equity_basket_open);
      GlobalVariableSet(m_gp + "peak",      m_peak_equity);
      GlobalVariableSet(m_gp + "day_eq",    m_day_start_equity);
      GlobalVariableSet(m_gp + "day_stamp", (double)m_day_stamp);
      GlobalVariableSet(m_gp + "consec",    (double)m_consec_losses);
      GlobalVariableSet(m_gp + "retry",     (double)m_close_retry);
      GlobalVariableSet(m_gp + "term",      m_terminal_pending ? 1.0 : 0.0);
      GlobalVariableSet(m_gp + "blkdir",    (double)m_blocked_dir);
     }

   void              LoadState()
     {
      if(GlobalVariableCheck(m_gp + "state"))     m_state = (ENUM_TRL_STATE)(int)GlobalVariableGet(m_gp + "state");
      if(GlobalVariableCheck(m_gp + "eq_open"))   m_equity_basket_open = GlobalVariableGet(m_gp + "eq_open");
      if(GlobalVariableCheck(m_gp + "peak"))      m_peak_equity        = GlobalVariableGet(m_gp + "peak");
      if(GlobalVariableCheck(m_gp + "day_eq"))    m_day_start_equity   = GlobalVariableGet(m_gp + "day_eq");
      if(GlobalVariableCheck(m_gp + "day_stamp")) m_day_stamp = (datetime)(long)GlobalVariableGet(m_gp + "day_stamp");
      if(GlobalVariableCheck(m_gp + "consec"))    m_consec_losses = (int)GlobalVariableGet(m_gp + "consec");
      if(GlobalVariableCheck(m_gp + "retry"))     m_close_retry   = (int)GlobalVariableGet(m_gp + "retry");
      if(GlobalVariableCheck(m_gp + "term"))      m_terminal_pending = (GlobalVariableGet(m_gp + "term") > 0.5);
      if(GlobalVariableCheck(m_gp + "blkdir"))    m_blocked_dir = (int)GlobalVariableGet(m_gp + "blkdir");
     }

   bool              IsNewDay()
     {
      MqlDateTime now, ref;
      TimeToStruct(TimeCurrent(), now);
      TimeToStruct(m_day_stamp, ref);
      return (now.day != ref.day || now.mon != ref.mon || now.year != ref.year);
     }

   //--- entry gate: PAUSED ถ้า daily-DD หรือ consec-loss breach (flat เท่านั้น)
   ENUM_TRL_STATE    EntryGateState()
     {
      double dayref = (m_day_start_equity > 0.0 ? m_day_start_equity : Balance());
      double day_dd = (dayref > 0.0 ? (dayref - Equity()) / dayref * 100.0 : 0.0);
      if(day_dd >= m_dailydd_pct) return TRL_PAUSED;                       // HIGH#2
      if(m_max_consec_losses > 0 && m_consec_losses >= m_max_consec_losses)
         return TRL_PAUSED;                                               // M3
      return TRL_IDLE;
     }

   void              EnterClosing(string reason, bool terminal)
     {
      m_close_reason = reason;   // เก็บให้ diagnostic log อ่าน (ไม่มีผลต่อ logic)
      PrintFormat("TRL: KILL [%s] basketPnL=%.2f peakDD=%.2f%% -> CLOSING%s",
                  reason, BasketPnL(),
                  (m_peak_equity > 0 ? (m_peak_equity - Equity()) / m_peak_equity * 100.0 : 0.0),
                  terminal ? " (terminal->HALT)" : "");
      m_state            = TRL_CLOSING;
      m_close_retry      = 0;
      m_terminal_pending = terminal;
      PersistState();
     }

   //--- CLOSING step: ปิด 1 รอบ/tick, ไม่ block OnTick (P2)
   void              ClosingStep()
     {
      for(int i = PositionsTotal() - 1; i >= 0; i--)
        {
         ulong tk = PositionGetTicket(i);
         if(tk == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) != m_symbol) continue;
         if(PositionGetInteger(POSITION_MAGIC) != m_magic)  continue;
         if(!m_trade.PositionClose(tk))
            PrintFormat("TRL: PositionClose(%I64u) fail retcode=%d", tk, m_trade.ResultRetcode()); // M6
        }

      if(CountPositions() == 0)
        {
         bool was_loss = (BasketPnL() < 0.0);
         OnBasketClosed(was_loss);
        }
      else
        {
         m_close_retry++;
         if(m_close_retry >= m_max_close_retry)
           {
            PrintFormat("TRL: CLOSING escalate — ปิดไม่สำเร็จ %d ครั้ง -> HALT", m_close_retry);
            m_state            = TRL_HALT;
            m_terminal_pending = false;
            PersistState();
           }
        }
     }

public:
                     CTrellisRisk(void) : m_trade(NULL), m_symbol(""), m_magic(0),
                                          m_hardstop_pct(5.0), m_dailydd_pct(5.0),
                                          m_equitystop_pct(12.0), m_min_margin_lvl(300.0),
                                          m_max_spread_pts(50), m_max_close_retry(10),
                                          m_max_consec_losses(5), m_max_total_dd(25.0), m_state(TRL_IDLE),
                                          m_equity_basket_open(0.0), m_peak_equity(0.0),
                                          m_day_start_equity(0.0), m_consec_losses(0),
                                          m_close_retry(0), m_terminal_pending(false),
                                          m_day_stamp(0), m_gp(""), m_close_reason(""),
                                          m_blocked_dir(0) {}

   bool              Init(CTrade *t, string sym, long magic, double hs, double dd, double es,
                          double mml, int msp, int mcr, int mcl, double mtd)
     {
      if(t == NULL) { Print("TRL: CTrade is NULL"); return false; }
      m_trade=t; m_symbol=sym; m_magic=magic;
      m_hardstop_pct=hs; m_dailydd_pct=dd; m_equitystop_pct=es; m_min_margin_lvl=mml;
      m_max_spread_pts=msp; m_max_close_retry=mcr; m_max_consec_losses=mcl; m_max_total_dd=mtd;
      m_gp = StringFormat("TRL_%s_%I64d_", sym, magic);
      // M5: tester/optimization -> เริ่ม state สะอาดทุก pass (กัน GV leak ข้าม pass)
      if(MQLInfoInteger(MQL_TESTER) || MQLInfoInteger(MQL_OPTIMIZATION))
         GlobalVariablesDeleteAll(m_gp);
      return true;
     }

   //--- RECONSTRUCT (OnInit) — P1/C2
   void              Reconstruct()
     {
      LoadState();
      if(m_peak_equity <= 0.0)      m_peak_equity      = Equity();
      if(m_day_start_equity <= 0.0 || IsNewDay())
        { m_day_start_equity = MathMax(Balance(), Equity()); m_day_stamp = TimeCurrent(); }

      int n = CountPositions();
      if(n > 0)
        {
         if(m_equity_basket_open <= 0.0) m_equity_basket_open = Equity() - BasketProfitSum();
         if(m_state == TRL_IDLE || m_state == TRL_PAUSED) m_state = TRL_GRID;
         PrintFormat("TRL: RECONSTRUCT %d positions -> state=%d (kill-checks รัน tick ถัด)", n, m_state);
        }
      else
        {
         if(m_state == TRL_CLOSING || m_state == TRL_GRID) m_state = TRL_IDLE;
         m_equity_basket_open = 0.0;
         m_terminal_pending   = false;
        }
      PersistState();
     }

   //--- basket lifecycle hooks (grid module เรียกทีหลัง) ----------
   void              OnBasketOpened(double equity_before = 0.0)
     {
      m_equity_basket_open = (equity_before > 0.0 ? equity_before : Equity()); // L7: capture ก่อน entry
      m_close_retry        = 0;
      m_close_reason       = "";   // เคลียร์ — position ที่หายเองโดยไม่ผ่าน EnterClosing (เช่น server SL) จะได้ไม่ติด reason เก่า
      if(m_state == TRL_IDLE || m_state == TRL_PAUSED) m_state = TRL_GRID;
      PersistState();
     }

   void              OnBasketClosed(bool was_loss)
     {
      if(was_loss) m_consec_losses++; else m_consec_losses = 0;
      m_equity_basket_open = 0.0;
      m_state = m_terminal_pending ? TRL_HALT : EntryGateState();   // M3: consec/daily -> PAUSED
      m_terminal_pending = false;
      PersistState();
     }

   //--- dispatcher: เรียกทุก tick จาก OnTick ----------------------
   void              OnTick()
     {
      if(m_state == TRL_HALT) return;

      double eq  = Equity();
      double bal = Balance();
      if(eq > m_peak_equity) m_peak_equity = eq;            // HWM update (HIGH#1)

      if(IsNewDay())
        {
         m_day_start_equity = MathMax(bal, eq);             // daily baseline (peak ไม่ reset = all-time, ใช้ cumulative HALT)
         m_day_stamp        = TimeCurrent();
         m_consec_losses    = 0;
         if(m_state == TRL_PAUSED) m_state = TRL_IDLE;      // auto-resume วันใหม่
         PersistState();
        }

      //--- (1) CUMULATIVE catastrophe HALT (terminal) — all-time peak HWM (C2: กัน −98% ซ้ำ) ---
      if(m_peak_equity > 0.0 && (m_peak_equity - eq) / m_peak_equity * 100.0 >= m_max_total_dd)
        {
         if(CountPositions() > 0) { EnterClosing("max-total-DD", true); ClosingStep(); }
         else { m_state = TRL_HALT; m_terminal_pending = false; PersistState();
                PrintFormat("TRL: max-total-DD %.1f%% (flat) -> HALT", (m_peak_equity - eq) / m_peak_equity * 100.0); }
         return;
        }
      //--- (2) DAILY soft-stop (non-terminal): ปิด basket + PAUSED → resume วันใหม่ (keep trading) ---
      if(m_day_start_equity > 0.0 && (m_day_start_equity - eq) / m_day_start_equity * 100.0 >= m_equitystop_pct)
        {
         if(CountPositions() > 0) { EnterClosing("day-stop", false); ClosingStep(); }
         else if(m_state != TRL_PAUSED) { m_state = TRL_PAUSED; PersistState(); }
         return;
        }

      switch(m_state)
        {
         case TRL_CLOSING:
            ClosingStep();
            return;
         case TRL_GRID:
            if(CountPositions() > 0)
              {
               double mlvl = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
               if(mlvl > 0.0 && mlvl < m_min_margin_lvl) { EnterClosing("margin-level", true); ClosingStep(); return; }
               double cap = -bal * m_hardstop_pct / 100.0;
               if(BasketPnL() <= cap) { EnterClosing("hard-stop", false); ClosingStep(); return; }
              }
            else { m_state = EntryGateState(); PersistState(); }   // basket หายเอง
            return;
         case TRL_IDLE:
         case TRL_PAUSED:
         default:
            m_state = EntryGateState();    // re-evaluate daily-DD/consec gate (HIGH#2/M3)
            return;
        }
     }

   //--- accessors / control ---------------------------------------
   ENUM_TRL_STATE    State()             const { return m_state; }
   string            CloseReason()       const { return m_close_reason; }

   //--- G1 re-entry guard (TRELLIS-007): state อยู่ใน risk เพื่อได้ persist + tester-clear เดิม
   int               BlockedDir()        const { return m_blocked_dir; }
   void              SetBlock(int dir)
     {
      m_blocked_dir = dir;   // single-slot: event ใหม่เขียนทับ (doc §2 G1)
      PersistState();
      PrintFormat("TRL: G1 block dir=%d (run-over — รอ close ข้าม EMA กลับ)", dir);
     }
   void              ClearBlock()
     {
      if(m_blocked_dir == 0) return;
      PrintFormat("TRL: G1 unblock dir=%d", m_blocked_dir);
      m_blocked_dir = 0;
      PersistState();
     }
   int               ConsecutiveLosses() const { return m_consec_losses; }
   double            PeakEquity()        const { return m_peak_equity; }
   bool              SpreadOK()          const { return SpreadPoints() <= m_max_spread_pts; }
   bool              EntryAllowed()      const { return m_state == TRL_IDLE; }
   int               Positions()         const { return CountPositions(); }
   double            BasketProfit()      const { return BasketPnL(); }            // floating P/L (equity-delta)
   //--- X1 (TRELLIS-007): ปิด same-tick — pattern เดียวกับ kill ภายใน (EnterClosing + ClosingStep)
   void              RequestClose(string r)
     { if(m_state == TRL_GRID) { EnterClosing(r, false); ClosingStep(); } }
   void              ResetHalt() { if(m_state == TRL_HALT) { m_state = TRL_IDLE; PersistState(); } }
   void              Deinit()    { PersistState(); }
  };
//+------------------------------------------------------------------+
