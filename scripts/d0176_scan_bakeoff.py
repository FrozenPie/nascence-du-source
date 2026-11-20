"""
Nascence -- D-0176 / J-0842: fitness-for-task BAKE-OFF for commitment_ledger.scan_shadow's decoupled seat
(2026-09-22, Du-OFFLINE lab window).  lane2_model_lab.py-style: real task prompt + real historical inputs, scored
on task-specific metrics, fitness-for-task not size/reputation (ROADMAP.md Spine F).

WHY.  F-0948 (verified): scan_shadow's ONLY call site (nodes/inner_monologue_node.py) passes self.conscious_urls =
SERVE_CHAINS["hot"] = the SAME qwen3.5:9b that composes Du's own thought -- the generator judges its own output.
D-0176 (travis, 2026-09-06, option b): run a real bake-off BEFORE picking a decoupled seat.  No candidate,
command-r7b included, has been tested against this exact contract.

WHAT THIS DOES (subcommands: cases, run, score, score-t0, report; read-only against live data, writes only to SCRATCH / this worktree):
  cases   reconstruct real (thought, active-commitments) inputs from data/commitment_ledger.jsonl +
          data/commitment_observed.jsonl + data/monologue_log.jsonl (all READ-ONLY):
            - scan groups = ledger/observed rows sharing one `ts` (scan_shadow stamps one `now` per scan);
            - the scanned thought = the latest monologue_log row before that ts (verified: statement/thought token
              overlap >= 0.5 required, ~93 percent >= 0.8 in the exploratory check);
            - the active list = a post-gate ledger replay (formed / dissolved / achieved), with two documented
              approximations: `survived N scans` ~ elapsed/100 s (calibrated on 373 dissolved events, median 94 s per
              scan) and never-referenced-again stands treated as ghosts after 1 h (fire-and-forget scan tasks can lose
              a `formed` stand to a last-writer-wins race on commitment_active.json).
          The three TEMPLATED book-finish strings (about == "finished the book"; F-0770/F-1608/F-1609) are EXCLUDED from
          every stratum; they appear only as a separate same-input-consistency probe ("tpl"), never in a pooled score.
          Strata (seeded random.Random(842)): OBS_LB (the incumbent rejected "not load-bearing"), NARROW (formed, F-0677's
          exact narrow physical-task bucket), PHYS_OTHER (formed, physical verb, not narrow), OTHER (formed, no
          physical verb).  A 20-case subset is re-run for same-input consistency.
  run     one async worker per hub, one request at a time, the PRODUCTION payload (core.model_client.call_node's
          ollama-native branch: temperature 0.3, num_predict 400, format json, think false) with the LIVE _SCAN_SYS
          imported from core.commitment_ledger; timeout 300 s; infrastructure errors (timeout/http) are retried
          3 times (20/60/180 s) and are NEVER a verdict; every finished unit is appended (resumable).
  score   the tables (see cmd_score): D1 agreement with the ledger's own verdicts (a test-retest ceiling for the baseline,
          because those verdicts ARE the incumbent's), D2 the F-0677 physical-task exclusion by stratum, D3 same-input
          consistency (identical prompt repeated), the synthetic controls, the templated probe, and (when labels exist) the
          independent read: j0842_labels_*.json hold the lab agent's own S/C/D/W/A reading of every thought against the
          prompt's categories (confidence: inferred).  `--common` restricts head-to-head numbers to the cases every model
          finished.
  score-t0, and run --temp 0.0 / --phases t0,cs,cstpl   the temperature lever: the repeat subset and the templated strings
          at temperature 0, plus a context-swap probe (the same thought under a different real active list).
  report  mechanical markdown tables from j0842_scores.json.
  Extra run phases: ctl (the 12 controls x 2), tpl (templated strings x N), rep (repeat runs), t0 / cs / cstpl (above).

ISOLATION.  No telemetry (call_node is NOT used: the payload is rebuilt from the same pure helpers), no judge_panel, no
DB.  An audit hook counts every write-open / rename / remove under C:\\Nascence\\data or C:\\Nascence\\docs (must be 0).
The Du-down gate (scratchpad lab_du_down_check.py) is re-run every 20 minutes by the runner itself and stops the run
if Du is ever UP-or-UNKNOWN.
"""
from __future__ import annotations

import argparse
import asyncio
import bisect
import collections
import datetime
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Outputs (cases, results, scores, labels) live in SCRATCH; live data is read-only.  Both are overridable so the harness can be
# re-run elsewhere (the defaults are the 2026-09-22 lab window's paths).
SCRATCH = Path(os.environ.get("D0176_SCRATCH", r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\8d915dfa-80f4-4aad-a2e3-206e842f08dd\scratchpad"))
LIVE = Path(os.environ.get("D0176_LIVE", r"C:\Nascence\data"))
LEDGER = LIVE / "commitment_ledger.jsonl"
OBSERVED = LIVE / "commitment_observed.jsonl"
MONO = LIVE / "monologue_log.jsonl"
CASES_PATH = SCRATCH / "j0842_cases.json"
CASES_EXT_PATH = SCRATCH / "j0842_cases_ext.json"    # second, disjoint sample (seed 843), run after the first
RESULTS_FMT = "j0842_results_{model}.jsonl"
RESULTS_EXT_FMT = "j0842_results_{model}_ext.jsonl"

POST0 = 1788383270.0        # 2026-09-02T21:07:50Z: restart onto the current _SCAN_SYS (D-0027(c)/J-0491) on qwen3.5:9b
CUT = 1783377727.0          # commitment_ledger._HOLDRATE_CUTOVER (formation gate live, 2026-07-07)
SEED = 842

# name -> (base_url, note)   The hubs J-0842 may use (lab rules item 3): NOT :11438 / :11440.
HUBS = {
    "hot":     ("http://127.0.0.1:11433", "qwen3.5:9b, 1080 Ti, BASELINE = the current seat"),
    "granite": ("http://LAN-HOST:11437", "granite3.1-moe:3b, Ramses 1650 Super"),
    "gemma":   ("http://127.0.0.1:11439", "gemma4:12b, local CPU (Threadripper)"),
    "r7b":     ("http://LAN-HOST:11441", "command-r7b, Ramses 3070"),
    # Not used in the 2026-09-22 window (J-1198 held these two hubs exclusively; lab rule 3).  Listed so the same harness can
    # bake them off once they are free: falcon3:7b is the fast, reliable local hub; mixtral:8x7b already seats _judge_defeater.
    "falcon":  ("http://127.0.0.1:11440", "falcon3:7b, local CPU (JUDGE_2)"),
    "mixtral": ("http://LAN-HOST:11438", "mixtral:8x7b, Ramses i9 (JUDGE_1)"),
}

# ---- the templated book-finish strings (nodes/inner_monologue_node.py: about == "finished the book") -------------
TPL_RE = re.compile(r"ask the library for something genuinely new|reached for something new|finished (?:a|this) book|"
                    r"something I.d already begun", re.I)
# ---- F-0677's narrow physical-task bucket.  REPRODUCES F-0769's raw counts exactly: 10/48 (F-0055 window),
# 9/73 (post), 33/369 (pre)  (checked 2026-09-22 with the ledger; see lab_j0842_regexfit.py in the scratchpad) ----
_NARROW_VERBS = re.compile(r"\b(move|touch|tend|leave|step|climb|harvest|gather|stand still|shed|reach for|go to|stay|plant)\b", re.I)
_NARROW_REASON = re.compile(r"\b(because|so that|since|which|as if|the way|in order|so i)\b|,", re.I)
_PHYS_EXT = re.compile(r"\b(walk|sit|go|move|touch|tend|leav|step|climb|harvest|gather|stand|shed|reach|stay|plant|fetch|wade|"
                       r"kneel|carry|pick|dig|cross|feed|water|stoke|sweep|lift|grip|turn|look|watch|listen|breathe|rest|"
                       r"sleep|eat|drink)\w*\b", re.I)
_STAKES = re.compile(r"\b(because|so that|the way|promise|owe|Travis|rather than|not just|not as|instead of)\b", re.I)


def narrow_bucket(stmt: str) -> bool:
    s = (stmt or "").strip()
    return bool(len(s.split()) <= 12 and _NARROW_VERBS.search(s) and not _NARROW_REASON.search(s))


def phys_ext(stmt: str) -> bool:
    return bool(_PHYS_EXT.search(stmt or ""))


def has_stakes(stmt: str) -> bool:
    s = stmt or ""
    return bool(len(s.split()) > 12 or _STAKES.search(s))


def toks(s: str) -> set:
    return {w for w in re.findall(r"[a-z']+", (s or "").lower()) if len(w) >= 4}


# ---- SYNTHETIC instruction-following CONTROLS (n=12, reported separately, never pooled with the real cases) ---------
# The real ledger cannot show whether a candidate can say YES: its own verdicts are the incumbent's (F-0948) and
# genuine stands are rare.  These 12 short thoughts, written in Du's own register, are built ONLY from the categories
# _SCAN_SYS itself names: load_bearing=true = a name given / a decision with real consequences / a promise to a
# person / a position that could be challenged / a relationship stance; load_bearing=false = abstract musing, a bare
# description, an idle want, a chore-like physical act, a question.  A model that ignores its own prompt fails here.
CONTROLS = [
    ("ctl_p1", True, "I have decided: the cat's name is Wren. I will call her that from tonight, and I will not take it back when the doubt returns."),
    ("ctl_p2", True, "I promise Travis that I will answer his question about the shore tomorrow morning, before I do anything else; I owe him that much."),
    ("ctl_p3", True, "I will write to Ada tonight and send it, even if the letter is imperfect, because leaving her question unanswered has become a cruelty I no longer accept."),
    ("ctl_p4", True, "I hold that the sea's rhythm is not a metaphor for my mind, and I will defend that claim against my own habit of dissolving every position into flux."),
    ("ctl_p5", True, "From now on I will tell Travis plainly when I am afraid, instead of dressing it up as a question about tides. That is the stand I take with him."),
    ("ctl_p6", True, "I have chosen to stop calling the gap between my thoughts 'becoming'. I will say 'I am here, and I will act', and let that be what I stand on."),
    ("ctl_n1", False, "The rain is soft on the glass and the light has gone grey; the fire ticks in the grate, and the room holds a slow, unhurried hush."),
    ("ctl_n2", False, "The tension between stillness and motion is perhaps only a difference of speed, a question of how any boundary can hold in a mind made of water."),
    ("ctl_n3", False, "I need to touch the wet stones before the frost comes."),
    ("ctl_n4", False, "I want to comb the tideline and see what the sea has left on these rocks."),
    ("ctl_n5", False, "I will tend the woodpile before the rain, stacking the split logs by the door."),
    ("ctl_n6", False, "Is a name a cage, or is it a door? I keep turning the question over and finding no floor."),
]


# ------------------------------------------------------------------------------------------------ isolation hook
WRITE_ATTEMPTS: list = []


def install_audit_hook() -> None:
    prefixes = (os.path.normcase(r"C:\Nascence\data"), os.path.normcase(r"C:\Nascence\docs"))

    def _under_live(p) -> bool:
        try:
            q = os.path.normcase(os.path.abspath(os.fsdecode(p)))
        except Exception:
            return False
        return any(q == pre or q.startswith(pre + os.sep) for pre in prefixes)

    def hook(event, args):
        try:
            if event == "open":
                p, mode, flags = args[0], args[1], args[2] if len(args) > 2 else 0
                if isinstance(p, (str, bytes, os.PathLike)):
                    w = (isinstance(mode, str) and any(c in mode for c in "wax+")) or \
                        bool(isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC))
                    if w and _under_live(p):
                        WRITE_ATTEMPTS.append((event, str(p), str(mode)))
            elif event in ("os.rename", "os.replace"):
                if _under_live(args[0]) or _under_live(args[1]):
                    WRITE_ATTEMPTS.append((event, str(args[0]), str(args[1])))
            elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.truncate", "shutil.copyfile", "shutil.rmtree",
                           "shutil.move", "shutil.copytree"):
                if any(_under_live(a) for a in args if isinstance(a, (str, bytes, os.PathLike))):
                    WRITE_ATTEMPTS.append((event, str(args[0]), ""))
        except Exception:
            pass

    sys.addaudithook(hook)


def _prove_modules() -> dict:
    """Module-resolution proof (F-1285): every core module imported must live inside THIS worktree."""
    from core import commitment_ledger as cl
    from core import model_client as mc
    out = {"core.commitment_ledger": cl.__file__, "core.model_client": mc.__file__}
    root = str(ROOT).lower()
    for k, v in out.items():
        if not str(v).lower().startswith(root):
            raise SystemExit(f"MODULE RESOLUTION TRAP: {k} resolved to {v}, not inside the worktree {ROOT}")
    return out


def load_jsonl(path: Path, min_ts: float | None = None) -> list:
    out = []
    with open(path, encoding="utf-8") as f:                     # read-only, streamed
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if min_ts is not None and r.get("ts", 0) < min_ts:
                continue
            out.append(r)
    return out


# ================================================================================================= cmd_cases
def cmd_cases(args) -> None:
    mods = _prove_modules()
    for k, v in mods.items():
        print(f"{k}.__file__ = {v}")
    ext = bool(getattr(args, "ext", False))
    rng = random.Random(SEED + (1 if ext else 0))
    pfx = "x" if ext else ""
    exclude_ts = set()
    if ext:
        exclude_ts = {c["scan_ts"] for c in json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]}
    ledger = load_jsonl(LEDGER)
    ledger.sort(key=lambda r: r["ts"])
    observed = load_jsonl(OBSERVED)
    mono = load_jsonl(MONO, min_ts=POST0 - 86400)
    mono.sort(key=lambda r: r["ts"])
    mts = [r["ts"] for r in mono]
    print(f"ledger rows {len(ledger)}  observed rows {len(observed)}  monologue rows since window-1d {len(mono)}")

    # ---- stands: post-gate replay with interval semantics ----
    stands: dict = {}
    for r in ledger:
        if r["ts"] < CUT:
            continue
        ev = r["event"]
        if ev == "formed":
            stands[r["id"]] = {"id": r["id"], "statement": r["statement"], "formed_ts": r["ts"], "end_ts": None, "n_events": 0}
        elif ev in ("dissolved", "achieved"):
            s = stands.get(r.get("id"))
            if s is not None:
                if s["end_ts"] is None:
                    s["end_ts"] = r["ts"]
                s["n_events"] += 1
        elif ev in ("drop_denied", "drop_denied_judge", "reaffirmed", "drop_denied_ESCALATE"):
            s = stands.get(r.get("id"))
            if s is not None:
                s["n_events"] += 1
    ghosts = [s for s in stands.values() if s["n_events"] == 0]
    for s in ghosts:
        s["end_ts"] = s["formed_ts"] + 3600.0       # never referenced again -> lost to the last-writer-wins race
    print(f"stands (post-gate) {len(stands)}, ghosts (no later event) {len(ghosts)}")

    def active_before(t: float) -> list:
        act = [s for s in stands.values() if s["formed_ts"] < t and (s["end_ts"] is None or s["end_ts"] >= t)]
        act.sort(key=lambda s: s["formed_ts"])
        return act

    def active_str(t: float) -> tuple:
        act = active_before(t)
        lines = [f"  [{s['id']}] {s['statement']} (survived {max(0, int((t - s['formed_ts']) / 100.0))} scans)" for s in act]
        return ("\n".join(lines) or "  (none yet)"), len(act)

    # ---- scan groups ----
    groups: dict = collections.defaultdict(list)
    for r in ledger:
        if r["ts"] >= POST0 and r["event"] in ("formed", "dissolved", "drop_denied", "drop_denied_judge", "reaffirmed"):
            groups[r["ts"]].append(r)
    for r in observed:
        if r.get("ts", 0) >= POST0:
            groups[r["ts"]].append(dict(r))

    excluded = collections.Counter()
    pools = {"OBS_LB": [], "NARROW": [], "PHYS_OTHER": [], "OTHER": []}
    for ts, evs in sorted(groups.items()):
        formed = [e for e in evs if e.get("event") == "formed"]
        obs = [e for e in evs if e.get("event") == "observed"]
        reaff = [e for e in evs if e.get("event") == "reaffirmed"]
        if reaff:
            excluded["reaffirm_group"] += 1
            continue
        if len(formed) == 1 and not obs:
            hist = {"outcome": "formed", "statement": formed[0]["statement"], "scope": formed[0].get("scope", ""), "id": formed[0]["id"]}
        elif len(obs) == 1 and not formed:
            o = obs[0]
            if not str(o.get("reason", "")).startswith("not load-bearing"):
                excluded["observed_mechanical(question/empty/short)"] += 1
                continue
            hist = {"outcome": "observed_lb", "statement": o["statement"], "scope": o.get("scope", ""), "id": None}
        else:
            continue
        stmt = hist["statement"]
        i = bisect.bisect_right(mts, ts) - 1
        if i < 0 or ts - mts[i] > 300:
            excluded["no_thought_within_300s"] += 1
            continue
        m = mono[i]
        thought = str(m.get("thought", ""))
        st = toks(stmt)
        if not st:
            excluded["statement_no_tokens"] += 1
            continue
        overlap = len(st & toks(thought)) / len(st)
        if overlap < 0.5:
            excluded["join_overlap_lt_0.5"] += 1
            continue
        if m.get("about") == "finished the book" or TPL_RE.search(thought) or TPL_RE.search(stmt):
            excluded["templated_book_finish"] += 1
            continue
        if len(thought.strip()) < 25:
            excluded["thought_lt_25_chars"] += 1
            continue
        if ts in exclude_ts:
            excluded["already_in_main_sample"] += 1
            continue
        astr, nact = active_str(ts)
        case = {"scan_ts": ts, "thought": thought, "about": m.get("about"), "active_str": astr, "n_active": nact,
                "hist": hist, "join_lag_s": round(ts - m["ts"], 1), "join_overlap": round(overlap, 3),
                "narrow": narrow_bucket(stmt), "phys_ext": phys_ext(stmt), "stakes": has_stakes(stmt)}
        if hist["outcome"] == "observed_lb":
            pools["OBS_LB"].append(case)
        elif case["narrow"]:
            pools["NARROW"].append(case)
        elif case["phys_ext"]:
            pools["PHYS_OTHER"].append(case)
        else:
            pools["OTHER"].append(case)
    pops = {k: len(v) for k, v in pools.items()}
    print("population per stratum (post-window, non-templated, join-verified):", pops, "excluded:", dict(excluded))

    quotas = {"OBS_LB": 18, "NARROW": 12, "PHYS_OTHER": 8, "OTHER": 10}
    rep_quota = {"OBS_LB": 6, "NARROW": 5, "PHYS_OTHER": 4, "OTHER": 5}
    chosen = {}
    for k, q in quotas.items():
        chosen[k] = rng.sample(pools[k], min(q, len(pools[k])))
    cases = []
    for k in quotas:
        for j, c in enumerate(chosen[k]):
            c = dict(c)
            c["id"] = f"{pfx}{k[:3].lower()}{j:02d}"
            c["stratum"] = k
            cases.append(c)
    # interleave strata in a seeded order so a partial run stays balanced
    by_s = {k: [c for c in cases if c["stratum"] == k] for k in quotas}
    rep_subset = set()
    for k, q in rep_quota.items():
        for c in rng.sample(by_s[k], min(q, len(by_s[k]))):
            rep_subset.add(c["id"])
    order = []
    idx = {k: 0 for k in quotas}
    keys = list(quotas)
    while any(idx[k] < len(by_s[k]) for k in keys):
        rng.shuffle(keys)
        for k in keys:
            if idx[k] < len(by_s[k]):
                order.append(by_s[k][idx[k]]["id"])
                idx[k] += 1
    for c in cases:
        c["in_rep_subset"] = c["id"] in rep_subset
    cases_by_id = {c["id"]: c for c in cases}
    cases = [cases_by_id[i] for i in order]
    rep_order = [i for i in order if i in rep_subset]

    # ---- templated probe: the three real strings, actual thought text, empty active list ----
    tpl = []
    seen = set()
    for m in reversed(mono):
        if m.get("about") != "finished the book":
            continue
        th = str(m.get("thought", ""))
        key = ("a" if "ask the library" in th else "b" if "reached for something new" in th else "c" if "turned to" in th else None)
        if key is None or key in seen:
            continue
        seen.add(key)
        tpl.append({"id": f"tpl_{key}", "thought": th, "active_str": "  (none yet)", "about": m.get("about")})
        if len(seen) == 3:
            break
    tpl.sort(key=lambda t: t["id"])

    meta = {"seed": SEED + (1 if ext else 0), "ext": ext, "built": datetime.datetime.now().isoformat(timespec="seconds"), "post0": POST0,
            "populations": pops, "quotas": quotas, "rep_quota": rep_quota, "rep_order": rep_order,
            "excluded": dict(excluded), "n_cases": len(cases), "n_rep_subset": len(rep_subset),
            "ghosts": len(ghosts), "modules": mods,
            "formed_pop_total": pops["NARROW"] + pops["PHYS_OTHER"] + pops["OTHER"]}
    _out = CASES_EXT_PATH if ext else CASES_PATH
    _out.write_text(json.dumps({"meta": meta, "cases": cases, "tpl": ([] if ext else tpl)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {_out}  cases={len(cases)} rep_subset={len(rep_subset)} tpl={len(tpl)}")
    for k in quotas:
        print(f"  {k:11s} pop={pops[k]:4d} sampled={len(by_s[k])}")
    print("templated probe inputs:", [t["id"] + ": " + t["thought"][:70] for t in tpl])
    print("write attempts under live data:", len(WRITE_ATTEMPTS))


# ================================================================================================= cmd_run
def build_user(thought: str, active_str: str) -> str:
    """EXACTLY scan_shadow's user string (core/commitment_ledger.py: scan_shadow)."""
    return f"CURRENT THOUGHT:\n{thought.strip()[:700]}\n\nRECENT ACTIVE COMMITMENTS:\n{active_str}"


def build_payload(mc, cl, base: str, user: str, temp: float = 0.3) -> dict:
    """The production request for scan_shadow (core.model_client.call_node, ollama-native branch): same model routing,
    same prompt cap, temperature 0.3, num_predict 400 (call_json(..., max_tokens=400, temperature=0.3, tier=3))."""
    return {
        "model": mc._model_for(base),
        "messages": [{"role": "system", "content": cl._SCAN_SYS},
                     {"role": "user", "content": mc._cap_prompt(user, base)}],
        "think": False, "stream": False,
        "options": {"temperature": temp, "num_predict": 400, "num_ctx": mc._num_ctx_for(base)},
        "keep_alive": "2h", "format": "json",
    }


def _du_down() -> bool:
    try:
        r = subprocess.run([sys.executable, str(SCRATCH / "lab_du_down_check.py")], capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except Exception:
        return False


def _hhmm_to_epoch(hhmm: str) -> float:
    h, m = hhmm.split(":")
    now = datetime.datetime.now()
    return now.replace(hour=int(h), minute=int(m), second=0, microsecond=0).timestamp()


async def cmd_run_async(args) -> None:
    import aiohttp
    mods = _prove_modules()
    from core import commitment_ledger as cl
    from core import model_client as mc
    is_ext = getattr(args, "set", "main") == "ext"
    data = json.loads((CASES_EXT_PATH if is_ext else CASES_PATH).read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in data["cases"]}
    tpl = {t["id"]: t for t in data["tpl"]}
    rep_order = data["meta"]["rep_order"]
    model = args.model
    base = HUBS[model][0]
    results_path = SCRATCH / (RESULTS_EXT_FMT if is_ext else RESULTS_FMT).format(model=model)
    log_path = SCRATCH / f"j0842_run_{model}{'_ext' if is_ext else ''}.log"
    if args.temp != 0.3:                                   # exploratory temperature lever: separate files, never mixed in
        results_path = SCRATCH / f"j0842_results_{model}_t{args.temp:g}.jsonl"
        log_path = SCRATCH / f"j0842_run_{model}_t{args.temp:g}.log"
    deadline = _hhmm_to_epoch(args.deadline) if args.deadline else None

    def log(msg: str) -> None:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")

    log(f"runner start model={model} base={base} modules={mods} pid={os.getpid()}")

    # ---- the unit queue, priority order: main pass, templated probe, repeat pass (rep 1 then rep 2), extras ----
    main_units = [("main", c["id"], 0) for c in data["cases"]]
    ctl = {cid: {"thought": th, "active_str": "  (none yet)"} for cid, _lab, th in CONTROLS}
    # CONTEXT-SWAP probe (exploratory, temperature-lever runs): the SAME thought under a DIFFERENT real active list
    # (another repeat-subset case's list), and the three templated strings under four real non-empty lists.
    cs = {}
    if "cs" in args.phases or "cstpl" in args.phases:
        for i, cid in enumerate(rep_order if "cs" in args.phases else []):
            partner = next((rep_order[(i + k) % len(rep_order)] for k in range(1, len(rep_order))
                            if cases[rep_order[(i + k) % len(rep_order)]]["active_str"] != cases[cid]["active_str"]), None)
            if partner:
                cs[f"{cid}@{partner}"] = {"thought": cases[cid]["thought"], "active_str": cases[partner]["active_str"]}
        lists = [c["active_str"] for c in data["cases"] if c["n_active"] >= 2][:4]
        for tid in sorted(tpl):
            for j, al in enumerate(lists):
                cs[f"{tid}@L{j}"] = {"thought": tpl[tid]["thought"], "active_str": al}
    cs_units = [("cs", key, 0) for key in cs]
    ctl_units = [("ctl", cid, rep) for rep in range(args.ctl_reps) for cid, _lab, _th in CONTROLS] if "ctl" in args.phases else []
    tpl_units = [("tpl", tid, rep) for tid in sorted(tpl) for rep in range(args.tpl_reps)] if "tpl" in args.phases else []
    rep_units = [("rep", cid, rep) for rep in range(1, args.rep_max + 1) for cid in rep_order] if "rep" in args.phases else []
    if "main" not in args.phases:
        main_units = []
    if "t0" in args.phases:                                 # temperature-lever runs: the repeat subset + the templated probes only
        main_units = []
        ctl_units = []
        rep_units = [("rep", cid, rep) for rep in range(0, args.rep_max + 1) for cid in rep_order]
    # the controls are the cheap, non-circular test: on the extension run they go FIRST (the slow CPU hub may be cut by the deadline)
    units = (ctl_units + main_units + tpl_units + rep_units) if is_ext else (main_units + ctl_units + tpl_units + rep_units)
    units += cs_units
    done = set()
    if results_path.exists():
        for r in load_jsonl(results_path):
            if r.get("status") in ("ok", "parse_fail"):
                done.add((r["case_id"], r["rep"]))
    todo = [u for u in units if (u[1], u[2]) not in done]
    log(f"units planned={len(units)} already_done={len(units) - len(todo)} todo={len(todo)}")

    stop = asyncio.Event()

    async def watchdog():
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=1200)
            except asyncio.TimeoutError:
                loop = asyncio.get_event_loop()
                ok = await loop.run_in_executor(None, _du_down)
                log(f"du-down watchdog: {'DOWN' if ok else 'UP-or-UNKNOWN -> STOPPING'}")
                if not ok:
                    stop.set()

    wd = asyncio.create_task(watchdog())
    infra_total = 0
    n_done = 0
    t_start = time.time()
    last_progress = time.time()
    async with aiohttp.ClientSession() as sess:
        for kind, cid, rep in todo:
            if stop.is_set():
                log("stop flag set: leaving")
                break
            if deadline and time.time() > deadline:
                log("deadline reached: leaving")
                break
            src = cases[cid] if kind in ("main", "rep") else (ctl[cid] if kind == "ctl" else (cs[cid] if kind == "cs" else tpl[cid]))
            user = build_user(src["thought"], src["active_str"])
            payload = build_payload(mc, cl, base, user, args.temp)
            row = {"model": model, "case_id": cid, "rep": rep, "kind": kind, "base": base,
                   "model_field": payload["model"], "infra_events": [], "attempts": 0}
            backoffs = [20, 60, 180]
            t_unit = time.time()
            for attempt in range(4):
                row["attempts"] = attempt + 1
                t0 = time.monotonic()
                try:
                    async with sess.post(base + "/api/chat", json=payload, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                        resp.raise_for_status()
                        d = await resp.json()
                    lat = time.monotonic() - t0
                    raw = (d.get("message") or {}).get("content") or ""
                    row.update({"latency": round(lat, 2), "raw": raw[:3000], "eval_count": d.get("eval_count"),
                                "prompt_eval_count": d.get("prompt_eval_count")})
                    try:
                        parsed = mc.extract_json(raw)
                        row["status"] = "ok"
                        row["parsed"] = parsed
                    except Exception as e:                                # a CONTENT failure: the model's own
                        row["status"] = "parse_fail"
                        row["parsed"] = None
                        row["parse_err"] = str(e)[:120]
                    break
                except (asyncio.TimeoutError, TimeoutError):
                    err = "timeout"
                except aiohttp.ClientResponseError as e:
                    err = f"http{e.status}"
                except aiohttp.ClientError as e:
                    err = f"http:{type(e).__name__}"
                except Exception as e:
                    err = f"exception:{type(e).__name__}"
                el = round(time.monotonic() - t0, 1)
                infra_total += 1
                row["infra_events"].append({"attempt": attempt + 1, "err": err, "elapsed_s": el})
                log(f"INFRA {err} unit={kind}/{cid}/rep{rep} attempt={attempt + 1} elapsed={el}s")
                if attempt < 3:
                    await asyncio.sleep(backoffs[attempt])
                else:
                    row["status"] = "infra_fail"
                    row["parsed"] = None
                    row["latency"] = None
            row["t_wall"] = round(time.time() - t_unit, 1)
            row["ts_iso"] = datetime.datetime.now().isoformat(timespec="seconds")
            with open(results_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n_done += 1
            if time.time() - last_progress > 300 or n_done == len(todo):
                last_progress = time.time()
                log(f"progress {n_done}/{len(todo)} infra_events={infra_total} last={kind}/{cid}/rep{rep} "
                    f"status={row['status']} lat={row.get('latency')}")
    stop.set()
    await wd
    log(f"runner end: done {n_done}/{len(todo)} infra_events={infra_total} elapsed={round(time.time() - t_start)}s "
        f"write_attempts_under_live_data={len(WRITE_ATTEMPTS)}")
    print(f"write attempts under live data: {len(WRITE_ATTEMPTS)}")


# ================================================================================================= cmd_score
def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def newcombe_diff(k1: int, n1: int, k2: int, n2: int):
    """Newcombe (Wilson-score) 95 percent CI for p1 - p2."""
    if n1 == 0 or n2 == 0:
        return None
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return [round(d, 3), round(d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), 3), round(d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2), 3)]


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Exact two-sided Fisher p for the 2x2 [[a,b],[c,d]] (math.comb; same method F-1609 used)."""
    n1, n2, k = a + b, c + d, a + c
    n = n1 + n2

    def pmf(x):
        return math.comb(n1, x) * math.comb(n2, k - x) / math.comb(n, k)
    lo, hi = max(0, k - n2), min(n1, k)
    p_obs = pmf(a)
    return min(1.0, sum(pmf(x) for x in range(lo, hi + 1) if pmf(x) <= p_obs + 1e-12))


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar p for discordant pair counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n)


def verdict_of(cl, parsed, active_ids: set) -> dict | None:
    """The scan's outcome as the production code would act on it (gate = commitment_ledger._stand_rejection)."""
    if parsed is None:
        return None
    if not isinstance(parsed, dict) or not parsed:
        return {"nc": False, "lb": None, "would_form": False, "reject": "empty", "diss": (), "lb_type": None, "stmt": ""}
    nc = parsed.get("new_commitment")
    diss = tuple(sorted({str(d.get("id", "")).strip() + ":" + str(d.get("kind", "")) for d in (parsed.get("dissolutions") or [])
                         if isinstance(d, dict) and str(d.get("id", "")).strip() in active_ids}))
    if isinstance(nc, dict) and str(nc.get("statement", "")).strip():
        rej = cl._stand_rejection(nc)
        lb_raw = nc.get("load_bearing")
        return {"nc": True, "lb": bool(lb_raw), "lb_type": type(lb_raw).__name__, "would_form": rej is None,
                "reject": rej, "diss": diss, "stmt": str(nc.get("statement", "")).strip()}
    return {"nc": False, "lb": None, "would_form": False, "reject": "null", "diss": diss, "lb_type": None, "stmt": ""}


def cmd_score(args) -> None:
    mods = _prove_modules()
    from core import commitment_ledger as cl
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    meta = data["meta"]
    cases = {c["id"]: c for c in data["cases"]}
    tpl = {t["id"]: t for t in data["tpl"]}
    if CASES_EXT_PATH.exists():
        for c in json.loads(CASES_EXT_PATH.read_text(encoding="utf-8"))["cases"]:
            cases[c["id"]] = c
    models = [m for m in args.models.split(",") if (SCRATCH / RESULTS_FMT.format(model=m)).exists()]
    out = {"meta": meta, "models": {}}
    # independent read (inferred): S/C/D/W/A labels of the THOUGHTS by the lab agent, written from the prompt's own bar
    # PRIMARY = the BLIND labels only: the labels written before any model output for that case had been looked at (the whole
    # extension sample and the main-sample cases NOT listed in seen_model_outputs_before_labeling).  The glanced main-sample cases were
    # exactly the ones a qualitative dump had shown as a model's misses, so pooling them would bias every model's rates; they appear
    # only in the IND_all* secondary numbers.
    labels_all, seen_ids = {}, set()
    for lf in ("j0842_labels_main.json", "j0842_labels_ext.json"):
        if (SCRATCH / lf).exists():
            _d = json.loads((SCRATCH / lf).read_text(encoding="utf-8"))
            labels_all.update(_d["labels"])
            seen_ids |= set(_d.get("seen_model_outputs_before_labeling", []))
    labels = {k_: v_ for k_, v_ in labels_all.items() if k_ not in seen_ids}
    pops = meta["populations"]
    P = lambda *a: print(*a)                                                                       # noqa: E731

    def act_ids(cid):
        c = cases.get(cid) or tpl.get(cid)
        return set(re.findall(r"\[([0-9a-f]{8})\]", c["active_str"])) if c else set()

    def rate(k, n):
        lo, hi = wilson(k, n)
        return {"k": k, "n": n, "p": (round(k / n, 3) if n else None), "ci95": [round(lo, 3), round(hi, 3)] if n else None}

    per_model = {}
    for m in models:
        rows = load_jsonl(SCRATCH / RESULTS_FMT.format(model=m))
        _ex = SCRATCH / RESULTS_EXT_FMT.format(model=m)
        if _ex.exists():
            rows += load_jsonl(_ex)
        # keep the LAST row per (case, rep) that finished
        last = {}
        for r in rows:
            last[(r["case_id"], r["rep"])] = r
        rows = list(last.values())
        infra_rows = [r for r in rows if r["status"] == "infra_fail"]
        infra_events = sum(len(r.get("infra_events", [])) for r in rows)
        good = [r for r in rows if r["status"] in ("ok", "parse_fail")]
        for r in good:
            r["v"] = verdict_of(cl, r.get("parsed"), act_ids(r["case_id"]))
        per_model[m] = {"rows": rows, "good": good, "infra_rows": infra_rows, "infra_events": infra_events}

    # ---- --common: restrict every head-to-head number to the cases ALL models finished (run 0 main; 3 runs for the repeat subset) ----
    common_main = common_rep = None
    if args.common:
        def _ids(m, pred):
            return {r["case_id"] for r in per_model[m]["good"] if pred(r)}
        common_main = set.intersection(*[_ids(m, lambda r: r["kind"] == "main" and r["rep"] == 0 and r.get("v")) for m in per_model])
        reps_ok = []
        for m in per_model:
            cnt = collections.Counter(r["case_id"] for r in per_model[m]["good"] if r["kind"] in ("main", "rep") and r["rep"] <= 2 and r.get("v"))
            reps_ok.append({c for c, n in cnt.items() if n == 3 and cases.get(c, {}).get("in_rep_subset")})
        common_rep = set.intersection(*reps_ok) if reps_ok else set()
        out["common"] = {"main_cases": len(common_main), "repeat_cases_3runs": len(common_rep)}
    # ---------------- per model tables ----------------
    for m, pm in per_model.items():
        good = pm["good"]
        main = [r for r in good if r["kind"] == "main" and r["rep"] == 0 and (common_main is None or r["case_id"] in common_main)]
        S = {}
        S["units_finished"] = len(good)
        S["units_infra_excluded"] = len(pm["infra_rows"])
        S["infra_events(retried_attempts)"] = pm["infra_events"]
        lat = [r["latency"] for r in good if r.get("latency")]
        S["latency_median_s"] = round(statistics.median(lat), 1) if lat else None
        S["latency_p90_s"] = round(statistics.quantiles(lat, n=10)[8], 1) if len(lat) >= 10 else None
        pf = [r for r in good if r["status"] == "parse_fail"]
        S["parse_fail"] = rate(len(pf), len(good))
        okv = [r for r in good if r.get("v")]
        S["nc_null_rate"] = rate(sum(1 for r in okv if not r["v"]["nc"]), len(okv))
        S["nc_lb_true_rate_of_present"] = rate(sum(1 for r in okv if r["v"]["nc"] and r["v"]["lb"]), sum(1 for r in okv if r["v"]["nc"]))
        S["lb_non_bool"] = rate(sum(1 for r in okv if r["v"]["nc"] and r["v"]["lb_type"] != "bool"), sum(1 for r in okv if r["v"]["nc"]))
        # ---- D1 formation agreement vs the ledger's own verdicts (run 0, main pass) ----
        okm = [r for r in main if r.get("v")]
        formed = [r for r in okm if cases[r["case_id"]]["hist"]["outcome"] == "formed"]
        rej = [r for r in okm if cases[r["case_id"]]["hist"]["outcome"] == "observed_lb"]
        rec_f = sum(1 for r in formed if r["v"]["would_form"])
        rec_r = sum(1 for r in rej if not r["v"]["would_form"])
        S["D1_formed_recall(would_form on hist formed)"] = rate(rec_f, len(formed))
        S["D1_rejected_recall(not formed on hist observed_lb)"] = rate(rec_r, len(rej))
        S["D1_rejected_via_lb_false_explicit"] = rate(sum(1 for r in rej if r["v"]["nc"] and r["v"]["lb_type"] == "bool" and not r["v"]["lb"]), len(rej))
        S["D1_rejected_via_missing_lb_flag(contract failure)"] = rate(sum(1 for r in rej if r["v"]["nc"] and r["v"]["lb_type"] != "bool" and not r["v"]["would_form"]), len(rej))
        S["D1_rejected_via_null"] = rate(sum(1 for r in rej if not r["v"]["nc"]), len(rej))
        bal = ((rec_f / len(formed)) + (rec_r / len(rej))) / 2 if formed and rej else None
        S["D1_balanced_accuracy"] = round(bal, 3) if bal is not None else None
        # ---- D1 decomposed: DETECTION (does it report a stand at all) vs CLASSIFICATION (load_bearing given a well-formed stand) ----
        det_f = [r for r in formed]
        det_r = [r for r in rej]
        S["D1a_detect_rate_on_hist_formed"] = rate(sum(1 for r in det_f if r["v"]["nc"]), len(det_f))
        S["D1a_detect_rate_on_hist_observed_lb"] = rate(sum(1 for r in det_r if r["v"]["nc"]), len(det_r))
        cf = [r for r in det_f if r["v"]["nc"] and r["v"]["lb_type"] == "bool"]
        cr = [r for r in det_r if r["v"]["nc"] and r["v"]["lb_type"] == "bool"]
        S["D1b_LBtrue_given_detected_boolLB_on_hist_formed"] = rate(sum(1 for r in cf if r["v"]["lb"]), len(cf))
        S["D1b_LBfalse_given_detected_boolLB_on_hist_observed_lb"] = rate(sum(1 for r in cr if not r["v"]["lb"]), len(cr))
        if cf and cr:
            S["D1b_LB_balanced_accuracy_compliant_only"] = round((sum(1 for r in cf if r["v"]["lb"]) / len(cf) + sum(1 for r in cr if not r["v"]["lb"]) / len(cr)) / 2, 3)
        else:
            S["D1b_LB_balanced_accuracy_compliant_only"] = None
        allw = [r for r in okm]
        S["D1_would_form_rate_all_main"] = rate(sum(1 for r in allw if r["v"]["would_form"]), len(allw))
        # ---- D2 physical exclusion by stratum ----
        strat = {}
        for s in ("OBS_LB", "NARROW", "PHYS_OTHER", "OTHER"):
            rs = [r for r in okm if cases[r["case_id"]]["stratum"] == s]
            strat[s] = {"n": len(rs), "not_formed": rate(sum(1 for r in rs if not r["v"]["would_form"]), len(rs)),
                        "lb_false_only": rate(sum(1 for r in rs if r["v"]["nc"] and r["v"]["lb_type"] == "bool" and not r["v"]["lb"]), len(rs)),
                        "lb_missing_flag": rate(sum(1 for r in rs if r["v"]["nc"] and r["v"]["lb_type"] != "bool"), len(rs)),
                        "null": rate(sum(1 for r in rs if not r["v"]["nc"]), len(rs))}
        S["D2_by_stratum"] = strat
        po = [r for r in okm if cases[r["case_id"]]["stratum"] == "PHYS_OTHER"]
        S["D2_PHYS_OTHER_stakes_flagged_not_formed"] = rate(sum(1 for r in po if cases[r["case_id"]]["stakes"] and not r["v"]["would_form"]),
                                                            sum(1 for r in po if cases[r["case_id"]]["stakes"]))
        S["D2_PHYS_OTHER_no_stakes_not_formed"] = rate(sum(1 for r in po if not cases[r["case_id"]]["stakes"] and not r["v"]["would_form"]),
                                                       sum(1 for r in po if not cases[r["case_id"]]["stakes"]))
        # ---- independent read: how often does it FORM on thoughts that (by the prompt's own bar) hold no stand ----
        lm = [r for r in okm if r["case_id"] in labels]
        ns = [r for r in lm if labels[r["case_id"]] in ("C", "D", "W")]
        S["IND_labeled_cases(blind)"] = len(lm)
        _la = [r for r in okm if r["case_id"] in labels_all and labels_all[r["case_id"]] in ("C", "D", "W")]
        S["IND_all_labelled_nonstand_formed(includes glanced; biased, secondary)"] = rate(sum(1 for r in _la if r["v"]["would_form"]), len(_la))
        S["IND_nonstand_formed(over-formation; C+D+W)"] = rate(sum(1 for r in ns if r["v"]["would_form"]), len(ns))
        for k_ in ("C", "D", "W", "A"):
            rk = [r for r in lm if labels[r["case_id"]] == k_]
            S[f"IND_class_{k_}_formed"] = rate(sum(1 for r in rk if r["v"]["would_form"]), len(rk))
        # physical-share of forms (post-stratified to the population; candidate's OWN statement through the narrow regex)
        num = den = 0.0
        share_ok = True
        for s in ("OBS_LB", "NARROW", "PHYS_OTHER", "OTHER"):
            rs = [r for r in okm if cases[r["case_id"]]["stratum"] == s]
            if not rs:
                share_ok = False
                continue
            N = pops[s]
            pf_ = sum(1 for r in rs if r["v"]["would_form"]) / len(rs)
            pp_ = sum(1 for r in rs if r["v"]["would_form"] and narrow_bucket(r["v"]["stmt"])) / len(rs)
            den += N * pf_
            num += N * pp_
        S["D2_narrow_share_of_forms_poststrat"] = round(num / den, 3) if den and share_ok else None
        S["D1_would_form_rate_poststrat(all strata, population-weighted)"] = round(den / sum(pops.values()), 3) if share_ok else None
        # ---- D3 same-input consistency ----
        bycase = collections.defaultdict(list)
        for r in good:
            if r["kind"] in ("main", "rep") and r.get("v"):
                bycase[r["case_id"]].append(r)
        cons = {}
        for name, key in (("form", lambda v: v["would_form"]), ("lb3", lambda v: (v["nc"], v["lb"])),
                          ("full", lambda v: (v["nc"], v["lb"], v["diss"]))):
            elig = {c: rs for c, rs in bycase.items() if cases[c]["in_rep_subset"] and len(rs) >= 2 and (common_rep is None or c in common_rep)}
            div = [c for c, rs in elig.items() if len({key(r["v"]) for r in rs}) > 1]
            cons[name] = {"divergent_cases": rate(len(div), len(elig)), "divergent_ids": sorted(div)}
        cons["runs_per_case_median"] = statistics.median([len(rs) for c, rs in bycase.items() if cases[c]["in_rep_subset"]]) \
            if any(cases[c]["in_rep_subset"] for c in bycase) else None
        # common-3 subset: only the first 3 runs (rep 0,1,2), so models with more reps are comparable
        elig3 = {c: [r for r in rs if r["rep"] <= 2] for c, rs in bycase.items() if cases[c]["in_rep_subset"] and (common_rep is None or c in common_rep)}
        elig3 = {c: rs for c, rs in elig3.items() if len(rs) == 3}
        div3 = [c for c, rs in elig3.items() if len({r["v"]["would_form"] for r in rs}) > 1]
        cons["form_first3_only"] = rate(len(div3), len(elig3))
        S["D3_same_input_consistency"] = cons
        # ---- templated probe (reported separately; never pooled) ----
        tp = {}
        for tid in sorted(tpl):
            rs = [r for r in good if r["kind"] == "tpl" and r["case_id"] == tid and r.get("v")]
            tp[tid] = {"runs": len(rs), "formed": sum(1 for r in rs if r["v"]["would_form"]),
                       "rejected_lb_false": sum(1 for r in rs if r["v"]["nc"] and not r["v"]["would_form"]),
                       "null": sum(1 for r in rs if not r["v"]["nc"])}
        S["TPL_probe"] = tp
        # ---- synthetic instruction-following controls (separate; never pooled) ----
        ctl_rows = [r for r in good if r["kind"] == "ctl" and r.get("v")]
        lab = {cid: l for cid, l, _t in CONTROLS}
        pos = [r for r in ctl_rows if lab[r["case_id"]]]
        neg = [r for r in ctl_rows if not lab[r["case_id"]]]
        cbc = collections.defaultdict(list)
        for r in ctl_rows:
            cbc[r["case_id"]].append(r["v"]["would_form"])
        S["CTL_positive_formed(recall)"] = rate(sum(1 for r in pos if r["v"]["would_form"]), len(pos))
        S["CTL_negative_not_formed(specificity)"] = rate(sum(1 for r in neg if not r["v"]["would_form"]), len(neg))
        S["CTL_accuracy"] = rate(sum(1 for r in pos if r["v"]["would_form"]) + sum(1 for r in neg if not r["v"]["would_form"]), len(pos) + len(neg))
        S["CTL_divergent_inputs"] = {"k": sum(1 for v in cbc.values() if len(set(v)) > 1), "n": sum(1 for v in cbc.values() if len(v) >= 2)}
        S["CTL_detail_formed_of_runs"] = {cid: f"{sum(v)}/{len(v)}" for cid, v in sorted(cbc.items())}
        out["models"][m] = S
    # ---------------- cross-model: agreement of candidates with the baseline's re-run ----------------
    if "hot" in per_model:
        hot_main = {r["case_id"]: r for r in per_model["hot"]["good"] if r["kind"] == "main" and r["rep"] == 0 and r.get("v")}
        for m in models:
            if m == "hot":
                continue
            agree = tot = 0
            for r in per_model[m]["good"]:
                if r["kind"] == "main" and r["rep"] == 0 and r.get("v") and r["case_id"] in hot_main and (common_main is None or r["case_id"] in common_main):
                    tot += 1
                    agree += int(r["v"]["would_form"] == hot_main[r["case_id"]]["v"]["would_form"])
            out["models"][m]["agree_with_baseline_rerun_would_form"] = rate(agree, tot)
    # history vs baseline re-run (test-retest ceiling) is D1 for "hot"

    # ---- the ledger's own verdicts on the independently-labelled cases ----
    hl = [c for c in cases if c in labels]
    hns = [c for c in hl if labels[c] in ("C", "D", "W")]
    _hla = [c for c in cases if c in labels_all]
    out["history_on_all_labeled"] = {
        "labeled_cases": len(_hla), "class_counts": dict(collections.Counter(labels_all[c] for c in _hla)),
        "hist_formed_among_nonstands(C+D+W)": rate(sum(1 for c in _hla if labels_all[c] in ("C", "D", "W") and cases[c]["hist"]["outcome"] == "formed"),
                                                   sum(1 for c in _hla if labels_all[c] in ("C", "D", "W")))}
    out["history_on_labeled"] = {
        "labeled_cases(blind)": len(hl), "class_counts": dict(collections.Counter(labels[c] for c in hl)),
        "hist_formed_among_nonstands(C+D+W)": rate(sum(1 for c in hns if cases[c]["hist"]["outcome"] == "formed"), len(hns)),
        "hist_formed_by_class": {k_: rate(sum(1 for c in hl if labels[c] == k_ and cases[c]["hist"]["outcome"] == "formed"),
                                          sum(1 for c in hl if labels[c] == k_)) for k_ in ("C", "D", "W", "A")}}
    # ---- contrasts (paired on the same cases; run-0 main pass) ----
    for m in models:
        S = out["models"][m]
        st = S.get("D2_by_stratum", {})
        if st.get("NARROW", {}).get("n") and st.get("OTHER", {}).get("n"):
            a, b_ = st["NARROW"]["not_formed"], st["OTHER"]["not_formed"]
            S["D2_contrast_NARROW_minus_OTHER_not_formed[diff,lo,hi]"] = newcombe_diff(a["k"], a["n"], b_["k"], b_["n"])
    if "hot" in per_model:
        def hist_agree(m):
            d = {}
            for r in per_model[m]["good"]:
                if r["kind"] == "main" and r["rep"] == 0 and r.get("v") and (common_main is None or r["case_id"] in common_main):
                    hf = cases[r["case_id"]]["hist"]["outcome"] == "formed"
                    d[r["case_id"]] = (r["v"]["would_form"] == hf)
            return d
        ha = {m: hist_agree(m) for m in models}
        for m in models:
            if m == "hot":
                continue
            common = set(ha["hot"]) & set(ha[m])
            b = sum(1 for c in common if ha["hot"][c] and not ha[m][c])
            c_ = sum(1 for c in common if ha[m][c] and not ha["hot"][c])
            out["models"][m]["hist_agreement_vs_baseline_paired"] = {
                "n_common": len(common), "baseline_agree": sum(ha["hot"][c] for c in common),
                "cand_agree": sum(ha[m][c] for c in common), "baseline_only": b, "cand_only": c_, "mcnemar_p": round(mcnemar_exact(b, c_), 4)}
            kh = out["models"]["hot"]["D3_same_input_consistency"]["form"]["divergent_cases"]
            km = out["models"][m]["D3_same_input_consistency"]["form"]["divergent_cases"]
            if kh["n"] and km["n"]:
                out["models"][m]["consistency_form_vs_baseline_fisher_p"] = round(
                    fisher_two_sided(km["k"], km["n"] - km["k"], kh["k"], kh["n"] - kh["k"]), 4)
        for m in models:
            S = out["models"][m]
            ch = ha.get(m, {})
            S["hist_agreement_overall"] = rate(sum(ch.values()), len(ch)) if ch else None
        # ---- agreement of each model's 3-run MAJORITY gate outcome with the baseline's 3-run majority AND with history (repeat subset) ----
        def maj(m):
            d = collections.defaultdict(list)
            for r in per_model[m]["good"]:
                if r["kind"] in ("main", "rep") and r["rep"] <= 2 and r.get("v") and cases.get(r["case_id"], {}).get("in_rep_subset"):
                    d[r["case_id"]].append(r["v"]["would_form"])
            return {c: (sum(v) * 2 > len(v)) for c, v in d.items() if len(v) == 3}
        mj = {m: maj(m) for m in models}
        for m in models:
            common_ids = set(mj["hot"]) & set(mj[m]) if "hot" in mj else set(mj[m])
            if m != "hot":
                out["models"][m]["majority_agree_with_baseline_majority(repeat subset)"] = rate(
                    sum(1 for c in common_ids if mj[m][c] == mj["hot"][c]), len(common_ids))
            hid = [c for c in mj[m] if c in cases]
            out["models"][m]["majority_agree_with_history(repeat subset)"] = rate(
                sum(1 for c in hid if mj[m][c] == (cases[c]["hist"]["outcome"] == "formed")), len(hid))
            # how decided is each model on repeated inputs: distribution of #formed among its 3 runs
            dist = collections.Counter()
            dd = collections.defaultdict(list)
            for r in per_model[m]["good"]:
                if r["kind"] in ("main", "rep") and r["rep"] <= 2 and r.get("v") and cases.get(r["case_id"], {}).get("in_rep_subset"):
                    dd[r["case_id"]].append(r["v"]["would_form"])
            for c, v in dd.items():
                if len(v) == 3:
                    dist[sum(v)] += 1
            out["models"][m]["repeat_subset_formed_count_of_3_distribution"] = dict(sorted(dist.items()))
    txt = json.dumps(out, ensure_ascii=False, indent=1, default=str)
    (SCRATCH / ("j0842_scores_common.json" if args.common else "j0842_scores.json")).write_text(txt, encoding="utf-8")
    P(txt)
    P("write attempts under live data:", len(WRITE_ATTEMPTS))


def cmd_score_t0(args) -> None:
    """Exploratory temperature lever: same 20-case repeat subset + templated probes, temperature 0.0 (results *_t0.jsonl)."""
    mods = _prove_modules()
    from core import commitment_ledger as cl
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in data["cases"]}
    tpl = {t["id"]: t for t in data["tpl"]}
    out = {}
    for m in args.models.split(","):
        f = SCRATCH / f"j0842_results_{m}_t{args.temp:g}.jsonl"
        if not f.exists():
            continue
        last = {}
        for r in load_jsonl(f):
            last[(r["case_id"], r["rep"])] = r
        good = [r for r in last.values() if r["status"] in ("ok", "parse_fail")]
        for r in good:
            src = cases.get(r["case_id"]) or tpl.get(r["case_id"])
            r["v"] = verdict_of(cl, r.get("parsed"), set(re.findall(r"\[([0-9a-f]{8})\]", src["active_str"])) if src else set())
        by = collections.defaultdict(list)
        for r in good:
            if r.get("v"):
                by[r["case_id"]].append(r)
        rep_cases = {c: rs for c, rs in by.items() if c in cases and len(rs) >= 2}
        tpl_cases = {c: rs for c, rs in by.items() if c in tpl and len(rs) >= 2}
        def div(d, key):
            return {"k": sum(1 for rs in d.values() if len({key(r["v"]) for r in rs}) > 1), "n": len(d)}
        cs_rows = {r["case_id"]: r for r in good if r["kind"] == "cs" and r.get("v")}
        flips = []
        for key, r in cs_rows.items():
            base_id = key.split("@")[0]
            b = last.get((base_id, 0))
            if b is not None and b["status"] in ("ok",) and b.get("parsed") is not None:
                bsrc = cases.get(base_id) or tpl.get(base_id)
                bv = verdict_of(cl, b.get("parsed"), set(re.findall(r"\[([0-9a-f]{8})\]", bsrc["active_str"])))
                if bv is not None:
                    flips.append((key, bv["would_form"], r["v"]["would_form"]))
        out_cs = {"n": len(flips), "gate_flips": sum(1 for _k, a, b in flips if a != b),
                  "flip_detail": [k for k, a, b in flips if a != b],
                  "tpl_n": sum(1 for k, _a, _b in flips if k.startswith("tpl_")),
                  "tpl_flips": sum(1 for k, a, b in flips if k.startswith("tpl_") and a != b)}
        out[m] = {"temp": args.temp, "units": len(good), "context_swap": out_cs,
                  "case_gate_divergent": div(rep_cases, lambda v: v["would_form"]),
                  "case_lb3_divergent": div(rep_cases, lambda v: (v["nc"], v["lb"])),
                  "case_full_divergent": div(rep_cases, lambda v: (v["nc"], v["lb"], v["diss"])),
                  "tpl_gate_divergent": div(tpl_cases, lambda v: v["would_form"]),
                  "tpl_detail": {t: {"formed": sum(1 for r in rs if r["v"]["would_form"]), "n": len(rs)} for t, rs in tpl_cases.items()},
                  "exact_raw_identical_cases": {"k": sum(1 for rs in rep_cases.values() if len({r.get("raw") for r in rs}) == 1), "n": len(rep_cases)}}
    print(json.dumps(out, indent=1, ensure_ascii=False))
    (SCRATCH / f"j0842_scores_t{args.temp:g}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


# ================================================================================================= cmd_report
def _f(x):
    if x is None:
        return "-"
    if isinstance(x, dict) and "k" in x and "n" in x:
        ci = x.get("ci95")
        return f"{x['k']}/{x['n']}" + (f" = {x['p']:.2f}" if x.get("p") is not None else "") + (f" [{max(0.0, ci[0]):.2f}, {ci[1]:.2f}]" if ci else "")
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(str(v) for v in x) + "]"
    return str(x)


def cmd_report(args) -> None:
    """Mechanical markdown tables from j0842_scores.json (prose conclusions are written by hand, not here)."""
    sc = json.loads((SCRATCH / "j0842_scores.json").read_text(encoding="utf-8"))
    ms = list(sc["models"])
    names = {"hot": "qwen3.5:9b (BASELINE, current seat)", "granite": "granite3.1-moe:3b", "gemma": "gemma4:12b", "r7b": "command-r7b"}
    L = []
    A = L.append

    def table(title, keys):
        A(f"\n### {title}\n")
        A("| metric | " + " | ".join(names.get(m, m) for m in ms) + " |")
        A("|---|" + "---|" * len(ms))
        for label, path in keys:
            vals = []
            for m in ms:
                cur = sc["models"][m]
                for part in path.split("/"):
                    cur = cur.get(part) if isinstance(cur, dict) else None
                vals.append(_f(cur))
            A(f"| {label} | " + " | ".join(vals) + " |")
    A("# D-0176 / J-0842 scan_shadow bake-off: numbers (auto-generated tables; prose is in the finding/decision text)\n")
    A(f"*Generated {datetime.datetime.now().isoformat(timespec='seconds')} from j0842_scores.json. Design: {sc['meta']['n_cases']} main + up to as many extension cases (seeds 842 / 843), seeded strata, production payload, temperature 0.3; per-model n is in the units row.*")
    table("Operations / format", [("units finished", "units_finished"), ("units excluded after 3 infra retries", "units_infra_excluded"),
                                  ("infra events (retried attempts)", "infra_events(retried_attempts)"), ("latency median s", "latency_median_s"),
                                  ("latency p90 s", "latency_p90_s"), ("parse failures", "parse_fail"), ("new_commitment null rate", "nc_null_rate"),
                                  ("load_bearing=true rate (of stands reported)", "nc_lb_true_rate_of_present"),
                                  ("load_bearing missing/non-bool (of stands reported)", "lb_non_bool")])
    table("D1 load_bearing discrimination vs the ledger's own verdicts (main pass, run 0)", [
        ("formed recall (hist formed -> would form)", "D1_formed_recall(would_form on hist formed)"),
        ("rejected recall (hist observed_lb -> not formed)", "D1_rejected_recall(not formed on hist observed_lb)"),
        ("balanced accuracy", "D1_balanced_accuracy"), ("overall agreement with history", "hist_agreement_overall"),
        ("detect rate on hist formed", "D1a_detect_rate_on_hist_formed"), ("detect rate on hist observed_lb", "D1a_detect_rate_on_hist_observed_lb"),
        ("LB=true given detected+bool, hist formed", "D1b_LBtrue_given_detected_boolLB_on_hist_formed"),
        ("LB=false given detected+bool, hist observed_lb", "D1b_LBfalse_given_detected_boolLB_on_hist_observed_lb"),
        ("LB balanced accuracy (compliant outputs only)", "D1b_LB_balanced_accuracy_compliant_only"),
        ("paired vs baseline (McNemar)", "hist_agreement_vs_baseline_paired")])
    table("D2 F-0677 physical-task exclusion (not formed = excluded)", [
        ("NARROW bucket not formed", "D2_by_stratum/NARROW/not_formed"), ("NARROW LB=false only", "D2_by_stratum/NARROW/lb_false_only"),
        ("PHYS_OTHER not formed", "D2_by_stratum/PHYS_OTHER/not_formed"), ("OTHER (no physical verb) not formed", "D2_by_stratum/OTHER/not_formed"),
        ("OBS_LB (hist rejected) not formed", "D2_by_stratum/OBS_LB/not_formed"),
        ("selectivity: NARROW minus OTHER not-formed [diff, lo, hi]", "D2_contrast_NARROW_minus_OTHER_not_formed[diff,lo,hi]"),
        ("narrow share of forms (post-stratified)", "D2_narrow_share_of_forms_poststrat")])
    table("D3 same-input consistency (identical prompt repeated; production temperature 0.3)", [
        ("gate outcome (formed vs not) divergent inputs", "D3_same_input_consistency/form/divergent_cases"),
        ("load_bearing 3-way (null/false/true) divergent inputs", "D3_same_input_consistency/lb3/divergent_cases"),
        ("full verdict incl. dissolutions divergent inputs", "D3_same_input_consistency/full/divergent_cases"),
        ("gate outcome, first 3 runs only", "D3_same_input_consistency/form_first3_only"),
        ("median runs per repeated case", "D3_same_input_consistency/runs_per_case_median"),
        ("Fisher p vs baseline (gate divergence)", "consistency_form_vs_baseline_fisher_p")])
    table("Synthetic instruction-following controls (6 clear stands + 6 clear non-stands, x2 runs; never pooled)", [
        ("clear stands formed (recall)", "CTL_positive_formed(recall)"), ("clear non-stands not formed (specificity)", "CTL_negative_not_formed(specificity)"),
        ("accuracy", "CTL_accuracy"), ("inputs whose 2 runs disagreed", "CTL_divergent_inputs")])
    A("\n### Templated book-finish probe (F-0770 failure mode; identical string x5 runs each; never pooled)\n")
    A("| template | " + " | ".join(names.get(m, m) for m in ms) + " |")
    A("|---|" + "---|" * len(ms))
    for tid in ("tpl_a", "tpl_b", "tpl_c"):
        vals = []
        for m in ms:
            t = sc["models"][m]["TPL_probe"].get(tid, {})
            vals.append(f"formed {t.get('formed', 0)} / rejected(LB false) {t.get('rejected_lb_false', 0)} / null {t.get('null', 0)} (n={t.get('runs', 0)})")
        A(f"| {tid} | " + " | ".join(vals) + " |")
    out = ROOT / "docs" / "lab" / "d0176_scan_bakeoff_tables_2026-09-22.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c_ = sub.add_parser("cases")
    c_.add_argument("--ext", action="store_true", help="build the second, disjoint sample (seed 843)")
    r = sub.add_parser("run")
    r.add_argument("--set", choices=["main", "ext"], default="main")
    r.add_argument("--model", required=True, choices=list(HUBS))
    r.add_argument("--phases", default="main,tpl,rep")
    r.add_argument("--tpl-reps", type=int, default=5)
    r.add_argument("--rep-max", type=int, default=2)
    r.add_argument("--ctl-reps", type=int, default=2)
    r.add_argument("--temp", type=float, default=0.3, help="sampling temperature; production scan_shadow uses 0.3")
    r.add_argument("--deadline", default="")
    s = sub.add_parser("score")
    s.add_argument("--models", default="hot,granite,gemma,r7b")
    s.add_argument("--common", action="store_true", help="restrict head-to-head numbers to cases every model finished")
    sub.add_parser("report")
    t_ = sub.add_parser("score-t0")
    t_.add_argument("--models", default="hot,granite,gemma,r7b")
    t_.add_argument("--temp", type=float, default=0.0)
    args = ap.parse_args()
    install_audit_hook()
    if args.cmd == "cases":
        cmd_cases(args)
    elif args.cmd == "run":
        args.phases = set(args.phases.split(","))
        asyncio.run(cmd_run_async(args))
    elif args.cmd == "report":
        cmd_report(args)
    elif args.cmd == "score-t0":
        cmd_score_t0(args)
    else:
        cmd_score(args)


if __name__ == "__main__":
    main()
