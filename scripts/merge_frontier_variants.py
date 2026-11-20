"""
One-off, reversible merge of the open 'mottainai' paraphrase variants in data/frontier.json (D-0486, J-2428).

DRY-RUN BY DEFAULT: prints what would merge and changes nothing. `--apply` first copies frontier.json to
frontier.json.premerge.<UTC stamp>.bak (restore = copy it back), then merges every OPEN question containing --term
into ONE canonical entry (most encounters, then earliest born):
  * canonical.encounters = sum of all merged entries' encounters; last_seen = max; a finding is carried over if the
    canonical has none;
  * every other variant stays IN THE FILE with status "merged" + merged_into=<canonical id> (never deleted) and its
    wording is listed in canonical["variants"] as lineage.
Run it ONLY while Du is down (it refuses --apply if data/nascence.log was written in the last 120 s, unless
--force-running). The restart that follows should carry FRONTIER_SEMANTIC_MERGE as the founder decides.

    python scripts/merge_frontier_variants.py                  # dry run
    python scripts/merge_frontier_variants.py --apply          # founder, Du down
    python scripts/merge_frontier_variants.py --file X.json    # operate on another file (tests)
"""
from __future__ import annotations
import argparse, json, shutil, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import frontier as fr, profile, store_persist as sp   # core BEFORE anything lab_env-ish


def plan_merge(data: dict, term: str) -> dict | None:
    """Mutates nothing. {'canonical': entry, 'absorb': [entries]} for the open questions containing `term`, or None."""
    t = term.lower()
    group = [q for q in data.get("questions", []) if q.get("status") == "open" and t in str(q.get("q", "")).lower()]
    if len(group) < 2:
        return None
    group.sort(key=lambda q: (-int(q.get("encounters", 1)), q.get("born", 0.0)))
    return {"canonical": group[0], "absorb": group[1:]}


def apply_merge(plan: dict, now: float | None = None) -> dict:
    """Mutates the entries in `plan` in place. Returns a summary."""
    now = now or time.time()
    c, absorb = plan["canonical"], plan["absorb"]
    before = int(c.get("encounters", 1))
    lineage = c.setdefault("variants", [])
    for q in absorb:
        c["encounters"] = int(c.get("encounters", 1)) + int(q.get("encounters", 1))
        c["last_seen"] = max(float(c.get("last_seen", 0.0)), float(q.get("last_seen", 0.0)))
        if not c.get("finding") and q.get("finding"):
            for k in ("finding", "finding_title", "finding_ts"):
                if k in q:
                    c[k] = q[k]
        lineage.append({"id": q.get("id"), "q": q.get("q"), "source": q.get("source"), "born": q.get("born"),
                        "encounters": int(q.get("encounters", 1)), "merged_ts": now})
        q["status"] = "merged"
        q["merged_into"] = c.get("id")
        q["merged_ts"] = now
    return {"canonical_id": c.get("id"), "canonical_q": c.get("q"), "absorbed": len(absorb),
            "encounters_before": before, "encounters_after": c["encounters"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--term", default="mottainai")
    ap.add_argument("--file", default=None, help="frontier json to operate on (default: data/frontier.json)")
    ap.add_argument("--force-running", action="store_true", help="skip the 'Du seems to be running' refusal")
    a = ap.parse_args(argv)
    path = Path(a.file) if a.file else fr._F
    data = json.loads(path.read_text(encoding="utf-8"))
    plan = plan_merge(data, a.term)
    if plan is None:
        print(f"nothing to merge: fewer than 2 open questions contain {a.term!r}")
        return 0
    c = plan["canonical"]
    print(f"{'APPLY' if a.apply else 'DRY RUN'} on {path}")
    print(f"canonical: [{c['id']}] enc={c.get('encounters', 1)} {c['q'][:110]}")
    print(f"absorbing {len(plan['absorb'])} open variants (encounters sum "
          f"{sum(int(q.get('encounters', 1)) for q in plan['absorb'])}):")
    for q in plan["absorb"][:12]:
        print(f"   [{q['id']}] enc={q.get('encounters', 1)} {q['q'][:100]}")
    if len(plan["absorb"]) > 12:
        print(f"   ... and {len(plan['absorb']) - 12} more")
    if not a.apply:
        print("dry run: nothing written. Re-run with --apply while Du is down.")
        return 0
    log = fr._F.parent / "nascence.log"
    if not a.force_running and not a.file and log.exists() and time.time() - log.stat().st_mtime < 120:
        print("REFUSING: data/nascence.log was written in the last 120 s -- Du looks live. Stop Du first "
              "(or --force-running).")
        return 2
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    bak = path.with_name(path.name + f".premerge.{stamp}.bak")
    shutil.copy2(path, bak)
    print(f"backup: {bak}")
    summary = apply_merge(plan)
    if not a.file:
        profile.mark_live()          # sole writer while Du is down; lets the fenced _write_light() refresh the sidecar
        fr._save(data)
    else:
        sp.write_text_atomic(path, json.dumps(data, ensure_ascii=False))
    print("merged:", json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
