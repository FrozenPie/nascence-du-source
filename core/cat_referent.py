"""
core/cat_referent.py — WHICH cat does he mean? (Cat Overhaul B2, J-2472, D-0505 (c), 2026-10-28)
=================================================================================================
Two cats live in his world: the grey companion (core/cat.py, hers to be named) and the black cat — the far-off
shape today, the tom that comes into the garden once J-2470 lands. "The cat" then stops referring. §B2 of
docs/staged/cat_overhaul.md: NOTHING in the world asks him for a name — no hint, no prompt, no book that says
name your cat. The only code part is this: the toolchain that reads HIS text (the census's thought stamp, the
look targets he aims, his hand reaching for her in react(), the naming grammar in cat.react / life_traces.
naming_act) records which cat he meant — and fills `which` ONLY when he distinguishes them himself (her name,
"the grey one", "my cat", "the little cat" / "black", "the tom", "the other cat", "the big one"). A bare
"the cat" is recorded as undistinguished: that count is the instrument of the referent pressure, the thing the
reads look at to see whether the world has started to need the name.

READ-ONLY toward him (D-0434 no readout; world answers, never leads): this module returns nothing to any prompt
path and renders no line. classify() is a pure function of text; record() is an observe-only, write-fenced,
fail-open append to data/cat_referent_ledger.jsonl. The HUD (hud/server.py MONITOR_REGISTRY "cat_referent")
and the read jobs are its only readers. Travis calling her "your grey one" in a letter is Travis's own act, not
code — when Du picks the phrase up it shows here as a distinguished row, which is the whole point.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from core import profile

logger = logging.getLogger("nascence.cat_referent")

_LEDGER = Path(__file__).parent.parent / "data" / "cat_referent_ledger.jsonl"

GREY = "grey"            # his companion (core/cat.py)
TOM = "tom"              # the black cat / the tom (cat.py's distant cat today; J-2470's life row later)

# Features only ONE of them has — what it means to distinguish them. Hers: the LOOK line in cat.py ("a thin grey
# cat, one ear notched, watchful green eyes"), possession (the tom is never his), smallness. His: black, big,
# scarred, the milky eye, a tom, the neighbour's, and the pointing words the old distant-look guard already
# honours ("the other/black/distant/far/second/strange cat", cat.look_line). A hyphen ends a word (J-0823).
_W = r"(?<![a-z-])(?:%s)(?![a-z-])"
_GREY_RE = re.compile(_W % "|".join((
    r"my (?:own )?(?:little |small |thin |grey |gray )?(?:cat|kitten|companion|stray|moggy)",
    r"(?:the |this |that )?(?:little|small|thin|young) (?:grey |gray )?(?:cat|one|kitten|stray|moggy)",
    r"(?:the |this |that |your |his )?(?:grey|gray) (?:one|cat|kitten|stray|moggy|companion|girl|thing)",
    r"notched ear", r"the notched one", r"green[- ]eyed", r"green eyes",
    r"(?:my|your) companion", r"(?:the |my )?companion cat", r"the cat (?:on|in) (?:my|your) lap",
    r"the kitten",
)), re.IGNORECASE)
_TOM_RE = re.compile(_W % "|".join((
    r"(?:the |this |that |a |an |old |big |great |scarred |one-eyed |neighbou?r'?s )+tom", r"tomcat",
    r"(?:the |this |that |a )?black (?:cat|one|tom|shape|moggy|stray|kitten)",
    r"(?:the |this |that )?(?:other|distant|far|far-off|second|strange|stranger|foreign|visiting|wild) (?:cat|one|tom)",
    r"(?:the |this |that )?(?:big|large|great|old|scarred|one-eyed|milky-eyed) (?:black |dark )?(?:cat|one|tom)",
    r"milky eye", r"one eye milky", r"(?:the )?neighbou?r'?s cat", r"(?:the )?cat (?:on|along|from) the (?:ridge|far wall|fence line|wall)",
    r"the intruder", r"the invader", r"the stranger cat", r"that cat on",
)), re.IGNORECASE)
_ANY_CAT_RE = re.compile(_W % "|".join((r"cat", r"cats", r"kitten", r"stray", r"moggy", r"puss", r"tomcat")), re.IGNORECASE)


def _name_of_her() -> str:
    try:
        from core import cat as _cat
        return str((_cat.status() or {}).get("name") or "").strip().lower()
    except Exception:
        return ""


def _name_of_tom() -> str:
    """The tom's own name, if he ever gives it one (life_traces individual, J-2470's row). '' until then."""
    try:
        from core import life as _life, life_traces as _lt
        for key, v in (_life._load().get("individuals") or {}).items():
            if _is_cat_row(key) and _lt.individual(key) and v.get("name"):
                return str(v["name"]).strip().lower()
    except Exception:
        pass
    return ""


def _is_cat_row(key: str) -> bool:
    """A life row that is a CAT individual is the other cat (she is never a life individual — she is cat.py's).
    Hook for J-2470: whatever key the tom's row takes ("tom", "black_cat", "tomcat", ...), this reads it."""
    k = str(key or "").lower()
    return "tom" in k.split("_") or "cat" in k.split("_") or k in ("tom", "tomcat", "black_cat", "the_tom")


def classify(text: str, her_name: str | None = None, tom_name: str | None = None) -> str | None:
    """Which cat does this text mean? GREY / TOM when he DISTINGUISHES them; "undistinguished" when it names
    a cat without telling them apart ("the cat", "the stray", bare pronouns are not counted at all); None when
    no cat is meant. Pure (no I/O) when both names are passed; otherwise reads the two names, fail-open."""
    t = " " + str(text or "") + " "
    if not t.strip():
        return None
    her = (her_name if her_name is not None else _name_of_her()) or ""
    tom = (tom_name if tom_name is not None else _name_of_tom()) or ""
    grey_hit = bool(_GREY_RE.search(t)) or (bool(her) and re.search(_W % re.escape(her), t, re.IGNORECASE) is not None)
    tom_hit = bool(_TOM_RE.search(t)) or (bool(tom) and re.search(_W % re.escape(tom), t, re.IGNORECASE) is not None)
    if grey_hit and tom_hit:
        return "both"              # he set them against each other in one breath: distinguished, both named
    if grey_hit:
        return GREY
    if tom_hit:
        return TOM
    if _ANY_CAT_RE.search(t):
        return "undistinguished"
    return None


def distinguished(which: str | None) -> bool:
    return which in (GREY, TOM, "both")


_mem: dict = {"last": {}}        # per-source dedupe: (text) -> ts
_DEDUPE_S = 90.0


def record(source: str, text: str, which: str | None = None, place: str | None = None, now: float | None = None,
           extra: dict | None = None) -> dict | None:
    """Observe-only append: one row per cat-meaning text from one of the readers (census / look / react /
    naming). `which` is classify(text) unless given. No row when the text means no cat at all. Write-fenced
    (profile.guard_path, D-0179) and fail-open: a non-live process gets None, never a raise. Returns the row
    (for tests) or None."""
    try:
        now = time.time() if now is None else float(now)
        if which is None:
            which = classify(text)
        if which is None:
            return None
        key = f"{source}|{str(text or '')[:120]}"
        last = _mem["last"].get(key)
        if last is not None and now - last < _DEDUPE_S:
            return None
        _mem["last"][key] = now
        if len(_mem["last"]) > 400:
            for k in sorted(_mem["last"], key=_mem["last"].get)[:200]:
                _mem["last"].pop(k, None)
        row = {"ts": round(now, 1), "source": str(source), "which": which if distinguished(which) else None,
               "distinguished": distinguished(which), "text": str(text or "")[:120], "place": place}
        if extra:
            row.update({k: v for k, v in extra.items() if k not in row})
        path = profile.guard_path(_LEDGER)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row
    except profile.NonLiveWriteError as exc:
        logger.debug("[cat_referent] refused by the fence (non-live): %s", exc)
        return None
    except Exception as exc:
        logger.debug("[cat_referent] record failed (non-fatal): %s", exc)
        return None


def record_naming(key: str, name: str, now: float | None = None) -> dict | None:
    """Hook for core/life_traces.give_name: a NAMED life individual that is a cat is the other cat, named —
    the strongest distinguishing act there is. Non-cat individuals are ignored. Fail-open."""
    try:
        if not _is_cat_row(key):
            return None
        return record("naming", f"named the {str(key).replace('_', ' ')} {name}", TOM, now=now,
                      extra={"name": str(name), "key": str(key)})
    except Exception:
        return None


def summary(window_s: float = 7 * 86400.0, now: float | None = None) -> dict:
    """For the HUD / the read jobs only: counts per referent in the window and the distinguished share.
    Never reaches a prompt."""
    now = time.time() if now is None else float(now)
    out = {"rows": 0, "grey": 0, "tom": 0, "both": 0, "undistinguished": 0, "share_distinguished": None,
           "by_source": {}}
    try:
        if not _LEDGER.exists():
            return out
        with open(_LEDGER, "rb") as f:
            try:
                if _LEDGER.stat().st_size > 400_000:
                    f.seek(-400_000, 2)
                    f.readline()
            except OSError:
                pass
            for raw in f:
                try:
                    r = json.loads(raw.decode("utf-8", "replace"))
                except Exception:
                    continue
                if not isinstance(r, dict) or now - float(r.get("ts", 0)) > window_s:
                    continue
                out["rows"] += 1
                w = r.get("which")
                if r.get("distinguished"):
                    out[w if w in ("grey", "tom", "both") else "both"] += 1
                else:
                    out["undistinguished"] += 1
                src = str(r.get("source") or "?")
                out["by_source"][src] = out["by_source"].get(src, 0) + 1
        if out["rows"]:
            out["share_distinguished"] = round((out["rows"] - out["undistinguished"]) / out["rows"], 3)
    except Exception as exc:
        logger.debug("[cat_referent] summary failed (non-fatal): %s", exc)
    return out
