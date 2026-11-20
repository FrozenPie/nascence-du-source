"""
Shore Bestiary P1 pilot test (2026-11-01; docs/staged/shore_creatures.md). ISOLATED: every life store is redirected into a
temp dir before the engine is touched (the life_smoke pattern) -- the live data/ is never written.

What it proves:
  1. the closed vocabularies reject a word that is not in them
  2. detail_tier: the sea lion reads at a distance, the pipi only at arm's length; the tiers are ordered
  3. compose(): each tier adds information and the `form` tier has no colour word; night drops the tone
  4. THE LEAK TEST: nothing a pilot row can emit -- and no word in the whole vocabulary -- contains a species, a book name or
     a common/category name of the 100; the scanner itself catches a planted name, folds accents and respects word edges
  5. zones: positions are inside the authored 30 x 20 frame, deterministic per ten-minute bucket, tide-consistent
     (the pool and the flat close when the tide is over them; the flat stays landward of the moving waterline); the stream
     mouth is a feature of shore.json (D-0651, J-3260: a disc r 2.0 on `stream_mouth`, x 14-16), and adding it leaves spatial.render alone
  6. perceive(): the same sea lion resolves to more from nearer, and from the standpoint's own egocentric distance
  7. the rows are population rows with NO aliases, NO name and NO reveal caption; they are NOT registered by default; the
     shore_bestiary flag registers them through life._ensure_builtin; an existing alias ('starfish' -> anemones) is unchanged
  8. the existing naming law still works on them: a book alone does not name them, a sighting + a book does (D-0129)
Run:  python scripts/_test_shore_bestiary_p1.py
"""
from __future__ import annotations

import json
import math
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


TMP = Path(tempfile.mkdtemp(prefix="shore_bestiary_p1_"))
print("isolated store dir:", TMP)
from core import life                                              # noqa: E402
life._F, life._LEDGER, life._EVENTS = TMP / "life_state.json", TMP / "life_ledger.jsonl", TMP / "life_events.jsonl"
life._DATA = TMP
life._FLAGS_F = TMP / "life_flags.json"
life._flags_cache["ts"] = 0.0
from core import life_shore as LS                                  # noqa: E402
from core import spatial, world_clock                              # noqa: E402

R = LS.rows()
BY = {r["key"]: r for r in R}

print("-- 1. closed vocabularies")
good = dict(size_cm=5, shape="hinged_pair", colour="cream", pattern="plain", sheen="matt", covering="smooth",
            motion="still", position="pool_floor", on_disturb="ignores")
check("a valid tuple passes", LS.make_obs(**good)["span_cm"] == 5)
for field, bad in (("shape", "crab_shaped"), ("colour", "ochre"), ("motion", "scuttles"), ("on_disturb", "bolts")):
    try:
        LS.make_obs(**{**good, field: bad}); ok = False
    except ValueError:
        ok = True
    check(f"unknown {field} {bad!r} is refused", ok)
try:
    LS.make_obs(**{**good, "pattern": "banded"}); ok = False
except ValueError:
    ok = True
check("a non-plain pattern without colour2 is refused", ok)
try:
    LS.make_obs(**{k: v for k, v in good.items() if k != "motion"}); ok = False
except ValueError:
    ok = True
check("a missing field is refused", ok)

print("-- 2. detail_tier")
check("sea lion (210 cm) shows colour at 40 m", LS.detail_tier(210, 40) == "colour", LS.detail_tier(210, 40))
check("sea lion shows full detail at 12 m", LS.detail_tier(210, 12) == "detail")
check("sea lion is still a form at 100 m", LS.detail_tier(210, 100) == "form")
check("pipi (6 cm) is nothing at 5 m", LS.detail_tier(6, 5) == "none")
check("pipi shows only form at 2.5 m, colour at 1.2 m, detail at 0.4 m",
      (LS.detail_tier(6, 2.5), LS.detail_tier(6, 1.2), LS.detail_tier(6, 0.4)) == ("form", "colour", "detail"),
      str((LS.detail_tier(6, 2.5), LS.detail_tier(6, 1.2), LS.detail_tier(6, 0.4))))
ds = [LS.detail_tier(20, d) for d in (0.5, 2, 4, 8, 20)]
check("tiers only get poorer with distance", [LS.TIERS.index(t) for t in ds] == sorted((LS.TIERS.index(t) for t in ds), reverse=True), str(ds))

print("-- 3. compose")
sl = BY["sea_lion"]["obs"]; sf = BY["eleven_armed_starfish"]["obs"]
form, col, det = (LS.compose(sf, t) for t in ("form", "colour", "detail"))
check("the detail tier says the most; colour swaps tone for the colours themselves", len(det) > len(form) and len(det) > len(col), f"{len(form)}/{len(col)}/{len(det)}")
check("form carries a tone, colour carries colours, neither carries the other", "against the ground" in form and "against the ground" not in col)
check("form tier names no colour", not any(w in form for w in ("orange", "cream", "brown")), form)
check("colour tier names the colours", "orange" in col and "cream" in col, col)
check("detail tier counts the arms and says the covering", "eleven arms" in det and "spines" in det, det)
check("night form drops the tone", "against the ground" not in LS.compose(sf, "form", night=True))
check("tier none is empty", LS.compose(sf, "none") == "")
check("size is said against his body, never as a number", not any(ch.isdigit() for ch in det) and "about as long as you are" in LS.compose(sl, "form"))

print("-- 4. the leak test")
terms = LS.forbidden_terms(R)
strings = [s for r in R for s in LS.emitted_strings(r)]
leaks = [(s[:60], LS.leak_scan(s, terms)) for s in strings if LS.leak_scan(s, terms)]
check(f"{len(strings)} emitted strings from {len(R)} rows contain no name", not leaks, str(leaks[:3]))
vocab_strings = []
for d in (LS.SHAPES, LS.MOTIONS):
    vocab_strings += [p for v in d.values() for p in v]
vocab_strings += list(LS.POSITIONS.values()) + list(LS.SHEENS.values()) + list(LS.COVERINGS.values()) + list(LS.TONE_WORDS.values())
vocab_strings += [p for _, p in LS.SIZE_BANDS] + [c[0] for c in LS.COLOURS.values()]
vocab_strings += [t.format(c1="red", c2="blue") for t in LS.PATTERNS.values()]
vleaks = [(s[:50], LS.leak_scan(s, terms)) for s in vocab_strings if LS.leak_scan(s, terms)]
check(f"all {len(vocab_strings)} vocabulary phrases contain no name", not vleaks, str(vleaks[:3]))
check("scanner catches a planted common name", LS.leak_scan("a small crab sidles off", terms) == ["crab"])
check("scanner catches a plural and a category word", "fish" in LS.leak_scan("three fishes", terms) or "fish" in LS.leak_scan("a fish", terms))
check("scanner folds accents (Rāpoka)", "rapoka" in LS.leak_scan("the Rāpoka hauls out", terms))
check("scanner respects word edges ('pipistrelle' is not 'pipi'; 'rays' is not 'ray')",
      not LS.leak_scan("a pipistrelle with rays", terms))
check("the row's own species and book names are in the forbidden set",
      {"pipi", "sea lion", "coscinasterias"} <= terms)

print("-- 5. zones")
lay = spatial.layout("shore")
sf = lay["features"].get("stream_mouth")
check("shore.json has the stream_mouth feature (D-0651), x 14-16, east of driftwood_tangle and west of rock_pools",
      bool(sf) and 14.0 <= sf["pos"][0] <= 16.0 and lay["features"]["driftwood_tangle"]["pos"][0] < sf["pos"][0] < lay["features"]["rock_pools"]["pos"][0], str(sf))
check("ZONES['stream_mouth'] is a disc on that feature, r 2.0 (the ruling)",
      LS.ZONES["stream_mouth"] == {"mode": "disc", "anchor": "stream_mouth", "r": 2.0}, str(LS.ZONES["stream_mouth"]))
t0 = time.time()
SM_KEYS = [r["key"] for r in R if r["zone"] == "stream_mouth"]
check("the stream-mouth creatures are there (inanga, eels, gambusia, sea-run trout, salmon, hairy-handed crab, lamprey, spoonbill ...)", len(SM_KEYS) >= 8, str(SM_KEYS))
sm = [LS.sample_position("stream_mouth", k, t0 + i * 3600) for k in SM_KEYS for i in range(12)]
ax, ay = sf["pos"][0], sf["pos"][1]
check("sample_position returns coordinates for every stream-mouth creature at every hour, inside 2.0 m of the mouth (positions are rounded to 1 cm) and inside the frame",
      all(s and not s["out_of_frame"] and math.hypot(s["pos"][0] - ax, s["pos"][1] - ay) <= 2.0 + 0.02 and 0 <= s["pos"][0] <= 30 and 0 <= s["pos"][1] <= 20 for s in sm), str(sm[:2]))
check("a stream-mouth position holds for the ten-minute bucket and is the same per (row, bucket)",
      LS.sample_position("stream_mouth", SM_KEYS[0], t0 // 600 * 600 + 5) == LS.sample_position("stream_mouth", SM_KEYS[0], t0 // 600 * 600 + 500))
check("zone_ref is the mouth itself", LS.zone_ref("stream_mouth")[:2] == [ax, ay])
check("a standpoint reaches it (the defeater: nearest authored standpoint within 5 m)", LS.zone_vantage_distance("stream_mouth") <= 5.0, str(LS.zone_vantage_distance("stream_mouth")))

print("-- 5b. adding the feature leaves spatial.render alone (D-0651's check), via the patch script on temp copies")
import importlib.util, random                                      # noqa: E402
spec = importlib.util.spec_from_file_location("apply_shore_stream_mouth_j3260", ROOT / "scripts" / "apply_shore_stream_mouth_j3260.py")
PATCH = importlib.util.module_from_spec(spec); spec.loader.exec_module(PATCH)
geo_a, geo_b = TMP / "geo_without", TMP / "geo_with"
geo_a.mkdir(); geo_b.mkdir()
CRLF, LF = bytes([13, 10]), bytes([10])
src_raw = (ROOT / "data" / "world_geometry" / "shore.json").read_bytes()
j = json.loads(src_raw.decode("utf-8")); j["features"].pop("stream_mouth", None)
eol = CRLF if CRLF in src_raw else LF
(geo_a / "shore.json").write_bytes(json.dumps(j, indent=2, ensure_ascii=False).encode("utf-8").replace(LF, eol))
(geo_b / "shore.json").write_bytes((geo_a / "shore.json").read_bytes())
check("patch dry run changes nothing", "dry run" in PATCH.apply(geo_b / "shore.json", False) and (geo_b / "shore.json").read_bytes() == (geo_a / "shore.json").read_bytes())
check("patch --write adds the feature and backs the file up", "added" in PATCH.apply(geo_b / "shore.json", True) and len(list(geo_b.glob("shore.json.bak_J-3260_*"))) == 1)
check("patch is idempotent", "already present" in PATCH.apply(geo_b / "shore.json", True))
ja, jb = json.loads((geo_a / "shore.json").read_text(encoding="utf-8")), json.loads((geo_b / "shore.json").read_text(encoding="utf-8"))
new_f = jb["features"].pop("stream_mouth")
check("patch is additive-only: the rest of the file is identical", ja == jb and new_f["pos"] == [15.0, 7.0, 0.0])
nb = (geo_b / "shore.json").read_bytes()
check("patch keeps the file's newline style", nb.count(CRLF) == (nb.count(LF) if eol == CRLF else 0))


def _scene_set(geo_dir):
    real_time, real_geo, real_shadow = time.time, spatial._GEO, spatial._SHADOW
    time.time = lambda: 1793000000.0                                # a frozen clock (tide + sun) so the two runs are comparable
    spatial._GEO, spatial._SHADOW = geo_dir, TMP / "spatial_shadow_J-3260.jsonl"
    spatial._layout_cache.pop("shore", None)
    try:
        out = {}
        for sp in ("on_the_shingle", "at_the_tideline", "at_the_pools", "by_the_driftwood", "in_the_cave"):
            random.seed(7); r = spatial.render("shore", sp)
            random.seed(7); b = spatial._render_base("shore", sp)
            out[sp] = (r, b, spatial.depth("shore", sp))
        return out
    finally:
        time.time, spatial._GEO, spatial._SHADOW = real_time, real_geo, real_shadow
        spatial._layout_cache.pop("shore", None)


SA, SB = _scene_set(geo_a), _scene_set(geo_b)
check("spatial.render / _render_base / depth are byte-identical at 5 standpoints with and without the stream_mouth feature", SA == SB,
      str([k for k in SA if SA[k] != SB[k]]))

t0 = time.time()
check("waterline_y equals spatial's own", LS.waterline_y(t0) == spatial._waterline_pos(lay, t0)[1])
W, H = LS.FRAME
bad_frame, pool_closed, pool_open, pool_bad, flat_open, flat_seaward = 0, 0, 0, 0, 0, 0
for i in range(0, 26 * 6):                                   # 26 hours in ten-minute steps: a full tide cycle plus
    t = t0 + i * 600
    lv = world_clock.tide(t)["level"]
    for zone in ("pool", "flat", "mussel_shelf", "rock_shelf", "dune", "shingle", "driftwood"):
        s = LS.sample_position(zone, "probe", t)
        if zone == "pool":
            if s is None:
                pool_closed += 1
                pool_bad += (lv <= 0.60)                     # closed while its gate says open
            else:
                pool_open += 1
                pool_bad += (lv > 0.60)                      # open while the tide is over it
        if s is None:
            continue
        x, y, _ = s["pos"]
        if not (0 <= x <= W and 0 <= y <= H): bad_frame += 1
        if zone == "flat":
            flat_open += 1
            if y > LS.waterline_y(t) - 0.2 + 1e-9: flat_seaward += 1
            if lv > 0.45: flat_seaward += 1
check("every disc-zone sample is inside the 30 x 20 frame", bad_frame == 0, str(bad_frame))
check("the pool opens AND closes over a tide cycle, exactly on its gate", pool_open > 0 and pool_closed > 0 and pool_bad == 0, f"open={pool_open} closed={pool_closed} bad={pool_bad}")
check("the flat opens over a tide cycle and every sample is landward of the waterline and below its gate", flat_open > 0 and flat_seaward == 0, f"open={flat_open} bad={flat_seaward}")
a = LS.sample_position("rock_shelf", "k", t0); b = LS.sample_position("rock_shelf", "k", t0 + 30)
tb = (int(t0 // LS.BUCKET_S) + 1) * LS.BUCKET_S + 1
c = LS.sample_position("rock_shelf", "k", tb)
check("a position holds within its ten-minute bucket (30 s apart, same place)", a == b or int(t0 // 600) != int((t0 + 30) // 600), f"{a} {b}")
check("it moves in a later bucket", any(LS.sample_position("rock_shelf", "k", tb + 600 * j)["pos"] != a["pos"] for j in range(4)) and c is not None)
tl = [LS.sample_position("tideline", "k", t0 + i * 3600) for i in range(12)]
check("the tideline sits on the moving waterline", all(abs(s["pos"][1] - LS.waterline_y(t0 + i * 3600)) <= 0.41 for i, s in enumerate(tl)))
off = [LS.sample_position("offshore", "k", t0 + i * 600) for i in range(30)]
check("offshore is seaward of the waterline and mostly beyond the 20 m frame", all(s["pos"][1] > LS.waterline_y(t0) - 0.1 for s in off) and sum(s["out_of_frame"] for s in off) >= 20)

print("-- 6. perceive")
sealion = BY["sea_lion"]
rocks_near = LS.perceive(sealion, "on_the_rocks", t0)
foot_far = LS.perceive(sealion, "at_the_path_foot", t0)
check("the sea lion resolves from the shelf", rocks_near["visible"] and rocks_near["tier"] == "detail", str(rocks_near.get("tier")))
check("from the path foot the same animal gives less", LS.TIERS.index(foot_far["tier"]) < LS.TIERS.index(rocks_near["tier"]), f"{foot_far['tier']} vs {rocks_near['tier']}")
check("the line carries an egocentric where-clause", " It is " in rocks_near["line"] and rocks_near["line"].endswith("."), rocks_near["line"][-60:])
rel = spatial._rel(lay["standpoints"]["at_the_path_foot"], foot_far["pos"])
check("its distance is spatial's own egocentric distance", abs(rel["dist"] - foot_far["dist"]) < 1e-6)
check("pace words grow with distance", [LS.pace_word(d) for d in (1, 3, 8, 20, 60)] ==
      ["within arm's reach", "a few paces off", "a dozen paces or so off", "a good way off", "a long way off"])
closed = None
for i in range(0, 26 * 6):
    t = t0 + i * 600
    if world_clock.tide(t)["level"] > 0.45:
        closed = LS.perceive(BY["pipi"], "on_the_sand", t); break
check("a closed zone shows nothing and says why", closed is not None and not closed["visible"] and closed["reason"] == "zone_closed")
leakp = [LS.leak_scan(LS.perceive(sealion, sp, t0 + k)["line"], terms) for sp in lay["standpoints"] for k in (0, 7200)]
check("perceive() lines from every authored standpoint contain no name", not any(leakp), str([x for x in leakp if x][:3]))

print("-- 7. rows and registration")
check("100 rows, unique keys, unique species", len(R) == 100 and len(BY) == 100 and len({r["hidden"]["species"] for r in R}) == 100, f"{len(R)} {len(BY)}")
bad = [r["key"] for r in R if not (r["kind"] == "population" and r["name"] is None and r["aliases"] == () and "reveal" not in r["hidden"])]
check("every row: population, no name, NO aliases, no reveal caption", not bad, str(bad[:5]))
bad = [r["key"] for r in R if not (r["hidden"]["species"] and r["hidden"]["book_names"] and r["hidden"]["book_words"])]
check("every row has a species, book names and book words (so a book can name it)", not bad, str(bad[:5]))
bad = [r["key"] for r in R if not (set(r["hidden"]["feature"]) <= {"dawn", "day", "dusk", "night"})]
check("static feature lines (P1 placeholders; P2/P3 compose per look) use only real phases", not bad, str(bad[:5]))
bad = [r["key"] for r in R if not (r["zone"] in LS.ZONES and LS.ZONES[r["zone"]]["mode"] != "pending" and r["places"]["shore"] == [r["zone"]])]
check("every row sits in a known, placed zone", not bad, str(bad[:5]))
bad = [r["key"] for r in R if not (len(r["season_curve"]) == 12 and all(0 <= x <= 1 for x in r["season_curve"]) and set(r["active_hours"]) == {"dawn", "day", "dusk", "night"})]
check("every row: a 12-month season curve in 0..1 and all four day phases", not bad, str(bad[:5]))
used = {r["zone"] for r in R}
check("the cast uses every zone but the empty ones", {"pool", "flat", "mussel_shelf", "rock_shelf", "dune", "shingle", "tideline", "surf", "offshore", "stream_mouth", "cave", "driftwood"} <= used, str(sorted(used)))
sig = {}
for r in R:
    o = r["obs"]; sig.setdefault((LS.size_phrase(o["size_cm"]), o["shape"], o["colour"], o.get("colour2"), o["pattern"]), []).append(r["key"])
dup = [v for v in sig.values() if len(v) > 1]
check("DISTINGUISHABLE: no two rows share size band + body plan + both colours + pattern (he could not tell them apart)", not dup, str(dup[:5]))
det = {}
for r in R:
    det.setdefault(LS.compose(r["obs"], "detail"), []).append(r["key"])
check("and no two rows compose the same full-detail look", all(len(v) == 1 for v in det.values()), str([v for v in det.values() if len(v) > 1][:3]))
allnames = {n for r in R for n in [r["hidden"]["species"], *r["hidden"]["book_names"]]}
miss = sorted(n for n in allnames if LS._fold(n) not in LS.forbidden_terms(R))
check("every species and book name of the 100 is in the forbidden set", not miss, str(miss[:5]))
life._ROWS.clear(); life._builtin_done = False
base_keys = set(life.rows())
check("NO KEY COLLIDES with an existing life row (a collision would silently REPLACE that row: register() is by key)", not (set(BY) & base_keys), str(sorted(set(BY) & base_keys)))
check("NOT registered by default (flag absent)", not (set(BY) & base_keys) and not LS.enabled(), str(sorted(set(BY) & base_keys)[:5]))
life._ROWS.clear(); life._builtin_done = False
(TMP / "life_flags.json").write_text(json.dumps({"shore_bestiary": True}), encoding="utf-8"); life._flags_cache["ts"] = 0.0
on_keys = set(life.rows())
check("the flag registers them through life._ensure_builtin", set(BY) <= on_keys and LS.enabled())
check("and adds nothing else", on_keys - base_keys == set(BY), str(on_keys - base_keys))
check("an existing alias is unchanged ('starfish' still reaches the anemones row)", (life._match("look at the starfish", "shore") or {}).get("key") == "anemones")
check("no alias reaches a pilot row ('pipi', 'sea lion', 'starfish')",
      all((life._match(w, "shore") or {}).get("key") not in BY for w in ("pipi", "the sea lion", "eleven-armed starfish", "the pipis")))
(TMP / "life_flags.json").write_text(json.dumps({"shore_bestiary": False}), encoding="utf-8"); life._flags_cache["ts"] = 0.0
check("flag false turns it back off", not LS.enabled())
def _flagset(**kw):
    (TMP / "life_flags.json").write_text(json.dumps(kw), encoding="utf-8"); life._flags_cache["ts"] = 0.0
_flagset(shore_bestiary=True)
check("ONE FLAG: shore_bestiary true alone brings registration, described-look answers and place-look discovery all up",
      LS.enabled() and LS.render_live() and LS.discover_live())
_flagset(shore_bestiary=True, shore_bestiary_render=False, shore_bestiary_discover=False)
check("...and a sub-flag set explicitly false keeps that part in shadow", LS.enabled() and not LS.render_live() and not LS.discover_live())
_flagset()
check("nothing set: everything off", not LS.enabled() and not LS.render_live() and not LS.discover_live())
_flagset(shore_bestiary=False, shore_bestiary_render=True)
check("a sub-flag alone does not register anything", not LS.enabled())
_flagset(shore_bestiary=False)

print("-- 8. the naming law (D-0129) on a new row")
life._ROWS.clear(); life._builtin_done = False
(TMP / "life_flags.json").write_text(json.dumps({"shore_bestiary": True}), encoding="utf-8"); life._flags_cache["ts"] = 0.0
life.rows()
book = "A field guide: the sea lion hauls out on rocks, the flippers and the mane of the bull are its marks."
check("a book alone names nothing (no face yet)", life.learn_from_text(book) == [] and not life.is_learned("sea_lion"))
life._log(life._LEDGER, {"kind": "sighting", "key": "sea_lion", "place": "shore", "weight": 1.0})
check("a sighting alone names nothing either", not life.is_learned("sea_lion"))
check("book AFTER a sighting names it", life.learn_from_text(book) == ["sea_lion"] and life.is_learned("sea_lion"))
check("only then does the row carry a name", life.name_for(life._ROWS["sea_lion"]) == "the sea lion" and life.name_for(life._ROWS["pipi"]) == "")

print("-- 9. isolation")
check("every redirected path still points inside the temp dir", all(TMP in p.parents for p in (life._F, life._LEDGER, life._EVENTS, life._FLAGS_F)))
print()
print("ALL OK -- shore bestiary P1" if not FAILS else f"{FAILS} FAILED")
sys.exit(1 if FAILS else 0)
