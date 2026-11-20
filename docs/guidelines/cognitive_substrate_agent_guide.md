# Cognitive Substrate & Non-LLM Task Execution Guide for AI Agents

> **Domain:** Agentic Coding / Task Economy / Non-LLM Primitives / Cognitive Efficiency / Context Window Optimization
> **Target Audience:** Claude, Antigravity Subagents, and Pair Programming Sessions

---

## 1. Executive Summary

This guide translates our empirical cognitive substrate findings into concrete operational rules for AI coding assistants and autonomous subagents working in `c:\Nascence` and `C:\FreshStart`.

By replacing expensive LLM token passes with deterministic non-LLM primitives (tool searches, targeted line viewing, static analyzers, and skill templates), we achieve:
- **81.1% reduction in unnecessary LLM/Subagent invocations**
- **79.9% token savings**
- **66.7% VRAM context pressure reduction**
- **+19.3% precision gain in context retrieval**

---

## 2. The 4 Operational Task Classes

```
                          EVERY USER REQUEST
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
Class A: Search             Class B: Judgment           Class C: Transmission
(find_by_name, grep)        (checklist.py, tests)       (line bounds, diffs)
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  ▼
                            Class D: Schema
                            (skills, workflows)
```

### Class A — Replace Search
- **Rule:** Never ask an LLM or subagent to browse directories or read raw file text blindly.
- **Tool Protocol:** Use `find_by_name` for file paths and `grep_search` for symbol/function definitions. Construct exact candidate sets before inspecting contents.

### Class B — Replace Judgment
- **Rule:** Never rely on LLM self-reflection to determine if code compiles or logic is correct.
- **Tool Protocol:** Execute deterministic commands: `python .agent/scripts/checklist.py .`, unit tests, or static linters. Base all diagnostics strictly on empirical log evidence.

### Class C — Replace Transmission
- **Rule:** Never pass full 10,000-line files or un-truncated context windows to subagents or prompt buffers.
- **Tool Protocol:** Transmit compact parameters $m = f(X, B)$: explicit `StartLine` and `EndLine` ranges, precise git diffs, and exact symbol signatures.

### Class D — Replace Repeated Generation
- **Rule:** Never re-derive multi-step setup scripts, refactoring patterns, or test harnesses from scratch.
- **Tool Protocol:** Encode recurring solutions as reusable **Skills** (`.agent/skills/`) or **Workflows** (`.agent/workflows/`).

---

## 3. Hodge Flow Anti-Rumination Brake

AI agents can fall into "rumination loops"—repeating the exact same failing shell command or asking the user the same question twice.

```text
                  COMMAND EXECUTION / DEBUG CYCLE
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
            Gradient Progress           Curl Rumination
            (∇Φ: changed code /         (curl Ψ: identical
             new diagnostic data)        command / repeated error)
                   │                           │
                   ▼                           ▼
            CONTINUE PASS               THROTTLE & PIVOT
```

- **If $\operatorname{curl} \Psi$ is detected:** Stop immediately. Inspect logs silently, analyze root causes, or ask for clarification rather than retrying the broken pattern.

---

## 4. Key References & Documentation Links
- **Staged Specification**: [`docs/archive/multidimensional_dynamical_field_plan.md`](file:///c:/Nascence/docs/archive/multidimensional_dynamical_field_plan.md) (v17)
- **Local Agent Skill**: [`C:\FreshStart\.agent\skills\cognitive-substrate\SKILL.md`](file:///C:/FreshStart/.agent/skills/cognitive-substrate/SKILL.md)
- **Cycle Benchmark Script**: [`scripts/benchmark_cognitive_cycle.py`](file:///c:/Nascence/scripts/benchmark_cognitive_cycle.py)
- **Substrate Benchmark Script**: [`scripts/benchmark_mathematical_substrate.py`](file:///c:/Nascence/scripts/benchmark_mathematical_substrate.py)
