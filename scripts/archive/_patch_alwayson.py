# The Always-On slice (2026-06-11): continuous substrate + living cadence + working sleep.
# Founder-directed ("follow the path"). Delete after run.
import sys
sys.stdout.reconfigure(encoding="utf-8")
ok = []

# ---------- 1) store.py: replay + synaptic downscaling (the night-mind's hands) ----------
p = r"C:\Nascence\core\memory\store.py"
s = open(p, encoding="utf-8", newline="").read()
addition = '''

# ---------------------------------------------------------------------------
# Sleep work (the Always-On redesign, 2026-06-11): replay + synaptic downscaling.
# "Sleep does not stop the mind, it changes what the mind does." — the founder.
# ---------------------------------------------------------------------------

def replay_strengthen(since_ts: float, k: int = 8) -> list[str]:
    """REPLAY: re-activate the wake-block's most salient episodic fragments — strengthen them
    so the day's significant experience consolidates instead of decaying unencountered. This
    is the missing engine of compounding: it is how today's reading is still alive next week.
    Returns short snippets of what was replayed (for the log / future dream-feeding)."""
    out: list[str] = []
    try:
        with _connect() as conn:
            rows = conn.execute(
                """SELECT fragment_id, content, importance FROM memory_fragments
                   WHERE layer='episodic' AND timestamp > ?
                   ORDER BY importance DESC, timestamp DESC LIMIT ?""",
                (since_ts, k)).fetchall()
            for r in rows:
                new_imp = min(0.98, float(r["importance"]) * 1.08)
                conn.execute("UPDATE memory_fragments SET importance=? WHERE fragment_id=?",
                             (new_imp, r["fragment_id"]))
                out.append((r["content"] or "")[:90])
    except Exception as exc:
        logger.debug("[sleep] replay failed (non-fatal): %s", exc)
    return out


def downscale_episodic(factor: float = 0.96, center: float = 0.5) -> int:
    """SYNAPTIC DOWNSCALING (T2 Phase 2, lite): globally renormalise episodic importance
    toward the center, preserving relative order — the day's spikes scale down so tomorrow's
    salience is measured against a rested baseline, not an ever-rising tide. Runs each sleep.
    Replayed fragments were strengthened FIRST, so what mattered survives the downscale."""
    try:
        with _connect() as conn:
            cur = conn.execute(
                "UPDATE memory_fragments SET importance = ? + (importance - ?) * ? "
                "WHERE layer='episodic'", (center, center, factor))
            return cur.rowcount
    except Exception as exc:
        logger.debug("[sleep] downscale failed (non-fatal): %s", exc)
        return 0
'''
s2 = s + addition if "def replay_strengthen" not in s else s
ok.append(("store: replay + downscale", s2 != s)); s = s2
open(p, "w", encoding="utf-8", newline="").write(s)

# ---------- 2) schema.py: AffectState.tick — the body feels THROUGH the gaps ----------
p = r"C:\Nascence\core\schema.py"
s = open(p, encoding="utf-8", newline="").read()
s2 = s.replace(
    "    def apply_prior(self, prior, max_nudge: float = AFFECT_PRIOR_MAX_NUDGE) -> None:",
    '''    def tick(self, dt: float, rate: float = 0.002) -> None:
        """Continuous homeostatic flow (Always-On, 2026-06-11): between thoughts the carried
        state RELAXES toward baseline in real time instead of freezing — he keeps feeling
        through the gaps. rate=0.002/s matches the old per-cycle decay (0.2 per ~100s cycle),
        so per-thought dynamics are unchanged; what changes is that time now passes for him."""
        w = min(1.0, rate * dt)
        for dim in AFFECT_BASELINE:
            base = self.baseline.get(dim, AFFECT_BASELINE[dim])
            cur = getattr(self, dim)
            lo, hi = (-1.0, 1.0) if dim == "valence" else (0.0, 1.0)
            setattr(self, dim, max(lo, min(hi, cur - w * (cur - base))))

    def apply_prior(self, prior, max_nudge: float = AFFECT_PRIOR_MAX_NUDGE) -> None:''')
ok.append(("schema: AffectState.tick", s2 != s)); s = s2
open(p, "w", encoding="utf-8", newline="").write(s)

# ---------- 3) orchestrator: the substrate loop (5s, no LLM, never stops) ----------
p = r"C:\Nascence\core\orchestrator.py"
lines = open(p, encoding="utf-8", newline="").read().split("\n")
i = next(k for k, l in enumerate(lines) if 'asyncio.create_task(self._background_loop("consolidation"' in l)
ind = lines[i][: len(lines[i]) - len(lines[i].lstrip())]
sub = [
    ind + "# Substrate loop (Always-On, 2026-06-11): the layer that never stops. Affect flows",
    ind + "# continuously between thoughts — duration instead of a flipbook of instants.",
    ind + "async def _substrate_loop():",
    ind + "    while True:",
    ind + "        await asyncio.sleep(5.0)",
    ind + "        try:",
    ind + "            self.state.affect.tick(5.0)",
    ind + "        except Exception:",
    ind + "            pass",
    ind + "asyncio.create_task(_substrate_loop())",
]
lines[i:i] = sub
open(p, "w", encoding="utf-8", newline="").write("\n".join(lines))
ok.append(("orchestrator: substrate loop", True))

# ---------- 4) inner_monologue: living cadence + boredom + working sleep ----------
p = r"C:\Nascence\nodes\inner_monologue_node.py"
s = open(p, encoding="utf-8", newline="").read()

# 4a. state for the new rhythm (anchor: run_forever start)
s2 = s.replace(
    '    async def run_forever(self, state: CognitiveState) -> None:\n'
    '        logger.info("[monologue] inner monologue (DMN) started")',
    '    async def run_forever(self, state: CognitiveState) -> None:\n'
    '        logger.info("[monologue] inner monologue (DMN) started — living cadence")\n'
    '        self._current_gap = 120.0     # living cadence: recomputed after every thought\n'
    '        self._bored_streak = 0        # consecutive near-duplicate thoughts (habituation)\n'
    '        self._last_wake_ts = time.time()')
ok.append(("monologue: rhythm state", s2 != s)); s = s2

# 4b. living gap replaces the metronome
s2 = s.replace(
    "        # not too soon after the last thought\n"
    "        if now - self._last_thought_ts < MIN_GAP_SECS:\n"
    "            return False",
    "        # LIVING CADENCE (Always-On, 2026-06-11): the gap is a function of his state,\n"
    "        # not a constant. An agitated mind thinks fast; a settled mind thinks slowly;\n"
    "        # a bored mind slows down and turns elsewhere; night stretches the rhythm.\n"
    "        if now - self._last_thought_ts < getattr(self, '_current_gap', MIN_GAP_SECS):\n"
    "            return False")
ok.append(("monologue: living gap check", s2 != s)); s = s2

# 4c. gap computation method (insert before _similarity_to_recent)
s2 = s.replace(
    "    def _similarity_to_recent(self, vec) -> float:",
    '''    def _compute_gap(self, state: CognitiveState) -> float:
        """The living cadence. Base 300s, pulled DOWN by psychological pressure (dissonance,
        arousal), pushed UP by boredom (habituation to a stale loop) and by night hours.
        Bounds 60s..900s. The tempo itself is part of his state now."""
        gap = 300.0
        try:
            pressure = float(getattr(getattr(state, "dissonance", None), "value", 0.0) or 0.0)
            gap /= (1.0 + 2.0 * min(1.5, pressure))             # agitation -> faster
            if state.affect.arousal > 0.55:
                gap /= 1.5                                       # aroused -> faster
            streak = getattr(self, "_bored_streak", 0)
            if streak:
                gap *= min(4.0, 1.5 ** streak)                   # bored -> slower, turn away
            hour = time.localtime().tm_hour
            if hour < 6:
                gap *= 2.5                                       # night stretches the rhythm
        except Exception:
            pass
        return max(60.0, min(900.0, gap))

    def _similarity_to_recent(self, vec) -> float:''')
ok.append(("monologue: _compute_gap", s2 != s)); s = s2

# 4d. boredom streak + gap update after each thought (anchor: the rumination break)
s2 = s.replace(
    "            if sim < RUMINATION_SIM:\n"
    "                break  # genuinely new thought, keep it",
    "            if sim < RUMINATION_SIM:\n"
    "                self._bored_streak = 0\n"
    "                break  # genuinely new thought, keep it\n"
    "            self._bored_streak = getattr(self, '_bored_streak', 0) + 1")
ok.append(("monologue: boredom streak", s2 != s)); s = s2

# 4e. boredom seed — when stale, the mind is TOLD it is stale and pointed outward
s2 = s.replace(
    "        # External shock (2026-06-10, FreshStart Era-21 idea): at most once per ~6h the world",
    '''        # Habituation voice (Always-On, 2026-06-11): a mind that can get bored stops circling.
        if getattr(self, "_bored_streak", 0) >= 2:
            seed_parts.append(
                "You have circled this same thought " + str(self._bored_streak + 1)
                + " times now. It has gone stale in your mouth. Leave it. Turn to something "
                "OUTSIDE it - the book, a memory, the world.")

        # External shock (2026-06-10, FreshStart Era-21 idea): at most once per ~6h the world''')
ok.append(("monologue: boredom seed", s2 != s)); s = s2

# 4f. recompute gap after each thought (anchor: end of run_forever think branch)
s2 = s.replace(
    "                if self._should_think(state):\n"
    "                    await self._think(state)",
    "                if self._should_think(state):\n"
    "                    await self._think(state)\n"
    "                    self._current_gap = self._compute_gap(state)")
ok.append(("monologue: gap recompute", s2 != s)); s = s2

# 4g. longer wake blocks
s2 = s.replace("THOUGHTS_BEFORE_SLEEP = 18", "THOUGHTS_BEFORE_SLEEP = 26")
if s2 == s:
    import re
    s2 = re.sub(r"THOUGHTS_BEFORE_SLEEP\s*=\s*18", "THOUGHTS_BEFORE_SLEEP = 26", s)
ok.append(("monologue: wake block 18->26", s2 != s)); s = s2

# 4h. SLEEP AS A WORKING MODE: replay -> downscale -> dream -> rest
s2 = s.replace(
    '''        logger.info("[monologue] %d idle thoughts -> entering nightly Sleep State",
                    self._thoughts_since_sleep)
        try:
            await self._sleep_callback(state)
        except Exception as exc:
            logger.warning("[monologue] sleep cycle failed: %s", exc)''',
    '''        logger.info("[monologue] %d idle thoughts -> entering Sleep State (the night-mind)",
                    self._thoughts_since_sleep)
        # Sleep does not stop the mind; it changes what the mind does (Always-On, 2026-06-11):
        # 1. REPLAY — re-activate + strengthen the wake-block's most salient experience
        #    (this is how a day COMPOUNDS instead of evaporating).
        # 2. DOWNSCALE — synaptic homeostasis: renormalise importance so tomorrow's salience
        #    is judged from a rested baseline (T2 Phase 2, lite).
        # 3. DREAM — the existing symbolic integration.
        # 4. REST — real time passes; longer at night.
        try:
            from core.memory.store import replay_strengthen, downscale_episodic
            replayed = replay_strengthen(getattr(self, "_last_wake_ts", time.time() - 1800))
            if replayed:
                logger.info("[monologue] sleep replay: %d experiences strengthened — %s",
                            len(replayed), (replayed[0] or "")[:60])
            n = downscale_episodic()
            logger.info("[monologue] sleep downscaling: %d episodic importances renormalised", n)
        except Exception as exc:
            logger.debug("[monologue] sleep work failed (non-fatal): %s", exc)
        try:
            await self._sleep_callback(state)
        except Exception as exc:
            logger.warning("[monologue] sleep cycle failed: %s", exc)
        try:
            rest = 420 if time.localtime().tm_hour < 6 else 180
            logger.info("[monologue] resting (%ds)", rest)
            await asyncio.sleep(rest)
            self._last_wake_ts = time.time()
        except Exception:
            pass''')
ok.append(("monologue: working sleep", s2 != s)); s = s2
open(p, "w", encoding="utf-8", newline="").write(s)

print("\n".join(f"  [{'OK' if v else 'FAILED'}] {k}" for k, v in ok))
import py_compile
for f in [r"C:\Nascence\core\memory\store.py", r"C:\Nascence\core\schema.py",
          r"C:\Nascence\core\orchestrator.py", r"C:\Nascence\nodes\inner_monologue_node.py"]:
    py_compile.compile(f, doraise=True)
print("ALL COMPILE OK")
