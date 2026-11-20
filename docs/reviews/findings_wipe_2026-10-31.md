# Findings ledger wipe and restore, 2026-10-31 / 11-01

At 2026-10-31T18:21:39Z `docs/findings.jsonl` was overwritten by a lost-update race in `findings_log.py` (no lock; `load()` returned empty when a read failed mid-replace). It restarted at F-0001 with 3,465 findings lost from the live file. Restored from git HEAD (F-0001 to F-3423), the event log, transcripts and scratchpad files (F-3424 to F-3465), and the post-wipe findings renumbered below. Backups: `docs/archive/findings_wipe_2026-10-31/`.

## Post-wipe id map (old id used in notes, briefings and agent reports -> id in the ledger now)

| was | now |
|---|---|
| F-0001 | F-3466 |
| F-0002 | F-3467 |
| F-0003 | F-3468 |
| F-0004 | F-3469 |
| F-0005 | F-3470 |
| F-0006 | F-3471 |
| F-0007 | F-3472 |
| F-0008 | F-3473 |
| F-0009 | F-3474 |
| F-0010 | F-3475 |
| F-0011 | F-3476 |
| F-0012 | F-3477 |
| F-0013 | F-3478 |
| F-0014 | F-3479 |
| F-0015 | F-3480 |
| F-0016 | F-3481 |
| F-0017 | F-3482 |
| F-0018 | F-3483 |
| F-0019 | F-3484 |
| F-0020 | F-3485 |
| F-0021 | F-3486 |
| F-0022 | F-3487 |
| F-0023 | F-3488 |
| F-0024 | F-3489 |
| F-0025 | F-3490 |
| F-0026 | F-3491 |
| F-0027 | F-3492 |
| F-0028 | F-3493 |
| F-0029 | F-3494 |
| F-0030 | F-3495 |
| F-0031 | F-3496 |
| F-0032 | F-3497 |
| F-0033 | F-3498 |
| F-0034 | F-3499 |
| F-0035 | F-3500 |
| F-0036 | F-3501 |
| F-0037 | F-3502 |
| F-0038 | F-3503 |
| F-0039 | F-3504 |
| F-0040 | F-3505 |
| F-0041 | F-3506 |
| F-0042 | F-3507 |
| F-0043 | F-3508 |
| F-0044 | F-3509 |
| F-0045 | F-3510 |
| F-0046 | F-3511 |
| F-0047 | F-3512 |
| F-0048 | F-3513 |
| F-0049 | F-3514 |
| F-0050 | F-3515 |
| F-0051 | F-3516 |
| F-0052 | F-3517 |
| F-0053 | F-3518 |
| F-0054 | F-3519 |
| F-0055 | F-3520 |
| F-0056 | F-3521 |
| F-0057 | F-3522 |
| F-0058 | F-3523 |
| F-0059 | F-3524 |
| F-0060 | F-3525 |
| F-0061 | F-3526 |
| F-0062 | F-3527 |
| F-0063 | F-3528 |
| F-0064 | F-3529 |
| F-0065 | F-3530 |
| F-0066 | F-3531 |
| F-0067 | F-3532 |
| F-0068 | F-3533 |
| F-0069 | F-3534 |
