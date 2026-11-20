# Du morning pulse, retired-mirror and known_text audit findings, known_text arm reader built

## Session timing
- **Session started:** 2026-11-14 17:35:48 UTC
- **Last message before wrap:** 2026-11-14 19:13:57 UTC
- **Wrapped:** 2026-11-14 19:13:58 UTC

## Summary
Morning check on Du (2026-11-15 NZ time) after the overnight job-run: Du is live and healthy, but the overnight builds are not loaded yet. Two liveness-audit alarms (behavioural mirror stale, known_text arm NEVER) were traced to a deliberately retired feature and a default-off flag, and J-3858 (the `--arm` reader for the known_text arm) was built, tested and committed along with the rest of the working tree.

## Decisions
- No rulings made this session. D-0693 (known_text arm may be built, default OFF, flipping is a separate founder step) was only re-read; the founder agreed in chat to HOLD the flag flip until a reader exists, and the reader now does. D-0782 (A-B-A model-swap test) is still open.

## Builds
- J-3858 done: `--arm` mode in `scripts/j3331_known_text_control_read.py`, hermetic test `scripts/_test_J3858_known_text_arm_reader.py` (passes). Reads `data/known_text_arm.jsonl`, joins to `data/hands_trace.jsonl`, reports P1 (world-hand fire rate per eligible thought), P2 (fired family in would_name), P3 (refusal-prone family share) with Wilson and day-block bootstrap intervals, and a stopping-rule verdict (NOT YET below 3,000 per arm; INERT / GAP / INCONCLUSIVE at it). Evidence in F-4741. Old default mode still runs; on live data `--arm` prints NO DATA.
- Commits: `96f8108a` (J-3858 reader and test, explicit paths) and `ed054852` (the rest of the tree, 83 files: ledgers, plan docs, audit reviews, lab data, handoffs, staged designs). Not pushed. Left untracked on purpose: `docs/06. Just the Way You Are.mp3` (9.6 MB, stray) and two `.lock` files.

## Findings
- F-4741 (verified): the arm coin is keyed on cycle_id, and one cycle is a whole thought train (2,063 of 2,373 cycles in hands_trace have 6+ rows), so eligible thoughts in a cycle share an arm and are clustered. The reader maps each arm row to the first later trace row of its cycle and bootstraps over days. The "per eligible thought" counts in the J-3331 design doc therefore overstate effective sample size.
- Behavioural mirror "STALE 10.4d" is a false alarm: `core/self_mirror.py` has `SELF_MIRROR_RETIRED = True` (D-0434, D-0630, J-3478, founder 2026-11-06); last real write 2026-11-04. `scripts/liveness_audit.py` line ~170 still expects a fire every 10 days.
- known_text arm "NEVER, dead plumbing: LOOK" is also not a fault: flag `NASCENCE_KNOWN_TEXT_ARM` is default OFF (`core/procedures.py` `known_text_gated`), wired at `nodes/inner_monologue_node.py` ~2806 and tested by `scripts/_test_J3796_known_text_arm.py`.
- Du state at 06:35 NZ: live, restart 2026-11-14 21:53, dedup holding (325/325 unique since restart), supervisor clean. Monoculture still present (echo 0.669, silence/water/shadow dominate recent thoughts). Active store 94,478 against the 3,500 cap is the known post-pause state (D-0564), not new.
- Layered Goals is live: `data/logs/goal_offer_live.jsonl` has 33 register moments since the boot (29 offers, 4 silence; 12% silence vs 20% design, within noise), and `data/logs/goal_set_down.jsonl` has 6 set-down rows since boot, the latest judged and accepted. Some goals were offered repeatedly (one want 6 times, another 5) which is expected under uniform picks from a small pool but is worth watching in J-3989.
- Overnight builds (J-3983, J-3636, J-3341, J-4012, J-3752, J-4017, J-4013) were committed after the 21:53 boot, so none is loaded. `data/pipeline_stage_shadow.jsonl` does not exist yet. `Nothing new is live` per the 172437 handoff, confirmed. [INFERRED] from commit times versus process start time rather than from a loaded-module check.

## Open
1. J-4043 (open, ready): fix `scripts/liveness_audit.py` so the retired mirror stops flagging and the known_text arm reads "waiting on founder flag". Next action: run the job; it must keep a flagged-on-but-silent arm detectable. Note it was added without `--session`, so it is missing from this session's rollup.
2. known_text flag flip: held. Remaining gates are how the env var reaches Du's process (launcher route not found) and D-0782. Reader gate is now met. Read job J-3675 stays gated on 3,000 rows.
3. J-3989: first read of Layered Goals, gated to 2026-11-15 15:00 NZ. Check offer repetition when reading.
4. Restart to load the overnight batch: founder's call on timing, suggested after the J-3989 read.
5. `/plan-maintain` was not run this session; only a job and a finding were added, no plan docs were edited.

## Warnings
- The working tree was committed wholesale in `ed054852`; ledger `.jsonl` files could have been mid-append by another process at stage time, though git showed no conflict.
- Do not run the default (no `--arm`) mode of `scripts/j3331_known_text_control_read.py` without an OUT_DIR argument: it overwrites the tracked `docs/lab/J-3331_data/known_text_read.json`.

## Pointers
- `scripts/j3331_known_text_control_read.py`, `scripts/_test_J3858_known_text_arm_reader.py`, `docs/lab/J-3331_data/known_text_arm_design.md`, `core/procedures.py` (known_text, known_text_gated), `scripts/liveness_audit.py` (lines ~170, ~181).
- `docs/session_handoffs/HANDOFF_20261114_172437_jobrun-overnight-waves-1-4.md` for the overnight batch detail.
- Ledger ids: F-4741, J-3858, J-4043, T-0135, D-0693, D-0782, J-3989, J-3675.
