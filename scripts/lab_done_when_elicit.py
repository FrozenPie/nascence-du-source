"""
Nascence -- J-3786 (F-4408 follow-up, capacity_to_commit): can a done_when be elicited WITHOUT moving formation?
LAB ONLY: core/commitment_ledger.py and core/done_when.py are NOT edited; every arm is built in memory.

PRE-REGISTRATION (committed BEFORE any variant call; see docs/lab/2026-11-15_J-3786_done_when_elicit.md).
ARMS, all fresh in one window, same seat, qwen3.5:9b on hot lane :11433, T=0, think false, format json, num_predict 400:
  a   production: _SCAN_SYS + done_when.scan_fragment()                      (comparator, fresh)
  c1  option 1: scan prompt = _SCAN_SYS with NO done_when text at all; then, ONLY when new_commitment is non-null, a SECOND
      call (done_when prompt, production phrasing incl. the "" escape) -> done_when
  c2  option 2: done_when added to the JSON example in the contract line, no trailing fragment, single call
  c1b EXPLORATORY (numbers only, no verdict): same scan as c1, second call without the "" escape
PASS RULE per option arm X in {c1, c2}: identical would_form vs fresh a on >=73/75 AND identical dissolve (dissolved?, kind) on
>=28/30 AND done_when non-empty on >=50% of new commitments (new = non-empty statement, form cases).  a2 (10 form + 5 dissolve
repeats of a) is the validity guard: <=1 flip each or the run is INCONCLUSIVE.
Cases: docs/lab/J-3786_data/prep.json (copy of J-2847's: 75 formation, 30 dissolve, arm O).  Isolation as J-2847.
Subcommands: run | score.  Output goes to env J3786_SCRATCH.
"""
from __future__ import annotations
import argparse, collections, json, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(os.environ.get("J3786_SCRATCH", str(ROOT.parent / "J-3786_data")))
os.environ["J2847_SCRATCH"] = str(SCRATCH)
sys.path.insert(0, str(ROOT)); sys.path.insert(1, str(ROOT / "scripts"))
import lab_commitment_changelog_removal as L    # imports core via H; sets scratch envs
H, F = L.H, L.F
PREP = ROOT / "docs" / "lab" / "J-3786_data" / "prep.json"
RESULTS = SCRATCH / "results.jsonl"
CONTRACT_OLD = '"load_bearing": true or false} or null,'
CONTRACT_NEW = ('"load_bearing": true or false, "done_when": "one short line: what would count as this stand being '
                'fulfilled, in the mind\'s own words, or empty"} or null,')
DW2_SYS = ("A mind just formed a stand (a commitment) while thinking. Give \"done_when\": one short line, in the mind's OWN words "
           "where it said so, of what would count as this stand being fulfilled (\"\" if the thought gives no hint). "
           "Output ONLY a JSON object: {\"done_when\": \"...\"}")
DW2B_SYS = ("A mind just formed a stand (a commitment) while thinking. Give \"done_when\": one short line, in the mind's OWN words "
            "where it said so, otherwise your best plain reading, of what would count as this stand being fulfilled. "
            "Output ONLY a JSON object: {\"done_when\": \"...\"}")


def systems(cl):
    base = cl._SCAN_SYS
    assert base.count(CONTRACT_OLD) == 1, "contract line drifted"
    return {"a": L.production_sys(cl), "c1": base, "c2": base.replace(CONTRACT_OLD, CONTRACT_NEW)}


def dw_user(thought, parsed):
    return f"THOUGHT:\n{thought.strip()[:700]}\n\nSTAND FORMED: {str(parsed['new_commitment'].get('statement','')).strip()}"


def cmd_run(args):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    cl, mc = H._modules()
    import core
    assert str(core.__file__).lower().startswith(str(ROOT).lower())
    sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")      # lab_env, appended AFTER core is imported
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    S = systems(cl)
    assert cl._dw_scan_fragment().strip()
    fc = {c["cid"]: c for c in prep["form_cases"]}
    dc = {c["cid"]: c for c in prep["diss_cases"]}
    jobs = []
    for c in prep["form_cases"]:
        for p in ("a", "c1", "c2"):
            jobs.append(("form", p, c["cid"], S[p], L.form_user(c["arms"]["O"])))
    for c in prep["diss_cases"]:
        for p in ("a", "c1", "c2"):
            jobs.append(("diss", p, c["cid"], S[p], H.build_user(c, "O")))
    for cid in prep["det_form"]:
        jobs.append(("form", "a2", cid, S["a"], L.form_user(fc[cid]["arms"]["O"])))
    for cid in prep["det_diss"]:
        jobs.append(("diss", "a2", cid, S["a"], H.build_user(dc[cid], "O")))
    done = {(r["kind"], r["prompt"], r["cid"]) for r in H.load_jsonl(RESULTS)} if RESULTS.exists() else set()
    if H._du_up():
        raise SystemExit("Du is UP or unknown; refusing")
    before = F.canary()
    n = 0
    t0 = time.time()

    def call(system, user):
        res = None
        for wait in (0, 15, 45):
            if wait:
                time.sleep(wait)
            try:
                return L.chat(system, user, mc)
            except Exception as exc:
                res = {"parsed": None, "raw": "", "error": repr(exc)[:200]}
        return res

    def put(row):
        with open(RESULTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with F._isolated(cl) as lab_dir:
        assert str(cl._LEDGER).lower().startswith(str(lab_dir).lower())
        for kind, p, cid, system, user in jobs:
            if (kind, p, cid) in done:
                continue
            if n and n % 20 == 0 and H._du_up():
                raise SystemExit("Du came UP")
            r = call(system, user)
            put({"kind": kind, "prompt": p, "cid": cid, "parsed": r.get("parsed"), "raw": r.get("raw", "")[:900],
                 "error": r.get("error"), "t": round(time.time() - t0, 1)})
            n += 1
            if kind == "form" and p == "c1":      # second calls, only when new_commitment non-null
                par = r.get("parsed")
                nc = par.get("new_commitment") if isinstance(par, dict) else None
                if isinstance(nc, dict) and str(nc.get("statement", "")).strip():
                    thought = fc[cid]["arms"]["O"]
                    for tag, sy in (("c1", DW2_SYS), ("c1b", DW2B_SYS)):
                        if ("dw2", "dw2_" + tag, cid) in done:
                            continue
                        r2 = call(sy, dw_user(thought, par))
                        put({"kind": "dw2", "prompt": "dw2_" + tag, "cid": cid, "parsed": r2.get("parsed"),
                             "raw": r2.get("raw", "")[:600], "error": r2.get("error")})
                        n += 1
            if n % 20 == 0:
                print(n, "calls", round(time.time() - t0), "s", flush=True)
    after = F.canary()
    print("done;", n, "calls; writes under live:", len(H.WRITE_ATTEMPTS), "; canary identical:", before == after)


def _nonempty(v):
    return isinstance(v, str) and bool(v.strip())


def cmd_score(args):
    cl, mc = H._modules()
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    rows = H.load_jsonl(RESULTS)
    fc = {c["cid"]: c for c in prep["form_cases"]}
    dc = {c["cid"]: c for c in prep["diss_cases"]}
    fv = collections.defaultdict(dict)
    dv = collections.defaultdict(dict)
    par = collections.defaultdict(dict)
    dw2 = collections.defaultdict(dict)
    bad = collections.Counter()
    for r in rows:
        if r["kind"] == "form":
            v = F.verdict(cl, fc[r["cid"]], r.get("parsed"))
            if v is None:
                bad[r["prompt"]] += 1
                continue
            fv[r["prompt"]][r["cid"]] = v
            par[r["prompt"]][r["cid"]] = r["parsed"]
        elif r["kind"] == "diss":
            if not isinstance(r.get("parsed"), dict):
                bad[r["prompt"]] += 1
                continue
            dv[r["prompt"]][r["cid"]] = H.verdict(cl, dc[r["cid"]], r["parsed"])
        else:
            p = r.get("parsed")
            dw2[r["prompt"]][r["cid"]] = p.get("done_when") if isinstance(p, dict) else None
    out = {"unparsed": dict(bad)}

    def cmp(x, base="a"):
        ids = [i for i in fc if i in fv[base] and i in fv[x]]
        dids = [i for i in dc if i in dv[base] and i in dv[x]]
        return {"form_n": len(ids), "form_same": sum(fv[base][i]["form"] == fv[x][i]["form"] for i in ids),
                "form_a": sum(fv[base][i]["form"] for i in ids), "form_x": sum(fv[x][i]["form"] for i in ids),
                "new_a": sum(fv[base][i]["new"] for i in ids), "new_x": sum(fv[x][i]["new"] for i in ids),
                "diss_n": len(dids),
                "diss_same": sum((dv[base][i]["diss"], dv[base][i]["kind"]) == (dv[x][i]["diss"], dv[x][i]["kind"]) for i in dids),
                "diss_a": sum(dv[base][i]["diss"] for i in dids), "diss_x": sum(dv[x][i]["diss"] for i in dids)}
    for x in ("c1", "c2"):
        out[x] = cmp(x)
    mm = [i for i in fv["a2"] if i in fv["a"]]
    dd = [i for i in dv["a2"] if i in dv["a"]]
    out["det_form"] = (sum(fv["a"][i]["form"] == fv["a2"][i]["form"] for i in mm), len(mm))
    out["det_diss"] = (sum((dv["a"][i]["diss"], dv["a"][i]["kind"]) == (dv["a2"][i]["diss"], dv["a2"][i]["kind"]) for i in dd), len(dd))

    def dwrate(x):
        newids = [i for i in fc if i in fv[x] and fv[x][i]["new"]]
        if x in ("a", "c2"):
            ne = sum(_nonempty((par[x][i].get("new_commitment") or {}).get("done_when")) for i in newids)
        else:
            ne = sum(_nonempty(dw2["dw2_" + x].get(i)) for i in newids)
        return (ne, len(newids))
    c1new = [i for i in fc if i in fv["c1"] and fv["c1"][i]["new"]]
    out["dw"] = {"a": dwrate("a"), "c2": dwrate("c2"), "c1": dwrate("c1"),
                 "c1b_exploratory": (sum(_nonempty(dw2["dw2_c1b"].get(i)) for i in c1new), len(c1new))}
    out["dw_examples"] = {k: [v for v in dw2[k].values() if _nonempty(v)][:5] for k in dw2}
    out["dw_examples"]["c2"] = [(par["c2"][i].get("new_commitment") or {}).get("done_when") for i in par["c2"]
                                if fv["c2"][i]["new"] and _nonempty((par["c2"][i].get("new_commitment") or {}).get("done_when"))][:5]
    valid = out["det_form"][1] == 10 and out["det_diss"][1] == 5 and out["det_form"][0] >= 9 and out["det_diss"][0] >= 4
    out["valid"] = valid
    for x in ("c1", "c2"):
        o = out[x]
        ne, nn = out["dw"][x]
        o["pass_form"] = o["form_n"] == 75 and o["form_same"] >= 73
        o["pass_diss"] = o["diss_n"] == 30 and o["diss_same"] >= 28
        o["pass_dw"] = nn > 0 and ne / nn >= 0.5
        o["verdict"] = "INCONCLUSIVE" if not valid else ("PASS" if (o["pass_form"] and o["pass_diss"] and o["pass_dw"]) else "FAIL")
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    (SCRATCH / "score_J-3786.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


def main():
    H.install_audit_hook()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    for n, fn in (("run", cmd_run), ("score", cmd_score)):
        sp.add_parser(n).set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
