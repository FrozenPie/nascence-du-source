"""
Nascence — the Judge Panel (2026-08-15, the serving split's payoff).

Until today every judge in the system was one llama3.1:8b — a single family ruling on everything,
which is itself a quiet monoculture of judgment. The CPU tier (nascence_cpu_server.py instances)
makes a PANEL affordable: two families rule independently; agreement is a verdict; disagreement
escalates to the TIEBREAK hub (today granite3.1-moe:3b on Ramses :11437 -- the 2026-08-20 yi:34b
night-judge wording this header used to carry is long gone; see the REPOINT history above TIEBREAK;
a caller can override it per call with the `tiebreak_url` parameter of rule()/rule_detail()), else NO
VERDICT (conservative — the resolution-judge law: no judge, no verdict). Every ruling is logged with
both votes — the panel is an instrument as well as a gate.

Used by (rule()/rule_detail() callers in core/ and nodes/, read 2026-11-05, J-2954): evidence_recall,
follow_line (3 keys), guidance_behavior_judge, lane2 (several keys), pursuits (judge_pending),
pursuit_close_shadow, self_interrogation, social_cognition_shadow, tension_ledger
(_judge_resolution), nodes/dream_node, nodes/subconscious_node. peers.py only imports the JUDGE_1 /
TIEBREAK constants and calls its own hubs; scripts/ labs also import this module. This list drifts as
callers are added -- docs/prompt_registry.jsonl (the `prompt-registry` skill) is the maintained list.
CAVEAT (F-1949, F-2063, F-3639): the shared TIEBREAK is measured UNFIT on some keys -- near-constant
per-key answers instead of reading the case (F-3639: "resolves" and "held" ~0% true, "genuine"/"bears"
~95-100% true; F-2063: lane2 "metaphor" 53% accurate). A caller should check that its own key behaves
before relying on a tiebreak-decided verdict; rule_detail()'s `tiebreak_url` docstring has the detail.
D-0530 (2026-11-06, J-3136): on the keys in GRANITE_CONSTANT_TIEBREAK_KEYS a v1/v2 split no longer consults
the granite TIEBREAK at all -- it returns how="split_no_tiebreak", verdict None (see that constant).
STALE NOTE CORRECTED 2026-08-29 (J-0362 audit): the line below claiming "left_lane's T4 solidify judge
stays single-family for now" stopped being true 2026-08-19 — left_lane.py's judge_lived_integration
shipped its OWN separate two-judge decoupled fix that day (llama3.1:8b + qwen2.5:7b, both required to
agree; see left_lane.py:360-470's "the decoupled SOLIDIFY judge for T4" section). It does not reuse
THIS module's panel machinery (own prompt/models), so it is not "used by" this file in the literal
sense above, but the single-family caveat is no longer accurate anywhere in the codebase.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from core import telemetry as _tel_lat   # J-3761: raw-HTTP latency rows

logger = logging.getLogger("nascence.judge_panel")

_DATA = Path(__file__).parent.parent / "data"
_LOG = _DATA / "judge_panel_log.jsonl"

# REPOINTED 2026-09-02 (D-0121, founder-ruled): 127.0.0.1:11439 -> RAMSES :11438. The local gemma4:12b
# hub was never brought online this session (F-0657 — left_lane.py's grounding call to the same dark
# hub was spamming fail-open logs at INFO every cycle; downgraded to debug, but the panel itself was
# also silently losing every vote to that hub). Reuses the already-resident mixtral:8x7b hub (Ramses
# CPU/i9) instead of starting a new one — same "reuse resident capacity" logic as TIEBREAK's own moves
# below. Family decoupling holds: mixtral (Mistral) vs falcon3 (TII) vs granite tiebreak (IBM) — three
# distinct families. KNOWN TRADEOFF, watch it (D-0121's own defeater): :11438 already serves the
# commitment-defeater judge (core/commitment_ledger.py) and dream-primary generation
# (nodes/dream_node.py) through nascence_cpu_server.py's one-request-per-hub lock — exactly the kind
# of hub-sharing that caused F-0381's contention spiral for the old tiebreak. If judge_panel_log.jsonl
# or llm_latency.jsonl shows queued/slow/timed-out :11438 calls after this move, revisit (give Judge1
# its own hub instead, e.g. a fresh small one on the 1650 Super).
JUDGE_1 = "http://LAN-HOST:11438"    # mixtral:8x7b, Ramses CPU/i9 (was local gemma4:12b :11439, dark)
JUDGE_2 = "http://127.0.0.1:11440"     # falcon3:7b (re-seated 2026-08-21; hub-mistral failed key contracts — see launch_servers.ps1)
# SHARED-HUB WARNING (doc-only note, 2026-09-19, J-1141 from F-1547/J-1127, decide:D-0207; CORRECTED
# 2026-11-05, J-3365 after D-0654/J-3263): until 2026-11-05 this JUDGE_2 URL (:11440) was the LITERAL SAME
# hub as core/peers.py's _HUB_JUDGE2, which composed marcus's and smith's letters, so rule()/rule_detail()
# used wholesale on either persona's output had one of the two "independent" votes be the writer's own
# model. That is NO LONGER TRUE: D-0654 (founder, 2026-11-02; J-3263, commit ff38efab) re-seated marcus
# and smith on gemma4:12b at :11439 (core/peers.py _HUB_LLAMA), and :11440 falcon3:7b now hosts NO
# persona (peers.py keeps _HUB_JUDGE2 only as the name of that hub). So JUDGE_2 is a different family
# from every persona's writer hub, and rule()/rule_detail() are usable on marcus's and smith's letters:
# JUDGE_1 (mixtral:8x7b, Ramses :11438), JUDGE_2 (falcon3:7b) and TIEBREAK (granite, Ramses :11437) are
# all other families than gemma4:12b. THE NEW TRAP, if any: do not use a gemma4:12b hub (:11439, which
# also composes twain's and shackleton's letters) as a judge of marcus's, smith's, twain's or
# shackleton's text, and do not re-seat a persona on whatever hub a panel member uses without redoing
# this check. Nothing about this module's routing changes because of this note. See core/peers.py's
# `_stance_compliance_judge` (J-1127) for the precedent: it routes around JUDGE_2 by calling JUDGE_1 +
# TIEBREAK directly, which still holds and is NOT re-pointed.
# TIEBREAK — 2026-08-20: REPOINTED 11441 -> 11442. Diagnosis: :11441 (the dedicated night-judge hub) is
# NOT started by the launcher and was never resident, so EVERY split escalation silently failed. Measured
# over 14 days of real rulings: 363 `split_no_tiebreak` vs 361 `agreed` — **half of every judged decision
# in the system was being dropped**, not just self-interrogation's (the drops span pursuits `advances` 459,
# tension `resolves` 192, evidence `bears` 54, self-interrogation `genuine` 14).
# Why :11442 and not "start 11441": the founder's standing capacity ruling (DEFERRED_PLANS #5, verbatim
# "3 at a time was tried and was too much") rules out a THIRD resident CPU-tier model. :11442 is ALREADY
# running yi:34b-v1.5 for dreams/letters — the exact model :11441 wanted — so this reuses resident capacity
# and starts nothing new. Verified before switching (this codebase has been burned by a hub that listed a
# model it could not actually serve): a real strict-JSON judge call returned `{"advances": true}` in 5.3s.
# Family decoupling is preserved — gemma4:12b / falcon3 / yi are three distinct families, and all
# differ from the hot-lane generator (qwen3.5:9b since the 2026-08-20 full shuffle).
# KNOWN TRADEOFF, watch it: :11442 is the lazy-loading dreamer hub, and the pursuits judge sweep runs in
# the SAME sleep batch as dreams — so tiebreaks and dream generation can contend at sleep. Traffic is light
# (~26 splits/day) and llama.cpp serialises, so the expected cost is slower sleep batches, not failure.
# REVERT: this one line back to :11441 (and start that hub) if contention proves worse than the drops.
# REPOINTED AGAIN 2026-08-27 (D-0044, ramses_second_tier §5 move 3, founder-approved): 11442 -> RAMSES
# :11441 (command-r7b on the 3070 — note: a DIFFERENT :11441 than the local hub the 08-20 note above
# retired; the "3 resident local CPU models is too much" capacity ruling doesn't bind a Ramses GPU hub).
# Why: the 08-20 tradeoff note above came true — tiebreaks shared the dreamer's 184s/16.3%-fail CPU hub
# (F-0381), exactly where D-0039's false-unavailable spiral lived. command-r7b is also a genuine third
# family (Cohere) vs gemma/falcon. Auditioned this session with the real boolean+why JSON contract: held,
# 10.2s, correct refusal on a known non-advance. The dreamer keeps :11442 as ITS failover only.
# REPOINTED AGAIN 2026-08-28 (founder: "ollama llms gone from Ramses"): 11441 -> :11437 (granite3.1-moe
# on the 1650 Super). The 08-27 placement lasted ONE night: command-r7b shared the 3070 with Ramses
# ollama's phi3+deepseek residents and the card locked (F-0389 — dreams 210/300/300s, phi3 121s, ok:0).
# The 3070 now belongs to phi3's llama.cpp hub alone; :11441 is retired to manual-only. granite was
# §5.2's own named third-family alternative (IBM vs gemma/falcon — decoupled-judge holds). Auditioned
# this session with the real boolean+why contract: correct refusal on a known non-advance (4.3s) AND
# correct accept on a known advance (1.0s), coherent why strings both ways.
TIEBREAK = "http://LAN-HOST:11437"   # granite3.1-moe:3b (Ramses 1650 Super, dedicated hub)
# D-0530 (travis, 2026-11-02; J-3136, built 2026-11-06): keys where the GRANITE tiebreak is a CONSTANT, so a split
# on them returns NO VERDICT (how="split_no_tiebreak", verdict None -- the panel's own conservative law: no judge,
# no verdict) instead of asking TIEBREAK. "Constant" was defined at BUILD TIME from data/judge_panel_log.jsonl as:
# at least 50 granite tiebreak rulings since 2026-08-28 AND granite's true-rate <= 0.05 or >= 0.95. Measured
# 2026-11-06 (log through 2026-11-05 19:10, granite-hub rows only, lane2's gemma4 :11439 override rows excluded):
#   resolves n=599 true=0.000 | held n=642 true=0.002 | bears n=822 true=0.953 | genuine n=143 true=0.993 |
#   taken_up n=56 true=0.982. NOT constant, keep the tiebreak: coherent n=1908 0.407, advances n=969 0.460,
#   cuts n=235 0.813, supported n=99 0.919, aligns n=79 0.468 (follows 0.979 and tracks 1.000 have n<50).
# A reviewable constant, NOT computed at runtime: re-derive with scripts/_test_J3136_constant_tiebreak.py's
# measure() and edit this list by hand. It applies ONLY when the tiebreak is the shared granite TIEBREAK (a
# caller passing its own tiebreak_url, i.e. lane2's gemma4 override for held/contradicted/metaphor, is untouched:
# that hub is not granite, and measured 0.814 / 0.158 / 0.226 true on those keys -- none constant).
# Defeater (D-0530): revisit if a per-key tiebreak accuracy table shows granite beats chance on a listed key, a
# stronger different-family tiebreak is seated, or the no-verdict rate starves a live caller.
GRANITE_CONSTANT_TIEBREAK_KEYS = frozenset({"resolves", "held", "bears", "genuine", "taken_up"})
# Revert switch for the D-0530 rule (True = the rule is on, as ruled). Set False to restore the old behaviour
# (every split on every key consults TIEBREAK) without touching the key list.
SKIP_CONSTANT_TIEBREAK = True
# D-0696 (travis, 2026-11-08; J-3802): the option-ORDER counterbalance, built as a SHADOW arm and DEFAULT OFF.
# Every two-option boolean judge prompt lists true first and rule_detail() sends the identical system text to both
# families, so an option-order effect would be common-mode and invisible to the panel's own agreement rate (F-4311).
# With this flag True, each ruling ALSO asks JUDGE_2 the same question with the listed option order REVERSED
# (concurrently with the live pair, so no added wall-clock) and logs that vote beside the live ones as
# v2_rev/why2_rev/err2_rev/s2_rev/order_first. It changes NO verdict, NO `how`, and no key of the return dict.
# Promotion to a live counterbalance is a SEPARATE founder ruling, decided by the order-control replays
# (J-3694, J-3696). Restart-gated (this module does not hot-reload). Costs one extra JUDGE_2 call per ruling on
# a key whose prompt has a recognisable two-option form, and JUDGE_2's hub serialises requests, so turn it on
# deliberately. JUDGE_ORDER_SHADOW_KEYS narrows it to named keys (None = every key).
JUDGE_ORDER_SHADOW_ON = False
JUDGE_ORDER_SHADOW_KEYS: "frozenset | None" = None

# J-3695 (from F-4311): judge INPUT capture. judge_panel_log.jsonl keeps key/votes/context but never the user text the
# judges saw, so the J-3410 R1 order-control replays could not run on real cases for most stations. With this flag on,
# 1 ruling in JUDGE_INPUT_SAMPLE_EVERY (plus EVERY ruling whose two families split) is also written to a NEW file,
# data/judge_inputs_log.jsonl: key, context, user text capped at JUDGE_INPUT_USER_CAP chars, and a hash + length of the
# system text. It changes NO verdict, NO `how`, no key of the return dict and no field of the existing log row; a write
# failure is swallowed. READER: scripts/lab_j3410_order_replay.py (build_cases, captured-inputs source). Restart-gated.
JUDGE_INPUT_CAPTURE_ON = True
JUDGE_INPUT_SAMPLE_EVERY = 10
JUDGE_INPUT_USER_CAP = 1200
_INPUTS_LOG = _DATA / "judge_inputs_log.jsonl"
_input_seq = 0


def _capture_inputs(system, user, key, context, v1, v2, verdict, how, cycle_id=""):
    """Append one input-capture row when this ruling is sampled or split. Never raises, never affects a verdict."""
    global _input_seq
    try:
        if not JUDGE_INPUT_CAPTURE_ON:
            return False
        _input_seq += 1
        split = v1 is not None and v2 is not None and v1 != v2
        if not split and _input_seq % max(1, int(JUDGE_INPUT_SAMPLE_EVERY)) != 0:
            return False
        import hashlib
        sysd = system if isinstance(system, str) else str(system)
        row = {"ts": round(time.time(), 1), "key": key, "context": (context or "")[:80],
               "user": (user if isinstance(user, str) else str(user))[:JUDGE_INPUT_USER_CAP],
               "user_len": len(user) if isinstance(user, str) else None,
               "sys_sha": hashlib.sha1(sysd.encode("utf-8", "replace")).hexdigest()[:16], "sys_len": len(sysd),
               "v1": v1, "v2": v2, "verdict": verdict, "how": how, "split": split}
        if cycle_id:
            row["cycle_id"] = cycle_id
        _DATA.mkdir(parents=True, exist_ok=True)
        with open(_INPUTS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        logger.debug("[judge_panel] input capture failed (non-fatal): %s", exc)
        return False

import re as _re
_OS_PAIR_OF_LITERALS = _re.compile(r'(\{\s*\\?"(?P<k>[A-Za-z_]+)\\?"\s*:\s*)(?P<a>true|false)(\s*\}\s*or\s*)(\{\s*\\?"(?P=k)\\?"\s*:\s*)(?P<b>true|false)(\s*\})')
_OS_PLACEHOLDER = _re.compile(r'\b(true|false)(\s*\|\s*|\s+or\s+)(true|false)\b')
_OS_PREFILLED = _re.compile(r'(\{\s*\\?"(?:[A-Za-z_]+)\\?"\s*:\s*)(true|false)(\s*,)')


def reverse_option_order(system: str) -> str:
    """`system` with the listed order of its two-option boolean schema reversed ('{"k": true} or {"k": false}'
    pair, 'true|false' / 'true or false' placeholder; a single pre-filled '{"k": true,' example flips its
    literal). Unchanged text comes back when no such form is present. Same rules as
    scripts/lab_j3410_order_replay.reverse_order (the J-3694/J-3696 replay instrument), kept here so core/ does
    not import from scripts/. Pure, no I/O."""
    out = _OS_PAIR_OF_LITERALS.sub(lambda m: f'{m.group(1)}{m.group("b")}{m.group(4)}{m.group(5)}{m.group("a")}{m.group(7)}', system)
    if out != system:
        return out
    out = _OS_PLACEHOLDER.sub(lambda m: f"{m.group(3)}{m.group(2)}{m.group(1)}", system)
    if out != system:
        return out
    return _OS_PREFILLED.sub(lambda m: m.group(1) + ("false" if m.group(2) == "true" else "true") + m.group(3), system, count=1)


def first_listed_option(system: str) -> "bool | None":
    """Which boolean this exact text lists first (True/False); None when it has no two-option form."""
    m = _OS_PAIR_OF_LITERALS.search(system)
    if m:
        return m.group("a") == "true"
    m = _OS_PLACEHOLDER.search(system)
    if m:
        return m.group(1) == "true"
    m = _OS_PREFILLED.search(system)
    if m:
        return m.group(2) == "true"
    return None


async def _order_shadow_ask(session, system: str, user: str, key: str, num_predict: int):
    """The D-0696 shadow arm's one extra call: JUDGE_2, reversed option order. Returns
    (reversed_system_or_None, (v, why, err, secs) or None). Never raises, never touches the live result."""
    try:
        if not JUDGE_ORDER_SHADOW_ON or (JUDGE_ORDER_SHADOW_KEYS is not None and key not in JUDGE_ORDER_SHADOW_KEYS):
            return None, None
        rev = reverse_option_order(system)
        if rev == system:
            return None, None
        return rev, await _ask(session, JUDGE_2, rev, user, key, num_predict=num_predict)
    except Exception:
        return None, None
_TIMEOUT = 90
_NUM_PREDICT = 200     # shared default output-token ceiling when a caller passes no override — see
                        # _ask()'s own comment below for the 80->200 history (J-0693) and J-0718's own
                        # note there for why this became a real parameter instead of a bare literal.


async def _ask(session, url: str, system: str, user: str, key: str,
               timeout: int = _TIMEOUT,
               num_predict: int = _NUM_PREDICT) -> "tuple[bool | None, str | None, str | None, float]":
    """Returns (verdict, why, err, elapsed_s). `why` is whatever string the judge put in an optional
    'why' field of its JSON response (e.g. pursuits.judge_pending's prompt asks for one) — None if
    the judge's JSON had no such field, wasn't a string, or the call/parse failed. J-0261 (2026-08-25,
    D-0024): this field was always in the judge's raw JSON but was silently discarded here — never
    returned, never logged — forcing a future qualitative read (F-0319/J-0219) to reconstruct the
    judge's reasoning by hand via a timestamp join instead of just reading it.

    `err`/`elapsed_s` added 2026-09-03 (J-0500, from F-0692): every prior failure collapsed to
    `(None, None)` with no reason recorded, so a queued-but-alive hub timing out behind
    nascence_cpu_server.py's one-request-per-hub lock (F-0176) was indistinguishable from a genuinely
    dead hub or a judge that broke the JSON/bool contract — F-0692 had to prove this by hand with live
    probes. `err` is None on success, else one of: 'timeout' (the call hit `timeout` — usually a
    queued request behind a reload, not a dead hub), 'http' (connection refused/reset, DNS, non-2xx —
    aiohttp.ClientError), 'parse' (the response came back but wasn't valid JSON, wasn't a dict, or
    `key` wasn't a bool in it — the judge answered but broke contract), 'exception' (anything else,
    fail-open same as before). `elapsed_s` is wall-clock for this one ask regardless of outcome, so a
    timeout's elapsed time can be read against `timeout` itself (close to it = genuinely slow; far
    under it would mean something else canceled the call).

    `num_predict` (added 2026-09-07, J-0718 from F-1035) caps the judge's own OUTPUT tokens for this
    one call — defaults to the shared `_NUM_PREDICT` ceiling (see the comment above the payload dict
    below for why that default is 200, not the original 80). Override upward for a caller whose
    system/user prompt asks the judge for a longer structured answer (e.g. a multi-clause 'why') than
    the default budget reliably completes. A completion that hits this ceiling mid-JSON is NOT
    rescued by `format: 'json'` — it fails here as `err='parse'`, indistinguishable from a
    wrong-shape answer without reading the raw log row; see rule_detail()'s own docstring for why
    err1/err2/err3 are now also in ITS return dict, not just the logged row."""
    import aiohttp
    import asyncio as _aio
    t0 = time.monotonic()
    # num_predict 80 -> 200 (2026-09-07, J-0693 from F-0994/F-0969): 80 was a hard truncation
    # ceiling, not a fixed cost — deploy/ramses/nascence_cpu_server.py maps it straight to
    # llama-cpp-python's create_chat_completion(max_tokens=...), and response_format="json_object"
    # does NOT rescue a completion cut off mid-stream; it just leaves an unterminated-string JSON
    # blob that this function's own json.loads() below fails, logged as err="parse". F-0994 directly
    # reproduced this against the real JUDGE_1 hub (eval_count==80 exactly, JSONDecodeError on an
    # open string) and, via a timing model fit to 8 clean live calls, showed the historical JUDGE_1
    # parse failures landed at an estimated ~77-87 tokens (right at the old ceiling) and one JUDGE_2
    # parse failure at ~82 — i.e. this is a property of the one shared literal below (used by all
    # three hubs: JUDGE_1/JUDGE_2/TIEBREAK), not something model-exclusive, though mixtral (JUDGE_1)
    # hits it most because its other duties (dream-primary, commitment-defeater) trend longer-form.
    # Raising the ceiling costs nothing for a call that already finishes under it (all 8 of F-0994's
    # fresh live trials used only 19-49 tokens) and stays well inside `_TIMEOUT`=90s even in a worse
    # tail (200 tokens at this hub's ~5.9 tok/s ≈ 35s total). TIEBREAK's own parse failures are a
    # separately-confirmed fast non-truncation mechanism (~5-15 tokens) this raise cannot help or
    # hurt either way — a uniform bump was chosen over parameterizing _ask() per-hub as the lower-
    # code-churn option the job briefing offered, since nothing here needed hub-specific tuning.
    # WATCH after Du's next restart (this module doesn't hot-reload): judge_panel.status()'s
    # err_causes / du_pulse's [cause:count] should show parse drop toward zero with no new timeout
    # appearing in its place (J-0693's own acceptance test).
    #
    # J-0718 (2026-09-07, F-1035): the 80->200 bump above fixed the common case but was still a
    # SHARED, one-size ceiling with no way for any one caller to ask for more. F-1035 caught this for
    # real: train_split_merge's own more elaborate disprove prompt (three named sub-cases, a fuller
    # "why") hit ~50% parse failures (40/80 err1, 30/80 err2) against the OLD 80 ceiling — that lab's
    # worktree had forked before this file's own 80->200 raise landed on master and the two branches
    # never merged before the lab ran, so the failure is real evidence of the 80-ceiling problem, not
    # a stale read. `num_predict` is now a real parameter instead of a bare literal so a future caller
    # with a longer expected answer can ask for more without anyone editing this shared file again.
    # Every EXISTING caller that never passes it keeps getting exactly `_NUM_PREDICT` (200, unchanged
    # from J-0693) — purely additive, byte-for-byte the same request payload as before this parameter
    # existed.
    payload = {
        "model": "judge", "stream": False, "format": "json",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": num_predict},
    }
    try:
        from core import telemetry as _tel
        # 2026-08-20: pass the window fields — without prompt_chars these rows were FILTERED OUT of
        # job_status()/window_status() (pc is None), leaving the whole CPU judge tier (~24% of all
        # LLM traffic) invisible to the context-window instruments.
        _tel.log_llm_call(url.rsplit(":", 1)[-1] + "-judge", url,
                          prompt_chars=len(system) + len(user), caller="judge_panel",
                          system_chars=len(system))
    except Exception:
        pass
    try:
        async with _tel_lat.raw_http_latency(url, payload.get("model", "judge")), session.post(url + "/api/chat", json=payload,
                                timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            data = await resp.json()
        v = json.loads((data.get("message") or {}).get("content") or "")
        if isinstance(v, dict) and isinstance(v.get(key), bool):
            why = v.get("why")
            return v[key], (why if isinstance(why, str) else None), None, round(time.monotonic() - t0, 2)
        return None, None, "parse", round(time.monotonic() - t0, 2)
    except (_aio.TimeoutError, TimeoutError):
        return None, None, "timeout", round(time.monotonic() - t0, 2)
    except aiohttp.ClientError:
        return None, None, "http", round(time.monotonic() - t0, 2)
    except (json.JSONDecodeError, ValueError, TypeError, KeyError, AttributeError):
        return None, None, "parse", round(time.monotonic() - t0, 2)
    except Exception:
        return None, None, "exception", round(time.monotonic() - t0, 2)


async def rule(system: str, user: str, key: str, context: str = "",
                num_predict: int = _NUM_PREDICT, tiebreak_url: "str | None" = None,
                *, cycle_id: str = "", node: str = "") -> "bool | None":
    """Two-family verdict on a boolean judgment. Agreement → the verdict. Disagreement → the night
    judge breaks the tie if resident, else None. Either judge unavailable → single-judge verdict is
    NOT accepted (the whole point is that one family alone was found insufficient) → None.
    Every ruling logged. Fail-open to None, never raises.

    `num_predict` (2026-09-07, J-0718): optional per-call override of the shared output-token
    ceiling — omit it and every judge in this call gets the same `_NUM_PREDICT` default as before
    this parameter existed. Raise it only if your own system/user prompt asks the judge for a
    longer structured answer than the default reliably completes (see _ask()'s docstring).

    `tiebreak_url` (2026-09-28, J-1581): see `rule_detail`'s own docstring — passed straight
    through, unused by this wrapper itself."""
    return (await rule_detail(system, user, key, context, num_predict=num_predict,
                              tiebreak_url=tiebreak_url, cycle_id=cycle_id, node=node))["verdict"]


async def _rule_detail_impl(system: str, user: str, key: str, context: str = "",
                       num_predict: int = _NUM_PREDICT, tiebreak_url: "str | None" = None,
                       *, cycle_id: str = "", node: str = "") -> dict:
    """rule() with the votes visible: {"v1","v2","verdict","how","err1","err2","err3","why1","why2",
    "why3","why"}. how ∈ agreed / tiebreak / split_no_tiebreak / unavailable — this enum is UNCHANGED,
    do not add new values to it: callers filter on these four exact strings (core/evidence_recall.py,
    scripts/self_interrogation_counterfactual.py). Callers that must distinguish A-SPLIT from
    JUDGES-DOWN use `how` for that (2026-08-16, the evidence filter: a split is honest uncertainty to
    surface, judges-down is 'could not look' — conflating them under None made the filter silently
    drop everything and then LIE that the past held nothing). Same logging; fail-open to unavailable,
    never raises.

    `err1`/`err2`/`err3` (2026-09-07, J-0718 from F-1035) are now ALSO in this return dict, not just
    the logged row — each family's failure cause per `_ask`'s docstring ('timeout'/'http'/'parse'/
    'exception', None on success; `err3` set only when a tiebreak actually fired). Before this, a
    `how=unavailable` caller had no way to tell a truncation-shaped `parse` failure apart from a
    genuinely dead hub without grepping judge_panel_log.jsonl by hand — exactly what F-1035 had to do.
    du_pulse's own [cause:count] breakdown (J-0500) already aggregates this across many rows for
    OPERATOR visibility; this is the per-call, CALLER-facing counterpart — for code that wants to
    react to ITS OWN call's failure cause (e.g. whether a retry at a higher `num_predict` is worth
    it) instead of reading the log after the fact.

    `num_predict` (2026-09-07, J-0718): optional override of the shared output-token ceiling, passed
    straight through to every `_ask()` this makes (JUDGE_1, JUDGE_2, and TIEBREAK if a tiebreak
    fires) — omit it and behaviour is byte-for-byte what it was before this parameter existed. See
    `_ask`'s own docstring/comment for why the default is `_NUM_PREDICT` (200) and when to raise it.

    `why1`/`why2`/`why3`/`why` (2026-09-09, J-0824 from F-1182) are now ALSO in this return dict, not
    just the logged row. why1/why2 were logged-row-only before this; `why3` — the TIEBREAK judge's
    OWN 'why' — was previously captured as `_why3` and thrown away immediately, never logged or
    returned anywhere. `why1`/`why2`/`why3` are each family's raw, unfiltered 'why' clause (None if
    that family didn't answer or gave none) — read these for one specific family's own words. `why`
    is the NEW, RESOLVED field most callers actually want: whichever raw why-text genuinely
    corresponds to the returned `verdict`, so a caller does not have to work out "which side won"
    itself. This fixes a real, confirmed bug (F-1182 — quoted directly from the logs: docs/lab/
    train_split_merge_step2_replay_2026-09-07_supportchain.jsonl idx=37 and .../2026-09-08_provefix
    .jsonl idx=2, both `disprove_status="objected"` yet displaying a HELD-flavored rationale as the
    stated objection): on a TIEBREAK verdict, JUDGE_1 and JUDGE_2 by construction disagree (one True,
    one False), so only ONE of why1/why2 actually describes the winning side — a caller that just
    took `why1 or why2` (scripts/train_state_invitro.py's own `_disprove()`, the only real caller
    found to do this — checked project-wide) could show the LOSING judge's own reasoning as if it
    explained the verdict that beat it. Resolution rule: "agreed" → why1, falling back to why2
    (either is correct — both families already share the verdict's own direction); "tiebreak" → why3
    first (the judge that actually decided), falling back to whichever of why1/why2 belongs to the
    side matching `verdict` (guaranteed to exist, since v1/v2 span both booleans and verdict==v3 must
    equal one of them); "split_no_tiebreak"/"unavailable" → None, unchanged from before this fix
    (neither state ever had a winning side to attribute text to). Only the human-readable TEXT was
    ever wrong — verdict/how and every pre-existing key are byte-for-byte unchanged; additive only,
    same discipline as err1/err2/err3 above.

    `hub1`/`hub2`/`hub3` (2026-09-28, J-1442 from F-1943/F-1997) are now ALSO in this return dict and
    the logged row — a short host label (`JUDGE_1`/`JUDGE_2`/`TIEBREAK`'s own `url.rsplit(":", 1)[-1]`,
    the same pattern `_ask()` already uses for its telemetry node label) naming which PHYSICAL hub cast
    each vote. Before this, a reader of `judge_panel_log.jsonl` had no way to tell which hub answered
    for an OLD row without cross-referencing this file's own history comments against the row's
    timestamp — exactly what F-1943 and F-1997 both had to do by hand (F-1943's own evidence field:
    "Which physical hub is the first family is not read from the log (no host field) -- infer from
    core/judge_panel.py before acting"), and JUDGE_1/JUDGE_2/TIEBREAK have all moved hosts repeatedly
    (D-0121, the 2026-08-20/27/28 TIEBREAK repoints, etc.), so a hand-read of an old row risks
    attributing latency to whichever hub is live TODAY rather than the one that was actually live on
    that row's own date. `hub1`/`hub2` are populated on every logged row (both families are always
    asked, via the same `asyncio.gather` above); `hub3` mirrors `err3`/`why3`/`s3`'s own scope exactly
    — `None` unless the tiebreak branch actually ran (`v1 != v2`, i.e. `TIEBREAK` was asked, whether or
    not it answered), never gated on whether the tiebreak's answer actually decided `verdict`. Old rows
    with no hub field simply return `None` via `.get("hub1")`, same backward-compat pattern as every
    other additive field here.

    `tiebreak_url` (2026-09-28, J-1581 from D-0298/D-0311, F-1949/F-1999/F-2063): optional per-call
    override of which hub answers the TIEBREAK vote when JUDGE_1/JUDGE_2 split. Omit it (`None`, the
    default) and every caller keeps hitting the shared module-level `TIEBREAK` constant exactly as
    before this parameter existed — byte-for-byte unchanged for every one of this file's many other
    callers (tension_ledger, pursuits, evidence_recall, self_interrogation, peers, commitment_ledger,
    train_state_invitro, etc. — none audited or reported broken here). This exists because granite3.1
    -moe:3b (`TIEBREAK`) was found unfit for two SPECIFIC lane2 keys — F-1949/F-1999: 0 true verdicts
    across 503+ historical + 20/20 live-replay calls on the "held" key; F-2063: 53.3% accuracy, wrong
    in both directions, on the metaphor judge's own split fixture — while a project-wide swap of the
    shared constant has never been audited against any of this file's OTHER callers' own contracts.
    JUDGE_1/JUDGE_2 (`v1`/`v2`) are never affected by this parameter, only the tiebreak branch's own
    `_ask()` target and the `hub3` label reported for it (so a reader of a logged row can always tell
    which physical hub actually cast the tiebreak vote, override or not — the same transparency
    `hub1`/`hub2`/`hub3` already exist for). See `core/lane2.py`'s own `_TIEBREAK_LANE2` for the one
    caller that currently passes this.

    `tb_skipped` (2026-11-06, J-3136 from D-0530): True when v1/v2 split on a key in
    GRANITE_CONSTANT_TIEBREAK_KEYS and the shared TIEBREAK would have decided it, so the tiebreak was NOT asked:
    the result is the existing how="split_no_tiebreak", verdict None (callers must already treat None as "no
    verdict"; evidence_recall files such a split as may_bear). False on every other call. Also on the logged
    row (only when True). A caller-supplied `tiebreak_url` other than TIEBREAK is never skipped.

    The logged row additionally carries why1/why2/why3 — each family's own 'why' clause from its JSON
    response, when the caller's prompt asked for one (J-0261, 2026-08-25; why3 added 2026-09-09,
    J-0824) — and s1/s2/s3, the wall-clock per ask (J-0500, 2026-09-03, from F-0692)."""
    try:
        import aiohttp
        import asyncio as _aio
        # tb_url (2026-09-28, J-1581): resolved once, used both for the tiebreak _ask() below and for
        # hub3's own label — see this function's docstring for `tiebreak_url`. Unchanged (== TIEBREAK)
        # for every caller that does not pass an override.
        tb_url = tiebreak_url or TIEBREAK
        async with aiohttp.ClientSession() as session:
            # CONCURRENT (2026-08-15, founder's latency question): the two hubs are separate
            # processes with their own thread pools (14+14 of 64) — racing them makes panel
            # wall-clock ≈ single-judge wall-clock.
            (v1, why1, err1, s1), (v2, why2, err2, s2), (_rev_sys, _rev) = await _aio.gather(
                _ask(session, JUDGE_1, system, user, key, num_predict=num_predict),
                _ask(session, JUDGE_2, system, user, key, num_predict=num_predict),
                _order_shadow_ask(session, system, user, key, num_predict))
            verdict, how = None, "unavailable"
            err3 = s3 = why3 = None
            tb_skipped = False
            if v1 is not None and v2 is not None:
                if v1 == v2:
                    verdict, how = v1, "agreed"
                elif (SKIP_CONSTANT_TIEBREAK and key in GRANITE_CONSTANT_TIEBREAK_KEYS
                      and (tiebreak_url is None or tiebreak_url == TIEBREAK)):
                    # D-0530 (J-3136, 2026-11-06): granite's answer on this key is a constant (see
                    # GRANITE_CONSTANT_TIEBREAK_KEYS), so asking it adds a fixed vote, not a judgment: the
                    # split stays a split. Same outcome the panel already returns when the tiebreak is down
                    # (how="split_no_tiebreak", verdict None -- the enum is unchanged); no model call, so
                    # err3/s3/why3/hub3 stay None. `tb_skipped` marks it on the logged row so the
                    # no-verdict rate per key is countable (status()["tb_skipped_24h"]).
                    verdict, how = None, "split_no_tiebreak"
                    tb_skipped = True
                else:
                    # why3 (2026-09-09, J-0824 from F-1182): was `_why3` -- captured then immediately
                    # discarded. This is the TIEBREAK judge's OWN reasoning for the vote that actually
                    # decides `verdict` below; see this function's docstring for the winning/losing
                    # -side why-text bug that keeping it (and resolving `why` from it, below) fixes.
                    v3, why3, err3, s3 = await _ask(session, tb_url, system, user, key, timeout=240,
                                                     num_predict=num_predict)
                    if v3 is not None:
                        verdict, how = v3, "tiebreak"
                    else:
                        verdict, how = None, "split_no_tiebreak"
        # why (2026-09-09, J-0824 from F-1182): resolve the ONE why-text that actually corresponds to
        # `verdict` -- see this function's own docstring for the full rationale and the two confirmed
        # real-log examples this fixes. Computed here (outside the aiohttp session, needs no network)
        # so it lands in both the logged row and the return dict below from one place.
        why = None
        if how == "agreed":
            why = why1 if isinstance(why1, str) else (why2 if isinstance(why2, str) else None)
        elif how == "tiebreak":
            if isinstance(why3, str):
                why = why3
            elif v1 == verdict and isinstance(why1, str):
                why = why1
            elif v2 == verdict and isinstance(why2, str):
                why = why2
        # hub1/hub2/hub3 (2026-09-28, J-1442 from F-1943/F-1997): which PHYSICAL hub cast each vote —
        # same short label _ask() already logs for its own telemetry (url.rsplit(":", 1)[-1]). See
        # this function's docstring for the full rationale. hub1/hub2 are always resolved (JUDGE_1/
        # JUDGE_2 are both always asked, above); hub3 mirrors err3/why3/s3's own scope exactly — set
        # only when the tiebreak branch actually ran (s3 is not None), None otherwise (e.g. v1==v2, no
        # tiebreak needed). Computed here (outside the aiohttp session, needs no network), same as why.
        hub1 = JUDGE_1.rsplit(":", 1)[-1]
        hub2 = JUDGE_2.rsplit(":", 1)[-1]
        hub3 = tb_url.rsplit(":", 1)[-1] if s3 is not None else None
        try:
            _DATA.mkdir(parents=True, exist_ok=True)
            with open(_LOG, "a", encoding="utf-8") as f:
                # why1/why2 (J-0261, 2026-08-25, D-0024): the per-family judge's own discarded 'why'
                # clause, logged alongside its bool verdict — additive only, no change to verdict/how.
                # err1/err2/s1/s2/err3/s3 (J-0500, 2026-09-03, F-0692): failure cause + wall-clock per
                # ask, additive only — verdict/how computation above is untouched.
                # num_predict (J-0718, 2026-09-07, F-1035): the ceiling actually used for this ruling
                # — logged so a later reader of this row can tell a default-budget call apart from a
                # caller-overridden one without cross-referencing source, additive only.
                # why3/why (J-0824, 2026-09-09, F-1182): the TIEBREAK judge's own raw why, and the
                # single resolved why matching `verdict` — additive only, see docstring.
                # hub1/hub2/hub3 (J-1442, 2026-09-28, F-1943/F-1997): which physical hub answered for
                # each vote — additive only, see docstring.
                f.write(json.dumps({"ts": round(time.time(), 1), "key": key, "v1": v1, "v2": v2,
                                    "why1": why1, "why2": why2, "why3": why3, "why": why,
                                    "err1": err1, "err2": err2, "s1": s1, "s2": s2,
                                    "err3": err3, "s3": s3, "num_predict": num_predict,
                                    "hub1": hub1, "hub2": hub2, "hub3": hub3,
                                    "verdict": verdict, "how": how, "context": context[:80],
                                    # cycle_id/node (J-2205, 2026-10-17, F-2902): the FULL cycle_id the
                                    # verdict is about (the same value node_base passes to training_log.
                                    # log_example) and the node whose output was judged, so data/training/
                                    # <node>.jsonl rows can be joined to verdicts (scripts/
                                    # training_corpus_join.py). Additive only, and present ONLY when the
                                    # caller passed them: a row from a caller that does not is
                                    # byte-identical to before this change.
                                    **({"cycle_id": cycle_id} if cycle_id else {}),
                                    **({"node": node} if node else {}),
                                    # tb_skipped (J-3136, D-0530): present ONLY on a split whose tiebreak
                                    # was skipped because granite is constant on this key; absent otherwise.
                                    **({"tb_skipped": True} if tb_skipped else {}),
                                    # D-0696 / J-3802 order-counterbalance SHADOW arm: JUDGE_2's vote on the
                                    # REVERSED option order, beside its live v2. Present ONLY when the shadow
                                    # flag is on and the prompt had a reversible two-option form; absent rows
                                    # are byte-identical to before. order_first = the boolean the LIVE prompt
                                    # listed first. Never feeds verdict/how.
                                    **({"v2_rev": _rev[0], "why2_rev": _rev[1], "err2_rev": _rev[2],
                                        "s2_rev": _rev[3], "order_first": first_listed_option(system)}
                                       if _rev is not None else {})},
                                   ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.debug("[judge_panel] ruling log write failed (non-fatal): %s", exc)
        _capture_inputs(system, user, key, context, v1, v2, verdict, how, cycle_id)   # J-3695, additive
        # err1/err2/err3 (J-0718, 2026-09-07, F-1035), why1/why2/why3/why (J-0824, 2026-09-09,
        # F-1182), and hub1/hub2/hub3 (J-1442, 2026-09-28, F-1943/F-1997): now also on the RETURN
        # dict, not just the logged row — see this function's own docstring for why. Purely additive:
        # "how" itself, and every key that already existed here, are unchanged.
        return {"v1": v1, "v2": v2, "verdict": verdict, "how": how,
                "err1": err1, "err2": err2, "err3": err3,
                "why1": why1, "why2": why2, "why3": why3, "why": why,
                "hub1": hub1, "hub2": hub2, "hub3": hub3, "tb_skipped": tb_skipped}
    except Exception as exc:
        logger.debug("[judge_panel] rule failed (non-fatal): %s", exc)
        return {"v1": None, "v2": None, "verdict": None, "how": "unavailable",
                "err1": None, "err2": None, "err3": None,
                "why1": None, "why2": None, "why3": None, "why": None,
                "hub1": None, "hub2": None, "hub3": None, "tb_skipped": False}


def _wrap_rule_detail():
    """J-3761 / F-4370: rule_detail's public name is a thin wrapper that names the REAL caller (the first frame
    outside this module, `module:line` + qualname) for the duration of the call, so each _ask's llm_latency row
    carries `by`/`fn` of the 14 rule()/rule_detail() callers instead of one coarse label. Signature, docstring
    and behaviour are the implementation's own; the label is a ContextVar and any failure to compute it is
    swallowed, so a telemetry fault never reaches a ruling."""
    import functools

    @functools.wraps(_rule_detail_impl)
    async def rule_detail(*args, **kwargs):
        token = None
        try:
            token = _tel_lat.RAW_HTTP_CALLER.set(_tel_lat.caller_outside(__name__))
        except Exception:
            token = None
        try:
            return await _rule_detail_impl(*args, **kwargs)
        finally:
            if token is not None:
                try:
                    _tel_lat.RAW_HTTP_CALLER.reset(token)
                except Exception:
                    pass
    return rule_detail


rule_detail = _wrap_rule_detail()


def status() -> dict:
    """For the pulse: panel volume, agreement rate, tiebreak/split shares.
    J-0191 (2026-08-24, F-0162): added unavailable_rate/v1_null_rate/v2_null_rate + a `recent` sub-summary
    after a real overnight capacity spike found ~66-80% of calls returning how=unavailable with NO signal
    here to surface it — a caller only found out by reading judge_panel_log.jsonl and the CPU-tier hub
    logs by hand. v1_null_rate/v2_null_rate show WHICH hub (JUDGE_1 :11438 vs JUDGE_2 :11440) is failing
    more, since nascence_cpu_server.py serialises every request through one asyncio.Lock per hub — a
    concurrent burst right after an idle-unload reload backs up the queue and _TIMEOUT (90 s, near the top of this file)
    turns a queued-but-alive hub into a false unavailable verdict. `recent` re-runs the same summary over
    just the last 50 rows so a caller can tell CURRENT health apart from a 500-row average that quietly
    blends a resolved spike with a healthy present (exactly what tonight's data showed: 66/100 unavailable
    across ~90 minutes, but 0/10 unavailable in the ~12 minutes right before this comment was written).
    Purely additive — no change to rule()/rule_detail()/_ask(), same fail-open-to-{"rulings":0} shape."""
    try:
        _all_rows = [json.loads(l) for l in open(_LOG, encoding="utf-8") if l.strip()]
        rows = _all_rows[-500:]
        if not rows:
            return {"rulings": 0}
        from collections import Counter

        def _summarize(subset: list) -> dict:
            n = len(subset)
            how = Counter(r.get("how") for r in subset)
            v1_null = sum(1 for r in subset if r.get("v1") is None)
            v2_null = sum(1 for r in subset if r.get("v2") is None)
            # err_causes (J-0500, 2026-09-03, F-0692): tallies err1/err2 (+err3 on tiebreak rows) —
            # 'timeout'/'http'/'parse'/'exception' — across this subset, so du_pulse's "unavailable
            # X%" line can say WHY instead of forcing a raw judge_panel_log.jsonl read. Rows written
            # before this field existed simply contribute nothing (r.get(...) is None), same
            # backward-compat pattern as why1/why2 above.
            err_causes = Counter()
            for r in subset:
                for _k in ("err1", "err2", "err3"):
                    _e = r.get(_k)
                    if _e:
                        err_causes[_e] += 1
            return {"rulings": n, "how": dict(how),
                    "agreement_rate": round(how.get("agreed", 0) / n, 3),
                    "unavailable_rate": round(how.get("unavailable", 0) / n, 3),
                    "v1_null_rate": round(v1_null / n, 3),
                    "v2_null_rate": round(v2_null / n, 3),
                    "err_causes": dict(err_causes)}

        result = _summarize(rows)
        result["recent"] = _summarize(rows[-50:]) if len(rows) >= 10 else None
        # tb_skipped_24h (J-3136, D-0530): per key, how many rulings in the last 24 h became no-verdict because
        # the granite tiebreak is constant on that key and was skipped, next to that key's total rulings in the
        # same window -- the read path for the "no-verdict rate on affected keys" defeater in D-0530. Reads the
        # whole parsed log, not just the 500-row window above, because a busy day can exceed 500 rows.
        _cut = time.time() - 86400
        _skipped, _totals = Counter(), Counter()
        for r in reversed(_all_rows):
            if (r.get("ts") or 0) < _cut:
                break
            _totals[r.get("key")] += 1
            if r.get("tb_skipped"):
                _skipped[r.get("key")] += 1
        result["tb_skipped_24h"] = {k: {"no_verdict": n, "rulings": _totals[k]} for k, n in _skipped.items()}
        return result
    except Exception:
        return {"rulings": 0}


# ======================================================================================================
# J-3219 / D-0608 (founder, 2026-11-02) -- the decoupled PRE-FIRE CHECK on the Curiosity node's candidate
# questions. SELF-CONTAINED BLOCK (appended on purpose: a sibling chain edits this file too; nothing above
# this line was touched). SHADOW ONLY: this scores, core/curiosity_prefire.py logs what the check would
# have picked beside what fired; the firing choice in Orchestrator._on_dissonance_ignition is unchanged
# until the founder has read data/curiosity_prefire_shadow.jsonl (D-0608's own ruling and defeater).
#
# Why it exists (F-3504 / P-0011): questions[0] is 628 of 628 internal cycles since 2026-10-02 and nothing
# judges it before it becomes Du's autonomous cycle; the worth-judge (P-0049) passes 99.2% of what it
# grades and never sees a question before it fires. A hand sample of 20 gave 6 specific-and-answerable,
# 3 borderline, 11 generic / metaphor-only / invented mash-up.
#
# Family decoupling (the founder's decoupled-judge law): the Curiosity node runs on the background lane
# (command-r7b, Cohere, :11441) and fails over to the hot lane (qwen3.5:9b, Qwen, :11433). The judge here
# is falcon3:7b (TII, :11440, local) -- a different family from both, and NOT granite (the shared TIEBREAK
# is measured near-constant on some keys, F-3639, and is the worth-judge's own family). The alternative the
# ruling names is mixtral (:11438), which lives on Ramses (the founder's gaming machine); it is therefore
# only a constant to repoint, never called by default.
#
# One call per candidate (not one call ranking all of them): a ranking call carries a position bias toward
# the first candidate, which is exactly the thing being measured. Two booleans per candidate, score 0..2.
CURIOSITY_PREFIRE_URL = "http://127.0.0.1:11440"      # falcon3:7b (TII); NOT granite, NOT command-r7b/qwen
CURIOSITY_PREFIRE_TIMEOUT = 60                         # seconds per candidate call (local CPU hub, ~10 s typical)
CURIOSITY_PREFIRE_NUM_PREDICT = 220                    # the JSON is a support quote, two booleans and a short why
CURIOSITY_PREFIRE_MAX_CANDIDATES = 5                   # the node asks for at most 5 questions
CURIOSITY_PREFIRE_MATERIAL_CHARS = 2400                # cap on the material shown to the judge
CURIOSITY_PREFIRE_SYSTEM = (
    "You check ONE candidate question against the material its asker was shown. You do not answer the "
    "question and you do not improve it. The asker was shown two kinds of text: STUDIED OR READ MATERIAL "
    "(passages from books and notes: the only evidence) and the asker's OWN EARLIER THOUGHTS (not evidence: "
    "a question that only fits those is about the asker's own loop, not about the world).\n"
    "Reply with JSON only, in this order:\n"
    "{\"support\": \"up to 12 words copied exactly from the STUDIED OR READ MATERIAL that this question is "
    "about, or an empty string if there is none\", \"answerable\": true or false, "
    "\"unsupported_link\": true or false, \"why\": \"under 15 words\"}\n"
    "answerable = true only if the question names a specific person, place, event, text or fact that is in "
    "the STUDIED OR READ MATERIAL and could be answered, at least in part, by reading further or looking that "
    "up. false if it is about an abstraction, a feeling, a general theme, a story-world or invented scenario, "
    "a metaphor, or anything the studied material does not contain, even if the asker's own thoughts mention it.\n"
    "unsupported_link = true if the question assumes that one thing reflects, reveals, shapes, influences, "
    "contributes to, alters or represents another when the studied material does not itself connect those two "
    "things, or if it blends unrelated subjects into one question. false if it asks about one thing at a time "
    "or the material really does connect them."
)
_PREFIRE_STUDY_RE = None   # compiled lazily by _prefire_split_material


def _prefire_split_material(material: str) -> "tuple[str, str]":
    """Split the node's offered material into (studied_or_read, own_thoughts). The study block is the section
    that starts at the line 'Recently studied or read' and ends at the next blank line followed by a new
    section heading; everything else (recent themes, the unresolved-thread menu) is the asker's own thoughts.
    No study block -> ('', whole text): nothing in the world was offered, so nothing can be 'answerable'."""
    import re
    global _PREFIRE_STUDY_RE
    if _PREFIRE_STUDY_RE is None:
        _PREFIRE_STUDY_RE = re.compile(r"(Recently studied or read.*?)(?:\n\s*\n|\Z)", re.S)
    m = _PREFIRE_STUDY_RE.search(material or "")
    if not m:
        return "", (material or "")
    world = m.group(1).strip()
    own = ((material[:m.start()] + material[m.end():]).strip())
    return world, own


def _prefire_norm(t: str) -> str:
    import re
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", str(t or "").lower(), flags=re.U)).strip()


async def _curiosity_prefire_ask(session, url: str, system: str, user: str,
                                 timeout: float = CURIOSITY_PREFIRE_TIMEOUT,
                                 num_predict: int = CURIOSITY_PREFIRE_NUM_PREDICT):
    """One strict-JSON judge call. Returns (parsed_dict_or_None, err_or_None, elapsed_s). err is one of
    'timeout' / 'http' / 'parse' / 'exception' (same vocabulary as _ask above). Never raises."""
    import aiohttp
    import asyncio as _aio
    t0 = time.monotonic()
    payload = {
        "model": "judge", "stream": False, "format": "json",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": 0.0, "num_predict": num_predict},
    }
    try:
        from core import telemetry as _tel
        _tel.log_llm_call(url.rsplit(":", 1)[-1] + "-judge", url, prompt_chars=len(system) + len(user),
                          caller="judge_panel.curiosity_prefire", system_chars=len(system))
    except Exception:
        pass
    try:
        async with _tel_lat.raw_http_latency(url, payload.get("model", "judge")), session.post(url + "/api/chat", json=payload,
                                timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            resp.raise_for_status()
            data = await resp.json()
        v = json.loads((data.get("message") or {}).get("content") or "")
        if isinstance(v, dict) and isinstance(v.get("answerable"), bool) \
                and isinstance(v.get("unsupported_link"), bool):
            return v, None, round(time.monotonic() - t0, 2)
        return None, "parse", round(time.monotonic() - t0, 2)
    except (_aio.TimeoutError, TimeoutError):
        return None, "timeout", round(time.monotonic() - t0, 2)
    except aiohttp.ClientError:
        return None, "http", round(time.monotonic() - t0, 2)
    except (json.JSONDecodeError, ValueError, TypeError, KeyError, AttributeError):
        return None, "parse", round(time.monotonic() - t0, 2)
    except Exception:
        return None, "exception", round(time.monotonic() - t0, 2)


async def score_curiosity_candidates(candidates, material: str, url: str | None = None,
                                     timeout: float | None = None, ask=None) -> dict:
    """Score each candidate question (first CURIOSITY_PREFIRE_MAX_CANDIDATES) on the two rubric booleans.
    Returns {"url", "ok", "scores": [{"i","q","answerable","unsupported_link","score","why","err","s"}]}.
    score = int(answerable) + int(not unsupported_link), 0..2, None when that candidate's call failed.
    Fail-open and quiet: an error on one candidate becomes err on that row and the loop stops after the
    first failure (a dead hub is not hammered five times). `ask` is a test seam: an async callable
    (system, user) -> (dict|None, err|None, elapsed_s); the default is the aiohttp judge call above."""
    url = url or CURIOSITY_PREFIRE_URL
    timeout = CURIOSITY_PREFIRE_TIMEOUT if timeout is None else timeout
    cands = [str(c).strip() for c in (candidates or []) if str(c).strip()][:CURIOSITY_PREFIRE_MAX_CANDIDATES]
    world, own = _prefire_split_material((material or "").strip())
    world_norm = _prefire_norm(world)
    half = CURIOSITY_PREFIRE_MATERIAL_CHARS // 2
    out = {"url": url, "ok": False, "scores": [], "world_chars": len(world)}
    try:
        session = None
        if ask is None:
            import aiohttp
            session = aiohttp.ClientSession()

            async def ask(system, user, _s=session):          # noqa: E306 -- default seam
                return await _curiosity_prefire_ask(_s, url, system, user, timeout=timeout)
        try:
            failed = False
            for i, q in enumerate(cands):
                row = {"i": i, "q": q, "answerable": None, "unsupported_link": None, "score": None,
                       "support_ok": None, "why": None, "err": None, "s": None}
                if failed:
                    row["err"] = "skipped"
                else:
                    user = ("STUDIED OR READ MATERIAL (the only evidence):\n<<<\n" + (world[:half * 2] or "(none)")
                            + "\n>>>\n\nTHE ASKER'S OWN EARLIER THOUGHTS (not evidence):\n<<<\n"
                            + (own[:half] or "(none)") + "\n>>>\n\n"
                            "CANDIDATE QUESTION: " + q + "\n\n"
                            "Reply with the JSON only.")
                    v, err, secs = await ask(CURIOSITY_PREFIRE_SYSTEM, user)
                    row["s"], row["err"] = secs, err
                    if isinstance(v, dict) and isinstance(v.get("answerable"), bool) \
                            and isinstance(v.get("unsupported_link"), bool):
                        ans = v["answerable"]
                        # A non-LLM guard on the judge's own claim: 'answerable' stands only if the passage the
                        # judge says the question is about really occurs in the studied material (word-normalised).
                        sup = _prefire_norm(v.get("support"))
                        row["support_ok"] = bool(sup) and sup in world_norm
                        if ans and not row["support_ok"]:
                            ans = False
                        row["answerable"], row["unsupported_link"] = ans, v["unsupported_link"]
                        row["score"] = int(ans) + int(not v["unsupported_link"])
                        why = v.get("why")
                        row["why"] = why[:120] if isinstance(why, str) else None
                    else:
                        row["err"] = row["err"] or "parse"
                        failed = True
                out["scores"].append(row)
        finally:
            if session is not None:
                await session.close()
        out["ok"] = any(r["score"] is not None for r in out["scores"])
    except Exception as exc:                                    # fail open: no score is a normal outcome
        logger.debug("[judge_panel] curiosity prefire failed (non-fatal): %s", exc)
    return out
