import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('public_manifest', ROOT / 'bin/prepare_manifest.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.samples = self.root / 'samples.tsv'
        self.pairs = self.root / 'pairs.tsv'
        self.rows = []
        for sid in ['sampleC', 'sampleA', 'sampleB']:
            files = []
            for mate in ['1', '2']:
                path = self.root / f'{sid}_{mate}.fq.gz'
                path.touch()  # file existence only, never treated as sequencing data
                files.append(path.name)
            self.rows.append([sid, *files])
        self.write_samples()
        self.write_pairs([['comparison2', 'sampleC', 'sampleB'], ['comparison1', 'sampleC', 'sampleA']])

    def write_samples(self):
        self.write(self.samples, ['sample_id', 'fastq_1', 'fastq_2'], self.rows)

    def write_pairs(self, rows):
        self.write(self.pairs, ['pair_id', 'sample1', 'sample2'], rows)

    def write(self, path, fields, rows):
        with path.open('w', newline='') as handle:
            writer = csv.writer(handle, delimiter='\t')
            writer.writerow(fields)
            writer.writerows(rows)

    def test_mapping_repeated_sample_and_order(self):
        samples, pairs = m.validate(self.samples, self.pairs)
        self.assertEqual([r['sample_id'] for r in samples], ['sampleC', 'sampleA', 'sampleB'])
        self.assertEqual([r['pair_id'] for r in pairs], ['comparison2', 'comparison1'])
        self.assertEqual([r['sample1'] for r in pairs], ['sampleC', 'sampleC'])
        self.assertTrue(all(Path(r['fastq_1']).is_absolute() for r in samples))
        out = self.root / 'validated'
        m.write_outputs(out, samples, pairs)
        self.assertEqual((out / 'expected_samples.txt').read_text(), 'sampleC\nsampleA\nsampleB\n')
        self.assertEqual(json.loads((out / 'cohort.json').read_text())['pair_count'], 2)

    def test_no_pairs(self):
        self.assertEqual(m.validate(self.samples)[1], [])

    def test_duplicate_sample(self):
        self.rows.append(self.rows[0])
        self.write_samples()
        with self.assertRaisesRegex(ValueError, 'Duplicate sample'):
            m.validate(self.samples)

    def test_invalid_ids(self):
        for value in ['A.1', '../A', 'A B', 'A;false', 'NA']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.identifier(value)

    def test_missing_mate_and_missing_file(self):
        for value in ['', 'missing.fastq']:
            with self.subTest(value=value):
                self.rows[0][2] = value
                self.write_samples()
                with self.assertRaises(ValueError):
                    m.validate(self.samples)

    def test_reused_reads(self):
        for index in [0, 1]:
            with self.subTest(index=index):
                saved = self.rows[index][2]
                self.rows[index][2] = self.rows[0][1]
                self.write_samples()
                with self.assertRaisesRegex(ValueError, 'FASTQ reused'):
                    m.validate(self.samples)
                self.rows[index][2] = saved

    def test_invalid_pairs(self):
        for rows in [
            [['p1', 'sampleC', 'missing']], [['p1', 'sampleC', 'sampleC']],
            [['p1', 'sampleC', 'sampleA'], ['p1', 'sampleC', 'sampleB']],
            [['p1', 'sampleC', 'sampleA'], ['p2', 'sampleA', 'sampleC']], [],
        ]:
            with self.subTest(rows=rows):
                self.write_pairs(rows)
                with self.assertRaises(ValueError):
                    m.validate(self.samples, self.pairs)

    def test_strict_header_and_rows(self):
        for content in ['pair_id\tfastq_1\tfastq_2\np1\tx\ty\n',
                        'sample_id\tfastq_1\tfastq_2\nA\tx\ty\textra\n',
                        'sample_id\tfastq_1\tfastq_2\nA\tx\n',
                        'sample_id\tfastq_1\tfastq_2\n']:
            with self.subTest(content=content):
                self.samples.write_text(content)
                with self.assertRaises(ValueError):
                    m.validate(self.samples)

    def test_symlink_reuse(self):
        link = self.root / 'alias.fq.gz'
        link.symlink_to(self.root / self.rows[0][1])
        self.rows[1][1] = link.name
        self.write_samples()
        with self.assertRaisesRegex(ValueError, 'FASTQ reused'):
            m.validate(self.samples)

    def test_annotation_checksum_fail_closed(self):
        bins = self.root / 'bins.rds'
        bins.write_text('plumbing placeholder')
        result = subprocess.run([sys.executable, str(ROOT / 'bin/prepare_manifest.py'),
            '--samples', str(self.samples), '--output', str(self.root / 'out'),
            '--pe150-bins', str(bins), '--pe150-sha256', '0' * 64], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('checksum mismatch', result.stderr)
        self.assertFalse((self.root / 'out').exists())


if __name__ == '__main__':
    unittest.main()
