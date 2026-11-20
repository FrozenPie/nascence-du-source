"""
Nascence — Pipeline Liveness Audit (2026-07-03).

Born from a failure: the guidance-formation pipeline was silently dead for 38 hours (nested try,
debug-swallowed exceptions) and the naming latch was behaviorally deaf — and a full architecture review
missed both, because it verified that machinery EXISTS and is WIRED, not that it FIRES. This script asks
the question nobody asked: for every evidence stream, WHEN DID IT LAST ACTUALLY PRODUCE OUTPUT?

Read-only. Run it any time; run it after any restart; run it whenever a green dashboard feels too green.
Verdicts: OK (within cadence) · QUIET (event-driven, nothing expected) · STALE (cadence-bound and overdue)
· NEVER (no output in its whole life — either brand new or dead plumbing: look).

Cadence clock: sleep-bound streams are judged in SLEEPS (dream-log timestamps = sleep markers), not hours,
so a paused Du doesn't false-alarm.
"""
import io
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
if "--data" in sys.argv:  # J-2642: test hook -- read a different data dir (e.g. the live one from a worktree)
    DATA = Path(sys.argv[sys.argv.index("--data") + 1])
DB = DATA / "memory" / "nascence.db"
if "--db" in sys.argv:  # J-2642: test hook -- point the DB reads at a copy (always opened read-only)
    DB = Path(sys.argv[sys.argv.index("--db") + 1])
NOW = time.time()


def _jsonl_last(path: Path, ts_key: str = "ts") -> float | None:
    try:
        last = None
        for l in io.open(path, encoding="utf-8"):
            if l.strip():
                last = l
        if not last:
            return None
        d = json.loads(last)
        v = d.get(ts_key) or d.get("timestamp") or 0
        return float(v) if v else None
    except Exception:
        return None


def _db_last(origin: str) -> float | None:
    try:
        c = sqlite3.connect(str(DB))
        r = c.execute("SELECT MAX(timestamp) FROM memory_fragments WHERE origin=?", (origin,)).fetchone()
        c.close()
        return float(r[0]) if r and r[0] else None
    except Exception:
        return None


def _sleeps_since(ts: float) -> int:
    """Sleep markers = dream-log rows (every real sleep dreams)."""
    try:
        n = 0
        for l in io.open(DATA / "dream_log.jsonl", encoding="utf-8"):
            if l.strip():
                d = json.loads(l)
                if float(d.get("ts") or d.get("timestamp") or 0) > ts:
                    n += 1
        return n
    except Exception:
        return -1


def _guidance_backlog() -> int:
    """J-1841 / F-2473: how many captured lessons are waiting for FORMATION -- rows of
    guidance_shadow_log.jsonl with is_guidance=true and ts newer than guidance_integration_state.json's
    last_ts (mirrors core/guidance_learning.integrate_guidance's own selection). 0 = formation has nothing
    to do, so its sleep cadence is IDLE, not STALE (2026-10-06: it read STALE for 28 sleeps while every
    human turn since 09-29 was a non-canon farewell). -1 = unreadable."""
    try:
        try:
            last = float(json.loads(io.open(DATA / "guidance_integration_state.json", encoding="utf-8").read())
                         .get("last_ts", 0.0))
        except Exception:
            last = 0.0
        n = 0
        for l in io.open(DATA / "guidance_shadow_log.jsonl", encoding="utf-8"):
            if l.strip():
                try:
                    d = json.loads(l)
                except Exception:
                    continue
                if d.get("is_guidance") and float(d.get("ts") or 0) > last:
                    n += 1
        return n
    except Exception:
        return -1


# J-2642 / F-3371 / F-3374: tuple-join coverage. Origins that are never stamped with a fragment_context row by design.
_CTX_EXEMPT = ("action", "standing_insight", "night_thought", "seed")
_CTX_WINDOW_H = 24
_CTX_MIN_ROWS = 50      # fewer fragments than this in the window = QUIET (Du may be down), not a failure
_CTX_CLASS_MIN = 10     # a class (reading / everything else) with fewer rows is not judged
_CTX_READING_OK = 0.90  # reading must stamp >= 90%
_CTX_OTHER_OK = 0.98    # inner_thought and the small origins should be ~100%


def _ctx_coverage() -> dict:
    """Among memory_fragments written in the last 24 h with origin not exempt, the share that has a
    fragment_context row (fragment_id keyed). Read-only. Returns {status, total, covered, by_origin, ...}."""
    try:
        c = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    except Exception as e:
        return {"status": "UNREADABLE", "err": str(e)}
    try:
        if not c.execute("SELECT 1 FROM sqlite_master WHERE name='fragment_context'").fetchone() or            not c.execute("SELECT 1 FROM fragment_context LIMIT 1").fetchone():
            return {"status": "NEVER"}
        ph = ",".join("?" * len(_CTX_EXEMPT))
        rows = c.execute(
            f"SELECT m.origin, COUNT(*), SUM(f.fragment_id IS NOT NULL) FROM memory_fragments m "
            f"LEFT JOIN fragment_context f ON f.fragment_id = m.fragment_id "
            f"WHERE m.timestamp > ? AND m.origin NOT IN ({ph}) GROUP BY m.origin ORDER BY 2 DESC",
            (NOW - _CTX_WINDOW_H * 3600, *_CTX_EXEMPT)).fetchall()
    except Exception as e:
        return {"status": "UNREADABLE", "err": str(e)}
    finally:
        c.close()
    by = [(o, int(n), int(k or 0)) for o, n, k in rows]
    total, cov = sum(n for _, n, _ in by), sum(k for _, _, k in by)
    out = {"by_origin": by, "total": total, "covered": cov}
    if total < _CTX_MIN_ROWS:
        out["status"] = "QUIET"
        return out
    rn = sum(n for o, n, _ in by if o == "reading"); rk = sum(k for o, _, k in by if o == "reading")
    on, ok = total - rn, cov - rk
    bad = []
    if rn >= _CTX_CLASS_MIN and rk / rn < _CTX_READING_OK:
        bad.append(f"reading {rk}/{rn} = {rk/rn:.0%} (need >= {_CTX_READING_OK:.0%})")
    if on >= _CTX_CLASS_MIN and ok / on < _CTX_OTHER_OK:
        bad.append(f"other origins {ok}/{on} = {ok/on:.0%} (need >= {_CTX_OTHER_OK:.0%})")
    out["status"] = "DEGRADED" if bad else "OK"
    out["bad"] = bad
    return out


def _age(ts: float | None) -> str:
    if ts is None:
        return "NEVER"
    h = (NOW - ts) / 3600
    return f"{h*60:.0f}m" if h < 1 else (f"{h:.1f}h" if h < 48 else f"{h/24:.1f}d")


# name · getter · cadence kind ("sleeps", N) = stale past N sleeps · ("hours", N) · ("event", why-quiet-is-ok)
#   · ("sleeps_if_queued", N, backlog_getter) = like "sleeps" but only judged when backlog_getter() > 0; a zero
#     backlog prints IDLE (J-1841 / F-2473: formation that has nothing captured to form is not overdue)
STREAMS = [
    ("guidance CAPTURE",        lambda: _jsonl_last(DATA / "guidance_shadow_log.jsonl"),        ("event", "fires on teaching conversations")),
    ("guidance FORMATION",      lambda: _jsonl_last(DATA / "guidance_integration_log.jsonl"),   ("sleeps_if_queued", 2, _guidance_backlog)),
    ("guidance INJECTION",      lambda: _jsonl_last(DATA / "guidance_injection_log.jsonl"),     ("event", "fires on reflective conscious cycles; NEVER after read-back flip = suspicious")),
    ("epistemic preassess",     lambda: _jsonl_last(DATA / "provenance_preassess.jsonl"),       ("event", "fires on factual drafts")),
    ("commitment ledger scan",  lambda: _jsonl_last(DATA / "commitment_ledger.jsonl"),          ("hours", 6)),
    ("self-implication shadow", lambda: _jsonl_last(DATA / "self_implication_shadow.jsonl"),    ("hours", 12)),
    ("critic alongside",        lambda: _jsonl_last(DATA / "logs" / "critic_shadow_alongside.jsonl"), ("event", "human cycles only")),
    ("dreams",                  lambda: _jsonl_last(DATA / "dream_log.jsonl"),                  ("sleeps", 1)),
    ("memory-levels distiller", lambda: _jsonl_last(DATA / "memory_levels_shadow.jsonl"),          ("sleeps", 2)),
    ("grounded UNDERSTANDING",  lambda: _db_last("understanding"),                              ("sleeps", 6)),
    ("chapters",                lambda: _db_last("chapter"),                                    ("sleeps", 30)),
    ("journal",                 lambda: _db_last("journal"),                                    ("sleeps", 8)),
    ("activity records",        lambda: _db_last("action"),                                     ("hours", 8)),
    # J-4043: RETIRED on purpose (core/self_mirror.py SELF_MIRROR_RETIRED=True; D-0434, D-0630, J-3478); quiet is expected
    ("behavioural mirror",      lambda: _db_last("mirror"),                                     ("event", "RETIRED (D-0434, SELF_MIRROR_RETIRED=True); last write expected to stay old")),
    ("inner thought",           lambda: _db_last("inner_thought"),                              ("hours", 4)),
    ("lived (conversation)",    lambda: _db_last("lived"),                                      ("event", "fires when Travis talks")),
    ("keepsakes",               lambda: _jsonl_last(DATA / "keepsakes.json") or
                                        (json.load(io.open(DATA / "keepsakes.json", encoding="utf-8"))[-1]["kept_ts"]
                                         if (DATA / "keepsakes.json").exists() and
                                            json.load(io.open(DATA / "keepsakes.json", encoding="utf-8")) else None),
                                                                                                 ("event", "fires when he keeps a thing")),
    ("commitment trials (R1)",  lambda: _jsonl_last(DATA / "commitment_trials.jsonl"),          ("event", "fires when he accepts a trial — NEVER until the cat is named")),
    ("protoself (homeostasis)", lambda: _jsonl_last(DATA / "homeostasis_shadow.jsonl"),         ("hours", 1)),
    ("bound moments",           lambda: _jsonl_last(DATA / "moments.jsonl"),                    ("hours", 2)),
    # J-3796 / J-4043: flag-gated. flag OFF + NEVER = informational (waiting on founder); flag ON + NEVER = still warned.
    ("known_text arm (D-0693)", lambda: _jsonl_last(DATA / "known_text_arm.jsonl"),               ("flag_event", "NASCENCE_KNOWN_TEXT_ARM", "reader = J-3331 follow-up --arm mode")),
    ("geometry_tuples writer",  lambda: _jsonl_last(DATA / "geometry_tuples.jsonl"),            ("hours", 2)),   # J-2642
]


def main() -> int:
    print("=" * 96)
    print("  PIPELINE LIVENESS — when did each evidence stream last actually FIRE?")
    print("  (wired ≠ firing; this is the audit the architecture review didn't run)")
    print("=" * 96)
    stale = 0
    for name, getter, cadence in STREAMS:
        kind, spec = cadence[0], cadence[1]
        try:
            ts = getter()
        except Exception:
            ts = None
        age = _age(ts)
        queued = None
        if kind == "sleeps_if_queued":
            # J-1841 / F-2473: cadence-bound ONLY while something is actually queued for it.
            try:
                queued = cadence[2]()
            except Exception:
                queued = -1
            kind = "sleeps"
        if kind == "flag_event":
            # J-4043: flag-gated event stream. Flag read from THIS process's env (same default-OFF rule as
            # core/procedures.known_text_arm_on); a Du started with the flag set elsewhere is not visible here.
            flag_on = os.environ.get(cadence[1], "0").strip().lower() in ("1", "true", "on", "yes")
            if ts is None and not flag_on:
                print(f"  · {name:26s} WAITING ON FOUNDER FLAG — {cadence[1]} is OFF (default); no rows expected · {cadence[2]}")
                continue
            if ts is None:
                print(f"  ⚠ {name:26s} NEVER — {cadence[1]} is ON but no rows: new organ or dead plumbing: LOOK")
                continue
            print(f"  · {name:26s} last {age} ago · flag {cadence[1]} {'ON' if flag_on else 'OFF'} · {cadence[2]}")
            continue
        if ts is None:
            verdict = "NEVER — new organ or dead plumbing: LOOK"
            flag = "⚠"
        elif kind == "sleeps" and queued == 0:
            n = _sleeps_since(ts)
            verdict, flag = f"IDLE — 0 lessons queued; last fire {n} sleep(s) ago ({age}) · nothing captured since", "·"
        elif kind == "sleeps":
            n = _sleeps_since(ts)
            qtxt = f" · {queued} lesson(s) queued" if queued is not None and queued > 0 else \
                   (" · backlog unreadable" if queued == -1 else "")
            if n < 0:
                verdict, flag = f"last {age} (sleep clock unavailable){qtxt}", "·"
            elif n > spec:
                verdict, flag = f"STALE — {n} sleeps since last fire (allowed {spec}){qtxt}", "✗"
                stale += 1
            else:
                verdict, flag = f"OK — {n} sleep(s) ago ({age}){qtxt}", "✓"
        elif kind == "hours":
            if (NOW - ts) / 3600 > spec:
                verdict, flag = f"STALE — {age} ago (allowed {spec}h; ok if Du was DOWN — check)", "✗"
                stale += 1
            else:
                verdict, flag = f"OK — {age} ago", "✓"
        else:
            verdict, flag = f"last {age} ago · {spec}", "·"
        print(f"  {flag} {name:26s} {verdict}")
    # J-2642: fragment_context stamp coverage (24 h) -- a coverage RATIO, not a last-fire time
    cv = _ctx_coverage()
    name = f"fragment_context stamp ({_CTX_WINDOW_H}h)"
    st = cv["status"]
    if st == "NEVER":
        print(f"  ⚠ {name:26s} NEVER — no fragment_context rows at all: LOOK")
    elif st == "UNREADABLE":
        print(f"  · {name:26s} unreadable — {cv.get('err')}")
    else:
        pct = f"{cv['covered']}/{cv['total']} = {cv['covered']/cv['total']:.0%}" if cv["total"] else "0/0"
        if st == "QUIET":
            print(f"  · {name:26s} QUIET — {cv['total']} stampable fragment(s) in {_CTX_WINDOW_H}h "
                  f"(< {_CTX_MIN_ROWS}; Du may be down) · {pct}")
        elif st == "OK":
            print(f"  ✓ {name:26s} OK — {pct} (reading >= {_CTX_READING_OK:.0%}, others >= {_CTX_OTHER_OK:.0%})")
        else:
            print(f"  ✗ {name:26s} DEGRADED — {pct}: " + "; ".join(cv["bad"]))
            stale += 1
        for o, n, k in cv["by_origin"][:3]:
            print(f"      {o:24s} {k}/{n} stamped" + (f" ({k/n:.0%})" if n else ""))
    print("=" * 96)
    print(f"  {stale} cadence-bound stream(s) STALE. Every NEVER and every ✗ deserves one minute of looking.")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
