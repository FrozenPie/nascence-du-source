"""scripts/_test_reply_discharge_shadow_j2530.py (J-2530, I-0108): hermetic proof of the reply-level corollary
discharge shadow. No LLM, no model, no live write. core is imported FIRST and asserted to be this tree; lab_env.isolate()
sandboxes the stores and redirects the shadow log; every write-mode open() is recorded and must land on the sandbox
shadow log only; live canary files are hashed before/after.

  [1] flag OFF by default: predict/resolve return None, hold nothing, open nothing for write
  [2] prediction() is pure and follows the declared weights (grounded+approved low, ungrounded+rejected high;
      probabilities sum to 1; response_type moves only p_ignored)
  [3] flag ON: predict holds a pending discharge without writing; a non-human or empty reply predicts nothing
  [4] resolve on a correction turn -> one row: actual_correction 1, self_surprise = |p_corr - 1|; fed False
  [5] land (uptake) and ignored turns classify as declared; nothing pending -> no row
  [6] the only write target is the sandbox shadow log; prediction_error / competence beliefs never touched
  [7] wiring: both orchestrator hooks present, the resolve hook behind the flag; no prediction_error.observe here
"""
from __future__ import annotations
import builtins, hashlib, io, json, sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import reply_discharge_shadow as rds  # noqa: E402
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
CANARY = [LIVE / "logs" / "reply_discharge_shadow.jsonl", LIVE / "capability_beliefs.json", LIVE / "social_state.json",
          LIVE / "capability_surprise.json", LIVE / "accuracy_observations.jsonl"]
before = {p: h(p) for p in CANARY}

WRITES: list = []
_real_open, _real_io_open = builtins.open, io.open


def _spy(file, mode="r", *a, **k):
    if any(c in str(mode) for c in "wax+"):
        WRITES.append(str(Path(str(file)).resolve()) if isinstance(file, (str, Path)) else repr(file))
    return _real_open(file, mode, *a, **k)


def mkstate(reply, *, approved=True, cconf=0.9, corrections=(), content=False, rt="answer", cid="c1"):
    return NS(voice=NS(final=reply), critic=NS(approved=approved, confidence=cconf, corrections=list(corrections)),
              executive=NS(response_type=rt), content_mode=content, cycle_id=cid)


def mkassess(grade, just, conf):
    return NS(grade=grade, justification=just, self_reported_confidence=conf, confabulation_signal=conf - just)


observed = []
import core.prediction_error as _pe  # noqa: E402
_orig_obs = getattr(_pe, "observe", None)
_pe.observe = lambda *a, **k: observed.append((a, k))

with isolate(db="empty", also=[(rds, ["_SHADOW"])]) as lab:
    shadow = Path(rds._SHADOW).resolve()
    check(shadow.is_relative_to(Path(lab).resolve()), "shadow log redirected into the lab dir")
    builtins.open = io.open = _spy
    try:
        # [1]
        check(rds.REPLY_DISCHARGE_SHADOW is False, "[1] flag is OFF by default")
        r1 = rds.predict(mkstate("The garden needs water today."), mkassess("SUSPECT", 0.5, 0.9))
        r2 = rds.resolve("no, that's wrong", social_spike=0.75, cycle_id="c2", background=False)
        check(r1 is None and r2 is None and rds._PENDING is None and not WRITES and not shadow.exists(),
              "[1] flag off: returns None, holds nothing, opens nothing for write")

        # [2]
        lo = rds.prediction(rds.signals(mkstate("x", approved=True, cconf=1.0), mkassess("KNOW", 1.0, 0.9)))
        hi = rds.prediction(rds.signals(mkstate("x", approved=False, cconf=0.3, corrections=["a", "b", "c"],
                                                content=True), mkassess("NO_BASIS", 0.0, 0.95)))
        exp_hi = round(min(1.0, rds.P_CORR_BASE + rds.W_UNJUSTIFIED + rds.W_CONFAB * 0.95 + rds.W_CRITIC_REJECT
                           + rds.W_CRITIC_CORR + rds.W_CRITIC_LOWCONF * 0.7 + rds.W_CONTENT), 3)
        check(lo["p"]["correction"] == rds.P_CORR_BASE, f"[2] grounded+approved -> base p_corr {lo['p']['correction']}")
        check(hi["p"]["correction"] == exp_hi and hi["predicted_class"] == "correction",
              f"[2] ungrounded+rejected -> p_corr {hi['p']['correction']} == declared sum {exp_hi}")
        check(all(abs(sum(x["p"].values()) - 1.0) <= 0.002 for x in (lo, hi)), "[2] probabilities sum to 1")
        q = rds.prediction(rds.signals(mkstate("x", rt="question"), mkassess("THINK", 0.75, 0.8)))
        rf = rds.prediction(rds.signals(mkstate("x", rt="reflection"), mkassess("THINK", 0.75, 0.8)))
        check(q["p"]["correction"] == rf["p"]["correction"] and q["p"]["ignored"] < rf["p"]["ignored"],
              "[2] response_type moves p_ignored only")
        nul = rds.prediction(rds.signals(NS(), None))
        check(nul["p"]["correction"] == rds.P_CORR_BASE, "[2] missing signals read neutral (no crash)")
        check(not WRITES, "[2] prediction/signals are pure")

        # [3]
        rds.REPLY_DISCHARGE_SHADOW = True
        check(rds.predict(mkstate("x"), mkassess("KNOW", 1, 1), input_type="autonomous") is None
              and rds.predict(mkstate("   "), mkassess("KNOW", 1, 1)) is None and rds._PENDING is None,
              "[3] non-human cycle or empty reply predicts nothing")
        p = rds.predict(mkstate("Paris is the capital of Spain, I believe.", approved=False, content=True, cid="c1"),
                        mkassess("SUSPECT", 0.5, 0.92))
        check(p is not None and rds._PENDING is p and not WRITES, "[3] predict holds a pending discharge, writes nothing")

        # [4]
        row = rds.resolve("No, that's wrong. Paris is in France.", social_spike=0.75, cycle_id="c2", background=False)
        got = [json.loads(x) for x in _real_open(shadow, encoding="utf-8")] if shadow.exists() else []
        check(len(got) == 1 and row is not None and got[0]["actual_class"] == "correction"
              and got[0]["actual_correction"] == 1.0, "[4] correction turn -> one row, actual_correction 1")
        check(got and got[0]["self_surprise"] == round(abs(p["p"]["correction"] - 1.0), 3) and got[0]["fed"] is False,
              f"[4] self_surprise = |p_corr - actual| = {got[0]['self_surprise'] if got else None}; fed False")
        check(got and got[0]["pred_cycle_id"] == "c1" and got[0]["resolve_cycle_id"] == "c2" and rds._PENDING is None,
              "[4] row joins predicting and resolving cycles; pending cleared")

        # [5]
        rds.predict(mkstate("The tomatoes in the garden ripened slowly this week.", cid="c3"), mkassess("THINK", .75, .8))
        r_land = rds.resolve("Which tomatoes did you pick?", cycle_id="c4", background=False)
        rds.predict(mkstate("The tomatoes in the garden ripened slowly this week.", cid="c5"), mkassess("THINK", .75, .8))
        r_ign = rds.resolve("Anyway, what is your favourite colour?", cycle_id="c6", background=False)
        rds.predict(mkstate("Seven times six is forty-two.", cid="c7"), mkassess("THINK", .75, .8))
        r_conf = rds.resolve("That's right.", cycle_id="c8", background=False)
        check(r_land["actual_class"] == "land" and "tomatoes" in r_land["uptake_words"]
              and r_land["self_surprise"] == r_land["predicted"]["correction"], "[5] uptake turn -> land")
        check(r_ign["actual_class"] == "ignored", "[5] no verdict, no shared content word -> ignored")
        check(r_conf["actual_class"] == "land" and r_conf["c_signal_confirmation"] is True, "[5] confirmation cue -> land")
        check(rds.resolve("hello again", cycle_id="c9", background=False) is None, "[5] nothing pending -> no row")
        rds.REPLY_DISCHARGE_SHADOW = False

        # [6]
        n = sum(1 for _ in _real_open(shadow, encoding="utf-8"))
        check(n == 4, f"[6] 4 resolved rows in the sandbox shadow log ({n})")
        check(set(WRITES) == {str(shadow)}, f"[6] the only write target is the sandbox shadow log ({len(WRITES)} opens)")
        check(not observed, "[6] prediction_error.observe never called (no cost wired)")
    finally:
        builtins.open, io.open = _real_open, _real_io_open
        if _orig_obs is not None:
            _pe.observe = _orig_obs

# [7] wiring
src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
mod = (ROOT / "core" / "reply_discharge_shadow.py").read_text(encoding="utf-8")
check("_rds.predict(self.state, _prov, input_type=input_type)" in src, "[7] predict hook after recall_wager")
check("if _rds.REPLY_DISCHARGE_SHADOW:\n                _rds.resolve(self.state.raw_input, social_spike=spike" in src,
      "[7] resolve hook after apply_correction, behind the flag")
check("prediction_error" not in mod.split('"""', 2)[2], "[7] module code never references prediction_error")
check(all(h(p) == before[p] for p in CANARY), "[7] live canaries unchanged")
print("PASS" if FAILS == 0 else f"FAIL ({FAILS})")
sys.exit(1 if FAILS else 0)
