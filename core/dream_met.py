"""
Computed dream "met" state (J-1995, D-0385, docs/staged/dream_overhaul.md sec 3b).  SHADOW / RESTART-GATED.

An arc is "met" not because the dreamer SAID its unresolved_core was faced, but because the waking mind
measurably stopped returning to the tension. Per arc A dreamed on local day d, tension source T = A's
seed tension_labels + final_unresolved_core (max cosine over them), a waking thought is a QUALIFYING
RECURRENCE if  cos(T, thought) >= THETA  AND  cos(T, thought) > cos(tail, thought) for every dream tail
(last 260 chars of the dream) from the 3 days before the thought (the D-0233 injected-text rule).
A day is OBSERVED if it has >= OBS_MIN waking thoughts (origins inner_thought + study; the stored
384-float32 embedding blob is used as-is, it is the live embedder's vector, cos 1.0000 on re-embed).

    baseline   recurrence days among observed days in [d-K, d-1]         < R  -> no-baseline
    silence    any recurrence in [d+1, d+N]                              yes -> unmet
    relapse    (met so far) any recurrence in [d+N+1, d+N+M]             yes -> relapsed, else met
    pending    the N+M window has not fully elapsed yet (today's partial day never counts)

Parameters are the J-1964 in-vitro replay's (docs/lab/dream_met_replay_20261008.md, F-2596):
theta 0.61, N 3, K 25, R 2, M 3. The state logic below is a line-for-line port of
docs/lab/dream_met_replay_20261008_scripts/replay_J_1964.py::states, and
scripts/dream_met_test.py checks parity against that script.

STORES (all append-only, none of them dream_log.jsonl, which is never mutated; close_reason untouched):
  data/logs/dream_met_state.jsonl      one row per state CHANGE per arc {dream_id,state,computed_at,params,...}
  data/logs/dream_tension_mass.jsonl   one row per calendar day: every tension's chronic_mass (the ledger
                                       second instrument; the replay could not do it - archive keeps only
                                       final snapshots)
  (J-3177, D-0565: each state row also carries an additive 'ending' = met-core | rest | open | unknown, from
   core/dream_rest.py, unless RESTING_ENDING is 'off'; 'met' itself is unchanged.)
  data/logs/dream_met_carry_shadow.jsonl  written by nodes/dream_node.py: the would-have-ended carry decision
  data/logs/closure_shadow.jsonl       written by core/closure.py (J-2118, D-0423): the would-be resolution
                                       fragment for every arc whose state becomes 'met' here, plus every
                                       provisional-met carry decision. Shadow only (CLOSURE_WRITE_LIVE=False).

PROVISIONAL MET (J-2118, D-0423 sub-question 2 = J-2003 option (a)). The computed definition above needs d+N+M
(= 6) complete days, but the carry withdraws after CARRY_MAX_NIGHTS (= 3) returns, so a live carry's root arc
is always 'pending' when the carry consults it (F-2608; live: 40 of 41 carry-shadow rows 'pending', 1
'unrecorded', 0 would-end, read 2026-10-15). The carry therefore asks a CHEAPER question of the same data:

    provisional_met    baseline real (>= R recurrence days in the K-day pre-window, exactly as above) AND
                       zero qualifying recurrences on every COMPLETE observed day in [d+1, today-1], with at
                       least PROVISIONAL["min_days"] such days elapsed
    provisional_unmet  baseline real AND a qualifying recurrence on one of those elapsed days
    no-baseline / pending (nothing elapsed yet) / unobs (an elapsed or pre-window day unobserved) / noT

The computed definition is kept for the record unchanged: provisional_* is never written to
dream_met_state.jsonl (which holds only the computed states), it is returned by thread_state() for the
carry check and logged by dream_node to dream_met_carry_shadow.jsonl + closure_shadow.jsonl. Under the current
cap the rule can fire only on the third night (carried_n = 2, one complete day elapsed): the first return night
has no complete day after d yet, and the cap withdraws the thread before a fourth.

Fail-open everywhere: nothing here may stop a dream from being logged.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path

import numpy as np

from core import dream_rest as _rest      # J-3177 (D-0565): arc_ending() classification; pure, no heavy imports

logger = logging.getLogger("nascence.dream_met")

_ROOT = Path(__file__).parent.parent
_DATA = _ROOT / "data"
DREAM_LOG = _DATA / "dream_log.jsonl"
STATE_LOG = _DATA / "logs" / "dream_met_state.jsonl"
MASS_LOG = _DATA / "logs" / "dream_tension_mass.jsonl"
TENSION_STATE_FILE = _DATA / "subconscious_state.json"

PARAMS = {"theta": 0.61, "N": 3, "K": 25, "R": 2, "M": 3, "obs_min": 5,
          "tail_chars": 260, "inj_days": 3}
FINAL_STATES = ("met", "unmet", "no-baseline", "relapsed")
# J-2118 (D-0423 / J-2003 (a)): complete observed days after the root arc's day needed before a provisional
# verdict is offered at all. 1 is the only value the CARRY_MAX_NIGHTS = 3 cap leaves room for (see docstring).
PROVISIONAL = {"min_days": 1}
PROVISIONAL_STATES = ("provisional_met", "provisional_unmet")
# J-2118: when compute_states() moves an arc to 'met', run_nightly hands the arc to core/closure.py (the
# resolution-fragment SHADOW writer). False = the exact pre-J-2118 nightly (no closure call at all).
CLOSURE_HOOK = True
MAX_AGE_DAYS = 60          # arcs older than this that never became gradable stop being retried
_DAY = 86400.0

# Test seam: replaced by a deterministic fake in the hermetic test. Default = the live embedder.
_embed_fn = None


def _embed(text: str):
    fn = _embed_fn
    if fn is None:
        from core.memory import store
        fn = store._embed
    return fn(text)


def _db_path() -> Path:
    from core.memory import store          # read at call time: lab_env.isolate may repoint DB_PATH
    return Path(store.DB_PATH)


def _day(ts: float) -> int:
    return datetime.date.fromtimestamp(ts).toordinal()


# ----------------------------------------------------------------------------------------------
# Pure computation (numpy only) - port of the replay's states()
# ----------------------------------------------------------------------------------------------
def _waking_frame(W, w_ts, tail_ts, tail_V, today: int, first_day: int, p: dict):
    """The shared pre-computation (J-2118: factored out of evaluate_arcs line-for-line so provisional_arc uses the
    identical math): drop today's partial day, the injected-tail similarity per thought (max cos to the tails of
    dreams in the inj_days before it), and the observed-day predicate. Returns (W, w_ts, wday, inj, obs)."""
    w_ts = np.asarray(w_ts, dtype=float)
    wday = np.array([_day(t) for t in w_ts], dtype=np.int64) if len(w_ts) else np.zeros(0, np.int64)
    keep = wday < today
    W, w_ts, wday = W[keep], w_ts[keep], wday[keep]
    n = len(w_ts)
    # injected-text similarity per thought: max cos to tails of dreams with ts in [t - 3d, t)
    inj = np.full(n, -1.0, dtype=np.float32)
    if n and len(tail_ts):
        tail_ts = np.asarray(tail_ts, dtype=float)
        order = np.argsort(tail_ts)
        sts = tail_ts[order]
        SD = W @ np.asarray(tail_V, dtype=np.float32).T
        lo = np.searchsorted(sts, w_ts - p["inj_days"] * _DAY)
        hi = np.searchsorted(sts, w_ts)
        for i in range(n):
            if hi[i] > lo[i]:
                inj[i] = SD[i, order[lo[i]:hi[i]]].max()
    counts: dict[int, int] = {}
    for x in wday.tolist():
        counts[x] = counts.get(x, 0) + 1
    obs = lambda x: first_day <= x < today and counts.get(x, 0) >= p["obs_min"]  # noqa: E731
    return W, w_ts, wday, inj, obs


def _recurrence_days(T, W, wday, inj, theta: float) -> set[int]:
    """Ordinal days holding a QUALIFYING recurrence of tension T (cos >= theta AND closer than any injected tail)."""
    st = (np.asarray(T, dtype=np.float32) @ W.T).max(axis=0)
    q = (st >= theta) & (st > inj)
    return set(np.unique(wday[q]).tolist())


def provisional_arc(arc_ts: float, T, W, w_ts, tail_ts, tail_V, today: int, first_day: int,
                    params: dict | None = None) -> tuple[str, dict]:
    """J-2118 (D-0423 / J-2003 (a)): the carry's cheaper question of ONE arc. Same baseline test as evaluate_arcs
    (>= R recurrence days among >= max(R, 0.6K) observed pre-window days), then instead of the full N+M window:
    every complete observed day in [d+1, today-1] clean -> provisional_met; a recurrence on one -> provisional_unmet.
    Fewer than PROVISIONAL['min_days'] complete days elapsed -> pending; an elapsed day unobserved -> unobs."""
    p = dict(PARAMS, **(params or {}))
    pv = dict(PROVISIONAL, **({k[5:]: v for k, v in (params or {}).items() if k.startswith("prov_")}))
    theta, K, Rm = p["theta"], p["K"], p["R"]
    if T is None or len(T) == 0:
        return "noT", {}
    W, w_ts, wday, inj, obs = _waking_frame(W, w_ts, tail_ts, tail_V, today, first_day, p)
    d = _day(float(arc_ts))
    if d - K < first_day:
        return "unobs", {}
    elapsed = list(range(d + 1, today))
    det = {"elapsed_days": len(elapsed), "min_days": pv["min_days"]}
    if len(elapsed) < pv["min_days"]:
        return "pending", det
    rdays = _recurrence_days(T, W, wday, inj, theta) if len(w_ts) else set()
    pre_obs = [x for x in range(d - K, d) if obs(x)]
    if len(pre_obs) < max(Rm, 0.6 * K):
        return "unobs", det
    if not all(obs(x) for x in elapsed):
        return "unobs", det
    base = sum(1 for x in pre_obs if x in rdays)
    det.update({"baseline_days": base, "observed_pre_days": len(pre_obs)})
    if base < Rm:
        return "no-baseline", det
    if any(x in rdays for x in elapsed):
        return "provisional_unmet", det
    return "provisional_met", det


def evaluate_arcs(arc_ts, arc_T, W, w_ts, tail_ts, tail_V, today: int, first_day: int,
                  params: dict | None = None) -> list[tuple[str, dict]]:
    """Classify every arc. arc_T[i] is an (n,384) array or None. W/w_ts the waking thoughts, tail_ts/tail_V the
    dream tails, today = ordinal of the first day NOT yet complete, first_day = ordinal of the first waking
    thought ever. Returns [(state, detail)] with state in no-baseline|met|unmet|relapsed (final) or
    pending | met-unobs | unobs | noT (non-final; met-unobs = met so far but the relapse window was not
    observable)."""
    p = dict(PARAMS, **(params or {}))
    theta, N, K, Rm, M = p["theta"], p["N"], p["K"], p["R"], p["M"]
    arc_ts = np.asarray(arc_ts, dtype=float)
    W, w_ts, wday, inj, obs = _waking_frame(W, w_ts, tail_ts, tail_V, today, first_day, p)
    n = len(w_ts)

    out: list[tuple[str, dict]] = []
    for a in range(len(arc_ts)):
        T = arc_T[a]
        if T is None or len(T) == 0:
            out.append(("noT", {})); continue
        d = _day(arc_ts[a])
        pre = range(d - K, d)
        win = range(d + 1, d + N + 1)
        rel = range(d + N + 1, d + N + M + 1)
        if d - K < first_day or d + N + M >= today:
            out.append(("pending" if d + N + M >= today else "unobs", {})); continue
        rdays = _recurrence_days(T, W, wday, inj, theta) if n else set()
        pre_obs = [x for x in pre if obs(x)]
        if len(pre_obs) < max(Rm, 0.6 * K):
            out.append(("unobs", {})); continue
        if not all(obs(x) for x in win):
            out.append(("unobs", {})); continue
        base = sum(1 for x in pre_obs if x in rdays)
        det = {"baseline_days": base, "observed_pre_days": len(pre_obs)}
        if base < Rm:
            out.append(("no-baseline", det)); continue
        if any(x in rdays for x in win):
            out.append(("unmet", det)); continue
        rel_obs = [x for x in rel if obs(x)]
        if len(rel_obs) < 0.6 * M:
            out.append(("met-unobs", det))
        elif any(x in rdays for x in rel_obs):
            out.append(("relapsed", det))
        else:
            out.append(("met", det))
    return out


# ----------------------------------------------------------------------------------------------
# Stores
# ----------------------------------------------------------------------------------------------
def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return rows


def _append(path: Path, row: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def latest_states(path: Path | None = None) -> dict[str, dict]:
    """dream_id -> its most recent state row."""
    out: dict[str, dict] = {}
    for r in _read_jsonl(path or STATE_LOG):
        if r.get("dream_id"):
            out[r["dream_id"]] = r
    return out


def arc_tension_texts(rec: dict) -> list[str]:
    t = [str(x) for x in ((rec.get("seed") or {}).get("tension_labels") or []) if str(x).strip()]
    if (rec.get("final_unresolved_core") or "").strip():
        t.append(rec["final_unresolved_core"])
    return t


def arc_tail(rec: dict, chars: int = 260) -> str:
    return " ".join((rec.get("final_narrative") or rec.get("narrative") or "").split())[-chars:]


def carry_thread_root(dream_log: Path | None = None) -> dict | None:
    """The first arc of the currently-carried unfaced thread: walk back from the last arc by its carried_n.
    None if the last arc did not end unresolved (no thread) or the log is unreadable."""
    arcs = [r for r in _read_jsonl(dream_log or DREAM_LOG) if "close_reason" in r]
    # J-3177 (D-0565): is_thread() is exactly `ended_unresolved` unless RESTING_ENDING is 'live', when an arc that
    # ended at rest is not a thread either (the carry no longer returns it; core/dream_rest.py).
    if not arcs or not _rest.is_thread(arcs[-1]):
        return None
    back = max(0, int(arcs[-1].get("carried_n", 0) or 0))
    return arcs[max(0, len(arcs) - 1 - back)]


def thread_state(dream_log: Path | None = None, state_log: Path | None = None, *,
                 provisional: bool = True, now: float | None = None, db_path: Path | None = None) -> dict:
    """Computed state of the current carry thread's root arc, for dream_node's carry check. J-2118: when the
    recorded state is not final (pending / unrecorded), also the PROVISIONAL verdict (provisional_state /
    provisional_detail; see provisional_arc). provisional=False is the exact pre-J-2118 return shape plus
    provisional_state=None. Any failure in the provisional half leaves it 'error' and the rest intact."""
    root = carry_thread_root(dream_log)
    if root is None:
        return {"root": None, "state": "none", "provisional_state": None}
    now = time.time() if now is None else now
    row = latest_states(state_log).get(root.get("dream_id"))
    age = None
    try:
        age = _day(now) - _day(float(root.get("ts")))
    except Exception:
        pass
    out = {"root": root.get("dream_id"), "state": (row or {}).get("state", "unrecorded"),
           "root_age_days": age, "provisional_state": None}
    if provisional and out["state"] not in FINAL_STATES:
        try:
            pstate, pdet = provisional_state(root, now, dream_log=dream_log, db_path=db_path)
            out["provisional_state"], out["provisional_detail"] = pstate, pdet
        except Exception as exc:
            logger.warning("[dream_met] provisional state failed (non-fatal): %r", exc)
            out["provisional_state"], out["provisional_detail"] = "error", {"error": repr(exc)}
    return out


def provisional_state(root: dict, now: float | None = None, *, dream_log: Path | None = None,
                      db_path: Path | None = None, params: dict | None = None) -> tuple[str, dict]:
    """J-2118: provisional_arc() for one dream_log record, against the waking store (read-only) and the recent
    dream tails (the D-0233 injected-text rule applies exactly as in compute_states). Pure read; writes nothing."""
    p = dict(PARAMS, **(params or {}))
    now = time.time() if now is None else now
    today = _day(now)
    texts = arc_tension_texts(root)
    if not texts or not root.get("ts"):
        return "noT", {}
    start = float(root["ts"]) - (p["K"] + 1) * _DAY
    W, w_ts, first = _load_waking(db_path or _db_path(), start)
    if first is None:
        return "unobs", {"reason": "no waking thoughts"}
    cache: dict[str, object] = {}

    def emb(text: str):
        k = hashlib.md5(text.encode("utf-8", "ignore")).hexdigest()
        if k not in cache:
            cache[k] = _embed(text)
        return cache[k]

    arcs = [r for r in _read_jsonl(dream_log or DREAM_LOG) if "close_reason" in r and r.get("ts")]
    tails = [(float(r["ts"]), emb(arc_tail(r, p["tail_chars"]))) for r in arcs
             if float(r["ts"]) >= start - p["inj_days"] * _DAY and arc_tail(r, p["tail_chars"])]
    tails = [(t, v) for t, v in tails if v is not None]
    vs = [v for v in (emb(t) for t in texts) if v is not None]
    T = np.stack(vs) if vs else None
    return provisional_arc(float(root["ts"]), T, W, w_ts, [t for t, _ in tails],
                           np.stack([v for _, v in tails]) if tails else np.zeros((0, 384), np.float32),
                           today, _day(first), params)


# ----------------------------------------------------------------------------------------------
# Nightly driver
# ----------------------------------------------------------------------------------------------
def _load_waking(db_path: Path, since_ts: float):
    c = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True, timeout=30.0)
    try:
        first = c.execute("SELECT MIN(timestamp) FROM memory_fragments WHERE origin IN ('inner_thought','study') "
                          "AND embedding IS NOT NULL").fetchone()[0]
        rows = c.execute("SELECT timestamp, embedding FROM memory_fragments WHERE origin IN ('inner_thought','study') "
                         "AND embedding IS NOT NULL AND timestamp >= ? ORDER BY timestamp", (since_ts,)).fetchall()
    finally:
        c.close()
    ts, vecs = [], []
    for t, blob in rows:
        v = np.frombuffer(blob, dtype=np.float32)
        if v.shape[0] == 384:
            ts.append(float(t)); vecs.append(v)
    W = np.stack(vecs) if vecs else np.zeros((0, 384), np.float32)
    return W, np.array(ts, dtype=float), (float(first) if first is not None else None)


def compute_states(now: float | None = None, *, dream_log: Path | None = None, db_path: Path | None = None,
                   state_log: Path | None = None, params: dict | None = None, write: bool = True) -> dict:
    """Evaluate every not-yet-final recent arc and append a row for each state CHANGE. Never mutates
    dream_log.jsonl. Idempotent: running twice in a night appends nothing the second time."""
    p = dict(PARAMS, **(params or {}))
    now = time.time() if now is None else now
    today = _day(now)
    arcs = [r for r in _read_jsonl(dream_log or DREAM_LOG) if "close_reason" in r and r.get("ts")]
    prior = latest_states(state_log)
    cand = [r for r in arcs
            if today - _day(float(r["ts"])) <= MAX_AGE_DAYS
            and (prior.get(r.get("dream_id")) or {}).get("state") not in FINAL_STATES
            and arc_tension_texts(r)]
    summary = {"candidates": len(cand), "appended": 0, "states": {}, "newly_met": []}
    if not cand:
        return summary
    start = min(float(r["ts"]) for r in cand) - (p["K"] + 1) * _DAY
    W, w_ts, first = _load_waking(db_path or _db_path(), start)
    if first is None:
        return summary
    cache: dict[str, object] = {}

    def emb(text: str):
        k = hashlib.md5(text.encode("utf-8", "ignore")).hexdigest()
        if k not in cache:
            cache[k] = _embed(text)
        return cache[k]

    tails = [(float(r["ts"]), emb(arc_tail(r, p["tail_chars"]))) for r in arcs
             if float(r["ts"]) >= start - p["inj_days"] * _DAY and arc_tail(r, p["tail_chars"])]
    tails = [(t, v) for t, v in tails if v is not None]
    arc_T = []
    for r in cand:
        vs = [emb(t) for t in arc_tension_texts(r)]
        vs = [v for v in vs if v is not None]
        arc_T.append(np.stack(vs) if vs else None)
    res = evaluate_arcs([float(r["ts"]) for r in cand], arc_T, W, w_ts,
                        [t for t, _ in tails], np.stack([v for _, v in tails]) if tails else np.zeros((0, 384), np.float32),
                        today, _day(first), p)
    paramrow = {k: p[k] for k in ("theta", "N", "K", "R", "M", "obs_min")}
    for r, (state, det) in zip(cand, res):
        summary["states"][state] = summary["states"].get(state, 0) + 1
        row_state = "pending" if state == "met-unobs" else state
        if row_state not in FINAL_STATES and row_state != "pending":
            continue                       # unobs / noT: nothing honest to record
        if (prior.get(r["dream_id"]) or {}).get("state") == row_state:
            continue
        state_row = {"dream_id": r["dream_id"], "state": row_state, "computed_at": now, "params": paramrow,
                     "arc_ts": r["ts"], "detail": det}
        if _rest.mode() != "off":
            # J-3177 (D-0565): additive key. 'met' means the waking mind stopped returning; this says what kind of
            # ending the arc had (met-core | rest | open | unknown), so a met that follows a rest is told apart from
            # one that follows a stall. Read by core/closure.py (record_dream_met row) and the shadow read.
            state_row["ending"] = _rest.arc_ending(r)
        if write:
            _append(state_log or STATE_LOG, state_row)
        summary["appended"] += 1
        if row_state == "met":
            # J-2118 (D-0423): the judge's verdict just became 'met' for this arc. Hand the arc (and the root of its
            # carry thread: walk back carried_n rows in the log) to run_nightly for core/closure.py. Recorded here
            # only; the closure call itself is run_nightly's, so compute_states stays a pure judge.
            try:
                idx = arcs.index(r)
                root = arcs[max(0, idx - max(0, int(r.get("carried_n", 0) or 0)))]
            except Exception:
                root = r
            summary["newly_met"].append({"arc": r, "root_id": root.get("dream_id"), "state_row": state_row})
    return summary


def log_tension_mass(now: float | None = None, *, state_file: Path | None = None,
                     mass_log: Path | None = None, top: int = 40) -> bool:
    """Append one row per local calendar day with every tension's chronic_mass (largest `top`). Returns whether
    a row was written."""
    now = time.time() if now is None else now
    ml = Path(mass_log or MASS_LOG)
    prev = _read_jsonl(ml)
    if prev and _day(float(prev[-1].get("ts", 0))) == _day(now):
        return False
    st = json.loads(Path(state_file or TENSION_STATE_FILE).read_text(encoding="utf-8"))
    tens = sorted(st.get("tensions", []) or [], key=lambda t: float(t.get("chronic_mass", 0) or 0), reverse=True)
    rows = [{"label": (t.get("label") or "")[:120], "chronic_mass": round(float(t.get("chronic_mass", 0) or 0), 3),
             "members": len(t.get("member_event_ids", []) or t.get("members", []) or [])} for t in tens[:top]]
    _append(ml, {"ts": now, "n_tensions": len(tens), "tensions": rows})
    return True


def run_nightly(now: float | None = None) -> dict:
    """The dream_node hook: compute states, then log the tension masses. Each half fail-open on its own."""
    out: dict = {}
    try:
        out["states"] = compute_states(now)
    except Exception as exc:
        logger.warning("[dream_met] state compute failed (non-fatal): %r", exc)
        out["states_error"] = repr(exc)
    if CLOSURE_HOOK:
        # J-2118 (D-0423 A, closure law, dream arm): for every arc the judge just marked 'met', core/closure.py
        # composes the would-be resolution fragment and appends it to data/logs/closure_shadow.jsonl. The judge
        # (this module) and the writer (closure.py) stay separate modules; closure writes NOTHING to the memory
        # DB while CLOSURE_WRITE_LIVE is False. Fail-open: a closure failure can never undo the state rows above.
        try:
            from core import closure as _closure
            out["closure"] = [_closure.record_dream_met(m["arc"], m["state_row"], root_id=m["root_id"], now=now)
                              for m in (out.get("states") or {}).get("newly_met", [])]
        except Exception as exc:
            logger.warning("[dream_met] closure hook failed (non-fatal): %r", exc)
            out["closure_error"] = repr(exc)
    if CLOSURE_HOOK and _rest.mode() != "off":
        # J-3177 (D-0565): the closure writer READS A REST AS A CLOSE candidate: one kind='rest_close' shadow row per
        # recent rest arc, certified only by an independent judge, nothing written to the memory DB. Fail-open.
        try:
            from core import closure as _closure
            out["rest_closes"] = _closure.record_rest_closes(now=now)
        except Exception as exc:
            logger.warning("[dream_met] rest-close hook failed (non-fatal): %r", exc)
            out["rest_close_error"] = repr(exc)
    try:
        out["mass_logged"] = log_tension_mass(now)
    except Exception as exc:
        logger.warning("[dream_met] tension-mass log failed (non-fatal): %r", exc)
        out["mass_error"] = repr(exc)
    return out
