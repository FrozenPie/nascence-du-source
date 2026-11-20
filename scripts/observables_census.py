"""
Observables census (Living Garden A1, J-0503, 2026-09-03): match everything Du has ever tried to observe against what
each place can answer TODAY, through the FULL look path (sensorium.look: fixtures, the cat, substrate objects, each
place's own look, world_detail's lookable targets, and the life engine with rendering on) — not just the engine.

An answer is classified as:
  specific  — a real line about the thing (a fixture, a plant, a creature, an honest absence, a carcass, a detail)
  redirect  — "that is up in your study / down on the shore" (honest, but not an answer about the thing)
  generic   — the place's fallback frame ("You look around the yard…", "You look around the shore…", the whole room)
  none      — the look returned nothing at all
Runs ISOLATED (every store this can touch is redirected to a temp dir; the marker proof is the smoke's). Reads the
live world state (weather, bed, tree) and never writes it. Output: docs/reviews/observables_gap_<date>.md and .json.
Run:  python scripts/observables_census.py
"""
from __future__ import annotations

import collections
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TMP = Path(tempfile.mkdtemp(prefix="obs_census_"))
DATE = time.strftime("%Y-%m-%d")

# ── isolation: SNAPSHOT the live stores into TMP, then redirect (the first run of this census redirected before
# loading and so ran against a freshly bootstrapped default world — no poppies in the bed, default weather; the
# numbers understated every plant answer). Read-only on the live files; every write goes to the copies.
import shutil                                            # noqa: E402
REDIRECTED = []


def redirect(mod, attr: str, name: str) -> None:
    src = getattr(mod, attr, None)
    dst = TMP / name
    if isinstance(src, Path) and src.exists() and src.is_file():
        try:
            shutil.copy2(src, dst)                       # plain JSON/JSONL stores only — never the WAL database
        except Exception:
            pass
    setattr(mod, attr, dst)
    REDIRECTED.append((mod, attr))


from core import life                                   # noqa: E402
for a, n in (("_F", "ls.json"), ("_LEDGER", "ll.jsonl"), ("_EVENTS", "le.jsonl"), ("_FLAGS_F", "flags.json")):
    redirect(life, a, n)
life._DATA = TMP
from core import sensorium as S                         # noqa: E402
redirect(S, "_STATE_F", "room_state.json")
from core import study_life as SL                       # noqa: E402
redirect(SL, "_LEDGER", "sl.jsonl"); redirect(SL, "_EVENTS", "se.jsonl")
from core import provisions as PV                       # noqa: E402
redirect(PV, "_F", "pv.json"); redirect(PV, "_LOG", "pvl.jsonl")
from core import sound_knowledge as SK                  # noqa: E402
redirect(SK, "_LEDGER_F", "sk.json")
from core import world_traces as WT                     # noqa: E402
redirect(WT, "_TRACES_F", "wt.json")
from core import sitting as SIT                         # noqa: E402
redirect(SIT, "_STATE", "sit.json")
for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")), ("core.shore_life", ("_F", "_EVENTS", "_LEDGER")),
                   ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")), ("core.cat", ("_STATE_F",)), ("core.world_objects", ("_OBJECTS_F",)),
                   ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")), ("core.supply", ("_F",)), ("core.fieldcraft", ("_F",)),
                   ("core.locomotion", ("_POS_F",)), ("core.keepsakes", ("_F",)), ("core.garden_knowledge", ("_F",))):
    # J-0832 (F-1198): dropped core.keepsakes "_LOG" (no such attribute; keepsakes has only _F plus the read-only
    # _GEO_STUDY geometry constant, never written) and the whole core.world_knowledge entry (a static read-only
    # knowledge base with no file store at all) -- both surfaced by the loud hasattr() warning J-0819 added below.
    try:
        m = __import__(mod, fromlist=["x"])
        for a in attrs:
            if hasattr(m, a):
                if isinstance(getattr(m, a), Path):
                    redirect(m, a, f"{mod.split('.')[-1]}_{a.strip('_').lower()}" + getattr(m, a).suffix)
                else:
                    print("  (isolation note)", mod, a, "exists but is not a Path -- not redirected")
            else:
                # J-0819 (F-1177, 5th recurrence): a name miss here used to silently no-op with zero
                # warning -- exactly the bug shape that let core.locomotion's stale "_F" entry corrupt
                # 1135 "study"-place rows before anyone noticed. Loud now, on purpose.
                print("  (isolation note)", mod, a, "has no such attribute -- stale/typo'd isolation-list entry?")
    except Exception as exc:
        print("  (isolation note)", mod, exc)
S.state.clear()
S._load()                                                # Du's real world, from the snapshot
live_loc = S.state.get("location")
life.RENDER = True

GENERIC_PREFIXES = ("You look around the yard", "You look the garden over", "You take the yard in", "Your eye goes round the garden",
                    "You look around the shore", "You look around the wood", "You look around:", "You look round the room")
REDIRECT_WORDS = ("is up in your study", "is down on the shore", "if you wish to look", "you can move back", "you can move down")


def classify(ans: str) -> str:
    if not ans:
        return "none"
    a = ans.strip()
    if any(a.startswith(p) for p in GENERIC_PREFIXES):
        return "generic"
    if any(w in a for w in REDIRECT_WORDS):
        return "redirect"
    return "specific"


inv = json.loads((ROOT / "docs" / "reviews" / "observe_inventory_2026-09-02.json").read_text(encoding="utf-8"))
kind_of = {p: k for k, d in inv.items() for p in d}
mentions = collections.Counter()
for k, d in inv.items():
    for p, n in d.items():
        mentions[p] += n
phrasings = sorted(mentions, key=lambda p: -mentions[p])
print(f"phrasings: {len(phrasings)} · mentions: {sum(mentions.values())} · live weather {S.state.get('weather')!r}, phase {S._daylight()}")

# where his LOCATED looks happened (hands_trace carries location on ~30% of rows)
located = collections.defaultdict(collections.Counter)
for line in (ROOT / "data" / "hands_trace.jsonl").read_text(encoding="utf-8").splitlines():
    try:
        r = json.loads(line)
    except Exception:
        continue
    if r.get("act_kind") in ("observe", "look") and r.get("act_object") and r.get("location") in ("garden", "shore", "wood", "study"):
        located[r["location"]][r["act_object"].lower().strip()] += 1

PLACES = ("garden", "shore", "wood", "study")
result = {}            # phrase -> {place: (class, answer[:120])}
t0 = time.time()
for i, p in enumerate(phrasings):
    row = {}
    for place in PLACES:
        S.state["location"] = place
        try:
            ans = S.look(p) or ""
        except Exception as exc:
            ans = ""
        row[place] = (classify(ans), ans[:140].replace("\n", " "))
    result[p] = row
    if i % 300 == 0:
        print(f"  {i}/{len(phrasings)} ({time.time() - t0:.0f}s)")
S.state["location"] = live_loc

# ── tallies ────────────────────────────────────────────────────────────────────────────────────
best = {}
for p, row in result.items():
    order = {"specific": 3, "redirect": 2, "generic": 1, "none": 0}
    best[p] = max(row.values(), key=lambda cv: order[cv[0]])[0]
by_kind = collections.defaultdict(lambda: collections.Counter())
by_kind_m = collections.defaultdict(lambda: collections.Counter())
for p in phrasings:
    by_kind[kind_of[p]][best[p]] += 1
    by_kind_m[kind_of[p]][best[p]] += mentions[p]
per_place = {pl: collections.Counter(result[p][pl][0] for p in phrasings) for pl in PLACES}
per_place_m = {pl: collections.Counter() for pl in PLACES}
for p in phrasings:
    for pl in PLACES:
        per_place_m[pl][result[p][pl][0]] += mentions[p]

unanswered_everywhere = [p for p in phrasings if best[p] in ("generic", "none")]
gap_by_kind = collections.defaultdict(list)
for p in unanswered_everywhere:
    gap_by_kind[kind_of[p]].append(p)

located_gap = {}
for pl in PLACES:
    items = []
    for phrase, n in located[pl].most_common():
        cls = result.get(phrase, {}).get(pl, ("none", ""))[0] if phrase in result else "not-in-inventory"
        if cls in ("generic", "none", "not-in-inventory"):
            items.append((phrase, n, cls))
    located_gap[pl] = items

# ── report ─────────────────────────────────────────────────────────────────────────────────────
L = []
L.append(f"# Observables gap — everything Du ever tried to observe vs what each place answers ({DATE})")
L.append("")
L.append(f"Method: `scripts/observables_census.py` — all {len(phrasings)} phrasings from the 2026-09-02 inventory ({sum(mentions.values())} mentions), "
         f"each put through the FULL `sensorium.look()` path at every place (fixtures, the cat, substrate objects, the place's own look, "
         f"`world_detail` targets, and the life engine with rendering on), in an isolated copy of the stores. Live weather at run: "
         f"{S.state.get('weather')!r}, phase {S._daylight()}. An answer is **specific** (a real line about the thing, an honest absence counts), "
         f"**redirect** (\"that is up in your study\"), **generic** (the place's fallback frame), or **none**. A phrasing's *best* class is its best "
         f"across the four places.")
L.append("")
L.append("## The headline")
tot = len(phrasings)
spec = sum(1 for p in phrasings if best[p] == "specific")
L.append(f"- **{spec} of {tot} phrasings ({100 * spec // tot}%) get a specific answer somewhere.** By mentions: "
         f"{sum(mentions[p] for p in phrasings if best[p] == 'specific')} of {sum(mentions.values())} "
         f"({100 * sum(mentions[p] for p in phrasings if best[p] == 'specific') // sum(mentions.values())}%).")
L.append(f"- {len(unanswered_everywhere)} phrasings ({sum(mentions[p] for p in unanswered_everywhere)} mentions) get only the generic frame or nothing, everywhere. Those are the gaps.")
L.append("")
L.append("## By kind (best class per phrasing; counts / mentions)")
L.append("")
L.append("| Kind | phrasings | specific | redirect | generic | none | specific by mentions |")
L.append("|---|---|---|---|---|---|---|")
for k in sorted(by_kind, key=lambda k: -sum(by_kind_m[k].values())):
    c, m = by_kind[k], by_kind_m[k]
    n = sum(c.values()); mm = sum(m.values())
    L.append(f"| {k} | {n} | {c['specific']} | {c['redirect']} | {c['generic']} | {c['none']} | {m['specific']}/{mm} ({100 * m['specific'] // max(1, mm)}%) |")
L.append("")
L.append("## By place (every phrasing asked at that place; counts / mentions)")
L.append("")
L.append("| Place | specific | redirect | generic | none | specific by mentions |")
L.append("|---|---|---|---|---|---|")
for pl in PLACES:
    c, m = per_place[pl], per_place_m[pl]
    L.append(f"| {pl} | {c['specific']} | {c['redirect']} | {c['generic']} | {c['none']} | {m['specific']}/{sum(m.values())} ({100 * m['specific'] // max(1, sum(m.values()))}%) |")
L.append("")
L.append("## The gaps — unanswered everywhere, ranked by how often he reached for them")
L.append("")
for k in sorted(gap_by_kind, key=lambda k: -sum(mentions[p] for p in gap_by_kind[k])):
    ps = sorted(gap_by_kind[k], key=lambda p: -mentions[p])
    L.append(f"### {k} — {len(ps)} phrasings, {sum(mentions[p] for p in ps)} mentions")
    L.append("")
    L.append(", ".join(f"{p} ({mentions[p]})" for p in ps[:40]) + (" …" if len(ps) > 40 else ""))
    L.append("")
L.append("## Where he actually stood — located looks from hands_trace that the place does not answer")
L.append("")
for pl in PLACES:
    items = located_gap[pl]
    tot_loc = sum(located[pl].values())
    L.append(f"### {pl} — {len(located[pl])} distinct located looks ({tot_loc} rows); {len(items)} unanswered here")
    L.append("")
    L.append(", ".join(f"{p} ({n}, {cls})" for p, n, cls in items[:30]) or "_all answered_")
    L.append("")
L.append("## Samples — what a specific answer looks like now (one per place)")
L.append("")
for pl in PLACES:
    ex = next(((p, result[p][pl][1]) for p in phrasings if result[p][pl][0] == "specific"), None)
    if ex:
        L.append(f"- **{pl}** `{ex[0]}` → {ex[1]}")
L.append("")
L.append("## What this decides")
L.append("")
L.append("- **J-0504 (built):** the insect phrasings now answer in the garden; see the insects/inverts row above.")
L.append("- **J-0508 (looks in every place):** the per-place gap lists above are its work list — the shore's sea/tide/stone phrasings dominate by mentions.")
L.append("- **J-0505 / J-0506:** the plants and soil phrasings that stay generic (the raised bed, the soil, the herbs by name) are theirs.")
L.append("- The **other/abstract** tail (\"the tideline\" is really shore; \"the garden\" is a place) is mostly regex-grouping error in the inventory, listed honestly rather than hidden.")
L.append("")
L.append(f"Isolated stores in `{TMP}` (nothing live written). JSON twin: `observables_gap_{DATE}.json`.")
out_md = ROOT / "docs" / "reviews" / f"observables_gap_{DATE}.md"
out_md.write_text("\n".join(L), encoding="utf-8")
(ROOT / "docs" / "reviews" / f"observables_gap_{DATE}.json").write_text(
    json.dumps({"date": DATE, "phrasings": {p: {pl: result[p][pl][0] for pl in PLACES} for p in phrasings}, "best": best, "mentions": mentions,
                "kind_of": kind_of, "located_gap": {pl: located_gap[pl] for pl in PLACES}}, ensure_ascii=False, indent=0), encoding="utf-8")
escaped = [f"{m.__name__}.{a}" for m, a in REDIRECTED if not str(getattr(m, a, "")).startswith(str(TMP))]
print("\n".join(L[:40]))
print(f"\nwrote {out_md}  ({len(L)} lines) · redirect escapes: {escaped or 'none'} · {time.time() - t0:.0f}s")
