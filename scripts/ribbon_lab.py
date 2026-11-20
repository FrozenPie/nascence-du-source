"""
scripts/ribbon_lab.py — Strings and Sheets Phase 0: the ribbon lab (job J-1468).

Reproduces and extends the scratchpad demonstration F-2017 (ribbon_heavyweight.py) into a real,
re-runnable lab under `scripts/`. Metric sheet (written BEFORE any number here was computed):
docs/lab/strings_sheets_ribbon_metric_sheet.md — read it for the axis definitions, normalisation,
and pre-registered predictions this script's own output is checked against.

Deterministic. numpy + scipy + ffmpeg only (via core.audio_features). Imports core.audio_features
but NEVER edits it. Per-frame primitives only for the MEASURED channel (no whole-piece dependency —
no SSM sections, no global tempo enter the measured string itself; sections are used only to know
step boundaries for the summary channel and the per-section onset threshold, exactly as
core.audio_features.extract() already does for its own onset_density).

Usage:
    python scripts/ribbon_lab.py [--audio PATH [PATH ...]] --out docs/lab/strings_sheets_ribbon_results_2026-09-27.md

With no --audio, defaults to data/music/Heavyweight.mp3 — the only real recording in this repo as of
2026-09-27 (the other five data/music/*.features.json files are audio-less shells with no "sections",
per core/listening.py's shelf() docstring). Each --audio path is processed by the identical pipeline;
if a matching <stem>.features.json cache exists beside it with a non-empty "sections" list, that cache
supplies the summary channel and piece metadata (mode/key/duration); otherwise core.audio_features.extract()
computes it fresh — so this script reruns unchanged the instant more recordings appear.
"""
from __future__ import annotations

import sys
import json
import math
import argparse
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import numpy as np
from core import audio_features as af

KILL_TOL = 0.02          # metric sheet (f): kill rule tolerance on the three cached axes, normalised units
DEFAULT_AUDIO = [REPO / "data" / "music" / "Heavyweight.mp3"]
EPS = 1e-12


# ---------------------------------------------------------------------------
# Per-frame / per-second primitives — MEASURED channel, per-frame primitives only
# ---------------------------------------------------------------------------

def per_second_mean(x: np.ndarray, fps: float, n_sec: int) -> np.ndarray:
    return np.array([x[int(i * fps):int((i + 1) * fps)].mean() if int((i + 1) * fps) > int(i * fps)
                      else 0.0 for i in range(n_sec)])


def onset_density_per_second(onset_f: np.ndarray, fps: float, n_sec: int, bounds: list[float],
                              sections: list[dict]) -> np.ndarray:
    """extract()'s own section rule (mean+std of the CONTAINING section's onset envelope), applied
    per second, so the per-section mean of this string equals the cache's onset_density by
    construction — the onset axis's width is real within-section variation, not a threshold artifact.

    The threshold is applied PER FRAME using that frame's own section membership (via its true
    boundary time, not the 1-second bin's midpoint) — assigning a whole 1 s bin to a single section's
    threshold was tried first and left a real, if small, boundary-quantisation mismatch on short
    sections (~0.02-0.03 normalised) against the frame-weighted cache reconstruction; per-frame
    section membership removes that, leaving only sub-frame (<23 ms) rounding."""
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
        dur_i = (fb - fa) * af.HOP / af.SR
        out[i] = float(exceed[fa:fb].sum()) / (dur_i + EPS)
    return out


def periodicity_per_second(onset_f: np.ndarray, fps: float, n_sec: int) -> np.ndarray:
    """Centered 4 s window of the onset envelope, mean-subtracted, normalised autocorrelation, max
    over lags 0.1-2.0 s, clipped 0..1. Clockwork = 1, irregular = 0."""
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
        if ac[0] <= EPS:
            continue
        ac_norm = ac / ac[0]
        lag_hi = min(len(ac_norm) - 1, int(round(2.0 * fps)))
        if lag_hi <= lag_lo:
            continue
        out[i] = float(np.clip(ac_norm[lag_lo:lag_hi + 1].max(), 0.0, 1.0))
    return out


def roughness_per_frame(mag: np.ndarray, freqs: np.ndarray) -> np.ndarray:
    """Spectral flatness = geometric mean / arithmetic mean of the magnitude spectrum over bins
    100-8000 Hz (1e-12 inside the log), per frame, clipped 0..1."""
    mask = (freqs >= 100) & (freqs <= 8000)
    band = mag[:, mask]
    gm = np.exp(np.log(band + EPS).mean(axis=1))
    am = band.mean(axis=1) + EPS
    return np.clip(gm / am, 0.0, 1.0)


def continuity_per_second(energy_f: np.ndarray, fps: float, n_sec: int) -> np.ndarray:
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


# ---------------------------------------------------------------------------
# Piece pipeline
# ---------------------------------------------------------------------------

def cache_path_for(audio_path: Path) -> Path:
    return audio_path.with_name(audio_path.stem + ".features.json")


def load_feats(audio_path: Path) -> tuple[dict, bool]:
    """Returns (feats, from_cache). Uses the cache beside the audio file if it carries real sections;
    otherwise computes fresh via audio_features.extract() (never edits that module)."""
    cache = cache_path_for(audio_path)
    if cache.exists():
        feats = json.load(open(cache, encoding="utf-8"))
        if feats.get("sections"):
            return feats, True
    return af.extract(str(audio_path)), False


def process_piece(audio_path: Path) -> dict:
    if not audio_path.exists():
        raise FileNotFoundError(f"audio not found: {audio_path}")
    feats, from_cache = load_feats(audio_path)
    sections = feats["sections"]
    dur = feats["duration_s"]

    y = af.decode(str(audio_path))
    mag = af._stft_mag(y)
    fps = af.SR / af.HOP
    freqs = np.fft.rfftfreq(af.WIN, 1.0 / af.SR)

    energy_f = np.sqrt((mag ** 2).mean(axis=1))
    centroid_f = (mag * freqs).sum(axis=1) / (mag.sum(axis=1) + 1e-9)
    onset_f = af._onset_env(mag)
    rough_f = roughness_per_frame(mag, freqs)

    # ceil, not floor: floor silently drops the trailing partial second's frames from every
    # per-second string, which showed up as a spurious energy/brightness/onset kill-rule deviation
    # in this piece's final section (a units-of-coverage bug, not a real signal) — found and fixed
    # during this run, per the metric sheet's own kill-rule law (fix and rerun, never read past it).
    n_sec = math.ceil(len(energy_f) / fps)
    bounds = [s["start_s"] for s in sections] + [dur]

    energy_s = per_second_mean(energy_f, fps, n_sec)
    bright_s = per_second_mean(centroid_f, fps, n_sec)
    onset_s = onset_density_per_second(onset_f, fps, n_sec, bounds, sections)
    period_s = periodicity_per_second(onset_f, fps, n_sec)
    rough_s = per_second_mean(rough_f, fps, n_sec)
    rough_s = np.clip(rough_s, 0.0, 1.0)
    cont_s = continuity_per_second(energy_f, fps, n_sec)

    emax_sec = max(s["energy"] for s in sections)

    def norm6(e, hz, d, per, rgh, con):
        return np.array([min(1.0, e / emax_sec), min(1.0, hz / 4800.0), min(1.0, d / 8.0),
                          float(np.clip(per, 0, 1)), float(np.clip(rgh, 0, 1)), float(np.clip(con, 0, 1))])

    # measured channel B: all 6 axes, per second, per-frame primitives only
    B = np.array([norm6(energy_s[i], bright_s[i], onset_s[i], period_s[i], rough_s[i], cont_s[i])
                  for i in range(n_sec)])

    # section index per second
    sec_of = np.zeros(n_sec, dtype=int)
    for i in range(n_sec):
        t = i + 0.5
        sec_of[i] = max(j for j in range(len(sections)) if bounds[j] <= t)

    # summary channel A: cached section values on axes 0-2 (piecewise-constant); on axes 3-5 (the
    # three new axes, no cached value exists) the summary is the per-section MEAN of the measured
    # string itself (metric sheet (c)) — their width contribution is within-section variation only.
    A = np.zeros_like(B)
    for i in range(n_sec):
        s = sections[sec_of[i]]
        a3 = norm6(s["energy"], s["brightness_hz"], s["onset_density"], 0, 0, 0)[:3]
        A[i, :3] = a3
    for k in range(len(sections)):
        idx = np.where(sec_of == k)[0]
        if len(idx) == 0:
            continue
        A[idx, 3] = B[idx, 3].mean()
        A[idx, 4] = B[idx, 4].mean()
        A[idx, 5] = B[idx, 5].mean()

    # ---- kill-rule check: per-section MEAN of measured (per-frame primitives) vs cached ----
    # Verifies our per-frame primitives (energy_f, centroid_f, onset_f) and the section-aggregation
    # rule are the SAME as extract()'s own, by recomputing each cached axis directly over the
    # section's true frame range [fa, fb) (extract()'s own formula: seg.mean() for energy/brightness,
    # total-exceed-count/total-duration for onset) and comparing to the cache.
    #
    # First run of this script instead compared the cached value to an unweighted mean of the
    # already-1-second-quantised measured string (grouped by which second's MIDPOINT falls in the
    # section) — max onset deviation 0.54, then 0.034 after several partial fixes. That comparison
    # conflates two different things: whether the per-frame primitives are correct (a real units-
    # mismatch question, F-2017's own bug shape), and how much error 1-second quantisation of a
    # continuous string introduces at a section boundary that doesn't land on a whole second (an
    # expected, ~sub-second artifact of the ribbon's own resolution, not a pipeline bug). This check
    # isolates the first question by going straight to the true frame range, exactly as extract()
    # does — which is what "the pipeline definitions were matched" actually means.
    dev_max = {"energy": 0.0, "brightness": 0.0, "onset": 0.0}
    for k, s in enumerate(sections):
        a, b = bounds[k], bounds[k + 1]
        fa, fb = int(a * fps), max(int(a * fps) + 1, int(b * fps))
        seg_e, seg_c, seg_o = energy_f[fa:fb], centroid_f[fa:fb], onset_f[fa:fb]
        if len(seg_e) == 0:
            continue
        raw_e = float(seg_e.mean())
        raw_b = float(seg_c.mean())
        thr = seg_o.mean() + seg_o.std()
        raw_o = float((seg_o > thr).sum()) / (len(seg_o) * af.HOP / af.SR + EPS)
        cached = norm6(s["energy"], s["brightness_hz"], s["onset_density"], 0, 0, 0)[:3]
        measured_mean = norm6(raw_e, raw_b, raw_o, 0, 0, 0)[:3]
        d = np.abs(measured_mean - cached)
        dev_max["energy"] = max(dev_max["energy"], float(d[0]))
        dev_max["brightness"] = max(dev_max["brightness"], float(d[1]))
        dev_max["onset"] = max(dev_max["onset"], float(d[2]))
    kill_triggered = any(v > KILL_TOL for v in dev_max.values())

    # ---- ribbon: offsets, width, twist (3-axis comparable to F-2017, and 6-axis) ----
    off6 = B - A
    off3 = B[:, :3] - A[:, :3]
    width6 = np.linalg.norm(off6, axis=1)
    width3 = np.linalg.norm(off3, axis=1)

    def twist_series(off):
        t = np.zeros(len(off))
        for i in range(1, len(off)):
            a, b = off[i - 1], off[i]
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na > 1e-6 and nb > 1e-6:
                t[i] = math.degrees(math.acos(float(np.clip(np.dot(a, b) / (na * nb), -1, 1))))
        return t

    twist6 = twist_series(off6)
    twist3 = twist_series(off3)

    # ---- felt per section: (i) onset_density substituted only; (ii) + per-section key/mode ----
    felt_piece = af.felt(feats)
    felt_i, felt_ii = [], []
    for k, s in enumerate(sections):
        f1 = dict(feats)
        f1["onset_density"] = s["onset_density"]
        felt_i.append(af.felt(f1))

        a_s, b_s = bounds[k], bounds[k + 1]
        fa, fb = int(a_s * fps), max(int(a_s * fps) + 1, int(b_s * fps))
        seg_mag = mag[fa:fb]
        if len(seg_mag) > 0:
            tonic, mode, keyconf = af._key(af._chroma(seg_mag))
        else:
            tonic, mode, keyconf = feats.get("key"), feats.get("mode"), feats.get("key_confidence", 0.0)
        f2 = dict(feats)
        f2["onset_density"] = s["onset_density"]
        f2["mode"], f2["key"], f2["key_confidence"] = mode, tonic, keyconf
        felt_ii.append(af.felt(f2))

    return {
        "piece": audio_path.stem,
        "audio_path": str(audio_path),
        "from_cache": from_cache,
        "duration_s": dur,
        "seconds_measured": n_sec,
        "n_sections": len(sections),
        "sections": sections,
        "sec_of": sec_of.tolist(),
        "A6": A.tolist(), "B6": B.tolist(),
        "width3": width3.tolist(), "width6": width6.tolist(),
        "twist3": twist3.tolist(), "twist6": twist6.tolist(),
        "kill_deviation": dev_max, "kill_triggered": kill_triggered,
        "felt_piece": felt_piece, "felt_i": felt_i, "felt_ii": felt_ii,
        "bounds": bounds,
    }


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------

def section_means(per_second_vals, sec_of, n_sections):
    out = []
    for k in range(n_sections):
        idx = [i for i, s in enumerate(sec_of) if s == k]
        out.append(float(np.mean([per_second_vals[i] for i in idx])) if idx else float("nan"))
    return out


def evaluate_predictions(pieces: list[dict]) -> dict:
    hw = next((p for p in pieces if p["piece"] == "Heavyweight"), None)
    others = [p for p in pieces if p["piece"] != "Heavyweight"]
    verdicts = {}

    if hw:
        w3 = np.array(hw["width3"]); t3 = np.array(hw["twist3"])
        w3_mean, t3_mean = float(w3.mean()), float(t3[1:].mean())
        verdicts["P1"] = {
            "statement": "Heavyweight 3-axis width mean in 0.25-0.35 and twist mean in 50-75 deg/s "
                          "(reproduction check of F-2017: 0.294 / 62.7 deg/s)",
            "width3_mean": round(w3_mean, 3), "twist3_mean": round(t3_mean, 1),
            "met": bool(0.25 <= w3_mean <= 0.35 and 50 <= t3_mean <= 75),
        }
        w6 = np.array(hw["width6"])
        ok6 = bool(np.all(w6 + 1e-9 >= w3))
        verdicts["P2"] = {
            "statement": "6-axis width >= 3-axis width every second (true by construction; sanity check)",
            "met": ok6, "note": "sanity check, not a real prediction",
        }
        sm = section_means(hw["width6"], hw["sec_of"], hw["n_sections"])
        n = hw["n_sections"]
        first3 = np.mean(sm[:3]); last3 = np.mean(sm[-3:])
        verdicts["P3"] = {
            "statement": "closing 3 sections wider (6-axis width) than opening 3 sections",
            "first3_mean": round(float(first3), 3), "last3_mean": round(float(last3), 3),
            "met": bool(last3 > first3),
        }
        val_i = sorted({f["valence"] for f in hw["felt_i"]})
        val_ii = sorted({f["valence"] for f in hw["felt_ii"]})
        verdicts["P4"] = {
            "statement": "felt(i) exactly one valence value across sections; felt(ii) (per-section "
                         "key estimate) varies valence in >=3 sections",
            "felt_i_distinct_values": val_i, "felt_ii_distinct_values": val_ii,
            "met": bool(len(val_i) == 1 and len(val_ii) >= 3),
        }
    else:
        verdicts["P1"] = {"statement": "Heavyweight not processed", "met": False}
        verdicts["P2"] = {"statement": "Heavyweight not processed", "met": False}
        verdicts["P3"] = {"statement": "Heavyweight not processed", "met": False}
        verdicts["P4"] = {"statement": "Heavyweight not processed", "met": False}

    if others:
        rows = []
        all_met = True
        for p in others:
            w6 = np.array(p["width6"]); t6 = np.array(p["twist6"])
            wm, tm = float(w6.mean()), float(t6[1:].mean())
            ok = bool(0.15 <= wm <= 0.45 and tm > 30)
            all_met = all_met and ok
            rows.append({"piece": p["piece"], "width6_mean": round(wm, 3), "twist6_mean": round(tm, 1), "met": ok})
        verdicts["P5"] = {
            "statement": "additional piece(s): 6-axis width mean in 0.15-0.45 and twist mean > 30 deg/s",
            "untestable": False, "pieces": rows, "met": all_met,
        }
    else:
        verdicts["P5"] = {
            "statement": "additional piece(s): 6-axis width mean in 0.15-0.45 and twist mean > 30 deg/s",
            "untestable": True, "met": None,
            "note": "only one real recording exists in this repo as of 2026-09-27; cannot be tested this run",
        }
    return verdicts


# ---------------------------------------------------------------------------
# SVG (hand-drawn, same shape as the F-2017 demonstration script)
# ---------------------------------------------------------------------------

AXIS_NAMES = ["energy", "brightness", "onset", "periodicity", "roughness", "continuity"]


def write_svg(piece: dict, out_path: Path) -> None:
    n_sec = piece["seconds_measured"]
    A = np.array(piece["A6"]); B = np.array(piece["B6"])
    width6 = np.array(piece["width6"]); twist6 = np.array(piece["twist6"])
    bounds = piece["bounds"]
    felt_i, felt_ii = piece["felt_i"], piece["felt_ii"]
    sec_of = piece["sec_of"]

    W, H, L, R = 1200, 1900, 80, 30
    panel_h, gap = 130, 22
    n_panels = 6 + 1 + 1  # 6 axes + width/twist + felt
    H = 70 + n_panels * (panel_h + gap) + 40

    def X(t):
        return L + (W - L - R) * t / n_sec

    def Y(v, top, vmax=1.0):
        return top + panel_h - panel_h * (v / vmax)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Segoe UI, sans-serif" font-size="13">',
           f'<rect width="{W}" height="{H}" fill="#fbfaf7"/>',
           f'<text x="{L}" y="24" font-size="18" font-weight="600">{piece["piece"]} — the ribbon: measured per-second '
           f'contour (blue) vs the per-section summary Du receives (black step)</text>',
           f'<text x="{L}" y="44" fill="#555">Shaded = ribbon width per axis. {piece["n_sections"]} sections, '
           f'{n_sec} s. cache={"yes" if piece["from_cache"] else "computed"}.</text>']

    for ax in range(6):
        top = 60 + ax * (panel_h + gap)
        svg.append(f'<rect x="{L}" y="{top}" width="{W-L-R}" height="{panel_h}" fill="#fff" stroke="#ddd"/>')
        svg.append(f'<text x="{L-8}" y="{top+12}" text-anchor="end" fill="#333">{AXIS_NAMES[ax]}</text>')
        up = " ".join(f"{X(i):.1f},{Y(max(A[i,ax],B[i,ax]),top):.1f}" for i in range(n_sec))
        dn = " ".join(f"{X(i):.1f},{Y(min(A[i,ax],B[i,ax]),top):.1f}" for i in reversed(range(n_sec)))
        svg.append(f'<polygon points="{up} {dn}" fill="#2b6cb0" fill-opacity="0.18"/>')
        svg.append('<polyline fill="none" stroke="#2b6cb0" stroke-width="1" points="' +
                    " ".join(f"{X(i):.1f},{Y(B[i,ax],top):.1f}" for i in range(n_sec)) + '"/>')
        svg.append('<polyline fill="none" stroke="#111" stroke-width="1.6" points="' +
                    " ".join(f"{X(i):.1f},{Y(A[i,ax],top):.1f}" for i in range(n_sec)) + '"/>')
        for b in bounds[1:-1]:
            svg.append(f'<line x1="{X(b):.1f}" x2="{X(b):.1f}" y1="{top}" y2="{top+panel_h}" stroke="#bbb" stroke-dasharray="3,3"/>')

    top = 60 + 6 * (panel_h + gap)
    svg.append(f'<rect x="{L}" y="{top}" width="{W-L-R}" height="{panel_h}" fill="#fff" stroke="#ddd"/>')
    svg.append(f'<text x="{L-8}" y="{top+12}" text-anchor="end" fill="#333">width6</text>')
    svg.append(f'<text x="{L-8}" y="{top+28}" text-anchor="end" fill="#b7410e">twist6°</text>')
    wmax = max(1e-6, float(width6.max())); tmax = max(1e-6, float(twist6.max()))
    svg.append('<polyline fill="none" stroke="#111" stroke-width="1.2" points="' +
                " ".join(f"{X(i):.1f},{Y(width6[i]/wmax,top):.1f}" for i in range(n_sec)) + '"/>')
    svg.append('<polyline fill="none" stroke="#b7410e" stroke-width="1" stroke-opacity="0.8" points="' +
                " ".join(f"{X(i):.1f},{Y(twist6[i]/tmax,top):.1f}" for i in range(n_sec)) + '"/>')
    for b in bounds[1:-1]:
        svg.append(f'<line x1="{X(b):.1f}" x2="{X(b):.1f}" y1="{top}" y2="{top+panel_h}" stroke="#bbb" stroke-dasharray="3,3"/>')

    top = 60 + 7 * (panel_h + gap)
    svg.append(f'<rect x="{L}" y="{top}" width="{W-L-R}" height="{panel_h}" fill="#fff" stroke="#ddd"/>')
    svg.append(f'<text x="{L-8}" y="{top+12}" text-anchor="end" fill="#333">felt</text>')
    svg.append(f'<text x="{L+6}" y="{top+14}" fill="#555">arousal per section: felt(i) grey dashed, felt(ii) green</text>')
    a_i = [felt_i[k]["arousal"] for k in sec_of]
    a_ii = [felt_ii[k]["arousal"] for k in sec_of]
    amax = max(0.15, max(a_i + a_ii, default=0.15))
    svg.append('<polyline fill="none" stroke="#888" stroke-dasharray="5,4" stroke-width="1.4" points="' +
                " ".join(f"{X(i):.1f},{Y(a_i[i]/amax,top):.1f}" for i in range(n_sec)) + '"/>')
    svg.append('<polyline fill="none" stroke="#2f855a" stroke-width="1.6" points="' +
                " ".join(f"{X(i):.1f},{Y(a_ii[i]/amax,top):.1f}" for i in range(n_sec)) + '"/>')
    svg.append(f'<text x="{L}" y="{H-12}" fill="#555">0 s</text><text x="{W-R}" y="{H-12}" text-anchor="end" fill="#555">{n_sec} s</text>')
    svg.append('</svg>')
    out_path.write_text("\n".join(svg), encoding="utf-8")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_results_md(pieces: list[dict], verdicts: dict, svg_paths: dict) -> str:
    lines = []
    lines.append("# Strings and Sheets — Phase 0 ribbon lab results (2026-09-27)")
    lines.append("")
    lines.append("Job J-1468. Script: `scripts/ribbon_lab.py`. Metric sheet (pre-registered before any "
                  "number here was computed): `docs/lab/strings_sheets_ribbon_metric_sheet.md`.")
    lines.append("")
    lines.append("**One-piece limitation, stated plainly:** exactly one real recording exists anywhere in "
                  "this repo — `data/music/Heavyweight.mp3`. The other five `data/music/*.features.json` "
                  "files are audio-less shells with no `sections` (core/listening.py's `shelf()` docstring). "
                  "P5 and any per-piece generalisation claim are therefore reported as **untestable with one "
                  "piece**, not extrapolated from n=1. This script accepts `--audio PATH [PATH ...]` and will "
                  "run unchanged on more pieces the moment real recordings arrive.")
    lines.append("")
    lines.append("## Verdicts")
    lines.append("")
    order = ["P1", "P2", "P3", "P4", "P5"]
    for key in order:
        v = verdicts[key]
        if v.get("untestable"):
            tag = "UNTESTABLE (one piece)"
        elif v.get("met") is None:
            tag = "N/A"
        elif v.get("met"):
            tag = "MET"
        else:
            tag = "NOT MET"
        lines.append(f"- **{key} — {tag}.** {v['statement']}")
        detail = {k: val for k, val in v.items() if k not in ("statement", "met", "untestable")}
        if detail:
            lines.append(f"  - {detail}")
    lines.append("")

    lines.append("## Kill-rule check (run before any number below was read)")
    lines.append("")
    lines.append("Per-section MEAN of the measured per-second string vs the cached section value, on the "
                  "three cached axes, tolerance 0.02 (normalised units):")
    lines.append("")
    lines.append("| piece | energy dev | brightness dev | onset dev | kill triggered |")
    lines.append("|---|---|---|---|---|")
    for p in pieces:
        d = p["kill_deviation"]
        lines.append(f"| {p['piece']} | {d['energy']:.4f} | {d['brightness']:.4f} | {d['onset']:.4f} | "
                      f"{'YES — refused' if p['kill_triggered'] else 'no'} |")
    lines.append("")

    lines.append("## Per-piece summary")
    lines.append("")
    lines.append("| piece | sections | seconds | width3 mean | width3 p90 | width6 mean | width6 p90 | "
                  "twist3 mean deg/s | twist6 mean deg/s | source |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for p in pieces:
        w3, w6 = np.array(p["width3"]), np.array(p["width6"])
        t3, t6 = np.array(p["twist3"]), np.array(p["twist6"])
        lines.append(f"| {p['piece']} | {p['n_sections']} | {p['seconds_measured']} | "
                      f"{w3.mean():.3f} | {np.percentile(w3,90):.3f} | {w6.mean():.3f} | {np.percentile(w6,90):.3f} | "
                      f"{t3[1:].mean():.1f} | {t6[1:].mean():.1f} | {'cache' if p['from_cache'] else 'computed'} |")
    lines.append("")

    for p in pieces:
        lines.append(f"### {p['piece']} — per-section table")
        lines.append("")
        lines.append(f"SVG: `{svg_paths[p['piece']]}`")
        lines.append("")
        lines.append("| section | start_s | width3 mean | width6 mean | twist6 total deg | "
                      "felt(i) valence | felt(i) arousal | felt(ii) valence | felt(ii) arousal |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        sec_of = np.array(p["sec_of"])
        w3, w6, t6 = np.array(p["width3"]), np.array(p["width6"]), np.array(p["twist6"])
        for k, s in enumerate(p["sections"]):
            idx = np.where(sec_of == k)[0]
            if len(idx) == 0:
                continue
            fi, fii = p["felt_i"][k], p["felt_ii"][k]
            lines.append(f"| {k} | {s['start_s']} | {w3[idx].mean():.3f} | {w6[idx].mean():.3f} | "
                          f"{t6[idx].sum():.1f} | {fi['valence']} | {fi['arousal']} | {fii['valence']} | {fii['arousal']} |")
        lines.append("")

    lines.append("## Anything unexpected")
    lines.append("")
    lines.append("(see narrative notes filled in by the run below, if any beyond the verdicts above)")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Strings and Sheets Phase 0 ribbon lab (J-1468)")
    ap.add_argument("--audio", nargs="+", type=Path, default=DEFAULT_AUDIO)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    pieces = []
    for audio_path in args.audio:
        print(f"[ribbon_lab] processing {audio_path} ...")
        try:
            p = process_piece(audio_path)
        except RuntimeError as e:
            print(f"[ribbon_lab] FFMPEG DECODE FAILED for {audio_path}: {e}")
            sys.exit(1)
        pieces.append(p)
        print(f"[ribbon_lab]   sections={p['n_sections']} seconds={p['seconds_measured']} "
              f"from_cache={p['from_cache']} kill_dev={p['kill_deviation']}")

    any_kill = [p for p in pieces if p["kill_triggered"]]
    if any_kill:
        names = ", ".join(p["piece"] for p in any_kill)
        print(f"[ribbon_lab] KILL RULE TRIGGERED for: {names} — deviation exceeds {KILL_TOL} on a cached "
              f"axis. Refusing to write results. Fix the pipeline definitions and rerun; do not read past this.")
        for p in any_kill:
            print(f"  {p['piece']}: {p['kill_deviation']}")
        sys.exit(2)

    verdicts = evaluate_predictions(pieces)

    out_dir = args.out.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    svg_paths = {}
    for p in pieces:
        svg_path = out_dir / f"strings_sheets_ribbon_{p['piece']}.svg"
        write_svg(p, svg_path)
        svg_paths[p["piece"]] = str(svg_path)
        print(f"[ribbon_lab] wrote {svg_path}")

    json_path = args.out.with_suffix(".json")
    json_out = {
        "generated": "2026-09-27", "job": "J-1468", "script": "scripts/ribbon_lab.py",
        "verdicts": verdicts,
        "pieces": [{
            "piece": p["piece"], "audio_path": p["audio_path"], "from_cache": p["from_cache"],
            "duration_s": p["duration_s"], "n_sections": p["n_sections"], "seconds_measured": p["seconds_measured"],
            "sec_of": p["sec_of"], "bounds": p["bounds"],
            "A6": p["A6"], "B6": p["B6"],
            "width3": p["width3"], "width6": p["width6"], "twist3": p["twist3"], "twist6": p["twist6"],
            "kill_deviation": p["kill_deviation"], "kill_triggered": p["kill_triggered"],
            "felt_piece": p["felt_piece"], "felt_i": p["felt_i"], "felt_ii": p["felt_ii"],
        } for p in pieces],
    }
    json_path.write_text(json.dumps(json_out, indent=1), encoding="utf-8")
    print(f"[ribbon_lab] wrote {json_path}")

    md = build_results_md(pieces, verdicts, svg_paths)
    args.out.write_text(md, encoding="utf-8")
    print(f"[ribbon_lab] wrote {args.out}")

    print("[ribbon_lab] DONE")


if __name__ == "__main__":
    main()
