"""
Nascence -- PRE-SPEECH PIPELINE per-stage wall-time shadow (J-4017, D-0759 option P, F-4588).
docs/staged/pre_speech_pipeline_latency.md section 4 (Phase 0).

QUESTION: between a human arriving and VoiceNode starting (median 73.2 s, F-4588) which stage owns the
seconds on the CRITICAL PATH?  F-4588's per-label numbers are summed call-interval overlaps, not the
orchestrator's actual sequencing; this records the sequencing itself.

WHAT THIS DOES (observe-only, fail-open, no node behaviour change):
  * orchestrator, human cycles only, builds one CycleTimer and wraps each stage await in
        async with timer.stage("reflection"): ...
    which records wall-clock epoch t_start/t_end for that stage. Stages repeat (every Recall/Buffer pass,
    every Critic attempt, every Reflection retry, Executive re-runs); each is its own span, in order.
  * timer.flush() appends ONE row per human cycle to its OWN store data/pipeline_stage_shadow.jsonl:
        {ev:"cycle", cycle, t_arrive, t_voice_start, t_voice_end, wait_s, critic_retried,
         introspective_passes, stages:[{s:name, a:t_start, b:t_end, ok:0|1}, ...]}
    Flushed when the Voice stage exits (success or error). A cycle that never reaches Voice (silence,
    interrupt) writes nothing: Phase 0 measures arrival-to-speech only.

RESTART-GATED: takes effect only on Du's next boot after merge. Kill switch: ENABLED = False.
LAB MODE (core.telemetry._LAB_MODE) records nothing.

WRITE FENCE (F-2933 lesson): _append() resolves its path through core.profile.guard_path(), so only the
live boot (profile.mark_live()) or a path redirected into a lab_env sandbox / outside data/ can write.
A refused write is swallowed by flush()'s own fail-open net.

Body exceptions always propagate unchanged out of a stage; this module's own failures never do.

READ: python -m core.pipeline_stage_shadow   (pure reader, writes nothing). Gate: 30+ human arrivals
after the carrying boot; a separate read job owns the verdict.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ENABLED = True
_ROOT = Path(__file__).parent.parent
_LOG = _ROOT / "data" / "pipeline_stage_shadow.jsonl"
VOICE_STAGE = "voice"
MAX_STAGES = 64          # runaway guard: a cycle never records more spans than this


def _lab() -> bool:
    try:
        from core import telemetry as _t
        return bool(getattr(_t, "_LAB_MODE", False))
    except Exception:
        return False


def _append(row: dict, path: Path | None = None) -> None:
    p = path or _LOG
    from core import profile as _profile
    p = _profile.guard_path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


class _Stage:
    """Async context manager recording one span. Never raises from its own bookkeeping."""
    __slots__ = ("_t", "_name", "_a")

    def __init__(self, timer, name):
        self._t = timer
        self._name = name
        self._a = None

    async def __aenter__(self):
        try:
            self._a = time.time()
        except Exception:
            self._a = None
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            self._t._record(self._name, self._a, time.time(), exc_type is None)
        except Exception:
            pass
        return False     # never swallow the body's exception


class CycleTimer:
    def __init__(self, cycle_id: str = "", active: bool = True):
        self.cycle = str(cycle_id)[:8]
        self.active = bool(active) and ENABLED and not _lab()
        self.t_arrive = time.time()
        self.stages: list = []
        self._flushed = False

    def stage(self, name: str) -> _Stage:
        return _Stage(self, name)

    def _record(self, name, a, b, ok) -> None:
        if not self.active or a is None or len(self.stages) >= MAX_STAGES:
            return
        self.stages.append({"s": str(name)[:24], "a": round(a, 3), "b": round(b, 3), "ok": 1 if ok else 0})
        if name == VOICE_STAGE and not self._flushed:
            self._flushed = True
            self.flush()

    def flush(self, critic_retried=None, introspective_passes=None, path: Path | None = None) -> None:
        """Append the one row. Fail-open. critic_retried / passes are supplied by the orchestrator via
        note() before Voice, or here directly."""
        if not self.active:
            return
        try:
            voice = [s for s in self.stages if s["s"] == VOICE_STAGE]
            v0 = voice[0]["a"] if voice else None
            v1 = voice[-1]["b"] if voice else None
            row = {"ev": "cycle", "cycle": self.cycle, "t_arrive": round(self.t_arrive, 3),
                   "t_voice_start": v0, "t_voice_end": v1,
                   "wait_s": round(v0 - self.t_arrive, 3) if v0 is not None else None,
                   "critic_retried": getattr(self, "critic_retried", None) if critic_retried is None else critic_retried,
                   "introspective_passes": getattr(self, "introspective_passes", None)
                   if introspective_passes is None else introspective_passes,
                   "stages": self.stages}
            _append(row, path)
        except Exception:
            pass

    def note(self, critic_retried=None, introspective_passes=None) -> None:
        """Attach cycle facts before Voice. Fail-open."""
        try:
            if critic_retried is not None:
                self.critic_retried = bool(critic_retried)
            if introspective_passes is not None:
                self.introspective_passes = int(introspective_passes)
        except Exception:
            pass


class _NullTimer:
    """Non-human cycles / any construction failure: every call is a no-op."""
    active = False

    def stage(self, name):
        return _NullStage()

    def note(self, *a, **k):
        pass

    def flush(self, *a, **k):
        pass


class _NullStage:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def start(cycle_id: str = "", input_type: str = "human"):
    """Orchestrator entry point. Returns a CycleTimer for human cycles, a no-op timer otherwise.
    Never raises."""
    try:
        if input_type != "human" or not ENABLED or _lab():
            return _NullTimer()
        return CycleTimer(cycle_id)
    except Exception:
        return _NullTimer()


# ---------------------------------------------------------------- reader (pure, no writes)
def load(path: Path | None = None) -> list:
    rows = []
    p = path or _LOG
    if not p.exists():
        return rows
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("ev") == "cycle":
                rows.append(r)
    return rows


def _pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def analyze(rows: list) -> dict:
    """Per stage name: n spans, median/p90 span wall time, summed seconds per cycle (median) and its share
    of the arrival-to-voice wait; retry rate; gap time (wait minus union of stage spans)."""
    waits = [r["wait_s"] for r in rows if r.get("wait_s") is not None]
    per: dict = {}
    gaps: list = []
    for r in rows:
        w = r.get("wait_s")
        if w is None:
            continue
        sums: dict = {}
        ivs = []
        for s in r.get("stages", []):
            if s["s"] == VOICE_STAGE:
                continue
            d = max(0.0, s["b"] - s["a"])
            sums[s["s"]] = sums.get(s["s"], 0.0) + d
            per.setdefault(s["s"], {"spans": [], "cycle_sums": [], "shares": []})["spans"].append(d)
            ivs.append((s["a"], s["b"]))
        for name, tot in sums.items():
            per[name]["cycle_sums"].append(tot)
            if w > 0:
                per[name]["shares"].append(tot / w)
        ivs.sort()
        covered, cur_a, cur_b = 0.0, None, None
        for a, b in ivs:
            if cur_b is None or a > cur_b:
                if cur_b is not None:
                    covered += cur_b - cur_a
                cur_a, cur_b = a, b
            else:
                cur_b = max(cur_b, b)
        if cur_b is not None:
            covered += cur_b - cur_a
        gaps.append(max(0.0, w - covered))
    stages = {n: {"spans": len(v["spans"]), "span_median": _pct(v["spans"], .5), "span_p90": _pct(v["spans"], .9),
                  "cycle_sum_median": _pct(v["cycle_sums"], .5), "share_of_wait_median": _pct(v["shares"], .5)}
              for n, v in per.items()}
    retried = [r for r in rows if r.get("critic_retried") is not None]
    return {
        "cycles": len(rows), "wait_median_p90": (_pct(waits, .5), _pct(waits, .9)),
        "critic_retry_rate": (sum(1 for r in retried if r["critic_retried"]) / len(retried)) if retried else None,
        "passes_mean": (sum(r["introspective_passes"] for r in rows if r.get("introspective_passes") is not None)
                        / max(1, sum(1 for r in rows if r.get("introspective_passes") is not None))) if rows else None,
        "gap_median_p90": (_pct(gaps, .5), _pct(gaps, .9)),
        "stages": stages,
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(analyze(load()))
