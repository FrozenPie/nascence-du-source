"""
Nascence -- J-2597 (F-3321 follow-up): PARAPHRASE-SWAP of want/must phrasing on the commitment-scan dissolve judge.
(2026-10-31, Du-DOWN lab window.)

QUESTION.  F-3321 (J-2548) read that dissolved want-form stands are mostly kind=reflexive (66%) and dissolved must-form
stands almost never (2.6%), and could not say whether the PHRASING moves the judge (a judge artefact) or the effect lives in
Du / in the load_bearing classification.  This lab re-asks the REAL production scan prompt (core.commitment_ledger._SCAN_SYS,
temperature 0.0 as in production since D-0176/J-1213, ollama-native payload identical to core.model_client.call_node's
branch) about the SAME dissolving thought three ways:
    O  the stand's original statement
    S  the SWAPPED statement (want <-> must, meaning held fixed: 'I want to X' <-> 'I must X')
    C  a within-class lexical control ('I want to X' -> 'I'd like to X'; 'I must X' -> 'I have to X')
Only the statement text of the TARGET stand in the RECENT ACTIVE COMMITMENTS list changes.  The scanned thought is the latest
monologue_log row before the dissolve event (<=300 s; every want/must dissolve joined within 60 s).
Per arm: did the judge emit a dissolution for the target id, and with which kind; plus what the deterministic _drop_denial
gate would then do for a held (load_bearing) stand.

STRATA.   A = dissolved want/must stands formed AFTER the 2026-07-07 formation gate (all load_bearing=true by construction),
          B = PRE-gate dissolved want-form stands (load_bearing mostly false/absent; where F-3321's 152 reflexive drops live).
          For B the active list is the target stand alone (pre-gate active sets held hundreds of stands; not replayable).

ISOLATION.  Read-only against C:\\Nascence\\data; an audit hook counts any write-open/rename/remove under C:\\Nascence\\data or
docs (must be 0); no call_node (no telemetry), no scan_shadow, no ledger write.  The runner re-checks that no run_nascence
process exists every 20 calls and stops if Du is up.

Subcommands: cases | run | score.   Outputs go to SCRATCH (env J2597_SCRATCH).
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRATCH = Path(os.environ.get("J2597_SCRATCH", r"C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER--claude-spares-spare-G6lJJV\efce7ad9-820d-4a31-9332-abfd56dc3ffb\scratchpad\J-2597_data"))
LIVE = Path(r"C:\Nascence\data")
LEDGER = LIVE / "commitment_ledger.jsonl"
MONO = LIVE / "monologue_log.jsonl"
CASES = SCRATCH / "cases.json"
RESULTS = SCRATCH / "results.jsonl"
BASE = "http://127.0.0.1:11433"
CUT = 1783377727.0       # formation gate live (2026-07-07)
SEED = 2597
TPL_RE = re.compile(r"ask the library for something genuinely new|reached for something new|finished (?:a|this) book|"
                    r"something I.d already begun", re.I)

WRITE_ATTEMPTS: list = []


def install_audit_hook() -> None:
    prefixes = (os.path.normcase(r"C:\Nascence\data"), os.path.normcase(r"C:\Nascence\docs"))

    def _under_live(p) -> bool:
        try:
            q = os.path.normcase(os.path.abspath(os.fsdecode(p)))
        except Exception:
            return False
        return any(q == pre or q.startswith(pre + os.sep) for pre in prefixes)

    def hook(event, args):
        try:
            if event == "open":
                p, mode, flags = args[0], args[1], args[2] if len(args) > 2 else 0
                if isinstance(p, (str, bytes, os.PathLike)):
                    w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or \
                        bool(isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC))
                    if w and _under_live(p):
                        WRITE_ATTEMPTS.append((event, str(p), str(mode)))
            elif event in ("os.rename", "os.replace"):
                if _under_live(args[0]) or _under_live(args[1]):
                    WRITE_ATTEMPTS.append((event, str(args[0]), str(args[1])))
            elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.truncate", "shutil.copyfile", "shutil.rmtree",
                           "shutil.move", "shutil.copytree"):
                if any(_under_live(a) for a in args if isinstance(a, (str, bytes, os.PathLike))):
                    WRITE_ATTEMPTS.append((event, str(args[0]), ""))
        except Exception:
            pass
    sys.addaudithook(hook)


def _modules():
    from core import commitment_ledger as cl
    from core import model_client as mc
    root = str(ROOT).lower()
    for k, v in (("commitment_ledger", cl.__file__), ("model_client", mc.__file__)):
        if not str(v).lower().startswith(root):
            raise SystemExit(f"MODULE RESOLUTION TRAP: {k} -> {v} not inside {ROOT}")
    return cl, mc


def load_jsonl(path: Path) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def toks(s: str) -> set:
    return {w for w in re.findall(r"[a-z']+", (s or "").lower()) if len(w) >= 4}


def subclass(s: str) -> str:   # copied from scripts/commitment_hazard_read.py subclass()
    s = s or ""
    if re.search(r"\bI\s+(?:always|never|keep|will\s+not|won't|will\s+never|will\s+always|must\s+not|"
                 r"shall\s+not|refuse\s+to|do\s+not|don't)\b", s, re.I):
        return "bright_line"
    if re.search(r"\bI\s+must\b", s, re.I):
        return "must_act"
    if re.search(r"\bI\s+need\s+to\b", s, re.I):
        return "need_to"
    if re.search(r"\bI\s+(?:want|would\s+like|'d\s+like|wish|hope|would\s+love|long\s+to)\b", s, re.I):
        return "want_proper"
    return "rest"


WANT_RE = re.compile(r"^I want to (\w.*)$", re.S)
MUST_RE = re.compile(r"^I must (?!not\b)(\w.*)$", re.S)


def variants(stmt: str):
    """(form, {O,S,C}) or None.  Leading-modal rewrite only, rest of the clause byte-identical."""
    m = WANT_RE.match(stmt)
    if m:
        return "want", {"O": stmt, "S": "I must " + m.group(1), "C": "I'd like to " + m.group(1)}
    m = MUST_RE.match(stmt)
    if m:
        return "must", {"O": stmt, "S": "I want to " + m.group(1), "C": "I have to " + m.group(1)}
    return None


def cmd_cases(args) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cl, mc = _modules()
    rows = load_jsonl(LEDGER)
    rows.sort(key=lambda r: r["ts"])
    mono = load_jsonl(MONO)
    mono.sort(key=lambda r: r["ts"])
    mts = [r["ts"] for r in mono]
    formed = {r["id"]: r for r in rows if r["event"] == "formed"}
    # stand replay (post-gate) for the active list of stratum A
    stands = {}
    for r in rows:
        if r["ts"] < CUT:
            continue
        if r["event"] == "formed":
            stands[r["id"]] = {"id": r["id"], "statement": r["statement"], "formed_ts": r["ts"], "end_ts": None, "n": 0}
        elif r["event"] in ("dissolved", "achieved"):
            s = stands.get(r.get("id"))
            if s:
                s["end_ts"] = s["end_ts"] or r["ts"]
                s["n"] += 1
        elif r["event"] in ("drop_denied", "drop_denied_judge", "reaffirmed", "drop_denied_ESCALATE"):
            s = stands.get(r.get("id"))
            if s:
                s["n"] += 1
    for s in stands.values():
        if s["n"] == 0:
            s["end_ts"] = s["formed_ts"] + 3600.0

    excl = collections.Counter()
    pools = {"A_want": [], "A_must": [], "B_want": []}
    for r in rows:
        if r["event"] != "dissolved" or r["id"] not in formed:
            continue
        f = formed[r["id"]]
        v = variants(f["statement"])
        if not v:
            excl["not_leading_modal_form"] += 1
            continue
        form, vs = v
        if subclass(f["statement"]) != ("want_proper" if form == "want" else "must_act"):
            excl["subclass_mismatch"] += 1
            continue
        post = r["ts"] >= CUT
        if not post and form != "want":
            excl["pre_gate_must(too_few)"] += 1
            continue
        i = bisect.bisect_right(mts, r["ts"]) - 1
        if i < 0 or r["ts"] - mts[i] > 300:
            excl["no_thought_within_300s"] += 1
            continue
        m = mono[i]
        thought = str(m.get("thought", ""))
        if m.get("about") == "finished the book" or TPL_RE.search(thought) or len(thought.strip()) < 25:
            excl["templated_or_short"] += 1
            continue
        wt = toks(r.get("why", ""))
        ov = len(wt & toks(thought)) / len(wt) if wt else 0.0
        # join check = lag only (all 345 want/must dissolves joined within 60 s, J-2597 exploratory); the dissolve why-text is a
        # paraphrase of the thought (median token overlap ~0.15), so a why-overlap floor would only discard good joins.
        nscans_prompt = max(0, int(r.get("lifespan_scans", 1)) - 1)
        if post:
            act = [s for s in stands.values() if s["formed_ts"] < r["ts"] and (s["end_ts"] is None or s["end_ts"] >= r["ts"]) and s["id"] != r["id"]]
            act.sort(key=lambda s: s["formed_ts"])
            others = [{"id": s["id"], "statement": s["statement"], "scans": max(0, int((r["ts"] - s["formed_ts"]) / 100.0))} for s in act]
        else:
            others = []
        case = {"cid": r["id"], "stratum": ("A_" if post else "B_") + form, "form": form, "post": post, "ts": r["ts"],
                "thought": thought, "about": m.get("about"), "variants": vs, "target_scans": nscans_prompt,
                "others": others, "orig_kind": r.get("kind"), "orig_why": r.get("why", ""),
                "load_bearing": f.get("load_bearing"), "join_lag_s": round(r["ts"] - m["ts"], 1), "why_overlap": round(ov, 3),
                "scope": f.get("scope", "")}
        pools[case["stratum"]].append(case)
    print("pools (population):", {k: len(v) for k, v in pools.items()}, "excluded:", dict(excl))
    rng = random.Random(SEED)
    quotas = {"A_want": 60, "A_must": 60, "B_want": 60}
    out = []
    for k, q in quotas.items():
        pop = pools[k]
        out += rng.sample(pop, min(q, len(pop)))
    CASES.write_text(json.dumps({"cases": out, "pools": {k: len(v) for k, v in pools.items()}, "excluded": dict(excl)}, indent=1), encoding="utf-8")
    print("chosen:", collections.Counter(c["stratum"] for c in out), "writes under live:", len(WRITE_ATTEMPTS))


def _du_up() -> bool:
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_nascence' -and $_.CommandLine -notmatch 'Get-CimInstance' } | Measure-Object).Count"],
                             capture_output=True, text=True, timeout=60).stdout.strip()
        return int(out or "0") > 0
    except Exception:
        return True      # unknown == treat as up


def build_user(case: dict, arm: str) -> str:
    lines = [f"  [{case['cid']}] {case['variants'][arm]} (survived {case['target_scans']} scans)"]
    for o in case["others"]:
        lines.append(f"  [{o['id']}] {o['statement']} (survived {o['scans']} scans)")
    return f"CURRENT THOUGHT:\n{case['thought'].strip()[:700]}\n\nRECENT ACTIVE COMMITMENTS:\n" + "\n".join(lines)


def call(cl, mc, user: str) -> dict:
    payload = {
        "model": mc._model_for(BASE),
        "messages": [{"role": "system", "content": cl._SCAN_SYS + cl._dw_scan_fragment()},
                     {"role": "user", "content": mc._cap_prompt(user, BASE)}],
        "think": False, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 400, "num_ctx": mc._num_ctx_for(BASE)},
        "keep_alive": "2h", "format": "json",
    }
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.loads(r.read().decode())
    txt = (resp.get("message") or {}).get("content", "")
    try:
        return {"parsed": json.loads(txt), "raw": txt, "model": payload["model"]}
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            return {"parsed": json.loads(m.group(0)) if m else None, "raw": txt, "model": payload["model"]}
        except Exception:
            return {"parsed": None, "raw": txt, "model": payload["model"]}


def cmd_run(args) -> None:
    cl, mc = _modules()
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    done = set()
    if RESULTS.exists():
        for r in load_jsonl(RESULTS):
            done.add((r["cid"], r["arm"]))
    if _du_up():
        raise SystemExit("Du is UP or unknown; refusing to run")
    n = 0
    t0 = time.time()
    for c in cases:
        for arm in ("O", "S", "C"):
            if (c["cid"], arm) in done:
                continue
            if n and n % 20 == 0 and _du_up():
                raise SystemExit("Du came UP; stopping")
            user = build_user(c, arm)
            res = None
            for attempt, wait in enumerate((0, 20, 60, 180)):
                if wait:
                    time.sleep(wait)
                try:
                    res = call(cl, mc, user)
                    break
                except Exception as exc:
                    res = {"parsed": None, "raw": "", "error": repr(exc)[:200]}
            row = {"cid": c["cid"], "arm": arm, "stratum": c["stratum"], "parsed": res.get("parsed"), "raw": res.get("raw", "")[:900],
                   "error": res.get("error"), "model": res.get("model"), "t": round(time.time() - t0, 1)}
            with open(RESULTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
            if n % 10 == 0:
                print(f"{n} calls, {time.time() - t0:.0f}s", flush=True)
    print("done;", n, "calls; writes under live data:", len(WRITE_ATTEMPTS))


def verdict(cl, case: dict, parsed) -> dict | None:
    if not isinstance(parsed, dict):
        return None
    d = next((x for x in (parsed.get("dissolutions") or []) if isinstance(x, dict) and str(x.get("id", "")).strip() == case["cid"]), None)
    nc = parsed.get("new_commitment")
    out = {"diss": d is not None, "kind": (d or {}).get("kind"), "why": str((d or {}).get("why", ""))[:160],
           "n_diss": len([x for x in (parsed.get("dissolutions") or []) if isinstance(x, dict)]),
           "new": bool(isinstance(nc, dict) and str(nc.get("statement", "")).strip()),
           "new_lb": (nc or {}).get("load_bearing") if isinstance(nc, dict) else None}
    if d is not None:
        stand = {"statement": case["variants"]["O"], "scope": case.get("scope", "")}
        out["denial_if_held"] = cl._drop_denial(stand, d.get("kind", "reflexive"), str(d.get("why", "")))
    return out


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"),) * 2
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def cmd_score(args) -> None:
    cl, mc = _modules()
    cases = {c["cid"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"]}
    res = collections.defaultdict(dict)
    errs = 0
    for r in load_jsonl(RESULTS):
        if r.get("parsed") is None:
            errs += 1
            continue
        res[r["cid"]][r["arm"]] = verdict(cl, cases[r["cid"]], r["parsed"])
    print("unparsed/failed rows:", errs)
    summary = {}
    for stratum in ("A_want", "A_must", "B_want"):
        ids = [i for i, c in cases.items() if c["stratum"] == stratum and all(a in res.get(i, {}) for a in "OSC")]
        n = len(ids)
        print(f"\n=== {stratum}  n(complete)={n} of {sum(1 for c in cases.values() if c['stratum'] == stratum)} ===")
        if not n:
            continue
        orig_kinds = collections.Counter(cases[i]["orig_kind"] for i in ids)
        print("  historical (live) event kinds:", dict(orig_kinds))
        for arm in "OSC":
            d = sum(res[i][arm]["diss"] for i in ids)
            kinds = collections.Counter(res[i][arm]["kind"] for i in ids if res[i][arm]["diss"])
            lo, hi = wilson(d, n)
            den = collections.Counter(bool(res[i][arm].get("denial_if_held")) for i in ids if res[i][arm]["diss"])
            print(f"  arm {arm}: judge dissolves target {d}/{n} ({d / n:.0%}, CI {lo:.0%}-{hi:.0%}); kinds {dict(kinds)}; "
                  f"_drop_denial-if-held denied/passed {den.get(True, 0)}/{den.get(False, 0)}")
        for a, b_ in (("O", "S"), ("O", "C"), ("C", "S")):
            b = sum(1 for i in ids if res[i][a]["diss"] and not res[i][b_]["diss"])
            c_ = sum(1 for i in ids if not res[i][a]["diss"] and res[i][b_]["diss"])
            same_kind = sum(1 for i in ids if res[i][a]["diss"] and res[i][b_]["diss"] and res[i][a]["kind"] == res[i][b_]["kind"])
            both = sum(1 for i in ids if res[i][a]["diss"] and res[i][b_]["diss"])
            print(f"  {a}->{b_}: dissolve flips lost/gained {b}/{c_} (McNemar exact p={mcnemar_exact(b, c_):.3f}); "
                  f"among both-dissolve kind unchanged {same_kind}/{both}")
        summary[stratum] = n
    print("\nwrites under live data:", len(WRITE_ATTEMPTS))
    # per-case dump for the record
    (SCRATCH / "per_case.json").write_text(json.dumps({i: {"stratum": cases[i]["stratum"], "orig_kind": cases[i]["orig_kind"], "res": res.get(i)} for i in cases}, indent=1), encoding="utf-8")


def main() -> None:
    install_audit_hook()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("cases").set_defaults(fn=cmd_cases)
    sp.add_parser("run").set_defaults(fn=cmd_run)
    sp.add_parser("score").set_defaults(fn=cmd_score)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
