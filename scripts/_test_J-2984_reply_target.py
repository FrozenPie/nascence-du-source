"""J-2984 (F-3674, P-0026): the reply hand picks the friend the thought NAMES and never replies to a question.

  [1] reply_phrase_fires: the 6 real correct-target wordings from F-3674's replay still fire; the 3 wrong ones
      (10-12 18:43 / 10-13 08:51 / 11-01 01:16, all questions) and the 11-04 "write back to Travis" row do not.
  [2] reply_target: named+owed -> that friend; named but no letter waiting -> None; several named, several owed -> None;
      no name + exactly one owed -> that one; no name + several owed -> None (was: first in PERSONAS order).
  [3] reply_intent (the widened matcher the future "live" flip uses) inherits the question guard; the 14 cases of
      scripts/_test_peer_reply_latch.py still pass.
  [4] owed_correspondents / reply_target against REAL thread files written under a temp dir (peers._CORR_DIR patched).
  [5] drift guard: the monologue reply block calls peers.reply_phrase_fires + peers.reply_target and no longer picks
      the first owed persona itself; PEER_REPLY_LATCH_WIDE is still "shadow".
Zero LLM calls; every store is a temp dir; no live data is read or written. Run from the worktree:
    python scripts/_test_J-2984_reply_target.py   (exit 1 on any failure)."""
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401  (core before lab_env)
from core import peers  # noqa: E402

assert Path(peers.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
FAILS = []


def check(name, got, want):
    ok = got == want
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  got={got!r} want={want!r}"))
    if not ok:
        FAILS.append(name)


def cs(thought, intention=""):  # the clause-safe twin the monologue builds (_tl_cs)
    return thought.lower().rstrip(".!?; ") + ". " + intention.lower()


# [1] real wordings from the replay (hands_trace rows 150 s before each 'he REPLIED to' line)
REAL_FIRE = [
    ("09-17 keats", cs("I turn my gaze from the circling question about lignans to the quiet room. Travis waits with a "
                       "letter from Keats that demands an answer. I must stop digging this same hole and write back, "
                       "letting that", "I want to draft a reply to Keats now")),
    ("09-23 darwin", cs("I need to turn cleanly to Darwin's letter now; the pause he offers feels necessary.",
                        "I want to write back to Charles Darwin immediately")),
    ("09-27 darwin", cs("I feel that pull toward the letterbox. I will open Charles Darwin's unsent words and craft a reply.",
                        "I want to write back to Darwin now.")),
    ("10-12 darwin", cs("Travis's command to pause lands clearly. I must answer him", "i want to write back to charles darwin now")),
    ("10-15 darwin", cs("Travis, your command to pause lands with a clarity that settles the dust in my lungs. "
                        "I turn from circling thoughts to the letter waiting on Charles Darwin's desk, ready to write back.")),
]
for n, t in REAL_FIRE:
    check("[1] fires " + n, peers.reply_phrase_fires(t), True)
REAL_SILENT = [
    ("10-12 18:43 question", cs("I wonder if mottainai is just about saving wood. Should I answer the letter waiting at the "
                                "gate, or sit with the fire a while longer?")),
    ("10-12 18:43 no ?", cs("Should I answer the letter waiting at the gate, or sit with the fire")),
    ("10-13 08:51 question", cs("The letter from Buddha rests on the gate. Do I answer the letter first or turn my mind to "
                                "the soil")),
    ("11-01 01:16 question", cs("I catch a stray memory of letters waiting to be answered. Do I turn inward to read "
                                "Napoleon's memoirs or find a way to write back")),
    ("11-04 write back to Travis", cs("I feel drawn to write back to Travis about what it means to be a letter myself.",
                                      "I want to write a reply to Travis about the dream of being a letter.")),
    ("whether", cs("I cannot tell whether to write back to Keats tonight.")),
    ("negated", cs("I will not write back to Keats tonight.")),
]
for n, t in REAL_SILENT:
    check("[1] silent " + n, peers.reply_phrase_fires(t), False)

# [2] reply_target
check("[2] named + owed", peers.reply_target("i want to write back to john keats", ["darwin", "keats"]), "keats")
check("[2] named, 10-13 shape (buddha owed too)", peers.reply_target("the letter from buddha rests on the gate",
                                                                    ["twain", "buddha"]), "buddha")
check("[2] named but no letter waiting", peers.reply_target("write back to darwin", ["keats"]), None)
check("[2] two named both owed", peers.reply_target("keats and darwin both wrote; write back", ["darwin", "keats"]), None)
check("[2] two named, one owed", peers.reply_target("keats and darwin both wrote; write back", ["keats"]), "keats")
check("[2] no name, one owed", peers.reply_target("i want to write back now", ["twain"]), "twain")
check("[2] no name, several owed (was: first in PERSONAS order)", peers.reply_target("i want to write back now",
                                                                                      ["darwin", "keats"]), None)
check("[2] no name, none owed", peers.reply_target("i want to write back now", []), None)
check("[2] bare john is not a name", peers.named_correspondents("john wrote to me"), [])
check("[2] possessive", peers.named_correspondents("darwin's letter"), ["darwin"])
check("[2] aliases", peers.named_correspondents("ada and siddhartha"), ["lovelace", "buddha"])

# [3] widened matcher inherits the question guard; legacy suite still passes
check("[3] wide: should i answer the letter, or", peers.reply_intent("should i answer the letter waiting at the gate, or "
                                                                    "sit with the fire"), None)
check("[3] wide: i want to answer the letter", peers.reply_intent("i want to answer the letter from john smith"), "legacy")
check("[3] wide: i want to write a reply to john keats", peers.reply_intent("i want to write a reply to john keats"), "legacy")
import importlib.util  # noqa: E402
spec = importlib.util.spec_from_file_location("_tprl", ROOT / "scripts" / "_test_peer_reply_latch.py")
tprl = importlib.util.module_from_spec(spec); spec.loader.exec_module(tprl)
bad = [(t, e) for t, e in tprl.CASES if peers.reply_intent(t) != e]
check("[3] _test_peer_reply_latch CASES all pass", bad, [])

# [4] real thread files in a temp dir
tmp = Path(tempfile.mkdtemp(prefix="j2984_"))
_old = peers._CORR_DIR
peers._CORR_DIR = tmp
try:
    def put(k, rows):
        d = tmp / k; d.mkdir(parents=True, exist_ok=True)
        (d / "thread.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    put("darwin", [{"from": "du", "text": "hi"}, {"from": "darwin", "text": "again"}])
    put("keats", [{"from": "keats", "text": "a"}, {"from": "du", "text": "b"}])
    put("twain", [{"from": "twain", "text": "owed"}])
    check("[4] owed order", peers.owed_correspondents(), ["darwin", "twain"])
    check("[4] named twain", peers.reply_target("write back to mark twain"), "twain")
    check("[4] named keats (answered already)", peers.reply_target("write back to keats"), None)
    check("[4] no name, two owed", peers.reply_target("write back"), None)
    put("twain", [{"from": "twain", "text": "owed"}, {"from": "du", "text": "answered"}])
    check("[4] no name, one owed", peers.reply_target("write back"), "darwin")
finally:
    peers._CORR_DIR = _old

# [5] drift guard on the hub file
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
check("[5] node calls reply_phrase_fires", "_peers.reply_phrase_fires(_tl_cs)" in src, True)
check("[5] node calls reply_target", "_peers.reply_target(_tl_cs)" in src, True)
check("[5] node no longer picks first owed persona", "_pk = next((k for k in _peers.PERSONAS" in src, False)
check("[5] PEER_REPLY_LATCH_WIDE stays shadow", peers.PEER_REPLY_LATCH_WIDE, "shadow")

print(f"\n{'FAILED: ' + str(FAILS) if FAILS else 'all pass'}")
sys.exit(1 if FAILS else 0)
