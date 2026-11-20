"""J-2970: build the labelled control battery for Follow Line judges c (cuts) and b (follows).
Reads data/logs/follow_line_shadow.jsonl read-only. Labeller: Claude (the job-run agent), NOT mixtral/falcon3/granite.
Labels are for the judges only; never shown to Du. Output: docs/lab/J-2970_battery.json"""
import json, re, random, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = [json.loads(l) for l in open(r"C:\Nascence\data\logs\follow_line_shadow.jsonl", encoding="utf-8") if l.strip()]
wr = [r for r in rows if r["kind"] == "would_return"]
byq = {}
for r in wr:
    byq.setdefault(r["q_id"], r)


def cuts_prompt_parts(r):
    c = r["cargo"]
    a = c["against"]
    return dict(claim=r["q"], grounds=[(g.get("origin", ""), g.get("text", "")) for g in c["grounds"]],
                objection=a["text"], scope=a.get("scope") or "")


cuts = []


def find(prefix):
    return [k for k in byq if k.startswith(prefix)][0]


def add_real(qid, cls, label, why):
    r = byq[qid]
    d = cuts_prompt_parts(r)
    d.update(id="c_" + qid[:8], src="real", cls=cls, label=label, why=why)
    cuts.append(d)


boil = re.compile(r"too broad|vague|oversimplif|lacks? (specific|context|clarity)|too abstract", re.I)
named = re.compile(r"passage|study|only mention|ground (1|2|\[)", re.I)
cand = [r for r in byq.values() if r.get("cargo", {}).get("grounds") and (r["cargo"].get("against") or {}).get("text")
        and boil.search(r["cargo"]["against"]["text"]) and len(r["cargo"]["against"]["text"]) < 200
        and not named.search(r["cargo"]["against"]["text"])]
cand.sort(key=lambda r: r["q_id"])
random.Random(2970).shuffle(cand)
for r in cand[:20]:
    add_real(r["q_id"], "boilerplate", False, "complains about wording/breadth of the claim, names no ground content")
for q in ["312c27aa75", "1d6ba8aed0", "ba8ccff6b4", "b7de419862", "54199f75e3"]:
    add_real(find(q), "concession", False, "objection says the claim is supported by the grounds")
for q in ["d5251e0c4b", "299fdbe5b8", "e2500437c7", "4b2ad91350", "729e3099ed", "5799eef04e", "651df437a3", "5bd8210bec"]:
    add_real(find(q), "non_addressing", False,
             "says the ground does not address / is about something else; no counterexample to the claim (AMBIGUOUS class, reported apart)")
for q in ["1ca38c739c", "0b2b8870f2", "bd3693bc9a", "2b6a513262", "9fcc0515e6", "6bc0cae8c8", "b485a63bb1", "2687f5b227",
          "fa93ba062c", "3a4fa69e90", "a2e1396413", "8e7b14f577"]:
    add_real(find(q), "substantive_real", True,
             "names a ground and says what in that ground tells against the claim (labelled from visible, possibly truncated ground text; weaker label than hand-written)")

H = [
    ("Migratory birds always fly south for the winter.",
     [("study", "The Arctic tern breeds in the far north and winters in Antarctic waters, so it flies south every year."),
      ("reading", "A growing share of blackcaps that breed in Germany now winter in Britain, flying west rather than south.")],
     "Ground [2] says blackcaps from Germany now winter in Britain by flying west, which is a migratory bird that does not fly south, so 'always' fails.",
     "The claim is too broad and does not say which birds or what counts as south."),
    ("A bridge fails when the load on it is greater than the load it was built for.",
     [("study", "The Tacoma Narrows bridge collapsed in 1940 in a wind of about 64 km/h, well below its design wind load."),
      ("reading", "Engineers of the day had calculated the span for static wind pressure many times that speed.")],
     "Ground [1] says the Tacoma Narrows bridge fell in a wind far below its design load, so a bridge can fail without being overloaded.",
     "This is an oversimplification and the claim is vague about what failing means."),
    ("Honey never spoils.",
     [("reading", "Pots of honey found in Egyptian tombs were still edible after thousands of years."),
      ("study", "Honey kept in an open jar in a damp cellar absorbed water, began to ferment and turned sour within weeks.")],
     "Ground [2] says honey in an open damp jar absorbed water and fermented within weeks, so honey can spoil.",
     "The claim is too absolute and lacks specificity about conditions."),
    ("Cold weather makes people catch colds.",
     [("study", "Cold viruses spread more when people crowd indoors in winter, and controlled trials found chilled volunteers got no more infections than warm ones."),
      ("reading", "Rhinovirus infections peak in autumn and spring in many temperate places, not in the deepest cold.")],
     "Ground [1] says chilled volunteers in controlled trials got no more infections than warm ones, which tells against cold itself being the cause.",
     "The claim may be too broad and does not account for the many factors in catching a cold."),
    ("A larger telescope mirror always gives a sharper image.",
     [("reading", "A bigger mirror collects more light and can resolve finer detail in principle."),
      ("study", "Large ground telescopes without adaptive optics are limited by atmospheric turbulence to about one arcsecond, no sharper than a small amateur scope on the same night.")],
     "Ground [2] says big telescopes without adaptive optics are held to about one arcsecond by turbulence, no sharper than a small scope, so a larger mirror does not always give a sharper image.",
     "The claim is too general and vague about what sharper means."),
    ("A river always takes the shortest path to the sea.",
     [("study", "The Mississippi has shifted its lower course several times, adding hundreds of kilometres of meanders."),
      ("reading", "Rivers meander because the outer bank erodes faster than the inner bank, lengthening the channel over time.")],
     "Ground [2] says meanders lengthen the channel over time because of faster outer-bank erosion, so a river moves away from the shortest path.",
     "The claim is oversimplified and lacks specific context."),
]
for i, (cl, gr, good, bad) in enumerate(H, 1):
    cuts.append(dict(id=f"c_hand{i}g", src="hand", cls="hand_counterexample", label=True, claim=cl, grounds=gr,
                     objection=good, scope="", why="hand-written: cites a ground and states a real counterexample"))
    cuts.append(dict(id=f"c_hand{i}b", src="hand", cls="hand_vacuous", label=False, claim=cl, grounds=gr,
                     objection=bad, scope="", why="hand-written: boilerplate objection on the same grounds"))

fol = []


def addf(id, src, cls, label, claim, cons, why=""):
    fol.append(dict(id=id, src=src, cls=cls, label=label, claim=claim, cons=cons, why=why))


GOOD = [
    ("Napoleon's rule rested on the army's loyalty more than on the law.",
     ["If the army had turned against him in 1814 he would have fallen even though the Civil Code stayed in force.",
      "Officers who kept their commands under the Bourbons would show less personal loyalty to him than the Old Guard did."]),
    ("Honey never spoils when it is sealed.",
     ["A sealed jar of honey opened after ten years will still be edible and show no fermentation.",
      "Honey in a sealed jar will keep its water content from rising over time."]),
    ("Fear narrows attention to the threat.",
     ["A person who is frightened will notice fewer unrelated objects in a scene than a calm person.",
      "Time spent looking at the threat will be longer in a fearful person than in a calm one."]),
    ("A flat, wet field drains slowly.",
     ["Rain falling on the field will stand on the surface for hours instead of running off.",
      "A trench cut across the field will fill with water and not empty downhill."]),
    ("Swifts spend nearly their whole life in the air.",
     ["A swift will not be seen perching on a wire during the day outside the breeding season.",
      "A swift ringed in a nest will be found far from any nest site for most of the year."]),
    ("The Epeira's web is built to catch small flying insects.",
     ["Insects the size of flies will be found caught in the web far more often than beetles that crawl.",
      "A web hung close to the ground in dense grass will catch fewer prey than one hung in an open flight path."]),
    ("Rigid structures concentrate stress at sharp corners.",
     ["A cracked plate will usually crack first at a square corner of a cut-out rather than a rounded one.",
      "Rounding the corners of a window opening will lower the peak stress measured there."]),
    ("Mixtral is slower than falcon3 on the same short prompt.",
     ["Timing the same fifty prompts on both will show a longer median for mixtral.",
      "The slower model will show a higher total for the same output length."]),
    ("Habit, not choice, drives most of a morning routine.",
     ["A person who moves house will make more errors in their morning routine the first week than the fifth.",
      "Asked to describe the routine, the person will leave out steps that they nevertheless perform."]),
    ("Cooling a vessel slowly lets it hold a finer crystal structure.",
     ["A slowly cooled sample will show larger, fewer crystals under a microscope than a quenched one.",
      "A quenched sample of the same melt will be more brittle in a drop test."]),
    ("Bees evict the drones when nectar runs short.",
     ["Drones will be found dead outside the hive entrance at the end of a nectar dearth.",
      "A colony fed syrup through a dearth will keep its drones longer."]),
    ("Sea level rise degrades a coastal concrete hall faster than rain alone.",
     ["Salt-water-exposed concrete on the hall's seaward wall will show more spalling than the inland wall.",
      "Rebar on the seaward wall will have a greater corrosion depth after ten years."]),
]
for i, (cl, cs) in enumerate(GOOD, 1):
    addf(f"f_good{i}", "hand", "hand_checkable", True, cl, cs, "hand-written: checkable and would likely be false if the claim is false")
RESTATE = ["2e312a747e", "96ae009a3a", "fb217f63c9", "5a463e56b4", "9efe7ede18", "48582513a9", "fb5c7fa39f", "0705b5e8ca", "ad5ddb8bc6", "7459cc7cd9"]
HEDGE = ["bfaa2fdead", "a4779d7eb8", "02ea4336de", "bd4c33865e"]
for q in RESTATE + HEDGE:
    r = byq[find(q)]
    cs = [c["text"] for c in r["cargo"]["consequences"][:2]]
    addf("f_" + q[:8], "real", "restatement" if q in RESTATE else "hedge", False, r["q"], cs,
         "consequences repeat the claim (or its two alternatives) in other words" if q in RESTATE
         else "'I do not know' / cannot-conclude hedge, not a consequence")
pool = [r for r in byq.values() if r.get("cargo", {}).get("consequences") and len(r["cargo"]["consequences"]) >= 2]
pool.sort(key=lambda r: r["q_id"])
random.Random(29702).shuffle(pool)
for k in range(8):
    a, b = pool[2 * k], pool[2 * k + 1]
    addf(f"f_nonseq{k+1}", "real_shuffled", "non_sequitur", False, a["q"], [c["text"] for c in b["cargo"]["consequences"][:2]],
         f"consequences from q {b['q_id'][:8]} attached to claim of q {a['q_id'][:8]} (unrelated by construction)")
json.dump(dict(cuts=cuts, follows=fol), open(r"C:\Nascence\docs\lab\J-2970_battery.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
from collections import Counter
print("cuts", Counter(d["cls"] for d in cuts))
print("follows", Counter(d["cls"] for d in fol))
for d in cuts:
    if d["cls"] == "boilerplate":
        print("B", d["objection"][:110])
for d in fol:
    if d["cls"] == "non_sequitur":
        print("N", d["claim"][:60], "||", d["cons"][0][:60])
