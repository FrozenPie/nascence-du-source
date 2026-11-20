"""J-2977: scripts/rejoin_appendix_a_j2977.py joins a telemetry label to the function of the file version that was
RUNNING, not the current one. Builds a throw-away git repo and a fake data dir under a temp dir; touches no live data.

Run from the worktree:  python scripts/_test_J2977_rejoin_appendix_a.py
"""
import datetime
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402,F401  (import core BEFORE any lab_env; this test needs no lab_env)
import rejoin_appendix_a_j2977 as R  # noqa: E402

assert (ROOT / "scripts" / "rejoin_appendix_a_j2977.py").exists()

V1 = '''def a():
    call_node_json("x")
def b():
    call_node_json("y")
'''
V2 = '''def pre():
    x = 1
    call_node_json("z")
''' + V1                      # every line of V1 moves down by 3


def ts(day, hh, mm=0):
    return datetime.datetime(2026, 10, day, hh, mm).timestamp()


def git(repo, *args, when=None):
    env = dict(os.environ)
    if when is not None:
        iso = datetime.datetime.fromtimestamp(when).strftime("%Y-%m-%dT%H:%M:%S")
        env["GIT_COMMITTER_DATE"] = iso
        env["GIT_AUTHOR_DATE"] = iso
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True).stdout


def main():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        repo, data = td / "repo", td / "data"
        (repo / "core").mkdir(parents=True)
        data.mkdir()
        git(repo, "init", "-q", "-b", "master")
        git(repo, "config", "user.email", "t@example.invalid")
        git(repo, "config", "user.name", "t")
        (repo / "core" / "mod.py").write_text(V1, encoding="utf-8")
        git(repo, "add", "core/mod.py")
        git(repo, "commit", "-q", "-m", "v1", when=ts(10, 9))
        (repo / "core" / "mod.py").write_text(V2, encoding="utf-8")
        git(repo, "add", "core/mod.py")
        git(repo, "commit", "-q", "-m", "v2", when=ts(20, 9))

        # Du started on the 15th (loads V1), edits landed on the 20th, Du restarted on the 22nd (loads V2).
        log = data / "nascence.log"
        log.write_text(
            "2026-10-15 08:00:00,000 [nascence.main] Nascence is awake. Enter text to begin a thought cycle.\n"
            "2026-10-22 08:00:00,000 [nascence.main] Nascence is awake. Enter text to begin a thought cycle.\n",
            encoding="utf-8")
        starts = R.process_starts(log)
        assert len(starts) == 2 and starts[0] < starts[1], starts

        repo_o = R.Repo(repo, "master")
        jn = R.Joiner(repo_o, starts)

        # 1. the drift case: a row on the 21st, AFTER the v2 commit but BEFORE the restart, label line 2 (V1's a()).
        fn, tag = jn.resolve("core.mod", 2, ts(21, 12))
        assert (fn, tag) == ("a", "B"), (fn, tag)                 # running version = V1
        assert jn.resolve_current("core.mod", 2, ts(25, 0)) == "pre", "old method must show the misattribution"
        # 2. a row after the restart: label line 7 is b() in V2
        assert jn.resolve("core.mod", 7, ts(23, 12)) == ("b", "B")
        # 3. a row whose line is not a call anywhere falls back to B and is flagged
        fn, tag = jn.resolve("core.mod", 1, ts(23, 12))
        assert tag.endswith("!"), tag
        # 4. no file: not a crash
        assert jn.resolve("asyncio.events", 94, ts(23, 12)) == ("?", "nopath")

        # 5. CLI end to end on fake data: 3 rows at the inventory-anchor week, one json out, no live data read
        rows = [
            {"ts": ts(30, 10), "model": "m", "node": "1", "by": "core.mod:2"},         # V1 era? start 22nd => V2 line 2 not a call
            {"ts": ts(30, 11), "model": "m", "node": "1", "by": "core.mod:5(Cls)"},
            {"ts": ts(30, 12), "model": "m", "node": "1", "by": "judge_panel"},
        ]
        (data / "llm_latency.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        out = td / "out.json"
        res = subprocess.run([sys.executable, str(ROOT / "scripts" / "rejoin_appendix_a_j2977.py"), "--repo", str(repo),
                              "--data", str(data), "--json", str(out)], capture_output=True, text=True)
        assert res.returncode == 0, res.stderr[-800:]
        payload = json.loads(out.read_text(encoding="utf-8"))
        inv = payload["inv"]
        assert "core.mod:a(Cls)" in inv, list(inv)                 # line 5 in V2 is a(), with the class suffix kept
        assert inv["core.mod:a(Cls)"]["new"][0] == 1
        assert payload["other_labels_30d_inv"].get("judge_panel") == 1

    # 6. registry matching: key, alias, node class
    reg = [{"id": "P-1", "keys": ["core.deliberation:_deliberate_run"]},
           {"id": "P-2", "keys": ["nodes.critic_node:CriticNode"]},
           {"id": "P-3", "keys": ["core.x:f#sysarg"]}]
    assert R.registry_match("core.deliberation:deliberate", reg) == ["P-1"]
    assert R.registry_match("core.node_base:NodeBase.run(CriticNode)", reg) == ["P-2"]
    assert R.registry_match("core.x:f", reg) == ["P-3"]
    assert R.fmt_pct(175, 1753) == "-90%" and R.fmt_pct(5, 0) == "new" and R.fmt_pct(0, 0) == "0"
    print("J-2977 rejoin test: OK")


if __name__ == "__main__":
    main()
