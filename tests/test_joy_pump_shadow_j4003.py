"""J-4003 / D-0776 B: shadow log of a valence-scaled joy pump. Isolated: temp log path, no live data/."""
import json, types
import core  # import core BEFORE anything that may reshape sys.path
from core import mood, schema


def _aff(v, j=0.2):
    return types.SimpleNamespace(valence=v, joy=j)


def test_flag_off_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(mood, "_JPS_LOG", tmp_path / "j.jsonl")
    monkeypatch.setattr(schema, "JOY_PUMP_VALENCE_SHADOW", False)
    assert mood.shadow_joy_pump(_aff(0.5), 0.3) is False
    assert not (tmp_path / "j.jsonl").exists()


def test_negative_valence_scales_to_zero(tmp_path, monkeypatch):
    monkeypatch.setattr(mood, "_JPS_LOG", tmp_path / "j.jsonl")
    monkeypatch.setattr(schema, "JOY_PUMP_VALENCE_SHADOW", True)
    a = _aff(-0.4)
    assert mood.shadow_joy_pump(a, 0.3, caller_line=7) is True
    r = json.loads((tmp_path / "j.jsonl").read_text().splitlines()[0])
    assert r["joy_live"] == 0.5 and r["joy_scaled"] == 0.2 and r["delta"] == -0.3 and r["line"] == 7
    assert a.joy == 0.2 and a.valence == -0.4


def test_positive_valence_and_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(mood, "_JPS_LOG", tmp_path / "j.jsonl")
    monkeypatch.setattr(schema, "JOY_PUMP_VALENCE_SHADOW", True)
    mood.shadow_joy_pump(_aff(0.5, 0.9), 0.4)
    r = json.loads((tmp_path / "j.jsonl").read_text().splitlines()[0])
    assert r["joy_live"] == 1.0 and abs(r["joy_scaled"] - 1.0) < 1e-9


def test_failopen(tmp_path, monkeypatch):
    monkeypatch.setattr(mood, "_JPS_LOG", tmp_path / "j.jsonl")
    monkeypatch.setattr(schema, "JOY_PUMP_VALENCE_SHADOW", True)
    assert mood.shadow_joy_pump(None, 0.3) is False
    assert mood.shadow_joy_pump(_aff(0.1), "x") is False
