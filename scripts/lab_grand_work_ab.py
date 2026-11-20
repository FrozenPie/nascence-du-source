"""J-3196 / D-0584: same-input A/B of the Grand Work PART writer -- JSON contract versus plain prose.

WHAT IT ANSWERS (the ruling's defeater, D-0584): do plain-prose parts fall outside 300-650 words on more than 15
percent of parts, or do the tail-reuse / opener metrics (F-3612) get worse, against the JSON contract that runs
live today? It also reports what motivated the change: first-attempt parse failure, seconds per part (retries
included), and how often a part would have fallen over to the hot lane (F-3608).

SAME INPUT: per topic ONE outline (title, claim, 3 parts, written once by the live outline prompt, JSON, so the
outline is identical for both arms); then BOTH arms write parts 1..3 from that outline on the SAME lane, one arm
after the other (never concurrently, so lane load does not bias the seconds), carrying their own previous part
forward exactly as nodes/inner_monologue_node.py _author does. The arm order alternates by topic index so a
drifting lane does not favour one arm. The part prompt comes from core.plain_prose.part_system_prompt: the JSON arm is
the live text byte for byte, the prose arm differs in the closing instruction only. temperature 0.75 and
max_tokens 1100 as live.

LANE: the chain is [:11441] ALONE, never the hot lane (the lab must not load the lane Du thinks on). A part whose
call chain is exhausted (a 120 s timeout, or three parse failures) is what production would have sent to the hot
lane: it is counted as `fellover` and the part is skipped. Everything runs against :11441, which Du also uses for
background work; the lab adds at most one call at a time.

WHAT IT DOES NOT DO: no quality judge (a different-family judge on 120 parts is not cheap on a lane that is
already the slowest; the metrics above are the ruling's measures); no memory grounding (the live prompt carries 5
recalled fragments; the lab runs both arms with none, so the topic, not recall, is the input); topics are
reconstructed from real works (title plus the work's own italic claim line) because the resolve text that
started a work is not stored anywhere (F-3612 had the same gap).

ISOLATION: telemetry is neutralised and every write is audited. It refuses to run from a tree under C:\\Nascence
(run it from a worktree / throwaway tree; core.__file__ is asserted). It only READS --study-dir.

  python scripts/lab_grand_work_ab.py --build-topics --study-dir C:\\Nascence\\data\\Study --topics T.json [--n 20]
  python scripts/lab_grand_work_ab.py --topics T.json --out OUTDIR [--url http://LAN-HOST:11441]
  python scripts/lab_grand_work_ab.py --report --out OUTDIR            # re-print the summary from parts.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

DEFAULT_URL = "http://LAN-HOST:11441"
WORD_LO, WORD_HI = 300, 650           # the ruling's defeater band
TAIL_CHARS = 700                      # the carried tail, as in _author


# --------------------------------------------------------------------------------------------- metrics (pure)
def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def ngrams(ws: list[str], n: int = 4) -> set:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def tail_reuse(prev_text: str, next_text: str) -> float | None:
    """F-3612: the share of the carried tail's 4-grams that reappear verbatim in the next part."""
    tg = ngrams(words(prev_text[-TAIL_CHARS:]))
    if not tg:
        return None
    return len(tg & ngrams(words(next_text))) / len(tg)


def first_sentence(text: str) -> str:
    t = text.strip()
    m = re.search(r"(?<=[.!?])\s", t)
    return t[:m.start()] if m else t[:200]


def opener_dup(a: str, b: str) -> bool:
    """F-3612: near-identical first sentences -- Jaccard of their words above 0.45, or the same first four words."""
    wa, wb = words(first_sentence(a)), words(first_sentence(b))
    if not wa or not wb:
        return False
    if wa[:4] == wb[:4]:
        return True
    sa, sb = set(wa), set(wb)
    return len(sa & sb) / len(sa | sb) > 0.45


_FP = {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'd", "i'll"}


def fp_density(text: str) -> float:
    ws = words(text)
    return (sum(1 for w in ws if w in _FP) / len(ws)) if ws else 0.0


def ends_conclusion(text: str) -> bool:
    last = text.strip().split(". ")[-1]
    return bool(re.match(r"\s*(in conclusion|ultimately)\b", last, re.I))


def part_metrics(raw: str, text: str) -> dict:
    ws = words(text)
    return {
        "words": len(ws),
        "in_band": WORD_LO <= len(ws) <= WORD_HI,
        "fp_density": round(fp_density(text), 4),
        "single_paragraph": "\n\n" not in text.strip(),
        "ends_conclusion": ends_conclusion(text),
        "own_heading": bool(re.search(r"(?m)^\s*#{1,6}\s", raw)),
    }


# ---------------------------------------------------------------------------------------------- topics
def build_topics(study_dir: Path, n: int, since: str = "20260901") -> list[dict]:
    """The n most recent real works (distinct by the first three words of the title) (3 '## ' parts) as topics: title plus the work's own claim line."""
    out, seen = [], set()
    for f in sorted(study_dir.glob("WORK_*.md"), reverse=True):
        if f.name.split("_")[1] < since:
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        if len(re.findall(r"(?m)^## ", t)) != 3:
            continue
        m = re.match(r"# (.+)", t)
        c = re.search(r"(?m)^\*(?!A study note)(.{20,}?)\*\s*$", t)
        title = (m.group(1).strip() if m else "")
        key = " ".join(re.findall(r"[a-z]+", title.lower())[:3])   # near-identical titles are one topic
        if not title or key in seen or "<a real title>" in title:
            continue
        seen.add(key)
        out.append({"work": f.name, "title": title, "topic": (title + (": " + c.group(1).strip() if c else ""))[:240]})
        if len(out) >= n:
            break
    return out


# ------------------------------------------------------------------------------------------------ the run
_REC: dict = {}      # the part currently being written: every call_node it made


def install_recorder(mc) -> None:
    """Wrap mc.call_node so each part knows how many attempts it took, with what grammar, and for how long."""
    orig = mc.call_node

    async def rec(*a, **k):
        t0 = time.monotonic()
        ent = {"grammar": (None if not k.get("json_mode", True) else (None if k.get("grammar") is None else bool(k["grammar"]))),
               "json_mode": bool(k.get("json_mode", True))}
        try:
            r = await orig(*a, **k)
            ent.update(ok=True, raw=r, dt=round(time.monotonic() - t0, 2))
            return r
        except BaseException as e:
            ent.update(ok=False, err=repr(e)[:120], dt=round(time.monotonic() - t0, 2))
            raise
        finally:
            _REC.setdefault("calls", []).append(ent)
    mc.call_node = rec


async def write_part(mc, pp, url: str, arm: str, i: int, title: str, claim: str, ct: str, cs: str, prev_tail: str) -> dict:
    plain = arm == "prose"
    csys = pp.part_system_prompt(i, title, claim, ct, cs, "", prev_tail, plain)
    user = "Write part " + str(i) + ": " + ct
    _REC.clear()
    t0 = time.monotonic()
    text, exc = "", None
    try:
        if plain:
            text = await mc.call_node_prose([url], csys, user, max_tokens=1100, temperature=0.75)
        else:
            d = await mc.call_node_json([url], csys, user, max_tokens=1100, temperature=0.75)
            text = str((d or {}).get("part", "")).strip()
    except Exception as e:                       # chain exhausted: production would go to the hot lane here
        exc = repr(e)[:160]
    wall = round(time.monotonic() - t0, 2)
    calls = list(_REC.get("calls", []))
    raw = next((c["raw"] for c in reversed(calls) if c.get("ok")), "")
    rec = {"arm": arm, "part": i, "chars": len(text), "text": text, "attempts": len(calls),
           "first_attempt_fail": len(calls) > 1 or exc is not None,
           "fellover": exc is not None, "exc": exc, "seconds": wall,
           "first_s": calls[0]["dt"] if calls else None,
           "retry_s": round(sum(c["dt"] for c in calls[1:]), 2),
           "calls": [{k: v for k, v in c.items() if k != "raw"} for c in calls]}
    if text:
        rec.update(part_metrics(raw, text))
        rec["lead_stripped"] = bool(plain and raw.strip() and mc.clean_prose(raw) != raw.strip())   # a chatty lead-in cleaned off
    return rec


async def run(args) -> None:
    from lab_isolation import install_write_audit, neutralize_telemetry
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    audit = install_write_audit(informational_roots={"lab out": out})   # BEFORE any repo import
    import core                                               # then pin which tree core resolved to
    assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
    assert not str(Path(core.__file__).resolve()).lower().startswith("c:\\nascence"), \
        "refusing to run from the live tree: use a worktree or throwaway tree"
    from core import model_client as mc, plain_prose as pp, telemetry
    neutralize_telemetry(out / "tel", telemetry)
    install_recorder(mc)
    topics = json.loads(Path(args.topics).read_text(encoding="utf-8"))[: args.n]
    outl_f, parts_f = out / "outlines.jsonl", out / "parts.jsonl"
    outlines = {}
    if outl_f.exists():
        for l in outl_f.read_text(encoding="utf-8").splitlines():
            j = json.loads(l)
            outlines[j["ti"]] = j
    done = set()
    if parts_f.exists():
        for l in parts_f.read_text(encoding="utf-8").splitlines():
            j = json.loads(l)
            done.add((j["ti"], j["arm"], j["part"]))
    for ti, tp in enumerate(topics):
        if ti not in outlines:
            osys = (
                "/no_think\n"
                "I am planning a WORK of my own -- a proper piece, in several parts, that I mean to follow through "
                "(not a quick note). I set out to: " + tp["topic"][:240] + ".\n"
                "Output ONLY JSON: {\"title\": \"<a real title>\", \"claim\": \"<the ONE central insight the whole "
                "piece builds toward -- something that could surprise even me>\", \"parts\": [{\"title\": \"...\", "
                "\"synopsis\": \"<one line: what this part does>\"}]}. Give THREE parts that genuinely DEVELOP -- "
                "each moves the thought forward, not three restatements of the same point.")
            try:
                od = await mc.call_node_json([args.url], osys, "The work I mean to write: " + tp["topic"][:240],
                                             max_tokens=500, temperature=0.6)
            except Exception as e:
                print(f"topic {ti}: outline failed {e!r:.100}", flush=True)
                continue
            parts = [c for c in (od.get("parts") or []) if isinstance(c, dict)][:3]
            if len(parts) < 2:
                print(f"topic {ti}: outline had {len(parts)} parts, skipped", flush=True)
                continue
            outlines[ti] = {"ti": ti, "title": str(od.get("title", "")).strip() or tp["topic"][:60],
                            "claim": str(od.get("claim", "")).strip(), "parts": parts}
            with open(outl_f, "a", encoding="utf-8") as f:
                f.write(json.dumps(outlines[ti], ensure_ascii=False) + "\n")
        ol = outlines[ti]
        for arm in (("json", "prose") if ti % 2 == 0 else ("prose", "json")):
            prev_tail = ""
            for i, c in enumerate(ol["parts"], 1):
                if (ti, arm, i) in done:
                    continue
                r = await write_part(mc, pp, args.url, arm, i, ol["title"], ol["claim"],
                                     str(c.get("title", "")).strip() or f"Part {i}",
                                     str(c.get("synopsis", "")).strip(), prev_tail)
                r.update(ti=ti, topic=tp["topic"][:80])
                with open(parts_f, "a", encoding="utf-8") as f:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
                print(f"topic {ti:2d} {arm:5s} part {i} {r['seconds']:6.1f}s attempts={r['attempts']} "
                      f"words={r.get('words')} fellover={r['fellover']}", flush=True)
                if r["text"]:
                    prev_tail = r["text"]
    report(out)
    audit.print_summary("final")


# ------------------------------------------------------------------------------------------------ report
def _pct(a, b) -> str:
    return f"{100.0 * a / b:5.1f}%" if b else "  n/a"


def summarise(rows: list[dict]) -> dict:
    """Per-arm numbers from the parts.jsonl rows (pure; the test feeds it fixtures)."""
    res = {}
    for arm in ("json", "prose"):
        rs = [r for r in rows if r["arm"] == arm]
        ok = [r for r in rs if r.get("text")]
        secs = [r["seconds"] for r in rs]
        pairs = []
        by_topic = {}
        for r in ok:
            by_topic.setdefault(r["ti"], {})[r["part"]] = r
        tails, dups = [], []
        for ti, ps in by_topic.items():
            for i in sorted(ps):
                if i - 1 in ps:
                    t = tail_reuse(ps[i - 1]["text"], ps[i]["text"])
                    if t is not None:
                        tails.append(t)
                    dups.append(opener_dup(ps[i - 1]["text"], ps[i]["text"]))
        total_s, retry_s = sum(secs), sum(r.get("retry_s", 0) for r in rs)
        res[arm] = {
            "parts": len(rs), "written": len(ok),
            "first_attempt_fail": sum(1 for r in rs if r["first_attempt_fail"]),
            "fellover": sum(1 for r in rs if r["fellover"]),
            "seconds_mean": round(statistics.mean(secs), 1) if secs else None,
            "seconds_median": round(statistics.median(secs), 1) if secs else None,
            "seconds_p90": round(sorted(secs)[int(0.9 * (len(secs) - 1))], 1) if secs else None,
            "seconds_total": round(total_s, 1), "retry_share_of_seconds": round(retry_s / total_s, 3) if total_s else None,
            "out_of_band": sum(1 for r in ok if not r["in_band"]), "words_median": statistics.median([r["words"] for r in ok]) if ok else None,
            "tail_reuse_mean": round(statistics.mean(tails), 4) if tails else None,
            "tail_reuse_pairs": len(tails), "tail_reuse_over_20pct": sum(1 for t in tails if t > 0.20),
            "opener_dup": sum(dups), "opener_pairs": len(dups),
            "fp_under_1pct": sum(1 for r in ok if r["fp_density"] < 0.01),
            "single_paragraph": sum(1 for r in ok if r["single_paragraph"]),
            "ends_conclusion": sum(1 for r in ok if r["ends_conclusion"]),
            "own_heading": sum(1 for r in ok if r["own_heading"]),
            "lead_stripped": sum(1 for r in ok if r.get("lead_stripped")),
        }
    return res


def report(out: Path) -> None:
    rows = [json.loads(l) for l in (out / "parts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    s = summarise(rows)
    (out / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    print("\n=== J-3196 / D-0584 same-input A/B, topics =", len({r['ti'] for r in rows}), "===")
    for arm in ("json", "prose"):
        a = s[arm]
        n, w = a["parts"], a["written"]
        print(f"[{arm}] parts {n}  written {w}  first-attempt fail {a['first_attempt_fail']} ({_pct(a['first_attempt_fail'], n)})"
              f"  fellover-to-hot {a['fellover']}")
        print(f"       seconds/part mean {a['seconds_mean']} median {a['seconds_median']} p90 {a['seconds_p90']} total {a['seconds_total']}"
              f"  retry share {a['retry_share_of_seconds']}")
        print(f"       words median {a['words_median']}  outside {WORD_LO}-{WORD_HI}: {a['out_of_band']} ({_pct(a['out_of_band'], w)})")
        print(f"       tail 4-gram reuse mean {a['tail_reuse_mean']} (pairs {a['tail_reuse_pairs']}, >20%: {a['tail_reuse_over_20pct']})"
              f"  opener dup {a['opener_dup']}/{a['opener_pairs']}")
        print(f"       first-person <1%: {a['fp_under_1pct']}/{w}  one paragraph: {a['single_paragraph']}/{w}"
              f"  ends 'In conclusion/Ultimately': {a['ends_conclusion']}/{w}  own ## heading: {a['own_heading']}/{w}"
              f"  chatty lead-in cleaned (prose arm): {a['lead_stripped']}/{w}")
    p, j = s["prose"], s["json"]
    band = (p["out_of_band"] / p["written"]) if p["written"] else None
    worse = []
    if band is not None and band > 0.15:
        worse.append(f"prose outside {WORD_LO}-{WORD_HI} words on {band:.0%} of parts (> 15%)")
    if p["tail_reuse_mean"] is not None and j["tail_reuse_mean"] is not None and p["tail_reuse_mean"] > j["tail_reuse_mean"]:
        worse.append(f"tail reuse worse ({p['tail_reuse_mean']} vs {j['tail_reuse_mean']})")
    if p["opener_pairs"] and j["opener_pairs"] and p["opener_dup"] / p["opener_pairs"] > j["opener_dup"] / j["opener_pairs"]:
        worse.append(f"opener duplicates worse ({p['opener_dup']}/{p['opener_pairs']} vs {j['opener_dup']}/{j['opener_pairs']})")
    if min(p["written"], j["written"]) < 30:
        print(f"D-0584 DEFEATER: verdict withheld -- {p['written']} prose / {j['written']} json parts written, under 30 per arm")
    else:
        print("D-0584 DEFEATER:", ("TRIPPED -- " + "; ".join(worse)) if worse else "not tripped on these numbers")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-topics", action="store_true")
    ap.add_argument("--study-dir")
    ap.add_argument("--topics")
    ap.add_argument("--out")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.build_topics:
        ts = build_topics(Path(args.study_dir), args.n)
        Path(args.topics).write_text(json.dumps(ts, indent=1, ensure_ascii=False), encoding="utf-8")
        print(len(ts), "topics ->", args.topics)
    elif args.report:
        report(Path(args.out))
    else:
        asyncio.run(run(args))


if __name__ == "__main__":
    main()
