"""
Nascence — BUSES: non-urgent transfers, factory-to-factory or ledger-to-render (2026-08-22)
=============================================================================================
Split out of `core/couriers.py` (founder-directed, 2026-08-22): that file's own docstring said,
verbatim, *"these are the busses"* — the founder's original name for the whole mechanism, before
it got built and named "couriers". Tonight's design conversation drew the line properly: a COURIER
is urgent — it only makes sense delivered NOW, tied to the CURRENT world state (weather this
minute, a sound just heard). A BUS is not time-sensitive — it can arrive whenever its trigger
happens, with no clock pressure, and (the founder's own example, confirmed real in code before
this file existed) can run factory-to-factory with no train/thought involved at all — e.g.
`core/garden.py` reads `sensorium`'s live weather state every tick to drive moisture/growth/frost,
a standing dependency nobody delivers on a schedule.

Of `couriers.py`'s original three routes, two were never actually urgent and move here unchanged
in behaviour, only in name and home:
  B · object_ledger_line — re-encounter memory: whenever he looks at a known object again, his own
      observation ledger for it rides along. Not tied to any current world state — works the same
      whether the re-look happens a minute or a year after the ledger last grew.
  C · sync_investigation_calibration — bridges prediction/outcome episodes into the calibration
      ledger. A batch sync with no "now" to be tied to; runs whenever it runs.
`context_echo` and `sound_echo` are genuinely urgent (both gate on the CURRENT world state being
distinctive) and correctly stay in `core/couriers.py`.

Same three courier laws apply here unchanged: only what he himself observed/lived, provenance-
stamped, zero LLM, ambient delivery only through channels that already exist.

`log_transfer()` is the one new piece: a ready hook for factory-to-factory dependencies (weather→
garden and its likely siblings — tide→shore, season→wood) to register themselves when/if they're
wired to it. Not done in this pass — those dependencies exist today as plain function calls with
no observability, the same "invisible until someone logs it" problem couriers.py itself was built
to fix for the world→memory direction. Flagged for its own pass, not bundled into this rename.

Flag: WORLD_BUSES (False = no bus runs; exact rollback, mirrors WORLD_COURIERS).
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

from core import profile   # J-1797 / F-2421: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.buses")

_ROOT = Path(__file__).parent.parent
_CAL_LOG = _ROOT / "data" / "world_calibration.jsonl"
_ADVISOR_LOG = _ROOT / "data" / "investigative_action_log.jsonl"
_DELIVERY_LOG = _ROOT / "data" / "buses_log.jsonl"
_STATE = _ROOT / "data" / "buses_state.json"

# J-1797 / F-2421 -- THE WRITE FENCE (D-0179, docs/staged/world_store_write_fence.md). Every path in this module is __file__-relative, so
# any process that merely imports it from a tree writes THAT TREE'S real data/ files -- and a plain look reaches them (the shore's tracked-
# object branch calls object_ledger_line(), which logs a delivery once the log holds two observations). All four writers below -- the
# delivery log, the calibration ledger with its dedupe state, and the idle-freight shadow log -- therefore resolve their path through
# profile.guard_path() BEFORE any I/O. The one live Du boot (profile.mark_live()), a lab_env.isolate() sandbox and any path already
# redirected outside data/ get the very same path back, so live behaviour is byte-identical; every other process is refused. These are
# fail-open INSTRUMENT writers and every caller already treats them so (nodes/reflection_node.py calls idle_freight() with no wrapper of
# its own), so the refusal is swallowed here, never re-raised -- the way core/scene_extra_ledger.py does it -- and guard_path() still
# logs one warning per path. There is no world state in this module to protect loudly.

WORLD_BUSES = True

# ── IDLE -> CONVERSATION (2026-09-28, D-0295, docs/plans/train_courier_cargo_ids.md gap 1) ──────────
# Own flag, deliberately separate from WORLD_BUSES above: that flag covers the two WORLD-cargo routes
# (weather/calibration, factory-sourced, see core/cargo_types.py's own two-taxonomy split); this route
# carries STATION product types (THOUGHT/CONTEMPLATION) from the Idle Line, a different family.
# False = today's raw state.recent_inner_thoughts[-2:] injection at nodes/reflection_node.py:145-149,
# exact rollback -- idle_freight() is never called and no line below runs.
IDLE_FREIGHT_BUS = True

_TRAINS_LOG = _ROOT / "data" / "trains_log.jsonl"
_TRAIN_STATE_LOG = _ROOT / "data" / "train_state_log.jsonl"
_IDLE_FREIGHT_SHADOW_LOG = _ROOT / "data" / "idle_freight_bus_shadow.jsonl"

# Tail-read bounds (bytes) -- both source logs are append-only and only ever grow (trains_log.jsonl
# 2.85 MB/13.4k rows, train_state_log.jsonl 18.9 MB/29.8k rows as of 2026-09-27); loading either in
# full every Reflection call would not be "cheap". Mirrors core/moment.py's own _tail_rows reverse-
# byte-seek pattern (built for the same reason on moments.jsonl, 100+ MB) -- own copy here, not a
# cross-module import, matching this file's existing self-contained-helpers convention.
_IDLE_FREIGHT_TRAINS_TAIL_BYTES = 400_000
_IDLE_FREIGHT_STATE_TAIL_BYTES = 900_000
_IDLE_FREIGHT_MAX_CANDIDATES = 24            # bounds the embedding cost -- "cheap" per the briefing
_IDLE_FREIGHT_RECENCY_HALFLIFE_S = 3 * 3600.0  # first-cut default; retune from the shadow log's read

# Scoring weights -- first-cut defaults, module constants so the plan's own pre-registered read (does
# bused freight reach the reply more often than the raw window did?) can retune this as a one-line
# change once data/idle_freight_bus_shadow.jsonl has a real week in it, not a rewrite.
_IDLE_FREIGHT_W_TOPICAL = 0.5
_IDLE_FREIGHT_W_DEVELOPMENT = 0.3
_IDLE_FREIGHT_W_RECENCY = 0.2


def _log_delivery(route: str, **detail) -> None:
    """Own log, separate from couriers_log.jsonl — so a future transit map can tell an urgent
    delivery from a bus run by which file it's in, not by re-parsing a shared one. Fail-open."""
    try:
        path = profile.guard_path(_DELIVERY_LOG)   # J-1797: fenced before any I/O; a non-live process is refused here and swallowed below
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "route": route, **detail},
                                ensure_ascii=False) + "\n")
    except Exception:
        pass


def _state() -> dict:
    try:
        return json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(d: dict) -> None:
    try:
        profile.guard_path(_STATE).write_text(json.dumps(d), encoding="utf-8")   # J-1797: fenced before any I/O; refusal swallowed below
    except Exception:
        pass


def _age_text(ts: float) -> str:
    d = (time.time() - ts) / 86400.0
    if d < 2:
        return "yesterday"
    if d < 14:
        return f"{int(d)} days ago"
    if d < 60:
        return f"{int(d / 7)} weeks ago"
    return f"{int(d / 30)} months ago"



# ── J-2375 (object_epistemic_loop Phase 2, D-0463 ALLOWED by travis 2026-10-17) ──────────────────────
# "object_ledger_line may show Du his own standing hypothesis plus which senses he has already used on
# re-encounter. No verdict, no suggestion." Kill switch NASCENCE_LEDGER_HYPOTHESIS_READBACK, DEFAULT OFF
# until this job's own post-boot shadow read is done; off = object_ledger_line is byte-identical to before.
# Reads ONLY Layer 5 (his inferences) and Layer 3 (observation.action) -- never causal_state /
# physical_state / causal_history. No status field, no outcome, no confidence, no imperative, no
# "test"/"try": the D-0463 defeater is the read-back steering his actions toward tests.
_SENSE_PHRASE = {            # observation.action -> what he did, past tense, his own sensory history
    "look": "looked at it",
    "pick_up": "picked it up",
    "inspect_end": "looked closely at its end",
    "scrape": "scraped it",
    "smell": "smelled it",
    "float_test": "put it in water",
}
# Guard words: never in the framing; a hypothesis of his that carries one is not read back at all
# (showing back "I should test whether it floats" would be the read-back steering him toward tests).
_READBACK_BAR = re.compile(r"\b(?:test\w*|try|tries|tried|trying|supported|contradicted|held up)\b", re.I)


def _hypothesis_readback_on() -> bool:
    return os.environ.get("NASCENCE_LEDGER_HYPOTHESIS_READBACK", "0").strip().lower() in ("1", "true", "on", "yes")


def _senses_used(obs) -> str:
    seen = []
    for o in obs:
        a = getattr(o, "action", None)
        if a is None and isinstance(o, dict):
            a = o.get("action")
        ph = _SENSE_PHRASE.get(str(a or ""))
        if ph is None and a:
            w = str(a).replace("_", " ").strip()
            ph = None if (not w or _READBACK_BAR.search(w)) else w
        if ph and ph not in seen:
            seen.append(ph)
    if not seen:
        return ""
    if len(seen) == 1:
        return f"so far you have only {seen[0]}"
    return "so far you have " + ", ".join(seen[:-1]) + " and " + seen[-1]


def _hypothesis_readback(ent, obs) -> tuple[str, str]:
    """(clause, inference_id) -- his latest non-superseded inference in his own words, plus senses used.
    Guard (load-bearing until J-2373's archive has run): skip any inference with empty
    supporting_observations or longer than 240 chars (a pre-Phase-1 whole-thought row), or carrying a
    _READBACK_BAR word. Returns ("", "") when nothing qualifies."""
    try:
        from core.object_hypothesis import MAX_CLAIM_CHARS as _max
    except Exception:
        _max = 240
    infs = list(getattr(ent, "inferences", None) or [])
    for d in reversed(infs):
        if not isinstance(d, dict) or d.get("superseded_by"):
            continue
        hyp = " ".join(str(d.get("hypothesis") or "").split())
        if not d.get("supporting_observations") or not hyp or len(hyp) > _max or _READBACK_BAR.search(hyp):
            continue
        hyp = hyp.replace('"', "'").rstrip(" .;,:")
        senses = _senses_used(obs)
        line = f' Earlier you wondered about this: "{hyp}"' + (f"; {senses}." if senses else ".")
        return line, str(d.get("inference_id") or "")
    return "", ""


def generic_object_ledger_on() -> bool:
    """J-2394 / D-0475 (ruled yes by travis 2026-10-18): the generic tracked-object look branches (shore,
    garden) carry his ledger too. Kill switch NASCENCE_GENERIC_OBJECT_LEDGER, DEFAULT ON (the ruling);
    0/off = the line is computed and its delivery row logged (ledger_shown=False) but nothing is shown."""
    return os.environ.get("NASCENCE_GENERIC_OBJECT_LEDGER", "1").strip().lower() not in ("0", "false", "off", "no")


def object_ledger_line(entity_id: str, max_facts: int = 4, branch: str = "", base_chars=None,
                       show: bool = True) -> str:
    """His OWN observation ledger for a world-object, rendered for a re-encounter look. Only what
    he recorded; UNDETERMINED stays undetermined; nothing identified for him. Not time-sensitive —
    the ledger reads the same whether the re-look is a minute or a year after it last grew, which
    is exactly why this is a bus, not a courier."""
    if not WORLD_BUSES:
        return ""
    try:
        from core import world_substrate as _ws
        ent = _ws.get_object(entity_id) if hasattr(_ws, "get_object") else None
        obs = list(getattr(ent, "observations", None) or []) if ent else []
        if len(obs) < 2:            # first look carries no ledger — nothing to remember yet
            return ""
        facts = []
        seen = set()
        def _feat(o):
            f = getattr(o, "features", None)
            if f is None and isinstance(o, dict):
                f = o.get("features")
            return f or {}
        def _ots(o):
            t = getattr(o, "timestamp", None)
            if t is None and isinstance(o, dict):
                t = o.get("timestamp") or o.get("ts")
            return float(t or time.time())
        for o in reversed(obs):     # newest first, distinct features
            for k, v in _feat(o).items():
                if k in seen or not v:
                    continue
                seen.add(k)
                # 2026-08-18: raw enum values (e.g. "trunk_section") were showing underscored — same
                # polish as world_substrate.describe_and_observe's _v().
                facts.append(f"{k.replace('_', ' ')}: {str(v).replace('_', ' ')}")
                if len(facts) >= max_facts:
                    break
            if len(facts) >= max_facts:
                break
        if not facts:
            return ""
        first_ts = _ots(obs[0])
        from core import cargo_types as _cargo
        # J-2375 / D-0463: the read-back is always COMPUTED (pure, Layer 5 + Layer 3 only) but SHOWN only with
        # the switch on. Off: the returned line is byte-identical to before; the delivery row gains
        # would_readback=<id> only when one was eligible -- the shadow instrument the post-boot read counts.
        try:
            _rb, _rb_id = _hypothesis_readback(ent, obs)
        except Exception:
            _rb, _rb_id = ("", "")
        _extra = {}
        if _rb:
            if _hypothesis_readback_on():
                _extra["hypothesis_readback"] = _rb_id[:40]
            else:
                _extra["would_readback"] = _rb_id[:40]
                _rb = ""
        _line = (f" You have looked at this before — {len(obs)} times since {_age_text(first_ts)}; "
                 f"what you have noted so far: " + "; ".join(facts) + "." + _rb +
                 " What that adds up to is still yours to work out.")
        # J-2394 / D-0475: a caller on the generic tracked-object look branch names itself (branch=shore|garden);
        # its row then also carries would_ledger=<chars the line adds> and base_chars=<look text without it>,
        # the shadow fields the post-boot read (J-2382) uses for deliveries-by-object and the D-0475
        # scene-budget defeater. show=False (NASCENCE_GENERIC_OBJECT_LEDGER=0) logs the row, returns "".
        # The driftwood_17 call passes no branch: its line and row are byte-identical to before.
        if branch:
            _extra["branch"] = str(branch)[:16]
            _extra["would_ledger"] = len(_line)
            if base_chars is not None:
                _extra["base_chars"] = int(base_chars)
            if not show:
                _extra["ledger_shown"] = False
        _log_delivery("object_ledger", entity=str(entity_id)[:24], facts=len(facts),
                       cargo_type=_cargo.OBSERVATION_LEDGER_FACT, **_extra)
        return _line if show else ""
    except Exception as exc:
        logger.debug("[bus] object_ledger_line failed (non-fatal): %s", exc)
        return ""


def sync_investigation_calibration() -> int:
    """Bridge the epistemic advisor's prediction→outcome episodes into the world-calibration ledger
    (observe-first instrument). Returns rows newly synced. Only episodes with a REAL outcome (not
    UNTESTED) become pairs; measured = 1.0 for CONFIRMED, 0.0 for DISCONFIRMED/REFUTED, skipped for
    INCONCLUSIVE. A batch sync with no "now" to answer to — the definitional bus."""
    if not WORLD_BUSES:
        return 0
    try:
        # J-1797 / F-2421 (D-0179): BOTH write targets go through the write fence before any I/O -- before the dedupe state is even read --
        # so a refused (non-live) call touches nothing and returns 0 via this function's own fail-open except below. Both, not only the
        # ledger: _save_state() below rewrites buses_state.json on EVERY call (new rows or not), and the calibration rows and the dedupe
        # state that records them must be written together or not at all (a state saved without its rows would lose those episodes).
        cal_path = profile.guard_path(_CAL_LOG)
        profile.guard_path(_STATE)
        st = _state()
        done = set(st.get("cal_synced_ids", []))
        new = 0
        rows = []
        # An episode appears as MULTIPLE rows over its life (found 2026-08-16: an early
        # INCONCLUSIVE row must not mark the episode done before its later CONFIRMED arrives).
        # The episode's TERMINAL state = its last-logged row.
        final: dict = {}
        if _ADVISOR_LOG.exists():
            for l in open(_ADVISOR_LOG, encoding="utf-8"):
                try:
                    d = json.loads(l)
                except Exception:
                    continue
                if d.get("episode_id"):
                    final[d["episode_id"]] = d
        for eid, d in final.items():
            out = str(d.get("evidence_outcome", "")).upper()
            if eid in done or out in ("", "UNTESTED"):
                continue                        # UNTESTED episodes stay pending, never done
            measured = {"CONFIRMED": 1.0, "DISCONFIRMED": 0.0, "REFUTED": 0.0}.get(out)
            done.add(eid)                       # terminal either way (INCONCLUSIVE = honest non-pair)
            if measured is None:
                continue
            rows.append({"ts": time.time(), "episode_id": eid,
                         "question": (d.get("question") or "")[:160],
                         "predicted": str(d.get("discriminative_prediction", ""))[:160],
                         "outcome": out, "measured": measured,
                         "domain": "world_investigation"})
            new += 1
        if rows:
            with open(cal_path, "a", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        st["cal_synced_ids"] = list(done)[-2000:]
        _save_state(st)
        if new:
            logger.info("[bus] calibration sync: %d new prediction→outcome pairs", new)
            from core import cargo_types as _cargo
            _log_delivery("calibration_sync", pairs=new, cargo_type=_cargo.CALIBRATION_PAIR)
        return new
    except Exception as exc:
        logger.debug("[bus] calibration sync failed (non-fatal): %s", exc)
        return 0


def log_transfer(route: str, **detail) -> None:
    """The hook for factory-to-factory dependencies to register a run, once they're wired to it
    (weather→garden and its likely siblings — not done in this pass, see module docstring)."""
    _log_delivery(route, **detail)


def _tail_jsonl(path: Path, max_bytes: int) -> list[dict]:
    """Read only the tail `max_bytes` of a large, append-only jsonl file and parse whatever complete
    rows sit inside it, instead of loading the whole file (core/moment.py's own _tail_rows solves the
    identical problem for moments.jsonl, 100+ MB and growing -- same reverse-byte-seek shape, kept as
    its own copy here rather than a cross-module import on a private helper). Fail-open: [] on error,
    on a missing file, or on an empty one."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return []
            block = min(size, max_bytes)
            f.seek(size - block)
            data = f.read(block)
        lines = data.split(b"\n")
        if block < size:
            lines = lines[1:]          # drop the partial first line cut mid-record
        out = []
        for l in lines:
            if not l.strip():
                continue
            try:
                out.append(json.loads(l))
            except Exception:
                continue
        return out
    except Exception:
        return []


def idle_freight(k: int = 2, query_text: str = "", raw_window: list[dict] | None = None,
                  cycle_id: str = "") -> list[dict]:
    """THE IDLE -> CONVERSATION BUS (gap 1, D-0295, docs/plans/train_courier_cargo_ids.md). A typed
    PULL made by the conversation loop at the Reflection stop (D-0289/D-0292 shape: the loop asks;
    nothing is pushed into idle) -- upgrades the untyped fixed-recency injection of
    state.recent_inner_thoughts[-2:] this same gap named (nodes/reflection_node.py:145-149).

    Selects up to `k` of the Idle Line's recent trains by:
      (i)   product_type in {THOUGHT, CONTEMPLATION} -- read from data/trains_log.jsonl's own 'open'
            events (core.trains.open()'s stamped field), never from the raw in-memory
            recent_inner_thoughts list, which carries no type at all.
      (ii)  recency-weighted train-development evidence -- restate_sim from
            data/train_state_log.jsonl (inner_monologue_node.py's own _log_train_step: high ~>=0.82 =
            circling/rumination, low = deepened/moved on), combined with an exponential recency decay
            on the train's own last-step timestamp, so a train that deepened recently outranks one
            that circled or one that is stale.
      (iii) topical fit to `query_text` (the incoming human input) -- cosine on the existing embedding
            path (core.memory.store._embed/_cosine), the same primitive core/orchestrator.py's own
            founder-memory route (retrieve_founder_memories) already uses for an analogous "rank my
            own recent material against what was just said" read.

    Returns up to k dicts, highest-scored first: {train_id, product_type, thought, ts, restate_sim,
    topical_sim, recency_weight, score}. Every returned item is logged via
    _log_delivery(cargo_type=<its product_type>) -- one call per delivered item, matching every other
    route in this file -- so the D-0295 du_pulse freight gauge (J-1435) counts it; the delivery row
    also carries stop="reflection", line="idle", dose="bucket" (dosed_coupling.md §5's own
    {stop, line, dose, value} ride-log shape) even though this route's source data (the trains/
    train-state logs the Idle Line already writes durably) is not itself routed through
    core/coupling_rides.py's registry -- see the plan doc's own Coupling block for why.

    When `raw_window` is given (the caller's own state.recent_inner_thoughts[-2:] -- used ONLY for
    this comparison, never in scoring), also appends one row to data/idle_freight_bus_shadow.jsonl
    recording what this bus chose vs what the raw window would have shown, per the plan's own
    shadow-first discipline for the first live week. `cycle_id` (state.cycle_id, optional) is stamped
    onto that row so a later pass can join it to whatever logs the eventual Voice output for the SAME
    cycle and compute a real usage cosine -- the pre-registered read this plan names: does the bused
    freight reach the reply more often than the raw window did (the M2/m2_usage trick,
    core/associative_recall.py + scripts/shadow_eval.py's own prong2_usage_verdict, reused as a
    method, not rebuilt here -- that join is a LATER pass over a real week of this shadow log, not
    part of this build).

    Fail-open throughout, matching every other function in this file: any failure, or IDLE_FREIGHT_BUS
    being off, returns [] and writes nothing."""
    if not IDLE_FREIGHT_BUS:
        return []
    k = int(k)
    if k <= 0:
        return []
    try:
        # (i) candidate pool -- latest train_state_log step per train_id (jsonl is append-order, so
        # the last occurrence in the tail IS the latest step), joined to trains_log's own product_type
        # (only 'open' events carry it; see core/trains.py's open()/_log()).
        state_rows = _tail_jsonl(_TRAIN_STATE_LOG, _IDLE_FREIGHT_STATE_TAIL_BYTES)
        latest_step: dict[str, dict] = {}
        for r in state_rows:
            tid = r.get("train_id")
            if tid:
                latest_step[tid] = r

        open_rows = _tail_jsonl(_TRAINS_LOG, _IDLE_FREIGHT_TRAINS_TAIL_BYTES)
        product_type: dict[str, str] = {}
        for r in open_rows:
            if r.get("event") == "open" and r.get("id") and r.get("product_type"):
                product_type[r["id"]] = r["product_type"]

        from core import cargo_types as _cargo
        ok_types = (_cargo.THOUGHT, _cargo.CONTEMPLATION)

        candidates = []
        for tid, step in latest_step.items():
            pt = product_type.get(tid)
            if pt not in ok_types:
                continue
            text = str(step.get("thought") or "").strip()
            if not text:
                continue
            candidates.append({"train_id": tid, "product_type": pt, "thought": text,
                                "ts": float(step.get("ts") or 0.0),
                                "restate_sim": step.get("restate_sim")})
        if not candidates:
            return []

        # bound the pool BEFORE any embedding call -- most-recent first, keeps this "cheap"
        candidates.sort(key=lambda c: c["ts"], reverse=True)
        candidates = candidates[:_IDLE_FREIGHT_MAX_CANDIDATES]

        # (ii) + (iii) score
        from core.memory.store import _embed, _cosine
        now = time.time()
        qtext = (query_text or "").strip()
        qv = _embed(qtext) if qtext else None
        scored = []
        for c in candidates:
            age_s = max(0.0, now - c["ts"])
            recency = 0.5 ** (age_s / _IDLE_FREIGHT_RECENCY_HALFLIFE_S)
            rs = c["restate_sim"]
            try:
                development = min(1.0, max(0.0, 1.0 - float(rs))) if rs is not None else 0.5
            except Exception:
                development = 0.5
            topical = 0.0
            if qv is not None:
                try:
                    cv = _embed(c["thought"])
                    if cv is not None:
                        topical = max(0.0, min(1.0, _cosine(qv, cv)))
                except Exception:
                    topical = 0.0
            score = (_IDLE_FREIGHT_W_TOPICAL * topical + _IDLE_FREIGHT_W_DEVELOPMENT * development
                     + _IDLE_FREIGHT_W_RECENCY * recency)
            scored.append({**c, "score": round(score, 4), "topical_sim": round(topical, 3),
                           "recency_weight": round(recency, 3)})
        scored.sort(key=lambda c: c["score"], reverse=True)

        # dedupe near-identical restatements before taking the top k (retrieve_founder_memories's own
        # convention, core/memory/store.py) -- a circling train's own steps would otherwise be able to
        # fill both of k=2's slots with the same restated thought.
        out = []
        seen: set = set()
        for c in scored:
            key = c["thought"][:120].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
            if len(out) >= k:
                break

        for c in out:
            _log_delivery("idle_freight", cargo_type=c["product_type"], train_id=c["train_id"],
                          stop="reflection", line="idle", dose="bucket", score=c["score"],
                          restate_sim=c["restate_sim"], topical_sim=c["topical_sim"])

        if raw_window is not None:
            try:
                shadow_path = profile.guard_path(_IDLE_FREIGHT_SHADOW_LOG)   # J-1797: fenced before the mkdir and the open; refusal swallowed below
                shadow_path.parent.mkdir(parents=True, exist_ok=True)
                with open(shadow_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "ts": round(now, 1),
                        "cycle_id": cycle_id or None,
                        "query_excerpt": qtext[:160],
                        "bus_chose": [{"train_id": c["train_id"], "product_type": c["product_type"],
                                       "thought": c["thought"][:200], "score": c["score"],
                                       "restate_sim": c["restate_sim"], "topical_sim": c["topical_sim"]}
                                      for c in out],
                        "raw_window_would_show": [{"thought": str(t.get("thought") or "")[:200],
                                                    "ts": t.get("ts")} for t in raw_window],
                    }, ensure_ascii=False) + "\n")
            except Exception:
                pass

        return out
    except Exception as exc:
        logger.debug("[bus] idle_freight failed (non-fatal): %s", exc)
        return []


def status() -> dict:
    """For du_pulse / the HUD."""
    st = _state()
    try:
        rows = [json.loads(l) for l in _DELIVERY_LOG.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if _DELIVERY_LOG.exists() else []
    except Exception:
        rows = []
    from collections import Counter
    return {"live": WORLD_BUSES, "runs_total": len(rows),
            "by_route": dict(Counter(r.get("route", "?") for r in rows)),
            "calibration_synced": len(st.get("cal_synced_ids", []))}
