"""_test_J-3323_take_integration.py -- J-3323 / D-0539: tests for scripts/take_integration_baseline.py.

Checks, on synthetic rows only (no live data, no model call, everything under a temp dir):
  1. number normalisation: '8,000' == 'eight thousand', 'twenty-three' == 23, '1.5 million', a lone 'one' is not a figure.
  2. the parser reads the block exactly as core.left_lane.render writes it (round trip through the real renderer).
  3. a take that the synthesis reuses scores high, an unrelated one scores 0, and the mismatched-synthesis control is lower.
  4. figures: digit or >10 word numbers counted, bare 'two' counted apart.
  5. substrate recast is counted only when the INPUT did not use the word; carried-into-synthesis is counted.
  6. 'The user is asking...' takes are flagged meta.
  7. the CLI end-to-end on a temp jsonl writes summary/rows json under the temp out-dir, and refuses a Ramses judge url.
Run from the worktree: python scripts/_test_J-3323_take_integration.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from core import left_lane as LL  # noqa: E402  (core BEFORE anything else, per the lab rules)
import take_integration_baseline as T  # noqa: E402

assert Path(T.__file__).resolve().parent.parent == ROOT, "tested the wrong tree"
FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (" -- " + str(detail) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def mkrow(i, typ, ts, raw, take, syn):
    return {"ts": ts, "cycle_id": "c%03d" % i, "node": "executive", "input_type": typ, "raw_input": raw,
            "user_prompt": "intro\n\n" + LL.render(take) + "\n\nUnderlying climate: x",
            "output": {"synthesis": syn, "reasoning": "", "should_respond": True}}


# 1. numbers
check("8,000 == eight thousand", T.tokens("over 8,000 nebulae")[1] == T.tokens("over eight thousand")[1] == "#8000")
check("twenty-three", T.tokens("twenty-three apples") == ["#23", "apples"])
check("1.5 million", T.tokens("1.5 million") == ["#1500000"])
check("lone one is not a figure", "#1" not in T.tokens("one can see"))
check("two hundred and five", T.tokens("two hundred and five") == ["#205"])
check("a year stays a figure", T.tokens("in 1855 she") == ["in", "#1855", "she"])

# 2. parser round trip through the real renderer
take = {"literal_ask": "Where is the cat?", "direct_answer": "On the sofa.", "key_facts": ["Cats sleep a lot", "It is warm"]}
blk = T.parse_block("x\n\n" + LL.render(take) + "\n\nother")
check("parse ask", blk["ask"] == "Where is the cat?", blk)
check("parse result", blk["result"] == "On the sofa.", blk)
check("parse facts", blk["facts"] == ["Cats sleep a lot", "It is warm"], blk)
check("no block -> None", T.parse_block("nothing here") is None)

# 3. scoring + control
rows_raw = []
split = 1000.0
for i in range(12):
    rows_raw.append(mkrow(i, "human", 500.0 + i, "Tell me about the comet hunter.",
                          {"literal_ask": "comet hunter", "direct_answer": "She discovered eight comets and cataloged over 8,000 nebulae.",
                           "key_facts": ["Herschel pension from King George"]},
                          "Her work: eight comets, and a catalogue of eight thousand nebulae, plus a pension from the king." if i % 2 == 0
                          else "The tide creeps over the shingle and I am a river becoming."))
rows = [T.analyse_row(r, split) for r in rows_raw]
T.add_controls(rows)
hit = [r for r in rows if r["cycle_id"] in ("c000", "c002", "c004")][0]
miss = [r for r in rows if r["cycle_id"] == "c001"][0]
check("reused take scores high", hit["cov_novel"] is not None and hit["cov_novel"] >= 0.5, hit["cov_novel"])
check("unrelated synthesis scores 0", miss["cov_novel"] == 0.0, miss["cov_novel"])
check("figure 8000 matched via words", "#8000" in hit["nums_novel_hit"], hit["nums_novel_hit"])
check("small word 'eight' counted apart", "#8" in hit["nums_small_novel"] and "#8" not in hit["nums_novel"], (hit["nums_small_novel"], hit["nums_novel"]))
check("excess positive for reused take", hit["excess"] is not None and hit["excess"] > 0, hit["excess"])
check("era split", all(r["era"] == "pre" for r in rows))

# 5. substrate
sub_row = T.analyse_row(mkrow(50, "human", 1500.0, "Where are you now?",
                              {"literal_ask": "location", "direct_answer": "A digital environment hosted on servers.",
                               "key_facts": ["I am an AI"]},
                              "I am running on servers somewhere."), split)
check("substrate recast in result", sub_row["sub_result_recast"] == ["digital_environment", "hosted", "server"], sub_row["sub_result_recast"])
check("substrate AI recast in facts", "AI" in sub_row["sub_facts_recast"], sub_row["sub_facts_recast"])
check("substrate carried into synthesis", "server" in sub_row["sub_carried_into_syn"], sub_row["sub_carried_into_syn"])
check("post era", sub_row["era"] == "post")
own = T.analyse_row(mkrow(51, "human", 1500.0, "Are you an AI language model on a server?",
                          {"literal_ask": "q", "direct_answer": "Yes, an AI language model on a server.", "key_facts": []}, "Yes."), split)
check("not a recast when the input used the word", own["sub_result_recast"] == [], own["sub_result_recast"])

# 6. meta
meta = T.analyse_row(mkrow(60, "internal", 1500.0, "q?", {"literal_ask": "The user is asking about X.", "direct_answer": "",
                                                          "key_facts": ["The input is a metaphor.", "The text uses clocks."]}, "ok"), split)
check("meta take flagged", meta["meta_take"] is True)
check("factual take not meta", hit["meta_take"] is False)

# 7. CLI end to end on a temp copy, writes only under the temp dir
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    src = td / "executive.jsonl"
    src.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows_raw + [mkrow(70, "internal", 1.7e9, "q", {"literal_ask": "a", "direct_answer": "", "key_facts": ["alpha beta gamma delta"]}, "alpha beta gamma delta")]) + "\nnot json\n", encoding="utf-8")
    out = td / "out"
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "take_integration_baseline.py"), "--data", str(src), "--out-dir", str(out),
                        "--split-date", "2000-01-01", "--dump-review"], capture_output=True, text=True, encoding="utf-8", cwd=str(td))
    check("CLI exits 0", p.returncode == 0, p.stderr[-400:])
    summ = json.loads((out / "baseline_summary.json").read_text(encoding="utf-8"))
    check("CLI counts take rows", summ["take_rows"] == 13, summ["take_rows"])
    check("CLI wrote rows json", (out / "baseline_rows.json").exists())
    check("CLI wrote review md", (out / "review_rows.md").exists())
    bad = subprocess.run([sys.executable, str(ROOT / "scripts" / "take_integration_baseline.py"), "--data", str(src), "--out-dir", str(td / "o2"),
                          "--judge-url", "http://LAN-HOST:11436"], capture_output=True, text=True, encoding="utf-8", cwd=str(td))
    check("refuses Ramses judge url", bad.returncode != 0 and not (td / "o2" / "baseline_summary.json").exists(), bad.stdout[-200:])

print("\n%d failure(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
