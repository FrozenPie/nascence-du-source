# World-loop wiring: research + study + shocks + latch + labels + prune + tasks. Delete after run.
import sys
sys.stdout.reconfigure(encoding="utf-8")
ok = []

# 1) curiosity: when it fires, LOOK IT UP — the world answers the question
p = r"C:\Nascence\nodes\curiosity_node.py"
s = open(p, encoding="utf-8", newline="").read()
s2 = s.replace(
    "        self._log_curiosity(questions, directions, urgency, ignited)",
    """        self._log_curiosity(questions, directions, urgency, ignited)

        # Web research (ported from Buddha, 2026-06-10): a fired curiosity now gets to ASK THE
        # WORLD, not only itself. Targeted on the top question's most specific word; a miss falls
        # through to serendipity (Buddha's 40% mode, deliberately preserved). The finding lands as
        # an origin='research' fragment — retrievable by the very internal cycle this ignition
        # starts. Fail-open: no network, no finding, no harm.
        if questions:
            try:
                from core import web_research as _wr
                got = _wr.lookup(_wr.term_from_question(questions[0]))
                if got:
                    _title, _extract = got
                    _wr.store_finding(_title, _extract, via=f"curiosity: {questions[0][:60]}")
                    self.logger.info("[curiosity] world answered: '%s'", _title)
            except Exception:
                pass""")
ok.append(("curiosity -> web research", s2 != s)); s = s2
open(p, "w", encoding="utf-8", newline="").write(s)

# 2) monologue: loosen the book latch + study note after reading + external shocks
p = r"C:\Nascence\nodes\inner_monologue_node.py"
s = open(p, encoding="utf-8", newline="").read()
s2 = s.replace(
    '            if "OPEN THE BOOK" in thought.upper():',
    '            _tl = thought.lower()\n'
    '            # Loosened latch (2026-06-10): he said "sitting with the open book" and "I want\n'
    '            # to know what the story is" for four hours and never tripped the exact phrase —\n'
    '            # a poet was asked to shout a shell command. Want, expressed naturally, now acts.\n'
    '            if any(w in _tl for w in ("open the book", "open it and read", "read the book",\n'
    '                                      "read on", "rather read", "want to read",\n'
    '                                      "pick up the book", "return to the book")):')
ok.append(("book latch loosened", s2 != s)); s = s2
s2 = s.replace(
    """                if got:
                    title, passage = got
                    logger.info("[monologue] he chose to READ: %s", title)
                    thought = (f"I opened '{title}' and read on. "
                               f"What stays with me: {passage[:220]}...")
                    about = f"reading {title}\"""",
    """                if got:
                    title, passage = got
                    logger.info("[monologue] he chose to READ: %s", title)
                    thought = (f"I opened '{title}' and read on. "
                               f"What stays with me: {passage[:220]}...")
                    about = f"reading {title}"
                    # The Study (2026-06-10): reading may leave a WORK behind — his own note
                    # about the book (a tablet: real file + retrievable fragment). His note,
                    # in his words, about the WORLD — the output half of the reading loop.
                    try:
                        note = await call_node_json(
                            self.base_urls,
                            "You are writing a private study note in your own voice about a "
                            "passage you just read. Be concrete about WHAT THE TEXT SAYS — "
                            "observations, facts, what struck you about the subject itself. "
                            "This is scholarship, not self-reflection. Output ONLY valid JSON. "
                            "Schema: {\\"note_title\\": \\"short title about the subject\\", "
                            "\\"note\\": \\"4-6 sentences about the passage's content\\"}",
                            f"The passage, from '{title}':\\n{passage[:2400]}",
                            max_tokens=400, temperature=0.5,
                        )
                        if note.get("note"):
                            from core.study import write_tablet
                            tp = write_tablet(note.get("note_title", title), note["note"], source=title)
                            if tp:
                                logger.info("[monologue] study tablet written: %s", tp.name)
                    except Exception as exc:
                        logger.debug("[monologue] study note failed (non-fatal): %s", exc)""")
ok.append(("study note after reading", s2 != s)); s = s2
# shocks: inject into the seed assembly (anchor: the open-book offer block we added earlier)
s2 = s.replace(
    "        # The open book (autonomous reading, 2026-06-10): he may CHOOSE to read instead",
    """        # External shock (2026-06-10, FreshStart Era-21 idea): at most once per ~6h the world
        # interrupts the idle mind, uninvited — the one input he cannot have generated himself.
        try:
            from core.web_research import maybe_shock
            _shock = maybe_shock()
            if _shock:
                seed_parts.append(
                    "Uninvited, from the world outside (you did not choose this): '"
                    + _shock[0] + "' — " + _shock[1][:260])
        except Exception:
            pass

        # The open book (autonomous reading, 2026-06-10): he may CHOOSE to read instead""")
ok.append(("external shocks in idle mind", s2 != s)); s = s2
open(p, "w", encoding="utf-8", newline="").write(s)

# 3) schema: labels for the new origins
p = r"C:\Nascence\core\schema.py"
s = open(p, encoding="utf-8", newline="").read()
s2 = s.replace(
    '            "reading":               "A book I am reading (ANOTHER author\\'s words — not my own writing)",',
    '            "reading":               "A book I am reading (ANOTHER author\\'s words — not my own writing)",\n'
    '            "study":                 "My own study note (my work, about the world)",\n'
    '            "research":              "Something I looked up (external fact — Wikipedia)",')
ok.append(("origin labels", s2 != s)); s = s2
open(p, "w", encoding="utf-8", newline="").write(s)

# 4) store: prune-protect all world-material
p = r"C:\Nascence\core\memory\store.py"
s = open(p, encoding="utf-8", newline="").read()
s2 = s.replace("ORDER BY (origin = 'reading') ASC, importance ASC, timestamp ASC",
               "ORDER BY (origin IN ('reading','study','research')) ASC, importance ASC, timestamp ASC")
ok.append(("prune protects world-material", s2 != s)); s = s2
open(p, "w", encoding="utf-8", newline="").write(s)

print("\n".join(f"  [{'OK' if v else 'FAILED'}] {k}" for k, v in ok))
import py_compile
for f in [r"C:\Nascence\nodes\curiosity_node.py", r"C:\Nascence\nodes\inner_monologue_node.py",
          r"C:\Nascence\core\schema.py", r"C:\Nascence\core\memory\store.py",
          r"C:\Nascence\core\web_research.py", r"C:\Nascence\core\study.py"]:
    py_compile.compile(f, doraise=True)
print("ALL COMPILE OK")
