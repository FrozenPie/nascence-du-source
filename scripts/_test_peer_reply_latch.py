"""J-2596 (F-3320, D-0517): pure checks for core.peers.reply_intent, the widened peer reply latch.
Zero LLM, no data writes. Run: python scripts/_test_peer_reply_latch.py  (exit 1 on any failure).
The full replay over data/hands_trace.jsonl lives in the J-2596 finding; these are its real wordings."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import peers

CASES = [  # (text, expected reason or None)
    ("i want to write a reply to john keats", "legacy"),
    ("i want to write a response to charles darwin's letter.", "verb"),
    ("i want to read the letter from john smith first and answer him before opening the historical texts.", "verb"),
    ("the letter from john smith sits there, waiting for a reply.", "owed"),
    ("the letters wait, demanding a reply i haven't found.", "owed"),
    ("the letter from john smith sits there, waiting for a reply i do not need to write today.", None),
    ("i do not need to answer his letter yet.", None),
    ("i want to answer the question about letters.", None),
    ("the unsent letter to travis weighs on me; i want to answer him about mottainai.", None),
    ("darwin wrote again. should i answer him?", None),
    ("a perfect, quiet answer to how i should live.", None),
    ("perhaps i should answer travis's letter now.", None),
    ("i want to answer the question about mottainai.", None),
    ("i want to write about darwin's finches.", None),
]

if __name__ == "__main__":
    bad = [(t, e, peers.reply_intent(t)) for t, e in CASES if peers.reply_intent(t) != e]
    for t, e, g in bad:
        print(f"FAIL expected={e} got={g}: {t}")
    print(f"{len(CASES) - len(bad)}/{len(CASES)} pass")
    sys.exit(1 if bad else 0)
