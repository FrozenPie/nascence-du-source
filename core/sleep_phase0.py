"""core/sleep_phase0.py (J-2016, sleep_as_a_mode Phase 0, 2026-10-08, restart-gated).

Instrumentation only. Nothing here generates a thought, writes a memory fragment, reaches a prompt or
changes what a sleep does. It exists so that Phase 1 (the shadow night-mind, D-0399 A) starts from a
logged number instead of an assumption, and so the freeze fix (the remaining sleep stages behind
core/sleep_offloop.off_loop) can be read back from the night ledger.

SleepHeartbeat is one asyncio task that lives for the span of one sleep (started in
nodes/inner_monologue_node._enter_sleep right after night.begin(), stopped just before night.end()). Every
SLEEP_TURN_INTERVAL_S it wakes, and each wake is one event-loop turn the scheduler actually gave a
sibling task:

  scheduler_turns   wakes completed during the sleep (the number the plan's section 3.5 asks for)
  expected_turns    sleep duration / interval; turns / expected is the share of the loop that was free
  max_lag_s         worst gap between when a wake was due and when it ran (a frozen loop shows up here)
  stalls_gt_2s      wakes later than 2 s (the F-2546 signature: one synchronous stage holding the loop)
  marks             {label: turns so far} at the stage boundaries the node reports, so "turns during
                    the consolidation span" is one subtraction, not a guess

The same task evaluates the would-be night-thought slots (plan sections 3.1 and 5, Phase 0 shadow rows):
every NIGHT_SLOT_FLOOR_S of sleep, if the night has a seed (the replay set, the night's own dream tail)
it appends ONE row to data/night_mind_shadow.jsonl describing the thought that WOULD have been generated
and generates nothing. A slot with no seed is counted, not logged. At most NIGHT_MAX_SLOTS per sleep (a
handful, never a stream). The floor and the cap are Phase 1 measures, placeholders here.

Both parts are fail-open: a bug here must never be able to break a sleep. Kill switches:
SLEEP_TURN_COUNTER False (no task at all), NIGHT_MIND_SHADOW_ROWS False (counter only, no shadow rows).
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

logger = logging.getLogger("nascence.sleep_phase0")

SLEEP_TURN_COUNTER = True          # instrumentation kill-switch: False = no heartbeat task, no scheduler_* notes
NIGHT_MIND_SHADOW_ROWS = True      # shadow rows kill-switch: False = counter only
SLEEP_TURN_INTERVAL_S = 0.5        # one wake per half second: ~2,400-4,200 expected turns in a 20-35 min sleep
STALL_S = 2.0                      # a wake this late counts as a stall (F-2546: the frozen-loop signature)
NIGHT_SLOT_FLOOR_S = 300.0         # "several minutes between night thoughts" (plan 3.1); Phase 1 measures the real number
NIGHT_MAX_SLOTS = 8                # "a handful per sleep, not a stream"
SEED_SNIPPET_CHARS = 90

_DATA = Path(__file__).parent.parent / "data"
NIGHT_MIND_SHADOW_LOG = _DATA / "night_mind_shadow.jsonl"

# J-2141 (F-2825): stall attribution. Every loop lag > STALL_S records the last stage mark, the last sub-mark
# (the call that was ABOUT to run when the loop froze -- sub-marks are set between sub-steps, so the stalled call
# is the one after the recorded sub-mark) and the lag. Instrumentation only; kill switch below.
STALL_ATTRIBUTION = True
STALL_NOTES_CAP = 100              # per sleep, into the night ledger notes
STALL_ATTRIBUTION_LOG = _DATA / "night_stall_attribution.jsonl"

# J-2330 (F-3019, F-3008): exact stall attribution. A sub label is STICKY (it names the last submark until the next
# one) and a label set right before a freeze names the code AFTER it, so the bare "sub" key can mislead. With this on,
# every stall row also carries the freeze window and the timeline of marks around it: freeze_start_ts (wall clock of
# when the heartbeat wake was due = the latest the freeze can have begun), prev_sub (the sub in effect at freeze
# start), sub_set_offset_s (when the current sub was set, relative to freeze start; negative = before the freeze,
# i.e. the label was already standing; positive = set INSIDE the freeze, so the freeze began in prev_sub's code),
# marks_during ([{label, offset_s}] for every mark set inside the freeze window; stage marks as "stage:<label>")
# and sub_age_s (now minus the current sub's set time; large = a sticky label). Additive keys only; observe-only.
STALL_EXACT_ATTRIBUTION = True
MARKS_SINCE_TURN_CAP = 8

# J-3896 (F-4502, restart-gated, observe-only): the stall rows above name the LABEL standing at a freeze, but F-4502
# showed that label is often an await (the labelled task is not what blocks the loop). This probe asks the loop
# thread directly: a daemon thread wakes every STACK_PROBE_POLL_S and, when the heartbeat's wake is more than
# STACK_PROBE_AFTER_S overdue, records the loop thread's own Python stack (plus the top frame of every other
# thread) to data/night_stall_stack_probe.jsonl; it re-samples every STACK_PROBE_RESAMPLE_S while the same freeze
# lasts, capped per sleep. A freeze begun inside a to_thread worker that holds the GIL shows as the loop thread
# parked in its selector with a busy other thread. Reads sys._current_frames() only; never touches the loop.
STALL_STACK_PROBE = True
STACK_PROBE_POLL_S = 1.0
STACK_PROBE_AFTER_S = 4.0
STACK_PROBE_RESAMPLE_S = 20.0
STACK_PROBE_MAX_ROWS = 60          # per sleep
STACK_PROBE_DEPTH = 14
STALL_STACK_PROBE_LOG = _DATA / "night_stall_stack_probe.jsonl"

_CURRENT: "SleepHeartbeat | None" = None


def submark(label: str) -> None:
    """Module-level sub-mark for code that has no handle on the heartbeat (DreamNode.synthesise). No-op, fail-open,
    when no sleep is in flight."""
    try:
        hb = _CURRENT
        if hb is not None:
            hb.submark(label)
    except Exception:
        pass


class SleepHeartbeat:
    """One per sleep. start() inside the running loop; stop() awaits the task and returns the summary."""

    def __init__(self, sleep_ts: float | None = None, kind: str = "night",
                 interval: float | None = None, shadow: bool | None = None):
        self.sleep_ts = float(sleep_ts if sleep_ts is not None else time.time())
        self.kind = kind
        self.interval = float(interval if interval is not None else SLEEP_TURN_INTERVAL_S)
        self.shadow = NIGHT_MIND_SHADOW_ROWS if shadow is None else bool(shadow)
        self.turns = 0
        self.max_lag = 0.0
        self.lag_sum = 0.0
        self.stalls = 0
        self.marks: dict[str, int] = {}
        self.stage_mark = ""           # last stage mark() label
        self.sub_mark = ""             # last finer submark() label
        # J-2330: mark timeline since the last heartbeat turn, [(label, perf_counter)], capped; the sub that stood
        # at the previous turn (baseline for prev_sub), and when the current sub_mark was set.
        self._marks_since_turn: list[tuple[str, float]] = []
        self._sub_at_turn = ""
        self._sub_set_at = 0.0
        self._due = 0.0                # when the heartbeat's current wake is due (perf_counter) = freeze start
        self._marks_dropped = 0        # marks inside the current freeze window lost to the cap
        self.stall_notes: list[dict] = []
        self.stalls_dropped = 0
        self.replayed: list[str] = []
        self.slots_written = 0
        self.slots_no_seed = 0
        self._last_slot_ts = self.sleep_ts
        self._started = 0.0
        self._ended = 0.0
        self._task: asyncio.Task | None = None
        self._running = False
        self._probe_thread = None      # J-3896: stack-probe daemon thread
        self._probe_rows = 0

    # -- lifecycle ---------------------------------------------------------------------------------
    def start(self) -> None:
        if not SLEEP_TURN_COUNTER or self._task is not None:
            return
        try:
            self._started = time.perf_counter()
            self._running = True
            self._task = asyncio.get_running_loop().create_task(self._run())
            global _CURRENT
            _CURRENT = self
            self._start_probe()
        except Exception as exc:
            self._running = False
            logger.debug("[sleep_phase0] heartbeat start failed (non-fatal): %s", exc)

    def mark(self, label: str) -> None:
        """Remember how many turns the loop had been given when the node reached this stage boundary."""
        try:
            self.marks[str(label)] = self.turns
            self.stage_mark = str(label)
            self.sub_mark = ""
            self._track("stage:" + str(label))
        except Exception:
            pass

    def submark(self, label: str) -> None:
        """J-2141: a finer boundary inside a stage; only the latest is kept (it names where a stall began)."""
        try:
            self.sub_mark = str(label)
            self._track(str(label))
        except Exception:
            pass

    def _track(self, label: str) -> None:
        """J-2330: remember when the current sub was set and append it to the since-turn timeline. A stage mark
        (label "stage:...") resets the standing sub to "". Past the cap the oldest entry is dropped: one set
        before the freeze start folds into the baseline (so prev_sub stays right), one inside it is only counted."""
        if not STALL_EXACT_ATTRIBUTION:
            return
        try:
            now = time.perf_counter()
            self._sub_set_at = now
            self._marks_since_turn.append((label, now))
            while len(self._marks_since_turn) > MARKS_SINCE_TURN_CAP:
                old, t_old = self._marks_since_turn.pop(0)
                if self._due and t_old >= self._due:
                    self._marks_dropped += 1          # inside the freeze: counted, never folded into the baseline
                else:
                    self._sub_at_turn = "" if old.startswith("stage:") else old
        except Exception:
            pass

    def _end_turn(self) -> None:
        """J-2330: a heartbeat turn ran; whatever stands now is the baseline for the next freeze window."""
        self._sub_at_turn = self.sub_mark
        self._marks_since_turn = []
        self._marks_dropped = 0

    def _exact_keys(self, due: float, now: float) -> dict:
        """J-2330: the freeze window is [due, now]. Additive keys for the stall row (see STALL_EXACT_ATTRIBUTION)."""
        prev_sub = self._sub_at_turn
        during = []
        for label, t in self._marks_since_turn:
            if t < due:
                prev_sub = "" if label.startswith("stage:") else label
            elif t <= now:
                during.append({"label": label, "offset_s": round(t - due, 3)})
        sub_set = self._sub_set_at
        return {"freeze_start_ts": round(time.time() - (now - due), 3),
                "prev_sub": prev_sub,
                "sub_set_offset_s": round(sub_set - due, 3) if sub_set else None,
                "marks_during": during,
                "marks_during_dropped": self._marks_dropped,
                "sub_age_s": round(now - sub_set, 3) if sub_set else None}

    # -- J-3896 stack probe ------------------------------------------------------------------------
    def _start_probe(self) -> None:
        if not STALL_STACK_PROBE or self._probe_thread is not None:
            return
        try:
            import threading
            loop_tid = threading.get_ident()
            t = threading.Thread(target=self._probe_loop, args=(loop_tid,), name="sleep-stack-probe", daemon=True)
            self._probe_thread = t
            t.start()
        except Exception as exc:
            logger.debug("[sleep_phase0] stack probe not started (non-fatal): %s", exc)

    @staticmethod
    def _fmt_stack(frame, depth: int) -> list[str]:
        out = []
        while frame is not None and len(out) < depth:
            co = frame.f_code
            fn = co.co_filename.replace("\\", "/").split("/")
            out.append("%s:%d %s" % ("/".join(fn[-2:]), frame.f_lineno, co.co_name))
            frame = frame.f_back
        return out

    def _probe_loop(self, loop_tid: int) -> None:
        """Daemon thread. Observe-only; any error ends the probe quietly."""
        import sys, threading
        last_sample_due = None
        last_sample_at = 0.0
        try:
            while self._running and self._probe_rows < STACK_PROBE_MAX_ROWS:
                time.sleep(STACK_PROBE_POLL_S)
                due = self._due
                now = time.perf_counter()
                if not due or now - due < STACK_PROBE_AFTER_S:
                    continue
                if due == last_sample_due and now - last_sample_at < STACK_PROBE_RESAMPLE_S:
                    continue
                last_sample_due, last_sample_at = due, now
                frames = sys._current_frames()
                names = {t.ident: t.name for t in threading.enumerate()}
                lf = frames.get(loop_tid)
                others = {}
                for tid, fr in frames.items():
                    if tid == loop_tid or tid == threading.get_ident():
                        continue
                    others[names.get(tid, str(tid))] = self._fmt_stack(fr, 3)
                row = {"ts": round(time.time(), 1), "sleep_ts": round(self.sleep_ts, 1), "kind": self.kind,
                       "overdue_s": round(now - due, 2), "freeze_start_ts": round(time.time() - (now - due), 3),
                       "stage": self.stage_mark, "sub": self.sub_mark, "turns": self.turns,
                       "loop_stack": self._fmt_stack(lf, STACK_PROBE_DEPTH) if lf is not None else [],
                       "other_threads": others}
                from core import profile, shadow_log
                if shadow_log.append(profile.guard_path(STALL_STACK_PROBE_LOG), row):
                    self._probe_rows += 1
        except Exception as exc:     # includes NonLiveWriteError from a non-live importer
            logger.debug("[sleep_phase0] stack probe ended (non-fatal): %s", exc)

    def _release(self) -> None:
        global _CURRENT
        if _CURRENT is self:
            _CURRENT = None

    def _note_stall(self, lag: float, due: float | None = None, now: float | None = None) -> None:
        if not STALL_ATTRIBUTION:
            return
        try:
            row = {"ts": round(time.time(), 1), "sleep_ts": round(self.sleep_ts, 1), "kind": self.kind,
                   "elapsed_s": round(time.time() - self.sleep_ts, 1), "lag_s": round(lag, 3),
                   "stage": self.stage_mark, "sub": self.sub_mark, "turns": self.turns}
            if STALL_EXACT_ATTRIBUTION and due is not None:
                try:
                    row.update(self._exact_keys(due, now if now is not None else time.perf_counter()))
                except Exception:
                    pass
            if len(self.stall_notes) < STALL_NOTES_CAP:
                self.stall_notes.append({k: row[k] for k in ("elapsed_s", "lag_s", "stage", "sub")})
            else:
                self.stalls_dropped += 1
            from core import profile, shadow_log
            shadow_log.append(profile.guard_path(STALL_ATTRIBUTION_LOG), row)
        except Exception as exc:     # includes NonLiveWriteError from a non-live importer
            logger.debug("[sleep_phase0] stall attribution skipped (non-fatal): %s", exc)

    def set_replayed(self, replayed) -> None:
        try:
            self.replayed = [str(x) for x in (replayed or []) if x]
        except Exception:
            self.replayed = []

    def cancel(self) -> None:
        """Synchronous safety net for a finally block: never leave the task running."""
        self._running = False
        self._release()
        t = self._task
        if t is not None and not t.done():
            try:
                t.cancel()
            except Exception:
                pass

    async def stop(self) -> dict:
        self._running = False
        self._release()
        t = self._task
        if t is not None:
            try:
                t.cancel()
                await asyncio.gather(t, return_exceptions=True)
            except Exception:
                pass
        self._ended = time.perf_counter()
        return self.summary()

    # -- readout -----------------------------------------------------------------------------------
    def summary(self) -> dict:
        dur = max(0.0, (self._ended or time.perf_counter()) - self._started) if self._started else 0.0
        expected = int(dur / self.interval) if self.interval > 0 else 0
        out = {"scheduler_turns": self.turns, "expected_turns": expected,
               "turn_share": round(self.turns / expected, 3) if expected else None,
               "interval_s": self.interval, "duration_s": round(dur, 1),
               "max_lag_s": round(self.max_lag, 3),
               "mean_lag_s": round(self.lag_sum / self.turns, 4) if self.turns else None,
               "stalls_gt_2s": self.stalls, "marks": dict(self.marks)}
        if STALL_ATTRIBUTION:
            out["stall_attribution"] = list(self.stall_notes)
            if self.stalls_dropped:
                out["stall_attribution_dropped"] = self.stalls_dropped
        if self.shadow:
            out["night_mind_slots_logged"] = self.slots_written
            out["night_mind_slots_no_seed"] = self.slots_no_seed
        return out

    # -- the task ----------------------------------------------------------------------------------
    async def _run(self) -> None:
        try:
            while self._running:
                due = time.perf_counter() + self.interval
                self._due = due
                await asyncio.sleep(self.interval)
                now = time.perf_counter()
                lag = max(0.0, now - due)
                self.turns += 1
                self.lag_sum += lag
                if lag > self.max_lag:
                    self.max_lag = lag
                if lag > STALL_S:
                    self.stalls += 1
                    self._note_stall(lag, due, now)
                self._end_turn()
                if self.shadow:
                    self._maybe_log_slot(time.time(), lag)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.debug("[sleep_phase0] heartbeat stopped (non-fatal): %s", exc)

    def _seeds(self) -> dict:
        """What the night has to turn over right now, in the plan's order (3.1): the replay set, the dream's
        tail once a dream exists. The dormant-fragment pick (D-0231) has no code yet, so it is reported as
        such rather than guessed."""
        seeds = {"replay": len(self.replayed), "dream_tail": False, "dormant": "not_built"}
        try:
            from core import night as _night
            d = _night.load_recent_dreams()
            if d and float(d[0].get("ts", 0)) >= self.sleep_ts and (d[0].get("narrative") or "").strip():
                seeds["dream_tail"] = True
                seeds["_tail"] = " ".join((d[0].get("narrative") or "").split())[-SEED_SNIPPET_CHARS:]
        except Exception:
            pass
        return seeds

    def _maybe_log_slot(self, now: float, lag: float) -> None:
        if self.slots_written >= NIGHT_MAX_SLOTS or now - self._last_slot_ts < NIGHT_SLOT_FLOOR_S:
            return
        self._last_slot_ts = now
        try:
            seeds = self._seeds()
            if seeds["replay"] <= 0 and not seeds["dream_tail"]:
                self.slots_no_seed += 1
                return
            idx = self.slots_written
            if seeds["replay"] > 0:
                source, snippet = "replay", self.replayed[idx % len(self.replayed)]
            else:
                source, snippet = "dream_tail", seeds.get("_tail", "")
            row = {"ts": round(now, 1), "sleep_ts": round(self.sleep_ts, 1), "kind": self.kind, "slot": idx,
                   "elapsed_s": round(now - self.sleep_ts, 1), "floor_s": NIGHT_SLOT_FLOOR_S,
                   "seed_available": True, "slot_available": True, "would_seed": source,
                   "seeds": {"replay": seeds["replay"], "dream_tail": seeds["dream_tail"], "dormant": seeds["dormant"]},
                   "seed_snippet": (snippet or "")[:SEED_SNIPPET_CHARS],
                   "scheduler_turns": self.turns, "loop_lag_s": round(lag, 3),
                   "generated": False, "phase": 0}
            from core import profile, shadow_log
            if shadow_log.append(profile.guard_path(NIGHT_MIND_SHADOW_LOG), row):
                self.slots_written += 1
        except Exception as exc:     # includes profile.NonLiveWriteError from a non-live importer: refused, swallowed
            logger.debug("[sleep_phase0] shadow slot row skipped (non-fatal): %s", exc)
