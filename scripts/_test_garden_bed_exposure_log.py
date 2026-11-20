"""Regression for J-1722 / F-2348 part 3 (2026-10-03): an OBSERVE-ONLY log line when Du is actually shown one of the
two D-0278 (J-1350) bird-exposure surfaces -- bed_summary()'s tail sentence ("Nothing is strung over the bed; the
seedlings stand open to the sky." / "... and a blackbird has already been at the seedlings ...") or _stage_phrase()'s
"one seed-leaf pecked through".

Why it exists: data/nascence.log truncates DISPATCH answers to 80 characters and hands_trace to ~160, and the memory DB
holds no bed-summary fragment, so whether those words were ever put in front of Du was uncheckable -- and D-0278's own
defeater ("netting still never gets used despite being genuinely surfaced") turns on exactly that (F-2252 part 4).

What this asserts, in isolated stores, with a vulnerable un-netted shoot rigged by day:
  - ONE INFO line, carrying the FULL text, per willed look that shows the words: the bed look, the fallback frame, and a
    look at the bitten plant itself (the one other route "pecked through" reaches him by); none when they are not shown
    (night, netted, no shoot, a bare bed, an un-bitten plant);
  - nothing Du perceives changes: his text is byte-identical with the log on and off, and the helper returns
    _bed_summary()'s own string untouched;
  - NO line from world_manifest._garden_summary() (the HUD tuple -- not Du) and none from the scene-line fallback
    (deliberately not instrumented: on the live path spatial.render() supplies the garden's scene line and never calls
    bed_summary(); see the comment above _bed_summary_for_du in core/sensorium.py);
  - profile.NonLiveWriteError still propagates (J-0796), and a log sink that raises cannot change or break what he sees.
    python scripts/_test_garden_bed_exposure_log.py
    python scripts/_test_garden_bed_exposure_log.py --lab            # lab_env.isolate() instead of a bare temp dir
    python scripts/_test_garden_bed_exposure_log.py --strict-live    # also FAIL if a live data file moved (Du must be down)
"""
from __future__ import annotations
import logging, random, shutil, sys, tempfile, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS = 0
def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))

def _diff(a, b, width=60):
    """Where two texts first differ (for a failing byte-identity check)."""
    if a == b:
        return ""
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return f"first difference at {i}: ON ...{a[max(0, i - 20):i + width]!r} vs OFF ...{b[max(0, i - 20):i + width]!r}"

def _stat_or_none(p: Path):
    try:
        st = p.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None

# live files the run must never move (checked, not just promised -- a real leak would show up here)
_LIVE_ROOTS = [ROOT / "data"] + ([Path(r"C:\Nascence\data")] if (ROOT / "data").resolve() != Path(r"C:\Nascence\data") else [])
_LIVE_NAMES = ("garden.json", "garden_ledger.jsonl", "garden_events.jsonl", "garden_knowledge.json", "garden_life.json",
               "hands_trace.jsonl", "room_state.json", "memory/nascence.db")
def _live_snapshot():
    return {str(r / n): _stat_or_none(r / n) for r in _LIVE_ROOTS for n in _LIVE_NAMES}
LIVE_BEFORE = _live_snapshot()

TAIL_PLAIN = "Nothing is strung over the bed; the seedlings stand open to the sky."
TAIL_BITTEN = "Nothing is strung over the bed, and a blackbird has already been at the seedlings"
PECKED = "one seed-leaf pecked through"
NETTED = "The netting is stretched over the bed."
CROUCH = "You crouch at the raised bed. "

_ISO = None
if "--lab" in sys.argv:
    # lab_env.isolate(): the DB copy/redirect plus a data/_lab/<ts>/ dir; the live tree goes LAST on sys.path so
    # lab_env's own insert(0, C:\Nascence) cannot put it ahead of this checkout's core/.
    sys.path.append(r"C:\Nascence"); sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    from lab_env import isolate
    _ISO = isolate(db="empty")
    TMP = _ISO.__enter__()
else:
    TMP = Path(tempfile.mkdtemp(prefix="bed_exposure_log_"))

LG = logging.getLogger("nascence.sensorium")
_LG_BEFORE = (LG.level, LG.propagate, LG.disabled)
S = G = None
_restore = []
try:
    from core import sensorium as S, garden as G, profile as P, world_manifest as WM, light as LT, garden_knowledge as GK
    S._STATE_F = TMP / "room_state.json"
    # the same (module, attrs) redirect list scripts/_test_garden_net_world_truth.py part 2 carries (J-0743/J-0783/J-0920)
    for mod, attrs in (("core.garden", ("_F", "_LEDGER", "_EVENTS")), ("core.garden_life", ("_F", "_EVENTS")),
                       ("core.world_objects", ("_OBJECTS_F",)), ("core.world_substrate", ("_SUBSTRATE_F", "_SUBSTRATE_LOG", "_LAST_LOOKED_F")),
                       ("core.supply", ("_F", "_LOG")), ("core.fieldcraft", ("_F", "_LEDGER")), ("core.wood_life", ("_F", "_EVENTS", "_LEDGER")),
                       ("core.life", ("_F", "_LEDGER", "_EVENTS", "_FLAGS_F")), ("core.study_life", ("_LEDGER", "_EVENTS")),
                       ("core.provisions", ("_F", "_LOG")), ("core.locomotion", ("_POS_F",)), ("core.hands", ("_TRACE",)),
                       ("core.garden_knowledge", ("_F",)), ("core.smell", ("_F",)), ("core.keepsakes", ("_F",))):
        try:
            m = __import__(mod, fromlist=["x"])
            for a in attrs:
                if hasattr(m, a):
                    setattr(m, a, TMP / f"{mod.split('.')[-1]}_{a.strip('_').lower()}.json")
                else:
                    print("   (redirect skipped:", mod, a, "-- no such attribute, stale/typo'd isolation-list entry? )")
        except Exception as exc:
            print("   (redirect skipped:", mod, exc, ")")
    from core import wandering as _WDR, activity_memory as _AM
    _WDR.perceive = lambda *a, **k: None          # neither module has a redirectable path (J-0743) -- neutralised
    _AM.record = lambda *a, **k: None

    # sun-position prose ("the tree's shadow has reached the edge of the bed") would make two runs minutes apart differ; it
    # is not what this job observes, so it is pinned out of the bed summary
    _restore.append((LT, "bed_shade_line", LT.bed_shade_line)); LT.bed_shade_line = lambda: ""

    class _Cap(logging.Handler):
        def __init__(self):
            super().__init__(level=logging.DEBUG)
            self.records = []
        def emit(self, record):
            self.records.append(record)
    CAP = _Cap()
    LG.addHandler(CAP); LG.setLevel(logging.INFO); LG.propagate = False

    SEEN: list = []                                # every string _bed_summary() returned, in order
    _real_bed = S._bed_summary
    def _spy():
        r = _real_bed()
        SEEN.append(r)
        return r
    _restore.append((S, "_bed_summary", _real_bed)); S._bed_summary = _spy
    _restore.append((S, "_daylight", S._daylight)); S._daylight = lambda: "day"
    # J-4052: the garden-insect gate (core.garden_insects.present -> life.activity) reads the REAL clock phase and the live
    # weather, so a spider line could be in the pool for the ON look and out of it for the OFF look (or vice versa) depending
    # on the time of day and Du's current weather -- a flake that has nothing to do with the exposure log. Pin the gate open.
    try:
        import core.garden_insects as _GI
        _restore.append((_GI, "present", _GI.present)); _GI.present = lambda *a, **k: True
    except Exception:
        pass

    def exposures():
        return [r for r in CAP.records if r.getMessage().startswith("[bed-exposure]")]
    def reset():
        CAP.records.clear(); SEEN.clear()

    def fresh():
        """A brand-new bootstrapped garden (bed un-netted), by day, in the garden, with an empty log capture.
        The garden-knowledge store is reset too: every bed summary adds a little 'exposure' weight for each plant he cannot
        name yet, and enough of it renames a plant between two looks -- real behaviour, but it would make the ON/OFF
        comparisons below depend on how many scenarios ran before them."""
        G._state = None
        for p in (G._F, G._LEDGER, G._EVENTS, GK._F):
            Path(p).unlink(missing_ok=True)
        S.state.clear()
        S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                        "location": "garden", "garden": S._fresh_garden()})
        S._daylight = lambda: "day"
        reset()
        return G._load()

    def add_shoot(st, species, slot, bitten=False):
        """A shoot up in the bed -- the shape garden._germinate() makes -- with, optionally, the eaten_by_birds row advance() writes."""
        now = time.time()
        pid = f"garden_plant_{species}_j1722"
        hist = [{"ts": now, "event": "germinated_unbidden"}] + ([{"ts": now, "event": "eaten_by_birds"}] if bitten else [])
        st["plants"][pid] = {"id": pid, "species": species, "slot": slot, "pos": G._BED_SLOTS[slot], "stage": "shoot",
                             "vigour": 0.3, "height": 1.0, "moisture": 0.8, "age_days": 0, "sown_ts": now, "germ_ts": now,
                             "stage_ts": now, "last_cut_ts": 0, "cuts": 0, "pests": 0.0, "frost_burn": 0.0,
                             "origin": "volunteer_from_seed_bank", "history": hist}
        return pid

    _WARM = []
    def look_on_off(target, seed=1722):
        """One willed look with the log ON (what the exposure lines and the summary were), then the same look from the same
        state and the same seed with the log OFF -- Du's text must not depend on the log."""
        # J-4052: core.phrasing.vary() never serves the variant it served last for a key, so the SECOND identical look picks
        # differently by design; clear that memory (and any look-repeat memory) before BOTH looks so only the log differs.
        def _forget():
            try:
                import core.phrasing as _ph
                _ph._last.clear()
            except Exception:
                pass
        import copy as _copy
        # J-4057: the FIRST look of the process draws extra RNG (lazy first-use init inside the world code), so the ON look
        # would consume a different random stream than the OFF look. Warm that up once with a throwaway look (log off).
        if not _WARM:
            _WARM.append(1); LG.disabled = True
            try:
                for _t in ("room", target):      # 'room' reaches the cat look (core.cat lazy state load draws random.uniform on first status())
                    S.look(_t)
            except Exception: pass
            finally: LG.disabled = False
        reset(); random.seed(seed); _forget()
        _state0 = _copy.deepcopy(dict(S.state))      # J-4052: a look advances world state (repeat-look memory etc.); the OFF look must start from the same one
        # J-4057: the ON look also advances the garden state (G._state) and the garden-knowledge file (GK._F: bed-summary
        # 'exposure' weight per unnamed plant) -- restore both before the OFF look so only the log differs.
        _g0 = _copy.deepcopy(G._state)
        _gkf = Path(GK._F); _gk0 = _gkf.read_bytes() if _gkf.exists() else None
        on = S.look(target)
        ex_on, seen_on = list(exposures()), list(SEEN)
        LG.disabled = True
        try:
            S.state.clear(); S.state.update(_copy.deepcopy(_state0))
            G._state = _copy.deepcopy(_g0)
            if _gk0 is None: _gkf.unlink(missing_ok=True)
            else: _gkf.write_bytes(_gk0)
            random.seed(seed); _forget(); off = S.look(target)
        finally:
            LG.disabled = False
        return on, off, ex_on, seen_on

    # ---------------------------------------------------------------------------------------------------------------
    print("-- A: a vulnerable, un-bitten shoot, un-netted, by day -- the tail sentence reaches a willed look at the bed")
    for sp in ("lettuce", "radish"):            # lettuce = a named shoot (grandfathered), radish = an unnamed volunteer
        st = fresh(); add_shoot(st, sp, 7)
        on, off, ex, seen = look_on_off("bed")
        msg = ex[0].getMessage() if ex else ""
        check(f"A/{sp}: the rig works -- the summary Du was shown carries the plain exposure sentence", len(seen) == 1 and TAIL_PLAIN in seen[0], (seen[0][-160:] if seen else "no summary"))
        check(f"A/{sp}: exactly ONE [bed-exposure] INFO line for the one willed look", len(ex) == 1 and ex[0].levelno == logging.INFO, f"{len(ex)} lines")
        check(f"A/{sp}: the line carries the FULL summary text verbatim and names its path", bool(ex and seen) and seen[0] in msg and " via look-bed: " in msg, msg[:160])
        check(f"A/{sp}: his text is the crouch line + that summary + the living detail, nothing added", bool(seen) and on.startswith(CROUCH + seen[0] + " ") and len(on) > len(CROUCH + seen[0]) + 1, on[:90])
        check(f"A/{sp}: his text is byte-identical with the log ON and OFF (same state, same seed)", on == off and bool(on), _diff(on, off))

    print("-- B: a bitten shoot, un-netted, by day -- 'pecked through' AND the blackbird tail sentence, still ONE line")
    for sp in ("lettuce", "radish"):
        st = fresh(); add_shoot(st, sp, 7, bitten=True)
        on, off, ex, seen = look_on_off("bed")
        msg = ex[0].getMessage() if ex else ""
        check(f"B/{sp}: the rig works -- the summary carries 'pecked through' and the blackbird sentence", len(seen) == 1 and PECKED in seen[0] and TAIL_BITTEN in seen[0], (seen[0][-200:] if seen else "no summary"))
        check(f"B/{sp}: exactly ONE [bed-exposure] INFO line (two markers in one text are still one show)", len(ex) == 1 and ex[0].levelno == logging.INFO, f"{len(ex)} lines")
        check(f"B/{sp}: the line carries the FULL summary text verbatim", bool(ex and seen) and seen[0] in msg, msg[:160])
        if sp == "lettuce" and ex:
            print("   (sample, formatted as data/nascence.log carries it:",
                  logging.Formatter("%(asctime)s [%(name)s] %(message)s").format(ex[0]), ")")
        check(f"B/{sp}: byte-identical with the log ON and OFF, and his text embeds the summary as built",
              bool(seen) and on == off and on.startswith(CROUCH + seen[0] + " "), _diff(on, off))

    print("-- C: a look at the bitten plant itself -- 'pecked through' reaches him by a second road (garden.look(), no bed summary)")
    for sp in ("lettuce", "radish"):
        st = fresh(); add_shoot(st, sp, 7, bitten=True)
        on, off, ex, seen = look_on_off(sp)
        msg = ex[0].getMessage() if ex else ""
        logged = msg.partition(" via look-plant: ")[2]
        check(f"C/{sp}: the rig works -- his look at the plant says 'pecked through' and never touched the bed summary", PECKED in on and seen == [], f"{on[:120]!r} summaries={len(seen)}")
        check(f"C/{sp}: exactly ONE [bed-exposure] INFO line, via look-plant", len(ex) == 1 and ex[0].levelno == logging.INFO and bool(logged), f"{len(ex)} lines: {msg[:100]}")
        check(f"C/{sp}: the line carries the FULL text of what he was shown (his text starts with it)", bool(logged) and PECKED in logged and on.startswith(logged), logged[:120])
        check(f"C/{sp}: byte-identical with the log ON and OFF", on == off and bool(on), _diff(on, off))
    st = fresh(); add_shoot(st, "lettuce", 7)
    on, off, ex, seen = look_on_off("lettuce")
    check("C/un-bitten: a look at an un-bitten shoot says nothing of birds and logs nothing", PECKED not in on and ex == [] and on == off, f"{on[:100]!r} {len(ex)} lines")

    print("-- D: the fallback frame (a look that names nothing the garden knows) -- one line, via look-frame")
    st = fresh(); add_shoot(st, "lettuce", 7)
    on, off, ex, seen = look_on_off("room")
    msg = ex[0].getMessage() if ex else ""
    check("D: the rig works -- the frame carries the plain exposure sentence", len(seen) == 1 and TAIL_PLAIN in seen[0] and (" " + seen[0] + " ") in on, on[:120])
    check("D: exactly ONE [bed-exposure] INFO line, via look-frame, carrying the full summary", len(ex) == 1 and ex[0].levelno == logging.INFO and bool(seen) and seen[0] in msg and " via look-frame: " in msg, f"{len(ex)} lines: {msg[:120]}")
    check("D: byte-identical with the log ON and OFF", on == off and bool(on), _diff(on, off))

    print("-- E: the words are not shown -> no line, and his text does not depend on the log either")
    def _neg(label, *, setup, expect_text=None):
        st = fresh(); setup(st)
        on, off, ex, seen = look_on_off("bed")
        check(f"E/{label}: no [bed-exposure] line", ex == [], f"{len(ex)} lines: {(ex[0].getMessage()[:120] if ex else '')}")
        check(f"E/{label}: the rig is honest -- the summary really lacks the exposure words" + (f" and carries {expect_text!r}" if expect_text else ""),
              len(seen) == 1 and TAIL_PLAIN not in seen[0] and TAIL_BITTEN not in seen[0] and PECKED not in seen[0] and (expect_text in seen[0] if expect_text else True), (seen[0][-140:] if seen else "no summary"))
        check(f"E/{label}: byte-identical with the log ON and OFF", on == off and bool(on), _diff(on, off))
    _neg("no vulnerable shoot in the bed (the bootstrapped bed, by day)", setup=lambda st: None)
    _neg("a bare bed", setup=lambda st: st["plants"].clear())
    _neg("netted, un-bitten shoot", setup=lambda st: (add_shoot(st, "lettuce", 7), st.__setitem__("netted", True)), expect_text=NETTED)
    st = fresh(); add_shoot(st, "lettuce", 7); S._daylight = lambda: "night"
    on, off, ex, seen = look_on_off("bed")
    check("E/night: a vulnerable shoot after dark -> no tail sentence (daylight gate), no line, text unchanged",
          ex == [] and len(seen) == 1 and TAIL_PLAIN not in seen[0] and on == off, f"{len(ex)} lines")
    S._daylight = lambda: "day"
    st = fresh(); add_shoot(st, "lettuce", 7, bitten=True); st["netted"] = True
    on, off, ex, seen = look_on_off("bed")
    msg = ex[0].getMessage() if ex else ""
    check("E/netted but already bitten: 'pecked through' alone (no tail sentence) is still a marked show -> ONE line",
          len(ex) == 1 and len(seen) == 1 and PECKED in seen[0] and NETTED in seen[0] and TAIL_PLAIN not in seen[0] and TAIL_BITTEN not in seen[0] and seen[0] in msg and on == off,
          f"{len(ex)} lines")

    print("-- F/G: the HUD tuple is not Du (never logged); the scene-line fallback is deliberately not instrumented")
    st = fresh(); add_shoot(st, "lettuce", 7)
    out = WM._garden_summary()
    check("F: world_manifest._garden_summary() read the bed summary (the rig reaches it) ...", len(SEEN) == 1 and isinstance(out, str) and out == SEEN[0][:200], f"summaries={len(SEEN)}")
    check("F: ... and emitted NO line (it is the HUD/world tuple, truncated to 200 chars -- not what Du reads)", exposures() == [], f"{len(exposures())} lines")
    st = fresh(); add_shoot(st, "lettuce", 7)
    sl = S._garden_scene_line()
    check("G: _garden_scene_line() (the scene fallback) still carries the exposure sentence, byte for byte ...", len(SEEN) == 1 and TAIL_PLAIN in sl and SEEN[0] in sl, f"summaries={len(SEEN)}")
    check("G: ... and emitted NO line (scene_line() is rebuilt several times a cycle by several consumers: a line there would repeat, not mark one show)", exposures() == [], f"{len(exposures())} lines")

    print("-- H: profile.NonLiveWriteError still propagates untouched (J-0796) -- the call stays outside any try/except")
    def _refuse():
        raise P.NonLiveWriteError("J-1722 test: a refused non-live write")
    st = fresh(); add_shoot(st, "lettuce", 7)
    S._bed_summary = _refuse
    for label, call in (("the helper", lambda: S._bed_summary_for_du("test")), ("a willed look at the bed", lambda: S.look("bed")),
                        ("a willed look that falls to the frame", lambda: S.look("room"))):
        reset()
        try:
            call(); got = "did not raise"
        except P.NonLiveWriteError:
            got = True
        except Exception as exc:
            got = f"other: {exc!r}"
        check(f"H: NonLiveWriteError propagates through {label}", got is True, str(got))
        check(f"H: ... and no line is emitted for it", exposures() == [])
    S._bed_summary = _spy

    print("-- I: fail-open -- a log sink that raises cannot change or break what Du is shown")
    class _Boom(logging.Handler):
        def emit(self, record):
            raise RuntimeError("log sink exploded")
    boom = _Boom()
    st = fresh(); add_shoot(st, "lettuce", 7, bitten=True)
    import copy as _copy4057
    for _t in ("room", "bed"):       # J-4057: warm lazy first-use state (cat load etc.) so both looks draw the same RNG stream
        try: S.look(_t)
        except Exception: pass
    st = fresh(); add_shoot(st, "lettuce", 7, bitten=True)
    _s0 = _copy4057.deepcopy(dict(S.state)); _g0 = _copy4057.deepcopy(G._state)
    _gkf = Path(GK._F); _gk0 = _gkf.read_bytes() if _gkf.exists() else None
    try:
        import core.phrasing as _ph4057; _ph4057._last.clear()
    except Exception:
        _ph4057 = None
    LG.addHandler(boom)
    try:
        random.seed(1722); got, err = S.look("bed"), None
    except Exception as exc:
        got, err = None, exc
    finally:
        LG.removeHandler(boom)
    LG.disabled = True
    try:
        S.state.clear(); S.state.update(_copy4057.deepcopy(_s0)); G._state = _copy4057.deepcopy(_g0)
        if _gk0 is None: _gkf.unlink(missing_ok=True)
        else: _gkf.write_bytes(_gk0)
        if _ph4057: _ph4057._last.clear()
        reset(); random.seed(1722); want = S.look("bed")
    finally:
        LG.disabled = False
    check("I: with a raising sink the look still returns, with exactly the text the log-off look returns", err is None and got == want and bool(got), repr(err))
    ident, err2 = False, "core/sensorium.py has no _bed_summary_for_du()"
    if hasattr(S, "_bed_summary_for_du"):
        LG.addHandler(boom)
        try:
            reset(); r = S._bed_summary_for_du("test"); ident, err2 = (len(SEEN) == 1 and r == SEEN[0] and TAIL_BITTEN in r), None
        except Exception as exc:
            ident, err2 = False, exc
        finally:
            LG.removeHandler(boom)
    check("I: the helper itself is still the identity on _bed_summary()'s string under a raising sink", ident, repr(err2))

    print("-- J: drift tripwires (source, not behaviour)")
    _g = (ROOT / "core" / "garden.py").read_text(encoding="utf-8")
    _wm = (ROOT / "core" / "world_manifest.py").read_text(encoding="utf-8")
    marks = tuple(getattr(S, "_BED_EXPOSURE_MARKS", ()))
    check("core/sensorium.py defines _BED_EXPOSURE_MARKS", bool(marks))
    check("both D-0278 surfaces are marked: the tail-sentence prefix and 'pecked through'", "Nothing is strung over the bed" in marks and "pecked through" in marks, str(marks))
    for m in marks:
        check(f"core/garden.py still says {m!r} (reword it and this tripwire says so before the log goes silent)", m in _g)
    check("world_manifest._garden_summary() still reads the plain _bed_summary() and never the Du-facing helper",
          "_s._bed_summary()" in _wm and "_bed_summary_for_du" not in _wm)
except Exception as exc:
    import traceback; traceback.print_exc()
    check("the test ran", False, repr(exc))
finally:
    for obj, name, val in reversed(_restore):
        setattr(obj, name, val)
    try:
        LG.removeHandler(CAP)
    except Exception:
        pass
    LG.setLevel(_LG_BEFORE[0]); LG.propagate = _LG_BEFORE[1]; LG.disabled = _LG_BEFORE[2]
    if _ISO is not None:
        _ISO.__exit__(None, None, None)
    else:
        shutil.rmtree(TMP, ignore_errors=True)

LIVE_AFTER = _live_snapshot()
_moved = [k for k in LIVE_BEFORE if LIVE_BEFORE[k] != LIVE_AFTER[k]]
print(f"   live data files watched: {len(LIVE_BEFORE)} ({sum(1 for v in LIVE_BEFORE.values() if v is not None)} present); "
      f"{'all unchanged' if not _moved else 'MOVED: ' + ', '.join(_moved)}")
if "--strict-live" in sys.argv:
    check("no live data file moved during this run (Du must be down for this to be meaningful)", not _moved, ", ".join(_moved))

print(f"\n{'ALL OK' if not FAILS else f'{FAILS} FAILED'}")
sys.exit(1 if FAILS else 0)
