"""J-3409 test: prompt construction, B4 two-stage chaining (stubbed model), few-shot leakage guard, and the report's P1-P3 logic
on a synthetic run. Touches no live data and calls no model: every write goes under a temp dir."""
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parent)); import _hermetic_data; _hermetic_data.install()  # J-3789/J-3583: no write to the tree's data/
import sys, json, tempfile, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import guidance_learning as gl        # core BEFORE lab_env / the lab modules
sys.path.insert(0, str(ROOT / "scripts"))
import lab_guidance_classify2 as M
import lab_guidance_classify2_report as R

assert Path(M.ROOT).resolve() == ROOT, "script must assert its own tree"
fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


# 1. prompts: no angle-bracket placeholder in the new arms; options listed in prose; reverse order really reverses
P = M.prompts()
for a in ("B0", "B2", "B3", "B4", "B0rev", "B2rev", "B3rev", "B4rev"):
    check(f"{a} has no <placeholder>", "<" not in P[a] and ">" not in P[a])
check("B keeps the J-3232 placeholder (verbatim control)", "<same_lesson|compatible_different|contradicts|unrelated>" in P["B"])
check("A is the live prompt verbatim", P["A"] == gl._CLASSIFY_SYS)
check("B2 adds the recall wording, B0 does not", "even if the surface words differ" in P["B2"] and "even if the surface words differ" not in P["B0"])
check("B3 = B2 + two examples", P["B3"].startswith(P["B2"]) and P["B3"].count('{"relation": "') == 2)
check("B0rev lists options reversed", "unrelated, contradicts, compatible_different, same_lesson" in P["B0rev"])
check("B3rev reverses the example order", P["B3rev"].index("compatible_different\"}") < P["B3rev"].index("same_lesson\"}"))
check("B4 has two stages", P["B4"].count("\n---\n") == 1)

# 2. few-shot texts appear in NO evaluation pair (guards the 'from OUTSIDE the evaluation sets' rule)
old = json.load(open(M.OLD / "pairs.json", encoding="utf-8"))
extra = json.load(open(M.OUT / "pairs_extra.json", encoding="utf-8"))
ev = {p["existing"] for p in old + extra} | {p["new"] for p in old + extra}
check("few-shot texts absent from every evaluation pair", all(t not in ev for t in M.SHOT_SAME + M.SHOT_DIFF))
check("20 S3 + 8 N2 extra pairs", sum(p["set"] == "S3" for p in extra) == 20 and sum(p["set"] == "N2" for p in extra) == 8)
hl = json.load(open(M.OUT / "hand_labels_extra.json", encoding="utf-8"))
check("every extra pair is hand-labelled", all(p["id"] in hl["labels"] for p in extra))
check("every S3 pair has a strength 1-3", all(hl["strength"].get(p["id"]) in (1, 2, 3) for p in extra if p["set"] == "S3"))

# 3. B4 chaining with a stubbed chat (no network)
calls = []
seq = iter(['{"same_principle": "no"}', '{"relation": "different"}', '{"same_principle": "yes"}', '{"same_principle": "maybe"}',
            '{"same_principle": "no"}', '{"relation": "contradicts"}'])


def fake_chat(url, model, sys_, user, **kw):
    calls.append(sys_[:40])
    return next(seq)


orig = M.L.chat
M.L.chat = fake_chat
M.ALL_P = P
try:
    check("B4 no->different maps to compat", M.ask("B4", "x", "y")[0] == "different")
    check("B4 yes is one call and maps to same_lesson", M.ask("B4", "x", "y")[0] == "same_lesson" and len(calls) == 3)
    check("B4 off-enum stage-1 answer is invalid (empty relation)", M.ask("B4", "x", "y")[0] == "")
    check("B4 no->contradicts maps to contradicts", M.ask("B4", "x", "y")[0] == "contradicts")
finally:
    M.L.chat = orig

# 4. report logic on a synthetic run in a temp dir
tmp = Path(tempfile.mkdtemp(prefix="J3409_test_"))
try:
    pairs_old = [{"id": f"S-{i}", "set": "S", "existing": "e", "new": "n"} for i in range(4)] + \
                [{"id": f"M-{i}", "set": "M", "existing": "e", "new": "n", "kind": "seed"} for i in range(4)]
    (tmp / "old").mkdir()
    json.dump(pairs_old, open(tmp / "old" / "pairs.json", "w"))
    json.dump({"legend": {}, "labels": {**{f"S-{i}": "S" for i in range(4)}, **{f"M-{i}": "N" for i in range(4)}}},
              open(tmp / "old" / "hand_labels.json", "w"))
    json.dump([{"id": "S3-00", "set": "S3", "existing": "e", "new": "n", "overlap": 0.2, "strength": 1}], open(tmp / "pairs_extra.json", "w"))
    json.dump({"legend": {}, "strength": {"S3-00": 1}, "labels": {"S3-00": "S"}}, open(tmp / "hand_labels_extra.json", "w"))
    rows = []
    for rep in range(3):
        for i in range(4):
            rows.append(dict(pid=f"S-{i}", arm="A", rep=rep, relation="assimilate", raw=""))
            rows.append(dict(pid=f"M-{i}", arm="A", rep=rep, relation="assimilate" if i < 2 else "unrelated", raw=""))
            # GOOD arm: keeps same, drops all false corroboration
            rows.append(dict(pid=f"S-{i}", arm="B2", rep=rep, relation="same_lesson", raw=""))
            rows.append(dict(pid=f"M-{i}", arm="B2", rep=rep, relation="compatible_different", raw=""))
            # BAD arm: loses recall
            rows.append(dict(pid=f"S-{i}", arm="B", rep=rep, relation="compatible_different", raw=""))
            rows.append(dict(pid=f"M-{i}", arm="B", rep=rep, relation="compatible_different", raw=""))
        rows += [dict(pid="S3-00", arm="A", rep=rep, relation="assimilate", raw=""), dict(pid="S3-00", arm="B2", rep=rep, relation="same_lesson", raw=""),
                 dict(pid="S3-00", arm="B", rep=rep, relation="contradicts", raw="")]
    (tmp / "author_runs.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    rep = R.main(tmp, tmp / "old")
    check("good arm B2 passes P1-P3", rep["verdicts"]["B2"]["PASS"] is True)
    check("lossy arm B fails (P1 wrong accommodate + P2 recall)", rep["verdicts"]["B"]["PASS"] is False and rep["verdicts"]["B"]["P1_wrong_accommodates"] == 3)
    check("Q holds exactly the two A-corroborated not-same pairs", sorted(rep["Q_pairs"]) == ["M-0", "M-1"])
    check("P3 reduction for B2 is 100 percent", abs(rep["verdicts"]["B2"]["P3_reduction"] - 1.0) < 1e-9)
    check("report files written under the temp dir", (tmp / "report.md").exists() and (tmp / "report.json").exists())
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("\nFAILED: %s" % fails if fails else "\nALL PASS")
sys.exit(1 if fails else 0)
