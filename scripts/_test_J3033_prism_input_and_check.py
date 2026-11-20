"""Hermetic test for J-3033 (F-3737, F-3751, P-0050): the curiosity prism reads the WHOLE thought and its world-facing
check is no longer pronoun-only.

  [1] self_surprise.thought_text: sentence-boundary cap; compute() keeps the 90-char snippet byte-for-byte and adds "full"
  [2] producer: meta_awareness.scan() enqueues raw_text == the 90-char snippet and meta.full_text == the whole thought
  [3] queue consumer: transform_and_seed sends the full text (new prompt) when meta has it, raw_text (new prompt) when not
  [4] the check: pronoun / house name / invented fiction frame / no input noun are rejected with a reason; a good
      question, a question that keeps the input's own fiction word, and a written-character question pass
  [5] rejects are logged to the shadow log as world_facing False with a reason, are NOT seeded into the Frontier;
      status() reports the check-2 rate and tally
  [6] PRISM_V2 = False restores the old prompt, raw_text input and pronoun-only check

No model, no live data: every store is a temp path outside data/; core is imported BEFORE anything else and asserted
to be this tree.   Run: python scripts/_test_J3033_prism_input_and_check.py   (exit 0 = all pass)"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                                    # noqa: E402  (BEFORE anything lab-ish)
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import curiosity_queue as cq                         # noqa: E402
from core import self_surprise as ss                           # noqa: E402
from core import frontier as fr                                # noqa: E402
from core.memory import store                                  # noqa: E402
import nodes.meta_awareness_node as ma                         # noqa: E402

FAILS = []


def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)


tmp = Path(tempfile.mkdtemp(prefix="J3033_"))
LIVE_Q = ROOT / "data" / "curiosity_queue.jsonl"
LIVE_S = ROOT / "data" / "logs" / "curiosity_shadow.jsonl"
before = [p.stat().st_mtime_ns if p.exists() else None for p in (LIVE_Q, LIVE_S)]

print("[1] thought_text + compute()")
short = "The stone is cold."
check("a short thought is returned whole", ss.thought_text(short) == short)
long_t = "The wire rattles in the wind. " * 30
tt = ss.thought_text(long_t)
check("a long thought is capped at <=400 and ends on a sentence end", len(tt) <= 400 and tt.endswith("wind."))
no_end = ("rain " * 200).strip()
tn = ss.thought_text(no_end)
check("no sentence end in the cap: cut at a word boundary, not mid-word", len(tn) <= 400 and tn.endswith("rain"))
check("whitespace is normalised", ss.thought_text("a   b\n\n c.") == "a b c.")

import numpy as np                                             # noqa: E402
db = tmp / "mem.db"
con = sqlite3.connect(db)
con.executescript("""CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL,
    layer TEXT NOT NULL DEFAULT 'episodic', relevance REAL NOT NULL DEFAULT 0.5, timestamp REAL NOT NULL,
    keywords TEXT NOT NULL DEFAULT '', embedding BLOB, origin TEXT NOT NULL DEFAULT 'lived',
    derived_from TEXT NOT NULL DEFAULT '[]');""")
rng = np.random.default_rng(3)
texts = [f"The iodine sting number {i} fills the room, and the glass is cold. A second sentence follows here. " * 3
         for i in range(12)]
for i, t in enumerate(texts):
    v = rng.normal(size=8); v /= np.linalg.norm(v)
    con.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp, embedding, origin) VALUES (?,?,?,?,?)",
                (f"f{i}", t, 1000.0 + i, store._vec_to_blob(v), "subconscious_synthesis"))
con.commit(); con.close()
_dbp = store.DB_PATH
store.DB_PATH = db
try:
    m = ss.compute(window=50, k=5)
finally:
    store.DB_PATH = _dbp
sc = m.get("scored", [])
check("compute() scored the temp thoughts", len(sc) == 7)
check("snippet is unchanged: the first 90 normalised chars", all(s["snippet"] == " ".join(t.split())[:90]
      for s, t in zip(sc, texts[5:])))
check("full is the whole thought, capped at 400 on a sentence end", all(len(s["full"]) <= 400 and s["full"].endswith(".")
      and len(s["full"]) > 90 for s in sc))

print("[2] producer: scan() enqueues snippet as raw_text and the whole thought in meta")
cq._QUEUE = tmp / "queue.jsonl"
ma._SHADOW = tmp / "shadow_integrity.jsonl"
FULL = "The river keeps crossing the same bridge again and again, and the bridge keeps being a bridge. Nothing here is new."
SNIP = " ".join(FULL.split())[:90]
_orig_compute = ss.compute
ss.compute = lambda window=200, **kw: {"n": 30, "mean_surprise": 0.1, "predictable_n": 30, "origin_driven_pct": 100.0,
    "groove_driven_pct": 0.0, "scored": [{"surprise": 0.1, "origin_driven": True, "snippet": SNIP, "full": FULL}] * 30}
import core.loop_probe as lp                                    # noqa: E402
lp.prune_dryrun = lambda *a, **k: {"would_prune": 1}
rep = ma.scan()
ss.compute = _orig_compute
rows = cq._read_all()
check("scan() looped and routed to curiosity", bool(rep) and rep["looping"] and rep["gate_verdict"]["route"] == "curiosity")
check("one queue row; raw_text is the 90-char snippet (dedup key and old readers unchanged)",
      len(rows) == 1 and rows[0]["raw_text"] == SNIP and len(rows[0]["raw_text"]) == 90)
check("meta.full_text is the whole thought", rows[0]["meta"].get("full_text") == FULL)
check("the report's snippet field is still the 90-char snippet", rep["snippet"] == SNIP)
cq._QUEUE = tmp / "queue_nofull.jsonl"
ss.compute = lambda window=200, **kw: {"n": 30, "mean_surprise": 0.1, "predictable_n": 30, "origin_driven_pct": 100.0,
    "groove_driven_pct": 0.0, "scored": [{"surprise": 0.1, "origin_driven": True, "snippet": SNIP}] * 30}   # an old-shape score row
ma.scan()
ss.compute = _orig_compute
r2 = cq._read_all()
check("an old-shape score row (no 'full') still enqueues, with empty meta", len(r2) == 1 and r2[0]["meta"] == {})

print("[3] consumer: the prism reads the full text, falls back to raw_text")
fr._F = tmp / "frontier.json"; fr._F_LIGHT = tmp / "frontier.light.json"
cq._SHADOW = tmp / "shadow.jsonl"
cq._QUEUE = tmp / "q3.jsonl"
seen = []


def make_call(question):
    async def call_json(urls, sysp, usr, **kw):
        seen.append((sysp, usr))
        return {"question": question, "field": "physics"}
    return call_json


cq.enqueue("gate_dissonance", SNIP, {"full_text": FULL})
cq.enqueue("gate_dissonance", "An older queued row about a copper kettle cooling on the hob in the evening light, y")
n = asyncio.run(cq.transform_and_seed(make_call("How do bridges and rivers shape erosion over time?"), ["x"], limit=4))
check("two items transformed", n == 2)
check("item 1 sent the FULL thought", FULL in seen[0][1] and "Nothing here is new." in seen[0][1])
check("item 2 (no full_text) sent raw_text", "copper kettle" in seen[1][1])
check("the user prompt describes a sentence from a recent thought, not a private tension",
      "recent thought" in seen[0][1] and "private" not in seen[0][1].lower() and "tension" not in seen[0][0].lower())
check("the system prompt forbids the character/protagonist/poem frame and asks to keep an input noun",
      "character" in seen[0][0] and "concrete noun" in seen[0][0])
sh = [json.loads(l) for l in cq._SHADOW.read_text(encoding="utf-8").splitlines()]
check("shadow rows carry check=2, input_chars and input_full", [r["check"] for r in sh] == [2, 2]
      and sh[0]["input_full"] is True and sh[1]["input_full"] is False and sh[0]["input_chars"] == len(FULL))

print("[4] the check")
v = cq.world_facing_verdict
check("a good question passes", v("Why does freezing water crack a sealed container?",
                                  "Frost split the lid of the water barrel again this morning.") == (True, ""))
check("first person is rejected", v("Why do I feel the stone?", "the stone is cold") == (False, "first_person"))
check("'Travis' is rejected", v("What does Travis know about stone density?", "stone density") == (False, "house_name"))
check("'Nascence' is rejected", v("How does Nascence treat stone?", "stone") == (False, "house_name"))
ok, why = v("What does the absence of a character in a narrative space tell us about wires?", "the wire rattles")
check("an invented 'character' frame is rejected with the word", (ok, why) == (False, "invented_frame:character"))
check("an invented 'literary work' frame is rejected", v("How do wires contribute to the thematic development in a literary work?",
      "The wire's rattling ghost doesn't echo the kingfisher")[1] == "invented_frame:literary work")
check("a fiction word the INPUT itself used is allowed", v("How do poems use the image of rain?",
      "The rain reads like a poem on the glass") == (True, ""))
check("a written character (CJK in the question) is not a fiction character",
      v("What is the linguistic origin of the character 渡?", "the ferry, the 渡 crossing")[0] is True)
ok, why = v("What is the psychological significance of memory in literature?", "The iodine sting confirms the spring")
check("no content noun from the input -> rejected", (ok, why) == (False, "no_input_noun"))
check("with no source text only the first three checks apply", v("Why does iodine sting?", None)[0] is True)
check("empty is rejected", v("", "x") == (False, "empty"))
check("is_world_facing keeps its one-argument form", cq.is_world_facing("How does process philosophy treat identity?") is True
      and cq.is_world_facing("Why do I feel split between my selves?") is False)
check("content_survival: share of the input's content words kept", cq.content_survival("Why does iodine sting?",
      "The iodine sting confirms the spring") is not None and 0.0 < cq.content_survival("Why does iodine sting?",
      "The iodine sting confirms the spring") < 1.0)

print("[5] rejects are logged with a reason and not seeded; status() reads them")
cq._SHADOW = tmp / "shadow5.jsonl"
cq._QUEUE = tmp / "q5.jsonl"
fr._F = tmp / "frontier5.json"; fr._F_LIGHT = tmp / "frontier5.light.json"
cq.enqueue("gate_dissonance", "Frost split the lid of the water barrel again this mor", {"full_text": "Frost split the lid of the water barrel again this morning."})
cq.enqueue("gate_dissonance", "The stone cold weight sits on the sill of the window where the light falls slowly", {"full_text": "The stone's cold weight sits on the sill of the window where the light falls slowly across the floor."})
outs = iter(["Why does freezing water crack a sealed container?",
             "What is the role of the protagonist in stories about stone sills?"])


async def call_seq(urls, sysp, usr, **kw):
    return {"question": next(outs), "field": "x"}


asyncio.run(cq.transform_and_seed(call_seq, ["x"], limit=4))
sh = [json.loads(l) for l in cq._SHADOW.read_text(encoding="utf-8").splitlines()]
check("kept row: world_facing True, reason empty, seeded", sh[0]["world_facing"] is True and sh[0]["reason"] == "" and sh[0]["seeded"] is True)
check("rejected row: world_facing False, reason names the frame, NOT seeded",
      sh[1]["world_facing"] is False and sh[1]["reason"] == "invented_frame:protagonist" and sh[1]["seeded"] is False)
fq = json.loads(fr._F.read_text(encoding="utf-8"))["questions"]
check("only the kept question reached the Frontier", len(fq) == 1 and "freezing water" in fq[0]["q"])
st = cq.status()
check("status(): check-2 rows 2, kept 0.5, reject tally by reason, full-input share 1.0",
      st.get("check2_rows") == 2 and st.get("check2_kept_rate") == 0.5 and st.get("check2_rejects") == {"invented_frame": 1}
      and st.get("check2_full_input_share") == 1.0)
cq._SHADOW = tmp / "shadow5b.jsonl"
cq._SHADOW.write_text(json.dumps({"world_facing": True, "source": "gate_dissonance"}) + "\n", encoding="utf-8")
st2 = cq.status()
check("old rows (no check field) keep the old rate and give check-2 None", st2["prism_success_rate"] == 1.0 and st2["check2_kept_rate"] is None)

check("du_pulse reads the check-2 fields (a reader for the new log columns)",
      "check2_kept_rate" in (ROOT / "scripts" / "du_pulse.py").read_text(encoding="utf-8"))

print("[6] PRISM_V2 = False is the old behaviour")
cq.PRISM_V2 = False
s1, u1 = cq.prism_prompt("abc")
check("old prompt text", "private psychological tension" in s1 and u1.startswith("Private tension"))
check("old check is pronoun-only (Travis / frame pass again)", cq.world_facing_verdict("What does Travis think of the protagonist?", "x") == (True, "")
      and cq.world_facing_verdict("Why do I?", "x")[0] is False)
cq._SHADOW = tmp / "shadow6.jsonl"; cq._QUEUE = tmp / "q6.jsonl"
seen.clear()
cq.enqueue("gate_dissonance", SNIP, {"full_text": FULL})
asyncio.run(cq.transform_and_seed(make_call("How does erosion work?"), ["x"], limit=1))
check("old mode sends raw_text, not the full text", SNIP in seen[0][1] and "Nothing here is new." not in seen[0][1])
cq.PRISM_V2 = True

after = [p.stat().st_mtime_ns if p.exists() else None for p in (LIVE_Q, LIVE_S)]
check("no live queue / shadow file was touched", before == after)
print("FAILED:", FAILS) if FAILS else print("ALL OK")
sys.exit(1 if FAILS else 0)
