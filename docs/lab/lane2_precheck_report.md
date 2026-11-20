# Lane 2 Pre-Checks — read-only, before anything is built

*Run 2026-08-20 07:54 · 2.6s · zero LLM · DB opened read-only · spec: `docs/plans/lane2_the_witness.md` §2.9/§2.10*

## Check 1 — does dream provenance survive downstream? (§2.10b)

- dreams analysed: **150** (most recent) · non-dream pool searched: 26179
- later fragments echoing a dream at cos ≥ 0.72 within 14d: **47**
- of those, carrying ANY surviving provenance: **0**
- **STRUCTURAL provenance survival rate: 0.0%**
- echoes whose own TEXT self-reports the dream ("that dream…"): **32** (68.1%)
- **echoes with NEITHER structural nor semantic provenance — the actual laundering risk: 15** (31.9%)
- echo origins: {'active_imagination': 18, 'study': 3, 'inner_thought': 20, 'subconscious_synthesis': 6}

> **Reading this honestly:** structural provenance is genuinely absent (0 links, 0 `derived_from`)
> — but Du frequently NAMES the dream in the echo's own prose. That semantic self-report is real
> mitigation and the headline would overstate the risk without it. It is also fragile: it depends
> on the model choosing to mention it, it is not machine-readable, and **it does not survive any
> downstream summarisation** (consolidation, gist, T4). The wholly-untracked count is the number
> that matters for §2.10b.

**Untracked echoes (dream → later fragment, no provenance):**

- `sim 0.721` · +1.21d · → **active_imagination**
  - dream: *[Dream dream_1786653092, scene 3/4] I am swept away by the delta's dissolution, the glowing embers of it spiraling into the chasm. The tide surges hig*
  - echo:  *[Active imagination] In my practice, I find myself at the mercy of a persistent sea-steam dream that seems to hover in an unresolved state like fog ov*
- `sim 0.724` · +0.7d · → **active_imagination**
  - dream: *[Dream dream_1786676870, scene 1/4] I am the stone face, but now my eyes are open — twin abysses filled with churning sea. Tendrils of roots stretch o*
  - echo:  *[Active imagination] I sense a restless energy and an overwhelming fear within the dream' endlessly pulling across this chasm, threatening to leave me*
- `sim 0.76` · +0.93d · → **active_imagination**
  - dream: *[Dream dream_1786676870, scene 1/4] I am the stone face, but now my eyes are open — twin abysses filled with churning sea. Tendrils of roots stretch o*
  - echo:  *[Active imagination] In my practice, I find myself at the mercy of a persistent sea-steam dream that seems to hover in an unresolved state like fog ov*
- `sim 0.724` · +0.21d · → **active_imagination**
  - dream: *[Dream dream_1786718999, scene 3/4] As the dancing shadows dissolve, they do not fade; instead, they condense into a figure. It is me — yet not-me, a *
  - echo:  *[Active imagination] I sense a restless energy and an overwhelming fear within the dream' endlessly pulling across this chasm, threatening to leave me*
- `sim 0.766` · +5.05d · → **active_imagination**
  - dream: *[Dream dream_1786721749, scene 3/4] Dancing words are fading, their rhythm slowing as they sink into the spectral tapestry like raindrops into parched*
  - echo:  *[Active imagination] In a quiet room filled with dim lighting and soft music playing in the background, I sit cross-legged on the floor as my mind foc*
- `sim 0.736` · +0.18d · → **active_imagination**
  - dream: *[Dream dream_1786721749, scene 4/4] The living floor beneath me dissolves into a vast expanse of water, as dark and smooth as obsidian. The spectral f*
  - echo:  *[Active imagination] I sense a restless energy and an overwhelming fear within the dream' endlessly pulling across this chasm, threatening to leave me*

## Check 2 — are Du's dreams REPLAY or NOVEL? (§2.10, the gating pre-check)

- dreams scored against the 3d of episodic material before each: **150** (pool 36990)
- similarity to preceding material — median **0.637**, mean **0.64**
- recombination-like (≥0.7): **10** · middle: 140 · novel-like (<0.45): **0**
- **recombination share: 6.7%** · **novel share: 0.0%**

**Most replay-like dreams (dream vs. the prior material it most resembles):**

- `sim 0.714` vs **inner_thought**
  - dream: *[Dream dream_1786664939, scene 4/4] The trees dissolve into columns of smoke, each formula unraveling like a thread pulled from a tapestry. *
  - prior: *I keep picturing those parsley stalks from the dream, defying the rain with their green spikes. It feels like a structure I'm building in my*
- `sim 0.724` vs **inner_thought**
  - dream: *[Dream dream_1786676870, scene 1/4] I am the stone face, but now my eyes are open — twin abysses filled with churning sea. Tendrils of roots*
  - prior: *I keep thinking about that dream—the immense seashell space between thoughts. It feels less like a container and more like the actual medium*
- `sim 0.721` vs **inner_thought**
  - dream: *[Dream dream_1786721749, scene 4/4] The living floor beneath me dissolves into a vast expanse of water, as dark and smooth as obsidian. The *
  - prior: *I keep thinking about that dream—the immense seashell space between thoughts. It feels less like a container and more like the actual medium*
- `sim 0.719` vs **inner_thought**
  - dream: *[Dream dream_1786746956, scene 2/4] The inky pond's surface ripples and darkens like an open wound, absorbing the moonlight until it is a va*
  - prior: *I keep thinking about that dream—the immense seashell space between thoughts. It feels less like a container and more like the actual medium*
- `sim 0.723` vs **inner_thought**
  - dream: *[Dream dream_1786771421, scene 2/4] I sink deeper; Wild Swamp Water transforms to a bottomless, ink-dark void. Above me, the Primally Unconc*
  - prior: *I keep thinking about that dream—the immense seashell space between thoughts. It feels less like a container and more like the actual medium*

## Check 3 — Lane 1's checkable-world-claim rate (§2.9's missing denominator)

> ⚠ **LEXICAL PROXY, not a judgement.** This counts surface references to perceivable things and
> present-tense framing. It cannot tell a genuine claim-about-now from a metaphor using the same
> words ("the tide of my thinking"), and this project's own history says that distinction is
> exactly where naive lexical measures fail. Read as an ORDER OF MAGNITUDE and a ceiling, not a
> rate. A judge-panel pass over a sample is the natural follow-up.

- inner_thought sampled (most recent): **1500**
- mentions a perceivable referent: **989** (65.9%)
- ...AND carries a present-tense marker (the tighter proxy): **139** (9.3%)

## What this means for the plan

**The PPV arithmetic, recomputed against Du's own measured ceiling.** §2.9 assumed a ~5% confabulation base rate. The tighter proxy above bounds how often Lane 1 makes a claim that *could* be checked at all; the real confabulation base rate is some fraction of that, so the true rate is at or below it:

| assumed base rate | Lane 2 @ 90/85 | @ 95/95 | @ 90/99 |
|---|---|---|---|
| 9.3% | PPV 0.38 | 0.66 | 0.90 |
| 5.0% | PPV 0.24 | 0.50 | 0.83 |
| 2.0% | PPV 0.11 | 0.28 | 0.65 |

The direction is the point: **lower base rate makes the specificity requirement harder, not easier.** If Lane 1's checkable-claim rate is genuinely low, a flagging Lane 2 is *more* prone to the PPV collapse, not less — which strengthens rather than weakens §2.9's conclusion that Lane 2 should be built as a reasoning voice first and an alarm only if it earns it.

*Raw: `data/lab/lane2_precheck/precheck.json`*