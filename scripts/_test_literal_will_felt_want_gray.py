"""J-2182 / D-0430 / F-2885: felt want + family verb on a GATED family -> GRAY, not DEED.
Pure classify() tests; no live data written. Run from the worktree: python scripts/_test_literal_will_felt_want_gray.py
Corpus gold check reads data/lab/literal_will/corpus.jsonl read-only if present (skipped otherwise)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
import core.literal_will as lw


def v(text, fam, loc="study"):
    r = [x for x in lw.classify(text, "", location=loc) if x["family"] == fam]
    return r[0]["verdict"] if r else "NONE"


fails = []
def check(name, got, want):
    ok = got == want
    print(("PASS " if ok else "FAIL ") + name, got)
    if not ok: fails.append(name)

# (a) felt want + verb reaching gated object -> GRAY
check("a felt+verb fire", v("the urge to tend the fire is strong, i will light the fire now", "fire"), "GRAY")
# (b) plain volition + verb still DEED; ungated family unaffected by felt want
check("b plain volition fire", v("i will light the fire now", "fire"), "DEED")
check("b ungated look stays DEED", v("the urge to tend the fire is strong, i will light the fire now", "look"), "DEED")
# (c) blockers still MUSING
check("c negation", v("the urge to light the fire, but i won't", "fire"), "MUSING")
check("c hypothetical", v("the urge to light the fire; if i were to light the fire it would warm me", "fire"), "MUSING")
# felt want w/o verb stays GRAY (weak), never DEED
check("felt no verb", v("my hands want the small ceremony of laying wood on the fire", "fire"), "GRAY")

# (d) retro corpus gold DEED rows
cp = ROOT.parent.parent.parent.parent / "x"  # placeholder, replaced below
for cand in (ROOT / "data/lab/literal_will/corpus.jsonl", Path(r"C:/Nascence/data/lab/literal_will/corpus.jsonl")):
    if cand.exists():
        cp = cand; break
if cp.exists():
    rows = [json.loads(l) for l in cp.read_text(encoding="utf-8").splitlines() if l.strip()]
    import subprocess, types
    head_src = subprocess.run(["git", "show", "HEAD:core/literal_will.py"], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout
    # HEAD may already include this change once committed -> compare against the pre-change parent instead
    if "D-0430 / F-2885 (J-2182)" in head_src:
        head_src = subprocess.run(["git", "show", "HEAD~1:core/literal_will.py"], cwd=ROOT, capture_output=True,
                                  text=True, encoding="utf-8", check=True).stdout
    old = types.ModuleType("core._lw_prechange"); old.__file__ = lw.__file__; old.__package__ = "core"
    sys.modules[old.__name__] = old
    exec(compile(head_src, old.__name__, "exec"), old.__dict__)
    gold = [c for c in rows if c["gold"] == "DEED"]
    for c in rows:
        a = [x for x in lw.classify(c["text"], "", location="study") if x["family"] == c["family"]]
        b = [x for x in old.classify(c["text"], "", location="study") if x["family"] == c["family"]]
        a = a[0]["verdict"] if a else "NONE"; b = b[0]["verdict"] if b else "NONE"
        if c["id"] in ("lw001", "lw009", "lw010", "lw011", "lw022", "lw024"):
            check(f"d gold DEED {c['id']} still DEED", a, "DEED")
        check(f"d corpus {c['id']} same as pre-change", a, b)
    print("corpus gold DEED rows:", len(gold))
else:
    print("SKIP corpus (not found)")

print("FAILS:", fails)
sys.exit(1 if fails else 0)
