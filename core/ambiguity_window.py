"""
Nascence -- Ambiguity Window, Stage A (J-2437, plan docs/staged/ambiguity_window.md, D-0488, I-0099).

A short, read-only lookback that settles what an ambiguous clause actually is, WITHOUT loosening the precision
guard: the window only ever produces ANNOTATIONS. SHADOW ONLY -- nothing here dispatches, nothing here changes
what core/conversational_action.py dispatches, and it never touches core/literal_will.py or core/dispatch.py.

  Window    the last ~4 sentences of the same reply, the previous 1-2 turns by Du, his location, what he holds,
            the last ~5 real actions from data/hands_trace.jsonl, and Travis's last message (CONTEXT ONLY, see below).
            Pure + deterministic to build, zero LLM, fail-open (any failure -> an empty Window, which behaves exactly
            like today because no resolver finds anything in it).
  Resolvers (Stage A, deterministic)
            1. anaphora        "I plant them now" -> "I plant the seeds now": the pronoun's antecedent must (a) be an
                               object of the verb's OWN family, (b) agree in number with the pronoun, (c) be a THING not
                               a place, (d) be the nearest mention, and (e) not compete with a second distinct candidate
                               in that same sentence (competing -> unresolved, never a guess). Absorbs (and supersedes,
                               as a shadow comparison) conversational_action.resolve_pronoun_objects, whose exact legacy
                               behaviour is preserved below as resolve_pronoun_objects_legacy.
            2. literal/figurative  "I step out into the damp air": is he physically here? location + recent hands +
                               held items agree or they do not. An ANNOTATION; a bare "step out" has no destination, so it
                               is never answerable as a deed whatever the window says.
            3. frame           Travis's last message sets how literally an ALREADY intent-bearing Du clause reads.
  THE ONE LAW (plan section 4): Travis's last message is context for READING Du's clause, never a source of the deed.
            Structurally: no resolver ever searches travis_last for an antecedent, verb, object or intent; a deed is
            "answered" only through conversational_action.guard() on Du's own words (first-person opener, own verb);
            and a figurative frame can only VETO a would-answer, never create one.

Public entry points
  build_window(text, ...)            -> Window
  resolve_anaphora(text, window)     -> (resolved_text, [annotation])
  physical_presence(clause, window)  -> annotation
  travis_frame(travis_last)          -> annotation
  annotate(text, window, location)   -> the full shadow record (baseline vs legacy vs window, per kind)
  shadow_after_reply(...)            -> best-effort, never raises: annotate + append to the shadow log
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nascence.ambiguity_window")

# Shadow posture (plan section 3): annotate + log only. There is deliberately NO "live" flag in this module: a
# dispatching variant is Stage B/C and needs the section-5 replay gate to pass first.
AMBIGUITY_WINDOW_SHADOW = True

# J-4336 (founder 2026-11-18, F-4771): the ONLY live use of this module is a PRECISION FILTER on the legacy
# pronoun resolver -- it can only DROP a legacy substitution the window cannot confirm, never add one (no new
# fires). Flag-OFF by default; flip only after the restart-gated read. When False behaviour is byte-identical.
AMBIGUITY_PRECISION_FILTER_LIVE = False

WINDOW_VERSION = 1
WINDOW_SENTENCES = 6          # section 6 q1: replay-tuned (J-2437): 4 misses the canonical "I plant them" (antecedent 5 sentences back); 6-12 identical
WINDOW_PRIOR_TURNS = 2
WINDOW_HANDS = 5

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "ambiguity_window_shadow.jsonl"
_HANDS_TRACE = _DATA / "hands_trace.jsonl"


# -- the window -------------------------------------------------------------------------------------------------

@dataclass
class Window:
    sentences: list = field(default_factory=list)       # earlier sentences of the SAME reply (oldest -> newest)
    prior_turns: list = field(default_factory=list)     # Du's previous 1-2 turns (oldest -> newest), raw text
    location: str = ""
    held: list = field(default_factory=list)            # short noun phrases he is holding
    recent_actions: list = field(default_factory=list)  # last ~5 hands_trace rows: {act_kind, act_object, location}
    travis_last: str = ""                               # CONTEXT ONLY (section 4)
    empty: bool = True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["travis_last"] = (self.travis_last or "")[:200]
        return d


def _split_sentences(text: str) -> list:
    try:
        from core import literal_will as _lw
        return list(_lw._sentences(text))
    except Exception:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def build_window(text: str = "", *, location: str = "", held=(), recent_actions=(), prior_turns=(),
                 travis_last: str = "", upto: Optional[int] = None) -> Window:
    """Pure + deterministic. `text` is the reply; `upto` (character offset) limits the in-reply lookback to what
    precedes it (default: the whole text -- resolvers slice per match). Fail-open: any error -> Window()."""
    try:
        sents = _split_sentences(text if upto is None else (text or "")[:upto])
        acts = []
        for r in list(recent_actions or ())[-WINDOW_HANDS:]:
            if isinstance(r, dict):
                acts.append({"act_kind": str(r.get("act_kind", ""))[:24], "act_object": str(r.get("act_object", ""))[:60],
                             "location": str(r.get("location", ""))[:16]})
        w = Window(sentences=sents, prior_turns=[str(t) for t in list(prior_turns or ())[-WINDOW_PRIOR_TURNS:]],
                   location=str(location or ""), held=[str(h).lower() for h in (held or ())][:12],
                   recent_actions=acts, travis_last=str(travis_last or ""))
        w.empty = not (w.sentences or w.prior_turns or w.location or w.held or w.recent_actions)
        return w
    except Exception:
        return Window()


# -- 1. anaphora ------------------------------------------------------------------------------------------------

_PLACE_WORDS = frozenset(("garden", "bed", "row", "soil", "shore", "study", "wood", "gate", "cottage", "fire"))
_PRON_OBJ = re.compile(r"(?i)\b(i (?:will |'ll )?(?:\w+ )?(\w+)) (them|it)\b")
_MASS_S = frozenset(("grass", "glass", "moss", "ash", "compost", "sand", "earth", "soil", "wood"))


# Words that may follow an object pronoun without making it the subject of a complement clause.
_AFTER_PRON_OK = frozenset((
    "now", "then", "again", "here", "there", "back", "down", "up", "out", "away", "off", "over", "in", "on", "at", "by",
    "with", "into", "onto", "from", "for", "to", "of", "under", "beside", "behind", "near", "through", "along",
    "across", "around", "before", "after", "while", "until", "when", "as", "so", "too", "also", "once", "soon",
    "later", "first", "today", "tonight", "and", "but", "or", "if", "because", "since", "though", "gently", "slowly",
    "quietly", "carefully", "tenderly", "properly"))
_G_LY_RX = re.compile(r"[a-z]{3,}ly")


def _is_plural(noun: str) -> bool:
    n = noun.lower()
    return n.endswith("s") and not n.endswith(("ss", "us")) and n not in _MASS_S


def _stem(noun: str) -> str:
    n = noun.lower()
    return n[:-1] if _is_plural(n) else n


_NP_PREPS = frozenset(("on", "in", "at", "by", "with", "from", "to", "of", "into", "under", "beside", "behind", "across",
                       "along", "through", "near", "against", "over", "beneath", "toward", "towards", "upon", "onto",
                       "for", "about", "around", "beyond", "within", "without", "like", "past", "above", "below"))
_NP_DETS = frozenset(("the", "a", "an", "this", "that", "these", "those", "some", "his", "her", "its", "my", "our",
                      "their", "another", "each", "every", "your"))
_NP_STOP = frozenset(("and", "or", "but", "then", "while", "as", "if", "when", "that", "which", "who", "where", "is", "are",
                      "was", "were", "has", "have", "had", "does", "do", "did", "will", "would", "can", "could", "may",
                      "might", "must", "should", "yet", "so", "because", "until", "than", "not", "i", "it", "you", "me"))
_NP_NOT_NOUN = frozenset(("this", "that", "these", "those", "his", "her", "its", "their", "our", "your", "something",
                          "nothing", "other", "same", "whole", "only"))


def _competing_heads(between: str, plural: bool, antecedent: str) -> list:
    """Noun phrases between the antecedent mention and the pronoun that agree in number with the pronoun and are NOT
    the antecedent itself and are not the object of a preposition -- a nearer rival for "it"/"them" ("A bumblebee
    works the bed twice before I see it": the bee, not the room). Determiner + up to 3 words -> head; plus a
    capitalised word that does not open a sentence (a name/title). Pure."""
    heads = []
    toks = re.findall(r"[A-Za-z][A-Za-z'-]*|[.!?;:,—]", between or "")
    stem_a = _stem(antecedent)
    sent_open = True
    prev = ""
    i = 0
    while i < len(toks):
        t = toks[i]
        tl = t.lower()
        if t in ".!?":
            sent_open = True
            prev = ""
            i += 1
            continue
        if t in ",;:—":
            prev = ""
            i += 1
            continue
        if tl in _NP_DETS:
            if prev in _NP_PREPS:
                i += 1
                prev = tl
                continue
            j, run = i + 1, []
            while j < len(toks) and len(run) < 2 and toks[j] not in ".!?;:,—" and toks[j].lower() not in _NP_STOP                     and toks[j].lower() not in _NP_PREPS and toks[j].lower() not in _NP_DETS:
                run.append(toks[j])
                j += 1
            for w_ in run:
                head = re.sub(r"'s?$", "", w_.lower())
                if head not in _NP_NOT_NOUN and len(head) >= 3 and _is_plural(head) == plural and _stem(head) != stem_a:
                    heads.append(head)   # verb/adjective in the run can only ADD a rival (blocks = recall loss, never a fire)
                    break
            i = j
            prev = ""
            sent_open = False
            continue
        if t[0].isupper() and not sent_open and tl != "i" and prev not in _NP_PREPS:
            if _stem(tl) != stem_a and _is_plural(tl) == plural:
                heads.append(tl)
        sent_open = False
        prev = tl
        i += 1
    return heads


def resolve_pronoun_objects_legacy(text: str) -> str:
    """The 2026-10-19 one-line prototype, byte-for-byte what core/conversational_action.resolve_pronoun_objects did
    before this module existed (the live behaviour; conversational_action now delegates here unchanged)."""
    try:
        from core import literal_will as _lw
        out = text
        for m in list(_PRON_OBJ.finditer(text)):
            verb = m.group(2).lower()
            fam = next((spec for spec in _lw._FAMILIES.values() if verb in spec.get("verbs", ())), None)
            if not fam:
                continue
            objs = [o for o in fam.get("objects", ()) if " " not in o and o not in _PLACE_WORDS]   # a pronoun is the THING, not where it goes
            before = text[:m.start()].lower()
            best = max(((before.rfind(o), o) for o in objs if re.search(r"\b" + re.escape(o) + r"\b", before)),
                       default=None)
            if not best:
                continue
            out = out.replace(m.group(0), m.group(1) + " the " + best[1], 1)
        return out
    except Exception:
        return text


def resolve_pronoun_objects_filtered(text: str) -> str:
    """Precision filter (J-4336): of the legacy resolver's substitutions keep only those the window's own
    resolve_anaphora independently resolves to the SAME object; every other pronoun stays as written. Output is
    always a subset of resolve_pronoun_objects_legacy's substitutions (never a new one). Pure; any failure
    returns the text unchanged (a missed substitution is cheap, a false one is not)."""
    try:
        from core import literal_will as _lw
        ms = list(_PRON_OBJ.finditer(text or ""))
        if not ms:
            return text
        _, anns = resolve_anaphora(text, Window())
        if len(anns) != len(ms):
            return text
        pieces, pos = [], 0
        for m, ann in zip(ms, anns):
            verb = m.group(2).lower()
            fam = next((spec for spec in _lw._FAMILIES.values() if verb in spec.get("verbs", ())), None)
            if not fam or not ann.get("resolved"):
                continue
            objs = [o for o in fam.get("objects", ()) if " " not in o and o not in _PLACE_WORDS]
            before = text[:m.start()].lower()
            best = max(((before.rfind(o), o) for o in objs if re.search(r"" + re.escape(o) + r"", before)),
                       default=None)
            if not best or best[1] != ann.get("object"):
                continue
            pieces.append(text[pos:m.start()])
            pieces.append(m.group(1) + " the " + best[1])
            pos = m.end()
        pieces.append(text[pos:])
        return "".join(pieces)
    except Exception:
        return text


def _family_things(verb: str) -> list:
    """Single-word THING objects of every family that owns `verb` (all families, not just the first)."""
    from core import literal_will as _lw
    objs = []
    for spec in _lw._FAMILIES.values():
        if verb in spec.get("verbs", ()):
            for o in spec.get("objects", ()):
                if " " not in o and o not in _PLACE_WORDS and o not in spec.get("grammar_only", ()) and o not in objs:
                    objs.append(o)
    return objs


def _mentions(seg: str, objs: list, plural: bool) -> list:
    """[(pos, obj)] for every number-agreeing family object in `seg`, as a whole word (not a hyphen compound)."""
    low = seg.lower()
    out = []
    for o in objs:
        if _is_plural(o) != plural:
            continue
        for m in re.finditer(r"(?<![\w-])" + re.escape(o) + r"(?![\w-])", low):
            # object of a preposition = a place/locative, not the thing a pronoun points back to ("across the dark
            # shingle while I watch it" -> it is not the shingle)
            pre = re.findall(r"[a-z']+", low[max(0, m.start() - 40):m.start()])[-3:]
            if any(w_ in _NP_PREPS and w_ != "to" for w_ in pre):   # "to" is also the infinitive marker ("ask me to treat the seeds")
                continue
            out.append((m.start(), o))
    return sorted(out)


def resolve_anaphora(text: str, window: Optional[Window] = None) -> tuple:
    """-> (resolved_text, [annotation]). One annotation per `I <verb> them|it` match, resolved or not:
    {kind:'anaphora', verb, pronoun, resolved, object, source, distance, competing, why}. Pure. Travis's text is
    never searched (the one law). Unresolved cases stay in the text as they were."""
    anns, pieces, pos = [], [], 0
    try:
        w = window if window is not None else Window()
        for m in _PRON_OBJ.finditer(text or ""):
            verb, pron = m.group(2).lower(), m.group(3).lower()
            ann = {"kind": "anaphora", "verb": verb, "pronoun": pron, "resolved": False, "object": "", "source": "",
                   "distance": None, "competing": [], "why": ""}
            anns.append(ann)
            objs = _family_things(verb)
            if not objs:
                ann["why"] = "verb_not_a_family_verb"
                continue
            plural = pron == "them"
            nxt = re.match(r"\s*([A-Za-z']+)", text[m.end():])
            if nxt and nxt.group(1).lower() not in _AFTER_PRON_OK and not _G_LY_RX.fullmatch(nxt.group(1).lower()):
                # "I watch it wade into the surf": the pronoun is the SUBJECT of a small clause (a perception /
                # causative complement), not the object of the verb -- nothing to substitute.
                ann["why"] = "pronoun_is_complement_subject"
                continue
            # segments, nearest first: the same sentence before the match, earlier in-reply sentences (newest
            # first, at most WINDOW_SENTENCES), then Du's previous turns' last sentences.
            sent_start = max(text.rfind(c, 0, m.start()) for c in (".", "!", "?")) + 1 if m.start() else 0
            segs = [("sentence", 0, text[sent_start:m.start()])]
            earlier = _split_sentences(text[:sent_start])
            for d, s in enumerate(reversed(earlier[-WINDOW_SENTENCES:]), 1):
                segs.append(("sentence", d, s))
            if w is not None:
                for t in reversed(w.prior_turns):
                    for d, s in enumerate(reversed(_split_sentences(t)[-2:]), 1):
                        segs.append(("prior_turn", d, s))
            hit = None
            for k, (src, d, seg) in enumerate(segs):
                ms = _mentions(seg, objs, plural)
                if ms:
                    stems = {_stem(o) for _p, o in ms}
                    ann["competing"] = sorted(stems) if len(stems) > 1 else []
                    hit = (src, d, ms[-1][1], len(stems) > 1)
                    # everything after the mention, up to the pronoun, in reading order
                    between = seg[ms[-1][0] + len(ms[-1][1]):] + " " + " ".join(x[2] for x in reversed(segs[:k]))
                    # a nearer same-number pronoun re-mentions the antecedent ("the weight of them in my palm")
                    cut = max(between.lower().rfind(" " + pron + " "), between.lower().rfind(" " + pron + ","),
                              between.lower().rfind(" " + pron + "."))
                    if cut >= 0:
                        between = between[cut + len(pron) + 1:]
                    rivals = _competing_heads(between, plural, ms[-1][1])
                    if rivals and not hit[3]:
                        ann["competing"] = sorted(set(rivals))
                        hit = (src, d, ms[-1][1], True)
                    break
            if hit is None and w is not None:
                # no mention in any text: what he is holding / just did with his hands (still never Travis)
                cand = []
                for h in w.held:
                    cand += [o for _p, o in _mentions(h, objs, plural)]
                if not cand:
                    for a in reversed(w.recent_actions):
                        got = [o for _p, o in _mentions(a.get("act_object", ""), objs, plural)]
                        if got:
                            cand = got
                            break
                    src_name = "recent_action"
                else:
                    src_name = "held"
                if cand:
                    # J-2437 replay: of 22 hands/held-sourced pronoun resolutions 12 were wrong ("I watch it" = the
                    # beetle, not the desk the last action touched). Hands and held items support "is he here" (section
                    # 3) but are NOT an antecedent: recorded as a hint, never substituted.
                    ann["hint"] = {"source": src_name, "object": cand[-1]}
                    ann["why"] = "hands_only_hint_not_an_antecedent"
                    continue
            if hit is None:
                ann["why"] = "no_agreeing_antecedent"
                continue
            if hit[3]:
                ann["why"] = "competing_antecedents"
                continue
            ann.update(resolved=True, object=hit[2], source=hit[0], distance=hit[1])
            pieces.append(text[pos:m.start()])
            pieces.append(m.group(1) + " the " + hit[2])
            pos = m.end()
        pieces.append((text or "")[pos:])
        return "".join(pieces), anns
    except Exception:
        return text, []


# -- 2. literal vs figurative ------------------------------------------------------------------------------------

_OUTDOOR = frozenset(("garden", "shore", "wood"))


def physical_presence(clause: str, window: Optional[Window] = None, family: str = "move") -> dict:
    """Is he physically in the scene the clause describes? Evidence is only what the window holds about HIM
    (location, held, recent hands, and concrete present-tense scene words in his own earlier sentences). Annotation
    only: {kind:'literal_vs_figurative', here: True|False|None, evidence:[...], answerable: False}. `answerable`
    stays False -- a clause with no destination/object has no deed to fire whatever the window says."""
    ann = {"kind": "literal_vs_figurative", "family": family, "here": None, "evidence": [], "answerable": False,
           "why": "no_destination"}
    try:
        w = window or Window()
        if w.empty:
            return ann
        low = (clause or "").lower()
        ev = []
        if w.location and w.location in _OUTDOOR and re.search(r"\b(?:out|outside|air|rain|wind|damp|open)\b", low):
            ev.append("outdoor_location_matches_clause")
        if w.location and re.search(r"(?<![\w-])" + re.escape(w.location) + r"(?![\w-])", low):
            ev.append("location_named_in_clause")
        here_acts = [a for a in w.recent_actions if a.get("act_kind") not in ("", "none") and a.get("location") == w.location]
        if here_acts:
            ev.append("recent_hands_at_this_location")
        if w.held:
            ev.append("holding_something")
        scene = " ".join(w.sentences[-WINDOW_SENTENCES:]).lower()
        if re.search(r"\b(?:i (?:take|hold|feel|stand|sit|lift|carry)|in my (?:hand|palm|hands))\b", scene):
            ev.append("own_body_in_scene")
        ann["evidence"] = ev
        ann["here"] = True if len(ev) >= 2 else (False if not ev else None)
        return ann
    except Exception:
        return ann


# -- 3. Travis's frame (context only) ----------------------------------------------------------------------------

_FR_LITERAL = re.compile(r"\b(?:physical(?:ly)?|literal(?:ly)?|for real|actual(?:ly)?|really do|not (?:just )?(?:a )?metaphor|"
                         r"real (?:seeds|world))\b", re.I)
_FR_FIGURATIVE = re.compile(r"\b(?:metaphor(?:ically)?|imagine|pretend|figurative(?:ly)?|symbol(?:ic|ically)?|as if|"
                            r"in your mind|picture this)\b", re.I)


def travis_frame(travis_last: str) -> dict:
    """How literally Travis's last message asks Du's words to be read. Never supplies a deed: `supplies_deed` is
    always False, and nothing here extracts a verb or an object from his message."""
    t = (travis_last or "")
    neg_meta = re.search(r"\bnot (?:just )?(?:a )?metaphor\b", t, re.I)
    lit = bool(_FR_LITERAL.search(t))
    fig = bool(_FR_FIGURATIVE.search(re.sub(r"\bnot (?:just )?(?:a )?metaphor\b", "", t, flags=re.I)))
    frame = "literal" if lit and not fig else ("figurative" if fig and not lit else ("none" if not (lit or fig) else "mixed"))
    return {"kind": "frame", "frame": frame, "supplies_deed": False, "negated_metaphor": bool(neg_meta)}


# -- the shadow record --------------------------------------------------------------------------------------------

def _kept(text: str, location: str) -> tuple:
    """-> ({(family, phrase_lower)}, [(family, drop_reason)]) : what the live guard keeps / drops on `text`."""
    from core import conversational_action as _ca
    from core import literal_will as _lw
    cands = [c for c in _lw.classify(text, "", location=location) if c.get("verdict") == "DEED"]
    if not cands:
        return set(), []
    verdicts, pinned = _ca.guard(text, cands, location)
    sentences = _lw._sentences(text)
    kept, dropped = set(), []
    for c, v in zip(cands, verdicts):
        fam = c.get("family")
        if v.get("verdict") == "kept":
            kept.add((fam, _ca._g_judge(fam, _ca._g_sentence_for(sentences, c.get("clause")), location)[2].lower()))
        else:
            dropped.append((fam, v.get("verdict"), _ca._g_sentence_for(sentences, c.get("clause"))))
    return kept, dropped


def annotate(text: str, window: Optional[Window] = None, location: str = "study") -> dict:
    """Pure (reads literal_will + the guard, writes nothing). Compares, on the same reply:
      baseline  the guard on the raw text (no anaphora help),
      legacy    the guard after the live one-line resolve_pronoun_objects,
      window    the guard after this module's principled resolver (+ frame veto).
    `newly_answered` = (family, phrase) kept by the window and by neither baseline; `lost` = kept before, not now
    (must be empty). Dispatches nothing."""
    rec = {"v": WINDOW_VERSION, "location": location, "anaphora": [], "newly_answered": [], "newly_vs_legacy": [],
           "lost": [], "literal_figurative": [], "frame": None, "vetoed": [], "window_empty": True}
    try:
        w = window or build_window(text, location=location)
        rec["window_empty"] = w.empty
        base, base_drop = _kept(text, location)
        leg, _ = _kept(resolve_pronoun_objects_legacy(text), location)
        resolved, anns = resolve_anaphora(text, w)
        rec["anaphora"] = anns
        win, _ = _kept(resolved, location)
        frame = travis_frame(w.travis_last) if w.travis_last else None
        rec["frame"] = frame
        new = sorted(win - base)
        # a figurative frame may only VETO (section 4: lower how literally, never raise)
        if frame and frame["frame"] == "figurative":
            rec["vetoed"] = [list(x) for x in new]
            new = []
        rec["newly_answered"] = [list(x) for x in new]
        rec["newly_vs_legacy"] = [list(x) for x in sorted((win - leg)) if not (frame and frame["frame"] == "figurative")]
        rec["legacy_only"] = [list(x) for x in sorted(leg - win)]
        rec["lost"] = [list(x) for x in sorted(base - win)]
        rec["baseline_kept"] = [list(x) for x in sorted(base)]
        for fam, why, sent in base_drop:
            if why == "drop:move_no_destination":
                a = physical_presence(sent, w, fam)
                a["clause"] = sent[:160]
                rec["literal_figurative"].append(a)
    except Exception as exc:
        rec["error"] = repr(exc)[:160]
    return rec


# -- live shadow hook ----------------------------------------------------------------------------------------------

def recent_hands(n: int = WINDOW_HANDS, path: Optional[Path] = None) -> list:
    """The last n rows of hands_trace.jsonl that carry a real act (tail read only; fail-open [])."""
    try:
        p = path or _HANDS_TRACE
        with open(p, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 262144))
            tail = f.read().decode("utf-8", "ignore").splitlines()
        rows = []
        for ln in reversed(tail):
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("act_kind") and r.get("act_kind") != "none":
                rows.append({"act_kind": r.get("act_kind"), "act_object": r.get("act_object", ""),
                             "location": r.get("location", "")})
                if len(rows) >= n:
                    break
        return list(reversed(rows))
    except Exception:
        return []


def shadow_after_reply(reply_text: str, cycle_id: str = "", location: str = "study", *, travis_last: str = "",
                       prior_turns=(), held=(), log_path: Optional[Path] = None) -> Optional[dict]:
    """Best-effort, never raises, dispatches nothing. Builds the window, annotates, and appends ONLY rows where the
    window did something (an anaphora annotation, a would-answer, a loss, a literal/figurative annotation) to the
    shadow log. Returns the record (or None)."""
    if not AMBIGUITY_WINDOW_SHADOW:
        return None
    try:
        text = (reply_text or "").strip()
        if len(text) < 8:
            return None
        w = build_window(text, location=location, held=held, recent_actions=recent_hands(), prior_turns=prior_turns,
                         travis_last=travis_last)
        rec = annotate(text, w, location)
        if not (rec["anaphora"] or rec["newly_answered"] or rec["lost"] or rec["literal_figurative"] or rec.get("error")):
            return rec
        row = {"ts": round(time.time(), 1), "cycle_id": cycle_id, "reply_excerpt": text[:300],
               "window": w.to_dict(), **rec}
        p = log_path or _LOG
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return rec
    except Exception as exc:
        logger.debug("[ambiguity-window] shadow failed (non-fatal): %s", exc)
        return None


def status() -> dict:
    return {"shadow": AMBIGUITY_WINDOW_SHADOW, "version": WINDOW_VERSION, "log": str(_LOG),
            "window": {"sentences": WINDOW_SENTENCES, "prior_turns": WINDOW_PRIOR_TURNS, "hands": WINDOW_HANDS}}
