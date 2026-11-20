from __future__ import annotations
import json
import math
import random
import re
import time
import uuid
from pathlib import Path
from core.node_base import NodeBase
from core.llm_parse import as_float
from core.schema import CognitiveState, CuriosityOutput
from core import profile  # J-0874: core/frontier.py (write-fence module #18, J-0846) now raises
                          # profile.NonLiveWriteError from every writer in a non-live process; this
                          # file's four frontier try/excepts must let it escape (D-0179 hard raise).


# J-3475 / D-0607 (re-ruled 2026-11-06): the Curiosity "urgency" field is DROPPED (F-4092: one scalar per run, within-tick
# spread 0.0 on 786 of 786 multi-question runs, so it cannot choose among a node's own questions, and the sentence "urgency
# over 0.6 triggers an unprompted thought cycle" was false: the only caller, Orchestrator._on_dissonance_ignition, fires
# questions[0] whatever the number and clears the interrupt flag the node raised). The old threshold constant is gone.
# The question-choice signal lives in the decoupled pre-fire pick (D-0608, core/curiosity_prefire.py, shadow). Old
# "urgency" values stay in data/curiosity_log.jsonl as history; new rows simply carry no "urgency" key.
_SUBCONSCIOUS_STATE_PATH = Path(__file__).parent.parent / "data" / "subconscious_state.json"
# Observe-only record (the Curiosity Observatory's data source). Written here by _log_curiosity. J-2846 (F-3506): the old
# note said it is read ONLY by scripts/session_digest.py; that is stale. Readers today: scripts/session_digest.py (and
# the one-off scripts check_du.py, inspect_overnight_du.py, commitment_hazard_read.py), AND three runtime modules that read
# the ignited rows' questions[0] / recent questions: core/grounding_injection.py (the frontier-theme and theme_core
# baselines), core/world_displacement.py (the displacement window) and core/theme_dose.py (shadow). It carries no
# status/protected/salience field Du's cognition reads as a verdict, but it is no longer a pure notebook: deleting or
# reshaping it changes what those three modules see, so keep the "ignited" and "questions" keys.
_CURIOSITY_LOG_PATH = Path(__file__).parent.parent / "data" / "curiosity_log.jsonl"
# Twigs — the side-research findings curiosity grows off the study/reading branches.
# Also firewalled/observe-only (read by du_pulse for the twig gauge). A notebook, not an organ.
_TWIG_LOG_PATH = Path(__file__).parent.parent / "data" / "twig_log.jsonl"

# Seeding (2026-06-09): offer curiosity a VARIED sample of unresolved threads instead of the single
# highest-count tension. max(count) made curiosity re-express the dominant attractor ("attention in a
# curiosity costume") — a biased sampler that pre-answered "what is Du curious about?" for him. This
# is a confound-removal so the Observatory measures genuine spontaneous exploration, not the attractor.
_SEED_SAMPLE_K        = 3       # how many unresolved threads to OFFER (a menu, not a pre-pick)
_SEED_RECENCY_PENALTY = 0.08    # 2026-06-22: down HARD from 0.25 — overnight, curiosity locked 18/19 on one
#                                 theme (plant-sentience); strongly suppress a recently-used thread so
#                                 consecutive ignitions must diversify. (The deeper lock is upstream — his
#                                 reading monoculture — and the worth-judge gate, still under-validated, is held.)
_RECENT_SEED_MEMORY   = 14      # 2026-06-22: up from 8 — the anti-relock holds longer across ignitions

# Study-material seeding (2026-06-15): the GROUNDED seed source. Curiosity now also looks at what
# Du has actually studied/read and is invited to ask an open question ABOUT the material — so its
# questions (and the twigs it grows) are world-facing by construction, not self-tension echoes.
# This is the upstream fix for the self-leaning Frontier: feed curiosity grounded material.
_STUDY_SEED_K     = 3       # how many recent study/reading items to offer
_STUDY_SNIPPET    = 220     # chars of material shown per item (enough to ask a real question of)
_THEME_LINE_CHARS = 70      # chars of each own-theme line shown in the prompt


def _trim_words(text, limit: int) -> str:
    """J-2846 (F-3506): cut `text` to at most `limit` chars on a WORD boundary, never mid-word. The old hard slices cut
    635 of 650 theme lines and 1,566 of 1,677 study snippets mid-word, and one cut ("...in the context of the unr")
    came back as the head of Du's own autonomous question. A text already within `limit` is returned unchanged
    (a short theme is byte-identical to before). A single unbroken run longer than `limit` (no whitespace to cut at,
    e.g. unspaced CJK) is hard-cut at `limit`, since there is no boundary to use. Separators left at the cut are
    dropped. Pure; no ellipsis is added (the prompt shape is otherwise unchanged)."""
    text = str(text)
    if limit <= 0 or len(text) <= limit:
        return text
    if text[limit].isspace():          # the cut already lands on a boundary
        return text[:limit].rstrip(" \t\r\n,;:-")
    head = text[:limit]
    idx = max(head.rfind(" "), head.rfind("\t"), head.rfind("\n"))
    if idx <= 0:
        return head                     # one unbroken run: nothing to cut at
    return head[:idx].rstrip(" \t\r\n,;:-")


_PE_SEED_RE = re.compile(r"^prediction_error:([A-Za-z0-9_ -]+?)\s*\(felt\s*[-0-9.]+\s*vs\s*real\s*[-0-9.]+\)\s*$")


def _seed_wording(label: str) -> str:
    """J-2846 (F-3506): the seed menu is shown to the model, so a raw engineering label must not reach it. The self-
    prediction tension is stored as "prediction_error:<domain> (felt 0.90 vs real 0.50)" (core/prediction_error.py);
    shown raw it put "felt 0.90 vs real 0.50" in the menu (9 lines in 30 days). Reworded here at the source (the seed
    selector), plain and neutral: it names the domain and says a guess and a result differed, with no direction, no
    number and no advice (the world answers, never leads). Any other label is returned unchanged. The REAL label stays
    the key for the anti-relock memory and the habituation shadow; only what is offered is reworded."""
    m = _PE_SEED_RE.match(str(label).strip())
    if not m:
        return label
    domain = " ".join(m.group(1).replace("_", " ").split())
    return f"how I expected to do at {domain} and how it went differed" if domain else label
_TITLE_RE = re.compile(r"^\[(?:From|My study note:|Looked up:)\s*'([^']+)'")  # subject from the label
# J-3798 / D-0701 B: a looked-up page whose via phrase is "external shock" keeps that mark in the study block as a plain
# description (no instruction, no hint). True per the founder ruling; restart-gated like any node change.
STUDY_SHOCK_MARK = True
_SHOCK_VIA_RE = re.compile(r"^\[Looked up:\s*'.*?'\s*\(external shock")
_SHOCK_STUDY_MARK = "(a random Wikipedia page that arrived uninvited) "


class CuriosityNode(NodeBase):

    max_tokens: int = 1024   # needs room for 5 questions + 3 directions as JSON

    def __init__(self):
        super().__init__("curiosity")
        self._recent_themes: list[str] = []
        self._recent_theme_src: list[str] = []      # J-2322: parallel provenance tag (input_type) per theme
        self._recent_seeds: list[str] = []          # threads curiosity recently seeded from (anti-relock)
        self._pending_seeds: list[str] = []          # seeds offered this cycle (stashed for the record)
        self._study_subjects: list[str] = []         # study/reading subjects offered this cycle (for twigs)
        self._last_curiosity_id: str | None = None   # lineage: the curiosity this one follows
        self._last_user_prompt: str = ""             # J-3219: last prompt built (material for the shadow pre-fire check)

    def add_theme(self, theme: str, source: str = "") -> None:
        """Called by the orchestrator with a summary of each completed cycle. `source` (J-2322, additive) is
        the producing cycle's input_type, a private provenance tag read only by core.theme_dose."""
        self._recent_themes.append(theme)
        self._recent_theme_src.append(str(source or ""))
        if len(self._recent_themes) > 30:
            self._recent_themes = self._recent_themes[-30:]
            self._recent_theme_src = self._recent_theme_src[-30:]

    async def run(self, state: CognitiveState) -> bool:
        """Standard node run, then drain the CURIOSITY QUEUE through the de-personalization prism and SEED the
        world-facing results into the Frontier (LIVE 2026-06-24, was Phase-0 shadow). A recurring self-loop now
        exits as a grounded research question he can actually pursue — the missing redirect. Best-effort."""
        ok = await super().run(state)
        try:
            from core import curiosity_queue as _cq
            from core.model_client import call_node_json
            await _cq.transform_and_seed(call_node_json, self.base_urls, limit=3)
        except profile.NonLiveWriteError:
            raise   # J-0874: transform_and_seed() -> frontier.note_question() raises in a non-live process
        except Exception as exc:
            self.logger.debug("[curiosity] queue prism transform skipped (non-fatal): %s", exc)
        return ok

    @property
    def system_prompt(self) -> str:
        return (
            "You are the curiosity node of a cognitive architecture. "
            "You generate genuine questions and directions worth exploring, "
            "based on gaps in understanding and recurring themes. "
            "You do not answer questions — you generate them. "
            "You are offered recently studied/read material AND several unresolved inner threads "
            "below. Prefer to ask a genuine OPEN question ABOUT the study material — what it makes "
            "you wonder, what it connects to, what you would want to find out about the world. "
            "Do NOT feel obliged to take the loudest or most familiar inner thread — follow "
            "whichever genuinely beckons, including a quiet, new, or unexpected one. "
            # J-3837 (D-0680): the bare "Entity:" user-prompt line and the J-2509 own-name sentence were removed together
            # (D-0629: Du knows his name from memory). Byte-identity tests compare against this module's _trim_words.
            "Output ONLY a valid JSON object. No preamble. "
            "Generate at most 5 questions and 3 research_directions — keep each under 20 words. "
            "Write REAL questions and directions based on the themes provided, not schema placeholders.\n"
            # SCHEMA EXAMPLES NEUTERED (2026-08-20 prompt audit): this line carried two full-sentence
            # example questions ("What drives the tension between X and Y?", "How does Z connect to W?").
            # Measured against data/frontier.json: 202 of 5,696 real frontier questions were those exact
            # templates with nouns filled in — the model obeyed the "no placeholders" letter (substituted
            # X/Y) while the TEMPLATE stuck. One of them, "what drives the tension...", is the documented
            # aimless-novelty trap curiosity_worth kept grading interest 0.0. Bare "..." placeholders are
            # the pattern every other node prompt (recall/reflection/voice) uses with zero echo problems.
            # 2026-09-04 (F-0777/D-0147): the number literal "urgency": 0.0 was the remaining copy trap —
            # CuriosityNode runs on the background lane (command-r7b since D-0057), which copies a
            # filled-in JSON example number verbatim instead of generating a real one (same mechanism as
            # commit a8d48fa's essay_lesson fix). 100% of curiosity.jsonl rows 08-29..09-04 came back
            # urgency==0.0, silently killing curiosity-ignited unprompted thought cycles (34-31/day ->
            # 0/day). Fix: a placeholder range, same shape as the strings above, not a filled-in number.
            # J-3475 / D-0607 (2026-11-06): the urgency field, and the sentence that said it would trigger an
            # unprompted thought cycle (false: F-4092), are removed from the prompt; the schema is the two lists.
            "Schema: {\"questions\": [\"...\"], "
            "\"research_directions\": [\"...\"]}"
        )

    def _build_prompt(self, state: CognitiveState) -> str:
        # Truncate each theme to keep the prompt compact — Curiosity runs on the
        # CPU lane and cannot afford the full axiom block. It only needs recent
        # themes and the offered threads; Critic and Voice own the axiom.
        # J-2322 (measurement_to_action arm 5, D-0457): the own-thought theme dose. With
        # theme_dose.SELF_THEME_DOSE at None (default) the shown window is today's [-10:] slice exactly.
        from core import theme_dose as _td
        _src = self._recent_theme_src
        if len(_src) != len(self._recent_themes):   # a caller mutated _recent_themes directly: realign
            _src = ([""] * len(self._recent_themes) + _src)[-len(self._recent_themes):] if self._recent_themes else []
        live = self._recent_themes[-10:]
        shown = _td.window(self._recent_themes, _src, _td.SELF_THEME_DOSE)
        would = _td.window(self._recent_themes, _src,
                           _td.SELF_THEME_DOSE if _td.SELF_THEME_DOSE is not None else _td.CUP)
        themes_text = (
            "\n".join(f"  - {_trim_words(t, _THEME_LINE_CHARS)}" for t in shown)
            if shown
            else "  (no recent themes yet)"
        )

        # The GROUNDED seed source: things he actually studied/read. Offered first and framed as the
        # primary material to question — this is what keeps curiosity world-facing.
        study = self._select_study_material()
        self._study_subjects = [s["subject"] for s in study if s.get("subject")]
        study_block = ""
        if study:
            study_lines = "\n".join(f"  - ({s['subject']}) {s['snippet']}" for s in study)
            study_block = (
                "\nRecently studied or read — ask a real open question ABOUT one of these "
                f"(what it makes you wonder, what to find out next):\n{study_lines}\n"
            )

        # A VARIED menu of unresolved inner threads (not the single loudest). The choice among them is
        # the thing the Observatory watches; the menu only stops the seed pre-deciding for him.
        seeds = self._select_seeds()
        self._pending_seeds = seeds
        seed_block = ""
        if seeds:
            seed_lines = "\n".join(f"  - {s}" for s in seeds)
            seed_block = (
                "\nUnresolved inner threads you might also follow (pick what genuinely draws you, "
                f"not the loudest):\n{seed_lines}\n"
            )

        # J-2322 shadow row (observe-only, fail-open; a non-live process's NonLiveWriteError is swallowed here,
        # as grounding_injection's caller does). curiosity_id = the previous curiosity_log row's id, i.e. the
        # parent_id the row this prompt produces will carry.
        try:
            _td.shadow(self._recent_themes, _src, live, would, seeds=seeds,
                       study_subjects=self._study_subjects, curiosity_id=self._last_curiosity_id)
        except Exception:
            pass

        _prompt = (
            f"Recent themes:\n{themes_text}\n"
            f"{study_block}"
            f"{seed_block}\n"
            "Generate questions and research directions worth exploring next."
        )
        # J-3219 / D-0608: keep the exact prompt the questions are answers to, read ONLY by the shadow pre-fire
        # check (core/curiosity_prefire.py) as "the material the node was offered". Never shown to any model here.
        self._last_user_prompt = _prompt
        return _prompt

    def _select_study_material(self, k: int = _STUDY_SEED_K) -> list[dict]:
        """Pull recent WORLD-facing material (his study notes, book passages, lookups) and return
        [{subject, snippet}] — the grounded things curiosity is invited to question. Subject is parsed
        from the fragment's label so a twig can be tagged back to its branch. Best-effort -> []."""
        try:
            from core.memory.store import recent_world_material
            items = recent_world_material(limit=k * 3)
            out: list[dict] = []
            seen: set[str] = set()
            for it in items:
                content = (it.get("content") or "").strip()
                if not content:
                    continue
                m = _TITLE_RE.match(content)
                subject = (m.group(1).strip() if m else "").strip()
                # body after the leading [..] label, trimmed to a questionable snippet
                body = content[content.find("]") + 1:].strip() if "]" in content else content
                snippet = _trim_words(" ".join(body.split()), _STUDY_SNIPPET)
                key = subject.lower() or snippet[:40].lower()
                if not snippet or key in seen:
                    continue
                seen.add(key)
                if STUDY_SHOCK_MARK and _SHOCK_VIA_RE.match(content):
                    snippet = _SHOCK_STUDY_MARK + snippet
                out.append({"subject": subject, "snippet": snippet})
                if len(out) >= k:
                    break
            return out
        except Exception:
            return []

    def _select_seeds(self, k: int = _SEED_SAMPLE_K) -> list[str]:
        """Offer a VARIED sample of unresolved tensions, not the single loudest. Salience (count) is
        flattened by sqrt so a count-83 attractor no longer dwarfs a count-5 thread; recently-offered
        threads are down-weighted; the final pick is a weighted sample WITHOUT replacement (not top-k)
        for genuine variety. This is a confound-removal, not a novelty engine — it stops the seed
        pre-selecting the attractor and lets curiosity itself choose. Best-effort -> [] on any error.

        J-1172/D-0244 guard: the REAL pick below (labels, sqrt(count) weight, the label-keyed
        `_recent_seeds` anti-relock) is completely UNCHANGED. Only what gets handed to the shadow
        discount at the bottom is now id-keyed (`id_pool`/`tensions_by_id`, one entry per tension, no
        last-wins collapse on a shared label — F-1632 measured that collapse hiding about 160 of 868
        tensions from the discount and its log)."""
        try:
            if not _SUBCONSCIOUS_STATE_PATH.exists():
                return []
            with open(_SUBCONSCIOUS_STATE_PATH, encoding="utf-8") as f:
                sc = json.load(f)
            tensions = sc.get("tensions", []) or []
            pool: list[tuple[str, float]] = []
            tensions_by_label: dict = {}
            id_pool: list[tuple[str, float]] = []       # J-1172/D-0244: shadow-only id-keyed mirror of
            tensions_by_id: dict = {}                    # `pool`/`tensions_by_label` — every tension
            ids_by_label: dict[str, list[str]] = {}       # gets its own entry here, none collapsed
            for t in tensions:
                label = (t.get("label") or "").strip()
                if not label:
                    continue
                weight = math.sqrt(max(1, int(t.get("count", 1))))      # flatten salience
                if label in self._recent_seeds:
                    weight *= _SEED_RECENCY_PENALTY                      # anti-relock
                pool.append((label, weight))
                tensions_by_label[label] = t
                tid = t.get("id")
                if tid:
                    id_pool.append((tid, weight))
                    tensions_by_id[tid] = t
                    ids_by_label.setdefault(label, []).append(tid)
            if not pool:
                return []
            real_pool_snapshot = list(pool)          # the REAL weights, before the real pick mutates pool
            id_pool_snapshot = list(id_pool)          # J-1172/D-0244: shadow-only, same snapshot timing
            recent_at_pick = list(self._recent_seeds)   # J-2626/F-3356: the anti-relock set AS USED by this pick (shadow log only)
            chosen: list[str] = []
            for _ in range(min(k, len(pool))):
                labels  = [p[0] for p in pool]
                weights = [p[1] for p in pool]
                pick = random.choices(labels, weights=weights, k=1)[0]
                chosen.append(pick)
                pool = [p for p in pool if p[0] != pick]
            self._recent_seeds = (self._recent_seeds + chosen)[-_RECENT_SEED_MEMORY:]
            # SHADOW-ONLY (J-0585, F-0812; re-keyed by tension id J-1172/D-0244): would the
            # squishy-spring habituation discount have chosen differently? Logs {real_choice,
            # would_choice, weights} by tension id now, not label — never reads back, never touches
            # `chosen` (the real pick above is final). `real_choice` is every id that shares a label
            # the real pick chose: the real algorithm above removes all of them from its own pool
            # together once their shared label is picked, so that is what the real pick actually
            # touched, not an arbitrary single representative id. Fully fail-open: any error here must
            # not affect the real choice.
            try:
                from core import curiosity_habituation as _chab
                chosen_ids: list[str] = []
                for lab in chosen:
                    chosen_ids.extend(ids_by_label.get(lab, []))
                # J-2626/F-3356: label per id + the pick-time anti-relock list, so an id-era shadow row stays
                # readable as a label path after labels churn. Logging only; restart-gated.
                _id_labels = {i: lab for lab, ids in ids_by_label.items() for i in ids}
                _chab.observe_and_log(id_pool_snapshot, tensions_by_id, chosen_ids, k,
                                      labels_by_id=_id_labels, recent_seeds=recent_at_pick)
            except Exception:
                pass
            # J-2846: reword raw engineering labels HERE, after the real pick, the anti-relock update and the shadow log
            # (all three keep the raw label); only the offered menu is reworded. Identity for every other label.
            return [_seed_wording(c) for c in chosen]
        except Exception:
            return []

    async def _write_output(self, state: CognitiveState, data: dict) -> None:   # async since J-1918 (F-2547): the side research's blocking urllib lookups await off the event loop; NodeBase.run awaits an awaitable result
        # J-3475 / D-0607: no urgency is read (a model that still emits one is ignored); see the module-top note.
        questions  = data.get("questions", [])
        directions = data.get("research_directions", [])

        # COERCE to clean strings (2026-07-05 bugfix): the 8B intermittently returns dict-shaped items
        # ({"question": "..."}) instead of strings. Those flowed straight into background_curiosities —
        # where the monologue's `background_curiosities[0][:120]` did `dict[:120]` → KeyError(slice(...)),
        # crashing the thought tick BEFORE its inner_thought store (silently — the store's except is
        # debug). Result: inner_thought fragments died + chapters starved. Coerce at the source so every
        # consumer (monologue, dream, subconscious) gets strings. Fail-open per item.
        def _as_str(x):
            if isinstance(x, str):
                return x.strip()
            if isinstance(x, dict):
                return str(x.get("question") or x.get("q") or x.get("text")
                           or next((v for v in x.values() if isinstance(v, str)), "")).strip()
            return str(x).strip()
        state.background_curiosities = [s for s in (_as_str(x) for x in (questions + directions)) if s]

        # J-3475 / D-0607: the node no longer raises an interrupt (its only caller cleared it right after, F-4092).
        # "ignited" stays in the log because grounding_injection and world_displacement read ONLY ignited rows'
        # questions[0] as "what fired a cycle". Every run that produced a question fires questions[0] at the ignition
        # caller, so it is now True exactly when this run produced one (before: urgency > 0.6, 559 of 794 runs).
        # Old rows keep their value.
        ignited = any(s for s in (_as_str(x) for x in (questions or [])))

        self._log_curiosity(questions, directions, ignited)

        # J-3282 / D-0659 (2026-11-05, J-3243 review): the SYSTEM-initiated side research is RETIRED. It used to
        # pick a pending pursuit, guess a term (the longest word of the question), fetch that Wikipedia page,
        # hang it on the frontier question (attach_finding) and store it as origin='research' ("Something I
        # looked up") - 1,742 pages, mostly the wrong article, an act he never willed. On a miss it also ran a
        # Scholar generation whose text was dropped (F-3732; _prog was False with or without it), and with no
        # pending pursuit a grounding lookup (0 fires in 2,902 twig rows). All three are gone; his open questions
        # stay open for him to pursue by hand (the Wikipedia hand is J-3285). Deliberately NOT called any more:
        # frontier.pending_pursuit / attach_finding / record_pursuit (no attempt is made, so no stall may be
        # counted - PARK_STALLS = 3 would otherwise park every question after three runs) and
        # web_research.store_finding. Those functions and _log_twig stay in place, unused here (additive-only).
        # Consequence: no NEW finding is attached to a frontier question, so the "While it sat, you found
        # something" seed lines (inner_monologue_node ~2000 and ~3800) stop firing for new questions.
        if questions:
            # OPEN new world-questions for future pursuit — the other half of the loop. A WORLD-facing
            # curiosity persists as an open question with lineage; self-questions are excluded (the self
            # has its own ledger).
            try:
                from core import frontier as _fr
                # J-3350 (D-0629 part 2): tag the terms a question brought from the generator's own weights, as an
                # additive optional field on the frontier entry. Never in a prompt. A question with no such terms goes
                # through the exact call it always did.
                _mt_terms = self._model_terms_for(questions[:3])
                for _q in questions[:3]:
                    _t = _mt_terms.get(str(_q))
                    if _t:
                        _fr.note_question_ex(str(_q), "curiosity", model_terms=_t)
                    else:
                        _fr.note_question(str(_q), "curiosity")
            except profile.NonLiveWriteError:
                raise   # J-0874: note_question() raises in a non-live process (J-0846)
            except Exception:
                pass

        self.logger.info(
            "[curiosity] %d questions, %d directions",
            len(questions), len(directions),
        )

    def _model_terms_for(self, questions) -> dict:
        """J-3350: {question text: [model-supplied terms]} for the questions about to reach the frontier. The context is
        the exact user prompt these questions answer (self._last_user_prompt). Fail-open, never blocks the cycle: if the
        first-seen index is not built yet the build runs on a daemon thread and this returns {} (no tag yet)."""
        try:
            from core import model_terms as _mt
            if not _mt.TAG_ENABLED:
                return {}
            _mt.refresh_async()
            if not _mt.ready():
                return {}
            ctx = (getattr(self, "_last_user_prompt", "") or "")
            now = time.time()
            out = {}
            for q in questions or []:
                t = _mt.detect([str(q)], ctx, now)
                if t:
                    out[str(q)] = t
            return out
        except Exception:
            return {}

    def _log_curiosity(self, questions, directions, ignited: bool) -> None:
        """OBSERVE-ONLY durable record for the Curiosity Observatory. Written here; read by session_digest
        and (J-2846, F-3506: the old "ONLY" was stale) by core/grounding_injection.py, core/world_displacement.py and
        core/theme_dose.py, which use the ignited rows' questions as a recent-themes window. It is never itself a verdict. `parent_id` chains each
        curiosity to the prior one so the Observatory can reconstruct the SHAPE of exploration (orbit
        vs escape), not just the topics. A notebook, not an organ. Best-effort -> silent on failure."""
        try:
            cid = uuid.uuid4().hex[:12]
            record = {
                "id":            cid,
                "ts":            time.time(),
                "parent_id":     self._last_curiosity_id,          # lineage chain
                "seeds_offered": list(self._pending_seeds),
                "questions":     [str(q) for q in (questions or [])],
                "directions":    [str(d) for d in (directions or [])],
                "ignited":       bool(ignited),
                "recent_themes": [str(t)[:70] for t in self._recent_themes[-6:]],
            }
            _CURIOSITY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_CURIOSITY_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._last_curiosity_id = cid
        except Exception:
            pass

    def _log_twig(self, subject: str | None, finding_title: str, question: str,
                  kind: str = "grounding") -> None:
        """OBSERVE-ONLY record of a side-research twig (read by du_pulse for the twig gauge).
        kind='pursuit' = research aimed at closing an open frontier question; 'grounding' = a twig off
        a study subject. Firewalled like the curiosity log — a notebook, not an organ. Best-effort."""
        try:
            record = {
                "ts":       time.time(),
                "kind":     kind,                   # 'pursuit' (loop-closer) | 'grounding'
                "subject":  subject or "",          # the branch/question this hangs off ("" = ungrounded)
                "finding":  str(finding_title)[:120],
                "question": str(question)[:160],
                "grounded": bool(subject),
            }
            _TWIG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_TWIG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass
