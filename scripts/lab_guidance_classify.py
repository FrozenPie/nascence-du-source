"""
J-3232 / D-0621 lab: replay core.guidance_learning._classify with three prompt variants on the background lane.

READ-ONLY LAB. Never edits the live prompt; never writes a live store. It reads COPIES of
data/guidance_beliefs.json and data/guidance_classify_log.jsonl (copied to a temp dir first), calls the
inference hubs over plain HTTP (NOT core.model_client, so no telemetry/latency log row is ever written to
a live file), and writes only under docs/lab/J-3232_data/.

Stages (run from the worktree):
  python scripts/lab_guidance_classify.py build     # copy live files to temp, build the pair sets -> pairs.json
  python scripts/lab_guidance_classify.py run       # author arms A/B/C on command-r7b -> author_runs.jsonl
  python scripts/lab_guidance_classify.py judge     # two different-family judges label every pair -> judge_runs.jsonl
  python scripts/lab_guidance_classify.py report    # tables -> report.json / report.md  (see lab_guidance_classify_report.py)

Arms
  A = the current live _CLASSIFY_SYS, verbatim (imported from core.guidance_learning).
  B = a 4-way variant: same_lesson / compatible_different / contradicts / unrelated, example UNFILLED.
  C = prompt A with its example output unfilled (placeholder instead of the pre-filled "assimilate").
  A-vs-C isolates the pre-filled-example effect; C-vs-B isolates the 4-way wording (both unfilled).
Author model: command-r7b (Cohere) on the Ramses background hub :11441, the live primary of SERVE_CHAINS["background"],
  same payload shape as core.model_client.call_node (temperature 0.2, num_predict 120, num_ctx 4096, format=json).
Judge models (different families from the author): gemma4:12b (Google), llama3.1:8b (Meta), phi4 (Microsoft) on the local
  ollama :11433 (the 1080 Ti is free while Du is down). Ground truth for the headline numbers is the HAND label
  (hand_labels.json); the judges are the decoupled cross-check and their agreement with the hand labels is reported.

PRE-REGISTERED DEFEATER READING (frozen before any author run; D-0621 gives no thresholds, these are mine):
  The 4-way variant B "passes" iff ALL of:
   (1) on hand-labelled NOT-same pairs inside the 10 mixed beliefs (set M) B routes away from corroborate
       (answers anything other than same_lesson) at least 30 percentage points more often than A does
       (A's corroborate = assimilate);
   (2) on the same-lesson set (set S, 56 hand-verified same-lesson pairs x REPEATS) B produces 0 accommodate/contradicts
       (the F-2203 "0 of 28 wrong accommodates" must not regress);
   (3) B's same-lesson -> same_lesson rate (true corroboration kept) is not more than 10 points below A's
       same-lesson -> assimilate rate on the same set.
  Otherwise the defeater says: leave the prompt.
"""
from __future__ import annotations
import json, os, sys, shutil, random, itertools, urllib.request, collections, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "lab" / "J-3232_data"
LIVE_DATA = Path(r"C:\Nascence\data")
TMP = Path(os.environ.get("TEMP", ".")) / "J-3232_copy"

AUTHOR_URL, AUTHOR_MODEL = "http://LAN-HOST:11441", "command-r7b"
JUDGES = {"mixtral": ("http://LAN-HOST:11438", "mixtral:8x7b"),
          "gemma4": ("http://127.0.0.1:11433", "gemma4:12b"),
          "llama31": ("http://127.0.0.1:11433", "llama3.1:8b"),
          "phi4": ("http://127.0.0.1:11433", "phi4:latest")}
# mixtral:8x7b on Ramses :11438 was started as judge #1 but ran ~30 s a call on the i9 CPU (and slowed the author hub's host);
# it was stopped after 11 rows and its partial file deleted. Judge families used instead: Google (gemma4), Meta (llama3.1), Microsoft (phi4).
REPEATS = 2           # samples per pair per arm at temperature 0.2
TIGHT8 = ["g40546190", "g45675272", "g20898348", "g81712100", "g78640841", "g81384728", "g36999143", "g66253255"]
MIXED10 = ["g72804061", "g93693252", "g64456712", "g90568341", "g92078461",
           "g46809289", "g50784324", "g43249169", "g93205430", "g83463523"]


# ---- the three prompts --------------------------------------------------------------------------
def prompt_A() -> str:
    sys.path.insert(0, str(ROOT))
    from core import guidance_learning as gl          # read-only import of the live constant
    return gl._CLASSIFY_SYS


def prompt_C() -> str:
    a = prompt_A()
    c = a.replace('{"relation": "assimilate"}', '{"relation": "<assimilate|accommodate|unrelated>"}')
    c = c.replace('{\\"relation\\": \\"assimilate\\"}', '{\\"relation\\": \\"<assimilate|accommodate|unrelated>\\"}')
    assert c != a, "could not unfill the example"
    return c


PROMPT_B = (
    "You already hold a BELIEF. You have just learned a NEW lesson. Decide their relation. Output ONLY a JSON "
    "object: {\"relation\": \"<same_lesson|compatible_different|contradicts|unrelated>\"}.\n"
    "same_lesson = the new lesson says the SAME thing as the belief, restated in other words or with a different "
    "example. Someone who holds the belief would say: yes, that is exactly what I already believe.\n"
    "compatible_different = the new lesson does not contradict the belief, but it is a DIFFERENT lesson (a different "
    "claim, subject or advice). Both could be true at once and neither merely restates the other. Sharing a theme, a "
    "phrase such as 'true understanding', or a general tone is NOT enough for same_lesson.\n"
    "contradicts = the new lesson genuinely CONTRADICTS the belief (opposite direction).\n"
    "unrelated = they are about different things."
)
B_MAP = {"same_lesson": "assimilate", "compatible_different": "compatible_different",
         "contradicts": "accommodate", "unrelated": "unrelated"}

JUDGE_SYS = (
    "You are labelling the relation between two short first-person lessons, A and B. First state each lesson's single "
    "core claim in a few words, then give a label. Output ONLY a JSON object: "
    "{\"claim_a\": \"...\", \"claim_b\": \"...\", \"label\": \"<same|compatible_different|contradicts|unrelated>\"}.\n"
    "same = B makes the same core claim as A, reworded or with another example (a holder of A would say that is exactly "
    "what they already believe).\n"
    "compatible_different = the two do not conflict, but B is a different claim from A (different advice, subject or "
    "mechanism); sharing a theme or generic wording such as 'true understanding' does not make them the same.\n"
    "contradicts = the core claims point in opposite directions and cannot both be held as stated.\n"
    "unrelated = they are about different things altogether."
)


# POSITION-BIAS CONTROLS (added after the first read of results, NOT pre-registered): the unfilled placeholders list the
# options in one fixed order, and the model's favourite answer in both B (compatible_different) and C (accommodate) was the
# SECOND listed option. Brev / Crev list the same options in reversed order; 1 repeat each.
PROMPT_Brev = PROMPT_B.replace("<same_lesson|compatible_different|contradicts|unrelated>",
                               "<unrelated|contradicts|compatible_different|same_lesson>")


def prompt_Crev() -> str:
    return prompt_A().replace('{"relation": "assimilate"}', '{"relation": "<unrelated|accommodate|assimilate>"}')


def user_msg(existing: str, new: str) -> str:   # identical to the live _classify user message
    return f"BELIEF you hold:\n\"{existing[:400]}\"\n\nNEW lesson:\n\"{new[:400]}\""


def judge_msg(a: str, b: str) -> str:
    return f"Lesson A:\n\"{a[:400]}\"\n\nLesson B:\n\"{b[:400]}\""


# ---- plain HTTP client (no live telemetry) ------------------------------------------------------
def chat(url: str, model: str, sys_: str, user: str, num_predict: int = 120, timeout: int = 300) -> str:
    p = {"model": model, "messages": [{"role": "system", "content": sys_}, {"role": "user", "content": user}],
         "think": False, "stream": False, "format": "json",
         "options": {"temperature": 0.2, "num_predict": num_predict, "num_ctx": 4096}, "keep_alive": "10m"}
    req = urllib.request.Request(url + "/api/chat", data=json.dumps(p).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return (json.load(r).get("message") or {}).get("content") or ""


def parse_json(raw: str) -> dict:
    try:
        return json.loads(raw.strip())
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {}


# ---- pair building ------------------------------------------------------------------------------
def build() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in ("guidance_beliefs.json", "guidance_classify_log.jsonl"):
        shutil.copy(LIVE_DATA / f, TMP / f)                      # read-only copy; nothing opened for write live
    beliefs = {b["id"]: b for b in json.load(open(TMP / "guidance_beliefs.json", encoding="utf-8"))}
    pairs: list[dict] = []

    def add(set_, pid, e, n, **meta):
        pairs.append({"id": pid, "set": set_, "existing": e, "new": n, **meta})

    # L: the logged classify rows (record != final)
    rows = [json.loads(l) for l in open(TMP / "guidance_classify_log.jsonl", encoding="utf-8")]
    k = 0
    for r in rows:
        if r.get("record") == "final":
            continue
        add("L", f"L{k:02d}", r["existing"], r["new"], domain=r.get("domain"), logged=r.get("relation"), ts=r["ts"])
        k += 1
    # M: the 10 mixed beliefs: seed capture[0] vs capture i, and the current medoid principle vs the other captures
    for g in MIXED10:
        b = beliefs[g]
        caps = b["captures"]
        for i in range(1, len(caps)):
            add("M", f"M-{g}-s{i:02d}", caps[0], caps[i], belief=g, domain=b["domain"], kind="seed")
        if b["principle"] != caps[0]:
            for i, c in enumerate(caps):
                if c != b["principle"]:
                    add("M", f"M-{g}-m{i:02d}", b["principle"], c, belief=g, domain=b["domain"], kind="medoid")
    # S: the F-2203 tight-8 same-lesson family, all 28 pairs in both directions
    for a, c in itertools.combinations(TIGHT8, 2):
        for (x, y), d in (((a, c), "f"), ((c, a), "r")):
            add("S", f"S-{x}-{y}", beliefs[x]["principle"], beliefs[y]["principle"], a=x, b=y, direction=d)
    # S2: same-lesson pairs found INSIDE mixed beliefs (hand-chosen)
    for g, i, j in [("g93693252", 3, 4), ("g93693252", 5, 6), ("g93693252", 7, 8), ("g93693252", 13, 14), ("g64456712", 3, 4)]:
        caps = beliefs[g]["captures"]
        add("S2", f"S2-{g}-{i}-{j}", caps[i], caps[j], belief=g)
    # U: random prefilter-passing pairs (same domain, token overlap >= 0.12, the live gate) from non-superseded beliefs
    sys.path.insert(0, str(ROOT))
    from core import guidance_learning as gl
    pool = [b for b in beliefs.values() if b.get("status") != "superseded"]
    rnd = random.Random(3232)
    seen, cand = set(), []
    for _ in range(20000):
        a, c = rnd.sample(pool, 2)
        if a["domain"] != c["domain"] or a["id"] == c["id"]:
            continue
        key = tuple(sorted((a["id"], c["id"])))
        if key in seen:
            continue
        seen.add(key)
        if gl._overlap(a["principle"] + " " + a.get("scope", ""), c["principle"] + " " + c.get("scope", "")) >= 0.12:
            cand.append((a, c))
        if len(cand) >= 40:
            break
    for n, (a, c) in enumerate(cand):
        add("U", f"U{n:02d}", a["principle"], c["principle"], a=a["id"], b=c["id"], domain=a["domain"])
    json.dump(pairs, open(OUT / "pairs.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("pairs:", dict(collections.Counter(p["set"] for p in pairs)))


# ---- run ----------------------------------------------------------------------------------------
def run() -> None:
    pairs = json.load(open(OUT / "pairs.json", encoding="utf-8"))
    prompts = {"A": prompt_A(), "B": PROMPT_B, "C": prompt_C()}
    json.dump(prompts, open(OUT / "prompts.json", "w", encoding="utf-8"), indent=1)
    path = OUT / "author_runs.jsonl"
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            done.add((r["pid"], r["arm"], r["rep"]))
    f = open(path, "a", encoding="utf-8")
    n = 0
    for p in pairs:
        for arm in "ABC":
            for rep in range(REPEATS):
                if (p["id"], arm, rep) in done:
                    continue
                try:
                    raw = chat(AUTHOR_URL, AUTHOR_MODEL, prompts[arm], user_msg(p["existing"], p["new"]))
                except Exception as e:
                    raw = f"ERR {e}"
                rel = str(parse_json(raw).get("relation", "")).strip().lower()
                f.write(json.dumps({"pid": p["id"], "arm": arm, "rep": rep, "raw": raw.strip()[:300], "relation": rel},
                                   ensure_ascii=False) + "\n")
                f.flush()
                n += 1
        if n and n % 150 == 0:
            print(n, "calls", flush=True)
    print("author calls this run:", n)


def run_ctrl() -> None:
    """Position-bias controls: arms Brev / Crev (reversed placeholder order), 1 repeat, same pairs, same payload."""
    pairs = json.load(open(OUT / "pairs.json", encoding="utf-8"))
    prompts = {"Brev": PROMPT_Brev, "Crev": prompt_Crev()}
    json.dump(prompts, open(OUT / "prompts_ctrl.json", "w", encoding="utf-8"), indent=1)
    path = OUT / "author_runs_ctrl.jsonl"
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            done.add((r["pid"], r["arm"], r["rep"]))
    f = open(path, "a", encoding="utf-8")
    for p in pairs:
        for arm in prompts:
            if (p["id"], arm, 0) in done:
                continue
            try:
                raw = chat(AUTHOR_URL, AUTHOR_MODEL, prompts[arm], user_msg(p["existing"], p["new"]))
            except Exception as e:
                raw = f"ERR {e}"
            rel = str(parse_json(raw).get("relation", "")).strip().lower()
            f.write(json.dumps({"pid": p["id"], "arm": arm, "rep": 0, "raw": raw.strip()[:300], "relation": rel},
                               ensure_ascii=False) + "\n")
            f.flush()
    f.close()


def judge(only: str | None = None) -> None:
    """Run one judge (argv[2]) or all; each judge writes its own judge_runs_<name>.jsonl (parallel-safe)."""
    pairs = json.load(open(OUT / "pairs.json", encoding="utf-8"))
    for name, (url, model) in JUDGES.items():
        if only and name != only:
            continue
        path = OUT / f"judge_runs_{name}.jsonl"
        done = set()
        if path.exists():
            for l in open(path, encoding="utf-8"):
                done.add(json.loads(l)["pid"])
        f = open(path, "a", encoding="utf-8")
        for p in pairs:
            if p["id"] in done:
                continue
            try:
                raw = chat(url, model, JUDGE_SYS, judge_msg(p["existing"], p["new"]), num_predict=260)
            except Exception as e:
                raw = f"ERR {e}"
            d = parse_json(raw)
            f.write(json.dumps({"pid": p["id"], "judge": name, "label": str(d.get("label", "")).strip().lower(),
                                "claim_a": d.get("claim_a"), "claim_b": d.get("claim_b"), "raw": raw.strip()[:400]},
                               ensure_ascii=False) + "\n")
            f.flush()
        f.close()
        print("judge done:", name, flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "judge":
        judge(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"build": build, "run": run, "ctrl": run_ctrl}.get(cmd, lambda: print(__doc__))()
