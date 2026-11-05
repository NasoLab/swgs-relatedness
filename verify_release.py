#!/usr/bin/env python3
"""Audit an exact text-only release snapshot and its complete independent release history."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RELEASE_ROOT = "0582e6ba1ded9c099dacce8f6d3d0786de18f726"
FORBIDDEN_SUFFIXES = ('.fastq', '.fastq.gz', '.fq', '.fq.gz', '.bam', '.bai', '.cram', '.crai',
    '.sam', '.sra', '.rds', '.rda', '.rdata', '.fna', '.fasta', '.fa', '.vcf', '.bed', '.sif',
    '.img', '.tar', '.gz', '.zip', '.xlsx', '.xls', '.xlsm', '.ods', '.docx', '.pptx', '.pdf',
    '.png', '.jpg', '.ipynb', '.pem', '.key', '.pyc')
FORBIDDEN_ROOTS = {'analyses', 'data', 'output', 'test_data', 'old_scripts', 'private', 'work', 'results', '.aws'}
PATTERNS = {
    'private_key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'aws_access_key': r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'github_token': r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b',
    'authenticated_url': r'https?://[^\s/]+:[^\s/@]+@',
    'study_identifier': r'\b(?:(?:VS|VR)\d{2}[-_]\d+[A-Za-z0-9_-]*|JN[_-]P\d+|CC-SUN-\d+)\b',
}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def inspect(path, data):
    if Path(path).parts[0] in FORBIDDEN_ROOTS or path.lower().endswith(FORBIDDEN_SUFFIXES):
        raise ValueError(f'Forbidden release artifact: {path}')
    if Path(path).name == 'run_pcc_llr.R':
        raise ValueError('Legacy scientific runner must remain external')
    if len(data) > 512 * 1024 or b'\0' in data:
        raise ValueError(f'Large or binary artifact: {path}')
    text = data.decode('utf-8')
    for label, expression in PATTERNS.items():
        if re.search(expression, text):
            raise ValueError(f'{label} marker found in {path}; inspect privately')
    # Ignore URL paths when checking institutional filesystem path literals.
    without_urls = re.sub(r'https?://[^\s)\]<>]+', '', text)
    if re.search(r'/(?:home|projects)/[A-Za-z0-9_.-]+/', without_urls):
        raise ValueError(f'Institutional absolute path in {path}')


def release_history(commit):
    rows = [line.split() for line in git('rev-list', '--reverse', '--parents', commit).decode().splitlines()]
    if not rows or rows[0] != [RELEASE_ROOT]:
        raise ValueError('Release history must start at the approved independent root')
    for previous, row in zip(rows, rows[1:]):
        if len(row) != 2 or row[1] != previous[0]:
            raise ValueError('Release history must be linear; merges/research ancestry are forbidden')
    return [row[0] for row in rows]


def commit_files(commit):
    files = {}
    for item in git('ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
        if not item:
            continue
        meta, name = item.split(b'\t', 1)
        mode, kind, oid = meta.split()
        if kind != b'blob' or mode not in {b'100644', b'100755'}:
            raise ValueError('Submodule/symlink/non-file entry in release')
        files[name.decode()] = git('cat-file', 'blob', oid.decode())
    return files


def working_files():
    names = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').split(b'\0')
    files = {}
    for name in names:
        if not name:
            continue
        path = name.decode(); source = ROOT / path
        if not source.is_file() or source.is_symlink():
            raise ValueError(f'Missing or linked release file: {path}')
        files[path] = source.read_bytes()
    return files


def audit_snapshot(files, require_publishable=False):
    approved = files['RELEASE_FILES.txt'].decode().splitlines()
    if approved != sorted(set(approved)) or set(files) != set(approved):
        raise ValueError('Release file set differs from exact allowlist')
    sums = {}
    for line in files['RELEASE_SHA256SUMS.txt'].decode().splitlines():
        digest, path = line.split('  ', 1)
        if path in sums:
            raise ValueError('Duplicate checksum entry')
        sums[path] = digest
    if set(sums) != set(files) - {'RELEASE_SHA256SUMS.txt'}:
        raise ValueError('Incomplete release checksum manifest')
    for path, data in files.items():
        inspect(path, data)
        if path in sums and hashlib.sha256(data).hexdigest() != sums[path]:
            raise ValueError(f'Release checksum mismatch: {path}')
    status = json.loads(files['RELEASE_STATUS.json'])
    if status['version'] != '0.1.0-dev' or status['end_to_end_validation'] != 'pending':
        raise ValueError('Unexpected development release/validation label')
    if require_publishable:
        if (not status['publication_authorized'] or status['project_license_status'] != 'cleared'
                or status.get('legacy_authorization_required')
                or not status.get('ownership_approval_reference')
                or not status.get('publication_approval_reference')
                or not status.get('publication_repository')):
            raise ValueError('Publication blocked: ownership/MIT authorization, approval records and destination decision are required')
        if 'LICENSE.MIT.proposed' in files or b'MIT License' not in files['LICENSE']:
            raise ValueError('Publication blocked: the authorized MIT license must be applied, not proposed')
    return dict(status='snapshot_audit_passed', files=len(files), bytes=sum(map(len,files.values())),
        end_to_end_validation=status['end_to_end_validation'], publication_authorized=status['publication_authorized'])


def audit(commit=None, require_publishable=False):
    if not commit:
        result = audit_snapshot(working_files(), require_publishable)
        result['history'] = 'working snapshot; full committed-history audit still required'
        return result
    commits = release_history(commit)
    for revision in commits:
        inspect('COMMIT_METADATA', git('cat-file', 'commit', revision))
        result = audit_snapshot(commit_files(revision), require_publishable and revision == commits[-1])
    result.update(history='independent root plus audited linear release descendants',
        root=RELEASE_ROOT, commits_audited=len(commits), every_reachable_snapshot_audited=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--commit', help='Audit every reachable release commit and snapshot instead of working files')
    p.add_argument('--require-publishable', action='store_true')
    a = p.parse_args()
    try:
        print(json.dumps(audit(a.commit, a.require_publishable), indent=2))
    except (ValueError, KeyError, UnicodeError, OSError, subprocess.CalledProcessError) as error:
        p.exit(1, f'Release audit failed: {error}\n')


if __name__ == '__main__':
    main()
