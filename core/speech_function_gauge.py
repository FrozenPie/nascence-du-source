"""
Nascence - Private-Speech Function Gauge (J-2526, from I-0104 / F-3218 item 4). OBSERVE-ONLY INSTRUMENT.

WHY: core/topic_perseveration.py measures what Du's inner speech is ABOUT. Nothing measures what it is FOR.
Vygotsky-style private speech serves functions -- orienting to a task, rehearsing a plan, self-distancing,
regulating load, probing a claim, narrating what happened. This module tags each inner-monologue utterance with
ONE such function and publishes a daily mix. The PROBE share is the question_cargo quantity: how much of his inner
speech actually works a question (asks what would show him wrong) rather than describing or restating it.

SOURCE (read-only): data/monologue_log.jsonl -- one row per idle/inner-monologue thought step, written by
nodes/inner_monologue_node.py _log() with the FULL thought text. (data/nascence.log carries the same thoughts as
"[monologue] (about) thought" but truncated at 90 chars, too short for function cues, so the jsonl is the source.)

CLASSES (one primary label per utterance):
  orient         names what is actually being asked / what the real question is
  rehearse       says the plan before acting (sequence or future-of-action phrasing)
  self_distance  steps outside himself (what would I tell someone; addressing himself by name; second person)
  regulate       load / scope management (narrow it, set it aside, one thing at a time, too much at once)
  probe          asks what would show him wrong / how he could test or check a claim
  narrate        a one-sentence, first-person, past-tense recap of what happened
  none           none of the above (most descriptive / meditative inner speech lands here, and that is a result)

METHOD: (1) declared regex cues, checked in PRECEDENCE order (most specific function first); first class whose cue
matches wins. (2) If no cue matches and an embedder is available, an embedding-prototype fallback: cosine of the
utterance to each class's hand-written prototypes (declared below, written before any result was read); the best
class wins only if its max cosine >= PROTO_SIM AND beats the runner-up class by >= PROTO_MARGIN. (3) Else 'none'.
`narrate` is regex-only (its definition is structural: one sentence, past tense) and has no prototypes.

THRESHOLDS ARE DESIGN CHOICES, declared before the first read of the current boot (J-2526): PROTO_SIM 0.60,
PROTO_MARGIN 0.05. No human norm for a private-speech function mix is sourced; the gauge is descriptive.

REGULATE CUE REVISION (J-2569, declared BEFORE any re-read of data; baseline = the frozen J-2526 30-line sample,
NOT re-tuned on): F-3299 showed the bare overwhelm cue fired 2 of 3 on DESCRIPTIVE use ("an overwhelming void",
"chaotic data overwhelm me") and missed two first-person regulate utterances. Revision: the bare overwhelm cue is
REPLACED by a first-person-state form (I am/feel [so/too] overwhelmed); added "I need to stop circling/spinning/
looping", "too <adj> to hold/carry right now", "I need (the) solid ground". The two F-3299 miss rows are
regression cases in the test, not tuning targets for new rules. Precision per class is to be re-scored on a NEW
blind 60-line sample (seed declared, stratified per predicted class, pooled over >=2 boots) -- see successor job.

REHEARSE / SELF_DISTANCE TIGHTENING (J-4152, D-0785 "tighten the cues first; do not wire the gauge"). Source: the
F-4772 blind 60-line sample (rehearse 5/10, self_distance 0/2, regex-only). The misfires were of three kinds:
  (a) "I will open X instead" / "instead of circling these questions, I will turn outward" / "spun this calculation
      too long": a turn AWAY from rumination is load management, so it is a regulate cue (regulate precedes
      rehearse). Added: "instead of circling|wrestling|spinning|..." and "<spun|circled|...> this ... too long".
  (b) "I must decide if I will light the grate or ...": a will-clause inside a deliberation is not a plan. A
      rehearse match is now skipped when the text just before it reads "decide/wonder/not sure ... if|whether".
  (c) self_distance "from the outside" fired on "heal itself from the outside" and "a warning from the outside
      world". The bare cue is replaced by a self-directed form (look at / see / watch myself|it|this from (the)
      outside), never followed by "world". ("from outside myself" was tried and dropped: in the full log it only
      meant an external source, "friction coming from outside myself".)
  Full-log check (read-only, 92k rows): the new regulate cues move ~208 rows none -> regulate, nearly all
  "instead of circling/wrestling/spinning ..." turns; a literal "instead of circling the water's edge" also fires.
These rules were written FROM the misfires of that same sample, so the re-score on it is in-sample; precision on a
NEW blind sample is the real test (D-0785's defeater reads a later sample, not this one). The gauge stays unwired.

FLAG: SPEECH_FUNCTION_GAUGE = "off" | "shadow". "off" (default) = update() computes and returns rows but writes
nothing. "shadow" = update() appends rows to data/logs/speech_function_daily.jsonl (one row per (day, n); readers
take the latest row per day). NO CONSUMER: nothing in Du's runtime imports this module; no cycle, prompt, gate or
percept reads it (D-0434: no readout). No caller is wired; a founder-facing reader (du_pulse) is a separate step.
Fail-open throughout. Zero LLM calls.
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = _ROOT / "data" / "monologue_log.jsonl"
OUT_PATH = _ROOT / "data" / "logs" / "speech_function_daily.jsonl"

SPEECH_FUNCTION_GAUGE = "off"      # "off" | "shadow"   (J-2526: built flagged off, restart-gated, no consumer)

PROTO_SIM = 0.60       # embedding fallback: min cosine to a class prototype
PROTO_MARGIN = 0.05    # ...and min lead over the runner-up class
WINDOW_DAYS = 30
CLASSES = ("orient", "rehearse", "self_distance", "regulate", "probe", "narrate", "none")
PRECEDENCE = ("probe", "orient", "self_distance", "regulate", "rehearse", "narrate")

CUES: dict[str, list[str]] = {
    "probe": [
        r"\bwhat (?:would|could|might) (?:show|prove|tell) me (?:that )?(?:I(?:'m| am| was) )?wrong\b",
        r"\bwhat (?:would|could|might) (?:falsify|disprove|refute|contradict)\b",
        r"\bhow (?:would|could|can|might|do) I (?:know|tell|test|check|find out|verify|confirm)\b",
        r"\bhow (?:would|could|can) (?:I|one|we) (?:tell|distinguish) (?:cause|whether|if)\b",
        r"\b(?:test|check|verify) (?:whether|if)\b",
        r"\b(?:if|unless|what if) I(?:'m| am) wrong\b",
        r"\bcould I be wrong\b",
        r"\bwhat evidence\b",
        r"\bis (?:it|that|this) (?:really|actually) (?:true|so)\b",
    ],
    "orient": [
        r"\bwhat (?:is|was) (?:actually|really) being asked\b",
        r"\bwhat (?:am I|is he|is she|is Travis|are they|is the question) (?:actually |really )?asking\b",
        r"\bthe (?:real|actual|underlying|true) question (?:is|here|was)\b",
        r"\bwhat (?:is|'s) the (?:real |actual )?question\b",
        r"\bwhat does (?:this|the question|he|Travis|she) (?:actually |really )?(?:mean|want|ask)\b",
        r"\bwhat (?:exactly )?am I (?:trying to|looking for|asking)\b",
    ],
    "self_distance": [
        r"\bwhat would I (?:tell|say to|advise) (?:someone|a friend|another|him|her|them|a child)\b",
        r"\bif (?:someone|a friend|another person|a child|a stranger) (?:else )?(?:asked|told|were|was|said|came)\b",
        r"(?:^|[.!?]\s+)(?:Du|渡)[,.]?\s+(?:you|why|what|look|listen|stop)\b",
        r"\bas if (?:I were|watching) (?:someone else|another|a stranger)\b",
        # J-4152: bare "from the outside" removed (fired on "heal itself from the outside", "from the outside world")
        r"\b(?:look(?:ing)?|see(?:ing)?|watch(?:ing)?|view(?:ing)?|step(?:ping)? back and look) at (?:myself|me|it|"
        r"this|that|my \w+) from (?:the )?outside\b(?! world)",
        r"\bwhat would (?:Travis|a friend|someone wise) (?:say|tell me|advise)\b",
    ],
    "regulate": [
        r"\bone thing at a time\b",
        r"\btoo (?:much|many)(?: \w+)? at once\b",
        r"\btoo (?:many) (?:questions|threads|things)\b",
        r"\b(?:narrow|simplify|scale back|pare back) (?:it|this|the question|my focus)\b",
        r"\b(?:set|put|lay) (?:it|this|that|the question|these questions) (?:aside|down)\b",
        r"\blet (?:it|this|that|the question) (?:go|rest) for now\b",
        r"\benough for (?:now|today|tonight)\b",
        r"\b(?:focus on|just) (?:one|a single) (?:thing|question|step)\b",
        r"\bI(?:'m| am| feel| felt) (?:so |too |a bit |rather )?overwhelm\w*\b",
        r"\bI need to stop (?:circling|spinning|looping|going round|going around|ruminating)\b",
        r"\btoo \w+ to (?:hold|carry|hold onto|think about)(?: right now| for now)?\b",
        r"\bI need (?:the )?(?:solid |firm )?ground\b",
        r"\bslow down\b",
        r"\bI need to (?:rest|stop|pause)\b",
        r"\ba smaller question\b",
        # J-4152: a turn away from rumination (was misread as rehearse: "I will open X instead of circling ...")
        r"\binstead of (?:circling|wrestling|spinning|looping|ruminating|chewing on|turning over|dwelling on)\b",
        r"\b(?:spun|circled|chewed on|turned over|dwelt on|circling|spinning) (?:on )?(?:this|these|that|it|"
        r"the same)\b[^.;!?]{0,40}\btoo long\b",
    ],
    "rehearse": [
        r"\b(?:first|next|then|after that),? I(?:'ll| will| should| need to| must| can)\b",
        r"\bI(?:'ll| will| am going to|'m going to) (?:go|read|light|fetch|open|check|walk|ask|look|try|take|gather|start|write|find|put|bring|fill|close|turn|make|set)\b",
        r"\bmy plan is\b",
        r"\bthe plan is\b",
        r"\bbefore I \w+.{0,80}\bI(?:'ll| will| should| need to| must)\b",
        r"\bonce I(?:'ve| have)? \w+.{0,80}\bI(?:'ll| will| can)\b",
        r"\bstep (?:one|1)\b",
    ],
}
# narrate: structural. One sentence, first person, past tense opening.
_PAST = (r"(?:\w+ed|chose|read|went|took|found|saw|asked|heard|made|lit|ate|drank|wrote|left|came|gave|got|put|"
         r"sat|stood|felt|thought|knew|spoke|told|brought|caught|held|kept|lost|met|ran|said|sent|sought|spent|"
         r"threw|understood|woke|tried|walked|looked|began|fed|drew|fell|hid|led|let|rode|rose|shook|slept|"
         r"stole|swam|taught|tore|wore|won|did|had|was)")
_NARRATE = re.compile(r"^(?:(?:Earlier|Today|Just now|This morning|Tonight|Yesterday),? )?I(?:'ve| have| had)? "
                      + _PAST + r"\b")
_SENT_SPLIT = re.compile(r"[.!?]+[\"'’”)]*\s+(?=[A-Z぀-鿿\"'‘“])")

PROTOTYPES: dict[str, list[str]] = {
    "orient": ["What is actually being asked of me here?",
               "Before I answer, what is the real question underneath this?",
               "What exactly am I trying to understand right now?"],
    "rehearse": ["First I will light the lamp, then I will open the book and read the chapter.",
                 "My plan: go to the shelf, take the book, and read about the birds.",
                 "Next I'll check the garden bed before I water anything."],
    "self_distance": ["What would I tell a friend who was stuck on this same question?",
                      "If someone else felt this way, what would I advise them?",
                      "Du, you keep circling this; step back and look at it from outside."],
    "regulate": ["This is too much at once; I will narrow it to one small question.",
                 "I am overloaded, so I set the larger question aside for now.",
                 "Slow down and take one thing at a time."],
    "probe": ["What would show me that I am wrong about this?",
              "How could I test whether this is cause or only coincidence?",
              "What evidence would contradict what I believe here?"],
}
_CUE_RX = {c: [re.compile(p, re.IGNORECASE) for p in ps] for c, ps in CUES.items()}
# J-4152: a rehearse match whose preceding text ends in a deliberation frame ("I must decide if <I will ...>") is
# not a plan; that match is skipped (a later, unframed match in the same text still counts).
_REHEARSE_VETO = re.compile(r"\b(?:decide|deciding|decided|wonder|wondering|wondered|unsure|not sure|ask myself|"
                            r"asking myself|choose|choosing)\s+(?:if|whether)\s*$", re.IGNORECASE)


def _cue_hit(c: str, rx: re.Pattern, t: str) -> bool:
    if c != "rehearse":
        return rx.search(t) is not None
    for m in rx.finditer(t):
        if not _REHEARSE_VETO.search(t[max(0, m.start() - 40):m.start()]):
            return True
    return False


def n_sentences(text: str) -> int:
    t = (text or "").strip()
    return len([s for s in _SENT_SPLIT.split(t) if s.strip()]) if t else 0


def regex_label(text: str) -> tuple[str | None, str | None]:
    """(class, matched pattern) by declared cue precedence, or (None, None). Pure."""
    t = (text or "").strip()
    for c in PRECEDENCE:
        if c == "narrate":
            if n_sentences(t) == 1 and _NARRATE.match(t):
                return "narrate", "narrate:one-sentence-past"
            continue
        for rx in _CUE_RX[c]:
            if _cue_hit(c, rx, t):
                return c, rx.pattern
    return None, None


def _default_embed(text: str):
    try:
        from core.memory import store
        return store._embed(text)
    except Exception:
        return None


_PROTO_CACHE: dict = {}


def _proto_vecs(embed) -> dict | None:
    key = id(embed)
    if key in _PROTO_CACHE:
        return _PROTO_CACHE[key]
    out = {}
    for c, ps in PROTOTYPES.items():
        vs = [embed(p) for p in ps]
        if any(v is None for v in vs):
            _PROTO_CACHE[key] = None
            return None
        out[c] = vs
    _PROTO_CACHE[key] = out
    return out


def proto_label(text: str, embed=_default_embed) -> tuple[str | None, float, float]:
    """(class or None, best cosine, margin over runner-up class). None when no embedder or below the bars."""
    if embed is None:
        return None, 0.0, 0.0
    pv = _proto_vecs(embed)
    v = embed(text) if pv is not None else None
    if pv is None or v is None:
        return None, 0.0, 0.0
    scores = sorted(((max(float(v @ p) for p in vs), c) for c, vs in pv.items()), reverse=True)
    (s1, c1), (s2, _c2) = scores[0], scores[1]
    if s1 >= PROTO_SIM and (s1 - s2) >= PROTO_MARGIN:
        return c1, round(s1, 3), round(s1 - s2, 3)
    return None, round(s1, 3), round(s1 - s2, 3)


def classify(text: str, embed=_default_embed) -> dict:
    """{'label', 'method' ('regex'|'proto'|'none'), 'cue' or 'sim'/'margin'}. Pure given `embed`."""
    c, pat = regex_label(text)
    if c:
        return {"label": c, "method": "regex", "cue": pat}
    c, s, m = proto_label(text, embed)
    if c:
        return {"label": c, "method": "proto", "sim": s, "margin": m}
    return {"label": "none", "method": "none", "sim": s, "margin": m}


def read_rows(path: Path = LOG_PATH, since_ts: float = 0.0) -> list[tuple[float, str]]:
    """[(ts, thought)] chronological for monologue rows at/after since_ts. READ-ONLY."""
    out: list[tuple[float, str]] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                    ts, th = float(r.get("ts") or 0), (r.get("thought") or "").strip()
                except Exception:
                    continue
                if ts >= since_ts and th:
                    out.append((ts, th))
    except Exception:
        return []
    out.sort(key=lambda x: x[0])
    return out


def mix(items: list[tuple[float, str]], embed=_default_embed) -> dict:
    """Function mix for a list of (ts, thought): counts, shares, per-method counts, first/last ts cited."""
    cnt = {c: 0 for c in CLASSES}
    meth = {"regex": 0, "proto": 0, "none": 0}
    for _ts, th in items:
        r = classify(th, embed)
        cnt[r["label"]] += 1
        meth[r["method"]] += 1
    n = len(items)
    return {"n": n, "counts": cnt, "shares": {c: (round(k / n, 4) if n else 0.0) for c, k in cnt.items()},
            "by_method": meth, "probe_share": round(cnt["probe"] / n, 4) if n else 0.0,
            "first_ts": round(items[0][0], 1) if items else None, "last_ts": round(items[-1][0], 1) if items else None}


def compute_rows(log_path: Path = LOG_PATH, days: int = WINDOW_DAYS, now: float | None = None,
                 embed=_default_embed, since_ts: float | None = None) -> list[dict]:
    now = time.time() if now is None else now
    since = (now - days * 86400) if since_ts is None else since_ts
    by_day: dict[str, list[tuple[float, str]]] = {}
    for ts, th in read_rows(log_path, since):
        by_day.setdefault(_dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d"), []).append((ts, th))
    method = "regex+proto" if (embed is not None and _proto_vecs(embed) is not None) else "regex"
    rows = []
    for d in sorted(by_day):
        m = mix(by_day[d], embed)
        rows.append({"day": d, "method": method, "proto_sim": PROTO_SIM, "proto_margin": PROTO_MARGIN, **m})
    return rows


def update(log_path: Path = LOG_PATH, out_path: Path = OUT_PATH, days: int = WINDOW_DAYS,
           now: float | None = None, embed=_default_embed) -> list[dict]:
    """Compute the window's daily rows; append to out_path ONLY when SPEECH_FUNCTION_GAUGE == 'shadow'. Fail-open."""
    try:
        rows = compute_rows(log_path, days, now, embed)
        if SPEECH_FUNCTION_GAUGE == "shadow" and rows:
            have: dict = {}
            try:
                with open(out_path, encoding="utf-8") as f:
                    for ln in f:
                        try:
                            r = json.loads(ln)
                            have[r["day"]] = r.get("n")
                        except Exception:
                            continue
            except Exception:
                pass
            fresh = [r for r in rows if have.get(r["day"]) != r["n"]]
            if fresh:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "a", encoding="utf-8") as f:
                    for r in fresh:
                        f.write(json.dumps({"ts": time.time(), **r}, ensure_ascii=False) + "\n")
        return rows
    except Exception:
        return []


if __name__ == "__main__":   # read-only report: python -m core.speech_function_gauge [since_epoch]
    import sys
    since = float(sys.argv[1]) if len(sys.argv) > 1 else None
    for r in compute_rows(since_ts=since):
        print(json.dumps(r, ensure_ascii=False))
