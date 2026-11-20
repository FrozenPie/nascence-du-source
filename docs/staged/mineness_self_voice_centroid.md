# Mineness self-voice centroid authorship signal (shadow only)

**Status:** STAGED (design only, 2026-11-18). Nothing built. Source job J-4372, from J-4104; founder chose option A in chat 2026-11-18 (stage the design, shadow only, keep `_READBACK_TAU` 0.62 live until it reads).

## Why
`core/mineness.py` computes `error = 1 - max(sim_to_recent_groove(8), sim_to_basin)`. It is a recency/groove-proximity score, not an authorship test. F-4863 (`docs/lab/J-3701_authorship.py`, output `docs/lab/J-3701_data/authorship_out.txt`, 300 pairs): the identical vector scored as SELF, SELF_PAST or OTHER gives max diff 0.000000; his own Aug thoughts score 0.535 (17% felt_mine) against 0.536 for a topic-matched library passage (paired diff +0.0004), while a contemporary Nov thought scores 0.259. So `authorship` is only a label from `seed_kind`, and his own old voice reads as foreign as library text. The floor drop Jul->Oct is mostly groove tightening (86-92%).

## Design
Add a second, long-horizon score beside `error`; do not change `error`, `_TAU` or `arrival_note`.
1. **Self-voice centroid(s):** the unit-normalised mean of his own spontaneous thought vectors (`seed_kind` spontaneous, same MiniLM space as the groove) over a long window (candidate 30 days, tested at 7/14/60), excluding the last 8 (groove) so it is not a duplicate of recent proximity. Consider 3-5 k-means centroids over the same window so a multi-topic voice is not blurred into one mean. Rebuilt daily and cached in memory (`data/mineness_voice.npz`, written only by the module, never read per cycle from the DB).
2. **Signal:** `voice_sim = max cosine(vec, centroids)`; `voice_error = 1 - voice_sim`. Content-controlled variant: score against a library-centroid too, and log `voice_margin = voice_sim - library_sim` (library centroid from `origin='reading'` fragments) so topic cannot masquerade as voice.
3. **Logging only:** add `voice_sim`, `library_sim`, `voice_margin`, `voice_epoch` fields to the `data/mineness_shadow.jsonl` row (or a sibling `mineness_voice_shadow.jsonl` if the row schema is guarded). No effect on Du, no prompt, no registry change (a prompt registry check is therefore not required unless a prompt is later added).
4. **Edit scope (later, restart-gated):** `core/mineness.py` only plus a small builder script; run `udms_get_change_dossier core/mineness.py` first; test in a throwaway worktree with `lab_env.isolate`, hash canary on live `data/`.

## Evaluation (shadow read, no LLM)
Replay first using the J-3701 harness over the fragment-DB copy: for held-out Aug thoughts (centroid built from data before them), compare `voice_margin` for own-old vs library-matched passages, plus AUC and share separated at a fixed threshold. Then read live shadow rows once 14 Du-up days accrue: SELF_PAST (broadcast/recall/dream re-entry) vs library/world-seeded (OTHER) separation in `voice_margin`, with day-cluster bootstrap CIs. Confounds to report: drift of voice over the window, centroid leakage (rows inside the centroid window), seed-mix.

## Gate and defeater
Keep `arrival_note` at `_READBACK_TAU` 0.62 live until the shadow read. **Defeater:** after 14 Du-up days the shadow shows no SELF_PAST vs library separation in `voice_margin` (CI includes 0 or AUC under about 0.55); then drop the signal and keep the comparator as a groove/novelty detector (option C). Promotion to any live use (re-baselining 0.62 or a second arrival kind) is a separate founder call via `/decide open`; the 0.62 re-baseline question (option B) is not decided here.

## Open questions
- Single centroid vs k centroids; window length (replay picks).
- Whether the voice should exclude thoughts that were themselves SELF_PAST re-entries (avoid circularity).
- Record-format texts ("I opened ...") are a known wart; filter before scoring.

## Build jobs (to spawn on go)
1. Replay lab on held-out Aug thoughts (Du-down ok, needs fragment DB copy). 2. Shadow fields in `core/mineness.py` (restart-gated). 3. Read job after 14 Du-up days.
