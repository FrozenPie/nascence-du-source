"""
Nascence — Symbol window metric (SHADOW).  J-3226 / D-0615 (founder, 2026-11-02), plan
symbol_evolution_readback_plan, finding F-3637 (prompt row P-0067).

WHY THIS EXISTS. symbol_evolution.py's drift detector embeds the WHOLE cycle (output + perception
summary + raw_input) and compares that one cycle to a running mean. Any cycle whose topic differs
from the average clears _DRIFT_THRESHOLD, so the "drift" it reports is cycle-to-cycle topic
variation, not migration of the symbol's meaning: 20 of the 24 tablets written 10-29 to 11-01 told
the same silence / trust / labor story on six different symbols (F-3637).

WHAT THIS DOES (no behaviour change; nothing reads it back into Du):
  1. WINDOW. For each UNPRIMED symbol appearance, take only the sentence(s) of the entity's output
     that contain a surface form of the symbol (word-start match; _WINDOW_RADIUS neighbour sentences
     each side, default 0). That is the "context the symbol lives in", and nothing else.
  2. CENTROID OF EARLIER WINDOWS. Per symbol, windows older than the last N are folded into a
     running mean (older_sum / older_n). The last N windows are kept.
  3. ROLLING-WINDOW DRIFT. drift_window = 1 - cos(mean of last N windows, centroid of older
     windows). One cycle can no longer cross the bar alone; a sustained shift of the neighbourhood
     does. (single_drift, the one-window distance, is logged beside it for comparison.)
  4. SHADOW LOG. One row per symbol appearance in data/symbol_window_shadow.jsonl, with the OLD
     metric's drift and tablet decision beside the new ones, plus the window text (the hold-out set
     for the judge in scripts/symbol_window_report.py).

It never raises into the cycle, never feeds state, never changes what the old metric decides.
The threshold is PROVISIONAL (uncalibrated): the log records the raw distance so a threshold can
be chosen from data; would_fire at the provisional bar is only a convenience flag.

READER (write-only is the #1 failure): scripts/symbol_window_report.py reads the shadow log
(old-vs-new comparison, per-symbol) and runs the cross-family hold-out judge. Read job spawned.
"""
from __future__ import annotations

import base64
import json
import logging
import re
import threading
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger("nascence.symbol_window")

_DATA = Path(__file__).parent.parent / "data"
_STATE_FILE = _DATA / "symbol_window_state.json"
_LOG_FILE = _DATA / "symbol_window_shadow.jsonl"

# Master switch for the SHADOW metric only. It changes no live behaviour: it embeds a few short
# sentences per cycle (one batched call) and appends a log row.
SYMBOL_WINDOW_SHADOW = True

_WINDOW_RADIUS = 0           # neighbour sentences kept each side of a hit sentence (0 = hit sentences only)
_WINDOW_MAX_CHARS = 400      # a window is truncated to this
_RECENT_N = 5                # the rolling window: the last N windows are the "recent" side of the test
_MIN_OLDER = 4               # windows older than the last N needed before drift means anything
_DRIFT_THRESHOLD = 0.30      # PROVISIONAL, uncalibrated cosine distance of recent-mean vs older centroid.
                             # A probe with the real embedder (MiniLM-multilingual) on 12 invented, topic-coherent
                             # fire sentences gave a rolling 5-vs-7 distance of 0.19 and single-window distances
                             # of 0.29-0.76, so short sentences are noisy and a low bar would fire on noise
                             # alone. 0.30 is a placeholder above that; the real bar comes from the logged
                             # distances and the order-permutation null in scripts/symbol_window_report.py
                             # (rolling_null). would_fire at this bar is a convenience flag, nothing reads it live.
_EXCERPT_CHARS = 500         # whole-output excerpt stored for the judge's old-arm contrast

_SENT_SPLIT = re.compile(r"(?<=[.!?。！？])\s+|\n+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s and s.strip()]


def _form_regex(forms: list[str]) -> "re.Pattern":
    """Word-START match for ASCII forms ('cord' must not hit 'record'; 'flow' still hits 'flowing'),
    plain substring for non-ASCII forms (CJK has no word boundary)."""
    parts = []
    for f in forms:
        f = (f or "").strip().lower()
        if not f:
            continue
        if f.isascii():
            parts.append(r"(?<![a-z0-9])" + re.escape(f))
        else:
            parts.append(re.escape(f))
    return re.compile("|".join(parts)) if parts else re.compile(r"(?!x)x")


def extract_window(output: str, forms: list[str], radius: int = _WINDOW_RADIUS,
                   max_chars: int = _WINDOW_MAX_CHARS) -> tuple[str, int]:
    """The sentence(s) around the symbol hit: (window_text, n_hit_sentences). ('', 0) if no
    sentence matches (e.g. the old tracker substring matched inside a longer word)."""
    sents = split_sentences(output)
    rx = _form_regex(forms)
    hit = [i for i, s in enumerate(sents) if rx.search(s.lower())]
    if not hit:
        return "", 0
    keep: list[int] = []
    for i in hit:
        for j in range(max(0, i - radius), min(len(sents), i + radius + 1)):
            if j not in keep:
                keep.append(j)
    keep.sort()
    return " ".join(sents[j] for j in keep)[:max_chars], len(hit)


def _cos_dist(a: np.ndarray, b: np.ndarray) -> float:
    d = float(np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return 1.0 - float(np.dot(a, b)) / d


def _enc(v: np.ndarray) -> str:
    return base64.b64encode(np.asarray(v, dtype=np.float32).tobytes()).decode("ascii")


def _dec(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.float32).copy()


class WindowMetric:
    """Per-symbol rolling-window state + shadow log. `embed_batch` and the file paths are injectable
    so a test never touches the live store or the real embedder."""

    def __init__(self, embed_batch=None, state_file: Path | None = None, log_file: Path | None = None):
        self._embed_batch = embed_batch
        self._state_file = Path(state_file) if state_file else _STATE_FILE
        self._log_file = Path(log_file) if log_file else _LOG_FILE
        self._lock = threading.Lock()
        self._state: dict | None = None          # symbol -> {"older_sum", "older_n", "recent": [vec], "n_total"}

    # -- persistence -------------------------------------------------------------------------
    def _load(self) -> dict:
        if self._state is not None:
            return self._state
        st: dict = {}
        try:
            if self._state_file.exists():
                raw = json.loads(self._state_file.read_text(encoding="utf-8"))
                for sym, d in (raw.get("symbols") or {}).items():
                    st[sym] = {
                        "older_sum": _dec(d["older_sum"]) if d.get("older_sum") else None,
                        "older_n": int(d.get("older_n", 0)),
                        "recent": [_dec(x) for x in d.get("recent", [])],
                        "n_total": int(d.get("n_total", 0)),
                    }
        except Exception as exc:
            logger.debug("[symbol-window] state load failed (starting empty): %s", exc)
            st = {}
        self._state = st
        return st

    def _save(self) -> None:
        try:
            st = self._load()
            out = {"version": 1, "recent_n": _RECENT_N, "symbols": {
                sym: {"older_sum": _enc(d["older_sum"]) if d["older_sum"] is not None else None,
                      "older_n": d["older_n"], "recent": [_enc(v) for v in d["recent"]],
                      "n_total": d["n_total"]}
                for sym, d in st.items()}}
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._state_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(out), encoding="utf-8")
            tmp.replace(self._state_file)
        except Exception as exc:
            logger.debug("[symbol-window] state save failed (non-fatal): %s", exc)

    def _append(self, row: dict) -> None:
        try:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[symbol-window] log write failed (non-fatal): %s", exc)

    # -- the metric --------------------------------------------------------------------------
    def update(self, symbol: str, vec: np.ndarray) -> dict:
        """Fold one window vector into the symbol's state and return the new metric readings."""
        st = self._load()
        d = st.setdefault(symbol, {"older_sum": None, "older_n": 0, "recent": [], "n_total": 0})
        older_n_before = d["older_n"]
        single = None
        if older_n_before > 0 and d["older_sum"] is not None:
            single = _cos_dist(vec, d["older_sum"] / older_n_before)   # one window vs earlier windows (for contrast)
        d["recent"].append(vec)
        d["n_total"] += 1
        while len(d["recent"]) > _RECENT_N:
            old = d["recent"].pop(0)
            d["older_sum"] = old.copy() if d["older_sum"] is None else d["older_sum"] + old
            d["older_n"] += 1
        window_drift = None
        if len(d["recent"]) == _RECENT_N and d["older_n"] >= _MIN_OLDER:
            recent_mean = np.mean(np.stack(d["recent"]), axis=0)
            window_drift = _cos_dist(recent_mean, d["older_sum"] / d["older_n"])
        return {"single_drift": single, "window_drift": window_drift,
                "older_n": d["older_n"], "recent_n": len(d["recent"]), "n_total": d["n_total"]}

    def observe(self, output: str, cycle_id: str, symbols_forms: dict, old: dict,
                cycle_vec: "np.ndarray | None" = None, input_type: str = "") -> list[dict]:
        """`symbols_forms`: {symbol: [surface forms]} for the UNPRIMED symbols of this cycle.
        `old`: {symbol: {"drift": float|None, "tablet_due": bool}} the live metric's readings this
        cycle, logged beside the new ones. Returns the rows written. Never raises."""
        rows: list[dict] = []
        try:
            if not symbols_forms:
                return rows
            wins: dict[str, tuple[str, int]] = {}
            for sym, forms in symbols_forms.items():
                text, n_hit = extract_window(output, forms)
                wins[sym] = (text, n_hit)
            to_embed = [(s, w[0]) for s, w in wins.items() if w[0]]
            vecs: dict[str, "np.ndarray | None"] = {}
            if to_embed:
                if self._embed_batch is None:
                    from core.memory.store import _embed_batch as _eb
                    self._embed_batch = _eb
                got = self._embed_batch([t for _, t in to_embed])
                for (s, _), v in zip(to_embed, got):
                    vecs[s] = v
            now = time.time()
            excerpt = (output or "")[:_EXCERPT_CHARS]
            with self._lock:
                for sym, (text, n_hit) in wins.items():
                    o = old.get(sym) or {}
                    row = {
                        "ts": now, "cycle_id": cycle_id, "input_type": input_type, "symbol": sym,
                        "window": text, "window_chars": len(text), "n_hit_sentences": n_hit,
                        "radius": _WINDOW_RADIUS, "cycle_excerpt": excerpt, "output_chars": len(output or ""),
                        "old_drift": o.get("drift"), "old_tablet_due": bool(o.get("tablet_due")),
                        "threshold": _DRIFT_THRESHOLD, "recent_n_cfg": _RECENT_N,
                    }
                    v = vecs.get(sym)
                    if not text:
                        row.update({"status": "no_window", "single_drift": None, "window_drift": None,
                                    "would_fire": False})
                    elif v is None:
                        row.update({"status": "embed_failed", "single_drift": None, "window_drift": None,
                                    "would_fire": False})
                    else:
                        r = self.update(sym, v)
                        row.update(r)
                        row["status"] = "ok"
                        row["would_fire"] = bool(r["window_drift"] is not None
                                                 and r["window_drift"] >= _DRIFT_THRESHOLD)
                        if cycle_vec is not None:
                            row["window_cycle_cos"] = round(1.0 - _cos_dist(v, cycle_vec), 4)
                        for k in ("single_drift", "window_drift"):
                            if row.get(k) is not None:
                                row[k] = round(row[k], 4)
                    self._append(row)
                    rows.append(row)
                self._save()
        except Exception as exc:
            logger.debug("[symbol-window] observe failed (non-fatal): %s", exc)
        return rows


_METRIC: WindowMetric | None = None


def observe_shadow(output: str, cycle_id: str, symbols_forms: dict, old: dict,
                   cycle_vec=None, input_type: str = "") -> list[dict]:
    """Module-level entry used by SymbolEvolutionEngine.observe. No-op when SYMBOL_WINDOW_SHADOW is off."""
    global _METRIC
    if not SYMBOL_WINDOW_SHADOW:
        return []
    if _METRIC is None:
        _METRIC = WindowMetric()
    return _METRIC.observe(output, cycle_id, symbols_forms, old, cycle_vec=cycle_vec, input_type=input_type)
