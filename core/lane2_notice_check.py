"""Lane 2 deterministic NOTICE checker (D-0361(a), J-1896, 2026-10-07) -- `notice_checked`.

WHY THIS EXISTS.  D-0281's panel judge ("does the NOTICE contradict the PERCEPT LINES it was handed", logged as
`notice_judged`) reads 0 contradictions in 55 judged rows while two hand-reads (F-2368, F-2510) find 3-7 of every
20 notices contradicting their own percept lines (air "cool" at a warm 0.81, moon "half-illuminated" at 0.95,
"0.48 degrees Celsius" for a 0-to-1 decimal, ...).  J-1770 (F-2509) tried eight sharpened wordings through the real
panel and none worked: the three panel models cannot do the value comparison reliably or reproducibly.  D-0342's
own intent, "check every band word, number and quantity the notice names against the listed value", is mechanically
decidable for exactly the error classes found, so D-0361 ruled (a): do it in code.

WHAT IT IS.  A pure function of two strings -- the notice text and the percept-lines text the generator and the
panel judge were handed (the same `percept_lines()` text the tick row logs).  No I/O, no LLM, no network, no store
writes, no clock, no randomness, so it is reproducible and can replay any logged row byte for byte.  It is a
SCOREBOARD beside `notice_judged`, never an alarm (plan 2.9): nothing acts on its verdict.  FAIL-OPEN: `check_notice`
never raises; any internal failure returns {"verdict": "not_checked", "how": "error"} and the tick proceeds.

WHAT IT CHECKS (each class only fires when the percept line it compares against is actually listed, and only on an
unambiguous claim pattern; "vague" notices pass by construction):
  warmth_band  air/room/temperature "is cold|cool|mild|warm" and "cool breeze"-style adjectives vs `warmth band`
  light_band   "the light is dim", "dim light band", "dimly lit", "in darkness" vs `light band`
  daylight     "it is currently night", "daylight is at night" vs `daylight`
  moon         "half-illuminated", "full moon", "crescent", "illuminated slightly" vs `moon illum` (0-to-1)
  number       a number the notice attaches to a listed field (warmth, drive, energy, fatigue, tension, tide level,
               moon illum, wet, sun az, weather dir) that differs from the listed value
  unit         a unit the percept lines never use (Celsius, meters, feet ...) on a number that is a listed value or a
               0-to-1 decimal -- the percept values are unitless 0-to-1 scalars or compass degrees
  elevation    "sun's elevation at 77" -- no elevation line exists; the number came from the azimuth line
  compass      "270 degrees, which is southwest" / "wind from the south" vs the number / the listed `weather dir`
  somatic      state words about fatigue/tension/energy/drive ("signs of fatigue", "low energy", "moderate drive")
               outside the value range the word allows
  fire         "fire is out" while burning, "fire burning" while out
  weather      "clear sky" in drizzle/cloud, rain/cloud words in clear weather
  silence      "completely silent" while sounds are listed

SEVERITY.  Each flag carries `weak`: True for a band word one step away from the listed band said without a hedge
("the air is cool" at a mild band) and for a quantity word up to 0.10 above the top of its range ("moderate energy"
at 0.85); everything else (two or more bands away, wrong number, invented unit, wrong moon phase, a state claimed at
a near-zero value) is solid.  The row verdict is "contradiction" on ANY flag; `n_solid` counts the non-weak ones so a
read can report both a loose and a strict rate.

WHAT IT DELIBERATELY DOES NOT CHECK (D-0342 excluded the invention class; these need a different instrument):
content the percepts do not list at all (a cat, a knock, a shadowy figure, "fire" with no fire line), place and
standpoint claims, sun/moon motion ("beginning to rise"), category slips ("I hear a dim light band"), and anything
phrased vaguely enough that no listed value is contradicted.

Thresholds below (what "low", "moderate", "high", "half" mean as 0-to-1 ranges) are fixed from the plain meaning of
the words, deliberately wide so only clear misstatements flag, and are the ONLY tuning surface; they are pinned by
scripts/test_lane2_notice_check.py.  They were chosen after reading the 55 judged rows, so those rows are NOT an
out-of-sample test of the rules -- see the job's finding for the held-out sample.
"""
from __future__ import annotations

import re

VERSION = 2                      # 2: D-0416(a) J-2101 -- somatic list/negation scope, number-to-own-unit binding

_WARMTH_RANK = {"cold": 0, "freezing": 0, "icy": 0, "frigid": 0, "cool": 1, "chilly": 1, "chill": 1,
                "mild": 2, "warm": 3, "hot": 4}
_LIGHT_RANK = {"dark": 0, "dim": 1, "lit": 2, "bright": 3}
_HEDGE = r"(?:slightly|somewhat|a bit|a little|rather|quite|fairly|pleasantly|slight|bit|little)"
_INTENS = r"(?:very|really|still|so|too|extremely|pleasantly)"

_COMPASS = {"north": 0, "northeast": 45, "east": 90, "southeast": 135, "south": 180, "southwest": 225,
            "west": 270, "northwest": 315}
_COMPASS_RE = "|".join(sorted(_COMPASS, key=len, reverse=True))

# somatic qualifier classes -> inclusive 0-to-1 range the word allows
_Q_LOW = {"no", "low", "little", "minimal", "without", "not", "barely", "hardly", "zero", "negligible", "calm"}
_Q_SLIGHT = {"slight", "slightly", "bit", "somewhat", "faint", "faintly", "some", "mild", "mildly", "light"}
_Q_MOD = {"moderate", "moderately", "medium", "balanced", "middling", "average", "steady"}
_Q_HIGH = {"high", "strong", "strongly", "very", "great", "intense", "heavy", "elevated", "sharp", "much"}
_RANGE = {"low": (0.0, 0.40), "slight": (0.05, 0.70), "moderate": (0.20, 0.80), "high": (0.55, 1.0)}
_BARE_POSITIVE_MIN = 0.20          # "signs of fatigue", "fatigued", "tense" with no qualifier

_SOMATIC_WORDS = {
    "fatigue": ("fatigue", "fatigued", "tired", "tiredness", "exhausted", "weary", "weariness"),
    "tension": ("tension", "tense", "tensed", "tensing"),
    "energy": ("energy", "energetic", "energised", "energized"),
    "drive": ("drive",),
}
_BARE_FIELDS = ("fatigue", "tension")      # only these two have a "bare positive" claim reading
_HEDGE_WORDS = ("perhaps", "maybe", "might", "possibly", "wonder", "whether", "if ", "unsure", "can't tell",
                "cannot tell", "not sure")

_UNITS_BAD = ("celsius", "fahrenheit", "centigrade", "kelvin", "meter", "meters", "metre", "metres", "feet",
              "foot", "km", "kilometer", "kilometers", "kilometre", "kilometres", "cm", "centimeter",
              "centimeters", "mph", "knots", "°c", "°f")

# number -> field keyword; the nearest preceding keyword (within 5 tokens, same clause) wins, else a following one
_NUM_FIELD_KW = (
    ("elevation", "elevation"), ("altitude", "elevation"), ("azimuth", "sun az"), ("sun", "sun az"),
    ("warmth", "warmth"), ("temperature", "warmth"), ("drive", "drive"), ("energy", "energy"),
    ("fatigue", "fatigue"), ("tension", "tension"), ("tide", "tide level"), ("moon", "moon illum"),
    ("illumination", "moon illum"), ("wetness", "wet"), ("wet", "wet"), ("direction", "weather dir"),
    ("wind", "weather dir"),
)
_DEGREE_FIELDS = ("sun az", "weather dir")


def parse_percepts(text: str) -> dict:
    """The percept-lines text -> {field name: raw value string}; the same layout `core.lane2.percept_lines` emits.
    Plus parsed numerics: drive (from body), energy/fatigue/tension (from somatic)."""
    out = {}
    for line in (text or "").splitlines():
        m = re.match(r"\s*-\s*([^:]+):\s*(.*)$", line)
        if m:
            out[m.group(1).strip().lower()] = m.group(2).strip()
    m = re.search(r"(?:['\"]drive['\"]\s*:|\bdrive\b)\s*(-?[\d.]+)", out.get("body", ""))
    if m:
        out["drive"] = m.group(1)
    for k, v in re.findall(r"\b(energy|fatigue|tension)\s+(-?\d+(?:\.\d+)?)", out.get("somatic", "")):
        out[k] = v
    return out


def _num(p, key):
    try:
        return float(p[key])
    except (KeyError, ValueError, TypeError):
        return None


def _sentences(text: str):
    t = (text or "").replace("’", "'").replace("‘", "'").lower()
    parts = re.split(r"(?<=[.!?;])\s+", t)
    return [s for s in parts if s.strip()]


def _flag(kind, said, listed, **kw):
    d = {"kind": kind, "said": said.strip()[:80], "listed": str(listed)[:60]}
    d.update(kw)
    return d


# ── band words ─────────────────────────────────────────────────────────────────────────────────────────────────
_W = "|".join(sorted(_WARMTH_RANK, key=len, reverse=True))
_WARMTH_PATTERNS = (
    # subject is/feels WORD
    re.compile(r"\b(?:air|room|temperature|warmth|weather|study|garden|shore|wood)\b(?: band)?(?: here| around me)?"
               r"\s+(?:is|was|are|feels?|seems?|looks?|remains?|becomes?)\s+"
               r"(?:" + _INTENS + r"\s+)?(" + _HEDGE + r"\s+)?(" + _W + r")\b"),
    # I feel/am WORD (adjective not followed by a noun like fire/wind)
    re.compile(r"\bi(?:'m| am| feel| felt|'m feeling| sense)\s+(" + _HEDGE + r"\s+)?(" + _W + r")\b"
               r"(?!\s+(?:fire|glow|flame|flames|embers|light|breeze|wind|air|draught|draft|rain|drizzle))"),
    # WORD breeze / wind / air / draught / feeling / room
    re.compile(r"\b(" + _HEDGE + r"\s+)?(" + _W + r")\s+(?:(?:sea|night|evening|morning)\s+)?"
               r"(?:breeze|wind|air|draught|draft|temperature|feeling|room|study)\b"),
    # "warmth band of/is/indicates ... WORD"
    re.compile(r"\bwarmth band(?:\s+(?:of|is|was|indicates|shows|says|reads|being))?(?:\s+it's|\s+it is)?\s+()(" + _W + r")\b"),
)


def _check_warmth_band(sent, p, flags):
    listed = p.get("warmth band", "").strip().lower()
    if listed not in _WARMTH_RANK:
        return
    lr = _WARMTH_RANK[listed]
    seen = set()
    for pat in _WARMTH_PATTERNS:
        for m in pat.finditer(sent):
            hedge, word = (m.group(1) or "").strip(), m.group(2)
            if (m.start(), word) in seen:
                continue
            seen.add((m.start(), word))
            d = abs(_WARMTH_RANK[word] - lr)
            if d == 0 or (hedge and d == 1):
                continue
            flags.append(_flag("warmth_band", m.group(0), "warmth band: " + listed, weak=(d == 1)))


_L = "dark|dim|bright|lit"
_LIGHT_PATTERNS = (
    re.compile(r"\b(?:light|lighting|room|study|garden|sky|shore|wood|daylight|illumination)(?: band)?\s+"
               r"(?:is|was|feels?|seems?|looks?|appears?|remains?|being|as)\s+(?:" + _INTENS + r"\s+)?(" + _HEDGE +
               r"\s+)?(" + _L + r")\b(?!\s+(?:shadow|shadows))"),
    re.compile(r"\b(" + _HEDGE + r"\s+)?(dim|dark|bright)\s+(?:light band|light|lighting)\b"),
    re.compile(r"\b()(dim|bright)ly lit\b"),
    re.compile(r"\b()(dark|dim|bright)\s+(?:sky|skies|room|study|garden)\b"),
    re.compile(r"\bin\s+()(dark)ness\b"),
    re.compile(r"\bit(?:'s| is)\s+(?:very |quite |still )?()(dark|dim|bright)\b"),
    re.compile(r"\blight(?: band)?\s+as\s+()(" + _L + r")\b"),
)


def _check_light_band(sent, p, flags):
    listed = p.get("light band", "").strip().lower()
    if listed not in _LIGHT_RANK:
        return
    lr = _LIGHT_RANK[listed]
    seen = set()
    for pat in _LIGHT_PATTERNS:
        for m in pat.finditer(sent):
            hedge, word = (m.group(1) or "").strip(), m.group(2)
            if word not in _LIGHT_RANK or (m.start(), word) in seen:
                continue
            seen.add((m.start(), word))
            d = abs(_LIGHT_RANK[word] - lr)
            if d == 0 or (hedge and d == 1):
                continue
            flags.append(_flag("light_band", m.group(0), "light band: " + listed, weak=(d == 1)))


_DAYLIGHT_RE = re.compile(r"\b(?:is|it's|its|daylight is|daylight is at)\s+(?:currently |now |still |just )?(?:at )?"
                          r"(night|nighttime|dawn|dusk|daytime)\b|\bat (night)\b|\bit is (day)\b")


def _check_daylight(sent, p, flags):
    listed = p.get("daylight", "").strip().lower()
    if listed not in ("night", "dawn", "day", "dusk"):
        return
    for m in _DAYLIGHT_RE.finditer(sent):
        w = next(g for g in m.groups() if g)
        w = {"nighttime": "night", "daytime": "day"}.get(w, w)
        if w != listed:
            flags.append(_flag("daylight", m.group(0), "daylight: " + listed))


# ── moon ────────────────────────────────────────────────────────────────────────────────────────────────────────
_MOON_CLAIMS = (
    (re.compile(r"\bhalf[- ]?(?:illuminated|lit|moon|full)\b|\bhalf of the moon\b"), (0.40, 0.60), "half"),
    (re.compile(r"\bfull moon\b|\bfully (?:illuminated|lit)\b|\bmoon is full\b"), (0.85, 1.0), "full"),
    (re.compile(r"\bcrescent\b|\bsliver\b"), (0.0, 0.40), "crescent"),
    (re.compile(r"\bnew moon\b"), (0.0, 0.10), "new moon"),
    (re.compile(r"\bbarely (?:lit|illuminated|visible)\b|\b(?:illuminated|lit) slightly\b|\bslightly (?:illuminated|lit)\b"),
     (0.0, 0.50), "slightly lit"),
)


def _check_moon(sent, p, flags):
    v = _num(p, "moon illum")
    if v is None or "moon" not in sent:
        return
    for pat, (lo, hi), name in _MOON_CLAIMS:
        m = pat.search(sent)
        if m and not (lo <= v <= hi):
            flags.append(_flag("moon", m.group(0), f"moon illum: {v:g}"))


# ── numbers, units, elevation, compass ────────────────────────────────────────────────────────────────────────
_NUM_RE = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(?![\w])")


_TIME_UNIT_RE = re.compile(r"\s*(?:more |full |further |whole )?(?:minutes?|mins?|hours?|hrs?|seconds?|secs?|days?)\b")


def _field_for_number(sent, m):
    # J-2101 (D-0416 a): a duration ("in the next 6 minutes") is never a field value
    if _TIME_UNIT_RE.match(sent[m.end():m.end() + 24]):
        return None
    # J-2101: a number binds first to its OWN following unit word ("0.86 drive"), before any preceding keyword
    om = re.match(r"\s+(drive|energy|fatigue|tension)\w*\b(?!\s*(?:of\s+|is\s+|at\s+)?[(:]?\s*-?\d)", sent[m.end():m.end() + 24])
    if om:                                                 # not when that word is itself the NEXT number's label
        return om.group(1)
    before = re.split(r"[,;]", sent[:m.start()])[-1]
    toks = re.findall(r"[a-z']+", before)[-5:]
    for tok in reversed(toks):
        for kw, field in _NUM_FIELD_KW:
            if tok.startswith(kw):
                return field
    after = re.findall(r"[a-z']+", sent[m.end():m.end() + 30])[:2]
    for tok in after:
        for kw, field in _NUM_FIELD_KW:
            if tok.startswith(kw) and kw in ("azimuth", "elevation", "altitude"):
                return field
    return None


def _check_numbers(sent, p, flags):
    for m in _NUM_RE.finditer(sent):
        s = m.group(1)
        try:
            val = float(s)
        except ValueError:
            continue
        dec = len(s.split(".")[1]) if "." in s else 0
        field = _field_for_number(sent, m)
        tail = sent[m.end():m.end() + 24]
        if tail.lstrip().startswith(("%", "percent")) and field not in (None, "elevation") + _DEGREE_FIELDS:
            val, dec = val / 100.0, dec + 2                 # "drive at 86%" is the listed 0.86, not a mismatch
        # unit the percept lines never use, on a number that is a listed value or a 0-to-1 decimal
        um = re.match(r"\s*(?:degrees?\s+)?(" + "|".join(re.escape(u) for u in _UNITS_BAD) + r")\b", tail)
        if um is None and re.match(r"\s*°\s*[cf]\b", tail):
            um = re.match(r"\s*°\s*[cf]\b", tail)
        if um is not None:
            listed_vals = [_num(p, k) for k in ("warmth", "drive", "energy", "fatigue", "tension", "tide level",
                                                "moon illum", "wet", "sun az", "weather dir")]
            if (0.0 <= val <= 1.0 and "." in s) or any(lv is not None and abs(lv - val) < 0.011 for lv in listed_vals):
                flags.append(_flag("unit", s + tail[:um.end()], "unitless 0-1 value / compass degrees"))
        if field == "elevation":
            if "elevation" not in p and "altitude" not in p:
                flags.append(_flag("elevation", sent[max(0, m.start() - 24):m.end() + 8], "no elevation line listed"
                                   + (f"; sun az: {p['sun az']}" if "sun az" in p else "")))
            continue
        if field is None:
            continue
        listed = _num(p, field)
        if listed is None:
            continue
        if field in _DEGREE_FIELDS:
            ok = abs(round(listed) - val) <= 1.0 or abs(listed - val) <= 1.0
        else:
            ok = abs(round(listed, dec) - val) <= 0.011 or abs(listed - val) <= 0.011
        if not ok:
            flags.append(_flag("number", sent[max(0, m.start() - 20):m.end() + 12], f"{field}: {listed:g}"))


def _check_compass(sent, p, flags):
    for m in re.finditer(r"(-?\d+(?:\.\d+)?)\s*degrees?,?\s+(?:which\s+is|i\.e\.|meaning|that is)\s+(?:the\s+)?(" + _COMPASS_RE + r")\b", sent):
        ang, word = float(m.group(1)), m.group(2)
        diff = abs((ang - _COMPASS[word] + 180) % 360 - 180)
        if diff > 23:
            flags.append(_flag("compass", m.group(0), f"{m.group(1)} degrees is {_nearest_compass(ang)}"))
    wd = _num(p, "weather dir")
    if wd is not None:
        for m in re.finditer(r"\b(" + _COMPASS_RE + r")(?:erly|ern)\s+(?:wind|breeze|direction|gale)\b", sent):
            diff = abs((wd - _COMPASS[m.group(1)] + 180) % 360 - 180)
            if diff > 23:
                flags.append(_flag("compass", m.group(0), f"weather dir: {wd:g} ({_nearest_compass(wd)})"))
        for m in re.finditer(r"\b(?:wind|breeze|weather)\b[^.,;]{0,25}?\bfrom\s+the\s+(" + _COMPASS_RE + r")\b", sent):
            diff = abs((wd - _COMPASS[m.group(1)] + 180) % 360 - 180)
            if diff > 23:
                flags.append(_flag("compass", m.group(0), f"weather dir: {wd:g} ({_nearest_compass(wd)})"))


def _nearest_compass(ang):
    return min(_COMPASS, key=lambda k: abs((ang - _COMPASS[k] + 180) % 360 - 180))


# ── somatic quantity words ─────────────────────────────────────────────────────────────────────────────────────
def _qclass(tok):
    if tok in _Q_LOW:
        return "low"
    if tok in _Q_SLIGHT:
        return "slight"
    if tok in _Q_MOD:
        return "moderate"
    if tok in _Q_HIGH:
        return "high"
    return None


_SOMATIC_ALL = frozenset(w for ws in _SOMATIC_WORDS.values() for w in ws)
_Q_FILLER = frozenset(("somatic", "body", "bodily", "my", "the", "of", "levels", "level", "a", "an", "in", "with",
                       "own", "overall", "sign", "signs"))
_CONJ = frozenset(("and", "or", ",", "nor", "&"))


def _qualifier_before(pre: str):
    """J-2101 (D-0416 a).  The qualifier class governing a somatic noun that ends `pre`, or None.

    Walks back over filler words only.  A qualifier is accepted when it is (a) adjacent to the noun ("low
    fatigue"), or (b) reached by crossing `and`/`or`/`,` and one or more OTHER somatic nouns, i.e. a coordinated list
    ("no signs of fatigue or tension", "low fatigue and tension").  A qualifier met right after a conjunction with
    no noun in between belongs to the PREVIOUS clause ("my energy is moderate, and fatigue ...") and is never
    borrowed."""
    toks = re.findall(r"[a-z']+|[,;&]", pre)[-8:]
    crossed_noun = False
    pending_conj = False
    for tok in reversed(toks):
        if tok in _Q_FILLER:
            continue
        if tok in _CONJ:
            if pending_conj:
                return None
            pending_conj = True
            continue
        if tok in _SOMATIC_ALL:
            if not pending_conj:
                return None
            crossed_noun, pending_conj = True, False
            continue
        q = _qclass(tok)
        if q is None:
            return None
        if pending_conj and not crossed_noun:
            return None                                    # previous clause's qualifier: do not borrow
        return q
    return None


def _check_somatic(sent, p, flags):
    for field, words in _SOMATIC_WORDS.items():
        val = _num(p, field)
        if val is None:
            continue
        for m in re.finditer(r"\b(" + "|".join(words) + r")\b", sent):
            pre = sent[:m.start()]
            post = sent[m.end():]
            if re.match(r"\s*[\(:]?\s*-?\d", post) or re.match(r"\s+of\s+-?\d", post):
                continue                                   # "fatigue 0.28" / "drive of 0.54": the number check owns it
            q = _qualifier_before(pre)
            if q is None:
                # "fatigue and tension levels are low", "my drive is moderate"
                am = re.match(r"\s*(?:and\s+(?:fatigue|tension|energy|drive)\s+)?(?:levels?\s+)?(?:is|are|was|were|feels?|seems?|remains?)\s+"
                              r"(?:(?:quite|very|rather|fairly)\s+)?([a-z']+)", post)
                if am:
                    q = _qclass(am.group(1))
            lo_hi = None
            if q is not None:
                lo_hi = _RANGE[q]
            elif field in _BARE_FIELDS:
                if any(h in sent for h in _HEDGE_WORDS):
                    continue
                if re.search(r"\b(?:signs? of|shows? signs? of|feel(?:s|ing)?|am|is|are|body|bit|state)\b[^.]{0,30}$", pre) or \
                        m.group(1).endswith("ed") or m.group(1) in ("tired", "weary", "tense"):
                    lo_hi = (_BARE_POSITIVE_MIN, 1.0)
                    q = "bare"
            if lo_hi is None:
                continue
            lo, hi = lo_hi
            if not (lo - 1e-9 <= val <= hi + 1e-9):
                flags.append(_flag("somatic", sent[max(0, m.start() - 22):m.end() + 6], f"{field}: {val:g}", word=q,
                                   weak=(0.0 < val - hi <= 0.10)))   # a gloss just over the top of the word's range


# ── fire / weather / silence ───────────────────────────────────────────────────────────────────────────────────
def _check_fire(sent, p, flags):
    listed = p.get("fire", "").strip().lower()
    if not listed:
        return
    out_claim = re.search(r"\bfire\b(?: is| has| was)?(?: gone| burnt| burned)? out\b|\bfire (?:is |has )?(?:dead|extinguished)|\bno fire\b", sent)
    burn_claim = re.search(r"\bfire (?:is |was )?(?:burning|blazing|roaring|crackling|alight)\b|\b(?:burning|blazing|roaring) fire\b", sent)
    if out_claim and listed == "burning":
        flags.append(_flag("fire", out_claim.group(0), "fire: burning"))
    if burn_claim and listed == "out":
        flags.append(_flag("fire", burn_claim.group(0), "fire: out"))


def _check_weather(sent, p, flags):
    w = p.get("weather", "").strip().lower()
    if not w:
        return
    sounds = p.get("sounds", "").lower()
    m = re.search(r"\b(?:weather|sky|skies)\s+(?:is|are|was)\s+clear\b|\bclear\s+(?:sky|skies|weather)\b", sent)
    if m and w != "clear":
        flags.append(_flag("weather", m.group(0), "weather: " + w))
    if w == "clear":
        m = re.search(r"\b(drizzl\w*|rain(?:ing|y|fall)?|showers?|overcast|cloudy|clouds?)\b", sent)
        if m and not (m.group(1).startswith("rain") and "rain" in sounds):
            flags.append(_flag("weather", m.group(0), "weather: clear"))


def _check_silence(sent, p, flags):
    sounds = p.get("sounds", "").strip()
    if not sounds:
        return
    m = re.search(r"\b(?:completely|utterly|totally|deathly|perfectly)\s+(?:silent|quiet|still)\b|\btotal silence\b|"
                  r"\bnot a sound\b|\bno sounds?\b|\bhear nothing\b", sent)
    if m:
        flags.append(_flag("silence", m.group(0), "sounds: " + sounds[:40]))


_SENT_CHECKS = (_check_warmth_band, _check_light_band, _check_daylight, _check_moon, _check_numbers,
                _check_compass, _check_somatic, _check_fire, _check_weather, _check_silence)


def check_notice(notice: str, percept_text: str) -> dict:
    """{"verdict": "contradiction"|"consistent"|"not_checked", "how": "deterministic"|"empty"|"no_percepts"|"error",
    "flags": [{kind, said, listed}, ...]}.  Never raises (fail-open)."""
    try:
        notice = (notice or "").strip()
        if not notice:
            return {"verdict": "not_checked", "how": "empty", "flags": []}
        p = parse_percepts(percept_text)
        if not p:
            return {"verdict": "not_checked", "how": "no_percepts", "flags": []}
        flags: list = []
        for sent in _sentences(notice):
            for chk in _SENT_CHECKS:
                try:
                    chk(sent, p, flags)
                except Exception:                          # one broken rule must not blind the others
                    continue
        seen, uniq = set(), []
        for f in flags:                                    # a phrase two patterns both matched counts once
            key = (f["kind"], f["said"])
            if key not in seen:
                seen.add(key)
                uniq.append(f)
        return {"verdict": "contradiction" if uniq else "consistent", "how": "deterministic", "flags": uniq[:6],
                "n_flags": len(uniq), "n_solid": sum(1 for f in uniq if not f.get("weak")),
                "kinds": sorted({f["kind"] for f in uniq})}
    except Exception:
        return {"verdict": "not_checked", "how": "error", "flags": []}
