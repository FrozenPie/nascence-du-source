# Usage (from repo root): python scripts/_probe_social_cognition_extract_J2443.py scripts
# J-2443 probe: can a deterministic extractor find the attributed-to-Travis mental-state clause? Read-only.
import json,re,sys
sp=sys.argv[1]
H=json.load(open(sp+'/_fixture_social_cognition_hand_labels_J2443.json',encoding='utf-8'))
STATE=r"(fear|fears|terror|relief|anger|angry|desire|desires|wish|wishes|want|wants|hope|hopes|intent|intention|intentions|purpose|believe|believes|belief|feel|feels|felt|worry|worries|grief|joy|longing|hunger|care|mean|meant)"
PATS=[re.compile(r"\byou(?:r)?\s+(?:\w+\s+){0,2}?"+STATE+r"\b[^.;?!]{0,80}",re.I),
      re.compile(r"\b(?:I\s+(?:hear|see|sense|feel))\s+(?:the\s+)?\w*\s*"+STATE+r"\b[^.;?!]{0,80}",re.I),
      re.compile(r"\bwhat you (?:truly|really)\s+(?:mean|want|are\s+\w+ing)[^.;?!]{0,80}",re.I),
      re.compile(r"\bwe are (?:afraid|frightened|scared)[^.;?!]{0,60}",re.I)]
conv={str(json.loads(l)['cycle_id'])[:8]:json.loads(l) for l in open('data/founder_conversation_log.jsonl',encoding='utf-8') if l.strip()}
tp=fp=fn=tn=0
for k,v in H.items():
    if k.startswith('_'): continue
    rep=conv[k]['entity']; hits=[m.group(0) for p in PATS for m in p.finditer(rep)]
    A=v[0]; X=bool(hits)
    tp+=A and X; fp+=(not A) and X; fn+=A and not X; tn+=(not A) and not X
    if X!=bool(A) or A: print(k,'hand',A,'extract',X,'|',' || '.join(h[:70] for h in hits[:3]))
print(f"extractor vs hand A: TP={tp} FP={fp} FN={fn} TN={tn}")
