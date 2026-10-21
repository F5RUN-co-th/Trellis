#!/bin/bash
# host19_run.sh — ทางเข้าเดียวของ preflight/regress/RG14 บน 172.31.1.19 (วินสั่ง 2026-10-20 · ตาราง state = Progress Log 2026-10-20)
# usage: bash host19_run.sh <run_dir> <mode> [reason]
#   mode: preflight | regress | rg14 | abort "<reason>" | t-sleep | t-137 | t-escape   (t-* = smoke ของ run.sh เอง)
# exit: rc ของ python · 75 lock ไม่ว่าง · 76 start gate · 77 state/env/process-group assert
# แยกจาก erfx: ทุกอย่างอยู่ใต้ /home/dev-ai/trellis-test · env -i · choom 1000 · nice 19 · ระบุ process ด้วย TRELLIS_RUN_ID (ไม่ใช้ ps -g / pgrep -f)
set -euo pipefail
[[ $- != *m* ]] || { echo "[run] job control เปิดอยู่ — ห้าม"; exit 77; }
ROOT=/home/dev-ai/trellis-test
PY=$ROOT/python/bin/python3.11
RUNDIR=$(realpath "$1"); MODE=$2; REASON=${3:-}
case "$RUNDIR/" in "$ROOT"/*/) ;; *) echo "[run] RUNDIR นอก $ROOT"; exit 77 ;; esac
REPO=$RUNDIR/repo; LOGD=$RUNDIR/run; mkdir -p "$LOGD"
NPYOFF="AVX512F AVX512CD AVX512_SKX AVX512_CLX AVX512_CNL AVX512_ICL AVX512_SPR"
ts() { TZ=UTC date '+%Y-%m-%d %H:%M:%S'; }
oomk() { awk '/^oom_kill /{print $2}' /proc/vmstat; }

procs_with_id() {   # pid ของทุก process (uid เดียวกัน) ที่ environ มี TRELLIS_RUN_ID=$1 · อ่านอย่างเดียว
  local d
  for d in /proc/[0-9]*; do
    [[ -r $d/environ ]] || continue
    if { tr '\0' '\n' < "$d/environ"; } 2>/dev/null | grep -qx "TRELLIS_RUN_ID=$1"; then echo "${d#/proc/}"; fi
  done
}
pgid_of() { awk '{print $5}' "/proc/$1/stat" 2>/dev/null || true; }   # process จบแล้ว = ค่าว่าง (ห้าม fail ใต้ set -e)

kill_all() {   # $1 run_id · TERM ทุก pgid ที่พบ → รอ ≤10s → KILL → สแกนซ้ำต้องว่าง
  local id=$1 p g pg i left
  for sig in TERM KILL; do
    pg=$( { for p in $(procs_with_id "$id"); do pgid_of "$p"; done; } | sort -u )
    for g in $pg; do kill -"$sig" -- "-$g" 2>/dev/null || true; done
    for i in $(seq 1 10); do [[ -z "$(procs_with_id "$id")" ]] && return 0; sleep 1; done
  done
  left=$(procs_with_id "$id" | tr '\n' ' ')
  [[ -z "$left" ]] || { echo "[run] kill_all: ยังเหลือ $left"; return 1; }
}

if [[ $MODE == abort ]]; then
  [[ -n $REASON ]] || { echo "[run] abort ต้องมีเหตุผล"; exit 77; }
  last=$(ls -t "$LOGD"/*.log 2>/dev/null | head -n1 || true)
  [[ -n $last ]] || { echo "[run] ไม่มี log"; exit 77; }
  id=$(sed -n '1s/.* run_id=\([^ ]*\).*/\1/p' "$last")
  echo "[OPERATOR-ABORT] $REASON ts=$(ts)" >> "$last"
  kill_all "$id"; echo "[run] abort ok ($last)"; exit 0
fi

cd "$REPO"
exec 9>"$LOGD/lock"; flock -n 9 || { echo "[run] lock ไม่ว่าง"; exit 75; }
avail=$(awk '/^MemAvailable/{print int($2/1024)}' /proc/meminfo); load1=$(cut -d' ' -f1 /proc/loadavg)
awk -v a="$avail" -v l="$load1" 'BEGIN{exit !(a>=8192 && l<14)}' || { echo "[run] start gate ไม่ผ่าน MemAvailable_MB=$avail load1=$load1"; exit 76; }

case $MODE in
  preflight) CMD=(Scripts/host19_preflight.py check --ref Scripts/host19_ref/preflight_ref.json --manifest "$RUNDIR/manifest.json") ;;
  regress)   [[ ! -e Scripts/ad4_cert_out_v2 ]] || { echo "[run] state: มี ad4_cert_out_v2 ก่อน regress"; exit 77; }
             CMD=(-W error::RuntimeWarning Scripts/ad4_card.py regress --skip-rg14) ;;
  rg14)      grep -q '"regress": true' Scripts/ad4_cert_out_v2/regress_receipt.json 2>/dev/null || { echo "[run] state: ไม่มี receipt regress=true"; exit 77; }
             CMD=(Scripts/ad4_card.py rg14) ;;
  t-sleep)   CMD=(-c "import time; time.sleep(600)") ;;
  t-137)     CMD=(-c "import os, signal; os.kill(os.getpid(), signal.SIGKILL)") ;;
  t-escape)  CMD=(-c "import subprocess, time; subprocess.Popen(['setsid', '-f', 'sleep', '300']); time.sleep(600)") ;;
  *) echo "[run] mode ไม่รู้จัก: $MODE"; exit 77 ;;
esac

att=1; while [[ -e "$LOGD/$MODE.$att.log" ]]; do att=$((att + 1)); done
if [[ $MODE == rg14 && $att == 1 && -e Scripts/ad4_cert_out_v2/rg14/checkpoint_v6.json ]]; then echo "[run] state: มี checkpoint ก่อน rg14 ครั้งแรก"; exit 77; fi
LOG=$LOGD/$MODE.$att.log; RUN_ID=$(cat /proc/sys/kernel/random/uuid); oom0=$(oomk)
ENV=(env -i PATH=/usr/bin:/bin HOME=$ROOT LANG=C.UTF-8 TZ=UTC OPENBLAS_VERBOSE=2 OPENBLAS_CORETYPE=Haswell
     "NPY_DISABLE_CPU_FEATURES=$NPYOFF" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
     GIT_CEILING_DIRECTORIES=$ROOT TRELLIS_RUN_ID=$RUN_ID)
echo "[run] start mode=$MODE att=$att ts=$(ts) run_id=$RUN_ID oom_kill=$oom0" > "$LOG"
vrc=0; vj=$("${ENV[@]}" "$PY" -I -B Scripts/host19_preflight.py venue --strict 2>>"$LOG") || vrc=$?
if [[ $vrc != 0 ]]; then echo "[run] venue FAIL rc=$vrc $vj" >> "$LOG"; echo "[run] end rc=77 oom_kill=$(oomk)" >> "$LOG"; exit 77; fi
echo "[venue] $vj" >> "$LOG"

hb=""; trap '[[ -n $hb ]] && kill "$hb" 2>/dev/null || true' EXIT
setsid -w choom -n 1000 -- nice -n 19 /usr/bin/time -v "${ENV[@]}" "$PY" -u -I -B "${CMD[@]}" >>"$LOG" 2>&1 9>&- &
pid=$!; echo "$pid" > "$LOGD/$MODE.$att.pid"

# invariant (N1): ทุก process ที่มี RUN_ID ต้องอยู่ใน pgid == $pid และ $pid ≠ pgid ของ run.sh
self_pg=$(pgid_of $$); viol=""
for i in $(seq 1 50); do
  ids=$(procs_with_id "$RUN_ID")
  [[ -n $ids ]] && break; kill -0 "$pid" 2>/dev/null || break; sleep 0.1
done
sleep 1
if kill -0 "$pid" 2>/dev/null; then   # ถ้า process จบไปแล้ว ไม่มีอะไรให้ตรวจ group · การสแกน RUN_ID หลังจบยังจับ process ที่หลุดได้
  [[ $(pgid_of "$pid") == "$pid" && "$pid" != "$self_pg" ]] || viol="pid $pid pgid=$(pgid_of "$pid") self=$self_pg"
  for p in $(procs_with_id "$RUN_ID"); do g=$(pgid_of "$p"); [[ -z $g || $g == "$pid" ]] || viol="$viol · $p pgid=$g"; done
fi
if [[ -n $viol ]]; then
  echo "[run] process-group invariant FAIL: $viol" >> "$LOG"; kill_all "$RUN_ID" >> "$LOG" 2>&1 || true
  wait "$pid" 2>/dev/null || true; echo "[run] end rc=77 oom_kill=$(oomk)" >> "$LOG"; exit 77
fi

( exec 9>&-; set +e; sp=""
  trap '[[ -n $sp ]] && kill "$sp" 2>/dev/null; exit 0' TERM   # ไม่ทิ้ง sleep ของ heartbeat ค้าง
  while kill -0 "$pid" 2>/dev/null; do
    for p in $(procs_with_id "$RUN_ID"); do
      g=$(pgid_of "$p"); [[ -z $g || $g == "$pid" ]] || { echo "[hb] ESCAPE $p pgid=$g → kill_all"; kill_all "$RUN_ID"; }
    done
    py=$(for p in $(procs_with_id "$RUN_ID"); do [[ $(cat /proc/$p/comm 2>/dev/null) == python3.11 ]] && echo $p; done | head -n1)
    rss=$(awk '/^VmRSS/{print $2}' /proc/$py/status 2>/dev/null); hwm=$(awk '/^VmHWM/{print $2}' /proc/$py/status 2>/dev/null)
    echo "[hb] ts=$(ts) rss_kb=${rss:-?} hwm_kb=${hwm:-?} memavail_mb=$(awk '/^MemAvailable/{print int($2/1024)}' /proc/meminfo) load1=$(cut -d' ' -f1 /proc/loadavg) psi_mem=\"$(head -n1 /proc/pressure/memory 2>/dev/null)\""
    sleep 60 & sp=$!; wait "$sp"; sp=""
  done ) >> "$LOG" 2>&1 &
hb=$!

rc=0; wait "$pid" || rc=$?
kill "$hb" 2>/dev/null || true; hb=""
left=$(procs_with_id "$RUN_ID" | tr '\n' ' ')
if [[ -n $left ]]; then echo "[run] เหลือ process หลังจบ: $left → kill_all" >> "$LOG"; kill_all "$RUN_ID" >> "$LOG" 2>&1 || true; [[ $rc == 0 ]] && rc=77; fi
echo "[run] end rc=$rc oom_kill=$(oomk)" >> "$LOG"
exit "$rc"
