"""
Launch CPU Tier Hubs in LAZY mode (load on first request, auto-unload when idle).
"""
import os
import sys
import time
import urllib.request
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
PYTHON = sys.executable
RESOLVE = ROOT / "scripts" / "resolve_blob.py"
HUB = ROOT / "scripts" / "nascence_cpu_server.py"
LOGDIR = ROOT / "data" / "logs"

LOGDIR.mkdir(parents=True, exist_ok=True)

tier = [
    {"name": "Judge1 gemma4:12b", "model": "gemma4", "tag": "12b", "alias": "gemma4:12b", "port": 11439, "threads": 14},
    {"name": "Judge2 falcon3:7b", "model": "falcon3", "tag": "7b", "alias": "falcon3:7b", "port": 11440, "threads": 14},
    {"name": "Dreamer yi34b (lazy)", "model": "yi", "tag": "34b-v1.5", "alias": "yi:34b-v1.5", "port": 11442, "threads": 20},
]


def test_api(port: int) -> bool:
    try:
        url = f"http://127.0.0.1:{port}/api/tags"
        req = urllib.request.urlopen(url, timeout=3)
        return req.status == 200
    except Exception:
        return False


def main():
    for t in tier:
        port = t["port"]
        if test_api(port):
            print(f"[NASCENCE] {t['name']} already up on :{port}")
            continue

        blob = subprocess.check_output([PYTHON, str(RESOLVE), t["model"], t["tag"]], text=True).strip()
        if not blob:
            print(f"[NASCENCE] WARN: no blob for {t['name']}")
            continue

        log_file = LOGDIR / f"cpu_tier_{port}.log"
        err_file = LOGDIR / f"cpu_tier_{port}.log.err"

        cmd = [
            PYTHON,
            str(HUB),
            "--model", blob,
            "--alias", t["alias"],
            "--port", str(port),
            "--threads", str(t["threads"]),
            "--ctx", "8192",
            "--lazy",
            "--idle-unload", "300",
        ]

        print(f"[NASCENCE] Starting {t['name']} on :{port} (LAZY, idle-unload 300s)...")
        f_out = open(log_file, "a", encoding="utf-8")
        f_err = open(err_file, "a", encoding="utf-8")
        
        # Use win32 flags if on Windows
        flags = 0
        if sys.platform == "win32":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=f_out,
            stderr=f_err,
            close_fds=True,
            creationflags=flags,
        )

    # Wait briefly and check port health
    time.sleep(2)
    for t in tier:
        port = t["port"]
        if test_api(port):
            print(f"[NASCENCE] {t['name']} port UP on :{port} (LAZY mode, 0 MB idle RAM)")
        else:
            print(f"[NASCENCE] WARN: {t['name']} port not up on :{port}")

if __name__ == "__main__":
    main()
