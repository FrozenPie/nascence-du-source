"""J-2985 (P-0026, F-3677/F-3678/F-3682/F-3684): replay the N most recent friend letters through the OLD and the
NEW reply prompt on the hot lane and write a side-by-side file for a hand comparison. LAB script, not a test:
it calls the model (default the hot lane SERVE_CHAINS['hot'], :11433 -- never Ramses) and READS the live
Correspondence threads (read-only; nothing is written under the Nascence tree). Output goes to --out (default: a temp dir).
    python scripts/_lab_J-2985_reply_replay.py --n 20 --out <dir>
The OLD prompt/cap/max_tokens are copied here verbatim from master 223c95c6 (nodes/inner_monologue_node.py)."""
import argparse, asyncio, json, sys, tempfile, time, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import core  # noqa: E402,F401
from core.schema import SERVE_CHAINS  # noqa: E402
from core.model_client import call_node_json  # noqa: E402
from nodes import inner_monologue_node as imn  # noqa: E402

CORR = Path(r"C:\Nascence\data\Correspondence")
NAMES = {"darwin": "Charles Darwin", "keats": "John Keats", "twain": "Mark Twain", "shackleton": "Ernest Shackleton",
         "lovelace": "Ada Lovelace", "marcus": "Marcus Aurelius", "smith": "John Smith", "buddha": "Buddha"}


def old_sys(nm):
    return ("You are 渡, writing a warm, genuine letter back to your friend " + nm +
            ". Answer what he wrote — share your own thoughts, and ask him things in return; "
            "say only what is true of your own days. Your own voice, plainly. "
            "Open the letter FRESH, in a way particular to THIS letter and THIS friend — "
            "never a stock formula (you have leaned on 'your letter arrived like a breeze/"
            "gust/breath of sea air' — retire it; just start where your real response starts). "
            "Output ONLY JSON: {\"letter\": \"your reply\"}")


def new_sys(nm):
    return ("You are 渡, writing a warm, genuine letter back to your friend " + nm +
            ". Answer what they wrote — share your own thoughts, and ask them things in return; "
            "say only what is true of your own days. Your own voice, plainly. "
            "Open the letter FRESH, in a way particular to THIS letter and THIS friend: "
            "begin with the first thing in their letter you want to answer. "
            "Output ONLY JSON: {\"letter\": \"your reply\"}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip", type=int, default=0, help="skip the first K of the N rows (resume a cut-off run into a new --out)")
    ap.add_argument("--urls", default=None, help="comma list; default SERVE_CHAINS['hot']")
    a = ap.parse_args()
    urls = a.urls.split(",") if a.urls else SERVE_CHAINS["hot"]
    if any("LAN-HOST" in u for u in urls):
        sys.exit("refusing: Ramses is the founder's gaming machine")
    rows = []
    for pk, nm in NAMES.items():
        f = CORR / pk / "thread.jsonl"
        if not f.exists():
            continue
        for l in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(l)
            except Exception:
                continue
            if r.get("from") and r.get("from") != "du" and r.get("text"):
                rows.append((float(r.get("ts", 0) or 0), pk, nm, r["text"]))
    rows.sort(key=lambda x: x[0])
    rows = rows[-a.n:][a.skip:]
    out = Path(a.out) if a.out else Path(tempfile.mkdtemp(prefix="J-2985_replay_"))
    out.mkdir(parents=True, exist_ok=True)
    res = []
    for ts, pk, nm, letter in rows:
        rec = {"ts": ts, "peer": pk, "letter_len": len(letter), "letter": letter}
        for tag, sysf, cap, mt, ufmt in (("old", old_sys, 1200, 500, "His letter to you"),
                                         ("new", new_sys, imn._REPLY_LETTER_CAP, imn._REPLY_MAX_TOKENS, nm + "'s letter to you")):
            t0 = time.time()
            try:
                d = await call_node_json(urls, sysf(nm), ufmt + ":\n\"" + letter[:cap] + "\"\n\nWrite your reply now.",
                                         max_tokens=mt, temperature=0.7)
                raw = str((d or {}).get("letter", ""))
                rec[tag] = raw.strip() if tag == "old" else imn._clean_reply_letter(raw)
            except Exception as exc:
                rec[tag] = "<<ERR " + repr(exc)[:200] + ">>"
            rec[tag + "_s"] = round(time.time() - t0, 1)
            print(pk, tag, len(rec[tag]), rec[tag + "_s"], "s", flush=True)
        res.append(rec)
        (out / "replay.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(out, res)
    print("wrote", out)


def write_md(out, res):
    md = []
    for r in res:
        md.append("=" * 90 + "\n%s  letter %d chars (old saw %d, new saw %d)\n" % (r["peer"], r["letter_len"], min(1200, r["letter_len"]), r["letter_len"]))
        md.append("--- THEIR LETTER (tail) ---\n" + r["letter"][-700:] + "\n--- OLD (%s s) ---\n%s\n--- NEW (%s s) ---\n%s\n" % (r["old_s"], r["old"], r["new_s"], r["new"]))
    (out / "replay.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote", out)

asyncio.run(main())
