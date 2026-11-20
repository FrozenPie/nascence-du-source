"""J-2836 (P-0004, F-3496): MemoryRouterNode internal framing + junk 'Key entities' line.

Replays logged memory_router teacher rows (read-only) through the OLD file (git 223c95c6) and the NEW file and
checks: human prompts unchanged except the dropped junk entities line; internal prompts lose the person frame;
the human system prompt is byte-identical. Writes only under a temp dir; touches no live data; no model calls.
"""
import sys, json, subprocess, types, tempfile, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (before lab_env)
from core.schema import CognitiveState, PerceptionOutput  # noqa: E402
import nodes.memory_router_node as new_mod  # noqa: E402
assert Path(new_mod.__file__).resolve().is_relative_to(ROOT), new_mod.__file__

src = subprocess.run(["git", "-C", str(ROOT), "show", "223c95c6:nodes/memory_router_node.py"],
                     capture_output=True, text=True, encoding="utf-8", check=True).stdout
old_mod = types.ModuleType("old_router"); exec(compile(src, "old_router", "exec"), old_mod.__dict__)
New, Old = new_mod.MemoryRouterNode(), old_mod.MemoryRouterNode()

LOG = Path("C:/Nascence/data/training/memory_router.jsonl")   # read-only
rows = [json.loads(l) for l in LOG.open(encoding="utf-8")]
HEAD = 'The person you are speaking with said:\n"'

def state_from(r):
    up = r["user_prompt"]
    assert up.startswith(HEAD + r["raw_input"] + '"\nSummary: '), up[:80]
    rest = up[len(HEAD + r["raw_input"] + '"\nSummary: '):]
    summ, ents = rest.rsplit("\nKey entities: ", 1)
    ents = [] if ents == "none" else ents.split(", ")
    st = CognitiveState(spirit_name="t", axiom="t", raw_input=r["raw_input"], input_type=r["input_type"])
    st.perception = PerceptionOutput(event_type="input", context_type="statement", entities=ents, summary=summ,
                                     **{k: v for k, v in {}.items()})
    return st

# --- system prompt: human byte-identical, internal adds exactly one line --------------------------------------
hs = CognitiveState(spirit_name="t", axiom="t", input_type="human")
isx = CognitiveState(spirit_name="t", axiom="t", input_type="internal")
assert New.system_prompt_for(hs) == New.system_prompt == Old.system_prompt
assert New.system_prompt_for(isx) == New.system_prompt_internal != Old.system_prompt
assert New.system_prompt_internal.replace(New._INTERNAL_SYSTEM_LINE, "") == Old.system_prompt
assert "hint" not in New._INTERNAL_SYSTEM_LINE.lower() and "remember" not in New._INTERNAL_SYSTEM_LINE.lower()

# --- full-log stats ---------------------------------------------------------------------------------------------
def junk_only(ents): return bool(ents) and not New._real_entities(ents)
stats = {"human": [0, 0, 0], "internal": [0, 0, 0]}   # total, junk-only-or-empty (line dropped), changed-human
ok_rows = []
for r in rows:
    try: st = state_from(r)
    except Exception: continue
    ok_rows.append((r, st))
    s = stats.setdefault(r["input_type"], [0, 0, 0]); s[0] += 1
    if not New._real_entities(st.perception.entities): s[1] += 1
    if r["input_type"] == "human":
        np_, op_ = New._build_prompt(st), Old._build_prompt(st)
        if np_ != op_:
            s[2] += 1
            # the only permitted difference: the Key entities line (dropped / shortened)
            assert np_.split("\nKey entities:")[0] == op_.split("\nKey entities:")[0]
print("rows parsed", len(ok_rows), "of", len(rows)); print("stats [total, entities line dropped, human prompts changed]:", stats)

# --- 20-row replay: 10 human + 10 internal, fixed seed ------------------------------------------------------------
random.seed(2836)
hum = [x for x in ok_rows if x[0]["input_type"] == "human"]; internal = [x for x in ok_rows if x[0]["input_type"] != "human"]
pick = random.sample(hum, 10) + random.sample(internal, 10)
n_same = n_ent = n_frame = 0
for r, st in pick:
    np_, op_ = New._build_prompt(st), Old._build_prompt(st)
    if r["input_type"] == "human":
        if np_ == op_: n_same += 1
        else: n_ent += 1
        assert np_.startswith(HEAD)
    else:
        assert np_.startswith("The entity's own thought:\n\"") and "person you are speaking" not in np_
        assert np_.split('"\nSummary:', 1)[0].endswith(r["raw_input"]); n_frame += 1
    assert "the_entity" not in np_ and "the_person" not in np_ and "Key entities: string" not in np_
print(f"replay 20: human identical {n_same}, human entities-line-only diff {n_ent}, internal reframed {n_frame}")

# --- synthetic edge cases -----------------------------------------------------------------------------------------
def mk(ents, it="human"):
    s = CognitiveState(spirit_name="t", axiom="t", raw_input="x", input_type=it)
    s.perception = PerceptionOutput(event_type="input", context_type="statement", entities=ents, summary="s"); return s
assert "Key entities" not in New._build_prompt(mk(["the_entity", "you", "string", "the person the entity is speaking with", "the entity's interlocutor"]))
assert "Key entities" not in New._build_prompt(mk([]))
assert New._build_prompt(mk(["the_world", "garden", "You"])).endswith("Key entities: garden")
assert New._build_prompt(mk(["Maxwell", "渡"], "internal")).endswith("Key entities: Maxwell, 渡")
s0 = CognitiveState(spirit_name="t", axiom="t", raw_input="x", input_type="human")   # no perception
assert New._build_prompt(s0) == Old._build_prompt(s0)
print("J-2836 router prompt test: OK")
