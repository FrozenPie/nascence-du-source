"""J-3440 (F-4070, object_epistemic_loop): how often is a recorded object "hypothesis" really an intention?

READ-ONLY.  Opens data/world_substrate.json, data/world_substrate.pre_archive_20261018_184006.json and
data/monologue_log.jsonl for reading only; writes only docs/lab/J-3440_data/ under this worktree.  Zero LLM.

DECLARED BEFORE ANY RESULT WAS LOOKED AT (no tuning to the outcome):

  PATTERN  core.object_hypothesis.DEONTIC_PATTERN, the deontic / intention frame, matched on a lowercased clause:
     "i should / shouldn't / ought to / must / need to / have to / had better / shall / will / won't / plan to /
      intend to / mean to / aim to / hope to / would like to / want to (not 'want to know/understand/find out/
      learn/see whether|if|what|how|why')", "i'll / i'd like to / i'd better / i'd rather", "i'm going to / gonna",
      "maybe|perhaps|possibly [,] i could|can|might|may|should|will|'ll|ought", "let me / let us / let's",
      "(just) let the|it|this|that|these|those|them", "we|you|one should", "should|shall i|we", "what if i|we".
     Deliberately NOT a frame: a bare "i could", "i can", "i might" (they also open claims: "i can tell it's rusted").
     The pattern text is asserted equal to the string pasted here, so it cannot drift to fit the data:
  PATTERN_TEXT_SHA = see PATTERN_ASSERT below.

  DEFINITIONS
     opens   : the frame starts in the first 3 words of the stored hypothesis clause (the "Maybe I should ..." case).
     inside  : the frame starts BEFORE the first claim word of the clause (claim word sits inside the intention).
               This is exactly what the extract gate removes: it keeps only the clause part before the frame.
     excluded: extractor hits (gate OFF) that the gate (ON) no longer returns for the same object.
  CORPORA
     A  data/world_substrate.json, every stored inference (4 on 2026-11-05).
     B  data/world_substrate.pre_archive_20261018_184006.json, 1476 whole-text legacy inferences; each is re-read
        clause-scoped through extract() (gate OFF = the extractor as live today) against ITS OWN object.
     C  data/monologue_log.jsonl (thought + intention, exactly the text the node feeds extract), replayed against
        every distinct (object_class, name) in the live store whose anchor word occurs in the row. Upper bound on
        what the extractor would record: the live node also needs the object looked at within 1800 s.
  THRESHOLDS (share of extractor hits, B and C separately, then pooled)
     excluded >= 5 %        -> MATERIAL: the extract exclusion is worth its flag.
     0.5 % <= excluded < 5 % -> PRESENT: build, but report it as a rare leak.
     excluded < 0.5 %       -> NEGLIGIBLE: build only the intervention_test guard.
  PRECISION (hand-read, no cherry-picking): the first 30 excluded hits in file order are printed in full; a
     false exclusion is one where the hit also contained a real claim about the object that the gate dropped.
     (The gate keeps a claim that sits BEFORE the frame, so only a claim wholly inside an intention is dropped.)
  GUARD: among extractor hits, count those whose intervention_test() returns candidates with the guard OFF and
     the number the guard (ON) removes; guard must change NOTHING on hits that carry no frame.

  python scripts/_scan_J-3440_deontic_frames.py            -> prints the report, writes docs/lab/J-3440_data/scan.json
"""
import json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core
assert Path(core.__file__).resolve().is_relative_to(HERE), core.__file__
from core import object_hypothesis as oh

PATTERN_ASSERT = (
    r"\bi\s+(?:should|shouldn't|ought\s+to|must|need\s+to|have\s+to|had\s+better|shall|will|won't|"
    r"plan\s+to|intend\s+to|mean\s+to|aim\s+to|hope\s+to|would\s+like\s+to|"
    r"want\s+to(?!\s+(?:know|understand|find\s+out|learn|see\s+(?:whether|if|what|how|why))))\b"
    r"|\bi'(?:ll|d\s+like\s+to|d\s+better|d\s+rather)\b"
    r"|\bi(?:'m|\s+am)\s+(?:going\s+to|gonna)\b|\bgonna\b|\bi\s+wanna\b"
    r"|\b(?:maybe|perhaps|possibly)\s*,?\s+i\s+(?:could|can|might|may|should|will|'ll|ought)\b"
    r"|\blet(?:'s|\s+me|\s+us)\b"
    r"|\b(?:just\s+)?let\s+(?:the|it|this|that|these|those|them)\b"
    r"|\b(?:we|you|one)\s+should\b|\bshould\s+(?:i|we)\b|\bshall\s+(?:i|we)\b|\bwhat\s+if\s+(?:i|we)\b"
)
assert oh.DEONTIC_PATTERN == PATTERN_ASSERT, "module pattern drifted from the declared pattern"

LIVE = Path(os.environ.get("J3440_DATA", r"C:\Nascence\data"))
OUT = HERE / "docs" / "lab" / "J-3440_data"
GATE_TS = time.mktime(time.strptime("2026-10-18 18:40:06", "%Y-%m-%d %H:%M:%S"))


def set_flags(extract_on: bool, guard_on: bool):
    os.environ["NASCENCE_DEONTIC_EXTRACT_GATE"] = "1" if extract_on else "0"
    os.environ["NASCENCE_DEONTIC_TEST_GUARD"] = "1" if guard_on else "0"


def frame_info(text: str) -> dict:
    """Per-clause frame facts for a stored/produced claim text."""
    out = {"frame": False, "opens": False, "inside": False}
    for c in oh.clauses(text):
        low = c.lower()
        fs = oh.deontic_frame_start(low)
        if fs is None:
            continue
        out["frame"] = True
        if len(re.findall(r"[a-z']+", low[:fs])) < 3:
            out["opens"] = True
        m = oh._CLAIM_RE.search(low)
        if m and fs <= m.start():
            out["inside"] = True
    return out


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def objects_of(d):
    return d if isinstance(d, dict) else {}


def pct(a, b):
    return round(100.0 * a / b, 2) if b else 0.0


def verdict(share):
    return "MATERIAL" if share >= 5 else ("PRESENT" if share >= 0.5 else "NEGLIGIBLE")


def cands(claim, cls, name, loc, fam):
    return oh.intervention_test(claim, cls, name, loc, families=fam)


def main():
    fam = oh._families()
    rep = {"declared": "see header", "families_known": len(fam)}
    excluded_examples = []

    # ---- A: live store
    live = objects_of(load(LIVE / "world_substrate.json"))
    A = []
    for oid, o in live.items():
        for i in (o.get("inferences") or []):
            h = i.get("hypothesis", "")
            fi = frame_info(h)
            set_flags(False, False)
            c_off = cands(h, o.get("object_class", ""), o.get("name", ""), o.get("location", ""), fam)
            set_flags(False, True)
            c_on = cands(h, o.get("object_class", ""), o.get("name", ""), o.get("location", ""), fam)
            set_flags(True, True)
            ex_on = oh.extract(h, o.get("object_class", ""), o.get("name", ""))
            A.append({"obj": oid, "hyp": h, **fi, "cands_guard_off": [(c["verb"], c["cue"]) for c in c_off],
                      "cands_guard_on": [(c["verb"], c["cue"]) for c in c_on], "extract_gate_on_keeps": bool(ex_on)})
    rep["A_live"] = {"n": len(A), "with_frame": sum(a["frame"] for a in A), "rows": A}

    # ---- B: pre-archive, clause-scoped through extract()
    pre = objects_of(load(LIVE / "world_substrate.pre_archive_20261018_184006.json"))
    nB = nHit = nExcl = nFrameHit = nOpens = nInside = candOff = candOn = 0
    guard_changes_nonframe = 0
    for oid, o in pre.items():
        cls, nm, loc = o.get("object_class", ""), o.get("name", ""), o.get("location", "")
        for i in (o.get("inferences") or []):
            nB += 1
            h = i.get("hypothesis", "")
            set_flags(False, False)
            r_off = oh.extract(h, cls, nm)
            if not r_off:
                continue
            nHit += 1
            claim = r_off[0]
            fi = frame_info(claim)
            set_flags(False, False)
            c_off = cands(claim, cls, nm, loc, fam)
            set_flags(False, True)
            c_on = cands(claim, cls, nm, loc, fam)
            set_flags(True, True)
            r_on = oh.extract(h, cls, nm)
            nFrameHit += fi["frame"]; nOpens += fi["opens"]; nInside += fi["inside"]
            candOff += bool(c_off); candOn += bool(c_on)
            if not fi["frame"] and c_off != c_on:
                guard_changes_nonframe += 1
            if not r_on:
                nExcl += 1
                excluded_examples.append({"corpus": "B", "obj": oid, "claim": claim, "cands_off": [(c["verb"], c["cue"]) for c in c_off]})
    rep["B_pre_archive"] = {"inferences": nB, "extractor_hits": nHit, "with_frame": nFrameHit, "opens": nOpens,
                            "inside": nInside, "excluded_by_gate": nExcl, "hits_with_candidates_guard_off": candOff,
                            "hits_with_candidates_guard_on": candOn, "guard_changed_a_frameless_hit": guard_changes_nonframe,
                            "excluded_share_pct": pct(nExcl, nHit), "verdict": verdict(pct(nExcl, nHit))}

    # ---- C: monologue replay against distinct live (class, name)
    pairs = {}
    for o in live.values():
        pairs[(o.get("object_class", ""), o.get("name", ""))] = o.get("location", "")
    anchor_pairs = {}
    for (cls, nm) in pairs:
        for a in oh.object_anchors(cls, nm):
            anchor_pairs.setdefault(a, set()).add((cls, nm))
    big = re.compile(r"\b(" + "|".join(re.escape(a) for a in sorted(anchor_pairs, key=len, reverse=True)) + r")s?\b")
    rows = hits = excl = withframe = opens = inside = cOff = cOn = 0
    era = {"pre_gate": [0, 0], "post_gate": [0, 0]}      # [hits, excluded]
    guard_changes_c = 0
    with open(LIVE / "monologue_log.jsonl", encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except Exception:
                continue
            rows += 1
            text = f"{r.get('thought', '')} {r.get('intention', '') or ''}"
            low = text.lower()
            # cheap exact prefilter (extract() needs a cue word and a claim word in one clause; neither => None)
            if oh._cue(low) is None and not any(oh._cue(c) for c in (x.lower() for x in oh.clauses(text))):
                continue
            if not oh._CLAIM_RE.search(low):
                continue
            found = {a for a in big.findall(low)}
            if not found:
                continue
            cand_pairs = set()
            for a in found:
                cand_pairs |= anchor_pairs.get(a, set())
            first_off = None
            on_any = False
            for (cls, nm) in cand_pairs:
                set_flags(False, False)
                ro = oh.extract(text, cls, nm)
                if not ro:
                    continue
                if first_off is None:
                    first_off = (cls, nm, ro)
                set_flags(True, True)
                if oh.extract(text, cls, nm):
                    on_any = True
            if first_off is None:
                continue
            hits += 1
            cls, nm, ro = first_off
            fi = frame_info(ro[0])
            withframe += fi["frame"]; opens += fi["opens"]; inside += fi["inside"]
            e = era["post_gate" if float(r.get("ts", 0)) >= GATE_TS else "pre_gate"]
            e[0] += 1
            set_flags(False, False)
            c_off = cands(ro[0], cls, nm, pairs[(cls, nm)], fam)
            set_flags(False, True)
            c_on = cands(ro[0], cls, nm, pairs[(cls, nm)], fam)
            cOff += bool(c_off); cOn += bool(c_on)
            if not fi["frame"] and c_off != c_on:
                guard_changes_c += 1
            if not on_any:
                excl += 1
                e[1] += 1
                excluded_examples.append({"corpus": "C", "ts": r.get("ts"), "obj": f"{cls}|{nm}", "claim": ro[0],
                                          "cands_off": [(c["verb"], c["cue"]) for c in c_off]})
    rep["C_monologue_replay"] = {"rows": rows, "rows_with_extractor_hit_any_object": hits, "with_frame": withframe,
                                 "opens": opens, "inside": inside, "excluded_by_gate": excl,
                                 "hits_with_candidates_guard_off": cOff, "hits_with_candidates_guard_on": cOn,
                                 "guard_changed_a_frameless_hit": guard_changes_c,
                                 "excluded_share_pct": pct(excl, hits), "verdict": verdict(pct(excl, hits)),
                                 "by_era_[hits,excluded]": era,
                                 "note": "upper bound: ignores the 1800 s last-looked-object requirement"}
    ph, pe = nHit + hits, nExcl + excl
    rep["pooled"] = {"extractor_hits": ph, "excluded": pe, "share_pct": pct(pe, ph), "verdict": verdict(pct(pe, ph))}
    set_flags(True, True)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "scan.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "excluded_examples.json").write_text(json.dumps(excluded_examples, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k != "A_live"}, indent=1, ensure_ascii=False))
    print("A_live:")
    for a in rep["A_live"]["rows"]:
        print("  ", json.dumps(a, ensure_ascii=False))
    print("FIRST 30 EXCLUDED (file order):")
    for e in excluded_examples[:30]:
        print("  ", json.dumps(e, ensure_ascii=False))
    print("total excluded examples:", len(excluded_examples))


if __name__ == "__main__":
    main()
