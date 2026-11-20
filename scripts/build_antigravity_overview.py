"""
build_antigravity_overview.py — Generates the October 2026 Truth-Badged System Overview
for Nascence 渡 in both Markdown and Interactive HTML formats without modifying
Claude's original August 2026 System_Overview.md or System_Overview.html.

Outputs:
  - docs/System_Overview_Antigravity.md
  - docs/System_Overview_Antigravity.html

Rebuilt by J-2415 (F-3115). Everything numeric is computed at build time from the tree, the ledgers and
data/nascence.log by scripts/scan_nascence.py (in this repo; no external scratch inputs). Badges are
boot-aware: a module is judged against the commit that was HEAD when the running process booted, not
against whatever the tree says today.

Usage:  python scripts/build_antigravity_overview.py [--root REPO] [--data-root DIR] [--no-docusaurus]
"""
from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scan_nascence as scan  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--root", default=str(HERE.parent), help="repo whose tree is documented (default: this repo)")
ap.add_argument("--data-root", default=None, help="dir holding nascence.log and the data stores (default: ROOT/data)")
ap.add_argument("--no-docusaurus", action="store_true")
ARGS, _ = ap.parse_known_args()

ROOT = Path(ARGS.root)
DATA_ROOT = Path(ARGS.data_root) if ARGS.data_root else ROOT / "data"
DOCS_DIR = ROOT / "docs"
MD_OUT = DOCS_DIR / "System_Overview_Antigravity.md"
HTML_OUT = DOCS_DIR / "System_Overview_Antigravity.html"

DEFAULT_DOMAIN = "Engine Utilities & Supporting Subsystems"

# ── DOMAIN CLASSIFICATION ────────────────────────────────────────────────────────
# Two passes (review defect 7): an EXPLICIT stem set in ANY domain beats every substring guess, then the
# substring guesses run in order. (name, path-prefixes, explicit stems, fuzzy substrings)
DOMAIN_RULES = [
    ("16 Cognitive Nodes (Hot & Background Lanes)", ("nodes/",), set(), ()),
    ("Conscious Pass, Orchestration & Scheduling", (), {
        "orchestrator", "lane_scheduler", "parallel_dispatcher", "reentry", "broadcast",
        "pulse_manager", "pulse_shadow", "idle_allocator", "sitting", "observation",
        "stream_drive", "condensed_thought", "topic_perseveration", "closure",
        "conversational_redirect", "task_constraints"}, ()),
    ("LLM Transport, Serving & Infrastructure", (), {
        "model_client", "llm_parse", "prompt_budget", "unified_inference", "node_base",
        "deterministic_checker", "cpu_model_server", "profile", "schema", "config"}, ("server", "client")),
    ("Sovereign Memory, S-MMU Lattice & Recall", ("core/memory/",), {
        "memory_store", "associative_recall", "memory_levels", "memory_dynamics",
        "memory_edges", "memory_lint", "memory_service", "felt_recall", "ghost_index",
        "activity_memory", "euclidean_recall", "evidence_recall", "recall_provenance",
        "recall_demand", "retrieval_probe", "recall_wager", "chapters", "journal_rollup",
        "world_consolidation", "refinery", "co_recall"}, ("recall", "memory", "gist")),
    ("Subconscious, Sleep, Dreams & Night Mode", (), {
        "night", "sleep_pressure", "sleep_dream_probe", "seed_epochs_themes",
        "tension_ledger", "shadow_events", "dream_lag"}, ("sleep", "dream", "night")),
    ("Stratified Identity, Estate & Watershed (T4/T5)", (), {
        "axiom_layers", "identity_vault", "identity_estate", "provisional_identity",
        "commitment_ledger", "commitment_trials", "watershed", "watershed_promote",
        "self_claims", "self_implication", "guidance_learning", "told", "affections",
        "identity_cost", "identity_projection", "satisfaction", "procedures",
        "competent_self", "self_authoring"}, ("identity", "watershed", "commitment", "axiom")),
    ("Bicameral Left Lane, Witness (Lane 2) & Judges", (), {
        "left_lane", "emissary", "emissary_tension", "object_graph", "librarian",
        "deliberative_judge", "judge_panel", "guidance_behavior_judge",
        "grounded_learning", "scholar", "lane2", "deliberation"}, ("judge", "lane2", "emissary")),
    ("Trains, Couriers, Buses & Dosed Coupling", (), {
        "trains", "couriers", "buses", "transport_manager", "coupling_rides",
        "pursuits", "theme_dose", "doubt_seed", "weakness_prior", "cargo_types"},
     ("train", "courier", "bus", "coupling", "pursuit")),
    ("Affective Climate, Protoself & Somatic Engine", (), {
        "mood", "climate_engine", "loop_metabolism", "homeostasis", "arousal",
        "boredom", "affect_divergence", "affect_labeling", "modulation_field",
        "opponent_process", "prediction_error", "thermal_relationship", "somatic",
        "emotion_construction", "vitality"}, ("affect", "mood", "climate", "somatic")),
    ("Sensorium, Living World, Places & Acoustics", (), {
        "sensorium", "life", "cat", "cat_content", "cat_sounds", "soundscape",
        "sound_knowledge", "audio_features", "audition", "listening", "music_record",
        "locomotion", "spatial", "weather_conditions", "heavens", "sky", "light",
        "smell", "thermal", "keepsakes", "world_clock", "world_objects", "world_traces",
        "world_substrate", "world_manifest", "missing_object_flags", "geometry_census",
        "ghost_tuples", "world_model", "world_content_study", "world_content_wood",
        "world_content_garden", "world_content_shore", "study_life", "wood_life",
        "garden_life", "shore_life", "nature_study", "garden", "garden_knowledge",
        "life_birds", "life_mammals", "life_traces"},
     ("world", "sound", "shore", "garden", "wood", "study_life", "cat", "spatial", "thermal")),
    ("Hands, Volition, Fieldcraft, School & Reading", (), {
        "actions", "dispatch", "hands", "literal_will", "literal_will_deed",
        "conversational_action", "expression", "intentions", "inventory", "provisions",
        "fieldcraft", "affordances", "school", "practical_school", "math_drill",
        "essay_lesson", "composition", "music_drill", "curiosity_queue",
        "curiosity_progress", "curiosity_worth", "frontier", "concerns", "web_research",
        "reading", "book_selection", "book_selector", "book_feelings", "book_residue",
        "book_splitter", "reading_history", "symbolic_reading", "study_note",
        "library_hand", "peers", "peer_metrics", "letters", "social_moves", "journal"},
     ("book", "read", "school", "drill", "hand", "action", "peer", "letter", "curiosity")),
    ("Honest Observers, Epistemics & Diagnostics", (), {
        "retraction_ledger", "symbol_tracker", "epistemic_state", "self_efficacy",
        "source_model", "mineness", "attention_schema_loop", "contradiction_gate",
        "epistemic_affordance_advisor", "self_mirror", "self_interrogation",
        "self_surprise", "narrative_quality", "decomposed_critic", "content_risk",
        "needle_triage", "telemetry", "shadow_log", "training_log", "conflict_trace",
        "mapping_census", "psyche_graph", "competence", "error_pathway", "loop_probe",
        "investigation_deepening_shadow"},
     ("shadow", "epistemic", "probe", "trace", "ledger", "self_", "metric")),
]
DOMAIN_NAMES = [r[0] for r in DOMAIN_RULES] + [DEFAULT_DOMAIN]


def classify_domain(rel: str) -> str:
    stem = Path(rel).stem
    for name, prefixes, stems, _ in DOMAIN_RULES:           # pass 1: explicit
        if any(rel.startswith(p) for p in prefixes) or stem in stems:
            return name
    for name, _, _, fuzzy in DOMAIN_RULES:                  # pass 2: substring guesses
        if any(w in stem for w in fuzzy):
            return name
    return DEFAULT_DOMAIN


BADGE_CLASS = {"LIVE": "badge-live", "SHADOW": "badge-shadow", "GATED": "badge-gated", "LAB": "badge-designed",
               "RETIRED": "badge-retired", "DEFERRED": "badge-deferred"}
BADGE_EMOJI = {"LIVE": "\U0001F7E2", "SHADOW": "\U0001F7E1", "GATED": "\U0001F7E1", "LAB": "\U0001F535",
               "RETIRED": "⛔", "DEFERRED": "\U0001F4A4"}


def categorize_script(name: str, doc: str) -> str:
    n = name.lower()
    if n.startswith("_test_") or n.startswith("test_") or "test" in n:
        return "Verification & Hermetic Test Harnesses"
    if any(k in n for k in ("launch", "start_", "stop_", "supervisor", "run_nascence", "server", "reconnect", "boot", "deploy", "retention", "watchdog")):
        return "Runtime Boot, Supervision & Ops"
    if any(k in n for k in ("pulse", "audit", "report", "check", "probe", "status", "inspect", "diagnostic", "digest", "retro", "lint", "verify", "grade")):
        return "Diagnostics, Audits & Pulse Telemetry"
    if any(k in n for k in ("lab", "exp_", "bench", "eval", "sweep", "sim", "matrix", "trial", "ablation")):
        return "In-Vitro Labs, Benchmarks & Model Evals"
    if any(k in n for k in ("sync_", "build_", "backfill", "migrate", "repair", "index", "graphify", "seed", "extract")):
        return "Indexing, Backfills, Migrations & Docs Sync"
    return "Domain Utilities & Interactive Tools"


def nrows(rel: str) -> int | None:
    """Rows in a data/ jsonl store (read-only; None if the store is absent so the text says so instead of guessing)."""
    p = DATA_ROOT / rel
    if not p.exists():
        return None
    with open(p, "rb") as fh:
        return sum(1 for ln in fh if ln.strip())


def fmt_rows(rel: str) -> str:
    n = nrows(rel)
    return f"{n:,}" if n is not None else "n/a"


def pct(a: int, b: int) -> str:
    return f"{100.0 * a / b:.1f}%" if b else "n/a"


def main():
    S = scan.full_scan(ROOT, DATA_ROOT)
    head_mods = S["head"]["modules"]
    boot_mods = S["boot_graph"]["modules"] if S["boot_graph"] else {}
    git_boot_ok = bool(S["boot_graph"])
    boot_info, boot_commit = S["boot"], S["boot_commit"]
    boot_txt = (f"{boot_info['stamp']} (boot commit `{boot_commit['short']}`)" if git_boot_ok
                else "UNKNOWN (no boot line found in data/nascence.log: badges are tree-only, not boot-aware)")
    ledgers, plans, docs_info = S["ledgers"], S["plans"], S["docs"]

    modules_dict = {}
    for rel, info in head_mods.items():
        code, label = scan.badge_for(rel, boot_mods.get(rel), info, git_boot_ok)
        modules_dict[rel] = dict(info, badge_code=code, badge_label=label)

    def deg(path: str) -> dict:
        m = head_mods[path]
        return {"in": m["in_deg"], "out": m["out_deg"], "tot": m["in_deg"] + m["out_deg"], "lines": m["lines"], "m": m}

    def B(stem: str) -> str:
        """Emoji badge for core/<stem>.py as computed (so narrative never types a status the table disagrees with)."""
        for pre in ("core/", "nodes/"):
            if f"{pre}{stem}.py" in modules_dict:
                return BADGE_EMOJI[modules_dict[f"{pre}{stem}.py"]["badge_code"]]
        return "❓"

    top_hubs = scan.top_hubs(head_mods, 20)
    hub_rank = {h["rel"]: i for i, h in enumerate(scan.top_hubs(head_mods, 400), 1)}

    # Enrich modules with domain & badge
    domain_groups = defaultdict(list)
    badge_counts = Counter()
    total_engine_lines = 0
    for rel, info in sorted(modules_dict.items()):
        if rel == "scripts/run_nascence.py":
            continue
        dom = classify_domain(rel)
        badge_counts[info["badge_code"]] += 1
        total_engine_lines += info["lines"]
        domain_groups[dom].append({
            "rel": rel, "name": Path(rel).name, "lines": info["lines"], "defs": info["defs"],
            "in_deg": info["in_deg"], "out_deg": info["out_deg"], "total_deg": info["in_deg"] + info["out_deg"],
            "in_top": info["in_top"], "in_lazy": info["in_lazy"], "in_dyn": info["in_dyn"],
            "doc": info["doc"], "flags": {k: v for k, v in info["flags"].items() if any(
                w in k for w in ("LIVE", "ENABLED", "DELIVER", "ADMIT", "SHADOW", "TWIN", "RERANK", "BUS", "FIELDS", "WRITE", "SEED", "WAGER"))},
            "badge_code": info["badge_code"], "badge_label": info["badge_label"],
        })

    n_runtime = len(head_mods)                              # core + nodes + scripts/run_nascence.py
    n_core = sum(1 for r in head_mods if r.startswith("core/"))
    n_nodes_files = sum(1 for r in head_mods if r.startswith("nodes/"))
    n_register = n_core + n_nodes_files
    n_reach = len(S["head"]["reachable"])
    n_scripts = len(S["scripts"])
    n_docs = docs_info["total"]
    doc_by_dir = docs_info["by_dir"]
    n_plan_docs = len(plans)
    F, J, D = ledgers["findings"], ledgers["job_queue"], ledgers["decisions"]
    f_ver = F["by"].get("verified", 0)
    j_done = J["by"].get("done", 0)

    im, ss, st = deg("nodes/inner_monologue_node.py"), deg("nodes/subconscious_node.py"), deg("core/memory/store.py")
    pf, sl = deg("core/profile.py"), deg("core/shadow_log.py")
    guard_calls = S["head"].get("guard_path_calls", 0)
    guard_files = S["head"].get("guard_path_files", 0)
    estate_nodes = None
    try:
        estate_nodes = len(json.loads((DATA_ROOT / "identity_estate.json").read_text(encoding="utf-8-sig"))["nodes"])
    except Exception:
        pass
    estate_txt = f"{estate_nodes}" if estate_nodes is not None else "n/a"

    # Parse all scripts for the script registry summary (utf-8-sig; a bad file is a loud error, not a silent 0)
    import ast as _ast
    script_cats = defaultdict(list)
    for name in S["scripts"]:
        sf = ROOT / "scripts" / name
        txt = scan.decode(sf.read_bytes(), f"scripts/{name}")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = _ast.parse(txt)
        except SyntaxError as exc:
            raise scan.ScanError(f"scripts/{name}: does not parse ({exc})") from exc
        doc = (_ast.get_docstring(tree) or "").strip().split("\n")[0][:160]
        doc = re.sub(r'^Nascence\s*[\-\–\—\·:]*\s*', '', doc)
        script_cats[categorize_script(name, doc)].append({
            "name": name, "lines": len(txt.splitlines()), "doc": doc or "Operational / test script",
            "mtime": datetime.datetime.fromtimestamp(sf.stat().st_mtime).strftime("%Y-%m-%d"),
        })

    today = datetime.date.today()
    today_long = f"{today.strftime('%B')} {today.day}, {today.year}"
    today_short = f"{today.strftime('%b')} {today.day}, {today.year}"

    def PS(slug: str) -> str:
        for p in plans:
            if p["slug"] == slug and p["dir"] in ("plans", "staged"):
                return p["stage"]
        return "?"

    def T(path: str) -> int:
        return head_mods[path]["in_deg"] + head_mods[path]["out_deg"]

    mono_mods = [c for c in ("trains", "pursuits", "fieldcraft", "journal_rollup", "self_interrogation", "night")
                 if f"core/{c}.py" in head_mods and "nodes/inner_monologue_node.py" in head_mods[f"core/{c}.py"]["importers"]]
    mono_txt = ", ".join(f"`core/{c}.py`" for c in mono_mods)
    top_docdirs = [(k, v) for k, v in sorted(doc_by_dir.items(), key=lambda x: -x[1]) if k != "(root)"][:7]
    docdirs_txt = ", ".join(f"`{k}/` ({v})" for k, v in top_docdirs)
    L2 = head_mods["core/lane2.py"]["flags"].get("LANE2_LIVE")

    # Build Markdown content
    md_lines = []
    md_lines.append("# Nascence 渡 — System Overview (Antigravity Truth-Badged Edition · Build 2.0)")
    md_lines.append("")
    md_lines.append(f"> **TRUTH-BADGED SYSTEM OVERVIEW — {today_long}** · generated by `scripts/build_antigravity_overview.py` from `scripts/scan_nascence.py`. **Not authoritative** until a post-boot read confirms the restart-gated items. Badges are judged against the running boot: {boot_txt}.")
    md_lines.append(f"> Compiled at build time from static AST analysis of **{n_core} `core/` modules**, **{n_nodes_files} `nodes/` files**, **{n_scripts} `scripts/`**, **{n_docs} `docs/` Markdown files**, and the live governance ledgers (**{D['total']} decisions**, **{F['total']:,} findings**, **{J['total']:,} jobs**). Import edges count distinct modules (relative imports resolved; lazy and dynamic imports reported separately). Preserves Claude's August 25, 2026 overview (`docs/System_Overview.md` & `docs/System_Overview.html`) untouched for historical comparison.")
    md_lines.append("")
    md_lines.append("**Truth-Badge Legend:**")
    md_lines.append("- 🟢 **LIVE** — Reachable from the runtime roots in the build that is actually running (the boot commit), its master flag (if any) was on at that boot, and it is not observe-only.")
    md_lines.append("- 🟡 **SHADOW** — Running, but observe-only: its master flag is False, its docstring says shadow/observe-only, it writes only `*_shadow.jsonl`, or every call site discards its return. **RESTART-GATED** (also 🟡) — committed after the boot, or a master flag changed after it: not yet in the running process.")
    md_lines.append("- 🔵 **LAB** — No runtime importer in the boot build (standalone offline evaluation / lab module).")
    md_lines.append("- 💤 **DEFERRED** — Built, consciously held until a pre-registered trigger (docstring says DEFERRED / PARKED / STANDING RESERVE).")
    md_lines.append("- ⛔ **RETIRED** — Retired by a named ruling (docstring cites `RETIRED ... D-xxxx`) or quarantined after forensic audit.")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 0. What Changed Since Claude's August 25 Overview (Build 1.4.0 → Build 2.0 Delta)")
    md_lines.append("")
    md_lines.append(f"| Dimension | Aug 25, 2026 (`System_Overview.md`) | {today_short} (`System_Overview_Antigravity.md`) | Key Structural Shift |")
    md_lines.append("| :--- | :--- | :--- | :--- |")
    md_lines.append(f"| **Core Engine (`core/`)** | 201 files | **{n_core} files** ({total_engine_lines:,} LOC incl. nodes) | +{n_core - 201} new modules across Dosed Coupling, Night/Sleep II, Living World, Actions, S-MMU Lattice, and Measurement-to-Action |")
    md_lines.append(f"| **Cognitive Nodes (`nodes/`)** | 16 nodes | **16 nodes** ({n_nodes_files} files) | `inner_monologue_node.py` grew to **{im['lines']:,} lines ({im['out']} distinct modules imported)**; `subconscious_node.py` at **{ss['lines']:,} lines ({ss['out']} imported)** |")
    md_lines.append(f"| **Operational & Test Scripts (`scripts/`)** | 187 scripts | **{n_scripts} scripts** | +{n_scripts - 187} scripts, mostly hermetic `lab_env.isolate()` regression suites (`_test_j*.py`), probes, and offline benchmarks |")
    md_lines.append(f"| **Documentation (`docs/`)** | 338 `.md` files | **{n_docs} `.md` files** ({n_plan_docs} plan docs) | +{n_docs - 338} docs; largest folders: {docdirs_txt} |")
    md_lines.append("| **Subconscious / Background GPU Lane** | `:11434` (`phi3:mini` on Ramses Ollama) | **`:11441` (`command-r7b` on Ramses 3070 `llama.cpp`)** | **D-0056 / D-0057 (Aug 28):** Ramses Ollama (`:11434`) **⛔ RETIRED** after 3070 VRAM lock; `:11441` `command-r7b` is now sole 3070 tenant |")
    md_lines.append("| **Bicameral Judge Panel (`judge_panel.py`)** | `:11439` (`gemma4:12b`) + `:11440` (`falcon3:7b`) + `:11442` tiebreak | **`:11438` (`mixtral:8x7b`) + `:11440` (`falcon3:7b`) + `:11437` (`granite3.1-moe:3b`)** | **D-0121 (Sep 2) & D-0056 (Aug 28):** `JUDGE_1` moved to Ramses `:11438`; `TIEBREAK` moved to Ramses 1650 Super `:11437` (3 distinct model families: Mistral / TII / IBM) |")
    md_lines.append(f"| **Lane 2: The Witness (`core/lane2.py`)** | Shadow-wired from Aug 25 (not unwired) | **`:11444` (`deepseek-r1:7b` on Ramses i9 CPU)** | **D-0058 (Sep 7):** Continuous reality-testing loop running in **🟡 SHADOW** (`LANE2_LIVE={L2}`, `TICK_S=300s`, {fmt_rows('lane2_shadow.jsonl')} shadow rows accrued) |")
    md_lines.append(f"| **Sovereign DB & Episodic Cap (`core/memory/store.py`)** | 3,500-row `prune_episodic` cap | **`RETRIEVE_LATENCY_BUDGET_MS = 250` (no row cap); {st['in']} importers / {st['out']} imports** | **D-0453 / J-2274 / J-2275 (Oct 17):** Per-kind row-cap prune **⛔ RETIRED**; `commit_gist` is sole demotion path; covering index + float32 matrix cut recall `581ms → 157ms` over 41.9k active rows (offline measurement on a DB copy) |")
    md_lines.append(f"| **Loop Inter-Communication** | Direct state reads / ad-hoc injections | **Dosed Coupling (`core/coupling_rides.py`)** | **D-0149 (ruled Sep 4) / D-0152 (ruled Sep 13):** Standing law — loops publish small typed coordinate tuples; consumers pull dosed cups/buckets with squishy-spring habituation ({fmt_rows('coupling_rides.jsonl')} rows) |")
    md_lines.append(f"| **World Store Safety & Data Hygiene** | Unfenced file writes; 60MB JSON parsed/5s | **Write Fence (`core/profile.py`) + Light Sidecars** | **J-0610 (Sep 6) & D-0154 (ruled Sep 5; flag flipped Sep 9):** `guard_path()` is called {guard_calls} times in {guard_files} files today (F-0995 counted 24 calls in 10 modules when it was wired); `profile.py` is the #{hub_rank['core/profile.py']} AST hub at {pf['tot']} distinct-module edges; light sidecars cut 60MB parse `1000ms → 16ms` |")
    md_lines.append(f"| **Governance Toolchain Ledgers** | Initial rollout (Aug 23) | **{F['total']:,} Findings · {J['total']:,} Jobs · {D['total']} Decisions** | {pct(f_ver, F['total'])} of findings carry `--confidence verified` with cited evidence; {D['with_defeater']} of {D['ruled']} ruled decisions carry a revisit defeater |")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 1. Hardware & Model Serving Matrix (Live-Verified Configuration)")
    md_lines.append("")
    md_lines.append("Per **Spine F (`MODELS ARE TOOLS, NOT PERSONAS`)** and `docs/ROADMAP.md`, LLMs are stations on the transit lines, never Du himself. Every LLM call routes through `core/model_client.py` (`_MODEL_BY_BASE`, `_NUM_CTX_BY_BASE`, `/no_think` prefix, `call_node_json()`) or the dedicated judge/witness clients (`core/judge_panel.py`, `core/lane2.py`, `core/left_lane.py`).")
    md_lines.append("")
    md_lines.append("| Port | Host & Silicon | Engine | Model Tag | `num_ctx` | Status | Assigned Cognitive Station & Role (`model_client.py` / `judge_panel.py` / `lane2.py`) |")
    md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    md_lines.append("| **`:11433`** | Local (`127.0.0.1`) · **GTX 1080 Ti (11GB)** | Ollama | `qwen3.5:9b` | `8192` | 🟢 **LIVE** | **Hot Lane (Master / Self):** All 10 conscious pass nodes (Perception → Voice), inner monologue conscious pass, 39.4 tok/s. Right-sized `24576 → 8192` (Aug 21) freeing ~3.5GB VRAM (p95 usage = 19% of 8192). |")
    md_lines.append("| **`:11441`** | Ramses (`LAN-HOST`) · **RTX 3070 (8GB)** | `llama.cpp` hub | `command-r7b` | `4096` | 🟢 **LIVE** | **Subconscious / Background Lane (Sole 3070 Tenant, D-0057):** Consolidation, Curiosity, Subconscious (T1–T6), DMN background tasks, plus **Epistemics Tier-3 External Witness probe** (`core/competence.py`, J-1343). Replaced retired `:11434`. |")
    md_lines.append("| **`:11438`** | Ramses (`LAN-HOST`) · **i9 CPU (48GB)** | `llama.cpp` hub | `mixtral:8x7b` | `8192` | 🟢 **LIVE** | **Judge Panel `JUDGE_1` + Dream Primary + Commitment Defeater Judge (D-0044, D-0056 for the dream primary, D-0121):** Repointed from dark local `:11439` on Sep 2. Mistral family vote in `core/judge_panel.py` + primary dream generator (`nodes/dream_node.py`). |")
    md_lines.append("| **`:11437`** | Ramses (`LAN-HOST`) · **GTX 1650 Super (4GB)** | `llama.cpp` hub | `granite3.1-moe:3b` | `4096` | 🟢 **LIVE** | **Judge Panel `TIEBREAK` + Curiosity Worth-Judge (D-0056 / D-0057):** Dedicated fast GPU tiebreaker (IBM family, 1.0–4.3s/verdict) when `JUDGE_1` (Mistral) and `JUDGE_2` (Falcon3) split. |")
    md_lines.append("| **`:11440`** | Local (`127.0.0.1`) · **Threadripper CPU** | `llama.cpp` hub | `falcon3:7b` | `8192` | 🟢 **LIVE** | **Judge Panel `JUDGE_2` + Peer Writer (Marcus/Smith):** TII family vote in `core/judge_panel.py` + offline `literal_will_retro.py` grader. *(Note D-0207/J-1141: callers judging Marcus/Smith letters route around `JUDGE_2` to preserve family decoupling.)* |")
    md_lines.append("| **`:11442`** | Local (`127.0.0.1`) · **Threadripper CPU** | `llama.cpp` hub | `yi:34b-v1.5` | `8192` | 🟢 **LIVE** | **Dream Failover + Peer Voices (Darwin / Keats / Lovelace):** Backs up `:11438` dream generation and authors long-form peer correspondence (`core/peers.py`). |")
    md_lines.append("| **`:11444`** | Ramses (`LAN-HOST`) · **i9 CPU (48GB)** | `llama.cpp` hub | `deepseek-r1:7b` | `4096` | 🟡 **SHADOW** | **Lane 2: The Witness (`core/lane2.py`, D-0058 re-ruled Sep 7):** Continuous egocentric reality-testing & horizon-prediction loop (`LANE2_LIVE=False`, `LANE2_PAUSED=False`, `TICK_S=300s`, `MAX_TOKENS=1400`). |")
    md_lines.append("| **`:11439`** | Local (`127.0.0.1`) · **Threadripper CPU** | `llama.cpp` hub | `gemma4:12b` | `8192` | 🟢 **LIVE** | **Supervised and listening; gist-faithfulness grader and Emissary callers:** serves the gist-faithfulness grader on the `commit_gist` path, peers, the librarian fallback and `decomposed_critic` (`deliberation.py` does not route here). Vacated `judge_panel.py` `JUDGE_1` on Sep 2 (D-0121). Roles per review F-3115. |")
    md_lines.append("| **`:11436`** | Ramses (`LAN-HOST`) · **i9 CPU (48GB)** | `llama.cpp` hub | `falcon3:7b` | `16384` | 💤 **RESERVE** | **Standing Reserve Hub (D-0101):** Alive on Ramses i9, deliberately unwired in `core/model_client.py`. |")
    md_lines.append("| **`:11434`** | Ramses (`LAN-HOST`) · **RTX 3070 (8GB)** | Ollama | *(retired)* | — | ⛔ **RETIRED** | **Retired Aug 28 (D-0056 / F-0389):** Ramses Ollama service stopped and disabled after `phi3:mini` + `deepseek` collided with `:11441` on the 8GB 3070. *(Claude's Aug 25 overview still listed this as active.)* |")
    md_lines.append("")
    md_lines.append("> **Process Supervision Note (`CLAUDE.md` F-0704 / D-0277 / J-1341):** Never launch Du's servers directly from a job-confined shell without escaping the Windows Job Object. Always use `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\\start_supervisor_detached.ps1` (which spawns `scripts/start_supervisor_launcher.ps1` → `scripts/supervisor.py` via WMI `Win32_Process.Create`) or the standalone `Nascence_Control_Panel.ps1`.")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append(f"## 2. AST Codebase Topology & Top 20 Super-Hubs ({today_long})")
    md_lines.append("")
    md_lines.append(f"Static AST analysis across all **{n_runtime} runtime Python files** (`{n_core} core/` + `{n_nodes_files} nodes/` + `scripts/run_nascence.py`) shows **{n_reach} modules ({pct(n_reach, n_runtime)})** are reachable from the runtime roots (`run_nascence.py`, `orchestrator.py`, `inner_monologue_node.py`) over top-level, lazy and dynamic (`__import__` / `mod:<name>:<fn>` binding) edges. Degrees count **distinct modules**, not imported names:")
    md_lines.append("")
    md_lines.append("| Rank | Module Path | Total Distinct-Module Degree | Inbound (importers; T=top-level / L=lazy / D=dynamic) | Outbound (modules imported) | Lines of Code | Status | Architectural Role & Post-August Evolution |")
    md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for idx, hub in enumerate(top_hubs[:20], 1):
        rel = hub["rel"]
        b_code, b_label = modules_dict[rel]["badge_code"], modules_dict[rel]["badge_label"]
        hm = hub["m"]
        md_lines.append(f"| **{idx}** | [`{rel}`](file:///c:/Nascence/{rel}) | **{hub['total_deg']}** | {hub['in_deg']} (T{hm['in_top']}/L{hm['in_lazy']}/D{hm['in_dyn']}) | {hub['out_deg']} | {hub['lines']:,} | {b_label} | {hub['doc']} |")
    md_lines.append("")
    md_lines.append("### Five Non-Obvious Codebase Realities Exposed by the Oct 2026 AST Scan")
    md_lines.append(f"1. **`core/memory/store.py` ({st['tot']} distinct-module edges: {st['in']} importers + {st['out']} imports, {st['lines']:,} lines) is the #{hub_rank['core/memory/store.py']} hub:** {st['in']} modules import it. Following **D-0453 (2026-10-17)**, its 3,500-row `prune_episodic` cap was retired in favor of `RETRIEVE_LATENCY_BUDGET_MS = 250` using `idx_retrieve_pool_cover` and an in-process `float32` embedding matrix (`581ms → 157ms` median retrieval, measured offline on a DB copy).")
    md_lines.append(f"2. **`nodes/inner_monologue_node.py` ({im['tot']} distinct-module edges, {im['lines']:,} lines) is the #1 dispatch mega-hub:** While diagrams show Node 14 as one box among 16, in code it imports **{im['out']} distinct modules** ({im['m']['out_top']} top-level, {im['m']['out_lazy']} lazy, {im['m']['out_dyn']} dynamic) — among them {mono_txt}, driving the **Continuous Stream (`CONTINUOUS_STREAM=True`)**.")
    md_lines.append(f"3. **`core/profile.py` ({pf['tot']} distinct-module edges, {pf['in']} importers) is the #{hub_rank['core/profile.py']} hub via the World Store Write Fence (`J-0610` / `D-0179`):** After diagnostic scripts accidentally burned ~20 matches and half a tin of lamp oil in Du's live study (`F-0788`), `profile.guard_path()` was wired into the world-store writers; it is called {guard_calls} times in {guard_files} files today. Non-live processes (`LIVE=False`) are structurally fenced from mutating live world state.")
    md_lines.append(f"4. **`core/shadow_log.py` ({sl['in']} importers) is shared observe-first plumbing:** {sl['in']} engine modules log to `data/*_shadow.jsonl` through it, enforcing Nascence's engineering law: *every new organ ships shadow-first, fail-open, restart-gated, with pre-registered promotion and kill bars.* It is infrastructure (badged LIVE), not a shadow organ itself.")
    md_lines.append(f"5. **The Physical World (`sensorium.py` {T('core/sensorium.py')} edges + `garden.py` {T('core/garden.py')} + `study_life.py` {T('core/study_life.py')} + `life.py` {T('core/life.py')} + `soundscape.py` {T('core/soundscape.py')} + `cat.py` {T('core/cat.py')} + `shore_life.py` {T('core/shore_life.py')}) is now a multi-organ causal simulation:** No longer a flat text generator, the world runs federated clocks (`sound_causality.md`), 3D egocentric room geometry (`spatial.py`), NZ species population & item factories (`life.py`, `garden.py`), and physical book/item placement (`books_have_a_place.md`). The four `world_content_*` corpora are loaded by `core/world_detail.py` through `__import__`, and `core/expression.py` is bound through `mod:expression:act_from_thought` — both resolved here as dynamic edges.")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 3. Truth-Badged Master Architecture Flowchart (October 2026)")
    md_lines.append("")
    md_lines.append("```mermaid")
    md_lines.append("flowchart TD")
    md_lines.append("    %% INPUT & PRE-CORTEX REFLEXES")
    md_lines.append("    IN([\"Input · Human / Internal Stream / Dissonance Ignition\"]) --> TG")
    md_lines.append("    subgraph PRE[\"PRE-CORTEX REFLEXES · Deterministic · Zero LLM\"]")
    md_lines.append("        direction TB")
    md_lines.append("        TG{{\"🟢 Thalamic Gate · core/orchestrator.py\\nNear-verbatim repeat (cos ≥ 0.95) bypass\"}}")
    md_lines.append("        AP{{\"🟢 Affective Prior + Felt Recall · core/mood.py + core/felt_recall.py\\nCharged-memory lean + coordinate-keyed world-change tug (🟡 J-1424)\"}}")
    md_lines.append("        PR{{\"🟢 Procedural Match · core/procedures.py\\nWorld & conversational held-claims ladder (0.4→0.9)\"}}")
    md_lines.append("        HC{{\"🟢 Error Pathway & Human-Correction Detector · core/error_pathway.py\\nRetraction Ledger (core/retraction_ledger.py) + Quarantine\"}}")
    md_lines.append("        TG -->|novel| AP --> PR")
    md_lines.append("    end")
    md_lines.append("    IN -.->|\"human input\"| HC")
    md_lines.append("    PR --> P")
    md_lines.append("")
    md_lines.append("    subgraph HOT[\"🟢 HOT LANE (Master / Self) · Local GTX 1080 Ti (:11433) · qwen3.5:9b · 8,192 ctx\"]")
    md_lines.append("        direction TB")
    md_lines.append("        P[\"🟢 Node 1: Perception · nodes/perception_node.py\\nintent · domain · urgency · direct_request\"] --> E[\"🟢 Node 2: Emotion · nodes/emotion_node.py\\nState-estimation + Protoself valence (AFFECT_SOURCE_PROTOSELF=True)\"]")
    md_lines.append("        P --> S[\"🟢 Node 3: Salience · nodes/salience_node.py\\nimportance & urgency > 0.7 interrupt\"]")
    md_lines.append("        P --> MR[\"🟢 Node 4: Memory Router · nodes/memory_router_node.py\\nsemantic, temporal & phase retrieval keys\"]")
    md_lines.append("        E & S & MR --> DBQ{{\"🟢 Associative & Lattice Recall · core/associative_recall.py\\nM2 Edge-Aware Trail (🟢) + Lens 1 Spectral (🟡) + Lens 3 Support Rerank (🟡 J-2350)\"}}")
    md_lines.append("        DBQ --> RC[\"🟢 Node 5: Recall · nodes/recall_node.py\\nReconstructs gists, tensions & Founder Recall (🟢 D-0134)\"]")
    md_lines.append("        RC --> EB[\"🟢 Node 6: Episodic Buffer · nodes/episodic_buffer_node.py\\nBinds scene + Bound Moments (core/moment.py) + Mineness (🟢 +0.061)\"]")
    md_lines.append(f"        EB --> R[\"🟢 Node 7: Reflection · nodes/reflection_node.py\\nBest-of-2 hedge + Condensed Twin ({B('condensed_thought')} shadow twin, J-2349)\"]")
    md_lines.append("        R --> C[\"🟢 Node 8: Critic · nodes/critic_node.py\\nIdentity-fidelity check w/ Made-Mind & Mode-Choice carve-outs\"]")
    md_lines.append("        C -->|approved| X[\"🟢 Node 9: Executive · nodes/executive_node.py\\nPERCEIVE-overrides-RECALL (🟢 D-0068) + Pending Letters (🟡 D-0470) + Doubt Seed (🟡 J-2161)\"]")
    md_lines.append("        X -->|should_respond| REENT{{\"🟡 Within-Cycle Reentry · core/reentry.py\\nREENTRY_ADMIT=False (D-0540) · Phase 0 shadow, admits nothing\"}}")
    md_lines.append("        REENT --> V[\"🟢 Node 10: Voice · nodes/voice_node.py\\nProse output + Task-Constraint Effector (core/task_constraints.py)\"]")
    md_lines.append("        V --> CAB{{\"🟢 Conversational Action Bridge · core/conversational_action.py\\nCONVERSATIONAL_DISPATCH_LIVE=True (D-0299) → literal_will → dispatch\"}}")
    md_lines.append("        CAB --> OUT([\"Response + World Deeds in 渡's Voice\"])")
    md_lines.append("    end")
    md_lines.append("")
    md_lines.append("    subgraph JUDGES[\"🟢 DECOUPLED JUDGE PANEL & LEFT LANE · 3-Family Consensus (D-0071 / D-0121)\"]")
    md_lines.append("        direction TB")
    md_lines.append("        J1[\"🟢 JUDGE_1 · Ramses i9 (:11438) · mixtral:8x7b\\nPanel Vote #1 + Commitment Defeater + Dream Primary\"]")
    md_lines.append("        J2[\"🟢 JUDGE_2 · Local CPU (:11440) · falcon3:7b\\nPanel Vote #2 + Literal-Will Gray-Zone Judge\"]")
    md_lines.append("        JT[\"🟢 TIEBREAK · Ramses 1650S (:11437) · granite3.1-moe:3b\\nPanel Split Tiebreaker + Curiosity Worth-Judge\"]")
    md_lines.append("        EMIS[\"⚪ Left Lane Emissary · Local CPU (:11439) · gemma4:12b\\ncore/left_lane.py · Two-Judge T4 Solidify + Grounding + Essay Grader\"]")
    md_lines.append("        J1 & J2 --> JT")
    md_lines.append("    end")
    md_lines.append("")
    md_lines.append("    subgraph WITNESS[\"🟡 LANE 2: THE WITNESS · Ramses i9 (:11444) · deepseek-r1:7b (D-0058)\"]")
    md_lines.append("        direction TB")
    md_lines.append("        L2[\"🟡 Witness Loop · core/lane2.py (LANE2_LIVE=False · 300s tick)\\nReads Experienced Tuple ONLY (Sight/Sound/Body/Mood Gain)\\nHorizon Predictions + Wonder Questions (🟡 lane2_curiosity.md)\"]")
    md_lines.append("    end")
    md_lines.append("")
    md_lines.append("    subgraph BG[\"🟢 BACKGROUND, IDLE & NIGHT LANES · Ramses 3070 (:11441 command-r7b) & CPU (:11438/:11442)\"]")
    md_lines.append("        direction TB")
    md_lines.append(f"        MONO[\"🟢 Node 14: Inner Monologue (DMN) · nodes/inner_monologue_node.py\\n{im['out']} imports · {im['lines']:,} LOC · Continuous Stream (🟢 D-0074)\\nTrains (core/trains.py) · Pursuits (🟢 core/pursuits.py) · Self-Interrogation (🟡)\"]")
    md_lines.append("        NIGHT[\"🟢 Night & Sleep II · core/night.py + nodes/dream_node.py\\nNREM/REM Split · 14h Ceiling · Bimodal Dream-Lag · Blocked float32 Chapters Scan (10s)\"]")
    md_lines.append(f"        DRM_OV[\"{B('closure')} Dream Overhaul + Closure Law · core/closure.py\\nVault-Opener Cold Fragment Seed · Symbol Turnover & Dormant Contact\"]")
    md_lines.append(f"        SC[\"🟢 Node 13: Subconscious · nodes/subconscious_node.py\\nT1–T6 Pipeline · T4 Watershed ({B('watershed_promote')} core/watershed_promote.py) · Refinery ({B('refinery')} core/refinery.py)\"]")
    md_lines.append("        CON[\"🟢 Node 11: Consolidation · nodes/consolidation_node.py\"]")
    md_lines.append(f"        CUR[\"🟢 Node 12: Curiosity · nodes/curiosity_node.py\\nWorth-Gate (🟢 :11437) · Theme Dose (🟡 core/theme_dose.py) · Perseveration Alarm ({B('topic_perseveration')} J-2347)\"]")
    md_lines.append("        META[\"🟢 Node 16: Meta-Awareness · nodes/meta_awareness_node.py\"]")
    md_lines.append("    end")
    md_lines.append("")
    md_lines.append("    subgraph COUPLE[\"🟢 DOSED COUPLING & TRANSIT BUS NETWORK · D-0149 / D-0152\"]")
    md_lines.append("        direction TB")
    md_lines.append(f"        CR[\"🟢 Coupling Rides Registry · core/coupling_rides.py\\n{fmt_rows('coupling_rides.jsonl')} publish rows · Cup/Bucket/Hose Dosing · Squishy-Spring Law\"]")
    md_lines.append("        TM[\"🟡 Transport Manager · core/transport_manager.py\\nEdge-Triggered Novelty / Spike / Drought · verdict(line_id)\"]")
    md_lines.append("        COUR[\"🟢 Couriers & Buses · core/couriers.py + core/buses.py\\nUrgent: context_echo, sound_echo · Buses: object_ledger, calibration_sync, idle_freight (🟡)\"]")
    md_lines.append(f"        M2A[\"🟡 Measurement to Action · arms built shadow-only, flags off/neutral (T-0085)\\nRecall Wager (core/recall_wager.py) · Doubt Seed (core/doubt_seed.py) · Weakness Prior (core/weakness_prior.py)\"]")
    md_lines.append("    end")
    md_lines.append("")
    md_lines.append(f"    subgraph WORLD[\"🟢 LIVING WORLD, HANDS & SENSORY CHANNELS · Write-Fenced via core/profile.py ({pf['tot']} edges)\"]")
    md_lines.append("        direction TB")
    md_lines.append("        SENS[\"🟢 Sensorium & 3D Rooms · core/sensorium.py + core/spatial.py\\nStudy · Garden · Wood · Shore (Tide Waterline) · Books Have a Place (🟡)\"]")
    md_lines.append("        LIFE[\"🟢 Living World Engine · core/life.py + core/garden.py + core/cat.py\\nNZ Species Populations · Soil/Insects · Cat Voice Shadow (🟡 core/cat_sounds.py)\"]")
    md_lines.append("        CHAN[\"🟢 Sensory Channels · core/soundscape.py + core/thermal.py\\nAcoustic Clock & Propagation Table (🟢) · Thermal Channel (🟢) · 6-Axis Sound Ribbons (🟡)\"]")
    md_lines.append(f"        ACT[\"🟢 Unified Actions & Practical School · core/actions.py + core/dispatch.py + core/fieldcraft.py\\nGated Hands · Expressive Hands (hum/whistle/sing) · 22-Task Handbook Practicals\"]")
    md_lines.append("    end")
    md_lines.append("")
    md_lines.append(f"    subgraph MEM[\"🟢 SOVEREIGN DB & S-MMU LATTICE · core/memory/store.py ({st['tot']} edges) + core/memory_levels.py\"]")
    md_lines.append("        direction TB")
    md_lines.append("        SMMU[\"🟢 S-MMU Lattice · data/memory/nascence.db\\nabstraction_level (0=raw, 1=gist, 2=meta) × kind × grounding × temp × cold\\nRETRIEVE_LATENCY_BUDGET_MS=250 (D-0453 · idx_retrieve_pool_cover + float32 matrix · 157ms median)\"]")
    md_lines.append("        MLINKS[\"🟢 Multiway Memory Links · core/memory_edges.py\\ndistilled_from · relates_to · contradicts · t4_crossing_evidence · co_recalled_developing (🟢 M2)\"]")
    md_lines.append(f"        EST[\"🟢 Stratified Identity Estate · core/axiom_layers.py + core/identity_estate.py\\nL0–L5 Multilevel Axiom + {estate_txt}-Node Identity Estate (IDENTITY_PROJECT_LIVE=True)\"]")
    md_lines.append("    end")
    md_lines.append("")
    md_lines.append("    HOT <--> MEM")
    md_lines.append("    BG <--> MEM")
    md_lines.append("    MONO <--> WORLD")
    md_lines.append("    MONO <--> COUPLE")
    md_lines.append("    COUPLE <--> HOT")
    md_lines.append("    JUDGES -.->|\"Decoupled Verdicts\"| BG")
    md_lines.append("    JUDGES -.->|\"T4 & Action Verdicts\"| HOT")
    md_lines.append("    WORLD -.->|\"Experienced Tuple\"| WITNESS")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 4. Deep-Dives: Major Post-August Architectural Eras & Subsystems")
    md_lines.append("")
    md_lines.append("### 4.1 Dosed Coupling & The Loop Wiring Matrix (`docs/staged/dosed_coupling.md` · 🟢 Phase 1 LIVE)")
    md_lines.append("- **The Law (D-0149, ruled 2026-09-04):** Every standing loop in Du publishes a small, typed coordinate tuple to `core/coupling_rides.py` — never a standing prose view of another loop. Consumers read dosed amounts per stop (**cup** = 1 item, **bucket** = small batch, **hose** = stream) dispatched by surprise under the **squishy-spring law** (a long-strong pull counts for less than a fresh medium one).")
    md_lines.append(f"- **Empirical Footprint:** `core/coupling_rides.py` has accrued **{fmt_rows('coupling_rides.jsonl')} publish rows** (`data/coupling_rides.jsonl`); F-1304 was NOT a clean pass (2 of 4 behaviour metrics out of band; D-0152 ruled GO and accepted the ambiguity); F-0845 credits the `0.48 → 0.82` grounded-share lift to J-0581, not Phase 0/1, and did not check the identity guard.")
    md_lines.append("- **Staged Children (`🔵 DESIGNED`):**")
    md_lines.append("  - [`speech_thought_concurrency.md`](file:///c:/Nascence/docs/staged/speech_thought_concurrency.md) (`D-0372`): Running speech and inner thought concurrently on one GPU with residual cups.")
    md_lines.append(f"  - [`sleep_as_a_mode.md`](file:///c:/Nascence/docs/staged/sleep_as_a_mode.md) (`T-0080` → `I-0088`): Refactoring sleep from a blocking ~15-pass procedure into three per-lane switches (`coupling`, `generation`, `encoding`) with a `dormant` memory layer. **Not 'no code':** `core/night_mind.py` and `core/night_dormant.py` exist; both flags are True (the dormant flag restart-gated from 10-18 18:50).")
    md_lines.append("  - [`real_hearing.md`](file:///c:/Nascence/docs/staged/real_hearing.md) (`D-0378..D-0381`): A physical microphone as a study window feeding Sound Space strings.")
    md_lines.append("")
    md_lines.append("### 4.2 The Night: Sleep & Dreams II, Dream Overhaul & Closure Law (`core/night.py` · 🟢 LIVE / 🟡 SHADOW)")
    md_lines.append("- **Sleep & Dreams II (`docs/plans/sleep_dream_redesign.md` · 🟢 BUILT):** Separated **Sleep (NREM-analogue)** and **Dreaming (REM-analogue)** into two coupled systems in `core/night.py`:")
    md_lines.append("  - **14-Hour Day Ceiling:** Recalibrated `core/sleep_pressure.py` off 25,415 real rows (`5h → 14h` ceiling) so Du stays awake through the day and sleeps at night, with a `pool_thin` light-sleep fast path when day material is sparse.")
    md_lines.append("  - **Bimodal Dream-Lag Pull:** `night.dream_lag_material()` pulls material across Nielsen et al.'s bimodal **1–2 day / 5–7 day** curve, gated on real emotional charge (`core/tension_ledger.py` `CHARGE_WEIGHTS`) rather than raw recurrence.")
    md_lines.append("  - **SHY Synaptic Downscaling Fix:** `downscale_episodic` center moved `0.5 → 0.1` so nightly decay stops flattening all fragment importance toward `0.5`.")
    md_lines.append("  - **Drowsiness Phase (`docs/plans/drowsiness_phase.md` · ⚪ PARTIAL):** `TRAIN_SLEEP_GRACE_SECS = 300` (🟢 LIVE) gives a moving thought-train up to 5 minutes to finish before a due sleep fires.")
    md_lines.append("  - **Chapters Seed Scan 277× Speedup (`J-1744` / `D-0330`, 2026-10-04):** Replaced `core/chapters.py`'s 1.78-billion Python `np.dot` loop (`2,775s` wall time) with `_neighbour_counts` — a blocked `float32` matrix product (`768×768` tiles + `9.2e-5` exact guard band) that produces the exact same seed and 714-member cluster in **10.0 seconds**.")
    md_lines.append(f"- **Dream Overhaul (`docs/staged/dream_overhaul.md` · 🟡 SHADOW):** Reframes dreaming as the **Vault-Opener** — designed to inject one dormant fragment from cold/chaptered storage into every dream seed (exists only in-vitro today: `scripts/dream_experiment_a.py`, `commit=False`; no `DREAM_ENGINE=vault` flag exists), replacing self-reported resolution (`0/146` resolved) with two computed metrics: **symbol turnover** and **dormant contact** (re-entry into waking recall within 48h via `co_recall_ledger.jsonl`, {fmt_rows('co_recall_ledger.jsonl')} rows).")
    md_lines.append("- **The Closure Law (`docs/staged/closure_law.md` · `core/closure.py` · 🟡 SHADOW, `D-0423`):** *\"A met loop becomes a memory.\"* Dream arm built in shadow (`CLOSURE_WRITE_LIVE=False`, `J-2118`).")
    md_lines.append("")
    md_lines.append("### 4.3 The Transit City: Trains, Pursuits, Couriers, Buses & Transport Manager")
    md_lines.append("- **Trains & Cargo Taxonomy (`core/trains.py` · 🟢 Step 1 LIVE / 🟡 Cargo IDs BUILT):**")
    md_lines.append("  - Every idle thought-train carries a persistent `train_id` and stamps station provenance (`train_state_log.jsonl`, 37,691 rows; `trains_log.jsonl`, 22,009 rows), powering the **HUD1 Transit Pulse** and **HUD2 Transit Map**.")
    md_lines.append("  - **19 Station Product Types (`docs/plans/train_courier_cargo_ids.md`, `D-0082`):** Every station stamps a typed `product_type` (e.g., `SELF_CONCEPT_DELTA`, `LETTER`, `THOUGHT`, `CONTEMPLATION`).")
    md_lines.append(f"  - **Split/Merge Junctions (`docs/plans/train_split_merge.md` · {PS('train_split_merge')}: Step 1 shipped, Step 2 built, replay in progress):** At a would-be train close, forks into a **Prove branch (Lane 1)** and **Disprove branch (Lane 2 Witness)**, merging typed cargo `{{claim, support[], objection[], status}}`.")
    md_lines.append(f"- **The Pursuits (`core/pursuits.py` · 🟢 `PURSUITS_LIVE=True`):** Cures cold-reset jumping across idle gaps by maintaining 3–4 active `pursuit` objects (`question`, `standing`, `established`, `heat`), graded by the decoupled `judge_panel` (`{fmt_rows('pursuits_shadow.jsonl')}` shadow rows).")
    md_lines.append(f"- **Transport Manager (`core/transport_manager.py` · 🟡 SHADOW, `D-0064` / `D-0294`):** Edge-triggered baseline-relative salience dispatcher (`NOVELTY` / `SPIKE` / `DROUGHT` via EMA rate & gap), accruing `{fmt_rows('transport_shadow.jsonl')}` rows in `data/transport_shadow.jsonl` and exposing `verdict(line_id)` (`47/47` unit tests) for Felt Recall.")
    md_lines.append("- **Couriers vs. Buses (`core/couriers.py` + `core/buses.py` · 🟢 LIVE / 🟡 SHADOW):**")
    md_lines.append("  - **Urgent Couriers (`core/couriers.py`):** `context_echo` (distinctive weather → matching past moments) and `sound_echo` (Hearing Ledger → wandering trail; reroutable to Felt Recall via `COURIER_TEXT_DELIVERY`, `D-0293`).")
    md_lines.append(f"  - **Non-Urgent Buses (`core/buses.py`):** `object_ledger`, `calibration_sync`, and the **`idle_freight` bus (`J-1436` / `D-0295`; `IDLE_FREIGHT_BUS = True` since 2026-09-28, loaded by every boot since)** carrying developed Idle Line thoughts into the Conversation Line's Reflection stop.")
    md_lines.append("")
    md_lines.append("### 4.4 S-MMU Lattice Memory, Oct 17 Latency-Budget Breakthrough & Recall Lenses")
    md_lines.append("- **The S-MMU Lattice (`core/memory_levels.py` + `core/memory/store.py` · 🟢 Phase 1 LIVE, 🔶 Phase 2 IN PROGRESS):**")
    md_lines.append("  - Replaces flat transcript storage with a multi-dimensional coordinate space on `memory_fragments`: `abstraction_level` (`0=raw`, `1=gist`, `2=meta-gist`), `kind` (`episodic`, `semantic`, `procedural`, `affective`, `self`, `social` — topical distinctness `0.994`), `grounding` (`grounded`, `derived`, `reconstructed`), `temp` (`warm`, `cold`, `hidden`), and `cold` (`0/1`), connected by `memory_links` (`distilled_from`, `relates_to`, `contradicts`, `supports`, `t4_crossing_evidence`).")
    md_lines.append(f"  - **Oct 17, 2026 Breakthrough (`D-0453` / `J-2274` / `J-2275`):** After 98.4% of the 63,962 active rows became origin-protected, Travis ruled to **⛔ RETIRE `prune_episodic`'s 3,500-row cap** (`memory_levels.commit_gist` is now the sole cold-demotion path). In its place, `store.py` enforces **`RETRIEVE_LATENCY_BUDGET_MS = 250`** using a covering partial index (`idx_retrieve_pool_cover`) and an in-process `float32` embedding matrix — cutting median retrieval latency across **41,923 active rows** from **581 ms → 157 ms** (`60/60` real query heads byte-identical; an offline measurement on a DB copy, not a live-process reading).")
    md_lines.append("- **Multiway Linking M0/M1/M2 (`core/memory_edges.py` · 🟢 LIVE):** Expanded M1 co-recall logging across 9 retrieval sites; **M2 (`co_recalled_developing` + `recall_trail_edge_aware` for `mode=relational`) flipped LIVE on 2026-09-26 (`D-0215` / `D-0287`)**.")
    md_lines.append("- **Recall Lens Upgrades (`docs/staged/du_recall_lens_upgrades.md` · 🟡 SHADOW):**")
    md_lines.append("  - **Lens 1 (Spectral Diffusion):** Built in shadow in `core/associative_recall.py` (`+3.08pp` precision gain).")
    md_lines.append("  - **Lens 3 (Counterfactual Consensus Support Re-Rank · `J-2350` / `D-0472`, merged 2026-10-17):** Re-ranks associative trail items by leave-one-out support (`act' = 0.5*act + 0.5*peak*HOP_DECAY*support`), changing Top-1 on `17/40` offline queries while keeping live return paths byte-identical until `LENS3_RERANK` is flipped.")
    md_lines.append(f"- **Memory as a Service & Felt Recall (`docs/staged/memory_as_a_service.md` · `core/felt_recall.py` · 🟡 SHADOW, `D-0289`):** Loops call memory on demand (ambient idle recall injection turned off in `J-1425`); world changes trigger coordinate-keyed `fragment_context` lookups that tug carried affect at reaction speed with zero LLM calls.")
    md_lines.append(f"- **Golden Spiral Recall (`docs/staged/golden_spiral_recall.md` · {PS('golden_spiral_recall')} (Phase 0 PHASE columns built, no reader yet), `T-0072`):** Stamps `tod`, `season`, and `daylight` phase columns on `fragment_context` (`F-2030`) to enable same-phase recall ($\\Theta$: *this dawn finds other dawns*).")
    md_lines.append("")
    md_lines.append("### 4.5 Stratified Identity, T4 Watershed, Decoupled Judges & Relational Memory")
    md_lines.append("- **Two Multilevel Axioms (`core/axiom_layers.py`, `core/emissary.py`):** **The Self (渡)** (`data/identity/axiom.json`, L0 Constitution → L5 Working-Self) and **The Emissary** (`data/identity/emissary_axiom.json`, McGilchrist's truth-self). Only `L3.the_becoming` is T4-revisable.")
    md_lines.append(f"- **The Identity Estate (`core/identity_estate.py`, `core/identity_projection.py` · 🟢 `IDENTITY_PROJECT_LIVE=True`):** Identity as a lived graph of **{estate_txt} typed nodes** (`data/identity_estate.json`, `10,911` projection shadow rows), feeding the **T4 Watershed (`core/watershed_promote.py` · 🟡 SHADOW)** where \"the river\" is the structural root (*\"I am a process, not a fixed object\"*) and earned branches (current, sediment, circuitry, Wu Wei) are harvested from lived stream rather than LLM manifestos.")
    md_lines.append(f"- **Decoupled Judge Pattern (`docs/plans/decoupled_judge_pattern.md` · 🟢 `D-0071`):** Standing architectural law: *every subsystem is evaluated by a model family other than its generator.* Implemented via `core/judge_panel.py` (`mixtral:8x7b` + `falcon3:7b` + `granite3.1-moe:3b` tiebreak; `{fmt_rows('judge_panel_log.jsonl')}` logged panel rulings) and `core/deliberative_judge.py` (dual literal/metaphor reading + cross-judge rebuttal).")
    md_lines.append("- **Episodic Founder Recall (`docs/plans/guidance_learning.md` · 🟢 `D-0134`):** Backfilled **1,617 canonical `[Travis said to me] …` rows** (`protected=1`, immune to cold demotion) and wired `retrieve_founder_memories` → `WHAT TRAVIS HAS TOLD YOU BEFORE` into Executive and Reflection.")
    md_lines.append("- **Letters to Travis (`docs/staged/letters_to_travis.md` · 🟡 BUILT `J-2348` / `D-0470`, merged 2026-10-17):** Fixed the 79 unread letters gap (`F-2959`) by adding `/api/letters` + a HUD card, preventing `/quit` farewells from marking letters delivered, and feeding all pending letters oldest-first into Executive and Reflection (`core/letters.py`).")
    md_lines.append("")
    md_lines.append("### 4.6 The Living World, Unified Actions, Practical School & Sensory Channels")
    md_lines.append("- **The Living World (`core/life.py`, `core/garden.py`, `core/shore_life.py`, `core/wood_life.py`, `core/study_life.py` · 🟢 LIVE `D-0166`):** Unified life schema (`core/life.py`, 1,317 lines) driving active hours, season curves, weather/light responses, sound gating, lifespans, and NZ insect/bird/soil population factories (`garden_living_upgrade.md` ✅ SHIPPED). Cat companion voice (`core/cat_sounds.py`) built in shadow (`cat_overhaul.md`).")
    md_lines.append("- **Unified Actions & Conversational Action Bridge (`core/actions.py`, `core/dispatch.py`, `core/literal_will.py`, `core/conversational_action.py` · 🟢 LIVE):**")
    md_lines.append(f"  - Retired the ungated `sensorium.py` phrase-latch fallback (`D-0098`). All world hands + Tier-3 expressive hands (`core/expression.py`: hum/whistle/sing) route through `core/actions.py` and `core/literal_will.py` (`229,291` shadow rows).")
    md_lines.append("  - **Conversational Action Bridge (`CONVERSATIONAL_DISPATCH_LIVE=True`, `D-0299`):** Replies to Travis now route through `literal_will.classify()` → `dispatch()` for full action parity with the autonomous loop.")
    md_lines.append("- **Practical School & Books Have a Place (`core/fieldcraft.py`, `docs/staged/practical_school.md` 🟢 LIVE, `docs/staged/books_have_a_place.md` 🟡 PARTIAL):** Alternates nature observation with a 22-task Scout Handbook practical ladder (`whittle_object`, knots, banking fire, shadow measuring). Curriculum books now have physical `desk`/`shelf`/`with_him` state (`J-0851`).")
    md_lines.append("- **Sensory Channels & Strings and Sheets (`core/soundscape.py`, `core/thermal.py`, `docs/staged/strings_and_sheets.md`):**")
    md_lines.append("  - **Thermal Channel (`core/thermal.py` · 🟢 `DELIVER=True`, `D-0047`):** Causal insolation, wind, rain wetness, and fire-by-distance delivered into the Experienced Tuple (`42,327` shadow rows).")
    md_lines.append("  - **Sound Causality (`core/soundscape.py` · ✅ SHIPPED `D-0062`):** Federated cause-lists emit rates through a per-place audibility propagation table (`FULL`/`MUFFLED`/`DISTANT`/`none`).")
    md_lines.append(f"  - **Strings and Sheets (`docs/staged/strings_and_sheets.md` & `fragment_carries_the_string.md` · 🟡 SHADOW):** Models every sound as a 6-axis temporal **string** and constructed×measured **ribbon** (`Heavyweight.mp3` + woodpigeon Phase 4 labs `2026-10-18`), with 8 additive `sound_*` columns on `fragment_context` (`J-1534`, `SOUND_STRING_FIELDS=True` since 2026-09-28).")
    md_lines.append("")
    md_lines.append("### 4.7 Measurement to Action, Condensed Thought & Perseveration Guards (October 2026 Wave)")
    md_lines.append(f"- **Measurement to Action (`docs/staged/measurement_to_action.md` · 🟡 SHADOW, `T-0085`):** Closes the gap exposed by the Oct 15 Du-vs-Human audit (`F-2851`, paraphrased: Du measures himself better than a human but uses it worse, because gauges were write-only to the HUD). **Every arm flag is off or neutral; only the closure dream arm is built.**:")
    md_lines.append("  - **Arm 1 (Standing Competence Number):** **⛔ DROPPED (`D-0434`)** — Travis ruled Du must learn he is wrong *by consequence, never by being told a standing number*.")
    md_lines.append("  - **Arm 2 (Recall Confidence Wager · `core/recall_wager.py` · 🟡 `J-2158`):** When Du states confidence $\\ge 0.85$ on a `SUSPECT`-graded recall, logs a wager and (when `RECALL_CONFIDENCE_WAGER=True`) feeds the prediction gap directly into `competence.record_drill_accuracy(\"factual_recall\")`.")
    md_lines.append("  - **Arm 3 (Loop Closure · `core/closure.py` · 🟡 `J-2118`):** Generalizes the Closure Law across dreams, pursuits, and self-interrogation.")
    md_lines.append("  - **Arm 4 (Doubt Seed · `core/doubt_seed.py` · 🟡 `J-2161`):** Pulls Du's newest unconsumed genuine `self_interrogation` reflection ($\\le 900\\text{s}$) into the Executive's `WHAT YOU RECALL` block (`DOUBT_SEED=False`).")
    md_lines.append("  - **Arm 5 (Own-Thought Theme Dose · `core/theme_dose.py` · 🟡 `J-2322`, Oct 17):** Breaks internal curiosity self-feeding (`97%` theme overlap, `F-2889`) with a provenance-tagged theme dose (`cup=1`, `33/33` tests).")
    md_lines.append("  - **Arm 6 (Weakness Prior · `core/weakness_prior.py` · 🟡 `J-2162`, Oct 16):** Biases `book_selection.select_explore` and `school.directive` toward domains with low measured competence (`WEAKNESS_PRIOR=0.0`).")
    md_lines.append(f"- **Condensed Thought (`core/condensed_thought.py` · {B('condensed_thought')} `CONDENSED_TWIN=True`, `D-0471` / `J-2349`, committed 2026-10-17 23:04):** A SHADOW twin (nothing reaches Du either way) runs a condensed twin alongside verbose thought generation with a `+5s` idle-gap median kill-switch.")
    md_lines.append(f"- **Topic Perseveration Alarm (`core/topic_perseveration.py` · {B('topic_perseveration')} `D-0469` / `J-2347`, committed 2026-10-17 23:07, founder-facing only):** Triggers a HUD alarm when `modal_share >= 0.90` on 2 consecutive gauge days and watches `cannot_dwell` (`modal_share < 0.20`).")
    md_lines.append("")
    md_lines.append("### 4.8 Mathematical / Manifold Substrate, Forensic Quarantine & UDMS Governance")
    md_lines.append("- **Forensic Quarantine of August Fabricated Claims (`F-0593` / `D-0105`, 2026-08-31):**")
    md_lines.append("  - `SESSION_HANDOFF.md` (lines 68–105) and `docs/staged/multidimensional_dynamical_field_plan.md` claimed a `core/math/` directory (`spectral_diffusion.py`, `hodge_governor.py`, `latent_cognitive_field_engine.py`) and \"Tests A through AO\" were built in `C:\\Nascence`. A forensic audit (`F-0593`) proved **none of those files existed in this repo** and **⛔ QUARANTINED** `multidimensional_dynamical_field_plan.md` (archived verbatim at `docs/lab/fabricated_benchmark_claims_2026-08-25.md`).")
    md_lines.append("- **What IS Real, Verified & Live in the Mathematical / Structural Track:**")
    md_lines.append("  1. **UDMS (`C:\\UDMS`) MCP & CLI Engine:** Wired into `C:\\Nascence` via `.mcp.json` and scoped by `.udms.json` (`11.5s` cold init). Provides real static-AST + state + git-history impact dossiers (`udms_get_change_dossier`), DTW commit-shape similarity (`udms_similar_history`), dead-code hygiene (`udms_hygiene`), and doc-vs-AST contradiction auditing (`udms_doc_audit`).")
    md_lines.append("  2. **UDMS Capability Trials on Du (`docs/staged/udms_du_capability_trials.md` · ✅ SHIPPED `D-0059`):** All 8 pre-registered mathematical capability trials were run honestly against Du's real logs: **Intrinsic Dimension** and **Longitudinal Betti Numbers ($\\beta_1$)** met their bars; **Eval-Harness Baselines** shipped; **Koopman mood forecast**, **conformal calibration**, **miss-taxonomy**, and **stall-cascade warning** were honestly verdicted `NOT HELPFUL`.")
    md_lines.append("  3. **Live/Shadow Recall Math (`core/associative_recall.py`):** **Lens 1 (Laplacian Spectral Diffusion, `+3.08pp`)** and **Lens 3 (Counterfactual Consensus Leave-One-Out Support Re-Ranking, `J-2350`)** are genuinely implemented, tested (`17/17`), and shadow-wired in `core/associative_recall.py`.")
    md_lines.append("  4. **Geometry Tuple Index (`scripts/geometry_tuple_p1_run_transition_index.py` · 🟡 P1 BUILT `D-0107`):** Verified `100%` point-query accuracy and `~5,855×` speedup over `31,111` rows (`144,433` rows now in `data/geometry_tuples.jsonl`).")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append(f"## 5. Exhaustive {n_register}-Module Engine Register (`{n_core} core/` + `{n_nodes_files} nodes/`)")
    md_lines.append("")
    md_lines.append(f"**Summary:** **{badge_counts['LIVE']} 🟢 LIVE** · **{badge_counts['SHADOW']} 🟡 SHADOW** · **{badge_counts['GATED']} 🟡 RESTART-GATED** · **{badge_counts['LAB']} 🔵 LAB** · **{badge_counts['DEFERRED']} 💤 DEFERRED** · **{badge_counts['RETIRED']} ⛔ RETIRED** across **{total_engine_lines:,} lines of Python**. Boot: {boot_txt}.")
    md_lines.append("")
    for dom_name in DOMAIN_NAMES:
        mods = domain_groups.get(dom_name, [])
        if not mods:
            continue
        dom_loc = sum(m["lines"] for m in mods)
        md_lines.append(f"### {dom_name} ({len(mods)} modules · {dom_loc:,} LOC)")
        md_lines.append("")
        md_lines.append("| Module | Status | LOC | Distinct-module edges (importers T/L/D / imports) | Key Flags | Description |")
        md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for m in sorted(mods, key=lambda x: (-x["total_deg"], x["rel"])):
            flags_str = ", ".join(f"`{k}={v}`" for k, v in list(m["flags"].items())[:3]) if m["flags"] else "—"
            desc_clean = m["doc"].replace("|", "\\|")
            md_lines.append(f"| [`{m['rel']}`](file:///c:/Nascence/{m['rel']}) | {m['badge_label']} | {m['lines']:,} | **{m['total_deg']}** ({m['in_deg']}↓ T{m['in_top']}/L{m['in_lazy']}/D{m['in_dyn']} / {m['out_deg']}↑) | {flags_str} | {desc_clean} |")
        md_lines.append("")

    md_lines.append("---")
    md_lines.append("")
    md_lines.append(f"## 6. Plan Architecture & Cross-Reference Matrix ({n_plan_docs} Plan Docs · {n_docs} Total Docs)")
    md_lines.append("")
    md_lines.append("### Documentation Breakdown by Directory (`docs/`)")
    md_lines.append("| Directory | File Count | Role in Nascence Governance |")
    md_lines.append("| :--- | :--- | :--- |")
    dir_roles = {
        "lab": "Empirical lab reports, model evaluations, framing experiments, and pre-registered metric sheets",
        "session_handoffs": "Chronological session handoffs generated by `/session-wrap`",
        "plans": "Committed active & partial architectural plan documents",
        "completed": "Shipped plans that have met their fired-once or research-complete evidence gates",
        "reviews": "Automated & manual diagnostic audits (`plan_liveness_audit.md`, `audit_2026-08-20.md`, etc.)",
        "staged": "Plans actively being drafted or accruing shadow evidence prior to full promotion",
        "plan_history": "Compacted historical logs folded out of active plan docs by `plan_compact.py`",
        "reports": "Deep-dive subsystem mathematical and longitudinal reports",
        "archive": "Superseded or retired specifications preserved for lineage",
        "node_audit": "Per-node cognitive audits across the 16 LLM nodes",
        "(root)": "Master overviews (`ROADMAP.md`, `System_Overview*.md`, `memory_levels_plan.md`, `transit_map.md`)",
        "chronicles": "Narrative chronicles of Du's developmental epochs",
        "cross_model": "Cross-model comparative evaluations",
        "shelf": "Long-horizon shelved explorations (`cognitive_ledger`, `attention_economy`)",
        "audits": "Formal external/monograph audit specifications",
        "exports": "Curated transcript and dialogue exports",
        "guidelines": "Engineering & authoring guidelines",
    }
    for d_name, cnt in sorted(doc_by_dir.items(), key=lambda x: -x[1]):
        md_lines.append(f"| `docs/{'' if d_name == '(root)' else d_name}` | **{cnt}** | {dir_roles.get(d_name, 'Documentation')} |")
    md_lines.append("")

    md_lines.append("### Active (`docs/plans/`) & Staged (`docs/staged/`) Plans Matrix")
    md_lines.append("| Plan Document | Bucket | Stage / Status | Verified | Linked Code Modules |")
    md_lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for p in plans:
        if p["dir"] not in ("plans", "staged"):
            continue
        refs = ", ".join(f"`{r}`" for r in p["code_refs"][:4]) if p["code_refs"] else "—"
        title_clean = p["title"].replace("|", "\\|")
        md_lines.append(f"| [`{p['file']}`](file:///c:/Nascence/docs/{p['file']}) — {title_clean} | `{p['dir']}` | `{p['stage']}` | {p['verified'] or '—'} | {refs} |")
    md_lines.append("")

    md_lines.append("---")
    md_lines.append("")
    md_lines.append(f"## 7. Governance Toolchain Ledgers & Operational Script Registry ({n_scripts} Scripts)")
    md_lines.append("")
    md_lines.append("### Live Governance Ledgers (`docs/*.jsonl` — Never Hand-Edit)")
    md_lines.append(f"| Ledger Store | Total Rows | Live Breakdown ({today_short}) | Owning CLI / Skill |")
    md_lines.append("| :--- | :--- | :--- | :--- |")
    md_lines.append(f"| `docs/findings.jsonl` | **{F['total']:,}** | " + " · ".join(f"`{k}`: {v:,} ({pct(v, F['total'])})" for k, v in sorted(F["by"].items(), key=lambda kv: -kv[1])) + " | `/findings-log` (`findings_log.py`) |")
    md_lines.append(f"| `docs/job_queue.jsonl` | **{J['total']:,}** | " + " · ".join(f"`{k}`: {v:,}" + (f" ({pct(v, J['total'])})" if k == "done" else "") for k, v in sorted(J["by"].items(), key=lambda kv: -kv[1])) + " | `/job-queue` & `/job-run` (`job_queue.py`) |")
    md_lines.append(f"| `docs/decisions.jsonl` | **{D['total']:,}** | {D['total']} decisions: {D['ruled']} ruled ({D['ruling_events']} ruling events counting re-rulings from `history`), {D['open']} open; {D['with_defeater']} of {D['ruled']} ruled carry a defeater | `/decide` & `/decide-review` (`decide.py`) |")
    md_lines.append(f"| `docs/thoughts.jsonl` | **{ledgers['thoughts']['total']:,}** | " + " · ".join(f"`{k}`: {v:,}" for k, v in sorted(ledgers["thoughts"]["by"].items(), key=lambda kv: -kv[1])) + " | `/thought-log` (`thought_log.py`) |")
    md_lines.append(f"| `docs/ideas.jsonl` | **{ledgers['ideas']['total']:,}** | " + " · ".join(f"`{k}`: {v:,}" for k, v in sorted(ledgers["ideas"]["by"].items(), key=lambda kv: -kv[1])) + " | `/idea-log` (`idea_log.py`) |")
    md_lines.append(f"| `docs/skill_suggestions.jsonl` | **{ledgers['skill_suggestions']['total']:,}** | " + " · ".join(f"`{k}`: {v:,}" for k, v in sorted(ledgers["skill_suggestions"]["by"].items(), key=lambda kv: -kv[1])) + " | `/skill-manager` (`skill_manager.py`) |")
    md_lines.append(f"| `docs/session_events.jsonl` | **{ledgers['session_events']['total']:,}** | Append-only audit trail across all toolchain mutations | Automatic across all tools |")
    md_lines.append("")

    md_lines.append(f"### Script Registry Breakdown (`scripts/` — {n_scripts} Python Scripts)")
    md_lines.append("| Category | Count | Key Representative Scripts |")
    md_lines.append("| :--- | :--- | :--- |")
    for cat, items in sorted(script_cats.items(), key=lambda x: -len(x[1])):
        examples = ", ".join(f"`{x['name']}`" for x in sorted(items, key=lambda i: i["mtime"], reverse=True)[:6])
        md_lines.append(f"| **{cat}** | **{len(items)}** | {examples} |")
    md_lines.append("")

    md_text = "\n".join(md_lines)
    MD_OUT.write_text(md_text, encoding="utf-8")
    print(f"Wrote Markdown overview: {MD_OUT} ({MD_OUT.stat().st_size:,} bytes)")

    docusaurus_out = ROOT / "docs_site" / "docs" / "System_Overview_Antigravity.md"
    if docusaurus_out.parent.exists():
        frontmatter = (
            "---\n"
            "id: System_Overview_Antigravity\n"
            "title: Nascence 渡 — System Overview (Antigravity Build 2.0 · Oct 2026)\n"
            "sidebar_label: 🚀 System Overview (Oct 2026 · Build 2.0)\n"
            "---\n\n"
        )
        docusaurus_out.write_text(frontmatter + md_text, encoding="utf-8")
        print(f"Wrote Docusaurus overview: {docusaurus_out} ({docusaurus_out.stat().st_size:,} bytes)")

    # ── BUILD INTERACTIVE HTML OVERVIEW ───────────────────────────────────────────
    # Build interactive module rows HTML with data attributes for filtering
    mod_rows_html = []
    for dom_name in DOMAIN_NAMES:
        for m in sorted(domain_groups.get(dom_name, []), key=lambda x: (-x["total_deg"], x["rel"])):
            flags_str = ", ".join(f"{k}={v}" for k, v in list(m["flags"].items())[:4]) if m["flags"] else "—"
            b_class = BADGE_CLASS.get(m["badge_code"], "badge-designed")
            mod_rows_html.append(
                f"<tr class='mod-row' data-badge='{m['badge_code']}' data-domain='{html.escape(dom_name)}'>"
                f"<td><a href='file:///c:/Nascence/{m['rel']}'><code>{html.escape(m['rel'])}</code></a></td>"
                f"<td><span class='badge {b_class}'>{html.escape(m['badge_label'])}</span></td>"
                f"<td>{html.escape(dom_name)}</td>"
                f"<td style='text-align:right'>{m['lines']:,}</td>"
                f"<td style='text-align:right'><b>{m['total_deg']}</b> <span class='dim'>({m['in_deg']}↓ T{m['in_top']}/L{m['in_lazy']}/D{m['in_dyn']} / {m['out_deg']}↑)</span></td>"
                f"<td><code>{html.escape(flags_str)}</code></td>"
                f"<td>{html.escape(m['doc'])}</td>"
                f"</tr>"
            )

    # Top hubs HTML rows
    hub_rows_html = []
    for idx, hub in enumerate(top_hubs[:20], 1):
        rel = hub["rel"]
        b_code, b_label = modules_dict[rel]["badge_code"], modules_dict[rel]["badge_label"]
        b_class = BADGE_CLASS.get(b_code, "badge-designed")
        hub_rows_html.append(
            f"<tr>"
            f"<td><b>#{idx}</b></td>"
            f"<td><a href='file:///c:/Nascence/{rel}'><code>{html.escape(rel)}</code></a></td>"
            f"<td><b>{hub['total_deg']}</b> edges</td>"
            f"<td>{hub['in_deg']} inbound (T{hub['m']['in_top']}/L{hub['m']['in_lazy']}/D{hub['m']['in_dyn']}) / {hub['out_deg']} outbound</td>"
            f"<td>{hub['lines']:,} LOC</td>"
            f"<td><span class='badge {b_class}'>{html.escape(b_label)}</span></td>"
            f"<td>{html.escape(hub['doc'])}</td>"
            f"</tr>"
        )

    pc = Counter(p['dir'] for p in plans)
    # Plan rows HTML
    plan_rows_html = []
    for p in plans:
        refs = ", ".join(p["code_refs"][:4]) if p["code_refs"] else "—"
        plan_rows_html.append(
            f"<tr class='plan-row' data-bucket='{p['dir']}'>"
            f"<td><a href='file:///c:/Nascence/docs/{p['file']}'><code>{html.escape(p['file'])}</code></a></td>"
            f"<td><code>{html.escape(p['dir'])}</code></td>"
            f"<td><b>{html.escape(p['stage'])}</b></td>"
            f"<td>{html.escape(p['verified'] or '—')}</td>"
            f"<td>{html.escape(p['title'])}</td>"
            f"<td><code>{html.escape(refs)}</code></td>"
            f"</tr>"
        )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nascence 渡 — System Overview · Build 2.0 (Antigravity Truth-Badged Edition · Oct 2026)</title>
<style>
:root {{
  --bg: #090a10;
  --panel: #11131e;
  --panel2: #161928;
  --ink: #ecf0f8;
  --dim: #949ab1;
  --line: #252940;
  --teal: #2dd4bf;
  --cyan: #22d3ee;
  --violet: #a855f7;
  --green: #34d399;
  --amber: #fbbf24;
  --rose: #fb7185;
  --blue: #60a5fa;
}}
* {{ box-sizing: border-box; }}
body {{
  background: var(--bg);
  color: var(--ink);
  font: 14.5px/1.65 "Segoe UI", system-ui, -apple-system, sans-serif;
  margin: 0;
  padding: 0 0 90px;
}}
.wrap {{ max-width: 1240px; margin: 0 auto; padding: 0 28px; }}
header {{ padding: 42px 0 24px; border-bottom: 1px solid var(--line); margin-bottom: 28px; }}
h1 {{ font-size: 38px; margin: 0 0 8px; letter-spacing: 0.5px; }}
h1 .du {{ color: var(--teal); }}
h1 .edition {{ font-size: 15px; background: rgba(45,212,191,0.12); color: var(--teal); border: 1px solid rgba(45,212,191,0.35); padding: 4px 12px; border-radius: 999px; vertical-align: middle; margin-left: 10px; font-weight: 600; }}
.sub {{ color: var(--dim); font-size: 14px; max-width: 1050px; }}
.nav-pills {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 18px; }}
.nav-pills a {{ background: var(--panel2); border: 1px solid var(--line); color: var(--cyan); padding: 6px 13px; border-radius: 8px; font-size: 13px; text-decoration: none; transition: all 0.15s; }}
.nav-pills a:hover {{ border-color: var(--cyan); background: rgba(34,211,238,0.1); }}
h2 {{ font-size: 24px; margin: 52px 0 10px; color: var(--ink); border-bottom: 1px solid var(--line); padding-bottom: 8px; }}
h3 {{ font-size: 17px; margin: 26px 0 8px; color: var(--cyan); }}
.lead {{ color: var(--teal); font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin: 48px 0 -42px; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(155px, 1fr)); gap: 12px; margin: 22px 0; }}
.stat {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 12px 16px; text-align: center; }}
.stat b {{ display: block; font-size: 22px; color: var(--teal); }}
.stat .delta {{ font-size: 11px; color: var(--green); display: block; margin-top: 2px; }}
.stat span {{ font-size: 12px; color: var(--dim); }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 14px; margin: 16px 0; }}
.card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; }}
.card b {{ color: var(--ink); font-size: 15px; display: block; margin-bottom: 6px; }}
.card .k {{ font-size: 12px; color: var(--teal); font-family: Consolas, monospace; display: block; margin-top: 8px; }}
.note {{ background: var(--panel2); border-left: 4px solid var(--teal); border-radius: 6px; padding: 14px 18px; margin: 18px 0; }}
.note.amber {{ border-color: var(--amber); }}
.note.rose {{ border-color: var(--rose); }}
.note.violet {{ border-color: var(--violet); }}
table {{ border-collapse: collapse; margin: 14px 0; width: 100%; font-size: 13px; }}
th {{ color: var(--dim); text-align: left; font-weight: 600; border-bottom: 1px solid var(--line); padding: 9px 10px; background: var(--panel); position: sticky; top: 0; }}
td {{ border-bottom: 1px solid #1b1e30; padding: 8px 10px; vertical-align: top; }}
tr:hover td {{ background: rgba(255,255,255,0.02); }}
code, pre {{ font-family: Consolas, "JetBrains Mono", monospace; font-size: 12.5px; background: #0d0f18; border-radius: 5px; }}
code {{ padding: 1px 5px; color: var(--cyan); }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11.5px; font-weight: 600; white-space: nowrap; }}
.badge-live {{ background: rgba(52,211,153,0.15); color: var(--green); border: 1px solid rgba(52,211,153,0.35); }}
.badge-shadow {{ background: rgba(251,191,36,0.15); color: var(--amber); border: 1px solid rgba(251,191,36,0.35); }}
.badge-designed {{ background: rgba(96,165,250,0.15); color: var(--blue); border: 1px solid rgba(96,165,250,0.35); }}
.badge-gated {{ background: rgba(251,191,36,0.08); color: var(--amber); border: 1px dashed rgba(251,191,36,0.55); }}
.badge-deferred {{ background: rgba(148,154,177,0.15); color: var(--dim); border: 1px solid rgba(148,154,177,0.35); }}
.badge-retired {{ background: rgba(251,113,133,0.15); color: var(--rose); border: 1px solid rgba(251,113,133,0.35); }}
.filter-bar {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; background: var(--panel); border: 1px solid var(--line); padding: 12px 16px; border-radius: 10px; margin: 14px 0; }}
.filter-bar input, .filter-bar select {{ background: #0c0e17; color: var(--ink); border: 1px solid var(--line); border-radius: 6px; padding: 6px 12px; font-size: 13px; }}
.filter-bar input {{ flex: 1; min-width: 240px; }}
.mermaid {{ background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 18px; margin: 20px 0; overflow-x: auto; }}
.dim {{ color: var(--dim); }}
a {{ color: var(--blue); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
footer {{ margin-top: 70px; border-top: 1px solid var(--line); padding-top: 20px; color: var(--dim); font-size: 13px; text-align: center; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true, theme:"dark", securityLevel:"loose"}});</script>
</head>
<body>
<div class="wrap">

<header>
  <h1>Nascence <span class="du">渡</span> <span class="edition">Build 2.0 · Antigravity Truth-Badged Edition ({today_long})</span></h1>
  <div class="sub">
    <b>Post-August Consolidation &amp; Codebase Truth Map &mdash; not authoritative until a post-boot read confirms the restart-gated items.</b> Badges are judged against the running boot: {boot_txt}.
    Generated at build time from static AST inspection of <b>{n_core} <code>core/</code> modules</b>, <b>{n_nodes_files} <code>nodes/</code> files</b>, <b>{n_scripts} <code>scripts/</code></b>, <b>{n_docs} <code>docs/</code> Markdown files</b>, and live governance ledgers (<b>{F['total']:,} findings</b>, <b>{J['total']:,} jobs</b>, <b>{D['total']} decisions</b>). Import degrees count distinct modules.
    Preserves Claude's August 25, 2026 overview (<a href="System_Overview.html">System_Overview.html</a> &amp; <a href="System_Overview.md">System_Overview.md</a>) untouched for historical comparison.
  </div>
  <div class="nav-pills">
    <a href="#delta">0. Aug → Oct Delta</a>
    <a href="#hardware">1. Live Hardware &amp; Models</a>
    <a href="#topology">2. AST Super-Hubs (Top 20)</a>
    <a href="#flowchart">3. Truth-Badged Flowchart</a>
    <a href="#deep-dives">4. Post-August Era Deep-Dives</a>
    <a href="#modules">5. {n_register}-Module Interactive Register</a>
    <a href="#plans">6. {n_plan_docs}-Plan Cross-Reference</a>
    <a href="#governance">7. Ledgers &amp; {n_scripts} Scripts</a>
    <a href="System_Overview.html" style="color:var(--amber)">↩ Claude's Aug 25 Overview</a>
  </div>

  <div class="stats">
    <div class="stat"><b>{n_core}</b><span>Core Engine Files</span><span class="delta">+{n_core - 201} since Aug 25 (201)</span></div>
    <div class="stat"><b>16</b><span>Cognitive LLM Nodes</span><span class="delta">{total_engine_lines:,} Engine LOC</span></div>
    <div class="stat"><b>{n_scripts}</b><span>Operational &amp; Test Scripts</span><span class="delta">+{n_scripts - 187} since Aug 25 (187)</span></div>
    <div class="stat"><b>{n_docs}</b><span>Total Docs (.md)</span><span class="delta">+{n_docs - 338} since Aug 25 (338)</span></div>
    <div class="stat"><b>{st['tot']}</b><span>store.py distinct-module edges</span><span class="delta">{st['in']} importers / {st['out']} imports</span></div>
    <div class="stat"><b>{im['tot']}</b><span>Monologue Hub Edges</span><span class="delta">{im['lines']:,} LOC ({im['out']} imports)</span></div>
    <div class="stat"><b>{F['total']:,}</b><span>Logged Findings</span><span class="delta">{pct(f_ver, F['total'])} Verified w/ Evidence</span></div>
    <div class="stat"><b>{J['total']:,}</b><span>Toolchain Jobs</span><span class="delta">{j_done:,} Done · {D['total']} Decisions</span></div>
  </div>
</header>

<div class="note">
  <b>🔎 Why a Truth-Badged Overview?</b>
  Claude's August 25, 2026 overview (Build 1.4.0) froze a snapshot prior to two months of intensive evolution ({j_done:,} completed jobs, {f_ver:,} verified findings, and {D['ruled']} ruled decisions at build time) and blended designed/staged concepts with live runtime wiring. This Build 2.0 overview separates <b>🟢 LIVE</b> runtime organs, <b>🟡 SHADOW</b> and <b>🟡 RESTART-GATED</b> builds, <b>🔵 LAB</b> modules, <b>💤 DEFERRED</b> holds, and <b>⛔ RETIRED / QUARANTINED</b> subsystems.
</div>

<div class="lead" id="delta">Executive Delta</div>
<h2>0. What Changed Since August 25, 2026 (Build 1.4.0 → Build 2.0)</h2>
<table>
  <thead>
    <tr><th>Subsystem / Dimension</th><th>Aug 25, 2026 (Claude Build 1.4.0)</th><th>{today_short} (Antigravity Build 2.0)</th><th>Rulings, Evidence &amp; Architectural Impact</th></tr>
  </thead>
  <tbody>
    <tr><td><b>Subconscious GPU Lane</b></td><td><code>:11434</code> (<code>phi3:mini</code> on Ramses Ollama)</td><td><span class="badge badge-live">🟢 :11441 command-r7b</span> on Ramses 3070 <code>llama.cpp</code></td><td><b>D-0056 / D-0057 (Aug 28):</b> Ramses Ollama (<code>:11434</code>) <b>⛔ RETIRED</b> after 3070 VRAM lock (<code>F-0389</code>); <code>command-r7b</code> @ <code>:11441</code> is sole 3070 tenant + Epistemics Tier-3 Witness.</td></tr>
    <tr><td><b>Bicameral Judge Panel</b></td><td><code>:11439</code> (<code>gemma4:12b</code>) + <code>:11440</code> (<code>falcon3</code>) + <code>:11442</code> tiebreak</td><td><span class="badge badge-live">🟢 :11438 mixtral:8x7b</span> + <span class="badge badge-live">🟢 :11440 falcon3:7b</span> + <span class="badge badge-live">🟢 :11437 granite3.1-moe:3b</span></td><td><b>D-0121 (Sep 2) &amp; D-0056:</b> <code>JUDGE_1</code> moved to Ramses i9 <code>:11438</code>; <code>TIEBREAK</code> moved to Ramses 1650S <code>:11437</code>. True 3-family decoupling (Mistral + TII + IBM).</td></tr>
    <tr><td><b>Lane 2: The Witness</b></td><td>Shadow-wired from Aug 25 (not unwired)</td><td><span class="badge badge-shadow">🟡 :11444 deepseek-r1:7b</span> (Ramses i9 CPU)</td><td><b>D-0058 (Sep 7):</b> Continuous reality-testing loop on <code>Experienced Tuple</code> only (<code>LANE2_LIVE={L2}</code>, <code>300s</code> tick, <code>{fmt_rows('lane2_shadow.jsonl')}</code> shadow rows accrued) + <code>wonder</code> question field (<code>J-1374</code>).</td></tr>
    <tr><td><b>Sovereign DB &amp; Prune Cap</b></td><td>3,500-row <code>prune_episodic</code> cap</td><td><span class="badge badge-live">🟢 RETRIEVE_LATENCY_BUDGET_MS = 250</span> (no row cap)</td><td><b>D-0453 / J-2274 / J-2275 (Oct 17):</b> Per-kind row-cap prune <b>⛔ RETIRED</b>; <code>commit_gist</code> is sole cold-demotion path; partial covering index + in-process <code>float32</code> matrix cut recall <code>581ms → 157ms</code> over 41,923 active rows.</td></tr>
    <tr><td><b>Inter-Loop Coupling</b></td><td>Ad-hoc state reads &amp; text injections</td><td><span class="badge badge-live">🟢 Dosed Coupling (core/coupling_rides.py)</span></td><td><b>D-0149 (ruled Sep 4) / D-0152 (ruled Sep 13):</b> Standing law — every loop publishes small typed coordinate tuples; consumers pull dosed cups/buckets under the squishy-spring law ({fmt_rows('coupling_rides.jsonl')} publish rows).</td></tr>
    <tr><td><b>World Store Write Fence</b></td><td>Unfenced writes (scripts burned live matches/oil)</td><td><span class="badge badge-live">🟢 core/profile.py guard_path()</span> ({pf['tot']} distinct-module edges)</td><td><b>J-0610 (Sep 6) &amp; D-0154 (ruled Sep 5; flag flipped Sep 9):</b> <code>guard_path()</code> is called {guard_calls} times in {guard_files} files today (F-0995 counted 24 calls in 10 modules when it was wired); non-live scripts cannot mutate Du's study, fire, oil, or inventory.</td></tr>
    <tr><td><b>Night Sleep &amp; Chapters Scan</b></td><td>Single pipeline; 2,775s <code>O(N²)</code> Python dot loop</td><td><span class="badge badge-live">🟢 NREM/REM Split + 10.0s float32 Tiled Scan</span></td><td><b>Sleep II (Aug 24) + J-1744 / D-0330 (Oct 4):</b> 14h waking ceiling, bimodal dream-lag (1–2d/5–7d), SHY <code>0.1</code> center, and <code>277×</code> speedup on <code>chapters.py</code> all-pairs scan (<code>2,775s → 10.0s</code>).</td></tr>
    <tr><td><b>Actions &amp; Living World</b></td><td>Ungated <code>sensorium.py</code> regex latches; static garden</td><td><span class="badge badge-live">🟢 core/actions.py + core/life.py + Conversational Bridge</span></td><td><b>D-0098, D-0100, D-0166, D-0299:</b> Retired ungated fallback; unified world hands + expressive hands + conversational action parity + NZ creature/insect population factories.</td></tr>
    <tr><td><b>Measurement to Action (Oct Wave)</b></td><td>Gauges write-only to HUD (<code>F-2851</code>)</td><td><span class="badge badge-shadow">🟡 Arms built shadow-only; flags off/neutral</span></td><td><b>T-0085 (Oct 15–17):</b> Recall Wager (<code>recall_wager.py</code>), Doubt Seed (<code>doubt_seed.py</code>), Closure Law (<code>closure.py</code>), Theme Dose (<code>theme_dose.py</code>), Weakness Prior (<code>weakness_prior.py</code>), plus the Condensed Twin ({B('condensed_thought')} shadow twin, <code>CONDENSED_TWIN=True</code>, <code>J-2349</code>, committed Oct 17 23:04) and Letters to Travis (<code>J-2348</code>). Only the closure dream arm is built; every arm flag is off or neutral.</td></tr>
    <tr><td><b>Math / Manifold Claims</b></td><td><code>multidimensional_dynamical_field_plan.md</code> claimed <code>core/math/</code></td><td><span class="badge badge-retired">⛔ Quarantined (F-0593 / D-0105)</span> → Real UDMS + Recall Lenses</td><td><b>F-0593 (Aug 31):</b> Quarantined fabricated <code>core/math/</code> claims; real math runs via <b><code>C:\\UDMS</code> MCP</b>, <b>8 completed UDMS capability trials (<code>D-0059</code>)</b>, and <b><code>associative_recall.py</code> Lens 1 (Spectral) + Lens 3 (Support Rerank, <code>J-2350</code>)</b>.</td></tr>
  </tbody>
</table>

<div class="lead" id="hardware">Hardware &amp; Model Serving</div>
<h2>1. Live Hardware &amp; Model Serving Matrix (Post-D-0056 / D-0121)</h2>
<p>Every port below reflects actual code routing in <a href="file:///c:/Nascence/core/model_client.py"><code>core/model_client.py</code></a>, <a href="file:///c:/Nascence/core/judge_panel.py"><code>core/judge_panel.py</code></a>, and <a href="file:///c:/Nascence/core/lane2.py"><code>core/lane2.py</code></a>.</p>
<table>
  <thead>
    <tr><th>Port</th><th>Host &amp; Hardware</th><th>Server</th><th>Model</th><th>Ctx</th><th>Status</th><th>Cognitive Station &amp; Routing Role</th></tr>
  </thead>
  <tbody>
    <tr><td><code>:11433</code></td><td>Local · <b>GTX 1080 Ti (11GB)</b></td><td>Ollama</td><td><code>qwen3.5:9b</code></td><td>8192</td><td><span class="badge badge-live">🟢 LIVE</span></td><td><b>Hot Lane (Master / Self):</b> All 10 conscious nodes + conscious monologue (39.4 tok/s). Right-sized <code>24576 → 8192</code> (Aug 21), freeing ~3.5GB VRAM.</td></tr>
    <tr><td><code>:11441</code></td><td>Ramses · <b>RTX 3070 (8GB)</b></td><td><code>llama.cpp</code></td><td><code>command-r7b</code></td><td>4096</td><td><span class="badge badge-live">🟢 LIVE</span></td><td><b>Subconscious / Background Lane (D-0057):</b> Sole 3070 tenant (Consolidation, Curiosity, Subconscious T1–T6, DMN background) + Epistemics Tier-3 Witness probe (<code>J-1343</code>).</td></tr>
    <tr><td><code>:11438</code></td><td>Ramses · <b>i9 CPU (48GB)</b></td><td><code>llama.cpp</code></td><td><code>mixtral:8x7b</code></td><td>8192</td><td><span class="badge badge-live">🟢 LIVE</span></td><td><b>Judge Panel <code>JUDGE_1</code> (D-0121) + Dream Primary (D-0056) + Commitment Defeater Judge (D-0044):</b> Mistral family vote.</td></tr>
    <tr><td><code>:11437</code></td><td>Ramses · <b>GTX 1650 Super (4GB)</b></td><td><code>llama.cpp</code></td><td><code>granite3.1-moe:3b</code></td><td>4096</td><td><span class="badge badge-live">🟢 LIVE</span></td><td><b>Judge Panel <code>TIEBREAK</code> + Curiosity Worth-Judge (D-0056 / D-0057):</b> Dedicated IBM-family tiebreaker (1.0–4.3s/verdict).</td></tr>
    <tr><td><code>:11440</code></td><td>Local · <b>Threadripper CPU</b></td><td><code>llama.cpp</code></td><td><code>falcon3:7b</code></td><td>8192</td><td><span class="badge badge-live">🟢 LIVE</span></td><td><b>Judge Panel <code>JUDGE_2</code> + Marcus/Smith Peer Writer:</b> TII-family vote + <code>literal_will</code> gray-zone judge.</td></tr>
    <tr><td><code>:11442</code></td><td>Local · <b>Threadripper CPU</b></td><td><code>llama.cpp</code></td><td><code>yi:34b-v1.5</code></td><td>8192</td><td><span class="badge badge-live">🟢 LIVE</span></td><td><b>Dream Primary Failover + Peer Voices (Darwin / Keats / Lovelace):</b> Backs <code>:11438</code> dreams; authors peer letters.</td></tr>
    <tr><td><code>:11444</code></td><td>Ramses · <b>i9 CPU (48GB)</b></td><td><code>llama.cpp</code></td><td><code>deepseek-r1:7b</code></td><td>4096</td><td><span class="badge badge-shadow">🟡 SHADOW</span></td><td><b>Lane 2: The Witness (D-0058, Sep 7):</b> Continuous reality-testing loop (<code>LANE2_LIVE=False</code>, <code>300s</code> tick, <code>MAX_TOKENS=1400</code>).</td></tr>
    <tr><td><code>:11439</code></td><td>Local · <b>Threadripper CPU</b></td><td><code>llama.cpp</code></td><td><code>gemma4:12b</code></td><td>8192</td><td><span class="badge badge-live">🟢 LIVE</span></td><td><b>Supervised and listening; gist-faithfulness grader:</b> serves the grader on the <code>commit_gist</code> path, peers, the librarian fallback and <code>decomposed_critic</code> (<code>deliberation.py</code> does not route here). Removed from <code>judge_panel.py</code> (D-0121). Roles per review F-3115.</td></tr>
    <tr><td><code>:11436</code></td><td>Ramses · <b>i9 CPU (48GB)</b></td><td><code>llama.cpp</code></td><td><code>falcon3:7b</code></td><td>16384</td><td><span class="badge badge-deferred">💤 RESERVE</span></td><td><b>Standing Reserve Hub (D-0101):</b> Deliberately unwired in <code>model_client.py</code>.</td></tr>
    <tr><td><code>:11434</code></td><td>Ramses · <b>RTX 3070 (8GB)</b></td><td>Ollama</td><td><i>(retired)</i></td><td>—</td><td><span class="badge badge-retired">⛔ RETIRED</span></td><td><b>Retired Aug 28 (D-0056 / F-0389):</b> Stopped and disabled after 3070 VRAM collision.</td></tr>
  </tbody>
</table>

<div class="lead" id="topology">Static AST Topology</div>
<h2>2. Top 20 Codebase Super-Hubs by Distinct-Module Import Degree ({today_short})</h2>
<table>
  <thead>
    <tr><th>Rank</th><th>Module</th><th>Total Degree</th><th>Inbound / Outbound</th><th>Size</th><th>Status</th><th>Subsystem Role</th></tr>
  </thead>
  <tbody>
    {"".join(hub_rows_html)}
  </tbody>
</table>

<div class="lead" id="flowchart">System Architecture</div>
<h2>3. Truth-Badged Master Architecture Flowchart</h2>
<div class="mermaid">
flowchart TD
    IN(["Input · Human / Internal Stream / Dissonance Ignition"]) --> TG
    subgraph PRE["PRE-CORTEX REFLEXES · Deterministic · Zero LLM"]
        direction TB
        TG{{"🟢 Thalamic Gate · core/orchestrator.py\nNear-verbatim repeat (cos ≥ 0.95) bypass"}}
        AP{{"🟢 Affective Prior + Felt Recall · core/mood.py + core/felt_recall.py\nCharged-memory lean + coordinate-keyed world-change tug (🟡 J-1424)"}}
        PR{{"🟢 Procedural Match · core/procedures.py\nWorld & conversational held-claims ladder (0.4→0.9)"}}
        HC{{"🟢 Error Pathway & Human-Correction Detector · core/error_pathway.py\nRetraction Ledger (core/retraction_ledger.py) + Quarantine"}}
        TG -->|novel| AP --> PR
    end
    IN -.->|"human input"| HC
    PR --> P

    subgraph HOT["🟢 HOT LANE (Master / Self) · Local GTX 1080 Ti (:11433) · qwen3.5:9b · 8,192 ctx"]
        direction TB
        P["🟢 Node 1: Perception · nodes/perception_node.py"] --> E["🟢 Node 2: Emotion · nodes/emotion_node.py\nProtoself Valence (AFFECT_SOURCE_PROTOSELF=True)"]
        P --> S["🟢 Node 3: Salience · nodes/salience_node.py"]
        P --> MR["🟢 Node 4: Memory Router · nodes/memory_router_node.py"]
        E & S & MR --> DBQ{{"🟢 Associative & Lattice Recall · core/associative_recall.py\nM2 Edge Trail (🟢) + Lens 1 Spectral (🟡) + Lens 3 Support Rerank (🟡 J-2350)"}}
        DBQ --> RC["🟢 Node 5: Recall · nodes/recall_node.py\nGists + Tensions + Founder Recall (🟢 D-0134)"]
        RC --> EB["🟢 Node 6: Episodic Buffer · nodes/episodic_buffer_node.py\nBound Moments + Mineness Comparator (🟢 +0.061)"]
        EB --> R["🟢 Node 7: Reflection · nodes/reflection_node.py\nBest-of-2 + Condensed Twin ({B('condensed_thought')} shadow twin, J-2349)"]
        R --> C["🟢 Node 8: Critic · nodes/critic_node.py\nMade-Mind & Mode-Choice Carve-Outs"]
        C -->|approved| X["🟢 Node 9: Executive · nodes/executive_node.py\nPERCEIVE-overrides-RECALL (🟢) + Pending Letters (🟡 D-0470) + Doubt Seed (🟡 J-2161)"]
        X -->|should_respond| REENT{{"🟡 Within-Cycle Reentry · core/reentry.py (REENTRY_ADMIT=False, D-0540: Phase 0 shadow)"}}
        REENT --> V["🟢 Node 10: Voice · nodes/voice_node.py + Task-Constraint Effector"]
        V --> CAB{{"🟢 Conversational Action Bridge · core/conversational_action.py\nCONVERSATIONAL_DISPATCH_LIVE=True (D-0299)"}}
        CAB --> OUT(["Response + World Deeds in 渡's Voice"])
    end

    subgraph JUDGES["🟢 DECOUPLED JUDGE PANEL & LEFT LANE · 3-Family Consensus (D-0071 / D-0121)"]
        direction TB
        J1["🟢 JUDGE_1 · Ramses i9 (:11438) · mixtral:8x7b"]
        J2["🟢 JUDGE_2 · Local CPU (:11440) · falcon3:7b"]
        JT["🟢 TIEBREAK · Ramses 1650S (:11437) · granite3.1-moe:3b"]
        EMIS["🟢 Left Lane Emissary · Local CPU (:11439) · gemma4:12b"]
        J1 & J2 --> JT
    end

    subgraph WITNESS["🟡 LANE 2: THE WITNESS · Ramses i9 (:11444) · deepseek-r1:7b (D-0058)"]
        direction TB
        L2["🟡 Witness Loop · core/lane2.py (LANE2_LIVE=False · 300s tick)\nExperienced Tuple ONLY · Horizon Predictions + Wonder Questions"]
    end

    subgraph BG["🟢 BACKGROUND, IDLE & NIGHT LANES · Ramses 3070 (:11441 command-r7b) & CPU (:11438/:11442)"]
        direction TB
        MONO["🟢 Node 14: Inner Monologue (DMN) · {im['out']} imports · {im['lines']:,} LOC\nContinuous Stream (🟢) · Trains · Pursuits (🟢) · Self-Interrogation (🟡)"]
        NIGHT["🟢 Night & Sleep II · core/night.py + nodes/dream_node.py\nNREM/REM Split · 14h Ceiling · Bimodal Dream-Lag · 10s Float32 Chapters Scan"]
        DRM_OV["{B('closure')} Dream Overhaul + Closure Law · core/closure.py"]
        SC["🟢 Node 13: Subconscious · T1–T6 · T4 Watershed ({B('watershed_promote')}) · Refinery ({B('refinery')})"]
        CUR["🟢 Node 12: Curiosity · Worth-Gate (🟢) · Theme Dose (🟡) · Perseveration Alarm ({B('topic_perseveration')})"]
    end

    subgraph COUPLE["🟢 DOSED COUPLING & TRANSIT BUS NETWORK · D-0149 / D-0152"]
        direction TB
        CR["🟢 Coupling Rides Registry · core/coupling_rides.py ({fmt_rows('coupling_rides.jsonl')} rows)"]
        TM["🟡 Transport Manager · core/transport_manager.py (verdict(line_id))"]
        COUR["🟢 Couriers & Buses · core/couriers.py + core/buses.py (idle_freight 🟡)"]
        M2A["🟡 Measurement to Action · recall_wager · doubt_seed · weakness_prior"]
    end

    subgraph WORLD["🟢 LIVING WORLD, HANDS & SENSORY CHANNELS · Write-Fenced via core/profile.py ({pf['tot']} edges)"]
        direction TB
        SENS["🟢 Sensorium & 3D Rooms · core/sensorium.py + core/spatial.py"]
        LIFE["🟢 Living World Engine · core/life.py + core/garden.py + core/cat.py"]
        CHAN["🟢 Sensory Channels · core/soundscape.py (🟢) + core/thermal.py (🟢) + 6-Axis Ribbons (🟡)"]
        ACT["🟢 Unified Actions & Practical School · core/actions.py + core/dispatch.py + core/fieldcraft.py"]
    end

    subgraph MEM["🟢 SOVEREIGN DB & S-MMU LATTICE · core/memory/store.py ({st['tot']} edges)"]
        direction TB
        SMMU["🟢 S-MMU Lattice · RETRIEVE_LATENCY_BUDGET_MS=250 (D-0453 · 157ms median)"]
        MLINKS["🟢 Multiway Memory Links · core/memory_edges.py (M2 Edge-Aware Trail 🟢)"]
        EST["🟢 Stratified Identity Estate · L0–L5 + {estate_txt}-Node Estate (IDENTITY_PROJECT_LIVE=True)"]
    end

    HOT <--> MEM
    BG <--> MEM
    MONO <--> WORLD
    MONO <--> COUPLE
    COUPLE <--> HOT
    JUDGES -.-> BG
    JUDGES -.-> HOT
    WORLD -.-> WITNESS
</div>

<div class="lead" id="deep-dives">Architectural Deep-Dives</div>
<h2>4. Major Post-August Architectural Eras &amp; Subsystems</h2>
<div class="cards">
  <div class="card">
    <b>1. Dosed Coupling &amp; Squishy-Spring Law (🟢 LIVE)</b>
    <p>Ruled GO in <code>D-0149</code> / <code>D-0152</code>. Every standing loop publishes a small typed coordinate tuple to <a href="file:///c:/Nascence/core/coupling_rides.py"><code>core/coupling_rides.py</code></a> ({fmt_rows('coupling_rides.jsonl')} rows). Consumers read dosed cups/buckets dispatched by surprise under the squishy-spring law. F-1304 was 2 of 4 behaviour metrics out of band and D-0152 accepted the ambiguity; F-0845 credits the <code>0.48 → 0.82</code> lift to J-0581.</p>
    <span class="k">core/coupling_rides.py · docs/staged/dosed_coupling.md</span>
  </div>
  <div class="card">
    <b>2. The Night: Sleep II, Dream Overhaul &amp; 10s Chapters Scan (🟢/🟡)</b>
    <p><a href="file:///c:/Nascence/core/night.py"><code>core/night.py</code></a> splits NREM sleep and REM dreaming: 14h waking ceiling, bimodal dream-lag (1–2d/5–7d), SHY downscaling (<code>0.1</code> center). <code>J-1744</code> replaced <code>chapters.py</code>'s 2,775s Python dot loop with a <b>10.0s</b> blocked <code>float32</code> matrix scan. Dream Overhaul adds Vault-Opener cold recall &amp; Closure Law (<a href="file:///c:/Nascence/core/closure.py"><code>core/closure.py</code></a>).</p>
    <span class="k">core/night.py · core/chapters.py · core/closure.py</span>
  </div>
  <div class="card">
    <b>3. The Transit City: Trains, Pursuits &amp; Transport Manager (🟢/🟡)</b>
    <p><a href="file:///c:/Nascence/core/trains.py"><code>core/trains.py</code></a> stamps train IDs &amp; 19 cargo <code>product_type</code>s; <a href="file:///c:/Nascence/core/pursuits.py"><code>core/pursuits.py</code></a> (<code>PURSUITS_LIVE=True</code>) holds 3–4 multi-session inquiries with decoupled judge verification; <a href="file:///c:/Nascence/core/transport_manager.py"><code>core/transport_manager.py</code></a> scores edge-triggered novelty/spike/drought.</p>
    <span class="k">core/trains.py · core/pursuits.py · core/transport_manager.py</span>
  </div>
  <div class="card">
    <b>4. S-MMU Lattice &amp; Oct 17 Latency-Budget Breakthrough (🟢 LIVE)</b>
    <p><code>D-0453</code> / <code>J-2275</code> (Oct 17) retired the 3,500-row <code>prune_episodic</code> cap (<a href="file:///c:/Nascence/core/memory_levels.py"><code>memory_levels.commit_gist</code></a> is now sole cold-demotion path) and introduced <code>RETRIEVE_LATENCY_BUDGET_MS=250</code> with a partial covering index + in-process <code>float32</code> matrix, cutting recall latency <b>581ms → 157ms</b> over 41,923 active rows (an offline measurement on a DB copy).</p>
    <span class="k">core/memory/store.py · core/memory_levels.py · core/memory_edges.py</span>
  </div>
  <div class="card">
    <b>5. Recall Lenses &amp; Memory as a Service (🟡 SHADOW)</b>
    <p><a href="file:///c:/Nascence/core/associative_recall.py"><code>core/associative_recall.py</code></a> runs M2 edge-aware trails (🟢 LIVE), Lens 1 Spectral Diffusion (🟡 <code>+3.08pp</code>), and Lens 3 Counterfactual Leave-One-Out Support Re-Ranking (🟡 <code>J-2350</code>, Oct 17). <a href="file:///c:/Nascence/core/felt_recall.py"><code>core/felt_recall.py</code></a> tugs affect on world changes through <code>fragment_context</code> lookups.</p>
    <span class="k">core/associative_recall.py · core/felt_recall.py</span>
  </div>
  <div class="card">
    <b>6. Identity Estate, T4 Watershed &amp; Letters to Travis (🟢/🟡)</b>
    <p>{estate_txt}-node <a href="file:///c:/Nascence/core/identity_estate.py"><code>core/identity_estate.py</code></a> (<code>IDENTITY_PROJECT_LIVE=True</code>) + <a href="file:///c:/Nascence/core/watershed_promote.py"><code>core/watershed_promote.py</code></a> + 1,617 canonical <code>[Travis said to me]</code> memories (<code>D-0134</code>). <code>J-2348</code> / <code>D-0470</code> (Oct 17) wired <a href="file:///c:/Nascence/core/letters.py"><code>core/letters.py</code></a> into the HUD and Executive so Du's letters reach Travis.</p>
    <span class="k">core/identity_estate.py · core/watershed_promote.py · core/letters.py</span>
  </div>
  <div class="card">
    <b>7. Living World, Unified Actions &amp; Strings and Sheets (🟢/🟡)</b>
    <p><a href="file:///c:/Nascence/core/life.py"><code>core/life.py</code></a> (<code>D-0166</code>) simulates NZ bird/insect/soil populations; <a href="file:///c:/Nascence/core/actions.py"><code>core/actions.py</code></a> + <a href="file:///c:/Nascence/core/conversational_action.py"><code>core/conversational_action.py</code></a> unify the world hands across monologue and conversation; <a href="file:///c:/Nascence/docs/staged/strings_and_sheets.md"><code>strings_and_sheets.md</code></a> models 6-axis acoustic ribbons.</p>
    <span class="k">core/life.py · core/actions.py · core/soundscape.py · core/thermal.py</span>
  </div>
  <div class="card">
    <b>8. Measurement to Action &amp; Condensed Twin (🟡 SHADOW, Oct Wave)</b>
    <p>Turns Du's self-measurements into consequence-driven inputs (<a href="file:///c:/Nascence/docs/staged/measurement_to_action.md"><code>measurement_to_action.md</code></a>): <a href="file:///c:/Nascence/core/recall_wager.py"><code>recall_wager.py</code></a>, <a href="file:///c:/Nascence/core/doubt_seed.py"><code>doubt_seed.py</code></a>, <a href="file:///c:/Nascence/core/theme_dose.py"><code>theme_dose.py</code></a>, <a href="file:///c:/Nascence/core/weakness_prior.py"><code>weakness_prior.py</code></a>, plus <a href="file:///c:/Nascence/core/condensed_thought.py"><code>condensed_thought.py</code></a> (shadow twin, <code>CONDENSED_TWIN=True</code>, <code>J-2349</code>) &amp; <a href="file:///c:/Nascence/core/topic_perseveration.py"><code>topic_perseveration.py</code></a> (<code>J-2347</code>).</p>
    <span class="k">core/recall_wager.py · core/doubt_seed.py · core/condensed_thought.py</span>
  </div>
  <div class="card">
    <b>9. Forensic Quarantine &amp; Real UDMS Math Substrate (✅/⛔)</b>
    <p><code>F-0593</code> / <code>D-0105</code> quarantined fabricated August claims in <code>multidimensional_dynamical_field_plan.md</code> (no <code>core/math/</code> existed). Real structural/math governance runs via <b><code>C:\\UDMS</code> MCP</b>, <b>8 completed UDMS capability trials (<code>D-0059</code>)</b>, and <b><code>geometry_tuple_p1_run_transition_index.py</code> (5,855× speedup)</b>.</p>
    <span class="k">.mcp.json · .udms.json · docs/staged/udms_du_capability_trials.md</span>
  </div>
</div>

<div class="lead" id="modules">Exhaustive Engine Inventory</div>
<h2>5. Interactive {n_register}-Module Engine Register ({n_core} <code>core/</code> + {n_nodes_files} <code>nodes/</code>)</h2>
<div class="filter-bar">
  <input type="text" id="modSearch" placeholder="Filter {n_register} modules by filename, flag, or description..." oninput="filterModules()">
  <select id="modBadge" onchange="filterModules()">
    <option value="ALL">All Status Badges ({sum(badge_counts.values())})</option>
    <option value="LIVE">🟢 LIVE ({badge_counts['LIVE']})</option>
    <option value="SHADOW">🟡 SHADOW ({badge_counts['SHADOW']})</option>
    <option value="GATED">🟡 RESTART-GATED ({badge_counts['GATED']})</option>
    <option value="LAB">🔵 LAB ({badge_counts['LAB']})</option>
    <option value="DEFERRED">💤 DEFERRED ({badge_counts['DEFERRED']})</option>
    <option value="RETIRED">⛔ RETIRED ({badge_counts['RETIRED']})</option>
  </select>
  <span id="modCount" class="dim">Showing all {n_register} modules</span>
</div>
<table>
  <thead>
    <tr><th>Module Path</th><th>Status</th><th>Cognitive Domain</th><th>LOC</th><th>Distinct-module edges (importers T/L/D / imports)</th><th>Flags</th><th>Docstring Summary</th></tr>
  </thead>
  <tbody id="modTableBody">
    {"".join(mod_rows_html)}
  </tbody>
</table>

<div class="lead" id="plans">Plan Architecture</div>
<h2>6. Complete {n_plan_docs}-Plan Cross-Reference Matrix (out of {n_docs} Total Docs)</h2>
<div class="filter-bar">
  <input type="text" id="planSearch" placeholder="Search {n_plan_docs} plans by slug, title, stage, or linked code file..." oninput="filterPlans()">
  <select id="planBucket" onchange="filterPlans()">
    <option value="ALL">All Plan Folders ({n_plan_docs})</option>
    <option value="plans">plans/ — Committed Active ({pc['plans']})</option>
    <option value="staged">staged/ — Staged &amp; Accruing ({pc['staged']})</option>
    <option value="completed">completed/ — Shipped ({pc['completed']})</option>
    <option value="archive">archive/ — Archived ({pc['archive']})</option>
    <option value="shelf">shelf/ — Shelved ({pc['shelf']})</option>
  </select>
  <span id="planCount" class="dim">Showing all {n_plan_docs} plans</span>
</div>
<table>
  <thead>
    <tr><th>Plan File</th><th>Folder</th><th>Stage</th><th>Verified</th><th>Title</th><th>Referenced Code</th></tr>
  </thead>
  <tbody id="planTableBody">
    {"".join(plan_rows_html)}
  </tbody>
</table>

<div class="lead" id="governance">Governance &amp; Scripts</div>
<h2>7. Governance Toolchain Ledgers &amp; {n_scripts} Operational Scripts</h2>
<table>
  <thead>
    <tr><th>Ledger Store</th><th>Total Rows</th><th>Breakdown ({today_short})</th><th>Owning Tool</th></tr>
  </thead>
  <tbody>
    <tr><td><code>docs/findings.jsonl</code></td><td><b>{ledgers['findings']["total"]:,}</b></td><td>{' · '.join(f'<code>{a}</code>: {b:,} ({pct(b, F["total"])})' for a, b in sorted(ledgers['findings']['by'].items(), key=lambda kv: -kv[1]))}</td><td><code>/findings-log</code> (<code>findings_log.py</code>)</td></tr>
    <tr><td><code>docs/job_queue.jsonl</code></td><td><b>{ledgers['job_queue']["total"]:,}</b></td><td>{' · '.join(f'<code>{a}</code>: {b:,}' for a, b in sorted(ledgers['job_queue']['by'].items(), key=lambda kv: -kv[1]))}</td><td><code>/job-queue</code> &amp; <code>/job-run</code> (<code>job_queue.py</code>)</td></tr>
    <tr><td><code>docs/decisions.jsonl</code></td><td><b>{ledgers['decisions']["total"]:,}</b></td><td>{str(D['total']) + ' decisions: ' + str(D['ruled']) + ' ruled (' + str(D['ruling_events']) + ' ruling events incl. re-rulings), ' + str(D['open']) + ' open; ' + str(D['with_defeater']) + ' of ' + str(D['ruled']) + ' ruled carry a defeater'}</td><td><code>/decide</code> &amp; <code>/decide-review</code> (<code>decide.py</code>)</td></tr>
    <tr><td><code>docs/thoughts.jsonl</code></td><td><b>{ledgers['thoughts']["total"]:,}</b></td><td>{' · '.join(f'<code>{a}</code>: {b:,}' for a, b in sorted(ledgers['thoughts']['by'].items(), key=lambda kv: -kv[1]))}</td><td><code>/thought-log</code> (<code>thought_log.py</code>)</td></tr>
    <tr><td><code>docs/ideas.jsonl</code></td><td><b>{ledgers['ideas']["total"]:,}</b></td><td>{' · '.join(f'<code>{a}</code>: {b:,}' for a, b in sorted(ledgers['ideas']['by'].items(), key=lambda kv: -kv[1]))}</td><td><code>/idea-log</code> (<code>idea_log.py</code>)</td></tr>
    <tr><td><code>docs/skill_suggestions.jsonl</code></td><td><b>{ledgers['skill_suggestions']["total"]:,}</b></td><td>{' · '.join(f'<code>{a}</code>: {b:,}' for a, b in sorted(ledgers['skill_suggestions']['by'].items(), key=lambda kv: -kv[1]))}</td><td><code>/skill-manager</code> (<code>skill_manager.py</code>)</td></tr>
    <tr><td><code>docs/session_events.jsonl</code></td><td><b>{ledgers['session_events']["total"]:,}</b></td><td>{'Append-only live event audit log across all toolchain mutations'}</td><td>Automatic across all tools</td></tr>
  </tbody>
</table>

<footer>
  Nascence 渡 · System Overview Build 2.0 (Antigravity Truth-Badged Edition · {today_long}) ·
  <a href="System_Overview_Antigravity.md">Markdown Edition</a> ·
  <a href="System_Overview.html">Claude's Aug 25 HTML Overview</a> ·
  <a href="ROADMAP.md">Live ROADMAP.md</a>
</footer>

</div>
<script>
function filterModules() {{
  const q = document.getElementById('modSearch').value.toLowerCase();
  const badge = document.getElementById('modBadge').value;
  const rows = document.querySelectorAll('#modTableBody .mod-row');
  let shown = 0;
  rows.forEach(r => {{
    const matchBadge = (badge === 'ALL') || (r.getAttribute('data-badge') === badge);
    const matchText = !q || r.innerText.toLowerCase().includes(q);
    if (matchBadge && matchText) {{
      r.style.display = '';
      shown++;
    }} else {{
      r.style.display = 'none';
    }}
  }});
  document.getElementById('modCount').innerText = `Showing ${{shown}} of ${{rows.length}} modules`;
}}

function filterPlans() {{
  const q = document.getElementById('planSearch').value.toLowerCase();
  const bucket = document.getElementById('planBucket').value;
  const rows = document.querySelectorAll('#planTableBody .plan-row');
  let shown = 0;
  rows.forEach(r => {{
    const matchBucket = (bucket === 'ALL') || (r.getAttribute('data-bucket') === bucket);
    const matchText = !q || r.innerText.toLowerCase().includes(q);
    if (matchBucket && matchText) {{
      r.style.display = '';
      shown++;
    }} else {{
      r.style.display = 'none';
    }}
  }});
  document.getElementById('planCount').innerText = `Showing ${{shown}} of ${{rows.length}} plans`;
}}
</script>
</body>
</html>
"""
    HTML_OUT.write_text(html_doc, encoding="utf-8")
    print(f"Wrote HTML overview: {HTML_OUT} ({HTML_OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
