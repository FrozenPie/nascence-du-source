"""
J-1930 (2026-10-07, F-2555): tests for core/asyncio_quiet.py and the inline copy in
scripts/nascence_cpu_server.py -- the loop exception handler that downgrades the benign
'_ProactorBasePipeTransport._call_connection_lost() ... ConnectionResetError [WinError 10054]' trace.

Run:  python scripts/test_asyncio_quiet.py        (plain asserts; also pytest-collectable)

What is exercised, on the REAL proactor loop with REAL transports:
  1. unit: is_benign_connection_reset() accepts exactly the F-2555 shape and rejects neighbours.
  2. positive control: a server-side transport whose socket's shutdown() raises
     ConnectionResetError(10054) -- the exact raise site proactor_events.py:165 -- produces the real
     'Exception in callback _ProactorBasePipeTransport._call_connection_lost()' trace through the
     real Handle._run -> loop.call_exception_handler path when NO handler is installed.
  3. the fix: same scenario with the handler installed -> zero traces, one DEBUG line, counter +1.
  4. negative controls, handler installed: an unrelated callback exception (ZeroDivisionError) and a
     ConnectionResetError/10054 raised from a callback that is NOT _call_connection_lost both still
     reach the default handler and are logged in full.
  5. the SO_LINGER-0 peer reset the briefing asked for is also driven against the server (the client
     RSTs every connection). NOTE: on this box (Python 3.14.3, Windows 11) the OS-level race that makes
     shutdown() itself raise did not reproduce on demand in ~500 attempts across six shapes (see F-2555's
     follow-up finding), so the deterministic reproduction above injects the raise at the exact CPython
     line instead of waiting for the kernel to lose the race.
  6. the nascence_cpu_server.py inline copy is run through the same scenario (skipped if its heavy
     imports -- fastapi / llama_cpp -- are unavailable).

Writes nothing under data/.
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import socket
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core  # noqa: E402  (import core BEFORE anything that could hijack sys.path)
assert Path(core.__file__).resolve().is_relative_to(ROOT), f"core resolved outside this tree: {core.__file__}"

from core import asyncio_quiet  # noqa: E402

TRACE_MARK = "Exception in callback _ProactorBasePipeTransport._call_connection_lost()"


def _reset_error() -> ConnectionResetError:
    # OSError(errno, strerror, filename, winerror): the 4th positional sets .winerror on Windows.
    return ConnectionResetError(10054, "An existing connection was forcibly closed by the remote host",
                                None, 10054)


class _RaisingShutdownSocket:
    """Delegates everything to the real socket except shutdown(), which raises the 10054 reset --
    i.e. the state the kernel leaves the socket in when the peer's RST wins the race."""
    def __init__(self, real):
        object.__setattr__(self, "_real", real)

    def shutdown(self, how):
        raise _reset_error()

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)


class _Capture:
    def __init__(self, level=logging.DEBUG):
        self.buf = io.StringIO()
        self.h = logging.StreamHandler(self.buf)
        self.h.setLevel(logging.DEBUG)
        self.log = logging.getLogger("asyncio")
        self.prev_level = self.log.level
        self.level = level

    def __enter__(self):
        self.log.addHandler(self.h)
        self.log.setLevel(self.level)
        return self

    def __exit__(self, *a):
        self.log.removeHandler(self.h)
        self.log.setLevel(self.prev_level)

    @property
    def text(self) -> str:
        return self.buf.getvalue()


def _rst_close(s: socket.socket) -> None:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    s.close()


async def _drive(n_conns: int, inject: bool, real_socks: list) -> None:
    """Server whose transports (optionally) get the raising-shutdown socket; client RSTs each conn."""
    async def handle(reader, writer):
        tr = writer.transport
        if inject:
            real_socks.append(tr._sock)
            tr._sock = _RaisingShutdownSocket(tr._sock)
        try:
            await reader.read(100)
        except Exception:
            pass
        writer.close()

    srv = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = srv.sockets[0].getsockname()[1]
    for _ in range(n_conns):
        s = socket.create_connection(("127.0.0.1", port))
        s.send(b"GET /api/tags HTTP/1.1\r\n\r\n")
        await asyncio.sleep(0.01)
        _rst_close(s)                      # SO_LINGER 0 -> RST, as the briefing specifies
        await asyncio.sleep(0.03)
    await asyncio.sleep(0.2)
    srv.close()
    # Deliberately NOT `await srv.wait_closed()`: when shutdown() raises inside _call_connection_lost
    # the transport never reaches server._detach(), and Server._wakeup() is only ever called from
    # _detach()/close() -- so wait_closed() blocks for good (first run of this test hung on exactly
    # that; recorded in the J-1930 finding as a second-order effect F-2555's GC argument does not cover).
    await asyncio.sleep(0.05)


def _cleanup(real_socks: list) -> None:
    for s in real_socks:
        try:
            s.close()
        except Exception:
            pass
    real_socks.clear()


# ---------------------------------------------------------------- 1. unit


def test_predicate_shape():
    loop = asyncio.new_event_loop()
    try:
        class _T:
            def _call_connection_lost(self, exc): pass
        handle = asyncio.Handle(_T()._call_connection_lost, (None,), loop)   # repr names the method
        ok = {"message": "Exception in callback", "exception": _reset_error(), "handle": handle}
        assert asyncio_quiet.is_benign_connection_reset(ok)
        # message-only fallback (no handle object)
        assert asyncio_quiet.is_benign_connection_reset(
            {"message": "Exception in callback _ProactorBasePipeTransport._call_connection_lost()",
             "exception": _reset_error()})
        # neighbours that must NOT match
        other_err = ConnectionResetError(10053, "aborted", None, 10053)
        assert not asyncio_quiet.is_benign_connection_reset({**ok, "exception": other_err})
        # (note: OSError(..., winerror=10054) is itself remapped to ConnectionResetError by CPython, so the
        # errno-free OSError below is the right 'same family, wrong error' neighbour)
        assert not asyncio_quiet.is_benign_connection_reset({**ok, "exception": OSError(22, "invalid argument")})
        assert not asyncio_quiet.is_benign_connection_reset({**ok, "exception": ZeroDivisionError()})
        assert not asyncio_quiet.is_benign_connection_reset({**ok, "exception": None})
        unrelated = asyncio.Handle(lambda: None, (), loop)
        assert not asyncio_quiet.is_benign_connection_reset({**ok, "handle": unrelated})
        assert not asyncio_quiet.is_benign_connection_reset({"message": "Task exception", "exception": _reset_error()})
    finally:
        loop.close()


# ---------------------------------------------------------------- 2. positive control (no handler)


def test_positive_control_trace_without_handler():
    real = []

    async def main():
        with _Capture(logging.ERROR) as cap:
            await _drive(5, inject=True, real_socks=real)
            return cap.text

    text = asyncio.run(main())
    _cleanup(real)
    n = text.count(TRACE_MARK)
    assert n == 5, f"expected 5 real traces from the uninstalled loop, got {n}:\n{text[:800]}"
    assert "proactor_events.py" in text and "_call_connection_lost" in text and "10054" in text


# ---------------------------------------------------------------- 3. the fix


def _run_with_handler(installer, counter_getter):
    real = []

    async def main():
        loop = asyncio.get_running_loop()
        before = counter_getter()
        installer(loop)
        installer(loop)                     # idempotent: second install must not stack
        with _Capture(logging.DEBUG) as cap:
            await _drive(7, inject=True, real_socks=real)
            text = cap.text
        return text, counter_getter() - before

    text, delta = asyncio.run(main())
    _cleanup(real)
    assert text.count(TRACE_MARK) == 0, f"trace still logged with handler installed:\n{text[:800]}"
    assert "proactor_events.py" not in text
    assert delta == 7, f"counter should have advanced by 7, got {delta}"
    assert text.count("[asyncio-quiet]") == 7, text[:800]


def test_fix_core_handler():
    _run_with_handler(lambda loop: asyncio_quiet.install_quiet_connection_reset(loop),
                      lambda: asyncio_quiet.quieted)


# ---------------------------------------------------------------- 4. negative controls


def _negative_controls(installer):
    async def main():
        loop = asyncio.get_running_loop()
        installer(loop)
        with _Capture(logging.ERROR) as cap:
            loop.call_soon(lambda: 1 / 0)
            def _unrelated_reset():
                raise _reset_error()
            loop.call_soon(_unrelated_reset)
            await asyncio.sleep(0.05)
            return cap.text

    text = asyncio.run(main())
    assert "ZeroDivisionError" in text, text
    assert text.count("Exception in callback") == 2, text
    assert "WinError 10054" in text, "a 10054 from a NON-_call_connection_lost callback must still log"
    assert "_unrelated_reset" in text, text
    assert TRACE_MARK not in text


def test_negative_controls_core():
    _negative_controls(lambda loop: asyncio_quiet.install_quiet_connection_reset(loop))


# ---------------------------------------------------------------- 5. plain SO_LINGER-0 RST, no injection


def test_plain_rst_run_is_clean_either_way():
    """The real kernel race (shutdown itself raising) did not reproduce on demand on this box; this
    only asserts the handler changes nothing about an ordinary RST'd connection's handling."""
    real = []

    async def main():
        asyncio_quiet.install_quiet_connection_reset(asyncio.get_running_loop())
        with _Capture(logging.ERROR) as cap:
            await _drive(10, inject=False, real_socks=real)
            return cap.text

    text = asyncio.run(main())
    assert "Exception in callback" not in text, text[:800]


# ---------------------------------------------------------------- 6. the cpu-server inline copy


def test_cpu_server_inline_copy():
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import nascence_cpu_server as cpu  # heavy: fastapi + llama_cpp
    except Exception as exc:                 # pragma: no cover
        print(f"  (skipped: nascence_cpu_server import failed: {exc})")
        return
    _run_with_handler(cpu._install_quiet_connection_reset, lambda: cpu._quieted_resets)
    _negative_controls(cpu._install_quiet_connection_reset)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    tests = [test_predicate_shape, test_positive_control_trace_without_handler, test_fix_core_handler,
             test_negative_controls_core, test_plain_rst_run_is_clean_either_way, test_cpu_server_inline_copy]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}", flush=True)
        except Exception as exc:
            failed += 1
            print(f"FAIL {t.__name__}: {type(exc).__name__}: {exc}", flush=True)
    print(f"{len(tests) - failed}/{len(tests)} passed", flush=True)
    sys.exit(1 if failed else 0)
