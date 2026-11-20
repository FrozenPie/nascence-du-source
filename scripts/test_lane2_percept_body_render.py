import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core
from core import lane2
from core.lane2_notice_check import parse_percepts

def test_body_clean_string():
    t = lane2.percept_lines({"world": {"place": "study"}, "body": {"drive": 0.41234}, "somatic": {"energy": 0.5}})
    assert "- body: drive 0.41" in t and "{" not in t
    assert "- somatic: energy 0.5" in t
    assert parse_percepts(t)["drive"] == "0.41"

def test_legacy_dict_repr_still_parses():
    assert parse_percepts("- body: {'drive': 0.41}")["drive"] == "0.41"

if __name__ == "__main__":
    test_body_clean_string(); test_legacy_dict_repr_still_parses(); print("ok")
