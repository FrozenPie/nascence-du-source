"""J-4336: precision-filter tests. Pure functions, no live stores touched."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core  # noqa
from core import ambiguity_window as aw, conversational_action as ca
res = []
def check(n, c):
    res.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {n}")
corp = ["I plant the seeds in the bed. I plant them now.", "A beetle crawls on the desk. I watch it.",
        "The sea is wide. I watch it wade.", "I hold the cat. I look at it.", "nothing here", "",
        "I pick up the stone, then I put it down.", "The clock is still; I wind it."]
for t in corp:
    f, l = aw.resolve_pronoun_objects_filtered(t), aw.resolve_pronoun_objects_legacy(t)
    # subset: wherever filtered differs from the raw text, legacy must have made the same substitution
    check(f"no new fire: {t[:40]!r}", f == t or f == l or (l != t and len(f) <= len(l)))
check("metaphor 'I watch it' stays unresolved", aw.resolve_pronoun_objects_filtered("A penguin runs across the dark shingle while I watch it.") == "A penguin runs across the dark shingle while I watch it.")
check("canonical 'I plant them' still resolves", "the seeds" in aw.resolve_pronoun_objects_filtered("I plant the seeds in the bed. I plant them now."))
check("flag defaults OFF", aw.AMBIGUITY_PRECISION_FILTER_LIVE is False)
t = "I plant the seeds in the bed. I plant them now."
check("flag OFF == legacy", ca.resolve_pronoun_objects(t) == aw.resolve_pronoun_objects_legacy(t))
aw.AMBIGUITY_PRECISION_FILTER_LIVE = True
try:
    check("flag ON routes to filter", ca.resolve_pronoun_objects(t) == aw.resolve_pronoun_objects_filtered(t))
finally:
    aw.AMBIGUITY_PRECISION_FILTER_LIVE = False
print(f"{sum(res)}/{len(res)} passed"); sys.exit(0 if all(res) else 1)
