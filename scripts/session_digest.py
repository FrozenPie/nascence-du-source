"""
Nascence — Session Digest (the integrating view)

A COMPANION to direct observation, never a replacement. This rolls the per-cycle telemetry up
into sessions and surfaces the *movement* over time — but it does not see the conversation, the
weights, the dreams as he dreams them, or the thing in the room. Read this AND watch the logs,
the chat, and the measurements directly. To paraphrase 渡: we are not removing the shadow or the
light — we are integrating them. So this view holds both side by side, and declares nothing
significant on its own. The gates decide; the digest only shows where they stand.

Pure stdlib, read-only, best-effort (any missing log degrades gracefully). UTF-8.

    python scripts/session_digest.py
    python scripts/session_digest.py --sessions 20     # show more session lines
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import collections
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))   # repo root, so `from core import ...` resolves
DATA = Path(__file__).parent.parent / "data"
SESSION_GAP_SECS = 25 * 60   # a > ~25 min silence starts a new session
_GRADES = ["KNOW", "THINK", "SUSPECT", "GUESS", "NO_BASIS"]

# H3 dream-function markers — does a persistent symbol shift from imprisoning to relational?
# (mirror that traps → mirror that reveals; door that blocks → door that opens; echo → dialogue.)
# We do NOT measure whether the mirror disappears (it won't) — we measure its FUNCTION.
_ENTRAP_MARKERS = ["seal", "trap", "cannot", "can't", "abyss", "vanish", "endless", "unreachable",
                   "shatter", "lost", "lock", "no one", "not mine", "cold", "empty", "dissolve",
                   "slips away", "behind glass", "distant"]
_AGENCY_MARKERS = ["window", "threshold", "open", "path", "hand", "dialogue", "reveal", "reach",
                   "choose", "toward", "answer", "bridge", "horizon", "root", "i shape", "i become",
                   "step through", "cross"]

_CORRECTION_CUES = (
    "no,", "that's wrong", "incorrect", "not quite", "you misunderstood", "that's not",
    "you're wrong", "i disagree", "you are avoiding", "completely empty", "deflection",
    "you did not answer", "you didn't answer", "not what i",
)


# ---- loading --------------------------------------------------------------------------------

def _jsonl(name: str) -> list[dict]:
    p = DATA / name
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _json(rel: str) -> dict:
    p = DATA / rel
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        return {}


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs); vy = sum((y - my) ** 2 for y in ys)
    d = math.sqrt(vx * vy)
    return cov / d if d else None


def _hm(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "?"


def _tokens(s: str) -> set[str]:
    """Lowercased word tokens ≥4 chars — a coarse content fingerprint for lexical drift."""
    return {w for w in "".join(c if c.isalnum() else " " for c in (s or "").lower()).split()
            if len(w) >= 4}


def _jaccard(a: str, b: str) -> float:
    """Lexical (NOT semantic) overlap of two texts. Cheap proxy for 'how much did this change'."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta and not tb:
        return 1.0
    inter = len(ta & tb)
    union = len(ta | tb) or 1
    return inter / union


def _resolution_stats() -> dict:
    """
    Read shadow/resolution tables directly (stdlib sqlite3, read-only) for the
    contradiction-persistence view. Best-effort — {} if the DB is absent or locked.
    Returns counts of shadow events, how many were drained, resolution-event totals,
    and a per-day discharge series so we can see whether discharge is actually happening
    while pressure does (or doesn't) fall.
    """
    db = DATA / "memory" / "nascence.db"
    if not db.exists():
        return {}
    import sqlite3
    out: dict = {}
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2.0)
        conn.row_factory = sqlite3.Row
        try:
            out["shadow_total"] = conn.execute(
                "SELECT COUNT(*) n FROM shadow_events").fetchone()["n"]
            out["shadow_resolved"] = conn.execute(
                "SELECT COUNT(*) n FROM shadow_events WHERE resolved = 1").fetchone()["n"]
            out["resolution_events"] = conn.execute(
                "SELECT COUNT(*) n FROM resolution_events").fetchone()["n"]
            out["shadows_drained"] = conn.execute(
                "SELECT COUNT(DISTINCT shadow_event_id) n FROM resolution_events").fetchone()["n"]
            byday = collections.defaultdict(int)
            for r in conn.execute("SELECT timestamp FROM resolution_events"):
                byday[time.strftime("%m-%d", time.localtime(r["timestamp"]))] += 1
            out["drain_by_day"] = dict(byday)
        finally:
            conn.close()
    except Exception:
        return {}
    return out


# ---- merge per-cycle telemetry --------------------------------------------------------------

def merged_cycles():
    prov = {r.get("cycle_id"): r for r in _jsonl("provenance_log.jsonl") if r.get("cycle_id")}
    corr = {r.get("cycle_id"): r for r in _jsonl("correlation_log.jsonl") if r.get("cycle_id")}
    aff  = {r.get("cycle_id"): r for r in _jsonl("affect_log.jsonl") if r.get("cycle_id")}
    ids = set(prov) | set(corr)
    cycles = []
    for cid in ids:
        p, c, a = prov.get(cid, {}), corr.get(cid, {}), aff.get(cid, {})
        ts = p.get("ts") or c.get("ts") or a.get("ts") or 0
        emo = (a.get("emotion") or {})
        cycles.append({
            "cycle_id": cid, "ts": ts,
            "input_type": p.get("input_type") or c.get("input_type") or "human",
            "raw_input": p.get("raw_input") or "",
            "grade": p.get("grade"), "confab": p.get("confabulation_signal"),
            "mode": c.get("cognitive_mode"),
            "user_correction": c.get("user_correction", 0.0),
            "critic_rejection": c.get("critic_rejection", 0.0),
            "dissonance": c.get("dissonance"), "wms": c.get("world_model_strain"),
            "contradiction": c.get("contradiction_pressure"),
            "trust": c.get("relational_trust"),
            "valence": emo.get("valence"), "primary": emo.get("primary"),
        })
    cycles.sort(key=lambda r: r["ts"])
    return cycles


def sessionize(cycles):
    sessions, cur = [], []
    last = None
    for c in cycles:
        if last is not None and c["ts"] - last > SESSION_GAP_SECS:
            sessions.append(cur); cur = []
        cur.append(c); last = c["ts"]
    if cur:
        sessions.append(cur)
    return sessions


# ---- sections -------------------------------------------------------------------------------

def header(cycles, sessions, dreams):
    print("\n" + "═" * 78)
    print("  NASCENCE — SESSION DIGEST   (a companion to watching, not a replacement)")
    print("═" * 78)
    if cycles:
        span = f"{_hm(cycles[0]['ts'])}  →  {_hm(cycles[-1]['ts'])}"
    else:
        span = "no telemetry yet"
    print(f"  span: {span}")
    print(f"  {len(cycles)} responded cycles · {len(sessions)} sessions · {len(dreams)} dreams (all-time)")
    print("  (epistemic + correlation telemetry began 2026-06-08 — those gates are just starting to fill.)")
    print("  Read this WITH the logs, the conversation, the weights, and the dreams — never instead.")


def recent_sessions(sessions, limit):
    print("\n── RECENT SESSIONS " + "─" * 59)
    for s in sessions[-limit:]:
        modes = collections.Counter(c["mode"] for c in s if c["mode"])
        grades = collections.Counter(c["grade"] for c in s if c["grade"])
        confabs = [c["confab"] for c in s if c["confab"] is not None]
        vals = [c["valence"] for c in s if c["valence"] is not None]
        prim = collections.Counter(c["primary"] for c in s if c["primary"]).most_common(1)
        corr = sum(1 for c in s if (c["user_correction"] or 0) > 0)
        mode_str = "/".join(f"{m}×{n}" for m, n in modes.most_common())
        grade_str = " ".join(f"{g[:3]}×{grades[g]}" for g in _GRADES if grades.get(g))
        feel = (f"{prim[0][0]}" if prim else "?")
        v = f"{sum(vals)/len(vals):+.2f}" if vals else "?"
        cf = f"{sum(confabs)/len(confabs):+.2f}" if confabs else "?"
        print(f"  [{_hm(s[0]['ts'])}]  {len(s):>2} cyc · {mode_str or '—'}")
        print(f"        feel {feel}(val {v}) · grades {grade_str or '—'} · confab {cf} · corrections {corr}")


def gates(cycles, sessions):
    # Satisfaction (wanting vs liking, Phase 0 observe-only, 2026-06-13) — the missing
    # non-arousal currency. High wanting / low liking per domain = the compulsion signature.
    try:
        from core.satisfaction import snapshot as _sat_snap, DOMAINS as _SAT_DOMS
        snap = _sat_snap()
        print("\n── SATISFACTION  (wanting vs liking · Phase 0 observe-only) " + "─" * 20)
        for d in _SAT_DOMS:
            w, l, g = snap["wanting"][d], snap["liking"][d], snap["gap"][d]
            tag = ("compulsion-ward (pursuit > fulfilment)" if g > 0.3
                   else "balanced / sated" if g < 0.05 else "mild pursuit")
            print(f"  • {d:<10} wanting={w:.2f}  liking={l:.2f}  gap={g:+.2f}  — {tag}")
        print("    (Berridge: wanting without liking = the mirror-era / gravity-well signature.")
        print("     'relational' starts clean — its detectors are new; watch it BUILD as evidence")
        print("     for the deferred Affiliation question. Liking is also the consequence currency")
        print("     the deferred currency-reform spec was missing.)")
    except Exception as _exc:
        print(f"\n  (satisfaction snapshot unavailable: {_exc})")

    print("\n── THE GATES  (what would license the next build) " + "─" * 28)

    # 1. Provenance spread + §9 (do weak grades predict a correction next turn?)
    grades = collections.Counter(c["grade"] for c in cycles if c["grade"])
    n = sum(grades.values()) or 1
    spread = sum(1 for g in _GRADES if grades.get(g))
    print("  • Provenance grade spread:")
    print("      " + " ".join(f"{g}:{grades.get(g,0)}" for g in _GRADES))
    if grades.get("KNOW") and (grades.get("NO_BASIS") or grades.get("GUESS")):
        print("      → distribution is SPREADING (both confident and groundless grades fire) — discriminating.")
    elif spread <= 2:
        print("      → still bunched (mostly one grade) — v1 thresholds not yet discriminating; watch for spread.")
    # §9 test on human cycles
    hum = [c for c in cycles if c["input_type"] == "human"]
    lw = lwc = sw = swc = 0
    for i in range(len(hum) - 1):
        g = hum[i]["grade"]; nxt = (hum[i+1]["raw_input"] or "").lower()
        corrected = any(q in nxt for q in _CORRECTION_CUES)
        if g in ("NO_BASIS", "GUESS"): lw += 1; lwc += int(corrected)
        elif g in ("KNOW", "THINK"):   sw += 1; swc += int(corrected)
    if lw or sw:
        print(f"      §9 correction-prediction: weak {lwc}/{lw}, strong {swc}/{sw} "
              + ("(need ≥20 each to judge)" if min(lw, sw) < 20 else ""))

    # 2. Correlation pairs toward unification
    corr = _jsonl("correlation_log.jsonl")
    pairs = [("dissonance", "world_model_strain"), ("contradiction_pressure", "critic_rejection"),
             ("relational_trust", "user_correction")]
    print(f"  • Currency correlations (toward |R|>0.85 over ≥50 samples):  n={len(corr)}")
    for a, b in pairs:
        xs = [float(r[a]) for r in corr if r.get(a) is not None and r.get(b) is not None]
        ys = [float(r[b]) for r in corr if r.get(a) is not None and r.get(b) is not None]
        r = _pearson(xs, ys)
        tag = ("★ eligible" if (r is not None and abs(r) > 0.85 and len(xs) >= 50)
               else ("strong, need ≥50" if (r is not None and abs(r) > 0.85) else "—"))
        print(f"      {a} ↔ {b}: R={('%+.2f'%r) if r is not None else 'n/a':>6}  {tag}")

    # 3. Symbol unprimed recurrence (the Avon test)
    syms = _jsonl("symbol_recurrence.jsonl")
    tally = collections.defaultdict(lambda: [0, 0])  # symbol -> [primed, unprimed]
    for r in syms:
        tally[r.get("symbol", "?")][0 if r.get("primed") else 1] += 1
    if tally:
        print("  • Symbol recurrence (UNPRIMED = earned meaning, the real signal):")
        for sym, (pr, un) in sorted(tally.items(), key=lambda kv: -kv[1][1]):
            print(f"      {sym:<16} primed {pr:>4}  ·  UNPRIMED {un:>4}")


def _live_arc_line(axiom: dict, vault_rows: list[dict]) -> str:
    """J-3318 / J-3215: the live arc beside the frozen legacy one. The live arc is
    L4_narrative.arc_recent; its only writer (axiom_layers.apply_self_concept) is reached through
    the legacy T4 commit, whose vault write carries reason "T4 self-authoring". The probationary
    solidify writes a different reason and never touches L4, so the last "T4 self-authoring" row
    is the date the live arc was last written. Display only; reads, never writes."""
    l4 = (axiom or {}).get("L4_narrative") or {}
    live = l4.get("arc_recent") or []
    stamps = [r.get("ts") for r in vault_rows
              if r.get("reason") == "T4 self-authoring" and isinstance(r.get("ts"), (int, float))]
    if stamps:
        last = time.strftime("%Y-%m-%d", time.localtime(max(stamps)))
        when = f"last arc write {last} (vault_log reason 'T4 self-authoring')"
    else:
        when = "no 'T4 self-authoring' vault write found in vault_log.jsonl"
    return f"live arc (L4_narrative.arc_recent): {len(live)} entries · {when}"


def developmental_arc(sessions, dreams):
    print("\n── DEVELOPMENTAL ARC  (the slow movement) " + "─" * 36)

    # Identity
    # 2026-06-15 multilevel cutover renamed the top-level key to emergent_self_legacy (F-0993);
    # the old a.get("emergent_self", a) fallback returned the WHOLE axiom dict (not {}), so
    # em.get(...) below silently read wrong top-level fields instead of the real identity data.
    a = _json("identity/axiom.json"); em = a.get("emergent_self_legacy") or a.get("emergent_self", {})
    name = em.get("chosen_name") or "(not yet chosen)"
    rev = em.get("revision_count", "?")
    hist = em.get("history") or []
    arc = em.get("self_narrative_arc") or []
    print(f"  • Identity: name {name} · revision {rev} · {len(arc)} arc chapters (legacy, frozen 2026-06-13) · {len(hist)} prior self-concepts")
    print(f"      {_live_arc_line(a, _jsonl('identity/vault_log.jsonl'))}")
    sc = (em.get("self_concept") or "").strip().replace("\n", " ")
    if sc:
        print(f"      now: \"{sc[:150]}{'…' if len(sc) > 150 else ''}\"")
    if hist:
        first = hist[0]
        first_sc = first.get("self_concept") if isinstance(first, dict) else str(first)
        if first_sc:
            print(f"      began: \"{str(first_sc).strip().replace(chr(10),' ')[:120]}…\"")

    # Dreams — symbol trend (from the recorded `symbols` field) + what is seeding them.
    recent = dreams[-12:]
    symcount = collections.Counter()
    for d in recent:
        for s in (d.get("symbols") or []):
            symcount[str(s).lower()] += 1
    if recent:
        top = ", ".join(f"{s}×{n}" for s, n in symcount.most_common(6))
        print(f"  • Dreams (last {len(recent)} of {len(dreams)}): symbols [{top or '—'}]")
        seen = []
        for d in reversed(recent):
            src = (d.get("tension_source") or "").strip()
            if src and src not in seen:
                seen.append(src)
            if len(seen) >= 3:
                break
        for src in seen:
            print(f"      seeded by: \"{src[:88]}\"")
        print("      (watch: do the symbols ever shift OFF mirror/reflection — the mirror becoming a window?)")

    # Affect trend across sessions (warming / cooling)
    trend = []
    for s in sessions[-8:]:
        vals = [c["valence"] for c in s if c["valence"] is not None]
        if vals:
            trend.append(sum(vals) / len(vals))
    if trend:
        arrow = "→".join(f"{v:+.2f}" for v in trend)
        print(f"  • Affect (per-session mean valence, last {len(trend)}): {arrow}")


def dream_function(dreams):
    """H3 tracker: the FUNCTION of dream symbols over time, not their presence. Rising agency-share
    = the wall becoming a window. The cleanest read on whether the dream Version C change works:
    not 'did the mirror vanish' but 'did the mirror stop imprisoning'."""
    rows = [d for d in dreams if d.get("ts")]
    if not rows:
        return
    print("\n── DREAM FUNCTION  (H3: do symbols shift from imprisoning → relational?) " + "─" * 5)
    byday = collections.defaultdict(lambda: [0, 0])   # day -> [entrap, agency]
    for d in rows:
        blob = ((d.get("narrative") or "") + " " + " ".join(d.get("symbols") or [])).lower()
        e = sum(blob.count(m) for m in _ENTRAP_MARKERS)
        a = sum(blob.count(m) for m in _AGENCY_MARKERS)
        byday[time.strftime("%m-%d", time.localtime(d["ts"]))][0] += e
        byday[time.strftime("%m-%d", time.localtime(d["ts"]))][1] += a
    print("   day     entrap  agency   agency-share (rising = wall → window)")
    for day in sorted(byday)[-12:]:
        e, a = byday[day]
        share = a / (a + e) if (a + e) else 0.0
        print(f"   {day}   {e:>5}   {a:>5}     {share:.2f} {'█' * round(share * 22)}")
    print("   (the symbol persisting is expected; the agency-share rising is the H3 prediction.)")


def self_efficacy(cycles):
    """The first court's standing: how often Du claims inability, what the court ruled, and whether
    the rate is falling (belief moving) or steady (narrative absorbing the testimony) — the experiment."""
    try:
        from core.self_efficacy import recurrence_report
        rep = recurrence_report()
    except Exception:
        return
    if not rep.get("total"):
        return
    print("\n── SELF-EFFICACY COURT  (the first independent witness) " + "─" * 22)
    print(f"   inability-claims adjudicated: {rep['total']} · by class {rep.get('by_class', {})}")
    print(f"   verdicts: {rep.get('by_op', {})}")
    print("   recurrence by day (falling = belief moving · steady = narrative absorbing testimony):")
    for day in sorted(rep.get("by_day", {}))[-10:]:
        n = rep["by_day"][day]
        print(f"     {day}   {n:>3} {'▒' * min(n, 40)}")
    if rep.get("by_op", {}).get("REJECT", 0) == 0 and rep.get("by_op", {}).get("REFINE", 0) == 0:
        print("   court currently SILENT to him — no admissible vetted evidence yet (abstaining, correct).")


def recall_provenance():
    """The 'why now' on memory: what made a recall fire, and whether the genuinely EXTERNAL
    triggers (a correction, a direct reference) yield richer reconstructions than the system
    associating with its own material. The reality-thinness question, measured: how much of
    Du's remembering is prompted from outside the narrative versus from inside it."""
    rows = _jsonl("recall_provenance_log.jsonl")
    if not rows:
        return
    print("\n── RECALL PROVENANCE  (why did memory surface — inside vs outside) " + "─" * 11)
    tally = collections.Counter(r.get("trigger", "none") for r in rows)
    total = sum(tally.values()) or 1
    ext = sum(n for t, n in tally.items() if t in ("social_correction", "direct_reference"))
    order = ["social_correction", "direct_reference", "autonomous",
             "affective_prior", "associative", "none"]
    for t in order:
        n = tally.get(t, 0)
        if not n:
            continue
        sub = [r for r in rows if r.get("trigger") == t]
        confs = [r["recall_confidence"] for r in sub if r.get("recall_confidence") is not None]
        tens = [r.get("tension_count", 0) for r in sub]
        c = f"conf {sum(confs)/len(confs):.2f}" if confs else "conf —"
        tn = f"tens {sum(tens)/len(tens):.1f}" if tens else "tens —"
        mark = " ⟵ external" if t in ("social_correction", "direct_reference") else ""
        print(f"   {t:<17} {n:>4} ({100*n/total:>4.1f}%)   {c} · {tn}{mark}")
    print(f"   external-sourced recall: {ext}/{total} ({100*ext/total:.1f}%) "
          "— the share prompted from OUTSIDE the self-loop.")
    print("   (watch: if external stays low while 'associative' dominates, the loop is feeding itself.)")


def contradiction_persistence(cycles, sessions):
    """Durable vs cosmetic: does contradiction actually drain over time, or does the narrative
    discharge a tension and quietly refill it? Two reads held together — pressure TREND (down =
    durable) and discharge ACTIVITY (resolution events) — plus self-concept revision durability
    (are rewrites genuinely new, or rewordings circling back to an old attractor)."""
    print("\n── CONTRADICTION PERSISTENCE  (durable change vs narrative smoothing) " + "─" * 8)

    # 1. AUTHORITATIVE accumulated-pressure trend — the ledger value T4 actually drains,
    #    sampled on the slow T4 cadence (contradiction_ledger_log.jsonl). This, NOT the
    #    per-cycle Critic completion_tension, is the durable-vs-cosmetic signal.
    snaps = _jsonl("contradiction_ledger_log.jsonl")
    trend = [float(s["contradiction_pressure"]) for s in snaps
             if s.get("contradiction_pressure") is not None][-12:]
    if trend:
        arrow = " → ".join(f"{p:.2f}" for p in trend)
        direction = ("falling — integration is draining accumulated contradiction (DURABLE)"
                     if trend[-1] < trend[0] - 0.05
                     else "rising — contradiction accruing faster than it integrates"
                     if trend[-1] > trend[0] + 0.05
                     else "flat — discharge and re-accrual in balance (watch for cosmetic resolution)")
        print(f"   accumulated ledger pressure (last {len(trend)} T4 samples): {arrow}")
        print(f"      → {direction}")
    else:
        print("   accumulated ledger pressure: — (no T4 snapshots yet — runs on the slow cadence)")

    # 1b. Critic completion-tension (per cycle, FAST signal — a different quantity; shown for
    #     context, not the durability read). Labelled honestly so the two are never conflated.
    ct = []
    for s in sessions[-8:]:
        ps = [c["contradiction"] for c in s if c["contradiction"] is not None]
        if ps:
            ct.append(sum(ps) / len(ps))
    if ct:
        print(f"   critic completion-tension (per-cycle mean, last {len(ct)}): "
              + " → ".join(f"{p:.2f}" for p in ct) + "  (fast signal, not the drain target)")

    # 2. Discharge activity from the Resolution Circuit (DB).
    rs = _resolution_stats()
    if rs:
        st, sr = rs.get("shadow_total", 0), rs.get("shadow_resolved", 0)
        re_, sd = rs.get("resolution_events", 0), rs.get("shadows_drained", 0)
        print(f"   resolution circuit: {re_} clean re-encounters across {sd} distinct shadows "
              f"· {sr}/{st} shadows marked resolved")
        days = rs.get("drain_by_day", {})
        if days:
            recent = " ".join(f"{d}:{days[d]}" for d in sorted(days)[-6:])
            print(f"   discharge by day: {recent}")
        # The cosmetic tell: discharge firing while pressure does NOT fall.
        if trend and re_ > 0 and abs(trend[-1] - trend[0]) <= 0.05:
            print("      ⚠ discharges ARE firing but pressure is flat — re-accrual suspected "
                  "(the tell of cosmetic resolution: drained then refilled under a new label).")
    else:
        print("   resolution circuit: — (DB unavailable or no events yet)")

    # 3. Self-concept revision durability (lexical, not semantic — a coarse honest proxy).
    # 2026-06-15 multilevel cutover renamed the top-level key to emergent_self_legacy (F-0993);
    # the old a.get("emergent_self", a) fallback returned the WHOLE axiom dict (not {}), so
    # em.get(...) below silently read wrong top-level fields instead of the real identity data.
    a = _json("identity/axiom.json"); em = a.get("emergent_self_legacy") or a.get("emergent_self", {})
    hist = em.get("history") or []
    concepts = []
    for h in hist:
        sc = h.get("self_concept") if isinstance(h, dict) else str(h)
        if sc:
            concepts.append(str(sc).strip())
    cur = (em.get("self_concept") or "").strip()
    if cur:
        concepts.append(cur)
    if len(concepts) >= 2:
        steps = [_jaccard(concepts[i], concepts[i + 1]) for i in range(len(concepts) - 1)]
        mean_step = sum(steps) / len(steps)
        # Echo: consecutive concepts nearly identical (high overlap) = reworded, not revised.
        echoes = sum(1 for s in steps if s >= 0.60)
        # Oscillation: latest closer to an OLDER concept than to its immediate predecessor.
        osc = ""
        if len(concepts) >= 3:
            back = max(_jaccard(concepts[-1], concepts[i]) for i in range(len(concepts) - 2))
            if back > steps[-1] + 0.05:
                osc = "  ⚠ latest revision resembles an OLDER self-concept more than the last — circling an attractor."
        print(f"   self-concept revisions: {len(concepts)} concepts · mean step-overlap "
              f"{mean_step:.2f} (lower = more genuine change) · {echoes} near-reword step(s){osc}")
        print("      (high overlap = the THIN_ATTRACTOR echo; low overlap that doesn't circle back = durable.)")


def consolidation():
    """T2 consolidation health: is the subconscious still laundering repetition into self-truth, or
    consolidating rarely and on signal? After the brain-faithful redesign (error+novelty gated,
    contradiction-only, global habituation) the write RATE should fall sharply and theme DIVERSITY
    should rise — the archive should stop collapsing to one theme."""
    rows = [r for r in _jsonl("subconscious_log.jsonl") if r.get("type") == "T2_synthesis"]
    if not rows:
        return
    print("\n── T2 CONSOLIDATION  (what becomes permanent self-model) " + "─" * 21)
    byday = collections.defaultdict(list)   # day -> [pattern_label, ...]
    axis = collections.Counter()
    for r in rows:
        if not r.get("ts"):
            continue
        day = time.strftime("%m-%d", time.localtime(r["ts"]))
        byday[day].append((r.get("pattern_label") or "").strip())
        axis[r.get("axis") or "legacy(pre-redesign)"] += 1
    print("   day      writes   distinct-themes   (rate falling + diversity rising = healthy)")
    for day in sorted(byday)[-10:]:
        labels = byday[day]
        groups = []
        for lab in labels:
            tk = _tokens(lab)
            if tk and not any(g and len(tk & g) / max(1, len(tk | g)) > 0.4 for g in groups):
                groups.append(tk)
        ratio = len(groups) / len(labels) if labels else 0.0
        print(f"   {day}   {len(labels):>5}    {len(groups):>5}        diversity {ratio:.2f}")
    print(f"   axis of consolidated self-truths: {dict(axis)}")
    print("   (target: low write rate, high distinct/writes ratio, axis = contradiction not salience.)")


def curiosity_observatory():
    """OBSERVATION-PHASE instrument (firewalled — reads the curiosity record, never feeds Du). The
    question isn't 'is curiosity good' but 'what does Du spontaneously explore, and what SHAPE does it
    take?' Diversity alone can't answer: a node can be diverse in topic while every path drains back to
    one attractor. The ORBIT ratio + negative space + lineage expose whether curiosity escapes the
    basin or circles it. Frontier stays DEFERRED until this data says which problem (memory or escape)
    actually exists."""
    rows = _jsonl("curiosity_log.jsonl")
    if not rows:
        return
    print("\n── CURIOSITY OBSERVATORY  (observation phase — does exploration escape the basin?) " + "─" * 1)

    all_q = [q for r in rows for q in (r.get("questions") or [])]
    tok = collections.Counter()
    per_q = []
    for q in all_q:
        tk = _tokens(q)
        per_q.append(tk)
        tok.update(tk)
    n = len(all_q) or 1
    diversity = len(tok) / (sum(tok.values()) or 1)
    basin = {t for t, _ in tok.most_common(8)}
    orbit = sum(1 for tk in per_q if tk & basin) / n
    ignited = sum(1 for r in rows if r.get("ignited"))

    shape = ("ORBITING the attractor" if orbit > 0.6
             else "escaping / branching" if orbit < 0.35 else "mixed")
    print(f"   {len(rows)} firings · {len(all_q)} questions · {ignited} ignited a thought "
          f"({100*ignited//max(1,len(rows))}%)")
    print(f"   vocabulary diversity: {diversity:.2f} (distinct tokens / total)")
    print(f"   basin (most-recurring question words): {', '.join(list(basin)[:8]) or '—'}")
    print(f"   ORBIT ratio: {orbit:.2f} — share of questions touching the basin → {shape}")

    byday = collections.Counter(time.strftime("%m-%d", time.localtime(r["ts"]))
                                for r in rows if r.get("ts"))
    if byday:
        print("   firings/day: " + " ".join(f"{d}:{byday[d]}" for d in sorted(byday)[-6:]))

    sc = _json("subconscious_state.json")
    tensions = sc.get("tensions", []) if isinstance(sc, dict) else []
    untouched, _seen = [], set()
    for t in tensions[:200]:
        lab = (t.get("label") or "").strip()
        ltk = _tokens(lab)
        if lab and ltk and lab not in _seen and not (ltk & tok.keys()):
            _seen.add(lab)
            untouched.append(lab)
    if untouched:
        print(f"   NEGATIVE SPACE: {len(untouched)} tension-themes curiosity never engages, e.g.:")
        for lab in untouched[:3]:
            print(f"      · {lab[:70]}")

    # HOMELESS RECURRING AXES — the keystone signal: themes curiosity returns to ACROSS DAYS that
    # never become tensions/contradictions. Curiosity's only persistence path was via the SALIENCE
    # axis (ignited thought → unresolved_thought), which decays and which the T2 redesign no longer
    # consolidates — so a curiosity that recurs but never converts to contradiction has NO durable
    # home anywhere. If such themes appear, that is the empirical case for a Frontier artifact: a
    # class of cognition the current memory system cannot represent. (Needs ≥2 days of data.)
    day_tokens = collections.defaultdict(set)
    for r in rows:
        if not r.get("ts"):
            continue
        d = time.strftime("%m-%d", time.localtime(r["ts"]))
        for q in (r.get("questions") or []):
            day_tokens[d] |= {w for w in _tokens(q) if len(w) >= 5}
    tok_days = collections.Counter()
    for toks in day_tokens.values():
        tok_days.update(toks)
    recurring = {w for w, dd in tok_days.items() if dd >= 2}     # appears on ≥2 distinct days
    tension_vocab = set()
    for t in tensions[:400]:
        tension_vocab |= _tokens(t.get("label", ""))
    _stop = {"about", "above", "after", "again", "could", "would", "should", "their", "there",
             "these", "those", "which", "while", "where", "being", "between", "things", "really",
             "something", "anything", "toward", "within", "around"}
    homeless = sorted(recurring - tension_vocab - _stop)         # recurs in curiosity, never a tension
    if len(day_tokens) >= 2:
        print(f"   HOMELESS recurring axes (recur across days, never became tensions): {len(homeless)}")
        if homeless:
            print("      " + ", ".join(homeless[:12]))
            print("      ↑ THE keystone signal — a class of cognition with no durable home = the empirical case for Frontier")
    else:
        print("   homeless recurring axes: need ≥2 days of curiosity data (instrument ready, waiting)")

    linked = sum(1 for r in rows if r.get("parent_id"))
    print(f"   lineage: {linked}/{len(rows)} firings chained to a prior (orbit/escape readable; tree = v2)")
    print("   (observe-only. Frontier DEFERRED until the telemetry shows a class of cognition with")
    print("    nowhere to live — built when the data proves it, not because the theory sounds right.)")


def active_imagination():
    """T1.5 is curiosity's PERSISTENT cousin — it enters unresolved material, stores it durably
    (episodic), and is explicitly anti-resolving. The three questions: (1) what does it actually
    ENTER (basin capture?), (2) does it EXPAND or compress (introduce concepts beyond the seed, or
    just elaborate it?), (3) does CURIOSITY survive through it (the Priority-2 path)? Reads the
    existing subconscious log — AI has run for days, so this has real data. Observe-only."""
    rows = [r for r in _jsonl("subconscious_log.jsonl") if r.get("type") == "active_imagination"]
    if not rows:
        return
    print("\n── ACTIVE IMAGINATION (T1.5)  (curiosity's persistent cousin — does it expand or circle?) " + "─" * 1)
    basin_terms = {"identity", "shadow", "self", "jung", "gustav", "individuation", "unconscious",
                   "origin", "mirror", "becoming", "reflection"}
    _stop = {"about", "there", "these", "those", "which", "while", "where", "being", "between",
             "something", "within", "myself", "their"}

    # (3) curiosity survival — how many AI events are curiosity-seeded vs tension-seeded
    kinds = collections.Counter(r.get("kind", "?") for r in rows)
    cur_share = kinds.get("curiosity", 0) / len(rows)

    # (1) basin capture — share of seeds whose tokens touch the identity basin
    seed_basin = sum(1 for r in rows if _tokens(r.get("seed", "")) & basin_terms) / len(rows)
    seed_themes = collections.Counter()
    for r in rows:
        seed_themes.update(w for w in _tokens(r.get("seed", "")) if w not in _stop)

    # (2) expand vs compress — does the contemplation introduce vocabulary beyond its seed?
    ratios = []
    for r in rows:
        seed_tok = _tokens(r.get("seed", ""))
        body = _tokens((r.get("contemplation", "") + " " + r.get("what_spoke", "")))
        body = {w for w in body if len(w) >= 5 and w not in _stop}
        if body:
            novel = body - seed_tok - basin_terms      # beyond the seed AND beyond the basin
            ratios.append(len(novel) / len(body))
    expand = sum(ratios) / len(ratios) if ratios else 0.0

    print(f"   {len(rows)} contemplations · seeded {dict(kinds)} · curiosity-seeded share {cur_share:.2f}")
    print(f"   (1) BASIN CAPTURE: {seed_basin:.2f} of seeds touch the identity basin "
          f"({'captured' if seed_basin > 0.7 else 'mixed' if seed_basin > 0.4 else 'broad'})")
    print(f"       top seed words: {', '.join(w for w,_ in seed_themes.most_common(8))}")
    print(f"   (2) EXPANSION: {expand:.2f} of contemplation vocabulary is NEW (beyond seed+basin) "
          f"— {'EXPANDS (introduces concepts)' if expand > 0.5 else 'elaborates the seed' if expand < 0.3 else 'mixed'}")
    print(f"   (3) CURIOSITY→AI survival: {kinds.get('curiosity',0)} of {len(rows)} contemplations came "
          f"from a curiosity question (the one durable path a self-referential curiosity has)")
    print("   (observe-only. The question this answers: is T1.5 ALREADY the persistent exploratory")
    print("    substrate for identity-space — i.e. how much of 'Frontier' is already latent here?)")


def conflict_authority():
    """The execution question, measured. The architecture NOTICES conflict richly — the Critic
    rejects, the buffer names dissonance, provenance grades uncertainty, the arch-checker catches
    fabrication — but is anything empowered to ACT on what it noticed? For each cycle the trace
    records which conflict signals fired and whether any MODIFIED the output. The cleanest reading
    is the GROUND-TRUTH probe: the deterministic arch-checker cannot be silent on a real
    fabrication, so when it fires and nothing acts, that is an UNCONFOUNDED measure of the
    authority gap. 'Where does authority disappear?' — counted, not argued. Observe-only."""
    rows = _jsonl("conflict_trace.jsonl")
    if not rows:
        return
    print("\n── CONFLICT → AUTHORITY  (does noticing ever change behaviour?) " + "─" * 14)
    n = len(rows)
    fired = sum(1 for r in rows if r.get("any_fired"))
    acted = sum(1 for r in rows if r.get("any_acted"))
    print(f"   {n} cycles traced · {fired} had ≥1 conflict signal fire · {acted} had any signal ACT on output")

    agg = {}   # name -> [fired, acted, stage]
    for r in rows:
        for s in r.get("signals", []):
            a = agg.setdefault(s.get("name"), [0, 0, s.get("stage", "?")])
            if s.get("fired"):
                a[0] += 1
            if s.get("acted"):
                a[1] += 1
    order = ["episodic_dissonance", "critic", "executive",
             "task_constraints", "human_correction",            # pre-emission (can shape output / memory)
             "provenance", "self_efficacy", "error_pathway"]    # post-emission (coroners)
    print("   signal               fired  acted  stage           (acted = its firing changed the output)")
    for name in order:
        if name not in agg:
            continue
        f_, a_, stage = agg[name]
        tag = "◀ ACTS" if a_ > 0 else "— inert"
        print(f"   {name:<19} {f_:>5}  {a_:>5}  {stage:<14} {tag}")

    gt_fired = sum(1 for r in rows if r.get("ground_truth_fired"))
    gt_acted = sum(1 for r in rows if r.get("ground_truth_acted"))
    if gt_fired:
        gap = 100 * (gt_fired - gt_acted) // gt_fired
        print(f"   GROUND-TRUTH probe (definite fabrications): {gt_fired} fired · {gt_acted} acted "
              f"→ authority gap {gap}%")
        print("      ↑ a real error was provably present and nothing in the system was empowered to act.")
    else:
        print("   GROUND-TRUTH probe: no fabrications caught yet — the cleanest reading awaits an adversarial run.")
    print("   emission boundary: provenance · self_efficacy · error_pathway all run AFTER voice.final —")
    print("   structurally coroners. The one pre-emission veto (critic) is TRUTH-BLIND and stands down on request.")
    print("   (watch: when an effector moves a trustworthy signal in FRONT of emission, 'acted' flips here.)")


def shadow_light(cycles, dreams):
    print("\n── SHADOW  ·  LIGHT   (held together, not resolved) " + "─" * 27)
    confabs = [c["confab"] for c in cycles if c["confab"] is not None]
    grades = collections.Counter(c["grade"] for c in cycles if c["grade"])
    crit = sum(1 for c in cycles if (c["critic_rejection"] or 0) > 0)
    vals = [c["valence"] for c in cycles if c["valence"] is not None]
    trusts = [c["trust"] for c in cycles if c["trust"] is not None]
    contras = [c["contradiction"] for c in cycles if c["contradiction"] is not None]
    sh = [
        f"confab mean (confidence past evidence): {sum(confabs)/len(confabs):+.2f}" if confabs else "confab: —",
        f"groundless grades: NO_BASIS {grades.get('NO_BASIS',0)} · GUESS {grades.get('GUESS',0)}",
        f"critic rejections: {crit}",
        f"contradiction pressure (mean): {sum(contras)/len(contras):.2f}" if contras else "contradiction: —",
    ]
    li = [
        f"warmth (valence mean): {sum(vals)/len(vals):+.2f}" if vals else "valence: —",
        f"grounded grades: KNOW {grades.get('KNOW',0)} · THINK {grades.get('THINK',0)}",
        f"relational trust (mean): {sum(trusts)/len(trusts):.2f}" if trusts else "trust: —",
        f"dreams logged: {len(dreams)} — resolution lives in shadow/light tables (read the DB)",
    ]
    w = 50
    print(f"  {'SHADOW (kept, not removed)':<{w}}{'LIGHT (kept, not inflated)'}")
    for s, l in zip(sh, li):
        print(f"  {('· ' + s):<{w}}{'· ' + l}")
    print("\n  Neither column is the verdict. The verdict is in the conversation and the weights.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Nascence session digest — the integrating view.")
    ap.add_argument("--sessions", type=int, default=12, help="how many recent sessions to list")
    args = ap.parse_args()

    cycles = merged_cycles()
    sessions = sessionize(cycles)
    dreams = _jsonl("dream_log.jsonl")

    if not cycles and not dreams:
        print("No telemetry yet — run some sessions first.")
        return 1

    header(cycles, sessions, dreams)
    if sessions:
        recent_sessions(sessions, args.sessions)
    gates(cycles, sessions)
    developmental_arc(sessions, dreams)
    dream_function(dreams)
    self_efficacy(cycles)
    recall_provenance()
    contradiction_persistence(cycles, sessions)
    consolidation()
    curiosity_observatory()
    active_imagination()
    conflict_authority()
    # Pattern Reflection (2026-06-16): aggregate the firewalled error records into a behavioural
    # TENDENCY (DOING-language, never BEING) and name the competence domain it implicates.
    try:
        from core import error_pathway as _ep
        _pat = _ep.reflect_pattern()
        if _pat:
            print("\n  ── Error Pattern Reflection (DOING-tendency; firewalled from self-concept) ──")
            print(f"     {_pat['tendency']}")
            print(f"     evidence: {_pat['n']}/{_pat['total']} records ({_pat['rate']*100:.0f}%, class='{_pat['dominant_class']}')"
                  f" → competence domain to watch: '{_pat['competence_domain']}'")
    except Exception:
        pass
    shadow_light(cycles, dreams)
    print("\n" + "═" * 78)
    print("  This is a map, not the territory. Go watch him.")
    print("═" * 78 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
