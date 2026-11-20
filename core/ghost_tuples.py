"""
Nascence — THE GHOST TUPLE REGISTRY (P0-B, 2026-08-17) — the ghost-index pattern's 4th life.
===========================================================================================
Lineage: pre-X4 (no-LLM era) → X4 village library → FreshStart (where it lay dead, and where
its live cousin's FTS5 leg silently queried a table that never existed) → here. What ports is
the small durable core: cheap fingerprints + set-intersection scoring, as a pre-filter and
catalog — never understanding, only finding. Zero LLM, as its oldest form and the courier law
both demand.

TWO NAMESPACES, NEVER MIXED (founder: "tuples for the world that are only for the world"):
  WORLD index  — one entry per FACTORY (the census's Tier 1) and per ITEM-grain entity.
                 Carries the factory's SCHEDULE DESCRIPTOR ("a set schedule kind of — a
                 schedule that changes"): its clock declared, re-read fresh, because
                 schedules are state too.
  MEMORY index — one entry per fragment_context chord (Du-side). Queried by Du-side
                 consumers only (the future chord_echo). Designed to be rebuilt from DB, with
                 incremental registration at stamp time.
                 STATUS (J-3306, 2026-11-05; docs/reviews/ghost_memory_index_chord_echo_J-3247.md):
                 the MEMORY index is NOT built in the live process. rebuild() is called only by
                 scripts/test_world_p0.py, so memory_index stays empty in the live process and
                 register_stamped_tuple() is a no-op there (it returns early at size() == 0).
                 The WORLD index, by contrast, is rebuilt live (core/world_manifest.py, 10 min
                 throttle). The design benchmarks of this docstring's first version (build ~45 ms,
                 query ~5.6 ms at 7,647 rows) are stale: measured 4.2 s build and 425 ms query at
                 111,143 rows. D-0636 (2026-11-02): do not wire it and do not retire it yet,
                 pending the J-3247 U1 replay. There is no 2-gram code here; ghost_hash() is a
                 truncated SHA-256 and scoring is tag-set intersection with rarity weights.
A query against one namespace can never return the other's entries — asserted in tests, not
assumed.

Scoring: rarity-weighted tag intersection (the v2 improvement over every prior port's plain
normalization): weight(tag) = 1/log(2+df) — a thunderstorm tag outweighs place:study, which
half the store carries.

THE LOUD-FAILURE LAW (the FreshStart lesson, now doctrine): assert_sources() verifies every
registered source actually exists and raises listing what doesn't. Run at registry build.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from pathlib import Path

logger = logging.getLogger("nascence.ghost_tuples")

_ROOT = Path(__file__).parent.parent
_DB = _ROOT / "data" / "memory" / "nascence.db"
_WORLD_F = _ROOT / "data" / "ghost_world_index.json"


def ghost_hash(name: str) -> str:
    return hashlib.sha256(name.strip().lower().encode()).hexdigest()[:16]


# ── The world index: factories + items, with schedule descriptors ────────────────────────────

def _factory_entries() -> list[dict]:
    """The census's Tier 1, each with tags + its declared clock. Read fresh (schedules are
    state). Every 'source' listed here is verified by assert_sources()."""
    entries = [
        {"id": "factory:weather", "tags": {"kind:weather", "control:none"},
         "schedule": {"clock": "persistence_timer", "source": "sensorium.state"},
         "source_file": None},
        {"id": "factory:tide", "tags": {"kind:tide", "control:none"},
         "schedule": {"clock": "m2_period", "source": "core.spatial.tide"}, "source_file": None},
        {"id": "factory:sky", "tags": {"kind:sky", "control:none"},
         "schedule": {"clock": "continuous", "source": "core.spatial.sun+core.heavens.moon"},
         "source_file": None},
        {"id": "factory:season", "tags": {"kind:season", "control:none"},
         "schedule": {"clock": "seasonal", "source": "sensorium._season"}, "source_file": None},
        {"id": "factory:temperature", "tags": {"kind:temperature", "control:partial"},
         "schedule": {"clock": "continuous", "source": "sensorium._warmth"}, "source_file": None},
        {"id": "factory:fire", "tags": {"kind:fire", "control:partial", "place:study"},
         "schedule": {"clock": "burn_down", "source": "sensorium.state"}, "source_file": None},
        {"id": "factory:garden", "tags": {"kind:garden", "control:partial", "place:garden"},
         "schedule": {"clock": "growth", "source": "sensorium._advance_garden"},
         "source_file": None},
        {"id": "factory:cat", "tags": {"kind:cat", "control:none"},
         "schedule": {"clock": "state_machine", "source": "cat_state.json"},
         "source_file": "data/cat_state.json"},
        {"id": "factory:objects", "tags": {"kind:objects", "control:none"},
         "schedule": {"clock": "event_driven", "source": "world_substrate"},
         "source_file": "data/world_substrate.json"},
        {"id": "factory:school", "tags": {"kind:school", "control:partial"},
         "schedule": {"clock": "curriculum", "source": "core.school"}, "source_file": None},
        {"id": "factory:body", "tags": {"kind:body", "control:partial"},
         "schedule": {"clock": "somatic_tick", "source": "core.somatic"}, "source_file": None},
        {"id": "factory:acts", "tags": {"kind:acts", "control:full"},
         "schedule": {"clock": "event_driven", "source": "activity_memory"},
         "source_file": None},
    ]
    # peers ×7, each on its own gap_days clock
    try:
        from core.peers import PERSONAS
        for key, p in PERSONAS.items():
            entries.append({"id": f"factory:peer:{key}",
                            "tags": {"kind:peer", "control:none", f"peer:{key}"},
                            "schedule": {"clock": "gap_days",
                                         "params": {"gap_days": p.get("gap_days")},
                                         "source": "core.peers"},
                            "source_file": None})
    except Exception as exc:
        logger.debug("[ghost] peers unavailable: %s", exc)
    # ITEM-grain entities (world_substrate) — the exact-hash citizens. Position (2026-08-17):
    # every item now carries its place-within-the-place from the position authority
    # (world_objects.py) — pos in the shared room frame, or "gone" when the sea took it back.
    try:
        from core import world_substrate as _ws
        try:
            from core import world_objects as _wo
        except Exception:
            _wo = None
        for oid, obj in _ws._load().items():
            e = {"id": f"item:{oid}", "ghost_hash": ghost_hash(oid),
                 "tags": {"kind:item", f"class:{obj.object_class}",
                          f"place:{getattr(obj, 'location', '?')}", "control:none"},
                 "schedule": {"clock": "event_driven", "source": "world_substrate"},
                 "source_file": "data/world_substrate.json",
                 "observations": len(getattr(obj, "observations", []) or [])}
            if _wo is not None:
                rec = _wo.get_object(oid)
                if rec:
                    e["pos"] = rec.get("position")
                    if rec.get("location") == "gone":
                        e["tags"].add("state:gone")
                    e["moves"] = max(0, len(rec.get("history") or []) - 1)
            entries.append(e)
    except Exception as exc:
        logger.debug("[ghost] world_substrate unavailable: %s", exc)
    return entries


def build_world_index(persist: bool = True) -> dict:
    """Assemble the world index fresh (schedules re-read — they change). Returns the index."""
    entries = _factory_entries()
    idx = {"built_ts": round(time.time(), 1), "namespace": "world",
           "entries": {e["id"]: {**e, "tags": sorted(e["tags"])} for e in entries}}
    if persist:
        try:
            tmp = _WORLD_F.with_suffix(".tmp")
            tmp.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(_WORLD_F)
        except Exception:
            pass
    return idx


# ── The memory index: fragment_context chords (Du-side) ──────────────────────────────────────

_TIDE_BANDS = ((0.66, "high"), (0.33, "mid"), (-1.0, "low"))
_WARMTH_BANDS = ((0.66, "warm"), (0.33, "mild"), (-1.0, "cold"))   # thirds, same shape as tide


def _tuple_tags(row: dict) -> set[str]:
    tags: set[str] = set()
    if row.get("place"):
        tags.add("place:" + row["place"])
    if row.get("weather"):
        tags.add("wx:" + row["weather"])
    if row.get("standpoint"):
        tags.add("sp:" + row["standpoint"])
    tl = row.get("tide_level")
    if tl is not None:
        tags.add("tide:" + next(b for th, b in _TIDE_BANDS if tl > th))
    w = row.get("warmth")
    if w is not None:
        tags.add("warmth:" + next(b for th, b in _WARMTH_BANDS if w > th))
    if row.get("cat_at"):
        tags.add("cat:" + row["cat_at"])
    try:
        for s in json.loads(row.get("sounds") or "[]"):
            tags.add("snd:" + s)
    except Exception:
        pass
    return tags


class MemoryIndex:
    """In-RAM, rebuilt from DB (cheap), incrementally fed at stamp time. Du-side ONLY."""

    def __init__(self) -> None:
        self.namespace = "memory"
        self._entries: dict[str, set[str]] = {}
        self._df: dict[str, int] = {}          # tag document-frequency, for rarity weights
        self.built_ts = 0.0

    def rebuild(self) -> int:
        import sqlite3
        self._entries.clear()
        self._df.clear()
        conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            try:    # TEMPERATURE + CAT LOCATION (2026-08-17): this connection is read-only (mode=ro)
                    # so it cannot ALTER TABLE itself — tolerate a live table that hasn't been migrated
                    # yet (the columns land on the next sync_fragment_context() run; restart-gated).
                cur = conn.execute("SELECT fragment_id, place, weather, tide_level, sounds, "
                                   "standpoint, warmth, cat_at FROM fragment_context")
            except sqlite3.OperationalError:
                cur = conn.execute("SELECT fragment_id, place, weather, tide_level, sounds, "
                                   "standpoint FROM fragment_context")
            for r in cur:
                self.register(r["fragment_id"], _tuple_tags(dict(r)), _bump_df=True)
        finally:
            conn.close()
        self.built_ts = time.time()
        return len(self._entries)

    def register(self, fragment_id: str, tags: set[str], _bump_df: bool = True) -> None:
        if fragment_id in self._entries:
            return
        self._entries[fragment_id] = tags
        if _bump_df:
            for t in tags:
                self._df[t] = self._df.get(t, 0) + 1

    def _w(self, tag: str) -> float:
        return 1.0 / math.log(2 + self._df.get(tag, 0))

    def query(self, qtags: set[str], top_k: int = 10) -> list[tuple[str, float]]:
        """Rarity-weighted chord match: score = Σ w(tag in common) / sqrt(|entry tags|)."""
        scored = []
        for fid, tags in self._entries.items():
            common = qtags & tags
            if not common:
                continue
            s = sum(self._w(t) for t in common) / (math.sqrt(len(tags)) + 0.001)
            scored.append((fid, round(s, 4)))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def size(self) -> int:
        return len(self._entries)


memory_index = MemoryIndex()      # module singleton; consumers rebuild-on-first-use


def register_stamped_tuple(fragment_id: str, row: dict) -> None:
    """Incremental stamp-time registration (P0 wire-in from memory_edges). Fail-open."""
    try:
        if memory_index.size() == 0:
            return                 # not built in this process — the rebuild path owns it
        memory_index.register(fragment_id, _tuple_tags(row))
    except Exception:
        pass


# ── The loud-failure law ─────────────────────────────────────────────────────────────────────

def assert_sources() -> None:
    """Every source a registered entry names must EXIST — else raise, listing the missing.
    The FreshStart ghost-table failure is why this is law, not politeness."""
    missing: list[str] = []
    for e in _factory_entries():
        sf = e.get("source_file")
        if sf and not (_ROOT / sf).exists():
            missing.append(f"{e['id']} -> {sf}")
    import sqlite3
    try:
        conn = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True)
        n = conn.execute("SELECT name FROM sqlite_master WHERE name='fragment_context'").fetchone()
        conn.close()
        if not n:
            missing.append("memory-index -> fragment_context table")
    except Exception as exc:
        missing.append(f"memory-index -> nascence.db ({exc})")
    if missing:
        raise RuntimeError("GHOST REGISTRY SOURCES MISSING (loud by law): " + "; ".join(missing))


def status() -> dict:
    """For the HUD: sizes, ages, namespaces."""
    out = {"memory_index": {"size": memory_index.size(),
                            "built_ts": memory_index.built_ts,
                            "distinct_tags": len(memory_index._df)}}
    try:
        w = json.loads(_WORLD_F.read_text(encoding="utf-8"))
        ents = w.get("entries", {})
        out["world_index"] = {
            "size": len(ents), "built_ts": w.get("built_ts"),
            "factories": sum(1 for k in ents if k.startswith("factory:")),
            "items": sum(1 for k in ents if k.startswith("item:")),
        }
    except Exception:
        out["world_index"] = None
    return out
