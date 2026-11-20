"""J-4314 (D-0841 b): fallen tree across the path slows Du's garden<->wood legs. Temp-path store only."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import wood_life as WL, locomotion as L
ok = True
def check(n, c):
    global ok; ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
tmp = Path(tempfile.mkdtemp()) / "wood_life.json"
WL._F = tmp
def put(ft): tmp.write_text(json.dumps({"fallen_tree": ft}), encoding="utf-8")
ft = {"across_path": True, "trunk_rounds_left": 18}
put(ft)
base = L._leg_secs("garden", "wood", "", False, "")
check("flag OFF: no change", L._du_leg_secs("garden", "wood", "", False, "") == base and L._du_leg_line("garden", "wood", "", False, "") == L._du_leg_line("garden", "wood", "", False, "") and "trunk" not in L._du_leg_line("garden", "wood", "", False, ""))
L.FALLEN_TREE_CONSEQUENCE = True
check("flag ON, across: slower garden->wood", abs(L._du_leg_secs("garden", "wood", "", False, "") - base * 1.5) < 1e-6)
check("flag ON, wood->garden slower too", L._du_leg_secs("wood", "garden", "", False, "") > L._leg_secs("wood", "garden", "", False, ""))
check("tag in line", "trunk" in L._du_leg_line("garden", "wood", "", False, ""))
check("shore leg unaffected", L._du_leg_secs("wood", "shore", "", False, "") == L._leg_secs("wood", "shore", "", False, ""))
check("cat/companion path (_leg_secs) untouched", L._leg_secs("garden", "wood", "", False, "") == base)
put({**ft, "across_path": False}); check("not across: unchanged", L._du_leg_secs("garden", "wood", "", False, "") == base)
put({**ft, "trunk_rounds_left": 0}); check("trunk gone: unchanged", L._du_leg_secs("garden", "wood", "", False, "") == base)
put(None); check("no tree: unchanged", L._du_leg_secs("garden", "wood", "", False, "") == base)
tmp.write_text("garbage"); check("corrupt store fail-open", L._du_leg_secs("garden", "wood", "", False, "") == base)
sys.exit(0 if ok else 1)
