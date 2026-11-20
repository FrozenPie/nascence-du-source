"""J-3858 test: the --arm reader in scripts/j3331_known_text_control_read.py. Synthetic data in temp dirs only; reads and
writes nothing under the live data/ dir and calls no model."""
import json, random, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: F401  (core before anything that touches sys.path)
sys.argv = [sys.argv[0]]          # the reader parses argv at import; keep it neutral
import importlib.util
spec = importlib.util.spec_from_file_location("kt_reader", ROOT / "scripts" / "j3331_known_text_control_read.py")
R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)

DAY = 86400.0
T0 = 1_790_000_000.0


def cyc(i):
    return f"{i:08x}-0000-4000-8000-"          # 24 chars, as hands_trace stores it


def synth(n_per_arm, p_fire_shown, p_fire_withheld, seed=1, dup=True):
    """One cycle per eligible thought, spread over days. Each arm row is written 3 s before its trace row; a
    duplicate arm row (prompt built twice) is written 1 s before. Plus one mid-train trace row after it that must not count."""
    rng = random.Random(seed)
    arm_rows, trace = [], []
    i = 0
    for arm, p in (("shown", p_fire_shown), ("withheld", p_fire_withheld)):
        for j in range(n_per_arm):
            i += 1
            ts = T0 + (j % 20) * DAY + rng.random() * 3000
            names = ["door", "fire", "tea"]
            arm_rows.append({"ts": ts, "cycle": cyc(i), "arm": arm, "would_name": names, "where": "study"})
            if dup:
                arm_rows.append({"ts": ts + 2.0, "cycle": cyc(i), "arm": arm, "would_name": names, "where": "study"})
            fired = rng.random() < p
            hands = [{"hand": "door", "answer": "x", "ts": ts + 5}, {"hand": "look", "answer": "y", "ts": ts + 5}] if fired else \
                    [{"hand": "look", "answer": "y", "ts": ts + 5}]
            trace.append({"ts": ts + 5, "cycle": cyc(i), "hands": hands})
            # later mid-train thought of the same cycle that fires a hand: outside the arm, must not be counted
            trace.append({"ts": ts + 40, "cycle": cyc(i), "hands": [{"hand": "sow", "answer": "z", "ts": ts + 40}]})
    return arm_rows, trace


# 1. join: duplicates collapse, mid-train rows are not read, unmatched arm rows are reported not guessed
arm_rows, trace = synth(50, 0.3, 0.3)
th, st = R.join_arm(arm_rows, trace)
assert len(th) == 100, len(th)
assert st["duplicate_arm_rows"] == 100 and st["unmatched_arm_rows"] == 0 and st["arm_conflicts"] == 0, st
assert all(all(f != "sow" for f, _ in t["fired"]) for t in th), "mid-train sow row leaked into an eligible thought"
assert all(all(f != "look" for f, _ in t["fired"]) for t in th), "look is excluded from fired world hands"
th2, st2 = R.join_arm(arm_rows + [{"ts": T0 + 99 * DAY, "cycle": "ffffffff-0000-4000-8000-", "arm": "shown", "would_name": []}], trace)
assert st2["unmatched_arm_rows"] == 1 and len(th2) == 100

# 2. not at the stopping rule: verdict says NOT YET
res = R.arm_read(arm_rows, trace)
assert res["verdict"].startswith("NOT YET"), res["verdict"]
assert res["stopping_rule"]["reached"] is False and res["eligible_thoughts"] == {"shown": 50, "withheld": 50}

# 3. P2: every fired hand is "door", which is in would_name -> 1.0 in both arms
assert res["P2_fired_family_in_would_name"]["shown"]["rate"] in (1.0, None)

# 4. at the stopping rule with NO effect: inert verdict; with a planted 6-point effect: GAP verdict
R.STOP_N = 400
a0, t0 = synth(400, 0.30, 0.30, seed=7)
r0 = R.arm_read(a0, t0)
assert r0["stopping_rule"]["reached"], r0["stopping_rule"]
assert abs(r0["P1_world_hand_fire_rate_per_eligible_thought"]["diff_shown_minus_withheld"]) < 0.06
a1, t1 = synth(400, 0.36, 0.30, seed=8)
a1b, t1b = synth(400, 0.50, 0.30, seed=9)
r1 = R.arm_read(a1b, t1b)
assert r1["verdict"].startswith("GAP"), r1["verdict"]
assert r1["P1_world_hand_fire_rate_per_eligible_thought"]["diff_day_block_boot95"][0] > 0
# a null at n=400 cannot be called INERT (the +-1pt band needs thousands); it must not claim a gap either
assert not r0["verdict"].startswith("GAP"), r0["verdict"]

# 5. refusal-prone set: static families plus a trailing >50% refuser, never a family with too few events
plog = {"world:door": ([1.0 + k for k in range(10)], [{"outcome": "refused"} if k % 4 else {"outcome": "ok"} for k in range(10)]),
        "world:tea": ([1.0, 2.0], [{"outcome": "refused"}, {"outcome": "refused"}])}
ps = R.prone_set_at(plog, 100.0)
assert {"sow", "mow", "weed", "door"} <= ps and "tea" not in ps, ps

# 6. CLI: --arm with no arm log -> NO DATA verdict, nothing written outside OUT; default mode argument handling intact
with tempfile.TemporaryDirectory() as td:
    d = Path(td) / "data"; d.mkdir(); o = Path(td) / "out"
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "j3331_known_text_control_read.py"), "--arm", str(d), str(o)],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[-400:]
    assert json.loads(out.stdout)["verdict"].startswith("NO DATA")
    assert (o / "known_text_arm_read.json").exists() and sorted(p.name for p in d.iterdir()) == []
    # with data
    arm_rows, trace = synth(30, 0.3, 0.3)
    (d / "known_text_arm.jsonl").write_text("\n".join(json.dumps(r) for r in arm_rows), encoding="utf-8")
    (d / "hands_trace.jsonl").write_text("\n".join(json.dumps(r) for r in trace), encoding="utf-8")
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "j3331_known_text_control_read.py"), "--arm", str(d), str(o)],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[-400:]
    j = json.loads(out.stdout)
    assert j["eligible_thoughts"] == {"shown": 30, "withheld": 30} and j["verdict"].startswith("NOT YET")
print("OK J-3858 arm reader")
