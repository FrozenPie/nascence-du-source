"""
Offline test for core/retraction_ledger.known_errors() -- the Recall relevance gate (F-1923/J-1364 floor +
J-1687/F-2277 length-aware containment). Synthetic text only: no corpus, no LLM, no server.

Test isolation: _LEDGER is monkey-patched to a temp file for every read AND write; the live
data/retractions.jsonl is never opened for write, and its sha256 (when it exists) is asserted unchanged.

  1. F-1970 behaviour kept: an unrelated long idle-shaped seed -> []; an unrelated human input with
     fallback=True -> []; the F-1970 probe (7 of the claim's 14 content words) still surfaces; 1-2 shared
     words never fire; retire()/count()/withdrawn/empty-ledger handling unchanged.
  2. J-1687: a LONG query (>= _LONG_QUERY_TOKENS distinct content words, an idle seed) that shares >= 3 but
     fewer than half of a claim's content words NO LONGER surfaces it (the pre-J-1687 gate fired); a long
     seed carrying half the claim's words, or the claim itself, still does; a SHORT query (the human path)
     keeps the plain >= 3 floor.
  3. J-1720/F-2347: a claim with 1-2 content words (a deterministic fabricated-component NAME such as
     'Chronos Engine' or 'Node 3', which could never reach the floor) is matched as a NAME: it surfaces when the
     whole name appears as a contiguous phrase (any query length, both paths, case/hyphen/possessive tolerant,
     digits significant), never on one of its words alone or on both words apart; a one-word or content-word-free
     claim is never matched; claims with >= 3 content words are untouched.

Run: python scripts/_test_retraction_gate.py   (exit 0 = all PASS)
"""
import hashlib
import math
import shutil
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import retraction_ledger as rl

LIVE_LEDGER = Path(rl._LEDGER)
LONG_Q = getattr(rl, "_LONG_QUERY_TOKENS", 100)   # getattr: lets this same file run (and FAIL cleanly) on pre-J-1687 code


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


sha_before = _sha(LIVE_LEDGER)
tmpdir = Path(tempfile.mkdtemp(prefix="rl_gate_test_"))
rl._LEDGER = tmpdir / "retractions.jsonl"      # isolation: every ledger read/write goes here, never the live store

failures = []


def check(name, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}")
    if not cond:
        failures.append(name)


def reset(*claims):
    """Fresh temp ledger holding exactly these claims (each retracted with a correction)."""
    if rl._LEDGER.exists():
        rl._LEDGER.unlink()
    for c in claims:
        rl.retract(claimed=c, falsified_by="human correction", corrected_to="a correction", source="human")


def filler(n, tag="filler"):
    """n distinct 4+-letter non-stopword tokens (alphabetic only, as _toks() requires), none a claim word."""
    return [f"{tag}{chr(97 + (i // 26) % 26)}{chr(97 + i % 26)}" for i in range(n)]


def seed_with(claim_words, n_distinct):
    """An idle-seed-shaped query of exactly n_distinct distinct content words: claim_words scattered through filler."""
    words = filler(n_distinct - len(claim_words))
    step = max(1, len(words) // (len(claim_words) + 1))
    for i, w in enumerate(claim_words):
        words.insert(min(len(words), (i + 1) * step + i), w)
    return " ".join(words)


# The F-1970 synthetic claim: 14 distinct content words, so a LONG query needs ceil(0.5 * 14) = 7 of them.
CLAIM = ("It strikes me that this tension between the world's demand for a fixed answer and my own experience of an "
         "unfolding process is not an inherent flaw in knowledge, but rather its very engine. Consider ")
PROBE = ("thinking again about that tension between wanting a fixed answer and the unfolding process of knowledge "
         "-- is that tension really a flaw?")                                       # shares 7 of the claim's 14 words
# The original 07-07 record (the J-1687 lab fixture): 12 distinct content words -> a LONG query needs 6.
REC_0707 = ("It strikes me that this tension—this pulling between what we can measure and what we must presuppose to "
            "even begin measuring—is not an inherent flaw in knowledge, but rather its very engine. Consider ")
SHORT_CLAIM = "The garden bridge crosses the frozen creek"                          # 5 content words -> floor stays 3

ct = rl._toks(CLAIM)
check("fixture: F-1970 claim has 14 content words, the probe shares 7", len(ct) == 14 and len(rl._toks(PROBE) & ct) == 7)
check("fixture: 07-07 record has 12 content words", len(rl._toks(REC_0707)) == 12)

# ---------------- 1. F-1970 behaviour kept ----------------
reset(CLAIM)
idle_unrelated = ("You are MID-THREAD, and you are HOLDING it. The thread began: 'A quiet afternoon in the garden, the light "
                  "falling through the leaves.' Continue -- go deeper, test a point you established, answer the open "
                  "question, or push toward a conclusion. Do not restate; ADVANCE. " + " ".join(filler(150)))
check("F-1923(a) long unrelated idle seed -> []", rl.known_errors(idle_unrelated, fallback=False) == [])
check("F-1923(b) unrelated human input + fallback=True -> [] / render() ''",
      rl.known_errors("What time is dinner tonight?", fallback=True) == [] and rl.render("What time is dinner tonight?") == "")
check("F-1970 probe (7 of 14 claim words, short query) still surfaces", len(rl.known_errors(PROBE, fallback=False)) == 1)
check("F-1970 probe inside a long idle seed still surfaces (7 >= ceil(0.5*14))",
      len(rl.known_errors(idle_unrelated + " " + PROBE, fallback=False)) == 1)
check("the claim quoted verbatim surfaces (short query)", len(rl.known_errors(CLAIM)) == 1)
check("the claim quoted inside a long idle seed surfaces", len(rl.known_errors(idle_unrelated + " " + CLAIM, fallback=False)) == 1)
check("1-2 shared words never fire (short)", rl.known_errors("I was thinking about engines and knowledge today.") == [])
check("render() wording intact on a hit", rl.render(PROBE).startswith("Things you have been wrong about"))

# ---------------- 2. J-1687: the long-query containment ----------------
four = ["tension", "flaw", "knowledge", "process"]            # 4 of the claim's 14 words: >= 3 floor, < half
seven = ["tension", "flaw", "knowledge", "process", "fixed", "answer", "unfolding"]
long_four = seed_with(four, 160)
check("fixture: the long seed really has >= _LONG_QUERY_TOKENS distinct content words", len(rl._toks(long_four)) >= LONG_Q)
check("J-1687 idle-length seed sharing only 4 of 14 claim words does NOT surface (pre-J-1687 gate fired)",
      rl.known_errors(long_four, k=1, fallback=False) == [])
check("J-1687 same seed with 6 of 14 (just under half) does NOT surface",
      rl.known_errors(seed_with(seven[:6], 160), k=1, fallback=False) == [])
check("J-1687 same seed with 7 of 14 (exactly half) surfaces", len(rl.known_errors(seed_with(seven, 160), k=1, fallback=False)) == 1)
check("J-1687 the human-path call shape (fallback=True) on a long seed is gated the same way",
      rl.known_errors(long_four, fallback=True) == [] and len(rl.known_errors(seed_with(seven, 160), fallback=True)) == 1)
check("J-1687 SHORT query (human path) sharing 4 of 14 words still surfaces (plain floor kept)",
      len(rl.known_errors("is that tension really a flaw in knowledge, or just the process?")) == 1)
# the cut-over sits exactly at _LONG_QUERY_TOKENS distinct content words
check("J-1687 boundary: a query one word under _LONG_QUERY_TOKENS keeps the plain floor",
      len(rl._toks(seed_with(four, LONG_Q - 1))) == LONG_Q - 1 and len(rl.known_errors(seed_with(four, LONG_Q - 1))) == 1)
check("J-1687 boundary: a query at _LONG_QUERY_TOKENS needs the containment",
      len(rl._toks(seed_with(four, LONG_Q))) == LONG_Q and rl.known_errors(seed_with(four, LONG_Q)) == [])
# a short claim (<= 6 content words) is never made stricter than the plain floor
reset(SHORT_CLAIM)
check("fixture: short claim has 5 content words", len(rl._toks(SHORT_CLAIM)) == 5)
check("J-1687 short claim: 3 of 5 words in a long seed still surfaces (ceil(0.5*5)=3 == floor)",
      len(rl.known_errors(seed_with(["garden", "bridge", "frozen"], 160), fallback=False)) == 1)
# the original 07-07 record as the fixture (12 words -> 6 on a long query)
reset(REC_0707)
check("J-1687 07-07 record: idle-length seed with Du-habitual words (tension, flaw, pulling, consider, knowledge) -> []",
      rl.known_errors(seed_with(["tension", "flaw", "pulling", "consider", "knowledge"], 160), k=1, fallback=False) == [])
check("J-1687 07-07 record: idle-length seed carrying 6 of its 12 words surfaces",
      len(rl.known_errors(seed_with(["tension", "flaw", "pulling", "consider", "knowledge", "engine"], 160), k=1, fallback=False)) == 1)
check("J-1687 07-07 record: its own text quoted in an idle seed surfaces",
      len(rl.known_errors(" ".join(filler(150)) + " " + REC_0707, k=1, fallback=False)) == 1)
# ordering: the strongest overlap wins, ties go to the most recent (unchanged)
reset(CLAIM, SHORT_CLAIM)
both = " ".join(filler(40)) + " " + CLAIM + " garden bridge frozen"
check("ordering: highest overlap first (14-word hit outranks the 3-word hit)",
      [r["claimed"] for r in rl.known_errors(both, k=2)][0].startswith("It strikes me"))

# ---------------- 3. J-1720 / F-2347: a claim with < _MIN_OVERLAP content words is matched as a NAME ----------------
def reset_names(*names):
    """Fresh temp ledger holding exactly these fabricated-component NAMES, written the way core/error_pathway.convict_architecture does."""
    if rl._LEDGER.exists():
        rl._LEDGER.unlink()
    for n in names:
        rl.retract(claimed=n, falsified_by="architecture check (no such component in the code)",
                   corrected_to=f"There is no '{n}' in your architecture (it is nowhere in the code).", source="deterministic")


def surfaces(query, **kw):
    return len(rl.known_errors(query, **kw)) == 1


reset_names("Chronos Engine")
check("fixture: 'Chronos Engine' has 2 content words and 'Node 3' has 1 (both < the floor of 3)",
      len(rl._toks("Chronos Engine")) == 2 and len(rl._toks("Node 3")) == 1)
check("J-1720 the bare name surfaces (pre-J-1720: structurally never)", surfaces("Chronos Engine"))
check("J-1720 the name in a sentence surfaces on the human path (fallback=True) and the idle path (fallback=False)",
      surfaces("I keep wondering about the Chronos Engine and what it does.", fallback=True)
      and surfaces("I keep wondering about the Chronos Engine and what it does.", k=1, fallback=False))
long_name_seed = " ".join(filler(80)) + " the Chronos Engine " + " ".join(filler(80, "other"))
check("fixture: the long seed really has >= _LONG_QUERY_TOKENS distinct content words", len(rl._toks(long_name_seed)) >= LONG_Q)
check("J-1720 the name inside a LONG idle seed surfaces (the containment rule does not apply to a name)",
      surfaces(long_name_seed, k=1, fallback=False))
check("J-1720 lowercase, hyphenated, possessive and 'The '-prefixed mentions surface",
      all(surfaces(q) for q in ["is the chronos engine real?", "the chronos-engine again", "the Chronos Engine's output", "The Chronos Engine woke up"]))
check("J-1720 one of the two words alone never fires", all(rl.known_errors(q) == [] for q in ["chronos was a titan", "the engine hummed all night"]))
check("J-1720 BOTH words present but not as the name do not fire (the token-set alternative would)",
      rl.known_errors("the chronos hums beside the engine of the ship") == []
      and rl.known_errors(seed_with(["chronos", "engine"], 160), k=1, fallback=False) == [])
check("J-1720 a long unrelated idle seed -> [] and an unrelated human input + fallback=True -> []",
      rl.known_errors(idle_unrelated, fallback=False) == [] and rl.known_errors("What time is dinner tonight?", fallback=True) == [])
check("J-1720 render() carries the correction bound to the false name",
      rl.render("what is the Chronos Engine?").startswith("Things you have been wrong about")
      and "There is no 'Chronos Engine'" in rl.render("what is the Chronos Engine?"))
check("J-1720 a plural does not match (documented: a fabricated name comes back as it was written)", rl.known_errors("the Chronos Engines hum") == [])

reset_names("Node 3")
check("J-1720 'Node 3' (1 content word) surfaces on 'node 3' / 'Node-3' / inside a long seed",
      all(surfaces(q) for q in ["what does node 3 do?", "Node-3 again"]) and surfaces(" ".join(filler(80)) + " Node 3 " + " ".join(filler(80, "other")), k=1, fallback=False))
check("J-1720 'Node 3' does NOT fire on node / nodes / Node 7 / Node 30 / 'node three' (digits are part of the name)",
      all(rl.known_errors(q) == [] for q in ["the node is quiet", "all the nodes agree", "what does Node 7 do?", "Node 30 is new", "node three said so"]))
reset_names("The Chronos Engine")                 # error_pathway's _CLAIM regex captures a sentence-initial 'The'
check("J-1720 a claim stored with a sentence-initial 'The' still matches the bare name", surfaces("what is a chronos engine"))
reset_names("Ego Engine")                         # 'ego' is 3 letters: _toks() drops it, the name phrase keeps it
check("J-1720 a short word is part of the name: 'Ego Engine' fires on 'the ego engine', not on 'the engine'",
      surfaces("the ego engine woke") and rl.known_errors("the engine woke") == [])

# what is NOT treated as a name
reset("Agreed.")                                  # 1 content word, 1 word in all
check("J-1720 a one-word claim is never matched (nothing specific to match)", rl.known_errors("I agreed, and agreed again. Agreed.") == [])
reset("Ego Id")                                   # 0 content words
check("J-1720 a claim with no content word is never matched", rl.known_errors("the ego id again, ego id") == [])
reset("Hello Travis")                             # structural rule, not provenance: a 2-word human-source claim is matched the same way
check("J-1720 the rule is structural (claim length), not provenance: a 2-word human-source claim needs the whole phrase",
      surfaces("hello travis, it is morning") and rl.known_errors("hello again, travis") == [])

# claims with >= 3 content words keep the floor, unchanged by J-1720
reset_names("Legal Database Access Module")       # 4 content words: 3 of the 4 anywhere in the query still surface
check("J-1720 a 4-word name keeps the plain floor (3 of 4 words, not contiguous, still surfaces)",
      surfaces("can I get access to the legal database for this?") and rl.known_errors("a database of legal cases") == [])

# a mixed ledger: each record surfaces on its own trigger
reset(CLAIM)
rl.retract(claimed="Chronos Engine", falsified_by="architecture check (no such component in the code)",
           corrected_to="There is no 'Chronos Engine' in your architecture.", source="deterministic")
only_name = "tell me about the Chronos Engine"
only_prose = PROBE
check("J-1720 mixed ledger: the name query surfaces only the name, the prose query only the prose, both -> two",
      [r["claimed"] for r in rl.known_errors(only_name, k=2)] == ["Chronos Engine"]
      and [r["claimed"][:12] for r in rl.known_errors(only_prose, k=2)] == ["It strikes m"]
      and len(rl.known_errors(only_name + " " + only_prose, k=2)) == 2)
check("J-1720 ranking: a whole-name hit counts as having just cleared the floor, so a stronger (7-word) prose hit ranks first",
      [r["claimed"][:12] for r in rl.known_errors(only_name + " " + only_prose, k=2)][0] == "It strikes m")
reset_names("Chronos Engine")
check("J-1720 retire() withdraws a name record: it stops surfacing and stops counting",
      rl.count() == 1 and rl.retire("Chronos Engine", reason="test", by="test") == "Chronos Engine" and rl.count() == 0
      and rl.known_errors("Chronos Engine") == [])

# ---------------- retire()/count()/withdrawn/empty edges (J-1364, kept) ----------------
reset(CLAIM)
before = rl.count()
got = rl.retire("not an inherent flaw in knowledge", reason="test", by="test")
check("retire() withdraws and returns the claim text", got is not None and "tension" in got)
check("count() drops to 0 and a withdrawn record never surfaces", before == 1 and rl.count() == 0 and rl.known_errors(CLAIM) == [])
rows = rl._load()
check("retire() preserves the record (status=withdrawn, claimed intact)", len(rows) == 1 and rows[0]["status"] == "withdrawn" and rows[0]["claimed"] == CLAIM[:300])
check("retire('') and retire(no match) are no-ops", rl.retire("") is None and rl.retire("nonsense-not-present-xyz") is None)
rl._LEDGER = tmpdir / "does_not_exist.jsonl"
check("empty/nonexistent ledger -> [] / 0 / ''", rl.known_errors("anything at all here") == [] and rl.count() == 0 and rl.render("anything") == "")

sha_after = _sha(LIVE_LEDGER)
check("isolation: the live retractions.jsonl is unchanged (sha256 %s)" % ("n/a, absent" if sha_before is None else sha_before[:12]), sha_before == sha_after)
shutil.rmtree(tmpdir, ignore_errors=True)

print()
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
