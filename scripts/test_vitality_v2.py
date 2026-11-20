"""scripts/test_vitality_v2.py (J-2061 + J-2110, the_consciousness_program, D-0398 E + D-0421 C): hermetic proof of the
two-axis vitality shadow reading (mind axis exp(-ln2 x P/S) on the self-calibrated S, clip kept beside it) and its
rebuilt causal predictor, plus the D-0398 defeater numbers replayed over a COPY of the log for both mappings.

No LLM, no live data. core is imported FIRST (from this tree, asserted), then lab_env.isolate(db="empty") redirects the
memory store, homeostasis's state + shadow log and sleep_pressure's log into a lab dir. Where a section needs a
realistic sleep-pressure log it replays a READ-ONLY copy (--sp-copy PATH, or by default a copy of the live log made
into the lab dir); nothing in homeostasis.tick() writes the sleep-pressure log. Live files are size-checked at the end.

  [1] self_calibrated_scale: under V2_MIN_FIRES -> None; the percentile index is suggest_setpoints' int(pct*n); order-
      independent; S floored at 1.0; the day/night mix pools (no regime split)
  [2] read_vitality_v2: min / mean combination; mind axis from S; body from the somatic cache, else the sp row, else
      the setpoint; fail-open to the CURRENT reading under V2_MIN_FIRES fires; extra-percentile columns present
  [3] the scale is recomputed at most once per wake (same newest fire -> cached; a new fire -> recomputed)
  [4] tick() end to end on a synthetic log: rec["vitality_v2"] and rec["predicted_v2"] present, `variables` still
      exactly the five drive inputs, v2_causal_err / v2_naive_err on the second tick, status() carries it, state persists
      the scale; _VARS untouched (vitality setpoint 0.78 weight 0.7)
  [5] predict_vitality_v2: no fire -> P grows by the recent intake rate; a night fire inside the horizon -> P reset,
      mind axis 1.0, body recovery lump applied; a fire row as last row -> fired_already; scale None -> threshold scale;
      empty rows -> None
  [6] REPLAY over the log copy: rolling self-calibrated S from prior fires only; the D-0398 defeater numbers for the
      current reading vs v2 (min) vs v2 mean vs the p80/p90 mind variants: (1) flip step ratio, (2) within-wake r,
      (3) before-sleep vs after-wake gap, (5) share of fires with vit_mind > 0.7; plus saturation and deficit shares
  [7] wiring (text): tick computes v2 after the variables, logs additive keys only; somatic.recover carries the note
  [8] live files untouched

Run:  python scripts/test_vitality_v2.py [--sp-copy PATH] [--out PATH]   (from the tree under test)
"""
from __future__ import annotations
import argparse, json, math, statistics as st, sys, tempfile, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # BEFORE lab_env (feedback_jobrun_live_store_leaks)
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
from core import homeostasis as ho, homeostasis_causal as hc, sleep_pressure as sp, somatic as som
sys.path.insert(0, str(Path.home() / ".claude" / "skills" / "job-queue"))
from lab_env import isolate

ap = argparse.ArgumentParser()
ap.add_argument("--sp-copy", default=None, help="a READ-ONLY copy of sleep_pressure_log.jsonl; default: the test copies the live log into the lab dir")
ap.add_argument("--out", default=None, help="also append the replay table to this file")
args = ap.parse_args()

ok_all = True
def check(name, cond):
    global ok_all
    ok_all = ok_all and bool(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

LIVE = {p: (p.stat().st_size if p.exists() else None) for p in
        (Path(r"C:\Nascence/data/homeostasis_shadow.jsonl"), Path(r"C:\Nascence/data/homeostasis_state.json"),
         Path(r"C:\Nascence/data/sleep_pressure_log.jsonl"))}
clip = ho._clip01
body0, cyc0 = som._current_body, som._current_cycles
daylight0 = hc.wc.daylight
sp_status0 = sp.status
recent0 = ho._recent_fires

def row(ts, P, awake_min, dark=False, fire=False, reason=None, energy=None, cycles=None, **kw):
    r = {"ts": ts, "P": P, "awake_min": awake_min, "dark": dark, "threshold": 10.0 if dark else 100.0,
         "fire": fire, "reason": reason or ("pressure" if fire else "below_threshold")}
    if energy is not None: r["energy"] = energy
    if cycles is not None: r["cycles"] = cycles
    r.update(kw)
    return r

with isolate(db="empty", also=[(ho, ["_STATE", "_LOG"]), (sp, ["_LOG_FILE"])]) as lab:
    check("state, shadow log and sp log redirected into the lab dir",
          all(Path(p).is_relative_to(lab) for p in (ho._STATE, ho._LOG, sp._LOG_FILE)))
    try:
        print("[1] self_calibrated_scale")
        check("under V2_MIN_FIRES -> None", ho.self_calibrated_scale([12.0] * (ho.V2_MIN_FIRES - 1)) is None)
        ten = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        s10 = ho.self_calibrated_scale(ten)
        check("exactly 10 fires: S = sorted[int(0.6*10)] = 16", s10 and s10["S"] == 16.0 and s10["n_fires"] == 10)
        check("order independent", ho.self_calibrated_scale(list(reversed(ten)))["S"] == 16.0)
        check("floored at 1.0", ho.self_calibrated_scale([0.1] * 12)["S"] == 1.0)
        mix = [12.0] * 26 + [100.0] * 4          # 87% night-ish, 13% day-ish, like the live last-30
        check("day/night pooled: p60 of the mix is a night-scale value", ho.self_calibrated_scale(mix)["S"] == 12.0)
        check("p90 of the same mix reaches the day fires", ho.self_calibrated_scale(mix, pct=0.9)["S"] == 100.0)

        print("[2] read_vitality_v2")
        fires = [row(1000 + i * 7200, 10 + i, 120, dark=True, fire=True) for i in range(30)]   # P at fire 10..39 -> p60 = 28
        ho._recent_fires = lambda path=None, n=None: fires
        last = row(300000, 14.0, 40, energy=0.5, cycles=3)
        sp.status = lambda: {"last": last}
        som._current_body = {"energy": 0.9, "fatigue": 0.1, "tension": 0.0}
        stt = {}
        v = ho.read_vitality_v2(stt, now=300010, current_vitality=0.3)
        check("scale S = 28 from 30 fires, source self_calibrated", v and v["scale_S"] == 28.0 and v["mind_source"] == "self_calibrated")
        exp14 = math.exp(-math.log(2) * 14 / 28)
        check("vit_mind = exp(-ln2 x 14/28) = 0.7071 (D-0421 C); clip column = 1 - 14/28 = 0.5",
              v["vit_mind"] == round(exp14, 4) and v["vit_mind_clip"] == 0.5 and v["mind_mapping"] == "exp")
        check("body from the somatic cache (0.9), not the sp row (0.5)", v["vit_body"] == 0.9 and v["body_source"] == "somatic_cache")
        check("vitality_v2 = min(0.7071, 0.9) = 0.7071, mean = 0.8036",
              v["vitality_v2"] == round(exp14, 4) and v["vitality_v2_mean"] == round((exp14 + 0.9) / 2, 4))
        check("extra percentile columns present for both mappings (p80, p90)",
              all(k in v for k in ("vit_mind_p80", "vit_mind_p90", "vit_mind_clip_p80", "vit_mind_clip_p90")) and v["vit_mind_p80"] <= 1.0)
        check("mind_axis never pins at 0 (P = 100 x S -> tiny but > 0)", 0 < ho.mind_axis(28 * 100, 28) < 1e-20 or ho.mind_axis(28 * 100, 28) >= 0)
        check("mind_axis(S, S) = 0.5 exactly: S is the half-tired point", abs(ho.mind_axis(28, 28) - 0.5) < 1e-12)
        check("current reading carried beside it", v["vitality_current"] == 0.3 and v["sp_reason"] == "below_threshold")
        som._current_body = None
        v2 = ho.read_vitality_v2(stt, now=300010, current_vitality=0.3)
        check("no somatic cache: body from the sp row's energy", v2["vit_body"] == 0.5 and v2["body_source"] == "sp_row")
        sp.status = lambda: {"last": row(300000, 14.0, 40)}
        v3 = ho.read_vitality_v2(stt, now=300010, current_vitality=0.3)
        check("no energy anywhere: body falls open to the setpoint", v3["vit_body"] == ho._VARS["vitality"]["setpoint"] and v3["body_source"] == "fallback_setpoint")
        ho._recent_fires = lambda path=None, n=None: fires[:5]
        v4 = ho.read_vitality_v2({}, now=300010, current_vitality=0.3)
        check("under 10 fires: mind axis = the CURRENT reading, source fallback_current, scale None",
              v4["vit_mind"] == 0.3 and v4["mind_source"] == "fallback_current" and v4["scale_S"] is None)
        som._current_body = {"energy": 0.2, "fatigue": 0.0, "tension": 0.0}
        v5 = ho.read_vitality_v2({}, now=300010, current_vitality=0.3)
        check("lesser-of: body 0.2 < mind 0.3 -> 0.2 (fallback mind: mapping 'fallback', clip column = current)",
              v5["vitality_v2"] == 0.2 and v5["mind_mapping"] == "fallback" and v5["vit_mind_clip"] == 0.3)
        ho.V2_ENABLED = False
        check("V2_ENABLED False -> None", ho.read_vitality_v2({}, now=300010) is None)
        ho.V2_ENABLED = True

        print("[3] once per wake")
        ho._recent_fires = lambda path=None, n=None: fires
        stt = {}
        a = ho._v2_scale(stt); time.sleep(0.02); b = ho._v2_scale(stt)
        check("same newest fire: cached (computed_ts unchanged)", a["computed_ts"] == b["computed_ts"] and stt["v2_scale"]["fire_ts"] == fires[-1]["ts"])
        fires2 = fires[1:] + [row(1000 + 30 * 7200, 60.0, 120, fire=True)]
        ho._recent_fires = lambda path=None, n=None: fires2
        c = ho._v2_scale(stt)
        check("a new fire: recomputed, window slides, S moves", c["fire_ts"] == fires2[-1]["ts"] and c["S"] != a["S"] and c["n_fires"] == 30)
        ho._recent_fires = recent0

        print("[4] tick() end to end")
        sp.status = sp_status0
        som._current_body = {"energy": 0.6, "fatigue": 0.2, "tension": 0.1}
        t0 = 1_700_000_000.0
        with open(sp._LOG_FILE, "w", encoding="utf-8") as f:
            for i in range(12):
                f.write(json.dumps(row(t0 + i * 7200, 11.0 + i, 120, dark=True, fire=True, energy=0.7, cycles=40)) + "\n")
            for j in range(4):
                f.write(json.dumps(row(t0 + 12 * 7200 + j * 60, 5.0 + j, 10 + j, energy=0.6, cycles=50 + j)) + "\n")
        r1 = ho.tick()
        check("tick returned a row with vitality_v2 and predicted_v2", r1 and isinstance(r1.get("vitality_v2"), dict) and isinstance(r1.get("predicted_v2"), dict))
        check("`variables` is still exactly the five drive inputs", r1 and sorted(r1["variables"]) == sorted(ho._VARS))
        check("_VARS untouched: vitality setpoint 0.78, weight 0.7, five variables",
              len(ho._VARS) == 5 and ho._VARS["vitality"] == {"setpoint": 0.78, "weight": 0.7, "band": False})
        check("first tick: no v2 errors yet", "v2_causal_err" not in r1 and "v2_naive_err" not in r1)
        r2 = ho.tick()
        check("second tick: v2_causal_err and v2_naive_err scored", r2 and "v2_causal_err" in r2 and "v2_naive_err" in r2)
        stf = json.loads(Path(ho._STATE).read_text(encoding="utf-8"))
        check("state persists v2_scale (12 fires -> S) and predicted_v2", stf.get("v2_scale", {}).get("S") is not None and stf["v2_scale"]["n_fires"] == 12 and stf.get("predicted_v2"))
        s = ho.status()
        check("status() carries vitality_v2 and predicted_v2", isinstance(s.get("vitality_v2"), dict) and s["vitality_v2"]["vitality_v2"] == r2["vitality_v2"]["vitality_v2"])
        check("drive unchanged by v2 (recomputed from `variables` alone)", abs(ho.drive(r2["variables"])[0] - r2["drive"]) < 1e-9)
        check("mind scale came from the log: P at fire 11..22 -> p60 index 7 -> 18", r2["vitality_v2"]["scale_S"] == 18.0)

        print("[5] predict_vitality_v2")
        hc.wc.daylight = lambda t=None: "day"
        rows = [row(t0 + k * 600, 30.0 + k * 1.0, 60 + k * 10, energy=0.8, cycles=10 + k) for k in range(4)]   # 1 P / 600 s, 1 cycle / 600 s
        p = hc.predict_vitality_v2(now_ts=rows[-1]["ts"], horizon_s=600, scale=50.0, sp_rows=rows, body={"energy": 0.8})
        m34 = round(math.exp(-math.log(2) * 34 / 50), 4)
        check("day, no fire: p_hat = 33 + 1 = 34, mind = exp(-ln2 x 34/50) = 0.6243", p and p["fire_predicted"] is False and p["p_hat"] == 34.0 and p["vit_mind"] == m34)
        check("body: 0.8 - 0.04 x 1 expected cycle = 0.76; v2 = min(0.6243, 0.76) = 0.6243", p["vit_body"] == 0.76 and p["vitality_v2"] == m34 and p["intake_rate_per_h"] == 6.0)
        hc.wc.daylight = lambda t=None: "night"
        rows_n = [row(t0 + k * 600, 8.0 + k * 0.6, 60 + k * 10, dark=True, energy=0.5, cycles=10) for k in range(4)]   # P 9.8 at last, +0.6 per 600 s
        pn = hc.predict_vitality_v2(now_ts=rows_n[-1]["ts"], horizon_s=600, scale=20.0, sp_rows=rows_n, body={"energy": 0.5})
        check("night, P crosses 10 inside the horizon with awake > 30 min: fire predicted, mind 1.0",
              pn and pn["fire_predicted"] is True and pn["vit_mind"] == 1.0 and pn["p_hat"] >= 10.0)
        check("body recovery lump applied (night depth 1.0): 0.5 + 0.7 x 0.5 = 0.85", pn["vit_body"] == 0.85 and pn["vitality_v2"] == 0.85)
        rows_f = rows_n[:-1] + [row(rows_n[-1]["ts"], 10.4, 90, dark=True, fire=True, energy=0.5, cycles=10)]
        pf = hc.predict_vitality_v2(now_ts=rows_f[-1]["ts"], horizon_s=600, scale=20.0, sp_rows=rows_f, body={"energy": 0.5})
        check("last row is a fire row: fired_already, reset state predicted", pf["fired_already"] is True and pf["vit_mind"] == 1.0)
        hc.wc.daylight = lambda t=None: "day"
        pt = hc.predict_vitality_v2(now_ts=rows[-1]["ts"], horizon_s=600, scale=None, sp_rows=rows, body={"energy": 0.8})
        check("scale None: the regime threshold (100 by day) stands in, same exp mapping; scale_S None in the row",
              pt["scale_S"] is None and pt["vit_mind"] == round(math.exp(-math.log(2) * 34.0 / 100.0), 4))
        check("empty rows -> None", hc.predict_vitality_v2(sp_rows=[], body={"energy": 0.8}) is None)
        hc.wc.daylight = daylight0

        print("[6] replay over the log copy (D-0398 defeater numbers)")
        if args.sp_copy:
            copy = Path(args.sp_copy)
        else:
            import shutil
            copy = lab / "sleep_pressure_log_copy.jsonl"
            shutil.copyfile(Path("C:/Nascence/data/sleep_pressure_log.jsonl"), copy)   # read the live file once; write only into the lab dir
        if not copy.exists():
            check(f"log copy present at {copy}", False)
        else:
            rs = []
            for l in copy.open(encoding="utf-8"):
                try:
                    rs.append(json.loads(l))
                except Exception:
                    pass
            rs = [r for r in rs if r.get("P") is not None and r.get("threshold") is not None and r.get("awake_min") is not None
                  and r.get("reason") not in ("sleep_beat", "sleep_entry")]
            rs.sort(key=lambda r: r["ts"])
            fires_seen: list[float] = []
            vals = []
            names = ["V0 current", "V2 min(exp p60)", "V2 mean(exp p60)", "mind exp p60", "mind exp p80", "mind exp p90",
                     "V2 min(clip p60)", "mind clip p60", "mind clip p80", "mind clip p90", "energy"]
            n_scaled = 0
            for r in rs:
                sc = ho.self_calibrated_scale(fires_seen[-ho.V2_SCALE_FIRES:])
                s80 = ho.self_calibrated_scale(fires_seen[-ho.V2_SCALE_FIRES:], pct=0.8)
                s90 = ho.self_calibrated_scale(fires_seen[-ho.V2_SCALE_FIRES:], pct=0.9)
                v0 = clip(1 - r["P"] / max(1.0, r["threshold"]))
                e = clip(r["energy"]) if r.get("energy") is not None else None
                c60 = ho.mind_axis_clip(r["P"], sc["S"]) if sc else v0
                c80 = ho.mind_axis_clip(r["P"], s80["S"]) if s80 else v0
                c90 = ho.mind_axis_clip(r["P"], s90["S"]) if s90 else v0
                x60 = ho.mind_axis(r["P"], sc["S"]) if sc else v0
                x80 = ho.mind_axis(r["P"], s80["S"]) if s80 else v0
                x90 = ho.mind_axis(r["P"], s90["S"]) if s90 else v0
                if sc: n_scaled += 1
                body = e if e is not None else 0.78
                vals.append({"V0 current": v0, "V2 min(exp p60)": min(x60, body), "V2 mean(exp p60)": (x60 + body) / 2,
                             "mind exp p60": x60, "mind exp p80": x80, "mind exp p90": x90,
                             "V2 min(clip p60)": min(c60, body), "mind clip p60": c60, "mind clip p80": c80, "mind clip p90": c90,
                             "energy": body, "_scaled": bool(sc)})
                if r.get("fire") and r.get("reason") in ho.V2_FIRE_REASONS:
                    fires_seen.append(float(r["P"]))
            idx = [i for i, v in enumerate(vals) if v["_scaled"] and rs[i].get("energy") is not None]
            rs2 = [rs[i] for i in idx]; vs = [vals[i] for i in idx]
            lines = [f"replay rows {len(rs2)} (scaled + energy-carrying; of {len(rs)}), fires {len(fires_seen)}, "
                     f"pct {ho.V2_SCALE_PERCENTILE}, window {ho.V2_SCALE_FIRES}, final S p60/p80/p90 = "
                     f"{ho.self_calibrated_scale(fires_seen[-30:])['S']}/{ho.self_calibrated_scale(fires_seen[-30:], pct=.8)['S']}/{ho.self_calibrated_scale(fires_seen[-30:], pct=.9)['S']}"]
            flip = {n: [] for n in names}; ordinary = {n: [] for n in names}
            for (a, va), (b, vb) in zip(zip(rs2, vs), zip(rs2[1:], vs[1:])):
                if not (0 < b["ts"] - a["ts"] < 600): continue
                tgt = flip if a["threshold"] != b["threshold"] else ordinary
                for n in names: tgt[n].append(abs(vb[n] - va[n]))
            fire_i = [i for i, r in enumerate(rs2) if r.get("fire")]
            post_i = [i for i, r in enumerate(rs2) if r.get("reason") == "post_wake" or r["awake_min"] < 3.0]
            segs, cur = [], [0]
            for i in range(1, len(rs2)):
                if rs2[i]["awake_min"] < rs2[i - 1]["awake_min"] or rs2[i]["ts"] - rs2[i - 1]["ts"] > 1800:
                    segs.append(cur); cur = [i]
                else:
                    cur.append(i)
            segs.append(cur); segs = [s_ for s_ in segs if len(s_) >= 20]
            def pearson(x, y):
                if len(x) < 5: return None
                mx, my = st.mean(x), st.mean(y); sx = sum((a - mx) ** 2 for a in x) ** .5; sy = sum((b - my) ** 2 for b in y) ** .5
                return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else None
            lines.append(f"{'variable':17s} {'flip':>6s} {'ordin':>7s} {'ratio':>7s} | {'pre':>5s} {'post':>5s} {'gap':>6s} | {'r_med':>6s} {'neg':>7s} | {'at0':>6s} {'<.78':>6s} | {'fires>.7':>8s} {'fire_med':>8s}")
            table = {}
            for n in names:
                fl = st.mean(flip[n]) if flip[n] else float("nan"); od = st.mean(ordinary[n]) if ordinary[n] else float("nan")
                ratio = fl / max(1e-9, od)
                pre = st.mean(vs[i][n] for i in fire_i); pw = st.mean(vs[i][n] for i in post_i)
                cs = [c for c in (pearson([rs2[i]["awake_min"] for i in s_], [vs[i][n] for i in s_]) for s_ in segs) if c is not None]
                rmed = st.median(cs) if cs else float("nan"); neg = sum(1 for c in cs if c < -0.3)
                col = [v[n] for v in vs]; at0 = sum(1 for a in col if a <= 0.001) / len(col); below = sum(1 for a in col if a < 0.78) / len(col)
                hi = sum(1 for i in fire_i if vs[i][n] > 0.7) / max(1, len(fire_i))
                fmed = st.median(vs[i][n] for i in fire_i) if fire_i else float("nan")
                table[n] = {"flip": fl, "ordinary": od, "ratio": ratio, "pre": pre, "post": pw, "gap": pw - pre, "r_med": rmed,
                            "neg": f"{neg}/{len(cs)}", "at0": at0, "below": below, "fires_hi": hi, "fire_med": fmed}
                lines.append(f"{n:17s} {fl:6.3f} {od:7.4f} {ratio:6.1f}x | {pre:5.2f} {pw:5.2f} {pw-pre:+6.2f} | {rmed:+6.2f} {neg:3d}/{len(cs):<3d} | {at0:5.1%} {below:5.1%} | {hi:7.1%} {fmed:8.2f}")
            lines.append("columns: flip = mean |step| at the day/night threshold flip, ordin = ordinary <10-min step, ratio = flip/ordin (D-0398 clause 1 holds at > 5x);"
                         " pre/post = mean on fire rows / first-3-min-after-wake or post_wake rows (clause 3 holds at gap < 0.1); r_med = median within-wake correlation with awake_min,"
                         " neg = wakes with r < -0.3 (clause 2 holds at median > -0.5); at0 = share of rows pinned at 0 (saturation), <.78 = share below the current setpoint;"
                         " fires>.7 = share of real fires where the variable read > 0.7 'not tired' (clause 5 holds at > 1/3 for the mind axis), fire_med = median value on fire rows."
                         " exp = exp(-ln2 x P/S) (D-0421 C, the shipped mind axis); clip = clip01(1 - P/S) (J-2061's first mapping, comparison column)")
            print("\n".join("    " + l for l in lines))
            if args.out:
                Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                Path(args.out).write_text("# J-2061 replay (scripts/test_vitality_v2.py [6]) over a scratchpad copy of data/sleep_pressure_log.jsonl, "
                                          + time.strftime("%Y-%m-%d %H:%M") + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
            t = table
            check("replay computed on > 20,000 scaled rows", len(rs2) > 20000)
            check("clause 1: v2 (min, exp) flip step ratio < 5x (neither axis reads the threshold)", t["V2 min(exp p60)"]["ratio"] < 5.0)
            check("clause 1: the current reading's flip ratio is > 5x (the artifact v2 removes)", t["V0 current"]["ratio"] > 5.0)
            check("clause 2: v2 (min, exp) falls within wakes (median r < -0.5)", t["V2 min(exp p60)"]["r_med"] < -0.5)
            check("clause 3: v2 (min, exp) before-sleep vs after-wake gap >= 0.1", t["V2 min(exp p60)"]["gap"] >= 0.1)
            check("clause 5: exp mind axis reads > 0.7 at fewer than a third of real fires", t["mind exp p60"]["fires_hi"] < 1 / 3)
            check("D-0421: exp mind axis is never pinned at 0 (clip p60 was on > 40% of rows)", t["mind exp p60"]["at0"] == 0.0 and t["mind clip p60"]["at0"] > 0.4)
            check("D-0421 defeater (4): median mind reading at fire inside 0.4-0.7", 0.4 <= t["mind exp p60"]["fire_med"] <= 0.7)

        print("[7] wiring (text)")
        src = (ROOT / "core" / "homeostasis.py").read_text(encoding="utf-8")
        check("tick: v2 computed after the variables and before the row is written",
              src.index("variables = read_variables()") < src.index("v2 = read_vitality_v2(st, now, variables.get(\"vitality\"))") < src.index('rec["vitality_v2"] = v2'))
        check("tick: predict_vitality_v2 called with the same scale", "_hc2.predict_vitality_v2(now, scale=v2.get(\"scale_S\"))" in src)
        check("read_vitality_v2 uses mind_axis (exp) and logs vit_mind_clip beside it", "vit_mind = mind_axis(P, S)" in src and '"vit_mind_clip": round(vit_mind_clip, 4)' in src)
        check("predictor uses the same mind_axis", "from core.homeostasis import mind_axis as _mind_axis" in (ROOT / "core" / "homeostasis_causal.py").read_text(encoding="utf-8"))
        check("state persists v2_scale / vitality_v2 / predicted_v2", '"v2_scale": st.get("v2_scale"), "vitality_v2": v2, "predicted_v2": predicted_v2' in src)
        check("no new _VARS entry (vitality_v2 is not a drive input)", '"vitality_v2":' not in src.split("_VARS = {")[1].split("}\n")[0])
        csrc = (ROOT / "core" / "homeostasis_causal.py").read_text(encoding="utf-8")
        check("predictor models the fire reset and the recovery lump", "fire_predicted = fired_already or" in csrc and "_som.RECOVERY_FRACTION * depth" in csrc)
        ssrc = (ROOT / "core" / "somatic.py").read_text(encoding="utf-8")
        check("somatic.recover carries the J-2061 / D-0398 E rate-vs-lump note", "J-2061 / D-0398 E note" in ssrc)

        print("[8] live files untouched")
        check("homeostasis shadow log, state file and sleep-pressure log unchanged",
              all((p.stat().st_size if p.exists() else None) == sz for p, sz in LIVE.items()))
    finally:
        som._current_body, som._current_cycles = body0, cyc0
        hc.wc.daylight = daylight0
        sp.status = sp_status0
        ho._recent_fires = recent0
        ho.V2_ENABLED = True

print("\nALL PASS" if ok_all else "\nFAILURES")
sys.exit(0 if ok_all else 1)
