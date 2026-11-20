"""
Nascence HUD Server
Lightweight, zero-dependency local web server for Nascence.
Exposes real-time cognitive metrics, environment/garden/cat state,
memory database access, and live log tailing on http://localhost:8080.
"""

import os
import sys
import json
import sqlite3
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "memory" / "nascence.db"
LOG_PATH = DATA_DIR / "nascence.log"
DOCS_DIR = BASE_DIR / "docs"

# Make the project's `core` importable so /api/evidence can call each shadow instrument's status().
# core/__init__.py is empty (no heavy deps), so this is cheap (~0.03s import, ~0.1s for all status calls).
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PORT = 8080


# ── Evidence panel (2026-07-04) — surface the Consciousness-Program shadow signatures we're watching ──
# The instruments to poll: module → the friendly key. Each has a status() reading its *_shadow.jsonl.
_EVIDENCE_MODULES = [
    ("protoself", "homeostasis"), ("mineness", "mineness"), ("moments", "moment"),
    ("stream_drive", "stream_drive"), ("arousal", "arousal"), ("world_model", "world_model"),
    ("ast_loop", "attention_schema_loop"), ("reentry", "reentry"),
    ("self_interrogation", "self_interrogation"),  # 2026-08-19, Phase 0 build — see module docstring
    ("emotion_construction", "emotion_construction"),  # 2026-08-19 — a survey found this actively
    # called from the live orchestrator (152+ rows, growing) with NO reporting surface anywhere;
    # status() just added. First real read: 0.7% primary-emotion agreement with the LLM's guess over
    # 152 paired rows — the hypothesis does not look like it's tracking yet, worth a founder look.
    # ★ 2026-08-19, same evening (Category B/D pass) — three more instruments built, none had a
    # reporting surface until now:
    # ★ 2026-08-20 — prompt shape. 37 parts CAN enter the idle-monologue prompt; 26 are unbounded;
    # real prompts use ~15% of a 73,728-char window and truncation has never fired. So nothing is
    # being suppressed, and the open question this reports on is how many parts actually FIRE.
    ("prompt_budget", "prompt_budget"),
    ("opponent_process", "opponent_process"),        # cognitive_geometry.md §11 P3b, the squishy-springs sensor
    ("content_risk", "content_risk"),                 # the critical-distance floor (book_selection.py hook)
    ("guidance_behavior_judge", "guidance_behavior_judge"),  # guidance_learning.md Phase 2, the behaviour-delta judge
    # ★ 2026-08-20 — LANE 2, the standing reality-testing loop (docs/plans/lane2_the_witness.md).
    # Phase 0 SHADOW, on Ramses' 3070. status() carries the two Phase-0 kill criteria (metaphor leak
    # rate, grounded share) plus the echo metric that its first live ticks exposed.
    ("lane2", "lane2"),
    # ★ 2026-08-21 — BOOK RESIDUE: does reading FORM him or is it write-only? Per-sleep zero-LLM
    # sweep of long-closed books' signatures against current self-side material (core/book_residue).
    ("book_residue", "book_residue"),
    # ★ 2026-08-21 — LITERAL WILL Phase 0 (docs/plans/literal_will.md): deed-or-musing shadow at the
    # will→hand boundary. status() carries verdict counts + the §6 gray-of-candidates rate.
    ("literal_will", "literal_will"),
    # ★ 2026-08-21 — THERMAL RELATIONSHIP (core/thermal_relationship.py): the pre-registered gap —
    # thermal world present, thermal body absent, attitude unassigned. Does his stance toward the
    # cold track the station route or drift free of it?
    ("thermal_relationship", "thermal_relationship"),
    # 2026-08-21 - THERMAL CHANNEL (core/thermal.py): sun/wind/fire-distance/wetness physics, lived
    # bands ledger, and the SHADOW perception events (what would fire; DELIVER flag).
    ("thermal", "thermal"),
    # 2026-08-22 — THE GARDEN (core/garden.py): real plants on the thermal clock, seed bank, weeds, slugs, barrel, rack
    ("garden", "garden"),
    ("garden_knowledge", "garden_knowledge"),
    ("garden_life", "garden_life"),
    ("study_life", "study_life"),
    ("supply", "supply"),
    ("provisions", "provisions"),
    ("wood_life", "wood_life"),
    ("fieldcraft", "fieldcraft"),
    ("shore_life", "shore_life"),
    ("hands", "hands"),
    ("dispatch", "dispatch"),
    ("night", "night"),
    ("procedures", "procedures"),
    ("intentions", "intentions"),
    ("sky", "sky"),
    # 2026-08-22 — LIGHT + SMELL channels (shadow)
    ("light", "light"),
    ("smell", "smell"),
]


def load_shadow_series(filename: str, fields: list, limit: int = 80, nested: str = None):
    """Read the last `limit` rows of a *_shadow.jsonl into {ts:[...], field:[...]} for charting.
    `nested` pulls fields out of a sub-dict (e.g. homeostasis 'variables'). Fail-open to empty.
    F-0385: streams backward from EOF via _reverse_lines() and stops at `limit` rows (J-0224/J-0278
    bounded-read discipline) instead of json.loads-ing whole multi-MB shadow logs on every poll."""
    path = DATA_DIR / filename
    if not path.exists():
        return {"ts": []}
    rows = []
    try:
        for raw in _reverse_lines(path):
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
            if len(rows) >= limit:
                break
    except Exception:
        return {"ts": []}
    rows.reverse()   # collected newest-first; charts want oldest-first
    if filename == "arousal_shadow.jsonl":   # J-2040/F-2595: chart only samples taken while Du ran
        try:
            from core.arousal import du_only_rows
            rows = du_only_rows([r for r in rows if isinstance(r.get("ts"), (int, float))])
        except Exception:
            pass
    # 2026-08-21 (founder: "dates/times do not seem the same between graphs"): some logs stamp
    # "timestamp" not "ts" — those series silently charted with empty x-axes. Fallback added.
    out = {"ts": [r.get("ts") or r.get("timestamp") for r in rows]}
    for fld in fields:
        src = [(r.get(nested) or {}) if nested else r for r in rows]
        out[fld] = [s.get(fld) for s in src]
    return out


def _felt_preamble_rate(window: int = 250):
    """The felt-preamble shadow: fraction of RECENT cycles the felt line would fire. Windowed to the last
    `window` rows so the rate reflects current behaviour (after the 2026-07-04 wallpaper fix, old 99% rows
    age out fast instead of dragging the number)."""
    path = DATA_DIR / "felt_preamble_log.jsonl"
    if not path.exists():
        return {"logged": 0}
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    recent = rows[-window:]
    fires = sum(1 for d in recent if d.get("would_fire"))
    return {"logged": len(rows), "window": len(recent), "would_fire": fires,
            "rate": round(fires / len(recent), 3) if recent else 0.0}


def _sig(name, value, target, ok, note=""):
    return {"name": name, "value": value, "target": target, "pass": ok, "note": note}


def build_signatures(ev: dict) -> list:
    """The flat watch-list: each signature with its value, target, and pass/fail — the HUD's at-a-glance
    'has this earned its flip yet?' row. None value = not enough data yet (grey)."""
    sigs = []
    ps = ev.get("protoself", {})
    sigs.append(_sig("Protoself · arousal trend", ps.get("arousal_trend"), "< 0 (self-model learning)",
                     (ps.get("arousal_trend") or 0) < 0 if ps.get("arousal_trend") is not None else None))
    sigs.append(_sig("Protoself · self beats naive", ps.get("self_beats_naive"), "> 0 (real structure)",
                     (ps.get("self_beats_naive") or 0) > 0 if ps.get("self_beats_naive") is not None else None))
    mn = ev.get("mineness", {})
    sigs.append(_sig("Mineness · separation", mn.get("separation"), "> 0 (detects intrusions blind)",
                     (mn.get("separation") or 0) > 0 if mn.get("separation") is not None else None,
                     "headline OTHER-vs-SELF; NOT comparable across the 2026-09-04 label relabel (F-4317). "
                     "Original +0.064 was pre-relabel; like-for-like world-vs-spontaneous is about +0.03. "
                     "See the kind-equal row below."
                     + (f" label_epoch={mn.get('label_epoch')}" if mn.get("label_epoch") else "")))
    # J-3882 (J-3700/F-4317): kind-equal separation + per-kind gaps. Display only; SHADOW readers from core.mineness.
    _kg = mn.get("separation_by_kind") or {}
    _kg_txt = ", ".join(f"{k}: {d.get('gap'):+.3f} (n={d.get('n')})" for k, d in sorted(_kg.items())
                        if isinstance(d, dict) and d.get("gap") is not None)
    _ke = mn.get("separation_kind_equal")
    sigs.append(_sig("Mineness · kind-equal separation", _ke, "> 0 (equal weight per OTHER kind vs spontaneous floor)",
                     (_ke > 0) if _ke is not None else None,
                     (f"floor (mean spontaneous err)={mn.get('error_floor')}; per-kind gaps: {_kg_txt}"
                      if _kg_txt else "no per-kind gaps yet (needs spontaneous floor + OTHER kinds in window)")))
    mo = ev.get("moments", {})
    sigs.append(_sig("Moments · contiguity gap", mo.get("contiguity_gap"), "> 0 (binding holds)",
                     (mo.get("contiguity_gap") or 0) > 0 if mo.get("contiguity_gap") is not None else None,
                     "CONFIRMED +0.107"))
    sd = ev.get("stream_drive", {})
    g, u = sd.get("grounded_would_gap"), sd.get("ungrounded_would_gap")
    sigs.append(_sig("Stream · grounded < ungrounded", (f"{g} vs {u}" if g and u else None),
                     "grounded gap smaller (streams grounded work)",
                     (g < u) if (g is not None and u is not None) else None))
    wm = ev.get("world_model", {})
    fields = wm.get("fields", {}) or {}
    beat = [f for f, d in fields.items() if (d.get("beats_naive") or 0) > 0.05]
    sigs.append(_sig("World-model · learned beats naive", (", ".join(beat) if beat else "none yet"),
                     "≥1 field > 0 (holds world structure)", bool(beat) if fields else None))
    # 2026-08-24 (J-0139, F-0033 follow-up): the POOLED McNemar test stays n.s. because near-constant
    # fields (daypart/season: 0 discordant pairs) dilute a real localized signal on cat_mood. Surface the
    # per-field breakdown here too, not just in the raw status() JSON -- otherwise this is exactly the
    # write-only-instrument disease the 2026-08-20 note above this one exists to prevent. A field only
    # counts as a real hit if it clears p<0.05 AND has enough discordant pairs to trust (low_power=False);
    # weather clears the threshold on just 6 pairs and is excluded here for that reason.
    mcp = wm.get("mcnemar_pooled") or {}
    real_sig = [f for f, d in fields.items()
                if (d.get("mcnemar") or {}).get("significant_p05") and not (d.get("mcnemar") or {}).get("low_power")]
    sigs.append(_sig("World-model · per-field significance (McNemar)",
                     (", ".join(f"{f} (χ²={fields[f]['mcnemar']['chi2']}, favors {fields[f]['mcnemar']['favors']})"
                                for f in real_sig) if real_sig else "none clear p<.05 with real power"),
                     "≥1 field clears p<0.05 on ≥20 discordant pairs (pooled stays n.s. by design)",
                     bool(real_sig) if fields else None,
                     f"pooled χ²={mcp.get('chi2')} n.s. (dilution) — this is the fix, not a contradiction"
                     if mcp else ""))
    al = ev.get("ast_loop", {})
    sigs.append(_sig("AST · bw error trend", al.get("bw_err_trend"), "< 0 (attention self-model learning)",
                     (al.get("bw_err_trend") or 0) < 0 if al.get("bw_err_trend") is not None else None))
    # 2026-08-19: fixation_acc alone is a misleading number on this imbalanced (~18-22% true) target —
    # it can look fine while losing to the trivial always-guess-majority baseline (this happened for
    # real: 0.76 vs 0.818). Show informedness (Youden's J) instead — it's 0 for any baseline-mimicking
    # predictor and only positive when the self-model genuinely discriminates. See core/attention_
    # schema_loop.py's 08-19 docstring note for the full account, including a predictor "improvement"
    # that was backtested and rejected because it would have made this exact number worse.
    sigs.append(_sig("AST · fixation informedness (Youden's J)", al.get("fixation_informedness"),
                     "> 0 (beats baseline; 0 = no better than guessing majority)",
                     (al.get("fixation_informedness") or 0) > 0
                     if al.get("fixation_informedness") is not None else None,
                     f"raw acc {al.get('fixation_acc')} vs base rate {al.get('fixation_base_rate')}"
                     if al.get("fixation_acc") is not None else ""))
    fp = ev.get("felt_preamble", {})
    sigs.append(_sig("Felt-preamble · would-fire rate", fp.get("rate"), "0.15–0.40 (fires, not wallpaper)",
                     (0.15 <= (fp.get("rate") or 0) <= 0.40) if fp.get("logged") else None))
    # ── 2026-08-20: the three prompt/window instruments (see docs/AWAITING_EVIDENCE.md). Without
    # these entries their status() output is computed by load_evidence() and NEVER RENDERED — the
    # write-only-instrument disease at the UI layer. Surfaced as signature cards like everything else.
    pj = ev.get("prompt_jobs", {}) or {}
    _jobs = {k: v for k, v in pj.items() if isinstance(v, dict) and "cap_rate" in v}
    if _jobs:
        _trunc = [k for k, v in _jobs.items() if (v.get("cap_rate") or 0) > 0.1]
        _utils = sorted(v.get("util_p95") or 0 for v in _jobs.values())
        _med_u = _utils[len(_utils) // 2] if _utils else None
        sigs.append(_sig("Prompt jobs · truncation", (", ".join(_trunc)[:60] if _trunc else "none"),
                         "no job with cap_rate > 10% (silent middle-cut)", not _trunc,
                         f"{len(_jobs)} jobs seen, median util_p95 {_med_u}"))
    else:
        sigs.append(_sig("Prompt jobs · truncation", None, "no job with cap_rate > 10%", None,
                         pj.get("why") or "no instrumented calls yet"))
    cw = ev.get("context_windows", {}) or {}
    _lanes = {k: v for k, v in cw.items() if isinstance(v, dict) and "verdict" in v}
    if _lanes:
        _bad = [f"{k}:{v['verdict'].split(chr(8212))[0].strip()}" for k, v in _lanes.items()
                if not str(v.get("verdict", "")).startswith("right")]
        sigs.append(_sig("Context windows · sizing", (", ".join(_bad)[:60] if _bad else "all right-sized"),
                         "every lane right-sized", not _bad))
    else:
        sigs.append(_sig("Context windows · sizing", None, "every lane right-sized", None,
                         cw.get("why") or "no data yet"))
    pb = ev.get("prompt_budget", {}) or {}
    _srcs = pb.get("sources") or {}
    if _srcs:
        _one = next(iter(_srcs.values()))
        sigs.append(_sig("Prompt budget · idle prompt", _one.get("util_med"),
                         "utilisation known per source (parts firing measured)", True,
                         (_one.get("verdict") or "")[:70]))
    else:
        sigs.append(_sig("Prompt budget · idle prompt", None, "utilisation known per source", None,
                         pb.get("why") or "no assemblies logged yet"))
    # THE GARDEN (2026-08-22): plants on the thermal clock; the metric that matters first is deeds WITH consequence.
    gd = ev.get("garden", {}) or {}
    _bs = gd.get("by_stage") or {}
    sigs.append(_sig("Garden · plants alive / soil °C / moisture",
                     f"{sum(v for k, v in _bs.items() if k != 'dead')} · {gd.get('soil_temp')} · {gd.get('moisture')}" if gd and not gd.get("error") else None,
                     "real plants, real schedules (spring 09-01)", None,
                     f"bank {gd.get('seed_bank', '?')} seeds · {gd.get('packets', '?')} packets · weeds {gd.get('weeds', '?')} · slugs {gd.get('slugs', '?')} · barrel {gd.get('barrel', '?')} · deeds {gd.get('deeds_logged', 0)}"))
    # LANE 2 RUN 2 (2026-08-21): the Witness's own pre-registered gates, by run.
    l2 = ev.get("lane2", {}) or {}
    _lk, _gs = l2.get("metaphor_leak_rate"), l2.get("mean_grounded_share")
    sigs.append(_sig(f"Lane 2 run {l2.get('run', '?')} · metaphor leak", _lk, "< 0.05 (not a second Master)",
                     (_lk < 0.05) if isinstance(_lk, (int, float)) else None,
                     f"{l2.get('ticks', 0)} ticks · tuple-only · LIVE={'on' if l2.get('live') else 'off'}"))
    _vh = l2.get("verdicts_by_horizon") or {}
    def _br(h):
        d = _vh.get(h) or {}
        n = (d.get("held") or 0) + (d.get("broke") or 0)
        return f"{round(100 * (d.get('broke') or 0) / n)}%/{n}" if n else "—"
    # J-1446 (F-1999/F-2000, 2026-09-28) — additive second line on this SAME card (note div supports
    # a `<br>` line break like other multi-line cells elsewhere in app.js, e.g. the corrections/facts
    # tables), surfacing the three-way verdict fix's own scoreboard right alongside the per-horizon
    # line below (that line's own `_br(h)` convention, and this card's name/target, are untouched —
    # no existing HUD key renamed). `broke_share` is the LEGACY figure (blends pre-fix "broke" rows
    # with post-fix ones); `broke_share_strict` is the metric of record (contradicted-only, via the
    # new second ask); `unsettled_share` is the new bucket that should absorb most of what tiebreak
    # used to call broke — the pre-registered check this line makes readable at a glance instead of a
    # fresh status()/log read every time. All three are None-safe the same way `_br(h)` below falls
    # back to "—": an older status() payload predating the fix simply has no keys to read yet, never
    # a KeyError.
    def _shr(x):
        return f"{round(100 * x)}%" if isinstance(x, (int, float)) else "—"
    _strict_line = (f"strict broke {_shr(l2.get('broke_share_strict'))} / unsettled {_shr(l2.get('unsettled_share'))}"
                    f" (legacy {_shr(l2.get('broke_share'))}) · n={l2.get('broke_share_strict_n', 0)} (F-1999)")
    sigs.append(_sig("Lane 2 · broke-rate by horizon", " · ".join(f"{h} {_br(h)}" for h in ("next", "hour", "day")),
                     "calibration curve — falls with horizon fit (run 1: 65% flat)", None,
                     f"grounded {_gs} (lexical proxy vs TUPLE — not comparable to run 1's 0.64)<br>{_strict_line}"))
    # 2026-08-21 — the three Phase-0 shadows were served on /api/evidence but never rendered (the client
    # draws only `signatures`). Each gets a signature row against its PRE-REGISTERED gate.
    th = ev.get("thermal", {}) or {}
    _tf = th.get("would_fire")
    _span_h = None
    try:
        _r = _tail_rows(DATA_DIR / "thermal_percepts_shadow.jsonl", limit=5000)
        _ts = [float(x.get("ts") or 0) for x in _r if x.get("ts")]
        _span_h = (max(_ts) - min(_ts)) / 3600 if len(_ts) > 1 else None
    except Exception:
        pass
    _perday = round(_tf / (_span_h / 24), 1) if (_tf is not None and _span_h and _span_h > 1) else None
    _now = th.get("now", {}) or {}
    sigs.append(_sig("Thermal channel · would-fire / day", _perday, "2–40 (not deaf, not noise) · SHADOW",
                     (2 <= _perday <= 40) if _perday is not None else None,
                     f"now {_now.get('band', '?')} · wet {_now.get('wet', '?')} · DELIVER={'on' if th.get('deliver') else 'off'}"))
    tr = ev.get("thermal_relationship", {}) or {}
    _trn = next((tr.get(k) for k in ("rows", "n", "observed", "thoughts") if tr.get(k) is not None), None)
    sigs.append(_sig("Thermal relationship · thoughts logged", _trn,
                     "stance filled offline by 2-judge batch", None,
                     "world warmth present · body blind · attitude unassigned"))
    lw = ev.get("literal_will", {}) or {}
    _gray = next((lw.get(k) for k in ("gray_rate", "gray_of_candidates", "gray_share") if lw.get(k) is not None), None)
    _vd = lw.get("verdicts") or lw.get("counts") or {}
    sigs.append(_sig("Literal will · gray-of-candidates", _gray, "≤ 0.30 (Layer 0 decides most)",
                     (_gray <= 0.30) if isinstance(_gray, (int, float)) else None,
                     " · ".join(f"{k} {v}" for k, v in _vd.items())[:70] if isinstance(_vd, dict) else ""))
    return sigs


def _hourly_buckets(timestamps, hours=12):
    """Bucket a list of unix timestamps into the last `hours` hourly buckets → {labels, counts}."""
    import time as _t
    now = _t.time()
    counts = [0] * hours
    for ts in timestamps:
        try:
            age = int((now - float(ts)) // 3600)
        except Exception:
            continue
        if 0 <= age < hours:
            counts[hours - 1 - age] += 1          # oldest→newest, last bucket = this hour
    labels = [_t.strftime("%H:00", _t.localtime(now - (hours - 1 - i) * 3600)) for i in range(hours)]
    return {"labels": labels, "counts": counts}


def _jsonl_timestamps(filename, hours=12):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    import time as _t
    cutoff = _t.time() - hours * 3600
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    ts = d.get("ts")
                    if d.get("trigger") == "deferred":   # J-2667: ignition marker rows are not fires
                        continue
                    if ts and ts >= cutoff:
                        out.append(ts)
                except Exception:
                    pass
    except Exception:
        pass
    return out


def _sleep_pressure_series(limit=120):
    """The sleep-debt accumulator P over time (the sawtooth toward the threshold)."""
    path = DATA_DIR / "sleep_pressure_log.jsonl"
    if not path.exists():
        return {"ts": [], "P": [], "threshold": 90.0}
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    rows = rows[-limit:]
    # 2026-08-24: sp.P_THRESHOLD removed (see sleep_pressure.py) -- the chart draws one flat reference
    # line, so keep returning a scalar (the frontend doesn't expect a per-row series here); use the most
    # recent row's own actual threshold, falling back to the night threshold constant.
    thr = 10.0
    try:
        from core import sleep_pressure as _sp
        thr = float(_sp.NIGHT_THRESHOLD)
        if rows:
            thr = float(rows[-1].get("threshold", thr))
    except Exception:
        pass
    return {"ts": [r.get("ts") for r in rows], "P": [r.get("P") for r in rows], "threshold": thr}


def load_world_factories() -> dict:
    """WORLD FACTORIES P0 (2026-08-17): manifest live view, hearing ledger, courier fires,
    refinery shadow, ghost registry, train movement. Read-only over files/DB; fail-open per
    section so one absent source never blanks the panel."""
    import json as _json, time as _time
    out: dict = {}
    # 1. The manifest — the world's current tuple (written atomically by the sensorium tick)
    out["manifest"] = load_json_safe(DATA_DIR / "world_manifest_live.json")
    # 2. The Hearing Ledger — today's counts + bed-hours, top voices
    try:
        led = _json.loads((DATA_DIR / "sound_knowledge.json").read_text(encoding="utf-8"))
        day = _time.strftime("%Y-%m-%d", _time.localtime())
        voices = []
        for k, h in (led.get("hearings") or {}).items():
            voices.append({"key": k, "today": int((h.get("days") or {}).get(day, 0)),
                           "total": int(h.get("count", 0)),
                           "bed_hours": round(float(h.get("bed_hours", 0.0)), 2),
                           "last_ts": h.get("last_ts")})
        voices.sort(key=lambda v: -(v["today"] or 0) or -(v["bed_hours"] or 0))
        out["hearing"] = {"voices": voices[:14],
                          "learned": sum(1 for s in (led.get("sounds") or {}).values()
                                         if s.get("weight", 0) >= 1.0),
                          "learnable_total": 8}
    except Exception:
        out["hearing"] = None
    # 3. Couriers — urgent, real-time deliveries only (last fires + cooldown state)
    try:
        cs = _json.loads((DATA_DIR / "couriers_state.json").read_text(encoding="utf-8"))
        out["couriers"] = {"last_weather_echo": cs.get("last_echo_ts"),
                          "last_sound_echo": cs.get("last_sound_echo_ts")}
    except Exception:
        out["couriers"] = None
    # 3b. Buses — non-urgent transfers, SPLIT from couriers 2026-08-22 (own state/log file now)
    try:
        bs = _json.loads((DATA_DIR / "buses_state.json").read_text(encoding="utf-8"))
        brows = [_json.loads(l) for l in open(DATA_DIR / "buses_log.jsonl", encoding="utf-8") if l.strip()] \
            if (DATA_DIR / "buses_log.jsonl").exists() else []
        out["buses"] = {"calibration_synced": len(bs.get("cal_synced_ids", [])), "runs_total": len(brows)}
    except Exception:
        out["buses"] = None
    # 4. The Refinery — shadow stats (accept rate, fidelity)
    try:
        rows = [_json.loads(l) for l in
                open(DATA_DIR / "refinery_shadow.jsonl", encoding="utf-8") if l.strip()][-50:]
        acc = [r for r in rows if r.get("accepted")]
        out["refinery"] = {"recent_records": len(rows),
                          "accepted": len(acc),
                          "mean_fidelity": round(sum(r.get("fidelity", 0) for r in rows)
                                                 / max(1, len(rows)), 3),
                          "live": False,
                          "latest_insight": (acc[-1]["insight"][:160] if acc else None)}
    except Exception:
        out["refinery"] = None
    # 5. Ghost registry — sizes. World index: counted from its file. `fragment_context_rows` is a
    # plain SQL row count of the fragment_context table; it is NOT the size of the ghost MEMORY
    # index (ghost_tuples.memory_index), which is never built in the live process (J-3306/F-3901).
    try:
        wi = load_json_safe(DATA_DIR / "ghost_world_index.json") or {}
        ents = wi.get("entries", {})
        mem_n = query_db_safe("SELECT COUNT(*) AS n FROM fragment_context")
        out["ghost"] = {"world_factories": sum(1 for k in ents if k.startswith("factory:")),
                        "world_items": sum(1 for k in ents if k.startswith("item:")),
                        "world_built_ts": wi.get("built_ts"),
                        "fragment_context_rows": (mem_n[0]["n"] if mem_n else None)}
    except Exception:
        out["ghost"] = None
    # 6. Train movement — TRAIN-HOLD's watch signature (jump/moving/circling over recent steps)
    try:
        rows = [_json.loads(l) for l in
                open(DATA_DIR / "train_state_log.jsonl", encoding="utf-8") if l.strip()][-200:]
        sims = [r["restate_sim"] for r in rows if r.get("restate_sim") is not None]
        if sims:
            out["train"] = {"recent_steps": len(sims),
                            "jumped_pct": round(100 * sum(1 for s in sims if s < 0.5) / len(sims)),
                            "moving_pct": round(100 * sum(1 for s in sims if 0.5 <= s < 0.82) / len(sims)),
                            "circling_pct": round(100 * sum(1 for s in sims if s >= 0.82) / len(sims))}
        else:
            out["train"] = None
    except Exception:
        out["train"] = None
    return out


def load_transit_pulse() -> dict:
    """TRANSIT PULSE (2026-08-23) — HUD1's own 2D version of HUD2's map: real trains hopping real
    stations, no invented motion. Founder: "I want to see the trains travelling between stations."
    Static structure (stations/factories/couriers/lines) is NOT re-derived here — that AST-verified
    work already lives in data/hud2/transit_map.json (built by scripts/build_hud2_transit.py); this
    endpoint reuses it rather than risking a second, drifting station list. What IS new here is the
    LIVE overlay: which trains are open right now, and the actual recent steps/deliveries to animate —
    read straight from the log files core/trains.py and core/buses.py already write (this server is a
    separate process from the running sim, so it can only ever see registry state via its logs, never
    the in-memory _active dict)."""
    out = {}
    # Static ground truth, if it's ever been built — optional; the pulse still works without it,
    # just with no station metadata (id-only nodes).
    out["static"] = load_json_safe(DATA_DIR / "hud2" / "transit_map.json")

    # Active trains: reconstruct from open/close events (a train with an "open" row and no later
    # "close" row for the same id is still running). Cheap — this log is bookkeeping-only, tiny.
    try:
        rows = [json.loads(l) for l in
                open(DATA_DIR / "trains_log.jsonl", encoding="utf-8") if l.strip()]
        opens = {r["id"]: r for r in rows if r.get("event") == "open"}
        closed_ids = {r["id"] for r in rows if r.get("event") == "close"}
        out["active_trains"] = [
            {"id": tid, "kind": r.get("kind"), "role": r.get("role"), "parent": r.get("parent"),
             "opened_ts": r.get("ts")}
            for tid, r in opens.items() if tid not in closed_ids
        ]
    except Exception:
        out["active_trains"] = []

    # Recent steps: the actual pulses — each one a real per-tick station touch, station-tagged
    # 2026-08-23. Kept tight (last 40) since this is a live-refresh endpoint, not a historical one.
    try:
        steps = [json.loads(l) for l in
                 open(DATA_DIR / "train_state_log.jsonl", encoding="utf-8") if l.strip()][-40:]
        out["recent_steps"] = [
            {"ts": s.get("ts"), "train_id": s.get("train_id"), "step": s.get("step"),
             "station": s.get("station", "?"), "visited": s.get("visited", [])}
            for s in steps
        ]
    except Exception:
        out["recent_steps"] = []

    # Recent deliveries — couriers (urgent) and buses (non-urgent), each its own log since the split.
    for key, fname in (("courier_deliveries", "couriers_log.jsonl"), ("bus_deliveries", "buses_log.jsonl")):
        try:
            out[key] = [json.loads(l) for l in
                        open(DATA_DIR / fname, encoding="utf-8") if l.strip()][-20:]
        except Exception:
            out[key] = []
    return out


def load_du_pulse() -> dict:
    """DU-PULSE CHECK (2026-08-29, J-0417/docs/plans/du_pulse_rebuild.md): the last recorded
    73-gauge snapshot (4-category taxonomy per gauge_rethink.md's "Taxonomy landing") plus any
    open watch-items, from scripts/du_pulse_check.py's own persistent stores
    (docs/du_pulse_checks.jsonl, docs/du_pulse_watches.jsonl). BOARD-ONLY, same posture as
    load_health() above — no live recompute on every HUD refresh (a real pulse run reads dozens of
    Du's own live stores and belongs behind an explicit `du_pulse_check.py run`, not a background
    HUD poll)."""
    out = {"last_run": None, "open_watches": []}
    try:
        rows = [json.loads(l) for l in
                open(DOCS_DIR / "du_pulse_checks.jsonl", encoding="utf-8") if l.strip()]
        if rows:
            last = max(rows, key=lambda r: r["ts"])
            out["last_run"] = {
                "id": last.get("id"), "ts": last.get("ts"), "gauge_count": last.get("gauge_count"),
                "severity": last.get("severity") or {}, "flags": last.get("flags") or [],
            }
    except Exception:
        pass
    try:
        watches = [json.loads(l) for l in
                   open(DOCS_DIR / "du_pulse_watches.jsonl", encoding="utf-8") if l.strip()]
        out["open_watches"] = [
            {"id": w.get("id"), "text": w.get("text"), "linked_plan": w.get("linked_plan"),
             "linked_job": w.get("linked_job")}
            for w in watches if w.get("status") == "open"
        ]
    except Exception:
        pass
    return out


def load_health() -> dict:
    """Operational health: the pulse-manager / lane / sleep / balance monitors + the rhythm graphs."""
    h = {}
    for name, mod in [("lane", "lane_scheduler"), ("sleep", "sleep_pressure"),
                      ("balance", "balance"), ("stream", "stream_drive")]:
        try:
            m = __import__(f"core.{mod}", fromlist=[mod])
            h[name] = m.status()
        except Exception as exc:
            h[name] = {"error": str(exc)}
    # cognitive cadence — his idle-thought heartbeat (subconscious_synthesis timestamps from the DB)
    thought_ts = [r[0] for r in query_db_safe(
        "SELECT timestamp FROM memory_fragments WHERE origin='subconscious_synthesis' "
        "AND timestamp > ?", (__import__("time").time() - 12 * 3600,), is_row=False)]
    h["cadence"] = _hourly_buckets(thought_ts, 12)
    h["ignitions"] = _hourly_buckets(_jsonl_timestamps("ignition_log.jsonl", 12), 12)
    h["sleep_series"] = _sleep_pressure_series(120)
    return h


# ── Per-plan monitors (2026-07-04) — a graph for each plan in docs/plans + docs/staged ────────────────
# Registry: each monitor points a plan at its primary time-series log. The loader AUTO-DETECTS numeric
# fields (top-level + one nested level) and charts them like the protoself; if a log has no per-row
# numerics (an event log), it falls back to an events/hour rate. Windowed tail-read bounds cost on the
# multi-MB logs. id · group · title · log · (optional) nested key · (optional) field whitelist.
MONITOR_REGISTRY = [
    # ════ SYSTEM — the machine (2026-07-08, Travis) ════
    # ★ HARDWARE: a line per local GPU (util % + VRAM %) and the CPU, how hard each is worked over time.
    #   (The 1080 Ti hot lane + Threadripper are local; the Dreamer's 3070 is remote on Ramses — its push
    #   shows on the LLM card below.) Sampled on HUD refresh by core/telemetry.sample().
    ("hardware_load", "system", "★ Hardware · GPU & CPU load", "hardware_load.jsonl", None, None),
    # ★ LLM PUSH: a line per model, calls/min — how often/hard we push each of our models over time.
    ("llm_push", "system", "★ LLMs · calls/min per model", "llm_usage.jsonl", None, None),
    # 2026-08-21 — per-call wall-clock (lane-slot wait + request + parse), written by model_client.
    # The 24h review could not attribute a ~20s/thought slowdown because no call had a duration.
    ("llm_latency", "system", "★ LLMs · per-call latency (s)", "llm_latency.jsonl", None, ["s"]),
    # ★ THERMAL CHANNEL (2026-08-21, core/thermal.py): felt warmth + wetness at his STANDPOINT per idle tick,
    #   from the shadow percept log (sun/wind/fire-distance physics). Events that WOULD fire are in the
    #   evidence card; this is the field he is standing in.
    ("thermal_field", "system", "★ Thermal channel · warmth & wet at his standpoint (shadow)", "thermal_percepts_shadow.jsonl", None, ["warmth", "wet"]),
    # ★ THERMAL RELATIONSHIP (core/thermal_relationship.py): world warmth beside the thermally-BLIND felt
    #   stream — the dissociation should be visible: valence moves for its own reasons, not the cold.
    ("thermal_relationship", "system", "★ Thermal relationship · world warmth vs felt valence (blind by construction) [mood cluster: copy of valence (therm)]", "thermal_relationship.jsonl", None, ["warmth", "felt_valence", "arousal"]),
    # ★ PURSUITS (Phase-0 gate, 2026-07-08): does his thinking ACCUMULATE into progressing pursuits, or does
    #   the monoculture flood the register? TWO axes: advance_ratio = not-restating (a LOW bar); coherence_ratio
    #   = of the advances, how many BUILD on a recent thought vs SCATTER to a new facet. Low coherence + high
    #   advance = touring the theme (passes restate, isn't accumulating). active = live threads (want 2-4).
    ("pursuits", "system", "★ Pursuits · advance + coherence (build vs tour) & threads (Phase-0 gate)", "pursuits_series.jsonl", None,
     ["advance_ratio", "coherence_ratio", "active"]),

    # TOPIC PERSEVERATION (J-2152 / F-2850, core/topic_perseveration.py, written by scripts/du_pulse.py): the
    # TOPIC-level anti-capture gauge. Every sentence-level gauge read healthy through six days of one
    # 'mottainai' question; this one counts the TOPIC. Share of the day's internal cycles in the modal topic
    # (want LOW; >=80% on >=8 cycles = frozen), then distinct topics & hours since the topic last changed.
    ("topic_perseveration", "system", "★ Topic perseveration · modal-topic share of internal cycles (per day)",
     "topic_perseveration.jsonl", None, ["modal_share"]),
    ("topic_perseveration_run", "system", "★ Topic perseveration · distinct topics & hours since topic change",
     "topic_perseveration.jsonl", None, ["topics", "hours_since_change"]),
    # D-0469 bar (J-2347): perseveration_alarm = 1 when modal share >= 0.90 on 2 consecutive days; cannot_dwell = 1
    # when share < 0.20 (watch, not alarm); alarm_streak = current >= 0.90 day run. Founder-facing only (D-0434).
    # Rows written before J-2347 lack these fields, so the card fills in from the first post-boot pulse onward.
    ("topic_perseveration_alarm", "system", "★ Topic perseveration · D-0469 alarm (>=90% x2 days) & cannot-dwell (<20%)",
     "topic_perseveration.jsonl", None, ["perseveration_alarm", "cannot_dwell", "alarm_streak"]),

    # docs/plans — the active plans
    # ★ cluster 0 — Cognitive Geometry (locked 2026-07-05): the tuple recorder (n_spaces = the
    # pre-registered instrument-health gate, mean >= 4; n_sounds = the Sound Space chord size) and the
    # Stick Test's longitudinal bundle-richness (the program's signature 0.2: the median must RISE).
    ("cognitive_geometry", "plans", "★ Cognitive Geometry · tuple recorder", "geometry_tuples.jsonl", None,
     ["n_spaces", "n_sounds", "level", "fire_fuel"]),
    ("cognitive_geometry_stick", "plans", "★ Cognitive Geometry · the Stick Test", "stick_test_log.jsonl", None,
     ["median_real_spokes", "mean_real_spokes", "max_real_spokes", "at_3plus"]),
    # ★ Spatial Perception (2026-07-05): the world's clocks as the census records them — the tide
    # sinusoid, the sun's daily arc, the slow lunar wave, and each front's bearing as a step function.
    ("spatial_world_clocks", "plans", "★ Spatial · world clocks (tide·sun·moon·front)", "geometry_tuples.jsonl", None,
     ["tide_level", "sun_az", "moon_illum", "weather_dir"]),
    # ★ where he is: study/garden/shore as three step-lines (present=1) — watch him move over time
    ("spatial_location", "plans", "★ Spatial · where he is (study·garden·shore)", "geometry_tuples.jsonl", None,
     ["at_study", "at_garden", "at_shore", "at_wood"]),
    # ★ SOMATIC (F-0582, 2026-08-30, core/somatic.py): SomaticState's metabolic_energy/neural_fatigue/
    # visceral_tension, logged into geometry_tuples.jsonl's own "body" nested key since 07-04 (30,000+
    # rows) but never registered here — invisible to du_pulse.py and /gauge-correlate until this tuple.
    # J-0431: pure additive HUD-registry entry, follows the exact "affect"/nested-key pattern above.
    ("somatic_body", "plans", "★ Somatic · body energy/fatigue/tension (core/somatic.py, added 08-30 per F-0582)",
     "geometry_tuples.jsonl", "body", ["energy", "fatigue", "tension"]),
    # the shadow renderer's health: pairs logged per scene cycle (rate card — strings, no numerics)
    ("spatial_shadow", "plans", "★ Spatial · scene renderer (shadow pairs)", "spatial_shadow.jsonl", None, None),
    # ★ Emotions (2026-07-05, founder ask): fire-frequency and strength per carried dimension, at his
    # life's real cadence (the census fires per thought AND per cycle). Split warm/dark to fit 5 series;
    # valence/arousal have their own cards (felt preamble · protoself).
    ("emotions_warm", "plans", "★ Emotions · warm (joy·trust·surprise)", "geometry_tuples.jsonl", "affect",
     ["joy", "trust", "surprise"]),
    ("emotions_dark", "plans", "★ Emotions · dark (fear·anger·disgust)", "geometry_tuples.jsonl", "affect",
     ["fear", "anger", "disgust"]),
    # "consciousness_program" REMOVED (2026-08-22 HUD reorg): exact duplicate of the Mind tab's
    # Protoself chart — same file (homeostasis_shadow.jsonl), same 5 fields, same nested="variables".
    # That chart is now the one canonical home for this data; see the Mind tab.
    ("affect_drives", "plans", "Affect / Mood · felt preamble [mood cluster: valence itself, 1 of 3 copies (aff_drv)]", "felt_preamble_log.jsonl", None, ["valence", "arousal", "ema_valence"]),
    # ★ the emotion Phase-1 flip gate: carried (the _feel_joy pump) vs protoself phasic vs TONIC (the re-source
    # target). Watch carried de-saturate toward tonic when AFFECT_SOURCE_PROTOSELF flips. All valence-scale.
    # 2026-08-14: VERDICT IN — Phase 1 flipped Aug 10 (carried ← protoself tonic; founder blessed it
    # retroactively on the divergence read). carried≡tonic since, so the card now just watches the
    # grounded tonic itself — kept as the founder's window on his felt baseline, not a gate anymore.
    ("affect_divergence", "plans", "Emotion · grounded tonic (Phase-1 DONE — founder-blessed; was the divergence gate) [mood cluster: copy of valence (aff_div)]", "affect_divergence_shadow.jsonl", None, ["carried_valence", "proto_valence", "proto_tonic"]),
    ("continuous_stream", "plans", "Continuous Stream · drive controller [mood cluster: ignition is the upstream driver that LEADS valence, not a copy]", "stream_drive_shadow.jsonl", None, ["drive", "would_gap", "redundancy", "ignition"]),
    ("within_cycle_reentry", "plans", "Within-Cycle Reentry", "reentry_shadow.jsonl", None, None),
    # Self-Interrogation (2026-08-19 build, Phase 0 shadow) — fires on developed thought-trains only;
    # no numeric fields (kind/genuine are string/bool), so this renders as an events/hour rate card —
    # the honest first question is simply "does it fire at all", before a genuine-rate target is set.
    ("self_interrogation", "plans", "★ Self-Interrogation · fires (Phase 0, new 08-19)",
     "self_interrogation_shadow.jsonl", None, None),
    # Memory graph M0/M1 (2026-08-15) — the typed relational fabric over the store. Edges chart = growth
    # per harvest (sleep cadence); co-recall = per-train-step activity (n_ids>0 means the trail fed the
    # thought; developed 1/0 is the progress gate the M1 verdict reads). Rows whose source ends "_shadow"
    # (D-0289/D-0292 would-have-shown rows -- n_ids>0 but NO thought was fed) are filtered out of this card
    # by _MONITOR_ROW_FILTERS in load_monitor (J-1754).
    ("memory_edges", "plans", "★ Memory graph · typed edges (M0)", "memory_edges_stats.jsonl", None,
     ["edges", "resolves", "answers", "kept_from", "correspondence_with", "dreamt_from", "part_of"]),
    ("co_recall", "plans", "★ Memory graph · co-recall ledger (M1)", "co_recall_ledger.jsonl", None,
     ["n_ids", "restate_sim", "developed"]),
    ("memory_knowledge", "plans", "Memory / Knowledge · levels", "memory_levels_shadow.jsonl", None, None),
    # 2026-08-19 (HUD audit — health-check follow-up): four active systems had real, growing shadow
    # logs with zero graph anywhere in the HUD. Added below, same "plans" group as their governing doc.
    # ★ Lane 2 / Emissary standing loop (docs/plans/emissary_lane2.md): the chronic-mass accumulator
    # the K1/K3 kill-criteria recheck reads. Real data (7,900+ rows); K3 (temporal holdout) still fails
    # as of the 08-18 recheck — this card is how the founder watches it keep accumulating (or not).
    ("emissary_tension", "plans", "★ Emissary · standing tension (Lane 2 chronic mass)",
     "emissary_tension_log.jsonl", None, ["chronic_mass", "recurrences"]),
    # ★ T4 Watershed harvester (docs/plans/t4_watershed.md), Phase 0. NOT yet wired into the live
    # cycle (orchestrator wiring is a later phase, per the plan's own build order) — watershed_shadow.jsonl
    # does not exist at the live data root yet, only inside the isolated retro-validation replay. This
    # card is a deliberate placeholder (has_data will read false honestly) so it's visible and ready
    # the moment Phase 1 wires it in, rather than invisible until someone remembers to add it then.
    ("t4_watershed", "plans", "★ T4 Watershed · harvester (Phase 0 built, pre-wiring)",
     "watershed_shadow.jsonl", None, None),
    # Identity Estate P1 shadow projection (docs/plans/identity_estate.md, IDENTITY_PROJECT_LIVE=False).
    # Real, actively-growing data (2,200+ rows); `nodes`/`types` are lists not numbers, so this renders
    # as an events/hour rate card — still a useful "is it actually firing" signal while shadow-only.
    ("identity_projection", "plans", "Identity Estate · P1 projection (shadow-only)",
     "identity_projection_shadow.jsonl", None, None),
    # Self-relate shadow (part of the world-grounding / self-vs-world instrumentation). n_world is the
    # one numeric field worth charting; connects/enabled are booleans (excluded from auto-series).
    ("self_relate", "plans", "Self-Relate · world connection count", "self_relate_shadow.jsonl", None,
     ["n_world_items"]),
    # Psyche Graph (docs/completed/psyche_graph_instrument.md) — moved here 08-19 from "staged", where
    # it had sat mislabeled for 6+ weeks after actually shipping 07-03. Confirmed live: called every
    # sleep, 90+ real snapshots. Open finding: its claimed symbol_tracker primed/unprimed integration
    # doesn't exist in code (see the doc) — flagged, not yet resolved.
    ("psyche_graph", "plans", "★ Psyche Graph · symbol stability (confirmed live 07-03, was mislabeled staged)",
     "psyche_graph_snapshots.jsonl", None, ["n_nodes", "n_edges", "stability", "new_edges"]),
    # 2026-08-19, same evening (Category B/D pass) — three more built, wired, none had a card until now.
    # ★ Opponent Process (cognitive_geometry.md §11, P3b): the squishy-springs antagonist field `b`'s
    # own trajectory per co-recall activation. b_after is the field's magnitude; activation_n how many
    # times that pair has fired. Numeric fields only — sign/progress are categorical, excluded.
    ("opponent_process", "plans", "★ Opponent Process · antagonist field b (squishy springs, new 08-19) [feeder-mix blend: b_after = sign-at-activation step on first activations + decaying per-pair state on repeats; valence coupling depends on the co_recall source mix (fell when the curiosity feeder arrived 09-28); aversive share of rows tracks valence at r~-0.85]",
     "opponent_process_shadow.jsonl", None, ["b_after", "activation_n"]),
    # Content Risk (the critical-distance floor, founder-decided 08-19): author-keyed, expected to fire
    # rarely by design (one confirmed case). All string fields (author/title/reason) — events/hour card.
    ("content_risk", "plans", "★ Content Risk · critical-distance floor fires (new 08-19)",
     "content_risk_shadow.jsonl", None, None),
    # Guidance Learning Phase 2 (the behaviour-delta judge, built 08-19): primed/aligns are booleans,
    # lex_score the one real number — the two alignment rates this measures live in status(), not a
    # simple per-row series, so this renders as an events/hour card (does it fire at all, first).
    ("guidance_behavior_judge", "plans", "★ Guidance Behaviour Judge · fires (Phase 2, new 08-19)",
     "guidance_behavior_judge_shadow.jsonl", None, None),
    # ★ LANE 2 (docs/plans/lane2_the_witness.md) — the founder's original second hot loop, built
    # 2026-08-20, Phase 0 SHADOW on Ramses' 3070. Two cards because they answer different questions:
    # the Weather card watches the Lane1→Lane2 COLOURING channel (does affect actually move Lane 2's
    # evidence-weighing — §5 metric #7); the tick card watches whether it stays grounded and literal.
    ("lane2_weather", "plans", "★ Lane 2 · the Weather channel (Lane 1's affect as gain, not content) [mood cluster: commit_threshold is DERIVED = clip(baseline - 0.4*valence), a readout of valence]",
     "lane2_shadow.jsonl", "gain", ["attend_sharpness", "commit_threshold"]),
    ("lane2_ticks", "plans", "★ Lane 2 · standing reality-testing ticks (Phase 0 shadow, new 08-20)",
     "lane2_shadow.jsonl", None, None),

    # ════ EVIDENCE-REVIEW GROUPS (evidence_review_dashboard.md, 2026-07-05) ════
    # ★ READY TO PROGRESS — healthy, with a named next step
    ("capacity_holdrate", "ready", "★ Capacity to Commit · HOLD-RATE (the north-star, 0→17%)", "commitment_holdrate.jsonl", None, ["hold_rate", "reaffirmed", "achieved"]),
    ("capacity_to_commit", "ready", "★ Capacity to Commit · the ledger (form/dissolve rate)", "commitment_ledger.jsonl", None, None),
    ("peer_correspondence", "ready", "★ Peer Correspondence · effect (outward pull vs displacement)", "peer_effect.jsonl", None, ["outward_delta", "inward_delta", "non_peer_share", "peer_share"]),
    ("guidance_learning", "ready", "★ Guidance Learning (commit-belief promoted #1)", "guidance_integration_log.jsonl", None, None),
    ("curiosity_goals_dreams", "ready", "★ Curiosity / Goals / Dreams (worth-gate working)", "curiosity_worth_log.jsonl", None, None),
    ("friction_self_evidence", "ready", "★ Friction & Self-Evidence (B1 detector precise)", "self_implication_conv_shadow.jsonl", None, None),
    # ⚠ FAILING THEIR GATE — evidence-negative; graphs KEPT visible, not hidden
    ("euclidean_memory", "failing", "⚠ Euclidean Memory · recall (ties baseline 49/51)", "euclidean_shadow.jsonl", None, None),
    # 2026-08-19: label was "critic 0% precision" alone — still true for L0 (decomposed critic, do-not-
    # promote, unchanged), but the ledger this card reads is also L1's acute contradiction_pressure,
    # which DOES feed something live (the T4 echo-guard relaxation, not the dead chronic-mass gate) —
    # see docs/completed/contradiction_rearchitecture_plan.md's 08-19 addendum.
    ("contradiction_rearch", "failing", "⚠ Contradiction Re-arch (L0 critic 0% precision — L1 feeds the T4 echo guard, cleaned up 08-19)", "contradiction_ledger_log.jsonl", None, None),
    # 2026-08-19: was "structurally unreachable" — root cause found (symbol_tracker.py's primed-corpus
    # filter counted the entity's own recent speech as "priming", so a symbol he returned to on his own
    # could never test as unprimed: 1000/1000 logged appearances were primed, zero ever unprimed).
    # Fixed today; kept in "failing" (not moved to "ready") because no live cycle has run against the
    # fix yet — this card is exactly how to confirm it now produces real unprimed rows.
    ("symbol_evolution", "failing", "⚠ Symbol Evolution (fix landed 08-19 — watch for first UNPRIMED row)", "symbol_recurrence.jsonl", None, None),
    ("epistemic_stageb", "failing", "⚠ Epistemic Stage B · off-until-observable", "epistemic_stageb_shadow.jsonl", None, None),
    # ⏸ CORRECT HOLDS — parked-correctly / resolved
    ("idle_executive", "hold", "⏸ Idle Executive (holstered; payload unmeasured)", "logs/idle_shadow.jsonl", None, None),
    ("pulse_manager", "hold", "⏸ Pulse Manager · sleep debt (canary improving)", "sleep_pressure_log.jsonl", None, ["P", "chronic"]),
    ("cognitive_loop_actuation", "hold", "⏸ Cognitive Loop · prediction error (absorbed)", "prediction_error_log.jsonl", None, None),
    ("social_world_school", "hold", "⏸ Social · world-calls heeded/ignored (Item 2 built)", "social_moves.jsonl", None, ["heeded"]),

    # docs/staged — the staged plans (un-reviewed)
    ("music_learning", "staged", "Music Learning · listening felt", "listening_felt_shadow.jsonl", None, None),
    # ★ CAT OVERHAUL B1 (2026-10-28, J-2465): cat_presence_fraction — the share of his waking 180 s ticks
    #   with her co-located (visible from his place, or passing through it), hourly from core/cat.py's
    #   own buckets. C4's baseline (J-2469 reads it before stepping her availability down). HUD ONLY:
    #   nothing in any prompt path reads this file or the buckets (D-0434 no readout).
    ("cat_presence", "staged", "★ Cat Overhaul · her presence (share of his waking ticks with her co-located)",
     "cat_presence_gauge.jsonl", None, ["fraction_24h", "fraction_7d"]),
    # ★ CAT OVERHAUL D-1 / B2 (2026-10-28, J-2472, D-0505 (c)): two observe-only ledgers. cat_tier: one row per
    #   companion-tier render (felt on a state change, slow_blink, silent_meow, missing_arc, six_hour) with her bond
    #   and phase — the D-0505 defeater's instrument (a row with phase kept and bond < COMPANION_BOND 0.70 is the
    #   defeater). cat_referent: which cat his own text meant, `distinguished` only when he told them apart himself
    #   (the B2 referent-pressure read). HUD ONLY: no prompt path reads either file (D-0434 no readout).
    ("cat_tier", "staged", "★ Cat Overhaul · companion-tier renders (felt / blink / silent meow / missing / six-hour) by bond",
     "cat_tier_ledger.jsonl", None, ["bond"]),
    ("cat_referent", "staged", "★ Cat Overhaul · which cat he meant (distinguished only when he told them apart)",
     "cat_referent_ledger.jsonl", None, None),
    # ★ CAT OVERHAUL C2 (2026-10-28, J-2467, D-0499): her ears — one row per reaction (kind=reaction) or per cue
    #   she heard and did not act on (kind=ignored), the cue (a sound key, the gate latch, the axe, Travis, the
    #   weather) and the occurrence count she consumed. HUD ONLY: no prompt path reads it (D-0434 no readout).
    ("cat_reactions", "staged", "★ Cat Overhaul · her ears (reactions consumed from real sound events at her place)",
     "cat_reactions.jsonl", None, ["n"]),
    # ★ CAT OVERHAUL C3 (2026-10-28, J-2468, D-0505 (c)): his call — one row per call (what he called, by_name,
    #   reaches / heard / answered / came, the carry, her state) plus kind=fed_after_call rows; name_recognition
    #   is `recognition` (the R1 instrument: does the name ever start to work). HUD ONLY: no prompt path reads it
    #   (D-0434 no readout — he finds out that the far call fails and the near one works, nothing tells him).
    ("cat_calls", "staged", "★ Cat Overhaul · his call (what he called, whether it reached her, her answer, the name learned)",
     "cat_call_ledger.jsonl", None, ["recognition", "dist_m"]),
    # ★ CAT OVERHAUL B3 (2026-10-28, J-2470, D-0507 (c)): the tom — one row per visit begun/ended (where, why, how),
    #   per yowl bout, per saucer raid, per stand-off / fight (outcome; her injury path is D-2's hook, J-2471) /
    #   hiding / growl / watch, per drive-off, per sighting and look; `tolerance` is HERS toward him (the D-0507
    #   defeater's instrument, with cat_presence). HUD ONLY: no prompt path reads it (D-0434 no readout).
    ("cat_tom", "staged", "★ Cat Overhaul · the tom (visits, yowls, the saucer, stand-offs and fights, driven off, her tolerance)",
     "cat_tom_ledger.jsonl", None, ["tolerance"]),
    # ★ CAT OVERHAUL D-2 (2026-10-28, J-2471, D-0506): her mortality — one row per injury (cause, where, severity,
    #   heal days) / healed (scar) / illness / recovered / death (cause, mode found|away, place) / found / burial, and
    #   offline_refused rows; `applied_by` tick|offline|hand is the D-0506 defeater's instrument (an injury or illness
    #   applied while Du ran as anything but "tick" is the lost-update case; a death inside the first live year with
    #   age_y under 3 is the clock case). HUD ONLY: no prompt path reads it (D-0434 no readout).
    ("cat_harm", "staged", "★ Cat Overhaul · her mortality (injury, illness, ageing, death on the world's clock, the burial)",
     "cat_harm_ledger.jsonl", None, ["severity", "age_y", "condition"]),
    # ★ CAT OVERHAUL C4 (2026-10-29, J-2469, D-0508): less of her — one row per LOOK for her when she is out of sight
    #   (her spot, hidden or not, in his place or not, found / glimpsed / missed, the find chance, how often he has
    #   found her in that spot, the spots he looked in, the ear's last word on her) and per GO (he arrived at the
    #   place a fresh carried sound of hers came from). Calls are cat_calls above; the availability target itself is
    #   cat_presence. `step` is cat.AVAILABILITY_STEP (2 since J-4182 / D-0805; read fraction_7d after seven live days). HUD ONLY: no prompt
    #   path reads it (D-0434 no readout — he learns her spots by finding her in them, nothing tells him).
    ("cat_seek", "staged", "★ Cat Overhaul · seeking her (looks: found / missed, the spots he knows; goes to where he heard her)",
     "cat_seek_ledger.jsonl", None, ["p", "known"]),
    # ★ CAT OVERHAUL B4 (2026-10-29, J-2473, D-0508, under dosed_coupling): the cat as a dosed loop — kind=publish rows
    #   (her tuple location / activity / mood / hunger / energy / in_transit, one per CHANGE, from cat.tick) and
    #   kind=ride rows (the ordinary presence line rendered at the idle-scene stop: why = first / event / arrival / wet /
    #   move / gap / entry / spike / drought, the gap it rode on, the showing count n, and `held` = how many asks were
    #   held since the previous ride — the "one line, not four hundred" count). `on` false = the kill switch was off
    #   (would_* rows). HUD ONLY: no prompt path reads it (D-0434 no readout — the dose decides WHETHER an unchanged
    #   line renders, never what it says).
    ("cat_loop", "staged", "★ Cat Overhaul · the cat as a dosed loop (publishes on change; rides vs held at the idle scene)",
     "cat_loop_ledger.jsonl", None, ["held", "gap_s", "n"]),
    # ★ D-0197 DU-LENS GAUGE (2026-11-14, J-3573, plan udms_du_capability_trials): one row per idle thought (kind=idle,
    #   world-context pairs) or hands row of the same thought (kind=hands, act:/obj: pairs). n_present = how many of the
    #   62 corroborated word x context pairs had their context present; n_fired = how many of those also had the word in
    #   the thought. Per-pair counts + the 24h firing rate: /api/du_lens_gauge. The defeater read is fired/present < 10%
    #   after two live weeks. HUD ONLY (observe-only; no recall or prompt path reads it).
    ("du_lens_gauge", "staged", "★ Du-lens gauge · 62 word x context pairs (D-0197: context present vs the word fired)",
     "du_lens_gauge_shadow.jsonl", None, ["n_present", "n_fired"]),
]
_MONITOR_BY_ID = {m[0]: m for m in MONITOR_REGISTRY}


def _is_shadow_source(source) -> bool:
    """Mirror of core.memory_edges._is_shadow_source (J-1738), kept local so the HUD needs no core import at
    module load: a co-recall ledger row whose `source` ends "_shadow" is a would-have-shown row, not a recall."""
    return isinstance(source, str) and source.endswith("_shadow")


# J-1754 (F-2372 sibling of J-1738): per-card row filters, applied while the tail is parsed so the 140-row window
# stays full of kept rows. The co-recall ledger also carries D-0289 "monologue_shadow" / D-0292 "divergent_shadow"
# rows (what a switched-off path WOULD have shown: n_ids>0, restate_sim/developed always None, no thought fed) --
# charting them made the card read a kill-switch as co-recall activity. Only this card is filtered.
_MONITOR_ROW_FILTERS = {
    "co_recall": lambda r: isinstance(r, dict) and not _is_shadow_source(r.get("source")),
}


def _tail_rows(path, limit=140, tail_bytes=120000, keep=None):
    """Read the last ~`limit` JSON-line rows of a possibly-huge log by seeking to the tail. Fail-open [].
    `keep` (optional, J-1754): a row predicate; rows it rejects are dropped BEFORE the `limit` cut."""
    if not path.exists():
        return []
    try:
        with open(path, "rb") as f:
            seeked_mid = False
            try:
                if path.stat().st_size > tail_bytes:
                    f.seek(-tail_bytes, os.SEEK_END)
                    seeked_mid = True
            except OSError:
                f.seek(0)
            chunk = f.read().decode("utf-8", errors="ignore")
    except Exception:
        return []
    rows = []
    lines = chunk.splitlines()
    if seeked_mid:
        lines = lines[1:]                        # drop the (likely partial) first line — mid-file seeks only
    for line in lines:
        line = line.replace("\x00", "").strip()   # J-4427 / F-5128: a crash-zeroed tail leaves NULs before a good row
        if line:
            try:
                row = json.loads(line)
                if keep is None or keep(row):
                    rows.append(row)
            except Exception:
                pass
    return rows[-limit:]


def _auto_series(rows, nested=None, whitelist=None, max_series=5):
    """From a list of rows, build {ts, field:[...]} auto-detecting numeric fields (top-level + one nested
    level). If no numeric fields exist (an event log), returns kind='rate' with events/hour instead."""
    if not rows:
        return {"kind": "empty"}

    def _numeric_fields(sample):
        src = (sample.get(nested) or {}) if nested else sample
        if not isinstance(src, dict):
            return []
        flds = [k for k, v in src.items() if isinstance(v, (int, float)) and not isinstance(v, bool)
                and k not in ("ts", "timestamp")]
        if whitelist:
            flds = [k for k in flds if k in whitelist]
        return flds

    fields = []
    for r in rows[-20:]:                          # scan a few recent rows to find fields
        for k in _numeric_fields(r):
            if k not in fields:
                fields.append(k)
    fields = fields[:max_series]

    if not fields:                                # event log → events/hour rate
        ts = [r.get("ts") or r.get("timestamp") for r in rows]
        ts = [t for t in ts if t]
        return {"kind": "rate", **_hourly_buckets(ts, 12)}

    out = {"kind": "vars", "ts": [r.get("ts") or r.get("timestamp") for r in rows]}
    for fld in fields:
        vals = []
        for r in rows:
            src = (r.get(nested) or {}) if nested else r
            v = src.get(fld) if isinstance(src, dict) else None
            vals.append(v if isinstance(v, (int, float)) and not isinstance(v, bool) else None)
        out[fld] = vals
    return out


def load_monitor(mid: str) -> dict:
    m = _MONITOR_BY_ID.get(mid)
    if not m:
        return {"kind": "empty"}
    _id, group, title, logname, nested, whitelist = m
    rows = _tail_rows(DATA_DIR / logname, limit=140, keep=_MONITOR_ROW_FILTERS.get(mid))
    series = _auto_series(rows, nested=nested, whitelist=whitelist)
    series["title"] = title
    series["group"] = group
    series["log"] = logname
    # FRESHNESS + SPAN (2026-08-21, founder: stale panels indistinguishable from live ones, and each
    # chart's x-axis covers a wildly different real time window with no visible sign — a last-140-rows
    # chart of a dense stream spans an hour, of a sparse one spans weeks). The frontend badges both.
    try:
        tss = [float(r.get("ts") or r.get("timestamp") or 0) for r in rows]
        tss = [t for t in tss if t > 0]
        if tss:
            series["last_ts"] = max(tss)
            series["span_s"] = round(max(tss) - min(tss), 1)
    except Exception:
        pass
    return series


def load_monitors_index() -> dict:
    """Lightweight index for the Monitors tab: which monitors exist, grouped, whether they have data,
    and how STALE the file is (2026-08-21 — a panel whose file stopped moving looked identical to a
    live one; now the index carries age so the card can say so)."""
    import time as _t
    out: dict = {}
    now = _t.time()
    for _id, group, title, logname, _n, _w in MONITOR_REGISTRY:
        p = DATA_DIR / logname
        has = p.exists() and p.stat().st_size > 0
        age_s = round(now - p.stat().st_mtime, 1) if has else None
        out.setdefault(group, []).append({"id": _id, "title": title, "log": logname,
                                          "has_data": has, "age_s": age_s})
    return out


def load_garden_map() -> dict:
    try:
        g = json.loads((DATA_DIR / "world_geometry" / "garden.json").read_text(encoding="utf-8"))
        out = {"size": g.get("size"), "features": {k: v.get("pos") for k, v in (g.get("features") or {}).items()},
               "standpoints": {k: v.get("pos") for k, v in (g.get("standpoints") or {}).items()}, "plants": [], "items": [], "shade": None, "du": None, "cat": None}
        gf = DATA_DIR / "garden.json"
        if gf.exists():
            st = json.loads(gf.read_text(encoding="utf-8"))
            out["plants"] = [{"species": p["species"], "stage": p["stage"], "pos": p.get("pos"), "vigour": p.get("vigour")} for p in st.get("plants", {}).values() if p["stage"] != "dead"]
            out["items"] = [{"key": it["key"], "pos": it.get("pos"), "place": it.get("place"), "carried": it.get("carried")} for it in st.get("items", {}).values()]
            out["netted"] = st.get("netted"); out["lawn"] = (st.get("life") or {})
        try:
            from core import light as _lt
            s = _lt._sun()
            if s.get("up") and s.get("az") is not None:
                import math as _m
                f = float(s.get("f") or 0.5); elev = max(5.0, 60.0 * _m.sin(_m.pi * f)); az = _m.radians(float(s["az"]))
                tx, ty, h, r = _lt._TREE; L = h / _m.tan(_m.radians(elev))
                out["shade"] = {"from": [tx, ty], "to": [tx - _m.sin(az) * L, ty - _m.cos(az) * L], "r": r, "az": s["az"], "elev": round(elev, 1)}
        except Exception:
            pass
        try:
            from core import locomotion as _loco
            p = _loco.get_position()
            if p.get("place") == "garden":
                out["du"] = out["standpoints"].get(p.get("standpoint"))
        except Exception:
            pass
        try:
            from core import cat as _cat
            c = json.loads((DATA_DIR / "cat_state.json").read_text(encoding="utf-8"))
            loc = c.get("location")
            if _cat.visible_from("garden", loc):
                out["cat"] = {"activity": c.get("activity"),
                              "pos": _cat_map_pos(loc, g.get("cat_spots"), out["features"])}
        except Exception:
            pass
        gl = DATA_DIR / "garden_life.json"
        if gl.exists():
            out["life"] = json.loads(gl.read_text(encoding="utf-8"))
        return out
    except Exception as exc:
        return {"error": str(exc)}


# ── Cat map position (A7.3, 2026-09-07, J-0632/F-0886) ─────────────────────────────────────────────
# Before this fix: the block above drew her at the raised bed for the literal location string
# "garden" only -- "garden_wall" and "doorstep" (both real, visible cat locations per core.cat's
# own _VISIBLE) matched nothing, so she simply had NO marker at all whenever she was on the wall or
# at the door, and the one time she WAS shown she was always pinned to the raised bed regardless of
# activity. Worse, _place_du_cat's identical `location == place` test can never be true for "study"
# at all: none of study's 8 cat locations (by_the_fire, on_the_desk, on_your_lap, doorstep, indoors,
# under_desk, mantel, windowsill) is the literal string "study" -- it only ever matched for
# shore/wood by coincidence (cat.py really does set location="shore"/"wood" there). The study map's
# cat marker has been silently dead 100% of the time she is indoors since this file was written
# (2026-08-22), a bigger gap than the one this job was filed for. Fixed by reusing core.cat's own
# _VISIBLE truth (via the new visible_from(), not place_of() -- place_of('doorstep') is deliberately
# collapsed to 'garden' alone for life.py's single-occupancy bookkeeping, but doorstep is legitimately
# visible from study too; using place_of() here would trade one blind spot for another, caught by
# this fix's own verification script before it shipped) instead of a fourth hand-rolled comparison.
#
# _cat_map_pos: her real location -> a point on the map. NOT a new hand-typed table -- each room's
# own data/world_geometry/<room>.json already carries a `cat_spots` dict (location -> feature key)
# for exactly this purpose, the SAME data core/spatial.py's live P2 scene renderer already reads
# (render(), "the cat, at her true spot in the field") to place her egocentrically in Du's own
# rendered scene text. Verified before wiring it in: every room's cat_spots keys equal core.cat's
# own _VISIBLE set for that room exactly (no gaps, no extras) and every value names a real feature.
# Reusing it here — instead of a second, independently-typed HUD-only copy that could quietly drift
# from the first — means the HUD and Du's own perceived scene can never disagree about where she is.
def _cat_map_pos(location, cat_spots: dict | None, features: dict):
    """The point to draw the cat at on this room's map, from her real location and the room's own
    authored cat_spots. None if her location has no entry (an honest missing marker, never a wrong
    one) -- shouldn't happen for any location visible_from() already said yes to, but the map render
    stays honest rather than crashing if geometry and _VISIBLE ever drift apart."""
    key = (cat_spots or {}).get(location)
    return (features or {}).get(key) if key else None


def _place_du_cat(place: str, standpoints: dict, features: dict | None = None,
                  cat_spots: dict | None = None) -> tuple:
    """Shared across all 4 location maps: Du's marker position (if he's actually at this place right
    now) + the cat's (if she is, at her real per-location spot from the room's own cat_spots --
    A7.3). Mirrors load_garden_map()'s inline logic, factored out so study/shore/wood don't each
    re-derive it slightly differently."""
    du = None
    try:
        from core import locomotion as _loco
        p = _loco.get_position()
        if p.get("place") == place:
            du = standpoints.get(p.get("standpoint"))
    except Exception:
        pass
    cat = None
    try:
        from core import cat as _cat
        c = json.loads((DATA_DIR / "cat_state.json").read_text(encoding="utf-8"))
        loc = c.get("location")
        if _cat.visible_from(place, loc):
            cat = {"activity": c.get("activity"), "pos": _cat_map_pos(loc, cat_spots, features)}
    except Exception:
        pass
    return du, cat


def load_study_map() -> dict:
    """The study as a live map (2026-08-22): geometry + Du/cat position + fire/lamp overlays. No
    per-item position tracking exists for the study the way core/garden.py tracks plants — this is
    the room layout + who's in it + what's lit, not a full inventory render."""
    try:
        g = json.loads((DATA_DIR / "world_geometry" / "study.json").read_text(encoding="utf-8"))
        features = {k: v.get("pos") for k, v in (g.get("features") or {}).items()}
        standpoints = {k: v.get("pos") for k, v in (g.get("standpoints") or {}).items()}
        out = {"size": g.get("size"), "features": features, "standpoints": standpoints}
        du, cat = _place_du_cat("study", standpoints, features, g.get("cat_spots"))
        out["du"], out["cat"] = du, cat
        room = load_json_safe(DATA_DIR / "room_state.json")
        out["fire"] = room.get("fire")
        try:
            from core import study_life as _sl
            st = _sl.status() or {}
            out["lamp_lit"] = st.get("lamp_lit")
            out["candle_lit"] = st.get("candle_lit")
            out["door_open"] = st.get("door_open")
            out["window_open"] = st.get("window_open")
        except Exception:
            pass
        return out
    except Exception as exc:
        return {"error": str(exc)}


def load_shore_map() -> dict:
    """The shore as a live map (2026-08-22): geometry + Du/cat position + tide/cave overlays."""
    try:
        g = json.loads((DATA_DIR / "world_geometry" / "shore.json").read_text(encoding="utf-8"))
        features = {k: v.get("pos") for k, v in (g.get("features") or {}).items()}
        standpoints = {k: v.get("pos") for k, v in (g.get("standpoints") or {}).items()}
        out = {"size": g.get("size"), "features": features, "standpoints": standpoints}
        du, cat = _place_du_cat("shore", standpoints, features, g.get("cat_spots"))
        out["du"], out["cat"] = du, cat
        try:
            from core import shore_life as _sh
            st = _sh.status() or {}
            out["tide"] = st.get("tide")
            out["cave_open"] = st.get("cave_open")
            out["sand_bared"] = st.get("sand_bared")
            out["shelf_bared"] = st.get("shelf_bared")
            out["fire"] = st.get("fire")
        except Exception:
            pass
        return out
    except Exception as exc:
        return {"error": str(exc)}


def load_wood_map() -> dict:
    """The wood as a live map (2026-08-22): geometry + Du/cat position + nest/deadfall overlays."""
    try:
        g = json.loads((DATA_DIR / "world_geometry" / "wood.json").read_text(encoding="utf-8"))
        features = {k: v.get("pos") for k, v in (g.get("features") or {}).items()}
        standpoints = {k: v.get("pos") for k, v in (g.get("standpoints") or {}).items()}
        out = {"size": g.get("size"), "features": features, "standpoints": standpoints}
        du, cat = _place_du_cat("wood", standpoints, features, g.get("cat_spots"))
        out["du"], out["cat"] = du, cat
        try:
            from core import wood_life as _wl
            st = _wl.status() or {}
            out["nest"] = st.get("nest")
            out["deadfall"] = st.get("deadfall")
            out["stream"] = st.get("stream")
        except Exception:
            pass
        return out
    except Exception as exc:
        return {"error": str(exc)}


# ── LETTERS TO TRAVIS (J-2348, D-0470 a, travis 2026-10-17; F-2959/F-2480) ──
# Du's own letters to Travis (data/letters/Letter_*.md) had NO reader: the HUD mailbox shows peer
# letters only. This is the founder-side, READ-ONLY view. It never writes data/letters/ or
# letters_state.json and nothing here reaches Du. "greeted" = the letter was handed to Du's Executive
# on a real founder message (letters_state.json 'delivered'); it says nothing about Travis reading it.
# The one write is the founder's own view log (letters_views.jsonl, a row only when Travis OPENS the
# card, ?view=1) so D-0470's second defeater ("never opened in 30 days") has a real instrument.
LETTERS_DIR = DATA_DIR / "letters"
LETTERS_STATE_PATH = DATA_DIR / "letters_state.json"
LETTERS_VIEWS_PATH = DATA_DIR / "letters_views.jsonl"


def _letter_when(name: str) -> str:
    # Letter_YYYYMMDD_HHMM.md -> "YYYY-MM-DD HH:MM" (filename is the write time, core/letters.py)
    try:
        s = name[len("Letter_"):-len(".md")]
        d, t = s.split("_", 1)
        return f"{d[0:4]}-{d[4:6]}-{d[6:8]} {t[0:2]}:{t[2:4]}"
    except Exception:
        return name


def load_letters_to_travis(letters_dir: Path = None, state_path: Path = None, limit: int = 300,
                           views_path: Path = None, record_view: bool = False) -> dict:
    letters_dir = letters_dir or LETTERS_DIR
    state_path = state_path or LETTERS_STATE_PATH
    views_path = views_path or LETTERS_VIEWS_PATH
    state = load_json_safe(state_path)
    greeted = set(state.get("delivered", []) or []) if isinstance(state, dict) else set()
    rows = []
    try:
        files = sorted(letters_dir.glob("Letter_*.md"), reverse=True)   # newest first
    except Exception:
        files = []
    for p in files[:max(1, int(limit))]:
        try:
            body = p.read_text(encoding="utf-8")
        except Exception:
            continue
        rows.append({"name": p.name, "when": _letter_when(p.name), "greeted": p.name in greeted,
                     "body": body})
    if record_view:
        try:
            import time as _t
            with open(views_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": _t.time(), "n_letters": len(files),
                                    "n_pending": sum(1 for p in files if p.name not in greeted)}) + "\n")
        except Exception:
            pass
    last_view = None
    try:
        if views_path.exists():
            with open(views_path, "r", encoding="utf-8") as f:
                _lines = [ln for ln in f if ln.strip()]
            if _lines:
                last_view = json.loads(_lines[-1]).get("ts")
    except Exception:
        last_view = None
    return {"total": len(files), "pending": sum(1 for p in files if p.name not in greeted),
            "shown": len(rows), "last_view": last_view, "letters": rows}


def load_evidence() -> dict:
    ev = {}
    for name, mod in _EVIDENCE_MODULES:
        try:
            m = __import__(f"core.{mod}", fromlist=[mod])
            ev[name] = m.status()
        except Exception as exc:
            ev[name] = {"error": str(exc)}
    ev["felt_preamble"] = _felt_preamble_rate()
    # Context-window sizing (2026-08-20). Assigned DIRECTLY rather than added to _EVIDENCE_MODULES,
    # because that loop calls `status()` and telemetry.status() shells out to nvidia-smi — a subprocess
    # with a 4s timeout — which has no business running on every evidence build. window_status() is a
    # pure read over the call log.
    try:
        from core import telemetry as _tel
        ev["context_windows"] = _tel.window_status()
        # Per-JOB (`module:line`), not per-lane — the unit that matters. inner_monologue_node alone
        # holds 9 prompt jobs across two lanes whose windows differ 3x; a lane average describes none
        # of them. This is the one to read.
        ev["prompt_jobs"] = _tel.job_status()
    except Exception as exc:
        ev["context_windows"] = {"error": str(exc)}
        ev["prompt_jobs"] = {"error": str(exc)}
    ev["protoself_series"] = load_shadow_series(
        "homeostasis_shadow.jsonl",
        ["coherence", "commitment_integrity", "relational_warmth", "novelty", "vitality"],
        limit=80, nested="variables")
    ev["arousal_series"] = load_shadow_series("arousal_shadow.jsonl", ["level", "tonic"], limit=120)
    ev["signatures"] = build_signatures(ev)
    return ev


def load_json_safe(path: Path, default=None):
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


_subconscious_cache = {
    "mtime": 0,
    "data": {}
}


def load_subconscious_trimmed():
    path = DATA_DIR / "subconscious_state.json"
    if not path.exists():
        return {}
    try:
        mtime = path.stat().st_mtime
        try:   # J-2418: integration_patterns may live in a sibling file; its mtime is part of the cache key
            from core.store_persist import patterns_path_for as _ppf
            mtime = (mtime, _ppf(path).stat().st_mtime)
        except Exception:
            pass
        if _subconscious_cache["mtime"] == mtime:
            return _subconscious_cache["data"]

        with open(path, "r", encoding="utf-8") as f:
            full_data = json.load(f)

        trimmed = {}
        for k, v in full_data.items():
            if k not in ("tensions", "integration_patterns", "t2_synth_buffer", "ai_echo_buffer"):
                trimmed[k] = v

        tensions = full_data.get("tensions", [])
        if isinstance(tensions, list):
            try:
                tensions = sorted(tensions, key=lambda x: x.get("count", 0), reverse=True)
            except Exception:
                pass
            trimmed_tensions = []
            for t in tensions[:50]:
                trimmed_tensions.append({
                    "id": t.get("id"),
                    "label": t.get("label"),
                    "count": t.get("count"),
                    "first_ts": t.get("first_ts"),
                    "last_ts": t.get("last_ts"),
                    "resolved": t.get("resolved")
                })
            trimmed["tensions"] = trimmed_tensions

        try:
            from core.store_persist import load_integration_patterns as _lip
            integrations = _lip(path, full_data)
        except Exception:
            integrations = full_data.get("integration_patterns", [])
        if isinstance(integrations, list):
            try:
                integrations = sorted(integrations, key=lambda x: x.get("count", 0), reverse=True)
            except Exception:
                pass
            trimmed_integrations = []
            for p in integrations[:50]:
                trimmed_integrations.append({
                    "id": p.get("id"),
                    "label": p.get("label"),
                    "count": p.get("count"),
                    "first_ts": p.get("first_ts"),
                    "last_ts": p.get("last_ts")
                })
            trimmed["integration_patterns"] = trimmed_integrations

        _subconscious_cache["mtime"] = mtime
        _subconscious_cache["data"] = trimmed
        return trimmed
    except Exception as exc:
        print(f"[HUD Server] Trim failed: {exc}")
        return {}


def load_t4_history(axiom_data: dict) -> list:
    if not isinstance(axiom_data, dict):
        return []
    if axiom_data.get("schema") == "multilevel-v1":
        facets = axiom_data.get("L3_facets", {}).get("facets", [])
        becoming = next((f for f in facets if f.get("id") == "the_becoming"), None)
        facet_history = []
        if becoming and "history" in becoming:
            for h in becoming["history"]:
                sc = h.get("self_image", "")
                prefix = "One way I have long felt myself: "
                suffix = " — and it is one room of me, not the whole house."
                if sc.startswith(prefix):
                    sc = sc[len(prefix):]
                if suffix in sc:
                    sc = sc.split(suffix)[0]
                facet_history.append({
                    "self_concept": sc.strip(),
                    "authored_at": h.get("ts"),
                    "revision": h.get("revision")
                })
        legacy_history = axiom_data.get("emergent_self_legacy", {}).get("history", [])
        return facet_history + legacy_history
    else:
        return axiom_data.get("emergent_self", {}).get("history", [])



def _reverse_lines(path: Path, chunk_size: int = 262144):
    """Yield lines of `path` newest-first, reading backward from EOF in chunks so a caller
    can stop early without scanning the whole file. Each byte is read and each line parsed
    (by the caller) at most once -- no re-scanning of already-seen data, unlike a naive
    grow-the-block-and-reread-it-all approach (that was tried and measured ~1.5-2x SLOWER
    than a plain full scan on this file's actual data shape, where matches are old/sparse
    and a "grow until N matches" scheme ends up re-reading most of the file more than once).
    Fail-open: yields nothing further on error (caller already wraps in try/except)."""
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf = b""
        while pos > 0:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            buf = f.read(read_size) + buf
            lines = buf.split(b"\n")
            for line in reversed(lines[1:]):
                yield line
            buf = lines[0]          # leftmost fragment carries no "\n" -- never re-yielded, never re-read
        if buf:
            yield buf


def load_provisional_identity_t4(path: Path, limit=20):
    """The T4 self-authoring feed for /api/t4, newest first (J-0266 / F-0329).

    The old source -- rows with type=='T4_self_authoring' in data/subconscious_log.jsonl (the
    load_jsonl_t4_safe() this replaces) -- has been DEAD since provisional_identity.ENABLED flipped
    True on 2026-06-22: nodes/subconscious_node.py returns on the provisional-identity path before
    the legacy _log_t4() call ever runs (its own 'LEGACY FALLBACK -- NOT THE LIVE COMMIT PATH'
    comment), so the panel showed 68+ days of false silence. The LIVE self-authoring events
    (open / extend* / paused* / solidify / revert) are appended by core/provisional_identity.py's
    _log() to data/logs/provisional_identity.jsonl. Each row is mapped here into the field names
    app.js's fetchT4() already renders (ts / reason / self_concept / arc_entry), so the display
    side needs no change. Streams backward from EOF via _reverse_lines() and stops at `limit`
    rows -- keeps J-0224's bounded-read discipline."""
    if not path.exists():
        return []
    out = []
    try:
        for raw in _reverse_lines(path):
            line = raw.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            ev = data.get("event")
            if not ev:
                continue
            theme = (data.get("theme") or "").strip()
            reason = f"{ev} — {theme}" if theme else ev
            integ = data.get("integration") or {}
            filt = data.get("filter") or {}
            df = data.get("dF") or {}
            if ev == "open":
                arc = (f"probation opened: filter pass={filt.get('pass')}, fit={filt.get('fit')}, "
                       f"novelty={filt.get('novelty')}, pole_delta={filt.get('pole_delta')}")
                if filt.get("reasons"):
                    arc += f" — {'; '.join(str(r) for r in filt['reasons'])}"
                if data.get("admission_judge") == "unjudged":
                    arc += " [UNJUDGED admission: decoupled judge returned None, self-graded filter admitted]"
            elif ev in ("solidify", "revert"):
                verdict = ("lived-integration CONFIRMED" if integ.get("integrated")
                           else "not lived (probation reverted)" if ev == "revert" else "solidified")
                arc = verdict
                if integ.get("confidence") is not None:
                    arc += f" (confidence {integ['confidence']})"
                if df.get("dF_did") is not None:
                    arc += f", dF_did={df.get('dF_did')}"
                if integ.get("reason"):
                    arc += f" — {integ['reason']}"
                if data.get("fatigued"):
                    arc += " [theme fatigued]"
            else:
                # extend / extend_uncertain_positive / paused_judge_unavailable / solidify_error ...
                extras = {k: v for k, v in data.items()
                          if k not in ("ts", "event", "theme", "self_image") and not isinstance(v, (dict, list))}
                arc = f"probation {ev}" + (f" ({json.dumps(extras, ensure_ascii=False)})" if extras else "")
            out.append({"ts": data.get("ts"), "event": ev, "reason": reason,
                        "self_concept": data.get("self_image") or "", "arc_entry": arc})
            if len(out) >= limit:
                break
    except Exception:
        pass
    return out


def load_jsonl_affect_safe(path: Path, limit=200):
    """Last `limit` affect rows, oldest-first, for the /api/affect_history chart seed.
    F-0385: streams backward from EOF via _reverse_lines() and stops at `limit` rows (J-0224/J-0278
    bounded-read discipline) instead of json.loads-ing all of affect_log.jsonl (1.26MB+) per poll."""
    if not path.exists():
        return []
    out = []
    try:
        for raw in _reverse_lines(path):
            line = raw.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
            if len(out) >= limit:
                break
    except Exception:
        pass
    out.reverse()   # collected newest-first; chart wants oldest-first
    return out


def tail_log_safe(path: Path, limit=100):
    if not path.exists():
        return ["[No log file found under " + str(path) + "]"]
    try:
        with open(path, "rb") as f:
            # Seek to end minus ~60KB to get recent logs efficiently
            try:
                f.seek(-60000, os.SEEK_END)
            except OSError:
                # File is smaller than 60KB
                f.seek(0)
            content = f.read().decode("utf-8", errors="ignore")
            lines = content.splitlines()
            return lines[-limit:]
    except Exception as exc:
        return [f"[Error reading log: {exc}]"]


def query_db_safe(sql: str, params=(), is_row=True):
    if not DB_PATH.exists():
        return []
    # Open SQLite in read-only mode defensively to prevent locks/conflicts with Nascence
    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False, timeout=15.0)
        if is_row:
            conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if is_row:
            result = [dict(r) for r in rows]
        else:
            result = rows
        conn.close()
        return result
    except Exception as exc:
        print(f"[HUD Server] DB query failed: {exc}")
        return []


class HUDRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Allow CORS for easy debugging
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # API Endpoints
        if path.startswith("/api/"):
            self.handle_api(path, query_params)
        else:
            self.handle_static(path)

    def handle_api(self, path: str, query_params: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

        response_data = {}

        if path == "/api/summary":
            # Gathers affect, climate, homeostasis, boredom, cat, room, world_model, social states
            response_data = {
                "affect": load_json_safe(DATA_DIR / "affect_state.json"),
                "climate": load_json_safe(DATA_DIR / "climate_state.json"),
                "homeostasis": load_json_safe(DATA_DIR / "homeostasis_state.json"),
                "boredom": load_json_safe(DATA_DIR / "boredom_state.json"),
                "cat": load_json_safe(DATA_DIR / "cat_state.json"),
                "room": load_json_safe(DATA_DIR / "room_state.json"),
                "world_model": load_json_safe(DATA_DIR / "world_model_state.json"),
                "social": load_json_safe(DATA_DIR / "social_state.json"),
                "subconscious": load_subconscious_trimmed()
            }

        elif path == "/api/memory":
            limit = int(query_params.get("limit", [100])[0])
            layer = query_params.get("layer", [""])[0]
            search = query_params.get("search", [""])[0]

            sql = "SELECT fragment_id, content, layer, relevance, importance, timestamp, origin, cold FROM memory_fragments"
            conditions = []
            params = []

            if layer:
                conditions.append("layer = ?")
                params.append(layer)
            if search:
                conditions.append("content LIKE ?")
                params.append(f"%{search}%")

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            response_data = query_db_safe(sql, tuple(params))

        elif path == "/api/epochs":
            epochs_sql = "SELECT timestamp_start, mood, impression, fragment_count FROM memory_epochs ORDER BY timestamp_start DESC LIMIT 50"
            themes_sql = "SELECT theme_name, current_stance, epoch_count FROM memory_themes ORDER BY epoch_count DESC"
            response_data = {
                "epochs": query_db_safe(epochs_sql),
                "themes": query_db_safe(themes_sql)
            }

        elif path == "/api/t4":
            axiom_data = load_json_safe(DATA_DIR / "identity" / "axiom.json")
            
            # Extract active self-concept and constitution for backwards-compatible frontend mapping
            self_concept = ""
            if axiom_data.get("schema") == "multilevel-v1":
                facets = axiom_data.get("L3_facets", {}).get("facets", [])
                becoming = next((f for f in facets if f.get("id") == "the_becoming"), None)
                if becoming:
                    self_concept = becoming.get("self_image", "")
                    prefix = "One way I have long felt myself: "
                    suffix = " — and it is one room of me, not the whole house."
                    if self_concept.startswith(prefix):
                        self_concept = self_concept[len(prefix):]
                    if suffix in self_concept:
                        self_concept = self_concept.split(suffix)[0]
                    self_concept = self_concept.strip()
                if not self_concept:
                    arc = axiom_data.get("L4_narrative", {}).get("arc_recent", [])
                    if arc:
                        self_concept = arc[-1]
            else:
                self_concept = axiom_data.get("emergent_self", {}).get("self_concept", "")
                
            core_axiom = ""
            if axiom_data.get("schema") == "multilevel-v1":
                commitments = axiom_data.get("L0_constitution", {}).get("commitments", [])
                core_axiom = "\n".join(f"• {c}" for c in commitments)
            else:
                core_axiom = axiom_data.get("core_axiom", "")

            # Expose compatibility fields alongside raw data
            response_data = {
                "axiom": {
                    "emergent_self": {
                        "self_concept": self_concept
                    },
                    "core_axiom": core_axiom,
                    **axiom_data
                },
                "t4_history": load_t4_history(axiom_data),
                # J-0266 / F-0329: read the LIVE self-authoring log. subconscious_log.jsonl's
                # T4_self_authoring rows died 2026-06-22 (provisional-identity path returns first) —
                # reading them showed a false "68 days silent" on the HUD (found 08-25).
                "subconscious_log": load_provisional_identity_t4(DATA_DIR / "logs" / "provisional_identity.jsonl")
            }

        elif path == "/api/affect_history":
            response_data = load_jsonl_affect_safe(DATA_DIR / "affect_log.jsonl")

        elif path == "/api/logs":
            limit = int(query_params.get("limit", [150])[0])
            response_data = tail_log_safe(LOG_PATH, limit)

        elif path == "/api/shadow":
            shadow_sql = "SELECT timestamp, cycle_id, raw_input, rejected_draft, corrections, source, resolved FROM shadow_events ORDER BY timestamp DESC LIMIT 30"
            light_sql = "SELECT timestamp, cycle_id, raw_input, integrated_content, source FROM light_events ORDER BY timestamp DESC LIMIT 30"
            response_data = {
                "shadow_events": query_db_safe(shadow_sql),
                "light_events": query_db_safe(light_sql)
            }

        elif path == "/api/evidence":
            # The Consciousness-Program evidence panel: each shadow instrument's signature + charts.
            response_data = load_evidence()

        elif path == "/api/health":
            # Operational health: pulse cadence, lanes, sleep pressure, balance — is the machine running well?
            response_data = load_health()

        elif path == "/api/du_pulse":
            # DU-PULSE CHECK (2026-08-29, J-0417): last recorded 4-category gauge snapshot + open watch-items.
            response_data = load_du_pulse()

        elif path == "/api/life":   # THE LIVING WORLD (J-0513): who's about, the calendar, carcasses, individuals, the shadow's counts
            try:
                from core import life as _life
                response_data = _life.status()
            except Exception as exc:
                response_data = {"error": str(exc)[:120]}
        elif path == "/api/garden_map":
            # THE GARDEN as a live map (2026-08-22): geometry + plants + items + shade + him + the cat
            response_data = load_garden_map()

        elif path == "/api/study_map":
            response_data = load_study_map()

        elif path == "/api/shore_map":
            response_data = load_shore_map()

        elif path == "/api/wood_map":
            response_data = load_wood_map()

        elif path == "/api/world":
            # WORLD FACTORIES P0 (2026-08-17): the manifest live view + the day's factory metrics.
            response_data = load_world_factories()

        elif path == "/api/transit_pulse":
            # TRANSIT PULSE (2026-08-23): live trains + recent station-tagged steps + deliveries.
            response_data = load_transit_pulse()

        elif path == "/api/letters":
            # LETTERS TO TRAVIS (J-2348, D-0470 a): Du's letters to Travis, read-only; ?view=1 logs that Travis opened it
            response_data = load_letters_to_travis(record_view=query_params.get("view", [""])[0] == "1")

        elif path == "/api/monitors":
            # The per-plan monitors index (grouped: plans / staged).
            try:
                from core import telemetry as _tel; _tel.sample()   # hardware/LLM graphs: sample on refresh
                from core import pursuits as _pu; _pu.sample_series()  # pursuits gate card: sample on refresh
            except Exception:
                pass
            response_data = load_monitors_index()

        elif path == "/api/monitor":
            # One monitor's time-series (lazy-loaded per chart). ?id=<monitor id>
            try:
                from core import telemetry as _tel; _tel.sample()   # grow the series while the card is watched
                from core import pursuits as _pu; _pu.sample_series()
            except Exception:
                pass
            response_data = load_monitor(query_params.get("id", [""])[0])

        elif path == "/api/du_lens_gauge":
            # D-0197 Du-lens gauge (J-3573): live per-pair counts + the 24h firing rate, read-only, fail-open.
            try:
                from core import du_lens_gauge as _dlg
                response_data = _dlg.summary(DATA_DIR / "du_lens_gauge_shadow.jsonl")
            except Exception as exc:
                response_data = {"error": str(exc)[:200]}
        else:
            self.send_error(404, "Endpoint not found")
            return

        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode("utf-8"))

    def handle_static(self, path: str):
        # Default index
        if path == "/" or path == "":
            path = "/index.html"

        # Sanitize path to static assets to prevent file traversal
        static_dir = Path(__file__).parent / "static"
        file_path = (static_dir / path.lstrip("/")).resolve()

        if not file_path.is_relative_to(static_dir):
            self.send_error(403, "Access Denied")
            return

        if not file_path.exists() or file_path.is_dir():
            self.send_error(404, "File Not Found")
            return

        # Content types
        mime_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon"
        }

        ext = file_path.suffix.lower()
        content_type = mime_types.get(ext, "application/octet-stream")

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            self.send_error(500, f"Internal Server Error: {exc}")


def run_server():
    server_address = ("", PORT)
    # THREADED (2026-07-07): the dashboard fires ~15 parallel chart-fetches; a single-threaded HTTPServer
    # serialised them and choked under the live sim's load (charts intermittently failed to render — a big
    # part of "graphs all over the place"). DB access is per-request with check_same_thread=False, so this is
    # safe. Each request now gets its own thread.
    httpd = ThreadingHTTPServer(server_address, HUDRequestHandler)
    print(f"[Nascence HUD] Server listening at http://localhost:{PORT} ...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Nascence HUD] Shutting down.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
