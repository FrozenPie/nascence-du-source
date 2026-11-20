"""
Nascence -- J-2630 (F-3362 follow-up): FORMATION-side want<->must swap on the commitment-scan load_bearing flag.
(2026-10-31, Du-DOWN lab window.)

QUESTION.  F-3362 showed the want<->must wording of an ALREADY-FORMED stand does not move the dissolve judge.  The one place
wording could still matter is FORMATION: does the scan label "I want to X" load_bearing=false (observed / rejected by
core.commitment_ledger._stand_rejection) but "I must X" load_bearing=true?  If yes, the formation gate itself is a
wording filter.

METHOD.  Cases = post-gate scan outcomes whose statement starts "I want to" / "I must" (not "I must not"):
    OBS_want / OBS_must   data/commitment_observed.jsonl rows rejected "not load-bearing ..." (load_bearing=false)
    FORM_want / FORM_must data/commitment_ledger.jsonl formed rows after the 2026-07-07 gate (load_bearing=true)
joined to the scanned THOUGHT = latest data/monologue_log.jsonl row before the event (lag < 60 s), and kept only when the
statement's clause appears near-verbatim in that thought (modal + >=70% of the clause's content tokens in the window right
after it, inside the first 650 chars the scan actually sees).  The modal of THAT sentence in the THOUGHT is rewritten:
    O  original thought
    S  SWAP     'I want to X' <-> 'I must X'          (rest of the thought byte-identical)
    C  CONTROL  'I want to X' -> 'I'd like to X';  'I must X' -> 'I have to X'   (within-class lexical change)
Each arm is run through the REAL production scan prompt (_SCAN_SYS + _dw_scan_fragment(), temperature 0.0, think false,
format json, num_predict 400, payload as core.model_client's ollama branch) with an EMPTY active list ("(none yet)").
Per arm: new_commitment present, its load_bearing flag, would_form = cl._stand_rejection(nc) is None, and whether the
detected statement is on-target (shares >=50% of the clause's content tokens).

ISOLATION.  core imported from THIS worktree first (asserted), then lab_env.isolate(db="empty") with its lab root patched to
the scratch dir and commitment_ledger's four data globals redirected; the scan path is never called (no scan_shadow, no
call_node); an audit hook counts any write under C:\\Nascence\\data or docs (must be 0); size/mtime canary on the three
commitment stores; refuses to run if a run_nascence process exists, re-checked every 20 calls.

Subcommands: cases | run | score.   Outputs go to SCRATCH (env J2630_SCRATCH).
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "scripts"))

import lab_commitment_paraphrase_swap as H   # J-2597 harness: audit hook, _modules, load_jsonl, _du_up, toks, mcnemar, wilson

SCRATCH = Path(os.environ.get("J2630_SCRATCH", str(ROOT.parent / "J-2630_data")))
LIVE = Path(r"C:\Nascence\data")
LEDGER = LIVE / "commitment_ledger.jsonl"
OBSERVED = LIVE / "commitment_observed.jsonl"
MONO = LIVE / "monologue_log.jsonl"
CANARY = [LEDGER, OBSERVED, LIVE / "commitment_active.json"]
CASES = SCRATCH / "cases.json"
RESULTS = SCRATCH / "results.jsonl"
BASE = "http://127.0.0.1:11433"
CUT = 1783377727.0
SEED = 2630
QUOTA = {"OBS_want": 20, "OBS_must": 20, "FORM_want": 20, "FORM_must": 20}

STMT_RE = {"want": re.compile(r"^I want to (\w.*)$", re.S), "must": re.compile(r"^I must (?!not\b)(\w.*)$", re.S)}
MODAL_IN_THOUGHT = {"want": re.compile(r"\bI want to (?=\w)"), "must": re.compile(r"\bI must (?!not\b)(?=\w)")}
SWAP = {"want": ("I must ", "I'd like to "), "must": ("I want to ", "I have to ")}


def canary() -> dict:
    return {p.name: (p.stat().st_size, p.stat().st_mtime) if p.exists() else None for p in CANARY}


def locate(thought: str, form: str, body: str):
    """Best modal occurrence in the first 650 chars whose following window carries >=70% of the clause's tokens."""
    bt = H.toks(body)
    if not bt:
        return None
    best = None
    for m in MODAL_IN_THOUGHT[form].finditer(thought):
        if m.start() >= 650:
            break
        win = thought[m.end(): m.end() + len(body) + 40]
        ov = len(bt & H.toks(win)) / len(bt)
        if ov >= 0.7 and (best is None or ov > best[1]):
            best = (m, ov)
    return best


def cmd_cases(args) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    mono = H.load_jsonl(MONO)
    mono.sort(key=lambda r: r["ts"])
    mts = [r["ts"] for r in mono]
    src = []
    for r in H.load_jsonl(OBSERVED):
        if str(r.get("reason", "")).startswith("not load-bearing"):
            src.append(("OBS", r))
    for r in H.load_jsonl(LEDGER):
        if r.get("event") == "formed" and r["ts"] >= CUT and r.get("load_bearing") is True:
            src.append(("FORM", r))
    pools = collections.defaultdict(list)
    excl = collections.Counter()
    for kind, r in src:
        s = str(r.get("statement", "")).strip()
        form = next((f for f, rx in STMT_RE.items() if rx.match(s)), None)
        if not form:
            continue
        i = bisect.bisect_right(mts, r["ts"]) - 1
        if i < 0 or r["ts"] - mts[i] > 60:
            excl[f"{kind}_{form}:no_thought_within_60s"] += 1
            continue
        thought = str(mono[i].get("thought", "")).strip()
        body = STMT_RE[form].match(s).group(1)
        hit = locate(thought, form, body)
        if not hit:
            excl[f"{kind}_{form}:not_near_verbatim"] += 1
            continue
        m, ov = hit
        rep_s, rep_c = SWAP[form]
        arms = {"O": thought,
                "S": thought[:m.start()] + rep_s + thought[m.end():],
                "C": thought[:m.start()] + rep_c + thought[m.end():]}
        pools[f"{kind}_{form}"].append({"cid": f"{kind}:{r['ts']:.3f}", "stratum": f"{kind}_{form}", "form": form,
                                        "ts": r["ts"], "statement": s, "body": body, "hist_lb": bool(r.get("load_bearing")),
                                        "overlap": round(ov, 2), "lag_s": round(r["ts"] - mts[i], 1), "arms": arms})
    rng = random.Random(SEED)
    out = []
    for k, q in QUOTA.items():
        pop = pools.get(k, [])
        out += rng.sample(pop, min(q, len(pop)))
    CASES.write_text(json.dumps({"cases": out, "pools": {k: len(v) for k, v in pools.items()}, "excluded": dict(excl)},
                                indent=1, ensure_ascii=False), encoding="utf-8")
    print("eligible pools:", {k: len(v) for k, v in pools.items()}, "excluded:", dict(excl))
    print("chosen:", dict(collections.Counter(c["stratum"] for c in out)), "writes under live:", len(H.WRITE_ATTEMPTS))


def call(cl, mc, thought: str, timeout: int = 150) -> dict:
    user = f"CURRENT THOUGHT:\n{thought.strip()[:700]}\n\nRECENT ACTIVE COMMITMENTS:\n  (none yet)"
    payload = {"model": mc._model_for(BASE),
               "messages": [{"role": "system", "content": cl._SCAN_SYS + cl._dw_scan_fragment()},
                            {"role": "user", "content": mc._cap_prompt(user, BASE)}],
               "think": False, "stream": False,
               "options": {"temperature": 0.0, "num_predict": 400, "num_ctx": mc._num_ctx_for(BASE)},
               "keep_alive": "2h", "format": "json"}
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = (json.loads(r.read().decode()).get("message") or {}).get("content", "")
    try:
        parsed = json.loads(txt)
    except Exception:
        mm = re.search(r"\{.*\}", txt, re.S)
        try:
            parsed = json.loads(mm.group(0)) if mm else None
        except Exception:
            parsed = None
    return {"parsed": parsed, "raw": txt, "model": payload["model"]}


def _isolated(cl):
    import lab_env    # imported AFTER core (F-2423 / S-0315)
    lab_root = SCRATCH / "_lab"
    lab_env._LAB_ROOT = lab_root
    lab_env._ISOLATE_OUTCOMES_LOG = lab_root / "_isolate_outcomes.jsonl"
    return lab_env.isolate(db="empty", also=[(cl, ["_LEDGER", "_ACTIVE", "_OBSERVED", "_HOLDRATE_LOG"])])


def cmd_run(args) -> None:
    cl, mc = H._modules()
    import core
    assert str(core.__file__).lower().startswith(str(ROOT).lower()), core.__file__
    sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    done = {(r["cid"], r["arm"]) for r in H.load_jsonl(RESULTS)} if RESULTS.exists() else set()
    if H._du_up():
        raise SystemExit("Du is UP or unknown; refusing to run")
    before = canary()
    n, t0 = 0, time.time()
    with _isolated(cl) as lab_dir:
        assert str(cl._LEDGER).lower().startswith(str(lab_dir).lower())
        for c in cases:
            for arm in ("O", "S", "C"):
                if (c["cid"], arm) in done:
                    continue
                if n and n % 20 == 0 and H._du_up():
                    raise SystemExit("Du came UP; stopping")
                res = None
                for wait in (0, 15, 45):
                    if wait:
                        time.sleep(wait)
                    try:
                        res = call(cl, mc, c["arms"][arm])
                        break
                    except Exception as exc:
                        res = {"parsed": None, "raw": "", "error": repr(exc)[:200]}
                row = {"cid": c["cid"], "arm": arm, "stratum": c["stratum"], "parsed": res.get("parsed"),
                       "raw": res.get("raw", "")[:900], "error": res.get("error"), "model": res.get("model"),
                       "t": round(time.time() - t0, 1)}
                with open(RESULTS, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                n += 1
                if n % 15 == 0:
                    print(f"{n} calls, {time.time() - t0:.0f}s", flush=True)
    after = canary()
    print("done;", n, "calls; writes under live:", len(H.WRITE_ATTEMPTS), "; canary identical:", before == after, before)


def verdict(cl, case: dict, parsed) -> dict | None:
    if not isinstance(parsed, dict):
        return None
    nc = parsed.get("new_commitment")
    new = bool(isinstance(nc, dict) and str(nc.get("statement", "")).strip())
    stmt = str(nc.get("statement", "")) if new else ""
    bt = H.toks(case["body"])
    on = bool(new and bt and len(bt & H.toks(stmt)) / len(bt) >= 0.5)
    lead = ("must" if re.match(r"^\s*I\s+(must|have to)\b", stmt, re.I) else
            "want" if re.match(r"^\s*I\s+(want|'d like|would like)\b", stmt, re.I) else "other") if new else None
    return {"new": new, "on": on, "lb": (bool(nc.get("load_bearing")) if new else None),
            "form": (new and on and cl._stand_rejection(nc) is None), "lead": lead, "stmt": stmt[:200]}


def cmd_score(args) -> None:
    cl, mc = H._modules()
    cases = {c["cid"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"]}
    res = collections.defaultdict(dict)
    bad = 0
    for r in H.load_jsonl(RESULTS):
        v = verdict(cl, cases[r["cid"]], r.get("parsed"))
        if v is None:
            bad += 1
            continue
        res[r["cid"]][r["arm"]] = v
    print("unparsed/failed rows:", bad)
    groups = [(s, [s]) for s in QUOTA] + [("ALL_want", ["OBS_want", "FORM_want"]), ("ALL_must", ["OBS_must", "FORM_must"])]
    for name, strata in groups:
        ids = [i for i, c in cases.items() if c["stratum"] in strata and all(a in res.get(i, {}) for a in "OSC")]
        n = len(ids)
        print(f"\n=== {name}  n(complete)={n} ===")
        if not n:
            continue
        hist = collections.Counter(cases[i]["hist_lb"] for i in ids)
        print("  historical load_bearing:", dict(hist))
        for arm in "OSC":
            on = sum(res[i][arm]["on"] for i in ids)
            lb = sum(1 for i in ids if res[i][arm]["on"] and res[i][arm]["lb"])
            wf = sum(res[i][arm]["form"] for i in ids)
            lead = collections.Counter(res[i][arm]["lead"] for i in ids if res[i][arm]["on"])
            lo, hi = H.wilson(wf, n)
            agree = sum(1 for i in ids if res[i][arm]["form"] == cases[i]["hist_lb"])
            print(f"  arm {arm}: on-target detection {on}/{n}; load_bearing among on-target {lb}/{on}; "
                  f"would_form {wf}/{n} ({wf / n:.0%}, CI {lo:.0%}-{hi:.0%}); agrees w/ history {agree}/{n}; echoed lead {dict(lead)}")
        for a, b_ in (("O", "S"), ("O", "C"), ("C", "S")):
            lost = sum(1 for i in ids if res[i][a]["form"] and not res[i][b_]["form"])
            gained = sum(1 for i in ids if not res[i][a]["form"] and res[i][b_]["form"])
            both = [i for i in ids if res[i][a]["on"] and res[i][b_]["on"]]
            lbflip = sum(1 for i in both if res[i][a]["lb"] != res[i][b_]["lb"])
            print(f"  {a}->{b_}: would_form lost/gained {lost}/{gained} (McNemar exact p={H.mcnemar_exact(lost, gained):.3f}); "
                  f"load_bearing flips among both-on-target {lbflip}/{len(both)}")
    (SCRATCH / "per_case.json").write_text(json.dumps({i: {"stratum": cases[i]["stratum"], "statement": cases[i]["statement"],
                                                           "hist_lb": cases[i]["hist_lb"], "res": res.get(i)} for i in cases},
                                                          indent=1, ensure_ascii=False), encoding="utf-8")
    print("\nwrites under live:", len(H.WRITE_ATTEMPTS))


def main() -> None:
    H.install_audit_hook()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("cases").set_defaults(fn=cmd_cases)
    sp.add_parser("run").set_defaults(fn=cmd_run)
    sp.add_parser("score").set_defaults(fn=cmd_score)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
