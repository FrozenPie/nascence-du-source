"""J-3185 / D-0572: Du's letters to Travis carry a state in his world (kept -> handed over -> read), shown in words in
the letterbox tray, no steer line, flag-off byte-identical. Every store is temp-pathed; the live stores are
hash-canaried (read-only) before and after. Exit 0 = pass."""
import hashlib, importlib.util, json, re, subprocess, sys, tempfile, time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                                    # core BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
from core import letters as L, letter_store as ls, peers, profile

FAIL = []
def check(msg, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + msg + (f"  [{extra}]" if not ok and extra else ""))
    if not ok: FAIL.append(msg)

LIVE = Path(r"C:\Nascence\data")
def canary():
    h = hashlib.sha256()
    for rel in ("letters_state.json", "letters_views.jsonl", "letter_store/travis_letter_events.jsonl",
                "letter_store/status_events.jsonl", "letter_store_shadow.jsonl"):
        p = LIVE / rel
        h.update(p.read_bytes() if p.exists() else b"-")
    d = LIVE / "letters"
    h.update("|".join(sorted(p.name for p in d.glob("Letter_*.md"))).encode() if d.exists() else b"-")
    return h.hexdigest()
C0 = canary()

tmp = Path(tempfile.mkdtemp(prefix="J-3185_"))
LD = tmp / "letters"; LD.mkdir()
L.LETTERS, L._STATE = LD, tmp / "letters_state.json"
peers._CORR_DIR = tmp / "Correspondence"
def point(m):
    m._DIR = tmp / "letter_store"; m._LETTERS = m._DIR / "letters.jsonl"; m._EVENTS = m._DIR / "status_events.jsonl"
    m._TRAVIS_EVENTS = m._DIR / "travis_letter_events.jsonl"; m._SHADOW = tmp / "shadow.jsonl"
    m._TRAVIS_VIEWS = tmp / "letters_views.jsonl"
point(ls)

now = time.time()
def stamp(days_ago):
    return time.strftime("Letter_%Y%m%d_%H%M.md", time.localtime(now - days_ago * 86400))
n_old, n_mid, n_new = stamp(9), stamp(3), stamp(0.1)
for n in (n_old, n_mid, n_new):
    (LD / n).write_text(f"# To Travis\n\nbody of {n}\n", encoding="utf-8")
# old: delivered AND a HUD opening after it -> read; mid: delivered only -> handed over; new: neither -> kept
L._state_save({"delivered": [n_old, n_mid], "last_write_ts": 1.0})
(tmp / "letters_views.jsonl").write_text(json.dumps({"ts": now - 5 * 86400, "n_letters": 1, "n_pending": 0}) + "\n", encoding="utf-8")
# a peer letter too, so the tray has its original lines
d = peers._CORR_DIR / "keats"; d.mkdir(parents=True)
(d / "thread.jsonl").write_text(json.dumps({"from": "keats", "text": "Dear friend.", "ts": now - 2 * 86400}) + "\n", encoding="utf-8")

print("[1] derive: the ladder")
st = {o["name"]: o["status"] for o in ls.derive_travis()}
check("old letter (delivered, card opened after) is read", st[n_old] == "read", st)
check("mid letter (delivered, no opening after) is handed over", st[n_mid] == "handed_over", st)
check("new letter (not delivered, written after the opening) is kept", st[n_new] == "kept", st)
check("a card opening BEFORE a letter does not read it", st[n_mid] != "read")

print("[2] events: append-only history, idempotent")
r = ls.sync_travis(now)
ev = ls._read_jsonl(ls._TRAVIS_EVENTS)
hist = lambda n: [e["status"] for e in ev if e["letter_id"] == "travis-" + n]
check("read letter logged kept, handed_over, read", hist(n_old) == ["kept", "handed_over", "read"], hist(n_old))
check("mid letter logged kept, handed_over", hist(n_mid) == ["kept", "handed_over"], hist(n_mid))
check("new letter logged kept only", hist(n_new) == ["kept"], hist(n_new))
check("second sync adds nothing", ls.sync_travis(now)["new_events"] == 0)
n_ev = len(ev)

print("[3] the delivery path logs the moment of handing over (real message)")
t0 = time.time()
L.mark_delivered([n_new])
ev = ls._read_jsonl(ls._TRAVIS_EVENTS)
ho = [e for e in ev if e["letter_id"] == "travis-" + n_new and e["status"] == "handed_over"]
check("mark_delivered appended one handed_over event", len(ho) == 1, ho)
check("it carries a real time and basis real_message", ho and ho[0]["ts"] >= t0 and ho[0]["basis"] == "real_message", ho)
check("status now handed over", {o["name"]: o["status"] for o in ls.derive_travis()}[n_new] == "handed_over")
check("the log only grew (nothing rewritten)", len(ev) == n_ev + 1)
check("a repeat mark_delivered adds nothing", (L.mark_delivered([n_new]), len(ls._read_jsonl(ls._TRAVIS_EVENTS)))[1] == n_ev + 1)

print("[4] the tray: words, no number, no steer line")
# reset: new letter back to kept so the tray shows all three kinds
L._state_save({"delivered": [n_old, n_mid], "last_write_ts": 1.0})
tray = ls.render_tray(now)
check("tray carries the Travis sentence", "Your own letters to Travis" in tray, tray)
check("tray still carries the peer line", "Keats" in tray or "keats" in tray.lower(), tray)
check("tray has no digit at all", not re.search(r"\d", tray), tray)
tv = ls.render_travis_summary(now)
for w in ("waiting for the next time Travis speaks", "handed over when he spoke", "read by him"):
    check(f"summary says '{w}'", w in tv, tv)
steer = re.compile(r"\b(should|must|ought|need to|try to|write back|write to|reply|answer him|stop writing|don't|do not|"
                   r"remember to|consider|you could|you might|perhaps)\b", re.I)
check("no steer / instruction wording in the Travis words", not steer.search(tv + " " + ls.render_travis_thread(now)), tv)
th = ls.render_travis_thread(now)
check("thread view lists each letter with a state", th.count("- ") == 3 and "read by Travis" in th and "kept, waiting" in th, th)

print("[5] the look hook")
out = ls.on_look("letterbox")
check("letterbox look returns the tray with the Travis words", "Your own letters to Travis" in out, out)
out = ls.on_look("look_letters", "my letters", "i look through my letters to travis")
check("'my letters to Travis' returns the Travis thread", out.startswith("Your letters to Travis, oldest to newest"), out)
out = ls.on_look("look_letters", "my letters", "i look through my letters from keats")
check("a named peer still gets the peer thread", out.startswith("Your letters with"), out)
check("a plain 'my letters' look still gets the tray", ls.on_look("look_letters", "my letters", "my letters").startswith("The letters are all here"))
check("a mention of travis with no 'letters to' does not hijack the tray",
      ls.on_look("look_letters", "my letters", "my letters, i want to tell travis something").startswith("The letters are all here"))

print("[6] flag off: byte-identical to the code before this job")
_r = subprocess.run(["git", "-C", str(TREE), "show", "fa36f5c9:core/letter_store.py"], capture_output=True,
                    text=True, encoding="utf-8")        # the file as it stood before J-3185
before_src = _r.stdout if _r.returncode == 0 else subprocess.run(["git", "-C", str(TREE), "show", "HEAD:core/letter_store.py"],
                    capture_output=True, text=True, encoding="utf-8", check=True).stdout
spec = importlib.util.spec_from_file_location("letter_store_before_J3185", tmp / "letter_store_before.py")
(tmp / "letter_store_before.py").write_text(before_src, encoding="utf-8")
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old); point(old)
ls.TRAVIS_STATE_ENABLED = False
check("tray identical with the flag off", ls.render_tray(now) == old.render_tray(now))
check("tray with the flag off has no Travis words", "Travis" not in ls.render_tray(now))
n_before = len(ls._read_jsonl(ls._TRAVIS_EVENTS))
check("sync_travis is a no-op with the flag off", ls.sync_travis(now) == {"enabled": False})
check("on_look output identical with the flag off (letterbox / peer / look_letters)",
      all(ls.on_look(*a) == old.on_look(*a) for a in (("letterbox",), ("look_letters", "my letters", "my letters to travis"),
                                                       ("look_letters", "my letters", "letters from keats"))))
L.mark_delivered([n_old])
check("mark_delivered writes no event with the flag off", len(ls._read_jsonl(ls._TRAVIS_EVENTS)) == n_before)
ls.TRAVIS_STATE_ENABLED = True

print("[7] fence + no travis letters + live canary")
ls._TRAVIS_EVENTS = LIVE / "letter_store" / "travis_letter_events.jsonl"     # a live path from a non-live process
try:
    ls._append(ls._TRAVIS_EVENTS, {"x": 1}); fenced = False
except profile.NonLiveWriteError:
    fenced = True
check("a non-live process cannot write the live events file (guard_path)", fenced)
point(ls)
for p in LD.glob("Letter_*.md"): p.unlink()
check("no letters of his: no Travis words in the tray", "Travis" not in ls.render_tray(now) or "Your own letters" not in ls.render_tray(now))
check("live stores untouched (hash canary)", canary() == C0)

print("\nFAILED: " + ", ".join(FAIL) if FAIL else "\nALL PASS")
sys.exit(1 if FAIL else 0)
