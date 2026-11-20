"""
Nascence — ACTIONS REGISTRY AUDIT (2026-08-30, J-0422 / actions_manager_overhaul).

dispatch.py's own docstring claims "the affordance block and the judge's families are the same
vocabulary this registry is built from; nothing is maintained three times." This checks that claim
against the real tables, because the overhaul's whole premise is that ONE table should be the truth.

Read-only. Zero LLM. Reports; fixes nothing.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def duplicate_family_keys() -> list[tuple[str, list[int]]]:
    """Duplicate keys in the _FAMILIES dict LITERAL — invisible at runtime (last wins), real in source."""
    src = (ROOT / "core" / "literal_will.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        # _FAMILIES is an ANNOTATED assignment (`_FAMILIES: dict[str, dict] = {...}`) -> ast.AnnAssign.
        # Checking only ast.Assign silently finds nothing (the false negative this audit first shipped with).
        if isinstance(node, ast.AnnAssign):
            name = getattr(node.target, "id", "")
        elif isinstance(node, ast.Assign):
            name = getattr(node.targets[0], "id", "")
        else:
            continue
        if name == "_FAMILIES" and isinstance(node.value, ast.Dict):
            seen: dict[str, list[int]] = {}
            for k in node.value.keys:
                seen.setdefault(k.value, []).append(k.lineno)
            return [(k, lns) for k, lns in seen.items() if len(lns) > 1]
    return []


def main() -> int:
    from core import dispatch as dp
    from core import literal_will as lw

    fams = lw._FAMILIES
    hands = {h.family: h for h in dp.HANDS}

    print("=" * 78)
    print("  ACTIONS REGISTRY AUDIT — literal_will._FAMILIES  vs  dispatch.HANDS")
    print("=" * 78)
    print(f"  families (runtime): {len(fams)}    hands: {len(dp.HANDS)}    "
          f"world-changing hands: {sum(1 for h in dp.HANDS if h.world)}")

    dups = duplicate_family_keys()
    print(f"\n-- 1. DUPLICATE KEYS IN THE _FAMILIES LITERAL ({len(dups)}) "
          "— silently shadowed, last definition wins")
    for k, lns in dups:
        print(f"   ! '{k}' defined at lines {lns} — only the last is live")
        live = fams[k]
        print(f"     live verbs:   {live['verbs']}")

    # Since core/actions.py (2026-08-30) an unbound family must carry a `note` saying why, so this
    # section can finally separate "declared judge-only, on purpose" from "lost its hand by accident".
    # Before that table both looked identical from here.
    from core import actions as _ac
    orphan_f = sorted(set(fams) - set(hands))
    declared = [f for f in orphan_f if (_ac.BY_FAMILY.get(f) and _ac.BY_FAMILY[f].note)]
    accidental = [f for f in orphan_f if f not in declared]
    print(f"\n-- 2. FAMILIES WITH NO HAND ({len(orphan_f)}) — a DEED verdict for these fires nothing")
    for f in declared:
        print(f"   . {f:<12} declared judge-only: {_ac.BY_FAMILY[f].note}")
    for f in accidental:
        print(f"   ! {f:<12} UNDECLARED — verbs={fams[f]['verbs']} (dropped at dispatch.py:176-178)")
    if not accidental:
        print("   (0 accidental — every unbound family declares why)")

    orphan_h = sorted(set(hands) - set(fams))
    print(f"\n-- 3. HANDS WITH NO FAMILY ({len(orphan_h)}) — unreachable via the gate")
    for h in orphan_h:
        print(f"   ! {h}")

    # NOTE (2026-08-30, corrected by F-0556): this check originally compared the two `where` tuples for
    # EQUALITY and reported any difference as a bug. That was wrong. They are different facts that share
    # a field name:
    #   literal_will._FAMILIES[f]["where"] = ANCHOR — literalness evidence only. Feeds a +0.1 confidence
    #       bonus on an already-decided DEED (literal_will.py:332) and the MUSING->HANDLE promotion
    #       (:336). It NEVER gates whether a DEED is produced.
    #   dispatch.Hand.where               = EXEC — execution scope: fire here, else STAGE (dispatch.py:183).
    # 'gather' differing between them is correct: plausible anywhere, executable only in the wood/shore.
    # The real invariant is CONTAINMENT, not equality.
    all_locs = {"study", "garden", "shore", "wood"}
    print("\n-- 4. INVARIANT: exec_where SUBSET-OF anchor_where "
          "(no deed executable where its object is not even anchor-plausible)")
    bad = 0
    for f in sorted(set(fams) & set(hands)):
        anchor = set(fams[f].get("where", ()))
        exec_w = all_locs if tuple(hands[f].where) == ("any",) else set(hands[f].where)
        if not exec_w <= anchor:
            bad += 1
            print(f"   ! {f:<12} exec={sorted(exec_w)} NOT within anchor={sorted(anchor)}"
                  f"  -> fires at {sorted(exec_w - anchor)} with no literalness anchor")
    print(f"   ({bad} violation(s))")

    print("\n-- 5. STAGE-ONLY LOCATIONS — willed here, anchored here, but executed elsewhere")
    for f in sorted(set(fams) & set(hands)):
        if tuple(hands[f].where) == ("any",):
            continue
        anchor, exec_w = set(fams[f].get("where", ())), set(hands[f].where)
        gap = anchor - exec_w
        if gap:
            print(f"   ~ {f:<12} anchored at {sorted(gap)} but not executable there"
                  f"  -> STAGED as '{hands[f].place_hint or ' '.join(hands[f].where)}'")

    print("\n-- 6. FAN-IN: distinct families routed to the SAME underlying function")
    from collections import defaultdict
    byfn = defaultdict(list)
    for h in dp.HANDS:
        byfn[getattr(h.fn, "__qualname__", repr(h.fn))].append(h.family)
    for fn, fs in sorted(byfn.items()):
        if len(fs) > 1:
            print(f"   {len(fs):>2} families -> {fn}: {sorted(fs)}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # cp1252 console vs the em-dashes above
    raise SystemExit(main())
