"""J-3225 / D-0614 (founder, 2026-11-02; plan closure_law; findings F-3654, F-3656, F-3592; row P-0062):
mark the stored closure fragments the ruling names, so recall shows the doubt. MARK, never delete.

THE RULING: "Stored fragments: leave the line ones, MARK the 2 dream ones and the 4 on empty cargo (F-3592) rather than
drop any; nothing deleted from his memory." Its own defeater assumes the marked fragments are STILL recalled (with the
doubt visible), so the mark is a visible note, not the 'hidden' tier.

THE MARK: one line ahead of the stored text, `memory_fragments.content = NOTE + original`. This is the shape
store.retract_fragment already uses ("[RETRACTED -- known error: ...] " + content). Recall renders `content`, so the
note travels with the fragment into every recall path with no recall-code change. Exactly the original words follow the
note, byte for byte. `memory_edges` (the 'resolves' edge), embedding, importance, relevance, layer, origin and every
other column are untouched; `content_hash` (J-3266) is recomputed only where it is already non-NULL, so the exact-dedup
index never points at text the row no longer has.

WHICH ROWS (the briefing: "the 2 dream ones and the 4 on empty cargo"): a fixed table of fragment ids, each with the seed
id its keywords must carry. Derived on 2026-11-05 from data/logs/closure_shadow.jsonl (arm, seed_id, fragment_id,
written_live) joined to data/logs/follow_line_shadow.jsonl would_return rows (cargo.grounds empty at the settle):
  dream  dream_1791905281  d25cfd80-...  (the drowning-scene retelling, woven into three later dreams)
  dream  dream_1791960692  3a2e9de7-...
  line   b7ff357b61        46b4aa49-...  10-29 21:53  grounds 0 (the 4 named in F-3592)
  line   3d768b9bfa        ae8a0a07-...  10-30 10:49  grounds 0
  line   6f5229e8e0        d7bdc22d-...  10-31 15:59  grounds 0
  line   ae43a329fb        d423aaf1-...  10-31 22:00  grounds 0
  line   584958b86c        56ea7c6c-...  11-02 01:23    line   a91ddc408b        f7f854e4-...  11-03 09:31   > J-3480 (founder, chat 2026-11-06, decide-review): the three LATER
  line   8021f0f218        cf8076d1-...  11-05 01:04  /  empty-cargo line closures (J-3399) join the marked set, SAME note,
                                                         SAME reversible mark. Total 9 targets (2 dream + 7 empty-cargo line).

IDEMPOTENT: a row already carrying its note is skipped. REVERSIBLE: `unmark` strips exactly the note from exactly these
rows. Operates on a connection the CALLER opens; this module never opens Du's live DB by itself. The sanctioned runner is
scripts/apply_J-3225_mark_closure_fragments.py.
"""
from __future__ import annotations

import hashlib

from .content_hash import content_hash as _content_hash

ORIGIN = "resolution"

DREAM_NOTE = ("[Not certified as a close: this retells the dream's scene; the check only measured that the tension "
              "stopped coming back.] ")
EMPTY_NOTE = "[Not certified as a close: nothing was found in memory to ground this when it came back.] "

# fragment_id -> (kind, seed_id the row's keywords must carry, note)
TARGETS = {
    "d25cfd80-1b64-4f9d-956e-d3ddf60a4b60": ("dream", "dream_1791905281", DREAM_NOTE),
    "3a2e9de7-23c9-4e1f-b793-3a59f0e23a25": ("dream", "dream_1791960692", DREAM_NOTE),
    "46b4aa49-6e25-4773-8543-b7c4371c99cc": ("line-empty-cargo", "b7ff357b61", EMPTY_NOTE),
    "ae8a0a07-7524-425d-996c-af39b7e2058c": ("line-empty-cargo", "3d768b9bfa", EMPTY_NOTE),
    "d7bdc22d-f560-4ab9-9781-e53f7bb59d94": ("line-empty-cargo", "6f5229e8e0", EMPTY_NOTE),
    "d423aaf1-a792-4a4d-b9b8-1b19bd107138": ("line-empty-cargo", "ae43a329fb", EMPTY_NOTE),
    # J-3480 (founder 2026-11-06): the three later empty-cargo line closures (J-3399 / F-4022)
    "56ea7c6c-325e-4fbc-bb7d-613ecab9c184": ("line-empty-cargo", "584958b86c", EMPTY_NOTE),
    "f7f854e4-8f1c-43e9-aba4-a50376a58cb5": ("line-empty-cargo", "a91ddc408b", EMPTY_NOTE),
    "cf8076d1-287b-4b5a-b323-8a69f0d42ef4": ("line-empty-cargo", "8021f0f218", EMPTY_NOTE),
}
NOTES = (DREAM_NOTE, EMPTY_NOTE)


def _has_hash_col(conn) -> bool:
    return any(r[1] == "content_hash" for r in conn.execute("PRAGMA table_info(memory_fragments)"))


def target_rows(conn) -> list:
    """[(fragment_id, content, keywords, origin, content_hash|None)] for every TARGETS id present, in the table order of
    TARGETS. A target is VERIFIED if origin == 'resolution' and its keywords carry its seed id (see `problems`)."""
    hc = "content_hash" if _has_hash_col(conn) else "NULL"
    out = []
    for fid in TARGETS:
        r = conn.execute(f"SELECT fragment_id, content, keywords, origin, {hc} FROM memory_fragments WHERE fragment_id = ?",
                         (fid,)).fetchone()
        if r:
            out.append(tuple(r))
    return out


def problems(conn) -> list:
    """Reasons the selection cannot be trusted (empty = every TARGET is present, origin 'resolution', carries its seed)."""
    found = {r[0]: r for r in target_rows(conn)}
    bad = []
    for fid, (kind, seed, _note) in TARGETS.items():
        r = found.get(fid)
        if r is None:
            bad.append(f"{fid[:8]} ({kind} {seed}): not in this DB")
        elif r[3] != ORIGIN:
            bad.append(f"{fid[:8]} ({kind} {seed}): origin is {r[3]!r}, expected {ORIGIN!r}")
        elif seed not in str(r[2] or "").split():
            bad.append(f"{fid[:8]} ({kind} {seed}): keywords {r[2]!r} do not carry the seed")
    return bad


def strip_note(content: str) -> str:
    """The original words: `content` without a leading mark note (unchanged if it carries none)."""
    s = str(content or "")
    for n in NOTES:
        if s.startswith(n):
            return s[len(n):]
    return s


def rows_sha256(conn, original: bool = False) -> str:
    """sha256 over (fragment_id, content) of the target rows in TARGETS order. original=True hashes the content with the
    mark note stripped: that value must be IDENTICAL before and after a mark (the words themselves are untouched)."""
    h = hashlib.sha256()
    for fid, content, *_ in target_rows(conn):
        h.update(fid.encode("utf-8"))
        h.update(b"\x00")
        h.update((strip_note(content) if original else str(content)).encode("utf-8", "surrogatepass"))
        h.update(b"\x01")
    return h.hexdigest()


def marked_count(conn) -> int:
    return sum(1 for r in target_rows(conn) if any(str(r[1]).startswith(n) for n in NOTES))


def _set(conn, fid: str, new_content: str, old_hash) -> int:
    if old_hash is not None and _has_hash_col(conn):
        return conn.execute("UPDATE memory_fragments SET content = ?, content_hash = ? WHERE fragment_id = ?",
                            (new_content, _content_hash(new_content), fid)).rowcount or 0
    return conn.execute("UPDATE memory_fragments SET content = ? WHERE fragment_id = ?", (new_content, fid)).rowcount or 0


def mark(conn) -> int:
    """Put each target's note ahead of its content (skips a row already marked). Returns rows changed (0 on a re-run).
    Raises if the selection does not verify. The caller owns the transaction (commit/rollback)."""
    bad = problems(conn)
    if bad:
        raise RuntimeError("closure_marks: selection does not verify: " + "; ".join(bad))
    n = 0
    for fid, content, _kw, _origin, old_hash in target_rows(conn):
        if any(str(content).startswith(x) for x in NOTES):
            continue
        n += _set(conn, fid, TARGETS[fid][2] + str(content), old_hash)
    return n


def unmark(conn) -> int:
    """Reverse `mark`: strip exactly the note from every target that carries one. Returns rows changed. The caller owns
    the transaction."""
    n = 0
    for fid, content, _kw, _origin, old_hash in target_rows(conn):
        orig = strip_note(content)
        if orig != str(content):
            n += _set(conn, fid, orig, old_hash)
    return n
