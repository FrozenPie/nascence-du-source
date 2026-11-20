"""J-1954 / D-0367: gauges-as-words prompt replay. OFFLINE -- builds prompts only, never calls a model.

  python scripts/_test_gauges_words_j1954.py dump AFFECT_LOG [N]   -> JSON of rendered prompts for the last N
        real affect_log rows (read-only), built by THIS tree
  python scripts/_test_gauges_words_j1954.py check AFFECT_LOG HEAD_TREE [N]
        -> runs `dump` here and in HEAD_TREE (a throwaway `git worktree add <path> HEAD`) and asserts
           (a) zero digits / gauge variable names on the gauge lines of every rendered prompt in THIS tree,
           (b) every line that differs from HEAD is a gauge line (nothing else in the prompts moved),
           (c) the joy-vs-heavy-mood contradiction no longer appears.

Live-store safety: core is imported BEFORE anything else and asserted to live inside the tree under test; the
felt_preamble log path is redirected to a temp file; AFFECT_LOG is only read."""
import sys, os, json, re, subprocess, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core  # noqa: E402  -- BEFORE anything that could touch data/
assert os.path.abspath(core.__file__).lower().startswith(ROOT.lower()), (core.__file__, ROOT)

GAUGE_PREFIX = ("Emotion", "Emotion right now", "Salience:", "Reflection confidence:", "Critic:", "Emotional state:",
                "FELT NOW:", "How you are just now:", "Your current mood:", "Right now you are carrying",
                "Attention (your own focus", "ATTENDING TO:", "ATTENTION (your own focus")
BAD = re.compile(r"\d|valence|arousal|confidence=|urgency=|relevance", re.I)


def _rows(path, n):
    rows = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try: rows.append(json.loads(ln))
            except Exception: pass
    return rows[-n:]


def dump(path, n):
    import tempfile
    from core import mood
    mood._FP_LOG = type(mood._FP_LOG)(os.path.join(tempfile.mkdtemp(prefix="j1954_"), "fp.jsonl"))
    from core.schema import (CognitiveState, AffectState, EmotionOutput, SalienceOutput, ReflectionOutput,
                             CriticOutput, AttentionSchema, PerceptionOutput)
    from nodes.executive_node import ExecutiveNode
    from nodes.reflection_node import ReflectionNode
    from nodes.voice_node import VoiceNode
    out = []
    for i, r in enumerate(_rows(path, n)):
        af = r.get("affect") or {}
        em = r.get("emotion") or {}
        aff = AffectState(**{k: float(af.get(k, 0.0)) for k in
                             ("joy", "fear", "anger", "trust", "surprise", "disgust", "valence", "arousal")})
        emo = EmotionOutput(joy=aff.joy, fear=aff.fear, anger=aff.anger, trust=aff.trust, surprise=aff.surprise,
                            disgust=aff.disgust, valence=float(em.get("valence", 0.0)),
                            arousal=float(em.get("arousal", 0.3)), primary=em.get("primary", "calm"))
        st = CognitiveState(spirit_name="Du", axiom="YOUR NAME: Du\nVOICE STYLE: plain.")
        st.raw_input = "test question"; st.input_type = "human"
        st.perception = PerceptionOutput(event_type="input", context_type="question", entities=[], summary="synthetic")
        st.affect = aff; st.emotion = emo
        st.salience = SalienceOutput(urgency=min(1.0, 0.1 + (i % 10) / 10), focus=["a", "b"], interrupt=False, reasoning="r")
        st.attention = AttentionSchema(focus=["x"], driver="novelty", bandwidth=(i % 100) / 100.0)
        st.reflection = ReflectionOutput(draft="d", confidence=(i % 100) / 100.0, needs_more_memory=False, emotionally_aligned=True)
        st.critic = CriticOutput(approved=(i % 3 != 0), confidence=(i % 100) / 100.0, identity_consistent=True,
                                 corrections=["fix"] if i % 3 == 0 else [])
        mood._cache_scalars(emo)
        lines = []
        for nm, node in (("exec", ExecutiveNode()), ("refl", ReflectionNode())):
            try: lines += [(nm, ln) for ln in node._build_prompt(st).split("\n")]
            except Exception as e: lines.append((nm, "BUILD-ERROR " + repr(e)))
        lines.append(("felt_descriptor", aff.felt_descriptor()))
        fw = getattr(mood, "current_felt_words", None)
        lines.append(("voice_felt", "How you are just now: " + (fw() if fw else mood.current_felt())))
        try:
            lines.append(("attn", st.attention.note()))
        except Exception as e: lines.append(("attn", "ERR " + repr(e)))
        mlw = getattr(mood, "mood_line_words", None)
        lines.append(("idle_mood", mlw(aff) if mlw else
                      f"Your current mood: valence {aff.valence:+.2f}, arousal {aff.arousal:.2f}, surprise {aff.surprise:.2f}, fear {aff.fear:.2f}."))
        out.append({"i": i, "lines": lines})
    print(json.dumps(out, ensure_ascii=False))


def _dump_in(tree, path, n):
    r = subprocess.run([sys.executable, os.path.join(tree, "scripts", "_test_gauges_words_j1954.py"), "dump", path, str(n)],
                       cwd=tree, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def check(path, head_tree, n):
    import shutil
    now = _dump_in(ROOT, path, n)
    dst = os.path.join(head_tree, "scripts", "_test_gauges_words_j1954.py")
    shutil.copy(os.path.abspath(__file__), dst)
    try: head = _dump_in(head_tree, path, n)
    finally: os.remove(dst)
    fails, gauge_lines, digits_head, contra_head, contra_now = [], 0, 0, 0, 0
    for a, b in zip(now, head):
        assert a["i"] == b["i"]
        ha = [x for x in a["lines"]]; hb = set(map(tuple, b["lines"])); na = set(map(tuple, a["lines"]))
        for nm, ln in a["lines"]:
            if ln.startswith("BUILD-ERROR") or ln.startswith("ERR "):
                fails.append(f"row {a['i']} {nm}: {ln}")
            if ln.lstrip(" -").startswith(GAUGE_PREFIX) or nm in ("felt_descriptor", "voice_felt", "attn", "idle_mood"):
                gauge_lines += 1
                if BAD.search(ln):
                    fails.append(f"row {a['i']} {nm}: gauge line carries digit/name: {ln!r}")
            if "heavy mood" in ln and "joy" in ln: contra_now += 1
            if (nm, ln) not in hb and not (ln.lstrip(" -").startswith(GAUGE_PREFIX) or nm in ("felt_descriptor", "voice_felt", "attn", "idle_mood")):
                fails.append(f"row {a['i']} {nm}: NON-gauge line changed vs HEAD: {ln!r}")
        for nm, ln in b["lines"]:
            if BAD.search(ln) and (ln.lstrip(" -").startswith(GAUGE_PREFIX) or nm in ("felt_descriptor", "voice_felt", "attn", "idle_mood")):
                digits_head += 1
            if "heavy mood" in ln and "joy" in ln: contra_head += 1
    print(json.dumps({"rows": len(now), "gauge_lines_checked": gauge_lines, "head_gauge_lines_with_digits_or_names": digits_head,
                      "contradiction_head": contra_head, "contradiction_now": contra_now, "fails": len(fails)}))
    for f in fails[:15]: print("FAIL", f)
    if contra_now: sys.exit(1)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    # J-4052: this is a two-argument CLI (dump / check), not a no-argument test; run bare it used to die with an IndexError that
    # a test runner reads as a logic failure. Bare, it now prints its usage and exits 0 (nothing was checked, and it says so).
    if len(sys.argv) < 2 or sys.argv[1] not in ("dump", "check"):
        print("usage: _test_gauges_words_j1954.py dump AFFECT_LOG [N] | check AFFECT_LOG HEAD_TREE [N]  -- no arguments given, nothing checked")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "dump": dump(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 300)
    else: check(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 300)
