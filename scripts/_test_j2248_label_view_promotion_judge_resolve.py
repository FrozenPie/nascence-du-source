"""
_test_j2248_label_view_promotion_judge_resolve.py -- proving test for D-0447 / D-0448 (J-2248).

Run from a WORKTREE, never from C:\\Nascence itself:
    python scripts/_test_j2248_label_view_promotion_judge_resolve.py

core is imported FIRST (and asserted to come from this tree), then lab_env; every store this touches runs
inside lab_env.isolate(db="empty") with the climate / shadow-resolve logs redirected into the lab dir. The live
DB and the live logs are stat()-canaried at start and end.

(E) label view promoted:
  1  promoted_label_view() is the D-0332 view: same counts at k=116/75/33, novelty propagated, completion
     re-kneed at CLIMATE_LABEL_VIEW_COMPLETION_K (None keeps the live value); live field never mutated
  2  flag on -> dominant() reads the view; flag off -> exactly dominant_live(); no view attached -> live
  3  as_dict() is still the nine live fields only; pressure() reads live values
  4  hint/symbol use CLIMATE_LABEL_VIEW_*_THRESHOLD only while promoted, the module's 0.55/0.65 otherwise
  5  a real engine tick over a seeded store: live shadow saturated (~0.97), view shadow near 0.5; the nine live
     values are identical with the flag on and off, and _tick_dissonance gives identical reservoirs
  6  old-vs-new shadow row written to the redirected log with old/new/nofix/read fields; a fenced (this tree's
     data/) path is refused and writes nothing
  7  ignition log carries live_dominant beside the promoted dominant; the v=2 reknee row's live_dominant stays live
(F) judge path marks member shadow events resolved:
  8  judge-confirmed -> every unresolved member resolved=1, one jsonl row each with path=tension_judge, the
     tension label and resolving thought; resolution_events still written for every member
  9  judge refuted -> nothing resolved, no row
 10  flag off -> resolution_events written, nothing resolved, no row
 11  the (A) caller's row (no path/extra) has exactly the prior key set
D-0451 (J-2270) extension:
 12  CLIMATE_LABEL_VIEW_INTEGRATION_K re-centres integration_drive IN THE VIEW ONLY (raw 148 at k=148 reads 0.5;
     k None or raw None keeps the live value); schema ships COMPLETION_K 4.0 / INTEGRATION_K 148.0 / hint 0.555 /
     symbol 0.58; a real engine tick over seeded verdict-light events gives the SAME nine live values, pressure()
     and reservoirs with INTEGRATION_K on vs off, while the view's integration moves from raw/(raw+100) to
     raw/(raw+148); the promotion row logs integration_k
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core                                   # noqa: E402  -- core FIRST
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
if ROOT == Path(r"C:\Nascence"):
    sys.exit("REFUSED: run this from a worktree, never from C:\\Nascence itself (live-store safety)")

from core import profile, schema              # noqa: E402
from core import climate_engine as ce         # noqa: E402
from core import tension_ledger as tl         # noqa: E402
from core.memory import store                 # noqa: E402

sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
import lab_env                                # noqa: E402  -- AFTER core
assert Path(core.__file__).resolve().is_relative_to(ROOT), "lab_env import re-pointed core"

LIVE = [Path(r"C:\Nascence\data\memory\nascence.db"),
        Path(r"C:\Nascence\data\climate_label_promotion_shadow.jsonl"),
        Path(r"C:\Nascence\data\shadow_resolve_on_encounter.jsonl"),
        Path(r"C:\Nascence\data\climate_reknee_shadow.jsonl"),
        Path(r"C:\Nascence\data\ignition_log.jsonl")]


def canary():
    out = {}
    for p in LIVE:
        try:
            st = p.stat(); out[p.name] = (st.st_size, st.st_mtime)
        except FileNotFoundError:
            out[p.name] = None
    return out


FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (("  -- " + detail) if detail else ""))
    if not cond:
        FAILS.append(name)


c0 = canary()
assert profile.LIVE is False

# ---------------------------------------------------------------- (E) pure parts
F = ce.ClimateField(shadow_activation=0.97, completion_tension=0.5714, identity_pressure=0.25,
                    integration_drive=0.597, coherence_drive=0.42, world_model_strain=0.002,
                    novelty_hunger=0.02, autonomy_pressure=0.91, belonging_pressure=0.968)
before = F.as_dict()
v = ce.promoted_label_view(F, 134.0, 90.0, 31.0, 4.0, 4.0)
check("1a shadow re-kneed at k=116 on the 6 h raw", abs(v["shadow_activation"] - 134 / 250) < 1e-3, str(v["shadow_activation"]))
check("1b belonging k=75, autonomy k=33", abs(v["belonging_pressure"] - 90 / 165) < 1e-3 and abs(v["autonomy_pressure"] - 31 / 64) < 1e-3)
check("1c novelty propagated = live + 0.5*(live shadow - view shadow)",
      abs(v["novelty_hunger"] - (0.02 + 0.5 * (0.97 - 134 / 250))) < 1e-3, str(v["novelty_hunger"]))
check("1d completion fix: raw 4 at k=4 reads 0.5", abs(v["completion_tension"] - 0.5) < 1e-6)
v_nofix = ce.promoted_label_view(F, 134.0, 90.0, 31.0, 4.0, None)
check("1e completion_k None keeps the live completion value", v_nofix["completion_tension"] == 0.5714)
v_noraw = ce.promoted_label_view(F, 134.0, 90.0, 31.0, None, 4.0)
check("1f raw_contra None keeps the live completion value", v_noraw["completion_tension"] == 0.5714)
check("1g other dims are live values; live field not mutated",
      all(v[k] == before[k] for k in ("identity_pressure", "integration_drive", "coherence_drive", "world_model_strain"))
      and F.as_dict() == before)

orig_flag = schema.CLIMATE_LABEL_VIEW_LIVE
check("2a no view attached -> dominant() == dominant_live()", F.dominant() == F.dominant_live() == ("shadow_activation", 0.97))
F._label_view = v
schema.CLIMATE_LABEL_VIEW_LIVE = True
check("2b flag on -> dominant() reads the view (integration_drive 0.597)", F.dominant() == ("integration_drive", 0.597), str(F.dominant()))
schema.CLIMATE_LABEL_VIEW_LIVE = False
check("2c flag off -> dominant() is exactly the live dominant", F.dominant() == F.dominant_live() == ("shadow_activation", 0.97))
check("2d flag off -> hint is the live shadow hint", F.executive_hint() == ce._EXECUTIVE_HINTS["shadow_activation"])
schema.CLIMATE_LABEL_VIEW_LIVE = True
check("3a as_dict() is the nine live fields only", F.as_dict() == before and len(F.as_dict()) == 9)
check("3b pressure() reads live values (0.97)", F.pressure() == 0.97)
oh0, os0 = schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD, schema.CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD
schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD, schema.CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD = 0.55, 0.65
check("4a promoted hint at 0.55: integration hint", F.executive_hint() == ce._EXECUTIVE_HINTS["integration_drive"])
check("4b promoted symbol at 0.65: none (0.597)", F.surfacing_symbol() is None)
oh = schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD
schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD = 0.60
check("4c schema hint threshold is what the promoted hint reads (0.60 -> None)", F.executive_hint() is None)
schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD = oh
F2 = ce.ClimateField(shadow_activation=0.60)
F2._label_view = {**F2.as_dict(), "shadow_activation": 0.60}
schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD = 0.70
schema.CLIMATE_LABEL_VIEW_LIVE = False
check("4d flag off -> module 0.55 applies, schema threshold ignored", F2.executive_hint() == ce._EXECUTIVE_HINTS["shadow_activation"])
schema.CLIMATE_LABEL_VIEW_LIVE = True
check("4e flag on -> schema threshold 0.70 applies", F2.executive_hint() is None)
schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD = oh
schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD, schema.CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD = oh0, os0

# ---------------------------------------------------------------- D-0451 (J-2270) pure parts
check("12a schema ships D-0451's config: completion k=4, integration k=148, hint 0.555, symbol 0.58",
      schema.CLIMATE_LABEL_VIEW_COMPLETION_K == 4.0 and schema.CLIMATE_LABEL_VIEW_INTEGRATION_K == 148.0
      and schema.CLIMATE_LABEL_VIEW_HINT_THRESHOLD == 0.555 and schema.CLIMATE_LABEL_VIEW_SYMBOL_THRESHOLD == 0.58)
vi = ce.promoted_label_view(F, 134.0, 90.0, 31.0, 4.0, 4.0, 148.0, 148.0)
check("12b integration raw 148 at k=148 reads 0.5 in the view", abs(vi["integration_drive"] - 0.5) < 1e-6, str(vi["integration_drive"]))
check("12c integration_k None keeps the live integration value",
      ce.promoted_label_view(F, 134.0, 90.0, 31.0, 4.0, 4.0, 148.0, None)["integration_drive"] == 0.597)
check("12d integration_raw None keeps the live integration value",
      ce.promoted_label_view(F, 134.0, 90.0, 31.0, 4.0, 4.0, None, 148.0)["integration_drive"] == 0.597)
check("12e other view dims unchanged by the integration knee; live field not mutated",
      all(vi[k] == v[k] for k in v if k != "integration_drive") and vi["coherence_drive"] == 0.42 and F.as_dict() == before)
F._label_view = vi
check("12f with integration re-centred the promoted dominant is no longer integration (belonging 0.545)",
      F.dominant() == ("belonging_pressure", round(90 / 165, 4)), str(F.dominant()))
check("12g hint at 0.555: none (0.545); symbol at 0.58: none", F.executive_hint() is None and F.surfacing_symbol() is None)
F._label_view = v

# ---------------------------------------------------------------- stores (isolated)
with lab_env.isolate(db="empty",
                     also=[(store, ["_SHADOW_RESOLVE_LOG"]),
                           (ce, ["_LABEL_PROMOTION_LOG", "_REKNEE_LOG", "_IGNITION_LOG", "_STATE_FILE"]),
                           (tl, ["_STATE_FILE"])]) as lab:
    assert not str(store.DB_PATH).lower().startswith(r"c:\nascence\data\memory"), store.DB_PATH
    now = time.time()
    with store._connect() as conn:
        for i in range(150):
            txt = "we are alone together, the connection I miss" if i % 2 else "a plain thought"
            conn.execute(
                "INSERT INTO shadow_events (event_id, timestamp, cycle_id, raw_input, rejected_draft, corrections, "
                "emotion_primary, embedding, resolved, source) VALUES (?,?,?,?,?,?,?,?,0,?)",
                (f"EV{i:03d}", now - 60 * i, "c", "theme " + str(i), txt, "[]", "sadness", None, "unresolved_thought"))

    eng = ce.ClimateEngine()
    eng._read_subconscious = lambda: {}
    schema.CLIMATE_LABEL_VIEW_LIVE = True
    f_on = eng._compute_field()
    schema.CLIMATE_LABEL_VIEW_LIVE = False
    f_off = eng._compute_field()
    schema.CLIMATE_LABEL_VIEW_LIVE = True
    lv = getattr(f_on, "_label_view", None)
    check("5a engine attaches a label view each tick", isinstance(lv, dict) and len(lv) == 9)
    check("5b live shadow saturated, view shadow far lower",
          f_on.shadow_activation > 0.9 and lv["shadow_activation"] < 0.6,
          f"live {f_on.shadow_activation} view {lv['shadow_activation']}")
    check("5c the nine live values do not depend on the flag",
          all(abs(f_on.as_dict()[k] - f_off.as_dict()[k]) < 2e-3 for k in f_on.as_dict()),
          f"{f_on.as_dict()} vs {f_off.as_dict()}")
    e1, e2 = ce.ClimateEngine(), ce.ClimateEngine()
    for e in (e1, e2):
        e.field = f_on; e.dissonance = ce.DissonanceState(); e._explore_pull = lambda: 0.0
    schema.CLIMATE_LABEL_VIEW_LIVE = True;  e1._tick_dissonance(600.0)
    schema.CLIMATE_LABEL_VIEW_LIVE = False; e2._tick_dissonance(600.0)
    schema.CLIMATE_LABEL_VIEW_LIVE = True
    check("5d reservoirs identical flag on/off (dissonance reads live fields)",
          e1.dissonance.as_dict() == e2.dissonance.as_dict() and e1._contrib == e2._contrib, str(e1.dissonance.as_dict()))

    # 12h-12k: D-0451 integration knee on a real tick over seeded verdict-light events (fake accessor, isolated)
    _orig_light = store.get_light_events_by_source
    _lt = time.time()
    store.get_light_events_by_source = lambda sources, limit=300: [{"timestamp": _lt} for _ in range(150)]
    try:
        oik = schema.CLIMATE_LABEL_VIEW_INTEGRATION_K
        schema.CLIMATE_LABEL_VIEW_INTEGRATION_K = 148.0
        g_on = eng._compute_field()
        schema.CLIMATE_LABEL_VIEW_INTEGRATION_K = None
        g_off = eng._compute_field()
        schema.CLIMATE_LABEL_VIEW_INTEGRATION_K = oik
    finally:
        store.get_light_events_by_source = _orig_light
    raw_i = g_on.integration_drive * 100.0 / (1.0 - g_on.integration_drive)
    check("12h live integration on k=100 (~0.60) and identical with INTEGRATION_K on/off",
          abs(g_on.integration_drive - 0.6) < 2e-3 and abs(g_on.integration_drive - g_off.integration_drive) < 1e-4,
          f"{g_on.integration_drive} vs {g_off.integration_drive}")
    check("12i the nine live values and pressure() do not depend on INTEGRATION_K",
          all(abs(g_on.as_dict()[k] - g_off.as_dict()[k]) < 2e-3 for k in g_on.as_dict()) and g_on.pressure() == g_off.pressure())
    check("12j view integration = raw/(raw+148) on, = live value off",
          abs(g_on._label_view["integration_drive"] - raw_i / (raw_i + 148.0)) < 2e-3
          and g_off._label_view["integration_drive"] == g_off.integration_drive,
          f"on {g_on._label_view['integration_drive']} off {g_off._label_view['integration_drive']}")
    e3, e4 = ce.ClimateEngine(), ce.ClimateEngine()
    e3.field, e4.field = g_on, g_off
    for e in (e3, e4):
        e.dissonance = ce.DissonanceState(); e._explore_pull = lambda: 0.0
    e3._tick_dissonance(600.0); e4._tick_dissonance(600.0)
    check("12k reservoirs (incl. the integration bleed) identical with INTEGRATION_K on/off",
          e3.dissonance.as_dict() == e4.dissonance.as_dict() and e3._contrib == e4._contrib, str(e3.dissonance.as_dict()))

    eng.field = f_on
    d, val = eng.field.dominant()
    eng._log_label_promotion(d, val)
    p = ce._LABEL_PROMOTION_LOG
    rows = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []
    check("6a one old-vs-new row written to the redirected log", len(rows) == 1 and str(p).startswith(str(lab)), str(p))
    if rows:
        r = rows[0]
        check("6b row: old = live dominant, new = view dominant, read = printed, nofix present",
              r["old_dominant"] == f_on.dominant_live()[0] and r["new_dominant"] == max(lv, key=lv.get)
              and r["read_dominant"] == d and "nofix_dominant" in r and r["live"] is True
              and r["completion_k"] == schema.CLIMATE_LABEL_VIEW_COMPLETION_K and len(r["view"]) == 9, str(r))
        check("12l promotion row logs integration_k", r.get("integration_k") == schema.CLIMATE_LABEL_VIEW_INTEGRATION_K, str(r.get("integration_k")))
    fenced = profile._DATA / "climate_label_promotion_shadow.jsonl"
    existed = fenced.exists()
    redirected = ce._LABEL_PROMOTION_LOG
    ce._LABEL_PROMOTION_LOG = fenced
    eng._log_label_promotion(d, val)
    check("6c fenced path (this tree's data/) refused, nothing written", fenced.exists() == existed)
    ce._LABEL_PROMOTION_LOG = redirected

    eng._log_ignition(d, val, "defensive", {"strain": 0.0})
    ig = [json.loads(l) for l in Path(ce._IGNITION_LOG).read_text(encoding="utf-8").splitlines()]
    check("7a ignition row carries live_dominant beside the promoted dominant",
          ig[-1]["dominant"] == d and ig[-1].get("live_dominant") == f_on.dominant_live()[0], str(ig[-1]))
    rk = eng._compute_reknee_cluster(now, 134.0, 31.0, 90.0, 4.0, f_on)
    check("7b v=2 reknee row live_dominant stays the LIVE (k=3) dominant", rk["live_dominant"] == f_on.dominant_live()[0],
          str(rk["live_dominant"]))

    # ------------------------------------------------------------ (F)
    vec = [0.0] * 384; vec[5] = 1.0
    state_path = Path(lab) / "subconscious_state_j2248.json"

    def write_state(members):
        state_path.write_text(json.dumps({"tensions": [{
            "label": "mottainai waste scarcity tension", "centroid": vec,
            "member_event_ids": members}]}), encoding="utf-8")

    def resolved(eid):
        with store._connect() as conn:
            return conn.execute("SELECT resolved FROM shadow_events WHERE event_id=?", (eid,)).fetchone()["resolved"]

    def n_res(eid):
        with store._connect() as conn:
            return conn.execute("SELECT COUNT(*) c FROM resolution_events WHERE shadow_event_id=?", (eid,)).fetchone()["c"]

    def shadow_rows():
        sp = Path(store._SHADOW_RESOLVE_LOG)
        return [json.loads(l) for l in sp.read_text(encoding="utf-8").splitlines()] if sp.exists() else []

    async def yes(thought, label): return True
    async def no(thought, label): return False
    THOUGHT = "I have settled the mottainai waste question: scarcity asks care, not hoarding, and I choose that."

    def run(judge, members):
        write_state(members)
        tl._judge_resolution = judge
        return asyncio.run(tl.check_and_resolve_internal_tension(
            THOUGHT, about="mottainai waste", vec=vec, cycle_id="monologue", state_path=state_path))

    schema.TENSION_JUDGE_RESOLVES_SHADOW = True
    base_rows = len(shadow_rows())
    out = run(no, ["EV010", "EV011"])
    check("9 judge refuted -> nothing resolved, no row, no resolution_event",
          out is None and resolved("EV010") == 0 and len(shadow_rows()) == base_rows and n_res("EV010") == 0)
    out = run(yes, ["EV010", "EV011", "EV-MISSING"])
    new = shadow_rows()[base_rows:]
    check("8a judge confirmed -> members resolved=1", out is not None and resolved("EV010") == 1 and resolved("EV011") == 1)
    check("8b one row per resolved member, path=tension_judge, label + thought present",
          len(new) == 2 and all(r["path"] == "tension_judge" and r["tension_label"].startswith("mottainai")
                                and r["resolving_thought"].startswith("I have settled") and r["n_members"] == 3
                                for r in new), str(new))
    check("8c resolution_events still written for every member (incl. the missing id)",
          n_res("EV010") == 1 and n_res("EV011") == 1 and n_res("EV-MISSING") == 1)
    check("8d untouched events stay unresolved", resolved("EV012") == 0)

    schema.TENSION_JUDGE_RESOLVES_SHADOW = False
    k = len(shadow_rows())
    out = run(yes, ["EV020"])
    check("10 flag off -> resolution_event written, not resolved, no row",
          out is not None and n_res("EV020") == 1 and resolved("EV020") == 0 and len(shadow_rows()) == k)
    schema.TENSION_JUDGE_RESOLVES_SHADOW = True

    store.resolve_shadow_on_encounter("EV030", "rid", "cyc", 0.9)
    last = shadow_rows()[-1]
    check("11 (A) caller row has exactly the prior key set",
          set(last) == {"ts", "event_id", "resolution_id", "cycle_id", "similarity", "source", "emotion_primary",
                        "theme", "event_ts", "event_age_h"}, str(sorted(last)))

schema.CLIMATE_LABEL_VIEW_LIVE = orig_flag
c1 = canary()
check("live canary unchanged (DB + 4 live logs)", c0 == c1, f"{c0} -> {c1}")
print("\nRESULT:", "ALL PASS" if not FAILS else f"{len(FAILS)} FAIL: {FAILS}")
sys.exit(1 if FAILS else 0)
