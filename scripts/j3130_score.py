"""J-3130 scoring: agreement of single-judge arms (and the panel emulation of two of them) with the hand labels.
Read-only on docs/lab/J-3130_data/*.json; writes docs/lab/J-3130_data/results.json and prints a table.
  python scripts/j3130_score.py gemma falcon [--variant narrow]
Emulation note: with the real JUDGE_1 (mixtral, Ramses) unavailable, 'AND' (both local judges say yes) is the
condition under which ANY panel containing both would return yes by agreement; 'OR' is the most a tiebreak could add."""
import json, sys, statistics as st
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "docs" / "lab" / "J-3130_data"


def load(name, variant):
    p = DATA / f"single_{name}_{variant}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def stats(items, labels, votes):
    """votes: {id: bool|None}.  Agreement counts only labeled items with an answer; None counted separately."""
    lab = [i for i in items if str(i["id"]) in labels]
    ans = [i for i in lab if votes.get(i["id"]) is not None]
    agree = sum(1 for i in ans if votes[i["id"]] == bool(labels[str(i["id"])]))
    tp = sum(1 for i in ans if votes[i["id"]] and labels[str(i["id"])])
    fp = sum(1 for i in ans if votes[i["id"]] and not labels[str(i["id"])])
    fn = sum(1 for i in ans if not votes[i["id"]] and labels[str(i["id"])])
    tn = sum(1 for i in ans if not votes[i["id"]] and not labels[str(i["id"])])
    allans = [i for i in items if votes.get(i["id"]) is not None]

    def yes_rate(sel):
        sel = [i for i in sel if votes.get(i["id"]) is not None]
        return {"n": len(sel), "yes": sum(1 for i in sel if votes[i["id"]]),
                "rate": round(sum(1 for i in sel if votes[i["id"]]) / len(sel), 3) if sel else None}
    return {"labeled": len(lab), "answered_labeled": len(ans), "no_answer_labeled": len(lab) - len(ans),
            "agree": agree, "agreement": round(agree / len(ans), 3) if ans else None,
            "agreement_if_noanswer_wrong": round(agree / len(lab), 3) if lab else None,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(tp / (tp + fp), 3) if tp + fp else None,
            "recall": round(tp / (tp + fn), 3) if tp + fn else None,
            "yes_weak_all": yes_rate([i for i in allans if i["weak"]]),
            "yes_solid_all": yes_rate([i for i in allans if not i["weak"]]),
            "yes_weak_labeled": yes_rate([i for i in ans if i["weak"]]),
            "yes_by_kind_all": {k: yes_rate([i for i in allans if i["kind"] == k])
                                for k in sorted({i["kind"] for i in items})},
            "agree_by_kind_labeled": {k: [sum(1 for i in ans if i["kind"] == k and votes[i["id"]] == bool(labels[str(i["id"])])),
                                          sum(1 for i in ans if i["kind"] == k)]
                                      for k in sorted({i["kind"] for i in items})}}


def main():
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    variant = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else "narrow"
    names = [n for n in names if n != variant]
    items = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
    labels = json.loads((DATA / "hand_labels.json").read_text(encoding="utf-8"))["labels"]
    res = {"variant": variant, "n_items": len(items), "n_labeled": len(labels), "judges": {}}
    votes = {}
    for n in names:
        raw = load(n, variant)
        votes[n] = {int(k): v["v"] for k, v in raw.items()}
        secs = [v["s"] for v in raw.values() if v.get("s") is not None]
        errs = {}
        for v in raw.values():
            errs[v.get("err")] = errs.get(v.get("err"), 0) + 1
        res["judges"][n] = {"n_done": len(raw), "errs": errs, **stats(items, labels, votes[n]),
                            "s_median": round(st.median(secs), 1) if secs else None,
                            "s_p90": round(sorted(secs)[int(0.9 * len(secs))], 1) if secs else None,
                            "s_total": round(sum(secs), 0)}
    if len(names) == 2:
        a, b = names
        both = {i["id"]: (votes[a].get(i["id"]), votes[b].get(i["id"])) for i in items}
        and_v = {k: (None if None in v else (v[0] and v[1])) for k, v in both.items()}
        or_v = {k: (None if None in v else (v[0] or v[1])) for k, v in both.items()}
        split = sum(1 for v in both.values() if None not in v and v[0] != v[1])
        res["AND"], res["OR"] = stats(items, labels, and_v), stats(items, labels, or_v)
        res["split_rate"] = round(split / max(1, sum(1 for v in both.values() if None not in v)), 3)
        res["both_answered"] = sum(1 for v in both.values() if None not in v)
    (DATA / f"results_{variant}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in res["judges"].items():
        print(k, {x: v[x] for x in ("n_done", "errs", "labeled", "answered_labeled", "agree", "agreement", "tp", "fp", "fn", "tn",
                                    "precision", "recall", "yes_weak_all", "yes_solid_all", "s_median", "s_p90")})
    for k in ("AND", "OR"):
        if k in res:
            print(k, {x: res[k][x] for x in ("answered_labeled", "agree", "agreement", "tp", "fp", "fn", "tn", "yes_weak_all", "yes_solid_all")})
    if "split_rate" in res:
        print("split_rate", res["split_rate"], "n", res["both_answered"])


if __name__ == "__main__":
    main()
