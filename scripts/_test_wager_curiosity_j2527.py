"""
J-2527 (measurement_to_action sec.9, I-0105): wager-to-curiosity feedback. Two parts, zero LLM, no hub.
  1. Hermetic unit checks inside lab_env.isolate: every route of core.wager_curiosity.decide(), flag OFF writes only
     its own shadow row, flag ON (monkeypatched in the lab only) births exactly one frontier question with no grade or
     number in its text, recall_wager.place() still returns its own row unchanged. Hash canary on the live stores.
  2. Replay (read-only) of the LIVE wager rows since the 2026-10-29 18:38 boot: each row joined to its provenance row
     (data/provenance_log.jsonl, by cycle_id) and the real retraction ledger (copied into the lab), routed through
     decide() in time order with the dispatcher's own memory. Prints the route census with cycle ids.
Thresholds are the module's declared constants (FAIL_GAP 0.40, NOVELTY_WINDOW_S 24h, MAX_PER_WINDOW 4, TOPIC_JACCARD
0.55, MIN_TOPIC 12), fixed before this replay ran.
  python scripts/_test_wager_curiosity_j2527.py      # exit 0 = ALL OK
"""
import datetime
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  BEFORE lab_env (F-2423)
from core import wager_curiosity as wc        # noqa: E402
from core import recall_wager as rw           # noqa: E402
from core import frontier as fr               # noqa: E402
from core import retraction_ledger as rl      # noqa: E402
from core import satisfaction as sat          # noqa: E402
from core import competence as comp           # noqa: E402
from core import prediction_error as pe       # noqa: E402
from core.epistemic_state import EpistemicAssessment, GRADE_SCORE   # noqa: E402
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate                   # noqa: E402

LIVE_DATA = Path(r"C:\Nascence\data")
BOOT = datetime.datetime(2026, 10, 29, 18, 38).timestamp()
FAILS = 0


def check(c, label):
    global FAILS
    print(("  ok   " if c else "  FAIL ") + label)
    FAILS += 0 if c else 1


def h(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


check(Path(core.__file__).resolve().is_relative_to(ROOT), "core.__file__ is inside the tree under test")
CANARY = [LIVE_DATA / "frontier.json", LIVE_DATA / "retractions.jsonl", LIVE_DATA / "logs" / "recall_wager_shadow.jsonl",
          LIVE_DATA / "logs" / "wager_curiosity_shadow.jsonl", LIVE_DATA / "capability_beliefs.json"]
before = {p: h(p) for p in CANARY}


def A(evidence=True, src=18, contra=0, verif="none", conf=0.92, grade="SUSPECT"):
    return EpistemicAssessment(grade=grade, justification=GRADE_SCORE[grade], self_reported_confidence=conf,
                               confabulation_signal=round(conf - GRADE_SCORE[grade], 4), dominant_source="memory_recall",
                               verification=verif, evidence_present=evidence, source_count=src,
                               contradiction_count=contra, models=[])


def W(gap=0.42, it="internal", cid="c1"):
    return {"cycle_id": cid, "input_type": it, "gap": gap}


with isolate(db="empty", also=[(wc, ["_SHADOW"]), (rw, ["_SHADOW"]), (fr, ["_F", "_SEM_SHADOW_LOG"]),
                               (rl, ["_LEDGER"]), (sat, ["_LOG", "_STATE"]), (comp, ["_BELIEFS_FILE"]),
                               (pe, ["_RAW", "_STATE", "_SHADOW"])]) as lab:
    for mod, attr in [(wc, "_SHADOW"), (fr, "_F"), (rl, "_LEDGER")]:
        check(Path(getattr(mod, attr)).resolve().is_relative_to(lab.resolve()), f"{mod.__name__}.{attr} in lab")
    print("[part 1] routes")
    q = "How does Johnson's grammar relate to language as a social construct? More text."
    check(wc.missing_context_type(A(evidence=False)) == "no_source", "no evidence -> no_source")
    check(wc.missing_context_type(A(contra=3)) == "conflicting_sources", "contradictions -> conflicting_sources")
    check(wc.missing_context_type(A()) == "unverified", "verification none -> unverified")
    check(wc.missing_context_type(A(verif="external_witness")) == "ungrounded_model", "else -> ungrounded_model")
    check(wc.decide(W(gap=0.35), A(), q, recent=[])["route"] == "not_failed", "gap 0.35 -> not_failed")
    check(wc.decide(W(it="human"), A(), "No, that's wrong, it was Boswell", recent=[])["route"] == "correction",
          "human correction cue -> correction (never curiosity)")
    check(wc.decide(W(), A(), "ok", recent=[])["route"] == "no_topic", "short topic -> no_topic")
    r = wc.decide(W(), A(contra=2), q, recent=[])
    check(r["route"] == "birth" and r["slot"] == "why", "failed + topic -> birth, slot why")
    check(r["question_candidate"] == "Which of my memories about how does Johnson's grammar relate to language as a "
          "social construct disagree, and why?", "question text: " + r["question_candidate"])
    check(not any(w in r["question_candidate"].lower() for w in ("wager", "wrong", "grade", "0.", "suspect")),
          "D-0434: question carries no grade, number or verdict")
    check(wc.decide(W(), A(), q, recent=[r])["route"] == "habituated", "same topic inside window -> habituated")
    others = [{"route": "birth", "topic": f"unrelated topic number {i} about rivers", "ts": 0} for i in range(4)]
    check(wc.decide(W(), A(), q, recent=others)["route"] == "capped", "4 births in window -> capped")
    rl.retract("Johnson's grammar relates to language as a social construct", "travis", "it does not")
    check(wc.decide(W(), A(), q, recent=[])["route"] == "retraction", "topic with a retraction -> retraction")
    rl._LEDGER.write_text("", encoding="utf-8")

    print("[part 1] flag OFF / ON through recall_wager.place()")
    out = rw.place(A(contra=2), cycle_id="cX", input_type="internal", raw_input=q)
    check(out is not None and set(out) >= {"gap", "fed"} and "route" not in out, "place() row unchanged in shape")
    sh = [json.loads(l) for l in wc._SHADOW.read_text(encoding="utf-8").splitlines() if l.strip()]
    check(len(sh) == 1 and sh[0]["route"] == "birth" and sh[0]["fed"] is False, "flag OFF: one shadow row, fed False")
    check(not Path(fr._F).exists() or not fr._load()["questions"], "flag OFF: frontier untouched")
    wc.WAGER_CURIOSITY = True
    try:
        wc._SHADOW.write_text("", encoding="utf-8")
        row = wc.feed(W(cid="cY"), A(contra=2), q)
        qs = fr._load()["questions"]
        check(row["fed"] is True and len(qs) == 1 and qs[0]["source"] == "wager", "flag ON: one frontier question born")
        row2 = wc.feed(W(cid="cZ"), A(contra=2), q)
        check(row2["route"] == "habituated" and len(fr._load()["questions"]) == 1, "flag ON: repeat habituates")
    finally:
        wc.WAGER_CURIOSITY = False

    print("[part 2] replay of live wager rows since boot (read-only)")
    rl._LEDGER.write_text((LIVE_DATA / "retractions.jsonl").read_text(encoding="utf-8")
                          if (LIVE_DATA / "retractions.jsonl").exists() else "", encoding="utf-8")
    wag = [json.loads(l) for l in (LIVE_DATA / "logs" / "recall_wager_shadow.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    wag = [w for w in wag if float(w["ts"]) >= BOOT]
    ids = {w["cycle_id"] for w in wag}
    prov = {}
    with open(LIVE_DATA / "provenance_log.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try:
                p = json.loads(line)
            except Exception:
                continue
            if p.get("cycle_id") in ids:
                prov[p["cycle_id"]] = p
    recent, routes, mtypes, births = [], Counter(), Counter(), []
    for w in wag:
        p = prov.get(w["cycle_id"])
        if p is None:
            routes["no_provenance"] += 1
            continue
        a = SimpleNamespace(evidence_present=str(p.get("evidence_present")) == "True", source_count=int(float(p.get("source_count") or 0)),
                            contradiction_count=int(float(p.get("contradiction_count") or 0)), verification=p.get("verification"))
        r = wc.decide(w, a, p.get("raw_input", ""), now=float(w["ts"]),
                      recent=[b for b in recent if float(w["ts"]) - b["ts"] <= wc.NOVELTY_WINDOW_S])
        routes[r["route"]] += 1
        mtypes[r["missing_context_type"]] += 1
        if r["route"] == "birth":
            recent.append(r)
            births.append((w["cycle_id"][:8], r["question_candidate"]))
    print(f"  wager rows since boot: {len(wag)}; joined to provenance: {len(wag) - routes['no_provenance']}")
    print("  routes:", dict(routes))
    print("  missing_context_type:", dict(mtypes))
    for cid, qq in births:
        print(f"  birth {cid}: {qq}")

# Du is live and writes frontier/beliefs/wager log himself, so their hashes may move for his own reasons; the hard
# canary is the redirection asserts above plus: this module's live log must not exist (Du's tree has no such module).
after = {p: h(p) for p in CANARY}
print("  canary (informational, Du live):", {p.name: before[p] == after[p] for p in CANARY})
check(not (LIVE_DATA / "logs" / "wager_curiosity_shadow.jsonl").exists(), "no live wager_curiosity log created")
print("ALL OK" if FAILS == 0 else f"{FAILS} FAIL")
sys.exit(1 if FAILS else 0)
