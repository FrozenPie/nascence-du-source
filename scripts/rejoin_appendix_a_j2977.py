"""J-2977 (F-3670): re-join the prompt inventory's Appendix A telemetry PER GIT COMMIT.

WHY. docs/reviews/du_prompt_inventory_2026-10-31.md Appendix A joined every `module:line(Class)` label in
data/llm_latency.jsonl to the function that holds that line in the CURRENT file. But the label is the line
number AT THE TIME OF THE CALL, and a file's lines drift with every edit, so an old-vintage label can land
inside an unrelated function today (F-3670: line 1431 of subconscious_node.py was Active Imagination on
2026-10-08 and is inside `_t2_synthesise` now, so T2 was credited with 1,643 Active Imagination calls).

WHAT THIS DOES (read-only: git show / git log, and the live data files opened for reading only).
  1. Parse every row's `by` label (`nodes.x:LINE(Class)` / `core.y:LINE`), module -> file path.
  2. For each file, list its versions on the mainline (`git log <ref> --first-parent -- <path>`).
  3. Pick the version that was RUNNING for the row. Du loads code once, at process start, so the running
     version is the newest commit at or before the last process start ("Nascence is awake" in
     data/nascence.log), not the newest commit before the row. Candidate order per row:
        B  newest commit <= last process start (what actually ran)
        A  newest commit <= the row's own timestamp (the job brief's method)
        C  commits made while that process was running (edit made, Du restarted, commit landed later)
     The first candidate in which the label's line is the start of a plausible LLM call (an ast.Call whose
     callee name looks like a call_*/ask/judge/generate, or an Await) wins; none valid -> B, flagged.
  4. Map the line to the qualified function name with ast (innermost def, class-qualified, nested defs
     dotted: `InnerMonologueNode._enter_sleep._nm_generate`), exactly the naming Appendix A used.
  5. Count per function in 30d / 7d / 24h windows ending at an anchor. Anchor 2026-10-31 23:00 local is the
     one that reproduces the old table exactly (core.deliberation:187 -> 13602 / 1669 / 491), so the OLD
     method (labels joined to the current file) is also recomputed here as a control and compared row by row.

Usage (from the worktree):
  python scripts/rejoin_appendix_a_j2977.py --out docs/reviews/du_prompt_inventory_appendix_a_rejoined_2026-11-07.md
  python scripts/rejoin_appendix_a_j2977.py --calibrate      # validity hit rate of the call-site predicate
Everything it reads lives outside the worktree (C:/Nascence/data); it writes only --out / --json.
"""
from __future__ import annotations

import argparse
import ast
import bisect
import collections
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

LABEL_RE = re.compile(r"^(?P<mod>[\w.]+):(?P<line>\d+)(?:\((?P<cls>\w+)\))?$")
CALLISH = re.compile(r"call|ask|llm|chat|gen|judge|complete|post|infer|invoke|consult|grade|score|best_of|one$|_run", re.I)
INV_ANCHOR = datetime.datetime(2026, 10, 31, 23, 0).timestamp()      # reproduces the old table exactly
DAY = 86400.0


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


# ---------------------------------------------------------------- per-version AST ----------------------------------
class Version:
    """One (path, commit): line -> qualified function, and the set of lines that start a plausible LLM call."""

    def __init__(self, src: str):
        self.line_fn: dict[int, str] = {}
        self.call_lines: set[int] = set()
        self.ok = True
        try:
            tree = ast.parse(src)
        except SyntaxError:
            self.ok = False
            return
        spans: list[tuple[int, int, str]] = []

        def walk(node, stack):
            for ch in ast.iter_child_nodes(node):
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    q = ".".join(stack + [ch.name])
                    spans.append((ch.lineno, ch.end_lineno or ch.lineno, q))
                    walk(ch, stack + [ch.name])
                elif isinstance(ch, ast.ClassDef):
                    walk(ch, stack + [ch.name])
                else:
                    walk(ch, stack)

        walk(tree, [])
        spans.sort(key=lambda s: -(s[1] - s[0]))            # widest first, narrower overwrite -> innermost wins
        for a, b, q in spans:
            for ln in range(a, b + 1):
                self.line_fn[ln] = q
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                name = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
                if name and CALLISH.search(name):
                    self.call_lines.add(n.lineno)
                    # a multi-line call: the frame line can be any argument line that itself holds a call/await
            elif isinstance(n, ast.Await):
                self.call_lines.add(n.lineno)

    def fn(self, line: int) -> str:
        return self.line_fn.get(line, "?")

    def valid(self, line: int) -> bool:
        return line in self.call_lines


class Repo:
    def __init__(self, repo: Path, ref: str):
        self.repo, self.ref = repo, ref
        self._hist: dict[str, list[tuple[int, str]]] = {}
        self._ver: dict[tuple[str, str], Version | None] = {}

    def history(self, path: str) -> list[tuple[int, str]]:
        if path not in self._hist:
            out = git(self.repo, "log", self.ref, "--first-parent", "--format=%ct %H", "--", path)
            h = []
            for ln in out.splitlines():
                p = ln.split()
                if len(p) == 2:
                    h.append((int(p[0]), p[1]))
            h.sort()
            self._hist[path] = h
        return self._hist[path]

    def version(self, path: str, commit: str) -> Version | None:
        k = (path, commit)
        if k not in self._ver:
            src = git(self.repo, "show", f"{commit}:{path}")
            self._ver[k] = Version(src) if src else None
        return self._ver[k]

    def commit_at(self, path: str, t: float) -> tuple[int, str] | None:
        h = self.history(path)
        if not h:
            return None
        i = bisect.bisect_right([c[0] for c in h], t) - 1
        return h[max(i, 0)]                                  # before the first commit: the earliest version

    def commits_between(self, path: str, t0: float, t1: float) -> list[tuple[int, str]]:
        return [c for c in self.history(path) if t0 < c[0] <= t1]


def module_path(repo: Path, mod: str) -> str | None:
    if mod == "__main__" or mod.startswith("asyncio"):
        return None
    rel = mod.replace(".", "/")
    for cand in (rel + ".py", rel + "/__init__.py", "scripts/" + rel + ".py"):
        if (repo / cand).exists() or git(repo, "ls-tree", "--name-only", "HEAD", cand).strip():
            return cand
    # a module that no longer exists at HEAD (or a lab script): look for any history under the plain path
    if git(repo, "log", "-1", "--format=%H", "--all", "--", rel + ".py").strip():
        return rel + ".py"
    return None


def process_starts(log: Path) -> list[float]:
    pat = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d),\d+ \[nascence\.main\] Nascence is awake")
    out = []
    with open(log, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            if "Nascence is awake" in ln:
                m = pat.match(ln)
                if m:
                    out.append(datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp())
    return sorted(set(out))


# ---------------------------------------------------------------- the join --------------------------------------------
class Joiner:
    def __init__(self, repo: Repo, starts: list[float]):
        self.r, self.starts = repo, starts
        self.paths: dict[str, str | None] = {}
        self.stat = collections.Counter()
        self.cache: dict[tuple, tuple[str, str]] = {}

    def path_of(self, mod: str) -> str | None:
        if mod not in self.paths:
            self.paths[mod] = module_path(self.r.repo, mod)
        return self.paths[mod]

    def candidates(self, path: str, t: float):
        s_i = bisect.bisect_right(self.starts, t) - 1
        s = self.starts[s_i] if s_i >= 0 else None
        nxt = self.starts[s_i + 1] if s_i + 1 < len(self.starts) else t + 1
        cands = []
        if s is not None:
            b = self.r.commit_at(path, s)
            if b:
                cands.append(("B", b))
        a = self.r.commit_at(path, t)
        if a and (not cands or a[1] != cands[0][1][1]):
            cands.append(("A", a))
        if s is not None:
            for c in self.r.commits_between(path, s, min(nxt, t + 1)):
                cands.append(("C", c))
        return cands

    method = "auto"                                      # auto | A | B  (A/B force one method for comparison)

    def resolve(self, mod: str, line: int, t: float) -> tuple[str, str]:
        """-> (qualified function or '?', method tag B/A/C/B!)"""
        path = self.path_of(mod)
        if not path:
            return "?", "nopath"
        cands = self.candidates(path, t)
        if self.method == "A":
            a_ = self.r.commit_at(path, t)
            cands = [("A", a_)] if a_ else []
        if not cands:
            return "?", "nohist"
        key = (path, line, tuple(c[1][1] for c in cands))
        if key in self.cache:
            return self.cache[key]
        res = None
        for tag, (_ct, h) in cands:
            v = self.r.version(path, h)
            if v and v.ok and v.valid(line):
                res = (v.fn(line), tag)
                break
        if res is None:
            tag, (_ct, h) = cands[0]
            v = self.r.version(path, h)
            res = ((v.fn(line) if v and v.ok else "?"), tag + "!")
        self.cache[key] = res
        return res

    def resolve_current(self, mod: str, line: int, snapshot_t: float) -> str:
        """The OLD method: the label's line looked up in the file as it stood at snapshot_t."""
        path = self.path_of(mod)
        if not path:
            return "?"
        c = self.r.commit_at(path, snapshot_t)
        if not c:
            return "?"
        v = self.r.version(path, c[1])
        return v.fn(line) if v and v.ok else "?"


def load_rows(p: Path, t_min: float):
    with open(p, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if r.get("ts", 0) >= t_min:
                yield r


def logged_fn(r: dict) -> str | None:
    """J-3760 / F-4371: the function name the row itself carries (`fn`, written beside `by` by model_client from the
    live frame's co_qualname), normalised to this script's key form (`Class.method`; a nested def's `<locals>` hop
    is dropped, matching Version.walk). None for an older row, which keeps the git reconstruction."""
    f = r.get("fn")
    if not f or not isinstance(f, str):
        return None
    return f.replace(".<locals>.", ".")


def time_now() -> float:
    return datetime.datetime.now().timestamp()


def fmt_key(mod: str, fn: str, cls: str | None) -> str:
    return f"{mod}:{fn}" + (f"({cls})" if cls else "")


def window_counts(rows_by_key, anchor):
    out = {}
    for k, lst in rows_by_key.items():
        a30 = sum(1 for t, *_ in lst if anchor - 30 * DAY < t <= anchor)
        a7 = sum(1 for t, *_ in lst if anchor - 7 * DAY < t <= anchor)
        a1 = sum(1 for t, *_ in lst if anchor - 1 * DAY < t <= anchor)
        if a30 or a7 or a1:
            out[k] = (a30, a7, a1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(ROOT))
    ap.add_argument("--data", default="C:/Nascence/data")
    ap.add_argument("--ref", default="master")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--method", choices=["auto", "A", "B"], default="auto",
                    help="force one version-pick method (A = newest commit before the row, B = running version) to compare")
    ap.add_argument("--old-md", default=str(ROOT / "docs/reviews/du_prompt_inventory_2026-10-31.md"))
    ap.add_argument("--registry", default="C:/Nascence/docs/prompt_registry.jsonl")
    ap.add_argument("--why", help="json {function key: short reason} for section 3")
    ap.add_argument("--extra-md", help="markdown appended after section 4 (sections 5+)")
    a = ap.parse_args()
    data = Path(a.data)
    repo = Repo(Path(a.repo), a.ref)
    starts = process_starts(data / "nascence.log")
    jn = Joiner(repo, starts)
    jn.method = a.method

    lat = data / "llm_latency.jsonl"
    last_ts = 0.0
    with open(lat, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                last_ts = max(last_ts, json.loads(ln)["ts"])
            except Exception:
                pass
    anchors = {"inv": INV_ANCHOR, "now": last_ts}
    t_min = min(anchors.values()) - 30 * DAY - 3600
    rows = list(load_rows(lat, t_min))

    def calibrate(method: str) -> str:
        """Share of the last-12h labels whose line is a call-site line in the version picked by method B or A."""
        tot = ok = 0
        for r in rows:
            if r["ts"] <= last_ts - 12 * 3600:
                continue
            m = LABEL_RE.match(r.get("by", ""))
            p = jn.path_of(m["mod"]) if m else None
            if not p:
                continue
            if method == "B":
                cs = jn.candidates(p, r["ts"])
                c = cs[0][1] if cs else None
            else:
                c = repo.commit_at(p, r["ts"])
            v = repo.version(p, c[1]) if c else None
            if v and v.ok:
                tot += 1
                ok += v.valid(int(m["line"]))
        return f"{ok}/{tot} = {100.0 * ok / max(tot, 1):.1f}%"

    cal_b, cal_a = calibrate("B"), calibrate("A")
    print("calibration  B (running version):", cal_b, "  A (newest commit before the row):", cal_a)
    if a.calibrate:
        return

    inv_snapshot = INV_ANCHOR
    new_rows = collections.defaultdict(list)       # key -> [(ts, model@node, raw label)]
    old_rows = collections.defaultdict(list)
    raw_other = collections.defaultdict(list)
    tags = collections.Counter()
    flows = collections.Counter()
    tag_by_mod = collections.defaultdict(collections.Counter)
    for r in rows:
        by = r.get("by", "")
        ts = r["ts"]
        mn = f"{r.get('model', '?')}@{r.get('node', '?')}"
        m = LABEL_RE.match(by)
        if not m:
            raw_other[by or "(empty)"].append((ts, mn, by))
            continue
        mod, line, cls = m["mod"], int(m["line"]), m["cls"]
        fn, tag = jn.resolve(mod, line, ts)
        _lf = logged_fn(r)
        if _lf:                                    # J-3760: the logged name beats the per-commit reconstruction
            fn, tag = _lf, "L"
        tags[tag] += 1
        tag_by_mod[mod][tag] += 1
        nk, ok_ = fmt_key(mod, fn, cls), fmt_key(mod, jn.resolve_current(mod, line, inv_snapshot), cls)
        if r.get("h"):                             # J-3761 / F-4370: a raw-HTTP station row (h=1); keep it apart from the
            nk, ok_ = nk + " [raw-http]", ok_ + " [raw-http]"   # model_client rows of the same function
        new_rows[nk].append((ts, mn, by))
        old_rows[ok_].append((ts, mn, by))
        if nk != ok_ and INV_ANCHOR - 30 * DAY < ts <= INV_ANCHOR:
            flows[(ok_, nk)] += 1

    # cross-check: the same per-version join on data/thought_station_log.jsonl (one row per call START; no latency)
    stn_rows = collections.defaultdict(list)
    stn = data / "thought_station_log.jsonl"
    if stn.exists():
        for r in load_rows(stn, t_min):
            m = LABEL_RE.match(r.get("by", ""))
            if not m:
                continue
            fn, _tag = jn.resolve(m["mod"], int(m["line"]), r["ts"])
            fn = logged_fn(r) or fn                # J-3760: prefer the logged function name
            stn_rows[fmt_key(m["mod"], fn, m["cls"])].append((r["ts"], "", r["by"]))

    res = {}
    for name, anc in anchors.items():
        res[name] = {"new": window_counts(new_rows, anc), "old": window_counts(old_rows, anc)}

    def models(lst, anc):
        c = collections.Counter(mn for t, mn, _ in lst if anc - 30 * DAY < t <= anc)
        return ", ".join(f"{k} {v}" for k, v in c.most_common(3))

    def raws(lst, anc):
        s = sorted({b for t, _, b in lst if anc - 30 * DAY < t <= anc})
        return s

    payload = {
        "anchor_inventory_local": datetime.datetime.fromtimestamp(INV_ANCHOR).isoformat(),
        "anchor_now_local": datetime.datetime.fromtimestamp(last_ts).isoformat(),
        "process_starts": len(starts),
        "resolution_tags": dict(tags),
        "tag_by_module": {k: dict(v) for k, v in tag_by_mod.items()},
        "inv": {k: {"new": v, "old": res["inv"]["old"].get(k)} for k, v in res["inv"]["new"].items()},
        "inv_old_only": {k: v for k, v in res["inv"]["old"].items() if k not in res["inv"]["new"]},
        "now": {k: v for k, v in res["now"]["new"].items()},
        "models": {k: models(v, INV_ANCHOR) for k, v in new_rows.items()},
        "raws": {k: raws(v, INV_ANCHOR) for k, v in new_rows.items()},
        "station_log_inv": window_counts(stn_rows, INV_ANCHOR),
        "flows": [[o, n, c] for (o, n), c in flows.most_common()],
        "other_labels_30d_inv": {k: sum(1 for t, *_ in v if INV_ANCHOR - 30 * DAY < t <= INV_ANCHOR) for k, v in raw_other.items()},
    }
    if a.json:
        Path(a.json).write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("anchor_inventory_local", "anchor_now_local", "process_starts", "resolution_tags")}))
    if a.out:
        old_md = Path(a.old_md)
        old_tbl = {}
        raw_http = []
        for ln in old_md.read_text(encoding="utf-8").splitlines():
            mm = re.match(r"\| (\d+) \| (\d+) \| (\d+) \| (.+?) \|", ln)
            if mm and ln.startswith("| ") and ln.count("|") >= 7:
                c = [x.strip() for x in ln.split("|")]
                old_tbl[c[4]] = (int(c[1]), int(c[2]), int(c[3]))
                if "raw-http" in c[4]:
                    raw_http.append(ln)
        mine = {k: tuple(v["old"]) for k, v in payload["inv"].items() if v.get("old")}
        mine.update({k: tuple(v) for k, v in payload["inv_old_only"].items()})
        comparable = [k for k in old_tbl if "raw-http" not in k]
        same = sum(1 for k in comparable if mine.get(k) == old_tbl[k])
        gone = set()
        names_now = {}
        for k in set(payload["inv"]) | set(payload["inv_old_only"]) | set(payload["now"]):
            mm = re.match(r"^([\w.]+):(.*?)(?:\((\w+)\))?$", k)
            mod, fn = mm.group(1), mm.group(2)
            if fn == "?":
                continue
            pth = jn.path_of(mod)
            c = repo.commit_at(pth, time_now()) if pth else None
            v = repo.version(pth, c[1]) if c else None
            if v and v.ok and fn not in set(v.line_fn.values()):
                gone.add(k)
        ctx = {"reg": registry_rows(Path(a.registry)), "cal_b": cal_b, "cal_a": cal_a,
               "control": f"{same} of {len(comparable)}", "gone": gone, "raw_http_lines": raw_http,
               "why": json.loads(Path(a.why).read_text(encoding="utf-8")) if a.why else {},
               "extra_md": Path(a.extra_md).read_text(encoding="utf-8") if a.extra_md else ""}
        Path(a.out).write_text(render(payload, ctx), encoding="utf-8")
        print("wrote", a.out, "control", ctx["control"], "gone", len(gone))


def pct(new, old):
    if old == 0:
        return None if new == 0 else float("inf")
    return (new - old) / old * 100.0


def fmt_pct(new, old):
    v = pct(new, old)
    if v is None:
        return "0"
    if v == float("inf"):
        return "new"
    return f"{v:+.0f}%"


def registry_rows(path: Path):
    try:
        return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except OSError:
        return []


# Appendix A names the function that held the call line; the registry key sometimes names the inner function the
# wrapper delegates to (or the call moved into the callee in a later refactor). Same prompt, matched by name and
# confirmed by reading the callers in master (J-2977).
ALIAS = {
    "core.deliberation:deliberate": "core.deliberation:_deliberate_run",
    "core.commitment_ledger:_scan_shadow_locked": "core.commitment_ledger:_scan_shadow_body",
    "nodes.subconscious_node:SubconsciousNode._synthesise_theme": "nodes.subconscious_node:SubconsciousNode._synthesise_theme_ex",
    "core.essay_lesson:compose": "core.essay_lesson:_compose_once",
}


def registry_match(key: str, reg):
    """registry rows whose keys cover this Appendix A key (`mod:Qual.func(Class)`)."""
    m = re.match(r"^([\w.]+):(.*?)(?:\((\w+)\))?$", key)
    if not m:
        return []
    mod, fn, cls = m.group(1), m.group(2), m.group(3)
    out = []
    for r in reg:
        for k in r.get("keys", []):
            base = k.split("#", 1)[0]
            if base == f"{mod}:{fn}" or base == ALIAS.get(f"{mod}:{fn}"):
                out.append(r["id"])
                break
            if cls and base.endswith(":" + cls) and base.startswith("nodes."):
                out.append(r["id"])
                break
    return out


def render(p, ctx) -> str:
    inv, now = p["inv"], p["now"]
    old_all = {k: v["old"] for k, v in inv.items() if v.get("old")}
    old_all.update(p["inv_old_only"])
    keys = set(inv) | set(old_all)
    reg = ctx["reg"]
    L = []
    w = L.append
    w("# Appendix A, re-joined per git commit (J-2977, F-3670)")
    w("")
    w(f"Generated {datetime.date.today().isoformat()} by `scripts/rejoin_appendix_a_j2977.py` from `data/llm_latency.jsonl` (read-only), "
      f"`data/nascence.log` (process starts) and the git history of the code. The old inventory "
      f"(`docs/reviews/du_prompt_inventory_2026-10-31.md`, Appendix A) is untouched.")
    w("")
    w("## 1. What was wrong, and how this table is built")
    w("")
    w("A telemetry label is `module:line(Class)`: the line number in the file **at the time of the call**. Appendix A looked every label up in the "
      "file as it stood on 2026-10-31, so any label written before an edit that shifted the file landed inside whatever function now sits on that line "
      "(T2 was credited with Active Imagination's calls; F-3670). This table looks each label up in the version of the file that **was running**.")
    w("")
    w("Which version was running. Du reads its code once, at process start. So the version is the newest mainline commit of that file at or before the "
      f"last `Nascence is awake` line in `data/nascence.log` ({p['process_starts']} starts found), not the newest commit before the row's timestamp. "
      "Per row the script tries, in order: B (commit at the last process start), A (commit at the row's own timestamp, the brief's method), C (a commit made while that process was running, "
      "for an edit that was live at start and only committed later); the first in which the label's line is the start of a plausible call "
      "(an `ast.Call` named like call/ask/judge/generate, or an `await`) wins.")
    w("")
    t = p["resolution_tags"]
    w(f"- Resolution of the {sum(t.values()):,} labelled rows read (30 days before the later anchor): logged function name `fn` (J-3760) {t.get('L', 0):,}, B {t.get('B', 0):,}, A {t.get('A', 0)}, C {t.get('C', 0)}, "
      f"no valid call line in any candidate {t.get('B!', 0)} (kept as B, unvalidated), no file to look up {t.get('nopath', 0)} (`asyncio.events`, `__main__`).")
    w(f"- Validation of the predicate (`--calibrate`, labels of the last 12 h of data): {ctx['cal_b']} under B against {ctx['cal_a']} under A. "
      "That gap is the evidence that the running version is the right one to join to: the newest commit before the row is wrong for about one row in six, "
      "because commits land after the restart that loaded the older code.")
    w(f"- Control: the OLD method (labels joined to the file as of the anchor) recomputed here reproduces {ctx['control']} of the old table's rows exactly, "
      "so the pipeline reads the same data the inventory did. Anchor = 2026-10-31 23:00 local, found by search (it reproduces `core.deliberation:187` = 13602 / 1669 / 491 exactly).")
    w("- Function names are the names in the version that ran. A function renamed later appears under its old name and is marked `†` (not in the current file); "
      "its calls are real, they belong to the renamed function.")
    w("- Not re-joined: the three raw-HTTP rows (`judge_panel`, `left_lane`, `lane2`). Their label has no line number, so nothing drifts, and `data/llm_calls.jsonl` now holds only 2026-11-05, "
      "so the 10-31 window cannot be recomputed; they are carried from the old table at the bottom of section 2.")
    w("")
    w("## 2. Corrected Appendix A (windows end 2026-10-31 23:00, the inventory's own anchor)")
    w("")
    w("`old` = the inventory's figure for the same function name (0 = row absent). `Δ30d` = rejoined against old. `now` = the same rejoin with windows ending at the last telemetry row "
      f"({p['anchor_now_local'][:16].replace('T', ' ')}, when Du was stopped). `†` = name not in the current file.")
    w("")
    w("| 30d | 7d | 24h | old 30d | Δ30d | now 30d / 7d / 24h | module:function(class) | models@port (30d) | raw labels (30d) |")
    w("|---|---|---|---|---|---|---|---|---|")

    def sk(k):
        n = (inv.get(k, {}).get("new") or [0, 0, 0])
        return (-n[1], -n[0], k)

    only_old = []
    for k in sorted(keys, key=sk):
        n = inv.get(k, {}).get("new") or [0, 0, 0]
        o = old_all.get(k) or [0, 0, 0]
        nw = now.get(k) or [0, 0, 0]
        if not any(n) and not any(nw):
            only_old.append(k)
            continue                                   # only in the old table: listed in section 3
        mark = " †" if k in ctx["gone"] else ""
        rl = p["raws"].get(k, [])
        rtxt = ", ".join(rl[:3]) + (f" (+{len(rl) - 3})" if len(rl) > 3 else "")
        w(f"| {n[0]} | {n[1]} | {n[2]} | {o[0]} | {fmt_pct(n[0], o[0])} | {nw[0]} / {nw[1]} / {nw[2]} | {k}{mark} | {p['models'].get(k, '')} | {rtxt} |")
    w("")
    w("Carried unchanged from the old table (raw-HTTP, coarse label, ~1-day window):")
    w("")
    w("| 30d | 7d | 24h | module:function(class) | models@port | raw labels seen |")
    w("|---|---|---|---|---|---|")
    for ln in ctx["raw_http_lines"]:
        w(ln)
    w("")
    w("## 3. Rows whose 30d figure moved by more than 25 percent")
    w("")
    w("A row counts as moved if |rejoined - old| / old > 25%, or it appears or disappears. A row that is only in the old table "
      "(rejoined 30d = 0) is a label the old join pinned to a function that never ran it.")
    w("")
    w("| old 30d | rejoined 30d | Δ | 7d old -> new | function | where the calls moved (30d, labels re-attributed) |")
    w("|---|---|---|---|---|---|")
    movers = []
    for k in keys:
        n = (inv.get(k, {}).get("new") or [0, 0, 0])
        o = old_all.get(k) or [0, 0, 0]
        if n[0] == o[0]:
            continue
        v = pct(n[0], o[0])
        if v is not None and abs(v) > 25:
            movers.append((abs(n[0] - o[0]), k, o, n))
    movers.sort(reverse=True)
    def short(k):
        return k.split(":", 1)[1] if ":" in k else k

    def why(k):
        gain = sorted(((c, o) for o, n, c in p["flows"] if n == k), reverse=True)[:2]
        lose = sorted(((c, n) for o, n, c in p["flows"] if o == k), reverse=True)[:2]
        bits = []
        if gain:
            bits.append("gains " + ", ".join(f"{c} from {short(o)}" for c, o in gain))
        if lose:
            bits.append("loses " + ", ".join(f"{c} to {short(n)}" for c, n in lose))
        return "; ".join(bits)

    for _d, k, o, n in movers:
        w(f"| {o[0]} | {n[0]} | {fmt_pct(n[0], o[0])} | {o[1]} -> {n[1]} | {k}{' †' if k in ctx['gone'] else ''} | {ctx['why'].get(k) or why(k)} |")
    w("")
    w(f"{len(movers)} rows moved by more than 25 percent, of {len(keys)} distinct function keys.")
    w("")
    w("## 4. Prompt-registry rows (`calls_7d`)")
    w("")
    w("`prompt_registry.py` stores `calls_7d` per row but has no flag to set it (`set` takes `--note`, not a count), so the registry owner has to edit the field "
      "another way or add `--calls-7d` (follow-up job). Listed: every registry row whose covered function has a changed 7d, or a 30d that moved by more than 25 percent.")
    w("")
    w("| row | stored calls_7d | Appendix A 7d (old -> rejoined) | 30d (old -> rejoined) | covered keys |")
    w("|---|---|---|---|---|")
    by_row = collections.defaultdict(list)
    for k in keys:
        for pid in registry_match(k, reg):
            by_row[pid].append(k)
    regmap = {r["id"]: r for r in reg}
    cmds = []
    for pid in sorted(by_row):
        ks = by_row[pid]
        o7 = sum((old_all.get(k) or [0, 0, 0])[1] for k in ks)
        n7 = sum((inv.get(k, {}).get("new") or [0, 0, 0])[1] for k in ks)
        o30 = sum((old_all.get(k) or [0, 0, 0])[0] for k in ks)
        n30 = sum((inv.get(k, {}).get("new") or [0, 0, 0])[0] for k in ks)
        stored = regmap[pid].get("calls_7d")
        moved30 = (o30 and abs(n30 - o30) / o30 > 0.25) or (o30 == 0 and n30)
        if o7 == n7 and not moved30:
            continue
        short = "; ".join(sorted(k.split(":", 1)[1] for k in ks))[:100]
        w(f"| {pid} | {stored if stored is not None else ''} | {o7} -> {n7} | {o30} -> {n30} | {short} |")
        if o7 != n7:                                   # calls_7d is only wrong where the 7d column moved
            note = f"Appendix A re-join (J-2977): 7d at the 10-31 anchor is {n7}, not {o7}; stored calls_7d {stored}"
            old_note = regmap[pid].get("note", "")
            cmds.append((pid, (old_note + " | " if old_note else "") + note))
    w("")
    w("Commands for the orchestrator, only for rows whose 7d column moved. `set --note` REPLACES the field, so each command repeats the row's current note and appends the correction:")
    w("")
    w("```")
    for pid, n in cmds:
        w(f'prompt_registry.py set {pid} --note "{n.replace(chr(34), chr(39))}" --session J-2977')
    w("```")
    w("")
    w(ctx.get("extra_md", ""))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
