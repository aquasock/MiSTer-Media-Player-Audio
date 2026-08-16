#!/usr/bin/env python3
"""Fail-closed verifier for the tracked D1 deterministic FLAC corpus manifest."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from flac_corpus_common import (
    EXPECTED_FLAC_VERSION,
    EXPECTED_METAFLAC_VERSION,
    GENERATED_DIR,
    MANIFEST_PATH,
    analysis_inventory,
    decode_command,
    flac_test,
    load_manifest,
    metadata_inventory,
    require_tool,
    sha256_file,
    transport_manifest,
)


def fail(message: str) -> None:
    raise SystemExit(f"VERIFY FAIL: {message}")


def verify(output_dir: Path, manifest_path: Path) -> None:
    flac = require_tool("flac", EXPECTED_FLAC_VERSION)
    metaflac = require_tool("metaflac", EXPECTED_METAFLAC_VERSION)
    manifest = load_manifest(manifest_path)

    if manifest.get("toolchain", {}).get("flac") != EXPECTED_FLAC_VERSION:
        fail("manifest FLAC version is not the pinned version")
    if manifest.get("toolchain", {}).get("metaflac") != EXPECTED_METAFLAC_VERSION:
        fail("manifest metaflac version is not the pinned version")
    if manifest.get("provenance", {}).get("third_party_media") is not False:
        fail("manifest provenance is not synthetic-only")
    if manifest.get("transport_profiles") != transport_manifest():
        fail("transport profile definitions/signatures differ from executable definitions")

    cases = [dict(zip(manifest["case_columns"], row)) for row in manifest["cases"]]
    negatives = [dict(zip(manifest["negative_columns"], row)) for row in manifest["derived_negatives"]]
    expected_files: set[str] = {"manifest.generated.json"}
    for case in cases:
        cid = case["case_id"]
        expected_files.update({f"{cid}.source.pcm", f"{cid}.flac", f"{cid}.decoded.pcm"})
    for negative in negatives:
        expected_files.add(negative["file"])

    actual_files = {p.name for p in output_dir.iterdir() if p.is_file()}
    missing = sorted(expected_files - actual_files)
    extra = sorted(actual_files - expected_files)
    if missing:
        fail(f"missing generated files: {missing}")
    if extra:
        fail(f"unexpected generated files: {extra}")

    generated_manifest = json.loads((output_dir / "manifest.generated.json").read_text())
    if generated_manifest != manifest:
        fail("generated manifest content differs from tracked manifest")

    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        for case in cases:
            case_id = case["case_id"]
            source_path = output_dir / f"{case_id}.source.pcm"
            flac_path = output_dir / f"{case_id}.flac"
            golden_path = output_dir / f"{case_id}.decoded.pcm"

            for label, path, want in (
                ("source_pcm", source_path, case["source_sha256"]),
                ("encoded_flac", flac_path, case["flac_sha256"]),
                ("golden_decoded_pcm", golden_path, case["decoded_sha256"]),
            ):
                got = sha256_file(path)
                if got != want:
                    fail(f"{case_id}: {label} SHA-256 mismatch: {got} != {want}")

            if source_path.read_bytes() != golden_path.read_bytes():
                fail(f"{case_id}: source/golden PCM content differs")
            if not flac_test(flac, flac_path):
                fail(f"{case_id}: reference flac --test rejected a manifest-valid stream")

            decoded_path = temp_dir / f"{case_id}.verify.pcm"
            subprocess.run(decode_command(flac, flac_path, decoded_path), check=True)
            if sha256_file(decoded_path) != case["decoded_sha256"]:
                fail(f"{case_id}: fresh reference decode does not match golden decoded PCM")

            analysis = analysis_inventory(flac, flac_path)
            analysis.pop("frame_offsets")
            metadata = metadata_inventory(metaflac, flac_path)
            expected_features = {
                "frame_count": case["frame_count"],
                "block_sizes": case["block_sizes"],
                "channel_assignments": case["channel_assignments"],
                "subframe_types": case["subframe_types"],
                "fixed_orders": case["fixed_orders"],
                "lpc_orders": case["lpc_orders"],
                "rice_partition_orders": case["rice_partition_orders"],
                "wasted_bits": case["wasted_bits"],
            }
            if analysis != expected_features:
                fail(f"{case_id}: observed FLAC frame feature inventory changed")
            if metadata["block_types"] != case["metadata_block_types"] or metadata["block_lengths"] != case["metadata_block_lengths"]:
                fail(f"{case_id}: metadata feature inventory changed")

    for negative in negatives:
        path = output_dir / negative["file"]
        if sha256_file(path) != negative["sha256"]:
            fail(f"{negative['case_id']}: negative SHA-256 mismatch")
        actual = "pass" if flac_test(flac, path) else "fail"
        if actual != negative["reference_test"]:
            fail(f"{negative['case_id']}: reference test result {actual}, expected {negative['reference_test']}")

    print(
        f"VERIFY PASS: {len(cases)} valid/unsupported cases, "
        f"{len(negatives)} invalid cases, and "
        f"{len(manifest['transport_profiles'])} transport profiles"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=GENERATED_DIR)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    if not args.output_dir.is_dir():
        fail(f"generated corpus directory not found: {args.output_dir}")
    verify(args.output_dir, args.manifest)


if __name__ == "__main__":
    main()
