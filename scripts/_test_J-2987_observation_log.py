"""
J-2987 (F-3687/F-3688, P-0069) -- hermetic test: core/journal.py write_observation logs scene+impulse with the entry,
keeps the impulse out of the user prompt (flag restores it), carries the colour/animal grounding rule, and
scripts/read_journal_observation_log.py measures leak and ungrounded kinds. The model call and store_fragment are
stubbed; the journal dir and log are temp dirs; no hub is touched.

  python scripts/_test_J-2987_observation_log.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  -- before lab_env; must resolve to THIS checkout

assert str(Path(core.__file__).resolve()).startswith(str(ROOT)), "core must come from the tree under test"
from core import journal as jr  # noqa: E402
from core.memory import store as _store  # noqa: E402

FAILS: list = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


tmp = Path(tempfile.mkdtemp(prefix="j2987_"))
jr._JOURNAL_DIR = tmp / "Journal"
jr._OBSERVATION_LOG = tmp / "journal_observation_log.jsonl"
_store.store_fragment = lambda *a, **k: None   # never touch the live memory store

SCENE = "A thin grey cat, one ear notched, watchful green eyes, sits by the grate. The fire is low."
IMPULSE = "the Portuguese encounter question remains unresolved"
ENTRY = "A thin grey cat with one notched ear sits by the grate and watches me with green eyes while the fire burns low."
seen = {}


async def fake_call(urls, system, user, max_tokens=0, temperature=0.0):
    seen["system"], seen["user"] = system, user
    return {"entry": ENTRY}


def run():
    return asyncio.run(jr.write_observation(fake_call, ["x"], "cat", SCENE, IMPULSE, {}))


# 1. default: impulse out of the prompt, row logged with full scene and impulse
check(jr.OBSERVATION_IMPULSE_IN_PROMPT is False, "default: impulse not in the prompt")
p = run()
check(p is not None and Path(p).exists(), "entry written to the (temp) day-book")
check("what made you reach" not in seen["user"] and "Portuguese" not in seen["user"],
      "user prompt carries neither the impulse line nor the impulse text")
check(SCENE in seen["user"], "user prompt still carries the scene")
rows = [json.loads(x) for x in jr._OBSERVATION_LOG.read_text(encoding="utf-8").splitlines() if x.strip()]
check(len(rows) == 1, "one log row per entry")
r = rows[0]
check(r["scene"] == SCENE and r["impulse"] == IMPULSE and r["entry"] == ENTRY and r["target"] == "cat",
      "row holds target, full scene, impulse and entry")
check(r["impulse_in_prompt"] is False and isinstance(r["ts"], float), "row carries ts and the flag state")

# 2. flag True restores the old line
jr.OBSERVATION_IMPULSE_IN_PROMPT = True
run()
check("what made you reach for the journal: " + IMPULSE in seen["user"], "flag True restores the impulse line")
jr.OBSERVATION_IMPULSE_IN_PROMPT = False

# 3. a long scene is logged whole though the model is shown 700 chars
long_scene = SCENE + " " + ("x" * 900)
asyncio.run(jr.write_observation(fake_call, ["x"], "cat", long_scene, IMPULSE, {}))
rows = [json.loads(x) for x in jr._OBSERVATION_LOG.read_text(encoding="utf-8").splitlines() if x.strip()]
check(rows[-1]["scene"] == long_scene.strip() and len(rows[-1]["scene"]) > 700, "full scene logged (not the 700-char cut)")

# 4. a too-short entry logs nothing; a log failure never blocks the entry
n = len(rows)


async def short_call(*a, **k):
    return {"entry": "short"}


asyncio.run(jr.write_observation(short_call, ["x"], "cat", SCENE, IMPULSE, {}))
check(len(jr._OBSERVATION_LOG.read_text(encoding="utf-8").splitlines()) == n, "rejected entry is not logged")
good = jr._OBSERVATION_LOG
jr._OBSERVATION_LOG = tmp / "a_file_not_a_dir" / "x" / "log.jsonl"
(tmp / "a_file_not_a_dir").write_text("block", encoding="utf-8")
check(run() is not None, "unwritable log path: the entry is still written (fail-open)")
jr._OBSERVATION_LOG = good

# 5. the prompt rule, stated positively, naming no colour or animal
sysm = jr.OBSERVATION_SYS
check("Every colour and every kind of animal you name comes from the text below" in sysm, "colour/animal rule present")
check("tabby" not in sysm.lower() and "ginger" not in sysm.lower(), "rule does not name tabby or ginger")

# 6. the reader
spec = importlib.util.spec_from_file_location("rjol", ROOT / "scripts" / "read_journal_observation_log.py")
rd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rd)
leaky = {"scene": SCENE, "impulse": IMPULSE, "entry": "The fire is low while the Portuguese encounter remains in my mind."}
clean = {"scene": SCENE, "impulse": IMPULSE, "entry": ENTRY, "target": "cat"}
tabby = {"scene": SCENE, "impulse": "", "entry": "A ginger tabby cat sits by the grate.", "target": "cat"}
check(len(rd.leak_words(leaky)) >= 2, "reader: flags the F-3687 impulse leak")
check(rd.leak_words(clean) == [], "reader: a grounded entry has no leak")
check(rd.ungrounded_kinds(tabby) == ["ginger", "tabby"], "reader: flags ginger/tabby absent from the scene")
check(rd.ungrounded_kinds(clean) == [], "reader: grey/green/cat from the scene are grounded")
summ = rd.summarize([leaky, clean, tabby])
check(summ["rows"] == 3 and summ["impulse_leak_ge2"] == round(1 / 3, 3) and summ["ungrounded_kind_rate"] == round(1 / 3, 3),
      "reader: summary rates")
check(rd.summarize([]) == {"rows": 0}, "reader: empty log is explicit")

print("\nFAILED: %d" % len(FAILS) if FAILS else "\nALL PASS")
sys.exit(1 if FAILS else 0)
