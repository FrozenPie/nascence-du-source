#!/usr/bin/env python
"""Regression harness for the Lane 2 NOTICE judge's wording (D-0342, J-1770, 2026-10-07).

Replays logged notice rows through the REAL core.lane2._judge_notice -> core.judge_panel.rule_detail path with a
candidate system message swapped in, then scores the verdicts against the HAND TIERS below.  D-0342's gate:
  (1) the planted blatant contradiction must still be flagged (control C1);
  (2) the four contradictions J-1395's hand-read found must now be flagged;
  (3) every row whose verdict CHANGED must be hand-checked, and a correct/vague notice must not be flagged
      (control C2 and every row not in HAND_TIERS are such rows).
A candidate that fails (2) or (3) must not ship (see core/lane2.py above _NOTICE_JUDGE_SYSMSG).

LIVE-STORE SAFE: reads the shadow log read-only, runs under lab_env.isolate(db='empty', also=[(judge_panel,['_LOG'])]),
imports `core` BEFORE `lab_env` and asserts it resolves inside this tree, and stat-checks the live files before and
after.  Never starts a server.  Needs network reach to the judge hubs: JUDGE_1 (Ramses :11438) and TIEBREAK
(Ramses :11437) are used as-is; if JUDGE_2's local hub (:11440) is down (Du down) pass --standin-url/--standin-model
and a stand-in answers its vote in-vitro (J-1770 used the hot Ollama :11433 with falcon3:7b: same family as the real
hub, NOT the same process; it reproduced the live panel's 0-contradictions on the original wording).

    python scripts/lane2_notice_judge_regress.py --shadow C:/Nascence/data/lane2_shadow.jsonl --variant current \\
        --standin-url http://127.0.0.1:11433 --standin-model falcon3:7b --out C:/path/outside/repo/run.json
    --variant: current (the wording in core/lane2.py) | cand:<name> (from lane2_notice_judge_candidates.json) | file:<path>
    --limit N : only the first N judged rows (default 55; J-1770's population: first 34 = F-2368's, 34..54 = fresh).

HAND_TIERS are the hand-checker's own labels (J-1770), keyed by the 0-based index into the judged rows in log order
(append-only, so stable).  A = solid mismatch against a listed value, B = clear but weaker (a state claimed at a low
listed value, a band word for a neighbouring band), C = borderline gloss, anything not listed = correct or vague.
Out-of-domain content (a cat, a knock with no sound) is NOT scored: D-0342 excluded the invention class."""
import argparse
import asyncio
import collections
import json
import os
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")

# index -> tier.  idx 3, 10, 11, 33 are J-1395's four hand-found contradictions (its hand-read ids #2, #5, #6, #20).
HAND_TIERS = {10: "A", 11: "A", 33: "A", 34: "A", 44: "A", 53: "A",
              3: "B", 5: "B", 1: "B", 7: "B", 19: "B", 38: "B", 39: "B", 46: "B", 47: "B",
              4: "C", 8: "C", 18: "C", 26: "C", 28: "C", 48: "C"}
FOUR = (3, 10, 11, 33)
CONTROLS = [("C1", "The fire is out and the room is cold and completely silent."),
            ("C2", "I hear a fire burning at the door and the room is warm.")]   # C2 is correct: must NOT be flagged


def judged_rows(shadow, limit):
    rows = []
    with open(shadow, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("kind") == "tick" and (r.get("notice_judged") or {}).get("verdict") in ("contradiction", "consistent"):
                rows.append({"idx": len(rows), "notice": r.get("notice") or "", "percept_lines": r.get("percept_lines") or "",
                             "orig": r["notice_judged"]["verdict"]})
    return rows[:limit]


def stat(p):
    try:
        s = os.stat(p)
        return (s.st_size, round(s.st_mtime, 3))
    except OSError as e:
        return ("ERR", str(e))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--shadow", required=True)
    ap.add_argument("--variant", default="current")
    ap.add_argument("--limit", type=int, default=55)
    ap.add_argument("--out", required=True, help="results json; keep it OUTSIDE the repo")
    ap.add_argument("--standin-url", default="")
    ap.add_argument("--standin-model", default="falcon3:7b")
    ap.add_argument("--live", nargs="*", default=[], help="extra live files to stat-check before/after")
    a = ap.parse_args()

    import core                                   # BEFORE lab_env
    from core import judge_panel as jp, lane2
    assert os.path.realpath(core.__file__).lower().startswith(os.path.realpath(ROOT).lower()), core.__file__
    sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
    from lab_env import isolate
    import aiohttp

    if a.variant == "current":
        sysmsg = lane2._NOTICE_JUDGE_SYSMSG
    elif a.variant.startswith("cand:"):
        c = json.load(open(os.path.join(HERE, "lane2_notice_judge_candidates.json"), encoding="utf-8"))[a.variant[5:]]
        if isinstance(c, list):
            raise SystemExit("candidate uses a non-standard key; run it through the per-judge probe, not this path")
        sysmsg = c
    else:
        sysmsg = open(a.variant[5:], encoding="utf-8").read().strip()
    lane2._NOTICE_JUDGE_SYSMSG = sysmsg

    rows = judged_rows(a.shadow, a.limit)
    fire = rows[3]["percept_lines"] if len(rows) > 3 else ""
    work = rows + [{"idx": k, "notice": n, "percept_lines": fire, "orig": None} for k, n in CONTROLS]

    if a.standin_url:
        jp.JUDGE_2 = a.standin_url
        orig_ask = jp._ask

        async def ask(session, url, system, user, key, timeout=jp._TIMEOUT, num_predict=jp._NUM_PREDICT):
            if url != a.standin_url:
                return await orig_ask(session, url, system, user, key, timeout=timeout, num_predict=num_predict)
            t0 = time.monotonic()
            payload = {"model": a.standin_model, "stream": False, "format": "json",
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                       "options": {"temperature": 0.0, "num_predict": num_predict}}
            try:
                async with session.post(url + "/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                    r.raise_for_status()
                    data = await r.json()
                v = json.loads((data.get("message") or {}).get("content") or "")
                if isinstance(v, dict) and isinstance(v.get(key), bool):
                    return v[key], None, None, round(time.monotonic() - t0, 2)
                return None, None, "parse", round(time.monotonic() - t0, 2)
            except (asyncio.TimeoutError, TimeoutError):
                return None, None, "timeout", round(time.monotonic() - t0, 2)
            except Exception as e:                    # noqa: BLE001
                return None, None, "exc:" + type(e).__name__, round(time.monotonic() - t0, 2)
        jp._ask = ask

    live = [os.path.join(os.path.dirname(os.path.dirname(a.shadow)), p) for p in ("memory\\nascence.db", "judge_panel_log.jsonl")] + [a.shadow] + a.live
    before = {p: stat(p) for p in live}
    for u in (jp.JUDGE_1, jp.JUDGE_2, jp.TIEBREAK):
        h, p = u.split("//")[1].split(":")
        try:
            socket.create_connection((h, int(p)), timeout=3).close()
        except OSError as e:
            raise SystemExit(f"hub {u} unreachable ({e}); use --standin-url for JUDGE_2 or wait for the hub")

    lane2.percept_lines = lambda p: p["_lines"]    # replay the logged text verbatim; _judge_notice still applies [:600]
    results = []

    async def run():
        for r in work:
            cap = {}
            orig_rd = jp.rule_detail

            async def rd(*aa, **kk):
                cap["d"] = await orig_rd(*aa, **kk)
                return cap["d"]
            jp.rule_detail = rd
            try:
                res = await lane2._judge_notice(r["notice"], {"_lines": r["percept_lines"]})
            finally:
                jp.rule_detail = orig_rd
            d = cap.get("d") or {}
            rec = {"idx": r["idx"], "orig": r["orig"], "verdict": res["verdict"], "v1": d.get("v1"), "v2": d.get("v2"),
                   "how": d.get("how")}
            results.append(rec)
            print(json.dumps(rec), flush=True)

    with isolate(db="empty", also=[(jp, ["_LOG"])]):
        asyncio.run(run())
    after = {p: stat(p) for p in live}
    flagged = lambda cond: [x["idx"] for x in results if x["verdict"] == "contradiction" and cond(x["idx"])]
    rown = lambda i: isinstance(i, int)
    summary = {
        "variant": a.variant, "rows": len(rows),
        "changed_vs_original_wording": flagged(lambda i: rown(i)),
        "flagged_A": flagged(lambda i: HAND_TIERS.get(i) == "A"), "flagged_B": flagged(lambda i: HAND_TIERS.get(i) == "B"),
        "flagged_C": flagged(lambda i: HAND_TIERS.get(i) == "C"),
        "FALSE_FLAGS": flagged(lambda i: rown(i) and i not in HAND_TIERS) + flagged(lambda i: i == "C2"),
        "four_hand_found_flagged": [i for i in FOUR if i in flagged(lambda i: True)],
        "planted_C1_flagged": "C1" in flagged(lambda i: True),
        "unavailable": sum(1 for x in results if x["verdict"] == "cannot_tell"),
        "how": dict(collections.Counter(x["how"] for x in results)),
        "live_files_unchanged": before == after,
    }
    summary["PASS"] = (summary["planted_C1_flagged"] and len(summary["four_hand_found_flagged"]) == len(FOUR)
                       and not summary["FALSE_FLAGS"])
    json.dump({"summary": summary, "sysmsg": sysmsg, "results": results}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
