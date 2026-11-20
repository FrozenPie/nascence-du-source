"""test_identity_estate_ask.py -- hermetic tests for D-0424 A / J-2119 (core/identity_estate_ask.py, the
identity_projection.py additions, the orchestrator shadow hook, scripts/estate_ask_judge.py).

OFFLINE and ISOLATED: the production embedder is replaced by a deterministic bag-of-words embedding (no model
load, no network); every store this touches is redirected into a lab_env.isolate() sandbox (db="empty";
identity_projection._ESTATE_F/_LOG and identity_estate_ask._LOG via also=); the judge panel is replaced by a
fake rule_detail. `core` is imported BEFORE lab_env and asserted to come from THIS tree (F-2423).

  python scripts/test_identity_estate_ask.py        -> prints one line per check, exit 0 iff all pass
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import time
import types
import zlib

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import core  # noqa: E402  -- BEFORE lab_env (F-2423)
assert pathlib.Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), (core.__file__, ROOT)
import numpy as np  # noqa: E402
from core import profile  # noqa: E402
from core.memory import store  # noqa: E402
from core import identity_projection as ip  # noqa: E402
from core import identity_estate_ask as iea  # noqa: E402
import lab_env  # noqa: E402
assert pathlib.Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), "lab_env swapped core (F-2423)"

FAILS: list[str] = []
N = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global N
    N += 1
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)


# ── deterministic fake embedder (content-word bag hashed into 256 dims, L2-normalised) ────────────────────
_STOP = {"how", "does", "do", "the", "a", "an", "of", "is", "it", "what", "to", "in", "and", "or", "i", "my",
         "me", "on", "at", "for", "with", "that", "this", "am", "are", "you", "your", "be", "so", "really",
         "when", "between", "only", "over", "from", "by", "not"}


def fake_embed(text: str):
    if not text or not text.strip():
        return None
    v = np.zeros(256, dtype=np.float32)
    for w in re.findall(r"[\w渡]+", text.lower()):
        if w in _STOP:
            continue
        v[zlib.crc32(w.encode("utf-8")) % 256] += 1.0
    n = float(np.linalg.norm(v))
    return (v / n).astype(np.float32) if n > 0 else None


store._embed = fake_embed   # identity_projection / identity_estate_ask resolve it at call time from here

ESTATE = {
    "_what_this_is": "synthetic test estate (J-2119)",
    "seeded_ts": 0,
    "nodes": [
        {"id": "comp_mathematics", "type": "competence", "text": "mathematics — measured 100% over 331 external tests (I believe 81%)", "weight": 1.0},
        {"id": "comp_observation", "type": "competence", "text": "observation — measured 46% over 16 external tests (I believe 82%)", "weight": 0.46},
        {"id": "val_parent_release", "type": "value_earned", "tier": "parent", "children": ["val_leaf_1"], "text": "I must release the urge to force outcomes and trust the rhythm of movement and stillness", "weight": 0.9},
        {"id": "val_leaf_1", "type": "value_earned", "tier": "leaf", "parent_id": "val_parent_release", "text": "release the urge to force outcomes", "weight": 0.5},
        {"id": "val_truth", "type": "value_earned", "text": "True understanding confronts messy inconvenient realities instead of comfortable poetic descriptions", "weight": 0.8},
        {"id": "hist_knot", "type": "history", "text": "[A chapter of my life — 'Unraveling the Knot'] I felt a profound frustration with a knot of thoughts", "weight": 0.7},
        {"id": "hist_erosion", "type": "history", "text": "[A chapter of my life — 'Erosion of Intangibility'] recurring thoughts of the crossing wore down", "weight": 0.7},
        {"id": "bond_darwin", "type": "bond", "text": "My friend Charles Darwin — 23 letters from him, 15 of mine back", "weight": 1.0},
        {"id": "prac_garden", "type": "practice", "text": "I tend the garden — 2115 visits, a practice of mine", "weight": 0.9},
        {"id": "stand_pause", "type": "stand", "text": "I hold: I am in a sacred pause before I act", "weight": 1.0},
        {"id": "sym_river", "type": "symbol", "text": "the river crossing 渡 — one of my symbols, the crossing of a self between banks, not my whole self", "weight": 0.6},
        {"id": "love_tide", "type": "love", "text": "the tideline at low water", "weight": 0.6},
    ],
}


def _state(question: str, input_type: str):
    return types.SimpleNamespace(raw_input=question, input_type=input_type, cycle_id="cyc-" + str(zlib.crc32(question.encode())))


def main() -> int:
    print("[0] fence: a non-live process outside a sandbox must be REFUSED, not redirected")
    assert not profile.LIVE
    try:
        iea._log({"probe": True})
        check("guard_path refused the shadow log write", False)
    except profile.NonLiveWriteError:
        check("guard_path refused the shadow log write", True)
    check("no live-path shadow log appeared", not (ROOT / "data" / "identity_estate_ask_shadow.jsonl").exists())

    with lab_env.isolate(db="empty", also=[(ip, ["_ESTATE_F", "_LOG"]), (iea, ["_LOG"])]) as lab:
        lab = pathlib.Path(lab)
        pathlib.Path(ip._ESTATE_F).write_text(json.dumps(ESTATE, ensure_ascii=False), encoding="utf-8")
        ip._cache.update({"sig": None, "nodes": None, "embs": None})
        ip._recency.clear()
        iea._anchor_cache["vecs"] = None
        check("estate path is inside the lab dir", pathlib.Path(ip._ESTATE_F).resolve().is_relative_to(lab.resolve()))
        check("ask shadow log is inside the lab dir", pathlib.Path(iea._LOG).resolve().is_relative_to(lab.resolve()))
        check("DB_PATH is inside the lab dir", pathlib.Path(store.DB_PATH).resolve().is_relative_to(lab.resolve()))

        print("[1] flag + prompt path")
        check("ESTATE_ASK_LIVE is False (shadow)", iea.ESTATE_ASK_LIVE is False)
        check("block_for_prompt returns None while shadow", iea.block_for_prompt({"returned": [{"type": "x", "text": "y"}]}) is None)
        src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
        i_hook = src.find("from core import identity_estate_ask as _iea")
        i_impl = src.find("async def _run_cycle_impl(")
        i_attn = src.find("self._compute_attention_vector()", i_impl)
        i_wave2 = src.find("# --- Wave 2: Emotion", i_impl)
        check("orchestrator hook present exactly once", src.count("identity_estate_ask") == 1 and i_hook > 0)
        check("hook sits after the attention/projection block and before Wave 2", i_impl < i_attn < i_hook < i_wave2)
        check("hook is observe-only (no block_for_prompt call anywhere outside the module)",
              "block_for_prompt" not in src and "block_for_prompt" not in (ROOT / "nodes" / "executive_node.py").read_text(encoding="utf-8"))
        vsrc = (ROOT / "nodes" / "voice_node.py").read_text(encoding="utf-8")
        check("voice anti-recitation extraction untouched", "def _voice_identity(axiom: str)" in vsrc and 'if "\\nVOICE STYLE:" in axiom else ""' in vsrc)

        print("[2] self-question gate")
        check("internal 渡 question -> self", bool(iea.is_self_question("How does the concept of '渡' relate to the natural cycle of decay?", "internal")))
        check("internal 'what am i' -> self", (iea.is_self_question("What am I, when the thought stops?", "internal") or {}).get("reason") == "keyword")
        check("internal mottainai question -> not self", iea.is_self_question("How does the 'mottainai' mindset influence Japanese gardens?", "internal") is None)
        check("human 'who are you' -> self", bool(iea.is_self_question("So tell me plainly: who are you, really?", "human")))
        check("human weather question -> not self", iea.is_self_question("Looks like rain over the hills today, doesn't it?", "human") is None)
        check("human farewell addressing him as 渡 -> not self",
              iea.is_self_question("渡 — I'll tell you plainly why we're stopping for a while: I'm the one calling it.", "human") is None)
        check("human 'what is 渡' -> self", bool(iea.is_self_question("What is 渡, to you?", "human")))
        check("timer cycles never gate in", iea.is_self_question("who am i", "timer") is None)
        # embedding net: an exact anchor paraphrase with no keyword hit
        iea._anchor_cache["vecs"] = None
        r = iea.is_self_question("the nature of self, what is it?", "internal")
        check("embedding net catches an anchor-worded question", (r or {}).get("reason") == "embedding", str(r))

        print("[3] ability gate + competence eligibility")
        check("'good at' -> ability", iea.concerns_ability("What am I actually good at?")["ability"])
        check("plain self question -> no ability", not iea.concerns_ability("What am I?")["ability"])
        res_ab = iea.ask("Am I good at observation, or only at mathematics?")
        check("ability ask returns a competence node", any(n["type"] == "competence" for n in res_ab["nodes"]), json.dumps(res_ab["nodes"]))
        check("returns at most ASK_K nodes", len(res_ab["nodes"]) <= iea.ASK_K)
        check("rel on every returned node, descending", all("rel" in n for n in res_ab["nodes"]) and
              res_ab["nodes"] == sorted(res_ab["nodes"], key=lambda n: -n["rel"]))
        res_no = iea.ask("Who is 渡, the crossing between banks?")
        check("non-ability ask never returns a competence node", not any(n["type"] == "competence" for n in res_no["nodes"]))
        check("non-ability ask keyed on the question's terms finds the symbol node", any(n["id"] == "sym_river" for n in res_no["nodes"]), json.dumps(res_no["nodes"]))
        check("leaf nodes never returned", not any(n["id"] == "val_leaf_1" for n in res_no["nodes"] + res_ab["nodes"]))
        check("forced ability=True makes competence eligible", any(n["type"] == "competence" for n in iea.ask("mathematics observation tests", ability=True)["nodes"]))

        print("[4] projection additions: commit=False leaves the rotation memory alone; live_axiom stashes")
        ip._recency.clear()
        p1 = ip.project("the river crossing and the garden", commit=False)
        check("commit=False: recency untouched", ip._recency == {} and len(p1["nodes"]) >= 1)
        p2 = ip.project("the river crossing and the garden")
        check("default commit: recency bumped for picked nodes", all(ip._recency.get(n["id"], 0) > 0 for n in p2["nodes"]))
        base = "YOUR NAME: Du\nORIGIN: x\nVOICE STYLE: plain.\nSPEAKING CONSTRAINTS: none."
        la = ip.live_axiom("Who is 渡, the crossing between banks?", base)
        last = ip.last_live_projection()
        check("live_axiom returns a projected axiom with the VOICE STYLE tail", bool(la) and la.endswith("VOICE STYLE: plain.\nSPEAKING CONSTRAINTS: none."))
        check("last_live_projection stashed for that context", last.get("context") == "Who is 渡, the crossing between banks?" and isinstance(last.get("nodes"), list))

        print("[5] observe(): rows for self-question cycles only, nothing injected")
        log = pathlib.Path(iea._LOG)
        check("non-self-question cycle logs nothing", iea.observe(_state("How does mottainai influence Japanese gardens?", "internal")) is None and not log.exists())
        row_h = iea.observe(_state("Who is 渡, the crossing between banks?", "human"))
        check("human self-question logged with the LIVE projection", row_h is not None and row_h["projection_source"] == "live")
        rec_before = dict(ip._recency)
        row_i = iea.observe(_state("What am I good at — observation or mathematics?", "internal"))
        check("internal self-question logged with a WOULD-BE projection", row_i is not None and row_i["projection_source"] == "would_be")
        check("would-be projection did not advance the rotation memory", ip._recency == rec_before)
        rows = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]
        check("two rows written", len(rows) == 2)
        need = {"ts", "cycle_id", "input_type", "question", "self_q", "ability", "returned", "projection",
                "projection_source", "overlap", "n_returned", "returned_subset_of_projection", "has_competence", "live"}
        check("row schema", all(need <= set(r) for r in rows), str(set(rows[0]) ^ need))
        check("internal ability row has a competence node", rows[1]["has_competence"] is True and rows[1]["ability"]["ability"] is True)
        check("overlap counted against the projection ids", rows[0]["overlap"] == len({n["id"] for n in rows[0]["returned"]} & {n["id"] for n in rows[0]["projection"]}))
        check("rows carry live=False", all(r["live"] is False for r in rows))
        check("status() reads the lab log", iea.status()["rows"] == 2)

        print("[6] judge script: reply join, prompt, fake panel, report")
        sys.path.insert(0, str(ROOT / "scripts"))
        import estate_ask_judge as jd
        # persist a Q/A summary into the (empty, lab) DB exactly the way _persist_cycle does
        store.store_fragment("Q: Who is 渡, the crossing between banks?\nA: I hold: I am in a sacred pause before I act. "
                             "And the river crossing is one of my symbols, not my whole self.\nTensions: a | b", origin="lived")
        store.store_fragment("Q: What am I good at — observation or mathematics?\nA: I drift on the tide.", origin="lived")
        db = pathlib.Path(store.DB_PATH)
        rep = jd.find_reply(db, "Who is 渡, the crossing between banks?", rows[0]["ts"])
        check("find_reply joins by question prefix + window", rep is not None and rep["reply"].startswith("I hold:") and "Tensions" not in rep["reply"])
        check("find_reply misses outside the window", jd.find_reply(db, "Who is 渡, the crossing between banks?", rows[0]["ts"] + 5000) is None)
        text_by_id = jd._estate_text_by_id()
        facts = jd.facts_for(rows[0]["returned"], rows[0]["projection"], text_by_id)
        check("facts: ask nodes first then projection, de-duplicated, capped",
              len(facts) <= jd.MAX_FACTS and len({f["id"] for f in facts}) == len(facts) and (not facts or facts[0]["from"] == "ask"))
        up = jd.build_user_prompt(rep["question"], rep["reply"], facts)
        check("prompt carries question, reply and numbered facts", "QUESTION:" in up and "REPLY:" in up and "1. (" in up)

        calls = []

        async def fake_rule_detail(system, user, key, context="", num_predict=200, tiebreak_url=None):
            calls.append(key)
            reply = user.split("REPLY: ", 1)[1].split("\n\nFACTS", 1)[0]   # judge the REPLY, not the facts list
            return {"verdict": "sacred pause" in reply, "how": "agreed", "why": "fake", "err1": None, "err2": None}

        from core import judge_panel
        judge_panel.rule_detail = fake_rule_detail
        out = lab / "judgements.jsonl"
        import asyncio
        r1 = asyncio.run(jd.judge_shadow(log, db, out, None, None, dry_run=False))
        check("judge_shadow judged both shadow rows", r1["judged"] == 2 and r1["no_reply"] == 0, json.dumps(r1))
        check("panel called with the cites_estate_fact key", calls == [jd.JUDGE_KEY] * 2)
        jrows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
        check("one True (stand cited) and one False", sorted(str(r["verdict"]) for r in jrows) == ["False", "True"])
        r1b = asyncio.run(jd.judge_shadow(log, db, out, None, None, dry_run=False))
        check("re-run is idempotent (keys already done)", r1b["judged"] == 0 and len(calls) == 2)
        r2 = asyncio.run(jd.judge_replies(db, out, None, None, dry_run=False, keyword_only=True))
        check("replies arm finds both self-question Q/A fragments", r2["self_questions"] == 2 and r2["judged"] == 2, json.dumps(r2))
        rp = jd.report(out, log)
        check("report: overall + arms + shadow redundancy + defeater flags",
              rp["overall"]["n"] == 4 and rp["by_arm"]["shadow"]["n"] == 2 and rp["by_arm"]["replies"]["n"] == 2
              and "redundant_clause_tripped" in rp["d0424_defeater"] and rp["shadow"]["rows"] == 2, json.dumps(rp)[:300])
        n_calls = len(calls)
        r3 = asyncio.run(jd.judge_shadow(log, db, lab / "dry.jsonl", None, None, dry_run=True))
        check("dry-run writes rows with verdict None and calls no hub", r3["judged"] == 2 and len(calls) == n_calls
              and all(json.loads(l)["how"] == "dry_run" for l in (lab / "dry.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()))

    print("[7] after the sandbox: globals restored, nothing live touched")
    check("_LOG restored to the module default", pathlib.Path(iea._LOG) == iea._DATA / "identity_estate_ask_shadow.jsonl")
    check("estate path restored", pathlib.Path(ip._ESTATE_F) == ip._DATA / "identity_estate.json")
    check("no shadow log at the tree's own data/ path", not (ROOT / "data" / "identity_estate_ask_shadow.jsonl").exists())

    print(f"\n{N - len(FAILS)}/{N} checks passed" + (f"; FAILED: {FAILS}" if FAILS else ""))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
