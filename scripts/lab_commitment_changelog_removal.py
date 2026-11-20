"""
Nascence -- J-2847 (P-0038 / F-0040, capacity_to_commit): paired replay for removing the change-log text from the commitment
scan prompt.  LAB ONLY: core/commitment_ledger.py is NOT edited; the variant is built in memory from the production prompt by
asserted anchor replacements.

QUESTION.  Can the change-log fragment
    " (W2.0, 2026-07-03; negative-example set broadened 2026-09-02 per F-0055/F-0677 -- the original single example didn't
      generalize, letting a run of short physical-task statements slip through as load-bearing)"
be removed from core.commitment_ledger._SCAN_SYS, AND the done_when fragment (core/done_when.py scan_fragment(), appended
AFTER the "Output ONLY" contract line today) be folded in BEFORE the "Output ONLY" contract line, with ZERO change in
detection?

ARMS (both run FRESH in the same window, same seat, so seat drift cannot masquerade as a wording effect):
    a  production:  cl._SCAN_SYS + cl._dw_scan_fragment()
    b  variant:     _SCAN_SYS minus the change-log parenthetical, with the done_when fragment placed before "Output ONLY"
    a2 repeat of a on 10 form + 5 dissolve cases (determinism / validity guard)
Cases: the J-2653 prep.json (75 J-2630 formation cases, arm O = the original thought; 30 J-2597 dissolve cases, arm O),
copied to docs/lab/J-2847_data/prep.json.  qwen3.5:9b on the hot lane :11433, temperature 0.0, think false, format json,
num_predict 400, empty active list for formation (identical call shape to J-2630/J-2653).

ISOLATION.  Same as J-2653: audit hook (0 writes under C:\\Nascence\\data or docs), lab_env.isolate(db="empty") with the lab root
patched into scratch and commitment_ledger's data globals redirected, size/mtime canary on the three commitment stores, refuses
to run if a run_nascence process exists (re-checked every 20 calls).  No scan_shadow, no call_node.

Subcommands: run | score.  Outputs go to SCRATCH (env J2847_SCRATCH).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(os.environ.get("J2847_SCRATCH", str(ROOT.parent / "J-2847_data")))
os.environ["J2630_SCRATCH"] = str(SCRATCH)          # the J-2630 harness's lab root + _isolated() land in OUR scratch
os.environ["J2597_SCRATCH"] = str(SCRATCH)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "scripts"))

import lab_commitment_paraphrase_swap as H     # audit hook, _modules, toks, load_jsonl, _du_up, verdict (dissolve)
import lab_commitment_formation_swap as F      # formation verdict, canary, _isolated

PREP = ROOT / "docs" / "lab" / "J-2847_data" / "prep.json"
RESULTS = SCRATCH / "results.jsonl"
BASE = os.environ.get("J2847_BASE", "http://127.0.0.1:11433")

CHANGELOG = (" (W2.0, 2026-07-03; negative-example set broadened 2026-09-02 per F-0055/F-0677 \u2014 the original single "
             "example didn't generalize, letting a run of short physical-task statements slip through as load-bearing)")
CONTRACT_ANCHOR = "Output ONLY a JSON object:"


def production_sys(cl) -> str:
    return cl._SCAN_SYS + cl._dw_scan_fragment()


def variant_sys(cl, drop_changelog: bool = True, fold_fragment: bool = True) -> str:
    """Production prompt minus the change-log text (drop_changelog), with the done_when fragment folded in before the
    contract line (fold_fragment).  Both True = pre-registered arm b; only-changelog = exploratory arm b1; only-fold = b2."""
    p = cl._SCAN_SYS
    assert p.count(CHANGELOG) == 1, "production prompt drifted; change-log anchor not found exactly once"
    assert p.count(CONTRACT_ANCHOR) == 1, "production prompt drifted; contract anchor not found exactly once"
    frag = cl._dw_scan_fragment()
    assert frag.strip(), "done_when fragment is empty (DONE_WHEN_AT_OPEN off?): nothing to fold, arm would be meaningless"
    v = p.replace(CHANGELOG, "") if drop_changelog else p
    if not fold_fragment:
        return v + frag
    head, tail = v.split(CONTRACT_ANCHOR)
    assert head.endswith("counts.\n"), repr(head[-30:])
    return head + frag.strip() + "\n" + CONTRACT_ANCHOR + tail


def chat(system: str, user: str, mc, timeout: int = 240) -> dict:
    payload = {"model": mc._model_for(BASE),
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": mc._cap_prompt(user, BASE)}],
               "think": False, "stream": False,
               "options": {"temperature": 0.0, "num_predict": 400, "num_ctx": mc._num_ctx_for(BASE)},
               "keep_alive": "2h", "format": "json"}
    req = urllib.request.Request(BASE + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        txt = (json.loads(r.read().decode()).get("message") or {}).get("content", "")
    try:
        parsed = json.loads(txt)
    except Exception:
        import re
        mm = re.search(r"\{.*\}", txt, re.S)
        try:
            parsed = json.loads(mm.group(0)) if mm else None
        except Exception:
            parsed = None
    return {"parsed": parsed, "raw": txt, "model": payload["model"]}


def form_user(thought: str) -> str:
    return f"CURRENT THOUGHT:\n{thought.strip()[:700]}\n\nRECENT ACTIVE COMMITMENTS:\n  (none yet)"


def cmd_run(args) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cl, mc = H._modules()
    import core
    assert str(core.__file__).lower().startswith(str(ROOT).lower()), core.__file__
    sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    psys, vsys = production_sys(cl), variant_sys(cl)
    explore = getattr(args, "explore", False)      # EXPLORATORY decomposition arms, added after the pre-registered verdict
    assert psys != vsys and len(vsys) < len(psys) + len(cl._dw_scan_fragment())
    (SCRATCH / "prompt_a.txt").write_text(psys, encoding="utf-8")
    (SCRATCH / "prompt_b.txt").write_text(vsys, encoding="utf-8")
    arms = [("a", psys), ("b", vsys)]
    if explore:
        arms = [("b1", variant_sys(cl, True, False)), ("b2", variant_sys(cl, False, True))]
    jobs = []
    for c in prep["form_cases"]:
        for prompt, system in arms:
            jobs.append(("form", prompt, "O", c["cid"], system, form_user(c["arms"]["O"])))
    for c in prep["diss_cases"]:
        for prompt, system in arms:
            jobs.append(("diss", prompt, "O", c["cid"], system, H.build_user(c, "O")))
    fc = {c["cid"]: c for c in prep["form_cases"]}
    dc = {c["cid"]: c for c in prep["diss_cases"]}
    if not explore:
        for cid in prep["det_form"]:
            jobs.append(("form", "a2", "O", cid, psys, form_user(fc[cid]["arms"]["O"])))
        for cid in prep["det_diss"]:
            jobs.append(("diss", "a2", "O", cid, psys, H.build_user(dc[cid], "O")))
    done = {(r["kind"], r["prompt"], r["arm"], r["cid"]) for r in H.load_jsonl(RESULTS)} if RESULTS.exists() else set()
    if H._du_up():
        raise SystemExit("Du is UP or unknown; refusing to run")
    before = F.canary()
    n, t0 = 0, time.time()
    with F._isolated(cl) as lab_dir:
        assert str(cl._LEDGER).lower().startswith(str(lab_dir).lower())
        for kind, prompt, arm, cid, system, user in jobs:
            if (kind, prompt, arm, cid) in done:
                continue
            if n and n % 20 == 0 and H._du_up():
                raise SystemExit("Du came UP; stopping")
            res = None
            for wait in (0, 15, 45):
                if wait:
                    time.sleep(wait)
                try:
                    res = chat(system, user, mc)
                    break
                except Exception as exc:
                    res = {"parsed": None, "raw": "", "error": repr(exc)[:200]}
            row = {"kind": kind, "prompt": prompt, "arm": arm, "cid": cid, "parsed": res.get("parsed"),
                   "raw": res.get("raw", "")[:900], "error": res.get("error"), "model": res.get("model"),
                   "t": round(time.time() - t0, 1)}
            with open(RESULTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
            if n % 15 == 0:
                print(f"{n} calls, {time.time() - t0:.0f}s", flush=True)
    after = F.canary()
    print("done;", n, "calls; writes under live:", len(H.WRITE_ATTEMPTS), "; canary identical:", before == after, before)


def _dw_present(parsed) -> bool:
    nc = (parsed or {}).get("new_commitment") if isinstance(parsed, dict) else None
    return bool(isinstance(nc, dict) and str(nc.get("done_when", "")).strip())


def compare(cl, prep: dict, rows: list, other: str = "b") -> dict:
    """Pure scoring over result rows; returns the numbers the pre-registered rule needs."""
    fc = {c["cid"]: c for c in prep["form_cases"]}
    dc = {c["cid"]: c for c in prep["diss_cases"]}
    fv = collections.defaultdict(dict)       # prompt -> cid -> verdict
    dv = collections.defaultdict(dict)
    parsed_of = collections.defaultdict(dict)
    bad = collections.Counter()
    for r in rows:
        if r["kind"] == "form":
            v = F.verdict(cl, fc[r["cid"]], r.get("parsed"))
            if v is None:
                bad[r["prompt"]] += 1
                continue
            fv[r["prompt"]][r["cid"]] = v
        else:
            if not isinstance(r.get("parsed"), dict):
                bad[r["prompt"]] += 1
                continue
            dv[r["prompt"]][r["cid"]] = H.verdict(cl, dc[r["cid"]], r["parsed"])
        parsed_of[(r["kind"], r["prompt"])][r["cid"]] = r.get("parsed")
    out: dict = {"unparsed": dict(bad)}
    ids = [i for i in fc if i in fv["a"] and i in fv[other]]
    out["form_n"] = len(ids)
    out["form_wf_same"] = sum(fv["a"][i]["form"] == fv[other][i]["form"] for i in ids)
    out["form_wf_flips"] = [(i, fc[i]["stratum"], fv["a"][i]["form"], fv[other][i]["form"]) for i in ids if fv["a"][i]["form"] != fv[other][i]["form"]]
    out["form_wf_a"] = sum(fv["a"][i]["form"] for i in ids)
    out["form_wf_b"] = sum(fv[other][i]["form"] for i in ids)
    out["form_new_same"] = sum(fv["a"][i]["new"] == fv[other][i]["new"] for i in ids)
    out["form_lb_same_when_both_new"] = (sum(fv["a"][i]["lb"] == fv[other][i]["lb"] for i in ids if fv["a"][i]["new"] and fv[other][i]["new"]),
                                         sum(1 for i in ids if fv["a"][i]["new"] and fv[other][i]["new"]))
    out["form_stmt_identical"] = sum(fv["a"][i]["stmt"] == fv[other][i]["stmt"] for i in ids)
    dids = [i for i in dc if i in dv["a"] and i in dv[other]]
    out["diss_n"] = len(dids)
    out["diss_same"] = sum((dv["a"][i]["diss"], dv["a"][i]["kind"]) == (dv[other][i]["diss"], dv[other][i]["kind"]) for i in dids)
    out["diss_flips"] = [(i, dc[i]["stratum"], (dv["a"][i]["diss"], dv["a"][i]["kind"]), (dv[other][i]["diss"], dv[other][i]["kind"]))
                         for i in dids if (dv["a"][i]["diss"], dv["a"][i]["kind"]) != (dv[other][i]["diss"], dv[other][i]["kind"])]
    out["diss_a"] = sum(dv["a"][i]["diss"] for i in dids)
    out["diss_b"] = sum(dv[other][i]["diss"] for i in dids)
    # done_when still produced (the fold's own side effect; reported, not part of the pass rule)
    fids = [i for i in ids if fv["a"][i]["new"] or fv[other][i]["new"]]
    out["dw_nonempty_when_new"] = {p: (sum(_dw_present(parsed_of[("form", p)].get(i)) for i in fids if fv[p][i]["new"]),
                                       sum(1 for i in fids if fv[p][i]["new"])) for p in ("a", other)}
    # determinism guard: a2 vs a
    mm = [i for i in fv["a2"] if i in fv["a"]]
    dd = [i for i in dv["a2"] if i in dv["a"]]
    out["det_form"] = (sum(fv["a"][i]["form"] == fv["a2"][i]["form"] for i in mm), len(mm))
    out["det_diss"] = (sum((dv["a"][i]["diss"], dv["a"][i]["kind"]) == (dv["a2"][i]["diss"], dv["a2"][i]["kind"]) for i in dd), len(dd))
    return out


def cmd_score(args) -> None:
    cl, mc = H._modules()
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    rows = H.load_jsonl(RESULTS)
    other = getattr(args, "other", "b") or "b"
    o = compare(cl, prep, rows, other)
    print(json.dumps(o, indent=1, ensure_ascii=False, default=str))
    if other != "b":     # exploratory decomposition arm: numbers only, no verdict
        print(f"\n[exploratory arm {other}] identical would_form {o['form_wf_same']}/{o['form_n']}; identical dissolve verdict+kind {o['diss_same']}/{o['diss_n']}")
        (SCRATCH / f"score_J-2847_{other}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        return
    p_form = o["form_n"] == 75 and o["form_wf_same"] >= 73
    p_diss = o["diss_n"] == 30 and o["diss_same"] >= 28
    valid = o["det_form"][0] >= o["det_form"][1] - 1 and o["det_diss"][0] >= o["det_diss"][1] - 1 and o["det_form"][1] == 10 and o["det_diss"][1] == 5
    print(f"\nFORMATION identical would_form {o['form_wf_same']}/{o['form_n']} (need >=73/75): {'PASS' if p_form else 'FAIL'}")
    print(f"DISSOLVE identical verdict+kind {o['diss_same']}/{o['diss_n']} (need >=28/30): {'PASS' if p_diss else 'FAIL'}")
    print(f"VALIDITY (production repeats a2 vs a: form {o['det_form']}, diss {o['det_diss']}; need <=1 flip each): {'OK' if valid else 'FAILED -> verdict INCONCLUSIVE'}")
    verdict = "INCONCLUSIVE" if not valid else ("PASS" if (p_form and p_diss) else "FAIL")
    print("VERDICT:", verdict)
    (SCRATCH / "score_J-2847.json").write_text(json.dumps({"numbers": o, "verdict": verdict}, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print("writes under live:", len(H.WRITE_ATTEMPTS))


def main() -> None:
    H.install_audit_hook()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("run", cmd_run), ("score", cmd_score)):
        sub = sp.add_parser(name)
        sub.set_defaults(fn=fn)
        if name == "score":
            sub.add_argument("--other", default="b", help="arm to compare with production a (b = pre-registered; b1/b2 = exploratory)")
        if name == "run":
            sub.add_argument("--explore", action="store_true", help="run the exploratory b1 (change-log only) and b2 (fold only) arms")
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
