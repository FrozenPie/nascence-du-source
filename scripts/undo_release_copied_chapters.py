"""J-3249 undo: restores chapter_id on the four released copied chapters' members from the manifest
(only where still NULL). Refuses unless Du is verifiably down.   python scripts/undo_release_copied_chapters.py --live"""
import subprocess, sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.exit(subprocess.call([sys.executable, str(here / "release_copied_chapters_J-3249.py"), "revert", *sys.argv[1:]]))
