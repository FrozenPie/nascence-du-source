"""
Hermetic test: scripts/chapter_id_repair_batch.py -- the D-0350 Origin exclusion in chapter_id clear-batch
selection (J-1837), plus the identity-kept guard and the F-1360 rule it sits on.

  [1] fixtures: a temp SQLite DB with the Origin pair (over-matcher O finished, victim V 3.6% read), the F-1615
      About-You pair, and a magnet gist; [2] F-1360 rule reproduces the known shapes; [3] the 26-style V-tagged
      rows are excluded from EVERY batch (T=V, T=O, T=an unrelated accepting subject), logged by id + tag;
      [4] identity-kept: O's own long-tag rows behind O's gist are not "misfiled" for T=V, while the About-You-
      Second-Edition rows behind the generic About-You gist still ARE (D-0221's first batch stays repairable);
      [5] mismatch + NULL-exposure flags; [6] read-only: the whole thing runs on a mode=ro connection and the
      module defines no data/ path; [7] canary: live stores untouched.

  python scripts/_test_chapter_id_repair_batch.py        # exit 0 = ALL OK; run FROM a worktree, never C:\\Nascence
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import uuid
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def _snap(p: Path):
    if not p.exists():
        return None
    st = p.stat()
    return (st.st_size, int(st.st_mtime_ns))


_LIVE = [Path(r"C:\Nascence\data\memory\nascence.db"), Path(r"C:\Nascence\data\memory\nascence.db-wal"),
         Path(r"C:\Nascence\data\world_consolidation_log.jsonl"), Path(r"C:\Nascence\data\satisfaction_log.jsonl"),
         Path(r"C:\Nascence\data\satisfaction_state.json"), Path(r"C:\Nascence\data\reading_state.json")]
_before = {p: _snap(p) for p in _LIVE}

import core                                           # noqa: E402  (BEFORE anything else -- F-2423)
check(Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from the tree under test ({core.__file__})")
import scripts.chapter_id_repair_batch as B           # noqa: E402
from core.world_consolidation import _cites           # noqa: E402

check(Path(B.__file__).resolve().is_relative_to(ROOT), "module under test is the worktree copy")
src = Path(B.__file__).read_text(encoding="utf-8")
check("__file__).parent.parent / \"data\"" not in src and "UPDATE " not in src.replace("``UPDATE memory_fragments SET chapter_id=NULL``", ""),
      "module has no data/ path constant and no UPDATE statement (selection only)")

O = B.ORIGIN_OVER_MATCHER_SUBJECT                     # 'On the Origin of Species by Means of Natural Selec'
V = B.ORIGIN_VICTIM_SUBJECT                           # 'The Origin of Species by Means of Natural Selectio'
O_LONG = "On the Origin of Species by Means of Natural Selection or th"      # the finished book's reading tag (60)
V_LONG = "The Origin of Species by Means of Natural Selection Or the P"      # the second book's reading tag (60)
check(_cites(O, f"[Reading — from '{V_LONG}'] x") and _cites(V, f"[Reading — from '{O_LONG}'] x"),
      "fixture reproduces F-2413: O accepts V's tags AND V accepts O's long tag (the asymmetric over-match)")
check(_cites(O, f"[x from '{V}'] y") and not _cites(V, f"[x from '{O}'] y"), "C(O,V) True, C(V,O) False (F-2160)")

TMP = Path(tempfile.mkdtemp(prefix="j1837_batch_"))
DB = TMP / "t.db"
rows: list[tuple] = []          # (fragment_id, origin, content, chapter_id)
gists: dict[str, str] = {}


def gist(tag, kind="understanding"):
    fid = str(uuid.uuid4())
    word = "from" if kind == "understanding" else "on"
    rows.append((fid, kind, f"[{kind.title()} — {word} '{tag}'] body about {tag}", None))
    gists[tag] = fid
    return fid


def frag(tag, chapter, n=1, origin="reading"):
    out = []
    for _ in range(n):
        fid = str(uuid.uuid4())
        rows.append((fid, origin, f"[Reading — from '{tag}'] excerpt {fid[:6]}", chapter))
        out.append(fid)
    return out


g_O = gist(O); g_V = gist(V); g_wild = gist("Wild Animals I Have Known"); g_magnet = gist("The Sky Is Falling", "essay")
g_about = gist("About You", "essay"); g_about2 = gist("About You Second Edition", "essay"); g_birds = gist("Indian Birds")
# The Origin pair as it is live (F-2413 / J-1837 census): V-tagged rows filed behind V's gist (the 26-shape),
# O's long-tag rows behind O's gist (identity), some O long-tag rows misfiled behind a magnet, plus V-tagged
# rows wrongly filed behind the magnet AND two UNFILED ones (the hazard states the exclusion must cover).
v_behind_v = frag(V_LONG, g_V, 24) + frag(V, g_V, 2)
o_behind_o = frag(O_LONG, g_O, 30)
o_exact_behind_o = frag(O, g_O, 3)      # tag == O: V's test does NOT accept it (C(V,O) False), never even flagged
o_behind_wild = frag(O_LONG, g_wild, 5)
v_behind_magnet = frag(V_LONG, g_magnet, 3)
v_null = frag(V_LONG, None, 2)
# F-1615: About You Second Edition rows behind the generic About You gist (must stay repairable) and behind Indian Birds.
ay2_behind_ay = frag("About You Second Edition", g_about, 4)
ay2_behind_birds = frag("About You Second Edition", g_birds, 2)
ay_behind_ay = frag("About You", g_about, 6)
# A smart-cut gist tag (D-0256 write side): the gist tag is the word-boundary cut of the long reading tag.
LONG_T = "Knots Splices and Rope Work A Practical Treatise Giving Comp"
g_knots = gist("Knots Splices and Rope Work A Practical Treatise")
knots_behind_own = frag(LONG_T, g_knots, 3)

with sqlite3.connect(DB) as w:
    w.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, origin TEXT, content TEXT, chapter_id TEXT)")
    w.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?)", rows)
    w.commit()

conn = B.open_ro(DB)
try:
    conn.execute("UPDATE memory_fragments SET chapter_id=NULL")
    ro_refused = False
except sqlite3.OperationalError:
    ro_refused = True
check(ro_refused, "[6] open_ro() refuses a write at the driver level")

logged: list[str] = []
print("[2]/[3] T = V (the victim subject)")
rep_v = B.select_clear_batch(conn, V, log=logged.append)
ids_v = {r["fragment_id"] for r in rep_v["batch"]}
ex_v = {r["fragment_id"] for r in rep_v["origin_excluded"]}
id_v = {r["fragment_id"] for r in rep_v["identity_kept"]}
check(rep_v["already_correct"] == 26, f"F-1360: the 26 V-tagged rows behind V's gist are already-correct ({rep_v['already_correct']})")
check(set(v_behind_magnet) <= ex_v and not (set(v_behind_magnet) & ids_v), "V-tagged rows behind the magnet are flagged misfiled but ORIGIN-EXCLUDED, not in the batch")
check(set(o_behind_o) <= id_v and not (set(o_behind_o) & ids_v), "[4] O's own long-tag rows behind O's gist: identity-kept, not in V's batch")
check(not (set(o_exact_behind_o) & (ids_v | id_v | ex_v)), "O's exact-tag rows are not flagged for T=V at all (C(V,O) False)")
check(set(o_behind_wild) <= ids_v, "O's long-tag rows behind Wild Animals ARE in the batch (genuinely misfiled, V's test accepts them)")
check(ids_v == set(o_behind_wild), f"batch for T=V is exactly those {len(o_behind_wild)} rows (got {len(ids_v)})")
check(len(ex_v) == 3 and all(r["tag"].startswith(V) for r in rep_v["origin_excluded"]), "origin_excluded carries fragment_id + tag for each excluded row")
check(any("EXCLUDED (D-0350 origin)" in ln for ln in logged) and sum("EXCLUDED (D-0350 origin)" in ln for ln in logged) == 3, "exclusions are logged, one line per fragment")
check(rep_v["origin_population"]["origin_tagged_total"] == 31 and rep_v["origin_exclusion_mismatch"], "[5] mismatch flag: fixture has 31 V-tagged rows, expected constant is 26")
check(rep_v["origin_population"]["origin_tagged_null_chapter"] == 2 and rep_v["origin_null_chapter_exposed"], "[5] NULL-exposure flag fires on the 2 unfiled V-tagged rows (D-0350 defeater)")
check(any("WARNING" in ln and "UNFILED" in ln for ln in logged), "NULL exposure is logged as a WARNING")

print("[3] T = O (the over-matcher)")
logged.clear()
rep_o = B.select_clear_batch(conn, O, log=logged.append)
ids_o = {r["fragment_id"] for r in rep_o["batch"]}
check(rep_o["already_correct"] == 33 + 26, f"O's test accepts V's tags: V-behind-V rows count as already-correct for T=O too ({rep_o['already_correct']})")
check(set(v_behind_magnet) <= {r["fragment_id"] for r in rep_o["origin_excluded"]} and not (set(v_behind_magnet) & ids_o),
      "V-tagged rows behind the magnet are ORIGIN-EXCLUDED from O's batch as well (title-independent)")
check(ids_o == set(o_behind_wild), "O's batch = the 5 misfiled O rows only")

print("[3] T = an unrelated subject whose test happens to accept V's tag")
conn.close()
g_species = gist("Species Means")        # signature {species, means} subset of V's -> accepts V's tags
rows_extra = [(str(uuid.uuid4()), "reading", f"[Reading — from 'Species Means'] x", g_wild)]
with sqlite3.connect(DB) as w:
    w.execute("INSERT INTO memory_fragments VALUES (?,?,?,?)", (g_species, "understanding", f"[Understanding — from 'Species Means'] body", None))
    w.executemany("INSERT INTO memory_fragments VALUES (?,?,?,?)", rows_extra)
    w.commit()
conn = B.open_ro(DB)
rep_s = B.select_clear_batch(conn, "Species Means", log=None)
check(_cites("Species Means", f"[x from '{V_LONG}'] y"), "fixture: 'Species Means' accepts V's long tag")
check(not ({r["fragment_id"] for r in rep_s["batch"]} & (set(v_behind_magnet) | set(v_behind_v))),
      "no V-tagged row reaches the batch of an unrelated accepting subject either")
check(set(v_behind_magnet) <= {r["fragment_id"] for r in rep_s["origin_excluded"]}, "...they are reported as origin_excluded there too")

print("[4] F-1615 About You pair stays repairable")
rep_ay2 = B.select_clear_batch(conn, "About You Second Edition", log=None)
ids_ay2 = {r["fragment_id"] for r in rep_ay2["batch"]}
check(ids_ay2 == set(ay2_behind_ay) | set(ay2_behind_birds), f"T='About You Second Edition': all 6 misfiled rows selected, incl. the 4 behind the generic 'About You' gist ({len(ids_ay2)})")
check(rep_ay2["identity_kept_count"] == 0 and rep_ay2["origin_excluded_count"] == 0, "no exclusion fires on the About You pair")
rep_ay = B.select_clear_batch(conn, "About You", log=None)
check({r["fragment_id"] for r in rep_ay["batch"]} == set(ay2_behind_birds), "T='About You' (generic): its test accepts the Second-Edition rows; only those behind Indian Birds are misfiled; the 6 'About You' rows behind 'About You' are correct")
check(B.is_identity_of("About You Second Edition", "About You") is False, "is_identity_of: a shorter prefix title is NOT an identity")
check(B.is_identity_of(O_LONG, O) and B.is_identity_of(V_LONG, V) and B.is_identity_of(V, V), "is_identity_of: equal / hard [:50] cut")
check(B.is_identity_of(LONG_T, "Knots Splices and Rope Work A Practical Treatise"), "is_identity_of: word-boundary (_smart_cut) gist tag")
rep_k = B.select_clear_batch(conn, "Knots Splices and Rope Work A Practical Treatise", log=None)
check(rep_k["batch_size"] == 0 and rep_k["already_correct"] == 3, "smart-cut gist: its own rows are already-correct under F-1360 (no identity guard needed)")
check(B.is_origin_excluded(V_LONG) and B.is_origin_excluded(V) and not B.is_origin_excluded(O_LONG) and not B.is_origin_excluded(""),
      "is_origin_excluded: V-prefix tags only, never O's, never empty")

print("[6] apply_exclusions is pure and order-preserving")
sample = [{"fragment_id": "a", "tag": V_LONG, "gist_tag": "x"}, {"fragment_id": "b", "tag": O_LONG, "gist_tag": O},
          {"fragment_id": "c", "tag": "Zed", "gist_tag": "Other"}]
k, e, i = B.apply_exclusions(sample)
check([r["fragment_id"] for r in k] == ["c"] and [r["fragment_id"] for r in e] == ["a"] and [r["fragment_id"] for r in i] == ["b"], "split is correct")

print("[CLI]")
out = TMP / "rep.json"
rc = B.main(["--db", str(DB), "--title", V, "--title", O, "--out", str(out), "--quiet"])
j = json.loads(out.read_text(encoding="utf-8"))
check(rc == 0 and j["total"]["titles"] == 2 and j["total"]["origin_excluded_total"] == 6 and j["total"]["origin_exclusion_mismatch"], "CLI writes the full report with totals + mismatch flag")
check(all("fragment_id" in r and "tag" in r for rep in j["reports"] for r in rep["origin_excluded"]), "report lists every excluded id with its tag")

conn.close()
shutil.rmtree(TMP, ignore_errors=True)

print("[7] canary")
_after = {p: _snap(p) for p in _LIVE}
check(_after == _before, "live stores untouched (size + mtime of DB/WAL/logs/reading_state)")

print("\nRESULT:", "ALL OK" if FAILS == 0 else f"{FAILS} FAIL")
sys.exit(1 if FAILS else 0)
