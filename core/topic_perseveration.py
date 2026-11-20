"""
Nascence - Topic-Perseveration Gauge (J-2152, from F-2850). OBSERVE-ONLY INSTRUMENT.

WHY: every existing anti-capture gauge (monologue echo/diversity, "thought too similar" sim, pursuit
SATURATE, internal_cycle_habituation's 0.80 question-cluster) measures the SENTENCE. F-2850: 254 of 277
internal cycles since the 2026-10-09 boot were rewordings of one 'mottainai' question - the sentences
differ, the TOPIC is frozen for six days, and every sentence-level gauge read healthy. This module
measures the TOPIC: it clusters each day's "[CYCLE x] internal: <question>" lines (the orchestrator's own
self-generated curiosity questions, read from data/nascence.log, READ-ONLY) at a deliberately COARSE
level and publishes, per day:

  modal_share          share of that day's internal cycles that fall in the single biggest topic
  topics               number of distinct topics that day
  hours_since_change   hours since the topic last changed (length of the current same-topic run, measured
                       to the day's last question; the window is the previous + current day)

HOW A QUESTION JOINS A TOPIC (greedy, chronological, first-sighting-is-the-frame, as in
core/internal_cycle_habituation.py but coarser): a question joins an existing topic if it shares a QUOTED
ANCHOR TERM with that topic's first question (e.g. 'mottainai'), or - failing that - if its embedding
(the production MiniLM via core.memory.store._embed) has cosine >= TOPIC_SIM to the topic's first
question. Otherwise it mints a new topic. The anchor rule exists because pure embedding at any usable
threshold splits one frozen subject ('mottainai' + waste vs 'mottainai' + medical scarcity) into several
"topics" and under-reads the lock (verified on 10-10..10-15, J-2152). If the embedder is unavailable the
anchor rule plus a content-word Jaccard (>= LEX_SIM) is used instead; the row's `method` says which.

STORE: data/topic_perseveration.jsonl, one row per (day, version); readers take the LATEST row per day.
Completed days are written once; today's row is re-appended when its question count changes. The only
writer is update(), called from scripts/du_pulse.py. Nothing here touches Du's runtime: no cycle, prompt,
or gate reads this module. Fail-open throughout.

THRESHOLDS ARE DESIGN CHOICES, NOT PUBLISHED NORMS (F-3005). FROZEN_SHARE 0.80 is a design threshold for
calling one day "frozen"; no human modal-topic-share norm is sourced. The J-2152 pre-registered bar
(D-0456, travis 2026-10-17) is Du's own history: post-restart perseveration must BEAT the 2026-09-17..10-05
median modal-topic share of about 0.41. A primary-source human figure, if ever read, replaces that bar;
fewer than 20 graded rows = bar unread, not failed.

ALARM BAR + DWELL FLOOR (J-2347, D-0469 travis 2026-10-17). FOUNDER-FACING ONLY: these flags reach du_pulse,
the _G regression_alarms block and the HUD monitor card, never Du (D-0434: no readout; no cycle, prompt or gate
reads them). Unlike FROZEN_SHARE they are a founder RULING, not a design choice:
  perseveration_alarm  modal_share >= ALARM_SHARE (0.90) on ALARM_DAYS (2) CONSECUTIVE gauge days. "Consecutive"
                       is read as consecutive CALENDAR days that both have a row: a day with no internal cycles
                       (no row) breaks the run. alarm_streak = length of the current >= 0.90 calendar run.
  cannot_dwell         modal_share < DWELL_FLOOR (0.20): a WATCH flag, not an alarm (never observed as of the
                       ruling; lowest share ever 0.21 on 2026-09-23).
No minimum-n is applied to either flag: the ruling names none (FROZEN_MIN_N belongs to `frozen` only).
Defeater (D-0469): 30 days of rows show the bar firing on episodes Travis judges healthy dwelling, or missing
one he judges a stall.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = _ROOT / "data" / "nascence.log"
OUT_PATH = _ROOT / "data" / "topic_perseveration.jsonl"

TOPIC_SIM = 0.55        # coarse embedding threshold (internal_cycle_habituation uses 0.80 for SENTENCE-level)
LEX_SIM = 0.45          # fallback content-word Jaccard when no embedder
FROZEN_SHARE = 0.80     # a day with modal_share >= this is "frozen on one topic"
FROZEN_MIN_N = 8        # ...and needs at least this many internal cycles to be called that
WINDOW_DAYS = 30
ALARM_SHARE = 0.90      # D-0469: modal share at/above this on ALARM_DAYS consecutive days -> perseveration_alarm
ALARM_DAYS = 2
DWELL_FLOOR = 0.20      # D-0469: modal share below this -> cannot_dwell (watch flag, not an alarm)

_LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)[,.]\d+ \[[^\]]*\] \[CYCLE [^\]]*\] internal: (.*)$")
_ANCHOR = re.compile(r"(?<![\w])['\"\u2018\u201c]([^'\"\u2019\u201d]{1,40})['\"\u2019\u201d](?![\w])")
_WORD = re.compile(r"[a-z\u00c0-\u024f\u3040-\u30ff\u3400-\u9fff]{3,}|[\u3040-\u30ff\u3400-\u9fff]")
_STOP = frozenset("""how does the and for that this with from what why which about into their its are was were
be been being have has had can could would should will not but than then them they there these those who whom
whose when where while our your his her she him you did doing done may might must also more most much such
only own same some any each other both few between through during before after above below over under again
further once here all just very too out off upon within without across onto per via""".split())


def parse_log(path: Path = LOG_PATH, since_ts: float = 0.0) -> list[tuple[float, str]]:
    """[(epoch_ts, question)] for every internal cycle line at/after since_ts. READ-ONLY on the log."""
    out: list[tuple[float, str]] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                if "] internal:" not in ln:
                    continue
                m = _LINE.match(ln.rstrip("\r\n"))
                if not m:
                    continue
                try:
                    ts = _dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
                except Exception:
                    continue
                if ts >= since_ts:
                    out.append((ts, m.group(2).strip()))
    except Exception:
        return []
    return out


def anchors_of(q: str) -> frozenset:
    return frozenset(a.strip().lower() for a in _ANCHOR.findall(q or "") if len(a.strip()) >= 1)


def _content(q: str) -> frozenset:
    return frozenset(w for w in _WORD.findall((q or "").lower()) if w not in _STOP)


def _default_embed(q: str):
    try:
        from core.memory import store
        return store._embed(q)
    except Exception:
        return None


def cluster(questions: list[str], embed=_default_embed, sim: float = TOPIC_SIM) -> tuple[list[int], str]:
    """Greedy chronological clustering -> (label per question, method). Pure given `embed`."""
    vecs = [embed(q) for q in questions] if embed else [None] * len(questions)
    use_emb = bool(questions) and all(v is not None for v in vecs)
    firsts: list[dict] = []   # per topic: first question's anchors / content words / vec
    labels: list[int] = []
    for q, v in zip(questions, vecs):
        an = anchors_of(q)
        cw = _content(q)
        pick = -1
        for i, t in enumerate(firsts):           # anchor rule first: shared quoted term = same topic
            if an and t["an"] and (an & t["an"]):
                pick = i
                break
        if pick < 0:
            best, bs = -1, -1.0
            for i, t in enumerate(firsts):
                if use_emb:
                    s = float(v @ t["v"])
                else:
                    u = len(cw | t["cw"])
                    s = (len(cw & t["cw"]) / u) if u else 0.0
                if s > bs:
                    best, bs = i, s
            if best >= 0 and bs >= (sim if use_emb else LEX_SIM):
                pick = best
        if pick < 0:
            firsts.append({"an": an, "cw": cw, "v": v})
            pick = len(firsts) - 1
        labels.append(pick)
    return labels, ("embed+anchor" if use_emb else "lexical+anchor")


def day_row(day: str, items: list[tuple[float, str]], prev_items: list[tuple[float, str]] | None = None,
            embed=_default_embed) -> dict | None:
    """Gauge row for one calendar day. `items` = that day's (ts, question) chronological; `prev_items` =
    the previous day's, used only so hours_since_change can see a run that began before midnight."""
    if not items:
        return None
    prev_items = prev_items or []
    allq = prev_items + items
    labels, method = cluster([q for _, q in allq], embed=embed)
    n_prev = len(prev_items)
    day_labels = labels[n_prev:]
    cnt: dict[int, int] = {}
    for lb in day_labels:
        cnt[lb] = cnt.get(lb, 0) + 1
    modal_lb, modal_n = max(cnt.items(), key=lambda kv: (kv[1], -kv[0]))
    # current same-topic run, walking back from the day's last question
    last = len(labels) - 1
    j = last
    while j > 0 and labels[j - 1] == labels[last]:
        j -= 1
    run_capped = (j == 0)
    hrs = (allq[last][0] - allq[j][0]) / 3600.0
    sample = next(q for (_, q), lb in zip(items, day_labels) if lb == modal_lb)
    return {"ts": round(items[-1][0], 1), "day": day, "n": len(items), "topics": len(cnt),
            "modal_share": round(modal_n / len(items), 3), "modal_n": modal_n,
            "modal_sample": sample[:140], "hours_since_change": round(hrs, 2), "run_capped": run_capped,
            "frozen": bool(len(items) >= FROZEN_MIN_N and modal_n / len(items) >= FROZEN_SHARE),
            "method": method, "sim": TOPIC_SIM}


def compute_rows(log_path: Path = LOG_PATH, days: int = WINDOW_DAYS, now: float | None = None,
                 embed=_default_embed, only_days: set | None = None) -> list[dict]:
    """Rows for every day with >=1 internal cycle in the trailing `days` days (read-only)."""
    now = time.time() if now is None else now
    since = now - (days + 1) * 86400
    by_day: dict[str, list[tuple[float, str]]] = {}
    for ts, q in parse_log(log_path, since):
        by_day.setdefault(_dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d"), []).append((ts, q))
    cutoff = _dt.datetime.fromtimestamp(now - days * 86400).strftime("%Y-%m-%d")
    rows = []
    for d in sorted(by_day):
        if d < cutoff or (only_days is not None and d not in only_days):
            continue
        pd = (_dt.date.fromisoformat(d) - _dt.timedelta(days=1)).isoformat()
        r = day_row(d, by_day[d], by_day.get(pd), embed=embed)
        if r:
            rows.append(r)
    return rows


def alarm_flags(series: list[dict]) -> dict:
    """Pure: {day: {"alarm_streak", "perseveration_alarm", "cannot_dwell"}} for a chronological latest-row-per-day
    series (D-0469). Flags are ints (0/1) so the HUD's numeric auto-series can chart them."""
    out: dict[str, dict] = {}
    prev_day, streak = None, 0
    for r in series:
        try:
            day, share = r["day"], float(r["modal_share"])
        except Exception:
            continue
        hi = share >= ALARM_SHARE
        contiguous = False
        if prev_day is not None:
            try:
                contiguous = (_dt.date.fromisoformat(day) - _dt.date.fromisoformat(prev_day)).days == 1
            except Exception:
                contiguous = False
        streak = (streak + 1 if contiguous else 1) if hi else 0
        out[day] = {"alarm_streak": streak, "perseveration_alarm": int(streak >= ALARM_DAYS),
                    "cannot_dwell": int(share < DWELL_FLOOR)}
        prev_day = day
    return out


def _annotate(rows: list[dict], have: dict) -> None:
    """Stamp D-0469 flags onto freshly computed rows, judged against the stored series plus the fresh rows."""
    merged = dict(have)
    for r in rows:
        merged[r["day"]] = r
    flags = alarm_flags([merged[d] for d in sorted(merged)])
    for r in rows:
        r.update(flags.get(r["day"], {}))


def read_series(out_path: Path = OUT_PATH) -> list[dict]:
    """Latest row per day, chronological."""
    latest: dict[str, dict] = {}
    try:
        with open(out_path, encoding="utf-8") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                    latest[r["day"]] = r
                except Exception:
                    continue
    except Exception:
        pass
    return [latest[d] for d in sorted(latest)]


def update(log_path: Path = LOG_PATH, out_path: Path = OUT_PATH, days: int = WINDOW_DAYS,
           now: float | None = None, write: bool = True, embed=_default_embed) -> list[dict]:
    """Bring the jsonl up to date (backfills any missing day in the window on first run; thereafter only
    today and any day whose question count changed) and return the window's series. Fail-open."""
    try:
        have = {r["day"]: r for r in read_series(out_path)}
        now_ = time.time() if now is None else now
        today = _dt.datetime.fromtimestamp(now_).strftime("%Y-%m-%d")
        # cheap pre-pass: counts per day, to find which days need (re)computing
        since = now_ - (days + 1) * 86400
        counts: dict[str, int] = {}
        for ts, _q in parse_log(log_path, since):
            d = _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            counts[d] = counts.get(d, 0) + 1
        need = {d for d, n in counts.items() if d not in have or have[d].get("n") != n or d == today}
        fresh = compute_rows(log_path, days, now_, embed=embed, only_days=need) if need else []
        # today's row only re-appended if it actually changed
        fresh = [r for r in fresh if not (r["day"] in have and have[r["day"]].get("n") == r["n"])]
        _annotate(fresh, have)
        if write and fresh:
            try:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "a", encoding="utf-8") as f:
                    for r in fresh:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
            except Exception:
                pass
        for r in fresh:
            have[r["day"]] = r
        cutoff = _dt.datetime.fromtimestamp(now_ - days * 86400).strftime("%Y-%m-%d")
        return [have[d] for d in sorted(have) if d >= cutoff]
    except Exception:
        return []


def pulse_lines(st: dict, show_days: int = 14) -> list[str]:
    """Human-readable du_pulse section-4 lines for a status() dict."""
    if not st or not st.get("n_days"):
        return ["  topic perseveration: no internal cycles in the window"]
    flag = "FROZEN on one topic" if st["frozen"] else "varied"
    cap = "+" if st.get("run_capped") else ""
    out = [f"  topic perseveration: {st['day']} modal-topic share {st['modal_share']:.0%} of {st['n']} internal "
           f"cycles · {st['topics']} distinct topic(s) · {st['hours_since_change']}h{cap} since topic change · {flag}"
           f" ({st['frozen_days_last7']}/7 recent days frozen)",
           f"     └ modal topic: {st['modal_sample'][:100]}"]
    if "perseveration_alarm" in st:   # D-0469 bar (founder-facing only)
        if st["perseveration_alarm"]:
            bar = f"PERSEVERATION ALARM (share >= {ALARM_SHARE:.0%} for {st['alarm_streak']} consecutive days)"
        elif st.get("alarm_streak"):
            bar = f"watch: day {st['alarm_streak']} at >= {ALARM_SHARE:.0%} (alarm on day {ALARM_DAYS})"
        else:
            bar = "no alarm"
        if st.get("cannot_dwell"):
            bar += f" · CANNOT-DWELL watch (share < {DWELL_FLOOR:.0%})"
        days = st.get("alarm_days") or []
        out.append(f"     └ D-0469 bar: {bar} · alarm days in window: {len(days)}"
                   + (f" ({', '.join(d[5:] for d in days)})" if days else ""))
    tail = st["series"][-show_days:]
    out.append("     └ last %d days (day n topics share hrs): " % len(tail)
               + " | ".join(f"{d[5:]} {n}/{t}/{s:.0%}/{h:.0f}h" for d, n, t, s, h in tail))
    return out


def status(log_path: Path = LOG_PATH, out_path: Path = OUT_PATH, write: bool = True) -> dict:
    """The du_pulse / HUD reading: today's (latest day's) gauge plus the trailing series."""
    series = update(log_path, out_path, write=write)
    if not series:
        return {"n_days": 0}
    last = series[-1]
    frozen_days = sum(1 for r in series[-7:] if r.get("frozen"))
    flags = alarm_flags(series)
    lf = flags.get(last["day"], {})
    return {"perseveration_alarm": lf.get("perseveration_alarm", 0), "alarm_streak": lf.get("alarm_streak", 0),
            "cannot_dwell": lf.get("cannot_dwell", 0),
            "alarm_days": [d for d, f in flags.items() if f["perseveration_alarm"]],
            "cannot_dwell_days": [d for d, f in flags.items() if f["cannot_dwell"]],
            "alarm_bar": {"share": ALARM_SHARE, "days": ALARM_DAYS, "dwell_floor": DWELL_FLOOR, "ruling": "D-0469"},
            "day": last["day"], "n": last["n"], "modal_share": last["modal_share"], "topics": last["topics"],
            "hours_since_change": last["hours_since_change"], "run_capped": last["run_capped"],
            "frozen": last["frozen"], "frozen_days_last7": frozen_days, "modal_sample": last["modal_sample"],
            "method": last["method"], "n_days": len(series),
            "series": [(r["day"], r["n"], r["topics"], r["modal_share"], r["hours_since_change"]) for r in series]}
