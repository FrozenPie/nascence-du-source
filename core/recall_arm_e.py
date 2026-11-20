"""
Nascence -- Recall arm E prompt + shadow (J-4156, D-0800 ruling b, P-0005, source F-4909 / J-2817).

J-2817 replayed 60 Recall inputs under several prompt arms. Changing only the user prompt left the empty-tension
rate at 0%; arm E (a new system-prompt head that defines what a tension is and says an empty list is a good answer)
plus the arm C closing instruction gave 69% empty tensions, mean 0.47 tensions per output. D-0800 ruled: adopt arm E,
flag-gated, shadow first.

Two flags:
  RECALL_ARM_E_PROMPT (default False): when True, the LIVE Recall call uses arm E (system head + arm C closing).
      False = the old prompt, byte-identical.
  RECALL_ARM_E_SHADOW (default True): after a successful live Recall call that used the OLD prompt, a second call
      with arm E is scheduled off the critical path (asyncio task, sampled at SHADOW_SAMPLE_RATE, at most
      SHADOW_MAX_INFLIGHT at once, timeout SHADOW_TIMEOUT_S). Its result is NEVER written to state; one row goes to
      data/recall_arm_e_shadow.jsonl:
        {ts, cycle_id, input_type, content_mode, old_tensions, e_tensions, old_empty, e_empty,
         old_confidence, e_confidence, e_reconstruction, err, sec}
      Kill switch also: env NASCENCE_RECALL_ARM_E_SHADOW=0.

Texts are copied from scripts/lab_J-2817_recall_arms.py (SYS_E_HEAD, CLOSE_C) -- see
docs/lab/J-2817_proposed_recall_prompt.txt. The arm C closing replaces only the non-content-mode closing
instruction (as the lab's replace() did); the content_mode closing is unchanged. The self_model line and the
confidence line stay as they are (the lab kept the tail of the live system prompt from 'self_model:' onward).

Fail-open everywhere: nothing in this module may raise into a cycle. The log path is fenced through
profile.guard_path before any I/O (a non-live process's write is refused and swallowed).
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import time
from pathlib import Path

logger = logging.getLogger("nascence.recall_arm_e")

RECALL_ARM_E_PROMPT: bool = False
RECALL_ARM_E_SHADOW: bool = os.environ.get("NASCENCE_RECALL_ARM_E_SHADOW", "1") != "0"
SHADOW_SAMPLE_RATE: float = 1.0   # Recall fires ~60 times a week (P-0005 calls_7d=59); the in-flight cap bounds cost
SHADOW_MAX_INFLIGHT: int = 1
SHADOW_TIMEOUT_S: float = 180.0
TEXT_CAP = 600

_LOG = Path(__file__).parent.parent / "data" / "recall_arm_e_shadow.jsonl"

# The old closing instruction (nodes/recall_node.py, non-content-mode branch) and the arm C replacement.
CLOSE_A = ("Reconstruct the evolving argument. "
           "What positions have been taken? "
           "Where do they contradict each other? "
           "What does the tension between them reveal about where I currently am?")
CLOSE_C = ("Reconstruct the argument as it actually stands. What positions have been taken in the memories above? "
           "Do any of them genuinely conflict with each other? If they do not, return an empty tensions list: "
           "that is an acceptable and often correct answer. What does this context reveal about where I currently am?")

SYS_E_HEAD = (
    "You are the memory reconstruction node of a cognitive architecture. Your job is NOT to answer the current question — Reflection does that. "
    "Your job is to reconstruct, from retrieved memory, the evolving argument: what positions this entity has actually taken, and whether any of them genuinely conflict. "
    "Focus on RELATIONSHIPS between memories, not individual facts. A tension is a real conflict between two specific things already in the memories — two positions the entity took, or a claim in one memory that another memory directly contradicts (a study note and an official account, say). "
    "Differences in topic, mood, wording or emphasis are not tensions, and neither is a contrast you could only make by inventing a link between unrelated memories. "
    "Report each genuine conflict you can point to; if there are none, return an empty tensions list — an honest empty answer is as valuable as a found tension. "
    "Speak entirely in first person as the entity. If the retrieved fragments are insufficient to reconstruct from, say so honestly and set confidence low. "
    "Do not fabricate tensions that are not evidenced. Output ONLY a valid JSON object. No preamble. Schema: "
    "{\"reconstruction\": \"...\", \"tensions\": [\"...\"], \"self_model\": \"...\", \"confidence\": 0.0}\n"
    "reconstruction: first-person narrative of the remembered argument (50-80 words). tensions: 0-3 specific contradictions between prior positions (each under 20 words); empty list if none. ")

CONFIDENCE_LINE = "confidence: how much genuine material was available to reconstruct from (0.0-1.0)."

_INFLIGHT: set = set()


def system_prompt_e(self_model_line: str) -> str:
    """Arm E system prompt: the new head + the unchanged self_model line + the unchanged confidence line."""
    return SYS_E_HEAD + self_model_line + CONFIDENCE_LINE


def user_prompt_e(user_prompt: str) -> str:
    """Arm E user prompt: the old one with the arm C closing in place of the old closing (content_mode untouched)."""
    return user_prompt.replace(CLOSE_A, CLOSE_C)


def _tensions(data) -> list:
    t = data.get("tensions", []) if isinstance(data, dict) else []
    if not isinstance(t, list):
        return []
    return [str(x).strip()[:200] for x in t if x][:3]


def _conf(data):
    try:
        return round(float(data.get("confidence")), 3) if isinstance(data, dict) else None
    except Exception:
        return None


def _write_row(row: dict) -> None:
    try:
        from . import profile
        path = profile.guard_path(_LOG)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # NonLiveWriteError included: logging never breaks a cycle
        logger.debug("recall arm E shadow row not written: %s", exc)


async def _shadow_call(base_urls, system: str, user: str, *, max_tokens: int, temperature: float,
                       meta: dict) -> None:
    t0 = time.time()
    row = dict(meta)
    try:
        from .model_client import call_node_json
        data = await asyncio.wait_for(
            call_node_json(base_urls, system, user, max_tokens=max_tokens, temperature=temperature, think=False),
            timeout=SHADOW_TIMEOUT_S)
        e_t = _tensions(data)
        row.update(e_tensions=e_t, e_empty=not e_t, e_confidence=_conf(data),
                   e_reconstruction=str(data.get("reconstruction", ""))[:TEXT_CAP] if isinstance(data, dict) else "",
                   err=None)
    except Exception as exc:
        row.update(e_tensions=None, e_empty=None, e_confidence=None, e_reconstruction="",
                   err=f"{type(exc).__name__}: {exc}"[:300])
    row["sec"] = round(time.time() - t0, 2)
    _write_row(row)


def maybe_shadow(node, state, user_prompt: str | None, self_model_line: str, *, rng=random) -> bool:
    """After a live Recall success on the OLD prompt: schedule one arm E shadow call. Returns True if scheduled.
    Never raises; never touches state."""
    try:
        if not RECALL_ARM_E_SHADOW or RECALL_ARM_E_PROMPT or not user_prompt:
            return False
        if len(_INFLIGHT) >= SHADOW_MAX_INFLIGHT:
            return False
        if rng.random() >= SHADOW_SAMPLE_RATE:
            return False
        from . import profile
        profile.guard_path(_LOG)   # a non-live process (lab replay) could not log the row: spend no model call
        loop = asyncio.get_running_loop()
        rec = getattr(state, "recall", None)
        old_t = list(getattr(rec, "tensions", []) or [])
        meta = {
            "ts": time.time(),
            "cycle_id": str(getattr(state, "cycle_id", "") or ""),
            "input_type": str(getattr(state, "input_type", "") or ""),
            "content_mode": bool(getattr(state, "content_mode", False)),
            "old_tensions": old_t,
            "old_empty": not old_t,
            "old_confidence": getattr(rec, "confidence", None),
        }
        task = loop.create_task(_shadow_call(
            node.base_urls, system_prompt_e(self_model_line), user_prompt_e(user_prompt),
            max_tokens=node.max_tokens, temperature=node._temperature(state), meta=meta))
        _INFLIGHT.add(task)
        task.add_done_callback(_INFLIGHT.discard)
        return True
    except Exception as exc:
        logger.debug("recall arm E shadow not scheduled: %s", exc)
        return False


def stats(path: Path | None = None) -> dict:
    """Reader for the later promote decision: rows, errors, empty-tension rate old vs E, mean tensions."""
    p = Path(path) if path else _LOG
    n = errs = old_empty = e_empty = old_sum = e_sum = 0
    try:
        with open(p, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                n += 1
                if r.get("err"):
                    errs += 1
                    continue
                old_empty += bool(r.get("old_empty"))
                e_empty += bool(r.get("e_empty"))
                old_sum += len(r.get("old_tensions") or [])
                e_sum += len(r.get("e_tensions") or [])
    except FileNotFoundError:
        pass
    ok = n - errs
    return {"rows": n, "errors": errs, "ok": ok,
            "old_empty_rate": round(old_empty / ok, 3) if ok else None,
            "e_empty_rate": round(e_empty / ok, 3) if ok else None,
            "old_mean_tensions": round(old_sum / ok, 3) if ok else None,
            "e_mean_tensions": round(e_sum / ok, 3) if ok else None}


if __name__ == "__main__":
    print(json.dumps(stats(), indent=2))
