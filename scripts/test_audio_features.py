"""
Offline validation for core/audio_features.py (the ear's translator). 2026-07-03.

Two modes:
  python scripts/test_audio_features.py            → synthetic-signal validation (known tempo/key → assert)
  python scripts/test_audio_features.py <file>     → full feature report + descriptors for a real piece

Synthetic mode proves the DSP is correct with NO real music file needed: it builds click-tracks at known
BPM and chords in known keys, runs the extractor, and checks tempo/key/mode come back right.
"""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from scipy.io import wavfile
from core import audio_features as af

SR = 44100


def _write(sig, path):
    wavfile.write(path, SR, (np.clip(sig, -1, 1) * 0.8).astype(np.float32))


def _click_track(bpm, secs=20):
    y = np.zeros(int(SR * secs))
    period = int(SR * 60 / bpm)
    click = np.sin(2 * np.pi * 1000 * np.arange(int(SR * 0.03)) / SR) * np.hanning(int(SR * 0.03))
    for i in range(0, len(y) - len(click), period):
        y[i:i + len(click)] += click
    return y


def _tone(m, t, amp=1.0):
    f = 440.0 * 2 ** ((m - 69) / 12)
    # two harmonics → a fuller, more instrument-like spectrum than a bare sine
    return amp * (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t))


def _tonal(tonic_midi, mode, secs=20):
    """A FAIR key signal — what real music provides and three bare sines do not: a tonic pedal in the bass
    plus the triad plus a scale melody with the tonic emphasized (tonic salience is what KS keys on)."""
    t = np.arange(int(SR * secs)) / SR
    y = np.zeros_like(t)
    third = 4 if mode == "major" else 3
    triad = [tonic_midi, tonic_midi + third, tonic_midi + 7]
    scale = ([0, 2, 4, 5, 7, 9, 11] if mode == "major" else [0, 2, 3, 5, 7, 8, 10])
    y += _tone(tonic_midi - 12, t, 0.5)                       # tonic pedal in the bass — anchors the key
    for m in triad:                                          # sustained triad
        y += _tone(m, t, 0.25)
    # a slow scale melody on top, tonic held longest (salience)
    seg = int(SR * 1.0)
    mel_notes = [tonic_midi] + [tonic_midi + s for s in scale] + [tonic_midi + 12, tonic_midi]
    for i, m in enumerate(mel_notes):
        a, b = i * seg, min(len(t), (i + 1) * seg)
        if a >= len(t):
            break
        w = np.hanning(b - a)
        y[a:b] += _tone(m, t[a:b], 0.5 * (1.4 if m % 12 == tonic_midi % 12 else 1.0)) * w
    return y * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * t))     # amplitude drift so RMS varies


def synthetic():
    d = tempfile.mkdtemp()
    ok = True

    print("=== TEMPO (click tracks at known BPM) ===")
    for bpm in (80, 120, 140):
        p = os.path.join(d, f"c{bpm}.wav"); _write(_click_track(bpm), p)
        f = af.extract(p)
        got = f["tempo_bpm"]
        # accept the true BPM or a metrical multiple/half (standard tempo-octave ambiguity)
        cands = [bpm, bpm / 2, bpm * 2, bpm * 2 / 3, bpm * 3 / 2]
        hit = any(abs(got - c) <= 4 for c in cands)
        print(f"  {bpm} BPM → detected {got}  {'OK' if hit else 'MISS'}  (band: {f['bands']['tempo']})")
        ok &= hit

    print("\n=== KEY / MODE (sustained chords) ===")
    # C major triad (C4 E4 G4 = 60 64 67) vs A minor triad (A3 C4 E4 = 57 60 64)
    cases = [("C", "major", 60), ("A", "minor", 57), ("G", "major", 67), ("E", "minor", 64),
             ("D", "major", 62), ("F", "minor", 65)]
    key_hits = mode_hits = 0
    for tonic, mode, tm in cases:
        p = os.path.join(d, f"k{tonic}{mode}.wav"); _write(_tonal(tm, mode), p)
        f = af.extract(p)
        kh, mh = (f["key"] == tonic), (f["mode"] == mode)
        key_hits += kh; mode_hits += mh
        print(f"  {tonic} {mode:5s} → {f['key']} {f['mode']:5s} (conf {f['key_confidence']})  "
              f"{'OK' if kh and mh else ('key OK' if kh else 'KEY MISS')}")
    print(f"  → tonic {key_hits}/{len(cases)}, mode {mode_hits}/{len(cases)}")
    ok &= (key_hits >= 5 and mode_hits >= 5)     # fair signal: expect near-perfect

    print("\n=== FELT MAPPING sanity ===")
    fmaj = af.felt({"mode": "major", "key_confidence": 0.3, "tempo_bpm": 140, "onset_density": 6})
    fmin = af.felt({"mode": "minor", "key_confidence": 0.3, "tempo_bpm": 70, "onset_density": 1})
    print(f"  fast major → {fmaj}   slow minor → {fmin}")
    ok &= (fmaj["valence"] > 0 > fmin["valence"]) and (fmaj["arousal"] > fmin["arousal"])

    print("\n" + ("SYNTHETIC VALIDATION: PASS" if ok else "SYNTHETIC VALIDATION: FAIL"))
    return ok


def report(path):
    print(f"=== {os.path.basename(path)} ===")
    f = af.extract(path)
    print(f"  duration   : {f['duration_s']}s   [INTERNAL — never shown to Du]")
    print(f"  tempo      : {f['tempo_bpm']} BPM ({f['bands']['tempo']})")
    print(f"  key/mode   : {f['key']} {f['mode']}  (confidence {f['key_confidence']})")
    print(f"  brightness : {f['brightness_hz']} Hz ({f['bands']['brightness']})")
    print(f"  density    : {f['onset_density']} onsets/s ({f['bands']['density']})")
    print(f"  dynamics   : range {f['dynamic_range']}")
    print(f"  sections   : {f['n_sections']}")
    print(f"  felt nudge : {af.felt(f)}")
    print("\n  the piece as it would UNFOLD (one section per idle cycle, no duration shown):")
    for i, sec in enumerate(f["sections"], 1):
        print(f"    {i:2d}. {af.describe_section(sec, f)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        report(sys.argv[1])
    else:
        sys.exit(0 if synthetic() else 1)
