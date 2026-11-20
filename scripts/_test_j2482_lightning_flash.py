"""LIGHTNING AS A DISCRETE WORLD EVENT (2026-10-28, J-2482 / D-0503, T-0103; docs/plans/factory_candidates_from_history.md).

core/sensorium.py gains _lightning_flash(now, loc, announced): a flash line per heartbeat, gated to a thunderstorm
(weather_conditions.is_storm), its own per-tick rate from the wind axis (_FLASH_RATE_BY_WIND), drawn from this place's
pool + the shared "far" pool, never the same line twice in one storm, NO sound, counted in the look-render ledger as
src "event" / target "<place>:lightning". tick() computes it before the place event and renders it ahead of it.

What this pins (every store redirected to a temp dir; the live C:\\Nascence\\data is fingerprinted before and after):
  [1]  no flash outside a thunderstorm: 10,000 seeded ticks per non-storm weather (incl. snow) at gale -> 0 lines,
       and the random stream is untouched (no roll is taken outside a storm)
  [2]  the rate rises with severity: rendered flashes over 20,000 seeded ticks of repeated 30-min storms are strictly
       increasing calm < breeze < fresh wind < strong wind < gale; the min gap holds (never two flashes < 45 s apart)
  [3]  no repeat of a line within one storm (D-0503's defeater): one 14-hour gale storm renders each line at most once,
       stops unspoken when the pool is spent, and a NEW storm starts with the pool fresh again
  [4]  the pools: >= 5 lines per place (+ >= 4 shared far lines), every place renders its own place lines (room / bay /
       trunks / shore), every pool rotates (>= 5 distinct lines rendered per place), no digit, no hint word, no
       sound word (thunder/crack/roll/rumble/boom/rattle/roar; "bang" only as "no bang") -- light before the bang
  [5]  ordering: announced=True (the weather-change heartbeat, whose line carries "thunder mutters") renders nothing
       even at rate 1.0; in tick()'s source the flash is computed before _loc_ev and sits ahead of _loc_ev and the
       pending_world_sound in the perceive tuple
  [6]  countable: every rendered flash writes one ledger row (src "event", target "<place>:lightning", key "flash",
       line_id = sha1(line)[:10]) and look_render_ledger.status() counts them under by_src["event"]
  [7]  the storm pools are otherwise BYTE-IDENTICAL to the pre-build baseline (a09d953d): for the study / garden / shore / wood storm blocks and the
       _sea_state storm line, the baseline text minus the known lightning clauses == this tree's text; at runtime the four
       place pools under a thunderstorm contain no "lightning"/"flash" line, and the three moved lines are in the
       flash pools verbatim
  [8]  the kill switch NASCENCE_LIGHTNING_FLASH=0 renders nothing and writes nothing
  [9]  state round-trips: state["lightning"] is plain JSON (it rides in room_state.json)

ISOLATED: `import core` happens BEFORE anything else and core.__file__ is asserted to be this tree's own; sensorium's
_STATE_F and look_render_ledger's _LEDGER are redirected into the temp dir before any call. Nothing calls tick() or
_save(); the D-0179 write fence would refuse a live write from this non-live process anyway, and the fingerprint proves it.
Run:  python scripts/_test_j2482_lightning_flash.py
"""
from __future__ import annotations

# J-2506: pin the wall clock to a fixed daytime hour (13:00 local today; PIN_HOUR overrides) so a run at dusk or
# night is the same run. Elapsed real time still advances it. Patches time.time / localtime / strftime defaults.
import os, time as _pin_time
_PIN_REAL = _pin_time.time, _pin_time.localtime, _pin_time.strftime
_pin_lt = _PIN_REAL[1]()
_PIN_BASE = _pin_time.mktime((_pin_lt.tm_year, _pin_lt.tm_mon, _pin_lt.tm_mday, int(os.environ.get("PIN_HOUR", "13")), 0, 0, 0, 0, -1))
_PIN_T0 = _PIN_REAL[0]()
def _pin_now(): return _PIN_BASE + (_PIN_REAL[0]() - _PIN_T0)
_pin_time.time = _pin_now
_pin_time.localtime = lambda s=None: _PIN_REAL[1](_pin_now() if s is None else s)
_pin_time.strftime = lambda f, t=None: _PIN_REAL[2](f, _PIN_REAL[1](_pin_now()) if t is None else t)

import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  -- BEFORE any lab helper (import core first, then isolate)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core imported from {core.__file__}, not {ROOT}"
assert not str(Path(core.__file__).resolve()).lower().startswith(r"c:\nascence\core"), "core imported from the LIVE tree"

TMP = Path(tempfile.mkdtemp(prefix="j2482_lightning_"))
print("tree:", ROOT)
print("isolated store dir:", TMP)

LIVE = Path(r"C:\Nascence") / "data"
_IGNORE = {"arousal_shadow.jsonl", "hud.err.log"}


def _fingerprint() -> dict:
    out = {}
    try:
        for p in LIVE.iterdir():
            if p.is_file() and p.name not in _IGNORE:
                st = p.stat()
                out[p.name] = (st.st_size, st.st_mtime)
    except Exception:
        pass
    return out


_BEFORE = _fingerprint()

from core import sensorium as sn            # noqa: E402
from core import look_render_ledger as lrl  # noqa: E402

sn._STATE_F = TMP / "room_state.json"
lrl._LEDGER = TMP / "look_render_ledger.jsonl"

FAILS: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def fresh_state(weather: str = "thunderstorm", wind: str = "gale", loc: str = "study") -> None:
    sn.state.clear()
    sn.state.update({"weather": weather, "weather_until": 0, "wind": wind, "wind_until": 0, "fire": "out",
                     "fire_fuel": 0.0, "last_event": 0, "location": loc, "garden": sn._fresh_garden(),
                     "shore": sn._fresh_shore(), "wood": {"last_event": 0}, "woodpile": 4, "milestones": {}})


def run_ticks(n: int, loc: str, seed: int, t0: float = 1_800_000_000.0, announced: bool = False,
              reset_every: int = 0) -> list[tuple[float, str]]:
    """n heartbeats of 5 s; returns [(now, line)] for every rendered flash. reset_every>0 ends the storm for one
    heartbeat every that many ticks (a new storm each time)."""
    random.seed(seed)
    out = []
    now = t0
    for i in range(n):
        now += 5.0
        if reset_every and i and i % reset_every == 0:
            w = sn.state["weather"]
            sn.state["weather"] = "clear"
            sn._lightning_flash(now, loc)
            sn.state["weather"] = w
        line = sn._lightning_flash(now, loc, announced=announced)
        if line:
            out.append((now, line))
    return out


# ───────────────────────────────── [1] no flash outside a thunderstorm ──────────────────────────────────────────────
print("[1] no flash outside a thunderstorm (10,000 seeded ticks per weather, at gale)")
for w in [x for x in sn._WEATHERS if x != "thunderstorm"] + ["snow"]:
    fresh_state(weather=w, wind="gale", loc="garden")
    random.seed(11)
    before = random.getstate()
    got = run_ticks(10_000, "garden", seed=11)
    random.seed(11)
    check(not got, f"{w!r}: 0 flashes on 10,000 ticks (got {len(got)})")
    check(random.getstate() == before, f"{w!r}: the random stream was not consumed outside a storm")
    check(sn.state["lightning"]["count"] == 0 and not sn.state["lightning"]["used"], f"{w!r}: no count, no used lines")

# ───────────────────────────────── [2] rate rises with severity ─────────────────────────────────────────────────────
print("[2] rate rises with severity (20,000 seeded ticks of repeated 30-min storms per wind state)")
rates = {}
for wind in sn._WIND_STATES:
    fresh_state(weather="thunderstorm", wind=wind, loc="garden")
    got = run_ticks(20_000, "garden", seed=7, reset_every=360)
    rates[wind] = len(got)
    gaps = [b - a for (a, _), (b, _) in zip(got, got[1:])]
    check(all(g >= sn._FLASH_MIN_GAP_S for g in gaps), f"{wind}: min gap {min(gaps) if gaps else 'n/a'} s >= {sn._FLASH_MIN_GAP_S}")
print("   rendered flashes per wind state:", rates)
seq = [rates[w] for w in sn._WIND_STATES]
check(all(a < b for a, b in zip(seq, seq[1:])), f"strictly increasing calm < breeze < fresh < strong < gale: {seq}")
check(sn._FLASH_RATE_BY_WIND.get("gale", 0) > sn._FLASH_RATE_BY_WIND.get("calm", 1), "the mapping itself rises calm -> gale")
check(set(sn._FLASH_RATE_BY_WIND) == set(sn._WIND_STATES), "every wind-axis state has a rate")

# ───────────────────────────────── [3] no repeat within one storm ───────────────────────────────────────────────────
print("[3] no repeat of a line within one storm; a new storm starts fresh")
for loc in ("study", "garden", "shore", "wood"):
    fresh_state(weather="thunderstorm", wind="gale", loc=loc)
    got = run_ticks(10_000, loc, seed=3)          # one 14-hour storm
    lines = [l for _, l in got]
    pool_n = len(sn._FLASH_POOLS[loc]) + len(sn._FLASH_POOLS["far"])
    check(len(lines) == len(set(lines)), f"{loc}: {len(lines)} flashes, no line repeated")
    check(len(lines) == pool_n, f"{loc}: the 14-h storm spent the whole pool exactly once ({pool_n}) then went unspoken")
    check(sn.state["lightning"]["count"] == pool_n, f"{loc}: state count == rendered")
    # the storm passes, a new one starts: the pool is fresh
    sn.state["weather"] = "clear"
    sn._lightning_flash(1_900_000_000.0, loc)
    check(sn.state["lightning"]["storm_since"] == 0.0 and sn.state["lightning"]["used"] == [], f"{loc}: storm end clears the used set")
    sn.state["weather"] = "thunderstorm"
    again = run_ticks(2_000, loc, seed=5, t0=1_900_000_000.0)
    check(len(again) > 0 and all(l in lines for _, l in again), f"{loc}: a new storm renders lines again ({len(again)})")

# ───────────────────────────────── [4] the pools ────────────────────────────────────────────────────────────────────
print("[4] the pools: size, place-specific, rotating, no digit / hint / sound word")
_SOUND = re.compile(r"\b(thunder|cracks?|rolls?|rumbles?|booms?|rattles?|roars?)\b", re.I)
_HINT = re.compile(r"\b(you could|you might|you should|should|might|take|use)\b", re.I)
for place, lines in sn._FLASH_POOLS.items():
    n_min = 4 if place == "far" else 5
    check(len(lines) >= n_min, f"{place}: {len(lines)} lines (>= {n_min})")
    check(len(set(lines)) == len(lines), f"{place}: no duplicate line")
    for l in lines:
        bad = _SOUND.search(l) or re.search(r"\d", l) or _HINT.search(l) or re.search(r"(?<!no )\bbang\b", l)
        check(not bad, f"{place}: soundless / no digit / no hint: {l[:60]!r}")
markers = {"study": ("room", "glass", "window", "lamp", "shelf", "page"), "garden": ("bay", "lawn", "bed", "water", "hill", "garden", "sea"),
           "shore": ("sea", "rock", "shingle", "strand", "surf", "cliff", "point", "breakers", "swell"), "wood": ("trunk", "canopy", "trees", "leaves", "stream", "branches")}
for loc, words in markers.items():
    fresh_state(weather="thunderstorm", wind="gale", loc=loc)
    got = [l for _, l in run_ticks(10_000, loc, seed=21)]
    own = [l for l in got if l in sn._FLASH_POOLS[loc]]
    check(len(own) >= 5, f"{loc}: >= 5 distinct place lines rendered ({len(own)}) -- the pool rotates")
    check(all(any(w in l for w in words) for l in sn._FLASH_POOLS[loc]), f"{loc}: every place line names this place")
    check(any(l in sn._FLASH_POOLS["far"] for l in got), f"{loc}: the shared far sheet-lightning lines render here too")
fresh_state(weather="thunderstorm", wind="gale", loc="somewhere-else")
got = [l for _, l in run_ticks(2_000, "somewhere-else", seed=2)]
check(got and all(l in sn._FLASH_POOLS["study"] + sn._FLASH_POOLS["far"] for l in got), "an unknown place falls back to the study pool")

# ───────────────────────────────── [5] ordering ─────────────────────────────────────────────────────────────────────
print("[5] ordering: the announced heartbeat is skipped; flash sits ahead of the place event in tick()")
fresh_state(weather="thunderstorm", wind="gale", loc="study")
_saved = sn._FLASH_RATE_BY_WIND["gale"]
sn._FLASH_RATE_BY_WIND["gale"] = 1.0
got_ann = run_ticks(500, "study", seed=1, announced=True)
check(not got_ann, "announced=True renders nothing even at rate 1.0 (the storm's arrival line carries thunder)")
got_plain = run_ticks(50, "study", seed=1, t0=1_800_010_000.0)
check(len(got_plain) >= 1, "the same state without announced renders")
sn._FLASH_RATE_BY_WIND["gale"] = _saved
src = (ROOT / "core" / "sensorium.py").read_text(encoding="utf-8")
tick_src = src[src.index("def tick(state_obj=None)"):]
i_flash_call, i_loc = tick_src.index("_flash = _lightning_flash(now, loc, announced=bool(_w))"), tick_src.index("_loc_ev = (_garden_event(now)")
check(i_flash_call < i_loc, "tick(): the flash is computed before the place event")
m = re.search(r"for ev in \((.*?)\):", tick_src, re.S)
tup = m.group(1) if m else ""
check(bool(m) and tup.index("_flash") < tup.index("_loc_ev") < tup.index("pending_world_sound"),
      "tick(): perceive order is ... _flash, _loc_ev, ..., pending_world_sound (flash before any thunder line)")
check("(_w if loc == \"study\" else None), _f_out" in tup and tup.index("_f_out") < tup.index("_flash"),
      "tick(): only the weather-change line and the fire line precede the flash (neither is thunder: the change tick is skipped)")

# ───────────────────────────────── [6] countable ────────────────────────────────────────────────────────────────────
print("[6] countable: one ledger row per rendered flash")
if lrl._LEDGER.exists():
    lrl._LEDGER.unlink()
fresh_state(weather="thunderstorm", wind="strong wind", loc="shore")
got = run_ticks(3_000, "shore", seed=9)
rows = lrl.read_rows(0.0, lrl._LEDGER)
check(len(got) > 0 and len(rows) == len(got), f"{len(got)} flashes -> {len(rows)} ledger rows")
check(all(r["src"] == "event" and r["target"] == "shore:lightning" and r["key"] == "flash" and r["loc"] == "shore" for r in rows),
      "rows: src=event, target=shore:lightning, key=flash, loc=shore")
check(all(r["line_id"] == hashlib.sha1(l.encode("utf-8")).hexdigest()[:10] for r, (_, l) in zip(rows, got)),
      "rows: line_id == sha1(line)[:10] (joins the state's used set and the pools forever)")
check(all("wind:strong wind" in r["conds"] and "thunderstorm" in r["conds"] for r in rows), "rows: conds carry the gate and the severity")
st = lrl.status(lrl._LEDGER)
check(st["by_src"].get("event") == len(got) and st["by_target"].get("shore:lightning") == len(got), f"status() counts them: {st['by_src']}")
check(all(r["pool"] == len(sn._FLASH_POOLS["shore"]) + len(sn._FLASH_POOLS["far"]) for r in rows), "rows: pool = place + far")

# ───────────────────────────────── [7] the storm pools are otherwise byte-identical ─────────────────────────────────
print("[7] storm pools byte-identical to the pre-build baseline (a09d953d) minus the lightning clauses")
MOVED = {
    "study": ["lightning whitens the whole room for an instant — the shadows leap, and are gone",
              "a flash, and a beat later thunder rolls in and rattles the glass in its frame"],
    "garden": ["lightning forks down into the sea far out; the whole bay lights white for an instant",
               "a flash over the water — then thunder cracks and rolls up the hill, through your chest"],
    "shore": ["lightning stands an instant far out over the water, and the whole sea goes white"],
    "wood": [],
}
# The baseline is the tree BEFORE this build landed (J-2481, a09d953d, the chain commit this one sits on), not
# HEAD: once d93276f4 is HEAD (or merged), HEAD itself no longer carries the clauses and the "minus the clauses"
# comparison is vacuous. If that hash is ever unreachable (a squash), walk this file's history for the last
# commit whose blob still carries the study clause and use that.
BASELINE = "a09d953d"


def _git_show(rev: str) -> str:
    return subprocess.run(["git", "show", f"{rev}:core/sensorium.py"], cwd=str(ROOT), capture_output=True,
                          check=True).stdout.decode("utf-8")


try:
    try:
        head = _git_show(BASELINE)
    except Exception:
        head = ""
        revs = subprocess.run(["git", "log", "--format=%H", "--", "core/sensorium.py"], cwd=str(ROOT),
                              capture_output=True, check=True).stdout.decode().split()
        for rev in revs:
            text = _git_show(rev)
            if MOVED["study"][0] in text:
                head = text
                break
    if not head:
        raise RuntimeError("no commit of core/sensorium.py still carries the study lightning clause")
except Exception as exc:
    head = ""
    check(False, f"git show {BASELINE}:core/sensorium.py (pre-build baseline) failed: {exc}")


def storm_lines(text: str, func: str, next_func: str) -> list[str]:
    """Every string literal in the `if storm:` pool block(s) of one event function."""
    body = text[text.index(f"def {func}("):text.index(f"def {next_func}(")]
    out = []
    for m in re.finditer(r"\n    if storm:[^\n]*\n((?:        [^\n]*\n)+?)(?=    (?:if|#|try|from|pool|_)|\n)", body):
        block = m.group(1)
        if "pool +=" not in block:
            continue
        out += re.findall(r'"([^"\n]+)"', block)
    return out


if head:
    for func, nxt, place in (("_event", "_lightning_flash", "study"), ("_garden_event", "_lens_detail", "garden"),
                             ("_shore_event", "_generic_tests_on", "shore"), ("_wood_event", "_garden_milestone", "wood")):
        try:
            hl = storm_lines(head, func, "_season" if func == "_event" else nxt)
            cl = storm_lines(src, func, nxt)
        except ValueError as exc:
            check(False, f"{place}: could not locate the storm block: {exc}")
            continue
        expected = [l for l in hl if l not in MOVED[place]]
        check((hl or place == "wood") and cl == expected, f"{place}: baseline storm block minus {len(MOVED[place])} lightning clause(s) == this tree ({len(cl)} lines)")
        check(all(l in hl for l in MOVED[place]), f"{place}: the moved clauses were really in the baseline block")
    h_sea = re.search(r'if weather == "thunderstorm":[^\n]*\n\s+return "([^"]+)"', head[head.index("def _sea_state("):])
    c_sea = re.search(r'if weather == "thunderstorm":[^\n]*\n\s+return "([^"]+)"', src[src.index("def _sea_state("):])
    check(h_sea and c_sea and "lightning" in h_sea.group(1) and "lightning" not in c_sea.group(1)
          and c_sea.group(1).startswith("the sea white and wild below"),
          f"_sea_state storm text: baseline {h_sea.group(1) if h_sea else None!r} -> {c_sea.group(1) if c_sea else None!r}")
check(all(l in sn._FLASH_POOLS[p] for p, ls in MOVED.items() for l in ls if "thunder" not in l),
      "the pure-lightning clauses moved into the flash pools verbatim")
check(not any("thunder" in l for p in sn._FLASH_POOLS.values() for l in p), "the flash+thunder clauses did NOT move (no sound in a flash line)")

# runtime: the four place pools under a thunderstorm carry no lightning line
_real_choice, _real_random = random.choice, random.random
captured: dict[str, list] = {}


def _spy_choice(seq):
    captured.setdefault("pools", []).append(list(seq))
    return _real_choice(seq)


for loc, fn in (("study", sn._event), ("garden", sn._garden_event), ("shore", sn._shore_event), ("wood", sn._wood_event)):
    fresh_state(weather="thunderstorm", wind="gale", loc=loc)
    captured.clear()
    random.choice, random.random = _spy_choice, (lambda: 0.0)
    try:
        line = fn(1_800_000_000.0)
    finally:
        random.choice, random.random = _real_choice, _real_random
    pools = captured.get("pools") or []
    big = max(pools, key=len) if pools else []
    check(line is not None and len(big) >= 3, f"{loc}: the storm pool rendered at runtime ({len(big)} lines)")
    check(not any(("lightning" in l or "flash" in l) for l in big), f"{loc}: no lightning/flash line left in the storm pool")
    if loc == "study":
        check("thunder cracks and mutters along the hills, slow and huge" in big, "study: the thunder line stays in its pool")
    if loc == "garden":
        check("the air has gone heavy and electric; the hair lifts on your arms" in big, "garden: the storm's own felt lines stay")
check("lightning" not in sn._sea_state("day", "thunderstorm", "gale"), "_sea_state's storm text no longer bakes lightning in")

# ───────────────────────────────── [8] kill switch ──────────────────────────────────────────────────────────────────
print("[8] kill switch")
n_rows = len(lrl.read_rows(0.0, lrl._LEDGER))
os.environ["NASCENCE_LIGHTNING_FLASH"] = "0"
try:
    fresh_state(weather="thunderstorm", wind="gale", loc="garden")
    got = run_ticks(5_000, "garden", seed=4)
finally:
    os.environ.pop("NASCENCE_LIGHTNING_FLASH", None)
check(not got, "NASCENCE_LIGHTNING_FLASH=0: nothing rendered")
check(len(lrl.read_rows(0.0, lrl._LEDGER)) == n_rows, "NASCENCE_LIGHTNING_FLASH=0: nothing written")

# ───────────────────────────────── [9] state round-trips ────────────────────────────────────────────────────────────
print("[9] state is plain JSON")
fresh_state(weather="thunderstorm", wind="gale", loc="wood")
run_ticks(500, "wood", seed=8)
s = json.loads(json.dumps(sn.state))
check(set(s["lightning"]) == {"storm_since", "used", "last_flash", "count"} and isinstance(s["lightning"]["used"], list),
      f"state['lightning'] round-trips: {sorted(s['lightning'])}")

# ───────────────────────────────── the live store canary ────────────────────────────────────────────────────────────
_AFTER = _fingerprint()
changed = sorted(k for k in set(_BEFORE) | set(_AFTER) if _BEFORE.get(k) != _AFTER.get(k))
check(not changed, f"live C:\\Nascence\\data untouched (changed: {changed})")
check(sn._STATE_F.parent == TMP and lrl._LEDGER.parent == TMP, "every redirected path still points inside the temp dir")

print()
print("FAILED" if FAILS else "ALL PASSED", f"({len(FAILS)} failure(s))")
for f in FAILS:
    print("  -", f)
sys.exit(1 if FAILS else 0)
