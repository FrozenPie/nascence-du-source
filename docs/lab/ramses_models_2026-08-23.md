# Ramses model tier — first real numbers, 2026-08-23

*Four hubs stood up on Ramses (`deploy/ramses/`, see `NASCENCE_NOTES.md` for the standup log):
`falcon3:7b` (i9 CPU, `:11436`), `mixtral:8x7b` (i9 CPU, `:11438`), `granite3.1-moe:3b` (1650
Super, `:11437`), `command-r7b` (3070, `:11441`). Three tests run against the three that pass a
basic contract check: `judge16.py`, `station_bench.py` (all 8 stations), `lane2_model_lab.py`.
Du was stopped throughout — zero live effect.*

**`granite3.1-moe:3b` is excluded from everything below.** Antigravity's own contract benchmark
found it fails to close valid JSON on 4/5 calls (exhausts its token budget mid-structure) — not
worth scoring on anything until that's fixed (bigger budget or a smaller schema).

**Method note on latency:** `command-r7b`'s `station_bench` run overlapped in time with its
`lane2_model_lab` run on the same GPU — both hit the same hub concurrently. `nascence_cpu_server.py`
serializes calls (one inference at a time per process), so nothing crashed or corrupted, but every
`command-r7b` wall-clock number below is inflated by queueing behind the other job. Treat its
accuracy/format numbers as real; treat its timing as **not yet measured cleanly**.

---

## 1. ★ THE HEADLINE — mixtral is a genuinely better judge, confirmed twice; command-r7b is not

Judge-shaped tasks, three separate designs, same pattern both times a direct comparison exists:

| Test | falcon3:7b | mixtral:8x7b | command-r7b |
|---|---|---|---|
| `judge16` (16 balanced cases, discrimination gate) | 0.625 | **0.812** | 0.562 |
| `station_bench`'s own `judge` task | 0.5 | **0.75** | 0.5 |

Mixtral wins both. Command-r7b — the model picked specifically for training-lineage independence
— is tied-worst or worst on both. **Lineage diversity and judgement quality are separate axes.**
A model from an untried vendor is not automatically a better judge; on this evidence it's the
weakest of the three tested, despite being the one candidate expected to help most with the
decoupled-judge problem.

`falcon3:7b` and `command-r7b` were both tested on `judge16` once before, via ollama, prior to any
Ramses work: `falcon3:7b` scored 0.75 there, `command-r7b` scored 0.625. **Both dropped moving to
the actual llama.cpp serving stack** (falcon3 to 0.625, command-r7b to 0.562) — most likely
quantization/sampling differences between what ollama had pulled and what's loaded here (Q4_K_M).
Same lesson `mistral:7b-instruct` taught earlier this week from the other direction (passed the lab,
failed the platform outright): **a lab result does not transfer across a platform change, in either
direction** — sometimes it fails outright, sometimes it just quietly gets worse.

---

## 2. Synthesis coverage — none of the three beats what's already running for free

`synthesise`'s `coverage` metric is the one that caught `llama3.1:8b` being the worst integrator in
the 33-model matrix despite winning on throughput. Checked against the current production model for
this exact role:

| model | coverage | wall |
|---|---|---|
| `phi3:mini` (current production) | **0.71** | **1.9s** |
| `falcon3:7b` | 0.71 | 38.9s |
| `command-r7b` | 0.71 | 119.3s* |
| `mixtral:8x7b` | 0.62 | 24.7s |

Three-way tie at the incumbent's own score, and mixtral — the model specifically picked and
justified for this synthesis role on the strength of its MoE architecture — scores *worse* than
the 3.8B model it would replace. Latency is irrelevant either way (Deep Line synthesis stations run
on 600-2700s clocks), so this isn't a speed story: **there is no coverage-quality case for moving
this station off `phi3:mini` today.**

---

## 3. Format compliance — clean across the board (the good news)

All three held `json_ok = 1.0` on every one of the 8 `station_bench` stations. Zero format
failures anywhere — a real, useful confirmation that the llama.cpp serving stack itself is solid
for all three, distinct from `granite3.1-moe`'s budget problem and `mistral:7b-instruct`'s earlier
JSON-shell failure.

## 4. Per-station notes worth keeping

- **`predict` (falsifiability):** mixtral and command-r7b both 1.0 (genuinely committal, avoid
  hedging); falcon3 only 0.67.
- **`voice`:** falcon3 perfect variety (1.0); mixtral weaker variety (0.33); **command-r7b's
  first_person drops to 0.33** — a real, specific weakness, breaks character more than the others.
- **`author` (long-form):** all three undershoot the target length badly (falcon3 94 words,
  mixtral 165, command-r7b 221 — closest but still scored `length_achieved=0.0`). None is
  currently suited to long-form generation without real prompt/budget tuning.
- **`lane2_model_lab`** (command-r7b only so far — falcon3/mixtral not yet run through this one):
  scored 0.875 composite, second only to the incumbent `deepseek-r1:7b` (0.932) and ahead of every
  other prior candidate — but **`json_ok` was only 0.583** on Lane 2's actual prompt shape, nearly
  half its calls didn't produce valid JSON there specifically, despite passing cleanly everywhere
  else tested. A model can hold contract on one prompt shape and fail it on another — worth
  re-running falcon3/mixtral through this same lab for a fair three-way comparison.

---

## What actually changed my mind today

Going in, mixtral was pitched as the synthesis pick and command-r7b as the judge-diversity pick.
The data says the opposite pairing is closer to right: **mixtral is the stronger judge candidate**,
and **neither new model beats the free incumbent on synthesis**. Command-r7b's real, distinguishing
weaknesses (weakest judge of the three, worst JSON reliability on Lane 2's specific prompt, weakest
first-person consistency) haven't shown up as a strength anywhere yet.

## Not yet run

- `falcon3:7b` / `mixtral:8x7b` through `lane2_model_lab` (needs to wait for the i9 CPU hub to be
  free of other load, to avoid the same contamination `command-r7b`'s run suffered).
- A clean, uncontended re-run of `command-r7b`'s `station_bench` timing.
- `granite3.1-moe:3b`, at all, until its JSON-closing failure is addressed.
