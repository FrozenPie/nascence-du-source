"""J-3176 (D-0564): hermetic test of core/memory_levels EPISODIC_DEMOTION_PAUSED.

WHAT IT PROVES (each check prints PASS/FAIL; exit code 1 if any FAIL):
  * pause ON (the shipped default): an eligible 'episodic' gist is still distilled, graded, STORED (origin='gist')
    and LINKED (distilled_from) -- but its raw children stay cold=0. Self and semantic gists demote their raw to
    cold=1 exactly as before. An ineligible episodic cluster (below the floor) writes nothing.
  * the summary dict carries held_gists / held_raw for the episodic hold and `demoted` counts ONLY the cold-gated
    kinds; the shadow-log row of a held gist carries held_cold=True, no other row carries the key.
  * a cold row that was cold BEFORE the run is not un-colded (no un-cold in this job).
  * the per-run demotion cap does not apply to a held gist (cap forced to 0: self/semantic stop, episodic still
    writes its gist).
  * pause OFF: the same fixture demotes the episodic raw too (the old behaviour), no held_cold rows.
  * episodic_hold_status() reads the per-day count back from the log; phase1_status() reports the flag.

HERMETIC: no model, no network. The memory DB is an EMPTY schema-initialised lab DB (lab_env.isolate(db="empty"));
the real _commit_gist runs against it; the module's own data paths are redirected into the lab dir; the live data
files are hashed before and after as a canary. `import core` comes BEFORE lab_env and is asserted to be this tree.

USAGE (repo root or a worktree):  python scripts/_test_j3176_episodic_demotion_pause.py
"""
import asyncio
import hashlib
import json
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

# topic token -> faithful the stub judge returns
SCENARIO = {"zephyrine": 0.90, "quillon": 0.60, "marlowe": 0.90, "tamsin": 0.85}
# (topic, origin, n)   origin -> kind via ml._KIND: reading=semantic, inner_thought=self, lived=episodic
GROUPS = [("zephyrine", "reading", 4), ("tamsin", "lived", 3), ("marlowe", "inner_thought", 5), ("quillon", "lived", 3)]

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
            rows.append((f"j3176-{tok}-{k}", f"Fragment {k} about {tok}: stub source text {gi}{k} for the J-3176 test.",
                         "episodic", 0.5, now - 1000 + gi * 10 + k, f"{tok} uniq{gi}x{k}x", origin, 0))
    # a row that was ALREADY cold before the run, outside the raw origins so it is never clustered
    rows.append(("j3176-precold", "Already cold episodic row.", "episodic", 0.5, now - 5000, "precold", "dream_fade", 1))
    with _store._connect() as conn:
        conn.executemany("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, "
                         "origin, abstraction_level, cold) VALUES (?,?,?,?,?,?,?,0,?)", rows)
        conn.commit()


def reset_db():
    with _store._connect() as conn:
        conn.execute("DELETE FROM memory_links")
        conn.execute("DELETE FROM memory_fragments")
        conn.commit()
    seed()


class Stubs:
    async def call_json(self, base_urls, sys_prompt, user_prompt, max_tokens=300, temperature=0.3):
        topic = user_prompt.split("Topic: ", 1)[1].split(".", 1)[0]
        return {"gist": f"stub gist about {topic}: long enough to clear the forty character floor."}

    async def grade_gist_faithfulness(self, gist, sources):
        topic = gist.split(" about ", 1)[1].split(":", 1)[0]
        return {"faithful": SCENARIO[topic], "invented": [], "feedback": f"stub grade for {topic}"}


def run(lab, tag, paused, cap=None):
    """One shadow_distill over a freshly seeded lab DB. Returns (summary, log rows, {fragment_id: cold}, gist rows, links)."""
    reset_db()
    saved = {a: getattr(ml, a) for a in ("_STATE", "_LOG", "_FETCH_PROBE_LOG", "_ROW_COUNT_LOG", "_DRIFT_LOG",
                                          "EPISODIC_DEMOTION_PAUSED", "MAX_DEMOTE_PER_RUN")}
    for a in ("_STATE", "_LOG", "_FETCH_PROBE_LOG", "_ROW_COUNT_LOG", "_DRIFT_LOG"):
        setattr(ml, a, lab / f"{tag}{a}.dat")
    ml.EPISODIC_DEMOTION_PAUSED = paused
    if cap is not None:
        ml.MAX_DEMOTE_PER_RUN = cap
    stubs = Stubs()
    orig_grade = _left_lane.grade_gist_faithfulness
    _left_lane.grade_gist_faithfulness = stubs.grade_gist_faithfulness
    try:
        out = asyncio.run(ml.shadow_distill(stubs.call_json, ["http://stub.invalid"]))
        rows = [json.loads(l) for l in ml._LOG.read_text(encoding="utf-8").splitlines() if l.strip()] if ml._LOG.exists() else []
        hold = ml.episodic_hold_status()
        with _store._connect() as conn:
            cold = {r[0]: r[1] for r in conn.execute("SELECT fragment_id, cold FROM memory_fragments WHERE origin != 'gist'")}
            gists = [(r[0], r[1], r[2]) for r in conn.execute(
                "SELECT fragment_id, kind, content FROM memory_fragments WHERE origin='gist'")]
            links = [(r[0], r[1], r[2]) for r in conn.execute("SELECT parent_id, child_id, link_type FROM memory_links")]
        return out, rows, cold, gists, links, hold
    finally:
        _left_lane.grade_gist_faithfulness = orig_grade
        for a, v in saved.items():
            setattr(ml, a, v)


def cold_of(cold, tok):
    return sorted({v for k, v in cold.items() if k.startswith(f"j3176-{tok}-")})


def main():
    print("module under test:", Path(ml.__file__).resolve())
    check("module under test is THIS tree's core/memory_levels.py", Path(ml.__file__).resolve().is_relative_to(ROOT))
    check("EPISODIC_DEMOTION_PAUSED ships True", ml.EPISODIC_DEMOTION_PAUSED is True)
    before = canary()

    with lab_env.isolate(db="empty") as lab:
        # ---- pause ON ------------------------------------------------------------------------------
        out, rows, cold, gists, links, hold = run(lab, "on_", True)
        print("summary (pause ON):", out)
        check("fixture formed the 4 intended clusters", out["clusters"] == 4, out["clusters"])
        kinds = sorted(g[1] for g in gists)
        check("3 gists stored: semantic + self + the eligible episodic (the below-floor episodic writes none)",
              kinds == ["episodic", "self", "semantic"], kinds)
        check("episodic raw (tamsin) stays WARM (cold=0)", cold_of(cold, "tamsin") == [0], cold_of(cold, "tamsin"))
        check("episodic raw (tamsin) is still LINKED beneath its gist (distilled_from)",
              sum(1 for _, c, t in links if t == "distilled_from" and c.startswith("j3176-tamsin-")) == 3)
        check("semantic raw (zephyrine) demotes to cold=1 as before", cold_of(cold, "zephyrine") == [1], cold_of(cold, "zephyrine"))
        check("self raw (marlowe) demotes to cold=1 as before", cold_of(cold, "marlowe") == [1], cold_of(cold, "marlowe"))
        check("below-floor episodic raw (quillon) stays warm and unlinked",
              cold_of(cold, "quillon") == [0] and not any(c.startswith("j3176-quillon-") for _, c, _ in links))
        check("summary: demoted counts only the cold-gated kinds (4 semantic + 5 self)", out["demoted"] == 9, out["demoted"])
        check("summary: held_gists=1, held_raw=3", (out["held_gists"], out["held_raw"]) == (1, 3), (out["held_gists"], out["held_raw"]))
        held_rows = [r for r in rows if r.get("held_cold")]
        check("exactly one log row carries held_cold, and it is the episodic tamsin gist",
              len(held_rows) == 1 and held_rows[0]["kind"] == "episodic" and held_rows[0]["topic"] and "tamsin" in held_rows[0]["source_ids"][0],
              [(r["kind"], r["topic"]) for r in held_rows])
        check("rows without a hold carry exactly the old key set (no held_cold key)",
              all("held_cold" not in r for r in rows if not r.get("held_cold")))
        check("a row that was cold before the run is not un-colded", cold.get("j3176-precold") == 1, cold.get("j3176-precold"))
        # read-back: run() called episodic_hold_status() while the module's _LOG pointed at this run's log
        today = time.strftime("%Y-%m-%d")
        check("episodic_hold_status(): 1 gist / 3 raw, grouped under today's date",
              hold["paused"] is True and hold["total_gists"] == 1 and hold["total_raw"] == 3
              and hold["by_day"] == {today: {"gists": 1, "raw": 3}}, hold)
        saved_log = ml._LOG
        ml._LOG = lab / "j3176_no_such_log.jsonl"
        try:
            empty = ml.episodic_hold_status()
        finally:
            ml._LOG = saved_log
        check("episodic_hold_status() on a missing log: empty shape",
              empty == {"paused": True, "total_gists": 0, "total_raw": 0, "by_day": {}}, empty)
        p1 = ml.phase1_status()
        check("phase1_status() reports episodic_paused", p1.get("episodic_paused") is True and "enabled" in p1, p1)

        # ---- cap does not bind a held gist ---------------------------------------------------------
        out_c, _, cold_c, gists_c, _, _ = run(lab, "cap_", True, cap=0)
        print("summary (pause ON, cap=0):", out_c)
        check("cap=0: no cold-gated gist commits (demoted=0)", out_c["demoted"] == 0, out_c["demoted"])
        check("cap=0: the held episodic gist is still written", out_c["held_gists"] == 1 and any(g[1] == "episodic" for g in gists_c))
        check("cap=0: nothing at all went cold", all(v == 0 for k, v in cold_c.items() if k != "j3176-precold"))

        # ---- pause OFF -----------------------------------------------------------------------------
        out_o, rows_o, cold_o, gists_o, _, _ = run(lab, "off_", False)
        print("summary (pause OFF):", out_o)
        check("pause OFF: episodic raw (tamsin) demotes again (old behaviour)", cold_of(cold_o, "tamsin") == [1], cold_of(cold_o, "tamsin"))
        check("pause OFF: demoted = 4 + 3 + 5 = 12, held 0/0", (out_o["demoted"], out_o["held_gists"], out_o["held_raw"]) == (12, 0, 0),
              (out_o["demoted"], out_o["held_gists"], out_o["held_raw"]))
        check("pause OFF: no row carries held_cold", not any(r.get("held_cold") for r in rows_o))

    after = canary()
    check("canary: live shadow log / state / fetch-probe / row-count / drift files and the live DB untouched", before == after,
          {k: (before[k], after[k]) for k in before if before[k] != after[k]} or "all identical")
    print("RESULT:", "FAIL (" + ", ".join(FAILS) + ")" if FAILS else "ALL PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
