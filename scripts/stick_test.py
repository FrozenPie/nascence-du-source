"""
Nascence — THE STICK TEST (CLI): bundle-richness census. Thin wrapper over core.stick_test.

Run any time for a printed table; it also appends one row to data/stick_test_log.jsonl (the same
longitudinal record the sleep hook and the HUD chart use). READ-ONLY, no LLM. See core/stick_test.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import stick_test as st   # noqa: E402


if __name__ == "__main__":
    res = st.census()
    if not res["rows"]:
        print("stick test: no data (DB unreadable?)")
        sys.exit(0)
    print(f"{'OBJECT':44} {'mentions':>8}  spokes")
    for r in sorted(res["rows"], key=lambda x: -x["real_spokes"]):
        print(f"{r['object'][:44]:44} {r['mentions']:>8}  {'+'.join(r['spokes']) or '(none)'}")
    s = res["summary"]
    print(f"\nSUMMARY: {s['objects']} objects · median real spokes = {s['median_real_spokes']} · "
          f"mean = {s['mean_real_spokes']} · max = {s['max_real_spokes']}")
    print(f"  1-spoke (blind-man concepts): {s['at_1_spoke']} · 2-spoke: {s['at_2_spokes']} · 3+: {s['at_3plus']}")
    print(f"  metric_version={s.get('metric_version')} — J-0006 (2026-08-24): real_spokes now credits "
          "within-channel accumulation (text mention-count level + sound co-occurrence-context level), "
          "not just channel presence. J-0154 (2026-08-24): book's state channel now also credits "
          "accumulation (co-occurrence-context level). J-0201 (2026-08-24): the kept cat's state channel "
          "now also credits accumulation (distinct (mood,activity,location) triple count, data-grounded "
          "quartile thresholds from its own longitudinal series); fire/herbs/keepsakes/distant-cat/audio "
          "investigated and confirmed to have no comparably real source, left as booleans. Not comparable "
          "point-for-point to earlier metric_version rows in the log; see core/stick_test.py's docstring.")
    if st.snapshot(res) is not None:
        print(f"[census row appended to {st._LOG.name} — the longitudinal record]")
    else:
        print("[log append failed]")
