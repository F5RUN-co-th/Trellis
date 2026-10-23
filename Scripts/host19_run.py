# -*- coding: utf-8 -*-
"""host19_run — ทางเข้าเดียวของ workload บน 172.31.1.19 (แทน host19_run.sh · spec = Plan/TRELLIS-010_host19_supervisor.md r13 + §13 (r14 · r15))

usage   PY -I -B Scripts/host19_run.py <rundir> <mode> [...]
  mode  preflight | regress | rg14            series B (front → supervisor แยก session → child chain)
        pilot                                  post-B: ad4_card.py pilot 0 30 (key ตายตัว c1full/h0pilot/-/0/30 · ไม่รับ args)
        cert_v2 <variant> <world> [cell] <k0> <k1>   post-B: 1 chunk ต่อการเรียก (certify v2 = serial · spec §13 D-1)
        abort "<reason>"                       ขอ abort run ที่กำลังรันใน RUNDIR นี้
        kill-orphan                            กู้ orphan/stale (ต้องไม่มี supervisor ที่ยัง alive)
        t-<name>                               smoke ของ supervisor เอง (เฉพาะ RUNDIR run_smoke*)
exit    = กฎ G-1 (host19_state.exit_code): rc จริงของ child ถ้า cause=child-exit ∧ viol ว่าง · อื่น 77 · gate 75 lock ไม่ว่าง / 76 ทรัพยากร / 77
ป้ายราย attempt ที่พิมพ์ = ใช้ตัดสินไปต่อ/หยุด/รันซ้ำเท่านั้น (ตาราง (2)–(6),(8)) · verdict ของ series = host19_accept.py บน .19 (CLAUDE.md §สนามรัน)
"""
import os, sys, signal, time, json, io, uuid, traceback, threading, glob, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                                                    # -I ตัด script dir ออกจาก sys.path
import host19_state as S

SELF = os.path.abspath(__file__)
STOP_SIGS = tuple(signal.Signals[n] for n in S.STOP_SIGNALS)             # r15: แหล่งเดียว = host19_state.STOP_SIGNALS (CUT_RC สร้างจากชุดเดียวกัน)
assert all(int(signal.Signals[n]) == v for n, v in S.STOP_SIGNALS.items()) and int(signal.SIGKILL) == S.SIGKILL_NUM, "เลข signal ≠ Linux ABI ของ record"
SIGS = STOP_SIGS + (signal.SIGCHLD, signal.SIGTSTP)
TICK = 0.2
def _cert_argv(key):
    v, w, c, k0, k1 = S.parse_key(key)
    return ["Scripts/ad4_card.py", "cert_v2", v, w] + ([] if c is None else [str(c)]) + [str(k0), str(k1)]


CMDS = {                                                                    # (rundir, key) → argv ของ child หลัก · key = None นอก POST_MODES
    "preflight": lambda rd, key: ["Scripts/host19_preflight.py", "check", "--ref", "Scripts/host19_ref/preflight_ref.json",
                                  "--manifest", os.path.join(rd, "manifest.json")],
    "regress": lambda rd, key: ["-W", "error::RuntimeWarning", "Scripts/ad4_card.py", "regress", "--skip-rg14"],
    "rg14": lambda rd, key: ["Scripts/ad4_card.py", "rg14"],
    "pilot": lambda rd, key: ["Scripts/ad4_card.py", "pilot", "0", "30"],     # = S.PILOT_KEY (card :88)
    "cert_v2": lambda rd, key: _cert_argv(key),
}
T_CMDS = {                                                                  # smoke ของ supervisor (§11) · python -c ใน child chain จริง
    "t-sleep": "import time; time.sleep(600)",
    "t-exit0": "print('t-exit0')",
    "t-raise": "raise AssertionError('t-raise')",
    "t-137": "import os, signal; os.kill(os.getpid(), signal.SIGKILL)",
    "t-pause": "import signal; signal.pause()",
    "t-ignterm": "import signal, time; time.sleep(5); signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(600)",   # ignore หลัง leaf check ผ่าน (KILLFAIL smoke)
    "t-escape": "import subprocess, time; subprocess.Popen(['setsid', '-f', 'sleep', '300']); time.sleep(600)",
    "t-bg": "import subprocess; subprocess.Popen(['sh', '-c', 'sleep 300 &']); print('t-bg')",
    "t-envclr": "import subprocess, time; subprocess.Popen(['setsid', '-f', 'env', '-i', 'sleep', '300']); time.sleep(600)",
    "t-spawnfail": "print('ไม่ควรรัน')",                                          # argv[0] ถูกแทนด้วย SPAWNFAIL_BIN → Popen raise = spawn-fail จริง
}
SPAWNFAIL_BIN = "/nonexistent/trellis-spawnfail"
DEADLINE = {"rg14": (1800, 72 * 3600), "regress": (1800, 72 * 3600), "preflight": (600, 2 * 3600)}   # (cpu_stall s, wall_cap s) · POST_MODES = S.post_deadline(key)
T_DEADLINE = (20, 600)
VENUE_WALL = 120
LEAF_WAIT = 60


def ts(): return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


class Gate(Exception):
    """ทางออกก่อน spawn child หลัก → gate record"""
    def __init__(self, rc, cause, reason, **extra):
        super().__init__(reason); self.rc, self.cause, self.reason, self.extra = rc, cause, reason, extra


# ====================================================================================== supervisor
class Supervisor:
    def __init__(self, rundir, mode, ns0, key=None):
        self.rundir, self.mode, self.ns0 = rundir, mode, ns0
        self.key = S.PILOT_KEY if mode == "pilot" else key                  # key ของ post-B (None นอก POST_MODES)
        if (self.key is not None) != (mode in S.POST_MODES): raise ValueError(f"key/mode ไม่เข้ากัน: {mode} {key}")
        if self.key is not None: S.parse_key(self.key)
        self.repo = os.path.join(rundir, "repo")
        self.pid = os.getpid()
        self.cause, self.viol, self.note, self.left = None, set(), [], []
        self.tb = []                                                        # traceback buffer → LOG หลัง kill_all
        self.registry = []                                                  # Popen ที่ยังไม่ reap
        self.seq = self.seq_seen = None
        self.run_id = None
        self.current_written = False
        self.log_path = None
        self.bt = None
        self.child = None; self.spawned = False
        self.abort_reason = None; self.sig = None
        self.lock_fd = None
        self.oom0 = None

    # ---------- helpers
    def err(self, msg):
        try:
            with open(S.run_path(self.rundir, f"super.{self.ns0}.err"), "a", encoding="utf-8") as f: f.write(msg.rstrip("\n") + "\n")
        except OSError:
            pass

    def set_cause(self, c):
        if self.cause is None: self.cause = c

    def hb(self, msg):
        """ข้อความระหว่างรัน → <mode>.<att>.hb · ก่อนมี LOG (เส้น gate) → super.<ns0>.err"""
        if not self.log_path: return self.err(msg)
        try:
            with open(self.log_path[:-4] + ".hb", "a", encoding="utf-8") as f: f.write(msg + "\n")
        except OSError:
            pass

    def my_st(self): return S.read_stat(self.pid)["starttime"]

    def test_flag(self, k): return self.mode.startswith("t-") and os.environ.get(k) == "1"

    # ---------- gate / current
    def write_gate(self, rc, cause, reason, **extra):
        assert cause in S.CAUSE_GATE, cause
        tag = f"{self.seq:08d}" if self.seq is not None else f"seen{(self.seq_seen or 0):08d}"
        rec = {"mode": self.mode, "rc": rc, "cause": cause, "viol": sorted(self.viol), "reason": reason, "seq": self.seq,
               "seq_seen": self.seq_seen, "ns0": self.ns0, "pid": self.pid, "run_id": self.run_id, "left": self.left,
               "boottime_ns": time.clock_gettime_ns(time.CLOCK_BOOTTIME), "ts": ts()}
        try: rec["boot_id"] = S.boot_id()
        except OSError: rec["boot_id"] = None
        rec.update(extra)
        S.write_json_atomic(S.run_path(self.rundir, f"gate.{tag}.{self.ns0}.{rc}.rec"), rec)
        return rec

    def write_current(self, state, **extra):
        cur = {"run_id": self.run_id, "state": state, "sup_pid": self.pid, "sup_starttime": self.my_st(), "boot_id": S.boot_id(),
               "seq": self.seq, "ns0": self.ns0, "mode": self.mode}
        cur.update(extra)
        S.write_json_atomic(S.run_path(self.rundir, "current"), cur)
        self.current_written = True

    # ---------- process control
    def reap_orphans(self):
        regs = {p.pid for p in self.registry}
        for st in S.all_stats().values():
            if st["ppid"] == self.pid and st["state"] == "Z" and st["pid"] not in regs:
                try:
                    os.waitpid(st["pid"], os.WNOHANG); self.hb(f"[run] reaped-orphan pid={st['pid']} comm={st['comm']}")
                except ChildProcessError:
                    pass

    def poll_all(self, reap=True):
        for p in list(self.registry):
            if p.poll() is not None: self.registry.remove(p)
        if reap: self.reap_orphans()

    def kill_all(self):
        """descendants (pid, starttime) · S.kill_targets(group=True: killpg เมื่อเป็น leader ของ pgid ตัวเอง) · เหลือ → killfail + left"""
        try:
            targets = {(s["pid"], s["starttime"]): s for s in S.descendants(self.pid)}
            if not targets: return True
            live = S.kill_targets(targets, group=True, poll_cb=self.poll_all, skip_kill=self.test_flag("TRELLIS_TEST_KILLFAIL"), tick=TICK)
            if not live: return True
            self.viol.add("killfail"); self.left = sorted(live)
            self.hb(f"[run] kill_all FAIL left={','.join(f'{p}:{st}' for p, st in sorted(live))}")
            return False
        except BaseException:
            self.viol.update(("killfail", "internal")); self.tb.append(traceback.format_exc()); self.err(traceback.format_exc())
            try: self.left = sorted((s["pid"], s["starttime"]) for s in S.descendants(self.pid))
            except BaseException: pass
            return False
        finally:
            self.poll_all()

    def spawn(self, argv, env, out_fd):
        def reset():
            for s in SIGS + (signal.SIGPIPE,): signal.signal(s, signal.SIG_DFL)
            signal.pthread_sigmask(signal.SIG_UNBLOCK, SIGS)
        p = subprocess.Popen(argv, cwd=self.repo, env=env, start_new_session=True, stdin=subprocess.DEVNULL, stdout=out_fd,
                             stderr=subprocess.STDOUT, close_fds=True, preexec_fn=reset)
        self.registry.append(p)
        return p

    # ---------- wait loop (primitive เดียว · venue และ child หลัก)
    def wait_child(self, child, cpu_stall, wall_cap, main):
        """→ เหตุที่จบ: exit | signal | abort | deadline-stall | deadline-wall | leaf-missing | viol-teardown"""
        t0 = time.monotonic(); t_abort = t_esc = t_hb = t_reap = 0.0
        leaf = None; leaf_done = not main; cpu_last = None; cpu_t = t0; chld = False
        while True:
            if child.poll() is not None:                                    # poll ก่อน dispatch ทุก tick (F4)
                self.poll_all()
                if main and not leaf_done: self.note.append("no-leaf-check")
                return "exit"
            now = time.monotonic()
            self.poll_all(reap=chld or now - t_reap >= 2)                   # reaper: เมื่อได้ SIGCHLD หรือทุก 2 s (orphan ที่ตายส่ง CHLD ถึง subreaper)
            if chld or now - t_reap >= 2: t_reap = now; chld = False
            info = signal.sigtimedwait(SIGS, TICK)
            if info is not None and info.si_signo == signal.SIGCHLD: chld = True; continue
            if info is not None:
                if child.poll() is not None:                                # child จบไปแล้ว: signal = note ไม่เปลี่ยน cause
                    if info.si_signo in STOP_SIGS: self.note.append(f"sig{info.si_signo}-after-exit"); self.sig = info.si_signo
                    continue
                if info.si_signo in STOP_SIGS:
                    self.sig = info.si_signo; return "signal"
                if info.si_signo == signal.SIGTSTP: self.hb(f"[hb] ts={ts()} SIGTSTP ignored")
                continue
            # ทุกการตัดสินด้านล่าง commit เฉพาะเมื่อ poll ณ จุดนั้นยังเห็น child alive (child จบเองระหว่างทาง → วนกลับไปคืน "exit")
            if now - t_abort >= 2:
                t_abort = now
                if child.poll() is None and self.take_abort(): return "abort"
            if main and not leaf_done:
                r = self.leaf_check(child)
                if r == "ok": leaf_done = True
                elif child.poll() is not None: continue
                elif r == "bad": self.viol.add("escape"); return "viol-teardown"
                elif now - t0 >= LEAF_WAIT: return "leaf-missing"
            if now - t_esc >= 30:
                t_esc = now
                esc = [s for s in S.descendants(self.pid) if s["pgid"] != child.pid]
                if esc and child.poll() is None:
                    self.viol.add("escape"); self.hb(f"[run] ESCAPE {[(s['pid'], s['comm'], s['pgid']) for s in esc]}")
                    return "viol-teardown"
            if main and leaf_done and leaf is None: leaf = self.find_leaf(child)
            if main and leaf is not None:
                st = S.read_stat(leaf)
                if st:
                    cpu = st["utime"] + st["stime"]
                    if cpu != cpu_last: cpu_last, cpu_t = cpu, now
                    elif now - cpu_t >= cpu_stall and child.poll() is None: return "deadline-stall"
            if now - t0 >= wall_cap and child.poll() is None: return "deadline-wall"
            if main and now - t_hb >= 60:
                t_hb = now; self.heartbeat(leaf)

    def find_leaf(self, child):
        for s in S.descendants(child.pid):
            if s["comm"] == "python3.11" and (S.environ_trellis(s["pid"]) or {}).get("TRELLIS_RUN_ID") == self.run_id: return s["pid"]
        return None

    def leaf_check(self, child):
        """ok | bad | wait · pgid(child)==child.pid ∧ pgid(leaf)==child.pid ∧ SigBlk∩S=∅ ∧ SigIgn∩S=∅"""
        leaf = self.find_leaf(child)
        if leaf is None: return "wait"
        cs, ls, mk = S.read_stat(child.pid), S.read_stat(leaf), S.sig_masks(leaf)
        if not cs or not ls or not mk: return "wait"
        mask = S.mask_of(SIGS)
        ok = cs["pgid"] == child.pid and ls["pgid"] == child.pid and not (mk[0] & mask) and not (mk[1] & mask)
        if not ok: self.hb(f"[run] leaf assert FAIL pgid={cs['pgid']}/{ls['pgid']} blk={mk[0]:x} ign={mk[1]:x}")
        return "ok" if ok else "bad"

    def heartbeat(self, leaf):
        rss = hwm = "?"
        if leaf:
            try:
                for l in io.open(f"/proc/{leaf}/status"):
                    if l.startswith("VmRSS:"): rss = l.split()[1]
                    if l.startswith("VmHWM:"): hwm = l.split()[1]
            except OSError:
                pass
        avail, load1 = S.mem_load()
        try: psi = io.open("/proc/pressure/memory").readline().strip()
        except OSError: psi = ""
        self.hb(f"[hb] ts={ts()} rss_kb={rss} hwm_kb={hwm} memavail_mb={avail} load1={load1} psi_mem=\"{psi}\"")

    def take_abort(self, final=False):
        p = S.run_path(self.rundir, "abort.req")
        try:
            req = S.read_json(p)
        except FileNotFoundError:
            return False                                                    # ENOENT = ไม่มี req (ไม่ใช่ internal)
        except ValueError:
            os.replace(p, S.run_path(self.rundir, f"abort.bad.{time.time_ns()}")); return False
        ns = req.get("ns", time.time_ns())
        if final:
            os.replace(p, S.run_path(self.rundir, f"abort.{req.get('run_id')}.{ns}.ignored")); return False
        if req.get("run_id") == self.run_id:
            os.replace(p, S.run_path(self.rundir, f"abort.{self.run_id}.{ns}.taken"))
            self.abort_reason = req.get("reason", ""); return True
        os.replace(p, S.run_path(self.rundir, f"abort.stale.{ns}")); self.hb(f"[run] abort stale id={req.get('run_id')}")
        return False

    def drain(self):
        """ก่อน spawn child หลัก: signal ค้าง / abort.req ค้าง → gate"""
        while True:
            info = signal.sigtimedwait(SIGS, 0)
            if info is None: break
            if info.si_signo in STOP_SIGS: self.sig = info.si_signo; raise Gate(77, "signal", f"signal {info.si_signo} ก่อน spawn")
        if self.take_abort(): raise Gate(77, "abort", f"abort ก่อน spawn: {self.abort_reason}")

    # ---------- start
    def pre_lock(self):
        for s in SIGS: signal.signal(s, signal.SIG_DFL)
        blk, ign = S.sig_masks(self.pid); m = S.mask_of(SIGS)
        bad = [s for s in SIGS if signal.getsignal(s) != signal.SIG_DFL]
        if bad or ign & m or (blk & m) != m: raise Gate(77, "pre-lock-assert", f"signal state: dfl_bad={bad} ign={ign:x} blk={blk:x}")
        if "numpy" in sys.modules: raise Gate(77, "pre-lock-assert", "numpy ถูก import ใน supervisor")
        if threading.active_count() != 1: raise Gate(77, "pre-lock-assert", f"threads={threading.active_count()}")
        bad_env = S.test_env_violation(self.mode, os.environ)
        if bad_env: raise Gate(77, "pre-lock-assert", f"{bad_env} ใน mode {self.mode}")
        import ctypes
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0: raise Gate(77, "pre-lock-assert", f"PR_SET_CHILD_SUBREAPER errno={ctypes.get_errno()}")

    def read_seq(self):
        try: return int(io.open(os.path.join(S.ROOT, "seq")).read().strip())
        except FileNotFoundError: return 0

    def seq_missing_with_records(self):
        """ไม่มี $ROOT/seq ทั้งที่เคยมี run (record ใน run_*/run) = seq reset → ห้ามเริ่ม (ลำดับ attempt จะผิด)"""
        if os.path.exists(os.path.join(S.ROOT, "seq")): return []
        return glob.glob(os.path.join(S.ROOT, "run_*", "run", "*.log")) + glob.glob(os.path.join(S.ROOT, "run_*", "run", "gate.*.rec"))

    def take_lock(self):
        import fcntl
        fd = os.open(os.path.join(S.ROOT, "trellis.lock"), os.O_RDWR | os.O_CREAT, 0o644)   # PEP 446: non-inheritable
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd); raise Gate(75, "lock-busy", "global lock ไม่ว่าง")
        self.lock_fd = fd
        rec = self.seq_missing_with_records()
        if rec: raise Gate(77, "state", f"$ROOT/seq หายทั้งที่มี record {len(rec)} ไฟล์ (seq reset) · ห้ามเริ่ม · ตรวจ/คืน seq ด้วยมือ")
        self.seq = self.read_seq() + 1
        p = os.path.join(S.ROOT, "seq"); tmp = p + ".tmp"
        with open(tmp, "w") as f: f.write(f"{self.seq}\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, p)
        dfd = os.open(S.ROOT, os.O_RDONLY); os.fsync(dfd); os.close(dfd)
        self.bt = time.clock_gettime_ns(time.CLOCK_BOOTTIME)                 # ใต้ lock: supervisor ถัดไปวัดได้หลังเราปล่อย lock เท่านั้น

    def stale_check(self):
        p = S.run_path(self.rundir, "current")
        if not os.path.exists(p): return
        cur = S.read_json(p); rid = cur.get("run_id")
        if rid and not S.resolved(self.rundir, rid) and not S.alive(cur["sup_pid"], cur["sup_starttime"], cur["boot_id"]):
            raise Gate(77, "stale-run", f"run {rid} ไม่ resolved และ supervisor ตาย → kill-orphan ก่อน", target_run_ids=[rid])

    def gates(self):
        avail, load1 = S.mem_load()
        if not (avail >= 8192 and load1 < 14): raise Gate(76, "resources", f"MemAvailable_MB={avail} load1={load1}")
        cert = os.path.join(self.repo, "Scripts", "ad4_cert_out_v2")
        if self.mode == "regress" and os.path.exists(cert): raise Gate(77, "state", "มี ad4_cert_out_v2 ก่อน regress")
        if self.mode == "rg14":
            try: rec = S.read_json(os.path.join(cert, "regress_receipt.json"))
            except (FileNotFoundError, ValueError): rec = {}
            if rec.get("regress") is not True: raise Gate(77, "state", "ไม่มี receipt regress=true")
            if self.next_att() == 1 and os.path.exists(os.path.join(cert, "rg14", "checkpoint_v6.json")):
                raise Gate(77, "state", "มี checkpoint ก่อน rg14 ครั้งแรก")
        if self.mode in S.POST_MODES:                                       # G-4: closure/SPEC ตรวจที่ child (ad4_card.py require_receipt) · chunk ซ้ำ = child assert
            try: rec = S.read_json(os.path.join(cert, "regress_receipt.json"))
            except (FileNotFoundError, ValueError): rec = {}
            if rec.get("regress") is not True or rec.get("rg14") is not True: raise Gate(77, "state", "ไม่มี receipt regress=true ∧ rg14=true")
        if not self.mode.startswith("t-"):                                  # gate คู่ของ judge ที่เดียว (S.may_spawn: B หลัง post · ประวัติ key · pilot ก่อน cert · k ทับ)
            try:
                gs, os_ = S.read_gates(self.rundir), S.read_orphans(self.rundir)
                atts = S.read_attempts(self.rundir)
                for a in atts: a["cls"] = S.classify_attempt(a, self.rundir, gs, os_)[0]
            except (S.ToolError, ValueError, OSError) as e:
                raise Gate(77, "state", f"อ่าน record ของ RUNDIR ไม่ได้: {type(e).__name__}: {e}")
            ok, why = S.may_spawn(self.mode, self.key, atts)
            if not ok: raise Gate(77, "state", why)
        found, unread = S.trellis_env_procs(exclude=(self.pid,))
        ids = {e["TRELLIS_RUN_ID"] for _, e in found}
        if unread:
            self.note.append(f"environ-unreadable={len(unread)}"); self.err(f"[run] environ อ่านไม่ได้ (same uid): {unread}")
        if ids: raise Gate(77, "orphan-env", f"มี process ที่ถือ TRELLIS_RUN_ID {sorted(ids)} → kill-orphan", target_run_ids=sorted(ids))

    def next_att(self):
        att = 1
        while os.path.exists(S.run_path(self.rundir, f"{self.mode}.{att}.log")): att += 1
        return att

    # ---------- main
    def main(self):
        self.seq_seen = self.read_seq()
        self.pre_lock()
        self.take_lock()
        self.stale_check()
        self.gates()
        self.run_id = str(uuid.uuid4())
        self.write_current("running")
        bid, st = S.boot_id(), self.my_st()
        env = S.child_env(self.run_id, self.pid, st, bid, self.rundir)
        env.update(S.post_env(self.key))                                    # Y-1 contingency (venue + child หลักเห็นค่าเดียวกัน)
        for k in S.TEST_ENV:
            if self.test_flag(k): env[k] = "1"
        # venue
        vjson = S.run_path(self.rundir, f"venue.{self.run_id}.json"); vout = S.run_path(self.rundir, f"venue.{self.run_id}.out")
        vfd = os.open(vout, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            venue = self.spawn([S.PY, "-I", "-B", "Scripts/host19_preflight.py", "venue", "--strict", "--out", vjson]
                               + (["--key", self.key, "--post-mode", self.mode] if self.key else []), env, vfd)
        finally:
            os.close(vfd)
        why = self.wait_child(venue, VENUE_WALL, VENUE_WALL, main=False)
        if why != "exit":
            self.kill_all()
            cause = {"signal": "signal", "abort": "abort", "deadline-wall": "deadline-wall", "deadline-stall": "deadline-wall"}.get(why, "viol-teardown")
            raise Gate(77, cause, f"ระหว่าง venue: {why}", venue_out=vout)
        vj = None
        try:
            vj = S.read_json(vjson)
        except (FileNotFoundError, ValueError):
            pass
        if venue.returncode != 0 or not vj or vj.get("run_id") != self.run_id or vj.get("pid") != venue.pid:
            try: tail = next((l.strip() for l in reversed(io.open(vout, encoding="utf-8", errors="replace").read().splitlines()) if l.strip()), "")
            except OSError: tail = ""
            raise Gate(77, "venue-fail", f"venue rc={venue.returncode} · {tail[:300]}", venue_rc=venue.returncode, venue_out=vout)   # Z-3
        if S.descendants(self.pid):
            self.kill_all(); self.viol.add("leftover"); raise Gate(77, "venue-exit", "descendant ค้างหลัง venue")
        try: diff = S.fp_diff(vj, S.read_attempts(self.rundir))             # R15-6 (§13 r15): fingerprint เดียวต่อ RUNDIR · ทุก mode · ก่อน LOG (ไม่กินโควตารันซ้ำ)
        except (S.ToolError, ValueError, OSError) as e: raise Gate(77, "state", f"อ่าน LOG ของ RUNDIR ไม่ได้ (R15-6): {type(e).__name__}: {e}")
        if diff: raise Gate(77, "state", f"env fingerprint ต่างจาก attempt แรกของ RUNDIR: {','.join(diff)} (R15-6 · series นี้ต่อไม่ได้ = run dir ใหม่)")
        self.drain()
        # child หลัก: LOG ⟺ พยายาม spawn · LOG ปรากฏพร้อม start + [venue] ครบ (tmp → link) หรือไม่ปรากฏเลย
        att = self.next_att()
        cmd = ["-c", T_CMDS[self.mode]] if self.mode.startswith("t-") else CMDS[self.mode](self.rundir, self.key)
        argv = ["/usr/bin/choom", "-n", "1000", "--", "/usr/bin/nice", "-n", "19", "/usr/bin/time", "-v", S.PY, "-u", "-I", "-B"] + cmd
        if self.mode == "t-spawnfail": argv[0] = SPAWNFAIL_BIN
        final = S.run_path(self.rundir, f"{self.mode}.{att}.log"); tmp = f"{final}.{self.ns0}.tmp"   # tmp ชื่อไม่ซ้ำ: tmp ค้างไม่ล็อก att
        self.oom0 = S.oom_kill()
        vj.pop("run_id", None); vj.pop("pid", None)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o644)
        try:
            os.write(fd, (S.fmt_start(self.mode, att, ts(), self.run_id, self.oom0, self.seq, self.ns0, bid, self.pid, st, self.bt, self.key) + "\n"
                          + "[venue] " + json.dumps(vj, ensure_ascii=False) + "\n").encode())
            os.fsync(fd)
            os.link(tmp, final)                                             # EEXIST = ล้ม (เท่า O_EXCL)
            self.log_path = final                                           # ตั้งหลัง link สำเร็จเท่านั้น (ก่อนหน้านี้ = เส้น gate)
            os.unlink(tmp)
            dfd = os.open(S.run_path(self.rundir), os.O_RDONLY); os.fsync(dfd); os.close(dfd)
            try:
                self.child = self.spawn(argv, env, fd); self.spawned = True   # fd ของ tmp (O_APPEND · inode เดียวกับ LOG) → stdout ของ child
            except (OSError, subprocess.SubprocessError) as e:
                self.set_cause("spawn-fail"); self.note.append(f"spawn-{type(e).__name__}"); return
        finally:
            os.close(fd)                                                    # ผู้เขียน LOG ระหว่างรัน = child chain เท่านั้น
        self.write_current("running", log=os.path.basename(self.log_path), att=att)
        cpu_stall, wall = (T_DEADLINE if self.mode.startswith("t-") else S.post_deadline(self.key) if self.mode in S.POST_MODES
                           else DEADLINE[self.mode])
        why = self.wait_child(self.child, cpu_stall, wall, main=True)
        self.set_cause("child-exit" if why == "exit" else why)

    # ---------- finalizer
    def run(self):
        try:
            self.main()
        except Gate as g:
            self.set_cause(g.cause); self._gate = g
        except BaseException:
            tb = traceback.format_exc(); self.tb.append(tb); self.err(tb); self.viol.add("internal")
            if not (self.child is not None and self.child.poll() is not None): self.set_cause("internal-error")
        try:
            return self.finalize()
        except BaseException:
            try: self.err(traceback.format_exc())
            except BaseException: pass
            os._exit(77)

    def _step(self, fn):
        try:
            fn()
        except BaseException:
            tb = traceback.format_exc(); self.tb.append(tb); self.err(tb); self.viol.add("internal")

    def finalize(self):
        g = getattr(self, "_gate", None)
        if self.log_path is None:                                           # ทางออกก่อน spawn child หลัก = gate record
            self._step(lambda: [p for p in self.registry if p.poll() is None] and self.kill_all())
            self._step(lambda: self.take_abort(final=True) if self.run_id else None)
            if g is None: g = Gate(77, "internal-error", "exception ก่อน spawn")
            rc = g.rc if not ("killfail" in self.viol and g.rc != 77) else 77
            rec = self.write_gate(rc, g.cause, g.reason, **g.extra)
            if self.current_written: self.write_current("exited", rc=rc)
            return S.exit_code("gate", rec)

        def s1():
            if self.child is not None and self.child.poll() is None:
                self.set_cause("internal-error"); self.kill_all()

        def s2():
            if self.test_flag("TRELLIS_TEST_RAISE_AFTER_REAP"): raise RuntimeError("TRELLIS_TEST_RAISE_AFTER_REAP")
            left = S.descendants(self.pid)
            if left:
                self.viol.add("leftover"); self.hb(f"[run] leftover {[(s['pid'], s['comm']) for s in left]}"); self.kill_all()

        def s3():
            if self.cause in ("signal", "abort", "deadline-stall", "deadline-wall", "leaf-missing", "viol-teardown", "internal-error"):
                if [p for p in self.registry if p.poll() is None]: self.kill_all()
        for fn in (s1, s2, s3, lambda: self.take_abort(final=True)): self._step(fn)
        try:
            self.poll_all()
        except BaseException:
            self.viol.add("internal")
        # ขั้น 5–8 รันเสมอ · ล้ม → super.err · exit 77 · ไม่แตะ current (stale ภายหลัง = fail-closed)
        try:
            if self.spawned and self.child.returncode is None:
                rc = 77; self.viol.add("killfail")
                cst = S.read_stat(self.child.pid)
                if cst and (self.child.pid, cst["starttime"]) not in self.left: self.left.append((self.child.pid, cst["starttime"]))
            elif self.spawned:
                r = self.child.returncode; rc = 128 - r if r < 0 else r
            else:
                rc = 77
            if self.sig and self.cause != "signal": self.note.append(f"sig{self.sig}")
            honored = self.cause == "abort" and self.abort_reason is not None and "killfail" not in self.viol
            fd = os.open(self.log_path, os.O_WRONLY | os.O_APPEND)
            try:
                with open(self.log_path, "rb") as f:
                    f.seek(0, 2)
                    if f.tell():
                        f.seek(-1, 2)
                        if f.read(1) != b"\n": os.write(fd, b"\n")
                for tb in self.tb:
                    os.write(fd, "".join(f"[run] internal: {l}\n" for l in tb.rstrip("\n").split("\n")).encode())
                if honored: os.write(fd, f"{S.ABORT_LINE}{self.abort_reason} ts={ts()} ns={time.time_ns()}\n".encode())
                end = S.fmt_end(rc, S.oom_kill(), self.seq, self.cause or "internal-error", self.viol,
                                [tuple(x) for x in self.left], [n.replace(" ", "_").replace(",", ";") for n in self.note])
                os.write(fd, (end + "\n").encode()); os.fsync(fd)
            finally:
                os.close(fd)
            rec = S.parse_end(end)
        except BaseException:
            self.err(traceback.format_exc()); return 77
        self.write_current("killfail" if "killfail" in self.viol else "exited", rc=rc)
        return S.exit_code("log", rec)


# ====================================================================================== front · client modes
def front_run(rundir, mode, key=None):
    rd = rundir
    os.makedirs(S.run_path(rd, ""), mode=0o755, exist_ok=True)
    if mode.startswith("t-") and not os.path.basename(rd).startswith(S.SMOKE_PREFIX):
        print(f"[run] mode {mode} ใช้ได้เฉพาะ RUNDIR {S.SMOKE_PREFIX}*"); return 77
    ns0 = time.time_ns()
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    if S.sig_masks(os.getpid())[1] & S.mask_of([signal.SIGCHLD]): print("[run] SIGCHLD ยัง ignore"); return 77
    errf = open(S.run_path(rd, f"super.{ns0}.err"), "ab")
    p = subprocess.Popen([S.PY, "-I", "-B", SELF, "--super", rd, mode, "--ns", str(ns0)] + (["--args", key] if key else []),
                         start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=errf, close_fds=True)
    errf.close()
    print(f"[run] supervisor pid={p.pid} ns={ns0} mode={mode}" + (f" args={key}" if key else ""))
    try:
        r = p.wait()
    except KeyboardInterrupt:
        print("[run] front ออก (supervisor ยังรันต่อ · ไม่ใช่ abort)"); return 130
    try:
        sup_rc = 128 - r if r < 0 else r
        got = S.record_of(rd, ns0)
        if got is None or got[0] == "log-noend":
            print(f"[run] ไม่มี record ของ ns={ns0} (supervisor rc={sup_rc}) · ดู run/super.{ns0}.err"); return 77
        if got[0] == "log-tool":
            print(f"[run] label=TOOL {got[1]} · log={os.path.basename(got[2])} (supervisor rc={sup_rc})"); return 77
        kind, rec, logp = got
        want = S.exit_code(kind, rec)
        if kind == "gate":
            print(f"[run] gate rc={rec['rc']} cause={rec['cause']} reason={rec.get('reason')} viol={rec.get('viol')}")
        else:
            print(f"[run] end rc={rec['rc']} cause={rec['cause']} viol={sorted(rec['viol']) or '-'} note={rec['note']} log={os.path.basename(logp)}")
            try:
                lab = S.attempt_label(rd, logp)
                print(f"[run] label verdict={lab['verdict']} child_class={lab['child_class']} ({lab['why']}) · ป้ายชั่วคราว: ใช้ตัดสินไปต่อ/หยุด/รันซ้ำ")
            except BaseException as e:
                print(f"[run] label=TOOL {type(e).__name__}: {e}")
        if sup_rc != want:
            print(f"[run] supervisor exit {sup_rc} ≠ ค่าตาม record {want}"); return 77
        return want
    except BaseException:
        traceback.print_exc(); return 77


def front_abort(rd, reason):
    p = S.run_path(rd, "current")
    cur = S.read_json(p) if os.path.exists(p) else None
    if cur and cur.get("state") == "running" and not S.alive(cur["sup_pid"], cur["sup_starttime"], cur["boot_id"]):
        print(f"[abort] E77:run-died run_id={cur.get('run_id')} (supervisor ตาย · start ถัดไปจะได้ stale-run → kill-orphan)"); return 77
    if not cur or cur.get("state") != "running":
        t_end = time.time() + 5
        while time.time() < t_end:                                         # รอ run ใหม่ ≤5 s
            time.sleep(1)
            if os.path.exists(p):
                c2 = S.read_json(p)
                if c2.get("state") == "running" and (not cur or c2.get("run_id") != cur.get("run_id")): cur = c2; break
        else:
            print("[abort] ignored-no-run"); return 0
    rid = cur["run_id"]
    S.write_json_atomic(S.run_path(rd, "abort.req"), {"run_id": rid, "reason": reason, "ns": time.time_ns()})
    for _ in range(25):
        time.sleep(1)
        if S.taken_exists(rd, rid): print(f"[abort] honored run_id={rid}"); return 0
        c = S.read_json(p)
        if c.get("run_id") == rid and c.get("state") != "running": print(f"[abort] ignored-completed run_id={rid}"); return 0
        if not S.alive(cur["sup_pid"], cur["sup_starttime"], cur["boot_id"]): print("[abort] E77:run-died"); return 77
    print("[abort] E77:abort-timeout (req ค้าง · supervisor จะ stale มันภายหลัง)"); return 77


def front_kill_orphan(rd):
    import fcntl
    fd = os.open(os.path.join(S.ROOT, "trellis.lock"), os.O_RDWR | os.O_CREAT, 0o644)
    t_end = time.time() + 5
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); break
        except BlockingIOError:
            if time.time() > t_end: print("[kill-orphan] lock ไม่ว่าง (มี supervisor รันอยู่)"); return 77
            time.sleep(0.5)
    groups = {}                                                             # run_id → {sup, rundir, targets}
    found, unread = S.trellis_env_procs(exclude=(os.getpid(),))
    if unread: print(f"[kill-orphan] environ อ่านไม่ได้ (same uid · ไม่นับเป็นเป้า): {unread}")
    for st, e in found:
        rid = e["TRELLIS_RUN_ID"]
        if "TRELLIS_SUP" not in e:
            print(f"[kill-orphan] 77 unknown-sup pid={st['pid']} comm={st['comm']} id={rid} · ไม่ kill · ตรวจ/kill ด้วยมือแล้วบันทึก Progress Log"); return 77
        try:
            grd = S.valid_rundir(e.get("TRELLIS_RUNDIR", ""), need_run=True)
        except ValueError as ex:
            print(f"[kill-orphan] 77 bad-rundir pid={st['pid']} ({ex}) · ไม่ kill ไม่เขียน"); return 77
        g = groups.setdefault(rid, {"sup": e["TRELLIS_SUP"], "rundir": grd, "targets": []})
        g["targets"].append((st["pid"], st["starttime"]))
    p = S.run_path(rd, "current")
    if os.path.exists(p):                                                   # (ข) stale/killfail ของ RUNDIR ที่เรียก
        cur = S.read_json(p); rid = cur.get("run_id"); bid = S.boot_id()
        try:
            unresolved = rid and not S.resolved(rd, rid)
            atts = [S.read_attempt(x) for x in glob.glob(S.run_path(rd, "*.log"))] if unresolved else []
        except S.ToolError as ex:
            print(f"[kill-orphan] 77 อ่าน record ของ {rd} ไม่ได้ ({ex}) · ไม่ kill"); return 77
        if unresolved:
            g = groups.setdefault(rid, {"sup": f"{cur['sup_pid']}:{cur['sup_starttime']}:{cur['boot_id']}", "rundir": rd, "targets": []})
            for a in atts:                                                  # left= ใช้เฉพาะ record ของ boot ปัจจุบัน (pid+starttime ข้าม boot ไม่มีความหมาย)
                if a["run_id"] == rid and a["end"] and a["boot_id"] == bid: g["targets"] += [t for t in a["end"]["left"] if t not in g["targets"]]
            for gr in S.read_gates(rd):
                if gr.get("run_id") == rid and gr.get("boot_id") == bid:
                    g["targets"] += [tuple(t) for t in gr.get("left") or [] if tuple(t) not in g["targets"]]
    if not groups: print("[kill-orphan] ไม่มีเป้า"); return 0
    rc = 0
    for rid, g in groups.items():
        sp, sst, bid = g["sup"].split(":")
        if S.alive(int(sp), int(sst), bid): print(f"[kill-orphan] 77 supervisor ของ {rid} ยัง alive · ไม่ kill"); rc = 77; continue
        live = S.kill_targets({tuple(t): None for t in g["targets"]}, group=False)   # ราย pid หลังเช็ค starttime (ไม่ killpg)
        if live: print(f"[kill-orphan] 77 ยังเหลือ {sorted(live)} ของ {rid} · ไม่เขียน marker"); rc = 77; continue
        ns = time.time_ns()
        S.write_json_atomic(S.run_path(g["rundir"], f"orphan.{rid}.{ns}.rec"),
                            {"id": rid, "targets": g["targets"], "ns": ns, "ts": ts(), "by_rundir": rd, "boot_id": S.boot_id()})   # r15: boot ของ kill-orphan (CUT ii)
        cp = S.run_path(g["rundir"], "current")
        if os.path.exists(cp):
            cur = S.read_json(cp)
            if cur.get("run_id") == rid: cur["state"] = "recovered"; S.write_json_atomic(cp, cur)
        print(f"[kill-orphan] {rid}: kill {len(g['targets'])} · orphan.rec → {g['rundir']}")
    return rc


def main(argv):
    if len(argv) >= 6 and argv[1] == "--super":
        signal.pthread_sigmask(signal.SIG_BLOCK, SIGS)                     # บรรทัดแรกของ supervisor
        key = argv[7] if len(argv) == 8 and argv[6] == "--args" else None   # front validate แล้ว (S.key_from_args)
        return Supervisor(argv[2], argv[3], int(argv[5]), key).run()
    if len(argv) < 3: print(__doc__); return 77
    try:
        rd = S.valid_rundir(argv[1])
    except ValueError as e:
        print(f"[run] {e}"); return 77
    if os.path.realpath(SELF) != os.path.join(rd, "repo", "Scripts", "host19_run.py"):
        print(f"[run] host19_run.py ต้องอยู่ใน {rd}/repo/Scripts (ได้ {SELF})"); return 77
    mode, rest = argv[2], argv[3:]
    if mode == "cert_v2":                                                   # K-1: args → key (validate รูป · variant/world จริง = child assert)
        try:
            key = S.key_from_args(rest)
            if S.parse_key(key)[1] == "h0pilot": raise ValueError("world h0pilot ใช้ mode pilot เท่านั้น")
        except ValueError as e: print(f"[run] cert_v2 args: {e}"); return 77
        return front_run(rd, mode, key)
    if mode == "pilot":
        if rest: print("[run] pilot ไม่รับ args (key ตายตัว " + S.PILOT_KEY + ")"); return 77
        return front_run(rd, mode)
    reason = rest[0] if rest else ""
    if any(ord(c) < 32 for c in reason) or S.ABORT_LINE.strip() in reason: print("[run] REASON มี control char หรือ token ต้องห้าม"); return 77
    if mode == "abort":
        if not reason: print("[abort] ต้องมีเหตุผล"); return 77
        return front_abort(rd, reason)
    if mode == "kill-orphan": return front_kill_orphan(rd)
    if mode in CMDS or mode in T_CMDS: return front_run(rd, mode)
    print(f"[run] mode ไม่รู้จัก: {mode}"); return 77


if __name__ == "__main__":
    sys.exit(main(sys.argv))
