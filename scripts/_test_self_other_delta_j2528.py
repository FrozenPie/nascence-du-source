"""scripts/_test_self_other_delta_j2528.py (J-2528, I-0106): hermetic proof of the typed self-other delta (observe-only).

No LLM, no embedding model (cost_fn is faked), no live write. core is imported FIRST and asserted to be this tree;
lab_env.isolate() sandboxes the stores; the shadow log is redirected into the sandbox; every write-mode open() is
recorded and must land on the sandbox shadow log or the caller-named replay output, nowhere else.

  [1] flag OFF by default; observe_human_turn returns None and opens nothing for writing
  [2] classify(): norm / value / role cues; capability only from the competence_c channel with domains;
      memory only from the retraction channel (its text is never cue-classified); untyped base-rate row
  [3] flag ON: one landed correction -> typed rows in the sandbox shadow log ONLY; repair_or_defend None;
      witness_only True; identity_cost_delta = magnitude * cost; return value None (G6)
  [4] a non-correction, non-guidance turn writes nothing
  [5] replay() over a synthetic data dir and over the LIVE data dir (read-only, hash canary) into the lab dir;
      replay refuses an output path inside data/
  [6] wiring: orchestrator hook sits right after apply_correction, behind the flag; no other module imports it;
      the module exposes nothing prompt-shaped
"""
from __future__ import annotations
import builtins, hashlib, io, json, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import self_other_delta as sod  # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

LIVE = Path(r"C:\Nascence\data")
FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")
CANARY = [LIVE / "guidance_shadow_log.jsonl", LIVE / "retractions.jsonl", LIVE / "peer_models.json",
          LIVE / "logs" / "self_other_delta_shadow.jsonl", LIVE / "capability_beliefs.json", LIVE / "social_state.json"]
before = {p: h(p) for p in CANARY}

WRITES: list = []
_real_open, _real_io_open = builtins.open, io.open


def _spy(file, mode="r", *a, **k):
    if any(c in str(mode) for c in "wax+"):
        WRITES.append(str(Path(str(file)).resolve()) if isinstance(file, (str, Path)) else repr(file))
    return _real_open(file, mode, *a, **k)


FAKE_COST = 0.4
sod._default_cost = lambda claim: FAKE_COST if claim else None   # never loads the embedding model

with isolate(db="empty", also=[(sod, ["_SHADOW"])]) as lab:
    shadow = Path(sod._SHADOW).resolve()
    check(shadow.is_relative_to(Path(lab).resolve()), "shadow log redirected into the lab dir")
    builtins.open = io.open = _spy
    try:
        # [1]
        check(sod.SELF_OTHER_DELTA_SHADOW is False, "[1] flag is OFF by default")
        r = sod.observe_human_turn("No, that's wrong. You should not talk about yourself.",
                                   {"cycle_id": "p1", "answer": "I am the river.", "domains": ["self"]},
                                   cycle_id="c1", social_spike=0.75, background=False)
        check(r is None and not WRITES and not shadow.exists(), "[1] flag off: returns None, opens nothing for write")

        # [2]
        c = sod.classify("You should stop that. What matters is honesty. You are not my teacher.")
        check(set(c) == {"norm", "value", "role"}, f"[2] classify finds norm/value/role: {sorted(c)}")
        rows = sod.build_rows(peer_id="Travis", self_claim="x", peer_signal="no, wrong.", channel="competence_c",
                              base=1.0, domains=["physics", "self"], cost_fn=lambda _: 0.5)
        check([x["delta_type"] for x in rows] == ["capability"] and rows[0]["delta_magnitude"] == round(2 / 3, 3),
              "[2] capability row comes only from competence_c domains (2 domains -> 0.667)")
        rows = sod.build_rows(peer_id="Travis", self_claim="x", peer_signal="no, wrong.", channel="social_correction",
                              base=1.0, domains=["physics"], cost_fn=lambda _: 0.5)
        check(all(x["delta_type"] != "capability" for x in rows), "[2] no capability row off the competence_c channel")
        rows = sod.build_rows(peer_id="human", self_claim="Paris is in Spain", peer_signal="you should check: what matters",
                              channel="retraction", base=1.0, memory_status="retracted", cost_fn=lambda _: 0.5)
        check([x["delta_type"] for x in rows] == ["memory"] and rows[0]["delta_magnitude"] == 1.0,
              "[2] retraction -> exactly one memory row, its text never cue-classified")
        rows = sod.build_rows(peer_id="Travis", self_claim="", peer_signal="no.", channel="social_correction",
                              base=1.0, cost_fn=lambda _: 0.5)
        check([x["delta_type"] for x in rows] == ["untyped"] and rows[0]["identity_cost"] is None,
              "[2] uncued correction -> one untyped row; no claim -> no identity cost")
        check(not WRITES, "[2] build_rows / classify are pure (no write opens)")

        # [3]
        sod.SELF_OTHER_DELTA_SHADOW = True
        r = sod.observe_human_turn("No, that's wrong. You should not talk about yourself. You are not my teacher.",
                                   {"cycle_id": "p1", "answer": "I am the river that remembers.", "domains": ["self"]},
                                   cycle_id="c1", social_spike=0.75, background=False)
        got = [json.loads(x) for x in _real_open(shadow, encoding="utf-8")] if shadow.exists() else []
        types = sorted(x["delta_type"] for x in got)
        check(r is None, "[3] observe returns None (nothing flows back, G6)")
        check(types == ["capability", "norm", "role"], f"[3] typed rows written: {types}")
        check(all(x["repair_or_defend"] is None and x["witness_only"] is True
                  and x["about"] == "du_model_of_peer_and_claim" for x in got), "[3] repair_or_defend None, witness_only")
        check(all(x["identity_cost"] == FAKE_COST and x["identity_cost_delta"] == round(x["delta_magnitude"] * FAKE_COST, 3)
                  for x in got), "[3] identity_cost_delta = magnitude * embeddedness of the challenged claim")
        check(all(x["self_claim"].startswith("I am the river") and x["peer_id"] == "Travis" for x in got),
              "[3] self_claim is the PRIOR answer from the competence pending record")
        check(set(WRITES) == {str(shadow)}, f"[3] the only write target is the sandbox shadow log ({len(WRITES)} opens)")

        # [4]
        n0 = len(got)
        sod.observe_human_turn("Tell me about the garden today.", {"cycle_id": "p2", "answer": "a"}, cycle_id="c2",
                               background=False)
        n1 = sum(1 for _ in _real_open(shadow, encoding="utf-8"))
        check(n1 == n0, "[4] a plain turn (no correction, not guidance) writes nothing")
        sod.SELF_OTHER_DELTA_SHADOW = False

        # [5] synthetic replay
        tmp = Path(tempfile.mkdtemp(dir=lab))
        (tmp / "guidance_shadow_log.jsonl").write_text("\n".join(json.dumps(x) for x in [
            {"ts": 1, "cycle_id": "g1", "raw_input": "You should answer first. Honesty matters more.", "is_guidance": True,
             "source": "Travis"},
            {"ts": 2, "cycle_id": "g2", "raw_input": "nice day", "is_guidance": False}]), encoding="utf-8")
        (tmp / "retractions.jsonl").write_text(json.dumps({"ts": 3, "claimed": "c", "falsified_by": "human",
                                                           "status": "suspended", "source": "human"}), encoding="utf-8")
        (tmp / "peer_models.json").write_text(json.dumps({"darwin": {"recent_reflections": [
            {"ts": 4, "text": "Charles disagreed with me about the bees; he is not my mirror."},
            {"ts": 5, "text": "Charles loves beetles."}]}}), encoding="utf-8")
        WRITES.clear()
        out = Path(lab) / "replay_synth_J-2528.jsonl"
        s = sod.replay(out, data_dir=tmp)
        check(s["signals"] == {"guidance": 1, "retraction": 1, "peer_reflection": 1}, f"[5] synthetic signals {s['signals']}")
        check(s["by_type"].get("memory") == 1 and s["by_type"].get("norm") == 1 and s["by_type"].get("value") == 1,
              f"[5] synthetic by_type {s['by_type']}")
        check(set(WRITES) == {str(out.resolve())}, "[5] replay writes only its caller-named output")
        try:
            sod.replay(tmp / "fake" / "data" / "logs" / "x_J-2528.jsonl", data_dir=tmp)   # harmless if not refused
            check(False, "[5] replay refuses an output inside data/")
        except ValueError:
            check(True, "[5] replay refuses an output inside data/")
        # live replay, read-only
        WRITES.clear()
        out2 = Path(lab) / "replay_live_J-2528.jsonl"
        s2 = sod.replay(out2, data_dir=LIVE)
        print("  live replay:", json.dumps(s2))
        check(set(WRITES) == {str(out2.resolve())}, "[5] live replay writes only its lab-dir output")
    finally:
        builtins.open, io.open = _real_open, _real_io_open

# [6]
src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
i = src.find("spike = self.social.state.apply_correction(self.state.raw_input)")
j = src.find("_sod.observe_human_turn(")
check(0 < i < j < i + 900 and "if _sod.SELF_OTHER_DELTA_SHADOW:" in src[i:j], "[6] hook right after apply_correction, flag-gated")
importers = [p.relative_to(ROOT).as_posix() for d in ("core", "nodes") for p in (ROOT / d).rglob("*.py")
             if "self_other_delta" in p.read_text(encoding="utf-8", errors="ignore") and p.name != "self_other_delta.py"]
check(importers == ["core/orchestrator.py"], f"[6] only the orchestrator references the module: {importers}")
check(not [n for n in dir(sod) if any(w in n.lower() for w in ("prompt", "inject", "render", "block", "readout"))],
      "[6] nothing prompt-shaped exported")

after = {p: h(p) for p in CANARY}
check(before == after, "live canary files byte-identical (incl. no live self_other_delta_shadow.jsonl)")
print("FAILS:", FAILS)
sys.exit(1 if FAILS else 0)
