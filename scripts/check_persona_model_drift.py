"""
Nascence -- PERSONAS model-field drift check (2026-10-03, J-1673; the prevention proposal from F-2245/J-1669).

core/peers.py's PERSONAS entries each carry a "model" string and a "url" (a hub, identified by its port).
What a port actually serves is declared in exactly one place -- core/model_client.py's _MODEL_BY_BASE (keyed
by the port string; the routing source of truth). Nothing links the two, so re-seating a hub silently strands
every persona on it with a stale string. That has now bitten this file twice, and both times the only
detector was a human re-reading it during unrelated work:
  * 2026-08-20 -- Marcus/Smith were routed to the hot lane (:11433) with a "model" naming a different model.
    Real ollama honours the field, so either letter could have EVICTED the pinned Self model (the full story
    is in core/peers.py's own module docstring).
  * 2026-10-02 -- twain/shackleton still said "llama3.1:8b" after the 2026-08-20 shuffle re-seated :11439 to
    gemma4:12b (J-1669 / F-2240). Harmless only because the llama.cpp hubs ignore the field.

What the field does at runtime (core/peers.compose_letter -> core/model_client.call_node): it goes in as
model_override, so it is (1) the "model" of the request -- honoured by real ollama (:11433), never read by the
llama.cpp hubs (scripts/nascence_cpu_server.py's /api/chat answers with its own --alias) -- and (2) the model
written to telemetry's llm_calls / thought_station rows. Drift is therefore an eviction risk on :11433 and a
mislabelled telemetry row on every hub port.

THE CHECK. For each persona, take the port from its "url"; if that port is a key of _MODEL_BY_BASE, the
persona's "model" must equal _MODEL_BY_BASE[port] exactly. A port that is NOT in the map is SKIPPED, never
flagged -- there is nothing to compare against (e.g. a future ollama-routed persona whose model field is
load-bearing and legitimately names its own model). Skips are printed with their reason, not hidden.

Read-only: it imports the two tables (both modules are import-clean -- no file or network I/O at import time),
calls no model, opens no socket and writes nothing, so it is safe to run any time, Du up or down. It reports and
fixes nothing; the exit status is the only "gate", and only if someone wires it into one.

Exit status: 0 = every comparable persona agrees; 1 = drift or a malformed entry; 2 = inconclusive (the tables
could not be loaded, or nothing at all was compared -- never a false all-clear).

    python scripts/check_persona_model_drift.py

Verified by scripts/_test_persona_model_drift.py (synthetic cases, the real tables, and the actual J-1669 bug
re-introduced into the real source text).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable, Mapping, NamedTuple
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent

# The one REAL ollama instance left (core/model_client.call_node: "the one real ollama instance left (local
# :11433 ...) plus EVERY nascence_cpu_server.py hub"). It honours the request's model field; every other port in
# _MODEL_BY_BASE is a llama.cpp hub that ignores it. Used ONLY to word how serious a DRIFT line is -- never to
# decide whether it is one.
_OLLAMA_PORTS = frozenset({"11433"})
_NOTE_OLLAMA = "real ollama honours this field: the wrong model here can load/evict on the hot lane"
_NOTE_HUB = "the hub ignores the field when serving; the wrong label lands in telemetry"

_LABEL = {"ok": "ok", "drift": "DRIFT", "skip": "skip", "malformed": "BAD"}


class Result(NamedTuple):
    persona: str
    status: str                  # "ok" | "drift" | "skip" | "malformed"
    port: str | None
    persona_model: str | None    # what PERSONAS says
    mapped_model: str | None     # what _MODEL_BY_BASE says (None when the port is not in the map)
    note: str = ""


def port_of(url: Any) -> str | None:
    """The port of a persona "url" as the string key _MODEL_BY_BASE uses, or None when there is no usable port."""
    if not isinstance(url, str):
        return None
    try:
        port = urlsplit(url if "://" in url else "//" + url).port
    except ValueError:           # urlsplit raises on a non-numeric or out-of-range port
        return None
    return str(port) if port is not None else None


def find_drift(personas: Mapping[str, Any], model_by_base: Mapping[str, str]) -> list[Result]:
    """One Result per persona, in PERSONAS' own order. Pure: no I/O, so it is testable on synthetic tables."""
    out: list[Result] = []
    for name, entry in personas.items():
        if not isinstance(entry, Mapping):
            out.append(Result(name, "malformed", None, None, None, "entry is not a dict"))
            continue
        url, model = entry.get("url"), entry.get("model")
        missing = [k for k, v in (("url", url), ("model", model)) if not isinstance(v, str)]
        if missing:
            # compose_letter hard-indexes p["url"] / p["model"], so this would be a KeyError at letter time.
            out.append(Result(name, "malformed", None, model if isinstance(model, str) else None, None,
                              "missing or non-string " + " and ".join(repr(k) for k in missing)))
            continue
        port = port_of(url)
        if port is None:
            out.append(Result(name, "skip", None, model, None, "no explicit port in url -- not compared"))
        elif port not in model_by_base:
            out.append(Result(name, "skip", port, model, None, "port not in _MODEL_BY_BASE -- not compared"))
        elif model == model_by_base[port]:
            out.append(Result(name, "ok", port, model, model_by_base[port]))
        else:
            note = _NOTE_OLLAMA if port in _OLLAMA_PORTS else _NOTE_HUB
            out.append(Result(name, "drift", port, model, model_by_base[port], note))
    return out


def exit_code(results: list[Result]) -> int:
    if any(r.status in ("drift", "malformed") for r in results):
        return 1
    if not any(r.status == "ok" for r in results):
        return 2                 # nothing was actually compared: refuse to look like an all-clear
    return 0


def format_result(r: Result) -> str:
    head = f"  {_LABEL[r.status]:<6} {r.persona:<12} {(':' + r.port) if r.port else '-':<7} "
    if r.status == "ok":
        return head + str(r.persona_model)
    if r.status == "drift":
        return (head + f"PERSONAS says {r.persona_model!r} but _MODEL_BY_BASE[{r.port!r}] says "
                f"{r.mapped_model!r}  ({r.note})")
    return head + r.note


def summary(results: list[Result]) -> str:
    n = {s: sum(1 for r in results if r.status == s) for s in _LABEL}
    return (f"{len(results)} personas | {n['ok']} agree | {n['drift']} DRIFT | "
            f"{n['malformed']} malformed | {n['skip']} skipped")


def load_tables() -> tuple[Mapping[str, Any], Mapping[str, str]]:
    """The real tables, imported from the checkout this script lives in (so a worktree checks itself)."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from core.model_client import _MODEL_BY_BASE
    from core.peers import PERSONAS
    return PERSONAS, _MODEL_BY_BASE


def main(loader: Callable[[], tuple[Mapping[str, Any], Mapping[str, str]]] | None = None) -> int:
    print("PERSONAS model-field drift check -- core/peers.py PERSONAS vs core/model_client._MODEL_BY_BASE")
    try:
        personas, model_by_base = (loader or load_tables)()
        if not isinstance(personas, Mapping) or not isinstance(model_by_base, Mapping):
            raise TypeError("PERSONAS and _MODEL_BY_BASE must both be dicts")
    except Exception as exc:     # ImportError (no aiohttp), a SyntaxError in an edited file, a renamed table ...
        print(f"  INCONCLUSIVE: could not load the two tables: {exc!r}")
        return 2
    results = find_drift(personas, model_by_base)
    for r in results:
        print(format_result(r))
    print("  " + summary(results))
    code = exit_code(results)
    if code == 2:
        print("  INCONCLUSIVE: nothing was compared -- this is NOT an all-clear.")
    return code


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # cp1252 console vs a non-ASCII model string
    except Exception:
        pass
    raise SystemExit(main())
