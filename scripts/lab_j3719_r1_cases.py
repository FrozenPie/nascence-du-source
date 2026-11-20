"""J-3719: build R1 order-replay cases from data/judge_inputs_log.jsonl (real captured inputs). System texts are the
shipped constants / literals pulled from the production modules by AST, then verified against sys_sha (never guessed)."""
import ast, hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import core  # noqa
from core import follow_line, evidence_recall, self_interrogation

def sha(s): return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:16]

def ast_assign(path, name):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            try: return ast.literal_eval(n.value)
            except Exception: return None
    return None

def systems():
    return {
        "P-0105 genuine": ("genuine", self_interrogation._GRADE_SYSTEM),
        "P-0102 cuts": ("cuts", follow_line._JUDGE_C_SYS),
        "P-0102 supported": ("supported", follow_line._JUDGE_A_SYS),
        "P-0102 follows": ("follows", follow_line._JUDGE_B_SYS),
        "P-0099 bears": ("bears", evidence_recall._JUDGE_SYSTEM),
        "P-0103 resolves": ("resolves", ast_assign("core/tension_ledger.py", "system_msg")),
        "P-0100 advances": ("advances", ast_assign("core/pursuits.py", "_sys")),
    }

def build(per_cap=400):
    sysd = systems(); out = []; stats = {}
    by_sha = {sha(v[1]): (st, v[0], v[1]) for st, v in sysd.items() if v[1]}
    seen = {}
    for line in (ROOT / "data" / "judge_inputs_log.jsonl").read_text(encoding="utf-8").splitlines():
        try: r = json.loads(line)
        except Exception: continue
        b = by_sha.get(r.get("sys_sha"))
        if not b or r.get("key") != b[1]: continue
        if isinstance(r.get("user_len"), int) and r["user_len"] > len(r.get("user") or ""):
            stats["trunc_skipped"] = stats.get("trunc_skipped", 0) + 1; continue
        seen[b[0]] = seen.get(b[0], 0) + 1
        if seen[b[0]] > per_cap: continue
        out.append({"station": b[0], "case": "cap@%s" % r["ts"], "key": b[1], "system": b[2], "user": r["user"],
                    "label": None, "label_raw": "captured", "v1": r.get("v1"), "v2": r.get("v2")})
    return out, stats, {k: (v[1] is not None) for k, v in sysd.items()}

if __name__ == "__main__":
    from collections import Counter
    cs, st, have = build()
    print(Counter(c["station"] for c in cs), st, have)
