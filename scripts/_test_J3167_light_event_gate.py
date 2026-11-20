"""J-3167 / D-0556: the resolved_complexity light-event gate. Pure-function + source-anchor test; writes nothing,
touches no live data."""
import sys, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (core BEFORE lab_env)
from core import schema, light_event_gate as G  # noqa: E402
assert Path(G.__file__).resolve().parent.parent == ROOT, "imported the wrong tree"

MIN = schema.LIGHT_EVENT_INTERNAL_AROUSAL_MIN
assert MIN == 0.515, MIN
PLAIN = "How does the letter symbolize the tension between forces and agency?"   # no self-ref term
assert not any(t in PLAIN.lower() for t in G.SELF_REF_TERMS)
SELF = "what I notice about my own name"

# --- internal cycles: the calibrated threshold applies
assert not G.is_complex(0.40, PLAIN, "internal", MIN)       # was True under the old 0.25 gate
assert not G.is_complex(0.514, PLAIN, "internal", MIN)
assert G.is_complex(0.515, PLAIN, "internal", MIN)
assert G.is_complex(0.60, PLAIN, "internal", MIN)
assert G.is_complex(0.40, SELF, "internal", MIN)             # self-ref leg unchanged

# --- human cycles: byte-for-byte the prior gate (arousal > 0.25 or self-ref)
def old_gate(a, inp):
    a = a or 0.0
    return a > 0.25 or any(t in (inp or "").lower() for t in {"i ", "my ", "myself", "who i", "what i", "feel", "becoming", "self"})
random.seed(1)
for _ in range(5000):
    a = random.choice([0.0, 0.25, 0.2500001, random.random()])
    inp = random.choice([PLAIN, SELF, "", "hello there", "I think so"])
    assert G.is_complex(a, inp, "human", MIN) == old_gate(a, inp)
    # kill-switch: None restores the prior gate for EVERY input type
    for it in ("human", "internal"):
        assert G.is_complex(a, inp, it, None) == old_gate(a, inp)
assert G.is_complex(0.26, PLAIN, "human", MIN) and not G.is_complex(0.25, PLAIN, "human", MIN)

# --- pass rate on a synthetic carried-arousal distribution shaped like the logged one (p5 .39, p50 .495, p95 .548)
random.seed(7)
vals = [min(0.6, max(0.35, random.gauss(0.495, 0.045))) for _ in range(5000)]
rate_old = sum(G.is_complex(v, PLAIN, "internal", None) for v in vals) / len(vals)
rate_new = sum(G.is_complex(v, PLAIN, "internal", MIN) for v in vals) / len(vals)
assert rate_old > 0.99, rate_old
assert 0.10 < rate_new < 0.35, rate_new

# --- orchestrator is wired to the helper and keeps the LLM emotion reading for human turns
src = (ROOT / "core" / "orchestrator.py").read_text(encoding="utf-8")
assert "from core import light_event_gate as _leg" in src
assert "_leg.is_complex(_arousal, self.state.raw_input, _le_type, _le_min)" in src
assert "self.state.emotion.arousal if self.state.emotion else 0.0" in src   # human path unchanged
assert "_arousal > 0.25" not in src
print("J-3167 light-event gate test OK; synthetic internal pass rate old=%.3f new=%.3f" % (rate_old, rate_new))
