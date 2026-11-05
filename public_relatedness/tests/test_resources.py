"""Portable source/resource resolution and atomic acquisition on synthetic bytes only."""
import ast
import gzip
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'bin' / file)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result
assets = module('resources_paths', 'assets.py')
setup = module('resources_setup', 'prepare_resources.py')
validation = module('resource_validation', 'validate_setup.py')

class ResourcesTests(unittest.TestCase):
    def test_bundled_sources_resolve_outside_repository(self):
        cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                p = assets.resolve({'resource_directory': folder})
                for key, param in assets.PARAMS.items():
                    source = Path(p[param]); self.assertTrue(source.is_file())
                    self.assertEqual(setup.sha256(source), assets.SOURCES[key]['sha256'])
                self.assertEqual(Path(p['llr_helper']), Path(folder) / assets.SOURCES['helper']['filename'])
                self.assertEqual(Path(p['pfreq']).name, 'pfreq_lusc_tcga_split.csv')
            finally: os.chdir(cwd)

    def test_minimal_configuration_has_no_script_paths(self):
        p = json.loads((ROOT / 'examples/run-params.json').read_text())
        self.assertEqual(set(p), {'samples', 'pairs', 'resource_directory', 'outdir'})
        self.assertNotIn('permission_cleared', json.dumps(p))

    def test_frozen_source_provenance_is_preserved(self):
        self.assertEqual(assets.SOURCES['runner']['sha256'], assets.SOURCES['runner']['historical_full_source_sha256'])
        self.assertEqual(assets.SOURCES['matching']['sha256'], assets.SOURCES['matching']['historical_full_source_sha256'])
        self.assertEqual(assets.SOURCES['preprocessing']['historical_full_source_sha256'], '16655beb5ea51c3f9297418d04a5a288d23689259f7845e6db553564232cabf6')
        self.assertEqual(assets.SOURCES['fraction_implementation']['historical_full_source_sha256'], 'e127424de7f54233dfc0281887d273e9e9deb81437250e1d08ac145070bb7f31')
        self.assertFalse(assets.SOURCES['helper']['bundled'])
        self.assertTrue((ROOT / 'vendor/breakclone/LICENSE').is_file())

    def test_gzip_acquisition_verifies_decompressed_bytes(self):
        body = b'synthetic reference marker only\n'
        record = dict(filename='marker.txt', sha256=hashlib.sha256(body).hexdigest(), url='https://example.invalid/marker', gzip=True)
        with tempfile.TemporaryDirectory() as folder:
            dest = setup.fetch(record, folder, opener=lambda *a, **k: io.BytesIO(gzip.compress(body)))
            self.assertEqual(dest.read_bytes(), body)
            self.assertEqual(list(Path(folder).glob('.swgs-acquire-*')), [])

    def test_failed_checksum_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            record = dict(filename='marker.txt', sha256='0'*64, url='https://example.invalid/marker')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                setup.fetch(record, folder, opener=lambda *a, **k: io.BytesIO(b'wrong synthetic bytes'))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_existing_reference_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / 'marker.txt'; dest.write_bytes(b'existing synthetic content')
            record = dict(filename=dest.name, sha256='0'*64, url='https://example.invalid/marker')
            with self.assertRaisesRegex(ValueError, 'Existing file differs'):
                setup.fetch(record, folder)
            self.assertEqual(dest.read_bytes(), b'existing synthetic content')

    def test_missing_reference_error_is_actionable(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for mate in ['one.fq.gz', 'two.fq.gz']: (root / mate).write_text('synthetic marker')
            samples=root/'samples.tsv';samples.write_text('sample_id\tfastq_1\tfastq_2\nA\tone.fq.gz\ttwo.fq.gz\n')
            with self.assertRaisesRegex(ValueError, 'prepare_resources.py'):
                validation.validate(dict(samples=str(samples), resource_directory=folder, outdir=str(root/'out')),metadata_only=True)

    def test_historical_core_retains_inclusive_all_overlaps(self):
        p=ROOT/'lib/relatedness/fraction_shared_historical.py'
        spec=importlib.util.spec_from_file_location('bp_core',p);core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
        rows=[dict(SampleID=s, Chr='1', SVType='DEL', boundary_type='start',coordinate=str(x)) for s,x in [('A',0),('A',1),('B',2500000)]]
        groups=core.group_observations(rows)
        self.assertEqual(core.counts(groups,'A','B')[0],(2,0,-1))
        groups['B'][('1','DEL','start')]=[2500002]
        self.assertEqual(core.counts(groups,'A','B')[0],(0,2,1))
        tree=ast.parse(p.read_text())
        self.assertFalse(any(isinstance(n,ast.FunctionDef) and n.name=='main' for n in tree.body))

if __name__=='__main__': unittest.main()
