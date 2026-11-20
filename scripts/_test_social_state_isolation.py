"""
Offline regression test for J-1690 / F-2283: core.social_model's social_state.json must be
rebased by core.profile.activate_profile() like every other per-agent data/ path constant.

THE LEAK. Since J-1358 (9b50d6b) the orchestrator save()s Du's LIVE relational state
(data/social_state.json) on EVERY input_type == "human" cycle. core.social_model's
_SOCIAL_STATE_PATH was missing from activate_profile()'s rebase tuple, so a '_smoke' / named-profile
harness that ran human cycles through a real Orchestrator (scripts/smoke_test.py, debate.py,
_verify_genesis.py) rewrote the REAL file instead of its own profile dir -- fake exchanges advancing
relational_trust / cycles_since_spike, and a correction-phrase probe leaving a spike on disk for the
next real boot to replay (F-1919's own harm).

HOW THIS TEST STAYS SAFE (it must never touch the real data/). Every path lives under a tempdir:
core.profile._DATA and core.social_model._SOCIAL_STATE_PATH are BOTH pointed into that tempdir
BEFORE activate_profile() runs, so the "live" file below is a STAND-IN -- even the failure this test
exists to catch (a leak) lands on the stand-in, never on the real file. No model servers, no DB, no
Orchestrator is constructed. (The real file's own sha256/mtime is also compared before/after, as an
advisory line -- a real Du exchange mid-run would legitimately move it, so it never fails the run.)

Covers:
  0. premise: the shipped default _SOCIAL_STATE_PATH is exactly core.profile._DATA / "social_state.json"
     (the generic rebase can only see a Path constant that lives under data/)
  1. un-activated (the real Du boot never calls activate_profile): SocialModelManager reads and
     writes the live file exactly as before
  2. activate_profile(<named>) rebases _SOCIAL_STATE_PATH into the profile dir
  3. the profile boots from the DEFAULT social state, not the live relational trust (read isolation)
  4. a simulated harness human cycle -- the three calls Orchestrator._compute_attention_vector makes on
     self.social: apply_correction (+ save on a spike), decay_cycle, save -- with a probe that contains
     a real correction phrase leaves the live file byte-identical (sha256 AND mtime_ns), and the spike
     lands in the profile's own file instead
  5. re-activating the same / another profile never nests profile dirs
  6. activate_profile(None) (root alias = Carl) restores the live path -- the identity no-op

Run: python scripts/_test_social_state_isolation.py   (exit 0 = all passed)
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import core.profile as P
import core.social_model as SM

results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if (detail and not cond) else ""))


def snap(path):
    """(sha256, mtime_ns) of a file, or None if it does not exist."""
    try:
        return (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
    except FileNotFoundError:
        return None


print("\n=== J-1690 / F-2283 -- social_state.json isolation (offline, tempdir stand-in) ===\n")

# --- 0. premise (read BEFORE anything is patched) ---------------------------------------------------
DEFAULT_PATH = SM._SOCIAL_STATE_PATH            # the real data/social_state.json of THIS tree
REAL_BEFORE = snap(DEFAULT_PATH)                # advisory snapshot of the real file
print("0. Premise")
try:
    _rel = DEFAULT_PATH.relative_to(P._DATA)
except ValueError:
    _rel = None
check("default _SOCIAL_STATE_PATH == core.profile._DATA / 'social_state.json'",
      _rel == Path("social_state.json"), f"{DEFAULT_PATH} vs _DATA={P._DATA}")

TMP = Path(tempfile.mkdtemp(prefix="j1690_social_iso_"))
try:
    FAKE_DATA = TMP / "data"
    FAKE_DATA.mkdir()
    LIVE = FAKE_DATA / "social_state.json"      # STAND-IN for the real data/social_state.json
    SEED = {                                    # mirrors the real file's shape after the J-1358 fix
        "relation_id": "travis", "expected_tone": "analytical", "relational_trust": 0.835,
        "user_expectations": [], "user_knowledge_state": {}, "interpersonal_tensions": [],
        "delta_social": 0.0, "cycles_since_spike": 1014, "state_version": 1,
    }
    OLD_NS = 1_700_000_000 * 10 ** 9            # a fixed old mtime: ANY rewrite is visible, even within one tick

    def seed_live():
        LIVE.write_text(json.dumps(SEED, indent=2), encoding="utf-8")
        os.utime(LIVE, ns=(OLD_NS, OLD_NS))

    # Point BOTH ends at the tempdir before anything under test can run.
    P._DATA = FAKE_DATA
    SM._SOCIAL_STATE_PATH = LIVE

    # --- 1. un-activated path == today's behaviour -------------------------------------------------
    print("\n1. Un-activated path (the real boot): reads and writes the live file as before")
    seed_live()
    _live_before = P.LIVE
    P.LIVE = True      # J-1810: save() is behind the D-0179 fence now; this part models the REAL boot (mark_live())
    m = SM.SocialModelManager()
    check("manager loaded the live file",
          m.state.relational_trust == 0.835 and m.state.cycles_since_spike == 1014,
          f"trust={m.state.relational_trust} cycles={m.state.cycles_since_spike}")
    m.state.decay_cycle()
    m.save()
    disk = json.loads(LIVE.read_text(encoding="utf-8"))
    check("save() wrote the live file",
          disk["cycles_since_spike"] == 1015 and disk["relational_trust"] == 0.84, disk)
    P.LIVE = _live_before      # restore: everything below models a NON-live harness process

    # --- 2. a named profile rebases the path --------------------------------------------------------
    print("\n2. activate_profile(<named>) rebases the social state path")
    seed_live()
    before = snap(LIVE)
    PROFILE = "_j1690_social_iso"
    base = P.activate_profile(PROFILE)
    expected = base / "social_state.json"
    check("profile dir is under the temp data root", base == FAKE_DATA / "profiles" / PROFILE, base)
    check("_SOCIAL_STATE_PATH rebased into the profile dir", SM._SOCIAL_STATE_PATH == expected,
          f"{SM._SOCIAL_STATE_PATH} != {expected}")

    # --- 3/4. a harness human cycle never touches the live file --------------------------------------
    print("\n3. A harness human cycle in the profile never touches the live file")
    h = SM.SocialModelManager()
    check("profile boots from the default social state, not the live relational trust",
          h.state.relational_trust == 0.85 and h.state.cycles_since_spike == 0 and not expected.exists(),
          f"trust={h.state.relational_trust} cycles={h.state.cycles_since_spike}")
    probe = "That is not what I asked. Just answer the question."   # real _CORRECTION_SIGNALS phrases
    spike = h.state.apply_correction(probe)
    if spike > 0:
        h.save()                    # orchestrator.py: the correction-spike branch's save
    h.state.decay_cycle()
    h.save()                        # orchestrator.py: J-1358's per-human-cycle save
    check("the probe really exercised the spike path", spike > 0)
    after = snap(LIVE)
    check("LIVE file byte-identical (sha256)", after is not None and after[0] == before[0],
          f"before={before} after={after}")
    check("LIVE file mtime_ns unchanged", after is not None and after[1] == before[1],
          f"before={before} after={after}")
    # J-1810 / F-2428: a NON-live process's save() is refused by guard_path even inside data/profiles/<name>/
    # (D-0179/D-0200), so persistence is deliberately gone; the harness's own state still evolves in memory.
    check("the harness's in-memory state carries the spike (persistence refused by the fence)",
          h.state.delta_social > 0.3 and not expected.exists(), (h.state.delta_social, expected.exists()))

    # --- 5. idempotent, never nests ------------------------------------------------------------------
    print("\n4. Re-activation never nests")
    P.activate_profile(PROFILE)
    check("same profile again -> same path", SM._SOCIAL_STATE_PATH == expected, SM._SOCIAL_STATE_PATH)
    other = P.activate_profile("_j1690_social_iso_b")
    check("another profile -> that profile's own path (not nested)",
          SM._SOCIAL_STATE_PATH == FAKE_DATA / "profiles" / "_j1690_social_iso_b" / "social_state.json"
          and other == FAKE_DATA / "profiles" / "_j1690_social_iso_b", SM._SOCIAL_STATE_PATH)

    # --- 6. root alias == identity no-op --------------------------------------------------------------
    print("\n5. Root alias (Carl) is an identity no-op")
    P.activate_profile(None)
    check("root alias restores the live path", SM._SOCIAL_STATE_PATH == LIVE, SM._SOCIAL_STATE_PATH)
    r = SM.SocialModelManager()
    check("manager reads the (untouched) live file again",
          r.state.relational_trust == 0.835 and r.state.cycles_since_spike == 1014,
          f"trust={r.state.relational_trust} cycles={r.state.cycles_since_spike}")
finally:
    shutil.rmtree(TMP, ignore_errors=True)

# --- advisory: the REAL file of the tree this script runs in ---------------------------------------
REAL_AFTER = snap(DEFAULT_PATH)
if REAL_AFTER == REAL_BEFORE:
    print(f"\n  [info] real {DEFAULT_PATH.name} untouched by this run: {REAL_BEFORE}")
else:
    print(f"\n  [WARN] real {DEFAULT_PATH} changed during this run (before={REAL_BEFORE} after={REAL_AFTER}); "
          f"if Du is live, a real exchange may legitimately have moved it -- otherwise investigate")

passed = sum(1 for _, ok in results if ok)
print(f"\n=== {passed}/{len(results)} passed ===")
sys.exit(0 if passed == len(results) else 1)
