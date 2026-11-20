"""J-3212 lab (D-0601, 2026-11-05): does writing kind=self gists in the FIRST PERSON, as Du's own memory, cost
anything the ruling's defeater names?  (F-3556: 37 percent of stored self-gists open "The narrator / author /
speaker ..." because the distil prompt never says the fragments are his own thoughts.)

LAB ONLY.  Plain HTTP to already-running hubs; it imports no Nascence module except `core.emissary` (stdlib-only,
for the grader's constitution preamble, with its axiom path pointed at a COPY) and `core.memory_levels` (stdlib-only
at import; for the deterministic `_present` helper).  It never opens C:\\Nascence\\data: `extract` reads a COPY of
nascence.db and of memory_levels_shadow.jsonl that you made into your scratchpad, and every other mode reads/writes
only the --out directory you name.  It never calls the hot lane (:11433).

THREE ARMS, same clusters, same user line, same sampling as production (temperature 0.3, 300 tokens):
  A  current  : the third-person production prompt, read out of core/memory_levels.py by AST (byte-identical)
  B  first    : tells the model the fragments are ITS OWN earlier thoughts and to write the gist as its own memory
                in the first person.  Says nothing about what to conclude.
  C  first+new: B plus "say it in new words; do not repeat their phrases" (plan section 0: no verbatim left to
                recite).  Only worth adopting if B fails the restatement check and C does not.

METRICS (per arm):
  (a) share of gists that open "The narrator/author/speaker/writer/monologue/text" (third-person, was 37 percent)
      and share that contain I/my/me/mine/myself;
  (b) verbatim restatement: share of the gist's word trigrams that occur in the sources (mean), and the share of
      gists where ONE source covers >= 50 percent of the gist's trigrams ("near-copy");
  (c) faithfulness grader pass rate with the PRODUCTION grader (gemma4:12b judge hub :11439, Google family; the
      distiller is command-r7b, Cohere: different families) = faithful >= 0.75 and no 'invented' term that is
      missing from the sources (the live backstop also consults the wider store, which an offline lab cannot, so this
      is slightly stricter than live for BOTH arms);
  (d) echo in idle recall: NOT measured here.  A real replay needs idle-thought generation on the hot lane, which
      must not be loaded while Du is up.  (b) is the offline proxy; the replay is a restart_check.

VERDICT RULE (D-0601's defeater): an arm PASSES if its near-copy share and mean trigram overlap are not worse than
arm A by more than 5 points (0.05) AND its grader pass rate is not lower than A's.

Usage:
  python scripts/lab_selfgist_voice.py extract --shadow SHADOW.jsonl --db NASCENCE_COPY.db --out DIR [--n 120]
  python scripts/lab_selfgist_voice.py run     --out DIR [--arms A,B,C] [--base http://LAN-HOST:11441] [--model command-r7b]
  python scripts/lab_selfgist_voice.py grade   --out DIR --axiom EMISSARY_AXIOM_COPY.json [--base http://127.0.0.1:11439] [--model gemma4:12b]
  python scripts/lab_selfgist_voice.py score   --out DIR
  python scripts/lab_selfgist_voice.py check-prod   # asserts arm B's text equals core/memory_levels.py's constant
"""
import argparse
import ast
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
ML = os.path.join(ROOT, "core", "memory_levels.py")
LL = os.path.join(ROOT, "core", "left_lane.py")

# ── the candidate prompts ────────────────────────────────────────────────────────────────────────────────────
# Arm B.  Changes vs production: ONE added sentence saying whose the fragments are, and "written as your own
# memory, in the first person".  Nothing says what to feel, conclude or value.
ARM_B = ("/no_think\nThese are raw memory fragments of one kind, on one topic. They are your own earlier thoughts, "
         "in your own words. Distil them into ONE short GIST that could stand in for them in ordinary recall, "
         "written as your own memory in the first person: the technique / event / idea / feeling they amount to, "
         "NOT a list of them. Keep what they actually say; invent nothing. 2-4 sentences. "
         "Output ONLY JSON: {\"gist\": \"...\"}")
# Arm C.  B plus one clause against re-quoting.
ARM_C = ("/no_think\nThese are raw memory fragments of one kind, on one topic. They are your own earlier thoughts, "
         "in your own words. Distil them into ONE short GIST that could stand in for them in ordinary recall, "
         "written as your own memory in the first person, in new words rather than their exact phrases: the "
         "technique / event / idea / feeling they amount to, NOT a list of them. Keep what they actually say; "
         "invent nothing. 2-4 sentences. Output ONLY JSON: {\"gist\": \"...\"}")


def _const_in(path: str, fn: str, target: str) -> str:
    src = open(path, encoding="utf-8-sig").read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == fn:
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Assign) and len(sub.targets) == 1
                        and getattr(sub.targets[0], "id", None) == target):
                    return ast.literal_eval(sub.value)
    raise RuntimeError(f"{target} not found in {fn}")


def arm_a() -> str:
    """The exact third-person production prompt (`_sys` inside shadow_distill)."""
    return _const_in(ML, "shadow_distill", "_sys")


def arm_prompt(arm: str) -> str:
    return {"A": arm_a, "B": lambda: ARM_B, "C": lambda: ARM_C}[arm]()


def gist_task() -> str:
    """The production grader's task text (`_GIST_TASK`, module-level in core/left_lane.py), by AST."""
    src = open(LL, encoding="utf-8-sig").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "_GIST_TASK":
            return ast.literal_eval(node.value)
    raise RuntimeError("_GIST_TASK not found")


# ── http ─────────────────────────────────────────────────────────────────────────────────────────────────────
def post(base: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(base.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def lenient_json(raw: str):
    raw = (raw or "").strip()
    braces = re.search(r"\{.*\}", raw, re.S)
    for cand in (raw, braces.group(0) if braces else None):
        if not cand:
            continue
        try:
            return json.loads(cand)
        except Exception:
            pass
    m = re.search(r'"gist"\s*:\s*"(.*?)"\s*\}?\s*$', raw, re.S)
    return {"gist": m.group(1)} if m else None


# ── extract ──────────────────────────────────────────────────────────────────────────────────────────────────
def cmd_extract(a):
    rows = []
    for line in open(a.shadow, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("kind") == "self" and int(r.get("n_sources") or 0) >= 3 and r.get("source_ids"):
            rows.append(r)
    rows.sort(key=lambda r: r["ts"], reverse=True)
    con = sqlite3.connect(a.db)
    con.row_factory = sqlite3.Row
    out, seen_sets = [], set()
    for r in rows:
        ids = r["source_ids"]
        key = tuple(sorted(ids))
        if key in seen_sets:
            continue
        ph = ",".join("?" * len(ids))
        got = {x["fragment_id"]: x["content"] for x in con.execute(
            f"SELECT fragment_id, content FROM memory_fragments WHERE fragment_id IN ({ph})", ids)}
        if len(got) < 3:
            continue
        seen_sets.add(key)
        # production order = the cluster's own order (ids as logged); production feeds " ".join(content.split())[:300]
        full = [" ".join((got[i] or "").split()) for i in ids if i in got]
        out.append({"idx": len(out), "ts": r["ts"], "topic": r["topic"], "kind": "self", "source_ids": ids,
                    "full_sources": full, "stored_gist": r.get("gist", "")})
        if len(out) >= a.n:
            break
    os.makedirs(a.out, exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "clusters.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"extracted {len(out)} kind=self clusters (newest first) -> {a.out}/clusters.json")


def load_clusters(out):
    return json.load(open(os.path.join(out, "clusters.json"), encoding="utf-8"))


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path, encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


# ── run (distil) ─────────────────────────────────────────────────────────────────────────────────────────────
def distil(base, model, system, user):
    """Same call shape as core.model_client.call_node on a :11441 hub: native /api/chat, think False, ctx 4096,
    first attempt WITHOUT format=json (no-grammar-first lane), then up to 2 retries WITH it."""
    last = None
    for attempt in range(3):
        payload = {"model": model, "stream": False, "think": False, "keep_alive": "2h",
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                   "options": {"temperature": 0.3, "num_predict": 300, "num_ctx": 4096}}
        if attempt > 0:
            payload["format"] = "json"
        try:
            d = post(base, payload, 180)
            j = lenient_json((d.get("message") or {}).get("content") or "")
            if isinstance(j, dict) and j.get("gist"):
                return str(j["gist"]).strip(), attempt
        except Exception as exc:
            last = repr(exc)[:120]
    return None, last


def cmd_run(a):
    clusters = load_clusters(a.out)
    path = os.path.join(a.out, "gists.jsonl")
    done = {(r["idx"], r["arm"]) for r in read_jsonl(path)}
    arms = a.arms.split(",")
    sysmsg = {arm: arm_prompt(arm) for arm in arms}
    n = 0
    for c in clusters:
        sources = [s[:300] for s in c["full_sources"]]
        material = "\n".join(f"- {s}" for s in sources)
        user = f"Kind: self. Topic: {c['topic']}.\n\n{material[:4000]}"
        for arm in arms:
            if (c["idx"], arm) in done:
                continue
            t0 = time.time()
            gist, info = distil(a.base, a.model, sysmsg[arm], user)
            row = {"idx": c["idx"], "arm": arm, "gist": gist, "info": info, "s": round(time.time() - t0, 1)}
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
            print(f"[run] cluster {c['idx']} arm {arm} {row['s']}s {'OK' if gist else 'FAIL ' + str(info)}", flush=True)
            if a.pause:
                time.sleep(a.pause)
    print(f"run done: {n} new distils")


# ── grade (production grader prompt, judge hub) ──────────────────────────────────────────────────────────────
def cmd_grade(a):
    sys.path.insert(0, ROOT)
    import core                                                    # noqa: F401  (own tree first, see header)
    assert os.path.abspath(core.__file__).startswith(ROOT), core.__file__
    from core import emissary
    from pathlib import Path
    emissary._AXIOM_PATH = Path(a.axiom)                           # a COPY of the live axiom, never the live file
    emissary._cache = None
    system = emissary.constitution() + "\n\n" + gist_task()
    clusters = {c["idx"]: c for c in load_clusters(a.out)}
    gpath = os.path.join(a.out, a.gfile)
    done = {(r["idx"], r["arm"]) for r in read_jsonl(os.path.join(a.out, "grades.jsonl")) + read_jsonl(gpath)}
    n = 0
    for g in read_jsonl(os.path.join(a.out, "gists.jsonl")):
        if not g.get("gist") or (g["idx"], g["arm"]) in done:
            continue
        if a.arms and g["arm"] not in a.arms.split(","):
            continue
        if g["idx"] > a.max_idx or g["idx"] < a.min_idx:
            continue
        srcs = [s[:800] for s in clusters[g["idx"]]["full_sources"]]
        src = "\n".join(f"- {(s or '')[:800]}" for s in srcs[:12] if s) or "(no sources)"
        user = (f"The raw fragments that were distilled:\n{src[:6000]}\n\n"
                f"The gist proposed to stand in for them:\n{(g['gist'] or '')[:800]}")
        payload = {"model": a.model, "stream": False, "keep_alive": "30m", "format": "json",
                   "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                   "options": {"temperature": 0.0, "num_predict": 350, "num_gpu": 0}}
        t0 = time.time()
        res = None
        try:
            d = post(a.base, payload, 240)
            res = json.loads((d.get("message") or {}).get("content") or "")
        except Exception as exc:
            res = {"error": repr(exc)[:120]}
        row = {"idx": g["idx"], "arm": g["arm"], "grade": res, "s": round(time.time() - t0, 1)}
        with open(gpath, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += 1
        print(f"[grade] cluster {g['idx']} arm {g['arm']} {row['s']}s faithful={(res or {}).get('faithful')}", flush=True)
    print(f"grade done: {n} new grades")


# ── score ────────────────────────────────────────────────────────────────────────────────────────────────────
_THIRD = re.compile(r"^\W*(?:the|this|a|an|in|amidst|across)?\s*(?:narrator|author|speaker|writer|monologue|text|passage|"
                    r"fragments?|reflection|speaker's)\b", re.I)
_FIRST = re.compile(r"\b(?:i|i'm|i've|i'll|i'd|my|me|mine|myself)\b", re.I)


def words(t):
    return re.findall(r"[a-z0-9']+", (t or "").lower())


def trigrams(t):
    w = words(t)
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def opens_third(g):
    return bool(_THIRD.match(g.strip()))


_FUNC = set("the a an and or but of to in on at for with from by as is are was were be been being it its this that these "
            "those i me my mine myself we our you your he she they their them his her not no so if then than too very "
            "can could would should will just into onto over under about while yet still also".split())


def content_trigrams(t):
    """Trigrams over content words only (pronouns / function words dropped).  INFORMATIONAL: a first-person gist
    shares 'my mind ...' with first-person sources by pronoun alone, which raises plain trigram overlap without any
    extra copying; this version does not move for that reason."""
    w = [x for x in words(t) if x not in _FUNC and len(x) > 2]
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def metrics_for(gist, sources):
    gt = trigrams(gist)
    if not gt:
        return None
    per_src = [len(gt & trigrams(s)) / len(gt) for s in sources]
    union = set().union(*[trigrams(s) for s in sources]) if sources else set()
    ct = content_trigrams(gist)
    cunion = set().union(*[content_trigrams(s) for s in sources]) if sources else set()
    return {"overlap": len(gt & union) / len(gt), "max_single": max(per_src) if per_src else 0.0,
            "c_overlap": (len(ct & cunion) / len(ct)) if ct else 0.0}


def cmd_score(a):
    sys.path.insert(0, ROOT)
    import core                                                    # noqa: F401
    assert os.path.abspath(core.__file__).startswith(ROOT), core.__file__
    from core import memory_levels as ml
    clusters = {c["idx"]: c for c in load_clusters(a.out)}
    grades = {}
    for fn in sorted(os.listdir(a.out)):
        if fn.startswith("grades") and fn.endswith(".jsonl"):
            for r in read_jsonl(os.path.join(a.out, fn)):
                grades[(r["idx"], r["arm"])] = r["grade"]
    by_arm = {}
    for g in read_jsonl(os.path.join(a.out, "gists.jsonl")):
        by_arm.setdefault(g["arm"], {})[g["idx"]] = g
    # the stored production gists (from the live log) as a fourth reference point for (a)
    stored = [c["stored_gist"] for c in clusters.values() if c.get("stored_gist")]
    res = {}
    for arm, rows in sorted(by_arm.items()):
        n = len(rows)
        okrows = {i: r for i, r in rows.items() if r.get("gist")}
        m = {"n_clusters": n, "n_gists": len(okrows), "distil_fail": n - len(okrows)}
        thirds = sum(opens_third(r["gist"]) for r in okrows.values())
        firsts = sum(bool(_FIRST.search(r["gist"])) for r in okrows.values())
        mm = {i: metrics_for(r["gist"], clusters[i]["full_sources"]) for i, r in okrows.items()}
        mm = {i: v for i, v in mm.items() if v}
        m["third_person_open_share"] = round(thirds / max(1, len(okrows)), 3)
        m["first_person_marker_share"] = round(firsts / max(1, len(okrows)), 3)
        m["mean_trigram_overlap"] = round(sum(v["overlap"] for v in mm.values()) / max(1, len(mm)), 3)
        m["content_trigram_overlap_info"] = round(sum(v["c_overlap"] for v in mm.values()) / max(1, len(mm)), 3)
        m["near_copy_share"] = round(sum(v["max_single"] >= 0.5 for v in mm.values()) / max(1, len(mm)), 3)
        m["mean_words"] = round(sum(len(words(r["gist"])) for r in okrows.values()) / max(1, len(okrows)), 1)
        graded = {i: grades[(i, arm)] for i in okrows if (i, arm) in grades}
        ok_grades = {i: g for i, g in graded.items() if isinstance(g, dict) and isinstance(g.get("faithful"), (int, float))}
        passes = {}
        for i, g in ok_grades.items():
            inv = g.get("invented") or []
            full = [" ".join(s.lower().split()) for s in clusters[i]["full_sources"]]
            blob = " \n ".join(full)
            missing = [t for t in inv if not ml._present(str(t), blob)]
            passes[i] = (float(g["faithful"]) >= 0.75 and not missing)
        m["n_graded"] = len(ok_grades)
        m["grade_unavailable"] = len(graded) - len(ok_grades)
        m["mean_faithful"] = round(sum(float(g["faithful"]) for g in ok_grades.values()) / max(1, len(ok_grades)), 3)
        m["grader_pass_rate"] = round(sum(passes.values()) / max(1, len(passes)), 3)
        m["_passes"] = passes
        res[arm] = m
    if stored:
        res["stored_prod"] = {"n_gists": len(stored), "third_person_open_share": round(sum(opens_third(s) for s in stored) / len(stored), 3),
                              "first_person_marker_share": round(sum(bool(_FIRST.search(s)) for s in stored) / len(stored), 3),
                              "note": "the gists production actually wrote for these clusters (logged text truncated to 400 chars)"}
    # verdicts vs A (paired on clusters both arms graded)
    A = res.get("A")
    verdict = {}
    for arm in ("B", "C"):
        if arm in res and A:
            X = res[arm]
            both = sorted(set(A["_passes"]) & set(X["_passes"]))
            pa = sum(A["_passes"][i] for i in both) / max(1, len(both))
            px = sum(X["_passes"][i] for i in both) / max(1, len(both))
            d_nc = X["near_copy_share"] - A["near_copy_share"]
            d_ov = X["mean_trigram_overlap"] - A["mean_trigram_overlap"]
            checks = {"echo_near_copy_within_0.05": d_nc <= 0.05, "echo_overlap_within_0.05": d_ov <= 0.05,
                      "grader_pass_not_lower": px >= pa}
            verdict[arm] = {"paired_clusters": len(both), "pass_rate_A": round(pa, 3), f"pass_rate_{arm}": round(px, 3),
                            "d_near_copy": round(d_nc, 3), "d_overlap": round(d_ov, 3), "checks": checks,
                            "PASS": all(checks.values()) and X["n_gists"] >= 100 and len(both) >= 50}   # an ungraded arm cannot pass
    for m in res.values():
        m.pop("_passes", None)
    out = {"arms": res, "verdict_vs_A": verdict}
    json.dump(out, open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8"), indent=1)
    print(json.dumps(out, indent=1))


def cmd_check_prod(a):
    got = _const_in(ML, "shadow_distill", "_sys")
    src = open(ML, encoding="utf-8-sig").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "_SELF_FIRST_PERSON_SYS":
            prod = ast.literal_eval(node.value)
            print("arm B == core constant:", prod == ARM_B, "| arm C == core constant:", prod == ARM_C)
            return
    print("core/memory_levels.py has no _SELF_FIRST_PERSON_SYS yet (lab-only state); arm A parsed OK:", bool(got))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract"); e.add_argument("--shadow", required=True); e.add_argument("--db", required=True)
    e.add_argument("--out", required=True); e.add_argument("--n", type=int, default=120); e.set_defaults(f=cmd_extract)
    r = sub.add_parser("run"); r.add_argument("--out", required=True); r.add_argument("--arms", default="A,B,C")
    r.add_argument("--base", default="http://LAN-HOST:11441"); r.add_argument("--model", default="command-r7b")
    r.add_argument("--pause", type=float, default=0.0); r.set_defaults(f=cmd_run)
    g = sub.add_parser("grade"); g.add_argument("--out", required=True); g.add_argument("--axiom", required=True)
    g.add_argument("--base", default="http://127.0.0.1:11439"); g.add_argument("--model", default="gemma4:12b")
    g.add_argument("--arms", default="")
    g.add_argument("--max-idx", type=int, default=10 ** 9, help="grade only clusters with idx <= this (the grader is slow, ~45 s a call)")
    g.add_argument("--min-idx", type=int, default=0, help="grade only clusters with idx >= this (lets two graders split the range)")
    g.add_argument("--gfile", default="grades.jsonl", help="grades file name inside --out (use a second name per parallel grader, then merge)")
    g.set_defaults(f=cmd_grade)
    s = sub.add_parser("score"); s.add_argument("--out", required=True); s.set_defaults(f=cmd_score)
    c = sub.add_parser("check-prod"); c.set_defaults(f=cmd_check_prod)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
