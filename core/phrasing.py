"""
Nascence — Phrasing variety (2026-07-07)
========================================
Break the VERBATIM-ECHO LOOP in the nudge surface. Du's idle-monologue seed is assembled from ~50 fixed frame
strings, and (with the sole exception of the guidance read-back) each one fires with IDENTICAL wording every
time it fires. The 2026-07-02 injection-solidity finding (see core/guidance_learning._phrase) is that an
identical re-presented string is twice harmful: (a) a verbatim-echo loop — Du parrots the frame's own words
back as if they were his thought; (b) an illusory-truth subsidy — mere repetition raises credence and blocks
habituation, so the nudge stops landing as anything but wallpaper. The cure the guidance path already uses is a
paraphrase pool selected fresh each time; this module generalises that one pattern into a shared primitive for
every fixed frame.

CONTRACT for a variant pool:
  • preserve MEANING — the pool is paraphrase/stance variation of ONE nudge, not different nudges;
  • preserve MECHANICAL TOKENS verbatim — routing keys the downstream parser reads (e.g. "OPEN THE BOOK",
    "read it again") must appear unchanged in every variant, or the nudge silently stops working;
  • vary wording AND, where it helps, STANCE (an invitation / a bare naming / a question) — richer than
    synonym-swapping, and it is the stance-scaffold ("you may take it up, or let it go") he echoes most.

Selection avoids the immediately-previous pick per key, so the same words never land twice in a row — the
strongest echo risk. Last-pick memory is in-process only (a dict); it resets on restart, which is fine — the
goal is local de-repetition, not a global schedule. Fail-open to the first variant on any error.
"""
from __future__ import annotations

import collections
import random
import time

_last: dict[str, int] = {}   # key -> index of the variant served last time (per process; reset on restart)


# prompt_manager P0 (D-0771, plan docs/staged/prompt_manager.md): OBSERVE-ONLY record of which variant each pool served,
# so a stored thought can be tied to the wording it was prompted with. `random` is consumed exactly as before; this
# only appends (ts, key, index, n_variants) to a bounded in-process ring that core.prompt_budget drains once per idle
# assembly. Picks are attributed to the NEXT assembly by time window, not by call (other threads may call vary()).
_picks: "collections.deque" = collections.deque(maxlen=200)


def _note(key: str, idx: int, n: int) -> None:
    try:
        _picks.append((round(time.time(), 1), key, idx, n))
    except Exception:
        pass


def drain_picks() -> list:
    """Return and clear the picks recorded since the last drain. Never raises."""
    out: list = []
    try:
        while _picks:
            out.append(_picks.popleft())
    except Exception:
        pass
    return out


# D-0787 option B (J-4153): an optional per-key COOLDOWN. cooldown=1 (the default) is the original rule, byte for
# byte the same draw: only the immediately-previous pick is barred. cooldown=k bars the last min(k, n-1) picks for
# the key, so a pool of n variants cycles through at least k distinct wordings before any one returns. Per process,
# like _last; reset on restart.
_hist: dict[str, "collections.deque"] = {}
_HIST_MAX = 16


def vary(key: str, variants: list[str], cooldown: int = 1) -> str:
    """Return one variant for `key`, never the one served last time for this key (breaks the verbatim-echo
    loop that identical re-presentation creates). Variants may carry {named} slots — the CALLER formats after,
    so slot values can contain anything (braces in the value are safe; only the template is a format string).
    `cooldown` > 1 (D-0787 B) also bars the picks before that, up to n-1 of them. Fail-open to variants[0]."""
    try:
        if not variants:
            return ""
        if len(variants) == 1:
            _note(key, 0, 1)
            return variants[0]
        prev = _last.get(key, -1)
        if cooldown and cooldown > 1:
            recent = list(_hist.get(key, ()))
            barred = set(recent[-min(int(cooldown), len(variants) - 1):]) if recent else set()
            barred.add(prev)
            choices = [i for i in range(len(variants)) if i not in barred] or \
                      [i for i in range(len(variants)) if i != prev]
        else:
            choices = [i for i in range(len(variants)) if i != prev]
        idx = random.choice(choices)
        _last[key] = idx
        try:
            _hist.setdefault(key, collections.deque(maxlen=_HIST_MAX)).append(idx)
        except Exception:
            pass
        _note(key, idx, len(variants))
        return variants[idx]
    except Exception:
        return variants[0] if variants else ""
