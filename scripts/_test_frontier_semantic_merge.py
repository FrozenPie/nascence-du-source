"""Hermetic test for D-0486 / J-2428: frontier semantic dedupe (shadow/enforce) + scripts/merge_frontier_variants.py.
Everything runs on temp files (fr._F, fr._F_LIGHT, fr._SEM_SHADOW_LOG redirected); sha256 canaries on the LIVE
data/frontier.json and data/curiosity_log.jsonl (read only, never written) must be unchanged at the end.
`import core` stays BEFORE anything lab_env-ish. Uses the real CPU embedding model (cached locally).
Run: python scripts/_test_frontier_semantic_merge.py   (exit 0 = all pass)"""
import hashlib, json, os, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from core import frontier as fr, profile            # noqa: E402

LIVE = Path(r"C:\Nascence\data")
def sha(p):
    p = Path(p); return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
CAN = {n: sha(LIVE / n) for n in ("frontier.json", "curiosity_log.jsonl")}

FAILS = []
def check(label, cond):
    print(("  ok   " if cond else "  FAIL ") + label)
    if not cond: FAILS.append(label)

tmp = Path(tempfile.mkdtemp(prefix="frontier_sem_"))
def fresh():
    fr._F = tmp / "frontier.json"; fr._F_LIGHT = tmp / "frontier.light.json"
    fr._SEM_SHADOW_LOG = tmp / "logs" / "shadow.jsonl"
    for p in (fr._F, fr._F_LIGHT, fr._SEM_SHADOW_LOG): p.unlink(missing_ok=True)
    fr._SEM_VEC_CACHE.clear()
def shadow_rows():
    return [json.loads(l) for l in fr._SEM_SHADOW_LOG.read_text(encoding="utf-8").splitlines()] if fr._SEM_SHADOW_LOG.exists() else []
def store(): return json.loads(fr._F.read_text(encoding="utf-8"))["questions"]

A = "How does 'mottainai' influence Japanese attitudes towards waste and resource conservation?"
B = "How does the 'mottainai' concept impact the Japanese attitude towards waste and resource management?"
C = "Why do granite coatings form on desert rock surfaces over thousands of years?"

# J-4052: D-0495 (2026-10-28) flipped the default from "shadow" to "enforce" (live); section [2] below now sets "shadow"
# explicitly so it still pins the shadow arm's behaviour.
print("[1] defaults"); check("default mode is enforce (D-0495)", fr.FRONTIER_SEMANTIC_MERGE == "enforce")
check("threshold 0.85", fr.SEMANTIC_MERGE_THRESHOLD == 0.85)

print("[2] shadow: logs would-merge, changes nothing live"); fresh(); fr.FRONTIER_SEMANTIC_MERGE = "shadow"
fr.note_question(A, "curiosity"); fr.note_question(C, "curiosity")
n0 = len(store()); fr.note_question(B, "curiosity")
qs = store()
check("paraphrase still becomes its own entry (live behaviour unchanged)", len(qs) == n0 + 1)
check("no entry carries variants", not any("variants" in q for q in qs))
rows = shadow_rows()
check("exactly one shadow row", len(rows) == 1)
check("row names the matched entry + sim >= threshold", rows and rows[0]["matched_q"] == A and rows[0]["sim"] >= 0.85 and rows[0]["mode"] == "shadow")
check("unrelated question produced no shadow row", all(r["new"] != C for r in rows))
check("matched entry's encounters untouched", [q for q in qs if q["q"] == A][0]["encounters"] == 1)

print("[3] off: no log, plain behaviour"); fresh(); fr.FRONTIER_SEMANTIC_MERGE = None
fr.note_question(A, "curiosity"); fr.note_question(B, "curiosity")
check("two entries, no shadow file", len(store()) == 2 and not fr._SEM_SHADOW_LOG.exists())

print("[4] enforce: merges, keeps lineage, never deletes"); fresh(); fr.FRONTIER_SEMANTIC_MERGE = "enforce"
fr.note_question(A, "curiosity"); t0 = time.time(); ok = fr.note_question(B, "reading")
qs = store()
check("returns True and keeps ONE entry", ok is True and len(qs) == 1)
check("encounters bumped to 2, last_seen refreshed", qs[0]["encounters"] == 2 and qs[0]["last_seen"] >= t0)
check("variant text kept as lineage", qs[0]["variants"][0]["q"] == B[:220].rstrip(".") and qs[0]["variants"][0]["source"] == "reading")
check("original text untouched", qs[0]["q"] == A.rstrip("."))
fr.note_question(C, "curiosity"); check("unrelated question still born separately", len(store()) == 2)

print("[5] fail-open on embedding trouble"); fresh(); fr.FRONTIER_SEMANTIC_MERGE = "enforce"
orig = fr._sem_vecs
def boom(_): raise RuntimeError("embedder down")
fr._sem_vecs = boom
fr.note_question(A, "curiosity"); r = fr.note_question(B, "curiosity")
check("question still recorded when embedder raises", r is True and len(store()) == 2)
fr._sem_vecs = orig

print("[6] token-overlap path unchanged; merged entries skipped"); fresh(); fr.FRONTIER_SEMANTIC_MERGE = None
fr.note_question(A, "curiosity"); fr.note_question(A, "curiosity")
check("exact repeat bumps encounters", len(store()) == 1 and store()[0]["encounters"] == 2)
d = json.loads(fr._F.read_text(encoding="utf-8")); d["questions"][0]["status"] = "merged"
fr._F.write_text(json.dumps(d), encoding="utf-8"); fr.note_question(A, "curiosity")
check("a 'merged' entry is not revived/refreshed", store()[0]["status"] == "merged" and len(store()) == 2)

print("[7] merge script: dry-run default, --apply on a temp copy")
sys.path.insert(0, str(Path(__file__).parent)); import merge_frontier_variants as mv
fresh(); fr.FRONTIER_SEMANTIC_MERGE = None
now = time.time()
mk = lambda i, q, enc, st="open": {"id": i, "q": q, "source": "curiosity", "toks": [], "born": now - 100 + int(i[1:]), "last_seen": now - 50,
     "last_offered": 0.0, "offers": 0, "encounters": enc, "status": st}
qs = [mk("m1", A, 3), mk("m2", B, 5), mk("m3", "What is the mottainai idea of gratitude for objects?", 2), mk("m4", "mottainai old one", 4, "faded"), mk("g1", C, 1)]
qs[2]["finding"] = "F"; qs[2]["finding_title"] = "T"; qs[2]["finding_ts"] = 1.0
fp = tmp / "copy.json"; fp.write_text(json.dumps({"questions": qs}), encoding="utf-8"); h0 = sha(fp)
check("dry run exits 0", mv.main(["--file", str(fp)]) == 0)
check("dry run wrote nothing", sha(fp) == h0 and not list(tmp.glob("copy.json.premerge*")))
check("apply exits 0", mv.main(["--file", str(fp), "--apply"]) == 0)
baks = list(tmp.glob("copy.json.premerge*.bak"))
check("backup written and identical to the original", len(baks) == 1 and sha(baks[0]) == h0)
out = {q["id"]: q for q in json.loads(fp.read_text(encoding="utf-8"))["questions"]}
check("canonical = highest encounters (m2), summed 5+3+2", out["m2"]["encounters"] == 10 and out["m2"]["status"] == "open")
check("absorbed kept in file as merged -> m2", all(out[i]["status"] == "merged" and out[i]["merged_into"] == "m2" for i in ("m1", "m3")))
check("variants lineage lists both texts", sorted(v["id"] for v in out["m2"]["variants"]) == ["m1", "m3"])
check("finding carried to canonical", out["m2"].get("finding") == "F")
check("faded + non-term entries untouched", out["m4"]["status"] == "faded" and out["g1"]["status"] == "open" and len(out) == 5)

print("[8] canaries: live stores untouched")
for n, h in CAN.items(): check(f"data/{n} hash unchanged", sha(LIVE / n) == h)

print("\nFAILED: %d" % len(FAILS) if FAILS else "\nALL PASS"); sys.exit(1 if FAILS else 0)
