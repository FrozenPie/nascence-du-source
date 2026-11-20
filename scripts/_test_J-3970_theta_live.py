import sys, os, tempfile
sys.path.insert(0, os.getcwd())
import core
assert os.getcwd().replace("\\","/").lower() in core.__file__.replace("\\","/").lower(), core.__file__
from core import associative_recall as ar
from pathlib import Path
tmp = Path(tempfile.mkdtemp())/"theta_live.jsonl"
ar._THETA_LIVE_LOG = tmp
rows = {"t1": {"content":"x","origin":"lived","timestamp":0.0}, "dup":{"content":"d","origin":"lived","timestamp":0.0},
        "self":{"content":"s","origin":"synthesis","timestamp":0.0}}
class R(dict):
    pass
ar._load_rows = lambda ids: {i: rows[i] for i in ids if i in rows}
frags=[{"fragment_id":f"f{i}","content":"c","origin":"lived"} for i in range(4)]
tr={"trigger":"idle_seed","top3_ids":["self","dup","t1"],"tod":.5,"season":.3}
rows["dup"]=rows["dup"]
out=ar._theta_inject(frags,tr,4,True)
ids=[f["fragment_id"] for f in out]; print(ids)
assert ids==["f0","f1","f2","dup"] and len(out)==4
out=ar._theta_inject(frags,{"top3_ids":["self"]},4,True); assert out==frags
out=ar._theta_inject(frags[:2],tr,4,True); print([f["fragment_id"] for f in out]); assert len(out)==3
print(tmp.read_text()[:300])
print("OK")
