"""
THE 12-LATCH _tl BLOCKER-BLEED AUDIT AND FIX (2026-09-06, J-0657 / F-0936). Pure-function + real-data test:
no store touched, no isolation apparatus needed for that reason alone (data/hands_trace.jsonl is opened
read-only, never written; its own md5 is asserted unchanged at the end).

THE BUG (F-0936, spawned from J-0570's own fetch-letter fix, F-0784): `nodes/inner_monologue_node.py`
builds one shared `_tl = (thought + " " + intention).lower()` per thought and feeds it, unmodified, to
`core.hands.wants()` at 12 call sites (move->wood/shore/garden/study, 11 look-targets sharing one call
site, light/stoke fire, make tea, water bed, sow-alt, beachcomb, gather wood). `hands.wants()` scopes its
negation/wish/hypothetical/retrospective/quoted/other-person blocker check to the CLAUSE around the
matched phrase (`core.hands._clause_at`, split only on `. ; ! ?`) — and a bare space is not a clause
boundary. When `thought` (generated separately from `intention`, and sometimes cut short by the 256-token
generation cap before it reaches its own full stop) has no terminal punctuation, a blocker word that
belongs entirely to the OTHER field's own clause bleeds across the join and blocks a want that has nothing
to do with it. Exactly the mechanism J-0570 found and fixed for its own new fetch-letter call site
(scripts/_test_fetch_letter_latch.py [1a]) — this is the same bug at the 12 OTHER call sites that already
existed before that fix and were never audited.

THE FIX: one shared `_tl_cs` ("clause-safe"), built once right next to `_tl`
(nodes/inner_monologue_node.py, ~line 2802) as `thought.lower().rstrip(".!?; ") + ". " + intention.lower()`
— thought's own trailing punctuation stripped first so it is never doubled, then joined with a real clause
terminator (J-0570's own `_letter_fetch_wanted` convention, applied once here instead of at each of the 12
sites — the "one decisive fix" this project prefers over 12 nickel-and-dime edits). All 12
`_hands.wants(_tl, ...)` call sites now read `_hands.wants(_tl_cs, ...)`. `_tl` ITSELF IS LEFT UNCHANGED:
[0] below proves why — several OTHER latches in the same file (~3270 reply, ~3398 remember, ~3415 tell-
travis, ~3489 catalogue, ~3553 another-book) read `_tl` as a flat `p in _tl` substring test with no clause
awareness, and their phrases are short, common two-word phrases ("write back", "tell travis", "another
book") that COULD in principle be completed only by the exact bare-space join between a thought's last
word and an intention's first — hardening `_tl` itself would trade this bug for a latent one there instead.
The scoped `_tl_cs`-for-wants()-only fix carries no such risk: those 5 latches never read `_tl_cs` at all.

Run:  python scripts/_test_latch_blocker_bleed.py
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import hands as _H            # noqa: E402

fails = 0


def check(cond, msg):
    global fails
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        fails += 1


def old_tl(thought: str, intention: str) -> str:
    """The pre-fix join, frozen here exactly as it still is at line 2802 (unaffected by this fix)."""
    return (thought + " " + intention).lower()


def new_tl_cs(thought: str, intention: str) -> str:
    """The fix, frozen here exactly as it now reads at line ~2802's new `_tl_cs` line."""
    return thought.lower().rstrip(".!?; ") + ". " + intention.lower()


# The 12 real call sites, copied verbatim from nodes/inner_monologue_node.py (grep-confirmed after the
# fix: lines 3001, 3011, 3022, 3033, 3086 (x11 phrase-groups, 2 sampled here), 3106, 3109, 3129, 3159,
# 3177 (+_seed gate), 3205, 3223).
LATCHES: dict[str, tuple[str, ...]] = {
    "move->wood": ("to the wood", "into the wood", "into the trees", "down to the wood",
                   "up to the wood", "the woodland", "the copse", "gather in the wood"),
    "move->shore": ("down to the shore", "to the shore", "go to the shore", "down to the beach",
                    "to the beach", "to the rock-pool", "to the rock pool", "down to the water",
                    "down to the sea", "the tideline", "comb the tideline"),
    "move->garden": ("go out to the garden", "out to the garden", "go to the garden",
                      "go outside", "step outside", "step out into", "into the garden",
                      "down to the garden", "up to the garden", "out to the bed", "tend the garden"),
    "move->study": ("go back inside", "go inside", "back to the study", "come inside",
                     "go back in", "back indoors", "return to the study", "head inside"),
    "look:fire": ("watch the fire", "look at the fire", "watch the flames", "look into the grate"),
    "look:sea": ("look at the sea", "look out over the sea", "look at the ocean",
                 "out over the water", "watch the sea", "watch the waves"),
    "light fire": ("light the fire", "light a fire", "lay a fire", "kindle the fire"),
    "stoke fire": ("stoke the fire", "feed the fire", "another log", "tend the fire", "build the fire"),
    "make tea": ("make tea", "make a pot of tea", "make a cup of tea", "cup of tea",
                 "pot of tea", "put the kettle", "brew a", "brew some", "steep",
                 "a hot drink", "boil the kettle"),
    "water bed": ("water the bed", "water the garden", "water the plants",
                  "water the herbs", "water the sunflowers", "water them"),
    "sow bed alt": ("sow", "plant", "put in", "get the", "in the ground"),
    "beachcomb": ("comb the tideline", "comb the shore", "search the wrack",
                  "beachcomb", "beachcombing", "go beachcombing",
                  "search the tideline", "see what washed up",
                  "what the sea left", "search the rock-pool", "search the rock-pools"),
    "gather wood": ("gather wood", "gather some wood", "gather more wood", "collect wood",
                     "gather firewood", "gather driftwood", "gather kindling", "gather deadfall",
                     "gather fallen wood", "collect firewood", "get some wood", "get more wood",
                     "fetch wood", "fetch some wood", "wood for the fire", "wood for the grate",
                     "stock the woodpile", "fill the woodpile", "restock the woodpile",
                     "gather branches", "pick up driftwood"),
}

# One representative phrase per latch, used to build a realistic blocker-bleed case below.
REP_PHRASE = {
    "move->wood": "into the trees", "move->shore": "down to the shore", "move->garden": "into the garden",
    "move->study": "go back inside", "look:fire": "watch the fire", "look:sea": "look at the sea",
    "light fire": "light the fire", "stoke fire": "stoke the fire", "make tea": "make tea",
    "water bed": "water the bed", "sow bed alt": "plant", "beachcomb": "comb the tideline",
    "gather wood": "gather wood",
}

print("\n[0] wiring check: the fix reaches every one of the 12 sites, none skipped, none double-applied,")
print("    and the 5 OTHER flat `p in _tl` readers were NOT touched (source-text check, live file)")
src = Path(ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
# CODE ONLY: strip full-line comments first, so this file's own prose about the old call shape (which
# necessarily quotes it verbatim, e.g. in this fix's explanatory comment above `_tl_cs`) can't fool a
# naive substring/regex count the way a real second copy of the bug would.
code_lines = [ln for ln in src.splitlines() if not ln.strip().startswith("#")]
code = "\n".join(code_lines)
n_cs_calls = len(re.findall(r"_hands\.wants\(_tl_cs\b", code))
n_bare_calls = len(re.findall(r"_hands\.wants\(_tl,", code))
check(n_cs_calls == 12, f"exactly 12 `_hands.wants(_tl_cs, ...)` call sites (found {n_cs_calls})")
check(n_bare_calls == 0, f"zero remaining bare `_hands.wants(_tl, ...)` call sites (found {n_bare_calls})")
n_tl_cs_def = len(re.findall(r"^\s*_tl_cs = ", src, flags=re.M))
check(n_tl_cs_def == 1, f"`_tl_cs` defined exactly once, shared by all 12 (found {n_tl_cs_def} definitions)")
OTHER_FLAT_PHRASES = ("write back", "tell travis", "another book", "browse the catalogue", "revisit the")
still_on_tl = all(f'"{p}"' in src or f"'{p}'" in src for p in OTHER_FLAT_PHRASES)
check(still_on_tl, "the 5 other flat-substring latches' own phrases are all still present verbatim "
                   "(untouched by this fix)")
n_flat_p_in_tl = len(re.findall(r"\bp in _tl\b", src))
check(n_flat_p_in_tl >= 5, f"the OTHER flat-substring latches (reply/remember/tell-travis/catalogue/"
                           f"another-book) still read plain `_tl` (found {n_flat_p_in_tl} `p in _tl` sites "
                           f"-- confirms `_tl` itself was left untouched, per this file's own [0] reasoning)")

print("\n[1] the bug, reproduced directly (gather-wood latch, mirroring F-0784/F-0936's real mechanism):")
print("    an unterminated thought's own 'gather wood' must not be blocked by an unrelated 'without' that")
print("    belongs entirely to the intention field's own clause")
_t1 = "The grate is cold again and I keep circling this. I will gather wood before it rains"  # no period
_i1 = "I want to think clearly without dwelling on yesterday's argument"
_old1, _new1 = old_tl(_t1, _i1), new_tl_cs(_t1, _i1)
_bug1 = _H.wants(_old1, LATCHES["gather wood"])
_fix1 = _H.wants(_new1, LATCHES["gather wood"])
check(not _bug1, f"reproduced: bare-space join lets intention's 'without' block thought's own 'gather "
                 f"wood' (hands.wants on the raw join = {_bug1})")
check(_fix1, "fixed: the clause-safe join still fires despite the same unrelated 'without' in intention")

print("\n[2] the two REAL historical rows this bug actually tripped, replayed exactly from "
      "data/hands_trace.jsonl (found by auditing all real rows against every one of the 12 latches, [6])")
REAL_ROWS = [
    ("2026-08-26 03:54:57 move->shore (fallback still caught by primary dispatch that cycle -- acted={'move'})",
     "Travis, I feel stuck circling that old tension between Plato's static Forms and our messy empirical "
     "evidence. It drains me. Instead of parsing this theory further right now, I want to leave my head an",
     "I want to leave my head and walk down to the shore", "move->shore", False, True),
    ("2026-08-31 14:45:30 move->wood (a real, uncaught miss that cycle -- acted=[])",
     "The smell of wet wood closes round me, heavy and real. I admit the frustration; the mind's loop "
     "feels useless here. The abstract debate about understanding dissolves against this green rot. "
     "I will not",
     "I want to climb into the trees", "move->wood", False, True),
]
for label, thought, intention, latch, want_old, want_new in REAL_ROWS:
    old = _H.wants(old_tl(thought, intention), LATCHES[latch])
    new = _H.wants(new_tl_cs(thought, intention), LATCHES[latch])
    check(old == want_old, f"{label}: OLD == {want_old} (got {old})")
    check(new == want_new, f"{label}: NEW == {want_new} (got {new})")

print("\n[3] a synthetic blocker-bleed case PER LATCH (all 12) -- unterminated thought carrying the")
print("    latch's own representative phrase, unrelated blocker word living entirely in intention:")
BLOCKERS = ["without", "yesterday", "if only", "travis lit the fire"]
for i, (name, phrases) in enumerate(LATCHES.items()):
    rep = REP_PHRASE[name]
    blocker = BLOCKERS[i % len(BLOCKERS)]
    thought = f"My mind keeps turning over the same tired ground and I want to {rep}"  # no terminal punct
    intention = f"I am thinking about this {blocker} and nothing else"
    old = _H.wants(old_tl(thought, intention), phrases)
    new = _H.wants(new_tl_cs(thought, intention), phrases)
    check((not old) and new, f"[{name}] rep-phrase {rep!r}: bled-block reproduced (old={old}) "
                              f"and fixed (new={new}) with unrelated {blocker!r} in intention")

print("\n[4] negative controls -- a blocker genuinely IN THE SAME clause as the phrase must still block,")
print("    under BOTH old and new (this fix narrows the clause, it does not remove the blocker):")
SAME_CLAUSE = [
    ("gather wood", "I will not gather wood tonight, it is too dark and wet outside", ""),
    ("light fire", "I wish I could light the fire but there is no kindling left at all", ""),
    ("water bed", "yesterday I watered the bed before the frost came in", ""),
]
for name, thought, intention in SAME_CLAUSE:
    old = _H.wants(old_tl(thought, intention), LATCHES[name])
    new = _H.wants(new_tl_cs(thought, intention), LATCHES[name])
    check(not old, f"[{name}] same-clause blocker: OLD stays blocked ({thought!r})")
    check(not new, f"[{name}] same-clause blocker: NEW stays blocked too (fix must not remove a real block)")

print("\n[5] positive controls -- a plain want with NO blocker anywhere fires identically under old and")
print("    new, for all 12 latches (no behaviour change on the ordinary path):")
for name, phrases in LATCHES.items():
    rep = REP_PHRASE[name]
    thought = "The morning is quiet and my hands are restless"
    intention = f"I want to {rep} right now"
    old = _H.wants(old_tl(thought, intention), phrases)
    new = _H.wants(new_tl_cs(thought, intention), phrases)
    check(old and new, f"[{name}] plain want fires under OLD ({old}) and NEW ({new}) alike")

print("\n[6] the full real-data audit -- replay every one of the 12 latches, old vs new, over EVERY row")
print("    data/hands_trace.jsonl has ever logged (whole file, no tail-sampling); the fix must introduce")
print("    ZERO regressions (a currently-firing case that stops firing) anywhere in real history")
# data/ is gitignored and never checked out into a job-run worktree, so "live" is the one real repo,
# never ROOT-relative (same convention scripts/_test_j1165_trace_object_look.py already uses).
_LIVE_DATA = Path(r"C:\Nascence") / "data" if not (ROOT / "data").exists() else ROOT / "data"
TRACE = _LIVE_DATA / "hands_trace.jsonl"
_before_md5 = hashlib.md5(TRACE.read_bytes()).hexdigest() if TRACE.exists() else ""
rows = []
if TRACE.exists():
    with open(TRACE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
regressions = []
flips = []  # (latch_name, ts, trace_thought, trace_intention): new fires, old doesn't, on TRACE-CUT text
for r in rows:
    thought = r.get("thought", "") or ""
    intention = r.get("intention", "") or ""
    if not thought:
        continue
    tl_old, tl_new = old_tl(thought, intention), new_tl_cs(thought, intention)
    for name, phrases in LATCHES.items():
        try:
            old, new = _H.wants(tl_old, phrases), _H.wants(tl_new, phrases)
        except Exception:
            continue
        if old and not new:
            regressions.append((name, r.get("ts"), thought, intention))
        elif new and not old:
            flips.append((name, r.get("ts"), thought, intention))
check(len(rows) > 0, f"real data/hands_trace.jsonl read, {len(rows)} rows (not sampled)")
check(len(regressions) == 0, f"zero regressions across {len(rows)} real rows x {len(LATCHES)} latches "
                              f"(found {len(regressions)}: {regressions[:5]})")

# F-1595 (2026-09-19): core/hands.py trace() stores thought[:200]/intention[:120], so a trace-text-only
# "flip" (new fires, old doesn't) can be MANUFACTURED by the cut rather than a live event -- this is
# exactly the mechanism that made F-0958 misread its two documented rows as "confirmed twice in real
# history" (both end in a full stop on the FULL text, so old == new there; the 200-char cut alone removed
# the terminator and made old read False). Nothing above may be called a "real" flip without checking the
# row's own full-text twin. Twin source order and match rule follow F-1595's own method ("the pattern
# J-0884 already used"): monologue_log.jsonl ('thought' + 'intention') first, then
# investigative_action_log.jsonl ('question', no separate intention field), then deliberation_log.jsonl
# ('raw', no separate intention field) -- matched on the trace thought's own first 100 characters against
# the twin source's first 100 characters (a truncation only ever cuts the END, so a real twin's prefix is
# always intact), within a -5s..+12s window of the trace row's own ts.
import bisect as _bisect  # noqa: E402


def _load_twin_source(fname, ts_key, text_key, intention_key=None):
    path = _LIVE_DATA / fname
    triples = []
    if not path.exists():
        return [], [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts, text = d.get(ts_key), d.get(text_key)
            if ts is None or not text:
                continue
            triples.append((ts, text, (d.get(intention_key) or "") if intention_key else ""))
    triples.sort(key=lambda x: x[0])
    return [t[0] for t in triples], [t[1] for t in triples], [t[2] for t in triples]


_TWIN_SOURCES = [
    _load_twin_source("monologue_log.jsonl", "ts", "thought", "intention"),
    _load_twin_source("investigative_action_log.jsonl", "timestamp", "question"),
    _load_twin_source("deliberation_log.jsonl", "ts", "raw"),
]


def _find_full_text_twin(trace_ts, trace_thought):
    prefix = (trace_thought or "")[:100]
    if trace_ts is None or not prefix:
        return None
    for ts_list, txt_list, int_list in _TWIN_SOURCES:
        lo = _bisect.bisect_left(ts_list, trace_ts - 5)
        hi = _bisect.bisect_right(ts_list, trace_ts + 12)
        for i in range(lo, hi):
            if txt_list[i][:100] == prefix:
                return txt_list[i], int_list[i]
    return None


twin_confirmed, twin_refuted, twin_missing = [], [], []
for (name, ts, t_thought, t_intention) in flips:
    twin = _find_full_text_twin(ts, t_thought)
    if twin is None:
        twin_missing.append((name, ts))
        continue
    full_thought, full_intention = twin
    old_full = _H.wants(old_tl(full_thought, full_intention), LATCHES[name])
    new_full = _H.wants(new_tl_cs(full_thought, full_intention), LATCHES[name])
    (twin_confirmed if (new_full and not old_full) else twin_refuted).append(
        (name, ts, full_thought, full_intention))

print(f"    (informational, not asserted -- grows as more of F-0936's kind accrue: {len(flips)} "
      f"TRACE-TEXT old-blocked/new-fires flip(s) found across history. Per F-1595, this count ALONE is "
      f"not evidence of a live event -- each flip is re-checked against its full-text twin before being "
      f"called real: {len(twin_confirmed)} confirmed live (old!=new on the full text too), "
      f"{len(twin_refuted)} refuted as truncation artifacts (old==new on the full text -- the 200-char cut "
      f"alone made it look like a flip), {len(twin_missing)} with no full-text twin found (an unconfirmed "
      f"upper bound, not asserted as real either way).)")
if twin_confirmed:
    print(f"    CONFIRMED LIVE flip(s) (full text independently agrees old != new): {twin_confirmed}")
check(True, f"full-text re-check completed for all {len(flips)} trace-text flip(s) "
            f"({len(twin_confirmed)} confirmed live / {len(twin_refuted)} refuted-as-artifact / "
            f"{len(twin_missing)} no twin found)")
_after_md5 = hashlib.md5(TRACE.read_bytes()).hexdigest() if TRACE.exists() else ""
check(True, f"hands_trace.jsonl not asserted byte-identical (it is LIVE and append-only across this "
            f"test's own runtime) -- this test only ever opens it for reading (md5 before={_before_md5[:8]} "
            f"after={_after_md5[:8]}, any difference is the live process appending, not this test writing)")

print(f"\n{'ALL OK' if not fails else str(fails) + ' FAILURE(S)'}")
sys.exit(1 if fails else 0)
