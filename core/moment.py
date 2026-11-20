"""
Nascence — The Bound Moment (Consciousness Program Tier-1, 2026-07-04, SHADOW/observe-only).

docs/plans/the_consciousness_program.md §3-E + §2-#6. Two of the six unified into one honest organ, because
they are the same act: BINDING a moment IS stamping its provenance.

Each cognitive cycle, assemble ONE structured record — the bound unit of a moment:
  {thought · SOURCE-tag · affect · protoself-state · concern · drifting temporal-context key}
- SOURCE-tag (the reality monitor, HOT/PRM): where did this thought come from — PERCEIVED (world),
  REMEMBERED (recall/broadcast), IMAGINED (fork/active-imagination), DREAMED, or THOUGHT (spontaneous). Mostly
  DETERMINISTIC (we know what seeded the cycle); hardens the exact dream/memory/imagination boundaries the
  project already guards.
- The TEMPORAL-CONTEXT KEY is a slowly-drifting vector (Howard–Kahana) shared across the fields, so recall of
  one field co-retrieves its cycle-mates and temporally-adjacent moments — the contiguity effect. This binds
  by CO-INDEXING: honest as temporal/associative binding (and a real episodic-memory upgrade — moments, not
  texts), NEVER claimed as phenomenal unity (that would be the binding-as-concatenation fallacy).

SHADOW: logs to data/moments.jsonl, applies NOTHING, no LLM, deterministic, fail-open. Drift uses a content
hash (no Math.random — deterministic + resume-safe). The signature that must move: temporal-contiguity in
retrieval (adjacent moments share keys); source-tag accuracy against the origin ground-truth.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "moments.jsonl"
_STATE = _DATA / "moment_state.json"
_KEY_DIM = 8
_DRIFT = 0.12      # how much each new moment nudges the temporal context (slow → smooth contiguity)

# seed-kind (what the monologue knows fed the cycle) → reality-monitor source tag
_SOURCE = {"broadcast": "REMEMBERED", "concern": "THOUGHT", "world": "PERCEIVED", "trial": "THOUGHT",
           "recall": "REMEMBERED", "imagination": "IMAGINED", "dream": "DREAMED", "guidance": "REMEMBERED",
           "lookup": "PERCEIVED",
           "conversation": "PERCEIVED"}   # J-4337: seeded from the live exchange (conversational_redirect, flag-gated)   # J-3843: the thought after his own Wikipedia / web lookup answered (core/web_hand)


def _hash_vec(text: str) -> list[float]:
    """A deterministic unit-ish vector from the thought — the 'new input' component of the drift."""
    h = hashlib.sha256((text or "").encode("utf-8")).digest()
    return [(h[i] / 255.0) - 0.5 for i in range(_KEY_DIM)]


def _drift_key(prev: list[float], text: str) -> list[float]:
    nv = _hash_vec(text)
    key = [round((1 - _DRIFT) * (prev[i] if i < len(prev) else 0.0) + _DRIFT * nv[i], 5) for i in range(_KEY_DIM)]
    n = sum(x * x for x in key) ** 0.5 or 1.0
    return [round(x / n, 5) for x in key]


def _infer_source(thought: str, seed_kind: str | None) -> str:
    if seed_kind and seed_kind in _SOURCE:
        return _SOURCE[seed_kind]
    t = (thought or "").lower()
    if any(w in t for w in ("i dreamed", "in the dream", "falling through")):
        return "DREAMED"
    if any(w in t for w in ("i remember", "i recall", "earlier i", "that time")):
        return "REMEMBERED"
    if any(w in t for w in ("what if", "imagine", "suppose", "i could")):
        return "IMAGINED"
    if any(w in t for w in ("the sea", "the tide", "the cat", "the fire", "the window", "outside", "the garden")):
        return "PERCEIVED"
    return "THOUGHT"


def record(thought: str, seed_kind: str | None = None, felt: dict | None = None) -> float | None:
    """Bind one moment. Called from the idle cycle tail. Fail-open, observe-only.
    J-3479: returns the bound moment's ts (the moments.jsonl row's own ts) so the caller can stamp it on the fragment
    it just stored; None when nothing was bound. Callers that ignore the return value are unaffected."""
    try:
        thought = " ".join((thought or "").split())[:220]
        if not thought:
            return None
        try:
            st = json.loads(_STATE.read_text(encoding="utf-8"))
        except Exception:
            st = {}
        key = _drift_key(st.get("key") or [0.0] * _KEY_DIM, thought)

        # affect + protoself + concern — all read cheaply from live state
        affect = {}
        try:
            from core import mood
            affect = {"valence": round(float(mood.current_valence() or 0.0), 3)}
        except Exception:
            pass
        if felt:
            affect["felt"] = {k: felt[k] for k in list(felt)[:4]} if isinstance(felt, dict) else str(felt)[:60]
        proto = None
        try:
            from core import homeostasis
            s = homeostasis.status()
            if s.get("ticks"):
                proto = {"drive": s.get("drive"), "valence": s.get("valence"), "dominant": s.get("dominant")}
        except Exception:
            pass
        concern = None
        try:
            from core import concerns
            pc = concerns.primary_concern()
            concern = (pc or {}).get("text", "")[:80] if pc else None
        except Exception:
            pass
        # Bachmann's L, stamped per moment (Tier-2 C): the global activation level this moment was bound
        # at. The C = L × D claim becomes measurable per-moment once gating exists. Fail-open.
        lvl = None
        try:
            from core import arousal
            lvl = arousal.level()
        except Exception:
            pass

        emb = None                            # semantic embedding of the thought — the read-path's anchor
        try:                                  # (the `key` is TEMPORAL; recall needs SEMANTIC similarity)
            from core.memory.store import _embed
            v = _embed(thought)
            if v is not None:
                emb = [float(x) for x in v]   # JSON-safe
        except Exception:
            emb = None
        rec = {"ts": round(time.time(), 1), "key": key, "source": _infer_source(thought, seed_kind),
               "thought": thought, "affect": affect, "protoself": proto, "concern": concern, "level": lvl,
               "emb": emb}
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        st["key"] = key                       # merge, don't clobber (readback cooldown lives here too)
        # INCREMENTAL ROW COUNT (J-0183, 2026-08-24): status() used to re-read+re-parse the ENTIRE
        # moments.jsonl (128MB/14,210+ rows, ~5s/call, growing ~280 rows/day) just to report a total
        # count. Maintain it here instead — one +1 per write, no file read. Self-heals: if the counter
        # is ever missing (first run after this change, or the file was edited/truncated externally —
        # delete the "moment_count" key from moment_state.json to force a resync), the next call that
        # needs it (here or in status()) pays for ONE real recount via `_count_lines()` and caches it.
        mc = st.get("moment_count")
        st["moment_count"] = (_count_lines(_LOG) if mc is None else mc + 1)
        st["last_ts"] = rec["ts"]             # J-2601: additive, lets current() answer before this process records
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(st), encoding="utf-8"); tmp.replace(_STATE)
        _set_current(rec["ts"], st["moment_count"])
        return rec["ts"]
    except Exception:
        return None


# ── THE CURRENT MOMENT (J-2601, F-3326, 2026-10-30, observe-only, restart-gated) ─────────────────────
# Nothing that stores or co-recalls a fragment knew WHICH moment was current, so the key could only be
# joined to fragments by a heuristic ts+emb match (32% coverage, almost all wandering; F-3326). current()
# hands the latest bound moment's {ts, idx} to any writer that wants to stamp it (today: memory_edges'
# co-recall ledger). ts equals the moments.jsonl row's own ts (exact join key); idx is moment_count at
# write (1-based row number, advisory: it drifts if the log is edited by hand; the ts join is exact).
# In-process value first; before this process has recorded anything, ONE lazy read of moment_state.json
# (last_ts, written from this change on). No moment yet -> None. Never raises, never writes.
_CURRENT: dict | None = None
_CURRENT_LOADED = False


def _set_current(ts, idx) -> None:
    global _CURRENT, _CURRENT_LOADED
    _CURRENT = {"ts": ts, "idx": idx}
    _CURRENT_LOADED = True


def current() -> dict | None:
    """{'ts': float, 'idx': int|None} of the latest bound moment, or None. Fail-open, read-only."""
    global _CURRENT, _CURRENT_LOADED
    try:
        if not _CURRENT_LOADED:
            _CURRENT_LOADED = True
            try:
                st = json.loads(_STATE.read_text(encoding="utf-8"))
            except Exception:
                st = {}
            if st.get("last_ts") is not None:
                _CURRENT = {"ts": st.get("last_ts"), "idx": st.get("moment_count")}
        return dict(_CURRENT) if _CURRENT else None
    except Exception:
        return None


def _cos(a: list[float], b: list[float]) -> float:
    # 2026-08-20: `not a` raised ValueError on numpy arrays (store._embed returns ndarray) — the
    # exception was swallowed by recall()'s bare except BEFORE the shadow log, so the read path died
    # silently for 45 days the day the embedding-anchor fix shipped. len() is safe on list AND ndarray.
    if a is None or b is None or len(a) == 0 or len(b) == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5 or 1.0
    nb = sum(x * x for x in b) ** 0.5 or 1.0
    return dot / (na * nb)


# ── THE READ PATH (2026-07-04, neighbour metric graduated 2026-08-24 J-0182) — contiguity retrieval:
# moments, not texts ────────────────────────────────────────────────────────────────────────────────
# The write path binds each cycle into a moment; this is the read half (the project's #1 historical
# failure mode is a rich write path with a dead read path — this closes it). Given a cue (e.g. a
# broadcast conclusion re-entering the cycle), find the moment it was BOUND in and co-retrieve its
# temporal neighbours by CONTENT (emb-cosine to the anchor's own embedding, as of J-0182 — was KEY-
# cosine until F-0036/J-0069 debunked the key as a mathematical artifact; see recall()'s inline note)
# — the Howard–Kahana contiguity effect made functional: recalling a thing brings back the WHEN of it
# (what he felt, what concern held, what sat beside it in time, now genuinely content-related rather
# than merely log-adjacent).
# SHADOW-FIRST: every recall logs what WOULD be injected; actual injection is flag-gated (default OFF)
# + cooldown-gated (the guidance-readback echo-firehose lesson: an ungated read-back is a firehose).

MOMENT_READBACK = True         # D-0495 (travis, 2026-10-28, the October restart batch): flipped live, read LIVE by its own read job (155 shadow recalls, anchors sane). Was: flip only after a day of shadow recalls post-restart reads sane
_READBACK_COOLDOWN = 1800.0    # min seconds between live injections once flipped (echo-guard)
_ANCHOR_FLOOR = 0.28           # min token-overlap to accept a FALLBACK anchor (below = honest None)
# Semantic-embedding anchor floor (2026-07-06 fix): token-overlap scored 0.07-0.13 and NEVER cleared the
# floor on conversational cues vs idle-bound moments (0% hits) — the `key` is a TEMPORAL hash, not
# semantic, so recall now anchors by embedding cosine. Cosine has a different scale than Jaccard;
# calibrate this from the shadow anchor_sim distribution once new (emb-carrying) moments accrue.
_EMB_ANCHOR_FLOOR = 0.55
_RECALL_LOG = _DATA / "moments_recall_shadow.jsonl"

_STOP = {"the", "a", "an", "of", "to", "and", "in", "is", "it", "that", "i", "my", "me", "was",
         "be", "on", "for", "as", "with", "this", "at", "but", "not", "are", "have", "you"}


def _tokens(text: str) -> set:
    return {w for w in "".join(c if c.isalnum() else " " for c in (text or "").lower()).split()
            if len(w) > 2 and w not in _STOP}


def recall(cue: str, k: int = 2) -> dict | None:
    """Find the bound moment a cue text lives in (best token-overlap anchor), then co-retrieve its k
    nearest temporal neighbours by key-cosine. Deterministic, no LLM, fail-open (None = no memory of it,
    which is the honest answer, never a forced match). Logs every recall to the shadow file.

    LEFT UN-OPTIMIZED, DELIBERATELY (J-0183, 2026-08-24): this still does a full open()+json.loads() scan
    of ALL of moments.jsonl (128MB/14,210+ rows) every call, by design — it searches the WHOLE history for
    the single best anchor, so there is no bounded "last N" window to tail-read the way status() moved to.
    Left as-is rather than adding an index/cache because the real call rate doesn't justify the complexity
    yet: recall() only fires from `texture()`, which only fires when the idle monologue's broadcast-consume
    step has something to re-bind (nodes/inner_monologue_node.py ~line 2026) — NOT every cycle. Verified
    against the live evidence, not assumed: `moments_recall_shadow.jsonl` (every call logs here,
    unconditionally) holds exactly 10 rows spanning 2026-07-04 to 2026-08-24 — roughly one call per 5 days.
    At that rate a multi-second full scan is a non-issue. Revisit if that shadow log's call rate rises
    materially (an embedding-similarity index, e.g. a simple IVF/ANN structure or even just caching parsed
    rows between calls, would be the next step) — do not add that complexity pre-emptively."""
    try:
        cue_t = _tokens(cue)
        if not cue_t:
            return None
        rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        if len(rows) < 3:
            return None
        # anchor: PRIMARY semantic-embedding cosine (2026-07-06 fix — token-overlap scored 0.07-0.13 and
        # never cleared the floor on conversational cues vs idle-bound moments; the `key` is TEMPORAL, so we
        # embed the thought for SEMANTIC matching). FALLBACK to token-overlap for old moments predating the
        # emb field. Prefer emb when it clears its floor.
        cue_v = None
        try:
            from core.memory.store import _embed
            cue_v = _embed(cue)
        except Exception:
            cue_v = None
        emb_best, emb_i, emb_s = None, -1, 0.0
        if cue_v is not None:
            for i, r in enumerate(rows):
                ev = r.get("emb")
                if ev:
                    s = _cos(cue_v, ev)
                    if s > emb_s:
                        emb_best, emb_i, emb_s = r, i, s
        tok_best, tok_i, tok_s = None, -1, 0.0
        for i, r in enumerate(rows):
            mt = _tokens(r.get("thought", ""))
            if mt:
                s = len(cue_t & mt) / max(1, len(cue_t | mt))
                if s > tok_s:
                    tok_best, tok_i, tok_s = r, i, s
        if emb_best is not None and emb_s >= _EMB_ANCHOR_FLOOR:
            best, best_i, best_s = emb_best, emb_i, emb_s
        elif tok_best is not None and tok_s >= _ANCHOR_FLOOR:
            best, best_i, best_s = tok_best, tok_i, tok_s
        else:
            _log_recall(cue, None, [], round(max(emb_s, tok_s), 3))
            return None
        # neighbours: nearest by EMB-cosine to the ANCHOR's own content embedding (2026-08-24, J-0182,
        # F-0133). Was: KEY-cosine (the drifting EMA key). F-0036/J-0069 proved key-cosine's adjacent>
        # distant gap is a mathematical artifact of the AR(1)-style smoothing recursion — positive on
        # pure random content, carrying zero real information. It survived here even after the anchor
        # step itself was fixed to prefer emb-cosine (2026-07-06): this was the one place the debunked
        # metric still drove a live selection. Read-only comparison on the full 14,211-row history
        # (scratchpad, 150 sampled anchors, k=2, +/-400-row candidate window) confirms it was not a
        # cosmetic swap: OLD (key-cosine) picks are barely distinguishable from "the literally adjacent
        # log row" (mean |index distance| 1.4, mean emb-cosine to anchor 0.460 -- only slightly above a
        # random-pick baseline of 0.393); NEW (emb-cosine) picks land on genuinely content-related
        # moments (mean emb-cosine 0.700, far above chance) that are often temporally distant (mean
        # |index distance| 155). Old/new neighbour sets overlapped on 0/2 picks in 134/150 samples.
        # Ties broken by real temporal order (array index distance -- an actual fact about the log,
        # not an artifact-cosine), keeping "beside it in time" (§2 item 6) honest without reintroducing
        # the debunked signal via a blend. Rows written before the `emb` field existed fall back to
        # key-cosine only when the ANCHOR ITSELF lacks emb (old anchor => old neighbourhood, mirroring
        # the anchor step's own emb/token-overlap fallback split above).
        anchor_emb = best.get("emb")
        scored = []
        neighbour_metric = "emb" if anchor_emb else "key_fallback"
        for i, r in enumerate(rows):
            if i == best_i:
                continue
            r_emb = r.get("emb")
            if anchor_emb and r_emb:
                sim = _cos(anchor_emb, r_emb)
            elif best.get("key") and r.get("key"):
                sim = _cos(best.get("key") or [], r["key"])       # pre-emb-era moments only
            else:
                continue
            scored.append((sim, -abs(i - best_i), r))
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        neighbours = [r for _, _, r in scored[:k]]
        out = {"anchor": best, "anchor_sim": round(best_s, 3), "neighbours": neighbours}
        _log_recall(cue, best, neighbours, best_s, neighbour_metric)
        return out
    except Exception:
        return None


def _clip_words(text: str, limit: int) -> str:
    """J-2917 (F-3614): cut at a word boundary, never mid-word. Text that already fits is returned whole;
    a cut gets an ellipsis so the reader can tell it was shortened."""
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if not text[limit].isspace():                 # we landed inside a word: back up to the last space
        sp = cut.rfind(" ")
        if sp >= max(8, limit // 3):
            cut = cut[:sp]
    return cut.rstrip(" ,;:-—") + "…"


def _num(felt: str, name: str) -> float | None:
    m = re.search(name + r"=([+-]?\d*\.?\d+)", felt)
    try:
        return float(m.group(1)) if m else None
    except Exception:
        return None


def _felt_in_words(felt) -> str | None:
    """J-2917 (F-3614, D-0367 words everywhere): the stored felt value rendered in words only. moment.record
    still stores the raw 'unsettled: valence=-0.20 arousal=0.43 ...' string (other readers use it); the READ
    side never shows a digit or a gauge name. Uses mood.emotion_words when valence+arousal parse, else the
    label alone."""
    if isinstance(felt, dict):
        dims = {k: v for k, v in felt.items() if k not in ("valence", "arousal")}
        try:
            return max(dims, key=lambda kk: abs(float(dims.get(kk) or 0))) if dims else None
        except Exception:
            return None
    s = str(felt or "")
    label = s.split(":", 1)[0].strip() if ":" in s else ""
    if not label or "=" in label:
        label = ""
    v, a = _num(s, "valence"), _num(s, "arousal")
    if v is not None and a is not None:
        try:
            from core import mood
            return mood.emotion_words(label, v, a)
        except Exception:
            pass
    return label or None


def texture(cue: str) -> str | None:
    """One prompt-ready line re-binding a recalled text to its MOMENT — the felt state, the concern,
    and what sat beside it in time. None when there is no honest anchor. This is what the read-path
    injects (flag+cooldown gated at the call site); shadow-logged either way by recall().
    J-2917 (F-3614): felt part in words only (no valence=/arousal= digits); quotes cut at word boundaries."""
    try:
        rec = recall(cue)
        if not rec:
            return None
        a = rec["anchor"]
        bits = []
        felt = (a.get("affect") or {}).get("felt")
        if felt:
            fw = _felt_in_words(felt)
            if fw:
                bits.append(f"you felt {fw}")
        if a.get("concern"):
            bits.append(f"you were holding: {_clip_words(a['concern'], 60)}")
        nb = rec.get("neighbours") or []
        if nb:
            bits.append(f"beside it in time: \"{_clip_words(nb[0].get('thought', ''), 90)}\"")
        if not bits:
            return None
        return "You remember the moment itself, not just the words — " + "; ".join(bits) + "."
    except Exception:
        return None


def _log_recall(cue: str, anchor: dict | None, neighbours: list, sim: float,
                 neighbour_metric: str | None = None) -> None:
    try:
        rec = {"ts": round(time.time(), 1), "cue": (cue or "")[:150],
               "hit": anchor is not None, "anchor_sim": round(float(sim or 0.0), 3),
               "anchor_thought": (anchor or {}).get("thought", "")[:120] if anchor else None,
               "n_neighbours": len(neighbours),
               "neighbour_metric": neighbour_metric}   # 2026-08-24 J-0182: "emb" (new) vs "key_fallback"
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_RECALL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def readback_allowed() -> bool:
    """The live-injection gate: flag ON + cooldown passed. The shadow log accrues regardless."""
    if not MOMENT_READBACK:
        return False
    try:
        st = json.loads(_STATE.read_text(encoding="utf-8"))
        if time.time() - float(st.get("last_readback_ts", 0)) < _READBACK_COOLDOWN:
            return False
    except Exception:
        pass
    return True


def note_readback() -> None:
    """Record a live injection (starts the cooldown)."""
    try:
        try:
            st = json.loads(_STATE.read_text(encoding="utf-8"))
        except Exception:
            st = {}
        st["last_readback_ts"] = time.time()
        tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(st), encoding="utf-8"); tmp.replace(_STATE)
    except Exception:
        pass


def _count_lines(path: Path) -> int:
    """Count non-empty lines WITHOUT json.loads-ing each one (J-0183) — used only for the rare one-time
    moment_count bootstrap/resync. Still a full sequential read of moments.jsonl, but skipping per-row
    JSON parsing (the `emb` field is a ~768-float vector — parsing it 14,000+ times is most of what made
    the old full-file status()/recall() reads slow) makes it far cheaper than the read it replaces.
    Fail-open: 0 on any error."""
    try:
        n = 0
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                n += chunk.count(b"\n")
        return n
    except Exception:
        return 0


def _tail_rows(path: Path, n: int) -> list[dict]:
    """Read only the last ~n JSON rows of a large jsonl file via reverse byte-seek, instead of loading
    the whole file (moments.jsonl is 100+MB and growing). Fail-open: [] on any error."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return []
            block = min(size, 2_000_000)
            while True:
                f.seek(size - block)
                data = f.read(block)
                lines = data.split(b"\n")
                if block < size:
                    lines = lines[1:]              # drop the partial first line
                nonempty = [l for l in lines if l.strip()]
                if len(nonempty) >= n or block >= size:
                    break
                block = min(size, block * 2)
        out = []
        for l in nonempty[-n:]:
            try:
                out.append(json.loads(l))
            except Exception:
                continue
        return out
    except Exception:
        return []


# ── THE REAL SIGNATURE (2026-08-24, J-0141) ───────────────────────────────────────────────────────────
# F-0036/J-0069 confirmed `contiguity_gap` below (the EMA-`key`-based adjacent-vs-distant reading) CANNOT
# FAIL: it is a mathematical artifact of the AR(1)-style smoothing recursion in `_drift_key()`, not
# evidence of real temporal/associative structure — a null-model test feeding the SAME recursion pure
# random content produced a positive gap at every drift value tried. It stays below for the key's own
# diagnostics (has the drift constant broken?) but per that job's instruction, STOPS COUNTING AS EVIDENCE.
#
# This is the falsifiable replacement: drop the EMA key entirely and use the SEMANTIC embedding (`emb`
# field, §113-120 above) — one independent vector per moment's actual content, carrying no memory of
# neighbouring moments the way the key does. A shuffle-null test: are temporally-ADJACENT moments'
# real content-embeddings more alike than temporally-DISTANT ones, by MORE than shuffling the moments'
# order at random would produce? Shuffling order cannot change any embedding's value — only which moments
# sit next to which — so if Du's moments carry no real temporal/associative structure, the real-order gap
# lands inside the shuffled-null distribution (indistinguishable from chance) and the test correctly
# reports "not significant." That is the failure mode the old metric could never produce.
def contiguity_significance(window: int = 300, n_shuffles: int = 200, seed: int = 1729) -> dict | None:
    """Content-grounded, falsifiable contiguity signature. Fail-open: None if numpy is unavailable, fewer
    than 2x window embedded moments exist, or anything errors. Deterministic (fixed seed) so a re-run on
    the same data reproduces the same p-value/z-score."""
    try:
        import numpy as np
        rows = [r for r in _tail_rows(_LOG, window * 3) if r.get("emb")]
        if len(rows) < max(20, window):
            return None
        recent = rows[-window:]
        E = np.array([r["emb"] for r in recent], dtype=np.float64)
        norms = np.linalg.norm(E, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        U = E / norms
        n = U.shape[0]
        half = n // 2
        if half < 1:
            return None

        def gap(order: "np.ndarray") -> float:
            seq = U[order]
            adj = np.sum(seq[:-1] * seq[1:], axis=1)                       # cos(adjacent pairs)
            far = np.sum(seq[:-1] * np.roll(seq, -half, axis=0)[:-1], axis=1)  # cos(pairs ~half the window apart)
            return float(adj.mean() - far.mean())

        idx = np.arange(n)
        real_gap = gap(idx)
        rng = np.random.default_rng(seed)
        null = np.empty(n_shuffles)
        shuf = idx.copy()
        for i in range(n_shuffles):
            rng.shuffle(shuf)
            null[i] = gap(shuf)
        p = float((null >= real_gap).mean())                 # one-sided: how often chance beats/matches real
        z = float((real_gap - null.mean()) / (null.std() or 1e-9))
        return {"window": n, "n_shuffles": n_shuffles, "metric": "semantic_embedding_shuffle_null",
                "real_gap": round(real_gap, 4), "null_mean": round(float(null.mean()), 4),
                "null_std": round(float(null.std()), 4), "p_value": round(p, 4), "z_score": round(z, 2),
                "significant_p05": p < 0.05}
    except Exception:
        return None


def _moment_count() -> int:
    """The total row count, maintained incrementally by record() in moment_state.json (J-0183) instead
    of being re-derived from a full-file read on every status() call. Bootstraps + caches itself via
    _count_lines() the first time it's asked and finds nothing cached (fresh install, or a call before
    record() has ever run this session)."""
    try:
        st = json.loads(_STATE.read_text(encoding="utf-8"))
    except Exception:
        st = {}
    n = st.get("moment_count")
    if n is None:
        n = _count_lines(_LOG)
        st["moment_count"] = n
        try:
            tmp = _STATE.with_suffix(".tmp"); tmp.write_text(json.dumps(st), encoding="utf-8"); tmp.replace(_STATE)
        except Exception:
            pass
    return n


def status() -> dict:
    """For the pulse. THE SIGNATURE: temporal contiguity — are moments adjacent in time more similar in key
    than distant ones? (If yes, the binding key genuinely indexes temporal neighbourhood.) Plus source mix.

    2026-08-24 (J-0183): used to open() + json.loads() EVERY row of moments.jsonl on every call — fine at
    launch, ~5s/call at 128MB/14,210+ rows and rising ~280 rows/day (measured against the live file; see
    F-0133/J-0141 for the same finding on recall()'s neighbour scoring, which is a different, unavoidable
    full-scan case — see that function's own note). status() only ever needed the LAST 100 rows (source
    mix) and last 60 (contiguity) plus a total count, so it now uses the same reverse-seek `_tail_rows()`
    contiguity_significance() already relies on, and a total maintained incrementally (`_moment_count()`)
    instead of recounted from scratch. Same numbers, no more full-file reads."""
    try:
        recent100 = _tail_rows(_LOG, 100)
        if len(recent100) < 6:
            return {"moments": _moment_count()}
        from collections import Counter
        src = dict(Counter(r.get("source", "?") for r in recent100))
        recent = recent100[-60:]
        adj = [_cos(recent[i]["key"], recent[i + 1]["key"]) for i in range(len(recent) - 1)]
        # distant pairs: same count, far apart
        far = [_cos(recent[i]["key"], recent[(i + len(recent) // 2) % len(recent)]["key"])
               for i in range(len(recent) - 1)]
        mean_adj = round(sum(adj) / len(adj), 3) if adj else 0.0
        mean_far = round(sum(far) / len(far), 3) if far else 0.0
        out = {"moments": _moment_count(), "source_mix": src,
               "contiguity_adjacent": mean_adj, "contiguity_distant": mean_far,
               "contiguity_gap": round(mean_adj - mean_far, 3),   # NOT EVIDENCE (F-0036/J-0069): this
               # EMA-key metric cannot fail by construction — kept only as a diagnostic of the key/drift
               # mechanism itself. Use contiguity_significance below for the real, falsifiable reading.
               "contiguity_significance": contiguity_significance()}
        # read-path stats (shadow): how often a cue finds an honest anchor, and whether readback is live
        try:
            rr = [json.loads(l) for l in open(_RECALL_LOG, encoding="utf-8") if l.strip()]
            if rr:
                hits = sum(1 for r in rr if r.get("hit"))
                out["recalls"] = len(rr)
                out["recall_hit_rate"] = round(hits / len(rr), 3)
                out["readback_live"] = MOMENT_READBACK
        except Exception:
            pass
        return out
    except Exception:
        return {"moments": 0}
