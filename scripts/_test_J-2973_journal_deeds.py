"""
Hermetic test for J-2973 (F-3663, F-3664, F-3667; P-0068): the nightly journal's deed input and SHAPE example.
No LLM, no live data: the model call is a fake that captures the user prompt; the journal dir / recap clock are
pointed at a temp dir; store_fragment, the frontier note and the likes ledger are stubbed.

  [1] a 60-deed, 20 h window with 20 thought-lines mixed in: the prompt holds at most 12 deeds, includes the first
      and the last deed, includes deeds from the last third of the window, keeps their order, and no "librarian" /
      "recall_evidence" line appears; it says how many kinds of thing there were and tells the model not to say it
  [2] a short window (<= 12 distinct deeds): all shown, no "spread" sentence
  [3] duplicate deeds (any case / spacing) show once, at first place
  [4] only thought-lines in the window: no model call, no file, no recap stamp
  [5] JOURNAL_SPREAD_ENABLED False restores the old input (first 12 in time order, thought-lines included)
  [6] JOURNAL_SYS carries no copyable worked example (the old SHAPE sentence and its pieces are gone, and no
      quoted full-sentence example remains); re-measure: difflib ratio of the old example against the prompt's
      best-matching sentence is low
  [7] the 124/328 measure on a synthetic window: thought-lines among the 12 shown = 0 (was 100% of a thought-heavy start)

Run:  python scripts/_test_J-2973_journal_deeds.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, difflib, re, sys, tempfile, types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE anything else from the tree (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import journal as J

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

TMP = Path(tempfile.mkdtemp(prefix="J2973_"))
J._JOURNAL_DIR = TMP / "Journal"
J._DAY_STATE_F = J._JOURNAL_DIR / ".day_recap_state.json"
J._frontier_note = lambda since: None
import core.memory.store as _store
_store.store_fragment = lambda *a, **k: None      # never write a live fragment

STATE = types.SimpleNamespace(affect=types.SimpleNamespace(valence=0.0, primary="calm"))
CALLS: list[str] = []

async def fake_model(base_urls, sys_prompt, user, **kw):
    CALLS.append(user)
    return {"entry": "I did some things today. It was a quiet day.", "liked": []}

def run(deeds):
    CALLS.clear()
    J._deeds_since = lambda since: list(deeds)
    J._DAY_STATE_F.unlink(missing_ok=True) if J._DAY_STATE_F.exists() else None
    return asyncio.run(J.write_entry(fake_model, ["http://stub"], STATE))

def prompt_deeds(user):
    return [ln[4:].strip() for ln in user.splitlines() if ln.startswith("  - ")]

# --- [1] 60 deeds over 20 h, 20 thought-lines mixed in --------------------------------------------------------
real = [f"observed thing number {i:02d}" for i in range(60)]
mixed = []
for i, d in enumerate(real):
    mixed.append(d)
    if i % 3 == 0:
        mixed.append(("librarian " if i % 2 else "recall_evidence ") + f"what was on my mind {i} cut mid-wo")
check("fixture: 80 rows, 60 real, 20 thought-lines", len(mixed) == 80 and sum(J._is_thought_line(x) for x in mixed) == 20)
p = run(mixed)
check("[1] entry written", p is not None and len(CALLS) == 1)
u = CALLS[0]; shown = prompt_deeds(u)
check("[1] at most 12 deeds shown", 1 <= len(shown) <= 12)
check("[1] first deed shown", real[0] in shown)
check("[1] last deed shown", real[-1] in shown)
last_third = set(real[40:])
check("[1] deeds from the last third of the window are named", len(last_third & set(shown)) >= 3)
check("[1] spread across the window (each third has at least 3)",
      all(len(set(real[a:b]) & set(shown)) >= 3 for a, b in ((0, 20), (20, 40), (40, 60))))
check("[1] order kept", [real.index(x) for x in shown] == sorted(real.index(x) for x in shown))
check("[1] no thought-line appears as a deed", not any("librarian" in x or "recall_evidence" in x for x in shown))
check("[1] no thought-line anywhere in the prompt", "librarian" not in u and "recall_evidence" not in u)
check("[1] says how many kinds of thing (60) and not to say it", "60 different kinds" in u and "Do not say how many" in u)

# --- [2] short window -----------------------------------------------------------------------------------------
short = [f"did short thing {i}" for i in range(7)]
run(short); u = CALLS[0]
check("[2] all 7 shown", prompt_deeds(u) == short)
check("[2] no spread sentence", "different kinds" not in u and u.startswith("Today, the plain record of what you actually did:"))

# --- [3] duplicates -------------------------------------------------------------------------------------------
run(["Went out to the garden", "observe the tide", "went  out to the garden", "OBSERVE THE TIDE", "looked at the sea"])
check("[3] duplicates once, first place kept",
      prompt_deeds(CALLS[0]) == ["Went out to the garden", "observe the tide", "looked at the sea"])

# --- [4] only thought-lines -----------------------------------------------------------------------------------
r = run(["librarian is this so", "recall_evidence my own past days"])
check("[4] no model call, no entry, no stamp", r is None and not CALLS and not J._DAY_STATE_F.exists())

# --- [5] flag off = old input ---------------------------------------------------------------------------------
J.JOURNAL_SPREAD_ENABLED = False
run(mixed); old = prompt_deeds(CALLS[0])
check("[5] flag off: first 12 rows in time order, thought-lines included",
      old == [x.strip() for x in mixed[:12]] and any(J._is_thought_line(x) for x in old))
J.JOURNAL_SPREAD_ENABLED = True

# --- [6] no copyable example ----------------------------------------------------------------------------------
OLD_SHAPE = ("I read more of my book today and wrote some notes on it. I went out to the garden a few times. "
             "I practised my arithmetic. It was a quiet, good day.")
sysp = J.JOURNAL_SYS
check("[6] old SHAPE sentences absent",
      all(s.strip() not in sysp for s in re.split(r"(?<=\.)\s+", OLD_SHAPE)) and "For SHAPE only" not in sysp)
check("[6] 'went out to the garden a few times' / 'practised my arithmetic' gone",
      "garden a few times" not in sysp and "arithmetic" not in sysp)
sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", sysp) if len(s.strip()) > 20]
best = max(difflib.SequenceMatcher(None, OLD_SHAPE.lower(), s.lower()).ratio() for s in sents)
sh = [difflib.SequenceMatcher(None, OLD_SHAPE.lower(), s.lower()).ratio() for s in re.split(r"(?<=\.)\s+", OLD_SHAPE)]
best_sent = max(max(difflib.SequenceMatcher(None, o.lower(), s.lower()).ratio() for s in sents)
                for o in re.split(r"(?<=\.)\s+", OLD_SHAPE))
print(f"      best whole-example ratio {best:.2f}, best per-sentence ratio {best_sent:.2f}")
check("[6] nothing in the prompt is near the old example (per-sentence ratio < 0.6)", best_sent < 0.6)
check("[6] the prompt still forbids invention and still asks for the JSON shape",
      "Invent NOTHING" in sysp and '"entry"' in sysp and '"liked"' in sysp)

# --- [7] the thought-line share, synthetic thought-heavy start -------------------------------------------------
heavy = [("librarian " if i % 2 else "recall_evidence ") + f"query {i} cut mid-w" for i in range(15)] + real
run(heavy); shown = prompt_deeds(CALLS[0])
old_share = sum(J._is_thought_line(x) for x in heavy[:12]) / 12
new_share = sum(J._is_thought_line(x) for x in shown) / max(1, len(shown))
check(f"[7] thought-lines among deeds shown: {old_share:.0%} before -> {new_share:.0%} now", old_share == 1.0 and new_share == 0.0)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
