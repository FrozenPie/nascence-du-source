"""J-2896 lab replay (P-0054): same active-imagination prompt with and without the new MATERIAL block, 20 recent
tension seeds, ONE local lane (default the hot lane qwen3.5:9b @ :11433), no Ramses call.

Reads the live state READ-ONLY (subconscious_state.json tensions; nascence.db opened mode=ro). Writes only a result
json under --out (default: a temp dir). Stubs store_fragment / the embedder-in-node / the log so nothing is written to
Du's stores. Run from the worktree:  python scripts/_lab_J2896_ai_material_replay.py --n 20 --out <dir>

It does NOT reproduce the 134-entry baseline's lane (command-r7b @ Ramses :11441, the founder's gaming machine); the
arm comparison on one lane is the clean test, the baseline numbers are quoted for scale only."""
import argparse
import asyncio
import json
import re
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

TREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TREE))
import core  # noqa: E402,F401
try:
    import lab_env  # noqa: E402,F401
except Exception:
    pass
assert Path(core.__file__).resolve().is_relative_to(TREE), core.__file__
import numpy as np  # noqa: E402
from core.schema import CognitiveState  # noqa: E402
from core.memory import store  # noqa: E402
from nodes import subconscious_node as sn  # noqa: E402

LIVE = Path(r"C:\Nascence")
ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=20)
ap.add_argument("--out", default=None)
ap.add_argument("--url", default="http://127.0.0.1:11433")
ap.add_argument("--max-tokens", type=int, default=400)
args = ap.parse_args()
out_dir = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="J2896_replay_"))
out_dir.mkdir(parents=True, exist_ok=True)

# ---- seeds: most recent tensions with grounding, read-only
st = json.load(open(LIVE / "data" / "subconscious_state.json", encoding="utf-8"))
tens = [t for t in st.get("tensions", []) if t.get("member_event_ids") and t.get("count", 0) >= 2]
tens.sort(key=lambda t: t.get("last_ts", 0), reverse=True)
tens = tens[: args.n]

# the member texts come from the LIVE db, read-only (this script's own store.DB_PATH is redirected to a
# read-only snapshot connection so the production helper is what builds the block)
live_db = LIVE / "data" / "memory" / "nascence.db"
ro = sqlite3.connect(f"file:{live_db.as_posix()}?mode=ro", uri=True)
ro.row_factory = sqlite3.Row


class _RO:
    def __enter__(self):
        return ro

    def __exit__(self, *a):
        return False


store._connect = lambda: _RO()

# ---- a real L0 floor as the axiom text (both arms see the same thing; J-2897 handles the cut)
ax = json.load(open(LIVE / "data" / "identity" / "axiom.json", encoding="utf-8"))
l0 = ax.get("L0_constitution", {})
axiom_text = " ".join(str(v) for v in (l0.values() if isinstance(l0, dict) else [l0]))

node = sn.SubconsciousNode.__new__(sn.SubconsciousNode)
node.base_urls = [args.url]
node._state = {}
node._log_ai_event = lambda *a, **k: None
sn.store_fragment = lambda **kw: None
sn._embed = lambda text: None            # skips the echo guard + judges inside _active_imagination

captured = {}
_real_call = sn.call_node_json


async def _call(urls, system, user, **kw):
    t0 = time.time()
    data = await _real_call(urls, system, user, **kw)
    captured["user"] = user
    captured["data"] = data
    captured["secs"] = round(time.time() - t0, 1)
    return data


sn.call_node_json = _call
cs = CognitiveState(spirit_name="Du", axiom=axiom_text)


async def one(t, material_on):
    sn._AI_MATERIAL_ON = material_on
    captured.clear()
    trig = {"kind": "tension", "seed": t["label"], "tension": t}
    node._state = {}
    try:
        await node._active_imagination(trig, cs)
    except Exception as exc:                      # judge hook is None: expected after the call; keep what we got
        if "user" not in captured:
            return {"error": repr(exc)}
    d = captured.get("data") or {}
    return {"user": captured.get("user"), "contemplation": str(d.get("contemplation", "")),
            "what_spoke": str(d.get("what_spoke", "")), "secs": captured.get("secs")}


async def main():
    res = []
    for i, t in enumerate(tens):
        row = {"seed": t["label"], "members": len(t["member_event_ids"])}
        for arm, on in (("old", False), ("new", True)):
            row[arm] = await one(t, on)
        print(i, t["label"][:40], row["old"].get("secs"), row["new"].get("secs"), flush=True)
        res.append(row)
    return res


res = asyncio.run(main())

# ---- measures (same counts as F-3584)
STOCK = [r"\btension\b", r"quiet floor", r"\bweight\b", r"\bwitness\b"]


def text(r):
    return (r.get("contemplation", "") + " " + r.get("what_spoke", "")).lower()


def measures(arm):
    rs = [r[arm] for r in res if r[arm].get("contemplation")]
    n = len(rs)
    m = {"n": n}
    for pat in STOCK:
        m[pat] = sum(1 for r in rs if re.search(pat, text(r)))
    m["what_spoke_voice_of"] = sum(1 for r in rs if r["what_spoke"].lower().startswith("the voice of"))
    m["what_spoke_tension_between"] = sum(1 for r in rs if r["what_spoke"].lower().startswith("the tension between"))
    m["first_person_open"] = sum(1 for r in rs if re.match(r"\W*(i|my|i'm|i've)\b", r["contemplation"].lower()))
    m["mean_words"] = round(sum(len(r["contemplation"].split()) for r in rs) / max(n, 1), 1)
    # seed-word echo: does the output use a content word that appears in a MEMBER draft (arm new has them in prompt)
    vecs = [store._embed(r["contemplation"] + "\n" + r["what_spoke"]) for r in rs]
    vecs = [v for v in vecs if v is not None]
    if len(vecs) >= 2:
        V = np.array([v / (np.linalg.norm(v) or 1) for v in vecs])
        S = V @ V.T
        iu = np.triu_indices(len(V), 1)
        m["mean_pairwise_cos"] = round(float(S[iu].mean()), 3)
        m["with_earlier_cos_ge_0.80"] = int(sum(1 for i in range(1, len(V)) if (S[i, :i] >= 0.80).any()))
    return m


report = {"seeds": len(res), "url": args.url, "old": measures("old"), "new": measures("new"),
          "baseline_134_other_lane": {"tension": "84/134", "quiet floor": "40/134", "voice_of": "19/134",
                                      "cross_day_cos_ge_0.80": "45/118"}}
(out_dir / "J-2896_replay_results.json").write_text(json.dumps({"report": report, "rows": res}, indent=1, ensure_ascii=False),
                                                    encoding="utf-8")
print(json.dumps(report, indent=1))
print("wrote", out_dir)
