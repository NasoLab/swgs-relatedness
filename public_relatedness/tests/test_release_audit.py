"""Release guards use synthetic in-memory artifacts; no sequencing inputs."""
import hashlib
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('release_guard', ROOT / 'verify_release.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReleaseAuditTests(unittest.TestCase):
    def test_approved_root_and_complete_history_are_audited(self):
        result = m.audit('HEAD')
        self.assertEqual(result['root'], m.RELEASE_ROOT)
        self.assertTrue(result['every_reachable_snapshot_audited'])

    def test_working_snapshot_matches_exact_allowlist_and_checksums(self):
        self.assertEqual(m.audit()['status'], 'snapshot_audit_passed')

    def test_publication_requires_actual_approval(self):
        with self.assertRaisesRegex(ValueError, 'Publication blocked'):
            m.audit(require_publishable=True)

    def test_unapproved_root_is_rejected(self):
        with patch.object(m, 'git', return_value=(('1' * 40) + '\n').encode()):
            with self.assertRaisesRegex(ValueError, 'approved independent root'):
                m.release_history('HEAD')

    def test_merge_ancestry_is_rejected(self):
        history = m.RELEASE_ROOT + '\n' + ('2' * 40) + ' ' + m.RELEASE_ROOT + ' ' + ('3' * 40) + '\n'
        with patch.object(m, 'git', return_value=history.encode()):
            with self.assertRaisesRegex(ValueError, 'merges/research ancestry'):
                m.release_history('HEAD')

    def test_changed_blob_is_rejected(self):
        files = m.working_files()
        files['README.md'] += b'\nchanged synthetic marker\n'
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            m.audit_snapshot(files)

    def test_payload_removed_from_tip_is_still_rejected_in_ancestor(self):
        clean = m.working_files()
        dirty = dict(clean)
        dirty['test_data/removed.fastq.gz'] = b'synthetic marker, no read data'
        dirty['RELEASE_FILES.txt'] = ('\n'.join(sorted(dirty)) + '\n').encode()
        dirty['RELEASE_SHA256SUMS.txt'] = ''.join(
            hashlib.sha256(data).hexdigest() + '  ' + path + '\n'
            for path, data in sorted(dirty.items()) if path != 'RELEASE_SHA256SUMS.txt').encode()
        tip = '2' * 40
        with patch.object(m, 'release_history', return_value=[m.RELEASE_ROOT, tip]), \
             patch.object(m, 'git', return_value=b'benign synthetic commit metadata'), \
             patch.object(m, 'commit_files', side_effect=lambda rev: dirty if rev == m.RELEASE_ROOT else clean):
            with self.assertRaisesRegex(ValueError, 'Forbidden release artifact'):
                m.audit(tip)

    def test_secret_marker_is_rejected(self):
        token = ('AK' + 'IA' + 'A' * 16).encode()
        with self.assertRaisesRegex(ValueError, 'aws_access_key'):
            m.inspect('synthetic.txt', token)


if __name__ == '__main__':
    unittest.main()
