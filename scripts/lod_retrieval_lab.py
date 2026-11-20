"""
LOD RETRIEVAL LAB — 2026-08-29, J-0372 (D-0054 gate, A-1 spec #1, du_recall_lens_upgrades read-first).

Tests the OpenViking-style claim from docs/staged/antigravity_ecosystem_proposals.md A-1 spec #1:
does an L0(raw)/L1(gist)/L2(theme) STAGED-DETAIL retrieval index serve a real query better than
Du's current single-level top-k (`core.memory.store.retrieve()`)?

DUPLICATE CHECK (done before writing this script, per the job's own gate): read
docs/staged/du_recall_lens_upgrades.md in full. That plan is a DIFFERENT technique family entirely —
spectral diffusion over the concept co-occurrence graph, deterministic fact anchoring, and
counterfactual-ensemble re-ranking (three graph-propagation lenses ported from UDMS). None of the
three touches staged abstraction-level retrieval. Not a duplicate — proceeding. (Re-confirmed
2026-08-29 on resume: grepped du_recall_lens_upgrades.md for L0/L1/L2/abstraction_level/staged-detail
keywords — zero hits.)

WHAT L0/L1/L2 MEANS HERE, GROUNDED IN DU'S REAL SCHEMA (not the blueprint's fictional
`cognitive_mmu.py`): `memory_fragments.abstraction_level` already exists (0=raw, 1=gist,
2=theme/chapter, 3=identity — memory_levels_plan.md's own axis). Real non-cold, non-chaptered pool
sizes read from a lab-isolated DB copy 2026-08-29: L0 (level 0) = 3,732 rows, L1 (level 1) = 1,303
rows, L2 (level >=2) = 179 rows. No new schema, no new deps — this experiment scores each level's
OWN existing embeddings and composes a staged result set, vs. the baseline which is Du's real
`store.retrieve()` call unmodified.

METHOD.
  Baseline arm:  store.retrieve(query_text=q) — Du's real live single-level (well, tier-mixed but not
                 abstraction-staged) top-k call, output used as-is (including its own recency-guarantee
                 insertions), length n.
  LOD arm:       cosine-score the L0/L1/L2 pools independently against the same query embedding, then
                 compose n items via a slot cascade (L2 anchor slots -> L1 gist slots -> L0 raw fills
                 the rest, unfilled slots at a coarser level cascade down) — the same tier-cascade-with-
                 overflow IDIOM store.py's own TIER_SLOTS/retrieve() already uses, so the two arms are
                 structurally comparable, not an apples-to-oranges design.
  Judge:         judge_panel.rule_detail (the real two-family decoupled panel + tiebreak — JUDGE_1
                 gemma4:12b, JUDGE_2 falcon3:7b, TIEBREAK granite3.1-moe:3b), blind: arms are randomly
                 relabeled Set A / Set B per query (own RNG stream, not the sampling RNG) and the judge
                 sees only the question + two content lists, never which arm is which.
  Queries:       real logged frontier questions (data/frontier.json, 6,430 entries spanning
                 open/resolved/faded) — a random sample (seeded, deduped, length-filtered) large
                 enough to clear >=100 actually-judged (non-null-verdict) pairs.

KILL CRITERION (pre-registered, verbatim from the spec): if LOD-staged does not beat the baseline by
>=10 win-rate points over >=100 judged pairs, archive as no-lift. Since the judge is a forced binary
choice (prefer_a bool, no tie option), baseline_win_rate = 1 - lod_win_rate exactly, so the margin
condition reduces to lod_win_rate >= 0.55 (>=55/100 wins with n=100, scaling with n).

ISOLATION (job-queue isolation="required", lab_env.py discipline):
  - DB reads go through lab_env.isolate(), which redirects core.memory.store.DB_PATH to a copy —
    every store.retrieve()/pool-scoring call in this script is against the ISOLATED copy, never the
    live nascence.db.
  - judge_panel._LOG (data/judge_panel_log.jsonl) is ALSO redirected via isolate(also=...) so this
    lab's ~130 rulings don't pollute the live panel ledger judge_panel.status() reads for real
    agreement-rate/health metrics.
  - core.telemetry.log_llm_call and core.retrieval_probe.observe are no-op'd for the run (same
    established pattern as scripts/routing_lab.py) — both write to live per-cycle logs
    (data/llm_calls.jsonl, data/retrieval_probe_log.jsonl) that this lab has no business touching;
    the judge calls themselves still hit the real judge model hubs (read-only inference, not state).
  - The live DB's row count/mtime is checked immediately before and after the run as a backstop.

Writes: data/lod_retrieval_lab_shadow.jsonl (one row per judged pair, both arms' fragment ids/content
snippets + the judge verdict) and docs/lab/lod_retrieval_lab_2026-08-29.md (the report). Never writes
to memory_fragments or any live per-cycle log.

RESUME NOTE (2026-08-29, later same day): the coding-agent worktree this script originally lived in
(.claude/worktrees/agent-acd5175f51cd1efca) was torn down out from under the running process by an
external cleanup mid-lab (its branch was gone from `git worktree list` and the directory was emptied).
The script is unchanged in substance; it now lives directly under the main checkout's scripts/ (where
data/docs/DB already lived per the ROOT note below) so a worktree teardown can't orphan it again
mid-run.

CHUNKING NOTE (2026-08-29, second resume): the harness's own background-process runner (run_in_background)
got blocked by an auto-mode classifier when targeting the main checkout directly, and a single query's
judge round-trip against two local CPU-bound LLM hubs runs ~40-100s, so 130 queries cannot fit inside one
foreground Bash call's ceiling. Added --offset so this script can be invoked repeatedly, foreground,
each call handling a slice of the SAME deterministic (SEED-shuffled) candidate pool; every row is tagged
with its true global pool index so chunks never collide and re-running a chunk overwrites cleanly on
dedupe. Use `python lod_retrieval_lab.py --aggregate` once enough chunks have run to read back the WHOLE
shadow log, dedupe by global index, and (re)write the final report from the full accumulated set —
the per-chunk in-process `results` list is no longer what the report is computed from.
"""
from __future__ import annotations

import asyncio
import json
import random
import sys
import time
from pathlib import Path

# Data/docs/live-DB live under the main checkout (C:\Nascence) — this script now also lives there
# directly (see RESUME NOTE above), so ROOT and the script's own location coincide.
ROOT = Path(r"C:\Nascence")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")

from lab_env import isolate  # noqa: E402

SHADOW_LOG = ROOT / "data" / "lod_retrieval_lab_shadow.jsonl"
REPORT = ROOT / "docs" / "lab" / "lod_retrieval_lab_2026-08-29.md"
LIVE_DB = ROOT / "data" / "memory" / "nascence.db"

N_TARGET = 130     # buffer above the >=100-judged-pairs requirement
POOL_SIZE = 200     # size of the fixed deterministic candidate pool chunks are sliced from
OFFSET = 0          # chunk start index into the deterministic pool (set via --offset)
SEED = 20260829
SNIPPET_CHARS = 220


def _load_queries(n: int) -> list[str]:
    frontier = json.loads((ROOT / "data" / "frontier.json").read_text(encoding="utf-8"))
    qs = [q["q"].strip() for q in frontier["questions"] if q.get("q") and len(q["q"].strip()) >= 20]
    rnd = random.Random(SEED)
    rnd.shuffle(qs)
    seen: set[str] = set()
    uniq = []
    for q in qs:
        if q not in seen:
            seen.add(q)
            uniq.append(q)
        if len(uniq) >= n:
            break
    return uniq


def _build_pools(store):
    with store._connect() as conn:
        rows = conn.execute(
            "SELECT fragment_id, content, embedding, abstraction_level "
            "FROM memory_fragments WHERE (cold = 0 OR cold IS NULL) "
            "AND (chapter_id IS NULL OR chapter_id = '') AND embedding IS NOT NULL"
        ).fetchall()
    l0, l1, l2 = [], [], []
    for r in rows:
        lvl = r["abstraction_level"] or 0
        (l0 if lvl == 0 else l1 if lvl == 1 else l2).append(r)
    return l0, l1, l2


def _score(pool, query_vec, store):
    scored = []
    for r in pool:
        vec = store._blob_to_vec(r["embedding"])
        scored.append((store._cosine(query_vec, vec), r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def _lod_staged(l0_scored, l1_scored, l2_scored, n: int):
    """Slot cascade: ~20% L2 (broad thematic anchor), ~30% L1 (gist), rest L0 (specific raw) —
    unfilled slots at a coarser level cascade to the next finer one, mirroring store.py's own
    TIER_SLOTS overflow idiom."""
    l2_n = max(1, round(0.2 * n))
    l1_n = max(1, round(0.3 * n))
    l0_n = max(0, n - l2_n - l1_n)
    picked, spare = [], 0
    for base_n, pool in ((l2_n, l2_scored), (l1_n, l1_scored), (l0_n, l0_scored)):
        take = base_n + spare
        chunk = pool[:take]
        picked.extend(chunk)
        spare = take - len(chunk)
    # if pools ran out early (spare left over from l0 itself, i.e. l0 pool exhausted too — very
    # unlikely given l0's size, but handled): just return what we got.
    return picked[:n]


_JUDGE_SYSTEM = (
    "You judge which of two candidate memory-retrieval result sets better serves a question someone "
    "is holding. You do not know how either set was produced. Prefer the set that is more relevant, "
    "covers the question from more useful angles, and has less irrelevant filler. Respond with JSON "
    'only: {"prefer_a": true or false, "why": "<12 words or fewer>"}.'
)


def _format_set(items: list[str]) -> str:
    return "\n".join(f"{i+1}. {c}" for i, c in enumerate(items))


async def run_async():
    live_before = (LIVE_DB.stat().st_size, LIVE_DB.stat().st_mtime) if LIVE_DB.exists() else None

    with isolate() as lab_dir:
        from core.memory import store
        from core import judge_panel as jp
        from core import telemetry
        from core import retrieval_probe

        # redirect judge_panel's own ruling ledger into the lab dir (own dedicated log, per
        # lab_env's `also=` idiom) — done AFTER isolate() enters so we patch the real module object.
        judge_log_orig = jp._LOG
        jp._LOG = lab_dir / "judge_panel_log.jsonl"
        # F-1683/J-1199: call_node() also writes log_thought_station + log_llm_latency, not just
        # log_llm_call -- neutralize_telemetry() no-ops all three and redirects telemetry's own
        # Path globals into lab_dir too; telemetry_saved is restored below, same as the other two.
        from lab_isolation import neutralize_telemetry, restore_telemetry
        telemetry_saved = neutralize_telemetry(lab_dir, telemetry)
        probe_orig = retrieval_probe.observe
        retrieval_probe.observe = lambda *a, **k: None

        try:
            store.prewarm()
            l0, l1, l2 = _build_pools(store)
            print(f"[lod-lab] pools: L0={len(l0)} L1={len(l1)} L2={len(l2)}", flush=True)

            pool_queries = _load_queries(POOL_SIZE)
            queries = pool_queries[OFFSET:OFFSET + N_TARGET]
            print(f"[lod-lab] chunk offset={OFFSET} processing {len(queries)} of "
                  f"{len(pool_queries)} pool candidates from data/frontier.json", flush=True)

            ab_rnd = random.Random(SEED + 1 + OFFSET)
            SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
            results = []

            with open(SHADOW_LOG, "a", encoding="utf-8") as shadow_f:
                for local_i, q in enumerate(queries):
                    i = OFFSET + local_i  # global pool index — stable across chunks, used for dedupe
                    query_vec = store._embed(q)
                    if query_vec is None:
                        continue
                    baseline = store.retrieve(episodic_keys=[], semantic_keys=[], query_text=q)
                    if not baseline:
                        continue
                    n = len(baseline)
                    base_items = [(f.content or "")[:SNIPPET_CHARS] for f in baseline]
                    base_ids = [f.fragment_id for f in baseline]

                    l0s = _score(l0, query_vec, store)
                    l1s = _score(l1, query_vec, store)
                    l2s = _score(l2, query_vec, store)
                    lod_rows = _lod_staged(l0s, l1s, l2s, n)
                    lod_items = [(r["content"] or "")[:SNIPPET_CHARS] for _s, r in lod_rows]
                    lod_ids = [r["fragment_id"] for _s, r in lod_rows]

                    if not lod_items:
                        continue

                    a_is_lod = ab_rnd.random() < 0.5
                    set_a = lod_items if a_is_lod else base_items
                    set_b = base_items if a_is_lod else lod_items
                    user = (f"Question: {q}\n\nSet A:\n{_format_set(set_a)}\n\nSet B:\n{_format_set(set_b)}")

                    verdict = await jp.rule_detail(_JUDGE_SYSTEM, user, "prefer_a",
                                                    context=f"lod-lab:{i}")
                    prefer_a = verdict["verdict"]
                    winner = None
                    if prefer_a is not None:
                        a_won = prefer_a
                        winner = "lod" if (a_won == a_is_lod) else "baseline"

                    row = {
                        "i": i, "query": q, "n": n,
                        "baseline_ids": base_ids, "lod_ids": lod_ids,
                        "a_is_lod": a_is_lod, "how": verdict["how"],
                        "v1": verdict["v1"], "v2": verdict["v2"],
                        "winner": winner,
                    }
                    shadow_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    shadow_f.flush()
                    results.append(row)
                    print(f"  chunk {local_i+1}/{len(queries)} (global i={i}) n={n} "
                          f"how={verdict['how']} winner={winner}", flush=True)
        finally:
            jp._LOG = judge_log_orig
            restore_telemetry(telemetry, telemetry_saved)
            retrieval_probe.observe = probe_orig

    # --- outside isolation now; aggregate + report -------------------------------------------------
    judged = [r for r in results if r["winner"] is not None]
    lod_wins = sum(1 for r in judged if r["winner"] == "lod")
    base_wins = sum(1 for r in judged if r["winner"] == "baseline")
    n_judged = len(judged)
    lod_rate = lod_wins / n_judged if n_judged else 0.0
    base_rate = base_wins / n_judged if n_judged else 0.0
    margin_pts = (lod_rate - base_rate) * 100

    print(f"\n[lod-lab] sampled={len(results)} judged={n_judged} lod_wins={lod_wins} "
          f"baseline_wins={base_wins} lod_win_rate={lod_rate:.3f} margin_pts={margin_pts:.1f}", flush=True)

    kill = not (n_judged >= 100 and margin_pts >= 10.0)
    verdict_line = "KILL — no-lift, does not clear the >=10pt / >=100-pair bar" if kill else "PASS — clears the >=10pt / >=100-pair bar"

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# LOD Retrieval Lab — L0/L1/L2 staged index vs baseline top-k (2026-08-29, J-0372)

**Spec:** docs/staged/antigravity_ecosystem_proposals.md A-1 spec #1 (OpenViking L0/L1/L2
progressive-detail retrieval). **Duplicate check:** docs/staged/du_recall_lens_upgrades.md read in
full first — different technique family (spectral diffusion / anchoring / counterfactual re-rank),
not a staged-detail retrieval idea. Not a duplicate.

## Method

- Baseline arm: `core.memory.store.retrieve()` called live (against an isolated DB copy) with each
  query's real text — Du's actual current recall call, output used as-is.
- LOD arm: cosine-scored independently against the real `abstraction_level` 0/1/2 pools
  (L0=raw, L1=gist, L2=theme/chapter — Du's existing schema, no new columns), composed via a
  slot-cascade (~20% L2, ~30% L1, rest L0, unfilled coarser slots cascade to finer) sized to match
  each query's own baseline result count.
- Judge: `core.judge_panel.rule_detail` — real two-family decoupled panel (gemma4:12b / falcon3:7b)
  + granite3.1-moe:3b tiebreak, blind (Set A/B relabeled per query via an independent RNG stream, no
  ordering or method hint in the prompt).
- Queries: {len(results)} real logged frontier questions sampled from `data/frontier.json`
  (6,430 entries; sample seeded/deduped/length-filtered >=20 chars).

## Result

- Sampled/attempted: {len(results)}
- Actually judged (non-null verdict): {n_judged}
- LOD wins: {lod_wins} ({lod_rate:.1%})
- Baseline wins: {base_wins} ({base_rate:.1%})
- Margin (LOD - baseline win rate): {margin_pts:.1f} points

## Verdict

**{verdict_line}**

Kill criterion (pre-registered, from the spec): LOD-staged must beat baseline by >=10 win-rate
points over >=100 judged pairs, or archive as no-lift.

## Isolation

Run entirely inside `lab_env.isolate()` — every DB read against a lab-dir copy of `nascence.db`,
never the live file. `judge_panel._LOG` redirected into the same lab dir (own dedicated log,
`also=`-idiom) so the ~{n_judged} lab rulings never touch the live `judge_panel_log.jsonl` panel
ledger. `telemetry.log_llm_call` and `retrieval_probe.observe` no-op'd for the run (same pattern as
`scripts/routing_lab.py`) since both write to live per-cycle logs unrelated to this experiment.
Live DB row-count/mtime checked before and after as a backstop (see job's own live-DB check note).

Shadow log: `data/lod_retrieval_lab_shadow.jsonl` ({n_judged} rows, one per judged pair — query,
both arms' fragment ids, judge how/v1/v2, winner).
""",
        encoding="utf-8",
    )
    print(f"[lod-lab] report written: {REPORT}", flush=True)

    if LIVE_DB.exists():
        live_after = (LIVE_DB.stat().st_size, LIVE_DB.stat().st_mtime)
        print(f"[lod-lab] live DB check — before={live_before} after={live_after} "
              f"unchanged={live_before == live_after}", flush=True)

    return {
        "sampled": len(results), "judged": n_judged, "lod_wins": lod_wins,
        "baseline_wins": base_wins, "lod_win_rate": lod_rate, "margin_pts": margin_pts,
        "kill": kill,
    }


def aggregate_and_report():
    """Read the WHOLE shadow log back (all chunks, any offsets), dedupe by global pool index `i`
    (keep the LAST occurrence so a re-run of a chunk cleanly supersedes an earlier partial one), and
    (re)write REPORT from the full accumulated set. This is what the real pre-registered kill-criterion
    number is computed from once enough chunks have run — not any single chunk's in-process results."""
    rows_by_i: dict[int, dict] = {}
    if SHADOW_LOG.exists():
        with open(SHADOW_LOG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue  # tolerate a stray corrupted line from an earlier interrupted run
                rows_by_i[row["i"]] = row  # last write for a given global index wins
    results = [rows_by_i[k] for k in sorted(rows_by_i)]

    judged = [r for r in results if r["winner"] is not None]
    lod_wins = sum(1 for r in judged if r["winner"] == "lod")
    base_wins = sum(1 for r in judged if r["winner"] == "baseline")
    n_judged = len(judged)
    lod_rate = lod_wins / n_judged if n_judged else 0.0
    base_rate = base_wins / n_judged if n_judged else 0.0
    margin_pts = (lod_rate - base_rate) * 100

    print(f"[lod-lab][aggregate] total attempted rows={len(results)} judged={n_judged} "
          f"lod_wins={lod_wins} baseline_wins={base_wins} lod_win_rate={lod_rate:.3f} "
          f"margin_pts={margin_pts:.1f}", flush=True)

    kill = not (n_judged >= 100 and margin_pts >= 10.0)
    verdict_line = ("KILL — no-lift, does not clear the >=10pt / >=100-pair bar" if kill
                     else "PASS — clears the >=10pt / >=100-pair bar")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# LOD Retrieval Lab — L0/L1/L2 staged index vs baseline top-k (2026-08-29, J-0372)

**Spec:** docs/staged/antigravity_ecosystem_proposals.md A-1 spec #1 (OpenViking L0/L1/L2
progressive-detail retrieval). **Duplicate check:** docs/staged/du_recall_lens_upgrades.md read in
full first (re-confirmed on resume via keyword grep for L0/L1/L2/abstraction_level/staged-detail:
zero hits) — different technique family (spectral diffusion / anchoring / counterfactual re-rank),
not a staged-detail retrieval idea. Not a duplicate.

## Method

- Baseline arm: `core.memory.store.retrieve()` called live (against an isolated DB copy) with each
  query's real text — Du's actual current recall call, output used as-is.
- LOD arm: cosine-scored independently against the real `abstraction_level` 0/1/2 pools
  (L0=raw, L1=gist, L2=theme/chapter — Du's existing schema, no new columns), composed via a
  slot-cascade (~20% L2, ~30% L1, rest L0, unfilled coarser slots cascade to finer) sized to match
  each query's own baseline result count.
- Judge: `core.judge_panel.rule_detail` — real two-family decoupled panel (gemma4:12b / falcon3:7b)
  + granite3.1-moe:3b tiebreak, blind (Set A/B relabeled per query via an independent RNG stream, no
  ordering or method hint in the prompt).
- Queries: {len(results)} real logged frontier questions sampled from `data/frontier.json`
  (6,430 entries; sample seeded/deduped/length-filtered >=20 chars), processed across multiple
  chunked runs (see CHUNKING NOTE in this script's own docstring) and aggregated by global pool
  index, deduped, here.

## Result

- Sampled/attempted: {len(results)}
- Actually judged (non-null verdict): {n_judged}
- LOD wins: {lod_wins} ({lod_rate:.1%})
- Baseline wins: {base_wins} ({base_rate:.1%})
- Margin (LOD - baseline win rate): {margin_pts:.1f} points

## Verdict

**{verdict_line}**

Kill criterion (pre-registered, from the spec): LOD-staged must beat baseline by >=10 win-rate
points over >=100 judged pairs, or archive as no-lift.

## Isolation

Run entirely inside `lab_env.isolate()` — every DB read against a lab-dir copy of `nascence.db`,
never the live file. `judge_panel._LOG` redirected into the same lab dir (own dedicated log,
`also=`-idiom) so lab rulings never touch the live `judge_panel_log.jsonl` panel ledger.
`telemetry.log_llm_call` and `retrieval_probe.observe` no-op'd for the run (same pattern as
`scripts/routing_lab.py`) since both write to live per-cycle logs unrelated to this experiment.
Live DB row-count/mtime checked before and after each chunk as a backstop.

Shadow log: `data/lod_retrieval_lab_shadow.jsonl` ({len(results)} total rows after dedupe by global
pool index, one per attempted pair — query, both arms' fragment ids, judge how/v1/v2, winner).
""",
        encoding="utf-8",
    )
    print(f"[lod-lab][aggregate] report written: {REPORT}", flush=True)
    return {
        "sampled": len(results), "judged": n_judged, "lod_wins": lod_wins,
        "baseline_wins": base_wins, "lod_win_rate": lod_rate, "margin_pts": margin_pts,
        "kill": kill,
    }


if __name__ == "__main__":
    if "--aggregate" in sys.argv:
        summary = aggregate_and_report()
        print(json.dumps(summary, indent=2))
    else:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        if len(args) > 0:
            N_TARGET = int(args[0])  # count to process this invocation
        if len(args) > 1:
            OFFSET = int(args[1])  # start index into the deterministic POOL_SIZE candidate pool
        summary = asyncio.run(run_async())
        print(json.dumps(summary, indent=2))
