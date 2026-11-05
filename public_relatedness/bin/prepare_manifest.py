#!/usr/bin/env python3
"""Validate local TSV inputs; emit ordered, staging-safe cohort contracts."""
import argparse
import csv
import hashlib
import json
import os
import re
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
PE150_SHA256 = '1d62a94b9a88845978c7bf709d00b35b0f3b1243ef894b442c3ac2861a23337c'


def validate_temp_directory(value):
    if value is None:
        return
    # Nextflow 24.10 embeds scratch paths in its launcher shell. Restrict the
    # path before that launcher or a container bind specification can use it.
    if not isinstance(value, str) or not re.fullmatch(r'/[A-Za-z0-9_./-]+', value):
        raise ValueError("temp_directory must be absolute and use only letters, digits, '/', '.', '_' or '-'")
    path = Path(value)
    if not path.is_absolute() or not path.is_dir() or not os.access(path, os.W_OK | os.X_OK):
        raise ValueError('temp_directory must be an existing writable absolute directory on the execution host')


def identifier(value):
    if not ID.fullmatch(value) or value == "NA":
        raise ValueError(f"Invalid identifier: {value!r}; use 1-80 letters, digits, '_' or '-'")
    return value


def table(path, columns):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != columns:
            raise ValueError(f"Expected TSV header {columns}, got {reader.fieldnames}")
        rows = list(reader)
    for row in rows:
        if None in row or any(v is None or not v or v != v.strip() for v in row.values()):
            raise ValueError("Blank, malformed or whitespace-padded manifest entry")
    return rows


def validate(samples_path, pairs_path=None, base=None):
    samples_path = Path(samples_path)
    base = Path(base) if base else samples_path.resolve().parent
    samples = table(samples_path, ["sample_id", "fastq_1", "fastq_2"])
    if not samples:
        raise ValueError("Sample manifest is empty")
    ids, used = set(), set()
    for row in samples:
        sid = identifier(row["sample_id"])
        if sid in ids:
            raise ValueError(f"Duplicate sample identifier: {sid}")
        ids.add(sid)
        for key in ("fastq_1", "fastq_2"):
            path = Path(row[key])
            path = (base / path).resolve() if not path.is_absolute() else path.resolve()
            if not path.is_file():
                raise ValueError(f"Missing FASTQ file for {sid}: {path}")
            if not str(path).lower().endswith((".fastq", ".fastq.gz", ".fq", ".fq.gz")):
                raise ValueError(f"Unsupported FASTQ extension: {path}")
            if any(c in str(path) for c in "\n\r\t"):
                raise ValueError("FASTQ path contains a control character")
            if path in used:
                raise ValueError(f"FASTQ reused across mates or samples: {path}")
            used.add(path)
            row[key] = str(path)
    pairs = table(pairs_path, ["pair_id", "sample1", "sample2"]) if pairs_path else []
    if pairs_path and not pairs:
        raise ValueError("Supplied pair manifest is empty")
    pair_ids, comparisons = set(), set()
    for row in pairs:
        pid = identifier(row["pair_id"])
        a, b = row["sample1"], row["sample2"]
        key = tuple(sorted((a, b)))
        if pid in pair_ids or key in comparisons:
            raise ValueError("Duplicate pair ID or unordered comparison")
        if a not in ids or b not in ids or a == b:
            raise ValueError(f"Invalid sample references in pair {pid}")
        pair_ids.add(pid)
        comparisons.add(key)
    return samples, pairs


def write_outputs(output, samples, pairs, annotation_sha256=None, development_stub=False):
    output.mkdir(parents=True, exist_ok=True)
    for name, rows, fields, delimiter in (
        ("samples.tsv", samples, ["sample_id", "fastq_1", "fastq_2"], "\t"),
        ("pairs.csv", pairs, ["pair_id", "sample1", "sample2"], ","),
    ):
        with (output / name).open("x", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)
    (output / "expected_samples.txt").write_text("".join(r["sample_id"] + "\n" for r in samples))
    (output / "cohort.json").write_text(json.dumps({
        "sample_ids": [r["sample_id"] for r in samples], "pair_count": len(pairs),
        "genome": "hg38", "layout": "pe", "bin_size_kb": 500,
        "pe150_annotation_sha256": annotation_sha256,
        "annotation_validation": ("not_checked" if annotation_sha256 is None else
                                  "development_stub" if development_stub else "approved_pe150_sha256"),
        "metric_execution": "ordered cohort adapters; status in result tables",
    }, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", required=True, type=Path)
    parser.add_argument("--pairs", type=Path)
    parser.add_argument("--base", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--pe150-bins", type=Path)
    parser.add_argument("--pe150-sha256")
    parser.add_argument("--development-stub", action="store_true", help="Nextflow stub artifacts only; not annotation validation")
    parser.add_argument("--temp-directory")
    args = parser.parse_args()
    try:
        validate_temp_directory(args.temp_directory)
        samples, pairs = validate(args.samples, args.pairs, args.base)
        if args.pe150_bins:
            if not args.development_stub and (args.pe150_sha256 or '').lower() != PE150_SHA256:
                raise ValueError("PE150 annotation checksum mismatch: only the approved PE150 asset is supported")
            if not args.pe150_sha256 or not re.fullmatch(r"[a-fA-F0-9]{64}", args.pe150_sha256):
                raise ValueError("Supply the validated hg38 PE150 500-kb annotation SHA256")
            digest = hashlib.sha256(args.pe150_bins.read_bytes()).hexdigest()
            if digest != args.pe150_sha256.lower():
                raise ValueError("PE150 annotation checksum mismatch")
        write_outputs(args.output, samples, pairs, args.pe150_sha256, args.development_stub)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Manifest validation failed: {error}\n")


if __name__ == "__main__":
    main()
