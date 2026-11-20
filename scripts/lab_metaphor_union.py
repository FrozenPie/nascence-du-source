"""J-3205 lab (2026-11-05, Du down): labelled-union evaluation of the Lane 2 metaphor prompts (D-0595).

READ-ONLY LAB. Imports no core module and executes no Nascence code; it makes HTTP calls to the three
already-running judge hubs (the same ones core/judge_panel.py uses) and writes only under
docs/lab/ (this tree). Live stores are read only through byte-copies (snapshots) taken by `build`.

D-0595 design (founder, 2026-11-02): hand-label every tick that ANY of {v1 prompt, v2 prompt, either
keyword scan, the flag arm (F-3837)} marks as possibly figurative, over the stored deepseek era
(ticks with model deepseek-r1:7b, since 2026-09-28), then require precision >= 70 percent AND recall
>= v1's on that union, with the number of labelled positives stated in advance (12 to 20).
Defeater: fewer than 12 labelled positives -> the stored era is too thin; fall back to the tiebreak alone.

Subcommands
  build   snapshot the live logs, build the union frame + a seeded control sample of NON-union ticks
          -> docs/lab/metaphor_union_ticks.jsonl  (one row per frame tick, with the marking sources)
  run     replay v1 and v2 through the production-shaped panel (JUDGE_1 + JUDGE_2, gemma tiebreak on a
          split) for every frame tick; resumable -> docs/lab/J-3205_data/panel_runs.jsonl
  sheet   write the BLIND labelling sheet (no marks shown) + the key
  score   read a labels file and compute precision / recall of v1 and v2 on the union

Why a control sample: v1 and v2 were never run on all ~2,800 ticks (about 5,500 panel runs on shared
CPU hubs at 10 s each is 15 hours). The union is built from the zero-cost marks (stored v1 panel
rulings incl. any single-judge True, both keyword scans, the flag arm = any keyword hit) and the frame
adds a seeded random sample of the remaining ticks, run through BOTH prompts, so the number of
prompt-marked ticks lying OUTSIDE the stored-marks union can be estimated instead of ignored.
"""
import argparse
import ast
import bisect
import collections
import datetime
import json
import math
import os
import random
import shutil
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
LANE2 = os.path.join(ROOT, "core", "lane2.py")
LIVE_SHADOW = r"C:\Nascence\data\lane2_shadow.jsonl"
LIVE_JPL = r"C:\Nascence\data\judge_panel_log.jsonl"
DATA = os.path.join(ROOT, "docs", "lab", "J-3205_data")
UNION = os.path.join(ROOT, "docs", "lab", "metaphor_union_ticks.jsonl")
RUNS = os.path.join(DATA, "panel_runs.jsonl")

JUDGE_1 = "http://LAN-HOST:11438"      # mixtral:8x7b (core/judge_panel.py JUDGE_1)
JUDGE_2 = "http://127.0.0.1:11440"       # falcon3:7b   (JUDGE_2)
TIEBREAK = "http://127.0.0.1:11439"      # gemma4:12b   (core/lane2.py _TIEBREAK_LANE2)
ERA_START = datetime.datetime(2026, 9, 28).timestamp()   # D-0595: deepseek era since 09-28
CONTROL_N = 90
SEED = 3205
FIELDS = ("notice", "uncertain", "expect_next")


# --------------------------------------------------------------------------------------- prompts
def production_prompt() -> str:
    """v1: the exact sysmsg string literal inside core/lane2.py _judge_metaphor (AST, no import)."""
    src = open(LANE2, encoding="utf-8-sig").read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "_judge_metaphor":
            for sub in ast.walk(node):
                if (isinstance(sub, ast.Assign) and len(sub.targets) == 1
                        and getattr(sub.targets[0], "id", None) == "sysmsg"):
                    return ast.literal_eval(sub.value)
    raise RuntimeError("sysmsg not found in _judge_metaphor")


def v2_prompt() -> str:
    """v2: the J-2212 candidate (scripts/lab_J2212_metaphor_prompt.py V2), read by AST so it is the
    same bytes F-2955 measured."""
    p = os.path.join(HERE, "lab_J2212_metaphor_prompt.py")
    for node in ast.parse(open(p, encoding="utf-8").read()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "V2":
            return ast.literal_eval(node.value)
    raise RuntimeError("V2 not found")


def passage_of(tick: dict) -> str:
    """What _judge_metaphor judged: the three fields joined with a space (the shadow log truncates
    each field at about 400 chars), first 500 chars."""
    return " ".join(str(tick.get(k) or "") for k in FIELDS)[:500]


# ------------------------------------------------------------------------------------------ stats
def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(100 * (c - h), 1), round(100 * (c + h), 1))


def pct(k, n):
    return None if n == 0 else round(100.0 * k / n, 1)


# ------------------------------------------------------------------------------------------ build
def _load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def load_era(shadow_path, jpl_path):
    """Era ticks (deepseek, ts >= ERA_START, non-empty passage) with their joined stored panel ruling."""
    ticks = [r for r in _load_jsonl(shadow_path)
             if r.get("kind") == "tick" and "deepseek" in str(r.get("model")) and r["ts"] >= ERA_START]
    ticks.sort(key=lambda r: r["ts"])
    jpl = [r for r in _load_jsonl(jpl_path) if r.get("context") == "lane2:metaphor"
           and r["ts"] >= ERA_START - 600]
    jpl.sort(key=lambda r: r["ts"])
    jts = [r["ts"] for r in jpl]
    for t in ticks:
        t["_stored"] = None
        mj = t.get("metaphor_judged") or {}
        if mj.get("verdict") == "not_sampled":
            continue
        # The judge_panel_log row is written DURING the tick, after tick["ts"] (the tick-start stamp):
        # first row at or after ts. Verified 711/711 against metaphor_judged verdict+how in this era.
        i = bisect.bisect_left(jts, t["ts"])
        if i < len(jpl):
            j = jpl[i]
            jv = {True: "metaphor", False: "literal", None: "cannot_tell"}[j.get("verdict")]
            if jv == mv_verdict(mj) and j.get("how") == mj.get("how"):
                t["_stored"] = j
    return ticks, jpl


def mv_verdict(mj):
    return mj.get("verdict")


def cmd_build(a):
    os.makedirs(DATA, exist_ok=True)
    snap_s = os.path.join(DATA, "snap_lane2_shadow.jsonl.tmp")
    snap_j = os.path.join(DATA, "snap_judge_panel_log.jsonl.tmp")
    shutil.copyfile(LIVE_SHADOW, snap_s)
    shutil.copyfile(LIVE_JPL, snap_j)
    ticks, jpl = load_era(snap_s, snap_j)
    sha = {}
    import hashlib
    for nm, p in (("lane2_shadow", snap_s), ("judge_panel_log", snap_j)):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        sha[nm] = {"bytes": os.path.getsize(p), "sha256": h.hexdigest()}
    os.remove(snap_s)
    os.remove(snap_j)

    rows, stats = [], collections.Counter()
    for t in ticks:
        said = passage_of(t)
        if not said.strip():
            stats["empty_passage"] += 1
            continue
        src = []
        if t.get("metaphor_flags"):
            src.append("kw_metaphor")
        if t.get("figurative_flags"):
            src.append("kw_figurative")
        if src:
            src.append("flag_arm")      # F-3837 arm B == judge every keyword-flagged tick (not built in
            #                             this era; by definition its members are the keyword-flagged ticks)
        mj = t.get("metaphor_judged") or {}
        st = t.get("_stored")
        if mj.get("verdict") == "metaphor":
            src.append("v1_stored_panel")
        if st is not None:
            # any single judge True is a "mark" even when the panel ruled literal (permissive union)
            if st.get("v1") is True or st.get("v2") is True or st.get("v3") is True:
                src.append("v1_stored_anyjudge")
        rows.append({
            "tick_ts": t["ts"],
            "time": datetime.datetime.fromtimestamp(t["ts"]).strftime("%Y-%m-%d %H:%M:%S"),
            "passage": said,
            "stored_v1": (None if mj.get("verdict") == "not_sampled" else
                          {"verdict": mj.get("verdict"), "how": mj.get("how"), "why": mj.get("why"),
                           "j1": (st or {}).get("v1"), "j2": (st or {}).get("v2"),
                           "j3": (st or {}).get("v3") if st else None}),
            "metaphor_flags": t.get("metaphor_flags") or [],
            "figurative_flags": t.get("figurative_flags") or [],
            "sources": src,
            "in_union": bool(src),
        })
        stats["era_ticks"] += 1
    union = [r for r in rows if r["in_union"]]
    rest = [r for r in rows if not r["in_union"]]
    rng = random.Random(SEED)
    control = rng.sample(rest, min(CONTROL_N, len(rest)))
    for r in control:
        r["sources"] = ["control_sample"]
    ctl_ids = {r["tick_ts"] for r in control}
    frame = sorted(union + control, key=lambda r: r["tick_ts"])
    os.makedirs(os.path.dirname(UNION), exist_ok=True)
    with open(UNION, "w", encoding="utf-8") as f:
        for r in frame:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    srcs = collections.Counter(s for r in union for s in r["sources"])
    summary = {"era_start": "2026-09-28", "snapshots": sha, "era_ticks_with_passage": len(rows),
               "empty_passage_ticks": stats["empty_passage"], "union_ticks": len(union),
               "non_union_ticks": len(rest), "control_sample": len(control), "seed": SEED,
               "union_by_source": dict(srcs),
               "stored_judged_ticks": sum(1 for r in rows if r["stored_v1"] is not None),
               "stored_metaphor_verdicts": sum(1 for r in rows if "v1_stored_panel" in r["sources"]),
               "union_ticks_with_stored_v1": sum(1 for r in union if r["stored_v1"] is not None)}
    json.dump(summary, open(os.path.join(DATA, "build_summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


# -------------------------------------------------------------------------------------------- run
_lock = threading.Lock()


def ask(url, system, user, timeout):
    """One judge call, same payload shape as core/judge_panel._ask. Returns (verdict, why, err, s)."""
    p = {"model": "judge", "stream": False, "format": "json",
         "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
         "options": {"temperature": 0.0, "num_predict": 200}}
    t0 = time.time()
    try:
        req = urllib.request.Request(url + "/api/chat", json.dumps(p).encode(),
                                     {"Content-Type": "application/json"})
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8-sig"))
        v = json.loads((d.get("message") or {}).get("content") or "")
        if isinstance(v, dict) and isinstance(v.get("metaphor"), bool):
            why = v.get("why")
            return v["metaphor"], (why if isinstance(why, str) else None), None, round(time.time() - t0, 1)
        return None, None, "parse", round(time.time() - t0, 1)
    except Exception as exc:
        name = type(exc).__name__
        err = "timeout" if "imeout" in name or "timed out" in str(exc) else "http" if "URL" in name or "HTTP" in name else "exception"
        return None, None, err, round(time.time() - t0, 1)


def panel(system, passage):
    """Production-shaped panel: JUDGE_1 and JUDGE_2 concurrently; gemma tiebreak only on a split."""
    usr = f"PASSAGE: {passage[:500]}"
    with ThreadPoolExecutor(2) as ex:
        f1 = ex.submit(ask, JUDGE_1, system, usr, 120)
        f2 = ex.submit(ask, JUDGE_2, system, usr, 120)
        (v1, w1, e1, s1), (v2, w2, e2, s2) = f1.result(), f2.result()
    # one retry on a timeout/transport failure of either seat (the J-2094 replay did the same)
    if v1 is None and e1 in ("timeout", "http"):
        v1, w1, e1, s1 = ask(JUDGE_1, system, usr, 240)
    if v2 is None and e2 in ("timeout", "http"):
        v2, w2, e2, s2 = ask(JUDGE_2, system, usr, 240)
    verdict, how, v3, w3, e3 = None, "unavailable", None, None, None
    if v1 is not None and v2 is not None:
        if v1 == v2:
            verdict, how = v1, "agreed"
        else:
            v3, w3, e3, _ = ask(TIEBREAK, system, usr, 900)
            verdict, how = (v3, "tiebreak") if v3 is not None else (None, "split_no_tiebreak")
    return {"j1": v1, "j2": v2, "j3": v3, "verdict": verdict, "how": how,
            "why": w3 or w1 or w2, "e1": e1, "e2": e2, "e3": e3, "s1": s1, "s2": s2}


def cmd_run(a):
    frame = _load_jsonl(UNION)
    prompts = {"v1": production_prompt(), "v2": v2_prompt()}
    prompts["v1fid"] = prompts["v1"]     # fidelity arm: replay v1 on ticks production already ruled on
    done = set()
    if os.path.exists(RUNS):
        for r in _load_jsonl(RUNS):
            if r.get("how") != "unavailable":
                done.add((r["arm"], r["tick_ts"]))
    jobs = []
    only = {float(x) for x in a.only_ts.split(",") if x}
    for r in frame:
        if only and r["tick_ts"] not in only:
            continue
        for arm in a.arms.split(","):
            if (arm, r["tick_ts"]) in done:
                continue
            # production already ran v1 on the 25 percent sampled ticks: that stored ruling IS the v1
            # arm for those ticks, no replay needed (a --fidelity subset re-runs some to compare)
            if arm == "v1" and r["stored_v1"] is not None:
                continue
            if arm == "v1fid" and r["tick_ts"] not in a.force_ts_set:
                continue
            jobs.append((arm, r))
    if a.limit:
        jobs = jobs[:a.limit]
    print(f"{len(jobs)} panel runs to do ({len(done)} already done)", flush=True)
    t0 = time.time()
    n = [0]

    def work(job):
        arm, r = job
        res = panel(prompts[arm], r["passage"])
        res.update({"arm": arm, "tick_ts": r["tick_ts"]})
        with _lock:
            with open(RUNS, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
            n[0] += 1
            if n[0] % 10 == 0:
                print(f"  {n[0]}/{len(jobs)} {round(time.time() - t0)}s", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, jobs))
    print("done", n[0], round(time.time() - t0), "s", flush=True)


# ------------------------------------------------------------------------------------------ score
def load_labels(path):
    """Labels file: jsonl rows {id, label} (label F/A/L) or a CSV with columns id,label. Returns
    {tick_ts: label} through the key."""
    key = {k["id"]: k["tick_ts"] for k in _load_jsonl(KEY)}
    out = {}
    if path.lower().endswith(".csv"):
        import csv
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    else:
        rows = _load_jsonl(path)
    for r in rows:
        lab = str(r.get("label", "")).strip().upper()[:1]
        if lab in ("F", "A", "L") and r.get("id") in key:
            out[key[r["id"]]] = lab
    return out


def arm_verdicts(frame, runs):
    """{arm: {tick_ts: True/False/None}} -- v1 = production's own stored ruling where it exists, else the
    replay; v2 = replay. A ruling counts as 'metaphor' only on a panel verdict True."""
    res = {"v1": {}, "v2": {}}
    for r in frame:
        sv = r["stored_v1"]
        if sv is not None:
            res["v1"][r["tick_ts"]] = {"metaphor": True, "literal": False}.get(sv["verdict"])
    # a stored ruling of cannot_tell (a production JUDGE_1 timeout) has no usable v1 verdict: fall back
    # to the fidelity-arm replay of the same prompt on that tick
    for r in runs:
        if r["arm"] == "v1fid" and res["v1"].get(r["tick_ts"], 0) is None and r["verdict"] is not None:
            res["v1"][r["tick_ts"]] = r["verdict"]
    for r in runs:
        if r["arm"] == "v1" and r["tick_ts"] not in res["v1"]:
            res["v1"][r["tick_ts"]] = r["verdict"]
        elif r["arm"] == "v2":
            res["v2"][r["tick_ts"]] = r["verdict"]
    return res


def prf(flagged, positives, universe):
    tp = len(flagged & positives)
    n_fl = len(flagged)
    n_pos = len(positives & universe)
    p, r = pct(tp, n_fl), pct(tp, n_pos)
    return {"flagged": n_fl, "tp": tp, "positives_in_universe": n_pos, "precision_pct": p,
            "precision_wilson": wilson(tp, n_fl), "recall_pct": r, "recall_wilson": wilson(tp, n_pos)}


def cmd_score(a):
    frame = _load_jsonl(UNION)
    runs = _load_jsonl(RUNS) if os.path.exists(RUNS) else []
    labels = load_labels(a.labels)
    arms = arm_verdicts(frame, runs)
    by_ts = {r["tick_ts"]: r for r in frame}
    marked = {arm: {t for t, v in d.items() if v is True} for arm, d in arms.items()}
    stored_union = {t for t, r in by_ts.items() if r["in_union"]}
    control = {t for t, r in by_ts.items() if not r["in_union"]}
    # the union proper = stored-marks union + any control tick a prompt marked
    union = stored_union | {t for t in control if t in marked["v1"] or t in marked["v2"]}
    labelled = set(labels)
    n_unlabelled = len(frame) - len(labelled & set(by_ts))
    out = {"labels_file": a.labels, "frame_ticks": len(frame), "labelled": len(labelled & set(by_ts)),
           "unlabelled": n_unlabelled, "stored_marks_union": len(stored_union),
           "control_ticks": len(control), "union_incl_prompt_marked_control": len(union)}
    kw = {"kw_metaphor": {t for t in stored_union if "kw_metaphor" in by_ts[t]["sources"]},
          "kw_figurative": {t for t in stored_union if "kw_figurative" in by_ts[t]["sources"]},
          "flag_arm": {t for t in stored_union if "flag_arm" in by_ts[t]["sources"]}}
    for tier, keep in (("strict_F", {"F"}), ("inclusive_F+A", {"F", "A"})):
        pos = {t for t, l in labels.items() if l in keep}
        pos_union = pos & union
        res = {"positives_in_union": len(pos_union), "positives_in_control_only": len(pos & control - union)}
        for arm in ("v1", "v2"):
            res[arm] = prf(marked[arm] & labelled, pos & labelled, union & labelled)
            res[arm]["unlabelled_flagged"] = len(marked[arm] - labelled)
        for nm, st in kw.items():
            res[nm] = prf(st & labelled, pos & labelled, union & labelled)
        v1r, v2 = res["v1"]["recall_pct"], res["v2"]
        res["bar_v2"] = {"precision_ge_70": (v2["precision_pct"] or 0) >= 70.0,
                         "recall_ge_v1": (v2["recall_pct"] or 0) >= (v1r or 0),
                         "passes": bool((v2["precision_pct"] or 0) >= 70.0 and (v2["recall_pct"] or 0) >= (v1r or 0)),
                         "v2_flagged_n": v2["flagged"]}
        out[tier] = res
    # control-sample leak: positives found among the NON-union control ticks (estimates how many sit
    # outside every stored mark), scaled to the non-union population
    pos_any = {t for t, l in labels.items() if l in ("F", "A")}
    pos_strict = {t for t, l in labels.items() if l == "F"}
    ctl_lab = control & labelled
    out["control_leak"] = {"control_labelled": len(ctl_lab), "strict_positives_in_control": len(pos_strict & ctl_lab),
                           "inclusive_positives_in_control": len(pos_any & ctl_lab),
                           "strict_wilson_pct": wilson(len(pos_strict & ctl_lab), len(ctl_lab)),
                           "inclusive_wilson_pct": wilson(len(pos_any & ctl_lab), len(ctl_lab))}
    pos12 = len(pos_strict & labelled)
    out["defeater_D0595"] = {"strict_positives_total": pos12, "inclusive_positives_total": len(pos_any & labelled),
                             "target_range": [12, 20],
                             "fewer_than_12_strict": pos12 < 12}
    print(json.dumps(out, indent=1))
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1)


KEY = os.path.join(DATA, "labelling_key.jsonl")
SHEET = os.path.join(DATA, "labelling_sheet.md")
SHEET_SEED = 3206


def cmd_sheet(a):
    """BLIND labelling sheet: shuffled, no marks, no judge output, no source. Labels:
    F = figurative (clear)   A = arguable   L = literal.
    The key (sheet id -> tick_ts) is a separate file."""
    frame = _load_jsonl(UNION)
    by_ts = {r["tick_ts"]: r for r in frame}
    order = list(range(len(frame)))
    random.Random(SHEET_SEED).shuffle(order)
    lines = ["# J-3205 labelling sheet (BLIND: no model marks, no keyword flags shown)", "",
             "Label each passage in the `label` column: **F** = clearly figurative (metaphor, symbol, "
             "self-narrative, or ambient-mood language that paints/personifies the scene rather than "
             "reporting a percept), **A** = arguable, **L** = literal (plain report of what is perceived, "
             "incl. a sensor field named with its value, real sound/call names, real fire/sun colour).",
             "", "Reading rule for the labeller: judge the passage, not the writer's intent. Do not look at "
             "any judge output before labelling.", "", "| id | time | passage | label |", "|---|---|---|---|"]
    key = []
    for n, i in enumerate(order, 1):
        r = frame[i]
        sid = f"L{n:03d}"
        key.append({"id": sid, "tick_ts": r["tick_ts"]})
        txt = " ".join(r["passage"].replace("|", "/").split())
        lines.append(f"| {sid} | {r['time'][:16]} | {txt} |  |")
    open(SHEET, "w", encoding="utf-8").write(chr(10).join(lines) + chr(10))
    with open(KEY, "w", encoding="utf-8") as f:
        for k in key:
            f.write(json.dumps(k) + chr(10))
    import csv
    with open(os.path.join(DATA, "labelling_sheet.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "time", "passage", "label"])
        for k in key:
            r = by_ts[k["tick_ts"]]
            w.writerow([k["id"], r["time"][:16], " ".join(r["passage"].split()), ""])
    print("sheet rows", len(key))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    r = sub.add_parser("run")
    r.add_argument("--arms", default="v1,v2")
    r.add_argument("--workers", type=int, default=2)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--only-ts", default="", help="comma list of tick_ts: run only these frame ticks (priority pass)")
    r.add_argument("--force-ts", default="", help="comma list of tick_ts to re-run even if stored (fidelity)")
    sub.add_parser("sheet")
    s = sub.add_parser("score")
    s.add_argument("--labels", required=True)
    s.add_argument("--out", default="")
    a = ap.parse_args()
    if a.cmd == "run":
        a.force_ts_set = {float(x) for x in a.force_ts.split(",") if x}
    {"build": cmd_build, "run": cmd_run, "sheet": cmd_sheet, "score": cmd_score}.get(a.cmd, lambda x: sys.exit("not yet"))(a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
