"""Regression for J-1680 / F-2252 (2026-10-03): core/garden.py net() must answer TRUE to the world.

On 2026-09-28 17:23:30 NZDT Du's purely DESCRIPTIVE thought ("... I stand still as the cold eases off me,
watching the low west light stretch across the thyme bed ...") fired the net family (verb "stretch" + object
"bed"; literal_will_shadow.jsonl line 138428: verdict DEED, volition FALSE) and net() -- which chose the
un-net direction with a bare substring test over the WHOLE thought ("off" in "eases off me") and never asked
whether the bed was netted -- answered "You lift the netting off the bed, roll it, and lean it against the
wall." and wrote {"deed": "unnet"} to data/garden_ledger.jsonl for a bed that was never netted (garden.json
netted False; the netting still at its creation position). A world-truth contamination hit (plan
garden_upgrade section 3 metric 5), and the garden's only net-family ledger row -- the very row D-0278's
defeater check looks for.

Extended 2026-10-03 by J-1749 / F-2378 (same day, restart-gated like J-1680): the net hand now has a HAND-LEVEL AGENT
GUARD (core/garden.py _wills_net / _net_reads: a verb occurrence counts only when its own sentence shows an agent
willing it) and a VERB-BOUND DIRECTION (the direction of the occurrence that passed: lift / take off = un-net,
every other table verb = net; bare off / remove / "take the net" are no longer evidence). Before it, ordinary
descriptive prose ("The long shadows stretch across the bed.") still reached the hand and netted the bed for
real, "I take the netting and stretch it over the bed." read un-net and "I lift the netting from the bed." read
net. The 09-28 sentence is now DECLINED at the gate (the hand writes nothing and answers nothing) rather than
answered with the honest no-netting line -- the J-1680 world-truth answers stay for a will that reaches the hand.

Extended 2026-10-04 by J-1772 / D-0344 (F-2378 part 2, restart-gated like the two above): Travis ruled "Yes: add untangle
and secure" -- the net row in core/actions.py now carries Du's own netting words (and only those two), and the J-1749 guard
above is what makes them safe. The two genuine netting wills of the whole record (both 2026-09-02, neither of which ever
reached the hand because neither verb was in the row) now reach the hand, read NET and net the bed; the four false reads the
bare words make (two refusals, a felt urge, the 09-28 prose) are declined with zero ledger rows, on a bare AND a netted bed.

Part 1 is pure: the direction rule, the agent guard (gate, veto reasons) and the small world-truth helpers net()
answers from.
Part 2 drives garden.act_from_thought(thought, "", family="net") -- the exact call the dispatcher made --
with every store it touches redirected into a temp dir (the life_smoke isolation pattern; `--lab` takes that
dir AND the DB redirect from lab_env.isolate(db="empty") instead), and asserts what the world ANSWERED and
what it WROTE: a transition is claimed (and logged, and moved) only when it really happened, and prose that is
not an agent's will is declined with zero ledger rows and nothing moved, on a bare AND a netted bed.
    python scripts/_test_garden_net_world_truth.py
    python scripts/_test_garden_net_world_truth.py --lab            # lab_env.isolate() instead of a bare temp dir
    python scripts/_test_garden_net_world_truth.py --strict-live    # also FAIL if a live data file moved (Du must be down)
"""
from __future__ import annotations
import json, shutil, sys, tempfile
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

def _stat_or_none(p: Path):
    try:
        st = p.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None

# The exact thought (data/monologue_log.jsonl line 54693) and the head of it the hand actually received
# (data/hands_trace.jsonl line 26528 keeps the first ~200 characters).
THOUGHT_0928 = ("The tui's click cuts through the circling argument. I stand still as the cold eases off me, watching "
                "the low west light stretch across the thyme bed. The scrape on the floor feels less like a flaw now "
                "and more like a start. I am ready to let the words evaporate and simply be here in the garden.")
THOUGHT_0928_HAND = THOUGHT_0928[:THOUGHT_0928.index(" and more like a start")]

# live files the run must never move (checked, not just promised -- a real leak would show up here)
_LIVE_ROOTS = [ROOT / "data"] + ([Path(r"C:\Nascence\data")] if (ROOT / "data").resolve() != Path(r"C:\Nascence\data") else [])
_LIVE_NAMES = ("garden.json", "garden_ledger.jsonl", "garden_events.jsonl", "garden_knowledge.json", "garden_life.json",
               "hands_trace.jsonl", "memory/nascence.db")
def _live_snapshot():
    return {str(r / n): _stat_or_none(r / n) for r in _LIVE_ROOTS for n in _LIVE_NAMES}
LIVE_BEFORE = _live_snapshot()

print("-- part 1: the direction rule and the world-truth helpers (pure)")
from core import garden as G

# (text, expected direction, why). J-1749 (F-2378): the direction is the VERB's own -- the direction of the net-family verb
# occurrence that PASSED the agent guard: lift and take off (contiguous or split) = un-net, every other table verb = net;
# the LAST passing occurrence in the first sentence that has one decides; the default is "net", as it always was. The bare
# words off / remove / 'take the net(ting)' are no longer evidence (they were J-1680's whole-word evidence rule).
DIR_CASES = (
    ("i stretch the netting over the bed", "net", "a plain net will"),
    ("i cover the seedlings with the netting", "net", "a plain net will"),
    ("i lift the netting off the bed", "unnet", "'lift' is an un-net verb"),
    ("i take off the netting", "unnet", "'take off' (contiguous) is an un-net verb"),
    ("i take the netting off the bed", "unnet", "the split phrasal 'take ... off' counts at its head word"),
    ("i lift the roll and take the net away from the bed", "unnet", "'lift' decides; 'take the net' is no longer evidence"),
    ("i take the net down from the bed", "net", "no family verb occurrence ('the net' is a noun) -> nothing to read; the gate never lets it reach net() anyway"),
    ("i lift the netting away and remove it from the bed", "unnet", "'lift' decides; 'remove' is no longer evidence"),
    ("i remove the netting from the bed", "net", "'remove' alone is no longer evidence (and is not a table verb: the gate does not read it)"),
    (THOUGHT_0928, "net", "its one table verb ('stretch') is VETOED (np_subject: 'the low west light stretch') so nothing passes -> the "
                          "default; the hand declines this thought at the gate (part 2), the old un-net reading came from the word 'off'"),
    ("i stretch the netting over the bed, then make a coffee", "net", "a plain net will; 'coffee' is irrelevant"),
    ("i stretch the netting over the bed, it is often windy here", "net", "a plain net will"),
    ("i stretch the netting over the bed and offer the birds the far corner", "net", "a plain net will"),
    ("i stretch the netting over the bed, an off-white sky behind it", "net", "a plain net will"),
    ("the cold eases off. i stretch the netting over the bed.", "net", "an 'off' in ANOTHER sentence is not evidence"),
    ("i stretch the netting over the bed. the cold eases off me.", "net", "an 'off' in ANOTHER sentence is not evidence"),
    ("", "net", "nothing to read -> the default direction"),
    # F-2378 (b): 'take the net(ting)' used to read un-net although the will is to stretch it over the bed
    ("i take the netting and stretch it over the bed.", "net", "F-2378 (b): the passing verb is 'stretch' -> net ('take the net' is no evidence)"),
    # F-2378 (d): lift was never un-net evidence in the old rule
    ("i lift the netting from the bed.", "unnet", "F-2378 (d): 'lift' is the un-net verb, with no 'off' anywhere"),
    ("i should lift the netting now that the seedlings are up.", "unnet", "F-2378 (d): 'lift'"),
    # F-2378 (e): the bare word 'off' (here 'lying far off') is no longer evidence
    ("i stretch the netting lying far off over the bed.", "net", "F-2378 (e): a bare 'off' is not evidence"),
    ("i stretch the netting over the bed, then lift it off again.", "unnet", "the LAST passing occurrence in the sentence decides"),
    ("i lift the netting and stretch it over the bed.", "net", "the LAST passing occurrence ('stretch') decides"),
    ("the shadows stretch across the bed. i lift the netting off the bed.", "unnet", "a sentence whose only occurrence is vetoed does not qualify; the next one does"),
    ("i stretch the netting over the bed. i lift it off again.", "net", "the FIRST qualifying sentence decides"),
)
if hasattr(G, "_net_direction"):
    for text, want, why in DIR_CASES:
        got = G._net_direction(text.lower())
        check(f"direction {want!r}: {text[:58]!r}{'...' if len(text) > 58 else ''} -- {why[:70]}", got == want, f"got {got!r}")
else:
    check("core/garden.py has _net_direction() (the verb-bound direction rule)", False)

# --- J-1749 / F-2378 acceptance table (the briefing's own probes). The gate + direction half is pure and checked here;
# part 2 drives each probe through act_from_thought(family="net") against a real isolated garden.
GENUINE_NET = (       # reaches the hand, direction net, one net row on a bare bed
    "I will stretch the netting over the bed.", "Stretch the netting over the bed.", "I stretch it over the bed.",
    "I should net the seedlings before the birds come.", "Let me cover the bed with the netting.",
    "I take the netting and stretch it over the bed.", "I feel I should stretch the netting over the bed.",
    "My hands stretch the netting over the bed.", "I lift the netting and stretch it over the bed.",
)
GENUINE_UNNET = (     # reaches the hand, direction unnet, one unnet row on a NETTED bed
    "I lift the netting off the bed.", "I take the netting off the bed.", "I will take off the netting.",
    "I lift the netting from the bed.", "I should lift the netting now that the seedlings are up.",
)
PROSE = (             # the hand declines: zero ledger rows, nothing moved, on a bare AND on a netted bed
    "I stand still as the cold eases off me, watching the low west light stretch across the thyme bed.",
    "The long shadows stretch across the bed.", "Shadows stretch across the bed.", "I watch the frost cover the bed.",
    "I feel the mist lift from the bed.", "The low light will stretch over the netting by evening.",
    "I watch the water stretch across the river bed.", "I stretch across the bed to reach the weeds.",
)
KNOWN_RESIDUAL = "I stretch my arms across the bed."     # agent plus body object: still passes (0 corpus hits; documented, NOT fixed here)
if hasattr(G, "_wills_net") and hasattr(G, "_net_reads"):
    for s in GENUINE_NET:
        check(f"genuine net reaches the hand and reads net: {s!r}", G._wills_net(s.lower()) is True and G._net_direction(s.lower()) == "net",
              f"gate {G._wills_net(s.lower())} dir {G._net_direction(s.lower())} reads {G._net_reads(s.lower())}")
    for s in GENUINE_UNNET:
        check(f"genuine un-net reaches the hand and reads unnet: {s!r}", G._wills_net(s.lower()) is True and G._net_direction(s.lower()) == "unnet",
              f"gate {G._wills_net(s.lower())} dir {G._net_direction(s.lower())} reads {G._net_reads(s.lower())}")
    for s in PROSE:
        check(f"prose is declined at the hand's gate: {s[:70]!r}", G._wills_net(s.lower()) is False,
              f"reads {G._net_reads(s.lower())}")
    check("KNOWN RESIDUAL (documented in F-2378, not fixed here): 'I stretch my arms across the bed.' still passes the guard",
          G._wills_net(KNOWN_RESIDUAL.lower()) is True)
    check("KNOWN RESIDUAL (the spec's intransitive rule): 'I lift up the netting off the bed.' is vetoed, 'I lift the netting up off the bed.' is not",
          G._wills_net("i lift up the netting off the bed.") is False and G._wills_net("i lift the netting up off the bed.") is True)
    check("the guard only ever NARROWS the shared gate: _wills_net(t) implies _wills(t, 'net') on every probe and direction case",
          all((not G._wills_net(x.lower())) or G._wills(x.lower(), "net")
              for x in GENUINE_NET + GENUINE_UNNET + PROSE + (KNOWN_RESIDUAL,) + tuple(c[0] for c in DIR_CASES)))

    # the veto REASONS: (sentence, the one reason its single table-verb occurrence is vetoed -- "" = passes)
    VETO_CASES = (
        ("the long shadows stretch across the bed.", "np_subject"),
        ("that bird netting will cover the bed.", "np_subject"),
        ("shadows stretch across the bed.", "intransitive"),
        ("i stretch across the bed to reach the weeds.", "intransitive"),
        ("i watch him stretch the netting over the bed.", "perception"),
        ("i heard it all stretch the netting over the bed.", "perception"),
        ("i am too tired to stretch the netting over the bed.", "refusal"),
        ("i refuse to stretch the netting over the bed.", "refusal"),
        ("i am unable to stretch the netting over the bed.", "refusal"),
        ("i feel the urge to stretch the netting over the bed.", "felt_want"),
        ("a sudden pull in my arms to stretch the netting over the bed.", "felt_want"),
        ("my hands stretch the netting over the bed.", ""),                    # "my" is NOT a determiner: an agent
        ("i stretch it over the bed.", ""),                                    # a pronoun object is not intransitive
        ("i notice the bed is bare and i should stretch the netting over it.", ""),   # "and i" breaks the perception chain
        ("the birds are coming, so i will stretch the netting over the bed.", ""),    # a comma breaks the determiner chain
        ("i lift the netting over the bed.", ""),                              # "lift" + "the" is not intransitive
    )
    for text, why in VETO_CASES:
        got = [r[3] for r in G._net_reads(text)]
        check(f"guard reason {why or 'PASS'!r}: {text!r}", len(got) == 1 and got[0] == why, f"got {got}")
else:
    check("core/garden.py has _wills_net() / _net_reads() (the net hand's agent guard)", False)

# --- J-1772 / D-0344 (2026-10-04): "untangle" and "secure" -- Du's own netting words -- are verbs of the net row in
# core/actions.py. They are safe ONLY behind the J-1749 guard above, and they point the NET direction. The two genuine
# netting wills of the whole record (F-2378: both 2026-09-02) reach the hand; the four false reads the bare words make
# (the 09-28 prose, two refusals, a felt urge) are read by the table gate but declined by the hand's guard.
from core import actions as AC
GENUINE_0902 = (
    # data/monologue_log.jsonl line 34483 (2026-09-02 16:06), as Du wrote it; then the clause as quoted in D-0344
    "I want to walk out to the garden and untangle that bird netting lying far off; the cat is waiting by the bed, and I need to "
    "put down this spinning worry about memory and updates into something physical with my hands.",
    "I want to walk out to the garden and untangle that bird netting lying far off",
    # data/literal_will_shadow.jsonl (2026-09-02 17:01), the clause
    "I cut back the brown woody stem, then reach for the tangled netting to secure the bed before the low sun sinks west.",
)
FALSE_0902 = (        # (sentence, the one veto reason the guard names): the table gate reads each; the hand declines each
    ("The bird netting lies there, tangled and useless, waiting for hands that refuse to untangle them while the world spins on.", "refusal"),
    ("I feel the pull of Aristotle's mean and the bird's dry rattle competing with the urge to untangle that netting.", "felt_want"),
    ("The pull toward the tangled netting tugs at me, urging me to stop analyzing and simply move, but I am too tired to untangle it now.", "refusal"),
    (THOUGHT_0928_HAND, "np_subject"),
)
MORE_GENUINE_D0344 = (   # (sentence, direction): ordinary first-person wills in the two new words, all pass the guard
    ("I will untangle the netting and spread it over the seedlings.", "net"),
    ("I should secure the bed with the netting.", "net"),
    ("Let me secure the netting over the bed.", "net"),
    ("I untangle it and secure the bed.", "net"),
    ("I untangle the netting and lift it off the bed.", "unnet"),     # the LAST passing occurrence ('lift') decides, as ever
    # the voice's STRUCTURED world act reaches the hand as "I will " + act_object (core/dispatch.py): the four real 2026-09-02 acts
    # (data/hands_trace.jsonl: act world "untangle the bird netting" 20:09 and 21:12, "untangle the netting" 21:13 and 23:28)
    ("I will untangle the bird netting", "net"),
    ("I will untangle the netting", "net"),
)
# KNOWN RESIDUALS (probes, NOT corpus: 0 of the 820 corpus texts has any of these shapes; documented, not fixed here -- the guard
# checks for an agent, not that the verb's object IS the netting; D-0344's defeater (a) -- a net row whose thought is not
# about the netting -- is exactly what the post-restart read of the ledger looks for):
RESIDUAL_D0344 = (
    "I want to untangle my thoughts by the bed.", "I feel secure in the bed of thyme.", "I secure the shutters and look at the bed.",
)
if hasattr(G, "_wills_net") and hasattr(G, "_net_reads"):
    _row = AC.BY_FAMILY["net"]
    check("D-0344: the net row carries untangle and secure -- and exactly the seven verbs, no other (reach for, tend, touch, pull, sort stay out)",
          tuple(_row.verbs) == ("net", "cover", "stretch", "take off", "lift", "untangle", "secure"), repr(_row.verbs))
    check("D-0344: the net row's objects are unchanged (the bare 'net' object stays out: the beach-net idiom)",
          tuple(_row.objects) == ("bed", "seedlings", "netting"), repr(_row.objects))
    check("D-0344: untangle and secure point the NET direction (neither is an un-net verb)",
          not ({"untangle", "secure"} & set(G._NET_UNNET_VERBS)) and set(G._NET_UNNET_VERBS) == {"lift", "take off"}, repr(G._NET_UNNET_VERBS))
    for s in GENUINE_0902:
        _r = G._net_reads(s.lower())
        check(f"D-0344 genuine 09-02 will reaches the hand, reads net, and its verb passes the guard: {s[:62]!r}",
              G._wills_net(s.lower()) is True and G._net_direction(s.lower()) == "net"
              and any(not x[3] and x[2] in ("untangle", "secure") for x in _r), f"gate {G._wills_net(s.lower())} dir {G._net_direction(s.lower())} reads {_r}")
    for s, why in FALSE_0902:
        _r = G._net_reads(s.lower())
        check(f"D-0344 false read [{why}]: the table gate reads it, the hand's guard declines it: {s[:62]!r}",
              G._wills(s.lower(), "net") is True and G._wills_net(s.lower()) is False and {x[3] for x in _r} == {why}, f"reads {_r}")
    for s, want in MORE_GENUINE_D0344:
        check(f"D-0344 ordinary will reaches the hand and reads {want!r}: {s!r}",
              G._wills_net(s.lower()) is True and G._net_direction(s.lower()) == want, f"gate {G._wills_net(s.lower())} dir {G._net_direction(s.lower())} reads {G._net_reads(s.lower())}")
    for s in RESIDUAL_D0344:
        check(f"KNOWN RESIDUAL (D-0344 defeater (a); 0 corpus hits, not fixed here): still passes the guard: {s!r}", G._wills_net(s.lower()) is True)
    check("D-0344: the guard still only NARROWS the shared gate on every new probe (_wills_net implies _wills)",
          all((not G._wills_net(x.lower())) or G._wills(x.lower(), "net")
              for x in GENUINE_0902 + RESIDUAL_D0344 + tuple(f[0] for f in FALSE_0902) + tuple(m[0] for m in MORE_GENUINE_D0344)))
else:
    check("core/garden.py has _wills_net() / _net_reads() (D-0344's two new verbs ride on the J-1749 guard)", False)

if hasattr(G, "_netted_now"):
    check("netted: flag set and the netting down -> netted", G._netted_now({"netted": True}, {"carried": False}) is True)
    check("netted: flag set but the netting is in his hands -> NOT netted (the flag only refreshes on the world tick)",
          G._netted_now({"netted": True}, {"carried": True}) is False)
    check("netted: flag clear -> not netted", G._netted_now({"netted": False}, {"carried": False}) is False)
    check("netted: no flag at all (an older save) -> not netted", G._netted_now({}, {}) is False)
else:
    check("core/garden.py has _netted_now() (the world-truth read net() guards on)", False)

if hasattr(G, "_no_netting_over_bed_line"):
    _l_wall = G._no_netting_over_bed_line({"carried": False, "pos": [7.2, 1.5, 0.0]})
    _l_hand = G._no_netting_over_bed_line({"carried": True, "pos": [5.5, 5.5, 0.6]})
    _l_else = G._no_netting_over_bed_line({"carried": False, "pos": [3.0, 9.0, 0.0]})
    _l_junk = G._no_netting_over_bed_line({"carried": False, "pos": "garbage"})
    check("honest line (at its rest spot): says nothing is over the bed and where the roll is",
          "no netting over the bed" in _l_wall and "by the wall" in _l_wall, repr(_l_wall))
    check("honest line (carried): says the roll is in his hands, not by the wall",
          "no netting over the bed" in _l_hand and "in your hands" in _l_hand and "wall" not in _l_hand, repr(_l_hand))
    check("honest line (set down elsewhere): names no place it cannot verify",
          "no netting over the bed" in _l_else and "wall" not in _l_else and "hands" not in _l_else, repr(_l_else))
    check("honest line survives a malformed position (never raises, still honest)", "no netting over the bed" in _l_junk, repr(_l_junk))
    check("no honest line claims a transition", not any("you lift" in x.lower() or "roll it" in x.lower() for x in (_l_wall, _l_hand, _l_else, _l_junk)))
else:
    check("core/garden.py has _no_netting_over_bed_line() (the honest answer to a lift with nothing to lift)", False)

# the twin of advance()'s own netted computation must keep reading what advance() reads -- a source tripwire, not a copy
_src = (ROOT / "core" / "garden.py").read_text(encoding="utf-8")
check("advance() still derives st['netted'] from the netting item (the world truth net() answers from)",
      'st["netted"] = bool(net.get("place") == "garden" and not net.get("carried")' in _src)

print("-- part 2: act_from_thought(family='net') answers what the world holds (isolated stores)")
_ISO = None
if "--lab" in sys.argv:
    # lab_env.isolate(): the DB copy/redirect plus a data/_lab/<ts>/ dir; the live tree goes LAST on sys.path so
    # lab_env's own insert(0, C:\Nascence) cannot put it ahead of this checkout's core/.
    sys.path.append(r"C:\Nascence"); sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
    from lab_env import isolate
    _ISO = isolate(db="empty")
    TMP = _ISO.__enter__()
else:
    TMP = Path(tempfile.mkdtemp(prefix="garden_net_truth_"))
try:
    from core import sensorium as S
    S._STATE_F = TMP / "room_state.json"
    # the same (module, attrs) redirect list scripts/_test_garden_grammar_derivation.py part 2 carries (J-0743/J-0783/J-0920)
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
    _AM.record = lambda *a, **k: None             # (garden._log()'s own deed cross-link calls this)

    def fresh():
        """A brand-new bootstrapped garden -- bed un-netted, the netting at its creation position -- and an empty ledger."""
        G._state = None
        for p in (G._F, G._LEDGER, G._EVENTS):
            Path(p).unlink(missing_ok=True)
        S.state.clear()
        S.state.update({"weather": "clear", "wind": "breeze", "fire": "out", "fire_fuel": 0.0, "last_event": 0,
                        "location": "garden", "garden": S._fresh_garden()})
        return G._load()

    def rows():
        try:
            return [{k: v for k, v in json.loads(ln).items() if k != "ts"}
                    for ln in Path(G._LEDGER).read_text(encoding="utf-8").splitlines() if ln.strip()]
        except FileNotFoundError:
            return []

    def snap(st):
        it = st["items"]["netting"]
        return {"netted": st.get("netted"), "pos": list(it["pos"]), "carried": bool(it.get("carried")), "place": it.get("place"),
                "hist": len(it.get("history", []))}

    def ask(thought, intention=""):
        return G.act_from_thought(thought, intention, family="net")

    def fresh_netted():
        """A fresh garden whose bed IS netted -- the flag and the netting item agree (advance() re-derives the flag from the item)."""
        st = fresh(); it = st["items"]["netting"]
        it["pos"] = [5.5, 5.5, 0.6]; it["place"] = "garden"; it["carried"] = False; st["netted"] = True
        return st

    # -- the 09-28 false fire: replayed exactly as the dispatcher made the call. J-1680 made the world answer honestly ("no
    # netting over the bed"); J-1749 goes one step earlier: the hand's agent guard DECLINES this descriptive prose at the gate,
    # so the hand answers nothing at all and writes nothing -- on a bare bed AND on a netted one.
    for label, thought in (("09-28 thought (full text)", THOUGHT_0928), ("09-28 thought (the ~200 chars the hand received)", THOUGHT_0928_HAND)):
        for bed in ("bare", "netted"):
            st = fresh_netted() if bed == "netted" else fresh(); b = snap(st)
            ans = ask(thought)
            check(f"{label}, {bed} bed: the hand DECLINES -- no answer at all (neither a net nor a lift is claimed)", not ans, repr(ans))
            check(f"{label}, {bed} bed: NO ledger row is written (the false 'unnet' deed J-1680 closed, the false 'net' row it left open)", rows() == [], str(rows()))
            check(f"{label}, {bed} bed: nothing moved -- netting where it was, flag and history untouched", snap(G._load()) == b, f"{b} -> {snap(G._load())}")

    # -- the genuine path, end to end: net -> net again -> un-net -> un-net again
    st = fresh(); b = snap(st)
    ans = ask("i stretch the netting over the bed")
    a = snap(G._load())
    check("genuine net: answered exactly as ever (untangle + stretch + peg)", (ans or "").startswith("You untangle the netting"), repr(ans))
    check("genuine net: exactly one ledger row, a 'net'", rows() == [{"deed": "net"}], str(rows()))
    check("genuine net: netted flips True, the netting goes over the bed, history +1, no longer carried",
          a["netted"] is True and a["pos"] == [5.5, 5.5, 0.6] and a["hist"] == b["hist"] + 1 and a["carried"] is False, f"{b} -> {a}")
    check("genuine net: the history row names the deed", G._load()["items"]["netting"]["history"][-1]["event"] == "stretched_over_the_bed_by_du")

    n1, a1 = rows(), snap(G._load())
    ans = ask("i stretch the netting over the bed")
    check("net on an already-netted bed: an honest no-op line", "already stretched over the bed" in (ans or "").lower(), repr(ans))
    check("net on an already-netted bed: NO new ledger row", rows() == n1, f"{n1} -> {rows()}")
    check("net on an already-netted bed: nothing moved (no second history row)", snap(G._load()) == a1, f"{a1} -> {snap(G._load())}")

    ans = ask("i lift the netting off the bed")
    a3 = snap(G._load())
    check("genuine un-net while netted: answered exactly as ever", ans == "You lift the netting off the bed, roll it, and lean it against the wall.", repr(ans))
    check("genuine un-net: the ledger gains exactly one 'unnet' row after the 'net' row", rows() == [{"deed": "net"}, {"deed": "unnet"}], str(rows()))
    check("genuine un-net: netted flips False and the netting returns to its rest position",
          a3["netted"] is False and a3["pos"] == [7.2, 1.5, 0.0], str(a3))

    n3 = rows()
    ans = ask("i lift the netting off the bed")
    check("un-net on a bare bed: an honest line that names where the roll really is (by the wall)",
          "no netting over the bed" in (ans or "").lower() and "by the wall" in (ans or "").lower(), repr(ans))
    check("un-net on a bare bed: NO new ledger row, nothing moved", rows() == n3 and snap(G._load()) == a3, f"{n3} -> {rows()}")

    # -- the netting in his hands
    st = fresh(); st["items"]["netting"]["carried"] = True; b = snap(st)
    ans = ask("i lift the netting off the bed")
    check("un-net while carrying the roll: honest line, says it is in his hands", "no netting over the bed" in (ans or "").lower() and "in your hands" in (ans or "").lower(), repr(ans))
    check("un-net while carrying the roll: no ledger row, still carried, nothing else moved", rows() == [] and snap(G._load()) == b, f"{b} -> {snap(G._load())}")
    st = fresh(); st["items"]["netting"]["carried"] = True; st["netted"] = True; b = snap(st)      # the flag is stale until the next world tick
    ans = ask("i lift the netting off the bed")
    check("un-net with a STALE netted flag while he holds the roll: still honest, no row, nothing moved",
          "no netting over the bed" in (ans or "").lower() and rows() == [] and snap(G._load()) == b, f"{ans!r} {rows()}")
    st = fresh(); st["items"]["netting"]["carried"] = True; b = snap(st)
    ans = ask("i stretch the netting over the bed")
    a = snap(G._load())
    check("genuine net while carrying the roll: works exactly as ever (put down over the bed, one 'net' row)",
          (ans or "").startswith("You untangle the netting") and rows() == [{"deed": "net"}] and a["netted"] is True and a["carried"] is False and a["pos"] == [5.5, 5.5, 0.6], f"{ans!r} {a}")

    # -- the substring / clause-local misreads that used to flip a net will into an un-net
    st = fresh()
    ans = ask("i stretch the netting over the bed, then make a coffee")
    check("'coffee' no longer flips a net will into an un-net: it nets (one 'net' row)", (ans or "").startswith("You untangle the netting") and rows() == [{"deed": "net"}], f"{ans!r} {rows()}")
    st = fresh()
    ans = ask("the cold eases off me. i stretch the netting over the bed.")
    check("an 'off' in a DIFFERENT sentence no longer flips it: it nets (one 'net' row)", (ans or "").startswith("You untangle the netting") and rows() == [{"deed": "net"}], f"{ans!r} {rows()}")

    # -- unchanged refusal: the netting is somewhere else entirely
    st = fresh(); st["items"]["netting"]["place"] = "wood"; st["items"]["netting"]["carried"] = False
    ans = ask("i lift the netting off the bed")
    check("the netting is not here: the old refusal, no row", ans == "The netting is not here." and rows() == [], f"{ans!r} {rows()}")

    # -- J-1749 / F-2378 acceptance table, driven end to end through act_from_thought(thought, "", family="net")
    for s in GENUINE_NET:
        st = fresh(); b = snap(st)
        ans = ask(s); a = snap(G._load())
        check(f"genuine net, bare bed: {s!r} -> the stretch answer, ONE 'net' row, bed netted",
              (ans or "").startswith("You untangle the netting") and rows() == [{"deed": "net"}] and a["netted"] is True
              and a["pos"] == [5.5, 5.5, 0.6] and a["hist"] == b["hist"] + 1, f"{ans!r} {rows()} {b} -> {a}")
    for s in GENUINE_UNNET:
        st = fresh_netted(); b = snap(st)
        ans = ask(s); a = snap(G._load())
        check(f"genuine un-net, netted bed: {s!r} -> the lift answer, ONE 'unnet' row, netting back by the wall",
              ans == "You lift the netting off the bed, roll it, and lean it against the wall." and rows() == [{"deed": "unnet"}]
              and a["netted"] is False and a["pos"] == [7.2, 1.5, 0.0], f"{ans!r} {rows()} {b} -> {a}")
        st = fresh(); b = snap(st)
        ans = ask(s)
        check(f"genuine un-net, bare bed: {s!r} -> reaches the hand and gets J-1680's honest no-netting line, no row, nothing moved",
              "no netting over the bed" in (ans or "").lower() and rows() == [] and snap(G._load()) == b, f"{ans!r} {rows()}")
    for s in PROSE:
        for bed in ("bare", "netted"):
            st = fresh_netted() if bed == "netted" else fresh(); b = snap(st)
            ans = ask(s)
            check(f"prose, {bed} bed: {s[:64]!r} -> declined (no answer), ZERO ledger rows, nothing moved",
                  not ans and rows() == [] and snap(G._load()) == b, f"{ans!r} {rows()} {b} -> {snap(G._load())}")

    # -- J-1772 / D-0344 acceptance, driven end to end through act_from_thought(thought, "", family="net"): the two genuine
    # 2026-09-02 wills reach the hand and take the NET direction; the four false reads (and the 09-28 prose) write nothing.
    for s in GENUINE_0902:
        st = fresh(); b = snap(st)
        ans = ask(s); a = snap(G._load())
        check(f"D-0344 genuine 09-02, bare bed: {s[:60]!r} -> the net answer, ONE 'net' row, bed netted (never the un-net line)",
              (ans or "").startswith("You untangle the netting") and rows() == [{"deed": "net"}] and a["netted"] is True
              and a["pos"] == [5.5, 5.5, 0.6] and a["hist"] == b["hist"] + 1, f"{ans!r} {rows()} {b} -> {a}")
        st = fresh_netted(); b = snap(st)
        ans = ask(s)
        check(f"D-0344 genuine 09-02, netted bed: {s[:60]!r} -> NET direction answers honestly ('already stretched'), NO row, nothing moved",
              "already stretched over the bed" in (ans or "").lower() and rows() == [] and snap(G._load()) == b, f"{ans!r} {rows()}")
    for s, want in MORE_GENUINE_D0344:
        if want == "net":
            st = fresh(); b = snap(st)
            ans = ask(s); a = snap(G._load())
            check(f"D-0344 ordinary net will, bare bed: {s!r} -> ONE 'net' row, bed netted",
                  (ans or "").startswith("You untangle the netting") and rows() == [{"deed": "net"}] and a["netted"] is True, f"{ans!r} {rows()}")
        else:
            st = fresh_netted(); b = snap(st)
            ans = ask(s); a = snap(G._load())
            check(f"D-0344 ordinary un-net will, netted bed: {s!r} -> ONE 'unnet' row, netting back by the wall",
                  ans == "You lift the netting off the bed, roll it, and lean it against the wall." and rows() == [{"deed": "unnet"}] and a["netted"] is False, f"{ans!r} {rows()}")
    for s, why in FALSE_0902:
        for bed in ("bare", "netted"):
            st = fresh_netted() if bed == "netted" else fresh(); b = snap(st)
            ans = ask(s)
            check(f"D-0344 false read [{why}], {bed} bed: {s[:64]!r} -> declined (no answer), ZERO ledger rows, nothing moved",
                  not ans and rows() == [] and snap(G._load()) == b, f"{ans!r} {rows()} {b} -> {snap(G._load())}")
except Exception as exc:
    import traceback; traceback.print_exc()
    check("part 2 ran", False, repr(exc))
finally:
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
