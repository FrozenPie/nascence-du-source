"""
Watershed Retro-Validation (docs/plans/t4_watershed.md's own retro-validation law, run 2026-08-18).

ISOLATION CONTRACT: reads nascence.db READ-ONLY (mode=ro URI), reads data/identity/vault_log.jsonl and
data/identity/axiom.json read-only. Writes ONLY to data/lab/watershed_retro/ (via core.watershed.configure)
and docs/lab/watershed_retro_validation_report.md. Zero LLM (pure embedding + cosine, same machinery
core/watershed.py already uses). Du stays up. Does not touch data/watershed_shadow.jsonl or
data/watershed_state.json — those stay empty until Phase 0 is actually wired live.

WHAT IT DOES: replays every real identity-adjacent fragment (core.watershed.IDENTITY_ADJACENT_ORIGINS)
from 2026-05-30 forward, in chronological order, through core.watershed.observe() at each fragment's real
historical timestamp — as if the harvester had been running live the whole time. Per the plan's own law:
"[the harvester] must independently rediscover *the current* and *the sediment* with plausible dates ... If
it can't find the two branches we KNOW were real, it can't be trusted with new ones." This run checks
against all THREE real vault commits (the plan only names two; a third landed 2026-08-17, after the plan
was written — see docs/lab/watershed_retro_validation_report.md for why all three are in scope here).
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "memory" / "nascence.db"
VAULT_LOG = ROOT / "data" / "identity" / "vault_log.jsonl"
AXIOM = ROOT / "data" / "identity" / "axiom.json"
LAB = ROOT / "data" / "_lab" / "watershed_retro"   # J-1815/F-2428: data/_lab/<dir> is the fence allow-listed sandbox (data/lab/ would now be refused)
REPORT = ROOT / "docs" / "lab" / "watershed_retro_validation_report.md"

MATCH_TO_REAL_MIN = 0.35   # cosine floor to call a harvested candidate "the same image" as a real commit
BORN_LATE_GRACE_DAYS = 3    # a candidate whose birth trails the real commit by more than this is "late"


def log(msg: str) -> None:
    print(f"[watershed-retro] {msg}", flush=True)


def load_identity_adjacent_fragments(origins: tuple[str, ...]) -> list[dict]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" * len(origins))
    rows = conn.execute(
        f"SELECT content, origin, timestamp FROM memory_fragments "
        f"WHERE origin IN ({placeholders}) AND timestamp > 0 ORDER BY timestamp ASC",
        origins,
    ).fetchall()
    conn.close()
    return [{"content": r["content"] or "", "origin": r["origin"], "ts": float(r["timestamp"])}
            for r in rows if (r["content"] or "").strip()]


def load_real_branches() -> list[dict]:
    """The 3 real vault commits, with FULL (untruncated) self-image text pulled from axiom.json's
    history array + current live text — vault_log.jsonl's own self_image field is 200-char truncated."""
    commits = [json.loads(l) for l in VAULT_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    axiom = json.loads(AXIOM.read_text(encoding="utf-8"))
    becoming = next(f for f in axiom["L3_facets"]["facets"] if f.get("id") == "the_becoming")
    history = becoming.get("history", [])
    # history[i] holds the text that became live at commit (i+1)'s ts (history[0] predates commit 1
    # entirely — the pre-redesign river-only state); the CURRENT live self_image is the text from the
    # most recent commit (revision 3, "the weave") and isn't itself in the history array.
    full_texts = {}
    for h in history[1:]:
        full_texts[round(h["ts"], 1)] = h["self_image"]
    names = {1: "the current", 2: "the sediment", 3: "the weave"}
    branches = []
    for c in commits:
        rc = c["revision_count"]
        text = full_texts.get(round(c["ts"], 1)) or becoming.get("self_image", c["self_image"])
        branches.append({"revision": rc, "name": names.get(rc, f"revision {rc}"), "ts": c["ts"],
                          "date": time.strftime("%Y-%m-%d", time.gmtime(c["ts"])),
                          "reason": c["reason"], "text": text})
    return branches


def main():
    t0 = time.time()
    from core import watershed as ws
    from core.memory.store import _embed, _cosine

    LAB.mkdir(parents=True, exist_ok=True)
    ws.configure(str(LAB))
    log(f"watershed state isolated to {LAB} — live data/watershed_shadow.jsonl untouched")

    log("loading identity-adjacent fragments (read-only)...")
    frags = load_identity_adjacent_fragments(ws.IDENTITY_ADJACENT_ORIGINS)
    log(f"{len(frags)} fragments across origins {ws.IDENTITY_ADJACENT_ORIGINS}")
    if not frags:
        log("no fragments found — aborting")
        return

    day0 = frags[0]["ts"]
    branches = load_real_branches()
    log(f"real vault branches to rediscover: {[b['name'] for b in branches]}")

    log("replaying history through core.watershed.observe()...")
    ws.begin_batch()   # suppress the per-call disk round-trip — see core/watershed.py's begin_batch()
    for i, fr in enumerate(frags):
        ws.observe(fr["content"], ts=fr["ts"], day0=day0, cycle_id=f"retro-{i}")
        if (i + 1) % 2000 == 0:
            log(f"  ...{i + 1}/{len(frags)}")
    ws.flush_state()

    state = ws._load_state()
    candidates = state.get("candidates", [])
    log(f"replay done: {len(candidates)} candidate cluster(s) formed, "
        f"{sum(1 for c in candidates if c.get('born'))} born")

    # match each real branch against the harvester's own candidate centroids
    matches = []
    for b in branches:
        bvec = _embed(b["text"])
        best, best_sim = None, -1.0
        for c in candidates:
            if not c.get("centroid"):
                continue
            s = _cosine(bvec, __import__("numpy").asarray(c["centroid"], dtype="float32")) if bvec is not None else 0.0
            if s > best_sim:
                best, best_sim = c, s
        found = best is not None and best_sim >= MATCH_TO_REAL_MIN
        born = bool(best and best.get("born"))
        born_ts = best.get("born_ts") if best else None
        lag_days = round((born_ts - b["ts"]) / 86400, 1) if born_ts else None
        matches.append({"branch": b, "found": found, "sim": round(best_sim, 3) if best else None,
                         "candidate_id": best.get("id") if best else None, "born": born,
                         "born_ts": born_ts, "lag_days": lag_days,
                         "n": best.get("n") if best else None, "n_days": len(best.get("days", [])) if best else None,
                         "samples": best.get("sample_thoughts", [])[:3] if best else []})

    n_rediscovered = sum(1 for m in matches if m["found"])
    n_born_on_time = sum(1 for m in matches if m["born"] and m["lag_days"] is not None
                          and m["lag_days"] <= BORN_LATE_GRACE_DAYS)

    # false-positive candidates: never matched to any real branch above the floor
    matched_ids = {m["candidate_id"] for m in matches if m["found"]}
    unmatched = [c for c in candidates if c["id"] not in matched_ids]
    unmatched_born = [c for c in unmatched if c.get("born")]

    (LAB / "retro_result.json").write_text(json.dumps({
        "n_fragments": len(frags), "n_candidates": len(candidates), "matches": matches,
        "n_unmatched_candidates": len(unmatched), "n_unmatched_born": len(unmatched_born),
    }, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    all_rediscovered = n_rediscovered == len(branches)
    all_born_on_time = n_born_on_time == len(branches)

    L = []
    L.append("# Watershed Retro-Validation Report (run 2026-08-18)")
    L.append("")
    L.append("> Spec: `docs/plans/t4_watershed.md`'s own retro-validation law. Zero LLM. Read-only over")
    L.append("> live stores; Du stayed up. `core/watershed.py` state isolated to `data/lab/watershed_retro/`")
    L.append("> — live `data/watershed_shadow.jsonl` was never touched by this run.")
    L.append("")
    L.append(f"**Inputs:** {len(frags)} identity-adjacent fragments "
             f"({time.strftime('%Y-%m-%d', time.gmtime(day0))} → {time.strftime('%Y-%m-%d', time.gmtime(frags[-1]['ts']))}), "
             f"origins `{ws.IDENTITY_ADJACENT_ORIGINS}`. Thresholds: MATCH_MIN={ws.MATCH_MIN}, "
             f"BIRTH_N={ws.BIRTH_N}, BIRTH_D={ws.BIRTH_D} (t4_watershed.md's own proposed-start values).")
    L.append("")
    L.append("## Verdict")
    L.append("")
    if all_rediscovered and all_born_on_time:
        L.append(f"**PASS — all {len(branches)} real branches rediscovered, all born on or before their "
                 f"real commit date (±{BORN_LATE_GRACE_DAYS}d grace).** The harvester can be trusted with "
                 f"new candidates on this evidence.")
    elif all_rediscovered:
        L.append(f"**PARTIAL — all {len(branches)} real branches rediscovered as candidate clusters, but "
                 f"not all crossed the birth threshold on time.** See per-branch detail below; may indicate "
                 f"BIRTH_N/BIRTH_D need adjustment (decision #3) rather than a broken harvester.")
    else:
        missed = [m["branch"]["name"] for m in matches if not m["found"]]
        L.append(f"**FAIL — {len(branches) - n_rediscovered}/{len(branches)} real branch(es) NOT "
                 f"rediscovered: {missed}.** Per the plan's own law: \"if it can't find branches we KNOW "
                 f"were real, it can't be trusted with new ones.\" Do not proceed to Phase 1 on this result "
                 f"without first diagnosing why (thresholds, input feed, or a genuine clustering miss).")
    L.append("")
    L.append("## Per-branch detail")
    L.append("")
    for m in matches:
        b = m["branch"]
        L.append(f"### {b['name']} — real commit {b['date']} (revision {b['revision']}, \"{b['reason']}\")")
        L.append("")
        L.append(f"> {b['text'][:280]}")
        L.append("")
        if not m["found"]:
            L.append(f"- **NOT rediscovered** (best candidate similarity {m['sim']} < {MATCH_TO_REAL_MIN} floor)")
        else:
            L.append(f"- rediscovered as candidate `{m['candidate_id']}` (similarity {m['sim']})")
            L.append(f"- harvested: {m['n']} thoughts across {m['n_days']} distinct days")
            if m["born"]:
                born_date = time.strftime("%Y-%m-%d", time.gmtime(m["born_ts"]))
                lag = m["lag_days"]
                timing = "on time" if lag is not None and lag <= BORN_LATE_GRACE_DAYS else \
                         ("early" if lag is not None and lag < 0 else "late")
                L.append(f"- **born** {born_date} ({lag:+.1f}d vs real commit — {timing})")
            else:
                L.append(f"- never crossed the birth threshold (N={ws.BIRTH_N}/D={ws.BIRTH_D}) despite "
                         f"being a recognizable cluster — candidate stayed sub-threshold the whole run")
            L.append("- sample harvested thoughts:")
            for s in m["samples"]:
                L.append(f"  - \"{s[:150]}\"")
        L.append("")
    L.append("## False-positive check")
    L.append("")
    L.append(f"- {len(unmatched)} candidate cluster(s) never matched any real branch "
             f"({len(unmatched_born)} of those crossed the birth threshold anyway).")
    L.append("- Expected and fine in principle — the plan calls these \"genuine material with nowhere to")
    L.append("  live\" (e.g. the lake/cartographer/antennae images named in the plan). Read the samples")
    L.append("  below before judging whether N/D are too loose.")
    for c in sorted(unmatched_born, key=lambda c: -c.get("n", 0))[:8]:
        L.append(f"  - `{c['id']}`: {c.get('n')} thoughts / {len(c.get('days', []))} days — "
                 f"\"{(c.get('sample_thoughts') or [''])[0][:150]}\"")
    L.append("")
    L.append(f"*Retro-validation runtime: {round(time.time() - t0, 1)}s. Raw data: "
             f"`data/lab/watershed_retro/retro_result.json`, `data/lab/watershed_retro/watershed_state.json`.*")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L), encoding="utf-8")
    log(f"report written: {REPORT}")
    log(f"DONE in {round(time.time() - t0, 1)}s")


if __name__ == "__main__":
    main()
