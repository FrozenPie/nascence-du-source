"""Follow Line bridge lab harness (J-3793). Pre-registration: docs/lab/FL_bridge_preregistration.md. Plan: question_cargo.

Phases (all resumable; outputs only under docs/lab/FL_bridge_data/):
    python -u scripts/_lab_FL_bridge_replay.py prep        # pieces + grounds per case (no model call; read-only sqlite)
    python -u scripts/_lab_FL_bridge_replay.py gen         # arms V0, V1, V2, V2c on the generator (Ramses :11441), one call in flight
    python -u scripts/_lab_FL_bridge_replay.py judge       # rubric (2 judges x outputs) + pairwise, one call in flight
    python -u scripts/_lab_FL_bridge_replay.py handcheck   # writes a blind 20-output sample for the hand check
    python -u scripts/_lab_FL_bridge_replay.py report      # tables, Wilson, sign tests, verdict text -> report_tables.md

Safety (section 8): runs from a throwaway worktree; `import core` BEFORE lab_env; live DB opened mode=ro only; no
memory_service.ask, no evidence_recall.gather; a write-audit hook counts any open-for-write under C:\\Nascence\\data; a
size+mtime canary of data/ top level is taken before and after every phase.
"""
from __future__ import annotations
import sys, os, json, time, random, re, math, sqlite3, asyncio, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
import numpy as np
from core import follow_line as fl
from core.memory import store
sys.path.append(r"C:\Users\USER\.claude\skills\job-queue")
from lab_env import isolate
import _lab_FL_bridge_prompts as P

LIVE_DATA = Path(r"C:\Nascence\data")
LIVE_DB = LIVE_DATA / "memory" / "nascence.db"
OUT = ROOT / "docs" / "lab" / "FL_bridge_data"
SEED = 4416
GEN_URLS = ["http://LAN-HOST:11441"]
JUDGES = {"gemma4": "http://127.0.0.1:11439", "falcon3": "http://127.0.0.1:11440"}
if os.environ.get("FL_JUDGE_ONLY"):          # run one judge per process (gemma4 answers in ~90 s, falcon3 in ~12 s; one call in flight PER HUB)
    JUDGES = {k: v for k, v in JUDGES.items() if k == os.environ["FL_JUDGE_ONLY"]}
ORIGINS = ["study", "reading", "gist", "understanding", "journal", "journal_week", "lived", "nature", "sound",
           "listening", "essay", "research"]
LETTERS = "ABCD"
BRIDGE_MAX_TOKENS = 320

# ── write audit + canary ──────────────────────────────────────────────────────────────────────────────────────
WRITES: list = []
def _audit(event, args):
    if event == "open":
        path, mode = args[0], args[1]
        try:
            if isinstance(path, (str, bytes, os.PathLike)) and mode and any(c in str(mode) for c in "wax+"):
                p = os.path.abspath(os.fsdecode(path)).lower()
                if p.startswith(r"c:\nascence\data") and not p.startswith(r"c:\nascence\data\_lab"):
                    WRITES.append(p)
        except Exception:
            pass
sys.addaudithook(_audit)

def canary() -> dict:
    out = {}
    for p in sorted(LIVE_DATA.iterdir()):
        try:
            st = p.stat()
            out[p.name] = (st.st_size, st.st_mtime_ns)
        except OSError:
            pass
    return out

def canary_diff(a: dict, b: dict) -> list:
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))

# ── helpers ───────────────────────────────────────────────────────────────────────────────────────────────────
def jl_read(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

def jl_append(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def age_phrase(ts_q: float, ts: float) -> str:
    d = max(0.0, (ts_q - ts) / 86400.0)
    if d < 1: return "earlier that day"
    if d < 2: return "yesterday"
    if d < 30: return f"{int(d)} days ago"
    if d < 60: return "a month ago"
    return f"{int(d / 30)} months ago"

def trigrams(t: str) -> set:
    t = " ".join((t or "").lower().split())
    return {t[i:i + 3] for i in range(max(0, len(t) - 2))}

def jacc(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 0.0

def cases() -> list:
    return json.loads((OUT / "cases.json").read_text(encoding="utf-8"))["cases"]

# ── prep ──────────────────────────────────────────────────────────────────────────────────────────────────────
def prep() -> None:
    cs = cases()
    conn = sqlite3.connect(f"file:{LIVE_DB.as_posix()}?mode=ro", uri=True)
    ph = ",".join("?" * len(ORIGINS))
    rows = conn.execute(f"SELECT fragment_id, origin, timestamp, embedding FROM memory_fragments "
                        f"WHERE origin IN ({ph}) AND embedding IS NOT NULL", ORIGINS).fetchall()
    ids = [r[0] for r in rows]; org = [r[1] for r in rows]
    ts = np.array([r[2] for r in rows], dtype=np.float64)
    E = np.vstack([np.frombuffer(r[3], dtype=np.float32) for r in rows])
    print(f"pool rows {len(rows)}  dim {E.shape[1]}")
    inputs = []
    for c in cs:
        qv = store._embed(c["q"])
        sims = E @ qv
        mask = ts < c["ts"]
        gset = set(c["ground_fragment_ids"])
        if gset:
            mask &= ~np.isin(np.array(ids), list(gset))
        cand = np.where(mask)[0]
        top = cand[np.argsort(-sims[cand])[:40]]
        # grounds (re-read by fragment id, same order as production)
        grounds = []
        for fid in c["ground_fragment_ids"]:
            r = conn.execute("SELECT content, origin, timestamp FROM memory_fragments WHERE fragment_id=?", (fid,)).fetchone()
            if r:
                grounds.append({"fragment_id": fid, "origin": r[1], "age": age_phrase(c["ts"], r[2]), "text": fl._grounds_cut(r[0] or "")})
        pieces, taken_org, taken_tg = [], set(), []
        for i in top:
            cos = float(sims[i])
            if cos < 0.25 or len(pieces) >= 4:
                break
            if org[i] in taken_org:
                continue
            r = conn.execute("SELECT content FROM memory_fragments WHERE fragment_id=?", (ids[i],)).fetchone()
            raw = (r[0] or "") if r else ""
            if org[i] == "lived" and fl._is_conversation_record(raw):
                continue
            text = fl._clip_boundary(raw.strip(), 200)
            tg = trigrams(text)
            if any(jacc(tg, t2) >= 0.50 for t2 in taken_tg):
                continue
            pieces.append({"fragment_id": ids[i], "origin": org[i], "age": age_phrase(c["ts"], float(ts[i])),
                           "cos": round(cos, 4), "text": text})
            taken_org.add(org[i]); taken_tg.append(tg)
        inputs.append({"q_id": c["q_id"], "stratum": c["stratum"], "q": c["q"], "ts": c["ts"], "grounds": grounds,
                       "pieces": pieces, "n_ground_ids": len(c["ground_fragment_ids"]),
                       "thin": len({p["origin"] for p in pieces}) < 2})
    conn.close()
    (OUT / "inputs.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print("pieces per case:", sorted(Counter(len(x["pieces"]) for x in inputs).items()),
          " thin:", sum(x["thin"] for x in inputs),
          " grounds missing:", sum(x["n_ground_ids"] - len(x["grounds"]) for x in inputs))

def load_inputs() -> list:
    return json.loads((OUT / "inputs.json").read_text(encoding="utf-8"))

# ── prompts / generation ──────────────────────────────────────────────────────────────────────────────────────
def g_block(grounds: list) -> str:
    return "\n".join(f"[{i}] ({g['origin']}, {g['age']}) {g['text']}" for i, g in enumerate(grounds, 1))

def p_block(pieces: list) -> str:
    return "\n".join(f"[{LETTERS[i]}] ({p['origin']}, {p['age']}) {p['text']}" for i, p in enumerate(pieces))

def sys_for(base: str, v1: bool) -> str:
    return base + (P.V1_ADDED_SENTENCE if v1 else "")

def user_why(inp: dict, v1: bool) -> str:
    u = f"{fl._input_label(inp['q'])}: {inp['q']}\n\nGROUNDS:\n" + (g_block(inp["grounds"]) if inp["grounds"] else "(none)")
    if v1 and inp["pieces"]:
        u += "\n\n" + P.ALSO_NEARBY_HEADER + "\n" + p_block(inp["pieces"])
    return u

def user_cons(inp: dict, why_text: str, v1: bool) -> str:
    u = f"{fl._input_label(inp['q'])}: {inp['q']}\n"
    if inp["grounds"]:
        u += "GROUNDS:\n" + "\n".join(f"[{i}] {g['text']}" for i, g in enumerate(inp["grounds"], 1)) + "\n"
    if v1 and inp["pieces"]:
        u += P.ALSO_NEARBY_HEADER + "\n" + p_block(inp["pieces"]) + "\n"
    if why_text:
        u += f"WHY: {why_text}\n"
    return u

async def gen_json(system: str, user: str, max_tokens: int, rec: dict) -> dict:
    from core.model_client import call_node_json
    t0 = time.monotonic()
    rec["calls"] = rec.get("calls", 0) + 1
    try:
        d = await call_node_json(GEN_URLS, system, user, max_tokens=max_tokens, temperature=0.3)
        return d if isinstance(d, dict) else {}
    except Exception as exc:
        rec.setdefault("errors", []).append(repr(exc)[:200])
        return {}
    finally:
        rec["secs"] = round(rec.get("secs", 0.0) + time.monotonic() - t0, 1)

async def run_stops(inp: dict, v1: bool, rec: dict) -> dict:
    """why, consequences, against. V0 skips why/against with no grounds (production); V1 skips only with neither."""
    have = bool(inp["grounds"]) or (v1 and bool(inp["pieces"]))
    out = {"why": "", "why_cites": [], "cons": [], "against": "", "against_cites": []}
    n_g = len(inp["grounds"]); n_all = n_g + (len(inp["pieces"]) if v1 else 0)
    def cites(d):
        res = []
        for c in (d.get("cites") or []):
            if isinstance(c, (int, float)) and 1 <= int(c) <= n_g: res.append(int(c))
            elif isinstance(c, str) and len(c) == 1 and c.upper() in LETTERS[:len(inp["pieces"])] and v1: res.append(c.upper())
        return res
    if have:
        d = await gen_json(sys_for(fl._WHY_SYS_V2, v1), user_why(inp, v1), fl.GEN_MAX_TOKENS, rec)
        out["why"] = fl._clip_boundary(str(d.get("why", "") or "").strip(), 400)
        out["why_cites"] = cites(d)
    d = await gen_json(sys_for(fl._CONS_SYS_V2, v1), user_cons(inp, out["why"], v1), fl.GEN_MAX_TOKENS, rec)
    for c in (d.get("consequences") or [])[:3]:
        if isinstance(c, dict):
            t = str(c.get("text", "") or "").strip()[:220]
            if len(t) >= 12:
                out["cons"].append(t)
    if have:
        d = await gen_json(sys_for(fl._AGAINST_SYS_V2, v1), user_why(inp, v1), fl.GEN_MAX_TOKENS, rec)
        t = fl._clip_boundary(str(d.get("objection", "") or "").strip(), 400)
        if t.rstrip(". ").lower() in ("none", "no objection", "no real objection", "n/a", "nothing"):
            t = ""
        out["against"] = t
        out["against_cites"] = cites(d) if t else []
    return out

def bridge_items(grounds: list, pieces: list) -> list:
    return list(grounds) + list(pieces)

async def run_bridge(q: str, items: list, rec: dict) -> dict:
    user = f"QUESTION: {q}\n\nPIECES:\n" + "\n".join(f"[{i}] ({g['origin']}, {g['age']}) {g['text']}" for i, g in enumerate(items, 1))
    d = await gen_json(P.BRIDGE_SYS, user, BRIDGE_MAX_TOKENS, rec)
    idx = [int(x) for x in (d.get("pieces") or []) if isinstance(x, (int, float)) and 1 <= int(x) <= len(items)]
    none = bool(d.get("none")) if "none" in d else (not d.get("structure"))
    return {"structure": str(d.get("structure", "") or "").strip(), "pieces": sorted(set(idx)),
            "prediction": str(d.get("prediction", "") or "").strip(), "breaks_when": str(d.get("breaks_when", "") or "").strip(),
            "none": none, "n_items": len(items), "empty": not d}

def donors(inps: list) -> dict:
    """V2c: for each case a seeded random OTHER case of a different stratum, with at least 2 texts, and unrelated question."""
    rng = random.Random(SEED)
    res = {}
    for inp in inps:
        pool = [o for o in inps if o["stratum"] != inp["stratum"] and len(o["grounds"]) + len(o["pieces"]) >= 2
                and jacc(trigrams(o["q"]), trigrams(inp["q"])) < 0.2]
        res[inp["q_id"]] = rng.choice(pool)["q_id"]
    return res

async def gen_phase() -> None:
    inps = load_inputs()
    by = {i["q_id"]: i for i in inps}
    don = donors(inps)
    runs_p = OUT / "author_runs.jsonl"
    done = {(r["q_id"], r["arm"]) for r in jl_read(runs_p)}
    saved = {(r["q_id"], r["arm"]): r for r in jl_read(runs_p)}
    n = 0
    for inp in inps:
        qid = inp["q_id"]
        for arm in ("V0", "V1", "V2", "V2c"):
            if (qid, arm) in done:
                continue
            rec = {"q_id": qid, "arm": arm, "ts": time.time()}
            if arm == "V0":
                rec["out"] = await run_stops(inp, False, rec)
            elif arm == "V1":
                rec["out"] = await run_stops(inp, True, rec)
            elif arm == "V2":
                v1 = saved.get((qid, "V1")) or next(r for r in jl_read(runs_p) if r["q_id"] == qid and r["arm"] == "V1")
                rec["out"] = v1["out"]                                  # V1's three stops, then the bridge
                rec["bridge"] = await run_bridge(inp["q"], bridge_items(inp["grounds"], inp["pieces"]), rec)
            else:
                d = by[don[qid]]
                rec["donor"] = d["q_id"]
                rec["bridge"] = await run_bridge(inp["q"], bridge_items(d["grounds"], d["pieces"]), rec)
            jl_append(runs_p, rec); saved[(qid, arm)] = rec; n += 1
            print(f"{qid} {arm} calls={rec.get('calls')} secs={rec.get('secs')} err={len(rec.get('errors', []))}", flush=True)
    print("gen done, new records:", n)

# ── judging ───────────────────────────────────────────────────────────────────────────────────────────────────
def texts_for(inp: dict, arm: str, by: dict, don: dict) -> tuple:
    """(grounds, pieces) the arm saw; V2c saw the donor's."""
    if arm == "V0": return inp["grounds"], []
    if arm == "V2c":
        d = by[don[inp["q_id"]]]; return d["grounds"], d["pieces"]
    return inp["grounds"], inp["pieces"]

def texts_block(gr: list, pi: list) -> str:
    parts = [f"[{i}] ({g['origin']}) {g['text']}" for i, g in enumerate(gr, 1)]
    parts += [f"[{LETTERS[i]}] ({p['origin']}) {p['text']}" for i, p in enumerate(pi)]
    return "\n".join(parts) if parts else "(no texts)"

def label_of(idx: int, gr: list) -> str:
    """bridge index (1-based over grounds then pieces) -> the label shown in the TEXTS block"""
    return f"[{idx}]" if idx <= len(gr) else f"[{LETTERS[idx - len(gr) - 1]}]"

def return_text(rec_stops: dict | None, bridge: dict | None, gr: list) -> str:
    parts = []
    if rec_stops:
        if rec_stops["why"]: parts.append("WHY: " + rec_stops["why"])
        if rec_stops["cons"]: parts.append("CONSEQUENCES:\n" + "\n".join("- " + c for c in rec_stops["cons"]))
        if rec_stops["against"]: parts.append("AGAINST: " + rec_stops["against"])
    if bridge is not None:
        if bridge["none"] or not bridge["structure"]:
            parts.append("BRIDGE: no shared structure found.")
        else:
            parts.append("BRIDGE: " + bridge["structure"] + " (rests on " + ", ".join(label_of(i, gr) for i in bridge["pieces"]) + ")"
                         + "\nPREDICTION: " + bridge["prediction"] + "\nBREAKS WHEN: " + bridge["breaks_when"])
    return "\n".join(parts) if parts else "(empty return)"

def judge_call(url: str, system: str, user: str, key_ok) -> tuple:
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": 160}}
    err, t0 = None, time.monotonic()
    for attempt, wait in enumerate((0, 20, 60)):
        if wait: time.sleep(wait)
        try:
            req = urllib.request.Request(url + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = json.loads(r.read())
            v = json.loads((data.get("message") or {}).get("content") or "")
            if isinstance(v, dict) and key_ok(v):
                return v, None, round(time.monotonic() - t0, 1)
            err = "parse"
        except Exception as exc:
            err = type(exc).__name__
    return None, err, round(time.monotonic() - t0, 1)

def rubric_ok(v: dict) -> bool:
    return v.get("s") in ("yes", "partly", "no") and v.get("c") in ("yes", "no") and v.get("n") in ("yes", "no")

def pair_ok(v: dict) -> bool:
    return v.get("winner") in ("A", "B", "neither")

def judge_phase() -> None:
    inps = load_inputs(); by = {i["q_id"]: i for i in inps}; don = donors(inps)
    runs = {(r["q_id"], r["arm"]): r for r in jl_read(OUT / "author_runs.jsonl")}
    rub_p, pair_p = OUT / "judge_runs_rubric.jsonl", OUT / "judge_runs_pair.jsonl"
    done_r = {(r["q_id"], r["arm"], r["judge"]) for r in jl_read(rub_p)}
    done_p = {(r["q_id"], r["pair"], r["judge"]) for r in jl_read(pair_p)}
    rng = random.Random(SEED)
    # rubric
    jobs = [(i["q_id"], arm) for i in inps for arm in ("V0", "V1", "V2", "V2c")]
    rng.shuffle(jobs)
    for qid, arm in jobs:
        inp = by[qid]; rec = runs[(qid, arm)]
        gr, pi = texts_for(inp, arm, by, don)
        out = return_text(None if arm == "V2c" else rec["out"], rec.get("bridge"), gr)
        user = f"QUESTION: {inp['q']}\n\nTEXTS:\n{texts_block(gr, pi)}\n\nOUTPUT:\n{out}"
        for jn, url in JUDGES.items():
            if (qid, arm, jn) in done_r: continue
            v, err, secs = judge_call(url, P.RUBRIC_SYS, user, rubric_ok)
            jl_append(rub_p, {"q_id": qid, "arm": arm, "judge": jn, "v": v, "err": err, "secs": secs})
            print("rubric", qid, arm, jn, err or (v["s"], v["c"], v["n"], v.get("p")), flush=True)
    # pairwise
    for pair in (("V1", "V0"), ("V2", "V1"), ("V2", "V0")):
        for inp in inps:
            qid = inp["q_id"]
            gr, pi = inp["grounds"], inp["pieces"]
            order = list(pair); rng.shuffle(order)
            texts = {a: return_text(runs[(qid, a)]["out"], runs[(qid, a)].get("bridge") if a == "V2" else None, gr) for a in pair}
            user = (f"QUESTION: {inp['q']}\n\nTEXTS:\n{texts_block(gr, pi)}\n\nRETURN A:\n{texts[order[0]]}\n\nRETURN B:\n{texts[order[1]]}")
            for jn, url in JUDGES.items():
                key = f"{pair[0]}>{pair[1]}"
                if (qid, key, jn) in done_p: continue
                v, err, secs = judge_call(url, P.PAIR_SYS, user, pair_ok)
                w = None if v is None else ("neither" if v["winner"] == "neither" else order[0 if v["winner"] == "A" else 1])
                jl_append(pair_p, {"q_id": qid, "pair": key, "judge": jn, "order": order, "winner": w, "err": err, "secs": secs})
                print("pair", qid, key, jn, err or w, flush=True)

# ── hand check sample ─────────────────────────────────────────────────────────────────────────────────────────
def handcheck() -> None:
    inps = load_inputs(); by = {i["q_id"]: i for i in inps}; don = donors(inps)
    runs = {(r["q_id"], r["arm"]): r for r in jl_read(OUT / "author_runs.jsonl")}
    keys = [(i["q_id"], a) for i in inps for a in ("V0", "V1", "V2", "V2c")]
    rng = random.Random(SEED + 1); pick = rng.sample(keys, 20)
    lines = ["# Hand-check sample (blind to arm; labels in handcheck_labels.json keyed by item number)\n"]
    key_map = {}
    for n, (qid, arm) in enumerate(pick, 1):
        inp = by[qid]; rec = runs[(qid, arm)]; gr, pi = texts_for(inp, arm, by, don)
        out = return_text(None if arm == "V2c" else rec["out"], rec.get("bridge"), gr)
        lines.append(f"## Item {n}\nQUESTION: {inp['q']}\nTEXTS:\n{texts_block(gr, pi)}\nOUTPUT:\n{out}\n")
        key_map[n] = [qid, arm]
    (OUT / "handcheck_sample.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "handcheck_key.json").write_text(json.dumps(key_map), encoding="utf-8")
    print("handcheck sample written")

# ── report ────────────────────────────────────────────────────────────────────────────────────────────────────
def wilson(k: float, n: int, z: float = 1.96) -> tuple:
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def sign_p(pos: int, neg: int) -> float:
    n = pos + neg
    if n == 0: return 1.0
    k = min(pos, neg)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

def report() -> None:
    inps = load_inputs(); by = {i["q_id"]: i for i in inps}; don = donors(inps)
    runs = {(r["q_id"], r["arm"]): r for r in jl_read(OUT / "author_runs.jsonl")}
    rub = jl_read(OUT / "judge_runs_rubric.jsonl"); pairs = jl_read(OUT / "judge_runs_pair.jsonl")
    def val(q, arm, key, f):
        vs = [f(r["v"][key]) for r in rub if r["q_id"] == q and r["arm"] == arm and r["v"] and key in r["v"] and f(r["v"][key]) is not None]
        return sum(vs) / len(vs) if vs else None            # split between the two judges = half credit
    S = lambda x: {"yes": 1.0, "partly": 0.0, "no": 0.0}.get(x); Sp = lambda x: {"yes": 1.0, "partly": 1.0, "no": 0.0}.get(x)
    Y = lambda x: {"yes": 1.0, "no": 0.0}.get(x)
    PP = lambda x: {"yes": 1.0, "partly": 1.0, "no": 0.0}.get(x)
    PN = lambda x: {"yes": 0.0, "partly": 0.0, "no": 1.0}.get(x)
    L = []
    def rate(arm, key, f, subset=None):
        qs = [i["q_id"] for i in inps if (subset is None or subset(i))]
        vs = [(q, val(q, arm, key, f)) for q in qs]; vs = [(q, v) for q, v in vs if v is not None]
        n = len(vs); k = sum(v for _, v in vs); lo, hi = wilson(k, n)
        return (k / n if n else float("nan"), lo, hi, n, dict(vs))
    def fmt(r): return f"{100*r[0]:.0f}% [{100*r[1]:.0f}-{100*r[2]:.0f}] n={r[3]}"
    def paired(a, b, key, f, subset=None):
        ra, rb = rate(a, key, f, subset)[4], rate(b, key, f, subset)[4]
        pos = sum(1 for q in ra if q in rb and ra[q] > rb[q]); neg = sum(1 for q in ra if q in rb and ra[q] < rb[q])
        return pos, neg, sign_p(pos, neg)
    for tag, subset in (("ALL 60 cases", None), ("WITHOUT thin cases", lambda i: not i["thin"])):
        L.append(f"\n### Rates, {tag} (mean of the two judges per output; a split is half credit; S = strict 'yes', S+ = yes or partly)\n")
        L.append("| measure | V0 | V1 | V2 | V2c |\n|---|---|---|---|---|")
        for name, key, f in (("S strict", "s", S), ("S+ (yes/partly)", "s", Sp), ("C combines", "c", Y), ("N non-trivial", "n", Y)):
            L.append(f"| {name} | " + " | ".join(fmt(rate(a, key, f, subset)) for a in ("V0", "V1", "V2", "V2c")) + " |")
        L.append("\nPaired sign tests (pos = first arm higher per case, neg = lower, ties dropped):\n")
        for a, b in (("V1", "V0"), ("V2", "V1"), ("V2", "V0")):
            for name, key, f in (("C", "c", Y), ("S", "s", S), ("N", "n", Y)):
                pos, neg, p = paired(a, b, key, f, subset)
                dpt = 100 * (rate(a, key, f, subset)[0] - rate(b, key, f, subset)[0])
                L.append(f"- {a} vs {b}, {name}: delta {dpt:+.1f} points, +{pos}/-{neg}, exact sign p={p:.3f}")
    # bridge-specific
    L.append("\n### Bridge outputs\n")
    for arm in ("V2", "V2c"):
        br = [(i["q_id"], runs[(i["q_id"], arm)]["bridge"]) for i in inps if (i["q_id"], arm) in runs]
        nn = [(q, b) for q, b in br if not b["none"] and b["structure"]]
        L.append(f"- {arm}: {len(br)} bridges, {len(nn)} claim a structure ('none' false), {len(br)-len(nn)} say none; empty/failed generations: {sum(1 for _, b in br if b['empty'])}")
        pp = [val(q, arm, "p", PP) for q, _ in nn]; pp = [v for v in pp if v is not None]
        pn = [val(q, arm, "p", PN) for q, _ in nn]; pn = [v for v in pn if v is not None]
        if pp:
            k = sum(pp); lo, hi = wilson(k, len(pp))
            L.append(f"  - P yes/partly among claimed structures: {100*k/len(pp):.0f}% [{100*lo:.0f}-{100*hi:.0f}] n={len(pp)}")
        if pn:
            k = sum(pn); lo, hi = wilson(k, len(pn))
            L.append(f"  - P no among claimed structures: {100*k/len(pn):.0f}% [{100*lo:.0f}-{100*hi:.0f}] n={len(pn)}")
        if arm == "V2c":
            L.append(f"  - V2c claimed-a-structure rate: {100*len(nn)/max(1,len(br)):.0f}% of {len(br)}")
    # pairwise
    L.append("\n### Pairwise (winner counts over both judges)\n")
    for key in ("V1>V0", "V2>V1", "V2>V0"):
        a, b = key.split(">")
        rr = [r for r in pairs if r["pair"] == key and r["winner"] is not None]
        wa = sum(1 for r in rr if r["winner"] == a); wb = sum(1 for r in rr if r["winner"] == b); ne = len(rr) - wa - wb
        sh = (wa + 0.5 * ne) / len(rr) if rr else float("nan")
        L.append(f"- {a} vs {b}: {a} wins {wa}, {b} wins {wb}, neither {ne} (n={len(rr)} judge-calls); {a} win share {100*sh:.0f}%")
    # cost, errors
    L.append("\n### Cost and failures\n")
    for arm in ("V0", "V1", "V2", "V2c"):
        rs = [runs[(i["q_id"], arm)] for i in inps if (i["q_id"], arm) in runs]
        L.append(f"- {arm}: {sum(r.get('calls',0) for r in rs)} calls, {sum(r.get('secs',0) for r in rs):.0f} s total, "
                 f"{sum(1 for r in rs if r.get('errors'))} records with errors")
    L.append(f"- judge failures (rubric): {sum(1 for r in rub if r['err'])}/{len(rub)}; (pair): {sum(1 for r in pairs if r['err'])}/{len(pairs)}")
    (OUT / "report_tables.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))

# ── main ──────────────────────────────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    before = canary()
    with isolate(db="empty"):
        if phase == "prep": prep()
        elif phase == "gen": asyncio.run(gen_phase())
        elif phase == "judge": judge_phase()
        elif phase == "handcheck": handcheck()
        elif phase == "report": report()
        else: print(__doc__)
    after = canary()
    print("CANARY data/ top-level changes:", canary_diff(before, after))
    print("WRITE-AUDIT opens-for-write under data/ (excl _lab):", len(WRITES), sorted(set(WRITES))[:10])
