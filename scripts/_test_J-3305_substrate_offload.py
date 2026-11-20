"""J-3305 (F-3900, J-3247 section 3e): the substrate tick's couriers + felt_recall run off the asyncio event loop.
Hermetic: `core` is imported BEFORE lab_env, core.__file__ is asserted inside this tree, lab_env.isolate() redirects
felt_recall / theta_shadow / couriers paths into the lab dir, transport_manager's state goes to a temp dir, every
model-free helper that would touch data/ is stubbed, and the live felt/theta/courier logs are hash-canaried.
Run: python scripts/_test_J-3305_substrate_offload.py"""
import sys, json, hashlib, pathlib, asyncio, threading, time, sqlite3, tempfile
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(ROOT)), core.__file__
from core import orchestrator as orch
from core import couriers as cour
from core import felt_recall as fr
from core import theta_shadow as theta
from core import transport_manager as tm
sys.path.append(str(pathlib.Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env


def sha(p):
    p = pathlib.Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


CANARY = [ROOT / "data" / n for n in ("felt_recall_shadow.jsonl", "theta_shadow.jsonl", "couriers_log.jsonl",
                                       "couriers_state.json", "transport_lines.json")]
before = [sha(p) for p in CANARY]
MAIN = threading.get_ident()
CALLS: list = []


class Mono:
    def __init__(self, holding):
        self._h = holding

    def _train_holding(self):
        if isinstance(self._h, Exception):
            raise self._h
        return self._h


def install(ctx=False, snd=False, felt_live=False, sleep=0.0, ctx_raises=False, felt_raises=False):
    CALLS.clear()

    def _ctx():
        CALLS.append(("context_echo", threading.get_ident(), time.monotonic()))
        time.sleep(sleep)
        if ctx_raises:
            raise RuntimeError("boom")
        return ctx

    def _snd():
        CALLS.append(("sound_echo", threading.get_ident(), time.monotonic()))
        return snd

    def _felt(affect=None):
        CALLS.append(("felt", threading.get_ident(), time.monotonic(), affect))
        time.sleep(sleep)
        if felt_raises:
            raise RuntimeError("boom")

    cour.context_echo, cour.sound_echo, fr.on_substrate_tick = _ctx, _snd, _felt
    fr.FELT_RECALL_LIVE = felt_live


def names():
    return [c[0] for c in CALLS]


def run(nodes, affect="AFF"):
    asyncio.run(orch._substrate_courier_felt_tick(nodes, affect))


real = (cour.context_echo, cour.sound_echo, fr.on_substrate_tick, fr.FELT_RECALL_LIVE)

# ---- 1. order, worker thread, same single worker, gates --------------------------------------------------------
install()
run({})
assert names() == ["context_echo", "sound_echo", "felt"], names()                     # couriers first, felt next
assert all(c[1] != MAIN for c in CALLS), "blocking calls must not run on the loop thread"
assert len({c[1] for c in CALLS}) == 1, "couriers and felt_recall share ONE worker thread (never overlap)"
assert CALLS[2][3] == "AFF"                                                              # affect passed through
print("1 order+thread: couriers->felt, one worker thread, off the loop:", names())

install(ctx=True)                                                                         # `or` short-circuit
run({})
assert names() == ["context_echo", "felt"], names()
install()
run({"monologue": Mono(True)})                                                           # TRAIN-HOLD: couriers skipped
assert names() == ["felt"], names()
install()
run({"monologue": Mono(False)})
assert names() == ["context_echo", "sound_echo", "felt"], names()
install()
run({"monologue": Mono(RuntimeError("x"))})                                              # gate lookup raises -> skipped (as before)
assert names() == ["felt"], names()
print("1b gates: short-circuit, TRAIN-HOLD, raising gate behave as the inline code did")

# ---- 2. fail-open per leg ---------------------------------------------------------------------------------------
install(ctx_raises=True)
run({})
assert names() == ["context_echo", "felt"], names()                                       # courier raise does not skip felt
install(felt_raises=True)
run({})                                                                                   # felt raise never escapes
assert names() == ["context_echo", "sound_echo", "felt"]
print("2 fail-open: a courier exception leaves felt_recall running; a felt exception does not escape")

# ---- 3. FELT_RECALL_LIVE: apply_prior mutates state.affect -> felt stays on the loop thread, after couriers ------
install(felt_live=True)
run({})
assert names() == ["context_echo", "sound_echo", "felt"], names()
assert CALLS[0][1] != MAIN and CALLS[1][1] != MAIN and CALLS[2][1] == MAIN, [c[1] for c in CALLS]
print("3 LIVE: couriers on the worker, felt_recall inline on the loop (affect mutation never leaves the loop)")

# ---- 4. the loop keeps ticking while the worker blocks ----------------------------------------------------------
install(sleep=0.4)


async def _hb():
    beats = 0

    async def beat():
        nonlocal beats
        while True:
            await asyncio.sleep(0.02)
            beats += 1
    t = asyncio.create_task(beat())
    t0 = time.monotonic()
    await orch._substrate_courier_felt_tick({}, None)
    dt = time.monotonic() - t0
    t.cancel()
    return beats, dt


beats, dt = asyncio.run(_hb())
assert dt >= 0.75 and beats >= 20, (beats, dt)        # ~0.8 s of blocking work, >= 20 heartbeats on the 20 ms timer
print(f"4 non-blocking: {beats} loop heartbeats during {dt:.2f}s of blocking courier+felt work")
cour.context_echo, cour.sound_echo, fr.on_substrate_tick, fr.FELT_RECALL_LIVE = real

# ---- 5. REAL felt_recall.on_substrate_tick on the worker, in an isolated lab ----------------------------------------
with lab_env.isolate(also=[(fr, ["_SHADOW_LOG", "_DB", "_COURIER_LOG"]), (theta, ["_SHADOW_LOG", "_DB"]),
                           (cour, ["_DB", "_STATE", "_DELIVERY_LOG"])], db="empty") as lab_dir:
    fr._get_baseline_valence = lambda: -0.0929
    fr._register_dispatcher_line = lambda dim, place, now: {"verdict": "none", "cold_start": False, "weight": 0.0}
    theta.log_ray = lambda *a, **k: {}
    fr.FELT_RECALL_LIVE = False
    fr._prev_tuple = {"place": "study", "weather": "overcast", "sounds": []}
    fr._last_fired.clear()
    fr._current_tuple = lambda: {"place": "study", "weather": "drizzle", "sounds": []}
    cour.context_echo, cour.sound_echo = (lambda: False), (lambda: False)
    fr.SHADOW_LOG_ROWS = None
    fr._SHADOW_LOG.parent.mkdir(parents=True, exist_ok=True)
    fr._SHADOW_LOG.write_text("", encoding="utf-8")
    run({}, affect=None)
    rows = [json.loads(l) for l in fr._SHADOW_LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 1 and rows[0]["dim"] == "weather" and rows[0]["fired"], rows
    assert fr._prev_tuple["weather"] == "drizzle"       # module state advanced exactly as in the inline path
    print("5 real felt_recall on the worker: 1 shadow row written in the lab dir, edge state advanced")

    # ---- 6. latent bug: _build_prior returned a 3-tuple on the SOUND_COORD_MATCH empty-scored path ------------------
    dbp = pathlib.Path(lab_dir) / "j3305_fc.db"
    c = sqlite3.connect(dbp)
    c.execute("CREATE TABLE fragment_context (fragment_id TEXT, weather TEXT, fire TEXT, light_band TEXT, cat_at TEXT, "
              "place TEXT, valence REAL, arousal REAL, tuple_ts REAL, source TEXT, sounds TEXT, sound_onset TEXT)")
    # candidate admitted by the widened WHERE (sound_onset NOT NULL) but unmeasurable -> dropped by _sound_closeness
    c.execute("INSERT INTO fragment_context VALUES ('f1','overcast',NULL,'dim',NULL,'study',0.2,0.5,1.0,'x','[]','not-json')")
    c.commit(); c.close()
    fr._DB = dbp
    fr.SOUND_COORD_MATCH = True
    try:
        out = fr._build_prior("sound:tui_song", "tui_song", {"place": "study"})
    finally:
        fr.SOUND_COORD_MATCH = False
    assert len(out) == 4 and out == (None, 0, None, []), out
    prior, n, frac, ids = out                            # the unpack _handle_edge does must not raise
    print("6 _build_prior empty-scored path returns the 4-tuple:", out)
cour.context_echo, cour.sound_echo, fr.on_substrate_tick, fr.FELT_RECALL_LIVE = real

# ---- 7. transport_manager lock: no lost updates under the worker thread + loop-side callers ---------------------------
with tempfile.TemporaryDirectory() as td:
    tm._STATE = pathlib.Path(td) / "transport_lines.json"
    tm._SHADOW_LOG = pathlib.Path(td) / "transport_shadow.jsonl"
    N_THREADS, N_EACH = 8, 40

    def hammer(i):
        for k in range(N_EACH):
            tm.observe("shared", 1000.0 + i * 1000 + k, 1.0)
            tm.verdict("shared")

    ts = [threading.Thread(target=hammer, args=(i,)) for i in range(N_THREADS)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    total = tm._load()["lines"]["shared"]["n_total"]
    assert total == N_THREADS * N_EACH, total
    assert hasattr(tm.observe, "__wrapped__") and hasattr(tm.dispatch_tick, "__wrapped__") and hasattr(tm.evaluate, "__wrapped__")
    print(f"7 transport_manager: {N_THREADS} threads x {N_EACH} observe+verdict -> n_total={total} (no lost updates)")

after = [sha(p) for p in CANARY]
assert before == after, (before, after)
print("OK: live canaries unchanged")
