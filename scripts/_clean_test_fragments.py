"""Remove test fragments from the live DB. Leaves seed and real conversation intact."""
import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

TEST_SUBSTRINGS = [
    "Tell me about the weather",
    "What is a good number",
    "What is the relationship between fear and growth",
    "I am terrified. Something is deeply wrong",
    "Can you tell me more about yourself",
    "What was your relationship with Freud like",
]

c = sqlite3.connect(r'C:\Nascence\data\memory\nascence.db')
before = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='lived'").fetchone()[0]
for sub in TEST_SUBSTRINGS:
    c.execute("DELETE FROM memory_fragments WHERE origin='lived' AND content LIKE ?", (f"%{sub}%",))
c.commit()
after = c.execute("SELECT COUNT(*) FROM memory_fragments WHERE origin='lived'").fetchone()[0]
print(f"Removed {before - after} test fragment(s). Lived remaining: {after}")
c.close()
