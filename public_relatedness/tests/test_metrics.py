"""Adapter contracts, precision and unsupported-case statuses; not biological fixtures."""
import csv
import importlib.util
import tempfile
import subprocess
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('metrics', ROOT / 'bin/run_metrics.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MetricContractTests(unittest.TestCase):
    def setUp(self):
        self.pairs = [dict(pair_id='p2', sample1='B', sample2='A'), dict(pair_id='p1', sample1='B', sample2='C')]
        self.values = [dict(p, pcc='0.12345678901234566', llr='-9.8765432101234567', llr_status='computed') for p in self.pairs]
        self.counts = [dict(p, shared='2', private_sample1='3', private_sample2='4', total='9') for p in self.pairs]
        self.implementation = types.SimpleNamespace(counts=lambda groups, a, b: ((2, 3, 4), []))

    def test_order_orientation_and_precision(self):
        rows = m.aggregate(self.pairs, self.values, self.counts, {}, self.implementation)
        m.require_order(rows, self.pairs)
        self.assertEqual(rows[0]['pcc'], self.values[0]['pcc'])
        self.assertEqual(rows[0]['llr'], self.values[0]['llr'])
        self.assertEqual(rows[0]['fraction_shared_rational'], '2/9')
        self.assertEqual(rows[0]['fraction_shared'], format(2/9, '.17g'))
        self.assertEqual(rows[0]['processing_status'], 'complete')
        self.assertEqual(set(rows[0]), set(m.PAIR_FIELDS))

    def test_reject_reordered_or_reoriented_metrics(self):
        for changed in [self.values[::-1], self.values[:1],
                        [dict(self.values[0], sample1='A', sample2='B'), self.values[1]]]:
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                m.aggregate(self.pairs, changed, self.counts, {}, self.implementation)

    def test_r_python_disagreement_fails(self):
        bad = types.SimpleNamespace(counts=lambda *args: ((1, 4, 5), []))
        with self.assertRaisesRegex(ValueError, 'disagree'):
            m.aggregate(self.pairs, self.values, self.counts, {}, bad)

    def test_unsupported_cases_preserve_counts(self):
        self.assertEqual(m.fraction_result((0, 0, 0)), (0, 'NA', 'NA', 'unsupported_both_zero'))
        self.assertEqual(m.fraction_result((4, 0, -2)), (2, 'NA', 'NA', 'unsupported_negative_private'))
        self.assertEqual(m.fraction_result((0, 0, 5)), (5, '0', '0', 'computed'))

    def test_failed_llr_never_becomes_complete(self):
        self.values[0].update(llr='NA', llr_status='failed')
        row = m.aggregate(self.pairs, self.values, self.counts, {}, self.implementation)[0]
        self.assertEqual(row['processing_status'], 'failed_metrics')
        self.assertEqual(row['llr_status'], 'failed')

    def test_nonfinite_pcc_is_explicit(self):
        self.values[0]['pcc'] = 'NaN'
        row = m.aggregate(self.pairs, self.values, self.counts, {}, self.implementation)[0]
        self.assertEqual(row['pcc_status'], 'failed_nonfinite')
        self.assertEqual(row['processing_status'], 'failed_metrics')

    def test_contracts_missing_samples_duplicates_and_multicomparison(self):
        with tempfile.TemporaryDirectory() as folder:
            samples, pairs = Path(folder) / 'samples.tsv', Path(folder) / 'pairs.csv'
            samples.write_text('sample_id\nA\nB\nC\n')
            pairs.write_text('pair_id,sample1,sample2\np2,B,A\np1,B,C\n')
            self.assertEqual(m.contracts(samples, pairs), (['A', 'B', 'C'], self.pairs))
            for content in ['pair_id,sample1,sample2\np1,A,missing\n',
                            'pair_id,sample1,sample2\np1,A,B\np2,B,A\n',
                            'pair_id,sample1,sample2\np1,A,A\n']:
                pairs.write_text(content)
                with self.assertRaises(ValueError):
                    m.contracts(samples, pairs)
            samples.write_text('sample_id\nA\nA\n')
            with self.assertRaises(ValueError):
                m.contracts(samples, pairs)

    def test_output_schema_and_precision_roundtrip(self):
        rows = m.aggregate(self.pairs, self.values, self.counts, {}, self.implementation)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'pair_results.tsv'
            m.write_table(path, m.PAIR_FIELDS, rows)
            with path.open() as handle:
                reader = csv.DictReader(handle, delimiter='\t')
                self.assertEqual(reader.fieldnames, m.PAIR_FIELDS)
                read = list(reader)
            self.assertEqual(read[0]['llr'], self.values[0]['llr'])
            self.assertEqual(read[0]['pcc'], self.values[0]['pcc'])

    def test_standalone_output_locations(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'samples.tsv').write_text('sample_id\nA\n')
            (root / 'pairs.csv').write_text('pair_id,sample1,sample2\n')
            (root / 'called.rds').touch()  # explicit stub-only marker
            result = subprocess.run([sys.executable, str(ROOT / 'bin/run_metrics.py'), '--stub',
                '--samples', str(root / 'samples.tsv'), '--pairs', str(root / 'pairs.csv'),
                '--called-rds', str(root / 'called.rds'), '--output', str(root / 'results')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = m.read_table(root / 'results/sample_results.tsv')
            self.assertEqual(rows[0]['profile_location'], str(root / 'called.rds'))
            self.assertTrue((root / 'results' / rows[0]['provenance_location']).is_file())


if __name__ == '__main__':
    unittest.main()
