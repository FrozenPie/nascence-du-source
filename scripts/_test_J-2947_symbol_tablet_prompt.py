"""J-2947 (F-3634, P-0067): the symbol tablet prompt gets a real "before", no drift number, no duplicate
voice, sentence-boundary cuts. Stubs every model call, the embedder and the store; touches no live data."""
import asyncio, re, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
import numpy as np  # noqa: E402
from core import symbol_evolution as se  # noqa: E402

assert Path(se.__file__).resolve().is_relative_to(ROOT), se.__file__
TMP = Path(tempfile.mkdtemp(prefix="j2947_"))   # nothing is written; kept for the convention

# ---- _cut_sentence ----------------------------------------------------------------------------
txt = ("The fire burned low in the hearth tonight. I watched it for a long while and thought of the "
       "winter ahead, of the knot I could not undo, and of everything that had to be carried across")
c = se._cut_sentence(txt, 60)
assert c == "The fire burned low in the hearth tonight.", c
c2 = se._cut_sentence(txt, 120)                       # no sentence end past 40%: falls back to a word boundary
assert txt.startswith(c2) and not c2.endswith(" ") and txt[len(c2)] == " ", repr(c2)
assert se._cut_sentence("short one.", 300) == "short one."
assert se._cut_sentence("", 10) == ""
assert se._cut_sentence('She said "stay." Then the rest went on and on and on', 20) in ('She said "stay."',), \
    se._cut_sentence('She said "stay." Then the rest went on and on and on', 20)
print("cut ok")

# ---- write_tablet with a stub model + stub store -----------------------------------------------
calls, stored = [], []
async def fake_call(base_urls, system_prompt, user_prompt, **kw):
    calls.append((system_prompt, user_prompt, kw))
    return {"tablet": "The star is a light I walk toward now."}
se.call_node_json = fake_call
se.memory_store.store_symbol_tablet = lambda sym, tab, drift: stored.append((sym, tab, drift)) or "id"

class St:   # the current exchange is already the last conversation_history entry when write_tablet runs
    conversation_history = [{"human": "hello", "entity": "An earlier answer about the harbour."},
                            {"human": "and now?", "entity": "The star above the roof stood very clear tonight."}]
eng = se.SymbolEvolutionEngine()
ctx = "The star above the roof stood very clear tonight."
DRIFT = 0.4137

# (a) a previous tablet exists: it is the model's "before"
se.memory_store.get_symbol_tablets = lambda sym, limit=1: [{"tablet": "The star once marked the edge of my map.", "created": se._LEGACY_TABLET_CUTOFF_TS + 60}]
asyncio.run(eng.write_tablet(St, "star", DRIFT, ctx))
sysp, usr, kw = calls[-1]
assert "The star once marked the edge of my map." in usr, usr
assert "What you wrote of it before" in usr
assert "what the earlier chronicle says it carried" in sysp
assert stored[-1] == ("star", "The star is a light I walk toward now.", DRIFT)     # drift still STORED
# (b) no drift digits, no "from where it began", no duplicate "Recent voice"
for bad in ("0.41", "4137", "distance", "from where it began", "Recent voice", "drift"):
    assert bad not in usr and bad not in sysp, bad
assert not re.search(r"\d\.\d\d", usr), usr
assert usr.count("The star above the roof stood very clear tonight.") == 1, usr    # said once, not twice
assert "An earlier answer about the harbour." not in usr
# (c) first chronicle: no "once"/"used to"/"over time"/"changed" promise to the model
se.memory_store.get_symbol_tablets = lambda sym, limit=1: []
asyncio.run(eng.write_tablet(St, "star", DRIFT, ctx))
sysp, usr, kw = calls[-1]
low = (sysp + usr).lower()
for bad in ("once", "used to", "changed", "shifted", "over time", "drifted", "what you wrote of it before",
            "0.41", "recent voice"):
    assert bad not in low, bad
assert "first chronicle" in sysp and "carries for you now" in sysp
assert kw["max_tokens"] == 160 and kw["temperature"] == 0.7
# (d) a store fault on the lookup degrades to the first-chronicle prompt, never raises
def boom(sym, limit=1): raise RuntimeError("db locked")
se.memory_store.get_symbol_tablets = boom
n = len(calls)
asyncio.run(eng.write_tablet(St, "star", DRIFT, ctx))
assert len(calls) == n + 1 and "first chronicle" in calls[-1][0]
# (e) a long context is cut on a sentence boundary
long_ctx = ("A " + "word " * 10 + "ended here. ") * 12
se.memory_store.get_symbol_tablets = lambda sym, limit=1: []
asyncio.run(eng.write_tablet(St, "star", DRIFT, long_ctx))
surfaced = calls[-1][1].split('How it surfaced just now:\n  "')[1].split('"\n')[0]
assert surfaced.endswith("ended here.") and len(surfaced) <= 300, surfaced[-40:]
print("write_tablet ok")

# ---- observe passes a sentence-cut context ------------------------------------------------------
se._embed = lambda t: np.ones(4, dtype=float)
cent = {"v": (np.array([1.0, 0, 0, 0]), 10, 0.0)}
se.memory_store.get_symbol_centroid = lambda s: cent["v"]
se.memory_store.update_symbol_centroid = lambda *a, **k: None
se._embed = lambda t: np.array([0.0, 1.0, 0, 0])      # orthogonal => drift 1.0 >= threshold
class S2:
    perception = None; raw_input = ""; conversation_history = []
out = ("The star hung over the roof. " * 20).strip()
from core import symbol_window_shadow as _sw   # stubbed: the shadow metric loads a real embedder and logs
_sw.observe_shadow = lambda *a, **k: None
w = eng.observe(S2, out, [{"symbol": "star", "primed": False}])
assert len(w) == 1 and w[0]["context"].endswith("roof.") and len(w[0]["context"]) <= 400, w
print("observe ok")

# ---- founder law: the read-back note is unchanged, nothing added to it --------------------------
src = (ROOT / "core" / "symbol_evolution.py").read_text(encoding="utf-8")
assert 'return (f"A meaning that has shifted for you — on \'{sym}\': \\"{tablet}\\" "\n' in src
assert 'f"You may let it inform you, or let it lie.")' in src
assert se.SYMBOL_READBACK is False
print("J-2947 all ok")
