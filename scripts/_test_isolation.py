"""Shared world-store isolation helper for scripts/ regression tests.

J-0922 (F-1287's own "shared-helper question", briefing item 3): at least 6 scripts under
scripts/ (_test_episodic_buffer.py, _test_emotional_pre_retrieval.py, _test_procedural_memory.py,
_test_autonoetic_timeline.py, _test_candles_name_migration.py, _test_dark_house_answers.py) hand-
copied a near-identical ~30-40 line ISOLATION header redirecting the same set of world-store path
constants before anything under test could reach a live write -- a set that grew one job at a time
(J-0518, 2026-09-03; J-0743, 2026-09-08; J-0830/F-1231, 2026-09-10; J-0870/F-1287, 2026-09-12) as
this plan's own audit chain kept finding one more never-guarded module reachable from
study_life._st() and from store_fragment()'s own census/watershed side-writes. This module is the
single place that set now lives; migrate a new caller here instead of copy-pasting the header again.

Usage (mirrors every header this replaces -- call BEFORE the first line that could reach any of
these writers, keep whatever `from core import X as ALIAS` / `import core.X as _x` import the
caller's own body still needs for later manipulation; this function patches the same underlying
module objects Python already caches, so an alias imported before or after this call sees the
identical, already-redirected object either way):

    import tempfile
    from pathlib import Path
    from scripts._test_isolation import redirect_world_stores

    TMP = Path(tempfile.mkdtemp(prefix="my_test_"))
    paths = redirect_world_stores(TMP, locomotion=True, watershed=True, census=True,
                                   extra=("satisfaction",))
    # paths["provisions"] -> TMP / "provisions.json", etc. -- for a caller that wants to assert
    # against one of the resolved paths directly.

Fail-loud convention (J-0819/F-1198, modelled directly here rather than the pre-J-0819 silent
hasattr()-noop OR the direct-assignment scripts' own "no hasattr() guard, rely on a later
NonLiveWriteError" convention -- this module deliberately upgrades every migrated caller to the
same best-known protection): every redirect goes through `hasattr()` first. A hit sets the
attribute and is included in the returned dict; a miss prints a loud
"(redirect skipped: <module> <attr> -- no such attribute, stale/typo'd isolation-list entry?)"
line and is left OUT of the returned dict -- a future rename surfaces itself immediately, the
same way J-0819's own guard already does for the 11-script REDIRECTS-table class, rather than
needing another manual audit job the next time one of these modules' internals move.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

# The optional single-purpose redirects recognised by `extra=`. Each was found reachable from
# exactly one (or a named few) of the 6 scripts' own call graphs, not the general _st()/
# store_fragment() chain the unconditional core set below covers -- pass only the ones a given
# caller's own call graph actually reaches (J-0832/F-1236's "dead weight" precedent: a script
# that never reaches a given writer should not carry its redirect "for completeness").
_KNOWN_EXTRAS = {
    "satisfaction",          # core.satisfaction._LOG/_STATE -- store.store_shadow_event() ->
                              # satisfaction.record("shadow_event") (J-0870/F-1287).
    "subconscious_light",    # nodes.subconscious_node._LIGHT_FILE -- SubconsciousNode's own
                              # state save, D-0154's hot-reader companion to _STATE_FILE
                              # (J-0870/F-1287). _STATE_FILE/_SC_LOG_FILE/_AXIOM_FILE themselves
                              # stay OUTSIDE this helper -- callers that use subconscious_node at
                              # all already set those 3 directly, this only adds the 4th.
    "procedures",             # core.procedures._F/_LOG -- never-guarded module, one
                              # admissible()-gate fixture-timing fix away from firing (J-0870/
                              # F-1287; the gate itself was later fixed by J-0872/F-1288).
    "loop_probe",             # core.loop_probe._LOG -- shadow_observe(), fired by a
                              # origin="subconscious_synthesis" fragment (J-0870/F-1287).
    "narrative_quality",      # core.narrative_quality._LOG -- log_score(), reached from a real
                              # T4 self-authoring commit (J-0870/F-1287).
    "telemetry",              # core.telemetry._CALLS -- model_client.call_node() logs
                              # unconditionally before any network attempt (J-0870/F-1287).
    "provisional_identity",   # core.provisional_identity._PROV/_LOG -- T4 v3's probationary
                              # admission loop opens a real provisional record (J-0873/F-1233,
                              # the same day, not itself in F-1287 -- folded in here as the same
                              # class of gap since it is real, current, and this helper's whole
                              # point is not leaving the next script to rediscover it).
    "contradiction_ledger",   # nodes.subconscious_node._CONTRADICTION_LEDGER_LOG -- the T4
                              # contradiction-pressure snapshot row _t4_self_authoring() appends
                              # in its own pressure-calc block. F-1287's own "recorded rather than
                              # monkeypatched" gap (no module constant existed to redirect) --
                              # hoisted by J-0923, same path/behaviour, now redirectable here.
    "t4_emissary_judge",      # nodes.subconscious_node._T4_EMISSARY_JUDGE_LOG -- the decoupled-
                              # emissary-judge shadow row _t4_self_authoring() appends in its own
                              # probationary-admission-gate block. Same F-1287 gap, same J-0923 fix
                              # as contradiction_ledger above.
    "mood",                   # core.mood._FP_LOG (felt_preamble_log.jsonl) -- a never-guarded
                              # module (zero profile.guard_path() calls anywhere in core/mood.py):
                              # felt_preamble()'s own unconditional shadow-log write (fires on
                              # EVERY call, live or not -- the notability gate only affects whether
                              # a *line* is returned for injection, never whether the row is
                              # written) fires from nodes/executive_node.py's own unconditional
                              # felt_preamble(source="executive") call inside _build_prompt(),
                              # reached by ANY ExecutiveNode()._build_prompt()/.run() (J-0922/
                              # F-1348's own "two gaps found while verifying" -> J-0976). The
                              # sibling call site, nodes/inner_monologue_node.py's own
                              # felt_preamble(source="monologue") inside _think(), is the other
                              # reachable path -- redirect this name whenever a caller's own graph
                              # constructs either node and actually drives it (._build_prompt()/
                              # .run()/._think()), not just imports it. nodes/dream_node.py and
                              # nodes/voice_node.py also import core.mood but only ever call its
                              # read-only current_vec()/current_valence()/current_felt() -- they
                              # never reach felt_preamble() at all, confirmed by direct read
                              # (J-0976), so constructing THOSE two alone never needs this redirect.
}


def _redirect(mod, attr: str, path: Path, *, mod_name: str) -> bool:
    """Set mod.attr = path when the attribute genuinely exists; otherwise warn loudly and skip
    (J-0819/F-1198's convention) rather than silently leaving the live default path in place."""
    if hasattr(mod, attr):
        setattr(mod, attr, path)
        return True
    print(f"   (redirect skipped: {mod_name} {attr} -- no such attribute, stale/typo'd isolation-list entry?)")
    return False


def redirect_world_stores(
    tmp_dir: Path,
    *,
    locomotion: bool = False,
    watershed: bool = False,
    census: bool = False,
    extra: Iterable[str] = (),
) -> Dict[str, Path]:
    """Apply the world-store redirect set to `tmp_dir`. Returns the resolved paths that were
    actually set (keyed by a short stable name, e.g. "provisions", "world_objects") so a caller
    that wants to assert against one of them still can. A skipped (hasattr-miss) redirect is
    left out of the returned dict -- see the module docstring's fail-loud convention.

    Always applied, unconditionally, as one unit -- J-0830/F-1231 proved incrementally that a
    partial redirect of this chain is not enough (redirecting only provisions/study_life still
    raises one hop further out, on world_substrate.json): sensorium._STATE_F, study_life._LEDGER
    /_EVENTS, provisions._F/_LOG, world_objects._OBJECTS_F (+ its _objects_cache/_last_load
    reset), world_substrate._SUBSTRATE_F/_SUBSTRATE_LOG/_LAST_LOOKED_F (+ its _cache/_cache_ts
    reset) -- the connected chain study_life._st() -> provisions.sync()/._ensure() ->
    world_substrate._save()/world_objects._save_objects() walks on nearly any state-touching
    call, not just the store_fragment()/census path below.

    locomotion=True -- core.locomotion._POS_F. Needed by callers whose own chain reaches
        store_fragment() -> experienced_tuple.experienced() -> _light_band() ->
        locomotion.position_standpoint() -> get_position() -> _save() (self-heals and saves on
        nearly any fresh-process call, F-1118/J-0778) -- or any other caller that already
        redirects it today; this flag does not assume WHY, only whether the caller's own header
        currently does.
    watershed=True -- core.watershed.configure(data_dir=tmp_dir). core.watershed.observe()
        (store.py:607) writes watershed_state.json/watershed_shadow.jsonl unconditionally for
        identity-adjacent origins, one step before the census in the store_fragment() chain.
    census=True -- core.geometry_census._LOG + core.arousal._DATA/_STATE/_LOG: the census row
        + arousal shadow row geometry_census.snapshot() appends once the chain above completes
        instead of raising -- J-0830/F-1231's own "false-green trap" (a script whose only
        change is the chain above no longer raising would otherwise start silently appending a
        real row to the live geometry_tuples.jsonl/arousal_shadow.jsonl the moment it is run
        from C:\\Nascence).
    extra -- any of _KNOWN_EXTRAS (see their own comments above); pass only what this caller's
        own call graph actually reaches. An unrecognised name is reported the same fail-loud way
        as a stale attribute, not silently ignored.
    """
    tmp_dir = Path(tmp_dir)
    paths: Dict[str, Path] = {}

    import core.sensorium as sensorium
    p = tmp_dir / "room_state.json"
    if _redirect(sensorium, "_STATE_F", p, mod_name="core.sensorium"):
        paths["room_state"] = p

    import core.study_life as study_life
    p = tmp_dir / "study_ledger.jsonl"
    if _redirect(study_life, "_LEDGER", p, mod_name="core.study_life"):
        paths["study_ledger"] = p
    p = tmp_dir / "study_events.jsonl"
    if _redirect(study_life, "_EVENTS", p, mod_name="core.study_life"):
        paths["study_events"] = p

    import core.provisions as provisions
    p = tmp_dir / "provisions.json"
    if _redirect(provisions, "_F", p, mod_name="core.provisions"):
        paths["provisions"] = p
    p = tmp_dir / "provisions_log.jsonl"
    if _redirect(provisions, "_LOG", p, mod_name="core.provisions"):
        paths["provisions_log"] = p

    import core.world_objects as world_objects
    p = tmp_dir / "world_objects.json"
    if _redirect(world_objects, "_OBJECTS_F", p, mod_name="core.world_objects"):
        paths["world_objects"] = p
    if hasattr(world_objects, "_objects_cache"):
        world_objects._objects_cache = {}
    else:
        print("   (redirect skipped: core.world_objects _objects_cache -- no such attribute, stale/typo'd isolation-list entry?)")
    if hasattr(world_objects, "_last_load"):
        world_objects._last_load = 0.0
    else:
        print("   (redirect skipped: core.world_objects _last_load -- no such attribute, stale/typo'd isolation-list entry?)")

    import core.world_substrate as world_substrate
    p = tmp_dir / "world_substrate.json"
    if _redirect(world_substrate, "_SUBSTRATE_F", p, mod_name="core.world_substrate"):
        paths["world_substrate"] = p
    p = tmp_dir / "world_substrate_events.jsonl"
    if _redirect(world_substrate, "_SUBSTRATE_LOG", p, mod_name="core.world_substrate"):
        paths["world_substrate_events"] = p
    p = tmp_dir / "world_substrate_last_looked.json"
    if _redirect(world_substrate, "_LAST_LOOKED_F", p, mod_name="core.world_substrate"):
        paths["world_substrate_last_looked"] = p
    if hasattr(world_substrate, "_cache"):
        world_substrate._cache = {}
    else:
        print("   (redirect skipped: core.world_substrate _cache -- no such attribute, stale/typo'd isolation-list entry?)")
    if hasattr(world_substrate, "_cache_ts"):
        world_substrate._cache_ts = 0.0
    else:
        print("   (redirect skipped: core.world_substrate _cache_ts -- no such attribute, stale/typo'd isolation-list entry?)")

    if locomotion:
        import core.locomotion as locomotion_mod
        p = tmp_dir / "position.json"
        if _redirect(locomotion_mod, "_POS_F", p, mod_name="core.locomotion"):
            paths["position"] = p

    if watershed:
        import core.watershed as watershed_mod
        watershed_mod.configure(data_dir=tmp_dir)
        paths["watershed_state"] = tmp_dir / "watershed_state.json"
        paths["watershed_shadow"] = tmp_dir / "watershed_shadow.json"

    if census:
        import core.geometry_census as geometry_census
        p = tmp_dir / "geometry_tuples.jsonl"
        if _redirect(geometry_census, "_LOG", p, mod_name="core.geometry_census"):
            paths["geometry_tuples"] = p

        import core.arousal as arousal
        if hasattr(arousal, "_DATA"):
            arousal._DATA = tmp_dir
        else:
            print("   (redirect skipped: core.arousal _DATA -- no such attribute, stale/typo'd isolation-list entry?)")
        p = tmp_dir / "arousal_state.json"
        if _redirect(arousal, "_STATE", p, mod_name="core.arousal"):
            paths["arousal_state"] = p
        p = tmp_dir / "arousal_shadow.jsonl"
        if _redirect(arousal, "_LOG", p, mod_name="core.arousal"):
            paths["arousal_shadow"] = p

    extra_set = set(extra)
    unknown = extra_set - _KNOWN_EXTRAS
    if unknown:
        print(f"   (redirect skipped: unknown extra(s) requested, not in _KNOWN_EXTRAS: {sorted(unknown)})")

    if "satisfaction" in extra_set:
        import core.satisfaction as satisfaction
        p = tmp_dir / "satisfaction_log.jsonl"
        if _redirect(satisfaction, "_LOG", p, mod_name="core.satisfaction"):
            paths["satisfaction_log"] = p
        p = tmp_dir / "satisfaction_state.json"
        if _redirect(satisfaction, "_STATE", p, mod_name="core.satisfaction"):
            paths["satisfaction_state"] = p

    if "subconscious_light" in extra_set:
        import nodes.subconscious_node as subconscious_node
        p = tmp_dir / "sc_state.light.json"
        if _redirect(subconscious_node, "_LIGHT_FILE", p, mod_name="nodes.subconscious_node"):
            paths["subconscious_light"] = p

    if "contradiction_ledger" in extra_set:
        import nodes.subconscious_node as subconscious_node
        p = tmp_dir / "contradiction_ledger_log.jsonl"
        if _redirect(subconscious_node, "_CONTRADICTION_LEDGER_LOG", p, mod_name="nodes.subconscious_node"):
            paths["contradiction_ledger_log"] = p

    if "t4_emissary_judge" in extra_set:
        import nodes.subconscious_node as subconscious_node
        p = tmp_dir / "t4_emissary_judge.jsonl"
        if _redirect(subconscious_node, "_T4_EMISSARY_JUDGE_LOG", p, mod_name="nodes.subconscious_node"):
            paths["t4_emissary_judge"] = p

    if "procedures" in extra_set:
        import core.procedures as procedures
        p = tmp_dir / "procedures.json"
        if _redirect(procedures, "_F", p, mod_name="core.procedures"):
            paths["procedures"] = p
        p = tmp_dir / "procedures_log.jsonl"
        if _redirect(procedures, "_LOG", p, mod_name="core.procedures"):
            paths["procedures_log"] = p
        # J-2578: observe_hand's refusal-kind shadow log (fail-open, but redirect it so a test
        # refusal never even tries the real data/ path).
        p = tmp_dir / "procedures_refusal_kind_shadow.jsonl"
        if _redirect(procedures, "_REFUSAL_KIND_SHADOW_LOG", p, mod_name="core.procedures"):
            paths["procedures_refusal_kind_shadow"] = p

    if "loop_probe" in extra_set:
        import core.loop_probe as loop_probe
        p = tmp_dir / "loop_probe_log.jsonl"
        if _redirect(loop_probe, "_LOG", p, mod_name="core.loop_probe"):
            paths["loop_probe_log"] = p

    if "narrative_quality" in extra_set:
        import core.narrative_quality as narrative_quality
        p = tmp_dir / "narrative_quality_log.jsonl"
        if _redirect(narrative_quality, "_LOG", p, mod_name="core.narrative_quality"):
            paths["narrative_quality_log"] = p

    if "telemetry" in extra_set:
        import core.telemetry as telemetry
        p = tmp_dir / "llm_calls.jsonl"
        if _redirect(telemetry, "_CALLS", p, mod_name="core.telemetry"):
            paths["llm_calls"] = p

    if "provisional_identity" in extra_set:
        import core.provisional_identity as provisional_identity
        p = tmp_dir / "provisional_axiom.json"
        if _redirect(provisional_identity, "_PROV", p, mod_name="core.provisional_identity"):
            paths["provisional_axiom"] = p
        p = tmp_dir / "provisional_identity_log.jsonl"
        if _redirect(provisional_identity, "_LOG", p, mod_name="core.provisional_identity"):
            paths["provisional_identity_log"] = p

    if "mood" in extra_set:
        import core.mood as mood
        p = tmp_dir / "felt_preamble_log.jsonl"
        if _redirect(mood, "_FP_LOG", p, mod_name="core.mood"):
            paths["felt_preamble_log"] = p

    return paths
