"""J-3212 (D-0601): hermetic test of core/memory_levels SELF_GIST_FIRST_PERSON.

WHAT IT PROVES (each check prints PASS/FAIL; exit code 1 if any FAIL):
  * flag ON (the shipped default): the distil call for a kind='self' cluster gets the first-person system prompt; the
    semantic and episodic clusters still get the production (third-person) prompt byte-for-byte; the user line is the same
    for every arm.
  * flag OFF: every cluster gets the production prompt (the old behaviour), no row carries a `voice` key.
  * the shadow-log row of a self gist written under the flag carries voice='first'; no other row carries the key.
  * everything downstream is unchanged by the flag: same clusters, same stored gists, same demotion counts, same
    held_cold accounting as with the flag off (the prompt is the ONLY difference).
  * the production prompt literal (`_sys` in shadow_distill) is exactly the text the lab's arm A reads; the lab's arm B
    text equals core's _SELF_FIRST_PERSON_SYS (no drift between what was measured and what ships).
  * the first-person prompt says whose the fragments are and asks for the first person, and contains no instruction about
    what to conclude (no 'should', 'must feel', 'believe', 'you are') -- founder law: the prompt is internal consolidation, not
    a message to Du, and the world answers and never leads.
  * self_voice_status() reads the split back from the log; on a missing log it returns the empty shape.

HERMETIC: no model, no network. The memory DB is an EMPTY schema-initialised lab DB (lab_env.isolate(db="empty")); the module's
own data paths are redirected into the lab dir; the live data files are hashed before and after as a canary. `import core`
comes BEFORE lab_env and is asserted to be this tree.

USAGE (repo root or a worktree):  python scripts/_test_j3212_selfgist_first_person.py
"""
import asyncio
import hashlib
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                             # noqa: E402  (BEFORE lab_env, on purpose)
from core.memory import store as _store                # noqa: E402
from core import left_lane as _left_lane               # noqa: E402
from core import memory_levels as ml                   # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
import lab_env                                          # noqa: E402

assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
assert Path(ml.__file__).resolve().is_relative_to(ROOT), ml.__file__

DATA = ROOT / "data" if (ROOT / "data" / "night_log.jsonl").exists() else Path(r"C:\Nascence\data")
CANARY_FILES = ["memory_levels_shadow.jsonl", "memory_levels_shadow_state.json", "memory_levels_fetch_probe.jsonl",
                "memory_levels_row_counts.jsonl", "memory_levels_drift_shadow.jsonl"]
CANARY_DB = DATA / "memory" / "nascence.db"

SCENARIO = {"zephyrine": 0.90, "marlowe": 0.90, "tamsin": 0.85}
# (topic, origin, n)   origin -> kind via ml._KIND: reading=semantic, inner_thought=self, lived=episodic
GROUPS = [("zephyrine", "reading", 4), ("tamsin", "lived", 3), ("marlowe", "inner_thought", 5)]

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


def seed():
    now = time.time()
    rows = []
    for gi, (tok, origin, n) in enumerate(GROUPS):
        for k in range(n):
            rows.append((f"j3212-{tok}-{k}", f"Fragment {k} about {tok}: stub source text {gi}{k} for the J-3212 test.",
                         "episodic", 0.5, now - 1000 + gi * 10 + k, f"{tok} uniq{gi}x{k}x", origin))
    with _store._connect() as conn:
        conn.executemany("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, "
                         "origin, abstraction_level, cold) VALUES (?,?,?,?,?,?,?,0,0)", rows)
        conn.commit()


def reset_db():
    with _store._connect() as conn:
        conn.execute("DELETE FROM memory_links")
        conn.execute("DELETE FROM memory_fragments")
        conn.commit()
    seed()


class Stubs:
    def __init__(self):
        self.calls = []        # (kind, system prompt, user prompt)

    async def call_json(self, base_urls, sys_prompt, user_prompt, max_tokens=300, temperature=0.3):
        kind = user_prompt.split("Kind: ", 1)[1].split(".", 1)[0]
        topic = user_prompt.split("Topic: ", 1)[1].split(".", 1)[0]
        self.calls.append((kind, sys_prompt, user_prompt))
        return {"gist": f"stub gist about {topic}: long enough to clear the forty character floor."}

    async def grade_gist_faithfulness(self, gist, sources):
        topic = gist.split(" about ", 1)[1].split(":", 1)[0]
        return {"faithful": SCENARIO[topic], "invented": [], "feedback": f"stub grade for {topic}"}


def run(lab, tag, first_person):
    reset_db()
    names = ("_STATE", "_LOG", "_FETCH_PROBE_LOG", "_ROW_COUNT_LOG", "_DRIFT_LOG", "SELF_GIST_FIRST_PERSON")
    saved = {a: getattr(ml, a) for a in names}
    for a in names[:5]:
        setattr(ml, a, lab / f"{tag}{a}.dat")
    ml.SELF_GIST_FIRST_PERSON = first_person
    stubs = Stubs()
    orig_grade = _left_lane.grade_gist_faithfulness
    _left_lane.grade_gist_faithfulness = stubs.grade_gist_faithfulness
    try:
        out = asyncio.run(ml.shadow_distill(stubs.call_json, ["http://stub.invalid"]))
        rows = [json.loads(l) for l in ml._LOG.read_text(encoding="utf-8").splitlines() if l.strip()] if ml._LOG.exists() else []
        voice = ml.self_voice_status(days=1)
        with _store._connect() as conn:
            cold = {r[0]: r[1] for r in conn.execute("SELECT fragment_id, cold FROM memory_fragments WHERE origin != 'gist'")}
            gists = sorted((r[0], r[1]) for r in conn.execute("SELECT kind, content FROM memory_fragments WHERE origin='gist'"))
        return out, rows, cold, gists, stubs.calls, voice
    finally:
        _left_lane.grade_gist_faithfulness = orig_grade
        for a, v in saved.items():
            setattr(ml, a, v)


def main():
    print("module under test:", Path(ml.__file__).resolve())
    check("module under test is THIS tree's core/memory_levels.py", Path(ml.__file__).resolve().is_relative_to(ROOT))
    check("SELF_GIST_FIRST_PERSON ships True", ml.SELF_GIST_FIRST_PERSON is True)
    before = canary()

    # ---- the prompt texts -------------------------------------------------------------------------
    lab_spec = importlib.util.spec_from_file_location("lab_selfgist_voice", ROOT / "scripts" / "lab_selfgist_voice.py")
    lab_mod = importlib.util.module_from_spec(lab_spec)
    lab_spec.loader.exec_module(lab_mod)
    prod_sys = lab_mod.arm_a()
    check("lab arm A is read from the production literal and is the third-person distil prompt",
          prod_sys.startswith("/no_think\nThese are raw memory fragments of one kind, on one topic. Distil them into ONE")
          and "first person" not in prod_sys, prod_sys[:80])
    check("lab arm B text == core _SELF_FIRST_PERSON_SYS (what was measured is what ships)",
          lab_mod.ARM_B == ml._SELF_FIRST_PERSON_SYS)
    p = ml._SELF_FIRST_PERSON_SYS
    check("first-person prompt says the fragments are his own thoughts and asks for the first person",
          "your own earlier thoughts" in p and "first person" in p and "Output ONLY JSON" in p)
    check("first-person prompt gives no instruction about what to conclude or feel",
          not re.search(r"\b(should|must feel|believe|you are|you should|remember that)\b", p, re.I), p)
    check("first-person prompt keeps the production guard rails (invent nothing, 2-4 sentences, not a list)",
          "invent nothing" in p and "2-4 sentences" in p and "NOT a list of them" in p)

    with lab_env.isolate(db="empty") as lab:
        # ---- flag ON ----------------------------------------------------------------------------
        on, rows_on, cold_on, gists_on, calls_on, voice_on = run(lab, "on_", True)
        print("summary (flag ON):", on)
        by_kind = {k: s for k, s, u in calls_on}
        check("3 clusters distilled (semantic, self, episodic)", sorted(by_kind) == ["episodic", "self", "semantic"], sorted(by_kind))
        check("self cluster got the FIRST-PERSON prompt", by_kind.get("self") == ml._SELF_FIRST_PERSON_SYS)
        check("semantic cluster got the production prompt byte-for-byte", by_kind.get("semantic") == prod_sys)
        check("episodic cluster got the production prompt byte-for-byte", by_kind.get("episodic") == prod_sys)
        check("user line has the same shape for every kind (Kind/Topic + '- ' bullets)",
              all(re.match(r"Kind: \w+\. Topic: \w+\.\n\n- ", u) for _, _, u in calls_on))
        tagged = [r for r in rows_on if r.get("voice")]
        check("exactly one log row carries voice='first', and it is the self gist",
              len(tagged) == 1 and tagged[0]["kind"] == "self" and tagged[0]["voice"] == "first", [(r["kind"], r.get("voice")) for r in rows_on])
        check("self_voice_status(): 1 new-prompt self row, 0 old, reads the logged gist text",
              voice_on["enabled"] is True and voice_on["first"]["rows"] == 1 and voice_on["old"]["rows"] == 0, voice_on)

        # ---- flag OFF ---------------------------------------------------------------------------
        off, rows_off, cold_off, gists_off, calls_off, voice_off = run(lab, "off_", False)
        print("summary (flag OFF):", off)
        check("flag OFF: every cluster got the production prompt", all(s == prod_sys for _, s, _ in calls_off), len(calls_off))
        check("flag OFF: no row carries a voice key", not any("voice" in r for r in rows_off))
        check("flag OFF: self_voice_status() counts the self row as old-prompt",
              voice_off["enabled"] is False and voice_off["first"]["rows"] == 0 and voice_off["old"]["rows"] == 1, voice_off)

        # ---- nothing else moves -----------------------------------------------------------------
        keys = ("clusters", "graded", "demoted", "held_gists", "held_raw", "mean_faithful")
        check("flag ON vs OFF: identical summary (clusters, graded, demoted, held, mean_faithful)",
              all(on[k] == off[k] for k in keys), {k: (on[k], off[k]) for k in keys})
        check("flag ON vs OFF: identical cold-gating of the raw rows", cold_on == cold_off)
        check("flag ON vs OFF: same stored gist kinds", [k for k, _ in gists_on] == [k for k, _ in gists_off], [k for k, _ in gists_on])
        strip = lambda rs: [{k: v for k, v in r.items() if k not in ("ts", "voice")} for r in rs]
        check("flag ON vs OFF: log rows identical apart from ts and the voice tag", strip(rows_on) == strip(rows_off))

        # ---- reader on real-shaped text ---------------------------------------------------------
        saved_log = ml._LOG
        ml._LOG = lab / "j3212_voice_log.jsonl"
        now = time.time()
        fixture = [
            {"ts": now, "kind": "self", "gist": "The narrator reflects on frustration in the ribs.", "voice": None},
            {"ts": now, "kind": "self", "gist": "The speaker finds arithmetic heavy.", "voice": None},
            {"ts": now, "kind": "self", "gist": "I keep returning to the cold slate and my pen.", "voice": "first"},
            {"ts": now, "kind": "self", "gist": "My mind drifts to the book, and I let it.", "voice": "first"},
            {"ts": now, "kind": "self", "gist": "The sums wait on the slate.", "voice": "first"},
            {"ts": now - 30 * 86400, "kind": "self", "gist": "The author is too old to count.", "voice": None},
            {"ts": now, "kind": "semantic", "gist": "The narrator of a semantic gist is not counted.", "voice": None},
        ]
        ml._LOG.write_text("\n".join(json.dumps({k: v for k, v in r.items() if v is not None}) for r in fixture) + "\n", encoding="utf-8")
        try:
            sv = ml.self_voice_status(days=7)
            ml._LOG = lab / "j3212_no_such_log.jsonl"
            empty = ml.self_voice_status(days=7)
        finally:
            ml._LOG = saved_log
        check("self_voice_status(): old arm = 2 rows, both open third-person, none first-person",
              sv["old"] == {"rows": 2, "third_person_open_share": 1.0, "first_person_marker_share": 0.0}, sv["old"])
        check("self_voice_status(): new arm = 3 rows, 0 third-person openers, 2/3 with I/my (the 3rd stays third-person)",
              sv["first"] == {"rows": 3, "third_person_open_share": 0.0, "first_person_marker_share": 0.667}, sv["first"])
        check("self_voice_status(): rows older than the window and other kinds are not counted", sv["first"]["rows"] + sv["old"]["rows"] == 5)
        check("self_voice_status() on a missing log: empty shape",
              empty["first"] == {"rows": 0} and empty["old"] == {"rows": 0}, empty)

    after = canary()
    check("canary: live shadow log / state / fetch-probe / row-count / drift files and the live DB untouched", before == after,
          {k: (before[k], after[k]) for k in before if before[k] != after[k]} or "all identical")
    print("RESULT:", "FAIL (" + ", ".join(FAILS) + ")" if FAILS else "ALL PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
