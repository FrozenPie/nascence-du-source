"""J-3111 test: core/social_cognition_shadow.status() reports unanimous rate, tiebreak share, pegged flag, per-bar
UNREAD marks, n-by-kind and cycles waiting. Every log is a temp-dir file (a synthetic one, plus a COPY of the live
shadow log if it can be read); no model call, no live store written. Import core BEFORE lab_env. Exit 0 = pass."""
import json, sys, pathlib, tempfile, shutil
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env  # noqa: F401  (imported to match the suite; the test itself only writes under a temp dir)
from core import social_cognition_shadow as S

FAILS = []
def check(l, c):
    print(("  ok   " if c else "  FAIL ") + l)
    if not c: FAILS.append(l)

def vote(v, how): return {"verdict": v, "how": how, "v1": v, "v2": v, "why": "stub"}

def row(cid, kind, tr, refs, attrs, supp, pv=S.PROMPT_V):
    """tr/refs/attrs/supp: (verdict, how) or None."""
    votes = {"tracks_intent": vote(*tr)}
    if refs: votes["refs_earlier"] = vote(*refs)
    votes["attributes"] = vote(*attrs)
    if supp: votes["attrib_supported"] = vote(*supp)
    return {"ts": 1.0, "cycle_id": cid, "human_ts": 1.0, "prompt_v": pv, "kind": kind, "tracks_intent": tr[0],
            "refs_earlier": refs[0] if refs else None, "attributes": attrs[0],
            "attrib_supported": supp[0] if supp else None, "lex_earlier_overlap": 1, "votes": votes}

tmp = pathlib.Path(tempfile.mkdtemp(prefix="J3111_"))
try:
    # ---- synthetic log with known counts: 10 conversation rows + 1 farewell
    rows = []
    for i in range(10):
        tr = (True, "agreed") if i < 6 else ((True, "tiebreak") if i < 8 else (False, "agreed"))
        refs = None if i == 0 else ((True, "tiebreak") if i < 4 else (False, "agreed"))
        attrs = (True, "agreed")                                        # pegged: 10/10 true
        supp = (True, "tiebreak") if i < 6 else ((False, "agreed") if i < 8 else (True, "agreed"))
        rows.append(row(f"c{i}", "conversation", tr, refs, attrs, supp))
    rows.append(row("f0", "farewell", (True, "agreed"), None, (True, "agreed"), (False, "agreed")))
    rows.append(row("old", "conversation", (True, "agreed"), None, (True, "agreed"), None, pv=2))   # other prompt_v
    rows.append({"ts": 2.0, "skip": "no-candidates"})                                               # not a score row
    log = tmp / "scs.jsonl"
    log.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    conv = tmp / "conv.jsonl"
    cl = [{"ts": 1790600000 + i, "cycle_id": f"c{i}", "human": "hello there", "entity": "hi"} for i in range(10)]
    cl += [{"ts": 1790600100, "cycle_id": "w1", "human": "tell me more about the house", "entity": "x"},
           {"ts": 1790600200, "cycle_id": "w2", "human": "y" * 1500, "entity": "x"},
           {"ts": 1790600300, "cycle_id": "w3", "human": "it's time to stop for a while", "entity": "x"},
           {"ts": 1700000000, "cycle_id": "ancient", "human": "before the probe", "entity": "x"}]
    conv.write_text("\n".join(json.dumps(r) for r in cl), encoding="utf-8")

    st = S.status(log, conv_path=conv)
    k = st["by_kind"]["conversation"]["keys"]
    check("scored counts only the default prompt_v score rows", st["scored"] == 11)
    t = k["tracks_intent"]
    check("tracks: n 10, true 8, rate 0.8", (t["n"], t["true"], t["rate"]) == (10, 8, 0.8))
    check("tracks: unanimous 6 agreed-true + 2 agreed-false -> 6/8 = 0.75", (t["unanimous_n"], t["unanimous_rate"]) == (8, 0.75))
    check("tracks: tiebreak 2 of 10 = 0.2, both true, 2/8 of the trues = 0.25",
          (t["tiebreak_n"], t["tiebreak_share"], t["tiebreak_true"], t["tiebreak_true_share"]) == (2, 0.2, 2, 0.25))
    s = k["attrib_supported"]
    check("supported: panel 8/10 pooled but unanimous only 2/4 (agreed true 2, agreed false 2) -> 0.5",
          (s["n"], s["true"], s["rate"], s["unanimous_n"], s["unanimous_rate"]) == (10, 8, 0.8, 4, 0.5))
    check("supported: tiebreak decided 6 of 10, 6 of the 8 trues = 0.75", (s["tiebreak_n"], s["tiebreak_share"], s["tiebreak_true_share"]) == (6, 0.6, 0.75))
    a = k["attributes"]
    check("attributes 10/10 true at n=10 >= MIN_N is PEGGED, with the no-information note", a["pegged"] is True and "no information" in a["note"])
    check("tracks 0.8 and supported 0.8 are not pegged", not t["pegged"] and not s["pegged"])
    r_ = k["refs_earlier"]
    check("refs: 9 rulings (first turn has no prior), 3 true", (r_["n"], r_["true"]) == (9, 3))
    # pegged needs n >= MIN_N: 3 all-true rulings are not flagged
    small = S.key_stats([row(f"s{i}", "conversation", (True, "agreed"), None, (True, "agreed"), None) for i in range(3)])
    check("3/3 true is not pegged (n < MIN_N)", small["tracks_intent"]["pegged"] is False and small["tracks_intent"]["rate"] == 1.0)
    low = S.key_stats([row(f"l{i}", "conversation", (False, "agreed"), None, (True, "agreed"), None) for i in range(9)])
    check("0/9 true is pegged low", low["tracks_intent"]["pegged"] is True)
    # split_no_tiebreak / unavailable rulings are counted aside, not in n
    nov = S.key_stats([row("n1", "conversation", (None, "split_no_tiebreak"), None, (True, "agreed"), None)])
    check("no-verdict ruling counted in no_verdict, not n", nov["tracks_intent"]["n"] == 0 and nov["tracks_intent"]["no_verdict"] == 1
          and nov["tracks_intent"]["rate"] is None and nov["tracks_intent"]["unanimous_rate"] is None)

    # ---- the verdict line is per bar, with UNREAD marks
    br = st["bar_result"]
    check("tracks_intent bar is read (MEETS/BELOW), refs and supported are UNREAD",
          br["tracks_intent"] in ("MEETS", "BELOW") and br["refs_earlier"].startswith("UNREAD") and br["attrib_supported_given_attributes"].startswith("UNREAD"))
    check("raw comparison kept in bar_raw", set(st["bar_raw"]) == set(br) and all(v in ("MEETS", "BELOW") for v in st["bar_raw"].values()))
    v = st["verdict"]
    check("verdict is no longer the blanket line", "BELOW BAR / PARTIAL" not in v and "MEETS BAR" not in v)
    check("verdict carries the hand-label figures", "12/15" in v and "6/8" in v and "errs low" in v and "6/15" in v and "4/8" in v)
    check("tracks_intent line says it is the only bar number with a hand-label check", "only bar number with one" in v)
    # ---- n-by-kind and waiting
    check("n_line: n by kind", "conversation 10" in st["n_line"] and "farewell 1" in st["n_line"])
    check("waiting: w1 conversation, w2 paste, w3 farewell = 3; 'ancient' before the probe excluded",
          st["waiting"] == {"n": 3, "by_kind": {"conversation": 1, "paste": 1, "farewell": 1}} and "cycles waiting: 3" in st["n_line"])
    # a test log without conv_path never reads the live conversation log
    st2 = S.status(log)
    check("test log without conv_path: waiting unknown, not the live count", st2["waiting"]["n"] is None and "waiting: unknown" in st2["n_line"])
    # thin data still INSUFFICIENT, still has n_line and keys
    thin = tmp / "thin.jsonl"
    thin.write_text(json.dumps(rows[0]), encoding="utf-8")
    st3 = S.status(thin, conv_path=conv)
    check("thin n: INSUFFICIENT verdict, n_line present", st3["verdict"].startswith("INSUFFICIENT") and "n_line" in st3 and "bar_result" not in st3)
    check("missing log fails open", S.status(tmp / "nope.jsonl", conv_path=conv).get("scored") == 0)

    # ---- v4 rows: criterion 3 votes live on the candidates
    def v4row(cid, clauses):
        cands = []
        for is_state, supp in clauses:
            c = {"clause": "you fear x", "is_state": is_state, "supported": supp,
                 "votes": {"attrib_clause": vote(is_state, "agreed")}}
            if is_state: c["votes"]["clause_supported"] = vote(supp, "tiebreak")
            cands.append(c)
        return {"ts": 3.0, "cycle_id": cid, "prompt_v": 4, "kind": "conversation", "tracks_intent": True, "refs_earlier": None,
                "attributes": any(c["is_state"] for c in cands), "attrib_supported": None, "lex_earlier_overlap": 0,
                "candidates": cands, "votes": {"tracks_intent": vote(True, "agreed")}}
    v4 = [v4row("v0", [(True, True), (False, None)]), v4row("v1", [(True, False)])]
    k4 = S.key_stats(v4)
    check("v4 attributes: 3 clause rulings, 2 true; supported: 2 rulings, 1 true, all tiebreak",
          (k4["attributes"]["n"], k4["attributes"]["true"]) == (3, 2) and
          (k4["attrib_supported"]["n"], k4["attrib_supported"]["true"], k4["attrib_supported"]["tiebreak_share"]) == (2, 1, 1.0))
    v4log = tmp / "v4.jsonl"
    v4log.write_text("\n".join(json.dumps(dict(v4row(f"q{i}", [(True, True)]))) for i in range(9)), encoding="utf-8")
    st4 = S.status(v4log, prompt_v=S.PROMPT_V4, conv_path=conv)
    check("v4 status: supported bar UNREAD with the v4-not-validated reason",
          "v4 not yet validated" in st4["bar_result"]["attrib_supported_given_attributes"])

    # ---- a COPY of the live log (if readable) must not break and must agree with an independent recount
    live = pathlib.Path("C:/Nascence/data/social_cognition_shadow.jsonl")
    if live.exists():
        cp = tmp / "live_copy.jsonl"
        shutil.copyfile(live, cp)
        stl = S.status(cp, prompt_v=3, conv_path=conv)   # the live rows are v3 (J-3112 bumped the default to 5)
        allr = [json.loads(x) for x in cp.read_text(encoding="utf-8").splitlines() if x.strip()]
        v3 = [r for r in allr if "tracks_intent" in r and r.get("prompt_v") == 3 and r.get("kind") == "conversation"]
        ks = stl["by_kind"]["conversation"]["keys"]
        vs = [r["votes"]["attributes"] for r in v3 if "attributes" in r.get("votes", {})]
        check(f"live copy: attributes recount matches (n={ks['attributes']['n']})",
              ks["attributes"]["n"] == sum(1 for x in vs if x["verdict"] is not None)
              and ks["attributes"]["unanimous_n"] == sum(1 for x in vs if x["verdict"] is not None and x["how"] == "agreed"))
        print("   live-copy verdict:", stl["verdict"])
        print("   live-copy n_line :", stl["n_line"])
        for key, d in ks.items():
            print(f"   {key:17s} n={d['n']:3d} rate={d['rate']} unanimous={d['unanimous_true']}/{d['unanimous_n']} "
                  f"tiebreak_share={d['tiebreak_share']} pegged={d['pegged']}")
    else:
        print("  (live shadow log not readable here; live-copy check skipped)")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)
