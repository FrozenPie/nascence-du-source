"""
graphify_force_html.py — regenerate graph.html as the aggregated community view when `graphify cluster-only`
silently skips it (found 2026-08-18).

WHY: past 5000 raw nodes, graphify's own `to_html()` CAN fall back to an aggregated community-level view
(circles = communities, not raw symbols) instead of skipping the render — but `cluster-only`'s CLI only
turns that fallback on when graph.json trips a BYTE-SIZE cap check (`_over_cap`, in security.py), which is
a different measurement than the node-count check `to_html()` itself uses. A graph that's over the 5000-node
viz limit but under the byte-size cap (plausible — this project's graph.json is a few MB, well under it)
gets `node_limit=None` passed through, so `to_html()` just raises and `cluster-only` prints "Skipped
graph.html" instead of building the aggregated view it's fully capable of. Net effect: once this project
crossed 5000 nodes, every `cluster-only` run silently dropped graph.html — no aggregated fallback, and the
force-directed "linked circles" view stopped being produced at all (a D3 tree can still be built separately
via `graphify tree`, but that's a different, hierarchical shape, not the community view people expect).

WHAT: loads the current graph.json + its existing community/label data directly and calls `to_html()`
itself, working around the CLI's gating bug. Default mode raises `node_limit` past the actual node count so
the RAW per-symbol graph renders directly — the dense many-dots view this project's graph.html has always
shown (comparison against archived snapshots confirmed the founder's read: the coarse aggregated-community
fallback, while functional, is visually a much thinner "sphere of a few hundred big circles" than the rich
raw view of thousands of individual symbol-nodes people actually want to browse). Pass --aggregate to force
the coarse community-circle fallback instead, if the raw graph ever gets too large for the browser to
handle smoothly. Re-run any time after a `cluster-only` that reports "Skipped graph.html".
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

from graphify.build import build_from_json
from graphify.export import to_html

OUT = Path('graphify-out')
raw = json.loads((OUT / 'graph.json').read_text(encoding='utf-8'))
G = build_from_json(raw, directed=bool(raw.get('directed', False)))
print(f'Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')

communities = defaultdict(list)
for n in raw.get('nodes', []):
    cid = n.get('community')
    if cid is not None:
        communities[cid].append(n['id'])
communities = dict(communities)
print('communities:', len(communities))

labels_raw = json.loads((OUT / '.graphify_labels.json').read_text(encoding='utf-8'))
labels = {int(k): v for k, v in labels_raw.items()}

aggregate = '--aggregate' in sys.argv
node_limit = 5000 if aggregate else (G.number_of_nodes() + 1)
to_html(G, communities, str(OUT / 'graph.html'), community_labels=labels, node_limit=node_limit)
print('wrote', OUT / 'graph.html', '(aggregated)' if aggregate else '(raw, all nodes)')
