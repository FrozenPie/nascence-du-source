"""Du Prompt-to-Model Benchmark Suite Runner (Stage A Archetype Screening + Stage B Per-Prompt Deep Banks).

SAFETY GATES:
  1. Shared GPU & Du Ollama Ports (:11433..:11442):
     - REFUSES to run unless `--confirm-du-down` is passed AND no active Du process / recent `data/llm_calls.jsonl` write (<120s) is detected.
  2. CPU-Only Spare-Port Track (`--cpu-spare-port`, e.g. http://127.0.0.1:11455):
     - Permitted for thread-capped standalone CPU `llama-server.exe` runs (e.g. Ternary-Bonsai-2 PTQ1_0 / Q2_0) ONLY when targeting a port outside Du's range (:11433..:11442).
  3. `--status` is 100% static/read-only and safe to run anytime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "lab" / "du_benchmark_manifest_p0.json"
FIXTURES_PATH = ROOT / "data" / "lab" / "du_benchmark_fixtures_p0.json"
OUT_DIR = ROOT / "data" / "lab" / "du_benchmark"
DU_RESERVED_PORTS = {str(p) for p in range(11433, 11445)}


def check_du_running(recent_window_s: float = 120.0) -> list[str]:
    """Return active Du indicators (recent llm_calls.jsonl writes or running processes)."""
    signals: list[str] = []
    llm_calls_file = ROOT / "data" / "llm_calls.jsonl"
    if llm_calls_file.exists():
        age_s = time.time() - llm_calls_file.stat().st_mtime
        if age_s < recent_window_s:
            signals.append(f"data/llm_calls.jsonl modified {age_s:.1f}s ago (< {recent_window_s:.0f}s)")
    try:
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'run_nascence|du_pulse' -and $_.CommandLine -notmatch 'Get-CimInstance' } | Select-Object -ExpandProperty CommandLine"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        signals.extend([line.strip() for line in res.stdout.splitlines() if line.strip()])
    except Exception as exc:
        signals.append(f"process_check_error: {exc}")
    return signals


def assert_execution_permitted(confirmed_du_down: bool, cpu_spare_port: bool, base_url: str) -> None:
    if cpu_spare_port:
        for p in DU_RESERVED_PORTS:
            if f":{p}" in base_url:
                raise SystemExit(
                    f"BLOCKED: --cpu-spare-port cannot target Du reserved port :{p} ({base_url}). Use a spare port e.g. :11455."
                )
        return
    if not confirmed_du_down:
        raise SystemExit(
            "BLOCKED: Du uses all standard ports. Pass --confirm-du-down after stopping Du."
        )
    active = check_du_running()
    if active:
        raise SystemExit(
            f"BLOCKED: Active Du signal(s) detected ({len(active)}): {active[0][:100]}"
        )


def query_ps_placement(base_url: str, model: str, timeout: int = 10) -> dict:
    """Poll Ollama /api/ps to record actual VRAM and total RAM placement (F-3064 check)."""
    req = urllib.request.Request(f"{base_url}/api/ps")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for m in data.get("models", []):
            if m.get("name") == model or m.get("model") == model:
                size_total = m.get("size") or 0
                size_vram = m.get("size_vram") or 0
                vram_pct = round(100.0 * size_vram / size_total, 1) if size_total else 0.0
                return {
                    "size_bytes": size_total,
                    "size_vram_bytes": size_vram,
                    "vram_pct": vram_pct,
                    "context_length": m.get("context_length"),
                }
    except Exception as exc:
        return {"ps_error": repr(exc)[:100]}
    return {"size_bytes": 0, "size_vram_bytes": 0, "vram_pct": 0.0}


def unload_ollama_model(base_url: str, model: str) -> None:
    """Explicitly unload an Ollama model after its pass so the 1080 Ti VRAM is clean for the next candidate."""
    body = {"model": model, "keep_alive": 0}
    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as _:
            pass
    except Exception:
        pass


def call_endpoint(
    base_url: str,
    model: str,
    backend: str,
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = False,
    num_ctx: int = 8192,
    num_predict: int = 350,
    temperature: float = 0.3,
    think: bool = False,
    reasoning_effort: str = "none",
    timeout: int = 240,
) -> dict:
    """Execute one benchmark call via Ollama (/api/chat) or llama-server (/v1/chat/completions) with pinned settings."""
    t0 = time.time()
    if backend.startswith("llama_server"):
        body: dict = {
            "model": model,
            "stream": False,
            "temperature": temperature,
            "max_tokens": num_predict,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if reasoning_effort and reasoning_effort != "default":
            body["reasoning_effort"] = reasoning_effort
        if expect_json:
            body["response_format"] = {"type": "json_object"}
        url = f"{base_url}/v1/chat/completions"
    else:
        body = {
            "model": model,
            "stream": False,
            "keep_alive": "10m",
            "think": think,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
                "num_predict": num_predict,
            },
        }
        if expect_json:
            body["format"] = "json"
        url = f"{base_url}/api/chat"

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {
            "ok": False,
            "error": repr(exc)[:140],
            "wall_s": round(time.time() - t0, 2),
            "pinned_num_ctx": num_ctx,
            "think": think,
            "reasoning_effort": reasoning_effort,
        }

    wall_s = round(time.time() - t0, 2)
    if backend.startswith("llama_server"):
        choices = payload.get("choices") or [{}]
        msg = choices[0].get("message") or {}
        content = (msg.get("content") or "").strip()
        reasoning_text = msg.get("reasoning_content") or ""
        usage = payload.get("usage") or {}
        timings = payload.get("timings") or {}
        pe_count = usage.get("prompt_tokens") or timings.get("prompt_n") or 0
        ev_count = usage.get("completion_tokens") or timings.get("predicted_n") or 0
        pe_tok_s = round(timings.get("prompt_per_second") or 0.0, 2)
        gen_tok_s = round(timings.get("predicted_per_second") or 0.0, 2)
        load_s = 0.0
        ttft_s = round((timings.get("prompt_ms") or 0.0) / 1000.0, 3)
        placement = {"backend": backend, "cpu_only": True, "vram_pct": 0.0}
    else:
        ns = 1e9
        load_s = round((payload.get("load_duration") or 0) / ns, 3)
        pe_count = payload.get("prompt_eval_count") or 0
        pe_s = (payload.get("prompt_eval_duration") or 0) / ns
        ev_count = payload.get("eval_count") or 0
        ev_s = (payload.get("eval_duration") or 0) / ns
        pe_tok_s = round(pe_count / pe_s, 2) if pe_s > 0 else 0.0
        gen_tok_s = round(ev_count / ev_s, 2) if ev_s > 0 else 0.0
        ttft_s = round(load_s + pe_s, 3)
        msg = payload.get("message") or {}
        content = (msg.get("content") or "").strip()
        reasoning_text = msg.get("thinking") or ""
        placement = query_ps_placement(base_url, model)

    valid_json = False
    if content:
        try:
            start, end = content.find("{"), content.rfind("}")
            if start != -1 and end != -1 and end > start:
                json.loads(content[start : end + 1])
                valid_json = True
        except Exception:
            valid_json = False

    return {
        "ok": True,
        "wall_s": wall_s,
        "load_s": load_s,
        "ttft_est_s": ttft_s,
        "prompt_tokens": pe_count,
        "prompt_tok_s": pe_tok_s,
        "output_tokens": ev_count,
        "gen_tok_s": gen_tok_s,
        "thinking_chars": len(reasoning_text),
        "pinned_num_ctx": num_ctx,
        "think": think,
        "reasoning_effort": reasoning_effort,
        "valid_json": valid_json,
        "placement": placement,
        "content": content,
    }


def print_status() -> None:
    if not MANIFEST_PATH.exists() or not FIXTURES_PATH.exists():
        raise SystemExit("Phase 0 manifest or fixtures missing.")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    active_du = check_du_running()
    models = manifest.get("candidate_models_primary") or []
    print("=== Du Prompt-to-Model Benchmark Suite — Phase 0 Status (v2.0) ===")
    print(f"Manifest: {MANIFEST_PATH} (schema v{manifest['schema_version']})")
    print(f"  Total registry rows:   {manifest['summary']['total_registry_rows']}")
    print(f"  Dispositions:          {manifest['summary']['dispositions']}")
    print(f"  Callable prompt sites: {manifest['summary']['callable_total']} (115 keys/stages)")
    print(f"  Archetype breakdown:   {manifest['summary']['archetype_counts']}")
    print(f"  Primary model slate:   {len(models)} models")
    print(f"  Resident seats target: {len(manifest.get('resident_seats_target', {}).get('seats', []))} seats")
    print(f"  Existing gold banks:   {len(manifest.get('existing_gold_banks', []))} banks wired")
    print(f"Fixtures: {FIXTURES_PATH} ({fixtures['fixture_count']} frozen fixtures)")
    print(f"  By archetype:          {fixtures.get('archetype_fixture_counts', {})}")
    print(f"  By regime:             {fixtures.get('regime_fixture_counts', {})}")
    print(f"Live Du activity check:  {len(active_du)} signal(s) -> {'GPU/OLLAMA GATE LOCKED (Du is UP)' if active_du else 'READY'}")


def build_blind_packets(raw_results: list[dict], fixtures: list[dict], seed: int = 42) -> tuple[list[dict], dict]:
    """Create blinded, shuffled, duplicate-controlled, calibration-anchored packets for Phase 3."""
    rng = random.Random(seed)
    by_fix: dict[str, list[dict]] = {}
    for row in raw_results:
        if row.get("ok") and row.get("content") and row.get("run_index", 0) == 0:
            by_fix.setdefault(row["fixture_id"], []).append(row)

    fix_lookup = {f["fixture_id"]: f for f in fixtures}
    packets = []
    secret_key = {}

    for fid, items in by_fix.items():
        fmeta = fix_lookup.get(fid, {})
        candidates = []
        for it in items:
            cid = "cand_" + hashlib.sha1(f"{fid}:{it['model']}:{rng.random()}".encode()).hexdigest()[:8]
            candidates.append({"candidate_id": cid, "output": it["content"]})
            secret_key[cid] = {"fixture_id": fid, "model": it["model"], "kind": "model_run"}

        base_out = fmeta.get("baseline_output")
        if isinstance(base_out, str) and base_out.strip():
            cid = "cand_" + hashlib.sha1(f"{fid}:du_baseline:{rng.random()}".encode()).hexdigest()[:8]
            candidates.append({"candidate_id": cid, "output": base_out})
            secret_key[cid] = {"fixture_id": fid, "model": "DU_BASELINE_ANCHOR", "kind": "calibration_anchor"}

        if items and len(packets) % 3 == 0:
            dup_src = rng.choice(items)
            cid = "cand_" + hashlib.sha1(f"{fid}:dup:{rng.random()}".encode()).hexdigest()[:8]
            candidates.append({"candidate_id": cid, "output": dup_src["content"]})
            secret_key[cid] = {"fixture_id": fid, "model": dup_src["model"], "kind": "duplicate_control"}

        rng.shuffle(candidates)
        packets.append({
            "fixture_id": fid,
            "prompt_id": fmeta.get("prompt_id"),
            "archetype": fmeta.get("archetype"),
            "regime": fmeta.get("regime"),
            "user_prompt_preview": (fmeta.get("user_prompt") or "")[:600],
            "candidates": candidates,
        })

    return packets, secret_key


def wait_for_llama_server(base_url: str, timeout_s: float = 90.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def run_phase(
    phase: str,
    base_url: str,
    repeats: int = 1,
    model_filter: str | None = None,
    backend_filter: str = "ollama",
    threads: int = 8,
) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    fixtures_pack = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    model_specs = manifest.get("candidate_models_primary") or []

    if backend_filter == "ollama":
        model_specs = [m for m in model_specs if m.get("backend", "ollama") == "ollama"]
    elif backend_filter == "llama_server":
        model_specs = [m for m in model_specs if m.get("backend", "").startswith("llama_server")]

    if model_filter:
        tokens = [t.strip().lower() for t in model_filter.split(",") if t.strip()]
        model_specs = [m for m in model_specs if any(t in m["model"].lower() for t in tokens)]

    all_fixtures = fixtures_pack["fixtures"]

    if phase == "smoke":
        selected = [f for f in all_fixtures if f["fixture_id"] in ("P-0001_fix_1", "P-0007_fix_1")]
        repeats = 2
    elif phase == "automated":
        selected = [
            f for f in all_fixtures
            if f["regime"] != "stage_b_deep_bank"
            and f["archetype"] in ("A1_classifiers_routers", "A2_judges_evaluators", "A3_distillation_closure", "A6_drills_knowledge")
        ]
    elif phase == "stage-b":
        selected = [
            f for f in all_fixtures
            if f["regime"] == "stage_b_deep_bank"
        ]
    else:  # blind-packets
        selected = [
            f for f in all_fixtures
            if f["regime"] != "stage_b_deep_bank"
            and f["archetype"] in ("A4_reasoning_synthesis", "A5_voice_imagination_prose", "A3_distillation_closure")
        ]

    out_file = OUT_DIR / f"results_{phase}.json"
    results: list[dict] = []
    completed_keys: set[tuple[str, str, int]] = set()
    if out_file.exists():
        try:
            results = json.loads(out_file.read_text(encoding="utf-8"))
            for r in results:
                if r.get("ok"):
                    completed_keys.add((r["model"], r["fixture_id"], int(r.get("run_index", 0))))
        except Exception:
            results = []

    for mspec in model_specs:
        model = mspec["model"]
        backend = mspec.get("backend", "ollama")
        pinned_ctx = int(mspec.get("pinned_num_ctx", 8192))
        pending_for_model = [
            (fix, r_idx)
            for fix in selected
            for r_idx in range(repeats)
            if (model, fix["fixture_id"], r_idx) not in completed_keys
        ]
        if not pending_for_model:
            print(f"\n--- Model: {model} (already complete for phase {phase}, skipping) ---")
            continue

        print(f"\n--- Model: {model} (backend={backend}, num_ctx={pinned_ctx}, calls={len(pending_for_model)}) ---", flush=True)
        proc = None
        target_url = base_url
        try:
            if backend.startswith("llama_server"):
                bin_path = mspec.get("binary_path", "")
                mod_path = mspec.get("model_path", "")
                if not os.path.exists(bin_path) or not os.path.exists(mod_path):
                    print(f"  [!] Missing binary or GGUF for {model}: {bin_path} / {mod_path}")
                    continue
                target_url = "http://127.0.0.1:11455"
                cmd = [
                    bin_path, "-m", mod_path, "--port", "11455",
                    "-c", str(pinned_ctx), "-ngl", "0", "-t", str(threads),
                ]
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if not wait_for_llama_server(target_url, timeout_s=90.0):
                    print(f"  [!] llama-server failed to become ready on {target_url}")
                    continue

            for fix, run_idx in pending_for_model:
                expect_json = fix["archetype"] in ("A1_classifiers_routers", "A2_judges_evaluators", "A6_drills_knowledge")
                sp = fix.get("system_prompt") or "You are Du's cognitive station. Follow the prompt instructions carefully."
                up = fix.get("user_prompt") or ""
                res = call_endpoint(
                    base_url=target_url,
                    model=model,
                    backend=backend,
                    system_prompt=sp,
                    user_prompt=up,
                    expect_json=expect_json,
                    num_ctx=pinned_ctx,
                    think=False,
                    reasoning_effort="none",
                )
                res.update({
                    "phase": phase,
                    "model": model,
                    "fixture_id": fix["fixture_id"],
                    "prompt_id": fix["prompt_id"],
                    "archetype": fix["archetype"],
                    "regime": fix["regime"],
                    "gold_label": fix.get("gold_label"),
                    "run_index": run_idx,
                })
                results.append(res)
                vram_pct = (res.get("placement") or {}).get("vram_pct", 0.0)
                print(
                    f"  [{fix['fixture_id']} r{run_idx}] ok={res.get('ok')} wall={res.get('wall_s')}s "
                    f"load={res.get('load_s', 0)}s gen={res.get('gen_tok_s', 0)}t/s json={res.get('valid_json')} vram={vram_pct}%",
                    flush=True,
                )

            # Save checkpoint after each model
            out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
            if backend == "ollama":
                unload_ollama_model(target_url, model)
        finally:
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except Exception:
                    proc.kill()

    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved {len(results)} total results to {out_file}", flush=True)

    if phase in ("blind-packets", "stage-b"):
        packets, secret_key = build_blind_packets(results, all_fixtures)
        packets_file = OUT_DIR / f"blind_packets_{phase}.json"
        key_file = OUT_DIR / f"blind_key_{phase}_DO_NOT_READ_UNTIL_SCORED.json"
        packets_file.write_text(json.dumps(packets, indent=2), encoding="utf-8")
        key_file.write_text(json.dumps(secret_key, indent=2), encoding="utf-8")
        print(f"Exported {len(packets)} blinded evaluation packets to {packets_file}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Du Prompt-to-Model Benchmark Suite")
    parser.add_argument("--status", action="store_true", help="Print static Phase 0 readiness (safe while Du is up)")
    parser.add_argument("--phase", choices=["smoke", "automated", "blind-packets", "stage-b"], help="Execution phase")
    parser.add_argument("--confirm-du-down", action="store_true", help="Explicit confirmation that Du is stopped")
    parser.add_argument("--cpu-spare-port", action="store_true", help="Allow CPU-only llama-server run on a non-Du spare port (e.g. :11455)")
    parser.add_argument("--base-url", default="http://127.0.0.1:11433", help="Target base URL")
    parser.add_argument("--backend", choices=["ollama", "llama_server", "all"], default="ollama", help="Backend filter")
    parser.add_argument("--model-filter", default=None, help="Comma-separated substring filter on model names")
    parser.add_argument("--repeats", type=int, default=2, help="Number of independent runs per (model, fixture)")
    parser.add_argument("--threads", type=int, default=8, help="Thread cap for standalone llama-server CPU runs")
    args = parser.parse_args()

    if args.status or not args.phase:
        print_status()
        return

    assert_execution_permitted(args.confirm_du_down, args.cpu_spare_port, args.base_url)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_phase(
        args.phase,
        args.base_url,
        repeats=args.repeats,
        model_filter=args.model_filter,
        backend_filter=args.backend,
        threads=args.threads,
    )


if __name__ == "__main__":
    main()
