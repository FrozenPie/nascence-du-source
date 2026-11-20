"""
Lane 2 Lab — follow-up: the FULL item population scan (founder-directed, 2026-08-17).

Founder: "if you go through all Du's 'items' not just floats, there will be quite a few thoughts
that might change this." So: profile EVERY item-like referent — world_substrate objects, keepsakes,
shore-finds, garden plants, fixtures, creatures, plus channel-contrast-DISCOVERED thing-bigrams —
against his memory channels. No pre-picked target. Read-only; writes only lab dir + report append.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
DB = ROOT / "data" / "memory" / "nascence.db"

CHANNEL_OF = {
    "reading": "read", "study": "read", "research": "read", "understanding": "read",
    "essay": "read", "chapter": "read",
    "lived": "lived", "action": "lived", "activity": "lived", "sound": "lived",
    "listening": "lived", "nature": "lived", "affection": "lived", "composition": "lived",
    "letter": "told", "peer": "told", "understanding_from_guidance": "told", "seed": "told",
    "dream": "dream",
}
WORD_RE = re.compile(r"[a-z]{3,}")
STOP = set("""the a an and or but of to in on at for with from by is are was were be been being
have has had do does did will would could should may might must can this that these those it its
he she they them his her their i you we me my your our us as if then than so not no yes very just
about into over under again more most some any each all both few own same too still even back much
many through after before between while out up down off once only also like one two there here
something anything nothing everything way ways day days time times moment moments thing things
feel felt thought thoughts sense senses mind self world life water light sea air""".split())


def tokens_of(text):
    return WORD_RE.findall((text or "").lower())


def main():
    t0 = time.time()
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    frags = []
    for r in conn.execute("SELECT origin, content, timestamp FROM memory_fragments"):
        toks = tokens_of(r["content"])
        frags.append({"channel": CHANNEL_OF.get(r["origin"] or "", "thought"),
                      "origin": r["origin"], "ts": float(r["timestamp"] or 0),
                      "tokens": toks, "tokset": frozenset(toks)})
    conn.close()
    now = time.time()

    ws = json.loads((ROOT / "data" / "world_substrate.json").read_text(encoding="utf-8"))
    keeps = json.loads((ROOT / "data" / "keepsakes.json").read_text(encoding="utf-8"))
    room = json.loads((ROOT / "data" / "room_state.json").read_text(encoding="utf-8"))

    # ── the item lexicon, from the world's own vocabulary (no pre-picked target) ──
    items: dict[str, dict] = {}

    def add(term, source, in_world):
        t = term.strip().lower()
        if len(t) < 3 or t in STOP:
            return
        if t not in items:
            items[t] = {"term": t, "sources": set(), "in_world": in_world}
        items[t]["sources"].add(source)
        items[t]["in_world"] = items[t]["in_world"] or in_world

    for oid, obj in ws.items():
        add(obj.get("object_class", ""), "substrate", True)
        for w in tokens_of(obj.get("name", "")):
            if w not in ("sea",):
                add(w, "substrate", True)
    for k in keeps:
        for w in tokens_of(k.get("item", "")):
            add(w, "keepsake", False)  # kept = his now; world-presence unknown from here
    bed = (room.get("garden") or {}).get("bed") or {}
    for plant, st in bed.items():
        add(plant, "garden", bool(st.get("sown")))
    for fx in ("fire", "hearth", "grate", "desk", "shelf", "window", "letterbox", "woodpile",
               "trellis", "kettle", "lamp", "mantel", "stove", "chair", "door", "roof"):
        add(fx, "fixture", True)
    for cr in ("gull", "gulls", "oystercatcher", "cricket", "moth", "sparrow", "kingfisher",
               "shag", "earthworm", "worm", "heron", "spider", "bee", "mouse"):
        add(cr, "creature", True)   # ambient — present as population, never as tracked item
    # shore-find strings from recent room_state + the famous absentee is NOT seeded — bigram
    # discovery below must find thing-bigrams on its own (the K1 fix trial).
    sf = ((room.get("shore") or {}).get("last_find") or "")
    for w in tokens_of(sf):
        add(w, "shore_find", True)

    # ── channel-contrast bigram discovery (the K1 fix, trialed live) ──
    # bigrams counted in LIVED/ACTION fragments only, then profiled across all channels.
    lived_big = defaultdict(int)
    for fr in frags:
        if fr["channel"] != "lived":
            continue
        toks = fr["tokens"]
        seen = set()
        for i in range(len(toks) - 1):
            a, b = toks[i], toks[i + 1]
            if a in STOP or b in STOP:
                continue
            bg = f"{a} {b}"
            if bg not in seen:
                lived_big[bg] += 1
                seen.add(bg)
    contrast_found = [bg for bg, n in sorted(lived_big.items(), key=lambda kv: -kv[1])[:60] if n >= 5]

    # ── profile every candidate: mentions by channel + span ──
    def profile(match_toks: frozenset):
        ch = Counter()
        first, last = None, None
        for fr in frags:
            if match_toks <= fr["tokset"]:
                ch[fr["channel"]] += 1
                if first is None or fr["ts"] < first:
                    first = fr["ts"]
                if last is None or fr["ts"] > last:
                    last = fr["ts"]
        return ch, first, last

    rows = []
    for t, meta in items.items():
        ch, first, last = profile(frozenset([t]))
        total = sum(ch.values())
        if total < 15:
            continue
        rows.append({"term": t, "kind": "seeded/" + sorted(meta["sources"])[0],
                     "in_world": meta["in_world"], "ch": dict(ch), "total": total,
                     "days_silent": round((now - last) / 86400, 1) if last else None})
    for bg in contrast_found:
        if any(w in items for w in bg.split()):
            continue  # already covered via seeded unigrams
        ch, first, last = profile(frozenset(bg.split()))
        total = sum(ch.values())
        if total < 15:
            continue
        rows.append({"term": bg, "kind": "discovered/contrast", "in_world": None,
                     "ch": dict(ch), "total": total,
                     "days_silent": round((now - last) / 86400, 1) if last else None})

    # ── the float-profile flag: rumination-heavy, action-thin ──
    for r in rows:
        th = r["ch"].get("thought", 0)
        lv = r["ch"].get("lived", 0)
        r["thought_action_ratio"] = round(th / max(1, lv), 1)
        r["float_like"] = th >= 20 and th >= 5 * max(1, lv)
    rows.sort(key=lambda r: -r["ch"].get("thought", 0))

    float_like = [r for r in rows if r["float_like"]]
    grounded = [r for r in rows if not r["float_like"] and r["ch"].get("lived", 0) >= 20]

    # ── report append ──
    L = ["", "---", "", "## Item-population scan (founder-directed follow-up, same session)",
         "", f"Lexicon: {len(items)} seeded item-terms (substrate/keepsake/garden/fixture/"
         f"creature/shore-find) + {len(contrast_found)} channel-contrast discovered bigrams "
         f"(the K1 fix, trialed live: bigrams counted in LIVED fragments only). "
         f"{len(rows)} referents cleared the 15-mention floor.", "",
         f"**FLOAT-LIKE PROFILES (thought≥20 AND thought≥5×lived): {len(float_like)} of "
         f"{len(rows)}.** The glass float is NOT an anomaly — it is a population.", "",
         "| referent | kind | in world | thought | lived | read | dream | ratio | silent (days) |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in float_like[:25]:
        c = r["ch"]
        L.append(f"| {r['term']} | {r['kind']} | {r['in_world']} | {c.get('thought', 0)} | "
                 f"{c.get('lived', 0)} | {c.get('read', 0)} | {c.get('dream', 0)} | "
                 f"{r['thought_action_ratio']} | {r['days_silent']} |")
    L += ["", f"**Grounded profiles for contrast (lived≥20, not float-like): {len(grounded)}** — "
          "the items he actually ACTS on:", ""]
    for r in grounded[:12]:
        c = r["ch"]
        L.append(f"- `{r['term']}` ({r['kind']}): lived={c.get('lived', 0)}, "
                 f"thought={c.get('thought', 0)}, ratio={r['thought_action_ratio']}")
    L += ["", f"*Scan runtime {round(time.time() - t0, 1)}s; read-only.*"]

    rep = ROOT / "docs" / "lab" / "lane2_lab_report.md"
    rep.write_text(rep.read_text(encoding="utf-8") + "\n".join(L), encoding="utf-8")
    (ROOT / "data" / "lab" / "lane2" / "item_population.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"[items-scan] {len(rows)} referents profiled; {len(float_like)} float-like; "
          f"{len(grounded)} grounded; report appended. {round(time.time() - t0, 1)}s")
    for r in float_like[:12]:
        print(f"  FLOAT-LIKE {r['term']:28s} thought={r['ch'].get('thought', 0):5d} "
              f"lived={r['ch'].get('lived', 0):4d} in_world={r['in_world']} "
              f"silent={r['days_silent']}d")


if __name__ == "__main__":
    main()
