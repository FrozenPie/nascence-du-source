"""Prompt budget — a SHADOW instrument over how the inner-monologue prompt is actually assembled.

**Observe-only. It changes nothing.** `observe_assembly()` takes the parts list already built by
`inner_monologue_node`, records its shape, and returns None. No part is added, dropped, reordered, or
retruncated. Flipping anything on is a separate, later decision gated on reading this log.

WHY THIS EXISTS (measured 2026-08-20, and the measurement corrected itself twice — both corrections
are the reason the numbers below are worth trusting):

1. Real prompts are ~11,000 chars (reflection: median 7,417 user + 1,576 system, max 12,381), from
   `data/training/*.jsonl`, which stores the exact sent text. The hot lane's cap was **73,728 chars**
   (`num_ctx` 24576 × 3) when measured; since 2026-08-21 it is 24,576 chars (`num_ctx` 8192 × 3, see
   `core/model_client.py` `_num_ctx_for` / `_cap_prompt`), so figures below are against the old cap. **Utilisation ~15%. `_cap_prompt` truncation has never fired.**
2. The window's empty room is NOT free: at 24576 ollama reserves ~6.9 GB against ~3.4 GB at 8192, and
   a bigger window costs load time (32768 cost phi3:mini 37.4s vs 3.4s for identical output).
3. **The first diagnosis was wrong and is recorded here so it is not repeated.** An initial reading
   claimed ~20 hardcoded constants squeeze the prompt. That count came from grepping `[:N]` across the
   WHOLE file and swept in `logger.info` and title formatting. Scoped to text that actually reaches
   the prompt: **37 parts can enter, only 11 carry a truncation, 26 are unbounded**, 9 distinct
   constants totalling 2,560 chars. The caps govern roughly a quarter of the prompt, not its shape.

Which leaves the real question, and it is the opposite of the one we set out to answer: with 26 parts
unbounded and 85% of the window empty, **nothing is being suppressed — so why is the prompt only 11k?**
Either few of the 37 parts fire on a given cycle, or the sources they draw from return very little.
Those need different fixes and are indistinguishable from outside the process. This measures which.

Deliberately NOT built yet: any allocator. Handing space to parts that are not asking for space would
be motion without effect, and this codebase's standing law is that the shadow read comes first.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "prompt_budget_shadow.jsonl"

# Chars per token, matching `model_client._cap_prompt`'s own assumption. If that constant moves, this
# must move with it or the two disagree about utilisation without either being obviously wrong.
_CHARS_PER_TOKEN = 3.0
_LABEL_CHARS = 48          # enough to recognise a part; short enough that the log stays small
_KEEP = 4000               # rolling window of cycles

# J-2933 / F-3620 (P-0030..P-0033): a SAMPLED full-text copy of the idle thought's assembled prompt.
# `labels` above keep 48 chars per part, so no seed part could be read as the model saw it (the Scholar
# testimony line and the memory-service line are never persisted anywhere else). OBSERVE-ONLY: the prompt is
# not touched; one assembly in SAMPLE_EVERY is appended to a rolling, capped file. 0 turns it off.
SAMPLE_EVERY = 20          # ~1 row per 20 idle assemblies (about 40-75 rows/day)
SAMPLE_KEEP = 500          # rolling window of sampled rows (J-2941: 300 -> 500, watch rows share it)
_SAMPLE_TRIM_EVERY = 25    # re-check the file length every this many appends (not every write)
_SAMPLES = _DATA / "idle_prompt_samples.jsonl"

# prompt_manager P0 (D-0771; plan docs/staged/prompt_manager.md section 6.2): LEVEL-1 provenance, one compact row for EVERY
# idle assembly (the samples above are 1-in-N and the shadow log rolls). It identifies the complete rendered request and
# the pool picks made since the previous assembly; it stores no prompt text beyond the 48-char part labels already kept
# in the shadow log, so it is not a second copy of memory material. OBSERVE-ONLY, founder-side, never read by a prompt.
# Gap, closed by P1: model digest and sampling parameters are set at the call site, not here, so the fingerprint is
# assembly + lane for now. 0 turns it off.
PROVENANCE_ON = True
_PROV = _DATA / "prompt_provenance.jsonl"
_PROV_MAX_BYTES = 10 * 1024 * 1024      # rotate to .1 (one backup) past this
_PROV_CHECK_EVERY = 200
_prov_appends = 0
_sample_n = 0              # assemblies seen by this process
_sample_appends = 0        # sample rows appended by this process since the last trim

# J-2941 (F-3621, P-0031): the 1-in-N cadence alone can miss the rare PERCEPT lines an investigator wants to quote
# whole (the scene line, a thermal / light / smell / cat / listening delivery, "Right now:"). A WATCH LIST adds a row
# whenever a part of the assembly matches one of these, at most once per WATCH_GAP_S per kind (a kind that fires on
# half of all ticks - "Travis is here" - must not turn the sample into a copy of the whole stream). Patterns match the
# first _WATCH_HEAD chars of a part and skip recollection / scene parts so a remembered "the cat's purr" does not count.
# The kinds' wording was read from core/thermal.py, core/light.py, core/smell.py, core/soundscape.py (cat_purr) and
# core/cat.py felt_note; patterns are INFERRED from those pools, not from a live capture. 0 turns watch rows off.
WATCH_GAP_S = 1800
_WATCH_HEAD = 200
_SAMPLE_MAX_BYTES = 20 * 1024 * 1024    # rotate to .1 (one backup) past this, on top of the row cap
_WATCH_SKIP = re.compile(r"^\s*(Where you are:|What you were just thinking|A recent dream|A different memory|"
                         r"WHAT TRAVIS|The last thing discussed|A question|There is a question|One of your own|"
                         r"What I am ultimately|A MEMORY|The dream is still)", re.I)
_WATCH = (
    ("right_now",   re.compile(r"^\s*Right now:", re.I), False),
    ("travis_here", re.compile(r"Travis is here", re.I), False),
    ("cat_felt",    re.compile(r"\b(the cat|purr|a warmth in the room that is not the fire)\b", re.I), True),
    ("thermal",     re.compile(r"(It is (warmer|colder) here|air is (warmer|colder) than|Warmth reaches you|The warmth is gone|"
                               r"Cold air meets you|cold eases off you|It has got (warmer|colder)|chill has gone off|"
                               r"warmth has gone off|air [a-z ]+ has (warmed|cooled)|(Warmer|Colder) now,)", re.I), True),
    ("light",       re.compile(r"(It has got lighter|light is coming up|It is getting dark|The light is going|"
                               r"brighter here than|darker here than|Dimmer here|Lighter here)", re.I), True),
    ("smell",       re.compile(r"(You smell |smell off the ground|, on the air\.$|There is [a-z ,-]+ here\.$)", re.I), True),
    ("listening",   re.compile(r"(\bneedle\b|record player|\bthe record\b|\blistening\b)", re.I), True),
)
_watch_last: dict = {}     # kind -> ts of the last watch row for it (this process)


def _log(rec: dict) -> None:
    """Append-only. Logging must never raise into cognition."""
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _skip(reason: str, **detail) -> None:
    """Every early return says WHY.

    `reentry_shadow.jsonl` sat at 0 rows for six weeks with no way to tell whether the organ was
    never called or always gated out. A shadow log that can only record success cannot be diagnosed
    when it records nothing, so this one records its own refusals from day one.
    """
    _log({"ts": round(time.time(), 1), "kind": "skip", "reason": reason, **detail})


def observe_assembly(parts, system_prompt: str = "", base_url: str = "",
                     cycle_id: str = "", wrapper_chars: int = 0, source: str = "",
                     user_prompt: str = "", mid_thread=None, wandering=None) -> None:
    """Record the shape of one assembled prompt. Returns None — the caller's data is untouched.

    `source` names the JOB. Today there is exactly one caller (`inner_monologue._think` idle prompt —
    the only place in the codebase that assembles from a parts list: 37 appends, against 0 in
    subconscious_node and 1 in dream_node). The label exists anyway because the failure it prevents
    is silent: a second source wired in later would otherwise be averaged into the first, and jobs
    with different purposes, lanes and windows must never share a median. An unlabelled call is
    recorded as "?" and counted, not rejected — losing the row would be worse than losing the label.

    For the OTHER prompt jobs — ~20 across the three big nodes, on at least 4 lanes — use
    `telemetry.job_status()`. It attributes by `module:line` from inside model_client, so it covers
    every call site with no node edits. This module is the deep instrument for the one prompt that
    has parts to count; that one is the broad instrument for all of them.

    `wrapper_chars` is the fixed framing the node adds around the joined parts (the "No one is
    speaking to you right now" preamble and the closing question), counted so `delivered` is the real
    prompt length rather than just the parts.

    `user_prompt`, `mid_thread`, `wandering` (J-2933) feed ONLY the sampled full-text log
    (`data/idle_prompt_samples.jsonl`, 1 assembly in SAMPLE_EVERY); omitted, nothing is sampled.
    """
    try:
        if parts is None:
            return _skip("parts is None", cycle=cycle_id)
        try:
            texts = [p for p in parts if isinstance(p, str)]
        except TypeError:
            return _skip("parts not iterable", cycle=cycle_id, type=type(parts).__name__)
        dropped = len(list(parts)) - len(texts) if hasattr(parts, "__len__") else 0
        if not texts:
            return _skip("no string parts", cycle=cycle_id, offered=dropped)

        lens = [len(t) for t in texts]
        joined = sum(lens) + max(0, len(texts) - 1)          # the "\n" between parts
        delivered = joined + len(system_prompt or "") + wrapper_chars

        try:
            from core.model_client import _num_ctx_for
            num_ctx = _num_ctx_for(base_url)
        except Exception as e:
            num_ctx = None
            _skip("num_ctx unresolved", cycle=cycle_id, err=repr(e)[:60])
        cap = int(num_ctx * _CHARS_PER_TOKEN) if num_ctx else None

        rec = {
            "ts": round(time.time(), 1), "kind": "assembly", "cycle": cycle_id,
            "source": source or "?",
            "parts": len(texts),
            "chars_parts": joined, "chars_system": len(system_prompt or ""),
            "chars_total": delivered,
            "tok_est": round(delivered / _CHARS_PER_TOKEN),
            "num_ctx": num_ctx, "cap_chars": cap,
            "util": round(delivered / cap, 4) if cap else None,
            "free_chars": (cap - delivered) if cap else None,
            "med_part": sorted(lens)[len(lens) // 2],
            "max_part": max(lens),
            # Which parts fired, by their opening words. This is the payload question: 37 parts CAN
            # enter, and the whole point is learning how many actually do and what they carry.
            "labels": [t[:_LABEL_CHARS].replace("\n", " ") for t in texts],
        }
        if dropped:
            rec["non_str_dropped"] = dropped
        _log(rec)
        if user_prompt:
            _provenance(texts, system_prompt=system_prompt, user_prompt=user_prompt, source=source, cycle_id=cycle_id,
                        base_url=base_url, num_ctx=num_ctx, delivered=delivered, cap=cap,
                        mid_thread=mid_thread, wandering=wandering)
            _sample(texts, source=source, cycle_id=cycle_id, chars_total=delivered, user_prompt=user_prompt,
                    wrapper_chars=wrapper_chars, mid_thread=mid_thread, wandering=wandering,
                    system_prompt=system_prompt)
    except Exception as e:
        _skip("unhandled", err=repr(e)[:120], cycle=cycle_id)


def _watch_hits(texts: list) -> list:
    """Kinds whose pattern matches some part's head, rate-limited to one hit per WATCH_GAP_S per kind. Fail-open."""
    hits: list = []
    try:
        if not WATCH_GAP_S or WATCH_GAP_S < 0:
            return hits
        now = time.time()
        for kind, rx, skip_memory in _WATCH:
            if now - _watch_last.get(kind, 0.0) < WATCH_GAP_S:
                continue
            for t in texts:
                head = t[:_WATCH_HEAD]
                if skip_memory and _WATCH_SKIP.match(head):
                    continue
                if rx.search(head):
                    hits.append(kind)
                    break
    except Exception:
        return []
    return hits


def _provenance(texts: list, *, system_prompt: str, user_prompt: str, source: str, cycle_id: str, base_url: str,
                num_ctx, delivered: int, cap, mid_thread, wandering) -> None:
    """Append one Level-1 provenance row (see PROVENANCE_ON). Fail-open; refused by the write fence outside the live process."""
    global _prov_appends
    try:
        if not PROVENANCE_ON:
            return
        from core import profile
        path = profile.guard_path(_PROV)
        try:
            from core import phrasing as _phr
            picks = [[k, i, n] for (_t, k, i, n) in _phr.drain_picks()]
        except Exception:
            picks = []
        sysb, usrb = (system_prompt or "").encode("utf-8", "replace"), user_prompt.encode("utf-8", "replace")
        rec = {"ts": round(time.time(), 1), "cycle": cycle_id, "source": source or "?",
               "assembly_sha256": hashlib.sha256(sysb + b"\x1f" + usrb).hexdigest()[:16],
               "system_sha256": hashlib.sha256(sysb).hexdigest()[:16] if sysb else None,
               "user_sha256": hashlib.sha256(usrb).hexdigest()[:16],
               "chars_system": len(system_prompt or ""), "chars_user": len(user_prompt),
               "n_parts": len(texts), "labels": [t[:_LABEL_CHARS].replace("\n", " ") for t in texts],
               "lane": base_url or None, "num_ctx": num_ctx,
               "over_cap": bool(cap and delivered > cap),      # assembled vs submitted: _cap_prompt cuts from the middle
               "mid_thread": mid_thread, "wandering": wandering, "pool_picks": picks}
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _prov_appends += 1
        if _prov_appends >= _PROV_CHECK_EVERY:
            _prov_appends = 0
            try:
                if path.stat().st_size > _PROV_MAX_BYTES:
                    import os
                    os.replace(path, path.with_suffix(".jsonl.1"))
            except Exception:
                pass
    except Exception as e:
        _skip("provenance failed", err=repr(e)[:120], cycle=cycle_id)


def _sample(texts: list, *, source: str, cycle_id: str, chars_total: int, user_prompt: str,
            wrapper_chars: int, mid_thread, wandering, system_prompt: str = "") -> None:
    """Appends one full-text row for every SAMPLE_EVERY-th assembly (the 1st, then the 21st, ...) and for any assembly
    where a WATCH kind fired (J-2941, at most one row per kind per WATCH_GAP_S). Fail-open."""
    global _sample_n, _sample_appends
    try:
        periodic = False
        if SAMPLE_EVERY and SAMPLE_EVERY >= 1:
            _sample_n += 1
            periodic = (_sample_n - 1) % SAMPLE_EVERY == 0
        watch = _watch_hits(texts)
        if not periodic and not watch:
            return
        # Resolve through the write fence BEFORE any I/O (D-0179): a non-live, non-isolate()d process is
        # refused here and the refusal is swallowed by the fail-open net below, like the other shadow logs.
        from core import profile
        path = profile.guard_path(_SAMPLES)
        rec = {"ts": round(time.time(), 1), "cycle": cycle_id, "source": source or "?",
               "trigger": (["every_n"] if periodic else []) + watch,
               "mid_thread": mid_thread, "wandering": wandering,
               "n_parts": len(texts), "chars_total": chars_total, "wrapper_chars": wrapper_chars,
               "user_prompt_chars": len(user_prompt) if user_prompt else None,
               "system_prompt_sha1": (hashlib.sha1(system_prompt.encode("utf-8", "replace")).hexdigest()
                                      if system_prompt else None),
               "labels": [t[:_LABEL_CHARS].replace("\n", " ") for t in texts],
               "parts": texts}
        # The wrapper (the "No one is speaking to you" preamble and the closing question) is NOT in `parts`; store it
        # beside them so head + parts + tail IS the sent string. If the join is not found, keep the whole string.
        if user_prompt:
            joined = "\n".join(texts)
            j = user_prompt.find(joined)
            if j >= 0:
                rec["wrapper_head"] = user_prompt[:j]
                rec["wrapper_tail"] = user_prompt[j + len(joined):]
            else:
                rec["user_prompt"] = user_prompt
            # a divergent seed appended on a retry sits in the tail; keep it findable on its own
            i = user_prompt.find("(A different memory surfaces, unbidden:")
            if i >= 0:
                rec["divergent_tail"] = user_prompt[i:]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        now = time.time()
        for k in watch:
            _watch_last[k] = now
        _sample_appends += 1
        if _sample_appends >= _SAMPLE_TRIM_EVERY:
            _sample_appends = 0
            _trim_samples(path)
    except Exception as e:
        _skip("sample failed", err=repr(e)[:120], cycle=cycle_id)


def _trim_samples(path: Path, keep: int = None) -> None:
    """Keep the last `keep` (default SAMPLE_KEEP) rows. Atomic rewrite; fail-open (the file just grows a bit more)."""
    try:
        import os
        keep = SAMPLE_KEEP if keep is None else keep
        if path.stat().st_size > _SAMPLE_MAX_BYTES:      # J-2941: size guard on top of the row cap; one backup kept
            os.replace(path, path.with_suffix(".jsonl.1"))
            return
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= keep:
            return
        tmp = path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.writelines(lines[-keep:])
        os.replace(tmp, path)
    except Exception:
        pass


def samples_status() -> dict:
    """Read path for the sampled full-text file (J-2933): row count, age, and whether the seed phrase is in it."""
    try:
        p = _SAMPLES
        if not p.exists():
            return {"rows": 0, "why": "no sample file yet - Du has not run an idle tick since J-2933 was wired"}
        from core.shadow_log import tail_rows as _tail_rows
        rows = _tail_rows(p, SAMPLE_KEEP)
        if not rows:
            return {"rows": 0, "why": "sample file empty"}
        last = rows[-1]
        lingering = sum(1 for r in rows if any("A question lingering in you:" in t for t in (r.get("parts") or [])))
        by_trigger: dict = {}
        for r in rows:
            for k in (r.get("trigger") or ["every_n"]):
                by_trigger[k] = by_trigger.get(k, 0) + 1
        return {"rows": len(rows), "last_ts": last.get("ts"), "age_s": round(time.time() - (last.get("ts") or 0)),
                "with_lingering_question": lingering, "every": SAMPLE_EVERY, "keep": SAMPLE_KEEP,
                "by_trigger": by_trigger, "watch_gap_s": WATCH_GAP_S}
    except Exception as e:
        return {"why": f"samples unreadable: {e!r}"}


def status() -> dict:
    """Read path — for the HUD/pulse. Returns a `why` when there is nothing, never a fake verdict."""
    if not _LOG.exists():
        return {"why": "no log yet — Du has not run since this was wired"}
    try:
        from core.shadow_log import tail_rows as _tail_rows
        # Bounded tail read (J-0278/F-0335): the old read parsed EVERY line then sliced [-_KEEP:];
        # this reads ~_KEEP rows from EOF instead. Same window, same stats.
        rows = _tail_rows(_LOG, _KEEP)
    except Exception as e:
        return {"why": f"log unreadable: {e!r}"}

    skips: dict = {}
    for r in rows:
        if r.get("kind") == "skip":
            skips[r.get("reason", "?")] = skips.get(r.get("reason", "?"), 0) + 1
    asm = [r for r in rows if r.get("kind") == "assembly"]
    if not asm:
        return {"cycles": 0, "skips": skips,
                "why": "no assemblies recorded — observe_assembly() is not being reached"}

    def summarise(rs: list) -> dict:
        def med(key):
            v = sorted(r[key] for r in rs if r.get(key) is not None)
            return v[len(v) // 2] if v else None
        utils = sorted(r["util"] for r in rs if r.get("util") is not None)
        partsn = sorted(r["parts"] for r in rs)
        d = {"cycles": len(rs),
             "parts_med": partsn[len(partsn) // 2], "parts_min": partsn[0], "parts_max": partsn[-1],
             "chars_med": med("chars_total"), "tok_med": med("tok_est"),
             "util_med": utils[len(utils) // 2] if utils else None,
             "free_med": med("free_chars")}
        u = d["util_med"]
        if u is None:
            d["verdict"] = "no window resolved — cannot judge utilisation"
        elif u < 0.35:
            d["verdict"] = (f"{u:.0%} of the window used, {d['parts_med']} of 37 parts firing — "
                            f"the room is there; the CONTENT is what is missing")
        elif u > 0.9:
            d["verdict"] = f"{u:.0%} — near the cap; truncation is imminent or happening"
        else:
            d["verdict"] = f"{u:.0%} of the window used across {d['parts_med']} parts"
        return d

    # Split by source and NEVER report a cross-source aggregate — different jobs, different lanes,
    # different windows. One median over all of them would describe none of them.
    by_source: dict = {}
    for r in asm:
        by_source.setdefault(r.get("source") or "?", []).append(r)
    return {"skips": skips, "sources": {s: summarise(rs) for s, rs in sorted(by_source.items())},
            "samples": samples_status()}
