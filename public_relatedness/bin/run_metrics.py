#!/usr/bin/env python3
"""Ordered cohort adapters and precise result tables; no scientific replacements."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path

METHOD = 'pcc_llr_relatedness_v1+historical_fraction_shared_multioverlap_v1'
HASHES = {
    'runner': '411676813fde9d1f3bd2b74fe08a59970a060e5bff564b561264c7a35b2ea15f',
    'pfreq': '582b6b53c4a4f70149b115c504685f24e983c522d63c1cb42c25a90db103e04f',
    'helper': 'fed28e2eca2ae213957c5e382e8e3deee698aae1d9eed0d39b57401e7cdc7f35',
    'preprocessing': '16655beb5ea51c3f9297418d04a5a288d23689259f7845e6db553564232cabf6',
    'matching': 'ac0a06306bcbc048a06180d7a06584695a3aa8e3279ca57068f9ade6544e8330',
    'fraction_implementation': 'e127424de7f54233dfc0281887d273e9e9deb81437250e1d08ac145070bb7f31',
}
PAIR_FIELDS = ['pair_id', 'sample1', 'sample2', 'pcc', 'llr', 'shared', 'private_sample1',
               'private_sample2', 'total', 'fraction_shared', 'fraction_shared_rational',
               'method_version', 'processing_status', 'pcc_status', 'llr_status', 'fraction_shared_status']
SAMPLE_FIELDS = ['sample_id', 'processing_status', 'qc_status', 'usable_bins', 'finite_segmented_bins',
                 'call_states', 'profile_location', 'profile_sha256', 'method_version', 'provenance_location']


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path, delimiter='\t'):
    with Path(path).open(newline='') as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_table(path, fields, rows):
    with Path(path).open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def contracts(samples_path, pairs_path):
    samples = [r['sample_id'] for r in read_table(samples_path)]
    if not samples or len(samples) != len(set(samples)) or any(not s or s != s.strip() for s in samples):
        raise ValueError('Empty/duplicate/invalid sample identifiers')
    pairs = [{k: r[k] for k in ['pair_id', 'sample1', 'sample2']} for r in read_table(pairs_path, ',')]
    ids, keys = set(), set()
    for row in pairs:
        a, b, pid = row['sample1'], row['sample2'], row['pair_id']
        key = tuple(sorted((a, b)))
        if not pid or pid != pid.strip() or pid in ids or key in keys:
            raise ValueError('Duplicate/conflicting pair definition')
        if a == b or a not in samples or b not in samples:
            raise ValueError('Missing sample or self-comparison')
        ids.add(pid)
        keys.add(key)
    return samples, pairs


def require_order(rows, pairs):
    if [(r['pair_id'], r['sample1'], r['sample2']) for r in rows] != [
        (r['pair_id'], r['sample1'], r['sample2']) for r in pairs
    ]:
        raise ValueError('Metric output changed pair count, order or orientation')


def fraction_result(counts):
    h, private1, private2 = counts
    total = h + private1 + private2
    status = ('unsupported_both_zero' if h == private1 == private2 == 0 else
              'unsupported_negative_private' if min(private1, private2) < 0 else 'computed')
    if status != 'computed':
        return total, 'NA', 'NA', status
    from fractions import Fraction
    exact = Fraction(h, total)
    return total, format(float(exact), '.17g'), str(exact), status


def aggregate(pairs, values, counts, groups, implementation):
    require_order(values, pairs)
    require_order(counts, pairs)
    rows = []
    for pair, metric, native in zip(pairs, values, counts):
        reconstructed, _ = implementation.counts(groups, pair['sample1'], pair['sample2'])
        inherited = tuple(int(native[k]) for k in ['shared', 'private_sample1', 'private_sample2'])
        if tuple(reconstructed) != inherited:
            raise ValueError('Recovered R/Python all-overlap counts disagree')
        total, fraction, exact, bp_status = fraction_result(inherited)
        if total != int(native['total']):
            raise ValueError('Historical total arithmetic mismatch')
        pcc_status = 'computed' if finite(metric['pcc']) else 'failed_nonfinite'
        llr_status = metric['llr_status']
        if llr_status == 'computed' and not finite(metric['llr']):
            llr_status = 'failed_nonfinite'
        status = ('failed_metrics' if pcc_status != 'computed' or llr_status != 'computed' else
                  'unsupported_fraction_shared' if bp_status != 'computed' else 'complete')
        rows.append(dict(pair, pcc=metric['pcc'], llr=metric['llr'], shared=inherited[0],
            private_sample1=inherited[1], private_sample2=inherited[2], total=total,
            fraction_shared=fraction, fraction_shared_rational=exact, method_version=METHOD,
            processing_status=status, pcc_status=pcc_status, llr_status=llr_status,
            fraction_shared_status=bp_status))
    return rows


def finite(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def run(args):
    samples, pairs = contracts(args.samples, args.pairs)
    # Fail before producing partial tables if an asset differs from the frozen authority.
    assets = ({k: getattr(args, k) for k in HASHES} if pairs else {'runner': args.runner}) if not args.stub else {}
    hashes = {}
    for key, path in assets.items():
        if path is None or sha256(path) != HASHES[key]:
            raise ValueError(f'Missing or checksum-mismatched metric asset: {key}')
        hashes[key] = HASHES[key]
    args.output.mkdir(parents=True, exist_ok=False)
    private = args.output / 'intermediate'
    private.mkdir()
    expected = private / 'expected.txt'
    expected.write_text(''.join(s + '\n' for s in samples))
    pairs_path = private / 'pairs.csv'
    with pairs_path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['pair_id', 'sample1', 'sample2'])
        writer.writeheader()
        writer.writerows(pairs)
    if args.stub:
        qc = [dict(sample_id=s, usable_bins='NA', finite_segmented_bins='NA', call_states='NA') for s in samples]
        rows = [dict(p, **{k: 'NA' for k in PAIR_FIELDS if k not in p}) for p in pairs]
        for row in rows:
            row.update(method_version=METHOD, processing_status='stub_not_computed',
                       pcc_status='stub_not_computed', llr_status='stub_not_computed', fraction_shared_status='stub_not_computed')
    else:
        adapter = Path(args.pcc_adapter) if args.pcc_adapter else Path(__file__).with_name('pcc_llr_adapter.R')
        subprocess.run([args.rscript, str(adapter), str(args.called_rds), str(expected), str(pairs_path),
            str(args.runner), str(args.pfreq or ''), str(args.helper or ''), str(private)], check=True)
        qc = read_table(private / 'sample_qc.tsv')
        if [r['sample_id'] for r in qc] != samples:
            raise ValueError('Sample QC output changed cohort membership or order')
        rows = []
        if pairs:
            adapter = Path(args.breakpoint_adapter) if args.breakpoint_adapter else Path(__file__).with_name('breakpoints_adapter.R')
            subprocess.run([args.breakpoint_rscript, str(adapter), str(args.called_rds), str(expected), str(pairs_path),
                str(args.preprocessing), str(args.matching), str(private)], check=True)
            spec = importlib.util.spec_from_file_location('historical_fraction_shared', args.fraction_implementation)
            implementation = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(implementation)
            groups = implementation.group_observations(read_table(private / 'observations.tsv'))
            # Profiles with no observations are still present in the checked cohort.
            for sid in samples:
                groups[sid]
            rows = aggregate(pairs, read_table(private / 'pcc_llr.tsv'),
                             read_table(private / 'breakpoint_counts.tsv'), groups, implementation)
    digest = sha256(args.called_rds)
    sample_rows = [dict(q, processing_status='stub_not_computed' if args.stub else 'processed',
        qc_status='not_assessed', profile_location=args.profile_location, profile_sha256=digest,
        method_version=METHOD, provenance_location=args.provenance_location) for q in qc]
    write_table(args.output / 'sample_results.tsv', SAMPLE_FIELDS, sample_rows)
    write_table(args.output / 'pair_results.tsv', PAIR_FIELDS, rows)
    provenance = dict(method_version=METHOD, asset_sha256=hashes, profile_sha256=digest,
        sample_count=len(samples), pair_count=len(pairs), pair_order='input order and orientation',
        llr_seed=1337, llr_execution='one sequential R process', stub=args.stub,
        profile_location=args.profile_location,
        status_counts={s: sum(r['processing_status'] == s for r in rows) for s in sorted({r['processing_status'] for r in rows})})
    (args.output / 'metric_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ['samples', 'pairs', 'called-rds', 'output']:
        p.add_argument('--' + flag, type=Path, required=True)
    for key in HASHES:
        p.add_argument('--' + key.replace('_', '-'), type=Path)
    p.add_argument('--pcc-adapter', type=Path)
    p.add_argument('--breakpoint-adapter', type=Path)
    p.add_argument('--rscript', default='Rscript')
    p.add_argument('--breakpoint-rscript', default='Rscript')
    p.add_argument('--profile-location')
    p.add_argument('--provenance-location', default='metric_provenance.json')
    p.add_argument('--stub', action='store_true', help='Empty orchestration artifacts only; no scientific scores')
    args = p.parse_args()
    args.profile_location = args.profile_location or str(args.called_rds.resolve())
    try:
        run(args)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        p.exit(1, f'Metric integration failed: {error}\n')


if __name__ == '__main__':
    main()
