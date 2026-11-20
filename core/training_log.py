"""
Nascence — Training Log
Captures (input → output) pairs from every node call, so the prompt-engineered
nodes act as teachers generating an in-domain distillation dataset for future
specialist models (see docs/RESEARCH_specialists.md).

One JSONL file per node: data/training/<node_id>.jsonl
Each line is one teacher example. Logging is best-effort — a logging failure
must NEVER break a thought cycle.

Toggle with the NASCENCE_TRAINING_LOG env var ("0" disables). Default: on.
"""

from __future__ import annotations
import os
import json
import time
import logging
from pathlib import Path

from . import profile

logger = logging.getLogger("nascence.training_log")

_LOG_DIR = Path(__file__).parent.parent / "data" / "training"
_ENABLED = os.environ.get("NASCENCE_TRAINING_LOG", "1") != "0"
_dir_ready = False


def _ensure_dir() -> None:
    global _dir_ready
    if not _dir_ready:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        _dir_ready = True


def log_example(
    node_id: str,
    user_prompt: str,
    output: dict,
    *,
    system_prompt: str = "",
    cycle_id: str = "",
    raw_input: str = "",
    input_type: str = "",
    hedged: bool = False,
    think: bool = False,
) -> None:
    """
    Append one teacher example for `node_id`. Best-effort; swallows all errors.

    The student model for a node is trained to map `user_prompt` (exactly what the
    teacher conditioned on) → `output` (the teacher's parsed result). `raw_input`
    and the perception-derived context live inside `user_prompt`; they are also
    surfaced separately for the embedding-regressor path (Emotion/Salience).
    """
    if not _ENABLED:
        return
    try:
        # J-1816 / F-2428 -- the write fence (D-0179): resolve the per-node file through profile.guard_path BEFORE any I/O
        # (before _ensure_dir()'s mkdir and before the open). INSIDE this existing fail-open try on purpose: logging is
        # documented best-effort and node_base calls it after every successful LLM call, so a refusal
        # (profile.NonLiveWriteError) must never break a cycle -- guard_path logs one warning per path and the except
        # below swallows it (debug line carries the refusal text). A LIVE process gets the same path back: byte-identical.
        path = profile.guard_path(_LOG_DIR / f"{node_id}.jsonl")
        _ensure_dir()
        record = {
            "ts":          time.time(),
            "cycle_id":    cycle_id,
            "node":        node_id,
            "input_type":  input_type,
            "raw_input":   raw_input,
            "user_prompt": user_prompt,
            "output":      output,
            "hedged":      hedged,
            # system_prompt is constant per node version; log it so a dataset is
            # self-describing even if the node's prompt later changes.
            "system_prompt": system_prompt,
        }
        if think:
            record["think"] = True   # J-2860: System-2 licensed call; absent = think off (licensed vs plain comparable)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # never break a cycle over logging
        logger.debug("training log write failed for %s: %s", node_id, exc)
