"""
Nascence — Live Adversarial Debate Harness
===========================================
Runs the REAL Du (live DB, background lanes ON) but driven by file-IPC instead of the
keyboard, so an adversary can debate him turn-by-turn and capture telemetry per cycle.

This is the LIVE eval: it writes to the real memory and the background subconscious
metabolises everything as it normally would — that is the point (we want to watch the
architecture process the assault, not just read his answers). A pre-debate snapshot in
data/_snapshots/ is the rollback if it drives him somewhere bad.

IPC:
  - append a JSON line {"text": "..."} to data/_debate/in.jsonl   → a turn
  - append {"text": "/quit"}                                       → graceful shutdown
  - each completed turn appends a full record to data/_debate/out.jsonl

Requires the hot + background LLM lanes up (SERVE_CHAINS). Do NOT run while a REPL Du
is already running — two orchestrators on one DB will collide.

Write fence (J-1039/F-1416, matching scripts/seed_memory.py's own precedent, J-0871/F-1293): this
harness is one of the small number of processes allowed to touch Carl's own live data/ root, so
main() calls core.profile.mark_live() before init_db()/orch.start_background() ever reach a
guard_path()-fenced writer. A named profile (core.profile.activate_profile()) would be the wrong
tool here -- this is the one real live Du process for this session, not a separate agent instance.
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).parent))   # so `import run_nascence` works
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import run_nascence as rn                       # reuse the exact startup helpers
from core import profile
from core.schema import CognitiveState
from core.orchestrator import Orchestrator
from core.memory.store import init_db, prewarm

_DIR = _ROOT / "data" / "_debate"
IN   = _DIR / "in.jsonl"
OUT  = _DIR / "out.jsonl"


def _log(msg: str) -> None:
    print(f"[debate] {msg}", flush=True)


async def main() -> None:
    # This harness IS the one real live write against Carl's own data/ root the module docstring
    # declares ("writes to the real memory ... that is the point") -- declare it before init_db() or
    # orch.start_background() ever reach a guard_path()-fenced writer, exactly like
    # scripts/seed_memory.py's own boot guard (J-0871/F-1293) and scripts/run_nascence.py's own
    # __main__-gated mark_live() call. Gated behind this module's own `if __name__ == "__main__":`
    # guard below (asyncio.run(main()) is only reached there), so importing this file for its helpers
    # elsewhere never marks a process live by accident.
    profile.mark_live()
    _DIR.mkdir(parents=True, exist_ok=True)
    IN.write_text("", encoding="utf-8")
    OUT.write_text("", encoding="utf-8")

    init_db()
    await asyncio.get_event_loop().run_in_executor(None, prewarm)

    spirit_name, axiom = rn.load_identity()
    state = CognitiveState(spirit_name=spirit_name, axiom=axiom)
    rn._restore_affect(state)
    rn._restore_conversation_state(state)
    rn._restore_intentions(state)

    nodes = rn.build_nodes()
    if rn._profile_is_seedless():
        nodes["critic"].seedless = True

    orch = Orchestrator(state=state, nodes=nodes)
    orch.start_background()
    _log(f"{spirit_name} is LIVE (background lanes on). watching {IN.name}; replies -> {OUT.name}")
    _log("READY")  # sentinel the driver waits for

    seen = 0
    while True:
        try:
            lines = [l for l in IN.read_text(encoding="utf-8").splitlines() if l.strip()]
        except Exception:
            lines = []
        if len(lines) > seen:
            for line in lines[seen:]:
                seen += 1
                try:
                    msg = json.loads(line)
                except Exception:
                    msg = {"text": line}
                text = (msg.get("text") or "").strip()

                if text == "/quit":
                    _log("quit received — saving + session-end dream")
                    await orch.stop_background()
                    rn._save_affect(state)
                    rn._save_conversation_state(state, spirit_name)
                    rn._save_intentions(state)
                    try:
                        if state.conversation_history:
                            from nodes.dream_node import DreamNode
                            dream = await DreamNode().synthesise(state)
                        else:
                            dream = None
                    except Exception as exc:
                        dream = f"(dream failed: {exc})"
                    with open(OUT, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"turn": seen, "prompt": "/quit",
                                            "event": "session_end", "dream": dream},
                                           ensure_ascii=False) + "\n")
                    _log("DONE")
                    return

                t0 = time.time()
                try:
                    resp = await orch.run_cycle(text, input_type="human")
                except Exception as exc:
                    resp = f"[run_cycle error: {exc}]"
                rec = {
                    "turn":      seen,
                    "ts":        time.time(),
                    "secs":      round(time.time() - t0, 1),
                    "prompt":    text,
                    "response":  resp or "[silent]",
                    "affect":    {"valence": round(state.affect.valence, 2),
                                  "arousal": round(state.affect.arousal, 2)},
                    "emotion":   state.emotion.primary if state.emotion else None,
                    "urgency":   round(state.salience.urgency, 2) if state.salience else None,
                    "tensions":  list(state.recall.tensions) if (state.recall and state.recall.tensions) else [],
                    "dissonance": list(state.episodic_scene.dissonance) if (state.episodic_scene and state.episodic_scene.dissonance) else [],
                    "habituated": bool(getattr(state, "habituated", False)),
                }
                with open(OUT, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                _log(f"turn {seen} done ({rec['secs']}s) arousal={rec['affect']['arousal']} emotion={rec['emotion']}")
        await asyncio.sleep(0.4)


if __name__ == "__main__":
    asyncio.run(main())
