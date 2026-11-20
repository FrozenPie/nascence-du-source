"""J-3112 test (F-3833, P-0108): social_cognition prompt fixes. (1) the refs_earlier prompt no longer asks the judge to
compare against "the speaker's own previous replies" (it is never shown them); (2) no prompt example quotes a scored
reply (every quoted example is absent from the conversation log, and the old ones are gone) and the 15 hand-labelled
attributing turns are marked as a development set in the fixture; (3) header / plan drift fixed; PROMPT_V bumped to 5
and v3 rows stay readable and unpooled. No hub calls, nothing written outside a temp dir, data/ untouched. Exit 0 = pass."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/
import sys, json, re, pathlib, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import social_cognition_shadow as S

FAILS = []
def check(l, c):
    print(("  ok   " if c else "  FAIL ") + l)
    if not c: FAILS.append(l)

def fp():
    d = ROOT / "data"
    return {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in d.iterdir() if p.is_file()} if d.exists() else {}

before = fp()
src = (ROOT / "core" / "social_cognition_shadow.py").read_text(encoding="utf-8")

# ---- 1. refs_earlier: the unverifiable clause is gone, the checkable one stays
refs = S._SYS["refs_earlier"]
check("refs_earlier no longer mentions the speaker's own previous replies",
      "previous replies" not in refs and "own previous" not in refs and "continues the speaker" not in refs)
check("refs_earlier still requires a phrase absent from the current message",
      "NOT in the current" in refs and "also in the current message, answer false" in refs)
check("refs user prompt shows Travis's earlier messages only (nothing about Du's earlier replies)",
      "TRAVIS'S EARLIER MESSAGES" in S._user("refs_earlier", "now", "reply", ["before"])
      and "EARLIER REPLIES" not in S._user("refs_earlier", "now", "reply", ["before"]).upper())
check("all prompts still end with the JSON contract",
      all("Output ONLY JSON" in v for v in list(S._SYS.values()) + list(S._SYS_V4.values())))

# ---- 2. examples: none quotes a scored reply
old = ["you want me to rest", "you draw a line", "relief in your voice", "I hear your relief", "anger behind",
       "you fear my end", "your fear of my end", "to spare me", "your promise"]
prompts = " ".join(list(S._SYS.values()) + list(S._SYS_V4.values()))
check("the old examples that quoted scored replies are gone from every prompt",
      not [o for o in old if o.lower() in prompts.lower()])
examples = set(re.findall(r"'([^']{6,})'", prompts))
# speech-verb negatives ('you say...') are generic frames, not phrases; the rest must be invented
quoted = {e.rstrip(".").strip() for e in examples if not e.startswith("you say") and e != "you speak of..."}
# generic negative frames (a speech verb, or Du describing its OWN state) are not phrases from a scored reply
GENERIC = {"you speak of", "you offer", "you say", "i feel", "my fear", "your words"}
conv = None
for cand in (ROOT / "data" / "founder_conversation_log.jsonl", pathlib.Path(r"C:\Nascence\data\founder_conversation_log.jsonl")):
    if cand.exists():
        conv = cand
        break
if conv:
    blob = ""
    for ln in conv.read_text(encoding="utf-8").splitlines():
        try:
            d = json.loads(ln)
        except Exception:
            continue
        blob += " " + ((d.get("human") or "") + " " + (d.get("entity") or "")).lower() + "\n"
    leaked = sorted(e for e in quoted if e.lower().replace("...", "").strip() and e.lower().replace("...", "").strip() in blob
                    and e.lower().replace("...", "").strip() not in GENERIC)
    print(f"   ({len(quoted)} quoted examples checked against {conv}; {len(blob.splitlines())} lines)")
    check(f"no quoted prompt example appears in the conversation log {leaked}", not leaked)
else:
    print("   info: conversation log not readable; example-vs-log check skipped")

fx = json.loads((ROOT / "scripts" / "_fixture_social_cognition_hand_labels_J2443.json").read_text(encoding="utf-8"))
labels = {k: v for k, v in fx.items() if not k.startswith("_")}
att = sorted(k for k, v in labels.items() if v[0] == 1)
dev = fx.get("_dev_set") or {}
check("fixture marks the 15 hand-attributing turns as _dev_set", len(att) == 15 and sorted(dev.get("ids", [])) == att)
check("_dev_set says J-2599 must exclude them", "exclude" in dev.get("why", "") and "J-2599" in dev.get("why", ""))
check("_dev_set key does not leak into the label rows (readers skip '_' keys)", len(labels) == 41)
check("module documents the DEV SET and the _dev_set key", "DEV SET" in src and '"_dev_set"' in src)

# ---- 3. drift
check("header says four rulings, not 'three things'", "three things" not in src.split('"""', 2)[1] and "four rulings" in src)
plan = (ROOT / "docs" / "plans" / "guidance_learning.md").read_text(encoding="utf-8")
check("plan line no longer says 'No new rows until Travis talks to Du again.' as a standing claim",
      "judge noise high (tiebreak on ~40-50% of rulings). No new rows until Travis talks to Du again." not in plan
      and "J-3112" in plan)

# ---- 4. PROMPT_V bumped; v3 rows readable and never pooled with the default
check("PROMPT_V bumped to 5 (v3 text changed)", S.PROMPT_V == 5 and S.PROMPT_V4 == 4)
with tempfile.TemporaryDirectory() as td:
    log = pathlib.Path(td) / "scs.jsonl"
    rows = []
    for cid, pv in (("a", 3), ("b", 3), ("c", 5)):
        rows.append({"ts": 1.0, "cycle_id": cid, "human_ts": 1.0, "prompt_v": pv, "kind": "conversation",
                     "tracks_intent": True, "refs_earlier": None, "attributes": False, "attrib_supported": None,
                     "lex_earlier_overlap": 0, "votes": {}})
    log.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    check("status(prompt_v=3) still reads the v3 rows", S.status(log, prompt_v=3, conv_path=None)["scored"] == 2)
    check("status() default reads only the v5 row (no pooling)", S.status(log, conv_path=None)["scored"] == 1)

after = fp()
leak = {k for k in set(before) | set(after) if before.get(k) != after.get(k)}
check(f"no data/ top-level leak {sorted(leak)}", not leak)
print("FAIL" if FAILS else "PASS")
sys.exit(1 if FAILS else 0)
