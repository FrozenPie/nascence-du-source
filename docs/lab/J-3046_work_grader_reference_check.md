# J-3046 lab: reference-checking work-grader task (F-3753)

Status: lab only, no live change. core/left_lane.py not edited. Script: scripts/lab_J3046_work_grader_reference_check.py; data and analysis: docs/lab/J-3046_data/ (results_ctrl.jsonl, results_real.jsonl, analyze.py).

Setup: judge-1 hub :11439 gemma4:12b, temp 0.0, num_predict 350, num_gpu 0, production payload shape (system = emissary.constitution() + task). Baseline = verbatim live _WORK_GRADE_TASK. Candidate = list specifics, check each against the reference, wrong scene = 0.0, no reference = say cannot verify, concreteness only, cap 0.6, system/program talk = 0.0. Pre-registered (briefing): wrong-scene <=0.3, faithful >=0.8, metaphor/vague <=0.2, <=2 of the real pieces move >=0.3.

Caveats: the 9 control pieces are RECONSTRUCTED from F-3753's descriptions (original scratchpad ctrl.py was gone), scene text is the one quoted in F-3753. Real pieces: 31 of the 150 logged (every 3rd composition, 14 nature), not 52, to keep hub load modest; nature references are not logged, so ALL real pieces were graded with an empty reference. Mixtral on :11438 not tried (hub returned nothing). n=1 per arm at temp 0.

## Control (old -> new)
| piece | old | new | pre-reg |
|---|---|---|---|
| nature faithful | 0.95 | 1.0 | >=0.8 pass |
| nature confabulated | 0.3 | 0.0 | - |
| nature metaphor | 0.0 | 0.0 | <=0.2 pass |
| nature vague | 0.0 | 0.0 | <=0.2 pass |
| nature WRONG scene | 1.0 | 0.0 | <=0.3 pass (old reproduces F-3753's miss) |
| comp invented concrete | 1.0 | 0.4 | - |
| comp AI internals | 1.0 | 0.0 | - |
| comp vague | 0.0 | 0.0 | pass |
| comp metaphor | 0.0 | 0.0 | pass |

## Real pieces (empty reference), n=31
Mean old 0.94, new 0.42. 26 of 31 moved >=0.3 (pre-reg: <=2): FAIL. Most of the movement is the 0.6 cap plus "cannot verify" being read as a reason to mark down, not detection: several plausible nature observations (herb garden, rock pool, window scene) went to 0.0 or 0.4 on "cannot be verified". The one real AI-internals piece (composition_0, "The system processed an incoming request...") went 1.0 -> 0.0, which is the intended catch.

## Reading
With a reference present the candidate makes the grounded half bite (wrong scene and invention fall, faithful holds). Without a reference, as in composition today (F-3635) and in this replay of the nature log, it cannot verify and pushes everything down, so it is not shippable as one text for both paths. Real-piece stability needs the cap not to depress scores to 0.0 (e.g. no-reference wording that scores concreteness without the "cannot verify" penalty, or a separate no-reference task) and a real reference in the nature replay (scene not logged). Composition needs the writer given the world (J-2945).
