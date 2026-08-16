#!/usr/bin/env python3
"""Deterministic reference proof for the bounded D3 constant-subframe FLAC subset."""
from __future__ import annotations

import hashlib
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


def main() -> None:
    for tool, expected in (("flac", "flac 1.5.0"), ("metaflac", "metaflac 1.5.0")):
        path = shutil.which(tool)
        if not path:
            raise SystemExit(f"missing {tool}")
        got = subprocess.run([path, "--version"], check=True, text=True, capture_output=True).stdout.strip()
        if got != expected:
            raise SystemExit(f"{tool} version mismatch: {got!r}")

    with tempfile.TemporaryDirectory(prefix="d3-flac-") as td:
        root = Path(td)
        for name, spec in EXPECTED.items():
            pcm, encoded = encode_case(root, name, spec["channels"], spec["rate"])
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

    print("D3 FLAC CONSTANT VERIFY PASS")
    print("  native FLAC: STREAMINFO-only, 4096-sample fixed blocks, CONSTANT subframes")
    print("  anchors: mono 44.1 kHz and stereo 48 kHz, 8192 samples each")
    print("  CRC: header CRC-8 and frame CRC-16 validated")
    print("  PCM: exact D1 SHA-256 for both anchors under deterministic output stalls")


if __name__ == "__main__":
    main()
