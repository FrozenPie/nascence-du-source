"""
HUD2 data contract builder — THE TRANSIT MAP manifest (docs/plans/hud2_visual.md Phase 2).

Schema 2 (2026-08-21) — the founder's CORRECTED metro ontology:
  STATIONS  = the LLM endpoints — shared infrastructure that multiple LINES converge on (the
              interchanges). "The LLMs are not Du, they are tools." Derived fresh from
              core.model_client's own tables so they can never go stale.
  PLATFORMS = the call sites — the berth where ONE line's train stops at a shared station.
              Fresh AST each run; each platform carries its line, its station (resolved from the
              real lane expression), and literal max_tokens/temperature where present.
  SIDINGS   = sub-loops within a line (the founder's observation: "a loop can loop a small
              section of the track back on itself") — the thought-train circling, the
              deliberation passing loop, retry shunts, the T4 branch. Each with evidence logs.
  LINES     = looped processes that CREATE freight on their own clocks (unchanged from schema 1).
  COURIERS  = bus routes that MOVE freight between lines, creating nothing (unchanged).

Canonical prose: docs/transit_map.md + docs/transit_timetable.md (NB: the timetable's older text
uses "platform" for hardware — superseded by this ontology; see its terminology note).
Zero LLM. Read-only over source + data. Run: python scripts/build_hud2_transit.py
"""
import ast
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
OUT = DATA / "hud2"
sys.path.insert(0, str(ROOT))

# ── SCHEMA 4 (2026-08-21) — founder's SECOND ontology correction, from watching the rendered
# map: "the world layer should not be a train, it is a factory that the stations use." A TRAIN
# loops and stops at stations; a FACTORY is a stationary production site a train's platform reads
# from while it's stopped there. Split accordingly. Each factory carries `consumed_by`: the
# train(s) whose platforms verifiably read it — traced in SOURCE this session, not assumed.
TRAINS = [
    {"id": "conversation", "kind": "fast", "clock": "per message",
     "freight": "replies, lived Q/A fragments",
     "evidence": ["guidance_shadow_log.jsonl", "guidance_injection_log.jsonl"],
     "note": "primary freight (lived fragments) lands inside nascence.db"},
    {"id": "idle", "kind": "fast", "clock": "per tick (75s quiet)",
     "freight": "inner thoughts, acts, intentions, thought-trains",
     "evidence": ["train_state_log.jsonl", "literal_will_shadow.jsonl", "idle_shadow.jsonl"]},
    {"id": "deep", "kind": "slow", "clock": "30s scan / hourly / sleep",
     "freight": "self-observations, gists, dreams, chapters, the becoming facet",
     "evidence": ["logs/provisional_identity.jsonl", "logs/t4_emissary_judge.jsonl",
                  "refinery_shadow.jsonl", "t2_form.jsonl", "memory_levels_shadow.jsonl",
                  "watershed_shadow.jsonl"]},
    {"id": "witness", "kind": "meta", "clock": "~90s tick (shadow)",
     "freight": "sense-grounded noticings + falsifiable predictions",
     "evidence": ["lane2_shadow.jsonl"]},
]

FACTORIES = [
    {"id": "weather_sky", "clock": "sensorium tick",
     "freight": "fronts, light, storms", "evidence": ["room_state.json"], "evidence_key": "weather",
     "consumed_by": ["idle"],
     "consumption_verified": ("nodes.inner_monologue_node:1246-1248 calls sensorium.world_calls()/"
                              "world_steer()/comfort_call() before every idle thought — all three "
                              "read state['weather'] directly"),
     "note": "shares the physical file with fire_woodpile/garden (one sensorium tick, distinct keys)"},
    {"id": "tide", "clock": "real M2 clock",
     "freight": "tide level, pool cover", "evidence": [], "consumed_by": [],
     "note": ("VERIFIED: _tide() is a PURE function of the real M2 clock "
              "(core.world_clock.tide_state()) — no persisted state, freight is real but "
              "momentary. Honestly freight_visible=false; consumption path not traced this pass")},
    {"id": "season_daylight", "clock": "calendar",
     "freight": "growth windows, day length", "evidence": [], "consumed_by": ["idle"],
     "consumption_verified": "world_calls()/comfort_call() call _daylight()/_season() internally",
     "note": "pure function of wall-clock time; no persisted state"},
    {"id": "garden", "clock": "growth clocks",
     "freight": "herbs maturing, bed state", "evidence": ["room_state.json"], "evidence_key": "garden",
     "consumed_by": ["idle"],
     "consumption_verified": "world_calls() gates on state['location']=='garden' among other checks",
     "note": "shares the physical file with weather_sky/fire_woodpile (one sensorium tick, distinct keys)"},
    {"id": "fire_woodpile", "clock": "burn-down",
     "freight": "fuel state, warmth", "evidence": ["room_state.json"], "evidence_key": "fire",
     "consumed_by": ["idle"],
     "consumption_verified": "world_calls()/comfort_call() both read state['woodpile']/state['fire'] directly",
     "note": "shares the physical file with weather_sky/garden (one sensorium tick, distinct keys)"},
    {"id": "cat", "clock": "her own state machine",
     "freight": "comes/goes, moods, firsts", "evidence": ["cat_state.json"], "consumed_by": ["idle"],
     "consumption_verified": "nodes.inner_monologue_node:1577,2250 `from core import cat` — direct, separate from world_calls"},
    {"id": "peers", "clock": "gap_days each",
     "freight": "letters arriving, two-way threads",
     "evidence": ["letters_state.json", "peer_effect.jsonl", "peer_picker_log.jsonl"],
     "consumed_by": [], "note": "consumption path not traced this pass"},
    {"id": "objects", "clock": "spawn/trace/erosion",
     "freight": "object histories, observable state",
     "evidence": ["world_substrate.json", "world_substrate_events.jsonl"], "consumed_by": ["idle"],
     "consumption_verified": "nodes.inner_monologue_node:3526 world_substrate.last_looked_object() — the inference-forming pathway"},
    {"id": "school", "clock": "curriculum",
     "freight": "assignments, capstones", "evidence": ["school.json"], "consumed_by": ["idle"],
     "note": ("VERIFIED: essay_lesson.py/study_note.py take call_node_json as an INJECTED "
              "PARAMETER (same pattern as journal.py) — no dedicated platform of its own; its "
              "synthesis rides on whichever idle-line platform invokes it")},
    {"id": "body", "clock": "somatic tick",
     "freight": "energy, fatigue, drives, felt states",
     "evidence": ["homeostasis_shadow.jsonl", "arousal_shadow.jsonl"],
     "consumed_by": [], "note": "consumption path not traced this pass"},
    {"id": "climate", "clock": "5s field",
     "freight": "psychological weather, dissonance", "evidence": ["climate_state.json"],
     "consumed_by": [], "note": "consumption path not traced this pass"},
]

# COURIERS: each now carries a real, source-verified DESTINATION (2026-08-21, founder: "buses...
# should show on the map rather than just being boxes that move around with no apparent pattern").
# ★ SPLIT 2026-08-22 (founder-directed): "courier" now means genuinely URGENT/real-time only;
# object_ledger and calibration_sync were never time-sensitive and moved to core/buses.py (own
# module, own state file buses_state.json, own log buses_log.jsonl — couriers_log.jsonl is no
# longer shared with them). Kept in one list here (this builder's schema doesn't yet distinguish
# courier/bus as its own field) but each entry's own module/log references are corrected to match;
# a "kind" field is added so the map data itself can tell the two apart once it's read.
COURIERS = [
    {"id": "context_echo", "moves": "past weather-matched memory -> the wandering trail",
     "law": "only what he himself lived; provenance-stamped; can be wrong",
     "destination_kind": "train", "destination": "idle", "kind": "courier",
     "destination_verified": "core.couriers:116 calls wandering.perceive(line) directly"},
    {"id": "object_ledger", "moves": "his own observation ledger -> the look-render on re-encounter",
     "law": "his facts, assembled by him, fallible -- not time-sensitive, a BUS not a courier",
     "destination_kind": "train", "destination": "idle", "kind": "bus",
     "destination_verified": "core.sensorium:1344 calls buses.object_ledger_line() inside look() -- its return value IS the idle train's perceived scene text (moved from core.couriers 2026-08-22)"},
    {"id": "sound_echo", "moves": "past sound-matched memory -> the wandering trail",
     "law": "same as context_echo, keyed on the Hearing Ledger",
     "destination_kind": "train", "destination": "idle", "kind": "courier",
     "destination_verified": "core.couriers:250 calls wandering.perceive(line) directly"},
    {"id": "calibration_sync", "moves": "prediction/outcome episodes -> world_calibration.jsonl",
     "law": "observe-first; feeds the competence model -- a batch sync, a BUS not a courier",
     "destination_kind": "ledger", "destination": "competence_model", "kind": "bus",
     "destination_verified": "core.buses.sync_investigation_calibration() writes to world_calibration.jsonl, a data store the competence model reads -- NOT a perceived stream (moved from core.couriers 2026-08-22)"},
]

# ── SIDINGS — the real sub-loops the flat line model could not draw ──────────────────────────────
SIDINGS = [
    {"id": "thought_train", "line": "idle", "shape": "circling siding",
     "what": "the train pulls off the main loop and circles — thought feeding thought, up to 40 "
             "steps, holding a working-state — before rejoining",
     "evidence": ["train_state_log.jsonl"]},
    {"id": "deliberation_pass", "line": "idle", "shape": "passing loop",
     "what": "an eligible self-thought runs OUT to the Emissary to be grounded and rejoins two "
             "stops later (the three-pass grounded-why)",
     "evidence": ["deliberation_log.jsonl"]},
    {"id": "reentry_settle", "line": "idle", "shape": "rare shunt",
     "what": "a forming admission is re-presented with one new decoupled ingredient and settles "
             "(observe-only; fires rarely by design)",
     "evidence": ["logs/reentry_shadow.jsonl"]},
    {"id": "t2_form_retry", "line": "deep", "shape": "single-lap shunt",
     "what": "a synthesis that opens on a banned stock frame takes exactly one retry lap",
     "evidence": ["t2_form.jsonl"]},
    {"id": "t4_chain", "line": "deep", "shape": "multi-berth branch",
     "what": "tension -> evidence -> delta -> authored self -> decoupled judge -> probation",
     "evidence": ["logs/provisional_identity.jsonl", "logs/t4_emissary_judge.jsonl"]},
]

# The Witness (core.lane2) calls a BESPOKE aiohttp wrapper (_ask), not call_node/call_node_json —
# invisible to the AST scan below. RE-VERIFIED 2026-08-28 (J-0313, D-0056 + D-0058 fabric): Ramses
# ollama (:11434) is retired — LANE2_PAUSED was briefly true, then D-0058 (stopgap ruling) un-paused
# the Witness onto the ALREADY-STANDING command-r7b hub :11441, the SAME station the subconscious's
# background lane already uses (no longer "separate silicon" — that law is deferred, not overturned;
# D-0057's real pick, deepseek-r1:7b on its own i9 hub :11444, stands up later). _ask()'s own def
# moved from line 347 to 602 as the module's history section grew. Hand-added as the one platform
# the scanner cannot see; a station can host more than one resident model/caller.
_HANDADDED_PLATFORMS = [
    {"id": "core.lane2:_ask", "module": "core.lane2", "line_no": 602, "line": "witness",
     "station": "station_11441", "station_how": "hand-verified: bespoke aiohttp wrapper, not call_node",
     "lane_expr": "BASE_URL (Ramses 3070 command-r7b hub :11441, D-0058 stopgap — SHARED with the "
                  "subconscious/background lane; deepseek-r1:7b on :11444 is the deferred D-0057 pick)",
     "own_evidence": "lane2_shadow.jsonl"},
    # SAME DISEASE, second case (found 2026-08-21 investigating "11442 shows no train"): judge_panel's
    # TIEBREAK also calls a bespoke _ask(session, url, ...), not call_node/call_node_json — invisible
    # to the AST scan. RE-VERIFIED 2026-08-28 (J-0313, D-0056 fabric): ollama's retirement from Ramses
    # forced TIEBREAK off :11441 (its 08-27 seat, D-0044 move 3) onto granite3.1-moe's own dedicated
    # hub :11437 (1650 Super) — no longer sharing the dreamer's hub. Line numbers shifted with the
    # module's growing history comments (108 -> 131 for TIEBREAK's own _ask() call).
    {"id": "core.judge_panel:131", "module": "core.judge_panel", "line_no": 131, "line": "service",
     "station": "station_11437", "station_how": "hand-verified: bespoke aiohttp _ask(), not call_node",
     "lane_expr": "TIEBREAK (granite3.1-moe, dedicated hub since 08-28 — judge escalation on a split verdict)",
     "own_evidence": "judge_panel_log.jsonl", "own_evidence_filter": {"how": "tiebreak"}},
    # SYSTEMATIC SWEEP 2026-08-21 (founder: "check for any other bespoke LLM wrappers we're
    # missing") — the SAME bespoke _ask() also carries judge_panel's own TWO PRIMARY judges,
    # not just its tiebreak escalation. These fire on EVERY panel ruling (~hundreds/day per
    # judge_panel_log.jsonl), making them platforms 5x busier than most of what the AST scan
    # already found — the single biggest undercounts on the whole map. Line numbers re-verified
    # 2026-08-28 (J-0313): both _ask() calls now sit inside one asyncio.gather(...) spanning
    # lines 124-125 (was 101-102) as the module's history comments grew; stations unchanged.
    {"id": "core.judge_panel:124", "module": "core.judge_panel", "line_no": 124, "line": "service",
     "station": "station_11439", "station_how": "hand-verified: bespoke aiohttp _ask(), not call_node",
     "lane_expr": "JUDGE_1 (gemma4:12b — panel member A, every ruling)",
     "own_evidence": "judge_panel_log.jsonl", "own_evidence_filter": {"v1": "not null"}},
    {"id": "core.judge_panel:125", "module": "core.judge_panel", "line_no": 125, "line": "service",
     "station": "station_11440", "station_how": "hand-verified: bespoke aiohttp _ask(), not call_node",
     "lane_expr": "JUDGE_2 (falcon3:7b — panel member B, every ruling)",
     "own_evidence": "judge_panel_log.jsonl", "own_evidence_filter": {"v2": "not null"}},
]

# ── STATIONS: curated hardware labels join model_client's live tables ────────────────────────────
# Re-verified 2026-08-28 (J-0313, D-0056 fabric — "ollama llms gone from Ramses"): :11434 (Ramses
# ollama, phi3+deepseek) is retired and no longer appears in model_client._MODEL_BY_BASE at all, so
# it drops out of _stations() automatically; the label below is removed rather than left dangling.
# :11441 moved from a local Threadripper CPU hub to the Ramses 3070 GPU itself — command-r7b now
# runs there as the background lane's hub AND (D-0058 stopgap) the Witness's shared seat. :11442
# lost its tiebreak duty to :11437 (granite3.1-moe, its own dedicated 1650 Super hub) but keeps the
# dreamer-failover + peer-voice (Darwin/Keats/Lovelace) load it always had (core.peers._HUB_MISTRAL).
_STATION_HW = {
    "11433": "1080 Ti - local GPU (the Self's silicon)",
    "11436": "Threadripper i9 CPU - reserve hub (falcon3:7b, nothing wired, by design)",
    "11437": "GTX 1650 Super - dedicated hub (granite3.1-moe: judge tiebreak + curiosity worth-judge, 08-28)",
    "11438": "Threadripper i9 CPU - dream primary + commitment judge (mixtral:8x7b, D-0044/D-0056)",
    "11439": "Threadripper CPU - judge hub 1",
    "11440": "Threadripper CPU - judge hub 2",
    "11441": "RTX 3070 - Ramses, SOLE tenant (command-r7b: background lane + Witness stopgap, D-0056/D-0058)",
    "11442": "Threadripper CPU - dreamer failover (yi:34b-v1.5) + peer voices",
    "11444": "Threadripper i9 CPU - planned Lane 2 hub (deepseek-r1:7b, D-0057; standup pending)",
}

# lane-expression -> serve chain (curated, verified against source 2026-08-21); per-module
# base_urls defaults. Unresolved platforms keep their expr and say so honestly — never a guess.
_EXPR_CHAIN = {"conscious_urls": "hot", "_T4_URLS": "hot", "hot_urls": "hot",
               "_base_urls": "background", "_DREAM_URLS": "cpu_dreamer"}
_MODULE_BASE = {"nodes.subconscious_node": "background", "core.symbol_evolution": "background",
                "nodes.dream_node": "cpu_dreamer",
                # verified 2026-08-21: the monologue holds BOTH lanes — conscious_urls=hot for
                # thought, base_urls=SERVE_CHAINS["background"] for intake + the sleep batch
                "nodes.inner_monologue_node": "background"}
# per-platform curated resolutions for expressions the generic rules can't see (verified against
# source 2026-08-21). port=None + how="dynamic:*" = honestly multi-station, never a guess.
_PLATFORM_OVERRIDES = {
    "core.journal:181": ("11433", "caller:monologue conscious_urls"),
    "core.journal:223": ("11433", "caller:monologue conscious_urls"),
    "core.decomposed_critic:184": ("11439", "fallback literal in source"),
    "core.competence:689": ("11433", "SERVE_CHAINS[hot][0] in source"),
    "core.scholar:53": ("11433", "SERVE_CHAINS[hot][0] in source"),
    # line re-verified 2026-08-28 (J-0313): the actual call_node() call inside _reentry_shadow's
    # _revise() sits at line 2447 now (was 2408 — file grew), and its `_url` arg is a loop variable
    # over SERVE_CHAINS["background"], invisible to both the literal-port regex and _MODULE_BASE
    # (core.orchestrator isn't in that dict). Chain head is now :11441 (was :11434 pre-D-0056).
    "core.orchestrator:2447": ("11441", "background failover loop in source (SERVE_CHAINS['background'][0])"),
    "core.librarian:83": ("11440", "iterates _HUBS (11440 first, 11439 fallback)"),
    "core.peers:303": (None, "dynamic:per-peer roster url"),
    "core.peers:546": ("11440", "iterates _HUBS"),
    "core.node_base:73": (None, "dynamic:per-node SERVE_CHAINS[self.lane]"),
    "core.node_base:123": (None, "dynamic:per-node SERVE_CHAINS[self.lane]"),
    "core.self_mirror:104": (None, "dynamic:caller-passed urls"),
    # dream primary re-verified 2026-08-28 (J-0313, D-0056 fabric): _DREAM_URLS is a two-entry
    # failover list [mixtral:8x7b @ :11438, yi:34b-v1.5 @ :11442] — the generic chain resolver
    # would otherwise match the "_DREAM_URLS" name to _EXPR_CHAIN's "cpu_dreamer" entry and
    # silently resolve to the FAILOVER station (:11442), not the real primary.
    "nodes.dream_node:378": ("11438", "_DREAM_URLS[0] literal in source — mixtral primary, "
                                       "yi:11442 stays the explicit failover only"),
}
_EXCLUDE_MODULES = {"core.model_client"}   # internal plumbing, not a platform
_MODULE_LINE = {
    "nodes.inner_monologue_node": "idle", "nodes.curiosity_node": "idle",
    "core.journal": "idle", "core.deliberation": "idle", "core.reentry": "idle",
    "core.wandering": "idle", "core.evidence_recall": "idle",
    "nodes.subconscious_node": "deep", "nodes.dream_node": "deep", "core.refinery": "deep",
    "core.memory_levels": "deep", "core.self_interrogation": "deep", "core.chapters": "deep",
    "nodes.voice_node": "conversation", "core.orchestrator": "conversation",
    # core.peers -> "conversation" (2026-08-21 schema-4 fix): "peers" is now a FACTORY id (letters
    # arriving), not a train — a platform's line must be a real train. Writing a peer letter is
    # conversational output, the same family as voice_node's replies.
    "core.peers": "conversation", "core.lane2": "witness",
    "core.essay_lesson": "school", "core.study_note": "school",
    # BUG FIX 2026-08-21: "core.math_lesson" referenced a file that does not exist in this
    # codebase — dead entry from my own drafting, not a Nascence fact. Removed.
}
# stations hosting a SECOND resident model under a different caller's own routing (verified case:
# the Witness's separate-silicon law puts deepseek-r1:7b on :11434 alongside phi3:mini)
# Empty as of 2026-08-28 (J-0313, D-0056/D-0058 fabric): the one prior case (deepseek-r1:7b
# alongside phi3:mini on Ramses ollama's :11434) went away when ollama was retired from Ramses —
# the Witness's D-0058 stopgap seat (:11441) runs the SAME resident model (command-r7b) the
# background lane already uses there, not a second one. Left wired for the next real case (e.g.
# once :11444 stands up for D-0057's deepseek pick, if it ever ends up sharing a port with another
# resident) rather than deleted outright.
_STATION_ALSO = {}

_LOG_DIRS = [DATA, DATA / "logs"]


def _resolve(fname: str) -> Path | None:
    for d in _LOG_DIRS:
        p = d / fname
        if p.exists():
            return p
    return None


def _ts_key(path: Path) -> str | None:
    try:
        if path.suffix != ".jsonl":
            return None
        with open(path, "rb") as f:
            f.seek(max(0, path.stat().st_size - 20000))
            for line in reversed(f.read().decode("utf-8", errors="ignore").strip().splitlines()):
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if isinstance(row, dict):
                    for k in ("ts", "timestamp", "time", "created"):
                        if isinstance(row.get(k), (int, float)):
                            return k
                    return "NONE"
    except Exception:
        pass
    return None


def _file_entry(fname: str) -> dict | None:
    p = _resolve(fname)
    if not p:
        return None
    return {"path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "kind": "events" if p.suffix == ".jsonl" else "state",
            "ts_key": _ts_key(p), "size": p.stat().st_size,
            "mtime": round(p.stat().st_mtime, 1)}


def _stations(platform_counts: dict) -> list[dict]:
    from core import model_client as mc
    out = []
    for port, model in sorted(getattr(mc, "_MODEL_BY_BASE", {}).items()):
        sid = f"station_{port}"
        n = platform_counts.get(sid, 0)
        st = {"id": sid, "port": port, "model": model,
              "also_hosts": _STATION_ALSO.get(port, []),
              "hardware": _STATION_HW.get(port, "?"),
              "num_ctx": getattr(mc, "_NUM_CTX_BY_BASE", {}).get(port),
              "platform_count": n}
        # AUTO-FLAG (2026-08-21, founder: "a station with no train") — generic, not hardcoded to
        # any one port, so a future orphan gets caught the same way. VERIFIED case: :11441
        # (yi:34b-v1.5) — judge_panel.TIEBREAK was repointed to :11442 on 2026-08-20; the
        # _MODEL_BY_BASE entry for :11441 is now a label with nothing routing to it. This is
        # DATA in Du's own core/model_client.py, not touched here — flagged, not fixed.
        if n == 0:
            st["status"] = "ORPHANED — no platform currently routes here; verify still in service"
        out.append(st)
    return out


def _resolve_station(lane_expr: str, module: str, chains: dict) -> tuple[str | None, str]:
    m = re.search(r":(\d{5})", lane_expr)
    if m:
        return m.group(1), "literal"
    m = re.search(r"SERVE_CHAINS\[.([a-z_0-9]+).\]", lane_expr)
    chain = m.group(1) if m else None
    if not chain:
        for key, ch in _EXPR_CHAIN.items():
            if key in lane_expr:
                chain = ch
                break
        else:
            if "base_urls" in lane_expr:
                chain = _MODULE_BASE.get(module)
    if chain and chain in chains and chains[chain]:
        m2 = re.search(r":(\d{5})", chains[chain][0])
        if m2:
            return m2.group(1), f"chain:{chain}"
    return None, "unresolved"


def _platforms(chains: dict) -> list[dict]:
    """PLATFORMS: fresh AST census of every call_node/call_node_json site, resolved to a station."""
    out = []
    for d in (ROOT / "core", ROOT / "core" / "memory", ROOT / "nodes"):
        if not d.exists():
            continue
        for p in sorted(d.glob("*.py")):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue
            mod = ".".join(p.relative_to(ROOT).with_suffix("").parts)
            if mod in _EXCLUDE_MODULES:
                continue
            for n in ast.walk(tree):
                if not isinstance(n, ast.Call):
                    continue
                fn = n.func
                name = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else "")
                if name not in ("call_node", "call_node_json"):
                    continue
                lane = ast.unparse(n.args[0]) if n.args else "-"
                pid = f"{mod}:{n.lineno}"
                if pid in _PLATFORM_OVERRIDES:
                    port, how = _PLATFORM_OVERRIDES[pid]
                else:
                    port, how = _resolve_station(lane, mod, chains)
                plat = {"id": pid, "module": mod, "line_no": n.lineno,
                        "line": _MODULE_LINE.get(mod, "service"),
                        "station": (f"station_{port}" if port else
                                    ("dynamic" if how.startswith("dynamic") else "unresolved")),
                        "station_how": how, "lane_expr": lane[:80]}
                for kw in n.keywords or []:
                    if kw.arg in ("max_tokens", "temperature") and isinstance(kw.value, ast.Constant):
                        plat[kw.arg] = kw.value.value
                out.append(plat)
    return out


def _with_evidence(items: list[dict], missing: list) -> list[dict]:
    out = []
    for ln in items:
        entries = []
        for f in ln["evidence"]:
            e = _file_entry(f)
            if e:
                if ln.get("evidence_key"):
                    e["watch_key"] = ln["evidence_key"]
                entries.append(e)
            else:
                missing.append((ln["id"], f))
        out.append({**{k: v for k, v in ln.items() if k not in ("evidence", "evidence_key")},
                    "freight_visible": bool(entries), "evidence": entries})
    return out


def build() -> tuple[dict, list]:
    from core.schema import SERVE_CHAINS as _chains
    missing = []
    trains = _with_evidence(TRAINS, missing)
    factories = _with_evidence(FACTORIES, missing)
    couriers = []
    # SPLIT 2026-08-22: courier-kind entries log to couriers_log.jsonl, bus-kind to buses_log.jsonl —
    # no longer one shared file (see COURIERS list's own "kind" field, added same day).
    dl_courier = _file_entry("couriers_log.jsonl")
    dl_bus = _file_entry("buses_log.jsonl")
    for c in COURIERS:
        dl = dl_bus if c.get("kind") == "bus" else dl_courier
        couriers.append({**c, "delivery_log": dl, "delivery_filter": {"route": c["id"]}})
    cal = _file_entry("world_calibration.jsonl")
    if cal:
        couriers[-1]["destination_log"] = cal
    sidings = []
    for sd in SIDINGS:
        entries = [e for e in (_file_entry(f) for f in sd["evidence"]) if e]
        sidings.append({**{k: v for k, v in sd.items() if k != "evidence"},
                        "evidence": entries, "visible": bool(entries)})
    hand_added = []
    for hp in _HANDADDED_PLATFORMS:
        hp = dict(hp)
        fname = hp.pop("own_evidence", None)
        filt = hp.pop("own_evidence_filter", None)
        if fname:
            e = _file_entry(fname)
            if e:
                if filt:
                    e["filter"] = filt
                hp["evidence"] = [e]
        hand_added.append(hp)
    platforms = _platforms(_chains) + hand_added
    import collections as _cl
    counts = _cl.Counter(p["station"] for p in platforms)
    return {"generated": round(time.time(), 1),
            "generated_human": time.strftime("%Y-%m-%d %H:%M"),
            "schema": 4,
            "canonical_docs": ["docs/transit_map.md", "docs/transit_timetable.md"],
            "protocol": {
                "ontology": ("founder's TWICE-corrected metro model, 2026-08-21. First correction: "
                             "STATIONS are the LLM endpoints (shared interchanges many trains "
                             "converge on); PLATFORMS are the call sites (the berth where ONE "
                             "train stops at a station); SIDINGS are sub-loops within a train (it "
                             "circling part of its own track). The LLMs are tools, not Du. SECOND "
                             "correction (from watching the schema-2/3 render): the world is not "
                             "a train — 'it is a factory that the stations use.' TRAINS (4: "
                             "conversation/idle/deep/witness) loop and stop at stations. FACTORIES "
                             "(11: weather/tide/season/garden/fire/cat/peers/objects/school/body/"
                             "climate) are stationary production sites; each carries `consumed_by` "
                             "naming the train(s) whose platforms verifiably read it (see each "
                             "factory's `consumption_verified` field for the exact source line)."),
                "freight": "a factory's or train's freight moved when an evidence file grew/changed (same rules as brain_graph)",
                "deliveries": ("couriers_log.jsonl (urgent/real-time routes) and buses_log.jsonl "
                               "(non-urgent — split from couriers 2026-08-22) each hold their own "
                               "routes' deliveries; filter rows by route field within each, and use "
                               "each entry's own `kind` field (courier|bus) to pick the right file"),
                "stations_live": "join station load on llm_usage.jsonl if desired; per-platform live logs do not exist",
                "honesty": ("freight_visible=false items and unresolved platforms are shown AS "
                            "unwatched/unresolved — never simulate activity. An empty `consumed_by` "
                            "or missing `destination_verified` means NOT YET TRACED, not 'nothing "
                            "happens' — draw those factories/couriers plainly, without a false edge."),
                "depot": ("platforms whose module belongs to no single passenger train carry "
                          "line='service' — render as NON-REVENUE depot/utility track (shared "
                          "infrastructure many trains pass through, e.g. memory writes), never "
                          "as a mystery 5th train"),
                "follow_a_thought": (
                    "HOW TO ANIMATE ONE COGNITIVE EVENT TRAVELING THE MAP (founder ask, "
                    "2026-08-21): a single idle-train tick is now a traceable path, not a guess -- "
                    "(1) a FACTORY's evidence file changes (e.g. room_state.json's 'weather' key); "
                    "(2) within the same tick, one of the idle train's PLATFORMS fires (a new row "
                    "in train_state_log.jsonl or idle_shadow.jsonl) -- its consumption is REAL per "
                    "that factory's consumed_by/consumption_verified field, not correlation-by-"
                    "coincidence; (3) a COURIER may deliver in the same window (couriers_log.jsonl "
                    "gains a 'route' row) -- its destination field says exactly where that lands "
                    "(idle train, or the competence ledger). Render one pulse traveling factory -> "
                    "(courier if any) -> the idle train's platform -> its train_state_log entry. "
                    "Because every edge here is a VERIFIED source-code binding, not a proximity "
                    "guess, the animation is honest even when two unrelated things happen to touch "
                    "files in the same second."
                ),
                "buffering": (
                    "if true real-time animation looks incoherent (bursty/out-of-order file "
                    "touches), a small server-side buffer -- hold ~10s of raw events, replay them "
                    "in strict timestamp order -- is a sound fix and entirely your own server's "
                    "concern; every evidence file already carries a real ts_key/mtime to order by."
                ),
            },
            "trains": trains, "factories": factories, "stations": _stations(counts),
            "platforms": platforms, "sidings": sidings, "couriers": couriers}, missing


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    g, missing = build()
    (OUT / "transit_map.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    vis = sum(1 for l in g["factories"] if l["freight_visible"])
    unres = sum(1 for pl in g["platforms"] if pl["station"] == "unresolved")
    consumed = sum(1 for f in g["factories"] if f["consumed_by"])
    print(f"transit_map.json: {len(g['trains'])} trains · {len(g['factories'])} factories "
          f"({vis} freight-visible, {consumed} with a verified consumer) · "
          f"{len(g['stations'])} stations · {len(g['platforms'])} platforms ({unres} unresolved) · "
          f"{len(g['sidings'])} sidings · {len(g['couriers'])} courier routes")
    for lid, f in missing:
        print(f"  (evidence not on disk, omitted: {lid} <- {f})")
    for pl in g["platforms"]:
        if pl["station"] == "unresolved":
            print(f"  (unresolved platform: {pl['id']} lane={pl['lane_expr'][:50]})")
