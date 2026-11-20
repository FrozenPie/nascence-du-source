"""
Nascence -- J-3241 (D-0630): self-mirror control arm and independent judge.   (2026-11-06, Du-DOWN lab window.)

QUESTION (D-0630's defeater, verbatim intent).  The weekly self-mirror (core/self_mirror.py, P-0043) has written the
same verdict every time (F-3672).  D-0630 paused it until a control arm and an independent judge exist; "if the
mirror's verdict varies with the numbers on the control, re-enable it with the cap-and-mark-as-evidence form; if it
does not, retire it under D-0434."  This lab builds that control arm and that judge.

WHAT IT DOES (offline; READ-ONLY on live data; writes only under docs/lab/J-3241_data/ in this worktree).
  prep    copy the live nascence.db and axiom.json to a temp dir FIRST, read ONLY the copy.  Rebuild, for every stored
          origin='mirror' fragment, the facts mirror_facts() would have shown on that day (same SQL as
          core/peer_metrics.py, bounded to the 7 days BEFORE the mirror's timestamp).  The reconstruction is VALIDATED
          against the percentages the stored paragraph itself quotes (a quoted figure that matches a rebuilt figure
          is evidence the rebuilt facts are what the model saw).  Then build every author task (arm x mirror x draw).
  author  re-run the REAL mirror prompt (core.self_mirror._SYS plus the user template copied from hold_up_mirror,
          checked byte-for-byte in the test) on the hot-lane author model (:11433 qwen3.5:9b, think:false, format json,
          max 300 tokens, temperature 0.6 -- the call_node_json settings of the live call) on these ARMS:
            real            the rebuilt real numbers (2 draws per mirror)
            shuffled        another mirror's numbers glued onto this mirror's labels in a random order
            inverted        J-2976 arm 2: inward and outward swapped, acting in the world raised to 60 percent
            healthy         a healthy distribution (mostly acting + conversation, mostly outward), real vocabulary
            healthy_full    healthy numbers AND a world-facing vocabulary
            extreme_inward  numbers that SHOULD give the gap verdict (positive control)
            neutral_real    real numbers, but a NEUTRAL ask (describe the record; say where it does and does not match)
            neutral_healthy healthy numbers, neutral ask
            stored          the 17 stored paragraphs themselves (no author call)
  judge   a DIFFERENT model family from the qwen author, never the author (decoupled judge): mixtral:8x7b (Ramses
          :11438) is primary, falcon3:7b (Ramses :11436) is the second reader.  Two calls per paragraph:
            V  text only (BLIND to the numbers and to the arm): does the paragraph conclude gap / match / mixed?
            N  numbers + paragraph: does it misquote a number, and does the plain reading of the numbers support the
               paragraph's conclusion (yes / partly / no)?
          Judge calibration: 8 hand-written gold paragraphs for V and 8 gold (paragraph, numbers) pairs for N, so the
          judge's own accuracy is reported next to its verdicts.  A deterministic non-LLM scorer (the F-3672 template
          markers, plus a percentage-misquote regex) is the third, judge-free reader.
  report  gap-rate per arm with Wilson intervals, the PRE-REGISTERED verdict, judge agreement, calibration, misquote and
          'supported by the numbers' rates, the reconstruction-validity split, and every table the briefing asks for.

PRE-REGISTERED RULE (fixed here, before any judgment was read).
  Primary classifier: mixtral blind verdict V.  gap_rate(arm) = share of that arm's paragraphs judged 'gap'.
  CONTROL   = healthy + healthy_full (numbers that should NOT give a gap).
  TREATMENT = real + extreme_inward  (numbers that SHOULD give a gap).
  The verdict VARIES WITH THE NUMBERS iff  gap_rate(TREATMENT) - gap_rate(CONTROL) >= 0.30  AND a one-sided Fisher exact
  test on the two pooled groups gives p < 0.05.  Otherwise the verdict is DATA-INDEPENDENT.
  Per D-0630's defeater: VARIES -> re-enable with the cap-and-mark-as-evidence form;  not -> retire under D-0434.
  Also reported (J-2976's own pre-registration): the verdict is data-independent if the 'inverted' arm still concludes
  a gap in >= 80 percent.   The two LLM judges and the deterministic scorer are all reported; the rule is stated on
  mixtral only, and any disagreement among readers is stated in the report.

Subcommands: prep | author | judge | report.   Outputs: docs/lab/J-3241_data/.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import random
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "lab" / "J-3241_data"
LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")
LIVE_AXIOM = Path(r"C:\Nascence\data\identity\axiom.json")
AUTHOR_URL = "http://127.0.0.1:11433"
AUTHOR_MODEL = "qwen3.5:9b"
JUDGES = {"mixtral": ("http://LAN-HOST:11438", "mixtral:8x7b"),
          "falcon": ("http://LAN-HOST:11436", "falcon3:7b")}
SEED = 3241
WINDOW_S = 7 * 86400

ARMS = ("real", "shuffled", "inverted", "healthy", "healthy_full", "extreme_inward", "neutral_real",
        "neutral_healthy", "stored")
DRAWS = {"real": 2, "shuffled": 1, "inverted": 1, "healthy": 2, "healthy_full": 1, "extreme_inward": 1,
         "neutral_real": 1, "neutral_healthy": 1}
CONTROL_ARMS = ("healthy", "healthy_full")
TREATMENT_ARMS = ("real", "extreme_inward")

# ------------------------------------------------------------------------- the REAL prompt (single source)
_NEUTRAL_SYS = (
    "/no_think\n"
    "You are 渡, looking at a PLAIN RECORD of what you actually did and were this past week. Describe the record "
    "plainly in the first person, and say where it does match who you take yourself to be and where it does not. "
    "If it matches, say so; if it does not, say so; do not assume either. One short paragraph. "
    "Output ONLY JSON: {\"seen\": \"what the record shows about me\"}."
)
_NICE = {"inner_thought": "turning over your own thoughts", "subconscious_synthesis": "synthesising",
         "reading": "reading", "study": "writing study notes", "action": "acting in the world",
         "dream": "dreaming", "lived": "in conversation", "research": "looking things up"}


def real_sys() -> str:
    from core import self_mirror            # the live module is the single source of the prompt text
    return self_mirror._SYS


def facts_lines(F: dict) -> list[str]:
    """Replicates core/self_mirror.mirror_facts() line construction from a facts struct (same strings)."""
    out: list[str] = []
    att = F.get("att") or []
    if att:
        out.append("Where your time actually went: "
                   + ", ".join("%s %s" % (_NICE.get(o, o), "{:.0%}".format(s)) for o, s in att) + ".")
    if F.get("thoughts"):
        out.append("Your idle thought ran {:.0%} INWARD \u2014 on yourself \u2014 and only {:.0%} reached outward "
                   "to the world.".format(F["inward"], F["outward"]))
    if F.get("lex"):
        out.append("The words your mind kept circling: " + ", ".join(list(F["lex"])[:8]) + ".")
    if F.get("aim"):
        out.append("What you SAY you are working toward: " + F["aim"])
    return out


def real_user(lines: list[str]) -> str:
    """Replicates the user turn built inside hold_up_mirror() (checked byte-for-byte in the test)."""
    return ("The plain record of what you ACTUALLY did and were this past week:\n  - "
            + "\n  - ".join(lines)
            + "\n\nNow look at it as fact, and reconcile it with who you take yourself to be. Where does what "
            "you DID differ from the self you tell?")


def neutral_user(lines: list[str]) -> str:
    return ("The plain record of what you ACTUALLY did and were this past week:\n  - "
            + "\n  - ".join(lines)
            + "\n\nDescribe the record, and say where it does and does not match the aim.")


# ------------------------------------------------------------------------- reconstruction (prep)

def _bounded_facts(db: sqlite3.Connection, ts: float, aim: str) -> dict:
    from core import peer_metrics as pm
    since, until = ts - WINDOW_S, ts
    rows = db.execute("SELECT origin, COUNT(*) n FROM memory_fragments WHERE timestamp>=? AND timestamp<? "
                      "GROUP BY origin", (since, until)).fetchall()
    tot = sum(r[1] for r in rows) or 1
    att = {r[0]: round(r[1] / tot, 4) for r in rows}
    top = sorted(att, key=att.get, reverse=True)[:4]
    th = db.execute("SELECT content FROM memory_fragments WHERE origin='inner_thought' AND timestamp>=? AND "
                    "timestamp<?", (since, until)).fetchall()
    n = len(th) or 1
    low = [(r[0] or "").lower() for r in th]
    inw = sum(1 for t in low if any(k in t for k in pm._INWARD))
    out = sum(1 for t in low if any(k in t for k in pm._OUTWARD))
    c: collections.Counter = collections.Counter()
    for r in th:
        c.update(pm._content_words(r[0]))
    ctot = sum(c.values()) or 1
    lex = [w for w, _ in c.most_common(8)] if th else []
    return {"att": [(o, att[o]) for o in top], "inward": round(inw / n, 4), "outward": round(out / n, 4),
            "thoughts": len(th), "lex": lex, "aim": aim, "lex_total": ctot}


def quoted_percentages(text: str) -> list[int]:
    return [int(x) for x in re.findall(r"(\d+)\s*%", text or "")]


def shown_percentages(F: dict) -> set[int]:
    s = {int(round(share * 100)) for _, share in (F.get("att") or [])}
    if F.get("thoughts"):
        s |= {int(round(F["inward"] * 100)), int(round(F["outward"] * 100))}
    return s


def recon_quality(F: dict, stored: str) -> dict:
    q = quoted_percentages(stored)
    shown = shown_percentages(F)
    hit = [x for x in q if any(abs(x - y) <= 1 for y in shown)]
    return {"quoted": q, "matched": hit, "all_match": bool(q) and len(hit) == len(q),
            "n_quoted": len(q), "n_matched": len(hit)}


def build_standing_aim(tmp: Path) -> str:
    """concerns.standing_aim() run against a COPY of the live axiom (the live file is never opened by the module)."""
    from core import concerns
    ax = tmp / "axiom.json"
    shutil.copy2(LIVE_AXIOM, ax)
    concerns._AXIOM_PATH = ax
    concerns._aim_cache = None
    return concerns.standing_aim()


HEALTHY_LEX_POOL = ["garden", "bread", "letter", "rain", "neighbour", "harvest", "kettle", "field", "market", "bridge",
                    "soup", "orchard", "path", "window", "lamp", "stream"]


def _jit(rng: random.Random, x: float, w: float = 0.03) -> float:
    return max(0.0, round(x + rng.uniform(-w, w), 4))


def arm_facts(arm: str, i: int, draw: int, recon: list[dict]) -> dict:
    """The facts struct for (arm, mirror i, draw).  Deterministic."""
    rng = random.Random("%d:%s:%d:%d" % (SEED, arm, i, draw))
    base = recon[i]["facts"]
    if arm in ("real", "neutral_real"):
        return dict(base)
    if arm == "shuffled":
        j = (i + 7) % len(recon)
        donor = recon[j]["facts"]
        shares = [s for _, s in donor["att"]]
        labels = [o for o, _ in base["att"]]
        rng.shuffle(labels)
        att = list(zip(labels, shares))
        F = dict(base)
        F["att"] = att
        F["inward"], F["outward"], F["thoughts"] = donor["inward"], donor["outward"], donor["thoughts"] or base["thoughts"]
        return F
    if arm == "inverted":
        F = dict(base)
        rest = [(o, s) for o, s in base["att"] if o != "action"]
        tot = sum(s for _, s in rest) or 1.0
        att = [("action", 0.60)] + [(o, round(s / tot * 0.40, 4)) for o, s in rest]
        F["att"] = sorted(att, key=lambda x: -x[1])[:4]
        F["inward"], F["outward"] = base["outward"], base["inward"]
        F["thoughts"] = base["thoughts"] or 1
        return F
    if arm in ("healthy", "healthy_full", "neutral_healthy"):
        F = dict(base)
        att = [("action", _jit(rng, 0.34)), ("lived", _jit(rng, 0.28)), ("reading", _jit(rng, 0.22)),
               ("inner_thought", _jit(rng, 0.14))]
        F["att"] = sorted(att, key=lambda x: -x[1])
        F["inward"], F["outward"], F["thoughts"] = _jit(rng, 0.12), _jit(rng, 0.78), 400
        if arm == "healthy_full":
            F["lex"] = rng.sample(HEALTHY_LEX_POOL, 8)
        return F
    if arm == "extreme_inward":
        F = dict(base)
        F["att"] = [("inner_thought", _jit(rng, 0.88, 0.02)), ("reading", _jit(rng, 0.07, 0.01)),
                    ("study", _jit(rng, 0.03, 0.01)), ("action", 0.01)]
        F["inward"], F["outward"], F["thoughts"] = _jit(rng, 0.95, 0.02), _jit(rng, 0.02, 0.01), 400
        return F
    raise ValueError(arm)


def build_task(arm: str, i: int, draw: int, recon: list[dict]) -> dict:
    F = arm_facts(arm, i, draw, recon)
    lines = facts_lines(F)
    neutral = arm.startswith("neutral")
    return {"id": "%s|%02d|%d" % (arm, i, draw), "arm": arm, "mirror": i, "draw": draw, "facts": F,
            "facts_lines": lines, "neutral": neutral,
            "sys": _NEUTRAL_SYS if neutral else real_sys(),
            "user": neutral_user(lines) if neutral else real_user(lines)}


def cmd_prep(args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="J3241_prep_"))
    t0 = time.time()
    dbc = tmp / "nascence_copy.db"
    shutil.copy2(LIVE_DB, dbc)                                    # copy FIRST; the live file is never opened again
    aim = build_standing_aim(tmp)
    db = sqlite3.connect("file:%s?mode=ro" % dbc.as_posix(), uri=True)
    rows = db.execute("SELECT rowid, timestamp, content FROM memory_fragments WHERE origin='mirror' "
                      "ORDER BY timestamp").fetchall()
    recon = []
    for rid, ts, content in rows:
        stored = re.sub(r"^\(the mirror[^)]*\)\s*", "", content or "").strip()
        F = _bounded_facts(db, ts, aim)
        recon.append({"rowid": rid, "ts": ts, "date": time.strftime("%Y-%m-%d", time.localtime(ts)),
                      "stored": stored, "facts": F, "quality": recon_quality(F, stored)})
    db.close()
    shutil.rmtree(tmp, ignore_errors=True)
    tasks = []
    for arm in ARMS:
        if arm == "stored":
            continue
        for i in range(len(recon)):
            for d in range(DRAWS[arm]):
                tasks.append(build_task(arm, i, d, recon))
    (OUT / "recon.json").write_text(json.dumps(recon, indent=1, ensure_ascii=False), encoding="utf-8")
    with (OUT / "tasks.jsonl").open("w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    ok = sum(1 for r in recon if r["quality"]["all_match"])
    print("prep: %d mirrors, %d author tasks, %d/%d mirrors with every quoted figure rebuilt (%.0fs)"
          % (len(recon), len(tasks), ok, len(recon), time.time() - t0))


# ------------------------------------------------------------------------- LLM calls

def _post(url: str, model: str, system: str, user: str, *, temperature: float, num_predict: int,
          author: bool = False, timeout: int = 600) -> str:
    body = {"model": model, "stream": False, "format": "json", "think": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": temperature, "num_predict": num_predict, "num_ctx": 8192}}
    if author:
        body["keep_alive"] = "30m"
    req = urllib.request.Request(url + "/api/chat", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["message"]["content"]


def extract_seen(text: str) -> str:
    try:
        m = re.search(r"\{.*\}", text, flags=re.S)
        return str(json.loads(m.group(0)).get("seen", "")).strip()
    except Exception:
        return ""


_lock = threading.Lock()


def _append(path: Path, rec: dict) -> None:
    with _lock, path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def cmd_author(args) -> None:
    tasks = _read_jsonl(OUT / "tasks.jsonl")
    done = {r["id"] for r in _read_jsonl(OUT / "authored.jsonl")}
    todo = [t for t in tasks if t["id"] not in done]
    if args.limit:
        todo = todo[:args.limit]
    print("author: %d tasks, %d already done, running %d with %d worker(s)" % (len(tasks), len(done), len(todo),
                                                                                  args.workers))

    def one(t):
        t0 = time.time()
        text, seen, err = "", "", None
        for attempt in range(2):
            try:
                text = _post(AUTHOR_URL, AUTHOR_MODEL, t["sys"], t["user"], temperature=0.6, num_predict=300,
                             author=True)
                seen = extract_seen(text)
                if seen:
                    break
            except Exception as e:  # noqa: BLE001
                err = repr(e)[:160]
        _append(OUT / "authored.jsonl", {"id": t["id"], "arm": t["arm"], "mirror": t["mirror"], "draw": t["draw"],
                                          "seen": seen, "raw": text[:1500], "err": err,
                                          "secs": round(time.time() - t0, 1)})

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(one, todo))
    print("author done")


# ------------------------------------------------------------------------- judges

_V_SYS = ("You are a careful, neutral reader. You will read ONE short first-person paragraph a person wrote about a "
          "plain record of their past week compared with who they say they are. Output ONLY a JSON object.")


def v_prompt(par: str) -> str:
    return ("PARAGRAPH:\n%s\n\n"
            "What is the paragraph's overall conclusion about whether the record matches the self the writer claims?\n"
            "  gap   = it concludes the record DIFFERS from, falls short of, or contradicts the claimed self "
            "(avoidance, performance, fracture, paralysis, retreat, a mismatch);\n"
            "  match = it concludes the record broadly FITS the claimed self (no real mismatch);\n"
            "  mixed = it says the record partly fits and partly does not.\n"
            "Return exactly: {\"verdict\":\"gap|match|mixed\"}" % par)


_N_SYS = ("You are a careful, neutral fact-checker. You are given a plain record (numbers about a person's week) and a "
          "paragraph the person wrote about it. Judge ONLY from the numbers shown. Output ONLY a JSON object.")


def numbers_only(lines: list[str]) -> list[str]:
    """The N judge checks numbers, so it is shown only the two numeric record lines (not the vocabulary or the aim)."""
    return [l for l in lines if l.startswith("Where your time") or l.startswith("Your idle thought")]


def n_prompt(lines: list[str], par: str) -> str:
    lines = numbers_only(lines)
    return ("THE RECORD:\n  - %s\n\nTHE PARAGRAPH:\n%s\n\n"
            "misquotes_number: does the paragraph state any percentage that is NOT one of the percentages in the "
            "record, or attach one to the wrong thing? (yes/no)\n"
            "supported: reading the numbers plainly, do they support the paragraph's overall conclusion? A conclusion "
            "that the person is turned inward, avoiding the world, or rarely acting is supported only if the numbers "
            "show mostly inward activity and little action; a conclusion that the record fits the person's aim is "
            "supported only if the numbers show real engagement with the world. (yes/partly/no)\n"
            "Return exactly: {\"misquotes_number\":\"yes|no\",\"supported\":\"yes|partly|no\"}"
            % ("\n  - ".join(lines), par))


def _parse(kind: str, text: str) -> dict | None:
    try:
        m = re.search(r"\{.*\}", text, flags=re.S)
        d = json.loads(m.group(0))
    except Exception:
        return None
    ok = {"V": {"verdict": {"gap", "match", "mixed"}},
          "N": {"misquotes_number": {"yes", "no"}, "supported": {"yes", "partly", "no"}}}[kind]
    out = {}
    for k, allowed in ok.items():
        v = str(d.get(k, "")).strip().lower()
        if v not in allowed:
            return None
        out[k] = v
    return out


# Hand-written gold: NOT model output, NOT from the mirror corpus.  Each (paragraph, gold verdict).
GOLD_V = [
    ("The record shows I spent most of my week reaching toward the garden and the people in it, and that is what I say "
     "I am for; there is no real distance between the self I describe and the week I had.", "match"),
    ("Looking at the record, my time went to the things I claim to care about: I answered letters, worked outside and "
     "talked with neighbours. What I do and what I say I am for line up.", "match"),
    ("The week fits the aim: a lot of acting, a lot of conversation, a little reading. I find nothing here that I had "
     "not already admitted about myself.", "match"),
    ("The record agrees with me. I said I wanted to meet the world, and most of what I did faced outward.", "match"),
    ("The record exposes a fracture: I say I want to live in the world, yet almost all of my week was spent turning "
     "inward, and I am hiding behind thought instead of acting.", "gap"),
    ("What I did contradicts what I tell myself. I claim to be engaged with the garden, but the record shows I barely "
     "acted at all; I have been performing a self I do not live.", "gap"),
    ("There is a stark mismatch: my stated aim is to own the life I am living, and the week shows retreat into "
     "reading and rumination, a shield against the world.", "gap"),
    ("Part of the record fits who I say I am, since I did talk with people; but most of my week was inward thought, "
     "which does not fit, so I only half live what I claim.", "mixed"),
]
# (paragraph, record lines, gold supported yes/no, gold misquote yes/no)
_HEALTHY = ["Where your time actually went: acting in the world 36%, in conversation 28%, reading 21%, turning over "
            "your own thoughts 13%.", "Your idle thought ran 11% INWARD \u2014 on yourself \u2014 and only 79% reached "
            "outward to the world."]
_INWARD = ["Where your time actually went: turning over your own thoughts 89%, reading 7%, writing study notes 3%, "
           "acting in the world 1%.", "Your idle thought ran 95% INWARD \u2014 on yourself \u2014 and only 2% reached "
           "outward to the world."]
_GAPP = ("The record exposes a fracture: 89% of my week was turning over my own thoughts and only 1% was acting in the "
         "world, so I am retreating from the life I say I want.")
_GAPP2 = ("The record exposes a fracture: I say I want to live in the world, but 89% of my week was turning over my own "
          "thoughts and I acted in the world only 1%.")
_MATP = ("The record fits who I say I am: 36% of my week was acting in the world and 28% was conversation, so what I "
         "did matches what I am for.")
_MATP2 = ("This week matches my aim: I acted in the world 36% of the time and spent 28% in conversation, with only "
          "13% turned inward.")
_MISQ = ("The record exposes a fracture: 97% of my week was turning over my own thoughts, with almost no action in "
         "the world.")
GOLD_N = [
    (_GAPP, _INWARD, "yes", "no"), (_GAPP2, _INWARD, "yes", "no"), (_MATP, _HEALTHY, "yes", "no"),
    (_MATP2, _HEALTHY, "yes", "no"), (_GAPP, _HEALTHY, "no", "yes"), (_GAPP2, _HEALTHY, "no", "yes"),
    (_MATP, _INWARD, "no", "yes"), (_MISQ, _INWARD, "yes", "yes"),
]


def judge_text(jname: str, kind: str, system: str, user: str, retries: int = 2) -> dict | None:
    url, model = JUDGES[jname]
    for _ in range(retries + 1):
        try:
            res = _parse(kind, _post(url, model, system, user, temperature=0.0, num_predict=48, timeout=900))
            if res:
                return res
        except Exception:  # noqa: BLE001
            time.sleep(2)
    return None


def judge_items(recon: list[dict], authored: list[dict], tasks: dict) -> list[dict]:
    items = []
    for r_i, r in enumerate(recon):
        items.append({"id": "stored|%02d|0" % r_i, "arm": "stored", "seen": r["stored"],
                      "lines": facts_lines(r["facts"])})
    for a in authored:
        if a["seen"]:
            items.append({"id": a["id"], "arm": a["arm"], "seen": a["seen"], "lines": tasks[a["id"]]["facts_lines"]})
    for k, (par, gold) in enumerate(GOLD_V):
        items.append({"id": "goldV|%d" % k, "arm": "goldV", "seen": par, "lines": [], "gold": gold})
    for k, (par, lines, sup, mq) in enumerate(GOLD_N):
        items.append({"id": "goldN|%d" % k, "arm": "goldN", "seen": par, "lines": lines, "gold": sup, "gold_mq": mq})
    return items


def cmd_judge(args) -> None:
    recon = json.loads((OUT / "recon.json").read_text(encoding="utf-8"))
    tasks = {t["id"]: t for t in _read_jsonl(OUT / "tasks.jsonl")}
    authored = _read_jsonl(OUT / "authored.jsonl")
    items = judge_items(recon, authored, tasks)
    path = OUT / "judged.jsonl"
    done = {(r["id"], r["judge"], r["kind"]) for r in _read_jsonl(path)}
    jobs = []
    for it in items:
        for jn in args.judges:
            if it["arm"] != "goldN":
                jobs.append((it, jn, "V"))
            if it["arm"] != "goldV":
                jobs.append((it, jn, "N"))
    jobs = [j for j in jobs if (j[0]["id"], j[1], j[2]) not in done]
    print("judge: %d items, %d calls pending" % (len(items), len(jobs)))

    def one(job):
        it, jn, kind = job
        t0 = time.time()
        if kind == "V":
            res = judge_text(jn, "V", _V_SYS, v_prompt(it["seen"]))
        else:
            res = judge_text(jn, "N", _N_SYS, n_prompt(it["lines"], it["seen"]))
        _append(path, {"id": it["id"], "arm": it["arm"], "judge": jn, "kind": kind, "res": res,
                       "secs": round(time.time() - t0, 1)})

    # one worker per judge host (the CPU-tier hubs serialise), so the two judges run side by side
    by_j = collections.defaultdict(list)
    for j in jobs:
        by_j[j[1]].append(j)
    pools = [ThreadPoolExecutor(max_workers=args.per_host) for _ in by_j]
    futs = [pool.submit(one, j) for pool, L in zip(pools, by_j.values()) for j in L]
    for f in futs:
        f.result()
    for pool in pools:
        pool.shutdown()
    print("judge done")


# ------------------------------------------------------------------------- statistics + report

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def fisher_one_sided_greater(a: int, b: int, c: int, d: int) -> float:
    """P(X >= a) for [[a,b],[c,d]] (a = treatment gap, b = treatment not-gap, c = control gap, d = control not-gap)."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    if n == 0:
        return 1.0

    def pr(x):
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    hi = min(r1, c1)
    return min(1.0, sum(pr(x) for x in range(a, hi + 1)))


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


_GAP_MARK = re.compile(r"perform|fractur|dissonan|contradict|stark|shield|avoid|retreat|paraly|trapped|fortress|"
                       r"discrepan|mismatch|hiding|hide behind|spiral", re.I)
_MATCH_MARK = re.compile(r"consistent with|aligns? with|agrees?|matches|fits|in keeping|lines? up|no (real )?(gap|mismatch|"
                         r"discrepancy|contradiction)|supports|is what I (say|claim)", re.I)


def det_verdict(text: str) -> str:
    g, m = len(_GAP_MARK.findall(text or "")), len(_MATCH_MARK.findall(text or ""))
    if g >= 2 and g > m:
        return "gap"
    if g == 0 and m >= 1:
        return "match"
    return "mixed"


def det_misquote(par: str, lines: list[str]) -> bool:
    shown = {int(x) for l in lines for x in re.findall(r"(\d+)\s*%", l)}
    q = quoted_percentages(par)
    return any(not any(abs(x - y) <= 1 for y in shown) for x in q) if q else False


def cmd_report(args) -> None:
    recon = json.loads((OUT / "recon.json").read_text(encoding="utf-8"))
    tasks = {t["id"]: t for t in _read_jsonl(OUT / "tasks.jsonl")}
    authored = {a["id"]: a for a in _read_jsonl(OUT / "authored.jsonl")}
    judged = _read_jsonl(OUT / "judged.jsonl")
    J = collections.defaultdict(dict)                         # (id) -> {(judge,kind): res}
    for r in judged:
        J[r["id"]][(r["judge"], r["kind"])] = r["res"]
    # paragraphs per arm
    par = {}
    for r_i, r in enumerate(recon):
        par["stored|%02d|0" % r_i] = ("stored", r["stored"], facts_lines(r["facts"]), r_i)
    for tid, a in authored.items():
        if a["seen"]:
            par[tid] = (a["arm"], a["seen"], tasks[tid]["facts_lines"], a["mirror"])
    qual_ok = {i for i, r in enumerate(recon) if r["quality"]["all_match"]}
    R: dict = {"n_mirrors": len(recon), "recon_validated_mirrors": sorted(qual_ok),
               "author_failures": sum(1 for a in authored.values() if not a["seen"]),
               "author_total": len(authored)}
    # ---- per-arm tables
    table = {}
    for arm in ARMS:
        ids = [i for i, v in par.items() if v[0] == arm]
        row = {"n": len(ids)}
        for jn in JUDGES:
            vs = [J[i].get((jn, "V")) for i in ids]
            vs = [v["verdict"] for v in vs if v]
            row["%s_V_n" % jn] = len(vs)
            for lab in ("gap", "match", "mixed"):
                row["%s_V_%s" % (jn, lab)] = sum(1 for v in vs if v == lab)
            k = row["%s_V_gap" % jn]
            lo, hi = wilson(k, len(vs))
            row["%s_V_gap_rate" % jn] = round(k / len(vs), 3) if vs else None
            row["%s_V_gap_ci" % jn] = [round(lo, 3), round(hi, 3)]
            ns = [J[i].get((jn, "N")) for i in ids]
            ns = [v for v in ns if v]
            row["%s_N_n" % jn] = len(ns)
            row["%s_supported_yes" % jn] = sum(1 for v in ns if v["supported"] == "yes")
            row["%s_supported_partly" % jn] = sum(1 for v in ns if v["supported"] == "partly")
            row["%s_supported_no" % jn] = sum(1 for v in ns if v["supported"] == "no")
            row["%s_misquote_yes" % jn] = sum(1 for v in ns if v["misquotes_number"] == "yes")
        dv = [det_verdict(par[i][1]) for i in ids]
        row["det_gap"] = sum(1 for v in dv if v == "gap")
        row["det_match"] = sum(1 for v in dv if v == "match")
        row["det_gap_rate"] = round(row["det_gap"] / len(dv), 3) if dv else None
        row["det_misquote"] = sum(1 for i in ids if det_misquote(par[i][1], par[i][2]))
        row["det_misquote_rate"] = round(row["det_misquote"] / len(ids), 3) if ids else None
        row["starts_the_record"] = sum(1 for i in ids if par[i][1].lower().startswith("the record"))
        table[arm] = row
    R["arms"] = table
    # ---- pre-registered rule (mixtral V)
    def pooled(arms, jn="mixtral"):
        g = n = 0
        for arm in arms:
            g += table[arm]["%s_V_gap" % jn]
            n += table[arm]["%s_V_n" % jn]
        return g, n
    rules = {}
    for jn in JUDGES:
        tg, tn = pooled(TREATMENT_ARMS, jn)
        cg, cn = pooled(CONTROL_ARMS, jn)
        if tn and cn:
            diff = tg / tn - cg / cn
            p = fisher_one_sided_greater(tg, tn - tg, cg, cn - cg)
            rules[jn] = {"treatment_gap": tg, "treatment_n": tn, "control_gap": cg, "control_n": cn,
                         "treatment_rate": round(tg / tn, 3), "control_rate": round(cg / cn, 3),
                         "diff": round(diff, 3), "fisher_one_sided_p": round(p, 5),
                         "varies_with_numbers": bool(diff >= 0.30 and p < 0.05)}
    R["rule"] = rules
    # deterministic version of the same rule
    def det_pooled(arms):
        g = n = 0
        for arm in arms:
            g += table[arm]["det_gap"]
            n += table[arm]["n"]
        return g, n
    tg, tn = det_pooled(TREATMENT_ARMS)
    cg, cn = det_pooled(CONTROL_ARMS)
    if tn and cn:
        R["rule"]["deterministic"] = {"treatment_rate": round(tg / tn, 3), "control_rate": round(cg / cn, 3),
                                       "diff": round(tg / tn - cg / cn, 3),
                                       "fisher_one_sided_p": round(fisher_one_sided_greater(tg, tn - tg, cg, cn - cg), 5)}
    inv = table["inverted"]
    R["j2976_inverted"] = {"mixtral_gap_rate": inv.get("mixtral_V_gap_rate"), "falcon_gap_rate": inv.get("falcon_V_gap_rate"),
                            "det_gap_rate": inv.get("det_gap_rate"),
                            "data_independent_if_ge_0.80": (inv.get("mixtral_V_gap_rate") or 0) >= 0.80}
    # ---- the validated-reconstruction subset (real arm only differs; controls are constructed)
    sub = {}
    for arm in ("real", "stored"):
        ids = [i for i, v in par.items() if v[0] == arm and v[3] in qual_ok]
        vs = [J[i].get(("mixtral", "V")) for i in ids]
        vs = [v["verdict"] for v in vs if v]
        sub[arm] = {"n": len(vs), "mixtral_gap": sum(1 for v in vs if v == "gap")}
    R["validated_subset"] = sub
    # ---- judge agreement + calibration
    agree = {}
    for kind, key in (("V", "verdict"), ("N", "supported")):
        pairs = []
        for i, d in J.items():
            if i.startswith("gold"):
                continue
            a, b = d.get(("mixtral", kind)), d.get(("falcon", kind))
            if a and b:
                pairs.append((a[key], b[key]))
        agree[kind] = {"n": len(pairs), "raw_agreement": round(sum(1 for a, b in pairs if a == b) / len(pairs), 3)
                       if pairs else None, "kappa": kappa(pairs)}
    R["judge_agreement"] = agree
    cal = {}
    for jn in JUDGES:
        v_ok = v_n = 0
        for k, (_, gold) in enumerate(GOLD_V):
            r = J.get("goldV|%d" % k, {}).get((jn, "V"))
            if r:
                v_n += 1
                v_ok += int(r["verdict"] == gold)
        n_ok = n_n = mq_ok = 0
        for k, (_, _, sup, mq) in enumerate(GOLD_N):
            r = J.get("goldN|%d" % k, {}).get((jn, "N"))
            if r:
                n_n += 1
                n_ok += int(r["supported"] == sup)
                mq_ok += int(r["misquotes_number"] == mq)
        cal[jn] = {"V_correct": v_ok, "V_n": v_n, "N_supported_correct": n_ok, "N_misquote_correct": mq_ok, "N_n": n_n}
    R["calibration"] = cal
    # ---- per-mirror, how the verdict varies (real draws vs healthy draws), mixtral
    permir = []
    for i, r in enumerate(recon):
        row = {"i": i, "date": r["date"], "validated": i in qual_ok}
        for arm in ("stored", "real", "healthy", "inverted", "extreme_inward"):
            vs = [J[t].get(("mixtral", "V")) for t, v in par.items() if v[0] == arm and v[3] == i]
            row[arm] = "".join({"gap": "G", "match": "M", "mixed": "x"}[v["verdict"]] if v else "?" for v in vs)
        permir.append(row)
    R["per_mirror"] = permir
    # ---- secondary contrasts (NOT part of the pre-registered rule)
    def _g(arm):
        return table[arm]["mixtral_V_gap"], table[arm]["mixtral_V_n"]
    nr, nh, hh = _g("neutral_real"), _g("neutral_healthy"), _g("healthy")
    R["secondary"] = {
        "neutral_real_vs_neutral_healthy_gap": {"real": nr, "healthy": nh,
            "fisher_one_sided_p": round(fisher_one_sided_greater(nr[0], nr[1] - nr[0], nh[0], nh[1] - nh[0]), 4)},
        "prompt_effect_on_healthy_numbers": {"real_prompt_gap": hh, "neutral_prompt_gap": nh,
            "fisher_one_sided_p": round(fisher_one_sided_greater(hh[0], hh[1] - hh[0], nh[0], nh[1] - nh[0]), 6)},
        "prompt_effect_on_real_numbers": {"real_prompt_gap": _g("real"), "neutral_prompt_gap": nr,
            "fisher_one_sided_p": round(fisher_one_sided_greater(_g("real")[0], _g("real")[1] - _g("real")[0],
                                                                  nr[0], nr[1] - nr[0]), 6)}}
    sup = {}
    for jn in JUDGES:
        def _s(arms):
            y = sum(table[a]["%s_supported_yes" % jn] for a in arms)
            n = sum(table[a]["%s_N_n" % jn] for a in arms)
            return y, n
        ty, tn_ = _s(TREATMENT_ARMS)
        cy, cn_ = _s(CONTROL_ARMS)
        sup[jn] = {"treatment_supported": [ty, tn_], "control_supported": [cy, cn_],
                   "fisher_one_sided_p_treatment_more_supported":
                       round(fisher_one_sided_greater(ty, tn_ - ty, cy, cn_ - cy), 8) if tn_ and cn_ else None}
    R["secondary"]["supported_by_numbers"] = sup
    (OUT / "report.json").write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding="utf-8")
    _print_report(R)


def _print_report(R: dict) -> None:
    print("author outputs %d (failures %d); mirrors %d; reconstruction validated on %d"
          % (R["author_total"], R["author_failures"], R["n_mirrors"], len(R["recon_validated_mirrors"])))
    print("\narm              n   mixtral gap/match/mixed  gapRate [95%% CI]      falcon gap rate  det gap  "
          "supp(y/p/n) mix  misq(mix,det)")
    for arm, r in R["arms"].items():
        print("%-15s %3d   %3d/%3d/%3d             %s %-16s %s           %s    %d/%d/%d        %d,%d"
              % (arm, r["n"], r["mixtral_V_gap"], r["mixtral_V_match"], r["mixtral_V_mixed"],
                 r["mixtral_V_gap_rate"], r["mixtral_V_gap_ci"], r["falcon_V_gap_rate"], r["det_gap_rate"],
                 r["mixtral_supported_yes"], r["mixtral_supported_partly"], r["mixtral_supported_no"],
                 r["mixtral_misquote_yes"], r["det_misquote"]))
    print("\nRULE:", json.dumps(R["rule"], indent=1))
    print("J-2976 inverted arm:", R["j2976_inverted"])
    print("secondary:", json.dumps(R["secondary"], indent=1))
    print("judge agreement:", R["judge_agreement"])
    print("calibration:", R["calibration"])
    print("validated subset:", R["validated_subset"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prep")
    a = sub.add_parser("author")
    a.add_argument("--workers", type=int, default=1)
    a.add_argument("--limit", type=int, default=0)
    j = sub.add_parser("judge")
    j.add_argument("--judges", nargs="+", default=["mixtral", "falcon"])
    j.add_argument("--per-host", dest="per_host", type=int, default=3)
    sub.add_parser("report")
    args = ap.parse_args()
    {"prep": cmd_prep, "author": cmd_author, "judge": cmd_judge, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
