"""J-3336 (stale-patch cue, second trigger; J-3144 review Option B): the REPEAT RECORD clause + its deterministic verifier.

PROVES (this tree only; a lab-dir EMPTY memory DB seeded by this test, a stub embedder, temp log paths; no live store read
or written, no model call, no network):
  [1] trigger     streak < 2 logs nothing; streak >= 2 logs one row (trigger='repeat_record', a string) even when nothing renders
  [2] selection   quoted rows = the (at most 2) nearest EARLIER inner_thought rows at stub-cosine >= REPEAT_SIM, by brute force; this
                  cycle's own row, a verbatim-refreshed row (timestamp >= store_t0), a system_note row, a far row and a
                  loop-word row are never quoted; the loop-word row is logged under `skipped`
  [3] form        'At 06:12 you wrote: "..."' / 'Yesterday at ..' / 'On 2 Nov at ..', oldest first, quote <= 120 chars (+ '...' when cut)
  [4] verifier    recompute_clauses() re-fetches by id and re-embeds: verify_row() is clean on every row; flags a tampered clause, a
                  deleted row, a changed stored timestamp, a stored text that no longer clears 0.82, a would_render flip, a
                  rendered clause with no qualifying earlier row, a cosine that does not recompute
  [5] language    frames carry no feeling word, imperative, count word or loop word; no clause carries a loop word; independent lists
  [6] none        no earlier row >= 0.82 -> would_render False, line None (the row is still logged)
  [7] read-only   the module writes nothing to the memory DB (row counts equal; a write through its connection is refused)
  [8] pool        the cache loads once and picks up a newly stored row on the next trigger as an EARLIER row
  [9] fence       a non-live process pointed at the live data path is refused before any I/O and writes nothing
  [10] status     status()['repeat_record'] counts rows / would-render / share-of-idle / language / non-recomputable and sets `stop`
  [11] shadow     the node calls the module twice (observe + observe_repeat_record), adds nothing to a prompt/seed/gap, still has
                  the untouched habituation block; the module keeps no write SQL; REPEAT_SIM == the node's RUMINATION_SIM

  python scripts/_test_j3336_repeat_record.py        # exit 0 = ALL OK
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import tempfile
import time
import zlib
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402  (core BEFORE lab_env)
sys.path.insert(1, str(Path.home() / ".claude" / "skills" / "job-queue"))
import lab_env  # noqa: E402

assert ROOT in Path(core.__file__).resolve().parents, core.__file__

import numpy as np  # noqa: E402
from core import profile, stale_patch_cue as spc  # noqa: E402
from core.memory import store  # noqa: E402

# independent word lists (not the module's)
FEELING = {"tired", "sick", "restless", "bored", "boredom", "stale", "stuck", "dead", "weary", "need", "needs", "want", "wants", "urge",
           "pull", "dull", "tedious", "stagnant", "exhausted", "frustrated", "trapped", "enough", "sad", "anxious", "uneasy", "longing"}
IMPERATIVE = {"go", "turn", "leave", "try", "open", "set", "step", "move", "make", "consider", "notice", "look", "stop", "get", "write",
              "read", "come", "take", "let", "break", "change", "choose", "pick", "begin", "start", "do", "think", "remember", "imagine",
              "ask", "find", "walk", "put", "return", "must", "should", "please", "never", "always"}
LOOPY = {"circled", "circling", "circle", "circles", "stale", "flat", "stuck", "gone"}
COUNTY = {"times", "twice", "thrice", "again", "repeated", "repeating", "same", "once"}

fails: list = []


def ok(cond, msg):
    if not cond:
        fails.append(msg)
        print("FAIL:", msg)


DIM = 256
SIM = 0.82          # written out here on purpose: the test must not read the module's own threshold


def stub_embed(text):
    """Deterministic bag-of-words embedder: shared tokens -> high cosine. Normalised float32, None for blank."""
    toks = re.findall(r"[a-z']+", (text or "").lower())
    if not toks:
        return None
    v = np.zeros(DIM, dtype=np.float32)
    for tk in toks:
        r = np.random.default_rng(zlib.crc32(tk.encode()))
        v += r.normal(0, 1, DIM).astype(np.float32)
    return (v / np.linalg.norm(v)).astype(np.float32)


def cos_of(a, b):
    return float(stub_embed(a) @ stub_embed(b))


WORDS = ("the harbour light moved slowly across the water while a gull held still above the old stone steps and I kept "
         "turning over what the keeper had said about the tide tables").split()


def variant(base_words, changes):
    w = list(base_words)
    for i in range(changes):
        w[3 + i * 4] = ("zz%d" % i) + w[3 + i * 4][::-1]
    return " ".join(w)


THOUGHT = " ".join(WORDS)                       # 30 words, ~160 chars
tmp = Path(tempfile.mkdtemp(prefix="j3336_"))
# a fixed local "now": 2026-11-07 10:00
NOW = time.mktime((2026, 11, 7, 10, 0, 0, 0, 0, -1))
T0 = NOW - 2.0


def at(y, mo, d, h, mi):
    return time.mktime((y, mo, d, h, mi, 0, 0, 0, -1))


def insert(conn, fid, content, ts, origin="inner_thought"):
    conn.execute("INSERT INTO memory_fragments (fragment_id, content, layer, timestamp, embedding, origin) VALUES (?,?,?,?,?,?)",
                 (fid, content, "episodic", ts, stub_embed(content).tobytes(), origin))
    conn.commit()


def reset_pool():
    spc._pool.update(key=None, ids=[], ts=None, mat=None)


with lab_env.isolate(db="empty") as lab_dir:
    real_embed = store._embed
    store._embed = stub_embed
    spc._LOG = tmp / "stale_patch_cue_shadow.jsonl"
    spc._RAILC_LOG = tmp / "grounding_injection_shadow.jsonl"
    try:
        db = Path(store.DB_PATH)
        ok(lab_dir in db.parents, f"the DB under test is in the lab dir, not live: {db}")
        wconn = sqlite3.connect(str(db))
        # ---- seed ------------------------------------------------------------------------------------
        A = variant(WORDS, 1)        # near, today 06:12
        B = variant(WORDS, 2)        # near, yesterday 21:40
        C = variant(WORDS, 3)        # near, 2 Nov 08:05 (eligible, but not among the two nearest, if farther)
        L = variant(WORDS, 1).replace("harbour", "stale")      # near but carries a loop word
        FAR = "the quarterly figures for the inland depot were entered into the ledger before noon"
        seeds = [("fa", A, at(2026, 11, 7, 6, 12)), ("fb", B, at(2026, 11, 6, 21, 40)), ("fc", C, at(2026, 11, 2, 8, 5)),
                 ("fl", L, at(2026, 11, 7, 7, 30)), ("ffar", FAR, at(2026, 11, 7, 8, 0))]
        for fid, txt, ts in seeds:
            insert(wconn, fid, txt, ts)
        MID = variant(WORDS, 6)                                       # below the bar (about 0.8), above a looser one
        insert(wconn, "fmid", MID, at(2026, 11, 5, 12, 0))
        ok(0.70 < cos_of(THOUGHT, MID) < SIM, f"seed sanity: the mid row sits between 0.70 and {SIM} ({cos_of(THOUGHT, MID):.3f})")
        insert(wconn, "fsys", variant(WORDS, 1) + " ", at(2026, 11, 7, 9, 0), origin="system_note")
        insert(wconn, "ffresh", THOUGHT, T0 + 0.5)                       # this cycle's own row (and a verbatim-refreshed one)
        for fid, txt, ts in seeds[:3]:
            ok(cos_of(THOUGHT, txt) >= SIM, f"seed sanity: {fid} clears {SIM} under the stub ({cos_of(THOUGHT, txt):.3f})")
        ok(cos_of(THOUGHT, FAR) < SIM, "seed sanity: the far row is far")
        ok(cos_of(THOUGHT, L) >= SIM, "seed sanity: the loop-word row is near")

        vec = stub_embed(THOUGHT)
        live = {"redirected": True, "escape": False, "felt": False}

        # ---- [1] trigger -----------------------------------------------------------------------------
        reset_pool()
        ok(spc.observe_repeat_record(THOUGHT, vec, streak=0, store_t0=T0, now=NOW) is None, "[1] streak 0 -> no row")
        ok(spc.observe_repeat_record(THOUGHT, vec, streak=1, store_t0=T0, now=NOW) is None, "[1] streak 1 -> no row")
        ok(not spc._LOG.exists(), "[1] nothing logged below the threshold")
        row = spc.observe_repeat_record(THOUGHT, vec, streak=2, streak_start=2, store_t0=T0, live=live, about="the keeper", now=NOW)
        ok(row is not None and row["trigger"] == "repeat_record" and isinstance(row["trigger"], str), "[1] streak 2 -> one row, trigger a string")
        ok(row["streak_end"] == 2 and row["streak_start"] == 2 and row["live"]["redirect"] and not row["live"]["escape"],
           f"[1] streak and live flags logged: {row['streak_end']} {row['streak_start']} {row['live']}")
        logged = [json.loads(x) for x in spc._LOG.read_text(encoding="utf-8").splitlines()]
        ok(len(logged) == 1 and logged[0]["thought"] == THOUGHT, "[1] the full kept thought is in the row (the verifier needs it)")

        # ---- [2] selection (brute force) ---------------------------------------------------------------
        elig = []
        for fid, txt, ts in seeds:
            c = cos_of(THOUGHT, txt)
            if ts < T0 and c >= SIM and "stale" not in txt:
                elig.append((c, fid, ts))
        elig.sort(reverse=True)
        want_ids = [f for _, f, _ in elig[:2]]
        got_ids = [q["id"] for q in row["quotes"]]
        ok(sorted(got_ids) == sorted(want_ids), f"[2] quoted = the two nearest eligible earlier rows: want {want_ids} got {got_ids}")
        ok(len(row["quotes"]) <= 2, "[2] at most 2 quotes")
        ok("fmid" not in [c["id"] for c in row["top_candidates"]], "[2] a row under the 0.82 bar is not even a candidate")
        for bad_id in ("ffresh", "fsys", "ffar", "fl", "fmid"):
            ok(bad_id not in got_ids, f"[2] {bad_id} is never quoted")
        ok(any(s_["id"] == "fl" and s_["why"].startswith("loop_word") for s_ in row["skipped"]), f"[2] loop-word row logged as skipped: {row['skipped']}")
        ok(row["n_candidates"] >= len(elig) and all(c["ts"] < T0 for c in row["top_candidates"]), "[2] candidates are all earlier than store_t0")
        for q in row["quotes"]:
            ok(abs(q["cos"] - cos_of(THOUGHT, [t for f, t, _ in seeds if f == q["id"]][0])) < 1e-3, f"[2] logged cosine = recomputed ({q['cos']})")
            ok(isinstance(q["feeling_words"], list), "[2] per-quote feeling_words listed for the hand-read")

        # ---- [3] form --------------------------------------------------------------------------------
        texts = [c["text"] for c in row["clauses"]]
        ok([c["ts"] for c in row["clauses"]] == sorted(c["ts"] for c in row["clauses"]), "[3] oldest first")
        by_id = {c["id"]: c["text"] for c in row["clauses"]}
        if "fa" in by_id:
            ok(by_id["fa"].startswith('At 06:12 you wrote: "'), f"[3] today form: {by_id['fa'][:40]}")
            ok(by_id["fa"].endswith('..."') and len(by_id["fa"]) <= len('At 06:12 you wrote: "') + 120 + 4, "[3] long quote cut at 120 chars + '...'")
            ok(by_id["fa"][len('At 06:12 you wrote: "'):-4] == " ".join(A.split())[:120], "[3] the quote is the verbatim prefix")
        if "fb" in by_id:
            ok(by_id["fb"].startswith('Yesterday at 21:40 you wrote: "'), f"[3] yesterday form: {by_id['fb'][:40]}")
        ok(spc.when_text(at(2026, 11, 2, 8, 5), NOW) == "On 2 Nov at 08:05", "[3] older-day form")
        ok(row["line"] == " ".join(texts), "[3] line = join of clauses")
        short = "the harbour light moved slowly across the water while a gull held still"
        ok(spc.quote_text(short) == short and not spc.quote_text(short).endswith("..."), "[3] a short quote is not cut and gets no '...'")

        # ---- [4] verifier ----------------------------------------------------------------------------
        ok(spc.verify_row(row) == [], f"[4] clean row verifies: {spc.verify_row(row)}")
        cd = spc.recompute_clauses(row)
        ok([(c["id"], c["text"]) for c in cd] == [(c["id"], c["text"]) for c in row["clauses"]], "[4] recompute_clauses re-derives the logged clauses")

        def tamper(fn):
            r = json.loads(json.dumps(row))
            fn(r)
            return spc.verify_row(r)

        ok("clauses_not_recomputable" in tamper(lambda r: r["clauses"][0].update(text=r["clauses"][0]["text"].replace("you wrote", "you said"))),
           "[4] tampered clause text flagged")
        ok("clauses_not_recomputable" in tamper(lambda r: r["clauses"][0].update(text=r["clauses"][0]["text"].replace(" at ", " at 1"))),
           "[4] a wrong hour flagged")
        ok(tamper(lambda r: r.update(would_render=False)) != [], "[4] would_render flip flagged")
        ok("quote_cos_not_recomputable" in tamper(lambda r: r["quotes"][0].update(cos=0.99)), "[4] a cosine that does not recompute flagged")
        ok(tamper(lambda r: r.update(thought="the quarterly figures for the inland depot were entered into the ledger")) != [],
           "[4] a quote not >= 0.82 of the logged thought flagged (non-recomputable)")
        ok("trigger_below_threshold" in tamper(lambda r: r.update(streak_end=1)), "[4] streak below 2 flagged")
        victim = row["quotes"][0]["id"]
        wconn.execute("UPDATE memory_fragments SET timestamp = timestamp + 5 WHERE fragment_id=?", (victim,))
        wconn.commit()
        ok("clauses_not_recomputable" in spc.verify_row(row), "[4] a changed stored timestamp flagged")
        wconn.execute("UPDATE memory_fragments SET timestamp = timestamp - 5 WHERE fragment_id=?", (victim,))
        wconn.execute("UPDATE memory_fragments SET content=? WHERE fragment_id=?", (FAR, victim))
        wconn.commit()
        ok("clauses_not_recomputable" in spc.verify_row(row), "[4] a stored text that no longer clears 0.82 flagged")
        wconn.execute("UPDATE memory_fragments SET content=? WHERE fragment_id=?", ([t for f, t, _ in seeds if f == victim][0], victim))
        wconn.execute("DELETE FROM memory_fragments WHERE fragment_id=?", (victim,))
        wconn.commit()
        ok("clauses_not_recomputable" in spc.verify_row(row), "[4] a deleted stored row flagged")
        insert(wconn, victim, [t for f, t, _ in seeds if f == victim][0], [ts for f, _, ts in seeds if f == victim][0])
        ok(spc.verify_row(row) == [], "[4] restored row verifies again")
        # a rendered clause with no qualifying earlier row
        fake = json.loads(json.dumps(row))
        fake["quotes"], fake["clauses"] = [], [{"clock": "repeat_record", "id": "ffar", "ts": at(2026, 11, 7, 8, 0), "text": 'At 08:00 you wrote: "' + FAR + '"'}]
        fake["line"], fake["would_render"] = fake["clauses"][0]["text"], True
        ok(spc.verify_row(fake) != [], "[4] a render with no qualifying earlier row fails the check")

        # ---- [5] language ----------------------------------------------------------------------------
        reset_pool()
        many = []
        for k in range(40):
            th = variant(WORDS, 0).replace("harbour", "wh%d" % k)
            insert(wconn, "ma%d" % k, variant([w if w != "harbour" else "wh%d" % k for w in WORDS], 1), NOW - 7200 - 600 * k)
            r_ = spc.observe_repeat_record(th, stub_embed(th), streak=2, store_t0=T0, now=NOW, live=live)
            if r_:
                many.append(r_)
        n_render = 0
        for r_ in many:
            ok(spc.verify_row(r_) == [], f"[5] row verifies: {spc.verify_row(r_)}")
            for c in r_["clauses"]:
                n_render += 1
                frame = c["text"].split(" you wrote:")[0]
                ws = set(re.findall(r"[a-z']+", frame.lower()))
                ok(not (ws & FEELING) and not (ws & IMPERATIVE - {"at", "on"}) and not (ws & COUNTY), f"[5] frame clean: {frame}")
                ok(not (set(re.findall(r"[a-z']+", c["text"].lower())) & LOOPY), f"[5] no loop word in clause: {c['text'][:60]}")
                ok(re.fullmatch(r"(At|Yesterday at|On \d{1,2} [A-Z][a-z]{2} at) \d\d:\d\d", frame) is not None, f"[5] frame is a plain time form: {frame}")
        ok(n_render >= 30, f"[5] the language check ran over {n_render} rendered clauses")

        # ---- [6] nothing earlier clears --------------------------------------------------------------
        other = "a long walk to the far orchard with nothing particular in mind beyond the colour of the leaves"
        r6 = spc.observe_repeat_record(other, stub_embed(other), streak=3, store_t0=T0, now=NOW)
        ok(r6 is not None and not r6["would_render"] and r6["line"] is None and r6["clauses"] == [] and r6["quotes"] == [],
           "[6] no qualifying earlier row -> would_render False, line None, row still logged")
        ok(spc.verify_row(r6) == [], "[6] and that row verifies (nothing rendered, nothing recomputed)")

        # ---- [7] read-only ---------------------------------------------------------------------------
        n_before = wconn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0]
        spc.observe_repeat_record(THOUGHT, vec, streak=2, store_t0=T0, now=NOW)
        ok(wconn.execute("SELECT COUNT(*) FROM memory_fragments").fetchone()[0] == n_before, "[7] row count unchanged by observe_repeat_record")
        rc = spc._ro_connect(db)
        try:
            rc.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp) VALUES ('x','y',1)")
            ok(False, "[7] a write through the module's connection must be refused")
        except sqlite3.OperationalError:
            pass
        finally:
            rc.close()

        # ---- [8] pool is incremental ---------------------------------------------------------------------
        reset_pool()
        spc.observe_repeat_record(THOUGHT, vec, streak=2, store_t0=T0, now=NOW)
        n_pool = len(spc._pool["ids"])
        nr = variant(WORDS, 1).replace("keeper", "warden")
        insert(wconn, "fnew", nr, NOW - 100.0)
        r8 = spc.observe_repeat_record(THOUGHT, vec, streak=2, store_t0=NOW - 50.0, now=NOW)
        ok(len(spc._pool["ids"]) == n_pool + 1 and "fnew" in spc._pool["ids"], "[8] the newly stored row joined the cached pool")
        ok(any(c["id"] == "fnew" for c in r8["top_candidates"]), "[8] and is an earlier candidate on the next trigger")
        r8b = spc.observe_repeat_record(THOUGHT, vec, streak=2, store_t0=NOW - 200.0, now=NOW)
        ok(all(c["id"] != "fnew" for c in r8b["top_candidates"]), "[8] a row stored after store_t0 is never earlier")
        r8c = spc.observe_repeat_record(THOUGHT, vec, streak=2, now=NOW)
        ok(r8c["store_t0_source"] == "default_now_minus_30s", "[8] a missing store_t0 is logged as a default")

        # ---- [10] status -----------------------------------------------------------------------------
        railc = spc._RAILC_LOG
        t_first = json.loads(spc._LOG.read_text(encoding="utf-8").splitlines()[0])["ts"]
        railc.write_text("".join(json.dumps({"ts": t_first + i}) + "\n" for i in range(2000)), encoding="utf-8")
        sd = spc.status(5000)
        rr = sd.get("repeat_record", {})
        ok(rr.get("rows", 0) >= 40 and rr["would_render"] >= 30, f"[10] status counts repeat rows: {rr}")
        ok(rr["idle_rows_since_first"] == 2000 and rr["would_render_share_of_idle"] is not None, "[10] share of idle computed against the Rail C rows")
        ok(rr["language_problems"] == 0 and rr["non_recomputable"] is None, "[10] language clean; recompute not checked unless asked")
        ok(rr["stop"] is (rr["would_render_share_of_idle"] > 0.05), f"[10] stop follows the 5 percent bar: share {rr['would_render_share_of_idle']}")
        sv = spc.status(5000, verify_repeat=True)["repeat_record"]
        ok(sv["non_recomputable"] == 0 and sv["non_recomputable_checked"] > 0, f"[10] verify_repeat recomputes the tail and finds none bad: {sv}")
        railc.write_text("".join(json.dumps({"ts": t_first + i}) + "\n" for i in range(100000)), encoding="utf-8")
        # a corrupted logged row trips the stop
        with open(spc._LOG, "a", encoding="utf-8") as f:
            bad_row = json.loads(json.dumps(row))
            bad_row["clauses"][0]["text"] = 'At 03:00 you wrote: "nothing like it"'
            f.write(json.dumps(bad_row) + "\n")
        sb = spc.status(5000, verify_repeat=True)["repeat_record"]
        ok(sb["non_recomputable"] >= 1 and sb["stop"] is True, f"[10] a non-recomputable logged clause sets stop: {sb}")

        # ---- [6b] the optional feeling-word skip (default off): his own quoted words are his, unless the switch is on
        NEEDY = variant(WORDS, 1).replace("keeper", "need")
        insert(wconn, "fneed", NEEDY, at(2026, 11, 7, 9, 30))
        ok(cos_of(THOUGHT, NEEDY) >= SIM, "[6b] seed sanity: the feeling-word row is near")
        reset_pool()
        ok(spc.REPEAT_SKIP_FEELING_QUOTES is False, "[6b] default: not skipped")
        r6a = spc.observe_repeat_record(THOUGHT, vec, streak=2, store_t0=T0, now=NOW)
        ok(any("need" in q["feeling_words"] for q in r6a["quotes"]) or all(q["id"] != "fneed" for q in r6a["quotes"]),
           "[6b] a quoted feeling word of his own is listed per quote")
        spc.REPEAT_SKIP_FEELING_QUOTES = True
        try:
            r6b = spc.observe_repeat_record(THOUGHT, vec, streak=2, store_t0=T0, now=NOW)
        finally:
            spc.REPEAT_SKIP_FEELING_QUOTES = False
        ok(all(q["id"] != "fneed" for q in r6b["quotes"]) and not any(q["feeling_words"] for q in r6b["quotes"]),
           f"[6b] with the switch on no quote carries a feeling word: {r6b['quotes']}")
        ok(spc.verify_row(r6b) == [], "[6b] and the row verifies")
        wconn.execute("DELETE FROM memory_fragments WHERE fragment_id='fneed'")
        wconn.commit()
        reset_pool()

        # ---- [9] fence -------------------------------------------------------------------------------
        keep = spc._LOG
        live_path = Path(spc.__file__).parent.parent / "data" / "stale_patch_cue_shadow.jsonl"
        existed = live_path.exists()
        size0 = live_path.stat().st_size if existed else 0
        spc._LOG = live_path
        ok(not profile.LIVE, "[9] this test process is not live")
        try:
            spc.observe_repeat_record(THOUGHT, vec, streak=2, store_t0=T0, now=NOW)
            ok(False, "[9] a non-live process must be refused")
        except profile.NonLiveWriteError:
            pass
        ok(live_path.exists() == existed and (not existed or live_path.stat().st_size == size0), "[9] nothing was written to the live path")
        spc._LOG = keep
        wconn.close()
    finally:
        store._embed = real_embed

# ---- [11] shadow-only structure ---------------------------------------------------------------------------
src = (ROOT / "nodes" / "inner_monologue_node.py").read_text(encoding="utf-8")
calls = sorted(re.findall(r"_spc\.(\w+)", src))
ok(calls == ["observe", "observe_repeat_record"], f"[11] the node calls the module exactly twice, got {calls}")
i = src.index("_spc.observe_repeat_record")
window = "\n".join(src.splitlines()[max(0, src[:i].count("\n") - 16): src[:i].count("\n") + 10])
ok("seed_parts" not in window and "system_prompt" not in window and "gap" not in window.replace("grounding", ""),
   "[11] the hook block touches no seed list, system prompt or gap")
ok('_se_h.fires("habituation"' in src and "Habituation voice (Always-On, 2026-06-11)" in src, "[11] the dead habituation block is still there, untouched")
ok('"store_t0"' in src and '"streak_end"' in src and "_bs_tick_start" in src, "[11] the node ctx carries store_t0 / streak_end / streak_start")
m = re.search(r"^RUMINATION_SIM\s*=\s*([0-9.]+)", src, re.M)
ok(m and float(m.group(1)) == SIM == spc.REPEAT_SIM, f"[11] REPEAT_SIM == the node's RUMINATION_SIM ({m.group(1) if m else None})")
mod = (ROOT / "core" / "stale_patch_cue.py").read_text(encoding="utf-8")
code = re.sub(r'""".*?"""', "", mod, flags=re.S)
ok(not re.search(r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER)\b", code), "[11] the module contains no write SQL")
ok("mode=ro" in code and "boredom.record" not in code and "_save(" not in code, "[11] read-only connection; boredom untouched")

print("ALL OK" if not fails else f"{len(fails)} FAILURES")
sys.exit(1 if fails else 0)
