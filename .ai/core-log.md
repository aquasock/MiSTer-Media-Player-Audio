## 001 COMMIT D0 435650e 2026-08-16T03:57:29-07:00

#### Coming From:

D0 f865537

#### Purpose:

Record the approved D0 repository-bootstrap boundary for MiSTer-Media-Player-Audio as an independent codebase. Freeze the inherited executable/source baseline to MiSTer-Media-Player commit `bc37008c167809bec951715cd0a924478fd5ee36`, preserve the Audio project's own `.ai` control state, and prohibit Audio RTL or other executable changes until the inherited baseline is imported and qualified.

#### Outcome:

Exact GitHub `main` metadata commit `435650e564f370efa93ba6b883887ec4f20d1efd` (`(f865537) core-log.md update`) modifies only `.ai/core-log.md` and records the approved D0 boundary.

The selected upstream baseline is exact commit `bc37008c167809bec951715cd0a924478fd5ee36`, tree `6028d29da1fa55920fdab7dd391202c30285aadb`. Evidence review established that the synthesized RTL/QIP/QSF/SDC/tool-source state from the hardware-qualified v0.4.0 executable baseline `1370c28e3d34b1fd603c17130986bc336da29a32` through `bc37008` is unchanged; intervening differences are release/project-control/documentation material and `.gitattributes` handling.

`MediaPlayer_top_00.svh` at the selected baseline contains the five advisory Audio integration anchors `AUDIO_FORK_POINT[PCM_OUT]`, `AUDIO_FORK_POINT[STREAM_SPLIT]`, `AUDIO_FORK_POINT[CLOCK_RESET]`, `AUDIO_FORK_POINT[DDR_CLIENT]`, and `AUDIO_FORK_POINT[AV_SYNC]`. D0 explicitly preserves those anchors and makes no FLAC, PCM-output, clocking, transport, DDR, or other Audio implementation change.

The Audio repository remains independent from the main MiSTer-Media-Player development line. The main-project agent may periodically inspect this repository for future reintegration conflicts, but Audio does not automatically merge or rebase moving main-project changes.

#### Next Steps:

Import the complete non-`.ai` source tree from exact upstream commit `bc37008c167809bec951715cd0a924478fd5ee36`, verify inherited file identity and preservation of all Audio-fork anchors, then commit the bootstrap source state before performing the D0 clean Quartus and hardware qualification.

#### Files Modified:

- `.ai/core-log.md`

#### Status:

- [ ] Built — metadata-only planning record; no executable build required at this boundary
- [x] Passed — D0 bootstrap boundary approved and released for implementation

---
## 002 COMMIT D0 2e202fa 2026-08-16T03:58:31-07:00

#### Coming From:

D0 435650e

#### Purpose:

Establish the independent MiSTer-Media-Player-Audio source baseline from exact MiSTer-Media-Player commit `bc37008c167809bec951715cd0a924478fd5ee36` while retaining the Audio project's own `.ai` control directory and making no executable source changes.

#### Outcome:

Exact GitHub `main` bootstrap commit `2e202fab2402788bf548654c75e27ca432289723` (`D0 bootstrap from MiSTer-Media-Player bc37008`) imports the complete inherited non-`.ai` tree. Git-object verification against upstream tree `6028d29da1fa55920fdab7dd391202c30285aadb` shows every top-level inherited non-`.ai` blob/tree SHA is identical, including `.editorconfig`, `.github`, `.gitignore`, project/documentation files, `files.qip`, and the complete `docs`, `rtl`, `sys`, and `tools` subtrees. The Audio `.ai` tree intentionally remains project-specific.

`MediaPlayer_top_00.svh` remains exact blob `a4d085e655e0566d2694d0701cbbf9372763fd85`, identical to upstream `bc37008`, and preserves all five advisory `AUDIO_FORK_POINT[...]` anchors. No FLAC decoder, common PCM path, stream split, audio clock domain, DDR audio client, A/V synchronization logic, or other Audio implementation is present. D0 source identity is therefore accepted; clean build, resource/timing capture, and MiSTer hardware qualification remain outstanding.

The bootstrap also corrects `.ai/build_commands.md` to reference the MiSTer-Media-Player-Audio repository. This is project-control metadata and does not alter synthesized behavior.

#### Next Steps:

Pull current Audio `main`, delete Quartus-generated `db/`, `incremental_db/`, and `output_files/` state, run `quartus_sh --flow compile MediaPlayer`, then run `quartus_sta -t tools/phase1p_timing.tcl`. Validate the unchanged inherited core on the standard MiSTer target, push `2e202fa_build_logs.tar.gz` and any requested D0 evidence into `.ai/current_results/`, and record ALMs, registers, block-memory/RAM blocks, DSPs, PLLs, setup/hold/recovery/removal timing, focused decoder/video timing, and observed hardware behavior before beginning D1.

#### Files Modified:

- Complete inherited non-`.ai` source tree from MiSTer-Media-Player `bc37008`
- `.ai/build_commands.md`

#### Status:

- [ ] Built — clean inherited D0 Quartus build not yet reported
- [ ] Passed — D0 hardware/resource/timing baseline not yet accepted

---
