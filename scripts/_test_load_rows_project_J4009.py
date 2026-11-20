"""J-4009 (F-4689): load_rows(project=True) is equivalent to legacy for everything downstream.
Decoupled check: legacy and projected rows are produced independently from the same file, then compared on
extract_regions (every row), _freeze_vector, dedupe_frozen_bursts, stick_test helpers, and census() output.
Usage: python scripts/_test_load_rows_project_J4009.py [path-to-geometry_tuples.jsonl] [--tail N] [--marginal]
Read-only on the source file; writes nothing but a temp copy."""
import sys, os, json, tempfile, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import mapping_census as mc, stick_test as st

args = [a for a in sys.argv[1:] if not a.startswith("--")]
src = pathlib.Path(args[0]) if args else ROOT / "data" / "geometry_tuples.jsonl"
tail = int(sys.argv[sys.argv.index("--tail") + 1]) if "--tail" in sys.argv else 0
if tail:
    lines = src.read_text(encoding="utf-8").splitlines()[-tail:]
    tmp = pathlib.Path(tempfile.mkdtemp()) / "t.jsonl"
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    src = tmp
mc._TUPLES = src
mc._LOG = pathlib.Path(tempfile.mkdtemp()) / "log.jsonl"   # never touch the live log

legacy = mc.load_rows(project=False)
proj = mc.load_rows(project=True)
assert len(legacy) == len(proj) > 0, (len(legacy), len(proj))
for a, b in zip(legacy, proj):
    assert mc.extract_regions(a) == mc.extract_regions(b)
    assert mc._freeze_vector(a) == mc._freeze_vector(b)
    assert a.get("ts") == b.get("ts") and a.get("source") == b.get("source")
    assert (a.get("thought") or "").strip() == (b.get("thought") or "").strip()
assert [r["ts"] for r in mc.dedupe_frozen_bursts(legacy)] == [r["ts"] for r in mc.dedupe_frozen_bursts(proj)]
assert (st._sound_context_index(legacy), st._book_context_index(legacy), st._cat_triple_count(legacy)) == \
       (st._sound_context_index(proj), st._book_context_index(proj), st._cat_triple_count(proj))
del legacy, proj

def run(flag):
    os.environ["NASCENCE_CENSUS_PROJECT"] = flag
    return mc.census(run_marginal_reach="--marginal" in sys.argv)
r0, r1 = run("0"), run("1")
assert json.dumps(r0, sort_keys=True, default=str) == json.dumps(r1, sort_keys=True, default=str), "census() differs"
r0d, r1d = (lambda f: (os.environ.__setitem__("NASCENCE_CENSUS_PROJECT", f), mc.census(run_marginal_reach=False, dedupe=True))[1])("0"), None
r1d = (os.environ.__setitem__("NASCENCE_CENSUS_PROJECT", "1"), mc.census(run_marginal_reach=False, dedupe=True))[1]
assert json.dumps(r0d, sort_keys=True, default=str) == json.dumps(r1d, sort_keys=True, default=str), "dedupe census() differs"
print("OK rows=%s marginal=%s" % (r0.get("rows"), "--marginal" in sys.argv))
