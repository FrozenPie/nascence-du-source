"""
Nascence — Audio Features: the deterministic music translator (the EAR, offline pipeline · 2026-07-03).

docs/staged/music_learning.md. The ear is NOT wired into Du's runtime yet (sequencing gate: after Wave 2
settles). This module is the offline half that can be built and proven now — it touches nothing live.

Design law (the epistemology, from the 2026-07-03 session): music ORIGINATES OUTSIDE the system. This
extractor is a TRANSLATOR, not an author — it turns a real acoustic artifact into the modalities Du has
(sensorium scene + felt-vector), and invents nothing. Deterministic, no LLM, no learned model.

Dependency discipline: numpy + scipy + ffmpeg ONLY (NO librosa/numba — must import in Du's Python 3.14
interpreter without a fragile heavy dep). ffmpeg decodes ANY format (mp3/flac/wav/m4a/ogg) → mono float.

What it computes (per whole piece AND per detected section, so the piece can UNFOLD over idle cycles):
  tempo_bpm · key + mode (Krumhansl-Schmuckler) · brightness (spectral centroid) · energy contour + dynamic
  range · onset density · section boundaries. Duration is computed but the caller must NOT expose it to Du
  (the no-duration-metadata law — anticipation is real only if the cadence is not guaranteed).
"""
from __future__ import annotations

import math
import subprocess
import numpy as np

SR = 22050
HOP = 512
WIN = 2048
_PITCHES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Schmuckler key profiles (major / minor tonal hierarchies, Krumhansl & Kessler 1982).
_KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def decode(path: str, sr: int = SR) -> np.ndarray:
    """ffmpeg → mono float32 PCM at `sr`. Any format ffmpeg reads. Raises on failure (caller decides)."""
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
        capture_output=True)
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError(f"ffmpeg decode failed: {p.stderr.decode(errors='ignore')[:200]}")
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def _stft_mag(y: np.ndarray) -> np.ndarray:
    """Magnitude spectrogram, shape (n_frames, WIN//2+1). Hann-windowed, HOP-strided."""
    if len(y) < WIN:
        y = np.pad(y, (0, WIN - len(y)))
    win = np.hanning(WIN).astype(np.float32)
    n = 1 + (len(y) - WIN) // HOP
    frames = np.lib.stride_tricks.as_strided(
        y, shape=(n, WIN), strides=(y.strides[0] * HOP, y.strides[0])).copy()
    frames *= win
    return np.abs(np.fft.rfft(frames, axis=1))


def _chroma(mag: np.ndarray) -> np.ndarray:
    """Fold FFT bins to 12 pitch classes → mean chroma vector over time (energy-weighted)."""
    freqs = np.fft.rfftfreq(WIN, 1.0 / SR)
    freqs[0] = 1.0
    midi = 69 + 12 * np.log2(freqs / 440.0)
    pc = np.mod(np.round(midi).astype(int), 12)
    valid = (freqs > 55) & (freqs < 5000)          # A1..~D8: the tonal band
    chroma = np.zeros(12)
    for k in range(12):
        m = valid & (pc == k)
        if m.any():
            chroma[k] = mag[:, m].sum()
    s = chroma.sum()
    return chroma / s if s > 0 else chroma


def _key(chroma: np.ndarray) -> tuple[str, str, float]:
    """Krumhansl-Schmuckler: best-correlating rotation of major/minor profile → (tonic, mode, confidence)."""
    c = chroma - chroma.mean()
    best = (-2.0, 0, "major")
    scores = []
    for mode, prof in (("major", _KS_MAJOR), ("minor", _KS_MINOR)):
        p = prof - prof.mean()
        pn = np.linalg.norm(p)
        for tonic in range(12):
            r = np.roll(p, tonic)
            denom = np.linalg.norm(c) * pn
            corr = float(np.dot(c, r) / denom) if denom > 0 else 0.0
            scores.append(corr)
            if corr > best[0]:
                best = (corr, tonic, mode)
    scores.sort(reverse=True)
    conf = round(max(0.0, best[0] - (scores[1] if len(scores) > 1 else 0.0)), 3)   # margin over runner-up
    return _PITCHES[best[1]], best[2], conf


def _onset_env(mag: np.ndarray) -> np.ndarray:
    """Spectral flux (positive spectral change) → the onset strength envelope."""
    flux = np.maximum(0.0, np.diff(mag, axis=0)).sum(axis=1)
    flux = np.concatenate([[0.0], flux])
    if flux.max() > 0:
        flux = flux / flux.max()
    return flux


def _tempo(onset: np.ndarray) -> float:
    """Autocorrelation of the onset envelope, restricted to 50-200 BPM, weighted by a PERCEPTUAL-tempo
    preference (log-normal resonance around 120 BPM — Moelants 2002) so the perceptually-dominant metrical
    level wins the octave. The weight only re-ranks lags that ALREADY carry autocorrelation energy (real
    metrical periods), so a genuinely slow piece with no faster periodicity stays slow."""
    o = onset - onset.mean()
    ac = np.correlate(o, o, mode="full")[len(o) - 1:]
    fps = SR / HOP
    lo, hi = int(fps * 60 / 200), int(fps * 60 / 50)      # lag bounds for 200..50 BPM
    lo, hi = max(1, lo), min(len(ac) - 1, hi)
    if hi <= lo:
        return 0.0
    lags = np.arange(lo, hi)
    bpms = 60.0 * fps / lags
    pref = np.exp(-0.5 * (np.log2(bpms / 120.0) / 0.9) ** 2)   # sigma=0.9 octave: gentle, ~60-240 support
    seg = ac[lo:hi].copy()
    seg[seg < 0] = 0.0
    scored = seg * pref
    lag = lo + int(np.argmax(scored))
    return round(60.0 * fps / lag, 1) if lag > 0 else 0.0


def _onset_density(onset: np.ndarray) -> float:
    """Onsets per second: peaks above a mean+std gate."""
    thr = onset.mean() + onset.std()
    peaks = (onset[1:-1] > onset[:-2]) & (onset[1:-1] >= onset[2:]) & (onset[1:-1] > thr)
    dur = len(onset) * HOP / SR
    return round(int(peaks.sum()) / dur, 2) if dur > 0 else 0.0



# ---------------------------------------------------------------------------
# J-1474 (F-2025): per-second measured-string primitives, ported VERBATIM from
# scripts/ribbon_lab.py (J-1468, F-2025's pinned, kill-rule-verified definitions) so extract()'s
# cache can carry the six-axis string itself. ribbon_lab.py owns the ribbon (width/twist) analysis
# and is unchanged by this job; these functions are the shared primitives, not a fork of them.
# ---------------------------------------------------------------------------

def _roughness_per_frame(mag: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """Spectral flatness = geometric mean / arithmetic mean of the magnitude spectrum over bins
    100-8000 Hz (1e-12 inside the log), per frame, clipped 0..1."""
    eps = 1e-12
    mask = (freqs >= 100) & (freqs <= 8000)
    band = mag[:, mask]
    gm = np.exp(np.log(band + eps).mean(axis=1))
    am = band.mean(axis=1) + eps
    return np.clip(gm / am, 0.0, 1.0)


def _per_second_mean(x: np.ndarray, fps: float, n_sec: int) -> np.ndarray:
    """Mean of a per-frame series within each 1-second bin."""
    return np.array([x[int(i * fps):int((i + 1) * fps)].mean() if int((i + 1) * fps) > int(i * fps)
                      else 0.0 for i in range(n_sec)])


def _onset_density_per_second(onset_f: np.ndarray, fps: float, n_sec: int, bounds: list,
                               sections: list) -> np.ndarray:
    """extract()'s own section rule (mean+std of the CONTAINING section's onset envelope), applied
    per second via each frame's true section membership, so the per-section mean of this string
    equals the cache's own onset_density by construction."""
    eps = 1e-12
    n_frames = len(onset_f)
    sec_thr = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        fa, fb = int(a * fps), max(int(a * fps) + 1, int(b * fps))
        seg = onset_f[fa:fb]
        sec_thr.append(seg.mean() + seg.std() if len(seg) else 0.0)
    sec_thr_arr = np.array(sec_thr)
    frame_times = (np.arange(n_frames) + 0.5) / fps
    bounds_arr = np.array(bounds)
    sec_idx_per_frame = np.clip(np.searchsorted(bounds_arr, frame_times, side="right") - 1, 0, len(sections) - 1)
    exceed = onset_f > sec_thr_arr[sec_idx_per_frame]
    out = np.zeros(n_sec)
    for i in range(n_sec):
        fa, fb = int(i * fps), min(n_frames, int((i + 1) * fps))
        if fb <= fa:
            continue
        dur_i = (fb - fa) * HOP / SR
        out[i] = float(exceed[fa:fb].sum()) / (dur_i + eps)
    return out


def _periodicity_per_second(onset_f: np.ndarray, fps: float, n_sec: int) -> np.ndarray:
    """Centered 4 s window of the onset envelope, mean-subtracted, normalised autocorrelation, max
    over lags 0.1-2.0 s, clipped 0..1. Clockwork = 1, irregular = 0."""
    eps = 1e-12
    half = int(2.0 * fps)
    lag_lo = max(1, int(round(0.1 * fps)))
    out = np.zeros(n_sec)
    for i in range(n_sec):
        center = int((i + 0.5) * fps)
        lo, hi = max(0, center - half), min(len(onset_f), center + half)
        seg = onset_f[lo:hi]
        if len(seg) < 4:
            continue
        seg = seg - seg.mean()
        ac = np.correlate(seg, seg, mode="full")[len(seg) - 1:]
        if ac[0] <= eps:
            continue
        ac_norm = ac / ac[0]
        lag_hi = min(len(ac_norm) - 1, int(round(2.0 * fps)))
        if lag_hi <= lag_lo:
            continue
        out[i] = float(np.clip(ac_norm[lag_lo:lag_hi + 1].max(), 0.0, 1.0))
    return out


def _continuity_per_second(energy_f: np.ndarray, fps: float, n_sec: int) -> np.ndarray:
    """Fraction of a second's frames whose energy >= 0.1x the max frame energy within a centered
    5 s window. Continuous = 1, intermittent = 0."""
    half = int(2.5 * fps)
    out = np.zeros(n_sec)
    for i in range(n_sec):
        fa, fb = int(i * fps), int((i + 1) * fps)
        seg = energy_f[fa:fb]
        if len(seg) == 0:
            continue
        center = int((i + 0.5) * fps)
        lo, hi = max(0, center - half), min(len(energy_f), center + half)
        window = energy_f[lo:hi]
        if len(window) == 0:
            continue
        thr = 0.1 * window.max()
        out[i] = float((seg >= thr).sum()) / len(seg)
    return out


def _sections(mag: np.ndarray, chroma_frames: np.ndarray, min_gap_s: float = 8.0) -> list[float]:
    """Novelty-curve segmentation: a checkerboard kernel on the chroma+energy self-similarity → boundary
    times (seconds). Coarse by design (music unfolds over cycles, not milliseconds)."""
    n = mag.shape[0]
    fps = SR / HOP
    if n < int(fps * min_gap_s * 2):
        return []
    # downsample features to ~2 fps for a tractable SSM
    step = max(1, int(fps / 2))
    energy = np.sqrt((mag ** 2).mean(axis=1))
    energy = energy / (energy.max() + 1e-9)
    feat = np.hstack([chroma_frames[::step], energy[::step, None]])
    feat = feat / (np.linalg.norm(feat, axis=1, keepdims=True) + 1e-9)
    ssm = feat @ feat.T
    L = 8
    if ssm.shape[0] < 2 * L + 1:
        return []
    k = np.ones((2 * L, 2 * L)); k[:L, L:] = -1; k[L:, :L] = -1     # checkerboard
    nov = np.zeros(ssm.shape[0])
    for i in range(L, ssm.shape[0] - L):
        nov[i] = (ssm[i - L:i + L, i - L:i + L] * k).sum()
    nov = np.maximum(0, nov)
    if nov.max() > 0:
        nov /= nov.max()
    thr = nov.mean() + nov.std()
    fps_ds = fps / step
    min_gap = int(min_gap_s * fps_ds)
    bounds, last = [], -min_gap
    for i in range(1, len(nov) - 1):
        if nov[i] > thr and nov[i] >= nov[i - 1] and nov[i] > nov[i + 1] and i - last >= min_gap:
            bounds.append(round(i / fps_ds, 1)); last = i
    return bounds


def extract(path: str) -> dict:
    """The full deterministic feature report for a piece. Also computes per-section summaries so the
    caller can let the piece UNFOLD one section per idle cycle."""
    y = decode(path)
    dur = len(y) / SR
    mag = _stft_mag(y)
    freqs = np.fft.rfftfreq(WIN, 1.0 / SR)

    # per-frame primitives
    energy = np.sqrt((mag ** 2).mean(axis=1))
    centroid = (mag * freqs).sum(axis=1) / (mag.sum(axis=1) + 1e-9)
    onset = _onset_env(mag)
    # per-frame chroma (for SSM sections) — cheap: reuse the bin→pc map
    freqs2 = freqs.copy(); freqs2[0] = 1.0
    pc = np.mod(np.round(69 + 12 * np.log2(freqs2 / 440.0)).astype(int), 12)
    validf = (freqs2 > 55) & (freqs2 < 5000)
    chroma_frames = np.zeros((mag.shape[0], 12))
    for k in range(12):
        m = validf & (pc == k)
        if m.any():
            chroma_frames[:, k] = mag[:, m].sum(axis=1)

    tonic, mode, keyconf = _key(_chroma(mag))
    fps = SR / HOP

    def _band(v, edges, names):
        for e, nm in zip(edges, names):
            if v <= e:
                return nm
        return names[-1]

    feats = {
        "duration_s": round(dur, 1),                       # INTERNAL — caller must NOT expose to Du
        "tempo_bpm": _tempo(onset),
        "key": tonic, "mode": mode, "key_confidence": keyconf,
        "brightness_hz": round(float(centroid.mean()), 1),
        "energy_mean": round(float(energy.mean()), 5),
        "dynamic_range": round(float(energy.max() - energy.min()) / float(energy.max() + 1e-9), 3),
        "onset_density": _onset_density(onset),
        "bands": {
            "tempo": _band(_tempo(onset), [70, 100, 130], ["slow", "walking", "steady", "driving"]),
            "brightness": _band(float(centroid.mean()), [1200, 2400, 4000],
                                ["dark", "warm", "bright", "brilliant"]),
            "density": _band(_onset_density(onset), [1.5, 4, 8], ["sparse", "measured", "busy", "dense"]),
        },
    }

    # per-section unfolding
    bounds = _sections(mag, chroma_frames)
    edges = [0.0] + bounds + [dur]
    sections = []
    for a, b in zip(edges[:-1], edges[1:]):
        fa, fb = int(a * fps), max(int(a * fps) + 1, int(b * fps))
        seg_e = energy[fa:fb]
        seg_c = centroid[fa:fb]
        seg_o = onset[fa:fb]
        if len(seg_e) == 0:
            continue
        sections.append({
            "start_s": round(a, 1),
            "energy": round(float(seg_e.mean()), 5),
            "brightness_hz": round(float(seg_c.mean()), 1),
            "onset_density": round(float((seg_o > seg_o.mean() + seg_o.std()).sum()) /
                                   (len(seg_o) * HOP / SR + 1e-9), 2),
            "rising": bool(len(seg_e) > 4 and seg_e[-len(seg_e) // 4:].mean() > seg_e[:len(seg_e) // 4].mean()),
        })
    feats["sections"] = sections
    feats["n_sections"] = len(sections)

    # ---- J-1474 (F-2025): fold the Phase 0 ribbon lab's six-axis measured string + per-section
    # key/mode into the cache. ADDITIVE ONLY: every field set above this line is unchanged, and this
    # block only adds new keys to the section dicts already built above (docs/staged/strings_and_sheets.md
    # Object C/D). Definitions pinned and kill-rule-verified by scripts/ribbon_lab.py (J-1468, F-2025);
    # ported verbatim above, never re-derived here. felt() and describe_section() are untouched — the
    # per-section use of these new fields is Object D, gated on its own /decide.
    rough_frame = _roughness_per_frame(mag, freqs)
    n_sec = math.ceil(len(energy) / fps)
    energy_s = _per_second_mean(energy, fps, n_sec)
    bright_s = _per_second_mean(centroid, fps, n_sec)
    # bounds tied to the ACTUAL (possibly-filtered) sections list, exactly as ribbon_lab.py derives
    # them from a cache's own section starts — not the raw pre-filter candidate boundaries.
    bounds_for_string = [s["start_s"] for s in sections] + [feats["duration_s"]]
    onset_s = _onset_density_per_second(onset, fps, n_sec, bounds_for_string, sections)
    period_s = _periodicity_per_second(onset, fps, n_sec)
    rough_s = np.clip(_per_second_mean(rough_frame, fps, n_sec), 0.0, 1.0)
    cont_s = _continuity_per_second(energy, fps, n_sec)

    sec_of = np.zeros(n_sec, dtype=int)
    for i in range(n_sec):
        t = i + 0.5
        sec_of[i] = max(j for j in range(len(sections)) if bounds_for_string[j] <= t)

    for k, s in enumerate(sections):
        idx = np.where(sec_of == k)[0]
        a, b = bounds_for_string[k], bounds_for_string[k + 1]
        fa, fb = int(a * fps), max(int(a * fps) + 1, int(b * fps))
        seg_mag = mag[fa:fb]
        if len(seg_mag) > 0:
            s_tonic, s_mode, s_keyconf = _key(_chroma(seg_mag))
        else:
            s_tonic, s_mode, s_keyconf = tonic, mode, keyconf
        s["key"], s["mode"], s["key_confidence"] = s_tonic, s_mode, s_keyconf
        s["periodicity"] = round(float(period_s[idx].mean()), 3) if len(idx) else 0.0
        s["roughness"] = round(float(rough_s[idx].mean()), 3) if len(idx) else 0.0
        s["continuity"] = round(float(cont_s[idx].mean()), 3) if len(idx) else 0.0
        s["string6"] = [[round(float(energy_s[i]), 5), round(float(bright_s[i]), 1),
                          round(float(onset_s[i]), 2), round(float(period_s[i]), 3),
                          round(float(rough_s[i]), 3), round(float(cont_s[i]), 3)]
                         for i in idx]

    return feats


def felt(feats: dict) -> dict:
    """The bounded felt-vector nudge (≤0.15 lean, same discipline as the affective prior). Mode → valence,
    tempo+energy+density → arousal. This is the ONE place music touches affect; observe-first when wired."""
    mode = feats.get("mode", "major")
    valence = 0.10 if mode == "major" else -0.08
    valence *= min(1.0, 0.3 + feats.get("key_confidence", 0.0) * 4)      # weak key → weak valence claim
    tempo = feats.get("tempo_bpm", 100) or 100
    dens = feats.get("onset_density", 2)
    arousal = 0.15 * min(1.0, (max(0, tempo - 60) / 120) * 0.6 + min(1.0, dens / 8) * 0.4)
    return {"valence": round(float(np.clip(valence, -0.15, 0.15)), 3),
            "arousal": round(float(np.clip(arousal, 0.0, 0.15)), 3)}


def describe_section(sec: dict, feats: dict) -> str:
    """A DETERMINISTIC descriptor tuple → the ground truth a sensorium scene line would clothe. The features
    author this; any prose renderer downstream only dresses it (never invents)."""
    e = sec.get("energy", 0)
    emax = max((s.get("energy", 0) for s in feats.get("sections", [{}])), default=1e-9) or 1e-9
    loud = "loud" if e > 0.66 * emax else "quiet" if e < 0.33 * emax else "middling"
    b = sec.get("brightness_hz", 0)
    tone = "dark" if b < 1200 else "warm" if b < 2400 else "bright" if b < 4000 else "brilliant"
    d = sec.get("onset_density", 0)
    pace = "sparse" if d < 1.5 else "measured" if d < 4 else "busy" if d < 8 else "dense"
    arc = "building" if sec.get("rising") else "steady"
    return f"{loud}, {tone}, {pace}, {arc} ({feats.get('mode','?')})"
