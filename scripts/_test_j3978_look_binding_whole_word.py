"""J-3978 / D-0760: look_binding matches bind_targets whole-word; up/out/far are no longer targets. Pure, no stores."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import core
import core.sound_knowledge as sk
assert str(pathlib.Path(core.__file__).resolve()).startswith(str(pathlib.Path(__file__).resolve().parents[1]))
fails = []
def chk(c, m):
    print(("  ok   " if c else "  FAIL ") + m)
    if not c: fails.append(m)
chk(not sk._binds_target("triplefin", ("fin", "dolphin")), "'triplefin' does not match 'fin'")
chk(sk._binds_target("the fin", ("fin",)), "'the fin' matches 'fin'")
chk(not sk._binds_target("treetops", ("tree",)), "'treetops' does not match 'tree'")
chk(sk._binds_target("a black cat on the wall", ("black cat",)), "multi-word target matches")
chk(sk._binds_target("the kōwhai tree", ("kōwhai",)), "macron target matches")
for k, v in sk.AUDITION.items():
    chk(v["bind_targets"], f"{k} still has targets")
    chk(not ({"up", "out", "far"} & set(v["bind_targets"])), f"{k} has no up/out/far")
print(f"{'FAILS' if fails else 'ALL OK'}: {len(fails)} failed")
raise SystemExit(1 if fails else 0)
