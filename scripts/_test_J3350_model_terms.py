"""J-3350 (D-0629 part 2): model_terms detector, frontier additive field, ledger shadow. Temp stores only.

Run (from the worktree):  python scripts/_test_J3350_model_terms.py
"""
from __future__ import annotations
import json, pathlib, sqlite3, sys, tempfile, time, types

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                     # noqa: E402  (BEFORE lab_env)
assert str(pathlib.Path(core.__file__).resolve()).lower().startswith(str(ROOT).lower()), core.__file__
from core import model_terms as mt, frontier, epistemic_state as es   # noqa: E402

ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and bool(cond)
    print(("  ok   " if cond else "  FAIL ") + name)

tmp = pathlib.Path(tempfile.mkdtemp(prefix="J3350_"))
db = tmp / "mem.db"
c = sqlite3.connect(db)
c.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT, timestamp REAL, origin TEXT)")
T0 = 1_000_000.0
rows = [("a", "a long walk by the river with Galileo and the telescope", T0 + 1),
        ("b", "Mahler wrote symphonies; war was everywhere", T0 + 2),
        ("c", "Hugo Munsterberg wrote about film in 1916", T0 + 3)]
c.executemany("INSERT INTO memory_fragments VALUES (?,?,?, 'lived')", rows)
c.commit(); c.close()
idx = mt.FirstSeenIndex(db, tmp / "idx.json")
check("index builds", idx.refresh() == 3 and idx.first.get("galileo") == T0 + 1)
check("index cache saves under a temp path", idx.save() and (tmp / "idx.json").exists())
check("index reloads from cache", mt.FirstSeenIndex(db, tmp / "idx.json").first == idx.first)
c = sqlite3.connect(db); c.execute("INSERT INTO memory_fragments VALUES ('d','Kepler later',?, 'lived')", (T0 + 9,)); c.commit(); c.close()
check("incremental refresh reads only new rows", idx.refresh() >= 1 and "kepler" in idx.first)

ASOF = T0 + 100
d = lambda q, ctx="": mt.detect([q], ctx, ASOF, idx)
check("mottainai (quoted) is flagged", d("How does the idea of 'mottainai' shape how things are used?") == ["mottainai"])
check("omotenashi (mid-sentence capital) is flagged", "omotenashi" in d("Why does hospitality, Omotenashi, matter?"))
check("possessive name stripped, accents folded", d("What did Milošević's rivals think of Münsterberg's films?")[:1] == ["milosevic"] or "milosevic" in d("What did Milošević's rivals think?"))
check("older memory term is not flagged (Galileo, Mahler)", d("Why did Galileo and Mahler never meet?") == [])
check("accent-folded match against memory (Munsterberg)", d("What did Münsterberg say about film?") == [])
check("sentence-initial capital is not a candidate", d("Mottainai is a word. Why use it?") == [])
check("stop-list word not flagged (War)", "war" not in d("What caused the Great War in Europe?"))
check("term in the prompt context is not flagged", d("How does 'mottainai' work?", "study: mottainai is a concept") == [])
check("term first seen AFTER asof is flagged, before asof is not",
      mt.detect(["Why 'Kepler'?"], "", T0 + 5, idx) == ["kepler"] and mt.detect(["Why 'Kepler'?"], "", T0 + 50, idx) == [])
check("truncation join ('galileoin') not flagged", d("What about Galileoin the telescope?") == [])
check("TAG_ENABLED False -> []", (setattr(mt, "TAG_ENABLED", False), d("How does 'mottainai' work?"))[1] == [] and
      setattr(mt, "TAG_ENABLED", True) is None)
check("detect never raises (bad input)", mt.detect(None, None, ASOF, idx) == [])

# frontier: additive field, byte for byte without it
frontier._F = tmp / "frontier.json"
for nm in ("_F_LIGHT",):
    if hasattr(frontier, nm):
        setattr(frontier, nm, tmp / "frontier_light.json")
Q1, Q2 = "What explains the wonder of an unusual quiet harbour at dawn today?", "How might a patient weaver choose threads for a difficult winter cloak?"
e1 = frontier.note_question_ex(Q1, "curiosity")
e2 = frontier.note_question_ex(Q2, "curiosity", model_terms=["weaver"])
if e1 is None or e2 is None:
    check("frontier writes to the temp store (skipped: store fenced in this process)", False)
else:
    check("no model_terms kwarg -> no model_terms keys on the entry", "model_terms" not in e1 and "model_terms_ts" not in e1)
    check("with model_terms -> additive fields only", set(e2) - set(e1) == {"model_terms", "model_terms_ts"} and e2["model_terms"] == ["weaver"])
    check("empty model_terms behaves as absent", "model_terms" not in frontier.note_question_ex("How might a quiet monastery bell shape a very long afternoon walk?", "curiosity", model_terms=[]))
    check("frontier file is the temp one", (tmp / "frontier.json").exists())

# ledger shadow
es.MODEL_TERMS_LEDGER = True
es._MODEL_TERMS_SHADOW = tmp / "model_terms_shadow.jsonl"
check("flag default is False in source", "MODEL_TERMS_LEDGER = False" in (ROOT / "core" / "epistemic_state.py").read_text(encoding="utf-8"))
Frag = lambda origin, content, it=None: types.SimpleNamespace(origin=origin, content=content, input_type=it, label="")
def run(frags, raw=Q2, conf=0.8):
    st = types.SimpleNamespace(raw_input=raw, memory_fragments=frags, cycle_id="cyc1", input_type="internal",
                               reflection=types.SimpleNamespace(confidence=conf, draft=""), conversation_history=[],
                               recall=None, episodic_scene=None, executive=None)
    led = es.ProvenanceLedger()
    a = led._compute(st)
    led._model_terms_shadow(st, a)
    return a
a = run([])
rows = [json.loads(l) for l in (tmp / "model_terms_shadow.jsonl").read_text(encoding="utf-8").splitlines()]
check("uncorroborated question row logged (NO_BASIS at confidence >= 0.60)", len(rows) == 1 and rows[0]["would_grade"] == "NO_BASIS"
      and rows[0]["real_grade"] == a.grade and rows[0]["terms"] == ["weaver"] and rows[0]["narrated_confidence"] == 0.8)
check("real grade unchanged by the shadow", a.grade == run([]).grade)
n0 = len((tmp / "model_terms_shadow.jsonl").read_text(encoding="utf-8").splitlines())
run([Frag("reading", "A weaver at her loom")])
check("a reading fragment whose body carries the term corroborates -> no new row",
      len((tmp / "model_terms_shadow.jsonl").read_text(encoding="utf-8").splitlines()) == n0)
run([Frag("research", "[Looked up: 'X' (pursuit: a weaver question)] Nothing here")])
check("a research prefix that quotes the question does NOT corroborate -> row logged",
      len((tmp / "model_terms_shadow.jsonl").read_text(encoding="utf-8").splitlines()) == n0 + 1)
run([Frag("lived", "Travis said weaver", "human")])
check("a human lived turn corroborates", len((tmp / "model_terms_shadow.jsonl").read_text(encoding="utf-8").splitlines()) == n0 + 1)
es.MODEL_TERMS_LEDGER = False

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
