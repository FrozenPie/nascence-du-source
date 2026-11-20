---
name: reference-windows-vss-recovery
description: "After a crash wipes Du's data/ files, Windows shadow copies are the recovery source; readable without admin via the GLOBALROOT path."
metadata:
  node_type: memory
  type: reference
  originSessionId: 0a53de93-3665-4bcd-8553-36fcc9cee2cc
  modified: 2026-11-19T22:55:10.475Z
---

This machine keeps daily Windows Volume Shadow Copies of C: (seen 2026-11-20: one per evening plus two at 04:51). `vssadmin list shadows` needs an admin terminal (ask the founder to run it), but the copies themselves are readable from a normal process with plain Python `open()` at `\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN\Nascence\data\<file>`.

A file being written at the moment of the snapshot can be all NUL inside that shadow; try the next older shadow for those. Copy out to a side folder, verify with `json.loads`, and only restore with Du stopped. `wmic` is absent on this Windows build; use `Get-CimInstance Win32_Process`.

Worked example and script: `C:\Nascence\data\_crash_recovery_20261120\restore.py`, findings F-5128 / F-5129.
