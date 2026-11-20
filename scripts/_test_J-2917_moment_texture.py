"""J-2917 (F-3614): moment.texture() carries no raw gauge digits and no mid-word cuts. Temp dir only; no live data."""
import sys, re, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core before lab_env)
from core import moment  # noqa: E402
assert Path(moment.__file__).resolve().parent.parent == ROOT, moment.__file__

tmp = Path(tempfile.mkdtemp())
moment._LOG = tmp / "moments.jsonl"; moment._STATE = tmp / "moment_state.json"

# 1. words-only felt, from the exact stored shape seen in data/moments.jsonl
w = moment._felt_in_words("unsettled: valence=-0.20 arousal=0.43 joy=1.00 fear=0.06 tru")
assert w and not re.search(r"\d|valence|arousal", w), w
assert w.startswith("unsettled"), w
assert moment._felt_in_words("glad: valence=0.8") == "glad", moment._felt_in_words("glad: valence=0.8")  # arousal missing -> label only
assert moment._felt_in_words({"valence": 0.9, "joy": 0.5, "fear": 0.1}) == "joy"
assert moment._felt_in_words("") is None

# 2. word-boundary clip
c = moment._clip_words("working through 'The Life of the Fly With Which are Interspersed with remarks'", 60)
assert len(c) <= 61 and c.endswith("\u2026") and not c[:-1].endswith("Interspe"), c
assert moment._clip_words("short text", 60) == "short text"
assert moment._clip_words("alpha beta gamma", 10) == "alpha\u2026" or moment._clip_words("alpha beta gamma", 10).startswith("alpha"), moment._clip_words("alpha beta gamma", 10)
assert moment._clip_words("abcdefghij klm", 10) == "abcdefghij\u2026"  # exact word end: no backing up

# 3. texture() end to end with a stubbed recall
anchor = {"affect": {"valence": -0.2, "felt": "unsettled: valence=-0.20 arousal=0.43 joy=1.00 fear=0.06 tru"},
          "concern": "pursuing: How does the family structure of cliff swallows influence colony survival rates",
          "thought": "x"}
nb = [{"thought": "The cliff swallow colony was loud this morning and the nests along the rock face were crowded with returning birds again today"}]
moment.recall = lambda cue, *a, **k: {"anchor": anchor, "neighbours": nb}
t = moment.texture("anything")
assert t and "you felt unsettled" in t, t
assert not re.search(r"valence=|arousal=|\d\.\d", t), t
print(t.encode('ascii','replace').decode())
# no half word: every fragment's last token (before the ellipsis) is a whole word from the source
src = anchor["concern"] + " " + nb[0]["thought"]
for frag in re.findall(r'holding: ([^;]+);', t) + re.findall(r'"([^"]+)"', t):
    last = frag.rstrip("\u2026").split()[-1]
    assert last in src.split(), (last, frag)
print("J-2917 OK")
