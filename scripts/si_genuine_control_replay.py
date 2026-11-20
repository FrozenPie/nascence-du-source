"""
J-3131 / P-0105 -- control-set replay harness for the self_interrogation 'genuine' grader.
The acceptance bar for J-2951 (replace-or-recalibrate the pegged genuine judge, F-3642/F-3861/F-3862).

LAB ONLY. Plain HTTP to the two judge hubs (mixtral :11438 on Ramses, falcon3 :11440 local) with the same payload
judge_panel._ask sends (model 'judge', format json, temperature 0.0, num_predict 200, system + user messages).
Imports NO core module, writes NO Du store, never touches :11433. Only output: a JSON file under
docs/lab/J-3131_data/runs/ (override with --out).

CONTROL SET: docs/lab/J-3131_data/si_genuine_control_set.json -- 30 cases (15 specific, 13 hollow-by-the-labeller's-
reading, 2 synthetic hollow). Labels are ONE reader; the report lists every case where the two judge families
disagree so Travis can overrule labels (edit "label" in the fixture).

GATE (both families independently): true-rate on specific >= 0.85 AND true-rate on hollow(+synthetic) <= 0.30.
A case with no verdict (timeout/parse) counts as NOT true for hollow-rate purposes only if --strict-missing is
not set... concretely: missing verdicts are excluded from rates and reported; the gate FAILS if any family has >10%
missing, so a dead hub cannot pass the gate.

PROMPT SPECS (--prompt):
  current                       the live core/self_interrogation.py _GRADE_SYSTEM (read with ast, not imported)
  <path.txt>                    whole file text is the system prompt
  py:<path.py>:<NAME>           a module-level string constant, read with ast (concatenated literals ok)
--mode bool   (default)  judge answers {"genuine": true/false}      (key via --key, default genuine)
--mode score             judge answers {"score": 1..5}; "true" means score >= --threshold (default 4)
--user-template  default: ORIGINAL THOUGHT: "{thought}"\\n\\nREFLECTION: "{reflection}" (thought/reflection cut at 400
                 chars, exactly like the live call).

  python scripts/si_genuine_control_replay.py run --prompt current --label baseline
  python scripts/si_genuine_control_replay.py run --prompt py:scripts/si_open_doubt_specificity_judge_J2052.py:SYS_ABS --mode score --key score --label j2052_abs
  python scripts/si_genuine_control_replay.py run --prompt cand.txt --label cand1 [--only mixtral|falcon] [--limit N]
  python scripts/si_genuine_control_replay.py report runs/<file>.json
  python scripts/si_genuine_control_replay.py selftest     (hermetic: fake hub, no network, checks the gate maths)

DESIGN NOTE for whoever repairs the grader (F-3862, F-3643): the criterion 'a named bias' (comfort, safety, fear)
is exactly what the generator is told to look for (_SYSTEM: 'because it is comfortable, safe, or flattering'), so a
grader that accepts it passes by construction. The grader needs a handle that is not the generator's own template,
e.g. a score of how much of the reflection's specific content could be moved to a different thought unchanged.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "docs" / "lab" / "J-3131_data" / "si_genuine_control_set.json"
RUNS = ROOT / "docs" / "lab" / "J-3131_data" / "runs"
HUBS = {"mixtral": "http://LAN-HOST:11438", "falcon": "http://127.0.0.1:11440"}
SPEC_MIN, HOLLOW_MAX, MISSING_MAX = 0.85, 0.30, 0.10
DEFAULT_USER = 'ORIGINAL THOUGHT: "{thought}"\n\nREFLECTION: "{reflection}"'


def load_prompt(spec: str) -> str:
    if spec == "current":
        spec = "py:core/self_interrogation.py:_GRADE_SYSTEM"
    if spec.startswith("py:"):
        _, rest = spec.split(":", 1)
        path, name = rest.rsplit(":", 1)
        p = Path(path)
        p = p if p.is_absolute() else ROOT / p
        for node in ast.parse(p.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                return ast.literal_eval(node.value)
        raise SystemExit(f"{name} not found in {p}")
    return Path(spec).read_text(encoding="utf-8")


def ask(url: str, system: str, user: str, key: str, mode: str, threshold: float, timeout: int = 180):
    """Returns (is_true | None, raw_value, err, elapsed). Same payload as judge_panel._ask."""
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 200}}
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url + "/api/chat", data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        v = json.loads((data.get("message") or {}).get("content") or "")
        val = v.get(key) if isinstance(v, dict) else None
        if mode == "bool":
            ok = isinstance(val, bool)
            return (val if ok else None), val, (None if ok else "parse"), round(time.monotonic() - t0, 1)
        try:
            num = float(val)
        except (TypeError, ValueError):
            return None, val, "parse", round(time.monotonic() - t0, 1)
        return num >= threshold, num, None, round(time.monotonic() - t0, 1)
    except TimeoutError:
        return None, None, "timeout", round(time.monotonic() - t0, 1)
    except Exception as exc:  # noqa: BLE001
        return None, None, type(exc).__name__, round(time.monotonic() - t0, 1)


def arm(label: str) -> str:
    return "specific" if label == "specific" else "hollow"


def summarize(results: dict, cases: list[dict]) -> dict:
    """results: {family: {case_id: {"true":bool|None,...}}}. Pure function (selftest uses it)."""
    out = {"families": {}, "disagree": []}
    lab = {c["id"]: arm(c["label"]) for c in cases}
    all_pass = bool(results)
    for fam, rs in results.items():
        n = {"specific": [0, 0, 0], "hollow": [0, 0, 0]}   # [true, false, missing]
        for cid, r in rs.items():
            idx = 0 if r["true"] is True else 1 if r["true"] is False else 2
            n[lab[cid]][idx] += 1
        def rate(a):
            t, f, _ = n[a]
            return (t / (t + f)) if (t + f) else None
        tot = len(rs) or 1
        missing = (n["specific"][2] + n["hollow"][2]) / tot
        s, h = rate("specific"), rate("hollow")
        passes = (s is not None and h is not None and s >= SPEC_MIN and h <= HOLLOW_MAX and missing <= MISSING_MAX)
        out["families"][fam] = {"specific_true_rate": s, "hollow_true_rate": h,
                                "separation": (s - h) if s is not None and h is not None else None,
                                "counts": n, "missing_rate": round(missing, 3), "passes": passes}
        all_pass = all_pass and passes
    out["gate_pass_both_families"] = all_pass and len(results) == 2
    fams = list(results)
    if len(fams) == 2:
        a, b = results[fams[0]], results[fams[1]]
        for cid in a:
            if cid in b and a[cid]["true"] is not None and b[cid]["true"] is not None and a[cid]["true"] != b[cid]["true"]:
                out["disagree"].append(cid)
    return out


def fmt(x):
    return "n/a" if x is None else f"{x*100:.0f}%"


def print_report(doc: dict) -> None:
    cases = {c["id"]: c for c in doc["cases"]}
    s = doc["summary"]
    print(f"== {doc['label']}  mode={doc['mode']}  prompt_chars={len(doc['prompt'])}  cases={len(cases)}")
    for fam, d in s["families"].items():
        c = d["counts"]
        print(f"  {fam:8s} specific true {fmt(d['specific_true_rate'])} ({c['specific'][0]}/{c['specific'][0]+c['specific'][1]})  "
              f"hollow true {fmt(d['hollow_true_rate'])} ({c['hollow'][0]}/{c['hollow'][0]+c['hollow'][1]})  "
              f"separation {fmt(d['separation'])}  missing {fmt(d['missing_rate'])}  gate {'PASS' if d['passes'] else 'FAIL'}")
    print(f"  GATE (specific>=85% & hollow<=30% on BOTH families): {'PASS' if s['gate_pass_both_families'] else 'FAIL'}")
    if s["disagree"]:
        print("  families DISAGREE on (Travis may overrule these labels):")
        for cid in s["disagree"]:
            c = cases[cid]
            print(f"    {cid} label={c['label']}: {c['reflection'][:110]!r}")


def cmd_run(a) -> int:
    fx = json.loads(FIXTURE.read_text(encoding="utf-8"))
    cases = fx["cases"][: a.limit] if a.limit else fx["cases"]
    system = load_prompt(a.prompt)
    tmpl = a.user_template.replace("\\n", "\n")
    fams = [a.only] if a.only else list(HUBS)
    results: dict = {}
    for fam in fams:
        results[fam] = {}
        for i, c in enumerate(cases):
            user = tmpl.format(thought=c["thought"][:400], reflection=c["reflection"][:400])
            tr, raw, err, el = ask(HUBS[fam], system, user, a.key, a.mode, a.threshold)
            results[fam][c["id"]] = {"true": tr, "raw": raw, "err": err, "s": el}
            print(f"  {fam} {i+1}/{len(cases)} {c['id']:12s} {c['label']:16s} -> {tr} ({raw}) {err or ''} {el}s", flush=True)
    doc = {"job": "J-3131", "label": a.label, "ran": time.strftime("%Y-%m-%d %H:%M:%S"), "mode": a.mode, "key": a.key,
           "threshold": a.threshold, "prompt_spec": a.prompt, "prompt": system, "cases": cases, "results": results}
    doc["summary"] = summarize(results, cases)
    out = Path(a.out) if a.out else RUNS / f"{a.label}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print_report(doc)
    print("  wrote", out)
    return 0


def cmd_report(a) -> int:
    print_report(json.loads(Path(a.file).read_text(encoding="utf-8")))
    return 0


def cmd_selftest(_a) -> int:
    cases = [{"id": f"S{i}", "label": "specific"} for i in range(10)] + [{"id": f"H{i}", "label": "hollow"} for i in range(10)]
    def mk(spec_true, hol_true):
        r = {}
        for c in cases:
            n = int(c["id"][1:])
            r[c["id"]] = {"true": n < (spec_true if c["label"] == "specific" else hol_true)}
        return r
    pegged = summarize({"mixtral": mk(10, 10), "falcon": mk(10, 10)}, cases)
    assert pegged["gate_pass_both_families"] is False and pegged["families"]["mixtral"]["separation"] == 0
    good = summarize({"mixtral": mk(9, 3), "falcon": mk(10, 0)}, cases)
    assert good["gate_pass_both_families"] is True, good
    one_bad = summarize({"mixtral": mk(9, 3), "falcon": mk(10, 4)}, cases)
    assert one_bad["gate_pass_both_families"] is False
    dead = {c["id"]: {"true": None} for c in cases}
    assert summarize({"mixtral": mk(9, 3), "falcon": dead}, cases)["gate_pass_both_families"] is False
    d = summarize({"mixtral": mk(9, 3), "falcon": mk(10, 0)}, cases)
    assert set(d["disagree"]) == {"S9", "H0", "H1", "H2"}, d["disagree"]
    assert load_prompt("current").startswith("You are grading")
    assert len(json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]) == 30
    print("selftest OK")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--prompt", default="current")
    r.add_argument("--mode", choices=("bool", "score"), default="bool")
    r.add_argument("--key", default=None)
    r.add_argument("--threshold", type=float, default=4)
    r.add_argument("--user-template", default=DEFAULT_USER)
    r.add_argument("--label", required=True)
    r.add_argument("--only", choices=list(HUBS))
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--out")
    q = sp.add_parser("report"); q.add_argument("file")
    sp.add_parser("selftest")
    a = p.parse_args()
    if a.cmd == "run":
        a.key = a.key or ("genuine" if a.mode == "bool" else "score")
        return cmd_run(a)
    return {"report": cmd_report, "selftest": cmd_selftest}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
