---
name: project-nascence-prompt-seat-routing
description: 🔵 Plan to route each Du prompt to the best model seat via a prompt-to-seat table instead of by lane; staged 2026-11-19, five founder rulings D-0872..D-0876, nothing built
metadata:
  type: project
---

Plan `docs/staged/prompt_seat_routing.md` (I-0166 promoted, T-0148 origin). Founder wants to move away from one hot-loop model and spread models across prompts by how well each works. Evidence: Antigravity's 2026-11-18 screening benchmark (`docs/staged/du_prompt_model_benchmark.md`, inferred per F-5117: gold banks 9-14 cases, Stage B n=10) and F-5118 (Ternary-Bonsai-2-27B CPU: prefill scales ~linearly to 32 threads, gen ~5-6 tok/s, 14/14 Defeater but majority baseline is 11/14).

**Why:** the same model wins one prompt and collapses on another (bonsai-27b 14/14 Defeater, constant veto on Critic; command-r7b strong A4, last on A5 voice). Seats are few (11 GB GPU swap costs 8-140 s), so the choice is prompt to one of ~5-7 resident seats, not 104 models.

**How to apply:** rulings D-0872 voice prompts one seat by default; D-0873 one resident model on hot GPU; D-0874 Bonsai-2 CPU seat 16 threads background-only; D-0875 dreamer :11442 protected; D-0876 each promotion its own /decide. Table defaults to today's behaviour (`inherit`), shadow before live, keep D-0354 (:11441 no grammar first). P0 = read-only table that replays recent llm_calls with zero diffs. Antigravity wrongly proposed dropping :11441 from _NO_GRAMMAR_FIRST_PORTS (contradicts D-0354). Related: [[project-nascence-prompt-manager]].
