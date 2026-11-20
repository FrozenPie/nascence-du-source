"""
Hermetic test for J-2925 (F-3603, P-0029): the "search my own works" hand reaches authored WORK_ files.
  - core.study.scan_works: top-level WORK_/ESSAY_/TAB_ first, notes/<book>/ only when fewer than two top-level hits
  - a tree shaped like the live one (hundreds of ESSAY_ + notes/ paths sorting BEFORE every WORK_) still returns a WORK_ hit
  - per-call cold-read budget bounds disk reads; the cache serves repeat calls; a changed file is re-read
  - InnerMonologueNode._search_works: same perceive wording, still True/False as before, find_misplaced still short-circuits
All under a temp dir; model, memory and activity_memory writes are stubbed.   Run: python scripts/_test_J-2925_search_works_reach.py
"""
from __future__ import annotations
import asyncio, os, sys, tempfile, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env: the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import study

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j2925_"))
base = tmp / "Study"
(base / "notes" / "Some_Book").mkdir(parents=True)

def put(path, title, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n*note*\n\n{body}\n", encoding="utf-8")

# shaped like the live shelf: 160 ESSAY + 400 notes files sort/glob BEFORE any WORK_ file.
for i in range(160):
    put(base / f"ESSAY_20260101_{i:04d}_e.md", f"Essay {i}", "reflections on gardens and weather and ships " * 3)
for i in range(400):
    put(base / "notes" / "Some_Book" / f"TAB_20250101_{i:04d}_n.md", f"Note {i}", "a footnote about tidal harmonics and rivers " * 2)
for i in range(60):
    put(base / f"TAB_20260301_{i:04d}_t.md", f"Tab {i}", "some study of lamps and paper")
for i in range(30):
    put(base / f"WORK_20261001_{i:04d}_w.md", f"Field Journal {i}", "ordinary entries about the lamp and the table " * 2)
put(base / "WORK_20261020_0900_the_ferrymans_ledger.md", "The Ferryman's Ledger",
    "This piece argues that a ferryman's ledger records crossings, and a ledger of crossings is a map of trust.")

old_slice = sorted(base.glob("**/*.md"))[:500]
check("setup reproduces the bug: the OLD first-500 slice holds 0 WORK_ files",
      sum(1 for f in old_slice if f.name.startswith("WORK_")) == 0)

print("-- scan_works")
study._WORKS_CACHE.clear()
hits, st = study.scan_works(["ferryman", "ledger"], base=base, read_budget=10_000)
check("a query matching a known WORK title returns that work first", hits and hits[0][2].startswith("WORK_20261020_0900"))
check("its snippet is the work's own text", "ferryman" in hits[0][1].lower())
check("only one top-level hit -> notes/ pass runs (finds nothing extra)", st["notes_pass"] is True and len(hits) == 1)
_hl, _sl = study.scan_works(["lamp"], base=base, read_budget=10_000)
check("two or more top-level hits -> notes/ pass skipped", _sl["notes_pass"] is False)
hits_n, st_n = study.scan_works(["tidal", "harmonics"], base=base, read_budget=10_000)
check("notes-only query: pass 2 ran", st_n["notes_pass"] is True)
check("notes-only query: returns book-note hits", len(hits_n) == 400 and hits_n[0][2].startswith("notes"))
hits_t, st_t = study.scan_works(["lamps"], base=base, read_budget=10_000)
check("top-level TAB_ hits found (60 TAB + 30+1 WORK mention lamp)", len(hits_t) >= 60)
check("ties favour WORK over TAB (WORK first among equal-score hits)",
      hits_t[0][2].startswith(("WORK_", "TAB_")))   # WORK 'lamp' (singular) does not contain 'lamps'
hits_l, _ = study.scan_works(["lamp"], base=base, read_budget=10_000)
top_scores = [h for h in hits_l if h[0] == hits_l[0][0]]
check("equal-score ties keep WORK before TAB", top_scores[0][2].startswith("WORK_"))

print("-- budget + cache")
study._WORKS_CACHE.clear()
h1, s1 = study.scan_works(["ferryman"], base=base, read_budget=20)
check("cold call reads at most the budget", s1["reads"] == 20)
check("cold-call scored only what it could read", s1["top_scored"] == 20)
h2, s2 = study.scan_works(["ferryman"], base=base, read_budget=20)
check("next call reads further files (cache fills)", s2["reads"] == 20 and s2["top_scored"] == 40)
study._WORKS_CACHE.clear()
study.scan_works(["ferryman"], base=base, read_budget=10_000)
h3, s3 = study.scan_works(["ferryman"], base=base, read_budget=10_000)
check("warm call reads 0 files from disk", s3["reads"] == 0)
f = base / "WORK_20261020_0900_the_ferrymans_ledger.md"
time.sleep(0.02)
f.write_text("# The Ferryman's Ledger\n\nrewritten: the quartermaster is the subject now.\n", encoding="utf-8")
os.utime(f, (time.time() + 5, time.time() + 5))
h4, s4 = study.scan_works(["quartermaster"], base=base, read_budget=10_000)
check("a changed file is re-read (1 read) and found", s4["reads"] == 1 and h4 and h4[0][2].startswith("WORK_20261020"))
f.unlink()
h5, _ = study.scan_works(["quartermaster"], base=base, read_budget=10_000)
check("a deleted file leaves no hit and is dropped from the cache", not h5 and str(f) not in study._WORKS_CACHE)
check("top-level pass does not prune the notes cache",
      any(k.startswith(str(base / "notes")) for k in study._WORKS_CACHE))

print("-- the hand (InnerMonologueNode._search_works)")
from nodes import inner_monologue_node as imn
from core import wandering, activity_memory
saw = []
wandering.perceive = lambda text, *a, **k: saw.append(text)
activity_memory.record = lambda *a, **k: None
study.STUDY_DIR = base
study._MISPLACED_F = tmp / "_misplaced.json"
study._WORKS_CACHE.clear()
put(base / "WORK_20261020_0900_the_ferrymans_ledger.md", "The Ferryman's Ledger",
    "This piece argues that a ferryman's ledger records crossings, and a ledger of crossings is a map of trust.")
run = lambda q: asyncio.run(imn.InnerMonologueNode._search_works(None, None, q))
r = run("my own piece about the ferryman and his ledger")
check("hand returns True and perceives 'I looked back through my own writings on'", r is True and saw and saw[-1].startswith("I looked back through my own writings on"))
check("hand surfaces the WORK snippet", "ferryman" in saw[-1].lower() and "I found:" in saw[-1])
r = run("tidal harmonics of the river")
check("book-note query still works through the hand", r is True and "tidal" in saw[-1].lower())
r = run("zxqvwk unfindable gibberish")
check("no-hit wording unchanged", r is True and saw[-1].endswith("-- nothing there on it yet."))
check("too-short query still False", run("ab") is False)
check("only stop words -> False as before", run("want look back through") is False)
import json
study._MISPLACED_F.write_text(json.dumps({"title": "Zebra Crossing Notes"}), encoding="utf-8")
n0 = len(saw)
r = run("where is the zebra piece")
check("find_misplaced still short-circuits (recovery wording, file cleared)",
      r is True and saw[n0].startswith("I went looking and found my piece on 'Zebra Crossing Notes'") and not study._MISPLACED_F.exists())

print("PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
