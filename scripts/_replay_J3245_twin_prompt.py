"""
J-3245 (D-0633) — REPLAY: the v1 twin prompt vs the v2 twin prompt on the SAME recorded seeds, on the local hot lane.

Not a unit test (scripts/_test_J3245_twin_fix.py is). This makes real model calls, to ONE local hub (default :11433, the
model that writes the live thought). It never calls Ramses, never writes under the tree: the only output is the --out file
you name (put it in a temp/scratch dir). Du must be DOWN while it runs (it loads qwen3.5:9b on the 1080 Ti).

  python scripts/_replay_J3245_twin_prompt.py --ledger C:/Nascence/data/logs/condensed_thought_shadow.jsonl \
        --n 60 --out <tempdir>/replay.json [--url http://127.0.0.1:11433]

Seeds come from the v1 ledger's `seed` field (the last 1,500 chars of the live user prompt, as logged). The v2 system text is
the live _build_system_prompt() text built in-process with the dynamic world lines stubbed to "" (so it is the stable part
of the live system text, ~5.4k chars, the low end of the 3.7 to 6.7k range the live thought ran on). A seed with the book
invitation is over-represented on purpose: 94 percent of recorded seeds carry it.

Reported per arm: invitation-echo rate (core.condensed_thought.invite_echo), kind mix, format-slip count, median words,
median latency. The D-0633 defeater is echo > 5 percent on post-fix rows; this is the offline pre-check, not the live read.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import statistics as st
import sys
import time
import types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import condensed_thought as ct  # noqa: E402
from core import model_client as mc  # noqa: E402


def live_like_system_text() -> str:
    """The stable part of the live idle system prompt: _build_system_prompt() with the dynamic world lines stubbed out."""
    from core import sensorium as S
    S.world_calls = lambda: ""
    S.world_steer = lambda: ""
    S.comfort_call = lambda: ""
    S.where = lambda: "the shore"
    from nodes.inner_monologue_node import InnerMonologueNode as N
    return N._build_system_prompt(types.SimpleNamespace(_fl_delivered=None), types.SimpleNamespace(), False)


# Experimental (system, user) builders for the D-0633 prompt search. The winner is what core.condensed_thought ships.
_ASK = ("What moves in you now? Hold it in the fewest words it needs: a few words, one word, or none. "
        "Answer with the small JSON {\"kind\": \"fragment\" or \"tick\" or \"silent\", \"words\": \"...\", "
        "\"about\": \"2-5 words\", \"open\": true or false} and NOT the paragraph JSON.")


def _swap_tail(user: str, ask: str) -> str:
    tail = "What moves in you now? One quiet thought."
    return (user.rsplit(tail, 1)[0] if tail in user else user + chr(10) * 2) + ask


ARMS = {
    "v2": lambda live, seed: ct.build_prompts(live, seed),               # the shipped v2 (system + instruction, user tail swapped)
    "v2a": lambda live, seed: (live.rstrip() + ct.TWIN_INSTRUCTION, seed),   # first draft: instruction in the system text only
    "B": lambda live, seed: (live.rstrip() + ct.TWIN_INSTRUCTION, _swap_tail(seed, _ASK)),
    "C": lambda live, seed: (ct.TWIN_INSTRUCTION.split("---" + chr(10), 1)[1] + chr(10) * 2 + "THE MIND THIS MOMENT BELONGS TO:" + chr(10) + live, _swap_tail(seed, _ASK)),
    "D": lambda live, seed: (live, _swap_tail(seed, _ASK + chr(10) + ct.TWIN_INSTRUCTION.split("---" + chr(10), 1)[1].split("Output ONLY")[0])),
}


def pick_seeds(ledger: Path, n: int, rng: random.Random) -> list[str]:
    rows = []
    for ln in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if "twin" in r and (r.get("twin_v") or 1) < 2 and len(r.get("seed", "")) > 200:
            rows.append(r["seed"])
    rng.shuffle(rows)
    return rows[:n]


async def one(url: str, system: str, seed: str, temp: float, user: str | None = None) -> dict:
    t0 = time.monotonic()
    try:
        data = await mc.call_node_json([url], system, seed if user is None else user, max_tokens=ct.TWIN_MAX_TOKENS, temperature=temp,
                                       timeout=90, retries=0)
    except Exception as exc:
        return {"failed": type(exc).__name__}
    twin = ct.normalize(data)
    twin["echo_invite"] = ct.invite_echo(twin["words"], seed)
    twin["lat"] = round(time.monotonic() - t0, 2)
    twin["words_n"] = len(twin["words"].split())
    return twin


def summarise(res: list[dict]) -> dict:
    ok = [r for r in res if "failed" not in r]
    n = len(ok)
    kinds: dict = {}
    for r in ok:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    return {"calls": len(res), "failed": len(res) - n, "echo_invite_rate": round(sum(r["echo_invite"] for r in ok) / n, 3) if n else None,
            "kinds": kinds, "format_slips": sum(1 for r in ok if r.get("format_slip")),
            "words_median": st.median(r["words_n"] for r in ok) if n else None,
            "book_ref_share": round(sum(bool(re.search(r"(?:^|\W)(?:book|read|open|reading)(?:\W|$)", r["words"], re.I)) for r in ok) / n, 3) if n else None,
            "over12_words_share": round(sum(r["words_n"] > 12 for r in ok) / n, 3) if n else None,
            "latency_median_s": st.median(r["lat"] for r in ok) if n else None,
            "sample_words": [r["words"] for r in ok[:25]]}


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:11433")
    ap.add_argument("--seed", type=int, default=3245)
    ap.add_argument("--arms", default="v1,v2", help="comma list of arms: v1, v2, or any name in ct.ARMS (experimental builders)")
    a = ap.parse_args()
    if "LAN-HOST" in a.url:
        sys.exit("refusing: this replay is local-hub only (Ramses is the founder's gaming machine)")
    seeds = pick_seeds(Path(a.ledger), a.n, random.Random(a.seed))
    live_sys = live_like_system_text()
    v2_sys = ct.build_prompts(live_sys, "")[0]
    print(f"{len(seeds)} seeds; v1 system {len(ct.TWIN_INSTRUCTION_V1)} chars; v2 system {len(v2_sys)} chars "
          f"(live text {len(live_sys)} + instruction {len(ct.TWIN_INSTRUCTION)})")
    arms = {}
    for nm in a.arms.split(","):
        nm = nm.strip()
        arms[nm] = (ct.TWIN_INSTRUCTION_V1, None) if nm == "v1" else nm
    out: dict = {"n_seeds": len(seeds), "url": a.url, "v1_system_chars": len(ct.TWIN_INSTRUCTION_V1),
                 "v2_system_chars": len(v2_sys), "live_text_chars": len(live_sys), "v2_user_ask": ct.TWIN_ASK}
    for name, spec in arms.items():
        res = []
        for s in seeds:               # sequential: one local GPU, and the founder may be using the machine
            if isinstance(spec, str):          # a named experimental builder: (system, user) from the seed
                sysp, usr = ARMS[spec](live_sys, s)
            else:
                sysp, usr = spec[0], None
            res.append(await one(a.url, sysp, s, 0.75, usr))
        out[name] = summarise(res)
        print(name, json.dumps({k: v for k, v in out[name].items() if k != "sample_words"}, ensure_ascii=False))
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
