"""
J-2973 re-measure (F-3664: 5 of 71 stored entries were near-verbatim copies of the old SHAPE example). A small A/B on
the LOCAL hot lane only (:11433; Ramses is never called): the same live deed rows (read-only sqlite, mode=ro, last 30 h)
go to (A) the OLD prompt + OLD input (first 12 rows in time order, thought-lines included) and (B) the NEW prompt + NEW
input (a spread, no thought-lines). N entries each. Nothing is written to any live store: only a JSON result file in the
temp path given on the command line.

Measures per arm: copy = max difflib ratio of the entry against the old example; leak = entry names a
librarian/recall_evidence line; late = entry mentions a word from a deed that sits in the LAST THIRD of the window and
not in the first 12 rows.

Run:  python scripts/_replay_J-2973_journal_prompt_ab.py <out.json> [N]    (from the tree under test)
"""
from __future__ import annotations
import asyncio, difflib, json, re, sqlite3, subprocess, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything else (F-2423)
from core import journal as J
from core.model_client import call_node_json

OUT = Path(sys.argv[1]); N = int(sys.argv[2]) if len(sys.argv) > 2 else 8
HOT = ["http://127.0.0.1:11433"]
OLD_EXAMPLE = ("I read more of my book today and wrote some notes on it. I went out to the garden a few times. "
               "I practised my arithmetic. It was a quiet, good day.")

old_src = ""
for _ref in ("HEAD", "HEAD~1", "master"):   # the pre-J-2973 file (HEAD itself once J-2973 is committed)
    old_src = subprocess.run(["git", "-C", str(ROOT), "show", f"{_ref}:core/journal.py"], capture_output=True,
                             text=True, encoding="utf-8").stdout
    if "For SHAPE only" in old_src:
        break
ns: dict = {}
m = re.search(r"^JOURNAL_SYS = \(.*?^\)\n", old_src, re.S | re.M)
exec(m.group(0), ns)
OLD_SYS = ns["JOURNAL_SYS"]
assert "For SHAPE only" in OLD_SYS and "For SHAPE only" not in J.JOURNAL_SYS

con = sqlite3.connect("file:C:/Nascence/data/memory/nascence.db?mode=ro", uri=True)
rows = con.execute("SELECT content FROM memory_fragments WHERE origin='action' AND timestamp>=? ORDER BY timestamp",
                   (time.time() - 30 * 3600,)).fetchall()
con.close()
all_deeds = [J._clean_deed(r[0]) for r in rows if r[0]]
print("rows in window:", len(all_deeds), "thought-lines:", sum(J._is_thought_line(d) for d in all_deeds))

def _prompt(deeds, lead):
    return (lead + "\n  - " + "\n  - ".join(d.strip() for d in deeds)
            + "\n\nAnd how the day felt, underneath: a quiet day.\n\nWrite tonight's entry now — only what you did today "
              "and how it felt, in plain words. Not what it means. Just the day.")

old_deeds = all_deeds[:12]
new_deeds, n_kinds = J._pick_deeds(all_deeds)
old_user = _prompt(old_deeds, "Today, the plain record of what you actually did:")
new_lead = ("Today, the plain record of what you actually did"
            + (f" (you did {n_kinds} different kinds of thing in all, so what follows is a spread of them, from the "
               f"beginning of the day to the end, in the order they happened; write about the whole day, not only "
               f"the first lines. Do not say how many):" if n_kinds > len(new_deeds) else ":"))
new_user = _prompt(new_deeds, new_lead)

kept = [d for d in all_deeds if not J._is_thought_line(d)]
third = kept[len(kept) * 2 // 3:]
STOP = set("the a an of to and in on at for my with i it is was observe observed looked went out time times".split())
def words(s): return {w for w in re.findall(r"[a-z']{4,}", s.lower()) if w not in STOP}
first_words = set().union(*[words(d) for d in old_deeds]) if old_deeds else set()
late_words = set().union(*[words(d) for d in third]) - first_words

async def one(sys_p, user):
    try:
        d = await call_node_json(HOT, sys_p, user, max_tokens=768, temperature=0.6, timeout=90, retries=1)
    except Exception as exc:
        return {"err": str(exc)[:120]}
    e = (d or {}).get("entry", "")
    e = (" ".join(str(x) for x in e) if isinstance(e, list) else str(e)).strip()
    return {"entry": e}

async def arm(name, sys_p, user):
    res = []
    for _ in range(N):
        res.append(await one(sys_p, user))
    outs = []
    for r in res:
        e = r.get("entry", "")
        if not e:
            outs.append({"err": r.get("err", "empty")}); continue
        copy = max([difflib.SequenceMatcher(None, e.lower(), OLD_EXAMPLE.lower()).ratio()]
                   + [difflib.SequenceMatcher(None, s.lower(), o.lower()).ratio()
                      for s in re.split(r"(?<=[.!?])\s+", e) for o in re.split(r"(?<=\.)\s+", OLD_EXAMPLE)])
        outs.append({"entry": e, "copy_ratio": round(copy, 2),
                     "leak": bool(re.search(r"librarian|recall_evidence", e, re.I)),
                     "late_hit": sorted(words(e) & late_words)[:6]})
    ok = [o for o in outs if "entry" in o]
    summ = {"arm": name, "n": len(outs), "answered": len(ok),
            "max_copy_ratio": max((o["copy_ratio"] for o in ok), default=None),
            "near_copies_ge_0.82": sum(o["copy_ratio"] >= 0.82 for o in ok),
            "leak": sum(o["leak"] for o in ok), "late_hit_entries": sum(bool(o["late_hit"]) for o in ok)}
    print(json.dumps(summ))
    return {"summary": summ, "outs": outs}

async def main():
    a = await arm("OLD prompt + OLD input", OLD_SYS, old_user)
    b = await arm("NEW prompt + NEW input", J.JOURNAL_SYS, new_user)
    OUT.write_text(json.dumps({"rows": len(all_deeds), "old_deeds": old_deeds, "new_deeds": new_deeds,
                               "n_kinds": n_kinds, "A": a, "B": b}, ensure_ascii=False, indent=1), encoding="utf-8")
asyncio.run(main())
