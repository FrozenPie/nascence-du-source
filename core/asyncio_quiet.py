"""
Nascence -- quiet one benign asyncio-on-Windows close trace (J-1930, 2026-10-07; F-2555 / F-1245).

THE NOISE. CPython's proactor transport (C:\\Python314\\Lib\\asyncio\\proactor_events.py,
_ProactorBasePipeTransport._call_connection_lost, 3.14.3 line 165) calls
``self._sock.shutdown(socket.SHUT_RDWR)`` unguarded inside a ``finally`` -- AFTER
``protocol.connection_lost()`` has already run. When the peer has already reset the connection
(WinError 10054, "An existing connection was forcibly closed by the remote host") that shutdown
raises, the loop's default exception handler logs a full traceback under the ``asyncio`` logger,
and the loop carries on. Nothing of ours is in the stack; no work is dropped; what the raise skips
(sock.close(), server._detach()) is reclaimed at GC because Server._clients is a WeakSet
(base_events.py:283). F-2555 counted it: 423 traces in data/nascence.log since 2026-08-20 at 1-13
per day, and 28-77% of ALL lines in data/logs/cpu_tier_{11439,11440,11442}.log. It alarms every
human reading the console and buries real errors in the CPU-tier logs.

THE FIX. A loop exception handler that recognises EXACTLY this case -- the exception is a
ConnectionResetError carrying winerror 10054 AND the failing handle is _call_connection_lost -- and
downgrades it to a single DEBUG line. Every other context goes to loop.default_exception_handler()
unchanged, so nothing else is swallowed. Deliberately NOT done: switching the loop policy to the
selector loop (aiohttp / uvicorn behaviour would change) or patching the transport class.

Installed by scripts/run_nascence.py (Du's own entry point, inside main() on the running loop) and,
as a self-contained inline copy (that script is deliberately standalone -- it is also deployed on
Ramses, see its own header), by scripts/nascence_cpu_server.py in its uvicorn startup hook.
"""
from __future__ import annotations

import asyncio
import logging

WINERROR_CONNRESET = 10054
_HANDLE_MARK = "_call_connection_lost"

# Count of quieted traces since install -- observable from a REPL / test, never written anywhere.
quieted = 0


def is_benign_connection_reset(context: dict) -> bool:
    """True only for the F-2555 shape: ConnectionResetError/10054 raised from the transport's own
    _call_connection_lost callback. Anything else -> False (caller must delegate to the default)."""
    exc = context.get("exception")
    if not isinstance(exc, ConnectionResetError):
        return False
    if getattr(exc, "winerror", None) != WINERROR_CONNRESET:
        return False
    handle = context.get("handle")
    where = repr(handle) if handle is not None else str(context.get("message", ""))
    return _HANDLE_MARK in where


def install_quiet_connection_reset(loop: "asyncio.AbstractEventLoop | None" = None,
                                   logger: "logging.Logger | None" = None) -> None:
    """Install the handler on ``loop`` (default: the running loop). Idempotent; wraps any handler
    already set (delegates to it instead of the default) so it composes with other installs."""
    if loop is None:
        loop = asyncio.get_running_loop()
    log = logger or logging.getLogger("asyncio")
    previous = loop.get_exception_handler()
    if getattr(previous, "_nascence_quiet_reset", False):
        return

    def _handler(lp, context):
        global quieted
        if is_benign_connection_reset(context):
            quieted += 1
            log.debug("[asyncio-quiet] peer reset during transport close (WinError 10054 in "
                      "_call_connection_lost) -- benign, suppressed; total %d", quieted)
            return
        if previous is not None:
            previous(lp, context)
        else:
            lp.default_exception_handler(context)

    _handler._nascence_quiet_reset = True   # type: ignore[attr-defined]
    loop.set_exception_handler(_handler)
