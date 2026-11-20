"""J-3256: scripts/build_voice_set.py cuts the voice set by DECOUPLED verdicts (D-0645). Synthetic data in a temp dir;
the live data/ is only hashed before/after to prove the builder never wrote to a live store.

  python scripts/_test_J3256_voice_set.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_voice_set", ROOT / "scripts" / "build_voice_set.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
assert ROOT in Path(B.__file__).resolve().parents, "builder resolves outside the worktree"

LIVE = Path("C:/Nascence/data")
WATCH = [LIVE / "training" / "voice.jsonl", LIVE / "social_cognition_shadow.jsonl", LIVE / "judge_panel_log.jsonl",
         LIVE / "self_interrogation_shadow.jsonl", LIVE / "training" / "critic.jsonl"]


def h(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "absent"


before = {p: h(p) for p in WATCH}
FAILS = 0


def check(cond, label):
    global FAILS
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS += 1


def w(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


T = Path(tempfile.mkdtemp(prefix="j3256_"))
mk = lambda cid, txt, it="internal": {"ts": 1.0, "cycle_id": cid, "node": "voice", "input_type": it,
                                      "output": {"final": txt}}
voice = [
    mk("A", "alpha reply " * 10, "human"),            # social fav -> kept
    mk("B", "beta reply " * 10, "human"),             # social unfav -> dropped
    mk("C", "first draft " * 10, "human"),            # redraft: NOT the delivered reply
    mk("C", "delivered reply " * 10, "human"),        # delivered; social unfav
    mk("D", "thought d " * 10),                       # self_int fav only -> kept
    mk("E", "thought e " * 10),                       # self_int fav + panel advances False -> dropped (veto)
    mk("F", "thought f " * 10),                       # no decoupled verdict -> uncovered
    mk("G", "thought g " * 10),                       # only a TRANSPORT panel row (key genuine) -> uncovered
    mk("H", "thought h " * 10),                       # social judges-unavailable (tracks_intent None) -> uncovered
]
w(T / "training" / "voice.jsonl", voice)
crit = lambda cid, ok, ts: {"ts": ts, "cycle_id": cid, "output": {"approved": ok}}
w(T / "training" / "critic.jsonl", [crit(c, True, 1) for c in "ABCDEFGH"] + [crit("C", False, 2)])
w(T / "founder_conversation_log.jsonl", [
    {"cycle_id": "A", "entity": "alpha reply " * 10}, {"cycle_id": "B", "entity": "beta reply " * 10},
    {"cycle_id": "C", "entity": "delivered reply " * 10}])
w(T / "social_cognition_shadow.jsonl", [
    {"ts": 5, "cycle_id": "A", "tracks_intent": True, "prompt_v": 3, "kind": "conversation"},
    {"ts": 1, "cycle_id": "B", "tracks_intent": True, "prompt_v": 2, "kind": "conversation"},   # superseded by v3
    {"ts": 2, "cycle_id": "B", "tracks_intent": False, "prompt_v": 3, "kind": "conversation"},
    {"ts": 3, "cycle_id": "C", "tracks_intent": False, "prompt_v": 3, "kind": "conversation"},
    {"ts": 4, "cycle_id": "H", "skip": "judges-unavailable"},
    {"ts": 4, "skip": "no-candidates"}])
w(T / "self_interrogation_shadow.jsonl", [
    {"ts": 1, "kind": "skip", "skip": "not-sampled"},
    {"ts": 2, "kind": "interrogate", "cycle_id": "D", "genuine": True},
    {"ts": 3, "kind": "interrogate", "cycle_id": "E", "genuine": True},
    {"ts": 4, "kind": "interrogate", "cycle_id": "H", "genuine": None}])
w(T / "judge_panel_log.jsonl", [
    {"ts": 1, "key": "advances", "verdict": False, "cycle_id": "E"},
    {"ts": 1, "key": "genuine", "verdict": False, "cycle_id": "G"},        # transport row: never counted
    {"ts": 1, "key": "tracks", "node": "voice", "verdict": False, "cycle_id": "F"},   # transport row: never counted
    {"ts": 1, "key": "resolves", "verdict": True}])

kept, s = B.build(T)
ids = [r["cycle_id"] for r in kept]
st = s["status"]
check(sorted(ids) == ["A", "D"], "kept exactly the cycles with only favourable decoupled verdicts: %s" % ids)
check(st == {"kept": 2, "dropped": 3, "uncovered": 4}, "status counts %s" % st)
rowC = [r for r in voice if r["cycle_id"] == "C"]
check(B.decide_row(rowC[0], B.load_sources(T), B.ALL_SOURCES)["status"] == "uncovered",
      "redraft that was not the delivered reply gets no social verdict")
check(B.decide_row(rowC[1], B.load_sources(T), B.ALL_SOURCES)["status"] == "dropped", "delivered redraft carries the verdict")
check(B.load_sources(T)["social"]["B"]["tracks_intent"] is False, "newest highest prompt_v ruling wins per cycle")
check(s["dropped_by_vetoing_source"] == {"social": 2, "panel": 1}, "veto attribution %s" % s["dropped_by_vetoing_source"])
check(s["panel_transport_rows_not_counted_here"] == {"genuine": 1, "tracks": 1}, "transport panel rows tallied, not counted")
check(s["per_source_coverage_rows"].get("panel") == 1, "panel source = advances rows only")
check(s["agreement"]["critic_keep_decoupled_drop"] == 2, "critic-keep/decoupled-drop counted: %s" % s["agreement"])
only = B.build(T, ("social",))[1]
check(only["status"].get("kept") == 1 and only["status"].get("dropped") == 2, "--sources social narrows the rule: %s" % only["status"])
check(all("decoupled" in r and r["decoupled_status"] == "kept" for r in kept), "verdicts joined per kept row")

# CLI: writes only the two derived files; refuses to overwrite a live corpus
out = T / "training" / "voice_set_decoupled.jsonl"
check(B.main(["--data", str(T)]) == 0 and out.exists() and out.with_name("voice_set_decoupled.summary.json").exists(),
      "CLI wrote the set + summary")
check(len(out.read_text(encoding="utf-8").splitlines()) == 2, "set file has 2 rows")
check(B.main(["--data", str(T), "--out", str(T / "training" / "voice.jsonl")]) == 2, "refuses to write over voice.jsonl")
check(len(voice) == len((T / "training" / "voice.jsonl").read_text(encoding="utf-8").splitlines()), "voice.jsonl untouched")
check(B.main(["--data", str(T), "--dry-run", "--out", str(T / "x.jsonl")]) == 0 and not (T / "x.jsonl").exists(), "--dry-run writes nothing")
check(before == {p: h(p) for p in WATCH}, "live stores byte-identical before/after")
print("ALL OK" if not FAILS else "FAILED: %d" % FAILS)
raise SystemExit(1 if FAILS else 0)
