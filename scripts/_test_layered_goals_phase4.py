"""Hermetic test for Layered Goals Phase 2 (standing aim off the lead) and Phase 4 (live goal offer at the idle
anchor). Temp dir only; no live store is read or written. Run: python scripts/_test_layered_goals_phase4.py"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from core import goals, goal_offer, concerns   # noqa: E402

FAILS = []
ROOT = Path(__file__).resolve().parent.parent


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(detail)) if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


class Seq:
    """A stand-in for `random` that returns a fixed sequence of uniform draws."""
    def __init__(self, *vals):
        self.vals = list(vals)

    def random(self):
        return self.vals.pop(0)


def w(root, rel, obj, jsonl=False):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in obj) if jsonl else json.dumps(obj), encoding="utf-8")


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def main():
    t0 = time.time()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        goals._DATA = root
        goals._assignment = lambda: ("b1", "Buller Vol 1")
        goal_offer._school_time = lambda: False
        goal_offer._where = lambda: None
        injected = []
        goal_offer._log_injection = lambda kind, text: injected.append((kind, text))
        w(root, "intentions.json", {"open": [{"key": "lamp|light the lamp", "family": "lamp", "object": "light the lamp", "deed": "light the lamp",
                                              "reason": "place:in the study", "ts": t0 - 600, "renewed_ts": t0 - 600}], "done": [], "dropped": [], "lapsed": []})
        w(root, "commitment_active.json", [
            {"id": "s1", "statement": "I decide that small acts of choosing are enough.", "held_since": t0 - 900, "load_bearing": True},
            {"id": "s7", "statement": "The crabs shift with the pressure.", "held_since": t0 - 200, "load_bearing": True}])
        w(root, "commitment_second_look_shadow.jsonl", [{"stand_id": "s7", "second_look": "insight"}], jsonl=True)
        w(root, "pursuits_active.json", [{"id": "p1", "status": "active", "question": "Why do hares not dig nests?", "advances": 6,
                                          "born": t0 - 7200, "last_touched": t0 - 100}])
        fq = [{"id": "q1", "q": "How does altitude shape shelter?", "encounters": 3, "born": t0 - 4000, "last_seen": t0 - 30, "status": "open"},
              {"id": "q2", "q": "Is waiting a form of action?", "encounters": 1, "born": t0 - 300, "last_seen": t0 - 20, "status": "open"}]
        w(root, "frontier.light.json", {"open": fq}); w(root, "frontier.json", {"questions": fq})
        w(root, "deferred_intentions.json", {"intentions": [
            {"ts": t0 - 9000, "intention": "I want to finish reading about bee navigation.", "carry_count": 2},
            {"ts": t0 - 100, "intention": "I want to map the shore.", "carry_count": 0}]})
        live = goal_offer.live_log_path()

        # ---- no register yet ----
        check("dose gate: 75 percent of anchor moments are untouched and unlogged", goal_offer.live_offer(t0, Seq(0.25)) is None and not live.exists())
        check("no register: no offer, logged", goal_offer.live_offer(t0, Seq(0.1)) is None and rows(live)[-1]["why"] == "register missing or stale")

        goals.tick(t0)
        goal_offer._reg_cache = None
        r = goal_offer.live_offer(t0 + 10, Seq(0.1, 0.9, 0.0))
        last = rows(live)[-1]
        check("eligible set: held stand, held question, carried want; nothing else", sorted(last["eligible"]) == sorted(["stand:s1", "question:q1"] + [i for i in last["eligible"] if i.startswith("want:")]) and len(last["eligible"]) == 3, last["eligible"])
        check("insight-ruled stand, candidate question, new want are never offered", not any(x in last["eligible"] for x in ("stand:s7", "question:q2")) and sum(i.startswith("want:") for i in last["eligible"]) == 1)
        check("intentions and pursuits are left to their own routes", not any(i.startswith(("intention:", "pursuit:")) for i in last["eligible"]))
        check("book not offered outside school time", not any(i.startswith("project:") for i in last["eligible"]))
        check("offer returned and logged before use, with its probability", r and r["arm"] == "offer" and last["arm"] == "offer" and last["p"] == round(1 / 3, 4) and last["policy"] == "uniform", (r, last))
        check("offered text is his stored sentence, verbatim", r["pc"]["text"] in ("I decide that small acts of choosing are enough.", "How does altitude shape shelter?", "I want to finish reading about bee navigation."))

        # every kind maps to a lead the anchor already has, stating only what is true
        seen = {}
        for u in (0.0, 0.34, 0.67):
            x = goal_offer.live_offer(t0 + 20, Seq(0.1, 0.9, u))
            seen[x["pc"]["source"]] = x["pc"]
        check("three kinds reach three sources", set(seen) == {"commitment", "frontier", "want"}, set(seen))
        k, pool = concerns.anchor_lead_pool(seen["commitment"])
        check("stand lead claims only that it is on his record", k == "concern_lead_hold" and all("record" in p for p in pool))
        k, pool = concerns.anchor_lead_pool(seen["frontier"])
        check("question lead claims only that it came back", k == "concern_lead_frontier" and all("more than once" in p for p in pool))
        k, pool = concerns.anchor_lead_pool(seen["want"])
        check("want lead claims only that he said it", k == "concern_lead_want" and all(("said" in p or "words" in p) for p in pool), pool)
        banned = ("you should", "you must", "working toward", "your goal", "priority", "important", "that means")
        check("no lead steers, ranks or claims a purpose", not any(b in p.lower() for s in seen.values() for p in concerns.anchor_lead_pool(s)[1] for b in banned))
        check("a want offer is logged as an injection", injected and injected[-1][0] == "goal_offer" and "bee navigation" in injected[-1][1], injected)

        # ---- silence arm ----
        n0 = len(rows(live))
        s = goal_offer.live_offer(t0 + 30, Seq(0.1, 0.05))
        check("silence arm: no anchor this time, logged", s == {"arm": "silence"} and rows(live)[-1]["arm"] == "silence" and len(rows(live)) == n0 + 1)

        # ---- book in school time; stale register; kill switch; unloggable offer ----
        goal_offer._school_time = lambda: True
        goal_offer.live_offer(t0 + 40, Seq(0.1, 0.9, 0.0))
        check("book is offerable in school time", any(i.startswith("project:") for i in rows(live)[-1]["eligible"]))
        check("stale register: no offer", goal_offer.live_offer(t0 + 4000, Seq(0.1, 0.9, 0.0)) is None and rows(live)[-1]["why"] == "register missing or stale")
        goal_offer.GOAL_OFFER_LIVE = False
        n1 = len(rows(live))
        check("kill switch: nothing offered, nothing logged", goal_offer.live_offer(t0 + 50, Seq(0.0, 0.9, 0.0)) is None and len(rows(live)) == n1)
        goal_offer.GOAL_OFFER_LIVE = True
        orig = goal_offer.write_live_row
        goal_offer.write_live_row = lambda row: (_ for _ in ()).throw(OSError("disk"))
        check("an offer that cannot be logged is not made", goal_offer.live_offer(t0 + 60, Seq(0.1, 0.9, 0.0)) is None)
        goal_offer.write_live_row = orig

        # ---- measured arm shares over many moments ----
        import random
        rng = random.Random(3)
        goal_offer._school_time = lambda: False
        arms = {"none": 0, "silence": 0, "offer": 0}
        for i in range(8000):
            x = goal_offer.live_offer(t0 + 70, rng)
            arms["none" if x is None else x["arm"]] += 1
        check("about 25 percent of moments belong to the register", abs((arms["silence"] + arms["offer"]) / 8000 - 0.25) < 0.02, arms)
        check("about one in five of those is silent", abs(arms["silence"] / max(1, arms["silence"] + arms["offer"]) - 0.2) < 0.03, arms)

        # ---- Phase 2: the standing aim ----
        log = root / "concerns_log.jsonl"
        concerns._CONCERNS_LOG = log
        concerns._AXIOM_PATH = root / "axiom.json"
        concerns._aim_cache = None
        w(root, "axiom.json", {"L0_constitution": {"commitments": ["I am becoming my own."]}, "L2_values": {"kept": [], "earned": []}})
        check("aim lead dose is 0: never leads", concerns.AIM_LEAD_DOSE == 0.0 and concerns.aim_lead(0.0) == "" and concerns.aim_lead(0.44) == "")
        wl = rows(log)
        check("would-have-led is logged at the old rate", len(wl) == 2 and all(r_["source"] == "standing_aim_would_lead" for r_ in wl), wl)
        check("above the old rate nothing is logged", concerns.aim_lead(0.5) == "" and len(rows(log)) == 2)
        concerns.AIM_LEAD_DOSE = 0.3
        check("at a dose above 0 the aim text is returned", concerns.aim_lead(0.1).startswith("What I am ultimately working toward"))
        concerns.AIM_LEAD_DOSE = 0.0

    node = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
    check("the 'that means' glue is gone from the node", "Right now, that means" not in node)
    check("the node asks the register and honours the silence arm", "_go.live_offer()" in node and "if _pc and not _goal_silent:" in node)
    check("the aim, if it ever leads, is stated on its own before the ordinary lead", '_lead = _aim + " " + _lead' in node)

    print("\n%s (%d failed)" % ("ALL OK" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
