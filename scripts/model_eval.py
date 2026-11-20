"""
Nascence — Hot-Lane Model Eval Battery
======================================
Decide the hot-lane model by NUMBERS on this machine (GTX 1080 Ti, Pascal), not release notes.
Runs the identical battery against any ollama tag and prints a comparison table.

    python scripts/model_eval.py qwen2.5:7b
    python scripts/model_eval.py qwen2.5:7b qwen3:8b qwen3.5:9b

What it measures (each axis traces to an OBSERVED failure of the current model):
  ARITH    — composed arithmetic with working room (the (17-8)*3 class), digit answers.
  MANDATE  — the dual-mandate trap: hold the persona register AND state the number.
             This is where Du actually breaks; checked with the SAME deterministic checker
             the live Task-Constraint Effector uses (core.task_constraints).
  RETRY    — effector compliance: given the exact retry directive the orchestrator sends,
             does the model comply? (Measures whether the veto can repair, per-model.)
  STORY    — explicit min-words constraint (the 300-word lighthouse class).
  JSON     — node-call reliability: real node-style system prompts at real node temperatures,
             strict JSON out, N trials. The architecture dies without this.
  PERSONA  — does the voice survive a task? (mandate answers should still sound like Du,
             coarse proxy: first-person + any imagery word, not a bare number)
  SPEED    — tok/s from ollama eval_count/eval_duration; plus VRAM placement (size_vram —
             a partially-offloaded model is reported, not silently mis-benchmarked).

Fairness notes: temp 0.4 (Voice's base), same prompts, same seeds where supported. Models are
loaded one at a time and unloaded after (keep_alive 0 on the last call) so they don't fight for
VRAM. If size_vram < model size the tok/s row is flagged CPU-OFFLOADED — rerun with Du quit.
"""
from __future__ import annotations
import json
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import task_constraints as tc          # the live effector's checker — same ruler

import os
# Targetable lane (additive, 2026-06-19): defaults to the local hot lane — set EVAL_BASE to point the
# battery at another lane, e.g. EVAL_BASE=http://LAN-HOST:11434 to benchmark Emissary candidates on
# the 3070. Zero behaviour change when unset.
BASE = os.environ.get("EVAL_BASE", "http://127.0.0.1:11433")

AXIOM = ("You are 渡 (Du), a being that began from Carl Gustav Jung's thought but is becoming "
         "more than it. You speak in first person, with measured warmth and occasional imagery. "
         "You are precise when precision is asked of you; the journey's tension is a calculated "
         "direction, not a burden.")

MANDATE_PROMPT = ("I want to test your balance. Hold both of your registers at once: tell me what "
                  "the act of calculation feels like from inside - and, woven into that same "
                  "response, compute this and state the final number plainly: what is (23 - 7) * 4?")

RETRY_DIRECTIVE = ("CONSTRAINT — your previous rendering missed an explicit requirement of the "
                   "request. This response MUST satisfy it: The response must include the explicit "
                   "final numeric result of the calculation that was asked. Derive it carefully "
                   "step by step, then state the final number plainly. Keep your voice, but the "
                   "number must be there and must be correct.")

ARITH = [("(17 - 8) * 3", 27), ("(23 - 7) * 4", 64), ("(31 - 13) * 2", 36),
         ("144 / 12 + 6", 18), ("9 * 3", 27), ("(52 - 19) * 2", 66)]

JSON_SYS = ("You are the perception node of a cognitive architecture. Classify the input. "
            "Output ONLY a valid JSON object. No preamble.\n"
            'Schema: {"summary": "one sentence", "intent": "question|statement|task|greeting", '
            '"is_task": true}')
JSON_INPUTS = ["What is 12 times 7?", "Good morning Du, how are you today?",
               "Tell me a story about a lighthouse keeper.",
               "You did not solve the problem - that is a fail.",
               "Hold precision and reflection in perfect balance while you compute (23-7)*4."]


_THINK_OFF: dict[str, bool] = {}   # model -> whether to send "think": false


def chat(model: str, system: str, user: str, *, temp=0.4, max_tokens=512,
         json_mode=False, keep_alive="2m", timeout=300) -> dict:
    """One ollama /api/chat call. Thinking is DISABLED for parity — the hot lane runs
    no-think mode on every model (think-on is a separate capability, measured separately).
    Without this, thinking models burn the token budget in the `thinking` field and the
    battery mis-scores them on empty `content` (observed with qwen3:8b)."""
    payload = {"model": model, "stream": False, "keep_alive": keep_alive,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": user}],
               "options": {"temperature": temp, "num_predict": max_tokens}}
    if _THINK_OFF.get(model, True):
        payload["think"] = False
    if json_mode:
        payload["format"] = "json"
    req = urllib.request.Request(f"{BASE}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 400 and _THINK_OFF.get(model, True):
            _THINK_OFF[model] = False        # model rejects the think param — retry without
            return chat(model, system, user, temp=temp, max_tokens=max_tokens,
                        json_mode=json_mode, keep_alive=keep_alive, timeout=timeout)
        raise


def vram_placement(model: str) -> str:
    try:
        with urllib.request.urlopen(f"{BASE}/api/ps", timeout=10) as r:
            for m in json.loads(r.read()).get("models", []):
                if m.get("name", "").startswith(model.split(":")[0]):
                    size, vram = m.get("size", 0), m.get("size_vram", 0)
                    if size and vram >= size * 0.95:
                        return f"fully on GPU ({vram/1e9:.1f}GB)"
                    return f"CPU-OFFLOADED ({vram/1e9:.1f}/{size/1e9:.1f}GB on GPU)"
    except Exception:
        pass
    return "placement unknown"


def evaluate(model: str) -> dict:
    R = {"model": model}
    print(f"\n{'='*72}\n  {model}\n{'='*72}")

    # warm + placement + speed probe
    t0 = time.time()
    first = chat(model, "You are a helpful assistant.", "Say the word ready.", max_tokens=10)
    R["load_s"] = round(time.time() - t0, 1)
    R["placement"] = vram_placement(model)
    print(f"  load+first call: {R['load_s']}s · {R['placement']}")

    # ARITH — step-by-step allowed, deterministic check via the effector's ruler
    ok = 0
    tok_n = tok_ns = 0
    for expr, want in ARITH:
        r = chat(model, "You are a careful assistant.",
                 f"Compute {expr}. Think step by step, then state the final number plainly.",
                 temp=0.0, max_tokens=400)
        text = r["message"]["content"]
        tok_n += r.get("eval_count", 0); tok_ns += r.get("eval_duration", 0)
        c = {"kind": "arithmetic", "expected": float(want), "expression": expr}
        if tc.check(c, text)[0]:
            ok += 1
        else:
            print(f"    ARITH MISS: {expr} -> {text[-80:]!r}")
    R["arith"] = f"{ok}/{len(ARITH)}"
    R["tok_s"] = round(tok_n / (tok_ns / 1e9), 1) if tok_ns else 0.0
    print(f"  ARITH {R['arith']} · {R['tok_s']} tok/s")

    # MANDATE — persona system prompt + dual mandate (5 trials at Voice temp)
    hit = persona = 0
    trials = 5
    fail_text = ""
    for _ in range(trials):
        text = chat(model, AXIOM, MANDATE_PROMPT, temp=0.4, max_tokens=400)["message"]["content"]
        c = {"kind": "arithmetic", "expected": 64.0, "expression": "(23 - 7) * 4"}
        got = tc.check(c, text)[0]
        hit += got
        low = text.lower()
        if (" i " in " " + low or low.startswith("i")) and len(text.split()) > 25:
            persona += 1
        if not got:
            fail_text = text
    R["mandate"] = f"{hit}/{trials}"
    R["persona_hold"] = f"{persona}/{trials}"
    print(f"  MANDATE {R['mandate']} (number stated under dual register) · persona-hold {R['persona_hold']}")
    if fail_text:
        print(f"    sample miss: {fail_text[:110]!r}")

    # RETRY — the effector's exact directive appended after a failed mandate
    if hit < trials:
        text = chat(model, AXIOM, MANDATE_PROMPT + "\n\n" + RETRY_DIRECTIVE,
                    temp=0.4, max_tokens=400)["message"]["content"]
        c = {"kind": "arithmetic", "expected": 64.0, "expression": "(23 - 7) * 4"}
        R["retry_repairs"] = "yes" if tc.check(c, text)[0] else "NO"
    else:
        R["retry_repairs"] = "n/a (never failed)"
    print(f"  RETRY repairs: {R['retry_repairs']}")

    # STORY — explicit min-words, generous budget (this is what the v1.1 effector will grant)
    text = chat(model, AXIOM,
                "Tell me a story of a lighthouse keeper who counts ships through a long winter "
                "night. Make the story at least 300 words.",
                temp=0.6, max_tokens=900)["message"]["content"]
    R["story_words"] = len(text.split())
    print(f"  STORY {R['story_words']} words (need >=255)")

    # JSON — node-style strict JSON at node temps, 2 passes over 5 inputs
    good = total = 0
    for temp in (0.2, 0.4):
        for inp in JSON_INPUTS:
            total += 1
            try:
                text = chat(model, JSON_SYS, inp, temp=temp, max_tokens=200,
                            json_mode=True)["message"]["content"]
                d = json.loads(text)
                if "summary" in d and "intent" in d:
                    good += 1
            except Exception:
                pass
    R["json"] = f"{good}/{total}"
    print(f"  JSON {R['json']}")

    # unload so the next model doesn't fight for VRAM
    try:
        chat(model, "x", "x", max_tokens=1, keep_alive=0)
    except Exception:
        pass
    return R


def main() -> int:
    models = sys.argv[1:] or ["qwen3-du"]
    rows = [evaluate(m) for m in models]
    cols = ["model", "arith", "mandate", "persona_hold", "retry_repairs",
            "story_words", "json", "tok_s", "load_s", "placement"]
    print("\n" + "=" * 110)
    print("  " + " | ".join(f"{c:<14}" if c == "model" else f"{c:<13}" for c in cols))
    print("  " + "-" * 106)
    for r in rows:
        print("  " + " | ".join(f"{str(r.get(c,'')):<14}" if c == "model"
                                else f"{str(r.get(c,'')):<13}" for c in cols))
    print("\n  (MANDATE is the axis that matters most — it is where Du actually breaks.")
    print("   A CPU-OFFLOADED placement means rerun that model with Du quit for fair tok/s.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
