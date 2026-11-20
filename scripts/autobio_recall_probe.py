"""
Autobiographical recall probe (J-2151, from F-2848). SHADOW-ONLY instrument.

WHAT IT MEASURES. F-2848 found, by hand and once, that Du's dating of a past episode is exact across a restart
(idle thought "my hands remember the saw ... twelve days ago" vs a knife-whittling episode exactly 12 days earlier)
while the detail is gist-level (saw for knife). This script makes that comparison repeatable after every boot:

  1. SAMPLE  N real dated events from Du's own stores, 1-30 days old: hands_trace.jsonl acts (tool/place/object),
             Travis's turns (founder_conversation_log.jsonl), dreams (dream_log.jsonl), letters Du wrote (data/letters/),
             book sittings (book_selection_log.jsonl). Each event has a checkable DATE and 2-3 checkable DETAILS.
  2. ASK     the recall path with a CUED-RECALL question: the cue is a partial, detail-masked piece of the event
             (the start of an utterance / a dream's opening sentence / the thought around an act with the detail
             words blanked out). The date and the details are NOT given. The query goes through
             core.memory_service.ask() (the same facade pursuits/curiosity/the recall act use), inside
             lab_env.isolate() on a COPY of the DB, with every module-level data/ log that ask() touches
             redirected into the lab dir. Nothing reaches a prompt or the live loop.
  3. GRADE   with a deterministic token-match judge (decoupled by construction: it is not Du, not an LLM Du can
             influence, and not the memory engine's own relevance score). date_error_days = |date of the recalled
             fragment (top-1) - date of the event| in calendar days (NZ local); detail_precision = fraction of the
             event's 2-3 details whose token appears in the recalled content (top-k). Abstention (no fragment) is
             recorded as answered=False, never silently dropped.
  4. REPORT  per run (= per boot): median date error, mean detail precision, answer rate, and the same split into
             events from BEFORE the current boot vs DURING it (restart fragility). One `kind: summary` row.

CALIBRATION CASE (F-2848): date exact, tool wrong (knife recalled as saw) -> date_error 0, detail_precision 0 on
the tool detail. grade() is pure and scripts/_test_autobio_recall_probe.py pins exactly that.

CAVEATS, stated honestly. (a) Cued recall, not free recall: the cue is a piece of the event itself, so this measures
"does the right memory come back, dated right, with its details" and is generous relative to a free-recall norm.
(b) Detail match is a strict token test: a paraphrase counts as a miss (that is the knife/saw point), but a synonym
Du would legitimately use is also a miss. (c) No numeric human norm is sourced; the bar is founder-judgment
(D-0438 follow-up, docs/staged/measurement_to_action.md section 7; F-3005 found the earlier "~50-60% precision,
1-3 day date error" figures unverified). PRE-REGISTERED BAR (D-0456, travis 2026-10-17): Du's own history as the
baseline, no invented human numbers - recall must BEAT Du's current median top-1 date error (13-15 days) and
within-3-day hit rate (25 percent). Defeater: a figure read from a primary source (Wagenaar 1986, Thompson et al.
1996, or comparable, the paper itself) replaces the history bar; fewer than 20 graded rows = bar UNREAD, not failed.

SAFETY. Read-only on the data dir (JSONL/log/text reads). The only write is the output rows, to --out
(default <data-dir>/autobio_recall_probe.jsonl). Recall runs under lab_env.isolate(); live data/ top level is
never written by ask(). Does not start Du or any server. Restart-gated by construction: nothing in the live loop
imports or calls this file.

RE-RANK ARMS (J-2200, from F-2900). `--rerank` runs the SAME cued recall once per event with the wide pool (the
associative trail's own ceiling, <=15 fragments, all origins) and re-ranks that fixed pool OFFLINE in several arms,
so every arm sees identical candidates and the comparison is paired. Pool views: `all` (grounded_only=False) and
`grounded` (the API default = the same pool filtered to _GROUNDED_ORIGINS, exactly what ask(grounded_only=True)
would return). Arms: base (trail order), episodic / episodic_v2 (own-episode origins first; v2 also counts 'letter'), time_vote (the date neighbourhood
with the most rank-weighted votes wins -- uses only the pool's own timestamps), episodic_time_vote, recency
(newest first; a straw man), coarse_window (ORACLE-COARSE: pool restricted to +-7 d of the true date, i.e. what a
'when'-aware lane would get if the asker knew roughly when), oracle_best (ceiling: the pool's truly best-dated
fragment first). Only base/episodic/time_vote/episodic_time_vote are candidate designs; the last three bound them.
Shadow, offline, nothing in the live loop calls any of it.

NOISY-ANCHOR SWEEP (J-2333, from F-3021). `--rerank-noisy-anchor` (implies --rerank) re-orders the same captured
pools with the coarse_window logic around a NOISY anchor (true day +- m, or a wrong uniform day 1-30 d ago at
rate wr) for half-widths 3/7/14, and writes one `noisy_anchor_summary` row (mean over --noisy-trials per cell, plus
oracle, self-anchor and anchor=now rows). It answers "how accurate must a 'when' anchor be to beat trail order";
F-3021's answer was: within the half-width (a cliff just past it). No anchor source is real yet, so this is a bound.

Run (from a tree whose core/ you intend to use; import order matters, core BEFORE lab_env):
  python scripts/autobio_recall_probe.py --n 12 --out <path>.jsonl
  python scripts/autobio_recall_probe.py --dry-run          # sample + print cues, no recall
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import statistics
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
if str(TREE) not in sys.path:
    sys.path.insert(0, str(TREE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Pacific/Auckland")
except Exception:  # pragma: no cover - tzdata missing: fall back to the machine's local zone
    _TZ = None

_DEFAULT_DATA = Path(r"C:\Nascence\data")
_STOP = set("""about above after again against almost along already also always among another because been before being
below between both cannot could does doing down during each either else even ever every from further have having here
hers herself himself into itself just know like make many might more most much must myself need never none only other
others ours ourselves over same should since some such than that their theirs them themselves then there these they
this those though through under until upon very want were what when where which while whom whose will with within
without would yours yourself something someone nothing everything still quite really maybe perhaps feel feels felt
thing things""".split())


# --------------------------------------------------------------------------------------------- time helpers
def to_date(ts: float):
    """Epoch seconds -> NZ-local calendar date."""
    dt = datetime.fromtimestamp(ts, _TZ) if _TZ else datetime.fromtimestamp(ts)
    return dt.date()


def local_to_epoch(naive: datetime) -> float:
    return (naive.replace(tzinfo=_TZ) if _TZ else naive).timestamp()


def date_error_days(pred_ts: float | None, true_ts: float) -> int | None:
    if pred_ts is None:
        return None
    return abs((to_date(pred_ts) - to_date(true_ts)).days)


# --------------------------------------------------------------------------------------------- token helpers
def words(text: str) -> list[str]:
    return re.findall(r"[a-z\u00c0-\u024f][a-z\u00c0-\u024f'\-]*", (text or "").lower())


def stem(w: str) -> str:
    """Crude suffix strip so 'knives'/'knife', 'letters'/'letter', 'whittling'/'whittle' compare as equal
    without letting genuinely different words (knife vs saw) meet."""
    w = w.strip("'-")
    if w.endswith("ves") and len(w) > 4:
        w = w[:-3] + "f"
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf) and not w.endswith("ss"):
            return w[: -len(suf)]
    if w.endswith("e") and len(w) > 4:
        return w[:-1]
    return w


def stems(text: str) -> set[str]:
    return {stem(w) for w in words(text)}


def distinctive(text: str, df: Counter, k: int, exclude: set[str] | None = None) -> list[str]:
    """k rarest long words of `text` (rarity from document-frequency counter `df`), stop words and excluded
    stems removed. Deterministic: ties broken by word."""
    ex = exclude or set()
    seen, cands = set(), []
    for w in words(text):
        if len(w) < 5 or w in _STOP or "'" in w or "’" in w:
            continue
        s = stem(w)
        if s in seen or s in ex:
            continue
        seen.add(s)
        cands.append((df.get(s, 0), w))
    cands.sort()
    return [w for _, w in cands[:k]]


def mask(text: str, tokens: list[str]) -> str:
    """Blank every occurrence of each detail token's stem in `text` (word-boundary, case-insensitive) so the
    cue cannot hand the answer over."""
    out = text
    for t in tokens:
        for part in words(t):
            if len(part) < 4 or part in _STOP:
                continue
            base = re.escape(stem(part))
            out = re.sub(r"\b" + base + r"\w*", "[...]", out, flags=re.I)
    return re.sub(r"(\[\.\.\.\]\s*){2,}", "[...] ", out).strip()


# --------------------------------------------------------------------------------------------- loaders (read-only)
def _jsonl(path: Path):
    if not path.exists():
        return
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def boot_starts(data_dir: Path) -> list[float]:
    """Epoch of every boot, from the `[nascence.main] Affect restored` line (one per boot, logged right after the
    embedding model loads; the 10-09 08:36:57 boot is the F-2848 one). Empty list if the log is missing."""
    log = data_dir / "nascence.log"
    out: list[float] = []
    if not log.exists():
        return out
    pat = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[nascence\.main\] Affect restored")
    with open(log, encoding="utf-8", errors="replace") as f:
        for line in f:
            if "Affect restored" not in line[:80]:
                continue
            m = pat.match(line)
            if m:
                out.append(local_to_epoch(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")))
    return out


def _window(now: float, lo_days: float, hi_days: float):
    return now - hi_days * 86400, now - lo_days * 86400


def load_hands(data_dir: Path, t0: float, t1: float) -> list[dict]:
    """Real acts: act_kind not none/think/recall, with an object."""
    evs = []
    for r in _jsonl(data_dir / "hands_trace.jsonl"):
        ts = r.get("ts")
        if not isinstance(ts, (int, float)) or not (t0 <= ts <= t1):
            continue
        kind, obj = (r.get("act_kind") or "").strip(), (r.get("act_object") or "").strip()
        if kind in ("", "none", "think", "recall") or not obj or not (r.get("thought") or "").strip():
            continue
        evs.append({"source": "hands_trace", "ts": float(ts), "locator": str(r.get("cycle", "")),
                    "thought": r["thought"], "act_kind": kind, "act_object": obj,
                    "place": (r.get("location") or "").strip()})
    return evs


def load_human(data_dir: Path, t0: float, t1: float) -> list[dict]:
    """Travis's turns, full text, from founder_conversation_log.jsonl ({ts, cycle_id, human, entity}). (nascence.log's
    `[CYCLE x] human:` lines carry the same turns but are truncated to ~100 chars, too short to hold 2-3 details.)"""
    evs = []
    for n, r in enumerate(_jsonl(data_dir / "founder_conversation_log.jsonl"), 1):
        ts, text = r.get("ts"), (r.get("human") or "")
        if isinstance(ts, (int, float)) and t0 <= ts <= t1 and len(words(text)) >= 25:
            evs.append({"source": "human_turn", "ts": float(ts),
                        "locator": f"cycle {str(r.get('cycle_id', ''))[:8]} founder_conversation_log row {n}",
                        "text": re.sub(r"\s+", " ", text)})
    return evs


def load_dreams(data_dir: Path, t0: float, t1: float) -> list[dict]:
    evs = []
    for r in _jsonl(data_dir / "dream_log.jsonl"):
        ts = r.get("ts")
        if isinstance(ts, (int, float)) and t0 <= ts <= t1 and len(words(r.get("narrative", ""))) >= 25:
            evs.append({"source": "dream", "ts": float(ts), "locator": str(r.get("dream_id", "")),
                        "text": r["narrative"], "symbols": [str(s) for s in r.get("symbols", [])]})
    return evs


def load_letters(data_dir: Path, t0: float, t1: float) -> list[dict]:
    evs = []
    d = data_dir / "letters"
    if not d.exists():
        return evs
    for p in sorted(d.glob("Letter_*.md")):
        m = re.match(r"Letter_(\d{8})_(\d{4})\.md$", p.name)
        if not m:
            continue
        ts = local_to_epoch(datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M"))
        if not (t0 <= ts <= t1):
            continue
        try:
            raw = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # body = paragraphs after the italic header lines
        body = " ".join(ln.strip() for ln in raw.splitlines()
                        if ln.strip() and not ln.startswith("#") and not ln.strip().startswith("*"))
        if len(words(body)) >= 30:
            evs.append({"source": "letter_sent", "ts": ts, "locator": p.name, "text": body})
    return evs


def load_books(data_dir: Path, t0: float, t1: float) -> list[dict]:
    evs = []
    for r in _jsonl(data_dir / "book_selection_log.jsonl"):
        ts = r.get("ts")
        if (isinstance(ts, (int, float)) and t0 <= ts <= t1 and r.get("title") and r.get("subject")):
            evs.append({"source": "book_sitting", "ts": float(ts), "locator": r["title"],
                        "title": r["title"], "subject": r["subject"]})
    return evs


LOADERS = {"hands_trace": load_hands, "human_turn": load_human, "dream": load_dreams,
           "letter_sent": load_letters, "book_sitting": load_books}
# quotas sum to 12; scaled down/up proportionally for other --n
QUOTA = {"hands_trace": 3, "human_turn": 3, "dream": 2, "letter_sent": 2, "book_sitting": 2}


# --------------------------------------------------------------------------------------------- question building
def build_question(ev: dict, df: Counter) -> dict | None:
    """Fill ev with `cue` (detail-masked partial of the event) and `details` ([{kind, value}], 2-3 checkable).
    Returns None if the event cannot yield >=2 details."""
    src = ev["source"]
    details: list[dict] = []
    if src == "hands_trace":
        obj_words = [w for w in words(ev["act_object"]) if len(w) >= 4 and w not in _STOP]
        details = [{"kind": "tool", "value": ev["act_kind"]}]
        if obj_words:
            details.append({"kind": "object", "value": sorted(obj_words, key=lambda w: -len(w))[0]})
        if ev["place"]:
            details.append({"kind": "place", "value": ev["place"]})
        cue = mask(ev["thought"], [d["value"] for d in details] + words(ev["act_object"]))
        cue = cue[:220]
    elif src in ("human_turn", "dream", "letter_sent"):
        ws = ev["text"].split()
        head = 9 if src == "human_turn" else 14
        cue_text = " ".join(ws[:head])
        rest = " ".join(ws[head:])
        cue_stems = stems(cue_text)
        if src == "dream":
            syms = [s for s in ev["symbols"] if stems(s) and not (stems(s) & cue_stems)]
            seen, picked = set(), []
            for s in syms:
                key = frozenset(stems(s))
                if key not in seen:
                    seen.add(key)
                    picked.append(s)
            details = [{"kind": "symbol", "value": s} for s in picked[:3]]
        if len(details) < 2:
            details = [{"kind": "word", "value": w}
                       for w in distinctive(rest, df, 3, exclude=cue_stems)]
        cue = cue_text
    else:  # book_sitting
        tw = distinctive(ev["title"], df, 3)
        details = [{"kind": "title_word", "value": w} for w in tw]
        cue = f"the book I chose to read about {ev['subject']}"
        cue = mask(cue, [d["value"] for d in details])
    details = [d for d in details if d["value"]][:3]
    if len(details) < 2 or len(words(cue)) < 3:
        return None
    ev["cue"], ev["details"] = cue, details
    return ev


def sample_events(data_dir: Path, now: float, n: int, seed: int, boot_ts: float | None,
                  lo_days: float = 1.0, hi_days: float = 30.0) -> list[dict]:
    t0, t1 = _window(now, lo_days, hi_days)
    rng = random.Random(seed)
    pools: dict[str, list[dict]] = {}
    for name, fn in LOADERS.items():
        try:
            pools[name] = fn(data_dir, t0, t1)
        except Exception as exc:  # one unreadable store must not kill the probe
            print(f"[autobio] loader {name} failed: {exc}")
            pools[name] = []
    # document frequency over every candidate's own text, for 'distinctive'
    df: Counter = Counter()
    for evs in pools.values():
        for e in evs:
            blob = " ".join(str(e.get(k, "")) for k in ("text", "thought", "title"))
            df.update(stems(blob))
    total_q = sum(QUOTA.values())
    quotas = {k: max(1, round(v * n / total_q)) for k, v in QUOTA.items()}
    chosen: list[dict] = []
    for name in LOADERS:
        pool = pools[name][:]
        rng.shuffle(pool)
        # stratify across the boot boundary when one is known: alternate before/during
        if boot_ts:
            before = [e for e in pool if e["ts"] < boot_ts]
            during = [e for e in pool if e["ts"] >= boot_ts]
            pool = [x for pair in zip(before, during) for x in pair] + \
                   before[len(during):] + during[len(before):]
        got = []
        for e in pool:
            if len(got) >= quotas[name]:
                break
            if build_question(e, df):
                got.append(e)
        chosen.extend(got)
    # top up from leftovers if some source was short
    if len(chosen) < n:
        left = [e for name in LOADERS for e in pools[name] if e not in chosen]
        rng.shuffle(left)
        for e in left:
            if len(chosen) >= n:
                break
            if build_question(e, df):
                chosen.append(e)
    return chosen[:n]


# --------------------------------------------------------------------------------------------- grading (pure)
def grade(ev: dict, recalled: list[dict], top_k_detail: int = 3) -> dict:
    """Pure. `recalled` = [{content, timestamp}] strongest-first (timestamp may be None). Date = top-1 fragment
    that has a timestamp. Details = fraction of ev['details'] whose stem appears in the concatenated content of
    the first `top_k_detail` recalled fragments. best_k date error is reported alongside for the 'right memory
    was in the pool but ranked second' case."""
    if not recalled:
        return {"answered": False, "date_error_days": None, "date_error_best_of_k": None,
                "detail_precision": 0.0, "details_hit": [], "details_miss": [d["value"] for d in ev["details"]],
                "pred_ts": None}
    top = next((r for r in recalled if r.get("timestamp") is not None), None)
    pred_ts = top["timestamp"] if top else None
    errs = [date_error_days(r["timestamp"], ev["ts"]) for r in recalled if r.get("timestamp") is not None]
    pool = stems(" ".join(r.get("content", "") or "" for r in recalled[:top_k_detail]))
    hit, miss = [], []
    for d in ev["details"]:
        parts = [stem(w) for w in words(d["value"])]
        (hit if parts and all(p in pool for p in parts) else miss).append(d["value"])
    return {"answered": True, "date_error_days": date_error_days(pred_ts, ev["ts"]),
            "date_error_best_of_k": min(errs) if errs else None,
            "detail_precision": round(len(hit) / len(ev["details"]), 3),
            "details_hit": hit, "details_miss": miss, "pred_ts": pred_ts}


def _med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 3) if xs else None


def summarize(rows: list[dict]) -> dict:
    def block(rs):
        ans = [r for r in rs if r["answered"]]
        return {"n": len(rs), "answered": len(ans),
                "median_date_error_days": _med([r["date_error_days"] for r in ans]),
                "mean_detail_precision": _mean([r["detail_precision"] for r in rs]),
                "exact_date_rate": (round(sum(1 for r in ans if r["date_error_days"] == 0) / len(ans), 3)
                                    if ans else None)}
    out = {"all": block(rows)}
    for ph in ("before_boot", "during_boot"):
        out[ph] = block([r for r in rows if r["phase"] == ph])
    out["by_source"] = {s: block([r for r in rows if r["source"] == s]) for s in sorted({r["source"] for r in rows})}
    return out


# --------------------------------------------------------------------------------------------- re-rank arms (J-2200)
# Own-episode origins: things Du lived or thought at a time. NOT episodes: reading (book text), syntheses
# (subconscious_synthesis, consolidation, gist, active_imagination), research/study/essay/peer material.
EPISODIC_ORIGINS = {"inner_thought", "lived", "action", "activity", "dream", "journal"}
# v2 (added after the first real run): 'letter' is a letter Du SENT -- his own act at a time -- and v1 demoted the
# correct fragment for 11/16 letter events. Kept as a separate arm so the v1 result stays reproducible.
EPISODIC_ORIGINS_V2 = EPISODIC_ORIGINS | {"letter"}
RERANK_ARMS = ("base", "episodic", "episodic_v2", "time_vote", "episodic_time_vote", "recency", "coarse_window", "oracle_best")
_WINDOW_DAYS = 7


def _day(ts):
    return to_date(ts).toordinal() if ts is not None else None


def _vote_order(pool: list[dict]) -> list[dict]:
    """Time anchor with no knowledge of the truth: each fragment votes 1/(rank+1) for its own calendar day and half
    that for the adjacent days; the day with the most votes wins (tie -> the day holding the better-ranked
    fragment); fragments within 1 d of the winning day come first (in pool order), then the rest. Fragments with no
    timestamp never vote and are placed with the rest."""
    dated = [(i, _day(f.get("timestamp"))) for i, f in enumerate(pool) if f.get("timestamp") is not None]
    if not dated:
        return list(pool)
    best_day, best_key = None, None
    for d in sorted({dd for _, dd in dated}):
        score = sum((1.0 if abs(dd - d) == 0 else 0.5) / (i + 1) for i, dd in dated if abs(dd - d) <= 1)
        first = min(i for i, dd in dated if dd == d)
        key = (-score, first)
        if best_key is None or key < best_key:
            best_day, best_key = d, key
    inside = [f for f in pool if f.get("timestamp") is not None and abs(_day(f["timestamp"]) - best_day) <= 1]
    ids = {id(f) for f in inside}
    return inside + [f for f in pool if id(f) not in ids]


def _window_order(pool: list[dict], anchor_day: int, half_width: int = _WINDOW_DAYS) -> list[dict]:
    """The coarse_window re-order around an arbitrary anchor (a calendar-day ordinal): dated fragments within
    +-half_width days of the anchor first, in pool order, then the rest in pool order; no fragment in the window ->
    the pool unchanged. coarse_window is this with anchor = the true event day."""
    inside = [f for f in pool if f.get("timestamp") is not None and abs(_day(f["timestamp"]) - anchor_day) <= half_width]
    ids = {id(f) for f in inside}
    return inside + [f for f in pool if id(f) not in ids] if inside else list(pool)


def rerank(pool: list[dict], arm: str, ev_ts: float | None = None, half_width: int = _WINDOW_DAYS) -> list[dict]:
    """Pure. `pool` = [{content, origin, timestamp, ...}] in trail order (strongest first). Returns the same
    fragments re-ordered (coarse_window keeps the rest after the in-window ones). `ev_ts` is used ONLY by the two
    oracle arms; `half_width` only by coarse_window (default 7 d = the J-2200 behaviour)."""
    if arm == "base":
        return list(pool)
    epi = [f for f in pool if f.get("origin") in EPISODIC_ORIGINS]
    rest = [f for f in pool if f.get("origin") not in EPISODIC_ORIGINS]
    if arm == "episodic":
        return epi + rest
    if arm == "episodic_v2":
        return ([f for f in pool if f.get("origin") in EPISODIC_ORIGINS_V2]
                + [f for f in pool if f.get("origin") not in EPISODIC_ORIGINS_V2])
    if arm == "time_vote":
        return _vote_order(pool)
    if arm == "episodic_time_vote":
        return _vote_order(epi) + _vote_order(rest) if epi else _vote_order(pool)
    if arm == "recency":
        dated = sorted([f for f in pool if f.get("timestamp") is not None], key=lambda f: -f["timestamp"])
        return dated + [f for f in pool if f.get("timestamp") is None]
    if arm in ("coarse_window", "oracle_best"):
        if ev_ts is None:
            raise ValueError(f"{arm} needs ev_ts")
        if arm == "coarse_window":
            return _window_order(pool, _day(ev_ts), half_width)
        dated = sorted([f for f in pool if f.get("timestamp") is not None],
                       key=lambda f: date_error_days(f["timestamp"], ev_ts))
        return dated + [f for f in pool if f.get("timestamp") is None]
    raise ValueError(f"unknown arm {arm!r}")


def sign_test_p(wins: int, losses: int) -> float | None:
    """Two-sided exact binomial sign test (ties excluded), p=0.5. None when there is nothing to test."""
    from math import comb
    n = wins + losses
    if n == 0:
        return None
    k = min(wins, losses)
    return round(min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n), 4)


def summarize_rerank(rows: list[dict]) -> dict:
    """rows = rerank_event rows. Per (pool_view, arm): aggregate + paired win/loss/tie vs base on top-1 date error
    (fewer days wins; an abstention pairs as a tie). Paired unit = (seed, event_ts, source)."""
    out: dict = {}
    for view in sorted({r["pool_view"] for r in rows}):
        vr = [r for r in rows if r["pool_view"] == view]
        base = {(r["seed"], r["event_ts"], r["source"]): r for r in vr if r["rerank_arm"] == "base"}
        views: dict = {}
        for arm in RERANK_ARMS:
            ar = [r for r in vr if r["rerank_arm"] == arm]
            if not ar:
                continue
            ans = [r for r in ar if r["answered"]]
            errs = [r["date_error_days"] for r in ans if r["date_error_days"] is not None]
            w = l = t = 0
            for r in ar:
                b = base.get((r["seed"], r["event_ts"], r["source"]))
                if b is None or arm == "base":
                    continue
                x, y = r["date_error_days"], b["date_error_days"]
                if x is None or y is None:
                    t += 1
                elif x < y:
                    w += 1
                elif x > y:
                    l += 1
                else:
                    t += 1
            views[arm] = {"n": len(ar), "answered": len(ans),
                          "median_date_error_days": _med(errs),
                          "mean_date_error_days": _mean(errs),
                          "within_3d_rate": round(sum(1 for e in errs if e <= 3) / len(errs), 3) if errs else None,
                          "exact_date_rate": round(sum(1 for e in errs if e == 0) / len(errs), 3) if errs else None,
                          "mean_detail_precision": _mean([r["detail_precision"] for r in ar]),
                          "top1_episodic_origin_rate": (round(sum(1 for r in ar if r.get("top1_origin") in EPISODIC_ORIGINS_V2)
                                                              / len(ar), 3) if ar else None),
                          "vs_base_wins_losses_ties": [w, l, t] if arm != "base" else None,
                          "vs_base_sign_p": sign_test_p(w, l) if arm != "base" else None}
        out[view] = views
    return out


# --------------------------------------------------------------------------------------------- noisy-anchor sweep (J-2333)
NOISY_ANCHOR_ERRORS = (0, 2, 4, 6, 8, 10, 12, 14, 16, 20)
NOISY_WRONG_RATES = (0.0, 0.2, 0.5)
NOISY_HALF_WIDTHS = (3, 7, 14)


def _top1_err_days(pool_days: list, true_day: int, anchor_day: int | None, hw: int) -> int | None:
    """Top-1 date error of _window_order(pool, anchor_day, hw) graded like grade() (top-1 = first DATED fragment),
    computed from the pool's precomputed day ordinals (None = undated). anchor_day None = base (trail order).
    Equivalent to re-ordering then grading; the test pins the equivalence."""
    if anchor_day is not None:
        for d in pool_days:
            if d is not None and abs(d - anchor_day) <= hw:
                return abs(d - true_day)
    for d in pool_days:
        if d is not None:
            return abs(d - true_day)
    return None


def _cell_stats(errs: list, base: list) -> tuple:
    pairs = [(x, y) for x, y in zip(errs, base) if x is not None and y is not None]
    e = [x for x in errs if x is not None]
    if not e:
        return None, None, sum(1 for x, y in pairs if x < y), sum(1 for x, y in pairs if x > y)
    return (statistics.median(e), sum(1 for x in e if x <= 3) / len(e),
            sum(1 for x, y in pairs if x < y), sum(1 for x, y in pairs if x > y))


def noisy_window_sweep(pool_by_event: list[dict], trials: int = 200, rng_seed: int = 2333, now: float | None = None,
                       anchor_errors=NOISY_ANCHOR_ERRORS, wrong_rates=NOISY_WRONG_RATES,
                       half_widths=NOISY_HALF_WIDTHS) -> dict:
    """Pure (deterministic given rng_seed). F-3021's noisy-anchor question, repeatable: how accurate must a coarse
    'when' anchor be before the coarse_window re-order beats trail order?

    pool_by_event = [{"event_ts": float, "views": {view_name: pool_in_trail_order}}]. Per view, per half-width hw,
    per anchor error m and wrong-anchor rate wr, each trial draws per event: with probability wr a WRONG anchor
    (uniform day in [now-30 d, now-1 d]), else anchor = true day + sign*m (random sign). Reported per cell, as the
    mean over trials: median top-1 date error, within-3-day rate, wins/losses vs base (trail order) on top-1 date
    error. Extra rows: oracle (m=0, wr=0), self_anchor (window centred on the base top-1 date; changes no top-1 by
    construction, `top1_changed` must be 0) and anchor_now (window centred on now: the clock-like anchors of F-3021).
    Events whose pool view has no dated fragment are abstentions: excluded from medians and from pairing."""
    rng = random.Random(rng_seed)
    if now is None:
        now = max((e["event_ts"] for e in pool_by_event), default=time.time()) + 86400
    now_day = _day(now)
    views = sorted({v for e in pool_by_event for v in e["views"]})
    out: dict = {"trials": trials, "rng_seed": rng_seed, "n_events": len(pool_by_event),
                 "anchor_errors": list(anchor_errors), "wrong_rates": list(wrong_rates),
                 "half_widths": list(half_widths), "views": {}}
    for v in views:
        evs = [(e, [(_day(f["timestamp"]) if f.get("timestamp") is not None else None) for f in e["views"].get(v, [])])
               for e in pool_by_event]
        true_days = [_day(e["event_ts"]) for e, _ in evs]
        base = [_top1_err_days(pd, td, None, 0) for (_, pd), td in zip(evs, true_days)]
        bm, b3, _, _ = _cell_stats(base, base)
        vb: dict = {"base": {"median_date_error_days": bm, "within_3d_rate": round(b3, 3) if b3 is not None else None,
                             "answered": sum(1 for x in base if x is not None)},
                    "cells": [], "oracle": {}, "self_anchor": {}, "anchor_now": {}}
        for hw in half_widths:
            # deterministic rows
            for name, anchors in (("oracle", true_days),
                                  ("anchor_now", [now_day] * len(evs)),
                                  ("self_anchor", [next((d for d in pd if d is not None), None) for _, pd in evs])):
                errs = [(_top1_err_days(pd, td, a, hw) if a is not None else b)
                        for (_, pd), td, a, b in zip(evs, true_days, anchors, base)]
                m, w3, w, l = _cell_stats(errs, base)
                row = {"median_date_error_days": m, "within_3d_rate": round(w3, 3) if w3 is not None else None,
                       "wins": w, "losses": l}
                if name == "self_anchor":
                    row["top1_changed"] = sum(1 for x, y in zip(errs, base) if x != y)
                vb[name][str(hw)] = row
            for mag in anchor_errors:
                for wr in wrong_rates:
                    meds, w3s, ws, ls = [], [], [], []
                    for _ in range(trials):
                        errs = []
                        for (_, pd), td in zip(evs, true_days):
                            a = now_day - rng.randint(1, 30) if rng.random() < wr else td + rng.choice((-1, 1)) * mag
                            errs.append(_top1_err_days(pd, td, a, hw))
                        m, w3, w, l = _cell_stats(errs, base)
                        if m is not None:
                            meds.append(m)
                            w3s.append(w3)
                        ws.append(w)
                        ls.append(l)
                    vb["cells"].append({"half_width": hw, "anchor_error_days": mag, "wrong_rate": wr,
                                        "median_date_error_days": round(statistics.mean(meds), 2) if meds else None,
                                        "within_3d_rate": round(statistics.mean(w3s), 3) if w3s else None,
                                        "wins": round(statistics.mean(ws), 1), "losses": round(statistics.mean(ls), 1)})
        out["views"][v] = vb
    return out


# --------------------------------------------------------------------------------------------- recall (real)
def _redirect_attrs(modules, data_dir_name: str = "data"):
    """(module, [attr]) for every module-level Path that points at a TOP-LEVEL file of a tree's data/ dir, so
    isolate(also=...) redirects each into the lab dir. Generic on purpose: ask() touches several modules'
    shadow logs / ledgers / embedding cache and enumerating them by hand is how live-store leaks happened."""
    pairs = []
    for m in modules:
        attrs = []
        for k, v in list(vars(m).items()):
            if isinstance(v, Path) and v.parent.name == data_dir_name and v.suffix:
                attrs.append(k)
        if attrs:
            pairs.append((m, attrs))
    return pairs


def drop_fragments_after(cutoff_ts: float | None, origins: list[str] | None = None,
                         except_origins: list[str] | None = None, random_n: int | None = None,
                         random_seed: int = 0) -> dict:
    """J-2636 (from F-3364): delete every fragment with timestamp > cutoff_ts, plus the rows that reference them
    (fragment_context, memory_links, memory_edges), from the ISOLATED DB COPY ONLY. Must be called inside the
    lab_env.isolate() block, where store.DB_PATH already points at the lab copy; refuses otherwise.
    Opt-in (--drop-after), default off. Returns counts.

    J-2652 (from F-3388) adds opt-in selectors, all default off, that narrow WHICH fragments the drop removes so the
    lever can be separated (defaults reproduce J-2636's behaviour exactly):
      origins        -- drop only fragments whose origin is in this list        (--drop-origins)
      except_origins -- drop only fragments whose origin is NOT in this list    (--drop-except-origins)
      random_n       -- drop a seeded random sample of exactly N of the selected fragments instead of all of them
                        (--drop-random-n / --drop-random-seed); with cutoff_ts=None the pool is the whole store
                        (the store-size null control)
    cutoff_ts=None means no date restriction."""
    import random
    from core.memory import store
    db = Path(str(store.DB_PATH)).resolve()
    assert db != Path("C:/Nascence/data/memory/nascence.db").resolve(), "refusing: live DB path"
    assert db.parent.parent.name != "data" or "_lab" in db.parts, f"refusing to delete from {db}: not a lab copy"
    out = {"cutoff_ts": cutoff_ts, "db": str(db), "origins": origins, "except_origins": except_origins,
           "random_n": random_n, "random_seed": random_seed}
    where, args = [], []
    if cutoff_ts is not None:
        where.append("timestamp > ?"); args.append(cutoff_ts)
    if origins:
        where.append("origin IN (%s)" % ",".join("?" * len(origins))); args += list(origins)
    if except_origins:
        where.append("(origin IS NULL OR origin NOT IN (%s))" % ",".join("?" * len(except_origins))); args += list(except_origins)
    assert where or random_n is not None, "drop_fragments_after: no selector given (refusing to delete the whole store)"
    sel = "SELECT fragment_id FROM memory_fragments" + (" WHERE " + " AND ".join(where) if where else "")
    with store._connect() as conn:
        out["fragments_total"] = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        conn.execute("CREATE TEMP TABLE _drop (fragment_id TEXT)")
        if random_n is None:
            conn.execute("INSERT INTO _drop " + sel, args)
        else:
            ids = sorted(r[0] for r in conn.execute(sel, args))
            out["random_pool"] = len(ids)
            pick = random.Random(random_seed).sample(ids, min(int(random_n), len(ids)))
            conn.executemany("INSERT INTO _drop VALUES (?)", [(i,) for i in pick])
        out["fragments_dropped"] = conn.execute("SELECT COUNT(*) FROM _drop").fetchone()[0]
        out["dropped_by_origin"] = dict(tuple(r) for r in conn.execute(
            "SELECT COALESCE(origin,'?'), COUNT(*) FROM memory_fragments WHERE fragment_id IN (SELECT fragment_id FROM _drop) "
            "GROUP BY 1 ORDER BY 2 DESC LIMIT 12").fetchall())
        out["dropped_dated_after_10_28"] = conn.execute(
            "SELECT COUNT(*) FROM memory_fragments WHERE timestamp > ? AND fragment_id IN (SELECT fragment_id FROM _drop)",
            (local_to_epoch(datetime(2026, 10, 28)),)).fetchone()[0]
        out["context_dropped"] = conn.execute("DELETE FROM fragment_context WHERE fragment_id IN (SELECT fragment_id FROM _drop)").rowcount
        out["links_dropped"] = conn.execute("DELETE FROM memory_links WHERE parent_id IN (SELECT fragment_id FROM _drop) "
                                            "OR child_id IN (SELECT fragment_id FROM _drop)").rowcount
        out["edges_dropped"] = conn.execute("DELETE FROM memory_edges WHERE src_id IN (SELECT fragment_id FROM _drop) "
                                            "OR dst_id IN (SELECT fragment_id FROM _drop)").rowcount
        conn.execute("DELETE FROM memory_fragments WHERE fragment_id IN (SELECT fragment_id FROM _drop)")
        conn.execute("DROP TABLE _drop")
        out["fragments_left"] = conn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        out["max_ts_left"] = conn.execute("SELECT MAX(timestamp) FROM memory_fragments").fetchone()[0]
    return out


def disable_recency() -> dict:
    """J-2652: recency multiplier OFF, in this process only. associative_recall.recall_trail seeds on
    sims * (0.4 + 0.6*imp) * (1.0 + 0.2*clip(1 - age/7, 0, 1)); the only consumer of the cached `age` array there is that
    multiplier, so serving a huge constant age from _matrix() makes it exactly 1.0 for every fragment. The monkeypatch
    lives in the probe process (the tree on disk and the live loop are untouched); refuses on the live DB path."""
    import numpy as np
    from core import associative_recall as ar
    from core.memory import store
    db = Path(str(store.DB_PATH)).resolve()
    assert db != Path("C:/Nascence/data/memory/nascence.db").resolve(), "refusing: live DB path"
    orig = ar._matrix

    def _matrix_no_age() -> dict:
        c = dict(orig())
        if c.get("age") is not None:
            c["age"] = np.full_like(c["age"], 1.0e6)   # clip(1 - 1e6/7, 0, 1) == 0  ->  recency == 1.0
        return c
    ar._matrix = _matrix_no_age
    return {"recency_multiplier": "off (age := 1e6 d in associative_recall._matrix, process-local)"}


def make_real_recall(k: int = 5, grounded_only: bool = True, lab_root: Path | None = None):
    """Returns (recall_fn, context_manager). Imports core BEFORE lab_env (F-2423) and asserts core came from this
    tree. The caller must run recall_fn only inside the `with`."""
    import core  # noqa: F401  (must precede lab_env)
    assert Path(core.__file__).resolve().is_relative_to(TREE), f"core from {core.__file__}, not {TREE}"
    sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
    import lab_env
    if lab_root is not None:   # J-2636: keep the (1 GB+) lab copies out of the live data/_lab; opt-in, default off
        lab_root = Path(lab_root)
        lab_root.mkdir(parents=True, exist_ok=True)
        lab_env._LAB_ROOT = lab_root
        lab_env._ISOLATE_OUTCOMES_LOG = lab_root / "_isolate_outcomes.jsonl"
    from core import memory_service, associative_recall, memory_edges
    pairs = _redirect_attrs([memory_service, associative_recall, memory_edges])
    iso = lab_env.isolate(also=pairs)

    live_emb = TREE / "data" / "embedding_matrix.npz"

    def seed_cache(lab_dir: Path):
        # read-only copy of the already-built embedding matrix so the probe does not re-embed 130k fragments.
        for cand in (_DEFAULT_DATA / "embedding_matrix.npz", live_emb):
            if cand.exists():
                import shutil
                shutil.copyfile(cand, lab_dir / "embedding_matrix.npz")
                return

    def recall(cue: str) -> list[dict]:
        from core.memory import store
        frags = memory_service.ask("autobio_probe", cue, k=k, grounded_only=grounded_only)
        ids = [f["fragment_id"] for f in frags if f.get("fragment_id")]
        ts = {}
        if ids:
            with store._connect() as conn:
                ph = ",".join("?" * len(ids))
                for r in conn.execute(f"SELECT fragment_id, timestamp FROM memory_fragments WHERE fragment_id IN ({ph})", ids):
                    ts[r["fragment_id"]] = r["timestamp"]
        return [{"content": f.get("content", ""), "timestamp": ts.get(f.get("fragment_id")),
                 "fragment_id": f.get("fragment_id"), "origin": f.get("origin")} for f in frags]

    return recall, iso, seed_cache


# --------------------------------------------------------------------------------------------- run
def run(data_dir: Path, out: Path, n: int, seed: int, now: float | None, boot_ts: float | None,
        recall_fn=None, ctx=None, seed_cache=None, dry_run: bool = False, lo_days=1.0, hi_days=30.0,
        grounded_only: bool = True, drop_after: float | None = None, lab_root: Path | None = None,
        drop_spec: dict | None = None, recency_off: bool = False) -> dict:
    now = now or time.time()
    boots = boot_starts(data_dir)
    if boot_ts is None:
        past = [b for b in boots if b <= now]
        boot_ts = past[-1] if past else None
    events = sample_events(data_dir, now, n, seed, boot_ts, lo_days, hi_days)
    run_id = f"autobio-{int(now)}-{uuid.uuid4().hex[:6]}"
    print(f"[autobio] run {run_id}: {len(events)} events, boot_ts="
          f"{datetime.fromtimestamp(boot_ts, _TZ).isoformat() if boot_ts else None}")
    if dry_run:
        for e in events:
            print(f"  {e['source']:13s} {to_date(e['ts'])}  cue={e['cue']!r}  details={[d['value'] for d in e['details']]}")
        return {"run_id": run_id, "events": len(events)}
    rows = []
    drop_info = None
    recency_info = None

    def do(rf):
        for e in events:
            try:
                rec = rf(e["cue"])
            except Exception as exc:
                print(f"[autobio] recall failed for {e['locator']}: {exc}")
                rec = []
            g = grade(e, rec)
            phase = "before_boot" if (boot_ts and e["ts"] < boot_ts) else "during_boot"
            rows.append({
                "ts": round(time.time(), 1), "kind": "event", "run_id": run_id, "source": e["source"],
                "event_ts": e["ts"], "event_date": str(to_date(e["ts"])), "age_days": round((now - e["ts"]) / 86400, 1),
                "phase": phase, "provenance": {"store": e["source"], "locator": e["locator"]},
                "cue": e["cue"], "details": e["details"],
                "recalled": [{"fragment_id": r.get("fragment_id"), "origin": r.get("origin"),
                              "date": str(to_date(r["timestamp"])) if r.get("timestamp") else None,
                              "snippet": (r.get("content") or "")[:160]} for r in rec[:3]],
                "judge": "deterministic-token-match/v1", "recall_arm": f"ask(grounded_only={grounded_only})", **{k: v for k, v in g.items() if k != "pred_ts"},
                "pred_date": str(to_date(g["pred_ts"])) if g["pred_ts"] else None})

    if recall_fn is not None:
        do(recall_fn)
    else:
        rf, iso, seed_cache = make_real_recall(grounded_only=grounded_only, lab_root=lab_root)
        with iso as lab_dir:
            seed_cache(lab_dir)
            if drop_after is not None or drop_spec:   # J-2636: events were sampled above from the JSONL stores, so the set is unaffected
                drop_info = drop_fragments_after(drop_after, **(drop_spec or {}))
                print(f"[autobio] drop-after: {drop_info}")
            if recency_off:   # J-2652
                recency_info = disable_recency()
                print(f"[autobio] {recency_info}")
            do(rf)
    summ = {"ts": round(time.time(), 1), "kind": "summary", "run_id": run_id,
            "boot_ts": boot_ts, "boot_iso": datetime.fromtimestamp(boot_ts, _TZ).isoformat() if boot_ts else None,
            "n_boots_seen": len(boots), "seed": seed, "recall_arm": f"ask(grounded_only={grounded_only})",
            "drop_after": drop_after, "drop_info": drop_info, "drop_spec": drop_spec, "recency_off": recency_info,
            "norm_note": "D-0456 bar (no sourced human norm): beat Du's own median top-1 date error 13-15 d and within-3-day hit rate 0.25",
            **summarize(rows)}
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        for r in rows + [summ]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    return summ


def run_rerank(data_dir: Path, out: Path, n: int, seeds: list[int], now: float | None, boot_ts: float | None,
               recall_fn=None, grounded_origins=None, top_k: int = 5,
               pool_k: int = 15, lo_days=1.0, hi_days=30.0, noisy_anchor: bool = False,
               noisy_trials: int = 200, noisy_seed: int = 2333) -> dict:
    """One wide-pool recall per event (all origins), then every re-rank arm over the identical pool, for both pool
    views. `recall_fn(cue)` -> pool list in trail order (injectable for tests). Writes `rerank_event` rows + one
    `rerank_summary` row to `out` (append). noisy_anchor=True (J-2333) also runs noisy_window_sweep over the same
    captured pools (one entry per seed x event row, as F-3021) and appends one `noisy_anchor_summary` row."""
    now = now or time.time()
    boots = boot_starts(data_dir)
    if boot_ts is None:
        past = [b for b in boots if b <= now]
        boot_ts = past[-1] if past else None
    run_id = f"autobio-rr-{int(now)}-{uuid.uuid4().hex[:6]}"
    per_seed = {s: sample_events(data_dir, now, n, s, boot_ts, lo_days, hi_days) for s in seeds}
    print(f"[autobio-rr] run {run_id}: seeds={seeds} events/seed={ {s: len(v) for s, v in per_seed.items()} }")
    rows: list[dict] = []
    pool_by_event: list[dict] = []

    def do(rf, gset):
        cache: dict[str, list[dict]] = {}
        for seed, events in per_seed.items():
            for e in events:
                if e["cue"] not in cache:
                    try:
                        cache[e["cue"]] = rf(e["cue"])
                    except Exception as exc:
                        print(f"[autobio-rr] recall failed for {e['locator']}: {exc}")
                        cache[e["cue"]] = []
                full = cache[e["cue"]]
                phase = "before_boot" if (boot_ts and e["ts"] < boot_ts) else "during_boot"
                view_pools = {"all": full, "grounded": [f for f in full if f.get("origin") in gset] if gset else full}
                pool_by_event.append({"event_ts": e["ts"], "views": view_pools})
                for view, pool in view_pools.items():
                    for arm in RERANK_ARMS:
                        top = rerank(pool, arm, e["ts"])[:top_k]
                        g = grade(e, top)
                        rows.append({"ts": round(time.time(), 1), "kind": "rerank_event", "run_id": run_id,
                                     "seed": seed, "source": e["source"], "event_ts": e["ts"],
                                     "event_date": str(to_date(e["ts"])), "age_days": round((now - e["ts"]) / 86400, 1),
                                     "phase": phase, "pool_view": view, "rerank_arm": arm, "pool_size": len(pool),
                                     "top1_origin": top[0].get("origin") if top else None,
                                     "top1_date": str(to_date(top[0]["timestamp"])) if top and top[0].get("timestamp") else None,
                                     "judge": "deterministic-token-match/v1",
                                     **{k: v for k, v in g.items() if k != "pred_ts"}})

    if recall_fn is not None:
        do(recall_fn, set(grounded_origins or []))
    else:
        rf, iso, seed_cache = make_real_recall(k=pool_k, grounded_only=False)
        from core import associative_recall
        with iso as lab_dir:
            seed_cache(lab_dir)
            do(rf, set(associative_recall._GROUNDED_ORIGINS))
    uniq = len({(r["event_ts"], r["source"]) for r in rows})
    summ = {"ts": round(time.time(), 1), "kind": "rerank_summary", "run_id": run_id, "seeds": seeds, "n_per_seed": n,
            "unique_events": uniq, "boot_ts": boot_ts, "pool_k": pool_k, "top_k": top_k,
            "episodic_origins": sorted(EPISODIC_ORIGINS), "episodic_origins_v2": sorted(EPISODIC_ORIGINS_V2), "window_days": _WINDOW_DAYS,
            "oracle_arms_note": "coarse_window and oracle_best read the true date: bounds, not designs",
            "arms": summarize_rerank(rows)}
    extra = []
    if noisy_anchor:
        extra.append({"ts": round(time.time(), 1), "kind": "noisy_anchor_summary", "run_id": run_id, "seeds": seeds,
                      "n_per_seed": n, "pool_k": pool_k,
                      "note": ("J-2333 / F-3021: anchor = true day +- m (random sign) or, at wrong_rate, a uniform day "
                               "1-30 d ago; oracle/self_anchor/anchor_now rows are deterministic; cells are means "
                               "over trials"),
                      **noisy_window_sweep(pool_by_event, noisy_trials, noisy_seed, now)})
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as f:
        for r in rows + [summ] + extra:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    return summ


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--data-dir", default=str(_DEFAULT_DATA), help="stores to sample events from (read-only)")
    ap.add_argument("--out", default=None, help="rows file (default <data-dir>/autobio_recall_probe.jsonl)")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--now", type=float, default=None, help="epoch 'now' for the 1-30 d window (default: time.time())")
    ap.add_argument("--boot-ts", type=float, default=None, help="override: epoch of the current boot")
    ap.add_argument("--all-origins", action="store_true",
                    help="ask(grounded_only=False): include non-grounded origins (inner thoughts, dreams). Default True = the API default")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--drop-after", default=None,
                    help="J-2636: YYYY-MM-DD (NZ local midnight) -- delete every fragment dated AFTER this from the "
                         "ISOLATED DB copy before recall (event sampling is unaffected). Default off.")
    ap.add_argument("--drop-origins", default=None,
                    help="J-2652: comma list; with --drop-after (or alone) delete ONLY fragments of these origins from the "
                         "ISOLATED copy (e.g. inner_thought; chapter,session_summary). Default off.")
    ap.add_argument("--drop-except-origins", default=None,
                    help="J-2652: comma list; delete only fragments whose origin is NOT in it (the complement partition). Default off.")
    ap.add_argument("--drop-random-n", type=int, default=None,
                    help="J-2652: delete a seeded random sample of exactly N of the selected fragments (whole store unless "
                         "--drop-after/--drop-origins narrow the pool): the store-size null control. Default off.")
    ap.add_argument("--drop-random-seed", type=int, default=0, help="J-2652: RNG seed for --drop-random-n")
    ap.add_argument("--recency-off", action="store_true",
                    help="J-2652: set associative_recall's recency multiplier to 1.0 inside the probe process only "
                         "(lab copy; no tree edit). Default off.")
    ap.add_argument("--lab-root", default=None, help="J-2636: directory for lab_env's lab dirs instead of data/_lab")
    ap.add_argument("--rerank", action="store_true",
                    help="J-2200: wide-pool recall once per event, then every offline re-rank arm (see docstring)")
    ap.add_argument("--seeds", default="0,1,2,3", help="comma list of sampling seeds for --rerank")
    ap.add_argument("--rerank-noisy-anchor", action="store_true",
                    help="J-2333: --rerank plus the F-3021 noisy-anchor window sweep (one noisy_anchor_summary row)")
    ap.add_argument("--noisy-trials", type=int, default=200, help="random trials per noisy-anchor cell")
    a = ap.parse_args(argv)
    dd = Path(a.data_dir)
    out = Path(a.out) if a.out else dd / "autobio_recall_probe.jsonl"
    if a.rerank or a.rerank_noisy_anchor:
        run_rerank(dd, out, a.n, [int(x) for x in a.seeds.split(",") if x != ""], a.now, a.boot_ts,
                   noisy_anchor=a.rerank_noisy_anchor, noisy_trials=a.noisy_trials)
        return
    drop_ts = None
    if a.drop_after:
        y, m, d = (int(x) for x in a.drop_after.split("-"))
        drop_ts = local_to_epoch(datetime(y, m, d))
    spec = {}
    if a.drop_origins:
        spec["origins"] = [x for x in a.drop_origins.split(",") if x]
    if a.drop_except_origins:
        spec["except_origins"] = [x for x in a.drop_except_origins.split(",") if x]
    if a.drop_random_n is not None:
        spec["random_n"] = a.drop_random_n
        spec["random_seed"] = a.drop_random_seed
    run(dd, out, a.n, a.seed, a.now, a.boot_ts, dry_run=a.dry_run, grounded_only=not a.all_origins,
        drop_after=drop_ts, lab_root=Path(a.lab_root) if a.lab_root else None,
        drop_spec=spec or None, recency_off=a.recency_off)


if __name__ == "__main__":
    main()
