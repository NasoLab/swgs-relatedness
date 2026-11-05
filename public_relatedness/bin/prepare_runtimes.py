#!/usr/bin/env python3
"""Acquire or reuse the frozen metrics SIF; SHA256 verification is mandatory."""
import argparse
import errno
import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = json.loads((ROOT / 'environments/runtime_images.json').read_text())
METRICS = next(image for image in INVENTORY['images'] if image['role'] == 'metrics')
spec = importlib.util.spec_from_file_location('resource_acquisition', ROOT / 'bin/prepare_resources.py')
acquisition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquisition)


def verify(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError('Missing metrics SIF: ' + str(path) + '; use --fetch-metrics or --existing-metrics. See docs/USAGE.md#runtime-setup')
    if acquisition.sha256(path) != METRICS['sha256']:
        raise ValueError('Metrics SIF checksum mismatch: ' + str(path) + '; existing files are never overwritten')
    return path


def setup(directory, *, download=False, existing=None):
    directory = Path(directory)
    dest = directory / METRICS['filename']
    if download and existing is not None:
        raise ValueError('Select either downloading or reusing an existing SIF')
    if dest.exists():
        return verify(dest)
    if existing is not None:
        source = verify(existing).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, dest)
        except FileExistsError:
            return verify(dest)
        except OSError as error:
            if error.errno == errno.EXDEV:
                raise ValueError('Existing SIF is on another filesystem; select a cache on that volume or set metrics_container to its verified path. No duplicate was copied') from error
            raise
        return dest
    if download:
        return acquisition.fetch(METRICS, directory)
    return verify(dest)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    location = p.add_mutually_exclusive_group(required=True)
    location.add_argument('--resources', type=Path, help='Use RESOURCE_DIRECTORY/containers, the full-workflow default')
    location.add_argument('--directory', type=Path, help='Explicit container cache; set image_directory to the same directory')
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument('--fetch-metrics', action='store_true', help='Explicit download from the pinned HTTPS URL')
    action.add_argument('--existing-metrics', type=Path, help='Verify and hard-link an existing SIF on the same filesystem; never rebuild or modify it')
    action.add_argument('--verify', action='store_true', help='Verify the existing cached metrics.sif without network access')
    args = p.parse_args()
    try:
        cache = args.directory if args.directory is not None else args.resources / 'containers'
        path = setup(cache, download=args.fetch_metrics, existing=args.existing_metrics)
    except (OSError, ValueError) as error:
        p.exit(2, 'Runtime setup failed: ' + str(error) + '\n')
    print(json.dumps(dict(metrics_container=str(path.resolve()), sha256=METRICS['sha256'],
                         verification='sha256', image_rebuilt=False,
                         upstream_oci_images={i['role']: i['oci_uri'] for i in INVENTORY['images'] if 'oci_uri' in i}), indent=2))


if __name__ == '__main__':
    main()
