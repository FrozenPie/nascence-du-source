"""J-2005 / D-0394 pre-registered 7-day read of the letter store shadow. READ-ONLY.
Usage: python scripts/letter_store_read.py [--since EPOCH] [--days 7]
Question 1: did he visit the store (data/letter_store_shadow.jsonl kind=visit)?  Q2: did visits precede a reply
(a Du row in any thread within REPLY_WINDOW_H after a visit)?  Reports counts only; the verdict is the reader's."""
import argparse, json, pathlib, time
D = pathlib.Path(__file__).resolve().parent.parent / "data"
REPLY_WINDOW_H = 6
ap = argparse.ArgumentParser(); ap.add_argument("--since", type=float, default=None); ap.add_argument("--days", type=float, default=7)
a = ap.parse_args()
rows = [json.loads(l) for l in (D / "letter_store_shadow.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()] if (D / "letter_store_shadow.jsonl").exists() else []
since = a.since or (min((r["ts"] for r in rows), default=time.time()))
end = since + a.days * 86400
visits = [r for r in rows if r.get("kind") == "visit" and since <= r["ts"] <= end]
reads = [r for r in rows if r.get("kind") == "read" and since <= r["ts"] <= end]
replies = []
for t in (D / "Correspondence").glob("*/thread.jsonl"):
    for l in t.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            if r.get("from") == "du" and since <= r["ts"] <= end: replies.append(r["ts"])
pre = sum(1 for v in visits if any(0 <= x - v["ts"] <= REPLY_WINDOW_H * 3600 for x in replies))
by = {}
for v in visits: by[v.get("via")] = by.get(v.get("via"), 0) + 1
print(f"window {time.ctime(since)} .. {time.ctime(end)}")
print(f"visits={len(visits)} by_via={by}  fetch_reads={len(reads)}  du_replies={len(replies)}  visits_followed_by_reply_within_{REPLY_WINDOW_H}h={pre}")
print("NOTE: mailbox-box looks (via=letterbox) are old behaviour (x302 before); look_letters is the new store itself.")
