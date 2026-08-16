# D1 deterministic FLAC corpus

This directory contains the source-controlled definition and verifier for the first
MiSTer-Media-Player-Audio FLAC regression corpus. Generated PCM and FLAC media stays
local under `tools/streams/generated/flac/` and is not committed.

## Tool pin

D1 is pinned to the Xiph reference command-line tools:

- `flac 1.5.0`
- `metaflac 1.5.0`

The generator exits on any version mismatch. The corpus uses native FLAC, raw signed
little-endian PCM input, compression level 5, one encoding thread, encoder verification,
no seektable, and no default padding. The metadata case adds fixed Vorbis comments and a
17-byte padding block deliberately.

## Generate and verify

From the repository root:

```bash
python3 tools/streams/generate_flac_corpus.py
python3 tools/streams/verify_flac_corpus.py
```

The normal generator path must reproduce the tracked `flac_corpus_manifest.json`
byte-for-byte. `--update-manifest` is a maintenance operation for an explicitly approved
corpus revision, not normal test execution.

## Case policy

The positive families are the D1 roadmap families:

- `flac_00_silence_mono_44100`
- `flac_01_silence_stereo_48000`
- `flac_02_impulse_mono_44100`
- `flac_03_channel_id_48000`
- `flac_04_ramp_extremes_44100`
- `flac_05_periodic_44100`
- `flac_06_lfsr_48000`
- `flac_07_correlated_stereo_48000`
- `flac_08_short_lengths_44100` (each concrete length has its own stable case ID)
- `flac_09_metadata_48000`

D1 also pins deterministic malformed streams for truncation and frame corruption, plus a
valid 24-bit FLAC stream classified as unsupported for the first 16-bit candidate envelope.
That classification is a project milestone boundary, not a limitation of the FLAC format.

The manifest records source PCM SHA-256, encoded FLAC SHA-256, golden decoded PCM SHA-256,
commands, sample counts, metadata blocks, frame block sizes, channel assignments, subframe
types/orders, Rice partition orders, and deterministic transport/backpressure profile
signatures. Observed encoded features are evidence about this corpus only; they do not by
themselves claim that the future FPGA decoder supports those features.

## Provenance

All PCM is generated algorithmically by `flac_corpus_common.py`. No downloaded audio,
recording, music, or other third-party media is used. Generated media is intentionally local
so the repository carries reproducible source, manifests, and verification logic rather than
binary test assets.
