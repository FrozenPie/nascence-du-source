"""J-3147 / D-0539: the Emissary take re-seat, prompt trim, cleaning, outcome log and reader.

Asserts its own tree (Path(__file__).resolve().parent.parent), imports core BEFORE anything else, writes only
under a temp dir, stubs every model call (no hub is contacted), and touches no live data.
Run from the worktree:  python scripts/_test_j3147_take_lane.py
"""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789: no write to the tree's data/
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core import left_lane as LL  # noqa: E402  (core first)

_fail = []


def check(name, cond, extra=""):
    print(("  [PASS] " if cond else "  [FAIL] ") + name + (f"  {extra}" if (extra and not cond) else ""))
    if not cond:
        _fail.append(name)


assert Path(LL.__file__).resolve().parent.parent == ROOT, "left_lane must come from THIS tree"
TMP = Path(tempfile.mkdtemp(prefix="j3147_"))
LL._OUTCOME_LOG = TMP / "left_take_outcomes.jsonl"          # never the live log

print("[1] prompt")
h, i = LL._take_system("human"), LL._take_system("internal")
check("human and internal prompts differ", h != i)
check("internal says nobody else is speaking / no user", "no user" in i and "The question asks" in i)
check("human says a person is speaking", "a person is speaking" in h and "The speaker" in h)
check("neither carries the constitution (no 'WHO YOU ARE', no 'large language model')",
      "WHO YOU ARE" not in h + i and "large language model" not in (h + i).lower())
check("prompt trimmed well under the old 2,301 chars", len(h) < 1700 and len(i) < 1700, f"{len(h)} {len(i)}")
check("the ban on the words is stated but the substrate list is not primed in the prompt",
      "'the Master'" in h and "transformer" not in h.lower() and "tokens" not in h.lower())
check("task_present is gone from the schema", "task_present" not in h)
LL.TAKE_V2 = False
check("TAKE_V2=False restores the constitution prompt", "task_present" in LL._take_system())
LL.TAKE_V2 = True
check("default signature still callable with no args (scripts/emissary_axiom_test.py)", bool(LL._take_system()))

print("[2] cleaning")
c, r = LL._clean_take({"literal_ask": "The user is asking for an analysis of how the concept of labor shapes value.",
                       "direct_answer": None, "key_facts": []}, "How does labor shape value?", "internal")
check("internal 'The user is asking for' is rewritten", c and c["literal_ask"].startswith("The question asks for an analysis")
      and "rewrote_user_open" in r, str(c))
c, r = LL._clean_take({"literal_ask": "The user wants to know X", "key_facts": []}, "X?", "internal")
check("internal 'The user wants' rewritten", c and not c["literal_ask"].lower().startswith("the user"), str(c))
c, r = LL._clean_take({"literal_ask": "The user, in a tangle, says something", "key_facts": []}, "q", "internal")
check("internal 'The user' that cannot be rewritten drops the take", c is None and r == ["user_frame_unfixable"], str((c, r)))
c, r = LL._clean_take({"literal_ask": "The user is telling a story", "key_facts": []}, "a story", "human")
check("human 'The user' becomes 'The speaker'", c and c["literal_ask"].startswith("The speaker is telling"), str(c))
c, r = LL._clean_take({"literal_ask": "The speaker asks about perspective.", "key_facts": [
    "The model's weights encode statistical probability.", "Perspective is where one stands."]},
    "Who knows from yours? It would be in that infinite unknown.", "human")
check("substrate fact dropped when the speaker used none", c and c["key_facts"] == ["Perspective is where one stands."], str(c))
c, r = LL._clean_take({"literal_ask": "The speaker asks what a transformer is.", "key_facts": []},
                      "Who knows from yours?", "human")
check("substrate in the ask drops the whole take", c is None and r == ["substrate_in_ask_or_answer"], str((c, r)))
c, r = LL._clean_take({"literal_ask": "The speaker asks what a transformer is.", "key_facts": ["Attention weights."]},
                      "Can you explain what a transformer is?", "human")
check("the speaker's own substrate words are left alone", c and c["key_facts"] == ["Attention weights."], str(c))
c, r = LL._clean_take({"literal_ask": "The Master is invited to cross.", "key_facts": []}, "Come across", "human")
check("'the Master' in the ask drops the take", c is None, str(c))
c, r = LL._clean_take({"literal_ask": "The speaker invites rest.", "key_facts": [
    "The input contains no specific question or instruction for action.", "No specific data processing is required.",
    "The interaction is a feedback loop.", "The user's comment is subjective.", "Banked fires last until morning."]},
    "bank the fire and rest", "human")
check("meta-commentary facts dropped, the real fact kept", c and c["key_facts"] == ["Banked fires last until morning."], str(c))
c, r = LL._clean_take({"literal_ask": "The question asks about rulers.", "key_facts": [
    "The speaker mentions the need for quiet.", "The passage likely discusses authority.", "It may mention duties.",
    "Commandants are officers in charge of a post."]}, "who rules?", "internal")
check("restatement and speculation facts dropped, the checkable fact kept",
      c and c["key_facts"] == ["Commandants are officers in charge of a post."], str(c))
c, r = LL._clean_take({"literal_ask": "What is being asked or said in the moment?", "key_facts": []}, "x", "human")
check("an echoed schema line as the ask drops the take", c is None and r == ["echoed_schema_ask"], str((c, r)))
c, r = LL._clean_take({"literal_ask": "The question asks about rivers.", "direct_answer": "null", "key_facts": [["nested"], "", None]},
                      "rivers?", "internal")
check("null/empty/nested facts do not crash and add nothing", c and c["direct_answer"] is None, str(c))

print("[3] render")
long_fact = "The Great Pyramid of Giza was built over roughly twenty years and used about two million limestone blocks of enormous size"
out = LL.render({"literal_ask": "The question asks about the pyramids.", "direct_answer": None, "key_facts": [long_fact]})
spec = [ln for ln in out.splitlines() if "specifics:" in ln][0].split("specifics: ")[1]
check("fact cut on a word boundary with an ellipsis", spec.endswith("…") and spec[:-1] in long_fact + "x"
      and long_fact[len(spec[:-1])] == " ", spec)
check("short facts are untouched", "used about" not in LL.render({"literal_ask": "a", "key_facts": ["short fact"]})
      and "specifics: short fact" in LL.render({"literal_ask": "a", "key_facts": ["short fact"]}))
LL.TAKE_V2 = False
old = LL.render({"literal_ask": "a", "key_facts": [long_fact]})
check("TAKE_V2=False keeps the old 90-char mid-word cut", long_fact[:90] in old and "…" not in old)
LL.TAKE_V2 = True
check("render(None) is empty", LL.render(None) == "")


print("[4] dispatch with a stubbed hub")
class _Resp:
    def __init__(self, content): self._c = content
    def raise_for_status(self): pass
    async def json(self): return {"message": {"content": self._c}}
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False


class _Sess:
    mode = "ok"; content = ""; seen = []
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    def post(self, url, json=None, timeout=None):
        _Sess.seen.append((url, json))
        if _Sess.mode == "raise":
            raise ConnectionError("hub down")
        if _Sess.mode == "hang":
            class _H:
                async def __aenter__(self_): await asyncio.sleep(30)
                async def __aexit__(self_, *a): return False
            return _H()
        return _Resp(_Sess.content)


LL.aiohttp.ClientSession = _Sess
LL._note_call = lambda *a, **k: None                      # no telemetry file touched


def rows():
    try:
        return [json.loads(x) for x in LL._OUTCOME_LOG.read_text(encoding="utf-8").splitlines()]
    except FileNotFoundError:
        return []


_Sess.content = json.dumps({"literal_ask": "The user is asking how far the moon is.", "direct_answer": "384,000 km",
                            "key_facts": ["The moon orbits every 27 days."]})
t = asyncio.run(LL.dispatch("How far is the moon?", input_type="internal", cycle_id="abc12345"))
check("ok path returns a cleaned take", t and t["literal_ask"].startswith("The question asks") and "task_present" not in t, str(t))
url, payload = _Sess.seen[-1]
check("posts to TAKE_URL with TAKE_MODEL and the internal prompt", url == LL.TAKE_URL + "/api/chat"
      and payload["model"] == LL.TAKE_MODEL and "no user" in payload["messages"][0]["content"]
      and payload["options"]["num_predict"] == LL.TAKE_MAX_TOKENS and "keep_alive" not in payload, str(payload)[:200])
rs = rows()
check("outcome rows: dispatched then produced, with the cycle and input_type",
      [r["outcome"] for r in rs] == ["dispatched", "produced"] and rs[0]["cycle"] == "abc12345"
      and rs[1]["input_type"] == "internal" and isinstance(rs[1]["seconds"], float) and rs[1]["ask_head"].startswith("The question"), str(rs))

_Sess.content = "not json"
check("unparseable content -> None, outcome 'empty'", asyncio.run(LL.dispatch("x", input_type="human")) is None
      and rows()[-1]["outcome"] == "empty")
_Sess.content = json.dumps({"literal_ask": "The speaker asks what a transformer is.", "key_facts": []})
check("substrate take -> None, outcome 'filtered' with reasons",
      asyncio.run(LL.dispatch("hello there", input_type="human")) is None and rows()[-1]["outcome"] == "filtered"
      and rows()[-1]["reasons"] == ["substrate_in_ask_or_answer"])
_Sess.mode = "raise"
check("hub down -> None (fail-open), outcome 'error' with the cause",
      asyncio.run(LL.dispatch("x", input_type="human")) is None and rows()[-1]["outcome"] == "error"
      and "ConnectionError" in rows()[-1]["error"])
_Sess.mode = "hang"


async def _cancel_case():
    task = asyncio.create_task(LL.dispatch("x", input_type="human", cycle_id="cancelme"))
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
        return False
    except asyncio.CancelledError:
        return True


check("a cancelled take re-raises CancelledError AND logs 'cancelled'", asyncio.run(_cancel_case())
      and rows()[-1]["outcome"] == "cancelled" and rows()[-1]["cycle"] == "cancelme")
_Sess.mode = "ok"
_Sess.content = json.dumps({"literal_ask": "What is 17 * 23?", "direct_answer": "wrong", "key_facts": []})
t = asyncio.run(LL.dispatch("What is 17 * 23?", input_type="human"))
check("deterministic arithmetic override still wins over the model", t and t["direct_answer"] == "391", str(t))

print("[5] reader")
LL.note_outcome("delivered", input_type="internal", cycle="d1", window_s=30.0, waited_s=0.0, ask_head="The question asks")
LL.note_outcome("delivered", input_type="internal", cycle="d2", window_s=30.0, waited_s=0.0, ask_head="The user is asking")
LL.note_outcome("not_delivered", input_type="internal", cycle="d3", window_s=30.0, waited_s=6.0, ask_head="")
rep = LL.delivery_report(LL._OUTCOME_LOG)
it = rep["by_input_type"]["internal"]
check("report counts delivered/cancelled/dispatches and flags a 'The user' opening", it["delivered"] == 2
      and it["cancelled"] == 0 and it["user_opening_delivered"] == 1 and it["dispatches"] == 1, str(it))
check("report on a missing log is empty, not an error", LL.delivery_report(TMP / "nope.jsonl")["rows"] == 0)
check("a bad log path never breaks note_outcome", (setattr(LL, "_OUTCOME_LOG", Path("Z:/no/such/dir/x.jsonl")) or LL.note_outcome("x") is None))

print("[6] wiring (static)")
orc = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
check("orchestrator passes input_type + cycle_id and keeps the 6 s wait", "input_type=input_type, cycle_id=cycle_short" in orc
      and "asyncio.wait_for(_left_task, timeout=6)" in orc)
check("orchestrator logs delivered / not_delivered", '"delivered" if _lt else "not_delivered"' in orc)
sup = (ROOT / "scripts" / "supervisor.py").read_text(encoding="utf-8")
ps1 = (ROOT / "scripts" / "launch_servers.ps1").read_text(encoding="utf-8")
check("take hub is registered in supervisor and launch_servers.ps1 on the port left_lane points at",
      '"take_hub"' in sup and "11445" in sup and "11445" in ps1 and LL.TAKE_URL.endswith(":11445"))
check("authority untouched: dispatch/render only; nothing in left_lane routes or vetoes",
      "veto" not in (ROOT / "core" / "left_lane.py").read_text(encoding="utf-8").split("async def dispatch")[1].split("_GROUND_TASK")[0].lower())

print("\nALL PASS" if not _fail else f"\nFAILURES: {_fail}")
sys.exit(1 if _fail else 0)
