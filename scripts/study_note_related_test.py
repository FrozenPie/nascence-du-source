"""
Hermetic test for J-3204 / D-0592: the study note's related-material injection is PASSAGE-level
(core/study_note.py _scored_scan_related / _related_context / _whole_item / compose_note).

No LLM, no embedder, no live data: runs INSIDE lab_env.isolate(db="empty"); store._embed is a deterministic fake
("ANG:<float>" in a text picks its direction); call_json is a fake that records the prompt.

  [1] _whole_item: a short item is returned whole; a long one is cut on a sentence boundary with the
      '[My study note: ...]' header stripped; with no boundary it cuts on a word, never mid-word
  [2] two DIFFERENT passages of one book get DIFFERENT related items (the old book-level walk gave every
      passage of a book the same three)
  [3] at most 2 items; the same book's own notes are never offered; an item with no content word in common
      with the passage is never offered even at high cosine
  [4] nothing qualifies -> ("", []) and compose_note leaves the 'Related material' section OUT of the prompt
  [5] the 'use ONLY if it genuinely fits' wording is unchanged when items are offered

Run:  python scripts/study_note_related_test.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423): the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import numpy as np
from core import study_note as sn
from core.memory import store
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

def _vec(angle: float) -> np.ndarray:
    v = np.array([np.cos(angle), np.sin(angle), 0.0, 0.0], dtype=np.float32)
    return v / np.linalg.norm(v)

def _fake_embed(text: str):
    m = re.search(r"ANG:([-\d.]+)", text or "")
    return _vec(float(m.group(1))) if m else _vec(0.0)

print("[1] _whole_item")
short = "[My study note: 'T' · on 'Book' · subject: S] The tide turns twice a day."
check("a short item is kept whole, header and all", sn._whole_item(short) == short)
longtxt = ("[My study note: 'T' · on 'Book' · subject: S] " + "The first sentence is here. " +
           "The second sentence follows on. " * 30)
cut = sn._whole_item(longtxt, 200)
check("a long item loses the fragment header", "[My study note" not in cut)
check("a long item ends on a sentence boundary", cut.endswith(".") and len(cut) <= 200)
words = sn._whole_item("alpha " * 200, 50)
check("no sentence boundary -> cut on a word, never mid-word", set(words.split()) == {"alpha"} and len(words) <= 50)

with isolate(db="empty") as lab_dir:
    assert "_lab" in str(store.DB_PATH), store.DB_PATH
    store._embed = _fake_embed
    def put(content: str, angle: float, origin="study"):
        return store.store_fragment(content=f"{content} ANG:{angle}", layer="episodic", relevance=0.8,
                                    importance=0.8, keywords=["study"], origin=origin,
                                    source_type="study_note", source_id="")

    f_tide = put("[My study note: 'Tides' · on 'Almanac' · subject: sea] Spring tides follow the new moon and "
                 "the full moon, when sun and moon pull together on the ocean.", 0.1)
    f_bees = put("[My study note: 'Bees' · on 'Hive Book' · subject: bees] A honey bee colony keeps its queen "
                 "and workers warm through winter by clustering around the brood.", 0.3)
    f_third = put("[My study note: 'Gulls' · on 'Shore Birds' · subject: birds] Gulls follow the ocean tide line "
                  "to feed on whatever the moon and sun pulled water leaves.", 0.15)
    f_same = put("[My study note: 'Own' · on 'The Sea Book' · subject: sea] Another note of the same book about "
                 "tides, the moon and the ocean.", 0.1)
    f_nolex = put("[My study note: 'Rocks' · on 'Geology' · subject: stones] Granite basalt feldspar quartz mica.", 0.1)

    print("[2] passage-level: different passages, different items")
    p_sea = "ANG:0.1 The spring tide rose with the new moon and the ocean pulled hard over the sand."
    p_bee = "ANG:0.3 In winter the bee colony clusters round the brood and keeps the queen warm."
    t_sea, ids_sea = sn._related_context("The Sea Book", p_sea)
    t_bee, ids_bee = sn._related_context("The Sea Book", p_bee)
    check("sea passage is offered the tide note first", ids_sea and ids_sea[0] == f_tide)
    check("bee passage is offered the bee note first", ids_bee and ids_bee[0] == f_bees)
    check("the two passages of ONE book do not get the same items", ids_sea != ids_bee)

    print("[3] cap, same-book exclusion, shared-content-word floor")
    check("at most 2 items", len(ids_sea) <= 2 and t_sea.count("\n- ") + t_sea.startswith("- ") <= 2)
    check("the same book's own note is never offered", f_same not in ids_sea + ids_bee)
    check("an item sharing no content word is never offered", f_nolex not in ids_sea + ids_bee)
    check("items are whole (the old 220-char cut is gone)", "sun and moon pull together on the ocean." in t_sea)

    print("[4] nothing qualifies -> no section in the prompt")
    t_none, ids_none = sn._related_context("The Sea Book", "ANG:2.5 Zebra quagga okapi.")
    check("no related items", (t_none, ids_none) == ("", []))
    seen = {}
    async def fake_call_json(base_urls, sys_p, user, **kw):
        seen["user"] = user
        return {"understanding": "x", "title": "t"}
    asyncio.run(sn.compose_note(fake_call_json, [], "The Sea Book", "a passage", related_text=t_none))
    check("compose_note omits the 'Related material' section when empty", "Related material" not in seen["user"])

    print("[5] wording unchanged when items are offered")
    asyncio.run(sn.compose_note(fake_call_json, [], "The Sea Book", p_sea, related_text=t_sea))
    check("'use ONLY if it genuinely fits' wording is unchanged",
          "Related material from elsewhere in your scholarship (use ONLY if it genuinely fits):\n- " in seen["user"])

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
