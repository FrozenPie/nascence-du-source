"""J-2806 (read-only analysis): classify every fast-path retrieve() probe row slower than 700 ms.
Reads C:/Nascence/data/{retrieve_latency_probe.jsonl,nascence.log,night_stall_attribution.jsonl} read-only.
Writes docs/lab/J-2806_data/outlier_classification.json and .md inside THIS worktree.
Rules (first match wins):
  cold-fill        the first fast-path call of its process (boot = 'Loading embedding model' log line): _EMB_MAT empty
  delta-tail       path fast+delta, total < 1500 ms: the tail of the delta path's slow mode (J-2806 finding: the patch
                   re-read flips to a MULTI-INDEX OR scan when >= 9 distinct fragments changed since the previous call)
  unexplained      everything else (flagged with sleep state / tick gap / stall stage so a reader can see what was around)"""
import json, re, bisect, datetime as dt, statistics as st
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
D = Path(r'C:/Nascence/data')
rows = [json.loads(l) for l in open(D / 'retrieve_latency_probe.jsonl', encoding='utf-8')]
calls = [r for r in rows if r.get('path') in ('fast', 'fast+delta')]
t_lo = calls[0]['timestamp'] - 7200
boots, sleep_ev, ticks = [], [], []
with open(D / 'nascence.log', encoding='utf-8', errors='replace') as f:
    for line in f:
        if 'Loading embedding model' in line or 'entering Sleep State' in line or '[night] waking:' in line or '[tier3] tick #' in line:
            ts = dt.datetime.strptime(line[:23], '%Y-%m-%d %H:%M:%S,%f').timestamp()
            if ts < t_lo: continue
            if 'Loading embedding model' in line: boots.append(ts)
            elif 'entering Sleep State' in line: sleep_ev.append((ts, 'enter'))
            elif '[night] waking:' in line: sleep_ev.append((ts, 'wake'))
            else: ticks.append(ts)
iv, cur = [], None
for ts, k in sleep_ev:
    if k == 'enter': cur = ts
    elif cur is not None: iv.append((cur, ts)); cur = None
sstart = [a for a, b in iv]
def in_sleep(s, e):
    k = bisect.bisect_right(sstart, e) - 1
    return any(j >= 0 and iv[j][0] <= e and iv[j][1] >= s for j in (k - 1, k))
gaps = [(ticks[i], ticks[i + 1]) for i in range(len(ticks) - 1)]
gstart = [g[0] for g in gaps]
def tick_gap(ts):
    k = bisect.bisect_right(gstart, ts) - 1
    return round(gaps[k][1] - gaps[k][0]) if 0 <= k < len(gaps) and gaps[k][0] <= ts <= gaps[k][1] else None
stalls = [json.loads(l) for l in open(D / 'night_stall_attribution.jsonl', encoding='utf-8')]
seen_boot, out = set(), []
for r in calls:
    tot = r['elapsed_ms_sql'] + r['elapsed_ms_score']; e = r['timestamp']; s = e - tot / 1000
    b = bisect.bisect_right(boots, s) - 1
    first = b >= 0 and b not in seen_boot
    if b >= 0: seen_boot.add(b)
    if tot <= 700: continue
    sl = in_sleep(s, e); tg = tick_gap(e)
    hit = [(x['stage'], x.get('sub'), x['lag_s']) for x in stalls if s - 3 <= x['ts'] <= e + 3]
    cls = 'cold-fill' if first else ('delta-tail' if r['path'] == 'fast+delta' and tot < 1500 else 'unexplained')
    note = []
    if cls == 'cold-fill' and (sl or tot > 8000): note.append('compound: sleep/night work overlapped the fill')
    # J-3714: phase attribution (rows written after the probe gained phase keys; older rows have none)
    ph = {k: r[k] for k in ('connect_ms', 'pool_lock_wait_ms', 'emb_lock_wait_ms', 'member_select_ms', 'emb_fetch_ms') if k in r}
    dom = max(ph, key=ph.get) if ph and max(ph.values()) >= 0.5 * tot else ('none>=50pct' if ph else 'no-phase-data')
    wal = r.get('wal_bytes')
    out.append({'phase': ph, 'dominant_phase': dom, 'emb_fetch_n': r.get('emb_fetch_n'), 'wal_mb': round(wal / 1048576, 1) if isinstance(wal, int) and wal >= 0 else None,
                'when': dt.datetime.fromtimestamp(e).strftime('%m-%d %H:%M:%S'), 'path': r['path'], 'total_ms': round(tot),
                'sql_ms': round(r['elapsed_ms_sql']), 'pool_rows': r['rows_fetched'], 'class': cls, 'in_sleep': sl,
                'tick_gap_s': tg, 'stall_overlap': hit[:2], 'note': '; '.join(note)})
(ROOT / 'docs/lab/J-2806_data').mkdir(parents=True, exist_ok=True)
(ROOT / 'docs/lab/J-2806_data/outlier_classification.json').write_text(json.dumps(out, indent=1), encoding='utf-8')
cnt = {}
for o in out: cnt[o['class']] = cnt.get(o['class'], 0) + 1
md = ['# J-2806 outlier classification (fast-path retrieve() calls > 700 ms)', '', f'Total {len(out)}; ' + ', '.join(f'{k}: {v}' for k, v in sorted(cnt.items())), '',
      '| when | path | total ms | pool | class | in sleep | tick gap s | stall overlap | dominant phase | WAL MB | note |', '|---|---|---|---|---|---|---|---|---|---|---|']
for o in out:
    md.append(f"| {o['when']} | {o['path']} | {o['total_ms']} | {o['pool_rows']} | {o['class']} | {o['in_sleep']} | {o['tick_gap_s']} | {o['stall_overlap']} | {o['dominant_phase']} | {o['wal_mb']} | {o['note']} |")
big = [o for o in out if o['total_ms'] > 1500]
md += ['', f"Calls over 1500 ms: {len(big)}; cold-fill {sum(o['class']=='cold-fill' for o in big)}, unexplained {sum(o['class']=='unexplained' for o in big)}, delta-tail {sum(o['class']=='delta-tail' for o in big)}"]
un = [o for o in out if o['class'] == 'unexplained']
bk = {}
for o in un: bk[o['dominant_phase']] = bk.get(o['dominant_phase'], 0) + 1
md += ['', 'Unexplained bucket by dominant phase (J-3714): ' + (', '.join(f'{k}: {v}' for k, v in sorted(bk.items())) or 'empty')]
(ROOT / 'docs/lab/J-2806_data/outlier_classification.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
print('\n'.join(md))
