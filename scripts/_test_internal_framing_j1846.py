"""D-0355 / J-1846 (2026-10-07): honest framing of internal cycles in the perception, executive and
voice prompts (state.input_type != "human"). OFFLINE -- builds prompts only, never calls a model.

  python scripts/_test_internal_framing_j1846.py dump            -> JSON of every prompt this tree builds
  python scripts/_test_internal_framing_j1846.py check HEAD_TREE -> runs `dump` in THIS tree and in
        HEAD_TREE (a throwaway `git worktree add <path> HEAD`), then asserts
          (a) every HUMAN prompt is byte-identical between the two trees,
          (b) the INTERNAL prompts carry none of the human-framing phrases and do carry the ruled wording.

Live-store safety: core is imported BEFORE anything else and asserted to live inside the tree under
test; the scene/mood readers the voice prompt calls are replaced by fixed strings so nothing reads
data/ and the human-prompt comparison is deterministic."""
import sys, os, json, subprocess
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core  # noqa: E402  -- BEFORE anything that could touch data/
assert os.path.abspath(core.__file__).lower().startswith(ROOT.lower()), (core.__file__, ROOT)

QUESTION = "How does the term 'X' relate to the historical context of Y?"
AXIOM = ("YOUR NAME: Du\nORIGIN: synthetic test axiom\nVOICE STYLE: plain, warm.\n"
         "SPEAKING CONSTRAINTS: no lectures.")


def _state(input_type):
    from core.schema import CognitiveState, PerceptionOutput, ExecutiveOutput
    st = CognitiveState(spirit_name="Du", axiom=AXIOM)
    st.raw_input = QUESTION
    st.input_type = input_type
    st.perception = PerceptionOutput(event_type="input", context_type="question", entities=[],
                                     summary="synthetic")
    st.executive = ExecutiveOutput(synthesis="SYNTHESIS-TEXT", should_respond=True,
                                   response_type="answer", reasoning="r")
    st.conversation_history = [{"human": "hello", "entity": "hi there"}]
    return st


def dump():
    from core import sensorium, mood
    sensorium.scene_line = lambda *a, **k: "SCENE-LINE"
    mood.current_felt = lambda *a, **k: "FELT-LINE"
    mood.current_felt_words = lambda *a, **k: "FELT-LINE"   # J-1954: voice reads the words renderer now
    from nodes.perception_node import PerceptionNode
    from nodes.executive_node import ExecutiveNode
    from nodes.voice_node import VoiceNode
    out = {}
    for it in ("human", "internal", "timer"):
        st = _state(it)
        p, e, v = PerceptionNode(), ExecutiveNode(), VoiceNode()
        sp = getattr(p, "system_prompt_for", None)
        out[it] = {
            "perception_system": sp(st) if sp else p.system_prompt,
            "perception_user":   p._build_prompt(st),
            "executive_system":  (e.system_prompt_for(st) if hasattr(e, "system_prompt_for") else e.system_prompt),
            "executive_user":    e._build_prompt(st),
            "voice_system":      (v.system_prompt_for(st) if hasattr(v, "system_prompt_for") else v.system_prompt),
            "voice_user":        v._build_prompt(st),
        }
    print(json.dumps(out, ensure_ascii=False))


def _dump_in(tree):
    r = subprocess.run([sys.executable, os.path.join(tree, "scripts", "_test_internal_framing_j1846.py"), "dump"],
                       cwd=tree, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def check(head_tree):
    now = dump_self()
    # HEAD has no copy of this test file: ship the dump logic by running THIS file with cwd=head tree.
    import shutil
    shutil.copy(os.path.abspath(__file__), os.path.join(head_tree, "scripts", "_test_internal_framing_j1846.py"))
    try:
        head = _dump_in(head_tree)
    finally:
        os.remove(os.path.join(head_tree, "scripts", "_test_internal_framing_j1846.py"))
    fails = []
    # (a) human byte-identical
    for k in now["human"]:
        if now["human"][k] != head["human"][k]:
            fails.append(f"HUMAN prompt changed: {k}")
    # input_type 'timer' is also != human: it follows the internal path, so just check it equals internal
    for k in now["internal"]:
        if now["timer"][k] != now["internal"][k]:
            fails.append(f"timer != internal: {k}")
    # (b) internal carries none of the human framing
    banned = ["Travis has just said", "The person you are speaking with", "what you say to Travis",
              "speaking with Travis", "HUMAN INTERLOCUTOR", "The person says", "to him now",
              "a separate person"]
    internal_text = {k: v for k, v in now["internal"].items() if k not in ("executive_system",)}
    for k, v in internal_text.items():
        for b in banned:
            if b in v:
                fails.append(f"internal {k} still contains {b!r}")
    must = {
        "perception_system": ["This is the entity's OWN thought, not a person's speech; summarise it in the first person."],
        "executive_user":    ["A question has risen in you, unprompted:"],
        "voice_user":        ["A question rose in you on your own; no one asked it:"],
        "voice_system":      ["what you say aloud, to yourself"],
    }
    for k, ms in must.items():
        for m in ms:
            if m not in now["internal"][k]:
                fails.append(f"internal {k} missing ruled wording {m!r}")
    # the question itself is passed through untouched everywhere it is quoted
    for k in ("perception_user", "executive_user", "voice_user"):
        if QUESTION not in now["internal"][k]:
            fails.append(f"internal {k} lost the question text")
    # the human prompts still carry the human wording (sanity that the test is not vacuous)
    for k, m in (("executive_user", "The person you are speaking with has just said to you:"),
                 ("voice_user", "Travis has just said to you:"), ("voice_system", "what you say to Travis"),
                 ("perception_system", "HUMAN INTERLOCUTOR")):
        if m not in now["human"][k]:
            fails.append(f"human {k} lost {m!r} (test vacuous or human path changed)")
    print("FAILS:" if fails else "ALL PASS", *fails, sep="\n  ")
    return 1 if fails else 0


def dump_self():
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "dump"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    if sys.argv[1:2] == ["dump"]:
        dump()
    elif sys.argv[1:2] == ["check"]:
        sys.exit(check(os.path.abspath(sys.argv[2])))
    else:
        print(__doc__)
