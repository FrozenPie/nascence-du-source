"""
Nascence — One-time backfill: seed L6 Temporal Epochs + L7 Thematic Threads
from existing history.

Carl already lived these sessions — the episodic record is in nascence.db. The
two new S-MMU 7 layers (memory_epochs L6, memory_themes L7) only begin forming
going forward (epochs at /quit, themes via the Subconscious T6 pass), so without
a backfill they start empty. This script indexes the history that already
happened: they are his memories already.

BOUNDARY RULE
  A new epoch begins when there is a > 30-min gap in the episodic stream OR the
  calendar day changes. Short conversational sittings become their own epoch;
  long autonomous overnight runs (continuous inner-monologue + nightly-sleep)
  become one epoch per day rather than a single 21-hour blob.

MATERIAL
  Per epoch, prefer substantive fragments (lived · session_summary · dream ·
  active_imagination); fall back to whatever the window has if there are < 3.
  Capped at 30, evenly sampled across the window so a dense day keeps its arc.

SYNTHESIS
  Mirrors the live _form_epoch / T6 logic exactly — same prompt, same background
  lane (CPU 11460 → GPU 11470 failover), same store_epoch / SubconsciousNode
  theme clustering — so seeded memories are indistinguishable from ones Carl
  forms himself from here on.

USAGE
  python scripts/seed_epochs_themes.py --dry-run   # show the carving, no LLM, no writes
  python scripts/seed_epochs_themes.py --commit     # back up DB, synthesise, write epochs + themes
"""

from __future__ import annotations

import os
import sys
import json
import time
import shutil
import asyncio
import argparse
import sqlite3
import types
from pathlib import Path

# Offline embeddings (same as run_nascence) + UTF-8 console for Carl's non-ASCII voice.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
DB = ROOT / "data" / "memory" / "nascence.db"

GAP_SECS     = 30 * 60          # > this gap in the episodic stream starts a new epoch
MAX_MATERIAL = 30               # cap fragments fed to one synthesis (even-sampled)
MIN_FRAGS    = 3               # windows smaller than this are skipped (matches live _form_epoch)
SUBSTANTIVE  = ("lived", "session_summary", "dream", "active_imagination")

# Test rows this session's round-trip check wrote into the live DB — removed before seeding.
_TEST_EPOCH_MOOD  = "restless circling"
_TEST_THEME_NAME  = "language as both tool and prison"


def _spirit_name() -> str:
    try:
        d = json.loads((ROOT / "data" / "identity" / "axiom.json").read_text(encoding="utf-8"))
        return d.get("name") or d.get("handle") or "Carl"
    except Exception:
        return "Carl"


def _local_day(ts: float) -> tuple[int, int]:
    lt = time.localtime(ts)
    return (lt.tm_year, lt.tm_yday)


def sessionize() -> list[list[sqlite3.Row]]:
    """Split episodic-layer fragments into epoch windows by the boundary rule."""
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT timestamp, origin, content FROM memory_fragments "
        "WHERE layer='episodic' ORDER BY timestamp"
    ).fetchall()
    conn.close()

    windows: list[list[sqlite3.Row]] = []
    cur: list[sqlite3.Row] = []
    last_ts = None
    last_day = None
    for r in rows:
        ts = r["timestamp"]
        day = _local_day(ts)
        if cur and ((ts - last_ts) > GAP_SECS or day != last_day):
            windows.append(cur)
            cur = []
        cur.append(r)
        last_ts = ts
        last_day = day
    if cur:
        windows.append(cur)
    return windows


def select_material(frags: list[sqlite3.Row]) -> list[sqlite3.Row]:
    """Prefer substantive fragments; even-sample down to MAX_MATERIAL, preserving the arc."""
    sub = [f for f in frags if f["origin"] in SUBSTANTIVE]
    pool = sub if len(sub) >= MIN_FRAGS else frags
    if len(pool) > MAX_MATERIAL:
        step = len(pool) / MAX_MATERIAL
        pool = [pool[int(i * step)] for i in range(MAX_MATERIAL)]
    return pool


def _fmt_range(a: float, b: float) -> str:
    lo = time.strftime("%Y-%m-%d %H:%M", time.localtime(a))
    hi = time.strftime("%H:%M", time.localtime(b))
    hrs = (b - a) / 3600
    return f"{lo}–{hi}  ({hrs:4.1f}h)"


def build_plan() -> list[dict]:
    """Return the list of epoch windows that qualify (>= MIN_FRAGS), with their material."""
    plan = []
    for w in sessionize():
        material = select_material(w)
        if len(material) < MIN_FRAGS:
            continue
        plan.append({
            "ts_start": w[0]["timestamp"],
            "ts_end":   w[-1]["timestamp"],
            "n_total":  len(w),
            "material": material,
        })
    return plan


def dry_run() -> None:
    plan = build_plan()
    print(f"\nProposed epochs (boundary: >{GAP_SECS//60}-min gap OR day change):\n")
    for i, e in enumerate(plan, 1):
        origins = {}
        for f in e["material"]:
            origins[f["origin"]] = origins.get(f["origin"], 0) + 1
        ostr = " ".join(f"{k}:{v}" for k, v in sorted(origins.items()))
        print(f"  {i:2}. {_fmt_range(e['ts_start'], e['ts_end'])}  "
              f"frags={e['n_total']:4} → feed {len(e['material']):2}  [{ostr}]")
        preview = e["material"][0]["content"][:90].replace("\n", " ")
        print(f"      e.g. {preview}")
    print(f"\n{len(plan)} epochs would be synthesised, then clustered into themes.")
    print("No LLM calls made, nothing written. Re-run with --commit to seed.\n")


async def commit() -> None:
    from core.model_client import call_node_json
    from core.schema import SERVE_CHAINS
    import core.memory.store as store
    from nodes.subconscious_node import SubconsciousNode

    # D-0353 / J-1839: --commit seeds epochs + themes into the LIVE memory DB on purpose from a
    # non-live process -- the explicit opt-in the live-DB write fence requires (--dry-run never
    # reaches this function and stays fenced).
    store.allow_live_writes("scripts/seed_epochs_themes.py --commit: seed L6 epochs + L7 themes")
    store.init_db()  # ensure L6/L7 tables exist
    name = _spirit_name()
    plan = build_plan()
    if not plan:
        print("Nothing to seed (no qualifying windows).")
        return

    # 1. Back up the live DB.
    bak = DB.with_name(DB.name + f".seedbak-{int(time.time())}")
    shutil.copy2(DB, bak)
    print(f"[backup] {bak.name}")

    # 2. Remove this session's test pollution.
    conn = sqlite3.connect(str(DB))
    n_e = conn.execute("DELETE FROM memory_epochs WHERE mood = ?", (_TEST_EPOCH_MOOD,)).rowcount
    n_t = conn.execute("DELETE FROM memory_themes WHERE theme_name = ?", (_TEST_THEME_NAME,)).rowcount
    conn.commit()
    conn.close()
    print(f"[cleanup] removed {n_e} test epoch(s), {n_t} test theme(s)")

    # 3. Synthesise + store an epoch per window (same prompt/lane as live _form_epoch).
    print(f"\n[epochs] synthesising {len(plan)} epochs on the background lane...")
    base = SERVE_CHAINS["background"]
    formed = 0
    for i, e in enumerate(plan, 1):
        frag_texts = "\n".join(
            f"  [{f['origin']}] {f['content'][:150].replace(chr(10), ' ')}" for f in e["material"]
        )
        system = (
            "/no_think\n"
            f"You are the epoch-synthesis function of {name}. "
            "You will be shown episodic memory fragments from one period. "
            "Synthesise them into a first-person impression of that period as a distinct stretch of experience. "
            "Output ONLY valid JSON with exactly two fields: "
            '{"mood": "...", "impression": "..."}. '
            "mood: 2–4 words naming the emotional quality of this time "
            "(e.g. 'anxious precision', 'quiet expansion', 'restless circling'). "
            "impression: 1–2 sentences: what was this period actually about — "
            "its essential why and what, in first person."
        )
        user = f"Period fragments:\n{frag_texts}"
        try:
            data = await call_node_json(base, system, user, max_tokens=200, temperature=0.45)
        except Exception as exc:
            print(f"  {i:2}. SKIP (LLM failed: {exc})")
            continue
        mood = str(data.get("mood", "")).strip()
        impression = str(data.get("impression", "")).strip()
        if not mood or not impression:
            print(f"  {i:2}. SKIP (empty synthesis)")
            continue
        store.store_epoch(
            session_id      = f"backfill-{i}",
            timestamp_start = e["ts_start"],
            timestamp_end   = e["ts_end"],
            mood            = mood,
            impression      = impression,
            fragment_count  = e["n_total"],
        )
        formed += 1
        print(f"  {i:2}. {time.strftime('%m-%d %H:%M', time.localtime(e['ts_start']))}  "
              f"{mood} — {impression[:70]}")
    print(f"[epochs] {formed} stored.")

    # 4. Cluster the seeded epochs into themes (reuse the real T6 logic).
    print("\n[themes] clustering epochs into thematic threads...")
    node = SubconsciousNode()
    epochs = store.get_epochs(limit=500)
    clusters = node._cluster_epochs(epochs)
    fake_state = types.SimpleNamespace(spirit_name=name)
    n_themes = 0
    for cl in clusters:
        if len(cl) < 2:
            continue
        before = {t["theme_id"] for t in store.get_themes(limit=500)}
        await node._synthesise_theme(cl, fake_state)
        after = store.get_themes(limit=500)
        if {t["theme_id"] for t in after} - before:
            n_themes += 1
    themes = store.get_themes(limit=500)
    print(f"[themes] {len(themes)} theme(s) now present:")
    for t in themes:
        print(f"   • {t['theme_name']} — {t['current_stance'][:80]}")

    print(f"\nDone. {formed} epochs + {len(themes)} themes seeded into Carl's memory.")
    print(f"Backup at {bak.name} if you need to roll back.\n")


async def rethemes() -> None:
    """Rebuild L7 themes cleanly from the existing epochs with the fixed (same-space) dedup.
    Wipes the duplicated theme rows and re-clusters once — deterministic, so it converges."""
    import core.memory.store as store
    from nodes.subconscious_node import SubconsciousNode

    # D-0353 / J-1839: same opt-in as commit() -- --rethemes rewrites the LIVE L7 theme rows.
    store.allow_live_writes("scripts/seed_epochs_themes.py --rethemes: rebuild L7 themes")
    store.init_db()  # runs the centroid / member_epoch_ids migration
    name = _spirit_name()

    bak = DB.with_name(DB.name + f".rethemebak-{int(time.time())}")
    shutil.copy2(DB, bak)
    print(f"[backup] {bak.name}")

    conn = sqlite3.connect(str(DB))
    n = conn.execute("DELETE FROM memory_themes").rowcount
    conn.commit(); conn.close()
    print(f"[cleanup] removed {n} existing theme row(s)")

    node = SubconsciousNode()
    epochs = store.get_epochs(limit=500)
    clusters = node._cluster_epochs(epochs)
    print(f"[themes] {len(epochs)} epochs -> clusters {[len(c) for c in clusters]}")
    fake_state = types.SimpleNamespace(spirit_name=name)
    for cl in clusters:
        if len(cl) < 2:
            continue
        await node._synthesise_theme(cl, fake_state)

    themes = store.get_themes(limit=500)
    print(f"\n[themes] {len(themes)} theme(s) now present:")
    for t in themes:
        mids = len(json.loads(t["member_epoch_ids"] or "[]"))
        print(f"   • ({t['epoch_count']} epochs, {mids} tracked) {t['theme_name']} — {t['current_stance'][:70]}")
    print(f"\nDone. Backup at {bak.name}.\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Seed L6 epochs + L7 themes from existing history.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="show the carving; no LLM, no writes")
    g.add_argument("--commit", action="store_true", help="back up DB, synthesise, write epochs + themes")
    g.add_argument("--rethemes", action="store_true", help="wipe + rebuild L7 themes only (fixed dedup)")
    args = ap.parse_args()
    if args.dry_run:
        dry_run()
    elif args.rethemes:
        asyncio.run(rethemes())
    else:
        asyncio.run(commit())


if __name__ == "__main__":
    main()
