# memory_as_a_service — folded history


---

# History folded on 2026-09-28 from `docs\staged\memory_as_a_service.md` (plan-compact, 17 section(s), verbatim, original order)

_Every J-/F-/D- id below is the canonical record; this file is the prose that once sat in the plan doc. Derived timeline: `plan_ledger.py memory_as_a_service`._

- **2026-09-28** (F-2179): Ledger-id citation audit (F-2141 follow-up, F-2179): pattern is isolated, not widespread -- 0 of 105 dated Current State bullets across 30 plan docs cite a nonexistent F, J, I or S id. Found a different, minor defect instead: guidance_learning.md has 2 bullets citing unpadded D-ids (D-134 etc for D-0134 etc, real decisions, wrong digit count) -- spawned as its own fix job, not this plan's.

- **2026-09-28** (F-2178): J-1588 (D-0312) built the additional memory.ask call for curiosity alongside Scholar, descend=True by default, verified 30/30 in an isolated harness (F-2178).
- **2026-09-28** (F-2171): J-1569: built and verified plan_compact.py --fold-bullets (F-2132, F-2171); dry-run folds 13 of 14 bullets here to 48142 bytes, was 60551, id audit clean, 40 ids, 0 unknown; write deferred, this doc is git-dirty from concurrent edits right now, follow-up job J-1609 will complete it; also found lane2_the_witness.md has the same gap, J-1610 spawned, and fixed a shared pointer-line bug in the existing fold-h3 mode along the way

- **2026-09-28** (F-2152): D-0310 implemented (J-1587): all three kill-switches (IDLE_AMBIENT_RECALL, IDLE_FOUNDER_RECALL, IDLE_DIVERGENT_SEED) flipped True to False, commit 7a16745 on master; restart-gated, not yet live; J-1512/J-1513 unblocked pending restart plus roughly 2 weeks of accrual (F-2152).
- **2026-09-28** (F-2145): J-1516 (F-2145): built and verified evidence_recall.gather()'s felt-coordinate join (reusing memory_service._fetch_context) plus one memory_edges.log_co_recall row per ask (source=recall_act), additive alongside evidence_log.jsonl; inner_monologue_node.py's _evidence_recall now calls memory_service.note_usage(recall_act, embed of the rendered evidence text) as the sec4.3 hook. No change to _candidates, the judge-panel filter, or render. Verified in an isolated sys.modules-faked harness (verify_J-1516.py, 22/22 checks), no live DB/ledger/LLM touched. Committed 9235ae9 on jobrun/memory_as_a_service. Found J-1515's facade (core/memory_service.py) is actually already landed (commit b517c6f, built on further by J-1542's 22655b0) even though its own job-queue ticket still reads in_progress -- proceeded on that real evidence rather than deferring; spawned a hygiene job to close J-1515's ticket out formally. D-0310/D-0312 untouched (unrelated scope, no active hold on this plan).

- **2026-09-28** (F-2144): F-2144, J-1550: wired core/felt_recall.py trigger-edge handler to the Transport Manager (D-0294 part A) -- observe()/verdict() called on every edge for the 4 non-sound trigger dims, writing dispatcher_verdict/dispatcher_cold_start/dispatcher_weight onto the ride row; sound dims correctly left at None (out of scope). Committed d36322a on jobrun/memory_as_a_service (not yet merged). Section 8 item (e) already present in this doc -- confirmed, no re-add needed. Verified in an isolated harness (scratchpad/verify_felt_recall_J-1550.py, 34/34 checks) plus scripts/_test_transport_manager.py (47/47, no regression). Spawned J-1577 (companion to J-1507) because J-1507own briefing never mentions item (e) at all -- real risk it gets silently skipped at the >=7-day read. D-0294 already ruled by travis, not re-ruled here; D-0310/D-0312 untouched (unrelated scope, no active hold).
- **2026-09-28** (F-2142): J-1542: built and verified the six-slot cue (who/what/where/when/why/how) on core/memory_service.py ask() per sec4.7, in worktree wt_memory_as_a_service, commit 22655b0 on branch jobrun/memory_as_a_service. A bare cue with no what keyword still resolves to what=cue using k (not k_per_slot), so J-1515's dream_node.py/pursuits.py call sites are unchanged, exactly today. Also built sec4.4's own ride-log write (stop/line/dose/value rows to data/memory_service_shadow.jsonl), which this job found J-1515 had not actually shipped despite sec4.7's own briefing assuming it existed. Found two of the when slot's three named engines (store.retrieve_epoch, chapters.recall_chapter) are not fragment-shaped and carry no per-item fragment_id -- handled honestly with fragment_id=None rather than a fabricated one; follow-up job spawned to consider giving them a real one. Verified in an isolated sys.modules-faked harness backed by a real in-memory sqlite fixture (34/34 checks), no live DB or process touched. Also found and reported (F-2143, S-0219) that findings_log.py silently lost an earlier concurrent finding (J-1530's) under this batch's real concurrent load.

- **2026-09-28** (F-2139): J-1534: built and verified docs/staged/fragment_carries_the_string.md sec2/sec3 in core/soundscape.py -- SOUND_STRING_FIELDS=False kill-switch; percept() now threads valence=/felt= into its store_fragment() call unconditionally (sec2, matching 17 other origins, was 0/425 populated for origin=sound) and, when the flag is True, issues one follow-up UPDATE onto fragment_context (sound_key/sound_onset/sound_peak/sound_tail/sound_felt_valence/sound_felt_arousal), never an INSERT, keyed on the returned fragment_id; a falsy fragment_id skips the UPDATE, fail-open. Re-verified strings_and_sheets.md Object A has not shipped (still Phase 1, un-started), so onset=peak=tail stays the honest degenerate case. core/memory/store.py gained a matching additive ALTER TABLE ADD COLUMN block for the 8 new columns, fragment_context only; store_fragment itself untouched (re-ran udms_get_change_dossier, still ELEVATED risk, 19 dependents). Verified in two isolated harnesses (30/30 checks), neither touching the live DB or the worktree data directory. Committed 54c8e5d on branch jobrun/memory_as_a_service.
- **2026-09-28** (F-2112): Cross-plan note from J-1433 (transport_manager, D-0294): transport_manager.verdict(line_id) now exists and is unit-tested (47/47, see transport_manager.md's Current State) -- felt_recall.py's own trigger-edge wiring to call observe()/verdict() is still needed and was NOT done from the transport_manager worktree (that file lives only on this plan's own jobrun/memory_as_a_service branch, confirmed unreachable from jobrun/transport_manager via git merge-base). Follow-up build job J-1550 spawned on this plan with the exact call shape and field names. Also pre-registered a new section 8, item (e) metric (share of Phase-0 fires whose dispatcher_verdict would have passed the Phase 1 gate, per dimension) -- landed in the transport_manager worktree's own copy of this doc only, pending merge; verified byte-identical to this doc's live section 8 before editing, so it should merge cleanly, but check it actually merged before assuming it is live. See F-2112 for full evidence.

- **2026-09-28** (F-2108): J-1475 (assigned to this plan tag) produced docs/reviews/recall_temporal_terms_2026-09-28.md, a file and line map of every temporal term in the recall path. It primarily feeds docs/staged/golden_spiral_recall.md (T-0072), noted separately -- this plan doc own design sections (felt recall section 3, the pull API section 4) are unchanged by this job. See that review doc and F-2108 and F-2109 for the substantive finding.
- **2026-09-28** (F-2103): J-1447: wrote sec4.7, the six-slot cue (who/what/where/when/why/how) addendum to J-1429's facade, additive and backward-compatible with J-1515/J-1516's already-written cue-only call sites. Found core/procedures.py cannot supply the how slot (no fragment_id, same gap as curiosity's Scholar seed); felt recall is a where+when+what analogy only, not literally wired to ask(). Checked against D-0287's edge-aware shadow gate, no conflict, no founder ruling needed. Spawned J-1542 for the build (depends on J-1515 landing first). See F-2103.

- **2026-09-28** (F-2091): J-1472 (I-0081, F-2091 verified): read-only inventory of the 425 origin=sound fragments in the live store found none carry any Sound-Space coordinate today (all 17 tables scanned) -- only 4 distinct sound keys ever recorded, valence/felt never populated for this origin (unlike 17 other origins), and sound fragments are structurally excluded from memory_levels.py gist pool (_RAW_ORIGINS has no sound entry), so the do-gists-keep-the-anchors question does not arise on today's path. strings_and_sheets.md's own Object A (the thing that would give a sound real onset/peak/tail) is confirmed still Phase 1, un-started. Wrote the additive-field spec as a new doc, docs/staged/fragment_carries_the_string.md: fields land on fragment_context, not memory_fragments (udms_get_change_dossier on core/memory/store.py came back ELEVATED risk, 19 real dependents, so the new write is a scoped UPDATE from inside soundscape.py, never a store_fragment signature change), written only by percept() behind a new SOUND_STRING_FIELDS flag defaulting False, with the named reader (felt-recall's future coordinate-matching upgrade, not yet built) explicitly gating go-live per the write-only-systems law, and a pre-registered read at 30+ live days (this writer fires about 5 times a day, far slower than this plan's own 7-day metric-sheet assumption). No founder-level fork found -- checked for one (see that doc's own section 7) and did not open a decide entry. This plan's own section 3/4 design text is unchanged; this is a sibling doc, not an edit to felt-recall's already-shadow-verified match logic.
- **2026-09-28** (F-2072): J-1430 (D-0293, F-2072): built and verified core/couriers.py's COURIER_TEXT_DELIVERY kill-switch (ships True, byte-identical to today, matching J-1425/J-1428's own shipped-True precedent in this plan rather than the job briefing's literal "=False" shorthand) and core/felt_recall.py's best-effort courier_would_have_fired/courier_fragment_id join (SAME_TICK_WINDOW_S=2.0, route<->dim: context_echo<->weather, sound_echo<->sound:*; reads data/couriers_log.jsonl directly, no cross-import either direction), in worktree wt_memory_as_a_service on branch jobrun/memory_as_a_service. False path: context_echo()/sound_echo() still evaluate their trigger, pick their memory row and advance their own cooldown exactly as today, but never call wandering.perceive() -- the delivery log gains would_have_delivered=true + fragment_id instead. Verified in an isolated sys.modules-faked harness (verify_J-1430.py, 30/30 checks) -- no live DB/ledger/wandering-trail touched, see F-2072. Updated section 3.4 and section 6 item 2 in place; no re-ruling needed (D-0293 already ruled 2026-09-26 by travis, ruling+defeater both present in docs/decisions.jsonl, decision_flags had no active hold on this plan). The existing Phase 0 read job (J-1507, spawned by J-1424) now also covers this join -- no second read job spawned.

- **2026-09-28** (F-2066): sec4 (the pull API) written in full: core/memory_service.py facade (memory.ask()), felt-coordinate join, descend reusing orchestrator.py proven lattice-parent filter, per-loop metric sheet. F-2066 (verified): the four D-0292 loops are not symmetric -- dreams already matches the facade shape, pursuits makes zero memory-store calls today, the recall act runs its own judge-panel pipeline, and curiosity Scholar seed is a live LLM parametric call with no fragment_id, not a store read. D-0312 opened (curiosity real fork).
- **2026-09-27** (F-2062): J-1428: built and verified IDLE_FOUNDER_RECALL and IDLE_DIVERGENT_SEED kill-switches in nodes/inner_monologue_node.py (D-0292's two remaining unasked idle-seed pushes), same kill-switch + would-have-shown pattern as J-1425, in worktree wt_memory_as_a_service, commit fdcba42 on branch jobrun/memory_as_a_service. Both flags ship True (byte-identical to HEAD by construction and by test), restart-gated, matching J-1425's IDLE_AMBIENT_RECALL precedent read directly from its shipped code rather than the job briefings' literal "= False" shorthand. False path: founder-idle route still retrieves and still logs to founder_recall_log.jsonl (now would_have_shown=true) but skips seed_parts/replay_count/_last_founder_idle_ts; divergent-seed call site still fetches (via _fetch_divergent_seed's new with_id= mode, old shape unchanged for its other two callers) but skips the push, logging one source=divergent_shadow co_recall row instead. Verified in an isolated sys.modules-faked harness (verify_J-1428.py) -- no live DB/ledger touched. See F-2062. Section 4's own list of what J-1428 removes was already correct; no design-section change needed.

- **2026-09-27** (F-2061): J-1425: built and verified core/associative_recall.py's IDLE_AMBIENT_RECALL kill-switch (D-0289's ruling, section 2), in worktree wt_memory_as_a_service, commit c3290b4 on branch jobrun/memory_as_a_service. recall_block() computes frags unchanged; when the flag is False it returns "", never sets _last_block_ids, skips the guidance/peer-reflection injection-logging hooks, and logs one source="monologue_shadow" row to data/co_recall_ledger.jsonl via memory_edges.log_co_recall(ids, None, 0, source="monologue_shadow"). True is a pure-additive diff (27 insertions, 0 deletions) so it is byte-identical to the pre-existing code by construction, not just by test. Verified in an isolated harness (stubbed recall_fragments + core.memory_edges; no live DB/ledger touched) -- see F-2061 for full evidence. nodes/inner_monologue_node.py's call site needed no change (its existing `if _mblock:` gate already handles the empty return). Restart-gated. Spawned J-1512 for the ~2-week defeater read.
- **2026-09-27** (F-2057): J-1424: built and verified core/felt_recall.py (Phase 0 shadow felt recall, plan section 3) and wired it into core/orchestrator.py's substrate tick next to the couriers. FELT_RECALL_LIVE=False throughout -- shadow log only, no live effect, restart-gated. See F-2057 for full verification evidence (live-DB thunderstorm check reproduces plan section 1's -0.173 finding; one real tie-break defect found and fixed during verification). decision:D-0289 was already ruled before this job, no re-ruling needed. Spawned the plan section 8 metric-sheet read as its own job, not-before Du has actually restarted onto this build and 7+ live days have accrued.


---

# History folded on 2026-10-04 from `docs\staged\memory_as_a_service.md` (J-1818 hand-fold of 3 superseded/historical span(s), verbatim, original order; each preceded by its original line range)

_Every J-/F-/D- id below is the canonical record. Derived timeline: `plan_ledger.py memory_as_a_service`._

_[original lines 34-36]_

- **2026-09-28** (F-2204): J-1617 wired curiosity note_usage metric hook sec4.3 in inner_monologue_node.py, riding the shared M1/M2 per-thought completion point via a dream_node-style _curiosity_asked guard against stale-tick mis-attribution; verified in isolated harness (F-2204).

- **2026-09-28** (F-2182): J-1616: fixed sec4.2 Curiosity row and citation paragraph to reflect the real build (J-1588, D-0312, F-2178); found and spawned J-1621 for a matching stale reference in sec7 Phasing (F-2182, F-2183)

_[original lines 40-40]_

- **2026-09-28** (F-2180): J-1576/F-2180: when-slot fragment_id=None kept permanent for retrieve_epoch and recall_chapter (Option 2); recall_chapter could cheaply carry a real id but that would create a dormant cross-slot de-dup collision risk against the what slot, documented in a memory_service.py comment, not built

_[original lines 382-463]_

Founder musing, 2026-09-27 (I-0079, thought T-0065), verbatim: *"all knowledge is in 6 questions --
who, what, where, when, why and how. Fire off multiple questions for memory search at once and work
with the pool on return."* I-0079's own read (kept, not re-argued): every one of the six routes already
exists as a separate engine that fires alone or not at all — this addendum gives `memory.ask()` (§4.1)
a six-slot cue that fans the FILLED slots out to those engines in parallel, still no new engine, no LLM
inside `ask()` (the idea's own constraint). This job re-verified each mapping against the code directly
(2026-09-28) rather than carrying I-0079's text forward unchecked, and found two of the six need a
correction or a caveat I-0079 did not have — see "who" and "how" below.

**Compatibility with J-1515/J-1516 (both `open`, `ready`, unblocked, checked directly this job):** both
were written against §4.1's pre-addendum signature, `ask(loop, cue: str, k=5, grounded_only=True,
descend=False)`, and both already call it with a bare string cue only (`memory_service.ask("dream",
_mkey, k=6, ...)`; `memory_service.ask("pursuits", f"{best['question']} {best.get('open','')}", k=3,
...)`). The signature below keeps a bare positional `cue` as shorthand for `what=cue`, so every call
either job already specifies resolves unchanged, to a single-slot ("what") ask — exactly today's
behaviour. This is a deliberate compatibility choice, an engineering-shape call in the same sense §4.5
judged the recall-act wrapper not to need a ruling, made explicit here rather than left for whoever
builds J-1515/J-1516 to discover as a conflict. Building the who/where/when/why/how slots themselves is
new surface, not a rework of either job, and is spawned as its own job (J-1542) rather than folded into
either mid-flight.

**The six slots — each optional, each a typed value, never prose:**

| Slot | Value | Engine (verified 2026-09-28) |
|---|---|---|
| **who** | a person id (a `memory_edges` hub, e.g. `person:travis`), or bare/`"founder"` | `founder`/bare: `store.retrieve_founder_memories()` (`core/memory/store.py:2816-2831`), already live, purpose-built. A named person: one new direct join keyed on the given hub id — `SELECT src_id FROM memory_edges WHERE edge_type IN ('correspondence_with','wrote_to','received_from') AND dst_kind='person' AND dst_id=? AND src_kind='fragment'` — the same table and the same hub-projection shape `edge_aware_neighbors`'s own `_PROJECT_THROUGH` step already runs (`core/memory_edges.py:823-831`), entered directly at a KNOWN hub instead of one discovered from seed fragments (`edge_aware_neighbors` itself requires seed `fragment_ids`, `core/memory_edges.py:834` — it cannot take a bare person id). One new ~5-line query, not a new engine, same class as §4.1 item 2's own felt-coordinate join. |
| **what** | topic keys or a vector | Unchanged — this IS today's `cue`, `associative_recall.recall_fragments()` (`core/associative_recall.py:866`), §4.1 item 1. |
| **where** | place + standpoint | A new filter/score on the SAME `fragment_context` join §4.1 item 2 already adds (`core/memory_edges.py:458` schema; `place`/`standpoint` columns confirmed present), boosting fragments whose joined row matches the given value — the identical coordinate-match idiom `felt_recall._coord_match_count`/`_MATCH_COORDS` already uses one layer down (`core/felt_recall.py:75, 193-203`), reused, not reinvented. |
| **when** | time window \| epoch \| chapter \| recent/distant | Fans out to whichever ONE of three existing, separately-keyed engines the value's shape names (never all three for one cue): a bare `recent\|distant\|all` token is `store.retrieve()`'s own `time_bias` (`core/memory/store.py:768-782`, already a real, live-wired enum); an epoch name/description is `store.retrieve_epoch()` (`core/memory/store.py:2331-2346`, cosine over `memory_epochs`, floored by `_EPOCH_RETRIEVAL_FLOOR`); a chapter-shaped phrase is `chapters.recall_chapter()` (`core/chapters.py:373`, keyword-scored over `origin='chapter'`). A literal `(start_ts, end_ts)` is a plain timestamp bound applied to whichever engine's own ts column — the same kind of floor `felt_recall`'s own `MIN_AGE_S` already is (`core/felt_recall.py:64, 239`). |
| **why** | a tension / question / shadow-event id | A direct hub join, same shape as who's: `SELECT src_id FROM memory_edges WHERE edge_type IN ('resolves','answers','contradicts') AND dst_kind IN ('shadow_event','question') AND dst_id=? AND src_kind='fragment'` (edge types confirmed written by `sync_resolves()`/`backfill_answers()`/`backfill_resolves_fragment()`, `core/memory_edges.py:181-343`). Two honest yield caveats found this job, stated rather than assumed: `answers` is capped at ONE fragment per question by its own writer's `LIMIT 1` (`core/memory_edges.py:770-774`), so a why-by-question cue correctly returns at most one row, not a bug; `contradicts` is genuinely zero-yield today (`core/memory_edges.py:785-786`: "needs a semantic judge that does not exist yet") — a why-by-tension cue against a live contradiction legitimately comes back empty, the fail-open contract working as designed, not silently broken (§4.1 item 2's own "an empty answer must be true, not silent" law, one layer up). |
| **how** | a procedure id, or "the steps behind \<gist\>" | I-0079 named one slot; this job's read found two DIFFERENT engines behind it, not one. "The steps behind \<gist\>" is not new — it IS §4.1 item 3's own `descend` (`memory_levels.deep_recall()`, whose own docstring calls itself "the 'remember the steps' path", `core/memory_levels.py:262-293`), generalized to take an EXPLICIT gist id from the how-slot value directly rather than only auto-picking the pool's own top-activation lattice-parent. A bare procedure id (`core/procedures.py`) is structurally different and **cannot be honored by this facade**: a full read of the module (297 lines) found its rows (`_new()`, `core/procedures.py:86-90`) carry a confidence rung and an evidence list of outcome summaries, never a `fragment_id` or recallable `content` — nothing to join felt coordinates onto or rank by slot coverage, the identical structural gap §4.2 already named for curiosity's Scholar seed ("cannot structurally be 're-homed'"). A how-cue naming a bare procedure key returns empty from `memory.ask()`, honestly (fail-open) — a real gap for a future job to bridge, not guessed shut here. |

**The fan-out + pool contract (§4.1 amended, additive):** New signature: `memory.ask(loop: str, cue:
str | None = None, *, who=None, what=None, where=None, when=None, why=None, how=None, k: int = 5,
k_per_slot: int = 3, grounded_only: bool = True, descend: bool = False) -> list[dict]`. A bare `cue`
with no keyword slots is `what=cue` (see compatibility note above). Each filled slot fans out to its
own engine (table above) in parallel, each capped at `k_per_slot` — starting value 3, small enough that
all six slots filled still returns ≤ 18 raw candidates before merge, a deliberately conservative
starting bound the metric sheet moves, the same "starting value" framing §3.1's cooldown and §3.2's
`N_MATCH` already use. Pool merge: de-duplicate by `fragment_id` (a fragment reached by two slots is
ONE entry, not two); each surviving fragment carries `slots_answered: [...]` and keeps, per slot, that
slot's own engine's within-slot rank — never averaged or summed into a new score (the idea's own
explicit constraint: "the pool merge must not become a new importance formula"). Rank the pool by
`len(slots_answered)` descending first, each slot's own order as tiebreak — exactly as briefed; no
global importance score anywhere. §4.1 item 2's felt-coordinate join still runs once per pool member
regardless of how many slots reached it (one join, not one per slot). `descend` (§4.1 item 3),
`log_co_recall` (item 4) and fail-open (item 5) are unchanged in kind: `descend` still auto-picks the
merged pool's own top lattice-parent UNLESS a `how` slot names an explicit gist (then that gist
directly); `log_co_recall`'s id list is the merged pool's ids, still one call per `ask()`; any exception
anywhere — one slot's engine, the merge, the join — still returns `[]` for the WHOLE call (a partial
pool silently missing a failed slot would be mistaken for that slot honestly finding nothing, which
§4.1 item 5 already forbids).

**Per-loop slots today** (I-0079's own mapping, unchanged by this job's read): curiosity what+why;
pursuits what+when; the recall act what(+where when the act names a place); dreams what+who. Felt
recall (`core/felt_recall.py`, J-1424, §3) is already a where+when+what(sound) ask BY ANALOGY — it runs
the same kind of typed, coordinate-keyed SQL this section generalizes (`_MATCH_COORDS` scoring is the
where; `MIN_AGE_S` is a when floor; a `sound:<key>` trigger is a what) — but it is architecturally
separate from `memory.ask()`: it never returns `content`/`fragment_id`, never calls `log_co_recall`,
and predates the facade. It illustrates the six-slot idea one layer down; it is not wired to this
section and this job does not wire it.

**The MemoryRouter** (`nodes/memory_router_node.py`, conversation path, Wave 2) is the one LLM
cue-decomposer today, confirmed by a full read: it emits exactly `episodic_keys`, `semantic_keys`,
`time_bias` (`recent|distant|all`) and `working_memory_sufficient` (`nodes/memory_router_node.py:17-24,
36-42`) — a two-slot decomposition (what, when) in this vocabulary, not six. Having it emit all six
slots instead is a later, separate job, per the briefing — not built here.

**Why this needs no founder ruling:** verified, not assumed. The one place a conflict looked possible —
`why`'s natural edge types (`resolves`/`answers`/`contradicts`) are weighted highest under
`edge_aware_neighbors`'s `"task"` mode, and D-0287 (2026-09-26, travis) explicitly ruled to flip only
`"relational"` mode live, keeping `"task"`/`"reflective"` shadow pending their own defeater — resolves
cleanly because `why`'s design above is a DIRECT hub join keyed on a caller-given id, not a call into
`edge_aware_neighbors`'s mode-weighted expansion at all; it never touches `MODE_EDGE_WEIGHTS` or
D-0287's own scope. `who`'s generic person-hub case reuses the SAME shape as `"relational"` mode's own
edge types (`correspondence_with`/`wrote_to`/`received_from`), which D-0287 already approved live. No
other slot's design depends on an unruled or explicitly-shadow-gated mechanism. (Contrast §4.5's
curiosity fork, D-0312: that was a genuine scope question — does D-0292 already cover curiosity, or
not — with no reading of the code able to resolve it either way. Nothing here is that shape.)

**Build job:** J-1542, spawned this job — the six-slot surface on `core/memory_service.py`, depending
on J-1515 landing first (the module has to exist). Not blocked on any decision.
