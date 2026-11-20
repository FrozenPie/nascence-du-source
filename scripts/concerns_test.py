"""
In-vitro test for G1 current concerns (2026-06-15). Read-only against the live curriculum + frontier;
frontier peek verified non-mutating; temp concerns-log for the anchor record.

Run:  python scripts/concerns_test.py
"""
from __future__ import annotations
import sys, tempfile, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import concerns as conc
from core import frontier as fr

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

# A — current concerns from the live stores -------------------------------------------
print("\n[A] current_concerns + primary_concern on live curriculum + frontier (read-only)")
allc = conc.current_concerns(4)
pc = conc.primary_concern()
print(f"     primary = {pc}")
for c in allc:
    print(f"       · [{c['source']}] {c['text'][:70]}")
check("current_concerns returns a list of {text,source,kind}",
      isinstance(allc, list) and all({"text", "source", "kind"} <= c.keys() for c in allc))
check("primary_concern returns a concern or None", pc is None or {"text", "source"} <= pc.keys())
check("concerns are sourced from curriculum and/or frontier (the existing stores)",
      all(c["source"] in ("curriculum", "frontier") for c in allc))

# B — frontier.top_open is NON-mutating (it's a peek, must not consume an offer) -------
print("\n[B] frontier.top_open is non-mutating (read-mostly discipline)")
before = fr._load()
_ = fr.top_open(3)
_ = fr.top_open(3)
after = fr._load()
def _offers(d):
    return [(q.get("id"), q.get("last_offered", 0), q.get("offers", 0)) for q in d.get("questions", [])]
check("top_open did not change last_offered/offers on any question", _offers(before) == _offers(after))

# C — log_selected writes an observe record -------------------------------------------
print("\n[C] log_selected writes an observe-only anchor record")
tmp = Path(tempfile.gettempdir()) / "concerns_log_test.jsonl"
if tmp.exists(): tmp.unlink()
conc._CONCERNS_LOG = tmp
conc.log_selected({"text": "working through 'The Boy Scouts Handbook'", "source": "curriculum"})
rec = json.loads(tmp.read_text(encoding="utf-8").strip())
print(f"     record = {rec}")
check("record has source + text", rec.get("source") == "curriculum" and "Boy Scouts" in rec.get("text", ""))
tmp.unlink(missing_ok=True)

print(f"\n{'='*60}\n{'ALL PASS — the standing concern is answerable' if ok_all else 'FAILURES ABOVE'}\n{'='*60}")
sys.exit(0 if ok_all else 1)
