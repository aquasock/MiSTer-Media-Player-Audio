#!/usr/bin/env python3
"""Shared deterministic FLAC D1 corpus definitions and helpers.

Generated media is intentionally local-only.  The tracked manifest pins the
expected output of FLAC/metaflac 1.5.0 for the cases defined here.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXPECTED_FLAC_VERSION = "flac 1.5.0"
EXPECTED_METAFLAC_VERSION = "metaflac 1.5.0"
MANIFEST_SCHEMA_VERSION = 2
CORPUS_REVISION = "D1-1"
GENERATOR_LICENSE = "Project-generated synthetic media; no third-party media input."

ROOT = Path(__file__).resolve().parent
GENERATED_DIR = ROOT / "generated" / "flac"
MANIFEST_PATH = ROOT / "flac_corpus_manifest.json"

CASE_COLUMNS = [
    "case_id", "group_id", "classification", "sample_rate_hz", "channels",
    "bits_per_sample", "sample_count", "pattern", "metadata_policy",
    "source_sha256", "flac_sha256", "decoded_sha256", "flac_size_bytes",
    "frame_count", "block_sizes", "channel_assignments", "subframe_types",
    "fixed_orders", "lpc_orders", "rice_partition_orders", "wasted_bits",
    "metadata_block_types", "metadata_block_lengths",
]

NEGATIVE_COLUMNS = [
    "case_id", "group_id", "classification", "base_case_id", "mutation",
    "reference_test", "file", "sha256", "size_bytes",
]


@dataclass(frozen=True)
class Case:
    case_id: str
    group_id: str
    sample_rate: int
    channels: int
    bits_per_sample: int
    sample_count: int
    pattern: str
    classification: str = "positive"
    metadata_case: bool = False


SHORT_LENGTHS = (1, 2, 3, 4, 7, 8, 15, 16, 31, 32, 33, 255, 256, 257, 4095, 4096, 4097)

CASES: tuple[Case, ...] = (
    Case("flac_00_silence_mono_44100", "flac_00_silence_mono_44100", 44100, 1, 16, 8192, "silence"),
    Case("flac_01_silence_stereo_48000", "flac_01_silence_stereo_48000", 48000, 2, 16, 8192, "silence"),
    Case("flac_02_impulse_mono_44100", "flac_02_impulse_mono_44100", 44100, 1, 16, 8192, "impulse"),
    Case("flac_03_channel_id_48000", "flac_03_channel_id_48000", 48000, 2, 16, 8192, "channel_id"),
    Case("flac_04_ramp_extremes_44100", "flac_04_ramp_extremes_44100", 44100, 1, 16, 8192, "ramp_extremes"),
    Case("flac_05_periodic_44100", "flac_05_periodic_44100", 44100, 2, 16, 8192, "periodic"),
    Case("flac_06_lfsr_48000", "flac_06_lfsr_48000", 48000, 1, 16, 8192, "lfsr"),
    Case("flac_07_correlated_stereo_48000", "flac_07_correlated_stereo_48000", 48000, 2, 16, 8192, "correlated_stereo"),
    *(Case(f"flac_08_short_len_{n:04d}_44100", "flac_08_short_lengths_44100", 44100, 1, 16, n, "short") for n in SHORT_LENGTHS),
    Case("flac_09_metadata_48000", "flac_09_metadata_48000", 48000, 2, 16, 4096, "metadata", metadata_case=True),
    Case("flac_neg_02_unsupported_24bit_mono_44100", "flac_negative", 44100, 1, 24, 4096, "lfsr24", classification="valid_unsupported"),
)

DERIVED_NEGATIVES = (
    {
        "case_id": "flac_neg_00_truncated_stereo_48000",
        "group_id": "flac_negative",
        "classification": "invalid_truncated",
        "base_case_id": "flac_01_silence_stereo_48000",
        "mutation": "remove_final_5_bytes",
        "reference_test": "fail",
    },
    {
        "case_id": "flac_neg_01_corrupt_frame_crc_mono_44100",
        "group_id": "flac_negative",
        "classification": "invalid_corrupted",
        "base_case_id": "flac_02_impulse_mono_44100",
        "mutation": "flip_bit_0x01_at_first_frame_payload_midpoint",
        "reference_test": "fail",
    },
)

TRANSPORT_PROFILES = {
    "continuous": {
        "chunk_pattern": [64],
        "input_stall_period": 0,
        "input_stall_length": 0,
        "output_stall_period": 0,
        "output_stall_length": 0,
        "prng_seed": 0,
        "description": "Continuous bounded chunks; output always ready.",
    },
    "byte_at_a_time": {
        "chunk_pattern": [1],
        "input_stall_period": 0,
        "input_stall_length": 0,
        "output_stall_period": 0,
        "output_stall_length": 0,
        "prng_seed": 0,
        "description": "Exactly one compressed byte per accepted input transfer.",
    },
    "periodic_input_stalls": {
        "chunk_pattern": [7, 3, 11, 5],
        "input_stall_period": 5,
        "input_stall_length": 2,
        "output_stall_period": 0,
        "output_stall_length": 0,
        "prng_seed": 0,
        "description": "Deterministic input-side backpressure only.",
    },
    "periodic_output_stalls": {
        "chunk_pattern": [16],
        "input_stall_period": 0,
        "input_stall_length": 0,
        "output_stall_period": 7,
        "output_stall_length": 3,
        "prng_seed": 0,
        "description": "Continuous input with deterministic PCM-output backpressure.",
    },
    "combined_stalls": {
        "chunk_pattern": [1, 4, 2, 9],
        "input_stall_period": 6,
        "input_stall_length": 1,
        "output_stall_period": 5,
        "output_stall_length": 2,
        "prng_seed": 0,
        "description": "Deterministic simultaneous input and output stalls.",
    },
    "fixed_seed_pseudorandom": {
        "chunk_pattern": [17],
        "input_stall_period": -1,
        "input_stall_length": -1,
        "output_stall_period": -1,
        "output_stall_length": -1,
        "prng_seed": 0x4D49535445524155,
        "description": "Fixed-seed xorshift64* chunks and stall decisions.",
    },
    "small_chunks": {
        "chunk_pattern": [1, 2, 3, 4],
        "input_stall_period": 0,
        "input_stall_length": 0,
        "output_stall_period": 0,
        "output_stall_length": 0,
        "prng_seed": 0,
        "description": "Repeating 1/2/3/4-byte compressed input chunks.",
    },
    "exact_final_byte_eos": {
        "chunk_pattern": [13],
        "input_stall_period": 0,
        "input_stall_length": 0,
        "output_stall_period": 0,
        "output_stall_length": 0,
        "prng_seed": 0,
        "description": "EOS asserted only with the transfer containing the exact final compressed byte.",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_tool(name: str, expected_version: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"required tool not found: {name}")
    got = subprocess.run([path, "--version"], check=True, text=True, capture_output=True).stdout.strip()
    if got != expected_version:
        raise SystemExit(f"{name} version mismatch: expected {expected_version!r}, got {got!r}")
    return path


def clamp_s16(value: int) -> int:
    return max(-32768, min(32767, value))


def lfsr16_step(state: int) -> int:
    # x^16 + x^14 + x^13 + x^11 + 1, fixed non-zero seed in callers.
    bit = ((state >> 0) ^ (state >> 2) ^ (state >> 3) ^ (state >> 5)) & 1
    return ((state >> 1) | (bit << 15)) & 0xFFFF


def lfsr24_step(state: int) -> int:
    # x^24 + x^23 + x^22 + x^17 + 1, fixed non-zero seed in callers.
    bit = ((state >> 0) ^ (state >> 1) ^ (state >> 2) ^ (state >> 7)) & 1
    return ((state >> 1) | (bit << 23)) & 0xFFFFFF


def sample_values(case: Case) -> Iterable[tuple[int, ...]]:
    state16 = 0x1ACE
    state24 = 0x5A17C3
    previous = 0
    period = (0, 4096, 12000, 24000, 32767, 12000, 0, -12000, -32768, -12000)
    for i in range(case.sample_count):
        if case.pattern == "silence":
            values = (0,) * case.channels
        elif case.pattern == "impulse":
            impulse = {0: 32767, 1: -32768, 17: 12345, case.sample_count // 2: -23456}.get(i, 0)
            values = (impulse,)
        elif case.pattern == "channel_id":
            left = ((i * 257) & 0xFFFF) - 32768
            right = 32767 - ((i * 509) & 0xFFFF)
            values = (left, right)
        elif case.pattern == "ramp_extremes":
            values = ((((i * 257) & 0xFFFF) - 32768),)
        elif case.pattern == "periodic":
            left = period[i % len(period)]
            right = period[(i + 3) % len(period)]
            values = (left, right)
        elif case.pattern == "lfsr":
            state16 = lfsr16_step(state16)
            values = (state16 - 32768,)
        elif case.pattern == "correlated_stereo":
            state16 = lfsr16_step(state16)
            left = state16 - 32768
            right = clamp_s16((3 * left + previous) // 4)
            previous = left
            values = (left, right)
        elif case.pattern == "short":
            seq = (0, 1, -1, 32767, -32768, 12345, -23456, 42)
            values = (seq[i % len(seq)],)
        elif case.pattern == "metadata":
            left = period[i % len(period)]
            right = clamp_s16(-left + ((i % 17) - 8) * 17)
            values = (left, right)
        elif case.pattern == "lfsr24":
            state24 = lfsr24_step(state24)
            values = (state24 - 0x800000,)
        else:
            raise ValueError(f"unknown PCM pattern: {case.pattern}")
        yield values


def make_pcm(case: Case) -> bytes:
    out = bytearray()
    if case.bits_per_sample == 16:
        for frame in sample_values(case):
            for value in frame:
                out += struct.pack("<h", value)
    elif case.bits_per_sample == 24:
        for frame in sample_values(case):
            for value in frame:
                if not -(1 << 23) <= value < (1 << 23):
                    raise ValueError(f"24-bit sample out of range: {value}")
                out += int(value & 0xFFFFFF).to_bytes(3, "little")
    else:
        raise ValueError(f"unsupported corpus bit depth: {case.bits_per_sample}")
    return bytes(out)


def encode_command(flac: str, case: Case, pcm_path: Path, flac_path: Path) -> list[str]:
    return [
        flac,
        "--force",
        "--silent",
        "--verify",
        "--threads=1",
        "--no-padding",
        "--no-seektable",
        "--no-preserve-modtime",
        "--force-raw-format",
        "--endian=little",
        "--sign=signed",
        f"--channels={case.channels}",
        f"--bps={case.bits_per_sample}",
        f"--sample-rate={case.sample_rate}",
        "-5",
        f"--output-name={flac_path}",
        str(pcm_path),
    ]


def decode_command(flac: str, flac_path: Path, pcm_path: Path) -> list[str]:
    return [
        flac,
        "--decode",
        "--force",
        "--silent",
        "--force-raw-format",
        "--endian=little",
        "--sign=signed",
        f"--output-name={pcm_path}",
        str(flac_path),
    ]


def normalize_command(command: list[str], output_dir: Path) -> list[str]:
    normalized = []
    for item in command:
        text = item.replace(str(output_dir), "$GENERATED_DIR")
        if text == shutil.which("flac"):
            text = "flac"
        elif text == shutil.which("metaflac"):
            text = "metaflac"
        normalized.append(text)
    return normalized


def set_metadata(metaflac: str, case: Case, flac_path: Path) -> list[list[str]]:
    commands: list[list[str]] = []
    if not case.metadata_case:
        command = [metaflac, "--dont-use-padding", "--remove", "--block-type=VORBIS_COMMENT", str(flac_path)]
        subprocess.run(command, check=True)
        commands.append(command)
        return commands

    clear = [metaflac, "--dont-use-padding", "--remove-all-tags", str(flac_path)]
    subprocess.run(clear, check=True)
    commands.append(clear)
    for tag in (
        "TITLE=MiSTer D1 deterministic metadata",
        "ARTIST=MiSTer-Media-Player-Audio",
        "COMMENT=synthetic project-generated corpus",
        "TRACKNUMBER=9",
    ):
        command = [metaflac, "--dont-use-padding", f"--set-tag={tag}", str(flac_path)]
        subprocess.run(command, check=True)
        commands.append(command)
    padding = [metaflac, "--add-padding=17", str(flac_path)]
    subprocess.run(padding, check=True)
    commands.append(padding)
    return commands


def metadata_inventory(metaflac: str, flac_path: Path) -> dict:
    result = subprocess.run([metaflac, "--list", str(flac_path)], check=True, text=True, capture_output=True)
    types: list[str] = []
    lengths: list[int] = []
    for line in result.stdout.splitlines():
        m = re.match(r"\s*type:\s*\d+\s*\(([^)]+)\)", line)
        if m:
            types.append(m.group(1))
        m = re.match(r"\s*length:\s*(\d+)", line)
        if m:
            lengths.append(int(m.group(1)))
    if not types:
        raise RuntimeError(f"no metadata blocks parsed from {flac_path}")
    return {"block_types": types, "block_lengths": lengths}


def analysis_inventory(flac: str, flac_path: Path) -> dict:
    with tempfile.TemporaryDirectory() as td:
        analysis_path = Path(td) / "analysis.txt"
        subprocess.run(
            [flac, "--analyze", "--force", "--silent", f"--output-name={analysis_path}", str(flac_path)],
            check=True,
        )
        text = analysis_path.read_text()

    block_sizes: set[int] = set()
    channel_assignments: set[str] = set()
    subframe_types: set[str] = set()
    fixed_orders: set[int] = set()
    lpc_orders: set[int] = set()
    rice_partition_orders: set[int] = set()
    wasted_bits: set[int] = set()
    frame_offsets: list[int] = []
    frame_count = 0

    for line in text.splitlines():
        if line.startswith("frame="):
            frame_count += 1
            fields = dict(re.findall(r"([A-Za-z_]+)=([^\s]+)", line))
            block_sizes.add(int(fields["blocksize"]))
            channel_assignments.add(fields["channel_assignment"])
            frame_offsets.append(int(fields["offset"]))
        elif line.lstrip().startswith("subframe="):
            fields = dict(re.findall(r"([A-Za-z_]+)=([^\s]+)", line))
            subframe_types.add(fields["type"])
            wasted_bits.add(int(fields.get("wasted_bits", "0")))
            if fields["type"] == "FIXED" and "order" in fields:
                fixed_orders.add(int(fields["order"]))
            if fields["type"] == "LPC" and "order" in fields:
                lpc_orders.add(int(fields["order"]))
            if fields.get("residual_type") == "RICE" and "partition_order" in fields:
                rice_partition_orders.add(int(fields["partition_order"]))

    if frame_count == 0:
        raise RuntimeError(f"no FLAC frames parsed from {flac_path}")
    return {
        "frame_count": frame_count,
        "frame_offsets": frame_offsets,
        "block_sizes": sorted(block_sizes),
        "channel_assignments": sorted(channel_assignments),
        "subframe_types": sorted(subframe_types),
        "fixed_orders": sorted(fixed_orders),
        "lpc_orders": sorted(lpc_orders),
        "rice_partition_orders": sorted(rice_partition_orders),
        "wasted_bits": sorted(wasted_bits),
    }


def flac_test(flac: str, flac_path: Path) -> bool:
    result = subprocess.run([flac, "--test", "--silent", str(flac_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def first_frame_offset(data: bytes) -> int:
    if not data.startswith(b"fLaC"):
        raise ValueError("not a native FLAC stream")
    pos = 4
    while True:
        if pos + 4 > len(data):
            raise ValueError("truncated FLAC metadata")
        header = data[pos]
        length = int.from_bytes(data[pos + 1 : pos + 4], "big")
        pos += 4 + length
        if header & 0x80:
            return pos


def derived_negative_bytes(spec: dict, base_data: bytes) -> bytes:
    if spec["mutation"] == "remove_final_5_bytes":
        if len(base_data) <= 5:
            raise ValueError("base FLAC too short to truncate")
        return base_data[:-5]
    if spec["mutation"] == "flip_bit_0x01_at_first_frame_payload_midpoint":
        start = first_frame_offset(base_data)
        if len(base_data) - start < 24:
            raise ValueError("base FLAC frame too short to corrupt safely")
        # Stay away from the frame header and final CRC16.  This changes frame data
        # while leaving the stream structurally recognizable to the reference decoder.
        index = start + (len(base_data) - start) // 2
        index = min(index, len(base_data) - 3)
        mutated = bytearray(base_data)
        mutated[index] ^= 0x01
        return bytes(mutated)
    raise ValueError(f"unknown negative mutation: {spec['mutation']}")


def _xorshift64star(state: int) -> tuple[int, int]:
    state &= 0xFFFFFFFFFFFFFFFF
    state ^= state >> 12
    state ^= (state << 25) & 0xFFFFFFFFFFFFFFFF
    state ^= state >> 27
    state &= 0xFFFFFFFFFFFFFFFF
    value = (state * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF
    return state, value


def transport_trace(profile_id: str, input_bytes: int = 257, output_items: int = 257) -> bytes:
    if profile_id not in TRANSPORT_PROFILES:
        raise ValueError(f"unknown transport profile: {profile_id}")
    p = TRANSPORT_PROFILES[profile_id]
    input_done = 0
    output_done = 0
    cycle = 0
    chunk_index = 0
    state = p["prng_seed"] or 1
    lines: list[str] = []

    while input_done < input_bytes or output_done < output_items:
        if cycle > 100000:
            raise RuntimeError(f"transport profile {profile_id} did not terminate")

        if profile_id == "fixed_seed_pseudorandom":
            state, r0 = _xorshift64star(state)
            state, r1 = _xorshift64star(state)
            chunk_limit = 1 + (r0 % 17)
            input_ready = (r0 >> 8) % 5 != 0
            output_ready = (r1 >> 11) % 4 != 0
        else:
            chunk_limit = p["chunk_pattern"][chunk_index % len(p["chunk_pattern"])]
            ip = p["input_stall_period"]
            il = p["input_stall_length"]
            op = p["output_stall_period"]
            ol = p["output_stall_length"]
            input_ready = not (ip > 0 and (cycle % ip) < il)
            output_ready = not (op > 0 and (cycle % op) < ol)

        remaining = input_bytes - input_done
        transfer = min(chunk_limit, remaining) if input_ready and remaining > 0 else 0
        if transfer:
            chunk_index += 1
            input_done += transfer
        if output_ready and output_done < output_items:
            output_done += 1
        eos = 1 if input_done == input_bytes and transfer > 0 else 0
        lines.append(f"{cycle}:{transfer}:{1 if output_ready else 0}:{eos}\n")
        cycle += 1

    if input_done != input_bytes or output_done != output_items:
        raise RuntimeError(f"transport profile {profile_id} lost data")
    if sum(int(line.split(":")[1]) for line in lines) != input_bytes:
        raise RuntimeError(f"transport profile {profile_id} duplicated input bytes")
    eos_count = sum(int(line.rstrip().split(":")[3]) for line in lines)
    if eos_count != 1:
        raise RuntimeError(f"transport profile {profile_id} EOS count is {eos_count}, expected 1")
    return "".join(lines).encode("ascii")


def transport_manifest() -> dict:
    result = {}
    for profile_id, definition in TRANSPORT_PROFILES.items():
        trace = transport_trace(profile_id)
        result[profile_id] = {
            **definition,
            "reference_input_bytes": 257,
            "reference_output_items": 257,
            "reference_trace_sha256": sha256_bytes(trace),
        }
    return result


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise SystemExit(f"manifest not found: {path}") from exc
    if data.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise SystemExit(
            f"manifest schema mismatch: expected {MANIFEST_SCHEMA_VERSION}, got {data.get('schema_version')!r}"
        )
    return data
