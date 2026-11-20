# Triage: Antigravity's du_telemetry_findings_for_claude.md vs Du's own data

**Date:** 2026-08-27 · **Job:** J-0293 · **By:** Claude (main session)
**Source under triage:** `docs/audits/du_telemetry_findings_for_claude.md` (Antigravity, 2026-08-26)
**Note:** the audit's JSON artifacts live in `C:\UDMS\data\viability_validation\` (not the Nascence
paths its own links claim).

## Verdicts

### 1. yi:34b dream-node bottleneck — ✅ CONFIRMED (and current)
`data/llm_latency.jsonl`: 227 yi:34b-v1.5 rows (their 211 + growth), mean **183.9s**, max **388.1s**
(exact match), **16.3% failure** (37/227; they said 15.64%). Callers all `nodes.dream_node:318/340/356`.
Real, ongoing, and the single worst latency×failure profile in the fabric. **Feeds J-0303**: dream
synthesis either moves to a stronger-served node, gets a smaller model, or gets its timeout/retry
budget redesigned.

### 2. "14 of 16 cognitive nodes dormant" — ❌ REFUTED as stated
Three independent errors in the audit's method:
- Its named heartbeat root is wrong: **`core/village_clock.py` does not exist**, and `scripts/du_pulse.py`
  is our read-only *monitoring* tool — Du's real entry is `scripts/run_nascence.py` → `core/orchestrator.py`,
  which imports the node set the audit called dormant.
- Module-level AST import scanning misses this codebase's dominant patterns: **function-local lazy imports**
  (315 `from core` imports inside `nodes/inner_monologue_node.py` alone) and the orchestrator's
  **string-keyed node registry** (`self.nodes.get("monologue")`).
- Live-log ground truth (this week's log): monologue **121,457** lines, subconscious **19,356**,
  curiosity **4,942**, dream **2,037**; reflection/critic/executive log 8/9/10 lines (they fire on human
  conversation cycles, which are rare — low-traffic, not unwired).
What survives: a *subset* of node files (voice, salience, perception, emotion, episodic_buffer,
memory_router, recall, consolidation) shows no live logger traffic — that is our long-known
write-only-systems watch item, not a newly-discovered "14 dormant organs."

### 3. "167/213 core modules disconnected" — ❌ GROSSLY INFLATED
Spot-check of the audit's own named examples: `core/arousal` has **7** real importers (incl. live-path
emotion_construction, lane2, listening), `core/associative_recall` **4** (incl. orchestrator,
inner_monologue, dream_node — the live recall path), `core/affections` **3**, `core/balance` **3**.
Only `core/attention_schema_loop` is near-orphaned (1). Same lazy-import blind spot as claim 2.
Some genuinely dead core modules surely exist, but this scan cannot identify them; treat its list as
untrustworthy. (J-0265 — the aliased-import grep-miss audit — is the right instrument for this
question.)

### 4. Port & model-string drift — 🟡 PARTLY CONFIRMED, labels wrong, genuinely useful
Real: `qwen2.5:7b` strings persist in **6 core files** (`lane2.py`, `left_lane.py`, `model_client.py`,
`schema.py`, +2); port `11441` hardcoded in 3 core files; odd ports `11460`/`11470` in 2/1.
Wrong: the audit labels 11436/11438/11441 "legacy/rare" — they are the **NEW Ramses tier** (falcon3:7b
on :11436, mixtral:8x7b on :11438 live since 08-23; command-r7b planned on :11441). Zero core refs to
11436/11438 is expected (nothing wired yet, by design). **Feeds J-0303**: the redistribution plan
should include a config-consolidation step (audit each qwen2.5:7b/odd-port ref: live default, dead
fallback, or stale).

### 5. Prompt-pressure figures — 🟡 PARTLY
Magnitudes reproduce (inner_monologue mean prompt ~3.4k chars across 562 calls in the current log);
their exact figures (707 calls / max 20,513 chars) don't reproduce from current files — likely a
different window or rotated log. Directionally fine, don't cite their exact numbers.

## Net
The audit's *telemetry* is trustworthy (claim 1, and usable parts of 4); its *code-topology* claims
(2, 3) are method artifacts and should not drive any work. Claims 1 and 4 flow into J-0303's
inventory. Finding: F-0381.
