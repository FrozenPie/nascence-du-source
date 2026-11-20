"""J-2928 (F-3612): does a different continuity input stop Grand Work parts restating the carried tail?
Arms on the SAME outline per topic, live JSON-contract part prompt, :11441 alone, one call at a time:
 a = live (previous part's last 700 chars)   b = previous part title+synopsis+its single last sentence
 c = one-line list of earlier part headings + 'open on a new idea'   d = no carry.
Judge (different family, falcon3:7b on judge2 hub :11440): does part N advance beyond N-1 (1-5).
Run from a throwaway worktree (refuses under C:\\Nascence):
  python scripts/lab_continuity_J2928.py --topics T.json --out OUT [--n 12] [--judge-url http://localhost:11440]
  python scripts/lab_continuity_J2928.py --report --out OUT
"""
from __future__ import annotations
import argparse, asyncio, json, re, statistics, sys, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # core BEFORE lab_env/lab_isolation
import lab_grand_work_ab as L

URL = "http://LAN-HOST:11441"
ARMS = ("a", "b", "c", "d")
STOP = set("the a an of and to in on for with is are as by at from or that this it its be".split())


def last_sentence(t: str) -> str:
    ss = re.split(r"(?<=[.!?])\s+", t.strip())
    return ss[-1][:300] if ss else ""


def heading_recall(title: str, text: str) -> float:
    ws = [w for w in L.words(title) if w not in STOP and len(w) > 2]
    tw = set(L.words(text))
    return (sum(1 for w in ws if w in tw) / len(ws)) if ws else 0.0


def carry_block(arm, i, parts, texts):
    if i == 1 or arm == "d":
        return ""
    pt = parts[i - 2]
    if arm == "b":
        return ("\n\nThe previous part was \"" + str(pt.get("title", "")) + "\" (" + str(pt.get("synopsis", "")) +
                "). Its last sentence was: " + last_sentence(texts[-1]) +
                "\nCarry the thought forward; do NOT repeat or restate any of it.")
    if arm == "c":
        hs = "; ".join(f"{k}. {str(p.get('title',''))}" for k, p in enumerate(parts[:i - 1], 1))
        return ("\n\nParts already written: " + hs + ". This part must open on a new idea, not the previous "
                "conclusion, and must not restate what those parts covered.")
    return ""


def build_prompt(pp, arm, i, title, claim, ct, cs, parts, texts):
    prev = texts[-1] if texts else ""
    if arm == "a":
        return pp.part_system_prompt(i, title, claim, ct, cs, "", prev, False)
    base = pp.part_system_prompt(i, title, claim, ct, cs, "", "", False)
    k = base.index("\nWrite this part IN FULL")
    return base[:k] + carry_block(arm, i, parts, texts) + base[k:]


async def run(a):
    from lab_isolation import install_write_audit, neutralize_telemetry
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    audit = install_write_audit(informational_roots={"lab out": out})
    assert not str(Path(core.__file__).resolve()).lower().startswith("c:\\nascence"), "run from a worktree"
    from core import model_client as mc, plain_prose as pp, telemetry
    neutralize_telemetry(out / "tel", telemetry)
    topics = json.loads(Path(a.topics).read_text(encoding="utf-8"))[: a.n]
    of, pf = out / "outlines.jsonl", out / "parts.jsonl"
    outl = {}
    if of.exists():
        for l in of.read_text(encoding="utf-8").splitlines():
            j = json.loads(l); outl[j["ti"]] = j
    done = {}
    if pf.exists():
        for l in pf.read_text(encoding="utf-8").splitlines():
            j = json.loads(l); done[(j["ti"], j["arm"], j["part"])] = j
    deadline = time.time() + a.max_hours * 3600
    for ti, tp in enumerate(topics):
        if time.time() > deadline:
            print("deadline reached"); break
        if ti not in outl:
            osys = ("/no_think\nI am planning a WORK of my own -- a proper piece, in several parts, that I mean to follow through "
                    "(not a quick note). I set out to: " + tp["topic"][:240] + ".\n"
                    "Output ONLY JSON: {\"title\": \"<a real title>\", \"claim\": \"<the ONE central insight the whole "
                    "piece builds toward -- something that could surprise even me>\", \"parts\": [{\"title\": \"...\", "
                    "\"synopsis\": \"<one line: what this part does>\"}]}. Give THREE parts that genuinely DEVELOP -- "
                    "each moves the thought forward, not three restatements of the same point.")
            try:
                od = await mc.call_node_json([URL], osys, "The work I mean to write: " + tp["topic"][:240], max_tokens=500, temperature=0.6)
            except Exception as e:
                print(f"topic {ti} outline failed {e!r:.80}", flush=True); continue
            parts = [c for c in (od.get("parts") or []) if isinstance(c, dict)][:3]
            if len(parts) < 3:
                print(f"topic {ti} outline {len(parts)} parts, skip"); continue
            outl[ti] = {"ti": ti, "title": str(od.get("title", "")).strip() or tp["topic"][:60],
                        "claim": str(od.get("claim", "")).strip(), "parts": parts}
            with open(of, "a", encoding="utf-8") as f:
                f.write(json.dumps(outl[ti], ensure_ascii=False) + "\n")
        ol = outl[ti]
        order = list(ARMS[ti % 4:] + ARMS[:ti % 4])
        for arm in order:
            texts = []
            for i, c in enumerate(ol["parts"], 1):
                ct = str(c.get("title", "")).strip() or f"Part {i}"
                key = (ti, arm, i)
                if key in done:
                    r = done[key]
                else:
                    csys = build_prompt(pp, arm, i, ol["title"], ol["claim"], ct, str(c.get("synopsis", "")).strip(), ol["parts"], texts)
                    t0 = time.monotonic(); text = ""; exc = None
                    try:
                        d = await mc.call_node_json([URL], csys, "Write part " + str(i) + ": " + ct, max_tokens=1100, temperature=0.75)
                        text = str((d or {}).get("part", "")).strip()
                    except Exception as e:
                        exc = repr(e)[:150]
                    r = {"ti": ti, "arm": arm, "part": i, "text": text, "exc": exc, "seconds": round(time.monotonic() - t0, 1),
                         "words": len(L.words(text)), "heading_recall": round(heading_recall(ct, text), 3)}
                    if texts and text:
                        r["tail_reuse"] = L.tail_reuse(texts[-1], text)
                        r["opener_dup"] = L.opener_dup(texts[-1], text)
                    with open(pf, "a", encoding="utf-8") as f:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    print(f"t{ti} {arm} p{i} {r['seconds']}s w={r['words']} reuse={r.get('tail_reuse')}", flush=True)
                    done[key] = r
                if r["text"]:
                    texts.append(r["text"])
                else:
                    break
    # judge pass
    jf = out / "judge.jsonl"
    judged = set()
    if jf.exists():
        for l in jf.read_text(encoding="utf-8").splitlines():
            j = json.loads(l); judged.add((j["ti"], j["arm"], j["part"]))
    for (ti, arm, i), r in sorted(done.items()):
        if i < 2 or not r["text"] or (ti, arm, i) in judged:
            continue
        prev = done.get((ti, arm, i - 1))
        if not prev or not prev["text"]:
            continue
        sysj = ("/no_think\nYou compare two consecutive parts of one essay. Output ONLY JSON: {\"advance\": <1-5>} where 1 = part B "
                "mostly restates part A, 5 = part B clearly moves beyond A with new ideas, evidence or turns.")
        usr = "PART A:\n" + prev["text"][:1800] + "\n\nPART B:\n" + r["text"][:1800]
        try:
            d = await mc.call_node_json([a.judge_url], sysj, usr, max_tokens=60, temperature=0.0)
            sc = d.get("advance")
        except Exception:
            sc = None
        with open(jf, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ti": ti, "arm": arm, "part": i, "advance": sc}) + "\n")
        print(f"judge t{ti} {arm} p{i} -> {sc}", flush=True)
    report(out)


def report(out: Path):
    rows = [json.loads(l) for l in (out / "parts.jsonl").read_text(encoding="utf-8").splitlines()]
    jr = {}
    jp = out / "judge.jsonl"
    if jp.exists():
        for l in jp.read_text(encoding="utf-8").splitlines():
            j = json.loads(l); jr[(j["ti"], j["arm"], j["part"])] = j["advance"]
    f = lambda x: f"{statistics.mean(x):.3f}" if x else "-"
    print("arm n_parts fail words tail_reuse opener_dup head_recall judge_advance(n) secs")
    for arm in ARMS:
        rs = [r for r in rows if r["arm"] == arm]
        ok = [r for r in rs if r["text"]]
        tr = [r["tail_reuse"] for r in ok if r.get("tail_reuse") is not None]
        od = [float(r["opener_dup"]) for r in ok if "opener_dup" in r]
        js = [v for (t, a_, p), v in jr.items() if a_ == arm and isinstance(v, (int, float))]
        print(arm, len(rs), len(rs) - len(ok), f([r["words"] for r in ok]), f(tr), f(od),
              f([r["heading_recall"] for r in ok]), f(js), f"({len(js)})", f([r["seconds"] for r in rs]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topics"); ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=12); ap.add_argument("--report", action="store_true")
    ap.add_argument("--judge-url", default="http://localhost:11440"); ap.add_argument("--max-hours", type=float, default=6)
    a = ap.parse_args()
    report(Path(a.out)) if a.report else asyncio.run(run(a))
