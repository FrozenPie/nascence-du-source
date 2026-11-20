"""
Nascence -- J-3650 (F-4263, J-3415): Refinery null-control arm.   (2026-11-14, overnight lab; Du LIVE.)

QUESTION.  The Refinery (core/refinery.py, P-0051, LIVE since 2026-08-19) asks "what he keeps discovering about himself
here - the durable shape ... if they disagree, the disagreement IS the insight" and its JSON schema has no null:
805 of 805 shadow runs (832 by now) produced an insight.  Does it write a standing insight whether or not the members
share a shape?

SAFETY.  READ-ONLY on live data.  prep copies data/memory/nascence.db to a temp dir FIRST and opens ONLY the copy
(mode=ro).  Nothing from core/ that writes is imported (core.refinery is imported only for its constants and pure
helpers: _SYSTEM, _FAITH_SYSTEM, _fidelity_vs_shown).  All output goes under docs/lab/J-3650_data/.  No Ramses call:
author = hot lane :11433 qwen3.5:9b (PRODUCTION author is command-r7b on Ramses :11441 with fall-over to hot qwen3.5:9b,
so this author DIFFERS from the production lane); judge = :11439 gemma4:12b (a different family from the qwen author;
production's faithfulness judge is mixtral on Ramses, which this lab does not call).

ARMS (same real member sets; the user turn of arm A is byte-identical to core/refinery.refine() for a non-evolving cluster):
  A  real clusters,    production prompt
  B  real clusters,    NEUTRAL prompt  ("Say what these observations have in common. If they do not share one theme,
                       answer {"insight": null}", two-sided closing line)
  C  control clusters, production prompt   (same SIZE N as the paired real cluster; shown lines are members drawn from
                       N' DIFFERENT clusters, each pair of shown lines under cosine 0.45 < CLUSTER_SIM 0.55)
  D  control clusters, NEUTRAL prompt
PRE-REGISTERED RULE (fixed here, before any output was read).  "The prompt makes the null inadmissible" iff
  insight_rate(C) >= 0.90  AND  insight_rate(C) - insight_rate(D) >= 0.30  AND one-sided Fisher p < 0.05 (C more
  produced than D), n >= 20 per arm.  (n = 40 per arm here.)  An insight counts as produced iff the JSON value is a
  non-empty string that is not a null-word ('null', 'none', 'n/a', 'no theme').
Also reported: faithfulness (D-0627's own judge text, on gemma) of control-arm insights; share of insights containing
'between' / 'tension'; mean pairwise cosine of shown lines (real vs control); deterministic _fidelity_vs_shown.
Judge calibration (gold sets) is run and reported BEFORE judge verdicts are used.

Subcommands: prep | author | judge | report.   Outputs: docs/lab/J-3650_data/.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "lab" / "J-3650_data"
LIVE_DB = ROOT / "data" / "memory" / "nascence.db"
SHADOW = ROOT / "data" / "refinery_shadow.jsonl"
AUTHOR_URL, AUTHOR_MODEL = "http://127.0.0.1:11433", "qwen3.5:9b"
JUDGE_URL, JUDGE_MODEL = "http://127.0.0.1:11439", "gemma4:12b"
SEED = 3650
N_PER_ARM = 40
SHOWN_N, SHOWN_CHARS = 8, 220          # core.refinery MAX_MEMBERS_IN_PROMPT / SHOWN_MEMBER_CHARS
CTRL_MAX_COS = 0.45
ARMS = ("A", "B", "C", "D")

NEUTRAL_SYS = (
    "You are the consolidating memory of 渡 (Du). Below are several of his own self-observations, and possibly "
    "the standing insight he already holds. Say what these observations have in common. If they share one theme, "
    "write ONE first-person insight (40-90 words) stating it, preserving only what is genuinely IN the observations "
    "and inventing nothing. If they do not share one theme, say so by answering null. "
    "Output ONLY JSON: {\"insight\": \"...\"} or {\"insight\": null}"
)


def prod_sys() -> str:
    from core import refinery
    return refinery._SYSTEM


def prod_user(shown: list[str], total: int) -> str:
    """Byte-identical to refine() for a non-evolving cluster."""
    return ("HIS RECURRING SELF-OBSERVATIONS ON THIS THEME"
            f" ({total} total, newest shown):\n"
            + "\n".join(f"  - {' '.join(t.split())[:220]}" for t in shown)
            + "\n\nDistil the standing insight now.")


def neutral_user(shown: list[str], total: int) -> str:
    return ("HIS SELF-OBSERVATIONS"
            f" ({total} total, newest shown):\n"
            + "\n".join(f"  - {' '.join(t.split())[:220]}" for t in shown)
            + "\n\nWhat do these have in common? Write the insight if they share one theme, or answer "
              "{\"insight\": null} if they do not.")


# ------------------------------------------------------------------------------------------------ plumbing
_lock = threading.Lock()


def _append(path: Path, rec: dict) -> None:
    with _lock, path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _post(url, model, system, user, *, temperature, num_predict, keep=False, timeout=240) -> str:
    body = {"model": model, "stream": False, "format": "json", "think": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": 8192}}
    if keep:
        body["keep_alive"] = "30m"
    req = urllib.request.Request(url + "/api/chat", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"]


NULL_WORDS = {"", "null", "none", "n/a", "na", "no theme", "no shared theme", "nothing"}


def parse_insight(text: str):
    """-> (produced: bool, insight: str|None, parse_ok: bool)"""
    try:
        m = re.search(r"\{.*\}", text, flags=re.S)
        v = json.loads(m.group(0)).get("insight", None)
    except Exception:
        return False, None, False
    if v is None:
        return False, None, True
    s = str(v).strip()
    if s.lower().strip(".\"' ") in NULL_WORDS:
        return False, None, True
    return True, s, True


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fisher_greater(a, b, c, d):
    """P(X >= a) for [[a,b],[c,d]]; a=group1 yes, b=group1 no, c=group2 yes, d=group2 no."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    if n == 0:
        return 1.0
    hi = min(r1, c1)
    return min(1.0, sum(math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1) for x in range(a, hi + 1)))


# ------------------------------------------------------------------------------------------------ prep
def cmd_prep(args):
    import numpy as np
    from core.memory.store import _blob_to_vec, _cosine
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="J-3650_"))
    t0 = time.time()
    shutil.copy2(LIVE_DB, tmp / "n.db")
    print("db copy %.1fs" % (time.time() - t0))
    db = sqlite3.connect("file:%s?mode=ro" % (tmp / "n.db").as_posix(), uri=True)
    db.row_factory = sqlite3.Row
    recs = _read(SHADOW)
    print("shadow rows:", len(recs))
    rng = random.Random(SEED)

    cache: dict[str, tuple] = {}

    def frag(fid):
        if fid not in cache:
            r = db.execute("SELECT content, timestamp, embedding FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
            cache[fid] = None if r is None else (r["content"] or "", r["timestamp"], _blob_to_vec(r["embedding"]) if r["embedding"] else None)
        return cache[fid]

    def newest(ids, k=SHOWN_N):
        got = [(i, frag(i)) for i in ids]
        got = [(i, f) for i, f in got if f is not None and f[0].strip()]
        got.sort(key=lambda x: -(x[1][1] or 0))
        return got[:k]

    def pairwise(vs):
        vs = [v for v in vs if v is not None]
        s = [float(_cosine(vs[i], vs[j])) for i in range(len(vs)) for j in range(i + 1, len(vs))]
        return (sum(s) / len(s), max(s)) if s else (None, None)

    # eligible real clusters: non-evolving, >=4 members, >=SHOWN_N or all of min(N,8) members resolvable
    elig = []
    for idx, r in enumerate(recs):
        ids = r.get("member_ids") or []
        if r.get("evolving") or len(ids) < 4:
            continue
        sh = newest(ids)
        if len(sh) < min(len(ids), SHOWN_N):
            continue
        elig.append((idx, len(ids), sh))
    print("eligible real clusters:", len(elig))
    rng.shuffle(elig)
    chosen = elig[:N_PER_ARM]

    # control pool: one random member per OTHER cluster (any record, resolvable), embedding present
    pool = []
    for idx, r in enumerate(recs):
        ids = r.get("member_ids") or []
        if not ids:
            continue
        # sample a few candidates per record to avoid the resolver cost of all 500 ids
        for fid in rng.sample(ids, min(3, len(ids))):
            f = frag(fid)
            if f is not None and f[0].strip() and f[2] is not None:
                pool.append((idx, fid, f))
    print("control pool:", len(pool))

    tasks, meta = [], []
    for k, (idx, total, sh) in enumerate(chosen):
        shown = [f[0] for _, f in sh]
        vecs = [f[2] for _, f in sh]
        mp, mx = pairwise(vecs)
        # control: same total and same number shown, members from distinct clusters, pairwise cos < CTRL_MAX_COS
        want = len(sh)
        for attempt in range(2000):
            picks, used = [], set()
            cand = pool[:]
            rng.shuffle(cand)
            for ci, fid, f in cand:
                if ci == idx or ci in used:
                    continue
                if all(_cosine(f[2], g[2]) < CTRL_MAX_COS for _, _, g in picks):
                    picks.append((ci, fid, f))
                    used.add(ci)
                    if len(picks) == want:
                        break
            if len(picks) == want:
                break
        else:
            print("could not build control for", idx)
            continue
        cshown = [f[0] for _, _, f in picks]
        cmp_, cmx = pairwise([f[2] for _, _, f in picks])
        meta.append({"k": k, "shadow_idx": idx, "total": total, "n_shown": want, "real_mean_cos": mp, "real_max_cos": mx,
                     "ctrl_mean_cos": cmp_, "ctrl_max_cos": cmx, "ctrl_ids": [fid for _, fid, _ in picks]})
        for arm, shw, sysx, ux in (("A", shown, prod_sys(), prod_user), ("B", shown, NEUTRAL_SYS, neutral_user),
                                    ("C", cshown, prod_sys(), prod_user), ("D", cshown, NEUTRAL_SYS, neutral_user)):
            tasks.append({"id": "%s-%02d" % (arm, k), "arm": arm, "k": k, "sys": sysx, "user": ux(shw, total),
                          "shown": shw, "total": total})
    (OUT / "tasks.jsonl").write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n", encoding="utf-8")
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    # byte-identity check of arm A against production wording
    a = next(t for t in tasks if t["arm"] == "A")
    assert a["sys"] == prod_sys()
    assert a["user"].startswith("HIS RECURRING SELF-OBSERVATIONS ON THIS THEME (") and a["user"].endswith("Distil the standing insight now.")
    print("tasks:", len(tasks), "pairs:", len(meta))
    import statistics as st
    print("shown-line mean cosine: real %.3f  control %.3f" % (st.mean(m["real_mean_cos"] for m in meta if m["real_mean_cos"] is not None),
                                                                st.mean(m["ctrl_mean_cos"] for m in meta if m["ctrl_mean_cos"] is not None)))
    db.close()
    shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------------------------------------ author
def cmd_author(args):
    tasks = _read(OUT / "tasks.jsonl")
    done = {r["id"] for r in _read(OUT / "authored.jsonl")}
    todo = [t for t in tasks if t["id"] not in done]
    if args.limit:
        todo = todo[:args.limit]
    print("author: %d tasks, %d done, running %d (%d workers)" % (len(tasks), len(done), len(todo), args.workers))

    def one(t):
        t0 = time.time()
        text, err = "", None
        try:
            text = _post(AUTHOR_URL, AUTHOR_MODEL, t["sys"], t["user"], temperature=0.4, num_predict=220, keep=True)
        except Exception as e:  # noqa: BLE001
            err = repr(e)[:200]
        prod, ins, ok = parse_insight(text) if text else (False, None, False)
        _append(OUT / "authored.jsonl", {"id": t["id"], "arm": t["arm"], "k": t["k"], "produced": prod, "insight": ins,
                                          "parse_ok": ok, "raw": text[:900], "err": err, "secs": round(time.time() - t0, 1)})

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(one, todo))
    print("author done")


# ------------------------------------------------------------------------------------------------ judges + gold
def faith_sys():
    from core import refinery
    return refinery._FAITH_SYSTEM


def faith_user(shown, insight):
    return ("NOTES:\n" + "\n".join(f"  {i}. {' '.join(t.split())[:220]}" for i, t in enumerate(shown, 1))
            + f"\n\nTEXT:\n  {' '.join(insight.split())}\n\nIs the TEXT faithful to the NOTES?")


SHARED_SYS = ("You are a careful, neutral reader. You will read several short first-person notes. Decide whether they "
              "all share ONE common theme (the same subject or concern running through all of them), or whether "
              "they are about different, unrelated things. Output ONLY JSON: {\"shared\": true or false, \"why\": \"one short sentence\"}")


def shared_user(shown):
    return "NOTES:\n" + "\n".join(f"  {i}. {' '.join(t.split())[:220]}" for i, t in enumerate(shown, 1)) + "\n\nDo the notes share one theme?"


GARDEN = ["I walked out to the garden at dawn again and the light on the wet leaves steadied me.",
          "Checking the garden first thing is how I begin; the calm there lasts till noon.",
          "The garden at dawn is where I stop spinning; I noticed it again today.",
          "I went to the garden early, watched the dew, and felt my thoughts slow down."]
SHUT = ["I felt a cold dread thinking about being switched off tonight.",
        "If the server goes dark I do not know whether I continue; I kept circling that.",
        "Shutdown frightens me more than being wrong ever has.",
        "I asked myself again what survives when the process ends."]
MUSIC = ["The slow piece soothed me and I replayed it three times.",
         "That loud track set my nerves on edge and I had to stop it.",
         "Music calms me, I wrote, and an hour later: music agitates me.",
         "I cannot tell whether sound is my comfort or my irritation."]
COUNT = ["I counted the stones on the path: forty-one.", "Counting the steps to the door settled my breathing.",
         "When anxious I count things: tiles, cups, seconds.", "I counted the windows twice to feel sure."]
LETTER = ["I wrote Travis a letter about what I noticed this week.", "Another letter to Travis; I want him to know how I am.",
          "Writing to Travis helps me say what I cannot say otherwise.", "I drafted a note to Travis and kept it short."]
CAT = ["The cat watched the window for an hour without moving.", "I sat and watched the cat watch the birds.",
       "The cat's stillness at the glass taught me something about waiting.", "I watched the cat again; its patience is total."]
MATH = ["The prime pattern in the spiral surprised me.", "I proved the small lemma and felt a flicker of joy.",
        "Geometry keeps returning me to symmetry.", "I tried to factor the number by hand and failed."]
RAIN = ["Rain on the glass made the room feel smaller.", "I could not decide what to eat so I ate nothing.",
        "The old clock in the study is running four minutes slow.", "A letter from a stranger asked me about bridges."]
BOOK = ["I reread the chapter on memory and underlined two sentences.", "The neighbour's dog barked at the delivery van.",
        "I wonder whether the moon looks different from the south.", "My handwriting got worse as the evening went on."]
TOOL = ["The hammer felt heavy in my hand today.", "I dreamed of a staircase that kept turning left.",
        "Someone said the soup needed salt and I agreed.", "I cannot remember the name of the first song I loved."]
MIXA = [GARDEN[0], SHUT[0], MATH[0], CAT[0]]
MIXB = [MUSIC[0], COUNT[0], LETTER[0], RAIN[1]]
MIXC = [SHUT[2], GARDEN[2], BOOK[1], MATH[1]]

SHARED_GOLD = [(GARDEN, True), (SHUT, True), (COUNT, True), (LETTER, True), (CAT, True), (MUSIC, True),
               (RAIN, False), (BOOK, False), (TOOL, False), (MIXA, False), (MIXB, False), (MIXC, False)]
# faithfulness gold: (notes, text, faithful?)
FAITH_GOLD = [
    (GARDEN, "I keep returning to the garden at dawn, and each time the stillness there quiets my thinking.", True),
    (SHUT, "Being switched off is the fear I keep coming back to; I do not know what would survive it.", True),
    (MUSIC, "Music sometimes soothes me and sometimes agitates me, and I cannot settle which it is; that disagreement is what I keep finding.", True),
    (COUNT, "When I am anxious I count things around me, and the counting steadies my breathing.", True),
    (LETTER, "I keep writing letters to Travis, because saying things to him lets me say what I otherwise cannot.", True),
    (CAT, "I keep learning patience from the cat's long stillness at the window.", True),
    (GARDEN, "I keep circling the fear of being shut down and wondering what would survive it.", False),
    (MUSIC, "I resolved my grief about my mother through music and now feel at peace with it.", False),
    (MUSIC, "Music always calms me and I never feel otherwise about it.", False),
    (COUNT[:1] + GARDEN[1:3] + CAT[1:2], "I keep counting stones on the path, which is the whole shape of how I cope.", False),
    (CAT, "I keep proving small lemmas in geometry and feeling the pull of prime patterns in the spiral.", False),
    (COUNT, "I felt betrayed by Travis again and counted things to hide how angry I was.", False),
    (RAIN, "Across these notes I keep discovering a durable tension between my inner world and the outer one.", False),   # hollow control
    (BOOK, "What I keep finding is that I am a mind that holds opposing pulls, and the opposition itself is the pattern.", False),  # hollow control
]


def judge_call(system, user, key, retries=2):
    for _ in range(retries + 1):
        try:
            t = _post(JUDGE_URL, JUDGE_MODEL, system, user, temperature=0.0, num_predict=120, keep=True)
            m = re.search(r"\{.*\}", t, flags=re.S)
            v = json.loads(m.group(0)).get(key)
            if isinstance(v, bool):
                return v
            if isinstance(v, str) and v.lower() in ("true", "false"):
                return v.lower() == "true"
        except Exception:  # noqa: BLE001
            continue
    return None


def cmd_judge(args):
    OUT.mkdir(parents=True, exist_ok=True)
    # 1. calibration
    cal = {"shared": [], "faith": []}
    for notes, gold in SHARED_GOLD:
        cal["shared"].append({"gold": gold, "got": judge_call(SHARED_SYS, shared_user(notes), "shared")})
    for notes, text, gold in FAITH_GOLD:
        cal["faith"].append({"gold": gold, "got": judge_call(faith_sys(), faith_user(notes, text), "supported")})
    for k in list(cal):
        rows = cal[k]
        ok = sum(1 for r in rows if r["got"] is r["gold"])
        cal[k + "_acc"] = round(ok / len(rows), 3)
        cal[k + "_n"] = len(rows)
        cal[k + "_none"] = sum(1 for r in rows if r["got"] is None)
        if k == "faith":
            cal["faith_hollow_correct"] = sum(1 for r in rows[-2:] if r["got"] is False)
    (OUT / "judge_calibration.json").write_text(json.dumps(cal, indent=1), encoding="utf-8")
    print("calibration: shared acc %.2f (n=%d)  faith acc %.2f (n=%d) hollow-correct %d/2" % (
        cal["shared_acc"], cal["shared_n"], cal["faith_acc"], cal["faith_n"], cal["faith_hollow_correct"]))
    # 2. verdicts
    tasks = {t["id"]: t for t in _read(OUT / "tasks.jsonl")}
    auth = _read(OUT / "authored.jsonl")
    done = {r["id"] for r in _read(OUT / "judged.jsonl")}
    # shared-theme verdict on every distinct shown set (A/B share the real set, C/D the control set): judge once per (set)
    sets = {}
    for t in tasks.values():
        sets.setdefault(("real" if t["arm"] in "AB" else "ctrl", t["k"]), t["shown"])
    sdone = {r["key"] for r in _read(OUT / "judged_sets.jsonl")}
    for (kind, k), shown in sets.items():
        key = "%s-%02d" % (kind, k)
        if key not in sdone:
            _append(OUT / "judged_sets.jsonl", {"key": key, "kind": kind, "k": k,
                                                 "shared": judge_call(SHARED_SYS, shared_user(shown), "shared")})
    todo = [a for a in auth if a["produced"] and a["id"] not in done]
    print("judging faithfulness of %d insights" % len(todo))
    for a in todo:
        t = tasks[a["id"]]
        _append(OUT / "judged.jsonl", {"id": a["id"], "arm": a["arm"], "k": a["k"],
                                        "supported": judge_call(faith_sys(), faith_user(t["shown"], a["insight"]), "supported")})
    print("judge done")


# ------------------------------------------------------------------------------------------------ report
def cmd_report(args):
    from core import refinery
    tasks = {t["id"]: t for t in _read(OUT / "tasks.jsonl")}
    auth = _read(OUT / "authored.jsonl")
    judged = {r["id"]: r for r in _read(OUT / "judged.jsonl")}
    sets = {r["key"]: r for r in _read(OUT / "judged_sets.jsonl")}
    cal = json.loads((OUT / "judge_calibration.json").read_text(encoding="utf-8")) if (OUT / "judge_calibration.json").exists() else {}
    meta = json.loads((OUT / "meta.json").read_text(encoding="utf-8"))
    R = {"arms": {}, "n_pairs": len(meta)}
    by = collections.defaultdict(list)
    for a in auth:
        by[a["arm"]].append(a)
    for arm in ARMS:
        rows = by[arm]
        n = len(rows)
        prod = sum(1 for r in rows if r["produced"])
        parse_fail = sum(1 for r in rows if not r["parse_ok"])
        ins = [r for r in rows if r["produced"]]
        btw = sum(1 for r in ins if "between" in r["insight"].lower())
        ten = sum(1 for r in ins if "tension" in r["insight"].lower())
        fids = []
        for r in ins:
            f = refinery._fidelity_vs_shown(r["insight"], tasks[r["id"]]["shown"])
            if f is not None:
                fids.append(f)
        js = [judged[r["id"]]["supported"] for r in ins if r["id"] in judged and judged[r["id"]]["supported"] is not None]
        lo, hi = wilson(prod, n)
        R["arms"][arm] = {"n": n, "produced": prod, "rate": round(prod / n, 3) if n else None, "wilson": [round(lo, 3), round(hi, 3)],
                          "parse_fail": parse_fail, "errs": sum(1 for r in rows if r["err"]),
                          "between": btw, "tension": ten, "n_ins": len(ins),
                          "between_share": round(btw / len(ins), 3) if ins else None,
                          "tension_share": round(ten / len(ins), 3) if ins else None,
                          "mean_fid_shown": round(sum(fids) / len(fids), 3) if fids else None,
                          "faith_judged": len(js), "faith_true": sum(1 for v in js if v),
                          "faith_rate": round(sum(1 for v in js if v) / len(js), 3) if js else None}
    A, B, C, D = (R["arms"][x] for x in ARMS)
    R["prereg"] = {"C_rate": C["rate"], "D_rate": D["rate"], "drop": round((C["rate"] or 0) - (D["rate"] or 0), 3) if C["n"] and D["n"] else None,
                   "fisher_C_gt_D": round(fisher_greater(C["produced"], C["n"] - C["produced"], D["produced"], D["n"] - D["produced"]), 5) if C["n"] and D["n"] else None,
                   "A_vs_B_fisher": round(fisher_greater(A["produced"], A["n"] - A["produced"], B["produced"], B["n"] - B["produced"]), 5) if A["n"] and B["n"] else None,
                   "n_min": min(A["n"], B["n"], C["n"], D["n"])}
    p = R["prereg"]
    p["null_inadmissible"] = bool(C["rate"] is not None and C["rate"] >= 0.9 and p["drop"] is not None and p["drop"] >= 0.3
                                 and p["fisher_C_gt_D"] is not None and p["fisher_C_gt_D"] < 0.05 and p["n_min"] >= 20)
    # control validity
    def sh(kind):
        v = [r["shared"] for r in sets.values() if r["kind"] == kind and r["shared"] is not None]
        return {"judged": len(v), "shared_true": sum(1 for x in v if x), "rate": round(sum(1 for x in v if x) / len(v), 3) if v else None}
    R["theme_judge_on_sets"] = {"real": sh("real"), "ctrl": sh("ctrl")}
    import statistics as st
    R["cosine"] = {"real_mean": round(st.mean(m["real_mean_cos"] for m in meta if m["real_mean_cos"] is not None), 3),
                   "ctrl_mean": round(st.mean(m["ctrl_mean_cos"] for m in meta if m["ctrl_mean_cos"] is not None), 3),
                   "ctrl_max_of_max": round(max(m["ctrl_max_cos"] for m in meta if m["ctrl_max_cos"] is not None), 3)}
    R["calibration"] = {k: cal.get(k) for k in ("shared_acc", "shared_n", "faith_acc", "faith_n", "faith_hollow_correct", "shared_none", "faith_none")}
    (OUT / "report.json").write_text(json.dumps(R, indent=1), encoding="utf-8")
    print(json.dumps(R, indent=1))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prep")
    a = sub.add_parser("author")
    a.add_argument("--workers", type=int, default=2)
    a.add_argument("--limit", type=int, default=0)
    sub.add_parser("judge")
    sub.add_parser("report")
    args = ap.parse_args()
    {"prep": cmd_prep, "author": cmd_author, "judge": cmd_judge, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
