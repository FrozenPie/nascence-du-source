# Judge1 repoint and Control Panel CPU-tier bug

## Session timing
- **Session started:** 2026-09-02T01:50:50Z
- **Last message before wrap:** 2026-09-02T04:17:49Z
- **Wrapped:** 2026-09-02 04:17:35 UTC

## Summary

Started from noisy log line (core/left_lane.py "ground unavailable" fail-open message, repeating every cycle) | ended finding/fixing real bug in Nascence_Control_Panel.ps1 silently preventing local CPU judge tier from ever starting, regardless of Du restarts | judge_panel.py Judge1 panel vote + left_lane.py grounding call deliberately repointed to already-resident Ramses hub | local tier also brought back up for real, restoring 3 previously-unaudited consumers: peers.py, decomposed_critic.py, librarian.py

## Decisions

- D-0121: judge_panel.py JUDGE_1 (panel member A) gemma4:12b local (127.0.0.1:11439)→mixtral:8x7b Ramses (LAN-HOST:11438), reusing already-resident commitment-defeater/dream-primary hub, not starting new one | family decoupling preserved: mixtral (Mistral) vs falcon3 Judge2 (TII) vs granite tiebreak (IBM) | defeater: revisit if judge_panel_log.jsonl/llm_latency.jsonl shows :11438 contention from combined load (F-0381 pattern) — if so, give Judge1 own hub
- D-0122: core/left_lane.py ground_thought()→same Ramses mixtral hub, scoped narrowly via new dedicated GROUND_URL/GROUND_MODEL constants, NOT shared BASE_URL/MODEL | rest of left_lane.py Emissary calls (dispatch, grade_essay, grade_work, grade_self_revision, grade_gist_faithfulness, claim_test_panel) still use shared BASE_URL/MODEL | same defeater as D-0121
- D-0125: rather than migrate remaining local-tier consumers (peers.py, decomposed_critic.py, librarian.py) to Ramses, founder chose to launch local CPU tier for real via scripts/launch_servers.ps1 | Judge1/Judge2/dreamer verified live afterward | defeater: revisit if local tier RAM footprint causes F-0389/2026-08-24-style overnight RAM pressure — migrate those 3 to Ramses then

## Fixes

- core/judge_panel.py: JUDGE_1 repointed per D-0121 | dated comment explains reuse-resident-capacity reasoning + accepted contention risk
- core/left_lane.py: added GROUND_URL/GROUND_MODEL constants, used only by ground_thought() (D-0122) | _note_call() now accepts optional model/url overrides so HUD telemetry attributes grounding calls to real hub, not shared BASE_URL/MODEL | "ground unavailable this cycle (fail-open)" log line downgraded logger.info→logger.debug (already-handled fail-open path, not real failure)
- core/schema.py: stale "judge_1" doc-only entries in SERVE_URLS/SERVE_CHAINS + header comment updated to point at real D-0121 location, not silently describe retired local hub
- scripts/launch_servers.ps1: header Judge1/Judge2 description updated twice this session — first noting Judge1 was left_lane-grounding-only (before peers.py etc. known) | corrected again after D-0125: local tier stays required, core/peers.py + core/decomposed_critic.py + core/librarian.py all still hardcode it directly
- Nascence_Control_Panel.ps1 (F-0684): Full-Start() previously called only Start-Supervisor + Start-HUD + Start-REPL | Start-Supervisor launches scripts/supervisor.py, whose watchdog manages exactly one server (local ollama, :11433) — never knew CPU hubs existed | menu option [1] could never bring up CPU judge tier regardless of restarts; only option [2] (calls launch_servers.ps1 directly) worked | fix: Full-Start now also calls Start-Servers-Silent before handing GPU lane to supervisor's watchdog
- Nascence_Control_Panel.ps1 (F-0685): $SUBCON_PORT was 11434 (Ramses ollama), retired 2026-08-28 (D-0056) when background/subconscious lane moved to command-r7b on Ramses :11441 | panel's Subconscious status check, menu header, Start-REPL preflight all checked dead port, would report ASLEEP forever regardless of real lane health | corrected to 11441 everywhere displayed + stale phi3:mini/mistral doc-comment references fixed throughout file
- scripts/supervisor.py: stale docstring/comments corrected, previously described pre-2026-08-15 single-ollama architecture (Judge+Dreamer same ollama process via num_gpu:0) | now states scope is local ollama only, names what it does NOT manage: CPU tier, Ramses background lane

## Findings

- F-0657 [verified]: original noisy log line = core/left_lane.py ground_thought() failing open every cycle because local Judge1 hub (127.0.0.1:11439) never brought online this session — not a port conflict, nothing else contending for port | deliberation.py already falls back to hot lane on this failure — nothing functionally broken, just noisy at INFO level
- F-0661/F-0662 [verified]: D-0121 + D-0122 repoints live-audited against real JSON contracts on new Ramses mixtral hub before finalizing — correct accept + correct refuse on judge_panel's boolean+why contract; coherent {grounding: str} response for ground_thought's contract
- F-0683 [verified]: founder restarted Du, saw same-looking "transport error on 127.0.0.1:11439 -- failing over" message | root-caused as NOT a regression of D-0121/D-0122 | came from 3 previously-unaudited consumers of local tier: core/peers.py (Twain/Shackleton letters hardcode :11439, Marcus/Smith hardcode :11440), core/decomposed_critic.py (default :11439 fallback for reflection-draft critic), core/librarian.py (:11440→:11439 chain, both hops dead) | WHOLE local CPU tier down all session (netstat confirmed only :11433 listening, before + after D-0121/D-0122), not just Judge1
- F-0684/F-0685 [verified]: see Fixes above — control panel's Full-Start bug = actual root cause of entire evening's :11439/:11440 saga | Subconscious status check bug is separate, independent, permanently-wrong readout, unrelated to tonight's incident

## Open

1. J-0496 (needs_input): should scripts/supervisor.py watchdog also auto-heal CPU judge tier (restart hung Judge1/Judge2/Dreamer hub, as it already restarts hung hot_ollama), not just rely on launch_servers.ps1 single start? | real design decision, not pure bugfix — CPU hubs launch differently (blob resolution via resolve_blob.py, --lazy/--idle-unload flags) than plain `ollama serve`, extending SERVERS not a one-line change | next: founder ruling via /decide, then implementation if approved
2. S-0025 (skill suggestion, open): session_handoff.py transcript lookup for new-path/rollup timing hardcoded to literal C--FreshStart project directory, regardless of actual session project | failed to find this session's own transcript (lives under C--Nascence), returned UNKNOWN for session_started/last_message_time | real values recovered by reading transcript file directly/manually, used (not UNKNOWN) in this handoff's timing block | next: ~/.claude/skills/session-wrap maintainer should derive project directory from cwd, not fixed literal

## Warnings

- Local CPU tier (Judge1 gemma4:12b :11439, Judge2 falcon3:7b :11440, dreamer yi:34b :11442) now running as of this session (via launch_servers.ps1, D-0125) | do not assume down without checking — was down most of session, not down right now
- core/left_lane.py dispatch()/grade_essay()/grade_work()/grade_self_revision()/grade_gist_faithfulness()/claim_test_panel() still use shared BASE_URL/MODEL (local :11439 gemma4:12b) — only ground_thought() moved to Ramses | don't assume whole Emissary module moved — it didn't, on purpose (D-0122's own defeater note)
- Nascence_Control_Panel.ps1 [1] Full Start fixed, now brings up CPU tier correctly — NOT true before this session's fix | don't trust prior assumption (old handoff, memory file, own recollection) that option [1] was already comprehensive

## Pointers

- Nascence_Control_Panel.ps1 (Full-Start, Show-Status, Show-Menu — the actual fix)
- scripts/supervisor.py (corrected docstring; still narrow-scope, see J-0496)
- core/judge_panel.py (JUDGE_1 constant)
- core/left_lane.py (GROUND_URL/GROUND_MODEL, ground_thought())
- core/peers.py (_HUB_LLAMA/_HUB_JUDGE2 — untouched this session, still hardcode local tier; relevant if J-0496 or future session migrates them)
- docs/plans/ramses_second_tier.md (plan D-0121/D-0122/D-0125 opened against)
