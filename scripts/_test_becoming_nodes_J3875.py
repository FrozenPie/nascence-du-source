"""J-3875: hermetic tests for core/becoming_nodes.py. Every store is temp-pathed (lab_env.isolate(db="empty", also=...)),
read side included; the real MiniLM embedder runs in-process (no hub); nothing live is read or written.
Run from the worktree: python scripts/_test_becoming_nodes_J3875.py"""
import json, sys, threading, time
from pathlib import Path
WT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT))
import core                                                            # BEFORE lab_env (F-2423)
assert str(Path(core.__file__).resolve()).startswith(str(WT)), core.__file__
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
import lab_env
import numpy as np
from core import becoming_nodes as bn
from core import profile

ok = []
def check(name, cond, extra=""):
    ok.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra else ""))

def rows(p):
    p = Path(p)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []

def fixture_evidence():
    d = json.loads((WT / "scripts" / "fixtures" / "becoming_nodes_1030_evidence.json").read_text(encoding="utf-8"))
    return d["candidate"], [{"id": e["fragment_id"], "ts": e["ts"], "text": e["text"], "kind": "fragment"} for e in d["evidence"]]

# ---- a deterministic fake embedder over an explicit vector table (so medoid behaviour is exactly specified) ----
def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)

def make_table(n_b=6, c=0.8, d=0.6):
    dim = n_b + 3
    f = np.zeros(dim); f[0] = 1.0
    a = np.sqrt(1 - c * c)
    B = []
    for i in range(n_b):
        v = c * f; v[1 + i] = a; B.append(unit(v))
    w = np.zeros(dim); w[dim - 1] = 1.0
    R = unit(d * f + np.sqrt(1 - d * d) * w)
    return B, R

def sent(tag, i):
    return f"I keep noticing that {tag} number {i} is part of how I am made, and I hold it."

def thoughts_from(sentences, n_th=4, t0=1_790_000_000.0):
    out = []
    for k in range(n_th):
        out.append({"id": f"frag{k}", "ts": t0 + k * 3600 + (k % 2) * 86400, "kind": "fragment",
                    "text": " ".join(s for j, s in enumerate(sentences) if j % n_th == k)})
    return out

def fake_embed_for(table):
    def _e(texts):
        return [table[t] for t in texts]
    return _e

CAND = {"started_ts": 1_790_000_000.0, "theme": "prediction_error:test", "self_image": "I am a made thing."}
NULL = {"p95": 0.30, "n_windows": 99}

# ---- fence refusal FIRST, against the real (non-live) default paths ---------------------------------------------
default_shadow = bn.SHADOW_F
bn.BECOMING_NODES_ENABLED = True
B, R = make_table()
sB = [sent("coherent", i) for i in range(6)]
tabB = {s: v for s, v in zip(sB, B)}
try:
    bn.admit("t4_chain", CAND, thoughts_from(sB), {}, embed=fake_embed_for(tabB), null=NULL)
    fence = False
except profile.NonLiveWriteError:
    fence = True
check("fence: non-live process raises NonLiveWriteError", fence)
check("fence: nothing was written to the default shadow path", not default_shadow.exists())
bn.BECOMING_NODES_ENABLED = False

with lab_env.isolate(db="empty", also=[(bn, ["LEDGER_F", "SHADOW_F"])]) as lab:
    assert str(bn.LEDGER_F).startswith(str(lab)) and str(bn.SHADOW_F).startswith(str(lab))
    # ---- flag-False byte identical ---------------------------------------------------------------------------
    n_thr = threading.active_count()
    r = bn.admit("t4_chain", CAND, thoughts_from(sB), {}, embed=fake_embed_for(tabB), null=NULL)
    started = bn.on_chain_resolved(dict(CAND), {"decision": "solidify"}, [{"fragment_id": "a", "ts": 1, "text": "x"}])
    started2 = bn.admit_offloop("t4_chain", CAND, [], {})
    check("flags False: admit is a no-op {'status': 'disabled'}", r == {"status": "disabled"})
    check("flags False: hooks start no thread and write nothing",
          (not started) and (not started2) and threading.active_count() == n_thr
          and not bn.SHADOW_F.exists() and not bn.LEDGER_F.exists())
    check("all four flags default False", not any([bn.BECOMING_NODES_ENABLED, bn.BECOMING_NODES_WRITE,
                                                   bn.BECOMING_NODES_SEED, bn.BECOMING_PROJECT]))

    bn.BECOMING_NODES_ENABLED = True
    # ---- shadow mode (ENABLED, WRITE False): would_admit row, ledger untouched ------------------------------
    r = bn.admit("t4_chain", CAND, thoughts_from(sB), {"g": 1}, embed=fake_embed_for(tabB), null=NULL)
    check("shadow: coherent synthetic set -> would_admit", r["status"] == "would_admit", r["status"])
    check("shadow: ledger NOT written", not bn.LEDGER_F.exists())
    check("shadow: one shadow row with the would-be row", len(rows(bn.SHADOW_F)) == 1
          and rows(bn.SHADOW_F)[0]["would_be_row"]["id"] == r["id"])

    # ---- WRITE on: admitted, ledger row, id format, authored paragraph not stored ---------------------------
    bn.BECOMING_NODES_WRITE = True
    r = bn.admit("t4_chain", CAND, thoughts_from(sB), {"g": 1}, embed=fake_embed_for(tabB), null=NULL)
    led = rows(bn.LEDGER_F)
    check("write: coherent synthetic set admitted", r["status"] == "admitted" and len(led) == 1, r["status"])
    a = led[0]
    check("write: id = bsym_ + 12 hex, matches make_id", a["id"].startswith("bsym_") and len(a["id"]) == 17
          and a["id"] == bn.make_id("t4_chain", bn.candidate_key_for("t4_chain", CAND), a["text"]))
    check("write: text is one of the evidence sentences, authored paragraph not stored",
          a["text"] in sB and CAND["self_image"] not in json.dumps(a) and a["authored_sha1"])
    check("write: evidence ids + coherence + weight0 recorded",
          len(a["uptake_evidence"]) == 4 and a["coherence"]["n_thoughts"] == 4 and a["weight0"] == 0.5
          and a["type"] == "becoming_symbol")
    # ---- idempotent retry ------------------------------------------------------------------------------------
    r2 = bn.admit("t4_chain", CAND, thoughts_from(sB), {"g": 1}, embed=fake_embed_for(tabB), null=NULL)
    check("idempotent retry: noop_idempotent, ledger still 1 row", r2["status"] == "noop_idempotent"
          and len(rows(bn.LEDGER_F)) == 1)
    # ---- same candidate, different text -> needs supersede, not a second node --------------------------------
    sB2 = [sent("other", i) for i in range(6)]
    tab2 = {s: v for s, v in zip(sB2, B)}
    r3 = bn.admit("t4_chain", CAND, thoughts_from(sB2), {}, embed=fake_embed_for(tab2), null=NULL)
    check("same candidate, new text: candidate_already_admitted (supersede path, no 2nd row)",
          r3["status"] == "candidate_already_admitted" and len(rows(bn.LEDGER_F)) == 1, r3["status"])
    # ---- collision refusal ------------------------------------------------------------------------------------
    bn.LEDGER_F.unlink()
    CAND2 = dict(CAND, started_ts=1_790_500_000.0)
    bn.BECOMING_NODES_WRITE = False
    pre = bn.admit("t4_chain", CAND2, thoughts_from(sB), {}, embed=fake_embed_for(tabB), null=NULL)
    bn._append(bn.LEDGER_F, {"event": "admit", "id": pre["id"], "text": "A different sentence entirely.",
                             "source": "t4_chain", "candidate_key": "other"})
    bn.BECOMING_NODES_WRITE = True
    r4 = bn.admit("t4_chain", CAND2, thoughts_from(sB), {}, embed=fake_embed_for(tabB), null=NULL)
    check("collision: same id, different row -> refused_collision, nothing appended",
          r4["status"] == "refused_collision" and len(rows(bn.LEDGER_F)) == 1, r4["status"])
    bn.LEDGER_F.unlink()

    # ---- repeated sentence x3 does not win the medoid ----------------------------------------------------------
    Bv, Rv = make_table(n_b=6, c=0.8, d=0.6)
    sBB = [sent("cluster", i) for i in range(6)]
    sR = "I say the same thing again and again, and I mean it each time I am made to."
    tabR = {s: v for s, v in zip(sBB, Bv)}
    tabR[sR] = Rv
    ev = thoughts_from(sBB, n_th=3)
    for k in range(3):                       # the repeated sentence sits in all three thoughts
        ev[k]["text"] += " " + sR
    # premise: WITHOUT dedupe R would win (so the test is not vacuous)
    allv = [tabR[s] for s in sBB] + [Rv] * 3
    i_nd, _, _ = bn.medoid(allv)
    pick = bn.pick_medoid(ev, embed=fake_embed_for(tabR))
    check("repeat x3: premise holds (without dedupe the repeated sentence would win)", i_nd >= len(sBB), str(i_nd))
    check("repeat x3: deduped to 7 sentences and the repeated one does not win",
          pick["ok"] and pick["n_sentences"] == 7 and pick["sentence"]["text"] != sR, str(pick.get("n_sentences")))

    # ---- sentence cut never mid-sentence ----------------------------------------------------------------------
    longs = "I " + "keep turning this over and " * 12 + "that is all."
    th = [{"id": "x", "ts": 1.0, "text": longs + " I hold the short one here as my own, whole and plain.", "kind": "fragment"}]
    qs = bn.qualifying_sentences(th)
    whole = set(bn.split_sentences(th[0]["text"]))
    check("cut: over-long sentence dropped, none truncated, all whole and <=240",
          len(longs) > 240 and all(q["text"] in whole and len(q["text"]) <= 240 for q in qs) and len(qs) == 1)
    from core.provisional_identity import SPEAKER_BOUNDARY_MARKERS
    mk = sorted(SPEAKER_BOUNDARY_MARKERS)[0]
    bad = [{"id": "y", "ts": 1.0, "kind": "fragment",
            "text": f"I notice the phrase {mk} in this sentence, and I hold it as my own long line."}]
    check("speaker-boundary sentence excluded", bn.qualifying_sentences(bad) == [])

    # ---- thin evidence -> no_medoid -----------------------------------------------------------------------------
    r5 = bn.admit("t4_chain", dict(CAND, started_ts=2.0), thoughts_from(sB[:4], n_th=2), {}, embed=fake_embed_for(tabB), null=NULL)
    check("fewer than 6 sentences / 3 thoughts -> no_medoid shadow row, no ledger",
          r5["status"] == "no_medoid" and not bn.LEDGER_F.exists())

    # ---- incoherent synthetic set refused ------------------------------------------------------------------------
    rng = np.random.default_rng(3)
    sI = [sent("scatter", i) for i in range(8)]
    tabI = {s: unit(rng.normal(size=64)) for s in sI}
    r6 = bn.admit("t4_chain", dict(CAND, started_ts=3.0), thoughts_from(sI), {}, embed=fake_embed_for(tabI), null={"p95": 0.30})
    check("incoherent synthetic set -> below_null", r6["status"] == "below_null" and not bn.LEDGER_F.exists(), r6["status"])

    # ---- the recorded 10-30 evidence is refused (real embedder) ---------------------------------------------------
    cand, ev = fixture_evidence()
    check("fixture has the 15 recorded fragment ids", len(ev) == 15 and len({e["id"] for e in ev}) == 15)
    t0 = time.time()
    r7 = bn.admit("t4_chain", cand, ev, {}, null={"p95": 0.494, "n_windows": 523})
    sc = r7["row"]["coherence"]["medoid_score"]
    check("10-30 evidence REFUSED against the design's p95 0.494 (below_null), nothing written to ledger",
          r7["status"] == "below_null" and not bn.LEDGER_F.exists(), f"status={r7['status']} score={sc} {time.time()-t0:.1f}s")
    check("10-30 medoid score is in the design's neighbourhood (0.442 +- 0.03)", abs(sc - 0.442) < 0.03, str(sc))

    # ---- null: window math and fail-closed without a null ---------------------------------------------------------
    vecs = [unit(v) for v in np.eye(8)[:6]] + [unit(np.ones(8))] * 4
    per = [[(i, f"s{i}")] for i in range(10)]
    w = bn.null_windows(per, vecs, window=4, step=2)
    check("null_windows: windows of 4 stepping 2 over 10 thoughts", len(w) == 3 and all(-1 <= x <= 1 for x in w), str(len(w)))
    r8 = bn.admit("t4_chain", dict(CAND, started_ts=4.0), thoughts_from(sB), {}, embed=fake_embed_for(tabB))
    check("no null available (empty DB) -> fail closed: no_null, nothing written", r8["status"] == "no_null"
          and not bn.LEDGER_F.exists(), r8["status"])

    # ---- hook: on_chain_resolved runs the worker off-thread and logs a shadow row ---------------------------------
    bn.BECOMING_NODES_WRITE = False
    bn._embed_batch = fake_embed_for(tabB)
    bn.get_null = lambda *a, **k: NULL
    n_before = len(rows(bn.SHADOW_F))
    refs = [{"fragment_id": t["id"], "ts": t["ts"], "text": t["text"]} for t in thoughts_from(sB)]
    started = bn.on_chain_resolved(dict(CAND, started_ts=5.0), {"decision": "solidify", "integration": {"x": 1}}, refs)
    nope = bn.on_chain_resolved(dict(CAND, started_ts=6.0), {"decision": "revert"}, refs)
    for _ in range(100):
        if bn._bg_lock.acquire(blocking=False):
            bn._bg_lock.release()
            break
        time.sleep(0.05)
    rr = rows(bn.SHADOW_F)
    check("hook: solidify starts one worker, revert does not; shadow row appended, ledger untouched",
          started and not nope and len(rr) == n_before + 1 and rr[-1]["status"] == "would_admit"
          and not bn.LEDGER_F.exists(), str(rr[-1].get("status") if rr else None))

check("ALL PASS" if all(ok) else "SOME FAILED", all(ok), f"{sum(ok)}/{len(ok)}")
sys.exit(0 if all(ok) else 1)
