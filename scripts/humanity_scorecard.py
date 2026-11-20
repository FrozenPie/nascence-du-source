"""Humanity scorecard: a fixed set of behavioural measures, computed the same way for every month.

Built 2026-11-16 (T-0140, F-4820). The humanity check of that day found fifteen earlier assessments and
no two on the same rubric, so "is Du getting more human-like" had no trend line. This script is that line.

RULES
- Read-only on data/. It calls no model and imports nothing from core/.
- Every measure has a frozen definition below. Changing one means bumping SCORECARD_VERSION and saying
  why in the CHANGES list; snapshots carry the version, so rows from different versions are never compared.
- Every run recomputes all months from the raw logs. `--write` also appends one snapshot to
  docs/humanity_scorecard.jsonl (owned by this tool; do not hand-edit) and rewrites
  docs/reviews/humanity_scorecard.md. If a past month's value differs between two snapshots of the same
  version, a log was rewritten or lost: the report says so.

USAGE
  python scripts/humanity_scorecard.py            print the table
  python scripts/humanity_scorecard.py --write    print, append a snapshot, rewrite the markdown report
  python scripts/humanity_scorecard.py --weeks    also print the last 8 ISO weeks
"""
import sys, os, json, re, argparse, statistics as st, collections, datetime as dt

sys.stdout.reconfigure(encoding='utf-8')

SCORECARD_VERSION = 1
CHANGES = ["v1 2026-11-16: first version (T-0140)."]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
SNAP = os.path.join(ROOT, 'docs', 'humanity_scorecard.jsonl')
REPORT = os.path.join(ROOT, 'docs', 'reviews', 'humanity_scorecard.md')
START = dt.datetime(2026, 6, 1).timestamp()

# key, wall, label, direction (+1 higher is more human-like, -1 lower is, 0 context only),
# tolerance (a change smaller than this is "same"), minimum n for a cell to count, definition
MEASURES = [
    ('active_hours', 'context', 'Active log hours', 0, 0, 1,
     'distinct clock hours with any line in data/nascence.log'),
    ('human_turns', 'context', 'Human turns', 0, 0, 1,
     'count of "[CYCLE x] human:" lines in data/nascence.log'),
    ('internal_cycles', 'context', 'Internal cycles', 0, 0, 1,
     'count of "[CYCLE x] internal:" lines in data/nascence.log'),

    ('dream_resolved', 'closure', 'Dreams judged resolved', +1, 0.03, 20,
     'share of rows in data/logs/dream_resolution_shadow.jsonl with a truthy judge_verdict (rows with a verdict only)'),
    ('frontier_resolved', 'closure', 'Questions resolved (by birth month)', +1, 0.03, 50,
     'share of data/frontier.json questions born in the period whose status is resolved/answered/closed, as of the run; recent months can still mature'),
    ('pursuit_would_resolve', 'closure', 'Pursuit close-asks that would resolve', +1, 0.05, 10,
     'share of rows in data/logs/pursuit_close_shadow.jsonl with would_resolve true'),
    ('pursuit_advance', 'closure', 'Pursuit steps that advance', +1, 0.05, 50,
     'advanced / (advanced + restated) events in data/pursuits_shadow.jsonl'),
    ('hold_rate', 'closure', 'Commitment hold rate', +1, 0.05, 5,
     'mean hold_rate over rows of data/commitment_holdrate.jsonl'),
    ('closure_gate_yes', 'closure', 'Closure gate verdicts resolved', +1, 0.05, 10,
     'share of rows in data/logs/closure_gate.jsonl with resolved true (n is the number of gate rows; a row whose judge was unavailable counts as not resolved)'),

    ('confidence_sd', 'confidence', 'Spread of stated recall confidence', +1, 0.02, 50,
     'population sd of recall_confidence in data/recall_provenance_log.jsonl; a constant gives 0'),
    ('calibration_r', 'confidence', 'Predicted vs measured skill (r)', +1, 0.10, 30,
     'Pearson r between predicted and measured over rows of data/prediction_error_log.jsonl; a belief that ignores results gives about 0, and a negative value means he is surer where he does worse; the factual_recall domain joined the log on 2026-10-29'),
    ('pred_gap', 'confidence', 'Prediction gap, all domains', -1, 0.04, 30,
     'mean |gap| over rows of data/prediction_error_log.jsonl'),
    ('competence_share', 'confidence', 'Competence in self-projection', +1, 0.02, 100,
     'share of rows in data/identity_projection_shadow.jsonl whose types list contains "competence"'),

    ('conflict_acted', 'affect', 'Contradiction acted on when fired', +1, 0.04, 30,
     'share of rows with any_fired in data/conflict_trace.jsonl that also have any_acted'),
    ('valence', 'affect', 'Standing mood (valence)', +1, 0.10, 50,
     'mean affect.valence over rows of data/affect_log.jsonl'),
    ('valence_sd', 'affect', 'Mood range (sd of valence)', 0, 0, 50,
     'population sd of affect.valence in data/affect_log.jsonl; context, no direction claimed'),

    ('topic_share', 'attention', 'Modal-topic share per day', -1, 0.10, 3,
     'median over days (n>=8 cycles) of the last modal_share row per day in data/topic_perseveration.jsonl (J-2152 gauge, from 2026-09-17)'),
    ('real_hand', 'deeds', 'Thoughts with a real hand dispatch', +1, 0.02, 200,
     'share of rows in data/hands_trace.jsonl with a non-empty hands list'),
    ('soc_intent', 'social', 'Reply tracks the human intent', +1, 0.08, 20,
     'share true of tracks_intent in data/social_cognition_shadow.jsonl, dated by human_ts'),
    ('soc_attrib', 'social', 'Claims about the human supported', +1, 0.08, 20,
     'share true of attrib_supported in data/social_cognition_shadow.jsonl, dated by human_ts'),
    ('integration', 'learning', 'Instruction integration events', 0, 0, 1,
     'sum of assimilated + accommodated + promoted over rows of data/guidance_integration_log.jsonl; context only, because it scales with how much the founder says'),
    ('gist_faithful', 'memory', 'Gist faithfulness', +1, 0.04, 50,
     'mean faithful over rows of data/memory_levels_shadow.jsonl'),
    ('grounding_deficit', 'memory', 'World queries with a grounding deficit', -1, 0.06, 30,
     'share of world_query rows in data/retrieval_probe_log.jsonl with grounding_deficit true'),
]
WALLS = ['closure', 'confidence', 'affect', 'attention', 'deeds', 'social', 'learning', 'memory', 'context']

VALS = collections.defaultdict(lambda: collections.defaultdict(list))   # key -> period -> values


def periods(ts):
    d = dt.datetime.fromtimestamp(ts)
    iso = d.isocalendar()
    return [d.strftime('%Y-%m'), '%d-W%02d' % (iso[0], iso[1])]


def add(key, ts, v):
    if not isinstance(ts, (int, float)) or ts < START or v is None:
        return
    for p in periods(ts):
        VALS[key][p].append(v)


def rows(rel):
    path = os.path.join(DATA, rel)
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                o = json.loads(line)
            except Exception:
                continue
            if isinstance(o, dict):
                yield o


def as_dict(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            import ast
            r = ast.literal_eval(v)
            return r if isinstance(r, dict) else {}
        except Exception:
            return {}
    return {}


def collect():
    hours = collections.defaultdict(set)
    line_re = re.compile(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)[,.]\d+ .*\[CYCLE [^\]]*\] (internal|human): ')
    path = os.path.join(DATA, 'nascence.log')
    if os.path.exists(path):
        with open(path, encoding='utf-8', errors='replace') as f:
            for ln in f:
                if len(ln) < 24 or ln[:2] != '20' or ln[4] != '-':
                    continue
                try:
                    d = dt.datetime.strptime(ln[:13], '%Y-%m-%d %H')
                except ValueError:
                    continue
                if d.timestamp() < START:
                    continue
                for p in periods(d.timestamp()):
                    hours[p].add(ln[:13])
                if '] internal: ' in ln or '] human: ' in ln:
                    m = line_re.match(ln)
                    if m:
                        ts = dt.datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S').timestamp()
                        add('human_turns' if m.group(2) == 'human' else 'internal_cycles', ts, 1)
    for p, h in hours.items():
        VALS['active_hours'][p] = [1] * len(h)

    for o in rows('logs/dream_resolution_shadow.jsonl'):
        if o.get('judge_verdict') is not None:
            add('dream_resolved', o.get('ts'), 1.0 if o['judge_verdict'] else 0.0)
    try:
        fr = json.load(open(os.path.join(DATA, 'frontier.json'), encoding='utf-8')).get('questions', [])
    except Exception:
        fr = []
    for q in fr:
        if isinstance(q, dict):
            add('frontier_resolved', q.get('born'), 1.0 if q.get('status') in ('resolved', 'answered', 'closed') else 0.0)
    for o in rows('logs/pursuit_close_shadow.jsonl'):
        if o.get('would_resolve') is not None:
            add('pursuit_would_resolve', o.get('ts'), 1.0 if o['would_resolve'] else 0.0)
    for o in rows('pursuits_shadow.jsonl'):
        if o.get('event') in ('advanced', 'restated'):
            add('pursuit_advance', o.get('ts'), 1.0 if o['event'] == 'advanced' else 0.0)
    for o in rows('commitment_holdrate.jsonl'):
        if isinstance(o.get('hold_rate'), (int, float)):
            add('hold_rate', o.get('ts'), o['hold_rate'])
    for o in rows('logs/closure_gate.jsonl'):
        if o.get('resolved') is not None:
            add('closure_gate_yes', o.get('ts'), 1.0 if o['resolved'] is True else 0.0)

    for o in rows('recall_provenance_log.jsonl'):
        if isinstance(o.get('recall_confidence'), (int, float)):
            add('confidence_sd', o.get('ts'), o['recall_confidence'])
    for o in rows('prediction_error_log.jsonl'):
        if isinstance(o.get('gap'), (int, float)):
            add('pred_gap', o.get('ts'), abs(o['gap']))
        if isinstance(o.get('predicted'), (int, float)) and isinstance(o.get('measured'), (int, float)):
            add('calibration_r', o.get('ts'), (o['predicted'], o['measured']))
    for o in rows('identity_projection_shadow.jsonl'):
        add('competence_share', o.get('ts'), 1.0 if 'competence' in (o.get('types') or []) else 0.0)

    for o in rows('conflict_trace.jsonl'):
        if o.get('any_fired'):
            add('conflict_acted', o.get('ts'), 1.0 if o.get('any_acted') else 0.0)
    for o in rows('affect_log.jsonl'):
        a = as_dict(o.get('affect'))
        if isinstance(a.get('valence'), (int, float)):
            add('valence', o.get('ts'), a['valence'])
            add('valence_sd', o.get('ts'), a['valence'])

    last = {}
    for o in rows('topic_perseveration.jsonl'):
        if o.get('day') and isinstance(o.get('modal_share'), (int, float)):
            last[o['day']] = o
    for o in last.values():
        if o.get('n', 0) >= 8:
            add('topic_share', o.get('ts'), o['modal_share'])
    for o in rows('hands_trace.jsonl'):
        add('real_hand', o.get('ts'), 1.0 if o.get('hands') else 0.0)
    for o in rows('social_cognition_shadow.jsonl'):
        t = o.get('human_ts') or o.get('ts')
        if isinstance(o.get('tracks_intent'), bool):
            add('soc_intent', t, 1.0 if o['tracks_intent'] else 0.0)
        if isinstance(o.get('attrib_supported'), bool):
            add('soc_attrib', t, 1.0 if o['attrib_supported'] else 0.0)
    for o in rows('guidance_integration_log.jsonl'):
        add('integration', o.get('ts'), sum(int(o.get(k) or 0) for k in ('assimilated', 'accommodated', 'promoted')))
    for o in rows('memory_levels_shadow.jsonl'):
        if isinstance(o.get('faithful'), (int, float)):
            add('gist_faithful', o.get('ts'), float(o['faithful']))
    for o in rows('retrieval_probe_log.jsonl'):
        if o.get('world_query'):
            add('grounding_deficit', o.get('ts'), 1.0 if o.get('grounding_deficit') else 0.0)


def pearson(pairs):
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return 0.0
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    return sum((x - mx) * (y - my) for x, y in pairs) / (sx * sy) if sx and sy else 0.0


def value(key, v):
    if not v:
        return None
    if key in ('active_hours', 'human_turns', 'internal_cycles', 'integration'):
        return float(sum(v))
    if key in ('confidence_sd', 'valence_sd'):
        return st.pstdev(v)
    if key == 'calibration_r':
        return pearson(v)
    if key == 'topic_share':
        return st.median(v)
    return sum(v) / len(v)


def table(cols):
    out = {}
    for key, wall, label, direction, tol, min_n, _ in MEASURES:
        out[key] = {}
        for p in cols:
            v = VALS[key].get(p, [])
            out[key][p] = {'v': None if not v else round(value(key, v), 4), 'n': len(v)}
    return out


def verdict(key, tab, cols):
    """Compare the latest counted cell with the first counted cell and with the one before it."""
    meta = {m[0]: m for m in MEASURES}[key]
    direction, tol, min_n = meta[3], meta[4], meta[5]
    if direction == 0:
        return '', ''
    ok = [p for p in cols if tab[key][p]['v'] is not None and tab[key][p]['n'] >= min_n]
    if len(ok) < 2:
        return 'too little data', 'too little data'

    def call(a, b):
        d = (tab[key][b]['v'] - tab[key][a]['v']) * direction
        return 'better' if d > tol else 'worse' if d < -tol else 'same'
    return '%s (since %s)' % (call(ok[0], ok[-1]), ok[0]), '%s (since %s)' % (call(ok[-2], ok[-1]), ok[-2])


def fmt(cell, key):
    if cell['v'] is None:
        return '-'
    if key in ('active_hours', 'human_turns', 'internal_cycles', 'integration'):
        return '%d' % cell['v']
    min_n = {m[0]: m[5] for m in MEASURES}[key]
    s = ('%.3f' % cell['v']) if abs(cell['v']) < 1 else ('%.2f' % cell['v'])
    return s + ('*' if cell['n'] < min_n else '')


def render(tab, cols, with_verdict=True):
    lines = ['| Wall | Measure | ' + ' | '.join(cols) + (' | Whole series | Last step |' if with_verdict else ' |'),
             '|---|---|' + '---|' * (len(cols) + (2 if with_verdict else 0))]
    tally = collections.Counter()
    for wall in WALLS:
        for key, w, label, direction, tol, min_n, _ in MEASURES:
            if w != wall:
                continue
            arrow = {1: ' (higher is better)', -1: ' (lower is better)', 0: ''}[direction]
            cells = ' | '.join(fmt(tab[key][p], key) for p in cols)
            if with_verdict:
                a, b = verdict(key, tab, cols)
                if direction:
                    tally[(wall, a.split(' ')[0])] += 1
                lines.append('| %s | %s%s | %s | %s | %s |' % (wall, label, arrow, cells, a, b))
            else:
                lines.append('| %s | %s%s | %s |' % (wall, label, arrow, cells))
    return lines, tally


def drift_check(tab, months):
    """Compare closed months with the latest snapshot of the same version."""
    if not os.path.exists(SNAP):
        return []
    prev = None
    for line in open(SNAP, encoding='utf-8'):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get('version') == SCORECARD_VERSION:
            prev = o
    if not prev:
        return []
    notes = []
    this_month = dt.datetime.now().strftime('%Y-%m')
    for key, _, label, direction, tol, _, _ in MEASURES:
        if key == 'frontier_resolved':
            continue   # matures by design
        for p in months:
            if p >= min(this_month, prev.get('run_month', this_month)):
                continue
            a = (prev.get('months', {}).get(key, {}).get(p) or {}).get('v')
            b = tab[key][p]['v']
            if a is not None and b is not None and abs(a - b) > max(tol, 1e-9) and direction:
                notes.append('%s %s: was %s in the %s snapshot, is %s now' % (label, p, a, prev.get('run'), b))
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--weeks', action='store_true')
    args = ap.parse_args()
    collect()
    now = dt.datetime.now()
    months, d = [], dt.date(2026, 6, 1)
    while (d.year, d.month) <= (now.year, now.month):
        months.append(d.strftime('%Y-%m'))
        d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    months = months[-8:]
    weeks = []
    for i in range(7, -1, -1):
        iso = (now - dt.timedelta(weeks=i)).isocalendar()
        weeks.append('%d-W%02d' % (iso[0], iso[1]))
    mt, wt = table(months), table(weeks)
    mlines, tally = render(mt, months)
    wlines, _ = render(wt, weeks, with_verdict=False)
    drift = drift_check(mt, months)

    head = ['# Humanity scorecard', '',
            'Version %d, run %s. Generated by `scripts/humanity_scorecard.py --write`; do not edit by hand.' % (SCORECARD_VERSION, now.strftime('%Y-%m-%d %H:%M')),
            'A star marks a cell with too few rows to count. The current month is partial.', '',
            '## By month', ''] + mlines + ['', '## Tally of the whole-series calls', '']
    for wall in WALLS:
        c = {k[1]: v for k, v in tally.items() if k[0] == wall}
        if c:
            head.append('- %s: %s' % (wall, ', '.join('%d %s' % (c[k], k) for k in ('better', 'same', 'worse', 'too') if k in c).replace('too', 'too little data')))
    head += ['', '## Last 8 ISO weeks', ''] + wlines
    if drift:
        head += ['', '## Past months that changed since the last snapshot', ''] + ['- ' + n for n in drift]
    head += ['', '## Definitions', '']
    for key, wall, label, direction, tol, min_n, definition in MEASURES:
        head.append('- **%s** (%s): %s. Same within %s; counts from n = %d.' % (label, wall, definition, tol, min_n))
    head += ['', '## Version history', ''] + ['- ' + c for c in CHANGES]
    text = '\n'.join(head) + '\n'

    print('\n'.join(mlines))
    print()
    for wall in WALLS:
        c = {k[1]: v for k, v in tally.items() if k[0] == wall}
        if c:
            print('%-11s %s' % (wall, dict(c)))
    if args.weeks:
        print()
        print('\n'.join(wlines))
    if drift:
        print('\nCHANGED SINCE LAST SNAPSHOT:')
        for n in drift:
            print('  ' + n)
    if args.write:
        snap = {'run': now.strftime('%Y-%m-%d %H:%M'), 'run_month': now.strftime('%Y-%m'), 'version': SCORECARD_VERSION,
                'months': mt, 'weeks': wt}
        with open(SNAP, 'a', encoding='utf-8') as f:
            f.write(json.dumps(snap, ensure_ascii=False) + '\n')
        with open(REPORT, 'w', encoding='utf-8') as f:
            f.write(text)
        print('\nwrote', os.path.relpath(REPORT, ROOT), 'and appended a snapshot to', os.path.relpath(SNAP, ROOT))


if __name__ == '__main__':
    main()
