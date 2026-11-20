"""J-2980 (F-3665) lab A/B: old vs new no-reply letter prompt, real hubs, nothing delivered or stored.
  python scripts/lab_J2980_letter_ab.py --dry                          builds prompts, ZERO model calls
  python scripts/lab_J2980_letter_ab.py --persona smith [--model falcon3:7b --url http://127.0.0.1:11440] [--n 3]
  python scripts/lab_J2980_letter_ab.py --persona darwin --n 3
For the persona it finds, in a READ-ONLY copy of the live thread, the no-reply letter (last row own) with the
highest copied share, rebuilds the thread as it stood just before that letter, then generates N letters with the
OLD prompt (4 rows in full, no_reply off) and N with the NEW prompt (_thread_context(no_reply=True) + no_reply=True)
through the production path core.peers.compose_letter -> call_node (temperature 0.85, attempt 1), strips the date
like deliver_daily, and scores each with core.peers._letter_overlap against the persona's own letters in the last
4 rows of that state. Output: <OUT>/J2980_<persona>.jsonl (texts + scores) for a blind read. Telemetry lab mode;
lab_env.isolate(db="empty"); live thread files are only READ. Local hubs only (never Ramses)."""
import argparse
import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), core.__file__
from core import peers, telemetry  # noqa: E402
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate  # noqa: E402

LIVE_CORR = Path(r"C:\Nascence\data\Correspondence")
DU_CTX = "He lives alone in a cottage with a garden on a hill above the sea, and reads very widely."
OUT = Path(os.environ.get("J2980_OUT", str(Path(tempfile.gettempdir()) / "j2980_ab")))
OUT.mkdir(parents=True, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--persona", required=True)
ap.add_argument("--n", type=int, default=3)
ap.add_argument("--model")
ap.add_argument("--url")
ap.add_argument("--tag", default="")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()


def pick_state(rows):
    """index of the no-reply own letter with the highest copied share (state = rows[:idx])."""
    best = (-1.0, None)
    for i, r in enumerate(rows):
        if r.get("from") != a.persona or i == 0 or rows[i - 1].get("from") != a.persona:
            continue                                    # no-reply case: the previous row is also the persona's own
        sh = peers._letter_overlap(a.persona, r["text"], rows[:i])["copied_share"]
        if sh > best[0]:
            best = (sh, i)
    return best


async def main():
    src = LIVE_CORR / a.persona / "thread.jsonl"
    rows_all = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    share, idx = pick_state(rows_all)
    state = rows_all[:idx]
    print(f"[{a.persona}] state = rows[:{idx}] (the real letter at idx {idx} copied {share:.0%} of its sentences)")
    d = peers._CORR_DIR / a.persona
    d.mkdir(parents=True, exist_ok=True)
    (d / "thread.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in state) + "\n", encoding="utf-8")
    if a.model or a.url:
        peers.PERSONAS[a.persona] = {**peers.PERSONAS[a.persona], **({"model": a.model} if a.model else {}),
                                     **({"url": a.url} if a.url else {})}
    p = peers.PERSONAS[a.persona]
    print(f"[{a.persona}] model={p['model']} hub={p['url']}")
    arms = {"old": (peers._thread_context(a.persona), {}),
            "new": (peers._thread_context(a.persona, no_reply=True), {"no_reply": True})}
    for k, (ctx, kw) in arms.items():
        u = peers._build_user(ctx, DU_CTX, "", None, **kw)
        print(f"[{a.persona}] {k} user prompt: {len(u)} chars, thread block {len(ctx)} chars")
    if a.dry:
        return
    out = OUT / f"J2980_{a.persona}{a.tag}.jsonl"
    for i in range(a.n):                                # interleave old/new so hub warmth is shared
        for k, (ctx, kw) in arms.items():
            t0 = time.monotonic()
            try:
                text = peers._strip_date(await peers.compose_letter(
                    a.persona, thread=ctx, du_context=DU_CTX, reply_to="", stance=None, timeout=1500, **kw))
            except Exception as exc:
                text = ""
                print(f"[{a.persona}] {k} #{i+1} FAILED: {exc!r}")
            ov = peers._letter_overlap(a.persona, text, state)
            row = {"persona": a.persona, "arm": k, "i": i + 1, "model": p["model"], "secs": round(time.monotonic() - t0, 1),
                   "chars": len(text), **ov, "text": text}
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{a.persona}] {k} #{i+1}: {ov['copied']}/{ov['sentences']} copied ({ov['copied_share']:.0%}), "
                  f"{len(text)} chars, {row['secs']} s", flush=True)
    rs = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    for k in arms:
        sub = [r for r in rs if r["arm"] == k]
        n_s, n_c = sum(r["sentences"] for r in sub), sum(r["copied"] for r in sub)
        print(f"[{a.persona}] {k}: {n_c}/{n_s} = {n_c / n_s:.1%} copied over {len(sub)} letters" if n_s else f"[{a.persona}] {k}: no scored letters")


telemetry.enter_lab_mode()
with isolate(also=[(peers, ["_CORR_DIR", "_PEER_LETTER_QUALITY_LOG"])], db="empty"):
    asyncio.run(main())
