"""
J-3785 lab: same-lesson panel check (core.guidance_learning._SAME_LESSON_SYS, J-3233/D-0622) as a stage-2 corroboration gate
over prompt A's 'assimilate' verdicts, vs the J-3409 B3 arm. READ-ONLY; writes only docs/lab/J-3785_data/.

Stage 1 = J-3409's own author_runs.jsonl arm A (command-r7b local, 3 repeats, 269 pairs) -- reused, not re-run.
Stage 2 = falcon3:7b (:11440, the panel's JUDGE_2 family) or gemma4:12b (:11439, reported separately) asked the exact
_SAME_LESSON_SYS on (existing, new) as (A, B), only for (pair, rep) where stage 1 said assimilate. A call is a
corroboration only if stage 1 assimilate AND stage 2 same_lesson true; an invalid/no verdict counts as NOT corroborating
in the strict reading (and is also reported fail-open, as the live code does).
Reversed-order check: the same question with A and B swapped (rep 0 only), on pairs A assimilated at least once.

  python scripts/lab_J-3785_same_lesson_gate.py run falcon3|gemma4 [fwd|rev]
  python scripts/lab_J-3785_same_lesson_gate.py report
"""
from __future__ import annotations
import json, sys, os, time, collections, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
D9 = ROOT / "docs" / "lab" / "J-3409_data"; D2 = ROOT / "docs" / "lab" / "J-3232_data"
OUT = ROOT / "docs" / "lab" / "J-3785_data"
HUBS = {"falcon3": ("http://127.0.0.1:11440", "falcon3:7b"), "gemma4": ("http://127.0.0.1:11439", "gemma4:12b")}
LIVE = Path(r"C:\Nascence\data")


def load():
    pairs = json.load(open(D2 / "pairs.json", encoding="utf-8")) + json.load(open(D9 / "pairs_extra.json", encoding="utf-8"))
    lab = dict(json.load(open(D2 / "hand_labels.json", encoding="utf-8"))["labels"])
    lab.update(json.load(open(D9 / "hand_labels_extra.json", encoding="utf-8"))["labels"])
    a = collections.defaultdict(dict)
    for l in open(D9 / "author_runs.jsonl", encoding="utf-8"):
        r = json.loads(l)
        if r["arm"] == "A":
            a[r["pid"]][r["rep"]] = r["relation"]
    return pairs, lab, a


def msg(p, rev):
    x, y = (p["new"], p["existing"]) if rev else (p["existing"], p["new"])
    return f"A:\n\"{x[:400]}\"\n\nB:\n\"{y[:400]}\""


def run(hub, mode):
    import lab_guidance_classify as L
    from core import guidance_learning as gl     # core BEFORE lab_env
    sys.path.insert(0, str(Path(r"C:\Users\USER\.claude\skills\job-queue")))
    from lab_env import isolate
    url, model = HUBS[hub]
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"stage2_{hub}_{mode}.jsonl"
    pairs, lab, a = load()
    done = set()
    if path.exists():
        for l in open(path, encoding="utf-8"):
            r = json.loads(l); done.add((r["pid"], r["rep"]))
    # priority: hand-same, then Q (A-corroborated not-same), so a partial run still answers P2/P3
    def prio(p):
        return 0 if lab.get(p["id"]) == "S" else 1
    jobs = []
    for p in sorted(pairs, key=prio):
        for rep in ([0, 1, 2] if mode == "fwd" else [0]):
            if mode == "rev":
                if not any(v == "assimilate" for v in a[p["id"]].values()):
                    continue
            elif a[p["id"]].get(rep) != "assimilate":
                continue
            if (p["id"], rep) not in done:
                jobs.append((p, rep))
    if mode == "fwd":   # rep-major so every pair gets rep 0 before rep 1
        jobs.sort(key=lambda j: (j[1], prio(j[0])))
    print(hub, mode, "jobs", len(jobs), flush=True)
    before = {f.name: (f.stat().st_size, int(f.stat().st_mtime)) for f in LIVE.iterdir() if f.is_file()}
    f = open(path, "a", encoding="utf-8"); t0 = time.time(); n = 0
    with isolate(also=[(gl, ["_BELIEFS", "_INTEG_LOG", "_INTEG_STATE", "_CLASSIFY_LOG", "_LOG", "_POLE_GATE_LOG", "_INJECT_LOG",
                             "_CONTRA_LOG"])], db="empty"):
        for p, rep in jobs:
            raw, err = "", None
            for attempt in (0, 1):
                try:
                    raw = L.chat(url, model, gl._SAME_LESSON_SYS, msg(p, mode == "rev"), num_predict=120, timeout=240)
                    err = None
                    break
                except Exception as e:
                    err = str(e)
            v = L.parse_json(raw).get("same_lesson") if raw else None
            f.write(json.dumps({"pid": p["id"], "rep": rep, "same": v if isinstance(v, bool) else None,
                                "raw": (raw or f"ERR {err}")[:300]}, ensure_ascii=False) + "\n"); f.flush()
            n += 1
            if n % 25 == 0:
                print(n, "calls", round(time.time() - t0), "s", flush=True)
    after = {f.name: (f.stat().st_size, int(f.stat().st_mtime)) for f in LIVE.iterdir() if f.is_file()}
    ch = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
    print("done", n, "calls; top-level data/ files changed during run (shared-tree noise possible):", ch[:10])


def wilson(k, n):
    if not n: return (0, 0)
    z = 1.96; ph = k / n
    d = 1 + z * z / n; c = ph + z * z / (2 * n); h = z * ((ph * (1 - ph) / n + z * z / (4 * n * n)) ** .5)
    return ((c - h) / d, (c + h) / d)


def load2(hub, mode):
    p = OUT / f"stage2_{hub}_{mode}.jsonl"
    d = {}
    if p.exists():
        for l in open(p, encoding="utf-8"):
            r = json.loads(l); d[(r["pid"], r["rep"])] = r["same"]
    return d


def report():
    import random
    pairs, lab, a = load()
    ids = [p["id"] for p in pairs]
    same = [i for i in ids if lab.get(i) == "S"]
    nots = [i for i in ids if lab.get(i) in ("N", "C", "U")]
    Q = [i for i in nots if any(v == "assimilate" for v in a[i].values())]
    L = []
    w = L.append
    w("# J-3785 results: same-lesson stage-2 gate over prompt A (author command-r7b, 3 reps from J-3409), judge per hub\n")
    w(f"hand-same pairs {len(same)}, not-same pairs {len(nots)}, Q (not-same A corroborates >=1 call) {len(Q)}\n")
    res = {}
    for hub in HUBS:
        fw = load2(hub, "fwd"); rv = load2(hub, "rev")
        if not fw:
            continue
        def rate(idset, strict=True):
            tot = ok = ok_fo = none = 0
            for i in idset:
                for rep in range(3):
                    if a[i].get(rep) == "assimilate":
                        pass
                    tot += 1
                    if a[i].get(rep) != "assimilate":
                        continue
                    v = fw.get((i, rep), "MISSING")
                    if v is True: ok += 1; ok_fo += 1
                    elif v is None: none += 1; ok_fo += 1
            return tot, ok, ok_fo, none
        covered = lambda idset: [i for i in idset if all(a[i].get(r) != "assimilate" or (i, r) in fw for r in range(3))]
        sc, qc = covered(same), covered(Q)
        w(f"\n## Judge {hub}\n")
        w(f"coverage: hand-same pairs fully run {len(sc)}/{len(same)}, Q pairs fully run {len(qc)}/{len(Q)}\n")
        tA = rate(sc); tG = rate(sc)
        a_same = sum(1 for i in sc for r in range(3) if a[i].get(r) == "assimilate"); n_same = len(sc) * 3
        g_same = tG[1]; gfo_same = tG[2]
        w(f"- P2 same-lesson corroboration (covered hand-same, call level): A {a_same}/{n_same} ({100*a_same/max(1,n_same):.0f}%); "
          f"A+gate strict {g_same}/{n_same} ({100*g_same/max(1,n_same):.0f}%); fail-open {gfo_same}/{n_same} ({100*gfo_same/max(1,n_same):.0f}%); "
          f"gate no-verdict {tG[3]}")
        a_q = sum(1 for i in qc for r in range(3) if a[i].get(r) == "assimilate"); a_q_rate = a_q / max(1, len(qc) * 3)
        g_q = rate(qc)[1]; gfo_q = rate(qc)[2]
        w(f"- P3 false corroboration on Q (call level, over {len(qc)*3} calls): A {a_q} ({100*a_q_rate:.0f}%); A+gate strict {g_q} "
          f"({100*g_q/max(1,len(qc)*3):.0f}%); fail-open {gfo_q}; reduction strict {100*(1-g_q/max(1,a_q)):.0f}%")
        w("- P1 wrong accommodates on same-lesson: the gate only ever REMOVES corroborations (never produces accommodate); A's own count is 0 "
          "on hand-same, so P1 holds by construction here; the cost shows as same-lesson pairs falling to 'separate belief' (P2).")
        # per-set P2
        for nm, pre in (("tight-8 (L-set S)", "L"), ("S3", "S3"), ("S2/mixed", "M")):
            ss = [i for i in sc if i.startswith(pre)]
            if ss:
                n_ = len(ss) * 3; k_ = sum(1 for i in ss for r in range(3) if fw.get((i, r)) is True)
                w(f"  - {nm}: {k_}/{n_} corroborated after gate ({100*k_/max(1,n_):.0f}%) vs A {sum(1 for i in ss for r in range(3) if a[i].get(r)=='assimilate')}/{n_}")
        # cluster bootstrap on P2 diff and P3 reduction
        rnd = random.Random(7)
        def boot(idset, f):
            vals = []
            for _ in range(2000):
                s = [rnd.choice(idset) for _ in idset]
                vals.append(f(s))
            vals.sort(); return vals[50], vals[1949]
        if sc:
            f2 = lambda s: 100 * (sum(1 for i in s for r in range(3) if fw.get((i, r)) is True) - sum(1 for i in s for r in range(3) if a[i].get(r) == 'assimilate')) / (3 * len(s))
            lo, hi = boot(sc, f2); w(f"- P2 gate-minus-A point diff (pct pts) bootstrap 95% [{lo:.1f}, {hi:.1f}]")
        if qc:
            f3 = lambda s: 100 * (1 - (sum(1 for i in s for r in range(3) if fw.get((i, r)) is True) / max(1, sum(1 for i in s for r in range(3) if a[i].get(r) == 'assimilate'))))
            lo, hi = boot(qc, f3); w(f"- P3 reduction (pct) bootstrap 95% [{lo:.1f}, {hi:.1f}]")
        # stability across repeats
        st = collections.Counter()
        for i in sc + qc:
            vs = [fw.get((i, r)) for r in range(3) if (i, r) in fw]
            if len(vs) >= 2:
                st["stable" if len(set(vs)) == 1 else "flips"] += 1
        w(f"- repeat stability (pairs with >=2 stage-2 calls): {dict(st)}")
        # reversed order
        if rv:
            def revrate(idset):
                ids_ = [i for i in idset if (i, 0) in rv]
                return len(ids_), sum(1 for i in ids_ if rv[(i, 0)] is True), sum(1 for i in ids_ if fw.get((i, 0)) is True)
            for nm, s in (("hand-same", same), ("Q", Q)):
                n_, k_, f_ = revrate(s)
                w(f"- reversed order ({nm}, rep0, pairs with a rev call {n_}): rev same {k_}, fwd same {f_}")
            ag = [i for i in rv if rv[i] is not None and fw.get(i) is not None]
            w(f"  - fwd/rev agreement on pairs with both verdicts: {sum(1 for i in ag if rv[i]==fw[i])}/{len(ag)}")
        w(f"- stage-2 no-verdict calls (invalid/ERR) fwd: {sum(1 for v in fw.values() if v is None)} of {len(fw)}")
        res[hub] = {"sc": len(sc), "qc": len(qc)}
    w("\nB3 reference (J-3409 report): hand-same corroboration 99% vs A 100%; Q not-same corroboration is the P3 table in docs/lab/J-3409_data/report.md.")
    (OUT / "report.md").write_text("\n".join(L), encoding="utf-8")
    json.dump(res, open(OUT / "report.json", "w"))
    print("\n".join(L))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "fwd")
    else:
        report()
