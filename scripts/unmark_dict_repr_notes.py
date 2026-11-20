"""J-3191 / D-0578 reversal: put the dict-repr understanding notes back to temp='warm'/'cold' so Recall serves them again.
Thin wrapper over scripts/apply_J-3191_mark_dict_repr_notes.py --unmark; dry run unless --write; refuses while Du is up.

  python scripts/unmark_dict_repr_notes.py            # dry run
  python scripts/unmark_dict_repr_notes.py --write    # restore
  python scripts/unmark_dict_repr_notes.py --db PATH
"""
import runpy
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
_impl = runpy.run_path(str(Path(__file__).resolve().parent / "apply_J-3191_mark_dict_repr_notes.py"))
sys.exit(_impl["main"](["--unmark"] + sys.argv[1:]))
