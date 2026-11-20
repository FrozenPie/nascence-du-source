"""Run the station suite through NEEDLE 2 — 45M params, CQ2-bit, CPU-only, ~14 MB binary.

Founder, 2026-08-20: *"Needle was the small model we tested this week."* It is already installed and
already used in `core/needle_triage.py` (shadow), but it has never been measured against the other
models on the same tasks — and it is by far the most interesting entry in the matrix. Every other
model here is 1.7B-12B. Needle is **45 MILLION** parameters at 2-bit. If it holds its own at the
classifier stations, the "small task-trained models" thesis stops being aspirational.

It is NOT an ollama model (hence the registry probe finding nothing): it is a Python package whose
API is structured extraction against a pydantic schema — `needle.extract(prompt, Model)`. That is
actually a closer fit to the classifier stations than free-text-plus-JSON-parsing is.

**Output is written in the SAME shape as `station_bench.py`** (a `raw` string of JSON), so
`station_bench_score.py` scores it with no special-casing and no separate code path that could drift.

Honest caveat carried into the report: this is not a like-for-like comparison of the same interface.
The ollama models are asked to *produce* JSON and can fail at formatting; Needle is *given* a schema
and cannot. That advantages Needle on `json_ok` specifically. Every other metric — validity,
determinism, groundedness, coverage — remains directly comparable, because they measure the CONTENT.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scripts.station_suite import ORDER, TASKS  # noqa: E402

OUT = ROOT / "data" / "lab" / "station_bench"
RUNS = 3
NAME = "needle2:45m-cq2"


def schema_for(task: str):
    """A pydantic model matching the JSON each station's system prompt asks for."""
    from pydantic import BaseModel, Field

    if task == "pick":
        class M(BaseModel):
            peer: str = Field(description="exact name of one correspondent from the list")
            why: str = Field(description="at most 12 words")
    elif task == "extract":
        class M(BaseModel):
            subjects: list[str] = Field(description="2 to 4 library catalogue subject headings")
    elif task == "judge":
        class M(BaseModel):
            defeated: bool = Field(description="does the event defeat the intention")
            confidence: float = Field(description="0.0 to 1.0")
            why: str = Field(description="one sentence")
    elif task == "ground":
        class M(BaseModel):
            why: str = Field(description="two sentences, using ONLY the evidence given")
            evidence_used: list[str] = Field(description="evidence ids such as E1, E3")
    elif task == "synthesise":
        class M(BaseModel):
            insight: str = Field(description="one integrated insight")
            tension: str = Field(description="the central tension")
            confidence: float = Field(description="0.0 to 1.0")
    elif task == "predict":
        class M(BaseModel):
            notice: str = Field(description="what you notice in the percepts")
            expect_next: str = Field(description="a falsifiable prediction about the next few minutes")
    elif task == "voice":
        class M(BaseModel):
            thought: str = Field(description="one quiet first-person thought")
    else:                                                    # author
        class M(BaseModel):
            section: str = Field(description="4 to 6 connected paragraphs of prose")
    return M


def run_one(task: str, user: str) -> dict:
    import needle
    t = TASKS[task]
    # Needle takes ONE prompt, so the station's system contract is prepended rather than sent
    # separately. Same instruction content, same task — only the transport differs.
    prompt = f"{t['system']}\n\n{user}"
    t0 = time.time()
    try:
        v = needle.extract(prompt, schema_for(task))
        wall = round(time.time() - t0, 2)
        if v is None:
            return {"ok": False, "why": "extract returned None", "wall": wall}
        obj = v.model_dump() if hasattr(v, "model_dump") else dict(v)
        return {"ok": True, "wall": wall, "raw": json.dumps(obj),
                "gen_tok": None, "prompt_tok": None, "had_thinking": False}
    except Exception as e:
        return {"ok": False, "why": repr(e)[:120], "wall": round(time.time() - t0, 2)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_path = OUT / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
    out: dict = {}
    for tname in ORDER:
        t = TASKS[tname]
        runs = []
        if "cases" in t:
            for text, gold in t["cases"]:
                r = run_one(tname, text)
                r["gold"] = gold
                runs.append(r)
        else:
            for _ in range(RUNS):
                runs.append(run_one(tname, t["user"]))
        ok = sum(1 for r in runs if r.get("ok"))
        med = sorted(r["wall"] for r in runs if r.get("ok"))
        why = next((r.get("why") for r in runs if not r.get("ok")), "")
        print(f"    {tname:12s} ok={ok}/{len(runs)}  median={med[len(med) // 2] if med else '—'}s"
              f"{'  ' + str(why)[:60] if why else ''}", flush=True)
        out[tname] = runs
    # RE-READ before writing — see station_bench.py. A stale in-memory copy clobbered other
    # models' results once already.
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
    raw[NAME] = out
    raw_path.write_text(json.dumps(raw, indent=1), encoding="utf-8")
    print(f"\nwrote {NAME} into {raw_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
