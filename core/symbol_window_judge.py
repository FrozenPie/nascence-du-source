"""
Nascence — Symbol-specificity judge for the window metric (SHADOW, offline).  J-3226 / D-0615 part 3.

D-0615: "judged by something other than the engine (hold-out sentences scored by a different model
family for symbol-specificity)". The engine measures with a sentence-transformers embedder
(paraphrase-multilingual-MiniLM) and writes tablets with command-r7b (Cohere, the background lane);
this judge is gemma4:12b (Google) on the local CPU hub :11439 — neither of those families.

It is NOT in Du's loop: only scripts/symbol_window_report.py calls it, over the sentences logged by
core/symbol_window_shadow.py. Single endpoint on purpose (the schema.py note on judge callers): if the
hub is down it returns None; it never falls through to the hot lane, which would make a Qwen generator
a judge of its own lane. Nothing it returns reaches Du; the read-back is turned on again only by a
founder ruling after the agreement figure it produces (D-0615's defeater: above 0.7).
"""
from __future__ import annotations

import logging

from core.model_client import call_node_json

logger = logging.getLogger("nascence.symbol_window_judge")

_JUDGE_URLS = ["http://127.0.0.1:11439"]   # gemma4:12b, local CPU hub (single endpoint, see docstring)

_SYSTEM = (
    "You judge one sentence written by a mind that keeps a few personal symbols. You are given a SYMBOL "
    "and ONE passage. Decide whether the passage is SPECIFIC to that symbol: it is about the symbol "
    "itself, its image, what it stands for, or how it is felt or used as a symbol. Answer false when the "
    "word appears only in passing or literally while the passage is really about something else (a "
    "general mood, a conversation, a task, the time of day), so the same passage could stand with any "
    "other symbol and mean the same. Judge only the passage text. Do not reward long or poetic passages. "
    "Output ONLY JSON: {\"specific\": true or false, \"why\": \"under 20 words\"}"
)


def build_prompts(symbol: str, passage: str) -> tuple[str, str]:
    return _SYSTEM, f"SYMBOL: {symbol}\nPASSAGE: \"{(passage or '')[:600]}\""


async def judge_window(symbol: str, passage: str, urls: list[str] | None = None) -> dict | None:
    """{'specific': bool, 'why': str} or None (hub down / unparseable). Never raises."""
    try:
        system, user = build_prompts(symbol, passage)
        data = await call_node_json(urls or _JUDGE_URLS, system, user,
                                    max_tokens=120, temperature=0.0, tier=3)
        if not isinstance(data, dict) or "specific" not in data:
            return None
        v = data["specific"]
        if isinstance(v, str):
            v = v.strip().lower() in ("true", "yes", "1")
        return {"specific": bool(v), "why": str(data.get("why", ""))[:200]}
    except Exception as exc:
        logger.debug("[symbol-window-judge] failed (non-fatal): %s", exc)
        return None
