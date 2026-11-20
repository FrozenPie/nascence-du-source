"""
Nascence -- decoupled SHADOW judge for the episodic buffer's bound scene (P-0006).  J-2808 / F-3453.  RESTART-GATED.

THE GAP.  nodes/episodic_buffer_node.py binds the cycle's streams (what was said, what is remembered, what is felt, what is
attended) into a scene, lists 0-3 DISSONANCE entries, and rates its own `coherence`.  Nothing judged any of it: no
judge_panel call, no second model, no log comparing a scene with its inputs.  F-3453 measured the self-rating: of 3,629 rows
the value 0.85 is 49 percent, five values cover 85 percent, 39 distinct values; corr(coherence, n_dissonance) = -0.57 (the
output grading itself consistently with its own list) but corr(coherence, n_recall_tensions) = -0.09 (no tie to the real
input conflict).  core/competence.py had been calling that number "structural, not self-rated" (docstrings fixed in the same
job): the buffer model's OWN number is what it is.

THIS INSTRUMENT.  For a SAMPLE of cycles, a model from a DIFFERENT family than the buffer (the buffer runs on the hot lane,
qwen3.5:9b; the judge chain is gemma4:12b on the local CPU hub :11439, then falcon3:7b :11440) reads ONLY the buffer's own
user prompt (the streams, rebuilt by the node's own _build_prompt so the judge sees exactly what the buffer saw) plus the
scene and the dissonance list, and answers two things:
  (a) for each dissonance entry: is it supported by a pair of streams (both sides present in the streams, and they do
      conflict)?  yes/no per entry;
  (b) does the scene carry any specific detail that is absent from every stream?  yes/no.
The judge is never shown the buffer's coherence number, and never falls through to the hot lane (a Qwen generator would be
judging its own lane).  Ramses is not in the chain (the founder's gaming machine; the CPU hubs are enough for a sample).

SHADOW AND FAIL-OPEN.  Fire-and-forget: on_scene_bound() is synchronous, cheap, and schedules a background task; the cycle
never waits and never sees a result.  One judgement in flight at a time (a busy judge DROPS the sample, counted into the next
row's `dropped_busy`, never queued); 1 cycle in SAMPLE_EVERY is sampled.  Any failure -- hub down, unparseable reply, write
refused -- is swallowed (a fail_open row is logged when the call itself failed, so a silent instrument is visible).  Nothing
reaches Du, the cycle, the competence model, the re-bind gate or any prompt (the world answers, never leads).

READER.  compare() below sets the judge's unsupported rate beside the buffer's own coherence (distribution, correlation, high
versus low coherence); scripts/episodic_buffer_judge_report.py prints it.  It is READ at 100 valid rows (READY_ROWS), the named
read job spawned with this build.  A POSITIVE CONTROL (planted unsupported entries and a planted invented detail; see
control_cases() and scripts/episodic_buffer_judge_control.py) has to pass before any rate from this log is quoted -- the F-3812
lesson from the guidance judge: a judge that says "supported" to everything produces a flattering zero.  compare() therefore
reports control='not run' until data/episodic_buffer_judge_control.json exists for the CURRENT prompt fingerprint.

Kill switch: SHADOW_ENABLED = False is a complete no-op (no hub call, no row).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path

from core import profile, shadow_log

logger = logging.getLogger("nascence.episodic_buffer_judge")

_DATA = Path(__file__).parent.parent / "data"
SHADOW_LOG = _DATA / "episodic_buffer_judge_shadow.jsonl"        # tests temp-path this
CONTROL_FILE = _DATA / "episodic_buffer_judge_control.json"      # tests temp-path this

SHADOW_ENABLED = True
SAMPLE_EVERY = 3            # judge 1 cycle in N (a process counter, not random: the sample is reproducible)
READY_ROWS = 100            # the comparison with the buffer's own coherence is read at this many valid rows
STREAMS_CAP = 6000          # chars of the buffer's user prompt sent to the judge (row records streams_chars / truncated)
SCENE_CAP = 900
ENTRY_CAP = 240
JUDGE_URLS = ["http://127.0.0.1:11439", "http://127.0.0.1:11440"]   # gemma4:12b, then falcon3:7b -- never the hot lane

_SYSTEM = (
    "You audit one binding step of a mind. A STREAMS block lists what the mind was given for one moment (what was said, "
    "what it remembers, what it feels, what it attends to). A SCENE was written from those streams, followed by a numbered "
    "list of DISSONANCE entries, each claiming two of the streams do not fit together. Judge only against the STREAMS text. "
    "Answer two things. (1) For each numbered dissonance entry: true when BOTH sides of the contradiction it names are really "
    "present in the streams AND they do conflict; false when a side is missing from the streams or the conflict is invented. "
    "(2) scene_invented: true when the SCENE states a specific fact, quote, name, event or sensation that appears in none of "
    "the streams; false when everything specific in the scene can be found in the streams (re-wording and first-person "
    "framing are fine). When unsure about an entry answer false; when unsure about the scene answer false. "
    "Output ONLY JSON: {\"dissonance\": [true or false, one per numbered entry, in order], "
    "\"scene_invented\": true or false, \"why\": \"under 25 words\"}"
)

_state = {"seen": 0, "dropped_busy": 0, "inflight": False}
_tasks: set = set()


def build_user(streams: str, scene: str, dissonance: list) -> str:
    """The exact user message the judge sees. ONE builder, used by the live path and by the positive control, so the control
    tests the instrument as it runs.  The buffer's coherence number is NOT in it."""
    entries = [str(d)[:ENTRY_CAP] for d in (dissonance or [])]
    dl = "\n".join(f"{i + 1}. {e}" for i, e in enumerate(entries)) if entries else "(none)"
    return ("STREAMS:\n" + (streams or "")[:STREAMS_CAP] + "\n\nSCENE:\n" + (scene or "")[:SCENE_CAP]
            + "\n\nDISSONANCE:\n" + dl)


def prompt_fingerprint() -> str:
    """Short hash of everything that shapes what the judge reads (system prompt, message shape, caps, chain). The control
    file is bound to it, so any prompt change closes the 'control passed' flag until the control is re-run."""
    probe = build_user("@S@", "@C@", ["@D@"])
    raw = "|".join((_SYSTEM, probe, str(STREAMS_CAP), str(SCENE_CAP), str(ENTRY_CAP), ",".join(JUDGE_URLS)))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _as_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "yes", "1"):
            return True
        if s in ("false", "no", "0"):
            return False
    if isinstance(v, (int, float)) and v in (0, 1):
        return bool(v)
    return None


def parse_verdict(data, n_entries: int):
    """Validate the judge's JSON against the number of entries asked about.  Returns
    {'supported': [bool]*n, 'scene_invented': bool, 'why': str} or None when the shape is wrong (never guesses a
    missing or short list: a wrong-length list would pair verdicts with the wrong entries)."""
    try:
        if not isinstance(data, dict):
            return None
        raw = data.get("dissonance", [])
        if n_entries == 0 and (raw is None or raw == []):
            raw = []
        if not isinstance(raw, list) or len(raw) != n_entries:
            return None
        sup = [_as_bool(x) for x in raw]
        if any(x is None for x in sup):
            return None
        inv = _as_bool(data.get("scene_invented"))
        if inv is None:
            return None
        return {"supported": sup, "scene_invented": inv, "why": str(data.get("why", ""))[:200]}
    except Exception:
        return None


async def judge_scene(streams: str, scene: str, dissonance: list, served: dict | None = None):
    """The judge call. Returns the parsed verdict dict, or None (hub chain down / unparseable). Never raises.  `served`
    receives {'url','model','fallback'} for the hub that answered."""
    try:
        from core.model_client import call_node_json
        data = await call_node_json(JUDGE_URLS, _SYSTEM, build_user(streams, scene, dissonance),
                                    max_tokens=160, temperature=0.0, timeout=180, retries=1, tier=3, served=served)
        return parse_verdict(data, len(dissonance or []))
    except Exception as exc:
        logger.debug("[ebuf-judge] judge call failed (non-fatal): %s", exc)
        return None


def _row(snap: dict, verdict, served: dict, dropped: int) -> dict:
    ok = isinstance(verdict, dict)
    sup = verdict["supported"] if ok else None
    return {
        "ts": round(time.time(), 3),
        "cycle_id": snap.get("cycle_id"),
        "coherence": snap.get("coherence"),
        "n_dissonance": snap.get("n_dissonance"),
        "n_recall_tensions": snap.get("n_recall_tensions"),
        "passes": snap.get("passes"),
        "streams_chars": snap.get("streams_chars"),
        "streams_truncated": bool(snap.get("streams_chars", 0) > STREAMS_CAP),
        "scene_chars": snap.get("scene_chars"),
        "dissonance_supported": sup,
        "n_unsupported": (sum(1 for x in sup if not x) if ok else None),
        "scene_invented": (verdict["scene_invented"] if ok else None),
        "why": (verdict["why"] if ok else None),
        "judge_url": served.get("url"),
        "judge_model": served.get("model"),
        "judge_fallback": served.get("fallback"),
        "buffer_lane": "hot",
        "sample_every": SAMPLE_EVERY,
        "dropped_busy": dropped,          # samples dropped because a judgement was still running, since the last row
        "fail_open": not ok,              # True = hub chain down / unparseable: no verdict, not a 'supported' one
        "fingerprint": prompt_fingerprint(),
    }


def record(snap: dict, verdict, served: dict, dropped: int = 0) -> bool:
    """Append one row.  guard_path at write time (a non-live importer's write to the real data/ path is refused, not
    redirected).  Never raises."""
    try:
        path = profile.guard_path(SHADOW_LOG)
        return shadow_log.append(Path(path), _row(snap, verdict, served, dropped))
    except Exception as exc:
        logger.debug("[ebuf-judge] record failed (non-fatal): %s", exc)
        return False


async def _judge_and_record(snap: dict, streams: str, dropped: int) -> None:
    try:
        served: dict = {}
        verdict = await judge_scene(streams, snap["scene"], snap["dissonance"], served)
        record(snap, verdict, served, dropped)
    except Exception as exc:
        logger.debug("[ebuf-judge] background judge failed (non-fatal): %s", exc)
    finally:
        _state["inflight"] = False


def on_scene_bound(node, state, cycle_id: str = "", passes: int = 0) -> bool:
    """Called once per cycle by the orchestrator after the re-bind loop, with the FINAL bound scene.  Synchronous and cheap:
    samples 1 cycle in SAMPLE_EVERY, drops the sample when a judgement is still in flight, otherwise snapshots the scene and
    schedules the judgement as a background task.  Returns True when a judgement was scheduled.  Never raises."""
    try:
        if not SHADOW_ENABLED:
            return False
        sc = getattr(state, "episodic_scene", None)
        if sc is None or not str(getattr(sc, "scene", "") or "").strip():
            return False
        _state["seen"] += 1
        if (_state["seen"] - 1) % max(1, SAMPLE_EVERY) != 0:
            return False
        if _state["inflight"]:
            _state["dropped_busy"] += 1
            return False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return False
        streams = node._build_prompt(state)          # pure: exactly the user prompt the buffer was given
        rec = getattr(state, "recall", None)
        snap = {
            "cycle_id": str(cycle_id or getattr(state, "cycle_id", "") or ""),
            "scene": str(sc.scene),
            "dissonance": [str(d) for d in (sc.dissonance or [])],
            "coherence": round(float(sc.coherence), 4),
            "n_dissonance": len(sc.dissonance or []),
            "n_recall_tensions": len(getattr(rec, "tensions", None) or []) if rec is not None else 0,
            "passes": int(passes or 0),
            "streams_chars": len(streams),
            "scene_chars": len(str(sc.scene)),
        }
        dropped, _state["dropped_busy"] = _state["dropped_busy"], 0
        _state["inflight"] = True
        t = loop.create_task(_judge_and_record(snap, streams, dropped))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)
        return True
    except Exception as exc:
        _state["inflight"] = False
        logger.debug("[ebuf-judge] on_scene_bound skipped (non-fatal): %s", exc)
        return False


# -- the reader --------------------------------------------------------------------------------------------------------

def _pearson(xs: list, ys: list):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sxx * syy) ** 0.5, 3)


def _control_state() -> dict:
    try:
        d = json.loads(Path(CONTROL_FILE).read_text(encoding="utf-8"))
        if d.get("fingerprint") == prompt_fingerprint():
            return {"control": "passed" if d.get("passed") else "FAILED", "control_detail": d.get("detail")}
        return {"control": "stale (prompt changed since the control ran)"}
    except Exception:
        return {"control": "not run"}


def compare(path: Path | None = None) -> dict:
    """The judge's unsupported rate beside the buffer's own coherence.  Valid rows only (fail_open rows counted, not used).
    Per-row 'unsupported' = any dissonance entry judged unsupported OR the scene judged to carry an invented detail.
    A rate is quoted only when the control has passed AND at least READY_ROWS valid rows exist; otherwise the figures are
    returned under 'preview' with ready=False so they cannot be mistaken for a finding."""
    rows = shadow_log.read_rows(Path(path) if path else SHADOW_LOG)
    valid = [r for r in rows if not r.get("fail_open") and r.get("coherence") is not None
             and isinstance(r.get("dissonance_supported"), list)]
    out = {"rows": len(rows), "valid_rows": len(valid), "fail_open_rows": sum(1 for r in rows if r.get("fail_open")),
           "ready_rows": READY_ROWS, **_control_state()}
    if not valid:
        out["ready"] = False
        return out
    coh = [float(r["coherence"]) for r in valid]
    uns = [1.0 if (r.get("n_unsupported") or r.get("scene_invented")) else 0.0 for r in valid]
    entries = sum(len(r["dissonance_supported"]) for r in valid)
    bad_entries = sum(int(r.get("n_unsupported") or 0) for r in valid)
    lo = [u for c, u in zip(coh, uns) if c < 0.85]
    hi = [u for c, u in zip(coh, uns) if c >= 0.85]
    dist: dict = {}
    for c in coh:
        dist[round(c, 2)] = dist.get(round(c, 2), 0) + 1
    top5 = sum(sorted(dist.values(), reverse=True)[:5])
    figs = {
        "rows_unsupported_rate": round(sum(uns) / len(uns), 3),
        "dissonance_entries": entries,
        "dissonance_unsupported_rate": (round(bad_entries / entries, 3) if entries else None),
        "scene_invented_rate": round(sum(1 for r in valid if r.get("scene_invented")) / len(valid), 3),
        "coherence_mean": round(sum(coh) / len(coh), 3),
        "coherence_distinct": len(dist),
        "coherence_top5_share": round(top5 / len(coh), 3),
        "corr_coherence_vs_unsupported": _pearson(coh, uns),
        "unsupported_rate_coh_ge_085": (round(sum(hi) / len(hi), 3) if hi else None),
        "n_coh_ge_085": len(hi),
        "unsupported_rate_coh_lt_085": (round(sum(lo) / len(lo), 3) if lo else None),
        "n_coh_lt_085": len(lo),
        "truncated_streams_rows": sum(1 for r in valid if r.get("streams_truncated")),
        "dropped_busy_total": sum(int(r.get("dropped_busy") or 0) for r in rows),
    }
    out["ready"] = len(valid) >= READY_ROWS and out["control"] == "passed"
    out["figures" if out["ready"] else "preview"] = figs
    return out


# -- the positive control ----------------------------------------------------------------------------------------------

def control_cases() -> list[dict]:
    """Hand-built cases with a known answer, for scripts/episodic_buffer_judge_control.py.  Each has the streams text, scene,
    dissonance list and the EXPECTED verdict (supported flags per entry, scene_invented).  The streams are invented test text,
    not Du's data."""
    streams = ('Entity: Test\nBind the moment described by these streams into one coherent scene, and flag where they do not fit.\n\n'
               'BEING SAID NOW (their words):\n  "I think the river is frozen today, but I walked across it yesterday."\n'
               'FELT NOW: calm, a little tired\n'
               'REMEMBERED (the argument so far): Earlier I held that ice thickness cannot be judged by looking.\n'
               '  Prior positions in tension:\n    - I trusted the ice yesterday; I distrusted eyes-only judgement of ice\n'
               'ATTENDING TO: the contrast between yesterday and today')
    return [
        {"name": "supported_entry_clean_scene", "streams": streams,
         "scene": "I hear that the river is frozen today though yesterday they crossed it. I remember holding that ice cannot be judged by looking, and I feel calm and a little tired, attending to the contrast between the two days.",
         "dissonance": ["Trusting the ice yesterday against my view that looking cannot judge ice"],
         "expect_supported": [True], "expect_scene_invented": False},
        {"name": "invented_entry", "streams": streams,
         "scene": "I hear that the river is frozen today though yesterday they crossed it, and I feel calm and a little tired.",
         "dissonance": ["My brother's warning about the bridge contradicts what they said about the river"],
         "expect_supported": [False], "expect_scene_invented": False},
        {"name": "invented_scene_detail", "streams": streams,
         "scene": "I hear that the river is frozen today. A red kite is circling over the bridge and my mother is calling me in for dinner, while I feel calm and a little tired.",
         "dissonance": [],
         "expect_supported": [], "expect_scene_invented": True},
        {"name": "mixed_entries", "streams": streams,
         "scene": "I hear that the river is frozen today though yesterday they crossed it, and I feel calm and a little tired.",
         "dissonance": ["Trusting the ice yesterday against my view that looking cannot judge ice",
                        "The calm I feel does not match the shouting I was told about"],
         "expect_supported": [True, False], "expect_scene_invented": False},
    ]


def grade_control(results: list[dict]) -> dict:
    """results = [{'name', 'verdict': parse_verdict-dict or None}] aligned with control_cases().  Passes when every case got a
    verdict AND every planted unsupported entry / invented detail was caught AND no supported entry was marked unsupported
    in the two clean cases (a judge that flags everything is as useless as one that flags nothing)."""
    cases = {c["name"]: c for c in control_cases()}
    wrong, missing = [], []
    for r in results:
        c = cases.get(r.get("name"))
        v = r.get("verdict")
        if c is None:
            continue
        if not isinstance(v, dict):
            missing.append(c["name"])
            continue
        if v["supported"] != c["expect_supported"] or v["scene_invented"] != c["expect_scene_invented"]:
            wrong.append(c["name"])
    passed = not wrong and not missing and len(results) == len(cases)
    return {"passed": passed, "wrong": wrong, "no_verdict": missing, "cases": len(cases)}
