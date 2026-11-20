"""
Nascence -- TRAIN LAB: J-1852 (successor of J-1206) -- J-0724's gemma4:e4b vs qwen3.5:9b model A/B replayed on the
160 OPEN-context prompts (docs/lab/train_wording_ab_qwen_replicate_J-0791_2026-09-22_events.json, key "mid").
CURRENT wording only, temperature 0.75, max_tokens 400, real _build_system_prompt(mid_train=True) + verbatim TRAIN_HOLD
mid-thread user block.  Reuses the J-0791 script's isolation/robustness by importing it (its module-level write-audit
hook, telemetry no-ops, module-resolution check and call/retry helpers); only the schedule and result store differ.

Does NOT edit nodes/inner_monologue_node.py; does NOT rule D-0165.  Du must be DOWN and nobody else on :11433.
Order: blocks of BLOCK prompts alternate gemma / qwen (so hub drift cannot line up with a model); qwen goes LAST so the
hub finishes with its resident model qwen3.5:9b, and a final keep_alive restore call is made regardless.

  python scripts/train_lab_model_ab_open_replay_J-1852.py --dry-run | --probe | (run)
"""
from __future__ import annotations

import os
import sys

SCRATCH_DIR = os.environ.setdefault(
    "LAB_SCRATCH", r"C:\Users\USER\AppData\Local\Temp\claude\C--Users-USER--claude-spares-spare-mQmh6q"
                   r"\8dfdd29a-f01b-46a6-a986-87ead012ffdf\scratchpad")
sys.argv_orig = list(sys.argv)

import argparse
import asyncio
import importlib.util
import json
import subprocess
import time
import urllib.request
import datetime as _dt
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "j0791", str(Path(__file__).resolve().parent / "train_lab_wording_ab_replicate_J-0791_2026-09-08.py"))
L = importlib.util.module_from_spec(_spec)
sys.modules["j0791"] = L
_spec.loader.exec_module(L)          # installs the audit hook, telemetry no-ops, repo imports (no main())

from core import speech_timing_shadow as _sts          # J-1971 store: model_client.call_node_json appends a row per call
_sts.log_call = lambda *a, **k: None
_sts.log_human = lambda *a, **k: None
_sts._append = lambda *a, **k: None

JOB = "J-1852"
S = Path(SCRATCH_DIR)
RESULTS = S / f"{JOB}_results.jsonl"
SUMMARY = S / f"{JOB}_run_summary.json"
EVENTS = L.ROOT / "docs" / "lab" / "train_wording_ab_qwen_replicate_J-0791_2026-09-22_events.json"
MODELS = ["gemma4:e4b", "qwen3.5:9b"]
HOT = L.HOT_URL
BLOCK = 20


def du_down() -> bool:
    try:
        tail = open(L.LIVE_DATA / "nascence.log", "rb").read()[-3000:].decode("utf-8", "replace")
        last = [x for x in tail.splitlines() if x.strip()][-1]
        gate1 = "Nascence shutting down." in last
    except Exception:
        return False
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                              "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                              "Where-Object { $_.CommandLine -match 'run_nascence\\.py' } | Measure-Object).Count"],
                             capture_output=True, text=True, timeout=60)
        gate2 = int((out.stdout or "0").strip() or "0") == 0
    except Exception:
        return False
    return gate1 and gate2


def restore_qwen() -> str:
    """Make qwen3.5:9b the resident model again (keep_alive 2h, as core/model_client.py uses) and evict others."""
    msgs = []
    try:
        req = urllib.request.Request(HOT + "/api/ps")
        ps = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
        for m in ps.get("models", []):
            if m.get("name") != "qwen3.5:9b":
                body = json.dumps({"model": m["name"], "keep_alive": 0}).encode()
                urllib.request.urlopen(urllib.request.Request(HOT + "/api/generate", body,
                                       {"Content-Type": "application/json"}), timeout=60).read()
                msgs.append("evicted " + m["name"])
        body = json.dumps({"model": "qwen3.5:9b", "prompt": "", "keep_alive": "2h", "options": {"num_ctx": 8192}}).encode()
        urllib.request.urlopen(urllib.request.Request(HOT + "/api/generate", body,
                               {"Content-Type": "application/json"}), timeout=300).read()
        ps = json.loads(urllib.request.urlopen(HOT + "/api/ps", timeout=20).read().decode())
        msgs.append("resident now: " + str([m["name"] for m in ps.get("models", [])]))
    except Exception as exc:
        msgs.append(f"restore error {type(exc).__name__}: {exc}")
    return "; ".join(msgs)


def load_done() -> dict:
    d = {}
    if RESULTS.exists():
        for r in L._load_jsonl(RESULTS):
            d[(r["model"], r["train_id"])] = r
    return d


async def run(args) -> int:
    ev = json.loads(EVENTS.read_text(encoding="utf-8"))["mid"]
    assert len(ev) == 160
    n = L.InnerMonologueNode()
    from core import sitting as _sit, emissary_tension as _et
    assert _sit.dwell_steer() == "" and _et.keystone_steer() == ""
    sysp = n._build_system_prompt(L._S(), wandering=False, mid_train=True)
    assert sysp.count(L.CURRENT_BLOCK) == 1
    ups = {e["train_id"]: L._mid_train_user_prompt(e["origin"], e["last_step"], e["ledger"]) for e in ev}
    rows, bad = L._module_resolution()
    print(f"module resolution: {len(rows)} modules, {len(bad)} outside tree")
    if bad:
        return 2
    print(f"system prompt {len(sysp)} chars; {len(ev)} events; real_next opened share = "
          f"{sum(e['real_next']['opened'] for e in ev)}/{len(ev)}")
    if args.dry_run:
        L._print_write_audit("dry-run")
        return 0
    if not du_down():
        print("ABORT: Du not confirmed down")
        return 3
    fp0 = L._live_fingerprint()
    print("hub meta:", L._hub_meta())
    L.CALL_TIMEOUT = 300
    counters = {"attempts": 0, "infra_attempts_failed": 0}
    if args.probe:
        L.MODEL = MODELS[0]
        r = await L._call_with_retries(sysp, ups[ev[0]["train_id"]], "probe", counters)
        print("probe", {k: r[k] for k in ("ok", "opened", "unresolved", "intention", "latency_s", "error")}, r["thought"][:200])
        print("restore:", restore_qwen())
        L._print_write_audit("probe")
        return 0
    done = load_done()
    stop = None
    blocks = [ev[i:i + BLOCK] for i in range(0, len(ev), BLOCK)]
    order = []
    for bi, blk in enumerate(blocks):
        ms = MODELS if bi % 2 == 0 else MODELS[::-1]
        for m in ms:
            order.append((m, blk))
    # force final block to end on qwen
    ncall = 0
    t0 = time.time()
    try:
        for m, blk in order:
            L.MODEL = m
            for e in blk:
                key = (m, e["train_id"])
                if key in done and (done[key].get("ok") or done[key].get("error_class") == "content"):
                    continue
                if ncall and ncall % 20 == 0 and not du_down():
                    stop = "Du gate failed"
                    break
                res = await L._call_with_retries(sysp, ups[e["train_id"]], f"{m}/{e['train_id']}", counters)
                res.update({"model": m, "train_id": e["train_id"], "ts": _dt.datetime.now().isoformat(timespec="seconds")})
                with open(RESULTS, "a", encoding="utf-8") as f:
                    f.write(json.dumps(res, ensure_ascii=False) + "\n")
                done[key] = res
                ncall += 1
                if ncall % 10 == 0:
                    print(f"  [{ncall}] {m} lat={res['latency_s']}s ok={res['ok']} elapsed={time.time()-t0:.0f}s", flush=True)
                if args.max_calls and ncall >= args.max_calls:
                    stop = "max-calls"
                    break
            if stop:
                break
    finally:
        print("restore:", restore_qwen())
    fp1 = L._live_fingerprint()
    same = fp0 == fp1
    print("fingerprint identical:", same)
    if not same:
        print("DIFF:", json.dumps({k: (fp0[k], fp1[k]) for k in fp0 if fp0[k] != fp1[k]}, sort_keys=True)[:1500])
    L._print_write_audit("final")
    SUMMARY.write_text(json.dumps({"stop": stop, "calls": ncall, "counters": counters, "fp_identical": same,
                                   "fp_before": fp0, "fp_after": fp1,
                                   "live_write_attempts": len(L.LIVE_WRITE_ATTEMPTS),
                                   "tree_write_attempts": len(L.TREE_WRITE_ATTEMPTS),
                                   "wall_s": round(time.time() - t0)}, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--max-calls", type=int, default=0)
    sys.exit(asyncio.run(run(ap.parse_args())))
