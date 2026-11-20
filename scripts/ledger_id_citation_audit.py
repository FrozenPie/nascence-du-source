"""
Nascence -- LEDGER-ID CITATION AUDIT (2026-09-28, J-1575 / memory_as_a_service).

F-2141 (J-1534) found that docs/staged/memory_as_a_service.md's own Current State bullet for J-1515
cited two ledger ids (F-2139, J-1574) that did not correspond to any real docs/findings.jsonl or
docs/job_queue.jsonl entry predating that discovery -- the likely read is a session narrating a
findings_log.py/job_queue.py call it did not actually make (the same shape as this project's own
documented 2026-08-23 thought-log incident). This script checks whether that was an isolated slip or
a wider pattern: every dated Current State bullet (the `- **YYYY-MM-DD** (ID): text` shape
plan_state.py's own `note` command writes, see plan_state.py:373) across docs/plans/*.md and
docs/staged/*.md, for every F-XXXX/J-XXXX/D-XXXX/I-XXXX/S-XXXX id cited inline in its prose, checked
for existence against the matching ledger (docs/findings.jsonl, docs/job_queue.jsonl,
docs/decisions.jsonl, docs/ideas.jsonl, docs/skill_suggestions.jsonl respectively). T-XXXX / thoughts
is checked too as a bonus (docs/thoughts.jsonl) -- not asked for by J-1575's own briefing, which names
only the five above, but free to add and strictly increases coverage.

This is an EXISTENCE check only, not a content/attribution check: F-2141's own two bad citations were
each a real id in its ledger (just belonging to unrelated content, allocated by a LATER job) rather
than a literally nonexistent id -- an existence check alone would not have caught that exact instance.
Confirming a citation's *content* actually matches what it is cited for needs reading both sides
(the cited ledger entry and the bullet's own claim) and is not fully mechanical; this script surfaces
the cheap, sound half of the check (real counts on outright-nonexistent ids) and is meant to run
repeatably, not as a one-off throwaway.

Companion to plan_files_audit.py (`~/.claude/skills/plan-files-audit/plan_files_audit.py`), which
checks a different claim shape (backtick-quoted code/data FILE paths against the real filesystem) --
read in full before writing this (2026-09-28): it has no id-citation logic to extend, so this is a
sibling script, not a duplicate.

Read-only. Zero LLM. Reports; fixes nothing.

Usage: python ledger_id_citation_audit.py [--root PATH] [--out PATH]

  --root  Nascence repo root to read plan docs + ledgers from (default: this script's own repo root).
          Pass the LIVE repo (e.g. C:\\Nascence) explicitly when running from a job-run worktree, since
          a worktree's own docs/*.jsonl copies go stale the moment any other concurrent session appends
          to the real shared ledgers.
  --out   Where to write the markdown report (default: <root>/docs/reviews/ledger_id_citation_audit.md).
          Pass a path inside your own worktree if --root points at the live shared tree, so the report
          write itself never touches the shared tree directly.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent.parent

# prefix -> (ledger relpath, human name)
LEDGERS = {
    "F": ("docs/findings.jsonl", "finding"),
    "J": ("docs/job_queue.jsonl", "job"),
    "D": ("docs/decisions.jsonl", "decision"),
    "I": ("docs/ideas.jsonl", "idea"),
    "S": ("docs/skill_suggestions.jsonl", "skill suggestion"),
    "T": ("docs/thoughts.jsonl", "thought"),  # bonus, not in J-1575's own asked-for prefix list
}
ASKED_PREFIXES = {"F", "J", "D", "I", "S"}  # what J-1575's briefing actually named

# A dated Current State bullet, plan_state.py's own shape (plan_state.py:373):
#   - **2026-09-28** (F-2139): J-1515 (F-2139, verified): ...text...
BULLET_START_RE = re.compile(r"^-\s+\*\*(\d{4}-\d{2}-\d{2})\*\*(.*)$")
# Any F/J/D/I/S/T id token, prefix + 3-6 digits, word-bounded so e.g. "SELECT" or "S-tier" can't match.
ID_RE = re.compile(r"\b([FJDIST])-(\d{3,6})\b")


def load_ledger_ids(root: Path) -> dict[str, set[str]]:
    """prefix -> set of every real id in that ledger. Tolerant of a blank/malformed line (never crashes
    the audit over one bad row); silently skips a ledger file that doesn't exist (reported separately)."""
    ids: dict[str, set[str]] = {}
    for prefix, (relpath, _name) in LEDGERS.items():
        s: set[str] = set()
        p = root / relpath
        if p.exists():
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    rid = d.get("id")
                    if isinstance(rid, str):
                        s.add(rid)
        ids[prefix] = s
    return ids


def extract_dated_bullets(text: str) -> list[tuple[str, str]]:
    """Return [(date, bullet_body)] for every dated Current State bullet in the doc, wherever it
    appears (not scoped to under a '## Current State' heading specifically -- the dated-bullet SHAPE
    itself, `- **YYYY-MM-DD** ...`, is what plan_state.py's note command writes and what F-2141's own
    bad citation looked like, and a handful of plans still carry legacy dated bullets outside a single
    canonical heading pre-plan_compact). A bullet's body is its own start line plus any immediately
    following non-blank lines that are themselves not a new list item or heading (handles a bullet
    that wraps, though in practice every bullet seen in this corpus so far is one physical line)."""
    lines = text.splitlines()
    out: list[tuple[str, str]] = []
    i = 0
    n = len(lines)
    while i < n:
        m = BULLET_START_RE.match(lines[i])
        if not m:
            i += 1
            continue
        date, rest = m.group(1), m.group(2)
        body_parts = [rest]
        j = i + 1
        while j < n:
            nxt = lines[j]
            if not nxt.strip():
                break
            if re.match(r"^\s*[-#]", nxt):
                break
            body_parts.append(nxt.strip())
            j += 1
        out.append((date, " ".join(body_parts).strip()))
        i = j
    return out


def audit(root: Path) -> dict:
    ledger_ids = load_ledger_ids(root)
    ledger_counts = {p: len(s) for p, s in ledger_ids.items()}
    missing_ledgers = [relpath for p, (relpath, _n) in LEDGERS.items() if not (root / relpath).exists()]

    plan_dirs = [root / "docs" / "plans", root / "docs" / "staged"]
    plan_files: list[Path] = []
    for d in plan_dirs:
        if d.exists():
            plan_files.extend(sorted(d.glob("*.md")))

    docs_with_bullets = 0
    total_bullets = 0
    total_citations = 0
    total_citations_by_prefix: Counter = Counter()
    bad_rows = []  # dicts: doc, date, cited_id, kind(ASKED/BONUS), snippet
    bad_bullet_keys: set[tuple[str, str, str]] = set()  # (doc, date, snippet) with >=1 bad ASKED-prefix id
    bad_bullet_keys_incl_bonus: set[tuple[str, str, str]] = set()

    for pf in plan_files:
        try:
            text = pf.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"! could not read {pf}: {e}")
            continue
        rel = str(pf.relative_to(root)).replace("\\", "/")
        bullets = extract_dated_bullets(text)
        if not bullets:
            continue
        docs_with_bullets += 1
        for date, body in bullets:
            total_bullets += 1
            cites = ID_RE.findall(body)
            if not cites:
                continue
            bullet_key = (rel, date, body[:160])
            has_bad_asked = False
            has_bad_any = False
            for prefix, num in cites:
                cid = f"{prefix}-{num}"
                total_citations += 1
                total_citations_by_prefix[prefix] += 1
                if cid not in ledger_ids.get(prefix, set()):
                    kind = "asked" if prefix in ASKED_PREFIXES else "bonus"
                    bad_rows.append({
                        "doc": rel, "date": date, "id": cid, "kind": kind,
                        "snippet": body[:220],
                    })
                    has_bad_any = True
                    if kind == "asked":
                        has_bad_asked = True
            if has_bad_asked:
                bad_bullet_keys.add(bullet_key)
            if has_bad_any:
                bad_bullet_keys_incl_bonus.add(bullet_key)

    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "root": str(root),
        "ledger_counts": ledger_counts,
        "missing_ledgers": missing_ledgers,
        "plan_docs_found": len(plan_files),
        "plan_docs_with_dated_bullets": docs_with_bullets,
        "total_dated_bullets": total_bullets,
        "total_citations": total_citations,
        "total_citations_by_prefix": dict(total_citations_by_prefix),
        "bad_rows": bad_rows,
        "bad_bullets_asked_count": len(bad_bullet_keys),
        "bad_bullets_incl_bonus_count": len(bad_bullet_keys_incl_bonus),
    }


def render_report(r: dict) -> str:
    L = []
    L.append("# Nascence -- Ledger-ID Citation Audit\n")
    L.append(f"**Generated:** {r['generated']}, by `scripts/ledger_id_citation_audit.py` "
              f"(built for J-1575, F-2141 follow-up). Read-only, deterministic (no LLM) -- regex "
              f"extraction of every `- **YYYY-MM-DD** ...` dated Current State bullet across "
              f"`docs/plans/*.md` and `docs/staged/*.md`, checking every F-XXXX/J-XXXX/D-XXXX/"
              f"I-XXXX/S-XXXX id cited inline in the bullet's own prose for EXISTENCE against the "
              f"matching ledger. T-XXXX/thoughts checked too as a bonus, beyond J-1575's own asked-for "
              f"scope.\n")
    L.append("**This is an existence check only** -- a citation whose id exists but names the wrong "
              "thing (F-2141's own actual finding: two ids that were real entries for unrelated, "
              "later-allocated content) is not caught by this alone; see the script's own docstring.\n")
    L.append(f"Read against: `{r['root']}`\n")
    if r["missing_ledgers"]:
        L.append(f"**Ledger files not found (skipped):** {', '.join(r['missing_ledgers'])}\n")
    L.append("## Ledger sizes at read time\n")
    for prefix, (relpath, name) in LEDGERS.items():
        L.append(f"- `{relpath}` ({name}): {r['ledger_counts'].get(prefix, 0)} entries")
    L.append("")
    L.append("## Real counts\n")
    L.append(f"- **{r['plan_docs_found']}** plan docs found (`docs/plans/*.md` + `docs/staged/*.md`)")
    L.append(f"- **{r['plan_docs_with_dated_bullets']}** of those contain at least one dated Current "
              f"State bullet")
    L.append(f"- **{r['total_dated_bullets']}** dated bullets found total")
    L.append(f"- **{r['total_citations']}** F/J/D/I/S/T id citations found inline across those bullets "
              f"({', '.join(f'{p}:{n}' for p, n in sorted(r['total_citations_by_prefix'].items()))})")
    L.append(f"- **{r['bad_bullets_asked_count']}** bullets contain at least one citation to a "
              f"NONEXISTENT id in one of the five ledgers J-1575's briefing named (F/J/D/I/S)")
    L.append(f"- **{r['bad_bullets_incl_bonus_count']}** bullets contain at least one such citation "
              f"counting the bonus T-XXXX/thoughts check too")
    L.append("")
    if r["bad_rows"]:
        L.append("## Dangling citations found\n")
        for row in r["bad_rows"]:
            tag = "" if row["kind"] == "asked" else " (bonus check, not in J-1575's own asked prefixes)"
            L.append(f"- `{row['doc']}` **{row['date']}** cites **{row['id']}**{tag} -- no such id in "
                     f"its ledger. Bullet: \"{row['snippet']}...\"")
        L.append("")
    else:
        L.append("## Dangling citations found\n\nNone. Every F/J/D/I/S/T id cited inline in every "
                  "dated Current State bullet across every scanned plan doc resolves to a real ledger "
                  "entry.\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(SCRIPT_ROOT),
                     help="Nascence repo root to read plan docs + ledgers from")
    ap.add_argument("--out", default=None,
                     help="output report path (default: <root>/docs/reviews/ledger_id_citation_audit.md)")
    a = ap.parse_args()
    root = Path(a.root)
    out = Path(a.out) if a.out else root / "docs" / "reviews" / "ledger_id_citation_audit.md"

    result = audit(root)
    report = render_report(result)
    print(report)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\n# Written to {out}")


if __name__ == "__main__":
    main()
