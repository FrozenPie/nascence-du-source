"""J-2397: re-measure the D-0477 re-picks. python -I scripts/strings_phase4_repick_lab.py <worktree> <scratch_root> <out_json>
Reads downloads from <scratch_root>/J-2397_dl_<key>/, old J-2027 copies from <scratch_root>/rec_J-2027/.
Writes window WAVs to <scratch_root>/J-2397_win/ and one JSON. Never touches C:\\Nascence\\data.
Signal-review code is copied unchanged from analyze_J-2027.py + tonal_J-2027.py (see sheet)."""
import sys, json, hashlib, math, wave, importlib.util
from pathlib import Path
import site; site.addsitedir(site.getusersitepackages())
WT = Path(sys.argv[1]); SR_ROOT = Path(sys.argv[2]); OUT = Path(sys.argv[3])
sys.path.insert(0, str(WT)); sys.path.insert(0, str(WT / "scripts"))
import core
assert Path(core.__file__).resolve().is_relative_to(WT.resolve()), core.__file__
import numpy as np
from core import audio_features as af
import ribbon_lab as rl
assert Path(rl.__file__).resolve().is_relative_to(WT.resolve())

fps = af.SR / af.HOP
freqs = np.fft.rfftfreq(af.WIN, 1.0 / af.SR)


def review(p: Path) -> dict:
    y = af.decode(str(p)); dur = len(y) / af.SR
    mag = af._stft_mag(y); pw = mag ** 2
    rms_f = np.sqrt(pw.mean(axis=1))
    cen = (mag * freqs).sum(axis=1) / (mag.sum(axis=1) + 1e-9)
    db = 20 * np.log10(rms_f + 1e-9); peak_db = db.max()
    act = db >= peak_db - 40; w = rms_f[act]
    cen_w = float((cen[act] * w).sum() / (w.sum() + 1e-12))
    spec = pw[act].mean(axis=0); tot = spec.sum() + 1e-12
    bands = {"<300": float(spec[freqs < 300].sum() / tot), "300-2k": float(spec[(freqs >= 300) & (freqs < 2000)].sum() / tot),
             "2k-6k": float(spec[(freqs >= 2000) & (freqs < 6000)].sum() / tot), ">6k": float(spec[freqs >= 6000].sum() / tot)}
    idx = np.argsort(spec * (freqs >= 40))[::-1]; dom = []
    for i in idx:
        f = float(freqs[i])
        if all(abs(f - d) > 60 for d in dom):
            dom.append(round(f, 0))
        if len(dom) == 5:
            break
    flat = af._roughness_per_frame(mag, freqs); flat_w = float((flat[act] * w).sum() / (w.sum() + 1e-12))
    on = af._onset_env(mag); thr = on.mean() + 2 * on.std()
    ev = [i for i in range(1, len(on) - 1) if on[i] > thr and on[i] >= on[i - 1] and on[i] > on[i + 1]]
    evm = []
    for i in ev:
        if not evm or (i - evm[-1]) / fps > 0.05:
            evm.append(i)
    # tonal (tonal_J-2027.py, unchanged; its own -30 dB activity gate)
    act30 = db >= db.max() - 30
    m = (freqs >= 1500) & (freqs <= 9000); band = mag[:, m]
    ratio = 20 * np.log10(band.max(axis=1) / (np.median(band, axis=1) + 1e-9))
    tonal = (ratio > 25) & act30; pkf = freqs[m][band.argmax(axis=1)]
    lm = (freqs >= 50) & (freqs <= 500); lb = mag[:, lm]
    lr = 20 * np.log10(lb.max(axis=1) / (np.median(lb, axis=1) + 1e-9))
    n10 = 10
    env10 = [round(float(db[int(i * len(db) / n10):max(int(i * len(db) / n10) + 1, int((i + 1) * len(db) / n10))].max() - peak_db), 1) for i in range(n10)]
    return {"duration_s": round(dur, 2), "silence_share_-40dB": round(float((db < peak_db - 40).mean()), 3),
            "quiet_share_-20dB": round(float((db < peak_db - 20).mean()), 3), "centroid_hz_w": round(cen_w, 0),
            "flatness_w": round(flat_w, 3), "dominant_hz": dom, "band_share": {k: round(v, 3) for k, v in bands.items()},
            "env10_db": env10, "onset_events": len(evm), "onset_rate_hz": round(len(evm) / max(dur, 1e-6), 2),
            "strongest_onset_s": round(float(np.argmax(on) / fps), 2),
            "tonal_share_1.5-9k": round(float(tonal[act30].mean()) if act30.any() else 0.0, 3),
            "tonal_peak_hz_median": round(float(np.median(pkf[tonal])), 0) if tonal.any() else None,
            "lowband_tonal_share": round(float(((lr > 25) & act30)[act30].mean()) if act30.any() else 0.0, 3)}


def band_power_per_sec(y, lo, hi):
    mag = af._stft_mag(y); sel = (freqs >= lo) & (freqs < hi)
    bp = (mag[:, sel] ** 2).mean(axis=1)
    n = math.ceil(len(bp) / fps)
    return np.array([bp[int(i * fps):int((i + 1) * fps)].mean() for i in range(n)]), bp


def best_window(y, lo, hi, length_s):
    ps, _ = band_power_per_sec(y, lo, hi)
    n = len(ps)
    if n <= length_s:
        return 0
    means = [ps[s:s + length_s].mean() for s in range(0, n - length_s + 1)]
    return int(np.argmax(means))


def thud_time(y):
    _, bp = band_power_per_sec(y, 50, 500)
    d = 10 * np.log10(bp + 1e-12); k = int(fps)
    rise = np.full(len(d), -np.inf)
    for i in range(k, len(d)):
        rise[i] = d[i] - np.median(d[i - k:i])
    i = int(np.argmax(rise))
    return i / fps, float(rise[i])


def write_wav(y, path):
    pcm = np.clip(y, -1, 1)
    pcm = (pcm * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(af.SR); wf.writeframes(pcm.tobytes())


def features(p: Path) -> dict:
    pc = rl.process_piece(p); feats = af.extract(str(p))
    w6 = np.array(pc["width6"]); t6 = np.array(pc["twist6"])
    return {"file": p.name, "duration_s": feats["duration_s"], "tempo_bpm": feats["tempo_bpm"], "key": feats["key"],
            "mode": feats["mode"], "key_confidence": feats["key_confidence"], "brightness_hz": feats["brightness_hz"],
            "energy_mean": feats["energy_mean"], "dynamic_range": feats["dynamic_range"], "onset_density": feats["onset_density"],
            "bands": feats["bands"], "n_sections": feats["n_sections"], "sections": feats["sections"],
            "measured_string6_norm": [[round(v, 4) for v in row] for row in pc["B6"]],
            "ribbon_width6_mean": round(float(w6.mean()), 4), "ribbon_width6_p90": round(float(np.percentile(w6, 90)), 4),
            "ribbon_twist6_mean_deg_s": round(float(t6[1:].mean()), 2) if len(t6) > 1 else None,
            "kill_deviation": pc["kill_deviation"], "kill_triggered": pc["kill_triggered"]}


old = json.loads((WT / "docs/lab/strings_sheets_phase4_features_2026-10-18.json").read_text(encoding="utf-8"))["keys"]
res = {"job": "J-2397", "sanity": {}, "keys": {}}
# 1. sanity: reproduce J-2027 review_signal on old files
ok = True
for k in ("dawn_chorus", "morepork_call", "wind_in_trees"):
    r = review(SR_ROOT / "rec_J-2027" / old[k]["file"]); s = old[k]["review_signal"]
    dev = max([abs(r["tonal_share_1.5-9k"] - s["tonal_share_1.5-9k"])] + [abs(r["band_share"][b] - s["band_share"][b]) for b in s["band_share"]])
    res["sanity"][k] = {"max_dev": round(dev, 4), "tonal": [r["tonal_share_1.5-9k"], s["tonal_share_1.5-9k"]], "lowband": [r["band_share"]["<300"], s["band_share"]["<300"]]}
    ok &= dev <= 0.002
res["sanity_ok"] = bool(ok)
print("sanity", res["sanity"], ok, flush=True)
if not ok:
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8"); sys.exit("sanity failed; nothing read")

WIN = SR_ROOT / "J-2397_win"; WIN.mkdir(exist_ok=True)
plan = {"dawn_chorus": "dawn_chorus__DOC46-tui-morning-chorus.mp3", "log_on_fire": "log_on_fire__455132.mp3",
        "morepork_call": "morepork_call__DOCmorepork-song.mp3", "wind_in_trees": "wind_in_trees__523389.mp3"}
for k, fn in plan.items():
    src = SR_ROOT / f"J-2397_dl_{k}" / fn
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    y = af.decode(str(src)); full_dur = len(y) / af.SR
    extra = {}
    if k == "dawn_chorus":
        s0 = best_window(y, 1500, 9000, 60); s1 = s0 + 60
    elif k == "morepork_call":
        s0 = best_window(y, 300, 2000, 15); s1 = s0 + 15
    elif k == "log_on_fire":
        t, rise = thud_time(y); s0 = max(0, int(math.floor(t)) - 1); s1 = s0 + 5
        extra = {"thud_t_s": round(t, 2), "thud_rise_db": round(rise, 1)}
    else:
        s0, s1 = 0, None
    seg = y[int(s0 * af.SR):(int(s1 * af.SR) if s1 else len(y))]
    wp = WIN / f"{k}__window_{s0}-{s1 if s1 else 'end'}.wav"; write_wav(seg, wp)
    entry = {"source_file": fn, "sha256": sha, "bytes": src.stat().st_size, "full_duration_s": round(full_dur, 2),
             "window_s": [s0, s1 if s1 else round(full_dur, 2)], **extra,
             "review_window": review(wp), "review_full": review(src) if s1 else None}
    if k == "dawn_chorus":   # robustness: every non-overlapping 60 s window
        entry["tonal_by_60s_block"] = []
        for b in range(0, int(full_dur // 60)):
            bp = WIN / f"{k}__block_{b*60}.wav"; write_wav(y[b * 60 * af.SR:(b + 1) * 60 * af.SR], bp)
            entry["tonal_by_60s_block"].append([b * 60, review(bp)["tonal_share_1.5-9k"]])
    f = features(wp); f["file"] = wp.name; f["review_signal"] = entry["review_window"]
    entry["features"] = f
    res["keys"][k] = entry
    rw = entry["review_window"]
    print(k, sha[:12], entry["window_s"], extra, "tonal", rw["tonal_share_1.5-9k"], "bands", rw["band_share"],
          "cen", rw["centroid_hz_w"], "env10", rw["env10_db"], "strongest_onset", rw["strongest_onset_s"], flush=True)

# 3. envelope test, J-2372 code unchanged
spec = importlib.util.spec_from_file_location("envlab", WT / "scripts" / "strings_phase4_envelope_lab.py")
env = importlib.util.module_from_spec(spec); spec.loader.exec_module(env)
cons = env.load_constructed()


def strings_from(fe):
    rows = [r for s in fe["sections"] for r in s["string6"]]
    return [env.norm_row(r) for r in rows]


strings_old = {k: strings_from(v) for k, v in old.items() if isinstance(v, dict) and "sections" in v}
strings_new = dict(strings_old)
for k in res["keys"]:
    strings_new[k] = strings_from(res["keys"][k]["features"])
strings_new.pop("moth_tap", None)
short = {k for k, v in strings_new.items() if len(v) < 3}


def headline(strs, exclude):
    prim = sorted(k for k in strs if k not in short and k not in exclude)
    ev = env.evaluate(strs, cons, prim)
    n = sum(v["pass"] for v in ev.values()); base = float(np.mean([v["baseline_share"] for v in ev.values()]))
    return {"pass": n, "n": len(prim), "share": round(n / len(prim), 4), "baseline": round(base, 4),
            "non_discriminating": base >= 0.8 * n / len(prim),
            "own_rank_median": float(np.median([v["own_rank"] for v in ev.values()])),
            "per_key": {k: {"pass": ev[k]["pass"], "n_in": ev[k]["n_in"], "misses": ev[k]["misses"], "own_rank": ev[k]["own_rank"],
                            "baseline_share": round(ev[k]["baseline_share"], 3), "measured_vertices": ev[k]["measured_vertices"]}
                        for k in res["keys"] if k in ev}}


# reproduce J-2372 first (old strings, its own exclusions) -> must give 19/63
repro = headline(strings_old, {"dawn_chorus", "log_on_fire"})
res["repro_J2372"] = {k: repro[k] for k in ("pass", "n", "share", "baseline")}
print("repro J-2372", res["repro_J2372"], flush=True)
res["read_a"] = headline(strings_new, {"dawn_chorus", "log_on_fire"})
res["read_b_all_in"] = headline(strings_new, set())
# own-envelope single-key checks for the two formerly excluded keys
for k in ("dawn_chorus", "log_on_fire"):
    rows = strings_new[k]; mv = env.vertices(rows)
    res["keys"][k]["envelope_own"] = env.key_verdict(mv, env.envelope(cons[k]["string"]))
    res["keys"][k]["envelope_own_old"] = env.key_verdict(env.vertices(strings_old[k]), env.envelope(cons[k]["string"]))
for k in ("morepork_call", "wind_in_trees"):
    res["keys"][k]["envelope_own_old"] = env.key_verdict(env.vertices(strings_old[k]), env.envelope(cons[k]["string"]))
    res["keys"][k]["envelope_own"] = env.key_verdict(env.vertices(strings_new[k]), env.envelope(cons[k]["string"]))
for r in ("read_a", "read_b_all_in"):
    print(r, {k: res[r][k] for k in ("pass", "n", "share", "baseline", "non_discriminating", "own_rank_median")})
for k in res["keys"]:
    print(k, "own env old", res["keys"][k]["envelope_own_old"], "new", res["keys"][k]["envelope_own"])
OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
print("wrote", OUT)
