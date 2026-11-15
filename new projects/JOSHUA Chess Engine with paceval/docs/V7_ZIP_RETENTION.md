# JOSHUA V7: ZIP Compression and Bounded Continuous Self-Play Logs

## Objective

Indefinite chess self-play must not accumulate an unlimited history of uncompressed traces. JOSHUA V7 adds a C++17 ZIP32/DEFLATE archive writer and rotates retained finished-game archives whenever the total configured disk allocation budget is exceeded. The default retention budget is **25,000,000 bytes (25 MB, decimal)**. This is a bounded *retained-logs* policy, not a limit on memory, the paceval runtime itself, other files on the disk or transient archive-creation overhead.

## Files written by the original C++ application

After a game child exits and the existing independent game analysis finishes, the supervisor writes `learning_report.md`, `learning_event.jsonl`, `analysis_queue.csv`, `games_index.csv` and the exact original engine traces into the game directory. It then streams every regular file into `sessions/archives/game_000001.zip`, using raw DEFLATE and CRC32. Internal paths are relative. The ZIP is first written with a `.part` suffix. When completed, the file is atomically renamed to `.zip`. **Only then** is the source game directory removed. ZIP creation or deletion errors stop the manager rather than silently discarding a game.

The archive includes the exact source `selfplay_timeline.csv`, `root_move_rankings.csv`, `run_evidence.json`, `game_uci.txt`, optional `game.pgn`, the human-readable learning report, the structured review queue and, in long-graph mode, every `ply_NNN` subfolder. Unfinished or failed games are archived with `interrupted.txt` or `incomplete_game.txt` and must **not** be interpreted as completed matches.

For convenience, the top-level `sessions/learning_log.md`, `learning_events.jsonl`, `analysis_queue.csv` and `games_index.csv` now contain **only the latest completed game**. They do not grow by appending data across all sessions. The complete historical records are inside the retained game ZIP files. `sessions/manager_errors.log` is truncated to a small rolling tail, and `sessions/retention_status.json` is overwritten after every archive.

## Rotation rule

The code enumerates only supervisor-managed ZIPs matching `game_*.zip` inside `sessions/archives`. They are sorted by increasing game number. It calculates the maximum of file length and physical allocated blocks (`st_blocks * 512`) to account for filesystem allocation of small files. The same accounting is applied to the rolling summary files. Archives are deleted oldest first until the retained managed disk allocation fits the budget. Unrelated user ZIPs are **never** deleted by the manager.

If a single new archive cannot fit, it too is deleted after rotation. The latest small summary remains available, and `ARCHIVE_COMMITTED ... latest_retained=no` explicitly reports that no full ZIP was retained for the oversized game. This is an intentional consequence of an unconditional disk ceiling; a discarded archive cannot be recovered from the local session after removal. Copy important archives to a different drive **before** the quota prunes them.

A persistent `sessions/next_game_id.txt` is updated before launching the next game, so restarts cannot silently reuse game numbers merely because an old ZIP was deleted. Existing uncompressed V6 game folders are archived at the beginning of the first V7 run, and prior aggregate session logs are migrated to `game_000000.zip`. This migration is itself subject to the quota; back up earlier results beforehand if they must be retained permanently.

## Runtime safety and limitations

By default, the supervisor monitors the active (uncompressed) game directory for a separate **25,000,000-byte** cap (`--max-active-bytes`). If the cap is exceeded, the engine child is terminated, the incomplete game is archived where possible and the manager stops. This prevents runaway trace creation in ordinary cases, but a child may briefly exceed the cap between polling checks. The archive is created while original raw files still exist, so temporary disk consumption can exceed 25 MB. The physical directory blocks, user-controlled shell redirection and other system files are not included in the retained-log budget. Operating-system crashes, disk exhaustion and filesystem errors cannot be made impossible by this application.

The quota can be changed for controlled tests via `--log-limit-bytes N`. The default always remains 25,000,000. The maximum active uncompressed game output can be changed separately via `--max-active-bytes N`. For a graph-intensive longgraph game requiring more than 25 MB of intermediate output, the active cap must be raised deliberately, with enough free disk space. Any archive greater than the retention budget will still be removed.

Do not set either limit below 4,096 bytes. Very small artificial budgets are useful for retention tests but may be too small even for the latest summary or filesystem block overhead.

## Run and share logs

```bash
./scripts/run_continuous.sh --mode alphabeta --model 4 --depth 2 \
  --quiescence 2 --plies 160 --max-games 0

# Optional export of every retained ZIP and the latest index for review:
python3 scripts/export_retained_logs.py --session sessions \
  --output JOSHUA_Logs_For_Analysis.zip
```

Give the generated export ZIP to a future ChatGPT conversation for analysis. Deleted older games are deliberately absent from the export. No automatic modification of Joshua's search logic or learned weights is performed during games.

## Validation evidence

`src/zip_log_archive.cpp` is the original C++ ZIP writer. `scripts/test_v7_zip_retention.py` checks archive integrity using the independent Python `zipfile` implementation, including CRC and decompression, retention with multiple games, monotonic numbering across restart, oversized archives and incomplete-game archiving after active-limit termination. `scripts/test_v6_supervisor.py` checks restart, failed engines and signal handling against historical fixtures. These tests are **offline process and file-format tests**, not fresh original paceval mathematical execution.
