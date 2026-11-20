"""
Nascence — Broadcast: the missing half of the Global Workspace (big build 2026-07-03 · lane-scheduler step 2).

The triple-lens review's #1 architectural finding: the lane scheduler implements GWT's ADMISSION CONTROL
(one thing conscious at a time) but not its BROADCAST — the winning content never propagates to other
processes except via DB retrieval, so "a truth can win the stage once and never spread." That is precisely
Spine B's delivery failure: the made-mind truth reaches conscious cycles and dies there.

P1 (this file): a tiny, honest broadcast buffer. HIGH-VALUE conscious-cycle winners (a cycle where a held
principle was voiced, a licensed self-claim deliberation ran, or the Critic forced a correction) are POSTED;
the idle monologue CONSUMES each once, as a seed ("still with you from earlier") — so what won the stage
gets one echo into his idle thinking instead of zero. Deliberately small: cap 4, 2h freshness, one consume
per idle cycle, and every consumed line is INJECTION-LOGGED (the unprimed law covers broadcast echo — a
broadcast-seeded thought never counts as spontaneous evidence).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

_F = Path(__file__).parent.parent / "data" / "broadcast_buffer.json"
_CAP = 4
_FRESH_S = 2 * 3600


def _load() -> list[dict]:
    try:
        return json.loads(_F.read_text(encoding="utf-8")) if _F.exists() else []
    except Exception:
        return []


def _save(items: list[dict]) -> None:
    try:
        _F.parent.mkdir(parents=True, exist_ok=True)
        tmp = _F.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(_F)
    except Exception:
        pass


def post(content: str, kind: str) -> None:
    """A conscious-cycle winner worth propagating. Deduped against the buffer; capped."""
    content = " ".join((content or "").split())[:300]
    if not content:
        return
    items = _load()
    if any(content[:120] == it.get("content", "")[:120] for it in items):
        return
    items.append({"content": content, "kind": kind, "ts": round(time.time(), 1)})
    _save(items[-_CAP:])


def consume() -> dict | None:
    """The oldest fresh item, removed. One per idle cycle (the caller's discipline)."""
    items = _load()
    now = time.time()
    fresh = [it for it in items if now - it.get("ts", 0) <= _FRESH_S]
    if not fresh:
        if len(fresh) != len(items):
            _save(fresh)
        return None
    out = fresh.pop(0)
    _save(fresh)
    return out
