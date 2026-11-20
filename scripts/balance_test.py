"""
In-vitro test for the reading-remediation balance gate (2026-06-15). No DB — mocks shares() to test the
hysteresis latch: the sprint starts when imbalanced, ends only when BOTH axes reach ~50%, and doesn't flap.

Run:  python scripts/balance_test.py
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import balance

PASS, FAIL = "✅", "❌"
ok_all = True
def check(name, cond):
    global ok_all; ok_all = ok_all and cond
    print(f"  {PASS if cond else FAIL} {name}")

def set_shares(r, l):
    balance.shares = lambda: {"reality_share": r, "light_share": l, "world": 0, "self": 0, "light": 0, "shadow": 0}

print(f"\nthresholds: EXIT_AT={balance.EXIT_AT}  REENTER_AT={balance.REENTER_AT}")

# start imbalanced (today's ~16%/23%) -> sprinting
balance._sprinting = None
set_shares(0.16, 0.23)
check("imbalanced (16%/23%) → sprint ON", balance.in_remediation() is True)

# one axis crosses 50 but the other still low -> STILL sprinting (don't stop early)
set_shares(0.55, 0.23)
check("reality balanced but light low → sprint STAYS on", balance.in_remediation() is True)

# both reach exit -> sprint ENDS
set_shares(0.48, 0.49)
check("both ≥ EXIT_AT → sprint ENDS", balance.in_remediation() is False)

# small dip into the hysteresis band (between REENTER and EXIT) -> stays OFF (no flap)
set_shares(0.44, 0.46)
check("dip into hysteresis band → stays OFF (no flapping)", balance.in_remediation() is False)

# fall below REENTER -> sprint RE-STARTS
set_shares(0.40, 0.46)
check("falls below REENTER_AT → sprint RE-STARTS", balance.in_remediation() is True)

# climbs back into band -> stays ON (hysteresis the other way)
set_shares(0.45, 0.46)
check("climbs into band from below → stays ON (no flapping)", balance.in_remediation() is True)

print(f"\n{'='*60}\n{'ALL PASS — the sprint has a real finish line' if ok_all else 'FAILURES ABOVE'}\n{'='*60}")
sys.exit(0 if ok_all else 1)
