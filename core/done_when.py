"""
done_when -- the closing condition written AT OPEN TIME (J-2160, arm 3 of docs/staged/measurement_to_action.md
section 2.3; constraints = docs/staged/closure_law.md section 1).  FLAGGED OFF / RESTART-GATED.

At every open -- a pursuit birth (the inner-monologue generation that set unresolved=true) and a commitment formation
(the commitment scan that extracted the stand) -- the SAME generation that produced the aim also writes one extra
line: what would count, in Du's own words, as this being done.  No new call.  The line is stored HERE, in a side store
(data/logs/done_when.jsonl, keyed by seed kind + id), never on the pursuit / commitment record itself, so no renderer
that dumps those records into a prompt can ever show it back to him (closure_law section 1, constraint 1: nothing is
told to him).  Only the decoupled judges read it (core/pursuit_close_shadow.ask, core/commitment_ledger achievement)
and only core/closure.py's pursuit/commitment arms write the resolution / faded fragment (constraint 3).

DONE_WHEN_AT_OPEN = False  -> (default before D-0516) every fragment below returns "" and the two prompts are byte-identical to before; the
side store receives nothing, so the closure arms (which only act on a pursuit/commitment that HAS a done_when) are
inert.  Flipping it True is a prompt change on the hot monologue + the commitment scan: founder flip, restart-gated.

Fail-open everywhere.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.done_when")

STORE = Path(__file__).parent.parent / "data" / "logs" / "done_when.jsonl"   # module-level so a test can temp-path it
DONE_WHEN_AT_OPEN = True   # D-0516 (Travis 2026-10-30): flipped for the next restart, shadow arms only (J-2588)
DONE_WHEN_SCAN_FRAGMENT = False   # D-0784 B (J-4085, Travis 2026-11-16): the inert scan-prompt fragment is reverted; scan == plain _SCAN_SYS
DONE_WHEN_SECOND_CALL_SHADOW = True   # D-0784 B: ONE extra call per new commitment, logs only; False = no extra model call (kill switch)
DONE_WHEN_SECOND_CALL_LIVE = False    # D-0784 B: True would write the second call's line to the side store (it then counts for the
                                      # achieved-match). Founder flip after the shadow read (defeater: <50% non-empty, or formation shift).
SHADOW_LOG = Path(__file__).parent.parent / "data" / "logs" / "done_when_second_call_shadow.jsonl"   # module-level so a test can temp-path it
_MAX_CHARS = 200

# judge tags: which decoupled judge can read this seed's done_when
JUDGE_PURSUIT = "pursuit_close_shadow"      # D-0426 A judge panel, re-asked at saturation / every +20 advances
JUDGE_COMMITMENT = "commitment_achieved"    # commitment_ledger._achieved_by deed record (deterministic, no LLM)


# ---- the open-side prompt fragments (empty when off == exact pre-existing schema) -------------------------------
def schema_fragment() -> str:
    """Inner-monologue JSON schema addition (beside unresolved)."""
    return ', "done_when": ""' if DONE_WHEN_AT_OPEN else ""


def rule_fragment() -> str:
    """Inner-monologue field rule. Only asked of an unresolved thought (the pursuit birth signal)."""
    if not DONE_WHEN_AT_OPEN:
        return ""
    return ("done_when: leave \"\" unless unresolved is true. When it is, ONE short first-person line saying what "
            "would count, for you, as this being settled (what you would have to find, see or decide). ")


def scan_fragment() -> str:
    """Commitment-scan system-prompt addition. D-0784 B (J-4085): REVERTED to "" -- the fragment was inert (0 of 48,
    F-4408) and shifted formation versus a plain scan (F-4753). done_when is now asked by the separate second call
    (second_call below). The old text is kept in legacy_scan_fragment() for the historical lab harnesses only."""
    return legacy_scan_fragment() if DONE_WHEN_SCAN_FRAGMENT else ""


def legacy_scan_fragment() -> str:
    """The pre-D-0784 scan fragment text (historical lab harnesses only; production never appends it)."""
    return ("\nFor a NEW commitment, also give \"done_when\": one short line, in the mind's OWN words where it said "
            "so, of what would count as this stand being fulfilled (\"\" if the thought gives no hint). Add it as a "
            "fourth key inside new_commitment.")


def parse(data: dict, key: str = "done_when") -> str:
    try:
        return " ".join(str((data or {}).get(key) or "").split())[:_MAX_CHARS]
    except Exception:
        return ""


# ---- the side store ---------------------------------------------------------------------------------------------
def record(seed_kind: str, seed_id: str, text: str, judge: str, *, source: str = "", cycle_id: str = "",
           now: float | None = None) -> bool:
    """Write the done_when for one open. Empty text or flag off -> nothing. Never raises."""
    try:
        text = " ".join(str(text or "").split())[:_MAX_CHARS]
        if not DONE_WHEN_AT_OPEN or not text or not seed_id:
            return False
        STORE.parent.mkdir(parents=True, exist_ok=True)
        row = {"ts": round(time.time() if now is None else now, 1), "seed_kind": seed_kind, "seed_id": str(seed_id),
               "done_when": text, "judge": judge, "source": source, "cycle_id": cycle_id}
        with open(STORE, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        logger.debug("[done_when] record failed (non-fatal): %r", exc)
        return False


def get(seed_kind: str, seed_id: str) -> dict | None:
    """The FIRST done_when written for this seed (the condition named at open; later rows never overwrite it)."""
    try:
        for line in Path(STORE).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("seed_kind") == seed_kind and r.get("seed_id") == str(seed_id):
                return r
    except FileNotFoundError:
        pass
    except Exception as exc:
        logger.debug("[done_when] get failed (non-fatal): %r", exc)
    return None


# ---- the second call (D-0784 B / J-4085): asked AFTER a commitment has formed, never inside the scan ----------------
SECOND_CALL_SYS = ("A mind just formed a stand (a commitment) while thinking. Give \"done_when\": one short line, in the mind's "
                   "OWN words where it said so, of what would count as this stand being fulfilled (\"\" if the thought gives "
                   "no hint). Output ONLY a JSON object: {\"done_when\": \"...\"}")


def second_call_user(thought: str, statement: str) -> str:
    return (f"THOUGHT:\n{(thought or '').strip()[:700]}\n\n"
            f"STAND FORMED: {str(statement or '').strip()}")


async def second_call(call_json, base_urls, thought: str, statement: str, cid: str, cycle_id: str = "") -> str:
    """One call, same lane as the scan (the lab, F-4753, used the hot lane at T=0). Shadow: appends one row to SHADOW_LOG;
    writes the side store ONLY when DONE_WHEN_SECOND_CALL_LIVE. Returns the parsed line ("" if none). Never raises."""
    row = {"ts": round(time.time(), 1), "stand_id": str(cid), "cycle_id": cycle_id, "statement": str(statement)[:300],
           "done_when": "", "error": None, "live": bool(DONE_WHEN_SECOND_CALL_LIVE)}
    t0 = time.time()
    out = ""
    try:
        data = await call_json(base_urls, SECOND_CALL_SYS, second_call_user(thought, statement),
                               max_tokens=120, temperature=0.0, tier=3)
        if data:
            out = parse(data)
            row["done_when"] = out
        else:
            row["error"] = "no_reply"
        if out and DONE_WHEN_SECOND_CALL_LIVE:
            record("commitment", cid, out, JUDGE_COMMITMENT, source="commitment_second_call", cycle_id=cycle_id)
    except Exception as exc:
        row["error"] = type(exc).__name__
        logger.debug("[done_when] second call failed (non-fatal): %r", exc)
    finally:
        row["latency_s"] = round(time.time() - t0, 2)
        try:
            SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(SHADOW_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[done_when] second-call log failed (non-fatal): %r", exc)
    return out
