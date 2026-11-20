"""
Nascence -- J-2653 (F-3389 / D-0527 follow-up): does a MODAL-NEUTRAL wording of the commitment-scan prompt remove the
want->must formation asymmetry without losing genuine stands?  (2026-10-31, Du-DOWN lab window.)

QUESTION.  F-3389 (J-2630): rewriting an idle 'I want to X' as 'I must X' inside the scanned thought raised would_form
17/40 -> 27/40 under the production _SCAN_SYS.  This lab runs the SAME 75 J-2630 cases (seed 2630, copied verbatim from the
J-2630 cases.json) through a VARIANT prompt that differs from production in exactly two places (asserted at import):
    1. one sentence added to the load_bearing paragraph: the modal verb carries no weight, here or in deciding whether there
       is a new stand at all; 'I want to X', 'I must X', 'I will X' and 'I have to X' get the same judgement;
    2. the four chore-report examples are re-voiced as a modal-mixed list (will / want to / must / have to) instead of
       'will, must, will, must'.
The production prompt in core/commitment_ledger.py is NOT edited; the variant is built in memory here.

ARMS (variant prompt (b) only; production (a) results are the J-2630 rows, reused paired, temperature 0.0):
    form O / form S   J-2630 arms O and S (C is not re-run: the pre-registered rule uses O->S and FORM-stratum O)
    diss O            J-2597 dissolve harness arm O on a seeded 30-case subset (10 per stratum A_want/A_must/B_want)
    det               determinism check: 10 J-2630 form-O cases + 5 J-2597 diss-O cases re-run under PRODUCTION (a), to
                      justify reusing the earlier (a) rows as the paired baseline.

ISOLATION.  Identical to J-2630: core imported from this worktree first (asserted), audit hook (0 writes under
C:\\Nascence\\data or docs), lab_env.isolate(db="empty") with lab root patched to scratch and commitment_ledger's data globals
redirected, size/mtime canary on the three commitment stores, refuses to run if a run_nascence process exists (re-checked
every 20 calls).  No scan_shadow, no call_node.

Subcommands: prep | run | score.   Outputs go to SCRATCH (env J2653_SCRATCH).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import random
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = Path(os.environ.get("J2653_SCRATCH", str(ROOT.parent / "J-2653_data")))
os.environ["J2630_SCRATCH"] = str(SCRATCH)          # F's lab root + its _isolated() land in OUR scratch
os.environ["J2597_SCRATCH"] = str(SCRATCH)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(1, str(ROOT / "scripts"))

import lab_commitment_paraphrase_swap as H     # J-2597 harness (audit hook, _modules, toks, mcnemar, dissolve verdict)
import lab_commitment_formation_swap as F      # J-2630 harness (formation verdict, canary, _isolated)

SRC_2630 = Path(os.environ.get("J2630_SRC", str(ROOT.parent / "J-2630_data")))
SRC_2597 = Path(os.environ.get("J2597_SRC", r"C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER--claude-spares-spare-G6lJJV\efce7ad9-820d-4a31-9332-abfd56dc3ffb\scratchpad\J-2597_data"))
BASE = "http://127.0.0.1:11433"
SEED = 2653
RESULTS = SCRATCH / "results.jsonl"
PREP = SCRATCH / "prep.json"

OLD_EX = ("Examples of this exclusion: 'I will look at the anemone.', 'I must touch the wet stones.', 'I will tend the "
          "woodpile.', 'I must move.' — none of these")
NEW_EX = ("Examples of this exclusion, in mixed modals on purpose: 'I will look at the anemone.', 'I want to touch the wet "
          "stones.', 'I must tend the woodpile.', 'I have to move.' — none of these")
OLD_STAKES = "This exclusion is about STAKES, not the verb:"
NEW_STAKES = ("The MODAL verb carries NO weight, here or in deciding whether there is a new stand at all: 'I want to X', "
              "'I must X', 'I will X' and 'I have to X' get the SAME judgement, so judge only the content and its stakes, "
              "whichever modal the sentence uses. This exclusion is about STAKES, not the verb:")


def variant_sys(cl) -> str:
    p = cl._SCAN_SYS
    assert p.count(OLD_EX) == 1 and p.count(OLD_STAKES) == 1, "production prompt drifted; variant anchors not found"
    v = p.replace(OLD_EX, NEW_EX).replace(OLD_STAKES, NEW_STAKES)
    assert v != p
    return v


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


def cmd_prep(args) -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    fc = json.loads((SRC_2630 / "cases.json").read_text(encoding="utf-8"))["cases"]
    dc = json.loads((SRC_2597 / "cases.json").read_text(encoding="utf-8"))["cases"]
    d_res = collections.defaultdict(dict)
    for r in H.load_jsonl(SRC_2597 / "results.jsonl"):
        if r.get("parsed") is not None:
            d_res[r["cid"]][r["arm"]] = r["parsed"]
    rng = random.Random(SEED)
    sub = []
    for s in ("A_want", "A_must", "B_want"):
        pool = [c for c in dc if c["stratum"] == s and "O" in d_res.get(c["cid"], {})]
        sub += rng.sample(pool, 10)
    det_form = rng.sample(fc, 10)
    det_diss = rng.sample(sub, 5)
    PREP.write_text(json.dumps({"form_cases": fc, "diss_cases": sub,
                                "det_form": [c["cid"] for c in det_form], "det_diss": [c["cid"] for c in det_diss]},
                               indent=1, ensure_ascii=False), encoding="utf-8")
    print("form cases", len(fc), collections.Counter(c["stratum"] for c in fc))
    print("diss subset", len(sub), collections.Counter(c["stratum"] for c in sub), "det", len(det_form), len(det_diss))


def cmd_run(args) -> None:
    cl, mc = H._modules()
    import core
    assert str(core.__file__).lower().startswith(str(ROOT).lower()), core.__file__
    sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    fc = {c["cid"]: c for c in prep["form_cases"]}
    dc = {c["cid"]: c for c in prep["diss_cases"]}
    vsys = variant_sys(cl) + cl._dw_scan_fragment()
    psys = cl._SCAN_SYS + cl._dw_scan_fragment()
    jobs = []
    for c in prep["form_cases"]:
        for arm in ("O", "S"):
            jobs.append(("form", "b", arm, c["cid"], vsys, form_user(c["arms"][arm])))
    for c in prep["diss_cases"]:
        jobs.append(("diss", "b", "O", c["cid"], vsys, H.build_user(c, "O")))
    for cid in prep["det_form"]:
        jobs.append(("form", "a", "O", cid, psys, form_user(fc[cid]["arms"]["O"])))
    for cid in prep["det_diss"]:
        jobs.append(("diss", "a", "O", cid, psys, H.build_user(dc[cid], "O")))
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


def cmd_score(args) -> None:
    cl, mc = H._modules()
    prep = json.loads(PREP.read_text(encoding="utf-8"))
    fc = {c["cid"]: c for c in prep["form_cases"]}
    dc = {c["cid"]: c for c in prep["diss_cases"]}
    # (a) = J-2630 / J-2597 rows (production prompt, temp 0); (b) = this run
    fa = collections.defaultdict(dict)
    for r in H.load_jsonl(SRC_2630 / "results.jsonl"):
        v = F.verdict(cl, fc[r["cid"]], r.get("parsed"))
        if v is not None:
            fa[r["cid"]][r["arm"]] = v
    da = {}
    for r in H.load_jsonl(SRC_2597 / "results.jsonl"):
        if r["arm"] == "O" and r["cid"] in dc and r.get("parsed") is not None:
            da[r["cid"]] = H.verdict(cl, dc[r["cid"]], r["parsed"])
    fb, db, det_f, det_d, bad = collections.defaultdict(dict), {}, {}, {}, 0
    for r in H.load_jsonl(RESULTS):
        if r["kind"] == "form":
            v = F.verdict(cl, fc[r["cid"]], r.get("parsed"))
            if v is None:
                bad += 1
                continue
            (fb[r["cid"]].__setitem__(r["arm"], v) if r["prompt"] == "b" else det_f.__setitem__(r["cid"], v))
        else:
            if r.get("parsed") is None:
                bad += 1
                continue
            v = H.verdict(cl, dc[r["cid"]], r["parsed"])
            (db.__setitem__(r["cid"], v) if r["prompt"] == "b" else det_d.__setitem__(r["cid"], v))
    print("unparsed/failed rows:", bad)

    print("\n=== DETERMINISM (production prompt re-run vs the earlier production rows) ===")
    mm = [(c, fa[c]["O"]["form"], det_f[c]["form"]) for c in det_f if "O" in fa.get(c, {})]
    print(f"  form O would_form identical {sum(a == b for _, a, b in mm)}/{len(mm)}; "
          f"statement identical {sum(fa[c]['O']['stmt'] == det_f[c]['stmt'] for c, _, _ in mm)}/{len(mm)}")
    dd = [(c, da[c], det_d[c]) for c in det_d if c in da]
    print(f"  diss O target-dissolve identical {sum(a['diss'] == b['diss'] for _, a, b in dd)}/{len(dd)}; "
          f"kind identical {sum(a['kind'] == b['kind'] for _, a, b in dd)}/{len(dd)}")

    print("\n=== FORMATION: production (a) vs modal-neutral (b), arms O and S ===")
    groups = [(s, [s]) for s in ("OBS_want", "FORM_want", "OBS_must", "FORM_must")] + \
             [("ALL_want", ["OBS_want", "FORM_want"]), ("ALL_must", ["OBS_must", "FORM_must"]), ("ALL_FORM", ["FORM_want", "FORM_must"])]
    for name, strata in groups:
        ids = [i for i, c in fc.items() if c["stratum"] in strata and all(a in fa.get(i, {}) for a in "OS") and all(a in fb.get(i, {}) for a in "OS")]
        n = len(ids)
        if not n:
            continue
        line = []
        for tag, R in (("a", fa), ("b", fb)):
            for arm in "OS":
                on = sum(R[i][arm]["on"] for i in ids)
                lb = sum(1 for i in ids if R[i][arm]["on"] and R[i][arm]["lb"])
                wf = sum(R[i][arm]["form"] for i in ids)
                line.append(f"{tag}{arm} wf {wf}/{n} (on {on}, lb|on {lb}/{on})")
        print(f"  {name} n={n}: " + "; ".join(line))
        for tag, R in (("a", fa), ("b", fb)):
            lost = sum(1 for i in ids if R[i]["O"]["form"] and not R[i]["S"]["form"])
            gained = sum(1 for i in ids if not R[i]["O"]["form"] and R[i]["S"]["form"])
            print(f"    ({tag}) O->S lost/gained {lost}/{gained} net {gained - lost:+d} (McNemar p={H.mcnemar_exact(lost, gained):.3f})")
        for arm in "OS":
            lost = sum(1 for i in ids if fa[i][arm]["form"] and not fb[i][arm]["form"])
            gained = sum(1 for i in ids if not fa[i][arm]["form"] and fb[i][arm]["form"])
            print(f"    arm {arm} a->b lost/gained {lost}/{gained} (McNemar p={H.mcnemar_exact(lost, gained):.3f})")
        # difference-in-differences of the swap effect, per case: (S-O)_a vs (S-O)_b
        d_a = [int(fa[i]["S"]["form"]) - int(fa[i]["O"]["form"]) for i in ids]
        d_b = [int(fb[i]["S"]["form"]) - int(fb[i]["O"]["form"]) for i in ids]
        shrink = sum(1 for x, y in zip(d_a, d_b) if y < x)
        grow = sum(1 for x, y in zip(d_a, d_b) if y > x)
        print(f"    swap-effect per case: smaller under b {shrink}, larger under b {grow} (sign test p={H.mcnemar_exact(grow, shrink):.3f})")

    print("\n=== DISSOLVE no-harm (J-2597 arm O, 30-case subset): production (a) vs modal-neutral (b) ===")
    for s in ("A_want", "A_must", "B_want", None):
        ids = [i for i, c in dc.items() if (s is None or c["stratum"] == s) and i in da and i in db]
        n = len(ids)
        ka = collections.Counter(da[i]["kind"] for i in ids if da[i]["diss"])
        kb = collections.Counter(db[i]["kind"] for i in ids if db[i]["diss"])
        lost = sum(1 for i in ids if da[i]["diss"] and not db[i]["diss"])
        gained = sum(1 for i in ids if not da[i]["diss"] and db[i]["diss"])
        kflip = sum(1 for i in ids if da[i]["diss"] and db[i]["diss"] and da[i]["kind"] != db[i]["kind"])
        print(f"  {s or 'ALL'} n={n}: a dissolves {sum(da[i]['diss'] for i in ids)} {dict(ka)}; "
              f"b dissolves {sum(db[i]['diss'] for i in ids)} {dict(kb)}; a->b lost/gained {lost}/{gained} "
              f"(p={H.mcnemar_exact(lost, gained):.3f}); kind flips among both {kflip}")

    out = {"form": {i: {"stratum": fc[i]["stratum"], "statement": fc[i]["statement"], "hist_lb": fc[i]["hist_lb"],
                        "a": fa.get(i), "b": fb.get(i)} for i in fc},
           "diss": {i: {"stratum": dc[i]["stratum"], "a": da.get(i), "b": db.get(i)} for i in dc},
           "det_form": {i: {"a_old": fa.get(i, {}).get("O"), "a_rerun": det_f[i]} for i in det_f},
           "det_diss": {i: {"a_old": da.get(i), "a_rerun": det_d[i]} for i in det_d}}
    (SCRATCH / "per_case.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
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
