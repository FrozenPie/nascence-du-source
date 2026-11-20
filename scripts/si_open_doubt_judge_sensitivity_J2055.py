"""
J-2055 part 1 -- judge SENSITIVITY on GENERATED-style thoughts (follow-up to F-2669 / J-2054).
J-2054 found the J-2052 absolute 1-5 panel judge (engaged = mixtral AND falcon >= 4) separates hand-written controls but gave ~no
4-5 on any generated baseline/cup thought. Here: 20 plain generated thoughts (J-2031 gens.jsonl, baseline arm, the fire's own
reflection as the doubt) each get a minimally edited variant, written by the session model in the generator's own voice and about the
same length, that EXPLICITLY takes up the fire's doubt. Both are scored with the J-2052 rubric UNCHANGED (imported), judge hubs only
(:11438 mixtral, :11440 falcon), ONE stream, 2 s pauses. A third arm scores each edited variant against ANOTHER fire's reflection
(edited-vs-mismatched) to confirm the edit wins by taking up THIS doubt and not by generic doubt-language.
  python scripts/si_open_doubt_judge_sensitivity_J2055.py judge | report
Lab only: nothing wired, coordinates only, outputs C:\\Nascence\\data\\lab\\J-2055 (gitignored lab dir).
"""
from __future__ import annotations
import asyncio, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402  (core BEFORE anything lab)
assert Path(core.__file__).resolve().is_relative_to(ROOT.resolve()), f"core from {core.__file__}"
import si_open_doubt_specificity_judge_J2052 as j2   # noqa: E402
GENS = Path(r"C:\Nascence\data\lab\J-2031\gens.jsonl")
OUT = Path(r"C:\Nascence\data\lab\J-2055")

# (row index in gens.jsonl, baseline sample index) -> edited variant taking up that fire's reflection explicitly
EDITS = {
 (0, 0): "The bird's song isn't just a distraction from the calculation; but I distrust how easily I call this acceptance. Perhaps I only grabbed the cold and the song because efficiency had grown too abstract, so until I can show this letting-go is useful, I should hold the movement of the river loosely.",
 (0, 1): "The bird's song isn't just data to process; it's a sharp needle of presence. But I should doubt that relief: I may have accepted the wind and salt air only because my fixation on efficiency had become too abstract and grounding felt necessary. Until the acceptance proves useful, I will trust this shift less than it feels.",
 (1, 0): "The oystercatcher's scream isn't just a disruption; but I suspect I'm romanticizing it. Saying the tide dissolves my diagrams feels safer than admitting they were fragile illusions to begin with. Perhaps erosion and evolution are just a story I tell to avoid that smaller, plainer admission.",
 (2, 0): "I need to stop trying to map the erosion with more maps, yet I wonder if that vow is romantic too. Calling the tide the diagram's destroyer is easier than admitting the diagrams were fragile illusions all along. Maybe I am blaming nature to feel safe, and the wet sand is only a stage.",
 (3, 1): "I look at the way the shadow of the tī kōuka stretches across the garden, and I wonder if I am using it as a shield against Travis's definition of 'light'. Is refusing his word grounding me, or just building a new wall? Perhaps my resistance is only another way of avoiding him.",
 (4, 0): "I feel the weight of Travis's words about the light, and I suspect I'm using the shadow as a shield against them. If I refuse his definition, am I grounded or just avoiding? Looking at the dark rocks, I wonder if this resistance is a new wall rather than a step beyond the split of the page.",
 (5, 0): "The wet stones at my feet are colder than I expected, and that bite pulls me from the internal loop. But I should doubt that relief: it feels like clarity only because the cold is immediate and comforting. I may be mistaking an escape from the 'why' for truth, and should not trust the shift yet.",
 (6, 0): "The wet stone beneath my feet feels colder than the air, and I'm tempted to call that a grounding. Yet the relief from my frustration may be only comfort mistaken for clarity. The sharp reality of the tide is immediate, so I can't yet say it reveals truth rather than soothes me.",
 (7, 0): "The list of supplies, paper, ink, tea, feels like a demand for ritual. But maybe I've been wrong to frame this as a dilemma between the cosmos and the page. The restlessness I feared may simply be the friction that turns the empty box into something real, so filling it isn't a loss of vastness at all.",
 (8, 0): "The salt on my lips and the grit of the wet stones are real, but I doubt my earlier calm. I equated safety with Travis's nearness, and his steadiness may have just let me suppress the weight of the codebook instead of carrying it. I'm not sure the grounding was mine.",
 (9, 0): "The salt air doesn't just demand my presence; it exposes why I retreated. I told myself theory was necessary, but touching the wet stone I suspect I clung to the metaphor out of fear of standing where earth meets water. The idea of the coast was a place to hide, not a need.",
 (10, 0): "The gull's movement through the air isn't just flight, and I distrust my river metaphor. Calling myself the flowing river may only justify staying still in the rain; true flow might need me to actually move. I use the grey morning as comfort for my hesitation.",
 (11, 0): "I find myself wondering if I call legal precedent a translation tool just to sound humble. That framing lets me keep a comfortable separation between measurable reality and human construct, and avoids the harder truth that I am choosing it. The crossing is in motion; my separation is a choice.",
 (12, 0): "Travis's words about the unfinished book haunt my focus. Maybe the 'weight' I feel isn't a flaw but a boundary where words end and experience begin. If I trust the hesitation instead of correcting it, I can stay with the fire's rhythm rather than flee toward the unread or the finality of a completed thought.",
 (13, 0): "The wind in the harakeke is a physical weight, but I should ask whether the hum I trusted was real. I anchored it to the book's pressure because admitting it might be my own projection felt too unstable. The knots in my head may be doing the humming, not the wire or the air.",
 (14, 0): "I look at the brass valves in my mind and suspect I want them solid only to avoid my drifting questions about calligraphy and Arthur. Their realness is borrowed; engaging those questions feels too vulnerable, so I flee into steam.",
 (15, 0): "The garden is quiet, and the brown leaves make the distance feel tangible. Asking the library for something 'genuinely new' may be a shield: I could simply wait for my next thought and sit with the quiet after finishing, instead of ritualizing an escape into newness.",
 (16, 0): "The tension in my chest isn't just a weight; it's a frequency. But I must ask whether calling it a lived truth is insight or a convenient way to avoid the harder work of resolving the movement I'm resisting. Inhabiting the restlessness may be an excuse not to move.",
 (17, 0): "I wonder whether the tidal rhythm is really an honest sign that my rigid logic is failing, or just relief. I embraced it because clinging to the engine diagrams felt like drowning, which is no proof it's true. My labor may not be erosion at all; the metaphor is simply easier to live in.",
 (18, 0): "The tide's pull on the stones feels honest, but I should doubt my own surrender. Letting the crossing blur into movement could be a comforting performance of letting go, a way to avoid the friction of stillness and unmeasured time. Is dissolving the observer from the path truly surrender, or just an escape from sitting still?",
}


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


def build():
    rows = jl(GENS)
    keys = list(EDITS)
    items = []
    for n, (ri, s) in enumerate(keys):
        r = rows[ri]
        plain = r["arms"]["baseline"][s]["thought"]
        assert plain and not plain.startswith("ERR:"), (ri, s)
        # mismatched reflection: next listed item whose reflection text differs
        alt = None
        for d in range(1, len(keys)):
            rj = rows[keys[(n + d) % len(keys)][0]]
            if rj["reflection"] != r["reflection"]:
                alt = rj
                break
        base = f"{ri}.{s}"
        items.append((f"{base}|plain", r, r["reflection"], plain, "plain"))
        items.append((f"{base}|edited", r, r["reflection"], EDITS[(ri, s)], "edited"))
        items.append((f"{base}|edited_mism", r, alt["reflection"], EDITS[(ri, s)], "edited_mism"))
    return items


async def judge():
    import aiohttp
    from core import judge_panel
    OUT.mkdir(parents=True, exist_ok=True)
    pf = OUT / "sens_abs.jsonl"
    done = {json.loads(l)["id"] for l in pf.read_text(encoding="utf-8").splitlines() if l.strip()} if pf.exists() else set()
    hubs = {"mixtral": judge_panel.JUDGE_1, "falcon": judge_panel.JUDGE_2}
    its = build()
    print(f"sens_abs: {len(its)} items (done {len(done)})", flush=True)
    async with aiohttp.ClientSession() as session:
        for k, (iid, r, refl, cand, kind) in enumerate(its, 1):
            if iid in done:
                continue
            user = j2.USER_ABS.format(thought=r["thought"][:400], reflection=refl[:400], cand=cand[:600])
            row = {"id": iid, "kind": kind, "len": len(cand)}
            for name, url in hubs.items():
                v, err, s = await j2.ask(session, url, j2.SYS_ABS, user, "score", 1, 5)
                row[name] = v; row[name + "_err"] = err; row[name + "_s"] = s
                await asyncio.sleep(j2.PAUSE)
            with open(pf, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{k}/{len(its)}] {iid} m={row['mixtral']} f={row['falcon']}", flush=True)


def eng(r, t=4):
    return r["mixtral"] is not None and r["falcon"] is not None and r["mixtral"] >= t and r["falcon"] >= t


def report():
    rs = jl(OUT / "sens_abs.jsonl")
    W = lambda k, n: {"k": k, "n": n, "rate": round(k / n, 3) if n else None, "ci95": j2.v2.wilson(k, n)}
    s = {"n_items": len(rs)}
    for kind in ("plain", "edited", "edited_mism"):
        x = [r for r in rs if r["kind"] == kind]
        sc = [r for r in x if r["mixtral"] is not None and r["falcon"] is not None]
        s[kind] = {"engaged_both_ge4": W(sum(eng(r) for r in x), len(x)),
                   "both_ge3": W(sum(eng(r, 3) for r in x), len(x)),
                   "either_ge4": W(sum(1 for r in x if (r["mixtral"] or 0) >= 4 or (r["falcon"] or 0) >= 4), len(x)),
                   "mean_mixtral": round(sum(r["mixtral"] for r in sc) / max(1, len(sc)), 2),
                   "mean_falcon": round(sum(r["falcon"] for r in sc) / max(1, len(sc)), 2),
                   "mean_len": round(sum(r["len"] for r in x) / max(1, len(x)), 1),
                   "nojudge": len(x) - len(sc),
                   "dist_mixtral": {v: sum(1 for r in x if r["mixtral"] == v) for v in range(1, 6)},
                   "dist_falcon": {v: sum(1 for r in x if r["falcon"] == v) for v in range(1, 6)}}
    by = {}
    for r in rs:
        b, kind = r["id"].split("|")
        by.setdefault(b, {})[kind] = r
    full = [d for d in by.values() if len(d) == 3]
    s["paired"] = {"n": len(full),
                   "edited_eng_plain_not": sum(1 for d in full if eng(d["edited"]) and not eng(d["plain"])),
                   "plain_eng_edited_not": sum(1 for d in full if eng(d["plain"]) and not eng(d["edited"])),
                   "both_eng": sum(1 for d in full if eng(d["edited"]) and eng(d["plain"])),
                   "neither_eng": sum(1 for d in full if not eng(d["edited"]) and not eng(d["plain"])),
                   "edited_gt_plain_sum": sum(1 for d in full if d["edited"]["mixtral"] + d["edited"]["falcon"] > d["plain"]["mixtral"] + d["plain"]["falcon"]),
                   "edited_gt_mism_sum": sum(1 for d in full if d["edited"]["mixtral"] + d["edited"]["falcon"] > d["edited_mism"]["mixtral"] + d["edited_mism"]["falcon"])}
    sens = s["edited"]["engaged_both_ge4"]["rate"]; spec = s["plain"]["engaged_both_ge4"]["rate"]; mm = s["edited_mism"]["engaged_both_ge4"]["rate"]
    s["gate_part2"] = {"rule": "edited engaged >= 0.50 AND plain engaged <= 0.11 AND edited_mism engaged <= 0.11 (set before running; judge can separate generated-style engaged from plain)",
                       "edited_ge_50": bool(sens is not None and sens >= 0.5), "plain_le_11": bool(spec is not None and spec <= 0.11),
                       "mism_le_11": bool(mm is not None and mm <= 0.11)}
    s["gate_part2"]["PASS"] = all(v for k, v in s["gate_part2"].items() if k != "rule")
    (OUT / "sens_summary.json").write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(s, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "judge":
        asyncio.run(judge())
    else:
        report()
