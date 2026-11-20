"""scripts/test_night_mind.py (J-2017, sleep_as_a_mode Phase 1): hermetic proof of the SHADOW night-mind.

No LLM call, no live data, no real sleep. Every store is temp-pathed (a synthetic shadow log); the generator and the
embedder are stubs; core is imported BEFORE anything else and its location is asserted to be this tree.

  [1] flag default OFF; the node only builds a NightMind behind the flag; AST: it never dispatches, writes a memory
      fragment, pushes a hint or grades (no store/hands/hint/judge name in the module's code)
  [2] the task: thoughts only after the first-after delay, floor apart, capped, seeded from the replay set then the dream
      tail (alternating once both exist), a dream from BEFORE the sleep is not a seed, no-seed slots counted not logged
  [3] rows: generated rows carry seed/thought/cosines, failed and timed-out generation is a row with generated False and
      an error, never an exception; kill by cancel leaves no running task
  [4] summary at stop(): thoughts/failed/seeds_available, per-thought cos_dream and median, stage times from the ledger,
      hold flags (dream-engine above 0.6, zero thoughts with seeds available)
  [5] the generator runs concurrently with the loop (a slow generate does not freeze sibling tasks)
  [6] evaluate(): insufficient under 7 sleeps; ok on a clean synthetic set; each of the four holds fires on its own
  [7] the live data/night_mind_shadow.jsonl was never touched

Run:  python scripts/test_night_mind.py   (from the tree under test)
"""
from __future__ import annotations
import ast, asyncio, hashlib, json, math, sys, tempfile, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE anything that could repoint paths
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import night_mind as nm

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

tmp = Path(tempfile.mkdtemp(prefix="j2017_"))
LIVE = ROOT / "data" / "night_mind_shadow.jsonl"
live_existed = LIVE.exists()
live_size = LIVE.stat().st_size if live_existed else 0

def fake_embed(text):
    """Deterministic bag-of-words hash embedding, normalised. Texts that share words are close."""
    v = [0.0] * 64
    for w in str(text).lower().split():
        v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]

def rows(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

class Gen:
    def __init__(self, delay=0.0, fail_at=(), text="a quiet thought about {seed}"):
        self.calls, self.delay, self.fail_at, self.text = [], delay, set(fail_at), text
    async def __call__(self, system, user):
        i = len(self.calls)
        self.calls.append((system, user))
        if self.delay:
            await asyncio.sleep(self.delay)
        if i in self.fail_at:
            raise RuntimeError("hub down")
        return self.text.format(seed=user.split(":", 1)[-1][:40])

def make(gen, log, **kw):
    kw.setdefault("first_after", 0.05); kw.setdefault("floor", 0.1); kw.setdefault("tick", 0.01)
    kw.setdefault("embed", fake_embed); kw.setdefault("stages_fn", lambda: {"replay": {"t": 1.0}, "downscale": {"t": 9.0}})
    return nm.NightMind(gen, log_path=log, **kw)

# ----------------------------------------------------------------------------------------------------------------
print("[1] flag and wiring")
check("NIGHT_MIND_ENABLED is True since J-2065 (founder-approved 2026-10-15; was False under J-2017)", nm.NIGHT_MIND_ENABLED is True)
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
tree = ast.parse(src)
fn = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "_enter_sleep")
seg = ast.get_source_segment(src, fn)
check("node builds NightMind only under NIGHT_MIND_ENABLED", "if _nmod.NIGHT_MIND_ENABLED:" in seg and "NightMind(" in seg)
check("node stops it before the waking percept and cancels in finally", seg.index("_nm.stop()") < seg.index("_night.wake()") and "_nm.cancel()" in seg)
check("node heartbeat drops Phase 0 slot rows only when the flag is on", "shadow=(False if _nmod.NIGHT_MIND_ENABLED else None)" in seg)
nm_src = Path(nm.__file__).read_text(encoding="utf-8")
code_only = "\n".join(l.split("#")[0] for l in nm_src.splitlines())
mod = ast.parse(nm_src)
names = {n.id for n in ast.walk(mod) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(mod) if isinstance(n, ast.Attribute)}
imports = {a.name for n in ast.walk(mod) if isinstance(n, ast.ImportFrom) for a in n.names} | {n.module for n in ast.walk(mod) if isinstance(n, ast.ImportFrom)}
pool = {str(x) for x in (names | imports) if x}
bad = [x for x in ("dispatch", "hands", "push_hint", "store_fragment", "add_fragment", "judge_panel", "lane2", "memory_fragments") if any(x in p for p in pool)]
store_imports = [p for p in pool if p.startswith("core.memory")]
check("module never imports/uses dispatch/hands/hint/judge/lane2/fragments", not bad)
check("the only memory-store use is the embedder (_embed), no writer", store_imports == ["core.memory.store"] and "_embed" in pool and not any(w in pool for w in ("store_fragment", "add_fragment", "write_fragment", "remember")))

# ----------------------------------------------------------------------------------------------------------------
print("[2] the task: cadence, cap, seeds")
async def run(gen, replayed, dreams, dur, log, sleep_ts=None, **kw):
    n = make(gen, log, replayed=replayed, dreams_fn=lambda: dreams, sleep_ts=sleep_ts, **kw)
    n.start(); await asyncio.sleep(dur); s = await n.stop(); return n, s

log = tmp / "a.jsonl"
g = Gen()
n, s = asyncio.run(run(g, ["the garden at dusk", "a letter unanswered", "cat on the sill"], [], 0.75, log, max_thoughts=3))
r = [x for x in rows(log) if x["kind"] == "night_thought"]
check("thoughts produced, capped at max_thoughts", 1 <= len(r) <= 3 and len(r) == s["thoughts"] and len(g.calls) <= 3)
check("slots are floor apart (>= 0.1 s) and not before first_after", all(b["ts"] - a["ts"] >= 0.09 for a, b in zip(r, r[1:])) and r[0]["elapsed_s"] >= 0.04)
check("replay set seeds first, in order", r[0]["seed_source"] == "replay" and r[0]["seed_snippet"] == "the garden at dusk")
check("rows: generated True, phase 1, dormant not_built, thought text present", all(x["generated"] and x["phase"] == 1 and x["seeds_dormant"] == "not_built" and x["thought"] for x in r))
check("prompt is the night's own material only (no world/conversation words)", all("Travis" not in u and "hint" not in u.lower() for _, u in g.calls))

t0 = time.time(); log2 = tmp / "b.jsonl"; g2 = Gen()
n, s = asyncio.run(run(g2, ["r1", "r2"], [{"ts": t0 + 1, "narrative": "the corridor folded into water and the clock ran backward"}], 0.9, log2, sleep_ts=t0, max_thoughts=4))
r = [x for x in rows(log2) if x["kind"] == "night_thought"]
check("once a dream exists the tail alternates in as a seed", {"replay", "dream_tail"} <= {x["seed_source"] for x in r} and any("clock" in x["seed_snippet"] for x in r if x["seed_source"] == "dream_tail"))

log3 = tmp / "c.jsonl"; g3 = Gen(); t1 = time.time()
n, s = asyncio.run(run(g3, [], [{"ts": t1 - 500, "narrative": "last night's dream"}], 0.4, log3, sleep_ts=t1))
check("no seed (and a dream from before this sleep is not one): nothing generated, slots counted", g3.calls == [] and s["slots_no_seed"] >= 1 and not s["seeds_available"] and not [x for x in rows(log3) if x["kind"] == "night_thought"])
check("no seeds -> hold_zero_thoughts False (not 'seeds available')", s["hold_zero_thoughts"] is False)

# ----------------------------------------------------------------------------------------------------------------
print("[3] failures are rows, never exceptions")
log4 = tmp / "d.jsonl"; g4 = Gen(fail_at=(0,))
n, s = asyncio.run(run(g4, ["x one", "y two", "z three"], [], 0.8, log4, max_thoughts=3))
rr = [x for x in rows(log4) if x["kind"] == "night_thought"]
check("a failing generate is a generated=False row with an error, counted in failed", rr[0]["generated"] is False and "hub down" in rr[0]["error"] and s["failed"] == 1)
check("the next slot still generates", any(x["generated"] for x in rr[1:]))
nm.GEN_TIMEOUT_S, _old = 0.05, nm.GEN_TIMEOUT_S
log5 = tmp / "e.jsonl"; g5 = Gen(delay=1.0)
n, s = asyncio.run(run(g5, ["slow"], [], 0.6, log5, max_thoughts=2))
nm.GEN_TIMEOUT_S = _old
rr = [x for x in rows(log5) if x["kind"] == "night_thought"]
check("a hub timeout is a failed row, not a stuck sleep", rr and rr[0]["generated"] is False and s["failed"] >= 1)
async def cancel_case():
    nn = make(Gen(delay=5.0), tmp / "f.jsonl", replayed=["q"]); nn.start(); await asyncio.sleep(0.3)
    nn.cancel(); await asyncio.sleep(0.05)
    return nn._task.done()
check("cancel() leaves no running task even mid-generation", asyncio.run(cancel_case()))

# ----------------------------------------------------------------------------------------------------------------
print("[4] summary row")
log6 = tmp / "g.jsonl"; t2 = time.time()
dream = "the corridor folded into water and the clock ran backward"
g6 = Gen(text="the corridor folded into water and the clock ran backward again")
n, s = asyncio.run(run(g6, ["alpha beta"], [{"ts": t2 + 1, "narrative": dream}], 0.7, log6, sleep_ts=t2, max_thoughts=3))
sm = [x for x in rows(log6) if x["kind"] == "sleep_summary"]
check("exactly one summary row, phase 1", len(sm) == 1 and sm[0]["phase"] == 1)
check("summary: per-thought cos_dream and median, stage times", len(sm[0]["cos_dream"]) == sm[0]["thoughts"] and sm[0]["cos_dream_median"] is not None and sm[0]["stage_t"] == {"replay": 1.0, "downscale": 9.0})
check("a thought that parrots the dream trips hold_dream_engine (median cos > 0.6)", sm[0]["cos_dream_median"] > 0.6 and sm[0]["hold_dream_engine"] is True)
log7 = tmp / "h.jsonl"; g7 = Gen(text="completely unrelated words here")
n, s = asyncio.run(run(g7, ["alpha beta"], [{"ts": t2 + 1, "narrative": dream}], 0.5, log7, sleep_ts=t2, max_thoughts=2))
check("an unrelated thought does not trip it", s["hold_dream_engine"] is False and (s["cos_dream_median"] or 0) < 0.6)
log8 = tmp / "i.jsonl"
g8 = Gen(fail_at=(0, 1, 2, 3))
n, s = asyncio.run(run(g8, ["a b"], [], 0.8, log8, max_thoughts=4))
check("seeds available but zero thoughts generated -> hold_zero_thoughts", s["seeds_available"] and s["thoughts"] == 0 and s["hold_zero_thoughts"] is True)
check("stop() twice is safe and returns the same summary", asyncio.run(n.stop()) == s)

# ----------------------------------------------------------------------------------------------------------------
print("[5] generation is concurrent with the loop")
async def conc():
    n = make(Gen(delay=0.5), tmp / "j.jsonl", replayed=["w"], max_thoughts=1)
    n.start(); ticks = 0; end = time.time() + 0.6
    while time.time() < end:
        await asyncio.sleep(0.02); ticks += 1
    await n.stop(); return ticks
check("a slow hot-hub call does not freeze sibling tasks (>= 10 ticks in 0.6 s; Windows timer granularity ~15 ms)", asyncio.run(conc()) >= 10)

# ----------------------------------------------------------------------------------------------------------------
print("[6] evaluate()")
def ledger(i, dur, kind="night", stages=8):
    return {"ts": 1000 + i * 10000, "kind": kind, "duration_s": dur, "stages": {f"s{k}": {"t": k} for k in range(stages)}}
def summ(i, **kw):
    d = {"kind": "sleep_summary", "phase": 1, "sleep_ts": 1000 + i * 10000 + 5, "sleep_kind": "night", "thoughts": 3,
         "seeds_available": True, "cos_dream_median": 0.3, "hold_zero_thoughts": False}
    d.update(kw); return d
base = [ledger(i, 1500) for i in range(-10, 0)]
good = [ledger(i, 1550) for i in range(0, 7)]
sh = [summ(i) for i in range(0, 7)]
check("under 7 sleeps: insufficient", nm.evaluate(sh[:5], base + good)["verdict"] == "insufficient")
e = nm.evaluate(sh, base + good)
check("clean set: ok, no holds, duration +3.3 pct", e["verdict"] == "ok" and not e["holds"] and abs(e["duration_up_pct"] - 3.3) < 0.2)
e = nm.evaluate(sh, base + [ledger(i, 1800) for i in range(0, 7)])
check("duration +20 pct: hold", "sleep_duration_up_over_15pct" in e["holds"])
e = nm.evaluate(sh, base + [ledger(i, 1500, stages=5) for i in range(0, 7)])
check("fewer ledger stages than baseline: passes-failing-open hold", "passes_failing_open_more_than_before" in e["holds"])
e = nm.evaluate([summ(i, thoughts=0, hold_zero_thoughts=True) if i == 2 else summ(i) for i in range(7)], base + good)
check("one sleep with seeds and zero thoughts: hold", "zero_thoughts_with_seeds_available" in e["holds"])
e = nm.evaluate([summ(i, cos_dream_median=0.72) for i in range(7)], base + good)
check("median cosine to dream 0.72: hold", "median_cosine_to_dream_over_0.6" in e["holds"] and e["verdict"] == "hold")

# ----------------------------------------------------------------------------------------------------------------
print("[8] J-2594 / D-0521 A: variety prompt + do-not-repeat list (V2, kept exactly behind NIGHT_PROMPT_VERSION = 2)")
nm.NIGHT_PROMPT_VERSION = 2   # J-3192: V3 is the default now; this section is the V2 regression
MONO = ("quiet", "silence", "dust", "weight", "settles", "heavy", "ink")   # the F-3283 monoculture words
check("V1 prompt preserved verbatim (starts the same, still says one quiet, private thought)", "Let one quiet, private thought form around it" in nm.SYSTEM_PROMPT_V1)
check("V2 prompt names none of the monoculture words and keeps the JSON output shape",
      not any(w in nm.SYSTEM_PROMPT_V2.lower() for w in MONO) and nm.SYSTEM_PROMPT_V2.endswith('Reply as JSON: {"thought": "<the thought>"}'))
check("temperature and token cap unchanged (0.8 / 160)", nm.GEN_TEMPERATURE == 0.8 and nm.GEN_MAX_TOKENS == 160)
check("flag on by default; _system_prompt follows it", nm.NIGHT_VARIETY_ENABLED is True and nm._system_prompt() == nm.SYSTEM_PROMPT_V2)
prior = ["the ink still smells of old parchment, and the silence is so heavy it feels like dust",
         "the weight of the question, ripples moving through the quiet mind, but the silence takes it back",
         "the quiet hum of a mind, dust settles on the sill", "a moth's wing beat in the quiet",
         "The match burns without smoke, just this sudden cold brightness."]
av = nm._avoid_images(prior, seed="")
check("avoid list: recurring image words, most frequent first (quiet, then silence/dust)", av[:1] == ["quiet"] and {"silence", "dust"} <= set(av) and "match" not in av)
check("avoid list never contains a stopword or a word of the current seed", "quiet" not in nm._avoid_images(prior, seed="the quiet garden") and "mind" not in av and "still" not in av)
check("avoid list capped at AVOID_MAX_WORDS and empty on no history / garbage", len(nm._avoid_images(prior * 5)) <= nm.AVOID_MAX_WORDS and nm._avoid_images([]) == [] and nm._avoid_images(None) == [])
logv = tmp / "v.jsonl"; logj = tmp / "vj.jsonl"
logv.write_text("".join(json.dumps({"kind": "night_thought", "generated": True, "phase": 1, "thought": t}) + "\n" for t in prior)
                + json.dumps({"kind": "night_thought", "generated": False, "error": "x"}) + "\n", encoding="utf-8")
logj.write_text(logv.read_text(encoding="utf-8") + "not json\n", encoding="utf-8")
check("prior thoughts read from the log tail, failed rows and junk skipped", nm._recent_logged_thoughts(logj) == prior and nm._recent_logged_thoughts(tmp / "missing.jsonl") == [])
gv = Gen(text="a lantern swinging over the {seed}")
n, s = asyncio.run(run(gv, ["the garden at dusk", "a letter unanswered"], [], 0.5, logv, max_thoughts=2))
rv = [x for x in rows(logv) if x.get("kind") == "night_thought" and x.get("prompt_v")]
check("rows carry prompt_v 2 and the avoid list; system prompt sent is V2", rv and all(x["prompt_v"] == 2 for x in rv) and rv[0]["avoid_images"][:1] == ["quiet"] and all(sp == nm.SYSTEM_PROMPT_V2 for sp, _ in gv.calls))
check("user prompt carries the do-not-repeat line after the seed, seed line unchanged",
      gv.calls[0][1].startswith("(something the day left with you): the garden at dusk\n\nRecent night thoughts kept coming back to: quiet") and gv.calls[0][1].endswith("What drifts up?"))
nm.NIGHT_VARIETY_ENABLED = False
logw = tmp / "w.jsonl"; logw.write_text(logv.read_text(encoding="utf-8"), encoding="utf-8")
gw = Gen()
n, s = asyncio.run(run(gw, ["the garden at dusk"], [], 0.4, logw, max_thoughts=1))
nm.NIGHT_VARIETY_ENABLED = True
rw = [x for x in rows(logw) if x.get("kind") == "night_thought" and x.get("prompt_v") == 1]
check("flag off: V1 prompt exactly, no avoid line (the J-2017 behaviour)", gw.calls and gw.calls[0][0] == nm.SYSTEM_PROMPT_V1 and gw.calls[0][1] == "(something the day left with you): the garden at dusk\n\nWhat drifts up?" and rw and rw[0]["avoid_images"] == [])

nm.NIGHT_PROMPT_VERSION = 3

# ----------------------------------------------------------------------------------------------------------------
print("[9] J-3192 / D-0579: V3 = no example list in the prompt, nouns-only do-not-repeat list")
EXAMPLES = ("an object", "a place", "a colour", "a sound", "a smell", "a touch", "a creature", "something that happened")
check("V3 is the default: version 3, _system_prompt is V3, SYSTEM_PROMPT alias is V3",
      nm.NIGHT_PROMPT_VERSION == 3 and nm._prompt_version() == 3 and nm._system_prompt() == nm.SYSTEM_PROMPT_V3 and nm.SYSTEM_PROMPT == nm.SYSTEM_PROMPT_V3)
check("V3 drops the example list, keeps the JSON shape, adds no new instruction sentence",
      not any(e in nm.SYSTEM_PROMPT_V3 for e in EXAMPLES) and nm.SYSTEM_PROMPT_V3.endswith('Reply as JSON: {"thought": "<the thought>"}')
      and all(e in nm.SYSTEM_PROMPT_V2 for e in EXAMPLES))
v2s = [x.strip() for x in nm.SYSTEM_PROMPT_V2.split(".") if x.strip()]
v3s = [x.strip() for x in nm.SYSTEM_PROMPT_V3.split(".") if x.strip()]
check("V3 is V2 with exactly the example clause removed (every V3 sentence is a V2 sentence or its prefix)",
      len(v2s) == len(v3s) and all(b == a or a.startswith(b) for a, b in zip(v2s, v3s)) and v3s[4] == "Let one private thought form around the particular thing in it")
check("V3 names none of the monoculture words", not any(w in nm.SYSTEM_PROMPT_V3.lower() for w in MONO))
# the lists F-3647 found on live calls
f3647 = [["single", "sharp", "black", "caught", "click", "cold", "dark", "empty"],
         ["single", "heavy", "sudden", "brass", "catching", "cold", "dust", "empty"]]
kept = [w for lst in f3647 for w in lst if not nm._not_noun(w)]
check("the F-3647 style words are not nouns for the filter (single sharp black caught cold dark empty heavy sudden catching)",
      all(nm._not_noun(w) for w in ("single", "sharp", "black", "caught", "cold", "dark", "empty", "heavy", "sudden", "catching",
                                     "faint", "quiet", "dancing", "turning", "waiting", "leaving", "forgotten", "faintly", "exists", "hangs")))
check("the nouns on those lists survive (click brass dust)", kept == ["click", "brass", "dust", "click", "brass", "dust"][:0] + [w for lst in f3647 for w in lst if w in ("click", "brass", "dust")])
check("suffix exceptions keep real nouns (ceiling morning seed universe memory) and the filter drops -ly/-ous/-ful/-ed/-ing/un- shapes",
      not any(nm._not_noun(w) for w in ("ceiling", "morning", "seed", "universe", "memory", "dust", "silence", "weight", "glass", "light", "room", "form"))
      and all(nm._not_noun(w) for w in ("slowly", "mysterious", "careful", "weightless", "pensive", "reddish", "glowing", "unlit", "unopened", "rusted")))
mixed = ["a single, heavy brass key sits on the table, cold and sharp",
         "a sudden cold draft, a single brass key, heavy on the table",
         "the single heavy key catches the sudden light of the dark room",
         "a dark room, a cold table, brass and dust, the key waiting"]
av3 = nm._avoid_images(mixed, seed="")
av2 = nm._avoid_images(mixed, seed="", nouns_only=False)
check("V2 list on this history carries adjectives; V3 list is nouns only", {"single", "heavy", "cold", "sudden"} <= set(av2) and av3 and set(av3) <= {"brass", "table", "draft", "key", "light", "room", "dust"} and "single" not in av3)
check("V3 list still ranks by recurrence, honours the seed exclusion, cap and empty input",
      av3[0] in ("brass", "table", "key", "room") and "brass" not in nm._avoid_images(mixed, seed="the brass door") and len(nm._avoid_images(mixed * 9)) <= nm.AVOID_MAX_WORDS
      and nm._avoid_images([]) == [] and nm._avoid_images(None) == [])
logx = tmp / "x.jsonl"
logx.write_text("".join(json.dumps({"kind": "night_thought", "generated": True, "phase": 1, "thought": t}) + "\n" for t in mixed), encoding="utf-8")
gx = Gen(text="a lantern swinging over the {seed}")
n, s = asyncio.run(run(gx, ["the garden at dusk", "a letter unanswered"], [], 0.5, logx, max_thoughts=2))
rx = [x for x in rows(logx) if x.get("kind") == "night_thought" and x.get("prompt_v")]
check("rows carry prompt_v 3 and a nouns-only avoid list; the system prompt sent is V3",
      rx and all(x["prompt_v"] == 3 for x in rx) and all(sp == nm.SYSTEM_PROMPT_V3 for sp, _ in gx.calls)
      and all("single" not in x["avoid_images"] and "heavy" not in x["avoid_images"] for x in rx) and rx[0]["avoid_images"])
check("user prompt wording is unchanged from V2 (the J-2594 line, no new sentence)",
      gx.calls[0][1].endswith("Leave those images alone this time and find a different one.\n\nWhat drifts up?") and "Recent night thoughts kept coming back to: " in gx.calls[0][1])
nm.NIGHT_PROMPT_VERSION = 2
logy = tmp / "y.jsonl"; logy.write_text("".join(json.dumps({"kind": "night_thought", "generated": True, "phase": 1, "thought": t}) + "\n" for t in mixed[1:]), encoding="utf-8")
gy = Gen()
n, s = asyncio.run(run(gy, ["the garden at dusk"], [], 0.4, logy, max_thoughts=1))
nm.NIGHT_PROMPT_VERSION = 3
ry = [x for x in rows(logy) if x.get("kind") == "night_thought" and x.get("prompt_v")]
check("NIGHT_PROMPT_VERSION = 2 restores V2 exactly: prompt_v 2, V2 prompt, adjectives back on the list",
      gy.calls and gy.calls[0][0] == nm.SYSTEM_PROMPT_V2 and ry and ry[-1]["prompt_v"] == 2 and "single" in ry[-1]["avoid_images"])
check("the flag off still means V1 whatever the version", (setattr(nm, "NIGHT_VARIETY_ENABLED", False), nm._prompt_version() == 1 and nm._system_prompt() == nm.SYSTEM_PROMPT_V1)[1])
nm.NIGHT_VARIETY_ENABLED = True

# ----------------------------------------------------------------------------------------------------------------
print("[7] live log untouched")
check("data/night_mind_shadow.jsonl unchanged", (LIVE.exists() == live_existed) and ((LIVE.stat().st_size if live_existed else 0) == live_size))
print("PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
