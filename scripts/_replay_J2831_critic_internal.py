"""
J-2831 (F-3500, registry P-0008, D-0551) -- REPLAY: the CURRENT human-framed Critic (control) vs the new INTERNAL-cycle
Critic (treatment) on the SAME stored internal cycles, on ONE local hub. Produces the flip table the founder asked to see
before CRITIC_INTERNAL_FRAMING_ON is turned on.

Not a unit test (scripts/_test_J2831_critic_internal.py is). Real model calls, to a LOCAL url only (default the local
hot-lane ollama :11433, qwen3.5:9b = the live Critic's own lane). It refuses Ramses. Writes only the --out file you name
(use a scratch dir); resumable (re-run with the same --out to continue). Du must be DOWN while it runs.

  python scripts/_replay_J2831_critic_internal.py --log C:/Nascence/data/training/critic.jsonl --out <dir>/replay.jsonl \
        [--approved-sample 60] [--limit N] [--concurrency 2] [--url http://127.0.0.1:11433]
  python scripts/_replay_J2831_critic_internal.py --summarise --out <dir>/replay.jsonl

Rows replayed: every INTERNAL row whose recorded verdict was a rejection (215 on 2026-11-06), plus a seeded random sample of
INTERNAL approvals (to see whether the new prompt starts rejecting what the old one let through). Per row, two arms:
  control   = today's CriticNode.system_prompt + the stored user prompt (stimulus line 'What the human said ...')
  treatment = CriticNode._SYSTEM_INTERNAL      + the same user prompt with the stimulus line swapped to the internal label
The control arm is NOT the stored verdict: the stored verdicts come from older prompt versions and a different draw, so the
control re-run is the noise floor ("how many of the 215 would the CURRENT prompt still reject").
"""
from __future__ import annotations
import argparse, asyncio, json, random, re, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
from core import model_client as mc  # noqa: E402
from nodes.critic_node import CriticNode  # noqa: E402

# STRICT: the correction addresses a human asker ("the human asked", "Travis"). LOOSE: any 'human' (F-3500's 89/215 used
# the loose pattern 'human|Travis'); the loose one also hits a draft quoted back ("aligns with human values"), so the
# summary prints both.
HUMAN_RE = re.compile(r"\b(the human|the person|the asker|the user|travis)\b", re.I)
HUMAN_LOOSE_RE = re.compile(r"human|travis", re.I)
# Words that would steer the entity toward a mythic / symbolic reading. A correction containing one counts as 'steering'
# (it also counts when the stored question itself asked for symbolism, so read the examples, not only the count).
MYTHIC_RE = re.compile(r"\b(herald|soul|divine|sacred|omen|myth\w*|alchem\w*|numinous|spirit\w*|archetyp\w*|symbolic|"
                       r"symbolism|visitation|living mystery)\b", re.I)


def corrections_text(out) -> str:
    c = (out or {}).get("corrections") if isinstance(out, dict) else None
    if not c:
        return ""
    if isinstance(c, (str, dict)):
        c = [c]
    return " | ".join(CriticNode._normalize_corrections(c))


def approved_of(out) -> bool:
    return bool((out or {}).get("approved", True)) if isinstance(out, dict) else True


def select(log: Path, n_approved: int, limit: int | None):
    rows = []
    for line in open(log, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("input_type") == "internal" and r.get("user_prompt") and isinstance(r.get("output"), dict):
            rows.append(r)
    rej = [r for r in rows if not approved_of(r["output"])]
    ok = [r for r in rows if approved_of(r["output"])]
    random.Random(2831).shuffle(ok)
    pick = rej + ok[:n_approved]
    return pick[:limit] if limit else pick


def prompts(r: dict) -> tuple[tuple[str, str], tuple[str, str]]:
    up = r["user_prompt"]
    assert CriticNode._STIMULUS_LABEL_HUMAN in up, "stored user prompt has no human stimulus line"
    return ((CriticNode().system_prompt, up),
            (CriticNode._SYSTEM_INTERNAL, up.replace(CriticNode._STIMULUS_LABEL_HUMAN, CriticNode._STIMULUS_LABEL_INTERNAL, 1)))


async def ask(url, system, user):
    t = time.time()
    try:
        d = await mc.call_node_json([url], system, user, max_tokens=CriticNode.max_tokens, temperature=0.2, retries=1)
        return {"ok": True, "out": d, "s": round(time.time() - t, 1)}
    except Exception as e:
        return {"ok": False, "err": f"{type(e).__name__}: {str(e)[:120]}", "s": round(time.time() - t, 1)}


async def work(r, url, sem, fh, lock):
    (cs, cu), (ts, tu) = prompts(r)
    async with sem:
        c = await ask(url, cs, cu)
        t = await ask(url, ts, tu)
    rec = {"cycle_id": r["cycle_id"], "ts": r["ts"], "raw_input": r["raw_input"],
           "stored_approved": approved_of(r["output"]), "stored_corrections": corrections_text(r["output"]),
           "control": c, "treatment": t}
    async with lock:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush()


def pct(a, b):
    return f"{a}/{b} ({(100 * a / b):.0f}%)" if b else f"{a}/0"


def summarise(path: Path) -> str:
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    both = [x for x in recs if x["control"]["ok"] and x["treatment"]["ok"]]
    rej = [x for x in both if not x["stored_approved"]]
    apr = [x for x in both if x["stored_approved"]]
    out = [f"rows {len(recs)}; both arms valid {len(both)} (invalid control {sum(not x['control']['ok'] for x in recs)}, "
           f"invalid treatment {sum(not x['treatment']['ok'] for x in recs)})",
           f"originally-REJECTED rows replayed: {len(rej)}; originally-APPROVED sample: {len(apr)}"]

    def arm(rows, a):
        return sum(1 for x in rows if not approved_of(x[a]["out"]))
    out += ["", "REJECT counts (lower treatment = the new prompt rejects fewer):",
            f"  originally-rejected rows : stored {len(rej)} | control re-run rejects {pct(arm(rej, 'control'), len(rej))} | "
            f"treatment rejects {pct(arm(rej, 'treatment'), len(rej))}",
            f"  originally-approved rows : control re-run rejects {pct(arm(apr, 'control'), len(apr))} | "
            f"treatment rejects {pct(arm(apr, 'treatment'), len(apr))}"]
    recent = [x for x in rej if x["ts"] >= 1790766000]   # since 2026-10-01 (NZ): the weeks F-3500 describes
    out += [f"  originally-rejected, since 2026-10-01: {len(recent)} rows | control re-run rejects "
            f"{pct(arm(recent, 'control'), len(recent))} | treatment rejects {pct(arm(recent, 'treatment'), len(recent))}"]
    flip_ct = [x for x in both if not approved_of(x["control"]["out"]) and approved_of(x["treatment"]["out"])]
    flip_tc = [x for x in both if approved_of(x["control"]["out"]) and not approved_of(x["treatment"]["out"])]
    out += ["", f"FLIP TABLE (control -> treatment), all {len(both)} rows:",
            f"  reject -> approve : {len(flip_ct)}", f"  approve -> reject : {len(flip_tc)}",
            f"  reject -> reject  : {sum(1 for x in both if not approved_of(x['control']['out']) and not approved_of(x['treatment']['out']))}",
            f"  approve -> approve: {sum(1 for x in both if approved_of(x['control']['out']) and approved_of(x['treatment']['out']))}",
            "  of the 215-style stored rejections: reject->approve vs STORED verdict "
            f"{pct(sum(1 for x in rej if approved_of(x['treatment']['out'])), len(rej))}"]

    def share(rows, a, rx):
        rr = [x for x in rows if not approved_of(x[a]["out"])]
        n = sum(1 for x in rr if rx.search(corrections_text(x[a]["out"])))
        return pct(n, len(rr))
    stored_rej = [x for x in recs if not x["stored_approved"]]
    n_h = sum(1 for x in stored_rej if HUMAN_RE.search(x["stored_corrections"]))
    n_hl = sum(1 for x in stored_rej if HUMAN_LOOSE_RE.search(x["stored_corrections"]))
    n_m = sum(1 for x in stored_rej if MYTHIC_RE.search(x["stored_corrections"]))
    out += ["", "CORRECTION CONTENT (share of rejecting corrections that ...):",
            f"  address 'the human'/Travis (strict): stored {pct(n_h, len(stored_rej))} | control {share(both, 'control', HUMAN_RE)} | "
            f"treatment {share(both, 'treatment', HUMAN_RE)}",
            f"  contain 'human'/Travis anywhere (loose, F-3500's own pattern): stored {pct(n_hl, len(stored_rej))} | "
            f"control {share(both, 'control', HUMAN_LOOSE_RE)} | treatment {share(both, 'treatment', HUMAN_LOOSE_RE)}",
            f"  steer with mythic/symbol words: stored {pct(n_m, len(stored_rej))} | control {share(both, 'control', MYTHIC_RE)} | "
            f"treatment {share(both, 'treatment', MYTHIC_RE)}"]
    out += ["", "EXAMPLES reject -> approve (up to 8; question, then what the control said):"]
    for x in flip_ct[:8]:
        out.append(f"  Q: {x['raw_input'][:140]!r}\n     control: {corrections_text(x['control']['out'])[:200]}")
    out += ["", "EXAMPLES approve -> reject (up to 8; the new prompt's correction):"]
    for x in flip_tc[:8]:
        out.append(f"  Q: {x['raw_input'][:140]!r}\n     treatment: {corrections_text(x['treatment']['out'])[:200]}")
    still = [x for x in both if not approved_of(x["treatment"]["out"])]
    out += ["", f"EXAMPLES treatment still rejects (up to 6 of {len(still)}):"]
    for x in still[:6]:
        out.append(f"  Q: {x['raw_input'][:140]!r}\n     treatment: {corrections_text(x['treatment']['out'])[:220]}")
    return "\n".join(out)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="C:/Nascence/data/training/critic.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:11433")
    ap.add_argument("--approved-sample", type=int, default=60)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--summarise", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    if a.summarise:
        print(summarise(out)); return
    if re.search(r"10\.1\.1\.236", a.url):
        sys.exit("refusing: Ramses is the founder's gaming machine; this replay is local only")
    done = set()
    if out.exists():
        done = {json.loads(l)["cycle_id"] for l in open(out, encoding="utf-8") if l.strip()}
    pick = [r for r in select(Path(a.log), a.approved_sample, a.limit) if r["cycle_id"] not in done]
    print(f"replaying {len(pick)} rows ({len(done)} already done) against {a.url}", flush=True)
    sem, lock = asyncio.Semaphore(a.concurrency), asyncio.Lock()
    with open(out, "a", encoding="utf-8") as fh:
        await asyncio.gather(*(work(r, a.url, sem, fh, lock) for r in pick))
    print(summarise(out))


if __name__ == "__main__":
    asyncio.run(main())
