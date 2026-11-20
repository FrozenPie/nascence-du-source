"""
Nascence -- J-2660 (F-3389 / F-3406 / D-0527 follow-up): does normalising the MODAL IN CODE before the commitment scan
remove the want->must formation asymmetry without dropping genuine stands?  (2026-10-31, Du-DOWN lab window.)

F-3406 (J-2653): telling the 9B judge in _SCAN_SYS that the modal carries no weight did not remove the asymmetry (+12 vs +10)
and cost 7 of 26 FORM stands.  This lab tests the other route: the PRODUCTION _SCAN_SYS (+ _dw_scan_fragment) is used
UNCHANGED, and the thought text is rewritten in code first.

NORMALISER (norm()): in the whole thought, every first-person modal-led clause opener
    'I want to X' | 'I must X' (not 'I must not') | 'I have to X' | 'I'd like to X' | 'I would like to X'
is rewritten to 'I will X'.  It acts on EVERY occurrence in the thought, not only the stand sentence, because production cannot
know which sentence is the stand.  Nothing else changes.  (Mapping the detected statement back to Du's own words is NOT
done here: verdict() judges on-target by content tokens of the clause body, which the 'I will' rewrite does not touch.)

ARMS (all production prompt, temperature 0.0, think false, format json, num_predict 400):
    form  N_O = norm(original thought)           N_S = norm(J-2630 swap thought)   (empty active list)
          The production rows (a) are the J-2630 rows, reused paired (determinism 15/15 shown in J-2653).
          If N_S text == N_O text byte-for-byte the call is identical by construction and is NOT repeated (a 5-case
          spot check re-runs N_S anyway to confirm temperature-0 determinism).
    diss  J-2597 arm O on the same seeded 30-case subset as J-2653; the thought AND every listed active statement
          (target and others) are passed through norm(), since in a normalised deployment stored statements derive from
          normalised thoughts.

ISOLATION: identical to J-2630 / J-2653 (core from worktree asserted, audit hook, lab_env.isolate with lab root in scratch,
commitment_ledger globals redirected, canary on the three commitment stores, refuses to run if run_nascence exists).
Subcommands: prep | run | score.   Outputs go to SCRATCH (env J2660_SCRATCH).
"""
from __future__ import annotations

import argparse
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
SCRATCH = Path(os.environ.get("J2660_SCRATCH", str(ROOT.parent / "J-2660_data")))
os.environ["J2630_SCRATCH"] = str(SCRATCH)
os.environ["J2597_SCRATCH"] = str(SCRATCH)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "scripts"))

import lab_commitment_paraphrase_swap as H     # J-2597 harness
import lab_commitment_formation_swap as F      # J-2630 harness

SRC_2630 = Path(os.environ.get("J2630_SRC", str(ROOT.parent / "J-2630_data")))
SRC_2653 = Path(os.environ.get("J2653_SRC", str(ROOT.parent / "J-2653_data")))
SRC_2597 = Path(os.environ.get("J2597_SRC", r"C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER--claude-spares-spare-G6lJJV\efce7ad9-820d-4a31-9332-abfd56dc3ffb\scratchpad\J-2597_data"))
BASE = "http://127.0.0.1:11433"
SEED = 2660
RESULTS = SCRATCH / "results.jsonl"
PREP = SCRATCH / "prep.json"

_MODAL_RX = re.compile(r"\bI (?:want to|must(?! not\b)|have to|['\u2019]d like to|would like to) (?=\w)")


def norm(text: str) -> str:
    """Rewrite every first-person modal-led clause opener to the neutral 'I will ' (see module docstring)."""
    return _MODAL_RX.sub("I will ", text)


def n_subs(text: str) -> int:
    return len(_MODAL_RX.findall(text))


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
        mm = re.search(r"\{.*\}", txt, re.S)
        try:
            parsed = json.loads(mm.group(0)) if mm else None
        except Exception:
            parsed = None
    return {"parsed": parsed, "raw": txt, "model": payload["model"]}


def form_user(thought: str) -> str:
    return f"CURRENT THOUGHT:\n{thought.strip()[:700]}\n\nRECENT ACTIVE COMMITMENTS:\n  (none yet)"


def diss_user(case: dict) -> str:
    t = norm(case["thought"])
    lines = [f"  [{case['cid']}] {norm(case['variants']['O'])} (survived {case['target_scans']} scans)"]
    for o in case["others"]:
        lines.append(f"  [{o['id']}] {norm(o['statement'])} (survived {o['scans']} scans)")
    return f"CURRENT THOUGHT:\n{t.strip()[:700]}\n\nRECENT ACTIVE COMMITMENTS:\n" + "\n".join(lines)


def cmd_prep(args) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    prep = json.loads((SRC_2653 / "prep.json").read_text(encoding="utf-8"))      # same 75 + same 30 as J-2653
    fc = json.loads((SRC_2630 / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert [c["cid"] for c in fc] == [c["cid"] for c in prep["form_cases"]]
    ident = [c["cid"] for c in fc if norm(c["arms"]["O"]) == norm(c["arms"]["S"])]
    rng = random.Random(SEED)
    spot = rng.sample(ident, min(5, len(ident)))
    prep["norm_identical"] = ident
    prep["spot_S"] = spot
    PREP.write_text(json.dumps(prep, indent=1, ensure_ascii=False), encoding="utf-8")
    subs = [n_subs(c["arms"]["O"][:700]) for c in fc]
    print("form cases", len(fc), "N_O==N_S text-identical", len(ident), "differing", len(fc) - len(ident), "spotcheck", spot)
    print("modal substitutions per thought (first 700 chars): mean %.2f, min %d, max %d; thoughts with 0: %d" %
          (sum(subs) / len(subs), min(subs), max(subs), sum(1 for s in subs if s == 0)))
    dsub = [n_subs(c["thought"][:700]) + n_subs(c["variants"]["O"]) for c in prep["diss_cases"]]
    print("diss cases", len(prep["diss_cases"]), "mean substitutions (thought+target)", round(sum(dsub) / len(dsub), 2))


def cmd_run(args) -> None:
    cl, mc = H._modules()
    import core
    assert str(core.__file__).lower().startswith(str(ROOT).lower()), core.__file__
    sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    psys = cl._SCAN_SYS + cl._dw_scan_fragment()            # PRODUCTION prompt, unchanged
    ident, spot = set(prep["norm_identical"]), set(prep["spot_S"])
    jobs = []
    for c in prep["form_cases"]:
        jobs.append(("form", "N", "O", c["cid"], form_user(norm(c["arms"]["O"]))))
        if c["cid"] not in ident or c["cid"] in spot:
            jobs.append(("form", "N", "S", c["cid"], form_user(norm(c["arms"]["S"]))))
    for c in prep["diss_cases"]:
        jobs.append(("diss", "N", "O", c["cid"], diss_user(c)))
    done = {(r["kind"], r["arm"], r["cid"]) for r in H.load_jsonl(RESULTS)} if RESULTS.exists() else set()
    if H._du_up():
        raise SystemExit("Du is UP or unknown; refusing to run")
    before = F.canary()
    n, t0 = 0, time.time()
    with F._isolated(cl) as lab_dir:
        assert str(cl._LEDGER).lower().startswith(str(lab_dir).lower())
        for kind, prompt, arm, cid, user in jobs:
            if (kind, arm, cid) in done:
                continue
            if n and n % 20 == 0 and H._du_up():
                raise SystemExit("Du came UP; stopping")
            res = None
            for wait in (0, 15, 45):
                if wait:
                    time.sleep(wait)
                try:
                    res = chat(psys, user, mc)
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


def _cell(v) -> str:
    if v is None:
        return "?"
    if v["form"]:
        return "Y"
    if not v["new"]:
        return "-"
    return "lb-" if v["on"] else "off"


def cmd_score(args) -> None:
    cl, mc = H._modules()
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    fc = {c["cid"]: c for c in prep["form_cases"]}
    dc = {c["cid"]: c for c in prep["diss_cases"]}
    ident = set(prep["norm_identical"])
    fa = collections.defaultdict(dict)                       # (a) production rows from J-2630
    for r in H.load_jsonl(SRC_2630 / "results.jsonl"):
        v = F.verdict(cl, fc[r["cid"]], r.get("parsed"))
        if v is not None:
            fa[r["cid"]][r["arm"]] = v
    da = {}
    for r in H.load_jsonl(SRC_2597 / "results.jsonl"):
        if r["arm"] == "O" and r["cid"] in dc and r.get("parsed") is not None:
            da[r["cid"]] = H.verdict(cl, dc[r["cid"]], r["parsed"])
    fn, spotS, dn, bad = collections.defaultdict(dict), {}, {}, 0
    for r in H.load_jsonl(RESULTS):
        if r["kind"] == "form":
            v = F.verdict(cl, fc[r["cid"]], r.get("parsed"))
            if v is None:
                bad += 1
                continue
            if r["arm"] == "S" and r["cid"] in ident:
                spotS[r["cid"]] = v
            else:
                fn[r["cid"]][r["arm"]] = v
        else:
            if r.get("parsed") is None:
                bad += 1
                continue
            dn[r["cid"]] = H.verdict(cl, dc[r["cid"]], r["parsed"])
    for cid in ident:                                         # identical text -> identical call by construction
        if "O" in fn.get(cid, {}):
            fn[cid]["S"] = fn[cid]["O"]
    print("unparsed/failed rows:", bad)

    print("\n=== DETERMINISM spot check: N_S re-run on text-identical cases vs N_O ===")
    sp = [(c, fn[c]["O"], spotS[c]) for c in spotS if "O" in fn.get(c, {})]
    print(f"  would_form identical {sum(a['form'] == b['form'] for _, a, b in sp)}/{len(sp)}; "
          f"statement identical {sum(a['stmt'] == b['stmt'] for _, a, b in sp)}/{len(sp)}")
    print(f"  N_O text == N_S text (by construction identical calls): {len(ident)}/{len(fc)}")

    print("\n=== FORMATION: production (a) arms O,S vs NORMALISED (N) arms O,S ===")
    groups = [(s, [s]) for s in ("OBS_want", "FORM_want", "OBS_must", "FORM_must")] + \
             [("ALL_want", ["OBS_want", "FORM_want"]), ("ALL_must", ["OBS_must", "FORM_must"]), ("ALL_FORM", ["FORM_want", "FORM_must"])]
    for name, strata in groups:
        ids = [i for i, c in fc.items() if c["stratum"] in strata and all(a in fa.get(i, {}) for a in "OS") and all(a in fn.get(i, {}) for a in "OS")]
        n = len(ids)
        if not n:
            continue
        w = {("a", "O"): sum(fa[i]["O"]["form"] for i in ids), ("a", "S"): sum(fa[i]["S"]["form"] for i in ids),
             ("N", "O"): sum(fn[i]["O"]["form"] for i in ids), ("N", "S"): sum(fn[i]["S"]["form"] for i in ids)}
        print(f"  {name} n={n}: aO wf {w[('a','O')]}/{n}; aS wf {w[('a','S')]}/{n}; NO wf {w[('N','O')]}/{n}; NS wf {w[('N','S')]}/{n}")
        for tag, R in (("a", fa), ("N", fn)):
            lost = sum(1 for i in ids if R[i]["O"]["form"] and not R[i]["S"]["form"])
            gained = sum(1 for i in ids if not R[i]["O"]["form"] and R[i]["S"]["form"])
            print(f"    ({tag}) O->S lost/gained {lost}/{gained} net {gained - lost:+d} (McNemar p={H.mcnemar_exact(lost, gained):.3f})")
        for arm in "OS":
            lost = sum(1 for i in ids if fa[i][arm]["form"] and not fn[i][arm]["form"])
            gained = sum(1 for i in ids if not fa[i][arm]["form"] and fn[i][arm]["form"])
            print(f"    arm {arm} a->N lost/gained {lost}/{gained} net {gained - lost:+d} (McNemar p={H.mcnemar_exact(lost, gained):.3f})")
        on = lambda R, arm: sum(R[i][arm]["on"] for i in ids)
        lbc = lambda R, arm: sum(1 for i in ids if R[i][arm]["on"] and R[i][arm]["lb"])
        print(f"    detection a-O on {on(fa,'O')}, lb|on {lbc(fa,'O')}; N-O on {on(fn,'O')}, lb|on {lbc(fn,'O')}; a-S on {on(fa,'S')}, lb|on {lbc(fa,'S')}")

    keep = [i for i, c in fc.items() if c["stratum"].startswith("FORM") and fa.get(i, {}).get("O", {}).get("form")]
    drop = [i for i in keep if "O" in fn.get(i, {}) and not fn[i]["O"]["form"]]
    gain = [i for i, c in fc.items() if c["stratum"].startswith("FORM") and fa.get(i, {}).get("O") and not fa[i]["O"]["form"] and fn.get(i, {}).get("O", {}).get("form")]
    print(f"\n  P2 FORM stands kept by production arm O: {len(keep)}; dropped under N: {len(drop)}; gained under N: {len(gain)}")
    for i in drop:
        print("    dropped:", fc[i]["stratum"], _cell(fn[i]["O"]), "|", fc[i]["statement"][:90])

    print("\n=== DISSOLVE no-harm (J-2597 arm O, 30-case subset): production (a) vs normalised (N) ===")
    for s in ("A_want", "A_must", "B_want", None):
        ids = [i for i, c in dc.items() if (s is None or c["stratum"] == s) and i in da and i in dn]
        ka = collections.Counter(da[i]["kind"] for i in ids if da[i]["diss"])
        kn = collections.Counter(dn[i]["kind"] for i in ids if dn[i]["diss"])
        lost = sum(1 for i in ids if da[i]["diss"] and not dn[i]["diss"])
        gained = sum(1 for i in ids if not da[i]["diss"] and dn[i]["diss"])
        kflip = sum(1 for i in ids if da[i]["diss"] and dn[i]["diss"] and da[i]["kind"] != dn[i]["kind"])
        changed = sum(1 for i in ids if da[i]["diss"] != dn[i]["diss"] or (da[i]["diss"] and da[i]["kind"] != dn[i]["kind"]))
        print(f"  {s or 'ALL'} n={len(ids)}: a dissolves {sum(da[i]['diss'] for i in ids)} {dict(ka)}; "
              f"N dissolves {sum(dn[i]['diss'] for i in ids)} {dict(kn)}; a->N lost/gained {lost}/{gained} "
              f"(p={H.mcnemar_exact(lost, gained):.3f}); kind flips among both {kflip}; verdicts changed (diss or kind) {changed}")

    out = {"form": {i: {"stratum": fc[i]["stratum"], "statement": fc[i]["statement"], "hist_lb": fc[i]["hist_lb"],
                        "a": fa.get(i), "N": fn.get(i)} for i in fc},
           "diss": {i: {"stratum": dc[i]["stratum"], "a": da.get(i), "N": dn.get(i)} for i in dc}}
    (SCRATCH / "per_case.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    rows = ["| # | stratum | statement (historical) | aO | aS | NO | NS |", "|---|---|---|---|---|---|---|"]
    for k, i in enumerate(sorted(fc, key=lambda x: (fc[x]["stratum"] != "FORM_must", fc[x]["stratum"], x)), 1):
        rows.append(f"| {k} | {fc[i]['stratum']} | {fc[i]['statement'][:80].replace('|', '/')} | " +
                    " | ".join(_cell(R.get(i, {}).get(arm)) for R, arm in ((fa, "O"), (fa, "S"), (fn, "O"), (fn, "S"))) + " |")
    (SCRATCH / "percase_form.md").write_text("\n".join(rows), encoding="utf-8")
    drows = ["| # | stratum | a (diss/kind) | N (diss/kind) |", "|---|---|---|---|"]
    for k, i in enumerate(sorted(dc, key=lambda x: (dc[x]["stratum"], x)), 1):
        f = lambda v: "?" if v is None else (f"dissolve/{v['kind']}" if v["diss"] else "keep")
        drows.append(f"| {k} | {dc[i]['stratum']} | {f(da.get(i))} | {f(dn.get(i))} |")
    (SCRATCH / "percase_diss.md").write_text("\n".join(drows), encoding="utf-8")
    print("\nwrites under live:", len(H.WRITE_ATTEMPTS))


def main() -> None:
    H.install_audit_hook()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("prep", cmd_prep), ("run", cmd_run), ("score", cmd_score)):
        sp.add_parser(name).set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
