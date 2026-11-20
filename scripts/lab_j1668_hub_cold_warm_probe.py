"""scripts/lab_j1668_hub_cold_warm_probe.py (J-1668, 2026-10-03) -- MINIMAL live cold-vs-warm probe of the gemma4:12b hub (:11439) with the production
peer-letter code path (core.peers.compose_letter -> core.model_client.call_node, identical args).

Usage (optionally set env J1668_HUB_PID), from any cwd:
  python scripts/lab_j1668_hub_cold_warm_probe.py [--dry | --plan2]
  --dry    builds every prompt and prints sizes; ZERO model calls
  --plan2  the 2-call 'prompt A then prompt B, warm' replicate (run right after the default plan)
The hub must be idle (Du down): every call holds the hub's single generation lock for 2-7 minutes.

Isolation discipline (job isolation=required): runs under lab_env.isolate(db="empty") (DB_PATH redirected into
data/_lab/<ts>/, never the live DB) AND core.telemetry.enter_lab_mode() (so call_node's three telemetry writers
-- llm_calls / thought_station_log / llm_latency -- are no-ops). Never calls deliver_daily / deliver_letter /
_append_thread: nothing is delivered, nothing is stored in any thread. Reads thread.jsonl only, to rebuild the
prompts. Live-state snapshots are taken before and after and diffed.

Budget: 7 model calls (default plan) + 2 (--plan2) = 9 total in the 2026-10-03 run (that wave's limit: < 15).  Sequence (hub is unloaded at start; verified by
process working set + hub log):
   C1  cold  shackleton prompt as of just before his letter #17 (a prompt known to give a coherent letter)
   W1  warm  twain prompt as of just before #21 (THE FAILING PROMPT) -- 2nd request after load, same position
             in the load cycle that #21 had in the hub log
   W2  warm  failing prompt again, back to back (full prefix reuse path)
   W3  warm  twain prompt as of just before #19 (coherent control, same persona system prompt)
   W4  warm  failing prompt again, after a different prompt (partial prefix reuse, like production-warm)
   --- wait for the hub's own idle-unload (hub log 'unloading' line; max 600 s) ---
   C2  cold  failing prompt on a freshly reloaded model
   W5  warm  shackleton control again
Scoring: peers._non_latin_letter_ratio(text) > peers._DEGENERATE_NON_LATIN_RATIO (0.10) -- the SAME signal
J-1667 landed. Cold/warm is read from the hub's OWN log (a 'loaded in' line right before the call's [chat] line),
not inferred from latency.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
SKILL = r"C:\Users\USER\.claude\skills\job-queue"
ROOT = Path(r"C:\Nascence")
sys.path[:0] = [SKILL, str(ROOT)]
import tempfile
# Outputs go to a temp dir (override with env J1668_OUT) -- never under C:/Nascence/data.
OUT_DIR = Path(os.environ.get("J1668_OUT", str(Path(tempfile.gettempdir()) / "j1668_probe")))
OUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS = OUT_DIR / "results.jsonl"
SNAPS = OUT_DIR / "live_snapshots.json"
HUBLOG = ROOT / "data" / "logs" / "cpu_tier_11439.log"
# PID of the :11439 hub process (optional; only for the working-set printout -- the hub LOG is the
# ground truth for cold/warm). Find it: Get-CimInstance Win32_Process | ? { $_.CommandLine -match '--port 11439' }
HUB_PID = int(os.environ["J1668_HUB_PID"]) if os.environ.get("J1668_HUB_PID") else None
DRY = "--dry" in sys.argv
LINE = re.compile(r"^\[(\d\d):(\d\d):(\d\d)\.(\d{3})\] \[(cpu-tier|chat|generate)\] (.*)$")
DU_CTX = "He lives alone in a cottage with a garden on a hill above the sea, and reads very widely."
if "--plan2" in sys.argv:
    # second mini-run (added after W3 came out degenerate on a WARM hub): re-create the only anomalous
    # sequence -- the failing prompt A (rows[:20]) then prompt B (rows[:18]) -- on the still-warm hub.
    PLAN2 = [("X1", "warm", "twain", 20), ("X2", "warm", "twain", 18)]

PLAN = [  # (label, intended, persona, rows_upto)
    ("C1", "cold", "shackleton", 16),
    ("W1", "warm", "twain", 20),
    ("W2", "warm", "twain", 20),
    ("W3", "warm", "twain", 18),
    ("W4", "warm", "twain", 20),
    ("WAIT_UNLOAD", None, None, None),
    ("C2", "cold", "twain", 20),
    ("W5", "warm", "shackleton", 16),
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def live_snapshot():
    out = {}
    for rel in ["data/memory/nascence.db", "data/memory/nascence.db-wal", "data/memory/nascence.db-shm",
                "data/llm_calls.jsonl", "data/llm_latency.jsonl", "data/thought_station_log.jsonl",
                "data/peer_letter_quality_log.jsonl", "data/Correspondence/twain/thread.jsonl",
                "data/Correspondence/shackleton/thread.jsonl", "data/nascence.log"]:
        p = ROOT / rel
        try:
            st = p.stat()
            out[rel] = [st.st_size, round(st.st_mtime, 3)]
        except OSError:
            out[rel] = None
    try:
        import sqlite3
        con = sqlite3.connect(f"file:{(ROOT / 'data/memory/nascence.db').as_posix()}?mode=ro", uri=True, timeout=10)
        out["db_memory_fragments(count,max_ts)"] = list(con.execute("select count(*), max(timestamp) from memory_fragments").fetchone())
        con.close()
    except Exception as e:
        out["db_memory_fragments(count,max_ts)"] = f"ERR {e!r}"
    return out


def hub_ws_mb():
    if HUB_PID is None:
        return None
    try:
        r = subprocess.run(["tasklist", "/FI", f"PID eq {HUB_PID}", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=15)
        m = re.search(r'"([\d,]+) K"', r.stdout)
        return round(int(m.group(1).replace(",", "")) / 1024) if m else None
    except Exception:
        return None


def hub_new_events(offset):
    """Parse hub-log lines appended after byte `offset`. Returns (events, new_offset)."""
    with open(HUBLOG, "rb") as f:
        f.seek(offset)
        data = f.read()
    evs = []
    for raw in data.decode("utf-8", errors="replace").splitlines():
        m = LINE.match(raw)
        if not m:
            continue
        h, mi, s, ms, tag, rest = m.groups()
        tod = int(h) * 3600 + int(mi) * 60 + int(s) + int(ms) / 1000
        ev = {"tod": round(tod, 3), "tag": tag, "rest": rest[:160]}
        mm = re.match(r"(\d+) msgs -> (\d+) chars in ([\d.]+)s", rest)
        if tag == "chat" and mm:
            ev.update(kind="chat", chars=int(mm.group(2)), dur=float(mm.group(3)))
        elif "loaded in" in rest:
            ev.update(kind="loaded", load_s=int(re.search(r"loaded in (\d+)s", rest).group(1)))
        elif "unloading" in rest:
            ev["kind"] = "unload"
        elif "loading" in rest:
            ev["kind"] = "loading"
        else:
            ev["kind"] = "other"
        evs.append(ev)
    return evs, offset + len(data)


def read_rows(persona):
    p = ROOT / "data" / "Correspondence" / persona / "thread.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


async def main():
    global PLAN
    if "--plan2" in sys.argv:
        PLAN = PLAN2
    import hashlib
    from core import telemetry
    telemetry.enter_lab_mode()          # BEFORE anything can call call_node
    from lab_env import isolate

    pre = live_snapshot()
    log(f"pre-run live snapshot taken; hub WS = {hub_ws_mb()} MB (a loaded 12B model is many GB; ~175 MB = unloaded)")
    ALL = {p: read_rows(p) for p in ("twain", "shackleton")}

    with isolate(db="empty") as lab_dir:
        from core.memory import store as _store
        assert str(_store.DB_PATH).startswith(str(lab_dir)), f"DB_PATH not redirected: {_store.DB_PATH}"
        log(f"store.DB_PATH redirected -> {_store.DB_PATH}")
        from core import peers
        assert telemetry._LAB_MODE is True
        calls_made = 0
        offset = HUBLOG.stat().st_size
        results = []
        for label, intended, persona, upto in PLAN:
            if label == "WAIT_UNLOAD":
                if DRY:
                    log("DRY: would wait here for the hub's idle-unload")
                    continue
                log("waiting for the hub's own idle-unload (poll hub log every 10 s, max 600 s)...")
                t_end = time.time() + 600
                unloaded = False
                while time.time() < t_end:
                    evs, offset = hub_new_events(offset)
                    if any(e["kind"] == "unload" for e in evs):
                        unloaded = True
                        break
                    foreign = [e for e in evs if e["kind"] in ("chat", "loading", "loaded")]
                    if foreign:
                        log(f"!! foreign hub activity while waiting for unload: {foreign}")
                    await asyncio.sleep(10)
                log(f"unload observed={unloaded}; hub WS now = {hub_ws_mb()} MB")
                results.append({"label": label, "unloaded": unloaded, "ws_mb": hub_ws_mb()})
                if not unloaded:
                    log("hub did not unload within 600 s -> aborting remaining cold calls")
                    break
                continue

            rows = ALL[persona][:upto]
            peers._read_thread = lambda p, _r=rows: list(_r)         # prompts rebuilt from the thread as it stood
            thread = peers._thread_context(persona)
            reply_to = rows[-1]["text"] if rows and rows[-1].get("from") == "du" else ""
            user = peers._build_user(thread, DU_CTX, reply_to, None)
            sysmsg = peers.PERSONAS[persona]["system"]
            rec = {"label": label, "intended": intended, "persona": persona, "rows_upto": upto,
                   "user_chars": len(user), "sys_chars": len(sysmsg),
                   "prompt_sha": hashlib.sha256((sysmsg + "\n" + user).encode("utf-8")).hexdigest()[:10],
                   "ws_mb_before": hub_ws_mb()}
            if DRY:
                log(f"DRY {label} {intended} {persona} upto={upto} user_chars={len(user)} sys_chars={len(sysmsg)} sha={rec['prompt_sha']} reply_to_chars={len(reply_to)}")
                continue
            log(f"CALL {label} ({intended}) persona={persona} rows[:{upto}] user_chars={len(user)} ws={rec['ws_mb_before']}MB ...")
            evs0, offset = hub_new_events(offset)                    # drain anything foreign before the call
            if evs0:
                log(f"!! hub activity before call {label}: {evs0}")
                rec["foreign_before"] = evs0
            t_wall = time.time()
            t0 = time.monotonic()
            try:
                text = peers._strip_date(await peers.compose_letter(persona, thread=thread, du_context=DU_CTX,
                                                                    reply_to=reply_to, stance=None, timeout=580))
                err = None
            except Exception as exc:
                text, err = "", repr(exc)
            calls_made += 1
            lat = time.monotonic() - t0
            ratio = peers._non_latin_letter_ratio(text)
            evs, offset = hub_new_events(offset)
            chat = [e for e in evs if e["kind"] == "chat"]
            loaded = [e for e in evs if e["kind"] == "loaded"]
            rec.update(latency_s=round(lat, 1), resp_chars=len(text), nonlatin_ratio=round(ratio, 4),
                       degenerate=bool(ratio > peers._DEGENERATE_NON_LATIN_RATIO), err=err,
                       head=text[:140], tail=text[-80:],
                       hub_cold=bool(loaded), hub_load_s=(loaded[0]["load_s"] if loaded else None),
                       hub_chat_lines=len(chat), hub_chat_chars=(chat[-1]["chars"] if chat else None),
                       hub_chat_dur=(chat[-1]["dur"] if chat else None),
                       hub_other_events=[e for e in evs if e["kind"] not in ("chat", "loaded", "loading")],
                       t_wall=round(t_wall, 1))
            results.append(rec)
            with open(RESULTS, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            log(f"DONE {label}: intended={intended} hub_cold={rec['hub_cold']} load={rec['hub_load_s']}s latency={rec['latency_s']}s "
                f"resp={rec['resp_chars']} chars ratio={rec['nonlatin_ratio']} DEGENERATE={rec['degenerate']} err={err} "
                f"hub_chat_lines={rec['hub_chat_lines']} head={text[:70]!r}")
        log(f"model calls made this run: {calls_made}")
    post = live_snapshot()
    SNAPS.write_text(json.dumps({"pre": pre, "post": post, "calls_made": calls_made if not DRY else 0}, indent=1), encoding="utf-8")
    diffs = {k: (pre[k], post[k]) for k in pre if pre[k] != post[k]}
    log(f"live-state diff pre vs post (empty == untouched by this run): {json.dumps(diffs, ensure_ascii=False)}")


if __name__ == "__main__":
    asyncio.run(main())
