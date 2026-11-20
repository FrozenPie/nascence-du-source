"""J-4353 / F-5105 fingerprint canary for the human-cycle lab recipe (no LLM, no hub calls).
Activates a throwaway profile + rebase_human_cycle_paths(), imports the orchestrator, performs real writes
through left_lane.note_outcome and companion._save/_log, then asserts the data/ top level of this tree AND of
C:/Nascence/data is byte-identical before/after and that none of the formerly-leaking modules still points at
live data/. Run from a git worktree (data/ there is empty) -- never needs the live tree to be touched."""
import hashlib, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))

def fp(d: Path):
    h = hashlib.sha256(); n = 0
    if d.is_dir():
        for f in sorted(os.listdir(d)):
            p = d / f
            if p.is_file():
                h.update(f.encode()); h.update(hashlib.sha256(p.read_bytes()).digest()); n += 1
    return n, h.hexdigest()

DIRS = {ROOT / "data", Path(r"C:/Nascence/data")}
before = {d: fp(d) for d in DIRS}
import core  # noqa
from core.profile import activate_profile
prof = Path(activate_profile("_t4353"))
import core.orchestrator  # noqa
from lab_human_cycle_paths import rebase_human_cycle_paths, audit_live_paths, LEAKING_MODULES
done = rebase_human_cycle_paths(prof)
from core import left_lane, companion
left_lane.note_outcome("delivered", probe="J-4353")
companion._save(); companion._log({"event": "probe"})
after = {d: fp(d) for d in DIRS}
leaks = [x for x in audit_live_paths() if x.split(".")[1] in {m.split(".")[1] for m in LEAKING_MODULES}
         and any(x.startswith(m + ".") for m in LEAKING_MODULES)]
print("rebased", len(done), "attrs; profile writes landed:",
      (prof / "left_take_outcomes.jsonl").exists(), (prof / "companion_state.json").exists())
print("remaining live-pointing attrs in fixed modules:", leaks)
print("other modules still pointing at live data/ (info):", [x for x in audit_live_paths() if x not in leaks][:15])
ok = before == after and not leaks and (prof / "left_take_outcomes.jsonl").exists()
print("FINGERPRINT", "UNCHANGED" if before == after else f"CHANGED {before} -> {after}")
print("PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
