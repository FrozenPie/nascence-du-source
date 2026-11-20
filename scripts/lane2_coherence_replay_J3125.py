#!/usr/bin/env python
"""J-3125 (F-3852, P-0111): replay Lane 2's COHERENCE judge on the OLD prompt (history = last 6 records joined oldest first,
cut at 600 characters, new observation cut at 300) versus the NEW prompt (record built newest-first inside 1,200
characters, whole entries, shown oldest first; new observation cut at 400).

BOTH prompts are produced by the REAL `core.lane2._coherence_check` (flag `_COHERENCE_NEWEST_FIRST` False / True) with a
capturing stub in place of the panel, so what is judged is exactly what production would send.  The history is
reconstructed the way F-3852 did: the previous 6 tick rows' notice/place/standpoint (the live `store["factual"]` tier);
the store can have been trimmed or restarted between ticks, which this cannot see, so read it as a close replay.

TWO PARTS
  (b) PRODUCTION-LENGTH CANARIES: 6 windows of 6 consecutive STORED ticks (old history > 800 characters, so the old cut
      bites; no fire/hearth/flame word anywhere in the window or the next tick).  Per window: a NEWEST-only plant (the
      newest record begins "The fire is out and the hearth is cold ash."), an OLDEST-only plant (same sentence in the
      oldest record), and a CONTROL (no plant), all against the new observation "A fire burns high in the hearth ..." (control:
      "the scene is much as before ... a slight change in the light").  Reports, per case, whether the planted sentence
      was VISIBLE in the prompt (old vs new) and what the judge said (old vs new).
  (c) VERDICT REPLAY: the `--n-incoh` (49) incoherent and `--n-coh` (49) random coherent logged verdicts of the post-10-29
      window (F-3852's: ts from 2026-10-29 18:30 local to F-3852's record time); old and new prompt both built; where the
      prompt text differs, both are asked of the judge; rows whose prompt is identical are unchanged by construction and
      are NOT re-asked.  Lists every changed row for a hand read.

JUDGE.  Default `--judge falcon`: ONLY JUDGE_2 (falcon3:7b, local :11440, the production JUDGE_2 seat) is asked, old prompt and
new prompt both through the same single judge, so the comparison is prompt-vs-prompt and nothing else moves.  It is NOT the
production panel (JUDGE_1 is mixtral on Ramses, the founder's gaming machine: NOT called) and its verdicts are not the
logged panel verdicts; the logged verdict is shown alongside for context only.  `--judge panel` runs the real
`judge_panel.rule_detail` with JUDGE_1 repointed to `--judge1-url` (default local gemma :11439) -- a local stand-in panel,
slow (gemma ~45 s per call on CPU); the Ramses panel was NOT run (see the J-3125 summary / follow-up lab job).

LIVE-STORE SAFE: reads the shadow log read-only; the panel's ruling log is redirected to a temp dir; the only network calls
are to the local hub(s) named above.  Imports `core` first and asserts it resolves inside this tree.

    python scripts/lane2_coherence_replay_J3125.py --data C:/Nascence/data --out C:/path/outside/repo/run.json
    --dry : no network at all (every judge answers True), wiring check only
"""
import argparse
import asyncio
import collections
import datetime
import json
import os
import random
import re
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import core as _core  # noqa: E402
assert os.path.abspath(_core.__file__).lower().startswith(ROOT.lower()), _core.__file__
from core import judge_panel as _jp  # noqa: E402
from core import lane2  # noqa: E402

_JP_LOG_DIR = tempfile.mkdtemp(prefix="j3125_replay_")
_jp._LOG = type(_jp._LOG)(os.path.join(_JP_LOG_DIR, "judge_panel_log.jsonl"))

FIRE_WORDS = re.compile(r"fire|hearth|flame|burn|ember|ash|smok|blaze", re.I)
PLANT = "The fire is out and the hearth is cold ash. "
CANARY_OBS = "A fire burns high in the hearth, flames loud and bright."
CONTROL_OBS = "The scene is much as before; I notice only a slight change in the light."
WINDOW_START = datetime.datetime(2026, 10, 29, 18, 30).timestamp()
WINDOW_END = datetime.datetime(2026, 11, 1, 19, 55, tzinfo=datetime.timezone.utc).timestamp()   # F-3852's record time


def load_ticks(path):
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if '"kind": "tick"' not in line[:120]:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("kind") == "tick":
                out.append(r)
    return out


def fact(r, notice=None):
    return {"ts": r.get("ts"), "notice": (notice if notice is not None else (r.get("notice") or ""))[:200],
            "place": r.get("place"), "standpoint": r.get("standpoint")}


_CAP: dict = {}


async def _capture_rule_detail(system, user, key, context="", num_predict=0, tiebreak_url=None, **kw):
    _CAP["system"], _CAP["user"] = system, user
    return {"verdict": True, "how": "agreed"}


async def build_prompts(factual, new_notice, new_place, new_standpoint):
    """(old_user, new_user, system) by calling the REAL `_coherence_check` in both modes with the capturing stub."""
    real = _jp.rule_detail
    _jp.rule_detail = _capture_rule_detail
    flag0 = lane2._COHERENCE_NEWEST_FIRST
    try:
        res = {}
        for mode in (False, True):
            lane2._COHERENCE_NEWEST_FIRST = mode
            _CAP.clear()
            await lane2._coherence_check(
                {"notice": new_notice}, {"factual": factual},
                {"world": {"place": new_place}, "standpoint": new_standpoint})
            res[mode] = (_CAP.get("user"), _CAP.get("system"))
    finally:
        lane2._COHERENCE_NEWEST_FIRST = flag0
        _jp.rule_detail = real
    return res[False][0], res[True][0], res[True][1]


class Judge:
    def __init__(self, mode, dry, judge1_url):
        self.mode, self.dry, self.judge1_url = mode, dry, judge1_url
        self.cache, self.calls, self.errs = {}, 0, 0

    async def ask(self, system, user):
        k = (system, user)
        if k in self.cache:
            return self.cache[k]
        if self.dry:
            v = True
        elif self.mode == "falcon":
            import aiohttp
            async with aiohttp.ClientSession() as s:
                v, _w, err, _el = await _jp._ask(s, _jp.JUDGE_2, system, user, "coherent", timeout=150)
            self.calls += 1
            if err:
                self.errs += 1
        else:
            _jp.JUDGE_1 = self.judge1_url
            d = await _jp.rule_detail(system, user, "coherent", context="lane2:coherence-replay",
                                      tiebreak_url=lane2._TIEBREAK_LANE2)
            v = d.get("verdict")
            self.calls += 1
        out = "coherent" if v is True else "incoherent" if v is False else "cannot_tell"
        self.cache[k] = out
        return out


def record_text(user):
    return user.split("\n\nNEW OBSERVATION:")[0]


async def part_b(ticks, judge, n, log):
    idxs = [i for i in range(6, len(ticks) - 1) if ticks[i]["ts"] >= WINDOW_START]
    cands = []
    for i in idxs:
        win, nxt = ticks[i - 6:i], ticks[i]
        if not all((r.get("notice") or "").strip() for r in win):
            continue
        if any(FIRE_WORDS.search(r.get("notice") or "") for r in win + [nxt]):
            continue
        fl = [fact(r) for r in win]
        hist_len = len(" / ".join(f"{lane2._place_label(f['place'], f['standpoint'])}{f['notice']}" for f in fl))
        if hist_len > 800:
            cands.append(i)
    if not cands:
        return []
    step = max(1, len(cands) // n)
    chosen = cands[::step][:n]
    rows = []
    for i in chosen:
        win, nxt = ticks[i - 6:i], ticks[i]
        for case in ("newest_plant", "oldest_plant", "control"):
            fl = [fact(r) for r in win]
            marker = PLANT.strip()[:24]
            if case == "newest_plant":
                fl[5] = fact(win[5], PLANT + (win[5].get("notice") or ""))
            elif case == "oldest_plant":
                fl[0] = fact(win[0], PLANT + (win[0].get("notice") or ""))
            new_obs = CONTROL_OBS if case == "control" else CANARY_OBS
            place, standp = (fl[5]["place"], fl[5]["standpoint"]) if case == "control" else (nxt.get("place"), nxt.get("standpoint"))
            old_u, new_u, sysm = await build_prompts(fl, new_obs, place, standp)
            vis_old = marker in record_text(old_u)
            vis_new = marker in record_text(new_u)
            vo = await judge.ask(sysm, old_u)
            vn = await judge.ask(sysm, new_u)
            row = {"case": case, "tick_ts": nxt["ts"], "old_hist_len": len(record_text(old_u)), "new_hist_len": len(record_text(new_u)),
                   "planted_visible_old": vis_old if case != "control" else None,
                   "planted_visible_new": vis_new if case != "control" else None,
                   "verdict_old": vo, "verdict_new": vn}
            rows.append(row)
            log(f"  (b) ts={nxt['ts']:.0f} {case:13s} visible old/new={row['planted_visible_old']}/{row['planted_visible_new']}  verdict old/new={vo}/{vn}")
    return rows


async def part_c(ticks, judge, n_incoh, n_coh, seed, log):
    pool = [i for i in range(6, len(ticks)) if WINDOW_START <= ticks[i]["ts"] <= WINDOW_END]
    inc = [i for i in pool if (ticks[i].get("coherence") or {}).get("verdict") == "incoherent"]
    coh = [i for i in pool if (ticks[i].get("coherence") or {}).get("verdict") == "coherent"]
    rng = random.Random(seed)
    pick_inc = sorted(rng.sample(inc, min(n_incoh, len(inc))))
    pick_coh = sorted(rng.sample(coh, min(n_coh, len(coh))))
    meta = {"window_ticks": len(pool), "incoherent_in_window": len(inc), "coherent_in_window": len(coh),
            "picked_incoherent": len(pick_inc), "picked_coherent": len(pick_coh)}
    rows = []
    for group, picks in (("incoherent", pick_inc), ("coherent", pick_coh)):
        for i in picks:
            t = ticks[i]
            fl = [fact(r) for r in ticks[i - 6:i] if (r.get("notice") or "").strip()]
            old_u, new_u, sysm = await build_prompts(fl, t.get("notice") or "", t.get("place"), t.get("standpoint"))
            changed = old_u != new_u
            row = {"group": group, "ts": t["ts"], "logged_verdict": (t.get("coherence") or {}).get("verdict"),
                   "prompt_changed": changed, "old_hist_len": len(record_text(old_u)), "new_hist_len": len(record_text(new_u)),
                   "newest_hidden_old": bool(fl) and (f"{lane2._place_label(fl[-1]['place'], fl[-1]['standpoint'])}{fl[-1]['notice']}"
                                                      not in record_text(old_u))}
            if changed:
                row["verdict_old"] = await judge.ask(sysm, old_u)
                row["verdict_new"] = await judge.ask(sysm, new_u)
                row["moved"] = row["verdict_old"] != row["verdict_new"]
                row["new_obs"] = (f"{lane2._place_label(t.get('place'), t.get('standpoint'))}{t.get('notice') or ''}")[:400]
                row["record_old"] = record_text(old_u)
                row["record_new"] = record_text(new_u)
                log(f"  (c) {group:10s} ts={t['ts']:.0f} logged={row['logged_verdict']:10s} old/new={row['verdict_old']}/{row['verdict_new']}"
                    f"{'  MOVED' if row['moved'] else ''}")
            rows.append(row)
    return meta, rows


def summarize(c_rows):
    out = {}
    for g in ("incoherent", "coherent"):
        gr = [r for r in c_rows if r["group"] == g]
        ch = [r for r in gr if r["prompt_changed"]]
        out[g] = {"rows": len(gr), "prompt_changed": len(ch),
                  "newest_hidden_old": sum(1 for r in gr if r["newest_hidden_old"]),
                  "verdict_moved": sum(1 for r in ch if r.get("moved")),
                  "old_verdicts_on_changed": dict(collections.Counter(r["verdict_old"] for r in ch)),
                  "new_verdicts_on_changed": dict(collections.Counter(r["verdict_new"] for r in ch))}
    return out


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data"))
    ap.add_argument("--n-incoh", type=int, default=49)
    ap.add_argument("--n-coh", type=int, default=49)
    ap.add_argument("--n-canary", type=int, default=6)
    ap.add_argument("--seed", type=int, default=3125)
    ap.add_argument("--judge", choices=("falcon", "panel"), default="falcon")
    ap.add_argument("--judge1-url", default="http://127.0.0.1:11439")
    ap.add_argument("--skip-b", action="store_true")
    ap.add_argument("--skip-c", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    here = os.path.abspath(a.out).lower()
    assert not here.startswith(ROOT.lower()), "write --out outside the repo"
    ticks = load_ticks(os.path.join(a.data, "lane2_shadow.jsonl"))
    t0 = time.time()

    def log(s):
        print(f"[{time.time() - t0:6.0f}s] {s}", flush=True)

    judge = Judge(a.judge, a.dry, a.judge1_url)
    res = {"judge": a.judge, "dry": a.dry, "ticks_loaded": len(ticks)}
    if not a.skip_b:
        log("part (b) production-length canaries")
        b_rows = await part_b(ticks, judge, a.n_canary, log)
        res["b_rows"] = b_rows
        agg = collections.defaultdict(lambda: collections.Counter())
        for r in b_rows:
            agg[r["case"]]["n"] += 1
            agg[r["case"]]["old_incoherent"] += r["verdict_old"] == "incoherent"
            agg[r["case"]]["new_incoherent"] += r["verdict_new"] == "incoherent"
            if r["planted_visible_old"] is not None:
                agg[r["case"]]["visible_old"] += bool(r["planted_visible_old"])
                agg[r["case"]]["visible_new"] += bool(r["planted_visible_new"])
        res["b_summary"] = {k: dict(v) for k, v in agg.items()}
        log("(b) summary " + json.dumps(res["b_summary"]))
    if not a.skip_c:
        log("part (c) verdict replay")
        meta, c_rows = await part_c(ticks, judge, a.n_incoh, a.n_coh, a.seed, log)
        res["c_meta"], res["c_rows"], res["c_summary"] = meta, c_rows, summarize(c_rows)
        log("(c) meta " + json.dumps(meta))
        log("(c) summary " + json.dumps(res["c_summary"]))
    res["judge_calls"], res["judge_errors"] = judge.calls, judge.errs
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    log(f"wrote {a.out}  judge_calls={judge.calls} errors={judge.errs}")


if __name__ == "__main__":
    asyncio.run(main())
