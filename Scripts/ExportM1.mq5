//+------------------------------------------------------------------+
//|  ExportM1.mq5 — export M1 bars ของ chart ปัจจุบันเป็น CSV          |
//|  (Trellis holdout pipeline — ใช้ตอน Dukascopy ล่ม)                |
//|                                                                  |
//|  วิธีใช้: เปิด chart XAUUSD (M1) -> ลาก script นี้ใส่ chart        |
//|  ผลลัพธ์: Common\Files\XAUUSD_M1_export.csv                       |
//|  format เดียวกับ Gloo/Data: date \t time \t O \t H \t L \t C \t vol \t 0 \t spread |
//+------------------------------------------------------------------+
#property copyright "Trellis"
#property version   "1.00"
#property script_show_inputs
#property strict

input datetime InpFrom = D'2026.02.01 00:00';   // เริ่ม (ทับซ้อน Dukascopy 3 สัปดาห์ไว้ cross-check)
input datetime InpTo   = D'2026.12.31 00:00';   // ถึง (เกินปัจจุบัน = เอาถึง bar ล่าสุด)

void OnStart()
  {
   string name = "XAUUSD_M1_export.csv";
   int fh = FileOpen(name, FILE_WRITE | FILE_ANSI | FILE_COMMON);
   if(fh == INVALID_HANDLE)
     {
      PrintFormat("ExportM1: FileOpen FAILED err=%d", GetLastError());
      return;
     }

   MqlRates rates[];
   int total = 0;
   datetime from = InpFrom;
   // ดึงเป็น chunk กัน history ใหญ่เกิน / fetch in chunks
   while(from < InpTo)
     {
      datetime to = MathMin(from + 30 * 86400, InpTo);
      int n = CopyRates(_Symbol, PERIOD_M1, from, to, rates);
      if(n <= 0)
        {
         PrintFormat("ExportM1: CopyRates %s -> %s ได้ %d (err=%d) — ข้าม",
                     TimeToString(from), TimeToString(to), n, GetLastError());
         from = to;
         continue;
        }
      for(int i = 0; i < n; i++)
        {
         if(rates[i].time < from) continue;      // กัน overlap ระหว่าง chunk
         MqlDateTime dt;
         TimeToStruct(rates[i].time, dt);
         FileWriteString(fh, StringFormat("%04d.%02d.%02d\t%02d:%02d:00\t%.2f\t%.2f\t%.2f\t%.2f\t%d\t0\t%d\n",
                         dt.year, dt.mon, dt.day, dt.hour, dt.min,
                         rates[i].open, rates[i].high, rates[i].low, rates[i].close,
                         (int)rates[i].tick_volume, (int)rates[i].spread));
         total++;
        }
      from = rates[n - 1].time + 60;
     }
   FileClose(fh);
   PrintFormat("ExportM1: เขียน %d bars -> Common\\Files\\%s (%s ถึง bar ล่าสุด)", total, name,
               TimeToString(InpFrom, TIME_DATE));
   Alert(StringFormat("ExportM1 เสร็จ: %d bars", total));
  }
//+------------------------------------------------------------------+
