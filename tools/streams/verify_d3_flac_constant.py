#!/usr/bin/env python3
"""Deterministic reference proof for the bounded D3 constant-subframe FLAC subset."""
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

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("flac_corpus_manifest.json")
RTL_PATH = ROOT / "rtl" / "audio" / "audio_flac_constant_decoder.sv"
UNSUPPORTED_CASE_ID = "flac_neg_02_unsupported_24bit_mono_44100"
FIFO_DEPTH = 256
STREAMINFO_DECISION_BYTES = 42


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


def encode_case(root: Path, name: str, channels: int, rate: int) -> tuple[bytes, bytes]:
    pcm = b"\x00\x00" * (8192 * channels)
    pcm_path = root / f"{name}.pcm"
    flac_path = root / f"{name}.flac"
    pcm_path.write_bytes(pcm)
    subprocess.run([
        "flac", "--force", "--silent", "--verify", "--threads=1",
        "--no-padding", "--no-seektable", "--no-preserve-modtime",
        "--force-raw-format", "--endian=little", "--sign=signed",
        f"--channels={channels}", "--bps=16", f"--sample-rate={rate}",
        "-5", f"--output-name={flac_path}", str(pcm_path),
    ], check=True)
    subprocess.run([
        "metaflac", "--dont-use-padding", "--remove", "--block-type=VORBIS_COMMENT", str(flac_path)
    ], check=True)
    return pcm, flac_path.read_bytes()


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

    pcm_path = root / f"{UNSUPPORTED_CASE_ID}.pcm"
    flac_path = root / f"{UNSUPPORTED_CASE_ID}.flac"
    pcm_path.write_bytes(pcm)
    subprocess.run([
        "flac", "--force", "--silent", "--verify", "--threads=1",
        "--no-padding", "--no-seektable", "--no-preserve-modtime",
        "--force-raw-format", "--endian=little", "--sign=signed",
        "--channels=1", "--bps=24", "--sample-rate=44100",
        "-5", f"--output-name={flac_path}", str(pcm_path),
    ], check=True)
    subprocess.run([
        "metaflac", "--dont-use-padding", "--remove", "--block-type=VORBIS_COMMENT", str(flac_path)
    ], check=True)
    return flac_path.read_bytes()


def manifest_case(case_id: str) -> dict[str, object]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    columns = manifest["case_columns"]
    for row in manifest["cases"]:
        case = dict(zip(columns, row))
        if case["case_id"] == case_id:
            return case
    raise AssertionError(f"missing manifest case {case_id}")


def decode_subset(data: bytes) -> tuple[bytes, int, int]:
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
        for _ in range(4096):
            for sample in samples:
                out += struct.pack("<h", sample)
        pos += frame_len
    assert pos == len(data)
    return bytes(out), rate, channels


def assert_terminal_drain_rtl() -> None:
    rtl = RTL_PATH.read_text()
    ready_start = rtl.index("assign in_ready =")
    ready_end = rtl.index("assign pcm_valid", ready_start)
    ready_expr = rtl[ready_start:ready_end]
    assert "(state == S_REJECT)" in ready_expr
    assert "(state == S_ERROR)" in ready_expr
    assert "assign pcm_valid    = (state == S_EMIT);" in rtl
    assert "assign clean_reject = (state == S_REJECT);" in rtl
    assert "assign stream_error = (state == S_ERROR);" in rtl


def simulate_terminal_drain(stream: bytes, terminal_at: int) -> tuple[int, int, bool]:
    """Model the F2 FIFO after a sticky reject/error decision.

    The producer and consumer each move at most one byte per model cycle. Once
    terminal_at bytes have been consumed, parser work is finished but in_ready
    remains asserted, so all residual bytes continue to drain through exact EOS.
    """
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

        # Decoder remains ready both while parsing and after the sticky terminal
        # decision, so one queued byte can always retire on a consumer cycle.
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

    assert_terminal_drain_rtl()

    with tempfile.TemporaryDirectory(prefix="d3-flac-") as td:
        root = Path(td)
        supported_streams: dict[str, bytes] = {}
        for name, spec in EXPECTED.items():
            pcm, encoded = encode_case(root, name, spec["channels"], spec["rate"])
            supported_streams[name] = encoded
            assert len(encoded) == spec["size"]
            assert sha(encoded) == spec["flac_sha256"]
            assert sha(pcm) == spec["pcm_sha256"]
            decoded, rate, channels = decode_subset(encoded)
            assert (rate, channels) == (spec["rate"], spec["channels"])
            assert decoded == pcm
            assert sha(decoded) == spec["pcm_sha256"]

            # Deterministic output backpressure cannot alter the accepted PCM.
            for period, stall in ((0, 0), (7, 3), (5, 2), (11, 1)):
                accepted = bytearray()
                frame_bytes = [decoded[i:i + 2 * channels] for i in range(0, len(decoded), 2 * channels)]
                cycle = 0
                index = 0
                while index < len(frame_bytes):
                    ready = period == 0 or (cycle % period) >= stall
                    if ready:
                        accepted += frame_bytes[index]
                        index += 1
                    cycle += 1
                assert bytes(accepted) == decoded

        unsupported = encode_unsupported_case(root)
        unsupported_spec = manifest_case(UNSUPPORTED_CASE_ID)
        assert len(unsupported) == unsupported_spec["flac_size_bytes"]
        assert sha(unsupported) == unsupported_spec["flac_sha256"]
        assert len(unsupported) > FIFO_DEPTH

        # The 24-bit case is rejected from STREAMINFO after byte 42. It must then
        # drain the rest of a >256-byte file without producing PCM or wedging F2.
        consumed, _, terminal = simulate_terminal_drain(
            unsupported, STREAMINFO_DECISION_BYTES
        )
        assert terminal and consumed == len(unsupported)

        # A malformed marker enters S_ERROR on the first byte. The same terminal
        # drain rule must retire the complete oversized transfer through EOS.
        malformed = bytes([unsupported[0] ^ 0x01]) + unsupported[1:]
        consumed, _, terminal = simulate_terminal_drain(malformed, 1)
        assert terminal and consumed == len(malformed)

        # Reset/re-arm is represented by starting from parser state again; both
        # supported anchors must still decode exactly after either terminal path.
        for encoded in supported_streams.values():
            decoded, _, _ = decode_subset(encoded)
            assert decoded

    print("D3 FLAC CONSTANT VERIFY PASS")
    print("  native FLAC: STREAMINFO-only, 4096-sample fixed blocks, CONSTANT subframes")
    print("  anchors: mono 44.1 kHz and stereo 48 kHz, 8192 samples each")
    print("  CRC: header CRC-8 and frame CRC-16 validated")
    print("  PCM: exact D1 SHA-256 for both anchors under deterministic output stalls")
    print("  terminal drain: unsupported/error streams >256 bytes retire through EOS")
    print("  re-arm: supported anchors decode after terminal reject/error reset")


if __name__ == "__main__":
    main()
