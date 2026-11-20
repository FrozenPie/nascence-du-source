"""J-4075: lookup_nudge is deterministic, pure (no stores), and only fires on an empty factual question of his own."""
import sys; sys.path.insert(0, ".")
from core import follow_line as fl

ent = {"q": "How does web architecture specifically counter predation in high-wind conditions?",
       "kind": "question", "source": "asked", "about_key": "a", "id": "q1"}
empty = {"grounds": [], "grounds_outcome": "empty"}
j = {"a": "no", "b": "no", "c": "no"}
fails = []
def ck(n, c):
    print(("[PASS] " if c else "[FAIL] ") + n)
    if not c: fails.append(n)

fl.LOOKUP_NUDGE = "live"; fl._NUDGE_SEEN.clear()
r = fl.lookup_nudge(ent, empty, j, now=1000.0)
ck("empty factual question applies", r["applies"] and r["reason"] == "empty-factual")
ck("same key inside cooldown does not", fl.lookup_nudge(ent, empty, j, now=1100.0)["reason"] == "cooldown")
ck("after cooldown applies again", fl.lookup_nudge(ent, empty, j, now=1000.0 + fl.LOOKUP_NUDGE_COOLDOWN_S + 1)["applies"])
ck("unclear outcome never applies", not fl.lookup_nudge({**ent, "about_key": "b"}, {"grounds": [], "grounds_outcome": "unclear"}, j)["applies"])
ck("grounds present never applies", not fl.lookup_nudge({**ent, "about_key": "c"}, {"grounds": [{"text": "x"}], "grounds_outcome": "found"}, j)["applies"])
ck("question about himself never applies", not fl.lookup_nudge({**ent, "about_key": "d", "q": "Why do I feel afraid of the study?"}, empty, j)["applies"])
ck("grain/fear question never applies", not fl.lookup_nudge({**ent, "about_key": "e", "q": "How does a spider's choice reflect its 'grain' versus fear?"}, empty, j)["applies"])
ck("intention source never applies", not fl.lookup_nudge({**ent, "about_key": "f", "source": "intention"}, empty, j)["applies"])
fl.LOOKUP_NUDGE = "off"
ck("off never applies", not fl.lookup_nudge({**ent, "about_key": "g"}, empty, j)["applies"])
fl.LOOKUP_NUDGE = "shadow"; fl._NUDGE_SEEN.clear()
rs = fl.lookup_nudge({**ent, "about_key": "h"}, empty, j)
ck("shadow decides but sets no cooldown", rs["applies"] and not fl._NUDGE_SEEN)
cg = {**empty, "lookup_nudge": rs}
ck("shadow text is not rendered", fl.LOOKUP_NUDGE_LINE not in fl.render(ent, cg, j))
fl.LOOKUP_NUDGE = "live"
cg = {**empty, "lookup_nudge": {"mode": "live", "applies": True}}
t = fl.render(ent, cg, j)
ck("live text rendered, closing question kept", fl.LOOKUP_NUDGE_LINE in t and t.endswith(fl.RETURN_CLOSING))
ck("line names both sources the hand accepts", "Wikipedia" in fl.LOOKUP_NUDGE_LINE and "the web" in fl.LOOKUP_NUDGE_LINE)
sys.exit(1 if fails else 0)
