#!/usr/bin/env python3
"""Read-only cached numerical gates; configuration/assets stay local and private."""
import argparse
import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_HASHES = {
    'pcc': '6156ebc932f78d59f1a14e8d292c38141c9f6f4cde16517ec50b65d7d7bc3976',
    'llr': '3e6fbf631ea77e3989a96e233a2fb460fe7efd4b2ff049efd1f6af06e6fa8203',
    'fraction_shared': 'b50cf730790800a1c12d04f472baa6e935f7d00c25997430baf46b627dbd4f49',
}
spec = importlib.util.spec_from_file_location('metrics', ROOT / 'bin/run_metrics.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
spec_assets = importlib.util.spec_from_file_location('asset_defaults', ROOT / 'bin/assets.py')
assets = importlib.util.module_from_spec(spec_assets)
spec_assets.loader.exec_module(assets)


def prepare(case, folder, rscript):
    folder.mkdir()
    samples = folder / 'samples.tsv'
    script = folder / 'inventory.R'
    script.write_text('suppressPackageStartupMessages({library(QDNAseq);library(Biobase)})\n'
                      'a<-commandArgs(TRUE); x<-readRDS(a[[1]]); '
                      'write.table(data.frame(sample_id=sampleNames(x)),a[[2]],sep="\\t",quote=FALSE,row.names=FALSE)\n')
    subprocess.run([rscript, str(script), case['called'], str(samples)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (folder / 'expected.txt').write_text(''.join(r['sample_id'] + '\n' for r in m.read_table(samples)))
    fixture = m.read_table(case['fixture'], ',' if case['fixture'].endswith('.csv') else '\t')
    pairs = [{'pair_id': f'comparison{i+1}', 'sample1': r.get('sample1', r.get('Sample1')),
              'sample2': r.get('sample2', r.get('Sample2'))} for i, r in enumerate(fixture)]
    path = folder / 'pairs.csv'
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['pair_id', 'sample1', 'sample2'])
        writer.writeheader()
        writer.writerows(pairs)
    return samples, path, fixture, pairs


def invoke(command, log):
    with log.open('w') as handle:
        subprocess.run(list(map(str, command)), check=True, stdout=handle, stderr=handle)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--existing-llr-results', type=Path,
                   help='Reuse a completed run of this adapter after verifying profile and resource hashes')
    args = p.parse_args()
    config = json.loads(args.config.read_text())
    resolved = assets.resolve({'resource_directory': config.get('resource_directory')})
    config.setdefault('resources', {})
    for key, param in dict(assets.PARAMS, helper='llr_helper', pfreq='pfreq').items():
        if key not in config['resources'] and resolved.get(param): config['resources'][key] = resolved[param]

    for key, expected in FIXTURE_HASHES.items():
        assert m.sha256(config[key]['fixture']) == expected, 'Frozen fixture checksum mismatch'
    args.output.mkdir(exist_ok=False, parents=True)
    report = {}
    # Full production adapter: all 62 pairs in fixture order, one seeded R loop.
    case = config['llr']
    folder = args.output / 'llr'
    samples, pairs_path, fixture, pairs = prepare(case, folder, config['rscript'])
    command = [sys.executable, ROOT / 'bin/run_metrics.py', '--samples', samples, '--pairs', pairs_path,
               '--called-rds', case['called'], '--rscript', config['rscript'],
               '--breakpoint-rscript', config['breakpoint_rscript'], '--output', folder / 'results']
    for key, path in config['resources'].items():
        command.extend(['--' + key.replace('_', '-'), path])
    if args.existing_llr_results:
        results = args.existing_llr_results
        provenance = json.loads((results / 'metric_provenance.json').read_text())
        assert provenance['asset_sha256'] == m.HASHES and not provenance['stub']
        assert provenance['profile_sha256'] == m.sha256(case['called'])
    else:
        invoke(command, folder / 'execution.log')
        results = folder / 'results'
    rows = m.read_table(results / 'pair_results.tsv')
    m.require_order(rows, pairs)
    differences = [abs(float(r['llr']) - float(f['LLR'])) for r, f in zip(rows, fixture)]
    assert len(rows) == len(fixture) == 62
    assert max(differences) <= 1e-12, 'LLR seeded numerical discrepancy'
    assert all(r['llr_status'] == 'computed' for r in rows), 'LLR did not compute every pair'
    assert list(rows[0]) == m.PAIR_FIELDS
    observed_samples = m.read_table(results / 'sample_results.tsv')
    assert list(observed_samples[0]) == m.SAMPLE_FIELDS
    assert [r['sample_id'] for r in observed_samples] == [r['sample_id'] for r in m.read_table(samples)]
    assert all(r['processing_status'] in {'complete', 'unsupported_fraction_shared'} for r in rows)
    report['llr'] = dict(pairs=62, matched=62, max_abs_difference=max(differences), tolerance=1e-12)
    # A cached object with an extra sample must fail before scoring/publication.
    missing_samples = folder / 'missing_samples.tsv'
    complete = m.read_table(samples)
    m.write_table(missing_samples, ['sample_id'], complete[:-1])
    no_pairs = folder / 'no_pairs.csv'
    no_pairs.write_text('pair_id,sample1,sample2\n')
    rejected = folder / 'missing_results'
    failure = subprocess.run([sys.executable, str(ROOT / 'bin/run_metrics.py'),
        '--samples', str(missing_samples), '--pairs', str(no_pairs), '--called-rds', case['called'],
        '--rscript', config['rscript'], '--output', str(rejected)], capture_output=True, text=True)
    assert failure.returncode != 0 and not (rejected / 'sample_results.tsv').exists()
    assert 'identical(sampleNames(object), expected)' in failure.stderr
    report['missing_sample_guard'] = dict(rejected=True, results_published=False)
    # PCC gate uses the recorded PCC environment and the same source functions.
    case = config['pcc']
    folder = args.output / 'pcc'
    samples, pairs_path, fixture, pairs = prepare(case, folder, config['pcc_rscript'])
    output = folder / 'results'
    invoke([config['pcc_rscript'], ROOT / 'bin/pcc_llr_adapter.R', case['called'], folder / 'expected.txt', pairs_path,
            config['resources']['runner'], '', '', output, 'pcc_regression'], folder / 'execution.log')
    rows = m.read_table(output / 'pcc_llr.tsv')
    m.require_order(rows, pairs)
    differences = [abs(float(r['pcc']) - float(f['pcc'])) for r, f in zip(rows, fixture)]
    assert len(rows) == len(fixture) == 66
    assert max(differences) <= 1e-12, 'PCC numerical discrepancy'
    report['pcc'] = dict(pairs=66, matched=66, max_abs_difference=max(differences), tolerance=1e-12)
    # Recompute breakpoint preprocessing + recovered R matching, then cross-check
    # the production Python all-overlap path and every historical arithmetic field.
    case = config['fraction_shared']
    folder = args.output / 'fraction_shared'
    samples, pairs_path, fixture, pairs = prepare(case, folder, config['breakpoint_rscript'])
    output = folder / 'results'
    resources = config['resources']
    invoke([config['breakpoint_rscript'], ROOT / 'bin/breakpoints_adapter.R', case['called'], folder / 'expected.txt',
            pairs_path, resources['preprocessing'], resources['matching'], output], folder / 'execution.log')
    spec = importlib.util.spec_from_file_location('historical', resources['fraction_implementation'])
    implementation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(implementation)
    groups = implementation.group_observations(m.read_table(output / 'observations.tsv'))
    native = m.read_table(output / 'breakpoint_counts.tsv')
    m.require_order(native, pairs)
    assert len(native) == len(fixture) == 38
    for pair, r, f in zip(pairs, native, fixture):
        observed, _ = implementation.counts(groups, pair['sample1'], pair['sample2'])
        expected = tuple(implementation.integer(f[k]) for k in ['shared', 'private_sample1', 'private_sample2'])
        assert tuple(observed) == expected == tuple(int(r[k]) for k in ['shared', 'private_sample1', 'private_sample2']), 'Historical count discrepancy'
        total, value, exact, status = m.fraction_result(observed)
        assert total == sum(expected) == int(r['total']) and status == 'computed'
        assert implementation.fraction_comparison(implementation.precise_fraction(observed), f['fraction_shared'])[2], 'Historical fraction precision discrepancy'
    report['fraction_shared'] = dict(pairs=38, exact_counts=38, supplied_fraction_precision_matches=38)
    (args.output / 'regression_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
