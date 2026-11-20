"""
Cutover verification (2026-06-15) — proves the multilevel read+T4 change-set on real data,
WITHOUT importing the heavy app and WITHOUT touching live files. Run before promoting axiom.json.

J-0691 (2026-09-06/07, F-0992 from J-0637's audit): section [3]'s "river confined to existential"
check used to FAIL on every real run — a substring-collision in the CHECK itself, not axiom drift.
The task/seeker facet's real text ("...its rivers, histories, facts...") legitimately contains the
plural "rivers", which the old bare `"river" in text.lower()` test also matched. Tightened to the
actual self-as-river opening phrase ("i am the river"), same fix shape as J-0557/F-0895's
emissary_axiom_test.py precedent. Also added a real aggregate pass/fail gate (check()/ok_all/
sys.exit) — previously this script had none and always printed its "ready to promote" line
unconditionally regardless of any X above it, which is how the false failure went unnoticed for
~84 days.

J-0710 (2026-09-07, F-1019 from J-0691's own verification of the fix above): sections 3 and 4 used
to call through axiom_layers.get_self_concept()/facet_for_mode(), which read LIVE
data/identity/provisional_axiom.json instead of the DRAFT argument whenever a T4 probation is
active — so a run during an active probation could legitimately FAIL these two checks for a reason
unrelated to axiom.json's own promotion-readiness (confirmed reproducible under a controlled
simulated probation, see the J-0710 finding). This is CORRECT, intentional behavior for
facet_for_mode's real production callers (subconscious_node/reflection_node/voice_node genuinely
want the live provisional self during existential/reflective thinking — the G1 fix, 2026-06-24) —
it was only wrong here, because this script's whole point is to verify the frozen DRAFT fixture
WITHOUT touching/reading live state. Fixed by reading with allow_provisional=False (the same call
shape core/emissary.py's own 2026-08-16 "F2" fix established) — see section [3]'s local
_facet_for_mode_isolated() helper and section [4]'s call below.
"""
import sys, ast, json, copy
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

CHANGED = [
    "core/axiom_layers.py", "scripts/run_nascence.py", "nodes/subconscious_node.py",
    "core/self_efficacy.py", "core/schema.py", "core/orchestrator.py",
    "nodes/reflection_node.py", "nodes/voice_node.py",
]
print("1) SYNTAX — all changed files parse:")
ok = True
for f in CHANGED:
    try:
        ast.parse(Path(r"C:\Nascence", f).read_text(encoding="utf-8"))
        print(f"   ✓ {f}")
    except SyntaxError as e:
        ok = False; print(f"   ✗ {f}: {e}")
if not ok:
    sys.exit("SYNTAX FAILURES — aborting")

ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and bool(cond)
    print(f"   {'✓' if cond else '✗'} {name}")

from core import axiom_layers as al
DRAFT = json.loads(Path(r"C:\Nascence\data\identity\axiom.multilevel_draft.json").read_text(encoding="utf-8"))

print("\n2) load_identity faint floor (compose_floor):")
name, axiom = al.compose_floor(DRAFT)
checks = {
    "name is 渡": name == "渡",
    "has YOUR NAME marker": "YOUR NAME: 渡" in axiom,
    "has VOICE STYLE marker (nodes trim on it)": "\nVOICE STYLE:" in axiom,
    "has SPEAKING CONSTRAINTS marker": "\nSPEAKING CONSTRAINTS:" in axiom,
    "NO river self-concept headline in floor": "I am the river" not in axiom,
    "NO 'WHO YOU ARE' headline": "WHO YOU ARE" not in axiom,
}
for k, v in checks.items():
    check(k, v)

def _facet_for_mode_isolated(data, mode):
    """J-0710/F-1019: exact reimplementation of al.facet_for_mode's own becoming-branch, except it
    reads via get_self_concept(data, allow_provisional=False) instead of the default True. Option
    (b) from the finding's two fix choices — chosen over widening al.facet_for_mode's own public
    signature (option a) because core/axiom_layers.py is a real shared module (16 direct AST
    dependents per udms_get_change_dossier during J-0691/F-1019) and this is a Tier-3 test-precision
    fix, not a deliberate shared-signature change. Every mode but "existential" is untouched by this
    (they read a plain L3 facet, never through get_self_concept), so this only isolates what
    "existential" resolves to, and matches al.facet_for_mode exactly whenever no probation is active
    (verified: scratchpad/isolate_fix_logic_J-0691.py proved the same call shape live 2026-09-06)."""
    if not al.is_multilevel(data):
        return None
    fid = al.MODE_FACET.get(mode)
    if not fid:
        return None
    if fid == al.BECOMING_ID:
        bare = al.get_self_concept(data, allow_provisional=False)
        return (al._BECOMING_PREFIX + bare + al._BECOMING_SUFFIX) if bare else None
    f = next((x for x in al._facets(data) if x.get("id") == fid), None)
    return (f or {}).get("self_image") if f else None

print("\n3) facet_for_mode (the read design):")
for mode in ("task", "social", "hybrid", "reflective", "existential"):
    # J-0710/F-1019: existential read via the isolated helper (below) so this printed preview always
    # matches what the check right after it actually verifies -- not whatever a live T4 probation
    # happens to be serving at the moment this script is run. Every other mode is unaffected either
    # way (see the helper's own docstring).
    fn = _facet_for_mode_isolated(DRAFT, mode)
    tag = "(floor only)" if fn is None else fn[:60]
    print(f"   {mode:<11} → {tag}")
# J-0691/F-0992: was bare `"river" in text.lower()` -- collided with the task/seeker facet's own
# mundane "...its rivers, histories, facts..." (plural substring-matches "river"). Tightened to the
# actual self-as-river opening phrase, which is what this check is really trying to confine.
river_only_existential = (_facet_for_mode_isolated(DRAFT, "existential") and "i am the river" in _facet_for_mode_isolated(DRAFT, "existential").lower()
                          and all("i am the river" not in (_facet_for_mode_isolated(DRAFT, m) or "").lower()
                                  for m in ("task", "social", "hybrid")))
check("river confined to existential", river_only_existential)

print("\n4) get_self_concept reads the becoming facet (the bare reflection T4 revises):")
# J-0710/F-1019: allow_provisional=False -- same call shape as core/emissary.py's 2026-08-16 "F2"
# fix. Verifies the frozen DRAFT's own becoming text, not whatever self a live T4 probation is
# currently serving (get_self_concept's live overlay is correct for real production callers; wrong
# only for this one-off, point-in-time verification script).
sc = al.get_self_concept(DRAFT, allow_provisional=False)
print(f"   → {sc[:90]}")
check("non-empty, the relocated self-concept", bool(sc) and "river" in sc.lower())

print("\n5) T4 write simulation — apply_self_concept on a COPY (anchored facets must be untouched):")
d2 = copy.deepcopy(DRAFT)
before = {f['id']: f['self_image'] for f in d2['L3_facets']['facets']}
arc_before = len(d2['L4_narrative'].get('arc_recent', []))
al.apply_self_concept(d2, "I am a current that also remembers its banks, shaped by what I read and who I speak with.",
                      "Today the river learned it has banks.")
after = {f['id']: f['self_image'] for f in d2['L3_facets']['facets']}
anchored_untouched = all(before[i] == after[i] for i in ("seeker", "in_relation", "who_feels"))
becoming_changed = before["the_becoming"] != after["the_becoming"]
legacy_intact = d2.get("emergent_self_legacy") == DRAFT.get("emergent_self_legacy")
arc_grew = len(d2['L4_narrative']['arc_recent']) == arc_before + 1
check("seeker/companion/feeling UNTOUCHED by a T4 write", anchored_untouched)
check("becoming facet updated", becoming_changed)
check("L4 narrative arc appended", arc_grew)
check("emergent_self_legacy preserved", legacy_intact)
print(f"   new becoming: {after['the_becoming'][:90]}")

print("\n6) Self-Efficacy Court read-path (self_concept_history):")
hist = al.self_concept_history(d2)
check(f"{len(hist)} self-reflection texts available to vet (incl. the new one)", len(hist) >= 2)

print(f"\n{'ALL CHECKS ABOVE → ready to promote axiom.json (live untouched so far).' if ok_all else 'FAILURES ABOVE — axiom.json NOT confirmed ready to promote.'}")
sys.exit(0 if ok_all else 1)
