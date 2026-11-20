"""
Living World — flip the shadow flags WITHOUT restarting Du (2026-09-03; 'book_gate' added 2026-09-17, J-0852;
'cat_found' added 2026-09-22, D-0253/J-1215).

  python scripts/life_flags.py show
  python scripts/life_flags.py render on|off      # looks: the life engine answers "look at the hedgehog" (vs shadow-logging)
  python scripts/life_flags.py gating on|off      # voices: creature sounds gated by who is present and awake (vs soundscape's own rules)
  python scripts/life_flags.py cat_sounds on|off  # her voice: the cat's sounds reach active_sounds (vs cat_sound_ledger.jsonl shadow) — cat_overhaul C1
  python scripts/life_flags.py book_gate on|off   # B3+B4: can_read()/the remediation stream actually gate on
                                                   # where the book is (vs would_block shadow rows) — books_have_a_place §4
  python scripts/life_flags.py cat_found on|off   # D-4/D-0253: the passive "found" larder credit actually adds a
                                                   # real cat_food object + narrates (vs cat_found_ledger.jsonl
                                                   # shadow) — cat_overhaul mechanism C. NOT flipped by J-1215 itself.
  python scripts/life_flags.py cat_ears on|off    # C2 (J-2467): her ears — LIVE by code default; off = kill switch
  python scripts/life_flags.py cat_call on|off    # C3 (J-2468): his call as its own hand (core/cat_call) — LIVE by
                                                   # code default; off = the hand is off (a call is no deed at all)
  python scripts/life_flags.py cat_harm on|off    # D-2 (J-2471, D-0506): her mortality (core/cat_harm: injury, illness,
                                                   # ageing, death) — LIVE by code default; off = no roll, no harm
                                                   # applied (a cat already dead stays dead: state is truth)
  python scripts/life_flags.py cat_dosed on|off   # B4 (J-2473, D-0508): her presence line read DOSED at the idle scene
                                                   # (core/cat_loop) — LIVE by code default; off = every scene build
                                                   # renders her as before B4 (the ledger keeps would_* rows)
  python scripts/life_flags.py clear              # back to the code defaults (all shadow)

Writes data/life_flags.json atomically; core/life (render/gating/cat_sounds) and core/study_life (book_gate) each
read it at most every 10 s, so Du's running process picks a flip up within seconds. The founder's call (D-0133 /
D-0204): flip when the shadow evidence reads right — scripts/life_shadow_replay.py replays core/life's own evidence
offline in minutes; data/life_events.jsonl holds its live would_answer / would_gate rows, data/study_events.jsonl
holds book_gate's own would_block rows (books_have_a_place §4's own bar: >=30 rows, zero false blocks in the study).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
F = ROOT / "data" / "life_flags.json"
LOG = ROOT / "data" / "life_events.jsonl"


def _read() -> dict:
    try:
        return json.loads(F.read_text(encoding="utf-8")) if F.exists() else {}
    except Exception:
        return {}


def _write(d: dict) -> None:
    tmp = F.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, indent=1), encoding="utf-8")
    tmp.replace(F)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": round(time.time(), 1), "kind": "flags", **d}) + "\n")
    except Exception:
        pass


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(ROOT))
    from core import life
    d = _read()
    if not argv or argv[0] == "show":
        print(f"file: {F} -> {d or '(absent: code defaults)'}")
        print(f"effective: render={'ON' if life.render_on() else 'shadow'}  gating={'ON' if life.gating_on() else 'shadow'}  "
              f"(code defaults RENDER={life.RENDER} SOUND_GATING={life.SOUND_GATING})")
        try:
            from core import cat_sounds
            print(f"           cat_sounds={'ON' if cat_sounds.render_on() else 'shadow'}  (code default RENDER={cat_sounds.RENDER}; "
                  f"ledger rows {cat_sounds.status()['ledger_rows']})")
        except Exception as exc:
            print(f"           cat_sounds: unavailable ({exc})")
        try:
            from core import study_life
            print(f"           book_gate={'ON' if study_life.book_gate_on() else 'shadow'}  (code default OFF; "
                  f"would_block rows in data/study_events.jsonl -- books_have_a_place §4's 3-day read)")
        except Exception as exc:
            print(f"           book_gate: unavailable ({exc})")
        try:
            from core import cat
            _found_rows = sum(1 for _ in open(cat._FOUND_LEDGER_F, encoding="utf-8")) if cat._FOUND_LEDGER_F.exists() else 0
            print(f"           cat_found={'ON' if cat.found_scrap_render_on() else 'shadow'}  (code default RENDER={cat.FOUND_SCRAP_RENDER}; "
                  f"ledger rows {_found_rows} -- D-0253/J-1215 mechanism C)")
        except Exception as exc:
            print(f"           cat_found: unavailable ({exc})")
        return 0
    if argv[0] == "clear":
        if F.exists():
            F.unlink()
        _write({}) if False else None
        print("cleared -> code defaults (all shadow)")
        return 0
    if len(argv) == 2 and argv[0] in ("render", "gating", "cat_sounds", "book_gate", "cat_found", "cat_ears", "cat_call", "cat_tom", "cat_harm", "cat_dosed") and argv[1] in ("on", "off"):
        key = {"cat_sounds": "cat_sounds_render", "cat_found": "cat_found_render", "cat_ears": "cat_ears_live",
               "cat_call": "cat_call_live", "cat_tom": "cat_tom_live", "cat_harm": "cat_harm_live"}.get(argv[0], argv[0])
        d[key] = argv[1] == "on"
        if argv[0] == "cat_harm":   # D-2 (J-2471): her mortality is LIVE by code default; off = no roll, no harm applied
            try:
                from core import cat_harm
                cat_harm._flags_cache["ts"] = 0.0
            except Exception:
                pass
        if argv[0] == "cat_dosed":  # B4 (J-2473): the dosed read is LIVE by code default; off = every scene build renders her
            try:
                from core import cat_loop
                cat_loop._flags_cache["ts"] = 0.0
            except Exception:
                pass
        _write(d)
        life._flags_cache["ts"] = 0.0
        if argv[0] == "cat_ears":   # C2 (J-2467): her ears are LIVE by code default; this is the kill switch
            try:
                from core import cat_ears
                cat_ears._flags_cache["ts"] = 0.0
            except Exception:
                pass
        if argv[0] == "cat_tom":    # B3 (J-2470): the tom is LIVE by code default; off = he stays on the ridge
            try:
                from core import cat_tom
                cat_tom._flags_cache["ts"] = 0.0
            except Exception:
                pass
        if argv[0] == "cat_call":   # C3 (J-2468): his call is LIVE by code default; this is the kill switch
            try:
                from core import cat_call
                cat_call._flags_cache["ts"] = 0.0
            except Exception:
                pass
        if argv[0] == "book_gate":
            try:
                from core import study_life
                study_life._flags_cache["ts"] = 0.0
            except Exception:
                pass
        if argv[0] == "cat_found":
            try:
                from core import cat
                cat._found_flags_cache["ts"] = 0.0
            except Exception:
                pass
        print(f"{argv[0]} -> {argv[1].upper()}   (effective within 10 s in Du's process)  file now {d}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
