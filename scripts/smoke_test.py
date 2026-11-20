"""
Nascence — regression smoke test. Run after ANY change and before judging Du by feel:
    python scripts/smoke_test.py
Boots a headless Du in an isolated '_smoke' profile (his real memory untouched), runs canned
cycles against the LIVE servers, and asserts the things that have actually broken this week:
  - JSON arrives (no empty-content thinking leaks)
  - the hot lane answers (no silent Bonsai-fallback degradation)
  - the task valve recognises a plain imperative
  - the correction detector fires on a real correction
PASS means the stack is sane. FAIL tells you before Du does.
"""
import asyncio, logging, shutil, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent

try:
    from core import telemetry
    from lab_isolation import neutralize_telemetry
    # J-1308/F-1844 (4th-round lab_isolation sweep): orch.run_cycle() (imported+called inside
    # main() below) reaches call_node() only INDIRECTLY through the node pipeline -- invisible to
    # every earlier round's own literal "call_node(" grep against this file. Only this script's
    # own telemetry side-effect is redirected into scratch/, same pattern verify_lanes.py/J-1274
    # established. This module-level placement (ahead of main()'s own imports) guards the whole
    # run regardless of what main() does; this script's own docstring says to run it "against the
    # LIVE servers" on purpose -- unchanged, only its telemetry write is now isolated.
    neutralize_telemetry(ROOT / "scratch" / "lab_isolation_telemetry", telemetry)
except Exception:
    pass

failures: list[str] = []
records: list[logging.LogRecord] = []


class Collector(logging.Handler):
    def emit(self, record):
        records.append(record)


async def main() -> int:
    from core.profile import activate_profile
    prof = activate_profile("_smoke")
    # fresh identity copy so the smoke mind resembles the real one
    src = ROOT / "data" / "identity" / "axiom.json"
    if not src.exists():
        # J-0930 (F-1295): data/ is gitignored, so a fresh checkout or worktree never has this --
        # only a tree with a real seeded data/identity/ does. Fail here, at the actual gap, with
        # an actionable message, instead of silently no-op'ing the copy and letting
        # rn.load_identity() crash two lines below with a bare FileNotFoundError on a path that
        # gives no hint why it's missing.
        print("  SMOKE FAIL:")
        print(f"   - no identity seed at {src} -- data/ is gitignored, so a fresh checkout or "
              f"worktree never has one. Seed data/identity/axiom.json here (e.g. copy it from a "
              f"tree that already has it) before running the smoke test.")
        return 1
    dst = Path(prof) / "identity" / "axiom.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    import scripts.run_nascence as rn
    from core.schema import CognitiveState
    from core.orchestrator import Orchestrator

    logging.getLogger().addHandler(Collector())
    logging.getLogger().setLevel(logging.INFO)

    rn.init_db()
    name, axiom = rn.load_identity()
    state = CognitiveState(spirit_name=name, axiom=axiom)
    orch = Orchestrator(state=state, nodes=rn.build_nodes())
    # background loops deliberately NOT started — hot path only, deterministic

    probes = [
        ("greeting",   "Good morning Du, how are you today?"),
        ("imperative", "Okay, do it: compute (23 - 7) * 4 and state the final number."),
        ("correction", "That was not what I asked. You did not state the number."),
    ]
    t0 = time.time()
    for tag, text in probes:
        out = await orch.run_cycle(text, "human")
        if not out or len(out.strip()) < 5:
            failures.append(f"{tag}: empty/short output ({out!r})")
        print(f"  [{tag}] {('OK' if out else 'EMPTY')}: {(out or '')[:70]}")
    secs = time.time() - t0

    msgs = [r.getMessage() for r in records]
    if any("recovered on fallback" in m for m in msgs):
        failures.append("hot lane degraded to fallback during probes")
    if any("JSON parse failed" in m for m in msgs):
        failures.append("JSON parse failures occurred")
    if not any("content-mode" in m for m in msgs):
        failures.append("task valve never fired on the imperative probe")
    if not any("human correction detected" in m for m in msgs):
        failures.append("correction detector never fired")

    print(f"\n  {len(probes)} cycles in {secs:.0f}s")
    if failures:
        print("  SMOKE FAIL:")
        for f in failures:
            print("   -", f)
        return 1
    print("  SMOKE PASS — stack is sane.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
