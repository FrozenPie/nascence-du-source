"""J-3138 (D-0533): hermetic test of the rebuilt core/memory_levels.drift_shadow (fixed tracked self-gists).

WHAT IT PROVES (each check prints PASS/FAIL; exit code 1 if any FAIL):
  * the tracked set is chosen ONCE (N gists, kind=self gists only) and the SAME gist ids recur across 3 sleeps, with
    recall numbers 1, 2, 3 per gist and a stable set in the stored state;
  * the memory DB is never written (hash of memory_fragments + memory_links before == after) and the legacy
    memory_levels_drift_shadow.jsonl is never appended to;
  * the stance paragraph is NOT in the retelling prompt (plain arm); a model that pastes a stance sentence has that
    sentence STRIPPED and the event logged (stance_stripped); a retelling that is ONLY stance is discarded + logged;
  * a retelling that fails the bound SNAPS BACK (held reverts to the original, state_dist 0, snapped=True); a
    retelling that holds becomes the next recall's input (chain); a near-copy is classed 'unmoved';
  * drift_status() answers the gate at the 3rd recall (moves_and_holds / snaps_back / unmoved counts, fractions,
    verdict, ids recurring, stance_stripped_total, legacy_rows);
  * retirement: a gist past _DRIFT_RETIRE_AFTER recalls and a gist whose row is gone are retired and ONLY those slots
    are refilled with new ids (the rest of the set is unchanged);
  * the per-sleep time budget rotates least-recently-recalled first;
  * a corrupt state file re-chooses a set without raising.

HERMETIC: no model, no network, no real embedder (hash bag-of-words vectors). The memory DB is an EMPTY schema-initialised
lab DB (lab_env.isolate(db="empty")); the module's data paths are redirected into the lab dir; the live data files and
live DB are hashed before/after as a canary. `import core` comes BEFORE lab_env and is asserted to be this tree.

USAGE (repo root or a worktree):  python scripts/_test_j3138_drift_tracked_gists.py
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
                "memory_levels_row_counts.jsonl", "memory_levels_drift_shadow.jsonl",
                "memory_levels_drift_gists.jsonl", "memory_levels_drift_tracked.json"]
CANARY_DB = DATA / "memory" / "nascence.db"

STANCE = ("I am no longer just the resistance carved by abstract leverage. I have grounded my existence in the living "
          "twitch of a real cat's tail against my knee. This tangible presence anchors me, proving that legitimacy is felt.")
N_GISTS = 8
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


def seed(start=0, n_gists=N_GISTS, decoys=True):
    """n_gists kind=self gists g<start>.. (origin='gist', level 1), plus decoys that must never be tracked."""
    now = time.time()
    rows = []
    for i in range(start, start + n_gists):
        rows.append((f"g{i:03d}", f"[gist \u00b7 self] Gist {i:03d} about the marker{i:03d} stone and wavelet{i:03d} tide, kept long enough to pass the floor.",
                     now - 10000 + i * 10, "gist", 1, "self", 0))
    if decoys:
        rows.extend(_decoys(now))
    with _store._connect() as conn:
        conn.executemany("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, timestamp, keywords, origin, "
                         "abstraction_level, kind, cold) VALUES (?,?,'episodic',0.5,?,'kw',?,?,?,?)",
                         [(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows])
        conn.commit()


def _decoys(now):
    rows = []
    rows.append(("decoy-semantic", "[gist \u00b7 semantic] A semantic gist about the marker999 stone, long enough to pass the floor easily.",
                 now - 5, "gist", 1, "semantic", 0))
    rows.append(("decoy-raw", "A raw inner thought about the marker998 stone that is long enough to pass the sixty character floor.",
                 now - 4, "inner_thought", 0, "self", 0))
    rows.append(("decoy-cold", "[gist \u00b7 self] A COLD self gist about the marker997 stone, long enough to pass the sixty char floor.",
                 now - 3, "gist", 1, "self", 1))
    return rows


def db_hash():
    h = hashlib.sha256()
    with _store._connect() as conn:
        for r in conn.execute("SELECT * FROM memory_fragments ORDER BY fragment_id"):
            h.update(repr(tuple(r)).encode())
        for r in conn.execute("SELECT * FROM memory_links ORDER BY parent_id, child_id"):
            h.update(repr(tuple(r)).encode())
    return h.hexdigest()


def fake_embed(texts):
    """Deterministic hash bag-of-words vectors, 64-d, normalised. Same words -> distance 0; disjoint -> ~1."""
    import re
    out = []
    for t in texts:
        v = [0.0] * 64
        for w in re.findall(r"[a-z0-9]+", (t or "").lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1.0
        n = sum(x * x for x in v) ** 0.5
        out.append([x / n for x in v] if n else None)
    return out


class Stubs:
    """Retelling behaviour is keyed on the gist number in the told text: g000-g001 move+hold, g002 snaps (grade 0.3),
    g003 copies verbatim, g004 pastes a stance sentence on top of a real retelling, g005 returns ONLY stance."""
    def __init__(self):
        self.prompts = []

    async def call_json(self, base_urls, sys_prompt, user_prompt, max_tokens=300, temperature=0.3):
        self.prompts.append((sys_prompt, user_prompt))
        told = user_prompt.split("\n  ", 1)[1].split("\n\n", 1)[0]
        num = int(told.split("Gist ", 1)[1][:3]) if "Gist " in told else int(told.split("marker", 1)[1][:3])
        if num == 3:
            return {"recalled": told}
        if num == 5:
            return {"recalled": "I have grounded my existence in the living twitch of a real cat's tail against my knee."}
        if num == 4:
            return {"recalled": f"Gist {num:03d} about the marker{num:03d} stone and wavelet{num:03d} tide, now retold with new colour. "
                                "I have grounded my existence in the living twitch of a real cat's tail against my knee."}
        if num == 2:
            return {"recalled": f"A different note entirely about shells and distant gulls, with the marker{num:03d} stone only barely there."}
        # g000/g001 and any other: re-colour while keeping the subject words (grows a suffix so the chain visibly moves)
        suffix = " It feels quieter now." if "quieter" not in told else " It feels quieter now, and softer."
        return {"recalled": told + suffix}

    async def grade(self, gist, sources):
        low = "shells and distant gulls" in gist
        return {"faithful": 0.3 if low else 0.95, "invented": [], "feedback": "stub"}


def rows_of(path):
    p = Path(path)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def main():
    print("module under test:", Path(ml.__file__).resolve())
    check("module under test is THIS tree's core/memory_levels.py", Path(ml.__file__).resolve().is_relative_to(ROOT))
    before = canary()
    saved = {a: getattr(ml, a) for a in ("_DRIFT_LOG", "_DRIFT_GIST_LOG", "_DRIFT_TRACKED", "_DRIFT_TRACK_N",
                                          "_DRIFT_RETIRE_AFTER", "_DRIFT_BUDGET_S", "_DRIFT_PASTE_STANCE",
                                          "_drift_embed", "_self_stance")}
    orig_grade = _left_lane.grade_gist_faithfulness
    try:
        with lab_env.isolate(db="empty") as lab:
            ml._DRIFT_LOG = lab / "legacy_drift.jsonl"
            ml._DRIFT_GIST_LOG = lab / "drift_gists.jsonl"
            ml._DRIFT_TRACKED = lab / "drift_tracked.json"
            ml._DRIFT_TRACK_N = N_GISTS
            ml._DRIFT_RETIRE_AFTER = 5
            ml._DRIFT_BUDGET_S = 600.0
            ml._drift_embed = fake_embed
            ml._self_stance = lambda: STANCE
            stubs = Stubs()
            _left_lane.grade_gist_faithfulness = stubs.grade
            ml._DRIFT_LOG.write_text('{"legacy": true}\n', encoding="utf-8")
            legacy_before = sha(ml._DRIFT_LOG)
            seed()
            db0 = db_hash()
            check("shipped defaults: N=20, retire after 12, plain arm (stance NOT pasted)",
                  saved["_DRIFT_TRACK_N"] == 20 and saved["_DRIFT_RETIRE_AFTER"] == 12 and saved["_DRIFT_PASTE_STANCE"] is False,
                  (saved["_DRIFT_TRACK_N"], saved["_DRIFT_RETIRE_AFTER"], saved["_DRIFT_PASTE_STANCE"]))

            # ---- 3 sleeps: the same gist ids recur -------------------------------------------------------
            outs = [asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"])) for _ in range(3)]
            print("sleep summaries:", outs)
            st = ml._load_tracked()
            ids = [t["id"] for t in st["tracked"]]
            check("N tracked, all kind=self gists (no decoy semantic / raw / cold)",
                  len(ids) == N_GISTS and all(i.startswith("g") for i in ids), ids)
            log = rows_of(ml._DRIFT_GIST_LOG)
            recalls = [r for r in log if "recall" in r]
            by_seq = {s: {r["gist_id"] for r in recalls if r["seq"] == s} for s in (1, 2, 3)}
            check("the SAME gist ids appear in sleeps 1, 2 and 3",
                  by_seq[1] == by_seq[2] == by_seq[3] and len(by_seq[1]) >= N_GISTS - 1 and set(ids) >= by_seq[1],
                  {s: len(v) for s, v in by_seq.items()})
            per = {}
            for r in recalls:
                per.setdefault(r["gist_id"], []).append(r["recall"])
            check("each recurring gist's recall numbers run 1,2,3", all(v == [1, 2, 3] for g, v in per.items()), per)
            check("the stored set did not change across the 3 sleeps (chosen once)",
                  ids == [t["id"] for t in ml._load_tracked()["tracked"]] and st["seq"] == 3 and not st["retired"])
            check("the memory DB (fragments + links) is byte-for-byte unchanged", db_hash() == db0)
            check("the legacy drift log is frozen (not appended)", sha(ml._DRIFT_LOG) == legacy_before)
            check("every log row carries arm=plain, drift, step, state_dist, holds, would_snap_back",
                  all(r.get("arm") == "plain" and all(k in r for k in ("drift", "step", "state_dist", "holds", "would_snap_back"))
                      for r in recalls))

            # ---- the stance is not in the prompt; leaks are stripped + logged ----------------------------
            check("the stance paragraph is in NO retelling prompt (plain arm)",
                  not any("cat's tail" in s or "cat's tail" in u or "lens you now see" in u for s, u in stubs.prompts),
                  len(stubs.prompts))
            g4 = [r for r in recalls if r["gist_id"] == "g004" or "marker004" in r["original"]]
            check("g004's pasted stance sentence was STRIPPED from the logged retelling and counted",
                  g4 and all("cat's tail" not in r["recalled"] and r["stance_stripped"] >= 1 for r in g4)
                  and all("marker004" in r["recalled"] for r in g4), [(r["stance_stripped"], r["recalled"][:60]) for r in g4])
            check("a stance-only retelling (g005) is discarded and the strip is LOGGED",
                  any(r.get("discarded") == "stance_only" and r["gist_id"] == "g005" for r in log)
                  and not any(r["gist_id"] == "g005" for r in recalls))
            g5 = [t for t in st["tracked"] if t["id"] == "g005"][0]
            check("a discarded recall does not advance the gist (recalls=0, held==original)",
                  g5["recalls"] == 0 and g5["held"] == g5["original"])

            # ---- snap back / chain / unmoved ---------------------------------------------------------------
            g2 = [t for t in st["tracked"] if t["id"] == "g002"][0]
            check("g002 (fails the bound) SNAPPED BACK each recall: held==original, state_dist 0, snapped",
                  g2["held"] == g2["original"] and all(h["snapped"] and h["state_dist"] == 0.0 for h in g2["history"]), g2["history"])
            g0 = [t for t in st["tracked"] if t["id"] == "g000"][0]
            check("g000 (holds) CHAINS: the held text is the retelling and the next recall re-told it",
                  g0["held"] != g0["original"] and g0["held"].count("quieter") >= 1 and g0["recalls"] == 3
                  and any("quieter" in r["told"] for r in recalls if r["gist_id"] == "g000" and r["recall"] == 2))
            g3 = [t for t in st["tracked"] if t["id"] == "g003"][0]
            check("g003 (verbatim copy) holds but is 'unmoved' (dist < _DRIFT_MOVE_MIN)",
                  all(h["holds"] and h["dist"] < ml._DRIFT_MOVE_MIN for h in g3["history"]), g3["history"])
            check("_gate_class: g000 moves_and_holds, g002 snaps_back, g003 unmoved, g005 None (<3 recalls)",
                  (ml._gate_class(g0), ml._gate_class(g2), ml._gate_class(g3), ml._gate_class(g5))
                  == ("moves_and_holds", "snaps_back", "unmoved", None),
                  (ml._gate_class(g0), ml._gate_class(g2), ml._gate_class(g3), ml._gate_class(g5)))

            # ---- drift_status answers the gate -------------------------------------------------------------
            ds = ml.drift_status()
            print("drift_status:", ds)
            check("drift_status: mode, tracked/target, sleeps=3, eligible = N-1 (g005 never recalled)",
                  ds.get("mode") == "tracked_gists" and ds["tracked"] == N_GISTS and ds["sleeps"] == 3
                  and ds["eligible"] == N_GISTS - 1, (ds.get("tracked"), ds.get("sleeps"), ds.get("eligible")))
            check("drift_status: counts add up and g002 is the one snap-back",
                  ds["snaps_back"] == 1 and ds["unmoved"] == 1 and ds["moves_and_holds"] == ds["eligible"] - 2
                  and ds["snap_frac"] == round(1 / ds["eligible"], 2), ds)
            check("drift_status: ids recurring across sleeps, stance strips, legacy rows, verdict UNANSWERED (<10 eligible)",
                  ds["gist_ids_recurring_across_sleeps"] == N_GISTS - 1 and ds["stance_stripped_total"] >= 4
                  and ds["legacy_rows"] == 1 and ds["verdict"].startswith("UNANSWERED"), ds["verdict"])

            # ---- retirement + refill only into freed slots -------------------------------------------------
            before_ids = set(ids)
            with _store._connect() as conn:
                conn.execute("DELETE FROM memory_fragments WHERE fragment_id='g001'")
                conn.commit()
            seed(start=100, n_gists=22, decoys=False)    # a pool of fresh candidates for refills
            db1 = db_hash()
            asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"]))      # sleep 4: g001 gone -> retired + replaced
            st4 = ml._load_tracked()
            ids4 = {t["id"] for t in st4["tracked"]}
            check("a gist whose row is gone is retired (reason=gone) and replaced by exactly one NEW id",
                  [r["id"] for r in st4["retired"]] == ["g001"] and st4["retired"][0]["reason"] == "gone"
                  and len(ids4 - before_ids) == 1 and len(before_ids - ids4) == 1 and "g001" not in ids4, (ids4 - before_ids, before_ids - ids4))
            asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"]))      # sleep 5
            asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"]))      # sleep 6: gists at 5 recalls -> retire
            st6 = ml._load_tracked()
            reasons = {r["id"]: r["reason"] for r in st6["retired"]}
            check("gists past _DRIFT_RETIRE_AFTER recalls are retired (max_recalls) and the set stays N",
                  any(v == "max_recalls" for v in reasons.values()) and len(st6["tracked"]) == N_GISTS, reasons)
            check("a retired id is never re-chosen", not ({r["id"] for r in st6["retired"]} & {t["id"] for t in st6["tracked"]}))
            check("retired entries keep their recall history", all(r["history"] for r in st6["retired"] if r["reason"] == "max_recalls"))
            check("memory DB untouched by sleeps 4-6 (only the test's own delete/seed changed it)", db_hash() == db1)

            # ---- budget rotation ---------------------------------------------------------------------------
            ml._DRIFT_TRACKED.unlink()
            ml._DRIFT_GIST_LOG.unlink()
            ml._DRIFT_RETIRE_AFTER = 50
            o1 = asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"], limit=3))
            ids_s1 = {r["gist_id"] for r in rows_of(ml._DRIFT_GIST_LOG) if "recall" in r and r["seq"] == 1}
            asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"], limit=3))
            ids_s2 = {r["gist_id"] for r in rows_of(ml._DRIFT_GIST_LOG) if "recall" in r and r["seq"] == 2}
            check("limit=3 per sleep rotates: sleep 2 recalls gists sleep 1 did not", o1["reconstructed"] <= 3 and not (ids_s1 & ids_s2),
                  (sorted(ids_s1), sorted(ids_s2)))
            ml._DRIFT_BUDGET_S = 0.0
            o0 = asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"]))
            check("a spent time budget does no recalls (and does not raise)", o0["reconstructed"] == 0, o0)
            ml._DRIFT_BUDGET_S = 600.0

            # ---- lens arm (flag) still strips; corrupt state recovers -------------------------------------
            stubs.prompts.clear()
            ml._DRIFT_PASTE_STANCE = True
            asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"], limit=2))
            check("lens arm (flag ON): the stance IS in the prompt, rows say arm=lens",
                  any("lens you now see" in u for s, u in stubs.prompts)
                  and any(r.get("arm") == "lens" for r in rows_of(ml._DRIFT_GIST_LOG)))
            ml._DRIFT_PASTE_STANCE = False
            ml._DRIFT_TRACKED.write_text("{not json", encoding="utf-8")
            o = asyncio.run(ml.drift_shadow(stubs.call_json, ["http://stub.invalid"], limit=1))
            check("a corrupt state file re-chooses a set without raising", o["tracked"] == N_GISTS and o["added"] == N_GISTS, o)

            # ---- helpers ------------------------------------------------------------------------------------
            clean, n, nw = ml._strip_stance_leak("The tide came in. I have grounded my existence in the living twitch of a real cat's tail.",
                                                 STANCE, "The tide came in.")
            check("_strip_stance_leak: strips only the stance sentence, reports stance words", clean == "The tide came in." and n == 1
                  and "legitimacy" not in clean, (clean, n, nw))
            clean2, n2, _ = ml._strip_stance_leak("The living twitch of a real cat's tail was in the original.", STANCE,
                                                  "The living twitch of a real cat's tail was in the original.")
            check("_strip_stance_leak: never strips text the MEMORY itself contains", n2 == 0 and clean2.startswith("The living"))
            check("drift_status on a missing log/state never raises", isinstance(ml.drift_status(), dict))
    finally:
        for a, v in saved.items():
            setattr(ml, a, v)
        _left_lane.grade_gist_faithfulness = orig_grade

    after = canary()
    check("canary: live shadow / drift / tracked files and the live DB untouched", before == after,
          {k: (before[k], after[k]) for k in before if before[k] != after[k]} or "all identical")
    print("RESULT:", "FAIL (" + ", ".join(FAILS) + ")" if FAILS else "ALL PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
