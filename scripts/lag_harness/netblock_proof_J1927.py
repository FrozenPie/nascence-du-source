"""scripts/lag_harness/netblock_proof_J1927.py (J-1927): prove the _prelude audit net-block before any timing run.
Once _NET['block'] is set after the event loop exists, (1) a plain socket.connect raises PermissionError from the
audit hook and (2) asyncio's open_connection (Windows IocpProactor.connect, which raises NO socket.connect audit
event) raises PermissionError from the monkeypatched connect. Unblocked, the same asyncio connect to a closed local
port reaches the OS (ConnectionRefusedError / OSError) -- the hub ports are NEVER touched here."""
import os, sys, asyncio, socket
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _prelude
from _prelude import _NET

CLOSED = ("127.0.0.1", 9)        # discard port: nothing listens (checked by the controller with netstat)

async def try_async():
    try:
        await asyncio.wait_for(asyncio.open_connection(*CLOSED), 3)
        return "CONNECTED?!"
    except Exception as e:
        return type(e).__name__ + ": " + str(e)[:80]

def try_sync():
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(CLOSED); return "CONNECTED?!"
    except Exception as e:
        return type(e).__name__ + ": " + str(e)[:80]
    finally:
        s.close()

loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
_NET["block"] = True
a_blocked = loop.run_until_complete(try_async())
s_blocked = try_sync()
_NET["block"] = False
a_open = loop.run_until_complete(try_async())
loop.close()
print("blocked  asyncio:", a_blocked)
print("blocked  socket :", s_blocked)
print("unblocked asyncio:", a_open)
ok = a_blocked.startswith("PermissionError") and s_blocked.startswith("PermissionError") and not a_open.startswith("PermissionError")
print("NETBLOCK PROOF:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
