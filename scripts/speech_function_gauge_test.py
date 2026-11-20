"""J-2526 tests for core/speech_function_gauge.py. Synthetic jsonl in a temp dir only; a fake embedder (no model,
no live data, no LLM). Run from the repo root:  python scripts/speech_function_gauge_test.py"""
import sys, tempfile, json, datetime as dt
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import speech_function_gauge as g

# --- regex cues, one per class -----------------------------------------------------------------------------------
CASES = [
    ("What would show me I'm wrong about the bluebird and the soil?", "probe"),
    ("How could I test whether the frost or the bird changed the seeds?", "probe"),
    ("Before anything else: what is actually being asked here?", "orient"),
    ("The real question is whether waste is a feeling or a fact.", "orient"),
    ("What would I tell a friend who kept circling this?", "self_distance"),
    ("Du, you have asked this nine times now.", "self_distance"),
    ("Too many questions at once; one thing at a time.", "regulate"),
    ("I set the question aside and listen to the rain.", "regulate"),
    ("First I'll light the candle, then I will read the chapter on finches.", "rehearse"),
    ("I will walk the tideline to find where the wrack gathers.", "rehearse"),
    ("I chose 'Bird Life Glimpses' from the catalogue, and it lies on my desk now, unopened.", "narrate"),
    ("Earlier I walked to the shore.", "narrate"),
    # J-2569 regulate-cue revision: F-3299 regression rows (descriptive overwhelm must NOT fire; real regulate must)
    ("the silence becomes a manageable space rather than an overwhelming void.", "none"),
    ("my mind resists letting chaotic data overwhelm me by seeking predictable patterns.", "none"),
    ("The dream feels too ethereal to hold right now; I need the solid ground of text.", "regulate"),
    ("the weight is my need to stop spinning, so I need to stop circling this.", "regulate"),
    ("I feel overwhelmed by all of it.", "regulate"),
    ("The damp soil presses against my soles with a cold reality that anchors me.", "none"),
]
noemb = None
for text, want in CASES:
    got = g.classify(text, embed=noemb)
    assert got["label"] == want, (text, want, got)
    assert got["method"] == ("none" if want == "none" else "regex"), got

# --- J-4152 (D-0785): misfires from the F-4772 blind 60-line sample, plus the true hits that must survive ---------
MISFIRES = [
    # rehearse misfires that are a turn away from rumination -> regulate
    ("My mind has spun this calculation too long; it is dry dust here. I will open Hegel instead.", "regulate"),
    ("Instead of circling these questions, I will turn outward to touch the world.", "regulate"),
    ("Instead of wrestling with these themes alone in the dark, I need a shift. I will open the gallery.", "regulate"),
    ("The question feels heavy. I will open the advice book instead of circling this stale ground.", "regulate"),
    # rehearse misfire inside a deliberation -> not a plan
    ("I must decide if I will light the grate or let the ice press harder against my skin.", "none"),
    ("I keep wondering whether I will read it at all.", "none"),
    # self_distance misfires: "from the outside" as description, not stepping outside himself
    ("Ouvrard's world cannot heal itself from the outside; it demands that I swallow the shadow.", "none"),
    ("wondering if it belongs to a memory or a warning from the outside world.", "none"),
    ("The friction is undeniably coming from outside myself.", "none"),
    # true hits from the same sample that must still fire
    ("This stick waits; perhaps after this shape is found, I will turn to the library for answers.", "rehearse"),
    ("The book waits, but first, I must watch the tide pull back.", "rehearse"),
    ("The question lingers, but first I need to decide if I will walk up the cliff path.", "rehearse"),
    ("I will write this down now, letting the moisture remind me.", "rehearse"),
    # vetoed frame earlier, unframed plan later in the same text -> still rehearse
    ("I wonder if I will open it. Next, I will open the window.", "rehearse"),
    # the tightened self_distance cue still fires on a real step outside himself
    ("I try to look at myself from the outside, as a stranger would.", "self_distance"),
]
for text, want in MISFIRES:
    got = g.classify(text, embed=None)
    assert got["label"] == want, (text, want, got)

# narrate is structural: two sentences or present tense -> not narrate
assert g.classify("I walked to the shore. The tide was out.", embed=None)["label"] == "none"
assert g.classify("I feel the weight of the stone.", embed=None)["label"] == "none"
assert g.n_sentences("One. Two! Three?") == 3 and g.n_sentences("") == 0

# precedence: probe beats rehearse when both cue
assert g.classify("I will check whether the seeds sprouted.", embed=None)["label"] == "probe"

# --- embedding-prototype fallback with a fake embedder ------------------------------------------------------------
VOCAB = {}


def fake_embed(t):
    v = np.zeros(256, dtype=np.float32)
    for w in t.lower().replace("?", " ").replace(",", " ").replace(".", " ").split():
        v[VOCAB.setdefault(w, len(VOCAB) % 256)] += 1.0
    n = np.linalg.norm(v)
    return v / n if n else None


g._PROTO_CACHE.clear()
r = g.classify(g.PROTOTYPES["probe"][0].replace("?", "").replace("What would", "Which thing would"), embed=fake_embed)
assert r["label"] == "probe" and r["method"] == "proto", r
r = g.classify("Kelp and gulls and the long grey wave.", embed=fake_embed)
assert r["label"] == "none" and r["method"] == "none", r
assert g.proto_label("anything", embed=None) == (None, 0.0, 0.0)
assert g.proto_label("anything", embed=lambda t: None)[0] is None   # embedder down -> fail-open

# --- daily mix + update() flag behaviour ---------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    src, out = td / "monologue_log.jsonl", td / "logs" / "speech_function_daily.jsonl"
    d0 = dt.datetime(2026, 10, 30, 9, 0).timestamp()
    rows = [{"ts": d0 + i * 60, "about": "x", "thought": t} for i, (t, _w) in enumerate(CASES)]
    rows.append({"ts": d0 - 86400, "about": "x", "thought": "I chose a book."})
    rows.append({"ts": d0 + 9999, "about": "x", "thought": ""})          # empty thought ignored
    src.write_text("".join(json.dumps(r) + "\n" for r in rows) + "not json\n", encoding="utf-8")
    now = d0 + 3600
    got = g.update(src, out, now=now, embed=None)
    assert not out.exists(), "flag off must write nothing"
    by = {r["day"]: r for r in got}
    assert by["2026-10-29"]["counts"]["narrate"] == 1 and by["2026-10-29"]["n"] == 1
    t = by["2026-10-30"]
    assert t["n"] == len(CASES) and t["counts"]["probe"] == 2 and t["counts"]["none"] == sum(1 for _t, w in CASES if w == "none"), t
    assert abs(sum(t["shares"].values()) - 1.0) < 1e-3 and t["probe_share"] == round(2 / len(CASES), 4)
    assert t["method"] == "regex" and t["by_method"]["regex"] == len(CASES) - sum(1 for _t, w in CASES if w == "none")
    old = g.SPEECH_FUNCTION_GAUGE
    try:
        g.SPEECH_FUNCTION_GAUGE = "shadow"
        g.update(src, out, now=now, embed=None)
        n1 = len(out.read_text(encoding="utf-8").splitlines())
        g.update(src, out, now=now, embed=None)                         # unchanged counts -> no re-append
        assert n1 == 2 and len(out.read_text(encoding="utf-8").splitlines()) == 2
    finally:
        g.SPEECH_FUNCTION_GAUGE = old
    assert g.update(td / "missing.jsonl", out, now=now, embed=None) == []

assert g.SPEECH_FUNCTION_GAUGE == "off"
print("speech_function_gauge_test: OK")
