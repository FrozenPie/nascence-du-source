import json, glob, statistics as st, sys, collections
D = sys.argv[1] if len(sys.argv) > 1 else "J-2636_out"
def load(cond, arm):
    ev = {}
    for f in sorted(glob.glob(f"{D}/{cond}_{arm}_s*.jsonl")):
        for l in open(f, encoding="utf-8"):
            r = json.loads(l)
            if r.get("kind") != "event": continue
            k = (r["source"], r["provenance"]["locator"], r["cue"])
            ev.setdefault(k, r)
    return ev
BINS = [("<=10-16", lambda d: d <= "2026-10-16"), ("10-17..19", lambda d: "2026-10-17" <= d <= "2026-10-19"),
        ("10-20..28", lambda d: "2026-10-20" <= d <= "2026-10-28"), (">=10-29", lambda d: d >= "2026-10-29")]
def stats(rs):
    n = len(rs)
    if not n: return "n=0"
    ans = [r for r in rs if r["answered"]]
    errs = [r["date_error_days"] for r in ans if r["date_error_days"] is not None]
    w3 = sum(1 for r in rs if r["answered"] and r["date_error_days"] is not None and r["date_error_days"] <= 3)
    ex = sum(1 for r in rs if r["answered"] and r["date_error_days"] == 0)
    pr = [r["detail_precision"] for r in rs]
    return (f"n={n} answered={len(ans)} median_err={st.median(errs) if errs else None} within3={w3}/{n}={w3/n:.0%} "
            f"exact={ex}/{n}={ex/n:.0%} precision={sum(pr)/n:.3f}")
newest = {"2026-10-29", "2026-10-30"}
for arm in ("A", "B"):
    c, d = load("ctl", arm), load("drop", arm)
    print(f"\n######## ARM {arm} ({'ask default grounded_only=True' if arm=='A' else 'all origins grounded_only=False'})  unique events ctl={len(c)} drop={len(d)} identical_event_set={set(c)==set(d)}")
    for name, f in BINS:
        keys = [k for k in c if k in d and f(c[k]["event_date"])]
        print(f"[{name}] CONTROL : {stats([c[k] for k in keys])}")
        print(f"[{name}] DROPPED : {stats([d[k] for k in keys])}")
        if keys:
            imp = sum(1 for k in keys if (d[k]["date_error_days"] if d[k]["answered"] else 999) < (c[k]["date_error_days"] if c[k]["answered"] else 999))
            wor = sum(1 for k in keys if (d[k]["date_error_days"] if d[k]["answered"] else 999) > (c[k]["date_error_days"] if c[k]["answered"] else 999))
            print(f"    paired: dropped better {imp}, worse {wor}, same {len(keys)-imp-wor}")
    # converse: where do wrong top-1s point (control)
    for name, f in BINS[:3]:
        keys = [k for k in c if f(c[k]["event_date"])]
        wrong = [c[k] for k in keys if c[k]["answered"] and c[k]["date_error_days"] not in (0, None)]
        wrong3 = [r for r in wrong if r["date_error_days"] > 3]
        to_new = [r for r in wrong if r["pred_date"] in newest]
        to_post = [r for r in wrong if r["pred_date"] and r["pred_date"] > "2026-10-28"]
        print(f"[converse ctl {name}] events={len(keys)} wrong_top1(err>0)={len(wrong)} err>3={len(wrong3)}  -> newest day(10-29/30)={len(to_new)}  -> any >10-28={len(to_post)}")
        oc = collections.Counter(r["recalled"][0]["origin"] for r in to_post); sc = collections.Counter(r["source"] for r in to_post)
        pd = collections.Counter(r["pred_date"] for r in to_post)
        print(f"      by top-1 origin {dict(oc)}  by event source {dict(sc)}  by pred_date {dict(pd)}")
    # what the dropped run points to for old events (still wrong ones)
    keys = [k for k in d if d[k]["event_date"] <= "2026-10-16"]
    wr = [d[k] for k in keys if d[k]["answered"] and d[k]["date_error_days"] not in (0, None)]
    print(f"[dropped <=10-16] wrong top-1={len(wr)}; top-1 pred_date histogram: {dict(sorted(collections.Counter(r['pred_date'] for r in wr).items()))}")
    print(f"      top-1 origins: {dict(collections.Counter(r['recalled'][0]['origin'] for r in wr))}; err>3: {sum(1 for r in wr if r['date_error_days']>3)}; error signed buckets (abs days) median {st.median([r['date_error_days'] for r in wr]) if wr else None}")
