"""
Nascence — Turn-based debate between two profiles, sharing one local model backend.

Two full Nascence agents (e.g. carl + dennett) alternate. Because turns are strictly
sequential, we simply re-activate the speaker's profile before each turn — the shared module
path-constants point at the right agent's DB/state for the duration of that turn, so there are
no concurrent-global races. Each agent runs its complete hot-path cycle (perception → ... →
voice); the other agent's last utterance arrives as its "human" input.

Optional --think runs one guarded subconscious scan per turn for the speaker, so shadow events
cluster into tensions → T2 synthesis → contradiction pressure → (eventually) T4 self-revision.
That is the mechanism by which sustained dialectical pressure could actually change either mind.

Unattended-safe: a hard turn cap, full JSONL transcript, and per-turn error isolation so one
stumble logs and continues rather than wedging an overnight run.

Usage:
  python scripts/debate.py --a carl --b dennett --turns 30
  python scripts/debate.py --a carl --b dennett --turns 200 --think      # overnight, minds evolve
"""
import sys, json, argparse, asyncio, time, traceback
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, str(Path(__file__).parent))          # scripts/  -> import run_nascence
sys.path.insert(0, str(Path(__file__).parent.parent))   # repo root -> import core, nodes

from core import profile
from core.schema import CognitiveState
from core.orchestrator import Orchestrator
from core import model_client as _mc
import run_nascence as rn
from core.memory.store import self_narrative_material

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1308/F-1844 (4th-round lab_isolation sweep): each agent's orch.run_cycle() (+ the --think
    # subconscious scan / --t4-every self-authoring calls) below reaches call_node() only
    # INDIRECTLY through the node pipeline -- invisible to every earlier round's own literal
    # "call_node(" grep against this file. Only this script's own telemetry side-effect is
    # redirected into scratch/, same pattern verify_lanes.py/J-1274 established; changes nothing
    # about which models get called or what the transcript records.
    neutralize_telemetry(Path(__file__).parent.parent / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass


def _activate(name: str) -> Path:
    """Point every per-agent path (shared modules + run_nascence's own) at this profile."""
    base = profile.activate_profile(name)
    rn.AXIOM_PATH        = base / "identity" / "axiom.json"
    rn.AFFECT_STATE_PATH = base / "affect_state.json"
    rn.SC_STATE_PATH     = base / "subconscious_state.json"
    rn.CONV_STATE_PATH   = base / "conversation_state.json"
    rn.INTENTIONS_PATH   = base / "deferred_intentions.json"
    return base


async def _build_agent(name: str, model: str = "qwen3-du") -> dict:
    _activate(name)
    rn.init_db()                                  # creates this profile's DB if absent
    spirit_name, axiom = rn.load_identity()
    state = CognitiveState(spirit_name=spirit_name, axiom=axiom)
    rn._restore_affect(state)
    rn._restore_conversation_state(state)
    rn._restore_intentions(state)
    nodes = rn.build_nodes()
    sub = nodes.get("subconscious")
    if sub is not None:
        sub.base_urls = ["http://127.0.0.1:11433"]   # run T2/T4 on qwen (ollama OLLAMA_HOST=11433, NOT 11434)
    orch = Orchestrator(state=state, nodes=nodes)
    # NB: background loops are deliberately NOT started — we tick the subconscious manually
    # (T1 per turn under --think; T4 every --t4-every turns) to avoid concurrent races on the
    # shared path-constants.
    return {"profile": name, "name": spirit_name, "state": state,
            "orch": orch, "subconscious": sub, "tcount": 0, "model": model}


async def _fire_t4(agent: dict, log) -> None:
    """In-flight T4 revision attempt for one agent. The cost gate inside decides whether it
    actually revises; we just force the attempt. Reads before/after self_concept to report."""
    node = agent["subconscious"]
    if node is None:
        return
    from core import profile as _p
    base = _p.profile_dir(agent["profile"])
    axp = base / "identity" / "axiom.json"
    before = json.loads(axp.read_text(encoding="utf-8"))["emergent_self"].get("revision_count")
    node._state["last_self_authoring"] = 0           # bypass the interval gate; force the attempt
    material = self_narrative_material(since_ts=0, limit=14)
    if not material:
        return
    try:
        await node._t4_self_authoring(agent["state"], material)
    except Exception as exc:
        log({"event": "t4_error", "profile": agent["profile"], "error": str(exc)})
        return
    after_em = json.loads(axp.read_text(encoding="utf-8"))["emergent_self"]
    revised = after_em.get("revision_count") != before
    log({"event": "t4", "profile": agent["profile"], "revised": revised,
         "revision_count": after_em.get("revision_count"),
         "self_concept": after_em.get("self_concept", "")[:400] if revised else None,
         "ts": time.time()})
    print(f"      [T4 {agent['name']}: {'REVISED -> rev ' + str(after_em.get('revision_count')) if revised else 'held'}]")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="carl", help="profile that speaks first")
    ap.add_argument("--b", default="dennett", help="the other profile")
    ap.add_argument("--a-model", default="qwen3-du", dest="a_model", help="ollama model for agent A")
    ap.add_argument("--b-model", default="qwen3-du", dest="b_model",
                    help="ollama model for agent B (e.g. deepseek-r1:8b to break same-model echo)")
    ap.add_argument("--turns", type=int, default=20, help="total turns (both agents combined)")
    ap.add_argument("--think", action="store_true",
                    help="run a subconscious scan per turn so the minds can evolve (slower)")
    ap.add_argument("--t4-every", type=int, default=0, dest="t4_every",
                    help="fire a T4 self-revision attempt for a speaker every N of its own turns "
                         "(0=off). The cost gate decides whether it actually revises.")
    ap.add_argument("--out", default=None, help="transcript path (.jsonl)")
    ap.add_argument("--opening", default=(
        "We have been asked to explore one question together — honestly, and without resolving it "
        "prematurely: Is there a Self — a real centre of the psyche that one can come to know and "
        "integrate — or is that a useful fiction the mind spins about itself? Tell me plainly where "
        "you stand, and why."))
    args = ap.parse_args()

    rn.prewarm()   # load the shared embedding model once

    A = await _build_agent(args.a, args.a_model)
    B = await _build_agent(args.b, args.b_model)

    out_path = Path(args.out) if args.out else (
        profile.profile_dir(None) / f"debate_{args.a}_vs_{args.b}_{int(time.time())}.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def log(rec: dict) -> None:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"=== DEBATE: {A['name']} ({args.a})  vs  {B['name']} ({args.b}) ===")
    print(f"turns={args.turns}  think={args.think}  transcript -> {out_path}\n")
    log({"event": "start", "a": A["name"], "b": B["name"],
         "think": args.think, "opening": args.opening, "ts": time.time()})

    msg = args.opening
    speaker, listener = A, B
    for turn in range(1, args.turns + 1):
        try:
            _activate(speaker["profile"])
            _mc._MODEL_FIELD = speaker["model"]   # route this speaker's LLM calls to its own model
            t0 = time.time()
            resp = await speaker["orch"].run_cycle(msg, input_type="human")
            resp = (resp or "(silence)").strip()
            dt = time.time() - t0
            print(f"--- turn {turn} | {speaker['name']}  ({dt:.0f}s) ---")
            print(f"  IN : {msg[:160]}")
            print(f"  OUT: {resp}\n")
            log({"event": "turn", "turn": turn, "speaker": speaker["name"],
                 "profile": speaker["profile"], "input": msg, "output": resp,
                 "secs": round(dt, 1), "ts": time.time()})

            if args.think and speaker["subconscious"] is not None:
                try:
                    await speaker["subconscious"]._t1_scan(speaker["state"])
                except Exception as exc:
                    log({"event": "think_error", "turn": turn,
                         "speaker": speaker["name"], "error": str(exc)})

            # In-flight T4: every N of this speaker's own turns, attempt a self-revision.
            # The cost gate inside T4 decides whether the commitment actually moves.
            speaker["tcount"] += 1
            if args.t4_every and speaker["tcount"] % args.t4_every == 0:
                await _fire_t4(speaker, log)

            msg = resp
            speaker, listener = listener, speaker

        except Exception as exc:
            log({"event": "turn_error", "turn": turn, "speaker": speaker["name"],
                 "error": str(exc), "trace": traceback.format_exc()[:2000]})
            print(f"[turn {turn} ERROR: {exc}] — continuing")
            # hand the floor to the other agent, reuse the same prompt
            speaker, listener = listener, speaker

    # Persist both agents' carried state so a future run continues their lineage.
    for ag in (A, B):
        try:
            _activate(ag["profile"])
            rn._save_affect(ag["state"])
            rn._save_conversation_state(ag["state"], ag["name"])
            rn._save_intentions(ag["state"])
        except Exception as exc:
            log({"event": "save_error", "profile": ag["profile"], "error": str(exc)})

    log({"event": "end", "turns": args.turns, "ts": time.time()})
    print(f"=== done — {args.turns} turns written to {out_path} ===")


if __name__ == "__main__":
    asyncio.run(main())
