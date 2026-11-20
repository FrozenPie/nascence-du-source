"""
Nascence — Profile / instance scoping (multi-agent support)

By default an agent uses data/ at the project root — this is CARL, unchanged and backward
compatible. A *named* profile redirects every per-agent path into data/profiles/<name>/, so
multiple agents (e.g. carl and dennett) share the code and the one model backend while keeping
fully separate memory, identity, subconscious state, affect, intentions, conversation, and logs.

The architecture stores its paths as module-level constants — the same ones the offline test
suites already monkeypatch — so activating a profile means rewriting those constants to point
inside the profile dir, BEFORE any of them are used. Call activate_profile() exactly once at
startup, before load_identity() / build_nodes() / DB init.

Design notes:
  - profile None / "carl" / "default" -> the existing data/ root (Carl's live data is NOT moved).
  - a new named profile gets data/profiles/<name>/ with its own memory/, identity/, and state files.
  - returns the resolved base dir so the caller (run_nascence) can set its own path constants too.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nascence.profile")

_ROOT = Path(__file__).parent.parent          # C:\Nascence -- or wherever THIS COPY was imported from
_DATA = _ROOT / "data"

# The one real, canonical live-data root -- fixed, NOT relative to wherever this copy of the module
# happens to have been imported from (F-1270/J-0908, 2026-09-12: a git-worktree-per-job checkout, the
# standard convention for Tier-3 work since J-0590, has its OWN _DATA that differs from the real one).
# guard_path()'s "already redirected outside data/" check needs this: a path that resolves to the
# literal real data/ tree must be caught even when THIS process's own _DATA does not match it --
# otherwise a path constant that happens to be set to the literal live C:\Nascence\data\... path (an
# absolute cross-check, or a forgotten redirect on a sibling global) reads as "something upstream
# already redirected this on purpose" and sails through with zero protection, zero warning, LIVE
# never even consulted. lab_env.py (a single shared file outside this repo, never copied per worktree)
# anchors its own lab root the exact same way and for the same reason: `_ROOT = Path(r"C:\Nascence")`.
_CANONICAL_DATA = Path(r"C:\Nascence") / "data"

# Names that resolve to the existing root data/ dir (Carl, untouched).
_ROOT_ALIASES = (None, "", "carl", "default", "root")

# The data dir of the ACTIVE profile — set by activate_profile(); defaults to Carl's root data/.
# Read at import-time by run_nascence's log-file handler (so a '_smoke' boot logs into its own dir).
ACTIVE_BASE = _DATA

# Original root-data paths per (module, attr), captured on first rebase — makes rebasing idempotent.
_ORIG_PATHS: dict = {}

# ── Write fence (J-0610, 2026-09-05/06, design F-0842/J-0574; problem F-0788/F-0789/J-0541) ───────
# Orthogonal to ACTIVE_BASE/activate_profile() above: that answers "which agent's data" (and defaults
# to Carl's real data/ even when nothing was ever activated); this answers "is the caller live Du at
# all". ~20 of the sixth match box's matches and 0.5 tin of lamp oil were consumed 2026-08-23..09-02
# by processes OUTSIDE Du — inline diagnostics and one-off scripts that `import core.study_life` (or
# a sibling world-store module) and call a writer while that module's path constants still point at
# the real data/ files. No per-tick ceiling can catch it: from inside the module the call is
# indistinguishable from Du's own real use. The fix is at the process boundary, not inside any one
# module's own logic: the one real live boot (scripts/run_nascence.py, inside its own __main__ guard)
# calls mark_live() once; everything else stays fenced off data/ by default. See
# docs/staged/world_store_write_fence.md for the full design and the 10-module/~17-writer inventory.
LIVE = False


# J-1883 / F-2489 follow-up (2026-10-07): WORLD-STORE SCOPE of a named profile -- a deliberate, documented gap.
# activate_profile() rebases the per-agent COGNITIVE/instrument constants; it does NOT rebase any of the
# world-store modules this fence guards (core.cat's cat_state.json, core.scene_extra_ledger's
# scene_extra_ledger.jsonl, core.look_render_ledger's look_render_ledger.jsonl (J-1899), provisions.json, room_state.json, the
# garden/study/shore/wood files, ... --
# the whole docs/staged/world_store_write_fence.md inventory). That is harmless TODAY because no code path
# is both live and named: scripts/run_nascence.py (the only mark_live() caller) never calls
# activate_profile(), and every activate_profile() caller (debate, smoke_test, _verify_*, ...) is non-live,
# so guard_path() refuses their world-store writes outright (D-0179). It becomes a real hazard the day a
# process is BOTH: a live named-profile boot would write Du's own world files. Rebasing just two of the
# ~24 world-store modules would only make a half-separate world, so the choice (own world per profile vs
# shared Du world) is left to that day -- this warning is the tripwire that makes the combination loud.
# scripts/_test_j1883_world_store_profile_scope.py pins the "no code path is live AND named" premise.
def _warn_if_live_named_profile(where: str) -> None:
    if LIVE and ACTIVE_BASE != _DATA:
        logger.warning(
            "profile: %s -- this process is LIVE and a NAMED profile is active (%s): the world-store modules "
            "(cat_state.json, scene_extra_ledger.jsonl, provisions.json, ...) are NOT rebased by "
            "activate_profile() and would write Du's own world files (J-1883/F-2489 follow-up; "
            "docs/staged/world_store_write_fence.md)", where, ACTIVE_BASE)


def mark_live() -> None:
    """Declare this process the one real live Du boot. Call exactly once, at startup, before any
    world-store writer can run — scripts/run_nascence.py does this inside its existing __main__
    guard (the one J-0576 added for the log-handler fix, commit 91c547f: one guard, two purposes)."""
    global LIVE
    LIVE = True
    _warn_if_live_named_profile("mark_live()")


# One warning per resolved path, not per call — a hot-loop writer (e.g. sensorium's tick-driven
# _save()) would otherwise spam the log every tick. Keying on the path string alone (rather than a
# literal (module, path) pair) is sufficient in practice: every writer this pass guards resolves its
# own module-level path constant, so path already implies module — with one known exception,
# core/garden.py and core/garden_life.py both legitimately share data/garden_events.jsonl, where
# this just means the first of the two to hit it wins the one warning log line. The refusal itself
# (the actual protection, below) is never deduped and fires on every non-live call regardless of
# warning state, so that exception costs a log line, not any safety.
_warned: set = set()


# D-0200 (ruled 2026-09-09, built J-0840; defect F-1083/J-0759, independently re-hit F-1098/F-1101):
# lab_env.isolate() -- the job-queue toolchain's own sanctioned isolation harness, and the one this
# module's own docstrings have named as a legitimate upstream redirector since J-0610 -- puts its lab
# dir at data/_lab/<timestamp>/, still a subpath of _DATA, so the relative_to() check above never
# cleared for it and every fenced module raised NonLiveWriteError straight through an "isolated" run.
# Fix chosen: an explicit, narrow allow-list here (D-0200's option B) rather than moving the lab root
# out of data/ (option A) -- moving it would have orphaned ~150 existing, finding-cited lab dirs from
# scripts/retention.py's D-0156 labs class and broken every `data/_lab/<stamp>` citation in
# findings.jsonl/docs/, for no gain in safety. This is NOT a widening of the fence: no live writer
# ever resolves a path under data/_lab/ (Du's own boot writes data/<file>; a named profile writes
# data/profiles/<name>/...), so a write landing there is by construction a sandboxed one. The
# allow-list is deliberately strict: the FIRST component must be exactly `_lab`, there must be at
# least one sandbox dir below it (data/_lab/<file> directly stays refused), and no `..` anywhere
# (data/_lab/x/../garden.json stays refused). data/lab/ (no underscore -- the old cat-harness path
# F-1081 already moved to a temp dir), data/_not_live/, data/profiles/ all stay refused exactly as
# before: activate_profile() rebases those constants itself and never needs this branch.
#
# F-1270/J-0908 note: lab_env.py's lab dir is ALWAYS physically under C:\Nascence\data\_lab\<stamp>
# (its own _ROOT is hardcoded, never relative to a worktree) -- so from a worktree-based process this
# path is a subpath of _CANONICAL_DATA, not this process's own _DATA. _is_lab_sandbox() itself doesn't
# care which root produced `rel`; guard_path()'s own two-root check (_data_relative(), below) is what
# makes sure a worktree-based isolate() call still reaches this allow-list instead of falling through
# the gap F-1270 closed ("outside _DATA -> assume already redirected, no further check").
_LAB_SANDBOX_DIR = "_lab"


def _is_lab_sandbox(rel: Path) -> bool:
    """True iff `rel` (a path already made relative to a recognized data root) is
    data/_lab/<sandbox-dir>/<...>."""
    parts = rel.parts
    return (len(parts) >= 3
            and parts[0].lower() == _LAB_SANDBOX_DIR
            and ".." not in parts)


def _data_relative(path: Path):
    r"""`path` made relative to whichever data root recognizes it: THIS process's own `_DATA` first
    (the common case -- a named profile, a test's own monkeypatch, or simply _ROOT already being the
    real root), then the fixed `_CANONICAL_DATA` (F-1270/J-0908: catches a path that IS the real live
    data/ tree even when this process's own `_DATA` is not it -- e.g. this copy of the module was
    imported from a git worktree rather than C:\Nascence). Returns None if `path` sits outside BOTH --
    a genuine upstream redirect (a tempdir, a different profile, lab_env's own DB_PATH, ...).
    """
    for root in (_DATA, _CANONICAL_DATA):
        try:
            return path.relative_to(root)
        except ValueError:
            continue
    return None


class NonLiveWriteError(RuntimeError):
    """Raised by guard_path() when a non-live process attempts to write to a real world-store path
    under data/. D-0179 (ruled 2026-09-06, implemented J-0704/J-0706): a non-live write is refused
    outright rather than silently redirected to data/_not_live/<file> as originally shipped
    (J-0610/F-0995) — the founder's own concern was that a diagnostic or lab script expecting a real
    write to succeed could read a silent data/_not_live/ redirect as its own false-negative success,
    a risk a warning log alone might not surface if nobody is watching it at the time. Call
    profile.mark_live() at startup if this genuinely is the one real live Du boot (see
    scripts/run_nascence.py's __main__ guard), or use lab_env.isolate() / a named profile if this is
    a diagnostic/lab script that should redirect its writes on purpose instead of hitting the fence."""


def guard_path(path: Path) -> Path:
    r"""
    Return `path` unchanged if this process is live (mark_live() was called), if `path` is already
    redirected outside the default data/ root by something upstream (activate_profile(), a test's own
    monkeypatch), or if it sits inside a lab_env.isolate() sandbox, data/_lab/<dir>/... (D-0200 —
    the one explicitly allow-listed subtree of data/, see _is_lab_sandbox()). Otherwise — an importer that never declared itself live,
    resolving a write straight at a default data/ path — log one warning per path and raise
    NonLiveWriteError (D-0179, 2026-09-06) naming the real path that was attempted, rather than
    silently redirecting the write as the original J-0610 design did.

    Call this at the point a writer resolves its path (`profile.guard_path(_F)`), not once at import
    time — the module-level constants themselves must stay untouched so a later mark_live() (or a
    profile activation that moves the same constant outside data/) is still honored by every
    subsequent call. Every one of this fence's ~19 call sites across the 19 inventoried modules now
    resolves its path with this call BEFORE its own try/except-wrapped I/O (not inside it) —
    specifically so this exception is never silently caught by that same fail-open net meant for
    genuine disk errors. See docs/staged/world_store_write_fence.md (J-0704/J-0706) for the full
    before/after and the one known, deliberate limitation: a caller that goes through a module's own
    public act()-style dispatcher (rather than calling a private _save()/_log() writer directly) may
    still have this exception swallowed by that dispatcher's OWN separate, pre-existing catch-all —
    a different, wider piece of architecture this job did not touch (see F-1024 for which
    dispatchers were checked, and its spawned follow-up job for closing that gap).

    "Already redirected outside data/" is checked against TWO roots, not one (F-1270/J-0908,
    2026-09-12): this process's own `_DATA`, and the fixed `_CANONICAL_DATA` — see `_data_relative()`.
    A path outside `_DATA` is NOT by itself proof of a genuine upstream redirect: it must also be
    outside `_CANONICAL_DATA` before this fence honors it as one. Without that second check, a
    process whose own `_DATA` differs from the real one (a git-worktree checkout, the standard
    convention for Tier-3 work since J-0590) would wave through any path constant that happened to be
    set to the literal live `C:\Nascence\data\...` path — an absolute cross-check, or a forgotten
    redirect on a sibling global — with zero protection, zero warning, LIVE never even consulted. See
    F-1270 for the direct, reproduced demonstration (11 real rows appended to the live
    provisions_log.jsonl with no exception raised anywhere in the call chain, pre-fix).
    """
    if LIVE:
        return path
    rel = _data_relative(path)
    if rel is None:
        return path      # outside data/ under every root this fence recognizes -- an upstream redirect
    if _is_lab_sandbox(rel):
        return path      # data/_lab/<dir>/... -- lab_env.isolate()'s own sandbox (D-0200, see below)
    key = str(path)
    if key not in _warned:
        _warned.add(key)
        logger.warning(
            "guard_path: non-live process attempted to write %s -- refused, not redirected "
            "(call profile.mark_live() at startup if this IS the real live Du process)",
            rel,
        )
    raise NonLiveWriteError(
        f"non-live process attempted to write to data/{rel} -- refused (D-0179). This process never "
        f"called profile.mark_live(), so it is not the real live Du boot. If it should be, call "
        f"mark_live() at startup; if it's a diagnostic/lab script that needs to write safely either "
        f"way, use lab_env.isolate() or a named profile to redirect this path BEFORE calling in, "
        f"rather than relying on this fence's own fallback."
    )


def profile_dir(name: str | None) -> Path:
    """Resolve a profile name to its data directory (without creating it)."""
    if name in _ROOT_ALIASES:
        return _DATA
    return _DATA / "profiles" / name


def activate_profile(name: str | None) -> Path:
    """
    Point every per-agent path constant at the given profile's data dir, and return that dir.
    Idempotent and safe to call once at startup. For a root-alias name this is effectively a
    no-op against the existing layout (Carl), so the default path is preserved exactly.
    """
    base = profile_dir(name)
    base.mkdir(parents=True, exist_ok=True)
    (base / "memory").mkdir(parents=True, exist_ok=True)
    (base / "identity").mkdir(parents=True, exist_ok=True)

    # core.memory.store — the episodic/semantic/shadow/procedural DB
    from core.memory import store
    store.DB_PATH = base / "memory" / "nascence.db"

    # nodes.subconscious_node — T1..T5 state, the synthesis log, and the axiom T4 writes
    from nodes import subconscious_node as scn
    scn._DATA_DIR    = base
    scn._STATE_FILE  = base / "subconscious_state.json"
    scn._SC_LOG_FILE = base / "subconscious_log.jsonl"
    scn._AXIOM_FILE  = base / "identity" / "axiom.json"

    # core.tension_ledger — reads the subconscious tension state (T6)
    from core import tension_ledger
    tension_ledger._STATE_FILE = base / "subconscious_state.json"
    tension_ledger._ATTEMPTS_LOG = base / "tension_judge_attempts.jsonl"   # J-3050

    # core.orchestrator — affect telemetry + the T2 read-back source
    from core import orchestrator
    orchestrator._AFFECT_LOG       = base / "affect_log.jsonl"
    orchestrator._SUBCONSCIOUS_LOG = base / "subconscious_log.jsonl"
    # J-1788 (2026-10-04): the pre-affect best-of-N shadow log (observe-only, D-0349's reader) -- a named-
    # profile boot must not write its cycles into the root profile's (Du's) own instrument.
    orchestrator._PRE_AFFECT_BEST_LOG = base / "pre_affect_best_shadow.jsonl"
    # J-2250 (D-0450): the pre-affect self-echo exclusion shadow log, same reasoning as the line above.
    orchestrator._PRE_AFFECT_SELF_ECHO_LOG = base / "pre_affect_self_echo_shadow.jsonl"
    # F-0665/F-0670 (2026-09-02): the permanent founder-conversation record. Missing this rebase
    # is exactly the bug this whole function exists to prevent (see the 2026-08-19 note below) —
    # caught live: scripts/smoke_test.py's first run wrote 3 fake test exchanges straight into the
    # REAL data/founder_conversation_log.jsonl because this line didn't exist yet.
    orchestrator._FOUNDER_LOG      = base / "founder_conversation_log.jsonl"
    # D-0134 (2026-09-03): the founder-memory route's own shadow log (what was recalled, per cycle).
    orchestrator._FOUNDER_RECALL_LOG = base / "founder_recall_log.jsonl"
    # J-1824 / F-2458 (2026-10-06, the J-1718 dynamic write audit): the Phase-3 correlation telemetry
    # (one row per cycle from _log_correlation) was the one orchestrator constant this hand-rebase
    # block never covered, so a named-profile human cycle appended its currencies to the ROOT
    # profile's data/correlation_log.jsonl. Same shape as the lines above; root alias = identity.
    orchestrator._CORRELATION_LOG = base / "correlation_log.jsonl"

    # ── Instrument / evidence modules (2026-07-02) ────────────────────────────────────────────────
    # The observe-first instruments (06-30 → 07-02) also store their paths as module-level constants
    # — without rebasing them, a '_smoke' boot POLLUTES the real evidence logs that gate flag-flips
    # (found in the 07-02 systems check: smoke rows in error_records, guidance captures — one
    # smoke-taught belief even PROMOTED into the belief store — conv-shadow, critic-alongside,
    # provenance, plus silent nudges to competence/symbol state). Generic rebase: every module-level
    # Path constant that lives under the root data/ dir is re-pointed into the profile dir. For a
    # root-alias profile base == data/, so the rebase is an identity no-op (Carl untouched).
    def _rebase_module_paths(mod_name: str) -> None:
        # Idempotent: the ORIGINAL root-data path is captured once per (module, attr) and every rebase
        # maps original → base/rel, so repeated / switched activations never nest profile dirs.
        try:
            import importlib
            m = importlib.import_module(mod_name)
            for attr, v in list(vars(m).items()):
                if not isinstance(v, Path):
                    continue
                key = (mod_name, attr)
                orig = _ORIG_PATHS.get(key)
                if orig is None:
                    try:
                        rel = v.relative_to(_DATA)
                    except ValueError:
                        continue          # a path outside data/ (e.g. a model file) — leave it
                    if rel.parts and rel.parts[0] == "profiles":
                        continue          # already profile-scoped — never treat as an original
                    _ORIG_PATHS[key] = v
                    orig = v
                setattr(m, attr, base / orig.relative_to(_DATA))
        except Exception as exc:
            logger.debug("profile rebase skipped for %s: %s", mod_name, exc)

    for _mod in (
        "core.error_pathway", "core.epistemic_state", "core.guidance_learning", "core.self_implication",
        "core.commitment_ledger", "core.decomposed_critic", "core.conflict_trace", "core.curator",
        "core.recall_provenance", "core.retraction_ledger", "core.self_efficacy", "core.competence",
        "core.symbol_tracker", "core.satisfaction", "core.narrative_quality", "core.affect_labeling",
        "core.sitting", "core.self_mirror", "core.training_log", "core.self_claims", "core.journal",
        "core.task_constraints",
        # 2026-08-19 (health-check finding): 7 more modules with module-level data Path constants that
        # were never added here — a second profile would silently read/write Carl's own files instead
        # of its own (journal_rollup shares journal's WEEK_*.md + rollup-state flag; pulse_shadow,
        # geometry_census, and psyche_graph would each build their census/graph from Carl's live state;
        # telemetry/broadcast/train_metrics would mix HUD/buffer/length data across instances).
        "core.journal_rollup", "core.pulse_shadow", "core.geometry_census", "core.psyche_graph",
        "core.telemetry", "core.broadcast", "core.train_metrics",
        # 2026-08-19: added at build time, not found-later — same rebase this whole loop exists for.
        "core.self_interrogation",
        # F-0671 (2026-09-02, caught by scripts/smoke_test.py the same way the 08-19 batch was
        # found): core.mood's _FP_LOG was missing — a second profile's felt-preamble entries would
        # have written into Carl's own data/felt_preamble_log.jsonl.
        "core.mood",
        # Same audit, same day: nodes.inner_monologue_node was ALSO missing (pre-existing, found
        # while adding conversational_redirect.md's Phase 0 shadow log to this exact module) --
        # monologue_log.jsonl itself, not just the new shadow file, would have leaked the same way.
        "nodes.inner_monologue_node",
        # F-2283/J-1690 (2026-10-03): core.social_model's _SOCIAL_STATE_PATH (data/social_state.json --
        # Du's LIVE relational state) was missing. Since J-1358 (9b50d6b, merged 2026-09-26) the
        # orchestrator save()s it on EVERY input_type == "human" cycle (core/orchestrator.py,
        # _compute_attention_vector), so a '_smoke' / named-profile boot that ran human cycles through
        # a real Orchestrator (scripts/smoke_test.py, debate.py, _verify_genesis.py) would have
        # rewritten the REAL file each cycle -- fake exchanges advancing relational_trust /
        # cycles_since_spike, and a probe containing a _CORRECTION_SIGNALS phrase leaving a spike on
        # disk for the next real boot to replay (F-1919's own harm). Same family as F-0665/F-0670 and
        # F-0671 above. SocialModelManager._load()/save() read the module global at call time, so the
        # rebase takes effect; for a root alias (Carl) base == data/ and this stays an identity no-op.
        # A lab_env.isolate() harness is NOT covered by this loop -- it must name
        # (core.social_model, ["_SOCIAL_STATE_PATH"]) in `also=` itself.
        "core.social_model",
        # J-1824 / F-2458 (2026-10-06): the J-1718 DYNAMIC write audit (a sys.addaudithook raising on
        # every real-data write under a throwaway profile, one real Orchestrator human cycle) caught
        # 13 attempted writes/opens from modules this tuple never named -- the static scan (F-2342)
        # could only say "115 candidates", the hook said which ones a cycle actually reaches:
        #   core.arousal              _DATA/_STATE/_LOG/_REGIME_STATE  (arousal_state.tmp, arousal_shadow.jsonl,
        #                              arousal_regime_shadow_state.tmp -- every human cycle)
        #   core.emotion_construction _DATA/_SHADOW_LOG/_AR_SHADOW_LOG (emotion_construction_shadow.jsonl; and
        #                              _affective_retrieval_shadow's sqlite3.connect(_DATA/memory/nascence.db)
        #                              -- a READ of Du's real memory from a throwaway profile, fixed by the
        #                              same _DATA rebase)
        #   core.attention_schema_loop _DATA/_LOG/_STATE                (ast_loop_shadow.jsonl)
        #   core.conversational_action _LOG                             (conversational_action_log.jsonl)
        #   core.unified_inference    _UNIFIED_LOG                      (unified_inference_log.jsonl)
        #   core.memory.store         _RETRIEVE_LATENCY_LOG             (retrieve_latency_probe.jsonl; only
        #                              DB_PATH was ever set by hand above -- the generic loop re-derives
        #                              the same DB_PATH, so this is consistent, not a double rebase)
        #   core.coupling_rides       _DATA/_LOG (derived from a repo _ROOT = Path(__file__).resolve()
        #                              .parent.parent -- _DATA itself is under data/, so the generic loop
        #                              does catch it; verified from a worktree by
        #                              scripts/_test_f2458_rebase_isolation.py). Fenced since J-1821 too:
        #                              a non-live named profile is refused, a live one writes its own dir.
        #   core.wandering            _LOG -- needed a code edit first: _log_trail() built the path inline
        #                              from __file__ at call time, so there was no constant to rebase.
        #                              Hoisted (byte-identical for the root profile) the same day.
        #   core.epistemic_affordance_advisor LOG_JSONL_PATH -- was anchored to a literal absolute
        #                              Path("c:/Nascence") (the one such constant in core/), so from a
        #                              worktree it hit the REAL tree (F-2458 row 9) AND this loop could
        #                              not see it (outside this process's _DATA). Re-anchored to __file__
        #                              the same day (identical for the live boot); now caught here.
        # One more from the same audit is handled by an explicit line above, not here: core.orchestrator's
        # _CORRELATION_LOG (sibling of the hand-rebased affect/founder logs). Per D-0179/D-0200 a
        # rebased module is not thereby fenced, and guard_path() still refuses data/profiles/<name>/
        # for a non-live process -- this rebase only decides WHICH tree a write aims at; mark_live()
        # decides whether it lands at all. Importing core.epistemic_affordance_advisor here (it was
        # previously first imported lazily inside the human cycle) is safe: it imports only
        # core.memory.store and core.affordances, both already loaded by the orchestrator above.
        "core.arousal", "core.emotion_construction", "core.attention_schema_loop",
        "core.conversational_action", "core.unified_inference", "core.memory.store",
        "core.coupling_rides", "core.wandering", "core.epistemic_affordance_advisor",
        # J-1867 / F-2489 (2026-10-07): the J-1718 audit RE-RUN on the J-1824-fixed tree (the first run
        # stopped at the first unclean cycle; this one ran all 3 probes) found core.associative_recall --
        # reached from the correction-probe cycle's memory recall -- writing 6 times to the tree's own
        # data/ top level: _save_persisted (embedding_matrix.tmp.npz -> embedding_matrix.npz, built from
        # _EMB_CACHE) and the four shadow logs _LOG / _LENS1_LOG / _LENS2_LOG / _LENS3_LOG. All are plain
        # module-level Path constants under data/, so naming the module here is the whole fix. Beyond
        # log noise this was a DATA-CORRUPTION leak: _refresh() reads the persisted matrix, drops every id
        # absent from the CURRENT DB's metadata, and _save_persisted()s the filtered result -- so a named
        # profile with its own (small) memory DB would have rewritten Du's real embedding_matrix.npz
        # down to the profile's handful of fragments. Rebased, the profile builds its own matrix from its
        # own DB (cheap: the matrix decode is incremental and a fresh profile DB is tiny).
        "core.associative_recall",
        # J-1867, same re-run: two more per-agent instrument logs whose writers are guard_path()-fenced
        # (J-1815/J-0610), so the audit hook never SAW them (the fence raises before any open) -- the
        # driver's own stderr showed "non-live process attempted to write retrieval_probe_log.jsonl" and
        # "... r_shadow.jsonl" (no profiles\<name>\ prefix = unrebased). A non-live process is safe; a LIVE
        # named-profile boot (mark_live() + a profile) would have appended to Du's own instrument files.
        # Plain module-level data/ Path constants, nothing to hoist.
        "core.retrieval_probe", "core.r_shadow",
        # J-1867, 2nd audit re-run after the fix above (the cycle path is stochastic -- LLM replies decide
        # which shadow instruments fire): core.reentry (_DATA/_LOG/_STATE) from orchestrator._reentry_shadow
        # -> settle_shadow -> _save_state (reentry_state.tmp) and _log_row (reentry_shadow.jsonl), UNFENCED
        # (no guard_path) -- a genuine hook-visible leak, cycle 3 of that re-run.
        "core.reentry",
        # J-2245 (D-0442): core.farewell_echo._LOG (voice_quote_block_log.jsonl), written from voice_node and
        # store.retrieve() on every voice build / farewell retrieve; fenced with guard_path, named here so a
        # live named-profile boot writes its own copy, not Du's.
        "core.farewell_echo",
        # J-2297 (D-0445 a): core.internal_context_gate._LOG (internal_cycle_context_shadow.jsonl), written
        # from orchestrator after voice on internal cycles; fenced with guard_path.
        "core.internal_context_gate",
        # J-2576 (F-3306): core.recall_served_log._LOG (recall_served_log.jsonl), written from orchestrator
        # just before voice on every voiced cycle; fenced with guard_path.
        "core.recall_served_log",
        # J-3310 (D-0552): core.memory.key_shadow._LOG (key_shadow.jsonl), written from orchestrator
        # _retrieve_memory beside the lens shadows; fenced with guard_path.
        "core.memory.key_shadow",
        # J-3319 (D-0637): core.chapter_descent_shadow._LOG (chapter_descent_shadow.jsonl), written from
        # orchestrator _retrieve_memory beside the key shadow; fenced with guard_path.
        "core.chapter_descent_shadow",
        # J-3402 (D-0682): core.urgency_shadow._LOG (training/urgency_shadow.jsonl), written from orchestrator at
        # the three urgency consumers; fenced with guard_path.
        "core.urgency_shadow",
        # J-4420: core.rewarm_shadow._LOG (rewarm_shadow.jsonl), written off-thread after voice / idle thought;
        # fenced with guard_path.
        "core.rewarm_shadow",
    ):
        _rebase_module_paths(_mod)

    # J-1867: associative_recall._cache holds the embedding matrix + metadata built from WHICHEVER DB
    # and persisted file were active when it was last refreshed, and is not keyed to either. Drop it on
    # every activation so a re-activation (switched profile in one process: tests, harnesses) can never
    # recall from the previous profile's matrix. For the normal single activation at startup the cache
    # is still empty, so this is a no-op and the root profile is byte-identical.
    try:
        from core import associative_recall as _ar
        _ar._cache.update(ts=0.0, M=None, ids=None, imp=None, age=None, walled=None, origin=None)
    except Exception as exc:
        logger.debug("associative_recall cache reset skipped: %s", exc)

    global ACTIVE_BASE
    ACTIVE_BASE = base
    _warn_if_live_named_profile("activate_profile()")

    logger.info("Profile activated: %s -> %s", name or "carl (root)", base)
    return base
