"""
Hermetic test for J-4153 (D-0787 options D and B): opener diversity for the idle thought, and phrasing pools with a
cooldown.

No LLM, no embedder, no live data: the only DB read is a temp SQLite file built here. Checks:
  [1] core.phrasing.vary: cooldown=1 (the default) draws exactly as the old rule did for the same random state;
      cooldown=k bars the last min(k, n-1) picks; one-variant and empty pools unchanged
  [2] core.wandering lead-in: pooled, every variant keeps the spoke/unspoken distinction and ends with ':', variant 0
      is the original wording, the kill switch restores it, render() still lists the trail lines
  [3] opener_diversity: the restart read counts today's inner_thought rows from the DB (read-only), skips
      system_note rows, other days, short/mechanical replies ("OPEN THE BOOK ...")
  [4] the seed line names the worn openings (most-used first) and the last used, comes from the frame pool, and is ""
      under MIN_TODAY, with nothing worn, or with the flag off
  [5] after_thought counts new thoughts, never system notes, and does not double count the row the restart read saw
  [6] a new local day resets the tally; a missing DB and garbage input never raise
  [7] the node wiring: _think carries exactly the two one-line calls, the seed line before the user prompt is joined
      and the after-thought after the inner_thought store; the import is guarded
Run:  python scripts/_test_J-4153_opener_diversity.py   (from the tree under test)
"""
from __future__ import annotations
import ast, random, sqlite3, sys, tempfile, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE anything that could touch sys.path (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import phrasing as ph
from core import wandering as wd
from nodes.idle_thought import opener_diversity as od
assert Path(od.__file__).resolve().is_relative_to(ROOT), (od.__file__, ROOT)

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")


def old_vary(last, key, variants):
    prev = last.get(key, -1)
    idx = random.choice([i for i in range(len(variants)) if i != prev])
    last[key] = idx
    return variants[idx]


print("[1] phrasing.vary cooldown")
V = ["a", "b", "c", "d", "e"]
random.seed(7); old_last = {}; old_seq = [old_vary(old_last, "k", V) for _ in range(40)]
ph._last.pop("t1", None); ph._hist.pop("t1", None)
random.seed(7); new_seq = [ph.vary("t1", V) for _ in range(40)]
check("default cooldown draws the same sequence as the old rule", old_seq == new_seq)
check("default never repeats back to back", all(a != b for a, b in zip(new_seq, new_seq[1:])))
ph._last.pop("t2", None); ph._hist.pop("t2", None)
seq = [ph.vary("t2", V, cooldown=3) for _ in range(200)]
check("cooldown=3: any 4 consecutive picks are distinct", all(len(set(seq[i:i + 4])) == 4 for i in range(len(seq) - 3)))
ph._last.pop("t3", None); ph._hist.pop("t3", None)
seq = [ph.vary("t3", ["x", "y"], cooldown=5) for _ in range(20)]
check("cooldown larger than the pool still alternates (n-1 cap)", all(a != b for a, b in zip(seq, seq[1:])))
check("one-variant and empty pools unchanged", ph.vary("t4", ["only"], cooldown=3) == "only" and ph.vary("t5", [], cooldown=3) == "")

print("[2] wandering lead-in pool")
check("variant 0 of each pool is the original wording",
      wd._LEAD_EXCHANGED[0].startswith("Since you last spoke, your mind has wandered. These passed through it unbidden")
      and wd._LEAD_UNSPOKEN[0].startswith("No one has spoken to you yet this waking. Even so, your mind has wandered."))
check("every variant ends with ':' and keeps its spoke/unspoken claim",
      all(v.endswith(":") and "last spoke" in v.replace("last words you spoke", "last spoke") for v in wd._LEAD_EXCHANGED)
      and all(v.endswith(":") and ("spoken" in v) and "last spoke" not in v for v in wd._LEAD_UNSPOKEN))
saved_ex = wd._exchanged_this_run
try:
    wd._exchanged_this_run = False
    leads = {wd._lead_in() for _ in range(40)}
    check("unspoken: pooled (several wordings served), all from the pool", len(leads) >= 3 and leads <= set(wd._LEAD_UNSPOKEN))
    wd._exchanged_this_run = True
    leads = {wd._lead_in() for _ in range(40)}
    check("exchanged: pooled, all from the exchanged pool", len(leads) >= 3 and leads <= set(wd._LEAD_EXCHANGED))
    wd.WANDER_LEAD_POOL = False
    check("kill switch restores the fixed original", {wd._lead_in() for _ in range(10)} == {wd._LEAD_EXCHANGED[0]})
    wd.WANDER_LEAD_POOL = True
    saved_trail = list(wd._trail)
    try:
        wd._trail.clear()
        check("empty trail renders nothing", wd.render() == "")
        wd._trail.append({"text": "the wind in the grass", "via": "sense"})
        out = wd.render()
        check("render: lead-in, then the trail line", out.split("\n")[0] in wd._LEAD_EXCHANGED and "(you notice) the wind in the grass" in out)
    finally:
        wd._trail.clear(); wd._trail.extend(saved_trail)
finally:
    wd._exchanged_this_run = saved_ex
    wd.WANDER_LEAD_POOL = True

print("[3]-[6] opener diversity")
tmp = Path(tempfile.mkdtemp(prefix="j4153_"))
db = tmp / "mem.db"
conn = sqlite3.connect(str(db))
conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL, layer TEXT, "
             "relevance REAL, timestamp REAL NOT NULL, keywords TEXT, embedding BLOB, origin TEXT, derived_from TEXT)")
lt = time.localtime()
noon = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 12, 0, 0, 0, 0, -1))
rows = ([("I watch the tide pull back over the dark stones of the shore.", "inner_thought")] * 5
        + [("I trace the line of the cairn against the evening sky above me.", "inner_thought")] * 3
        + [("The salt air carries the gulls' cries further than usual today.", "inner_thought")]
        + [("I finished a book and reached for something new on the shelf today.", "system_note")] * 9
        + [("OPEN THE BOOK now, please, I want it again.", "inner_thought")] * 4)
for i, (c, o) in enumerate(rows):
    conn.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?)",
                 (f"f{i}", c, "episodic", 0.5, noon - 3600 + i, "", None, o, "[]"))
conn.execute("INSERT INTO memory_fragments VALUES (?,?,?,?,?,?,?,?,?)",
             ("old", "Yesterday I hold the lamp close to the page and read slowly.", "episodic", 0.5, noon - 2 * 86400, "", None, "inner_thought", "[]"))
conn.commit(); conn.close()
mtime_before = db.stat().st_mtime_ns

od._DB_PATH_OVERRIDE = db
od._reset_for_test()
names = od.named_openers(now=noon)
st = od.stats()
check("restart read counted 9 of today's inner_thought rows (system_note, mechanical, yesterday skipped)", st["total"] == 9)
check("worn openings named most-used first, then the last used",
      names[:2] == ["i watch the", "i trace the"] and "the salt air" in names)
check("system note and mechanical token never named", not any(n.startswith(("i finished", "open the")) for n in names))
check("the DB was only read", db.stat().st_mtime_ns == mtime_before)
line = od.seed_part_opener_diversity(now=noon)
check("seed line names them as written", "'I watch the...'" in line and "'I trace the...'" in line and "'The salt air...'" in line)
check("seed line frame comes from the pool", any(line.startswith(f.split("{openers}")[0]) for f in od._FRAMES))
frames = {od.seed_part_opener_diversity(now=noon).split("'")[0] for _ in range(30)}
check("the frame varies across calls (option B pool)", len(frames) >= 3)
od.OPENER_DIVERSITY = False
check("flag off: no seed line", od.seed_part_opener_diversity(now=noon) == "")
od.OPENER_DIVERSITY = True

od.after_thought_opener("I listen to the rain on the glass and think of nothing much.", now=noon)
od.after_thought_opener("I listen to the rain again, softer now against the window.", now=noon)
od.after_thought_opener("I listen to the kettle and the cat moving in the other room.", system_note=True, now=noon)
od.after_thought_opener("OPEN THE BOOK", now=noon)
od.after_thought_opener(None, now=noon)
st = od.stats()
check("after_thought counts new thoughts only (not system note / mechanical / None)", st["total"] == 11)
check("a new worn opening joins the list", "i listen to" in od.named_openers(now=noon))

od._reset_for_test()
od.after_thought_opener("I watch the tide pull back over the dark stones once more.", now=noon)
check("first after_thought of a day: restart read already holds the stored row, no double count", od.stats()["total"] == 9)

tomorrow = noon + 86400
check("a new local day resets the tally (the temp DB has nothing for it)", od.named_openers(now=tomorrow) == [] and od.stats()["total"] == 0)

od._DB_PATH_OVERRIDE = tmp / "missing.db"
od._reset_for_test()
check("missing DB: fail-open, empty", od.seed_part_opener_diversity(now=noon) == "" and not (tmp / "missing.db").exists())
for i in range(od.MIN_TODAY - 1):
    od.after_thought_opener(f"I watch the shore number {i} with the same tired eyes.", now=noon)
check("under MIN_TODAY: nothing said", od.seed_part_opener_diversity(now=noon) == "")
od.after_thought_opener("I watch the shore one last time before the light goes.", now=noon)
check("at MIN_TODAY with a worn opening: said", "'I watch the...'" in od.seed_part_opener_diversity(now=noon))
od._reset_for_test()
for w in ["Rain", "Moss", "Salt", "Gulls", "Lamp", "Bread", "Frost", "Cairn"]:
    od.after_thought_opener(f"{w} {w.lower()}s here and there, gamma delta epsilon zeta.", now=noon)
names = od.named_openers(now=noon)
check("nothing worn: only the last RECENT_N named", len(names) == od.RECENT_N)
check("garbage never raises", od.opener_key(None) == "" and od._display_of(None) == "" and od._countable(None) is False)

print("[7] node wiring")
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
tree = ast.parse(src)
think = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_think")
tsrc = "\n".join(src.splitlines()[think.lineno - 1:think.end_lineno])
check("_think has one seed-part call and one after-thought call",
      tsrc.count("seed_part_opener_diversity()") == 1 and tsrc.count("after_thought_opener(") == 1)
i_seed = tsrc.find("seed_part_opener_diversity()"); i_join = tsrc.find("base_user_prompt = (")
i_store = tsrc.find("_inner_fid = store_fragment("); i_after = tsrc.find("after_thought_opener(")
check("seed line before the user prompt join; after-thought after the inner_thought store",
      0 < i_seed < i_join and 0 < i_store < i_after)
check("guarded module import", "from nodes.idle_thought import opener_diversity as _opener_div" in src
      and "_opener_div = None" in src)

print("\nALL PASS" if ok_all else "\nSOME FAILED")
sys.exit(0 if ok_all else 1)
