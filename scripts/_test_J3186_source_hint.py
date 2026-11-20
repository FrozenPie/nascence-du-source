"""J-3186 / D-0573: narrowed source-code hint. Reads only; a replay (optional, argv[1] = a COPY of
deliberation_log.jsonl) reports survival counts. Writes nothing."""
import sys, json, time, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (core before lab_env)
from core import source_sight as ss
import core.left_lane as ll

# --- unit assertions
assert ss.is_self_mechanism("my memory is long") and not ss.is_self_mechanism_narrow("my memory is long")

assert ss.is_self_mechanism_narrow("the river and the shadow")
assert ss.is_self_mechanism_narrow("a loop of tension")
assert ss.is_self_mechanism_narrow("my loop returns")             # one non-generic term
assert not ss.is_self_mechanism_narrow("the shadow of the wall")  # one generic term
assert not ss.is_self_mechanism_narrow("")
# old API untouched
assert ss.is_self_mechanism("the shadow of the wall") and ss.see_code.__module__ == "core.source_sight"
assert ss.hit_shares_content_word("the lantern in my memory", {"file": "core/lantern_room.py", "line": "x"})
assert ss.hit_shares_content_word("the lanterns and the loop", {"file": "core/x.py", "line": "# the lantern burns while the loop runs on"})
assert not ss.hit_shares_content_word("a tension about waiting", {"file": "core/affections.py", "line": "T2 fires only on a tension cluster"})
assert not ss.hit_shares_content_word("the shadow of the tide", {"file": "core/actions.py", "line": "# the shadow function was lost steeply"})
assert ll.GROUND_CODE_HINT_NARROW is True
print("unit ok; tree:", ROOT)

if len(sys.argv) > 1:
    cutoff = time.time() - 30 * 86400
    n = flag_old = flag_new = hit_old = hit_new = 0
    old_files = {}; new_files = {}
    for line in open(sys.argv[1], encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("source") != "emissary" or r.get("ts", 0) < cutoff or not r.get("raw"):
            continue
        n += 1
        raw = r["raw"]
        if ss.is_self_mechanism(raw):
            flag_old += 1
            h = ss.see_code(raw, k=1)
            if h:
                hit_old += 1; old_files[h[0]["file"]] = old_files.get(h[0]["file"], 0) + 1
        if ss.is_self_mechanism_narrow(raw):
            flag_new += 1
            h = ss.see_code_narrow(raw, k=1)
            if h:
                hit_new += 1; new_files[h[0]["file"]] = new_files.get(h[0]["file"], 0) + 1
    print(f"thoughts={n} old: flagged={flag_old} hits={hit_old} | new: flagged={flag_new} hits={hit_new}")
    top = lambda d: sorted(d.items(), key=lambda x: -x[1])[:8]
    print("old top files:", top(old_files)); print("new top files:", top(new_files))
    for f in ("core/actions.py", "core/book_feelings.py"):
        print(f"{f}: old {old_files.get(f,0)} -> new {new_files.get(f,0)}")
