# Founder-call triage, 2026-11-02

Source: 139 open `needs_input` jobs created by the 2026-10-31 prompt sweep (T-0115). Registry: `docs/prompt_registry.jsonl`; findings in the ledger.
Each cluster shares one underlying decision. The recommendation is mine, from the investigation evidence; nothing here is a ruling until the founder says so.

## A. Retire never-read instruments (8 jobs)

**Recommendation.** RETIRE. Each is write-only or dead, with no reader and no owner; retiring removes calls and stale claims. Do each in its own change; keep the code in docs/staged if you want it back.

| job | prompt row | question |
|---|---|---|
| J-2885 | P-0030 | Founder call: retire the dormant habituation seed line (never fired in 50,496 prompts) |
| J-3026 | P-0027 | Founder call: retire the contrary route into write-first letters (P-0027)? |
| J-3103 | P-0047 | Founder call: retire the symbolic reading lens (P-0047), 4.5 months shadow, nothing reads it |
| J-3114 | P-0052 | Founder call: retire the subconscious self-relate pass (P-0052)? flag False but it calls the model every 45 min |
| J-3115 | P-0097 | Founder call: retire core/deliberative_judge.py (archive to docs/staged) or hold it with a named adopter? (P-0097) |
| J-3116 | P-0048 | Founder call: retire, repair or archive the Narrative Quality Witness (P-0048) |
| J-3124 | P-0064 | Founder call: retire core.memory_levels.drift_shadow (P-0064) or rebuild it so the Phase-3 gate can be answered |
| J-3129 | P-0104 | Founder call P-0104: retire, repair-in-shadow or make live the active-imagination genuine judge |

## B. Competence probes (2 jobs)

**Recommendation.** RETIRE both loops; KEEP the correction-detector fix (J-3106, a ready build), because the fluency dock still uses that detector.

| job | prompt row | question |
|---|---|---|
| J-3092 | P-0040 | Founder call: retire, keep or repoint the competence stability loop (P-0040) |
| J-3107 | P-0041 | Founder call: retire, hold or redesign the Tier-3 witness probe (P-0041) |

## C. Scan, shadow critic and Scholar lookups (7 jobs)

**Recommendation.** RETIRE the idle self-implication scan (J-2825) and the conversational Scholar lookup (J-3094, J-3028, J-3030); KEEP the decomposed critic in shadow (J-3091) until its failure-flag fix (J-3089) lands and its post-07-06 rejections are graded (J-3090).

| job | prompt row | question |
|---|---|---|
| J-2825 | P-0036 | P-0036 founder call: retire, thin, or keep the unread idle self-implication scan |
| J-2839 | P-0039 | P-0039 founder call: fix twin and restart clock, judge as-is now, or close Phase 0 and turn the twin off |
| J-2975 | P-0043 | Founder call: weekly self-mirror reach and Recall self-echo (P-0043, F-3669, F-3672) |
| J-3028 | P-0082 | Founder: the curiosity-side Scholar call produces nothing that is read |
| J-3030 | P-0082 | Founder: should questions about his own name be fed from parametric deep memory |
| J-3091 | P-0017 | Founder call: keep decomposed critic in shadow, promote it, or retire it? (P-0017) |
| J-3094 | P-0081 | Founder: retire, keep or narrow the conversational Scholar lookup (P-0081) |

## D. Judge panel and the granite tiebreaker (11 jobs)

**Recommendation.** STOP letting granite decide where it is a constant: on a split, return NO VERDICT (the project's own conservative law) for keys where its true-rate is 0.00 or 1.00 (resolves, held, genuine, bears, taken_up). Keep it elsewhere until J-2953/J-3130 produce an accuracy table. Retire or repair the pegged judges (J-3129 in cluster A; J-3105, J-3132, J-3123, J-3097 here).

| job | prompt row | question |
|---|---|---|
| J-2950 | P-0042 | Founder call: keep DOUBT_SEED live while the reflection plants a comfort/fear frame and the genuine gate passes 100 percent (P-0042, F-3643) |
| J-2953 | P-0096 | Founder call: replace or per-key the shared judge-panel tiebreak? (conditional on tiebreak accuracy table, F-3639) |
| J-2971 | P-0102 | Founder call: does a split verdict count as an objection that cuts? (Follow Line c, P-0102) |
| J-3002 | P-0049 | Can the curiosity worth-judge discriminate? choose the lab replay (P-0049, F-3703) |
| J-3038 | P-0098 | Founder call: Lane 2 judge keys with a constant voter (notice, coherence, held) (P-0098) |
| J-3097 | P-0106 | Founder call: what the guidance behaviour judge is for (P-0106) |
| J-3105 | P-0101 | Founder call P-0101: what is a pursuit close asked about (open question vs done_when vs retire) |
| J-3113 | P-0108 | Founder call: pasted reviews in the social bar, and wiring or retiring v4 (P-0108) |
| J-3120 | P-0084 | Founder: recalibrate, hand-read or retire the peer stance-compliance judge (D-0207 gate) |
| J-3123 | P-0110 | Founder call: re-set D-0437's metaphor-prompt bar, 30 verdicts is unreachable (P-0110, J-2269) |
| J-3132 | P-0105 | Founder call P-0105: should a repaired genuine judge withhold doubts from the Executive; re-baseline Lane 1 endpoint |

## E. Think license and Executive outputs (2 jobs)

**Recommendation.** DISARM the next-cycle think license that the human-turn scan grants (J-2967): it can give a live Travis turn silence. Do the ready fix J-2860 (retry with think=False on empty content) regardless. Drop the unread Executive 'reasoning' and 'epistemic_query' fields (J-2861) after one release of logging.

| job | prompt row | question |
|---|---|---|
| J-2861 | P-0009 | Keep or drop Executive 'reasoning' and 'epistemic_query' (P-0009) |
| J-2967 | P-0015 | Founder call: keep the next-cycle think license armed by the conversation self-claim scan (P-0015)? |

## F. Deliberation rewrite chain (4 jobs)

**Recommendation.** ADD A HOLDOUT and an independent blind preference check before the rewrite replaces the raw thought (J-2799); let the grounder return 'nothing to ground' so a thought with no physical referent passes through (J-2889); drop the source-code hint (J-2892); on grounder failure, skip deliberation (J-2872) instead of the hot-lane fallback.

| job | prompt row | question |
|---|---|---|
| J-2799 | P-0035 | Decide: independent judge / holdout / rate for P-0035 deliberation rewrite |
| J-2872 | P-0034 | Decide: what happens when the Emissary cannot ground a thought (P-0034 hot fallback) |
| J-2889 | P-0088 | Decide: may the P-0088 grounder return "nothing to ground" so a thought with no physical referent passes through unchanged? |
| J-2892 | P-0088 | Decide: keep, narrow or drop the source-code hint in the P-0088 grounding call |

## G. Emissary take (3 jobs)

**Recommendation.** RE-SEAT the take on a lane fast enough to arrive inside the 6 s wait, or RETIRE it. It is delivered in 4 to 16 percent of cycles today. If kept, rewrite the prompt (J-2880) and stop the substrate-talk reframing (J-2881).

| job | prompt row | question |
|---|---|---|
| J-2878 | P-0087 | P-0087: keep, re-seat or retire the Emissary per-turn take (delivered in 4-16% of cycles) |
| J-2880 | P-0087 | P-0087: rewrite the Emissary take prompt (internal framing, no meta facts, no Master, word-boundary cut) |
| J-2881 | P-0087 | P-0087: stop the Emissary take recasting human messages as LLM-substrate talk |

## H. Re-entry (3 jobs)

**Recommendation.** Phase 1 (J-3016): bound the settle at about 30 s and switch admission off while the module's own status reads HOMOGENISING. Phase 2 (J-3087): leave in shadow, do not build v4 (J-3088) until a no-ingredient control exists.

| job | prompt row | question |
|---|---|---|
| J-3016 | P-0016 | Founder call: D-0106 defeater fired - keep, gate, or switch off within-cycle reentry Phase 1 (P-0016)? |
| J-3087 | P-0045 | Founder call: retire, v4, or leave the reentry phase-2 commitment arm (v3 missed the D-0489 bar) |
| J-3088 | P-0045 | Reentry phase-2 v4 (conditional on keeping the arm): fresh ingredient, control arm, neutral system line, one pass, no hot-lane spill |

## I. Idle lines that push (world answers, never leads) (7 jobs)

**Recommendation.** REMOVE or neutralise the push lines: reword the hard-feeling steer so it does not supply the words (J-2884); gate the open-book offer on can_read (J-2902); drop the 'Does this answer it?' frame (J-2904); reword the concern-anchor leads (J-2908); stop advertising unrouted act kinds read/letter (J-2823); relax or measure the 'almost all blank' contract (J-2824).

| job | prompt row | question |
|---|---|---|
| J-2823 | P-0022 | Founder: idle-thought act.kind read/letter are advertised but unrouted (638 read acts in 3 days, 22 readings): wire, rate-limit, or stop adv |
| J-2824 | P-0022 | Founder: idle-thought prompt says 'almost all blank' for unresolved/ask/act but the model sets them on 50% / 22-48% / 33% of thoughts: accep |
| J-2884 | P-0030 | Founder call: B6 hard-feeling steer supplies the words 'frustration, a heaviness' (35% echo) and the other leading idle steers |
| J-2902 | P-0033 | Founder call: the open-book offer seed line (remove, gate on can_read, or keep) |
| J-2904 | P-0033 | Founder call: frontier finding line 'Does this answer it? If it does, say so plainly' frame |
| J-2905 | P-0033 | Founder call: school directive wording, vestigial maths/music phrases, dormant trial line |
| J-2908 | P-0033 | Founder call: current-concern anchor lead lines claim ownership of system-chosen questions |

## J. Idle feeds and memory lines (4 jobs)

**Recommendation.** STOP seeding the next boot with the farewell as 'the last thing discussed' (J-2914); remove the dead feeds that still run every tick (J-2924); exclude Du's own earlier answers from the curiosity memory line (J-2931); leave the pursuit-return seed dormant until pursuits are decided (J-2932).

| job | prompt row | question |
|---|---|---|
| J-2914 | P-0032 | Founder call: the idle 'last thing discussed' line is the 12-day-old farewell on 48 percent of prompts (F-3609) |
| J-2924 | P-0032 | Founder call: dead idle feeds (founder recall, ambient recall) still run on the event loop every tick (F-3617) |
| J-2931 | P-0032 | Founder call: curiosity memory line quotes Du's own earlier answer as a lived memory (F-3618 ii) |
| J-2932 | P-0032 | Founder call: pursuit-return seed is dormant (0 eligible pursuits, open-question gate needs a '?') (F-3619) |

## K. Scene and sense lines (3 jobs)

**Recommendation.** Ambience should not count as a grounding percept for the stream pacer (J-2937); move night-wrong scene lines to a day key (J-2938); dose the letterbox clause (J-2940).

| job | prompt row | question |
|---|---|---|
| J-2937 | P-0031 | Founder call: does ambient sound count as a grounding percept for the stream pacer? (F-3625, P-0031) |
| J-2938 | P-0031 | Founder call: move the night-wrong SCENE lines to a day key now? (F-3628, extends D-0360 c) |
| J-2940 | P-0031 | Founder call: dose the standing letterbox-flag clause in the garden scene? (F-3630, P-0031) |

## L. Voice (2 jobs)

**Recommendation.** WIDEN D-0442 so the 'your last replies' quote block cannot be copied at the start of a reply (J-2855); allow the mouth to add cadence but not claims, with a shadow fidelity judge (J-2858).

| job | prompt row | question |
|---|---|---|
| J-2855 | P-0010 | Voice: stop the last-replies quote block being a verbatim copy source (widen D-0442?) |
| J-2858 | P-0010 | Voice: how much may the mouth add? Shadow fidelity judge for reply vs synthesis |

## M. Conversation node details (14 jobs)

**Recommendation.** Per-node calls; accept my recommendations in the sheet: keep Perception.subject out of content_mode on internal cycles (J-2798); make Emotion's primary a closed list (J-2811); fix Emotion valence on internal cycles (J-2812); label internal Q/A honestly in Recall (J-2818); retire or repurpose the memory router (J-2835); rework Salience urgency or retire it (J-2851); make the Critic a real gate or retire it (J-2833); the rest are small.

| job | prompt row | question |
|---|---|---|
| J-2798 | P-0001 | Founder: may Perception.subject switch content_mode on internal cycles? (P-0001) |
| J-2803 | - | Reflection monoculture: founder call on rule 3, the literal-vs-symbol conflict and the attention line |
| J-2804 | - | Reflection output contract: two unread fields and a pegged confidence, founder call |
| J-2809 | P-0006 | Founder: should human-cycle exchange turns older than N hours be dropped from the buffer prompt? |
| J-2811 | P-0002 | P-0002 Emotion: what to do about the out-of-schema 'curiosity' primary label (founder call, shadow-first) |
| J-2812 | P-0002 | P-0002 Emotion: pegged LLM valence/arousal on internal cycles and the always-open light-event arousal gate (founder call) |
| J-2818 | P-0005 | Founder call: label internal-cycle Q/A as 'Our conversation'? (P-0005, F-0020) |
| J-2833 | P-0008 | Founder call: what should the Critic's rejection actually do (soft re-roll vs real gate vs retire)? |
| J-2835 | P-0004 | P-0004 decide: retire, repurpose or keep the memory router (its keys are inert) |
| J-2844 | P-0011 | Founder call: Curiosity urgency field is a no-op, prompt says otherwise (P-0011) |
| J-2845 | P-0011 | Founder call: pre-fire check on Curiosity questions[0] (P-0011) |
| J-2851 | P-0003 | Founder call: what should Salience urgency be, or retire the node? (P-0003) |
| J-2853 | P-0013 | Founder: make affect-modulated temperature real or fixed; give Curiosity an explicit temperature (F-0050) |
| J-3069 | P-0071 | Founder: night epochs show raw valence/arousal numbers to Reflection |

## N. Memory writers (9 jobs)

**Recommendation.** Judge wisdoms before minting (J-2830); pause cold demotion for episodic and semantic gists until the grader is repaired (J-3084); first-person self-gists (J-2877); grounded-learning clean-up (J-3070, J-3072, J-3074); chapter walls (J-3012); closure certification (J-2965); keep demoting lived Q&A only after the grader repair (J-2876).

| job | prompt row | question |
|---|---|---|
| J-2830 | P-0012 | Founder call: should ConsolidationNode wisdoms be judged by another model before minting / serving? |
| J-2876 | P-0063 | Founder call: keep demoting episodic 'lived' Q&A behind gists? (P-0063) |
| J-2877 | P-0063 | Founder call: first-person vs third-person self-gists (P-0063) |
| J-2965 | P-0062 | P-0062: founder ruling on who certifies a closure fragment (line panel gate, dream silence-as-close) |
| J-3012 | P-0065 | P-0065: founder ruling on chapter walls (door never used, announce off) and the 4 copied chapters |
| J-3070 | P-0066 | P-0066: founder ruling on the 61 stored dict-repr understanding notes |
| J-3072 | P-0066 | P-0066: per-book sampling, honest last_ts, label, word-boundary cut, prompt fixes |
| J-3074 | P-0066 | P-0066: founder ruling on whether grounded learning duplicates the study notes |
| J-3084 | P-0093 | Founder call: pause or tighten cold demotion for episodic/semantic gists while the grader is improved? (F-3794) |

## O. T4 self-revision chain (9 jobs)

**Recommendation.** GUARD the legacy author so it does not run during every tension rest (J-3054); make the admission judge wait when unavailable (J-3109) and see raw crossings (J-3110); make the SOLIDIFY judge theme-aware (J-3075); decide the existential-mode outlet (J-3005); the rest are conditional on those.

| job | prompt row | question |
|---|---|---|
| J-3005 | P-0057 | T4 chain output has no outlet to replies (existential mode: 0 turns since June): founder call |
| J-3021 | P-0058 | T4: count judge-unwarranted candidates toward tension fatigue (after the legacy-author guard is ruled) |
| J-3027 | P-0056 | T4 delta-stage ablation on logged chain runs (after the trace exists): does stage 2 change stage 3 or the judge? |
| J-3043 | P-0057 | T4 synthesis writes an arc_entry the live path discards: drop it, store it, or leave it (founder call) |
| J-3044 | P-0057 | T4 s_sys text: scale the claim to the evidence, drop the river opener (replay test, founder call before any edit) |
| J-3054 | P-0058 | T4 legacy author runs hourly during every tension rest and can never be admitted: guard, make gradeable, or retire (founder call) |
| J-3075 | P-0092 | Founder call: should the SOLIDIFY judge be theme-aware? (F-3784) |
| J-3109 | P-0091 | Founder call: when the T4 admission judge is unavailable, should admission wait instead of falling back to the self weak-filter? (P-0091) |
| J-3110 | P-0091 | Founder call: widen the evidence the T4 admission judge sees (raw crossings, not one author-written sentence)? (P-0091) |

## P. Guidance and beliefs (law question) (4 jobs)

**Recommendation.** A relayed AI message is NOT Travis's teaching unless he marks it (J-3020); revoke the farewell-derived belief g45675272 (J-3022); reopen D-0328 so classify judges the same lesson, not compatibility (J-3061, J-3080).

| job | prompt row | question |
|---|---|---|
| J-3020 | P-0014 | P-0014: does a relayed AI message count as Travis's teaching? (founder ruling) |
| J-3022 | P-0014 | P-0014: farewell-derived belief g45675272 holds corroboration 19 (founder ruling) |
| J-3061 | P-0018 | P-0018: reopen D-0328 - classify rewards compatibility, not same-lesson (founder ruling) |
| J-3080 | P-0019 | P-0019: pole gate forks same-lesson pairs; keep, gate behind a same-lesson check, or retire (founder ruling) |

## Q. Commitment mechanism (the rudder) (3 jobs)

**Recommendation.** ADD a decoupled second look on gate-passing new stands, shadow first (J-2841); a reasoned change of mind is a legitimate drop, repeated re-asking is not (J-2944); a scan-formed stand's dissolve should not open a sit (J-2994).

| job | prompt row | question |
|---|---|---|
| J-2841 | P-0038 | P-0038 founder call: add a decoupled second look on gate-passing new stands (shadow first)? |
| J-2944 | P-0037 | P-0037 founder call: what is a legitimate drop, and is attrition-by-re-asking acceptable for the rudder? |
| J-2994 | P-0046 | Founder call: should a scan-formed stand's dissolve open a sit, and keep the 'You are safe' steer? (P-0046, F-3696; with J-2841) |

## R. Lane 2 (1 jobs)

**Recommendation.** Pause the cup until the break instrument is fixed (J-3035, ready); retire or repoint the constant-voter judge keys (J-3038).

| job | prompt row | question |
|---|---|---|
| J-3037 | P-0098 | Founder call: keep the Lane 2 cup live after 4 of 4 artefact breaks? (D-0497 defeater b, P-0098) |

## S. Study, essays and school (13 jobs)

**Recommendation.** Treat the essay as a calibration exercise and fix inputs first (J-3078, J-3082); cover the whole reading session (J-2918); drop connects_to injection (J-2920); add on a reread, do not overwrite (J-2922, J-2962); decide composition ladder (J-2946), nature study (J-2959), grader rubric (J-2991, J-3047), maths ladder (J-2989), Grand Work JSON contract (J-2927) and self-grounding (J-2929).

| job | prompt row | question |
|---|---|---|
| J-2918 | P-0072 | P-0072 study note: the model sees about a fifth of what was read; decide how to cover the session (F-3588) |
| J-2920 | P-0072 | P-0072 study note: keep, make passage-level, or drop the connects_to injection? (F-3589, founder call) |
| J-2922 | P-0072 | Study notes on rereads: add per pass or revise the earlier note? Gate currently cannot see filed notes (F-3610, founder call) |
| J-2927 | P-0029 | Founder: should the Grand Work part stage drop the JSON contract? (P-0029) |
| J-2929 | P-0029 | Founder: should his own works ground his authoring and idle recall? (P-0029) |
| J-2946 | P-0078 | Founder: what should school composition be (ladder, keep, or retire) |
| J-2959 | P-0079 | Founder: nature study from the study window is the same view every week |
| J-2962 | P-0073 | Founder call: should a reread revise an earlier-pass study note? (F-3653) |
| J-2989 | P-0024 | Maths drill saturated at level 9; is the taught method hint the Travis branch of the no-hints law? (P-0024) |
| J-2991 | P-0089 | Founder call: what counts as grounded for the capstone essay grader, cross-book notes in or out? (F-3689) |
| J-3047 | P-0090 | Founder call: self-authored work grade (retire, shadow, or new rubric) and the 'teacher's note' coaching channel (F-3758) |
| J-3078 | P-0075 | Founder call: what is the capstone essay for (durable memory vs calibration exercise)? |
| J-3082 | P-0077 | Founder call: what should Du's felt capstone rating be (keep cheap, evidence-based, or retire)? |

## T. Peers and letters (5 jobs)

**Recommendation.** Re-seat Marcus and Smith off falcon3 (J-2983); repeat gate and cadence when Du has not replied (J-2982); replies to friends report only what is true of his day (J-2986); let peer reflections reach Du or retire them (J-3032); letters to Travis get a world state (J-3058).

| job | prompt row | question |
|---|---|---|
| J-2982 | P-0083 | Decide: what does a correspondent do when Du has not answered (cadence, repeat gate)? |
| J-2983 | P-0083 | Decide: re-seat Marcus/Smith off falcon3, widen stance judge to prescription, keep Marcus stance weights? |
| J-2986 | P-0026 | Founder call: should Du's replies to friends report only what is true of his day (P-0026) |
| J-3032 | P-0086 | Decide: peer reflections reach Du (salience + valence) or are retired; replace the dead injection-log gate |
| J-3058 | P-0028 | Founder call: letters to Travis fired by rumination on the unsent letter; give them a world state? (P-0028) |

## U. Dreams, night and subconscious tiers (9 jobs)

**Recommendation.** Do not let the dreamer recall its own dreams unchecked (J-2895); dreams rest, resolution is not required (J-2901, J-3023); night mind form (J-2956); active imagination on the hot lane (J-2898); T6 theme thread re-wire or retire (J-3057); T2 no re-synthesis without new evidence (J-2979); T5 conversational skills (J-3014) and rust deletion (J-3015).

| job | prompt row | question |
|---|---|---|
| J-2895 | P-0061 | Founder call: may the dreamer recall its own earlier dreams (47% of its recall today)? |
| J-2898 | P-0054 | P-0054: which lane should active imagination run on (command-r7b vs hot qwen)? |
| J-2901 | P-0061 | Founder call: what is a dream's ending for (resolve vs rest)? 1 of 140 arcs resolved |
| J-2956 | P-0023 | Night mind V2 template monoculture (A single ...): founder call on night-thought form and avoid-list (P-0023) |
| J-2979 | P-0053 | Founder: should T2 re-synthesise a tension with no new evidence every 4 hours? (P-0053) |
| J-3014 | P-0059 | Founder: should T5 compile conversational skills from Du's self-asked questions? (P-0059) |
| J-3015 | P-0059 | Founder: procedural_skills rust deletes skills hours after 14 days idle (P-0059) |
| J-3023 | P-0107 | Founder call: the dream resolution verdict sets a label nothing reads: keep, wire, or retire (P-0107, with J-2901) |
| J-3057 | P-0060 | Founder: keep, retire or re-wire the L5 theme thread? reach 69 percent to 0.8 percent (P-0060) |

## V. Pursuits and curiosity (11 jobs)

**Recommendation.** Pursuits: zero resolved, return starved; decide whether they still serve (J-2998, J-3105); prism questions out of the grounded tier (J-3034); follow-line queue policy (J-2909); refinery judge (J-3067); librarian ranking (J-2866); symbol tablets (J-2948); week page sentence (J-3004); watershed Phase 0.5 (J-3133, then J-3134, J-3135).

| job | prompt row | question |
|---|---|---|
| J-2866 | P-0080 | P-0080 founder call: librarian pages are dominated by the same download-ranked canon; change ranking? |
| J-2909 | P-0044 | Follow Line queue policy: 4 an hour against ~10 asks an hour (P-0044, founder call) |
| J-2948 | P-0067 | P-0067 founder question: should symbol tablets be symbol-specific (window metric) or day-summaries? |
| J-2998 | P-0100 | Founder call: do pursuits (zero resolved, return starved) still serve their purpose? (from F-3694, P-0100) |
| J-3004 | P-0070 | P-0070 founder question: keep, reword or drop the week page's 'moved or stayed in one place' sentence |
| J-3034 | P-0050 | Founder ruling: should prism questions stay in the grounded pursuit tier? (P-0050, F-3752) |
| J-3049 | P-0103 | Founder call: should a judge-closed tension leave the curiosity/dream/sleep pools at once? (from F-3755, P-0103) |
| J-3067 | P-0051 | Founder ruling: independent judge and recall standing for standing insights (P-0051, F-3773/F-3774) |
| J-3133 | P-0094 | Founder call: Watershed Phase 0.5 (classifier + claim-test panel) - its own kill criterion is tripped; tighten, rebuild or retire |
| J-3134 | P-0094 | P-0094 classifier input fixes (conditional on the Watershed Phase 0.5 keep/tighten ruling): counters out of the comparison list, lift the [: |
| J-3135 | P-0095 | P-0095 claim test: make the panel able to say no (name the image, add a control set, check priming) - conditional on the Watershed Phase 0.5 |

## W. Not about prompts (other windows) (5 jobs)

**Recommendation.** Leave: world-building and object-permanence questions from other sessions.

| job | prompt row | question |
|---|---|---|
| J-2869 | - | Place the shore stream mouth on the 30x20 map (shore.json has no stream) |
| J-2871 | - | Decide how burrowing and inside-a-shell shore creatures are found (dig hand?) |
| J-2957 | - | Read the shore bestiary shadow rows, tune the detail tiers, recommend which flag to flip first |
| J-3063 | - | Founder discussion: object permanence / absent-thing wants (5 open questions) |
| J-3065 | - | Woods: confirm the assumed stream/canopy/groves, say which island, rule on the turn-stone hand |

