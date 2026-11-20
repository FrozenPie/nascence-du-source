"""
In-vitro test for the BOREDOM-REDIRECT (#2, 2026-06-15). No LLM, temp frontier store.
A) the gap-nudge is a SINGLE bounded pre-redirect pause, not a sustained plateau or an
   escalating ramp — it fires only below REDIRECT_THRESHOLD and is undone once the redirect
   itself takes over (J-0876/F-1291: rewritten from a stale "stays elevated" assertion that
   never matched the 2026-06-16 BUGFIX in nodes/inner_monologue_node.py::_compute_gap).
B) frontier.closeable_seed returns only finding-carrying (closeable) questions.
C) _redirect_patch turns OUTWARD: a closeable Frontier question first, else the open book.

Run:  python scripts/boredom_redirect_test.py
"""
from __future__ import annotations
import sys, tempfile, types
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

from nodes.inner_monologue_node import InnerMonologueNode, REDIRECT_THRESHOLD
from core import frontier as fr
# ISOLATION (J-0928, 2026-09-14, F-1291/J-0876): sections [B]/[C] below call fr.note_question()
# 3x; frontier.py:170-175 unconditionally fires core.satisfaction.record("frontier_born") inside
# a bare `except Exception: pass` on every one of those calls. core.satisfaction._LOG/_STATE are
# never redirected by anything else in this script -- a 7th script carrying the exact unfenced-
# cognitive-store class J-0870/F-1287 already fixed in 6 others (missed there, not in that job's
# own named list). Redirect BEFORE the first note_question() call below, same tempdir + naming
# convention fr._F/_F_LIGHT already use (no hasattr() guard, on purpose, F-1198).
from core import satisfaction as _sat
_sat._LOG = Path(tempfile.gettempdir()) / "boredom_satisfaction_test.jsonl"
_sat._STATE = Path(tempfile.gettempdir()) / "boredom_satisfaction_test_state.json"
_sat._LOG.unlink(missing_ok=True)
_sat._STATE.unlink(missing_ok=True)

node = InnerMonologueNode()

# A — ONE bounded pre-redirect pause: nudges up below REDIRECT_THRESHOLD, then is UNDONE ---
# (not a sustained plateau across every bored streak, and not an escalating ramp). Per
# _compute_gap's own "BUGFIX 2026-06-16" comment: once streak reaches REDIRECT_THRESHOLD,
# _redirect_patch is boredom's real response, and stretching the gap further would
# paradoxically slow the very tick that should turn outward — so the pause is removed, not
# sustained. This matches the original design doc's own language exactly (one of "at most ONE
# bounded incubation pause", docs/completed/boredom_redirection_research.md §3 design
# implication 1) — g1 == g2 in the old assertion was a stale reading of "single" as "flat
# elevated plateau" instead of "fires once, pre-redirect, then stops" (J-0876/F-1291).
print("\n[A] _compute_gap: boredom gets ONE brief PRE-REDIRECT pause, not a sustained/escalating one")
state = types.SimpleNamespace(
    dissonance=types.SimpleNamespace(value=0.0),
    affect=types.SimpleNamespace(arousal=0.3),
)
def g(streak):
    node._bored_streak = streak
    return node._compute_gap(state)
g0, g1, g2, g3, g5 = g(0), g(1), g(2), g(3), g(5)
print(f"     gap by streak: 0={g0:.0f}  1={g1:.0f}  2={g2:.0f}  3={g3:.0f}  5={g5:.0f}"
      f"  (REDIRECT_THRESHOLD={REDIRECT_THRESHOLD})")
check("boredom nudges the gap up pre-redirect (g1 > g0)", g1 > g0)
check(f"the pause is UNDONE at/after REDIRECT_THRESHOLD ({REDIRECT_THRESHOLD}): "
      "g2==g3==g5==g0 (redirect takes over, not a sustained plateau)", g2 == g3 == g5 == g0)
check("the old 1.5**streak balloon is gone (g5 < 2*g1)", g5 < 2 * g1)
node._bored_streak = 0

# B — closeable_seed only returns finding-carrying questions -----------------------------
print("\n[B] frontier.closeable_seed returns only CLOSEABLE (finding-carrying) questions")
tmp = Path(tempfile.gettempdir()) / "boredom_frontier_test.json"
if tmp.exists(): tmp.unlink()
fr._F = tmp
fr._F_LIGHT = tmp.with_name("boredom_frontier_test.light.json")   # J-0846 (F-1212/F-1213): light sidecar too
fr._F_LIGHT.unlink(missing_ok=True)
fr.note_question("Why does capillary action draw water up a narrow tube?", "curiosity")
fr.note_question("What makes granite form those strange coatings?", "curiosity")
check("no finding yet -> closeable_seed is None", fr.closeable_seed() is None)
# attach a finding to the first
p = fr.pending_pursuit()
fr.attach_finding(p["id"], "Capillary action",
                  "Capillary action is caused by adhesion and surface tension drawing liquid upward.")
seed = fr.closeable_seed()
print(f"     closeable -> {seed['q'][:50] if seed else None}")
check("now returns the question that carries a finding", seed and "capillary" in seed["q"].lower())
check("the finding rides along", seed and "adhesion" in (seed.get("finding") or "").lower())

# C — _redirect_patch turns outward: frontier first, else the book -----------------------
print("\n[C] _redirect_patch: closeable Frontier question > the open book")
# re-attach (closeable_seed marked it offered; OFFER_GAP keeps it from re-offering immediately),
# so use a fresh question to guarantee a closeable one is available this instant
fr.note_question("Why do stars twinkle when planets do not?", "curiosity")
p2 = fr.pending_pursuit()
fr.attach_finding(p2["id"], "Stellar scintillation",
                  "Twinkling is caused by turbulence in the atmosphere refracting starlight.")
patch = node._redirect_patch()
print(f"     patch kind = {patch[1] if patch else None}")
check("redirects to a frontier question when one is closeable", patch and patch[1] == "frontier")
check("the seed turns him OUTWARD (sets the loop down)", patch and "set it down" in patch[0].lower())

# empty frontier -> falls back to the book
tmp.unlink(missing_ok=True)
fr._F_LIGHT.unlink(missing_ok=True)
fr._F = Path(tempfile.gettempdir()) / "boredom_frontier_empty.json"
if fr._F.exists(): fr._F.unlink()
fr._F_LIGHT = fr._F.with_name("boredom_frontier_empty.light.json")   # J-0846
fr._F_LIGHT.unlink(missing_ok=True)
patch2 = node._redirect_patch()
print(f"     patch kind (no frontier) = {patch2[1] if patch2 else None}")
check("falls back to OPEN THE BOOK when no closeable question", patch2 and patch2[1] == "reading")
check("book fallback instructs the read", patch2 and "open the book" in patch2[0].lower())
fr._F.unlink(missing_ok=True)
fr._F_LIGHT.unlink(missing_ok=True)
_sat._LOG.unlink(missing_ok=True)          # J-0928
_sat._STATE.unlink(missing_ok=True)        # J-0928

print(f"\n{'='*60}\n{'ALL PASS — boredom redirects, silence is capped' if ok_all else 'FAILURES ABOVE'}\n{'='*60}")
sys.exit(0 if ok_all else 1)
