"""scripts/_test_common_ground_shadow_j2523.py (J-2523, I-0101): hermetic proof of the failed-to-object ledger (observe-only).

No LLM, no embedding model, no live write. core is imported FIRST and asserted to be this tree; lab_env.isolate()
sandboxes the stores; LEDGER is redirected into the sandbox; every write-mode open() is recorded and must land on
the sandbox ledger or the caller-named replay output, nowhere else.

  [1] flag OFF by default; observe_exchange returns None and opens nothing for writing
  [2] build_row(): each status is produced by the rule that names it -- user_said, failed_to_object,
      both_accepted, corrected, du_inferred; echo is not a claim; questions and assumed_unverified recorded
  [3] next-turn resolution: Travis's reply resolves Du's previous du_inferred claim (resolves_prev)
  [4] flag ON: one row per exchange, ONLY in the sandbox ledger; return value None; fail-open on junk input
  [5] replay(): synthetic source into the lab dir; refuses an output inside data/; LIVE founder log read-only
      (hash canary) into the lab dir -- prints the replay summary
  [6] wiring: the orchestrator hook sits in the human-output block behind the flag; no other module imports it;
      the module imports no store writer
"""
from __future__ import annotations
import builtins, hashlib, io, json, re, sys, tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import common_ground_shadow as cg  # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate  # noqa: E402

LIVE = Path(r"C:\Nascence\data")
OUT = Path(tempfile.mkdtemp(prefix="cg_J-2523_"))   # replay outputs: outside every data/ dir
FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")
CANARY = [LIVE / "founder_conversation_log.jsonl", LIVE / "common_ground_shadow.jsonl",
          LIVE / "guidance_shadow_log.jsonl", LIVE / "retractions.jsonl"]
before = {p: h(p) for p in CANARY}

WRITES: list = []
_real_open, _real_io_open = builtins.open, io.open


def _spy(file, mode="r", *a, **k):
    if any(c in str(mode) for c in "wax+"):
        WRITES.append(str(Path(str(file)).resolve()) if isinstance(file, (str, Path)) else repr(file))
    return _real_open(file, mode, *a, **k)


def st(row, by="travis"):
    return [c["status"] for c in row["claims"] if c["by"] == by]


with isolate(db="empty", also=[(cg, ["LEDGER"])]) as lab:
    ledger = Path(cg.LEDGER).resolve()
    check(ledger.is_relative_to(Path(lab).resolve()), "LEDGER redirected into the lab dir")
    builtins.open = io.open = _spy
    try:
        # [1]
        check(cg.COMMON_GROUND_SHADOW is False, "[1] flag is OFF by default")
        r = cg.observe_exchange("The garden needs water every morning.", "Yes, I will water it.", cycle_id="x")
        check(r is None and not WRITES and not ledger.exists(), "[1] flag off: returns None, opens nothing for write")

        # [2]
        a = cg.build_row("The garden needs fresh water every single morning.",
                         "Yes. The garden needs fresh water each morning, and I will carry it.", now=1000.0)
        check(st(a) == ["both_accepted"] and a["counts"]["echo"] == 1 and st(a, "du") == [],
              f"[2] opening assent + uptake -> both_accepted; restatement is echo: {st(a)} {a['counts']}")
        b = cg.build_row("Cats can see perfectly in total darkness.",
                         "Actually, cats cannot see in total darkness; their eyes need a little light.", now=1000.0)
        check(st(b) == ["corrected"], f"[2] objection cue on the claim -> corrected: {st(b)}")
        c = cg.build_row("The river carries the old stones downstream every spring.",
                         "The stones the river carries downstream remember the mountain they left.", now=1000.0)
        check(st(c) == ["failed_to_object"] and "c1" in c["assumed_unverified"],
              f"[2] taken up, no assent/objection -> failed_to_object, listed assumed_unverified: {st(c)}")
        d = cg.build_row("Your bread recipe needs much more salt.",
                         "I watched the lantern flicker slowly tonight beside the window.", now=1000.0)
        check(st(d) == ["user_said"] and st(d, "du") == ["du_inferred"],
              f"[2] unaddressed -> user_said; Du's own new assertion -> du_inferred: {st(d)} {st(d, 'du')}")
        e = cg.build_row("Hello Du. Where did you put the blue lantern?",
                         "Perhaps the blue lantern sits on the shelf near the door. Did you look there?", now=1000.0)
        qs = [(q["by"], q["answered_in_reply"]) for q in e["open_questions"]]
        check(qs == [("travis", True), ("du", None)], f"[2] questions recorded with who asked / answered: {qs}")
        check(not e["claims"] or all(c_["status"] != "user_said" for c_ in e["claims"]),
              "[2] 'Hello Du.' is below MIN_CLAIM_TOKENS and is not a claim")
        f = cg.build_row("There is no rain today, the field is dry.", "There is no light in the hall tonight at all.",
                         now=1000.0)
        check("corrected" not in st(f), f"[2] a bare in-prose 'no' is not an objection: {st(f)}")
        stat = {s for row in (a, b, c, d) for s in st(row) + st(row, "du")}
        check({"user_said", "du_inferred", "both_accepted", "failed_to_object"} <= stat,
              f"[2] all four briefed statuses are distinct values in the data: {sorted(stat)}")
        check(all(c_["revise_if"] for row in (a, b, c, d) for c_ in row["claims"]), "[2] every claim has revise_if")
        check(not WRITES, "[2] build_row is pure (no write opens)")

        # [3]
        mem = {"row_id": None, "ts": None, "du_claims": []}
        cg._remember(d, mem)
        nxt = cg.build_row("No, the lantern was steady tonight, it did not flicker slowly.", "I see.", prev=mem,
                           now=1000.0 + 60)
        res = [(x["claim_id"], x["status"]) for x in nxt["resolves_prev"]]
        check(res == [("c2", "corrected")], f"[3] Travis's next turn resolves Du's claim -> corrected: {res}")
        late = cg.build_row("No, the lantern was steady tonight.", "I see.", prev=mem,
                            now=1000.0 + cg.RESOLVE_WINDOW_S + 1)
        check(late["resolves_prev"] == [], "[3] no resolution outside RESOLVE_WINDOW_S")

        # [4]
        cg.COMMON_GROUND_SHADOW = True
        r1 = cg.observe_exchange("Your bread recipe needs much more salt.",
                                 "I watched the lantern flicker slowly tonight beside the window.", cycle_id="c1")
        r2 = cg.observe_exchange("No, the lantern was steady tonight, it did not flicker slowly.",
                                 "I hear you; I will look again.", cycle_id="c2")
        got = [json.loads(x) for x in _real_open(ledger, encoding="utf-8")] if ledger.exists() else []
        check(r1 is None and r2 is None, "[4] observe returns None")
        check(len(got) == 2 and got[1]["resolves_prev"] and got[1]["resolves_prev"][0]["prev_row_id"] == got[0]["row_id"],
              f"[4] two rows, second resolves the first's du claim ({len(got)} rows)")
        check(all(x["witness_only"] and x["origin"] == "common_ground_shadow" for x in got), "[4] origin-tagged, witness_only")
        check(set(WRITES) == {str(ledger)}, f"[4] the only write target is the sandbox ledger ({len(WRITES)} opens)")
        n0 = len(WRITES)
        for junk in [(None, "x"), ("x", None), ("", ""), (object(), 5)]:
            cg.observe_exchange(*junk)
        check(len(WRITES) <= n0 + 1, "[4] junk input never raises (fail-open)")
        cg.COMMON_GROUND_SHADOW = False

        # [5]
        src = Path(lab) / "synthetic_founder_J-2523.jsonl"
        with _real_open(src, "w", encoding="utf-8") as fo:
            fo.write(json.dumps({"ts": 1000.0, "cycle_id": "s1", "human": "Your bread recipe needs much more salt.",
                                 "entity": "I watched the lantern flicker slowly tonight beside the window."}) + "\n")
            fo.write(json.dumps({"ts": 1060.0, "cycle_id": "s2",
                                 "human": "No, the lantern was steady tonight, it did not flicker slowly.",
                                 "entity": "I hear you."}) + "\n")
        WRITES.clear()
        s = cg.replay(OUT / "replay_synth_J-2523.jsonl", src)
        check(s["rows"] == 2 and s["resolves_prev"] == {"corrected": 1}, f"[5] synthetic replay: {s}")
        try:
            cg.replay(LIVE / "common_ground_replay_J-2523.jsonl", LIVE / "founder_conversation_log.jsonl")
            check(False, "[5] replay refuses an output inside data/")
        except ValueError:
            check(True, "[5] replay refuses an output inside data/")
        live = cg.replay(OUT / "replay_live_J-2523.jsonl", LIVE / "founder_conversation_log.jsonl")
        print("  LIVE REPLAY SUMMARY:", json.dumps(live))
        check(all(Path(w).resolve().is_relative_to(OUT.resolve()) for w in WRITES),
              f"[5] replay wrote only inside its temp out dir ({len(WRITES)} opens)")
        try:
            import shutil
            shutil.copy(OUT / "replay_live_J-2523.jsonl", Path(sys.argv[1])) if len(sys.argv) > 1 else None
        except Exception as exc:
            print("  (copy of live replay rows skipped:", exc, ")")
    finally:
        builtins.open, io.open = _real_open, _real_io_open

after = {p: h(p) for p in CANARY}
check(before == after, "[5] live canaries unchanged (founder log, ledger, guidance, retractions)")

# [6]
orch = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
i = orch.find("from core import common_ground_shadow as _cg")
block_start = orch.rfind('if output and input_type == "human":', 0, i)
check(i > 0 and block_start > 0 and i - block_start < 6000 and "if _cg.COMMON_GROUND_SHADOW:" in orch[i:i + 200],
      "[6] orchestrator hook sits in the human-output block, behind the flag")
importers = [p for p in list((ROOT / "core").rglob("*.py")) + list((ROOT / "nodes").rglob("*.py"))
             if "common_ground_shadow" in p.read_text(encoding="utf-8", errors="ignore")
             and p.name not in ("orchestrator.py", "common_ground_shadow.py")]
check(not importers, f"[6] no other core/nodes module references it: {[p.name for p in importers]}")
src_txt = (ROOT / "core" / "common_ground_shadow.py").read_text(encoding="utf-8")
imps = set(re.findall(r"^\s*(?:from|import)\s+([\w.]+)", src_txt, re.M))
check(imps <= {"__future__", "json", "logging", "re", "time", "uuid", "pathlib", "core"},
      f"[6] imports only stdlib + core.shadow_log: {sorted(imps)}")
check("from core import shadow_log" in src_txt and src_txt.count("from core import") == 1,
      "[6] the one core import is shadow_log")

print(f"\n{'PASS' if FAILS == 0 else 'FAIL'}: {FAILS} failing checks")
sys.exit(1 if FAILS else 0)
