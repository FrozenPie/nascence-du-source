"""
Nascence — INVENTORY: the shared item contract (2026-08-30, J-0422,
docs/staged/actions_manager_overhaul.md, founder ruling D-0099).

WHY THIS EXISTS. Five location modules each grew their own copy of the same idea — a declared item
table, a carryable set, and a per-item dict with carried/place/bio/history — and they diverged in
shape, in arity, and in whether they can be extended at all. The consequence was not cosmetic
(F-0558): in study_life and wood_life a NEWLY DECLARED ITEM NEVER REACHES AN EXISTING SAVE.
study_life._st() builds its items only inside `if not st.get("_init")` and the live save is already
initialised; wood_life._load() only returns defaults when the JSON fails to parse. Every access site
is a direct index, so the KeyError that follows is swallowed by the enclosing try/except in act() and
the new hand just silently does nothing. garden was the only module with a migration, and it hardcodes
one key ("water_bucket") as an `elif` off the bootstrap branch — so only one migration can ever run.

sync_items() is the general form of garden's hardcoded block: it diffs the DECLARED table against what
is SAVED and creates whatever is missing. It is additive-only — it never overwrites an item that
already exists (a save is the truth about a thing Du has handled, and its history and position are his,
not the table's) and it never removes one, so an item retired from the declared table keeps existing in
the world until something deliberately takes it away.

Each module keeps building its own item dict, in its own shape, via the `build` callback. That is
deliberate for this first pass: unifying the SHAPES changes live data (garden stores an "id" the other
two derive, garden keeps a second parallel st["carried"] list, wood has no set-down at all), and each
of those is a real behavioural decision that belongs in its own reviewed pass. This module makes adding
an item WORK everywhere first; converging the shape is the step after.

Zero LLM. Fail-open. Additive.
"""
from __future__ import annotations

from typing import Callable, Iterable

# The shape the five modules are converging ON (garden is already here bar nothing; study_life and
# wood_life match it except they omit "id" and derive it at register time instead). New code should
# use make_item(); existing modules keep their own builder until their own migration pass.
ITEM_KEYS = ("id", "key", "name", "pos", "place", "carried", "bio", "history")


def make_item(key: str, name: str, pos, place: str, bio: str, *,
              id_prefix: str = "", ts: float | None = None) -> dict:
    """The canonical item dict. `ts` is the biography's first event time — pass a real (seeded or
    back-dated) timestamp so a newly-migrated item does not claim to have appeared this second."""
    import time as _t
    return {"id": f"{id_prefix}{key}" if id_prefix else key, "key": key, "name": name, "pos": pos,
            "place": place, "carried": False, "bio": bio,
            "history": [{"ts": ts if ts is not None else _t.time(), "event": bio}]}


def sync_items(saved: dict, declared: Iterable, build: Callable[[tuple], dict]) -> list[str]:
    """Create every declared item that is missing from `saved`. Returns the keys actually added.

    saved     — the module's live {key: item_dict} mapping, mutated in place.
    declared  — the module's _ITEMS table; each entry's FIRST field is the item key (true of
                garden's 4-tuples and study_life's / wood_life's 5-tuples alike).
    build     — build(entry) -> the item dict, in THAT module's own shape.

    Additive-only: never overwrites and never deletes. Idempotent — calling it on every load is the
    point, since that is what makes a table edit reach an already-initialised save.
    """
    added: list[str] = []
    if saved is None:
        return added
    for entry in declared:
        try:
            key = entry[0]
        except Exception:
            continue
        if not key or key in saved:
            continue
        try:
            saved[key] = build(entry)
            added.append(key)
        except Exception:
            continue          # fail-open: one malformed row must not cost the others
    return added


def carried(saved: dict) -> list[str]:
    """Keys currently in hand, read from the per-item flag — the one representation all three
    item-bearing modules agree on (garden's parallel st["carried"] list is a second copy of this)."""
    return [k for k, it in (saved or {}).items() if isinstance(it, dict) and it.get("carried")]


def present_at(saved: dict, key: str, here: str) -> bool:
    """Is the item to hand — carried, or lying in this place? study_life._need_here's rule, shared."""
    it = (saved or {}).get(key) or {}
    return bool(it.get("carried") or it.get("place") == here)
