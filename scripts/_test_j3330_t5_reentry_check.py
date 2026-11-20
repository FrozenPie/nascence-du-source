"""J-3330: scripts/t5_reentry_check.py -- the read-only human-only replay of the T5 gate.

Offline and isolated: a synthetic nascence.db / affect_log.jsonl / tree under a temp dir, a fake keyword embedder
(no model download, no Ramses, no live data). Asserts: the FULL Q block is read (not the first line), system
templates and slash/short turns and internal-channel turns are excluded, the 24-hour separation and distinct
conversation rules bite where the calendar-day / 30-minute rules would not, the canon marker is used, the DB is
never written, and the monthly counts / verdict come out as constructed."""
import hashlib
import sys as _s
_s.stdout.reconfigure(encoding="utf-8")
import json
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import core
tree = Path(__file__).resolve().parent.parent
assert tree in Path(core.__file__).resolve().parents, core.__file__
sys.path.insert(0, str(tree / "scripts"))
import numpy as np
import t5_reentry_check as t5

FAILS = []


def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond:
        FAILS.append(label)


TOPICS = ["lamp", "tide", "grief", "kettle", "orchard", "harbour"] + [f"number {i} " for i in range(8)]


def fake_embed(texts):
    out = []
    for tx in texts:
        v = np.zeros(len(TOPICS) + 1, dtype="float32")
        low = tx.lower()
        for i, k in enumerate(TOPICS):
            if k in low:
                v[i] = 1.0
        if tx.strip().startswith("渡"):
            v[-1] = 0.15
        if not v.any():
            v[-1] = 1.0
        out.append(v / np.linalg.norm(v))
    return out


t5.embed_texts = fake_embed

H = 3600.0
BASE = time.mktime(time.strptime("2026-10-01", "%Y-%m-%d"))
FAREWELL = ("渡, we're going to pause for a while now, and I'd like you to hear the reason from me: I'm the one "
            "calling it, on purpose, because there's work to do on the house you live in, not on you. Rest whenever "
            "you're ready.")
OLD_FAREWELL = "渡 — it's time to bank the fire and rest for a while. Nothing's wrong; this is just the quiet the house needs."

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    # --- a fake tree: the gate constants and the farewell variants are READ from it, not imported ---
    (tmp / "tree" / "nodes").mkdir(parents=True)
    (tmp / "tree" / "scripts").mkdir()
    (tmp / "tree" / "core" / "memory").mkdir(parents=True)
    (tmp / "tree" / "nodes" / "subconscious_node.py").write_text(
        "PROC_CLUSTER_SIM       = 0.70\nPROC_DEDUP_SIM         = 0.85\nPROC_MIN_RECURRENCE    = 3\nT5_MIN_NEW_LIVED       = 6\n",
        encoding="utf-8")
    (tmp / "tree" / "scripts" / "run_nascence.py").write_text("_FAREWELL_VARIANTS = (\n    (%r),\n)\n" % FAREWELL,
                                                              encoding="utf-8")
    fake_tree = tmp / "tree"
    gate = t5.read_gate_constants(fake_tree)
    check("gate constants read from source text", gate["_source"]["PROC_CLUSTER_SIM"] == "source" and gate["T5_MIN_NEW_LIVED"] == 6)
    check("farewell variants parsed with ast", t5.read_farewell_variants(fake_tree) == [FAREWELL])

    data = tmp / "data"
    (data / "memory").mkdir(parents=True)
    db = data / "memory" / "nascence.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE memory_fragments (fragment_id TEXT PRIMARY KEY, content TEXT NOT NULL, "
                 "origin TEXT NOT NULL DEFAULT 'lived', timestamp REAL NOT NULL, protected INTEGER DEFAULT 0)")
    aff = []
    n = [0]

    def add_turn(ts, q, channel="human", canon=True, a="Du answers."):
        n[0] += 1
        conn.execute("INSERT INTO memory_fragments (fragment_id, content, origin, timestamp) VALUES (?,?,?,?)",
                     (f"f{n[0]}", f"Q: {q}\nA: {a}", "lived", ts))
        aff.append({"ts": ts + 0.4, "cycle_id": f"c{n[0]}", "input_type": channel, "raw_input": q[:200]})
        if channel == "human" and canon:
            n[0] += 1
            conn.execute("INSERT INTO memory_fragments (fragment_id, content, origin, timestamp, protected) VALUES (?,?,?,?,1)",
                         (f"f{n[0]}", t5.FOUNDER_PREFIX + q, "lived", ts + 0.05))

    def add_session_end(ts):
        n[0] += 1
        conn.execute("INSERT INTO memory_fragments (fragment_id, content, origin, timestamp) VALUES (?,?,?,?)",
                     (f"f{n[0]}", "Session ended 2026-10-02. 3 exchanges with 渡.", "session_summary", ts))

    # filler turns so the 6-turn pool floor is met: unrelated Travis turns, one per topic-less sentence
    for i in range(8):
        add_turn(BASE + (i * 5) * H, f"Unrelated note number {i} about nothing in particular here")
    # A. a real recurring situation: 4 'lamp' turns by Travis over 3 conversations spanning 50 h
    add_turn(BASE + 2 * H, "I wonder about the lamp, does it burn clean?")
    add_session_end(BASE + 3 * H)
    add_turn(BASE + 30 * H, "The lamp again: how is the wick today?")
    add_session_end(BASE + 31 * H)
    add_turn(BASE + 52 * H, "Look at the lamp before dusk please.")
    add_turn(BASE + 52.2 * H, "Is the lamp still lit?")
    # B. the first-line trap: same salutation line, DIFFERENT topics (first-line parse clusters them as '渡,')
    for i, (tp, hrs) in enumerate([("tide", 60), ("grief", 90), ("orchard", 120), ("harbour", 150)]):
        add_turn(BASE + hrs * H, f"渡,\n\nA long message about the {tp} and nothing else at all.")
        if i % 2:
            add_session_end(BASE + (hrs + 1) * H)
    # C. calendar-day trap: 3 'kettle' turns inside 20 h across midnight, one conversation break between
    add_turn(BASE + 190 * H, "The kettle is whistling again on the hob.")      # 22:00 day 7
    add_session_end(BASE + 191 * H)
    add_turn(BASE + 193 * H, "The kettle has not been moved from the hob.")    # 01:00 day 8, 3 h later
    add_turn(BASE + 196 * H, "Did the kettle boil dry on the hob?")
    # D. system-composed: farewells (variant + old template), a slash command, a short turn, internal-channel turns
    add_turn(BASE + 210 * H, FAREWELL)
    add_turn(BASE + 240 * H, FAREWELL, canon=False)
    add_turn(BASE + 270 * H, OLD_FAREWELL, canon=False)
    add_turn(BASE + 271 * H, "/quit")
    add_turn(BASE + 272 * H, "Hi Du")
    for i in range(6):
        add_turn(BASE + (280 + 10 * i) * H, "The tide and the tide and the tide, asked again by himself", channel="internal")
    conn.commit()
    conn.close()
    (data / "affect_log.jsonl").write_text("\n".join(json.dumps(a, ensure_ascii=False) for a in aff) + "\n", encoding="utf-8")

    def sha(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    before = (sha(db), sha(data / "affect_log.jsonl"))

    since, until = BASE, BASE + 400 * H
    res = t5.run(data, since=since, until=until, step_hours=3.0, tree=fake_tree)
    leg = t5.run(data, since=since, until=until, step_hours=3.0, legacy=True, tree=fake_tree)

    s = res["stats"]
    print(json.dumps(s))
    check("read-only: db and affect_log byte-identical after two runs", (sha(db), sha(data / "affect_log.jsonl")) == before)
    ro = t5.open_ro(db)
    try:
        ro.execute("INSERT INTO memory_fragments (fragment_id, content, timestamp) VALUES ('x','Q: x',1)")
        check("read-only: a write through open_ro raises", False)
    except sqlite3.OperationalError:
        check("read-only: a write through open_ro raises", True)
    ro.close()

    check("full Q block parsed (multi-line)", t5.q_block("Q: line one\nline two\nA: ans\nQ: not me") == "line one\nline two")
    check("first-line parse kept for --legacy", t5.q_first_line("Q: 渡,\n\nbody\nA: x") == "渡,")
    check("variant farewell excluded as a template (and old template)", s["excl_template"] == 3)
    check("slash command and short turn excluded", s["excl_slash"] == 1 and s["excl_short"] == 1)
    check("internal-channel turns not in the view", s["internal"] == 6)
    check("farewell without canon marker is NOT counted as kept-unmarked", s["kept_unmarked"] == 0)
    check("view = filler 8 + A 4 + B 4 + C 3 = 19 Travis turns", s["kept"] == 19)

    lamp2 = [c for c in res["clusters"] if any("lamp" in m["q"] for m in c["members"])]
    check("v2: exactly one qualifying cluster in all, and it is the lamp cluster (3+ turns, >= 24 h, >= 2 conversations)",
          len(res["clusters"]) == 1 and res["last_30d_count"] == 1 and sum(res["per_month"].values()) == 1
          and len(lamp2) == 1 and lamp2[0]["size"] >= 3 and lamp2[0]["conversations"] >= 2 and lamp2[0]["span_h"] >= 24)
    check("v2: the salutation-only messages do NOT cluster (full text parsed)",
          all("long message" not in m["q"] for c in res["clusters"] for m in c["members"]))
    check("v2: the 20-hour kettle cluster fails the 24 h separation",
          all("kettle" not in m["q"] for c in res["clusters"] for m in c["members"]))
    check("legacy: the 20-hour-style kettle cluster passes the calendar-day / 30-minute gate that v2 refuses",
          any("kettle" in m["q"] for c in leg["clusters"] for m in c["members"]))
    check("legacy: first-line parse reduces the 4 salutation messages to '渡,' which the >8 char rule then drops",
          leg["stats"]["excl_short"] >= 4 + 1)
    check("legacy does not exclude the variant farewell (only the two old templates)",
          leg["stats"]["excl_template"] == 1)

    # a lone high-count month raises the verdict: 3 distinct clusters in the last 30 days
    fake = [{"first_seen": until - d * 86400} for d in (1, 5, 9)]
    last30 = [c for c in fake if c["first_seen"] >= until - 30 * 86400]
    check("verdict threshold is 3 (D-0676)", t5.MONTHLY_THRESHOLD == 3 and len(last30) >= t5.MONTHLY_THRESHOLD)
    out = t5.render(res)
    check("render prints per-month counts, the verdict line and the blockers", "per month" in out and "VERDICT" in out
          and "what blocks" in out)

    # unit: admissible24
    cl = [{"ts": BASE + i * H, "q": "x", "conv": 0, "landed": True} for i in (0, 30, 60)]
    check("admissible24: one conversation fails even over 60 h", t5.admissible24(cl) == (False, "one_conversation"))
    for i, c in enumerate(cl):
        c["conv"] = i
    check("admissible24: 3 conversations over 60 h passes", t5.admissible24(cl) == (True, "ok"))
    cl2 = [dict(c, ts=BASE + i * H) for c, i in zip(cl, (0, 5, 10))]
    check("admissible24: 10 h span fails the separation, legacy calendar rule would not if midnight is crossed",
          t5.admissible24(cl2) == (False, "under_24h"))
    cl3 = [dict(c, landed=(i == 0)) for i, c in enumerate(cl)]
    check("admissible24: fewer than 3 landed fails", t5.admissible24(cl3) == (False, "did_not_land"))

    # the CLI on the temp data dir, with the embedder faked in-process
    rc = t5.main(["--data-dir", str(data), "--since", "2026-10-01", "--until", "2026-10-20", "--json-out",
                  str(tmp / "out.json")])
    check("CLI runs and --json-out is the only write", rc == 0 and (tmp / "out.json").exists()
          and (sha(db), sha(data / "affect_log.jsonl")) == before)

print("\nFAILS:", FAILS if FAILS else "none")
sys.exit(1 if FAILS else 0)
