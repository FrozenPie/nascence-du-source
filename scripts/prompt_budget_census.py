"""Census of how the inner-monologue prompt is currently shaped — read-only, writes nothing.

The P0 measurement for `core/prompt_budget.py`. Answers, from the source itself: how many parts can
enter the prompt, how many carry a hardcoded truncation, what those constants are, and what the
theoretical maximum prompt is if every part fired at full allowance. That last number, set against the
lane's real window, is the whole question — measured 2026-08-20, the hot lane's cap is 73,728 chars and
real prompts run ~11,000.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # house rule: print() dies on non-ASCII without this

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "nodes" / "inner_monologue_node.py"
TRUNC = re.compile(r"\[:(\d+)\]")


def spans(src: str, needle: str) -> list[str]:
    """Balanced-paren span of every `needle(...)` call — a regex cannot match nested parens."""
    out = []
    for m in re.finditer(re.escape(needle) + r"\(", src):
        i, depth = m.end() - 1, 0
        for j in range(i, len(src)):
            if src[j] == "(":
                depth += 1
            elif src[j] == ")":
                depth -= 1
                if depth == 0:
                    out.append(src[i:j + 1])
                    break
    return out


def main() -> int:
    src = SRC.read_text(encoding="utf-8")
    sp = spans(src, "seed_parts.append")
    with_trunc = [s for s in sp if TRUNC.search(s)]
    caps = [int(x) for s in sp for x in TRUNC.findall(s)]

    print(f"parts that can enter the prompt      : {len(sp)}")
    print(f"  ...carrying a hardcoded truncation : {len(with_trunc)}")
    print(f"  ...with NO truncation (unbounded)  : {len(sp) - len(with_trunc)}")
    print(f"truncation constants in prompt content: {len(caps)} uses, {len(set(caps))} distinct")
    print(f"  values: {sorted(set(caps))}")
    print()
    print(f"theoretical max if every capped part fired at full allowance: {sum(caps):,} chars")
    print("  (parts with NO cap are unbounded and not counted — the real ceiling is higher)")
    print()
    print("For comparison, measured the same day from data/training/*.jsonl (real sent text):")
    print("  reflection median 7,417 chars · max 12,381   |   hot-lane cap 73,728 chars")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
