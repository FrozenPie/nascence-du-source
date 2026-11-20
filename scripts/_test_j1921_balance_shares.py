"""J-1921 / F-2548: idle_allocator balance_world / balance_light read the 0..1 shares ("reality_share"/"light_share"),
not the COUNT keys -- shadow-only, kill-switched, with a one-time reset of the two balance channels' constant-0.0 history.

Proves, against the pre-change module (git show <old-rev>:core/idle_allocator.py, loaded under another name):
  [A] channel unit tests: raw == (TARGET - share)/TARGET on a fake shares dict (both axes, edge values), the key-missing
      fallback to the old keys (== old module's answer), BALANCE_USE_SHARES=False == the old module exactly.
  [B] history versioning: a 500/500-zeros balance history is dropped ONCE (balance_schema stamped 2, other channels'
      history/streak untouched), not again on the next tick; kill switch off = no reset and no stamp; fresh / corrupt
      state file fail open; no .tmp left behind.
  [C] full-fidelity replay: the real shadow_tick() of OLD and NEW driven tick-for-tick over the last N rows of a COPY/READ of
      data/logs/idle_shadow.jsonl (every non-balance channel replays its logged raw; the balance channels are the real
      code fed the shares embedded in each row's lineage) from the REAL persisted state (500 zeros) -- balance wins fall,
      balance raw is non-zero and varies, p_norm leaves 1.0, and NO other channel's raw or p_norm changes.
  [D] a scenario with the balance gates closed: the whole record (minus ts) and the state file are identical between OLD and
      NEW except the balance_schema stamp.
All state/log paths are temp; no model calls; no network; core imported BEFORE anything else.  Run it from a throwaway
worktree, never from C:\\Nascence.  Read-only reads of the live shadow log / state are only for [C] and only via --shadow-log / --state.
Usage: python scripts/_test_j1921_balance_shares.py [--old-rev fa240f8] [--shadow-log PATH] [--state PATH] [--ticks 4000]"""
import sys, os, json, random, tempfile, subprocess, importlib.util, argparse, copy, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import core                                                         # core BEFORE anything else (live-store safety)
assert os.path.abspath(core.__file__).lower().startswith(ROOT.lower()), core.__file__
assert os.path.normcase(ROOT) != os.path.normcase(r"C:\Nascence"), "run from a throwaway worktree, never the live tree"
import socket
def _no_net(*a, **k):
    raise OSError("J-1921 test: network blocked")
socket.socket.connect = _no_net; socket.socket.connect_ex = _no_net
try:
    socket.create_connection(("127.0.0.1", 9), timeout=0.2); _blocked = False
except OSError as _e:
    _blocked = "blocked" in str(_e)
assert _blocked, "network block did not take"
from core import idle_allocator as new
from core import balance
assert os.path.abspath(new.__file__).lower().startswith(ROOT.lower())

ap = argparse.ArgumentParser()
ap.add_argument("--old-rev", default="fa240f8")
ap.add_argument("--shadow-log", default=r"C:\Nascence\data\logs\idle_shadow.jsonl")
ap.add_argument("--state", default=r"C:\Nascence\data\idle_allocator_state.json")
ap.add_argument("--ticks", type=int, default=4000)
args = ap.parse_args()
TMP = tempfile.mkdtemp(prefix="j1921_")

src = subprocess.run(["git", "-C", ROOT, "show", f"{args.old_rev}:core/idle_allocator.py"],
                     capture_output=True, text=True, encoding="utf-8", check=True).stdout
assert "BALANCE_USE_SHARES" not in src and "def _ch_balance_world" in src
old_path = os.path.join(TMP, "idle_allocator_old_j1921.py")
open(old_path, "w", encoding="utf-8").write(src)
spec = importlib.util.spec_from_file_location("idle_allocator_old_j1921", old_path)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)

FAILS = []
def check(name, ok, extra=""):
    print(("PASS " if ok else "FAIL ") + name + ((" -- " + str(extra)) if extra else ""), flush=True)
    if not ok:
        FAILS.append(name)

def point(mod, tag):
    d = os.path.join(TMP, tag)
    os.makedirs(os.path.join(d, "logs"), exist_ok=True)
    mod._DATA = __import__("pathlib").Path(d)
    mod._STATE = mod._DATA / "idle_allocator_state.json"
    mod._LOG = mod._DATA / "logs" / "idle_shadow.jsonl"
    assert os.path.abspath(str(mod._STATE)).lower().startswith(TMP.lower())
    return d

class FakeBalance:
    """Swap core.balance.shares/needs_* for fakes; restore on exit."""
    def __init__(self, shares, world=True, light=True):
        self.s, self.w, self.l = shares, world, light
    def __enter__(self):
        self.saved = (balance.shares, balance.needs_reality, balance.needs_light)
        balance.shares = lambda: dict(self.s)
        balance.needs_reality = lambda: self.w
        balance.needs_light = lambda: self.l
        return self
    def __exit__(self, *a):
        balance.shares, balance.needs_reality, balance.needs_light = self.saved

SH = {"reality_share": 0.3, "light_share": 0.4, "world": 1721, "self": 1724, "light": 665, "shadow": 793}

# =============================================================================================================
print("== [A] channel unit tests")
T = balance.TARGET
with FakeBalance(SH):
    w, l = new._ch_balance_world(), new._ch_balance_light()
check("A1 world raw == (TARGET - reality_share)/TARGET", abs(w[0] - (T - 0.3) / T) < 1e-12, w[0])
check("A2 light raw == (TARGET - light_share)/TARGET", abs(l[0] - (T - 0.4) / T) < 1e-12, l[0])
check("A3 justification / key / kind / lineage keep their shape",
      w[1:4] == ("reality", "regulatory", "reality-axis deficit=0.20") and l[1:4] == ("light", "regulatory", "light-axis deficit=0.10")
      and w[4] == {"shares": SH} and l[4] == {"shares": SH}, (w[1:4], l[1:4]))
with FakeBalance(SH):
    ow, ol = old._ch_balance_world(), old._ch_balance_light()
check("A4 the OLD module on the same shares reproduces the bug (raw 0.0, counts as the axis)", ow[0] == 0.0 and ol[0] == 0.0, (ow[0], ol[0]))

for label, shares in [("share==TARGET", {**SH, "reality_share": 0.5, "light_share": 0.5}),
                      ("share>TARGET", {**SH, "reality_share": 0.9, "light_share": 0.7}),
                      ("share==0.0 present", {**SH, "reality_share": 0.0, "light_share": 0.0}),
                      ("share None", {**SH, "reality_share": None, "light_share": None})]:
    with FakeBalance(shares):
        w, l = new._ch_balance_world(), new._ch_balance_light()
    rs, ls_ = shares["reality_share"] or 0.0, shares["light_share"] or 0.0
    ew, el = min(1.0, max(0.0, T - rs) / T), min(1.0, max(0.0, T - ls_) / T)
    check(f"A5 edge {label}", abs(w[0] - ew) < 1e-12 and abs(l[0] - el) < 1e-12 and 0.0 <= w[0] <= 1.0, (w[0], l[0]))

for label, shares in [("new keys absent, counts present", {"world": 1721, "light": 665, "self": 3}),
                      ("new keys absent, zero counts", {"world": 0, "light": 0, "self": 0}),
                      ("only legacy aliases", {"reality": 0.2, "self": 0.1}),
                      ("empty dict", {})]:
    with FakeBalance(shares):
        nw, nl = new._ch_balance_world(), new._ch_balance_light()
        ow, ol = old._ch_balance_world(), old._ch_balance_light()
    check(f"A6 key-missing fallback == old module ({label})", nw == ow and nl == ol, (nw[0], ow[0], nl[0], ol[0]))

new.BALANCE_USE_SHARES = False
try:
    with FakeBalance(SH):
        kw, kl = new._ch_balance_world(), new._ch_balance_light()
        ow, ol = old._ch_balance_world(), old._ch_balance_light()
    check("A7 BALANCE_USE_SHARES=False is exactly the old read", kw == ow and kl == ol and kw[0] == 0.0, (kw[0], kl[0]))
finally:
    new.BALANCE_USE_SHARES = True

with FakeBalance(SH, world=False, light=False):
    check("A8 gates closed -> None (unchanged)", new._ch_balance_world() is None and new._ch_balance_light() is None)
check("A9 constants updated", set(new.CONSTANT_BY_DESIGN) == {"self", "flavour"}
      and {"balance_world", "balance_light"} <= set(new.GRADED_CHANNELS)
      and not (set(new.GRADED_CHANNELS) & set(new.CONSTANT_BY_DESIGN)))

# =============================================================================================================
print("== [B] history versioning")
HIST_OTHER = {"curiosity": [1.0] * 500, "concern": [0.55] * 499 + [0.45], "self": [0.55] * 500, "flavour": [0.2] * 500}
def mkstate(**extra):
    st = {"history": {**copy.deepcopy(HIST_OTHER), "balance_world": [0.0] * 500, "balance_light": [0.0] * 500},
          "streak": {"curiosity": 2, "balance_world": 1}}
    st.update(extra)
    return st

def only_balance_tick(mod, tag, state_obj, closed=False):
    d = point(mod, tag)
    if state_obj is not None:
        open(mod._STATE, "w", encoding="utf-8").write(state_obj if isinstance(state_obj, str) else json.dumps(state_obj))
    saved = {k: mod._CHANNELS[k] for k in mod._CHANNELS}
    mod._CHANNELS = {k: v for k, v in saved.items() if k in ("balance_world", "balance_light", "self")}
    try:
        with FakeBalance(SH, world=not closed, light=not closed):
            random.seed(1); rec = mod.shadow_tick({})
    finally:
        mod._CHANNELS = saved
    st = json.loads(open(mod._STATE, encoding="utf-8").read())
    return rec, st, d

rec, st, d = only_balance_tick(new, "B1", mkstate())
check("B1 first tick: balance history dropped to the single new row, schema stamped",
      st["balance_schema"] == 2 and st["history"]["balance_world"] == [round(rec["candidates"][0]["raw"], 4)] and len(st["history"]["balance_light"]) == 1,
      (len(st["history"]["balance_world"]), st.get("balance_schema")))
check("B1b the new rows are cold-start 0.5 (not pinned 1.0 against zeros)",
      all(c["cold_start"] and c["p_norm"] == 0.5 for c in rec["candidates"] if c["channel"].startswith("balance")))
check("B1c other channels' history + streak untouched by the reset",
      all(st["history"][k] == HIST_OTHER[k] for k in ("curiosity", "concern", "flavour")) and st["streak"].get("curiosity") == 2)
check("B1d no .tmp left behind", not os.path.exists(str(new._STATE.with_suffix(".tmp"))))
rec2 = None
random.seed(1)
with FakeBalance(SH):
    rec2 = new.shadow_tick({})
st2 = json.loads(open(new._STATE, encoding="utf-8").read())
check("B2 second tick: reset does NOT repeat (history grows 1 -> 2)", len(st2["history"]["balance_world"]) == 2 and len(st2["history"]["balance_light"]) == 2,
      (len(st2["history"]["balance_world"]),))

_, stk, _ = only_balance_tick(new, "B3", mkstate(balance_schema=2))
check("B3 state already at schema 2: nothing dropped (history 500 -> 500)", len(stk["history"]["balance_world"]) == 500 and stk["balance_schema"] == 2)

new.BALANCE_USE_SHARES = False
try:
    _, stk, _ = only_balance_tick(new, "B4", mkstate())
finally:
    new.BALANCE_USE_SHARES = True
check("B4 kill switch off: no reset, no stamp", len(stk["history"]["balance_world"]) == 500 and "balance_schema" not in stk)

_, stf, _ = only_balance_tick(new, "B5", None)
check("B5 fresh (no state file): stamped 2", stf["balance_schema"] == 2)
_, stc, _ = only_balance_tick(new, "B6", "{ this is not json")
check("B6 corrupt state file fails open (fresh state, stamped 2)", stc["balance_schema"] == 2 and len(stc["history"]["balance_world"]) == 1)
_, stn, _ = only_balance_tick(new, "B7", {"history": {"curiosity": [1.0] * 5}, "streak": {}})
check("B7 pre-existing state with NO balance history: stamped, nothing else lost", stn["balance_schema"] == 2 and stn["history"]["curiosity"][:5] == [1.0] * 5)
rec_c, stg, _ = only_balance_tick(new, "B8", mkstate(), closed=True)
check("B8 gates closed on the migrating tick: the reset still lands once", stg["balance_schema"] == 2 and "balance_world" not in stg["history"])

# =============================================================================================================
print("== [C] full-fidelity replay over logged shadow rows")
def read_tail_rows(path, n):
    sz = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(max(0, sz - n * 6000))
        data = f.read()
    lines = data.split(b"\n")[1:]
    rows = []
    for ln in lines:
        try:
            rows.append(json.loads(ln.decode("utf-8")))
        except Exception:
            pass
    return rows[-n:]

if not (os.path.exists(args.shadow_log) and os.path.exists(args.state)):
    check("C0 replay inputs present", False, f"missing {args.shadow_log} or {args.state} (pass --shadow-log/--state)")
else:
    rows = read_tail_rows(args.shadow_log, args.ticks)
    live_state_text = open(args.state, "r", encoding="utf-8").read()             # read-only
    real_state = json.loads(live_state_text)
    check("C0 replay inputs: rows + the REAL persisted state with 500 zeros for both balance channels",
          len(rows) >= min(args.ticks, 1000) and all(real_state["history"].get(c) == [0.0] * 500 for c in ("balance_world", "balance_light")),
          (len(rows), {c: len(real_state["history"].get(c, [])) for c in ("balance_world", "balance_light")}))

    def replay(mod, tag):
        point(mod, tag)
        open(mod._STATE, "w", encoding="utf-8").write(live_state_text)
        saved_ch = dict(mod._CHANNELS)
        out = []
        try:
            for i, row in enumerate(rows):
                bycand = {c["channel"]: c for c in row["candidates"]}
                shares = None
                for ch in ("balance_world", "balance_light"):
                    if ch in bycand:
                        shares = (bycand[ch].get("lineage") or {}).get("shares")
                        break
                chans = {}
                for ch in saved_ch:
                    if ch in ("balance_world", "balance_light"):
                        chans[ch] = saved_ch[ch]                      # the REAL channel code
                    elif ch in bycand:
                        c = bycand[ch]
                        chans[ch] = (lambda _c: (lambda ctx: (_c["raw"], _c["binding_key"], _c["key_kind"], _c["justification"], {})))(c)
                    else:
                        chans[ch] = lambda ctx: None
                mod._CHANNELS = chans
                with FakeBalance(shares or SH, world="balance_world" in bycand, light="balance_light" in bycand):
                    random.seed(i)
                    rec = mod.shadow_tick({})
                out.append(rec)
        finally:
            mod._CHANNELS = saved_ch
        return out

    ro = replay(old, "C_old")
    rn = replay(new, "C_new")
    check("C1 every tick produced a record in both", all(ro) and all(rn) and len(ro) == len(rn) == len(rows))

    def wins(rs):
        from collections import Counter
        c = Counter(r["would_pick_argmax"] for r in rs if r); n = sum(c.values()) or 1
        return {k: round(v / n, 4) for k, v in c.most_common()}
    wo, wn = wins(ro), wins(rn)
    print("   OLD win-share:", wo); print("   NEW win-share:", wn)
    bo = wo.get("balance_world", 0) + wo.get("balance_light", 0)
    bn = wn.get("balance_world", 0) + wn.get("balance_light", 0)
    check("C2 balance win-share falls sharply (old %.3f -> new %.3f)" % (bo, bn), bo > 0.03 and bn < bo * 0.5, (bo, bn))

    def chrows(rs, ch, field):
        return [c[field] for r in rs for c in r["candidates"] if c["channel"] == ch]
    for ch in ("balance_world", "balance_light"):
        raws_o, raws_n = chrows(ro, ch, "raw"), chrows(rn, ch, "raw")
        pn = chrows(rn, ch, "p_norm")
        if not raws_n:
            check(f"C3 {ch} present in replay", False); continue
        mean_n = sum(raws_n) / len(raws_n)
        check(f"C3 {ch}: old raw all constant, new raw non-zero and varying",
              len(set(raws_o)) <= 2 and len(set(raws_n)) > 5 and max(raws_n) > 0.0 and mean_n > 0.0,
              (len(raws_n), sorted(set(raws_o))[:3], round(mean_n, 3), len(set(raws_n))))
        warm = [p for p, c in zip(pn, [c for r in rn for c in r["candidates"] if c["channel"] == ch]) if not c["cold_start"]]
        check(f"C4 {ch}: p_norm leaves 1.0 once warm (not pinned)", bool(warm) and min(warm) < 1.0 and sum(1 for p in warm if p == 1.0) < len(warm) * 0.5,
              (len(warm), min(warm) if warm else None, sum(1 for p in warm if p == 1.0)))
        cold_n = sum(1 for c in [c for r in rn for c in r["candidates"] if c["channel"] == ch] if c["cold_start"])
        check(f"C5 {ch}: re-warm is the 20-row cold start, not 500", cold_n == min(20, len(raws_n)), cold_n)
    others = ("contradiction", "concern", "curiosity", "boredom", "self", "wander", "flavour")
    same = True; bad = None
    for ch in others:
        for fld in ("raw", "p_norm"):
            a, b = chrows(ro, ch, fld), chrows(rn, ch, fld)
            if a != b:
                same = False; bad = (ch, fld, len(a), len(b))
    check("C6 no other channel's raw or p_norm changes (own history only)", same, bad)
    st_o = json.loads(open(old._STATE, encoding="utf-8").read()); st_n = json.loads(open(new._STATE, encoding="utf-8").read())
    check("C7 non-balance state history identical; balance history re-warmed from real values (OLD stays all-zero); schema stamped only in NEW",
          all(st_o["history"][k] == st_n["history"][k] for k in st_o["history"] if not k.startswith("balance"))
          and st_n["balance_schema"] == 2 and "balance_schema" not in st_o and len(set(st_n["history"]["balance_world"])) > 5 and set(st_o["history"]["balance_world"]) == {0.0})
    check("C8 the live state/log were only READ (temp paths in both modules)",
          all(os.path.abspath(str(p)).lower().startswith(TMP.lower()) for p in (old._STATE, old._LOG, new._STATE, new._LOG)))

# =============================================================================================================
print("== [D] balance gates closed: records + state identical, OLD vs NEW")
def scenario(mod, tag):
    d = point(mod, tag)
    saved = dict(mod._CHANNELS)
    recs = []
    try:
        rnd = random.Random(7)
        def mk(name, key, kind):
            return lambda ctx, n=name: (min(1.0, max(0.0, ctx["x"][n])), key, kind, f"{n} j", {"k": 1})
        for i in range(300):
            ctx = {"bored_streak": rnd.choice([0, 0, 1, 2, 4]), "dissonance": round(rnd.random(), 3),
                   "x": {"contradiction": rnd.random(), "curiosity": rnd.choice([1.0, 1.0, 0.9]), "concern": rnd.choice([0.55, 0.45])}}
            mod._CHANNELS = dict(saved)
            for n, key, kind in (("contradiction", "tension", "semantic"), ("curiosity", "curio", "semantic"), ("concern", "work", "semantic")):
                mod._CHANNELS[n] = mk(n, key, kind)
            with FakeBalance(SH, world=False, light=False):
                random.seed(i)
                r = mod.shadow_tick(ctx)
            r = dict(r); r.pop("ts")
            recs.append(r)
    finally:
        mod._CHANNELS = saved
    return recs, open(mod._STATE, encoding="utf-8").read(), open(mod._LOG, encoding="utf-8").read()

ro, so, lo = scenario(old, "D_old")
rn, sn, ln = scenario(new, "D_new")
check("D1 300 records identical (minus ts)", ro == rn)
def strip_ts(log):
    return [{k: v for k, v in json.loads(x).items() if k != "ts"} for x in log.splitlines()]
check("D2 the jsonl log is identical (minus ts)", strip_ts(lo) == strip_ts(ln))
jo, jn = json.loads(so), json.loads(sn)
jn_c = {k: v for k, v in jn.items() if k != "balance_schema"}
check("D3 state identical except the balance_schema stamp", jo == jn_c and jn.get("balance_schema") == 2)

shutil.rmtree(TMP, ignore_errors=True)
print("\nRESULT:", "ALL PASS" if not FAILS else f"{len(FAILS)} FAIL: {FAILS}")
sys.exit(1 if FAILS else 0)
