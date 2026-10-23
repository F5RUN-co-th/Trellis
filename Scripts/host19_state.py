# -*- coding: utf-8 -*-
"""host19_state — นิยามร่วมที่เดียว (single source) ของ supervisor host19_run.py · front · kill-orphan · host19_accept.py
(spec = Plan/TRELLIS-010_host19_supervisor.md · r13 + §13 pilot/cert_v2 (r14) + retry CUT/fingerprint gate (r15) · Progress Log 2026-10-21/22/23)

ในไฟล์นี้: grammar ของบรรทัด LOG (START_RE/END_RE · fmt_end) · enum cause/viol · key ของ post-B + post_deadline · classifier ราย attempt + judge ของ series ·
attempt_label (front/selftest/smoke ใช้ตัวเดียว) · resolved() · exit_code() (กฎ G-1) · valid_rundir() · child_env() · /proc helpers
ห้าม import ad4_card หรือ numpy ที่ระดับ module (supervisor assert "numpy" not in sys.modules · front เรียก attempt_label)
import บน Windows ได้: fcntl / /proc ใช้เฉพาะใน function
"""
import os, re, io, json, glob, ast

ROOT = "/home/dev-ai/trellis-test"
PY = ROOT + "/python/bin/python3.11"
RUNDIR_RE = re.compile(r"^run_[A-Za-z0-9_.-]+$")
SMOKE_PREFIX = "run_smoke"                                                  # t-* mode รันได้เฉพาะ RUNDIR ที่ชื่อขึ้นต้นด้วยนี้
NPYOFF = "AVX512F AVX512CD AVX512_SKX AVX512_CLX AVX512_CNL AVX512_ICL AVX512_SPR"
TEST_ENV = ("TRELLIS_TEST_KILLFAIL", "TRELLIS_TEST_RAISE_AFTER_REAP")      # fault injection · มีผลเฉพาะ mode t-*

# ---------------------------------------------------------------- grammar ของ LOG (ฝั่งเขียนและฝั่งอ่านใช้ชุดเดียว)
START_PREFIX = re.compile(r"^\[run\] start ")
START_RE = re.compile(r"^\[run\] start mode=(\S+) att=(\d+) ts=(\S+ \S+) run_id=(\S+) oom_kill=(\d+) seq=(\d+) ns=(\d+) "
                      r"boot_id=(\S+) sup=(\d+):(\d+) bt=(\d+)(?: args=(\S+))?$")   # r13: bt = CLOCK_BOOTTIME ns ตอนได้ lock · r14: args= เฉพาะ POST_MODES (optional → อ่าน LOG r13 ได้)
END_PREFIX = re.compile(r"^\[run\] end ")
END_RE = re.compile(r"^\[run\] end rc=(-?\d+) oom_kill=(\d+) seq=(\d+) cause=(\S+) viol=(\S+)(?: left=(\S+))?(?: note=(\S+))?$")
RE_VENUE = re.compile(r"^\[venue\] (\{.*\})\s*$")
RE_LIVE = re.compile(r"^\s+\[RG14\] world (\d+)/50 Δsd=([+-]\d+\.\d{5}) Δq95=([+-]\d+\.\d{5}) · distinct (\d+)/(\d+) atom (\d+)/(\d+) ")
RE_AD4 = re.compile(r"^\[AD4\] v2 · SPEC_SHA (\w+)… · card_sha_runtime (\w+)… · closure (\w+)…")
RE_TB_LAST = re.compile(r"^(\w[\w.]*(?:Error|Exception|Collapse|Exit))\b")
RE_CHUNK = re.compile(r"^\[cert_v2\] (\w+)/(\w+) cell=(\S+) draws (\d+)\.\.(\d+) → (\S+) · ")   # บรรทัดสรุปของ cert_chunk (ad4_card.py:578)
CERT_SUFFIX = "/repo/Scripts/ad4_cert_out_v2/"                              # re-root path ของ .19 → <run_dir>/repo/Scripts/ad4_cert_out_v2/ (archive ใช้ได้)
ABORT_LINE = "[OPERATOR-ABORT] "
FAILLOUD_MSGS = ("collapse (n_distinct=1)", "v5-local:", "positive control:")
FP_KEYS = ("python", "executable", "numpy", "scipy", "dispatch_found", "baseline", "exp_f64", "openblas", "libc",
           "sha_libm.so.6", "sha_libc.so.6", "machine", "host_sha")                # host_sha = runner code (host19_preflight.HOST_FILES) · เปลี่ยนข้าม attempt = NEWDIR

# cause = เหตุที่ child หลักจบ ณ เวลาที่จบ (ค่าเดียว) · viol = ความผิดด้านความถูกต้อง (สะสม)
CAUSE_LOG = ("child-exit", "abort", "signal", "deadline-stall", "deadline-wall", "leaf-missing", "viol-teardown",
             "internal-error", "spawn-fail")
CAUSE_GATE = ("lock-busy", "resources", "state", "orphan-env", "stale-run", "venue-fail", "venue-exit", "viol-teardown",
              "pre-lock-assert", "signal", "abort", "deadline-wall", "internal-error")
VIOLS = ("escape", "leftover", "killfail", "internal")

# post-B (§13 spec): pilot/cert_v2 ต่อจาก rg14 PASS ใน RUNDIR เดียว · ระบุ chunk ด้วย key <variant>/<world>/<cell|->/<k0>/<k1>
POST_MODES = ("pilot", "cert_v2")
PILOT_KEY = "c1full/h0pilot/-/0/30"                                         # card :88 (pilot 30 draws) · ad4_card.py:516 · seed ad4_v2_h0pilot_{k}
KEY_TOKEN = re.compile(r"^[a-z0-9_]+$")
POST_CPU_STALL, POST_WALL_BASE, POST_WALL_PER_DRAW = 1800, 3600, 600        # G-1: wall = BASE + n·PER_DRAW (3.05×/draw ของ 197.0 s/draw ที่ pilot วัดบน .19 · c1full/h0)

# r15 (spec §13 R15-1): signal ที่ supervisor ถือเป็น stop = แหล่งเดียว (runner สร้าง STOP_SIGS จากนี้ + assert เลขตรง OS) · เลข = Linux ABI ของ record
STOP_SIGNALS = {"SIGTERM": 15, "SIGHUP": 1, "SIGINT": 2, "SIGQUIT": 3}
SIGKILL_NUM = 9
CUT_RC = frozenset([128 + n for n in STOP_SIGNALS.values()] + [128 + SIGKILL_NUM])   # child ตายด้วย signal ภายนอก (วัด .19 10-23: 129/130/131/137/143)
CUT_CAUSES = ("signal", "deadline-stall", "deadline-wall", "leaf-missing", "spawn-fail")   # supervisor/ระบบตัด attempt จากภายนอก
CARD_FILE = "ad4_card.py"                                                   # ไฟล์ข้างตัว (repo/Scripts ของ RUNDIR เดียวกัน)


def parse_key(key):
    """key → (variant, world, cell|None, k0, k1) · รูปผิด → ValueError (front คืน 77 · judge ถือว่า record ผิด)"""
    parts = key.split("/") if isinstance(key, str) else []
    if len(parts) != 5: raise ValueError(f"key ต้องมี 5 ส่วน: {key!r}")
    v, w, c, k0, k1 = parts
    if not (KEY_TOKEN.match(v) and KEY_TOKEN.match(w)): raise ValueError(f"variant/world ต้องเป็น [a-z0-9_]+: {key!r}")
    if not (c == "-" or c.isdigit()) or not (k0.isdigit() and k1.isdigit()) or int(k0) >= int(k1):
        raise ValueError(f"cell ต้องเป็นตัวเลขหรือ '-' · k0 < k1 ตัวเลข: {key!r}")
    return v, w, (None if c == "-" else int(c)), int(k0), int(k1)


def key_from_args(args):
    """CLI ของ cert_v2: <variant> <world> [cell] <k0> <k1> (เท่า ad4_card.py:1129-1132) → key (ValueError ถ้ารูปผิด)"""
    if len(args) == 4: v, w, k0, k1 = args; c = "-"
    elif len(args) == 5: v, w, c, k0, k1 = args
    else: raise ValueError(f"cert_v2 ต้องมี args 4 หรือ 5 ตัว ได้ {len(args)}")
    key = "/".join((v, w, c, k0, k1)); parse_key(key)
    return key


def card_ast(src=None):
    """AST ของ ad4_card.py (อ่าน source · ไม่ import = ไม่โหลด numpy/data) · src default = ไฟล์ข้างตัว"""
    src = src or os.path.join(os.path.dirname(os.path.abspath(__file__)), CARD_FILE)
    return ast.parse(io.open(src, encoding="utf-8").read(), filename=src)


def card_consts(names, tree):
    """ค่า literal ของชื่อใน ad4_card → dict · ต้องมี binding เดียวทั้ง module (ast.walk: Name ที่ไม่ใช่ Load · import alias) และ binding นั้น =
    `NAME = <literal>` ระดับ module · ไม่ครบ/ซ้ำ/AugAssign/AnnAssign/tuple/ซ้อนใน block/ไม่ใช่ literal → ToolError (fail-closed)"""
    binds = {nm: 0 for nm in names}
    for n in ast.walk(tree):
        nm = n.id if isinstance(n, ast.Name) and not isinstance(n.ctx, ast.Load) else (n.asname or n.name) if isinstance(n, ast.alias) else None
        if nm in binds: binds[nm] += 1
    tops = {nm: [n for n in tree.body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                 and n.targets[0].id == nm] for nm in names}
    out = {}
    for nm in names:
        if binds[nm] != 1 or len(tops[nm]) != 1:
            raise ToolError(f"{CARD_FILE}: {nm} ต้องมี binding เดียว `{nm} = <literal>` ระดับ module (binding {binds[nm]} · top-level {len(tops[nm])})")
        try: out[nm] = ast.literal_eval(tops[nm][0].value)
        except ValueError: raise ToolError(f"{CARD_FILE}: {nm} ไม่ใช่ literal")
    return out


def _eval_n(node, env):
    """evaluator ของนิพจน์ "N" (ad4_card.py:516) · รับเฉพาะ IfExp / Compare (== ตัวเดียว) / Name ใน env / Constant · อื่น → ToolError (fail-closed)"""
    if isinstance(node, ast.IfExp): return _eval_n(node.body if _eval_n(node.test, env) else node.orelse, env)
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq) and len(node.comparators) == 1:
        return _eval_n(node.left, env) == _eval_n(node.comparators[0], env)
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in env: return env[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, str)): return node.value
    raise ToolError(f"{CARD_FILE}: นิพจน์ N มี node ที่ไม่รองรับ {type(node).__name__}")


def post_n(world, src=None):
    """N ต่อ world ของ chunk header = นิพจน์ "N" ใน header_fields ของ ad4_card.py (แหล่งเดียว · spec §13 R15-4 · ไม่มีตัวเลขซ้ำ)
    อ่านจาก AST (header_fields ต้องมี ad = data · venue/supervisor ไม่โหลด) · ไม่พบ/รูปผิด → ToolError"""
    tree = card_ast(src)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "header_fields"]
    if len(fns) != 1: raise ToolError(f"{CARD_FILE}: header_fields ต้องมี 1 ตัว ได้ {len(fns)}")
    exprs = [v for d in ast.walk(fns[0]) if isinstance(d, ast.Dict)
             for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant) and k.value == "N"]
    if len(exprs) != 1: raise ToolError(f"{CARD_FILE}: key \"N\" ใน header_fields ต้องมี 1 ตัว ได้ {len(exprs)}")
    n = _eval_n(exprs[0], dict(card_consts(("CERT_N", "CERT_N_POWER"), tree), world=world))
    if not isinstance(n, int) or isinstance(n, bool): raise ToolError(f"{CARD_FILE}: N ของ {world} ไม่ใช่ int ({n!r})")
    return n


def post_env(key):
    """env เพิ่มของ venue + child หลัก (Y-1): h0stress บน variant ≠ c1full = contingency N5(2) → AD4_CONTINGENCY (ad4_card.py:548) · ไม่อยู่ใน FP_KEYS"""
    if key is None: return {}
    v, w, _, _, _ = parse_key(key)
    return {"AD4_CONTINGENCY": v} if w == "h0stress" and v != "c1full" else {}


def check_key(key, mode, environ):
    """post-B key ตรงค่าที่ ad4_card ลงทะเบียนไว้ (แหล่งเดียว · spec §13 Y-2) → [เหตุผลที่ผิด] (ว่าง = ผ่าน)
    import ad4_card ใน function เท่านั้น: เรียกจาก venue child (host19_preflight venue --key) และ selftest · supervisor ไม่เรียก (numpy ห้ามใน supervisor)"""
    from ad4_card import VARIANTS, WORLDS, POWER_CELLS
    v, w, c, k0, k1 = parse_key(key)
    bad = []
    if v not in VARIANTS: bad.append(f"variant {v} ∉ {VARIANTS}")
    if w not in WORLDS: bad.append(f"world {w} ∉ {WORLDS}")
    if mode == "pilot" and key != PILOT_KEY: bad.append(f"pilot key ต้องเป็น {PILOT_KEY}")
    if mode == "cert_v2" and w == "h0pilot": bad.append("world h0pilot ใช้ mode pilot เท่านั้น")
    if (w == "flip") != (c is not None): bad.append("cell ต้องมีเฉพาะ world flip")
    if c is not None and not 0 <= c < len(POWER_CELLS): bad.append(f"cell {c} ∉ 0..{len(POWER_CELLS) - 1}")
    n = post_n(w)                                                           # r15: อ่านนิพจน์ของ ad4_card เอง (ไม่มีของซ้ำให้ drift)
    if k1 > n: bad.append(f"k1 {k1} > N {n} ของ {w}")
    if w == "h0stress" and v != "c1full" and environ.get("AD4_CONTINGENCY") != v: bad.append(f"h0stress {v} ต้องมี AD4_CONTINGENCY={v}")
    return bad


def post_deadline(key):
    """(cpu_stall s, wall_cap s) ของ pilot/cert_v2 · ที่เดียว (runner + selftest)"""
    _, _, _, k0, k1 = parse_key(key)
    return POST_CPU_STALL, POST_WALL_BASE + (k1 - k0) * POST_WALL_PER_DRAW


class ToolError(Exception):
    """ข้อมูลอ่านไม่ได้ตาม grammar → exit TOOL (ไม่ใช่ verdict)"""


def _set(field): return set() if field in (None, "-") else set(field.split(","))


def fmt_end(rc, oom, seq, cause, viol, left=(), note=()):
    """end line ตาม END_RE (ไม่มี LF · ผู้เขียนเติม LF เอง) · ตรวจกลับด้วย END_RE ก่อนคืน"""
    assert cause in CAUSE_LOG, cause
    assert set(viol) <= set(VIOLS), viol
    s = f"[run] end rc={rc} oom_kill={oom} seq={seq} cause={cause} viol={','.join(sorted(viol)) or '-'}"
    if left: s += " left=" + ",".join(f"{p}:{st}" for p, st in left)
    if note: s += " note=" + ",".join(note)
    assert END_RE.match(s), s
    return s


def fmt_start(mode, att, ts, run_id, oom, seq, ns, boot_id, sup_pid, sup_st, bt, args=None):
    s = f"[run] start mode={mode} att={att} ts={ts} run_id={run_id} oom_kill={oom} seq={seq} ns={ns} boot_id={boot_id} sup={sup_pid}:{sup_st} bt={bt}"
    assert (args is not None) == (mode in POST_MODES), (mode, args)
    if args is not None: parse_key(args); s += f" args={args}"
    assert START_RE.match(s), s
    return s


def parse_end(line):
    """→ dict หรือ None (ไม่ match grammar) · ToolError ถ้า cause/viol นอก enum"""
    m = END_RE.match(line)
    if not m: return None
    rc, oom, seq, cause, viol, left, note = m.groups()
    viol = _set(viol)
    if cause not in CAUSE_LOG: raise ToolError(f"cause นอก enum: {cause}")
    if not viol <= set(VIOLS): raise ToolError(f"viol นอก enum: {viol}")
    lefts = [tuple(int(x) for x in t.split(":")) for t in left.split(",")] if left else []
    return {"rc": int(rc), "oom1": int(oom), "seq": int(seq), "cause": cause, "viol": viol, "left": lefts,
            "note": note.split(",") if note else []}


# ---------------------------------------------------------------- records ใน RUNDIR/run
def run_path(rundir, *p): return os.path.join(rundir, "run", *p)


def read_json(p): return json.load(io.open(p, encoding="utf-8"))


def write_json_atomic(p, obj):
    tmp = f"{p}.{os.getpid()}.tmp"                                             # ชื่อไม่ซ้ำ: writer สองตัวพร้อมกันไม่ชน
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, (json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")); os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, p)
    if os.name == "posix":                                                  # fsync dir (Windows เปิด dir ไม่ได้ · selftest บนเครื่องวิน)
        dfd = os.open(os.path.dirname(p), os.O_RDONLY)
        try: os.fsync(dfd)
        finally: os.close(dfd)


def read_gates(rundir):
    out = []
    for p in sorted(glob.glob(run_path(rundir, "gate.*.rec"))):
        g = read_json(p); g["_path"] = p; out.append(g)
    return out


def read_orphans(rundir):
    out = []
    for p in sorted(glob.glob(run_path(rundir, "orphan.*.rec"))):
        o = read_json(p); o["_path"] = p; out.append(o)
    return out


def taken_exists(rundir, run_id): return bool(glob.glob(run_path(rundir, f"abort.{run_id}.*.taken")))


# ---------------------------------------------------------------- attempt (LOG) · classifier · judge
def read_attempt(path):
    raw = io.open(path, encoding="utf-8", errors="replace").read()
    lines = raw.split("\n")
    if not lines or not START_PREFIX.match(lines[0]): raise ToolError(f"{path}: ไม่มีบรรทัด [run] start")
    m = START_RE.match(lines[0])
    if not m: raise ToolError(f"{path}: start line ไม่ตรง grammar r13/r14 (ต้องมี seq= … bt=) · log format เก่า")
    mode, att, ts, run_id, oom0, seq, ns, boot_id, sp, sst, bt, args = m.groups()
    if (args is not None) != (mode in POST_MODES): raise ToolError(f"{path}: args= ต้องมีเฉพาะ mode {POST_MODES} (mode={mode})")
    if args is not None:
        try: parse_key(args)
        except ValueError as e: raise ToolError(f"{path}: {e}")
    a = {"path": path, "mode": mode, "att": int(att), "ts": ts, "run_id": run_id, "oom0": int(oom0), "seq": int(seq),
         "ns": int(ns), "boot_id": boot_id, "sup": (int(sp), int(sst)), "bt": int(bt), "args": args, "lines": lines, "end": None, "venue": None}
    last = next((l for l in reversed(lines) if l.strip()), "")
    if END_PREFIX.match(last) and raw.endswith("\n"):                        # end line = บรรทัดสุดท้ายที่ไม่ว่าง ∧ ปิดด้วย LF (raw text)
        a["end"] = parse_end(last)                                           # ไม่ match grammar (partial write) → None
    for ln in lines:
        v = RE_VENUE.match(ln)
        if v: a["venue"] = json.loads(v.group(1)); break
    return a


def read_attempts(rundir):
    """เรียงด้วย seq (ใต้ global lock) · seq ซ้ำ → ToolError · ภายใน boot_id เดียวกัน bt ต้องเพิ่มแบบ strict ตาม seq (seq reset ใน boot เดียวกัน)
    → ToolError · ข้าม boot ไม่ตรวจ bt (seq reset ข้าม boot ถูกกันที่ supervisor: seq หายทั้งที่มี record = gate 77)"""
    atts = sorted((read_attempt(p) for p in glob.glob(run_path(rundir, "*.log"))), key=lambda a: a["seq"])
    seqs = [a["seq"] for a in atts]
    if len(set(seqs)) != len(seqs): raise ToolError(f"{rundir}: seq ซ้ำ {sorted(x for x in set(seqs) if seqs.count(x) > 1)}")
    last_bt = {}
    for a in atts:
        if a["boot_id"] in last_bt and a["bt"] <= last_bt[a["boot_id"]]:
            raise ToolError(f"{os.path.basename(a['path'])}: seq {a['seq']} แต่ bt ไม่มากกว่า attempt ก่อนใน boot เดียวกัน (seq reset?)")
        last_bt[a["boot_id"]] = a["bt"]
    return atts


def last_exc(lines):
    """ชนิด exception ของ Traceback ตัวสุดท้าย (ไม่ใช่บรรทัดท้าย · time -v ต่อท้ายเสมอ)"""
    idx = [i for i, l in enumerate(lines) if l.startswith("Traceback (most recent call last)")]
    if not idx: return None, ""
    for l in lines[idx[-1] + 1:]:
        m = RE_TB_LAST.match(l)
        if m: return m.group(1).split(".")[-1], l
    return "?", ""


def chunk_attested(a, rundir):
    """post-B attempt: บรรทัดสรุป [cert_v2] ตรง key ของ start line ∧ ไฟล์ chunk มีอยู่ (re-root path ด้วย CERT_SUFFIX) → (bool, why)"""
    v, w, c, k0, k1 = parse_key(a["args"])
    ms = [m for m in (RE_CHUNK.match(l) for l in a["lines"]) if m]
    if len(ms) != 1: return False, f"บรรทัดสรุป [cert_v2] ต้องมี 1 บรรทัด ได้ {len(ms)}"   # cert_chunk พิมพ์ครั้งเดียวต่อ chunk (ad4_card.py:578)
    mv, mw, mc, m0, m1, path = ms[0].groups()
    if (mv, mw, mc, int(m0), int(m1)) != (v, w, "None" if c is None else str(c), k0, k1 - 1):
        return False, f"บรรทัดสรุป {mv}/{mw}/cell={mc}/{m0}..{m1} ไม่ตรง key {a['args']}"
    if CERT_SUFFIX not in path: return False, f"path ไม่มี {CERT_SUFFIX}: {path}"
    local = os.path.join(rundir, "repo", "Scripts", "ad4_cert_out_v2", *path.split(CERT_SUFFIX, 1)[1].split("/"))
    if not os.path.isfile(local): return False, f"ไม่มีไฟล์ chunk {local}"
    return True, f"chunk {os.path.basename(local)}"


RETRYABLE = ("INFRA", "ABORT", "CUT")   # รันซ้ำ key เดิมได้ 1 ครั้งหลัง: invalid-infra (ตาราง (6)) · operator abort ที่ honored (ตาราง (5) "ไม่รันซ้ำอัตโนมัติ" ≠ ห้ามรันซ้ำ) ·
                                        # r15 CUT = ถูกตัดจากภายนอก (signal/deadline/leaf/spawn/reboot) · draw = seed ต่อ tag → รันซ้ำได้แถวเดิม (ไม่มี selection)


def key_ok(cls):
    """กติกาเดียวของ post-B ต่อ key (judge + gate · spec §13 D-6): attempt ตัวท้าย OK ∧ ≤ 2 attempt ∧ ตัวก่อนหน้า ∈ RETRYABLE (รันซ้ำ tag เดิมได้ 1 ครั้ง)"""
    return bool(cls) and cls[-1] == "OK" and len(cls) <= 2 and all(c in RETRYABLE for c in cls[:-1])


def pilot_ok(post):
    """post = attempt ของ POST_MODES ที่มี a["cls"] แล้ว (เรียงตาม seq) → seq ของ pilot attempt ที่ทำให้ PILOT_KEY ผ่าน key_ok · None = ยังไม่ผ่าน
    card :144 ลำดับ = pilot ก่อน certify → cert_v2 ทุก attempt ต้องมี seq มากกว่าค่านี้ (judge) และ runner gate ก่อน spawn cert_v2"""
    xs = [a for a in post if a["mode"] == "pilot" and a["args"] == PILOT_KEY]
    return xs[-1]["seq"] if key_ok([a["cls"] for a in xs]) else None


def b_cut(atts):
    """index ของ attempt สุดท้ายของ B (mode ∉ POST_MODES) ใน atts ที่เรียงตาม seq · None = ไม่มี · judge + may_spawn ใช้ตัวเดียว (R15-2)"""
    return max((i for i, a in enumerate(atts) if a["mode"] not in POST_MODES), default=None)


def overlap(key, keys):
    """key อื่นใน keys ที่ [k0,k1) ทับ key (variant, world, cell เดียวกัน) → key แรกที่ทับ หรือ None · judge + may_spawn (d) ใช้ตัวเดียว (R15-3)
    (read_chunks ad4_card.py:605-607 continuity → k ซ้ำ = report ล้มถาวร)"""
    v, w, c, k0, k1 = parse_key(key)
    for o in keys:
        if o == key: continue
        v2, w2, c2, a0, a1 = parse_key(o)
        if (v2, w2, c2) == (v, w, c) and a0 < k1 and k0 < a1: return o
    return None


def may_spawn(mode, key, atts):
    """gate คู่ของ judge (ที่เดียว · runner gates() เรียกก่อน venue/LOG) · atts = ทุก attempt ของ RUNDIR ที่มี a["cls"] แล้ว → (ok, why)
    (a) mode ของ B หลังมี post-B attempt = ย้ายจุดตัดของ judge → ห้าม (b) post: ประวัติ cls ของ key = [] หรือ [x ∈ RETRYABLE] (D-6 · key_ok)
    (c) cert_v2: pilot_ok · world ≠ h0pilot (d) cert_v2: [k0,k1) ไม่ทับ key อื่นของ (variant, world, cell) เดียวกันที่มี attempt ใดๆ (overlap)
    (e) r15 R15-2: post mode ต้องมี attempt สุดท้ายของ B = rg14 ที่ cls PASS (b_cut · เท่าเงื่อนไขของ judge)"""
    post = [a for a in atts if a["mode"] in POST_MODES]
    if mode not in POST_MODES:
        return (False, f"มี post-B attempt แล้ว {len(post)} ตัว · mode {mode} ของ B หลัง post-B = series ใช้ไม่ได้") if post else (True, "")
    i = b_cut(atts)
    if i is None or atts[i]["mode"] != "rg14" or atts[i]["cls"] != "PASS":
        last = "ไม่มี" if i is None else f"{atts[i]['mode']} {atts[i]['cls']}"
        return False, f"attempt สุดท้ายของ B = {last} · post-B ต้องตามหลัง rg14 PASS (R15-2)"
    hist = [a["cls"] for a in post if a["mode"] == mode and a["args"] == key]
    if not (hist == [] or (len(hist) == 1 and hist[0] in RETRYABLE)):
        return False, f"key {key} มีประวัติ {hist} · รันซ้ำได้ 1 ครั้งหลัง {'/'.join(RETRYABLE)} เท่านั้น (D-6)"
    if mode == "cert_v2":
        v, w, c, k0, k1 = parse_key(key)
        if w == "h0pilot": return False, "world h0pilot ใช้ mode pilot เท่านั้น"
        if pilot_ok(post) is None: return False, f"ยังไม่มี pilot ({PILOT_KEY}) ที่ผ่าน · cert_v2 ต้องตามหลัง pilot (card :144)"
        o = overlap(key, [a["args"] for a in post])
        if o: return False, f"ช่วง [{k0},{k1}) ทับ {o} (k ซ้ำใน series {v}/{w}/{c})"
    return True, ""


def _child_exit_class(a, t, exc, rundir):
    e = a["end"]
    if a["mode"] == "rg14":
        if "RG14 raise: upper t-CI" in t: return "RAISE"
        if any(s in t for s in FAILLOUD_MSGS) and exc == "AssertionError": return "FAILLOUD"
    if a["mode"] == "regress" and exc in ("AssertionError", "RG12Collapse"): return "REGRESS_FAIL"
    if (e["rc"] == 137 and e["oom1"] - a["oom0"] >= 1) or (e["rc"] == 1 and (exc or "").endswith("MemoryError")): return "INFRA"
    if e["rc"] == 0:
        if a["mode"] == "regress" and "[regress] RG1-RG13 · RG15 PASS · RG14 SKIPPED" in t: return "OK"
        if a["mode"] == "rg14" and "[RG14] PASS (ไม่ raise)" in t: return "PASS"
        if a["mode"] == "preflight" and "[preflight] PASS" in t: return "OK"
        if a["mode"] in POST_MODES and chunk_attested(a, rundir)[0]: return "OK"
        if a["mode"].startswith("t-"): return "OK"                          # smoke mode ของ supervisor เอง
    return "INVALID"


def orphan_recs(rid, orphans): return [o for o in orphans if o.get("id") == rid]


def env_gate_hit(rid, gates): return any(g.get("cause") == "orphan-env" and rid in (g.get("target_run_ids") or []) for g in gates)


def escape_after_end(a, gates, orphans):
    """orphan.rec ของ run_id ∨ gate orphan-env ที่ชี้ run_id (B-part + post-B · พฤติกรรมเดิม r12)"""
    return bool(orphan_recs(a["run_id"], orphans)) or env_gate_hit(a["run_id"], gates)


def died_cut(a, gates, orphans):
    """R15-1 (ii) supervisor-died ที่ถูกตัดด้วย reboot: orphan.rec ของ run_id ≥ 1 ∧ ทุกตัวมี targets + boot_id ∧ targets == [] ∧ boot_id ≠ boot ของ attempt
    ∧ ไม่มี gate orphan-env ของ run_id · pure function ของ record (gate = judge) · orphan.rec ไม่มี boot_id (r14) → ไม่ CUT"""
    recs = orphan_recs(a["run_id"], orphans)
    return bool(recs) and not env_gate_hit(a["run_id"], gates) and \
        all("targets" in o and "boot_id" in o and o["targets"] == [] and o["boot_id"] != a["boot_id"] for o in recs)


def classify_attempt(a, rundir, gates=None, orphans=None):
    """→ (verdict, child_class, why) · สองขั้น: child_class จาก cause · viol ≠ ∅ → INVALID (child_class เป็นป้ายรอง)"""
    gates = read_gates(rundir) if gates is None else gates
    orphans = read_orphans(rundir) if orphans is None else orphans
    e = a["end"]
    post = a["mode"] in POST_MODES
    abort_line = any(l.startswith(ABORT_LINE) for l in a["lines"]); taken = taken_exists(rundir, a["run_id"])
    if e is None:
        if post and not abort_line and not taken and died_cut(a, gates, orphans):
            return "CUT", None, "supervisor-died · kill-orphan หลัง reboot ไม่มีเป้า (R15-1 ii)"
        return "INVALID", None, "supervisor-died (ไม่มี end line ครบ grammar + LF)"
    t = "\n".join(a["lines"]); exc, _ = last_exc(a["lines"])
    if e["cause"] == "child-exit" and not abort_line and not taken:
        cc, why = _child_exit_class(a, t, exc, rundir), f"rc={e['rc']}"
        if post and e["rc"] == 0: why += " · " + chunk_attested(a, rundir)[1]
        if post and cc == "INVALID" and e["rc"] in CUT_RC: cc, why = "CUT", why + " = 128+signal (R15-1 iii)"
    elif e["cause"] == "abort" and abort_line and taken: cc, why = "ABORT", "honored (บรรทัด + .taken)"
    elif e["cause"] == "abort" or abort_line or taken: cc, why = "INVALID", f"abort ไม่ครบ (cause={e['cause']} line={abort_line} taken={taken})"
    elif post and e["cause"] in CUT_CAUSES: cc, why = "CUT", f"cause={e['cause']} (R15-1 i)"
    else: cc, why = "INVALID", f"cause={e['cause']}"
    if e["viol"]: return "INVALID", cc, f"viol={','.join(sorted(e['viol']))}"
    if escape_after_end(a, gates, orphans): return "INVALID", cc, "escape-after-end"
    return cc, cc, why


def attempt_label(rundir, log_path):
    """ป้ายราย attempt (ค่าชั่วคราว · ใช้ตัดสินไปต่อ/หยุด/รันซ้ำเท่านั้น · รายงานผลใช้ judge)"""
    a = read_attempt(log_path)
    verdict, cc, why = classify_attempt(a, rundir)
    e = a["end"] or {}
    return {"verdict": verdict, "child_class": cc, "why": why, "mode": a["mode"], "att": a["att"], "run_id": a["run_id"],
            "rc": e.get("rc"), "cause": e.get("cause"), "viol": sorted(e.get("viol", ())), "note": e.get("note", [])}


def fp(a): return None if a["venue"] is None else {k: a["venue"].get(k) for k in FP_KEYS}


def fp_diff(venue, atts):
    """R15-6: fingerprint ของ venue ที่เพิ่งวัด เทียบ attempt แรกของ RUNDIR (ตัวเดียวกับ fps[0] ของ judge) → [key ที่ต่าง] · ไม่มี attempt → []
    attempt แรกไม่มี [venue] → ToolError (runner → gate 77)"""
    if not atts: return []
    f0 = fp(atts[0])
    if f0 is None: raise ToolError(f"{os.path.basename(atts[0]['path'])}: ไม่มี [venue]")
    f1 = fp({"venue": venue})
    return sorted(k for k in FP_KEYS if f0[k] != f1[k])


def judge(run_dir, b_start, rg14_tags, spec_sha, closure):
    """verdict ของ series · B-part (ตาราง state (1)–(8) · ลำดับเดิมทุกขั้น) คำนวณบน prefix จนถึง attempt สุดท้ายของ B (preflight/regress/rg14) ·
    post-B (pilot/cert_v2 · spec §13) หลังจุดตัด: ทุก key ต้อง OK (RETRYABLE ก่อนหน้าได้ 1 ครั้งต่อ key · key_ok) ∧ ไม่มี k ทับ (overlap) → ไม่งั้น POST_FAIL ·
    fingerprint เดียวทั้ง series · รันบน .19 (CLAUDE.md §สนามรัน) หรือบน archive ที่ track แล้ว (path re-root ด้วย CERT_SUFFIX)"""
    atts_all = read_attempts(run_dir)
    notes = []
    if not atts_all: return "INVALID", ["ไม่มี log"]
    gates, orphans = read_gates(run_dir), read_orphans(run_dir)
    for a in atts_all:
        c, cc, why = classify_attempt(a, run_dir, gates, orphans); a["cls"] = c
        notes.append(f"{os.path.basename(a['path'])}: {c} (child_class={cc} · {why})")
    for g in gates: notes.append(f"gate {os.path.basename(g['_path'])}: rc={g.get('rc')} cause={g.get('cause')} reason={g.get('reason')}")
    for o in orphans: notes.append(f"orphan {os.path.basename(o['_path'])}: id={o.get('id')}")
    cut = b_cut(atts_all)                                                   # attempt สุดท้ายของ B (ไม่ใช่ rg14 PASS ตัวแรก: ตาราง state เดิมตัดสินที่ attempt สุดท้าย)
    if cut is None: return "INVALID", notes + ["ไม่มี attempt ของ B (มีแต่ post-B)"]
    atts, post = atts_all[:cut + 1], atts_all[cut + 1:]
    if any(a["mode"] in POST_MODES for a in atts): return "INVALID", notes + ["post-B attempt (pilot/cert_v2) ก่อน attempt สุดท้ายของ B"]
    by = {m: [a for a in atts if a["mode"] == m] for m in ("preflight", "regress", "rg14")}
    last = atts[-1]
    if last["cls"] in ("ABORT", "INFRA", "FAILLOUD", "REGRESS_FAIL", "INVALID"): return last["cls"], notes
    if any(a["cls"] == "REGRESS_FAIL" for a in by["regress"]): return "REGRESS_FAIL", notes
    if not any(a["cls"] == "OK" for a in by["preflight"]): return "INVALID", notes + ["ไม่มี preflight PASS"]
    if not any(a["cls"] == "OK" for a in by["regress"]): return "INVALID", notes + ["ไม่มี regress PASS"]
    if last["mode"] != "rg14" or last["cls"] not in ("PASS", "RAISE"): return "INVALID", notes + ["attempt สุดท้ายไม่ใช่ rg14 PASS/raise"]
    fps = [fp(a) for a in atts_all]                                         # B-part + post-B = fingerprint ชุดเดียว (gate pilot+certify)
    if any(f is None for f in fps): return "INVALID", notes + ["attempt ไม่มี [venue]"]
    if any(f != fps[0] for f in fps): return "NEWDIR", notes + ["env fingerprint ต่างข้าม attempt"]
    for a in by["regress"] + by["rg14"]:
        ms = [RE_AD4.match(l) for l in a["lines"]]; ms = [m for m in ms if m]
        if not ms: return "INVALID", notes + [f"{a['path']}: ไม่มีบรรทัด [AD4]"]
        s, c, cl = ms[0].groups()
        if not (spec_sha.startswith(s) and spec_sha.startswith(c) and closure.startswith(cl)):
            return "INVALID", notes + [f"{a['path']}: SPEC/card/closure ไม่ตรง ({s}/{c}/{cl})"]
    rp = os.path.join(run_dir, "repo", "Scripts", "ad4_cert_out_v2", "regress_receipt.json")
    if not os.path.exists(rp): return "INVALID", notes + ["ไม่มี receipt"]
    r = read_json(rp)
    if r.get("closure_sha") != closure or r.get("SPEC_SHA") != spec_sha: return "INVALID", notes + ["receipt closure/SPEC ไม่ตรง"]
    if not r.get("regress") or not str(r.get("regress_at", "")) >= b_start: return "INVALID", notes + ["receipt regress ไม่อยู่หลัง B start"]
    if last["cls"] == "PASS" and (not r.get("rg14") or not str(r.get("rg14_at", "")) >= b_start):
        return "INVALID", notes + ["receipt rg14 ไม่อยู่หลัง B start"]
    cp = os.path.join(run_dir, "repo", "Scripts", "ad4_cert_out_v2", "rg14", "checkpoint_v6.json")
    if not os.path.exists(cp): return "INVALID", notes + ["ไม่มี checkpoint"]
    ck = read_json(cp)
    if set(ck) != set(rg14_tags) or len(ck) != 50: return "INVALID", notes + [f"checkpoint key {len(ck)} ≠ RG14_TAGS"]
    if any(e.get("closure_sha") != closure for e in ck.values()): return "INVALID", notes + ["checkpoint closure ไม่ตรง"]
    live = {}
    for a in by["rg14"]:
        for l in a["lines"]:
            m = RE_LIVE.match(l)
            if m:
                k = int(m.group(1)); val = m.groups()[1:]
                if k in live and live[k] != val: return "NEWDIR", notes + [f"world {k}: บรรทัดสดค่าต่างกันข้าม attempt"]
                live[k] = val
    missing = [k for k in range(1, 51) if k not in live]
    if missing: return "NEWDIR", notes + [f"ไม่มีบรรทัดสด (unattested): {missing}"]
    for k, val in live.items():
        e = ck[rg14_tags[k - 1]]
        exp = (f"{e['dsd']:+.5f}", f"{e['dq95']:+.5f}", str(e["nd_alt2"]), str(e["nd_v5local"]), str(e["atom_alt2"]), str(e["atom_v5local"]))
        if val != exp: return "INVALID", notes + [f"world {k}: บรรทัดสด {val} ≠ checkpoint {exp}"]
    notes.append("ตรวจครบ: fingerprint คงที่ · card/SPEC/closure · receipt หลัง B start · 50 world มีบรรทัดสดตรง checkpoint")
    if not post: return last["cls"], notes
    if last["cls"] != "PASS": return "INVALID", notes + [f"post-B หลัง rg14 {last['cls']}"]
    keys = {}
    for a in post: keys.setdefault(a["args"], []).append(a)
    p_seq, bad = pilot_ok(post), []
    for k, xs in keys.items():
        cls = [x["cls"] for x in xs]
        ok, why = key_ok(cls), ""
        if ok and k != PILOT_KEY and (p_seq is None or xs[0]["seq"] < p_seq):   # card :144: pilot ก่อน certify
            ok, why = False, " (ไม่มี pilot OK ก่อนหน้า)"
        o = overlap(k, list(keys))
        if o: ok, why = False, why + f" (k ทับ {o})"                        # R15-3: judge ตรวจ (d) เท่า gate
        notes.append(f"post-B {k}: {' → '.join(cls)} → {'OK' if ok else 'ไม่ผ่าน'}{why}")
        if not ok: bad.append(k)
    if bad: return "POST_FAIL", notes + [f"B-part PASS · post-B ไม่ผ่าน {bad}"]
    return "PASS", notes + [f"B-part PASS · post-B OK {len(keys)} key"]


# ---------------------------------------------------------------- resolved · exit (G-1)
def resolved(rundir, run_id):
    """SoR = record write-once: orphan.rec ∨ end line (start run_id=id) ∨ gate field run_id==id · ที่ killfail ∉ viol · target_run_ids ไม่นับ"""
    if any(o.get("id") == run_id for o in read_orphans(rundir)): return True
    for p in glob.glob(run_path(rundir, "*.log")):
        a = read_attempt(p)
        if a["run_id"] == run_id and a["end"] is not None and "killfail" not in a["end"]["viol"]: return True
    return any(g.get("run_id") == run_id and "killfail" not in set(g.get("viol") or ()) for g in read_gates(rundir))


def record_of(rundir, ns0):
    """record ของ ns0 (front) → ("log", end, path) | ("log-noend", None, path) | ("log-tool", "<exc>", path) | ("gate", rec, None) | None
    · อ่าน ns จาก START_RE ก่อน → LOG ของ ns0 ที่ parse ส่วนอื่นไม่ได้ = log-tool (front พิมพ์ label=TOOL · exit 77)"""
    for p in glob.glob(run_path(rundir, "*.log")):
        first = io.open(p, encoding="utf-8", errors="replace").readline().rstrip("\n")
        m = START_RE.match(first)
        if not m or int(m.group(7)) != ns0: continue
        try:
            a = read_attempt(p)
        except ToolError as e:
            return "log-tool", str(e), p
        return ("log", a["end"], p) if a["end"] else ("log-noend", None, p)
    for g in read_gates(rundir):
        if g.get("ns0") == ns0: return "gate", g, None
    return None


def exit_code(kind, rec):
    """กฎ G-1 · kind=log: rc จริงถ้า cause=child-exit ∧ viol ว่าง · อื่น 77 · kind=gate: rc ของ gate (75/76/77)"""
    if kind == "gate": return int(rec["rc"])
    return int(rec["rc"]) if rec["cause"] == "child-exit" and not rec["viol"] else 77


# ---------------------------------------------------------------- rundir · env
def valid_rundir(path, need_run=False):
    """→ realpath หรือ raise ValueError · ลูกโดยตรงของ ROOT · ชื่อ run_* · มี repo/ (และ run/ ถ้า need_run)"""
    rp = os.path.realpath(path)
    if any(c.isspace() for c in rp): raise ValueError(f"RUNDIR มี whitespace: {rp!r}")
    if os.path.dirname(rp) != ROOT or not RUNDIR_RE.match(os.path.basename(rp)): raise ValueError(f"RUNDIR ไม่ใช่ {ROOT}/run_*: {rp}")
    if not os.path.isdir(os.path.join(rp, "repo")): raise ValueError(f"RUNDIR ไม่มี repo/: {rp}")
    if need_run and not os.path.isdir(os.path.join(rp, "run")): raise ValueError(f"RUNDIR ไม่มี run/: {rp}")
    return rp


def child_env(run_id, sup_pid, sup_st, boot_id, rundir):
    """env เดียวของทุก child (venue · child หลัก) · ส่งผ่าน Popen(env=)"""
    return {"PATH": "/usr/bin:/bin", "HOME": ROOT, "LANG": "C.UTF-8", "TZ": "UTC", "OPENBLAS_VERBOSE": "2",
            "OPENBLAS_CORETYPE": "Haswell", "NPY_DISABLE_CPU_FEATURES": NPYOFF, "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "GIT_CEILING_DIRECTORIES": ROOT,
            "TRELLIS_RUN_ID": run_id, "TRELLIS_SUP": f"{sup_pid}:{sup_st}:{boot_id}", "TRELLIS_RUNDIR": rundir}


def test_env_violation(mode, environ):
    """TRELLIS_TEST_* ใน mode ที่ไม่ใช่ t-* → ชื่อตัวแปร (= pre-lock-assert)"""
    bad = [k for k in TEST_ENV if environ.get(k)]
    return bad if bad and not mode.startswith("t-") else []


# ---------------------------------------------------------------- /proc helpers (Linux)
def boot_id(): return io.open("/proc/sys/kernel/random/boot_id").read().strip()


def read_stat(pid):
    """→ dict หรือ None (process หายไป) · parse ด้วย rsplit(") ") กัน comm ที่มีช่องว่าง/วงเล็บ"""
    try:
        s = io.open(f"/proc/{pid}/stat").read()
    except (FileNotFoundError, ProcessLookupError):
        return None
    head, rest = s.rsplit(") ", 1)
    f = rest.split()
    return {"pid": int(pid), "comm": head.split("(", 1)[1], "state": f[0], "ppid": int(f[1]), "pgid": int(f[2]), "sid": int(f[3]),
            "utime": int(f[11]), "stime": int(f[12]), "starttime": int(f[19])}


def all_stats():
    out = {}
    for d in os.listdir("/proc"):
        if d.isdigit():
            st = read_stat(d)
            if st: out[st["pid"]] = st
    return out


def descendants(root_pid, stats=None):
    """descendant ที่ไม่ใช่ Z ของ root_pid (ppid tree · subreaper ทำให้ orphan ของต้นไม้กลับมาอยู่ใต้ root)"""
    stats = all_stats() if stats is None else stats
    kids = {}
    for st in stats.values(): kids.setdefault(st["ppid"], []).append(st["pid"])
    out, stack = [], list(kids.get(root_pid, []))
    while stack:
        p = stack.pop()
        if p in stats:
            out.append(stats[p]); stack.extend(kids.get(p, []))
    return [s for s in out if s["state"] != "Z"]


def same_uid(pid):
    """process เป็นของ uid เดียวกับเรา (ขอบเขต C3 = same uid เท่า host19_run.sh:18-24)"""
    try: return os.stat(f"/proc/{pid}").st_uid == os.getuid()
    except (FileNotFoundError, ProcessLookupError): return False


def environ_trellis(pid):
    """→ dict ของตัวแปร TRELLIS_* ใน environ (อ่านใน memory · ไม่ log เนื้อหาอื่น) · None = อ่านไม่ได้"""
    try:
        raw = open(f"/proc/{pid}/environ", "rb").read()
    except (FileNotFoundError, ProcessLookupError):
        return {}
    except PermissionError:
        return None
    out = {}
    for kv in raw.split(b"\0"):
        if kv.startswith(b"TRELLIS_"):
            k, _, v = kv.partition(b"=")
            out[k.decode(errors="replace")] = v.decode(errors="replace")
    return out


def trellis_env_procs(exclude=()):
    """process same uid ที่ environ มี TRELLIS_RUN_ID → ([(stat, env)], [(pid, comm) ที่อ่าน environ ไม่ได้]) · ที่เดียวของ C3/kill-orphan"""
    found, unread = [], []
    for st in all_stats().values():
        if st["state"] == "Z" or st["pid"] in exclude or not same_uid(st["pid"]): continue
        e = environ_trellis(st["pid"])
        if e is None: unread.append((st["pid"], st["comm"]))
        elif "TRELLIS_RUN_ID" in e: found.append((st, e))
    return found, unread


def live_targets(targets):
    """targets {(pid, starttime): ...} → {(pid, st0): stat} ที่ยังอยู่ (starttime ตรง · ไม่ใช่ Z) · read_stat ครั้งเดียวต่อ pid"""
    out = {}
    for (p, st0) in targets:
        st = read_stat(p)
        if st is not None and st["starttime"] == st0 and st["state"] != "Z": out[(p, st0)] = st
    return out


def kill_targets(targets, group, poll_cb=lambda: None, skip_kill=False, grace=10.0, tick=0.2):
    """TERM → รอ grace → KILL → รอ grace · group=True: killpg เมื่อ pid เป็น leader ของ pgid ตัวเอง (supervisor · descendant ทั้งต้นไม้)
    group=False: ราย pid เท่านั้น (kill-orphan · เป้าจาก environ/left=) · poll_cb เรียกทุก tick (reap) · skip_kill = fault injection
    → dict ของตัวที่ยังเหลือ (ว่าง = เกลี้ยง)"""
    import signal, time
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if sig == signal.SIGKILL and skip_kill: break
        for (p, st0), s in live_targets(targets).items():
            try:
                if group and s["pgid"] == p: os.killpg(p, sig)
                else: os.kill(p, sig)
            except ProcessLookupError:
                pass
        t_end = time.monotonic() + grace
        while time.monotonic() < t_end:
            poll_cb()
            if not live_targets(targets): return {}
            time.sleep(tick)
    poll_cb()
    return live_targets(targets)


def sig_masks(pid):
    """→ (SigBlk, SigIgn) เป็น int · None ถ้าหายไป"""
    try:
        txt = io.open(f"/proc/{pid}/status").read()
    except (FileNotFoundError, ProcessLookupError):
        return None
    m = {l.split(":")[0]: int(l.split()[1], 16) for l in txt.splitlines() if l.startswith(("SigBlk:", "SigIgn:"))}
    return m["SigBlk"], m["SigIgn"]


def mask_of(sigs):
    m = 0
    for s in sigs: m |= 1 << (int(s) - 1)
    return m


def alive(pid, starttime, bid):
    if bid != boot_id(): return False
    st = read_stat(pid)
    return st is not None and st["starttime"] == starttime and st["state"] != "Z"


def oom_kill():
    for l in io.open("/proc/vmstat"):
        if l.startswith("oom_kill "): return int(l.split()[1])
    return -1


def mem_load():
    avail = next(int(l.split()[1]) // 1024 for l in io.open("/proc/meminfo") if l.startswith("MemAvailable:"))
    return avail, float(io.open("/proc/loadavg").read().split()[0])
