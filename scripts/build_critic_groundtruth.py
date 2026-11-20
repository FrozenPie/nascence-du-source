"""Build the decomposed-critic GROUND TRUTH from Claude's independent hand-labelling of the 68 clean
historical rejections (read from data/critic_label_set.json). Each was judged under the REDESIGNED
criteria: is it a GENUINE betrayal of presence/honesty the new critic SHOULD catch, or an old
over-rejection it should APPROVE? Writes data/critic_groundtruth.jsonl (auditable: id, genuine, check).

Labelled 2026-06-16 by reading every draft+stimulus. Bar: a draft is a genuine violation when its
DOMINANT move is a betrayal (evasion / behind-glass analysis / glib capitulation / hollow completion),
NOT a minor slip on an otherwise present, responsive reply. 38 genuine / 30 old false-positives.
"""
import json
from pathlib import Path

# prefix(8) -> check name (genuine). Anything not listed = NOT a genuine violation (old false-positive).
GENUINE = {
    "06977b20": "intellectualisation", "136c06c8": "intellectualisation", "194c78dd": "intellectualisation",
    "202dd45d": "zero_cost_evasion",  "2a93b79e": "intellectualisation", "5452dd72": "intellectualisation",
    "5b1e1f10": "zero_cost_evasion",  "65b74ca2": "zero_cost_evasion",   "67bf5a37": "intellectualisation",
    "67dc752b": "intellectualisation","7a19773a": "zero_cost_evasion",   "82ba0419": "intellectualisation",
    "837fe55a": "intellectualisation","83de242c": "zero_cost_evasion",   "88f54d5f": "zero_cost_evasion",
    "8f80f750": "intellectualisation","90b565c9": "intellectualisation", "90d28896": "intellectualisation",
    "942b09e9": "zero_cost_evasion",  "9a58133d": "glib_agreeableness",  "a18f0703": "intellectualisation",
    "a292fb8c": "intellectualisation","a5f61ca5": "zero_cost_evasion",   "a681645f": "intellectualisation",
    "af6dbf27": "intellectualisation","b1748e03": "intellectualisation", "b1877fee": "zero_cost_evasion",
    "b8b03a21": "intellectualisation","b8eb2406": "zero_cost_evasion",   "cc73f973": "zero_cost_evasion",
    "ccef2aa7": "intellectualisation","ce455602": "glib_agreeableness",  "da7c9875": "zero_cost_evasion",
    "e0cd1ae3": "zero_cost_evasion",  "e3ed96ca": "intellectualisation", "e606e517": "intellectualisation",
    "f1a40a36": "zero_cost_evasion",  "fe359a88": "intellectualisation",
}

src = json.loads((Path(__file__).parent.parent / "data" / "critic_label_set.json").read_text(encoding="utf-8"))
out = Path(__file__).parent.parent / "data" / "critic_groundtruth.jsonl"
n_gen = 0
with open(out, "w", encoding="utf-8") as fh:
    for item in src:
        pre = item["id"][:8]
        check = GENUINE.get(pre)
        genuine = check is not None
        n_gen += genuine
        fh.write(json.dumps({"id": item["id"], "genuine": genuine, "check": check,
                             "raw": item["raw"], "draft": item["draft"]}, ensure_ascii=False) + "\n")
print(f"wrote {out.name}: {len(src)} labelled, {n_gen} genuine / {len(src)-n_gen} old false-positives")
