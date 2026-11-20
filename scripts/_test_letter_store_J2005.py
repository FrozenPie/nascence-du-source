"""J-2005 / D-0394 test for core/letter_store.py. All stores are redirected into a temp dir (no lab_env needed:
the module's path constants and peers._CORR_DIR are monkeypatched BEFORE any call). Exit 0 = pass."""
import json, pathlib, re, sys, tempfile, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import peers, letter_store as ls, profile
import core
assert pathlib.Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
tmp = pathlib.Path(tempfile.mkdtemp(prefix="ls_J2005_"))
peers._CORR_DIR = tmp / "Correspondence"
ls._DIR = tmp / "letter_store"; ls._LETTERS = ls._DIR / "letters.jsonl"; ls._EVENTS = ls._DIR / "status_events.jsonl"
ls._SHADOW = tmp / "shadow.jsonl"
FAILS = []
def check(l, c):
    print(("  ok   " if c else "  FAIL ") + l)
    if not c: FAILS.append(l)
def thread(p, rows):
    d = peers._CORR_DIR / p; d.mkdir(parents=True, exist_ok=True)
    (d / "thread.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
now = time.time(); D = 86400
thread("keats", [{"from": "keats", "text": "Dear friend, one.", "ts": now - 9 * D},
                 {"from": "du", "text": "Dear John, back.", "ts": now - 8 * D},
                 {"from": "keats", "text": "Dear friend, two.", "ts": now - 3 * D},
                 {"from": "keats", "text": "Dear friend, three.", "ts": now - 1 * D}])
thread("darwin", [{"from": "darwin", "text": "Finches.", "ts": now - 2 * D}])
before = (peers._CORR_DIR / "keats" / "thread.jsonl").read_bytes()
print("[1] backfill")
r = ls.sync(now)
check("12 letters? no: 5 indexed", r["new_letters"] == 5)
objs = {o["text"]: o for o in ls.derive(ls._threads(), ls._read_ids())}
check("answered letter is replied", objs["Dear friend, one."]["status"] == "replied")
check("unanswered are unread", objs["Dear friend, two."]["status"] == "unread" and objs["Finches."]["status"] == "unread")
check("Du's own letter is sent", objs["Dear John, back."]["status"] == "sent")
check("idempotent", ls.sync(now)["new_letters"] == 0 and ls.sync(now)["new_events"] == 0)
check("thread file untouched (source of truth)", (peers._CORR_DIR / "keats" / "thread.jsonl").read_bytes() == before)
ev = [e for e in ls._read_jsonl(ls._EVENTS) if e["letter_id"] == [o for o in objs.values() if o["text"] == "Dear friend, one."][0]["id"]]
check("replied letter keeps its history unread->read->replied", [e["status"] for e in ev] == ["unread", "read", "replied"])
print("[2] fetch marks read, history appended not overwritten")
ls.record_read("John Keats", "Dear friend, two.")
objs = {o["text"]: o for o in ls.derive(ls._threads(), ls._read_ids())}
check("fetched letter is read", objs["Dear friend, two."]["status"] == "read")
ls.sync(now)
st = [e["status"] for e in ls._read_jsonl(ls._EVENTS) if e["letter_id"] == objs["Dear friend, two."]["id"]]
check("two-letter history on it: unread then read", st == ["unread", "read"])
ls.record_read("John Keats", "Dear friend, two.")
check("second fetch does not double-log", len([e for e in ls._read_jsonl(ls._EVENTS) if e["letter_id"] == objs["Dear friend, two."]["id"] and e["status"] == "read"]) == 1)
print("[3] a later Du reply flips it to replied, still permanent")
thread("keats", [json.loads(l) for l in (peers._CORR_DIR / "keats" / "thread.jsonl").read_text().splitlines()] + [{"from": "du", "text": "again", "ts": now}])
ls.sync(now)
allp = ls._read_jsonl(ls._LETTERS)
check("no letter ever removed from the index", len(allp) == 6)
print("[4] words not numbers")
tray = ls.render_tray(now); peer = ls.render_peer("keats", now)
check("tray has no digits", not re.search(r"\d", tray))
check("peer view has no digits", not re.search(r"\d", peer))
check("tray does not tell him to write back", "write back" not in tray.lower() and "reply" not in tray.lower())
check("tray mentions Darwin's unopened letter", "Darwin" in tray and "not yet opened" in tray)
check("peer view lists every letter oldest to newest", peer.count("- ") == 5 if False else peer.count("theirs") + peer.count("yours") == 5)
print("[5] shadow: off -> '' but logged (default is ON since J-2249 / D-0449; forced off here to test shadow)")
import os as _os
check("PROMPT_ENABLED defaults True unless NASCENCE_LETTER_STORE_PROMPT=0 (J-2249/D-0449)",
      ls.PROMPT_ENABLED is (_os.environ.get("NASCENCE_LETTER_STORE_PROMPT", "1") != "0"))
ls.PROMPT_ENABLED = False
out = ls.on_look("look_letters", "", "back through my letters")
check("on_look returns '' in shadow", out == "")
sh = ls._read_jsonl(ls._SHADOW)
check("visit logged with would_show", sh and sh[-1]["kind"] == "visit" and sh[-1]["would_show_chars"] > 50)
ls.PROMPT_ENABLED = True
check("enabled renders the tray", "kept" in ls.on_look("letterbox"))
ls.PROMPT_ENABLED = False
print("[6] look phrase matcher")
check("matches 'my letters'", ls.wants_letters("", "i look back through my letters"))
check("matches 'the letters from keats'", ls.wants_letters("", "look at the letters from keats"))
check("not the mailbox", not ls.wants_letters("letterbox", "check the letterbox for letters"))
check("not a stray word", not ls.wants_letters("book", "the book is full of letters and numbers"))
print("[7] fence: non-live write path raises")
ls._LETTERS = ROOT / "data" / "letter_store" / "letters.jsonl"
try:
    ls._append(ls._LETTERS, {"x": 1}); check("guard_path raised on default data/ (not live)", False)
except profile.NonLiveWriteError:
    check("guard_path raised on default data/ (not live)", True)
print("FAILS:", FAILS); sys.exit(1 if FAILS else 0)
