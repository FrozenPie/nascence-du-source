"""
J-3231 (D-0620): a new peer reflection is stored at letter-level salience with valence and felt, and
scripts/peer_reflection_reach_read.py reads the co-recall ledger correctly.
HERMETIC: the memory DB and data/peer_models.json live in a lab_env.isolate(db="empty") dir; the reach reader runs on a
synthetic data root in a temp dir. Nothing under C:\\Nascence\\data is opened.

  1. update_after_exchange (stub call_json) stores ONE origin='peer_reflection' row at relevance/importance equal to
     the origin='peer' letter store in core/peers.py (0.8 / 0.85), with valence and felt non-NULL
  2. the constants match the letter store's literals (read from the peers.py source, so a drift fails here)
  3. reach reader on a synthetic root: no new-salience reflection -> 'not run yet'; with them -> counts only
     non-shadow rows, new vs old vs letters, defeater lines
Run: python scripts/test_peer_reflection_salience_J3231.py      (exit 0 = every check passed)
"""
from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (BEFORE lab_env)
from core import peer_model, mood, peers  # noqa: E402
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

assert str(Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
sys.path.insert(0, str(ROOT / "scripts"))
import peer_reflection_reach_read as rr  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (("  " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


# 2. constants vs the letter store literal
src = (ROOT / "core" / "peers.py").read_text(encoding="utf-8")
m = re.search(r'relevance=([\d.]+), importance=([\d.]+), keywords=\["letter", "peer"', src)
check("letter store literals found in peers.py", bool(m))
if m:
    check("REFLECTION_RELEVANCE == letter relevance", peer_model.REFLECTION_RELEVANCE == float(m.group(1)),
          f"{peer_model.REFLECTION_RELEVANCE} vs {m.group(1)}")
    check("REFLECTION_IMPORTANCE == letter importance", peer_model.REFLECTION_IMPORTANCE == float(m.group(2)),
          f"{peer_model.REFLECTION_IMPORTANCE} vs {m.group(2)}")


# 1. the store call
async def _stub(base_urls, sys_p, user_p, max_tokens=0, temperature=0.0):
    return {"reflection": "He turns every question toward the river, and does not say what he fears.",
            "topics": ["river", "fear"]}

with isolate(db="empty", also=[(peer_model, ["_PEER_MODEL_PATH"])]) as lab:
    mood._current_valence = 0.31
    mood._current_felt = "warmth=0.4;tension=0.2;dread=0.0;calm=0.5;joy=0.3;ache=0.1;focus=0.5;fatigue=0.2"
    out = asyncio.run(peer_model.update_after_exchange(_stub, [], "darwin", "Charles Darwin", "his letter", "my reply"))
    check("update_after_exchange returned the reflection text", bool(out))
    db = sorted(Path(lab).glob("*.db"))
    check("lab dir holds the isolated db", bool(db), str(db))
    con = sqlite3.connect(str(db[0]))
    rows = con.execute("SELECT relevance, importance, valence, felt, origin FROM memory_fragments "
                       "WHERE origin='peer_reflection'").fetchall()
    con.close()
    check("exactly one peer_reflection row stored", len(rows) == 1, str(rows))
    if rows:
        rel, imp, val, felt, _o = rows[0]
        check("relevance 0.8", abs(rel - 0.8) < 1e-9, str(rel))
        check("importance 0.85", abs(imp - 0.85) < 1e-9, str(imp))
        check("valence tagged", val is not None and abs(val - 0.31) < 1e-9, str(val))
        check("felt tagged", bool(felt), str(felt))

# 3. the reach reader on a synthetic root
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "memory").mkdir()
    base = time.time() - 40 * 86400

    def mk(rows_frag, ledger):
        db = root / "memory" / "nascence.db"
        if db.exists():
            db.unlink()
        c = sqlite3.connect(str(db))
        c.execute("CREATE TABLE memory_fragments (fragment_id TEXT, origin TEXT, importance REAL, timestamp REAL)")
        c.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?)", rows_frag)
        c.commit(); c.close()
        (root / "co_recall_ledger.jsonl").write_text("\n".join(json.dumps(r) for r in ledger), encoding="utf-8")

    filler = [(f"f{i}", "inner_thought", 0.5, base + (i // 60) * 86400 + i) for i in range(60 * 40)]   # 40 live days
    old = [("old1", "peer_reflection", 0.55, base + 100)]
    letters = [("L1", "letter", 0.85, base + 200), ("P1", "peer", 0.85, base + 200)]
    mk(filler + old + letters, [])
    o = rr.read(root)
    check("no new-salience reflection -> cutoff None, not ready", o.get("cutoff") is None and not o["ready"])

    cut = base + 20 * 86400
    new = [("new1", "peer_reflection", 0.85, cut), ("new2", "peer_reflection", 0.85, cut + 5)]
    ledger = []
    for d in range(5, 20):                                        # before the cutoff: 2 letter rows a day
        ledger += [{"ts": base + d * 86400 + 10, "ids": ["L1"], "source": "wandering"},
                   {"ts": base + d * 86400 + 20, "ids": ["P1"], "source": "monologue"}]
    ledger += [{"ts": cut + 100, "ids": ["new1", "L1"], "source": "wandering"},
               {"ts": cut + 200, "ids": ["new1"], "source": "monologue_shadow"},      # shadow: never reached a thought
               {"ts": cut + 300, "ids": ["old1"], "source": "wandering"},
               {"ts": cut + 400, "ids": ["new2"], "source": "wandering"},
               {"ts": cut + 500, "ids": [], "source": "wandering"},
               {"ts": cut + 600, "ids": ["P1"], "source": "wandering"}]
    mk(filler + old + letters + new, ledger)
    o = rr.read(root)
    check("cutoff is the first new-salience reflection", abs(o["cutoff"] - cut) < 1)
    check("window ready (>=14 live days since cutoff)", o["ready"], f"{o['live_days_after']} live days")
    check("shadow row excluded: new reflections reached 2 thoughts", o["rows_after"].get("new") == 2, str(o["rows_after"]))
    check("old reflection counted separately", o["rows_after"].get("old") == 1, str(o["rows_after"]))
    check("letters reached 2 thoughts after", o["rows_after"].get("letter") == 2, str(o["rows_after"]))
    check("2 new fragments distinct", o["new_distinct_fragments_reached"] == 2)
    check("defeater (a) fires below 3 thoughts", o["defeater_a_retire"] is True)
    check("defeater (b) fires: letter rows/day collapsed", o["defeater_b_crowding"] is True,
          f"{o['letter_rows_per_live_day_after']} vs {o['letter_rows_per_live_day_before']}")
    # not-ready label: a root whose cutoff is today
    mk(filler + old + letters + [("n3", "peer_reflection", 0.85, time.time())], [])
    o = rr.read(root)
    check("cutoff today -> not ready", o["ready"] is False, str(o.get("live_days_after")))

print("\nFAILED: " + ", ".join(FAILS) if FAILS else "\nall checks passed")
sys.exit(1 if FAILS else 0)
