"""
Hermetic test for J-3190 / D-0577: a long reading session becomes ONE study note PER ~5000-character chunk
(core/study_note.py _chunk_session / _pick_chunks / _sitting_spans / write_or_revise / store_note frontmatter).

No LLM, no embedder, no live data: runs INSIDE lab_env.isolate(db="empty") with the chunking log and the study
dir redirected into the lab dir; store._embed is a deterministic fake; compose_note records what each model call
was handed. The real store_note writes the TAB file, so the frontmatter assertions read the real file.

  [1] _chunk_session: <=5000 -> one chunk; a 6000 sitting -> two near-equal chunks; 24000 -> 5 chunks, each
      <=5000, every cut on a sentence end, no word lost or split, no tiny tail
  [2] a sentence-less text still never cuts mid-word; a single unbroken word run is cut only as a last resort
  [3] _pick_chunks: all up to the cap; past it, evenly spread, first and last included
  [4] _sitting_spans: exact when 'chars' add up; estimated (exact=False) when they do not
  [5] write_or_revise, 4 sittings (~5800 each): cap bites (3 notes of 5 chunks), every compose call <=5000,
      frontmatter records the sittings and characters that note's model call saw; chunking-log row written
  [6] a short session is unchanged: one compose call with the whole passage, session passed through untouched
  [7] same-call revision: a chunk that revises an earlier chunk's note keeps both chunks' sittings in the frontmatter

Run:  python scripts/study_note_chunking_test.py   (from the tree under test)
"""
from __future__ import annotations
import asyncio, json, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # BEFORE lab_env (F-2423): the tree under test must win on sys.path
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import numpy as np
from core import study_note as sn
from core.memory import store
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

WORDS = ("river stone bridge candle harbour weather orchard kettle lantern meadow copper thistle "
         "granite ferry willow ember compass ledger quarry saddle").split()

def prose(n_chars: int, seed: int = 0) -> str:
    """Sentences of 6-14 words, deterministic; at least n_chars long, ends on a full stop."""
    out, i = [], seed
    while sum(len(x) + 1 for x in out) < n_chars:
        k = 6 + (i * 7) % 9
        out.append(" ".join(WORDS[(i + j * 3) % len(WORDS)] for j in range(k)).capitalize() + ".")
        i += 1
    return " ".join(out)

def words(t: str):
    return t.split()

# ---------------------------------------------------------------- [1] chunking
print("[1] _chunk_session")
p = prose(4900)
check("<=5000 chars -> exactly one chunk spanning everything", sn._chunk_session(p) == [(0, len(p))])
p6 = prose(6000)
sp = sn._chunk_session(p6)
check("a 6000-char sitting -> two chunks, both <=5000, near-equal (not 5000 + a 1000 tail)",
      len(sp) == 2 and all(b - a <= 5000 for a, b in sp) and abs((sp[0][1] - sp[0][0]) - (sp[1][1] - sp[1][0])) < 800)
p24 = prose(24000)
sp = sn._chunk_session(p24)
chunks = [p24[a:b].strip() for a, b in sp]
check("24000 chars -> ceil(len/5000) chunks", len(sp) == -(-len(p24) // 5000))
check("every chunk <=5000 and non-trivial", all(len(c) <= 5000 and len(c) > 2000 for c in chunks))
check("every chunk but the last ends on a sentence end", all(c.endswith(".") for c in chunks))
check("no word lost, none split: the chunks' words concatenate to the passage's words",
      [w for c in chunks for w in words(c)] == words(p24))
check("spans contiguous apart from skipped whitespace", all(p24[sp[i][1]:sp[i + 1][0]].strip() == "" for i in range(len(sp) - 1)))
check("a chunk never begins mid-word", all(a == 0 or p24[a - 1].isspace() for a, _ in sp))

# ---------------------------------------------------------------- [2] no sentences / no spaces
print("[2] no sentence ends")
nos = " ".join(WORDS[i % len(WORDS)] for i in range(2400))        # ~16000 chars, no punctuation
sp = sn._chunk_session(nos)
cs = [nos[a:b].strip() for a, b in sp]
check("sentence-less text: cut on whitespace, words intact, chunks <=5000",
      all(len(c) <= 5000 for c in cs) and [w for c in cs for w in words(c)] == words(nos))
blob = "x" * 12000
check("an unbroken run with no space is still chunked (last resort) and loses nothing",
      sum(b - a for a, b in sn._chunk_session(blob)) == 12000 and all(b - a <= 5000 for a, b in sn._chunk_session(blob)))

# ---------------------------------------------------------------- [3] pick
print("[3] _pick_chunks")
check("under the cap -> all", sn._pick_chunks(2, 3) == [0, 1] and sn._pick_chunks(3, 3) == [0, 1, 2])
check("24 chunks, cap 3 -> first, middle, last", sn._pick_chunks(24, 3) == [0, 12, 23])
check("5 chunks, cap 3 -> 0, 2, 4", sn._pick_chunks(5, 3) == [0, 2, 4])
check("cap 1 -> first", sn._pick_chunks(9, 1) == [0])

# ---------------------------------------------------------------- [4] sitting spans
print("[4] _sitting_spans / _sub_session")
sits = [{"encounter_id": f"e{i}", "pass": 0, "chars": c} for i, c in enumerate([100, 50, 80])]
text = "a" * 100 + "\n" + "b" * 50 + "\n" + "c" * 80
spans, exact = sn._sitting_spans(text, sits)
check("exact spans when chars + separators == len(passage)", exact and spans == [(0, 100), (101, 151), (152, 232)])
sub = sn._sub_session(sits, spans, exact, 90, 160)
check("chunk [90,160) overlaps all three sittings with 10 / 50 / 8 chars",
      [x["encounter_id"] for x in sub] == ["e0", "e1", "e2"] and [x["seen_chars"] for x in sub] == [10, 50, 8]
      and not any(x["seen_est"] for x in sub))
spans2, exact2 = sn._sitting_spans(text + "zzz", sits)
check("chars that do not add up -> estimated, evenly laid out", not exact2 and len(spans2) == 3)

# ---------------------------------------------------------------- [5]-[7] end to end
with isolate(also=[(sn, ["_CHUNK_LOG", "STUDY_DIR"])], db="empty") as lab_dir:
    assert "_lab" in str(store.DB_PATH), store.DB_PATH
    store._embed = lambda t: np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)   # every note a perfect duplicate: used only where find_revisable is live
    # keep the real store_note from touching the other knowledge stores -- not under test here
    import importlib
    for modname in ("sound_knowledge", "garden_knowledge", "garden_life", "wood_life", "shore_life", "life"):
        try:
            m = importlib.import_module(f"core.{modname}")
            m.learn_from_text = lambda *a, **k: None
        except Exception:
            pass
    sn._related_context = lambda bt, pa: ("", [])
    sn._log_m1_co_recall = lambda *a, **k: None
    sn._first_sentence = lambda t: ""                      # no follow-line boarding
    seen_prompts = []
    counter = {"n": 0}
    async def fake_compose(call_json, base_urls, book_title, passage, related_text=""):
        seen_prompts.append(passage)
        counter["n"] += 1
        return {"title": f"Chunk note {counter['n']}", "subject": f"subject {counter['n']}", "key_facts": [], "thoughts": "",
                "connects_to": "", "question": "", "understanding": f"I see that thing number {counter['n']} holds."}
    sn.compose_note = fake_compose
    sn.find_revisable = lambda n, **k: None                # no dedup hit: all chunks store NEW (the gate itself is tested in study_note_reread_test)

    def frontmatter(res):
        return Path(res["path"]).read_text(encoding="utf-8").split("\n")[2]

    print("[5] four ~5800-char sittings -> cap bites")
    sit_texts = [prose(5800, seed=s * 11) for s in range(4)]
    sit_texts = [t[: t.rfind(".") + 1] for t in sit_texts]
    session = [{"encounter_id": f"enc{i}", "book": "b", "title": "T", "offset": i * 6000, "pass": 0, "chars": len(t)}
               for i, t in enumerate(sit_texts)]
    passage = "\n".join(sit_texts)
    n_chunks = len(sn._chunk_session(passage))
    out = asyncio.run(sn.write_or_revise(None, [], "The Book of Rivers", passage, session=session))
    check(f"{n_chunks} chunks in the session, capped at {sn._MAX_NOTES_PER_SESSION} notes",
          n_chunks > sn._MAX_NOTES_PER_SESSION and out["chunks_total"] == n_chunks and out["chunks_made"] == sn._MAX_NOTES_PER_SESSION
          and out["capped"] and len(out["notes"]) == sn._MAX_NOTES_PER_SESSION and out["action"] == "new")
    check("every compose call was handed <=5000 characters, none cut mid-word",
          len(seen_prompts) == sn._MAX_NOTES_PER_SESSION and all(len(x) <= 5000 for x in seen_prompts)
          and all(x == x.strip() and x.endswith(".") for x in seen_prompts))
    fm = [frontmatter(o) for o in out["notes"]]
    for f in fm:
        print("      ", f)
    check("each TAB frontmatter says pass, sittings and chars (exact, no '(est.)')",
          all(re.search(r"pass: 0 · sittings: \d+ · chars: \d+\*$", f) and "(est.)" not in f for f in fm))
    seen_total = sum(int(re.search(r"chars: (\d+)", f).group(1)) for f in fm)
    check("chars recorded == the characters those prompts held (within whitespace)",
          abs(seen_total - sum(len(x) for x in seen_prompts)) <= 8)
    first_sittings = int(re.search(r"sittings: (\d+)", fm[0]).group(1))
    check("the first note saw only the opening sitting(s), not the whole stretch's four", 1 <= first_sittings < 4)
    log_rows = [json.loads(l) for l in (lab_dir / "study_note_chunking_log.jsonl").read_text(encoding="utf-8").splitlines()]
    check("chunking log row: chunks_total, capped, notes, seen_share",
          len(log_rows) == 1 and log_rows[0]["capped"] is True and log_rows[0]["notes"] == 3
          and log_rows[0]["chunks_total"] == n_chunks and 0.0 < log_rows[0]["seen_share"] < 1.0 and log_rows[0]["sittings"] == 4)

    print("[6] short session unchanged")
    seen_prompts.clear()
    short = prose(3000)
    s1 = [{"encounter_id": "only", "pass": 1, "chars": len(short)}]
    out = asyncio.run(sn.write_or_revise(None, [], "Short Book", short, session=s1))
    fm = frontmatter(out)
    check("one compose call, whole passage; one note; no chunk keys", seen_prompts == [short] and "notes" not in out and out["action"] == "new")
    check("frontmatter: pass 1, sittings 1, and no chars field (session untouched, as before D-0577)",
          "pass: 1 · sittings: 1" in fm and "chars:" not in fm)
    out = asyncio.run(sn.write_or_revise(None, [], "Short Book", short))
    check("no session at all still works (no sittings in frontmatter)", out["action"] == "new" and "sittings" not in frontmatter(out))

    print("[7] same-call revision keeps both chunks' sittings")
    seen_prompts.clear()
    state = {"fid": None}
    def fake_find(note, book_pass=None):
        # chunk 1: nothing to revise; chunk 2 onward: revise the note chunk 1 just stored
        return None if state["fid"] is None else (state["fid"], "old body", state["path"])
    orig_store = sn.store_note
    def spy_store(note, book_title, revise_target=None, session=None, **kw):   # J-2961: forwards `prior`
        r = orig_store(note, book_title, revise_target=revise_target, session=session, **kw)
        if state["fid"] is None:
            state["fid"], state["path"] = r["fragment_id"], r["path"]
        return r
    async def fake_revise(call_json, base_urls, existing_body, new_note, **kw):   # J-2961: + existing_extra
        return dict(new_note)
    sn.find_revisable, sn.store_note, sn._revise = fake_find, spy_store, fake_revise
    two = [prose(5400, seed=3), prose(5400, seed=9)]
    two = [t[: t.rfind(".") + 1] for t in two]
    s2 = [{"encounter_id": f"x{i}", "pass": 0, "chars": len(t)} for i, t in enumerate(two)]
    out = asyncio.run(sn.write_or_revise(None, [], "Revise Book", "\n".join(two), session=s2))
    revised = [o for o in out["notes"] if o["action"] == "revised"]
    fm = Path(state["path"]).read_text(encoding="utf-8").split("\n")[2]
    print("      ", fm)
    total_chars = sum(len(t) for t in two)
    check("chunk 2 revised chunk 1's note", len(out["notes"]) >= 2 and len(revised) >= 1)
    check("its frontmatter now lists both sittings and both chunks' characters, marked revised",
          "revised" in fm and "sittings: 2" in fm and abs(int(re.search(r"chars: (\d+)", fm).group(1)) - total_chars) <= 8)

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
