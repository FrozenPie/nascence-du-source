import random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lab_reentry_blind_pair as m

lo, hi = m.wilson(30, 40)
assert 0.59 < lo < 0.75 < hi < 0.87, (lo, hi)
assert m.wilson(0, 0) == (0.0, 1.0)


def judge(p):  # stub model: prefers whichever passage contains REV
    a = p.split('A: "')[1].split('"')[0]
    return "A" if "REV" in a else "B"


rng = random.Random(1)
assert all(m.judge_pair(judge, "base", "REV", rng) is True for _ in range(50))
assert m.judge_pair(lambda p: "maybe", "x", "y", rng) is None
rows = [{"first": "f%d" % i, "settled": "REV%d" % i, "ingredients": ["i"], "ingredients_full": ["ingredient"]}
        for i in range(20)]
res = m.run(rows, judge, lambda p: "REVx" if "ingredient" in p.split("context")[0] else "plain", rng,
            ["logged", "ingr", "control"], False)
assert res["logged"]["share"] == 1.0 and res["ingr"]["n"] == 20 and res["control"]["n"] == 20
print("ok")
