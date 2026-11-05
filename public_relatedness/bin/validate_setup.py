#!/usr/bin/env python3
"""Read-only validation of portable JSON parameters and frozen resource identities."""
import argparse
import importlib.util
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'bin' / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


manifest = module('public_manifest', 'prepare_manifest.py')
metrics = module('public_metrics', 'run_metrics.py')
assets = module('asset_paths', 'assets.py')


def require_file(value, label):
    if not value or not Path(value).is_file():
        raise ValueError(f'Missing local file: {label}' + assets.missing_hint(label))
    return Path(value)


def require_executable(value, label):
    executable = shutil.which(str(value)) if value else None
    if executable is None or not os.access(executable, os.X_OK):
        raise ValueError(f'Missing executable: {label}')


def validate(params, *, metadata_only=False, check_images=False, profiles='singularity',
             reference_manifest=None, image_inventory=None):
    params = assets.resolve(params)
    selected = profiles.split(',')
    if any(p not in {'local', 'singularity', 'docker', 'slurm'} for p in selected):
        raise ValueError('Unknown execution profile')
    if 'docker' in selected and 'singularity' in selected:
        raise ValueError('Select one container runtime')
    if params.get('paired_end', True) is not True or params.get('crop_50', False) is not False:
        raise ValueError('Expected paired-end sequencing without CROP:50')
    manifest.validate_temp_directory(params.get('temp_directory'))
    cached = bool(params.get('called_rds'))
    if cached:
        require_file(params['called_rds'], 'called_rds')
        samples, pairs = metrics.contracts(require_file(params.get('validated_samples'), 'validated_samples'),
                                            require_file(params.get('validated_pairs'), 'validated_pairs'))
    else:
        if not {'docker', 'singularity'} & set(selected):
            raise ValueError('FASTQ execution requires a container runtime profile')
        samples, pairs = manifest.validate(require_file(params.get('samples'), 'samples'), params.get('pairs'))
        ref = require_file(params.get('reference'), 'reference')
        if not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*\.(fa|fasta|fna)', ref.name):
            raise ValueError('Unsupported reference FASTA basename')
        checksum = params.get('pe150_bins_sha256', manifest.PE150_SHA256)
        if not isinstance(checksum, str) or checksum.lower() != manifest.PE150_SHA256:
            raise ValueError('Only the approved PE150 annotation checksum is supported')
        resources = reference_manifest or json.loads((ROOT / 'references/manifest.json').read_text())
        for asset in resources['resources']:
            if asset['config_param'] == 'pfreq':
                continue  # checked with all frozen metric assets below
            param = asset['config_param']
            path = require_file(str(params.get(param, '')) + asset.get('suffix', ''), asset['id'])
            if not metadata_only and metrics.sha256(path) != asset['sha256']:
                raise ValueError(f'Reference checksum mismatch: {asset["id"]}')
    runner = require_file(params.get('pcc_llr_runner'), 'pcc_llr_runner')
    if not metadata_only and metrics.sha256(runner) != metrics.HASHES['runner']:
        raise ValueError('Metric resource checksum mismatch: pcc_llr_runner')
    if pairs:
        keys = {'pfreq': 'pfreq', 'helper': 'llr_helper', 'preprocessing': 'breakpoint_preprocessing',
                'matching': 'breakpoint_matching', 'fraction_implementation': 'fraction_implementation'}
        for key, param in keys.items():
            path = require_file(params.get(param), param)
            if not metadata_only and metrics.sha256(path) != metrics.HASHES[key]:
                raise ValueError(f'Metric resource checksum mismatch: {param}')
    if not params.get('metrics_container'):
        require_executable(params.get('metrics_rscript', 'Rscript'), 'metrics_rscript')
        if pairs:
            require_executable(params.get('breakpoint_rscript', 'Rscript'), 'breakpoint_rscript')
    for profile, executable in [('singularity', 'singularity'), ('docker', 'docker'), ('slurm', 'sbatch')]:
        if profile in selected:
            require_executable(executable, profile)
    outdir = params.get('outdir')
    if not outdir or not str(outdir).strip():
        raise ValueError('Supply a fresh output directory')
    output = Path(outdir)
    if any((output / name).exists() for name in ['sample_results.tsv', 'pair_results.tsv']):
        raise ValueError('Output directory already contains result tables')
    if check_images or params.get('image_directory'):
        inventory = image_inventory or json.loads((ROOT / 'environments/runtime_images.json').read_text())
        directory = params.get('image_directory')
        for image in inventory.get('images', inventory.get('containers', [])):
            if cached and image['role'] != 'metrics':
                continue
            if image['role'] == 'metrics':
                path = require_file(params.get('metrics_container'), 'metrics_container; provide the validated metrics.sif in image_directory')
            else:
                if not directory:
                    raise ValueError('Supply image_directory for immutable archive verification')
                path = require_file(Path(directory) / image['filename'], image['role'])
            if not metadata_only and metrics.sha256(path) != image['sha256']:
                raise ValueError(f'Container archive checksum mismatch: {image["role"]}')
    return dict(status='metadata_valid' if metadata_only else 'resource_identities_verified',
                content_verification='not_performed' if metadata_only else 'sha256',
                samples=len(samples), pairs=len(pairs), profiles=selected,
                containers_scientifically_validated=False, mode='cached' if cached else 'fastq')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--params', type=Path, required=True)
    parser.add_argument('--profiles', default='singularity')
    parser.add_argument('--runtime-params', type=Path, help='Optional execution-environment JSON merged before run parameters')
    parser.add_argument('--metadata-only', action='store_true', help='Validate structure/presence only; does not verify file contents')
    parser.add_argument('--check-images', action='store_true')
    args = parser.parse_args()
    try:
        params = json.loads(args.runtime_params.read_text()) if args.runtime_params else {}
        params.update(json.loads(args.params.read_text()))
        result = validate(params, metadata_only=args.metadata_only,
                          check_images=args.check_images, profiles=args.profiles)
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.exit(2, f'Configuration validation failed: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
