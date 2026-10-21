# -*- coding: utf-8 -*-
"""host19_preflight — ตัวตนของ input + env สำหรับรัน regress/RG14 บน 172.31.1.19 (วินสั่ง 2026-10-20 · Progress Log 2026-10-20)

modes
  manifest --out F.json --treeish REV [--repo DIR] [--tar F.tar] [--same-blobs-as G.json]
                                         (Windows) manifest ของชุด input: non-M1 = bytes ของ git blob ที่ treeish (SHA-1 assert ราย member ·
                                         ทุก path 1 ครั้ง · mode 100644/100755 · type blob · LFnorm(worktree)==blob · .npy worktree==blob) ·
                                         M1 = disk bytes (repo Gloo · ต้องไม่อยู่ใน treeish) · tar arcname repo/... · --same-blobs-as = blob id ราย path ต้องเท่าชุดที่ smoke2 ผ่าน
  emit --out F.json                      (Windows) reference: header_fields() ของ ad4_card + h0 _sha_lf + venue fingerprint
  check --ref F.json --manifest F.json   (.19) assert venue + manifest + เทียบ reference · exit 0 / 77 venue-env / 78 data / 2 tool-error
  venue [--strict] [--out F.json]        venue fingerprint · --out (absolute) = เขียน JSON atomic พร้อม run_id/pid (supervisor ตรวจ) · ไม่มี --out = พิมพ์

ตัวตนของข้อมูล = header_fields() (ad4_card.py:513-523 · X_sha/dayix_sha/n/NF/Nemb/fold_sizes/closure/SPEC/card_sha) — ไม่เขียนสูตร hash ใหม่ (Working Rule 3)
h0 = _sha_lf (ad4_card.py:57) · M1 = bytes sha ใน manifest · encoding ของ data hash ใน card §7 E-12 (:144) เป็นของ main phase — ขั้น 4a ต้อง reuse ฟังก์ชันเดียวกัน
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):   # ก่อน import numpy (ad4_card.py:16-18 ตั้งให้เฉพาะ argv ของ mode ตัวเอง)
    os.environ[_k] = "1"
assert "numpy" not in sys.modules, "numpy ถูก import ก่อนตั้ง threads"
sys.path.insert(0, HERE)                                                   # -I ตัด script dir ออกจาก sys.path
import io, json, hashlib, glob, ctypes, platform, tarfile, time, traceback, argparse, subprocess

REPO = os.path.dirname(HERE)
DATA_REL = "D:/workspace/Doc/T.me/R&D/Gloo/Data"                           # brain_v1_run.py:73 · บน POSIX = relative ต่อ cwd
YEARS = list(range(2011, 2021))                                            # brain_v1_run.py:75 · FROZEN: M1 เฉพาะ 2011-2020
MODULES = ["ad4_card", "ad1_card", "ad2_card", "tp1_card", "direction_predictor", "direction_at_real_exit",
           "ad1_gate_calib", "brain_v1_run", "dir_features", "dual_asian_sim", "entry_platform",
           "opportunity_unit_v3", "opportunity_unit_v4", "test_b_direction_decomp"]
H0 = ["h0_day_facts_2012_2020.csv", "h0_pokefeat_2012_2020.csv", "h0_dcfeat_2012_2020.csv"]   # brain_v1_run.py:115-117
HOST_FILES = ["Scripts/host19_run.py", "Scripts/host19_state.py", "Scripts/host19_preflight.py", "Scripts/host19_accept.py"]
REF_FILES = ["Scripts/host19_ref/preflight_ref.json", "Scripts/host19_ref/preflight_ref_X.npy"]   # emit ก่อน manifest (ไม่มีวงจร: ref ไม่อ้าง manifest)
CARD = "Plan/TRELLIS-010_card_AD4_fine_cadence.md"
DISPATCH_ON = ["SSSE3", "SSE41", "POPCNT", "SSE42", "AVX", "F16C", "FMA3", "AVX2"]
BASELINE = ["SSE", "SSE2", "SSE3"]
EXIT_VENUE, EXIT_DATA, EXIT_TOOL = 77, 78, 2


class VenueError(Exception): pass
class DataError(Exception): pass


def sha_bytes(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def input_set():
    """(relpath ใน repo, path บนดิสก์ local) ของชุด input ที่ระบุชัด · M1 อยู่ที่ DATA_REL (relative ต่อ repo บน .19)"""
    out = [(f"Scripts/{m}.py", os.path.join(HERE, f"{m}.py")) for m in MODULES]
    out += [(CARD, os.path.join(REPO, CARD))]
    out += [(f"Research/h0/{f}", os.path.join(REPO, "Research", "h0", f)) for f in H0]
    out += [(f, os.path.join(REPO, f)) for f in HOST_FILES + REF_FILES]
    out += [(f"{DATA_REL}/XAUUSD_M1_{y}.csv", os.path.join(DATA_REL, f"XAUUSD_M1_{y}.csv")) for y in YEARS]
    return out


def _git(repo, *args, data=None):
    return subprocess.run(["git", "-C", repo] + list(args), input=data, capture_output=True, check=True).stdout


def git_blobs(repo, treeish, rels):
    """→ (tree oid, {rel: (mode, oid, bytes)}) ของ treeish · resolve tree oid ครั้งเดียว · SHA-1 blob assert ราย member · ทุก path 1 ครั้ง"""
    tree = _git(repo, "rev-parse", "--verify", treeish + "^{tree}").decode().strip()
    ent = {}
    for rec in _git(repo, "ls-tree", "-r", "-z", tree, "--", *rels).split(b"\0"):
        if not rec: continue
        meta, path = rec.split(b"\t", 1); mode, typ, oid = meta.decode().split(); path = path.decode()
        if path in ent: raise DataError(f"path ซ้ำใน tree: {path}")
        if typ != "blob" or mode not in ("100644", "100755"): raise DataError(f"{path}: type/mode {typ}/{mode}")
        ent[path] = (mode, oid)
    miss = [r for r in rels if r not in ent]; extra = [p for p in ent if p not in rels]
    if miss or extra: raise DataError(f"treeish {treeish}: ขาด {miss} · เกิน {extra}")
    raw = _git(repo, "cat-file", "--batch", data="".join(ent[r][1] + "\n" for r in rels).encode())
    res, i = {}, 0
    for r in rels:
        nl = raw.index(b"\n", i); oid, typ, size = raw[i:nl].decode().split(); size = int(size)
        body = raw[nl + 1:nl + 1 + size]; i = nl + 1 + size + 1
        if oid != ent[r][1] or typ != "blob" or hashlib.sha1(b"blob %d\0" % size + body).hexdigest() != oid:
            raise DataError(f"{r}: blob SHA-1 ไม่ตรง")
        res[r] = (ent[r][0], oid, body)
    return tree, res


def mode_manifest(out, treeish, repo=None, tar_path=None, same_as=None):
    repo = repo or REPO
    allset = input_set()
    m1 = [(rel, src) for rel, src in allset if rel.startswith(DATA_REL + "/")]
    rels = [rel for rel, _ in allset if not rel.startswith(DATA_REL + "/")]
    tree, blobs = git_blobs(repo, treeish, rels)
    for rel in rels:                                                        # worktree (ที่แก้จริง) ต้องเท่า blob ของ treeish
        wt = open(os.path.join(REPO, rel), "rb").read(); body = blobs[rel][2]
        if (wt if rel.endswith(".npy") else wt.replace(b"\r\n", b"\n")) != body: raise DataError(f"{rel}: worktree ≠ blob ของ {treeish}")
        if rel in HOST_FILES and b"\r" in body: raise DataError(f"{rel}: blob มี CR")
    in_tree = set(_git(repo, "ls-tree", "-r", "-z", "--name-only", tree).decode().split("\0"))   # ไม่ใช้ pathspec: "D:/…" = absolute บน Windows
    if in_tree & {r for r, _ in m1}: raise DataError("M1 อยู่ใน treeish (ต้องมาจาก repo Gloo)")
    files = {rel: hashlib.sha256(blobs[rel][2]).hexdigest() for rel in rels}
    for rel, src in m1:
        if not os.path.isfile(src): raise DataError(f"ไม่มีไฟล์ M1: {src}")
        files[rel] = sha_bytes(src)
    m = {"created": time.strftime("%Y-%m-%d %H:%M:%S"), "treeish": treeish, "tree": tree, "repo": os.path.realpath(repo),
         "blobs": {rel: blobs[rel][1] for rel in rels}, "files": files}
    if same_as:
        ref = json.load(io.open(same_as, encoding="utf-8"))["blobs"]
        diff = sorted((set(ref) ^ set(m["blobs"])) | {r for r in ref if r in m["blobs"] and ref[r] != m["blobs"][r]})
        if diff: raise DataError(f"blob id ≠ ชุดที่ smoke2 ผ่าน: {diff}")
    io.open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(m, indent=1, ensure_ascii=False))
    if tar_path:
        with tarfile.open(tar_path, "w") as t:
            for rel in rels:
                mode, _, body = blobs[rel]
                ti = tarfile.TarInfo("repo/" + rel); ti.size = len(body); ti.mode = 0o755 if mode == "100755" else 0o644
                ti.mtime = int(time.time()); ti.uid = ti.gid = 0; ti.uname = ti.gname = ""
                t.addfile(ti, io.BytesIO(body))
            for rel, src in m1:
                ti = t.gettarinfo(src, arcname="repo/" + rel); ti.mode = 0o644; ti.uid = ti.gid = 0; ti.uname = ti.gname = ""
                with open(src, "rb") as f: t.addfile(ti, f)
        with tarfile.open(tar_path) as t:                                   # ตรวจด้วย tarfile (ไม่ pipe) · bytes ราย member = manifest
            mem = {x.name: x for x in t.getmembers()}
            bad = [n for n in mem if "ad4_cert_out" in n or not n.startswith("repo/")]
            if bad: raise DataError(f"tar มีไฟล์ต้องห้าม/ผิดที่: {bad[:5]}")
            if len(t.getnames()) != len(files) or len(mem) != len(files): raise DataError(f"tar {len(t.getnames())} ไฟล์ ≠ manifest {len(files)}")
            for rel in files:
                if hashlib.sha256(t.extractfile(mem["repo/" + rel]).read()).hexdigest() != files[rel]: raise DataError(f"tar member {rel} ≠ manifest")
    print(f"[manifest] {len(files)} files (tree {tree[:12]} @ {treeish}) → {out}" + (f" · tar {tar_path}" if tar_path else ""))


def _openblas_libs():
    import numpy, scipy
    res = {}
    for pkg, mod, sfx in (("numpy", numpy, "64_"), ("scipy", scipy, "")):
        d = os.path.join(os.path.dirname(os.path.dirname(mod.__file__)), f"{pkg}.libs")
        libs = [p for p in glob.glob(os.path.join(d, "*openblas*")) if p.endswith((".so", ".dll")) or ".so." in p]
        if len(libs) != 1: raise VenueError(f"{pkg}.libs: ต้องเจอ openblas 1 ไฟล์ ได้ {libs}")
        L = ctypes.CDLL(libs[0]); r = {"lib": os.path.basename(libs[0])}
        for key, sym, rt in (("corename", "scipy_openblas_get_corename", ctypes.c_char_p),
                             ("threads", "scipy_openblas_get_num_threads", ctypes.c_int),
                             ("config", "scipy_openblas_get_config", ctypes.c_char_p)):
            try:
                f = getattr(L, sym + sfx)
            except AttributeError:
                raise VenueError(f"{pkg}: ไม่มี symbol {sym + sfx}")
            f.restype = rt; v = f()
            r[key] = v.decode() if isinstance(v, bytes) else v
        res[pkg] = r
    return res


def host_sha():
    """sha256 ของ HOST_FILES (แหล่งเดียว) ที่ REPO นี้ · "rel:sha" ต่อบรรทัด → sha256"""
    lines = [f"{rel}:{sha_bytes(os.path.join(REPO, rel))}" for rel in HOST_FILES]
    return hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()


def venue(strict_paths):
    """fingerprint + assert ค่าที่วัด · strict_paths=True บน .19 (python/numpy/scipy ต้องอยู่ใต้ trellis-test · isolated)"""
    import numpy, scipy
    from numpy._core._multiarray_umath import __cpu_features__ as F, __cpu_dispatch__ as D, __cpu_baseline__ as B
    from numpy.lib.introspect import opt_func_info
    import scipy.stats  # noqa: F401  โหลด openblas ตัวที่สอง (ad4_card.py:1017 ใช้ scipy.stats)
    found = [f for f in D if F[f]]
    exp_cur = opt_func_info(func_name="^exp$", signature="float64")["exp"]["dd"]["current"]
    ob = _openblas_libs()
    v = {"python": platform.python_version(), "executable": sys.executable, "isolated": sys.flags.isolated,
         "numpy": numpy.__version__, "scipy": scipy.__version__, "numpy_file": numpy.__file__, "scipy_file": scipy.__file__,
         "dispatch_found": found, "baseline": list(B), "exp_f64": exp_cur, "openblas": ob,
         "float_repr": sys.float_repr_style, "platform": platform.platform(), "machine": platform.machine(),
         "host_sha": host_sha()}                                            # runner code ที่ attempt นี้ใช้ (อยู่ใน FP_KEYS ของ host19_state)
    if hasattr(os, "confstr"):
        try: v["libc"] = os.confstr("CS_GNU_LIBC_VERSION")
        except (ValueError, OSError): v["libc"] = None
    for p in ("/lib/x86_64-linux-gnu/libm.so.6", "/lib/x86_64-linux-gnu/libc.so.6"):
        if os.path.exists(p): v["sha_" + os.path.basename(p)] = sha_bytes(os.path.realpath(p))
    errs = []
    if found != DISPATCH_ON: errs.append(f"dispatch {found} ≠ {DISPATCH_ON}")
    if list(B) != BASELINE: errs.append(f"baseline {list(B)}")
    if any(F[f] for f in D if f.startswith("AVX512")): errs.append("AVX512 เปิดอยู่")
    if exp_cur != "AVX2": errs.append(f"exp f64 current={exp_cur}")
    for pkg, r in ob.items():
        if r["corename"] != "Haswell": errs.append(f"{pkg} corename={r['corename']}")
        if r["threads"] != 1: errs.append(f"{pkg} threads={r['threads']}")
    if (numpy.__version__, scipy.__version__) != ("2.3.2", "1.17.1"): errs.append(f"versions {numpy.__version__}/{scipy.__version__}")
    if sys.version_info[:3] != (3, 11, 7): errs.append(f"python {platform.python_version()}")
    if sys.float_repr_style != "short": errs.append("float_repr_style")
    if strict_paths:
        import ssl, _hashlib, zlib  # noqa: F401
        root = os.path.realpath(os.path.join(REPO, "..", ".."))           # trellis-test/<run>/repo → trellis-test
        for k in ("executable", "numpy_file", "scipy_file"):
            if not os.path.realpath(v[k]).startswith(root + os.sep): errs.append(f"{k} อยู่นอก {root}: {v[k]}")
        if sys.flags.isolated != 1: errs.append("ไม่ได้รันด้วย -I")
    if errs: raise VenueError("; ".join(errs))
    return v


def build_ad():
    from ad4_card import AD4, AD1                                          # ad4_card.py:1121-1122 สร้าง ad แบบนี้
    ad = AD4.__new__(AD4); AD1.__init__(ad)
    return ad


def data_identity(ad):
    from ad4_card import header_fields, _sha_lf
    hf = header_fields(ad, "preflight", "preflight", None)
    keep = ("closure_sha", "SPEC_SHA", "card_sha_runtime", "n", "NF", "Nemb", "fold_sizes", "prefix_sizes", "X_sha", "dayix_sha")
    ident = {k: hf[k] for k in keep}
    ident["h0_sha_lf"] = {f: _sha_lf(os.path.join(REPO, "Research", "h0", f)) for f in H0}
    return ident


def mode_emit(out):
    v = venue(strict_paths=False)
    ad = build_ad()
    import numpy as np
    xnpy = os.path.splitext(out)[0] + "_X.npy"                             # ใช้ diagnose ulp ต่อคอลัมน์เมื่อ X_sha ไม่ตรง
    np.save(xnpy, ad.X)
    ref = {"created": time.strftime("%Y-%m-%d %H:%M:%S"), "venue_emit": v, "identity": data_identity(ad),
           "X_npy": os.path.basename(xnpy), "X_npy_sha": sha_bytes(xnpy)}
    io.open(out, "w", encoding="utf-8", newline="\n").write(json.dumps(ref, indent=1, ensure_ascii=False))
    print(f"[emit] reference → {out} · X_sha {ref['identity']['X_sha'][:12]}… · closure {ref['identity']['closure_sha'][:12]}…")


def x_ulp_report(ad, ref_path, ref):
    import numpy as np
    p = os.path.join(os.path.dirname(os.path.abspath(ref_path)), ref["X_npy"])
    if sha_bytes(p) != ref["X_npy_sha"]: return "X_npy sha ไม่ตรง"
    Xr = np.load(p)
    if Xr.shape != ad.X.shape: return f"shape {Xr.shape} ≠ {ad.X.shape}"
    a, b = Xr.astype(float), ad.X.astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.abs(a - b) / np.spacing(np.maximum(np.abs(a), np.abs(b)))
    d = np.where((a == b), 0.0, d)
    return "max ulp ต่อคอลัมน์: " + str([float(x) for x in np.nanmax(d, axis=0)])


def mode_check(ref_path, manifest_path):
    ref = json.load(io.open(ref_path, encoding="utf-8"))
    man = json.load(io.open(manifest_path, encoding="utf-8"))
    if os.path.realpath(os.getcwd()) != os.path.realpath(REPO): raise VenueError(f"cwd {os.getcwd()} ≠ repo {REPO}")
    v = venue(strict_paths=True)
    print("[venue] " + json.dumps(v, ensure_ascii=False))
    data_dir = os.path.realpath(DATA_REL)
    if not data_dir.startswith(os.path.realpath(REPO) + os.sep): raise VenueError(f"DATA {data_dir} อยู่นอก repo")
    m1 = sorted(os.listdir(data_dir))
    if m1 != [f"XAUUSD_M1_{y}.csv" for y in YEARS]: raise DataError(f"M1 ไม่ตรง 2011-2020: {m1}")
    if os.path.exists(os.path.join(HERE, "ad4_cert_out_v2")): raise VenueError("มี Scripts/ad4_cert_out_v2 อยู่แล้ว (state ไม่สะอาด)")
    bad = []
    for rel, s in man["files"].items():
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p) or sha_bytes(p) != s: bad.append(rel)
    if bad: raise DataError(f"manifest ไม่ตรง: {bad}")
    ad = build_ad()
    ident = data_identity(ad)
    diff = {k: (ref["identity"][k], ident[k]) for k in ref["identity"] if ref["identity"][k] != ident[k]}
    if diff:
        extra = (" · " + x_ulp_report(ad, ref_path, ref)) if "X_sha" in diff else ""
        raise DataError("identity ไม่ตรง: " + json.dumps({k: [str(a)[:24], str(b)[:24]] for k, (a, b) in diff.items()}, ensure_ascii=False) + extra)
    print(f"[preflight] PASS · manifest {len(man['files'])} files · X_sha {ident['X_sha'][:12]}… · closure {ident['closure_sha'][:12]}…")


def mode_venue(strict, out):
    v = venue(strict_paths=strict)
    if not out: print(json.dumps(v, ensure_ascii=False)); return
    if not os.path.isabs(out): raise VenueError(f"--out ต้องเป็น absolute path: {out}")
    v = dict(v, run_id=os.environ.get("TRELLIS_RUN_ID"), pid=os.getpid())   # supervisor ตรวจ run_id/pid ตรงกับ child ที่ spawn
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f: f.write(json.dumps(v, ensure_ascii=False)); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, out)
    print(f"[venue] → {out}")


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="host19_preflight")
    sp = ap.add_subparsers(dest="mode", required=True)
    m = sp.add_parser("manifest"); m.add_argument("--out", required=True); m.add_argument("--treeish", required=True)
    m.add_argument("--repo"); m.add_argument("--tar"); m.add_argument("--same-blobs-as")
    e = sp.add_parser("emit"); e.add_argument("--out", required=True)
    c = sp.add_parser("check"); c.add_argument("--ref", required=True); c.add_argument("--manifest", required=True)
    v = sp.add_parser("venue"); v.add_argument("--strict", action="store_true"); v.add_argument("--out")
    return ap.parse_args(argv[1:])


def main(argv):
    try:
        a = parse_args(argv)
    except SystemExit:
        return EXIT_TOOL
    try:
        if a.mode == "manifest": mode_manifest(a.out, a.treeish, a.repo, a.tar, a.same_blobs_as)
        elif a.mode == "emit": mode_emit(a.out)
        elif a.mode == "check": mode_check(a.ref, a.manifest)
        elif a.mode == "venue": mode_venue(a.strict, a.out)
    except VenueError as e:
        print(f"[preflight] VENUE FAIL: {e}"); return EXIT_VENUE
    except DataError as e:
        print(f"[preflight] DATA FAIL: {e}"); return EXIT_DATA
    except Exception:
        traceback.print_exc(); return EXIT_TOOL
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
