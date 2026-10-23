#!/bin/bash
# R-A (วินสั่ง 2026-10-22 · spec §13 D-5): S1 c81b4cf (runner r14) · preflight → regress → rg14 → pilot · หยุดเมื่อ exit ≠ 0 (ไม่ retry อัตโนมัติ)
# exit ของ driver = rc ของขั้นที่ล้ม (0 = ครบทุกขั้น) · ไม่มีบรรทัด stray-check แบบ pgrep (F8 ของ b_958974d.sh)
cd /home/dev-ai/trellis-test || exit 2
PY=python/bin/python3.11; R=run_c81b4cf; H=$R/repo/Scripts/host19_run.py
run() { "$PY" -I -B "$H" "$R" "$@"; }
echo "=== R-A start $(TZ=UTC date '+%F %T') UTC"
final=0
for m in preflight regress rg14 pilot; do
  echo "=== $m $(TZ=UTC date '+%F %T')"; run $m; rc=$?; echo "$m exit=$rc"
  if [ $rc -ne 0 ]; then echo "=== STOP: $m exit=$rc"; final=$rc; break; fi
done
echo "=== kill-orphan sweep"; run kill-orphan; echo "sweep exit=$?"
echo "=== end lines"; for f in $R/run/*.log; do echo "$(basename $f): $(tail -n1 $f)"; done
echo "=== gates"; ls $R/run/gate.*.rec 2>/dev/null || echo none
echo "=== R-A end $(TZ=UTC date '+%F %T') UTC · driver exit=$final"
exit $final
