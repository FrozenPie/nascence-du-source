---
name: windows-charmap-daemons
description: "Every Python daemon launched on this Windows machine needs sys.stdout.reconfigure(encoding='utf-8') at the top — otherwise print() crashes on any non-ASCII char (Polish names, emojis, Vietnamese diacritics, etc.)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c154ccfb-a20f-496e-ac83-94f884030593
---

Windows defaults stdout to `cp1252`. Python `print()` raises `UnicodeEncodeError: 'charmap' codec can't encode character` on anything outside Latin-1 — Polish ż, Turkish ı, Vietnamese ế, Croatian ć, Latvian ā, emojis 🦠🧠, etc.

The exception bubbles up and the caller logs something misleading like "Web research failed" or "CONTAGION Persist Error" — but the underlying operation succeeded. Only the *logging step* died. Diagnosing this is painful because the surface symptom hides the real failure.

**Hit count 2026-05-27:** 53 chronicler.log occurrences overnight, all on international spirit names and a few emoji in contagion payloads. Buddha lost meaningful Wikipedia material from any non-Anglo spirit.

## The Fix

At the **top of every daemon script** (before any `print()` runs):
```python
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass  # Python <3.7 or non-tty
```

Single line per stream. Wraps in try/except so it doesn't break in unusual contexts. Already applied to `scripts/run_chronicler_pulse.py` on 2026-05-27.

## How to Apply

When writing or auditing any new daemon (the upcoming 1-bit swarm server, llama.cpp wrappers, future Oracle variants), add this block **first**. Don't wait for the bug to surface — it will, the moment a spirit with a non-ASCII name appears in a log line.

Already missing from (as of 2026-05-27, worth a sweep if scope allows):
- `scripts/run_oracle_pulse.py` — Oracle daemon
- `scripts/pulse_master.py` — Background heartbeat
- `scripts/neural_daemon.py` — Task orchestrator
- `scripts/nexus_server.py` — Bridge server
- `scripts/llama_hub_server.py` — Oracle's llama.cpp wrapper
- Any future `start_slot_*_swarm.bat`-launched Python process

Alternative: set `$env:PYTHONIOENCODING = 'utf-8'` in `Sovereign_Control_Panel.ps1` before launching any daemon. One change, covers all. The per-script fix is more robust (survives manual launches), the env-var fix is more centralised.
