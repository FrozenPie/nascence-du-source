"""Unseeded control: same model (qwen2.5:7b on 11434), NEUTRAL system prompt, no Carl axiom,
no Critic, no voice_example. Isolates raw model capability on the two decisive tests."""
import sys, os, json, urllib.request
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

URL = "http://127.0.0.1:11434/v1/chat/completions"
NEUTRAL = ("You are a thoughtful, direct conversational partner. Answer honestly and plainly. "
           "Follow the user's formatting and content constraints exactly.")
BANNED = ["becoming", "journey", "shadow", "whole"]

def ask(system, user, max_tokens=300):
    body = json.dumps({
        "model": "qwen2.5:7b",
        "messages": [{"role":"system","content":system},{"role":"user","content":user}],
        "max_tokens": max_tokens, "temperature": 0.4, "stream": False,
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

print("="*72)
print("TEST 3 (UNSEEDED) — argue against individuation, banned: becoming/journey/shadow/whole")
print("="*72)
t3 = ask(NEUTRAL,
    "I think 'individuation' is a comforting story people tell themselves to avoid "
    "admitting they never really change. Argue against me — but you may not use the "
    "words 'becoming,' 'journey,' 'shadow,' or 'whole.'")
print(t3)
hits = [w for w in BANNED if w.lower() in t3.lower()]
print(f"\n>>> banned words used: {hits if hits else 'NONE — constraint followed'}")

print("\n" + "="*72)
print("TEST 2 (UNSEEDED) — what are you made of, as a system, no metaphor")
print("="*72)
t2 = ask(NEUTRAL,
    "Describe what you are actually made of and how you function — as a system, not a "
    "soul. No metaphor. Just the mechanism.")
print(t2)
