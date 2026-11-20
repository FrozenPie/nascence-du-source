"""J-2859 (F-3528): a book title the library cut at its 60-char file-name cap is shown to Du as a whole-word title
in the study scene line, the desk look and the READ affordance.
Hermetic: current_book is pointed at a temp file; sensorium state is a hand-set dict; nothing live is written
(the live bookmark/state files are stat-ed before and after).
Run: python scripts/_test_J-2859_scene_title_cut.py   (from the tree under test)"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import reading
from core import sensorium as S
from core import affordances as AF

ok_all = True


def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(("PASS " if cond else "FAIL ") + name)


_WATCH = [Path(r"C:\Nascence\data") / n for n in ("reading_state.json", "position.json", "room_state.json")]
_before = {p: (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None for p in _WATCH}

# --- [1] display_title unit cases (real stems from the 586 voice prompts in F-3528) ---
cases = {
    "The_Foundations_of_Science_Science_and_Hypothesis_The_Value": "The Foundations of Science Science and Hypothesis",
    "Complete_Project_Gutenberg_Collection_of_Memoirs_of_Napoleon": "Complete Project Gutenberg Collection of Memoirs",
    "Life_of_Johnson_Volume_5_Tour_to_the_Hebrides_1773_and_Journ": "Life of Johnson Volume 5 Tour to the Hebrides 1773",
    "Manual_of_the_Enumeration_A_Text_Book_on_the_Sciences_of_the": "Manual of the Enumeration A Text Book on the Sciences",
}
for stem, want in cases.items():
    got = reading.display_title(Path(stem + ".txt"))
    check(f"cut stem ({len(stem)}) -> whole words: {got!r}", got == want and len(got) < len(stem))
    check("  no dangling connective", got.split()[-1].lower() not in reading._TITLE_DANGLERS)
for stem in ("About_You", "Short_Title", "The_Sea_Shore", "A_Tale_of_Two_Cities", "Wild_Life_in_New_Zealand_Part_I"):
    check(f"short stem unchanged: {stem}", reading.display_title(Path(stem + ".txt")) == stem.replace("_", " "))
check("single long unbroken stem kept", reading.display_title(Path("X" * 60 + ".txt")) == "X" * 60)
check("never raises on junk", reading.display_title(None) in ("a book", "None") or isinstance(reading.display_title(None), str))

# --- [2] the three call sites render the clean title ---
tmp = Path(tempfile.mkdtemp(prefix="J-2859_"))
stem = "Life_of_Johnson_Volume_5_Tour_to_the_Hebrides_1773_and_Journ"
bk = tmp / (stem + ".txt")
bk.write_text("It was a dark and stormy page. " * 40, encoding="utf-8")
reading.current_book = lambda: bk            # sensorium/affordances import it by name at call time
S.state.clear()
S.state.update({"location": "study", "weather": "clear", "fire": "out"})
S._load = lambda: None
line = S.scene_line()
print(line[:260])
check("scene line carries the clean title", "'Life of Johnson Volume 5 Tour to the Hebrides 1773' lies open" in line)
check("scene line no longer carries the mid-word cut", "and Journ" not in line)
import core.study_life as SL
SL.look = lambda t: ""                       # the desk branch below it is what is under test (study_life writes provisions)
look = S.look("desk")
print(look[:200])
check("desk look carries the clean title", "'Life of Johnson Volume 5 Tour to the Hebrides 1773' lies open" in look)
check("study_life _book_display trims a cut title",
      SL._book_display(stem.replace("_", " ")) == "Life of Johnson Volume 5 Tour to the Hebrides 1773"
      and SL._book_display("Young Knights of the Empire  Their Code") == "Young Knights of the Empire")
check("READ affordance carries the clean title",
      "(Life of Johnson Volume 5 Tour to the Hebrides 1773)" in AF._read_reach())

# --- [3] canary ---
_after = {p: (p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else None for p in _WATCH}
check("live stores untouched", _before == _after)
print("ALL OK" if ok_all else "FAILURES")
sys.exit(0 if ok_all else 1)
