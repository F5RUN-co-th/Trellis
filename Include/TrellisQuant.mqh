//+------------------------------------------------------------------+
//|  TrellisQuant.mqh                                                 |
//|  Trellis EA — quant tools (regime detection)                     |
//|  อ้างอิง Plan/TRELLIS-004 §3.1                                    |
//+------------------------------------------------------------------+
#property strict

//--- Efficiency Ratio (Kaufman) — regime filter -------------------
//  ER = |net move| / Σ|step moves|  ·  ER→1 = trending, ER→0 = choppy/ranging
//  unbiased (ไม่มี regression/unit-root bias แบบ AR(1)) — เป็น TREND-REJECT filter
//  (RW ก็ ER ต่ำ → ผ่าน; กรองเฉพาะ trending ออก ซึ่งเป็นตัวที่ฆ่า grid)
//  p[] = closed bars เรียงเก่า→ใหม่
double EfficiencyRatio(const double &p[], int n)
  {
   if(n < 2) return 1.0;
   double net  = MathAbs(p[n - 1] - p[0]);
   double path = 0.0;
   for(int i = 1; i < n; i++)
      path += MathAbs(p[i] - p[i - 1]);
   if(path <= 0.0) return 1.0;          // flat → ไม่เทรด (return สูง = ไม่ผ่าน gate)
   return net / path;
  }
//+------------------------------------------------------------------+
