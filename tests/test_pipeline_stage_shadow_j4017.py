"""J-4017 / D-0759: pre-speech per-stage wall-time shadow. Hermetic: temp store, no live data/."""
import asyncio, json
import core  # import core BEFORE anything that may reshape sys.path
from pathlib import Path
from core import pipeline_stage_shadow as pss, profile, telemetry

_TREE = Path(__file__).resolve().parent.parent


def test_core_is_this_tree():
    assert str(Path(core.__file__).resolve()).startswith(str(_TREE))


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


async def _cycle(t, with_voice=True, fail_stage=None):
    async with t.stage("perception"):
        await asyncio.sleep(0.01)
    async with t.stage("critic"):
        await asyncio.sleep(0.01)
    async with t.stage("critic"):
        await asyncio.sleep(0.01)
    t.note(critic_retried=True, introspective_passes=2)
    if fail_stage:
        async with t.stage("executive"):
            raise ValueError("boom")
    if with_voice:
        async with t.stage("voice"):
            await asyncio.sleep(0.01)


def test_row_written_at_voice(tmp_path, monkeypatch):
    log = tmp_path / "p.jsonl"
    monkeypatch.setattr(pss, "_LOG", log)
    monkeypatch.setattr(profile, "guard_path", lambda p: p)
    t = pss.start("abcdef1234", "human")
    _run(_cycle(t))
    rows = pss.load(log)
    assert len(rows) == 1
    r = rows[0]
    assert [s["s"] for s in r["stages"]] == ["perception", "critic", "critic", "voice"]
    assert r["critic_retried"] is True and r["introspective_passes"] == 2
    assert r["wait_s"] >= 0.03 and r["t_voice_start"] >= r["t_arrive"]
    a = pss.analyze(rows)
    assert a["cycles"] == 1 and a["stages"]["critic"]["spans"] == 2 and a["critic_retry_rate"] == 1.0


def test_non_human_is_noop(tmp_path, monkeypatch):
    log = tmp_path / "p.jsonl"
    monkeypatch.setattr(pss, "_LOG", log)
    monkeypatch.setattr(profile, "guard_path", lambda p: p)
    _run(_cycle(pss.start("c1", "internal")))
    assert not log.exists()


def test_no_voice_no_row_and_body_exception_propagates(tmp_path, monkeypatch):
    log = tmp_path / "p.jsonl"
    monkeypatch.setattr(pss, "_LOG", log)
    monkeypatch.setattr(profile, "guard_path", lambda p: p)
    t = pss.start("c2", "human")
    try:
        _run(_cycle(t, fail_stage=True))
        raised = False
    except ValueError:
        raised = True
    assert raised and not log.exists()
    assert t.stages[-1]["s"] == "executive" and t.stages[-1]["ok"] == 0


def test_kill_switch_and_lab(tmp_path, monkeypatch):
    log = tmp_path / "p.jsonl"
    monkeypatch.setattr(pss, "_LOG", log)
    monkeypatch.setattr(profile, "guard_path", lambda p: p)
    monkeypatch.setattr(pss, "ENABLED", False)
    _run(_cycle(pss.start("c3", "human")))
    assert not log.exists()
    monkeypatch.setattr(pss, "ENABLED", True)
    monkeypatch.setattr(telemetry, "_LAB_MODE", True)
    _run(_cycle(pss.start("c4", "human")))
    assert not log.exists()


def test_write_fence_failopen(tmp_path, monkeypatch):
    # non-live process, shipped path: guard_path refuses; nothing raises, nothing is written
    assert profile.LIVE is False
    live = pss._LOG
    before = live.exists()
    _run(_cycle(pss.start("c5", "human")))
    assert live.exists() == before


def test_stage_failure_in_recorder_never_raises(tmp_path, monkeypatch):
    t = pss.start("c6", "human")
    monkeypatch.setattr(t, "_record", lambda *a, **k: 1 / 0)
    _run(_cycle(t))   # must not raise
