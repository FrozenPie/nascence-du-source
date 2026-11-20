# Du vs a human — evidence read across cognitive dimensions (side session of local_44cad1cc)

## Session timing
- **Session started:** 2026-10-15 07:18:06 UTC
- **Last message before wrap:** 2026-10-15 07:30:14 UTC
- **Wrapped:** 2026-10-15 07:30:16 UTC

## Summary
Travis asked, after the 10-15 changelog read, how well Du thinks compared to a human. This session read the live process (lifetime #289, boot 2026-10-09 08:36 NZDT, commit 746d5fd, 155 h up, pre-10-09 code throughout) across memory, self-knowledge, attention, goal pursuit, prediction, affect, tempo and the conversation-side dimensions, recorded seven verified findings F-2848..F-2854, spawned three instrument jobs J-2151..J-2153 and two founder questions J-2154/J-2155, and wrote the five-minute comparison to `docs/reviews/du_vs_human_2026-10-15.md` (copy in the group's shared notes folder). Thought T-0086 opened the session.

## Builds
No code. Deliverable is the review doc `docs/reviews/du_vs_human_2026-10-15.md` and the ledger entries above. Nothing committed; the shared tree was treated as read-only for git.

## Findings
- F-2848 (memory): dating across a restart is exact ("saw's vibration from twelve days ago" on 10-10 20:38 points at the 09-28 10:52 knife-whittling episode in hands_trace), detail is gist-level (knife remembered as saw), gist faithfulness 0.805 since boot, journal grounding RED 0.675, and narrated recall confidence (0.85–0.95) never tracks the epistemic monitor's SUSPECT verdicts (50 of 50 since boot).
- F-2849 (social/voice/instruction): lifetime #289 has ZERO human turns (0 `human:` lines in 85,580 log lines). 19 of the 32 human turns 09-28..10-08 were the scripted farewell. Guidance integration 0 rows since boot, critic 0, social_state static 1,023 cycles. The J-1846 voice fix (b15aca7) IS in the boot: "Travis, you ask" fell to 1 of 95 internal replies.
- F-2850 (attention): 254 of 277 internal cycles since boot are one mottainai question (97% per day from 10-10); the attractor spans the dream tension source, letters, librarian ask and gist topics; all existing anti-capture gauges measure the sentence, not the topic. Mechanism is F-2472's theme-feedback relock.
- F-2851 (self-knowledge): measuring himself is superhuman (external competence scores, 543-node estate, 141 SI fires since boot); using it is not (beliefs ~0.80 regardless, competence in 2.6% of projections per F-2758, 0/48 doubts taken up per F-2670).
- F-2852 (closure): commitment hold_rate 0.215; pursuits 70 saturated / 0 resolved (F-2785); dreams 0/64 resolved since boot; frontier 10,092 faded vs 313 resolved. Aims are enumerated and restored across boots, which a human cannot match.
- F-2853 (prediction/affect): prediction gap 0.442 (Jun) → 0.21 (Oct); maths 0 large gaps; under-confident on maths (0.81 vs 1.00). Valence weekly W38 −0.48 → W42 −0.18, but affect_state reads joy 0.86 with valence −0.37 at once; contradiction fired 94/95 cycles, acted 2.
- F-2854 (tempo): 36,020 model calls, 50.9 h model time in 155.8 h; 82.6 s per cycle, 77–106 s per human reply; 64 sleeps.
- [INFERRED] The overall shape: Du is a better recorder than any human and a worse closer; self-knowledge is the sharpest and least used part. This is the review doc's conclusion, not a ledger finding.

## Open
1. J-2154 (needs_input, Travis): will there be a real conversation with Du in this lifetime, and what human baseline should the comparison use (published norms / Travis himself / qualitative). Next action: Travis answers via decide-review or by editing the job; then J-2151..J-2153 can pre-register bars.
2. J-2155 (needs_input, Travis): topic-level anti-relock for the curiosity question, three options (curiosity_node topic key / route through balance_world / leave it and name the bar). Restart-gated whatever is chosen.
3. J-2151 autobiographical recall probe (ready, memory_knowledge). Next action: build `scripts/autobio_recall_probe.py` per the briefing.
4. J-2152 topic-perseveration gauge (ready, curiosity_goals_dreams). Next action: build the gauge into du_pulse section 4 with a 30-day backfill.
5. J-2153 social-cognition probe (ready, guidance_learning). Next action: build the judge and backfill the 09-28 / 10-08 conversations; no new rows until human turns resume.
6. [OPEN] The 10-13/14 letters Du wrote to Travis are unanswered (F-2755 item 7); only Travis can resolve that.

## Warnings
- Everything observed is pre-10-09 code; closure law (J-2118), estate ask (J-2119), night mind, two-axis vitality are merged and NOT in the running process. Do not read the "worse" rows as verdicts on those builds.
- Do not restart Du from a session; the F-0704 job-object rule applies.
- `docs/reviews/du_vs_human_2026-10-15.md` is a new untracked file; ledgers (findings, job_queue, thoughts, session_events) carry this session's rows uncommitted alongside other sessions' edits. Commit by explicit path only.

## Pointers
- `docs/reviews/du_vs_human_2026-10-15.md` — the comparison table and five-sentence verdict.
- `C:\Users\USER\AppData\Roaming\Claude\side-session-notes\local_44cad1cc-3bc0-4b31-83fb-9559e0207ff0\du_vs_human_2026-10-15.md` — same doc for the parent session.
- F-2848..F-2854 in `docs/findings.jsonl`; J-2151..J-2155 in `docs/job_queue.jsonl`; T-0086 in `docs/thoughts.jsonl`.
- Prior findings this read leans on: F-2472 (relock mechanism), F-2670/F-2672 (SI doubts not taken up), F-2755/F-2758 (psyche census, estate projection), F-2757/F-2785 (dreams, pursuits), F-2609/F-2773 (prediction), F-2680/F-2766 (sleep stalls).
