"""J-1765 (D-0336): hermetic test that core/memory_levels.shadow_distill no longer spends the fix (b) second
distil + grade pair, and that status() / the d0272_fix_b_shadow aggregate still read old AND new rows.

WHAT IT PROVES (each is a separate check; all print PASS/FAIL, exit code 1 if any FAIL):
  * 2 LLM calls per cluster (1 distil + 1 grade), not 4 -- counted by a stub call_json and a stub grader;
    the fix (b) prompt text never reaches the model; the _SYS_FIX_B_SHADOW constant is gone (no dead path).
  * every other part of the row and of the returned summary is unchanged: the row has exactly the old keys
    minus `fix_b_shadow`, the demotion/commit accounting is as before, the fetch-probe / row-count / state side
    logs are still written.
  * status() works on an old-format log (rows with a fix_b_shadow dict, with None, and with no key), on a
    new-format log (no row has the field), and on a missing log; the d0272_fix_b_shadow aggregate keeps its
    shape and is computed from the rows that carry the field.
  * (--baseline PATH) the same fixture run through another copy of memory_levels.py (e.g. HEAD's pre-change one)
    gives rows that are field-for-field identical except for `ts` and `fix_b_shadow`, and an identical summary.

HERMETIC: no model, no network, nothing started or stopped. The memory DB is an EMPTY schema-initialised lab DB
(lab_env.isolate(db="empty"): DB_PATH redirected into data/_lab/<ts>/), each module's own four data paths are
redirected into that lab dir, _commit_gist is stubbed (it would write the store), and the live data files are
hashed before and after as a canary.

USAGE (repo root or a worktree):
    python scripts/_test_j1765_end_fix_b_shadow.py                    # the memory_levels.py in THIS tree: must PASS
    python scripts/_test_j1765_end_fix_b_shadow.py --module PATH      # test another copy; HEAD's pre-change copy must
                                                                      # FAIL the call-count / key / constant checks
    python scripts/_test_j1765_end_fix_b_shadow.py --baseline PATH    # also compare against that copy's rows
"""
import argparse
import asyncio
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")        # lab_env prints non-ASCII; Windows charmap guard
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
# This tree's core/ must win: lab_env inserts C:\Nascence at sys.path[0] on import, so import core FIRST.
sys.path.insert(0, str(ROOT))
from core.memory import store as _store            # noqa: E402  (imported before lab_env on purpose)
from core import left_lane as _left_lane           # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
import lab_env                                      # noqa: E402

DATA = ROOT / "data" if (ROOT / "data" / "night_log.jsonl").exists() else Path(r"C:\Nascence\data")   # worktrees have no data/
CANARY_FILES = ["memory_levels_shadow.jsonl", "memory_levels_shadow_state.json", "memory_levels_fetch_probe.jsonl",
                "memory_levels_row_counts.jsonl", "memory_levels_drift_shadow.jsonl"]
CANARY_DB = DATA / "memory" / "nascence.db"

NEW_ROW_KEYS = {"ts", "kind", "topic", "n_sources", "source_ids", "gist", "faithful", "source_fidelity", "feedback",
                "invented_claims", "false_flags", "source_sample"}
STATUS_KEYS = {"logged", "mean_faithful", "mean_source_fidelity", "recent", "invented_claims", "false_flags",
               "false_flag_rate", "d0272_fix_b_shadow"}
AGG_KEYS = {"n", "mean_faithful", "eligible_rate", "current_eligible_rate_paired"}
FIXB_PHRASE = "pretrained knowledge"     # distinctive text of the strengthened (fix b) prompt, absent from the live one

# topic token -> (faithful the stub judge returns, 'invented' terms it claims)
SCENARIO = {"zephyrine": (0.90, []),                   # eligible            -> committed
            "quillon": (0.60, []),                     # below the 0.75 floor -> raw stays warm
            "marlowe": (0.90, ["Qzxv Wuthering"]),     # judge claims invention; in no source, not in the store -> GENUINE
            "tamsin": (0.80, [])}                      # eligible            -> committed
GROUPS = [("zephyrine", "reading", 4), ("quillon", "reading", 3), ("marlowe", "inner_thought", 4), ("tamsin", "lived", 3)]

FAILS = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + str(detail)) if detail != "" else ""))
    if not ok:
        FAILS.append(name)


def sha(p):
    p = Path(p)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canary():
    snap = {n: sha(DATA / n) for n in CANARY_FILES}
    st = CANARY_DB.stat() if CANARY_DB.exists() else None
    snap["nascence.db(size,mtime_ns)"] = (st.st_size, st.st_mtime_ns) if st else None
    return snap


def load_module(path):
    if path is None:
        from core import memory_levels as ml
        return ml
    spec = importlib.util.spec_from_file_location("ml_under_test_" + Path(path).stem, str(path))
    ml = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ml)
    return ml


def redirect(ml, tag, lab):
    """Point all five of the module's own data paths into the lab dir; returns the originals for restoring."""
    orig = {a: getattr(ml, a) for a in ("_STATE", "_LOG", "_FETCH_PROBE_LOG", "_ROW_COUNT_LOG", "_DRIFT_LOG")}
    for a in orig:
        setattr(ml, a, lab / f"{tag}{a}.dat")
    return orig


def seed_fragments():
    now = time.time()
    rows = []
    for gi, (tok, origin, n) in enumerate(GROUPS):
        for k in range(n):
            rows.append((f"j1765-{tok}-{k}", f"Fragment {k} about {tok}: stub source text {gi}{k} for the J-1765 test.",
                         "episodic", 0.5, now - 1000 + gi * 10 + k, f"{tok} uniq{gi}x{k}x", origin))
    with _store._connect() as conn:
        conn.executemany("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, "
                         "origin, abstraction_level, cold) VALUES (?,?,?,?,?,?,?,0,0)", rows)
        conn.commit()
    return len(rows)


class Stubs:
    def __init__(self):
        self.distil, self.grade, self.commit = [], [], []

    async def call_json(self, base_urls, sys_prompt, user_prompt, max_tokens=300, temperature=0.3):
        self.distil.append((sys_prompt, user_prompt))
        topic = user_prompt.split("Topic: ", 1)[1].split(".", 1)[0]
        variant = "FIXB" if FIXB_PHRASE in sys_prompt else "CUR"
        return {"gist": f"{variant} stub gist about {topic}: long enough to clear the forty character floor."}

    async def grade_gist_faithfulness(self, gist, sources):
        self.grade.append((gist, list(sources)))
        topic = gist.split(" about ", 1)[1].split(":", 1)[0]
        faithful, invented = SCENARIO[topic]
        return {"faithful": faithful, "invented": list(invented), "feedback": f"stub grade for {topic}"}

    def commit_gist(self, gist, kind, crows, faithful):
        self.commit.append((kind, sorted(r["fragment_id"] for r in crows), faithful))
        return f"stub-gist-{len(self.commit)}"


def run_module(ml, tag, lab):
    """Run ml.shadow_distill once over the seeded fixture with stubs; returns (summary, rows, stubs)."""
    stubs = Stubs()
    orig_paths = redirect(ml, tag, lab)
    orig_commit, orig_p1 = ml._commit_gist, ml.PHASE1_ENABLED
    orig_pause = getattr(ml, "EPISODIC_DEMOTION_PAUSED", None)
    orig_voice = getattr(ml, "SELF_GIST_FIRST_PERSON", None)
    orig_grade = _left_lane.grade_gist_faithfulness
    ml._commit_gist, ml.PHASE1_ENABLED = stubs.commit_gist, True
    ml.EPISODIC_DEMOTION_PAUSED = False       # J-3176 (D-0564): this test pins the PRE-pause accounting (episodic demotes too)
    ml.SELF_GIST_FIRST_PERSON = False         # J-3212 (D-0601): and the pre-voice row shape (no `voice` key on self rows)
    _left_lane.grade_gist_faithfulness = stubs.grade_gist_faithfulness
    try:
        out = asyncio.run(ml.shadow_distill(stubs.call_json, ["http://stub.invalid"]))
        rows = [json.loads(l) for l in ml._LOG.read_text(encoding="utf-8").splitlines() if l.strip()] if ml._LOG.exists() else []
        side = {"fetch_probe_rows": len(ml._FETCH_PROBE_LOG.read_text(encoding="utf-8").splitlines()) if ml._FETCH_PROBE_LOG.exists() else 0,
                "row_count_rows": len(ml._ROW_COUNT_LOG.read_text(encoding="utf-8").splitlines()) if ml._ROW_COUNT_LOG.exists() else 0,
                "state": json.loads(ml._STATE.read_text(encoding="utf-8")) if ml._STATE.exists() else None}
        return out, rows, stubs, side
    finally:
        ml._commit_gist, ml.PHASE1_ENABLED = orig_commit, orig_p1
        if orig_pause is not None:
            ml.EPISODIC_DEMOTION_PAUSED = orig_pause
        else:
            del ml.EPISODIC_DEMOTION_PAUSED
        if orig_voice is not None:
            ml.SELF_GIST_FIRST_PERSON = orig_voice
        else:
            ml.__dict__.pop("SELF_GIST_FIRST_PERSON", None)
        _left_lane.grade_gist_faithfulness = orig_grade
        for a, v in orig_paths.items():
            setattr(ml, a, v)


def status_fixture(ml, lab):
    """status() on hand-written logs: old format, new format, mixed, and a missing file. Paths restored after."""
    def row(faithful, fb=..., claims=()):
        r = {"ts": 1.0, "kind": "semantic", "topic": "t", "n_sources": 3, "source_ids": ["a"], "gist": "g" * 50,
             "faithful": faithful, "source_fidelity": 0.9, "feedback": "", "invented_claims": [list(c) for c in claims],
             "false_flags": 0, "source_sample": "s"}
        if fb is not ...:
            r["fix_b_shadow"] = fb
        return r

    def fb(faithful, eligible):
        return {"gist": "gb" * 30, "faithful": faithful, "source_fidelity": 0.9, "feedback": "", "invented_claims": [],
                "genuine_invention": False, "eligible_to_commit": eligible}

    mixed = [row(0.9),                              # pre-wire row: no key
             row(0.8, fb(0.9, True)),               # wired: current eligible, fix b eligible
             row(0.6, fb(0.8, True)),               # wired: current NOT eligible, fix b eligible
             row(0.9, None),                        # wired but the fix (b) call failed: key present, value None
             row(0.9, claims=[("Zz", "GENUINE")])]  # NEW format: no key at all (current ineligible: GENUINE)
    new_only = [row(0.9), row(0.7), row(0.85, claims=[("Qq", "IN_SOURCE")])]
    saved = ml._LOG
    try:
        res = {}
        for name, rows in (("mixed", mixed), ("new_only", new_only)):
            p = lab / f"status_{ml.__name__}_{name}.jsonl"
            p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            ml._LOG = p
            res[name] = ml.status()
        ml._LOG = lab / f"status_{ml.__name__}_missing.jsonl"
        res["missing"] = ml.status()
        return res
    finally:
        ml._LOG = saved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", help="memory_levels.py to test (default: this tree's core/memory_levels.py)")
    ap.add_argument("--baseline", help="another memory_levels.py to run on the same fixture and compare rows against")
    a = ap.parse_args()

    ml = load_module(a.module)
    print("module under test:", Path(ml.__file__).resolve())
    if a.module is None:
        check("module under test is THIS tree's core/memory_levels.py", Path(ml.__file__).resolve().is_relative_to(ROOT))
    before = canary()

    with lab_env.isolate(db="empty") as lab:
        n_frag = seed_fragments()
        print(f"fixture: {n_frag} fragments, {len(GROUPS)} intended clusters (lab dir {lab})")

        # ---- shadow_distill: call count, row shape, accounting ---------------------------------------
        out, rows, stubs, side = run_module(ml, "new_", lab)
        n_cl = out.get("clusters")
        n_d, n_g = len(stubs.distil), len(stubs.grade)
        print(f"summary: {out}")
        print(f"calls: distil={n_d} grade={n_g} total={n_d + n_g} for {n_cl} clusters "
              f"-> {((n_d + n_g) / n_cl) if n_cl else float('nan'):.2f} per cluster")
        check("fixture formed the 4 intended clusters", n_cl == 4, f"clusters={n_cl}")
        check("exactly 1 distil call per cluster", n_d == n_cl, f"distil calls={n_d}, clusters={n_cl}")
        check("exactly 1 grade call per cluster", n_g == n_cl, f"grade calls={n_g}, clusters={n_cl}")
        check("2 LLM calls per cluster in total (not 4)", (n_d + n_g) == 2 * n_cl, f"total={n_d + n_g}, expected {2 * n_cl}")
        check("the fix (b) prompt text never reaches the model", not any(FIXB_PHRASE in s for s, _ in stubs.distil))
        check("_SYS_FIX_B_SHADOW constant is gone (no dead path left)", not hasattr(ml, "_SYS_FIX_B_SHADOW"))
        check("one row per cluster was logged", len(rows) == n_cl, f"rows={len(rows)}")
        bad_keys = [sorted(set(r) ^ NEW_ROW_KEYS) for r in rows if set(r) != NEW_ROW_KEYS]
        check("every row has exactly the old keys minus fix_b_shadow", not bad_keys, bad_keys[:2])
        by_topic = {r["topic"]: r for r in rows}
        check("rows carry the CURRENT-prompt gist, unchanged", all(r["gist"].startswith("CUR stub gist about " + r["topic"]) for r in rows))
        check("rows carry the stub judge's faithful scores", all(r["faithful"] == SCENARIO[r["topic"]][0] for r in rows))
        check("GENUINE invention backstop still recorded", by_topic.get("marlowe", {}).get("invented_claims") == [["Qzxv Wuthering", "GENUINE"]],
              by_topic.get("marlowe", {}).get("invented_claims"))
        committed = sorted(c[1][0].split("-")[1] for c in stubs.commit)
        check("commit accounting unchanged: only the eligible, backstop-clean clusters commit", committed == ["tamsin", "zephyrine"], committed)
        check("summary: demoted counts the committed sources (4 + 3)", out.get("demoted") == 7, out.get("demoted"))
        check("summary: graded / invented_claims / false_flags / mean_faithful as before",
              (out.get("graded"), out.get("invented_claims"), out.get("false_flags"), out.get("mean_faithful")) == (4, 1, 0, 0.8),
              (out.get("graded"), out.get("invented_claims"), out.get("false_flags"), out.get("mean_faithful")))
        check("side logs still written (fetch probe 1 row, row counts 3 rows, state frontier)",
              side["fetch_probe_rows"] == 1 and side["row_count_rows"] == 3 and isinstance(side["state"], dict) and side["state"].get("last_ts"), side)

        # ---- status(): old rows, new rows, mixed, missing ---------------------------------------------
        st = status_fixture(ml, lab)
        mx, no = st["mixed"], st["new_only"]
        check("status() keys unchanged (mixed log)", set(mx) == STATUS_KEYS, sorted(set(mx) ^ STATUS_KEYS))
        check("d0272_fix_b_shadow keeps its 4-key shape", set(mx["d0272_fix_b_shadow"]) == AGG_KEYS, mx["d0272_fix_b_shadow"])
        check("aggregate computed from the rows that carry the field (n=2 of 5; the None row and the key-less rows skipped)",
              mx["d0272_fix_b_shadow"] == {"n": 2, "mean_faithful": 0.85, "eligible_rate": 1.0, "current_eligible_rate_paired": 0.5},
              mx["d0272_fix_b_shadow"])
        check("status() logged count includes every row", mx["logged"] == 5, mx["logged"])
        check("status() on a log of ONLY new-format rows: aggregate is the empty shape, rest still computed",
              no["d0272_fix_b_shadow"] == {"n": 0, "mean_faithful": None, "eligible_rate": None, "current_eligible_rate_paired": None}
              and no["logged"] == 3 and no["mean_faithful"] == 0.817 and no["invented_claims"] == 1 and no["false_flags"] == 1,
              {k: no[k] for k in ("logged", "mean_faithful", "invented_claims", "false_flags", "d0272_fix_b_shadow")})
        check("status() on a missing log: the existing short default", st["missing"] == {"logged": 0, "mean_faithful": None, "recent": []}, st["missing"])

        # status() reading the rows this very run wrote through the real writer (new format on the new module)
        saved_log = ml._LOG
        ml._LOG = lab / "new__LOG.dat"
        try:
            real = ml.status()
        finally:
            ml._LOG = saved_log
        check("status() on the rows the real shadow_distill just wrote: logged=4 and the fix_b aggregate is the empty shape",
              real.get("logged") == 4 and set(real) == STATUS_KEYS
              and real["d0272_fix_b_shadow"] == {"n": 0, "mean_faithful": None, "eligible_rate": None, "current_eligible_rate_paired": None},
              {k: real.get(k) for k in ("logged", "d0272_fix_b_shadow")})

        # ---- optional: field-for-field comparison against a baseline copy ----------------------------
        if a.baseline:
            base = load_module(a.baseline)
            print("baseline module:", Path(base.__file__).resolve())
            b_out, b_rows, b_stubs, _ = run_module(base, "base_", lab)
            print(f"baseline calls: distil={len(b_stubs.distil)} grade={len(b_stubs.grade)} total={len(b_stubs.distil) + len(b_stubs.grade)}")
            b_by = {r["topic"]: r for r in b_rows}
            strip = lambda r, drop: {k: v for k, v in r.items() if k not in drop}
            same = (set(b_by) == set(by_topic)
                    and all(strip(by_topic[t], {"ts"}) == strip(b_by[t], {"ts", "fix_b_shadow"}) for t in by_topic))
            check("baseline rows are field-for-field identical to the new rows except ts and fix_b_shadow", same)
            check("baseline summary dict identical to the new summary dict", b_out == out, (b_out, out))
            check("baseline committed the same clusters", sorted(c[1][0] for c in b_stubs.commit) == sorted(c[1][0] for c in stubs.commit))
            check("baseline (pre-change) really did spend 2x the calls, so the comparison is meaningful",
                  len(b_stubs.distil) + len(b_stubs.grade) == 4 * out["clusters"], (len(b_stubs.distil), len(b_stubs.grade)))

    after = canary()
    check("canary: live shadow log / state / fetch-probe / row-count / drift files and the live DB untouched", before == after,
          {k: (before[k], after[k]) for k in before if before[k] != after[k]} or "all identical")
    print("RESULT:", "FAIL (" + ", ".join(FAILS) + ")" if FAILS else "ALL PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
