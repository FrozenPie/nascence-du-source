"""J-3187 (D-0574): the idle seed's "The last thing discussed" line is omitted while conversation_history is only the
restored previous-session exchange and no live exchange has happened this run (core.wandering._exchanged_this_run).

  [1] source: the flag exists (True), the gate reads core.wandering._exchanged_this_run, the line text is unchanged.
  [2] behaviour: the real gate block is cut out of nodes/inner_monologue_node.py and exec'd against stubs:
        restored + no live exchange   -> no line
        live exchange this run        -> the line, byte-identical to the old format
        flag off                      -> the line (old behaviour), even with no live exchange
        signal unreadable             -> the line (fail-open)
        empty history / train-hold    -> no line (unchanged)
  [3] core.wandering.on_human_exchange() flips the signal, so the line returns after Travis speaks.
Pure source + temp state; touches no live data.   python scripts/_test_J3187_restored_last_thing.py
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (BEFORE anything else)

assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")

# [1]
assert "IDLE_SEED_DROP_RESTORED_LAST_THING = True" in src
assert "_w_lt._exchanged_this_run" in src
# J-4052: re-pinned -- the 120-char slice became _seed_cut(..., 120) (seed text hygiene) after J-3187.
assert 'seed_parts.append(f"The last thing discussed -- them: \\"{_seed_cut(last.get(\'human\',\'\'), 120)}\\" "' in src
print("[1] ok")

# [2] cut the real gate block out
a = src.index("        _drop_restored_last = False")
b = src.index("                              f\"you: \\\"{_seed_cut(last.get('entity',''), 120)}\\\"\")", a)   # J-4052 re-pin
b = src.index("\n", b) + 1
block = textwrap.dedent(src[a:b])


def run(history, exchanged, flag=True, hold_quiet=False, broken=False):
    import types
    import core.wandering as w
    w._exchanged_this_run = exchanged
    seed_parts: list = []
    st = types.SimpleNamespace(conversation_history=history)
    g = {"IDLE_SEED_DROP_RESTORED_LAST_THING": flag, "state": st, "seed_parts": seed_parts, "_hold_quiet": hold_quiet,
         "_seed_cut": lambda t, n, terminate=False: t[:n]}   # J-4052: stand-in (inputs here are <= 120 chars)
    if broken:
        # make `from core import wandering` yield an object without the attribute
        import sys as _s
        real = _s.modules["core.wandering"]
        fake = types.ModuleType("core.wandering")
        _s.modules["core.wandering"] = fake
        import core as _c
        old_attr = getattr(_c, "wandering", None)
        _c.wandering = fake
        try:
            exec(block, g)
        finally:
            _s.modules["core.wandering"] = real
            _c.wandering = old_attr if old_attr is not None else real
    else:
        exec(block, g)
    return seed_parts


H = [{"human": "h" * 150, "entity": "e" * 150}]
want = [f'The last thing discussed -- them: "{"h" * 120}" you: "{"e" * 120}"']
assert run(H, exchanged=False) == []
assert run(H, exchanged=True) == want
assert run(H, exchanged=False, flag=False) == want
assert run(H, exchanged=False, broken=True) == want
assert run([], exchanged=True) == []
assert run(H, exchanged=True, hold_quiet=True) == []
print("[2] ok")

# [3]
import core.wandering as w  # noqa: E402
w._exchanged_this_run = False
assert run(H, exchanged=w._exchanged_this_run) == []
w.on_human_exchange()
assert w._exchanged_this_run is True
assert run(H, exchanged=w._exchanged_this_run) == want
w._exchanged_this_run = False
print("[3] ok")
print("ALL OK")
