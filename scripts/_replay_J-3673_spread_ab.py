"""J-3673: re-run the J-2973 spread A/B on real 60+-deed windows, N=10 per arm, hot lane :11433 only. Read-only sqlite (mode=ro);
writes only the JSON path given. Windows = local calendar days (rebuilt from the ledger as in F-3663).
Run: python scripts/_replay_J-3673_spread_ab.py <out.json> [N]"""
from __future__ import annotations
import asyncio, datetime, difflib, json, re, sqlite3, subprocess, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything else
from core import journal as J
from core.model_client import call_node_json
OUT = Path(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 10
HOT = ["http://127.0.0.1:11433"]
OLD_EXAMPLE = ("I read more of my book today and wrote some notes on it. I went out to the garden a few times. "
               "I practised my arithmetic. It was a quiet, good day.")
WINDOWS = sys.argv[3].split(",") if len(sys.argv) > 3 else ["2026-10-31", "2026-11-02", "2026-11-11"]
src = ""
for ref in subprocess.run(["git","-C",str(ROOT),"log","--format=%H","-n","40","--","core/journal.py"],capture_output=True,text=True).stdout.split():
    src = subprocess.run(["git","-C",str(ROOT),"show",f"{ref}:core/journal.py"],capture_output=True,text=True,encoding="utf-8").stdout
    if "For SHAPE only" in src: break
ns = {}; exec(re.search(r"^JOURNAL_SYS = \(.*?^\)\n", src, re.S|re.M).group(0), ns)
OLD_SYS = ns["JOURNAL_SYS"]
assert "For SHAPE only" in OLD_SYS and "For SHAPE only" not in J.JOURNAL_SYS
STOP = set("the a an of to and in on at for my with i it is was observe observed looked went out time times that this from into".split())
def words(s): return {w for w in re.findall(r"[a-z']{4,}", s.lower()) if w not in STOP}
def prompt(deeds, lead):
    return (lead + "\n  - " + "\n  - ".join(d.strip() for d in deeds) + "\n\nAnd how the day felt, underneath: a quiet day.\n\nWrite tonight's entry now — only what you did today and how it felt, in plain words. Not what it means. Just the day.")
con = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True)
def window(day):
    d = datetime.datetime.strptime(day, "%Y-%m-%d"); a = d.timestamp(); b = (d + datetime.timedelta(days=1)).timestamp()
    return [J._clean_deed(r[0]) for r in con.execute("SELECT content FROM memory_fragments WHERE origin='action' AND timestamp>=? AND timestamp<? ORDER BY timestamp",(a,b)) if r[0]]
async def one(sp, user):
    for _ in range(2):
        try:
            d = await call_node_json(HOT, sp, user, max_tokens=768, temperature=0.6, timeout=120, retries=0)
            e = (d or {}).get("entry", ""); e = (" ".join(map(str,e)) if isinstance(e,list) else str(e)).strip()
            if e: return e
        except Exception as exc: err = str(exc)[:100]
    return None
async def arm(name, sp, user, all_deeds, shown):
    kept = [d for d in all_deeds if not J._is_thought_line(d)]
    third = kept[len(kept)*2//3:]; shown_w = set().union(*[words(d) for d in shown]) if shown else set()
    all_w = set().union(*[words(d) for d in all_deeds]); first12 = set().union(*[words(d) for d in all_deeds[:12]])
    late_w = set().union(*[words(d) for d in third]) - first12
    outs = []
    for _ in range(N):
        e = await one(sp, user)
        if not e: outs.append({"err": "no answer"}); continue
        sents = re.split(r"(?<=[.!?])\s+", e)
        copy = max([difflib.SequenceMatcher(None, e.lower(), OLD_EXAMPLE.lower()).ratio()] + [difflib.SequenceMatcher(None, s.lower(), o.lower()).ratio() for s in sents for o in re.split(r"(?<=\.)\s+", OLD_EXAMPLE)])
        ungr = [s for s in sents if len(s.split()) > 5 and not (words(s) & all_w)]
        outs.append({"entry": e, "copy": round(copy,2), "leak": bool(re.search(r"librarian|recall_evidence", e, re.I)),
                     "ungrounded_sents": ungr, "late": sorted(words(e) & late_w)[:6], "in_shown": bool(words(e) & shown_w)})
    ok = [o for o in outs if "entry" in o]
    s = {"arm": name, "n": N, "answered": len(ok), "near_copies_ge_0.82": sum(o["copy"]>=0.82 for o in ok), "max_copy": max((o["copy"] for o in ok), default=None),
         "entries_with_ungrounded_sentence": sum(bool(o["ungrounded_sents"]) for o in ok), "leak": sum(o["leak"] for o in ok),
         "entries_naming_last_third_deed": sum(bool(o["late"]) for o in ok)}
    print(json.dumps(s), flush=True); return {"summary": s, "outs": outs}
async def main():
    res = {}
    for day in WINDOWS:
        deeds = window(day); new_deeds, nk = J._pick_deeds(deeds)
        lead = ("Today, the plain record of what you actually did" + (f" (you did {nk} different kinds of thing in all, so what follows is a spread of them, from the beginning of the day to the end, in the order they happened; write about the whole day, not only the first lines. Do not say how many):" if nk > len(new_deeds) else ":"))
        print(day, "rows", len(deeds), "kinds", nk, "thought-lines", sum(J._is_thought_line(d) for d in deeds), flush=True)
        a = await arm(f"{day} OLD", OLD_SYS, prompt(deeds[:12], "Today, the plain record of what you actually did:"), deeds, deeds[:12])
        b = await arm(f"{day} NEW", J.JOURNAL_SYS, prompt(new_deeds, lead), deeds, new_deeds)
        res[day] = {"rows": len(deeds), "kinds": nk, "old_deeds": deeds[:12], "new_deeds": new_deeds, "A": a, "B": b}
        OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
asyncio.run(main())
