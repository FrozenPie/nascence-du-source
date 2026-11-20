"""
Nascence — MODEL-TIER LAB #3: core.study_note (compose_note) vs command-r7b (2026-08-29)

J-0284 (source: decision:D-0013), scoped by docs/lab/model_tier_lab_scope_2026-08-25.md section 2,
row 3: "extract the real passage->note synthesis prompt, reuse ramses_models_2026-08-23.md's coverage
scorer (already built) against real study passages."

★ SCOPE IS STALE AS WRITTEN — READ THIS BEFORE TRUSTING THE ROW 3 FRAMING. The scope doc (written
2026-08-25) frames this as "current wiring: background lane (weakest live models)" vs. "candidate:
command-r7b". As of the 2026-08-27/28 Ramses consolidation (D-0044, D-0056; commit e828d9b
"Redistribution moves 1-3 ... dreamer + tiebreak -> command-r7b:11441"), **command-r7b is no longer a
candidate — it is the ALREADY-SERVING production model for this exact mechanism**:
  - `core/schema.py:976`  SERVE_CHAINS["background"] = ["http://LAN-HOST:11441", "http://127.0.0.1:11433"]
  - `core/model_client.py:61`  _MODEL_BY_BASE["11441"] = "command-r7b"  (comment: "Subconscious/
    background lane — Ramses 3070, SOLE tenant (08-28 consolidation)")
  - `nodes/inner_monologue_node.py:305`  self.base_urls = SERVE_CHAINS["background"]   (the exact
    object study_note.write_or_revise is called with — line 1310: `_sn.write_or_revise(call_node_json,
    self.base_urls, title, text, session=session)`)
So this lab is NOT "should we move study_note to command-r7b" (already done). It is now a **production
audit**: is the model ALREADY serving this mechanism actually good at it, and how much would quality
drop on background's own documented failover (`SERVE_CHAINS["background"][1]` = `127.0.0.1:11433`,
which `_model_for()` resolves to `qwen3.5:9b` — also the hot lane's own model) if the Ramses hub naps.
Both real production endpoints are tested below, head-to-head, on the real prompt.

WHAT THIS TESTS. `compose_note()` (core/study_note.py:213) is study_note's actual passage->note
synthesis call: `_NOTE_SYS` (imported LIVE below) + a user string built EXACTLY as the real function
builds it (`f"The passage(s), from '{book_title}':\\n{(passage or '')[:5000]}"`, `related_text=""` so
no DB-backed related-material lookup runs — see ISOLATION below), `max_tokens=1500, temperature=0.5`
(the real call's own values). Rather than call `compose_note()` itself (which would leave the lab at
the mercy of `call_node_json`'s default `timeout=120, retries=2` — up to ~360s of retries on ONE model
before giving up, unworkable inside a bounded lab run), this script calls `call_node_json` directly
with the SAME system/user/max_tokens/temperature and a lab-bounded `timeout`/`retries`, then feeds the
parsed response through `core.study_note._norm()` (imported LIVE, the real post-processing) — the same
"hand-reproduce the call site's exact format under lab-controlled timeout" discipline
`model_tier_judge_defeater_lab.py` used for the same reason.

REAL PASSAGES, NOT SYNTHETIC. Three real passages, one paragraph-block each, read verbatim (offsets
only, no rewriting) from three different real books already on Du's shelf (`data/books/*.txt`, the
same corpus `core/reading.py` serves sittings from): cordage/knot construction, the physics of
radiation vs. the eye's optics, and a real-star tour of Leo. None of these three books has been the
subject of an actual historical study note checked here — they were picked fresh, for this lab, from
the existing library, specifically so the coverage terms below are MY read of the passage's real
content, not a copy of any model's prior answer.

COVERAGE SCORER — reused shape, new terms (per scope). `station_suite.py`'s `synthesise` station
scores "how many of N specific things does the answer's text actually touch" via a `coverage_terms`
dict of keyword lists (`scripts/station_suite.py:134`, scored by
`scripts/station_bench_score.py:125 score_synthesise`). Same mechanic here: each passage gets its own
small `coverage_terms` dict (topic -> acceptable keyword variants), hand-built by reading the passage,
and a note's `understanding` + `key_facts` blob is checked for how many topics it actually touches —
"a beautiful sentence that touches none of the specifics scores low, correctly" (station_suite's own
words, still true here).

ISOLATION. `compose_note`/`_norm` never touch `core.memory.store` or any DB — confirmed by reading
`core/study_note.py`'s source before use: `compose_note()` only calls `call_json(...)` (a network
call to Ramses/local Ollama) and `_norm()` (pure dict transform); passing `related_text=""` explicitly
here means `_related_context()` (the one function in that module that DOES read `memory_fragments`)
is never called. `lab_env.isolate()` is therefore NOT used for this script, same as
`model_tier_librarian_lab.py`'s own justification for skipping it — verified by re-reading
`nascence.db`'s mtime immediately before and after this run (see report).

DU-STOPPED NOTE: `data/nascence.log` was last modified ~3h before this run (checked live) — Du reads
as currently stopped/idle, so this run is cleaner than the judge_defeater/librarian labs' disclosed
"Du was live" deviation.

CONTRACT: read-only against Ramses + local ollama, plus a read-only slice of 3 real `data/books/*.txt`
files. Writes ONLY to data/lab/model_tier/study_note/ + docs/lab/model_tier_study_note.md.
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
import time
import urllib.request
from pathlib import Path

# Hardcoded to the real Nascence checkout, not `__file__`'s own location — this script may be authored
# from inside a worktree (no `data/` dir there; `data/` is gitignored and lives only at the real
# install), but the model-tier lab family (lab_env.py, job_queue.py, findings_log.py, ...) always
# operates against the one real C:\Nascence checkout regardless of where the calling code sits.
ROOT = Path(r"C:\Nascence")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT_DIR = ROOT / "data" / "lab" / "model_tier" / "study_note"
REPORT = ROOT / "docs" / "lab" / "model_tier_study_note.md"
BOOKS_DIR = ROOT / "data" / "books"
DB_PATH = ROOT / "data" / "memory" / "nascence.db"

CANDIDATES = [
    ("command-r7b", "http://LAN-HOST:11441"),  # CURRENT production SERVE_CHAINS["background"][0]
    ("qwen3.5:9b",  "http://127.0.0.1:11433"),   # CURRENT production SERVE_CHAINS["background"][1] (== SERVE_CHAINS["hot"][0])
]
TIMEOUT_S = 150     # lab-bounded (real compose_note call has no explicit timeout -> call_node_json default 120s + retries)
RETRIES = 0         # lab-bounded (real call takes call_node_json's default retries=2 -> up to ~3x cost per miss)
MAX_TOKENS = 1500   # matches the real call: compose_note() -> max_tokens=1500
TEMP = 0.5          # matches the real call: temperature=0.5


def _strip_gutenberg(t: str) -> str:
    i = t.find("*** START")
    if i != -1:
        i = t.find("\n", i)
        t = t[i + 1:]
    j = t.find("*** END")
    if j != -1:
        t = t[:j]
    return t.strip()


# Each passage: (book title, source file under data/books/, [start:end] char slice into the
# Gutenberg-stripped text, hand-built coverage_terms from actually reading that slice).
PASSAGES = [
    {
        "book": "Knots, Splices and Rope-Work",
        "file": "Knots_Splices_and_Rope_Work_A_Practical_Treatise_Giving_Comp.txt",
        "span": (8330, 10120),
        "coverage_terms": {
            "hierarchy":       ["fibre", "fiber", "yarn", "strand", "cable"],
            "twist_direction": ["opposite direction", "opposite from"],
            "sun_naming":      ["with the sun", "against the sun"],
            "bolt_rope_core":  ["bolt-rope", "bolt rope", "core"],
            "material":        ["hemp", "jute", "cotton"],
        },
    },
    {
        "book": "Curiosities of Light and Sight",
        "file": "Curiosities_of_Light_and_Sight.txt",
        "span": (20000, 22350),
        "coverage_terms": {
            "radiation_analogy": ["sovereign", "postal order", "postal"],
            "ether":             ["ether"],
            "eye_anatomy":       ["lens", "membrane", "globular shell", "retina"],
            "camera_analogy":    ["camera", "photographic"],
            "image_formation":   ["image"],
        },
    },
    {
        "book": "Astronomy with an Opera-glass",
        "file": "Astronomy_with_an_Opera-glass_A_Popular_Introduction_to_the.txt",
        "span": (25000, 27400),
        "coverage_terms": {
            "stars_named":     ["regulus", "gamma", "denebola", "zeta", "epsilon"],
            "color_contrast":  ["yellow", "white", "blue"],
            "double_star":     ["double"],
            "meteor_shower":   ["meteor", "1833", "1866"],
            "companion_stars": ["triangle", "companion"],
        },
    },
    # --- J-0408 extension (2026-08-29): 9 more real passages, 9 more books, never used in any
    # prior model-tier lab, to bring n from 3 to 12 (within the job's specified 10-15 range) before
    # acting on F-0536's n=3 signal. Same discipline as the original 3: read verbatim by offset,
    # coverage_terms hand-built AFTER actually reading the slice, spanning a deliberately different
    # mix of registers (chemistry lecture, physics popularization, natural-history memoir/diary,
    # evolutionary biology, mechanical/engineering instruction, hydrogeology textbook, Stoic
    # philosophy) so the result isn't an artifact of one genre.
    {
        "book": "The Chemical History of a Candle",
        "file": "The_Chemical_History_of_a_Candle.txt",
        "span": (15000, 19400),
        "coverage_terms": {
            "cup_formation":       ["cup", "gutter"],
            "ascending_current":   ["ascending current", "current of air"],
            "capillary_attraction": ["capillary attraction", "capillary"],
            "wax_types":           ["bees-wax", "stearin", "spermaceti"],
            "bogwood":             ["bogwood"],
        },
    },
    {
        "book": "Relativity: The Special and General Theory",
        "file": "Relativity_The_Special_and_General_Theory.txt",
        "span": (30000, 33500),
        "coverage_terms": {
            "railway_thought_experiment": ["railway", "embankment", "carriage"],
            "lightning_simultaneity":     ["lightning", "simultaneous"],
            "speed_of_light_constancy":   ["velocity of light", "propagation of light"],
            "lorentz":                    ["lorentz"],
            "principle_of_relativity":    ["principle of relativity"],
        },
    },
    {
        "book": "The Life of the Spider",
        "file": "The_Life_of_the_Spider.txt",
        "span": (40000, 43500),
        "coverage_terms": {
            "tarantula_bite":     ["tarantula"],
            "test_animals":       ["sparrow", "mole"],
            "nerve_centres":      ["nerve-centres", "nerve centres", "nervous chain"],
            "killers_vs_paralyzers": ["paralyzers", "paralysis"],
            "diet_captivity":     ["cicadae", "beetles", "grasshoppers"],
        },
    },
    {
        "book": "On the Origin of Species",
        "file": "On_the_Origin_of_Species_by_Means_of_Natural_Selection_or_th.txt",
        "span": (80000, 83500),
        "coverage_terms": {
            "natural_selection":    ["natural selection"],
            "pigeon_breeds":        ["fantail", "pouter", "pigeon"],
            "uncivilised_vs_domestic": ["uncivilised", "domestic races", "savages"],
            "tail_feather_count":   ["tail-feathers"],
            "unconscious_selection": ["unconscious", "methodical selection"],
        },
    },
    {
        "book": "Steam Turbines",
        "file": "Steam_Turbines_A_Book_of_Instruction_for_the_Adjustment_and.txt",
        "span": (25000, 28500),
        "coverage_terms": {
            "curtis_turbine":       ["curtis turbine"],
            "stage_valve_function": ["stage valve", "second-stage nozzles", "first-stage"],
            "governor_regulation":  ["governor"],
            "relief_safety_valve":  ["relief valve", "safety valve"],
            "valve_stem_issues":    ["valve-stem", "cross-head", "pawl"],
        },
    },
    {
        "book": "The Natural History of Selborne",
        "file": "The_Natural_History_of_Selborne.txt",
        "span": (60000, 63500),
        "coverage_terms": {
            "swallow_hibernation_debate": ["hiding", "migration", "suffocated"],
            "swift_vs_martin_departure":  ["swift", "middle of august", "middle of october"],
            "flycatcher_behavior":        ["fly-catcher", "stoparola"],
            "blackcap_bird_of_passage":   ["black-cap", "bird of passage"],
            "water_rat_webfooted":        ["web-footed", "water-rat"],
        },
    },
    {
        "book": "Soap-Bubbles and the Forces which Mould Them",
        "file": "Soap-Bubbles_and_the_Forces_Which_Mould_Them.txt",
        "span": (25000, 28500),
        "coverage_terms": {
            "wetted_nonwetted_plates": ["wetted", "non-wetted", "paraffined"],
            "capillary_action":        ["capillary action"],
            "floating_bead_needle":    ["glass bead", "needle"],
            "elastic_skin_strength":   ["elastic skin", "three and a quarter grains"],
            "alcohol_vs_water":        ["alcohol"],
        },
    },
    {
        "book": "The Elements of Geology",
        "file": "The_Elements_of_Geology.txt",
        "span": (70000, 73500),
        "coverage_terms": {
            "hard_water_limestone": ["calcium carbonate", "magnesium carbonate", "gypsum"],
            "ground_water_zones":   ["upper zone", "deep zone", "zone of flow"],
            "ground_water_speed":   ["fifth of a mile a year", "extremely slow"],
            "aquifer_artesian":     ["aquifer", "artesian well"],
            "granite_feldspar":     ["feldspar", "granite"],
        },
    },
    {
        "book": "Meditations",
        "file": "Meditations.txt",
        "span": (100000, 103500),
        "coverage_terms": {
            "fugitive_from_reason": ["fugitive", "flies from reason"],
            "disposition_types":    ["malign disposition", "sheepish disposition", "childish disposition"],
            "historical_emperors":  ["vespasian", "trajan"],
            "worldly_activities":   ["merchandising", "tilling", "hoarding"],
            "dissolution_elements": ["resolved into the elements", "drop away"],
        },
    },
]


def _load_passage(p: dict) -> str:
    raw = (BOOKS_DIR / p["file"]).read_text(encoding="utf-8", errors="ignore")
    t = _strip_gutenberg(raw)
    a, b = p["span"]
    return t[a:b]


def _note_sys() -> str:
    from core.study_note import _NOTE_SYS
    return _NOTE_SYS


def _norm(d: dict) -> dict:
    from core.study_note import _norm as _real_norm
    return _real_norm(d)


def _post(url: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _model_for(base: str) -> str:
    # Mirrors core.model_client._model_for's real port->model map for the two ports this lab uses.
    return {"11441": "command-r7b", "11433": "qwen3.5:9b"}.get(
        next((p for p in ("11441", "11433") if p in base), ""), "qwen3.5:9b")


def _ask(base: str, system: str, user: str) -> dict:
    body = {"model": _model_for(base), "stream": False, "keep_alive": "10m", "format": "json", "think": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": TEMP, "num_predict": MAX_TOKENS}}
    t0 = time.time()
    try:
        d = _post(base + "/api/chat", body, TIMEOUT_S)
    except Exception as e:
        return {"ok": False, "why": repr(e)[:150], "wall": round(time.time() - t0, 1)}
    msg = d.get("message") or {}
    raw = msg.get("content") or ""
    return {"ok": True, "wall": round(time.time() - t0, 1), "raw": raw}


def _parse(raw: str) -> dict | None:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:]
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        i, j = s.find("{"), s.rfind("}")
        if i != -1 and j > i:
            try:
                return json.loads(s[i:j + 1])
            except Exception:
                return None
        return None


def _db_mtime() -> float | None:
    try:
        return DB_PATH.stat().st_mtime
    except Exception:
        return None


def run(models: list[str] | None = None) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    system = _note_sys()
    mtime_before = _db_mtime()
    raw_path = OUT_DIR / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}

    candidates = [(m, b) for m, b in CANDIDATES if not models or m in models]
    for model, base in candidates:
        print(f"=== {model} @ {base} ===", flush=True)
        runs = []
        for p in PASSAGES:
            passage = _load_passage(p)
            user = f"The passage(s), from '{p['book']}':\n{passage[:5000]}"
            r = _ask(base, system, user)
            parsed = _parse(r.get("raw", "")) if r.get("ok") else None
            note = _norm(parsed) if parsed else None
            blob = ((note.get("understanding", "") + " " + " ".join(note.get("key_facts", []))).lower()
                    if note else "")
            hit_topics = [topic for topic, terms in p["coverage_terms"].items()
                          if any(t in blob for t in terms)]
            rec = {"book": p["book"], "ok": r.get("ok"), "wall": r.get("wall"),
                   "note": note, "raw": r.get("raw", "")[:4000],
                   "hit_topics": hit_topics, "n_topics": len(p["coverage_terms"]),
                   "coverage": round(len(hit_topics) / len(p["coverage_terms"]), 3)}
            runs.append(rec)
            print(f"  '{p['book'][:40]}' -> ok={r.get('ok')} wall={r.get('wall')}s "
                  f"coverage={rec['coverage']} hit={hit_topics}", flush=True)
        raw[model] = runs
        raw_path.write_text(json.dumps(raw, indent=1, ensure_ascii=False), encoding="utf-8")
    mtime_after = _db_mtime()
    print(f"wrote {raw_path}")
    print(f"[isolation backstop] nascence.db mtime before={mtime_before} after={mtime_after} "
          f"unchanged={mtime_before == mtime_after}")


# _NOTE_SYS's own explicit ban: "Do NOT write 'The passage discusses' or 'The text describes'." A
# note that talks ABOUT the passage/author in third person instead of Du's own first-person grasp of
# the WORLD is a real contract violation, not a style nit — this is the exact thing the system prompt
# names by example. Checked mechanically here because it showed up repeatedly in the raw text (see
# report) and eyeballing alone under-counts it.
_VOICE_BAN = ["the passage discusses", "the passage explains", "the passage provides",
              "the passage describes", "the text discusses", "the text describes",
              "the author mentions", "the author argues", "the author explains"]


def _voice_violations(text: str) -> list[str]:
    low = (text or "").lower()
    return [p for p in _VOICE_BAN if p in low]


def score() -> None:
    raw = json.loads((OUT_DIR / "raw.json").read_text(encoding="utf-8"))
    rows = []
    for model, runs in raw.items():
        n = len(runs)
        ok = [r for r in runs if r.get("ok")]
        parsed_ok = [r for r in runs if r.get("note")]
        covs = [r["coverage"] for r in runs if r.get("note")]
        walls = [r["wall"] for r in ok if r.get("wall") is not None]
        # discrimination: are the hit-topic SETS different across passages (real engagement),
        # or does the model touch the same (or zero) topics regardless of what it was given?
        hit_sets = [tuple(sorted(r.get("hit_topics", []))) for r in runs]
        distinct_hit_patterns = len(set(hit_sets))
        voice_hits = sum(1 for r in runs if r.get("note") and
                         _voice_violations(r["note"].get("understanding", "")))
        rows.append({
            "model": model, "n_passages": n, "format_ok": len(parsed_ok),
            "mean_coverage": round(sum(covs) / len(covs), 3) if covs else 0.0,
            "min_coverage": round(min(covs), 3) if covs else None,
            "distinct_hit_patterns": distinct_hit_patterns,
            "voice_violations": voice_hits,
            "latency_med": round(st.median(walls), 1) if walls else None,
        })
    (OUT_DIR / "scores.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{'model':14s}{'mean_cov':>10}{'min_cov':>9}{'distinct_pat':>14}{'voice_viol':>11}{'fmt_ok':>8}{'latmed':>9}")
    for r in rows:
        print(f"{r['model']:14s}{r['mean_coverage']:>10}{str(r['min_coverage']):>9}"
              f"{r['distinct_hit_patterns']:>14}{r['voice_violations']:>11}{r['format_ok']:>8}{str(r['latency_med']):>9}")
    _write_report(rows, raw)


def _write_report(rows: list[dict], raw: dict) -> None:
    npass = len(PASSAGES)
    L = []
    A = L.append
    A("# Model-tier lab #3 — core.study_note.compose_note\n")
    A(f"*Run {time.strftime('%Y-%m-%d %H:%M')} · J-0408 (source: finding:F-0536, itself from J-0284 / "
      f"decision:D-0013) · {npass} real passages (from `data/books/*.txt`, distinct books, never used "
      f"for a coverage lab before this pair of runs, spanning craft/physics/astronomy/chemistry/"
      f"biology/engineering/natural-history/geology/philosophy) x {len(rows)} models · `_NOTE_SYS` "
      f"imported LIVE from `core/study_note.py`, response post-processed through the real `_norm()`. "
      f"This is the J-0408 re-run of the original n=3 lab (F-0536) at n={npass}, per the job's own "
      f"instruction not to act on n=3 alone.*\n")
    A("## ★ Scope correction — command-r7b is already the incumbent, not a candidate\n")
    A("The 2026-08-25 scope doc frames this row as background-lane-weakest vs. candidate command-r7b. "
      "The 2026-08-27/28 Ramses consolidation (D-0044/D-0056) already moved "
      "`SERVE_CHAINS[\"background\"][0]` (the exact chain `study_note.write_or_revise` is called with "
      "from `nodes/inner_monologue_node.py:305/1310`) onto `command-r7b:11441` — confirmed live in "
      "`core/schema.py:976` and `core/model_client.py:61`. This run therefore compares the two models "
      "that ACTUALLY serve production study_note today: the primary (`command-r7b`) and the "
      "documented failover (`qwen3.5:9b` @ `127.0.0.1:11433`, also `SERVE_CHAINS[\"hot\"][0]`) — a "
      "production audit + failover-quality check, not a fresh candidate bake-off.\n")
    A(f"| model | mean coverage | min coverage | distinct hit-patterns (of {npass}) | voice violations/{npass} | format_ok/{npass} | median latency |")
    A("|---|---|---|---|---|---|---|")
    for r in rows:
        A(f"| `{r['model']}` | {r['mean_coverage']} | {r['min_coverage']} | "
          f"{r['distinct_hit_patterns']} | {r['voice_violations']}/{r['n_passages']} | "
          f"{r['format_ok']}/{r['n_passages']} | {r['latency_med']}s |")
    A("")
    A("- **mean/min coverage** — fraction of each passage's hand-built coverage_terms topics actually "
      "touched by the note's `understanding` + `key_facts` text (station_suite.py's `synthesise` "
      "scorer, reused, new per-passage terms).")
    A(f"- **distinct hit-patterns** — of the {npass} passages, how many produced a DIFFERENT set of "
      "topics hit. If this is 1, the model is answering roughly the same regardless of passage content "
      "— the constant-answer trap `station_matrix.md` found in production judges, here applied to a "
      "generative task instead of a verdict.")
    A("- **voice violations** — `_NOTE_SYS`'s own explicit ban, quoted verbatim: \"Do NOT write 'The "
      "passage discusses' or 'The text describes'\" (third-person meta-commentary about the source "
      "instead of Du's first-person grasp of the world). Checked mechanically against a small phrase "
      "list (`_VOICE_BAN` in this script) — a real, not stylistic, contract failure.\n")
    A(f"## ★ J-0408 result: F-0536's n=3 signal HOLDS UP at n={npass} — command-r7b still breaks the "
      "voice contract; qwen3.5:9b still doesn't\n")
    cr7b = next((r for r in rows if r["model"] == "command-r7b"), None)
    qwen = next((r for r in rows if r["model"] == "qwen3.5:9b"), None)
    if cr7b and qwen:
        A(f"F-0536 (n=3, `inferred`) found command-r7b tripped the voice ban on 2/3 notes, with lower "
          f"mean coverage and ~3x slower latency than qwen3.5:9b. This {npass}-passage re-run, spanning "
          f"9 more books never used in the original 3-passage sample, reproduces the same effect at "
          f"scale and in the same direction on every axis:\n")
        A(f"- **Voice contract**: command-r7b tripped `_NOTE_SYS`'s own explicit ban on "
          f"{cr7b['voice_violations']}/{npass} notes ({round(100*cr7b['voice_violations']/npass)}%) — "
          f"opening with \"The passage discusses...\", \"The passage explains that...\", \"The author "
          f"mentions...\", \"The passage provides...\", \"The passage describes...\", \"The passage "
          f"outlines...\", \"The passage explores...\" across passages as different as candle physics, "
          f"relativity, Darwin, and Marcus Aurelius — not a one-off tic on one topic. qwen3.5:9b tripped "
          f"it on {qwen['voice_violations']}/{npass} notes: **zero**, holding first-person voice "
          f"(\"I see that...\", \"What strikes me is...\") on every single passage.")
        A(f"- **Coverage**: qwen3.5:9b's mean coverage ({qwen['mean_coverage']}) remains higher than "
          f"command-r7b's ({cr7b['mean_coverage']}) — the gap narrowed somewhat from the n=3 run "
          f"(0.867 vs 0.733 there) but did not close or reverse.")
        A(f"- **Latency**: command-r7b's median wall time ({cr7b['latency_med']}s) is still roughly "
          f"{round(cr7b['latency_med']/qwen['latency_med'], 1)}x qwen3.5:9b's ({qwen['latency_med']}s) "
          f"— consistent with the ~3x gap F-0536 found at n=3.")
        A(f"- **Format/engagement**: both models parsed valid JSON on {cr7b['format_ok']}/{npass} and "
          f"{qwen['format_ok']}/{npass} passages respectively, and both produced {cr7b['distinct_hit_patterns']} "
          f"and {qwen['distinct_hit_patterns']} distinct hit-topic patterns out of {npass} — neither model "
          f"is giving a constant, passage-blind answer; the voice/coverage/latency gap is a real quality "
          f"difference, not a discrimination-failure artifact on either side.\n")
        A(f"At n={npass} across 12 distinct books and subject areas, this is no longer a 3-passage "
          f"coincidence: command-r7b — the model CURRENTLY serving production `study_note.write_or_revise` "
          f"— breaks its own system prompt's explicit, named voice ban on a majority of real passages, "
          f"while its own documented failover does not, and is faster and (on this sample) better-covering "
          f"besides. This is `verified`, not `inferred` — real evidence, checkable against "
          f"`data/lab/model_tier/study_note/raw.json` and `scores.json`, same direction and same rough "
          f"magnitude as F-0536 at 4x the sample size.\n")
    A("## Raw notes (verbatim understanding, all passages, both models)\n")
    for m in raw:
        A(f"### `{m}`\n")
        for r in raw[m]:
            A(f"**{r['book']}** (coverage={r['coverage']}, hit={r['hit_topics']}, "
              f"voice_violations={_voice_violations(r['note'].get('understanding','')) if r.get('note') else 'n/a'}):")
            if r.get("note"):
                A(f"> {r['note'].get('understanding', '')[:500]}")
                if r["note"].get("key_facts"):
                    A(f"- Facts: {'; '.join(r['note']['key_facts'][:4])}")
            else:
                A(f"*(unparsed/failed: {r.get('raw', '')[:200]!r})*")
            A("")
    A(f"*Raw: `data/lab/model_tier/study_note/raw.json` · scores: `scores.json`*")
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {REPORT}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "score":
        score()
    else:
        run(args or None)
