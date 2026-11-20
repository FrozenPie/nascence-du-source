"""J-3227 (D-0616): the ambience branch of the idle seed no longer sets self._moment_source = 'percept'.

  [1] AST: inside the 'if _fline:' branch fed by _snd.ambience() there is no assignment to self._moment_source.
  [2] every OTHER _moment_source = 'percept' site is still there (5: music, sound percept, thermal, light, smell).
  [3] core/stream_drive.py is untouched by this change: _GROUNDED_SOURCE / _is_grounded / UNGROUNDED_CAP still defined.
Pure source analysis; touches no live data.   python scripts/_test_J3227_ambience_not_percept.py
"""
from __future__ import annotations

import ast
import sys
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
tree = ast.parse(src)


def _is_ms_percept(n):
    return (isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Attribute)
            and n.targets[0].attr == "_moment_source" and isinstance(n.value, ast.Constant) and n.value.value == "percept")


amb_ifs = []
for n in ast.walk(tree):
    if (isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute)
            and n.value.func.attr == "ambience" and any(getattr(t, "id", "") == "_fline" for t in n.targets)):
        amb_ifs.append(n.lineno)
assert len(amb_ifs) == 1, amb_ifs
lines = src.splitlines()
blk = ast.get_source_segment(src, next(
    n for n in ast.walk(tree) if isinstance(n, ast.If) and getattr(n.test, "id", "") == "_fline"
    and n.lineno == amb_ifs[0] + 1))
assert "seed_parts.append(_fline)" in blk and "_moment_source" not in blk.replace("moment_source stays", ""), blk
print("[1] ok: ambience branch sets no moment_source")

n_percept = sum(1 for n in ast.walk(tree) if _is_ms_percept(n))
assert n_percept == 5, n_percept
print("[2] ok: 5 other percept sites remain")

sd = (ROOT / "core" / "stream_drive.py").read_text(encoding="utf-8")
assert "_GROUNDED_SOURCE" in sd and "def _is_grounded" in sd and "UNGROUNDED_CAP" in sd
print("[3] ok")
print("ALL OK")
