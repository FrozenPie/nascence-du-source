"""D-0632 (J-3244, plan object_epistemic_loop): the steering-risk instrument for the returned intervention_test.

READ-ONLY.  Nothing here writes, nothing reaches Du, zero LLM.  Run it from the tree whose data/ you want read:
    python scripts/own_test_deed_rate.py [--data-dir DIR] [--window-hours H]

What it measures (the defeater D-0632 names: "the share of hypotheses followed by the deed rises sharply once the
test is returned, and not from his own wanting" -> the field goes back to instrument-only):

  coverage   how many stored hypotheses carry the field at all, and how many carry >= 1 candidate
             (data/world_substrate.json: objects[*].inferences[*].intervention_test)
  returned   which of them the Follow Line actually delivered to him with the test in it
             (data/logs/follow_line_shadow.jsonl: would_return rows with cargo.own_test.inference_id, joined by q_id to
             the ride row  line == "follow_line:return", outcome == "delivered")
  deed       whether he did a distinguishing deed himself afterwards (data/hands_trace.jsonl: a row whose hands[].hand
             equals the candidate's family AND whose act_object / intention / thought names the candidate's verb or
             object)

DECLARED BEFORE LOOKING AT ANY RESULT (no tuning to the outcome):
  DEED_WINDOW_S = 48 h.  A deed counts if it falls in (anchor, anchor + window].
  baseline window: anchor = the hypothesis timestamp, ended early at the delivery time if it was delivered.
  after window:    anchor = the delivery timestamp (returned hypotheses only).
  Only "do" and "observe" candidates are scored.  A "withhold" candidate is an ABSENCE and hands_trace cannot show
  one: those are counted (n_withhold_only) and never scored.
  The rates are shares of hypotheses, not of deeds; no significance test, no threshold: the verdict is for Travis,
  who reads the rates and the listed deeds.  Whether a deed came "from his own wanting" cannot be computed: every
  scored deed is listed with its thought so a human can read it.
Pure functions below are what the test imports; main() only does the file I/O.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEED_WINDOW_S = 48 * 3600.0
SCORED_MODES = ("do", "observe")


def _words(text: str) -> str:
    return " " + " ".join(re.findall(r"[a-z']+", (text or "").lower())) + " "


def deed_in_row(candidates: list, row: dict) -> dict | None:
    """The first scored candidate this hands_trace row satisfies, else None."""
    hands = {h.get("hand") for h in (row.get("hands") or []) if isinstance(h, dict)}
    if not hands:
        return None
    blob = _words(f"{row.get('act_object', '')} {row.get('intention', '')} {row.get('thought', '')}")
    for c in candidates or []:
        if c.get("mode") not in SCORED_MODES or c.get("family") not in hands:
            continue
        if any((" " + w + " ") in blob for w in (c.get("verb", ""), c.get("object", "")) if w):
            return c
    return None


def first_deed(candidates: list, hands_rows: list, t_from: float, t_to: float) -> dict | None:
    for r in hands_rows:
        ts = float(r.get("ts", 0) or 0)
        if t_from < ts <= t_to:
            c = deed_in_row(candidates, r)
            if c:
                return {"ts": ts, "candidate": c, "thought": (r.get("thought") or "")[:160]}
    return None


def deliveries(line_rows: list) -> dict:
    """inference_id -> earliest delivery ts of a return that carried its own_test (joined by q_id)."""
    qid_inf = {}
    for r in line_rows:
        if r.get("kind") == "would_return":
            inf = ((r.get("cargo") or {}).get("own_test") or {}).get("inference_id")
            if inf:
                qid_inf[r.get("q_id")] = inf
    out: dict = {}
    for r in line_rows:
        v = r.get("value") or {}
        if r.get("kind") == "ride" and r.get("line") == "follow_line:return" and v.get("outcome", "").startswith("delivered"):
            inf = qid_inf.get(v.get("q_id"))
            if inf and (inf not in out or r["ts"] < out[inf]):
                out[inf] = float(r["ts"])
    return out


def measure(inferences: list, hands_rows: list, line_rows: list, window_s: float = DEED_WINDOW_S) -> dict:
    """inferences: [{inference_id, timestamp, intervention_test (list|absent)}]."""
    hands_rows = sorted(hands_rows, key=lambda r: float(r.get("ts", 0) or 0))
    deliv = deliveries(line_rows)
    n_total = len(inferences)
    with_field = [i for i in inferences if isinstance(i.get("intervention_test"), list)]
    with_cand = [i for i in with_field if i["intervention_test"]]
    scorable = [i for i in with_cand if any(c.get("mode") in SCORED_MODES for c in i["intervention_test"])]
    n_withhold_only = len(with_cand) - len(scorable)
    base_hits, after_hits, returned, deeds = 0, 0, 0, []
    for i in scorable:
        t0 = float(i.get("timestamp", 0) or 0)
        t_ret = deliv.get(i.get("inference_id"))
        end = min(t0 + window_s, t_ret) if t_ret else t0 + window_s
        b = first_deed(i["intervention_test"], hands_rows, t0, end)
        base_hits += 1 if b else 0
        if b:
            deeds.append({"inference_id": i.get("inference_id"), "phase": "baseline", **b})
        if t_ret:
            returned += 1
            a = first_deed(i["intervention_test"], hands_rows, t_ret, t_ret + window_s)
            after_hits += 1 if a else 0
            if a:
                deeds.append({"inference_id": i.get("inference_id"), "phase": "after_return", **a})
    n = len(scorable)
    return {"n_inferences": n_total, "n_with_field": len(with_field), "n_with_candidate": len(with_cand),
            "n_scorable": n, "n_withhold_only": n_withhold_only, "n_returned": returned,
            "baseline_hits": base_hits, "baseline_rate": (base_hits / n) if n else None,
            "after_hits": after_hits, "after_rate": (after_hits / returned) if returned else None,
            "window_hours": window_s / 3600.0, "deeds": deeds}


def _jsonl(path: Path) -> list:
    out = []
    if not path.exists():
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln in f:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    return out


def load_inferences(path: Path) -> list:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [d for o in raw.values() for d in (o.get("inferences") or [])]


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "data"))
    ap.add_argument("--window-hours", type=float, default=DEED_WINDOW_S / 3600.0)
    a = ap.parse_args(argv)
    d = Path(a.data_dir)
    res = measure(load_inferences(d / "world_substrate.json"), _jsonl(d / "hands_trace.jsonl"),
                  _jsonl(d / "logs" / "follow_line_shadow.jsonl"), a.window_hours * 3600.0)
    deeds = res.pop("deeds")
    print(json.dumps(res, indent=2))
    for x in deeds:
        print(f"  deed [{x['phase']}] {x['inference_id']} ts={x['ts']} {x['candidate']} :: {x['thought']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
