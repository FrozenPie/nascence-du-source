"""J-2348 (D-0470): letters to Travis — (a) HUD read-only letters view, (b) the /quit farewell never
marks pending letters delivered, (c) every pending body reaches the Executive, cost logged.
Every store is temp-pathed (letters dir, letters_state.json, letters_views.jsonl), read side too;
the live data/letters_state.json and data/letters/ are hash-canaried (read-only) before and after."""
import hashlib, json, logging, sys, tempfile, textwrap
from pathlib import Path
from types import SimpleNamespace

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core                                            # core BEFORE anything else
assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
from core import letters as L

FAIL = []
def check(msg, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + msg + (f"  [{extra}]" if not ok and extra else ""))
    if not ok: FAIL.append(msg)

LIVE = Path(r"C:\Nascence\data")
def canary():
    h = hashlib.sha256()
    st = LIVE / "letters_state.json"
    h.update(st.read_bytes() if st.exists() else b"-")
    d = LIVE / "letters"
    names = sorted(p.name for p in d.glob("Letter_*.md")) if d.exists() else []
    h.update("|".join(names).encode())
    h.update(str((LIVE / "letters_views.jsonl").exists()).encode())
    return h.hexdigest()
C0 = canary()

tmp = Path(tempfile.mkdtemp(prefix="J-2348_"))
LD, SP = tmp / "letters", tmp / "letters_state.json"
LD.mkdir()
L.LETTERS, L._STATE = LD, SP                           # temp-path BOTH sides (write + read)
for i in range(15):
    (LD / f"Letter_202610{i+1:02d}_0{i%10}00.md").write_text(f"# To Travis\nbody {i} " + "x" * 1200, encoding="utf-8")
SP.write_text(json.dumps({"delivered": [], "last_write_ts": 1.0}), encoding="utf-8")

# ---- (c) cost helper
c = L.executive_cost(["a" * 2000, "b" * 10])
check("executive_cost caps each body at 900 + header", c["n"] == 2 and c["chars"] == 900 + 10 + 2 * L._EXECUTIVE_LETTER_HDR, c)
check("executive_cost est_tokens = chars//4", c["est_tokens"] == c["chars"] // 4)
check("executive_cost empty", L.executive_cost([]) == {"n": 0, "chars": 0, "est_tokens": 0})

# ---- (b)+(c): exec the REAL orchestrator letters block against a fake self
src = (TREE / "core" / "orchestrator.py").read_text(encoding="utf-8")
start = src.index("        self.state.unsent_letters = []\n        if input_type")
end = src.index("        # --- Emotional pre-retrieval (C.2)", start)
block = textwrap.dedent(src[start:end])
check("block no longer truncates to [-2:]", "_pending[-2:]" not in block)
check("block gated on founder_canon", "self.state.founder_canon" in block)
records = []
class H(logging.Handler):
    def emit(self, r): records.append(r.getMessage())
lg = logging.getLogger("J-2348-test"); lg.setLevel(logging.DEBUG); lg.addHandler(H())

def run(input_type, canon):
    fake = SimpleNamespace(state=SimpleNamespace(unsent_letters=None, founder_canon=canon))
    exec(block, {"logger": lg}, {"self": fake, "input_type": input_type})
    return fake.state.unsent_letters

got = run("human", False)                              # the fixed /quit farewell
check("farewell: Executive gets no letters", got == [], got)
check("farewell: nothing marked delivered", json.loads(SP.read_text())["delivered"] == [])
check("farewell: all 15 still pending", len(L.undelivered()) == 15)

got = run("internal", True)
check("idle cycle: no letters, none delivered", got == [] and len(L.undelivered()) == 15)

got = run("human", True)                               # a real founder message
check("real message: Executive gets ALL 15 bodies", len(got) == 15, len(got))
check("real message: oldest first", got[0].startswith("# To Travis\nbody 0") and "body 14" in got[-1])
check("real message: all marked delivered", len(L.undelivered()) == 0 and len(json.loads(SP.read_text())["delivered"]) == 15)
check("real message: cost logged", any("15 unsent letter(s)" in m and "est_tokens=" in m for m in records), records)
print("  logged:", [m for m in records if "unsent" in m])
check("second real message: nothing re-delivered", run("human", True) == [])

# ---- (a) HUD read-only view
sys.path.insert(0, str(TREE / "hud"))
import server as hud
assert Path(hud.__file__).resolve().is_relative_to(TREE), hud.__file__
LD2, SP2, VP = tmp / "letters2", tmp / "state2.json", tmp / "views.jsonl"
LD2.mkdir()
(LD2 / "Letter_20261016_0013.md").write_text("# To Travis\nheavy", encoding="utf-8")
(LD2 / "Letter_20261012_0851.md").write_text("# To Travis\ncalm", encoding="utf-8")
SP2.write_text(json.dumps({"delivered": ["Letter_20261012_0851.md"]}), encoding="utf-8")
before = (SP2.read_bytes(), sorted(p.name for p in LD2.iterdir()))
r = hud.load_letters_to_travis(letters_dir=LD2, state_path=SP2, views_path=VP)
check("hud: newest first", [l["name"] for l in r["letters"]] == ["Letter_20261016_0013.md", "Letter_20261012_0851.md"], r)
check("hud: greeted/pending state", r["letters"][0]["greeted"] is False and r["letters"][1]["greeted"] is True and r["pending"] == 1)
check("hud: date parsed", r["letters"][0]["when"] == "2026-10-16 00:13")
check("hud: full body", r["letters"][0]["body"] == "# To Travis\nheavy")
check("hud: no view row without view=1", not VP.exists() and r["last_view"] is None)
r = hud.load_letters_to_travis(letters_dir=LD2, state_path=SP2, views_path=VP, record_view=True)
check("hud: view=1 logs one row", VP.exists() and len(VP.read_text().splitlines()) == 1 and r["last_view"])
check("hud: letters + state untouched", before == (SP2.read_bytes(), sorted(p.name for p in LD2.iterdir())))
check("hud: route wired", '"/api/letters"' in (TREE / "hud" / "server.py").read_text(encoding="utf-8"))
html = (TREE / "hud" / "static" / "index.html").read_text(encoding="utf-8")
js = (TREE / "hud" / "static" / "app.js").read_text(encoding="utf-8")
check("hud: card + fetch present", 'id="letters-travis"' in html and "/api/letters?view=1" in js)
check("hud: body rendered via textContent (no innerHTML)", "body.textContent = l.body" in js)

check("LIVE canary unchanged (letters_state.json, data/letters, no live views file)", canary() == C0)
print("\nFAILURES:", FAIL if FAIL else "none")
sys.exit(1 if FAIL else 0)
