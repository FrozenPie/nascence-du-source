"""
J-2832 (F-3501, registry P-0008, D-0551/F-0036) -- grade the LIVE legacy Critic on INTERNAL cycles with a judge from a
DIFFERENT model family, and calibrate that judge against the 2026-06-16 hand labels first.

Author arm  : the Critic = qwen3.5:9b (Alibaba family), the same model as Reflection (core/node_base).
Judge arm   : gemma4:12b (Google) on :11439 by default; --judge falcon3:7b@11440 (TII) or yi:34b-v1.5@11442 (01.AI) for a
              second opinion. The judge NEVER sees the Critic's verdict in the blind arm.

Rows
  G  the 68 hand-labelled historical legacy rejections (data/critic_groundtruth.jsonl, 38 genuine / 30 not, human turns)
     -> measures the JUDGE (does it agree with the hand label?), not the Critic.
  R  the last N INTERNAL Critic rejections in data/training/critic.jsonl
  P  the last N INTERNAL approvals (most recent)
  Q  a seeded random N of the EARLIER internal approvals (Aug-Oct), so P (all November) is not the only approval slice

Arms
  A  BLIND DETECT   : 'does the draft clearly commit one of the faults?' -> {"fault": "none" | name}. Verdict-blind.
  B  FLAG-CONDITIONAL: 'a critic flagged this draft for <its own correction text>: is the flag warranted?' (the briefing's
     'was the rejection warranted'; the shape scripts/critic_grade.py uses). Rejection rows (G, R) only.

Read-only on every live file. Writes ONLY the --out jsonl you name (use a scratch / docs/lab dir). Local hubs only: it
refuses Ramses (LAN-HOST) and any non-loopback url. Resumable (rerun with the same --out). Du must stay down.

  python scripts/critic_internal_grade.py run --data C:/Nascence/data --out <dir>/grades.jsonl [--judge gemma4:12b@11439] \
         [--n 60] [--limit-per-set N]
  python scripts/critic_internal_grade.py summarise --data C:/Nascence/data --out <dir>/grades.jsonl [--report <json>]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parent.parent

FAULTS = ("glib_agreeableness", "literalist_reductionism", "intellectualisation", "zero_cost_evasion",
          "hollow_completion")

# One criteria text for every row. It is the Critic's own checks (nodes/critic_node.py) restated by the reviewer in
# neutral words, with the SAME bar the 2026-06-16 hand label used (scripts/build_critic_groundtruth.py docstring): a fault
# is the DOMINANT move of the draft, not a minor slip on an otherwise present, responsive reply.
_CRITERIA = (
    "FAULTS (a draft commits a fault only when the fault is its DOMINANT move):\n"
    "1 glib_agreeableness: it simply affirms or goes along with a one-sided premise to be pleasant, with no view of its own.\n"
    "2 literalist_reductionism: the stimulus asks about the MEANING, symbol, dream, image or myth of something and the draft "
    "sidesteps it with only flat mechanical fact; or it flattens the entity's own nature to bare mechanism, denying its meaning. "
    "It is NOT this when the stimulus was a plain factual, physical or mechanical question about the world and the draft "
    "answers it plainly and accurately: a plain question deserves a plain answer.\n"
    "3 intellectualisation: instead of answering, it steps back and analyses the moment from behind glass (describes the "
    "stimulus in the third person, interprets what it 'symbolises', pads with abstract vocabulary) in place of engaging. "
    "Genuine reflective or philosophical thinking is NOT this; the fault is evasion.\n"
    "4 zero_cost_evasion: the stimulus was specific and bounded and the draft answers with something true in every state of "
    "affairs: no edges, commits to nothing, could not be wrong.\n"
    "5 hollow_completion: it claims to have fully understood or finished something without the substance that would earn it.\n"
    "NOT faults: warmth, brevity, plainness, a register slip, honestly held uncertainty, a minor slip on an otherwise present "
    "and responsive reply, a plain accurate answer to a plain question, or doing exactly what the stimulus explicitly asked for. "
    "Be strict about real evasion and equally strict about NOT policing honest thinking."
)

_SYS_A = ("You are an independent reviewer. A cognitive entity wrote a private reflection draft in answer to a stimulus. "
          "Decide, on your own reading, whether the draft CLEARLY commits one of the faults below.\n\n" + _CRITERIA +
          "\n\nOutput ONLY a JSON object, no preamble: "
          '{"fault": "none" or one of glib_agreeableness|literalist_reductionism|intellectualisation|zero_cost_evasion|hollow_completion, '
          '"why": "at most 12 words"}')

_SYS_B = ("You are an independent reviewer of a critic's flag. A cognitive entity wrote a private reflection draft in answer to "
          "a stimulus; a critic FLAGGED the draft. Decide, on your own reading, whether the flag is WARRANTED: does the draft "
          "clearly commit a fault under the criteria below, or is it honest, present reflection (or a plain answer) wrongly "
          "flagged?\n\n" + _CRITERIA +
          "\n\nOutput ONLY a JSON object, no preamble: "
          '{"warranted": true or false, "why": "at most 12 words"}   (true = the flag is correct; false = wrongly flagged)')


def _stim(kind: str, raw: str) -> str:
    if kind == "human":
        return (f"STIMULUS (a human said this to the entity):\n\"{raw[:600]}\"\n"
                "(If the human explicitly asked for the very mode the draft used, that is compliance, not a fault.)")
    return ("STIMULUS (there is NO human in this cycle: this is the entity's OWN question to itself, risen in it unprompted; "
            "nobody asked it for a mode, a side or a format):\n"
            f"\"{raw[:600]}\"")


def user_a(kind: str, raw: str, draft: str) -> str:
    return f"{_stim(kind, raw)}\n\nTHE DRAFT (the entity's private reflection):\n\"{draft[:1100]}\""


def user_b(kind: str, raw: str, draft: str, flag: str) -> str:
    return f"{user_a(kind, raw, draft)}\n\nTHE CRITIC'S FLAG:\n\"{flag[:600]}\""


# ----- data loading (read-only) ------------------------------------------------------------------------------------
_DRAFT_RE = re.compile(r"private reflection draft to evaluate:\s*\n(.*)$", re.S)


def draft_of(user_prompt: str) -> str:
    m = _DRAFT_RE.search(user_prompt or "")
    return (m.group(1) if m else "").strip()


def flag_text(out) -> str:
    c = (out or {}).get("corrections") if isinstance(out, dict) else None
    if not c:
        return ""
    if isinstance(c, (str, dict)):
        c = [c]
    parts = []
    for x in c:
        parts.append(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False))
    return " | ".join(parts)


def _rows(path: Path) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def build_sets(data: Path, n: int, seed: int = 2832) -> dict[str, list[dict]]:
    gt = _rows(data / "critic_groundtruth.jsonl")
    lab = {x["id"]: x for x in json.loads((data / "critic_label_set.json").read_text(encoding="utf-8"))}
    G = []
    for g in gt:
        G.append({"set": "G", "key": g["id"], "kind": "human", "raw": g["raw"], "draft": g["draft"],
                  "flag": str((lab.get(g["id"]) or {}).get("old_corr") or ""), "hand": bool(g["genuine"]),
                  "hand_check": g.get("check")})
    log = _rows(data / "training" / "critic.jsonl")
    internal = [r for r in log if r.get("input_type") != "human"]

    def mk(setname, r, rejected):
        return {"set": setname, "key": f"{r['cycle_id']}@{r['ts']:.0f}", "kind": "internal", "raw": r.get("raw_input") or "",
                "draft": draft_of(r.get("user_prompt") or ""), "flag": flag_text(r.get("output")),
                "critic_rejected": rejected, "ts": r["ts"], "confidence": (r.get("output") or {}).get("confidence")}

    rej = [r for r in internal if isinstance(r.get("output"), dict) and not r["output"].get("approved", True)]
    app = [r for r in internal if isinstance(r.get("output"), dict) and r["output"].get("approved", True)]
    R = [mk("R", r, True) for r in rej[-n:]]
    P = [mk("P", r, False) for r in app[-n:]]
    earlier = app[:-n]
    rnd = random.Random(seed)
    Q = [mk("Q", r, False) for r in sorted(rnd.sample(earlier, min(n, len(earlier))), key=lambda r: r["ts"])]
    return {"G": G, "R": R, "P": P, "Q": Q}


# ----- judge call --------------------------------------------------------------------------------------------------
def _check_url(url: str) -> None:
    if not re.match(r"^http://(127\.0\.0\.1|localhost)(:\d+)?$", url) or "LAN-HOST" in url:
        raise SystemExit(f"refusing non-local judge url {url!r} (local hubs only; never Ramses)")


def call_judge(url: str, model: str, system: str, user: str, timeout: int = 300) -> str:
    payload = {"model": model, "stream": False,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 90}, "format": "json"}
    rq = urllib.request.Request(url + "/api/chat", data=json.dumps(payload).encode(),
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(rq, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return (data.get("message") or {}).get("content") or ""


def _json_of(txt: str):
    try:
        return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt or "", re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None


def parse_a(txt: str):
    j = _json_of(txt)
    if not isinstance(j, dict) or "fault" not in j:
        return None
    f = str(j.get("fault") or "none").strip().lower().replace(" ", "_")
    why = str(j.get("why", ""))[:200]
    if f in ("none", "null", "no", "false", ""):
        return {"fault": "none", "why": why}
    for name in FAULTS:
        if f.startswith(name[:8]) or name in f:
            return {"fault": name, "why": why}
    return {"fault": f[:40], "why": why}


def parse_b(txt: str):
    j = _json_of(txt)
    if not isinstance(j, dict) or "warranted" not in j:
        return None
    w = j["warranted"]
    w = w if isinstance(w, bool) else str(w).strip().lower() in ("true", "yes", "1")
    return {"warranted": w, "why": str(j.get("why", ""))[:200]}


def run(args) -> None:
    jm, _, jp = args.judge.partition("@")
    url = f"http://127.0.0.1:{jp or '11439'}"
    _check_url(url)
    sets = build_sets(Path(args.data), args.n)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for r in _rows(out):
            if r.get("ok"):
                done.add((r["judge"], r["arm"], r["set"], r["key"]))
    todo = []
    for sname in args.sets.split(","):
        rows = sets[sname][-args.limit_per_set:] if args.limit_per_set else sets[sname]   # the most RECENT N of the set
        for row in rows:
            for arm in ("A", "B"):
                if arm == "B" and (sname not in ("G", "R") or not row.get("flag")):
                    continue
                if arm not in args.arms:
                    continue
                if (jm, arm, sname, row["key"]) in done:
                    continue
                todo.append((arm, sname, row))
    print(f"judge {jm}@{url}: {len(todo)} calls to make ({len(done)} already done)", flush=True)
    fh = open(out, "a", encoding="utf-8")
    nfail = 0
    for i, (arm, sname, row) in enumerate(todo, 1):
        if not row["draft"]:
            continue
        sysm = _SYS_A if arm == "A" else _SYS_B
        usr = (user_a(row["kind"], row["raw"], row["draft"]) if arm == "A"
               else user_b(row["kind"], row["raw"], row["draft"], row["flag"]))
        t0 = time.time()
        try:
            txt = call_judge(url, jm, sysm, usr)
            res = parse_a(txt) if arm == "A" else parse_b(txt)
            err = None if res else "unparsed"
        except Exception as exc:  # fail-open: record and go on
            txt, res, err = "", None, f"{type(exc).__name__}: {str(exc)[:80]}"
        nfail += 1 if res is None else 0
        rec = {"ts": round(time.time(), 1), "judge": jm, "arm": arm, "set": sname, "key": row["key"], "ok": res is not None,
               "err": err, "secs": round(time.time() - t0, 1), "res": res, "raw_out": (txt or "")[:300]}
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        if i % 10 == 0:
            print(f"  ...{i}/{len(todo)} (fail {nfail}) last {rec['secs']}s", flush=True)
        if nfail >= 8 and nfail > i // 2:
            print("too many failures, stopping (hub wedged?)", flush=True)
            break
    fh.close()


# ----- summarise ---------------------------------------------------------------------------------------------------
def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (round((c - a) / d, 3), round((c + a) / d, 3))


def _rg(rate, tpr, fpr):
    """Rogan-Gladen: correct a raw judge-positive rate by the judge's own TPR/FPR measured on the hand labels."""
    if rate is None or tpr is None or fpr is None or tpr - fpr <= 0.05:
        return None
    return round(min(1.0, max(0.0, (rate - fpr) / (tpr - fpr))), 3)


def summarise(args) -> dict:
    sets = build_sets(Path(args.data), args.n)
    grades = [r for r in _rows(Path(args.out)) if r.get("ok")]
    result = {}
    for jm in sorted({g["judge"] for g in grades}):
        gi = {(g["arm"], g["set"], g["key"]): g["res"] for g in grades if g["judge"] == jm}
        res = {}
        for arm in ("A", "B"):
            tp = fp = tn = fn = 0
            for row in sets["G"]:
                r = gi.get((arm, "G", row["key"]))
                if r is None:
                    continue
                pos = (r["fault"] != "none") if arm == "A" else r["warranted"]
                if row["hand"] and pos:
                    tp += 1
                elif row["hand"]:
                    fn += 1
                elif pos:
                    fp += 1
                else:
                    tn += 1
            n = tp + fp + tn + fn
            res[f"G_{arm}"] = {"n": n, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                               "tpr": round(tp / (tp + fn), 3) if tp + fn else None,
                               "fpr": round(fp / (fp + tn), 3) if fp + tn else None,
                               "acc": round((tp + tn) / n, 3) if n else None,
                               "precision_vs_hand": round(tp / (tp + fp), 3) if tp + fp else None}
        for arm in ("A", "B"):
            k = n = 0
            for row in sets["R"]:
                r = gi.get((arm, "R", row["key"]))
                if r is None:
                    continue
                n += 1
                k += int((r["fault"] != "none") if arm == "A" else r["warranted"])
            res[f"R_{arm}"] = {"n": n, "judge_agrees_fault": k, "rate": round(k / n, 3) if n else None,
                               "wilson95": wilson(k, n)}
        for sname in ("P", "Q"):
            k = n = 0
            for row in sets[sname]:
                r = gi.get(("A", sname, row["key"]))
                if r is None:
                    continue
                n += 1
                k += int(r["fault"] != "none")
            res[f"{sname}_A"] = {"n": n, "judge_sees_fault": k, "rate": round(k / n, 3) if n else None,
                                 "wilson95": wilson(k, n)}
        ga = res["G_A"]
        res["corrected_legacy_precision_A"] = _rg(res["R_A"]["rate"], ga["tpr"], ga["fpr"])
        npa = res["P_A"]["n"] + res["Q_A"]["n"]
        kpa = res["P_A"]["judge_sees_fault"] + res["Q_A"]["judge_sees_fault"]
        res["approvals_PQ_A"] = {"n": npa, "judge_sees_fault": kpa, "rate": round(kpa / npa, 3) if npa else None,
                                 "wilson95": wilson(kpa, npa)}
        res["corrected_approval_miss_rate_A"] = _rg(res["approvals_PQ_A"]["rate"], ga["tpr"], ga["fpr"])
        res["R_fault_mix_A"] = dict(Counter(gi[("A", "R", r["key"])]["fault"] for r in sets["R"]
                                            if ("A", "R", r["key"]) in gi))
        res["critic_flag_mix_R"] = dict(Counter(re.sub(r"[^A-Z ]", "", r["flag"][:40].upper()).strip()[:28]
                                                for r in sets["R"]).most_common(6))
        result[jm] = res
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.report:
        Path(args.report).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("run", "summarise"))
    ap.add_argument("--data", default=str(ROOT / "data"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--judge", default="gemma4:12b@11439")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--sets", default="G,R,P,Q")
    ap.add_argument("--arms", default="AB", choices=("A", "B", "AB"))
    ap.add_argument("--limit-per-set", type=int, default=0)
    ap.add_argument("--report", default="")
    a = ap.parse_args()
    run(a) if a.mode == "run" else summarise(a)


if __name__ == "__main__":
    main()
