# Watchers parked — 2026-08-04

These three scripts automate exam-batch pickup and (for arm_watcher)
flip ARMED=True citing an owner signature dated 2026-08-02. That
signature predates the 2026-08-04 reset (docs/reset_2026-08-04.md),
which established that re-arming is a FRESH explicit owner act. The old
exam batch log also still contained a stale BATCH_COMPLETE line, so the
trigger condition was half-satisfied by leftovers.

Re-enable condition: a new signature block dated after 2026-08-04 in the
relevant proposals doc, then `git mv` the script back and re-verify its
trigger log is current. Until then they stay here, inert.
