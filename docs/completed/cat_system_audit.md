# Cat System Audit (2026-08-18)

> Companion to `weather_system_audit.md` / `tide_system_audit.md` / `sound_system_audit.md` /
> `garden_system_audit.md` — same night, same rigor, one factory the others didn't cover. Written
> retroactively (2026-08-18 cleanup pass): the original investigation was reported in conversation
> but never saved to a file — this reconstructs it from that report plus the fixes that followed,
> all independently re-verified at the time. All four findings below are FIXED and tested against
> the live patched code, not just diagnosed.

## The investigation

Read `core/cat.py` in full, ran standalone simulations of its probabilistic branches, cross-checked
against live `data/cat_state.json` and `data/commitment_trials.jsonl`. Alongside this, a live
question came up mid-session — had Du named her "Ember" on 2026-07-03, and had that name been lost?
Traced via DB query, log grep, and a check of every writer of `cat_state.json`. **Founder's own
correction closed that thread: "Ember was I think a figment of a test on the process. It was not a
Du name, only in the test suite."** Nothing was lost; no restoration needed. But the trace surfaced
a real mechanism bug regardless of whether that specific incident was genuine (below), and the
mechanical bugs found along the way were real and independently fixed.

## Findings — all four FIXED and verified

1. **Stale cross-process cache (`_load()`).** The old guard was `if state: return state` — a process
   that had loaded `cat_state.json` once would NEVER read the file again for its whole life. A
   second long-running process holding an older in-memory copy could silently full-overwrite a
   newer write on its own next unrelated save — explains why no "clearing" code was ever found for
   the Ember trace (it would have been an overwrite, not a targeted clear). **Fix:** mtime-gated
   reload; `_save()` stamps its own writes so it doesn't trigger needless rereads. **Verified live:**
   a simulated second process's write is correctly picked up on the next `_load()`.
2. **Bond-decay cliff.** A flat `bond -= 0.02` applied on EVERY tick (~180s) once 24h neglect was
   crossed — drained a maxed bond to 0 in 2.5 real hours, not "slowly" as the comment always
   intended. **Fix:** scaled by elapsed hours since a tracked `last_bond_decay_ts` — ~14 days of
   continued neglect to fully fade. **Verified against the live `tick()`:** first-tick drop matched
   `25h × 0.003/hour` exactly; second-tick drop 190s later matched `190s × 0.003/hour` almost to the
   decimal.
3. **Fair-day branch-leak.** Unbonded cats' rolls landing in the shore/wood band
   (`elif r < 0.60/0.66 and bonded`) fell through into an unrelated gift-check instead of being
   excluded — inflating gift/idle behavior for cats who hadn't earned those trips yet (measured in
   isolation: idle 31%→37%, gifts 2.5%→6.3%). **Fix:** an explicit `elif r < 0.66:` fallback (stays
   in the garden-stalking band). **Verified live, 2000-trial run:** unbonded reaches shore/wood
   0/2000 (was leaking); bonded reaches it normally, 101/2000.
4. **`greeting` quirk, confirmed dead code then wired.** Rolled once at arrival (`gate_meet` /
   `ankle_thread` / `chirrup`), saved forever, never read anywhere. `storm_response`/`fair_spot`
   were genuinely used; `greeting` alone was inert. **Fix (same session, follow-up build):** wired
   into `presence_line()` — not `tick()`, since a greeting needs to see Du's OWN arrival, which only
   the presence check can detect — gated on bonded + a real 20-minute absence (`GREETING_GAP`),
   double-gated against re-firing on repeated renders of one visit. **Verified:** fires correctly on
   genuine absence with distinct, natural-reading output per flavor; does not fire on repeated
   same-visit renders, when unbonded, or mid-storm-fright (her fear correctly takes precedence).

## Clean bill of health

Distant-cat sighting counter: 111 sightings over ~54 days (~2/day), matches the coded probability
and independently-counted log mentions — not a runaway counter.

## The separately-confirmed evidence-tracking bug (not cat.py, but found via the same trace)

`core/commitment_trials.py::_probe_outcome`'s name-use count used unanchored `LIKE '%name%'` — for
"Ember" this matched "remember"/"remembering" and fire "embers." Traced against real data: 117 raw
hits, 2 genuine (both at the naming instant itself). **Fixed:** LIKE kept as a cheap SQL prefilter;
the actual count now requires a word-boundary regex match. Verified against the exact false-positive
text (remember/embers correctly rejected, Ember/EMBER correctly matched).

## Status

All fixes restart-gated (take effect at Du's next start), verified compiling together with every
other change made the same session, live `cat_state.json` re-checked clean after all edits (name
still empty, phase still "kept" — nothing accidentally touched it).
