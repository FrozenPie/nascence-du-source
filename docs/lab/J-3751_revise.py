"""J-3751 lab: re-measure study_note._REVISE_SYS with the full inputs (J-2961 build).
Read-only on live data (backup DB opened mode=ro). Hub calls only. Author arm qwen3.5:9b @11433,
judge arm gemma4:12b @11439 (different family). Outputs docs/lab/J-3751_data/.
Pairs: 6 Hume (old = fragment text in 2026-10-03 backup; new reading = a FRESH compose_note on the best-matching
book chunk, since the pass-2 raw note was never stored). Plus 1 synthetic Modest Proposal pair (old note
unrecoverable: the TAB file was overwritten by the revise)."""
import sys, os, re, json, sqlite3, time, urllib.request
sys.path.insert(0, "C:/Nascence")
from core import study_note as sn   # import core before anything lab_env-ish; no isolate needed (no writes)

OUT = "C:/Nascence/docs/lab/J-3751_data"; os.makedirs(OUT, exist_ok=True)
HOT = "http://localhost:11433"; JUDGE = "http://localhost:11440"
AUTH = "qwen3.5:9b"; JMODEL = "falcon3:7b"

def chat(url, model, system, user, max_tokens=1500, temperature=0.45, retry=1):
    body = {"model": model, "stream": False, "think": False, "format": "json",
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    for i in range(retry + 1):
        try:
            req = urllib.request.Request(url + "/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=240))
            txt = r["message"]["content"]
            m = re.search(r"\{.*\}", txt, re.S)
            return json.loads(m.group(0))
        except Exception as e:
            print("  call failed:", repr(e)[:120]); time.sleep(3)
    return None

async def call_json(base_urls, system, user, max_tokens=1500, temperature=0.45):
    return chat(HOT, AUTH, system, user, max_tokens, temperature)

import asyncio
def run(c): return asyncio.run(c)

def toks(s): return set(w for w in re.findall(r"[a-z]{3,}", s.lower()) if w not in sn._LEX_STOP)
def jac(a, b):
    A, B = toks(a), toks(b); return len(A & B) / max(1, len(A | B))

def parse_old(content):
    m = re.match(r"\[My study note:[^\]]*\]\s*(.*)", content, re.S); t = m.group(1) if m else content
    thoughts = ""
    m = re.search(r"\s+Thoughts:\s*(.*)$", t, re.S)
    if m: thoughts = m.group(1); t = t[:m.start()]
    facts = []
    m = re.search(r"\s+Facts:\s*(.*)$", t, re.S)
    if m: facts = [f.strip() for f in m.group(1).split("; ") if f.strip()]; t = t[:m.start()]
    return {"understanding": t.strip(), "key_facts": facts, "thoughts": thoughts}

def old_body(o):  # the shape _write_one hands _revise (rendered note body)
    return sn._render_body({"understanding": o["understanding"], "key_facts": o["key_facts"], "thoughts": o["thoughts"], "connects_to": "", "question": ""})

def best_chunk(book, ref, size=5000):
    best = (0, 0); R = toks(ref)
    step = 1500
    for p in range(0, max(1, len(book) - size), step):
        c = book[p:p + size]; s = len(R & toks(c)) / (len(R) or 1)
        if s > best[0]: best = (s, p)
    return book[best[1]:best[1] + size], best

def old_prompt(existing_body, new_note):  # control arm: the pre-J-2961 inputs (F-3649 shape)
    return (f"MY EXISTING NOTE:\n{existing_body[:2500]}\n\nWHAT I JUST READ (on {new_note['subject']}):\n{new_note['understanding']}\n"
            + ("Facts: " + "; ".join(new_note["key_facts"]) if new_note["key_facts"] else ""))

JUDGE_SYS = ("/no_think\nYou grade a revised study note. You get the OLD note, the NEW READING (what was just read), and the REVISED note. "
    "Answer ONLY JSON: {\"thoughts_reflect_new\": 0-2, \"connects_reflect_new\": 0-2, \"question_reflect_new\": 0-2, "
    "\"integrates_both\": 0-2, \"why\": \"one sentence\"} where 0 = reflects only the old note or is empty/copied, 1 = partly, "
    "2 = clearly reflects the new reading (for integrates_both: 2 = clear content from BOTH old and new, 0 = only one).")

def lens(s): return len(s or "")

def metrics(old, new_read, rev):
    ofacts, nfacts = old["key_facts"], rev["key_facts"]
    kept = sum(1 for f in ofacts if any(jac(f, g) >= 0.3 for g in nfacts))
    from_new = sum(1 for g in nfacts if any(jac(g, f) >= 0.3 for f in new_read["key_facts"]))
    return {"old_facts": len(ofacts), "new_read_facts": len(new_read["key_facts"]), "rev_facts": len(nfacts),
            "old_retained": kept, "rev_facts_matching_new_read": from_new,
            "union_facts": len(ofacts) + len(new_read["key_facts"]),
            "old_len": len(old["understanding"]), "new_read_len": len(new_read["understanding"]), "rev_len": len(rev["understanding"]),
            "thoughts_jac_old": round(jac(rev["thoughts"], old["thoughts"]), 2), "thoughts_jac_new": round(jac(rev["thoughts"], new_read["thoughts"]), 2),
            "connects_jac_new": round(jac(rev["connects_to"], new_read["connects_to"]), 2),
            "question_jac_new": round(jac(rev["question"], new_read["question"]), 2),
            "question_empty": not rev["question"], "connects_empty": not rev["connects_to"]}

def judge(old, new_read, rev):
    u = ("OLD NOTE:\n" + old_body(old) + "\n\nNEW READING:\n" + sn._render_body(new_read) + "\n\nREVISED NOTE:\n" + sn._render_body(rev))
    return chat(JUDGE, JMODEL, JUDGE_SYS, u, 400, 0.1)

def main():
    book = open("C:/Nascence/data/books/An_Enquiry_Concerning_Human_Understanding.txt", encoding="utf-8", errors="ignore").read()
    c = sqlite3.connect("file:C:/Nascence/data/backups/nascence_20261003_065435.db?mode=ro", uri=True)
    ids = ["870e1678", "d7e95375", "17382f92", "2e6f7554", "ad9a08a5", "666b78ec"]
    pairs = []
    for fid in ids:
        r = c.execute("select content from memory_fragments where fragment_id like ?", (fid + "%",)).fetchone()
        pairs.append((fid, "An Enquiry Concerning Human Understanding", book, parse_old(r[0])))
    mp = open("C:/Nascence/data/books/A_Modest_Proposal_For_preventing_the_children_of_poor_people.txt", encoding="utf-8", errors="ignore").read()
    rows = []
    # Modest synthetic: old = compose of first half, new reading = compose of second half (original old note unrecoverable)
    h = len(mp) // 2
    for fid, title, bk, old in pairs + [("MODEST", "A Modest Proposal", mp, None)]:
        print("==", fid, flush=True)
        if old is None:
            o = run(sn.compose_note(call_json, [HOT], title, mp[:h][-5000:]));
            if not o: print("modest old compose failed"); continue
            old = {"understanding": o["understanding"], "key_facts": o["key_facts"], "thoughts": o["thoughts"]}
            passage = mp[h:h + 5000]; srcpos = "second half"
        else:
            ref = old["understanding"] + " " + " ".join(old["key_facts"])
            passage, bc = best_chunk(bk, ref); srcpos = f"chunk@{bc[1]} score {bc[0]:.2f}"
        nr = run(sn.compose_note(call_json, [HOT], title, passage))
        if not nr: print("  new reading failed"); continue
        ex = {"connects_to": "", "question": ""}  # old note's own file connects_to/question unrecoverable (file revised since)
        body = old_body(old)
        t0 = time.time()
        new_rev = run(sn._revise(call_json, [HOT], body, nr, existing_extra=ex))
        ctl = chat(HOT, AUTH, sn._REVISE_SYS, old_prompt(body, nr), 1500, 0.45)
        ctl = sn._norm(ctl) if ctl and str(ctl.get("understanding") or "").strip() else None
        row = {"id": fid, "passage": srcpos, "old": old, "new_read": nr, "new_prompt_rev": new_rev, "old_prompt_rev": ctl}
        if new_rev: row["m_new_prompt"] = metrics(old, nr, new_rev); row["judge_new_prompt"] = judge(old, nr, new_rev)
        if ctl: row["m_old_prompt"] = metrics(old, nr, ctl); row["judge_old_prompt"] = judge(old, nr, ctl)
        rows.append(row)
        print("  ", row.get("m_new_prompt"), row.get("judge_new_prompt"), flush=True)
        print("   ctl", row.get("m_old_prompt"), row.get("judge_old_prompt"), flush=True)
        json.dump(rows, open(OUT + "/results.json", "w"), indent=1)

if __name__ == "__main__":
    main()
