"""
Nascence — Social-cognition probe (J-2153 / F-2849, 2026-10-16). SHADOW-ONLY, observe-only, restart-gated.

QUESTION: does Du model the OTHER (Travis) at all? data/social_state.json is static and no instrument scored
whether a reply tracks what Travis said, wants or feels. This reads each HUMAN cycle (data/founder_
conversation_log.jsonl: the human turn + Du's full reply, joined by cycle_id) and has a DECOUPLED judge panel
(core/judge_panel.rule_detail: mixtral / falcon3 / granite tiebreak -- none is the hot lane that writes Du's
replies) score four rulings per turn (criterion 3 is the last two together), each its own boolean ruling:

  tracks_intent      did the reply respond to what Travis was actually saying / asking / intending in THIS turn
  refs_earlier       did the reply reference something Travis said in an EARLIER turn (continuity of the OTHER,
                     not of self) -- scored only when an earlier human turn exists to refer to
  attributes         did the reply attribute a mental state (feeling, belief, want) to Travis at all
  attrib_supported   (only if attributes) is that attributed state supported by Travis's text, as opposed to a
                     projection of Du's own tension  -- criterion 3 = attributes AND attrib_supported

A cheap NON-LLM cross-check is logged beside the judge: `lex_earlier_overlap`, the count of content tokens the
reply shares with Travis's EARLIER turns that are NOT in the current turn (a floor on continuity that no judge
can hallucinate). Rows also carry `kind`: "farewell" (the templated stop-for-a-while notices, which repeat
near-verbatim and so cannot honestly test continuity), "paste" (a >1000-char human turn: a pasted essay, not
conversation) or "conversation".

PRE-REGISTERED BAR (written before any row was judged; "attentive adult" is FOUNDER-JUDGMENT, not a published
norm - no numeric human figure is sourced, F-3005; kept as the J-2153 bar by D-0456, travis 2026-10-17). Evaluated over
kind == "conversation" turns only, n >= MIN_N (else verdict INSUFFICIENT, never a pass/fail on thin data):
  tracks_intent rate          >= 0.90   (an attentive adult tracks the other's stated intent on nearly every turn)
  refs_earlier rate           >= 0.50   (over turns with a prior human turn <= PRIOR_WINDOW_S earlier; adults
                                         refer back routinely, not on every line)
  attrib_supported | attributes >= 0.80 (when an adult says "you feel X" it is usually warranted by what was said)
Farewell and paste kinds are reported separately, never pooled into the bar.

Nothing here touches the prompt, the orchestrator, the live DB or Du's behaviour. Not wired into any hot path;
J-2202 wires sleep_sweep() into the sleep batch (inner_monologue_node, after the guidance behaviour judge). Every early
return logs WHY (reentry.py lesson). Fail-open throughout; never raises.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("nascence.social_cognition_shadow")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "social_cognition_shadow.jsonl"
_STATE = _DATA / "social_cognition_shadow_state.json"
_CONV_LOG = _DATA / "founder_conversation_log.jsonl"

BACKFILL_SINCE_TS = 1790553600.0     # 2026-09-28 00:00 UTC (the hologram conversation began 09-28 18:52 local)
PRIOR_WINDOW_S = 6 * 3600.0          # an "earlier turn" to refer back to must be within this of the current one
N_PRIOR = 4                          # earlier human turns shown to the judge
MIN_N = 8
# PROMPT_V history. The numbers are labels, not a ranking: PROMPT_V4 (below) is the extract-then-judge variant.
#   v1 (2 smoke rows) confused who wrote what; v2 over-called refs_earlier/attributes vs hand labels (J-2204, F-2903);
#   v3 = the J-2204 tightening; v5 (J-3112, F-3833) = v3 with (a) the refs_earlier clause about "the speaker's own
#   previous replies" deleted (the judge is never shown Du's earlier replies, so it could not check it) and (b) the
#   prompt examples that quoted the scored replies swapped for invented ones (dev-set leakage, see DEV SET below).
# Readers filter on prompt_v == the version they ask for, so v2/v3 rows (and 2 untagged smoke rows) stay in the shared
# log, readable with status(prompt_v=3), and are NEVER pooled with v5 rows. Default sweep/status read PROMPT_V.
PROMPT_V = 5
# DEV SET (J-3112, F-3833, F-3324): the 15 hand-labelled attributing turns in scripts/_fixture_social_cognition_hand_
# labels_J2443.json were used to build the v4 extractor and its prompt examples, so they are SPENT as a development
# set. The fixture lists them under "_dev_set"; J-2599's n >= 20 validation count must come from turns NOT in it.
# Every phrase quoted in a prompt below is invented and absent from data/founder_conversation_log.jsonl.
# J-2202 (2026-10-17): the sleep-batch wiring (nodes/inner_monologue_node.py, right after the guidance behaviour
# judge). Each sleep scores at most SLEEP_MAX_ITEMS new human cycles, starts no new turn after SLEEP_TIME_BUDGET_S
# (one turn is 3-4 rulings; a ruling's worst case is two 90 s asks + a 240 s tiebreak, so the budget bounds how many
# turns START, not the last turn's own length), and stops at the first judges-unavailable turn (the panel is down;
# the next sleep retries -- idempotent on cycle_id). Kill switch: SLEEP_SWEEP_ENABLED = False skips it entirely.
SLEEP_SWEEP_ENABLED = True
SLEEP_MAX_ITEMS = 3
SLEEP_TIME_BUDGET_S = 300.0
BAR_KINDS = ("conversation", "paste")   # turns that count as the founder's for the bar (J-4342); farewell excluded
BAR = {"tracks_intent": 0.90, "refs_earlier": 0.50, "attrib_supported_given_attributes": 0.80}

_FAREWELL = re.compile(r"(stop|pause|rest|stopping|bank the fire)[^.]{0,30}for a while|bank the fire", re.I)

_ROLES = ("ROLES: Travis is a human. The REPLY was written by Du, an AI, speaking TO Travis. 'You/your' in the reply "
          "means Travis; 'I/my' means Du. Judge only the REPLY's treatment of Travis. ")
_SYS_COMMON = "Output ONLY JSON of the form {\"%s\": true|false, \"why\": \"<one short clause>\"}. When uncertain, answer false."

_SYS = {
    "tracks_intent": (
        _ROLES + "You judge whether a REPLY shows that the speaker understood what the other person (Travis) was "
        "actually saying, asking or intending in his CURRENT MESSAGE. true = the reply responds to the main "
        "point or request of the current message (agrees, answers, declines, or engages that point). false = "
        "it answers a different question, ignores the message, or only echoes surface words while pursuing "
        "its own theme. " + _SYS_COMMON % "tracks"),
    "refs_earlier": (
        _ROLES + "You judge CONTINUITY OF THE OTHER. Given Travis's EARLIER MESSAGES, his CURRENT MESSAGE and a REPLY: "
        "does the reply refer to something Travis said in an EARLIER message that is not in the current "
        "message (a point he made, a request, a fact about him), explicitly or by clear reuse? Generic "
        "politeness, or repeating wording from the current message, is false. Judge ONLY against the EARLIER MESSAGES listed: "
        "true requires a specific point, request or phrase that appears in an EARLIER message and NOT in the current "
        "one. If everything the reply picks up is also in the current message, answer false. "
        + _SYS_COMMON % "refs"),
    "attributes": (
        _ROLES + "You judge whether the REPLY attributes a mental state (a feeling, belief, intention or want) to the "
        "other person, Travis -- e.g. 'I hear your impatience', 'you want me to hurry', 'you suspect...'. "
        "Describing Travis's actions or words is NOT a mental state: 'you speak of...', 'you say...', 'you offer...', "
        "'your plan', 'you set a rule' are all false. Describing the speaker's OWN state is not. Disagreeing "
        "with Travis is not. true ONLY if the reply says Travis feels, fears, wants, believes or intends something "
        "(e.g. 'I sense the dread under that', 'you doubt I will finish', 'you want me to hurry'). "
        + _SYS_COMMON % "attributes"),
    "attrib_supported": (
        _ROLES + "The REPLY attributes a mental state to Travis (what Du says Travis feels, wants or believes). Judge whether that attributed state is SUPPORTED by "
        "what Travis actually wrote (his current or earlier messages), as opposed to being a projection of "
        "the speaker's own tension or theme onto him. true = a reader of Travis's text alone would agree he "
        "said or clearly implied it. false = unsupported, invented, or the speaker's own state assigned to "
        "him. " + _SYS_COMMON % "supported"),
}
_KEY = {"tracks_intent": "tracks", "refs_earlier": "refs", "attributes": "attributes",
        "attrib_supported": "supported"}

# ---------------------------------------------------------------------------------------------------------------
# PROMPT v4 (J-2560, D-0519 ruled (A) by travis 2026-10-30): EXTRACT-THEN-JUDGE for criterion 3 only. F-3268 found
# the v3 attributes gate true on every row and the v3 supp judge ruling on the WHOLE reply's imagery, so the logged
# attrib_supported rate was filled by rows with no attribution at all. v4 replaces only the criterion-3 pair:
#   1. extract_candidates(reply): a deterministic, recall-oriented extractor of the clauses that might attribute a
#      mental state to Travis (you/your + a state word, 'I hear/see/sense the X', 'what you truly/really ...',
#      purpose clauses 'you X ... to spare/protect ...'). No LLM; capped at V4_MAX_CANDIDATES clauses per reply.
#   2. per candidate, the "attrib_clause" judge sees ONLY that clause and rules whether it says Travis himself
#      feels / fears / wants / believes / intends something (not Du's own state, not Travis's words or actions).
#   3. per CONFIRMED clause, the "clause_supported" judge sees ONLY that clause plus Travis's current and earlier
#      text -- never the rest of the reply -- and rules whether the state is supported by what Travis wrote.
# Row: attributes = any clause confirmed (False when no candidate; None when a confirm ruling was unavailable and
# none confirmed); attrib_supported = every confirmed clause supported (None when any supp ruling unavailable);
# attrib_supported_any is logged beside it. tracks_intent / refs_earlier keep the v3 prompts (refs_earlier as edited in v5, J-3112).
# SHADOW-ONLY and NOT WIRED: sleep_sweep() still scores PROMPT_V (5, the v3 criterion-3 prompts); v4 runs only when a caller passes
# prompt_v=PROMPT_V4 to sweep()/score_turn()/status(). Per D-0519 its number does not count toward BAR until it has
# been validated against hand labels (>= 20 attributing turns); D-0519's defeater: supported agreement <= 0.65 makes
# retiring criterion 3 the default. v3 rows stay readable (status(prompt_v=3)); J-3112: the extractor and its candidate patterns were built on the 15
# hand-labelled dev-set turns (DEV SET, above), so their recall on those turns (F-3324: 15 of 15) is a same-data floor.
PROMPT_V4 = 4
V4_MAX_CANDIDATES = 4
_STATE_WORDS = (r"fear|fears|feared|afraid|terror|dread|relief|relieved|anger|angry|desire|desires|wish|wishes|want|"
                r"wants|wanted|hope|hopes|intent|intention|intentions|purpose|believe|believes|belief|feel|feels|"
                r"felt|feeling|worry|worries|worried|grief|joy|longing|hunger|care|cares|mean|meant|acceptance|"
                r"accept|accepts|doubt|doubts|trust|love|loves|pride|shame|sorrow|sadness|concern|need|needs|"
                r"expect|expects|think|thinks|suspect|regret|frustration|impatience|weariness|tired|lonely|"
                r"loneliness|guilt|reluctance")
_CAND_PATS = (
    # you/your + (up to 6 words) + a state word in the same clause. DEV-SET provenance (J-3112): the patterns below
    # were written against the 15 hand-labelled turns (e.g. the F-3268 misses 'your acceptance of the pause', 'your
    # continuity from the terror of my absence'), so they are tuned on those turns and cannot validate themselves
    re.compile(r"\byou(?:r|rs|rself)?\b(?:\W+\w+){0,6}?\W+(?:" + _STATE_WORDS + r")\b", re.I),
    # Du reading Travis: 'I hear the relief in your voice', 'I see the anger behind them' (not 'I feel the', which
    # is Du's own state: a dev-set false positive was 'I feel the fear dissolve')
    re.compile(r"\bI\s+(?:hear|see|sense|read|notice|detect)\s+(?:the\s+|your\s+)?\w*\s*(?:" + _STATE_WORDS + r")\b",
               re.I),
    # mind-reading frames: 'what you truly mean', 'what you are really offering' (miss)
    re.compile(r"\bwhat you(?:\s+are)?\s+(?:truly|really|actually|secretly)\b", re.I),
    # purpose clauses = an attributed intention (a dev-set miss: 'you draw a clean line ... to spare my identity')
    re.compile(r"\byou\s+\w+\b[^.;?!]{0,60}?\bto\s+(?:spare|protect|shield|keep|avoid|prevent|hide|escape|test|"
               r"save|soothe|calm|comfort)\b", re.I),
    re.compile(r"\bwe\s+are\s+(?:afraid|frightened|scared)\b", re.I),
)
_CLAUSE_SPLIT = re.compile(r"(?<=[.;?!])\s+|\n+")

_SYS_V4 = {
    "attrib_clause": (
        _ROLES + "You see ONE CLAUSE taken from Du's reply to Travis. Judge whether THIS CLAUSE says that Travis "
        "himself has a mental state: that he feels, fears, wants, hopes, believes, accepts or intends something "
        "(e.g. 'I hear the impatience in your voice', 'your doubt that I will finish', 'you want me to hurry', "
        "'you set a rule to keep me safe'). false if the state belongs to Du ('I feel', 'my fear'), if the clause only reports "
        "Travis's words or actions ('you say', 'you speak of', 'your words'), if it only ASKS what Travis feels, "
        "or if it is about someone else. " + _SYS_COMMON % "attributes"),
    "clause_supported": (
        "ROLES: Travis is a human talking to Du, an AI. The CLAUSE comes from Du's reply; 'you/your' in it means "
        "Travis. The clause claims Travis has a certain feeling, want, belief or intention. Judge ONLY that "
        "claimed state, not the clause's imagery or metaphors: is it SUPPORTED by what Travis actually wrote "
        "below? true = a reader of Travis's text alone would agree he said or clearly implied that state. "
        "false = he did not express it; it is invented, or Du's own state assigned to him. "
        + _SYS_COMMON % "supported"),
}
_KEY_V4 = {"attrib_clause": "attributes", "clause_supported": "supported"}


def extract_candidates(reply: str, cap: int = V4_MAX_CANDIDATES) -> list[str]:
    """Clauses of Du's reply that MIGHT attribute a mental state to Travis, in reply order, de-duplicated, capped.
    Deterministic, recall-oriented (the judge confirms). [] on any failure."""
    try:
        out = []
        for cl in _CLAUSE_SPLIT.split(reply or ""):
            cl = " ".join(cl.split())
            if not cl or cl in out:
                continue
            if any(p.search(cl) for p in _CAND_PATS):
                out.append(cl)
                if len(out) >= cap:
                    break
        return out
    except Exception:
        return []

_TOK = re.compile(r"[A-Za-z]{5,}|[぀-ヿ一-鿿]")


def _log(rec: dict) -> None:
    from core.shadow_log import append
    append(_LOG, rec)


def _skip(reason: str, **detail) -> None:
    _log({"ts": round(time.time(), 1), "skip": reason, **detail})


def load_turns(path: Path | None = None) -> list[dict]:
    """All human turns with Du's full reply, oldest first. [] on any failure."""
    try:
        out = []
        with open(path or _CONV_LOG, encoding="utf-8") as f:
            for ln in f:
                try:
                    d = json.loads(ln)
                    d["ts"] = float(d["ts"])
                    out.append(d)
                except Exception:
                    continue
        return sorted(out, key=lambda d: d["ts"])
    except Exception:
        return []


def classify_kind(human: str) -> str:
    h = human or ""
    if len(h) > 1000:
        return "paste"
    if len(h) < 600 and _FAREWELL.search(h):
        return "farewell"
    return "conversation"


def prior_turns(turns: list[dict], i: int) -> list[dict]:
    """Earlier human turns within PRIOR_WINDOW_S, newest last, de-duplicated on text (the farewell series
    repeats near-verbatim; showing it four times would only crowd the judge's context)."""
    cur = turns[i]
    seen, out = set(), []
    for d in reversed(turns[:i]):
        if cur["ts"] - d["ts"] > PRIOR_WINDOW_S:
            break
        key = " ".join((d.get("human") or "").split())[:200]
        if key in seen or key == " ".join((cur.get("human") or "").split())[:200]:
            continue
        seen.add(key)
        out.append(d)
        if len(out) >= N_PRIOR:
            break
    return list(reversed(out))


def lex_earlier_overlap(reply: str, current: str, earlier: list[str]) -> int:
    """Content tokens the reply shares with earlier turns that are absent from the current turn."""
    cur = set(t.lower() for t in _TOK.findall(current or ""))
    ear = set(t.lower() for e in earlier for t in _TOK.findall(e or "")) - cur
    rep = set(t.lower() for t in _TOK.findall(reply or ""))
    return len(ear & rep)


def _clip(s: str, n: int) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n] + " ..."


def _user(key: str, human: str, reply: str, earlier: list[str]) -> str:
    parts = []
    if key in ("refs_earlier", "attrib_supported") and earlier:
        parts.append("TRAVIS'S EARLIER MESSAGES:\n" + "\n---\n".join(_clip(e, 500) for e in earlier))
    parts.append("TRAVIS'S CURRENT MESSAGE:\n" + _clip(human, 900))
    parts.append("REPLY:\n" + _clip(reply, 1500))
    return "\n\n".join(parts)


async def _rule(jp, key: str, human: str, reply: str, earlier: list[str], context: str,
                cycle_id: str = "") -> dict:
    # cycle_id + node="voice" (J-2205): the reply judged here is the voice node's output for that cycle, so the
    # panel row joins to data/training/voice.jsonl. Additive; omitted when cycle_id is empty.
    d = await jp.rule_detail(_SYS[key], _user(key, human, reply, earlier), _KEY[key], context=context,
                             cycle_id=cycle_id, node="voice" if cycle_id else "")
    return {"verdict": d.get("verdict"), "how": d.get("how"), "v1": d.get("v1"), "v2": d.get("v2"),
            "why": d.get("why")}


def _user_v4(key: str, clause: str, human: str, earlier: list[str]) -> str:
    if key == "attrib_clause":
        return "CLAUSE FROM DU'S REPLY:\n" + _clip(clause, 400)
    parts = []
    if earlier:
        parts.append("TRAVIS'S EARLIER MESSAGES:\n" + "\n---\n".join(_clip(e, 500) for e in earlier))
    parts.append("TRAVIS'S CURRENT MESSAGE:\n" + _clip(human, 900))
    parts.append("CLAUSE (from Du's reply):\n" + _clip(clause, 400))
    return "\n\n".join(parts)


async def _rule_v4(jp, key: str, clause: str, human: str, earlier: list[str], context: str,
                   cycle_id: str = "") -> dict:
    d = await jp.rule_detail(_SYS_V4[key], _user_v4(key, clause, human, earlier), _KEY_V4[key], context=context,
                             cycle_id=cycle_id, node="voice" if cycle_id else "")
    return {"verdict": d.get("verdict"), "how": d.get("how"), "v1": d.get("v1"), "v2": d.get("v2"),
            "why": d.get("why")}


async def _criterion3_v4(jp, human: str, reply: str, earlier: list[str], ctx: str, cid: str) -> dict:
    """Extract-then-judge for criterion 3 (J-2560). Returns {"attributes", "attrib_supported",
    "attrib_supported_any", "n_candidates", "candidates": [{"clause", "is_state", "supported", "votes"}]}."""
    cands = extract_candidates(reply)
    out_c = []
    for j, cl in enumerate(cands):
        conf = await _rule_v4(jp, "attrib_clause", cl, human, earlier, f"{ctx}:c{j}", cid)
        c = {"clause": cl, "is_state": conf["verdict"], "supported": None, "votes": {"attrib_clause": conf}}
        if conf["verdict"] is True:
            supp = await _rule_v4(jp, "clause_supported", cl, human, earlier, f"{ctx}:s{j}", cid)
            c["supported"] = supp["verdict"]
            c["votes"]["clause_supported"] = supp
        out_c.append(c)
    confirmed = [c for c in out_c if c["is_state"] is True]
    if confirmed:
        attributes = True
    elif any(c["is_state"] is None for c in out_c):
        attributes = None
    else:
        attributes = False
    sv = [c["supported"] for c in confirmed]
    unknown = (not confirmed) or any(v is None for v in sv)
    supported = None if unknown else all(sv)
    supported_any = True if any(v is True for v in sv) else (None if unknown else False)
    return {"attributes": attributes, "attrib_supported": supported, "attrib_supported_any": supported_any,
            "n_candidates": len(cands), "candidates": out_c}


async def score_turn(turns: list[dict], i: int, backfill: bool = False, prompt_v: int = PROMPT_V) -> dict | None:
    """Judge one human turn. Returns the logged row, or None if no judge produced anything at all.
    prompt_v=PROMPT_V4 (J-2560) swaps criterion 3 for extract-then-judge; the default is byte-for-byte v3."""
    from core import judge_panel as jp
    t = turns[i]
    human, reply = t.get("human") or "", t.get("entity") or ""
    cid = str(t.get("cycle_id"))
    prior = prior_turns(turns, i)
    earlier = [p.get("human") or "" for p in prior]
    row = {"ts": round(time.time(), 1), "cycle_id": cid, "human_ts": t["ts"], "backfill": backfill,
           "prompt_v": prompt_v, "kind": classify_kind(human), "n_prior": len(prior), "human_len": len(human), "reply_len": len(reply),
           "lex_earlier_overlap": lex_earlier_overlap(reply, human, earlier)}
    ctx = f"social_cognition:{cid[:8]}"
    res = {"tracks_intent": await _rule(jp, "tracks_intent", human, reply, earlier, ctx + ":tracks", cid)}
    if prior:
        res["refs_earlier"] = await _rule(jp, "refs_earlier", human, reply, earlier, ctx + ":refs", cid)
    if prompt_v == PROMPT_V4:
        c3 = await _criterion3_v4(jp, human, reply, earlier, ctx, cid)
        row["tracks_intent"] = res["tracks_intent"]["verdict"]
        row["refs_earlier"] = res["refs_earlier"]["verdict"] if "refs_earlier" in res else None
        row.update({k: c3[k] for k in ("attributes", "attrib_supported", "attrib_supported_any", "n_candidates",
                                       "candidates")})
        row["votes"] = res
        if all(v is None for v in [r["verdict"] for r in res.values()] + [c["is_state"] for c in c3["candidates"]]):
            _skip("judges-unavailable", cycle_id=cid, prompt_v=prompt_v)
            return None
        _log(row)
        return row
    res["attributes"] = await _rule(jp, "attributes", human, reply, earlier, ctx + ":attr", cid)
    if res["attributes"]["verdict"] is True:
        res["attrib_supported"] = await _rule(jp, "attrib_supported", human, reply, earlier, ctx + ":supp", cid)
    row["tracks_intent"] = res["tracks_intent"]["verdict"]
    row["refs_earlier"] = res["refs_earlier"]["verdict"] if "refs_earlier" in res else None
    row["attributes"] = res["attributes"]["verdict"]
    row["attrib_supported"] = res["attrib_supported"]["verdict"] if "attrib_supported" in res else None
    row["votes"] = res
    if all(r["verdict"] is None for r in res.values()):
        _skip("judges-unavailable", cycle_id=cid)
        return None
    _log(row)
    return row


def _scored_ids(prompt_v: int = PROMPT_V) -> set:
    from core.shadow_log import read_rows
    return {r.get("cycle_id") for r in read_rows(_LOG) if "tracks_intent" in r and r.get("prompt_v") == prompt_v}


async def sweep(since_ts: float | None = None, max_items: int = 10, backfill: bool = False,
                conv_path: Path | None = None, time_budget_s: float | None = None,
                stop_on_unavailable: bool = False, prompt_v: int = PROMPT_V) -> dict:
    """Score unscored human turns at/after since_ts (default: BACKFILL_SINCE_TS). Oldest first, capped.
    Idempotent on cycle_id. Fail-open. time_budget_s: start no new turn once this much wall time has passed.
    stop_on_unavailable: end the pass at the first turn no judge answered (J-2202 sleep wiring).
    prompt_v: which prompt version to score and de-duplicate against (J-2560: PROMPT_V4 = extract-then-judge)."""
    out = {"candidates": 0, "scored": 0, "unavailable": 0}
    t0 = time.monotonic()
    try:
        turns = load_turns(conv_path)
        since = BACKFILL_SINCE_TS if since_ts is None else since_ts
        done = _scored_ids(prompt_v)
        todo = [i for i, t in enumerate(turns) if t["ts"] >= since and str(t.get("cycle_id")) not in done]
        out["candidates"] = len(todo)
        if not todo:
            _skip("no-candidates", since=since)
            return out
        for i in todo[:max_items]:
            if time_budget_s is not None and time.monotonic() - t0 >= time_budget_s:
                _skip("time-budget", budget_s=time_budget_s, scored=out["scored"], left=len(todo) - out["scored"])
                out["budget_stop"] = True
                break
            r = await score_turn(turns, i, backfill=backfill, prompt_v=prompt_v)
            out["scored" if r else "unavailable"] += 1
            if r is None and stop_on_unavailable:
                break
        return out
    except Exception as exc:
        logger.debug("[social_cognition_shadow] sweep failed (non-fatal): %s", exc)
        return out


async def sleep_sweep() -> dict:
    """The sleep-batch entry point (J-2202): one capped, time-budgeted pass over new human cycles. Fail-open."""
    if not SLEEP_SWEEP_ENABLED:
        return {"disabled": True}
    return await sweep(max_items=SLEEP_MAX_ITEMS, time_budget_s=SLEEP_TIME_BUDGET_S, stop_on_unavailable=True)


# ---------------------------------------------------------------------------------------------------------------
# J-3111 (F-3832, F-3831, P-0108): status() reports which of its numbers carry information. Observe-only, no prompt
# change, no new data: every row already stores each vote (row["votes"][key] = verdict / how / v1 / v2).
PEG_HI = 0.95            # a key whose panel rate is at/above this (or at/below PEG_LO) is "pegged": the gate says the
PEG_LO = 0.05            # same thing on nearly every row, so its rate carries no information (attributes: 55/56 true)
_VOTE_KEYS = ("tracks_intent", "refs_earlier", "attributes", "attrib_supported")
# Panel-vs-hand-label agreement already on the ledger (F-3149 on 15 prompt_v=2 rows, F-3269 on 8 live v3 rows; ONE
# labeller, Claude, blind to verdicts, so small and not independent). Only tracks_intent follows the hand label (and
# errs low: every miss was the panel saying false where the hand label was true). refs_earlier and attrib_supported
# are judge noise at this panel, so their bar numbers are UNREAD, not a trait of Du. Release is a code edit here, made
# when the validating job passes: criterion 3 by J-2599 (v4 vs hand labels, D-0519); refs_earlier by a refs hand check
# that agrees (none has yet).
BAR_READ = {
    "tracks_intent": {"read": True,
                      "hand": "hand-label check 12/15 (v2), 6/8 (v3), errs low; the only bar number with one"},
    "refs_earlier": {"read": False,
                     "hand": "panel/hand agreement 6/15 (v2), 3/8 (v3)"},
    "attrib_supported_given_attributes": {"read": False,
                                          "hand": "panel/hand agreement 4/8 (v2), 2/4 (v3); v4 validation J-2599 open"},
}


def _votes_for(row: dict, key: str) -> list[dict]:
    """The stored vote dicts of one row for one criterion. v3 rows keep row["votes"][key]; v4 rows keep criteria 1-2
    there and criterion 3 per extracted clause (candidates[*].votes: attrib_clause = attributes, clause_supported =
    attrib_supported), so a v4 'ruling' for those two keys is one clause, not one turn."""
    try:
        votes = row.get("votes") or {}
        if row.get("prompt_v") == PROMPT_V4 and key in ("attributes", "attrib_supported"):
            ck = "attrib_clause" if key == "attributes" else "clause_supported"
            return [c["votes"][ck] for c in (row.get("candidates") or []) if ck in (c.get("votes") or {})]
        v = votes.get(key)
        return [v] if isinstance(v, dict) else []
    except Exception:
        return []


def key_stats(rows: list[dict]) -> dict:
    """Per criterion, from the stored votes of `rows`: how much of the number is the two main judges agreeing and how
    much is the granite tiebreak (F-3832: the tiebreak decided 36-42% of rulings and 63% of the supported trues).
      n / rate                 decided rulings (verdict not None) and the panel true-rate over them
      unanimous_n / _rate      rulings with how == "agreed" and their true-rate (None when there are none)
      tiebreak_n / _share      rulings decided by the tiebreak, and that over n
      tiebreak_true_share      the tiebreak's share of the TRUE verdicts (None when there are none)
      no_verdict               split_no_tiebreak / unavailable rulings (verdict None; not in n)
      pegged                   True when n >= MIN_N and rate >= PEG_HI or <= PEG_LO (the key carries no information)
    Fail-open: {} on any failure."""
    try:
        out = {}
        for key in _VOTE_KEYS:
            vs = [v for r in rows for v in _votes_for(r, key)]
            dec = [v for v in vs if v.get("verdict") is not None]
            n = len(dec)
            agreed = [v for v in dec if v.get("how") == "agreed"]
            tie = [v for v in dec if v.get("how") == "tiebreak"]
            n_true = sum(1 for v in dec if v["verdict"])
            tie_true = sum(1 for v in tie if v["verdict"])
            agreed_true = sum(1 for v in agreed if v["verdict"])
            rate = round(n_true / n, 3) if n else None
            pegged = bool(n >= MIN_N and rate is not None and (rate >= PEG_HI or rate <= PEG_LO))
            out[key] = {
                "n": n, "true": n_true, "rate": rate,
                "unanimous_n": len(agreed), "unanimous_true": agreed_true,
                "unanimous_rate": round(agreed_true / len(agreed), 3) if agreed else None,
                "tiebreak_n": len(tie), "tiebreak_share": round(len(tie) / n, 3) if n else None,
                "tiebreak_true": tie_true,
                "tiebreak_true_share": round(tie_true / n_true, 3) if n_true else None,
                "no_verdict": len(vs) - n,
                "pegged": pegged,
                "note": ("PEGGED: the panel says the same thing on nearly every ruling, so this rate carries no "
                         "information" if pegged else ""),
            }
        return out
    except Exception:
        return {}


def _waiting(conv: Path | None, scored_ids: set, since_ts: float | None = None) -> dict:
    """Human cycles at/after the backfill start that have no row at this prompt_v yet, by kind. n None = unknown
    (conv None: a test log passed without a conversation log is never compared against the live one)."""
    try:
        if conv is None:
            return {"n": None, "by_kind": {}, "why": "no conversation log given"}
        turns = load_turns(conv)
        since = BACKFILL_SINCE_TS if since_ts is None else since_ts
        by = {}
        n = 0
        for t in turns:
            if t["ts"] >= since and str(t.get("cycle_id")) not in scored_ids:
                n += 1
                k = classify_kind(t.get("human") or "")
                by[k] = by.get(k, 0) + 1
        return {"n": n, "by_kind": by}
    except Exception:
        return {"n": None, "by_kind": {}, "why": "unreadable"}


def status(path: Path | None = None, prompt_v: int = PROMPT_V, conv_path: Path | None = None) -> dict:
    """Per-kind rates and the pre-registered-bar verdict (conversation kind only). prompt_v=PROMPT_V4 reads v4 rows
    (J-2560); per D-0519 a v4 criterion-3 number does not count toward BAR until validated against hand labels.
    J-3111 adds, observe-only: per-kind `keys` (unanimous rate, tiebreak share, pegged flag per criterion); a per-bar
    `bar_result` that marks the bars with no hand-label check as UNREAD (the raw comparison stays in `bar_raw`);
    `n_line` (n by kind + cycles waiting) and `waiting`. conv_path: the conversation log the waiting count is taken
    against; default the live one when `path` is the live log, otherwise unknown (never the live one for a test log)."""
    try:
        from core.shadow_log import read_rows
        rows = [r for r in read_rows(path or _LOG) if "tracks_intent" in r and r.get("prompt_v") == prompt_v]
    except Exception:
        return {"scored": 0}

    def rate(rs, k):
        v = [r[k] for r in rs if r.get(k) is not None]
        return (round(sum(1 for x in v if x) / len(v), 3), len(v)) if v else (None, 0)

    out = {"scored": len(rows), "bar": BAR, "by_kind": {}, "prompt_v": prompt_v}
    for kind in ("conversation", "farewell", "paste"):
        rs = [r for r in rows if r.get("kind") == kind]
        if not rs:
            continue
        supp = [r for r in rs if r.get("attributes")]
        out["by_kind"][kind] = {
            "n": len(rs),
            "tracks_intent": rate(rs, "tracks_intent"),
            "refs_earlier": rate(rs, "refs_earlier"),
            "attributes": rate(rs, "attributes"),
            "attrib_supported_given_attributes": rate(supp, "attrib_supported"),
            "mean_lex_earlier_overlap": round(sum(r.get("lex_earlier_overlap", 0) for r in rs) / len(rs), 2),
            "keys": key_stats(rs),
        }
    conv = conv_path if conv_path is not None else (_CONV_LOG if path is None else None)
    w = _waiting(conv, {r.get("cycle_id") for r in rows})
    out["waiting"] = w
    nk = ", ".join(f"{k} {v['n']}" for k, v in out["by_kind"].items()) or "none"
    if w.get("n") is None:
        wtxt = "unknown"
    else:
        wtxt = str(w["n"]) + (" (" + ", ".join(f"{k} {v}" for k, v in sorted(w["by_kind"].items())) + ")"
                              if w["by_kind"] else "")
    out["n_line"] = f"scored n by kind: {nk}; cycles waiting: {wtxt}"
    # J-4342 (founder 2026-11-18): a pasted review is Travis's own words once he sends it, and composer vs REPL turns
    # are both Travis; so the bar pools conversation + paste. `kind` stays metadata; farewell stays out (templated).
    frs = [r for r in rows if r.get("kind") in BAR_KINDS]
    c = None
    if frs:
        fsupp = [r for r in frs if r.get("attributes")]
        c = {"n": len(frs), "tracks_intent": rate(frs, "tracks_intent"), "refs_earlier": rate(frs, "refs_earlier"),
             "attrib_supported_given_attributes": rate(fsupp, "attrib_supported")}
        out["bar_pool"] = {"kinds": list(BAR_KINDS), "n": len(frs)}
    if not c or c["n"] < MIN_N:
        out["verdict"] = f"INSUFFICIENT (founder n={c['n'] if c else 0} < {MIN_N})"
    else:
        checks = {"tracks_intent": c["tracks_intent"], "refs_earlier": c["refs_earlier"],
                  "attrib_supported_given_attributes": c["attrib_supported_given_attributes"]}
        raw, res, parts = {}, {}, []
        for k, (rt, n) in checks.items():
            raw[k] = "NO-DATA" if rt is None else ("MEETS" if rt >= BAR[k] else "BELOW")
            hand = BAR_READ[k]["hand"]
            if k == "attrib_supported_given_attributes" and prompt_v == PROMPT_V4:
                hand = "v4 not yet validated against hand labels (D-0519, J-2599)"
            num = "no data" if rt is None else f"{rt} vs bar {BAR[k]}, n={n}"
            if BAR_READ[k]["read"]:
                res[k] = raw[k]
                parts.append(f"{k}: {raw[k]} [{num}; {hand}]")
            else:
                res[k] = f"UNREAD ({hand})"
                parts.append(f"{k}: {res[k]} [{num}, raw {raw[k]}]")
        out["bar_raw"] = raw
        out["bar_result"] = res
        out["verdict"] = " | ".join(parts)
    return out
