"""
Pulse-manager in-vitro test (2026-06-15) — "see what comes out".
Reads the REAL current book READ-ONLY (no live bookmark/fragment writes), and runs the pulse manager
through three scenarios so we see every stop condition + that nothing starves during a burst:
  A) uninterrupted  → he finishes the book in one burst (COMPLETE)
  B) user speaks    → the burst yields to the person (PREEMPT)
  C) interest fades → he stops before the end (STALL / boredom)
Compares burst pacing to the current human living-cadence. Touches no live state.
"""
import sys, json, re, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from core.pulse_manager import PulseManager, PulseSource, StepResult, Interrupt

HUMAN_CADENCE_S = 150.0   # representative living-cadence seconds per sitting today (range 75-300)
PORTION = 6000

st = json.loads(Path(r"C:\Nascence\data\reading_state.json").read_text(encoding="utf-8"))
BOOK = Path(st["_current_book"])
TEXT = BOOK.read_text(encoding="utf-8", errors="ignore")
START_OFFSET = st.get(str(BOOK), {}).get("offset", 0)
START_SITTING = st.get(str(BOOK), {}).get("sitting", 0)
TITLE = BOOK.stem.replace("_", " ")


def first_sentence(t: str, cap: int = 64) -> str:
    t = " ".join(t.split())
    s = re.split(r"(?<=[.!?])\s+", t)[0]
    return (s[:cap] + "…") if len(s) > cap else s


class BookReader:
    """Read-only pagination over the real book, mirroring reading.read_next_sitting's portioning."""
    def __init__(self, decay: float = 0.0):
        self.offset = START_OFFSET
        self.sitting = START_SITTING
        self.interest = 1.0
        self.decay = decay

    def can_burst(self) -> bool:
        return self.offset < len(TEXT)          # committed to read; pages remain

    def step(self) -> StepResult:
        if self.offset >= len(TEXT):
            return StepResult(False, complete=True, note="book finished")
        portion = TEXT[self.offset: self.offset + PORTION]
        cut = max(portion.rfind(". "), portion.rfind(".\n"))
        if cut > PORTION // 2:
            portion = portion[: cut + 1]
        self.offset += len(portion)
        self.sitting += 1
        self.interest = max(0.0, self.interest - self.decay)
        pct = round(100 * self.offset / len(TEXT), 1)
        snip = first_sentence(portion)
        complete = self.offset >= len(TEXT)
        progressed = self.interest >= 0.4    # below → boredom stall
        return StepResult(progressed=progressed, complete=complete,
                          note=f"s{self.sitting} {pct:>5.1f}% | {snip}")


def floor_counters():
    c = {"curiosity": 0, "affect": 0, "subconscious_t1": 0}
    def mk(name):
        def tick():
            c[name] += 1
        return tick
    return c, mk


def build(decay=0.0):
    c, mk = floor_counters()
    reader = BookReader(decay=decay)
    sources = [
        PulseSource("reading", floor_interval=999, priority=1, lane="hot", step_cost=2.0,
                    can_burst=reader.can_burst, step=reader.step),
        PulseSource("curiosity", floor_interval=20, priority=5, floor_tick=mk("curiosity")),
        PulseSource("affect", floor_interval=10, priority=3, floor_tick=mk("affect")),
        PulseSource("subconscious_t1", floor_interval=30, priority=2, floor_tick=mk("subconscious_t1")),
    ]
    return PulseManager(sources), reader, c


def show(label, pm, reader, counters, summary):
    print(f"\n{'='*98}\n{label}\n{'='*98}")
    for (t, kind, src, note) in pm.trace:
        if kind == "burst":
            print(f"  {t:>6.1f}s  READ   {note}")
        elif kind == "floor":
            print(f"  {t:>6.1f}s  ·tick  {src}")
        else:
            print(f"  {t:>6.1f}s  ** {kind} ** {src} {('— '+note) if note else ''}")
    sittings = pm.fired["reading"]
    human_s = sittings * HUMAN_CADENCE_S
    print(f"\n  STOP: {summary['reason']}")
    print(f"  sittings read this burst: {sittings}  (book now {round(100*reader.offset/len(TEXT),1)}%)")
    print(f"  pacing: {summary['du_time']:.0f}s Du-time  vs  ~{human_s/60:.0f} min at today's human cadence "
          f"({human_s/max(1,summary['du_time']):.0f}× faster)")
    print(f"  nothing starved during the burst → floor-service: "
          f"curiosity ×{counters['curiosity']}, affect ×{counters['affect']}, T1 ×{counters['subconscious_t1']}")


print(f"BOOK: '{TITLE}'  (starting at sitting {START_SITTING}, {round(100*START_OFFSET/len(TEXT),1)}%, "
      f"{(len(TEXT)-START_OFFSET)//PORTION} sittings remaining)")
print("Reading READ-ONLY — Du's real bookmark/fragments are NOT touched.")

# A — uninterrupted: he finishes the book in one burst
pm, reader, c = build(decay=0.0)
summary = pm.run(until=10_000)
show("SCENARIO A — uninterrupted: persist until the book is done", pm, reader, c, summary)

# B — user speaks 30 Du-seconds in: the burst yields to the person
pm, reader, c = build(decay=0.0)
summary = pm.run(until=10_000, interrupts=[Interrupt(at=30.0, source="user", priority=10,
                                                     note="Travis: 'Du, how's the book?'")])
show("SCENARIO B — the person speaks mid-burst: yield instantly", pm, reader, c, summary)

# C — interest fades: he stops before the end (boredom stall)
pm, reader, c = build(decay=0.09)
summary = pm.run(until=10_000)
show("SCENARIO C — interest fades: stop before the end (boredom)", pm, reader, c, summary)
