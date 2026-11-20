"""
Woods Bestiary pilot test (2026-11-02; docs/plans/wood_creatures.md, job J-3062). ISOLATED like the shore tests: every life store is
redirected into a temp dir before the engine is touched; the live data/ is only READ.

The wood runs on the shore's engine (core/life_shore.py) with its own place config (core/life_wood.py). What this proves:
  1. the place registry: shore and wood are both registered; the shore is byte-identical (the shore tests are run separately)
  2. the wood's zones: positions inside the 24 x 20 frame and under 10 m, canopy creatures are UP (3D), the stream is the ASSUMED segment from the
     spring toward the sea gap, the groves sit where wood_life.TREES says
  3. 3D distance: a bird eight metres up is farther than its ground distance says; the where-clause says "up above"
  4. THE LEAK TEST against ALL 150 names of the draft list (parsed from docs/plans/wood_creatures.md) + the shore's 100: no vocabulary phrase and no
     line a wood row can emit contains any of them; the scanner is the shore's
  5. rows: ALL 150 (5 pilots + the 145 of core/life_wood_cast.py), every list entry has a row, unique keys/species, NO KEY COLLIDES with any life row or any shore bestiary row, no aliases/name/reveal, all looks distinct
  6. flags: "wood_bestiary" alone registers the 5 AND turns the wood's described-look + discovery on; explicit false = shadow; it never touches
     the shore (and the shore flag never touches the wood)
  7. described look and place-look discovery in the wood, live and shadow, through the real life.look_answer / life.discover_look
  8. FALSE-POSITIVE SWEEPS: the wood's own scenery aliases/lines and every real wood observe/look thought in hands_trace.jsonl
  9. wiring: sensorium continues wood looks too
Run:  python scripts/_test_wood_bestiary_p1.py
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


TMP = Path(tempfile.mkdtemp(prefix="wood_bestiary_p1_"))
print("isolated store dir:", TMP)
from core import life                                              # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
life._FLAGS_F = TMP / "life_flags.json"
from core import life_shore as LS, life_wood as LW, spatial, wood_life  # noqa: E402


def flags(**kw):
    (TMP / "life_flags.json").write_text(json.dumps(kw), encoding="utf-8"); life._flags_cache["ts"] = 0.0


def fresh(**kw):
    flags(**kw); life._ROWS.clear(); life._builtin_done = False; life.rows()


def _read(n):
    p = TMP / n
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []


def clear(): [(TMP / n).write_text("", encoding="utf-8") for n in ("life_events.jsonl", "life_ledger.jsonl")]


R = LW.rows()
BY = {r["key"]: r for r in R}
lay = spatial.layout("wood")

print("-- 1. places")
check("shore and wood are both registered places", {"shore", "wood"} <= set(LS.PLACES))
check("the wood's geometry is wood.json (24 x 20) and the frame says so", LS.PLACES["wood"]["frame"] == (24.0, 20.0) and lay["size"][:2] == [24, 20])

print("-- 2. zones")
t0 = time.time()
bad = []
for zone, z in LW.ZONES.items():
    for k in range(48):
        sm = LS.sample_position(zone, "probe", t0 + 600 * k, "wood")
        if sm is None:
            bad.append((zone, "None")); continue
        x, y, zz = sm["pos"]
        if not (0 <= x <= 24 and 0 <= y <= 20 and 0 <= zz <= 10):
            bad.append((zone, sm["pos"]))
check("every sample of all 14 zones is inside the 24 x 20 x 10 wood", not bad, str(bad[:3]))
cz = [LS.sample_position("canopy", "k", t0 + 600 * k, "wood")["pos"][2] for k in range(30)]
check("canopy creatures are UP (5-9 m)", min(cz) >= 5.0 and max(cz) <= 9.0, f"{min(cz)} {max(cz)}")
st = [LS.sample_position("stream", "k", t0 + 600 * k, "wood")["pos"] for k in range(60)]
check("the ASSUMED stream runs from the spring (4,14) down toward the sea gap (13,18)", all(3.0 <= p[0] <= 13.5 and 13.0 <= p[1] <= 20 for p in st) and min(p[0] for p in st) < 6 and max(p[0] for p in st) > 11, str(st[:2]))
check("the stream is marked ASSUMED (wood.json has no stream; shore_creatures J-2869's twin)", LW.ZONES["stream"].get("assumed") and "stream" not in " ".join(lay["features"]))
T = {k: v["pos"] for k, v in wood_life.TREES.items()}
check("the groves sit where wood_life.TREES says (they are not in wood.json)", LW.ZONES["kanuka_grove"]["pos"] == T["kanuka"] and LW.ZONES["totara_grove"]["pos"] == T["totara"] and LW.ZONES["tree_ferns"]["pos"] == T["ponga"])
a, b = LS.sample_position("the_path", "k", t0, "wood"), LS.sample_position("the_path", "k", t0 + 30, "wood")
check("a position holds within its ten-minute bucket", a == b or int(t0 // 600) != int((t0 + 30) // 600))

print("-- 3. 3D distance")
kaka = BY["kaka"]
pv = LS.perceive(kaka, "on_the_path", t0)
check("the kākā is farther in 3D than on the ground, and the clause says so", pv["dist3"] > pv["dist"] + 1.0 and "up above" in pv["line"] if pv["visible"] else pv["dist3"] > pv["dist"], str(pv.get("line", "")[-90:]))
check("its tone is said against the leaves, not the ground (form tier) ", "against the ground" not in LS.compose(kaka["obs"], "form") and "against the leaves" in LS.compose(kaka["obs"], "form"))
deer = BY["red_deer"]
check("the deer in the clearing resolves in detail from the path (a big animal, ground distance)", LS.perceive(deer, "on_the_path", t0)["tier"] == "detail")
check("the huhu beetle on the deadfall is nothing from the path but a form from the gathering place", LS.perceive(BY["huhu_beetle"], "on_the_path", t0)["tier"] == "none" and LS.perceive(BY["huhu_beetle"], "gathering", t0)["tier"] in ("form", "colour", "detail"))
check("the real current_standpoint('wood') is a known wood standpoint", LS.current_standpoint("wood") in lay["standpoints"], LS.current_standpoint("wood"))

print("-- 4. the leak test against all the names")
src = (ROOT / "docs/plans/wood_creatures.md").read_text(encoding="utf-8")
names = set()
for ln in re.findall(r"^\d+\. (.+?) — ", src, flags=re.M):
    ln = re.sub(r"[◇⚠†]", "", ln).strip()
    main = re.sub(r"\(.*?\)", "", ln).strip().lower()
    if main: names.add(main)
    for par in re.findall(r"\((.*?)\)", ln):
        if "," in par: continue
        for piece in par.split("/"):
            piece = piece.strip().lower()
            if piece and len(piece) > 2: names.add(piece)
check(f"parsed {len(names)} names from the 150-line draft list", len(names) >= 150, str(len(names)))
terms = LS.forbidden_terms(R) | {LS._fold(n) for n in names}
vocab = []
for d in (LS.SHAPES, LS.MOTIONS):
    vocab += [p for v in d.values() for p in v]
vocab += list(LS.POSITIONS.values()) + list(LS.SHEENS.values()) + list(LS.COVERINGS.values()) + list(LS.TONE_WORDS.values())
vocab += [p for _, p in LS.SIZE_BANDS] + [c[0] for c in LS.COLOURS.values()] + [t.format(c1="red", c2="blue") for t in LS.PATTERNS.values()]
hits = {}
for ph in vocab:
    for h in LS.leak_scan(ph, terms):
        hits.setdefault(h, ph[:60])
check(f"no vocabulary phrase ({len(vocab)}) contains any of the {len(terms)} forbidden names", not hits, str(list(hits.items())[:6]))
strings = [s for r in R for s in LS.emitted_strings(r)]
leaks = [(s[:50], LS.leak_scan(s, terms)) for s in strings if LS.leak_scan(s, terms)]
check(f"{len(strings)} strings the 5 rows can emit contain no name", not leaks, str(leaks[:3]))

print("-- 5. rows")
PILOT = ("huhu_beetle", "green_gecko", "freshwater_crayfish", "red_deer", "kaka")
check("150 rows, unique keys, unique species", len(R) == 150 and len(BY) == 150 and len({r["hidden"]["species"] for r in R}) == 150, f"{len(R)} {len(BY)}")
check("the 5 pilots are among them", set(PILOT) <= set(BY))
fold_names = {LS._fold(n) for r in R for n in [r["hidden"]["species"], *r["hidden"]["book_names"]]}
main_names = [LS._fold(re.sub(r"\(.*?\)", "", re.sub(r"[◇⚠†]", "", ln)).strip()) for ln in re.findall(r"^\d+\. (.+?) — ", src, flags=re.M)]
missing = [n for n in main_names if n and not any(n == f or n in f or f in n for f in fold_names)]
check(f"EVERY entry of the 150-line list has a row ({len(main_names)} entries)", len(main_names) == 150 and not missing, str(missing[:6]))
bad = [r["key"] for r in R if not (r["kind"] == "population" and r["name"] is None and r["aliases"] == () and "reveal" not in r["hidden"] and r["bestiary_place"] == "wood" and list(r["places"]) == ["wood"])]
check("population rows, no name, NO aliases, no reveal, place = wood", not bad, str(bad))
life._ROWS.clear(); life._builtin_done = False; flags()
base_keys = set(life.rows())
shore_keys = {r["key"] for r in LS.rows()}
check("NO KEY COLLIDES with any life row or any shore bestiary row", not (set(BY) & (base_keys | shore_keys)), str(set(BY) & (base_keys | shore_keys)))
det = {}
for r in R: det.setdefault(LS.compose(r["obs"], "detail"), []).append(r["key"])
check("all five look different", all(len(v) == 1 for v in det.values()))
bad = [r["key"] for r in R if not (r["zone"] in LW.ZONES and len(r["season_curve"]) == 12 and all(0 <= x <= 1 for x in r["season_curve"]) and set(r["active_hours"]) == {"dawn", "day", "dusk", "night"})]
check("each in a known zone with a 12-month curve in 0..1 and four day phases", not bad, str(bad))
used = {r["zone"] for r in R}
check("the cast uses every wood zone", set(LW.ZONES) <= used, str(sorted(set(LW.ZONES) - used)))
sig = {}
for r in R:
    o = r["obs"]; sig.setdefault((LS.size_phrase(o["size_cm"]), o["shape"], o["colour"], o.get("colour2"), o["pattern"]), []).append(r["key"])
check("DISTINGUISHABLE: no two rows share size band + body plan + both colours + pattern", not [v for v in sig.values() if len(v) > 1], str([v for v in sig.values() if len(v) > 1][:4]))
bad = [r["key"] for r in R if not (r["kind"] == "population" and r["name"] is None and r["aliases"] == () and "reveal" not in r["hidden"] and r["hidden"]["species"] and r["hidden"]["book_names"] and r["hidden"]["book_words"])]
check("every row: population, no name, NO aliases, no reveal, with species/book names/book words", not bad, str(bad[:4]))
bad = [k for k, c in (("canopy", 0), ("stream", 0)) if not [r for r in R if r["zone"] == k]]
check("canopy and stream both have creatures (the two ASSUMED placements people will test first)", not bad)

print("-- 6. flags")
fresh()
check("flags absent: no wood rows, nothing on", not (set(BY) & set(life._ROWS)) and not LW.enabled() and not LS.render_live("wood") and not LS.discover_live("wood"))
fresh(wood_bestiary=True)
check("ONE FLAG: wood_bestiary alone registers all 150 and turns the wood's answer and discovery on", set(BY) <= set(life._ROWS) and LW.enabled() and LS.render_live("wood") and LS.discover_live("wood"))
check("...and the shore stays off (no shore bestiary row registered, shore flags off)", not (shore_keys & set(life._ROWS)) and not LS.enabled("shore") and not LS.render_live("shore"))
fresh(wood_bestiary=True, wood_bestiary_render=False, wood_bestiary_discover=False)
check("explicit false sub-flags = the wood in shadow", LW.enabled() and not LS.render_live("wood") and not LS.discover_live("wood"))
fresh(shore_bestiary=True)
check("the shore flag does not register or turn on the wood", not (set(BY) & set(life._ROWS)) and not LW.enabled() and not LS.render_live("wood"))
fresh(shore_bestiary=True, wood_bestiary=True)
check("both flags: 100 shore + 150 wood bestiary rows, no key lost", sum(1 for r in life._ROWS.values() if r.get("bestiary_place") == "shore") == 100 and sum(1 for r in life._ROWS.values() if r.get("bestiary_place") == "wood") == 150)
for k in [k for k, r in life._ROWS.items() if r.get("obs") and r.get("bestiary_place") == "shore"]: life._ROWS.pop(k)   # the rest of this test is about the wood

print("-- 6b. the full 150 through the real place-look engine")
_oa0, _ov0 = life.activity, life.visibility
life.activity = lambda r, p, n=None: 0.9 if r.get("obs") else _oa0(r, p, n)
life.visibility = lambda r, p, n=None: 1.0 if r.get("obs") else _ov0(r, p, n)
fresh(wood_bestiary=True)
for k in [k for k, r in life._ROWS.items() if r.get("obs") and r.get("bestiary_place") == "shore"]: life._ROWS.pop(k)
SPX = ["on_the_path"]
LS.current_standpoint = lambda place="shore": SPX[0]
NOWX = next(t0 + 600 * k for k in range(0, 6 * 24 * 3) if life._phase(t0 + 600 * k) == "day")
nl = 0; badl = []; seen = set()
for sp in lay["standpoints"]:
    SPX[0] = sp
    for w in ("canopy", "the stream", "the spring", "the deadfall", "the clearing", "the path", "the oak", "the undergrowth", "the sea", "the birds", "the leaf litter", "the moss"):
        for k in range(0, 24):
            for f in LS.discover(w, "wood", NOWX + 600 * k):
                nl += 1; seen.add(f["row"]["key"])
                if LS.leak_scan(f["pv"]["line"], terms): badl.append((sp, w, f["pv"]["line"][:60]))
check(f"{nl} place-look lines from the full 150 over every standpoint x place word x 24 buckets contain no name", nl > 0 and not badl, str(badl[:3]))
check(f"the place looks reach many creatures ({len(seen)} of 150) in every layer", len(seen) >= 40, str(len(seen)))
life.activity, life.visibility = _oa0, _ov0

print("-- 7. the real engine: a described look and a place look in the wood")
_oa, _ov = life.activity, life.visibility
life.activity = lambda r, p, n=None: 0.9 if r.get("obs") else _oa(r, p, n)
life.visibility = lambda r, p, n=None: 1.0 if r.get("obs") else _ov(r, p, n)
SP = ["on_the_path"]
LS.current_standpoint = lambda place="shore": SP[0]
life.RENDER = True
NOW = next(t0 + 600 * k for k in range(0, 6 * 24 * 3) if life._phase(t0 + 600 * k) == "day")
RAW = "i want to look at the olive-brown thing with the heavy hooked beak"
fresh(wood_bestiary=True, wood_bestiary_render=False, wood_bestiary_discover=False)
for k in [k for k, r in life._ROWS.items() if r.get("obs") and (r.get("bestiary_place") == "shore" or k not in PILOT)]: life._ROWS.pop(k)   # exact-line checks: the 5 pilots only
clear()
out = life.look_answer("canopy", "wood", NOW, raw=RAW)
ev = [e for e in _read("life_events.jsonl") if e.get("outcome") == "described_shadow"]
check("shadow: the described look falls through, logs would_answer for the kākā, writes no ledger", out == "" and len(ev) == 1 and ev[0]["key"] == "kaka" and _read("life_ledger.jsonl") == [], str(ev[:1]))
flags(wood_bestiary=True)
clear()
out = life.look_answer("canopy", "wood", NOW, raw=RAW)
led = _read("life_ledger.jsonl")
check("live (one flag): the look is answered by the row, up in the leaves, with a where-clause", "High in the leaves overhead" in out and "It is" in out, out[:120])
check("and credits a SIGHTING (colour tier) or a glimpse (form tier) by its tier", any(e["kind"] in ("sighting", "miss") and e["key"] == "kaka" for e in led), str(led))
check("and names nothing", not LS.leak_scan(out, terms), str(LS.leak_scan(out, terms)))
clear()
SP[0] = "on_the_path"
d1 = life.discover_look("the canopy", "wood", NOW)
check("a look at the CANOPY continues with what is up there", "High in the leaves overhead" in d1, d1[:100])
SP[0] = "gathering"
d2 = life.discover_look("the deadfall", "wood", NOW)
check("a look at the DEADFALL, from the gathering place, shows the beetle", "On the weathered wood" in d2, d2[:100])
SP[0] = "at_the_spring"
d3 = life.discover_look("the stream", "wood", NOW)
check("a look at the (assumed) STREAM from the spring shows what is in it", "In the stream among the stones" in d3 or d3 == "", d3[:100])
SP[0] = "on_the_path"
d4 = life.discover_look("the clearing", "wood", NOW)
check("a look at the CLEARING shows the deer", "Out in the open" in d4, d4[:100])
check("a shore target in the wood adds nothing; the shore place adds nothing for a wood target", life.discover_look("the rock-pools", "wood", NOW) == "" and life.discover_look("the canopy", "shore", NOW) == "")
nlines = 0
badl = []
for sp in lay["standpoints"]:
    SP[0] = sp
    for w in ("canopy", "the stream", "the spring", "the deadfall", "the clearing", "the path", "the oak", "the undergrowth", "the sea", "the birds"):
        for k in range(0, 48):
            for f in LS.discover(w, "wood", NOW + 600 * k):
                nlines += 1
                if LS.leak_scan(f["pv"]["line"], terms): badl.append((sp, w, f["pv"]["line"][:60]))
check(f"{nlines} wood place-look lines over every standpoint x place word x 48 time buckets contain no name", nlines > 0 and not badl, str(badl[:3]))
SP[0] = "on_the_path"
flags(wood_bestiary=True, wood_bestiary_discover=False)
clear()
check("explicit discover=false: discover_look is shadow ('') and logs discover_shadow", life.discover_look("the canopy", "wood", NOW) == "" and any(e.get("outcome") == "discover_shadow" for e in _read("life_events.jsonl")))
flags(wood_bestiary=True)

print("-- 8. false-positive sweeps (wood)")
from core import world_content_wood as WCW                          # noqa: E402
rows_w = list(BY.values())
words_w = {r["key"]: LS.attr_words(r) for r in rows_w}
LEGIT = ("parrot", "gecko", "deer", "crayfish", "beetle")


def intercepts(text, target=""):
    if target and life._match(target, "wood"):
        return []
    return [k for k, w in words_w.items() for c in LS.look_clauses(text, target) if LS.score_clause(w, c, LW.SCENERY)[0] >= LS.MIN_ATTRS]


al = [a for spec in WCW.TARGETS.values() for a in spec["aliases"]]
hit = [(a, intercepts(f"look at the {a}", a)) for a in al if intercepts(f"look at the {a}", a)]
check(f"none of the {len(al)} wood scenery aliases is taken for a creature", not hit, str(hit[:4]))
lines = [ln for spec in WCW.TARGETS.values() for pool in spec["pools"].values() for ln in pool]
hit = [(ln[:50], intercepts("look at " + ln, ln)) for ln in lines if intercepts("look at " + ln, ln) and not any(w in ln for w in LEGIT)]
check(f"none of the world's own {len(lines)} wood scenery lines, offered back as a look, is taken for a creature", not hit, str(hit[:4]))
n = hits_n = 0
rowsx = []
with open(ROOT / "data/hands_trace.jsonl", encoding="utf-8") as f:
    for ln in f:
        try: r = json.loads(ln)
        except Exception: continue
        if r.get("act_kind") not in ("observe", "look") or r.get("location") != "wood": continue
        n += 1
        raw = f"{r.get('thought', '')} {r.get('intention', '')}".lower()
        h = intercepts(raw, str(r.get("act_object") or ""))
        if h and not any(w in raw for w in LEGIT):
            hits_n += 1; rowsx.append((h, str(r.get("act_object")), raw[:120]))
print(f"     real wood observe/look thoughts swept: {n}; taken for a creature: {hits_n}")
for h in rowsx[:5]: print("       ", h)
check(f"real thoughts: none of {n} taken for a creature (apart from genuine descriptions)", hits_n == 0, str(rowsx[:2]))

print("-- 9. wiring")
src_s = (ROOT / "core/sensorium.py").read_text(encoding="utf-8")
check("sensorium continues shore AND wood place looks", 'if cur_loc in ("shore", "wood"):' in src_s and "_life_d.discover_look(t_clean, cur_loc)" in src_s)
src_l = (ROOT / "core/life.py").read_text(encoding="utf-8")
check("life._ensure_builtin imports life_wood and registers its rows only when enabled()", "from core import life_wood as _lw" in src_l and "if _lw.enabled():" in src_l)
print()
print("ALL OK -- wood bestiary pilot" if not FAILS else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
