//+------------------------------------------------------------------+
//|  VerifyBTClock.mq5 — ตรวจ clock+เนื้อหาของ XAUUSD_BT ที่เก็บใน    |
//|  terminal จริงหลัง re-import (TRELLIS-010 Stage 0 — READ-ONLY)    |
//|                                                                  |
//|  วิธีใช้: ลาก script ใส่ chart ไหนก็ได้ → อ่านผลใน Experts log     |
//|  ทุกเช็คพิมพ์ PASS/FAIL — ต้อง PASS ครบทุกข้อก่อนรัน v4f          |
//+------------------------------------------------------------------+
#property copyright "Trellis"
#property version   "1.03"   // v1.03: definitive date-range probe + SERIES_SYNCHRONIZED (Engineer ขั้น A) + warmup probe ธ.ค.2024 + แก้ label TERMINAL_FIRSTDATE
#property strict

const string SYM = "XAUUSD_BT";
int g_pass = 0, g_fail = 0;

void Check(bool ok, string what)
  {
   if(ok) { g_pass++; Print("  [PASS] ", what); }
   else   { g_fail++; Print("  [FAIL] ", what); }
  }

// นับ/ดู tick แรกในหน้าต่างเวลา / first tick in window (small windows only)
bool FirstTickIn(datetime from, datetime to, MqlTick &out)
  {
   MqlTick arr[];
   int n = CopyTicksRange(SYM, arr, COPY_TICKS_ALL, (long)from * 1000, (long)to * 1000);
   if(n <= 0) return false;
   out = arr[0];
   return true;
  }

int CountTicksIn(datetime from, datetime to)
  {
   MqlTick arr[];
   return CopyTicksRange(SYM, arr, COPY_TICKS_ALL, (long)from * 1000, (long)to * 1000);
  }

// เทียบ bar OHLC ที่เวลา t กับค่าคาดหวัง (จากไฟล์ต้นทางที่ verify แล้ว)
void CheckBar(datetime t, double o, double h, double l, double c, string tag)
  {
   MqlRates r[];
   int n = CopyRates(SYM, PERIOD_M1, t, 1, r);
   if(n != 1 || r[0].time != t)
     {
      Check(false, tag + ": bar " + TimeToString(t, TIME_DATE | TIME_MINUTES) + " ไม่พบใน terminal");
      return;
     }
   bool ok = MathAbs(r[0].open - o) < 1e-6 && MathAbs(r[0].high - h) < 1e-6 &&
             MathAbs(r[0].low - l) < 1e-6 && MathAbs(r[0].close - c) < 1e-6;
   Check(ok, StringFormat("%s: bar %s OHLC stored=%.2f/%.2f/%.2f/%.2f expect=%.2f/%.2f/%.2f/%.2f",
                          tag, TimeToString(t, TIME_DATE | TIME_MINUTES),
                          r[0].open, r[0].high, r[0].low, r[0].close, o, h, l, c));
  }

// DEFINITIVE probe (Engineer ขั้น A): ขอ bars ทั้งช่วงแบบ date-range (ไม่ใช่ bar เดียว)
// + รอ SERIES_SYNCHRONIZED — แยกเคส "ยังไม่โหลด" (รอ) กับ "ไม่มีจริง" (synced แต่ว่าง) ได้ขาด
int ProbeRangeBars(datetime from, datetime to, string tag, MqlRates &r[])
  {
   int n = -1, err = 0;
   bool synced = false;
   for(int attempt = 0; attempt < 40; attempt++)
     {
      ResetLastError();
      n = CopyRates(SYM, PERIOD_M1, from, to, r);
      err = GetLastError();
      synced = (bool)SeriesInfoInteger(SYM, PERIOD_M1, SERIES_SYNCHRONIZED);
      if(n > 0) break;
      if(n == 0 && synced) break;   // synced แล้วแต่ว่าง = ไม่มีข้อมูลจริงในช่วงนี้
      Sleep(500);
     }
   Print(StringFormat("  [PROBE] %s: n=%d synced=%s err=%d%s", tag, n,
                      synced ? "true" : "false", err,
                      n > 0 ? StringFormat(" · first=%s last=%s",
                              TimeToString(r[0].time, TIME_DATE | TIME_MINUTES),
                              TimeToString(r[n - 1].time, TIME_DATE | TIME_MINUTES)) : ""));
   return n;
  }

// หา bar เวลา t ใน array ที่ probe มาแล้ว เทียบ open
void CheckBarOpenInArray(MqlRates &r[], int n, datetime t, double o, string tag)
  {
   for(int i = 0; i < n; i++)
      if(r[i].time == t)
        {
         Check(MathAbs(r[i].open - o) < 1e-6,
               StringFormat("%s: open stored=%.2f expect=%.2f", tag, r[i].open, o));
         return;
        }
   Check(false, tag + ": ไม่พบ bar " + TimeToString(t, TIME_DATE | TIME_MINUTES) + " ใน range ที่ probe ได้");
  }

void OnStart()
  {
   Print("=== VerifyBTClock (READ-ONLY) — XAUUSD_BT after re-import ===");
   SymbolSelect(SYM, true);

   // 1) จุดเริ่มปี: tick แรกของ 2025 ต้องอยู่ 01:00 (BT-clock) — ตำแหน่ง UTC เก่า (23:00 คืนก่อน) ต้องว่าง
   MqlTick tk;
   bool got = FirstTickIn(D'2025.01.01 20:00', D'2025.01.02 02:00', tk);
   Check(got && tk.time == D'2025.01.02 01:00:00',
         "2025 first tick = " + (got ? TimeToString(tk.time, TIME_DATE | TIME_SECONDS) : "NONE") + " (expect 2025.01.02 01:00:00)");
   Check(CountTicksIn(D'2025.01.01 20:00', D'2025.01.02 00:59') <= 0,
         "2025.01.01 20:00-2025.01.02 00:59 ว่าง (ตำแหน่ง UTC เก่าต้องไม่มี tick)");

   got = FirstTickIn(D'2026.01.01 20:00', D'2026.01.02 02:00', tk);
   Check(got && tk.time == D'2026.01.02 01:00:00',
         "2026 first tick = " + (got ? TimeToString(tk.time, TIME_DATE | TIME_SECONDS) : "NONE") + " (expect 2026.01.02 01:00:00)");

   // 2) จุดจบ 2025: tick สุดท้ายต้อง ~23:58:59 ของ 31 ธ.ค. (ตำแหน่ง UTC เก่า = 21:58)
   MqlTick arr[];
   int n = CopyTicksRange(SYM, arr, COPY_TICKS_ALL, (long)D'2025.12.31 20:00' * 1000, (long)D'2026.01.01 06:00' * 1000);
   bool endok = (n > 0 && arr[n - 1].time >= D'2025.12.31 23:58:00' && arr[n - 1].time < D'2026.01.01 00:00:00');
   Check(endok, "2025 last tick = " + (n > 0 ? TimeToString(arr[n - 1].time, TIME_DATE | TIME_SECONDS) : "NONE") + " (expect 23:58:xx)");

   // 3) Bar OHLC ตรงไฟล์ต้นทาง (ค่าจาก stage0_verify_import.py — ครอบหนาว/shoulder/ร้อน)
   CheckBar(D'2025.03.17 00:00', 2984.28, 2984.64, 2983.05, 2984.16, "shoulder-Mar (จุด price-match EU proof)");
   CheckBar(D'2025.07.08 12:00', 3323.45, 3324.35, 3322.68, 3324.18, "summer");
   CheckBar(D'2025.12.15 20:00', 4304.24, 4305.07, 4303.61, 4304.98, "winter-Dec");
   CheckBar(D'2026.02.20 15:00', 5024.95, 5025.82, 5024.60, 5024.69, "2026-Feb");

   // 4) DEFINITIVE: bars 2023 ทั้งปีอยู่ไหม (date-range + SERIES_SYNCHRONIZED — Engineer ขั้น A)
   //    บริบท: doc ยืนยัน "ticks with no minute bar are ignored" ใน tester → คำถามนี้ชี้ขาด
   //    (หลักฐานแวดล้อม: v4b_2324 เทรด 2023-24 ได้ 340 ไม้เมื่อเช้า = bars เคย serve ได้วันนี้)
   MqlRates pr[];
   int n23b = ProbeRangeBars(D'2023.01.01', D'2023.12.31 23:59', "bars 2023 ทั้งปี", pr);
   Check(n23b > 100000, StringFormat("bars 2023 ทั้งปี: %d bars (คาด ~340,000+)", n23b));
   // expect จาก MQL5\Files\XAUUSD_M1_2023.csv (แหล่ง import จริงของ terminal — ตรง tick file ด้วย)
   // หมายเหตุ: ฉบับ Gloo/Data ต่าง 1 tick (1984.10) — ความต่าง 2 ฉบับถูกวัดรวมใน drift 2023 แล้ว
   if(n23b > 0)
      CheckBarOpenInArray(pr, n23b, D'2023.03.20 00:00', 1984.15,
                          "2023 shoulder bar 03.20 00:00");

   // 4b) WARMUP ของ v4f_25: ธ.ค. 2024 ต้องมี bars (EMA2880+slope1440 ~4320 bars ก่อน 2025.01.01)
   //     ไม่มี = tester เลื่อน start อัตโนมัติ (doc: "starting date will be automatically shifted")
   MqlRates pw[];
   int nwarm = ProbeRangeBars(D'2024.12.01', D'2024.12.31 23:59', "bars ธ.ค. 2024 (warmup v4f_25)", pw);
   Check(nwarm > 20000, StringFormat("warmup ธ.ค. 2024: %d bars (คาด ~28,000)", nwarm));

   // 5) ticks ปีเก่ายังอ่านได้ (สถานะ tick database — คนละฐานกับ bars)
   int n22 = CountTicksIn(D'2022.03.15 10:00', D'2022.03.15 10:10');
   int n23 = CountTicksIn(D'2023.03.20 10:00', D'2023.03.20 10:10');
   int n24 = CountTicksIn(D'2024.06.10 10:00', D'2024.06.10 10:10');
   Check(n22 > 0, StringFormat("ticks 2022 ยังอยู่ (2022.03.15 10:00-10:10 พบ %d ticks)", n22));
   Check(n23 > 0, StringFormat("ticks 2023 ยังอยู่ (2023.03.20 10:00-10:10 พบ %d ticks)", n23));
   Check(n24 > 0, StringFormat("ticks 2024 ยังอยู่ (2024.06.10 10:00-10:10 พบ %d ticks)", n24));

   // 6) ช่วง series ปัจจุบัน + ขอบเขตข้อมูลใน terminal
   datetime fd  = (datetime)SeriesInfoInteger(SYM, PERIOD_M1, SERIES_FIRSTDATE);
   datetime ld  = (datetime)SeriesInfoInteger(SYM, PERIOD_M1, SERIES_LASTBAR_DATE);
   datetime tfd = (datetime)SeriesInfoInteger(SYM, PERIOD_M1, SERIES_TERMINAL_FIRSTDATE);
   long     bc  = SeriesInfoInteger(SYM, PERIOD_M1, SERIES_BARS_COUNT);
   Print("  [INFO] M1 series: bars_count=", bc, " · first=", TimeToString(fd, TIME_DATE),
         " -> last=", TimeToString(ld, TIME_DATE | TIME_MINUTES));
   Print("  [INFO] TERMINAL_FIRSTDATE=", TimeToString(tfd, TIME_DATE),
         " (จุดเริ่มข้อมูลทุกชนิดของ symbol ใน terminal — doc: regardless of timeframe)");

   if(g_fail == 0)
      Print("=== ผล: PASS=", g_pass, " FAIL=0 — พร้อมรัน v4f ===");
   else
      Print("=== ผล: PASS=", g_pass, " FAIL=", g_fail, " — ห้ามรัน v4f จนกว่าจะเคลียร์ ===");
  }
//+------------------------------------------------------------------+
