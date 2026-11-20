# prompt_manager: audit round 1 dispositions (2026-11-14)

> Moved out of `docs/staged/prompt_manager.md` section 10 to keep the plan under the 40 KB cap. Unedited.

## Audit round 1: questions and dispositions

Auditors: Gemini (pasted into session 2026-11-14) and GPT (full text saved at `C:\AISaves\# Prompt Manager — independent crit.txt`).
Per the pasted-review-provenance note, both are outside reviews and are treated as inputs, not rulings.

| Q | Gemini | GPT | Disposition in v2 |
|---|---|---|---|
| 1 Evidence for P0/P1 alone | Yes; observability gap is critical | Yes, with conditions; telemetry is traceability, not causality | Adopted. P0 approved; P1 conditional. |
| 2 Gates | Add a soak time; relax vocabulary-indistinguishability to schema+length | 30% firing is weak (exposure, not influence); split into safety / equivalence / effectiveness; replace-vs-rotate | Adopted GPT's structure plus Gemini's 14-day soak (6.6). |
| 3 Tiering | T0 pinned; a T2 that dictates structure must be promoted and frozen | Classify by operational consequence; allow multiple tags | Both adopted (6.5). |
| 4 Metrics | n-gram proxies resist Goodhart; no LLM diversity metric | Linguistic diagnostics only; add semantic/longitudinal as research; split frustration/circling; do not optimise topic count | GPT adopted; **Gemini's Goodhart claim not adopted** (section 8). |
| 5 No-hints / authorship | Travis authors T2 variants directly; LLM drafts risk assistant idioms | Claude may draft structural lines; three roles; founder essential for affect/attention/identity/Travis-branch | **Unresolved; founder decision** (11, Q2). |
| 6 Judge | Scripted checks primary; LLM only for binary equivalence | Layered: scripted, independent semantic review, human; different family is not independence; no LLM sole authority; none needed for P1 | Adopted (6.6, 6.7). |
| 7 condensed_thought | Sequence: fix twin first | Sequence; record D-0633 tail as its own revision | Adopted (P1 gate). |
| 8 idle_executive_plan | Table is "database", renderer is "view" | Division of responsibility; manager owns wording and provenance only, not orchestration or budget | Adopted; ownership table in 12. |
| 9 Registry check | Sibling script | Extend the registry check; avoid two commands that can disagree; validate that no unregistered construction path remains | **Unresolved; founder decision** (11, Q6). |
| 10 Harness timing | Build early for the noise floor | Build incrementally; noise floor yes, full framework no | Adopted GPT's P2a/P2b split. |
| 11 (GPT) Can exact experimental conditions be reconstructed (dynamic content, ordering, truncation, inference config)? | — | New question; "more important than where the Table lives" | Added as the central acceptance question; 6.2, 6.4, P0/P1 exit criteria. |

**Additions adopted from GPT beyond the ten questions:** identity model (6.1); assembly hash and execution fingerprint (6.2); prompt lineage
(6.2); replacement vs rotation (6.3); reconstruction vs replay (6.4); change ledger (8); historical reconstruction, migration by
priority, template/data/assembly separation, privacy/retention (6.1, 6.2, 9); and the caution to verify R1–R11 before any claim rests on them.
**Research caveat carried forward (GPT 7.5):** R1 supports prompt sensitivity, not rotation; R3 needs logprobs on our lanes; R7 is about
a different generation procedure; R9 needs its evaluation setup read; R11 needs benchmarking on our own servers. P0/P1 do not depend on any of these.

---

