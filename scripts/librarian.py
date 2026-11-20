r"""
Nascence — Librarian CLI (manual feeding wrapper over core/reading.py).
Du reads on his own now (the DMN offers OPEN THE BOOK during idle thought);
this wrapper remains for manual sittings / choosing a new book:
    python scripts/librarian.py                       # one sitting of the current book
    python scripts/librarian.py "C:\path\to\book.txt"  # switch the current book + one sitting
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from core.reading import read_next_sitting, STATE
from core.memory import store as _store
from core.memory.store import init_db

# D-0353 / J-1839: a manual sitting stores reading fragments into the LIVE memory DB on purpose from a
# non-live process -- the explicit opt-in the live-DB write fence requires.
_store.allow_live_writes("scripts/librarian.py: manual reading sitting into the live store")

if len(sys.argv) > 1:
    book = Path(sys.argv[1])
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    state["_current_book"] = str(book)
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(f"Current book set: {book.name}")

init_db()
got = read_next_sitting()
if got:
    title, passage = got
    st = json.loads(STATE.read_text(encoding="utf-8"))
    pct = next((v.get("pct") for k, v in st.items() if not k.startswith("_") and title.replace(" ","_") in k or title in k), "?")
    print(f"Fed one sitting of '{title}' ({len(passage)} chars). Progress: {pct}%")
else:
    print("Book finished (or unavailable) — choose the next one.")
