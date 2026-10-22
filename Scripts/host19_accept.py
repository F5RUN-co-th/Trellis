# -*- coding: utf-8 -*-
"""host19_accept — จัดสถานะของ series บน .19 (regress/RG14 + post-B pilot/cert_v2) ตามตาราง state ที่ลงทะเบียนไว้ (Progress Log 2026-10-20 · spec §13)
รันบน .19 ด้วย `nice -n 19 python/bin/python3.11 -I -B` (CLAUDE.md §สนามรัน · runner ไม่มีโหมด accept)

usage
  python Scripts/host19_accept.py <run_dir> [--b-start "YYYY-mm-dd HH:MM:SS" (UTC)] [--local-ck <checkpoint 22 world ของ Windows>]
  b_start default = ts (UTC) ของ start line แรกใน run_dir (B ใช้ RUNDIR สด · receipt ต้องเกิดหลังจุดนี้) · --b-start = override (UTC เท่านั้น)
  python Scripts/host19_accept.py --selftest

<run_dir> = trellis-test/run_<S1short>/ บน .19 หรือ archive ที่ track แล้ว (Scripts/ad4_cert_out_v2/host19_<S1short>/ · layout เดียวกัน: run/ + repo/Scripts/ad4_cert_out_v2/)
script นี้เป็นเจ้าของ verdict ของ series และตัวเลขเทียบ 22 world (report ไม่ใช่ gate) · classifier/judge/grammar = host19_state.py (ที่เดียว)
gate record = note เท่านั้น (ไม่มี workload รัน) · ตาราง (6)/(8) ระหว่าง series = operator จากป้ายราย attempt ที่ host19_run.py พิมพ์

exit: 0 valid+RG14 PASS (+ post-B ทุก key OK ถ้ามี) · 10 valid+RG14 raise · 3 RG14 FAIL-loud instrument · 4 regress ล้มบน .19 (blocker วิน) ·
      5 operator abort · 6 invalid-infra (รันซ้ำได้ 1 ครั้ง) · 7 run dir ใหม่ (fingerprint ไม่ตรง / ไม่มีบรรทัดสด) ·
      8 B-part PASS แต่ post-B (pilot/cert_v2) มี key ไม่ผ่าน (D-6: หยุดรายงานวิน) · 1 invalid-อื่น · 2 tool-error
"""
import os, sys, re, io, json, tempfile, shutil, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import host19_state as S

ST = {"PASS": 0, "RAISE": 10, "FAILLOUD": 3, "REGRESS_FAIL": 4, "ABORT": 5, "INFRA": 6, "NEWDIR": 7, "POST_FAIL": 8, "INVALID": 1, "TOOL": 2}
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def resolve_b_start(run_dir, override=None):
    """→ (b_start, ที่มา) · override ต้องตรงรูป TS_RE (UTC) · default = ts ของ start line แรก (ตาม seq) · ไม่มี LOG → ToolError"""
    if override is not None:
        if not TS_RE.match(override): raise S.ToolError(f"--b-start ต้องเป็น 'YYYY-mm-dd HH:MM:SS' (UTC): {override!r}")
        return override, "override"
    atts = S.read_attempts(run_dir)
    if not atts: raise S.ToolError("ไม่มี LOG ให้ derive b_start")
    return atts[0]["ts"], "derived"


def report_22(ck_path, local_ck_path, rg14_tags):
    import numpy as np
    ck = json.load(io.open(ck_path, encoding="utf-8")); lo = json.load(io.open(local_ck_path, encoding="utf-8"))
    rows, int_bad = [], 0
    for t in sorted(lo, key=lambda t: rg14_tags.index(t)):
        a, b = lo[t], ck[t]
        ib = [k for k in ("nd_alt2", "nd_v5local", "atom_alt2", "atom_v5local") if a[k] != b[k]]
        int_bad += bool(ib)
        du = []
        for k in ("sd_alt2", "sd_v5local", "q95_alt2", "q95_v5local"):
            x, y = float(a[k]), float(b[k])
            if x == y: du.append(0.0)
            elif x == 0.0 or y == 0.0: du.append(float("inf"))
            else: du.append(abs(x - y) / float(np.spacing(max(abs(x), abs(y)))))
        rows.append((t, ib, max(du)))
    print(f"[report 22-world · ไม่ใช่ gate] world ที่ int ไม่ตรง: {int_bad}/{len(rows)} · max d_ulp (sd/q95) ต่อ world: " +
          ", ".join(f"{t[-3:]}={d:.0f}" for t, _, d in rows))
    print("  ตีความ: .19 ต่าง Windows = residual ข้าม venue · ห้ามอ้างเทียบเท่าถ้า int ไม่ตรง")


def main(argv):
    if "--selftest" in argv: return selftest()
    if len(argv) < 2 or argv[1].startswith("--"): print(__doc__); return ST["TOOL"]
    try:
        from ad4_card import RG14_TAGS, SPEC_SHA, closure_sha
        run_dir = argv[1]
        b_start, src = resolve_b_start(run_dir, argv[argv.index("--b-start") + 1] if "--b-start" in argv else None)
        print(f"[accept] b_start={b_start} (UTC · {src})")
        state, notes = S.judge(run_dir, b_start, list(RG14_TAGS), SPEC_SHA, closure_sha())
        for n in notes: print("  " + n)
        print(f"[accept] STATE = {state}")
        if "--local-ck" in argv and state in ("PASS", "RAISE"):
            report_22(os.path.join(run_dir, "repo", "Scripts", "ad4_cert_out_v2", "rg14", "checkpoint_v6.json"),
                      argv[argv.index("--local-ck") + 1], list(RG14_TAGS))
        return ST[state]
    except Exception:
        traceback.print_exc(); return ST["TOOL"]


# ============================ selftest (positive control + mutation ต่อ predicate + negative control) ============================
VENUE = {"python": "3.11.7", "executable": "/x/python3.11", "numpy": "2.3.2", "scipy": "1.17.1", "dispatch_found": ["AVX2"],
         "baseline": ["SSE"], "exp_f64": "AVX2", "openblas": {"numpy": {"corename": "Haswell"}}, "libc": "glibc 2.39",
         "sha_libm.so.6": "aa", "sha_libc.so.6": "bb", "machine": "x86_64", "host_sha": "h0"}


def _log(root, name, mode, seq, body, rc=0, v=VENUE, oom=(0, 0), cause="child-exit", viol=(), run_id=None, end=True, lf=True,
         note=(), left=(), ts="2026-10-21 01:00:00", boot="b0", bt=None, args=None):
    """LOG format r13/r14 (fmt_start/fmt_end ของ host19_state) · end=False → ไม่มี end line · lf=False → ไม่มี LF ปิด · bt default = seq·1000"""
    rid = run_id or f"u{seq}"
    L = [S.fmt_start(mode, 1, ts, rid, oom[0], seq, 1000 + seq, boot, 4242, 99, seq * 1000 if bt is None else bt, args)]
    if v is not None: L.append("[venue] " + json.dumps(v))
    L += body + ["\tExit status: %d" % (rc if rc < 128 else 0)]
    if end: L.append(S.fmt_end(rc, oom[1], seq, cause, set(viol), left, note))
    io.open(os.path.join(root, "run", name), "w", encoding="utf-8", newline="\n").write("\n".join(L) + ("\n" if lf else ""))
    return rid


CHUNK_ROOT_19 = "/home/dev-ai/trellis-test/run_x/repo/Scripts/ad4_cert_out_v2/"   # path ที่ ad4_card.py:578 พิมพ์บน .19 (absolute)


def _post(root, name, seq, key, kind="ok", v=VENUE):
    """post-B attempt (r14 · args=key) · kind: ok · noline · nofile · nosuffix · mismatch · infra · fail · ไฟล์ chunk สร้างใต้ <root>/repo/... (= re-root)"""
    var, w, c, k0, k1 = S.parse_key(key)
    fname = f"{w}_{k0}_{k1}.csv" if c is None else f"{w}_c{c}_{k0}_{k1}.csv"     # ชื่อของ fixture เท่านั้น · judge ไม่สร้างชื่อเอง (อ่าน path จากบรรทัด)
    shown = (CHUNK_ROOT_19 if kind != "nosuffix" else "/tmp/elsewhere/") + f"{var}/{fname}"
    m1 = k1 - 1 if kind != "mismatch" else k1
    line = f"[cert_v2] {var}/{w} cell={c} draws {k0}..{m1} → {shown} · 109.0 s/draw"
    body, kw = ([] if kind == "noline" else [line, line] if kind == "twolines" else [line]), {}
    if kind == "infra": body, kw = [], dict(rc=137, oom=(0, 1))
    if kind == "fail": body, kw = ["Traceback (most recent call last):", "AssertionError: chunk มีอยู่แล้ว"], dict(rc=1)
    if kind == "abort": body, kw = [f"{S.ABORT_LINE}erfx ต้องใช้เครื่อง ts=x ns=1"], dict(rc=143, cause="abort")   # honored = บรรทัด + .taken (ด้านล่าง)
    if kind in ("ok", "noline", "mismatch", "nosuffix", "twolines"):
        d = os.path.join(root, "repo", "Scripts", "ad4_cert_out_v2", var); os.makedirs(d, exist_ok=True)
        io.open(os.path.join(d, fname), "w", encoding="utf-8", newline="\n").write("# x\n# schema: k\n")
    mode = "pilot" if key == S.PILOT_KEY and name.startswith("pilot") else "cert_v2"
    rid = _log(root, name, mode, seq, body, v=v, args=key, **kw)
    if kind == "abort": io.open(os.path.join(root, "run", f"abort.{rid}.5.taken"), "w").write("{}")


POST = {                                                                    # mut → [(ชื่อ LOG, seq, key, kind, venue)]
    "post_ok": [("pilot.1.log", 10, S.PILOT_KEY, "ok", VENUE)],
    "post_noline": [("pilot.1.log", 10, S.PILOT_KEY, "noline", VENUE)],
    "post_nofile": [("pilot.1.log", 10, S.PILOT_KEY, "nofile", VENUE)],
    "post_fp": [("pilot.1.log", 10, S.PILOT_KEY, "ok", dict(VENUE, host_sha="h2"))],
    "post_infra_retry": [("pilot.1.log", 10, S.PILOT_KEY, "infra", VENUE), ("pilot.2.log", 11, S.PILOT_KEY, "ok", VENUE)],
    "post_infra2": [("pilot.1.log", 10, S.PILOT_KEY, "infra", VENUE), ("pilot.2.log", 11, S.PILOT_KEY, "infra", VENUE)],
    "post_fail_last": [("pilot.1.log", 10, S.PILOT_KEY, "ok", VENUE), ("cert_v2.1.log", 11, "c1full/h0cal/-/0/10", "fail", VENUE)],
    "post_cert4": [("pilot.1.log", 10, S.PILOT_KEY, "ok", VENUE), ("cert_v2.1.log", 11, "c1full/h0cal/-/0/10", "ok", VENUE)],
    "post_cert5": [("pilot.1.log", 10, S.PILOT_KEY, "ok", VENUE), ("cert_v2.1.log", 11, "c1full/flip/3/0/10", "ok", VENUE)],
    "post_AB": [("pilot.1.log", 10, S.PILOT_KEY, "ok", VENUE), ("cert_v2.1.log", 11, "c1full/h0cal/-/0/10", "infra", VENUE),
                ("cert_v2.2.log", 12, "c1full/h0cal/-/10/20", "ok", VENUE)],
    "post_AA": [("pilot.1.log", 10, S.PILOT_KEY, "ok", VENUE), ("cert_v2.1.log", 11, "c1full/h0cal/-/0/10", "infra", VENUE),
                ("cert_v2.2.log", 12, "c1full/h0cal/-/0/10", "ok", VENUE)],
    "post_nosuffix": [("pilot.1.log", 10, S.PILOT_KEY, "nosuffix", VENUE)],
    "post_mismatch": [("pilot.1.log", 10, S.PILOT_KEY, "mismatch", VENUE)],
    "post_before": [("pilot.1.log", 5, S.PILOT_KEY, "ok", VENUE)],
    # C-5 (card :144 pilot ก่อน certify) · C-2 (บรรทัดสรุป 1 บรรทัดพอดี)
    "post_nopilot": [("cert_v2.1.log", 10, "c1full/h0cal/-/0/10", "ok", VENUE)],
    "post_cert_first": [("cert_v2.1.log", 10, "c1full/h0cal/-/0/10", "ok", VENUE), ("pilot.1.log", 11, S.PILOT_KEY, "ok", VENUE)],
    "post_pilot_infra": [("pilot.1.log", 10, S.PILOT_KEY, "infra", VENUE), ("cert_v2.1.log", 11, "c1full/h0cal/-/0/10", "ok", VENUE)],
    "post_pilot_retry_cert": [("pilot.1.log", 10, S.PILOT_KEY, "infra", VENUE), ("pilot.2.log", 11, S.PILOT_KEY, "ok", VENUE),
                              ("cert_v2.1.log", 12, "c1full/h0cal/-/0/10", "ok", VENUE)],
    "post_twolines": [("pilot.1.log", 10, S.PILOT_KEY, "twolines", VENUE)],
    # AB-1: honored ABORT รันซ้ำ key เดิมได้ 1 ครั้ง (RETRYABLE)
    "post_abort_retry": [("pilot.1.log", 10, S.PILOT_KEY, "abort", VENUE), ("pilot.2.log", 11, S.PILOT_KEY, "ok", VENUE),
                         ("cert_v2.1.log", 12, "c1full/h0cal/-/0/10", "ok", VENUE)],
    "post_abort_only": [("pilot.1.log", 10, S.PILOT_KEY, "ok", VENUE), ("cert_v2.1.log", 11, "c1full/h0cal/-/0/10", "abort", VENUE)],
}


def _fixture(root, tags, spec, cl, mut=None):
    os.makedirs(os.path.join(root, "run")); cd = os.path.join(root, "repo", "Scripts", "ad4_cert_out_v2", "rg14"); os.makedirs(cd)
    ad4 = f"[AD4] v2 · SPEC_SHA {spec[:12]}… · card_sha_runtime {spec[:12]}… · closure {cl[:12]}… · threads=1"
    ck, live = {}, []
    for i, t in enumerate(tags):
        e = {"dsd": 0.001 * (i + 1) + 1e-9, "dq95": -0.002 * (i + 1), "sd_alt2": 0.1 + i, "sd_v5local": 0.1, "q95_alt2": 0.2, "q95_v5local": 0.2,
             "nd_alt2": 99, "nd_v5local": 90 - i % 3, "atom_alt2": 1, "atom_v5local": 2, "closure_sha": cl}
        ck[t] = e
        live.append(f"  [RG14] world {i+1}/50 Δsd={e['dsd']:+.5f} Δq95={e['dq95']:+.5f} · distinct {e['nd_alt2']}/{e['nd_v5local']} atom {e['atom_alt2']}/{e['atom_v5local']} · 10s (checkpoint {i+1}/50)")
    v2 = dict(VENUE, libc="glibc 2.40") if mut in ("fp", "J1", "J2") else dict(VENUE, host_sha="h1") if mut == "host_sha" else VENUE
    if mut not in ("J3", "J6"):
        _log(root, "preflight.1.log", "preflight", 1, ["[preflight] PASS · manifest"], v=None if mut == "J4" else VENUE)
    if mut == "J6": return
    if mut == "J7":
        json.dump(ck, io.open(os.path.join(cd, "checkpoint_v6.json"), "w", encoding="utf-8")); return
    if mut in ("regress_fail", "J1", "J5"):
        _log(root, "regress.1.log", "regress", 2, [ad4, "Traceback (most recent call last):", "AssertionError: RG7 legacy k=0: p 0.123 ≠ 0.124"], rc=1)
        if mut != "regress_fail":
            _log(root, "regress.2.log", "regress", 3, [ad4, "[regress] RG1-RG13 · RG15 PASS · RG14 SKIPPED"])
    else:
        _log(root, "regress.1.log", "regress", 2, [ad4, "[regress] RG1-RG13 · RG15 PASS · RG14 SKIPPED"])
    if mut == "drop_live": live = live[:-1]
    if mut == "live_val": live[3] = re.sub(r"Δsd=[+-]\d+\.\d{5}", "Δsd=+9.99999", live[3])
    if mut == "resumed_only": live = [re.sub(r" · distinct.*$", " (checkpoint)", l) for l in live]
    body = [ad4] + live + ["[RG14] Δsd: mean=+0.000001", "[RG14] PASS (ไม่ raise) · point flip = report เท่านั้น",
                           f"[receipt] rg14 ✓ · closure {cl[:12]}… · SPEC_SHA {spec[:12]}… · regress=True rg14=True"]
    kw = {}
    if mut == "raise": body = [ad4] + live + ["Traceback (most recent call last):", "AssertionError: RG14 raise: upper t-CI ของ paired mean < 0"]; kw["rc"] = 1
    if mut == "raise_leftover": body = [ad4] + live + ["Traceback (most recent call last):", "AssertionError: RG14 raise: upper t-CI ของ paired mean < 0"]; kw.update(rc=1, viol=("leftover",))
    if mut == "collapse": body = [ad4] + live[:3] + ["Traceback (most recent call last):", "AssertionError: RG14 ad4_rg14_w53: แขน Alt-2 collapse (n_distinct=1) — FAIL-loud"]; kw["rc"] = 1
    if mut in ("oom", "J2", "J5"): body = [ad4] + live[:3]; kw.update(rc=137, oom=(0, 1))
    if mut == "memerr": body = [ad4] + live[:3] + ["Traceback (most recent call last):", "MemoryError"]; kw["rc"] = 1
    if mut in ("abort", "abort_notaken", "abort_killfail"):
        body = [ad4] + live[:3] + [f"{S.ABORT_LINE}erfx ต้องใช้เครื่อง ts=x ns=1"]; kw.update(rc=143, cause="abort")
        if mut == "abort_killfail": kw.update(viol=("killfail",), left=((77, 7),))
    if mut == "kill_nooom": body = [ad4] + live[:3]; kw["rc"] = 137
    if mut == "deadline_oom": body = [ad4] + live[:3]; kw.update(rc=137, oom=(0, 1), cause="deadline-wall")
    if mut == "spawnfail": body = []; kw.update(rc=77, cause="spawn-fail")
    if mut == "note_signal": kw["note"] = ("sig15-after-exit",)
    if mut == "internal_after": kw["viol"] = ("internal",)
    if mut in ("noend", "noend_orphan"): kw["end"] = False
    if mut == "nolf": kw["lf"] = False
    if mut == "card": body[0] = body[0].replace(f"card_sha_runtime {spec[:12]}", "card_sha_runtime 000000000000")
    if mut in ("J1", "J3", "J4"): pass                                       # rg14 PASS ปกติ
    rid = _log(root, "rg14.1.log", "rg14", 9, body, v=v2, **kw)
    if mut == "J5": os.remove(os.path.join(root, "run", "regress.2.log"))   # J5 = regress FAIL (ไม่ใช่ตัวท้าย) + ล่าสุด INFRA fp เดียวกัน
    if mut == "abort": io.open(os.path.join(root, "run", f"abort.{rid}.5.taken"), "w").write("{}")
    if mut == "abort_killfail": io.open(os.path.join(root, "run", f"abort.{rid}.5.taken"), "w").write("{}")
    if mut in ("orphan_after_end", "noend_orphan"): S.write_json_atomic(os.path.join(root, "run", f"orphan.{rid}.7.rec"), {"id": rid})
    if mut == "c3_after_end":
        S.write_json_atomic(os.path.join(root, "run", "gate.00000010.8.77.rec"), {"rc": 77, "cause": "orphan-env", "target_run_ids": [rid], "ns0": 8})
    if mut == "gate75":
        for i in (1, 2): S.write_json_atomic(os.path.join(root, "run", f"gate.seen00000009.{i}.75.rec"), {"rc": 75, "cause": "lock-busy", "ns0": i})
    if mut == "seq_order":                                                  # ลำดับ seq สวนลำดับชื่อไฟล์: PASS (seq 9) ชื่อ rg14.1 · OOM (seq 10) ชื่อ rg14.0
        _log(root, "rg14.0.log", "rg14", 10, [ad4] + live[:3], rc=137, oom=(0, 1), run_id="uoom")   # ล่าสุดตาม seq = INFRA
    if mut == "dup_seq": _log(root, "rg14.0.log", "rg14", 9, [ad4] + live[:3], rc=137, oom=(0, 1), run_id="udup")
    if mut == "bt_rev": _log(root, "rg14.0.log", "rg14", 10, [ad4] + live[:3], rc=137, oom=(0, 1), run_id="ubt", bt=1)
    if mut == "bt_rev_xboot": _log(root, "rg14.0.log", "rg14", 10, [ad4] + live[:3], rc=137, oom=(0, 1), run_id="ubt", bt=1, boot="b1")
    if mut == "ck_extra": ck["bogus"] = dict(ck[tags[0]])
    if mut == "ck_closure": ck[tags[5]] = dict(ck[tags[5]], closure_sha="deadbeef")
    json.dump(ck, io.open(os.path.join(cd, "checkpoint_v6.json"), "w", encoding="utf-8"))
    rec = {"closure_sha": cl, "SPEC_SHA": spec, "regress": True, "rg14": mut not in ("raise", "raise_leftover"),
           "regress_at": "2026-10-21 01:30:00", "rg14_at": "2026-10-21 03:00:00"}
    if mut == "stale_receipt": rec["regress_at"] = "2026-09-24 15:54:00"
    json.dump(rec, io.open(os.path.join(root, "repo", "Scripts", "ad4_cert_out_v2", "regress_receipt.json"), "w", encoding="utf-8"))
    for name, seq, key, kind, v in POST.get(mut, ()): _post(root, name, seq, key, kind, v)


def _judge_case(tags, spec, cl, mut):
    d = tempfile.mkdtemp(prefix="h19acc_")
    try:
        _fixture(d, tags, spec, cl, mut)
        try:
            return S.judge(d, "2026-10-21 00:00:00", tags, spec, cl)
        except S.ToolError as e:
            return "TOOL", [str(e)]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _unit_checks():
    """END_RE / exit_code / valid_rundir / test_env / ToolError / attempt_label (ไม่ต้องใช้ ad4_card)"""
    out = []
    def ok(name, cond): out.append((name, bool(cond)))
    e = S.parse_end(S.fmt_end(0, 0, 3, "child-exit", set()))
    ok("END clean", e and e["viol"] == set() and e["left"] == [] and e["note"] == [])
    e = S.parse_end(S.fmt_end(0, 0, 3, "child-exit", set(), note=("sig15-after-exit",)))
    ok("END note=", e and e["note"] == ["sig15-after-exit"])
    e = S.parse_end(S.fmt_end(77, 0, 3, "signal", {"killfail"}, left=((12, 34),)))
    ok("END left=", e and e["left"] == [(12, 34)] and e["viol"] == {"killfail"})
    e = S.parse_end(S.fmt_end(77, 0, 3, "signal", {"killfail", "internal"}, left=((12, 34), (5, 6)), note=("x",)))
    ok("END left+note", e and e["left"] == [(12, 34), (5, 6)] and e["note"] == ["x"])
    ok("END ผิดลำดับ suffix", S.parse_end("[run] end rc=0 oom_kill=0 seq=3 cause=child-exit viol=- note=x left=1:2") is None)
    ok("END format เก่า", S.parse_end("[run] end rc=0 oom_kill=0") is None)
    try: S.parse_end("[run] end rc=0 oom_kill=0 seq=3 cause=bogus viol=-"); ok("END cause นอก enum → ToolError", False)
    except S.ToolError: ok("END cause นอก enum → ToolError", True)
    ok("exit log clean", S.exit_code("log", {"rc": 0, "cause": "child-exit", "viol": set()}) == 0)
    ok("exit log rc=1 child-exit", S.exit_code("log", {"rc": 1, "cause": "child-exit", "viol": set()}) == 1)
    ok("exit log leftover → 77", S.exit_code("log", {"rc": 0, "cause": "child-exit", "viol": {"leftover"}}) == 77)
    ok("exit log signal → 77", S.exit_code("log", {"rc": 143, "cause": "signal", "viol": set()}) == 77)
    ok("exit gate 75", S.exit_code("gate", {"rc": 75}) == 75)
    ok("test_env t-*", S.test_env_violation("t-exit0", {"TRELLIS_TEST_KILLFAIL": "1"}) == [])
    ok("test_env real mode", S.test_env_violation("rg14", {"TRELLIS_TEST_KILLFAIL": "1"}) == ["TRELLIS_TEST_KILLFAIL"])
    # r14: key · post_deadline · grammar (r13 อ่านได้ · args เฉพาะ POST_MODES)
    ok("key cert_v2 4 args", S.key_from_args(["c1full", "h0cal", "0", "10"]) == "c1full/h0cal/-/0/10")
    ok("key cert_v2 5 args", S.key_from_args(["c1full", "flip", "3", "0", "10"]) == "c1full/flip/3/0/10")
    for bad_args in (["c1full", "h0cal", "10", "0"], ["c1full", "h0cal", "x", "1"], ["c1 full", "h0cal", "0", "1"], ["c1full", "h0cal", "0"], ["C1", "h0cal", "0", "1"]):
        try: S.key_from_args(bad_args); ok(f"key รูปผิด {bad_args} → ValueError", False)
        except ValueError: ok(f"key รูปผิด {bad_args} → ValueError", True)
    ok("post_deadline pilot = (1800, 3600+30·600)", S.post_deadline(S.PILOT_KEY) == (1800, 21600))
    ok("post_deadline cert 0..10", S.post_deadline("c1full/h0cal/-/0/10") == (1800, 9600))
    # key_ok / pilot_ok = กติกาเดียวที่ judge และ runner gate เรียก (V-2)
    ok("key_ok OK", S.key_ok(["OK"])); ok("key_ok INFRA→OK", S.key_ok(["INFRA", "OK"]))
    ok("key_ok INFRA→INFRA ✗", not S.key_ok(["INFRA", "INFRA"])); ok("key_ok INVALID→OK ✗", not S.key_ok(["INVALID", "OK"]))
    ok("key_ok INFRA→INFRA→OK ✗", not S.key_ok(["INFRA", "INFRA", "OK"])); ok("key_ok [] ✗", not S.key_ok([]))
    ok("key_ok ABORT→OK", S.key_ok(["ABORT", "OK"])); ok("key_ok ABORT→INFRA→OK ✗", not S.key_ok(["ABORT", "INFRA", "OK"]))
    P = lambda seq, cls, key=S.PILOT_KEY: {"mode": "pilot" if key == S.PILOT_KEY else "cert_v2", "args": key, "seq": seq, "cls": cls}
    ok("pilot_ok OK → seq", S.pilot_ok([P(10, "OK")]) == 10)
    ok("pilot_ok INFRA→OK → seq ตัวท้าย", S.pilot_ok([P(10, "INFRA"), P(11, "OK")]) == 11)
    ok("pilot_ok INFRA → None", S.pilot_ok([P(10, "INFRA")]) is None)
    ok("pilot_ok ไม่มี pilot (cert เท่านั้น) → None", S.pilot_ok([P(10, "OK", "c1full/h0cal/-/0/10")]) is None)
    # may_spawn = gate คู่ของ judge (W-1..W-3 · k ทับ)
    A = lambda mode, seq, cls, key=None: {"mode": mode, "args": key, "seq": seq, "cls": cls}
    B3 = [A("preflight", 1, "OK"), A("regress", 2, "OK"), A("rg14", 3, "PASS")]
    PL = A("pilot", 4, "OK", S.PILOT_KEY); CK = "c1full/h0cal/-/0/10"
    ms = lambda mode, key, atts: S.may_spawn(mode, key, atts)[0]
    ok("may_spawn B ก่อน post", ms("rg14", None, B3)); ok("may_spawn B หลัง post ✗", not ms("rg14", None, B3 + [PL]))
    ok("may_spawn preflight หลัง post ✗", not ms("preflight", None, B3 + [PL]))
    ok("may_spawn pilot ครั้งแรก", ms("pilot", S.PILOT_KEY, B3)); ok("may_spawn pilot ซ้ำหลัง OK ✗", not ms("pilot", S.PILOT_KEY, B3 + [PL]))
    ok("may_spawn pilot หลัง INFRA", ms("pilot", S.PILOT_KEY, B3 + [A("pilot", 4, "INFRA", S.PILOT_KEY)]))
    ok("may_spawn pilot หลัง INVALID ✗", not ms("pilot", S.PILOT_KEY, B3 + [A("pilot", 4, "INVALID", S.PILOT_KEY)]))
    ok("may_spawn pilot หลัง INFRA×2 ✗", not ms("pilot", S.PILOT_KEY, B3 + [A("pilot", 4, "INFRA", S.PILOT_KEY), A("pilot", 5, "INFRA", S.PILOT_KEY)]))
    ok("may_spawn pilot หลัง ABORT", ms("pilot", S.PILOT_KEY, B3 + [A("pilot", 4, "ABORT", S.PILOT_KEY)]))
    for h in (["ABORT", "ABORT"], ["INFRA", "ABORT"], ["ABORT", "INVALID"]):
        ok(f"may_spawn pilot หลัง {h} ✗", not ms("pilot", S.PILOT_KEY, B3 + [A("pilot", 4 + i, c, S.PILOT_KEY) for i, c in enumerate(h)]))
    ok("may_spawn cert ไม่มี pilot ✗", not ms("cert_v2", CK, B3)); ok("may_spawn cert หลัง pilot OK", ms("cert_v2", CK, B3 + [PL]))
    ok("may_spawn cert h0pilot ✗", not ms("cert_v2", "c1full/h0pilot/-/30/40", B3 + [PL]))
    ok("may_spawn cert key ซ้ำหลัง OK ✗", not ms("cert_v2", CK, B3 + [PL, A("cert_v2", 5, "OK", CK)]))
    ok("may_spawn cert ทับ [5,15) ✗", not ms("cert_v2", "c1full/h0cal/-/5/15", B3 + [PL, A("cert_v2", 5, "OK", CK)]))
    ok("may_spawn cert ติดกัน [10,20)", ms("cert_v2", "c1full/h0cal/-/10/20", B3 + [PL, A("cert_v2", 5, "OK", CK)]))
    ok("may_spawn cert ทับกับ INFRA key อื่น ✗", not ms("cert_v2", "c1full/h0cal/-/5/15", B3 + [PL, A("cert_v2", 5, "INFRA", CK)]))
    ok("may_spawn cert world/cell อื่นไม่ถือว่าทับ", ms("cert_v2", "c1full/flip/3/0/10", B3 + [PL, A("cert_v2", 5, "OK", CK)]))
    ok("may_spawn cert flip cell ต่างกันไม่ทับ", ms("cert_v2", "c1full/flip/4/0/10", B3 + [PL, A("cert_v2", 5, "OK", "c1full/flip/3/0/10")]))
    ok("may_spawn pilot mode ผ่าน cert_v2 ไม่นับเป็น pilot", S.pilot_ok([A("cert_v2", 4, "OK", S.PILOT_KEY)]) is None)
    # post_env (Y-1) · post_n anti-drift (Z-6) · check_key (Y-2)
    ok("post_env h0stress c1restr", S.post_env("c1restr/h0stress/-/0/200") == {"AD4_CONTINGENCY": "c1restr"})
    ok("post_env h0stress c1full = {}", S.post_env("c1full/h0stress/-/0/200") == {}); ok("post_env None = {}", S.post_env(None) == {})
    from ad4_card import WORLDS, CERT_N, CERT_N_POWER
    ok("post_n = ad4_card.py:513 ครบทุก world", all(S.post_n(w) == (CERT_N_POWER if w == "flip" else (30 if w == "h0pilot" else CERT_N)) for w in WORLDS))
    ck = lambda key, mode, env=None: not S.check_key(key, mode, {"AD4_CONTINGENCY": env} if env else {})
    ok("check_key pilot", ck(S.PILOT_KEY, "pilot")); ok("check_key cert h0cal 0..10", ck(CK, "cert_v2"))
    ok("check_key flip 3", ck("c1full/flip/3/0/10", "cert_v2")); ok("check_key flip 6 0..50", ck("c1full/flip/6/0/50", "cert_v2"))
    for bad_k, why in (("c1full/h0cal/-/190/210", "k1 > N"), ("c1ful/h0cal/-/0/10", "variant"), ("c1full/flip/7/0/10", "cell ≥ 7"),
                       ("c1full/flip/-/0/10", "flip ไม่มี cell"), ("c1full/h0cal/3/0/10", "non-flip มี cell"), ("c1full/flip/3/0/51", "flip k1 > 50"),
                       ("c1full/h0pilot/-/0/30", "cert h0pilot"), ("c1full/bogus/-/0/10", "world")):
        ok(f"check_key {why} ✗", not ck(bad_k, "cert_v2"))
    ok("check_key pilot key อื่น ✗", not ck("c1full/h0pilot/-/0/10", "pilot"))
    ok("check_key h0stress c1restr ไม่มี env ✗", not ck("c1restr/h0stress/-/0/200", "cert_v2"))
    ok("check_key h0stress c1restr + env", ck("c1restr/h0stress/-/0/200", "cert_v2", "c1restr"))
    ok("check_key h0stress c1full", ck("c1full/h0stress/-/0/200", "cert_v2"))
    r13 = ("[run] start mode=rg14 att=1 ts=2026-10-21 08:30:21 run_id=u9 oom_kill=0 seq=79 ns=1 boot_id=b0 sup=1:2 bt=3")
    m = S.START_RE.match(r13); ok("START_RE r13 (ไม่มี args) match · args=None", m is not None and m.groups()[-1] is None)
    try: S.fmt_start("rg14", 1, "2026-10-21 01:00:00", "u", 0, 1, 1, "b0", 1, 1, 1, "c1full/h0cal/-/0/10"); ok("fmt_start args ใน mode B → assert", False)
    except AssertionError: ok("fmt_start args ใน mode B → assert", True)
    try: S.fmt_start("pilot", 1, "2026-10-21 01:00:00", "u", 0, 1, 1, "b0", 1, 1, 1); ok("fmt_start pilot ไม่มี args → assert", False)
    except AssertionError: ok("fmt_start pilot ไม่มี args → assert", True)
    root0 = S.ROOT; d = tempfile.mkdtemp(prefix="h19root_")
    try:
        S.ROOT = os.path.realpath(d)
        for n in ("run_x", "run_smoke2", "smoke", "python"): os.makedirs(os.path.join(d, n, "repo"))
        os.makedirs(os.path.join(d, "run_x", "sub", "repo"))
        def v(p):
            try: S.valid_rundir(os.path.join(d, p)); return True
            except ValueError: return False
        ok("valid_rundir run_x", v("run_x")); ok("valid_rundir run_smoke2", v("run_smoke2"))
        ok("valid_rundir smoke ✗", not v("smoke")); ok("valid_rundir python ✗", not v("python"))
        ok("valid_rundir ROOT ✗", not v("")); ok("valid_rundir nested ✗", not v(os.path.join("run_x", "sub")))
        # attempt_label: end line ครบ field แต่ cause นอก enum → ToolError (front พิมพ์ label=TOOL)
        rd = os.path.join(d, "run_x"); os.makedirs(os.path.join(rd, "run"))
        lp = os.path.join(rd, "run", "t-exit0.1.log")
        io.open(lp, "w", newline="\n").write(S.fmt_start("t-exit0", 1, "2026-10-21 01:00:00", "u1", 0, 1, 1, "b0", 1, 1, 1) + "\n[run] end rc=0 oom_kill=0 seq=1 cause=bogus viol=-\n")
        try: S.attempt_label(rd, lp); ok("label cause นอก enum → ToolError", False)
        except S.ToolError: ok("label cause นอก enum → ToolError", True)
        got = S.record_of(rd, 1)
        ok("record_of cause นอก enum → log-tool (front: label=TOOL · 77)", got is not None and got[0] == "log-tool")
        ok("record_of ns อื่น → None", S.record_of(rd, 2) is None)
        io.open(lp, "w", newline="\n").write("[run] start mode=t-exit0 att=1 ts=2026-10-21 01:00:00 run_id=u1 oom_kill=0\n[run] end rc=0 oom_kill=0\n")
        try: S.attempt_label(rd, lp); ok("start ไม่มี seq → ToolError format เก่า", False)
        except S.ToolError: ok("start ไม่มี seq → ToolError format เก่า", True)
        io.open(lp, "w", newline="\n").write(S.fmt_start("t-exit0", 1, "2026-10-21 01:00:00", "u1", 0, 1, 1, "b0", 1, 1, 1) + " args=c1full/h0cal/-/0/10\n")
        try: S.read_attempt(lp); ok("read: args= ใน mode ที่ไม่ใช่ post → ToolError", False)
        except S.ToolError: ok("read: args= ใน mode ที่ไม่ใช่ post → ToolError", True)
        pp = os.path.join(rd, "run", "pilot.1.log")
        io.open(pp, "w", newline="\n").write("[run] start mode=pilot att=1 ts=2026-10-21 01:00:00 run_id=u2 oom_kill=0 seq=2 ns=2 boot_id=b0 sup=1:1 bt=2\n")
        try: S.read_attempt(pp); ok("read: pilot ไม่มี args= → ToolError", False)
        except S.ToolError: ok("read: pilot ไม่มี args= → ToolError", True)
        os.remove(pp)
        io.open(lp, "w", newline="\n").write(S.fmt_start("t-exit0", 1, "2026-10-21 01:00:00", "u1", 0, 1, 1, "b0", 1, 1, 1) + "\n" + S.fmt_end(0, 0, 1, "child-exit", set()) + "\n")
        lab = S.attempt_label(rd, lp)
        ok("label t-exit0 = OK", lab["verdict"] == "OK" and lab["cause"] == "child-exit")
        ok("record_of ns ตรง → log", (S.record_of(rd, 1) or ("",))[0] == "log")
        ok("resolved (end clean)", S.resolved(rd, "u1"))
        ok("resolved ไม่มี id", not S.resolved(rd, "nope"))
        ok("b_start derived = ts ของ start แรก", resolve_b_start(rd) == ("2026-10-21 01:00:00", "derived"))
        ok("b_start override UTC", resolve_b_start(rd, "2026-10-21 00:00:00") == ("2026-10-21 00:00:00", "override"))
        try: resolve_b_start(rd, "21/10/2026 07:00"); ok("b_start override รูปผิด → ToolError", False)
        except S.ToolError: ok("b_start override รูปผิด → ToolError", True)
        # fixture "kill -9 หลัง end line ก่อน current": end clean + current=running ของ sup ที่ตายแล้ว → resolved (ไม่มี stale-run ปลอม)
        S.write_json_atomic(os.path.join(rd, "run", "current"), {"run_id": "u1", "state": "running", "sup_pid": 1, "sup_starttime": 1, "boot_id": "b0"})
        ok("kill -9 หลัง end ก่อน current → resolved", S.resolved(rd, "u1"))
        # kill -9 ก่อน end line: LOG ไม่มี end → ไม่ resolved (stale-run ถูกต้อง)
        io.open(lp, "w", newline="\n").write(S.fmt_start("t-exit0", 1, "2026-10-21 01:00:00", "u1", 0, 1, 1, "b0", 1, 1, 1) + "\n")
        ok("kill -9 ก่อน end → ไม่ resolved", not S.resolved(rd, "u1"))
    finally:
        S.ROOT = root0; shutil.rmtree(d, ignore_errors=True)
    return out


def selftest():
    from ad4_card import RG14_TAGS, SPEC_SHA, closure_sha
    tags, cl = list(RG14_TAGS), closure_sha()
    cases = [(None, "PASS", None), ("raise", "RAISE", None), ("collapse", "FAILLOUD", None), ("regress_fail", "REGRESS_FAIL", None),
             ("abort", "ABORT", None), ("oom", "INFRA", None), ("memerr", "INFRA", None), ("kill_nooom", "INVALID", "rc=137"),
             ("fp", "NEWDIR", "fingerprint"), ("drop_live", "NEWDIR", "unattested"), ("resumed_only", "NEWDIR", "unattested"),
             ("live_val", "INVALID", "บรรทัดสด"), ("card", "INVALID", "SPEC/card/closure"), ("ck_extra", "INVALID", "checkpoint key"),
             ("ck_closure", "INVALID", "checkpoint closure"), ("stale_receipt", "INVALID", "receipt regress"),
             # r12: cause/viol · end line grammar · abort ครบ · escape-after-end · seq · gate = note
             ("abort_notaken", "INVALID", "abort ไม่ครบ"), ("abort_killfail", "INVALID", "viol=killfail"),
             ("deadline_oom", "INVALID", "cause=deadline-wall"), ("spawnfail", "INVALID", "cause=spawn-fail"),
             ("raise_leftover", "INVALID", "child_class=RAISE"), ("note_signal", "PASS", None), ("internal_after", "INVALID", "viol=internal"),
             ("noend", "INVALID", "supervisor-died"), ("noend_orphan", "INVALID", "supervisor-died"), ("nolf", "INVALID", "supervisor-died"),
             ("orphan_after_end", "INVALID", "escape-after-end"), ("c3_after_end", "INVALID", "escape-after-end"),
             ("gate75", "PASS", None), ("seq_order", "INFRA", None),
             # r13: seq/bt · host_sha
             ("dup_seq", "TOOL", "seq ซ้ำ"), ("bt_rev", "TOOL", "bt ไม่มากกว่า"), ("bt_rev_xboot", "INFRA", None),
             ("host_sha", "NEWDIR", "fingerprint"),
             # J1–J7 = ผลวัดของ judge เดิม (Engineer #16 probe · วัดซ้ำ #18) · format ใหม่
             ("J1", "REGRESS_FAIL", None), ("J2", "INFRA", None), ("J3", "INVALID", "ไม่มี preflight PASS"),
             ("J4", "INVALID", "ไม่มี [venue]"), ("J5", "INFRA", None), ("J6", "INVALID", "ไม่มี log"), ("J7", "INVALID", "ไม่มี regress PASS"),
             # r14 (spec §13): post-B pilot/cert_v2 · B-part บน prefix · retry ต่อ key · re-root path
             ("post_ok", "PASS", "post-B OK 1 key"), ("post_noline", "POST_FAIL", "ต้องมี 1 บรรทัด ได้ 0"), ("post_nofile", "POST_FAIL", "ไม่มีไฟล์ chunk"),
             ("post_fp", "NEWDIR", "fingerprint"), ("post_infra_retry", "PASS", "INFRA → OK → OK"), ("post_infra2", "POST_FAIL", "INFRA → INFRA → ไม่ผ่าน"),
             ("post_fail_last", "POST_FAIL", "B-part PASS · post-B ไม่ผ่าน"), ("post_cert4", "PASS", "post-B OK 2 key"),
             ("post_cert5", "PASS", "post-B OK 2 key"), ("post_AB", "POST_FAIL", "c1full/h0cal/-/0/10: INFRA → ไม่ผ่าน"),
             ("post_AA", "PASS", "INFRA → OK → OK"), ("post_nosuffix", "POST_FAIL", "path ไม่มี"), ("post_mismatch", "POST_FAIL", "ไม่ตรง key"),
             ("post_before", "INVALID", "ก่อน attempt สุดท้ายของ B"),
             ("post_nopilot", "POST_FAIL", "ไม่มี pilot OK ก่อนหน้า"), ("post_cert_first", "POST_FAIL", "ไม่มี pilot OK ก่อนหน้า"),
             ("post_pilot_infra", "POST_FAIL", "ไม่มี pilot OK ก่อนหน้า"), ("post_pilot_retry_cert", "PASS", "post-B OK 2 key"),
             ("post_twolines", "POST_FAIL", "ต้องมี 1 บรรทัด ได้ 2"),
             ("post_abort_retry", "PASS", "ABORT → OK → OK"), ("post_abort_only", "POST_FAIL", "ABORT → ไม่ผ่าน")]
    bad = 0
    for mut, want, why in cases:
        got, notes = _judge_case(tags, SPEC_SHA, cl, mut)
        txt = " ".join(notes)
        ok = got == want and (why is None or why in txt); bad += not ok
        print(f"  {'OK ' if ok else 'BAD'} {str(mut):17s} → {got:12s} (คาด {want}{' · ' + why if why else ''})" + ("" if ok else f" · {notes[-3:]}"))
    units = _unit_checks()
    for name, cond in units:
        bad += not cond
        print(f"  {'OK ' if cond else 'BAD'} {name}")
    n = len(cases) + len(units)
    print(f"[selftest] {n - bad}/{n} OK")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
