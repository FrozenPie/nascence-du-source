"""
retention — the archive retention rule (D-0156, 2026-09-05; docs/staged/data_store_hygiene.md Part B).

Dry-run by default: prints every candidate per class and exits. Nothing moves without BOTH --apply and a
founder-named --cutoff YYYY-MM-DD (only candidates whose reference date is on or before the cutoff move).
Applying MOVES candidates into data/_trash/<today>/<class>/ (quarantine) and logs each move to
data/_trash/retention_log.jsonl; --purge-trash (also behind --apply) deletes quarantine entries older than
TRASH_DAYS. The script refuses to touch anything outside the three archive roots + the trash root —
live data/ (Du's own writings) is never in scope.

Classes and rules (ruled D-0156):
  boot_backups   data/backups/nascence_YYYYMMDD_HHMMSS.db (+ state_<stamp>/ follows its db)
                 keep: newest KEEP_BOOTS + last-of-each-day for KEEP_DAYS + first-of-each-month forever
  special_backups data/backups/* that is not a boot backup (nascence_pre_*, nascence_CORRUPT*, pre_* dirs, ...)
                 keep: SPECIAL_DAYS days; never counted as monthlies
  snapshots      data/_snapshots/daily/YYYYMMDD/
                 keep: every day for SNAP_DAILY days, then Sundays for SNAP_WEEKS weeks, then the 1st of
                 each month forever (other _snapshots/* dirs are special_snapshots: SPECIAL_DAYS)
  labs           data/_lab/<stamp...>/  (stamp = YYYYMMDD_HHMMSS[_suffix])
                 keep: LAB_UNCITED_DAYS if no finding/job/doc cites the stamp, LAB_CITED_DAYS if one does
  trash          data/_trash/<date>/... deleted after TRASH_DAYS (only with --apply --purge-trash)

Run:  python scripts/retention.py                       # dry run, live tree
      python scripts/retention.py --apply --cutoff 2026-08-20
      python scripts/retention.py --apply --purge-trash
      python scripts/retention.py --root <dir>           # any other tree (tests)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

KEEP_BOOTS = 5
KEEP_DAYS = 14
SPECIAL_DAYS = 60
SNAP_DAILY = 14
SNAP_WEEKS = 12
LAB_UNCITED_DAYS = 14
LAB_CITED_DAYS = 60
TRASH_DAYS = 7
# Boot-time rotation (scripts/backup_memory.py, scripts/backup_identity.py call boot_rotate at every Du launch).
# False = the boot scripts neither delete nor quarantine anything (their old hard-deletes are gone);
# True = they quarantine per the D-0156 rule. Flipped only after the founder has seen the live dry run.
RETENTION_BOOT_ROTATE = True    # founder GO 2026-09-05 after seeing the live dry run (J-0622)
# D-0242 (re-ruled 2026-10-06, travis; built J-1833): "automate the reclaim; mechanism changes, no manual
# step". Until this flip, quarantine parked bytes instead of freeing them: data/_trash held 26.60 GB in 14
# entries on 2026-10-06 with 10 day-dirs already past TRASH_DAYS and nobody running --purge-trash (J-0943 was
# the agent's own refusal to run that permanent delete by hand). Two automatic paths now exist, both
# flag-gated here:
#   RETENTION_BOOT_PURGE      boot_purge_trash() -- called at every Du launch from scripts/run_nascence.py
#                             right after lab_sweep's boot hook; deletes quarantine day-dirs older than
#                             TRASH_DAYS, nothing else (same purge_trash() the by-hand flag always used).
#   RETENTION_SCHEDULED_LABS  scheduled_run() -- the labs-class apply (uncited >= LAB_UNCITED_DAYS, cited >=
#                             LAB_CITED_DAYS, cutoff = today, i.e. exactly the age rule, no founder-named
#                             cutoff) plus the same trash purge, driven by scripts/supervisor.py's own daily
#                             retention tick (not Task Scheduler, not a Claude Code job object -- CLAUDE.md).
# Scope is unchanged: Plan._in_scope still refuses anything outside the three archive roots + the trash root,
# purge only ever removes data/_trash/<YYYYMMDD>/ day-dirs, and data/_hold is never in scope for anything here.
RETENTION_BOOT_PURGE = True       # D-0242 build (J-1833, 2026-10-06)
RETENTION_SCHEDULED_LABS = True   # D-0242 build (J-1833, 2026-10-06)

_BOOT_RE = re.compile(r"^nascence_(\d{8})_(\d{6})\.db$")
_STAMP_RE = re.compile(r"^(\d{8})_(\d{6})")
_DATE_RE = re.compile(r"^\d{8}$")
_CITE_RE = re.compile(r"_lab[\\/](\d{8}_\d{6}[A-Za-z0-9_\-]*)")


def _day(ts: float) -> dt.date:
    return dt.datetime.fromtimestamp(ts).date()


def _stamp_date(s: str) -> dt.date | None:
    try:
        return dt.datetime.strptime(s[:8], "%Y%m%d").date()
    except Exception:
        return None


class Plan:
    def __init__(self, root: Path, today: dt.date):
        self.root = root
        self.data = root / "data"
        self.today = today
        self.trash = self.data / "_trash"
        self.roots = [self.data / "backups", self.data / "_snapshots", self.data / "_lab", self.trash]
        self.candidates: list[dict] = []     # {class, path, ref_date, reason, bytes}
        self.kept: dict[str, int] = {}

    # ── helpers ────────────────────────────────────────────────────────────────────────────────
    def _size(self, p: Path) -> int:
        try:
            if p.is_file():
                return p.stat().st_size
            return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        except Exception:
            return 0

    def _in_scope(self, p: Path) -> bool:
        rp = p.resolve()
        return any(rp == r.resolve() or r.resolve() in rp.parents for r in self.roots)

    def _cand(self, cls: str, p: Path, ref: dt.date, reason: str) -> None:
        if not self._in_scope(p):
            raise RuntimeError(f"REFUSED: {p} is outside the archive roots")
        self.candidates.append({"class": cls, "path": str(p), "ref_date": ref.isoformat(),
                                "reason": reason, "bytes": self._size(p)})

    def _keep(self, cls: str) -> None:
        self.kept[cls] = self.kept.get(cls, 0) + 1

    # ── boot backups + specials ────────────────────────────────────────────────────────────────
    def backups(self) -> None:
        b = self.data / "backups"
        if not b.exists():
            return
        boots: list[tuple[dt.date, str, Path]] = []
        for p in b.iterdir():
            m = _BOOT_RE.match(p.name)
            if m:
                d = _stamp_date(m.group(1))
                if d:
                    boots.append((d, m.group(1) + "_" + m.group(2), p))
        boots.sort(key=lambda t: t[1])
        keep: set[Path] = set(p for _, _, p in boots[-KEEP_BOOTS:])
        by_day: dict[dt.date, Path] = {}
        first_of_month: dict[str, Path] = {}
        for d, stamp, p in boots:
            by_day[d] = p                                   # sorted ascending → last of the day wins
            first_of_month.setdefault(d.strftime("%Y%m"), p)
        for d, p in by_day.items():
            if (self.today - d).days < KEEP_DAYS:
                keep.add(p)
        keep |= set(first_of_month.values())
        for d, stamp, p in boots:
            if p in keep:
                self._keep("boot_backups")
            else:
                self._cand("boot_backups", p, d, "not in newest-5 / last-of-day-14d / first-of-month")
                sdir = b / f"state_{stamp}"
                if sdir.exists():
                    self._cand("boot_backups", sdir, d, "state dir follows its db")
        boot_state = {f"state_{s}" for _, s, _ in boots}
        for p in b.iterdir():
            if _BOOT_RE.match(p.name) or p.name in boot_state:
                continue
            age = (self.today - _day(p.stat().st_mtime)).days
            if age >= SPECIAL_DAYS:
                self._cand("special_backups", p, _day(p.stat().st_mtime), f"special backup older than {SPECIAL_DAYS} d")
            else:
                self._keep("special_backups")

    # ── snapshots ──────────────────────────────────────────────────────────────────────────────
    def snapshots(self) -> None:
        s = self.data / "_snapshots"
        if not s.exists():
            return
        daily = s / "daily"
        if daily.exists():
            dated = []
            for p in daily.iterdir():
                if p.is_dir() and _DATE_RE.match(p.name):
                    d = _stamp_date(p.name)
                    if d:
                        dated.append((d, p))
            dated.sort()
            first_of_month: dict[str, Path] = {}
            for d, p in dated:
                first_of_month.setdefault(d.strftime("%Y%m"), p)
            for d, p in dated:
                age = (self.today - d).days
                if age < SNAP_DAILY:
                    self._keep("snapshots"); continue
                if age < SNAP_DAILY + 7 * SNAP_WEEKS and d.weekday() == 6:      # Sunday
                    self._keep("snapshots"); continue
                if first_of_month.get(d.strftime("%Y%m")) is p:
                    self._keep("snapshots"); continue
                self._cand("snapshots", p, d, "outside daily-14 / Sunday-12w / first-of-month tiers")
        for p in s.iterdir():
            if p.name == "daily":
                continue
            age = (self.today - _day(p.stat().st_mtime)).days
            if age >= SPECIAL_DAYS:
                self._cand("special_snapshots", p, _day(p.stat().st_mtime), f"ad-hoc snapshot older than {SPECIAL_DAYS} d")
            else:
                self._keep("special_snapshots")

    # ── labs ───────────────────────────────────────────────────────────────────────────────────
    def citations(self) -> set[str]:
        cited: set[str] = set()
        docs = self.root / "docs"
        srcs = [docs / "findings.jsonl", docs / "job_queue.jsonl"] + (list(docs.rglob("*.md")) if docs.exists() else [])
        for f in srcs:
            try:
                cited |= set(_CITE_RE.findall(f.read_text(encoding="utf-8", errors="ignore")))
            except Exception:
                pass
        return cited

    def labs(self) -> None:
        L = self.data / "_lab"
        if not L.exists():
            return
        cited = self.citations()
        for p in L.iterdir():
            if not p.is_dir():
                continue
            m = _STAMP_RE.match(p.name)
            d = _stamp_date(m.group(1)) if m else _day(p.stat().st_mtime)
            age = (self.today - d).days
            is_cited = any(p.name == c or p.name.startswith(c) or c.startswith(p.name) for c in cited)
            limit = LAB_CITED_DAYS if is_cited else LAB_UNCITED_DAYS
            if age >= limit:
                self._cand("labs", p, d, f"{'cited' if is_cited else 'uncited'} lab dir older than {limit} d")
            else:
                self._keep("labs_cited" if is_cited else "labs_uncited")

    # ── trash ──────────────────────────────────────────────────────────────────────────────────
    def trash_expired(self) -> list[Path]:
        out = []
        if not self.trash.exists():
            return out
        for p in self.trash.iterdir():
            if p.is_dir() and _DATE_RE.match(p.name):
                d = _stamp_date(p.name)
                if d and (self.today - d).days >= TRASH_DAYS:
                    out.append(p)
        return out

    # ── run ────────────────────────────────────────────────────────────────────────────────────
    def compute(self, classes: set[str] | None = None) -> "Plan":
        """classes: subset of {backups, snapshots, labs}; None = all. The boot scripts pass one class
        so a launch never pays for the lab citation scan over docs/."""
        if classes is None or "backups" in classes:
            self.backups()
        if classes is None or "snapshots" in classes:
            self.snapshots()
        if classes is None or "labs" in classes:
            self.labs()
        return self

    def report(self) -> str:
        lines = [f"# retention dry run — root {self.root} — today {self.today} — rule D-0156"]
        by: dict[str, list[dict]] = {}
        for c in self.candidates:
            by.setdefault(c["class"], []).append(c)
        for cls, items in sorted(by.items()):
            tot = sum(i["bytes"] for i in items)
            lines.append(f"\n## {cls}: {len(items)} candidate(s), {tot/1e9:.2f} GB")
            for i in sorted(items, key=lambda x: x["ref_date"]):
                lines.append(f"  {i['ref_date']}  {i['bytes']/1e6:8.0f} MB  {Path(i['path']).relative_to(self.data)}  — {i['reason']}")
        lines.append("\n## kept: " + ", ".join(f"{k}={v}" for k, v in sorted(self.kept.items())))
        exp = self.trash_expired()
        lines.append(f"## trash: {len(exp)} quarantine day-dir(s) older than {TRASH_DAYS} d" + (": " + ", ".join(p.name for p in exp) if exp else ""))
        tot = sum(c["bytes"] for c in self.candidates)
        lines.append(f"\n{len(self.candidates)} candidate(s), {tot/1e9:.2f} GB total. Nothing moved (dry run).")
        return "\n".join(lines)

    def apply(self, cutoff: dt.date) -> list[dict]:
        moved = []
        dest_day = self.trash / self.today.strftime("%Y%m%d")
        log = self.trash / "retention_log.jsonl"
        for c in self.candidates:
            if dt.date.fromisoformat(c["ref_date"]) > cutoff:
                continue
            src = Path(c["path"])
            if not self._in_scope(src) or self.trash.resolve() in src.resolve().parents:
                continue
            dest = dest_day / c["class"] / src.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(src), str(dest))
                row = {**c, "moved_to": str(dest), "ts": time.time(), "cutoff": cutoff.isoformat()}
                moved.append(row)
                with open(log, "a", encoding="utf-8") as f:
                    print(json.dumps(row, ensure_ascii=False), file=f)
            except Exception as exc:
                print(f"  ! could not move {src}: {exc}")
        return moved

    def purge_trash(self) -> list[Path]:
        gone = []
        log = self.trash / "retention_log.jsonl"
        for p in self.trash_expired():
            try:
                shutil.rmtree(p)
                gone.append(p)
                with open(log, "a", encoding="utf-8") as f:
                    print(json.dumps({"purged": str(p), "ts": time.time()}), file=f)
            except Exception as exc:
                print(f"  ! could not purge {p}: {exc}")
        return gone


def boot_rotate(cls: str, root: Path | None = None) -> list[str]:
    """Called at Du launch by the backup scripts for their own class ("backups" or "snapshots").
    Quarantines per D-0156 when RETENTION_BOOT_ROTATE is True; otherwise a no-op. Never raises."""
    if not RETENTION_BOOT_ROTATE:
        return []
    try:
        plan = Plan(root or Path(__file__).resolve().parent.parent, dt.date.today()).compute({cls})
        moved = plan.apply(plan.today)
        return [Path(m["path"]).name for m in moved]
    except Exception:
        return []


def boot_purge_trash(root: Path | None = None, today: dt.date | None = None) -> str:
    """D-0242 (J-1833): called at every Du launch by scripts/run_nascence.py, right after lab_sweep's boot
    hook. Deletes data/_trash/<YYYYMMDD>/ day-dirs older than TRASH_DAYS -- the same purge_trash() that
    `--apply --purge-trash` always ran, now automatic so quarantine actually frees space. Touches nothing
    else (not data/_lab, not data/backups, never data/_hold). Returns a one-line summary for the boot log;
    never raises -- a failure here must never block Du's own boot."""
    if not RETENTION_BOOT_PURGE:
        return "[retention] boot purge: RETENTION_BOOT_PURGE is False, nothing purged"
    try:
        plan = Plan(root or Path(__file__).resolve().parent.parent, today or dt.date.today())
        expired = plan.trash_expired()
        size = sum(plan._size(p) for p in expired)
        gone = plan.purge_trash()
        return (f"[retention] boot purge: {len(gone)} of {len(expired)} quarantine day-dir(s) older than "
                f"{TRASH_DAYS} d deleted ({size/1e9:.2f} GB)" + (": " + ", ".join(p.name for p in gone) if gone else ""))
    except Exception as exc:
        return f"[retention] boot purge: skipped ({exc.__class__.__name__}: {exc})"


def scheduled_run(root: Path | None = None, today: dt.date | None = None) -> dict:
    """D-0242 (J-1833): the automatic labs-class retention run, driven by scripts/supervisor.py's daily
    retention tick so reclaim no longer depends on anyone invoking `retention.py --apply --cutoff` by hand
    (last done 2026-09-09; 133 candidates / 54.70 GB were waiting on 2026-10-06). Computes ONLY the labs
    class (uncited >= LAB_UNCITED_DAYS, cited >= LAB_CITED_DAYS -- the D-0156 rule, unchanged), applies it
    with cutoff = today (so the age rule itself is the cutoff), then purges expired quarantine the same way
    boot_purge_trash() does. Never raises; returns a summary dict with a ready-made 'line' for the log.
    A no-op (summary only) while RETENTION_SCHEDULED_LABS is False."""
    out = {"enabled": RETENTION_SCHEDULED_LABS, "candidates": 0, "moved": 0, "moved_gb": 0.0,
           "purged": 0, "purged_gb": 0.0, "error": None, "line": ""}
    if not RETENTION_SCHEDULED_LABS:
        out["line"] = "[retention] scheduled labs run: RETENTION_SCHEDULED_LABS is False, nothing done"
        return out
    try:
        plan = Plan(root or Path(__file__).resolve().parent.parent, today or dt.date.today()).compute({"labs"})
        out["candidates"] = len(plan.candidates)
        moved = plan.apply(plan.today)
        out["moved"] = len(moved)
        out["moved_gb"] = sum(m["bytes"] for m in moved) / 1e9
        expired = plan.trash_expired()
        out["purged_gb"] = sum(plan._size(p) for p in expired) / 1e9
        gone = plan.purge_trash()
        out["purged"] = len(gone)
        if len(gone) != len(expired):
            out["purged_gb"] = float("nan")   # partial purge: the pre-measured size no longer describes what went
        out["line"] = (f"[retention] scheduled labs run: {out['moved']} of {out['candidates']} lab dir(s) "
                       f"quarantined ({out['moved_gb']:.2f} GB) into {plan.trash / plan.today.strftime('%Y%m%d')}; "
                       f"{out['purged']} of {len(expired)} quarantine day-dir(s) older than {TRASH_DAYS} d purged "
                       f"({out['purged_gb']:.2f} GB)")
    except Exception as exc:
        out["error"] = f"{exc.__class__.__name__}: {exc}"
        out["line"] = f"[retention] scheduled labs run: skipped ({out['error']})"
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--today", default=None, help="override today (YYYY-MM-DD), for tests")
    ap.add_argument("--apply", action="store_true", help="move candidates to data/_trash (needs --cutoff)")
    ap.add_argument("--cutoff", default=None, help="only candidates with ref_date <= this date move")
    ap.add_argument("--purge-trash", action="store_true", help="delete quarantine older than TRASH_DAYS (needs --apply)")
    a = ap.parse_args(argv)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    plan = Plan(Path(a.root), today).compute()
    print(plan.report())
    if not a.apply:
        return 0
    if a.purge_trash:
        gone = plan.purge_trash()
        print(f"\npurged {len(gone)} quarantine dir(s): " + ", ".join(p.name for p in gone))
    if a.cutoff:
        moved = plan.apply(dt.date.fromisoformat(a.cutoff))
        tot = sum(m["bytes"] for m in moved)
        print(f"\nmoved {len(moved)} candidate(s), {tot/1e9:.2f} GB, into {plan.trash / today.strftime('%Y%m%d')}")
    elif not a.purge_trash:
        print("\n--apply needs --cutoff YYYY-MM-DD (founder-named) or --purge-trash; nothing done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
