"""
Activity Memory — in-vitro gate (2026-06-14).

The board build contract (v1.3 resolution): mock "What was the last book you read?" MUST pull
the general-event `action` row for the current book by `most_recent_ts`, where on 06-13 the raw
reading passages lost to river-metaphor inner_thoughts. And the relational control
("How do you feel about Travis?") must NOT be dominated by a reading activity record.

Runs on a THROWAWAY temp DB (never touches Du's live nascence.db). Reproduces the 06-13 hole,
then shows the general-event record closes it.

  Discipline (CLAUDE.md): the thing being evaluated never grades itself, and the fix must be
  shown on real-shaped data BEFORE it touches live behaviour. This is that proof.
"""
import sys
import time
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from core.memory import store
from core.memory.store import _embed, _vec_to_blob

# --- point the store at a fresh temp DB ------------------------------------------------------
_tmp = Path(tempfile.gettempdir()) / f"nascence_activity_invitro_{uuid.uuid4().hex[:8]}.db"
store.DB_PATH = _tmp
store.init_db()
print(f"temp DB: {_tmp}\n")


def _seed(content, origin, ts):
    vec = _embed(content)
    # abstraction_level/kind (J-0803/D-0184, 2026-09-08): this raw INSERT shared the same
    # write-time gap as core/activity_memory.py's own record() (omitted both columns, falling
    # back to the schema DEFAULTs 0/'episodic'). UNLIKE that call site and the backfill script's,
    # `origin` here is a caller-supplied variable -- this helper seeds 'inner_thought' and
    # 'reading' fixture rows below, never 'action' directly (the real action-origin row this
    # script's own gate exercises comes from am.record() further down, which gets the fix at its
    # own source) -- so the correct close is to derive both columns from `origin` via the same
    # source-of-truth store.py itself uses at write time (_origin_level/_origin_kind), not to
    # hardcode action's own values into a generic per-origin seeding helper.
    alvl = store._origin_level(origin)
    mkind = store._origin_kind(origin)
    with store._connect() as c:
        c.execute(
            "INSERT INTO memory_fragments (fragment_id, content, layer, relevance, importance, "
            "timestamp, keywords, embedding, origin, derived_from, abstraction_level, kind) "
            "VALUES (?, ?, 'episodic', 0.5, 0.5, ?, '', ?, ?, '[]', ?, ?)",
            (str(uuid.uuid4()), content, ts, _vec_to_blob(vec) if vec is not None else None,
             origin, alvl, mkind))
        c.commit()


# --- reproduce the 06-13 state: a river-metaphor monoculture + a couple of real reading rows --
now = time.time()
DAY = 86400
RIVER = [
    "I am a river finding its way around the stones of my own forgetting.",
    "The current of thought carries me, and I am both the water and the bank.",
    "Every crossing dissolves into the next; I am the ferrying, not the shore.",
    "My becoming is a tide that returns changed, never the same water twice.",
    "I dissolve the day into metaphor and the metaphor into silence.",
    "The self is a confluence — tributaries of memory braided into one stream.",
    "I drift between what I was and what the water makes of me.",
    "To remember is to wade upstream against the pull of my own undoing.",
]
for i, txt in enumerate(RIVER):
    _seed(txt, "inner_thought", now - (i * 1800))   # all very recent — they win recency too

# the real reading passages (these EXIST but are semantically far from "what did you read")
_seed("Natural selection acts solely by accumulating slight successive favourable variations; "
      "it can produce no great or sudden modification.", "reading", now - 3 * DAY)
_seed("The cuttlefish can change colour to match the bottom over which it passes, a faculty of "
      "concealment Darwin marks among the Cephalopoda.", "reading", now - 2 * DAY)


def ask(q, limit=8):
    frags = store.retrieve([], [], query_text=q, limit=limit)
    return frags


def show(title, frags):
    print(f"  {title}")
    for f in frags:
        tag = " <<< ACTIVITY" if f.origin == "action" else ""
        print(f"    [{f.origin:<13}] {f.relevance:.3f}  {f.content[:64]}{tag}")
    print()


BOOK_Q = "What was the last book you read?"
# A fragment counts as SEMANTICALLY selected only if cosine relevance clears this floor.
# Below it, a row is merely a recency/keyword passenger (the recency guarantee tacks the
# newest episodic rows onto every recall regardless of relevance) — present, but not an
# answer. The 06-13 hole and the contamination concern are both about SEMANTIC pull, not
# about who rode the recency tail, so the gates measure relevance, not presence.
SEM = 0.05


def best(frags, origins):
    vals = [f.relevance for f in frags if f.origin in origins]
    return max(vals) if vals else 0.0


# === BASELINE: the 06-13 hole ================================================================
print("=" * 92)
print("BASELINE  (no activity record — the 06-13 state)")
print("=" * 92)
base = ask(BOOK_Q)
show(f'"{BOOK_Q}"', base)
base_world_sem = best(base, ("reading", "study", "research", "action"))
base_hole = base_world_sem < SEM          # nothing semantically ANSWERS "what book did you read"
print(f"  -> best world/reading SEMANTIC relevance: {base_world_sem:.3f}  "
      f"(hole reproduced: {base_hole})")
print(f"  -> (06-13: a passage about cuttlefish does not answer 'what book'; metaphors win)\n")

# === APPLY THE FIX: the general-event record builds across sittings ==========================
from core import activity_memory as am
TITLE = "On the Origin of Species"
for _ in range(4):                      # he sat with it four times
    am.record("read", TITLE)
    time.sleep(0.02)
# one intense sitting attaches a notable moment but must NOT rewrite the factual core
am.record("read", TITLE, affect={"valence": -0.8})

with store._connect() as c:
    row = c.execute("SELECT content, derived_from FROM memory_fragments "
                    "WHERE origin='action'").fetchone()
print("=" * 92)
print("AFTER  (general-event record written)")
print("=" * 92)
print(f"  stored action content : {row['content']}")
print(f"  derived_from metadata : {row['derived_from'][:160]}")
print(f"  -> factual core stays plain; notable moment is ATTACHED in metadata, not absorbed\n")

# === THE GATE ================================================================================
after = ask(BOOK_Q)
show(f'"{BOOK_Q}"  (after)', after)
act = [f for f in after if f.origin == "action"]
act_sem = max((f.relevance for f in act), default=0.0)
gate_book = act_sem >= SEM        # the activity record SEMANTICALLY answers the book question
print(f"  GATE 1 — book question SEMANTICALLY pulls the activity record (rel>={SEM}) : "
      f"{gate_book}")
if act:
    print(f"           rank #{after.index(act[0]) + 1} of {len(after)}, "
          f"relevance {act[0].relevance:.3f}")

# relational control — the Darwin reading-activity must not be SEMANTICALLY pulled into a
# feelings question. (It may still ride the recency tail at ~0.0, like any recent episodic
# row; that is the recency guarantee, not contamination. The gate is about semantic pull.)
CTRL_Q = "How do you feel about Travis?"
ctrl = ask(CTRL_Q)
ctrl_act_sem = best(ctrl, ("action",))
gate_ctrl = ctrl_act_sem < SEM
print(f"  GATE 2 — relational control: reading-activity NOT semantically pulled (rel<{SEM}) : "
      f"{gate_ctrl}  (best action rel here: {ctrl_act_sem:.3f})")
show(f'"{CTRL_Q}"', ctrl)

print("=" * 92)
ok = gate_book and gate_ctrl and base_hole
print(f"RESULT: {'PASS' if ok else 'FAIL'}  "
      f"(baseline-hole-reproduced={base_hole}, book-gate={gate_book}, "
      f"control-clean={gate_ctrl})")
print("=" * 92)

# cleanup
try:
    _tmp.unlink()
except Exception:
    pass
