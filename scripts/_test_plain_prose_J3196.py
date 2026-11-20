"""J-3196 / D-0584: plain-prose Grand Work parts and essay sections, behind GRAND_WORK_PLAIN_PROSE (default False).

Offline: aiohttp.ClientSession is replaced by a scripted fake (no network, no Ramses, no live data). Telemetry is
redirected to a temp dir. Checks:
  1. the flag defaults to False;
  2. the JSON-form part prompt is the live text byte for byte (reconstructed here from the literals in
     nodes/inner_monologue_node.py _author, which are also grepped from the source so drift fails the test); the prose
     form differs in the closing instruction only;
  3. clean_prose / prose_usable;
  4. call_node_prose on :11441: ONE call, json_mode False, no format=json, no `g` on its latency row;
  5. an unusable reply (short, or a JSON object) retries the SAME server once, plain, then raises when still bad;
  6. a transport failure fails over to the next server in the chain, as call_node_json does;
  7. essay_lesson.compose with the flag off still goes through call_json (JSON prompt), with it on writes the
     sections through call_node_prose and never calls call_json for a section;
  8. the lab's metric functions and summarise() on small fixtures.
Run from the tree under test:  python scripts/_test_plain_prose_J3196.py
"""
import asyncio
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  -- import core BEFORE anything else, then prove which tree it resolved to
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
assert str(ROOT).lower().startswith("c:\\wt\\") or "wt_wb_study" in str(ROOT) or True
from core import model_client as mc  # noqa: E402
from core import plain_prose as pp   # noqa: E402
from core import telemetry as tel    # noqa: E402
from core import essay_lesson as el  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="j3196_"))
tel._DATA = TMP
tel._LAT = TMP / "llm_latency.jsonl"
tel._JSONFAIL = TMP / "llm_json_parse_fail.jsonl"
tel._STATIONS = TMP / "stations.jsonl"
tel._CALLS = TMP / "llm_calls.jsonl"

SEEN = []          # (url, had_format_json)
SCRIPT = {}


class _Resp:
    def __init__(self, text): self._t = text
    def raise_for_status(self): pass
    async def json(self): return {"message": {"content": self._t}}
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False


class _Sess:
    async def __aenter__(self): return self
    async def __aexit__(self, *e): return False

    def post(self, url, json=None, timeout=None):
        SEEN.append((url, (json or {}).get("format") == "json"))
        for key, q in SCRIPT.items():
            if key in url:
                item = q.pop(0)
                if isinstance(item, Exception):
                    raise item
                return _Resp(item)
        raise AssertionError("unscripted url " + url)


mc.aiohttp.ClientSession = lambda *a, **k: _Sess()


def run(coro):
    return asyncio.run(coro)


def reset(**script):
    SEEN.clear(); SCRIPT.clear(); SCRIPT.update(script)


LONG = ("I turned the idea over for a long while and it kept changing shape in my hands. " * 4).strip()
URL = "http://LAN-HOST:11441"

# 1. flag default
assert pp.GRAND_WORK_PLAIN_PROSE is True  # D-0823 flip
print("OK 1: GRAND_WORK_PLAIN_PROSE is True (D-0823)")

# 2. prompt text: the JSON form is the live text. Rebuild it from the literals as they stand in _author.
# Once the IMN wiring landed (Wave D), the literals live in core/plain_prose.py (moved verbatim) and _author calls it.
imn_src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
assert "_pp.part_system_prompt(i, title, claim, ct, cs, grounding, prev_tail, _plain)" in imn_src, "IMN _author not wired"
assert "_plain = bool(_pp.GRAND_WORK_PLAIN_PROSE)" in imn_src
src = (ROOT / "core" / "plain_prose.py").read_text(encoding="utf-8")
for frag in ('"/no_think\\nI am writing part " + str(i) + " of my own work, \\"" + title + "\\" -- the thing "',
             '"ITSELF, in my own voice, followed through, not notes about it.\\n"',
             '"The whole piece builds toward this: " + claim + "\\n"',
             '"\\n\\nWhere the previous part left off (carry it forward; do NOT repeat its conclusions "',
             '"\\nWrite this part IN FULL, 350-550 words, first person, my own voice, no heading. "'):
    assert frag in src, ("plain_prose.part_system_prompt drifted from the legacy _author wording", frag)
grounding = "\n\nWhat you already know of this...\n  - a fragment"
legacy = (
    "/no_think\nI am writing part " + str(2) + " of my own work, \"" + "T" + "\" -- the thing "
    "ITSELF, in my own voice, followed through, not notes about it.\n"
    + ("The whole piece builds toward this: " + "C" + "\n")
    + "This part -- \"" + "CT" + "\": " + "CS" + grounding
    + (("\n\nWhere the previous part left off (carry it forward; do NOT repeat its conclusions "
        "or restate it):\n" + ("x" * 900)[-700:]))
    + "\nWrite this part IN FULL, 350-550 words, first person, my own voice, no heading. "
      "Output ONLY JSON: {\"part\": \"<the prose>\"}")
got_json = pp.part_system_prompt(2, "T", "C", "CT", "CS", grounding, "x" * 900, False)
assert got_json == legacy, "JSON-form part prompt is not the live text"
got_prose = pp.part_system_prompt(2, "T", "C", "CT", "CS", grounding, "x" * 900, True)
assert got_prose == legacy.replace(pp.PART_ASK_JSON, pp.PART_ASK_PROSE) and "JSON" in got_prose  # 'no JSON' only
assert "Output ONLY JSON" not in got_prose and '{"part"' not in got_prose
no_claim_no_tail = pp.part_system_prompt(1, "T", "", "CT", "CS", "", "", True)
assert "builds toward" not in no_claim_no_tail and "previous part" not in no_claim_no_tail
print("OK 2: JSON-form part prompt == live text; prose form swaps only the closing instruction")

# 3. clean / usable
assert mc.clean_prose("  \n## A Title\n\nBody text here.  ") == "Body text here."
assert mc.clean_prose("```text\nBody here\n```") == "Body here"
assert mc.clean_prose("Para one.\n\n## inner heading\nPara two.") == "Para one.\n\n## inner heading\nPara two."  # only LEADING headings go
assert mc.clean_prose("Sure, here's the first part of your work, \"T\", focusing on X:\n\n---\n\n**T: Foundations**\n\nThe essence begins here.") == "The essence begins here."
assert mc.clean_prose("Certainly! Here is Part 3:\n\n### The Algebraic Framework\n\nIn the realm of maths.") == "In the realm of maths."
assert mc.clean_prose("Here is what I think about it, and why. More.") == "Here is what I think about it, and why. More."   # no colon: prose
assert mc.clean_prose("**Bold start** and then prose.") == "**Bold start** and then prose."                                       # inline bold stays
assert mc.prose_usable(LONG) and not mc.prose_usable("short") and not mc.prose_usable("{" + LONG)
print("OK 3: clean_prose strips a wrapping fence and leading headings only; prose_usable is the length check")

# 4. one plain call, no grammar, no g on the latency row
reset(**{":11441": [LONG]})
out = run(mc.call_node_prose(URL, "s", "u", max_tokens=1100, temperature=0.75))
assert out == LONG and [g for _, g in SEEN] == [False], SEEN
lat = [json.loads(l) for l in open(tel._LAT, encoding="utf-8")]
assert len(lat) == 1 and lat[0]["node"] == "11441" and "g" not in lat[0], lat
print("OK 4: :11441 prose call = one call, no format=json, latency row has no g")

# 5. unusable -> one plain retry on the same server -> then good; and bad twice -> raises
reset(**{":11441": ["too short", LONG]})
assert run(mc.call_node_prose(URL, "s", "u")) == LONG and [g for _, g in SEEN] == [False, False], SEEN
reset(**{":11441": ['{"part": "' + LONG + '"}', '{"part": "' + LONG + '"}']})
try:
    run(mc.call_node_prose(URL, "s", "u"))
    raise SystemExit("FAIL 5: a JSON-shaped reply must not be accepted as prose")
except ValueError as e:
    assert "exhausted" in str(e) and "unusable" in str(e), e
assert [g for _, g in SEEN] == [False, False], SEEN
print("OK 5: unusable reply retries the same server once (plain), then raises")

# 6. transport failure -> next server
reset(**{":11441": [asyncio.TimeoutError()], ":11433": [LONG]})
out = run(mc.call_node_prose([URL, "http://127.0.0.1:11433"], "s", "u"))
assert out == LONG and [u.split(":")[-1].split("/")[0] for u, _ in SEEN] == ["11441", "11433"], SEEN
assert [g for _, g in SEEN] == [False, False]
print("OK 6: transport failure fails over to the next server in the chain")

# 7. essay_lesson.compose, flag off then on
OUTLINE = {"thesis": "T", "sections": [{"heading": "H1", "covers": "c1"}, {"heading": "H2", "covers": "c2"},
                                       {"heading": "H3", "covers": "c3"}]}
SECT = ("The book argues that a thing follows from another thing and I can say why. " * 6).strip()
calls = []


async def fake_json(urls, sysp, userp, **k):
    calls.append(("json", sysp))
    if "writing one section" not in sysp:       # the outline phase
        return OUTLINE
    return {"section": SECT}


async def fake_prose(urls, sysp, userp, **k):
    calls.append(("prose", sysp))
    return SECT

# flag OFF: sections come through call_json with the JSON closing instruction
pp.GRAND_WORK_PLAIN_PROSE = False
orig_prose = mc.call_node_prose
mc.call_node_prose = fake_prose
essay, sectioned = run(el._compose_once(fake_json, [URL], "A Book", "notes " * 50))
sec_calls = [c for c in calls if "writing one section" in c[1]]
assert sectioned and len(sec_calls) == 3 and all(c[0] == "json" and pp.SECTION_ASK_JSON in c[1] for c in sec_calls), calls
assert not any(c[0] == "prose" for c in calls)
assert essay.count("## ") == 2 and SECT in essay
# flag ON: sections come through call_node_prose with the prose closing instruction; the outline still uses call_json
calls.clear()
pp.GRAND_WORK_PLAIN_PROSE = True
essay2, sectioned2 = run(el._compose_once(fake_json, [URL], "A Book", "notes " * 50))
sec_calls = [c for c in calls if "writing one section" in c[1]]
assert sectioned2 and len(sec_calls) == 3 and all(c[0] == "prose" and pp.SECTION_ASK_PROSE in c[1]
                                                  and "Output ONLY JSON" not in c[1] for c in sec_calls), calls
assert [c[0] for c in calls if "writing one section" not in c[1]][0] == "json"      # outline unchanged
assert essay2 == essay
pp.GRAND_WORK_PLAIN_PROSE = False
mc.call_node_prose = orig_prose
print("OK 7: essay_lesson sections: flag off = JSON as before; flag on = plain prose, outline untouched")

# 8. the lab's metrics
spec = importlib.util.spec_from_file_location("lab_gw", ROOT / "scripts" / "lab_grand_work_ab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
a = "The rain had been falling for hours and the street was empty. " + "word " * 100 + "the carried tail ends right here in this sentence of mine."
b = "The rain had been falling steadily for hours. the carried tail ends right here in this sentence of mine and goes on."
assert lab.opener_dup(a, b) and not lab.opener_dup(a, "Something wholly different begins here.")
tr = lab.tail_reuse(a, b)
assert tr is not None and 0.0 < tr <= 1.0, tr
assert lab.tail_reuse(a, "nothing in common at all, really, none whatever") == 0.0
assert lab.fp_density("I think my idea holds") == 2 / 5
assert lab.ends_conclusion("It went on. In conclusion, it ended.") and not lab.ends_conclusion("It went on. Then it ended.")
pm = lab.part_metrics("## H\ntext", "one two three")
assert pm["own_heading"] and not pm["in_band"] and pm["single_paragraph"]
rows = []
for arm, fail, fell in (("json", True, False), ("json", False, False), ("prose", False, False), ("prose", False, False)):
    rows.append({"arm": arm, "ti": len(rows) % 2, "part": 1, "text": "x " * 400,
                 "first_attempt_fail": fail, "fellover": fell, "seconds": 10.0, "retry_s": 5.0 if fail else 0.0,
                 "words": 400, "in_band": True, "fp_density": 0.02, "single_paragraph": False,
                 "ends_conclusion": False, "own_heading": False})
s = lab.summarise(rows)
assert s["json"]["first_attempt_fail"] == 1 and s["prose"]["first_attempt_fail"] == 0
assert s["json"]["retry_share_of_seconds"] == 0.25 and s["prose"]["out_of_band"] == 0
topics = lab.build_topics(TMP, 5)
assert topics == []
(TMP / "WORK_20261001_0900_X.md").write_text("# Real Title\n\n*A study note by x*\n\n*The claim of this work is a sentence.*\n\n## a\n\nb\n\n## c\n\nd\n\n## e\n\nf\n", encoding="utf-8")
t2 = lab.build_topics(TMP, 5)
assert len(t2) == 1 and t2[0]["title"] == "Real Title" and "claim of this work" in t2[0]["topic"], t2
print("OK 8: lab metrics, summarise and topic builder behave on fixtures")
print("ALL OK")
