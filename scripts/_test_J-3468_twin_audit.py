"""J-3468: test the twin-row audit rule and the arms on a synthetic file under a temp dir. Touches no live data."""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import core  # noqa: E402,F401  (import core BEFORE any lab_env, per the job-run test rule)
import j3468_twin_row_audit as a  # noqa: E402

assert Path(a.__file__).resolve().parent.parent == ROOT, "test must run against its own tree"

LONG = "I stop circling that colonial hierarchy question and feel the cold rain on the window, steady"


def row(ts, source, thought, valence=0.6, arousal=0.4, sounds=("rain_on_roof",), tension=0.2):
    return {"ts": ts, "source": source, "place": "study", "weather": "rain", "fire": "burning",
            "objects": {"cat": {"mood": "calm", "activity": "asleep", "location": "rug"}, "book": "Walden",
                        "garden_bed": ["mint"]},
            "body": {"energy": 0.5, "fatigue": 0.1, "tension": tension},
            "affect": {"valence": valence, "arousal": arousal, "joy": 0.5, "trust": 0.5, "surprise": 0.1,
                       "fear": 0.1, "anger": 0.0, "disgust": 0.0},
            "thought": thought, "level": 0.3, "sounds": list(sounds), "n_spaces": 6, "n_sounds": len(sounds),
            "tide_level": 0.5, "sun_az": 180.0, "moon_illum": 0.4, "weather_dir": 270, "fire_fuel": 0.3,
            "at_study": 1, "at_garden": 0, "at_shore": 0, "at_wood": 0}


def build() -> list[dict]:
    rows, ts = [], 1_790_000_000.0
    for k in range(300):
        ts += 60
        full = f"{LONG} number {k} " + "x" * 40
        raw70 = full[:70]
        if k % 5 == 0:
            raw70 = raw70.replace(" ", "  ", 2)          # whitespace run in the stamp, as store.py slices content raw
        if k % 7 == 0:
            rows.append(row(ts, "inner_thought", "an unrelated stamp with no idle partner " + str(k)))
            continue                                      # inner_thought without twin
        rows.append(row(ts, "inner_thought", raw70, tension=0.2))
        gap = 0.2 if k % 11 else 3.0                      # every 11th pair has a 3 s gap (outside 1.2, inside 10)
        rows.append(row(ts + gap, "idle", full, tension=0.25))
        if k % 13 == 0:
            rows.append(row(ts + 5, "reading", "a passage"))
    return rows


def main() -> None:
    rows = build()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        p = td / "geometry_tuples.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        # 1. the rule on the raw list
        pairs_expected = sum(1 for k in range(300) if k % 7 != 0)
        n_gap = sum(1 for k in range(300) if k % 7 != 0 and k % 11 == 0)
        st12 = a.flag_stamp_twins(rows)
        st10 = a.flag_stamp_twins(rows, 10.0)
        assert len(st10) == pairs_expected, (len(st10), pairs_expected)
        assert len(st12) == pairs_expected - n_gap, (len(st12), pairs_expected - n_gap)
        assert all(rows[i]["source"] == "inner_thought" for i in st10)
        # an unmatched inner_thought is never flagged
        assert not any(rows[i]["thought"].startswith("an unrelated") for i in st10)
        # 2. a stamp can't claim an idle row twice: duplicate stamps -> only one flagged
        dup = [rows[1], rows[1], rows[2]]
        assert len(a.flag_stamp_twins(dup)) == 1
        # 3. full run on the temp file, writing under the temp dir only
        res = a.run(p, td / "out", n_permutations=3, n_shuffles=3)
        assert (td / "out" / "results.json").exists()
        tc = res["twin_census"]
        assert tc["twin_stamp_rows"] == len(st12) and tc["idle_rows"] == 300 - len([k for k in range(300) if k % 7 == 0])
        assert res["mapping_census"]["asis"]["rows"] == len(rows)
        assert res["mapping_census"]["stripped"]["rows"] == len(rows) - len(st12)
        assert res["mapping_census"]["stripped_wide"]["rows"] == len(rows) - len(st10)
        # idle rows carry the fields the stamp rows lack on the real file; here both carry them, so presence is 1.0
        assert res["stamp_vs_idle_fields"]["hud_fields"]["cognitive_geometry.level"]["stamp_present"] == 1.0
        assert res["object_graph_commonality"]["asis"]["n_tuples_alltime"] == len(rows)
        assert res["object_graph_commonality"]["stripped"]["n_tuples_alltime"] == len(rows) - len(st12)
        # 4. the audit never wrote the input
        assert p.read_text(encoding="utf-8").count("\n") == len(rows)
    print("J-3468 twin audit test OK:", len(rows), "rows,", len(st12), "twins @1.2s,", len(st10), "@10s")


if __name__ == "__main__":
    main()
