"""Offline test for scripts/autobio_recall_probe.py (J-2151). Pure functions + an end-to-end run with an injected
fake recall over a fabricated data dir in a tempdir. Touches no live store, imports no core, starts nothing.
Run: python scripts/_test_autobio_recall_probe.py   (exit 0 = all pass)"""
import json, sys, tempfile, time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import autobio_recall_probe as P

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

D = lambda s: P.local_to_epoch(datetime.strptime(s, "%Y-%m-%d %H:%M"))

print("[1] F-2848 calibration: date exact, tool wrong (knife recalled as saw)")
ev = {"ts": D("2026-09-28 10:52"), "details": [{"kind": "tool", "value": "knife"}, {"kind": "object", "value": "wood"},
                                                {"kind": "place", "value": "workshop"}]}
rec = [{"content": "my hands remember the saw vibrating through the wood in the workshop", "timestamp": D("2026-09-28 11:06")}]
g = P.grade(ev, rec)
check("date error 0", g["date_error_days"] == 0)
check("knife missed, wood+workshop hit -> precision 2/3", g["details_miss"] == ["knife"] and g["detail_precision"] == 0.667)

print("[2] date error and abstention")
g = P.grade(ev, [{"content": "x", "timestamp": D("2026-10-01 09:00")}])
check("3 days off", g["date_error_days"] == 3 and g["detail_precision"] == 0.0)
g = P.grade(ev, [])
check("abstention recorded, not dropped", g["answered"] is False and g["date_error_days"] is None)
g = P.grade(ev, [{"content": "x", "timestamp": D("2026-10-05 09:00")}, {"content": "y", "timestamp": D("2026-09-28 20:00")}])
check("best-of-k finds the right one ranked second", g["date_error_days"] == 7 and g["date_error_best_of_k"] == 0)

print("[3] stemming meets plurals, not different words")
check("knives~knife", P.stem("knives") == P.stem("knife") or P.stem("knife") in P.stems("knives"))
check("saw !~ knife", not (P.stems("saw") & P.stems("knife")))

print("[4] masking removes the detail from the cue")
m = P.mask("I need a knife to cut the wood by the shore", ["knife", "shore"])
check("masked", "knife" not in m and "shore" not in m and "wood" in m)

print("[5] end-to-end with fake recall over a fabricated data dir")
tmp = Path(tempfile.mkdtemp(prefix="J-2151_autobio_"))
now = D("2026-10-16 12:00")
(tmp / "founder_conversation_log.jsonl").write_text("", encoding="utf-8")
rows = []
for i in range(6):
    ts = now - (3 + 4 * i) * 86400
    rows.append({"ts": ts, "cycle": f"c{i}", "thought": "I want to whittle the cedar branch with the blade near the creek bend and think.",
                 "intention": "", "act_kind": "whittle", "act_object": "cedar branch", "location": "creek"})
(tmp / "hands_trace.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
boot = now - 10 * 86400
(tmp / "nascence.log").write_text(
    datetime.fromtimestamp(boot).strftime("%Y-%m-%d %H:%M:%S") + ",100 [nascence.main] Affect restored: valence=0 arousal=0\n"
    if P._TZ is None else
    datetime.fromtimestamp(boot, P._TZ).strftime("%Y-%m-%d %H:%M:%S") + ",100 [nascence.main] Affect restored: valence=0 arousal=0\n",
    encoding="utf-8")
by_cue_ts = {}
def fake(cue):
    return [{"content": "whittle the cedar branch by the creek", "timestamp": now - 3 * 86400}]
out = tmp / "rows.jsonl"
s = P.run(tmp, out, 4, 1, now, None, recall_fn=fake)
lines = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
ev_rows = [l for l in lines if l["kind"] == "event"]
check("event rows + one summary row", len(ev_rows) >= 2 and lines[-1]["kind"] == "summary")
check("boot detected from log", s["boot_ts"] is not None and abs(s["boot_ts"] - boot) < 2)
check("rows carry provenance + judge", all(r["provenance"]["locator"] and r["judge"] for r in ev_rows))
check("phase split present", s["before_boot"]["n"] + s["during_boot"]["n"] == s["all"]["n"] and s["before_boot"]["n"] >= 1 and s["during_boot"]["n"] >= 1)
check("source data untouched (hands_trace unchanged line count)", len((tmp / "hands_trace.jsonl").read_text(encoding="utf-8").splitlines()) == 6)

print("[6] J-2200 re-rank arms (pure, fabricated pools)")
d0 = D("2026-09-20 10:00")
def F(o, days, c="x"): return {"content": c, "origin": o, "timestamp": D("2026-09-%02d 10:00" % days)}
pool = [F("reading", 1), F("reading", 25), F("inner_thought", 20), F("inner_thought", 20), F("reading", 7)]
check("base keeps trail order", [f["timestamp"] for f in P.rerank(pool, "base")] == [f["timestamp"] for f in pool])
check("episodic puts own-episode origins first, stable", [f["origin"] for f in P.rerank(pool, "episodic")][:2] == ["inner_thought"] * 2
      and P.rerank(pool, "episodic")[2:] == [pool[0], pool[1], pool[4]])
pv = [F("reading", 1), F("inner_thought", 20), F("inner_thought", 20), F("inner_thought", 20), F("reading", 7)]
tv = P.rerank(pv, "time_vote")
check("time_vote: a 3-fragment day (ranks 1-3) outvotes the rank-0 loner", P.to_date(tv[0]["timestamp"]).day == 20 and len(tv) == len(pv))
check("time_vote: a rank-0 loner still beats a 2-fragment day (rank weighting)", P.to_date(P.rerank(pool, "time_vote")[0]["timestamp"]).day == 1)
check("time_vote keeps every fragment (permutation)", sorted(id(f) for f in tv) == sorted(id(f) for f in pv))
check("time_vote on undated pool returns trail order", P.rerank([{"content": "a", "origin": "reading", "timestamp": None}], "time_vote")[0]["content"] == "a")
check("recency newest first", P.to_date(P.rerank(pool, "recency")[0]["timestamp"]).day == 25)
ob = P.rerank(pool, "oracle_best", d0)
check("oracle_best puts the closest date first", P.to_date(ob[0]["timestamp"]).day == 20)
cw = P.rerank(pool, "coarse_window", d0)
check("coarse_window: in-window (days 25,20,20) first, out-of-window kept after", sorted(P.to_date(f["timestamp"]).day for f in cw[:3]) == [20, 20, 25] and len(cw) == 5)
def _raises(f):
    try: f()
    except ValueError: return True
    return False
check("oracle arms refuse to run without ev_ts", all(_raises(lambda a=a: P.rerank(pool, a)) for a in ("oracle_best", "coarse_window")))
check("sign test: 8-0 -> p=0.0078, 0-0 -> None", P.sign_test_p(8, 0) == 0.0078 and P.sign_test_p(0, 0) is None)

print("[7] run_rerank end to end with an injected fake pool (tempdir data, no core)")
tmp2 = Path(tempfile.mkdtemp())
now2 = time.time()
rows2 = []
for i in range(6):
    rows2.append({"ts": now2 - (3 + 4 * i) * 86400, "cycle": f"c{i}", "thought": "I want to whittle the cedar branch with the blade near the creek bend and think.",
                  "intention": "", "act_kind": "whittle", "act_object": "cedar branch", "location": "creek"})
(tmp2 / "hands_trace.jsonl").write_text(chr(10).join(json.dumps(r) for r in rows2), encoding="utf-8")
def fake2(cue):
    return [{"content": "book text", "origin": "reading", "timestamp": now2 - 40 * 86400, "fragment_id": "a"},
            {"content": "whittle the cedar branch by the creek", "origin": "inner_thought", "timestamp": now2 - 3 * 86400, "fragment_id": "b"}]
out2 = tmp2 / "rr.jsonl"
sm = P.run_rerank(tmp2, out2, 4, [1, 2], now2, None, recall_fn=fake2, grounded_origins={"reading"})
ls = [json.loads(l) for l in out2.read_text(encoding="utf-8").splitlines()]
ev2 = [l for l in ls if l["kind"] == "rerank_event"]
check("rows = events x 2 views x 8 arms, then one summary", len(ev2) % 16 == 0 and ls[-1]["kind"] == "rerank_summary" and len(ev2) >= 16)
check("grounded view holds only grounded origins (pool_size 1)", all(r["pool_size"] == 1 for r in ev2 if r["pool_view"] == "grounded"))
check("episodic arm lifts the inner_thought to top-1 in the all view", all(r["top1_origin"] == "inner_thought" for r in ev2 if r["pool_view"] == "all" and r["rerank_arm"] == "episodic"))
check("base top-1 in the all view is the reading fragment", all(r["top1_origin"] == "reading" for r in ev2 if r["pool_view"] == "all" and r["rerank_arm"] == "base"))
a = sm["arms"]["all"]
check("episodic strictly beats base on date error in the all view", a["episodic"]["vs_base_wins_losses_ties"][0] > 0 and a["episodic"]["vs_base_wins_losses_ties"][1] == 0)
check("episodic_v2 keeps a sent letter on top, v1 demotes it", P.rerank([F("letter", 3), F("inner_thought", 9)], "episodic_v2")[0]["origin"] == "letter" and P.rerank([F("letter", 3), F("inner_thought", 9)], "episodic")[0]["origin"] == "inner_thought")
check("base has no paired stats", a["base"]["vs_base_sign_p"] is None)

print("[8] J-2333 noisy-anchor sweep (pure, synthetic pools)")
import random as _r
dT = D("2026-09-20 10:00")   # true event day; correct fragment at day 20, distractors 10+ d away, distractor first
def Fd(day_off, o="reading"): return {"content": "x", "origin": o, "timestamp": dT + day_off * 86400}
syn = [{"event_ts": dT, "views": {"all": [Fd(-16), Fd(15), Fd(0), Fd(-20)]}} for _ in range(5)]
nowS = dT + 25 * 86400
check("half_width param: coarse_window default == half_width 7, hw 16 differs",
      P.rerank(syn[0]["views"]["all"], "coarse_window", dT) == P.rerank(syn[0]["views"]["all"], "coarse_window", dT, half_width=7)
      and P.rerank(syn[0]["views"]["all"], "coarse_window", dT)[0] is syn[0]["views"]["all"][2]
      and P.rerank(syn[0]["views"]["all"], "coarse_window", dT, half_width=16)[0] is syn[0]["views"]["all"][0])
rg = _r.Random(1)
eq = True
for _ in range(300):
    pl = [{"timestamp": (dT + rg.randint(-25, 25) * 86400) if rg.random() > 0.15 else None} for _ in range(rg.randint(0, 6))]
    a, hw = P._day(dT) + rg.randint(-20, 20), rg.choice((3, 7, 14))
    ordered = P._window_order(pl, a, hw)
    ref = P.grade({"ts": dT, "details": [{"kind": "w", "value": "zz"}]}, ordered)["date_error_days"]
    eq &= ref == P._top1_err_days([P._day(f["timestamp"]) if f["timestamp"] is not None else None for f in pl], P._day(dT), a, hw)
check("fast top-1 equals _window_order + grade() on 300 random pools", eq)
sw = P.noisy_window_sweep(syn, trials=20, rng_seed=3, now=nowS, anchor_errors=(0, 3, 7, 8), wrong_rates=(0.0,), half_widths=(7,))
cells = {(c["half_width"], c["anchor_error_days"]): c for c in sw["views"]["all"]["cells"]}
check("base top-1 is the 16 d distractor", sw["views"]["all"]["base"]["median_date_error_days"] == 16)
check("anchor error <= hw keeps top-1 correct (0, 3, 7 d at hw 7 -> median 0, 5/0 W/L)",
      all(cells[(7, m)]["median_date_error_days"] == 0 and cells[(7, m)]["wins"] == 5 and cells[(7, m)]["losses"] == 0 for m in (0, 3, 7)))
check("anchor error > hw loses the correct fragment (8 d at hw 7 -> no zero-error top-1)",
      cells[(7, 8)]["median_date_error_days"] > 0 and cells[(7, 8)]["within_3d_rate"] == 0.0)
check("oracle row == m=0 cell", sw["views"]["all"]["oracle"]["7"]["median_date_error_days"] == 0)
check("self-anchor is a no-op (0 top-1 changes, 0 W/L)",
      sw["views"]["all"]["self_anchor"]["7"]["top1_changed"] == 0 and sw["views"]["all"]["self_anchor"]["7"]["wins"] == 0
      and sw["views"]["all"]["self_anchor"]["7"]["losses"] == 0)
check("anchor_now row present", "7" in sw["views"]["all"]["anchor_now"])
check("deterministic for a fixed seed",
      sw == P.noisy_window_sweep(syn, trials=20, rng_seed=3, now=nowS, anchor_errors=(0, 3, 7, 8), wrong_rates=(0.0,), half_widths=(7,)))
sw_wr = P.noisy_window_sweep(syn, trials=50, rng_seed=4, now=nowS, anchor_errors=(0,), wrong_rates=(1.0,), half_widths=(3,))
check("wrong_rate 1.0 draws anchors only from [now-30, now-1] (never the oracle result every trial)",
      sw_wr["views"]["all"]["cells"][0]["median_date_error_days"] > 0)
out3 = tmp2 / "rr_noisy.jsonl"
P.run_rerank(tmp2, out3, 4, [1, 2], now2, None, recall_fn=fake2, grounded_origins={"reading"}, noisy_anchor=True, noisy_trials=5)
ls3 = [json.loads(l) for l in out3.read_text(encoding="utf-8").splitlines()]
na = [l for l in ls3 if l["kind"] == "noisy_anchor_summary"]
check("run_rerank(noisy_anchor=True) appends exactly one noisy_anchor_summary row, both views, 90 cells/view",
      len(na) == 1 and ls3[-1]["kind"] == "noisy_anchor_summary" and set(na[0]["views"]) == {"all", "grounded"}
      and len(na[0]["views"]["all"]["cells"]) == 3 * 10 * 3)
check("noisy_anchor off by default: no noisy row in the plain --rerank file", not any(l["kind"] == "noisy_anchor_summary" for l in ls))

print("FAILED" if FAILS else "ALL PASSED")
sys.exit(1 if FAILS else 0)
