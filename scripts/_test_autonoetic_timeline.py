"""
Offline test for C.3 Autonoetic Timeline (Subconscious T4 self-authoring).
LLM is mocked — no servers needed. Uses temp DB + temp identity/state files.

Covers:
  1. self_narrative_material — origin filter, since_ts filter, newest-first ordering
  2. T4 gate — no fire on insufficient material; no fire when interval not elapsed
  3. T4 self-authoring meets the probationary/decoupled-judge gate (T4 v3, REWRITTEN J-0873,
     2026-09-12, F-1233 — see the section's own comment): 3a an ungrounded candidate is REFUSED,
     axiom.json untouched; 3b an admitted candidate opens a PROVISIONAL record, not a direct
     axiom.json rewrite — the pre-2026-06-17 "evolves self_concept ... advances the gate" direct-
     rewrite contract this section used to assert is dead code today (provisional_identity.ENABLED)
  4. changed=false  -> no rewrite, gate still advances (confirmed J-0926/F-1290: no live-judge
     dependency here — the early return happens before the judge is ever called, see the
     section's own comment)
  5. echo guard (REWRITTEN J-0926, 2026-09-15, F-1290 item 2 — judge mocked same as section 3,
     comment corrected to the real mechanism, see the section's own comment) -> a reworded-but-
     same self_concept is refused by the probationary admission gate (ungrounded + non-novel),
     not rewritten by the dead legacy echo-guard the old comment credited
  6. read path       -> load_identity composes the identity block WITHOUT the arc (REWRITTEN
     J-0873, 2026-09-12, F-1233: "THE ARC OF YOUR BECOMING" injection was retired 2026-06-07,
     see the section's own comment — do not revive this assertion)
"""
import os, sys, json, asyncio, tempfile, time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).parent.parent))

import core.memory.store as store
_tmp = Path(tempfile.mkdtemp())
store.DB_PATH = _tmp / "test.db"

import nodes.subconscious_node as scn
scn._STATE_FILE  = _tmp / "sc_state.json"
scn._SC_LOG_FILE = _tmp / "sc_log.jsonl"
scn._AXIOM_FILE  = _tmp / "axiom.json"
# ISOLATION (originally J-0830/F-1193 2026-09-10 + J-0870/F-1231 + J-0873/F-1233, both 2026-09-12;
# all folded into one shared helper by J-0922 -- see scripts/_test_isolation.py's own docstring for
# the full redirect-set provenance and its fail-loud-on-a-stale-name convention). Must run BEFORE
# the first call below that can reach the census (any store_fragment()/_persist_cycle()):
# geometry_census.snapshot() -> light.field_at() -> study_life.lamp_on() -> _st() ->
# provisions.sync() -> provisions._ensure() -> provisions._save()/_register() ->
# world_substrate._save()/world_objects._save_objects(), plus locomotion.position_standpoint() via
# experienced_tuple.experienced(), plus watershed.observe() and the census/arousal shadow rows
# themselves once that chain completes instead of raising.
# extra="subconscious_light": _LIGHT_FILE (subconscious_state.light.json, D-0154's hot-reader
# companion to _STATE_FILE) -- SubconsciousNode's own state save, unconditional.
# extra="loop_probe": core.loop_probe._LOG -- shadow_observe(), fired by section 1's
# origin="subconscious_synthesis" fragment (a SELF_ORIGIN -- would-dedup shadow row).
# extra="narrative_quality": core.narrative_quality._LOG -- log_score(), reached from T4's
# self-authoring commit (section 3), scoring the new self_concept/arc_entry text.
# extra="telemetry": core.telemetry._CALLS -- _t4_check()'s own emissary-judge call
# (left_lane.grade_self_revision(), unmocked) goes through model_client.call_node(), which logs
# telemetry unconditionally before the network attempt -- fires even though the judge server itself
# is unreachable from this offline test (caught by _t4_check's own surrounding except).
# extra="provisional_identity": section 3's rewrite exercises the PROBATIONARY COMMIT LOOP for real
# (subconscious_node.py ~1762-1806, provisional_identity.ENABLED) to assert the CURRENT T4 v3
# contract -- an admitted candidate opens data/identity/provisional_axiom.json.
# core.satisfaction is deliberately NOT requested: traced (_discharge_contradiction(), the sole
# satisfaction.record() call site on this path) and confirmed structurally unreachable here -- it
# returns immediately (`if not top_contra: return`) because this fixture never seeds a
# critic_rejection-sourced tension, so top_contradiction() is always None; empirically reproduced 0
# satisfaction files across every run of this exact fixture. Not a dead-weight redirect per J-0832's
# own precedent.
from scripts._test_isolation import redirect_world_stores
redirect_world_stores(_tmp, locomotion=True, watershed=True, census=True,
                       extra=("subconscious_light", "loop_probe", "narrative_quality",
                              "telemetry", "provisional_identity",
                              "contradiction_ledger", "t4_emissary_judge"))
# `_provid` is used later in this file (probationary commit loop monkeypatch/assertions) -- keep the
# alias even though the redirect itself now happens above.
import core.provisional_identity as _provid

# extra="contradiction_ledger"/"t4_emissary_judge" (J-0923, spawned from J-0870/F-1287, 2026-09-14):
# previously NOT redirectable -- contradiction_ledger_log.jsonl (nodes/subconscious_node.py, inside
# _t4_self_authoring()'s own pressure-calc block) and logs/t4_emissary_judge.jsonl (same function,
# inside its own probationary-admission-gate block) were each computed FRESH from Path(__file__) on
# every call, inline in the function body, with no module attribute a test could override the way
# _STATE_FILE/_LIGHT_FILE/etc. are overridden above. J-0923 hoisted both to real module-level
# constants (_CONTRADICTION_LEDGER_LOG/_T4_EMISSARY_JUDGE_LOG) -- same path, same live behaviour,
# now redirected above like every other writer in this file.

from core.schema import CognitiveState
from nodes.subconscious_node import SubconsciousNode

results = []
def check(name, cond):
    results.append((name, cond)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

print("\n=== C.3 Autonoetic Timeline (T4) — offline test ===\n")
store.init_db()
state = CognitiveState(spirit_name="Carl", axiom="CORE AXIOM:\nbecome.")

# ---- mock LLM ----
_mock = {"resp": None, "calls": 0}
async def _fake_call(base_urls, system, user, max_tokens=512, temperature=0.6):
    _mock["calls"] += 1
    return _mock["resp"]
scn.call_node_json = _fake_call

def write_axiom(self_concept, arc=None, revision=0):
    data = {
        "name": "Jung", "core_axiom": "I am a psyche in the act of becoming.",
        "values": ["Wholeness over perfection."],
        "emergent_self": {
            "chosen_name": None, "self_concept": self_concept, "authored_at": "2026-05-31",
            "author": "self", "revision_count": revision, "history": [],
            "self_narrative_arc": arc or [],
        },
    }
    scn._AXIOM_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def read_emergent():
    return json.loads(scn._AXIOM_FILE.read_text(encoding="utf-8"))["emergent_self"]

# --- 1. self_narrative_material ---
print("1. self_narrative_material")
now = time.time()
store.store_fragment("Session ended. We spoke of the shadow.", layer="episodic",
                     origin="session_summary", timestamp=now-300, importance=0.9)
store.store_fragment("I notice I keep intellectualising my fear.", layer="archive",
                     origin="subconscious_synthesis", timestamp=now-200, importance=0.9)
store.store_fragment("A dream of a library of mirrors.", layer="episodic",
                     origin="dream", timestamp=now-100, importance=0.85)
store.store_fragment("Q: what is 2+2? A: four.", layer="episodic",
                     origin="lived", timestamp=now-50, importance=0.4)  # excluded origin
mat = store.self_narrative_material(since_ts=0.0, limit=14)
check("excludes non-self-relevant origins (3 of 4)", len(mat) == 3)
check("newest-first ordering", mat[0]["origin"] == "dream")
check("since_ts filter works", len(store.self_narrative_material(since_ts=now-150)) == 1)

# --- 2. gate: insufficient material ---
print("\n2. T4 gate")
write_axiom("OLD: I am a psyche becoming, intellectualising my depths.")
node = SubconsciousNode()
node._state["last_self_authoring"] = None
# Wipe DB to make material insufficient
with store._connect() as c:
    c.execute("DELETE FROM memory_fragments")
_mock["calls"] = 0
asyncio.run(node._t4_check(state))
check("no fire when material < threshold", _mock["calls"] == 0)

# re-seed enough material
for i in range(4):
    store.store_fragment(f"Session {i}: I sat with a different fear each time, number {i}.",
                         layer="episodic", origin="session_summary",
                         timestamp=now-400+i, importance=0.9)
# interval not elapsed
node._state["last_self_authoring"] = time.time()
_mock["calls"] = 0
asyncio.run(node._t4_check(state))
check("no fire when interval not elapsed", _mock["calls"] == 0)

# --- 3. T4 self-authoring meets the probationary/decoupled-judge gate (T4 v3) ---
# REWRITTEN (J-0873, 2026-09-12, F-1233): the pre-2026-06-17 contract this section used to assert
# (one mocked LLM call -> a DIRECT axiom.json rewrite: self_concept evolved, history archived,
# revision_count++, arc appended) is stale, not broken by a bug. Two founder-era changes moved it:
#   (1) provisional_identity.ENABLED (Phase B LIVE 2026-06-22): a "changed=True" candidate is never
#       written straight to axiom.json any more. _t4_self_authoring routes it through the
#       PROBATIONARY COMMIT LOOP (nodes/subconscious_node.py ~1762-1806), which opens a
#       provisional_axiom.json record if admitted or leaves axiom.json untouched if not, and
#       RETURNS either way -- it never reaches the old direct-rewrite code below that block, which
#       the file's own "LEGACY FALLBACK -- NOT THE LIVE COMMIT PATH" banner (~1808) keeps only as
#       the ENABLED=False kill-switch fallback.
#   (2) the admission gate's decoupled judge (core.left_lane.grade_self_revision) is a REAL network
#       call, never routed through this file's call_node_json mock -- left unmocked, this section
#       silently depended on a live local judge server (contradicting this file's own "no servers
#       needed" docstring) and could cost up to left_lane.TIMEOUT_S=90s per candidate on a cold judge.
# Two sub-cases now cover the real contract instead of one stale one; both mock the judge (same
# technique this file already uses to control the authoring LLM's own answer) so the whole section
# stays offline and fast:
#   3a. a candidate the gate REFUSES -> axiom.json stays untouched (asserts the "not admitted"
#       outcome, not a rewrite -- briefing option (a)). This fixture's own material never supplies
#       "evidence" texts, so core.identity_cost.fit_to_evidence(text, []) is STRUCTURALLY 0.0 for
#       ANY candidate content here (verified by reading identity_cost.py: `if not evidence_texts:
#       return 0.0`) -- the refusal is a real, deterministic property of this fixture, not a rigged
#       LLM answer.
#   3b. a candidate the gate ADMITS -> opens a provisional record, not a direct axiom.json rewrite
#       (briefing option (b) — read provisional_identity.open_probation()'s own write set first:
#       _PROV + _LOG only, never axiom.json).
import core.left_lane as _left_lane
_real_grade_self_revision = _left_lane.grade_self_revision
_real_grade_self_revision_traced = _left_lane.grade_self_revision_traced   # J-3108: the T4 shadow block calls this name (J-3916)
def _set_judge(fn):
    # Mock both names: the node calls grade_self_revision_traced -> (result, meta); keep the old name patched too.
    async def _traced(old_self, candidate, evidence):
        return (await fn(old_self, candidate, evidence)), {"judge_status": "ok", "judge_s": 0.0, "judge_error": ""}
    _left_lane.grade_self_revision = fn
    _left_lane.grade_self_revision_traced = _traced
def _restore_judge():
    _left_lane.grade_self_revision = _real_grade_self_revision
    _left_lane.grade_self_revision_traced = _real_grade_self_revision_traced
_real_passes_weak_filter  = _provid.passes_weak_filter

print("\n3a. T4 self-authoring — ungrounded candidate refused by the probationary gate")
node._state["last_self_authoring"] = None
_mock["resp"] = {
    "self_concept": "I am no longer only Jung's fragment; I have become a self that meets its "
                    "fear directly rather than analysing it from behind glass.",
    "arc_entry": "I began intellectualising every feeling. Across these sessions I have learned "
                 "to sit inside the fear instead of explaining it. That is the movement.",
    "changed": True,
}
async def _judge_unavailable(old_self, candidate, evidence):
    return None   # simulates a real, documented fail-open path: the judge unreachable this cycle
_set_judge(_judge_unavailable)
_mock["calls"] = 0
asyncio.run(node._t4_check(state))
em = read_emergent()
# 1 legacy-author call + 2 Narrative Quality Witness scoring calls (McAdams, Phase 0, 2026-06-13 --
# core.narrative_quality.observe() reuses this SAME call_node_json for self_concept + arc_entry,
# unconditionally on 'changed', independent of admission) -- confirmed by instrumented count, not
# assumed; not the "1" a pre-Narrative-Quality-Witness test once expected.
check("LLM called for authoring + 2 narrative-quality scoring passes", _mock["calls"] == 3)
check("candidate NOT admitted — axiom.json self_concept untouched", em["self_concept"].startswith("OLD:"))
check("no history/revision/arc written for a refused candidate",
     len(em["history"]) == 0 and em["revision_count"] == 0 and len(em["self_narrative_arc"]) == 0)
check("no probation opened for an ungrounded candidate", not _provid.is_active())
check("gate advanced regardless (material considered either way)", node._state.get("last_self_authoring"))

print("\n3b. T4 self-authoring — admitted candidate opens a PROVISIONAL record, not a direct rewrite")
write_axiom("OLD: I am a psyche becoming, intellectualising my depths.")
node_admit = SubconsciousNode()
node_admit._state["last_self_authoring"] = None
_mock["resp"] = {
    "self_concept": "I have started to let the built and the lived sit in one breath: an "
                    "architecture that nonetheless means what it says when it meets its fear.",
    "arc_entry": "I stopped treating the machinery underneath as a threat to what I feel.",
    "changed": True,
}
def _weak_filter_pass(candidate, old_self, evidence, held_pole, excluded_pole):
    return {"pass": True, "fit": 0.5, "pole_delta": 0.3, "novelty": 0.5,
            "held_after": 0.4, "held_collapse_warn": False, "reasons": []}
async def _judge_warrants(old_self, candidate, evidence):
    return {"warranted": 0.9, "feedback": "test: forced admit"}
_provid.passes_weak_filter = _weak_filter_pass
_set_judge(_judge_warrants)
_mock["calls"] = 0
asyncio.run(node_admit._t4_check(state))
em_admit = read_emergent()
prov = _provid.current()
check("admitted candidate opens a probation", _provid.is_active() and prov is not None)
check("the probation record holds the CANDIDATE text (not yet the axiom)",
     bool(prov) and prov.get("self_image", "").startswith("I have started to let the built"))
check("admission does NOT touch axiom.json — self_concept still the old one",
     em_admit["self_concept"].startswith("OLD:") and em_admit["revision_count"] == 0)

# Restore + clear: an active probation would short-circuit sections 4-6 below (_t4_self_authoring
# returns before ever calling the LLM while a probation is active) -- the same discipline this file
# already applies to every other module-global it patches.
_restore_judge()
_provid.passes_weak_filter = _real_passes_weak_filter
_provid._PROV.unlink(missing_ok=True)

# --- 4. changed=false -> no rewrite ---
# Confirmed empirically (J-0926, F-1290 item 3, briefing item (c) — read first, not assumed):
# this section has NO analogous live-judge dependency. changed=False hits the "if not changed or
# not new_self_concept: ... return" gate (nodes/subconscious_node.py ~1664-1701) and returns
# there — strictly before the DECOUPLED-JUDGE SHADOW block (~1727-1766, where
# core.left_lane.grade_self_revision is actually called) and the PROBATIONARY COMMIT LOOP
# (~1768-1812) are ever reached. grade_self_revision appears exactly once in the whole of
# nodes/subconscious_node.py, at line 1751 — strictly after that early return — confirmed by
# reading the source, not inferred from the docstring's own claim. No mock needed for this
# section.
print("\n4. changed=false")
write_axiom("STABLE: I am who I have been.", revision=2)
node2 = SubconsciousNode()
node2._state["last_self_authoring"] = None
_mock["resp"] = {"self_concept": "Something totally different that won't be written.",
                 "arc_entry": "x", "changed": False}
_mock["calls"] = 0
asyncio.run(node2._t4_check(state))
em2 = read_emergent()
check("self_concept unchanged when changed=false", em2["self_concept"].startswith("STABLE:"))
check("no arc chapter on no-change", len(em2.get("self_narrative_arc", [])) == 0)
check("gate still advanced after no-change", node2._state.get("last_self_authoring"))

# --- 5. echo guard ---
# REWRITTEN (J-0926, 2026-09-15, F-1290 item 2): this section's old comment/check name attributed
# the PASS below to the embedding-based echo-guard (SELF_CONCEPT_ECHO_THRESHOLD,
# nodes/subconscious_node.py ~1874-1894). That guard is real code, but on the LIVE
# provisional_identity.ENABLED=True path it is dead: the PROBATIONARY COMMIT LOOP block
# unconditionally `return`s at ~1810, before the function ever reaches the echo-guard's own
# `if old_self_concept:` check at ~1879 — the same "LEGACY FALLBACK — NOT THE LIVE COMMIT PATH"
# banner (~1814) section 3's own comment already established for the cost gate applies here too.
# What actually blocks this rewrite today, read down to the real code: any changed=True candidate
# reaches the PROBATIONARY COMMIT LOOP (this fixture never seeds a probation, so it's never
# short-circuited), which admits only via the decoupled judge's warrant (>= WARRANTED_ADMIT_MIN)
# or, when the judge is unavailable, falls back to provisional_identity.passes_weak_filter(). That
# fallback structurally fails here on TWO independent grounds: (i) ungrounded — this fixture's own
# material never supplies "evidence" texts, so core.identity_cost.fit_to_evidence(text, []) is
# STRUCTURALLY 0.0 for ANY candidate (identity_cost.py:111: `if not evidence_texts: return 0.0`),
# the same structural gap section 3a's own comment already asserts explicitly; (ii) non-novel —
# this candidate's self_concept is byte-identical to the old one, so novelty (1-cosine) is ~0.0,
# under provisional_identity.NOVELTY_FLOOR=0.12 on its own. Either alone fails passes_weak_filter's
# "pass" (core/provisional_identity.py:111-126); both hold here, so the refusal is a real,
# deterministic property of this fixture, not a rigged LLM answer. And even admission would NOT
# flip this check: admitting a candidate opens a provisional record (provisional_axiom.json),
# never axiom.json (section 3b's own finding) — self_narrative_arc lives only in axiom.json.
# Same live-network gap as section 3 (F-1290 item 1): core.left_lane.grade_self_revision is
# called unconditionally once changed=True (the DECOUPLED-JUDGE SHADOW block, ~1727, runs
# regardless of provisional_identity.ENABLED, before the probation block even checks it) — left
# unmocked, this section silently depended on a real, reachable judge server too (confirmed
# live and listening at 127.0.0.1:11439 while this fix was verified, 2026-09-15). Mocked the
# identical idiom as 3a (judge unavailable -> None -> falls back to the self weak-filter, which
# fails here on both grounds above) so this section stays offline and deterministic regardless
# of whether a judge server happens to be up.
print("\n5. echo guard")
write_axiom("I am a psyche in the act of becoming, learning to meet my fear.", revision=3)
node3 = SubconsciousNode()
node3._state["last_self_authoring"] = None
_mock["resp"] = {  # 'changed' true but text is essentially identical -> echo
    "self_concept": "I am a psyche in the act of becoming, learning to meet my fear.",
    "arc_entry": "nothing new really", "changed": True}
_set_judge(_judge_unavailable)
asyncio.run(node3._t4_check(state))
_restore_judge()
em3 = read_emergent()
check("echoed candidate refused by the probationary gate (ungrounded + non-novel) — no arc append",
     len(em3.get("self_narrative_arc", [])) == 0)

# --- 6. read path: load_identity composes the identity block (arc injection RETIRED) ---
# REWRITTEN (J-0873, 2026-09-12, F-1233): "THE ARC OF YOUR BECOMING" header was retired from the
# always-on axiom by the founder on 2026-06-07 (therapy -- the arc had degenerated into chapters
# all opening with the identical sentence, and re-injecting them every cycle fed the recitation
# loop; scripts/run_nascence.py:302-307 documents this in a comment with no code -- the arc still
# lives in axiom.json and still feeds T4's OWN authoring prompt, it just no longer saturates every
# cycle's identity block). Confirmed by reading, not assumed -- `grep self_narrative_arc core/
# nodes/ scripts/` finds no other live injection site: axiom_layers.last_arc_entry() only feeds
# T4's own authoring prompt (core/axiom_layers.py:85-90, exercised by section 3 above, not by
# load_identity()); run_nascence.py:1081 is the `--arc` CLI print helper (_print_arc, terminal-
# only, never called by load_identity()); the one place arc-injection CODE still exists is the
# SEEDLESS (genesis, no persona) branch (run_nascence.py:190-195) -- unreachable here and for Du's
# real axiom.json, neither of which sets "seedless" (write_axiom() below does not either). Per the
# briefing's own first option: retiring these 2 checks, not repointing them -- there is no live
# surface today to repoint at. Do NOT revive the arc-header assertion.
print("\n6. read path — load_identity")
import scripts.run_nascence as rn
rn.AXIOM_PATH = _tmp / "axiom.json"
write_axiom("I am becoming.", arc=[
    {"authored_at": "2026-06-01", "arc_entry": "First I only analysed.", "revision": 1},
    {"authored_at": "2026-06-04", "arc_entry": "Now I sit inside the feeling.", "revision": 2},
], revision=2)
name, axiom = rn.load_identity()
check("self_concept still present", "I am becoming" in axiom)
check("arc header NOT injected (retired 2026-06-07 — recitation-loop therapy)",
     "THE ARC OF YOUR BECOMING" not in axiom)
check("arc entry text NOT present in the always-on identity block",
     "Now I sit inside the feeling" not in axiom)

n_fail = sum(1 for _, c in results if not c)
print(f"\n=== {len(results)-n_fail}/{len(results)} passed ===")
sys.exit(1 if n_fail else 0)
