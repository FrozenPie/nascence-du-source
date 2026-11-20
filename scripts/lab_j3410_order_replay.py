"""J-3410 (from F-4044): option-ORDER control replay for Du's judge prompts.

F-4044 found that on command-r7b the unfilled placeholder form {"relation": "<a|b|c>"} is order-biased: reversing the
listed options flipped the verdict distribution. This lab asks the same question of the boolean placeholders the judge
panel ships ("true|false", "true or false", "<true or false>", '{"k": true} or {"k": false}'): does a judge's answer
change when ONLY the order of the two listed options is reversed?

For each pilot station it
  1. builds the REAL prompt by calling the production function with core.judge_panel.rule_detail stubbed to capture
     (system, user, key) -- nothing is re-typed here, so the prompt text is the shipped text;
  2. asks a LOCAL hub the original prompt and the same prompt with the option order reversed (reverse_order());
  3. reports, per station and hub: the true-rate under each order, how many verdicts flipped, P(first-listed option
     chosen) under each order (a pure position effect gives ~1.0 under both; no effect gives the two summing to 1.0),
     an exact McNemar p on the discordant pairs, and accuracy against the fixture's hand label where it has one.

Never touches Ramses (LAN-HOST). Hubs are the local CPU-tier hubs :11440 falcon3:7b and :11439 gemma4:12b (the hot
lane :11433 hung on 2026-11-06, see the J-3410 finding). Reads fixtures under docs/lab read-only; writes only --out.

    python scripts/lab_j3410_order_replay.py run  --out docs/lab/J-3410_data/order_replay_runs.jsonl
    python scripts/lab_j3410_order_replay.py report --out docs/lab/J-3410_data/order_replay_runs.jsonl
    python scripts/lab_j3410_order_replay.py cases           # list the cases without any network call
    python scripts/lab_j3410_order_replay.py cases --captured data/judge_inputs_log.jsonl   # + real captured inputs

J-3695: data/judge_inputs_log.jsonl (written by core.judge_panel._capture_inputs: sampled + every split, user text
capped at 1200 chars, system text kept only as a sha1/length) is read here by load_captured(). The system text is
recovered by matching the hash against the shipped prompts of the pilot stations; rows whose hash matches nothing are
counted as unresolved, never guessed. Captured cases have no hand label (label None), so they enter the flip-rate and
position-effect numbers but not the accuracy columns.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (import core BEFORE anything that resolves paths)

assert Path(core.__file__).resolve().parent.parent == ROOT, "core resolved outside this tree"

HUBS = {"falcon3": "http://127.0.0.1:11440", "gemma4": "http://127.0.0.1:11439"}
FORBIDDEN = ("LAN-HOST",)

# ----------------------------------------------------------------------------------------------------------------
# option-order reversal
# ----------------------------------------------------------------------------------------------------------------
_PAIR_OF_LITERALS = re.compile(r'(\{\s*\\?"(?P<k>[A-Za-z_]+)\\?"\s*:\s*)(?P<a>true|false)(\s*\}\s*or\s*)(\{\s*\\?"(?P=k)\\?"\s*:\s*)(?P<b>true|false)(\s*\})')
_PLACEHOLDER = re.compile(r'\b(true|false)(\s*\|\s*|\s+or\s+)(true|false)\b')
_PREFILLED = re.compile(r'(\{\s*\\?"(?:[A-Za-z_]+)\\?"\s*:\s*)(true|false)(\s*,)')


def reverse_order(system: str) -> str:
    """Return `system` with the listed order of every two-option boolean schema reversed.

    Handles: '{"k": true} or {"k": false}' (both literals), 'true|false' / 'true or false' / '<true or false>'
    (unfilled placeholder). A single pre-filled example ('{"k": true, ...') flips its literal (the model sees the
    OTHER option named). A prompt with none of these forms comes back unchanged (callers check `changed`)."""
    out = _PAIR_OF_LITERALS.sub(lambda m: f'{m.group(1)}{m.group("b")}{m.group(4)}{m.group(5)}{m.group("a")}{m.group(7)}', system)
    if out != system:
        return out
    out = _PLACEHOLDER.sub(lambda m: f"{m.group(3)}{m.group(2)}{m.group(1)}", system)
    if out != system:
        return out
    return _PREFILLED.sub(lambda m: m.group(1) + ("false" if m.group(2) == "true" else "true") + m.group(3), system, count=1)


def first_listed(system: str) -> "bool | None":
    """Which boolean the schema line names FIRST in this exact text (True/False), None when no two-option form."""
    m = _PAIR_OF_LITERALS.search(system)
    if m:
        return m.group("a") == "true"
    m = _PLACEHOLDER.search(system)
    if m:
        return m.group(1) == "true"
    m = _PREFILLED.search(system)
    if m:
        return m.group(2) == "true"
    return None


# ----------------------------------------------------------------------------------------------------------------
# real prompts, captured from production code
# ----------------------------------------------------------------------------------------------------------------
class _Capture:
    def __init__(self):
        self.calls = []

    async def rule_detail(self, system, user, key, context="", **kw):
        self.calls.append({"system": system, "user": user, "key": key})
        return {"verdict": None, "how": "unavailable", "v1": None, "v2": None}


def _capture(coro_fn, *a, patch_attrs: "dict | None" = None, **kw):
    from core import judge_panel as jp
    cap = _Capture()
    old = jp.rule_detail
    jp.rule_detail = cap.rule_detail
    patched = []
    try:
        for (mod, name), val in (patch_attrs or {}).items():
            patched.append((mod, name, getattr(mod, name)))
            setattr(mod, name, val)
        asyncio.run(coro_fn(*a, **kw))
    finally:
        jp.rule_detail = old
        for mod, name, val in patched:
            setattr(mod, name, val)
    return cap.calls


def build_cases(limit_per: int = 0, seed: int = 3410) -> list:
    rnd = random.Random(seed)
    cases = []
    lab = ROOT / "docs" / "lab"

    # --- P-0117 guidance same-lesson (J-3232 pairs + hand labels; S = same lesson, N/U/C/X = not the same) ---
    from core import guidance_learning as gl
    pairs = json.loads((lab / "J-3232_data" / "pairs.json").read_text(encoding="utf-8"))
    labels = json.loads((lab / "J-3232_data" / "hand_labels.json").read_text(encoding="utf-8"))["labels"]
    same, notsame = [], []
    for p in pairs:
        lb = labels.get(p["id"])
        if lb in (None, "B"):
            continue
        (same if lb == "S" else notsame).append((p, lb))
    rnd.shuffle(notsame)
    pick = same + notsame[: max(len(same), 60)]
    for p, lb in pick:
        calls = _capture(gl._same_lesson, p["existing"], p["new"])
        if calls:
            c = calls[0]
            cases.append({"station": "P-0117 same_lesson", "case": p["id"], "key": c["key"], "system": c["system"],
                          "user": c["user"], "label": lb == "S", "label_raw": lb})

    # --- P-0109 lane2 held (J-3210 hand labels: H = held, U = unsettled) ---
    from core import lane2
    rows = [json.loads(x) for x in (lab / "J-3210_lane2_held_labels.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    for r in rows:
        calls = _capture(lane2._judge_prior, r["prediction"], r["observed_now"],
                         patch_attrs={(lane2, "percept_lines"): (lambda p: p)})
        if calls:
            c = calls[0]
            cases.append({"station": "P-0109 held", "case": r["id"], "key": c["key"], "system": c["system"],
                          "user": c["user"], "label": r["label"] == "H", "label_raw": r["label"]})

    # --- P-0110 lane2 metaphor (J-3205 passages; Claude pre-labels F figurative / A arguable / L literal) ---
    ticks = {}
    for x in (lab / "metaphor_union_ticks.jsonl").read_text(encoding="utf-8").splitlines():
        if x.strip():
            r = json.loads(x)
            ticks[r["tick_ts"]] = r
    pre = [json.loads(x) for x in (lab / "J-3205_data" / "prelabels_claude.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    fa = [p for p in pre if p["label"] in ("F", "A")]
    lit = [p for p in pre if p["label"] == "L"]
    rnd.shuffle(lit)
    for p in fa + lit[:60]:
        t = ticks.get(p["tick_ts"])
        if not t:
            continue
        calls = _capture(lane2._judge_metaphor, {"notice": t["passage"]})
        if calls:
            c = calls[0]
            cases.append({"station": "P-0110 metaphor", "case": p["id"], "key": c["key"], "system": c["system"],
                          "user": c["user"], "label": (p["label"] == "F") if p["label"] != "A" else None,
                          "label_raw": p["label"]})
    if limit_per:
        out, seen = [], {}
        for c in cases:
            seen[c["station"]] = seen.get(c["station"], 0) + 1
            if seen[c["station"]] <= limit_per:
                out.append(c)
        cases = out
    return interleave(cases)


def sys_sha(system: str) -> str:
    return hashlib.sha1(system.encode("utf-8", "replace")).hexdigest()[:16]


def load_captured(path: Path, known_cases: list, per_sha_cap: int = 200) -> tuple:
    """Turn captured judge inputs into replayable cases. Returns (cases, n_unresolved, n_rows).

    A row is replayable only when its sys_sha equals the hash of a system prompt the pilot builders produce today
    (known_cases); a row whose user text was cut at the capture cap (user_len > len(user)) is skipped, since a
    truncated question is not the question the judges saw."""
    if not path.exists():
        return [], 0, 0
    by_sha = {}
    for c in known_cases:
        by_sha.setdefault(sys_sha(c["system"]), c)
    out, unresolved, n, seen = [], 0, 0, {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        n += 1
        base = by_sha.get(r.get("sys_sha"))
        if base is None or r.get("key") != base["key"]:
            unresolved += 1
            continue
        if isinstance(r.get("user_len"), int) and r["user_len"] > len(r.get("user") or ""):
            unresolved += 1
            continue
        seen[r["sys_sha"]] = seen.get(r["sys_sha"], 0) + 1
        if seen[r["sys_sha"]] > per_sha_cap:
            continue
        out.append({"station": base["station"] + " (captured)", "case": "cap@%s" % r.get("ts"), "key": r["key"],
                    "system": base["system"], "user": r["user"], "label": None, "label_raw": "captured"})
    return out, unresolved, n


def interleave(cases: list) -> list:
    """Round-robin by station, positives and negatives alternating inside a station, so a run stopped at any point
    has covered every station about equally (the hubs are slow and shared)."""
    by = {}
    for c in cases:
        by.setdefault(c["station"], {True: [], False: [], None: []}).setdefault(c["label"], []).append(c)
    queues = []
    for st, d in by.items():
        q = []
        pos, neg, unk = list(d[True]), list(d[False]), list(d[None])
        while pos or neg or unk:
            for src in (pos, neg, unk):
                if src:
                    q.append(src.pop(0))
        queues.append(q)
    out = []
    while any(queues):
        for q in queues:
            if q:
                out.append(q.pop(0))
    return out


# ----------------------------------------------------------------------------------------------------------------
# asking a local hub (same payload as core.judge_panel._ask)
# ----------------------------------------------------------------------------------------------------------------
def ask(url: str, system: str, user: str, key: str, timeout: float = 150.0, num_predict: int = 200):
    assert not any(f in url for f in FORBIDDEN), "this lab never calls Ramses"
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": num_predict}}
    req = urllib.request.Request(url + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        v = json.loads((data.get("message") or {}).get("content") or "")
        if isinstance(v, dict) and isinstance(v.get(key), bool):
            return v[key], None, round(time.monotonic() - t0, 2)
        return None, "parse", round(time.monotonic() - t0, 2)
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        return None, "http:" + type(exc).__name__, round(time.monotonic() - t0, 2)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None, "parse", round(time.monotonic() - t0, 2)


def run(out: Path, hubs: list, cases: list, ask_fn=ask) -> int:
    done = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
                done.add((r["hub"], r["station"], r["case"], r["order"]))
            except Exception:
                pass
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out, "a", encoding="utf-8") as fh:
        for c in cases:
            rev = reverse_order(c["system"])
            if rev == c["system"]:
                continue
            for hub in hubs:
                for order, sysmsg in (("orig", c["system"]), ("rev", rev)):
                    k = (hub, c["station"], c["case"], order)
                    if k in done:
                        continue
                    v, err, el = ask_fn(HUBS[hub], sysmsg, c["user"], c["key"])
                    fh.write(json.dumps({"hub": hub, "station": c["station"], "case": c["case"], "order": order,
                                         "first_listed": first_listed(sysmsg), "verdict": v, "err": err, "s": el,
                                         "label": c["label"], "label_raw": c["label_raw"]}) + "\n")
                    fh.flush()
                    n += 1
    return n


# ----------------------------------------------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------------------------------------------
def _mcnemar_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * p)


def report(rows: list) -> dict:
    by = {}
    for r in rows:
        by.setdefault((r["station"], r["hub"]), {}).setdefault(r["case"], {})[r["order"]] = r
    res = {}
    for (st, hub), cs in sorted(by.items()):
        n_pair = n_true_o = n_true_r = 0
        t2f = f2t = 0
        first_o = first_r = 0
        acc = {"orig": [0, 0], "rev": [0, 0]}
        pos_neg = {"orig": {"pos": [0, 0], "neg": [0, 0]}, "rev": {"pos": [0, 0], "neg": [0, 0]}}
        invalid = 0
        for case, d in cs.items():
            o, v = d.get("orig"), d.get("rev")
            if not o or not v:
                continue
            if o["verdict"] is None or v["verdict"] is None:
                invalid += 1
                continue
            n_pair += 1
            n_true_o += int(o["verdict"]); n_true_r += int(v["verdict"])
            if o["verdict"] and not v["verdict"]:
                t2f += 1
            if not o["verdict"] and v["verdict"]:
                f2t += 1
            first_o += int(o["verdict"] == o["first_listed"])
            first_r += int(v["verdict"] == v["first_listed"])
            lb = o["label"]
            if lb is not None:
                for name, x in (("orig", o), ("rev", v)):
                    acc[name][0] += 1
                    acc[name][1] += int(x["verdict"] == lb)
                    pos_neg[name]["pos" if lb else "neg"][0] += 1
                    pos_neg[name]["pos" if lb else "neg"][1] += int(x["verdict"] == lb)
        if not n_pair:
            continue
        res["%s | %s" % (st, hub)] = {
            "n_pairs": n_pair, "invalid_pairs": invalid,
            "true_rate_orig": round(n_true_o / n_pair, 3), "true_rate_rev": round(n_true_r / n_pair, 3),
            "flips_T_to_F": t2f, "flips_F_to_T": f2t, "flip_rate": round((t2f + f2t) / n_pair, 3),
            "mcnemar_p": round(_mcnemar_p(t2f, f2t), 4),
            "p_first_listed_orig": round(first_o / n_pair, 3), "p_first_listed_rev": round(first_r / n_pair, 3),
            "first_listed_sum": round((first_o + first_r) / n_pair, 3),
            "acc_orig": (round(acc["orig"][1] / acc["orig"][0], 3) if acc["orig"][0] else None),
            "acc_rev": (round(acc["rev"][1] / acc["rev"][0], 3) if acc["rev"][0] else None),
            "recall_pos_orig": (round(pos_neg["orig"]["pos"][1] / pos_neg["orig"]["pos"][0], 3) if pos_neg["orig"]["pos"][0] else None),
            "recall_pos_rev": (round(pos_neg["rev"]["pos"][1] / pos_neg["rev"]["pos"][0], 3) if pos_neg["rev"]["pos"][0] else None),
            "recall_neg_orig": (round(pos_neg["orig"]["neg"][1] / pos_neg["orig"]["neg"][0], 3) if pos_neg["orig"]["neg"][0] else None),
            "recall_neg_rev": (round(pos_neg["rev"]["neg"][1] / pos_neg["rev"]["neg"][0], 3) if pos_neg["rev"]["neg"][0] else None),
        }
    return res


def cases_with_captured(limit_per: int, captured: str) -> list:
    cs = build_cases(limit_per)
    if captured:
        extra, unres, n = load_captured(Path(captured), cs)
        print("captured rows", n, "replayable", len(extra), "unresolved", unres)
        cs = interleave(cs + extra)
    return cs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "report", "cases"])
    ap.add_argument("--out", default=str(ROOT / "docs" / "lab" / "J-3410_data" / "order_replay_runs.jsonl"))
    ap.add_argument("--hubs", default="falcon3,gemma4")
    ap.add_argument("--limit-per", type=int, default=0)
    ap.add_argument("--captured", default="", help="data/judge_inputs_log.jsonl: add real captured inputs (J-3695)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    out = Path(a.out)
    if a.cmd == "cases":
        cs = cases_with_captured(a.limit_per, a.captured)
        from collections import Counter
        print(Counter(c["station"] for c in cs))
        for st in sorted({c["station"] for c in cs}):
            c = next(x for x in cs if x["station"] == st)
            print("==", st, "first_listed:", first_listed(c["system"]), "->", first_listed(reverse_order(c["system"])))
        return 0
    if a.cmd == "run":
        cs = cases_with_captured(a.limit_per, a.captured)
        print("cases", len(cs), "hubs", a.hubs)
        n = run(out, [h for h in a.hubs.split(",") if h], cs)
        print("asked", n)
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines() if x.strip()]
    rep = report(rows)
    (out.parent / (out.stem + "_report.json")).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    for k, v in rep.items():
        print(k, json.dumps(v))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
