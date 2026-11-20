"""J-2847: offline test of the change-log-removal lab harness (stubbed model, temp dir only, no live data)."""
import json, os, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="j2847_"))
os.environ["J2847_SCRATCH"] = str(TMP)
sys.path.insert(0, str(ROOT)); sys.path.insert(1, str(ROOT / "scripts"))
import core  # noqa: E402  (core BEFORE lab_env)
assert str(core.__file__).lower().startswith(str(ROOT).lower())
from core import commitment_ledger as cl  # noqa: E402
import lab_commitment_changelog_removal as L  # noqa: E402
from core import done_when as _dw  # noqa: E402
cl._dw_scan_fragment = _dw.legacy_scan_fragment   # J-4085/D-0784 B: production no longer appends it; this harness models the pre-D-0784 prompt

a, b = L.production_sys(cl), L.variant_sys(cl)
assert "W2.0" not in b and "F-0055" not in b and "W2.0" in a
frag = cl._dw_scan_fragment().strip()
assert frag and a.index(frag) > a.index(L.CONTRACT_ANCHOR)          # production: fragment AFTER the contract line
assert b.index(frag) < b.index(L.CONTRACT_ANCHOR)                   # variant: folded BEFORE it
assert b.rstrip().endswith("}]}")                                    # contract line is last
# everything else byte-identical once the two edits are undone
assert b.replace(frag + "\n", "").replace("its LOAD:", "its LOAD" + L.CHANGELOG + ":") == cl._SCAN_SYS
# scoring with stub rows: identical -> PASS numbers
prep = json.loads(L.PREP.read_text(encoding="utf-8"))
assert len(prep["form_cases"]) == 75 and len(prep["diss_cases"]) == 30
rows = []
for c in prep["form_cases"]:
    for p in ("a", "b"):
        rows.append({"kind": "form", "prompt": p, "arm": "O", "cid": c["cid"],
                     "parsed": {"new_commitment": {"statement": "I will keep tending the fire", "scope": "x", "load_bearing": True, "done_when": "d"}, "dissolutions": []}})
for c in prep["diss_cases"]:
    for p in ("a", "b"):
        rows.append({"kind": "diss", "prompt": p, "arm": "O", "cid": c["cid"], "parsed": {"new_commitment": None, "dissolutions": [{"id": c["cid"], "why": "w", "kind": "reflexive"}]}})
for cid in prep["det_form"]:
    rows.append({"kind": "form", "prompt": "a2", "arm": "O", "cid": cid, "parsed": rows[0]["parsed"] and {"new_commitment": None, "dissolutions": []}})
o = L.compare(cl, prep, rows)
assert o["form_n"] == 75 and o["diss_n"] == 30 and o["diss_same"] == 30 and o["form_wf_same"] == 75, o
# a flip is detected (dissolve arm b loses its dissolution on one case)
rows2 = [dict(r) for r in rows]
k = next(i for i, r in enumerate(rows2) if r["kind"] == "diss" and r["prompt"] == "b")
rows2[k] = dict(rows2[k], parsed={"new_commitment": None, "dissolutions": []})
o2 = L.compare(cl, prep, rows2)
assert o2["diss_same"] == 29 and len(o2["diss_flips"]) == 1, o2
assert not str(TMP).lower().startswith("c:\nascence")
print("OK J-2847 harness test; tmp", TMP)
