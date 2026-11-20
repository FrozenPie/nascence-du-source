"""J-3166 / D-0555 lab: replay recent Emotion-node rows with a 7th (curiosity) channel and an enumerated `primary`.

PHASE 1, SHADOW. Read-only on the training log; writes only the --out path you give it. Nothing here changes the live
prompt, AffectState, mood.felt_text, retrieval or any persisted summary.

The founder's defeater (D-0555): revisit if the replay shows |corr(curiosity, any of the other six)| > 0.9, or if
label/argmax agreement stays under 70% -> enumerate the six channels instead.

Modes
  baseline  NO model call. Scores the LOGGED (live-prompt) outputs of the last N rows: label distribution and
            label/argmax-of-six agreement. This is the "before" the replay is compared with.
  replay    Re-asks the SAME user prompt of each of the last N rows under the candidate prompt
            (core.emotion_curiosity.shadow_system_prompt), one model call per row through the hot lane, writes one
            result row per input row to --out, then prints the report. Run with Du DOWN or the hot lane idle: it is
            ~N calls at temperature 0.2. Telemetry writers are neutralised (lab_isolation) so no live telemetry
            file is appended to.
  score     NO model call. Reads a --results file written by `replay` and prints the report again.

Report (replay/score): label distribution, label/argmax agreement (seven channels, and the same rows' six-channel
agreement under the live prompt), correlation of the curiosity channel with the other six + valence + arousal,
how many embedded felt-text labels change (and, with --embed, the cosine between the old and new felt-text vectors),
and D-0555's defeater verdict.

Always run against a COPY of the live log, never the live file:
    python scripts/lab_emotion_curiosity_channel.py baseline --src <copy of emotion.jsonl> --n 200
    python scripts/lab_emotion_curiosity_channel.py replay   --src <copy> --n 200 --out <results.jsonl> [--embed]
    python scripts/lab_emotion_curiosity_channel.py score    --results <results.jsonl> [--src <copy> --n 200]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (BEFORE lab_env / lab_isolation / anything else)
assert Path(core.__file__).resolve().parent.parent == ROOT, core.__file__

from core import emotion_curiosity as ec  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEFAULT_SRC = ROOT / "data" / "training" / "emotion.jsonl"


def read_tail(path: Path, n: int) -> list[dict]:
    """The last n parseable rows of a jsonl file (keeps only the fields the lab needs)."""
    rows: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("node") == "emotion" and isinstance(r.get("output"), dict) and r.get("user_prompt"):
                rows.append(r)
    return rows[-n:]


def live_rec(r: dict) -> dict:
    """A parse_reply-shaped record from a LOGGED live-prompt output (no curiosity channel)."""
    o = r["output"]
    rec = ec.parse_reply(o)
    rec["curiosity"] = 0.0
    return rec


def baseline_report(rows: list[dict]) -> dict:
    recs = [live_rec(r) for r in rows]
    st = ec.label_stats(recs, ec.CHANNELS6)
    st["disagree_with_argmax_of_six"] = st["n"] - st["agree"]
    st["by_input_type"] = {}
    for it in sorted({r.get("input_type") for r in rows}):
        sub = [live_rec(r) for r in rows if r.get("input_type") == it]
        s = ec.label_stats(sub, ec.CHANNELS6)
        st["by_input_type"][it] = {"n": s["n"], "agreement": s["agreement"]}
    return st


async def _replay(rows: list[dict], out: Path, embed: bool) -> None:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    neutralize_telemetry(out.parent / "telemetry_scratch", telemetry)
    from core.model_client import call_node_json
    from core.schema import SERVE_CHAINS
    system = ec.shadow_system_prompt()
    chain = SERVE_CHAINS["hot"]
    with open(out, "w", encoding="utf-8") as f:
        for i, r in enumerate(rows):
            try:
                data = await call_node_json(chain, system, r["user_prompt"], max_tokens=512, temperature=0.2)
                ok = True
            except Exception as exc:
                data, ok = {}, False
                print(f"  [{i + 1}/{len(rows)}] call failed: {exc}", flush=True)
            res = {"cycle_id": r.get("cycle_id"), "input_type": r.get("input_type"), "ok": ok,
                   "live": live_rec(r), "shadow": ec.parse_reply(data) if ok else None}
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            if (i + 1) % 20 == 0:
                print(f"  {i + 1}/{len(rows)} replayed", flush=True)


def _cosine(a, b):
    try:
        import numpy as np
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        d = float(np.linalg.norm(a) * np.linalg.norm(b))
        return float(a @ b / d) if d else None
    except Exception:
        return None


def score_results(results: list[dict], embed: bool = False) -> dict:
    good = [r for r in results if r.get("ok") and r.get("shadow")]
    shadow = [r["shadow"] for r in good]
    live = [r["live"] for r in good]
    rep = {
        "rows": len(results), "rows_scored": len(good), "rows_failed": len(results) - len(good),
        "live_prompt_six_channel": ec.label_stats(live, ec.CHANNELS6),
        "candidate_prompt_seven_channel": ec.label_stats(shadow, ec.CHANNELS7),
        "candidate_prompt_vs_six_argmax": ec.label_stats(shadow, ec.CHANNELS6),
        "curiosity_channel": ec.channel_correlations(shadow),
    }
    changed = sum(1 for a, b in zip(live, shadow) if a["primary"] != b["primary"])
    ft = {"rows": len(good), "primary_label_changed": changed,
          "primary_label_changed_share": round(changed / len(good), 4) if good else None}
    if embed and good:
        try:
            from core.memory.store import _embed
            cos = []
            for a, b in zip(live, shadow):
                va, vb = _embed(ec.felt_text_live(a)), _embed(ec.felt_text_with_curiosity(b))
                c = _cosine(va, vb) if (va is not None and vb is not None) else None
                if c is not None:
                    cos.append(c)
            if cos:
                ft["embed_cosine_old_vs_new_mean"] = round(sum(cos) / len(cos), 4)
                ft["embed_cosine_old_vs_new_min"] = round(min(cos), 4)
                ft["embed_cosine_below_0.9_share"] = round(sum(1 for c in cos if c < 0.9) / len(cos), 4)
                ft["embed_pairs"] = len(cos)
        except Exception as exc:
            ft["embed_error"] = str(exc)[:200]
    rep["felt_text_change"] = ft
    rep["defeater_D0555"] = ec.defeater_verdict(
        rep["candidate_prompt_seven_channel"]["agreement"], rep["curiosity_channel"]["max_abs_r_vs_six"])
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["baseline", "replay", "score"])
    ap.add_argument("--src", default=str(DEFAULT_SRC), help="a COPY of data/training/emotion.jsonl")
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--out", help="replay: where to write the per-row results (never data/)")
    ap.add_argument("--results", help="score: a results file written by replay")
    ap.add_argument("--embed", action="store_true", help="also price the felt-text change with the MiniLM embedder")
    a = ap.parse_args()

    if a.mode == "baseline":
        rows = read_tail(Path(a.src), a.n)
        print(json.dumps(baseline_report(rows), indent=2, ensure_ascii=False))
        return 0
    if a.mode == "replay":
        if not a.out:
            ap.error("replay needs --out")
        out = Path(a.out).resolve()
        if ROOT / "data" in out.parents:
            ap.error("--out must not be under data/")
        out.parent.mkdir(parents=True, exist_ok=True)
        rows = read_tail(Path(a.src), a.n)
        print(f"replaying {len(rows)} rows under the candidate prompt ...", flush=True)
        asyncio.run(_replay(rows, out, a.embed))
        a.results = str(out)
    results = [json.loads(l) for l in open(a.results, encoding="utf-8") if l.strip()]
    print(json.dumps(score_results(results, embed=a.embed), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
