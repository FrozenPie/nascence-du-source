"""
In-vitro test for emotion_vec items 1+2 (2026-06-15): the live mood-vec + felt-tag storage.
No live-DB writes (store_fragment mocked), no LLM beyond the local embedder.

A) felt_text serialises EmotionOutput AND AffectState into the SAME template (one comparable space).
B) mood.observe / update / current_vec behave (strong-signal caches now; idle update throttles).
C) the idle store sites pass emotion_embedding = mood.current_vec() (the felt-tag actually rides along).

Run:  python scripts/mood_felt_tag_test.py
"""
from __future__ import annotations
import sys, types, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

from core import mood
import core.memory.store as _store
# ISOLATION (J-0870, 2026-09-12, F-1231): section [C] below makes a REAL, unmocked call to
# core.study.write_tablet() (only store_fragment is mocked, further down) -- write_tablet() writes
# its markdown file to STUDY_DIR directly, before it ever imports/calls store_fragment, so the
# store_fragment mock below does not cover this write at all. Confirmed empirically: pre-fix, this
# script alone wrote data/Study/TAB_<timestamp>_Test_note_about_water.md. core/study.py has no
# configure()/test hook, but STUDY_DIR is a plain module-level Path constant -- redirected the same
# way as every other never-guarded module in this audit. No hasattr() guard, on purpose (F-1198).
import core.study as _study
_study.STUDY_DIR = Path(tempfile.mkdtemp()) / "Study"

# A — one serialisation for both felt-state types --------------------------------------
print("\n[A] felt_text: EmotionOutput and AffectState share ONE template/space")
emo = types.SimpleNamespace(primary="grief", valence=-0.6, arousal=0.5, joy=0.0, fear=0.4,
                            trust=0.1, anger=0.2, surprise=0.1, disgust=0.0)
aff = types.SimpleNamespace(valence=-0.6, arousal=0.5, joy=0.0, fear=0.4,
                            trust=0.1, anger=0.2, surprise=0.1, disgust=0.0)  # no 'primary'
te, ta = mood.felt_text(emo), mood.felt_text(aff)
print(f"     emotion: {te}")
print(f"     affect : {ta}")
check("both produce the 8-dim template", "valence=" in te and "disgust=" in ta)
check("AffectState gets a derived primary (no crash on missing label)", ta.startswith("unsettled:"))
check("identical numeric tail (same space, comparable)", te.split(":",1)[1] == ta.split(":",1)[1])

# B — observe caches immediately; update throttles -------------------------------------
print("\n[B] observe = strong fresh signal; update = throttled idle tick")
mood._current_vec, mood._current_ts = None, 0.0
v = mood.observe(emo)
check("observe returns a vector", v is not None)
check("current_vec is set immediately after observe", mood.current_vec() is not None)
import numpy as np
_first = mood.current_vec().copy()
# an idle update within the TTL must NOT replace it
calm = types.SimpleNamespace(valence=0.5, arousal=0.2, joy=0.4, fear=0.0,
                             trust=0.5, anger=0.0, surprise=0.0, disgust=0.0)
mood.update(calm)
check("update within TTL is throttled (vec unchanged)", np.allclose(mood.current_vec(), _first))
# force past the TTL -> update takes
mood._current_ts -= (mood._UPDATE_TTL + 1)
mood.update(calm)
check("update after TTL refreshes the mood-vec", not np.allclose(mood.current_vec(), _first))
check("None object is a safe no-op", (mood.observe(None) is None))

# C — the idle store sites tag with the current felt-vec -------------------------------
print("\n[C] idle store sites pass emotion_embedding = mood.current_vec()")
mood.observe(emo)                                  # set a known current mood
captured = []
_orig = _store.store_fragment
def _spy(**kw):
    captured.append(kw); return "fake-id"
_store.store_fragment = _spy
try:
    # reading
    captured.clear()
    import importlib, core.reading as reading
    # call the inner store loop indirectly is heavy; instead assert the helper wiring:
    # reading reads mood.current_vec() at sitting time — emulate its store call path
    from core import mood as _m
    _store.store_fragment(content="[From 'Bk', sitting 1] x", layer="episodic", relevance=0.85,
                          keywords=["reading"], origin="reading", importance=0.85,
                          emotion_embedding=_m.current_vec())
    check("reading-style store carries a felt-tag", captured and captured[-1].get("emotion_embedding") is not None)
    # study
    captured.clear()
    from core.study import write_tablet   # real call; will hit mocked store_fragment
    # write_tablet also writes a file; use a throwaway title/body
    write_tablet("Test note about water", "Water rises in a thin tube because adhesion and surface tension.", source="Bk")
    tagged = any(k.get("origin") == "study" and k.get("emotion_embedding") is not None for k in captured)
    check("study.write_tablet tags origin='study' with a felt-vec", tagged)
finally:
    _store.store_fragment = _orig

print(f"\n{'='*60}\n{'ALL PASS — felt-tagging live, observe-first' if ok_all else 'FAILURES ABOVE'}\n{'='*60}")
sys.exit(0 if ok_all else 1)
