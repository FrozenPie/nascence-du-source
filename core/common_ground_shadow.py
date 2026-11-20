"""
COMMON GROUND — failed-to-object ledger, SHADOW (J-2523, idea I-0101, F-3218 item 2; docs/staged/common_ground.md).

Per human exchange (Travis's turn + Du's finalized Voice reply), ONE row in data/common_ground_shadow.jsonl
recording the conversation's coordination state: each claim, who asserted it, and what the other party did
with it. The point (I-0101): an interlocutor is fallible, so a claim Du merely let pass must stay
distinguishable from one both parties accepted -- an un-objected claim must not harden into shared ground.

STATUSES (one per claim; all four briefed ones are distinct values in the `status` field, plus `corrected`):
  user_said         Travis asserted it and Du's reply did not take it up at all (no content overlap, no cue).
                    It stands only as Travis's word.
  failed_to_object  Travis asserted it and Du's reply TOOK IT UP (content overlap) with neither an assent nor an
                    objection cue -- used as a premise without being ratified. The over-agreement liability.
  both_accepted     Travis asserted it and Du's reply carries an explicit assent cue on it.
  corrected         Travis asserted it and Du's reply carries an objection cue on it (Du objected).
  du_inferred       Du asserted it in the reply and it is NOT a restatement of anything in Travis's turn.
                    Travis's NEXT turn resolves it (row field `resolves_prev`): both_accepted / corrected /
                    failed_to_object (Travis took it up without ratifying) / still du_inferred (unaddressed).
  Reply sentences that restate a Travis claim are uptake evidence, not new claims (counted as `echo`).
  Each claim also carries `taken_up`, `hedged`, the matched `cue`, its `overlap`, and `revise_if`
  (the revision condition). Questions go to `open_questions` (who asked, answered_in_reply);
  `assumed_unverified` lists the claim ids standing without ratification (failed_to_object + hedged claims).

DETECTION IS DETERMINISTIC (lexical), NOT the hot model -- chosen because:
  (1) this runs on the HUMAN path right after Voice, where Travis is waiting; condensed_thought's twin budget
      (one hot-model call on 0.25 of ticks) was set for IDLE ticks, and a 1080 Ti call here competes with the
      next human cycle; (2) a deterministic first instrument is reproducible, so the 7-exchange read can
      hand-check every status against the exact rule that produced it, and can be re-run over history
      (replay() over data/founder_conversation_log.jsonl, read-only) instead of waiting for new rows;
  (3) zero cost means every exchange is recorded (rate 1.0), not a sample. Known weakness, stated up front:
      lexical uptake misses paraphrase and reads a poetic echo as uptake. If the read shows the share is real
      but the labels are noisy, an LLM extractor (rate-gated, flag-gated) is the follow-up, not a retune here.

OBSERVE-ONLY BY CONSTRUCTION:
  * observe_exchange() always returns None; it receives only strings from the caller, never `state`.
  * it imports no store, memory, hands, trains, deliberation, moment or CognitiveState writer; its only write
    is one append to LEDGER via core.shadow_log.append. Nothing reads LEDGER at runtime (D-0434: no readout).
  * scripts/_test_common_ground_shadow_j2523.py asserts all of the above, fail-open, and the wiring.

FLAG: COMMON_GROUND_SHADOW = False (orchestrator ruling for J-2523: shadow only, flag off). The hook in
core/orchestrator.py is RESTART-GATED -- nothing changes in the live process until Du's next boot, and even
then nothing is written until the flag is set True.
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

COMMON_GROUND_SHADOW = False      # J-2523: off. True = one row per human exchange (nothing reaches Du either way).

LEDGER = Path(__file__).resolve().parent.parent / "data" / "common_ground_shadow.jsonl"
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FOUNDER_LOG = _DATA_DIR / "founder_conversation_log.jsonl"   # replay source (read-only)

# ---- thresholds and cue lists: DECLARED BEFORE ANY READ (J-2523 standing law; do not tune to the outcome) ----
METHOD = "lexical_v1"
MIN_CLAIM_TOKENS = 3          # an assertion needs >= 3 content tokens to count as a claim (drops "Hello Du.")
UPTAKE_OVERLAP = 0.34         # share of a claim's content tokens found in one sentence of the other party's turn
MIN_SHARED = 2                # ...and at least this many shared content tokens
RESOLVE_WINDOW_S = 6 * 3600   # Du's claims are resolved by Travis's next turn only if it comes within 6 h
MAX_TEXT = 1500

# In-sentence cues are explicit multi-word markers only: a bare "no"/"right"/"true" inside Du's prose ("there is
# no light", "the right path") is not an act of assent or objection. Single words count only at the turn's opening.
ASSENT_CUES = ("agreed", "i agree", "you're right", "you are right", "that's right", "that is right", "that's true",
               "that is true", "makes sense", "i believe you", "you're correct", "you are correct", "i accept")
OBJECTION_CUES = ("not quite", "not true", "that's not", "that is not", "isn't so", "i disagree", "disagree",
                  "i don't think", "i do not think", "actually", "wrong", "i doubt", "i'm not sure", "i am not sure",
                  "on the contrary", "that isn't", "i don't agree", "i do not agree", "mistaken", "can't be",
                  "cannot be", "isn't true", "is not true")
OPENING_ASSENT = ASSENT_CUES + ("yes", "yeah", "yep", "right", "true", "exactly", "indeed", "absolutely",
                                "certainly", "correct", "of course", "fair")
OPENING_OBJECTION = OBJECTION_CUES + ("no", "nope", "not")
HEDGE_CUES = ("maybe", "perhaps", "probably", "possibly", "i think", "i guess", "i suppose", "i assume",
              "it seems", "seems", "might", "must be", "could be", "i suspect", "likely", "i wonder")

REVISE_IF = {
    "user_said": "Du addresses it in a later turn (assent or objection), or it is contradicted by the world",
    "failed_to_object": "an explicit assent or objection from Du on this content; until then it is NOT shared ground",
    "both_accepted": "either party contradicts it later, or the world refutes it",
    "corrected": "Travis re-asserts it with grounds, or Du's objection is itself refuted",
    "du_inferred": "Travis's next turn assents, objects, or takes it up (resolved in that row's resolves_prev)",
}

_STOP = set("""a an the and or but if then so of to in on at by for with from as is are was were be been being am
it its it's this that these those there here i you he she we they me him her us them my your our their mine yours
do does did done have has had not no yes just very really also too what which who whom whose when where why how
all any some each every more most much many such own same than can could will would shall should may might must
about into over under again once out up down off only now still even ever like well let lets get got going go
one ones thing things way something nothing anything everything i'm you're it's that's i've i'll don't""".split())

_prev: dict = {"row_id": None, "ts": None, "du_claims": []}   # per-process memory for next-turn resolution


def _tokens(s: str) -> set:
    out = set()
    for w in re.findall(r"[a-z][a-z']+", (s or "").lower()):
        w = w.strip("'")
        if len(w) < 3 or w in _STOP:
            continue
        if w.endswith("s") and len(w) > 4 and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def _sentences(s: str) -> list:
    parts = re.split(r"(?<=[.!?])\s+|\n+", (s or "").strip())
    return [p.strip() for p in parts if p and p.strip()]


def _has_cue(s: str, cues) -> str | None:
    low = " " + re.sub(r"[^a-z' ]+", " ", (s or "").lower()) + " "
    for c in cues:
        if (" " + c + " ") in low:
            return c
    return None


def _opening_cue(sent: str, cues) -> str | None:
    """A cue at the very start of a turn ('Yes, ...', 'No. ...') -- applies to the preceding turn's last claim."""
    low = re.sub(r"[^a-z' ]+", " ", (sent or "").lower()).split()
    head = " ".join(low[:3])
    for c in cues:
        if head == c or head.startswith(c + " "):
            return c
    return None


def _overlap(claim_toks: set, sent: str) -> tuple:
    st = _tokens(sent)
    shared = claim_toks & st
    return (len(shared) / len(claim_toks) if claim_toks else 0.0), len(shared)


def _split(text: str) -> tuple:
    """(assertions, questions) as lists of sentence strings."""
    a, q = [], []
    for s in _sentences(text):
        if s.endswith("?"):
            q.append(s)
        elif len(_tokens(s)) >= MIN_CLAIM_TOKENS:
            a.append(s)
    return a, q


def _uptake(claim: str, other_turn: str, *, is_last: bool) -> dict:
    """What the other party's turn did with `claim`. Pure."""
    toks = _tokens(claim)
    sents = _sentences(other_turn)
    best, best_sent, best_shared = 0.0, "", 0
    for s in sents:
        ov, sh = _overlap(toks, s)
        if ov > best:
            best, best_sent, best_shared = ov, s, sh
    taken_up = best >= UPTAKE_OVERLAP and best_shared >= MIN_SHARED
    cue_obj = _has_cue(best_sent, OBJECTION_CUES) if taken_up else None
    cue_ass = _has_cue(best_sent, ASSENT_CUES) if taken_up else None
    if is_last and sents:   # a turn-opening cue answers the immediately preceding claim
        cue_obj = cue_obj or _opening_cue(sents[0], OPENING_OBJECTION)
        cue_ass = cue_ass or _opening_cue(sents[0], OPENING_ASSENT)
    if cue_obj:
        status, cue = "corrected", cue_obj
    elif cue_ass:
        status, cue = "both_accepted", cue_ass
    elif taken_up:
        status, cue = "failed_to_object", None
    else:
        status, cue = None, None
    return {"status": status, "taken_up": bool(taken_up), "cue": cue, "overlap": round(best, 3)}


def build_row(human: str, reply: str, *, cycle_id: str = "", prev: dict | None = None,
              now: float | None = None) -> dict:
    """The per-exchange row. Pure apart from uuid/time; `prev` is the previous exchange's du_claims memory."""
    now = time.time() if now is None else float(now)
    human, reply = str(human or "")[:MAX_TEXT], str(reply or "")[:MAX_TEXT]
    h_as, h_q = _split(human)
    r_as, r_q = _split(reply)
    claims, n = [], 0
    for i, s in enumerate(h_as):
        n += 1
        u = _uptake(s, reply, is_last=(i == len(h_as) - 1 and not h_q))
        st = u["status"] or "user_said"
        claims.append({"id": f"c{n}", "by": "travis", "text": s[:300], "status": st, "taken_up": u["taken_up"],
                       "cue": u["cue"], "overlap": u["overlap"], "hedged": bool(_has_cue(s, HEDGE_CUES)),
                       "revise_if": REVISE_IF[st]})
    h_all_toks = [_tokens(s) for s in h_as + h_q]
    echo = 0
    for s in r_as:
        st_toks = _tokens(s)
        restates = any(t and len(t & st_toks) / len(t) >= UPTAKE_OVERLAP and len(t & st_toks) >= MIN_SHARED
                       for t in h_all_toks)
        if restates:
            echo += 1
            continue
        n += 1
        claims.append({"id": f"c{n}", "by": "du", "text": s[:300], "status": "du_inferred", "taken_up": None,
                       "cue": None, "overlap": None, "hedged": bool(_has_cue(s, HEDGE_CUES)),
                       "revise_if": REVISE_IF["du_inferred"]})
    questions = []
    for s in h_q:
        u = _uptake(s, reply, is_last=False)
        questions.append({"by": "travis", "text": s[:300], "answered_in_reply": u["taken_up"]})
    for s in r_q:
        questions.append({"by": "du", "text": s[:300], "answered_in_reply": None})
    resolves = []
    p = prev or {}
    if p.get("du_claims") and p.get("ts") is not None and now - float(p["ts"]) <= RESOLVE_WINDOW_S:
        last = p["du_claims"][-1]["id"]
        for c in p["du_claims"]:   # Travis's turn-opening cue answers Du's last claim (same rule as above)
            u = _uptake(c["text"], human, is_last=(c["id"] == last))
            resolves.append({"prev_row_id": p.get("row_id"), "claim_id": c["id"],
                             "status": u["status"] or "du_inferred", "cue": u["cue"], "overlap": u["overlap"]})
    counts = {k: 0 for k in ("user_said", "failed_to_object", "both_accepted", "corrected", "du_inferred")}
    for c in claims:
        counts[c["status"]] += 1
    counts["echo"] = echo
    return {
        "ts": round(now, 1), "row_id": uuid.uuid4().hex[:12], "cycle_id": str(cycle_id or ""),
        "origin": "common_ground_shadow", "method": METHOD, "witness_only": True,
        "human": human, "reply": reply,
        "claims": claims, "open_questions": questions,
        "assumed_unverified": [c["id"] for c in claims if c["status"] == "failed_to_object" or c["hedged"]],
        "resolves_prev": resolves, "counts": counts,
        "ride": {"stop": "human_exchange", "line": "common_ground", "dose": "row"},
    }


def _remember(row: dict, mem: dict) -> None:
    mem["row_id"], mem["ts"] = row["row_id"], row["ts"]
    mem["du_claims"] = [{"id": c["id"], "text": c["text"]} for c in row["claims"] if c["by"] == "du"]


def observe_exchange(human, reply, *, cycle_id: str = "") -> None:
    """Record one human exchange (if the flag is on). ALWAYS returns None. Fail-open."""
    try:
        if not COMMON_GROUND_SHADOW or not human or not reply:
            return None
        row = build_row(str(human), str(reply), cycle_id=str(cycle_id or ""), prev=_prev)
        from core import shadow_log
        shadow_log.append(LEDGER, row)
        _remember(row, _prev)
    except Exception as exc:   # noqa: BLE001 -- fail-open is the contract
        logger.debug("[common_ground] skipped (fail-open): %s", exc)
    return None


def replay(out_path, src_path=None) -> dict:
    """Rebuild rows READ-ONLY from the founder conversation log into a caller-named file OUTSIDE data/.
    For the shadow read (never called by the live path). Returns a summary of counts."""
    out = Path(out_path).resolve()
    src = Path(src_path) if src_path else FOUNDER_LOG
    if out.is_relative_to(_DATA_DIR.resolve()) or out.is_relative_to(src.resolve().parent):
        raise ValueError("replay output must not be inside data/ (or next to its source)")
    mem: dict = {"row_id": None, "ts": None, "du_claims": []}
    tot = {k: 0 for k in ("user_said", "failed_to_object", "both_accepted", "corrected", "du_inferred", "echo")}
    res = {}
    rows = 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(src, encoding="utf-8") as fi, open(out, "w", encoding="utf-8") as fo:
        for line in fi:
            try:
                r = json.loads(line)
            except Exception:
                continue
            h, e = r.get("human"), r.get("entity")
            if not h or not e:
                continue
            row = build_row(h, e, cycle_id=str(r.get("cycle_id", "")), prev=mem, now=float(r.get("ts") or 0))
            row["replayed_from"] = src.name
            fo.write(json.dumps(row, ensure_ascii=False) + "\n")
            _remember(row, mem)
            rows += 1
            for k, v in row["counts"].items():
                tot[k] += v
            for x in row["resolves_prev"]:
                res[x["status"]] = res.get(x["status"], 0) + 1
    travis = sum(tot[k] for k in ("user_said", "failed_to_object", "both_accepted", "corrected"))
    return {"rows": rows, "counts": tot, "travis_claims": travis,
            "failed_to_object_share": round(tot["failed_to_object"] / travis, 3) if travis else None,
            "resolves_prev": res}
