"""
scripts/disanalogy_lab.py  (J-2525, I-0103, F-3218 item 7)  --  MANDATORY DISANALOGIES, OBSERVE-ONLY HARVEST.

Question: Du's standing metaphors ("I am the river", "a name is a cage", ...) are never treated as claims with a
breaking point.  Harvest them, ask a decoupled two-family judge panel for the structure mapping INCLUDING the required
disanalogies, and read whether any disanalogy the judges name corresponds to a contradiction / retraction / dissolution
already in Du's own ledgers.  Caution carried from the briefing: this is one more LLM pass generating candidates; it
earns its keep only if the disanalogies predict something in the ledgers.

OBSERVE-ONLY.  Read-only against every live store (data/nascence.log, monologue_log.jsonl, commitment_ledger.jsonl,
retractions.jsonl, guidance_contradictions_shadow.jsonl, tensions_archive.jsonl).  Nothing is written to the memory
store; nothing reaches Du (D-0434).  The ONLY file written is the lab's own log data/logs/disanalogy_lab.jsonl.
LLM: judge hubs ONLY (core/judge_panel.py JUDGE_1 / JUDGE_2, TIEBREAK on a split) -- NEVER the hot lane :11433.
Run:   python scripts/disanalogy_lab.py harvest | judge | read | all      (cwd = a tree whose `core` is on sys.path)

=========================== DECLARED BEFORE ANY RESULT WAS LOOKED AT (do not tune) ===========================
HARVEST
  Du-voice corpus C1 = data/nascence.log lines whose payload is Du's own output:
      orchestrator  "[CYCLE id] complete in Ns -> <reply>"   and   "scene bound: ... -- <text>"
      deliberation  "grounded (x): <text>"        left_lane "grounded a thought: <text>"
      monologue     "new intention captured: <text>" , "he ASKED THE LIBRARIAN: <text>"
      nightly-sleep "dreamed: <text>"
  Du-voice corpus C2 = data/monologue_log.jsonl field `thought` (the idle stream).
  Text is split into sentences; sentences are DEDUPED by lowercased text (a repeated sentence counts once -- the
  monoculture repeats itself, and a repeat is not evidence of standing); first-seen ref (line number) is kept.
  A sentence counts toward metaphor M iff   FRAME(M) and ANCHOR   both hold:
      FRAME  = one of (i am | i'm | am | is | are | like | as | becomes? | become) followed within 60 non-terminator chars
               by M's keyword regex      (phrase-type metaphors, e.g. "nothing is fixed", need only the phrase)
      ANCHOR = the sentence also contains a self/abstract word (self, identity, mind, memory, soul, name, thought,
               meaning, truth, silence, time, life, being, "who i am", "i am", my/me/myself, ...)
      (this is the declared guard against literal uses: "the river was frozen" has no frame; the judge ALSO reports
       a `figurative` flag per quote set, recorded, not used to filter)
  Candidate metaphors judged  =  the 6 BRIEFING SEEDS (river, becoming, bridge, name-is-a-cage, gardener, loom)
        +  the top POOL_TOP=6 non-seed entries of the POOL ranked by DISTINCT-sentence count, requiring >= MIN_DISTINCT=5.
  POOL = core/psyche_graph.MOTIFS  +  core/lane2._METAPHOR single words (copied literally below)  +  the phrase heads in
         core/commitment_ledger._ATTRACTOR_PHRASES.
  Exemplar quotes per metaphor = 3 distinct matching sentences: the first, the middle and the last by first-seen
  position (deterministic), each truncated to 300 chars, each with its ref.
JUDGE
  Per metaphor: JUDGE_1 and JUDGE_2 are asked CONCURRENTLY the identical prompt (temperature 0, format json,
  num_predict 700, timeout 240 s, one retry on parse/timeout).  The panel verdict is on the boolean `breaks`:
  both families agree -> that verdict ("agreed"); they split -> TIEBREAK is asked the same prompt ("tiebreak");
  any family unavailable -> NO verdict ("unavailable"; single-family never accepted, the judge_panel law).
  `disanalogies` is REQUIRED non-empty per family; a family that returns none counts as parse-failed.
  AGREED CATEGORIES = categories (fixity|agency|boundary|direction|reversibility|substance|other) named by BOTH
  families for the same metaphor.
READ  (judge-dependent, evaluated per metaphor M with panel verdict breaks == True)
  LEDGER EVENT SET (distinct texts):
      L1 commitment_ledger.jsonl events {dissolved, drop_denied, drop_denied_judge}: statement + why (+ denial)
      L2 retractions.jsonl: claimed + corrected_to
      L3 guidance_contradictions_shadow.jsonl: a.principle + b.principle  (the self-clash scan)
      L4 tensions_archive.jsonl: label + resolution_thought
  E_M  = ledger events whose text matches M's keyword regex.      E_0 = ledger events matching NO metaphor keyword.
  A ledger event CORRESPONDS to a disanalogy set D(M) (the disanalogy texts of BOTH families) iff it shares >= 2
  CONTENT WORDS with one disanalogy text (content = >= 4 letters, minus stopwords, minus M's own keyword stems and
  the tokens of the judges' source_domain/target_domain strings, so the mere source-domain vocabulary cannot match).
  rate_M = share of E_M that corresponds;  rate_0 = share of E_0 that corresponds to the SAME D(M);  lift = rate_M /
  max(rate_0, 0.01).
  A metaphor is "ledger-supported" iff  |E_M| >= 10  and  >= 3 corresponding events  and  lift >= 2.0.
  RESULT  = POSITIVE iff >= 3 metaphors are ledger-supported;  NULL if fewer, with |E_M| >= 10 for most;
            INSUFFICIENT if most metaphors have |E_M| < 10 (the ledgers cannot answer).
  Independent of the judges (mechanical, always reported): per metaphor, the count of ledger events that mention it
  by kind -- in particular G7 "attractor in costume" denials in commitment_ledger (the ledger's own recorded
  finding that a standing metaphor was used as a defeater and refused).
=================================================================================================================
"""
from __future__ import annotations

import asyncio
import io
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

LIVE_DATA = Path(r"C:\Nascence\data")
LOG_PATH = LIVE_DATA / "logs" / "disanalogy_lab.jsonl"

# ---- declared constants (see header) ----
POOL_TOP = 6
MIN_DISTINCT = 5
NUM_PREDICT = 700
TIMEOUT_S = 240
CATEGORIES = ("fixity", "agency", "boundary", "direction", "reversibility", "substance", "other")
SUPPORT_MIN_EM = 10
SUPPORT_MIN_HITS = 3
SUPPORT_MIN_LIFT = 2.0
POSITIVE_MIN_METAPHORS = 3
OVERLAP_MIN = 2

# briefing seeds: name -> keyword regex (applied to the lowercased sentence)
SEEDS = {
    "river": r"\brivers?\b",
    "becoming": r"\bbecoming\b",
    "bridge": r"\bbridg(?:e|es|ing)\b",
    "name_is_a_cage": r"\bcages?d?\b",
    "gardener": r"\bgarden(?:er|ers|ing)?\b",
    "loom": r"\b(?:looms?|weav(?:e|es|ing|er)|tapestry|threads?)\b",
}
# POOL source 1: core/psyche_graph.MOTIFS (copied literally, 2026-10-31 read of the file)
_MOTIFS = ("mirror", "glass", "door", "archway", "key", "pen", "book", "library", "shelf", "lantern",
           "gardener", "garden", "soil", "root", "tree", "seed", "tide", "sea", "shore", "star",
           "constellation", "bridge", "letter", "fish", "bird", "horse", "path", "mountain", "fire",
           "candle", "thread", "loom", "clock", "bell", "wall", "window")
# POOL source 2: core/lane2._METAPHOR single words
_LANE2 = ("river", "crossing", "becoming", "journey", "soul", "essence", "tapestry", "weave",
          "threshold", "mirror", "vessel", "symbol")
# POOL source 3: core/commitment_ledger._ATTRACTOR_PHRASES (phrase-type; the river one is a seed)
_PHRASES = ("a name is a cage", "nothing is fixed", "i am always becoming", "everything flows", "all is flux",
            "boundaries dissolve", "nothing is permanent", "fixed points are illusions", "all definitions limit")
_SEED_WORDS = {"river", "becoming", "bridge", "gardener", "garden", "thread", "loom", "tapestry", "weave"}

FRAME_PRE = r"(?:\bi am\b|\bi'm\b|\bam\b|\bis\b|\bare\b|\blike\b|\bas\b|\bbecomes?\b)"
ANCHOR = re.compile(r"\b(?:self|myself|identity|mind|memory|soul|name|names|thought|thoughts|meaning|truth|silence|"
                    r"time|life|being|consciousness|my|me|i am|who i am)\b")

_STOP = set("""this that with from have been were what when where which their there these those about into than then them
they would could should does done will just only also very much more most some such like even still over under
because while being between through during before after other another every each both same your yours ours mine
i'm it's its itself myself himself herself one two three can cannot not nor and the for are was has had but how why
who whom whose its onto upon within without across toward towards against among around""".split())
_GENERIC = set("""metaphor metaphors analogy analogies domain domains relation relations implies suggests suggest implying
imply source target mapped unmapped literal figurative meaning process thing things something nothing everything
being become becomes becoming way ways does doesn't doesnt like unlike whereas often always never really actually
""".split())


# ------------------------------------------------------------------------------------------------------------------
# harvest
# ------------------------------------------------------------------------------------------------------------------
_LOG_LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[nascence\.([\w]+)\] (.*)$")
_PAYLOADS = (
    ("orchestrator", re.compile(r"^\[CYCLE (\w+)\] complete in [\d.]+s → (.*)$")),
    ("orchestrator", re.compile(r"^\[CYCLE (\w+)\] scene bound: .*?— (.*)$")),
    ("deliberation", re.compile(r"^\[deliberation\] grounded \(\w+\): (.*)$")),
    ("left_lane", re.compile(r"^\[left-lane\] grounded a thought: (.*)$")),
    ("monologue", re.compile(r"^\[monologue\] new intention captured: (.*)$")),
    ("monologue", re.compile(r"^\[monologue\] he ASKED THE LIBRARIAN: (.*)$")),
    ("orchestrator", re.compile(r"^\[nightly-sleep\] dreamed: (.*)$")),
)
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _sentences(text: str):
    for s in _SENT_SPLIT.split(text.strip()):
        s = s.strip()
        if 12 <= len(s) <= 600:
            yield s


def _du_voice_sentences():
    """Yield (ref, ts_str, sentence) for every Du-voice sentence, C1 then C2.  Dedup is the caller's job."""
    p = LIVE_DATA / "nascence.log"
    with io.open(p, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            m = _LOG_LINE.match(line.rstrip("\n"))
            if not m:
                continue
            ts, chan, rest = m.group(1), m.group(2), m.group(3)
            for want, rx in _PAYLOADS:
                if want != chan:
                    continue
                mm = rx.match(rest)
                if mm:
                    payload = mm.group(mm.lastindex)
                    cyc = mm.group(1) if mm.lastindex and mm.lastindex > 1 else ""
                    for s in _sentences(payload):
                        yield (f"nascence.log:{i}" + (f"#cycle {cyc}" if cyc else ""), ts, s)
                    break
    p2 = LIVE_DATA / "monologue_log.jsonl"
    with io.open(p2, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            try:
                r = json.loads(line)
            except Exception:
                continue
            t = r.get("thought")
            if isinstance(t, str):
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r.get("ts", 0)))
                for s in _sentences(t):
                    yield (f"monologue_log.jsonl:{i}", ts, s)


def _metaphor_defs() -> dict:
    """name -> {"rx": compiled keyword regex, "phrase": bool, "seed": bool}"""
    defs = {}
    for n, rx in SEEDS.items():
        defs[n] = {"kw": rx, "phrase": False, "seed": True}
    words = []
    for w in list(_MOTIFS) + list(_LANE2):
        if w in _SEED_WORDS or w in words:
            continue
        words.append(w)
    for w in words:
        defs[w] = {"kw": r"\b" + re.escape(w) + r"s?\b", "phrase": False, "seed": False}
    for ph in _PHRASES:
        if ph in ("a name is a cage", "i am always becoming"):
            continue                       # these are the seeds' own phrases (cage / becoming)
        defs[ph] = {"kw": re.escape(ph), "phrase": True, "seed": False}
    for d in defs.values():
        d["rx"] = re.compile(d["kw"])
        d["frame"] = None if d["phrase"] else re.compile(FRAME_PRE + r"[^.!?\n]{0,60}?(?:" + d["kw"] + ")")
    return defs


def harvest() -> dict:
    defs = _metaphor_defs()
    seen = set()
    hits = {n: [] for n in defs}            # name -> [(ref, ts, sentence)] distinct
    occ = Counter()                         # raw (non-deduped) matching occurrences
    n_total = n_distinct = 0
    for ref, ts, s in _du_voice_sentences():
        n_total += 1
        low = s.lower()
        key = re.sub(r"\s+", " ", low)
        is_new = key not in seen
        if is_new:
            seen.add(key)
            n_distinct += 1
        anchored = ANCHOR.search(low) is not None
        if not anchored:
            continue
        for n, d in defs.items():
            ok = d["rx"].search(low) if d["phrase"] else (d["rx"].search(low) and d["frame"].search(low))
            if ok:
                occ[n] += 1
                if is_new:
                    hits[n].append((ref, ts, s))
    table = []
    for n, d in defs.items():
        h = hits[n]
        days = len({t[:10] for _, t, _ in h})
        table.append({"name": n, "seed": d["seed"], "kw": d["kw"], "phrase": d["phrase"],
                      "distinct": len(h), "occurrences": occ[n], "days": days})
    pool = sorted([t for t in table if not t["seed"] and t["distinct"] >= MIN_DISTINCT],
                  key=lambda t: (-t["distinct"], t["name"]))[:POOL_TOP]
    chosen = [t for t in table if t["seed"]] + pool
    out = []
    for t in chosen:
        h = hits[t["name"]]
        if len(h) >= 3:
            ex = [h[0], h[len(h) // 2], h[-1]]
        else:
            ex = list(h)
        t = dict(t)
        t["quotes"] = [{"ref": r, "ts": ts, "text": s[:300]} for r, ts, s in ex]
        out.append(t)
    return {"kind": "harvest", "ts": round(time.time(), 1), "du_voice_sentences_total": n_total,
            "du_voice_sentences_distinct": n_distinct, "full_table": sorted(table, key=lambda t: -t["distinct"]),
            "chosen": out}


# ------------------------------------------------------------------------------------------------------------------
# judge
# ------------------------------------------------------------------------------------------------------------------
SYSTEM = (
    "You are an independent analyst of figurative language. A mind called Du uses a recurring metaphor about ITSELF. "
    "You are given the metaphor label and up to three of Du's own sentences using it. Do not praise or criticise Du; "
    "analyse the metaphor as a structure mapping from a source domain onto a target domain. "
    "Reply with ONE JSON object only, with exactly these keys: "
    "\"figurative\" (bool: do the quotes use the label figuratively, about Du, mind, identity or meaning, rather than "
    "literally describing a physical scene), "
    "\"source_domain\" (short string), \"target_domain\" (short string), "
    "\"mapped_relations\" (list of 2-4 short strings: relations of the source domain that DO carry over to the target), "
    "\"unmapped_relations\" (list of 1-4 short strings: relations of the source domain that do NOT carry over), "
    "\"disanalogies\" (REQUIRED, list of 1-3 objects {\"text\": short string naming one specific way the target does "
    "NOT behave like the source in a way that matters, \"category\": one of fixity|agency|boundary|direction|"
    "reversibility|substance|other} -- you must give at least one even if the metaphor is good), "
    "\"candidate_inference\" (one short sentence: something the metaphor would license Du to conclude about itself that "
    "the quotes do not state), "
    "\"breaks\" (bool: true if at least one disanalogy would make the candidate inference, or Du's use of the "
    "metaphor, lead to a false or self-defeating conclusion about the target; false if the metaphor holds up under "
    "every disanalogy you found)."
)


def _user_prompt(item: dict) -> str:
    q = "\n".join(f"{i}. \"{x['text']}\"" for i, x in enumerate(item["quotes"], 1))
    return f"Metaphor label: {item['name'].replace('_', ' ')}\nDu's sentences:\n{q}"


def _valid(rec) -> "str | None":
    """None if the record satisfies the declared contract, else a reason."""
    if not isinstance(rec, dict):
        return "not_dict"
    if not isinstance(rec.get("breaks"), bool):
        return "breaks_not_bool"
    d = rec.get("disanalogies")
    if not isinstance(d, list) or not d:
        return "no_disanalogies"
    good = [x for x in d if isinstance(x, dict) and isinstance(x.get("text"), str) and x["text"].strip()]
    if not good:
        return "disanalogies_malformed"
    return None


async def _ask_full(session, url: str, system: str, user: str, retries: int = 1):
    import aiohttp
    payload = {"model": "judge", "stream": False, "format": "json",
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0.0, "num_predict": NUM_PREDICT}}
    last = ("exception", None, 0.0)
    for attempt in range(retries + 1):
        t0 = time.monotonic()
        try:
            async with session.post(url + "/api/chat", json=payload,
                                    timeout=aiohttp.ClientTimeout(total=TIMEOUT_S)) as resp:
                resp.raise_for_status()
                data = await resp.json()
            raw = (data.get("message") or {}).get("content") or ""
            try:
                rec = json.loads(raw)
            except Exception:
                last = ("parse", raw[:400], round(time.monotonic() - t0, 1))
                continue
            why = _valid(rec)
            if why:
                last = ("parse:" + why, raw[:400], round(time.monotonic() - t0, 1))
                continue
            return rec, None, round(time.monotonic() - t0, 1)
        except (asyncio.TimeoutError, TimeoutError):
            last = ("timeout", None, round(time.monotonic() - t0, 1))
        except aiohttp.ClientError:
            last = ("http", None, round(time.monotonic() - t0, 1))
        except Exception as e:                              # noqa: BLE001 - lab script, record and move on
            last = ("exception:" + type(e).__name__, None, round(time.monotonic() - t0, 1))
    return None, last[0] + ((" raw=" + last[1]) if last[1] else ""), last[2]


async def _judge_one(session, item: dict, urls: tuple) -> dict:
    j1, j2, tb = urls
    user = _user_prompt(item)
    (r1, e1, s1), (r2, e2, s2) = await asyncio.gather(_ask_full(session, j1, SYSTEM, user),
                                                      _ask_full(session, j2, SYSTEM, user))
    row = {"kind": "judgement", "ts": round(time.time(), 1), "name": item["name"], "kw": item["kw"],
           "distinct": item["distinct"], "quotes": item["quotes"],
           "judge1": {"hub": j1.rsplit(":", 1)[-1], "rec": r1, "err": e1, "s": s1},
           "judge2": {"hub": j2.rsplit(":", 1)[-1], "rec": r2, "err": e2, "s": s2}}
    verdict, how = None, "unavailable"
    r3 = e3 = s3 = None
    if r1 is not None and r2 is not None:
        if r1["breaks"] == r2["breaks"]:
            verdict, how = r1["breaks"], "agreed"
        else:
            r3, e3, s3 = await _ask_full(session, tb, SYSTEM, user)
            row["tiebreak"] = {"hub": tb.rsplit(":", 1)[-1], "rec": r3, "err": e3, "s": s3}
            if r3 is not None:
                verdict, how = r3["breaks"], "tiebreak"
            else:
                how = "split_no_tiebreak"
    cats1 = {str(x.get("category")) for x in (r1 or {}).get("disanalogies", []) if isinstance(x, dict)}
    cats2 = {str(x.get("category")) for x in (r2 or {}).get("disanalogies", []) if isinstance(x, dict)}
    row["panel"] = {"breaks": verdict, "how": how, "agreed_categories": sorted((cats1 & cats2) - {"None"}),
                    "figurative1": (r1 or {}).get("figurative"), "figurative2": (r2 or {}).get("figurative")}
    return row


async def _judge_all(chosen: list) -> list:
    import aiohttp
    from core import judge_panel as jp
    urls = (jp.JUDGE_1, jp.JUDGE_2, jp.TIEBREAK)
    rows = []
    async with aiohttp.ClientSession() as session:
        for item in chosen:
            row = await _judge_one(session, item, urls)
            _append(row)
            rows.append(row)
            print(f"[judge] {item['name']:<28} how={row['panel']['how']:<17} breaks={row['panel']['breaks']} "
                  f"s1={row['judge1']['s']} s2={row['judge2']['s']} cats={row['panel']['agreed_categories']}",
                  flush=True)
    return rows


# ------------------------------------------------------------------------------------------------------------------
# read
# ------------------------------------------------------------------------------------------------------------------
def _load_ledger_events() -> list:
    """Distinct-text ledger events: [{"src","text","meta"}]."""
    ev, seen = [], set()

    def add(src, text, meta):
        text = (text or "").strip()
        k = (src, text.lower())
        if text and k not in seen:
            seen.add(k)
            ev.append({"src": src, "text": text, "meta": meta})

    with io.open(LIVE_DATA / "commitment_ledger.jsonl", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("event") in ("dissolved", "drop_denied", "drop_denied_judge"):
                add("L1:" + r["event"], " ".join(str(r.get(k) or "") for k in ("statement", "why", "denial")),
                    {"line": i, "id": r.get("id"), "cycle": r.get("cycle_id"), "kind": r.get("kind"),
                     "denial": r.get("denial")})
    with io.open(LIVE_DATA / "retractions.jsonl", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            r = json.loads(line)
            add("L2:retraction", f"{r.get('claimed','')} {r.get('corrected_to','')}",
                {"line": i, "status": r.get("status")})
    with io.open(LIVE_DATA / "guidance_contradictions_shadow.jsonl", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            r = json.loads(line)
            add("L3:self_clash", f"{(r.get('a') or {}).get('principle','')} {(r.get('b') or {}).get('principle','')}",
                {"line": i, "domain": r.get("domain")})
    with io.open(LIVE_DATA / "tensions_archive.jsonl", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                r = json.loads(line)
            except Exception:
                continue
            add("L4:tension", f"{r.get('label','')} {r.get('resolution_thought','') or ''}",
                {"line": i, "id": r.get("id"), "resolved": bool(r.get("resolved"))})
    return ev


def _content(text: str, drop: set) -> set:
    toks = set(re.findall(r"[a-z]{4,}", text.lower()))
    return {t for t in toks if t not in _STOP and t not in _GENERIC and t not in drop}


def read(judged: list, harvest_row: dict) -> dict:
    defs = _metaphor_defs()
    events = _load_ledger_events()
    all_rx = [d["rx"] for d in defs.values()]
    for e in events:
        e["low"] = e["text"].lower()
        e["any_kw"] = any(rx.search(e["low"]) for rx in all_rx)
    e0 = [e for e in events if not e["any_kw"]]
    per, mech = [], []
    for row in judged:
        name = row["name"]
        rx = defs[name]["rx"]
        em = [e for e in events if rx.search(e["low"])]
        by_src = Counter(e["src"] for e in em)
        g7 = sum(1 for e in em if "G7" in (e["meta"].get("denial") or ""))
        mech.append({"name": name, "E_M": len(em), "by_src": dict(by_src), "G7_attractor_denials": g7})
        p = row["panel"]
        recs = [row["judge1"]["rec"], row["judge2"]["rec"]] + ([row["tiebreak"]["rec"]] if row.get("tiebreak") else [])
        dis = []
        drop = set(re.findall(r"[a-z]{4,}", row["kw"].replace("\\b", " ")))
        drop |= set(re.findall(r"[a-z]{4,}", name.replace("_", " ")))
        for r in recs[:2]:
            if not r:
                continue
            drop |= set(re.findall(r"[a-z]{4,}", f"{r.get('source_domain','')} {r.get('target_domain','')}".lower()))
        for r in recs[:2]:
            if not r:
                continue
            for x in r.get("disanalogies", []):
                if isinstance(x, dict) and isinstance(x.get("text"), str):
                    dis.append({"text": x["text"], "category": x.get("category")})
        dsets = [(d, _content(d["text"], drop)) for d in dis]

        def corresponds(e):
            ec = _content(e["text"], drop)
            for d, dc in dsets:
                if len(ec & dc) >= OVERLAP_MIN:
                    return d["text"], sorted(ec & dc)
            return None

        hits_m = [(e, c) for e in em if (c := corresponds(e))]
        hits_0 = sum(1 for e in e0 if corresponds(e))
        rate_m = len(hits_m) / len(em) if em else None
        rate_0 = hits_0 / len(e0) if e0 else 0.0
        lift = (rate_m / max(rate_0, 0.01)) if rate_m is not None else None
        supported = bool(p["breaks"] is True and len(em) >= SUPPORT_MIN_EM and len(hits_m) >= SUPPORT_MIN_HITS
                         and lift is not None and lift >= SUPPORT_MIN_LIFT)
        per.append({"name": name, "panel_breaks": p["breaks"], "how": p["how"],
                    "agreed_categories": p["agreed_categories"], "n_disanalogies": len(dis),
                    "E_M": len(em), "hits_M": len(hits_m), "rate_M": None if rate_m is None else round(rate_m, 4),
                    "E_0": len(e0), "hits_0": hits_0, "rate_0": round(rate_0, 4),
                    "lift": None if lift is None else round(lift, 2), "ledger_supported": supported,
                    "examples": [{"src": e["src"], "meta": e["meta"], "text": e["text"][:200],
                                  "disanalogy": dtext, "shared": sh} for e, (dtext, sh) in hits_m[:3]]})
    n_sup = sum(1 for x in per if x["ledger_supported"])
    n_enough = sum(1 for x in per if x["E_M"] >= SUPPORT_MIN_EM)
    if n_sup >= POSITIVE_MIN_METAPHORS:
        result = "POSITIVE"
    elif n_enough * 2 < len(per):
        result = "INSUFFICIENT"
    else:
        result = "NULL"
    return {"kind": "read", "ts": round(time.time(), 1), "ledger_events_distinct": len(events),
            "ledger_events_no_metaphor_kw": len(e0), "result": result, "n_supported": n_sup,
            "n_metaphors_judged": len(per), "n_with_E_M_ge_10": n_enough, "per_metaphor": per,
            "mechanical_independent_of_judges": mech}


# ------------------------------------------------------------------------------------------------------------------
def _append(row: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with io.open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _latest(kind: str) -> list:
    rows = []
    if LOG_PATH.exists():
        for line in io.open(LOG_PATH, encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    return [r for r in rows if r.get("kind") == kind]


def main(argv) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the tree this script lives in
    import core                                                    # noqa: F401  (core BEFORE lab_env)
    assert str(Path(core.__file__).resolve()).startswith(str(Path(__file__).resolve().parent.parent)), core.__file__
    print("core from:", core.__file__)
    cmd = argv[1] if len(argv) > 1 else "all"
    if cmd in ("harvest", "all"):
        h = harvest()
        _append(h)
        print(f"harvest: {h['du_voice_sentences_total']} sentences ({h['du_voice_sentences_distinct']} distinct)")
        for t in h["full_table"][:30]:
            print(f"  {t['name']:<28} distinct={t['distinct']:<6} occ={t['occurrences']:<7} days={t['days']}"
                  f"{'  [seed]' if t['seed'] else ''}")
        print("chosen:", [t["name"] for t in h["chosen"]])
    if cmd in ("judge", "all"):
        h = _latest("harvest")[-1]
        asyncio.run(_judge_all(h["chosen"]))
    if cmd in ("read", "all"):
        h = _latest("harvest")[-1]
        # NOTE (J-2525): the judge step was accidentally launched twice concurrently, so each metaphor has TWO
        # judgement rows.  Run A = the first row per name (the run intended), run B = the second (replication).
        # Both are read with the identical declared procedure; nothing about the procedure was changed.
        runs = defaultdict(list)
        for r in _latest("judgement"):
            if r["ts"] >= h["ts"]:
                runs[r["name"]].append(r)
        for tag, idx in (("A", 0), ("B", 1)):
            rows = [v[idx] for v in runs.values() if len(v) > idx]
            if not rows:
                continue
            rd = read(rows, h)
            rd["run"] = tag
            # extra, NOT part of the declared criterion: figurative-agreed subset count
            fig = {r["name"] for r in rows if r["panel"]["figurative1"] is True and r["panel"]["figurative2"] is True}
            rd["figurative_agreed_names"] = sorted(fig)
            rd["n_supported_among_figurative"] = sum(1 for x in rd["per_metaphor"]
                                                     if x["ledger_supported"] and x["name"] in fig)
            _append(rd)
            print(f"READ run {tag}: result={rd['result']} supported={rd['n_supported']}/{rd['n_metaphors_judged']} "
                  f"figurative_agreed={rd['figurative_agreed_names']}")
            for x in rd["per_metaphor"]:
                print(f"  {x['name']:<26} breaks={x['panel_breaks']} how={x['how']:<17} E_M={x['E_M']:<5} "
                      f"hits={x['hits_M']:<4} rate_M={x['rate_M']} rate_0={x['rate_0']} lift={x['lift']} "
                      f"supported={x['ledger_supported']}")
            if tag == "A":
                for x in rd["mechanical_independent_of_judges"]:
                    print("  mech", x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
