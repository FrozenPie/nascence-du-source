"""
Dream Overhaul — Experiment A (J-1059): four-arm in-vitro A/B on identical seeds.
docs/staged/dream_overhaul.md sec 6. commit=False, zero live writes -- see isolation note below.

Arms (fixed 3 scenes, MAX_EPISODES forced to 3 so length is not a variable):
  A0 current engine   (materials re-fed each scene, recall block each scene)  -- the control
  A1 no re-feed       (scene 1 gets everything; scenes 2/3 get only the continuity block)
  A2 no re-feed + dormant node (A1 + one dormant fragment in scene 1's seed)
  A3 dormant only, re-feed kept (isolates the dormant effect from the re-feed effect)

ISOLATION (job-queue isolation="required"): every call in this script goes through
lab_env.isolate(), which redirects core.memory.store.DB_PATH to a COPY of the live DB before
any of nodes.dream_node / core.night / core.associative_recall / core.memory_edges touch it --
this script never opens C:\\Nascence\\data\\memory\\nascence.db directly, read or write. commit=False
on every synthesise() call additionally skips _store_episode/_bridge_final/_ground_symbols/_log_arc
(verified by reading synthesise() -- the `if commit:` block at nodes/dream_node.py gates all four).
Sidecars that write OUTSIDE the DB_PATH choke point (core.telemetry's _CALLS/_STATIONS/_LAT; Phase 1's
_DREAM_STATE_LOG in nodes.dream_node and core.dream_probe's own log) are covered too: telemetry's three
globals are redirected via isolate()'s `also=`, and _DREAM_STATE_LOG / dream_probe.log_seed_pairs are
simply never reached because this script calls DreamNode._gen_episode() directly in its own loop
(mirroring scripts/dream_arc_test.py's established pattern) rather than calling synthesise() --
_log_transition() and log_seed_pairs() are called from INSIDE synthesise()'s own loop body, never from
_gen_episode or _gather_materials. Backstop: this script prints the live DB's mtime before and after
the whole run so a human (or the finding write-up) can confirm it never moved.

WORKTREE NOTE: this script must import nodes.dream_node / core.* from THIS worktree (it carries J-1057's
Phase 1 seed-capture fields), not from C:\\Nascence directly -- lab_env.py hardcodes C:\\Nascence onto
sys.path[0]. Import order below (lab_env first, then insert this worktree's root at 0) makes the
worktree win for every module imported after that point; see the long comment at the top of main().
"""
from __future__ import annotations

import sys, os, json, time, random, argparse, asyncio, hashlib
from pathlib import Path

_WORKTREE = Path(__file__).parent.parent.resolve()

# ---- import order matters here: see module docstring -----------------------------------------
sys.path.insert(0, r"C:\Users\USER\.claude\skills\job-queue")
import lab_env                      # this pushes C:\Nascence to sys.path[0] as a side effect
sys.path.insert(0, str(_WORKTREE))  # now the worktree wins for every NEW import below
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from types import SimpleNamespace
from core.schema import SERVE_CHAINS  # noqa: F401 (import confirms worktree resolution below)
from core import axiom_layers as al
from core import night as night_mod
from core.memory import store as mstore
from core import associative_recall as assoc
from core import memory_edges as medges
import nodes.dream_node as dn

SCRATCH = Path(r"C:\Users\USER\AppData\Local\Temp\claude\C--Nascence\00e97919-3e83-4e8f-8aaa-b0d563d7d361\scratchpad")
LIVE_DB = Path(r"C:\Nascence\data\memory\nascence.db")

ARMS = ["A0", "A1", "A2", "A3"]
NO_REFEED_ARMS = {"A1", "A2"}
DORMANT_ARMS = {"A2", "A3"}
N_SCENES = 3  # forced -- "length is not a variable"

DORMANT_ORIGINS = ("lived", "reading", "correspondence", "study", "research")  # D-0231 filter
DORMANT_MIN_AGE_DAYS = 30
DORMANT_CO_RECALL_ABSENT_DAYS = 14


def worktree_check():
    print(f"[setup] nodes.dream_node resolved from: {dn.__file__}")
    print(f"[setup] core.memory.store resolved from: {mstore.__file__}")
    assert str(_WORKTREE).lower() in dn.__file__.lower(), "dream_node did NOT resolve from the worktree!"
    assert str(_WORKTREE).lower() in mstore.__file__.lower(), "store did NOT resolve from the worktree!"
    assert hasattr(dn.DreamNode(), "_gather_materials")
    # Phase 1 (J-1057) sanity: confirms we really have the worktree's post-J-1057 code, not a stale copy.
    src = Path(dn.__file__).read_text(encoding="utf-8")
    assert "_seed_fragment_ids" in src, "worktree dream_node.py missing J-1057 Phase 1 fields?"
    print("[setup] worktree resolution OK (J-1057 fields present)")


# ---------------------------------------------------------------------------
# Seed freezing
# ---------------------------------------------------------------------------

def _h12(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8", "replace")).hexdigest()[:12]


def _bounded_day_residue(hist_now: float, k: int = 2) -> list[str]:
    """J-1077 ROOT-CAUSE FIX, replaces the plain core.night.dream_lag_material(now=hist_now, k=k) call
    below. Diagnosed live this run: with day_step=4.0 and start_offset_days=10.0 (14 seeds spanning
    ~10-62 real days back), ALL 14 frozen seeds still collided into 1 distinct material_hash (and
    identical recalled_ids) -- worse than the pilot's 1-day-step run (2 distinct blocks / 6 seeds).
    Widening the day_step was NOT the real fix. Root cause (read core.night.day_material +
    dream_lag_material directly): dream_lag_material's OWN "recent" window call --
    `day_material(recent_lo, k=k_recent)` -- passes NO `until_ts`, so its SQL is
    `WHERE timestamp > recent_lo` with no upper bound. For a LIVE call (now=None -> real time.time())
    that is correct (nothing exists past real "now" anyway). For a HISTORICAL hist_now, it is wrong:
    the query pulls memory_fragments ranked by importance/recency ALL THE WAY UP TO THE REAL PRESENT,
    so `materials[0]` (built from this recent block) ends up dominated by genuinely-recent real
    content regardless of how far back hist_now is shifted -- explaining the total collision. The
    "far" window call already passes `until_ts=far_hi` and is NOT the source of the bug.
    This function reproduces dream_lag_material's own two-window blend (same constants, same
    DREAM_LAG_RECENT_SHARE split) but calls core.night.day_material directly with `until_ts=hist_now`
    on BOTH windows, closing the open upper bound. day_material already supports `until_ts` (used by
    the far window already) -- this is a call-site fix, NOT a change to core/night.py (production,
    live-engine code is never touched; this lives only in this lab script)."""
    recent_lo = hist_now - night_mod.DREAM_LAG_RECENT_DAYS[1] * 86400.0
    far_lo = hist_now - night_mod.DREAM_LAG_FAR_DAYS[1] * 86400.0
    far_hi = hist_now - night_mod.DREAM_LAG_FAR_DAYS[0] * 86400.0
    k_recent = max(1, round(k * night_mod.DREAM_LAG_RECENT_SHARE))
    k_far = max(0, k - k_recent) or (1 if k >= 2 else 0)
    recent = night_mod.day_material(recent_lo, k=k_recent, until_ts=hist_now)  # <- the fix: bound this too
    far = night_mod.day_material(far_lo, k=k_far, until_ts=far_hi) if k_far else []
    blocks = recent + far
    return blocks[:k] if blocks else night_mod.day_material(hist_now - 7 * 86400.0, k=k, until_ts=hist_now)


def freeze_seeds(n_seeds: int, lab_dir: Path, spirit_name: str, axiom: str, day_step: float = 4.0,
                  start_offset_days: float = 0.0) -> list[dict]:
    """Build n_seeds real seeds. Day residue varies per seed (real historical `now` timestamps,
    spaced `day_step` real days apart, via the bounded _bounded_day_residue() above -- NOT
    core.night.dream_lag_material() directly, see that function's own docstring for why). J-1077 fix
    (docs/lab/dream_experiment_a_2026-09-17.md limitation 2): the pilot's 1-day-apart steps did NOT
    reliably change the day-residue window on this corpus -- 6 of 6 pilot seeds collided into only 2
    distinct day-residue blocks; widening day_step alone (tried 4.0 + a 10-day start offset, 14 seeds
    spanning ~62 days) made it WORSE (1/14 distinct) until the real root cause (an unbounded upper-end
    query inside dream_lag_material's own "recent" window) was found and worked around, see
    _bounded_day_residue(). Checked at run time whether real historical Phase-1-instrumented
    dream_log.jsonl arcs (J-1057, F-1471) exist yet to draw `now` from instead of arbitrary offsets:
    as of 2026-09-18, data/dream_log.jsonl has 0 rows carrying the Phase-1 'seed'/'engine' keys (Du has
    not yet been restarted onto the wt_coupled_cluster_2 build) -- that path is NOT feasible yet.
    `start_offset_days` shifts the whole window further back (real days) so a second/third batch of
    seeds for the same experiment does not re-freeze the exact same `now` values as an earlier batch.
    Tension is pulled ONCE from the live (copied) subconscious_state.json snapshot and reused across
    all seeds -- there is no historical-tension reconstruction available (_load_top_tensions has no
    `now` parameter, it reads the current snapshot only); this is a documented approximation, not a
    hidden one. Recalled fragments and the dormant candidate DO vary per seed (both keyed on that
    seed's own day-block text). Everything here is READ-ONLY against the (already-isolated) DB copy."""
    node = dn.DreamNode()
    now0 = time.time() - start_offset_days * 86400.0
    tension_blocks = node._load_top_tensions(1, require_charge=True)  # same snapshot for every seed
    seeds = []
    for i in range(n_seeds):
        hist_now = now0 - i * day_step * 86400.0  # i * day_step real days back
        try:
            day = _bounded_day_residue(hist_now, k=2)
        except Exception as exc:
            print(f"[freeze] seed {i}: _bounded_day_residue failed: {exc}")
            day = []
        blocks = (day or []) + (tension_blocks or [])
        if not blocks:
            print(f"[freeze] seed {i}: no day residue and no tension -- skipping (real night had nothing)")
            continue
        materials = [blocks[min(j, len(blocks) - 1)] for j in range(N_SCENES)]

        mkey = materials[0][:240]
        try:
            recalled = assoc.recall_fragments(mkey, k=6)
        except Exception as exc:
            print(f"[freeze] seed {i}: recall_fragments failed: {exc}")
            recalled = []
        recalled_ids = [r.get("fragment_id") for r in recalled if r.get("fragment_id")]
        memories_txt = ""
        if recalled:
            memories_txt = ("\n\nRemembered things from his life that may surface -- TRANSFORMED, never "
                             "narrated literally -- as the dream's images (recombine them):\n"
                             + "\n".join(f"  - {' '.join((r['content'] or '').split())[:140]}" for r in recalled))

        dormant = pick_dormant_fragment(day_block_text=materials[0], seed_ids=recalled_ids, hist_now=hist_now)

        seeds.append({
            "seed_idx": i,
            "hist_now": hist_now,
            "materials": materials,
            "memories_txt": memories_txt,
            "recalled_ids": recalled_ids,
            "material_hash": _h12(materials[0]),
            "dormant": dormant,  # dict or None
        })
        print(f"[freeze] seed {i}: day_blocks={len(day)} tension_blocks={len(tension_blocks)} "
              f"recalled={len(recalled_ids)} dormant={'yes:' + dormant['fragment_id'][:8] if dormant else 'NONE'}")
    return seeds


def pick_dormant_fragment(day_block_text: str, seed_ids: list[str], hist_now: float) -> dict | None:
    """D-0231 candidate rule (docs/staged/dream_overhaul.md sec 1): cold/chaptered, origin in
    DORMANT_ORIGINS, age >= 30d, absent from co_recall_ledger.jsonl for >= 14d, cosine to this seed's
    day block below the 30th percentile of the SAME seed's recalled-fragment cosines, no memory_edges
    edge to any seed id. Uniform among eligible. Read-only SQL against the isolated DB copy + a
    read-only scan of the (also isolated) co_recall_ledger.jsonl copy."""
    day_vec = mstore._embed(day_block_text)
    if day_vec is None:
        return None
    age_cutoff = hist_now - DORMANT_MIN_AGE_DAYS * 86400.0
    placeholders = ",".join("?" * len(DORMANT_ORIGINS))
    with mstore._connect() as conn:
        rows = conn.execute(
            f"SELECT fragment_id, content, embedding, origin, timestamp FROM memory_fragments "
            f"WHERE origin IN ({placeholders}) AND chapter_id IS NOT NULL AND timestamp <= ? "
            f"AND embedding IS NOT NULL",
            (*DORMANT_ORIGINS, age_cutoff)).fetchall()
    if not rows:
        return None

    # co_recall_ledger absence >= 14 days
    recent_ids = set()
    ledger_path = Path(mstore.DB_PATH).parent / "co_recall_ledger.jsonl"  # copied in by amain() beside
                                                                           # the lab dir's nascence.db
    cutoff = hist_now - DORMANT_CO_RECALL_ABSENT_DAYS * 86400.0
    if ledger_path.exists():
        try:
            for line in ledger_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                # J-1800 (F-2425): a *_shadow row is a would-have-shown row a kill-switched path logged
                # INSTEAD of showing anything (D-0289 monologue_shadow, D-0292 divergent_shadow) -- never
                # a recall, so it must not make a fragment look recently recalled. One definition, in core.
                if medges._is_shadow_source(row.get("source")):
                    continue
                # J-1865 (F-2487): bound the window ABOVE at hist_now too. D-0231's rule is the 14 days BEFORE
                # this simulated night; for a historical hist_now (freeze_seeds walks back in time) an
                # unbounded `>= cutoff` also counted recalls made AFTER that night, up to the real freeze
                # moment -- the same defect family as J-1077's day_material root cause.
                _row_ts = float(row.get("ts", row.get("timestamp", 0)) or 0)
                if cutoff <= _row_ts <= hist_now:
                    # J-1800 (F-2425): every row log_co_recall() has ever written carries "ids"; nothing
                    # carries "fragment_ids". Reading only the latter left recent_ids empty on every freeze
                    # before this fix (pilot6, scale14b, scaleC), so D-0231's 14-day absence rule never
                    # bit. Read the real key; tolerate the old one in case a hand-made ledger uses it.
                    ids = row.get("ids")
                    if ids is None:
                        ids = row.get("fragment_ids")
                    for fid in (ids or []):
                        recent_ids.add(fid)
        except Exception as exc:
            print(f"[dormant] co_recall_ledger scan failed (non-fatal): {exc}")

    # edges to any seed id
    edged_ids = set()
    if seed_ids:
        try:
            with medges._connect() as conn:
                ph = ",".join("?" * len(seed_ids))
                for r in conn.execute(
                        f"SELECT src_id, dst_id FROM memory_edges WHERE "
                        f"(src_kind='fragment' AND src_id IN ({ph})) OR "
                        f"(dst_kind='fragment' AND dst_id IN ({ph}))", (*seed_ids, *seed_ids)).fetchall():
                    edged_ids.add(r["src_id"]); edged_ids.add(r["dst_id"])
        except Exception as exc:
            print(f"[dormant] edge scan failed (non-fatal): {exc}")

    cands = []
    for r in rows:
        fid = r["fragment_id"]
        if fid in recent_ids or fid in edged_ids:
            continue
        vec = mstore._blob_to_vec(r["embedding"])
        cos = mstore._cosine(day_vec, vec)
        cands.append((fid, r["content"], r["origin"], cos))
    if not cands:
        return None

    # recalled-fragment cosines to the same day block -> 30th percentile threshold
    recalled_coses = []
    if seed_ids:
        with mstore._connect() as conn:
            ph = ",".join("?" * len(seed_ids))
            for r in conn.execute(f"SELECT embedding FROM memory_fragments WHERE fragment_id IN ({ph}) "
                                   f"AND embedding IS NOT NULL", seed_ids).fetchall():
                recalled_coses.append(mstore._cosine(day_vec, mstore._blob_to_vec(r["embedding"])))
    threshold = float(np.percentile(recalled_coses, 30)) if recalled_coses else 1.0  # no recall -> no filter bite
    eligible = [c for c in cands if c[3] < threshold] or cands  # fall back to full pool if the filter empties it
    fid, content, origin, cos = random.choice(eligible)
    return {"fragment_id": fid, "content": content, "origin": origin, "cosine_to_day": cos,
            "n_candidates": len(cands), "n_eligible": len(eligible), "threshold": threshold}


# ---------------------------------------------------------------------------
# Arm execution
# ---------------------------------------------------------------------------

class ExpDreamNode(dn.DreamNode):
    """Subclass only -- nodes/dream_node.py is never edited. Used ONLY as a container for _gen_episode
    (called directly in run_arc()'s own loop below, matching scripts/dream_arc_test.py's established
    pattern) -- synthesise() itself is never invoked, so Phase 1's _log_transition()/log_seed_pairs()
    side-effect logs are never reached (they are called from inside synthesise()'s loop body only)."""
    pass


async def run_arc(seed: dict, arm: str, state) -> dict:
    node = ExpDreamNode()
    prev = None
    phases = ["open", "develop", "close"]  # N_SCENES=3 -- matches synthesise()'s own deterministic
                                            # phase sequence when MAX_EPISODES==MIN_EPISODES==3
    scenes = []
    t0 = time.time()
    n_calls = 0
    for idx in range(N_SCENES):
        refeed = arm not in NO_REFEED_ARMS or idx == 0
        material = seed["materials"][idx] if refeed else ""
        memories = seed["memories_txt"] if idx == 0 else ""  # recall is ALWAYS scene-1-only in every
                                                               # arm here (matches sec 1 "once"); A0's
                                                               # difference from A1/A2/A3 is materials
                                                               # re-feed only, not memories re-feed --
                                                               # the live engine's own re-feed of
                                                               # `memories` every scene (synthesise()
                                                               # passes the same dream_memories string
                                                               # to every _gen_episode call) is NOT
                                                               # reproduced for A0 either, since it is
                                                               # not the variable this experiment tests
                                                               # (materials re-feed is; see plan sec 6
                                                               # table -- only the "re-feed" column
                                                               # varies A0 from A1). Documented in the
                                                               # lab report as a scope choice.
        if idx == 0 and arm in DORMANT_ARMS and seed.get("dormant"):
            d = seed["dormant"]
            stranger = (f"\n\nA distant, unbidden memory surfaces too -- do not narrate it literally, "
                        f"let it tinge the imagery if anything: \"{' '.join((d['content'] or '').split())[:140]}\"")
            memories = (memories or "") + stranger

        t_call = time.time()
        data = await node._gen_episode(state, material, prev, idx, phases[idx],
                                       carried_over=False, memories=memories)
        n_calls += 1
        if data is None:
            scenes.append(None)
            break
        data["_wall_s"] = round(time.time() - t_call, 1)
        scenes.append(data)
        prev = data
    return {"arm": arm, "seed_idx": seed["seed_idx"], "scenes": scenes,
            "n_calls": n_calls, "wall_s": round(time.time() - t0, 1)}


# ---------------------------------------------------------------------------
# Measures
# ---------------------------------------------------------------------------

_STEM_SUFFIXES = ("ing", "ings", "es", "s")


def _stem(w: str) -> str:
    w = w.lower().strip()
    for suf in _STEM_SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _symbol_set(symbols: list) -> set:
    return {_stem(s) for s in (symbols or []) if s}


def turnover(scenes: list[dict | None]) -> float | None:
    valid = [s for s in scenes if s]
    if len(valid) < 2:
        return None
    jaccards = []
    for a, b in zip(valid, valid[1:]):
        sa, sb = _symbol_set(a.get("symbols")), _symbol_set(b.get("symbols"))
        if not sa and not sb:
            jaccards.append(1.0)  # both empty -> treat as no turnover, matches "stalled" spirit
            continue
        inter = len(sa & sb); union = len(sa | sb) or 1
        jaccards.append(inter / union)
    return round(1.0 - (sum(jaccards) / len(jaccards)), 4)


def dormant_contact(scenes: list[dict | None], dormant_content: str | None) -> float | None:
    if not dormant_content:
        return None
    dvec = mstore._embed(dormant_content)
    if dvec is None:
        return None
    best = None
    for s in scenes:
        if not s or not s.get("narrative"):
            continue
        nvec = mstore._embed(s["narrative"])
        if nvec is None:
            continue
        c = mstore._cosine(dvec, nvec)
        best = c if best is None else max(best, c)
    return round(best, 4) if best is not None else None


def recent_contact(scenes: list[dict | None], recent_day_block: str) -> float | None:
    return dormant_contact(scenes, recent_day_block)  # same computation, different target text


# ---------------------------------------------------------------------------
# Resume support (J-1139, F-1545)
# ---------------------------------------------------------------------------
# F-1545 (2026-09-19) found a real hazard: amain() below opened both its results and scenes files in
# overwrite ("w") mode with no way to continue a batch that crashed partway through -- relaunching under
# the SAME --tag/--job-id (the obvious "continue" command) would SILENTLY DESTROY whatever rows had
# already been banked (real wall-clock time + real LLM-hub cost). The two helpers below plus the new
# --resume flag fix this additively: default behavior (no --resume passed) is byte-for-byte unchanged.

def _load_existing_seeds(seeds_path: Path) -> list[dict] | None:
    """If a seeds json from an earlier (possibly crashed) run of this exact job-id/tag already exists,
    load it verbatim instead of re-freezing. Re-freezing on a resumed run would NOT reproduce the same
    seeds -- freeze_seeds()'s own `now0 = time.time() - ...` is real wall-clock time, which has moved on
    since the original freeze -- so a resume MUST reuse the original seeds file to keep already-completed
    (seed_idx, arm) rows comparable to the ones still to come. Returns None (caller falls back to a fresh
    freeze) if the file does not exist or fails to parse -- best-effort, never raises."""
    if not seeds_path.exists():
        return None
    try:
        data = json.loads(seeds_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) and data else None
    except Exception as exc:
        print(f"[resume] failed to load existing seeds from {seeds_path}: {exc!r} -- falling back to a fresh freeze")
        return None


def _load_completed_pairs(results_path: Path) -> set[tuple[int, str]]:
    """(seed_idx, arm) pairs already present in an existing results .jsonl, so amain()'s run loop can
    skip them (real LLM cost avoided) instead of re-running or silently overwriting them. Malformed/
    partial lines (e.g. a crash mid-flush) are skipped with a printed warning, never fatal."""
    pairs: set[tuple[int, str]] = set()
    if not results_path.exists():
        return pairs
    for i, line in enumerate(results_path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            pairs.add((row["seed_idx"], row["arm"]))
        except Exception as exc:
            print(f"[resume] results line {i} unparseable, skipping ({exc!r}): {line[:120]!r}")
    return pairs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def amain(args):
    worktree_check()
    live_mtime_before = LIVE_DB.stat().st_mtime if LIVE_DB.exists() else None

    # J-1139 (F-1545): computed once, up front, so both the scenes-file open below and the seeds/results
    # handling inside the isolate() block see the SAME resume decision. When args.resume is False (the
    # pre-existing default) neither branch below is taken -- behavior is byte-for-byte unchanged.
    seeds_path = SCRATCH / f"dream_exp_a_seeds_{args.job_id}_{args.tag}.json"
    results_path = SCRATCH / f"dream_exp_a_results_{args.job_id}_{args.tag}.jsonl"
    resume_seeds = _load_existing_seeds(seeds_path) if args.resume else None
    completed_pairs = _load_completed_pairs(results_path) if args.resume else set()
    if args.resume:
        print(f"[resume] --resume passed: {len(resume_seeds) if resume_seeds else 0} existing seed(s) "
              f"loaded, {len(completed_pairs)} already-completed (seed_idx, arm) pair(s) will be skipped "
              f"(not re-run, not overwritten).")

    scenes_path = None
    scenes_file = None
    if args.save_scenes:
        # J-1110 (F-1516): ADDITIVE ONLY -- the existing results .jsonl row (seed_idx, arm, n_scenes_ok,
        # turnover, dormant_contact, recent_contact, n_calls, wall_s, error) is unchanged, byte-for-byte,
        # whether or not this flag is passed. This just ALSO persists the per-scene narrative text that
        # run_arc()'s own `scenes` list already holds in memory and previously discarded once the row was
        # computed -- F-1516 found this made a retroactive judge-panel shadow read on a completed batch
        # impossible (the text needed to score no longer existed anywhere, live or isolated). Same
        # {job_id}_{tag} sidecar naming convention as the existing seeds/results/log files.
        scenes_path = SCRATCH / f"dream_exp_a_scenes_{args.job_id}_{args.tag}.jsonl"
        # J-1139 (F-1545): append instead of overwrite when resuming into an existing sidecar.
        scenes_mode = "a" if (args.resume and scenes_path.exists()) else "w"
        scenes_file = open(scenes_path, scenes_mode, encoding="utf-8")

    from core import telemetry as tel
    with lab_env.isolate(also=[(tel, ["_CALLS", "_STATIONS", "_LAT", "_HW", "_LLM"])]) as lab_dir:
        # co_recall_ledger.jsonl isn't a `also=` pair (it's read-only here, never written by this
        # script) but pick_dormant_fragment() looks for a COPY of it beside the isolated DB so a
        # real ledger snapshot is available; lab_env's isolate() only copies nascence.db, not the
        # ledger, so copy it in ourselves (read-only use, never written back).
        real_ledger = Path(r"C:\Nascence\data\co_recall_ledger.jsonl")
        lab_ledger = lab_dir / "co_recall_ledger.jsonl"
        if real_ledger.exists():
            import shutil
            shutil.copy2(real_ledger, lab_ledger)
            # pick_dormant_fragment() looks for it at mstore.DB_PATH.parent / "co_recall_ledger.jsonl";
            # DB_PATH is lab_dir/nascence.db (lab_env.py's _copy_db), so .parent == lab_dir == where we
            # just copied it -- read-only use, this script never writes the ledger back.
        ax = json.loads(Path(r"C:\Nascence\data\identity\axiom.json").read_text(encoding="utf-8"))
        name, floor = al.compose_floor(ax) if al.is_multilevel(ax) else ("渡", str(ax.get("core_axiom", "")))
        state = SimpleNamespace(spirit_name=name, axiom=floor, background_curiosities=[
            "what does it mean to change and still be myself", "the river and the self -- one or two?"])

        if resume_seeds is not None:
            seeds = resume_seeds
            note = "" if len(seeds) == args.n_seeds else (
                f" (note: --n-seeds {args.n_seeds} is ignored in resume mode; the loaded file's own "
                f"seed count governs)")
            print(f"[resume] loaded {len(seeds)} seed(s) verbatim from {seeds_path} -- freeze_seeds() "
                  f"NOT called (re-freezing now would draw different real-time hist_now values and not "
                  f"match the seeds already-completed rows were scored against).{note}")
        else:
            seeds = freeze_seeds(args.n_seeds, lab_dir, name, floor, day_step=args.day_step,
                                  start_offset_days=args.start_offset_days)
            seeds_path.write_text(json.dumps([{k: v for k, v in s.items()} for s in seeds],
                                             ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            print(f"[freeze] {len(seeds)} seeds frozen -> {seeds_path}")

        results = []
        # J-1139 (F-1545): append instead of overwrite when resuming into an existing results file.
        results_mode = "a" if (args.resume and results_path.exists()) else "w"
        with open(results_path, results_mode, encoding="utf-8") as rf:
            for seed in seeds:
                for arm in ARMS:
                    if (seed["seed_idx"], arm) in completed_pairs:
                        print(f"[resume] seed {seed['seed_idx']} arm {arm} already in results -- "
                              f"skipping (not re-run, not overwritten)", flush=True)
                        continue
                    print(f"[run] seed {seed['seed_idx']} arm {arm} ...", flush=True)
                    try:
                        arc = await run_arc(seed, arm, state)
                    except Exception as exc:
                        print(f"[run] seed {seed['seed_idx']} arm {arm} FAILED: {exc!r}")
                        arc = {"arm": arm, "seed_idx": seed["seed_idx"], "scenes": [], "error": repr(exc)}
                    dormant_c = None
                    recent_c = None
                    if arc.get("scenes"):
                        dormant_c = dormant_contact(arc["scenes"], seed["dormant"]["content"] if seed.get("dormant") else None)
                        recent_c = recent_contact(arc["scenes"], seed["materials"][0])
                    row = {
                        "seed_idx": seed["seed_idx"], "arm": arm,
                        "n_scenes_ok": sum(1 for s in arc.get("scenes", []) if s),
                        "turnover": turnover(arc.get("scenes", [])),
                        "dormant_contact": dormant_c,
                        "recent_contact": recent_c,
                        "n_calls": arc.get("n_calls"), "wall_s": arc.get("wall_s"),
                        "error": arc.get("error"),
                    }
                    results.append(row)
                    rf.write(json.dumps(row) + "\n"); rf.flush()
                    print(f"[run]   -> turnover={row['turnover']} dormant_contact={row['dormant_contact']} "
                          f"recent_contact={row['recent_contact']} wall_s={row['wall_s']}", flush=True)

                    if scenes_file is not None:
                        # scenes_detail: one entry per scene slot (None for a scene that never came back,
                        # e.g. the scale14b-0/A1 partial-generation gap F-1516 already found) -- narrative/
                        # symbols/tension_source/unresolved_core/movement, exactly what _gen_episode()
                        # returns, minus only the internal `_wall_s` timing key this script itself added.
                        scenes_detail = [
                            ({k: v for k, v in s.items() if k != "_wall_s"} if s else None)
                            for s in arc.get("scenes", [])
                        ]
                        scenes_file.write(json.dumps({
                            "seed_idx": seed["seed_idx"], "arm": arm, "scenes": scenes_detail,
                            "dormant_content": (seed.get("dormant") or {}).get("content"),
                        }, ensure_ascii=False) + "\n")
                        scenes_file.flush()

        print(f"[run] all results -> {results_path}")
        if scenes_file is not None:
            scenes_file.close()
            print(f"[run] all scenes -> {scenes_path}")

    live_mtime_after = LIVE_DB.stat().st_mtime if LIVE_DB.exists() else None
    print(f"[backstop] live DB mtime before={live_mtime_before} after={live_mtime_after} "
          f"unchanged={live_mtime_before == live_mtime_after}")
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seeds", type=int, default=20)
    ap.add_argument("--tag", type=str, default="full")
    ap.add_argument("--job-id", type=str, default="J1059",
                     help="job id used in output filenames (default J1059 preserves the original "
                          "pilot's naming; pass your own job id for a new batch, e.g. J1077)")
    ap.add_argument("--day-step", type=float, default=4.0,
                     help="real days between seeds' `now` timestamps (J-1077 fix; pilot used 1.0 and "
                          "6/6 seeds collided into 2 distinct day-residue blocks)")
    ap.add_argument("--start-offset-days", type=float, default=0.0,
                     help="shift the whole seed window this many real days further back, so a later "
                          "batch does not re-freeze the same `now` values as an earlier one")
    ap.add_argument("--save-scenes", action="store_true", default=False,
                     help="J-1110 (F-1516): additively persist each arc's per-scene narrative/symbols/"
                          "unresolved_core to a dream_exp_a_scenes_{job_id}_{tag}.jsonl sidecar, so a "
                          "judge-panel shadow read (scripts/dream_exp_a_judge_shadow.py) is possible "
                          "afterward. Default off -- existing results-row schema and default behavior "
                          "are unchanged either way.")
    ap.add_argument("--resume", action="store_true", default=False,
                     help="J-1139 (F-1545): if a seeds/results file for this exact --job-id/--tag pair "
                          "already exists (e.g. a batch that crashed partway through), reuse the "
                          "existing seeds verbatim (no re-freeze -- real wall-clock time has moved on, "
                          "a fresh freeze would not match already-completed rows) and skip any "
                          "(seed_idx, arm) pair already present in the results file, appending new rows "
                          "instead of overwriting. Default off -- omitting this flag preserves the exact "
                          "pre-existing overwrite behavior (what F-1545 found silently destroys banked "
                          "rows on a naive same-tag relaunch).")
    args = ap.parse_args()
    asyncio.run(amain(args))
