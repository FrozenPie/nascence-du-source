"""J-3869: regime_shadow_verdict states the right verdict; hermetic (temp state files only, no live data)."""
import json, sys, tempfile
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from core import arousal as ar
assert Path(ar.__file__).resolve().is_relative_to(root)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import regime_shadow_verdict as v

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    ar._REGIME_STATE = d / "missing"
    assert v.verdict(ar.regime_shadow_status()).startswith("NO-DATA")
    def put(**kw):
        p = d / "st"; p.write_text(json.dumps(kw), encoding="utf-8"); ar._REGIME_STATE = p
        return v.verdict(ar.regime_shadow_status())
    assert put(resolved_count=3, resolved_cycles_sum=9, resolved_seconds_sum=90.0, longest_streak_cycles=5, longest_streak_seconds=40.0).startswith("INSUFFICIENT")
    assert put(resolved_count=36, resolved_cycles_sum=360, resolved_seconds_sum=36*60.0, longest_streak_cycles=30, longest_streak_seconds=900.0).startswith("READABLE-OK")
    assert put(resolved_count=36, resolved_cycles_sum=360, resolved_seconds_sum=36*3600.0, longest_streak_cycles=90, longest_streak_seconds=9000.0).startswith("STALE-RISK")
    assert put(resolved_count=36, resolved_cycles_sum=360, resolved_seconds_sum=36*60.0, longest_streak_cycles=900, longest_streak_seconds=30000.0).startswith("STALE-RISK")
print("OK")
