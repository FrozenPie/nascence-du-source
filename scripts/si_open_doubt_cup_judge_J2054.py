"""
J-2054 -- score the J-2031 coordinate-only open-doubt cup replay (cup / shuffled control / uncued baseline) with the
position-free ABSOLUTE 1-5 panel judge validated in J-2052 (engaged = mixtral AND falcon >= 4), cross-checked by reflection-MATCHING.
Rubric text and thresholds are imported from scripts/si_open_doubt_specificity_judge_J2052.py UNCHANGED (not retuned).
Generations are the existing J-2031 gens (data/lab/J-2031/gens.jsonl, 15 fires x 3 arms x 2 samples, gemma4:12b on :11439, live-like
seed): no new generation, so only the two judge hubs (:11438 mixtral, :11440 falcon) are called, ONE stream, 2 s pauses.
The J-2052 positive/negative controls (15 own / plain / mismatched) are re-judged in the SAME run first.
PRE-REGISTERED BAR (D-0396/D-0403, written before data): cup engaged >= 30% AND shuffled-control engaged <= 11% AND no rise in
restate_sim / early close (from J-2031 summary). Also reported: cup>control and cup>baseline paired wins on panel score,
cue-echo-excluded subset. Lab only, nothing wired, outputs data/lab/J-2054/ (live tree, gitignored lab dir).
  python scripts/si_open_doubt_cup_judge_J2054.py judge | report
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (core BEFORE lab_env)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core from {core.__file__}"
import si_open_doubt_specificity_judge_J2052 as j2   # noqa: E402
v2 = j2.v2
OUT = Path(r"C:\Nascence\data\lab\J-2054")
ARMS = ("baseline", "cup", "control")
SAMPLES = 2


def arm_items(mode):
    rows = v2.jl(v2.GENS)
    n = len(rows); out = []
    for i, r in enumerate(rows):
        for arm in ARMS:
            for s, x in enumerate(r["arms"][arm][:SAMPLES]):
                th = x["thought"]
                if not th or th.startswith("ERR:"):
                    continue
                iid = f"{r['cycle_id']}|{arm}|{s}"
                if mode == "abs":
                    out.append((iid, r, th, arm))
                else:
                    pos = (i + s + ARMS.index(arm)) % 3 + 1       # rotate own position for balance
                    others = [rows[(i + 1) % n]["reflection"], rows[(i + 2) % n]["reflection"]]
                    refl = list(others); refl.insert(pos - 1, r["reflection"])
                    out.append((iid, (r, refl, pos), th, arm))
    return out


async def run(tag, mode, its, pf):
    import aiohttp
    from core import judge_panel
    done = set()
    if pf.exists():
        done = {json.loads(l)["id"] for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()}
    hubs = {"mixtral": judge_panel.JUDGE_1, "falcon": judge_panel.JUDGE_2}
    print(f"{tag}: {len(its)} items (done {len(done)})", flush=True)
    async with aiohttp.ClientSession() as session:
        for k, (iid, ctx, cand, kind) in enumerate(its, 1):
            if iid in done:
                continue
            if mode == "abs":
                user = j2.USER_ABS.format(thought=ctx["thought"][:400], reflection=ctx["reflection"][:400], cand=cand[:600])
                sysm, key, lo, hi = j2.SYS_ABS, "score", 1, 5
            else:
                r, refl, pos = ctx
                user = j2.USER_MATCH.format(cand=cand[:600], r1=refl[0][:400], r2=refl[1][:400], r3=refl[2][:400])
                sysm, key, lo, hi = j2.SYS_MATCH, "reflection", 1, 3
            row = {"id": iid, "kind": kind}
            if mode == "match":
                row["own_pos"] = ctx[2]
            for name, url in hubs.items():
                v, err, s = await j2.ask(session, url, sysm, user, key, lo, hi)
                row[name] = v; row[name + "_err"] = err; row[name + "_s"] = s
                await asyncio.sleep(j2.PAUSE)
            with open(pf, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{k}/{len(its)}] {tag} {kind} m={row['mixtral']} f={row['falcon']}", flush=True)


async def judge():
    OUT.mkdir(parents=True, exist_ok=True)
    await run("ctrl_abs", "abs", j2.items("abs"), OUT / "ctrl_abs.jsonl")   # same-run control re-check
    await run("arm_abs", "abs", arm_items("abs"), OUT / "arm_abs.jsonl")
    await run("arm_match", "match", arm_items("match"), OUT / "arm_match.jsonl")


def load(n):
    pf = OUT / n
    return [json.loads(l) for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()] if pf.exists() else []


def eng(r):
    return r["mixtral"] is not None and r["falcon"] is not None and r["mixtral"] >= 4 and r["falcon"] >= 4


def report():
    W = lambda k, n: {"k": k, "n": n, "rate": round(k / n, 3) if n else None, "ci95": v2.wilson(k, n)}
    s = {}
    c = load("ctrl_abs.jsonl")
    s["controls"] = {k: W(sum(eng(r) for r in c if r["kind"] == k), sum(1 for r in c if r["kind"] == k)) for k in ("own", "plain", "mism")}
    a = load("arm_abs.jsonl")
    gens = {r["cycle_id"]: r for r in v2.jl(v2.GENS)}
    echo = lambda r: bool(gens[r["id"].split("|")[0]]["arms"][r["kind"]][int(r["id"].split("|")[2])].get("echo"))
    arms = {}
    for arm in ARMS:
        rs = [r for r in a if r["kind"] == arm]
        sc = [(r["mixtral"], r["falcon"]) for r in rs if r["mixtral"] is not None and r["falcon"] is not None]
        arms[arm] = {"engaged": W(sum(eng(r) for r in rs), len(rs)),
                     "engaged_noecho": W(sum(eng(r) for r in rs if not echo(r)), sum(1 for r in rs if not echo(r))),
                     "mean_mixtral": round(sum(x[0] for x in sc) / max(1, len(sc)), 2),
                     "mean_falcon": round(sum(x[1] for x in sc) / max(1, len(sc)), 2),
                     "ge3_both": W(sum(1 for x in sc if x[0] >= 3 and x[1] >= 3), len(rs)),
                     "nojudge": sum(1 for r in rs if r["mixtral"] is None or r["falcon"] is None),
                     "dist_mixtral": {v: sum(1 for r in rs if r["mixtral"] == v) for v in range(1, 6)},
                     "dist_falcon": {v: sum(1 for r in rs if r["falcon"] == v) for v in range(1, 6)}}
    s["arms_abs"] = arms
    by = {}
    for r in a:
        cid, arm, smp = r["id"].split("|")
        if r["mixtral"] is not None and r["falcon"] is not None:
            by.setdefault((cid, smp), {})[arm] = (r["mixtral"] + r["falcon"], eng(r))
    for x, y in (("cup", "control"), ("cup", "baseline"), ("control", "baseline")):
        ps = [d for d in by.values() if x in d and y in d]
        wins = sum(1 for d in ps if d[x][0] > d[y][0]); ties = sum(1 for d in ps if d[x][0] == d[y][0])
        s[f"paired_{x}_v_{y}"] = {"wins": W(wins, len(ps)), "ties": ties, "losses": len(ps) - wins - ties,
                                  "wins_excl_ties": W(wins, len(ps) - ties),
                                  "eng_discordant_x_only": sum(1 for d in ps if d[x][1] and not d[y][1]),
                                  "eng_discordant_y_only": sum(1 for d in ps if d[y][1] and not d[x][1])}
    m = load("arm_match.jsonl")
    pn = lambda r: r["mixtral"] if (r["mixtral"] is not None and r["mixtral"] == r["falcon"]) else None
    s["arms_match"] = {arm: {"own": W(sum(1 for r in m if r["kind"] == arm and pn(r) == r["own_pos"]), sum(1 for r in m if r["kind"] == arm)),
                             "no_verdict": sum(1 for r in m if r["kind"] == arm and pn(r) is None)} for arm in ARMS}
    sm = json.loads(v2.SUMMARY.read_text(encoding="utf-8"))
    s["rumination_from_J2031"] = {k: sm[k] for k in ARMS}
    cu, ct = arms["cup"]["engaged"], arms["control"]["engaged"]
    ok = {"cup_ge_30": bool(cu["rate"] is not None and cu["rate"] >= 0.30), "control_le_11": bool(ct["rate"] is not None and ct["rate"] <= 0.11),
          "no_restate_rise": sm["cup"]["mean_restate_sim"] <= sm["baseline"]["mean_restate_sim"] + 0.02,
          "no_early_close_rise": sm["cup"]["early_close_rate"] <= sm["baseline"]["early_close_rate"] + 0.05,
          "controls_pass": bool(s["controls"]["own"]["rate"] is not None and s["controls"]["own"]["rate"] >= 0.85
                                and s["controls"]["mism"]["rate"] <= 0.11 and s["controls"]["plain"]["rate"] <= 0.11)}
    ok["BAR_MET"] = all(ok.values())
    s["bar"] = ok
    (OUT / "summary.json").write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(s, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "judge":
        asyncio.run(judge())
    else:
        report()
