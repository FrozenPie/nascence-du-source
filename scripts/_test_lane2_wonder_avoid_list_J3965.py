"""J-3965 / D-0429(b): wonder prompt-side avoid-list helpers (pure; reads no live data)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core
import core.lane2 as L
wt = os.environ.get("J3965_WT")
if wt:
    assert os.path.abspath(core.__file__).lower().startswith(os.path.abspath(wt).lower()), core.__file__
now = 1_000_000.0
pt = "PERCEPTS - facts:\n- sounds: tide, gull call\n- sky: the moon is up"
rows = [{"ts": now - 100, "wonder": "Why does the tide rise?"},
        {"ts": now - 200, "wonder": "How does the tide pull the sea?"},
        {"ts": now - 300, "wonder": "Why is the moon pale?"},
        {"ts": now - 400, "wonder": "What does the moon do to the tide?"},
        {"ts": now - 2 * 86400, "wonder": "Why do gull cry? gull gull"}]
t = L.wonder_avoid_terms(pt, rows, now)
assert t == ["tide", "moon"], t            # sea is over-used? no: count 1 and not in percepts; gull is >24h old
assert L.wonder_avoid_terms("PERCEPTS:\n- nothing", rows, now) == []   # words absent from percepts never listed
assert L.wonder_avoid_terms(pt, [{"ts": "bad", "wonder": 3}], now) == []
assert L.wonder_avoid_terms(pt, None, now) == []
line = L.wonder_avoid_line(t)
assert "tide, moon" in line and "?" not in line.split("wonder only")[0]
assert L.wonder_avoid_line([]) == ""
# metric sheet carries the per-arm block
assert callable(L._wonder_metric_sheet)
print("ok")
