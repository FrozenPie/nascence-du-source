"""J-4002 / D-0775 B: shadow log of the without-vitality mood word. Isolated: temp log path, no live data/."""
import json, types
import core  # import core BEFORE anything that may reshape sys.path
from core import mood, schema


def _aff(v):
    return types.SimpleNamespace(valence=v, arousal=0.3)


def test_math_and_words(tmp_path, monkeypatch):
    st = {"drive": 0.6, "per_drive": {"vitality": 0.36 * 0.44}}
    r = mood.valence_without_vitality(st)
    assert abs(r["drive_wo"] - (0.36 - 0.1584) ** 0.5) < 1e-9
    assert abs(r["valence_wo"] - (1 - 2 * r["drive_wo"])) < 1e-9


def test_flag_off_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(mood, "_MWS_LOG", tmp_path / "m.jsonl")
    monkeypatch.setattr(schema, "MOOD_WORDS_NO_VITALITY_SHADOW", False)
    assert mood.shadow_mood_words_no_vitality(_aff(-0.4), status={"drive": 0.7, "per_drive": {"vitality": 0.2}}) is False
    assert not (tmp_path / "m.jsonl").exists()


def test_flag_on_logs_both_words_and_leaves_line(tmp_path, monkeypatch):
    monkeypatch.setattr(mood, "_MWS_LOG", tmp_path / "m.jsonl")
    monkeypatch.setattr(schema, "MOOD_WORDS_NO_VITALITY_SHADOW", True)
    a = _aff(-0.4)
    before = mood.mood_line_words(a)
    assert mood.shadow_mood_words_no_vitality(a, status={"drive": 0.7, "per_drive": {"vitality": 0.2}}) is True
    row = json.loads((tmp_path / "m.jsonl").read_text().splitlines()[0])
    assert row["word"] == "low" and row["word_wo"] != row["word"] and row["valence_wo"] > row["valence"]
    assert mood.mood_line_words(a) == before and a.valence == -0.4


def test_failopen(tmp_path, monkeypatch):
    monkeypatch.setattr(mood, "_MWS_LOG", tmp_path / "m.jsonl")
    monkeypatch.setattr(schema, "MOOD_WORDS_NO_VITALITY_SHADOW", True)
    assert mood.shadow_mood_words_no_vitality(_aff(0.0), status={"drive": None}) is False
    assert mood.shadow_mood_words_no_vitality(None) is False
