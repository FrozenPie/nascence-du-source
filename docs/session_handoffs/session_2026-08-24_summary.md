# Session 2026-08-24 — SQLite Concurrency & CPU Tier Memory Management

**Date:** 2026-08-24  
**Status:** All tasks completed & verified. System RAM restored to baseline.

---

## 1. SQLite Database Lock Fix

### Issue Summary
Running `scripts/run_nascence.py` caused a startup crash during `init_db()`:

```text
File "C:\Nascence\scripts\run_nascence.py", line 462, in main
  init_db()
File "C:\Nascence\core\memory\store.py", line 187, in init_db
  _init_shadow_table(conn)
sqlite3.OperationalError: database is locked
```

### Root Cause
1. `_connect()` in `core/memory/store.py` connected with default SQLite 5.0s timeout and default rollback journal mode.
2. Concurrent queries from `hud/server.py` or background nodes locked `nascence.db` while `init_db()` executed DDL statements.

### Fix Applied
- **`core/memory/store.py` (`_connect()`):** Added `timeout=30.0`, `PRAGMA journal_mode=WAL;`, and `PRAGMA busy_timeout=30000;`.
- **`hud/server.py` (`query_db_safe()`):** Added `timeout=15.0`.
- **`nodes/subconscious_node.py`:** Added `timeout=15.0`.
- **Verification:** Verified `PRAGMA journal_mode` returns `wal`. Multi-threaded concurrent test passed with zero lock errors.

---

## 2. CPU Tier Memory Management & Lazy Loading

### Issue Summary
System RAM was over the memory limit:
- **Total System RAM:** 63.88 GB
- **Used RAM:** **59.78 GB (93.6% utilized)**
- **Free RAM:** **4.10 GB**

### Diagnosis & Root Cause
Inspected running processes via PowerShell / WMI:
- **PID 28788** (`yi:34b-v1.5` on Port 11442): **33.41 GB RAM**
- **PID 10580** (`gemma4:12b` on Port 11439): **8.36 GB RAM**
- **PID 32900** (`falcon3:7b` on Port 11440): **4.87 GB RAM**
- Total Python CPU servers held **46.64 GB RAM**.

### Actions & Fixes Applied
1. **Memory Recovery:** Terminated the heavy CPU hub processes. Recovered **~46.5 GB RAM**. Free system RAM rose to **~50.8 GB (Used RAM: 13.0 GB / 20.4%)**.
2. **Lazy Loading Configuration (`scripts/launch_servers.ps1`):**
   - Configured all 3 CPU hubs (Judge1 port `11439`, Judge2 port `11440`, Dreamer port `11442`) with `--lazy` and `--idle-unload 300`.
   - Hubs now bind ports instantly with 0 MB model RAM at startup, loading GGUF models into RAM only on demand when a call arrives and automatically unloading 5 minutes (300s) after idle.
3. **Dedicated Launcher (`scripts/launch_cpu_hubs.py`):** Created a Python helper script to manage CPU hub processes in background daemon mode.

---

## 3. Current System State for Next Session

| Component | Status | Details |
| :--- | :--- | :--- |
| **System RAM** | **13.0 GB Used / 50.8 GB Free** | Healthy baseline |
| **SQLite DB** | **WAL Mode Enabled** | `init_db()` lock-free |
| **GPU Model** | `qwen3.5:9b` (Port 11433) | Online & warmed on GPU |
| **CPU Tier** | Ports 11439, 11440, 11442 | Configured with `--lazy --idle-unload 300` |
