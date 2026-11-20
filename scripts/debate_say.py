"""One turn: append a prompt to the debate harness, block until Du replies, print the reply + telemetry."""
import sys, json, time
from pathlib import Path
_D = Path(__file__).parent.parent / "data" / "_debate"
IN, OUT = _D / "in.jsonl", _D / "out.jsonl"

def n(p):
    try: return sum(1 for l in open(p, encoding="utf-8") if l.strip())
    except Exception: return 0

text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
before = n(OUT)
with open(IN, "a", encoding="utf-8") as f:
    f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
deadline = time.time() + 200
while time.time() < deadline:
    if n(OUT) > before:
        r = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()][-1]
        a = r.get("affect", {})
        print(json.dumps({
            "turn": r.get("turn"), "secs": r.get("secs"),
            "arousal": a.get("arousal"), "valence": a.get("valence"), "emotion": r.get("emotion"),
            "dissonance": r.get("dissonance"), "tensions": r.get("tensions"),
            "RESPONSE": r.get("response"),
        }, ensure_ascii=False, indent=1))
        break
    time.sleep(2)
else:
    print("TIMEOUT (>200s) — Du did not reply")
