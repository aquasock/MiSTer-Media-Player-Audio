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
## 004 COMMIT D1 2ca7be5 2026-08-16T05:07:23-07:00

#### Coming From:

D0 40ec769

#### Purpose:

Establish the deterministic FLAC corpus/generator/manifest infrastructure required before decoder RTL, with pinned reference tools, stable case identities, fail-closed reproducibility checks, deterministic malformed/unsupported cases, and deterministic compressed-input/PCM-output backpressure profiles while leaving all FPGA implementation source unchanged.

#### Outcome:

Exact GitHub `main` source commit `2ca7be591df912e6bfcc03a9dbe6ed1755c85e00` (`Add deterministic FLAC D1 corpus`) is one commit ahead of the approved D1 planning boundary and modifies exactly six intended paths. No RTL, QIP, QSF, SDC, clocking, DDR, transport integration, decoder, or PCM-output implementation source changes.

The D1 corpus pins `flac 1.5.0` and `metaflac 1.5.0`, uses only algorithmically generated signed integer PCM, and keeps generated `.pcm`/`.flac` media local under `tools/streams/generated/flac/`. The tracked manifest records stable IDs, source PCM SHA-256, encoded FLAC SHA-256, golden decoded PCM SHA-256, exact sample counts, channel/rate/bit-depth metadata, metadata-block inventory, FLAC frame/block/subframe/channel-assignment observations, and the deterministic tool/command policy. Seventeen concrete short-length members are individually identified for lengths 1, 2, 3, 4, 7, 8, 15, 16, 31, 32, 33, 255, 256, 257, 4095, 4096, and 4097 samples.

The generated corpus contains 27 valid or valid-but-first-milestone-unsupported streams and two deterministic invalid streams. The unsupported case is a valid 24-bit mono FLAC stream; the invalid cases are deterministic truncation and frame-payload corruption whose reference `flac --test` result is pinned to failure. Eight deterministic transport profiles are pinned: continuous, byte-at-a-time, periodic input stalls, periodic output stalls, combined stalls, fixed-seed pseudorandom stalls/chunks, small chunks, and exact-final-byte EOS.

A clean local regeneration using the pinned tools reproduces the tracked manifest exactly. Python compilation succeeds, and `verify_flac_corpus.py` reports `VERIFY PASS: 27 valid/unsupported cases, 2 invalid cases, and 8 transport profiles`. The verifier fails closed on tool versions, schema/content, generated file set, hashes, reference FLAC test/decode, observed feature inventory, metadata inventory, and transport-profile signatures.

The observed encoded corpus spans FLAC subframe types `CONSTANT`, `FIXED`, `LPC`, and `VERBATIM`; channel assignments `INDEPENDENT`, `MID_SIDE`, and `RIGHT_SIDE`; fixed predictor orders 0/1/2; LPC order 8; and Rice partition orders 0/3/4/5. These are corpus observations only and do not claim the future FPGA decoder supports all observed features.

`.ai/core-standards.md` still has no controlled FLAC source record. D1 used the official Xiph FLAC 1.5.0 reference tools/documentation for corpus generation and validation; any standards-library addition remains a separate explicitly scoped metadata boundary.

#### Next Steps:

Preserve this D1 corpus as the deterministic reference infrastructure. The next engineering boundary is D2: prove the codec-independent signed 16-bit mono/stereo 44.1/48 kHz PCM contract, buffering/output adapter, deterministic valid/ready backpressure and stream re-arm, and real MiSTer audio output before integrating a FLAC decoder. D2 requires its own approved implementation boundary.

#### Files Modified:

- `.gitignore`
- `tools/streams/FLAC_CORPUS.md`
- `tools/streams/flac_corpus_common.py`
- `tools/streams/flac_corpus_manifest.json`
- `tools/streams/generate_flac_corpus.py`
- `tools/streams/verify_flac_corpus.py`

#### Status:

- [x] Built — D1 generator/verifier executed locally with pinned FLAC/metaflac 1.5.0; no Quartus build is required because FPGA implementation source is unchanged
- [x] Passed — tracked manifest regenerates exactly and fail-closed verification passes for 27 valid/unsupported cases, 2 invalid cases, and 8 transport profiles

---
## 005 COMMIT D2 081c006 2026-08-16T05:16:26-07:00

#### Coming From:

D1 2ca7be5

#### Purpose:

Implement the codec-independent PCM/output proof before FLAC decoder integration: signed 16-bit mono/stereo at 44.1/48 kHz, deterministic valid/ready backpressure, clean stream re-arm on Audio Test mode changes, clock-domain-safe buffering into MiSTer's 24.576 MHz audio domain, and direct signed AUDIO_L/AUDIO_R output without modifying the MPEG-2 video decoder or adding compressed-audio RTL.

#### Outcome:

The approved D2 source boundary spans three sequential GitHub `main` commits: `bfc4273390437139de4adc7194b3507b0ec1413b` (`Add D2 PCM test source`), `95eedbcfbbcad305b2f822485b60e525b8f97f1f` (`Add D2 PCM CDC FIFO`), and integration commit `081c006c8d8f6876493642ad1bc228c9261730f7` (`Integrate D2 PCM output proof`). Comparison from the approved D2 plan boundary `0c48eeb39ef448105e6af202e3ea46f36d29c645` through `081c006` shows exactly six intended paths: `MediaPlayer_top_00.svh`, `files.qip`, three new `rtl/audio/` modules, and `tools/streams/verify_d2_pcm_path.py`. No H.262 decoder, video presentation, DDR, PLL, SDC, compressed-audio, or FLAC implementation file changes.

The PCM producer runs in `clk_mpeg2` and exposes stable valid/ready sample data; its phase state advances only on `valid && ready`, so FIFO backpressure cannot alter the accepted sample sequence. Modes 1-4 provide 44.1 kHz mono, 44.1 kHz stereo, 48 kHz mono, and 48 kHz stereo deterministic square-wave proof streams. The left channel is approximately 440 Hz, stereo right is approximately 660 Hz, mono duplication occurs only in the output adapter, and MiSTer output uses `AUDIO_S=1` with `AUDIO_MIX=0`.

A 256-word x 34-bit DCFIFO transfers `{rate_48k, stereo, left, right}` from `clk_mpeg2` to `CLK_AUDIO` using synchronized asynchronous-clear release. Audio Test mode changes on `status[3:1]` generate a stretched Audio-only reset request and independently synchronized release into the source and output domains; MPEG reset/readiness is not coupled to Audio readiness.

The output adapter uses the existing MiSTer `CLK_AUDIO` 24.576 MHz clock. 48 kHz is exact at one sample every 512 clocks. The 44.1 kHz integer accumulator produces exact long-term rate with deterministic 557/558-clock sample intervals. A real FIFO underrun forces silence and sets a sticky internal diagnostic.

The deterministic checker was run locally after the integrated source was staged and reports `D2 PCM VERIFY PASS`. For each of the four modes it pins an 8192-sample PCM SHA-256, proves accepted PCM is identical under continuous, periodic, bursty, and deterministic pseudorandom-like ready patterns, proves reset/re-arm reproduces the exact independent stream start, verifies 48 kHz `/512` scheduling, and verifies the 44.1 kHz 557/558-clock scheduling signature.

Quartus compilation, post-fit resource/timing delta versus the accepted D0 denominator, and physical MiSTer audio-output behavior have not yet been validated. D2 therefore remains open at the hardware-validation boundary.

#### Next Steps:

1. Pull current Audio `main` and run `python3 tools/streams/verify_d2_pcm_path.py`; expect `D2 PCM VERIFY PASS`.
2. Remove `db/`, `incremental_db/`, and `output_files/`, then run `quartus_sh --flow compile MediaPlayer` and `quartus_sta -t tools/phase1p_timing.tcl`.
3. Load the resulting core on the standard MiSTer target and exercise Audio Test: Off, 44.1k Mono, 44.1k Stereo, 48k Mono, and 48k Stereo. Confirm Off is silent; all four active modes are stable; mono is centered/equal L/R; stereo has the distinct lower-frequency left and higher-frequency right tones; repeated mode changes and reset re-arm cleanly; and existing MPEG/video behavior remains unchanged.
4. Push `081c006_build_logs.tar.gz` plus any D2 test notes/resources into `.ai/current_results/` and report the hardware results.
5. Compare ALMs, registers, RAM blocks/bits, DSPs, PLLs, global/focused timing, and structural warnings against D0 before closing D2 or proceeding to FLAC RTL.

#### Files Modified:

- `MediaPlayer_top_00.svh`
- `files.qip`
- `rtl/audio/audio_pcm_test_source.sv`
- `rtl/audio/audio_pcm_fifo.sv`
- `rtl/audio/audio_pcm_output_adapter.sv`
- `tools/streams/verify_d2_pcm_path.py`

#### Status:

- [ ] Built — deterministic D2 software verification passes; clean Quartus build/resource/timing evidence is pending
- [ ] Passed — MiSTer validation of all four PCM modes, re-arm behavior, and video non-regression is pending

---
## 006 COMMIT D2 081c006 2026-08-16T05:38:00-07:00

#### Coming From:

D2 081c006

#### Purpose:

Accept the user-reported D2 clean-build and MiSTer hardware-validation result, bind it to the uploaded build-evidence package, and close the codec-independent PCM/output milestone before any FLAC decoder RTL is started.

#### Outcome:

The user reports that all requested D2 tests pass. This accepts the requested software/clean-build/STA/hardware validation boundary: Audio Test Off is silent; 44.1 kHz mono/stereo and 48 kHz mono/stereo operate as requested; channel behavior is correct; repeated mode changes and reset re-arm cleanly; and the inherited MPEG/video behavior shows no reported regression.

`.ai/current_results/cefcb94_build_logs.tar.gz` is present as Git blob `dc195a704d7b2624c7d35109c53b3c133bd175e8`, size 1,190,225 bytes. The filename reflects the metadata-only `cefcb94` core-log commit at the user's build HEAD; under the project cycle convention the executable D2 source boundary remains `081c006c8d8f6876493642ad1bc228c9261730f7` because metadata-only `.ai` commits do not change the cycle source SHA.

The GitHub connector can verify the package identity but cannot decode the gzip payload, so this agent is not representing fitter/STA/resource numbers as independently extracted from that archive. The clean-build/timing result is accepted from the user's explicit all-tests-pass report, while the exact binary package is retained as the auditable build artifact for later local inspection if needed.

D2 is accepted and closed as the hardware-proven common PCM/output milestone. The next engineering boundary is D3: a bounded FLAC decoder behind the established compressed-input and codec-independent PCM contracts. No D3 source work is authorized by this entry.

#### Next Steps:

Archive the accepted D2 build package under the executable cycle SHA, complete the required compatibility check against current MiSTer-Media-Player development, then prepare the D3 implementation plan and wait for explicit user approval before modifying FLAC RTL.

#### Files Modified:

- `.ai/core-log.md`

#### Status:

- [x] Built — user reports the requested clean Quartus/STA validation passes; build package is present in `.ai/current_results/`
- [x] Passed — all requested D2 MiSTer audio modes, mode/reset re-arm, and MPEG/video non-regression checks reported passing

---
## 007 COMMIT D2 081c006 2026-08-16T05:43:00-07:00

#### Coming From:

D2 081c006

#### Purpose:

Finalize the accepted D2 cycle by archiving its build evidence and checking the independent Audio implementation against the current MiSTer-Media-Player development line for immediate reintegration conflicts.

#### Outcome:

Archive commit `e84ac0ad20d24a0630d4aa1406a5471d6090ff37` (`(081c006) archiving results`) renames the accepted build artifact from `.ai/current_results/cefcb94_build_logs.tar.gz` to `.ai/archived_results/081c006_build_logs.tar.gz` without changing its Git blob `dc195a704d7b2624c7d35109c53b3c133bd175e8`. `.ai/current_results/` is returned to its `.gitkeep`-only state.

The current MiSTer-Media-Player `master` metadata tip is `16eec4fc7ddd674a7e09ca450e3ec40407fb8430`; its current functional source commit is `b11590cf77febb7364a13e628a64e107fc2a8620` (`Consolidate generalized P parser`). The main project's current work is parser consolidation. At `b11590c`, `MediaPlayer_top_00.svh` remains exact blob `a4d085e655e0566d2694d0701cbbf9372763fd85`, identical to the frozen Audio starting point, so the top-level Audio fork anchors have not moved. The opening `files.qip` insertion context used by D2 is also unchanged.

No immediate D2 reintegration conflict is present. The main project's `files.qip` has evolved elsewhere as parser sources changed, so eventual reintegration must merge the three Audio source-list entries into the then-current main source list rather than replacing main's `files.qip` with the frozen Audio copy. The standalone `rtl/audio/` paths remain isolated from the main parser work.

D2 is fully closed. D0 remains the zero-change denominator, D1 remains the deterministic FLAC corpus boundary, and D2 is the hardware-proven common PCM/output boundary. The next proposed development cycle is D3, bounded FLAC decode into the existing PCM contract; implementation requires explicit user approval.

#### Next Steps:

Prepare and present the D3 bounded-FLAC implementation/validation boundary. Do not modify FLAC RTL until the user explicitly approves that plan.

#### Files Modified:

- `.ai/core-log.md`

#### Status:

- [x] Built — D2 build evidence archived under the executable cycle SHA
- [x] Passed — D2 hardware acceptance closed; compatibility review finds no immediate reintegration conflict

---
## 008 COMMIT D3 f9d6c0f 2026-08-16T05:55:39-07:00

#### Coming From:

D2 081c006

#### Purpose:

Implement the approved first bounded native-FLAC decode boundary behind the D2 codec-independent PCM contract, proving real FLAC marker/metadata/frame parsing for the deterministic D1 silence anchors without pulling FIXED/LPC/Rice decoding or broader metadata support forward into D3.

#### Outcome:

The D3 source boundary spans six sequential GitHub `main` commits from `2cceef97b96a4de426124822eb92273e6daab924` (`Add D3 bounded FLAC decoder`) through integration tip `f9d6c0f3b60c5426642e92f5e5b997f3d74c852a` (`Add D3 FLAC sources to Quartus project`). Comparison from closed-D2 metadata tip `5948c067c1323d771e238250ad52c0877756af06` through `f9d6c0f` reports exactly six changed paths: `MediaPlayer_top_00.svh`, `MediaPlayer_top_07.svh`, `files.qip`, `rtl/audio/audio_flac_constant_decoder.sv`, `rtl/audio/audio_flac_stream_fifo.sv`, and `tools/streams/verify_d3_flac_constant.py`. No H.262 decoder, video reconstruction/presentation, DDR, PLL, or SDC file changes.

D1 corpus inspection showed that `flac_00_silence_mono_44100` is a 64-byte native FLAC stream and `flac_01_silence_stereo_48000` is a 70-byte native FLAC stream. Each contains one final 34-byte STREAMINFO metadata block followed by exactly two fixed 4096-sample frames using independent-channel CONSTANT subframes. Their pinned encoded SHA-256 values are `035d023a6b960325db67252ece6d4b29cf7e0a72558030af129e7ba2b3f70e4e` and `660f237bdb3fa3474dcca80c8b6f63126aaaf8a2105a9904eca596f1cd79f5a4`; their exact golden PCM hashes remain the D1 source hashes `4fe7b59af6de3b665b67788cc2f99892ab827efae3a467342b3bb4e3bc8e5bfe` and `c35020473aed1b4642cd726cad727b63fff2824ad68cedd7ffb73c7cbd890479`.

The decoder implements the native `fLaC` marker, one final STREAMINFO block, fixed 4096-sample block sizing, 16-bit mono/stereo stream properties at 44.1/48 kHz, fixed-block single-byte frame numbers, independent CONSTANT subframes, FLAC frame-header CRC-8, frame CRC-16, exact PCM sample counting, exact-final-byte EOS, and sticky `EOS_OK` / `CLEAN_REJECT` / `STREAM_ERROR` terminal states. Valid FLAC syntax outside this deliberately narrow D3 envelope rejects cleanly instead of being misdecoded; malformed marker/sequence/CRC/EOS terminates as stream error. PCM is released only after its complete compressed frame has passed CRC validation.

`MediaPlayer_top_00.svh` adds F2 `FLAC` file loading as a sibling HPS transport using its own 256-byte DCFIFO from `clk_sys` to `clk_mpeg2`; F1 and all MPEG stream-readiness logic remain video-only. Audio-local reset stretching now also covers FLAC file starts and holds HPS with `ioctl_wait` while the compressed/audio output paths are cleared, preventing loss of the first file byte. Download completion is synchronized into the decoder domain and becomes EOS only after the compressed FIFO drains. D2 Audio Test modes remain an override; with Audio Test Off, the FLAC decoder owns the established D2 PCM valid/ready contract. A successful silence-anchor FLAC terminal state is ORed into USER so real hardware has an observable success indication despite the decoded PCM being silent.

The deterministic reference verifier was run locally with exact `flac 1.5.0` / `metaflac 1.5.0` and reports `D3 FLAC CONSTANT VERIFY PASS`. It regenerates both D1 anchor streams, verifies their exact encoded sizes/hashes, parses STREAMINFO and both frames, validates every frame-header CRC-8 and frame CRC-16, reconstructs the exact 8192-sample PCM stream, matches the pinned D1 PCM SHA-256, and proves accepted PCM remains invariant under four deterministic output-ready stall profiles.

`.ai/core-standards.md` still does not contain FLAC. D3 therefore used RFC 9639, `Free Lossless Audio Codec (FLAC)`, IETF Standards Track, December 2024, as the external normative format source. RFC 9639 defines the native marker/STREAMINFO/frame layout, frame-header CRC-8, CONSTANT subframe coding, and frame CRC-16 used by this implementation. Adding RFC 9639 to the controlled standards library remains a separate metadata action.

Quartus compilation, fitted resource/timing delta versus D0/D2, physical F2 transfer behavior, USER terminal indication, and MiSTer regression testing remain pending. D3 is therefore implemented but not yet hardware-accepted.

#### Next Steps:

1. Pull current Audio `main` and run `python3 tools/streams/verify_d3_flac_constant.py`; expect `D3 FLAC CONSTANT VERIFY PASS`.
2. Run `python3 tools/streams/generate_flac_corpus.py` to materialize the ignored D1 media, then use `tools/streams/generated/flac/flac_00_silence_mono_44100.flac` and `flac_01_silence_stereo_48000.flac` for F2 hardware tests.
3. Remove `db/`, `incremental_db/`, and `output_files/`; run `quartus_sh --flow compile MediaPlayer` and `quartus_sta -t tools/phase1p_timing.tcl`.
4. On MiSTer, start from reset with Audio Test Off and no prior successful video diagnostic. Load each supported FLAC through F2 independently; each should remain silent by design and finish with solid USER, proving the exact supported decode/EOS path. Reload each stream and reset between loads to prove re-arm. Load `flac_neg_02_unsupported_24bit_mono_44100.flac`; it must terminate without USER success, hang, or corruption of later supported reloads.
5. Re-run all four D2 Audio Test modes and the standing MPEG video regressions to prove the new F2 transport/decoder does not couple into video readiness or break the D2 output path.
6. Push `f9d6c0f_build_logs.tar.gz` plus any D3 hardware notes/resources into `.ai/current_results/` and report the result. Compare ALMs/registers/RAM/DSP/PLL and timing against D0 and D2 before closing D3 or expanding FLAC syntax.

#### Files Modified:

- `MediaPlayer_top_00.svh`
- `MediaPlayer_top_07.svh`
- `files.qip`
- `rtl/audio/audio_flac_constant_decoder.sv`
- `rtl/audio/audio_flac_stream_fifo.sv`
- `tools/streams/verify_d3_flac_constant.py`

#### Status:

- [ ] Built — deterministic D3 reference verification passes; clean Quartus build/resource/timing evidence is pending
- [ ] Passed — MiSTer F2 supported-stream/re-arm/clean-reject and D2/video regression validation is pending

---
## 009 COMMIT D3 97399dc 2026-08-16T07:21:00-07:00

#### Coming From:

D3 97399dc

#### Purpose:

Record the D3 hardware-blocking file-selector failure and the proposed minimal correction before modifying source. Normal generated `.flac` files are not visible in MiSTer's F2 browser even though the D3 decoder and generated media use the expected FLAC filename extension.

#### Outcome:

Evidence review confirms the generated lowercase `.flac` suffix is not the problem: current MiSTer file matching is case-insensitive. The active Audio `CONF_STR` currently declares `F2,FLAC,Open FLAC Audio;`. MiSTer's file-selector extension filter is evaluated in three-character units, so four-character `FLAC` cannot represent `.flac` as intended. Current MiSTer file matching supports wildcard characters in the three-character pattern; `FL*` therefore matches `.flac` without requiring users to rename generated files.

Proposed source boundary: modify only `MediaPlayer_top_00.svh`, changing `F2,FLAC,Open FLAC Audio;` to `F2,FL*,Open FLAC Audio;`. Do not alter the FLAC transport, decoder, PCM path, MPEG/video logic, QIP, clocks, DDR, or timing constraints.

Validation after approval: clean Quartus/STA build, verify normal lowercase `.flac` files become visible/selectable through F2, then repeat the existing D3 supported mono/stereo silence-anchor, re-arm, unsupported-24-bit clean-reject, D2 Audio Test, and MPEG/video regression matrix. This is a D3 corrective cycle, not D4 feature expansion.

#### Next Steps:

Await explicit user approval. If approved, make the single `MediaPlayer_top_00.svh` selector-filter change and commit it as the next official build hash. No source change is authorized by this entry alone.

#### Files Modified:

- `.ai/core-log.md`

#### Status:

- [ ] Built — proposal only; no new executable build has been produced
- [ ] Passed — awaiting user approval for the one-line D3 selector correction

---
## 010 COMMIT D3 152b8f8 2026-08-16T07:29:37-07:00

#### Coming From:

D3 97399dc

#### Purpose:

Apply the approved minimal MiSTer F2 selector correction so normal `.flac` files are visible without changing the D3 decoder or transport boundary.

#### Outcome:

Exact GitHub source commit `152b8f8ae2a51882be4b1f8dfb7f03e77ef0daaf` (`Fix D3 FLAC file selector`) modifies exactly one line in exactly one file: `MediaPlayer_top_00.svh` changes `F2,FLAC,Open FLAC Audio;` to `F2,FL*,Open FLAC Audio;`. GitHub's commit diff confirms no other source path or line changed.

This preserves the existing F2 index, compressed-audio FIFO, FLAC decoder, D2 PCM contract, MPEG/video readiness, QIP, clocks, DDR, and timing constraints. `152b8f8` is the new official D3 build hash for this corrective validation cycle.

#### Next Steps:

Pull current Audio `main`, perform a clean Quartus/STA build, and verify lowercase `.flac` files are now visible/selectable through F2. Then repeat the existing D3 supported mono/stereo silence-anchor tests, reset/re-arm, unsupported 24-bit clean-reject followed by supported reload, all four D2 Audio Test modes, and the standing MPEG/video regressions. Place any additional diagnostic resources in `.ai/current_results/`; the normal build and timing outputs belong in root `output_files/` and `phase1p_timing_reports/` under the current workflow. Report the results before any archive or compatibility action.

#### Files Modified:

- `MediaPlayer_top_00.svh`

#### Status:

- [ ] Built — source correction committed; clean Quartus/STA build is pending
- [ ] Passed — corrected F2 file visibility and D3 hardware regression matrix are pending

---