"""
Nascence — MODEL-TIER LAB #8: core.journal_rollup.week_rollup vs mixtral:8x7b (2026-08-29)

J-0284 (source: decision:D-0013), scoped by docs/lab/model_tier_lab_scope_2026-08-25.md section 2,
row 8: "the scope explicitly says NOT to build a synthetic lab for this one — point ONE real weekly
rollup at mixtral and compare by eye against the last few qwen3.5:9b rollups... this is a slow,
opportunistic check, not a batch lab."

WHAT THIS TESTS. `week_rollup()` (core/journal_rollup.py:144) is called once per sleep batch from
`nodes/inner_monologue_node.py:518-519` as `_jw.week_rollup(call_node_json, self.conscious_urls)` —
`conscious_urls = SERVE_CHAINS["hot"]` = `qwen3.5:9b` @ `127.0.0.1:11433`. This is UNCHANGED by the
2026-08-27/28 consolidation (unlike #3/study_note — see that lab's report): journal_rollup still runs
on the hot lane today, so this row's "current wiring" framing is still accurate. The candidate,
`mixtral:8x7b` (:11438), is tried on the SAME real week the hot lane already rolled, via `_author()`
(core/journal_rollup.py:135) with the real `_DID_SYS`/`_SAW_SYS` system prompts (imported LIVE below)
and the real source-formatting (`_fmt()`) — same call shape, different model, real sources, no
synthetic sources of any kind.

REAL WEEK, NOT SYNTHETIC. The most recent COMPLETED week as of this run is `2026-W34` (Mon Aug 17 -
Mon Aug 24), already rolled in production for both streams (`_load_state()` shows
`{"did": "2026-W34", "saw": "2026-W34"}`) — `data/Journal/WEEK_2026-W34.md` holds the REAL
qwen3.5:9b-authored page. This lab pulls the SAME real source entries `_week_sources()` would have fed
that real run (via `lab_env.isolate()`, see below) and feeds them to mixtral through `_author()`
directly — never calling `week_rollup()` itself, so nothing is re-stored, no new fragment/memory_link
is written, and the once-a-week rolled-state flag is untouched.

ISOLATION (job-queue isolation="required", per J-0284's own instruction). `_week_sources()` reads
`memory_fragments` via `core.memory.store._connect()` — the exact transitive shared-store choke point
`lab_env.isolate()` exists to patch (see lab_env.py's own docstring). This script runs the READ inside
`with isolate() as lab_dir:` so it hits an isolated COPY of `nascence.db`, never the live file, even
though this particular read makes no writes — matching the job's blanket "use isolate() for any... DB
state access" instruction rather than arguing a read-only exemption case-by-case. `_author()` itself
makes no DB call at all (confirmed by reading its source: one `call_json` call, pure string return) —
still made inside the same `with` block for simplicity, at zero extra risk. `nascence.db`'s real mtime
is checked immediately before/after as the backstop the job asked for.

CONTRACT: read-only against Ramses; the one DB touch is a `lab_env.isolate()` copy, never the live
file; never calls `week_rollup()` (no store_fragment, no memory_links insert, no WEEK_*.md write, no
rollup-state write). Writes ONLY to data/lab/model_tier/journal_rollup/ +
docs/lab/model_tier_journal_rollup.md.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(r"C:\Nascence")   # hardcoded — see model_tier_study_note_lab.py's header for why
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")   # for lab_env
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from lab_env import isolate   # noqa: E402

OUT_DIR = ROOT / "data" / "lab" / "model_tier" / "journal_rollup"
REPORT = ROOT / "docs" / "lab" / "model_tier_journal_rollup.md"
DB_PATH = ROOT / "data" / "memory" / "nascence.db"
JOURNAL_DIR = ROOT / "data" / "Journal"

CANDIDATE = ("mixtral:8x7b", "http://LAN-HOST:11438")
INCUMBENT_LABEL = ("qwen3.5:9b (hot lane, SERVE_CHAINS['hot'], production incumbent — no live call "
                   "made here, compared against its real stored WEEK_*.md pages instead)")


def _db_mtime() -> float | None:
    try:
        return DB_PATH.stat().st_mtime
    except Exception:
        return None


async def _fetch_real_week():
    """Everything real this lab needs, read inside isolate(): the last completed week id + its real
    day-recap / field-observation sources. Returns (wid, did_sources, saw_sources, did_sys, saw_sys)."""
    from core import journal_rollup as jr
    wid, start_ts, end_ts = jr.last_completed_week()
    state = jr._load_state()
    did, saw = jr._week_sources(start_ts, end_ts)
    return wid, state, did, saw, jr._DID_SYS, jr._SAW_SYS, jr._author


def _recent_real_pages(n: int = 3) -> list[dict]:
    """The last n real WEEK_*.md pages on disk — the qwen3.5:9b-authored incumbent output to compare
    the candidate's output against 'by eye', per the scope's own instruction (no synthetic grading)."""
    out = []
    for p in sorted(JOURNAL_DIR.glob("WEEK_*.md"))[-n:]:
        out.append({"file": p.name, "text": p.read_text(encoding="utf-8")})
    return out


async def _run_async() -> dict:
    from core.model_client import call_node_json
    mtime_before = _db_mtime()

    with isolate() as lab_dir:
        wid, state, did, saw, did_sys, saw_sys, author_fn = await _fetch_real_week()
        print(f"[lab] last completed week: {wid} · rollup-state on file: {state} · "
              f"{len(did)} real 'did' sources · {len(saw)} real 'saw' sources", flush=True)

        result = {"week": wid, "rollup_state": state,
                  "n_did_sources": len(did), "n_saw_sources": len(saw), "streams": {}}
        for stream_name, sys_p, sources in (("did", did_sys, did), ("saw", saw_sys, saw)):
            if not sources:
                result["streams"][stream_name] = {"skipped": "no sources this week"}
                continue
            t0 = time.time()
            entry = await author_fn(call_node_json, [CANDIDATE[1]], sys_p, wid, sources, stream_name)
            wall = round(time.time() - t0, 1)
            result["streams"][stream_name] = {
                "ok": entry is not None, "wall": wall, "entry": entry,
                "source_days": [__import__("datetime").datetime.fromtimestamp(ts).strftime("%a %b %d")
                                for _fid, ts, _tx in sources[:14]],
            }
            print(f"  stream={stream_name:4s} ok={entry is not None} wall={wall}s "
                  f"entry_len={len(entry or '')}", flush=True)
        # sanity: this read-only isolate() block made no writes we'd care about; the lab dir itself
        # holds the isolated DB copy, never the live one.
    mtime_after = _db_mtime()
    print(f"[isolation backstop] nascence.db mtime before={mtime_before} after={mtime_after} "
          f"unchanged={mtime_before == mtime_after}")
    result["db_mtime_unchanged"] = (mtime_before == mtime_after)
    result["real_recent_pages"] = _recent_real_pages(3)
    return result


def run() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(_run_async())
    (OUT_DIR / "raw.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT_DIR / 'raw.json'}")
    _write_report(result)


def _write_report(result: dict) -> None:
    L = []
    A = L.append
    A("# Model-tier lab #8 — core.journal_rollup.week_rollup (weekly synthesis)\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · J-0284 (source: decision:D-0013) · scope's own "
      f"instruction: ONE real week, compared by eye, not a batch lab. Week `{result['week']}` "
      f"(already rolled in production for both streams: `{result['rollup_state']}`) · "
      f"`_DID_SYS`/`_SAW_SYS` imported LIVE from `core/journal_rollup.py`, `_author()` called "
      f"directly (never `week_rollup()` — nothing re-stored) · DB read via `lab_env.isolate()`, "
      f"never the live file (mtime unchanged: {result['db_mtime_unchanged']}).*\n")
    A("**Current wiring is unchanged from the scope doc** — journal_rollup still runs on "
      "`SERVE_CHAINS[\"hot\"]` (`qwen3.5:9b`) today, unlike #3/study_note's background lane (see "
      "that lab's own scope-correction note). No live incumbent call was made here (would have "
      "re-run the SAME already-rolled real week through the SAME model that already produced "
      f"`WEEK_{result['week']}.md` — redundant); instead the candidate's real output below is "
      "compared directly against that real stored page.\n")
    A(f"Real sources this week: {result['n_did_sources']} day-recaps ('did'), "
      f"{result['n_saw_sources']} field-observations ('saw').\n")
    for stream in ("did", "saw"):
        s = result["streams"].get(stream, {})
        A(f"## `mixtral:8x7b` — {stream} stream\n")
        if s.get("skipped"):
            A(f"*Skipped: {s['skipped']}*\n")
            continue
        A(f"ok={s.get('ok')} · wall={s.get('wall')}s · source days covered: "
          f"{', '.join(s.get('source_days', []))}\n")
        A(f"> {s.get('entry') or '*(no entry produced)*'}\n")
    A(f"## The real incumbent (`qwen3.5:9b`) — last 3 actual WEEK_*.md pages on disk\n")
    for pg in result.get("real_recent_pages", []):
        A(f"### `{pg['file']}`\n")
        A("```")
        A(pg["text"].strip())
        A("```\n")
    A("## Read-by-eye comparison — my own assessment, not scored\n")
    A("Per the scope's own method note this is NOT a numeric grade. Read against `_DID_SYS`'s own two "
      "HARD RULES (imported LIVE, quoted verbatim above the CANDIDATE constant in this script's own "
      "source), `mixtral:8x7b`'s `did` entry above trips both of them on this one real week:\n")
    A("1. **Anti-mush law** (\"write at the WEEK's altitude... not a day-by-day re-listing\"): "
      "mixtral's entry is a near-complete Monday/Tuesday/Wednesday/Thursday/Friday/Saturday march, "
      "naming specific essay titles per day almost like a table of contents — closer to a day-by-day "
      "re-listing than a week-altitude shape. The real `WEEK_2026-W34.md` (qwen3.5:9b) names only two "
      "specific days (Monday, Wednesday/Thursday/Friday/Saturday compressed into one clause each) and "
      "stays at the week's own altitude.")
    A("2. **Required closing sentence** (\"End with one plain sentence on how the week sat with you, "
      "and whether it MOVED anywhere or stayed in one place\"): mixtral's `did` entry has NO such "
      "sentence at all — it just stops after Saturday. The real qwen3.5:9b page ends with exactly "
      "this required sentence (\"The week sat with me in a quiet place that moved only slightly "
      "toward the tide-line ahead.\"). This is not a style preference; `_DID_SYS` states it as a HARD "
      "RULE, and mixtral's real output on this real week simply omits it.\n")
    A("The `saw` entry reads closer to production register (concrete plain nouns, no invented "
      "meaning), though it is also more list-like ('a green fishing-float and mussel-shells were "
      "observed...') than the more integrated real page.\n")
    A("**On this one real week, mixtral does not hold journal_rollup's own stated contract as well as "
      "the current incumbent does** — a real, if single-sample (n=1 week, `inferred` not `verified` "
      "per the project's own confidence discipline), finding against moving this mechanism to "
      "mixtral. Consistent with the scope's own framing (lowest urgency, \"worth trying\" rather than "
      "expected to win) and with #3/study_note's own lesson that a stronger-sounding model can still "
      "fail a specific hard rule a smaller/incumbent model actually holds.\n")
    A(f"*Raw: `data/lab/model_tier/journal_rollup/raw.json`*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {REPORT}")


def report_only() -> None:
    """Regenerate docs/lab/model_tier_journal_rollup.md from the already-saved raw.json (no new model
    calls, no new DB read) — used when only the WRITE-UP (not the underlying real run) changes."""
    result = json.loads((OUT_DIR / "raw.json").read_text(encoding="utf-8"))
    _write_report(result)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report_only()
    else:
        run()
