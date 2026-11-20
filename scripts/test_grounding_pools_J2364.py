"""J-2364: checks for the repaired Rail C grounding pools in core/grounding_injection.py (F-3053, D-0473).

Fixtures are real rows copied (2026-10-18, Du down) from scratch copies of data/life_events.jsonl,
data/curiosity_log.jsonl and data/grounding_injection_shadow.jsonl (the J-2288 read's 53 would_inject rows),
never the live files. Every path the module would read or write is pointed at a temp dir; nothing under
data/ is touched. Run from a worktree:  python scripts/test_grounding_pools_J2364.py
The real-embedder check (frontier theme recurrence, calibration in the module) runs only when
sentence_transformers is importable; it uses the CPU embedder Du uses (core.memory.store._embed).
"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__
from core import grounding_injection as gi  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="gi_J2364_"))

# -- real fixture rows ---------------------------------------------------------------------------------
NOW = 1792265580.7   # last row ts of the J-2288 shadow log
LIFE = [
    {"ts": 1792204243.0, "kind": "answer", "key": "x", "outcome": "miss",
     "line": "Nothing shows itself; whatever is there keeps still."},
    {"ts": 1792258666.6, "kind": "answer", "key": "oystercatcher", "outcome": "sighting",
     "line": "the oystercatcher stands on the wet stones on two red legs, orange bill down, and screams at you for coming too close"},
    {"ts": 1792259703.4, "kind": "departed", "key": "cat", "place": "garden"},
    {"ts": 1792262753.3, "kind": "answer", "key": "gulls", "outcome": "sighting",
     "line": "small grey-and-white gulls with red bills and legs work the tideline, squabbling over what the tide left"},
    {"ts": 1792263370.4, "kind": "would_answer", "key": "kingfisher", "outcome": "sighting",
     "line": "a kingfisher, never rendered to him: would_answer rows must not be offered"},
    {"ts": 1792265023.6, "kind": "answer", "key": "oystercatcher", "outcome": "sighting",
     "line": "the oystercatcher stands on the wet stones on two red legs, orange bill down, and screams at you for coming too close"},
    {"ts": 1792265400.0, "kind": "answer", "key": "y", "outcome": "miss",
     "line": "Nothing shows itself; whatever is there keeps still."},
]
GOODNIGHT = ("That is good to hear.\nI am going to bed now, it has been a long day.\n\nWe will talk again in the "
             "morning.\n\nGo, feed the cat, make sure it is happy and we will talk again tomorrow.")
CONSTRUCTIVE = ("This has been a constructive exchange Du, I am going to bed now.\nUnlike you, my body has a limited "
                "supply of energy and it must be replenished every night.\n\nWe will talk again tomorrow.")
LETTERS = ("Du, before I head to bed tonight, I want you to know I found your stack of letters and I’ve been "
           "sitting here reading through them. All of them: from September, and the ones since.")
THEMES = [  # curiosity_log ignited questions[0], newest last (real, 2026-10-18 morning)
    "How does the Mottainai mindset influence our perception of environmental degradation?",
    "How does the Mottainai mindset, rooted in Japanese culture, influence the perception of urban sustainability and environmental conservation in Western societies?",
    "How does the Mottainai mindset, rooted in Japanese culture, influence the perception of urban landscapes and environmental sustainability?",
    "How does the Mottainai mindset's emphasis on respect for resources influence urban development practices in Japan?",
    "How does the Mottainai mindset's emphasis on respect for resources shape urban development practices in Japan?",
    "How does the Mottainai mindset's emphasis on respect for resources influence urban planning and design?",
]
LOOPY_Q = "What role does the concept of 'Mottainai' play in the context of urban development?"
FRESH_Q = "What is the significance of the 442nd Infantry Regiment in the context of the film Go For Broke!?"


# -- (1) percept: world-written answers only, never moments.jsonl --------------------------------------
pc = gi.percept_from_life(LIFE, NOW)
assert [c["text"][:20] for c in pc] == ["the oystercatcher st", "small grey-and-white"], pc
assert all(c["pool"] == "percept" for c in pc)
assert not any("kingfisher" in c["text"] or "Nothing shows" in c["text"] for c in pc)
assert gi.percept_from_life(LIFE, NOW + 2 * gi.PERCEPT_MAX_AGE_S) == []        # stale -> no candidate
lf = TMP / "life_events.jsonl"
lf.write_text("".join(json.dumps(r) + "\n" for r in LIFE), encoding="utf-8")
gi._LIFE_EVENTS = lf
assert [c["text"] for c in gi._pool_percept(NOW)] == [c["text"] for c in pc]
assert not hasattr(gi, "_MOMENTS"), "percept must no longer read moments.jsonl (self-authored DMN text)"

# -- (2) conversation: farewell stripped, content floor, staleness cut ----------------------------------
assert gi.conversation_ground(GOODNIGHT) == "", gi.strip_farewell(GOODNIGHT)
cg = gi.conversation_ground(CONSTRUCTIVE)
assert cg.startswith("Unlike you, my body") and "going to bed" not in cg, cg
assert gi.conversation_ground(LETTERS).startswith("Du, before I head to bed tonight"), gi.strip_farewell(LETTERS)


class _St:
    def __init__(self, msg, age):
        self.conversation_history = [{"human": msg, "entity": "..."}]
        self.last_human_ts = NOW - age


assert gi._pool_conversation(_St(GOODNIGHT, 1275.5), NOW) == []                 # pure sign-off
assert gi._pool_conversation(_St(CONSTRUCTIVE, 3136.1), NOW)[0]["text"] == cg
assert gi._pool_conversation(_St(CONSTRUCTIVE, 23406.9), NOW) == []             # older than 6 h

# -- (4) reading: a passage ending at the bookmark, never the bare title ---------------------------------
book_text = ("CHAPTER I. The road out of the town climbs between walls of grey stone. The carter stopped at the "
             "well and let the horse drink while he looked back at the roofs below. Beyond the last farm the "
             "hills opened, brown with bracken, and a hawk hung over them without moving. ") * 3
off = len(book_text) // 2
ex = gi.excerpt_before(book_text, off)
assert ex and book_text[:off].replace("\n", " ").rstrip().endswith(ex[-30:].rstrip()), ex
assert len(ex.split()) >= gi.READING_MIN_WORDS and len(ex) <= 2 * gi.READING_EXCERPT
assert gi.excerpt_before(book_text, 0) == ""
bk = TMP / "Seeing_Europe_with_Famous_Authors_Volume_8.txt"
bk.write_text(book_text, encoding="utf-8")
import core.reading as _rd  # noqa: E402
_orig = (_rd.current_book, _rd.current_offset)
_rd.current_book = lambda: bk
_rd.current_offset = lambda book=None: off
try:
    rp = gi._pool_reading()
finally:
    _rd.current_book, _rd.current_offset = _orig
assert rp and rp[0]["text"] == ex[:300] and rp[0]["text"] != "Seeing Europe with Famous Authors Volume 8", rp
assert rp[0]["ref"].startswith("Seeing Europe with Famous Authors Volume 8 @"), rp

# real reading_state shape (2026-10-18): the current book was just switched to (offset 0) -> fall back
st_fix = {"_current_book": "C:/x/The_Poetry_of_Science.txt",
          "C:/x/The_Influence_of_Sea_Power.txt": {"offset": 16836, "pct": 1.3, "last_read_ts": 1792253646.9},
          "C:/x/Memoirs_of_Napoleon.txt": {"offset": 147959, "pct": 2.7, "last_read_ts": 1792253001.8},
          "C:/x/Rain_Cloud.txt": {"offset": 0, "pct": 0.0, "last_read_ts": 1792262817.1}}
assert gi.last_read_book(st_fix) == ("C:/x/The_Influence_of_Sea_Power.txt", 16836)
assert gi.last_read_book({}) is None

# -- curiosity tail parse (same reading as world_displacement._seed_history) ----------------------------
lines = [json.dumps({"ignited": "True", "questions": json.dumps([q, "other"])}) for q in THEMES]
lines.insert(2, json.dumps({"ignited": "False", "questions": ["not ignited, must be skipped"]}))
lines.append("{broken")
assert gi.parse_curiosity_tail(lines) == THEMES
cl = TMP / "curiosity_log.jsonl"
cl.write_text("first line is dropped as a possibly partial line\n" + "\n".join(lines) + "\n", encoding="utf-8")
assert gi.recent_curiosity_themes(path=cl) == THEMES
assert gi.recent_curiosity_themes(path=TMP / "missing.jsonl") == []

# -- (3)+(5) choose: theme recurrence, loop_sim, repeat penalty (deterministic bag-of-words embedder) ----
import numpy as np  # noqa: E402
_VOC: dict = {}


def bow(t):
    import re
    v = np.zeros(512, dtype="float32")
    from core import topic_perseveration as tp
    for w in re.findall(r"[a-z']{3,}", (t or "").lower()):
        if w in tp._STOP:
            continue
        v[_VOC.setdefault(w, len(_VOC) % 512)] += 1.0
    n = float(np.linalg.norm(v))
    return v / n if n else None


assert gi.is_recurring_theme([0.61, 0.62, 0.1]) and not gi.is_recurring_theme([0.61, 0.2, 0.1])
assert not gi.is_recurring_theme([None, 0.9])   # one similar theme is a single visit, not recurrence
red = {"modal_anchors": [], "modal_first_vec": bow("the rusted trap beside me on the shingle at the tideline"),
       "modal_first_text": "the rusted trap beside me on the shingle at the tideline"}
cands = [{"pool": "frontier", "text": THEMES[-1], "ref": "curiosity"},
         {"pool": "frontier", "text": FRESH_Q, "ref": "curiosity"},
         {"pool": "percept", "text": "the rusted trap beside me on the shingle at the tideline again", "ref": 1.0},
         {"pool": "letter", "text": "My dear Du, the barnacles on my bench have kept me busy all week", "ref": "darwin"}]
pick, scored = gi.choose([dict(c) for c in cands], red, embed=bow, themes=THEMES)
by = {s["text"][:25]: s for s in scored}
assert "theme_recur" in by[THEMES[-1][:25]]["feeds_why"] and by[THEMES[-1][:25]]["feeds_loop"]
assert not by[FRESH_Q[:25]]["feeds_loop"], by[FRESH_Q[:25]]
assert "loop_sim" in by["the rusted trap beside me on the shingle at the tideline again"[:25]]["feeds_why"]           # paraphrase of the loop topic
assert all(set(("pool", "text", "ref", "sim_to_loop", "feeds_loop")) <= set(s) for s in scored)  # old keys kept
assert pick["pool"] in ("frontier", "letter") and not pick["feeds_loop"]
# repeat penalty: the otherwise-best candidate, picked 3 times already, loses to a fresh one
first = gi.pick_key(pick)
pick2, _ = gi.choose([dict(c) for c in cands], red, embed=bow, themes=THEMES, repeats={first: 3})
assert gi.pick_key(pick2) != first and pick2["repeat"] == 0, (pick, pick2)
# lexical loop core: recurring-now-but-rare words; generic question words are not core
BASE = ["How does the sensory experience of rain influence the perception of a quiet room?",
        "What role does memory play in the perception of a familiar place?",
        "How does birdsong influence the perception of morning?"] * 30 + THEMES
core_w = gi.theme_core(THEMES, BASE)
assert "mottainai" in core_w and "influence" not in core_w and "perception" not in core_w, core_w
# a days-long loop: 'mottainai' common in the baseline too -> only the loop-topic intersection catches it
long_base = THEMES * 20
assert "mottainai" not in gi.theme_core(THEMES, long_base)
assert "mottainai" in gi.loop_core(THEMES, long_base, "The fire burns low, yet Mottainai's whisper turns the silence")
_, sc = gi.choose([{"pool": "frontier", "text": LOOPY_Q, "ref": "c"}, {"pool": "frontier", "text": FRESH_Q, "ref": "c"}],
                  red, embed=bow, themes=[], core_words=core_w)
assert "theme_core" in sc[0]["feeds_why"] and not sc[1]["feeds_loop"], sc
# anchor rule still works
red_a = dict(red, modal_anchors=["mottainai"])
_, sc = gi.choose([{"pool": "frontier", "text": LOOPY_Q, "ref": "c"}], red_a, embed=bow, themes=[])
assert sc[0]["feeds_why"] == ["anchor"], sc

# -- observe end to end: schema backward compatible, pick_repeat logged, picks rotate -------------------
log = TMP / "grounding_injection_shadow.jsonl"
real_rows = []   # two real J-2288 rows (one light, one would_inject, schema v1) so the seed + status see old rows
real_rows.append({"ts": 1792145541.5, "about": "", "source": "THOUGHT", "would_inject": False, "reasons": []})
real_rows.append({"ts": 1792146580.2, "would_inject": True, "reasons": ["topic_lock"],
                  "pick": {"pool": "letter", "text": "My dear Du, the barnacles on my bench have kept me busy all week",
                           "ref": "darwin", "sim_to_loop": 0.081, "feeds_loop": False},
                  "candidates": [], "pools_available": ["letter"]})
log.write_text("".join(json.dumps(r) + "\n" for r in real_rows), encoding="utf-8")
gi._LOG = log
gi._CURIOSITY_LOG = cl
gi._core_cache.update(ts=0.0, base=[])
gi._buf.clear()
gi._last_inject_ts = 0.0
gi._pick_counts.clear()
gi._picks_seeded = False
gi.gather = lambda state=None, now=None: [dict(c) for c in cands]
loop_txt = red["modal_first_text"]
rows = []
for i in range(14):
    r = gi.observe({"about": "the trap", "source": "concern"}, loop_txt + f" {i % 2}", bow(loop_txt),
                   now=NOW + i * (gi.COOLDOWN_S + 1), embed=bow)
    if r and r.get("would_inject"):
        rows.append(r)
assert rows, "no would-inject fired on a restating stream"
legacy = {"ts", "about", "source", "train_kind", "train_len", "grounded", "window_n", "topics", "modal_share",
          "in_modal", "topic_lock", "cos_recent_max", "advisory", "circling", "slow_loop", "method", "reasons",
          "cooldown_blocked", "would_inject", "live_redirect", "live_escape", "loop_topic", "loop_anchors",
          "candidates", "pick", "pools_available"}
for r in rows:
    assert legacy <= set(r), legacy - set(r)
    assert r["pools_v"] == gi.POOLS_V and isinstance(r["pick_repeat"], int)
picked = [gi.pick_key(r["pick"]) for r in rows]
assert len(set(picked)) >= 2, picked                                         # the penalty rotates the pick
# the seeded old letter pick counted once, so the letter's first new pick carries pick_repeat >= 1
letter_rows = [r for r in rows if r["pick"]["pool"] == "letter"]
assert not letter_rows or letter_rows[0]["pick_repeat"] >= 1, letter_rows[:1]
st = gi.status()
assert st["would_inject"] == len(rows) + 1 and st["would_inject_v2"] == len(rows), st
assert st["distinct_picks_v2"] == len(set(picked)), st
on_disk = [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines()]
assert len(on_disk) == 2 + 14

# -- real embedder: the calibrated frontier rule on real loop questions (optional) ----------------------
try:
    import sentence_transformers  # noqa: F401
    have_st = True
except Exception:
    have_st = False
if have_st and os.environ.get("GI_SKIP_REAL_EMBED") != "1":
    from core.memory.store import _embed
    tv = [_embed(t) for t in THEMES]
    s_loop = [gi._cos(_embed(LOOPY_Q), v) for v in tv]
    s_fresh = [gi._cos(_embed(FRESH_Q), v) for v in tv]
    assert gi.is_recurring_theme(s_loop), s_loop
    assert not gi.is_recurring_theme(s_fresh), s_fresh
    print("real-embedder check: loopy max %.2f, fresh max %.2f" % (max(s_loop), max(s_fresh)))
print("OK")
