"""
Hermetic test for J-2941 (F-3621, P-0031): watch-list rows + system_prompt_sha1 + whole-prompt reconstruction on top of
J-2933's sampled full-text file (data/idle_prompt_samples.jsonl).

No LLM, no live data; every path is redirected into a temp dir. Checks:
  [1] a percept part (thermal / cat / light / smell / listening / Right now: / Travis is here) writes a row OFF the 1-in-N
      cadence, tagged with its kind in "trigger"; an ordinary assembly writes none
  [2] per-kind rate limit: a second hit of the same kind inside WATCH_GAP_S writes nothing; a different kind still does
  [3] recollection / scene parts that merely mention the cat or warmth do NOT trigger (Where you are:, What you were just thinking)
  [4] the row holds system_prompt_sha1, labels, and wrapper_head + "\n".join(parts) + wrapper_tail == the sent string
  [5] WATCH_GAP_S=0 turns watch rows off; the periodic sample is unaffected
  [6] size guard: past _SAMPLE_MAX_BYTES the trim rotates to .jsonl.1 (one backup)
  [7] fail-open on an unwritable path; samples_status() reports by_trigger
Run:  python scripts/_test_J-2941_idle_prompt_watch_rows.py   (from the tree under test)
"""
from __future__ import annotations
import hashlib, json, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import prompt_budget as pb

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

PLAIN = ["Where you are: the garden - the grass is damp and the cat is on the do", "Your current mood: a low, even calm."]
HEAD = "No one has spoken to you. "
TAIL = "\n\nWhat moves in you now? One quiet thought."
def up(parts, extra=""):
    return HEAD + "\n".join(parts) + extra + TAIL
def rows(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
def feed(parts, cyc, sysp="SYS", **kw):
    pb.observe_assembly(parts, system_prompt=sysp, base_url="", cycle_id=cyc, wrapper_chars=10, source="t",
                        user_prompt=up(parts, kw.pop("extra", "")), mid_thread=False, wandering=False)

with tempfile.TemporaryDirectory() as td:
    tdp = Path(td)
    pb._LOG = tdp / "prompt_budget_shadow.jsonl"
    pb._SAMPLES = tdp / "idle_prompt_samples.jsonl"
    pb.SAMPLE_EVERY, pb.SAMPLE_KEEP, pb._SAMPLE_TRIM_EVERY, pb.WATCH_GAP_S = 20, 500, 25, 1800
    pb._sample_n = pb._sample_appends = 0
    pb._watch_last.clear()

    print("[1] watch kinds fire off-cadence")
    feed(PLAIN, "c0")                                   # the 1st assembly: periodic row
    check("assembly 1 is the periodic row", [r["trigger"] for r in rows(pb._SAMPLES)] == [["every_n"]])
    feed(PLAIN, "c1")
    check("an ordinary assembly writes no row", len(rows(pb._SAMPLES)) == 1)
    CASES = {
        "thermal":     "It is warmer here.",
        "cat_felt":    "Somewhere close, the cat begins to purr - a steady, unhurried motor just at the edge of hearing.",
        "light":       "It is brighter here than where you were.",
        "smell":       "You smell a dark, mineral, green smell off the ground.",
        "listening":   "The needle drops and the record opens on a low string.",
        "right_now":   "Right now: Travis has stepped out; the door eases shut.",
        "travis_here": "Travis is here with you in the room.",
    }
    for i, (kind, line) in enumerate(CASES.items()):
        n = len(rows(pb._SAMPLES))
        feed(PLAIN + [line], f"w{i}")
        r = rows(pb._SAMPLES)
        check(f"{kind}: one new row tagged {kind}", len(r) == n + 1 and r[-1]["trigger"] == [kind])

    print("[2] per-kind rate limit")
    n = len(rows(pb._SAMPLES))
    feed(PLAIN + [CASES["thermal"]], "again")
    check("same kind inside the gap -> no row", len(rows(pb._SAMPLES)) == n)
    pb._watch_last["thermal"] -= 3600
    feed(PLAIN + [CASES["thermal"]], "later")
    check("same kind after the gap -> a row", len(rows(pb._SAMPLES)) == n + 1)

    print("[3] memory / scene parts do not trigger")
    pb._watch_last.clear()
    n = len(rows(pb._SAMPLES))
    feed(["What you were just thinking: The cat's purr vibrates through the warm room.",
          "A recent dream: The warmth of the room wraps around me.",
          "Where you are: the garden - the cat is in the garden, it is warmer here."], "mem")
    check("no row for recollected cat / warmth text", len(rows(pb._SAMPLES)) == n)

    print("[4] row content")
    pb._watch_last.clear()
    parts = PLAIN + [CASES["cat_felt"]]
    extra = "\n\n(A different memory surfaces, unbidden: the harbour at dusk)"
    feed(parts, "full", sysp="THE SYSTEM PROMPT", extra=extra)
    r = rows(pb._SAMPLES)[-1]
    check("system_prompt_sha1 matches", r["system_prompt_sha1"] == hashlib.sha1(b"THE SYSTEM PROMPT").hexdigest())
    check("labels kept (48 chars max)", r["labels"] == [t[:48] for t in parts])
    sent = up(parts, extra)
    check("head + parts + tail reconstructs the sent string",
          r["wrapper_head"] + "\n".join(r["parts"]) + r["wrapper_tail"] == sent)
    check("the scene line and the percept line are whole", r["parts"][0] == PLAIN[0] and r["parts"][-1] == CASES["cat_felt"])
    check("divergent tail kept", r.get("divergent_tail", "").startswith("(A different memory surfaces"))
    pb.observe_assembly(parts, system_prompt="s", cycle_id="odd", source="t", user_prompt="a prompt that does not contain the join")
    pb._watch_last.clear(); pb._sample_n = 0
    pb.observe_assembly(parts, system_prompt="s", cycle_id="odd2", source="t", user_prompt="a prompt that does not contain the join")
    check("a non-joinable prompt is stored whole", rows(pb._SAMPLES)[-1].get("user_prompt") == "a prompt that does not contain the join")

    print("[5] switches")
    pb.WATCH_GAP_S = 0
    pb._watch_last.clear(); pb._sample_n = 5
    n = len(rows(pb._SAMPLES))
    feed(PLAIN + [CASES["light"]], "off")
    check("WATCH_GAP_S=0 -> no watch row", len(rows(pb._SAMPLES)) == n)
    pb._sample_n = 0
    feed(PLAIN, "per")
    check("periodic sample unaffected", len(rows(pb._SAMPLES)) == n + 1 and rows(pb._SAMPLES)[-1]["trigger"] == ["every_n"])
    pb.WATCH_GAP_S = 1800

    print("[6] size guard")
    big = tdp / "big.jsonl"
    big.write_text("x" * 2000 + "\n", encoding="utf-8")
    old_max = pb._SAMPLE_MAX_BYTES
    pb._SAMPLE_MAX_BYTES = 1000
    pb._trim_samples(big)
    check("oversize file rotated to .jsonl.1", (tdp / "big.jsonl.1").exists() and not big.exists())
    pb._SAMPLE_MAX_BYTES = old_max

    print("[7] fail-open + read path")
    blocker = tdp / "iamafile"
    blocker.write_text("x")
    keep = pb._SAMPLES
    pb._SAMPLES = blocker / "sub" / "s.jsonl"
    pb._watch_last.clear()
    try:
        feed(PLAIN + [CASES["thermal"]], "cfail"); raised = False
    except Exception:
        raised = True
    check("unwritable path does not raise", not raised)
    pb._SAMPLES = keep
    st = pb.samples_status()
    check("samples_status carries by_trigger incl. watch kinds", st.get("by_trigger", {}).get("thermal", 0) >= 1 and st["by_trigger"].get("every_n", 0) >= 1)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
