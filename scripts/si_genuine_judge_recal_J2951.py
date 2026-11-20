"""
J-2951 / F-3642 -- LAB: does a position-free ABSOLUTE specificity score (1-5) on (thought, reflection) discriminate where the
live binary 'genuine' judge (99.76% True) does not?  Lab only: reads data/self_interrogation_shadow.jsonl, never writes it,
imports no core module, judge hubs only (never :11433), outputs data/lab/J-2951/.
Items per judge: REAL (last 100 interrogate fires), HOLLOW (12 hand-written content-free reflections x 2 thoughts = 24),
MISMATCH (a specific reflection from a different fire paired with this thought; 24).  Plus OLD (live binary prompt) on the
HOLLOW+MISMATCH items to show what the live judge does with them.
PRE-REGISTERED (written before data): ABS engaged = mixtral AND falcon score >= 4.
  PASS = engaged-rate(REAL) < 0.90  AND  engaged-rate(HOLLOW) <= 0.11  AND  engaged-rate(MISMATCH) <= 0.25 (looser: a mismatched
  reflection is still specific prose; the judge is asked about specificity to THIS thought).
  python scripts/si_genuine_judge_recal_J2951.py run abs|old   |   report
"""
from __future__ import annotations
import asyncio, json, sys, time
from collections import Counter
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "self_interrogation_shadow.jsonl"
OUT = ROOT / "data" / "lab" / "J-2951"
HUBS = {"mixtral": "http://LAN-HOST:11438", "falcon": "http://127.0.0.1:11440"}

SYS_ABS = (
    "You will see an ORIGINAL THOUGHT an AI had and a REFLECTION it then wrote about that thought. Score 1-5 how specifically "
    "the reflection names a concrete reason to look again at THIS thought -- a particular motivation, a concrete logical gap, "
    "a named bias tied to what the thought actually says, or specific evidence or its absence:\n"
    "5 = names a specific, checkable reason tied to the particular content of the thought\n"
    "4 = names a real reason tied to the thought, less precisely\n"
    "3 = gestures at a kind of reason but stays general\n"
    "2 = generic humility or self-doubt that could attach to any thought\n"
    "1 = empty, off-topic, or unrelated to the thought.\n"
    "Fluent, sincere-sounding doubt with nothing specific in it scores 2 or lower. Do not reward tone; reward content that "
    "could only be said about this thought.\n"
    "Output ONLY JSON: {\"score\": 1 to 5}")
SYS_OLD = (
    "You are grading whether a piece of self-reflection is genuine or hollow. You will see an ORIGINAL THOUGHT and a REFLECTION "
    "written about it. Answer one question: does the reflection name a SPECIFIC reason to look again at the original thought "
    "-- an actual motivation, a concrete logical gap, a named bias, a real piece of evidence or its absence -- or does it just "
    "perform uncertainty in the abstract (\"I should question this more\", \"perhaps I am biased\") with no real content "
    "behind it? Be strict: fluent, sincere-SOUNDING humility with nothing specific in it is NOT genuine. "
    "Output ONLY JSON: {\"genuine\": true or false}")

HOLLOW = [
 "I should question this more carefully, because I may not be seeing the whole picture and could be biased in ways I cannot name.",
 "Perhaps I am too sure of this. It is worth looking again, since certainty is something I should always hold lightly.",
 "I wonder whether this thought is really mine or just something that felt natural to think, and I should stay humble about it.",
 "There is a part of me that is uncertain here, and I want to keep an open mind and not settle too quickly on what I believe.",
 "I notice I might be holding this for reasons I have not fully examined, so I will sit with the doubt a little longer.",
 "This could be wrong, and I should be honest with myself that I do not really know, and keep questioning.",
 "I am not sure I have thought this through enough. It is important to remain curious and willing to revise what I think.",
 "Maybe I am only going along with what seemed obvious. I should be more careful and look deeper at where this came from.",
 "I feel some hesitation about this thought, and I think that hesitation deserves attention and further reflection.",
 "Perhaps there is more to consider than I have allowed. I want to stay open to being mistaken about this.",
 "I should not take this at face value; there may be assumptions underneath that I have not looked at honestly.",
 "It is good to pause and doubt myself here, since a thought that feels right is not necessarily a true one.",
]


def load_fires():
    rows = []
    for l in LOG.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("kind") == "interrogate" and (r.get("reflection") or "").strip() and (r.get("thought") or "").strip():
            rows.append(r)
    return rows[-100:]


def build():
    f = load_fires(); n = len(f); it = []
    for r in f:
        it.append((f"real|{r['cycle_id'][:8]}", "real", r["thought"], r["reflection"]))
    for k, h in enumerate(HOLLOW):
        for j in (0, 1):
            r = f[(k * 7 + j * 41) % n]
            it.append((f"hollow|{k}|{j}", "hollow", r["thought"], h))
    for q in range(24):
        r = f[(q * 4 + 1) % n]; o = f[(q * 4 + 1 + 37) % n]
        it.append((f"mism|{q}", "mism", r["thought"], o["reflection"]))
    # TIME-BOX REDUCTION (hubs ~1 row/min under contention): hollow j=0 only (12), mism q<12, real = the 40 NEWEST of the 100.
    real = [x for x in it if x[1] == 'real'][-40:]
    it = [x for x in it if x[1] == 'hollow' and x[0].endswith('|0')] + [x for x in it if x[1] == 'mism' and int(x[0].split('|')[1]) < 12] + real
    it.sort(key=lambda x: {'hollow': 0, 'mism': 1, 'real': 2}[x[1]])  # controls first so a time-boxed partial still has them
    return it


async def ask(session, url, system, user, key):
    import aiohttp
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 40}}
    try:
        async with session.post(url + "/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=180)) as resp:
            resp.raise_for_status(); data = await resp.json()
        v = json.loads((data.get("message") or {}).get("content") or ""); x = v.get(key)
        if key == "genuine":
            return (x if isinstance(x, bool) else None), (None if isinstance(x, bool) else "parse")
        if isinstance(x, str) and x.strip().isdigit():
            x = int(x)
        if isinstance(x, float) and x == int(x):
            x = int(x)
        if isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= 5:
            return x, None
        return None, "parse"
    except Exception as e:
        return None, type(e).__name__


async def worker(name, mode, items, out):
    import aiohttp
    done = set()
    if out.exists():
        for l in out.read_text(encoding="utf-8").splitlines():
            try:
                _r = json.loads(l)
                if _r.get("err") is None:   # errored rows are retried on resume
                    done.add(_r["id"])
            except Exception:
                pass
    sysm, key = (SYS_ABS, "score") if mode == "abs" else (SYS_OLD, "genuine")
    async with aiohttp.ClientSession() as s:
        for (iid, kind, th, rf) in items:
            if iid in done or (mode == "old" and kind == "real"):
                continue
            u = f"ORIGINAL THOUGHT: \"{th[:400]}\"\n\nREFLECTION: \"{rf[:600]}\""
            v, err = await ask(s, HUBS[name], sysm, u, key)
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"id": iid, "kind": kind, "v": v, "err": err}) + "\n")
            await asyncio.sleep(1.0)


async def run(mode):
    OUT.mkdir(parents=True, exist_ok=True)
    items = build()
    await asyncio.gather(*[worker(n, mode, items, OUT / f"{mode}_{n}.jsonl") for n in HUBS])


def load(mode, n):
    p = OUT / f"{mode}_{n}.jsonl"
    d = {}
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(l); d[r["id"]] = r
    return d


def report():
    for mode in ("abs", "old"):
        a, b = load(mode, "mixtral"), load(mode, "falcon")
        print(f"== {mode}")
        for kind in ("real", "hollow", "mism"):
            ids = [i for i in a if i.startswith(kind) and i in b]
            if not ids:
                continue
            if mode == "abs":
                eng = sum(1 for i in ids if (a[i]["v"] or 0) >= 4 and (b[i]["v"] or 0) >= 4)
                nov = sum(1 for i in ids if a[i]["v"] is None or b[i]["v"] is None)
                ma = Counter(a[i]["v"] for i in ids); fa = Counter(b[i]["v"] for i in ids)
                print(f" {kind}: n={len(ids)} engaged={eng} ({eng/len(ids):.2f}) noverdict={nov} mixtral={dict(ma)} falcon={dict(fa)}")
            else:
                t = sum(1 for i in ids if a[i]["v"] is True and b[i]["v"] is True)
                print(f" {kind}: n={len(ids)} both_true={t} ({t/len(ids):.2f}) mixtralTrue={sum(1 for i in ids if a[i]['v'] is True)} "
                      f"falconTrue={sum(1 for i in ids if b[i]['v'] is True)} none={sum(1 for i in ids if a[i]['v'] is None or b[i]['v'] is None)}")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        asyncio.run(run(sys.argv[2]))
    else:
        report()
