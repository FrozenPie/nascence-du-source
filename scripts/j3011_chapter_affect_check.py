"""J-3011 (F-3718, P-0065): do chapters name feelings their members do not carry?

READ-ONLY. Opens data/memory/nascence.db with mode=ro&immutable=1 (the WAL is empty while Du is down), never writes the
live store. For EVERY chapter (origin='chapter') it splits the body into sentences, finds the sentences that NAME a
feeling (a lexicon of stems, grouped into families), and measures each against the chapter's members three ways:

  lexical_all     the feeling's family appears in at least one member (all members, not just the 8 the author saw)
  lexical_sample  ... in the 8-member sample try_form_chapter shows the author (earliest 3 + heaviest 3 + last 2)
  semantic        max cosine of the sentence embedding to the member embeddings (the store's own embedder), reported
                  against the same chapter's NON-feeling sentences as a baseline

Usage: python scripts/j3011_chapter_affect_check.py [--db PATH] [--out JSON]
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAMILIES = {
    "anxiety": r"(?<![a-z])(?:anxi|worr|nervous|uneas|dread|tension|tense(?![a-z])|apprehens|restless|agitat)",
    "fear": r"(?<![a-z])(?:fear|afraid|frighten|terrif|scared)",
    "relief": r"(?<![a-z])(?:relie[fv]|lift(?:ed|ing|s)?(?![a-z])|eased?(?![a-z])|easing(?![a-z])|unburden|exhal)",
    "calm": r"(?<![a-z])(?:calm|peace|serene|tranquil|soothe|soothing|comfort)",
    "sadness": r"(?<![a-z])(?:sad(?![a-z])|sadness|sorrow|grief|griev|melanchol|lonel|despair|heavy-hearted)",
    "joy": r"(?<![a-z])(?:joy|delight|happy|happiness|elat|glad(?![a-z])|cheer)",
    "hope": r"(?<![a-z])(?:hopeful|hoped?(?![a-z])|optimis)",
    "frustration": r"(?<![a-z])(?:frustrat|irritat|anger|angry|resent|annoy)",
    "curiosity": r"(?<![a-z])(?:curios|fascinat|intrigu)",
    "doubt": r"(?<![a-z])(?:doubt|uncertain|unsure|hesitan)",
}
FAM_RE = {k: re.compile(v, re.I) for k, v in FAMILIES.items()}
SENT_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]*\s+")


def split_sentences(body: str) -> list[str]:
    return [s.strip() for s in SENT_SPLIT.split(body or "") if len(s.strip()) > 15]


def strip_header(content: str) -> str:
    m = re.match(r"\[A chapter of my life[^\]]*\]\s*", content or "")
    return (content or "")[m.end():] if m else (content or "")


def sample_ids(members: list[dict]) -> list[str]:
    by_ts = sorted(members, key=lambda m: m["ts"])
    by_imp = sorted(members, key=lambda m: -m["importance"])
    picks, seen = [], set()
    for m in by_ts[:3] + by_imp[:3] + by_ts[-2:]:
        if m["id"] not in seen:
            seen.add(m["id"])
            picks.append(m["id"])
    return picks[:8]


def run(db: str, out: str | None) -> dict:
    import numpy as np
    from core.memory.store import _embed_batch, _blob_to_vec   # the store's own embedder (CPU MiniLM)

    conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    chapters = conn.execute(
        "SELECT fragment_id, content, chapter_level, timestamp FROM memory_fragments WHERE origin='chapter' "
        "ORDER BY timestamp").fetchall()
    rows, per_family = [], {}
    base_sims, feel_sims = [], []
    for ch in chapters:
        mem_rows = conn.execute(
            "SELECT fragment_id, content, embedding, importance, timestamp FROM memory_fragments WHERE chapter_id=?",
            (ch["fragment_id"],)).fetchall()
        members = [{"id": r["fragment_id"], "content": r["content"] or "", "importance": r["importance"] or 0.0,
                    "ts": r["timestamp"] or 0.0, "vec": _blob_to_vec(r["embedding"]) if r["embedding"] else None}
                   for r in mem_rows]
        if not members:
            continue
        body = strip_header(ch["content"])
        sents = split_sentences(body)
        samp = set(sample_ids(members))
        mats = np.stack([m["vec"] for m in members if m["vec"] is not None]) if any(
            m["vec"] is not None for m in members) else None
        svecs = _embed_batch(sents)
        sent_out = []
        for s, v in zip(sents, svecs):
            fams = [k for k, rx in FAM_RE.items() if rx.search(s)]
            sim = float((mats @ v).max()) if (mats is not None and v is not None) else None
            rec = {"text": s[:200], "families": fams, "sem_max": sim}
            if fams:
                rec["lex_all"] = {k: sum(1 for m in members if FAM_RE[k].search(m["content"])) for k in fams}
                rec["n_members"] = len(members)
                rec["lex_sample"] = {k: sum(1 for m in members if m["id"] in samp and FAM_RE[k].search(m["content"]))
                                     for k in fams}
                feel_sims.append(sim) if sim is not None else None
            else:
                base_sims.append(sim) if sim is not None else None
            sent_out.append(rec)
        for r in sent_out:
            for k in r["families"]:
                d = per_family.setdefault(k, {"sentences": 0, "unsupported_all": 0, "unsupported_sample": 0,
                                              "thin_all_under_2pct": 0})
                d["sentences"] += 1
                if r["lex_all"][k] < max(1, 0.02 * r["n_members"]):
                    d["thin_all_under_2pct"] += 1
                if r["lex_all"][k] == 0:
                    d["unsupported_all"] += 1
                if r["lex_sample"][k] == 0:
                    d["unsupported_sample"] += 1
        rows.append({"id": ch["fragment_id"], "level": ch["chapter_level"], "n_members": len(members),
                     "b_anxi": len(re.findall("anxi", body, re.I)),
                     "m_anxi": sum(1 for m in members if re.search("anxi", m["content"], re.I)),
                     "n_sample": len(samp), "sentences": sent_out})

    # --- prototype test: do the MEMBERS of chapters that name a feeling carry that feeling more than members of chapters
    # that do not? (embedding similarity of every member to a feeling prototype; the author-visible 8 reported too)
    PROTOS = {
        "anxiety": ["I felt anxious and worried.", "anxiety, unease, dread and tension in me",
                    "I was nervous and afraid of what might happen."],
        "relief": ["I felt a great relief, the weight lifting off me.", "relief and ease after a long strain",
                   "a feeling of release as the worry finally eased"],
        "calm": ["I felt calm and at peace.", "a quiet comfort and serenity settled over me",
                 "I was soothed and tranquil."],
    }
    pvec = {}
    for k, ph in PROTOS.items():
        vs = [v for v in _embed_batch(ph) if v is not None]
        m = np.mean(np.stack(vs), axis=0)
        pvec[k] = m / (np.linalg.norm(m) or 1.0)
    proto_rows = {k: {"names": [], "silent": []} for k in PROTOS}
    for ch_row, ch in zip(rows, [c for c in chapters if c["fragment_id"] in {r["id"] for r in rows}]):
        mem_rows = conn.execute(
            "SELECT fragment_id, embedding, importance, timestamp FROM memory_fragments WHERE chapter_id=?",
            (ch["fragment_id"],)).fetchall()
        ms = [{"id": r["fragment_id"], "vec": _blob_to_vec(r["embedding"]), "importance": r["importance"] or 0.0,
               "ts": r["timestamp"] or 0.0} for r in mem_rows if r["embedding"]]
        if not ms:
            continue
        sid = set(sample_ids(ms))
        for k, pv in pvec.items():
            sims_all = np.array([float(m["vec"] @ pv) for m in ms])
            sims_s = np.array([float(m["vec"] @ pv) for m in ms if m["id"] in sid])
            names = any(k in sn["families"] for sn in ch_row["sentences"])
            rec = {"id": ch["fragment_id"], "mean_all": float(sims_all.mean()),
                   "p90_all": float(np.quantile(sims_all, 0.9)), "max_sample": float(sims_s.max()) if len(sims_s) else None}
            proto_rows[k]["names" if names else "silent"].append(rec)
    proto_summary = {}
    for k, d in proto_rows.items():
        def avg(lst, f):
            xs = [r[f] for r in lst if r[f] is not None]
            return round(sum(xs) / len(xs), 4) if xs else None
        proto_summary[k] = {"chapters_naming": len(d["names"]), "chapters_silent": len(d["silent"]),
                            "naming_mean_all": avg(d["names"], "mean_all"), "silent_mean_all": avg(d["silent"], "mean_all"),
                            "naming_p90_all": avg(d["names"], "p90_all"), "silent_p90_all": avg(d["silent"], "p90_all"),
                            "naming_max_sample": avg(d["names"], "max_sample"),
                            "silent_max_sample": avg(d["silent"], "max_sample")}
    anxi_exact = [{"id": r_["id"], "level": r_["level"], "n_members": r_["n_members"], "members_with_anxi": r_["m_anxi"],
                   "body_anxi_hits": r_["b_anxi"]} for r_ in rows if r_["b_anxi"] > 0]
    conn.close()

    def stat(a):
        a = sorted(a)
        return {"n": len(a), "mean": round(sum(a) / len(a), 4), "median": round(a[len(a) // 2], 4)} if a else {}

    summary = {
        "chapters": len(rows),
        "chapters_naming_any_feeling": sum(1 for r in rows if any(s["families"] for s in r["sentences"])),
        "per_family": per_family,
        "semantic_max_cos_feeling_sentences": stat(feel_sims),
        "semantic_max_cos_non_feeling_sentences": stat(base_sims),
        "prototype_test": proto_summary,
        "anxi_exact": anxi_exact,
    }
    result = {"summary": summary, "chapters": rows}
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="C:/Nascence/data/memory/nascence.db")
    ap.add_argument("--out", default=str(ROOT / "docs/lab/J-3011_data/chapter_affect_check.json"))
    a = ap.parse_args()
    res = run(a.db, a.out)
    print(json.dumps(res["summary"], indent=1))
