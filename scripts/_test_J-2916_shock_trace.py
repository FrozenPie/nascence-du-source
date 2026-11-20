"""J-2916 test: scripts/j2916_shock_trace.py on a synthetic store. Builds a temp DB (memory_fragments / memory_edges /
memory_links) and temp data files, runs the analysis against them, and asserts the by-id and lexical counts. Runs
from the worktree; asserts its own tree; touches no live data (all paths point at a temp dir); no model is called."""
import contextlib
import io
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass
assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
sys.path.insert(0, str(TREE / "scripts"))
import j2916_shock_trace as T  # noqa: E402
assert Path(T.__file__).resolve().is_relative_to(TREE)

tmp = Path(tempfile.mkdtemp(prefix="j2916_"))
end = time.time()
DAY = 86400.0
db = tmp / "nascence.db"
c = sqlite3.connect(db)
c.execute("create table memory_fragments (fragment_id text, content text, layer text, relevance real, timestamp real, "
          "keywords text, origin text, importance real, derived_from text, replay_count integer)")
c.execute("create table memory_edges (edge_id integer, src_kind text, src_id text, dst_kind text, dst_id text, "
          "edge_type text, weight real, provenance text, created real)")
c.execute("create table memory_links (parent_id text, child_id text, link_type text, weight real, created real)")


def frag(fid, ts, origin, content, imp=0.8, replay=0, df="[]"):
    c.execute("insert into memory_fragments values (?,?,?,?,?,?,?,?,?,?)",
              (fid, content, "episodic", 0.8, ts, "", origin, imp, df, replay))


t0 = end - 10 * DAY
# one shock (cited later by a T2 synthesis), one pursuit-fetched control (never cited), filler reading rows
frag("S1", t0, "research", "[Looked up: 'Zanzibar Quillwort' (external shock \u2014 uninvited)] A rare quillwort of Zanzibar marshes.", replay=1)
frag("C1", t0 + 3 * DAY, "research", "[Looked up: 'Gravity' (pursuit: x)] Gravity is a force.")
for k in range(10):
    frag(f"R{k}", t0 + 600 * (k + 1), "reading", f"passage {k} about rivers")
frag("T2a", t0 + 900, "subconscious_synthesis", "The Zanzibar Quillwort lands on my floor like an uninvited guest.",
     df=json.dumps(["shadow-event-1"]))
frag("T2b", t0 + 5 * DAY, "subconscious_synthesis", "Nothing relevant here at all.")
for k in range(3000):   # background so document-frequency filtering has a corpus
    frag(f"I{k}", t0 + 7 * DAY + k * 10, "inner_thought", f"the tide and the stone {k}")
c.execute("insert into memory_edges values (1,'fragment','C1','question','Q1','answers',1.0,'x',0)")
c.commit()
c.close()
(tmp / "deliberation_log.jsonl").write_text(json.dumps({"ts": t0 + 1000, "about": "x", "raw": "zanzibar quillwort again"}) + "\n", encoding="utf-8")
(tmp / "curiosity_log.jsonl").write_text(json.dumps({"id": "a", "ts": t0 + 1200, "questions": ["What is a Zanzibar Quillwort?"], "seeds_offered": ["unresolved: name"]}) + "\n", encoding="utf-8")
(tmp / "pursuits_shadow.jsonl").write_text("", encoding="utf-8")
(tmp / "pursuits_active.json").write_text("[]", encoding="utf-8")
(tmp / "nascence.log").write_text("", encoding="utf-8")

out = tmp / "out"
sys.argv = ["j2916", "--db", str(db), "--data", str(tmp), "--out", str(out), "--days", "30"]
with contextlib.redirect_stdout(io.StringIO()):
    T.main()
r = json.loads((out / "shock_trace_results_30d.json").read_text(encoding="utf-8")) if (out / "shock_trace_results_30d.json").exists() \
    else json.loads((out / "shock_trace_results.json").read_text(encoding="utf-8"))
assert r["n_shock"] == 1 and r["n_control"] == 1, (r["n_shock"], r["n_control"])
assert r["lexical_shock"]["T2"]["post"]["total"] == 1, r["lexical_shock"]["T2"]
assert r["lexical_shock"]["T2"]["pre"]["total"] == 0
assert r["lexical_shock"]["curiosity"]["post"]["total"] == 1
assert r["lexical_shock"]["curiosity_seeds"]["post"]["total"] == 0
assert r["lexical_shock"]["deliberation"]["post"]["total"] == 1
assert r["lexical_control_all"]["T2"]["post"]["total"] == 0
# by-id: derived_from names a shadow event, not the fragment; the shock has no edges; the control has one
assert r["id_level_shock"]["fragments_with_derived_child"] == 0
assert r["id_level_shock"]["replay_fragments"] == 1 and r["id_level_control"]["replay_fragments"] == 0
assert r["id_level_control"]["edges"] == {"answers->question": 1}, r["id_level_control"]["edges"]
# feed reconstruction: 10 newer reading rows + the control => the shock is in the newest-6 feed only for 6 newer rows;
# T2a is written 900 s after S1, after R0..R0 (600 s) => inside the feed; cite per exposure counted
fe = r["feed_exposure"]["shock"]["T2_top6"]
assert fe["exposures"] >= 1 and fe["cites"] == 1, fe
assert r["tests_fisher_one_sided"]["T2 fragments cited >=1 (shock vs control)"]["shock"] == "1/1"
# only the window's own files were written, all under the temp dir
assert all(p.resolve().is_relative_to(tmp) for p in out.iterdir())
print("OK J-2916 shock trace test")
