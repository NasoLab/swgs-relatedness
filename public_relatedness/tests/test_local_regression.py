"""Opt-in, read-only historical evidence; no fixtures/identifiers are redistributed."""
import importlib.util
import os
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.environ.get('PUBLIC_HISTORICAL_REGRESSION') == '1', 'Local historical assets require separate access')
class LocalHistoricalTests(unittest.TestCase):
    def test_38_historical_pairs(self):
        path = os.environ.get('PUBLIC_HISTORICAL_CONFIG')
        if not path:
            self.skipTest('Supply an authorized external PUBLIC_HISTORICAL_CONFIG')
        config = json.loads(Path(path).read_text())
        case = config['fraction_shared']
        spec = importlib.util.spec_from_file_location('local_historical', config['resources']['fraction_implementation'])
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        fixture = Path(case['fixture'])
        reference = m.read(fixture)
        self.assertEqual(len(reference), 38)
        groups = m.group_observations(m.read(Path(case['observations'])))
        inventory = {r['sample_id']: r for r in m.read(Path(case['availability']))}
        # No patient-level contents are printed or written, even on failure.
        matches = 0
        for row in reference:
            a, b = row['Sample1'], row['Sample2']
            for sid in (a, b):
                self.assertTrue(sid in inventory, 'Missing historical profile inventory entry')
                if sid not in groups:
                    self.assertEqual(int(inventory[sid]['non_neutral_segments']), 0,
                                     'Missing observations for a nonzero profile')
            observed, _ = m.counts(groups, a, b)
            expected = tuple(m.integer(row[k]) for k in ['shared', 'private_sample1', 'private_sample2'])
            counts_match = observed == expected
            precision_match = m.fraction_comparison(m.precise_fraction(observed), row['fraction_shared'])[2]
            matches += counts_match and precision_match
        self.assertEqual(matches, 38, 'Historical count/fraction regression did not match all 38 pairs')


if __name__ == '__main__':
    unittest.main()
