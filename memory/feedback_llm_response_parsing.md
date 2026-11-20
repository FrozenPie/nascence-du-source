---
name: llm-response-parsing
description: Two LLM response-parsing pitfalls (Ollama thinking-field split + <think>-tag burial) require the same fallback applied at FIVE distinct entry points in core/inference. Missing any one site silently breaks a different agent.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c154ccfb-a20f-496e-ac83-94f884030593
---

In this codebase, "empty response from model" is almost never an inference failure — it's a parser missing one of two distinct ways reasoning models hide their output. Both have the same fix. Both must be applied at **five** sites, because different agents (main sim spirits, judge, Buddha, Oracle) route through different facade entry points.

## The Two Patterns

**1. Tag-level burial (older, pre-Ollama-0.5):**
deepseek-r1 emits its entire answer inside `<think>...</think>`, with nothing after the closing tag. Parser strips think tags → response is empty.

**2. Field-level split (Ollama 0.5+, current):**
Modern Ollama puts reasoning into a separate `thinking` JSON field. When the model hits `done_reason=length` mid-think, the visible `response` field is empty and all generated tokens (often 2048+) sit in `thinking`.

Confirmed via direct probe 2026-05-26:
```json
{"model":"deepseek-r1:8b", "response":"", "thinking":"First", "done":false}
```

## The Fix (Same in Both Cases)

After parsing/think-stripping, before returning, check:
```python
if not response_text and thinking_buffer:
    response_text = thinking_buffer
```

For `/api/chat` (executor), the field is `message.thinking`. For `/api/generate` (facade), it's top-level `thinking`.

## The Five Sites (as of 2026-05-27)

| # | File | Function | Used by |
|---|------|----------|---------|
| 1 | `core/inference/executor.py` | `call_ollama` | Legacy direct calls |
| 2 | `core/inference/executor.py` | `call_ollama_async` | Async legacy calls |
| 3 | `core/inference/facade.py` | `run_task_monitored` | Main sim spirits (sync path) |
| 4 | `core/inference/facade.py` | `run_task_monitored_async` | Main sim spirits (async, primary path) |
| 5 | `core/inference/facade.py` | `run_task` | **Buddha's CHRONICLER missions** — missed until 2026-05-27, blocked all SYNTHESIS_ and Grand Work production |

## Why It Keeps Recurring

Each fix session believes it caught the canonical path:
- Session 1 fixed only `executor.call_ollama`. Main sim still bled because spirits use `facade.run_task_monitored_async`.
- Session 2 fixed both facade monitored paths. Buddha still bled because chronicler missions use `facade.run_task` (different function entirely).
- Session 3 (2026-05-27) found the chronicler path while diagnosing zero Grand Works.

There may be a 6th. Before declaring this class of bug fixed:
```
grep -rn "response.*=.*result\[.response.\]\|response.*=.*result\.get(.response" core/inference/
```
Every match needs the fallback. Don't assume — verify.

## Diagnostic Signature

`[VALIDATOR] FAILED: Response empty or critically short.` followed by Oracle escalation also returning empty (`{"error": "no_action_found"}`) → think-burial in a parser that lacks the fallback. The model IS generating tokens (`eval_count` will be high in the EMPTY DIAG log line); the parser is throwing them away.
