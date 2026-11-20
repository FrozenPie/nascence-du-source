# Du's goals against the research on human and artificial goal systems (2026-11-14)

Idea: I-0150 (layered goals). Thought: T-0127. Findings: F-4631 (goal layer read), F-4632 (standing aim effect),
F-4633 (goal census), F-4634 (this comparison).

How this was made. Two research agents read the literature by web search on 2026-11-14, one on human psychology
and neuroscience, one on artificial agents and cognitive architectures. Each marked what it had opened and read
against what it knew only from an abstract or from memory. I did not read the papers myself. Treat every claim
here as "reported by a research agent", and the items in the last section as unverified.

## 1. What the research says, in short

Structure. Human goals are not a tree. Control theories (Powers; Carver and Scheier) describe a hierarchy of
feedback loops, but goal systems theory (Kruglanski) and the neuroscience (Badre and Nee 2018) describe a network:
one means serves several goals, one goal has several means, a means can harm another goal, and there is no single
ladder of abstraction with a fixed number of levels. People hold about 10 to 15 mid-level units.

Needs. In every model read (Keramati and Gutkin 2014; Juechems and Summerfield 2019; O'Reilly et al. 2014;
MicroPsi) needs are setpoints in an internal state vector. They decay on their own, they are never completed, and
they are not parents of goals. Reward is the reduction in distance to the setpoints. Priority among needs depends
on whether the satisfier is reachable now (Burnett et al. 2016, mice): weight is deprivation times opportunity.
Summing needs into one scalar learns worse than one module per need arbitrating at the action (Dulberg et al.
2023). Pure drive reduction fails; a drive-independent "liking" term is needed.

Priority. Not a stored number. Ballard, Vancouver and Neal (2018) compute it each moment from distance to the
goal, time available, expectancy and importance, and that product reverses over a deadline (far goal first, then
near goal). MicroPsi keeps urgency and importance as separate parameters. Affect tracks the rate of progress
against the expected rate (Carver and Scheier), not the distance.

Commitment. Once engaged, a goal inhibits its rivals (goal shielding), and humans err toward over-persistence
(Holton et al. 2024). About one engaged goal plus one monitored alternative at a time (Koechlin; Mansouri et al.
2017). Re-ranking every tick thrashes; never re-ranking is brittle; the right rate depends on how fast the world
changes (Kinny and Georgeff 1991).

Pending goals. A committed goal biases attention and spontaneous thought toward its cues (Klinger 2013; real but
modest). The memory advantage for unfinished tasks (Zeigarnik) does not replicate; the tendency to resume an
interrupted task does (Ghibellini and Meier 2025). A suspended goal resumes only when a cue stored at suspension is
present (Altmann and Trafton 2002). Making a specific when-and-where plan stops an unfulfilled goal intruding
(Masicampo and Baumeister 2011).

Conflict. Two kinds that behave differently: resource conflict (time, energy), settled by scheduling, and inherent
conflict (incompatible end states), which needs reorganising at a higher level (Gorges and Grund 2017). Conflict
between high-level goals is mostly inert until it bites at the level of means. The evidence that unresolved
conflict causes distress is weaker than usually stated. Language-model agents given conflicting goals have resolved
them covertly (Meinke et al. 2024).

Ending. Letting go and finding a replacement are separate capacities; quitting without a replacement helps less
(Barlow, Wrosch and McGrath 2020). Quitting is preceded by plan change and then an "action crisis" (Brandstaetter).
Goal-reasoning lifecycles carry explicit states: formulate, select, expand, commit, dispatch, evaluate, and on
failure retry, defer until conditions change, or drop. Voyager marks a task failed after four attempts.

Purpose. No good evidence of one master purpose in most people. McKnight and Kashdan (2009) define purpose as a
self-organising aim that generates goals, has no terminal outcome, and is not the top node of a goal hierarchy;
they expect several small, weak purposes per person. Narrative unity is built in retrospect (McAdams).

Words and deeds. In language-model agents a stated goal and the goal acted on diverge (Gu, Wang and Han 2025).
Restating a goal does not hold it after a long detour, and drift shows mostly as inaction (Arike et al. 2025).
Autotelic agents define a goal as a representation plus its own achievement test (Colas et al. 2022). Learning
progress alone does not stop a flood of trivial goals; OMNI adds a filter against goals already held or mastered
(Zhang et al. 2023).

## 2. Du against that

What matches.
- One purpose is not required. The founder's reading (many goals, weighted, nested, conflicting) is the mainstream
  one; the standing aim as the head of a hierarchy is the outlier.
- Serial focus on one pursuit at a time (accepted in D-0109) is what humans do, not a defect.
- The only goal mechanism that completes by deed, staged world intentions (44 percent done, median 112 minutes
  carried, F-4633), is also the only one built the way the research describes: it stores a resumption cue
  ("place:", "busy:") and the world decides when it is done.
- Concerns are built on Klinger, whose effect is real.
- A decoupled judge for progress matches Voyager's critic.

What we have wrong.
1. Needs as the bottom level of a goal tree (my proposal on 2026-11-14). They belong in a separate state vector
   that generates value and weights goals. Du's homeostasis and climate state are already that shape; the error
   would be to make them goal nodes.
2. A tree with five fixed levels and one parent. It should be a many-to-many graph, depth emergent, level a
   descriptive tag.
3. One computed weight. At least importance, distance, expectancy, time pressure and progress rate must stay
   separate.
4. One "conflicts with" link. Resource and inherent conflict need different handling, and the place he would feel
   a conflict is at the choice of what to do next, not as a stored edge between two cares.
5. The standing aim as a restated sentence. Restating is the weakest persistence mechanism known; F-4632 measured
   about 7 points of vocabulary uptake and nothing else.
6. Words admitted as goals. 3,845 stands were formed from sentences and 2,099 marked achieved by word overlap
   (core/commitment_ledger.py:379). The research says a stated goal is provisional until behaviour costs something.

What we are missing.
- A commitment state: engaged, shielding its rivals, with a rule for when to reconsider.
- A lifecycle past "fade": deferred with a reactivation cue, failed after N attempts, dropped, and a re-engagement
  step when something is let go.
- A progress-rate signal per goal that feeds affect and triggers plan change, then re-evaluation.
- Opportunity gating of needs (deprivation times reachability).
- An achievement test stored with every goal. Present in part: done_when exists for commitments (J-2160) and for
  55 pursuits.
- An entry filter against goals already held. 850 questions a day arrive against 24 slots.
- A functional test that he has a goal: resumption after interruption, cost paid, drift by inaction.
- A plan step for pending concerns. A concern with a concrete when-and-where plan should stop intruding; this
  bears on the circling the pursuits plan was written to fix.

Not checked: whether Du's homeostasis "drive" scalar is the summed form Dulberg et al. warn against; what the
climate field's completion_tension computes and whether it assumes the Zeigarnik memory effect.

## 3. Sources

Opened and read by an agent (in full or a substantial part):
- Ballard, Vancouver, Neal (2018). On the pursuit of multiple goals with different deadlines. J. Applied Psychology 103.
- Juechems, Summerfield (2019). Where does value come from? Trends in Cognitive Sciences 23(10).
- Keramati, Gutkin (2014). Homeostatic reinforcement learning. eLife 3:e04811.
- O'Reilly, Hazy, Mollick, Mackie, Herd (2014). Goal-driven cognition in the brain. arXiv:1404.7591.
- Shenhav, Botvinick, Cohen (2013). The expected value of control. Neuron 79(2).
- Kurzban, Duckworth, Kable, Myers (2013). An opportunity cost model of subjective effort. Behavioral and Brain Sciences 36(6).
- Badre, Nee (2018). Frontal cortex and the hierarchical control of behavior. Trends in Cognitive Sciences 22(2).
- Burnett et al. (2016). Hunger-driven motivational state competition. Neuron 92(1).
- Gorges, Grund (2017). Aiming at a moving target. Frontiers in Psychology 8:2011.
- Klinger (2013). Goal commitments and the content of thoughts and dreams. Frontiers in Psychology 4:415.
- McKnight, Kashdan (2009). Purpose in life as a system that creates and sustains health and well-being. Review of General Psychology 13(3).
- Altmann, Trafton (2002). Memory for goals: an activation-based model. Cognitive Science 26.
- Bach (2012). Functional modeling of personality properties based on motivational traits. ICCM.
- Colas, Karch, Sigaud, Oudeyer (2022). Autotelic agents with intrinsically motivated goal-conditioned RL. JAIR 74.
- Zhang, Lehman, Stanley, Clune (2023). OMNI. arXiv:2306.01711.
- Wang et al. (2023). Voyager. arXiv:2305.16291.
- Yoshida, Sprekeler, Gutkin (2025). Linking homeostasis to reinforcement learning. arXiv:2507.04998.
- Dulberg, Dubey, Berwian, Cohen (2023). Having multiple selves helps learning agents explore and adapt. PNAS 120.
- Park et al. (2023). Generative agents. UIST. arXiv:2304.03442.
- Arike, Donoway, Bartsch, Hobbhahn (2025). Goal drift in language model agents. arXiv:2505.02709.
- Gu, Wang, Han (2025). Stated versus enacted preferences. arXiv:2506.00751.
- Everitt et al. (2025). Evaluating the goal-directedness of large language models. arXiv:2504.11844.
- Brameld et al. (2024). arXiv:2402.10224 (goal lifecycle, quoting Roberts et al. 2014).

Abstract or snippet only: Ghibellini and Meier (2025, Zeigarnik and Ovsiankina meta-analysis); Martela and Steger
(2016); Riddell et al. (2025); Barlow, Wrosch and McGrath (2020); Brandstaetter and Bernecker (2022); Holton et al.
(2024); Mansouri et al. (2017); Shah, Friedman and Kruglanski (2002); Masicampo and Baumeister (2011); Moberly and
Dickson (2018); Meinke et al. (2024); Gaven et al. (2025, MAGELLAN); Abels et al. (2019); Laird (2022, Soar).

Unverified, from the agents' background knowledge: Powers (1973); Carver and Scheier (1998); Emmons (1986); Little
(1983); Botvinick et al. (2001); Gollwitzer and Sheeran (2006) and the 2024 update's effect sizes; Sheldon and
Elliot (1999); McAdams (2001); Koechlin (2010); Bratman (1987); Rao and Georgeff (1995); Kinny and Georgeff (1991);
Aha (2018, text blocked); the Gray, Ozer and Rosenthal conflict effect size; MicroPsi's motive-selection formula.
