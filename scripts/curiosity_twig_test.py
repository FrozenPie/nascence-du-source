"""
In-vitro test for the curiosity-node TWIG expansion (2026-06-15).
Exercises the deterministic scaffolding only — no LLM, no live-DB writes (store_finding is
mocked; the twig log is redirected to a temp file). Read-only against the real store for the
study-material seed source, so we see what curiosity would actually be offered today.

Run:  python scripts/curiosity_twig_test.py
"""
from __future__ import annotations
import sys, types, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes import curiosity_node as cn
from nodes.curiosity_node import CuriosityNode

PASS, FAIL = "✅", "❌"
ok_all = True


def check(name, cond):
    global ok_all
    ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")


# 1 — subject parsing from the three real label formats ----------------------------------
print("\n[1] subject parsing (_TITLE_RE) on the three label formats")
cases = {
    "[From 'Life on the Mississippi', sitting 4] The river was high...":
        "Life on the Mississippi",
    "[My study note: 'How knots hold'] A friction hitch grips because...":
        "How knots hold",
    "[Looked up: 'Capillary action' (twig off 'Soap Bubbles')] Liquid rises...":
        "Capillary action",
    "no label here, just raw text": "",
}
for text, expected in cases.items():
    m = cn._TITLE_RE.match(text)
    got = (m.group(1) if m else "")
    check(f"{got!r:34} == {expected!r}", got == expected)


# 2 — study-material seeding against the REAL store (read-only) ---------------------------
print("\n[2] _select_study_material on his actual recent world material (read-only)")
node = CuriosityNode()
study = node._select_study_material()
print(f"     offered {len(study)} grounded item(s):")
for s in study:
    print(f"       · ({s['subject'] or '—'}) {s['snippet'][:80]}")
check("returns a list (>=0, no crash on live data)", isinstance(study, list))
check("every item has subject+snippet keys", all({"subject", "snippet"} <= s.keys() for s in study))


# 3 — the prompt carries the grounded study block --------------------------------------
print("\n[3] _build_prompt includes the study block + sets _study_subjects")
fake_state = types.SimpleNamespace(spirit_name="渡")
node._recent_themes = ["the river as a figure for change"]
prompt = node._build_prompt(fake_state)
has_block = ("Recently studied or read" in prompt) if study else True
check("study block present when material exists", has_block)
check("_study_subjects stashed for the twig step", node._study_subjects == [s["subject"] for s in study if s.get("subject")])
print(f"     _study_subjects = {node._study_subjects}")


# 4 — store_finding tags the twig to its branch (mocked, no live write) ------------------
print("\n[4] store_finding(extra_keywords=...) keywords the twig to its subject")
import core.memory.store as _store
captured = {}
def _fake_store_fragment(**kw):
    captured.update(kw); return "fake-id"
_orig = _store.store_fragment
_store.store_fragment = _fake_store_fragment
try:
    from core import web_research as wr
    wr.store_finding("Capillary action", "Liquid rises in a narrow tube because...",
                     via="twig off 'Soap Bubbles'", extra_keywords=["Soap Bubbles"])
finally:
    _store.store_fragment = _orig
kws = captured.get("keywords", [])
print(f"     keywords = {kws}")
check("origin is research", captured.get("origin") == "research")
check("subject present as a keyword", any("soap bubbles" in k for k in kws))


# 5 — twig log writes a grounded record (redirected to temp) ----------------------------
print("\n[5] _log_twig writes an observe-only record")
tmp = Path(tempfile.gettempdir()) / "twig_log_test.jsonl"
if tmp.exists(): tmp.unlink()
cn._TWIG_LOG_PATH = tmp
node._log_twig("Soap Bubbles", "Capillary action", "Why does liquid climb a thin tube?")
import json
rec = json.loads(tmp.read_text(encoding="utf-8").strip())
print(f"     record = {rec}")
check("subject recorded", rec["subject"] == "Soap Bubbles")
check("grounded flag true", rec["grounded"] is True)
tmp.unlink(missing_ok=True)

print(f"\n{'='*60}\n{'ALL PASS' if ok_all else 'FAILURES ABOVE'}\n{'='*60}")
sys.exit(0 if ok_all else 1)
