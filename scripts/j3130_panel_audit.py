"""J-3130: can the judge panel audit the notice checker's flags with a NARROW said-vs-listed ask?

Reads docs/lab/J-3130_data/items.json (built by scripts/j3130_collect_flags.py), asks every item through
core.judge_panel.rule_detail (key 'contradicts', context 'lane2:notice_flag_audit') with the lane-2 gemma seat as
tiebreak, and writes per-item results to docs/lab/J-3130_data/panel_<arm>.json.  Resumable (skips ids already in the
out file).  LOCAL HUBS ONLY: every URL is asserted to be 127.0.0.1 (Ramses is the founder's gaming machine; the real
JUDGE_1 mixtral and the default granite TIEBREAK are on Ramses, so JUDGE_1 is stood in by a local hub, see --judge1).
Isolation: lab_env.isolate(db='empty', also=[(judge_panel, ['_LOG'])]) so nothing reaches data/judge_panel_log.jsonl.
Never edits core/lane2.py.

  python scripts/j3130_panel_audit.py --arm single --hub http://127.0.0.1:11439 --name gemma   # one judge, same _ask path
  python scripts/j3130_panel_audit.py --arm single --hub http://127.0.0.1:11440 --name falcon
  # NOT RUN in J-3130 (needs Ramses; follow-up lab job): the real panel, JUDGE_1 mixtral :11438 + falcon + a tiebreak
  python scripts/j3130_panel_audit.py --arm panel --allow-ramses --judge1 http://LAN-HOST:11438       --tiebreak http://127.0.0.1:11439        # gemma seat (_TIEBREAK_LANE2); --tiebreak http://LAN-HOST:11437 = default granite
  Extra variant (exploratory, tuned after seeing the narrow-ask misses, so NOT out-of-sample): --variant scale_enriched
  = SYSMSG_SCALE (adds the 0-to-1 scale and band order) + unit flags get the percept line carrying the number.
"""
import argparse, asyncio, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401  (BEFORE lab_env, so lab_env patches the same module objects)
from core import judge_panel  # noqa: E402

DATA = ROOT / "docs" / "lab" / "J-3130_data"
SYSMSG = ("You judge whether a short first-person NOTICE states something that a LISTED PERCEPT value makes false. "
          "Say true only if the notice's claim is opposite to or clearly at odds with the listed value; a loose or "
          "approximate word is not a contradiction. Output ONLY JSON: "
          "{\"contradicts\": true|false, \"why\": \"<one short clause>\"}")
# extra arm (not the job's ask): adds the one fact the narrow ask withholds, that percept numbers are 0-to-1 scales
SYSMSG_SCALE = SYSMSG.replace(
    "Say true only if",
    "Percept numbers are 0-to-1 scales (0 = none, 1 = maximum) unless they are compass degrees; bands run "
    "dark < dim < lit < bright and cold < cool < mild < warm < hot. Say true only if")
LOCAL = "http://127.0.0.1:"


def build_user(item: dict, enrich_unit: bool = False) -> str:
    listed = item["listed"]
    if enrich_unit and item["kind"] == "unit":
        # extra arm: replace the checker's synthetic 'unitless ...' text by the percept line carrying the number
        import re
        m = re.search(r"(\d+(?:\.\d+)?)", item["said"])
        if m:
            for ln in item["percept_lines"].splitlines():
                if m.group(1) in ln and ":" in ln:
                    listed = ln.strip("- ").strip()
                    break
    return f"NOTICE EXCERPT: {item['clause']}  LISTED PERCEPT: {listed}"


def assert_local(*urls, allow_ramses=False):
    for u in urls:
        if allow_ramses and u.startswith("http://LAN-HOST:"):
            continue
        assert u.startswith(LOCAL), f"non-local hub refused (Ramses is off limits): {u}"


async def run_single(items, out_path: Path, sysmsg: str, hub: str, enrich_unit=False, limit=None, timeout=240):
    """One judge, the SAME judge_panel._ask the panel uses (so prompt framing, format=json, num_predict and
    parsing are identical); records (verdict, why, err, seconds) per item.  Resumable."""
    import aiohttp
    out = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    t_all = time.monotonic()
    async with aiohttp.ClientSession() as session:
        for it in [i for i in items if str(i["id"]) not in out][:limit]:
            v, why, err, s = await judge_panel._ask(session, hub, sysmsg, build_user(it, enrich_unit),
                                                    "contradicts", timeout=timeout)
            out[str(it["id"])] = {"v": v, "why": why, "err": err, "s": s}
            out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
            print(it["id"], it["kind"], "weak" if it["weak"] else "solid", v, err, s, flush=True)
    return out, round(time.monotonic() - t_all, 1)


async def run_items(items, out_path: Path, sysmsg: str, tiebreak_url: str, enrich_unit=False, limit=None):
    out = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    todo = [it for it in items if str(it["id"]) not in out][:limit]
    t_all = time.monotonic()
    for it in todo:
        t0 = time.monotonic()
        d = await judge_panel.rule_detail(sysmsg, build_user(it, enrich_unit), "contradicts",
                                          context="lane2:notice_flag_audit", tiebreak_url=tiebreak_url)
        out[str(it["id"])] = {k: d.get(k) for k in ("v1", "v2", "verdict", "how", "err1", "err2", "err3",
                                                       "why1", "why2", "why3", "s1", "s2", "s3")}
        out[str(it["id"])]["wall_s"] = round(time.monotonic() - t0, 2)
        out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(it["id"], it["kind"], "weak" if it["weak"] else "solid", d.get("v1"), d.get("v2"),
              d.get("verdict"), d.get("how"), out[str(it["id"])]["wall_s"], flush=True)
    return out, round(time.monotonic() - t_all, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="single", choices=["single", "panel"])
    ap.add_argument("--hub", default="http://127.0.0.1:11439")
    ap.add_argument("--name", default="gemma")
    ap.add_argument("--allow-ramses", action="store_true", help="panel arm only; the founder's gaming machine")
    ap.add_argument("--judge1", default="http://127.0.0.1:11442")
    ap.add_argument("--judge2", default="http://127.0.0.1:11440")
    ap.add_argument("--tiebreak", default="http://127.0.0.1:11439")
    ap.add_argument("--variant", default="narrow", choices=["narrow", "scale_enriched"])
    ap.add_argument("--only-labeled", action="store_true", help="run only the hand-labeled items")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--timeout", type=int, default=240)
    a = ap.parse_args()
    if a.arm == "single":
        assert_local(a.hub)
    else:
        assert_local(a.judge1, a.judge2, a.tiebreak, allow_ramses=a.allow_ramses)
    items = json.loads((DATA / "items.json").read_text(encoding="utf-8"))
    if a.only_labeled:
        lab = json.loads((DATA / "hand_labels.json").read_text(encoding="utf-8"))["labels"]
        items = [i for i in items if str(i["id"]) in lab]
    sysmsg = SYSMSG_SCALE if a.variant == "scale_enriched" else SYSMSG
    tag = a.name if a.arm == "single" else "panel_" + a.tiebreak.rsplit(":", 1)[-1]
    out_path = DATA / f"{a.arm}_{tag}_{a.variant}.json"
    sys.path.insert(0, "C:/Users/USER/.claude/skills/job-queue")
    from lab_env import isolate
    with isolate(db="empty", also=[(judge_panel, ["_LOG"])]) as lab_dir:
        enrich = a.variant == "scale_enriched"
        if a.arm == "single":
            print("lab dir", lab_dir, "hub", a.hub)
            out, wall = asyncio.run(run_single(items, out_path, sysmsg, a.hub, enrich, a.limit, a.timeout))
        else:
            judge_panel.JUDGE_1, judge_panel.JUDGE_2, judge_panel._TIMEOUT = a.judge1, a.judge2, a.timeout
            print("lab dir", lab_dir, "J1", a.judge1, "J2", a.judge2, "TB", a.tiebreak)
            out, wall = asyncio.run(run_items(items, out_path, sysmsg, a.tiebreak, enrich, a.limit))
    print("done", len(out), "items; wall", wall, "s")


if __name__ == "__main__":
    main()
