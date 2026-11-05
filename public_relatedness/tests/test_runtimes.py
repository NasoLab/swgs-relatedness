"""Pinned runtime acquisition on synthetic bytes; no network or scientific payloads."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_setup', ROOT / 'bin/prepare_runtimes.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
spec = importlib.util.spec_from_file_location('runtime_assets', ROOT / 'bin/assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)
spec = importlib.util.spec_from_file_location('runtime_mount_check', ROOT / 'bin/check_runtime_mounts.py')
mounts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mounts)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.body = b'synthetic runtime acquisition marker only\n'
        self.sha = hashlib.sha256(self.body).hexdigest()
        self.patch = patch.dict(m.METRICS, sha256=self.sha, url='https://example.invalid/metrics.sif')
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def download(self, body):
        original = m.acquisition.fetch
        return patch.object(m.acquisition, 'fetch', side_effect=lambda record, directory:
                            original(record, directory, opener=lambda *a, **k: io.BytesIO(body)))

    def test_download_verifies_bytes_before_publishing(self):
        with self.download(self.body):
            dest = m.setup(self.root, download=True)
        self.assertEqual(dest.read_bytes(), self.body)
        self.assertEqual(list(self.root.glob('.swgs-acquire-*')), [])

    def test_wrong_download_is_not_published(self):
        with self.download(b'wrong synthetic bytes'), self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            m.setup(self.root, download=True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_valid_cache_never_downloads_again(self):
        dest = self.root / 'metrics.sif'
        dest.write_bytes(self.body)
        with patch.object(m.acquisition, 'fetch', side_effect=AssertionError('Network must not run')):
            self.assertEqual(m.setup(self.root, download=True), dest)

    def test_wrong_cache_is_never_overwritten(self):
        dest = self.root / 'metrics.sif'
        dest.write_bytes(b'existing wrong synthetic bytes')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            m.setup(self.root, download=True)
        self.assertEqual(dest.read_bytes(), b'existing wrong synthetic bytes')

    def test_existing_sif_is_verified_and_linked_without_copy(self):
        source = self.root / 'source.sif'
        source.write_bytes(self.body)
        dest = m.setup(self.root / 'cache', existing=source)
        self.assertTrue(os.path.samefile(source, dest))
        self.assertEqual(source.read_bytes(), self.body)

    def test_wrong_existing_source_is_not_linked(self):
        source = self.root / 'source.sif'
        source.write_bytes(b'wrong source marker')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            m.setup(self.root / 'cache', existing=source)
        self.assertFalse((self.root / 'cache/metrics.sif').exists())

    def test_missing_cache_has_actionable_error(self):
        with self.assertRaisesRegex(ValueError, '--fetch-metrics'):
            m.setup(self.root)

    def test_resource_directory_resolves_metrics_cache(self):
        p = assets.resolve(dict(resource_directory=str(self.root)))
        self.assertEqual(p['metrics_container'], str(self.root / 'containers/metrics.sif'))
        self.assertEqual(p['metrics_rscript'], '/opt/swgs/bin/Rscript-llr')
        self.assertEqual(p['breakpoint_rscript'], '/opt/swgs/bin/Rscript-general')

    def test_cached_host_scoring_remains_explicitly_available(self):
        p = assets.resolve(dict(resource_directory=str(self.root), called_rds='called.rds'))
        self.assertFalse(p.get('metrics_container'))
        self.assertEqual(p['metrics_rscript'], 'Rscript-llr')

    def test_cached_scoring_uses_downloaded_image_unless_host_selected(self):
        dest = self.root / 'containers/metrics.sif'
        dest.parent.mkdir()
        dest.write_bytes(self.body)
        p = assets.resolve(dict(resource_directory=str(self.root), called_rds='called.rds'))
        self.assertEqual(p['metrics_container'], str(dest))
        host = assets.resolve(dict(resource_directory=str(self.root), called_rds='called.rds',
                                   metrics_rscript='Rscript-llr', breakpoint_rscript='Rscript-general'))
        self.assertFalse(host.get('metrics_container'))

    def test_all_public_selectors_use_manifest_digests(self):
        config = (ROOT / 'nextflow.config').read_text()
        modules = ''.join((ROOT.parent / p).read_text() for p in [
            'modules/local/trimmomatic/main.nf', 'modules/local/alignment/main.nf',
            'modules/local/mark_duplicates/main.nf', 'public_relatedness/modules/cohort.nf'])
        images = json.loads((ROOT / 'environments/runtime_images.json').read_text())['images']
        public = [i for i in images if 'oci_uri' in i]
        self.assertEqual(len(public), 4)
        for image in public:
            self.assertRegex(image['oci_uri'], r'^docker://.+@sha256:[a-f0-9]{64}$')
            self.assertEqual(image['platform'], 'linux/amd64')
            self.assertIn(image['oci_uri'], config)
            self.assertIn(image['oci_uri'], modules)
        metric = next(i for i in images if i['role'] == 'metrics')
        self.assertEqual(metric['sha256'], 'ae7c40c285c19a6db6d01bb61f839cdd348f4cfd3f7510ae533091e2ed9f7151')
        self.assertEqual(metric['url'], 'https://bcgsc.ca/downloads/rcorbett/metrics-internal.sif')

    def test_host_parent_bind_is_rejected_for_embedded_r(self):
        targets = mounts.mount_targets('1 0 0:1 / / rw - squashfs image ro\n2 1 0:2 / /opt/runtime rw - ext4 host rw\n')
        with self.assertRaisesRegex(ValueError, 'hidden by a host bind'):
            mounts.check_paths(['/opt/runtime/lib/R/library'], targets)

    def test_narrow_input_mount_does_not_hide_r(self):
        targets = mounts.mount_targets('1 0 0:1 / / rw - squashfs image ro\n2 1 0:2 / /mnt/inputs rw - ext4 host rw\n')
        mounts.check_paths(['/opt/runtime/lib/R/library'], targets)


if __name__ == '__main__':
    unittest.main()
