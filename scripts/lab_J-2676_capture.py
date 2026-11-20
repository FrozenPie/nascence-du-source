"""J-2676 lab step A: capture real request payloads for the hot-lane prefix-cache replay.

Du must be DOWN. Runs 5 real founder utterances through the real node pipeline in a throwaway profile + lab_env
isolate(db="empty"), against the live ollama :11433 lane, recording every aiohttp POST (url, payload, reply counts,
wall). Non-local hosts are refused (fail-open ClientError). Also rebuilds the idle-thought system prompt variants with
the real InnerMonologueNode._build_system_prompt. Writes ONLY to --out (a scratchpad dir).

  python scripts/lab_J-2676_capture.py --out <dir> [--n 5]
"""
import argparse, asyncio, json, random, shutil, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402,F401  (BEFORE lab_env)
sys.path.insert(0, r"C:/Users/USER/.claude/skills/job-queue")
import aiohttp  # noqa: E402
from lab_env import isolate  # noqa: E402

REC: list = []
CUR = {"chain": None}
_orig_post = aiohttp.ClientSession.post


class _CM:
    def __init__(self, cm, url, payload):
        self.cm, self.url, self.payload = cm, url, payload
        self.t0 = time.monotonic()

    async def __aenter__(self):
        resp = await self.cm.__aenter__()
        orig_json = resp.json
        me = self

        async def _json(*a, **k):
            data = await orig_json(*a, **k)
            me.data = data
            return data
        resp.json = _json
        return resp

    async def __aexit__(self, *a):
        r = await self.cm.__aexit__(*a)
        d = getattr(self, "data", None) or {}
        REC.append({"chain": CUR["chain"], "seq": len(REC), "url": self.url, "payload": self.payload,
                    "wall": round(time.monotonic() - self.t0, 3),
                    "pe": d.get("prompt_eval_count"), "ped": d.get("prompt_eval_duration"),
                    "ec": d.get("eval_count"), "ed": d.get("eval_duration"),
                    "content": (d.get("message") or {}).get("content") if isinstance(d, dict) else None,
                    "ok": a[0] is None})
        return r


def _post(self, url, *a, **k):
    u = str(url)
    if not ("127.0.0.1" in u or "localhost" in u):
        raise aiohttp.ClientConnectionError("J-2676 lab: non-local host refused")
    return _CM(_orig_post(self, url, *a, **k), u, k.get("json"))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    from core.profile import activate_profile
    prof = Path(activate_profile("_J2676_lab"))
    from lab_human_cycle_paths import rebase_human_cycle_paths  # J-4353 / F-5105
    rebase_human_cycle_paths(prof)
    src = ROOT / "data" / "identity" / "axiom.json"
    (prof / "identity").mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, prof / "identity" / "axiom.json")
    from core.schema import CognitiveState
    from core.orchestrator import Orchestrator
    from core.memory.store import init_db
    import run_nascence
    try:
        from core import telemetry
        from lab_isolation import neutralize_telemetry
        neutralize_telemetry(out / "telemetry", telemetry)
    except Exception as e:
        print("neutralize_telemetry failed:", repr(e)[:100])

    rows = [json.loads(l) for l in open(ROOT / "data" / "founder_conversation_log.jsonl", encoding="utf-8") if l.strip()]
    pool = [r["human"] for r in rows[:-12] if isinstance(r.get("human"), str) and 40 < len(r["human"]) < 300]
    utter = random.Random(2676).sample(pool, a.n)
    json.dump(utter, open(out / "utterances.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    aiohttp.ClientSession.post = _post
    with isolate(db="empty") as lab:
        print("lab dir", lab)
        init_db()
        name, axiom = run_nascence.load_identity()
        state = CognitiveState(spirit_name=name, axiom=axiom)
        nodes = run_nascence.build_nodes()
        orch = Orchestrator(state=state, nodes=nodes)
        for i, u in enumerate(utter):
            CUR["chain"] = f"human{i}"
            t0 = time.monotonic()
            try:
                resp = await orch.run_cycle(u, input_type="human")
            except Exception as e:
                resp = "ERR " + repr(e)[:200]
            n = sum(1 for r in REC if r["chain"] == CUR["chain"])
            print(f"chain {i}: {time.monotonic()-t0:.1f}s wall, {n} posts, resp {str(resp)[:60]!r}")
        # idle system prompt variants, rebuilt by the real method
        CUR["chain"] = "idle_sys"
        try:
            from nodes.inner_monologue_node import InnerMonologueNode
            node = InnerMonologueNode()
            sysv = {}
            for wand in (False, True):
                for mid in (False, True):
                    try:
                        sysv[f"wand{int(wand)}_mid{int(mid)}"] = node._build_system_prompt(state, wand, mid_train=mid)
                    except Exception as e:
                        print("sysprompt fail", wand, mid, repr(e)[:150])
            json.dump(sysv, open(out / "idle_system_prompts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("idle system variants:", {k: len(v) for k, v in sysv.items()})
        except Exception as e:
            print("InnerMonologueNode build failed:", repr(e)[:300])
        try:
            await orch.stop_background()
        except Exception:
            pass
    aiohttp.ClientSession.post = _orig_post
    with open(out / "capture_posts.jsonl", "w", encoding="utf-8") as f:
        for r in REC:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    print("posts by chain/url:", Counter((r["chain"], r["url"].split("/api")[0].split("/v1")[0]) for r in REC))


asyncio.run(main())
