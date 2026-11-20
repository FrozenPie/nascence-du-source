"""J-4154: _EPOCH_RETRIEVAL_FLOOR = 0.66 (D-0795). Temp-path store; nothing under data/ touched."""
import sys, tempfile, sqlite3
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pathlib import Path
import core.memory.store as S
assert str(Path(S.__file__).resolve()).startswith(str(Path(__file__).resolve().parents[1])), S.__file__
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
check("floor == 0.66", S._EPOCH_RETRIEVAL_FLOOR == 0.66)
class Row(dict): pass
def run(sim):
    rows = [{"embedding": b"x", "id": 1}]
    class C:
        def __enter__(s): return s
        def __exit__(s, *a): return False
        def execute(s, q): 
            class R:
                def fetchall(r): return rows
            return R()
    S_embed, S_conn, S_cos, S_blob = S._embed, S._connect, S._cosine, S._blob_to_vec
    try:
        S._embed = lambda t: [1.0]; S._connect = lambda: C(); S._cosine = lambda a, b: sim; S._blob_to_vec = lambda b: [1.0]
        return S.retrieve_epoch("q")
    finally:
        S._embed, S._connect, S._cosine, S._blob_to_vec = S_embed, S_conn, S_cos, S_blob
check("0.65 -> none", run(0.65) == [])
check("0.62 (old-floor pass) -> none", run(0.62) == [])
check("0.67 -> one", len(run(0.67)) == 1)
sys.exit(1 if fails else 0)
