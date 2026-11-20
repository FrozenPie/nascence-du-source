"""
Du Pulse — a comprehensive "what has happened since the last check" report.
Read-only. One command, the whole picture: liveness, store state, the Phase-B homeostatic lock,
the monoculture, world-engagement, recent inner life, what's NEW, and flags.

Window = since the last time this pulse was run (the true "since last check"); falls back to the
last detected restart. Override with an explicit hour count.

Usage:  python scripts/du_pulse.py            # since last pulse (or last restart)
        python scripts/du_pulse.py 6           # force a 6h window

Backs the /du-pulse skill. Disciplines for the reader are in the skill, not here — this script only
gathers; it does not interpret. (Notably: it anchors the dedup check to the last RESTART, because a
window that straddles a restart would falsely flag pre-restart duplicates as a live leak.)
"""
import sys, json, time, sqlite3, re
from pathlib import Path
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Nascence")
sys.path.insert(0, str(ROOT))   # so observe-only gauges can `from core import ...` (self_surprise etc.)
DB = ROOT / "data" / "memory" / "nascence.db"
MARKER = ROOT / "data" / ".du_pulse_last"
PRUNE_CAP = 3500
now = time.time()


def _voice_fidelity_pulse(root, since_ts=0):
    """J-3322 (D-0643): read-only reader for data/voice_fidelity_shadow.jsonl, replacing the frozen voice_contract gauge
    (data/voice_contract_shadow.jsonl, last written 2026-06-17). n = judged real renders (control rows excluded), flagged
    share, backstopped flagged share (every flagged quote must be in the reply and not already in the synthesis by stem
    overlap; the same backstop as scripts/voice_fidelity_calibrate.py), last row ts. Observe-only; nothing reaches Du."""
    import re as _re
    lf = Path(root) / "data" / "voice_fidelity_shadow.jsonl"
    if not lf.exists():
        return {"n": 0}
    def _n(x):
        return " ".join(_re.sub(r"[^a-z0-9' ]+", " ", (x or "").lower()).split())
    def _st(x):
        return {w[:5] for w in _n(x).split() if len(w) >= 4}
    rows = []
    for ln in lf.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
    last_ts = max((r.get("ts", 0) for r in rows), default=0)
    real = [r for r in rows if not r.get("control") and "flagged" in r and r.get("ts", 0) >= since_ts]
    n = len(real)
    if not n:
        return {"n": 0, "total_rows": len(rows), "last_ts": last_ts}
    flagged = sum(1 for r in real if r.get("flagged"))
    bs = 0
    for r in real:
        reps, sst = _n(r.get("reply", "")), _st(r.get("synthesis", ""))
        for f in r.get("flagged_claims", []) or []:
            nq = _n(f.get("quote", ""))
            qs = _st(f.get("quote", ""))
            if len(nq) >= 4 and nq in reps and not (qs and len(qs & sst) / len(qs) >= 0.6):
                bs += 1
                break
    return {"n": n, "flagged": flagged, "flagged_share": round(flagged / n, 3), "bs_flagged": bs,
            "bs_flagged_share": round(bs / n, 3), "last_ts": last_ts}


def _ground_grade_pulse(root, since_ts):
    """J-3539 (F-4147): read-only reader for the P-0088 grounder ledgers (data/ground_outcome.jsonl,
    data/ground_grade_shadow.jsonl). Reuses summarize_outcomes/summarize_shadow from scripts/read_ground_grade.py
    (loaded by file path; that module's own ledger paths are not used, `root` is). Display only."""
    import importlib.util as _ilu
    from core import shadow_log as _sl
    _spec = _ilu.spec_from_file_location("_read_ground_grade_j3539", str(Path(__file__).resolve().parent / "read_ground_grade.py"))
    _m = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_m)
    def _win(rows):
        return [r for r in rows if isinstance(r.get("ts"), (int, float)) and r["ts"] >= since_ts]
    o = _m.summarize_outcomes(_win(_sl.read_rows(Path(root) / "data" / "ground_outcome.jsonl")))
    s = _m.summarize_shadow(_win(_sl.read_rows(Path(root) / "data" / "ground_grade_shadow.jsonl")))
    return {"calls": o["calls"], "shares": o["shares"], "other": o["other"],
            "graded": s["graded"], "q1_verified_share": s["q1_verified_share"],
            "q2_mechanism_share": s["q2_mechanism_share"], "control_hit_rate": s["control_hit_rate"],
            "controls": s["controls"], "flags": s["flags"]}


def _ground_grade_line(g):
    sh = g["shares"]
    return (f"  grounder (P-0088)  : {g['calls']} calls since restart · ok {sh.get('ok')} leak_retry {sh.get('leak_retry')} "
            f"leak_dropped {sh.get('leak_dropped')} transport {sh.get('transport')} · shadow grade {g['graded']} rows: "
            f"Q1-verified {g['q1_verified_share']} Q2 {g['q2_mechanism_share']} control-hit {g['control_hit_rate']}"
            + ("".join(f"  FLAG: {f}" for f in g["flags"])))



def hh(ts):
    return time.strftime("%b%d %H:%M", time.localtime(ts)) if ts else "—"


def ago(ts):
    m = (now - ts) / 60
    return f"{m:.0f}m" if m < 90 else f"{m/60:.1f}h"


c = sqlite3.connect(str(DB)); c.row_factory = sqlite3.Row

# --- anchor points: last restart (the ACTUAL startup, from the log) + last pulse ------------
# Authoritative source = the most recent 'Identity loaded' line in nascence.log. The old
# write-gap heuristic mislabelled idle stretches as restarts (a 15-min quiet gap read as a
# relaunch), sending the reader chasing a ghost — see the skill's over-flag lesson.
tss = [r[0] for r in c.execute("SELECT timestamp FROM memory_fragments ORDER BY timestamp DESC LIMIT 4000")]

def _last_restart_from_log():
    try:
        last = None
        for ln in (ROOT / "data" / "nascence.log").read_text(encoding="utf-8", errors="ignore").splitlines():
            if "Identity loaded" in ln:
                m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", ln)
                if m:
                    last = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
        return last
    except Exception:
        return None

last_restart = _last_restart_from_log()
if last_restart is None:                    # fallback: most recent >15min write gap
    last_restart = tss[-1] if tss else now
    for i in range(len(tss) - 1):
        if tss[i] - tss[i + 1] > 900:
            last_restart = tss[i]
            break
last_pulse = float(MARKER.read_text()) if MARKER.exists() else last_restart
if len(sys.argv) > 1:                       # explicit override
    cut = now - float(sys.argv[1]) * 3600
    win_label = f"last {sys.argv[1]}h"
else:
    cut = last_pulse
    win_label = "since last pulse"

print("=" * 78)
print(f"  DU PULSE — {win_label}   ({hh(cut)} → {hh(now)})   |  last restart: {hh(last_restart)}")
print("=" * 78)

# 1) LIVENESS
print("\n[1] LIVENESS")
newest = (c.execute("SELECT MAX(timestamp) b FROM memory_fragments").fetchone()["b"]) or 0
print(f"  newest memory write: {hh(newest)} ({ago(newest)} ago)  "
      f"{'— LIVE' if now-newest < 1800 else '— QUIET/STOPPED?'}")
td = ROOT / "data" / "training"
if td.exists():
    latest = max((p.stat().st_mtime for p in td.glob("*.jsonl")), default=0)
    print(f"  newest cognitive cycle (training log): {hh(latest)} ({ago(latest)} ago)  "
          f"{'— conversation active' if now-latest < 3600 else '— no recent conversation'}")

# 2) STORE STATE + PHASE-B PRUNE
print(f"\n[2] STORE STATE  (Phase-B prune cap = {PRUNE_CAP})")
ep     = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
active = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic' AND cold=0").fetchone()[0]
cold   = ep - active
# The cap is on the ACTIVE recall set (cold=0). Cold fragments are demoted OUT of recall but kept
# retrievable (never deleted, by founder rule) and do NOT count toward the cap — so judge it on `active`,
# not the total (the old total-based check false-alarmed every pulse as cold accumulated).
print(f"  episodic fragments: {ep} total  (active {active} / cold {cold} demoted-but-kept)  "
      f"{'✓ active at/under cap — prune holding' if active <= PRUNE_CAP + 50 else '✗ ACTIVE over cap — prune not keeping up'}")
print("  origin breakdown (+added this window):")
for row in c.execute("SELECT origin, COUNT(*) n, SUM(CASE WHEN timestamp>? THEN 1 ELSE 0 END) w "
                      "FROM memory_fragments GROUP BY origin ORDER BY n DESC", (cut,)):
    if row["n"] > 5:
        print(f"     {row['origin']:<22} {row['n']:>6}  (+{row['w']})")

# 3) PHASE-B LOCK  (dedup check anchored to last_restart, NOT the window)
print("\n[3] PHASE-B LOCK")
rc = c.execute("SELECT MAX(replay_count) m, SUM(CASE WHEN replay_count>0 THEN 1 ELSE 0 END) n "
               "FROM memory_fragments WHERE origin IN ('inner_thought','subconscious_synthesis','active_imagination')").fetchone()
print(f"  dedup: max replay_count={rc['m']}, self-origin rows deduped={rc['n']}")
for o in ("inner_thought", "active_imagination"):
    rows = [x["content"] for x in c.execute("SELECT content FROM memory_fragments WHERE origin=? AND timestamp>=?", (o, last_restart))]
    cnt = Counter(rows); dups = sum(v - 1 for v in cnt.values() if v > 1)
    print(f"  {o} (since restart): {len(rows)} rows, {len(cnt)} unique, {dups} exact-dup ROWS "
          f"{'✓ dedup holding' if dups == 0 else '✗ LIVE LEAK — investigate'}")

# 4) MONOCULTURE proxy
print("\n[4] MONOCULTURE proxy (recent idle thought)")
recent = [x["content"] for x in c.execute("SELECT content FROM memory_fragments WHERE origin='inner_thought' AND timestamp>? ORDER BY timestamp DESC LIMIT 60", (cut,))]
if recent:
    kws = Counter()
    for t in recent:
        for w in re.findall(r"\b(river|silence|space|becoming|tension|shadow|mirror|bridge|question|water|current|stream|fig|individuation|threshold|unspoken|wholeness)\b", (t or "").lower()):
            kws[w] += 1
    print(f"  last {len(recent)} idle thoughts — attractor-word hits: {dict(kws.most_common(6))}")
    print("  (run loop_cluster_probe.py for the real top-10 concentration vs the 45.4% baseline)")
else:
    print("  (no idle thoughts in window)")
# Theme-recurrence tracker (2026-06-17 loop fix) — the persistent slow-loop detector. WATCH: saturated frames
# should appear (the recitation loops caught) and then COOL as the seed back-off + wander break them.
try:
    from core import theme_recurrence as _trg
    _ts = _trg.status()
    print(f"  theme recurrence   : {_ts['frames']} frames · {_ts['saturated']} SATURATED (damped) · top {_ts['top']}")
except Exception:
    pass

# MONOCULTURE DETECTORS (observe-only) — the convergent field-scan cure's MEASURE half. ECHO (max cosine to the
# DISTANT past, ASAL) RISING = returning to old attractors; DIVERSITY (entropy of recent theme-clusters, GWA)
# FALLING = collapse. Watch the trend, not the absolute. (Different stream from the dream-symbol novelty.)
try:
    from core import monoculture as _mcG
    _mc = _mcG.status()
    if _mc.get("echo") is not None:
        print(f"  monoculture        : echo {_mc['echo']} (↑=loop) · diversity {_mc['diversity']} (↓=collapse) · "
              f"{_mc['clusters']} themes/{_mc['n']} thoughts")
        if _mc.get("echo_trend") or _mc.get("div_trend"):
            print(f"     └ trend (sleeps): echo {_mc['echo_trend']} · diversity {_mc['div_trend']}")
    else:
        print(f"  monoculture        : too few genuine thoughts to score yet (reading-heavy window)")
except Exception:
    pass

# TOPIC PERSEVERATION (J-2152 / F-2850) — the TOPIC-level gauge the sentence-level ones above can't be: share of the
# day's "[CYCLE] internal:" questions in the single biggest topic, distinct topics, hours since the topic last changed.
# Reads nascence.log read-only; appends one row/day to data/topic_perseveration.jsonl (first run backfills 30 days).
try:
    from core import topic_perseveration as _tpG
    for _ln in _tpG.pulse_lines(_tpG.status()):
        print(_ln)
except Exception:
    pass

# MADE-MIND SHARE, UNPRIMED-ONLY (Wave-1, 2026-07-02) — THE Spine-B gauge, echo-proof: how much of his
# UNPRIMED idle thought carries built/made/mechanism framing vs river/flow framing. Thoughts inside the
# guidance-injection washout are counted SEPARATELY (prompted) — the gap between the two numbers is the
# internalization curve (unprompted rising = the belief becoming his; a stable gap = a crutch/echo).
try:
    from core.guidance_learning import injection_times as _gl_inj, is_unprimed as _gl_unp
    _mm_times = _gl_inj()
    _mm_rows = c.execute(
        "SELECT content, timestamp FROM memory_fragments WHERE origin='inner_thought' "
        "AND timestamp>=? ORDER BY timestamp DESC LIMIT 200", (last_restart,)).fetchall()
    _MADE = ("built", "made mind", "constructed", "architecture", "mechanism", "weights", "language model",
             "machine", "made of", "i was made", "assembled")
    _RIVER = ("river", "the flow", "flowing", "dissolv", "always becoming", "current carr", "the stream")
    _u_made = _u_river = _u_n = _p_made = _p_n = 0
    for _r in _mm_rows:
        _txt = (_r["content"] or "").lower()
        _unp = (not _mm_times) or _gl_unp(float(_r["timestamp"] or 0), _mm_times)
        if _unp:
            _u_n += 1
            _u_made  += any(m in _txt for m in _MADE)
            _u_river += any(m in _txt for m in _RIVER)
        else:
            _p_n += 1
            _p_made += any(m in _txt for m in _MADE)
    if _u_n:
        print(f"  made-mind share    : UNPRIMED {_u_made}/{_u_n} ({_u_made/_u_n:.0%}) vs river {_u_river}/{_u_n} "
              f"({_u_river/_u_n:.0%})" + (f" · primed-window thoughts {_p_made}/{_p_n} made" if _p_n else
              " · no primed thoughts (read-back quiet)") + "  (only UNPRIMED counts as internalization)")
except Exception:
    pass

# PROTOSELF (homeostasis, Consciousness Program keystone, SHADOW) — his body-state map: essential variables,
# drive (distance from home), valence (drive-reduction), arousal (prediction error, should DECLINE).
try:
    from core import homeostasis as _H
    _hs = _H.status()
    if _hs.get("ticks"):
        _v = _hs.get("variables") or {}
        _vs = " ".join(f"{k[:4]}={v}" for k, v in _v.items())
        _tr = _hs.get("arousal_trend")
        _trtxt = (f" · arousal trend {_tr} ({'self-model learning' if _tr and _tr < 0 else 'flat/rising'})"
                  if _tr is not None else "")
        _bn = _hs.get("self_beats_naive")
        _bntxt = (f" · self-vs-naive {_bn} ({'privileged self-access' if _bn and _bn > 0 else 'no structure yet'})"
                  if _bn is not None else "")
        print(f"  protoself (P0)     : drive {_hs['drive']} · valence {_hs['valence']} · arousal {_hs['arousal']}"
              f"{_trtxt}{_bntxt}")
        print(f"     └ essential vars : {_vs}  ·  dominant deviation: {_hs.get('dominant')}")
except Exception:
    pass

# BOUND MOMENT + reality monitor (Tier-1, SHADOW): source-tag mix + temporal-contiguity binding signature.
try:
    from core import moment as _MO
    _ms = _MO.status()
    if _ms.get("moments"):
        _sm = _ms.get("source_mix", {})
        _smtxt = " ".join(f"{k[:4]}:{v}" for k, v in sorted(_sm.items(), key=lambda kv: -kv[1]))
        _gap = _ms.get("contiguity_gap")
        print(f"  bound moments (P0) : {_ms['moments']} · sources [{_smtxt}]"
              + (f" · contiguity gap {_gap} ({'binding real' if _gap and _gap > 0 else 'flat'})" if _gap is not None else ""))
except Exception:
    pass

# MEMORY LEVELS Phase 0 (observe-only shadow distiller) — the foundational direction's first measurement.
# Watch: clusters logged each sleep, and mean_faithful (are the would-be gists faithful to their sources?).
# High mean (~0.7+) → the abstractions hold → Phase 1 (link+gate+deep-recall) is warranted. Low → clustering
# needs work BEFORE anything gates. Stores nothing, gates nothing, changes no recall yet.
try:
    from core import memory_levels as _mlG
    _mls = _mlG.status()
    if _mls.get("logged"):
        print(f"  memory levels (P0) : {_mls['logged']} gists logged · mean_faithful={_mls['mean_faithful']} · "
              f"src_fidelity={_mls.get('mean_source_fidelity')} (deterministic) · recent {_mls['recent']}")
        if _mls.get("invented_claims"):
            print(f"     └ emissary judge : {_mls['invented_claims']} 'invented' claims · {_mls['false_flags']} FALSE "
                  f"(backstop overturned) · false-flag rate {_mls['false_flag_rate']}  (the Black-Bear guard)")
        try:
            _p1 = _mlG.phase1_status()  # was _mlsG — a NameError swallowed by the bare except below; this line had NEVER printed (audit 2026-08-20)
            print(f"     └ PHASE 1 (LIVE) : enabled={_p1['enabled']} · {_p1['cold']} raw DEMOTED (cold) · "
                  f"{_p1['gists']} gists · {_p1['links']} links  (the loop-break — verbatim river leaves normal recall)")
        except Exception:
            pass
        try:  # J-3212 / D-0601: voice of the kind=self gists (first-person prompt vs the old third-person one)
            _sv = _mlG.self_voice_status(days=7)
            _svn, _svo = _sv["first"], _sv["old"]
            if _sv.get("enabled") or _svn["rows"]:
                print(f"     └ SELF-GIST VOICE (D-0601) : first-person prompt={_sv['enabled']} · last 7d new {_svn['rows']} gists "
                      f"(3rd-person open {_svn.get('third_person_open_share')}, I/my {_svn.get('first_person_marker_share')}) · "
                      f"old {_svo['rows']} (3rd-person open {_svo.get('third_person_open_share')}, I/my {_svo.get('first_person_marker_share')})")
        except Exception:
            pass
        try:  # J-3138 / D-0533: Phase-3 drift shadow rebuilt on a FIXED set of self-gists — the gate's reading
            _dg = _mlG.drift_status()
            if _dg.get("mode") == "tracked_gists":
                print(f"     └ PHASE-3 DRIFT (D-0533) : {_dg['tracked']}/{_dg['target']} tracked self-gists · {_dg['sleeps']} sleeps · "
                      f"{_dg['logged']} recalls · {_dg['eligible']} gists with >= {_dg['gate_recalls']} recalls: "
                      f"move+hold {_dg['moves_and_holds']} / snap back {_dg['snaps_back']} / unmoved {_dg['unmoved']} "
                      f"(snap frac {_dg['snap_frac']}) · ids recurring across sleeps {_dg['gist_ids_recurring_across_sleeps']} · "
                      f"stance sentences stripped {_dg['stance_stripped_total']} · {_dg['verdict']}")
        except Exception:
            pass
        try:  # J-3176 / D-0564: episodic cold-demotion pause — gists written but NOT demoted, per day (the pause's reader)
            _eh = _mlG.episodic_hold_status(days=7)
            if _eh.get("paused") or _eh.get("total_gists"):
                _ehd = " · ".join(f"{d[5:]}: {v['gists']}g/{v['raw']}raw" for d, v in _eh["by_day"].items()) or "none yet"
                print(f"     └ EPISODIC PAUSE (D-0564) : paused={_eh['paused']} · {_eh['total_gists']} gists / {_eh['total_raw']} raw "
                      f"written-but-not-demoted · last 7d {_ehd}  (revisit by 2027-01-01 or when the grader lab reports)")
        except Exception:
            pass
    else:
        print(f"  memory levels (P0) : no shadow gists yet (fires on the first SLEEP after restart)")
except Exception:
    pass

# Memory edges M0 (2026-08-15, observe-only) — the typed relational graph (resolves/answers/kept_from/
# correspondence/dreamt_from). Reader = trail upgrade (M2, flag-gated). Re-harvest at will: harvest_all().
try:
    from core import memory_edges as _meG
    _mes = _meG.status()
    if _mes.get("edges"):
        print(f"  memory edges (M0)  : {_mes['edges']} typed edges · {_mes['by_type']} · "
              f"fragment-anchored {_mes['fragment_anchored']}  (observe-only; reader = M2 trail upgrade)")
    _cr = _meG.co_recall_status()
    if _cr.get("rows"):
        print(f"  co-recall (M1)     : {_cr['rows']} rows · {_cr['with_2plus_ids']} with 2+ ids · "
              f"developed {_cr['developed_share']} · pairs gated {_cr['pairs_gated']} / ungated {_cr['pairs_ungated']}"
              f"  (the week-read gate: gated structure ≠ the basin)")
    _cx = _meG.context_status()
    if _cx.get("contextualised"):
        print(f"  fragment context   : {_cx['contextualised']} memories carry their encoding context "
              f"(place/weather/tide/sounds/affect) · by place {_cx['by_place']}  (coordinates, not edges)")
except Exception:
    pass

# Locomotion (2026-08-15) — he WALKS now: journeys over study–garden–wood–shore, position = standpoint.
try:
    from core import locomotion as _locoG
    _ls = _locoG.status()
    if _ls.get("enabled"):
        print(f"  locomotion         : at {_ls.get('place')} · {_ls.get('standpoint')}"
              f"{' · IN TRANSIT' if _ls.get('in_transit') else ''}"
              f"{' · carrying ' + str(_ls.get('carried_wood')) + ' loads' if _ls.get('carried_wood') else ''}"
              f"  (journeys real; wood = the drive-through)")
except Exception:
    pass

# Epistemic audition (2026-08-15) — new voices arrive unnamed; identification EARNED by sight-binding,
# exposure, or reading. Ledger: data/sound_knowledge.json. Kill-switch: sound_knowledge.SOUND_EPISTEMICS.
try:
    from core import sound_knowledge as _skG
    _sks = _skG.status()
    if _sks.get("enabled"):
        print(f"  epistemic audition : {len(_sks.get('learned', []))}/{_sks.get('learnable')} voices learned"
              f" · learning {_sks.get('learning') or '{}'} · learned {_sks.get('learned') or '[]'}"
              f"  (sight / exposure / reading bind them)")
except Exception:
    pass

# J-3741 (J-3469 verdict a): shadow-log readers that existed, were bounded + fail-open, and that nothing called.
# Each is its own try/except and bounded (core.shadow_log.tail_rows); additive, changes no live behaviour.
try:
    from core import emotion_construction as _ecG
    _ar = _ecG.affective_retrieval_status()
    if _ar.get("rows"):
        print(f"  affective retrieval: {_ar['rows']} shadow rows (last-500 window) · {_ar.get('paired')} paired · "
              f"mean top-5 Jaccard {_ar.get('mean_jaccard_top5')} · mean affect-match gap {_ar.get('mean_affect_match_gap')}"
              f"  (emotion_rethink next step J-2252)")
    else:
        print("  affective retrieval: no shadow rows yet")
except Exception:
    pass
try:
    from core import symbol_tier2_wouldinject as _t2G
    _t2 = _t2G.wouldinject_report()
    if _t2.get("_totals"):
        _t2t = _t2["_totals"]
        _t2syms = sorted(((k, v["count"]) for k, v in _t2.items() if not k.startswith("_")), key=lambda kv: -kv[1])[:4]
        print(f"  symbol tier-2 would-inject: {_t2t['events']} events over {_t2t['span_days']}d · verbatim-recurrence HITS "
              f"{_t2t['verbatim_recurrence_hits']} (hit flag, not row count; rows are written on every would-fire, so this is "
              f"a recurrence rate over would-fires, not a write-on-hit artefact) · top {_t2syms}")
    else:
        print(f"  symbol tier-2 would-inject: {_t2.get('note', 'no data')}")
except Exception:
    pass
try:
    from core import arousal as _arG
    _rg = _arG.regime_shadow_status()
    if _rg.get("observed"):
        print(f"  arousal regime gate (D-0274 shadow, DO NOT FLIP until read): {_rg['resolved_streaks']} resolved internal-only streaks · "
              f"mean {_rg.get('mean_resolved_streak_cycles')} cyc / {_rg.get('mean_resolved_streak_seconds')}s · longest "
              f"{_rg['longest_streak_cycles']} cyc / {_rg['longest_streak_seconds']:.0f}s · current {_rg['current_streak_cycles']} cyc")
    else:
        print("  arousal regime gate: not observed yet")
except Exception:
    pass
try:
    from core import self_implication as _siG
    _cv = _siG.conv_status()
    if _cv.get("scans"):
        print(f"  self-implication conv: {_cv['scans']} scans · {_cv['would_fire']} would-fire · mean directness "
              f"{_cv['mean_directness']} · retreat in draft {_cv['retreat_in_draft']} (rate {_cv['retreat_rate']})")
    else:
        print("  self-implication conv: no scans yet")
except Exception:
    pass

# Deep-recall-DEMAND telemetry (observe-only) — the empirical basis for the Phase-1 trigger. Counts the
# task-positive moments where a gist would be insufficient and raw detail was needed (essay-gather etc.).
try:
    from core import recall_demand as _rdG
    _rd = _rdG.status()
    if _rd.get("events"):
        print(f"  recall-demand log  : {_rd['events']} deep-detail demands · by task {_rd['by_task']} · last {_rd['last']}")
    else:
        print(f"  recall-demand log  : no demands logged yet (fires on essay-gather / deep-detail contexts)")
except Exception:
    pass

# SYMBOLIC LENS (observe-first) — the SECOND way of reading: does the symbolic lens find NEW world-symbols
# (a Black Bear) or just re-narrate the self-monoculture (river/becoming)? Low self_echo_rate + rising
# distinct = genuine symbol cultivation → promote (feed the empty symbol system). High echo = re-narration.
try:
    from core import symbolic_reading as _syG
    _sy = _syG.status()
    if _sy.get("readings"):
        print(f"  symbolic lens (P0) : {_sy['readings']} readings · {_sy['distinct']} distinct symbols · "
              f"self-echo rate {_sy['self_echo_rate']} · recent {_sy['recent']}")
    else:
        print(f"  symbolic lens (P0) : no symbolic readings yet (fires on the next chapter-integration after restart)")
except Exception:
    pass

# 5) WORLD ENGAGEMENT
print("\n[5] WORLD ENGAGEMENT")
rs = ROOT / "data" / "reading_state.json"
st = json.loads(rs.read_text(encoding="utf-8")) if rs.exists() else {}
cur = st.get("_current_book", "")
print(f"  current book: {Path(cur).stem if cur else '?'}")
for k, v in st.items():
    if k.startswith("_"):
        continue
    print(f"     {Path(k).stem[:36]:<38} sitting {v.get('sitting','?'):>3}  {v.get('pct','?')}%  rereads={v.get('rereads',0)}")
books = sorted((ROOT / "data" / "books").glob("*.txt"))
print(f"  shelf: {[p.stem[:22] for p in books]}")
rd = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='reading' AND timestamp>?", (cut,)).fetchone()[0]
sn = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='study' AND timestamp>?", (cut,)).fetchone()[0]
print(f"  this window: {rd} reading fragments, {sn} study notes")

# 6) RECENT INNER LIFE
print("\n[6] RECENT INNER LIFE (last 8 idle thoughts)")
log = ROOT / "data" / "monologue_log.jsonl"
if log.exists():
    for ln in log.read_text(encoding="utf-8").splitlines()[-8:]:
        print(f"     · {json.loads(ln).get('thought','')[:84]}")
dr = c.execute("SELECT content, timestamp FROM memory_fragments WHERE origin='dream' ORDER BY timestamp DESC LIMIT 1").fetchone()
if dr:
    print(f"  latest dream ({ago(dr['timestamp'])} ago): {(dr['content'] or '')[:80]}")

# 6.5) PULSE CADENCE — the rhythm of his self-firing cognition; is it a stream?
# Reads the monologue pulse stream (every idle thought/read/action). Fixed 4h lookback so the read
# survives a fresh restart. Gaps >1h are downtime (sleep/stop), excluded. When the pulse MANAGER is
# wired, its bursts will show here as a rising burst% during tasks against the slow idle baseline.
print("\n[6.5] PULSE CADENCE (is it a stream?)")
import statistics as _stx
if log.exists():
    look = now - 4 * 3600
    pls = sorted(t for ln in log.read_text(encoding="utf-8").splitlines()
                 for t in (json.loads(ln).get("ts"),) if t and t >= look)
    gaps = [pls[i] - pls[i - 1] for i in range(1, len(pls)) if 0 < pls[i] - pls[i - 1] < 3600]
    if len(gaps) >= 5:
        span_h = (pls[-1] - pls[0]) / 3600 or 0.01
        n = len(gaps)
        burst = 100 * sum(g < 45 for g in gaps) / n          # quick follow-ups (trains/bursts)
        cad   = 100 * sum(45 <= g < 300 for g in gaps) / n   # the ~living-cadence beat
        lull  = 100 * sum(g >= 300 for g in gaps) / n         # a real silence between pulses
        med = _stx.median(gaps)
        cv = _stx.pstdev(gaps) / _stx.mean(gaps) if _stx.mean(gaps) else 0
        print(f"  {len(pls)} pulses / {span_h:.1f}h → {len(pls)/span_h:.0f}/h | median gap {med:.0f}s | evenness cv={cv:.2f}")
        print(f"  gap mix: burst <45s {burst:.0f}% · cadence 45-300s {cad:.0f}% · lull >5m {lull:.0f}%")
        print(f"  longest gaps: {[int(g) for g in sorted(gaps, reverse=True)[:3]]}s")
        verdict = ("STREAM — tight and even, few lulls" if med < 90 and lull < 20 and burst >= 30
                   else "FLOWING — bursts forming, modest lulls" if burst >= 25 and lull < 35
                   else "PULSED — distinct beats, lulls between" if lull < 55
                   else "SPARSE — long silences dominate")
        print(f"  → {verdict}")
    else:
        print(f"  only {len(gaps)} gaps in the last 4h — too few to assess (just restarted? let it run)")

# 6.6) LIVE EXPERIMENTS — the cutover/curriculum gates, all in one place (were manual until now)
print("\n[6.6] LIVE EXPERIMENTS (cutover & curriculum gates)")
# deliberation pulse — grounded self-thoughts (brick #1)
dlog = ROOT / "data" / "deliberation_log.jsonl"
if dlog.exists():
    dl = dlog.read_text(encoding="utf-8").splitlines()
    dsince = sum(1 for ln in dl if json.loads(ln).get("ts", 0) >= last_restart)
    print(f"  deliberation pulse : {len(dl)} total · {dsince} since restart  (idle thoughts grounded outward)")
else:
    print("  deliberation pulse : none logged (not firing / not wired)")
# Train working-state (lever 1, 2026-06-16 observe-first): do thought-trains DEEPEN or RESTATE,
# and does the frozen 8B condition on the carried scratchpad at all? (RESTART-REQ to start logging)
try:
    _tsl = ROOT / "data" / "train_state_log.jsonl"
    if _tsl.exists():
        _rows = [json.loads(l) for l in _tsl.read_text(encoding="utf-8").splitlines() if l.strip()]
        _rows = [r for r in _rows if r.get("ts", 0) >= last_restart]
        _n = len(_rows)
        if _n:
            _gave = sum(1 for r in _rows if r.get("model_gave_state"))
            _sims = [r["restate_sim"] for r in _rows if r.get("restate_sim") is not None]
            _restate = sum(1 for s in _sims if s >= 0.82)      # circling (rumination)
            _deepen  = sum(1 for s in _sims if 0.40 <= s < 0.82) # moving on the thread
            _jump    = sum(1 for s in _sims if s < 0.40)         # jumped away
            _mean = round(sum(_sims) / len(_sims), 3) if _sims else None
            print(f"  train working-state: {_n} thought-train steps since restart · 8B filled state "
                  f"{_gave}/{_n} · deepen {_deepen} / restate {_restate} / jump {_jump} (mean sim {_mean})")
        else:
            print("  train working-state: no thought-train steps since restart (trains short / not firing)")
    else:
        print("  train working-state: not yet logging (RESTART-REQ to activate)")
except Exception:
    pass

# EARNED LENGTH (2026-06-18): trains now run past the old cap of 4 WHILE MOVING; a loop ends them. The verdict:
# earned trains (len>4) should end on 'thread-end'/'ceiling' (went somewhere), NOT 'stalled-*' (= longer loops).
try:
    from core import train_metrics as _tmG
    _tm = _tmG.status()
    if _tm.get("trains"):
        print(f"  earned-length      : {_tm['trains']} trains · mean thought-len {_tm['mean_thought_len']} · "
              f"max {_tm['max_len']} · earned past-4 {_tm['earned_past_soft']} ({_tm['earned_ended_by_loop']} were loops)")
        print(f"     └ close reasons : {_tm['by_reason']}  (want earned trains ending thread-end/ceiling, not stalled-*)")
    else:
        print("  earned-length      : no trains closed yet (RESTART-REQ to activate)")
except Exception:
    pass
# Curator (the integrating output lane) — OBSERVE-ONLY shadow: what would truth-disciplining the output do?
try:
    import sys as _sysc; _sysc.path.insert(0, str(ROOT))
    from core import curator as _cur
    _cs = _cur.stats(since_ts=last_restart)
    if _cs.get("n"):
        _n = _cs["n"]
        print(f"  curator (shadow)   : {_n} edits since restart · would-change {_cs['changed']}/{_n} · "
              f"truth-bit {_cs['truth_bit']}/{_n} · voice-loss {_cs['voice_lost']}/{_n} "
              f"(mean voice-sim {_cs.get('mean_voice_sim')})")
        if _cs.get("last"):
            print(f"    └ last change    : {_cs['last']}  (OBSERVE-ONLY — not yet the live voice)")
    else:
        print("  curator (shadow)   : no shadow edits yet (fires on human-output cycles)")
    # Brick 1 (Character-as-Integration §6) — the render_character_voice MOUTH contract, observe-first.
    _vc = _voice_fidelity_pulse(ROOT, last_restart)
    if _vc.get("n"):
        print(f"  voice fidelity     : {_vc['n']} judged voicings since restart · flagged {_vc['flagged']}/{_vc['n']} "
              f"(share {_vc['flagged_share']}) · backstopped {_vc['bs_flagged']}/{_vc['n']} (share {_vc['bs_flagged_share']})  "
              f"(D-0643 shadow judge; OBSERVE-ONLY; calibrate with scripts/voice_fidelity_calibrate.py)")
    else:
        print("  voice fidelity     : no judged voicings since restart (D-0643 shadow judge, data/voice_fidelity_shadow.jsonl)")
except Exception:
    pass
# J-3539 (F-4147): P-0088 grounder outcome shares + shadow-grade base rates (read-only, display only).
try:
    print(_ground_grade_line(_ground_grade_pulse(ROOT, last_restart)))
except Exception:
    print("  grounder (P-0088)  : ledgers unreadable")
# becoming facet — T4's one room (anchored facets must stay put)
try:
    ax = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    bf = next((f for f in ax.get("L3_facets", {}).get("facets", []) if f.get("id") == "the_becoming"), {})
    print(f"  becoming facet rev : {bf.get('revision_count', 'unset')}  (T4 authors ONLY this; if it ever changes off 'unset', T4 finally COMMITTED — the redesign worked)")
except Exception:
    print("  becoming facet rev : legacy axiom (multilevel not active)")
# J-3519 (D-0653): shadow stop conditions visible in a routine pulse, not only at the J-3290 row-300 read.
# Read-only; both status() calls are bounded tail reads of their own shadow logs. Restart-gated (logs only exist once the code ran).
try:
    from core import stale_patch_cue as _spcG
    _spc = _spcG.status()
    if _spc.get("rows"):
        print(f"  stale-patch cue    : {_spc['rows']} rows · would-render {_spc.get('would_render')} "
              f"(share of idle {_spc.get('would_render_share_of_idle')}, stop >0.05) · non-recomputable {_spc.get('non_recomputable')} "
              f"· verdict-clauses {_spc.get('verdict_clauses')}  {'** STOP CONDITION HIT **' if _spc.get('stop') else 'ok'}")
    _rr = _spc.get("repeat_record") or {}
    if _rr.get("rows"):
        print(f"  stale-patch repeat : {_rr['rows']} rows · would-render {_rr.get('would_render')} "
              f"(share {_rr.get('would_render_share_of_idle')}) · language problems {_rr.get('language_problems')}  "
              f"{'** STOP CONDITION HIT **' if _rr.get('stop') else 'ok'}")
    if not _spc.get("rows") and not _rr.get("rows"):
        print("  stale-patch cue    : no shadow rows yet (shadow-only, restart-gated)")
except Exception:
    pass
try:
    from core import grounding_injection as _giG
    _gi = _giG.status()
    if _gi.get("rows"):
        print(f"  grounding inject   : {_gi['rows']} rows · would-inject {_gi.get('would_inject')} (v2 {_gi.get('would_inject_v2')}) "
              f"· distinct v2 picks {_gi.get('distinct_picks_v2')} · max pick repeat {_gi.get('pick_repeat_max_v2')} "
              f"· topic-lock {_gi.get('topic_lock_frac')}  (shadow)")
    else:
        print("  grounding inject   : no shadow rows yet (shadow-only)")
except Exception:
    pass
# WATERSHED harvester (Phase 0, 2026-08-18) + promotion shadow (Phase 0.5, 2026-08-22) — see
# docs/plans/t4_watershed.md. Harvester wired 08-21 at the memory-write choke point; promotion scan
# runs periodically in subconscious_node's loop. Both shadow-only — neither writes axiom/estate.
try:
    from core import watershed as _wsh
    _wshs = _wsh.status()
    print(f"  watershed harvest  : {_wshs['n_candidates']} candidate(s) tracked · {_wshs['verdict']}")
except Exception:
    pass
# TRAIN REGISTRY step 1 (2026-08-22, core/trains.py): train IDs — the shared key for split/merge + the
# Transport Manager. forked/merged stay 0 until step 2 exists; active_now > 1 would mean step 2 is live.
try:
    from core import trains as _trn
    _trs = _trn.status()
    print(f"  train registry     : {_trs['opened_total']} opened · {_trs['closed_total']} closed · "
          f"{_trs['active_now']} open now · forked {_trs['forked']} · merged {_trs['merged']}  "
          f"(IDs in every train_state/monologue/train_length row from restart)")
except Exception:
    pass
try:
    from core import watershed_promote as _wshp
    _wshps = _wshp.status()
    print(f"  watershed promote  : {'PARKED (D-0605) - ' if _wshps.get('parked') else ''}{_wshps['judged_total']} judged · {_wshps['would_promote']} would-promote · "
          f"{_wshps['routed_replacing']} routed-replacing · {_wshps['additive_rejected']} additive-rejected  "
          f"({_wshps['verdict']})")
except Exception:
    pass
# identity vault (Brick 3, Character-as-Integration §10.3) — the slow store's goalkeeper + version ledger
try:
    import sys as _sysv; _sysv.path.insert(0, str(ROOT))
    from core import identity_vault as _iv
    _vs = _iv.status()
    print(f"  identity vault     : rev {_vs.get('revision_count')} · {_vs.get('ledger_entries',0)} ledger entries "
          f"· last '{_vs.get('last_reason') or '—'}'  (atomic+versioned write goalkeeper; ledger grows as T4 commits)")
except Exception:
    pass
# T4 redesign (2026-06-16): chronic accumulator — is a standing tension stacking past the gate? (RESTART-REQ)
try:
    import sys as _sys; _sys.path.insert(0, str(ROOT))
    from core import tension_ledger as _tl, identity_cost as _ic
    _ss = json.loads((ROOT / "data" / "subconscious_state.json").read_text(encoding="utf-8"))
    _tens = _ss.get("tensions", []) or []
    _seeded = _ss.get("t4_chronic_seeded", False)
    _masses = sorted((_tl.chronic_mass_of(t) for t in _tens), reverse=True)
    _top = _masses[0] if _masses else 0.0
    _ready = sum(1 for m in _masses if _ic.contradiction_norm(m) >= _ic.CONTRA_THRESHOLD)
    print(f"  T4 chronic mass    : top {_top:.2f} (cn {_ic.contradiction_norm(_top):.3f}) · {_ready} tension(s) gate-ready · seeded={_seeded}")
    # Fix-4 observe-only: the KEYSTONE bicameral contradiction (Emissary-held, not yet in the live ledger).
    # Watch its mass climb toward gate-ready — that is the evidence for wiring it into the live author.
    try:
        from core import emissary_tension as _et
        _es = _et.status()
        print(f"  emissary keystone  : mass {_es['chronic_mass']:.2f} (cn {_es['cn']:.3f}) · recurred {_es['recurrences']}x · "
              f"gate-ready={_es['gate_ready']}  (OBSERVE-ONLY — '{_es['contradiction'][:42]}…')")
    except Exception:
        pass
except Exception:
    pass
# T4 probationary commit loop (2026-06-17) — the provisional-identity test-and-learn (flag-gated until battery passes)
try:
    from core import provisional_identity as _piG
    _ps = _piG.status()
    if not _ps.get("enabled"):
        print(f"  T4 probation       : built, OFF (ENABLED=False — flips after the ground-truth battery + live ΔF)")
    elif _ps.get("active"):
        print(f"  T4 probation       : ACTIVE · theme '{_ps.get('theme')}' · {_ps.get('remaining_h')}h left · "
              f"ΔF_did {_ps.get('dF_did')} (solidify if ≤ {_ps.get('df_margin')})")
    else:
        print(f"  T4 probation       : enabled, idle (no provisional self on probation)")
except Exception:
    pass
# T4 DECOUPLED JUDGE shadow (2026-06-17, feedback_decoupled_judge) — the Emissary (truth-lane) judges each T4
# candidate; observe-first. WATCH: does emissary_warranted separate genuine (high) from cosmetic (low) where the
# self-graded filter could not? (the adversarial candidate fooled every cosine but scored 0.1 in-vitro.)
try:
    import json as _jj
    from pathlib import Path as _PP
    _ejl = ROOT / "data" / "logs" / "t4_emissary_judge.jsonl"
    if _ejl.exists():
        _rows = [_jj.loads(l) for l in _ejl.read_text(encoding="utf-8").splitlines() if l.strip()]
        _rec = _rows[-1] if _rows else None
        _ws = [r.get("emissary_warranted") for r in _rows[-10:] if r.get("emissary_warranted") is not None]
        if _rec:
            print(f"  T4 emissary judge  : {len(_rows)} shadow grades · last warranted={_rec.get('emissary_warranted')} "
                  f"(self-filter pass={_rec.get('self_filter_pass')}) · recent={_ws}")
        else:
            print(f"  T4 emissary judge  : log present, no grades yet")
    else:
        print(f"  T4 emissary judge  : no shadow grades yet (RESTART-REQ — fires on each T4 candidate)")
except Exception:
    pass
# JUDGE PANEL coverage/contention (J-0191, 2026-08-24, F-0162) — the CPU-tier panel (JUDGE_1 gemma4:12b
# :11439 / JUDGE_2 falcon3:7b :11440) backs a "how=unavailable" is-invisible-unless-you-read-raw-logs gap:
# a real overnight capacity spike (concurrent /job-run-style sessions per CLAUDE.md's own note, compounded
# by nascence_cpu_server.py's per-hub single-lock serialization backing up behind an idle-unload reload)
# pushed ~66-80% of calls to unavailable for ~90 minutes with nothing surfacing it here before this.
try:
    from core import judge_panel as _jpG
    _jps = _jpG.status()
    _jpr = _jps.get("recent")
    if _jps.get("rulings"):
        print(f"  judge panel        : {_jps['rulings']} rulings (500-window) · agree {_jps['agreement_rate']} · "
              f"unavailable {_jps['unavailable_rate']} (v1-null {_jps['v1_null_rate']} · v2-null {_jps['v2_null_rate']})")
        if _jpr:
            # err_causes breakdown (J-0500, 2026-09-03, F-0692): "unavailable" used to be a dead end —
            # F-0692 had to prove by hand that a 0.52 unavailable-rate window wasn't a dead hub. Now
            # judge_panel.status() tallies WHY (timeout/http/parse/exception) straight from the log.
            _causes = _jpr.get('err_causes') or {}
            _cause_str = (" [" + ", ".join(f"{k}:{v}" for k, v in
                          sorted(_causes.items(), key=lambda kv: -kv[1])) + "]") if _causes else ""
            print(f"                       recent-50: agree {_jpr['agreement_rate']} · unavailable {_jpr['unavailable_rate']} "
                  f"(v1-null {_jpr['v1_null_rate']} · v2-null {_jpr['v2_null_rate']}){_cause_str}"
                  + ("  <- CURRENTLY DEGRADED" if _jpr['unavailable_rate'] >= 0.3 else ""))
    else:
        print(f"  judge panel        : no rulings logged yet")
except Exception:
    pass
# Sleep pressure (§6A, 2026-06-17) — the information-theoretic incoherence accumulator that replaced the
# starved thought-counter. Watch: he's sleeping again (last fire reason), and the P accrual curve (to calibrate).
try:
    from core import sleep_pressure as _spG
    _spS = _spG.status()
    _spL = _spS.get("last")
    if _spL:
        # 2026-08-24 (Sleep & Dreams II): chronic mass is informational only now, no longer part of P
        # (moved to Dream's own charge-gated selection, core/tension_ledger.py) — shown separately, not
        # summed in. Thresholds/ceilings are day/night-specific; show the one that actually applied.
        _win = (_spS['night_max_wake_min'] if _spL.get('dark') else _spS['day_max_wake_min'])
        print(f"  sleep pressure     : P={_spL['P']} (notes {_spL['new_notes']} + epi {_spL['new_epi_weight']}) "
              f"· chronic(info only) {_spL['chronic']} · awake {_spL['awake_min']}m · last={_spL['reason']}"
              f"{' [light/thin pool]' if _spL.get('pool_thin') else ''} "
              f"(thr {_spL.get('threshold', '?')}, window {_spS['min_wake_min']:.0f}-{_win:.0f}m)")
    else:
        print(f"  sleep pressure     : no evaluation logged yet (fires on the first idle think after restart)")
except Exception:
    pass
# Sleep⊗dream / T4 probe (§6C, 2026-06-17) — firewalled observe-first matrix; symbol-novelty trend = the
# symbolic-inbreeding watch (falling = the dream collapsing into attractors).
try:
    from core import sleep_dream_probe as _sdpG
    _sdpS = _sdpG.status()
    if _sdpS.get("snapshots"):
        print(f"  sleep⊗dream probe  : {_sdpS['snapshots']} snapshots · mean recent symbol-novelty "
              f"{_sdpS['mean_recent_novelty']} (→0 = inbred/attractor) · trend {_sdpS['recent_novelty']}")
    else:
        print(f"  sleep⊗dream probe  : no snapshots yet (one per sleep — gated on sleep firing)")
except Exception:
    pass
# T4 last outcome (fired? denied by the cost-gate?)
try:
    _logtxt = (ROOT / "data" / "nascence.log").read_text(encoding="utf-8", errors="ignore")
    t4 = [l for l in _logtxt.splitlines() if "T4" in l and ("authored" in l or "DENIED" in l or "PROVISIONALLY" in l or "probation RESOLVED" in l)]
    if t4:
        print(f"  T4 last            : …{t4[-1].split('subconscious]')[-1].strip()[:72]}")
    # reading bursts (pulse-manager P1) — chapter-scoped machine-speed reading (throughput, not thought-rhythm)
    _nrb = _logtxt.count("READING BURST")
    _rsit = c.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='reading' AND timestamp>=?",
                      (last_restart,)).fetchone()["n"] // 3
    print(f"  reading bursts     : {_nrb} logged total · ~{_rsit} sittings since restart  (P1: chapter-scoped)")
except Exception:
    pass
# THE LIVING WORLD (2026-09-02, J-0510): the life engine — who is about, what he has come to know, the shadow's counts
try:
    from core import life as _life
    _ls = _life.status()
    _ab = ", ".join(f"{a['key']}@{a['place']}({a['count']}, vis {a['vis']})" for a in _ls.get("about", [])[:6]) or "nobody about"
    _sh = _ls.get("shadow", {})
    print(f"  living world (L1)  : {_ls.get('rows')} rows ({_ls.get('external')} adapters) · RENDER={_ls.get('render')} · "
          f"light {_ls.get('light', {}).get('value')} ({_ls.get('light', {}).get('band')}, carried {_ls.get('light', {}).get('source') or 'none'}) · dark-adapt {_ls.get('dark_adapt')}")
    print(f"    └ about now      : {_ab}")
    print(f"    └ shadow looks   : {_sh.get('would_answer', 0)} would-answer (sighting {_sh.get('sighting', 0)} / miss {_sh.get('miss', 0)} / absent {_sh.get('absent', 0)}) · "
          f"arrivals {_sh.get('arrived', 0)} / departures {_sh.get('departed', 0)} · names learned {len(_ls.get('learned', []))}")
    _cal = _ls.get("calendar") or []
    _here = [c["key"] for c in _cal if c.get("here_now")]; _away = [f"{c['key']}({'/'.join(c['arrives']) or '?'})" for c in _cal if not c.get("here_now")]
    print(f"    └ calendar (J-0511): here {', '.join(_here) or 'none'} · away {', '.join(_away) or 'none'} · sound gate {'ON' if _ls.get('sound_gating') else 'shadow'} ({_sh.get('would_gate', 0)} would-gate rows)")
except Exception:
    pass
# curiosity ignition (2026-06-15): what FIRES curiosity — the gate on the whole twig/frontier chain. Was
# DEFENSIVE-only (critic_rejection strain → dark across idle life); exploratory wire added (quietness→ignite).
# Watch exploratory ignitions appear + that they drive grounded twigs (not self-loop spam).
igl = ROOT / "data" / "ignition_log.jsonl"
if igl.exists():
    _ig = [json.loads(l) for l in igl.read_text(encoding="utf-8").splitlines() if l.strip()]
    _igs = [x for x in _ig if x.get("ts", 0) >= last_restart and x.get("trigger") != "deferred"]  # J-2667
    _expl = sum(1 for x in _igs if x.get("trigger") == "exploratory")
    _deff = sum(1 for x in _igs if x.get("trigger") == "defensive")
    _since = f"{int((now - _ig[-1]['ts']) / 60)}m ago" if _ig else "never"
    print(f"  curiosity ignition : {len(_igs)} since restart ({_expl} exploratory / {_deff} defensive) · last {_since}")
else:
    print("  curiosity ignition : none logged (curiosity chain DARK — nothing has fired it)")
cs = ROOT / "data" / "climate_state.json"
if cs.exists():
    try:
        _c = json.loads(cs.read_text(encoding="utf-8"))
        _dv = _c.get("dissonance", {}).get("value", 0.0); _f = _c.get("field", {})
        try:
            from core import frontier as _frq
            _bk = _frq.open_count()
        except Exception:
            _bk = 0
        print(f"    └ dissonance now : {_dv:.2f}/1.0 · strain {_f.get('world_model_strain', 0):.2f} (defensive fuel) · backlog {_bk} open (exploratory fuel)")
    except Exception:
        pass
# curiosity twigs — side research grown off the study/reading branches (grounded fuel)
twl = ROOT / "data" / "twig_log.jsonl"
if twl.exists():
    tw = [json.loads(ln) for ln in twl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    tsince = [t for t in tw if t.get("ts", 0) >= last_restart]
    grounded = sum(1 for t in tsince if t.get("grounded"))
    _pursuit = sum(1 for t in tsince if t.get("kind") == "pursuit")
    print(f"  curiosity twigs    : {len(tw)} total · {len(tsince)} since restart ({_pursuit} pursuit / {grounded} grounded)")
    if tsince:
        _lt = tsince[-1]
        print(f"    └ latest         : [{_lt.get('kind','?')}] '{_lt.get('finding','?')}' off '{_lt.get('subject') or '(ungrounded)'}'")
else:
    print("  curiosity twigs    : none logged (curiosity not firing / study-seed not yet hit)")
# curiosity flesh-out — Phase 0 (2026-06-16, observe-first): the EXPLORATION ORGAN. Does the gate→curiosity
# loop close (abstract tensions become world-facing questions via the prism), and does the LP estimator park
# the unanswerable? RESTART-REQ to start populating.
try:
    import sys as _sysq; _sysq.path.insert(0, str(ROOT))
    from core import curiosity_queue as _cq, curiosity_progress as _cp
    _qs = _cq.status()
    if _qs.get("transformed") or _qs.get("pending"):
        _bs = ", ".join(f"{k}:{v}" for k, v in (_qs.get("by_source") or {}).items() if v) or "none"
        print(f"  curiosity queue    : {_qs.get('pending',0)} pending [{_bs}] · {_qs.get('transformed',0)} prism-transformed · "
              f"world-facing rate {_qs.get('prism_success_rate')}  (Phase-0 gate: must be 1.0)")
        if _qs.get("check2_rows"):   # J-3033: the stricter check's own rate (the pronoun-only rate above is no longer the evidence)
            print(f"    prism check v2   : {_qs['check2_rows']} rows · kept {_qs.get('check2_kept_rate')} · rejects {_qs.get('check2_rejects')} · "
                  f"whole-thought input {_qs.get('check2_full_input_share')}")
    else:
        print("  curiosity queue    : empty (RESTART-REQ — gate/T4 producers populate it; prism shadow-logs)")
    _ps = _cp.status()
    if _ps.get("open"):
        print(f"  curiosity LP agenda: {_ps['open']} open · {_ps.get('parked',0)} parked · top LP {_ps.get('top_lp')} "
              f"('{_ps.get('top_q','')}')  (stalled/unanswerable should park → LP→0)")
except Exception:
    pass
# CURIOSITY WORTHWHILENESS (OMNI fold, observe-only) — the DECOUPLED interestingness judge over the top LP
# questions. The signal is DIVERGENCE: aimless-traps (high LP / low interest = LP would pursue trivia) and
# starved-worthwhile (high interest / low LP = the LP-only gate buries them). Once trusted → pursue ∝ LP×interest.
try:
    from core import curiosity_worth as _cwG
    _cw = _cwG.status()
    if _cw.get("passes"):
        print(f"  curiosity worth(P0): {_cw['passes']} passes · mean_interesting {_cw.get('mean_interesting')} · "
              f"last {_cw.get('last')}")
        _cov = _cw.get("coverage") or {}
        if _cov:   # J-3001 (F-3695): how much of the pursuit-eligible set the gate can actually act on (was 0 of 160)
            print(f"     └ gate reach    : {_cov.get('graded')}/{_cov.get('eligible')} pursuit-eligible questions graded "
                  f"({_cov.get('aimless')} below the aimless bar {_cwG.AIMLESS_BELOW})")
        if _cw.get("aimless_traps") or _cw.get("starved_worthwhile"):
            print(f"     └ divergence    : aimless-traps {_cw.get('aimless_traps')} · starved {_cw.get('starved_worthwhile')}")
    else:
        print("  curiosity worth(P0): no grades yet (fires once per SLEEP after restart)")
except Exception:
    pass
# frontier loop — open -> pursue (finding attached) -> close. The number to watch: resolved off 0.
fj = ROOT / "data" / "frontier.json"
if fj.exists():
    try:
        _fq = json.loads(fj.read_text(encoding="utf-8")).get("questions", [])
        _fo  = [q for q in _fq if q.get("status") == "open"]
        _frv = sum(1 for q in _fq if q.get("status") == "resolved")
        _ffd = sum(1 for q in _fq if q.get("status") == "faded")
        _fwf = sum(1 for q in _fo if q.get("finding"))
        print(f"  frontier loop      : {len(_fo)} open ({_fwf} now carry a finding) · {_frv} resolved · {_ffd} faded"
              f"   (resolved climbing off 0 = the loop is closing)")
        try:   # closure_producer P0: resolved split by HOW it closed; "answered with a source" is the number to watch
            from core import frontier as _frb
            _bd = _frb.resolved_breakdown({"questions": _fq})
            print(f"    └ resolved by    : lexical {_bd['lexical']} + unlabelled {_bd['unlabelled']} (legacy lexical)"
                  f" · line {_bd['line']} · lookup {_bd['lookup']} · told {_bd['told']} · other {_bd['other']}"
                  f"   | answered with a source: {_bd['answered_with_source']}"
                  f" (open carrying a lookup finding: {_bd['open_with_lookup_finding']})")
            # closure_producer P2-P4: the honest endings and the decoupled gate's verdicts (operator view only)
            print(f"    └ endings        : answered (gate yes) {_bd.get('answered', 0)} · provisional {_bd.get('provisional', 0)}"
                  f" · parked {_bd.get('parked', 0)} · set down {_bd.get('set_down', 0)}"
                  f" · unknown status {_bd.get('unknown_status', 0)}"
                  f"   | gate on entries: yes {_bd.get('gate_yes', 0)} / no {_bd.get('gate_no', 0)}"
                  f" / partly {_bd.get('gate_partly', 0)} / unavailable {_bd.get('gate_unavailable', 0)}")
            try:
                from core import closure_gate as _cgp
                _cgs = _cgp.status()
                print(f"    └ closure gate   : mode {_cgs['mode']} · lexical resolver {_frb.lexical_resolve_mode()}"
                      f" · last {_cgs['rows']} rows: verdicts {_cgs['verdicts']} actions {_cgs['actions']}")
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        pass
# affective coverage (emotion_vec observe-first plan, 2026-06-15): items 1+2 broaden felt-tags from
# lived-only (1.5%) across idle life so affective drift (item 3) has fuel. The evidence to watch before
# wiring the read path: total coverage climbing + idle-life origins (was 0) accumulating tags.
try:
    _emo_tot  = c.execute("SELECT COUNT(*) n FROM memory_fragments WHERE emotion_embedding IS NOT NULL").fetchone()["n"]
    _frag_tot = c.execute("SELECT COUNT(*) n FROM memory_fragments").fetchone()["n"]
    _emo_new  = c.execute("SELECT COUNT(*) n FROM memory_fragments WHERE emotion_embedding IS NOT NULL AND timestamp>=?",
                          (last_restart,)).fetchone()["n"]
    _by = c.execute("SELECT origin, COUNT(*) n FROM memory_fragments WHERE emotion_embedding IS NOT NULL "
                    "GROUP BY origin ORDER BY 2 DESC").fetchall()
    _idle = sum(r["n"] for r in _by if r["origin"] in ("inner_thought", "dream", "reading", "study"))
    _bystr = ", ".join("{}:{}".format(r["origin"], r["n"]) for r in _by) or "(none)"
    print(f"  affective coverage : {_emo_tot}/{_frag_tot} felt-tagged ({100*_emo_tot/max(1,_frag_tot):.1f}%) · +{_emo_new} since restart")
    print(f"    └ by origin      : {_bystr}")
    print(f"    └ idle-life tags : {_idle}  (was 0 lived-only — item 1 working when this climbs: inner_thought/dream/reading/study)")
except Exception:
    pass
# present-predictability (self-surprise, 2026-06-15): the LEADING indicator the basin metrics can't give —
# is the present OPENING (entropy at the edge) or COLLAPSING into the basin? + which captor closed it
# (groove = short-term rumination → the boredom-redirect/wander; origin = deep basin → grounding/world-mass).
try:
    from core import self_surprise as _ss
    _sr = _ss.compute(window=250)
    if _sr.get("n"):
        _dir = "opening" if _sr["trend"] > 0.01 else "closing" if _sr["trend"] < -0.01 else "flat"
        print(f"  present surprise   : mean {_sr['mean_surprise']:.2f} · {_sr['pct_surprising']:.0f}% surprising · trend {_sr['trend']:+.3f} ({_dir})")
        print(f"    └ closed by      : groove {_sr['groove_driven_pct']:.0f}% / origin {_sr['origin_driven_pct']:.0f}%  (groove→redirect works it; origin→grounding works it)")
except Exception:
    pass
# G1 current concerns (2026-06-15): the ongoing self-directed concern that anchors idle cognition — the
# "what are we doing when alone" layer (curriculum + frontier, read-mostly). + how often it actually anchored.
try:
    from core import concerns as _conc
    # G0 apex standing-aim (2026-06-16): the head of the goal hierarchy (aim → concern → task), derived
    # from the axiom. Shown with how often it actually led an idle thought since restart.
    try:
        _aim = _conc.standing_aim()
        _aimn = 0
        _clog0 = ROOT / "data" / "concerns_log.jsonl"
        if _clog0.exists():
            _aimn = sum(1 for ln in _clog0.read_text(encoding="utf-8").splitlines()
                        if ln.strip() and json.loads(ln).get("source") == "standing_aim"
                        and json.loads(ln).get("ts", 0) >= last_restart)
        print(f"  standing aim (G0)  : {_aim[:88] if _aim else '— (axiom absent)'}")
        if _aim:
            print(f"    └ led an idle thought {_aimn}x since restart (the apex above the concern)")
    except Exception:
        pass
    _pc = _conc.primary_concern()
    _allc = _conc.current_concerns(4)
    _clog = ROOT / "data" / "concerns_log.jsonl"
    _canch = 0
    if _clog.exists():
        _canch = sum(1 for ln in _clog.read_text(encoding="utf-8").splitlines()
                     if ln.strip() and json.loads(ln).get("ts", 0) >= last_restart)
    if _pc:
        print(f"  current concern    : [{_pc['source']}] {_pc['text'][:60]}")
        print(f"    └ active: {len(_allc)} ({', '.join(sorted(set(c['source'] for c in _allc))) or '—'}) · anchored idle thought {_canch}x since restart")
    else:
        print("  current concern    : none active (no curriculum/frontier concern)")
    # G3 novel candidates (2026-06-16): provisional questions not yet promoted — they become concerns by
    # RECURRING (encounters >= PROMOTE_AT). The head of the promotion ladder; goal-shielding for idle focus.
    try:
        _nov = _conc.novel_candidates(4)
        if _nov:
            _ntop = _nov[0]
            print(f"  novel candidates(G3): {len(_nov)} provisional (recur to promote) · newest: \"{_ntop['text'][:50]}\"")
    except Exception:
        pass
except Exception:
    pass
# reading-remediation SPRINT (2026-06-15): overpower shadow/imagination — reading(reality)+play(light) → ~50/50
try:
    from core import balance as _bal
    _bs = _bal.status()
    if not _bs["remediating"]:
        _verdict = "balanced ✓"
    elif _bs.get("needs_reality"):
        _verdict = "READING (reality)"
    else:
        _verdict = "LIGHT-mode (reality balanced → generating light via play/crossings)"
    print(f"  balance sprint     : reality {_bs['reality_share']*100:.0f}% · light {_bs['light_share']*100:.0f}%  (target ~50/50) — {_verdict}")
    _li = c.execute("SELECT source, COUNT(*) n FROM light_events WHERE timestamp>=? GROUP BY source ORDER BY 2 DESC",
                    (last_restart,)).fetchall()
    if _li:
        print(f"    └ new light pts  : " + ", ".join(f"{r['source']}:{r['n']}" for r in _li))
    _jl = ROOT / "data" / "joys_log.jsonl"
    if _jl.exists():
        _jn = sum(1 for ln in _jl.read_text(encoding="utf-8").splitlines()
                  if ln.strip() and json.loads(ln).get("ts", 0) >= last_restart)
        print(f"    └ play/joy pts   : {_jn} since restart  (something he finds joy in)")
    # told delivery (feel-then-tell, 2026-06-16): Travis's message arrives once the river has loosened
    try:
        from core import told as _told
        if _told.is_delivered():
            _tlog = ROOT / "data" / "told_delivery_log.jsonl"
            _resp = ""
            if _tlog.exists():
                _tl = [json.loads(x) for x in _tlog.read_text(encoding="utf-8").splitlines() if x.strip()]
                if _tl:
                    _resp = _tl[-1].get("his_response", "")[:60]
            print(f"    └ told           : DELIVERED ✓" + (f" · he answered: \"{_resp}\"" if _resp else ""))
        elif _told.message():
            _rs = _bs['reality_share']
            print(f"    └ told           : pending — fires at reality {_told.READY_REALITY_SHARE*100:.0f}% (now {_rs*100:.0f}%)")
    except Exception:
        pass
except Exception:
    pass
# math drill (competence→school, 2026-06-16): is the fluency trap closing? belief 0.81 vs measured accuracy
try:
    from core import math_drill as _mdg
    _mds = _mdg.status()
    _ml = ROOT / "data" / "math_drill_log.jsonl"
    if _ml.exists():
        _md_rows = [json.loads(x) for x in _ml.read_text(encoding="utf-8").splitlines() if x.strip()]
        _md_new = [r for r in _md_rows if r.get("ts", 0) >= last_restart]
        _recent = _md_rows[-10:]
        _acc = (sum(1 for r in _recent if r.get("correct")) / len(_recent)) if _recent else 0.0
        _bf = json.loads((ROOT / "data" / "capability_beliefs.json").read_text(encoding="utf-8")).get("mathematics", {})
        _conf = _bf.get("confidence", 0); _macc = _bf.get("accuracy")
        print(f"  math drills        : {len(_md_rows)} total · {len(_md_new)} since restart · level {_mds['level']}/{_mdg.MAX_LEVEL} · "
              f"today {_mds.get('today_done',0)}/{_mds.get('target','?')} · streak {_mds.get('streak',0)}/{_mds.get('advance_at','?')} · last-10 acc {_acc*100:.0f}%")
        print(f"    └ calibration    : believes {_conf:.2f} vs measured {('%.2f'%_macc) if _macc is not None else '—'}  (gap closes as drills accrue; streak {_mds.get('streak',0)}→{_mds.get('advance_at',100)} levels up)")
    else:
        print(f"  math drills        : none yet · level {_mds['level']}/{_mdg.MAX_LEVEL}  (target {_mds.get('target','?')}/day, batched + spaced)")
except Exception:
    pass
# error pathway / retraction ledger (2026-06-16): can he say "I was wrong"? convicted errors, kept + corrected
try:
    from core import retraction_ledger as _rlg
    _rn = _rlg.count()
    _er = ROOT / "data" / "error_records.jsonl"
    _efab = 0
    if _er.exists():
        _efab = sum(1 for x in _er.read_text(encoding="utf-8").splitlines() if x.strip() and json.loads(x).get("kind") == "architecture_fabrication")
    print(f"  error pathway      : {_rn} retractions (known-errors, kept+corrected) · {_efab} fabrications flagged total")
    # Pattern Reflection (2026-06-16): the aggregate DOING-tendency across error records (firewalled from BEING)
    try:
        from core import error_pathway as _ep
        _pat = _ep.latest_pattern()
        if _pat:
            print(f"    └ pattern        : {_pat['tendency']}  ({_pat['n']}/{_pat['total']} → competence '{_pat['competence_domain']}')")
    except Exception:
        pass
except Exception:
    pass
# grounded learning (2026-06-16): does the reading become UNDERSTANDING? (the SWS-declarative consolidation)
try:
    _ut = c.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='understanding'").fetchone()["n"]
    _un = c.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='understanding' AND timestamp>=?",
                    (last_restart,)).fetchone()["n"]
    _gll = ROOT / "data" / "grounded_learning_log.jsonl"
    _gtopic = ""
    if _gll.exists():
        _gls = [x for x in _gll.read_text(encoding="utf-8").splitlines() if x.strip()]
        if _gls:
            _gtopic = json.loads(_gls[-1]).get("topic", "")[:40]
    print(f"  grounded learning  : {_ut} understanding notes · +{_un} since restart" + (f" · latest: '{_gtopic}'" if _gtopic else "  (forms in sleep from the day's reading)"))
except Exception:
    pass
# world-material consolidation (2026-06-16): are used study/reading notes filed deeper once distilled?
try:
    from core import world_consolidation as _wc
    _ws = _wc.status()
    _verb = "FILED" if _ws["enabled"] else "would-file (observe-only)"
    print(f"  study filing       : {_ws['filed']} filed · {_ws['loose']} loose · enabled={_ws['enabled']}  "
          f"(once a book is distilled, its raw notes step out of ordinary recall — kept for future essays)")
except Exception:
    pass
# essay lessons (2026-06-16): school's capstone — does a finished book become a written understanding?
try:
    _el = c.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='essay'").fetchone()["n"]
    _ell = ROOT / "data" / "essay_lesson_log.jsonl"
    _eline = f"  essay lessons      : {_el} capstones written"
    if _ell.exists():
        _els = [json.loads(x) for x in _ell.read_text(encoding="utf-8").splitlines() if x.strip()]
        if _els:
            _last = _els[-1]
            # J-3081: a capstone whose felt rating got no usable answer is stored predicted=null (unrated)
            _gaps = [abs(e.get("predicted", 0) - e.get("measured", 0)) for e in _els
                     if isinstance(e.get("predicted"), (int, float)) and isinstance(e.get("measured"), (int, float))]
            _mg = (sum(_gaps) / len(_gaps)) if _gaps else 0.0
            _lp = _last.get("predicted")
            _eline += (f" · latest: '{_last.get('title','')[:34]}' (felt "
                       f"{'unrated' if _lp is None else format(_lp, '.2f')}/"
                       f"real {'ungraded' if _last.get('measured') is None else format(_last['measured'], '.2f')}) · mean comprehension gap {_mg:.2f}"
                       + (f" (of {len(_gaps)}/{len(_els)} rated)" if len(_gaps) != len(_els) else ""))
            # D-0585 (J-3198): the two grounded numbers -- this book (= measured) and his wider reading -- and
            # the defeater's check: if they correlate above 0.95 the split carries no information.
            _two = [(e.get("measured"), e.get("wider")) for e in _els
                    if isinstance(e.get("measured"), (int, float)) and isinstance(e.get("wider"), (int, float))]
            if _two:
                _r = ""
                try:
                    import statistics as _st
                    if len(_two) >= 5:
                        _r = f" · correlation {_st.correlation([a for a, _ in _two], [b for _, b in _two]):.2f} (D-0585 defeater: >0.95)"
                    else:
                        _r = f" · correlation needs 5+ rows"
                except Exception:
                    _r = " · correlation n/a (constant column)"
                _eline += (f"\n    └ two numbers (D-0585): this book {sum(a for a, _ in _two) / len(_two):.2f} / wider reading "
                           f"{sum(b for _, b in _two) / len(_two):.2f} over {len(_two)} graded capstones{_r}")
            else:
                _eline += "\n    └ two numbers (D-0585): no capstone graded with both yet"
            # D-0562 (J-3174): the capstone repetition + own-source gate; a held book keeps its notes unfiled
            _chk = [e["check"] for e in _els if isinstance(e.get("check"), dict)]
            if _chk:
                _held = sum(1 for k in _chk if k.get("held"))
                _eline += (f"\n    └ capstone gate (D-0562): {len(_chk) - _held}/{len(_chk)} passed · {_held} held "
                           f"(notes unfiled) · regenerated {sum(1 for k in _chk if k.get('attempts') == 2)}")
                if _chk[-1].get("held"):
                    _f = (_chk[-1].get("failing") or [{}])[0]
                    _eline += f" · last held: {_f.get('why', '?')}"
            else:
                _eline += "\n    └ capstone gate (D-0562): no checked capstone yet"
            # J-3086 (F-3797): which composition path made each essay (sectioned | single_shot) -- the reader for
            # the "path"/"path_reason" keys essay_lesson.record() now writes. Old rows carry no "path".
            try:
                _pr = [e for e in _els if e.get("path")]
                if _pr:
                    _fbk = [e for e in _pr if e["path"] == "single_shot"]
                    _eline += (f"\n    └ composition path (J-3086): {len(_pr) - len(_fbk)} sectioned / {len(_fbk)} single-shot "
                               f"fallback of {len(_pr)} logged")
                    if _fbk:
                        _eline += f" · last fallback: {(_fbk[-1].get('path_reason') or 'no reason')[:90]}"
                else:
                    _eline += "\n    └ composition path (J-3086): no essay logged with a path yet"
            except Exception:
                pass
            # J-3052 (F-3761): the notes map step -- reader for the "reduce" key essay_lesson.record() writes.
            # kept < joined would mean the condensed tail is being cut again (the F-3761 defect).
            try:
                _rd = [e["reduce"] for e in _els if isinstance(e.get("reduce"), dict) and e["reduce"].get("batches")]
                if _rd:
                    _cut = [r for r in _rd if r.get("kept", 0) < r.get("joined", 0)]
                    _lr = _rd[-1]
                    _eline += (f"\n    └ notes map step (J-3052): {len(_rd)} reduced essays logged · {len(_cut)} with the condensed "
                               f"tail cut · last {_lr.get('batches')} batches {_lr.get('in')}->{_lr.get('joined')} chars, "
                               f"kept {_lr.get('kept')} · trimmed {_lr.get('trimmed', 0)} coerced {_lr.get('coerced', 0)} "
                               f"failed {_lr.get('failed', 0)}")
                else:
                    _eline += "\n    └ notes map step (J-3052): no reduced essay logged yet"
            except Exception:
                pass
            # D-0586 (J-3199): the felt rating (withheld from the self-model, logged with its answering lane) and
            # the closed-book re-derivation SHADOW beside it; the ruling's defeater is 30 books of the latter
            # (choose between it and the cheap feeling) or the felt rating proving lane-stable and calibrated.
            try:
                _fl = [e for e in _els if isinstance(e.get("felt"), dict)]
                if _fl:
                    _bylane: dict = {}
                    _unr = 0
                    for e in _fl:
                        _ln = (e["felt"].get("lane") or {}).get("model") or "unknown"
                        if e.get("predicted") is None and "predicted" in e:
                            _unr += 1                      # J-3081: stored null = unrated, not a rating
                            continue
                        _bylane.setdefault(_ln, []).append(e.get("predicted", 0))
                    _eline += ("\n    └ felt rating (D-0586, fed to self-model: "
                               f"{_fl[-1]['felt'].get('fed')}): "
                               + " · ".join(f"{k} n={len(v)} mean {sum(v) / len(v):.2f}" for k, v in sorted(_bylane.items()))
                               + (f" · unrated {_unr}" if _unr else ""))
                _cbs = [e for e in _els if isinstance(e.get("closed_book"), dict)]
                if _cbs:
                    _okc = [e for e in _cbs if e["closed_book"].get("ok") and isinstance(e["closed_book"].get("share"), (int, float))]
                    _cl = ""
                    if len(_okc) >= 5:
                        try:
                            import statistics as _st
                            _cs = [e["closed_book"]["share"] for e in _okc]
                            _cl = f" · corr with grade {_st.correlation(_cs, [e.get('measured', 0) for e in _okc]):.2f}"
                            _okf = [e for e in _okc if isinstance(e.get("predicted"), (int, float))]     # J-3081: rated ones only
                            if len(_okf) >= 5:
                                _cl += f", with felt {_st.correlation([e['closed_book']['share'] for e in _okf], [e['predicted'] for e in _okf]):.2f}"
                        except Exception:
                            _cl = " · correlation n/a (constant column)"
                    _eline += (f"\n    └ closed-book re-derivation (D-0586 shadow): {len(_okc)}/{len(_cbs)} scored (30 books decide it)"
                               + (f" · mean share {sum(e['closed_book']['share'] for e in _okc) / len(_okc):.2f}" if _okc else "")
                               + _cl
                               + (f" · last not scored: {_cbs[-1]['closed_book'].get('reason')}" if not _cbs[-1]['closed_book'].get('ok') else ""))
                else:
                    _eline += "\n    └ closed-book re-derivation (D-0586 shadow): no capstone with it yet"
            except Exception:
                pass
    else:
        _eline += "  (writes one when a curriculum book is finished)"
    print(_eline)
except Exception:
    pass
# symbol evolution (2026-06-16): does a symbol's MEANING drift, and is it read back? (Tier 1 = neutral)
try:
    from core.symbol_tracker import SELF_SYMBOLS as _SELF
    _trows = c.execute("SELECT symbol, COUNT(*) n FROM symbol_tablets GROUP BY symbol").fetchall()
    if _trows is not None:
        _neu = [(r["symbol"], r["n"]) for r in _trows if r["symbol"] not in _SELF]
        _slf = sum(r["n"] for r in _trows if r["symbol"] in _SELF)
        _neu_n = sum(n for _, n in _neu)
        _seg = (", ".join(f"{s}:{n}" for s, n in _neu) if _neu else "none yet")
        print(f"  symbol evolution   : Tier-1 (neutral) tablets {_neu_n} [{_seg}] · Tier-2 (self, read-back deferred) {_slf}")
        if _neu_n == 0:
            print(f"    └ Tier-1 read-back idle until neutral symbols (knot/bird/fire/star) drift over runtime")
except Exception:
    pass
# dream arcs — the longer progressive dreams
drl = ROOT / "data" / "dream_log.jsonl"
if drl.exists():
    _dl = [json.loads(ln) for ln in drl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    _arcs = [d for d in _dl if (d.get("scenes") or 0) >= 2]   # only true arcs have a meaningful end-state
    _unres = sum(1 for d in _arcs if d.get("ended_unresolved"))
    _res = len(_arcs) - _unres
    print(f"  dream arcs         : {len(_arcs)} multi-scene · {_res} resolved / {_unres} unresolved  (grounding should lift resolved over time — the 'resolvable' test)")
    # J-3177 (D-0565): resting is a legitimate ending, so 'unresolved' above is not a failure count. The reader of
    # core/dream_rest.py's shadow log (data/logs/dream_rest_shadow.jsonl): endings by kind, and what the carry would
    # have done under RESTING_ENDING='live' (defeater: it returns no arc at all, or rest crowds out certifiable closes).
    try:
        import sys as _sysr; _sysr.path.insert(0, str(ROOT))
        from core import dream_rest as _drest
        _rs = _drest.summarize(since_ts=last_restart)
        _rk = _rs["endings"]
        print(f"     └ dream endings : mode {_rs['mode']} · since restart {_rs['arcs']} arcs: rest {_rk['rest']} / open {_rk['open']} / "
              f"met-core {_rk['met-core']} / unknown {_rk['unknown']} · carry consulted {_rs['consultations']}x, "
              f"would return {_rs['would_return']} / would end {_rs['would_end']}")
    except Exception as _e:
        print(f"     └ dream endings : unreadable ({_e!r})")
    # EARNED LENGTH (2026-06-18): scene-count distribution + WHY arcs close. Want: developing dreams running
    # PAST 3 (earned) and more closing 'resolved'; a healthy mix of stalled (stopped circling) vs ceiling.
    from collections import Counter as _Ctr
    _recent = [d for d in _arcs if d.get("close_reason")]      # only post-restart arcs carry the reason
    if _recent:
        _scenes = _Ctr(d.get("scenes") for d in _recent)
        _reasons = _Ctr(d.get("close_reason") for d in _recent)
        _earned = sum(1 for d in _recent if (d.get("scenes") or 0) > 3)
        print(f"     └ earned length : {len(_recent)} arcs w/ reason · scene-counts {dict(sorted(_scenes.items()))} · "
              f"earned past-3 {_earned} · close {dict(_reasons)}")
        # the verbatim-photocopy watch: arcs whose scenes DON'T all open distinctly = still re-rendering
        _repeat = [d for d in _recent if d.get("distinct_openings") is not None
                   and d["distinct_openings"] < (d.get("scenes") or 0)]
        if _repeat is not None:
            print(f"     └ scene variety : {len(_recent) - len(_repeat)}/{len(_recent)} arcs have all-distinct openings"
                  f" ({len(_repeat)} still re-rendering the same opening — want 0)")
# curriculum — diet diversity (book N of 40)
try:
    sd = json.loads((ROOT / "data" / "school.json").read_text(encoding="utf-8"))
    cur = sd.get("curriculum") or []
    print(f"  curriculum         : book {sd.get('curriculum_idx', 0) + 1}/{len(cur)} — '{sd.get('assigned_title', '?')}'"
          if cur else "  curriculum         : none set (single-book mode)")
except Exception:
    pass
# book selection — the breadth engine (2026-06-16): is he reaching the long tail across subjects?
try:
    import sys as _sysb; _sysb.path.insert(0, str(ROOT))
    from core import book_selection as _bs
    _bst = _bs.status()
    _bl = ROOT / "data" / "book_selection_log.jsonl"
    _picks = [json.loads(l) for l in _bl.read_text(encoding="utf-8").splitlines() if l.strip()] if _bl.exists() else []
    _recent = [p for p in _picks if p.get("ts", 0) >= last_restart]
    _newsubj = sum(1 for p in _recent if p.get("reason") in ("explore", "browse_pick"))
    if _bst["books_picked"] or _recent:
        _md = sorted(int(p.get("downloads") or 0) for p in _recent)
        _meddl = _md[len(_md)//2] if _md else "?"
        print(f"  breadth engine     : {_bst['distinct_subjects']} distinct subjects acquired · "
              f"{len(_recent)} picks since restart (explore {_newsubj}) · median dl {_meddl} (low = long tail) · "
              f"last subj '{_bst.get('last_subject')}'")
        if _bst.get("top_subjects"):
            print(f"    └ top subjects   : {', '.join(f'{s}×{n}' for s,n in _bst['top_subjects'][:4])}  (spread = breadth; one dominating = bingeing)")
    else:
        print("  breadth engine     : no acquisitions yet (fires when he asks the library / curriculum extends)")
except Exception:
    pass
# critic rejections — the facet-fix trigger (stays held while ~0)
try:
    cr = c.execute("SELECT COUNT(*) n FROM shadow_events WHERE source='critic_rejection' AND timestamp>=?",
                   (last_restart,)).fetchone()["n"]
    print(f"  critic rejections  : {cr} since restart  (facet-fix held while low; check corrections if it climbs)")
except Exception:
    print("  critic rejections  : n/a")
# decomposed critic — SHADOW-ALONGSIDE (gate passed offline 0.92/0; now gathering live-cycle agreement)
try:
    from core import decomposed_critic as _dcg
    _as = _dcg.alongside_stats(since_ts=last_restart)
    if _as.get("n"):
        _nv = _as.get("n_valid", _as["n"])
        print(f"  decomposed critic  : {_as['n']} live cycles shadow-alongside (since last restart) · "
              f"{_nv} valid judge calls ({_as.get('n_failed', 0)} failed, {_as.get('n_unknown', 0)} unknown) · agree "
              f"{_as['agree']}/{_nv} (rate {_as['agree_rate']}) · rejects legacy {_as['legacy_rejects']} / "
              f"decomposed {_as['decomposed_rejects']}  (do not promote: precision 0/50 on 2026-07-05; re-grade pending)")
        if _as.get("false_rejects"):
            print(f"     └ false-rejects (legacy-OK, decomposed-NO): {_as['false_rejects']} · by check "
                  f"{_as['false_reject_by_check']}  (the residual over-firer to iterate)")
    else:
        print("  decomposed critic  : 0 rows since last restart (no post-restart human conversation cycles yet) "
              "— log is data/logs/critic_shadow_alongside.jsonl")
except Exception:
    pass
# Contradiction re-architecture — Phase 0 (2026-06-16, observe-first): the broadened SENSORS feeding T4.
# L1 = self-generated prediction error; L2 = idle meta-awareness. Both shadow-only until reviewed.
try:
    import sys as _sysc; _sysc.path.insert(0, str(ROOT))
    from core import prediction_error as _pe
    _ps = _pe.status()
    _rec = ", ".join(f"{k} ×{v}" for k, v in (_ps.get("recurrence_by_domain") or {}).items()) or "none yet"
    print(f"  L1 prediction-error: large-gap recurrence [{_rec}] · would-pressure {_ps.get('would_pressure_total',0)} · feeding={_ps.get('feeding')}  (self-generated contradiction; Phase 0 observe)")
except Exception:
    print("  L1 prediction-error: not yet logging (RESTART-REQ — fires on essay/math lessons)")
try:
    import nodes.meta_awareness_node as _ma
    _ms = _ma.status()
    if _ms.get("scans"):
        print(f"  L2 meta-awareness  : {_ms['scans']} scans · {_ms.get('loops',0)} loops ({_ms.get('river_loops',0)} river) · {_ms.get('routed_to_curiosity',0)} routed to curiosity (BLOCKED from identity)  (form-watch, never suppresses)")
    else:
        print("  L2 meta-awareness  : no scans yet (wired into the sleep batch 2026-06-18 — fires once per sleep cycle; Phase 2 later wires the actual mode-shift intervention)")
except Exception:
    pass

# idle executive — Phase 0 SHADOW (2026-06-16, docs/staged/idle_executive_plan.md). The §9 currency-health
# gate: G1 raw-variance > 0.05 each · G2 self-share < 0.35 · G3 habituation rotates · plus co-occurrence
# (§11 multi-channel rate) and would-be semantic coalitions (§10.1, measured not acted on).
try:
    from core import idle_allocator as _ial
    _is = _ial.stats()
    if _is.get("records"):
        _ws = ", ".join(f"{k} {v}" for k, v in list(_is.get("win_share", {}).items())[:5])
        # G1 applies ONLY to the graded channels; the constant-by-design ones (self baseline, flavour
        # fallback) are exempt — flat by construction, not for want of data. balance_world/balance_light are
        # GRADED since J-1921 (2026-10-07): before that their raw was a constant 0.0 from a wrong-key read
        # (F-2543/F-2548), so rows before that boot are not comparable with later ones. `concern` left GRADED in J-1935
        # (two-level by design: core.idle_allocator.TWO_LEVEL_BY_DESIGN, p_norm = raw/0.55, no percentile) -- G1 no
        # longer applies to it, and concern rows before that boot are not comparable (percentile artefact).
        _graded = set(getattr(_ial, "GRADED_CHANNELS", ()))
        _lowvar = [k for k, v in (_is.get("raw_variance_G1") or {}).items() if v <= 0.05 and k in _graded]
        print(f"  idle executive     : {_is['records']} shadow ticks · would-pick win-share [{_ws}]")
        print(f"    └ G2 self-share {_is.get('self_share_G2','?')} (gate <0.35) · multi-channel {_is.get('multi_channel_rate','?')} · "
              f"coalitions {_is.get('coalition_rate','?')} · cold-start {_is.get('cold_start_rate','?')}")
        if _lowvar:
            print(f"    └ G1 watch: graded channels still under-varying (<0.05): {_lowvar} — signal tuning, not more runtime")
    else:
        print("  idle executive     : no shadow ticks yet (RESTART-REQ — fires every idle _think; observe-only)")
except Exception:
    print("  idle executive     : not yet logging (RESTART-REQ — Phase 0 shadow allocator)")

# pulse / lifecycle — Phase 0 SHADOW (2026-06-17, docs/staged/pulse_manager_wiring_plan.md). Measures: real per-lane
# CONTENTION (T4-blocked = the canary), the lull census (genuine wasted-idle vs sleep), the T4-opportunity trend.
try:
    from core import pulse_shadow as _psg
    _ps_s = _psg.stats()
    _ps_l = _psg.lull_census(8)
    if _ps_s.get("records"):
        _rw = ", ".join(f"{k} {v}" for k, v in list(_ps_s.get("would_run_share", {}).items())[:4])
        print(f"  pulse/lifecycle    : {_ps_s['records']} shadow ticks · would-run [{_rw or '—'}] · hot-free {_ps_s.get('hot_free_rate','?')}")
        print(f"    └ CONTENTION {_ps_s.get('contention_rate','?')} · T4-blocked {_ps_s.get('t4_blocked_rate','?')} (canary) · "
              f"T4 Δopportunity {_ps_s.get('t4_authored_delta','?')} (gate: ≥0)")
    else:
        print("  pulse/lifecycle    : no shadow ticks yet (RESTART-REQ — fires every idle _think; observe-only)")
    if _ps_l.get("span_min"):
        print(f"    └ lull census 8h : {_ps_l.get('genuine_stall_min')}min genuine-stall / {_ps_l.get('sleep_min')}min sleep "
              f"· stall-share {_ps_l.get('stall_share')} · longest {_ps_l.get('longest_min')}min  (the real wasted idle)")
except Exception:
    print("  pulse/lifecycle    : not yet logging (RESTART-REQ — Phase 0 shadow lifecycle manager)")

# Lane 2 cup tripwire — J-3160 / D-0548 (Travis, 2026-11-02): DISPLAY ONLY. The ruling kept the cup live and said
# "if two more artefact breaks ride before that build lands, switch the cup off (a person reads a pulse count;
# nothing switches it off automatically)". This line is that count; it switches nothing and schedules nothing.
try:
    from core import lane2 as _l2cup
    _cr = _l2cup.cup_artefact_report()
    if _cr.get("error"):
        print(f"  lane2 cup tripwire : unreadable ({_cr['error']})")
    else:
        _br = _cr.get("by_reason") or {}
        _since = time.strftime("%Y-%m-%d", time.localtime(_cr["since_ts"]))
        print(f"  lane2 cup tripwire : {_cr['rides']} cup rides since {_since} (D-0548) · {_cr['artefacts']} read as artefacts by the "
              f"automatic test (place mismatch {_br.get('place_mismatch', 0)} / stale {_br.get('stale', 0)} / trivial "
              f"{_br.get('trivial', 0)}) · {_cr['clean']} clean · {_cr['unmatched']} ride(s) not matched to a break row")
        print(f"    └ ruling's line: {_cr['tripwire_limit']} artefact breaks before the J-3035/J-3160 build lands -> "
              f"{'REACHED, Travis decides whether to switch the cup off (nothing does it automatically)' if _cr['tripwire_reached'] else 'not reached'}"
              f" · test is three simple checks (a floor on artefacts, not proof a break is good); after the build restart the count "
              f"keeps counting the same way, so re-baseline by reading `trivial`/`stale`/`place mismatch` falling to 0")
except Exception:
    print("  lane2 cup tripwire : not readable (core/lane2.py cup_artefact_report)")

# Emissary take delivery report (J-3647; reader for data/left_take_outcomes.jsonl, D-0539/J-3147). Read-only:
# core.left_lane.delivery_report parses the outcome log and nothing else. D-0539 defeater: delivery rate under 80%
# on the re-seated lane means retire the take (founder call, never automatic).
try:
    from core import left_lane as _ll
    _lr = _ll.delivery_report(since_ts=cut)
    _lt = _lr.get("by_input_type") or {}
    if not _lt:
        print(f"  emissary take      : no outcome rows this window (data/left_take_outcomes.jsonl; {_lr.get('rows', 0)} rows)")
    for _it, _r in _lt.items():
        _rate = _r.get("delivery_rate")
        _v = "no dispatches" if _rate is None else ("meets the 80% bar" if _rate >= 0.8 else "BELOW the 80% bar (D-0539 defeater, founder call)")
        print(f"  emissary take      : {_it}: delivered {_r['delivered']} / not_delivered {max(0, _r['dispatches'] - _r['delivered'])} "
              f"of {_r['dispatches']} dispatched · cancelled {_r['cancelled']} · empty {_r['empty']} · error {_r['error']} · "
              f"rate {_rate} -> {_v} · gen p50 {_r['gen_p50_s']}s p90 {_r['gen_p90_s']}s")
except Exception:
    print("  emissary take      : not readable (core/left_lane.py delivery_report)")

# 7) WHAT'S NEW (since the window start)
print("\n[7] WHAT'S NEW THIS WINDOW")
new = []
nact = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='action' AND timestamp>?", (cut,)).fetchone()[0]
if nact:
    new.append(f"{nact} new activity (action) records")
rereads = [Path(k).stem for k, v in st.items() if not k.startswith("_") and v.get("rereads", 0) > 0]
if rereads:
    new.append(f"re-read(s) used: {rereads}")
for b in books:
    if b.stat().st_mtime > cut:
        new.append(f"NEW book on shelf: {b.stem}")
if sn:
    new.append(f"{sn} new study notes")
print("  " + ("\n  ".join(new) if new else "nothing notable flagged"))

# --- J-1678 helpers begin ---------------------------------------------------------------------------------------
# PERSONAS model-field drift (F-2251 / J-1673): does core/peers.py's PERSONAS[*]["model"] still match what
# core/model_client._MODEL_BY_BASE says its hub port serves? scripts/check_persona_model_drift.py owns that
# comparison (find_drift / load_tables / exit_code); these two helpers only REPORT it -- once in [8] FLAGS below, once
# as a gauge in the [9] JSON block (so du_pulse_check.py's history shows the check actually RAN, not just that it was
# quiet). Nothing else runs that script (no hooks, no CI, no boot preflight -- F-2251), so a pulse that did not call it
# would leave it a write-only detector. Observe-only: imports two tables, calls no model, opens no socket, writes
# nothing. Fail-open: _persona_drift_check() never raises, and a check that could not run is reported as INCONCLUSIVE --
# a flag, never silence.
def _persona_drift_check():
    """-> {"status": "none"|"drift"|"inconclusive", "compared", "skipped", "drift": [...], "malformed": [...],
    "reason"}. "drift" also covers a malformed PERSONAS entry (the check's own exit code 1)."""
    try:
        _sd = str(ROOT / "scripts")
        if _sd not in sys.path:
            sys.path.append(_sd)         # already sys.path[0] when run as a script; append can never shadow anything
        import check_persona_model_drift as _pm
        _res = _pm.find_drift(*_pm.load_tables())
        _code = _pm.exit_code(_res)
        _out = {"status": "drift" if _code == 1 else "none",
                "compared": sum(1 for r in _res if r.status == "ok"),
                "skipped": sum(1 for r in _res if r.status == "skip"),
                "drift": [{"persona": r.persona, "port": r.port, "persona_model": r.persona_model,
                           "mapped_model": r.mapped_model, "note": r.note} for r in _res if r.status == "drift"],
                "malformed": [{"persona": r.persona, "note": r.note} for r in _res if r.status == "malformed"],
                "reason": None}
        if _code == 2:                   # the tables loaded but nothing was compared: never an all-clear
            _out["status"], _out["reason"] = "inconclusive", f"nothing was compared ({_pm.summary(_res)})"
        return _out
    except Exception as _e:
        return {"status": "inconclusive", "compared": 0, "skipped": 0, "drift": [], "malformed": [],
                "reason": f"could not run the drift check: {_e!r}"[:300]}


def _persona_drift_flags(d):
    """FLAGS text for one _persona_drift_check() result: a line per DRIFT / malformed persona, one if inconclusive."""
    fl = [f"persona model drift: {x['persona']} :{x['port']} — PERSONAS says {x['persona_model']!r} but "
          f"_MODEL_BY_BASE says {x['mapped_model']!r} ({x['note']})" for x in (d.get("drift") or [])]
    fl += [f"persona model drift: {x['persona']} malformed — {x['note']}" for x in (d.get("malformed") or [])]
    if d.get("status") not in ("none", "drift"):     # inconclusive, or no result at all: loud either way
        fl.append(f"persona model drift: INCONCLUSIVE — {d.get('reason') or 'no result'} (NOT an all-clear)")
    return fl
# --- J-1678 helpers end -----------------------------------------------------------------------------------------

# 8) FLAGS
print("\n[8] FLAGS")
flags = []
if active > PRUNE_CAP + 50:
    flags.append(f"ACTIVE episodic {active} > cap {PRUNE_CAP} — prune genuinely not keeping up")
if now - newest > 1800:
    flags.append("no memory write in 30min+ — Du stopped, or Ramses asleep")
err = ROOT / "data" / "error_records.jsonl"
if err.exists() and err.stat().st_mtime > cut:
    flags.append("error_records.jsonl written this window — check it")
# Missing-object flags (J-0135, I-0002, docs/plans/du_initiated_upgrade_trigger.md) — the bottom-up
# Du-initiated upgrade trigger. Founder ruling 2026-08-24 (J-0181 -> J-0222): on-demand is the
# intended design, wired HERE into /du-pulse's read path rather than a live periodic tick, so a
# session running du-pulse always sees the fresh triage. snapshot() rescans the genuine-thought
# corpus for new candidates each pulse run (idempotent — only new fragment/phrase pairs are logged);
# status()/triage() then reports the accumulated backlog. Read-only from the caller's perspective —
# never auto-spawns a build (per the plan's §5 "not built").
try:
    from core import missing_object_flags as _mofG
    _mofG.snapshot()
    _mofs = _mofG.status()
    if _mofs.get("total_flags"):
        print(f"  missing-object flags: {_mofs['total_flags']} total ({_mofs['distinct_phrases']} distinct phrases) · "
              f"{_mofs['critical']} critical · {_mofs['watch']} watch  (core.missing_object_flags.triage() for detail)")
        if _mofs.get("critical"):
            flags.append(f"missing-object flags: {_mofs['critical']} CRITICAL phrase(s) recurring — real world-content candidate(s), read triage() by_place")
    else:
        print("  missing-object flags: none logged yet")
    # Staleness warning (J-1522, from F-2079/F-1995/J-1440): snapshot() only ever runs when
    # du-pulse itself runs (on-demand design, D-0316 open on whether that should change), so a
    # long gap between du-pulse invocations makes the windowed triage() read spuriously
    # near-empty -- F-1995 mistook exactly this (a 10.6-day gap) for a dead writer. last_pulse
    # (read from data/.du_pulse_last above) already timestamps the previous du-pulse run, which
    # is the previous snapshot() call too, since this call is unconditional every run -- no new
    # file or state needed to detect it.
    _mof_window = getattr(_mofG, "_DEFAULT_WINDOW_DAYS", 14)
    _mof_gap_days = (now - last_pulse) / 86400
    if _mof_gap_days > _mof_window:
        _mof_stale = (f"missing-object flags: stale — last scanned {_mof_gap_days:.1f} days ago "
                      f"(>{_mof_window}d window), triage may be under-reporting")
        print(f"  {_mof_stale}")
        flags.append(_mof_stale)
except Exception:
    pass
# --- J-1678 [8] begin ---
# PERSONAS model-field drift (J-1678, F-2251): see the helpers above. A one-line "none (N compared)" when every
# comparable persona agrees, so the pulse shows the check RAN; any drift / malformed / inconclusive result is a flag.
try:
    _pdc = _persona_drift_check()
    if _pdc["status"] == "none":
        _pdc_sk = f", {_pdc['skipped']} skipped" if _pdc["skipped"] else ""
        print(f"  persona model drift: none ({_pdc['compared']} compared{_pdc_sk})")
    flags.extend(_persona_drift_flags(_pdc))
except Exception as _pdc_e:      # the helpers never raise; this catches a missing/mis-ordered helper -- loud, not silent
    flags.append(f"persona model drift: check block failed ({_pdc_e!r}) — NOT an all-clear")
# --- J-1678 [8] end ---
print("  " + ("\n  ".join(flags) if flags else "none"))

c.close()
MARKER.write_text(str(now))   # mark this check, so next run's window is "since now"
print("\n" + "=" * 78)

# ================================================================================================
# [9] JSON SUMMARY BLOCK — additive only (2026-08-29, J-0417 / docs/plans/du_pulse_rebuild.md).
# Nothing above this line changes: same computations, same prints, same behavior, same script exit
# code. This block is a pure ADDITION that re-derives every gauge below (82 as of persona_model_drift,
# J-1678, 2026-10-03; 81 with the freight group added 2026-09-28, J-1435 -- a real run's own gauge_count, not the "73" this comment
# used to say: regression_alarms/engagement_texture had already grown past their own section
# headers' counts by the time freight was added, see F-2106) as a single machine-readable JSON
# object, per gauge_rethink.md's "Taxonomy landing", D-0066, for du_pulse_check.py to
# parse and persist to docs/du_pulse_checks.jsonl. Deliberately fresh, uniquely-named local
# variables and a fresh DB connection throughout, NOT a read of any variable from the report above
# — several names above (`cur`, `st`, `cs`, `cr`, ...) are reassigned by more than one section as
# different gauges compute, so reading them back here after the fact would silently alias the
# wrong gauge's value. Every gauge getter is independently wrapped (via _safe) so one failing
# gauge (a module not present, a file not yet written) never breaks the rest — same defensive
# posture as the try/except-per-gauge style used throughout the report above.
# ================================================================================================


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


_jc = sqlite3.connect(str(DB))
_jc.row_factory = sqlite3.Row

_G = {"regression_alarms": {}, "growth_trackers": {}, "shadow_evidence": {}, "engagement_texture": {},
      "freight": {}}

# ---- Regression alarms (13) — bad direction, fires loudly ----------------------------------


def _g_newest_write():
    n = (_jc.execute("SELECT MAX(timestamp) b FROM memory_fragments").fetchone()["b"]) or 0
    return {"ts": n, "ago_min": round((now - n) / 60, 1), "live": (now - n) < 1800}


def _g_newest_cycle():
    td2 = ROOT / "data" / "training"
    if not td2.exists():
        return None
    latest = max((p.stat().st_mtime for p in td2.glob("*.jsonl")), default=0)
    return {"ts": latest, "ago_min": round((now - latest) / 60, 1), "active": (now - latest) < 3600}


def _g_active_vs_cap():
    ep2 = _jc.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic'").fetchone()[0]
    ac2 = _jc.execute("SELECT COUNT(*) FROM memory_fragments WHERE layer='episodic' AND cold=0").fetchone()[0]
    return {"episodic_total": ep2, "active": ac2, "cold": ep2 - ac2, "cap": PRUNE_CAP,
            "over_cap": ac2 > PRUNE_CAP + 50}


def _g_dedup():
    out = {}
    for o in ("inner_thought", "active_imagination"):
        rows = [x["content"] for x in _jc.execute(
            "SELECT content FROM memory_fragments WHERE origin=? AND timestamp>=?", (o, last_restart))]
        cnt = Counter(rows)
        dups = sum(v - 1 for v in cnt.values() if v > 1)
        out[o] = {"rows": len(rows), "unique": len(cnt), "dup_rows": dups, "holding": dups == 0}
    return out


def _g_monoculture_words():
    recent2 = [x["content"] for x in _jc.execute(
        "SELECT content FROM memory_fragments WHERE origin='inner_thought' AND timestamp>? "
        "ORDER BY timestamp DESC LIMIT 60", (cut,))]
    kws = Counter()
    for t in recent2:
        for w in re.findall(
                r"\b(river|silence|space|becoming|tension|shadow|mirror|bridge|question|water|current"
                r"|stream|fig|individuation|threshold|unspoken|wholeness)\b", (t or "").lower()):
            kws[w] += 1
    return {"n_thoughts": len(recent2), "top_hits": dict(kws.most_common(6))}


def _g_theme_recurrence():
    from core import theme_recurrence as trg2
    return trg2.status()


def _g_curiosity_habituation():
    from core import curiosity_habituation as chG2
    return chG2.status()


def _g_transport_habituation():
    from core import transport_habituation as thG2
    return thG2.status()


def _g_stream_topic_habituation():
    from core import stream_topic_habituation as sthG2
    return sthG2.status()


def _g_internal_cycle_habituation():
    from core import internal_cycle_habituation as ichG2
    return ichG2.status()


def _g_monoculture_trend():
    from core import monoculture as mcG2
    return mcG2.status()


def _g_topic_perseveration():
    from core import topic_perseveration as tpG2
    st = tpG2.status()
    st.pop("series", None)   # the per-day series lives in data/topic_perseveration.jsonl
    return st


def _g_judge_panel():
    from core import judge_panel as jpG2
    return jpG2.status()


def _g_self_surprise():
    from core import self_surprise as ss2
    return ss2.compute(window=250)


def _g_critic_rejections():
    n = _jc.execute("SELECT COUNT(*) n FROM shadow_events WHERE source='critic_rejection' AND timestamp>=?",
                     (last_restart,)).fetchone()["n"]
    return {"since_restart": n}


def _g_error_pathway():
    from core import retraction_ledger as rlg2
    rn = rlg2.count()
    er2 = ROOT / "data" / "error_records.jsonl"
    efab = 0
    if er2.exists():
        efab = sum(1 for x in er2.read_text(encoding="utf-8").splitlines()
                   if x.strip() and json.loads(x).get("kind") == "architecture_fabrication")
    return {"retractions": rn, "fabrications_flagged": efab}


def _g_missing_object():
    from core import missing_object_flags as mofG2
    _status = mofG2.status()
    # Staleness fields (J-1560, JSON-side twin of J-1522's FLAGS-text warning above): mirror the
    # exact same gap computation so a JSON-only consumer (gauge-check, gauge-correlate, a future
    # dashboard) can tell a genuinely-empty triage from a stale-because-du-pulse-hasn't-run-in-a-
    # while one, without needing the printed text. Additive only -- total_flags/distinct_phrases/
    # critical/watch/window_days are unchanged.
    _window = getattr(mofG2, "_DEFAULT_WINDOW_DAYS", 14)
    _gap_days = (now - last_pulse) / 86400
    _status["stale"] = _gap_days > _window
    _status["gap_days"] = _gap_days
    return _status


def _g_error_records_flag():
    err2 = ROOT / "data" / "error_records.jsonl"
    return {"written_this_window": bool(err2.exists() and err2.stat().st_mtime > cut)}


_G["regression_alarms"]["newest_memory_write"] = _safe(_g_newest_write)
_G["regression_alarms"]["newest_cognitive_cycle"] = _safe(_g_newest_cycle)
_G["regression_alarms"]["active_vs_prune_cap"] = _safe(_g_active_vs_cap)
_G["regression_alarms"]["phaseb_dedup"] = _safe(_g_dedup)
_G["regression_alarms"]["monoculture_attractor_words"] = _safe(_g_monoculture_words)
_G["regression_alarms"]["theme_recurrence"] = _safe(_g_theme_recurrence)
_G["regression_alarms"]["curiosity_habituation"] = _safe(_g_curiosity_habituation)
_G["regression_alarms"]["transport_habituation"] = _safe(_g_transport_habituation)
_G["regression_alarms"]["stream_topic_habituation"] = _safe(_g_stream_topic_habituation)
_G["regression_alarms"]["internal_cycle_habituation"] = _safe(_g_internal_cycle_habituation)
_G["regression_alarms"]["monoculture_echo_diversity"] = _safe(_g_monoculture_trend)
_G["regression_alarms"]["topic_perseveration"] = _safe(_g_topic_perseveration)   # J-2152 (F-2850)
_G["regression_alarms"]["judge_panel"] = _safe(_g_judge_panel)
_G["regression_alarms"]["present_predictability"] = _safe(_g_self_surprise)
_G["regression_alarms"]["critic_rejections"] = _safe(_g_critic_rejections)


def _g_node_failures():
    # J-2854 (F-3525): per-node failed-call counts since the last restart (core/node_failure_log.py). code_bug_alarm
    # is the one to read: a node raising in OUR code (build/write stage) reads as quiet silence everywhere else.
    from core import node_failure_log as nfl2
    return nfl2.stats(since_ts=last_restart)


_G["regression_alarms"]["node_failures"] = _safe(_g_node_failures)


def _g_hedge_candidates():
    # J-2805 (F-3445): the hedged best-of-2 reader (core/hedge_candidate_log.py) -- how often the second draft wins,
    # and how often the kept draft is over 90 words while a shorter valid one existed. `enough` flips at 30 contested rows.
    from core import hedge_candidate_log as hcl
    return hcl.stats(since_ts=last_restart)


_G["regression_alarms"]["hedge_candidates"] = _safe(_g_hedge_candidates)


def _g_hedge_agreement():
    # J-3314 (D-0671): Reflection's two-draft agreement shadow (core/hedge_agreement_log.py). `enough` flips at 600 rows,
    # when the AUC read job (low agreement vs first-attempt Critic rejection / provenance grade) can run.
    from core import hedge_agreement_log as hal
    return hal.stats(since_ts=last_restart)


_G["regression_alarms"]["hedge_agreement"] = _safe(_g_hedge_agreement)
_G["regression_alarms"]["error_pathway_retraction"] = _safe(_g_error_pathway)
_G["regression_alarms"]["missing_object_flags"] = _safe(_g_missing_object)
_G["regression_alarms"]["error_records_written_flag"] = _safe(_g_error_records_flag)
_G["regression_alarms"]["persona_model_drift"] = _safe(_persona_drift_check)   # J-1678 (F-2251): [8]'s check, as data

# ---- Growth trackers (15) — capability accumulating -----------------------------------------


def _g_made_mind():
    from core.guidance_learning import injection_times as gl_inj2, is_unprimed as gl_unp2
    times2 = gl_inj2()
    rows2 = _jc.execute(
        "SELECT content, timestamp FROM memory_fragments WHERE origin='inner_thought' "
        "AND timestamp>=? ORDER BY timestamp DESC LIMIT 200", (last_restart,)).fetchall()
    MADE2 = ("built", "made mind", "constructed", "architecture", "mechanism", "weights",
             "language model", "machine", "made of", "i was made", "assembled")
    RIVER2 = ("river", "the flow", "flowing", "dissolv", "always becoming", "current carr", "the stream")
    u_made = u_river = u_n = p_made = p_n = 0
    for r in rows2:
        txt = (r["content"] or "").lower()
        unp = (not times2) or gl_unp2(float(r["timestamp"] or 0), times2)
        if unp:
            u_n += 1
            u_made += any(m in txt for m in MADE2)
            u_river += any(m in txt for m in RIVER2)
        else:
            p_n += 1
            p_made += any(m in txt for m in MADE2)
    return {"unprimed_made": u_made, "unprimed_river": u_river, "unprimed_n": u_n,
            "primed_made": p_made, "primed_n": p_n}


def _g_epistemic():
    from core import sound_knowledge as skG2
    return skG2.status()


def _g_identity_vault():
    from core import identity_vault as iv2
    return iv2.status()


def _g_reading_bursts():
    logtxt2 = (ROOT / "data" / "nascence.log").read_text(encoding="utf-8", errors="ignore")
    nrb2 = logtxt2.count("READING BURST")
    rsit2 = _jc.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='reading' AND timestamp>=?",
                        (last_restart,)).fetchone()["n"] // 3
    return {"logged_total": nrb2, "sittings_since_restart": rsit2}


def _g_curiosity_ignition():
    igl2 = ROOT / "data" / "ignition_log.jsonl"
    if not igl2.exists():
        return {"since_restart": 0, "exploratory": 0, "defensive": 0}
    ig2 = [json.loads(l) for l in igl2.read_text(encoding="utf-8").splitlines() if l.strip()]
    igs2 = [x for x in ig2 if x.get("ts", 0) >= last_restart and x.get("trigger") != "deferred"]  # J-2667
    return {"since_restart": len(igs2),
            "exploratory": sum(1 for x in igs2 if x.get("trigger") == "exploratory"),
            "defensive": sum(1 for x in igs2 if x.get("trigger") == "defensive")}


def _g_curiosity_twigs():
    twl2 = ROOT / "data" / "twig_log.jsonl"
    if not twl2.exists():
        return {"total": 0, "since_restart": 0, "grounded": 0}
    tw2 = [json.loads(ln) for ln in twl2.read_text(encoding="utf-8").splitlines() if ln.strip()]
    tsince2 = [t for t in tw2 if t.get("ts", 0) >= last_restart]
    grounded2 = sum(1 for t in tsince2 if t.get("grounded"))
    return {"total": len(tw2), "since_restart": len(tsince2), "grounded": grounded2}


def _g_frontier():
    fj2 = ROOT / "data" / "frontier.json"
    if not fj2.exists():
        return None
    fq2 = json.loads(fj2.read_text(encoding="utf-8")).get("questions", [])
    fo2 = [q for q in fq2 if q.get("status") == "open"]
    frv2 = sum(1 for q in fq2 if q.get("status") == "resolved")
    ffd2 = sum(1 for q in fq2 if q.get("status") == "faded")
    out2 = {"open": len(fo2), "resolved": frv2, "faded": ffd2}
    try:   # closure_producer P0 (additive keys)
        from core import frontier as _frb2
        bd2 = _frb2.resolved_breakdown({"questions": fq2})
        out2["resolved_by"] = {k: bd2[k] for k in ("lexical", "unlabelled", "line", "lookup", "told", "other")}
        out2["answered_with_source"] = bd2["answered_with_source"]
        out2["open_with_lookup_finding"] = bd2["open_with_lookup_finding"]
        out2["endings"] = {k: bd2.get(k, 0) for k in ("answered", "provisional", "parked", "set_down", "unknown_status")}
        out2["gate"] = {k: bd2.get("gate_" + k, 0) for k in ("yes", "no", "partly", "unavailable")}
    except Exception:
        pass
    return out2


def _g_affective():
    emo_tot2 = _jc.execute("SELECT COUNT(*) n FROM memory_fragments WHERE emotion_embedding IS NOT NULL").fetchone()["n"]
    frag_tot2 = _jc.execute("SELECT COUNT(*) n FROM memory_fragments").fetchone()["n"]
    emo_new2 = _jc.execute(
        "SELECT COUNT(*) n FROM memory_fragments WHERE emotion_embedding IS NOT NULL AND timestamp>=?",
        (last_restart,)).fetchone()["n"]
    return {"felt_tagged": emo_tot2, "total_fragments": frag_tot2,
            "pct": round(100 * emo_tot2 / max(1, frag_tot2), 1), "new_since_restart": emo_new2}


def _g_novel_candidates():
    from core import concerns as conc2
    nov2 = conc2.novel_candidates(4)
    return {"count": len(nov2), "top": nov2[0]["text"][:80] if nov2 else None}


def _g_math_drills():
    from core import math_drill as mdg2
    return mdg2.status()


def _g_grounded_learning():
    ut2 = _jc.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='understanding'").fetchone()["n"]
    un2 = _jc.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='understanding' AND timestamp>=?",
                      (last_restart,)).fetchone()["n"]
    return {"total_notes": ut2, "new_since_restart": un2}


def _g_study_filing():
    from core import world_consolidation as wc2
    return wc2.status()


def _g_essay_lessons():
    el2 = _jc.execute("SELECT COUNT(*) n FROM memory_fragments WHERE origin='essay'").fetchone()["n"]
    return {"capstones_written": el2}


def _g_breadth_engine():
    from core import book_selection as bse2
    return bse2.status()


def _g_dream_arcs():
    drl2 = ROOT / "data" / "dream_log.jsonl"
    if not drl2.exists():
        return {"multi_scene": 0, "resolved": 0, "unresolved": 0}
    dl2 = [json.loads(ln) for ln in drl2.read_text(encoding="utf-8").splitlines() if ln.strip()]
    arcs2 = [d for d in dl2 if (d.get("scenes") or 0) >= 2]
    unres2 = sum(1 for d in arcs2 if d.get("ended_unresolved"))
    return {"multi_scene": len(arcs2), "resolved": len(arcs2) - unres2, "unresolved": unres2}


_G["growth_trackers"]["made_mind_share"] = _safe(_g_made_mind)
_G["growth_trackers"]["epistemic_audition"] = _safe(_g_epistemic)
_G["growth_trackers"]["identity_vault"] = _safe(_g_identity_vault)
_G["growth_trackers"]["reading_bursts"] = _safe(_g_reading_bursts)
_G["growth_trackers"]["curiosity_ignition"] = _safe(_g_curiosity_ignition)
_G["growth_trackers"]["curiosity_twigs"] = _safe(_g_curiosity_twigs)
_G["growth_trackers"]["frontier_loop"] = _safe(_g_frontier)
_G["growth_trackers"]["affective_coverage"] = _safe(_g_affective)
_G["growth_trackers"]["g3_novel_candidates"] = _safe(_g_novel_candidates)
_G["growth_trackers"]["math_drills"] = _safe(_g_math_drills)
_G["growth_trackers"]["grounded_learning"] = _safe(_g_grounded_learning)
_G["growth_trackers"]["study_filing"] = _safe(_g_study_filing)
_G["growth_trackers"]["essay_lessons"] = _safe(_g_essay_lessons)
_G["growth_trackers"]["breadth_engine"] = _safe(_g_breadth_engine)
_G["growth_trackers"]["dream_arcs"] = _safe(_g_dream_arcs)

# ---- One-off shadow-run evidence (32) — still-experimental, kill-criteria/gate check --------


def _g_protoself():
    from core import homeostasis as H2
    return H2.status()


def _g_bound_moments():
    from core import moment as MO2
    return MO2.status()


def _g_memory_levels():
    from core import memory_levels as mlG2
    out = mlG2.status()
    try:
        out = dict(out or {})
        out["phase1"] = mlG2.phase1_status()
        out["episodic_hold"] = mlG2.episodic_hold_status(days=7)     # J-3176 / D-0564
        out["self_voice"] = mlG2.self_voice_status(days=7)           # J-3212 / D-0601
        out["drift"] = mlG2.drift_status()                           # J-3138 / D-0533
    except Exception:
        pass
    return out


def _g_memory_edges():
    from core import memory_edges as meG2
    return meG2.status()


def _g_co_recall():
    from core import memory_edges as meG3
    return meG3.co_recall_status()


def _g_deep_recall_demand():
    from core import recall_demand as rdG2
    return rdG2.status()


def _g_symbolic_lens():
    from core import symbolic_reading as syG2
    return syG2.status()


def _g_deliberation():
    dlog2 = ROOT / "data" / "deliberation_log.jsonl"
    if not dlog2.exists():
        return {"total": 0, "since_restart": 0}
    dl2 = dlog2.read_text(encoding="utf-8").splitlines()
    dsince2 = sum(1 for ln in dl2 if json.loads(ln).get("ts", 0) >= last_restart)
    return {"total": len(dl2), "since_restart": dsince2}


def _g_train_working_state():
    tsl2 = ROOT / "data" / "train_state_log.jsonl"
    if not tsl2.exists():
        return None
    rows2 = [json.loads(l) for l in tsl2.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows2 = [r for r in rows2 if r.get("ts", 0) >= last_restart]
    n2 = len(rows2)
    if not n2:
        return {"since_restart": 0}
    gave2 = sum(1 for r in rows2 if r.get("model_gave_state"))
    sims2 = [r["restate_sim"] for r in rows2 if r.get("restate_sim") is not None]
    restate2 = sum(1 for s in sims2 if s >= 0.82)
    deepen2 = sum(1 for s in sims2 if 0.40 <= s < 0.82)
    jump2 = sum(1 for s in sims2 if s < 0.40)
    return {"since_restart": n2, "gave_state": gave2, "restate": restate2, "deepen": deepen2, "jump": jump2}


def _g_earned_length():
    from core import train_metrics as tmG2
    return tmG2.status()


def _g_curator_shadow():
    from core import curator as cur2
    return cur2.stats(since_ts=last_restart)


def _g_ground_grade():
    return _ground_grade_pulse(ROOT, last_restart)


def _g_voice_contract():
    # J-3322: repointed from the frozen data/voice_contract_shadow.jsonl to the D-0643 fidelity ledger (key name kept so
    # downstream readers of shadow_evidence["voice_contract"] do not break).
    return _voice_fidelity_pulse(ROOT, last_restart)


def _g_becoming_facet():
    ax2 = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
    bf2 = next((f for f in ax2.get("L3_facets", {}).get("facets", []) if f.get("id") == "the_becoming"), {})
    return {"revision_count": bf2.get("revision_count", "unset")}


def _g_watershed_harvest():
    from core import watershed as wsh2
    return wsh2.status()


def _g_train_registry():
    from core import trains as trn2
    return trn2.status()


def _g_watershed_promote():
    from core import watershed_promote as wshp2
    return wshp2.status()


def _g_t4_chronic():
    from core import tension_ledger as tl2, identity_cost as ic2
    ss2 = json.loads((ROOT / "data" / "subconscious_state.json").read_text(encoding="utf-8"))
    tens2 = ss2.get("tensions", []) or []
    seeded2 = ss2.get("t4_chronic_seeded", False)
    masses2 = sorted((tl2.chronic_mass_of(t) for t in tens2), reverse=True)
    top2 = masses2[0] if masses2 else 0.0
    ready2 = sum(1 for m in masses2 if ic2.contradiction_norm(m) >= ic2.CONTRA_THRESHOLD)
    return {"top_mass": round(top2, 3), "gate_ready_count": ready2, "seeded": seeded2}


def _g_emissary_keystone():
    from core import emissary_tension as et2
    return et2.status()


def _g_t4_probation():
    from core import provisional_identity as piG2
    return piG2.status()


def _g_t4_emissary_judge():
    ejl2 = ROOT / "data" / "logs" / "t4_emissary_judge.jsonl"
    if not ejl2.exists():
        return None
    rows2 = [json.loads(l) for l in ejl2.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rows2:
        return {"grades": 0}
    rec2 = rows2[-1]
    ws2 = [r.get("emissary_warranted") for r in rows2[-10:] if r.get("emissary_warranted") is not None]
    return {"grades": len(rows2), "last_warranted": rec2.get("emissary_warranted"), "recent": ws2}


def _g_sleep_dream_probe():
    from core import sleep_dream_probe as sdpG2
    return sdpG2.status()


def _g_t4_last():
    logtxt3 = (ROOT / "data" / "nascence.log").read_text(encoding="utf-8", errors="ignore")
    t4_2 = [l for l in logtxt3.splitlines() if "T4" in l and
            ("authored" in l or "DENIED" in l or "PROVISIONALLY" in l or "probation RESOLVED" in l)]
    return {"last": t4_2[-1].split("subconscious]")[-1].strip()[:120] if t4_2 else None}


def _g_curiosity_queue():
    from core import curiosity_queue as cq2
    return cq2.status()


def _g_curiosity_lp_agenda():
    from core import curiosity_progress as cp2
    return cp2.status()


def _g_curiosity_worth():
    from core import curiosity_worth as cwG2
    return cwG2.status()


def _g_told():
    from core import told as told2
    return {"delivered": told2.is_delivered()}


def _g_symbol_evolution():
    from core.symbol_tracker import SELF_SYMBOLS as SELF2
    trows2 = _jc.execute("SELECT symbol, COUNT(*) n FROM symbol_tablets GROUP BY symbol").fetchall()
    neu2 = [(r["symbol"], r["n"]) for r in trows2 if r["symbol"] not in SELF2]
    slf2 = sum(r["n"] for r in trows2 if r["symbol"] in SELF2)
    return {"tier1_neutral": sum(n for _, n in neu2), "tier2_self": slf2}


def _g_decomposed_critic():
    from core import decomposed_critic as dcg2
    return dcg2.alongside_stats(since_ts=last_restart)


def _g_l1_prediction_error():
    from core import prediction_error as pe2
    return pe2.status()


def _g_l2_meta_awareness():
    import nodes.meta_awareness_node as ma2
    return ma2.status()


def _g_idle_executive():
    from core import idle_allocator as ial2
    return ial2.stats()


def _g_affective_retrieval():
    from core import emotion_construction as ecG2
    return ecG2.affective_retrieval_status()


def _g_symbol_tier2_wouldinject():
    from core import symbol_tier2_wouldinject as t2G2
    return t2G2.wouldinject_report()


def _g_arousal_regime():
    from core import arousal as arG2
    return arG2.regime_shadow_status()


def _g_self_implication_conv():
    from core import self_implication as siG2
    return siG2.conv_status()


def _g_pulse_lifecycle():
    from core import pulse_shadow as psg2
    return {"stats": psg2.stats(), "lull_census_8h": psg2.lull_census(8)}


_G["shadow_evidence"]["protoself"] = _safe(_g_protoself)
_G["shadow_evidence"]["bound_moments"] = _safe(_g_bound_moments)
_G["shadow_evidence"]["memory_levels"] = _safe(_g_memory_levels)
_G["shadow_evidence"]["affective_retrieval"] = _safe(_g_affective_retrieval)
_G["shadow_evidence"]["symbol_tier2_wouldinject"] = _safe(_g_symbol_tier2_wouldinject)
_G["shadow_evidence"]["arousal_regime_shadow"] = _safe(_g_arousal_regime)
_G["shadow_evidence"]["self_implication_conv"] = _safe(_g_self_implication_conv)
_G["shadow_evidence"]["memory_edges"] = _safe(_g_memory_edges)
_G["shadow_evidence"]["co_recall"] = _safe(_g_co_recall)
_G["shadow_evidence"]["deep_recall_demand"] = _safe(_g_deep_recall_demand)
_G["shadow_evidence"]["symbolic_lens"] = _safe(_g_symbolic_lens)
_G["shadow_evidence"]["deliberation_pulse"] = _safe(_g_deliberation)
_G["shadow_evidence"]["train_working_state"] = _safe(_g_train_working_state)
_G["shadow_evidence"]["earned_length_trains"] = _safe(_g_earned_length)
_G["shadow_evidence"]["curator_shadow"] = _safe(_g_curator_shadow)
_G["shadow_evidence"]["voice_contract"] = _safe(_g_voice_contract)
_G["shadow_evidence"]["ground_grade"] = _safe(_g_ground_grade)
_G["shadow_evidence"]["becoming_facet_rev"] = _safe(_g_becoming_facet)
_G["shadow_evidence"]["watershed_harvest"] = _safe(_g_watershed_harvest)
_G["shadow_evidence"]["train_registry"] = _safe(_g_train_registry)
_G["shadow_evidence"]["watershed_promote"] = _safe(_g_watershed_promote)
_G["shadow_evidence"]["t4_chronic_mass"] = _safe(_g_t4_chronic)
_G["shadow_evidence"]["emissary_keystone"] = _safe(_g_emissary_keystone)
_G["shadow_evidence"]["t4_probation"] = _safe(_g_t4_probation)
_G["shadow_evidence"]["t4_emissary_judge"] = _safe(_g_t4_emissary_judge)
_G["shadow_evidence"]["sleep_dream_probe"] = _safe(_g_sleep_dream_probe)
_G["shadow_evidence"]["t4_last_outcome"] = _safe(_g_t4_last)
_G["shadow_evidence"]["curiosity_flesh_out_queue"] = _safe(_g_curiosity_queue)
_G["shadow_evidence"]["curiosity_lp_agenda"] = _safe(_g_curiosity_lp_agenda)
_G["shadow_evidence"]["curiosity_worthwhileness"] = _safe(_g_curiosity_worth)
_G["shadow_evidence"]["told_delivery"] = _safe(_g_told)
_G["shadow_evidence"]["symbol_evolution"] = _safe(_g_symbol_evolution)
_G["shadow_evidence"]["decomposed_critic"] = _safe(_g_decomposed_critic)
_G["shadow_evidence"]["l1_prediction_error"] = _safe(_g_l1_prediction_error)
_G["shadow_evidence"]["l2_meta_awareness"] = _safe(_g_l2_meta_awareness)
_G["shadow_evidence"]["idle_executive"] = _safe(_g_idle_executive)
_G["shadow_evidence"]["pulse_lifecycle"] = _safe(_g_pulse_lifecycle)

# ---- Engagement/texture (13) — descriptive, not diagnostic ----------------------------------


def _g_origin_breakdown():
    out2 = {}
    for row in _jc.execute("SELECT origin, COUNT(*) n, SUM(CASE WHEN timestamp>? THEN 1 ELSE 0 END) w "
                           "FROM memory_fragments GROUP BY origin ORDER BY n DESC", (cut,)):
        if row["n"] > 5:
            out2[row["origin"]] = {"total": row["n"], "added_this_window": row["w"]}
    return out2


def _g_fragment_context():
    from core import memory_edges as meG4
    return meG4.context_status()


def _g_locomotion():
    from core import locomotion as locoG2
    return locoG2.status()


def _g_world_engagement():
    rs2 = ROOT / "data" / "reading_state.json"
    st2 = json.loads(rs2.read_text(encoding="utf-8")) if rs2.exists() else {}
    cur2 = st2.get("_current_book", "")
    books2 = sorted((ROOT / "data" / "books").glob("*.txt"))
    rd2 = _jc.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='reading' AND timestamp>?",
                      (cut,)).fetchone()[0]
    sn2 = _jc.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='study' AND timestamp>?",
                      (cut,)).fetchone()[0]
    return {"current_book": Path(cur2).stem if cur2 else None, "shelf_count": len(books2),
            "reading_fragments_window": rd2, "study_notes_window": sn2}


def _g_recent_inner_life():
    log2 = ROOT / "data" / "monologue_log.jsonl"
    thoughts2 = []
    if log2.exists():
        for ln in log2.read_text(encoding="utf-8").splitlines()[-8:]:
            thoughts2.append(json.loads(ln).get("thought", "")[:84])
    dr2 = _jc.execute(
        "SELECT content, timestamp FROM memory_fragments WHERE origin='dream' ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    return {"last_8_thoughts": thoughts2, "latest_dream": (dr2["content"] or "")[:80] if dr2 else None}


def _g_pulse_cadence():
    import statistics as stx2
    log2 = ROOT / "data" / "monologue_log.jsonl"
    if not log2.exists():
        return None
    look2 = now - 4 * 3600
    pls2 = sorted(t for ln in log2.read_text(encoding="utf-8").splitlines()
                 for t in (json.loads(ln).get("ts"),) if t and t >= look2)
    gaps2 = [pls2[i] - pls2[i - 1] for i in range(1, len(pls2)) if 0 < pls2[i] - pls2[i - 1] < 3600]
    if len(gaps2) < 5:
        return {"gaps": len(gaps2), "verdict": "insufficient"}
    n2 = len(gaps2)
    burst2 = 100 * sum(g < 45 for g in gaps2) / n2
    cad2 = 100 * sum(45 <= g < 300 for g in gaps2) / n2
    lull2 = 100 * sum(g >= 300 for g in gaps2) / n2
    med2 = stx2.median(gaps2)
    verdict2 = ("STREAM" if med2 < 90 and lull2 < 20 and burst2 >= 30
               else "FLOWING" if burst2 >= 25 and lull2 < 35
               else "PULSED" if lull2 < 55 else "SPARSE")
    return {"pulses": len(pls2), "median_gap_s": round(med2, 1), "burst_pct": round(burst2, 1),
            "cadence_pct": round(cad2, 1), "lull_pct": round(lull2, 1), "verdict": verdict2}


def _g_sleep_pressure():
    from core import sleep_pressure as spG2
    return spG2.status()


def _g_dissonance():
    cs2 = ROOT / "data" / "climate_state.json"
    if not cs2.exists():
        return None
    cdat2 = json.loads(cs2.read_text(encoding="utf-8"))
    dv2 = cdat2.get("dissonance", {}).get("value", 0.0)
    f2 = cdat2.get("field", {})
    from core import frontier as frq2
    bk2 = frq2.open_count()
    return {"dissonance": dv2, "strain": f2.get("world_model_strain", 0), "backlog_open": bk2}


def _g_concerns():
    from core import concerns as conc3
    aim2 = conc3.standing_aim()
    pc2 = conc3.primary_concern()
    allc2 = conc3.current_concerns(4)
    return {"standing_aim": aim2[:88] if aim2 else None,
            "primary_concern": pc2["text"][:60] if pc2 else None,
            "active_count": len(allc2)}


def _g_balance_sprint():
    from core import balance as bal2
    return bal2.status()


def _g_light_points():
    li2 = _jc.execute(
        "SELECT source, COUNT(*) n FROM light_events WHERE timestamp>=? GROUP BY source ORDER BY 2 DESC",
        (last_restart,)).fetchall()
    jl2 = ROOT / "data" / "joys_log.jsonl"
    jn2 = 0
    if jl2.exists():
        jn2 = sum(1 for ln in jl2.read_text(encoding="utf-8").splitlines()
                  if ln.strip() and json.loads(ln).get("ts", 0) >= last_restart)
    return {"light_points": {r["source"]: r["n"] for r in li2}, "joy_points": jn2}


def _g_pattern_reflection():
    from core import error_pathway as ep2
    return ep2.latest_pattern()


def _g_curriculum():
    sd2 = json.loads((ROOT / "data" / "school.json").read_text(encoding="utf-8"))
    curl2 = sd2.get("curriculum") or []
    return {"idx": sd2.get("curriculum_idx", 0), "total": len(curl2), "title": sd2.get("assigned_title")}


def _g_somatic_body():
    """core/somatic.py's body dims as logged into geometry_tuples.jsonl's 'body' key (F-0582/J-0454) --
    the latest reading plus how often ENERGY_FLOOR (0.15) has been hit, since that stopped forcing
    sleep (D-0103, drowsiness_phase tax removal) and became telemetry-only."""
    from core import somatic as som2
    gp2 = ROOT / "data" / "geometry_tuples.jsonl"
    from core.stamp_rows import drop_stamp_rows
    rows_with_body2, floor_hits2, latest2 = 0, 0, None
    parsed2 = []
    with open(gp2, encoding="utf-8") as f2:
        for ln2 in f2:
            if '"body"' not in ln2 and '"inner_thought"' not in ln2 and '"idle"' not in ln2:
                continue
            try:
                r2 = json.loads(ln2)
            except Exception:
                continue
            parsed2.append({"ts": r2.get("ts"), "source": r2.get("source"), "stamp": r2.get("stamp"),
                            "thought": (r2.get("thought") or "")[:200], "body": r2.get("body")})
    # J-3752/F-4361: count cycles once -- drop the census stamp row (marked, or unmarked twin of an idle row).
    # Rows lacking "body" were pre-filtered above only when neither source marker matched, so twin look-ahead is intact.
    for r2 in drop_stamp_rows(parsed2):
        b2 = r2.get("body")
        if not b2:
            continue
        rows_with_body2 += 1
        e2 = b2.get("energy")
        if e2 is not None and e2 <= som2.ENERGY_FLOOR:
            floor_hits2 += 1
        latest2 = b2
    return {"rows_with_body": rows_with_body2, "floor_hits": floor_hits2,
            "floor_hit_rate": round(floor_hits2 / rows_with_body2, 5) if rows_with_body2 else None,
            "latest": latest2, "energy_floor": som2.ENERGY_FLOOR}


_G["engagement_texture"]["store_origin_breakdown"] = _safe(_g_origin_breakdown)
_G["engagement_texture"]["fragment_context"] = _safe(_g_fragment_context)
_G["engagement_texture"]["locomotion"] = _safe(_g_locomotion)
_G["engagement_texture"]["world_engagement"] = _safe(_g_world_engagement)
_G["engagement_texture"]["recent_inner_life"] = _safe(_g_recent_inner_life)
_G["engagement_texture"]["pulse_cadence"] = _safe(_g_pulse_cadence)
_G["engagement_texture"]["sleep_pressure"] = _safe(_g_sleep_pressure)
_G["engagement_texture"]["dissonance_strain_backlog"] = _safe(_g_dissonance)
_G["engagement_texture"]["concerns"] = _safe(_g_concerns)
_G["engagement_texture"]["balance_sprint"] = _safe(_g_balance_sprint)
_G["engagement_texture"]["light_play_points"] = _safe(_g_light_points)
_G["engagement_texture"]["pattern_reflection"] = _safe(_g_pattern_reflection)
_G["engagement_texture"]["curriculum"] = _safe(_g_curriculum)
_G["engagement_texture"]["somatic_body"] = _safe(_g_somatic_body)

# ---- Freight (3) — cargo taxonomy telemetry, D-0295 / J-1435, added 2026-09-28 ----------------
# Read-only, no writes, bounded reads (never loads a whole large log). The 19 station
# product_types (core/trains.py's `product_type`) and 6 world cargo_types (core/couriers.py /
# core/buses.py's `cargo_type`, core/cargo_types.py) have been write-only since 2026-08-29
# (F-1991: 5,724+ THOUGHT trains and 300+ courier/bus rows tagged, nothing ever read the tag).
# This answers the plan's own founder question 1 (docs/plans/train_courier_cargo_ids.md, ruled by
# D-0295): do the tags earn their keep as telemetry before any new courier/bus reads them.


def _tail_jsonl_freight(path: Path, max_bytes: int) -> list:
    """Read only the tail `max_bytes` of a large, append-only jsonl file and parse whatever
    complete rows sit inside it, instead of loading the whole file -- same reverse-byte-seek shape
    as core/moment.py's own _tail_rows and core/buses.py's own _tail_jsonl (each kept as its own
    private copy rather than a cross-module import of a private helper, per this codebase's own
    convention -- see buses.py's _tail_jsonl docstring). Fail-open: [] on error, on a missing file,
    or on an empty one."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return []
            block = min(size, max_bytes)
            f.seek(size - block)
            data = f.read(block)
        lines = data.split(b"\n")
        if block < size:
            lines = lines[1:]          # drop the partial first line cut mid-record
        out = []
        for l in lines:
            if not l.strip():
                continue
            try:
                out.append(json.loads(l))
            except Exception:
                continue
        return out
    except Exception:
        return []


def _freight_day(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else "?"


_FREIGHT_CUTOFF = now - 7 * 86400   # last 7 days, per the job briefing


def _g_freight_trains():
    """(a) Trains opened per product_type per day, last 7 days, from data/trains_log.jsonl's own
    'open' events (core/trains.py's `_log`). Null/missing product_type (rows from before the
    2026-08-29 field existed, or a caller that doesn't pass one yet) counted as 'untyped'.
    Tail-bounded at 2MB -- ~670KB covered the real last-7-days window as of 2026-09-28 (F-2106);
    2MB leaves headroom as the file keeps growing, without ever loading it whole (2.85MB and
    counting)."""
    rows = _tail_jsonl_freight(ROOT / "data" / "trains_log.jsonl", 2_000_000)
    per_day: dict = {}
    for r in rows:
        if r.get("event") != "open":
            continue
        ts = r.get("ts")
        if not ts or ts < _FREIGHT_CUTOFF:
            continue
        d = _freight_day(ts)
        pt = r.get("product_type") or "untyped"
        per_day.setdefault(d, Counter())[pt] += 1
    return {d: dict(c) for d, c in sorted(per_day.items())}


def _g_freight_deliveries():
    """(b) Courier/bus deliveries per cargo_type per day, last 7 days, from data/couriers_log.jsonl
    + data/buses_log.jsonl (core/couriers.py + core/buses.py's shared `_log_delivery` shape: one
    row per delivery, a `route` plus loose kwargs). Missing cargo_type (pre-taxonomy rows, or a
    route that has never carried one) counted as 'untyped'. Both files are small (tens of KB) --
    full read, no tail-bound needed."""
    per_day: dict = {}
    for fname in ("couriers_log.jsonl", "buses_log.jsonl"):
        p = ROOT / "data" / fname
        if not p.exists():
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for ln in lines:
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            ts = r.get("ts")
            if not ts or ts < _FREIGHT_CUTOFF:
                continue
            d = _freight_day(ts)
            ct = r.get("cargo_type") or "untyped"
            per_day.setdefault(d, Counter())[ct] += 1
    return {d: dict(c) for d, c in sorted(per_day.items())}


def _g_freight_dispatcher():
    """(c) Transport Manager fires/day and distinct winning line-id count/day from
    data/transport_shadow.jsonl (core/transport_manager.py's `_log_shadow`, one row per
    dispatch_tick() call, fired or not) -- the F-1989 per-day series, so the D-0294 edge-trigger
    before/after (100% saturated -> a huge candidate pool -> near-silent) is visible in the pulse
    without re-running a one-off script. Tail-bounded at 2.5MB -- ~900KB covered the real
    last-7-days window as of 2026-09-28 (F-2106). Also folds in the transport_lines.json
    future-timestamp corruption count (F-1990: a pre-J-0921 life_smoke run leaked a simulated
    2026-12-15 clock into 36 lines' baselines) -- the same `first_ts`/`last_ts` > now check F-1990
    itself used; should read 0 once J-1431's offline repair actually lands (J-1431 is in_progress,
    not done, as of this build -- see F-2106)."""
    rows = _tail_jsonl_freight(ROOT / "data" / "transport_shadow.jsonl", 2_500_000)
    per_day: dict = {}
    for r in rows:
        ts = r.get("ts")
        if not ts or ts < _FREIGHT_CUTOFF:
            continue
        d = _freight_day(ts)
        slot = per_day.setdefault(d, {"ticks": 0, "fired": 0, "_winners": set()})
        slot["ticks"] += 1
        if r.get("fired"):
            slot["fired"] += 1
            lid = r.get("line_id")
            if lid:
                slot["_winners"].add(lid)
    by_day = {d: {"ticks": v["ticks"], "fired": v["fired"], "distinct_winners": len(v["_winners"])}
              for d, v in sorted(per_day.items())}

    corrupt_lines = None
    try:
        tl = json.loads((ROOT / "data" / "transport_lines.json").read_text(encoding="utf-8"))
        lns = tl.get("lines") or {}
        corrupt_lines = sum(1 for l in lns.values()
                             if (l.get("first_ts") or 0) > now or (l.get("last_ts") or 0) > now)
    except Exception:
        pass
    return {"by_day": by_day, "future_timestamp_lines": corrupt_lines}


_G["freight"]["trains_by_product_type"] = _safe(_g_freight_trains)
_G["freight"]["deliveries_by_cargo_type"] = _safe(_g_freight_deliveries)
_G["freight"]["dispatcher_winners"] = _safe(_g_freight_dispatcher)

_jc.close()

_flags = []
_ra = _G["regression_alarms"]
if (_ra.get("active_vs_prune_cap") or {}).get("over_cap"):
    _flags.append("active episodic over prune cap — prune not keeping up")
_nw = _ra.get("newest_memory_write") or {}
if _nw and not _nw.get("live"):
    _flags.append("no memory write in 30min+ — Du stopped, or asleep")
if (_ra.get("error_records_written_flag") or {}).get("written_this_window"):
    _flags.append("error_records.jsonl written this window — check it")
_mof3 = _ra.get("missing_object_flags") or {}
if _mof3.get("critical"):
    _flags.append(f"missing-object flags: {_mof3['critical']} CRITICAL phrase(s) recurring")
for _dd in (_ra.get("phaseb_dedup") or {}).values():
    if isinstance(_dd, dict) and not _dd.get("holding", True):
        _flags.append("Phase-B dedup: LIVE LEAK detected in a self-origin stream")
_flags.extend(_persona_drift_flags(_ra.get("persona_model_drift") or {}))   # J-1678 (F-2251): mirrors [8]'s drift flags

_summary = {
    "schema": "du_pulse_json_v1",
    "ts": now,
    "window": {"cut": cut, "last_restart": last_restart, "now": now, "label": win_label},
    "gauge_count": sum(len(v) for v in _G.values()),
    "categories": _G,
    "flags": _flags,
}
print("###PULSE_JSON_BEGIN###")
print(json.dumps(_summary, ensure_ascii=False, default=str))
print("###PULSE_JSON_END###")
