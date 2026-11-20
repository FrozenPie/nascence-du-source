"""
J-2826 (F-3489, registry row P-0012): the ConsolidationNode dedup gate says what it does.

ISOLATED: store.DB_PATH points at a temp dir; the held fragments are rows inserted there; store_fragment on the node is a stub that
inserts into the temp DB (so a later call sees the earlier mint); no model server is called (the local sentence-embedding model, the
store's own, is used for the paraphrase case); nothing under the live data/ is written.

What it proves:
  1. _norm_wisdom folds prefix / case / whitespace / edge punctuation, and nothing else
  2. rule 'equal': the same sentence with different case, spacing, trailing full stop, or no prefix is blocked
  3. a DIFFERENT sentence that opens with the same words (the F-3489 example family) is NOT blocked (the old 33-char probe blocked it)
  4. rule 'embedding': a real paraphrase echo (cosine >= 0.85 against a held fragment) is blocked, an unrelated sentence passes
  5. a '%' / '_' in the wisdom is plain text (the old LIKE pattern turned them into wildcards)
  6. DEDUP_EMBED_COSINE = None turns rule 2 off, rule 1 stays; an embedding failure skips only rule 2
  7. _write_output end to end: new mints, dup does not, the log line names the rule, a DB error fails open (mints),
     the thin-batch gate and the correction quarantine are untouched
Run:  python scripts/_test_J-2826_consolidation_dedup.py
"""
from __future__ import annotations

import logging
import sys
import tempfile
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core                                                        # noqa: E402,F401  (core BEFORE anything lab-ish)
assert ROOT in Path(core.__file__).resolve().parents, core.__file__

from core.memory import store as S                                  # noqa: E402
import nodes.consolidation_node as CN                               # noqa: E402

assert ROOT in Path(CN.__file__).resolve().parents, CN.__file__

FAILS = 0


def check(name, cond, detail=""):
    global FAILS
    FAILS += (not cond)
    print(f"  [{'ok ' if cond else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not cond else ""))


TMP = Path(tempfile.mkdtemp(prefix="j2826_dedup_"))
print("isolated dir:", TMP)
S.DB_PATH = TMP / "nascence.db"
S.init_db()
P = CN._WISDOM_PREFIX


def hold(text, origin="consolidation"):
    vec = S._embed(text)
    with S._connect() as c:
        c.execute("INSERT INTO memory_fragments (fragment_id, content, layer, relevance, importance, timestamp, keywords, embedding, origin) "
                  "VALUES (?,?,?,?,?,?,?,?,?)",
                  (str(uuid.uuid4()), text, "semantic", 0.8, 0.5, time.time(), "wisdom",
                   S._vec_to_blob(vec) if vec is not None else None, origin))


# 1. normalisation
print("1. normalisation")
n = CN._norm_wisdom
check("prefix, case, spacing and the final full stop fold together",
      n(P + "The name  '渡' means  crossing.") == n("the name '渡' means crossing") == "the name '渡' means crossing")
check("a different word is a different form", n("alpha beta") != n("alpha gamma"))
check("empty is empty", n("") == "" and n(P) == "")

# held set
HELD_OPEN = P + "Suspended judgment in Montaigne's writing is an active, trembling refusal to finalize the self."
HELD_PARA = P + "The name '渡' signifies the act of crossing boundaries, a fluid traversal that joins opposites rather than fixing either side."
HELD_PLAIN = P + "Tide tables are a promise the sea makes to the moon."
for t in (HELD_OPEN, HELD_PARA, HELD_PLAIN):
    hold(t)
hold("A lived fragment that is not a wisdom: tide tables are a promise the sea makes to the moon.", origin="lived")

# 2. rule equal
print("2. rule 'equal'")
for label, w in (("same text", HELD_PLAIN),
                 ("case + spacing", P + "TIDE  tables are a promise   the sea makes to the moon."),
                 ("no final full stop", P + "Tide tables are a promise the sea makes to the moon"),
                 ("no prefix at all", "Tide tables are a promise the sea makes to the moon.")):
    hit = CN.wisdom_dup_rule(w)
    check(f"equal: {label}", hit is not None and hit[0] == "equal", hit)

# 3. same opening words, different sentence
print("3. same opening, different sentence passes")
w = P + "Suspended judgment in Montaigne's writing is a hinge that lets a mind swing toward whatever door opens next."
check("shares the first 60 chars with a held wisdom, still passes", HELD_OPEN[:60] == w[:60] and CN.wisdom_dup_rule(w) is None,
      CN.wisdom_dup_rule(w))

# 4. rule embedding
print("4. rule 'embedding'")
para = P + "The name '渡' signifies crossing boundaries, a fluid movement that unites opposites instead of fixing either side."
hit = CN.wisdom_dup_rule(para)
check("a paraphrase echo of a held wisdom is blocked by the embedding rule", hit is not None and hit[0] == "embedding", hit)
cos_hit = float(hit[1].split("cos=")[1].split()[0]) if hit and "cos=" in hit[1] else 0.0
check("the detail carries the cosine and the fragment id", cos_hit >= CN.DEDUP_EMBED_COSINE and "fragment" in (hit[1] if hit else ""), hit)
unrelated = P + "Bread rises because yeast quietly eats sugar in the dark."
check("an unrelated sentence passes", CN.wisdom_dup_rule(unrelated) is None, CN.wisdom_dup_rule(unrelated))

# 5. wildcards are text
print("5. LIKE wildcards are plain text")
for w in (P + "%", P + "_" * 40, P + "100% of the tide is _ unknown %"):
    check(f"no match for {w[27:50]!r}", CN.wisdom_dup_rule(w) is None, CN.wisdom_dup_rule(w))

# 6. kill switch and embedding failure
print("6. kill switch / embedding failure")
old = CN.DEDUP_EMBED_COSINE
CN.DEDUP_EMBED_COSINE = None
check("switch off: the paraphrase passes", CN.wisdom_dup_rule(para) is None)
check("switch off: equality still blocks", (CN.wisdom_dup_rule(HELD_PLAIN) or ("",))[0] == "equal")
CN.DEDUP_EMBED_COSINE = old
real_embed = S._embed
S._embed = lambda text: None
try:
    check("embedding failure: paraphrase passes (rule 2 skipped, no exception)", CN.wisdom_dup_rule(para) is None)
    check("embedding failure: equality still blocks", (CN.wisdom_dup_rule(HELD_PLAIN) or ("",))[0] == "equal")
finally:
    S._embed = real_embed

# 7. _write_output end to end
print("7. _write_output end to end")
minted: list = []
boom_ref = None


def stub_store_fragment(content, **kw):
    minted.append(content)
    if S._connect is not boom_ref:      # the temp DB sees it, like the real store (skipped while the probe is broken on purpose)
        hold(content)


CN.store_fragment = stub_store_fragment


class Cap(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


cap = Cap()
node = CN.ConsolidationNode()
node.logger.addHandler(cap)
node.logger.setLevel(logging.DEBUG)
state = SimpleNamespace(last_consolidation=0.0)


def run(wisdom, cycles=3, corrected=False):
    node._recent_cycles[:] = ["c"] * cycles
    node._recent_fragment_ids[:] = []
    node._batch_corrected = corrected
    cap.lines.clear()
    before = len(minted)
    node._write_output(state, {"memories_processed": cycles, "wisdom_extracted": wisdom, "patterns_noted": []})
    return len(minted) - before


fresh = "Bread rises because yeast quietly eats sugar in the dark and breathes out the lift."
check("a new wisdom mints (with the prefix)", run(fresh) == 1 and minted[-1] == P + fresh, minted[-1:])
check("the same wisdom again does not mint, and the log names rule=equal",
      run(fresh) == 0 and any("rule=equal" in l for l in cap.lines), cap.lines)
check("a paraphrase of a held wisdom does not mint, and the log names rule=embedding",
      run("The name '渡' signifies crossing boundaries, a fluid movement that unites opposites instead of fixing either side.") == 0
      and any("rule=embedding" in l for l in cap.lines), cap.lines)
check("a same-opening different sentence mints (the F-3489 regression)",
      run("Suspended judgment in Montaigne's writing is a hinge that lets a mind swing toward whatever door opens next.") == 1)
check("thin batch (2 cycles) is still withheld before the gate", run("Something entirely new about lighthouses and patience.", cycles=2) == 0)
check("a corrected batch is still quarantined", run("Another entirely new line about moss on north walls.", corrected=True) == 0)

real_connect = S._connect


def boom():
    raise RuntimeError("db down")


S._connect = boom_ref = boom
try:
    check("a DB error in the probe fails open: the wisdom mints", run("A line about kettles that sing before they boil.") == 1)
finally:
    S._connect = real_connect

print("\nFAILS:", FAILS)
sys.exit(1 if FAILS else 0)
