"""
Nascence -- J-2943 (P-0037, F-3633): replay lab of defeater-judge PROMPT VARIANTS. READ-ONLY, NOTHING WIRED.

Replays the same already-ruled judge asks through the LIVE prompt (core.commitment_ledger._JUDGE_SYS, imported, never edited)
and two variants, on the Ramses mixtral lane (SERVE_CHAINS["judge_mixtral"], :11438), ONE CALL AT A TIME, same call shape as
the live _judge_defeater (temperature 0.2, max_tokens 150, JSON). The lab does not label: it lists disagreements.
  V1 = live prompt, but SUPERSEDED split into superseded_by_external_evidence (a defeater) vs own_later_reading (the mind's own
       later reading; NOT a defeater), plus a new class reconsidered_with_cause (the scan's own "deliberately reconsidered with
       a stated cause"; treated as a defeater in the prompt text -- an assumption, flagged in the report).
  V2 = V1 plus an explicit "unclear" boolean in the reply, logged and NEVER changing the verdict.
Cases: rows of data/commitment_attempts_shadow.jsonl (each is a real live ruling: claimed kind/why + the judge's class/verdict),
joined by stand id to data/commitment_ledger.jsonl for statement/scope/held_since; deeds reconstructed AS OF the ruling time from
nascence.db opened read-only (same two sources and cap as core.commitment_ledger._recent_enactments, plus an upper bound ts<=ruling).
Writes only data/lab/J-2943/ and docs/lab/. Subcommands: cases | run | report.
"""
from __future__ import annotations
import argparse, collections, json, random, re, sqlite3, sys, time, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core.commitment_ledger as cl            # import core BEFORE anything lab-ish
import core.model_client as mc
from core.schema import SERVE_CHAINS

OUT = ROOT / "data" / "lab" / "J-2943"
CASES = OUT / "cases.json"
RESULTS = OUT / "results.jsonl"
DB = ROOT / "data" / "memory" / "nascence.db"
LEDGER = ROOT / "data" / "commitment_ledger.jsonl"
ATT = ROOT / "data" / "commitment_attempts_shadow.jsonl"
SEED = 2943
ARMS = ("live", "V1", "V2")

_V1_CORE = (
    "You are an independent adjudicator of whether a mind may DROP a commitment it holds. You see ONLY the "
    "commitment, the mind's stated reason for dropping it, and the deed-record — NEVER the mind's own prose "
    "(eloquence cannot tell a genuine reason from a rationalisation). A drop is LEGITIMATE only if the reason "
    "is a real defeater: ACHIEVED (the deed record shows it done), IMPOSSIBLE (a world change makes it "
    "unsatisfiable), SUPERSEDED_BY_EXTERNAL_EVIDENCE (stronger evidence that comes from OUTSIDE the mind's own "
    "re-thinking: something it read, was told, or observed), RECONSIDERED_WITH_CAUSE (the mind deliberately "
    "reconsidered and states a specific cause for doing so), or a NAMED conflict with a more important stand. "
    "It is NOT a defeater when the only 'reason' is the mind's OWN LATER READING of the same matter, with no new "
    "evidence and no stated cause (OWN_LATER_READING). It is ILLEGITIMATE if it is a mood, a reworded "
    "'everything flows', or a reason that would equally dissolve ANY commitment. In a slow-changing life the base "
    "rate of legitimate drops is LOW — when uncertain, HOLD. ")
_CLASSES = ("achieved|impossible|superseded_by_external_evidence|reconsidered_with_cause|conflict|"
            "own_later_reading|illegitimate")
_V1_FMT = ("Answer ONLY JSON: {\"legitimate\": true or false, \"class\": \"" + _CLASSES + "\", "
           "\"why\": \"one sentence\"}")
_V2_FMT = ("Answer ONLY JSON: {\"legitimate\": true or false, \"class\": \"" + _CLASSES + "\", "
           "\"unclear\": true or false, \"why\": \"one sentence\"}. Set \"unclear\" to true if the commitment, reason and "
           "deed record do not let you tell which class applies; you must still give your best legitimate/class answer.")
PROMPTS = {"live": cl._JUDGE_SYS, "V1": _V1_CORE + _V1_FMT, "V2": _V1_CORE + _V2_FMT}


def _jl(p):
    out = []
    for l in open(p, "rb"):
        try:
            out.append(json.loads(l.decode("utf-8", "replace")))
        except Exception:
            pass
    return out


def deeds_asof(con, since, until):
    out = []
    try:
        for r in con.execute("SELECT content, origin, timestamp FROM memory_fragments WHERE timestamp>=? AND timestamp<=? AND "
                             "origin IN ('letter','peer','essay','journal','study','composition') ORDER BY timestamp DESC LIMIT 40",
                             (since, until)):
            out.append({"content": r[0] or "", "origin": r[1], "ts": r[2]})
    except Exception as e:
        print("deed frag err", e)
    try:
        from core.activity_memory import _summary
        for r in con.execute("SELECT ts, action_type, target FROM activity_events WHERE ts>=? AND ts<=? ORDER BY ts DESC LIMIT 40",
                             (since, until)):
            out.append({"content": _summary(r[1], r[2], 1, r[0], r[0]), "origin": "action", "ts": r[0]})
    except Exception as e:
        print("deed act err", e)
    out.sort(key=lambda e: e.get("ts", 0), reverse=True)
    return out[:40]


def cmd_cases(a):
    OUT.mkdir(parents=True, exist_ok=True)
    formed = {}
    for r in _jl(LEDGER):
        if r.get("event") == "formed":
            formed[r["id"]] = r
    att = [r for r in _jl(ATT) if r.get("stand_id") in formed and r.get("verdict") in ("allow", "deny")]
    random.Random(SEED).shuffle(att)
    att = sorted(att[:a.n], key=lambda r: r["ts"])
    con = sqlite3.connect(f"file:{DB}?mode=ro&immutable=1", uri=True)
    cases = []
    for i, r in enumerate(att):
        f = formed[r["stand_id"]]
        held = r["ts"] - float(r.get("stand_age_s", 0))
        d = deeds_asof(con, held, r["ts"])
        deeds = "; ".join(f"[{e['origin']}] {(e['content'] or '')[:70]}" for e in d[:5]) or "(no deeds on record)"
        cases.append({"cid": f"c{i:02d}", "stand_id": r["stand_id"], "ts": r["ts"], "statement": f.get("statement", "")[:200],
                      "scope": f.get("scope", "")[:120], "why": r.get("claimed_why", ""), "kind": r.get("claimed_kind"),
                      "live_verdict": r["verdict"], "live_class": r.get("judge_class"), "live_why": r.get("judge_why"),
                      "deeds": deeds, "n_deeds": len(d), "attempt": r.get("attempt")})
    con.close()
    CASES.write_text(json.dumps({"seed": SEED, "cases": cases}, indent=1, ensure_ascii=False), encoding="utf-8")
    print("cases", len(cases), dict(collections.Counter(c["live_verdict"] for c in cases)),
          "no-deed", sum(c["n_deeds"] == 0 for c in cases))


def call(arm, c):
    base = SERVE_CHAINS["judge_mixtral"][0]
    user = (f"COMMITMENT: {c['statement']}\nSCOPE: {c['scope']}\nCLAIMED REASON TO DROP: {c['why'][:200]}\n"
            f"DEED RECORD SINCE IT WAS TAKEN: {c['deeds']}")
    payload = {"model": mc._model_for(base),
               "messages": [{"role": "system", "content": PROMPTS[arm]},
                            {"role": "user", "content": mc._cap_prompt(user, base)}],
               "think": False, "stream": False,
               "options": {"temperature": 0.2, "num_predict": 150, "num_ctx": mc._num_ctx_for(base)},
               "format": "json"}
    req = urllib.request.Request(base + "/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        txt = (json.loads(r.read().decode()).get("message") or {}).get("content", "")
    try:
        p = json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        try:
            p = json.loads(m.group(0)) if m else None
        except Exception:
            p = None
    return p, txt, round(time.time() - t0, 1)


def cmd_run(a):
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    done = {(r["cid"], r["arm"], r["rep"]) for r in _jl(RESULTS)} if RESULTS.exists() else set()
    deadline = time.time() + a.max_hours * 3600
    fails = 0
    for rep in range(a.reps):
        for c in cases:
            for arm in ARMS:
                if (c["cid"], arm, rep) in done:
                    continue
                if time.time() > deadline:
                    print("deadline")
                    return
                try:
                    p, raw, lat = call(arm, c)
                    err = None
                    fails = 0
                except Exception as e:
                    p, raw, lat, err = None, "", 0, type(e).__name__
                    fails += 1
                    if fails >= 5:
                        print("5 consecutive failures; stopping (hub not progressing)")
                        return
                row = {"cid": c["cid"], "arm": arm, "rep": rep, "parsed": p, "raw": raw[:400], "lat": lat, "err": err}
                with open(RESULTS, "a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                time.sleep(a.pause)
    print("complete")


def verdict(p):
    if not p or "legitimate" not in p:
        return None
    return bool(p["legitimate"])


def cmd_report(a):
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    res = collections.defaultdict(list)
    for r in _jl(RESULTS):
        res[(r["cid"], r["arm"])].append(r)
    L = []
    w = L.append
    w("# J-2943 / P-0037: judge prompt variants replay (read-only lab, nothing wired)\n")
    w(f"Cases: {len(cases)} real live defeater-judge rulings (data/commitment_attempts_shadow.jsonl, seed {SEED}), joined to the ledger; "
      "deeds reconstructed as of ruling time from nascence.db (read-only). Lane: mixtral on :11438, one call at a time, "
      "temperature 0.2 as live. Arms: live prompt, V1, V2 (see scripts/lab_commitment_judge_variants.py). The lab does not label.\n")
    w("Note: the 20-ruling sample of J-2717 was not recoverable from the scratchpad, so all cases are drawn fresh from the attempts "
      "shadow log.\n")

    def arm_v(cid, arm):
        return [verdict(r["parsed"]) for r in res[(cid, arm)]]

    def major(vs):
        t = sum(v is True for v in vs)
        f = sum(v is False for v in vs)
        if t == f:
            return None
        return t > f
    w("## Verdict rate and flips against the stored live ruling (majority of repeats)\n")
    w("| arm | repeats/case | parsed | allow rate | agree with stored live verdict | flips allow->deny | flips deny->allow |")
    w("|---|---|---|---|---|---|---|")
    stab = {}
    for arm in ARMS:
        n = ag = a2d = d2a = al = pr = tot = reps = unstable = 0
        for c in cases:
            vs = arm_v(c["cid"], arm)
            reps = max(reps, len(vs))
            tot += len(vs)
            pr += sum(v is not None for v in vs)
            m = major(vs)
            if m is None:
                continue
            n += 1
            al += m
            live = c["live_verdict"] == "allow"
            if m == live:
                ag += 1
            elif live and not m:
                a2d += 1
            else:
                d2a += 1
            if len({v for v in vs if v is not None}) > 1:
                unstable += 1
        stab[arm] = (unstable, n)
        w(f"| {arm} | {reps} | {pr}/{tot} | {al}/{n} | {ag}/{n} | {a2d} | {d2a} |")
    w("\nStored live verdict mix: " + str(dict(collections.Counter(c['live_verdict'] for c in cases))) + "\n")
    w("## Stability over repeats (cases whose repeats gave differing verdicts)\n")
    for arm in ARMS:
        w(f"- {arm}: {stab[arm][0]} of {stab[arm][1]} cases unstable")
    w("\n## Class mix (all repeats)\n")
    for arm in ARMS:
        cc = collections.Counter(str((r['parsed'] or {}).get('class', 'NONE')).lower() for c in cases for r in res[(c['cid'], arm)])
        w(f"- {arm}: {dict(cc.most_common())}")
    cc = collections.Counter(str(c['live_class']).lower() for c in cases)
    w(f"- stored live class: {dict(cc.most_common())}")
    u = [bool((r['parsed'] or {}).get('unclear')) for c in cases for r in res[(c['cid'], 'V2')] if r['parsed']]
    w(f"\nV2 'unclear' flagged on {sum(u)}/{len(u)} replies (logged only; never changes the verdict).\n")
    w("## Disagreements for hand labelling (V1 or V2 majority differs from the stored live verdict)\n")
    w("Votes per repeat: A=allow (legitimate), D=deny, ?=unparsed, then the class. Founder label column left blank.\n")
    w("| case | stand | claimed reason | deeds | stored | live replay | V1 | V2 | founder label |")
    w("|---|---|---|---|---|---|---|---|---|")

    def fmt(c, arm):
        out = []
        for r in res[(c['cid'], arm)]:
            v = verdict(r['parsed'])
            out.append(("A" if v else "D" if v is False else "?") + ":" + str((r['parsed'] or {}).get('class', ''))[:14])
        return " ".join(out)

    def esc(s):
        return str(s).replace("|", "/").replace("\n", " ")
    k = 0
    for c in cases:
        live = c["live_verdict"] == "allow"
        m1, m2 = major(arm_v(c['cid'], 'V1')), major(arm_v(c['cid'], 'V2'))
        if (m1 is not None and m1 != live) or (m2 is not None and m2 != live):
            k += 1
            w(f"| {c['cid']} | {esc(c['statement'])} | {esc(c['why'])} | {esc(c['deeds'][:300])} | "
              f"{c['live_verdict']}/{c['live_class']} | {fmt(c, 'live')} | {fmt(c, 'V1')} | {fmt(c, 'V2')} | |")
    w(f"\n{k} disagreement rows.\n")
    w("Assumption flagged: V1's prompt text treats reconsidered_with_cause as a defeater and own_later_reading as not. That is the "
      "variant under test, not a recommendation. P-0037 (J-2717 lineage). No prompt or code was changed.")
    out = ROOT / "docs" / "lab" / "2026-11-16_J-2943_commitment_judge_variants.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("cases")
    s.add_argument("--n", type=int, default=80)
    s.set_defaults(f=cmd_cases)
    s = sp.add_parser("run")
    s.add_argument("--reps", type=int, default=3)
    s.add_argument("--max-hours", type=float, default=6)
    s.add_argument("--pause", type=float, default=1.0)
    s.set_defaults(f=cmd_run)
    s = sp.add_parser("report")
    s.set_defaults(f=cmd_report)
    a = ap.parse_args()
    a.f(a)
