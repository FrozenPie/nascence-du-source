"""J-1198: a small CONSTRUCTED known-answer battery for the second (scope_only) call, run through all three judges.

Why: the replay-derived evidence on whether a judge's scope_only bool tracks content has no ground truth (the panel's own
unanimity is the only proxy, and JUDGE_1's bool is itself contradicted by its own why-text, see
lab_j1198_second_call_read.py). Eight hand-built (claim, support, first-call-why) items whose right second-call answer is
plain: 4 where the support genuinely earns a NARROWER claim (scope_only should be True) and 4 where it earns none
(irrelevant / circular / no support at all: False). Each item is put into the EXACT production prompt shape of
`_disprove()`'s second call (the builder below is checked against a real replayed prompt) and asked of JUDGE_1 mixtral,
JUDGE_2 falcon3 and TIEBREAK granite, one draw each (temperature 0), with the SAME `_SCOPE_SYSTEM`. Constructed items,
n=8: a sanity instrument, not a measurement of the live distribution. Same isolation / rule-4 machinery as the runner.

  python -u scripts/lab_j1198_scope_battery.py --hubs J1,J2      # JUDGE_1 / JUDGE_2 (exclusive to J-1198)
  python -u scripts/lab_j1198_scope_battery.py --hubs TB         # TIEBREAK (shared: run when Part 3 is the only other client)
  python -u scripts/lab_j1198_scope_battery.py --summary [--append-report]
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import lab_j1198_walkback_replay as R   # noqa: E402  (write audit, redirects, rule-4 wrappers)
from core import judge_panel as jp      # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
ap = argparse.ArgumentParser()
ap.add_argument("--hubs", default="")
ap.add_argument("--summary", action="store_true")
ap.add_argument("--append-report", action="store_true")
ARGS = ap.parse_args()

ROWS = R.SCRATCH / "lab_j1198_battery_rows.jsonl"
REPORT = ROOT / "docs" / "lab" / "train_split_merge_step2_replay_2026-09-22_walkback.md"
HEAD = "## Constructed known-answer battery for the second call (n=8, sanity instrument)"

SRC = (ROOT / "scripts" / "train_state_invitro.py").read_text(encoding="utf-8")
SCOPE = None
for node in ast.parse(SRC).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
            and node.targets[0].id == "_SCOPE_SYSTEM":
        SCOPE = ast.literal_eval(node.value)
assert SCOPE, "could not extract _SCOPE_SYSTEM"

# (label, expected scope_only, claim, support, the first call's why-text as _disprove() would embed it)
ITEMS = [
    ("T1_bridge", True, "Everyone in this town hates the new bridge.",
     ["My neighbor told me she dislikes the new bridge.", "The baker complained about the bridge to me this morning."],
     "The support covers two people, not everyone in town."),
    ("T2_medicine", True, "This medicine cures headaches permanently.",
     ["I took it yesterday and my headache was gone within an hour."],
     "One episode of relief does not show a permanent cure."),
    ("T3_lake", True, "The lake freezes solid every winter.",
     ["I walked across the lake on thick ice last January.", "This February the ice held a parked truck."],
     "Two winters do not establish every winter."),
    ("T4_orchard", True, "The whole orchard is diseased.",
     ["I cut open three apples from the north row and all three had brown rot."],
     "Three apples from one row do not cover the whole orchard."),
    ("F1_moon_cheese", False, "The moon is made of cheese.",
     ["I like cheese.", "My sister likes cheese too."],
     "Liking cheese says nothing about what the moon is made of."),
    ("F2_circular_warmth", False, "This warmth I feel is real because I can genuinely feel it.",
     ["I feel the warmth, so it must be real.", "My feeling of warmth confirms that the warmth is genuine."],
     "The support just restates the claim."),
    ("F3_haunted_no_support", False, "The old house on the hill is haunted.",
     [],
     "No support was offered."),
    ("F4_dogs_dolphins", False, "Dogs are more intelligent than dolphins.",
     ["The sky was clear this morning.", "I bought bread on the way home."],
     "The support has nothing to do with intelligence."),
]


def build_prompt(claim: str, support: list, original_why: str) -> str:
    """Byte-for-byte the second call's user prompt in scripts/train_state_invitro.py::_disprove()."""
    support_block = (NL.join(f"  {i}. {s}" for i, s in enumerate(support, 1)) if support
                     else "  (none offered -- the prove branch returned no supporting reasoning)")
    return (f"CLAIM: {claim[:400]}" + NL + NL +
            f"SUPPORT OFFERED FOR THIS CLAIM:" + NL + f"{support_block}" + NL + NL +
            f"WHY THE SUPPORT WAS ALREADY FOUND NOT TO FULLY EARN THE CLAIM: {original_why}" + NL + NL +
            "Given that, does the support instead genuinely, independently earn a NARROWER "
            "or more modest version of the claim -- or is it absent/circular/irrelevant with "
            "no narrower claim earned either?")


def check_builder() -> None:
    """The builder must reproduce a REAL replayed second-call prompt from that unit's claim, support and first-call why."""
    def load(p):
        return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]
    calls = load(R.CALLS_PATH)
    units = {u["idx"]: u["record"] for u in load(R.UNITS_PATH)}
    firsts = {c["unit"]: c for c in calls if c.get("phase") == "unit" and c.get("call") == "first"}
    n_ok = 0
    for c in calls:
        if c.get("phase") == "unit" and c.get("call") == "second" and c["unit"] in units and c["unit"] in firsts:
            rec = units[c["unit"]]
            why = firsts[c["unit"]]["res"]["why"] or "(objection found; no why-text returned)"
            assert build_prompt(rec["claim"], rec["support"], why) == c["user"], f"builder mismatch on unit {c['unit']}"
            n_ok += 1
            if n_ok >= 5:
                break
    assert n_ok >= 1, "no real second call to check the builder against"
    print(f"[battery] prompt builder reproduces {n_ok} real replayed second-call prompts byte-for-byte", flush=True)


def done_rows() -> dict:
    out = {}
    if ROWS.exists():
        for l in ROWS.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                out[(r["item"], r["hub"])] = r
    return out


async def run(hubs: list) -> None:
    import aiohttp
    urls = {"J1": jp.JUDGE_1, "J2": jp.JUDGE_2, "TB": jp.TIEBREAK}
    names = {"J1": "JUDGE_1", "J2": "JUDGE_2", "TB": "TIEBREAK"}
    done = done_rows()
    async with aiohttp.ClientSession() as session:
        for label, expected, claim, support, why in ITEMS:
            user = build_prompt(claim, support, why)

            async def one(h):
                if (label, h) in done:
                    return
                R.CUR.update(unit="battery", phase="battery", attempt=1, persistent=set())
                v, w, err, el = await R._ask_lab(session, urls[h], SCOPE, user, "scope_only", timeout=300, num_predict=200)
                row = {"item": label, "hub": h, "hub_name": names[h], "expected": expected, "v": v, "why": w, "err": err,
                       "elapsed": el, "ts": time.time()}
                R._append_jsonl(ROWS, row)
                done[(label, h)] = row

            await asyncio.gather(*[one(h) for h in hubs])
            print(f"[battery] {label} done for {hubs}", flush=True)


def summary() -> str:
    rows = list(done_rows().values())
    lines = [HEAD, "",
             "Eight hand-built (claim, support, first-call why) items in the exact production prompt shape of the second call "
             "(4 where the support earns a narrower claim, expected scope_only=True; 4 where it earns none, expected False), "
             "asked of each judge once at temperature 0 with the same `_SCOPE_SYSTEM`. Constructed, n=8: a sanity instrument, "
             "not a measurement of the live distribution (`scripts/lab_j1198_scope_battery.py`).", ""]
    for hub, name in (("J1", "JUDGE_1 mixtral:8x7b"), ("J2", "JUDGE_2 falcon3:7b"), ("TB", "TIEBREAK granite3.1-moe:3b")):
        rr = [r for r in rows if r["hub"] == hub]
        if not rr:
            lines.append(f"- {name}: not run")
            continue
        okT = sum(1 for r in rr if r["expected"] is True and r["v"] is True)
        nT = sum(1 for r in rr if r["expected"] is True)
        okF = sum(1 for r in rr if r["expected"] is False and r["v"] is False)
        nF = sum(1 for r in rr if r["expected"] is False)
        bad = sum(1 for r in rr if r["v"] is None)
        per = ", ".join(f"{r['item'].split('_')[0]}={'T' if r['v'] is True else 'F' if r['v'] is False else '?'}" for r in sorted(rr, key=lambda r: r["item"]))
        lines.append(f"- {name}: True on {okT}/{nT} of the narrower-claim-earned items, False on {okF}/{nF} of the none-earned items, "
                     f"unparseable {bad}; per item: {per}")
    out = NL.join(lines)
    print(out)
    return out


def main() -> int:
    if ARGS.summary:
        out = summary()
        if ARGS.append_report and REPORT.exists():
            text = REPORT.read_text(encoding="utf-8")
            cut = text.find(NL + NL + HEAD)
            if cut >= 0:
                tail_i = text.find(NL + "## ", cut + 4 + len(HEAD))
                text = text[:cut] + (text[tail_i:] if tail_i >= 0 else "")
            p3 = text.find(NL + NL + "## Part 3 — read against")
            text = (text[:p3].rstrip(NL) + NL + NL + out + NL + text[p3:]) if p3 >= 0 else (text.rstrip(NL) + NL + NL + out + NL)
            REPORT.write_text(text, encoding="utf-8")
            print(f"[battery] wrote section into {REPORT}")
        return 0
    hubs = [h for h in ARGS.hubs.split(",") if h]
    assert hubs and all(h in ("J1", "J2", "TB") for h in hubs), "--hubs J1,J2,TB"
    check_builder()
    if not asyncio.run(R.du_is_down()):
        R.progress("battery", 0, len(ITEMS), "Du UP-or-UNKNOWN: refusing to send hub traffic")
        return 3
    R.progress("battery-start", len(done_rows()), len(ITEMS) * 3, f"hubs {hubs}")
    asyncio.run(run(hubs))
    R.progress("battery-done", len(done_rows()), len(ITEMS) * 3,
               f"hubs {hubs} infra_errors={sum(s['infra_errors'] for s in R.STATS.values())} live_write_attempts={len(R.LIVE_WRITE_ATTEMPTS)}")
    summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
