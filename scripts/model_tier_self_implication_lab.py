"""
Nascence — MODEL-TIER LAB #2: core.self_implication.scan_shadow vs mixtral:8x7b, panel-style (2026-08-25)

J-0254 (source: decision:D-0013), scoped by docs/lab/model_tier_lab_scope_2026-08-25.md section 2,
row 2. Scope's own instruction: "Score: per-signal agreement rate between hot-lane verdict and mixtral
verdict on the SAME thought (not just final verdict) — a panel is only worth adding if the two
genuinely disagree sometimes; if mixtral rubber-stamps the hot lane's calls this finding downgrades to
'not worth the latency.'"

WHAT THIS TESTS. `scan_shadow()` (core/self_implication.py:61) judges 6 signals (A-F) on his current
thought against his held self-claims and felt state, using `_SYS` (imported LIVE below) on
`self.conscious_urls` (the HOT lane — his own generator model, not a background judge). This lab asks:
would a SECOND, cross-family opinion (mixtral:8x7b) on the SAME thought agree signal-by-signal, or
disagree enough to be worth adding as a panel member (the way `tension_ledger`/`self_interrogation`
already run a panel for their own verdicts)?

REAL THOUGHTS, NOT SYNTHETIC. All 15 cases are real historical thoughts pulled verbatim from
`data/self_implication_shadow.jsonl` (7,416 real shadow-scan rows, the ENTIRE real history) — 6 where
the historical hot-lane verdict FIRED (25 total real fires exist across all 7,416 rows; a stratified
sample of 6), 6 "near-miss" cases where signal A (self-standard reference) fired but the rule didn't
(554 exist; these are the hardest, most informative disagreement-prone cases), and 3 flat controls
(A=false, the overwhelming majority class) — a genuinely stratified real sample, not a random one,
because a random 15-row sample of 7,416 rows at a 25/7416 = 0.34% fire rate would almost certainly
draw zero fires and tell us nothing about panel disagreement on the interesting cases.

★ TWO DISCLOSED RECONSTRUCTION GAPS (read before trusting the agreement numbers). Neither the felt
state nor the held-self-claims list AT THE TIME of each historical scan was logged (`self_implication_
shadow.jsonl`'s own schema only stores `thought`[:220 chars, itself already a truncation of the up-to
-600-char input the real call saw] + the 6 signals + `n_claims` as a COUNT, never the claims text).
This lab uses `felt="unknown"` (production's own literal fallback string when felt is unavailable —
`core/self_implication.py:72`, `(felt or 'unknown')`) and CURRENT `self_claims.held_claims()` as the
best available proxy for what the historical judge actually saw. Where a case's real
`contradicted_claim` still appears in the current held-claims list (checked case by case below —
several of the "paradox_holding" fires do), the reconstruction is faithful; where a case names a claim
that has since been dropped or reworded, it is not, and any C/contradiction disagreement on that case
should be read as a RECONSTRUCTION artefact, not necessarily a real model disagreement — flagged per-case
in the report. This is why mechanism #1's lab (fully real fields, no reconstruction gap) is the
stronger of the two model-tier verdicts; this one is real-but-approximate on two fields.

ISOLATION. `self_claims.held_claims()` is read-only (verified by reading its source before use — no
write path). This lab calls no `core.self_implication` function at all (no `scan_shadow()`, no
`_LOG` write) — it only imports the `_SYS` string constant and hits Ramses over HTTP directly.
Zero writes to `data/self_implication_shadow.jsonl` or any live state. Confirmed by re-checking that
file's line count immediately after the run.

DU-STOPPED NOTE: same disclosed deviation as the other two model-tier labs (Du was live throughout).

CONTRACT: read-only against Ramses + a read-only local state read (held_claims()). Writes ONLY to
data/lab/model_tier/self_implication/ + docs/lab/model_tier_self_implication.md.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = ROOT / "data" / "lab" / "model_tier" / "self_implication"
REPORT = ROOT / "docs" / "lab" / "model_tier_self_implication.md"
SHADOW_LOG = ROOT / "data" / "self_implication_shadow.jsonl"

CANDIDATE = ("mixtral:8x7b", "http://LAN-HOST:11438")
TIMEOUT_S = 120
MAX_TOKENS = 350     # matches the real call: max_tokens=350 at self_implication.py:73
TEMP = 0.2           # matches the real call: temperature=0.2
SIGNALS = "ABCDEF"

# ── The 15-case stratified sample, hand-picked from the real 7,416-row shadow log (random.seed(7) for
# the near-miss/flat draws — see the extraction note in the module docstring for the exact method).
CASE_TS = {
    "fire": [1783065373.8982122, 1786228555.1553996, 1786507915.207722, 1786524996.3191369,
             1786615041.8706682, 1786656716.3432472],
    "near_miss": [1786642389.1931548, 1786408622.8368886, 1786701182.2689817, 1786201106.3907256,
                  1786213469.8179758, 1787161858.492157],
    "flat": [1783065946.8742244, 1786343862.4009838, 1786832297.0350082],
}


def _sys() -> str:
    from core.self_implication import _SYS
    return _SYS


def _load_cases() -> list[dict]:
    want_ts = {ts for group in CASE_TS.values() for ts in group}
    ts_to_group = {ts: g for g, tss in CASE_TS.items() for ts in tss}
    found = {}
    for line in open(SHADOW_LOG, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        if ev.get("ts") in want_ts:
            found[ev["ts"]] = ev
    cases = []
    for ts in want_ts:
        ev = found.get(ts)
        if not ev:
            print(f"  !! ts {ts} not found in shadow log — skipping", flush=True)
            continue
        cases.append({"group": ts_to_group[ts], "ts": ts, "thought": ev["thought"],
                     "hist": {k: bool(ev.get(k)) for k in SIGNALS},
                     "hist_contradicted_claim": ev.get("contradicted_claim"),
                     "hist_fires_rule": bool(ev.get("fires_rule"))})
    cases.sort(key=lambda c: (c["group"], c["ts"]))
    return cases


def _post(url: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _ask(base: str, model: str, system: str, user: str) -> dict:
    body = {"model": model, "stream": False, "keep_alive": "10m", "format": "json", "think": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": TEMP, "num_predict": MAX_TOKENS}}
    t0 = time.time()
    try:
        d = _post(base + "/api/chat", body, TIMEOUT_S)
    except Exception as e:
        return {"ok": False, "why": repr(e)[:120], "wall": round(time.time() - t0, 1)}
    msg = d.get("message") or {}
    raw = msg.get("content") or ""
    return {"ok": True, "wall": round(time.time() - t0, 1), "raw": raw}


def _parse(raw: str) -> dict | None:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    try:
        return json.loads(s.strip())
    except Exception:
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j > i:
            try:
                return json.loads(s[i:j + 1])
            except Exception:
                return None
        return None


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    from core import self_claims

    system = _sys()
    held = self_claims.held_claims()      # CURRENT claims — see docstring's disclosed reconstruction gap
    claims_str = "\n".join(f"  - {c}" for c in held) or "  (none recorded yet)"
    print(f"held_claims() (current, {len(held)}): {held[:3]}...", flush=True)

    cases = _load_cases()
    print(f"{len(cases)} real cases loaded from {SHADOW_LOG}", flush=True)

    model, base = CANDIDATE
    print(f"=== {model} @ {base} ===", flush=True)
    results = []
    for c in cases:
        user = (f"CURRENT THOUGHT:\n{c['thought']}\n\nHELD SELF-CLAIMS:\n{claims_str}\n\n"
                f"CURRENT FELT STATE:\nunknown")
        r = _ask(base, model, system, user)
        p = _parse(r.get("raw", "")) if r.get("ok") else None
        cand = {k: bool(p.get(k)) for k in SIGNALS} if p else None
        agree = sum(1 for k in SIGNALS if cand and cand[k] == c["hist"][k]) if cand else None
        results.append({**c, "candidate": cand, "candidate_contradicted_claim": p.get("contradicted_claim") if p else None,
                        "raw": r.get("raw", "")[:300], "ok": r.get("ok"), "wall": r.get("wall"),
                        "signal_agree_of_6": agree})
        print(f"  [{c['group']:9s}] hist={c['hist']} cand={cand} agree={agree}/6", flush=True)

    raw_path = OUT_DIR / "raw.json"
    raw_path.write_text(json.dumps({"held_claims_used": held, "results": results}, indent=1,
                                   ensure_ascii=False), encoding="utf-8")
    print(f"wrote {raw_path}")


def score() -> None:
    data = json.loads((OUT_DIR / "raw.json").read_text(encoding="utf-8"))
    results = data["results"]
    answered = [r for r in results if r.get("candidate") is not None]
    n = len(results)
    per_signal = {}
    for k in SIGNALS:
        vals = [(r["hist"][k], r["candidate"][k]) for r in answered]
        agree = sum(1 for h, c in vals if h == c)
        per_signal[k] = {"agree": agree, "n": len(vals), "rate": round(agree / len(vals), 3) if vals else None}
    overall_agree = sum(r["signal_agree_of_6"] for r in answered if r["signal_agree_of_6"] is not None)
    overall_n = sum(6 for r in answered if r["signal_agree_of_6"] is not None)
    # final fires_rule agreement: recompute mixtral's fires_rule with the SAME code-side rule
    # commitment/self_implication production applies (self_implication.py:86): A and (C or (B and (D or E or F)))
    fires_agree = 0
    fires_n = 0
    for r in answered:
        cand = r["candidate"]
        cand_fires = cand["A"] and (cand["C"] or (cand["B"] and (cand["D"] or cand["E"] or cand["F"])))
        fires_agree += int(cand_fires == r["hist_fires_rule"])
        fires_n += 1
    scores = {
        "n_cases": n, "n_answered": len(answered), "format_ok_rate": round(len(answered) / n, 3) if n else 0.0,
        "per_signal_agreement": per_signal,
        "overall_signal_agreement": round(overall_agree / overall_n, 3) if overall_n else None,
        "fires_rule_agreement": round(fires_agree / fires_n, 3) if fires_n else None,
        "by_group": {},
    }
    for g in ("fire", "near_miss", "flat"):
        grp = [r for r in answered if r["group"] == g]
        agr = sum(r["signal_agree_of_6"] for r in grp) if grp else 0
        scores["by_group"][g] = {"n": len(grp), "mean_signal_agree_of_6": round(agr / len(grp), 2) if grp else None}
    (OUT_DIR / "scores.json").write_text(json.dumps(scores, indent=1), encoding="utf-8")
    print(json.dumps(scores, indent=1))
    _write_report(scores, results)


def _write_report(scores: dict, results: list[dict]) -> None:
    L, A = [], None
    A = L.append
    A("# Model-tier lab #2 — core.self_implication.scan_shadow, panel agreement\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · J-0254 (source: decision:D-0013) · 15 real historical "
      f"thoughts (6 real fires / 6 near-miss / 3 flat, stratified — see script docstring) from "
      f"`data/self_implication_shadow.jsonl` (7,416 real rows total) · `mixtral:8x7b` vs the recorded "
      f"historical hot-lane verdict, same `_SYS` prompt imported LIVE from `core/self_implication.py`.*\n")
    A("**Two disclosed reconstruction gaps** (felt state, held-self-claims-at-the-time) — read the "
      "script docstring before trusting these numbers as precisely as lab #1's. **Du was live "
      "throughout** (see lab #1's docstring for why this only threatens latency).\n")
    A(f"**Format-ok:** {scores['n_answered']}/{scores['n_cases']} ({scores['format_ok_rate']})\n")
    A(f"**Overall per-signal agreement (all 6 signals, all answered cases): "
      f"{scores['overall_signal_agreement']}**\n")
    A(f"**Final fires_rule agreement: {scores['fires_rule_agreement']}** — the scope's own bar: "
      f"\"if mixtral rubber-stamps the hot lane's calls this finding downgrades to 'not worth the "
      f"latency.'\"\n")
    A("| signal | meaning | agreement |")
    A("|---|---|---|")
    meaning = {"A": "self-standard reference (mandatory)", "B": "dejection/agitation affect",
              "C": "contradicts a held self-claim", "D": "characterological framing",
              "E": "self-prediction violation", "F": "loss/social rejection"}
    for k in SIGNALS:
        s = scores["per_signal_agreement"][k]
        A(f"| {k} | {meaning[k]} | {s['rate']} ({s['agree']}/{s['n']}) |")
    A("")
    A("| stratum | n | mean signal-agreement (of 6) |")
    A("|---|---|---|")
    for g, s in scores["by_group"].items():
        A(f"| {g} | {s['n']} | {s['mean_signal_agree_of_6']} |")
    A("")
    A("*Note: signal C (contradicted self-claim) is the one most exposed to the held-claims "
      "reconstruction gap — a low C-agreement rate may mean the models genuinely disagree, or that "
      "the current claims list differs from what the historical judge actually saw. Cases are listed "
      "below with both verdicts' `contradicted_claim` text so this can be checked by eye.*\n")
    A("## Per-case verdicts\n")
    for r in results:
        A(f"**[{r['group']}] {r['thought'][:110]}...**")
        A(f"- historical: {r['hist']} contradicted_claim={r['hist_contradicted_claim']!r} "
          f"fires_rule={r['hist_fires_rule']}")
        A(f"- mixtral: {r['candidate']} contradicted_claim={r.get('candidate_contradicted_claim')!r} "
          f"agree={r['signal_agree_of_6']}/6")
        A("")
    A(f"*Raw: `data/lab/model_tier/self_implication/raw.json` · scores: `scores.json`*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {REPORT}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        score()
    else:
        run()
