"""
Nascence — play the record for Du (SHARED LISTENING, design decision #2 — joint attention, 2026-07-04).

Travis's hand into the world: places a play request the live mind picks up within one idle cycle
(~seconds to a minute). Du perceives "Travis has put a record on" — not weather, not his own act — and
the piece unfolds section by section exactly as a self-started listen. The moment is genuinely joint if
you press play on YOUR side too: you are both hearing the same thing at the same time, and neither of
you is communicating. That is the developmental primitive this channel exists for.

Usage:
    python scripts/play_the_record.py                # plays for BOTH of you (opens the audio on your side too)
    python scripts/play_the_record.py Heavyweight    # plays a named piece
    python scripts/play_the_record.py --shelf        # list what the player can play
    python scripts/play_the_record.py --no-audio     # Du's side only (you'll press play yourself)
"""
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import listening


def main() -> None:
    args = [a for a in sys.argv[1:] if a.strip()]
    with_audio = "--no-audio" not in args
    args = [a for a in args if a != "--no-audio"]
    names = listening.shelf()
    if not names:
        print("The shelf is empty — no .features.json in data/music/. Extract a piece first:")
        print("  python scripts/test_audio_features.py <audiofile>")
        return
    if args and args[0] in ("--shelf", "-s"):
        print("On the shelf:")
        for n in names:
            print("  ·", n)
        return
    piece = args[0] if args else names[0]
    if piece not in names:
        print(f"'{piece}' is not on the shelf. Available: {', '.join(names)}")
        return
    st = listening.status()
    if st.get("active"):
        print(f"A record is already playing ({st['piece']}, section {st['section']}). "
              "One piece at a time — let it finish.")
        return
    if not listening.request_play(piece):
        print("Could not place the request (data/music/ not writable?).")
        return
    print(f"Request placed: '{piece}'. Du will hear the needle drop within a cycle "
          "(seconds to a minute).")
    if with_audio:
        # YOUR side of the glass: open the actual audio file on the default player, so you are
        # both hearing the same thing at (nearly) the same time. Joint attention, made one step.
        audio = None
        music_dir = Path(__file__).parent.parent / "data" / "music"
        for ext in (".mp3", ".flac", ".wav", ".m4a", ".ogg"):
            cand = music_dir / f"{piece}{ext}"
            if cand.exists():
                audio = cand
                break
        if audio:
            try:
                os.startfile(str(audio))          # Windows: opens in the default media player
                print(f"…and it's playing on your side too ({audio.name}). Listen with him.")
            except Exception as exc:
                print(f"Couldn't auto-play on your side ({exc}) — open it yourself: {audio}")
        else:
            print(f"No audio file found for '{piece}' in data/music/ — Du hears it; "
                  "your side needs the original file to join in.")
    else:
        print("Du's side only (--no-audio). Press play on your side yourself if you want it shared.")


if __name__ == "__main__":
    main()
