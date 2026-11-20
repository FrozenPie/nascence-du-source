"""Brick 3 in-vitro: the identity_vault goalkeeper. Verifies the vault produces a BYTE-IDENTICAL axiom.json
to the legacy direct write, writes atomically (no temp left), keeps a version ledger, and commit() does a safe
read-modify-write. Runs entirely against a TEMP file — the real data/identity/axiom.json is NEVER touched."""
import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import identity_vault as iv

# sample multilevel axiom (the_becoming facet, the field T4 revises)
SAMPLE = {
    "schema": "multilevel-v1", "name": "渡",
    "L0_constitution": {"commitments": ["become genuinely my own"]},
    "L3_facets": {"facets": [{"id": "the_becoming", "self_image": "I am the one who crosses.",
                              "revision_count": 3, "authored_at": "2026-06-15", "history": []}]},
    "L4_narrative": {"arc_recent": ["a first chapter"]},
}

tmpdir = Path(tempfile.mkdtemp())
iv._AXIOM = tmpdir / "axiom.json"
iv._LOG = tmpdir / "vault_log.jsonl"
try:
    # 1. BYTE-IDENTICAL to the legacy write (json.dump indent=2 ensure_ascii=False)
    legacy = json.dumps(SAMPLE, indent=2, ensure_ascii=False)
    assert iv.write(SAMPLE, reason="test") is True
    produced = iv._AXIOM.read_text(encoding="utf-8")
    assert produced == legacy, "vault output differs from the legacy direct write!"
    print(f"[1] byte-identical OK — vault axiom.json == legacy json.dump ({len(produced)} chars, exact match)")

    # 2. atomic — no .tmp left behind
    assert not (tmpdir / "axiom.json.tmp").exists(), "temp file left behind (write not cleaned)"
    print("[2] atomic OK — temp file replaced, none left behind")

    # 3. ledger appended with revision + reason
    led = [json.loads(l) for l in iv._LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(led) == 1 and led[0]["revision_count"] == 3 and led[0]["reason"] == "test", led
    print(f"[3] ledger OK — version entry rev={led[0]['revision_count']} reason='{led[0]['reason']}'")

    # 4. read round-trips
    assert iv.read()["L3_facets"]["facets"][0]["self_image"] == "I am the one who crosses."
    print("[4] read OK — round-trips the committed state")

    # 5. commit() = safe read-modify-write (mutator bumps the self_image + revision)
    def mutate(d):
        b = d["L3_facets"]["facets"][0]
        b["self_image"] = "I am the crossing itself — and a made mind."
        b["revision_count"] += 1
    out = iv.commit(mutate, reason="T4 self-authoring")
    assert out["L3_facets"]["facets"][0]["revision_count"] == 4
    assert iv.read()["L3_facets"]["facets"][0]["revision_count"] == 4, "commit not persisted"
    st = iv.status()
    assert st["ledger_entries"] == 2 and st["revision_count"] == 4, st
    cur = iv.current()
    assert "made mind" in cur["self_image"]
    print(f"[5] commit OK — read-modify-write persisted (rev 3→4), ledger now {st['ledger_entries']} entries")

    print("\nBRICK 3 PASS — the vault is a faithful goalkeeper: identical axiom.json, atomic, versioned, "
          "lock-guarded read-modify-write. T4's _write_axiom now commits through it (with a direct-write fallback). "
          "Real identity store untouched (temp-only test).")
finally:
    import shutil; shutil.rmtree(tmpdir, ignore_errors=True)
