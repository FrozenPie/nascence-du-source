"""J-3719 Ramses arm: same harness as lab_j3719_r1_run.py but against mixtral:8x7b (:11438) / command-r7b (:11441) on Ramses
(founder confirmed Ramses free 2026-11-17). Usage: lab_j3719_ramses_run.py <hub> <out.jsonl> [cap]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lab_j3719_r1_run as r
rp = r.rp
rp.FORBIDDEN = ()
rp.HUBS.update({"mixtral": "http://LAN-HOST:11438", "cr7b": "http://LAN-HOST:11441", "granite": "http://LAN-HOST:11437"})
if __name__ == "__main__":
    hub, out = sys.argv[1], Path(sys.argv[2]); cap = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    cs = r.all_cases(cap)
    print(len(cs), "cases", flush=True)
    print("asked", rp.run(out, [hub], cs, ask_fn=lambda u, s, us, k: rp.ask(u, s, us, k, timeout=120.0, num_predict=200)), flush=True)
    rows = [__import__("json").loads(x) for x in out.read_text(encoding="utf-8").splitlines() if x.strip()]
    rep = rp.report(rows)
    out.with_name(out.stem + "_report.json").write_text(__import__("json").dumps(rep, indent=1), encoding="utf-8")
    for k, v in rep.items(): print(k, __import__("json").dumps(v))
