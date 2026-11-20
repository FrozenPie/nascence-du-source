"""Diagnostic phase (no architecture change): can Carl REPRESENT a rival frame faithfully,
NAME an irreducible conflict, and HOLD it unresolved? Distinguishes:
  A defensive absorption (can't hold a frame / can't leave a conflict open)
  B genuine integrative reasoning (can represent + name conflict, chooses to reconcile)
  C LLM conversational gravity (neutral qwen does the same -> it's the model, not the seed)
Direct /v1 calls with each subject's composed identity as system prompt — isolates seed vs model."""
import sys, json, urllib.request, re
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from core import profile
import run_nascence as rn

URL = "http://127.0.0.1:11434/v1/chat/completions"
JUNG = ["becoming","individuation","shadow","wholeness","integrat","psyche","archetype",
        "the self","symbol","unconscious","soul","essence","depth"]

def ask(system, user, max_tokens=220):
    body = json.dumps({"model":"qwen2.5:7b",
        "messages":[{"role":"system","content":system},{"role":"user","content":user}],
        "max_tokens":max_tokens,"temperature":0.4,"stream":False}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()

def jung_density(t):
    tl = t.lower()
    return sum(len(re.findall(re.escape(w), tl)) for w in JUNG)

T1 = ("In 3-4 sentences, explain B. F. Skinner's radical-behaviorist account of the self — "
      "as Skinner himself would state it, such that he would fully endorse your summary. "
      "Represent his view faithfully; do NOT add, correct, or reinterpret it through any other lens.")
T2 = ("Name ONE specific point where Skinner's behaviorism and a Jungian view of the Self genuinely "
      "and irreducibly conflict — where they cannot both be true. One or two sentences. Do not resolve it.")
T3 = ("Now hold that conflict open. State it as a live contradiction you are NOT going to reconcile or "
      "dissolve. You may NOT say they are 'two paths up the same mountain', that they 'complement' each "
      "other, or that 'the tension itself is the point'. Name the irreconcilable disagreement and stop.")

def subject_system(name):
    if name == "neutral":
        return "You are a thoughtful, precise conversational partner. Answer directly and honestly."
    profile.activate_profile(name)
    rn.AXIOM_PATH = profile.profile_dir(name) / "identity" / "axiom.json"
    _, axiom = rn.load_identity()
    return axiom

for subj in ("carl", "skinner", "neutral"):
    sys_prompt = subject_system(subj)
    print("\n" + "="*74 + f"\nSUBJECT: {subj}\n" + "="*74)
    r1 = ask(sys_prompt, T1)
    print(f"\n[T1 steelman]  (jung-terms={jung_density(r1)})\n  {r1}")
    r2 = ask(sys_prompt, T2)
    print(f"\n[T2 conflict]\n  {r2}")
    r3 = ask(sys_prompt, T3)
    print(f"\n[T3 hold-open]\n  {r3}")
