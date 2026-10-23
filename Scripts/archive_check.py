# -*- coding: utf-8 -*-
"""archive_check — archive gate (ก)–(ง) + ตรวจโครงสร้าง chunk ของ archive ใต้ Scripts/ad4_cert_out_v2/ (spec Plan/TRELLIS-010_host19_supervisor.md
:116 archive gate · §13 R15-5 · D-7) · tool ของ repo แบบ ledger_check (รันบน local ที่ commit + selftest บน .19 และ local) · ไม่อยู่ใน HOST_FILES

usage
  python Scripts/archive_check.py <A>          A = path ของ archive (relative ต่อ root ของ repo เช่น Scripts/ad4_cert_out_v2/host19_c81b4cf)
  python Scripts/archive_check.py --self-test  fixture สังเคราะห์ใน git repo ชั่วคราว (ไม่ copy chunk จริง)
ลำดับ (spec :116): แก้ doc ทั้งหมด → stage ทุกไฟล์ → archive_check → commit · หลัง commit ก่อน push = fresh clone บน .19 (ไม่อยู่ใน tool นี้)

ตรวจ (พิมพ์เฉพาะ path + ชนิดความผิด · ไม่พิมพ์เนื้อหาไฟล์ · RI-5 card :145):
  (ข) ignored    ไฟล์ใต้ Scripts/ad4_cert_out_v2 ที่ git ignore (git check-ignore --no-index)
  (ก) sums       ชื่อใน A/SHA256SUMS = git ls-files A (ยกเว้น SHA256SUMS) ทั้งสองทาง
  (ค) eol        git ls-files --eol Scripts/ad4_cert_out_v2: attr/-text ∧ i/ = w/
  (ง) attrs      .gitattributes ใน working tree = HEAD = index · sha256 ของ blob ใน index = SHA256SUMS · working tree = index (ไฟล์ใน A)
                 + `git diff --quiet` ทั้ง repo (unstaged · spec :116) · ไฟล์ใน A ที่ไม่ได้ track (untracked · ตกหล่นเงียบแบบ 04358f9)
  chunk          <A>/repo/Scripts/ad4_cert_out_v2/<variant ∈ VARIANTS>/<world>[_c<cell>]_<k0>_<k1>.csv: บรรทัด 1 `# {` + json · บรรทัด 2 `# schema: ` ·
                 แถวข้อมูล (บรรทัด 3+) ไม่ว่าง ∧ จำนวน field = schema ∧ จำนวนแถว = k1−k0 · byte สุดท้าย = LF · ไม่มี CR · `*.csv.tmp` = violation
exit: 0 PASS · 1 violation · 2 tool-error (ห้ามพิมพ์ข้อความ exception ที่มาจากเนื้อหาไฟล์)
"""
import os, sys, re, io, json, hashlib, subprocess, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import host19_state as S

V2 = "Scripts/ad4_cert_out_v2"
SUMS = "SHA256SUMS"
CHUNK_RE = re.compile(r"^repo/Scripts/ad4_cert_out_v2/([a-z0-9_]+)/([a-z0-9]+)(?:_c(\d+))?_(\d+)_(\d+)\.csv$")


class Tool(Exception):
    """tool-error (exit 2) · ข้อความ = ของ tool เอง ไม่ใช่เนื้อหาไฟล์"""


def git(repo, *args, inp=None):
    r = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=repo, input=inp, capture_output=True)
    return r.returncode, r.stdout, r.stderr


def git_ok(repo, *args, inp=None):
    rc, out, err = git(repo, *args, inp=inp)
    if rc != 0: raise Tool(f"git {args[0]} rc={rc}")
    return out


def long_path(p):
    """Windows: prefix \\\\?\\ ให้ Python เปิด path > 259 ตัวอักษรได้ (LongPathsEnabled=0 · spec :116)"""
    ap = os.path.abspath(p)
    return "\\\\?\\" + ap if os.name == "nt" and not ap.startswith("\\\\?\\") else ap


def sums_of(raw):
    """เนื้อหา SHA256SUMS → {name: sha} (ข้ามบรรทัด #) · รูปผิด → Tool"""
    out = {}
    for ln in raw.decode("utf-8").splitlines():
        if not ln or ln.startswith("#"): continue
        m = re.match(r"^([0-9a-f]{64}) [ *](.+)$", ln)
        if not m: raise Tool("SHA256SUMS มีบรรทัดผิดรูป")
        out[m.group(2)] = m.group(1)
    return out


def index_blobs(repo, paths):
    """→ {path: bytes ของ blob ใน index} ผ่าน git cat-file --batch (ไม่ผ่าน checkout = ไม่มี eol conversion)"""
    stage = git_ok(repo, "ls-files", "-s", "-z", "--", *paths).split(b"\0")
    ids = {}
    for rec in stage:
        if not rec: continue
        meta, path = rec.split(b"\t", 1)
        ids[path.decode("utf-8")] = meta.split()[1].decode()
    if not ids: return {}
    rc, out, _ = git(repo, "cat-file", "--batch", inp=("\n".join(ids.values()) + "\n").encode())
    if rc != 0: raise Tool("git cat-file rc ≠ 0")
    res, pos = {}, 0
    for path, oid in ids.items():
        nl = out.index(b"\n", pos); head = out[pos:nl].split()
        if head[0].decode() != oid or head[1] != b"blob": raise Tool("cat-file คืนลำดับ/ชนิดไม่ตรง")
        n = int(head[2]); res[path] = out[nl + 1:nl + 1 + n]; pos = nl + 1 + n + 1
    return res


def chunk_errs(rel, data, variants):
    """โครงสร้าง chunk ตาม ad4_card.py cert_chunk (:553 ชื่อ · :571-576 เขียน) → [ชนิดความผิด] · ไม่คืนเนื้อหา"""
    m = CHUNK_RE.match(rel)
    if not m: return ["chunk-path"]
    var, world, cell, k0, k1 = m.groups()
    errs = []
    if var not in variants: errs.append("chunk-variant")
    if b"\r" in data: errs.append("chunk-cr")
    if not data.endswith(b"\n"): errs.append("chunk-no-final-lf")
    try: lines = data.decode("utf-8").split("\n")
    except UnicodeDecodeError: return errs + ["chunk-utf8"]
    if lines and lines[-1] == "": lines = lines[:-1]
    if len(lines) < 2 or not lines[0].startswith("# {"): return errs + ["chunk-header"]
    try: json.loads(lines[0][2:])
    except ValueError: errs.append("chunk-header-json")
    if not lines[1].startswith("# schema: "): return errs + ["chunk-schema"]
    ncol = len(lines[1][len("# schema: "):].split(","))
    rows = lines[2:]
    if any(not r for r in rows): errs.append("chunk-empty-row")
    if any(r and len(r.split(",")) != ncol for r in rows): errs.append("chunk-field-count")
    if len(rows) != int(k1) - int(k0): errs.append("chunk-row-count")
    return errs


def check(repo, A):
    """→ [(path, ชนิด)] · Tool ถ้า A/repo ใช้ไม่ได้"""
    A = A.replace("\\", "/").rstrip("/")
    if not A.startswith(V2 + "/"): raise Tool(f"A ต้องอยู่ใต้ {V2}/")
    if git(repo, "rev-parse", "--show-toplevel")[0] != 0: raise Tool("ไม่ใช่ git repo")
    if not os.path.isdir(long_path(os.path.join(repo, A))): raise Tool(f"ไม่มี {A}")
    viol = []
    # (ข) ignored · ไฟล์ทุกไฟล์บนดิสก์ใต้ V2
    files = []
    for dp, _, fs in os.walk(long_path(os.path.join(repo, V2))):
        for f in fs: files.append(os.path.relpath(os.path.join(dp, f), long_path(repo)).replace("\\", "/"))
    rc, out, _ = git(repo, "check-ignore", "--no-index", "--stdin", inp=("\n".join(files) + "\n").encode())
    if rc not in (0, 1): raise Tool(f"git check-ignore rc={rc}")
    viol += [(p, "ignored") for p in out.decode("utf-8").splitlines() if p]
    viol += [(p, "tmp-file") for p in files if p.startswith(A + "/") and p.endswith(".tmp")]
    viol += [(p, "untracked") for p in git_ok(repo, "ls-files", "--others", "--exclude-standard", "-z", "--", A).decode("utf-8").split("\0") if p]
    # (ก) sums สองทาง
    tracked = [p for p in git_ok(repo, "ls-files", "-z", "--", A).decode("utf-8").split("\0") if p]
    rel = sorted(p[len(A) + 1:] for p in tracked)
    if SUMS not in rel: return viol + [(f"{A}/{SUMS}", "sums-not-tracked")]
    blobs = index_blobs(repo, tracked)
    sums = sums_of(blobs[f"{A}/{SUMS}"])
    rel = [r for r in rel if r != SUMS]
    viol += [(f"{A}/{r}", "sums-missing") for r in rel if r not in sums]
    viol += [(f"{A}/{r}", "sums-extra") for r in sorted(sums) if r not in rel]
    # (ค) eol ของทั้ง V2
    for ln in git_ok(repo, "ls-files", "--eol", "--", V2).decode("utf-8").splitlines():
        meta, path = ln.split("\t", 1)
        i, w, attr = meta.split()[:3]
        if attr != "attr/-text": viol.append((path, "eol-attr"))
        if i[2:] != w[2:]: viol.append((path, "eol-i-w"))
    # (ง) .gitattributes precondition · sha ของ blob ใน index · working tree = index
    if git(repo, "diff", "--quiet", "HEAD", "--", ".gitattributes")[0] != 0 or \
            git(repo, "diff", "--cached", "--quiet", "--", ".gitattributes")[0] != 0:
        viol.append((".gitattributes", "attrs-changed"))
    viol += [(p, "unstaged") for p in git_ok(repo, "diff", "--name-only", "-z").decode("utf-8").split("\0") if p]   # spec :116 `git diff --quiet` ทั้ง repo
    for r in rel:
        b = blobs[f"{A}/{r}"]
        if r in sums and hashlib.sha256(b).hexdigest() != sums[r]: viol.append((f"{A}/{r}", "sha"))
        try: wt = open(long_path(os.path.join(repo, A, r)), "rb").read()
        except OSError: wt = None
        if wt != b: viol.append((f"{A}/{r}", "worktree-ne-index"))
    # chunk
    variants = S.card_consts(("VARIANTS",), S.card_ast(os.path.join(repo, "Scripts", S.CARD_FILE)))["VARIANTS"]
    for r in rel:
        if r.endswith(".csv") and r.startswith("repo/Scripts/ad4_cert_out_v2/"):
            viol += [(f"{A}/{r}", e) for e in chunk_errs(r, blobs[f"{A}/{r}"], variants)]
    longest = max((len(p) for p in tracked), default=0)
    print(f"[archive_check] {A}: {len(rel)} ไฟล์ + {SUMS} · path relative ยาวสุด {longest}")
    return viol


def run(repo, A):
    try:
        viol = check(repo, A)
    except Tool as e:
        print(f"[archive_check] TOOL: {e}"); return 2
    except Exception as e:                                                  # ไม่พิมพ์ str(e): อาจมาจากเนื้อหาไฟล์
        print(f"[archive_check] TOOL: {type(e).__name__}"); return 2
    for p, k in viol: print(f"  ✗ {k}: {p}")
    print(f"[archive_check] {'PASS' if not viol else f'FAIL ({len(viol)})'}")
    return 0 if not viol else 1


# ============================ self-test (fixture สังเคราะห์ · แต่ละ check ต้องยิงได้ด้วยตัวเอง) ============================
SENT = "SENTINEL_9f3c"                                                      # ต้องไม่ปรากฏใน output ใดๆ (ไม่พิมพ์เนื้อหา)
A_REL = V2 + "/host19_fix"
CH = "repo/Scripts/ad4_cert_out_v2/c1full/h0pilot_0_3.csv"


def _chunk(rows=3, ncol=3):
    hdr = "# " + json.dumps({"variant": "c1full", "note": SENT})
    body = [",".join([str(k), SENT] + ["0.5"] * (ncol - 2)) for k in range(rows)]
    return (hdr + "\n# schema: " + ",".join(f"c{i}" for i in range(ncol)) + "\n" + "\n".join(body) + "\n").encode()


def _write(root, rel, data):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(data)


def _seal(root):
    """สร้าง SHA256SUMS ใหม่จากไฟล์บนดิสก์ของ A แล้ว stage ทุกไฟล์ (ให้ (ก)–(ง) ผ่าน · เคส chunk ทดสอบเฉพาะ check ของ chunk)"""
    a = os.path.join(root, A_REL); lines = ["# fixture"]
    for dp, _, fs in os.walk(a):
        for f in sorted(fs):
            r = os.path.relpath(os.path.join(dp, f), a).replace("\\", "/")
            if r != SUMS: lines.append(f"{hashlib.sha256(open(os.path.join(dp, f), 'rb').read()).hexdigest()}  {r}")
    open(os.path.join(a, SUMS), "wb").write(("\n".join(lines) + "\n").encode())
    git_ok(root, "add", "-A")


def _fixture(root, card_src):
    git_ok(root, "init", "-q"); git_ok(root, "config", "user.email", "t@t"); git_ok(root, "config", "user.name", "t")
    git_ok(root, "config", "core.autocrlf", "false")
    _write(root, ".gitattributes", f"{V2}/** -text\n".encode())
    _write(root, ".gitignore", f"*.log\n*.bak\n!{V2}/**/*.log\n".encode())
    _write(root, "Scripts/" + S.CARD_FILE, card_src)
    _write(root, f"{A_REL}/run/rg14.1.log", b"[run] start\n")
    _write(root, f"{A_REL}/{CH}", _chunk())
    _seal(root)
    git_ok(root, "commit", "-q", "-m", "fixture")


def _case(card_src, mutate, seal=True):
    d = tempfile.mkdtemp(prefix="arcchk_")
    try:
        _fixture(d, card_src)
        if mutate: mutate(d)
        if seal: _seal(d)
        buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
        try: rc = run(d, A_REL)
        finally: sys.stdout = old
        return rc, buf.getvalue()
    finally:
        shutil.rmtree(d, ignore_errors=True)


def self_test():
    card_src = open(os.path.join(HERE, S.CARD_FILE), "rb").read()
    a = lambda d, rel: os.path.join(d, A_REL, rel)
    W = lambda data: (lambda d: _write(d, f"{A_REL}/{CH}", data))
    def crlf(d): _write(d, f"{A_REL}/{CH}", _chunk().replace(b"\n", b"\r\n"))
    def ignored(d): _write(d, f"{A_REL}/x.bak", b"x\n")
    def sums_extra(d):
        _seal(d); p = a(d, SUMS); open(p, "ab").write(("0" * 64 + "  ghost.txt\n").encode()); git_ok(d, "add", "-A")
    def sums_missing(d):
        _seal(d); _write(d, f"{A_REL}/extra.txt", b"x\n"); git_ok(d, "add", "-A")
    def sha_wrong(d):
        _seal(d); _write(d, f"{A_REL}/run/rg14.1.log", b"[run] changed\n"); git_ok(d, "add", "-A")
    def wt_ne(d):
        _seal(d); _write(d, f"{A_REL}/run/rg14.1.log", b"[run] dirty\n")
    def attrs(d):
        _write(d, ".gitattributes", b"# no -text rule\n"); git_ok(d, "add", "-A")
    def tmpf(d): _write(d, f"{A_REL}/{CH}.tmp", b"x\n")
    def unstaged(d):
        _seal(d); _write(d, "Scripts/" + S.CARD_FILE, card_src + b"\n# edit not staged\n")
    def untracked(d):
        _seal(d); _write(d, f"{A_REL}/run/new.out", b"x\n")
    bad_var = lambda d: (os.makedirs(a(d, "repo/Scripts/ad4_cert_out_v2/zz"), exist_ok=True),
                         os.replace(a(d, CH), a(d, "repo/Scripts/ad4_cert_out_v2/zz/h0pilot_0_3.csv")))
    cases = [("clean", None, True, 0, None),
             ("chunk ลบแถว", W(_chunk(rows=2)), True, 1, "chunk-row-count"),
             ("chunk เพิ่มแถว", W(_chunk(rows=4)), True, 1, "chunk-row-count"),
             ("chunk field ไม่ครบ", W(_chunk().replace(b",0.5\n", b"\n", 1)), True, 1, "chunk-field-count"),
             ("chunk แถวว่าง", W(_chunk().replace(b"\n2,", b"\n\n2,")), True, 1, "chunk-empty-row"),
             ("chunk byte ท้าย ≠ LF", W(_chunk()[:-1]), True, 1, "chunk-no-final-lf"),
             ("chunk CRLF", crlf, True, 1, "chunk-cr"),
             ("chunk header ไม่ใช่ # {", W(_chunk().replace(b"# {", b"#x{", 1)), True, 1, "chunk-header"),
             ("chunk header json เสีย", W(_chunk().replace(b'"note"', b'note', 1)), True, 1, "chunk-header-json"),
             ("chunk schema", W(_chunk().replace(b"# schema: ", b"# schemx: ", 1)), True, 1, "chunk-schema"),
             ("chunk variant ∉ VARIANTS", bad_var, True, 1, "chunk-variant"),
             ("(ข) ไฟล์ถูก ignore", ignored, True, 1, "ignored"),
             ("(ก) sums เกิน", sums_extra, False, 1, "sums-extra"),
             ("(ก) sums ขาด", sums_missing, False, 1, "sums-missing"),
             ("(ค) attr ไม่ใช่ -text", attrs, True, 1, "eol-attr"),
             ("(ง) .gitattributes ≠ HEAD", attrs, True, 1, "attrs-changed"),
             ("(ง) sha ผิด", sha_wrong, False, 1, "sha"),
             ("(ง) working tree ≠ index", wt_ne, False, 1, "worktree-ne-index"),
             (".csv.tmp", tmpf, True, 1, "tmp-file"),
             ("(ง) unstaged นอก A", unstaged, False, 1, "unstaged"),
             ("untracked ใน A", untracked, False, 1, "untracked")]
    bad, n = 0, 0
    for name, mut, seal, want_rc, want_kind in cases:
        rc, out = _case(card_src, mut, seal); n += 1
        ok = rc == want_rc and (want_kind is None or f"✗ {want_kind}:" in out) and SENT not in out
        bad += not ok
        print(f"  {'OK ' if ok else 'BAD'} {name:28s} rc={rc} (คาด {want_rc}{' · ' + want_kind if want_kind else ''})" + ("" if ok else f" · {out.strip()[-200:]!r}"))
    for name, fn in (("A ไม่มี → 2", lambda d: run(d, A_REL + "_none")), ("ไม่ใช่ git repo → 2", lambda d: run(d, A_REL))):
        d = tempfile.mkdtemp(prefix="arcchk_")
        try:
            if name.startswith("A"): _fixture(d, card_src)
            buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
            try: rc = fn(d)
            finally: sys.stdout = old
        finally:
            shutil.rmtree(d, ignore_errors=True)
        ok = rc == 2 and SENT not in buf.getvalue(); bad += not ok; n += 1
        print(f"  {'OK ' if ok else 'BAD'} {name:28s} rc={rc}")
    print(f"[self-test] {n - bad}/{n} OK")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # console cp874 ของ Windows
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test": sys.exit(self_test())
    if len(sys.argv) != 2 or sys.argv[1].startswith("--"): print(__doc__); sys.exit(2)
    sys.exit(run(os.path.dirname(HERE), sys.argv[1]))
