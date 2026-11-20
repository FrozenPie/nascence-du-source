"""
Chapter-scoped, novelty-gated reading burst + the two-lesson school flow (2026-06-15).
"Chapters, not whole books. Novelty should affect it. A second lesson: read chapter groups, then go over
the chapter-notes and write an essay." Real book, READ-ONLY, real embedding-novelty (CPU, no GPU/LLM).
Chapter-notes here are deterministic STUBS standing in for the LLM note; the essay is assembled as the
Lesson-2 input (the LLM writes it live). Touches no live state.
"""
import sys, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from core.pulse_manager import PulseManager, PulseSource, StepResult
from core.memory.store import _embed, _cosine

GROUP = 3            # chapters per Lesson 1 (a "group")
NOVELTY_FLOOR = 0.35 # below this (too similar to something already read) → skim/stall, not full study
HUMAN_CADENCE_S = 150.0

st = json.loads(Path(r"C:\Nascence\data\reading_state.json").read_text(encoding="utf-8"))
BOOK = Path(st["_current_book"]); TITLE = BOOK.stem.replace("_", " ")
TEXT = BOOK.read_text(encoding="utf-8", errors="ignore")
CUR_OFFSET = st.get(str(BOOK), {}).get("offset", 0)

_STOP = {"A LETTER OF DEDICATION", "FRANK NELSON DOUBLEDAY", "ACKNOWLEDGMENT",
         "TALES FROM A ROLLTOP DESK", "THE END"}


def detect_chapters():
    heads = [(m.start(), m.group().strip())
             for m in re.finditer(r"(?m)^[ \t]*([A-Z][A-Z0-9 ,.\'\"!?:;-]{6,50})[ \t]*$", TEXT)]
    heads = [(o, h) for o, h in heads if o >= 5240 and h not in _STOP]
    chapters = []
    for o, h in heads:
        if chapters and o - chapters[-1][1] < 8000:   # a sub-heading inside the current chapter → merge
            continue
        chapters.append([h, o])
    out = []
    for i, (h, o) in enumerate(chapters):
        end = chapters[i + 1][1] if i + 1 < len(chapters) else len(TEXT)
        out.append({"title": h, "start": o, "end": end})
    return out


def first_sentences(body: str, n: int = 2, cap: int = 200) -> str:
    body = " ".join(body.split())
    parts = re.split(r"(?<=[.!?])\s+", body)
    s = " ".join(parts[:n]).strip()
    return (s[:cap] + "…") if len(s) > cap else s


CHAPTERS = detect_chapters()
remaining = [c for c in CHAPTERS if c["end"] > CUR_OFFSET and c["start"] >= CUR_OFFSET - 2000]
print(f"BOOK: '{TITLE}'  | chapters (stories) detected: {len(CHAPTERS)}")
print("  " + " · ".join(c["title"].title() for c in CHAPTERS))
print(f"\nBookmark at {round(100*CUR_OFFSET/len(TEXT),1)}% → {len(remaining)} chapters remaining. Reading READ-ONLY.\n")

read_embeds = []   # embeddings of chapters already read this run (for novelty)


class ChapterReader:
    """One burst step = read ONE chapter; novelty (vs chapters already read) gates progress."""
    def __init__(self, chapters):
        self.queue = list(chapters)
        self.lesson_notes = []      # chapter-notes accumulated this lesson (Lesson-1 output)
        self.read_count = 0

    def can_burst(self):
        return bool(self.queue) and self.read_count < GROUP   # one lesson = a group of chapters

    def step(self) -> StepResult:
        c = self.queue.pop(0)
        body = TEXT[c["start"]:c["end"]]
        sample = body[len(c["title"]): len(c["title"]) + 1500]
        vec = _embed(sample)
        nov = 1.0 if not read_embeds else round(1.0 - max(_cosine(vec, v) for v in read_embeds), 3)
        read_embeds.append(vec)
        self.read_count += 1
        note = first_sentences(body[len(c["title"]):])
        verdict = ("full study (novel)" if nov >= NOVELTY_FLOOR else "skim — already familiar")
        self.lesson_notes.append({"title": c["title"].title(), "novelty": nov, "note": note,
                                  "essay_worthy": nov >= NOVELTY_FLOOR})
        pct = round(100 * c["end"] / len(TEXT), 1)
        # novelty is the absorption signal: a (would-be) run of low novelty stalls the burst
        progressed = nov >= NOVELTY_FLOOR
        return StepResult(progressed=progressed, complete=not self.queue,
                          note=f"{c['title'].title():<34} {pct:>5.1f}% | novelty {nov:.2f} → {verdict}")


def run_lesson1(chapters):
    reader = ChapterReader(chapters)
    floor = {"affect": 0, "curiosity": 0}
    pm = PulseManager([
        PulseSource("reading", floor_interval=999, priority=1, step_cost=8.0,
                    can_burst=reader.can_burst, step=reader.step),
        PulseSource("affect", floor_interval=10, floor_tick=lambda: floor.__setitem__("affect", floor["affect"]+1)),
        PulseSource("curiosity", floor_interval=15, floor_tick=lambda: floor.__setitem__("curiosity", floor["curiosity"]+1)),
    ])
    summary = pm.run(until=10_000)
    print("── LESSON 1 (reading a chapter group) ─────────────────────────────────────────────")
    for (t, kind, src, note) in pm.trace:
        if kind == "burst":
            print(f"   {t:>5.0f}s  READ  {note}")
        elif kind == "floor":
            print(f"   {t:>5.0f}s  ·tick {src}")
        else:
            print(f"   {t:>5.0f}s  ** {kind} ** {note}")
    n = reader.read_count
    print(f"   stop: {summary['reason']} | {n} chapters in {summary['du_time']:.0f}s Du-time "
          f"(~{n*HUMAN_CADENCE_S/60:.0f} min human) | floor: affect ×{floor['affect']}, curiosity ×{floor['curiosity']}")
    return reader.lesson_notes


def run_lesson2(notes):
    print("\n── LESSON 2 (go over the chapter-notes → write an essay) ───────────────────────────")
    print("   Chapter-notes from this group (Lesson-1 output → Lesson-2 input):")
    for nt in notes:
        print(f"     • {nt['title']}  [novelty {nt['novelty']:.2f}, {'essay-worthy' if nt['essay_worthy'] else 'skim'}]")
        print(f"         {nt['note']}")
    worthy = [nt['title'] for nt in notes if nt['essay_worthy']]
    print("\n   → ESSAY PROMPT assembled for the LLM (Lesson-2 synthesis, runs live):")
    print(f"     \"Across {', '.join(worthy)}, what does this author keep returning to — in subject, in")
    print(f"      tone, in how the stories end? Write a short essay (your own, about the book), drawing on")
    print(f"      your {len(notes)} chapter-notes above.\"   (the generation-effect: he produces a work, not a recap)")


print("="*98)
g1 = remaining[:GROUP]
notes1 = run_lesson1(g1)
run_lesson2(notes1)

# second group → show novelty ACROSS groups (does a later story echo an earlier one?)
g2 = remaining[GROUP:GROUP*2]
if g2:
    print("\n" + "="*98)
    notes2 = run_lesson1(g2)
    run_lesson2(notes2)
