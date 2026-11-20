"""J-1932 / F-2557: HUD process vs Du process on the telemetry files. Offline, temp dir only, nvidia-smi stubbed.
Two real OS processes: 'du' appends numbered rows to llm_calls.jsonl via log_llm_call and calls kick() in a tight loop;
'hud' calls sample(force=True) in a tight loop (the HUD /api refresh). Caps are shrunk so _cap rewrites constantly.
CONTROL (hud runs with the owner check disabled = pre-fix behaviour) vs FIX. Metric: after the run, llm_calls.jsonl must be
parseable and its sequence numbers contiguous (a gap or an unparseable line = a lost/torn Du append); hardware_load/llm_usage
must have no unparseable lines. Then: owner stops -> the HUD resumes sampling within _OWNER_FRESH_S.
Usage: python scripts/test_telemetry_two_process.py [--secs 12]"""
import sys, os, time, json, subprocess, tempfile, pathlib, argparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core                                              # core BEFORE anything else
assert os.path.normcase(ROOT) != os.path.normcase(r"C:\Nascence"), "run from a throwaway worktree"
from core import telemetry as T

def setup(d):
    d = pathlib.Path(d)
    T._CALLS, T._HW, T._LLM, T._OWNER_STAMP = d/"llm_calls.jsonl", d/"hardware_load.jsonl", d/"llm_usage.jsonl", d/"owner.stamp"
    T._gpu_load = lambda: {}
    T._SAMPLE_MIN_GAP = 0.0
    T._CALLS_CAP, T._SERIES_CAP = int(os.environ.get("J1932_CAP", 200)), 20

def role_du(d, secs):
    setup(d); end = time.time() + secs; n = 0
    while time.time() < end:
        n += 1
        T.log_llm_call("m", node=str(n))
        if n % 3 == 0:
            T.kick(); w = T._worker
            if w: w.join(2)
    print(n)

def role_hud(d, secs, guest):
    setup(d)
    if not guest: T._OWNER_FRESH_S = -1.0           # control: pre-fix behaviour (always samples)
    end = time.time() + secs
    while time.time() < end:
        T.sample(force=True)

def check(d, total):
    d = pathlib.Path(d); out = {}
    for name in ("llm_calls", "hardware_load", "llm_usage"):
        bad = 0; rows = []
        for l in (d/f"{name}.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
            try: rows.append(json.loads(l))
            except Exception: bad += 1
        out[name] = (len(rows), bad)
        if name == "llm_calls":
            seq = [int(r["node"]) for r in rows]
            out["gaps"] = sum(1 for a, b in zip(seq, seq[1:]) if b != a + 1)
            out["last_seq"] = seq[-1] if seq else None
    return out

def run(guest, secs):
    d = tempfile.mkdtemp(prefix="j1932_")
    py = sys.executable; me = os.path.abspath(__file__)
    du = subprocess.Popen([py, me, "--role", "du", "--dir", d, "--secs", str(secs)], stdout=subprocess.PIPE, text=True)
    hud = subprocess.Popen([py, me, "--role", "hud" if guest else "hudctl", "--dir", d, "--secs", str(secs)])
    total = int(du.communicate()[0].strip() or 0); hud.wait()
    return d, total, check(d, total)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--role"); ap.add_argument("--dir"); ap.add_argument("--secs", type=float, default=12)
    a = ap.parse_args()
    if a.role == "du": role_du(a.dir, a.secs); sys.exit()
    if a.role in ("hud", "hudctl"): role_hud(a.dir, a.secs, a.role == "hud"); sys.exit()
    fails = []
    for guest in (False, True):
        d, total, r = run(guest, a.secs)
        print(("FIX    " if guest else "CONTROL"), "du appended", total, r, flush=True)
        if guest and (r["gaps"] or any(r[k][1] for k in ("llm_calls", "hardware_load", "llm_usage"))): fails.append("fix still loses/tears")
        if guest and r["last_seq"] != total: fails.append("tail seq != total appended")
    # handoff: stale owner stamp -> guest samples; fresh stamp -> guest no-op
    d = tempfile.mkdtemp(prefix="j1932h_"); setup(d); T._OWNER_STAMP.write_text("1")
    T._SAMPLE_MIN_GAP = 0.0; T._OWNER_FRESH_S = 30.0
    T.sample(force=True); fresh_rows = T._HW.exists() and T._HW.read_text().strip() != ""
    old = time.time() - 60; os.utime(T._OWNER_STAMP, (old, old))
    T.sample(force=True); stale_rows = T._HW.exists() and T._HW.read_text().strip() != ""
    print("guest no-op while owner stamp fresh:", not fresh_rows, "| guest resumes when stamp stale:", stale_rows)
    if fresh_rows or not stale_rows: fails.append("handoff")
    print("PASS" if not fails else "FAIL " + "; ".join(fails)); sys.exit(1 if fails else 0)
