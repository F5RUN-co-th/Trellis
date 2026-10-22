#!/bin/bash
# B (วินสั่ง 2026-10-21): S1 958974d · preflight → regress → rg14 W=50 → kill-orphan sweep · หยุดเมื่อ exit ≠ 0 (ไม่ retry อัตโนมัติ)
cd /home/dev-ai/trellis-test || exit 2
PY=python/bin/python3.11; R=run_958974d; H=$R/repo/Scripts/host19_run.py
run() { "$PY" -I -B "$H" "$R" "$@"; }
echo "=== B start $(TZ=UTC date '+%F %T') UTC"
for m in preflight regress rg14; do
  echo "=== $m $(TZ=UTC date '+%F %T')"; run $m; rc=$?; echo "$m exit=$rc"
  if [ $rc -ne 0 ]; then echo "=== STOP: $m exit=$rc"; break; fi
done
echo "=== kill-orphan sweep"; run kill-orphan; echo "sweep exit=$?"
echo "=== end lines"; for f in $R/run/*.log; do echo "$(basename $f): $(tail -n1 $f)"; done
echo "=== gates"; ls $R/run/gate.*.rec 2>/dev/null || echo none
echo "=== stray"; pgrep -u dev-ai -af "trellis-test" | grep -v b_958974d || echo none
echo "=== B end $(TZ=UTC date '+%F %T') UTC"
