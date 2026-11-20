"""J-3415: dump the prompt text (string literals) behind every prompt-registry row, read-only.
Usage: python scripts/_scan_J-3415_prompt_text.py OUTDIR
Writes one file per prompt id: the string constants inside the registered function plus the
module-level string constants the function references by name."""
import ast, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
REG = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT/'docs'/'prompt_registry.jsonl'
rows = [json.loads(l) for l in open(REG, encoding='utf-8') if l.strip()]

def strs(node):
    res = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) > 30:
            res.append((n.lineno, n.value))
        elif isinstance(n, ast.JoinedStr):
            parts = []
            for v in n.values:
                if isinstance(v, ast.Constant): parts.append(str(v.value))
                else: parts.append('{..}')
            s = ''.join(parts)
            if len(s) > 30: res.append((n.lineno, s))
    # dedupe (JoinedStr constants appear twice)
    seen = set(); o = []
    for ln, s in sorted(res):
        if s in seen: continue
        seen.add(s); o.append((ln, s))
    return o

def find_func(tree, qual):
    parts = qual.split('.')
    cur = tree
    for p in parts:
        nxt = None
        for n in ast.walk(cur) if cur is tree else cur.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == p:
                nxt = n; break
        if nxt is None: return None
        cur = nxt
    return cur

for r in rows:
    text = []
    for key in r.get('keys', []):
        mod, _, fn = key.partition(':')
        fn = fn.split('#')[0].split('@')[0]
        fn = fn.split(' ')[0]
        path = ROOT / (mod.replace('.', '/') + '.py')
        if not path.exists(): text.append(f'## {key}: FILE MISSING'); continue
        src = path.read_text(encoding='utf-8-sig', errors='replace')
        tree = ast.parse(src)
        node = tree if not fn else find_func(tree, fn.replace('.one', '').split('.one')[0])
        if node is None:
            # nested function e.g. _reentry_shadow._revise
            node = None
            for n in ast.walk(tree):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fn.split('.')[-1]:
                    node = n; break
        if node is None: text.append(f'## {key}: FUNC NOT FOUND'); continue
        text.append(f'## {key}  ({path.relative_to(ROOT)} L{getattr(node,"lineno",0)}-{getattr(node,"end_lineno",0)})')
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        mod_consts = []
        for n in tree.body:
            if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in names for t in n.targets):
                for ln, s in strs(n.value): mod_consts.append((n.targets[0].id, ln, s))
        for nm, ln, s in mod_consts: text.append(f'-- const {nm} L{ln}:\n{s}\n')
        for ln, s in strs(node): text.append(f'-- L{ln}:\n{s}\n')
    (out / f"{r['id']}.txt").write_text('\n'.join(text), encoding='utf-8')
print('wrote', len(rows))
