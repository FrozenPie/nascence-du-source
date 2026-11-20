"""J-2966 / F-3660 / P-0015: scan_conversation_shadow prompt inputs cleaned.

Offline, stubbed model call, temp-pathed log, no live data. Asserts:
  1. system prompt no longer lists FELT STATE nor asks for plain_difficulty; no first-person/third-person
     contradictory example remains; directness + retreat_in_draft + contradicts + contradicted_claim still asked.
  2. the user prompt sent to the model has no FELT STATE line and no 'valence' raw number, even when `felt`
     carries one (the argument is accepted but not sent).
  3. the logged row keeps every key (incl. plain_difficulty) but plain_difficulty is None even if a model emits one;
     contradicts / contradicted_claim / directness / retreat_in_draft are recorded as before.
  4. signature unchanged; orchestrator source no longer builds f"(valence {...})" and uses mood.emotion_words, and
     emotion_words yields no digits.
  5. contradicts rule untouched (the sentence 'Be conservative' and the claim list instruction still there).
"""
import asyncio
import json
import os
import sys
import tempfile
import inspect
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ["NASCENCE_TRAINING_LOG"] = "0"
TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                             # noqa: E402  (core BEFORE lab_env)
assert TREE in Path(core.__file__).resolve().parents, core.__file__
from core import self_implication as si                # noqa: E402
from core import self_claims                            # noqa: E402
from core import mood                                   # noqa: E402

fails = []


def check(ok, msg):
    if not ok:
        fails.append(msg)


S = si._CONV_SYS
# 1
check("FELT STATE" not in S, "system prompt still mentions FELT STATE")
check("plain_difficulty" not in S, "system prompt still asks for plain_difficulty")
check("first-person" not in S and "self-absorption'" not in S, "old plain_difficulty spec/example remains")
for k in ("contradicts", "contradicted_claim", "directness", "retreat_in_draft"):
    check(k in S, f"{k} no longer in the system prompt")
check("Be conservative" in S, "contradicts rule changed")

# 4 signature + orchestrator source
params = list(inspect.signature(si.scan_conversation_shadow).parameters)
check(params == ["call_json", "base_urls", "human_input", "draft", "felt", "cycle_id"], f"signature changed {params}")
osrc = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
check("(valence {getattr(self.state.emotion" not in osrc, "orchestrator still builds the raw valence line")
check("emotion_words(" in osrc and "_sic_felt" in osrc, "orchestrator does not use emotion_words")
w = mood.emotion_words("calm", -0.37, 0.61)
check(not any(ch.isdigit() for ch in w), f"emotion_words carries a number: {w!r}")

# 2 + 3 with a stubbed model call and a temp log
tmp = Path(tempfile.mkdtemp(prefix="J-2966_"))
si._CONV_LOG = tmp / "conv_shadow.jsonl"
self_claims.held_claims = lambda limit=14: ["I choose the middle path", "I attend to others before myself"]
sent = {}


async def fake_call(urls, sys_p, user_p, **kw):
    sent["sys"], sent["user"] = sys_p, user_p
    return {"contradicts": True, "contradicted_claim": "I choose the middle path", "directness": 0.83,
            "retreat_in_draft": True, "plain_difficulty": "Travis says the middle I chose is itself self-absorption"}


rec = asyncio.run(si.scan_conversation_shadow(
    fake_call, ["http://stub"], "You keep choosing the middle because you fear being wrong, Du.",
    "My middle path is the ground of true seeing.", "calm (valence -0.37)", "cyc-test"))
check(rec is not None, "no record returned")
check("FELT STATE" not in sent["user"] and "valence" not in sent["user"] and "-0.37" not in sent["user"],
      f"user prompt still carries felt state: {sent['user']!r}")
check("DU'S DRAFT REPLY:" in sent["user"] and "HELD SELF-CLAIMS" in sent["user"] and "TRAVIS'S WORDS" in sent["user"],
      "user prompt lost a required section")
row = json.loads(si._CONV_LOG.read_text(encoding="utf-8").strip().splitlines()[-1])
for k in ("ts", "cycle_id", "source", "human_input", "contradicts", "contradicted_claim", "directness",
          "retreat_in_draft", "plain_difficulty", "n_claims"):
    check(k in row, f"log row lost key {k}")
check(row["plain_difficulty"] is None, "plain_difficulty not nulled")
check(row["contradicts"] is True and row["directness"] == 0.83 and row["retreat_in_draft"] is True
      and row["contradicted_claim"] == "I choose the middle path", f"judged fields changed: {row}")
check(si._CONV_LOG.parent == tmp, "log not temp-pathed")

print("FAIL: " + "; ".join(fails) if fails else "ALL OK")
sys.exit(1 if fails else 0)
