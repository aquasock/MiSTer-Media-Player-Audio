## 001 PLAN D0 f865537 2026-08-16T03:56:00-07:00

#### Coming From:

new Audio project control state at `f865537f357f88b0e789408bcd59151ffc4b22b9`

#### Purpose:

Begin D0 repository bootstrap for MiSTer-Media-Player-Audio as an independent codebase. The inherited executable/source baseline is frozen to MiSTer-Media-Player commit `bc37008c167809bec951715cd0a924478fd5ee36`. Audio development will proceed independently from the main project's moving development branch. The main-project agent may periodically inspect this repository for reintegration conflicts, but Audio does not automatically merge or rebase main-project changes.

#### Evidence / Approved Boundary:

- Selected upstream baseline: `bc37008c167809bec951715cd0a924478fd5ee36` (`added ai folder empty dirs`).
- Upstream tree at that commit: `6028d29da1fa55920fdab7dd391202c30285aadb`.
- Comparison from the hardware-qualified v0.4.0 executable baseline `1370c28e3d34b1fd603c17130986bc336da29a32` through `bc37008` shows no synthesized RTL/QIP/QSF/SDC/tool-source changes; intervening changes are release/project-control/documentation material and `.gitattributes` handling.
- `MediaPlayer_top_00.svh` at `bc37008` contains the advisory Audio integration anchors `AUDIO_FORK_POINT[PCM_OUT]`, `AUDIO_FORK_POINT[STREAM_SPLIT]`, `AUDIO_FORK_POINT[CLOCK_RESET]`, `AUDIO_FORK_POINT[DDR_CLIENT]`, and `AUDIO_FORK_POINT[AV_SYNC]`.
- D0 must preserve the inherited executable source unchanged. No FLAC, PCM-output, clocking, transport, DDR, or other Audio RTL is authorized in D0.
- Preserve this repository's Audio-specific `.ai` control state rather than replacing it with the main project's `.ai` history.

#### Outcome:

D0 planning/evidence review is complete and approved. The Audio repository is an independent GitHub repository (`fork: false`) and its current branch history does not contain the upstream objects. GitHub's Git Data API rejects direct cross-repository use of the upstream blob/tree/commit SHAs, so the exact source import must be performed through a local Git checkout/repository transfer rather than by synthesizing a partial source tree through the connector.

The required source state after import is: every inherited non-`.ai` path matches `bc37008` exactly, while `.ai/` remains the Audio project's control directory.

#### Next Steps:

1. Import the complete non-`.ai` source tree from exact upstream commit `bc37008c167809bec951715cd0a924478fd5ee36` into this repository without executable edits.
2. Verify inherited file identity against the upstream commit and preserve all `AUDIO_FORK_POINT[...]` comments.
3. Commit the bootstrap source state.
4. Have the user pull/clone the resulting Audio repository and perform a clean Quartus build using `quartus_sh --flow compile MediaPlayer` followed by `quartus_sta -t tools/phase1p_timing.tcl`.
5. Record D0 ALMs, registers, RAM/block-memory, DSPs, PLLs, timing, and hardware behavior from the clean inherited build before any Audio implementation begins.

#### Files Modified:

- `.ai/core-log.md`

#### Status:

- [x] D0 evidence review complete
- [x] D0 bootstrap boundary approved
- [ ] Exact `bc37008` source tree imported
- [ ] Clean inherited Quartus build completed
- [ ] D0 hardware/resource/timing baseline accepted

---
