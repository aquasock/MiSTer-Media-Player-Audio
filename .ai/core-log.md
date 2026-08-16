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
## 003 COMMIT D0 40ec769 2026-08-16T04:37:57-07:00

#### Coming From:

D0 2e202fa

#### Purpose:

Accept the user-designated `40ec769_build_logs.tar.gz` package as the D0 clean-build evidence for the independent Audio baseline, despite the build being taken several repository commits after the original `2e202fa` bootstrap, and determine whether those intervening commits invalidate the D0 resource/timing denominator.

#### Outcome:

The user explicitly designated `.ai/current_results/40ec769_build_logs.tar.gz` as the D0 build-result package and stated that the intervening commits do not affect the build data. GitHub reports the package as blob `8aaa5f983606261480476a22df0ffadd9f4d362f`, size 1,196,547 bytes. The copies currently named `1b46fc6_build_logs.tar.gz`, `77e6399_build_logs.tar.gz`, and `40ec769_build_logs.tar.gz` are byte-identical because all three resolve to that same blob.

Comparison from bootstrap commit `2e202fab2402788bf548654c75e27ca432289723` to build boundary `40ec769b6be147fbaba8f9ecef1d6810ef4e127b` shows no RTL, QIP, SDC, source-list, decoder, DDR, presentation, clocking, or Audio implementation changes. The only synthesized-project file touched is `MediaPlayer.qsf`, where commit `77e6399aac44e9ffc8348f21b9f9522ee5163bd1` changes only `LAST_QUARTUS_VERSION` from `17.0.0 Lite Edition` to `17.0.2 Lite Edition`, matching the user's actual Quartus Prime 17.0.2 Lite build environment. The inherited design therefore remains the D0 executable baseline.

For D0 accounting, the accepted baseline resource/timing shape is the hardware-qualified unchanged v0.4.0 executable state: Quartus Prime 17.0.2 Build 602 targeting Cyclone V `5CSEBA6U23I7`; 31,782 / 41,910 ALMs (76%), 43,812 registers, 461,345 / 5,662,720 block-memory bits (8%) in 73 / 553 RAM blocks (13%), 68 / 112 DSPs (61%), and 3 / 6 PLLs (50%). Setup endpoint TNS is zero; global worst setup is +0.167 ns; decoder same-clock worst setup is +1.311 ns with 0/100 violations; video same-clock worst setup is +6.987 ns with 0/80 violations; hold +0.248 ns; recovery +4.117 ns; removal +0.704 ns; minimum pulse-width +0.462 ns. The standing structural warning counts are `no_clock=3094`, `multiple_clock=86`, `virtual_clock=1`, `no_input_delay=14`, `no_output_delay=129`, with zero loops and zero latches.

The GitHub connector can verify the binary package identity and repository/source equivalence but does not decode the contents of this 1.2 MB tar.gz archive. The numerical baseline above is therefore accepted under the user's instruction to use `40ec769_build_logs.tar.gz` together with the previously qualified identical executable source evidence, rather than being represented as a fresh connector-side extraction of the archive.

Hardware validation is now explicit rather than inherited: on 2026-08-16 the user reports that all requested D0 MiSTer hardware tests pass on the standard target, with no reported regression, stall, or crash. Together with the source-identity and build evidence above, D0 is closed as the accepted zero-change denominator for subsequent Audio resource/timing comparisons.

The accepted `40ec769_build_logs.tar.gz` blob was archived under `.ai/archived_results/`, and the three byte-identical active copies were removed from `.ai/current_results/` in commit `14668e2d6063d868be0fcbe99214c1ee315d091a` (`(40ec769) archiving results`).

#### Next Steps:

Begin D1 with the deterministic FLAC corpus/generator/manifest boundary. Preserve D0 as the denominator for all later resource accounting, and continue treating main-project compatibility reviews as observation/reintegration guidance rather than an automatic merge or rebase requirement.

#### Files Modified:

- `.ai/core-log.md`

#### Status:

- [x] Built — `40ec769_build_logs.tar.gz` accepted as D0 build evidence; intervening source changes do not alter the executable baseline
- [x] Passed — all requested D0 MiSTer hardware tests reported passing; D0 baseline accepted and closed

---
