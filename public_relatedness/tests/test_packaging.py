"""Configuration/identity checks with tiny file markers; no reference regeneration."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('setup_validation', ROOT / 'bin/validate_setup.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.samples = self.root / 'samples.tsv'
        for n in ['one.fq.gz', 'two.fq.gz', 'GCA_000001405.15_GRCh38.fna', 'bins.rds']:
            (self.root / n).write_text('metadata marker only\n')
        self.samples.write_text('sample_id\tfastq_1\tfastq_2\nA\tone.fq.gz\ttwo.fq.gz\n')
        self.params = dict(samples=str(self.samples), reference=str(self.root / 'GCA_000001405.15_GRCh38.fna'),
                           pe150_bins=str(self.root / 'bins.rds'), pe150_bins_sha256=m.manifest.PE150_SHA256,
                           outdir=str(self.root / 'results'), metrics_rscript=sys.executable)
        self.runner = self.root / 'runner.R'
        self.runner.write_text('explicit test marker; not a scientific implementation\n')
        self.runner_sha = m.metrics.sha256(self.runner)
        self.params['pcc_llr_runner'] = str(self.runner)
        self.refs = dict(resources=[dict(id='test_marker', config_param='pe150_bins', suffix='',
                                         sha256=m.metrics.sha256(self.root / 'bins.rds'))])

    def validate(self, **kwargs):
        with patch.object(m, 'require_executable'), patch.dict(m.metrics.HASHES, runner=self.runner_sha):
            return m.validate(self.params, reference_manifest=self.refs, **kwargs)

    def test_content_identity_and_metadata_only_statuses(self):
        self.assertEqual(self.validate()['status'], 'resource_identities_verified')
        self.assertEqual(self.validate(metadata_only=True)['content_verification'], 'not_performed')
        (self.root / 'bins.rds').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.validate()

    def test_bundled_runner_is_automatic_and_overrides_checksum_locked(self):
        del self.params['pcc_llr_runner']
        self.assertEqual(self.validate(metadata_only=True)['status'], 'metadata_valid')
        self.params['pcc_llr_runner'] = str(self.runner)
        self.runner.write_text('changed test marker')
        with self.assertRaisesRegex(ValueError, 'pcc_llr_runner'):
            self.validate()

    def test_reject_self_asserted_unapproved_annotation_hash(self):
        self.params['pe150_bins_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'approved PE150'):
            self.validate(metadata_only=True)

    def test_invalid_profile_and_conflicting_runtimes(self):
        for profiles in ['unknown', 'docker,singularity', 'local']:
            with self.subTest(profiles=profiles), self.assertRaises(ValueError):
                self.validate(profiles=profiles)

    def test_existing_results_are_protected(self):
        out = Path(self.params['outdir'])
        out.mkdir()
        (out / 'pair_results.tsv').touch()
        with self.assertRaisesRegex(ValueError, 'already contains'):
            self.validate()

    def test_temporary_volume_must_be_available_and_bind_safe(self):
        volume = self.root / 'large_volume_tmp'
        volume.mkdir()
        self.params['temp_directory'] = str(volume)
        self.validate(metadata_only=True)
        for value in ['relative/tmp', str(self.root / 'missing'), str(self.samples),
                      '/tmp/colon:path', '/tmp/comma,path', '/tmp/new\nline',
                      '/tmp/with space', "/tmp/with'quote", '/tmp/$HOME', 12, '']:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'temp_directory'):
                self.params['temp_directory'] = value
                self.validate(metadata_only=True)

    def test_archives_checked_by_sif_hash(self):
        image = self.root / 'recorded.img'
        image.write_text('image marker')
        self.params['image_directory'] = str(self.root)
        inventory = dict(containers=[dict(filename=image.name, sha256=m.metrics.sha256(image), role='test')])
        self.validate(check_images=True, image_inventory=inventory)
        image.write_text('replaced')
        with self.assertRaisesRegex(ValueError, 'Container archive checksum mismatch'):
            self.validate(check_images=True, image_inventory=inventory)

    def test_missing_reference_reports_path_and_installation(self):
        reference = Path(self.params['reference'])
        reference.unlink()
        with self.assertRaises(ValueError) as caught:
            self.validate(metadata_only=True)
        message = str(caught.exception)
        for expected in [str(reference), 'public_relatedness/INSTALL.md', 'prepare_resources.py']:
            self.assertIn(expected, message)

    def test_missing_annotation_reports_path_and_acquisition(self):
        annotation = Path(self.params['pe150_bins'])
        annotation.unlink()
        resources = json.loads((ROOT / 'references/manifest.json').read_text())['resources']
        self.refs = dict(resources=[r for r in resources if r['id'] == 'qdnaseq_pe150_500kb'])
        with self.assertRaises(ValueError) as caught:
            self.validate(metadata_only=True)
        message = str(caught.exception)
        for expected in [str(annotation), 'qdnaseq_pe150_500kb', 'prepare_resources.py',
                         'public_relatedness/INSTALL.md', 'public_relatedness/references/README.md']:
            self.assertIn(expected, message)

    def test_missing_index_reports_path_and_reference_instructions(self):
        resources = json.loads((ROOT / 'references/manifest.json').read_text())['resources']
        self.refs = dict(resources=[r for r in resources if r['id'] == 'bwa_mem2_index_0123'])
        with self.assertRaises(ValueError) as caught:
            self.validate(metadata_only=True)
        message = str(caught.exception)
        for expected in [self.params['reference'] + '.0123', 'bwa_mem2_index_0123',
                         'public_relatedness/INSTALL.md', 'public_relatedness/references/README.md']:
            self.assertIn(expected, message)

    def test_missing_images_report_paths_and_runtime_instructions(self):
        self.params['image_directory'] = str(self.root)
        images = json.loads((ROOT / 'environments/runtime_images.json').read_text())['images']
        for image in images:
            with self.subTest(role=image['role']):
                with self.assertRaises(ValueError) as caught:
                    local_override = {k: v for k, v in image.items() if k != 'oci_uri'}
                    self.validate(metadata_only=True, check_images=True, image_inventory=dict(images=[local_override]))
                message = str(caught.exception)
                for expected in [str(self.root / image['filename']), 'image_directory',
                                 'public_relatedness/INSTALL.md', 'public_relatedness/environments/README.md',
                                 'public_relatedness/environments/runtime_images.json']:
                    self.assertIn(expected, message)

    def test_public_images_need_only_local_metrics_sif(self):
        self.params['image_directory'] = str(self.root)
        (self.root / 'metrics.sif').write_text('synthetic image marker; metadata-only check')
        result = self.validate(metadata_only=True, check_images=True)
        selected = result['runtime_selection']
        self.assertEqual(sum(v['source'] == 'oci' for v in selected.values()), 4)
        self.assertEqual(selected['metrics']['source'], 'local_sif')

    def test_invalid_legacy_override_does_not_fall_back_to_oci(self):
        self.params['image_directory'] = str(self.root)
        first = json.loads((ROOT / 'environments/runtime_images.json').read_text())['images'][0]
        (self.root / first['filename']).write_text('wrong synthetic image marker')
        with self.assertRaisesRegex(ValueError, 'Container archive checksum mismatch: trimmomatic'):
            self.validate(check_images=True)

    def test_reference_manifest_has_approved_annotation_and_sidecars(self):
        data = json.loads((ROOT / 'references/manifest.json').read_text())
        annotation = [r for r in data['resources'] if r['config_param'] == 'pe150_bins']
        self.assertEqual(annotation[0]['sha256'], m.manifest.PE150_SHA256)
        self.assertEqual({r['suffix'] for r in data['resources'] if r['config_param'] == 'reference'},
                         {'', '.0123', '.amb', '.ann', '.bwt.2bit.64', '.pac'})
        self.assertFalse(data['assets_bundled'])

    def test_no_unearned_container_validation_or_oci_digest(self):
        data = json.loads((ROOT / 'environments/inventory.json').read_text())
        self.assertTrue(all(c['oci_manifest_digest'] is None for c in data['containers']))
        self.assertIn('unbuilt', data['build_status'])
        for label in ['general-r', 'llr-r']:
            lock = ROOT / 'environments' / label / 'conda-explicit-linux-64.txt'
            self.assertIn('@EXPLICIT', lock.read_text())
            self.assertNotIn('latest', lock.read_text())

    def test_real_preflight_rejects_fake_asset_even_with_matching_self_hash(self):
        bins = self.root / 'bins.rds'
        result = subprocess.run([sys.executable, str(ROOT / 'bin/prepare_manifest.py'),
            '--samples', str(self.samples), '--output', str(self.root / 'manifest'),
            '--pe150-bins', str(bins), '--pe150-sha256', m.metrics.sha256(bins)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('approved PE150', result.stderr)
        self.assertFalse((self.root / 'manifest').exists())


if __name__ == '__main__':
    unittest.main()
