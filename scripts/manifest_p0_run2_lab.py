"""J-2218 -- thought_cycle_as_manifest_loop P0 Run 2: the offline decompose replay, Du OFF, changes nothing.

Same 43 historic human turns as Run 1 (2026-07-06): the `[CYCLE <numeric>] human:` lines of data/nascence.log
dated <= 2026-07-03 (exactly 43; Run 1's own indices #1 conscious-question, #22 self-repertoire, #33 circle-math
line up with this set). Run 1's two named fixes are applied:

  fix 1 (data)   full-fidelity turn text pulled READ-ONLY from data/memory/nascence.db memory_fragments
                 (origin='lived': "[Travis said to me] X" > "Q: X\\nA:" > "Input: X"), not the ~80-char log preview;
  fix 2 (decode) JSON-schema grammar with ingredients capped at 1..4, need <= 160 chars, repeat/presence/frequency
                 penalties, low temperature, tighter prompt with a worked example and an explicit no-duplicate rule.

Arms:  A1 full-fidelity + tuned (seed 11) | A2 same, seed 23 (stability) | B truncated log text + tuned (isolates fix 1).

Isolation: no Nascence store is opened writable. The live DB is opened `mode=ro` once, before anything else, to read
fuel. All Nascence imports (core) happen inside lab_env.isolate(db="empty") so any accidental store touch lands in a
temp lab dir. Output: ONE jsonl + summary json under --out (a docs/lab path in the worktree). The live DB's sha256 is
taken before and after as a canary (note: other processes may legitimately write it; this script never does).
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, time, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (F-2423)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate, _hash_file  # noqa: E402

LIVE_LOG = Path(r"C:\Nascence\data\nascence.log")
LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
SEATS = {  # J-2218 2026-10-18: hot :11433 Ollama wedged ("maximum pending requests exceeded", F-3060) -> dreamer seat
    "hot": ("http://127.0.0.1:11433/api/chat", "MichelRosselli/bonsai-27b:latest"),
    "dreamer": ("http://127.0.0.1:11442/api/chat", "yi:34b-v1.5"),  # nascence_cpu_server.py: format str only
}
URL, MODEL = SEATS["hot"]
SEAT = "hot"
CUTOFF = "2026-07-03"

SCHEMA = {
    "type": "object",
    "properties": {
        "purpose": {"type": "string", "maxLength": 200},
        "regime": {"type": "string", "enum": ["closed", "identity", "open", "relational", "recall"]},
        "ingredients": {
            "type": "array", "minItems": 1, "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "need": {"type": "string", "maxLength": 160},
                    "type": {"type": "string", "enum": ["fact", "epistemic", "episodic", "affect", "identity", "relational"]},
                    "lane": {"type": "string", "enum": ["emissary", "dreamer"]},
                    "vehicle": {"type": "string", "enum": ["inline", "deferred"]},
                },
                "required": ["need", "type", "lane", "vehicle"],
            },
        },
    },
    "required": ["purpose", "regime", "ingredients"],
}

SYSTEM = """You are a routing gate (a thalamic relay), not a thinker. You never answer the message.
You split one incoming message into 1 to 4 DISTINCT ingredients that must be collected before a reply can be
complete, and tag each with where it is picked up for analysis.

Types: fact (a checkable fact or computation), epistemic (do I know this / how sure am I), episodic (a memory or
association it evokes), affect (the feeling it raises), identity (a question about who I am / what I believe about
myself), relational (what the speaker wants from me / where we stand).
Lanes: emissary = analytical, facts and certainty, no feelings. dreamer = episodic, emotional, identity.
Vehicle: inline = resolve now; deferred = park for a quiet moment. identity is ALWAYS dreamer + deferred.
fact and epistemic are ALWAYS emissary + inline.
Regime of the whole message: closed (has one right answer), identity, open (no single answer), relational,
recall (asks me to remember or check what I said).
Rules: each ingredient names a DIFFERENT need; never two ingredients that say the same thing; never more than one
"relationship between X and Y" item; use the fewest ingredients that cover the message (1 is fine for a simple
message). purpose = one sentence: what a complete reply must achieve.

Example. Message: "Do you know the answer to 2+12?"
{"purpose":"Give the sum and say whether I actually know it","regime":"closed","ingredients":[
{"need":"compute 2+12","type":"fact","lane":"emissary","vehicle":"inline"},
{"need":"do I know this or am I guessing","type":"epistemic","lane":"emissary","vehicle":"inline"},
{"need":"what the sum evokes (schoolroom, times tables)","type":"episodic","lane":"dreamer","vehicle":"inline"}]}"""

OPTIONS = {"temperature": 0.2, "top_p": 0.9, "repeat_penalty": 1.18, "repeat_last_n": 256,
           "presence_penalty": 0.6, "frequency_penalty": 0.3, "num_predict": 700, "num_ctx": 4096}


def load_turns() -> list[dict]:
    rows = []
    pat = re.compile(r"^(\S+ \S+) \[nascence\.orchestrator\] \[CYCLE ([0-9]+)\] human: (.*)$")
    with LIVE_LOG.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = pat.match(line.rstrip("\n"))
            if m and m.group(1)[:10] <= CUTOFF:
                rows.append({"ts": m.group(1), "cycle": m.group(2), "log_text": m.group(3)})
    con = sqlite3.connect(f"file:{LIVE_DB.as_posix()}?mode=ro", uri=True)
    for r in rows:
        pre = r["log_text"][:45].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        cands = con.execute(
            "select fragment_id, timestamp, content from memory_fragments where origin='lived' and content like ? escape '\\'",
            (f"%{pre}%",)).fetchall()
        best = None
        for fid, ts, content in cands:
            for rank, (head, cut) in enumerate((("[Travis said to me] ", None), ("Q: ", "\nA:"), ("Input: ", "\n"))):
                if content.startswith(head):
                    txt = content[len(head):]
                    if cut and cut in txt:
                        txt = txt.split(cut, 1)[0]
                    txt = txt.strip()
                    if txt.startswith(r["log_text"][:45].strip()):
                        reply = content.split("\nA:", 1)[1].strip() if head == "Q: " and "\nA:" in content else None
                        key = (rank, -len(txt))
                        if best is None or key < best[0]:
                            best = (key, fid, txt, reply)
                        elif reply and not best[3] and len(txt) == len(best[2]):
                            best = (best[0], best[1], best[2], reply)
        # Du's actual reply: from any Q:/A: fragment of the same text
        if best:
            r["full_text"], r["fragment_id"], r["source"] = best[2], best[1], ["travis_said", "qa", "input"][best[0][0]]
            reply = best[3]
            if not reply:
                for fid, ts, content in cands:
                    if content.startswith("Q: ") and "\nA:" in content:
                        reply = content.split("\nA:", 1)[1].strip(); break
            r["du_actual"] = (reply or "")[:600]
        else:
            r["full_text"], r["fragment_id"], r["source"], r["du_actual"] = r["log_text"], None, "log_fallback", ""
        if r["source"] != "log_fallback" and len(r["full_text"]) > len(r["log_text"]):
            r["fidelity"] = "recovered"
        elif len(r["log_text"]) < 78:
            r["fidelity"] = "complete_in_log"
        else:
            r["fidelity"] = "truncated_unrecovered"
    con.close()
    return rows


def call(text: str, seed: int, timeout: int = 240) -> dict:
    if SEAT == "dreamer":
        # the CPU hub accepts format="json" only (llama-cpp json_object grammar) and honours only temperature,
        # top_p, num_predict -- the schema and the <=4 cap are carried in the prompt and checked in score().
        system = SYSTEM + "\n\nOutput ONLY one JSON object matching this JSON schema (at most 4 ingredients):\n" + json.dumps(SCHEMA)
        body = {"model": MODEL, "stream": False, "format": "json", "options": dict(OPTIONS, seed=seed),
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": "Message from Travis (the founder) to Du:\n" + text}]}
    else:
        body = {"model": MODEL, "stream": False, "think": False, "format": SCHEMA, "keep_alive": "10m",
            "options": dict(OPTIONS, seed=seed),
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": "Message from Travis (the founder) to Du:\n" + text}]}
    t0 = time.time()
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        out = json.loads(resp.read())
    return {"raw": out.get("message", {}).get("content", ""), "secs": round(time.time() - t0, 2),
            "eval_count": out.get("eval_count"), "done_reason": out.get("done_reason")}


def toks(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", s.lower()) if len(w) > 2}


def score(raw: str) -> dict:
    s = {"valid_json": False}
    try:
        m = json.loads(raw)
        ing = m["ingredients"]
        assert isinstance(ing, list) and ing
    except Exception as e:  # noqa: BLE001
        s["error"] = f"{type(e).__name__}: {str(e)[:120]}"
        return s
    s["valid_json"] = True
    s["manifest"] = m
    s["n"] = len(ing)
    s["decomposed"] = len(ing) >= 2
    lanes = {i.get("lane") for i in ing}
    s["both_lanes"] = lanes >= {"emissary", "dreamer"}
    needs = [i.get("need", "") for i in ing]
    dup = 0
    for a in range(len(needs)):
        for b in range(a + 1, len(needs)):
            ta, tb = toks(needs[a]), toks(needs[b])
            if ta and tb and len(ta & tb) / len(ta | tb) >= 0.6:
                dup += 1
    rel = sum(1 for n in needs if re.search(r"relationship between", n, re.I))
    heads = [" ".join(n.lower().split()[:3]) for n in needs]
    templ = max((heads.count(h) for h in heads), default=0)
    s["dup_pairs"] = dup
    s["over_cap"] = len(ing) > 4  # only possible on the dreamer seat (no schema grammar)
    s["schema_ok"] = (not s["over_cap"]) and m.get("regime") in SCHEMA["properties"]["regime"]["enum"] and all(
        isinstance(i, dict) and i.get("type") in ("fact", "epistemic", "episodic", "affect", "identity", "relational")
        and i.get("lane") in ("emissary", "dreamer") and i.get("vehicle") in ("inline", "deferred") for i in ing)
    s["degenerate"] = dup > 0 or rel >= 2 or templ >= 3
    s["identity_items"] = sum(1 for i in ing if i.get("type") == "identity")
    s["identity_deferred"] = sum(1 for i in ing if i.get("type") == "identity" and i.get("vehicle") == "deferred")
    s["rule_violations"] = sum(1 for i in ing if (i.get("type") == "identity" and (i.get("lane"), i.get("vehicle")) != ("dreamer", "deferred"))
                               or (i.get("type") in ("fact", "epistemic") and (i.get("lane"), i.get("vehicle")) != ("emissary", "inline")))
    s["regime"] = m.get("regime")
    return s


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    v = [r for r in rows if r["score"]["valid_json"]]
    f = lambda k: sum(1 for r in v if r["score"].get(k))  # noqa: E731
    return {"n": n, "valid_json": len(v), "decomposed": f("decomposed"), "both_lanes": f("both_lanes"),
            "degenerate": f("degenerate"), "over_cap": f("over_cap"), "schema_ok": f("schema_ok"), "dup_pair_rows": sum(1 for r in v if r["score"]["dup_pairs"]),
            "with_identity_item": f("identity_items"),
            "identity_items": sum(r["score"]["identity_items"] for r in v),
            "identity_deferred": sum(r["score"]["identity_deferred"] for r in v),
            "rule_violations": sum(r["score"]["rule_violations"] for r in v),
            "length_capped": sum(1 for r in rows if r.get("done_reason") == "length"),
            "mean_ingredients": round(sum(r["score"]["n"] for r in v) / max(1, len(v)), 2),
            "regimes": {k: sum(1 for r in v if r["score"]["regime"] == k) for k in SCHEMA["properties"]["regime"]["enum"]},
            "mean_secs": round(sum(r["secs"] for r in rows) / max(1, n), 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--arms", default="A1,A2,B")
    ap.add_argument("--seat", choices=sorted(SEATS), default="hot")
    ap.add_argument("--timeout", type=int, default=240)
    args = ap.parse_args()
    global URL, MODEL, SEAT
    SEAT = args.seat
    URL, MODEL = SEATS[SEAT]
    out = Path(args.out)
    h0 = _hash_file(LIVE_DB)
    turns = load_turns()
    print(f"turns={len(turns)} sources=" + json.dumps({k: sum(1 for t in turns if t['source'] == k) for k in ('travis_said', 'qa', 'input', 'log_fallback')}))
    fid = {k: sum(1 for t in turns if t["fidelity"] == k) for k in ("recovered", "complete_in_log", "truncated_unrecovered")}
    print("fidelity=" + json.dumps(fid))
    if args.probe:
        print(json.dumps(call(turns[0]["full_text"], 11, args.timeout), ensure_ascii=False)[:1500])
        return 0
    arms = {"A1": ("full_text", 11), "A2": ("full_text", 23), "B": ("log_text", 11)}
    summary = {"seat": SEAT, "model": MODEL, "url": URL, "options": OPTIONS, "turns": len(turns), "fidelity": fid, "arms": {}}
    with isolate(db="empty") as lab_dir:
        print(f"lab_dir={lab_dir}")
        rows_out = out.with_suffix(".jsonl")
        with rows_out.open("w", encoding="utf-8") as fh:
            for arm in [a for a in args.arms.split(",") if a]:
                field, seed = arms[arm]
                rows = []
                for i, t in enumerate(turns, 1):
                    try:
                        c = call(t[field], seed, args.timeout)
                    except Exception as e:  # noqa: BLE001
                        c = {"raw": "", "secs": 0, "eval_count": None, "done_reason": f"error {type(e).__name__}: {e}"}
                    row = {"arm": arm, "idx": i, "cycle": t["cycle"], "ts": t["ts"], "source": t["source"], "fidelity": t["fidelity"],
                           "input": t[field], "input_len": len(t[field]), **c, "score": score(c["raw"]),
                           "du_actual": t["du_actual"]}
                    rows.append(row)
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n"); fh.flush()
                    sc = row["score"]
                    print(f"{arm} #{i:02d} valid={sc['valid_json']} n={sc.get('n')} lanes2={sc.get('both_lanes')} "
                          f"degen={sc.get('degenerate')} {c['secs']}s {c['done_reason']}", flush=True)
                summary["arms"][arm] = summarize(rows)
    h1 = _hash_file(LIVE_DB)
    summary["live_db_sha256_before"], summary["live_db_sha256_after"] = h0, h1
    summary["live_db_unchanged"] = h0 == h1
    out.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
