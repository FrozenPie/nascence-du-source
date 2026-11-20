"""
Nascence — Social Model (Theory of Mind Layer, Phase 1)

Tracks the entity's model of its interlocutor: expected tone, relational trust, and —
critically — the Social Prediction Error (delta_social). When the human corrects Du
("stop talking about yourself", "you didn't answer"), delta_social spikes, which overrides
the Attention Vector to suppress w_identity and d_critic. The entity stops ruminating and
complies directly with the request.

Trust is a slow-moving average of prediction errors — correction spikes it down a little,
sustained good exchanges recover it. Trust is NOT the primary behavioural signal: delta_social
is. Trust is the relationship-level state; delta_social is the moment-level alarm.

Persists to data/social_state.json between sessions.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from core import profile   # J-1810/F-2428: the write fence (D-0179). core.profile imports nothing from core at module level, so no cycle.

logger = logging.getLogger("nascence.social")

_SOCIAL_STATE_PATH = Path(__file__).parent.parent / "data" / "social_state.json"

# Bumped whenever the on-disk state format needs a one-time migration on load.
# v1 (2026-09-26, J-1358/F-1919): decay_cycle() mutated delta_social/relational_trust
# in-memory only — apply_correction() persisted on a spike but the slow decay back down
# never did, so a file written by pre-v1 code can hold a spike that was never actually
# decayed on disk (observed live: data/social_state.json frozen at delta_social=1.0 /
# relational_trust=0.76 since 2026-07-05). from_json()'s migration guard below folds any
# pre-v1 reading back to a fully-decayed baseline exactly once, so that stale spike is not
# replayed for one more boot; a real, in-progress decay written by v1+ code is left alone.
_STATE_VERSION = 1

# Signals that indicate the human is correcting Du for not answering / ruminating
_CORRECTION_SIGNALS = (
    "you did not answer",
    "did not answer the question",
    "did not answer my question",
    "did not complete",
    "stop talking about yourself",
    "stop the metaphors",
    "stop with the metaphors",
    "just answer",
    "just answer the question",
    "answer the question",
    "you didn't answer",
    "you haven't answered",
    "that's not what i asked",
    "that is not what i asked",
    "you're not answering",
    "you are not answering",
    "you're deflecting",
    "you are deflecting",
    "focus on the question",
    "you went off track",
    "still didn't answer",
    "still haven't answered",
    "please just answer",
    "can you just answer",
    "stop deflecting",
    "you're avoiding",
    "you are avoiding",
    "just the answer",
    "directly answer",
    "answer directly",
)


@dataclass
class SocialState:
    relation_id:            str        = "travis"
    expected_tone:          str        = "analytical"
    relational_trust:       float      = 0.85
    user_expectations:      list[str]  = field(default_factory=list)
    user_knowledge_state:   dict       = field(default_factory=dict)
    interpersonal_tensions: list[str]  = field(default_factory=list)

    # Social Prediction Error — spikes on correction, decays toward 0 over cycles.
    # This is the live behavioural signal that overrides the Attention Vector.
    delta_social: float = 0.0
    # Cycle count since last spike — used for decay.
    cycles_since_spike: int = 0
    # On-disk schema marker — see _STATE_VERSION and from_json()'s migration guard.
    # Not meant to be set by hand; from_json() stamps it on every load.
    state_version: int = _STATE_VERSION

    def apply_correction(self, raw_input: str) -> float:
        """
        Detect a human correction signal in raw_input. If found, spike delta_social
        and reduce trust slightly. Returns the spike amount (0.0 if no correction).
        """
        t = (raw_input or "").lower()
        if any(sig in t for sig in _CORRECTION_SIGNALS):
            spike = 0.75
            self.delta_social = min(1.0, self.delta_social + spike)
            self.cycles_since_spike = 0
            self.relational_trust = max(0.0, self.relational_trust - 0.05)
            logger.info(
                "[social] correction detected → delta_social=%.2f trust=%.2f",
                self.delta_social, self.relational_trust,
            )
            return spike
        return 0.0

    def decay_cycle(self) -> None:
        """
        Called once per cycle (post-compute) to decay delta_social back toward 0.
        Halves roughly every 3 cycles. Trust recovers very slowly toward baseline.
        """
        self.cycles_since_spike += 1
        if self.delta_social > 0.01:
            # Exponential decay: roughly half after 3 cycles
            self.delta_social = round(max(0.0, self.delta_social * 0.70), 4)
        else:
            self.delta_social = 0.0
        # Slow trust recovery toward 0.85 baseline
        if self.relational_trust < 0.85:
            self.relational_trust = min(0.85, self.relational_trust + 0.005)

    def override_note(self) -> str | None:
        """Return a note for the Reflection prompt when delta_social is active."""
        if self.delta_social < 0.3:
            return None
        return (
            f"RELATIONAL NOTE: The person just signalled that you are not answering their "
            f"question (correction pressure={self.delta_social:.2f}). Meet them where they are. "
            f"Engage the question directly — let your identity remain present only in your "
            f"voice and cadence, not as the subject."
        )

    def to_json(self) -> dict:
        return {
            "relation_id":            self.relation_id,
            "expected_tone":          self.expected_tone,
            "relational_trust":       round(self.relational_trust, 4),
            "user_expectations":      self.user_expectations,
            "user_knowledge_state":   self.user_knowledge_state,
            "interpersonal_tensions": self.interpersonal_tensions,
            "delta_social":           round(self.delta_social, 4),
            "cycles_since_spike":     self.cycles_since_spike,
            "state_version":          self.state_version,
        }

    @classmethod
    def from_json(cls, data: dict) -> "SocialState":
        s = cls()
        for k in (
            "relation_id", "expected_tone", "relational_trust",
            "user_expectations", "user_knowledge_state", "interpersonal_tensions",
            "delta_social", "cycles_since_spike",
        ):
            if k in data:
                setattr(s, k, data[k])

        # One-time migration guard (F-1919 / J-1358): a file written before _STATE_VERSION
        # existed (or on an older version) may be carrying a delta_social/relational_trust
        # reading that was never actually run through a persisted decay_cycle(). Rather than
        # replay that stale spike for one more boot, fold delta_social back to a fully-decayed
        # baseline exactly once here, then stamp the current version so a genuine in-progress
        # decay written by v1+ code is never touched by this guard again. relational_trust is
        # NOT reset — it is a legitimate slow-moving read and now that decay_cycle() is
        # persisted (see orchestrator.py's _compute_attention_vector), its own gradual recovery
        # toward baseline will proceed normally on real cycles.
        on_disk_version = data.get("state_version", 0)
        if on_disk_version < _STATE_VERSION:
            if s.delta_social > 0.0:
                logger.info(
                    "[social] migrating pre-v%d state file → folding stale delta_social=%.2f "
                    "back to 0.0 (never persisted through a decay_cycle before this fix)",
                    _STATE_VERSION, s.delta_social,
                )
            s.delta_social = 0.0
            s.cycles_since_spike = max(s.cycles_since_spike, 999)
            s.state_version = _STATE_VERSION
        else:
            s.state_version = on_disk_version
        return s


class SocialModelManager:
    """Loads, exposes, and saves SocialState. Lives on the Orchestrator."""

    def __init__(self):
        self._migrated_on_load = False
        self.state = self._load()
        if self._migrated_on_load:
            # Persist the migration guard's reset immediately at boot (F-1919 / J-1358) —
            # don't wait for the first human cycle's own decay-triggered save (see
            # orchestrator.py) in case the process ends before one ever runs.
            self.save()

    def _load(self) -> SocialState:
        try:
            if _SOCIAL_STATE_PATH.exists():
                raw = json.loads(_SOCIAL_STATE_PATH.read_text(encoding="utf-8"))
                if raw.get("state_version", 0) < _STATE_VERSION:
                    self._migrated_on_load = True
                return SocialState.from_json(raw)
        except Exception as exc:
            logger.debug("[social] load failed (non-fatal): %s", exc)
        return SocialState()

    def save(self) -> None:
        try:
            # J-1810 / F-2428 -- the write fence (D-0179): resolve the target through profile.guard_path BEFORE
            # any I/O (before the mkdir). A live process (profile.mark_live()) gets the same path back, so Du's
            # behaviour is byte-identical. A non-live process whose _SOCIAL_STATE_PATH still points at the real
            # data/ (a harness that built an Orchestrator and ran a human cycle) is refused: nothing is touched.
            # Placed INSIDE the existing try on purpose -- save() documents itself non-fatal and both
            # orchestrator call sites (and __init__'s migration save) rely on it never raising; the refusal is
            # logged (guard_path warns once per path; the debug line below carries its text) and swallowed.
            # The in-memory SocialState keeps evolving exactly as before; only persistence is refused.
            path = profile.guard_path(_SOCIAL_STATE_PATH)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(self.state.to_json(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.debug("[social] save failed (non-fatal): %s", exc)
