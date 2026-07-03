//+------------------------------------------------------------------+
//|  TrellisDiag.mqh                                                  |
//|  Trellis EA — per-basket diagnostic logger (TRELLIS-DIAG)         |
//|                                                                  |
//|  Logging เท่านั้น — ห้ามมีผลต่อการตัดสินใจเทรดใดๆ                  |
//|  Logging only — MUST NOT affect any trading decision.            |
//|                                                                  |
//|  Output: CSV 1 แถว/basket ที่ Common\Files\Trellis_diag_*.csv     |
//|  วิเคราะห์ด้วย Scripts/diag_analyze.py                            |
//+------------------------------------------------------------------+
#property strict

class CTrellisDiag
  {
private:
   bool              m_enabled;
   int               m_handle;
   int               m_id;                // running basket counter

   //--- per-basket state ------------------------------------------
   bool              m_open;
   datetime          m_open_time;
   int               m_dir;
   double            m_er;                // ER ตอนเข้า (-1 = ไม่มีข้อมูล)
   double            m_dev_atr;           // |close-EMA| / ATR ตอนเข้า
   double            m_atr;
   int               m_spread;
   int               m_levels;            // grid levels สูงสุดที่ใช้
   double            m_lots;              // lot รวมทั้ง basket
   double            m_eq_open;           // equity ก่อนเปิดไม้แรก (baseline realized)
   bool              m_first;             // ยังไม่เคย update MFE/MAE
   double            m_mfe, m_mae;        // max/min floating P&L (USD, equity-delta)
   datetime          m_mfe_time, m_mae_time;

   void              ResetBasket()
     {
      m_open = false; m_first = true;
      m_open_time = 0; m_dir = 0; m_er = -1.0; m_dev_atr = 0.0; m_atr = 0.0;
      m_spread = 0; m_levels = 0; m_lots = 0.0; m_eq_open = 0.0;
      m_mfe = 0.0; m_mae = 0.0; m_mfe_time = 0; m_mae_time = 0;
     }

   //--- เขียน 1 แถว CSV + flush ทันที (กันข้อมูลหายถ้า tester ตาย)
   void              WriteRow(string reason, double realized)
     {
      datetime now = TimeCurrent();
      MqlDateTime dt;
      TimeToStruct(m_open_time, dt);
      string row = StringFormat(
         "%d,%s,%s,%d,%d,%.4f,%.3f,%.2f,%d,%d,%d,%.2f,%.2f,%d,%.2f,%d,%.2f,%s,%.2f\n",
         m_id,
         TimeToString(m_open_time, TIME_DATE | TIME_SECONDS),
         TimeToString(now,         TIME_DATE | TIME_SECONDS),
         (int)((now - m_open_time) / 60),
         m_dir, m_er, m_dev_atr, m_atr, m_spread, dt.hour,
         m_levels, m_lots,
         m_mfe, (int)((m_mfe_time - m_open_time) / 60),
         m_mae, (int)((m_mae_time - m_open_time) / 60),
         realized, reason,
         AccountInfoDouble(ACCOUNT_BALANCE));
      FileWriteString(m_handle, row);
      FileFlush(m_handle);
     }

public:
                     CTrellisDiag(void) : m_enabled(false), m_handle(INVALID_HANDLE), m_id(0)
     { ResetBasket(); }

   //--- เปิดไฟล์ CSV ใน Common\Files (อยู่รอดหลัง tester จบ) --------
   bool              Init(long magic, string tag, bool enabled)
     {
      m_enabled = enabled;
      if(!m_enabled) return true;

      string name = StringFormat("Trellis_diag_%I64d_%s.csv", magic, tag);
      m_handle = FileOpen(name, FILE_WRITE | FILE_ANSI | FILE_COMMON);
      if(m_handle == INVALID_HANDLE)
        {
         PrintFormat("DIAG: FileOpen(%s) FAILED err=%d", name, GetLastError());   // fail loud
         return false;
        }
      FileWriteString(m_handle,
         "basket_id,open_time,close_time,age_bars,dir,er_entry,dev_atr,atr_entry,"
         "spread_pts,hour,levels_max,lots_total,mfe_usd,mfe_age,mae_usd,mae_age,"
         "realized_usd,exit_reason,balance_after\n");
      FileFlush(m_handle);
      PrintFormat("DIAG: logging -> Common\\Files\\%s", name);
      return true;
     }

   //--- basket เปิด (เรียกหลัง entry สำเร็จ) ------------------------
   void              OnOpen(int dir, double er, double dev_atr, double atr,
                            int spread_pts, double lot, double eq_before)
     {
      if(!m_enabled) return;
      if(m_open)   // ไม่ควรเกิด (one-at-a-time) — fail loud ไม่เขียนทับเงียบ
         PrintFormat("DIAG: OnOpen ทับ basket #%d ที่ยังไม่ปิด — record เดิมหาย", m_id);
      ResetBasket();
      m_open      = true;
      m_id++;
      m_open_time = TimeCurrent();
      m_dir       = dir;
      m_er        = er;
      m_dev_atr   = dev_atr;
      m_atr       = atr;
      m_spread    = spread_pts;
      m_levels    = 1;
      m_lots      = lot;
      m_eq_open   = eq_before;
      m_mfe_time  = m_open_time;
      m_mae_time  = m_open_time;
     }

   //--- grid เติมไม้ -------------------------------------------------
   void              OnFill(int levels, double lot)
     {
      if(!m_enabled || !m_open) return;
      m_levels = (int)MathMax(m_levels, levels);
      m_lots  += lot;
     }

   //--- update MFE/MAE ทุก tick ระหว่าง TRL_GRID ---------------------
   void              OnTickUpdate(double pnl)
     {
      if(!m_enabled || !m_open) return;
      if(m_first || pnl > m_mfe) { m_mfe = pnl; m_mfe_time = TimeCurrent(); }
      if(m_first || pnl < m_mae) { m_mae = pnl; m_mae_time = TimeCurrent(); }
      m_first = false;
     }

   //--- basket ปิด (เรียกตอน state transition -> flat) ---------------
   void              OnClose(string reason)
     {
      if(!m_enabled) return;
      if(!m_open)
        {
         PrintFormat("DIAG: OnClose(%s) ไม่มี basket record — ข้าม (row หาย 1)", reason);   // fail loud
         return;
        }
      WriteRow(reason, AccountInfoDouble(ACCOUNT_EQUITY) - m_eq_open);
      ResetBasket();
     }

   //--- ปิดไฟล์ · basket ค้างตอน test จบ -> flush ด้วย reason test-end
   void              Deinit()
     {
      if(!m_enabled) return;
      if(m_open)
         WriteRow("test-end", AccountInfoDouble(ACCOUNT_EQUITY) - m_eq_open);
      if(m_handle != INVALID_HANDLE) { FileClose(m_handle); m_handle = INVALID_HANDLE; }
     }
  };
//+------------------------------------------------------------------+
