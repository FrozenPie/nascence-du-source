"""J-3288 test: the lab tooling for the study-note key_fact leak check. Asserts its own tree; imports core BEFORE lab_env;
writes only under a temp dir; touches no live data and calls no model.
Run from the worktree: python scripts/_test_J-3288_study_fact_check.py"""
from __future__ import annotations
import json, sqlite3, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa: E402,F401
assert Path(core.__file__).resolve().is_relative_to(ROOT), (core.__file__, ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
import _lab_J3288_classify as C  # noqa: E402
import _lab_J3288_build_sample as B  # noqa: E402
import _lab_J3288_judge as J  # noqa: E402

P = ("In the course of the year 1813 alone, one million forty thousand soldiers were summoned. General Jomini, Swiss by birth, "
     "had deserted his post. The temporary bridges were made of beams taken from the cabins of the Poles. Fouche was made a Senator.")


def main():
    sents = C.sentences(P); sst = [C.content_stems(s) for s in sents]; pst = C.content_stems(P)
    # a verbatim-ish fact is present; a paraphrase is not 'absent'; a fact made of other words is absent
    assert C.classify("General Jomini deserted his post", P, sents, sst, pst)["verdict"] == "present"
    assert C.classify("Jomini, a Swiss, abandoned his post", P, sents, sst, pst)["verdict"] in ("paraphrased", "present")
    assert C.classify("Rivers froze early that winter near Smolensk", P, sents, sst, pst)["verdict"] == "absent"
    # entity check: spelled-out number, accent folding, ethnonym fold pass; an invented date / name fails
    assert C.entity_missing("1,040,000 soldiers summoned in 1813", P) == []
    assert C.entity_missing("Fouché was appointed a Senator", P) == []
    assert C.entity_missing("Beams came from Polish cabins", P) == []
    assert C.entity_missing("Jomini deserted in 1802", P) == ["#1802"]
    assert C.entity_missing("Marshal Davout deserted", P) == ["Davout"]
    # note-file parser (frontmatter + facts)
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "TAB_x.md"
        f.write_text("# T\n\n*A study note by X · 2026-11-05 18:02 · on: Some Book · subject: x y · pass: 1 · sittings: 5*\n\n"
                     "I see.\n\n**What I learned:**\n- fact one\n- fact two\n\n**My thoughts:** hm\n", encoding="utf-8")
        n = B.parse_note(f)
        assert n["book"] == "Some Book" and n["pass"] == 1 and n["sittings"] == 5 and n["key_facts"] == ["fact one", "fact two"], n
        assert not n["revised"]
        f.write_text("# T\n\n*A study note by X · 2026-11-05 18:02 · on: Some Book · subject: x · revised*\n\nI see.\n", encoding="utf-8")
        assert B.parse_note(f)["revised"]
    # judge refuses Ramses without a network call
    try:
        sys.argv = ["x", "--hub", "http://LAN-HOST:11438", "--out", str(Path(tempfile.gettempdir()) / "j3288_x.json")]
        J.main()
        raise AssertionError("judge accepted a Ramses hub")
    except SystemExit as e:
        assert "Ramses" in str(e)
    print("J-3288 test OK")


if __name__ == "__main__":
    main()
