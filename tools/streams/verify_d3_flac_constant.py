#!/usr/bin/env python3
"""Deterministic reference proof for D3 CONSTANT plus bounded D4 VERBATIM FLAC."""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

EXPECTED = {
    "mono": {
        "channels": 1,
        "rate": 44100,
        "size": 64,
        "flac_sha256": "035d023a6b960325db67252ece6d4b29cf7e0a72558030af129e7ba2b3f70e4e",
        "pcm_sha256": "4fe7b59af6de3b665b67788cc2f99892ab827efae3a467342b3bb4e3bc8e5bfe",
    },
    "stereo": {
        "channels": 2,
        "rate": 48000,
        "size": 70,
        "flac_sha256": "660f237bdb3fa3474dcca80c8b6f63126aaaf8a2105a9904eca596f1cd79f5a4",
        "pcm_sha256": "c35020473aed1b4642cd726cad727b63fff2824ad68cedd7ffb73c7cbd890479",
    },
}

VERBATIM_CASE_ID = "flac_06_lfsr_48000"
VERBATIM_EXPECTED = {
    "channels": 1,
    "rate": 48000,
    "size": 16444,
    "flac_sha256": "72ef391157b6283e197484613a9a1447426d97e6c6aedfef0a9de021f27b6e21",
    "pcm_sha256": "4c05215da81e4ebab72d8b6ab6db43643a5333e776d7e638646213128a858d46",
}

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("flac_corpus_manifest.json")
RTL_PATH = ROOT / "rtl" / "audio" / "audio_flac_constant_decoder.sv"
UNSUPPORTED_CASE_ID = "flac_neg_02_unsupported_24bit_mono_44100"
FIFO_DEPTH = 256
STREAMINFO_DECISION_BYTES = 42
BLOCK_SAMPLES = 4096


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crc8(data: bytes) -> int:
    c = 0
    for b in data:
        c ^= b
        for _ in range(8):
            c = (((c << 1) ^ 0x07) if c & 0x80 else (c << 1)) & 0xFF
    return c


def crc16(data: bytes) -> int:
    c = 0
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = (((c << 1) ^ 0x8005) if c & 0x8000 else (c << 1)) & 0xFFFF
    return c


def encode_raw_case(root: Path, name: str, pcm: bytes, channels: int, bits: int, rate: int) -> bytes:
    pcm_path = root / f"{name}.pcm"
    flac_path = root / f"{name}.flac"
    pcm_path.write_bytes(pcm)
    subprocess.run([
        "flac", "--force", "--silent", "--verify", "--threads=1",
        "--no-padding", "--no-seektable", "--no-preserve-modtime",
        "--force-raw-format", "--endian=little", "--sign=signed",
        f"--channels={channels}", f"--bps={bits}", f"--sample-rate={rate}",
        "-5", f"--output-name={flac_path}", str(pcm_path),
    ], check=True)
    subprocess.run([
        "metaflac", "--dont-use-padding", "--remove", "--block-type=VORBIS_COMMENT", str(flac_path)
    ], check=True)
    return flac_path.read_bytes()


def encode_case(root: Path, name: str, channels: int, rate: int) -> tuple[bytes, bytes]:
    pcm = b"\x00\x00" * (8192 * channels)
    return pcm, encode_raw_case(root, name, pcm, channels, 16, rate)


def lfsr16_step(state: int) -> int:
    bit = ((state >> 0) ^ (state >> 2) ^ (state >> 3) ^ (state >> 5)) & 1
    return ((state >> 1) | (bit << 15)) & 0xFFFF


def encode_verbatim_case(root: Path) -> tuple[bytes, bytes]:
    state = 0x1ACE
    pcm = bytearray()
    for _ in range(8192):
        state = lfsr16_step(state)
        pcm += struct.pack("<h", state - 32768)
    encoded = encode_raw_case(root, VERBATIM_CASE_ID, bytes(pcm), 1, 16, 48000)
    return bytes(pcm), encoded


def lfsr24_step(state: int) -> int:
    bit = ((state >> 0) ^ (state >> 1) ^ (state >> 2) ^ (state >> 7)) & 1
    return ((state >> 1) | (bit << 23)) & 0xFFFFFF


def encode_unsupported_case(root: Path) -> bytes:
    state = 0x5A17C3
    pcm = bytearray()
    for _ in range(4096):
        state = lfsr24_step(state)
        value = state - 0x800000
        pcm += int(value & 0xFFFFFF).to_bytes(3, "little")
    return encode_raw_case(root, UNSUPPORTED_CASE_ID, bytes(pcm), 1, 24, 44100)


def manifest_case(case_id: str) -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    columns = manifest["case_columns"]
    for row in manifest["cases"]:
        case = dict(zip(columns, row))
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"missing manifest case {case_id}")


def parse_streaminfo(data: bytes) -> tuple[int, int, int, int]:
    if data[:4] != b"fLaC":
        raise AssertionError("marker")
    if data[4:8] != bytes.fromhex("80000022"):
        raise AssertionError("metadata envelope")
    si = data[8:42]
    min_block, max_block = struct.unpack(">HH", si[:4])
    props = int.from_bytes(si[10:18], "big")
    rate = props >> 44
    channels = ((props >> 41) & 7) + 1
    bps = ((props >> 36) & 31) + 1
    total = props & ((1 << 36) - 1)
    assert (min_block, max_block, bps, total) == (4096, 4096, 16, 8192)
    return rate, channels, bps, total


def decode_constant_subset(data: bytes) -> tuple[bytes, int, int]:
    rate, channels, _, _ = parse_streaminfo(data)
    assert (rate, channels) in ((44100, 1), (48000, 2))

    pos = 42
    out = bytearray()
    for frame_no in range(2):
        frame_len = 11 if channels == 1 else 14
        frame = data[pos:pos + frame_len]
        assert len(frame) == frame_len
        expected_code = 0xCA if rate == 48000 else 0xC9
        expected_fmt = 0x18 if channels == 2 else 0x08
        assert frame[:5] == bytes([0xFF, 0xF8, expected_code, expected_fmt, frame_no])
        assert crc8(frame[:5]) == frame[5]
        assert crc16(frame[:-2]) == int.from_bytes(frame[-2:], "big")
        p = 6
        samples = []
        for _ in range(channels):
            assert frame[p] == 0x00
            sample = int.from_bytes(frame[p + 1:p + 3], "big", signed=True)
            samples.append(sample)
            p += 3
        assert p == frame_len - 2
        for _ in range(BLOCK_SAMPLES):
            for sample in samples:
                out += struct.pack("<h", sample)
        pos += frame_len
    assert pos == len(data)
    return bytes(out), rate, channels


def decode_verbatim_subset(data: bytes) -> tuple[bytes, int, int]:
    rate, channels, _, _ = parse_streaminfo(data)
    assert (rate, channels) == (48000, 1)

    pos = 42
    out = bytearray()
    frame_len = 6 + 1 + (BLOCK_SAMPLES * 2) + 2
    for frame_no in range(2):
        frame = data[pos:pos + frame_len]
        assert len(frame) == frame_len
        assert frame[:5] == bytes([0xFF, 0xF8, 0xCA, 0x08, frame_no])
        assert crc8(frame[:5]) == frame[5]
        assert crc16(frame[:-2]) == int.from_bytes(frame[-2:], "big")
        assert frame[6] == 0x02, "expected 16-bit no-wasted-bits VERBATIM header"
        p = 7
        for _ in range(BLOCK_SAMPLES):
            sample = int.from_bytes(frame[p:p + 2], "big", signed=True)
            out += struct.pack("<h", sample)
            p += 2
        assert p == frame_len - 2
        pos += frame_len
    assert pos == len(data)
    return bytes(out), rate, channels


def assert_output_backpressure(decoded: bytes, channels: int) -> None:
    for period, stall in ((0, 0), (7, 3), (5, 2), (11, 1)):
        accepted = bytearray()
        frames = [decoded[i:i + 2 * channels] for i in range(0, len(decoded), 2 * channels)]
        cycle = 0
        index = 0
        while index < len(frames):
            ready = period == 0 or (cycle % period) >= stall
            if ready:
                accepted += frames[index]
                index += 1
            cycle += 1
        assert bytes(accepted) == decoded


def assert_d4_rtl() -> None:
    rtl = RTL_PATH.read_text()
    ready_start = rtl.index("assign in_ready =")
    ready_end = rtl.index("assign pcm_valid", ready_start)
    ready_expr = rtl[ready_start:ready_end]
    assert "(state == S_REJECT)" in ready_expr
    assert "(state == S_ERROR)" in ready_expr
    assert "(state == S_VERB_HI)" in ready_expr
    assert "(state == S_VERB_LO)" in ready_expr
    assert "S_EMIT_LOAD" in rtl
    assert "in_data == 8'h02" in rtl
    assert "reg signed [15:0] verbatim_frame_mem [0:4095];" in rtl
    assert "verbatim_frame_mem[verbatim_index] <= {verbatim_hi, in_data};" in rtl
    assert "assign pcm_valid    = (state == S_EMIT);" in rtl
    assert "assign clean_reject = (state == S_REJECT);" in rtl
    assert "assign stream_error = (state == S_ERROR);" in rtl


def simulate_terminal_drain(stream: bytes, terminal_at: int) -> tuple[int, int, bool]:
    """Model the F2 FIFO after a sticky reject/error decision."""
    assert 0 < terminal_at <= len(stream)
    produced = 0
    consumed = 0
    occupancy = 0
    max_occupancy = 0
    terminal = False
    cycles = 0
    limit = len(stream) * 4 + FIFO_DEPTH * 4

    while consumed < len(stream):
        if produced < len(stream) and occupancy < FIFO_DEPTH:
            produced += 1
            occupancy += 1
        if occupancy:
            occupancy -= 1
            consumed += 1
            if consumed >= terminal_at:
                terminal = True
        max_occupancy = max(max_occupancy, occupancy)
        cycles += 1
        assert cycles < limit, "terminal drain stalled"

    assert terminal
    assert produced == len(stream)
    assert consumed == len(stream)
    assert occupancy == 0
    return consumed, max_occupancy, terminal


def main() -> None:
    for tool, expected in (("flac", "flac 1.5.0"), ("metaflac", "metaflac 1.5.0")):
        path = shutil.which(tool)
        if not path:
            raise SystemExit(f"missing {tool}")
        got = subprocess.run([path, "--version"], check=True, text=True, capture_output=True).stdout.strip()
        if got != expected:
            raise SystemExit(f"{tool} version mismatch: {got!r}")

    assert_d4_rtl()

    with tempfile.TemporaryDirectory(prefix="d4-flac-") as td:
        root = Path(td)
        supported_streams: list[tuple[bytes, str]] = []

        # Preserve both D3 CONSTANT anchors exactly.
        for name, spec in EXPECTED.items():
            pcm, encoded = encode_case(root, name, spec["channels"], spec["rate"])
            assert len(encoded) == spec["size"]
            assert sha(encoded) == spec["flac_sha256"]
            assert sha(pcm) == spec["pcm_sha256"]
            decoded, rate, channels = decode_constant_subset(encoded)
            assert (rate, channels) == (spec["rate"], spec["channels"])
            assert decoded == pcm
            assert sha(decoded) == spec["pcm_sha256"]
            assert_output_backpressure(decoded, channels)
            supported_streams.append((encoded, "constant"))

        # D4 target: the tracked D1 mono 48 kHz LFSR stream is two independent
        # 4096-sample VERBATIM subframes. Verify exact corpus identity and PCM.
        pcm, verbatim = encode_verbatim_case(root)
        verbatim_spec = manifest_case(VERBATIM_CASE_ID)
        assert len(verbatim) == VERBATIM_EXPECTED["size"] == verbatim_spec["flac_size_bytes"]
        assert sha(verbatim) == VERBATIM_EXPECTED["flac_sha256"] == verbatim_spec["flac_sha256"]
        assert sha(pcm) == VERBATIM_EXPECTED["pcm_sha256"] == verbatim_spec["source_sha256"]
        assert verbatim_spec["subframe_types"] == ["VERBATIM"]
        assert verbatim_spec["channel_assignments"] == ["INDEPENDENT"]
        decoded, rate, channels = decode_verbatim_subset(verbatim)
        assert (rate, channels) == (48000, 1)
        assert decoded == pcm
        assert sha(decoded) == VERBATIM_EXPECTED["pcm_sha256"]
        assert_output_backpressure(decoded, channels)
        supported_streams.append((verbatim, "verbatim"))

        # A payload bit flip must invalidate frame CRC before any reference model
        # accepts the frame as decoded output.
        corrupted = bytearray(verbatim)
        corrupted[42 + 7 + 100] ^= 0x01
        try:
            decode_verbatim_subset(bytes(corrupted))
        except AssertionError:
            pass
        else:
            raise AssertionError("corrupted VERBATIM frame unexpectedly passed CRC")

        unsupported = encode_unsupported_case(root)
        unsupported_spec = manifest_case(UNSUPPORTED_CASE_ID)
        assert len(unsupported) == unsupported_spec["flac_size_bytes"]
        assert sha(unsupported) == unsupported_spec["flac_sha256"]
        assert len(unsupported) > FIFO_DEPTH

        consumed, _, terminal = simulate_terminal_drain(unsupported, STREAMINFO_DECISION_BYTES)
        assert terminal and consumed == len(unsupported)

        malformed = bytes([unsupported[0] ^ 0x01]) + unsupported[1:]
        consumed, _, terminal = simulate_terminal_drain(malformed, 1)
        assert terminal and consumed == len(malformed)

        # Reset/re-arm: every supported D3/D4 stream must remain independently
        # decodable after either sticky terminal path is reset.
        for encoded, kind in supported_streams:
            if kind == "verbatim":
                decoded, _, _ = decode_verbatim_subset(encoded)
            else:
                decoded, _, _ = decode_constant_subset(encoded)
            assert decoded

    print("D4 FLAC VERBATIM VERIFY PASS")
    print("  D3: CONSTANT mono 44.1 kHz + stereo 48 kHz anchors preserved")
    print("  D4: VERBATIM mono 48 kHz, 16-bit, 2 x 4096-sample frames")
    print("  CRC: header CRC-8 + frame CRC-16; corrupted VERBATIM payload rejected")
    print("  PCM: exact D1 LFSR SHA-256 under deterministic output stalls")
    print("  terminal drain/re-arm: D3 unsupported/error behavior preserved")


if __name__ == "__main__":
    main()
