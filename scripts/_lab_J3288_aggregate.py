"""J-3288 step 4: join the deterministic verdicts (facts.json) with the cross-family judge labels
(judge_gemma4_12b.json) and with the hand-read verdicts (hand_labels.json, optional), report rates, the
lexical-check confusion table, and dump a reading file of every disagreement / judged-absent fact with the
best-matching sentences of the passage the writer saw. Writes only under docs/lab/J-3288_data/.
Run: python scripts/_lab_J3288_aggregate.py"""
from __future__ import annotations
import json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "docs" / "lab" / "J-3288_data"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _lab_J3288_classify import content_stems, sentences, stem, entity_missing  # noqa: E402


def best_sents(fact: str, text: str, k: int = 2) -> list[str]:
    fs = content_stems(fact)
    ss = sentences(text)
    sc = sorted(((len(fs & content_stems(s)) / max(1, len(fs)), i) for i, s in enumerate(ss)), reverse=True)[:k]
    return [f"[{round(c, 2)}] {ss[i][:300]}" for c, i in sc]


def main():
    sample = json.load(open(D / "sample.json", encoding="utf-8"))["sample"]
    facts = json.load(open(D / "facts.json", encoding="utf-8"))
    judge = json.load(open(D / "judge_gemma4_12b.json", encoding="utf-8"))
    hand = json.load(open(D / "hand_labels.json", encoding="utf-8")) if (D / "hand_labels.json").exists() else {}
    rows = []
    for f in facts:
        j = judge.get(str(f["note"]), {}).get("labels") or {}
        lab = j.get(str(f["fact_idx"] + 1))
        f["judge"] = lab if lab in ("P", "R", "A") else None
        h = hand.get(f"{f['note']}.{f['fact_idx']}")
        f["hand"] = h
        f["ent_missing"] = entity_missing(f["fact"], sample[f["note"]]["passage_seen"])
        f["ent_missing_full"] = entity_missing(f["fact"], sample[f["note"]]["passage"])
        f["final"] = h or f["judge"]
        rows.append(f)
    judged = [r for r in rows if r["judge"]]
    notes_judged = sorted({r["note"] for r in judged})
    print("facts", len(rows), "judged", len(judged), "notes judged", len(notes_judged))
    c = collections.Counter(r["judge"] for r in judged)
    print("judge", dict(c), {k: round(v / len(judged), 3) for k, v in c.items()})
    print("lexical-vs-judge:")
    ct = collections.Counter((r["seen"]["verdict"], r["judge"]) for r in judged)
    for k in sorted(ct):
        print("  ", k, ct[k])
    # per-note
    per = collections.defaultdict(lambda: [0, 0])
    for r in judged:
        per[r["note"]][0] += 1
        per[r["note"]][1] += r["judge"] == "A"
    print("notes with >=1 judged-A fact:", sum(1 for v in per.values() if v[1]), "of", len(per),
          "; with >=half A:", sum(1 for v in per.values() if v[1] * 2 >= v[0]))
    # deterministic check variants vs judge (A = positive class "ungrounded")
    def conf(pred):
        tp = sum(1 for r in judged if pred(r) and r["judge"] == "A")
        fp = sum(1 for r in judged if pred(r) and r["judge"] != "A")
        fn = sum(1 for r in judged if not pred(r) and r["judge"] == "A")
        return tp, fp, fn
    print("deterministic variants (flag = ungrounded); tp/fp/fn vs judge-A:")
    for name, pred in [
        ("window cov<0.50 or missing num/name (the verdict 'absent')", lambda r: r["seen"]["verdict"] == "absent"),
        ("any stem cov (whole seen passage) <0.6", lambda r: (r["seen"]["cov_all"] or 0) < 0.6),
        ("any stem cov (whole seen passage) <0.7", lambda r: (r["seen"]["cov_all"] or 0) < 0.7),
        ("any stem cov (whole seen passage) <0.8", lambda r: (r["seen"]["cov_all"] or 0) < 0.8),
        ("missing number/name only", lambda r: bool(r["seen"]["missing"])),
        ("cos_max_full <0.70", lambda r: r.get("cos_max_full", 1) < 0.70),
        ("ENTITY check: a number/name of the fact not in the seen passage", lambda r: bool(r["ent_missing"])),
        ("ENTITY check against the WHOLE session text", lambda r: bool(r["ent_missing_full"])),
        ("ENTITY check OR stem cov(whole seen)<0.6", lambda r: bool(r["ent_missing"]) or (r["seen"]["cov_all"] or 0) < 0.6),
    ]:
        print("  ", name, conf(pred))
    if hand:
        hc = collections.Counter(r["hand"] for r in rows if r["hand"])
        print("hand labels", dict(hc))
    print("entity-check flags:", sum(1 for r in rows if r["ent_missing"]), "of", len(rows), "facts;",
          "notes with a flag:", len({r['note'] for r in rows if r['ent_missing']}))
    if hand:
        hj = [r for r in rows if r["hand"]]
        for name, pred in [("ENTITY check", lambda r: bool(r["ent_missing"]))]:
            tp = sum(1 for r in hj if pred(r) and r["hand"] in ("E", "A")); fp = sum(1 for r in hj if pred(r) and r["hand"] == "G")
            fn = sum(1 for r in hj if not pred(r) and r["hand"] in ("E", "A"))
            print("vs HAND labels (hand-read subset n=%d):" % len(hj), name, "tp", tp, "fp", fp, "fn", fn)
    if hand:
        hj = [r for r in rows if r["hand"]]
        bad = lambda r: r["hand"] in ("E", "A")
        print("deterministic variants vs HAND labels, n=%d hand-read facts (%d problems); flag = ungrounded:" % (len(hj), sum(1 for r in hj if bad(r))))
        for name, pred in [
            ("lexical 'absent' (window cov<0.5 or missing number/name)", lambda r: r["seen"]["verdict"] == "absent"),
            ("stem coverage of whole seen passage <0.7", lambda r: (r["seen"]["cov_all"] or 0) < 0.7),
            ("stem coverage of whole seen passage <0.8", lambda r: (r["seen"]["cov_all"] or 0) < 0.8),
            ("ENTITY check (number/name not in passage)", lambda r: bool(r["ent_missing"])),
            ("gemma judge says A", lambda r: r["judge"] == "A"),
        ]:
            tp = sum(1 for r in hj if pred(r) and bad(r)); fp = sum(1 for r in hj if pred(r) and not bad(r)); fn = sum(1 for r in hj if not pred(r) and bad(r))
            print("   %-62s flags %3d  caught %d/%d  false alarms %d" % (name, tp + fp, tp, tp + fn, fp))
    # reading file
    out = []
    for r in rows:
        if r["ent_missing"] or r["judge"] == "A" or (r["judge"] in ("P", "R") and r["seen"]["verdict"] == "absent") or (r["judge"] == "A" and r["seen"]["verdict"] != "absent"):
            s = sample[r["note"]]
            out.append(f"### {r['note']}.{r['fact_idx']}  judge={r['judge']} lexical={r['seen']['verdict']} cov_all={r['seen']['cov_all']} cat={r['category']} missing={r['seen']['missing']}\n"
                       f"book: {s['book'][:60]}\nFACT: {r['fact']}\n" + "\n".join("  seen> " + x for x in best_sents(r['fact'], s['passage_seen'])) +
                       ("\n" + "\n".join("  FULL> " + x for x in best_sents(r['fact'], s['passage'], 1)) if r["category"] != "grounded_in_seen_window" else "") + "\n")
    (D / "reading_file.md").write_text("\n".join(out), encoding="utf-8")
    json.dump(rows, open(D / "facts_joined.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("reading file entries", len(out))


if __name__ == "__main__":
    main()
