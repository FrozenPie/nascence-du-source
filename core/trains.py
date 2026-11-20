"""
Nascence — the TRAIN REGISTRY (step 1 of the split/merge design, 2026-08-22).
=============================================================================
Founder, same evening: "Trains should be logged with an ID so there can be multiple 'thoughts' going
at once but still being able to know what cargo belongs to what." And the deeper reason: "the reason
we were looking at a transport manager was exactly this — if there are multiple trains, the LLMs and
factories would need to be able to tell whose cargo was whose."

Before this file there was NO train identity anywhere in the codebase: the Idle Line's train was five
scalar attributes on InnerMonologueNode (_train_len / _thread / _state / _ledger / _vecs), so exactly one
train could exist, and train_state_log.jsonl rows carried no id — two trains' steps would have been
indistinguishable. This registry is the shared key that lane 2, the couriers, and the (planned, unbuilt)
Transport Manager can all import. It lives in core/, not inside the monologue node, for that reason.

STEP 1 IS ADDITIVE AND BEHAVIOUR-NEUTRAL. The node keeps its scalars as the hot working state (nothing
that reads them changes); this module only mints ids, mirrors each train's record, and stamps ids into the
logs. Folding the scalars INTO the record — and fork/merge itself — is step 2, shadow-first, after a day
of logs shows an identical train-length distribution to before this landed.

TRAIN CARGO IDS (2026-08-29, D-0082, docs/plans/train_courier_cargo_ids.md): `product_type` is a
second, separate, additive field -- what KIND of thing a train's output actually is (a thought, a
letter, an axiom revision, a judge verdict... see core/cargo_types.py's 19-value taxonomy, derived
from docs/lab/llm_station_cargo_map.md). It does NOT touch or widen `cargo` below -- one train
record, two non-overlapping fields, every train gets a `product_type`, only step-2 fork/merge
trains will ever get a `cargo` bundle.

Record shape (the agreed data model):
  id · parent (set on a fork; None for a root) · role ("main" | "prove" | "disprove") · kind
  ("thought" | "reading") · origin · len · thread · state · ledger · cargo · product_type ·
  opened_ts · closed_ts · close_reason
`cargo` is the one genuinely new field — marked PROTECTED per the GPT auditor review the founder forwarded
(08-22; auditor recommendation, carried pending the founder's step-2 lab read): what a merge hands back is
*what did I find?*, never a transcript. Shape (supersedes the first draft's {claim, from, held, evidence}):
    {"claim": str, "support": [str], "objection": [str],
     "status": "held" | "held_within_scope" | "objected" | "undetermined"}
`held_within_scope` added 2026-09-11 (J-0835, D-0181 — founder ruling 2026-09-09, "recalibrate
disprove"): the disprove branch's own middle case, for when the offered support is real,
independent, and non-circular but only earns a NARROWER claim than the one actually asserted (the
why-text names that narrower claim) — distinct from `objected` (no real/independent support at
all) and from `held` (the support earns the claim as stated, not just a piece of it). Added because
J-0802's own PROVE-side fix (this same decision, its prior ruling) raised the objected share
90.0%->95.0% instead of lowering it — the dominant remaining complaint was scope/generalization
mismatch, not circularity, so folding that case into `objected` was itself flagged as a possible
certainty-machine mirror (kill criterion #2). Computed entirely in `scripts/train_state_invitro.py`
(`_disprove()` / `_SCOPE_SYSTEM`) — this registry module does not validate or interpret any cargo
`status` value, by design (fail-open, per this file's own closing line).
UNDETERMINED is a legal, successful merge outcome (the world's own UNDetermined law, inherited) — a train
may carry *unknown* forward. Without that status the prove/disprove pair becomes a certainty machine.
UNDETERMINED does not mean only "the panel was unavailable" (2026-09-14, J-0986, D-0213): it also now
covers a DISTRUSTED tiebreak-decided vote on the disprove call site (`scripts/train_state_invitro.py`'s
`_disprove()`, both its `_DISPROVE_SYSTEM` and `_SCOPE_SYSTEM` calls) — the deciding judge answered, but
F-1204/F-1271/F-1280/F-1321/F-1357 (this same plan) found that specific judge's vote on this call site
not reliably content-sensitive, so it is not trusted regardless of what it answered. This registry module
does not distinguish the two causes (fail-open, per this file's own closing line) — see `_disprove()`'s
own docstring for which `how`/`scope_how` value on a cargo record marks which.
Cargo may change at LATER stations when a branch meets real evidence (observation, memory, sound, world
change, absence of expected evidence). Empty until fork/merge (step 2) exists.

Fail-open everywhere — a registry fault must never cost a thought.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from core import profile   # J-1821 / F-2453: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "trains_log.jsonl"          # open / close / (later) fork / merge events, one row each

_active: dict[str, dict] = {}              # id -> record, for every train currently open
_last_closed: dict | None = None


def new_id() -> str:
    return "t_" + uuid.uuid4().hex[:6]


def station_for_url(url: str) -> str:
    """Canonical station id from a serving URL — same `station_{port}` convention already used by
    `scripts/build_hud2_transit.py`'s AST-derived stations, so a future HUD1 map and HUD2's existing
    one name the same physical endpoint the same way. Best-effort; '?' on anything unparseable."""
    try:
        port = str(url).rsplit(":", 1)[-1].split("/")[0]
        return f"station_{port}" if port.isdigit() else "?"
    except Exception:
        return "?"


def open(kind: str, origin: str, role: str = "main", parent: str | None = None,
         product_type: str | None = None) -> dict:
    """Mint a train. Returns the record (also held in the registry until close()).

    `product_type` (2026-08-29, D-0082): one of core/cargo_types.py's station-product-type
    constants, naming what KIND of output this train will carry -- additive, optional (None
    when the caller doesn't yet know or the train predates this field's callers), and never
    validated against the taxonomy here (fail-open; a typo'd tag must never cost a thought)."""
    rec = {"id": new_id(), "parent": parent, "role": role, "kind": str(kind or "thought"),
           "origin": (origin or "")[:200], "len": 0, "thread": "", "state": "", "ledger": [], "cargo": [],
           "product_type": product_type,
           "opened_ts": round(time.time(), 1), "closed_ts": None, "close_reason": None}
    _active[rec["id"]] = rec
    _log({"event": "open", "id": rec["id"], "parent": parent, "role": role, "kind": rec["kind"],
          "origin": rec["origin"][:120], "product_type": product_type})
    return rec


def get(train_id: str | None) -> dict | None:
    return _active.get(train_id) if train_id else None


def update(train_id: str | None, **fields) -> None:
    """Mirror the node's hot scalars into the record (len / thread / state / ledger). Cheap; no I/O."""
    rec = _active.get(train_id) if train_id else None
    if rec is None:
        return
    for k, v in fields.items():
        if k in rec and k not in ("id", "parent", "opened_ts"):
            rec[k] = v


def close(train_id: str | None, reason: str) -> dict | None:
    """Close a train with WHY. Returns the closed record (dropped from the active set)."""
    global _last_closed
    rec = _active.pop(train_id, None) if train_id else None
    if rec is None:
        return None
    rec["closed_ts"] = round(time.time(), 1)
    rec["close_reason"] = str(reason or "unknown")
    _last_closed = rec
    _log({"event": "close", "id": rec["id"], "parent": rec.get("parent"), "role": rec.get("role"),
          "kind": rec.get("kind"), "len": rec.get("len"), "reason": rec["close_reason"],
          "cargo_n": len(rec.get("cargo") or [])})
    return rec


def active() -> list[dict]:
    return list(_active.values())


def _log(row: dict) -> None:
    try:
        # J-1821 / F-2453 -- THE WRITE FENCE (D-0179): resolved BEFORE the mkdir so a refused (non-live) writer does not even create data/. Live, lab-sandbox and
        # outside-data paths get the same path back (byte-identical); refusal is swallowed by the fail-open except below. _active (in-memory ids) is untouched.
        path = profile.guard_path(_LOG)
        _DATA.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), **row}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def status() -> dict:
    """For du_pulse / the HUD: how many trains open right now, and the lineage shape of the log."""
    try:
        rows = [json.loads(l) for l in _LOG.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if _LOG.exists() else []
    except Exception:
        rows = []
    opens = [r for r in rows if r.get("event") == "open"]
    closes = [r for r in rows if r.get("event") == "close"]
    return {"active_now": len(_active), "opened_total": len(opens), "closed_total": len(closes),
            "forked": sum(1 for r in opens if r.get("parent")),           # 0 until step 2 exists
            "merged": sum(1 for r in closes if r.get("reason") == "merged"),
            "roles": {k: sum(1 for r in opens if r.get("role") == k) for k in ("main", "prove", "disprove")}}
