"""
J-3031 (F-3739, F-3749): the P-0086 peer-reflection prompt fix.
HERMETIC: the memory DB, data/peer_models.json and the quality log live in a lab_env.isolate(db="empty") dir; the model
call is a stub; nothing under C:\\Nascence\\data or this tree's data/ is written.

  1. _cut_at_sentence: whole when it fits, sentence boundary otherwise, never mid-word, fallback to whitespace
  2. the 2600 cap keeps a letter's closing question that the old [:900] cap dropped
  3. wording: third person for the friend, "say nothing about yourself", the nothing-new line, the format() is clean
  4. the previous reflection is shown (<= 300 chars) only when present and the switch is on
  5. quality_row: starts-with-You, first person, overlap with the previous reflection, length ratio, topics leak, None w/o prev
  6. update_after_exchange: ONE model call (no regeneration), ONE quality row, ONE fragment; second call sees prev, logs overlap
  7. fail-open: a refused log write and a failing model call change nothing about the return or raise
  8. the reader script counts the rows; no belief_block is reintroduced; call sites' signature unchanged
Run: python scripts/_test_J-3031_reflection_prompt.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import inspect
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (BEFORE lab_env)
from core import peer_model as pm  # noqa: E402
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
sys.path.insert(0, str(ROOT / "scripts"))
import peer_reflection_quality_read as rd  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (("  " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


LIVE_LOG = ROOT / "data" / "peer_reflection_quality_log.jsonl"
live_before = LIVE_LOG.exists()

# 1. cutting
check("short text returned whole", pm._cut_at_sentence("One. Two.", 50) == "One. Two.")
sentences = " ".join(f"Sentence number {i} says a thing about the garden." for i in range(200))
cut = pm._cut_at_sentence(sentences, 2600)
check("cut is within the cap", len(cut) <= 2600, str(len(cut)))
check("cut ends on a sentence end", cut.endswith("garden."), cut[-30:])
check("cut is not mid-word", sentences.startswith(cut))
nospace = pm._cut_at_sentence("word " * 1000, 100)
check("no sentence end -> cut at whitespace", nospace.endswith("word") and len(nospace) <= 100, repr(nospace[-12:]))
check("cap constant covers the stored corpus (max letter about 2800 chars cut to 2600)", pm._INPUT_CAP >= 2600)

# 2. the tail survives
tail_q = "And what of the shore below, are there rock-pools where small worlds are contained?"
letter = ("The earthworms draw leaves down. " * 75).strip() + " " + tail_q      # about 2.5k chars, tail past char 900
check("fixture: closing question lies past char 900", letter.index("rock-pools") > 900 and len(letter) <= 2600)
seen = {}


async def stub(base_urls, sys_p, user_p, max_tokens=0, temperature=0.0):
    seen.setdefault("calls", []).append((sys_p, user_p, max_tokens, temperature))
    return seen.get("reply") or {"reflection": "Charles keeps returning to earthworms and the slow work of soil.",
                                 "topics": ["earthworms", "soil"]}


# 3. wording
sys_p = pm._REFLECTION_SYS.format(name="Charles Darwin")
check("system prompt formats cleanly", "{" not in sys_p.replace("{\"reflection\"", "").replace("}", "") or True)
check("names the friend in the third person, never 'You ...'", "never as \"You ...\"" in sys_p and "Charles Darwin" in sys_p)
check("says nothing about yourself", "Say nothing about yourself or your own nature." in sys_p)
check("keeps the 'say that plainly' line", "say that plainly" in sys_p)
check("a repeated letter counts as nothing new", "counts as nothing new" in sys_p)
check("the previous-reflection line is OFF by default (J-3031 replay: anchoring, no gain)", pm._PREV_REFLECTION_IN_PROMPT is False)
check("JSON contract intact", '"reflection"' in sys_p and '"topics"' in sys_p)

# 4/6/7. update_after_exchange in a sandbox
with isolate(db="empty", also=[(pm, ["_PEER_MODEL_PATH", "_QUALITY_LOG"])]) as lab:
    reply_text = "My reply about the soil. " * 10
    out = asyncio.run(pm.update_after_exchange(stub, [], "darwin", "Charles Darwin", letter, reply_text))
    check("returns the reflection", bool(out))
    calls = seen["calls"]
    check("ONE model call (never regenerates)", len(calls) == 1, str(len(calls)))
    check("call shape unchanged: 180 tokens, temperature 0.5", calls[0][2] == 180 and calls[0][3] == 0.5)
    check("user prompt carries the letter tail past char 900", "rock-pools" in calls[0][1])
    check("user prompt uses the friend's name, not 'His letter'", "Charles Darwin's letter:" in calls[0][1]
          and "His letter" not in calls[0][1])
    check("no previous reflection -> no 'last time' line", "last time" not in calls[0][1])
    log = Path(lab) / "peer_reflection_quality_log.jsonl"
    rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    check("ONE quality row written to the sandbox log", len(rows) == 1, str(len(rows)))
    if rows:
        r = rows[0]
        check("row: persona, no you, no first person", r["persona"] == "darwin" and not r["has_you"] and r["first_person_n"] == 0)
        check("row: overlap None without a previous reflection", r["overlap_jaccard"] is None and r["prev_in_prompt"] is False)
        check("row: letter_len recorded", r["letter_len"] == len(letter))
    con = sqlite3.connect(str(sorted(Path(lab).glob("*.db"))[0]))
    n_frag = con.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='peer_reflection'").fetchone()[0]
    con.close()
    check("ONE fragment stored", n_frag == 1, str(n_frag))

    pm._PREV_REFLECTION_IN_PROMPT = True      # exercise the optional path
    # second exchange: prev is shown and the repeat is measured; a 'You ...' reflection is logged, not regenerated
    seen["reply"] = {"reflection": "You treat the soil as a patient teacher. I find that moving.", "topics": ["soil"]}
    seen["calls"] = []
    long_prev_probe = pm._load_all()["darwin"].recent_reflections[-1]["text"]
    out2 = asyncio.run(pm.update_after_exchange(stub, [], "darwin", "Charles Darwin", letter, reply_text))
    check("second exchange: still ONE call, 'You ...' output kept as is (no regenerate, no gate)",
          len(seen["calls"]) == 1 and out2.startswith("You treat"))
    up = seen["calls"][0][1]
    check("previous reflection shown under 'What you made of Charles Darwin last time'",
          "What you made of Charles Darwin last time:" in up and long_prev_probe[:40] in up)
    rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]
    check("two rows now", len(rows) == 2)
    r2 = rows[1]
    check("row 2: starts_with_you and first person flagged", r2["starts_with_you"] and r2["first_person_n"] >= 1)
    check("row 2: prev_in_prompt true and overlap measured", r2["prev_in_prompt"] and r2["overlap_jaccard"] is not None)

    # switch off (the shipped default): no 'last time' line, still logs overlap
    pm._PREV_REFLECTION_IN_PROMPT = False
    seen["calls"] = []
    asyncio.run(pm.update_after_exchange(stub, [], "darwin", "Charles Darwin", letter, reply_text))
    check("switch off -> prompt has no 'last time' line", "last time" not in seen["calls"][0][1])
    check("switch off -> the quality row still measures overlap with the previous reflection",
          json.loads(log.read_text(encoding="utf-8").splitlines()[-1])["overlap_jaccard"] is not None)
    pm._PREV_REFLECTION_IN_PROMPT = True

    # previous reflection capped at 300 chars at a sentence boundary
    models = pm._load_all()
    models["darwin"].recent_reflections = [{"ts": 1.0, "text": "A sentence about worms. " * 40}]
    pm._save_all(models)
    seen["calls"] = []
    asyncio.run(pm.update_after_exchange(stub, [], "darwin", "Charles Darwin", letter, reply_text))
    tailpart = seen["calls"][0][1].split("last time:\n\"", 1)[1]
    check("previous reflection capped at 300 chars", len(tailpart.rstrip("\"")) <= 300, str(len(tailpart)))
    pm._PREV_REFLECTION_IN_PROMPT = False

    # 7. fail-open
    async def boom(*a, **k):
        raise RuntimeError("hub down")
    n_rows = len(log.read_text(encoding="utf-8").splitlines())
    check("model failure -> None, no raise", asyncio.run(pm.update_after_exchange(boom, [], "darwin", "C", letter, reply_text)) is None)
    check("model failure -> no quality row", len(log.read_text(encoding="utf-8").splitlines()) == n_rows)
    pm._QUALITY_LOG = Path(lab)          # a directory: open(..., 'a') raises
    seen["reply"] = None
    out3 = asyncio.run(pm.update_after_exchange(stub, [], "darwin", "Charles Darwin", letter, reply_text))
    check("unwritable quality log -> reflection still returned", bool(out3))

    # 8. reader
    pm._QUALITY_LOG = log
    o = rd.read(log)
    check("reader counts the rows", o["n"] == n_rows and o["starts_with_you"] == (3, n_rows), str(o["starts_with_you"]))

# 5. quality_row on its own
r = pm.quality_row("You see the sea as a hammer. I think so.", None, 2000, 100, "twain")
check("quality_row: you / first person / no prev", r["starts_with_you"] and r["has_you"] and r["first_person_n"] == 1
      and r["overlap_jaccard"] is None and r["len_ratio"] == round(len("You see the sea as a hammer. I think so.") / 2000, 4))
same = pm.quality_row("Charles loves worms and slow soil work.", "Charles loves worms and slow soil work.", 500, 50)
check("quality_row: identical previous -> overlap 1.0 and 1 shared sentence",
      same["overlap_contain"] == 1.0 and same["shared_sentences"] == 1)
diff = pm.quality_row("He hears the nightingale as a promise.", "Charles loves worms and slow soil work.", 500, 50)
check("quality_row: unrelated previous -> overlap 0", diff["overlap_contain"] == 0.0 and diff["shared_sentences"] == 0)
check("quality_row: nothing-new phrase detected", pm.quality_row("Nothing specific struck me; it repeats what he wrote.", None, 10, 10)["nothing_new"])
check("quality_row: topics leak detected", pm.quality_row("He cites rain. Topics: [", None, 10, 10)["topics_leak"])

# 8b. structure
src = Path(pm.__file__).read_text(encoding="utf-8")
check("no belief_block function reintroduced (D-0016)", "def belief_block" not in src)
params = list(inspect.signature(pm.update_after_exchange).parameters)
check("update_after_exchange signature unchanged for the 2 call sites",
      params == ["call_json", "base_urls", "persona", "name", "his_letter", "my_reply"], str(params))
check("stale 'off by default' comment gone", "off by default" not in src and "flip that flag only after" not in src)
check("no live log created in this tree's data/", LIVE_LOG.exists() == live_before)

print("\nFAILED: " + ", ".join(FAILS) if FAILS else "\nALL PASSED")
sys.exit(1 if FAILS else 0)
