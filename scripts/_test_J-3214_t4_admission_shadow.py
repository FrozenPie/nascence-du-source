"""Proof for J-3214 (D-0603): source checks that the T4 raw-crossings shadow grade is additive and gates nothing.
No network, no live data written.   python scripts/_test_J-3214_t4_admission_shadow.py   # exit 0 = ALL OK"""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "nodes" / "subconscious_node.py").read_text(encoding="utf-8")
fails = []
def chk(name, cond):
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond: fails.append(name)
chk("log constant points at data/t4_admission_shadow.jsonl", '_DATA_DIR / "t4_admission_shadow.jsonl"' in src)
chk("chain return carries raw crossings capped at 200", '"crossings": [str(c or "").replace(chr(10), " ")[:200]' in src)
blk = src[src.index("J-3214 / D-0603 SHADOW paired grade"):src.index("PROBATIONARY COMMIT LOOP")]
chk("second grade uses the traced judge on the raw list", "grade_self_revision_traced(old_self_concept, new_self_concept, _rawlist)" in blk)
chk("block never assigns _emj (gate reads only the live verdict)", not re.search(r"\b_emj\s*=", blk))
chk("block is wrapped fail-open", "except Exception as _rawex" in blk)
chk("both verdicts logged", '"current_warranted"' in blk and '"raw_warranted"' in blk)
gate = src[src.index("PROBATIONARY COMMIT LOOP"):]
chk("gate still reads only _emj", "_judge = (_emj or {}).get" in gate and "_rj" not in gate[:6000])
print("ALL OK" if not fails else "FAILED"); sys.exit(1 if fails else 0)
