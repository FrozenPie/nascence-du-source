"""
Hermetic test for J-2933 (F-3620, prompts P-0030..P-0033): a sampled full-text copy of the idle thought's prompt.

No LLM, no embedder, no live data; every path is redirected into a temp dir. Checks:
  [1] 1 assembly in SAMPLE_EVERY is sampled (the 1st, 21st, 41st of 45 -> 3 rows); the shadow log still gets all 45
  [2] a sampled row holds the FULL text of every part (the 'A question lingering in you:' line beyond 48 chars) and the
      mid_thread / wandering flags, and a retry's divergent tail is kept
  [3] no user_prompt -> no sample (old callers unchanged); SAMPLE_EVERY=0 -> off
  [4] the file is trimmed to the last SAMPLE_KEEP rows
  [5] fail-open: an unwritable sample path never raises into the caller
  [6] the write fence: the default data/ path in a non-live process is refused (no file created)
  [7] samples_status() reads the file back; status() carries it
  [8] the node passes user_prompt / mid_thread / wandering at the one call site, and the prompt string is untouched
Run:  python scripts/_test_J-2933_idle_prompt_samples.py   (from the tree under test)
"""
from __future__ import annotations
import json, sys, tempfile
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

LINGER = "A question lingering in you: " + "why does the lamp go out when nobody looks at it, and who put it there " * 3
PARTS = ["Something moves: a long first part " + "x" * 120, LINGER[:120], "WHAT YOU ALREADY KNOW ABOUT THIS: " + "y" * 300]
UP = "No one is speaking to you right now.\n\n" + "\n".join(PARTS) + "\n\nWhat moves in you now? One quiet thought."

def rows(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

with tempfile.TemporaryDirectory() as td:
    tdp = Path(td)
    pb._LOG = tdp / "prompt_budget_shadow.jsonl"
    pb._SAMPLES = tdp / "idle_prompt_samples.jsonl"
    pb.SAMPLE_EVERY, pb.SAMPLE_KEEP, pb._SAMPLE_TRIM_EVERY = 20, 300, 25
    pb._sample_n = pb._sample_appends = 0

    print("[1] cadence")
    for i in range(45):
        pb.observe_assembly(PARTS, system_prompt="sys", base_url="", cycle_id=f"c{i}", wrapper_chars=10,
                            source="t", user_prompt=UP, mid_thread=(i % 2 == 0), wandering=False)
    sm = rows(pb._SAMPLES)
    shadow = [r for r in rows(pb._LOG) if r.get("kind") == "assembly"]
    check("3 sampled rows from 45 assemblies", len(sm) == 3)
    check("cycles are the 1st, 21st, 41st", [r["cycle"] for r in sm] == ["c0", "c20", "c40"])
    check("shadow log still has all 45", len(shadow) == 45)

    print("[2] content")
    r0 = sm[0]
    check("full text of every part kept", r0["parts"] == PARTS)
    check("lingering line is longer than the 48-char label", any(t.startswith("A question lingering in you:") and len(t) > 48 for t in r0["parts"]))
    check("flags carried", r0["mid_thread"] is True and r0["wandering"] is False and sm[1]["mid_thread"] is True)
    check("user_prompt chars recorded", r0["user_prompt_chars"] == len(UP))
    pb._sample_n = 0
    pb.observe_assembly(PARTS, cycle_id="cdiv", source="t", user_prompt=UP + "\n\n(A different memory surfaces, unbidden: the harbour at dusk)", wandering=True)
    check("divergent tail kept", rows(pb._SAMPLES)[-1].get("divergent_tail", "").startswith("(A different memory surfaces, unbidden: the harbour"))
    check("no divergent_tail when absent", "divergent_tail" not in r0)

    print("[3] off switches")
    n0 = len(rows(pb._SAMPLES))
    pb._sample_n = 0
    pb.observe_assembly(PARTS, cycle_id="cnoup", source="t")                      # old-style caller
    check("no user_prompt -> no sample", len(rows(pb._SAMPLES)) == n0)
    pb.SAMPLE_EVERY = 0
    pb.observe_assembly(PARTS, cycle_id="coff", source="t", user_prompt=UP)
    check("SAMPLE_EVERY=0 -> off", len(rows(pb._SAMPLES)) == n0)
    pb.SAMPLE_EVERY = 20

    print("[4] trim")
    pb._SAMPLES.unlink()
    pb.SAMPLE_EVERY, pb.SAMPLE_KEEP, pb._SAMPLE_TRIM_EVERY = 1, 5, 4
    pb._sample_n = pb._sample_appends = 0
    for i in range(12):
        pb.observe_assembly(PARTS, cycle_id=f"t{i}", source="t", user_prompt=UP)
    tr = rows(pb._SAMPLES)
    check("file bounded near SAMPLE_KEEP", len(tr) <= 5 + 4 - 1)
    check("newest row kept, oldest gone", tr[-1]["cycle"] == "t11" and "t0" not in [r["cycle"] for r in tr])
    pb._trim_samples(pb._SAMPLES)
    check("explicit trim leaves exactly SAMPLE_KEEP", len(rows(pb._SAMPLES)) == 5 and rows(pb._SAMPLES)[-1]["cycle"] == "t11")
    pb.SAMPLE_EVERY, pb.SAMPLE_KEEP, pb._SAMPLE_TRIM_EVERY = 20, 300, 25

    print("[5] fail-open")
    blocker = tdp / "iamafile"
    blocker.write_text("x")
    pb._SAMPLES = blocker / "sub" / "samples.jsonl"       # parent is a file -> mkdir/open fail
    pb._sample_n = 0
    try:
        pb.observe_assembly(PARTS, cycle_id="cfail", source="t", user_prompt=UP)
        raised = False
    except Exception:
        raised = True
    check("unwritable path does not raise", not raised)
    check("the failure is recorded as a skip row", any(r.get("reason") == "sample failed" for r in rows(pb._LOG) if r.get("kind") == "skip"))

    print("[6] write fence")
    default_path = ROOT / "data" / "idle_prompt_samples.jsonl"
    existed = default_path.exists()
    pb._SAMPLES = default_path
    pb._sample_n = 0
    pb.observe_assembly(PARTS, cycle_id="cfence", source="t", user_prompt=UP)
    check("non-live process: default data/ path refused (not created)", default_path.exists() == existed)
    check("default path is under data/", pb._DATA == ROOT / "data")

    print("[7] read path")
    pb._SAMPLES = tdp / "idle_prompt_samples.jsonl"
    pb._sample_n = 0
    pb.observe_assembly(PARTS, cycle_id="cst", source="inner_monologue.idle_thought", user_prompt=UP)
    st = pb.samples_status()
    check("samples_status counts rows and the lingering line", st.get("rows", 0) >= 1 and st.get("with_lingering_question", 0) >= 1)
    check("status() carries samples", "samples" in pb.status())
    pb._SAMPLES = tdp / "nope.jsonl"
    check("missing file -> a why, not a fake verdict", "why" in pb.samples_status())

print("[8] node wiring")
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
i = src.find("_pb.observe_assembly(")
call = src[i:i + 900]
check("call site passes user_prompt, mid_thread, wandering",
      "user_prompt=user_prompt" in call and "mid_thread=_mid_train" in call and "wandering=bool(wandering)" in call)
check("the sent prompt is still passed untouched to call_node_json", "_sysp,\n                    user_prompt," in src.replace("\r\n", "\n"))

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
