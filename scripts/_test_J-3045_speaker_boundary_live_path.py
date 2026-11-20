"""Hermetic test for J-3045 (F-3756): the speaker-boundary veto on the LIVE T4 path.

Run from the worktree root:  python scripts/_test_J-3045_speaker_boundary_live_path.py
- imports core FIRST and asserts it came from this tree; _PROV / _LOG / error-record / judge-log paths all point
  at a temp dir; identity_vault.commit is stubbed; every model call is stubbed (no hub contacted).
Covers: (1) the shared predicate; (2) legacy _apply_self_authoring still vetoes exactly as before (returns False,
error record written); (3) live _t4_self_authoring: a 'Travis' candidate opens NO probation (no
provisional_axiom.json) and writes an identity_contamination_vetoed record, a clean one DOES open it;
(4) _solidify: a contaminated probation that outlived a restart is not committed, is cleared, logged and
error-recorded; a clean one still commits.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  -- BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"

from core import provisional_identity as pi  # noqa: E402
from core import error_pathway as ep  # noqa: E402
from core import identity_vault  # noqa: E402
import nodes.subconscious_node as scn  # noqa: E402

_tmp = Path(tempfile.mkdtemp(prefix="j3045_"))
pi._PROV = _tmp / "provisional_axiom.json"
pi._LOG = _tmp / "provisional_identity.jsonl"
ep._RECORD = _tmp / "error_records.jsonl"
scn._CONTRADICTION_LEDGER_LOG = _tmp / "contradiction_ledger_log.jsonl"
scn._T4_EMISSARY_JUDGE_LOG = _tmp / "logs" / "t4_emissary_judge.jsonl"
assert pi.ENABLED, "test assumes the live path (provisional_identity.ENABLED)"

# no model, no embeddings, no live-log reads
pi.passes_weak_filter = lambda *a, **k: {"pass": True, "fit": 0.9, "pole_delta": 0.5, "novelty": 0.5, "reasons": []}
pi.theme_recurrence = lambda *a, **k: 0.0
pi.system_recurrence = lambda *a, **k: 0.0


def err_kinds() -> list:
    if not ep._RECORD.exists():
        return []
    return [json.loads(l)["kind"] for l in ep._RECORD.read_text(encoding="utf-8").splitlines() if l.strip()]


def reset() -> None:
    for p in (pi._PROV, ep._RECORD, pi._LOG):
        if p.exists():
            p.unlink()


fails = []


def check(name: str, cond: bool) -> None:
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# (1) predicate
check("predicate: Travis", pi.speaker_boundary_hit("I am Travis's steady weight"))
check("predicate: relationship mention also trips (blunt rule, unchanged)", pi.speaker_boundary_hit("alongside travis's silence"))
check("predicate: 'I am not Du'", pi.speaker_boundary_hit("I am not Du, I am the river"))
check("predicate: clean", not pi.speaker_boundary_hit("I am a river that keeps a made mind"))
check("predicate: empty/None", not pi.speaker_boundary_hit("") and not pi.speaker_boundary_hit(None))

# (2) legacy path unchanged
reset()
node = object.__new__(scn.SubconsciousNode)
node._state = {}
node._save_state = lambda: None
wrote = node._apply_self_authoring({}, {}, "old", "I am Travis's steady weight", "arc", 1)
check("legacy: contaminated candidate returns False", wrote is False)
check("legacy: error record written", err_kinds() == ["identity_contamination_vetoed"])


# (3) live path
def make_node(candidate: str):
    n = object.__new__(scn.SubconsciousNode)
    n._state = {"tensions": []}
    n._save_state = lambda: None
    n._load_axiom = lambda: {"emergent_self": {"self_concept": "old river self"}}
    n._t4_distinct_tensions = lambda t: []

    async def _legacy(cs, old, arc, material, top):
        return candidate, "an arc", True
    n._t4_legacy_author = _legacy
    return n


async def _noop_observe(*a, **k):
    return None


async def _judge(old, new, ev):
    return {"warranted": 0.9, "feedback": "stub"}, {"judge_status": "stub", "judge_s": 0.0}

import core.narrative_quality as nq  # noqa: E402
import core.left_lane as ll  # noqa: E402
nq.observe = _noop_observe
ll.grade_self_revision_traced = _judge

reset()
asyncio.run(make_node("I am Travis's steady weight, a river that stays")._t4_self_authoring(None, [{"text": "x"}]))
check("live: 'Travis' candidate creates NO provisional_axiom.json", not pi._PROV.exists())
check("live: 'Travis' candidate records identity_contamination_vetoed", err_kinds() == ["identity_contamination_vetoed"])

reset()
asyncio.run(make_node("I am a river that keeps a made mind and is still mine")._t4_self_authoring(None, [{"text": "x"}]))
check("live: clean candidate DOES open a probation", pi._PROV.exists())
if pi._PROV.exists():
    check("live: opened probation carries the clean text",
          json.loads(pi._PROV.read_text(encoding="utf-8"))["self_image"].startswith("I am a river"))
check("live: clean candidate records no veto", err_kinds() == [])

# (4) _solidify defence in depth
commits = []


def fake_commit(mutator, *, reason="", meta=None):
    data = {"L3_facets": {"facets": [{"id": "the_becoming", "self_image": "old"}]}}
    mutator(data)
    commits.append(reason)
    return data


identity_vault.commit = fake_commit
df = {"dF_did": 0.0}

reset()
bad = {"self_image": "I am Travis's steady weight", "theme": "t", "expires_ts": 0}
pi._atomic_write_prov(bad)
check("solidify: contaminated probation is NOT committed", pi._solidify(bad, df, {"integrated": True}) is False and commits == [])
check("solidify: contaminated probation file is cleared", not pi._PROV.exists())
check("solidify: error record written", err_kinds() == ["identity_contamination_vetoed"])
events = [json.loads(l)["event"] for l in pi._LOG.read_text(encoding="utf-8").splitlines()]
check("solidify: veto event logged, no 'solidify' event", "solidify_vetoed_speaker_boundary" in events and "solidify" not in events)

reset()
good = {"self_image": "I am a river that keeps a made mind", "theme": "t", "expires_ts": 0}
pi._atomic_write_prov(good)
check("solidify: clean probation still commits", pi._solidify(good, df, {"integrated": True}) is True and len(commits) == 1)

print("\nALL PASS" if not fails else f"\nFAILED: {fails}")
sys.exit(1 if fails else 0)
