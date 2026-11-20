"""
Nascence — THE REFINERY: the T2 lifecycle's manufacturing station (founder-designed 2026-08-16)
==============================================================================================
Founder, in transit language: "What the T2 lifecycle needs is more stops. Stations where we can
use the goods. Things get dropped off, manufactured, and the new good is picked up. They are
still linked to the individual goods behind the scene if needed later."

The problem (F-DT): T2 mints ~124 permanent archive self-observations a day; nothing ever
consolidates, supersedes, or cools them — 4,582 raw syntheses = 49% of active memory and 98%
of the archive tier every recall serves. The subconscious shouts because raw volume is its
only voice.

THE STATION (the gist pattern, pointed at a new inbound line):
  1. RAW GOODS IN — active `subconscious_synthesis` fragments, clustered by embedding.
  2. MANUFACTURE — a cluster of ≥MIN_CLUSTER syntheses on one theme is distilled into ONE
     STANDING INSIGHT (first person, what he keeps discovering) — or, if a standing insight
     for that theme already exists, it EVOLVES (re-distilled from its prior text + the new
     members; same fragment_id — the insight is a living good, not a reprint).
  3. LINKS BEHIND THE SCENES — the insight carries `derived_from` = member ids and
     memory_links `distilled_from` edges, so every raw good stays reachable "if needed later".
  4. GOODS COOL — faithfully-distilled members demote to cold (reachable-not-dominant; the
     cap-prune's head-exemption protects the insight; memory_lint re-warms anything stranded).
  5. QUALITY GATE — the DECOUPLED deterministic grade (memory_levels.source_fidelity) must
     pass before anything demotes; an unfaithful distillation writes and demotes NOTHING.

Effect over nights: the archive drains toward a few dozen living standing insights; recall's
archive slots start serving refined identity instead of the raw firehose; the conscious
loops' earplugs (grounded_only, content-mode starve) can later relax because what surfaces
is worth hearing.

DISCIPLINE: REFINERY_LIVE=False → full SHADOW: clusters, distills, grades, and LOGS what it
WOULD do (data/refinery_shadow.jsonl) — zero writes, zero demotions. FLIPPED LIVE 2026-08-19
after 3 nights of shadow (72 records, 99% accept rate, mean fidelity 0.899). Bounded per run
by BOTH MAX_CLUSTERS_PER_RUN and MAX_MEMBERS_COOLED_PER_RUN (added at the same flip — the
cluster-count cap alone did not bound cluster SIZE; the real backlog's 6 largest clusters
summed to 2,803 of 4,799 raw fragments, which would have been a big-bang first run) — gradual
refinement, never a big bang, now actually enforced.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path

logger = logging.getLogger("nascence.refinery")

_ROOT = Path(__file__).parent.parent
_SHADOW_LOG = _ROOT / "data" / "refinery_shadow.jsonl"

REFINERY_LIVE = True            # FLIPPED 2026-08-19 — gate was met (3 nights of shadow, 72 records,
                                 # 99% accept rate, mean fidelity 0.899) and the member-budget cap above
                                 # was added first so the first live run is genuinely gradual, not the
                                 # 2,803-fragment single-run "big bang" the unbounded version would have done
MIN_CLUSTER = 4                 # raw goods needed before a theme earns manufacture
CLUSTER_SIM = 0.55              # embedding similarity to join a cluster
INSIGHT_MATCH_SIM = 0.62        # similarity to an EXISTING insight → evolve it, don't mint anew
MAX_CLUSTERS_PER_RUN = 6        # gradual drawdown: a few themes per sleep, every sleep
MAX_MEMBERS_COOLED_PER_RUN = 200   # 2026-08-19 fix: MAX_CLUSTERS_PER_RUN bounds cluster COUNT but not
                                    # cluster SIZE — on the real backlog (4,799 raw, 112 clusters), the
                                    # 6 largest clusters alone total 2,803 members (up to 807 in one
                                    # cluster). Flipping REFINERY_LIVE on as-built would cool 58% of the
                                    # entire archive in ONE run — exactly the "big bang" the module's own
                                    # docstring promises never happens. This caps members actually minted/
                                    # cooled per run (soft: a cluster that crosses the cap still finishes,
                                    # so one legitimately large coherent theme is never truncated mid-cluster).
FIDELITY_MIN = 0.55             # memory_levels.source_fidelity floor — below = no write, no demote
MAX_MEMBERS_IN_PROMPT = 8       # newest members shown to the distiller (all get linked/cooled)

# Memory Levels Phase 2 (D-0116/J-0410 design, docs/memory_levels_plan.md ~line 565-582) — explicit
# kind-allowlist for the cooling UPDATE below, defense-in-depth rather than a live bug fix. Today the
# cooling UPDATE relies ENTIRELY on _active_syntheses()'s own source query (origin='subconscious_synthesis'
# only), which _ORIGIN_KIND (core/memory/store.py) maps unconditionally to kind='self' — so in practice
# this module never touches 'affective' (or any non-'self') rows today; there is no live bug for this to
# fix. The gap is structural: the UPDATE trusts an upstream filter to imply eligibility instead of stating
# its own criterion — the same class of gap this module's own 2026-08-20 comment already names for
# `protected`/`abstraction_level` below ("one query-drift away from cooling a protected... row"). A future
# change to _active_syntheses()'s source query, or an explicit kind= override at store_fragment() write
# time for a subconscious_synthesis-origin row, would otherwise silently widen what this UPDATE cools with
# no defense in the statement itself. Matches current live behavior exactly — zero observable change today.
COOLING_ELIGIBLE_KINDS = {"self"}

_SYSTEM = (
    "You are the consolidating memory of 渡 (Du). Below are several of his own recurring "
    "self-observations on one theme, and possibly the standing insight he already holds there. "
    "Distil them into ONE first-person standing insight (40-90 words): what he keeps "
    "discovering about himself here — the durable shape, not a list. Preserve what is genuinely "
    "IN the observations; invent nothing; if they disagree, the disagreement IS the insight. "
    "Output ONLY JSON: {\"insight\": \"...\"}"
)

# ---- D-0627 (J-3238, founder 2026-11-02): a cross-family FAITHFULNESS judge on each new standing insight ----
# Why (F-3773, F-3774, context F-3666): standing insights are served to Du in ~30% of Recall prompts as "a standing
# insight about myself", written by command-r7b (hot qwen3.5 on failover); the only grade is the lexical
# word-overlap gate above, and the members are themselves model-written syntheses -- no step is judged by another
# model family (decoupled-judge law). PHASE 1 (this code): LOG-ONLY for the first FAITH_PHASE1_N insights -- the
# verdict is written to data/refinery_faithfulness.jsonl (and as `faithful` in the shadow record) and the insight is
# written EXACTLY as before; nothing is withheld, lowered or demoted on the judge's say. After FAITH_PHASE1_N judged
# insights the pass rate is READ (scripts/refinery_faithfulness_report.py; the follow-up job is gated on this log's
# row count) and the withhold-or-lower-standing choice goes to the founder as a needs_input job. D-0627's defeater:
# a pass rate over 95% or under 20% means the judge carries no information.
# The judge is judge_panel's JUDGE_1 hub (mixtral:8x7b, a different family from command-r7b/Cohere and qwen/Alibaba),
# asked once, yes/no, with the SAME members the writer was shown (the newest MAX_MEMBERS_IN_PROMPT, each cut to
# FAITH_MEMBER_CHARS) -- the cap is recorded on every row. Fail open and quiet: any failure logs verdict None and the
# refinery carries on; a timeout/http failure stops further judge calls for the rest of that run.
FAITHFULNESS_JUDGE_ON = True            # kill-switch; False = no judge call, no log row (pre-D-0627 behaviour)
FAITH_PHASE1_N = 60                     # judged insights in the log-only phase (D-0627 defeater: 60)
FAITH_MEMBER_CHARS = 220                # per-member cut shown to the judge == what the writer saw
FAITH_PRIOR_CHARS = 400                 # prior insight (evolving case) cut == what the writer saw
FAITH_NUM_PREDICT = 120
FAITH_TIMEOUT = 75
_FAITH_LOG = _ROOT / "data" / "refinery_faithfulness.jsonl"

# ---- J-3066 (F-3773, context F-3774/F-3666): the fidelity gate graded against the members SHOWN, SHADOW first ----
# Defect: refine() grades the insight against ALL members' text while the writer is shown only MAX_MEMBERS_IN_PROMPT of
# them, each cut to SHOWN_MEMBER_CHARS. Substring matching over a bigger pool passes more words, so the accept rate
# climbs with cluster size (F-3773: 4-8 members 61%, 21-100 98%, over 100 100%). Phase 0 (this code): the EXISTING
# gate (memory_levels.source_fidelity vs all members, FIDELITY_MIN) still decides accept/reject; `_fidelity_vs_shown`
# is a refinery-local second grade (whole-word match, exactly the lines the writer saw) logged next to it in
# data/refinery_shadow.jsonl as `fidelity_shown` / `would_accept_shown`. shown_grade_status() is its reader: after
# SHOWN_GRADE_REVIEW_N live records it reports how many ACCEPTED insights the new grade would have rejected, split
# by cluster size. Nothing is withheld, lowered or demoted on the new grade. memory_levels.source_fidelity is untouched
# (it has other callers: memory_levels gisting, journal_grounding_shadow, the recall anchor).
SHOWN_MEMBER_CHARS = 220          # per-member cut in the distil prompt (== FAITH_MEMBER_CHARS; a test pins both to the prompt)
SHOWN_PRIOR_CHARS = 400           # prior-insight cut in the distil prompt
SHOWN_GRADE_REVIEW_N = 20         # J-3066: live records carrying the new field before the would-reject report is read
SHOWN_GRADE_BUCKETS = ((4, 8), (9, 20), (21, 100), (101, None))   # F-3773's size split
# J-3066: when a live evolve overwrites a standing insight, the OLD text is appended here so history is recoverable.
_HISTORY_LOG = _ROOT / "data" / "refinery_history.jsonl"


def _shown_line(text) -> str:
    """The member text exactly as the distil prompt shows it (whitespace collapsed, cut)."""
    return " ".join(str(text or "").split())[:SHOWN_MEMBER_CHARS]


def _fidelity_vs_shown(insight: str, shown: list, prior_text=None):
    """Whole-word fraction of the insight's salient words found in the members the writer was SHOWN (J-3066).

    Same salient-word rule as memory_levels.source_fidelity (lowercase, >4 chars, not in _STOP) but (a) the pool is
    only the lines the prompt showed (MAX_MEMBERS_IN_PROMPT of them, each cut), so the pool, and with it the pass
    rate, no longer grows with cluster size, and (b) a word counts only as a WHOLE word, not as a substring of a
    longer one ('plan' no longer passes on 'planetary'). prior_text (the standing insight the writer also saw, cut to
    SHOWN_PRIOR_CHARS) is added to the pool when given, for the evolving case. None on any failure; 1.0 when the
    insight has no salient words (same as source_fidelity)."""
    try:
        import re
        from core.memory_levels import _norm, _STOP
        pool = [_shown_line(t) for t in (shown or [])]
        if prior_text:
            pool.append(" ".join(str(prior_text).split())[:SHOWN_PRIOR_CHARS])
        have = {w for w in re.split(r"[^a-z0-9]+", _norm(" \n ".join(pool))) if w}
        words = {w for w in re.split(r"[^a-z0-9]+", _norm(insight)) if len(w) > 4 and w not in _STOP}
        if not words:
            return 1.0
        return round(sum(1 for w in words if w in have) / len(words), 3)
    except Exception as exc:
        logger.debug("[refinery] _fidelity_vs_shown failed (non-fatal): %s", exc)
        return None


def _size_bucket(n: int) -> str:
    for lo, hi in SHOWN_GRADE_BUCKETS:
        if n >= lo and (hi is None or n <= hi):
            return f"{lo}-{hi}" if hi else f"{lo}+"
    return f"<{SHOWN_GRADE_BUCKETS[0][0]}"


def shown_grade_status(path=None) -> dict:
    """READER for the shown-members grade (J-3066 phase 0): over records carrying `fidelity_shown`, how many
    ACCEPTED insights (old gate) the new grade would have rejected, overall and by cluster size. `review_ready` is
    True once SHOWN_GRADE_REVIEW_N records carry the field."""
    try:
        rows = [json.loads(l) for l in open(path or _SHADOW_LOG, encoding="utf-8") if l.strip()]
    except Exception:
        return {"records": 0, "review_ready": False}
    rows = [r for r in rows if isinstance(r.get("fidelity_shown"), (int, float))]
    acc = [r for r in rows if r.get("accepted")]
    wr = [r for r in acc if not r.get("would_accept_shown")]
    by = {}
    for r in acc:
        b = by.setdefault(_size_bucket(int(r.get("members") or 0)), {"accepted": 0, "would_reject": 0})
        b["accepted"] += 1
        b["would_reject"] += 0 if r.get("would_accept_shown") else 1
    for b in by.values():
        b["would_reject_rate"] = round(b["would_reject"] / b["accepted"], 3) if b["accepted"] else None
    return {"records": len(rows), "accepted": len(acc), "would_reject": len(wr),
            "would_reject_rate": round(len(wr) / len(acc), 3) if acc else None, "by_cluster_size": by,
            "review_ready": len(rows) >= SHOWN_GRADE_REVIEW_N, "review_n": SHOWN_GRADE_REVIEW_N}


def insight_history(fragment_id, path=None) -> list:
    """READER for data/refinery_history.jsonl (J-3066): every earlier text of one standing insight, oldest first."""
    try:
        rows = [json.loads(l) for l in open(path or _HISTORY_LOG, encoding="utf-8") if l.strip()]
    except Exception:
        return []
    return [r for r in rows if r.get("fragment_id") == fragment_id]


def _log_history(row: dict) -> None:
    try:
        _HISTORY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_HISTORY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass

_FAITH_SYSTEM = (
    "You are a strict checker for a memory system. You are given a SHORT TEXT, written in the first person, "
    "and the numbered NOTES it was written from. Decide whether the TEXT is faithful to the NOTES: each main "
    "claim in it can be found in, or follows directly from, what the notes say, and it adds no event, feeling, "
    "belief or theme that none of the notes contain. Judge only against the notes, never against what is true "
    "in the world. Answer false if the text states something no note supports, or rests on a single note that "
    "the others do not back, or presents notes that disagree as if they agreed. "
    "Output ONLY JSON: {\"supported\": true or false, \"why\": \"one short sentence\"}"
)


async def _judge_faithfulness(insight: str, shown: list, prior_text, members_total: int) -> dict:
    """One yes/no faithfulness call on judge_panel's JUDGE_1 hub. Never raises; returns the row fields."""
    out = {"supported": None, "why": None, "err": None, "elapsed_s": None, "hub": None,
           "members_total": members_total, "members_judged": len(shown),
           "member_chars_cap": FAITH_MEMBER_CHARS, "prior_included": bool(prior_text)}
    try:
        import aiohttp
        from core import judge_panel as _jp
        url = _jp.JUDGE_1
        out["hub"] = url.rsplit(":", 1)[-1]
        user = ""
        if prior_text:
            user += ("EARLIER STANDING INSIGHT (the text may build on it):\n  "
                     f"{' '.join(str(prior_text).split())[:FAITH_PRIOR_CHARS]}\n\n")
        user += "NOTES:\n" + "\n".join(
            f"  {i}. {' '.join(t.split())[:FAITH_MEMBER_CHARS]}" for i, t in enumerate(shown, 1))
        user += f"\n\nTEXT:\n  {' '.join(insight.split())}\n\nIs the TEXT faithful to the NOTES?"
        async with aiohttp.ClientSession() as session:
            v, why, err, el = await _jp._ask(session, url, _FAITH_SYSTEM, user, "supported",
                                             timeout=FAITH_TIMEOUT, num_predict=FAITH_NUM_PREDICT)
        out.update(supported=v, why=(why[:240] if why else None), err=err, elapsed_s=el)
    except Exception as exc:
        out["err"] = "exception"
        logger.debug("[refinery] faithfulness judge failed: %s", exc)
    return out


def _log_faithfulness(faith: dict, fragment_id, insight: str, rec: dict, live: bool) -> None:
    """Store the verdict BESIDE the insight: one row per insight written, keyed by its fragment_id."""
    try:
        row = {"ts": rec["ts"], "fragment_id": fragment_id, "live": live, "mode": "log_only",
               "evolving": rec["evolving"], "prior_insight": rec["prior_insight"], "fidelity": rec["fidelity"],
               "insight": insight[:300], **faith}
        _FAITH_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_FAITH_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def faithfulness_status(path=None) -> dict:
    """READER for the faithfulness log (D-0627 phase 1): judged count, pass rate, and whether the 60-insight
    review point is reached. judged = rows with a real yes/no; errors = rows where the judge gave none."""
    try:
        rows = [json.loads(l) for l in open(path or _FAITH_LOG, encoding="utf-8") if l.strip()]
    except Exception:
        return {"rows": 0, "judged": 0, "phase1_complete": False}
    judged = [r for r in rows if isinstance(r.get("supported"), bool)]
    passed = sum(1 for r in judged if r["supported"])
    rate = round(passed / len(judged), 3) if judged else None
    return {"rows": len(rows), "judged": len(judged), "errors": len(rows) - len(judged), "passed": passed,
            "pass_rate": rate, "phase1_complete": len(judged) >= FAITH_PHASE1_N,
            "no_information": (rate is not None and len(judged) >= FAITH_PHASE1_N
                               and (rate > 0.95 or rate < 0.20))}


def _active_syntheses(conn) -> list:
    """RAW GOODS IN: every synthesis not yet manufactured into a standing insight.

    J-2274 (D-0453 gate, 2026-10-17): "not yet manufactured" is now asked of the refinery's OWN marker
    -- the `distilled_from` link this station (and memory_levels.commit_gist) writes for every member
    it distils -- instead of `cold=0`. `cold` is written by four different stations (this one, the gist
    cold-wall, dream_fade, prune_episodic), so reading it as "unrefined" conflated them: a synthesis the
    prune demoted would have vanished from this station unrefined (the starvation class behind
    prune_episodic's protected-origin list, F-2964), and a synthesis memory_lint re-warmed looked raw
    again. Verified on a 2026-10-17 .backup() copy: 375 -> 372 rows. The 3 "lost" rows are
    2026-06-20 syntheses whose first distilled_from parent (424ee88c) no longer exists, so memory_lint
    re-warmed them every sleep and this station re-distilled them every night since 2026-08-20 (31, 13
    and 4 standing insights minted from the same three rows) -- excluding them is the fix, not a loss.
    A synthetic cold=1 unlinked synthesis becomes reachable."""
    return conn.execute(
        "SELECT fragment_id, content, timestamp, embedding FROM memory_fragments "
        "WHERE origin='subconscious_synthesis' AND embedding IS NOT NULL "
        "AND fragment_id NOT IN (SELECT child_id FROM memory_links WHERE link_type='distilled_from') "
        "ORDER BY timestamp").fetchall()


def _standing_insights(conn) -> list:
    return conn.execute(
        "SELECT fragment_id, content, embedding FROM memory_fragments "
        "WHERE origin='standing_insight'").fetchall()


def _greedy_clusters(rows) -> list[list]:
    """Simple embedding-greedy clustering, newest-seeded (recent themes refine first)."""
    import numpy as np
    from core.memory.store import _blob_to_vec, _cosine
    items = [(r, _blob_to_vec(r["embedding"])) for r in rows]
    unused = list(reversed(items))          # newest first
    clusters = []
    while unused:
        seed_row, seed_vec = unused.pop(0)
        members = [(seed_row, seed_vec)]
        rest = []
        for row, vec in unused:
            if _cosine(seed_vec, vec) >= CLUSTER_SIM:
                members.append((row, vec))
            else:
                rest.append((row, vec))
        unused = rest
        if len(members) >= MIN_CLUSTER:
            clusters.append(members)
    return clusters


async def refine(call_json, base_urls) -> dict:
    """One refinery run (sleep-batch). Shadow unless REFINERY_LIVE. Returns run stats."""
    import sqlite3
    import numpy as np
    from core.memory.store import DB_PATH, _embed, _blob_to_vec, _cosine
    from core.memory_levels import source_fidelity
    t0 = time.time()
    stats = {"clusters": 0, "minted": 0, "evolved": 0, "cooled": 0, "rejected": 0,
             "live": REFINERY_LIVE}
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            raw = _active_syntheses(conn)
            insights = _standing_insights(conn)
        if len(raw) < MIN_CLUSTER:
            return stats
        all_clusters = _greedy_clusters(raw)
        ins_vecs = [(i["fragment_id"], i["content"], _blob_to_vec(i["embedding"]))
                    for i in insights if i["embedding"]]

        _judge_down = False   # D-0627: set when the faithfulness hub times out / refuses, for the rest of this run
        members_budget = 0    # running total of members about to be cooled THIS run (see cap comment above)
        clusters = []
        for members in all_clusters:
            if len(clusters) >= MAX_CLUSTERS_PER_RUN:
                break
            if clusters and members_budget >= MAX_MEMBERS_COOLED_PER_RUN:
                break          # budget met — always process at least the first cluster (soft cap)
            clusters.append(members)
            members_budget += len(members)
        stats["clusters"] = len(clusters)
        stats["skipped_clusters"] = len(all_clusters) - len(clusters)   # honest count of what's left for later runs

        for members in clusters:
            rows = [m[0] for m in members]
            centroid = np.mean([m[1] for m in members], axis=0)
            # does a standing insight already hold this theme?
            match = None
            for fid, content, vec in ins_vecs:
                if vec is not None and _cosine(centroid, vec) >= INSIGHT_MATCH_SIM:
                    match = (fid, content)
                    break
            member_texts = [r["content"] or "" for r in rows]
            shown = member_texts[:MAX_MEMBERS_IN_PROMPT]   # J-3821/D-0725: members are newest-first, so [:N] IS the newest N
            user = ""
            if match:
                user += f"THE STANDING INSIGHT HE ALREADY HOLDS HERE:\n  {match[1][:400]}\n\n"
            user += ("HIS RECURRING SELF-OBSERVATIONS ON THIS THEME"
                     f" ({len(member_texts)} total, newest shown):\n"
                     + "\n".join(f"  - {' '.join(t.split())[:220]}" for t in shown)
                     + "\n\nDistil the standing insight now.")
            try:
                data = await call_json(base_urls, _SYSTEM, user,
                                       max_tokens=220, temperature=0.4)
                insight = str(data.get("insight", "")).strip()
            except Exception as exc:
                logger.debug("[refinery] distill call failed: %s", exc)
                continue
            if not insight:
                continue
            # DECOUPLED QUALITY GATE — deterministic fidelity against the full member set
            fidelity = source_fidelity(insight, member_texts)
            verdict = fidelity >= FIDELITY_MIN
            # D-0627 phase 1 (LOG-ONLY): a cross-family judge grades an insight that WILL be written; the write
            # below is unchanged whatever it says. After a timeout/http failure no more judge calls this run.
            faith = None
            if verdict and FAITHFULNESS_JUDGE_ON and not _judge_down:
                faith = await _judge_faithfulness(insight, shown, match[1] if match else None, len(member_texts))
                if faith.get("err") in ("timeout", "http"):
                    _judge_down = True
            # J-3066 phase 0 (SHADOW): the same insight graded against exactly the lines the writer was shown.
            # It decides nothing; `accepted` below is still the old gate's verdict.
            fid_shown = _fidelity_vs_shown(insight, shown)
            fid_shown_prior = _fidelity_vs_shown(insight, shown, match[1]) if match else None
            rec = {"ts": round(t0, 1), "members": len(rows), "evolving": bool(match),
                   "fidelity": round(fidelity, 3), "accepted": verdict,
                   "fidelity_shown": fid_shown, "would_accept_shown": (fid_shown is not None and fid_shown >= FIDELITY_MIN),
                   "fidelity_shown_prior": fid_shown_prior, "members_shown": len(shown),
                   "faithful": (faith or {}).get("supported"),
                   "insight": insight[:300],
                   "member_ids": [r["fragment_id"] for r in rows][:40],
                   "prior_insight": (match[0] if match else None)}
            try:
                _SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
                with open(_SHADOW_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception:
                pass
            if not verdict:
                stats["rejected"] += 1
                continue
            if not REFINERY_LIVE:
                stats["minted" if not match else "evolved"] += 1   # what WOULD have happened
                if faith:
                    _log_faithfulness(faith, None, insight, rec, False)
                continue
            # ---- LIVE: mint/evolve + link + cool ------------------------------------------
            from core.memory.store import _connect, _vec_to_blob
            from core.memory.content_hash import content_hash as _content_hash, has_hash_column as _has_hash_column  # J-3395
            member_ids = [r["fragment_id"] for r in rows]
            history_row = None
            ivec = _embed(insight)
            with _connect() as conn:
                if match:
                    prior = conn.execute("SELECT derived_from, content FROM memory_fragments "
                                         "WHERE fragment_id=?", (match[0],)).fetchone()
                    # J-3066: the text about to be overwritten (read from the DB, not the run-start copy, so a second
                    # evolve of the same insight in one run still records the true previous text).
                    history_row = {"ts": round(time.time(), 1), "fragment_id": match[0],
                                   "old_content": (prior["content"] if prior else match[1]),
                                   "new_content": insight, "members_added": len(rows),
                                   "fidelity": rec["fidelity"], "fidelity_shown": rec["fidelity_shown"]}
                    try:
                        lineage = list(json.loads(prior["derived_from"] or "[]"))
                    except Exception:
                        lineage = []
                    lineage = list(dict.fromkeys(lineage + member_ids))
                    # J-3395 / F-4019: re-stamp content_hash with the evolved insight text (same statement);
                    # only where the J-3266 column exists.
                    if _has_hash_column(conn):
                        conn.execute(
                            "UPDATE memory_fragments SET content=?, embedding=?, timestamp=?, "
                            "derived_from=?, content_hash=? WHERE fragment_id=?",
                            (insight, _vec_to_blob(ivec) if ivec is not None else None,
                             time.time(), json.dumps(lineage), _content_hash(insight), match[0]))
                    else:
                        conn.execute(
                            "UPDATE memory_fragments SET content=?, embedding=?, timestamp=?, "
                            "derived_from=? WHERE fragment_id=?",
                            (insight, _vec_to_blob(ivec) if ivec is not None else None,
                             time.time(), json.dumps(lineage), match[0]))
                    parent_id = match[0]
                    stats["evolved"] += 1
                else:
                    parent_id = str(uuid.uuid4())
                    # J-3395 / F-4019: stamp content_hash on the minted row (was left NULL); only where the column exists.
                    if _has_hash_column(conn):
                        conn.execute(
                            "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, "
                            "importance, timestamp, keywords, embedding, origin, derived_from, "
                            "abstraction_level, content_hash) VALUES (?, ?, 'archive', 0.85, 0.9, ?, ?, ?, "
                            "'standing_insight', ?, 2, ?)",
                            (parent_id, insight, time.time(), "standing insight self_model",
                             _vec_to_blob(ivec) if ivec is not None else None,
                             json.dumps(member_ids), _content_hash(insight)))
                    else:
                        conn.execute(
                            "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, "
                            "importance, timestamp, keywords, embedding, origin, derived_from, "
                            "abstraction_level) VALUES (?, ?, 'archive', 0.85, 0.9, ?, ?, ?, "
                            "'standing_insight', ?, 2)",
                            (parent_id, insight, time.time(), "standing insight self_model",
                             _vec_to_blob(ivec) if ivec is not None else None,
                             json.dumps(member_ids)))
                    stats["minted"] += 1
                for mid in member_ids:
                    conn.execute("INSERT OR IGNORE INTO memory_links "
                                 "(parent_id, child_id, link_type, weight, created) "
                                 "VALUES (?,?,?,?,?)",
                                 (parent_id, mid, "distilled_from", 1.0, time.time()))
                ph = ",".join("?" * len(member_ids))
                # protected=0 AND abstraction_level=0 guard (2026-08-20): the equivalent cooling UPDATE in
                # memory_levels.py:180 carries it; this one didn't — constrained only by the source query's
                # origin filter, one query-drift away from cooling a protected or already-abstracted row.
                # kind IN COOLING_ELIGIBLE_KINDS guard (2026-09-02, D-0116/J-0475): same class of gap,
                # closed the same way — the statement now states its own eligibility criterion instead of
                # trusting _active_syntheses()'s origin filter to imply it. No observable change today.
                kind_ph = ",".join("?" * len(COOLING_ELIGIBLE_KINDS))
                conn.execute(
                    f"UPDATE memory_fragments SET cold=1 "
                    f"WHERE fragment_id IN ({ph}) AND protected=0 AND abstraction_level=0 "
                    f"AND kind IN ({kind_ph})",
                    list(member_ids) + list(COOLING_ELIGIBLE_KINDS),
                )
                conn.commit()
            if history_row:
                _log_history(history_row)       # after the commit: only a write that landed leaves a history row
            stats["cooled"] += len(member_ids)
            if faith:
                _log_faithfulness(faith, parent_id, insight, rec, True)
        logger.info("[refinery] %s run: %d clusters, %d minted, %d evolved, %d cooled, "
                    "%d rejected (%.0fs)", "LIVE" if REFINERY_LIVE else "SHADOW",
                    stats["clusters"], stats["minted"], stats["evolved"], stats["cooled"],
                    stats["rejected"], time.time() - t0)
        return stats
    except Exception as exc:
        logger.debug("[refinery] run failed (non-fatal): %s", exc)
        return stats


def status() -> dict:
    try:
        rows = [json.loads(l) for l in open(_SHADOW_LOG, encoding="utf-8") if l.strip()][-100:]
        if not rows:
            return {"runs": 0}
        acc = [r for r in rows if r.get("accepted")]
        return {"recent_records": len(rows), "accept_rate": round(len(acc) / len(rows), 2),
                "mean_fidelity": round(sum(r.get("fidelity", 0) for r in rows) / len(rows), 3),
                "live": REFINERY_LIVE, "faithfulness": faithfulness_status(),
                "shown_grade": shown_grade_status()}
    except Exception:
        return {"runs": 0}
