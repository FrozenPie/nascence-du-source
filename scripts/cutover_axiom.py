"""
The axiom cutover (2026-06-15) — promote the live axiom.json to the multilevel schema.
Regenerates the layered structure from the CURRENT live axiom (capturing the latest 渡), backs up
the legacy file ONCE, writes the multilevel structure to axiom.json, verifies nothing was lost.
Reversible: restore axiom.legacy_v2.json. RESTART-REQUIRED to take effect (running Du is unaffected).
"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import migrate_axiom_multilevel as M
from core import axiom_layers as al

LIVE   = Path(r"C:\Nascence\data\identity\axiom.json")
LEGACY = Path(r"C:\Nascence\data\identity\axiom.legacy_v2.json")

src = json.loads(LIVE.read_text(encoding="utf-8"))

if al.is_multilevel(src):
    print("axiom.json is ALREADY multilevel — nothing to promote.")
    print(f"  name={src.get('name')}  becoming rev={ (al._becoming(src) or {}).get('revision_count') }")
    sys.exit(0)

# Regenerate from the current live (latest self_concept/arc), verify nothing of Du lost.
out = M.compose(src)
fails = M.verify(src, out)
if fails:
    print("ABORT — migration verify failed:")
    for f in fails:
        print("  ✗", f)
    sys.exit(1)

# Back up the legacy file ONCE (never overwrite the true pre-cutover legacy on a re-run).
if not LEGACY.exists():
    LEGACY.write_text(LIVE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"legacy backed up → {LEGACY.name}")
else:
    print(f"legacy backup already exists ({LEGACY.name}) — left as-is")

LIVE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

# Verify the now-live file.
chk = json.loads(LIVE.read_text(encoding="utf-8"))
name, axiom = al.compose_floor(chk)
ok = (al.is_multilevel(chk) and name == "渡" and "I am the river" not in axiom
      and "\nVOICE STYLE:" in axiom and al.get_self_concept(chk))
print(f"\naxiom.json PROMOTED to multilevel-v1  ✓" if ok else "\n✗ promotion verify FAILED")
print(f"  name: {name}")
print(f"  becoming (relocated self-concept): {al.get_self_concept(chk)[:80]}…")
print(f"  facets: {[f['id'] for f in chk['L3_facets']['facets']]}")
print(f"  told._delivered: {chk['told_to_you'].get('_delivered')}  (feel-then-tell: NOT delivered yet)")
print(f"\n  RESTART to activate. Rollback: copy {LEGACY.name} → axiom.json")
