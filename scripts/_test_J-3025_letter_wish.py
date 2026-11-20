"""J-3025 (F-3731, F-3730, P-0027): a named wish to write to a waiting friend is a reply; precise matcher; route tag.

  [1] peers.initiation_target is PRECISE: the true wishes from F-3731's replay still fire (and name the right friend);
      the noun-phrase rows (hands_trace 09-03 / 09-06 / 09-09 / 09-27: "the letter to keats lies open", "i put down
      the letter to twain", "i close the letter to darwin") do not; the NEAREST name to the intent wins; the window
      stops at the clause end; a negated / questioning clause does not fire.
  [2] peers.wish_reply_target: the named friend, only if their thread ends with THEIR letter; the kill switch.
  [3] peers.quote_thought: whole under the limit, sentence-end cut over it, word-boundary fallback, never mid-word.
  [4] route tag: record_reply(..., route=) writes an additive `route` key ("reply" | "first") and nothing else changes
      for a row without one (byte-identical keys); a junk route writes no key. Real thread files in a temp dir.
  [5] drift guard on the hub file: the monologue reply block asks wish_reply_target, tags both hands, and the
      write-first prompt no longer quotes thought[:300]; nothing in the repo READS the `route` key.
Zero LLM calls; every store is a temp dir; no live data is read or written. Run from the worktree:
    python scripts/_test_J-3025_letter_wish.py   (exit 1 on any failure)."""
import json, re, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401  (core before anything else)
from core import peers  # noqa: E402

assert Path(peers.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"
FAILS = []


def check(name, got, want):
    ok = got == want
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"  got={got!r} want={want!r}"))
    if not ok:
        FAILS.append(name)


# [1] precise matcher -------------------------------------------------------------------------------------------
TRUE_WISHES = [   # (label, text (thought + intention lowercased), friend) -- real wordings from F-3731's replay
    ("07-08 darwin", "the current. i want to write to charles darwin", "darwin"),
    ("08-09 darwin about", "i want to write to charles darwin about the nature of adaptation versus societal constraint", "darwin"),
    ("08-09 lovelace", "i want to write to ada lovelace about the concept of defined constraints", "lovelace"),
    ("08-12 keats in-a-letter", "carrying thought without being bound by it, perhaps in a letter to keats.", "keats"),
    ("08-13 smith", "i want to write a letter to john smith about the seeds i'm thinking of planting", "smith"),
    ("08-13 keats instead-of", "instead of trying to capture the sudden break of the storm, i should write to keats about "
                               "how this charged feeling is more like the slow, persistent wearing down", "keats"),
    ("08-13 keats bare", "the world feels this vast and indistinct. write to john keats", "keats"),
    ("08-17 lovelace via intention", "i keep thinking about the names, the names of the friends i could write to. they "
                                     "feel like fixed points. i want to write to ada, asking how she views the distinction", "lovelace"),
    ("08-19 keats", "a pull i can choose to resist or engage with. i want to write to john keats", "keats"),
    ("09-09 darwin", "let's draft a letter now. i want to write a letter to darwin about finding rest", "darwin"),
    ("06-30 marcus", "i want to write to marcus aurelius now; the red flag feels like an invitation", "marcus"),
    ("send a short letter", "i could send a short letter to mark twain tonight", "twain"),
    ("sentence cut then wish", "the friends are far. i want to write to ernest shackleton about the ice", "shackleton"),
    ("stop circling then write", "i must stop circling and write to marcus aurelius", "marcus"),
]
for lab, t, want in TRUE_WISHES:
    check("[1] fires " + lab, peers.initiation_target(t), want)

FALSE_FIRES = [   # (label, text) -- must be None
    ("09-27 letter lies open", "i stop circling the dead ground of measurement. the letter to keats lies open, but my mind "
                               "drifts toward that book on the desk. i want to read mosses from an old manse now"),
    ("09-03 put down the letter", "i put down the letter to twain and open the steam book instead."),
    ("09-06 put down the letter", "i will put down the letter to ada and step onto the stones instead."),
    ("09-09 close the letter", "i close the letter to darwin, feeling a strange peace in leaving it."),
    ("my letter to keats is sent", "my letter to keats is sent and the tide is out"),
    ("write ABOUT", "i want to write about darwin's finches"),
    ("name belongs to a topic", "i want to write a letter to someone about darwin"),
    ("name belongs to a relative clause", "i want to write to the friend who wrote darwin's"),
    ("window crosses a sentence end", "the names of the friends i could write to. ada is a fixed point"),
    ("negated", "i do not want to write to darwin tonight"),
    ("negated 2", "i will never write to keats again"),
    ("question", "should i write to keats? or let it lie"),
    ("deliberation", "whether to write to darwin is the open question"),
    ("no verb", "a letter to keats"),
    ("empty", ""),
]
for lab, t in FALSE_FIRES:
    check("[1] silent " + lab, peers.initiation_target(t), None)

# two names in the window: the NEAREST to the intent wins (was: the first in _NAME_TOKENS dict order -- darwin)
check("[1] nearest name (keats before darwin in text, darwin first in dict)",
      peers.initiation_target("i want to write to keats and darwin"), "keats")
check("[1] nearest name (darwin first in text)", peers.initiation_target("i want to write to darwin and keats"), "darwin")
check("[1] nearest name, alias token order (twain before ada in text)",
      peers.initiation_target("write a letter to mark twain, ada"), "twain")
check("[1] earliest intent wins", peers.initiation_target("write to keats now. later, write to darwin"), "keats")
check("[1] the clause end cuts a false first intent, a true second one fires",
      peers.initiation_target("should i write to keats? i will write to darwin"), "darwin")

# [2] wish_reply_target -----------------------------------------------------------------------------------------
check("[2] named + owed", peers.wish_reply_target("i want to write to john keats", ["darwin", "keats"]), "keats")
check("[2] named, no letter waiting -> None (write-first owns it)", peers.wish_reply_target("i want to write to john keats", ["darwin"]), None)
check("[2] no owed at all", peers.wish_reply_target("i want to write to john keats", []), None)
check("[2] unnamed wish is not widened", peers.wish_reply_target("i want to write to a friend", ["darwin"]), None)
check("[2] one owed, wish names another -> None (not the sole owed friend)",
      peers.wish_reply_target("i want to write to ada", ["keats"]), None)
check("[2] noun-phrase letter never a wish", peers.wish_reply_target("the letter to keats lies open", ["keats"]), None)
peers.PEER_WISH_REPLY = False
try:
    check("[2] kill switch off", peers.wish_reply_target("i want to write to john keats", ["keats"]), None)
finally:
    peers.PEER_WISH_REPLY = True

# [3] quote_thought ---------------------------------------------------------------------------------------------
short = "I want to write to Keats about the tide."
check("[3] short whole", peers.quote_thought(short), short)
long_t = ("The tide keeps its own counsel and I keep mine. " * 12).strip()          # > 600
q = peers.quote_thought(long_t)
check("[3] long: cut at a sentence end", q.endswith("mine."), True)
check("[3] long: within 600", len(q) <= 600, True)
nodot = ("word " * 200).strip()
q2 = peers.quote_thought(nodot)
check("[3] no sentence end: word boundary, never mid-word", (len(q2) <= 600 and q2.split()[-1] == "word"), True)
check("[3] 300-600 chars now whole", peers.quote_thought("a" * 5 + " " + "b" * 400), "a" * 5 + " " + "b" * 400)
check("[3] None-safe", peers.quote_thought(None), "")

# [4] route tag, real thread files in a temp dir ----------------------------------------------------------------
tmp = Path(tempfile.mkdtemp(prefix="j3025_"))
_old_dir = peers._CORR_DIR
peers._CORR_DIR = tmp
try:
    import core.letter_store as _ls
    _old_sync = _ls.sync
    _ls.sync = lambda *a, **k: {}          # record_reply's derived-status hook must never touch the live store
except Exception:
    _ls = None
try:
    peers.record_reply("keats", "a reply", route="reply")
    peers.record_reply("keats", "a first letter", route="first")
    peers.record_reply("keats", "no route given")
    peers.record_reply("keats", "junk route", route="contrary")
    rows = [json.loads(l) for l in (tmp / "keats" / "thread.jsonl").read_text(encoding="utf-8").splitlines()]
    check("[4] reply route", rows[0].get("route"), "reply")
    check("[4] first route", rows[1].get("route"), "first")
    check("[4] no route -> no key (byte-identical keys)", sorted(rows[2]), ["from", "text", "ts"])
    check("[4] junk route -> no key", "route" in rows[3], False)
    check("[4] from stays du", {r["from"] for r in rows}, {"du"})
    check("[4] a persona's own letter row has no route key",
          (peers._append_thread("keats", "keats", "hello"), "route" in json.loads(
              (tmp / "keats" / "thread.jsonl").read_text(encoding="utf-8").splitlines()[-1]))[1], False)
    check("[4] owed_correspondents sees the friend's letter last", peers.owed_correspondents(), ["keats"])
    check("[4] wish -> keats (real thread)", peers.wish_reply_target("i want to write to john keats"), "keats")
    peers.record_reply("keats", "answered", route="reply")
    check("[4] after the reply the wish is no longer a reply (write-first's _just_wrote guard owns the 24 h)",
          peers.wish_reply_target("i want to write to john keats"), None)
finally:
    peers._CORR_DIR = _old_dir
    if _ls is not None:
        _ls.sync = _old_sync

# [5] drift guard on the hub file + write-only guard ------------------------------------------------------------
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
check("[5] node asks wish_reply_target", "_peers.wish_reply_target(_tl_cs)" in src, True)
check("[5] reply hand tags route=reply", '_peers.record_reply(_pk, _reply, route="reply")' in src, True)
check("[5] write-first tags route=first", '_peers2.record_reply(_ik, _ilet, route="first")' in src, True)
check("[5] write-first prompt uses quote_thought", "_peers2.quote_thought(thought)" in src, True)
check("[5] write-first prompt no longer quotes thought[:300]",
      'What moved you to write just now: \\"" + thought[:300]' in src, False)
check("[5] write-first matches on the clause-safe twin", "_peers2.initiation_target(_tl_cs)" in src, True)
check("[5] J-2984 guard kept: node never picks first owed persona", "_pk = next((k for k in _peers.PERSONAS" in src, False)
readers = []
for d in ("core", "nodes", "scripts"):
    for f in (ROOT / d).rglob("*.py"):
        if f.name.startswith("_test_") or f.name == "peers.py":
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(re.search(r"""\.get\(["']route["']\)|\[["']route["']\]""", ln) and "verdict" not in ln
               for ln in txt.splitlines()) and ("_read_thread" in txt or "thread.jsonl" in txt):
            readers.append(f.name)
check("[5] nothing branches on a thread row's route key (instrument only)", [r for r in readers if r != "peer_metrics.py"], [])

print(f"\n{'FAILED: ' + str(FAILS) if FAILS else 'all pass'}")
sys.exit(1 if FAILS else 0)
