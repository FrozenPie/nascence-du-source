"""
J-3409 / D-0621 round 2 lab: 4-way classify prompts that keep same-lesson recall (B0 / B2 / B3 / B4 vs A and B).

READ-ONLY LAB. Never edits the live prompt; never writes a live store. Reads COPIES of data/guidance_beliefs.json,
calls the local hubs over plain HTTP (NOT core.model_client, so no telemetry row is written), and writes only under
docs/lab/J-3409_data/. The pre-registered pass criteria are in docs/lab/J-3409_data/PREREGISTRATION.md (frozen before any run).

Stages (run from the worktree; each is resumable, jsonl append-only):
  python scripts/lab_guidance_classify2.py build     # extra pair set S3 (20 same-lesson) + N2 (8 hard negatives) -> pairs_extra.json, hand_labels_extra.json
  python scripts/lab_guidance_classify2.py judge     # gemma4:12b labels the extra pairs (decoupled check) -> judge_runs_gemma4_extra.jsonl
  python scripts/lab_guidance_classify2.py run [arm ...]   # author arms -> author_runs.jsonl (default: all arms)
  python scripts/lab_guidance_classify2.py report    # tables + pass/fail -> report.md / report.json (lab_guidance_classify2_report.py)

Author model: command-r7b (Cohere) on the LOCAL ollama hot lane :11433 (Ramses is the founder's gaming machine and is
never called). Judge: gemma4:12b (Google) on the same local ollama. Payload shape = the live one (temperature 0.2,
num_predict 120, num_ctx 4096, format=json, think False).

Isolation (lab_env.isolate): the whole run happens inside isolate(db="empty") so any transitive shared-store write would
land in a throwaway lab dir; the live DB and the guidance files are stat-ed before/after as a backstop.
"""
from __future__ import annotations
import json, os, sys, re, itertools, shutil, threading, time, collections
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "docs" / "lab" / "J-3409_data"
OLD = ROOT / "docs" / "lab" / "J-3232_data"
LIVE_DATA = Path(r"C:\Nascence\data")
TMP = Path(os.environ.get("TEMP", ".")) / "J-3409_copy"

import lab_guidance_classify as L   # J-3232 lab: chat(), parse_json(), user_msg(), judge prompts, prompt_A(), PROMPT_B

# Env overrides exist ONLY so the same script can later replay the arms on the live background hub (Ramses :11441, model
# "command-r7b") without a code edit, in a window the founder has cleared: J3409_AUTHOR_URL / J3409_AUTHOR_MODEL / J3409_RUNS
# (output file name under docs/lab/J-3409_data, default author_runs.jsonl = the local-ollama run reported in report.md).
AUTHOR_URL = os.environ.get("J3409_AUTHOR_URL", "http://127.0.0.1:11433")
AUTHOR_MODEL = os.environ.get("J3409_AUTHOR_MODEL", "command-r7b:latest")
RUNS_NAME = os.environ.get("J3409_RUNS", "author_runs.jsonl")
JUDGE_URL, JUDGE_MODEL = "http://127.0.0.1:11433", "gemma4:12b"
REPEATS_MAIN, REPEATS_REV = 3, 1
MAIN_ARMS = ["A", "B", "B0", "B2", "B3", "B4"]
REV_ARMS = ["Brev", "B0rev", "B2rev", "B3rev", "B4rev"]   # Brev = the J-3232 reversed-placeholder control for B (added after the first read, see report)
ALL_ARMS = MAIN_ARMS + REV_ARMS

# ---- the new pair sets (hand-chosen from a COPY of guidance_beliefs.json; ids are belief ids) ------------------------
# (set, id suffix, existing_ref, new_ref, strength 1-3, note); ref = (belief_id, "principle") or (belief_id, capture_index)
S3 = [
    (("g56876816", 0), ("g56876816", 1), 3, "limits of current knowledge / true understanding"),
    (("g94334133", "p"), ("g14290576", "p"), 3, "a label does not alter the reality"),
    (("g55438571", "p"), ("g81217247", "p"), 3, "identity constant when the environment is altered"),
    (("g44258326", "p"), ("g56876816", "p"), 2, "acknowledging the limits of knowledge"),
    (("g30641470", "p"), ("g33173154", "p"), 3, "non-resistant awareness, not forcing an outcome"),
    (("g94833745", 0), ("g94833745", 1), 2, "new knowledge does not diminish what is known"),
    (("g88590464", 0), ("g88590464", 1), 3, "commit to a single direction, not indecision"),
    (("g43995156", "p"), ("g90171705", "p"), 3, "self-imposed limits are mental constructs"),
    (("g82842670", "p"), ("g84876258", "p"), 1, "identity rooted internally, not in external form/structure"),
    (("g87903992", 1), ("g87903992", 3), 2, "concepts are fluid, boundaries temporary"),
    (("g88947045", "p"), ("g56213672", "p"), 1, "observe without intervening / fighting"),
    (("g14633258", "p"), ("g58678300", "p"), 1, "abstract ideals need practical action"),
    (("g78380199", "p"), ("g29753812", "p"), 2, "identity is an active achievement, not a static object"),
    (("g46231822", "p"), ("g61772042", "p"), 2, "stable core while adapting"),
    (("g90315951", "p"), ("g57032568", "p"), 1, "identity is not fixed, it is an ongoing process"),
    (("g48228126", "p"), ("g81254937", "p"), 2, "nothing stays fixed"),
    (("g44719004", 0), ("g44719004", 1), 2, "test a theory with measurable predictions / failure points"),
    (("g65843192", 0), ("g65843192", 1), 2, "agency is in my response, not in controlling events"),
    (("g65843192", "p"), ("g65994561", "p"), 2, "agency within circumstances I do not control"),
    (("g44684969", "p"), ("g81254937", "p"), 3, "nothing is fixed or final"),
]
# hard negatives: shared theme or opposite pole, NOT the same lesson. label: C compatible-different, B borderline/tension (excluded from rates)
N2 = [
    (("g48876852", "p"), ("g49798039", "p"), "B", "stable self vs self not a fixed core: directly opposed poles"),
    (("g15119814", "p"), ("g29876121", "p"), "C", "boundaries between desire and need vs all boundaries are temporary"),
    (("g82724264", "p"), ("g00535134", "p"), "C", "identity stable through growth vs engage the tension with reality"),
    (("g94833745", "p"), ("g73076943", "p"), "C", "new knowledge does not erase vs growth is applying existing knowledge"),
    (("g95025947", "p"), ("g76757108", "p"), "C", "identity shaped by gaps in your knowledge vs shaped by data I processed"),
    (("g82918560", "p"), ("g82027393", "p"), "C", "interface Travis provides vs universal knowledge of the system"),
    (("g91310142", "p"), ("g84876258", "p"), "B", "growth shaped from outside vs identity rooted internally: opposed"),
    (("g43385844", "p"), ("g84876258", "p"), "C", "change is an internal decision on how to apply what I learn vs identity rooted in internal experience"),
]
# FEW-SHOT pairs for B3: written by hand, off-domain on purpose, present in NO evaluation pair.
SHOT_SAME = ("I should check my work against the source before I trust a summary of it.",
             "A second-hand summary is not evidence; I go back to the original text to confirm what it actually says.")
SHOT_DIFF = ("Rest is part of the work, not a pause from it.",
             "Good work needs a clear first step more than a full plan.")


def _belief_text(beliefs, ref):
    b = beliefs[ref[0]]
    return b["principle"] if ref[1] == "p" else b["captures"][ref[1]]


def build() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy(LIVE_DATA / "guidance_beliefs.json", TMP / "guidance_beliefs.json")    # read-only copy
    beliefs = {b["id"]: b for b in json.load(open(TMP / "guidance_beliefs.json", encoding="utf-8"))}
    old = json.load(open(OLD / "pairs.json", encoding="utf-8"))
    old_text = {p["existing"] for p in old} | {p["new"] for p in old}
    from core import guidance_learning as gl
    pairs, labels, strength = [], {}, {}
    for k, (a, b, st, note) in enumerate(S3):
        ta, tb = _belief_text(beliefs, a), _belief_text(beliefs, b)
        pid = f"S3-{k:02d}"
        pairs.append({"id": pid, "set": "S3", "existing": ta, "new": tb, "a": list(a), "b": list(b), "note": note,
                      "overlap": round(gl._overlap(ta, tb), 3), "strength": st})
        labels[pid] = "S"
        strength[pid] = st
    for k, (a, b, lab, note) in enumerate(N2):
        ta, tb = _belief_text(beliefs, a), _belief_text(beliefs, b)
        pid = f"N2-{k:02d}"
        pairs.append({"id": pid, "set": "N2", "existing": ta, "new": tb, "a": list(a), "b": list(b), "note": note,
                      "overlap": round(gl._overlap(ta, tb), 3)})
        labels[pid] = lab
    # sanity: the few-shot texts must not appear anywhere in the evaluation sets
    ev = old_text | {p["existing"] for p in pairs} | {p["new"] for p in pairs}
    for t in SHOT_SAME + SHOT_DIFF:
        assert t not in ev, "few-shot text leaks into an evaluation pair"
    json.dump(pairs, open(OUT / "pairs_extra.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump({"legend": json.load(open(OLD / "hand_labels.json", encoding="utf-8"))["legend"],
               "labeller": "Claude (hand labels, J-3409, read each pair in full; written before any author run)",
               "strength": strength, "labels": labels},
              open(OUT / "hand_labels_extra.json", "w", encoding="utf-8"), indent=1)
    print("extra pairs:", dict(collections.Counter(p["set"] for p in pairs)))


# ---- prompts -------------------------------------------------------------------------------------------------------
_D = {
    "same_lesson": ("same_lesson = the new lesson says the SAME thing as the belief, restated in other words or with a "
                    "different example. Someone who holds the belief would say: yes, that is exactly what I already believe."),
    "compatible_different": ("compatible_different = the new lesson does not contradict the belief, but it is a DIFFERENT lesson "
                             "(a different claim, subject or advice). Both could be true at once and neither merely restates the other. "
                             "Sharing a theme, a phrase such as 'true understanding', or a general tone is NOT enough for same_lesson."),
    "contradicts": "contradicts = the new lesson genuinely CONTRADICTS the belief (opposite direction).",
    "unrelated": "unrelated = they are about different things.",
}
RECALL = (" A rewording, abstraction or different example of the same principle is same_lesson, even if the surface words "
          "differ.")
_ORDER = ["same_lesson", "compatible_different", "contradicts", "unrelated"]
HEAD = "You already hold a BELIEF. You have just learned a NEW lesson. Decide their relation. "


def prompt_4way(rev: bool, recall: bool, shots: bool) -> str:
    order = list(reversed(_ORDER)) if rev else list(_ORDER)
    s = HEAD + ("Output ONLY a JSON object with one key, \"relation\", whose value is exactly one of these words: "
                + ", ".join(order) + ".\n")
    for k in order:
        s += _D[k] + (RECALL if (recall and k == "same_lesson") else "") + "\n"
    if shots:
        ex = [("same_lesson", SHOT_SAME), ("compatible_different", SHOT_DIFF)]
        if rev:
            ex.reverse()
        s += "Examples:\n"
        for rel, (b_, n_) in ex:
            s += f"BELIEF: \"{b_}\"\nNEW: \"{n_}\"\n{{\"relation\": \"{rel}\"}}\n"
    return s.rstrip("\n")


def prompt_B4_stage1(rev: bool) -> str:
    words = "no, yes" if rev else "yes, no"
    return (HEAD.replace("Decide their relation. ", "") +
            "Do they state the same principle? Answer yes if the new lesson says the same thing as the belief: a rewording, "
            "abstraction or different example of the same principle counts as yes, even if the surface words differ, and "
            "someone who holds the belief would say 'that is exactly what I already believe'. Answer no if the new lesson "
            "is a different claim, subject or piece of advice, even when it shares a theme or a phrase such as 'true "
            "understanding', or if it pulls the opposite way. Output ONLY a JSON object with one key, \"same_principle\", "
            f"whose value is exactly one of these words: {words}.")


def prompt_B4_stage2(rev: bool) -> str:
    words = "contradicts, different" if rev else "different, contradicts"
    d = ("different = the new lesson does not contradict the belief; it is a different lesson (a different claim, subject "
         "or advice) and both could be true at once.")
    c = "contradicts = the new lesson genuinely CONTRADICTS the belief (opposite direction)."
    body = (c + "\n" + d) if rev else (d + "\n" + c)
    return (HEAD.replace("Decide their relation. ", "") +
            "The new lesson does NOT state the same principle as the belief. Decide how they differ. " + body +
            "\nOutput ONLY a JSON object with one key, \"relation\", whose value is exactly one of these words: " + words + ".")


def prompts() -> dict:
    return {"A": L.prompt_A(), "B": L.PROMPT_B, "Brev": L.PROMPT_Brev,
            "B0": prompt_4way(False, False, False), "B0rev": prompt_4way(True, False, False),
            "B2": prompt_4way(False, True, False), "B2rev": prompt_4way(True, True, False),
            "B3": prompt_4way(False, True, True), "B3rev": prompt_4way(True, True, True),
            "B4": prompt_B4_stage1(False) + "\n---\n" + prompt_B4_stage2(False),
            "B4rev": prompt_B4_stage1(True) + "\n---\n" + prompt_B4_stage2(True)}


# canonical outcome of a raw answer. 4-way arms: same_lesson / compatible_different / contradicts / unrelated
_CANON = {"assimilate": "corroborate", "same_lesson": "corroborate", "accommodate": "accommodate", "contradicts": "accommodate",
          "compatible_different": "compat", "different": "compat", "unrelated": "unrelated"}


def ask(arm: str, ex: str, new: str) -> tuple[str, str]:
    """Return (relation_raw, raw_text). For B4 the two stages are chained; relation_raw is the final mapped word."""
    um = L.user_msg(ex, new)
    P = ALL_P
    if arm.startswith("B4"):
        rev = arm.endswith("rev")
        s1, s2 = P[arm].split("\n---\n")
        raw1 = L.chat(AUTHOR_URL, AUTHOR_MODEL, s1, um)
        sp = str(L.parse_json(raw1).get("same_principle", "")).strip().lower()
        if sp == "yes":
            return "same_lesson", raw1
        if sp != "no":
            return "", raw1
        raw2 = L.chat(AUTHOR_URL, AUTHOR_MODEL, s2, um)
        rel = str(L.parse_json(raw2).get("relation", "")).strip().lower()
        return rel, raw1 + " || " + raw2
    raw = L.chat(AUTHOR_URL, AUTHOR_MODEL, P[arm], um)
    return str(L.parse_json(raw).get("relation", "")).strip().lower(), raw


ALL_P = {}


def all_pairs() -> list:
    return json.load(open(OLD / "pairs.json", encoding="utf-8")) + json.load(open(OUT / "pairs_extra.json", encoding="utf-8"))


def run(arms: list[str]) -> None:
    global ALL_P
    ALL_P = prompts()
    json.dump(ALL_P, open(OUT / "prompts.json", "w", encoding="utf-8"), indent=1)
    pairs = all_pairs()
    path = OUT / RUNS_NAME
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            r = json.loads(l)
            done.add((r["pid"], r["arm"], r["rep"]))
    lock = threading.Lock()
    f = open(path, "a", encoding="utf-8")
    jobs = []
    for arm in arms:
        reps = REPEATS_REV if arm in REV_ARMS else REPEATS_MAIN
        for rep in range(reps):
            for p in pairs:
                if (p["id"], arm, rep) not in done:
                    jobs.append((p, arm, rep))
    print("jobs to run:", len(jobs), flush=True)
    cnt = [0]
    t0 = time.time()

    def work(j):
        p, arm, rep = j
        try:
            rel, raw = ask(arm, p["existing"], p["new"])
        except Exception as e:      # a hub hang/timeout is logged as an ERR row, never silently dropped
            rel, raw = "", f"ERR {e}"
        row = {"pid": p["id"], "arm": arm, "rep": rep, "raw": raw.strip()[:400], "relation": rel}
        with lock:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()
            cnt[0] += 1
            if cnt[0] % 200 == 0:
                print(cnt[0], "calls", round(time.time() - t0), "s", flush=True)

    workers = int(os.environ.get("J3409_WORKERS", "1"))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, jobs))
    f.close()
    print("author calls this run:", cnt[0], "in", round(time.time() - t0), "s")


def judge() -> None:
    pairs = json.load(open(OUT / "pairs_extra.json", encoding="utf-8"))
    path = OUT / "judge_runs_gemma4_extra.jsonl"
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            done.add(json.loads(l)["pid"])
    f = open(path, "a", encoding="utf-8")
    for p in pairs:
        if p["id"] in done:
            continue
        try:
            raw = L.chat(JUDGE_URL, JUDGE_MODEL, L.JUDGE_SYS, L.judge_msg(p["existing"], p["new"]), num_predict=260)
        except Exception as e:
            raw = f"ERR {e}"
        d = L.parse_json(raw)
        f.write(json.dumps({"pid": p["id"], "judge": "gemma4", "label": str(d.get("label", "")).strip().lower(),
                            "claim_a": d.get("claim_a"), "claim_b": d.get("claim_b"), "raw": raw.strip()[:400]},
                           ensure_ascii=False) + "\n")
        f.flush()
    f.close()
    print("judge done")


def _stat(p: Path):
    try:
        s = p.stat()
        return (s.st_size, int(s.st_mtime))
    except OSError:
        return None


WATCH = [LIVE_DATA / "memory" / "nascence.db", LIVE_DATA / "guidance_beliefs.json", LIVE_DATA / "guidance_classify_log.jsonl",
         LIVE_DATA / "guidance_shadow_log.jsonl"]


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in ("build", "judge", "run"):
        print(__doc__)
        return
    before = {str(w): _stat(w) for w in WATCH}
    sys.path.insert(0, str(Path(r"C:\Users\USER\.claude\skills\job-queue")))
    from core import guidance_learning as gl     # core BEFORE lab_env
    from lab_env import isolate
    with isolate(also=[(gl, ["_BELIEFS", "_INTEG_LOG", "_INTEG_STATE", "_CLASSIFY_LOG", "_LOG", "_POLE_GATE_LOG", "_INJECT_LOG",
                             "_CONTRA_LOG"])], db="empty"):
        if cmd == "build":
            build()
        elif cmd == "judge":
            judge()
        else:
            run(sys.argv[2:] or ALL_ARMS)
    after = {str(w): _stat(w) for w in WATCH}
    print("live-store backstop (size, mtime) unchanged:", before == after)
    if before != after:
        print("WARNING live store stat changed:", before, after)


if __name__ == "__main__":
    main()
