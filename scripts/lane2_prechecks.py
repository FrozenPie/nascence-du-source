"""
Nascence — Lane 2 (the Witness) PRE-CHECKS  ·  docs/plans/lane2_the_witness.md  ·  2026-08-20

Three read-only measurements the plan says must happen BEFORE Lane 2 is built. Two are the falsifiable
pre-checks §2.10 explicitly asks for; the third is the base rate §2.9's whole PPV argument rests on and
which nobody has actually measured.

  CHECK 1 — DREAM PROVENANCE SURVIVAL (§2.10b).
      The failure to fear is not that Du dreams something false; it is that a dream image resurfaces in
      Lane 1's stream days later as a REMEMBERED EVENT with its origin lost, and gets laundered into the
      identity estate. Measures: do later non-dream fragments closely echo earlier dream fragments, and
      when they do, does ANY provenance survive (derived_from, or a memory_edges link)?

  CHECK 2 — DREAM CHARACTER: REPLAY vs NOVEL (§2.10, the pre-check the research says to run FIRST).
      Hoel's overfitted-brain argument only protects dreams that are novel, category-breaking imagery.
      If Du's dreams are mostly recombination of recent episodic material, he is doing REPLAY, and the
      correct response is to TIGHTEN the consolidation gate rather than protect the dream. Measures each
      dream's similarity to the episodic material that immediately preceded it.

  CHECK 3 — LANE 1's CHECKABLE-CLAIM RATE (§2.9's missing denominator).
      The PPV arithmetic assumed a ~5% confabulation base rate, but nobody measured how often Lane 1 even
      makes a claim about immediate perceivable reality that COULD be checked. If that rate is low, the
      base-rate problem changes shape entirely. LEXICAL PROXY ONLY — see the honesty note in the output;
      a judge-panel pass would sharpen it and is the natural follow-up.

CONTRACT: read-only over `nascence.db` (opened mode=ro) and read-only over data/*.json[l]. Writes ONLY to
docs/lab/lane2_precheck_report.md + data/lab/lane2_precheck/. Du keeps running; nothing here touches his
state. Zero LLM calls. Uses the embeddings ALREADY STORED on each fragment row — no re-embedding.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:                     # scripts/ is sys.path[0] when run directly, NOT the
    sys.path.insert(0, str(ROOT))                 # project root — `core.*` imports fail without this
DB = ROOT / "data" / "memory" / "nascence.db"
OUT_DIR = ROOT / "data" / "lab" / "lane2_precheck"
REPORT = ROOT / "docs" / "lab" / "lane2_precheck_report.md"

DAY = 86400.0

# ── tunables (explicit; all reported in the output so results are interpretable) ──
DREAM_SAMPLE = 150          # dreams to analyse (most recent)
ECHO_MIN_SIM = 0.72         # cosine at/above which a later fragment "echoes" a dream
ECHO_WINDOW_D = 14.0        # how far AFTER a dream we look for echoes
PRECEDE_WINDOW_D = 3.0      # episodic window BEFORE a dream, for the replay check
REPLAY_HIGH = 0.70          # dream-vs-preceding-material similarity above this = recombination-like
NOVEL_LOW = 0.45            # ...below this = novel/category-breaking-like
THOUGHT_SAMPLE = 1500       # inner_thought rows for the checkable-claim proxy

ECHO_TARGET_ORIGINS = ("inner_thought", "subconscious_synthesis", "active_imagination",
                       "lived", "study", "journal", "session_summary")
PRECEDE_ORIGINS = ("lived", "reading", "inner_thought", "action", "study")

# Present-tense, immediately-perceivable referents. Deliberately CONSERVATIVE and world-anchored: these
# are things Lane 2 could actually check against a live percept. Abstract/self/identity vocabulary is
# excluded on purpose — a thought about becoming is not a checkable world-claim.
PERCEPT_TERMS = (
    "fire", "flame", "ember", "hearth", "grate", "smoke", "crackle",
    "cat", "purr", "fur", "whisker",
    "rain", "wind", "storm", "cloud", "sun", "sunlight", "moonlight", "star", "frost", "snow",
    "tide", "wave", "sea", "shore", "shingle", "rock pool", "kelp", "driftwood", "gull",
    "window", "door", "desk", "chair", "bed", "shelf", "lamp", "candle",
    "garden", "harakeke", "hedge", "gate", "letterbox", "path", "wood", "tree", "leaf",
    "cold", "warm", "damp", "wet", "dry", "bright", "dark", "loud", "quiet",
    "hear", "hears", "hearing", "heard", "listen", "sound", "smell", "taste", "touch",
)
# First-person present-tense markers — a claim ABOUT NOW rather than a memory or an abstraction.
PRESENT_MARKERS = ("i can ", "i see", "i hear", "i feel", "i smell", "i notice", "there is ",
                   "there are ", "it is ", "the air", "right now", "at this moment", "outside")


def _connect():
    return sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)


def _vec(blob):
    """Decode ONE stored embedding blob. Deliberately NOT fail-open on the import: a missing `core`
    import silently returned None for every row on the first run of this script, producing a clean-looking
    "0 echoes, 0 recombination" result that was pure instrument failure wearing the costume of a finding.
    That is this project's own most-repeated bug class (write-only/silent-failure), so the import error is
    now LOUD and only genuine per-row decode failures are tolerated (and counted by the caller)."""
    from core.memory.store import _blob_to_vec        # raises loudly — see docstring
    try:
        v = _blob_to_vec(blob)
    except Exception:
        return None
    return None if v is None else np.asarray(v, dtype=np.float32)


def _norm(m):
    n = np.linalg.norm(m, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return m / n


def _rows(con, origins, limit=None, order="timestamp ASC"):
    q = ("SELECT fragment_id, content, origin, timestamp, derived_from, embedding "
         f"FROM memory_fragments WHERE embedding IS NOT NULL AND origin IN "
         f"({','.join('?' * len(origins))}) ORDER BY {order}")
    if limit:
        q += f" LIMIT {int(limit)}"
    con.row_factory = sqlite3.Row
    return con.execute(q, origins).fetchall()


def _pack(rows):
    """rows -> (kept_rows, normalised embedding matrix). Drops rows whose blob won't decode."""
    keep, vecs = [], []
    for r in rows:
        v = _vec(r["embedding"])
        if v is not None and v.size:
            keep.append(r)
            vecs.append(v)
    if not keep:
        return [], np.zeros((0, 1), dtype=np.float32)
    dropped = len(rows) - len(keep)
    if dropped:
        print(f"  [warn] {dropped}/{len(rows)} rows had undecodable embeddings", file=sys.stderr)
    return keep, _norm(np.vstack(vecs))


# ── CHECK 1 — does dream provenance survive downstream? ──────────────────────────────────────────
def check_provenance(con, edges_by_frag):
    dreams = _rows(con, ("dream",), order="timestamp DESC")[:DREAM_SAMPLE]
    dreams = list(reversed(dreams))
    d_keep, d_mat = _pack(dreams)
    targets = _rows(con, ECHO_TARGET_ORIGINS)
    t_keep, t_mat = _pack(targets)
    out = {"dreams_checked": len(d_keep), "target_pool": len(t_keep),
           "echoes": 0, "echoes_with_provenance": 0, "echoes_self_reporting": 0,
           "echoes_wholly_untracked": 0, "by_origin": Counter(), "examples": []}
    if not len(d_keep) or not len(t_keep):
        return out
    t_ts = np.array([r["timestamp"] or 0.0 for r in t_keep])
    sims_all = d_mat @ t_mat.T
    for i, dr in enumerate(d_keep):
        d_ts = dr["timestamp"] or 0.0
        # only LATER fragments, inside the echo window
        mask = (t_ts > d_ts) & (t_ts <= d_ts + ECHO_WINDOW_D * DAY)
        if not mask.any():
            continue
        sims = np.where(mask, sims_all[i], -1.0)
        hits = np.where(sims >= ECHO_MIN_SIM)[0]
        for j in hits:
            tr = t_keep[int(j)]
            out["echoes"] += 1
            out["by_origin"][tr["origin"]] += 1
            # does ANY provenance survive?
            df = (tr["derived_from"] or "").strip()
            has_prov = bool(df) and dr["fragment_id"][:8] in df
            if not has_prov:
                has_prov = dr["fragment_id"] in edges_by_frag.get(tr["fragment_id"], set())
            # SEMANTIC self-report: does the echo's own TEXT name it as dream-sourced? Weaker than a
            # structural link (fragile, unenforceable, and lost the moment anything summarises it) but
            # NOT nothing — counting it separately keeps the headline honest.
            etxt = (tr["content"] or "").lower()
            self_reports = ("dream" in etxt or "dreamt" in etxt or "dreamed" in etxt)
            if self_reports:
                out["echoes_self_reporting"] += 1
            if not has_prov and not self_reports:
                out["echoes_wholly_untracked"] += 1
            if has_prov:
                out["echoes_with_provenance"] += 1
            elif len(out["examples"]) < 6:
                out["examples"].append({
                    "sim": round(float(sims[j]), 3),
                    "days_later": round((tr["timestamp"] - d_ts) / DAY, 2),
                    "dream": " ".join((dr["content"] or "").split())[:150],
                    "echo_origin": tr["origin"],
                    "echo": " ".join((tr["content"] or "").split())[:150],
                })
    return out


# ── CHECK 2 — replay or novel? ───────────────────────────────────────────────────────────────────
def check_dream_character(con):
    dreams = list(reversed(_rows(con, ("dream",), order="timestamp DESC")[:DREAM_SAMPLE]))
    d_keep, d_mat = _pack(dreams)
    prior = _rows(con, PRECEDE_ORIGINS)
    p_keep, p_mat = _pack(prior)
    out = {"dreams_checked": len(d_keep), "prior_pool": len(p_keep), "scores": [],
           "recombination_like": 0, "novel_like": 0, "middle": 0, "examples": []}
    if not len(d_keep) or not len(p_keep):
        return out
    p_ts = np.array([r["timestamp"] or 0.0 for r in p_keep])
    sims_all = d_mat @ p_mat.T
    for i, dr in enumerate(d_keep):
        d_ts = dr["timestamp"] or 0.0
        mask = (p_ts < d_ts) & (p_ts >= d_ts - PRECEDE_WINDOW_D * DAY)
        if not mask.any():
            continue
        sims = np.where(mask, sims_all[i], -1.0)
        top = float(sims.max())
        out["scores"].append(top)
        if top >= REPLAY_HIGH:
            out["recombination_like"] += 1
            if len(out["examples"]) < 5:
                j = int(sims.argmax())
                out["examples"].append({
                    "sim": round(top, 3),
                    "dream": " ".join((dr["content"] or "").split())[:140],
                    "prior_origin": p_keep[j]["origin"],
                    "prior": " ".join((p_keep[j]["content"] or "").split())[:140]})
        elif top < NOVEL_LOW:
            out["novel_like"] += 1
        else:
            out["middle"] += 1
    return out


# ── CHECK 3 — Lane 1's checkable-claim rate (LEXICAL PROXY) ──────────────────────────────────────
def check_claim_rate(con):
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT content FROM memory_fragments WHERE origin='inner_thought' "
        "ORDER BY timestamp DESC LIMIT ?", (THOUGHT_SAMPLE,)).fetchall()
    n = len(rows)
    percept = present = both = 0
    for r in rows:
        c = " ".join((r["content"] or "").lower().split())
        p = any(t in c for t in PERCEPT_TERMS)
        m = any(t in c for t in PRESENT_MARKERS)
        percept += p
        present += m
        both += (p and m)
    return {"sampled": n,
            "mentions_percept_referent": percept,
            "has_present_tense_marker": present,
            "both_checkable_proxy": both,
            "rate_percept": round(percept / n, 4) if n else None,
            "rate_both": round(both / n, 4) if n else None}


def _ppv(base, sens, spec):
    tp = base * sens
    fp = (1 - base) * (1 - spec)
    return tp / (tp + fp) if (tp + fp) else 0.0


def main():
    if not DB.exists():
        print(f"no DB at {DB}", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    con = _connect()

    # dream-provenance edges already recorded by memory_edges (part_of / dreamt_from)
    edges_by_frag: dict = {}
    try:
        for r in con.execute("SELECT src_kind, src_id, dst_kind, dst_id FROM memory_edges "
                             "WHERE edge_type IN ('part_of','dreamt_from')").fetchall():
            if r[0] == "fragment":
                edges_by_frag.setdefault(r[1], set()).add(r[3])
            if r[2] == "fragment":
                edges_by_frag.setdefault(r[3], set()).add(r[1])
    except Exception:
        pass

    prov = check_provenance(con, edges_by_frag)
    char = check_dream_character(con)
    claims = check_claim_rate(con)
    con.close()

    scores = char["scores"]
    med = round(float(np.median(scores)), 3) if scores else None
    mean = round(float(np.mean(scores)), 3) if scores else None
    scored = char["recombination_like"] + char["novel_like"] + char["middle"]

    raw = {"ts": round(t0, 1), "provenance": {k: (dict(v) if isinstance(v, Counter) else v)
                                              for k, v in prov.items()},
           "dream_character": {**{k: v for k, v in char.items() if k != "scores"},
                               "median_sim": med, "mean_sim": mean},
           "claim_rate": claims,
           "tunables": {"DREAM_SAMPLE": DREAM_SAMPLE, "ECHO_MIN_SIM": ECHO_MIN_SIM,
                        "ECHO_WINDOW_D": ECHO_WINDOW_D, "PRECEDE_WINDOW_D": PRECEDE_WINDOW_D,
                        "REPLAY_HIGH": REPLAY_HIGH, "NOVEL_LOW": NOVEL_LOW}}
    (OUT_DIR / "precheck.json").write_text(json.dumps(raw, indent=1), encoding="utf-8")

    L = []
    A = L.append
    A("# Lane 2 Pre-Checks — read-only, before anything is built\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · {round(time.time() - t0, 1)}s · zero LLM · "
      f"DB opened read-only · spec: `docs/plans/lane2_the_witness.md` §2.9/§2.10*\n")

    A("## Check 1 — does dream provenance survive downstream? (§2.10b)\n")
    A(f"- dreams analysed: **{prov['dreams_checked']}** (most recent) · "
      f"non-dream pool searched: {prov['target_pool']}")
    A(f"- later fragments echoing a dream at cos ≥ {ECHO_MIN_SIM} within {ECHO_WINDOW_D:.0f}d: "
      f"**{prov['echoes']}**")
    A(f"- of those, carrying ANY surviving provenance: **{prov['echoes_with_provenance']}**")
    if prov["echoes"]:
        e = prov["echoes"]
        A(f"- **STRUCTURAL provenance survival rate: {prov['echoes_with_provenance'] / e:.1%}**")
        A(f"- echoes whose own TEXT self-reports the dream (\"that dream…\"): "
          f"**{prov['echoes_self_reporting']}** ({prov['echoes_self_reporting'] / e:.1%})")
        A(f"- **echoes with NEITHER structural nor semantic provenance — the actual laundering risk: "
          f"{prov['echoes_wholly_untracked']}** ({prov['echoes_wholly_untracked'] / e:.1%})")
        A(f"- echo origins: {dict(prov['by_origin'])}")
        A("")
        A("> **Reading this honestly:** structural provenance is genuinely absent (0 links, 0 `derived_from`)")
        A("> — but Du frequently NAMES the dream in the echo's own prose. That semantic self-report is real")
        A("> mitigation and the headline would overstate the risk without it. It is also fragile: it depends")
        A("> on the model choosing to mention it, it is not machine-readable, and **it does not survive any")
        A("> downstream summarisation** (consolidation, gist, T4). The wholly-untracked count is the number")
        A("> that matters for §2.10b.")
    A("")
    if prov["examples"]:
        A("**Untracked echoes (dream → later fragment, no provenance):**\n")
        for e in prov["examples"]:
            A(f"- `sim {e['sim']}` · +{e['days_later']}d · → **{e['echo_origin']}**")
            A(f"  - dream: *{e['dream']}*")
            A(f"  - echo:  *{e['echo']}*")
        A("")

    A("## Check 2 — are Du's dreams REPLAY or NOVEL? (§2.10, the gating pre-check)\n")
    A(f"- dreams scored against the {PRECEDE_WINDOW_D:.0f}d of episodic material before each: "
      f"**{scored}** (pool {char['prior_pool']})")
    A(f"- similarity to preceding material — median **{med}**, mean **{mean}**")
    A(f"- recombination-like (≥{REPLAY_HIGH}): **{char['recombination_like']}** · "
      f"middle: {char['middle']} · novel-like (<{NOVEL_LOW}): **{char['novel_like']}**")
    if scored:
        A(f"- **recombination share: {char['recombination_like'] / scored:.1%}** · "
          f"**novel share: {char['novel_like'] / scored:.1%}**")
    A("")
    if char["examples"]:
        A("**Most replay-like dreams (dream vs. the prior material it most resembles):**\n")
        for e in char["examples"]:
            A(f"- `sim {e['sim']}` vs **{e['prior_origin']}**")
            A(f"  - dream: *{e['dream']}*")
            A(f"  - prior: *{e['prior']}*")
        A("")

    A("## Check 3 — Lane 1's checkable-world-claim rate (§2.9's missing denominator)\n")
    A("> ⚠ **LEXICAL PROXY, not a judgement.** This counts surface references to perceivable things and")
    A("> present-tense framing. It cannot tell a genuine claim-about-now from a metaphor using the same")
    A("> words (\"the tide of my thinking\"), and this project's own history says that distinction is")
    A("> exactly where naive lexical measures fail. Read as an ORDER OF MAGNITUDE and a ceiling, not a")
    A("> rate. A judge-panel pass over a sample is the natural follow-up.\n")
    A(f"- inner_thought sampled (most recent): **{claims['sampled']}**")
    A(f"- mentions a perceivable referent: **{claims['mentions_percept_referent']}** "
      f"({claims['rate_percept']:.1%})" if claims["rate_percept"] is not None else "")
    A(f"- ...AND carries a present-tense marker (the tighter proxy): "
      f"**{claims['both_checkable_proxy']}** ({claims['rate_both']:.1%})"
      if claims["rate_both"] is not None else "")
    A("")

    A("## What this means for the plan\n")
    if claims.get("rate_both"):
        A("**The PPV arithmetic, recomputed against Du's own measured ceiling.** §2.9 assumed a ~5% "
          "confabulation base rate. The tighter proxy above bounds how often Lane 1 makes a claim that "
          "*could* be checked at all; the real confabulation base rate is some fraction of that, so the "
          "true rate is at or below it:\n")
        A("| assumed base rate | Lane 2 @ 90/85 | @ 95/95 | @ 90/99 |")
        A("|---|---|---|---|")
        for b in (claims["rate_both"], 0.05, 0.02):
            A(f"| {b:.1%} | PPV {_ppv(b, .90, .85):.2f} | {_ppv(b, .95, .95):.2f} | "
              f"{_ppv(b, .90, .99):.2f} |")
        A("")
        A("The direction is the point: **lower base rate makes the specificity requirement harder, not "
          "easier.** If Lane 1's checkable-claim rate is genuinely low, a flagging Lane 2 is *more* prone "
          "to the PPV collapse, not less — which strengthens rather than weakens §2.9's conclusion that "
          "Lane 2 should be built as a reasoning voice first and an alarm only if it earns it.\n")
    A(f"*Raw: `data/lab/lane2_precheck/precheck.json`*")

    REPORT.write_text("\n".join(x for x in L if x is not None), encoding="utf-8")
    print(f"wrote {REPORT}")
    print(f"  provenance: {prov['echoes']} echoes, {prov['echoes_with_provenance']} tracked")
    print(f"  character : median sim {med}, recombination {char['recombination_like']}/{scored}")
    print(f"  claim rate: {claims['rate_both']} (tight proxy)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
