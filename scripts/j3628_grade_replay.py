"""J-3628: replay the D-0585 two-number essay grader on 6 essays (old window vs new). Local judge-1 hub only.
Usage: python scripts/j3628_grade_replay.py <lineage.json> <outdir>
lineage.json = {name: {"essay": str, "sources": [{"id","content","origin"}]}} (built read-only from the DB edges;
file: ids are resolved here against data/Study). Writes <outdir>/results.jsonl; touches no live store."""
import sys, json, asyncio, re, time
from pathlib import Path
sys.path.insert(0, "C:/Nascence")
import core, core.left_lane as ll                       # core BEFORE lab_env
assert core.__file__.replace("\\", "/").startswith("C:/Nascence/"), core.__file__
sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
import lab_env
import aiohttp
from core import emissary as _emissary
from core.study import STUDY_DIR, NOTES_SUBDIR

OLD_TASK = (
    "TASK (grade a capstone essay): The Master has finished a book and written an essay on what it taught "
    "him about the world. You are the truth-self \u2014 judge how GROUNDED the essay is in what the book actually "
    "says: are its claims solid, factual, about the book's real subject? Or has it drifted into his own "
    "impression, metaphor, or self-reflection? You are given his notes on the book as the reference. Be a "
    "fair but honest examiner \u2014 reward real grasp of the world, mark down vagueness and self-projection.\n"
    "Output ONLY a valid JSON object. No preamble.\n"
    "Schema: {\"grounded\": 0.0, \"feedback\": \"one sentence: what was solid, what was thin\"}  "
    "(grounded is 0.0..1.0: 1.0 = every claim solid and about the world; 0.0 = mostly impression/metaphor)"
)   # verbatim from `git show f17b0612^:core/left_lane.py`

def clip(t): return " ".join((t or "").split())[:500]

def file_note(fid):
    name = fid[len("file:"):]
    for p in list(STUDY_DIR.glob(name + "*")) + list(NOTES_SUBDIR.glob("*/" + name + "*")):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        return clip(txt.split("*\n\n", 1)[-1].strip() or txt)
    return None

def build(name, v):
    book, wider, missing = [], [], 0
    for s in v["sources"]:
        c = file_note(s["id"]) if s["id"].startswith("file:") else clip(s["content"])
        if not c: missing += 1; continue
        own = s["id"].startswith("file:") or s["origin"] == "understanding"
        (book if own else wider).append("- " + c if False else c)
    return "\n".join(book), "\n".join(wider), missing

async def grade_old(title, notes, essay):
    user = (f"The book: '{title}'.\n\nHis notes on it (the reference for what the book says):\n"
            f"{notes[:2500]}\n\nHis essay to grade:\n{essay[:2500]}")
    payload = {"model": ll.MODEL, "stream": False, "keep_alive": "30m",
               "messages": [{"role": "system", "content": _emissary.constitution() + "\n\n" + OLD_TASK},
                            {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": ll.MAX_TOKENS, "num_gpu": 0}, "format": "json"}
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{ll.BASE_URL}/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=ll.JUDGE_TIMEOUT_S)) as r:
            r.raise_for_status(); d = await r.json()
    return json.loads((d.get("message") or {}).get("content") or "")

def main():
    lin = json.load(open(sys.argv[1], encoding="utf-8")); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    ll.JUDGE_TIMEOUT_S = 900              # shared CPU hub is slow under load; the production 240 s would fail-open
    ll._note_call = lambda *a, **k: None  # no llm_calls.jsonl write
    done = set()
    rf = out / "results.jsonl"
    if rf.exists(): done = {json.loads(l)["name"] for l in rf.open(encoding="utf-8")}
    with lab_env.isolate(db="empty"):
        for name, v in lin.items():
            if name in done: continue
            book, wider, missing = build(name, v)
            essay = v["essay"]; t0 = time.time()
            row = {"name": name, "n_sources": len(v["sources"]), "missing_sources": missing, "book_chars": len(book),
                   "wider_chars": len(wider), "essay_chars": len(essay)}
            try:
                row["old"] = asyncio.run(grade_old(name, book + ("\n" + wider if wider else ""), essay))
            except Exception as e:
                row["old_err"] = repr(e)[:200]
            try:
                row["new"] = asyncio.run(ll.grade_essay(name, book, essay, wider_material=wider))
            except Exception as e:
                row["new_err"] = repr(e)[:200]
            row["secs"] = round(time.time() - t0, 1)
            with rf.open("a", encoding="utf-8") as f: f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(name, row.get("old"), row.get("new"), row["secs"], flush=True)
main()
