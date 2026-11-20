---
name: project-nascence-du-prompt-model-benchmark
description: Prompt-to-model benchmark suite for Du (Antigravity, screening pass done 2026-11-18, inferred per F-5117); evidence base for prompt seat routing, never changes seats by itself
metadata:
  type: project
---

Plan `docs/staged/du_prompt_model_benchmark.md`. Goal is grouping about 104 callable prompts onto Du's 5 to 7 resident model seats (model swaps on the 1080 Ti cost 8 to 127 s, F-3064), not 104 model swaps. Screening pass complete 2026-11-18 (confidence inferred, F-5117): report `docs/lab/du_prompt_model_benchmark_results_2026-11-18.md`, runner `scripts/du_prompt_benchmark_suite.py`. Ternary-Bonsai-2 CPU result is F-5118.

Gates: the GPU/Ollama matrix runs only with Du stopped (`--confirm-du-down`); the CPU spare-port track (:11455) is allowed anytime. Guardrail: findings never modify prompts or seats; the sign-off path is `docs/staged/prompt_seat_routing.md` (D-0872..D-0876).

**Why:** founder wants models matched to prompts by measured fit.
**How to apply:** treat results as inferred, not verified; deeper gold banks (hermes3:8b, falcon3:7b on Defeater/Critic) come before any live judge-seat change.
