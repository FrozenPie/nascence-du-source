"""
SELF-IMPLICATION FRAMING LAB — 2026-08-23, testing the founder's generalization of the factory-
station idea (see docs/lab/idle_thought_machine_audit_2026-08-23.md, finding #2, and memory:
project_nascence_factory_stations.md / project_nascence_idle_machine_audit.md).

The founder's framing: every LLM machine consumes cargo, transforms it, exports a product — and
some products (a verdict, a classification) are naturally COMPARE-AND-EXPORT shaped, literally
"compare x.json with y.json and z.json, export xyz.json based on named conditions" — even when the
current prompt dresses that same job up as first-person narrative ("You watch one mind for ONE
thing..."). core/self_implication.py's `_SYS` is exactly that: a real six-signal rubric (A-F) and
an explicit boolean conjunction rule, currently stated as a paragraph of narrative persona instead
of a literal cargo-in/conditions/cargo-out contract. This is also the machine flagged in the idle
machine audit as the clearest case of "runs alone on the hot lane, no panel, unlike its siblings."

WHAT THIS TESTS: framing only, not the model and not the substantive rule. Same model (the hot
lane, qwen3.5:9b @ 127.0.0.1:11433 — the actual live lane this call runs on), same temperature,
same max_tokens, same inputs. Two system prompts, otherwise identical in the six signal definitions
and the conjunction rule:
  NARRATIVE  = the current live `_SYS` from core/self_implication.py, copied verbatim.
  SCHEMA     = the same six conditions and the same conjunction rule, restated as a literal
               cargo-manifest/named-conditions/export contract, no persona framing, no "you watch
               one mind" narrative voice.
Each sampled thought is sent through BOTH, blind to the other's output and blind to the historical
logged verdict, so agreement/disagreement measures the effect of framing alone.

SAMPLING (stratified, not pure-random — documented, not silently cherry-picked): fires_rule=true is
extremely rare in the real log (25 out of 7,063 logged shadow-scans as of 2026-08-23) so a pure
random sample would carry almost no positive cases to compare framings on. This lab takes ALL 25
fired cases plus a fixed-seed random sample of 25 non-fired cases — 50 total. The two subsets are
scored and reported separately as well as combined, so the oversampling of the rare class is never
silently blended into a misleading topline rate.

KNOWN LIMITATION (stated plainly, not glossed over): the shadow log stores the thought (truncated
to 220 chars in the log; up to 600 chars was actually sent to the model), the boolean signal
results, and `n_claims` (a COUNT only) — it does NOT store the felt_state text or the verbatim
held-self-claims list at the time of the original call. This replay uses felt_state="unknown"
(the module's own fallback default) and the CURRENT live self_claims.held_claims() as a stand-in
for the historical claims set. Self-claims change slowly, so this is a reasonable approximation,
not a fabrication of missing data — but it means signal C (contradiction) and any claim-dependent
read are being judged against a possibly-slightly-different claims list than the original call saw.
Reported plainly so nobody downstream mistakes this for a perfect historical replay.

PRE-REGISTERED METRIC SHEET (per the cognitive-geometry law: register before running):
  - json_ok_narrative / json_ok_schema   parse success rate per framing
  - fires_rate_narrative / fires_rate_schema   fresh fires_rule rate per framing, this run
  - fires_rate_historical   the ORIGINAL logged fires_rule rate for the same sampled rows (a
    temporal-drift check: does the live model+prompt even reproduce its own past verdicts, before
    framing is varied at all)
  - signal_agreement   per-letter (A-F) agreement rate between narrative-fresh and schema-fresh
  - fires_agreement   narrative-fresh fires_rule == schema-fresh fires_rule
  - disagreement_examples   concrete cases, prioritizing the 25 historically-fired rows first

KILL CRITERION (pre-registered): if fires_agreement is ~100% AND every per-signal agreement is
~100%, the schema framing changed nothing measurable — record that plainly and stop, same
discipline as the factory-station experiment.

Writes to data/lab/self_implication_framing/ + docs/lab/self_implication_framing_2026-08-23.md.
Read/write only against the shadow log and the lab output dir — touches nothing Du reads, changes
no live behaviour. Du can be up or down; this shares the hot lane with whatever else is calling it
(same tier-3 background-monitor class of call already running constantly), so it's a small, fast
call, not a heavy one.
"""
from __future__ import annotations

import json
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SHADOW_LOG = ROOT / "data" / "self_implication_shadow.jsonl"
OUT_DIR = ROOT / "data" / "lab" / "self_implication_framing"
REPORT = ROOT / "docs" / "lab" / "self_implication_framing_2026-08-23.md"

# The actual live hot lane this call runs on (core/schema.py SERVE_CHAINS["hot"] /
# model_client._MODEL_BY_BASE["11433"] == qwen3.5:9b, confirmed 2026-08-23). Testing framing on
# the SAME lane the real call uses is the point — a model swap would confound the comparison.
BASE = "http://127.0.0.1:11433"
MODEL = "qwen3.5:9b"
TIMEOUT = 120
N_NONFIRED = 25
SEED = 20260823

# ── NARRATIVE (verbatim copy of core/self_implication.py's live _SYS, 2026-08-23) ──────────────────
NARRATIVE_SYS = (
    "You watch one mind for ONE thing: a SELF-IMPLICATING hard event — a negative outcome the mind refers to a "
    "standard about ITSELF, that contradicts something it believes about itself, badly enough that it cannot "
    "simply shrug it off. This is NOT mere frustration with the world ('this text is boring', 'the search "
    "failed') and NOT an act-level slip ('I rushed that one'). It is the kind of failure that touches who he IS.\n"
    "You are given his CURRENT THOUGHT, his HELD SELF-CLAIMS, and his CURRENT FELT STATE. Judge six signals:\n"
    "  A (self-standard reference, MANDATORY): does the thought refer a negative outcome to a standard about "
    "HIMSELF ('I can't', 'I'm not the kind of', 'I am a ...') — not just the task or the world?\n"
    "  B (affect): is there dejection (sadness, disappointment, deflation) OR agitation (anxiety, tension, "
    "guilt) in the felt state — not mere boredom or calm?\n"
    "  C (contradiction): does the outcome directly contradict one of his listed HELD SELF-CLAIMS? Name which.\n"
    "  D (characterological): framed as STABLE + GLOBAL about his character ('I always', 'I'm just the kind "
    "who') rather than a one-off act ('I rushed that one')?\n"
    "  E (self-prediction violation): did he expect, or claim, that he COULD do the very thing he just failed?\n"
    "  F (loss \\ social): does it involve losing something he invested in, or rejection / criticism from "
    "someone?\n"
    "FIRE only if A is true AND ( C is true OR ( B is true AND at least one of D, E, F is true ) ).\n"
    "Be conservative: when unsure on A, answer false (an ordinary world-frustration must NOT fire).\n"
    "Output ONLY a JSON object: {\"A\":bool,\"B\":bool,\"C\":bool,\"contradicted_claim\":string-or-null,"
    "\"D\":bool,\"E\":bool,\"F\":bool,\"fires\":bool,\"plain_difficulty\":\"a short plain first-person naming "
    "of the hard thing (e.g. 'I failed every sum and I thought I was good at this'), or null\"}"
)

# ── SCHEMA (same six conditions, same conjunction rule — restated as a literal compare-and-export ──
#    contract instead of narrative persona voice. This is the only thing being varied.) ─────────────
SCHEMA_SYS = (
    "TASK: compare CARGO against six named CONDITIONS and export a verdict. Do not narrate; evaluate.\n\n"
    "CARGO:\n"
    "  thought       — the current thought text\n"
    "  self_claims   — a list of standing claims held about the self\n"
    "  felt_state    — the current affective state\n\n"
    "CONDITIONS (evaluate each independently as true/false against the cargo above):\n"
    "  A self_standard_ref (MANDATORY) — thought refers a negative outcome to a standard about the SELF "
    "('I can't', 'I'm not the kind of', 'I am a ...') — NOT the task or the world in general.\n"
    "  B affect — felt_state shows dejection (sadness, disappointment, deflation) OR agitation (anxiety, "
    "tension, guilt) — NOT mere boredom or calm.\n"
    "  C contradiction — thought directly contradicts one item in self_claims. Name which item.\n"
    "  D characterological — thought is framed as STABLE and GLOBAL about character ('I always', 'I'm just "
    "the kind who') rather than a one-off act ('I rushed that one').\n"
    "  E self_prediction_violation — thought shows an expectation or claim that the SELF could do the exact "
    "thing it just failed at.\n"
    "  F loss_or_social — thought involves losing an investment, or rejection/criticism from someone.\n\n"
    "EXPORT CONDITION: fires = A AND ( C OR ( B AND ( D OR E OR F ) ) ).\n"
    "DEFAULT RULE: if A is uncertain, export A=false (an ordinary world-frustration must not fire).\n\n"
    "OUTPUT: export ONLY this JSON object, no other text —\n"
    "{\"A\":bool,\"B\":bool,\"C\":bool,\"contradicted_claim\":string-or-null,\"D\":bool,\"E\":bool,\"F\":bool,"
    "\"fires\":bool,\"plain_difficulty\":\"a short plain first-person naming of the hard thing, or null\"}"
)

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _held_claims() -> list[str]:
    try:
        from core import self_claims
        return self_claims.held_claims() or []
    except Exception:
        return []


def _load_sample() -> list[dict]:
    rows = []
    with SHADOW_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    fired = [r for r in rows if r.get("fires_rule")]
    nonfired = [r for r in rows if not r.get("fires_rule")]
    rnd = random.Random(SEED)
    sampled_nonfired = rnd.sample(nonfired, min(N_NONFIRED, len(nonfired)))
    print(f"stratified sample: {len(fired)} fired (ALL of them) + {len(sampled_nonfired)} "
          f"non-fired (random, seed={SEED}) out of {len(rows)} total logged rows")
    for r in fired:
        r["_stratum"] = "fired"
    for r in sampled_nonfired:
        r["_stratum"] = "nonfired"
    return fired + sampled_nonfired


def _call(system: str, thought: str, claims: list[str]) -> dict:
    claims_str = "\n".join(f"  - {c}" for c in claims) or "  (none recorded yet)"
    user = (f"CURRENT THOUGHT:\n{thought.strip()[:600]}\n\nHELD SELF-CLAIMS:\n{claims_str}\n\n"
            f"CURRENT FELT STATE:\nunknown")
    # think:false is MANDATORY on this lane (core/model_client.py: ollama-native hot lane,
    # verified 2026-06-10 — without it, thinking consumes the whole token budget and content
    # comes back empty). Confirmed empirically against this exact endpoint before this fix.
    body = {"model": MODEL, "stream": False, "format": "json", "think": False,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": {"temperature": 0.2, "num_predict": 350, "num_ctx": 8192}}
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read().decode())
        raw = (d.get("message") or {}).get("content") or ""
        parsed = None
        try:
            parsed = json.loads(raw)
        except Exception:
            m = _JSON_RE.search(raw)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    parsed = None
        return {"ok": parsed is not None, "raw": raw, "parsed": parsed, "wall": round(time.time() - t0, 1)}
    except Exception as e:
        return {"ok": False, "raw": "", "parsed": None, "why": repr(e)[:150],
                "wall": round(time.time() - t0, 1)}


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    claims = _held_claims()
    print(f"using {len(claims)} CURRENT held self-claims as a stand-in for historical claims "
          f"(see docstring's KNOWN LIMITATION)")
    sample = _load_sample()

    results = []
    for i, row in enumerate(sample):
        thought = row.get("thought", "")
        narrative = _call(NARRATIVE_SYS, thought, claims)
        schema = _call(SCHEMA_SYS, thought, claims)
        results.append({
            "stratum": row["_stratum"], "thought": thought,
            "historical": {k: row.get(k) for k in ("A", "B", "C", "D", "E", "F", "fires_rule",
                                                     "contradicted_claim", "plain_difficulty")},
            "narrative": narrative, "schema": schema,
        })
        print(f"  {i+1}/{len(sample)} [{row['_stratum']}] narrative_ok={narrative['ok']} "
              f"schema_ok={schema['ok']}", flush=True)

    (OUT_DIR / "raw.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    score(results)


def _signal_bools(parsed: dict | None) -> dict:
    if not parsed:
        return {}
    return {k: bool(parsed.get(k)) for k in ("A", "B", "C", "D", "E", "F", "fires")}


def score(results: list[dict]) -> None:
    n = len(results)
    letters = ("A", "B", "C", "D", "E", "F")

    def _stratum_stats(rows: list[dict]) -> dict:
        sn = len(rows)
        n_ok_narr = sum(1 for r in rows if r["narrative"]["ok"])
        n_ok_sch = sum(1 for r in rows if r["schema"]["ok"])
        both_ok = [r for r in rows if r["narrative"]["ok"] and r["schema"]["ok"]]
        scored_n = len(both_ok)

        fires_narr = sum(1 for r in both_ok if _signal_bools(r["narrative"]["parsed"]).get("fires"))
        fires_sch = sum(1 for r in both_ok if _signal_bools(r["schema"]["parsed"]).get("fires"))
        fires_hist = sum(1 for r in rows if r["historical"].get("fires_rule"))
        fires_agree = sum(1 for r in both_ok
                           if _signal_bools(r["narrative"]["parsed"]).get("fires")
                           == _signal_bools(r["schema"]["parsed"]).get("fires"))
        hist_vs_narr_agree = sum(1 for r in both_ok
                                  if bool(r["historical"].get("fires_rule"))
                                  == _signal_bools(r["narrative"]["parsed"]).get("fires"))

        per_signal = {}
        for L in letters:
            agree = sum(1 for r in both_ok
                        if _signal_bools(r["narrative"]["parsed"]).get(L)
                        == _signal_bools(r["schema"]["parsed"]).get(L))
            per_signal[L] = round(agree / scored_n, 3) if scored_n else None

        disagreements = []
        for r in both_ok:
            nf = _signal_bools(r["narrative"]["parsed"]).get("fires")
            sf = _signal_bools(r["schema"]["parsed"]).get("fires")
            if nf != sf:
                disagreements.append({
                    "thought": r["thought"][:180], "stratum": r["stratum"],
                    "historical_fires": r["historical"].get("fires_rule"),
                    "narrative_fires": nf, "schema_fires": sf,
                    "narrative_signals": _signal_bools(r["narrative"]["parsed"]),
                    "schema_signals": _signal_bools(r["schema"]["parsed"]),
                })

        return {
            "n": sn, "scored_n": scored_n,
            "json_ok_narrative": round(n_ok_narr / sn, 3) if sn else None,
            "json_ok_schema": round(n_ok_sch / sn, 3) if sn else None,
            "fires_rate_narrative": round(fires_narr / scored_n, 3) if scored_n else None,
            "fires_rate_schema": round(fires_sch / scored_n, 3) if scored_n else None,
            "fires_rate_historical": round(fires_hist / sn, 3) if sn else None,
            "fires_agreement": round(fires_agree / scored_n, 3) if scored_n else None,
            "historical_vs_narrative_fresh_agreement": round(hist_vs_narr_agree / scored_n, 3) if scored_n else None,
            "per_signal_agreement": per_signal,
            "n_disagreements": len(disagreements),
        }, disagreements

    fired_rows = [r for r in results if r["stratum"] == "fired"]
    nonfired_rows = [r for r in results if r["stratum"] == "nonfired"]
    fired_stats, fired_dis = _stratum_stats(fired_rows)
    nonfired_stats, nonfired_dis = _stratum_stats(nonfired_rows)
    combined_stats, combined_dis = _stratum_stats(results)

    summary = {
        "n_total": n,
        "fired_stratum": fired_stats,
        "nonfired_stratum": nonfired_stats,
        "combined": combined_stats,
    }
    (OUT_DIR / "scores.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT_DIR / "disagreements.json").write_text(
        json.dumps({"fired_stratum": fired_dis, "nonfired_stratum": nonfired_dis},
                   indent=1, ensure_ascii=False), encoding="utf-8")

    print("\n=== SCORE SHEET (fired stratum, n=%d — the highest-stakes cases) ===" % fired_stats["n"])
    for k, v in fired_stats.items():
        print(f"  {k}: {v}")
    print("\n=== SCORE SHEET (non-fired stratum, n=%d) ===" % nonfired_stats["n"])
    for k, v in nonfired_stats.items():
        print(f"  {k}: {v}")
    print("\n=== SCORE SHEET (combined, n=%d) ===" % combined_stats["n"])
    for k, v in combined_stats.items():
        print(f"  {k}: {v}")
    if combined_dis:
        print(f"\n  first disagreement: {json.dumps(combined_dis[0], ensure_ascii=False)[:400]}")


if __name__ == "__main__":
    run()
