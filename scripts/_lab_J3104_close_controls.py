"""J-3104 (P-0101) acceptance replay: do the pursuit-close judges still discriminate in the NEW prompt shape?

Builds 10 positive controls, 5 circling negatives (the P-0101 cases.json set, re-expressed as pursuits so the prompt comes
from core.pursuit_close_shadow.build_prompt, i.e. the real code), plus N real saturated pursuits with their real
standings, and asks each hub directly (judge_panel._ask).  READ-ONLY on the live register; writes only --out.
Default hubs are LOCAL (falcon3 :11440, gemma4:12b :11439).  Ramses (mixtral :11438) is the founder's gaming machine and
is NOT called unless --ramses is passed explicitly (20+N calls: a lab job runs it when the machine is free).
Run: python scripts/_lab_J3104_close_controls.py --out <file.json> [--ramses] [--real 10] [--cases <cases.json>]"""
from __future__ import annotations
import argparse, asyncio, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import core.pursuit_close_shadow as pcs  # noqa: E402
import core.judge_panel as jp  # noqa: E402

CASES = r"C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER--claude-spares-spare-AEHCil\aa94f138-79e2-4f75-92fd-106b1898e0bd\scratchpad\P-0101\cases.json"
REG = r"C:\Nascence\data\pursuits_active.json"
LOCAL_HUBS = {"falcon3:7b": "http://127.0.0.1:11440", "gemma4:12b": "http://127.0.0.1:11439"}
RAMSES_HUBS = {"mixtral:8x7b": "http://LAN-HOST:11438"}


def build_cases(cases_path: str, reg_path: str, n_real: int) -> list[dict]:
    reg = json.load(open(reg_path, encoding="utf-8"))
    by_open = {(p.get("open") or "").strip(): p for p in reg if (p.get("open") or "").strip()}
    out = []
    for c in json.load(open(cases_path, encoding="utf-8")):
        if c["label"] not in ("POS", "NEG_circle"):
            continue
        m = re.match(r"PURSUIT \(driving question\): (.*?)\n\nITS STANDING POSITION: (.*?)\n\n", c["user"], re.S)
        q, st = m.group(1), m.group(2)
        src = by_open.get(q.strip())
        birth = (src or {}).get("question") or "The cat shifts on the sill and the light goes grey over the roofs."
        out.append({"id": c["id"], "label": c["label"],
                    "p": {"id": c["id"], "question": birth, "standing": st, "open": q, "advances": 40, "status": "saturated"}})
    real = sorted((p for p in reg if p.get("status") == "saturated" and (p.get("open") or "").strip().endswith("?")
                   and p.get("standing")), key=lambda p: str(p.get("id")))[:n_real]
    for p in real:
        out.append({"id": "real_" + str(p["id"])[:8], "label": "REAL",
                    "p": {"id": p["id"], "question": p.get("question", ""), "standing": p["standing"], "open": p["open"],
                          "advances": p.get("advances", 40), "status": "saturated"}})
    for c in out:
        b = pcs.build_prompt(c["p"])
        assert b is not None, c["id"]
        c["system"], c["user"], c["fields"] = b
    return out


async def run(cases, hubs, out=None):
    import aiohttp
    res = []
    async with aiohttp.ClientSession() as s:
        for name, url in hubs.items():
            for c in cases:
                v, why, err, el = await jp._ask(s, url, c["system"], c["user"], "resolved")
                res.append({"hub": name, "id": c["id"], "label": c["label"], "verdict": v, "why": (why or "")[:200],
                            "err": err, "s": round(el, 1)})
                print(f"{name:14s} {c['id']:14s} {c['label']:10s} -> {v} {err or ''}", flush=True)
                if out:                                    # partial runs (a busy hub times out) are not lost
                    Path(out).write_text(json.dumps({"summary": summarize(res), "results": res, "partial": True},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    return res


def summarize(res):
    out = {}
    for r in res:
        k = (r["hub"], r["label"])
        a = out.setdefault(k, {"true": 0, "false": 0, "none": 0})
        a["true" if r["verdict"] is True else "false" if r["verdict"] is False else "none"] += 1
    return {f"{h}|{l}": v for (h, l), v in out.items()}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ramses", action="store_true", help="also call mixtral on Ramses (founder's gaming machine; opt-in)")
    ap.add_argument("--only-ramses", action="store_true")
    ap.add_argument("--real", type=int, default=10)
    ap.add_argument("--hubs", default="", help="comma list of hub names to use (default: all local hubs)")
    ap.add_argument("--cases", default=CASES)
    ap.add_argument("--reg", default=REG)
    a = ap.parse_args()
    cases = build_cases(a.cases, a.reg, a.real)
    hubs = {} if a.only_ramses else dict(LOCAL_HUBS)
    if a.hubs:
        hubs = {k: v for k, v in hubs.items() if k in a.hubs.split(",")}
    if a.ramses or a.only_ramses:
        hubs.update(RAMSES_HUBS)
    res = asyncio.run(run(cases, hubs, a.out))
    Path(a.out).write_text(json.dumps({"summary": summarize(res), "results": res, "n_cases": len(cases)},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summarize(res), indent=1))
