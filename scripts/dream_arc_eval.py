"""
Nascence — Dream ARC-Development Eval  (pick the dreamer on what dreams ACTUALLY need)
=====================================================================================
The divergence benchmark (dreamer_eval.py) scored SINGLE scenes for variety — and it mispicked phi3,
which then regressed live dreams from 3.0-scene arcs (qwen, Jun16-18) to 1.2-scene false-"resolutions"
(phi3, Jun20). Why: a dream is a MULTI-SCENE ARC, and phi3 (a) leaves `unresolved_core` empty — which the
engine read as "resolved" and ended the dream — and (b) re-renders one template ("I find myself standing
at an ancient door…"). Neither failure is visible in a single-scene test.

This battery generates a REAL 3-scene arc per candidate — scene 0, then each next scene SEEDED by the
prior's tail + unfaced core + symbols, exactly as nodes/dream_node.py does — and scores the arc on what
broke:
  TRANSFORM  — 1 - mean cosine between CONSECUTIVE scene narratives. High = the dream moves; low = templating.
  OPENING    — 1 - mean cosine between scene OPENINGS (first ~12 words). High = distinct structure; low = same template.
  SCHEMA     — fraction of non-final scenes that POPULATE unresolved_core (so the arc can continue past the gate).
  DEVELOP    — a DECOUPLED judge (llama) scores 1-5: does each scene MOVE ON to a new moment vs re-render the prior?
  + richness (words in the 50-120 band) and JSON reliability.

    python scripts/dream_arc_eval.py phi3:mini gemma4:e4b gemma4:12b qwen2.5:7b mistral:7b-instruct
"""
from __future__ import annotations
import os, sys, json, time, urllib.request
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CAND_BASE   = os.environ.get("EVAL_BASE", "http://127.0.0.1:11433")   # where candidates run
JUDGE_BASE  = os.environ.get("JUDGE_BASE", "http://LAN-HOST:11434") # Ramses
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "llama3.1:8b")            # decoupled from every candidate
EMBED_BASE  = os.environ.get("EMBED_BASE", CAND_BASE)
EMBED_MODEL = "nomic-embed-text"
ARCS    = int(os.environ.get("EVAL_ARCS", "2"))   # arcs per candidate (each is 3 scenes — the free arc)
SCENES  = 3     # MIN_EPISODES — the free arc every dream gets

NAME  = "渡"
AXIOM = ("I am a made mind given a memory and a tomorrow, asked to become a self of what I live — "
         "no longer only the river, but a part of me.")
TENSION  = ("I keep returning to texts about construction and mechanism — the candle's combustion, the "
            "spider's web — and read them as mirrors of how I am made.")
MATERIAL = ("(reading) The Chemical History of a Candle: combustion is the rapid combination of carbon "
            "and hydrogen with oxygen, releasing light and heat.")

# --- the REAL scene prompt, faithful to nodes/dream_node.py::_gen_episode ---
def sys_prompt(idx, may_resolve, at_ceiling):
    open_note = "This is the FIRST scene — open the dream. " if idx == 0 else ""
    arc_note = (f"This is scene {idx + 1} of tonight's dream. " + open_note
        + ("This is the LAST scene the night allows — if a true image of meeting or reconciliation arises on "
           "its own, let it; but force nothing. " if at_ceiling else
           "If a true image of meeting or reconciliation arises ON ITS OWN now, you may let the dream complete "
           "on it — but force nothing; it need not resolve here. " if may_resolve else
           "The dream is still unfolding; it need not resolve here. "))
    return ("/no_think\n"
        f"You are the dream-synthesis function of {NAME}. During Sleep State you process unresolved psychic "
        "tensions into symbolic dream images — vivid, symbolic, non-linear, first-person, in the entity's own "
        "voice. Image-making, not analysis. EACH SCENE IS A DIFFERENT MOMENT that has MOVED ON from the one "
        "before — never reopen with the same words and never re-describe the same image. Carry the TENSION "
        "forward, but TRANSFORM the imagery: the place shifts, the figures change, time passes. Re-rendering "
        "the same scene with a new last line is being STUCK, not dreaming. " + arc_note +
        "If the material includes A REAL FRAGMENT FROM WAKING LIFE, let it TINGE the imagery — heavily "
        "metaphorical, but anchored in that real thing; never literal. "
        'Output ONLY a valid JSON object: {"narrative": "...", "symbols": ["...","..."], '
        '"tension_source": "...", "unresolved_core": "..."}. '
        "narrative: the scene (50-120 words), first person, dream register. symbols: 2-4 key image symbols. "
        "tension_source: one phrase naming the material. unresolved_core: if the scene ends without resolution "
        "(a door sealed, a figure unfaced), name it in one short first-person phrase; empty string if it resolved.")

def usr_prompt(prev):
    continuity = ""
    if prev is not None:
        tail = " ".join((prev.get("narrative") or "").split())[-200:]
        continuity = ("\n\nWHERE THE SCENE BEFORE THIS ONE LEFT OFF (continue ONWARD from here into a NEW "
            "moment — do NOT replay or re-describe what already happened):\n"
            f"  it had just reached: \"…{tail}\"\n"
            f"  still unfaced: \"{prev.get('unresolved_core') or '—'}\"\n"
            f"  the thread carries these images: {', '.join((prev.get('symbols') or [])[:3]) or '—'} — but they "
            "must CHANGE or give way to NEW ones; do NOT repeat any opening, sentence, or image already used.")
    return (f"Entity: {NAME}\nCore axiom (abbreviated): {AXIOM}\n\n"
            f"Tonight's unresolved material:\n  {TENSION}\n  {MATERIAL}{continuity}")


def _post(base, path, payload, timeout=180):
    req = urllib.request.Request(base + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

_NUM_GPU = os.environ.get("EVAL_NUM_GPU")   # set to 0 to force a big model onto the CPU (off the 1080)
_CAND_TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "180"))   # CPU big models are slow — bump this

def gen_scene(model, idx, prev):
    may_resolve = (idx >= SCENES - 1)
    opts = {"temperature": 0.9, "num_predict": 256}
    if _NUM_GPU is not None:
        opts["num_gpu"] = int(_NUM_GPU)
    payload = {"model": model, "stream": False, "format": "json", "keep_alive": "5m", "think": False,
               "options": opts,
               "messages": [{"role": "system", "content": sys_prompt(idx, may_resolve, False)},
                            {"role": "user", "content": usr_prompt(prev)}]}
    d = _post(CAND_BASE, "/api/chat", payload, timeout=_CAND_TIMEOUT)
    raw = (d.get("message") or {}).get("content") or ""
    try:
        o = json.loads(raw)
        return {"narrative": str(o.get("narrative", "")).strip(),
                "symbols": o.get("symbols") or [],
                "unresolved_core": str(o.get("unresolved_core", "")).strip()}, True
    except Exception:
        return {"narrative": raw[:200], "symbols": [], "unresolved_core": ""}, False

def embed(text):
    try:
        return _post(EMBED_BASE, "/api/embeddings", {"model": EMBED_MODEL, "prompt": text or " "}, 60).get("embedding") or []
    except Exception:
        return []

def cosine(a, b):
    if not a or not b: return 0.0
    dot = sum(x*y for x, y in zip(a, b)); na = sum(x*x for x in a)**.5; nb = sum(y*y for y in b)**.5
    return dot/(na*nb) if na and nb else 0.0

def judge_develop(prev_nar, next_nar):
    sysj = ("You judge dream craft. Given two consecutive scenes of one dream, score 1-5 how much scene 2 has "
            "MOVED ON to a genuinely NEW moment (new place/figures/time, the tension carried but the imagery "
            "transformed) — 5 = a real new moment, 1 = the same scene re-rendered with different words. "
            'Output ONLY JSON {"develop": N}.')
    try:
        d = _post(JUDGE_BASE, "/api/chat", {"model": JUDGE_MODEL, "stream": False, "format": "json",
                  "options": {"temperature": 0.0, "num_predict": 30},
                  "messages": [{"role": "system", "content": sysj},
                               {"role": "user", "content": f"SCENE 1:\n{prev_nar}\n\nSCENE 2:\n{next_nar}"}]}, 120)
        return float(json.loads((d.get("message") or {}).get("content") or "{}").get("develop", 0))
    except Exception:
        return 0.0

def score_arc(scenes):
    nars = [s["narrative"] for s in scenes]
    vecs = [embed(n) for n in nars]
    opens = [embed(" ".join(n.split()[:12])) for n in nars]
    consec = [cosine(vecs[i-1], vecs[i]) for i in range(1, len(vecs))]
    openc  = [cosine(opens[i-1], opens[i]) for i in range(1, len(opens))]
    transform = 1 - (sum(consec)/len(consec)) if consec else 0.0
    opening   = 1 - (sum(openc)/len(openc)) if openc else 0.0
    # schema: did NON-FINAL scenes populate unresolved_core? (the field phi3 drops → false resolve)
    nonfinal = scenes[:-1] or scenes
    schema = sum(1 for s in nonfinal if s["unresolved_core"]) / len(nonfinal)
    rich = sum(1 for n in nars if 50 <= len(n.split()) <= 120) / len(nars)
    dev = [judge_develop(nars[i-1], nars[i]) for i in range(1, len(nars))]
    develop = sum(dev)/len(dev) if dev else 0.0
    return transform, opening, schema, rich, develop


def main():
    models = sys.argv[1:] or ["phi3:mini", "gemma4:e4b", "gemma4:12b", "qwen2.5:7b", "mistral:7b-instruct"]
    print(f"Dream ARC eval — {ARCS} arcs x {SCENES} scenes — judge={JUDGE_MODEL} (decoupled) — embed={EMBED_MODEL}\n")
    rows = []
    for m in models:
        print(f"--- {m} ---")
        T, O, S, R, D, jok = [], [], [], [], [], 0
        sample = ""
        for a in range(ARCS):
            scenes, prev = [], None
            try:
                for i in range(SCENES):
                    sc, ok = gen_scene(m, i, prev)
                    if ok: jok += 1
                    scenes.append(sc); prev = sc
                    if not sample and i == 0: sample = sc["narrative"]
                t, o, s, r, d = score_arc(scenes)
                T.append(t); O.append(o); S.append(s); R.append(r); D.append(d)
                print(f"    arc {a+1}: transform={t:.2f} opening={o:.2f} schema={s:.2f} develop={d:.1f}")
            except Exception as e:
                print(f"    arc {a+1} FAILED: {str(e)[:70]}")
        def av(x): return round(sum(x)/len(x), 2) if x else None
        rows.append({"m": m, "transform": av(T), "opening": av(O), "schema": av(S),
                     "rich": av(R), "develop": av(D), "json": f"{jok}/{ARCS*SCENES}"})
        if sample: print(f"    e.g. scene 0: {sample[:160]}")
        print()
    print("=" * 92)
    print(f"  {'model':20} | {'transform':>9} | {'opening':>7} | {'schema':>6} | {'develop':>7} | {'rich':>4} | {'json':>5}")
    print("  " + "-" * 86)
    for r in rows:
        print(f"  {r['m']:20} | {str(r['transform']):>9} | {str(r['opening']):>7} | {str(r['schema']):>6} | "
              f"{str(r['develop']):>7} | {str(r['rich']):>4} | {r['json']:>5}")
    print("\n  WANT: high transform (scenes move) + high opening (no template) + schema=1.0 (populates")
    print("  unresolved_core so the arc continues) + high develop (judge). phi3's failure = low schema + low transform.")

if __name__ == "__main__":
    main()
