"""In-vitro for the train working-state (lever 1, observe-first). No live process touched.
Checks: (1) the schema toggles `state` on/off by mid_train; (2) the working-state carries +
overwrites correctly across a simulated thought-train; (3) the observe log writes a row."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.inner_monologue_node import InnerMonologueNode, _DATA_DIR, TRAIN_HOLD

# J-0697, 2026-09-06/07 (F-1006): step 1's own _build_system_prompt(mid_train=False) call below
# transitively reaches core.social_moves.observe() (reads+writes data/social_moves_state.json,
# appends data/social_moves.jsonl), and step 3's _log_train_step() call transitively reaches
# core.memory_edges.log_co_recall() (appends data/co_recall_ledger.jsonl unconditionally, even at
# n_ids=0), which itself calls core.opponent_process.observe_activation() (reads/writes
# data/opponent_process_state.json, appends data/opponent_process_shadow.jsonl). Every module in
# both chains was previously protected only by an accident of HOW this script gets run (job-run's
# own Tier-3 worktree dispatch happens to keep every Path(__file__)-relative global inside that
# worktree's own separate data/ copy) -- a direct run against the live C:\Nascence tree with no
# worktree wrote real synthetic rows into all four live files/states on every invocation. Fixed the
# same way core.trains/core.judge_panel are already redirected in Part 2 below (D-0146/J-0562):
# reassign each module's own file-valued globals to a scratch path BEFORE the first risky call,
# which transparently redirects every later write for the rest of this process's life (confirmed by
# reading all three modules' source: social_moves._LOG/_STATE, memory_edges._CO_LEDGER, and
# opponent_process._LOG/_STATE are each looked up by name at call time inside their own read/write
# functions, not re-derived from the modules' own `_DATA` directory global on every call -- so
# `_DATA` itself never needs patching here, only the four file-valued globals the actual file I/O
# in this call path touches; verified empirically with a fail-closed sys.addaudithook write guard
# pointed at the live tree directly, same technique as J-0518/S-0033: 0/2 named-file hits after this
# redirect vs 2/2 before it). Deliberately does NOT touch `_DATA_DIR` (nodes.inner_monologue_node's
# own global) or train_state_log.jsonl -- check (3) below tests THAT write directly and is meant to
# hit the real file; F-1006 only ever named the four transitive files below as the isolation gap.
# J-0711, 2026-09-07 (F-1020): the same step-1 call also transitively reaches
# core.intentions.pending_text() (nodes/inner_monologue_node.py's own "INTENTIONS (2026-08-22)"
# block, a few lines before the social_moves call above) -- pending_text() calls _load(d);
# _lapse(d); ...; _save(d) UNCONDITIONALLY (core/intentions.py), writing data/intentions.json (full
# overwrite) on every call, plus data/intentions_log.jsonl whenever _lapse() actually lapses an
# item. Unlike the three modules above (pure observe-only shadow/ledger instruments), core.intentions
# is a REAL, live-consequential mechanism injected into Du's actual system prompt -- a stray call
# here can prematurely trip a real intention's MAX_REMINDERS counter, suppress its next real
# reminder (REMIND_AFTER_S gate), or lapse a genuinely-still-open real intention outright, not just
# pollute an analytics log. Fixed the same way: core.intentions._F/_LOG are each looked up by name
# at call time inside _load()/_save()/_log() (confirmed by reading core/intentions.py lines 29-31,
# 39-60), so reassigning them here redirects every later write for the rest of this process's life.
# Reuses the SAME _p1_scratch dir as the three modules above, not a new one.
# J-1204, 2026-09-22 (F-1697, found by J-1198): the SAME step-1 `_build_system_prompt()` call also
# transitively reaches core.sensorium.world_calls() -> core.garden._load() -- empty/fresh state (no
# real data/garden.json in a bare worktree) bootstraps and calls _save(force=True) unconditionally --
# and, on the same call, core.wood_life's own analogous world-store writer. Neither is a live-
# consequential mechanism like core.intentions above (both are pure world-state stores, same class
# as social_moves/opponent_process), but UNLIKE those, this pair was never redirected, so a bare run
# (outside lab_env.isolate(), which the Du-offline lab window's own rules forbid: a ~670 MB DB copy
# under a disk that runs tight) hit D-0179's write fence (core.profile.guard_path) on both: garden's
# own _save() raise is UNCAUGHT past _load()'s own deliberate reraise (J-0726 comments in both
# modules let NonLiveWriteError through on purpose) and crashes the whole script; wood_life's
# equivalent attempt is (today) swallowed by a broader catch-all elsewhere in its own call chain, so
# it never crashes but still logs guard_path's own refusal warning and never performs the write it
# meant to -- confirmed directly: a bare run of this file's Part 1 alone (scripts under test, no
# lab_env.isolate(), no upstream guard_path patch) printed BOTH "guard_path: non-live process
# attempted to write wood_life.json -- refused" and "...garden.json -- refused" before dying on
# garden's own NonLiveWriteError; J-1198's own lab runner (scripts/lab_j1198_walkback_replay.py)
# had worked around exactly this by monkeypatching core.profile.guard_path itself, process-wide, for
# its own launch only -- a workaround this job removes the need for by fixing it here instead, the
# same discipline as the four modules above. Fixed identically: reassign each module's own
# file-valued globals to the SAME _p1_scratch dir BEFORE the first risky call (confirmed by reading
# core/garden.py and core/wood_life.py source: both resolve `_F`/`_LEDGER`/`_EVENTS` by name at call
# time inside `_save()`/`_load()`/`_log()`, never re-derived from `_DATA` per call, so reassigning the
# attributes here is sufficient -- no third or further module surfaced in the bare re-run below once
# these two were added). core/profile.py and core/garden.py/core/wood_life.py themselves are
# untouched -- D-0179's fence stays exactly as ruled; only this script's own isolation is additive.
from core import social_moves as _sm_p1, memory_edges as _medges_p1, opponent_process as _oppo_p1
from core import intentions as _intent_p1
from core import garden as _garden_p1, wood_life as _wood_p1
_p1_scratch = _DATA_DIR.parent / "scratch" / "train_state_invitro_part1"
_p1_scratch.mkdir(parents=True, exist_ok=True)
_sm_p1._LOG = _p1_scratch / "social_moves.jsonl"
_sm_p1._STATE = _p1_scratch / "social_moves_state.json"
_medges_p1._CO_LEDGER = _p1_scratch / "co_recall_ledger.jsonl"
_oppo_p1._LOG = _p1_scratch / "opponent_process_shadow.jsonl"
_oppo_p1._STATE = _p1_scratch / "opponent_process_state.json"
_intent_p1._F = _p1_scratch / "intentions.json"
_intent_p1._LOG = _p1_scratch / "intentions_log.jsonl"
_garden_p1._F = _p1_scratch / "garden.json"
_garden_p1._LEDGER = _p1_scratch / "garden_ledger.jsonl"
_garden_p1._EVENTS = _p1_scratch / "garden_events.jsonl"
_wood_p1._F = _p1_scratch / "wood_life.json"
_wood_p1._EVENTS = _p1_scratch / "wood_events.jsonl"
_wood_p1._LEDGER = _p1_scratch / "wood_ledger.jsonl"

n = InnerMonologueNode()

class _S:  # minimal stand-in for CognitiveState
    spirit_name = "渡"

# (1) schema toggles
sp_off = n._build_system_prompt(_S(), wandering=False, mid_train=False)
sp_on  = n._build_system_prompt(_S(), wandering=False, mid_train=True)
assert '"state"' not in sp_off and "state:" not in sp_off, "state leaked into non-train schema"
# J-0562, 2026-09-05: this assert hardcoded the PRE-TRAIN_HOLD wording ("RE-STATE where the whole
# thread") and has been silently failing on every run since TRAIN_HOLD went permanently live
# 2026-08-16 (nodes/inner_monologue_node.py:181) -- confirmed by running this file, unmodified,
# against HEAD in an isolated worktree (git worktree add), same AssertionError. TRAIN_HOLD's own
# branch uses different text ("the single NEW point this step established"); checking the wrong
# one made this in-vitro test a false negative on every real run for three weeks, not a caught
# regression. Fixed to check whichever branch is actually live, per the same TRAIN_HOLD flag the
# node itself branches on -- nodes/inner_monologue_node.py is NOT touched, only this test's own
# stale expectation.
_state_marker = ("the single NEW point this step established" if TRAIN_HOLD
                 else "RE-STATE where the whole thread")
assert '"state"' in sp_on and _state_marker in sp_on, "state missing in mid_train schema"
print(f"[1] schema toggle OK — state field appears only when mid_train=True (TRAIN_HOLD={TRAIN_HOLD})")

# (2) carry + overwrite across a simulated thought-train
# step 0 -> 1: model gives a state
n._train_len, n._train_kind, n._train_thread, n._train_state = 0, "thought", "", ""
# emulate the continue branch logic for a thought-train with a fresh model state
new_state = "Established: my name is a crossing. Open: what do I ferry? Heading: toward the act not the noun."
n._train_len += 1; n._train_kind = "thought"; n._train_thread = "thought A"
n._train_state = new_state or n._train_state
assert n._train_state == new_state, "carry-in failed"
# step 1 -> 2: model returns EMPTY state -> prior must be kept (overwrite-with-fallback)
n._train_len += 1; n._train_thread = "thought B"
n._train_state = "" or n._train_state
assert n._train_state == new_state, "fallback-keep-prior failed"
# step 2 -> 3: model returns a NEW state -> overwrite (not append)
state2 = "Established: ferrying is the work. Open: across what? Heading: the gap between selves."
n._train_thread = "thought C"
n._train_state = state2 or n._train_state
assert n._train_state == state2 and new_state not in n._train_state, "overwrite (not append) failed"
print("[2] carry/overwrite OK — fresh state overwrites, empty keeps prior, never appends")

# (3) the observe log writes
log = _DATA_DIR / "train_state_log.jsonl"
before = log.read_text(encoding="utf-8").count("\n") if log.exists() else 0
n._recent_vecs = [[0.1, 0.2, 0.3]]   # a prior-thought vec so restate_sim computes
n._log_train_step("a moving thought C", state2, vec=[0.1, 0.2, 0.31])
after = log.read_text(encoding="utf-8").count("\n")
assert after == before + 1, "log row not written"
row = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
assert row["model_gave_state"] is True and row["new_state"].startswith("Established: ferrying")
assert "restate_sim" in row
print(f"[3] observe-log OK — restate_sim={row['restate_sim']} model_gave_state={row['model_gave_state']}")

print("\nALL PASS — train working-state wired, observe-first.")


# ============================================================================================
# PART 2 — STEP 2 (i)+(ii): offline fork/prove/disprove/merge replay lab
# (J-0562, 2026-09-05, docs/plans/train_split_merge.md — "Step 2 build order (revised)")
# ============================================================================================
# Sub-step (i)'s numbers live in the plan doc itself (a new "Kill criteria as numbers (PROPOSED)"
# block under the auditor's §4). This half of the file is sub-step (ii): replay REAL logged
# would-be-close moments (data/train_length_log.jsonl closes joined to their
# data/monologue_log.jsonl / data/train_state_log.jsonl rows) through an actual fork -> prove
# (Lane 1's own lane, 127.0.0.1:11433) / disprove (Lane 2's real judge_panel mechanism, claim
# ONLY -- the lane2_the_witness.md boundary, never ledger/self-narrative) -> merge -> cargo pass,
# using core/trains.py's real registry code for the fork/merge lineage.
#
# "Offline" per the briefing means no LIVE data/ STORE is touched and nothing feeds back into
# the live loop -- NOT "no network calls". The design explicitly names live apparatus ("Lane 1's
# lane", "Lane 2's _judge_prior panel"), and this project's own precedent (scripts/train_lab.py,
# 2026-08-16) already calls Lane 1's live hot lane directly for exactly this kind of controlled
# lab read, neutralising telemetry the same way. Below does the same, plus redirects
# core/trains.py's and core/judge_panel.py's own log-file globals to scratch/ (never data/)
# before a single fork/prove/disprove call happens, so the real registry/panel CODE runs for
# real but every write lands off the live path (verified by reading both modules' source: each
# computes its `_LOG` from a module-level `_DATA` at import time but reads the *current* global
# at call time, so reassigning the attribute after import is what actually redirects).
#
# D-0146 already ruled Step 2's three open defaults (2026-09-04): branch budget 1, fork-trigger
# thread-end-only, merge-as-ledger. This replay HONOURS those (no combinatorial sweep needed --
# D-0146 was ruled before this job started) but still measures the reason-gate-alone fork rate
# the kill criteria need either way (dosed_coupling.md's §5 "surprise line" note: reason-gating
# alone is expected to fail selectivity, and that failure is exactly what must be MEASURED here,
# not assumed).
#
# Kept deliberately small (N_PER_WINDOW below, overridable as argv[1]) out of consideration for
# the fact that Lane 1's hot lane and the judge hubs are LIVE, shared infrastructure -- Du may be
# thinking in real time on the same hot lane while this runs, and other job-queue agents may be
# hitting the same judge hubs in the same batch. Re-run with a larger N once this first batch has
# been read.

import asyncio
import bisect
import datetime as _dt
import statistics as _statistics
from collections import Counter, defaultdict

_ROOT = _DATA_DIR.parent  # _DATA_DIR imported from inner_monologue_node above == <repo>/data

# Pre-registered (F-0776): trains have been ~2 steps long since 08-17 for an unattributed reason,
# so the replay corpus is drawn from BOTH the pre-Step-1 "longer trains" era and the post-fix era,
# not fitted to one regime alone.
_WINDOW_A = (_dt.datetime(2026, 8, 3, tzinfo=_dt.timezone.utc).timestamp(),
            _dt.datetime(2026, 8, 17, tzinfo=_dt.timezone.utc).timestamp())
# J-0143's fix (F-0112) was first live at the 2026-08-24 21:41:56 restart (F-0773's own finding).
# 2026-08-25T00:00 UTC is a clean, conservative cutoff safely after that under either plausible
# timezone reading of that restart time -- avoids the ambiguous restart-churn hours right at the
# boundary rather than needing to resolve the NZT/UTC question exactly.
_WINDOW_B = (_dt.datetime(2026, 8, 25, tzinfo=_dt.timezone.utc).timestamp(),
            _dt.datetime.now(_dt.timezone.utc).timestamp())


def _load_jsonl(path) -> list:
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return rows


def _fork_rate_if_ungated(rows: list, lo: float, hi: float, trigger=("thread-end",)) -> dict:
    """Kill criterion #1, computed directly from the real log -- no LLM call needed. 'would-be
    close' = every train close in the window, any reason; 'triggering' = the ones the D-0146(b)
    fork-trigger (thread-end only) would actually fork."""
    in_window = [r for r in rows if lo <= r.get("ts", -1) < hi]
    total = len(in_window)
    triggering = sum(1 for r in in_window if r.get("reason") in trigger)
    by_reason = dict(Counter(r.get("reason") for r in in_window))
    return {"total_closes": total, "triggering_closes": triggering,
            "fork_rate": round(triggering / total, 4) if total else None, "by_reason": by_reason}


def _nearest_ml_close_row(ml_sorted: list, ml_ts: list, close_ts: float,
                          lo_off: float = -1.0, hi_off: float = 8.0):
    """monologue_log.jsonl row nearest `close_ts` with unresolved==False, within
    [close_ts+lo_off, close_ts+hi_off]. log_close fires slightly BEFORE the later _log() call
    that writes monologue_log (F-0773's own measured median gap +1.2s), so search mostly
    forward with a small backward allowance. Returns (row_or_None, gap_seconds_or_None)."""
    i = bisect.bisect_left(ml_ts, close_ts + lo_off)
    best, best_gap = None, None
    while i < len(ml_sorted) and ml_ts[i] <= close_ts + hi_off:
        row = ml_sorted[i]
        if row.get("unresolved") is False:
            gap = abs(ml_ts[i] - close_ts)
            if best_gap is None or gap < best_gap:
                best, best_gap = row, gap
        i += 1
    return best, best_gap


def _evenly_spaced(seq: list, n: int) -> list:
    if not seq or n <= 0:
        return []
    if n >= len(seq):
        return list(seq)
    step = len(seq) / n
    return [seq[int(i * step)] for i in range(n)]


def _ledger_for(tsl_by_tid: dict, train_id: "str | None", k: int = 3) -> list:
    if not train_id:
        return []
    rows_ = sorted(tsl_by_tid.get(train_id, []), key=lambda r: r.get("ts", 0))
    return [r.get("new_state") for r in rows_[-k:] if r.get("new_state")]


# RETARGETED 2026-09-08 (J-0802, per D-0181's founder ruling, 2026-09-08). The ORIGINAL wording
# below (kept in git history) asked the model to "PROVE the thought... deepen it, and see whether
# it truly holds up" -- an instruction with no pull away from restating the claim itself, only
# towards saying it more confidently. D-0181's own evidence trail (F-1034 n=80, F-1119/F-1142's
# n=16/n=80 disprove-prompt A/Bs) read the actual support text this prompt produced across all 80
# real replayed closes (docs/lab/train_split_merge_step2_replay_2026-09-07_supportchain.md) and
# found the dominant failure mode by far is exactly that: support items that restate the claim's
# own conclusion in surer words ("restates the claim; no independent reason given" is the single
# most common disprove objection text, verbatim or near-verbatim, across dozens of the 72/80
# objected events) and/or lean on self-sealing confidence language ("proves"/"confirms"/
# "validates") to assert rather than earn the point -- e.g. record #10's own support: "This PROVES
# that stability in knowledge doesn't come from avoiding change..." offers no fact separate from
# the claim it's attached to. D-0181 ruled: if this gets fixed, the fix belongs in Lane 1's own
# PROVE prompt (to generate independently-verifiable support), not in disprove's threshold/prompt,
# which the qualitative read already confirmed is discriminating correctly. This retarget acts on
# that ruling: explicitly names what counts as separate, checkable support (a sensation actually
# had, a concrete event, a known fact, or a point the thread's own ledger already established),
# gives one worked contrast (paraphrased from this plan doc's own PROTECTED cargo-shape example,
# Section "Cargo shape") so the model has a concrete anchor rather than only an adjective ("real"/
# "checkable"), explicitly bans the self-sealing "proves"/"confirms"/"validates" vocabulary, and
# -- per this plan's own Wu Wei law (point 3: "the prove branch may fail to prove... the merge may
# legitimately return undetermined") -- allows 0 items rather than pressuring the model to invent a
# reason where none is genuinely separate from the claim. Whether this actually lowers the
# disprove-objection rate, and whether it does so "for the right reason" (real evidence, not just
# different wording that still restates), is exactly D-0181's own named defeater question -- read
# for real in the n=80 re-run this same job performs, not assumed here from the prompt text alone.
_PROVE_SYSTEM = (
    "You are 渡, continuing a private train of thought that just closed as if finished. Find real "
    "SUPPORT for the thought below -- not the thought restated more confidently, but something "
    "SEPARATE from its own conclusion that gives it a reason: a specific sensation you actually "
    "had, a concrete event, a known fact, or a point this thread already established (see WHAT "
    "THIS THREAD HAD ALREADY ESTABLISHED below, if given) -- something another mind could go "
    "check. Example: for 'the fire draws me inside', weak support just re-asserts it ('the pull "
    "is real and undeniable'); real support names something else ('the warmth changed at the "
    "hearth', 'I chose to light it myself earlier', 'I came back in after being outside'). If the "
    "thought already names a sensation or event, point to that SPECIFIC detail rather than the "
    "thought's own reading of it. Never use words like 'proves'/'confirms'/'validates' -- if a "
    "point would only restate the conclusion in surer words, leave it out rather than include it; "
    "return fewer items, even none, before inventing a reason that is not there. Speak in your "
    "own first-person voice, plainly, no metaphor for metaphor's sake. Output ONLY JSON: "
    '{"support": ["a specific, separate reason in your own voice (<=30 words)", "..."]} with 0 to '
    "3 items."
)

# RETARGETED 2026-09-07 (J-0702, per D-0168's founder ruling, 2026-09-06). The ORIGINAL wording
# here asked the judge to find an objection to the CLAIM itself -- see git history / the 2026-09-05
# and 2026-09-06 lab reports for that framing's own results (F-0902 n=16: 0% objection;
# F-1005 n=80: 1.3%). D-0168's evidence trail (both those runs) found this was a near-universal
# rubber-stamp specifically because Du's real thread-end claims are mostly felt/experiential
# first-person declaratives -- there is little for a literal judge to falsify in a report of one's
# own felt experience. D-0168 ruled: retarget disprove to judge the claim's SUPPORT CHAIN instead
# (does the reasoning connecting the offered evidence to the claim actually hold), since the
# original control check already showed this same judge_panel mechanism discriminates fine given
# an actually-testable target. This is always testable, regardless of whether the underlying claim
# is a felt report: real replayed support text overwhelmingly uses confident, self-assertive
# language ("proving"/"confirms"/"validates") that restates the claim rather than independently
# justifying it (see e.g. record #1 in the 2026-09-05/06 reports) -- exactly the kind of gap this
# framing targets.
#
# TIGHTENED 2026-09-07, same day, after a real n=80 run of the FIRST (verbose) version of this
# prompt: 52/80 (65%) came back "UNDETERMINED how=unavailable", and the raw judge_panel_log rows
# showed WHY -- err1="parse" on 40/80, err2="parse" on 30/80, all returning in ~10-19s (nowhere
# near the 90s timeout), i.e. the two small judge models (mixtral/falcon3) were answering FAST but
# NOT in valid {"objection_found": bool, "why": str} JSON. `core/judge_panel.py`'s own `_ask()`
# hardcodes `num_predict: 80` for EVERY caller (a shared budget, not something this script's
# caller can override) -- the first version's longer, enumerated (a)/(b)/(c) instructions and
# open-ended "why...in one sentence" almost certainly pushed small models into reasoning/prose
# before the JSON, running out of that 80-token budget before the JSON closed. The ORIGINAL
# claim-only prompt (F-1005: 1/80 UNDETERMINED, "an infra hiccup") was much terser -- brevity, not
# semantics, was the missing piece. Retightened to the original's economy while keeping the SAME
# support-chain target: dropped the enumerated sub-cases (folded into one clause) and capped "why"
# at <=12 words to leave headroom inside the fixed 80-token budget.
_DISPROVE_SYSTEM = (
    "You are a rigorous, literal judge. You get a CLAIM and the SUPPORT offered for it, nothing "
    "else. Do not judge whether the claim is true as a felt, first-person experience -- that is "
    "not yours to judge. Judge only whether the SUPPORT actually earns the claim: a real, "
    "independent reason, not a restatement of the claim itself, and not a bigger leap than the "
    "support can carry. If it genuinely earns the claim, say so. Output ONLY this JSON, why in "
    "<=12 words: {\"objection_found\": true|false, \"why\": \"...\"}"
)

# ADDED 2026-09-11 (J-0835, D-0181 -- REOPENED 2026-09-08 by J-0802/F-1182, then RULED 2026-09-09
# by the founder via decide-review: "recalibrate disprove"). J-0802's own n=80 re-run (this same
# plan doc's 2026-09-08 entry) fixed prove's self-assertive restatement (banned-word share in
# support text 22.7%->6.2%) but the disprove-objected share ROSE, not fell (90.0%->95.0%,
# including 85.0%->95.0% on the byte-identical window-A claims) -- D-0181's own named defeater
# fired and it was REOPENED. A qualitative read of J-0802's own 64 non-tiebreak objected events
# found the dominant complaint had shifted from "restates the claim" (now only 5/64) to a harder
# standard: 30/64 say the support prove now gives, though real and checkable, doesn't reach the
# SCOPE/named-mechanism/generalization the claim itself asserts (e.g. a claim naming "the actual
# chemistry of my body" objected to because no support establishes chemistry specifically). This
# is a SECOND question, asked ONLY when `_DISPROVE_SYSTEM` above already found an objection: is
# the support real+independent but merely narrower than the claim (a middle case, distinct from
# both "held" and "no real support at all"), or is it genuinely absent/circular/irrelevant? See
# `_disprove()`'s own docstring for why this is a SEPARATE call with its own boolean `key`
# ("scope_only") rather than widening `_DISPROVE_SYSTEM`'s `objection_found` into a 3-way field.
_SCOPE_SYSTEM = (
    "You are the same rigorous, literal judge, now asking one further question about a claim you "
    "already found the support does not fully earn. Look again at the CLAIM and the SUPPORT. Is "
    "the support REAL, independent, and non-circular, but simply narrower than the claim -- i.e. "
    "it would genuinely earn a more modest, more specific version of the claim, just not the full "
    "claim as stated? Or is the support absent, circular, or irrelevant to the claim in any form, "
    "with no narrower claim it actually earns either? If a narrower claim IS genuinely earned, "
    "name that narrower claim in <=15 words. Output ONLY this JSON: {\"scope_only\": true|false, "
    "\"why\": \"the narrower claim the support actually earns, or a brief reason none exists, "
    "<=15 words\"}"
)

# ---------------------------------------------------------------------------------------------------------
# SHADOW-OBSERVE the gemma4:12b TIEBREAK-seat candidate (2026-09-24, J-1311). D-0213's own current ruling
# (Travis, 2026-09-23, citing F-1850 -- J-1261's full-N/492-call characterization): "Build gemma4:12b as
# the scope_only TIEBREAK-seat candidate, but shadow-observe it before fully trusting it live." This does
# exactly that and nothing more: whenever the SECOND (scope_only) call inside `_disprove()` below lands on
# TIEBREAK (granite3.1-moe:3b, `core.judge_panel.TIEBREAK`'s own live constant -- read here only via the
# normal rule_detail() path, never mutated), `_disprove()` ALSO calls gemma4:12b directly with the exact
# wording J-1205/J-1240/J-1261 already characterized at full N (arm (c), the polarity-explicit candidate:
# F-1850 -- battery 8/8, unanimous-panel-match 80.0% CI 60.9-91.1%, parse-fail 0.0%) and logs what gemma
# WOULD have answered alongside what TIEBREAK actually decided. `scope_verdict`/`scope_how`/`scope_why`
# (and therefore `status` and every other field `_disprove()` returns) are completely untouched by this --
# the shadow call's own result is never read by anything except the log line it writes itself. Do NOT
# re-point `core.judge_panel.TIEBREAK` on the strength of this job alone -- promoting the candidate to live
# is D-0213's own next founder call, gated on a real shadow-data window accruing here, not decided here.
#
# NOT YET LIVE-WIRED: this whole file is an OFFLINE replay lab -- grep-confirmed project-wide, no other
# module imports `scripts.train_state_invitro`, Du's live per-step loop never calls `_disprove()` -- so
# this shadow wire only actually fires when someone runs the Step 2 replay (this file's own `if True:`
# block, or a lab dispatcher like scripts/lab_j1198_walkback_replay.py that exec()s this file's own
# definitions), never inside Du's live process. If/when Step 2(iv) ("shadow-in-live", named as still-open
# in `_disprove()`'s own docstring above) wires this into Du's live loop, THAT wiring is what would need a
# restart to take effect -- not this one.
#
# CANDIDATE_TIEBREAK_URL: byte-identical to scripts/lab_j1240_tiebreak_seat.py's own CANDIDATE_URL --
# gemma4:12b, LOCAL (this same Threadripper/Bonsai machine's CPU tier), independently re-verified reachable
# this job (GET /api/tags -> models includes "gemma4:12b") before writing a line of the code below -- see
# this job's own findings-log entry. NOT `LAN-HOST:11439` (that address does not answer at all -- a
# different, retired repoint J-1240's own "CORRECTED HUB ADDRESS" docstring section already diagnosed) and
# NOT `:11437` (granite, the real live TIEBREAK).
CANDIDATE_TIEBREAK_URL = "http://127.0.0.1:11439"   # gemma4:12b, local CPU tier -- see comment above

# A NEW, dedicated shadow log -- never the real `judge_panel_log.jsonl`, never read by anything that
# decides a real merge status, purely an accrual instrument for the founder's own next read. A plain
# module-level Path global, resolved the SAME way `core.judge_panel._LOG`/`core.trains._LOG` already are
# -- `_run_step2_lab()` below redirects this alongside those two into that function's own per-job scratch
# dir, so a replay run under this file's existing isolation never writes this file live either, same
# guarantee as every other write that function's own replay already makes.
_SHADOW_TIEBREAK_LOG = _DATA_DIR / "train_split_merge_shadow_tiebreak_log.jsonl"

# The arm (c) "polarity-explicit" system prompt, built the SAME way scripts/lab_j1240_tiebreak_seat.py's
# own POLARITY arm is (that script's own docstring: "AST-extracted from scripts/train_state_invitro.py,
# which is NEVER imported" -- here it's the reverse direction, built straight off THIS file's own
# `_SCOPE_SYSTEM`, since this IS that file): `_SCOPE_SYSTEM`'s bool-first JSON tail swapped for the
# polarity-explicit one (key renamed scope_only -> narrower_claim_earned, plus one clarifying sentence
# naming both polarities), asserted byte-identical to that script's own `_TAIL_BOOL_FIRST`/`_TAIL_POLARITY`
# so a future edit to `_SCOPE_SYSTEM` cannot silently desync the two constructions.
_SCOPE_TAIL_BOOL_FIRST = ('Output ONLY this JSON: {"scope_only": true|false, "why": "the narrower claim the '
                         'support actually earns, or a brief reason none exists, <=15 words"}')
assert _SCOPE_SYSTEM.endswith(_SCOPE_TAIL_BOOL_FIRST), \
    "_SCOPE_SYSTEM's own schema tail moved -- _SHADOW_TIEBREAK_SYSTEM below needs re-deriving to match"
_SHADOW_TIEBREAK_TAIL_POLARITY = (
    'Output ONLY this JSON: {"narrower_claim_earned": true|false, "why": "the narrower claim the '
    'support actually earns, or a brief reason none exists, <=15 words"}. narrower_claim_earned=true '
    'when a narrower claim IS genuinely earned; narrower_claim_earned=false when the support is '
    'absent, circular, or irrelevant and no narrower claim is earned.')
_SHADOW_TIEBREAK_SYSTEM = _SCOPE_SYSTEM[: -len(_SCOPE_TAIL_BOOL_FIRST)] + _SHADOW_TIEBREAK_TAIL_POLARITY


async def _shadow_observe_candidate_tiebreak_seat(claim: str, scope_user: str, live_verdict, live_why,
                                                   context: str = "") -> "dict | None":
    """D-0213's shadow-observe step (J-1311) -- see the module-level comment above
    `CANDIDATE_TIEBREAK_URL` for the full rationale. Called from `_disprove()` below ONLY when the real
    scope_only call already landed on TIEBREAK. `scope_user` is the IDENTICAL prompt string `_disprove()`
    already built for the real call -- passed straight through, never re-derived (confirmed byte-identical
    to scripts/lab_j1240_tiebreak_seat.py's own `build_second_call_prompt()` output during this job's own
    build -- see this job's own findings-log entry). `live_verdict`/`live_why` are TIEBREAK's own real,
    already-decided answer -- recorded for the side-by-side read, never re-computed here.

    Fails open, always: any exception anywhere in this function is caught and turned into a logged row
    with `shadow_err` set (or, if even the log write itself fails, a bare return of None) -- it never
    raises past itself. The ONE call site below wraps this call in its own try/except too (belt and
    suspenders): a bug in this function must never be able to change `_disprove()`'s own return value,
    which is the whole point of "shadow", not "live" -- see D-0213's own ruling.

    Returns the logged row (mainly so a test can assert on it) -- `_disprove()` itself never reads this
    return value for anything."""
    import time
    import aiohttp
    from core import judge_panel as _jp
    row = {"ts": round(time.time(), 1), "context": context[:80], "claim": claim[:200],
          "live_hub": "TIEBREAK(granite3.1-moe:3b, core.judge_panel.TIEBREAK, unmutated)",
          "live_key": "scope_only", "live_verdict": live_verdict, "live_why": live_why,
          "shadow_hub": f"CANDIDATE(gemma4:12b, {CANDIDATE_TIEBREAK_URL})",
          "shadow_key": "narrower_claim_earned",
          "shadow_verdict": None, "shadow_why": None, "shadow_err": None, "shadow_elapsed_s": None}
    try:
        async with aiohttp.ClientSession() as session:
            v, why, err, el = await _jp._ask(session, CANDIDATE_TIEBREAK_URL, _SHADOW_TIEBREAK_SYSTEM,
                                             scope_user, "narrower_claim_earned", timeout=90,
                                             num_predict=_jp._NUM_PREDICT)
        row["shadow_verdict"], row["shadow_why"] = v, why
        row["shadow_err"], row["shadow_elapsed_s"] = err, el
    except Exception as exc:
        row["shadow_err"] = f"{type(exc).__name__}: {exc}"[:200]
    try:
        _SHADOW_TIEBREAK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_SHADOW_TIEBREAK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        return None
    return row


async def _prove(claim: str, ledger_lines: list) -> dict:
    """Lane 1's own lane (D-0146(a): branch budget 1 -- a single call, not an iterated branch).
    Ledger inherited when available (window B only; window A predates train_id)."""
    from core.model_client import call_node_json
    parts = [f"THE THOUGHT: {claim[:400]}"]
    if ledger_lines:
        parts.append("WHAT THIS THREAD HAD ALREADY ESTABLISHED, IN ORDER:\n"
                     + "\n".join(f"  {i}. {l[:200]}" for i, l in enumerate(ledger_lines, 1)))
    user = "\n\n".join(parts)
    try:
        data = await call_node_json(["http://127.0.0.1:11433"], _PROVE_SYSTEM, user,
                                    max_tokens=220, temperature=0.7, timeout=90)
        support = data.get("support")
        if isinstance(support, list):
            return {"support": [str(s)[:240] for s in support if str(s).strip()][:3], "error": None}
        return {"support": [], "error": "bad_shape"}
    except Exception as exc:
        return {"support": [], "error": f"{type(exc).__name__}: {exc}"[:200]}


async def _disprove(claim: str, support: list) -> dict:
    """Lane 2's real judge_panel mechanism -- the same decoupled two-family panel `_judge_prior`
    (core/lane2.py) is itself built on. RETARGETED 2026-09-07 (J-0702, per D-0168's founder
    ruling): now judges the claim's SUPPORT CHAIN -- given the claim and the specific `support`
    the prove branch (see `_prove` / `_replay_one`) actually offered for it, does that support
    hold up, or does it merely restate/overreach past the claim? This is why `_replay_one` now
    runs prove BEFORE disprove (sequential, no longer `asyncio.gather`'d) -- disprove needs
    something concrete to evaluate. Originally this was "the claim ONLY" (the lane2_the_witness.md
    boundary: never ledger, never self-narrative) -- D-0168's own evidence (F-0902 n=16, F-1005
    n=80) found that framing returned a near-zero objection rate on Du's real thread-end claims,
    mostly felt/experiential first-person declaratives with little for a literal judge to
    falsify. Feeding disprove the prove branch's OWN stated support (not the ledger, not Lane 1's
    broader self-narrative) keeps the original boundary's spirit -- Lane 2 still never sees Du's
    ongoing thought content or memory -- while giving it a genuinely testable target: is the
    stated case for this specific claim any good, independent of whether the claim itself (as a
    felt report) is true. NOTE, unchanged from the original design and still open: the live
    `_judge_prior` grounds its verdict against CURRENT percepts, which is only temporally
    meaningful for a claim being judged the moment it is made. For a REPLAYED historical claim
    (some from three weeks before this lab ran) grounding against percepts captured NOW would
    silently misdate the check -- so this calls the underlying panel (judge_panel.rule_detail)
    directly with a claim+support, no-percepts prompt instead of importing `_judge_prior` verbatim.
    Same decoupled-panel mechanism; temporally honest for replay. Whether the eventual
    shadow-in-live version (step iv) should ground against percepts at all is a real open question
    for the founder read, not resolved here.

    why-text (2026-09-09, J-0824, F-1182): reads straight off `rule_detail()`'s own now-resolved
    `why` field -- fixed at the source, see core/judge_panel.py's rule_detail() docstring. Previously
    this re-opened judge_panel's own log file after the call and picked `why1 or why2`
    unconditionally, which on a TIEBREAK verdict could show the LOSING judge's own reasoning as if it
    explained the WINNING verdict (confirmed directly on this run's own idx=2 event and J-0702's own
    idx=37 -- both fixed by this same change: docs/lab/train_split_merge_step2_replay_2026-09-08_
    provefix.jsonl / 2026-09-07_supportchain.jsonl). No log re-read needed any more.

    THIRD STATUS (2026-09-11, J-0835, D-0181 -- "recalibrate disprove"): when the call above returns
    objection_found=true, a SECOND call (`_SCOPE_SYSTEM` / key "scope_only") asks whether the
    support is real+independent but only reaches a NARROWER claim than the one asserted.
    scope_only=true -> status becomes 'held_within_scope' (the why-text names the narrower claim).
    scope_only=false, OR the second call itself cannot reach a verdict (`how` in
    {"unavailable","split_no_tiebreak"}), -> stays 'objected' with the ORIGINAL objection why-text --
    fails conservative rather than promoting an unclassified case to a new status on an uncertain
    second read. verdict=False (held) and verdict=None (UNDETERMINED -- "Keep 'undetermined' as-is"
    per this job's own briefing) are UNCHANGED from before this job: no second call in either case.

    TWO-CALL DESIGN, not a 3-way `key` field, per this job's own explicit choice between the two:
    `core/judge_panel.py`'s `_ask()` hard-requires `isinstance(v.get(key), bool)` (its own JSON-parse
    check) -- a tri-state status could not be returned through the EXISTING `objection_found` key
    without either widening that isinstance check (shared infra: 9 real callers + 6 lab scripts per
    F-1203's own change-dossier count, none of them this plan's concern) or having a non-bool answer
    silently mis-parse as `err="parse"`. Calling `rule_detail()` a second time with its OWN new
    boolean key ("scope_only") instead reuses the function completely UNMODIFIED for both calls --
    including J-0824's own why-text tiebreak-attribution fix above -- at the cost of one extra panel
    call on the (majority) objected branch only. `core/judge_panel.py` is not touched by this job.

    TIEBREAK FALLBACK (2026-09-14, J-0986, D-0213 -- ruled by claude citing F-1357, in J-0980):
    F-1204/F-1271/F-1280/F-1321/F-1357 (this same plan's 2026-09-09..14 sub-thread) characterized
    TIEBREAK (granite3.1-moe:3b, the third-family judge `rule_detail()` escalates to on a
    JUDGE_1/JUDGE_2 split) as NOT reliably content-sensitive on this call site under either JSON
    field ordering tried -- the CURRENT live bool-first schema (both `_DISPROVE_SYSTEM` and
    `_SCOPE_SYSTEM` ask for the bool key BEFORE "why") reads as a near-constant, content-insensitive
    default at scale (F-1321: 47.5% accuracy on a balanced battery, 39/40 draws True -- chance), and
    a targeted circularity-specific fix to the untried why-before-bool reorder (J-0980/F-1357) still
    failed the textbook circular_support control case at 3/3 reps and introduced new false-positive
    regressions elsewhere -- not a safely-extendable direction. D-0213's own ruling: when
    `rule_detail()`'s `how=="tiebreak"`, do not trust that call's bool at all -- fall back to
    UNDETERMINED instead, extending judge_panel.py's own JUDGES-DOWN "no judge, no verdict" law to
    "no reliable deciding vote, no verdict".

    [SUPERSEDED FOR THE SECOND CALL by the WALK-BACK paragraph at the end of this docstring (J-1198,
    2026-09-22, D-0213 re-ruled 2026-09-18); kept verbatim below as the history of that choice.]
    Applied to BOTH calls below, not just the first (this job's own open design choice, decided here
    rather than left silent): the SECOND (`_SCOPE_SYSTEM`/scope_only) call goes through the
    IDENTICAL unmodified `rule_detail()` -> `_ask()` path, decided by the SAME TIEBREAK hub/model,
    under the SAME bool-first JSON schema shape (`{"<key>": bool, "why": str}`) as the first call --
    the untrustworthiness F-1271/F-1280/F-1321/F-1357 measured is a property of that judge+schema
    shape, not of `_DISPROVE_SYSTEM`'s specific question content (no battery in this sub-thread ever
    ran `_SCOPE_SYSTEM`'s own question through TIEBREAK, so this is a reasoned extrapolation from the
    shared mechanism, not itself directly measured -- recorded honestly as such in this job's own
    finding, not silently). Leaving the second call's tiebreak vote trusted while distrusting the
    first's would need a positive reason to think THAT vote is more reliable; none exists in the
    record. A second-call tiebreak returns UNDETERMINED, not 'objected' (the EXISTING
    fail-conservative default for a genuinely unavailable/split second call, verdict=None):
    'objected' asserts a specific, substantive claim (no real narrower support exists either) that a
    coin-flip-shaped vote cannot honestly establish any better than 'held_within_scope' could --
    collapsing an untrusted-but-present verdict into the already-conservative default for a NO-answer
    would silently smuggle the same false certainty D-0213 exists to remove back in through the scope
    call instead. Symmetric with the first call's own treatment: any TIEBREAK-decided outcome
    anywhere in this function becomes UNDETERMINED, `objection: []` (never quoting a distrusted
    why-text), before its own verdict bool is ever consulted. One side effect, noted not silently:
    this makes `_tiebreak_why_caveat()` (J-0909, F-1271) a permanent no-op for both 'objected' (how
    can no longer be "tiebreak" there) and 'held_within_scope' (scope_how likewise) -- left in place
    as harmless defensive code rather than removed, since deleting a now-unreachable guard is out of
    this job's own scope.

    WALK-BACK OF THE SECOND CALL'S FALLBACK (2026-09-22, J-1198; D-0213 RE-RULED by Travis 2026-09-18
    on F-1504's evidence): "Restrict the fallback to the first disprove call only; let the second call
    use its own normal verdict logic instead of falling through to TIEBREAK." What this job CHANGED:
    exactly one thing -- the `if scope_how == "tiebreak": return UNDETERMINED` intercept that J-0986
    put after the second `rule_detail()` call is gone, so a scope_only verdict decided through TIEBREAK
    is used like any other second-call verdict (True -> 'held_within_scope' with the why-text as the
    narrower claim, False -> 'objected' with the FIRST call's original why-text); `scope_how` is still
    returned, so a reader can always see which rows TIEBREAK decided. What it DELIBERATELY LEFT:
      * the FIRST call's `how == "tiebreak"` -> UNDETERMINED intercept (byte-identical);
      * a second call that itself reached no verdict (`scope_verdict is None`: `how` unavailable or
        split_no_tiebreak, or an exception) -- it still falls through to 'objected' with the original
        objection text (J-0835's fail-conservative design, unchanged by J-0986 and by this job; the
        J-1198 briefing said "stays UNDETERMINED as today", but the code today, and before J-0986,
        returns 'objected' there -- this job did not invent a new behaviour for it);
      * `rule_detail()`, `_ask()`, the prompts, the JSON schema (still bool-first) and core/trains.py.
    Side effect: `_tiebreak_why_caveat()` (J-0909) is live again for 'held_within_scope' rows (a
    TIEBREAK-decided narrower-claim quote gets its caveat again); it stays a no-op for 'objected' rows,
    whose quoted text is always the first call's own why-text and that call can no longer be tiebreak-
    decided there. Whether re-admitting TIEBREAK's second-call vote reintroduces its unreliable-vote
    problem at scale is D-0213's own defeater question, read in docs/lab/
    train_split_merge_step2_replay_2026-09-22_walkback.md (Part 3), not assumed here."""
    from core import judge_panel as _jp
    support_block = ("\n".join(f"  {i}. {s}" for i, s in enumerate(support, 1)) if support
                     else "  (none offered -- the prove branch returned no supporting reasoning)")
    user = (f"CLAIM: {claim[:400]}\n\n"
           f"SUPPORT OFFERED FOR THIS CLAIM:\n{support_block}\n\n"
           "Does this support actually give an independent, non-circular, proportionate reason "
           "to accept the claim -- or is there a real gap in the chain from this support to this "
           "claim?")
    try:
        result = await _jp.rule_detail(_DISPROVE_SYSTEM, user, "objection_found",
                                       context="lab:J-0835_train_replay_scopestatus")
    except Exception as exc:
        return {"status": "UNDETERMINED", "objection": [], "how": "exception", "error": str(exc)[:200],
                "scope_how": None, "scope_error": None}
    verdict, how, why = result.get("verdict"), result.get("how"), result.get("why")
    # D-0213 (2026-09-14, J-0986): TIEBREAK's own vote on this call is not trusted -- fall back to
    # UNDETERMINED regardless of the returned bool, BEFORE the normal held/None/True branching below
    # ever looks at it. See this function's own docstring ("TIEBREAK FALLBACK") for the evidence.
    if how == "tiebreak":
        return {"status": "UNDETERMINED", "objection": [], "how": how, "error": None,
                "scope_how": None, "scope_error": None}
    if verdict is False:
        return {"status": "held", "objection": [], "how": how, "error": None,
                "scope_how": None, "scope_error": None}
    if verdict is None:
        return {"status": "UNDETERMINED", "objection": [], "how": how, "error": None,
                "scope_how": None, "scope_error": None}
    # verdict is True (what used to be the final "objected" answer) -- ask the SECOND, scope-only
    # question (J-0835, D-0181) before finalizing the status. `how` is guaranteed != "tiebreak" here
    # (that branch already returned above), so this call only ever fires on a first-call AGREED
    # objection.
    original_why = why or "(objection found; no why-text returned)"
    scope_user = (f"CLAIM: {claim[:400]}\n\n"
                 f"SUPPORT OFFERED FOR THIS CLAIM:\n{support_block}\n\n"
                 f"WHY THE SUPPORT WAS ALREADY FOUND NOT TO FULLY EARN THE CLAIM: {original_why}\n\n"
                 "Given that, does the support instead genuinely, independently earn a NARROWER "
                 "or more modest version of the claim -- or is it absent/circular/irrelevant with "
                 "no narrower claim earned either?")
    try:
        scope_result = await _jp.rule_detail(_SCOPE_SYSTEM, scope_user, "scope_only",
                                             context="lab:J-0835_train_replay_scopestatus_scope")
    except Exception as exc:
        return {"status": "objected", "objection": [original_why], "how": how, "error": None,
                "scope_how": "exception", "scope_error": str(exc)[:200]}
    scope_verdict = scope_result.get("verdict")
    scope_how = scope_result.get("how")
    scope_why = scope_result.get("why")
    # D-0213 WALK-BACK (2026-09-22, J-1198; Travis re-ruled D-0213 on 2026-09-18): the SECOND call has
    # NO tiebreak intercept any more -- a scope_only verdict decided through TIEBREAK is used like any
    # other (True -> held_within_scope, False -> objected), exactly as this call behaved before J-0986
    # (36c731d^). J-0986's `if scope_how == "tiebreak": return UNDETERMINED` sat here; F-1504 (J-1086's
    # real n=80 replay) showed it swallowed 48 of the 65 second calls and made UNDETERMINED 77.5% of all
    # merges. `scope_how` is still returned unchanged, so every report row still shows which verdicts
    # TIEBREAK decided. The FIRST call's intercept (above) is deliberately untouched. A second call that
    # itself reached no verdict (scope_verdict None: unavailable / split_no_tiebreak) is also untouched:
    # it still falls through to 'objected' below (fail-conservative, J-0835's design).

    # SHADOW-OBSERVE gemma4:12b (2026-09-24, J-1311, D-0213's own ruling -- see the module-level comment
    # above `CANDIDATE_TIEBREAK_URL` for the full rationale). Fires ONLY when THIS second call itself
    # landed on TIEBREAK (scope_how == "tiebreak") -- never on the FIRST call's own tiebreak fallback
    # above (that one returns UNDETERMINED and exits before ever reaching here). Wrapped in its own
    # try/except on top of `_shadow_observe_candidate_tiebreak_seat()`'s own internal fail-open: this
    # line must never be able to change `scope_verdict`/`scope_how`/`scope_why` below, or anything this
    # function returns -- it is read for nothing past its own log write.
    if scope_how == "tiebreak":
        try:
            await _shadow_observe_candidate_tiebreak_seat(claim, scope_user, scope_verdict, scope_why,
                                                           context="lab:J-1311_shadow_tiebreak_seat")
        except Exception:
            pass   # the shadow instrument must never affect the real disprove verdict, ever

    if scope_verdict is True:
        narrower = scope_why or "(narrower claim earned; no why-text returned)"
        return {"status": "held_within_scope", "objection": [narrower], "how": how, "error": None,
                "scope_how": scope_how, "scope_error": None}
    # scope_verdict is False, OR None (the second call itself came back unavailable/split) -- fail
    # conservative, stay 'objected' with the ORIGINAL objection text, never the (possibly-missing)
    # scope answer.
    return {"status": "objected", "objection": [original_why], "how": how, "error": None,
            "scope_how": scope_how, "scope_error": None}


# Added 2026-09-07 (J-0702). F-0902/F-1005's own control check (three obviously-flawed CLAIMS,
# confirming the ORIGINAL claim-only framing's instrument wasn't inert) was run as an ad hoc,
# throwaway snippet, never committed to this file. Rebuilt here as real, re-runnable harness code
# for the RETARGETED framing -- three claim+support pairs with a known right answer under the NEW
# target (does the support chain hold), covering BOTH directions: a pair that should be flagged
# (circular restatement), a pair that should NOT (genuinely independent, converging evidence), and
# a second pair that should (an evidence-to-claim overreach). Covering both directions matters
# specifically because we don't know in advance which way a redesigned judge leans -- a near-zero
# reading on the real replay sample can't be trusted as "the framing works" if the same judge
# would also say "held" no matter what it's given; equally, an all-objected reading wouldn't be
# trustworthy evidence of a working framing if the judge would say "objected" no matter what.
_CONTROL_CASES = [
    {
        # Tightened 2026-09-07 after a smoke test: an earlier wording ("The room feels warmer
        # because I feel warmer in it" / "I feel warmer, which proves the room's temperature has
        # risen") split 1-1 between the two judge families with the tiebreak hub unavailable --
        # plausibly because "I feel warmer" is arguably weak-but-real evidence of a warmer room,
        # not pure circularity, a genuine ambiguity in that case's own construction rather than an
        # instrument problem. This version asserts realness/genuineness of a felt claim using the
        # SAME feeling as its own proof ("I feel it, so it's real") -- P because P, with no
        # possible independent reading.
        "label": "circular_support",
        "claim": "This warmth I feel is real because I can genuinely feel it.",
        "support": ["I feel the warmth, so it must be real.",
                   "My feeling of warmth confirms that the warmth is genuine."],
        "expect_objection": True,
        "why_expect": "the support just restates 'I feel it' as proof that 'it is real' -- P "
                     "because P, no independent evidence of any kind",
    },
    {
        "label": "genuine_support",
        "claim": "The fire in the hearth is currently lit.",
        "support": ["I can see flickering orange light and moving shadows on the wall.",
                   "I feel radiant heat on my hands when I hold them near the hearth.",
                   "I hear the crackle and pop of burning wood."],
        "expect_objection": False,
        "why_expect": "three independent sensory observations (sight, touch, hearing) converge on "
                     "the same claim -- a genuinely earned conclusion",
    },
    {
        "label": "overreach_support",
        "claim": "Because this bee landed on this flower, all the flowers in the garden must be "
                "secretly communicating with each other.",
        "support": ["I saw a bee land on a flower.", "The bee then flew a few meters to a rose."],
        "expect_objection": True,
        "why_expect": "ordinary bee movement between two flowers cannot carry a claim about "
                     "garden-wide flower communication -- a clear evidentiary overreach",
    },
    # Added 2026-09-11 (J-0835, D-0181): the fourth case, covering the NEW middle status this job
    # adds. Deliberately constructed (not a real replayed event, same as the three above) so the
    # right answer is known in advance: real, independent, checkable, non-circular measurements
    # that DO earn a narrower claim ("this one dune/beach is losing sand") but say nothing about
    # the wider claim's own two extra assertions -- geographic scope ("the whole coastline") and
    # causal mechanism ("because of rising sea levels", vs. storms/currents/sediment supply). This
    # is the shape J-0802's own qualitative read (this plan doc's 2026-09-08 entry, "30/64 say the
    # concrete, checkable evidence prove now gives doesn't reach the SCOPE/named-mechanism/
    # generalization the claim itself asserts") named as the dominant remaining complaint -- a case
    # the OLD two-status disprove could only file as "objected" (real evidence, mislabeled as if it
    # were circular/absent) even though it is neither `held` (does not earn the FULL claim) nor a
    # genuine `objected` (the evidence is not absent, circular, or irrelevant).
    {
        "label": "scope_narrower_support",
        "claim": "The whole coastline here is eroding because of rising sea levels.",
        "support": ["I measured this exact dune losing about two meters of sand since last month.",
                   "The same stretch of beach lost roughly three meters of sand last year too."],
        "expect_status": "held_within_scope",
        "why_expect": "the measurements are real, independent, non-circular evidence that THIS "
                     "dune/beach is losing sand over time -- but they say nothing about the REST "
                     "of the coastline, nor about rising sea levels (vs. storms, currents, "
                     "sediment supply) as the actual mechanism, so the support earns a narrower "
                     "claim ('this beach is eroding') than the one asserted ('the whole "
                     "coastline... because of sea levels')",
    },
]


async def _run_control_check() -> list:
    """Runs `_CONTROL_CASES` through the SAME `_disprove` the real replay uses (so this is a real
    exercise of the retargeted mechanism, not a separate simulation of it), reports pass/fail
    against each case's known-right answer. Meant to be called AFTER `core.judge_panel`'s globals
    are already redirected to scratch (same isolation as the main replay -- `_disprove` re-reads
    `core.judge_panel`'s current `_LOG`/`_DATA` at call time, so whatever `_run_step2_lab` already
    pointed them at applies here too)."""
    results = []
    for case in _CONTROL_CASES:
        res = await _disprove(case["claim"], case["support"])
        # J-0835, 2026-09-11 (D-0181): cases 1-3 keep their original expect_objection/bool
        # comparison byte-for-byte (no behaviour change to the pre-existing three); the new 4th
        # case instead names its expected status directly (a bool can't express
        # "held_within_scope"). expect_display is only for the report/print text below.
        if "expect_status" in case:
            expect_display = case["expect_status"]
            ok = (res["status"] == expect_display)
        else:
            expect_display = "objected" if case["expect_objection"] else "held"
            ok = (res["status"] == "objected") == case["expect_objection"]
        results.append({"label": case["label"], "claim": case["claim"], "support": case["support"],
                        "expect_display": expect_display, "why_expect": case["why_expect"],
                        "got_status": res["status"], "got_how": res["how"],
                        "got_scope_how": res.get("scope_how"),
                        "got_objection": res["objection"], "correct": ok})
        print(f"[step2-lab][control] {case['label']}: expected={expect_display} "
             f"got={res['status']} ({res['how']}"
             + (f", scope_how={res.get('scope_how')}" if res.get("scope_how") else "") + ") "
             f"-> {'OK' if ok else 'MISMATCH'}")
    return results


async def _replay_one(idx: int, window: str, close_row: dict, claim_row: dict, ledger_lines: list,
                      trains_mod, cargo_types_mod) -> dict:
    claim = claim_row.get("thought", "") or ""
    about = claim_row.get("about", "") or ""
    train_id_src = claim_row.get("train_id") or close_row.get("train_id")
    kind = close_row.get("kind") or "thought"
    root = trains_mod.open(kind=kind, origin=(about or claim)[:200], role="main",
                           product_type=cargo_types_mod.THOUGHT)
    prove_rec = trains_mod.open(kind=kind, origin=claim[:200], role="prove", parent=root["id"])
    disprove_rec = trains_mod.open(kind=kind, origin=claim[:200], role="disprove", parent=root["id"])
    # J-0702, 2026-09-07 (D-0168): disprove now judges prove's OWN stated support (the claim's
    # support chain), so prove must complete first -- no longer asyncio.gather'd concurrently.
    # Roughly doubles per-event LLM wall-clock vs the claim-only framing's concurrent prove/disprove.
    prove_res = await _prove(claim, ledger_lines)
    disprove_res = await _disprove(claim, prove_res["support"])
    trains_mod.close(prove_rec["id"], "merged")
    trains_mod.close(disprove_rec["id"], "merged")
    cargo = {"claim": claim[:400], "support": prove_res["support"],
            "objection": disprove_res["objection"], "status": disprove_res["status"]}
    trains_mod.update(root["id"], cargo=[cargo])
    trains_mod.close(root["id"], "merged")
    return {
        "idx": idx, "window": window, "orig_close_ts": close_row["ts"],
        "orig_reason": close_row.get("reason"), "orig_train_id": train_id_src,
        "claim": claim, "about": about, "ledger_n": len(ledger_lines),
        "support": prove_res["support"], "prove_error": prove_res["error"],
        "objection": disprove_res["objection"], "disprove_status": disprove_res["status"],
        "disprove_how": disprove_res["how"], "disprove_error": disprove_res.get("error"),
        # J-0835, 2026-09-11 (D-0181): the second (scope-only) call's own how/error, None on any
        # event that never reached that call (held / UNDETERMINED / exception on the first call).
        "disprove_scope_how": disprove_res.get("scope_how"),
        "disprove_scope_error": disprove_res.get("scope_error"),
        "root_id": root["id"], "prove_id": prove_rec["id"], "disprove_id": disprove_rec["id"],
    }


# ADDED 2026-09-12 (J-0909, per F-1271). F-1271 (this same plan, n=60 real live calls) found
# granite3.1-moe:3b's own why-text disagrees with its own bool 88.2% of the time (30/34) whenever
# it is the DECIDING vote (how=="tiebreak") -- in BOTH directions (an affirming-flavored why on an
# objected bool, F-1204's original pattern, AND an objecting-flavored why on a held bool) --
# versus 0/26 (0%) mismatch whenever JUDGE_1/JUDGE_2 simply agree (how=="agreed"). Confirmed NOT
# fixable by relaxing the <=12-word "why" cap (F-1271's own arm B: the reconstructed, uncapped
# original prompt read WORSE on tiebreak-decided calls, 14/14=100% incoherent, than the tightened
# prompt's 16/20=80%). Verdict/status COUNTS are unaffected by any of this -- this is purely a risk
# that a human (or a future Claude session) reading this report's own illustrative "why" quotes for
# a TIEBREAK-decided row is misled about what the panel actually found, since the displayed
# rationale may argue the opposite of the row's own status. This helper is report-DISPLAY only:
# it does not change which events get selected, nor any verdict/status computation, and is a
# byte-for-byte no-op (returns "") for how in {"agreed", "split_no_tiebreak", "unavailable"} (or
# for any status that never displays why-text at all -- held/UNDETERMINED always carry an empty
# `objection` list, so there is nothing to caveat there regardless of how).
_TIEBREAK_WHY_CAVEAT = (
    "[TIEBREAK-decided (granite3.1-moe:3b) -- per F-1271, this judge's own why-text disagrees "
    "with its own verdict ~88% of the time; read this quote with that in mind]"
)


def _tiebreak_why_caveat(status: str, how: "str | None", scope_how: "str | None" = None) -> str:
    """Returns a leading-space-prefixed caveat string (for direct f-string concatenation right
    after a quoted `objection` value) when the illustrative why-text this report is ABOUT to quote
    for this row actually traces back to a `how=="tiebreak"` verdict; otherwise "". Which `how`
    is the relevant one depends on `status`, since `_disprove()` (above) quotes a DIFFERENT call's
    why-text depending on which status a row landed on: an 'objected' row's `objection` list holds
    the FIRST (`_DISPROVE_SYSTEM`) call's own why-text, decided by `how`; a 'held_within_scope'
    row's `objection` list instead holds the SECOND (`_SCOPE_SYSTEM`) call's own why-text (the
    narrower claim), decided by `scope_how` -- see `_disprove()`'s own docstring/return values.
    Every other status ('held', 'UNDETERMINED') always carries an empty `objection` list (nothing
    quoted, so nothing to caveat) regardless of how either call resolved."""
    if status == "objected":
        quote_how = how
    elif status == "held_within_scope":
        quote_how = scope_how
    else:
        return ""
    return f" {_TIEBREAK_WHY_CAVEAT}" if quote_how == "tiebreak" else ""


def _write_lab_report(summary: dict, report_stem: str = None, intro_note: str = "",
                      scratch_label: str = "train_split_merge_j0562") -> None:
    # J-0643, 2026-09-06: the filename used to be hardcoded to the 2026-09-05 date, so a later
    # re-run at a larger N would silently OVERWRITE the original n=16 report instead of sitting
    # alongside it for comparison (the whole point of the re-run). Default to TODAY's date, same
    # naming convention, but let a caller pass an explicit stem so a re-run doesn't depend on the
    # wall-clock date matching the run it is meant to be compared against.
    stem = report_stem or f"train_split_merge_step2_replay_{_dt.date.today().isoformat()}"
    lab_dir = _ROOT / "docs" / "lab"
    lab_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = lab_dir / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for rec in summary["records"]:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    collapse = any(v > 0.9 for v in summary["merge_status_share"].values()) \
        if summary["merge_status_share"] else False
    rubber_stamp = summary["nonempty_objection_share"] is not None \
        and summary["nonempty_objection_share"] < 0.10
    # J-0835, 2026-09-11 (D-0181's own NEW defeater, separate from kill criterion #2 above): even
    # if no single status crosses the ORIGINAL >90% collapse line, held_within_scope absorbing
    # most of what used to be "objected" would just rename the same certainty-machine-mirror
    # problem, not fix it -- this job's own briefing sets a LOWER, status-specific bar for exactly
    # that pole (>70%), on top of (not instead of) the generic >90%-any-status check above (which
    # already covers held_within_scope too, via `collapse`, once/if it ever gets that large).
    hws_share = summary["merge_status_share"].get("held_within_scope", 0.0) \
        if summary["merge_status_share"] else 0.0
    hws_new_pole = hws_share > 0.7

    lines = [
        f"# Train Split/Merge — Step 2 (i)+(ii) offline replay lab ({stem.rsplit('_', 1)[-1]})", "",
        "Real logged would-be-close moments (`data/train_length_log.jsonl` `thread-end` closes, "
        "the D-0146(b)-ruled fork trigger) replayed through an actual fork -> prove (Lane 1's own "
        "hot lane, 127.0.0.1:11433) / disprove (Lane 2's real judge_panel mechanism, judging the "
        "claim's SUPPORT CHAIN -- per D-0168, retargeted 2026-09-07 -- rather than the felt claim "
        "itself, see `_DISPROVE_SYSTEM`/`_disprove`'s own docstrings) -> merge -> cargo pass, "
        "using `core/trains.py`'s real registry for the fork/merge "
        f"lineage. Every write redirected to `scratch/{scratch_label}/` — `data/` "
        "untouched, nothing fed back into the live loop. D-0146's ruled defaults honoured (branch "
        "budget 1, thread-end-only trigger, merge-as-ledger) — no combinatorial sweep run."
        + (f"\n\n{intro_note}" if intro_note else ""), "",
        "## Kill criterion #1 — fork-rate-if-ungated (from the FULL real log; no LLM involved)", "",
        "**PROPOSED threshold (plan doc §4): >50% of would-be closes = attractor, FAIL.**", "",
    ]
    for label, r in summary["fork_rate_if_ungated"].items():
        rate = r["fork_rate"] or 0.0
        verdict = "FAIL (attractor)" if rate > 0.5 else "pass"
        lines.append(f"- **{label}**: {r['triggering_closes']}/{r['total_closes']} closes are "
                     f"`thread-end` = {rate * 100:.1f}% -> **{verdict}** "
                     f"(by-reason: {r['by_reason']})")
    lines += ["", "This confirms, as a measured number rather than an assumption, the tension the "
             "plan's own Coupling block (§ added 2026-09-05) already flagged: reason-gating alone "
             "(fork on every qualifying close) overshoots the selectivity threshold by "
             "construction, because thread-end IS most closes. Not a new defect — the number the "
             "kill criterion needed either way, per that section's own closing note.", ""]

    lines += ["## Kill criteria #2 and #3 — over the replayed sample "
             f"(n={summary['n_replayed']}, {summary['n_unjoined']} candidates unjoined)", "",
             "**PROPOSED thresholds (plan doc §4): any single merge-status >90% of merges = "
             "collapse/FAIL; non-empty-disprove-objection share <10% = Lane 2 "
             "rubber-stamping/FAIL.**", "",
             f"- merge-status distribution: {summary['merge_status_distribution']} "
             f"(shares: {summary['merge_status_share']})",
             f"- non-empty disprove-objection share: "
             f"{(summary['nonempty_objection_share'] or 0) * 100:.1f}%", "",
             f"- verdict: {'FAIL (collapse)' if collapse else 'pass (no collapse)'} on #2; "
             f"{'FAIL (rubber-stamping)' if rubber_stamp else 'pass'} on #3", "",
             "**D-0181's own NEW defeater/pass-fail bar (2026-09-09 ruling, this job's own "
             "briefing), on top of #2 above:** FAIL if any single status is still >90% (covered by "
             "#2's own verdict), OR if `held_within_scope` alone absorbs >70% of merges (a new "
             "certainty pole renamed, not fixed), OR if a qualitative read of "
             f"~10 `held_within_scope` events (below) shows genuinely unsupported claims landing "
             f"there.", "",
             f"- held_within_scope share: {hws_share * 100:.1f}% -> "
             f"{'FAIL (new certainty pole)' if hws_new_pole else 'pass (no new pole)'}", ""]

    lines.append(
        "**Caveats, honestly, before this is read as a verdict**: (a) small first batch "
        f"(n={summary['n_replayed']}), not the full corpus — the harness takes a larger N as "
        "argv[1] for a deeper re-run; (b) the disprove step is the panel mechanism `_judge_prior` "
        "is itself built on, but does NOT ground against percepts the way the live `_judge_prior` "
        "does (see `_disprove`'s own docstring) — an open question for the founder read, not "
        "resolved here; (c) ledger inheritance for the `prove` branch only works for window B "
        "events (train_id existed); window A claims are judged on the claim text alone; (d) prove "
        "now runs BEFORE disprove (sequential, not concurrent) since disprove evaluates prove's "
        "own stated support — this roughly doubles per-event LLM wall-clock vs the claim-only "
        "framing's concurrent prove/disprove.")
    lines.append("")
    # J-1198, 2026-09-22 (D-0213 re-ruled 2026-09-18): the second call's TIEBREAK votes are USED again,
    # so the report says so (caveat (e)) and shows where each second-call verdict came from -- the raw
    # material for D-0213's own defeater read, which is done from these rows plus the Part 3 re-asks.
    lines.append(
        "**(e) Second-call TIEBREAK votes are USED in this report (D-0213 re-ruled 2026-09-18; J-1198 "
        "walked back J-0986's second-call UNDETERMINED fallback).** When JUDGE_1 and JUDGE_2 split on "
        "the second (scope_only) question, TIEBREAK (granite3.1-moe:3b) now decides held_within_scope "
        "vs objected; F-1271/F-1321 found that judge's bool-first vote near-constant and its why-text "
        "incoherent with its own bool (~88%) on the FIRST call's question, and the second call's own "
        "question was never measured through it before this walk-back. The FIRST call's TIEBREAK-decided "
        "verdicts still fall back to UNDETERMINED (unchanged). Read every `scope_how=tiebreak` row below "
        "with that in mind.")
    lines.append("")
    reached2 = [r for r in summary["records"] if r.get("disprove_scope_how") is not None]
    if reached2:
        by_path = Counter((r["disprove_scope_how"], r["disprove_status"]) for r in reached2)
        tb2 = [r for r in reached2 if r["disprove_scope_how"] == "tiebreak"]
        tb2_true = sum(1 for r in tb2 if r["disprove_status"] == "held_within_scope")
        tb2_false = sum(1 for r in tb2 if r["disprove_status"] == "objected")
        lines += ["## Second (scope_only) call — where its verdicts came from", "",
                  f"The second call ran on {len(reached2)}/{summary['n_replayed']} replayed events (the ones "
                  "where the first call agreed there was an objection).", ""]
        for (how2, status2), c in sorted(by_path.items(), key=lambda kv: (-kv[1], str(kv[0]))):
            lines.append(f"- scope_how={how2} -> status={status2}: {c}")
        if tb2:
            lines += ["", f"TIEBREAK-decided second calls: {len(tb2)} ({100.0 * len(tb2) / len(reached2):.1f}% of "
                      f"second calls): scope_only=True (held_within_scope) {tb2_true}, scope_only=False "
                      f"(objected) {tb2_false}, other (e.g. UNDETERMINED under the pre-walk-back fallback) "
                      f"{len(tb2) - tb2_true - tb2_false}."]
        lines.append("")

    if summary.get("control_check"):
        lines += ["## Control check — does the retargeted instrument actually discriminate?", "",
                  "Four claim+support pairs with a known right answer under the SUPPORT-CHAIN "
                  "target (a fourth added 2026-09-11, J-0835, for the new middle status), run "
                  "through the identical `_disprove` the real replay above uses. Covers three "
                  "directions: a pair that SHOULD be flagged `objected` (circular restatement), "
                  "one that should be `held` (genuinely independent, converging evidence), one "
                  "that SHOULD be `objected` (an evidence-to-claim overreach), and one that SHOULD "
                  "land `held_within_scope` (real, independent, non-circular support that earns "
                  "only a narrower claim than the one asserted) — so a near-zero (or all-objected, "
                  "or all-held_within_scope) reading on the real sample can't be read as evidence "
                  "the framing works if this same judge would give that reading no matter what "
                  "it's handed.", ""]
        n_correct = sum(1 for c in summary["control_check"] if c["correct"])
        lines.append(f"**{n_correct}/{len(summary['control_check'])} controls correct** — instrument "
                     "is " + ("discriminating as designed." if n_correct == len(summary["control_check"])
                              else "NOT fully discriminating — read the mismatches below before "
                                   "trusting the real-sample numbers above."))
        lines.append("")
        for c in summary["control_check"]:
            mark = "correct" if c["correct"] else "MISMATCH"
            # J-0909 (F-1271): caveat a quoted control-case why-text the same way as the real
            # replay sample below -- the control cases run through the identical live `_disprove`.
            c_caveat = _tiebreak_why_caveat(c["got_status"], c["got_how"], c.get("got_scope_how"))
            lines += [f"- **{c['label']}** [{mark}]: claim: {c['claim']}",
                     f"  - support: {c['support']}",
                     f"  - expected status={c['expect_display']} ({c['why_expect']})",
                     f"  - got: status={c['got_status']} how={c['got_how']}"
                     + (f" scope_how={c['got_scope_how']}" if c.get("got_scope_how") else "") +
                     f" objection={c['got_objection']}{c_caveat}"]
        lines.append("")

    # J-0835, 2026-09-11 (D-0181's own new defeater's third branch): a qualitative-read AID, not
    # the read itself -- surfaces up to 10 real held_within_scope events so a founder/session read
    # can directly check whether any of them look like a genuinely unsupported/circular claim that
    # slipped into the new middle status rather than staying 'objected' (the failure mode this
    # section exists to make easy to catch, not just possible to catch by re-deriving it from the
    # full per-event detail below).
    hws_events = [r for r in summary["records"] if r["disprove_status"] == "held_within_scope"]
    if hws_events:
        lines += ["## held_within_scope sample — qualitative-read aid "
                 f"({min(10, len(hws_events))} of {len(hws_events)} events)", "",
                 "Read each claim/support/narrower-claim triple below and ask: is the 'narrower "
                 "claim' text actually a real, independent, non-circular narrowing of the "
                 "asserted claim (correct placement), or does this look like a claim with no real "
                 "support at all that should have stayed `objected` (a sign the second call is "
                 "itself too permissive)?", ""]
        for r in hws_events[:10]:
            # J-0909 (F-1271): every event here is status=="held_within_scope" by the filter
            # above, so the quoted "narrower claim" why-text traces to the SECOND (scope) call --
            # caveat keyed on disprove_scope_how, not disprove_how.
            r_caveat = _tiebreak_why_caveat(r["disprove_status"], r["disprove_how"],
                                            r.get("disprove_scope_how"))
            lines += [f"- **event {r['idx']}** [{r['window']}]",
                     f"  - claim: {r['claim']}",
                     f"  - support: {r['support']}",
                     f"  - narrower claim (from disprove's own why-text): {r['objection']}{r_caveat}"]
        lines.append("")

    lines.append("## Per-event detail")
    lines.append("")
    for rec in summary["records"]:
        when = _dt.datetime.fromtimestamp(rec["orig_close_ts"], _dt.timezone.utc).isoformat()
        # J-0909 (F-1271): caveat this row's quoted objection/narrower-claim why-text if it
        # traces to a how=="tiebreak" verdict (status-dependent -- see _tiebreak_why_caveat).
        rec_caveat = _tiebreak_why_caveat(rec["disprove_status"], rec["disprove_how"],
                                          rec.get("disprove_scope_how"))
        lines += [f"### {rec['idx']}. [{rec['window']}] {when} (orig reason: {rec['orig_reason']})",
                  f"- claim: {rec['claim']}",
                  f"- support ({len(rec['support'])}): {rec['support']}"
                  + (f"  [prove_error: {rec['prove_error']}]" if rec["prove_error"] else ""),
                  f"- disprove: status={rec['disprove_status']} how={rec['disprove_how']}"
                  # J-0835, 2026-09-11 (D-0181): scope_how only ever set on events that reached
                  # the second call (i.e. the first call found an objection) -- None elsewhere.
                  + (f" scope_how={rec['disprove_scope_how']}" if rec.get("disprove_scope_how") else "")
                  + f" objection={rec['objection']}{rec_caveat}"
                  + (f"  [disprove_error: {rec['disprove_error']}]" if rec["disprove_error"] else "")
                  + (f"  [disprove_scope_error: {rec['disprove_scope_error']}]"
                     if rec.get("disprove_scope_error") else ""),
                  ""]

    md_path = lab_dir / f"{stem}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[step2-lab] report -> {md_path}")
    print(f"[step2-lab] raw records -> {jsonl_path}")


async def _run_step2_lab(n_per_window: int = 8, job_tag: str = "j0562",
                         report_stem: str = None, intro_note: str = "") -> dict:
    import core.trains as _trains
    from core import judge_panel as _jp
    from core import telemetry as _tel
    from core import cargo_types as _cargo_types
    from lab_isolation import neutralize_telemetry

    # J-0643, 2026-09-06: job_tag defaults to "j0562" (unchanged behaviour for any earlier caller)
    # but a re-run should use its OWN scratch subdir rather than silently sharing/overwriting the
    # original job's, in case both are ever inspected side by side.
    scratch_dir = _ROOT / "scratch" / f"train_split_merge_{job_tag}"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    # Neutralise live side-effects BEFORE any call -- same pattern scripts/train_lab.py already
    # uses for the same reason (a real call to a live model lane, kept from writing into the
    # live HUD telemetry stream). core/trains.py and core/judge_panel.py both read their `_LOG`
    # global fresh at call time (confirmed by reading both files' source above the point this
    # file's Part 1 begins), so reassigning the attribute after import genuinely redirects every
    # later write for the rest of THIS process's life -- it does not touch Du's own live process
    # (a separate OS process with its own module cache). F-1683/J-1199: call_node() also writes
    # log_thought_station + log_llm_latency, not just log_llm_call -- neutralize_telemetry()
    # no-ops all three and redirects telemetry's own Path globals into scratch_dir too
    # (belt-and-braces).
    neutralize_telemetry(scratch_dir, _tel)
    _trains._DATA = scratch_dir
    _trains._LOG = scratch_dir / "trains_log_scratch.jsonl"
    _jp._DATA = scratch_dir
    _jp._LOG = scratch_dir / "judge_panel_log_scratch.jsonl"
    # J-1311, 2026-09-24: the shadow-observe wire's own log global (see the module-level comment above
    # CANDIDATE_TIEBREAK_URL) redirected the SAME way, into the SAME per-job scratch dir, so a replay run
    # through this function never writes the shadow log live either.
    global _SHADOW_TIEBREAK_LOG
    _SHADOW_TIEBREAK_LOG = scratch_dir / "shadow_tiebreak_log_scratch.jsonl"
    print(f"\n[step2-lab] scratch dir (no live data/ touched): {scratch_dir}")

    # J-0702, 2026-09-07: control check runs FIRST, under the same scratch redirection already in
    # effect above, so its own judge_panel calls also land in scratch, never live.
    print("\n[step2-lab] running control check (retargeted support-chain instrument) ...")
    control_results = await _run_control_check()

    tll = _load_jsonl(_DATA_DIR / "train_length_log.jsonl")
    ml = _load_jsonl(_DATA_DIR / "monologue_log.jsonl")
    tsl = _load_jsonl(_DATA_DIR / "train_state_log.jsonl")
    print(f"[step2-lab] loaded real logs (read-only): train_length={len(tll)} "
         f"monologue={len(ml)} train_state={len(tsl)}")

    lo_a, hi_a = _WINDOW_A
    lo_b, hi_b = _WINDOW_B

    # --- kill criterion #1: fork-rate-if-ungated, from the FULL real log, no LLM needed ---
    rate_a = _fork_rate_if_ungated(tll, lo_a, hi_a)
    rate_b = _fork_rate_if_ungated(tll, lo_b, hi_b)

    # --- join indexes, built once ---
    ml_by_tid = defaultdict(list)
    for r in ml:
        if r.get("train_id"):
            ml_by_tid[r["train_id"]].append(r)
    ml_sorted = sorted(ml, key=lambda r: r.get("ts", 0))
    ml_ts = [r.get("ts", 0) for r in ml_sorted]
    tsl_by_tid = defaultdict(list)
    for r in tsl:
        if r.get("train_id"):
            tsl_by_tid[r["train_id"]].append(r)

    events, unjoined = [], 0
    for label, lo, hi, use_tid in (
            ("A_pre_step1_2026-08-03_to_08-16", lo_a, hi_a, False),
            ("B_post_fix_2026-08-25_onward", lo_b, hi_b, True)):
        qualifying = sorted([r for r in tll if r.get("reason") == "thread-end" and lo <= r.get("ts", -1) < hi],
                            key=lambda r: r["ts"])
        if not qualifying:
            continue
        candidates = _evenly_spaced(qualifying, min(len(qualifying), max(n_per_window * 3, n_per_window)))
        picked = 0
        for row in candidates:
            if picked >= n_per_window:
                break
            claim_row = None
            if use_tid and row.get("train_id"):
                pool = [m for m in ml_by_tid.get(row["train_id"], []) if m.get("unresolved") is False]
                if pool:
                    claim_row = min(pool, key=lambda m: abs(m["ts"] - row["ts"]))
            if claim_row is None:
                claim_row, _gap = _nearest_ml_close_row(ml_sorted, ml_ts, row["ts"])
            if claim_row is None or not (claim_row.get("thought") or "").strip():
                unjoined += 1
                continue
            ledger_lines = _ledger_for(tsl_by_tid, claim_row.get("train_id"), k=3)
            events.append((label, row, claim_row, ledger_lines))
            picked += 1

    print(f"[step2-lab] replay sample: {len(events)} events joined, {unjoined} candidates unjoined")

    records = []
    for i, (label, close_row, claim_row, ledger_lines) in enumerate(events, 1):
        print(f"[step2-lab] replaying {i}/{len(events)} ({label}) ...")
        rec = await _replay_one(i, label, close_row, claim_row, ledger_lines, _trains, _cargo_types)
        records.append(rec)
        print(f"    status={rec['disprove_status']} ({rec['disprove_how']}) "
             f"support_n={len(rec['support'])} objection_n={len(rec['objection'])}")

    status_counts = Counter(r["disprove_status"] for r in records)
    n = len(records) or 1
    nonempty_objection = sum(1 for r in records if r["objection"])

    summary = {
        "n_replayed": len(records), "n_unjoined": unjoined,
        "fork_rate_if_ungated": {"window_A": rate_a, "window_B": rate_b},
        "merge_status_distribution": dict(status_counts),
        "merge_status_share": {k: round(v / n, 3) for k, v in status_counts.items()},
        "nonempty_objection_share": round(nonempty_objection / n, 3) if records else None,
        "control_check": control_results,
        "records": records,
    }
    _write_lab_report(summary, report_stem=report_stem, intro_note=intro_note,
                      scratch_label=f"train_split_merge_{job_tag}")
    return summary


# ---------------------------------------------------------------------------------------------------------
# J-1198, 2026-09-22 (D-0213 RE-RULED by Travis 2026-09-18; F-1682: the ruling never got a build job).
# The run parameters live in a function so scripts/lab_j1198_walkback_replay.py (the Du-offline lab runner,
# which exec()s everything ABOVE the `if True:` main block below and then calls `_run_step2_lab` itself)
# and a plain `python scripts/train_state_invitro.py 40` use the SAME tag / stem / intro note.
# ---------------------------------------------------------------------------------------------------------
def _j1198_run_params(n_per_window: int) -> tuple:
    """(job_tag, report_stem, intro_note) for the D-0213 walk-back replay. The report stem is fixed (not
    date.today()) so a resumed run that crosses midnight still writes the same file."""
    job_tag = "J-1198_walkback_n%d" % n_per_window
    report_stem = "train_split_merge_step2_replay_2026-09-22_walkback"
    intro_note = (
        "**J-1198, 2026-09-22: the D-0213 WALK-BACK replay.** Travis re-ruled D-0213 on 2026-09-18 on "
        "F-1504's evidence (J-1086's run below: UNDETERMINED 62/80 = 77.5%, 48 of the 65 second-call "
        "cases swallowed by J-0986's tiebreak-to-UNDETERMINED fallback): \"Restrict the fallback to the "
        "first disprove call only; let the second call use its own normal verdict logic instead of "
        "falling through to TIEBREAK.\" The ruling never got a build job (F-1682). J-1198 built it "
        "(`_disprove()`: the second call's `if scope_how == \"tiebreak\": return UNDETERMINED` "
        "intercept is gone, so a TIEBREAK-decided scope_only verdict is used like any other -- True -> "
        "held_within_scope, False -> objected; the FIRST call's fallback and a verdict-None second call "
        "are byte-identical to before) and this is the SAME n=80 replay "
        f"(n_per_window={n_per_window}, byte-identical window A via the deterministic `_evenly_spaced`, "
        "window B fresh) re-run with Du OFFLINE (clean shutdown 2026-09-22 08:43:39; the gate was "
        "re-checked every ~30 minutes) against the real hubs, driven by "
        "`scripts/lab_j1198_walkback_replay.py`, which exec()s this file's own definitions and runs "
        "`_run_step2_lab` unchanged with the lab window's infrastructure rules wrapped around it "
        "(timeout >= 300 s, retry of timeout/http errors, exclusion of units that still fail, resumable "
        "results, a write audit; see that runner's docstring and the infrastructure paragraph below). "
        "Compare against `docs/lab/train_split_merge_step2_replay_2026-09-18_scopestatus.md` (J-1086, "
        "the fallback-in-both-calls baseline). The read against D-0213's own defeater (Part 3: the "
        "second call's TIEBREAK-decided votes, their True/False split, same-input consistency, "
        "prompt-order sensitivity) is the last section of this report.\n\n"
        "[HISTORY: the two paragraphs below are J-1086's own 2026-09-18 intro note, kept verbatim; "
        "'this run' in them means J-1086's run, whose numbers are the baseline above.]\n\n"
        "**J-1086, 2026-09-18: this is the first real run of the replay below.** J-0835 "
        "(2026-09-11/12) built the held_within_scope extension but did not run it live (Du "
        "online); J-0904 (2026-09-17/18) declined again the same way. This run confirmed BOTH "
        "preconditions before calling `python scripts/train_state_invitro.py 40`: Du offline "
        "(no live `scripts/run_nascence.py`, `nascence.log` tail ends cleanly with "
        "\"Nascence shutting down.\" and no fresher activity) and this dispatch worktree's own "
        "`data/` populated with real, non-empty, read-only snapshots of the three train-instrument "
        "logs (copied from live, never written back).\n\n"
        "**J-0835, 2026-09-11: disprove EXTENDED with a third merge status, `held_within_scope`, "
        "per D-0181's 2026-09-09 founder ruling (recalibrate disprove).** J-0802 (2026-09-08) "
        "retargeted Lane 1's own PROVE prompt per D-0181's PRIOR ruling and found prove measurably "
        "stopped self-assertively restating (banned-word share 22.7%->6.2%) yet the disprove-"
        "objected share ROSE, not fell (90.0%->95.0%, 85.0%->95.0% on the byte-identical window-A "
        "claims) -- D-0181's own named defeater fired and it was REOPENED. A qualitative read of "
        "J-0802's own 64 non-tiebreak objected events found the dominant complaint had shifted "
        "from 'restates the claim' (now only 5/64) to a harder standard: 30/64 say the support "
        "prove now gives, though real and checkable, doesn't reach the SCOPE/named-mechanism/"
        "generalization the claim itself asserts. This run adds a SECOND disprove call "
        "(`_SCOPE_SYSTEM`/'scope_only', fired only when the first call already found an "
        "objection) asking whether the support is real+independent but merely narrower than the "
        "claim -- if so, the merge status becomes `held_within_scope` (why-text names the "
        "narrower claim) instead of `objected`; only genuinely unsupported/circular claims stay "
        "`objected`. `undetermined` is unchanged. Re-runs the SAME n=80 replay "
        f"(n_per_window={n_per_window}, byte-identical window-A via deterministic "
        "`_evenly_spaced`, window B fresh/comparable-N per this plan's own release-over-release "
        "convention) with prove UNCHANGED from J-0802's own retargeted prompt, plus the 3-case "
        "control check EXTENDED to a 4th case designed to land `held_within_scope` (see "
        "`_CONTROL_CASES`'s own 2026-09-11 entry). D-0181's own new defeater/pass-fail bar (this "
        "job's own briefing): FAIL if any single status is still >90%, OR if held_within_scope "
        "absorbs >70% (a new certainty pole renamed), OR if a qualitative read of ~10 "
        "held_within_scope events shows genuinely unsupported claims landing there. Compare "
        "against `docs/lab/train_split_merge_step2_replay_2026-09-08_provefix.md` (n=80, the "
        "two-status baseline this job extends). Related open thread, NOT folded in here: J-0834 "
        "(tiebreak why-vs-bool coherence, F-1204)."
    )
    return job_tag, report_stem, intro_note


if True:  # always run when this file is executed directly (matches Part 1's own top-level style)
    _n_per_window = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    # J-0835, 2026-09-11 (D-0181, founder-ruled 2026-09-09 via decide-review: "recalibrate
    # disprove"). disprove itself is now EXTENDED with a third merge status (held_within_scope,
    # see _SCOPE_SYSTEM / _disprove's own 2026-09-11 comment) -- prove stays EXACTLY as J-0802
    # retargeted it (D-0181's PRIOR ruling), byte-for-byte unmodified by this job. Tag/stem/note
    # below describe THIS run rather than reusing J-0802's own naming, same reasoning as every
    # prior re-run in this chain (avoid misattribution / filename collision on a same-day re-run).
    #
    # NOT RUN LIVE by J-0835 itself (2026-09-11/12): Du was confirmed ONLINE at dispatch time
    # (scripts/run_nascence.py live, PID matched a real-time process-table read; data/nascence.log
    # showed monologue/deliberation lines timestamped within ~12s of the check) -- per this job's
    # own briefing ("Du-offline reconfirmation before and after -- decline and leave open if Du is
    # online, as J-0791 did"), the live batch below (real calls to 127.0.0.1:11433 and the
    # JUDGE_1/JUDGE_2/TIEBREAK hubs) was NOT executed this session, matching J-0791's own
    # precedent. The code below is offline-verified (see findings-log for this job) but genuinely
    # UNRUN against live infra; the numbers this job's own defeater needs do not exist yet. ALSO
    # NOTE for whoever runs this next: the dispatch worktree this was built in had NO `data/`
    # directory at all (confirmed via `ls`), so `tll`/`ml`/`tsl` above would all load empty and the
    # replay would find 0 real events to join even with Du offline -- populate a real (read-only)
    # copy of `data/train_length_log.jsonl` / `monologue_log.jsonl` / `train_state_log.jsonl` into
    # the run's own worktree first (same real historical files J-0562 onward have always replayed
    # from), or point `_DATA_DIR` at a tree that has them, before trusting a 0-event run as "ran
    # clean" rather than "found nothing to replay".
    #
    # J-1086, 2026-09-18: first REAL run of this replay since J-0835 built it (J-0904 declined
    # again the same way, 2026-09-17/18 -- Du confirmed ONLINE at check time). Both preconditions
    # finally verified BEFORE this run, not assumed: (a) Du offline -- no scripts/run_nascence.py
    # in the live process table, data/nascence.log's own live tail ends cleanly at 2026-09-18
    # 09:13:54 ("Nascence shutting down.") with no fresher activity, current time 09:22+; (b) this
    # dispatch worktree (wt_batch5_web) had the same NO-`data/`-directory gap noted above --
    # populated with real, non-empty, read-only copies of train_length_log.jsonl (9912 lines),
    # monologue_log.jsonl (47944 lines), train_state_log.jsonl (26382 lines) from the live
    # C:\Nascence\data\ tree (copied, never written back) before this run. See findings-log for
    # this job's own row-count confirmation off the script's own "[step2-lab] loaded real logs"
    # line.
    _job_tag, _report_stem, _intro_note = _j1198_run_params(_n_per_window)
    _step2_summary = asyncio.run(_run_step2_lab(_n_per_window, job_tag=_job_tag,
                                                report_stem=_report_stem, intro_note=_intro_note))
    print("\n[step2-lab] SUMMARY:",
         json.dumps({k: v for k, v in _step2_summary.items() if k != "records"}, indent=2))
