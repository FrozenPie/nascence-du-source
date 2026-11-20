"""J-4353 / F-5105: close the live data/ leaks left by the human-cycle lab recipe.

activate_profile() (core/profile.py) rebases only the modules named in its own tuple. J-2676's throwaway
human cycles (scripts/lab_J-2676_capture.py, scripts/_first_thought.py) reached modules that are NOT in it, so
their fixed data/ paths were written in the LIVE tree: ambiguity_window_shadow, companion_state /
companion_actions_log, left_take_outcomes, intentions.json, social_moves_state, symbol_window_state/shadow,
voice_fidelity_shadow. rebase_human_cycle_paths(prof) re-points every module-level Path constant of those
modules that sits at the live data/ tree into the profile dir, the same rule activate_profile() applies.
Recipe-local on purpose (no core/ edit); the durable fix is to name these modules in core/profile.py's tuple.
"""
from __future__ import annotations
import importlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE_DATA = ROOT / "data"

LEAKING_MODULES = (
    "core.ambiguity_window", "core.companion", "core.intentions", "core.left_lane",
    "core.social_moves", "core.symbol_window_shadow", "core.voice_fidelity", "core.goals",
)
_ORIG: dict = {}


def _under_live(p: Path):
    """Relative path if p is inside live data/ and not already in profiles/ or _lab/, else None."""
    for root in (LIVE_DATA, Path(r"C:\Nascence") / "data"):
        for cand in (p, p.resolve() if p.is_absolute() else p):
            try:
                rel = cand.relative_to(root)
            except ValueError:
                try:
                    rel = cand.relative_to(root.resolve())
                except ValueError:
                    continue
            if rel.parts and rel.parts[0] in ("profiles", "_lab"):
                return None
            return rel
    return None


def rebase_human_cycle_paths(prof: Path) -> list[str]:
    """Rebase LEAKING_MODULES' data/ Path constants into `prof`. Call right after activate_profile()."""
    done = []
    for name in LEAKING_MODULES:
        m = importlib.import_module(name)
        for attr, v in list(vars(m).items()):
            if not isinstance(v, Path):
                continue
            key = (name, attr)
            orig = _ORIG.get(key)
            if orig is None:
                if _under_live(v) is None:
                    continue
                _ORIG[key] = orig = v
            setattr(m, attr, Path(prof) / _under_live(orig))
            done.append(f"{name}.{attr}")
    return done


def audit_live_paths(prefixes=("core.", "nodes.")) -> list[str]:
    """Every loaded core/nodes module Path constant still pointing at live data/ (top level or below)."""
    bad = []
    for name, m in list(sys.modules.items()):
        if not name.startswith(prefixes) or m is None:
            continue
        for attr, v in list(vars(m).items()):
            if isinstance(v, Path) and _under_live(v) is not None:
                bad.append(f"{name}.{attr}={_under_live(v)}")
    return bad
