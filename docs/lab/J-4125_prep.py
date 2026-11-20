"""J-4125 prep: reuse J-2888 inputs (same 100-row sample, same user prompts / context); rewrite arm systems B, C, D so the reply is one string
(never an object). Pure text surgery on the J-2888 systems; no core import, nothing live touched."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
src = json.load(open(r"C:\Nascence\docs\lab\J-2888_data\inputs.json", encoding="utf-8"))
S = src["systems"]
ONE = ' The value of "grounding" must be ONE plain string of prose (or null) - never an object, list or extra keys.'
def swap(s, old_tail_marker, new_tail):
    i = s.index(old_tail_marker); return s[:i] + new_tail
B = S["B"]; i = B.index("Schema:")
B_new = B[:i] + ('Schema: {"grounding": "2-3 sentences of concrete real-world mechanism behind the literal referent of the thought, as one plain string"}, '
                 'or {"grounding": null} when the thought has no physical referent whose mechanism could be named.' + ONE)
C = S["C"]; i = C.index("Schema:")
C_new = C[:i] + ('Schema: {"grounding": "2-3 sentences of concrete real-world mechanism behind the literal referent of the thought, as one plain string"}, '
                 'or {"grounding": null} when the thought has no physical referent.' + ONE + "\n"
                 "Never write the words 'symbolizes', 'represents' or 'alludes' (or symbol, metaphor, evokes): say what the thing physically is and does, not what it means.")
D = S["D"]; i = D.index("Schema:")
D_new = D[:i] + ('Schema: {"grounding": "2-3 sentences of concrete real-world mechanism behind the literal referent of the thought, as one plain string"}, '
                 'or {"grounding": null}.' + ONE + "\n"
                 "Give the mechanism ONLY when the thought itself names a concrete physical thing (an object, a material, an animal, a sound, a place feature, a weather or light condition); "
                 "for a thought about a feeling, an idea, a person's act, a book, or a self-image with no physical thing named, answer null. "
                 "Name no object, place, person, number or file that the thought does not itself contain; if the mechanism is uncertain, say less, not more.")
out = {"systems": {"B": B_new, "C": C_new, "D": D_new}, "prompts": {k: {a: v[a] for a in ("B", "C", "D")} for k, v in src["prompts"].items()}}
json.dump(out, open(r"C:\Nascence\docs\lab\J-4125_data\inputs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for a in "BCD": print(a, out["systems"][a][-700:], "\n----")
