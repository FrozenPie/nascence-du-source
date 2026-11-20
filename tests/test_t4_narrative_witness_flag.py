"""J-3840 (D-0672 option A): T4_NARRATIVE_WITNESS gates only the two T4 narrative_quality observe calls.
Static/hermetic: parses source only, imports nothing, touches no data/ path."""
import ast, pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "nodes" / "subconscious_node.py"


def test_flag_default_true_and_gates_observe():
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    flag = [n for n in tree.body if isinstance(n, ast.Assign)
            and any(getattr(t, "id", "") == "T4_NARRATIVE_WITNESS" for t in n.targets)]
    assert len(flag) == 1 and flag[0].value.value is True
    gated = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.If) and "T4_NARRATIVE_WITNESS" in ast.unparse(n.test):
            body = ast.unparse(n)
            assert "t4_self_concept" in body and "t4_arc" in body
            gated += 1
    assert gated == 1
    # no other observe call for these kinds outside the gate
    assert SRC.read_text(encoding="utf-8").count('"t4_arc"') == 1


if __name__ == "__main__":
    test_flag_default_true_and_gates_observe(); print("ok")
