#!/usr/bin/env python3
"""Capture installed Conda records without private prefixes or authenticated URLs."""
import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlsplit

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--prefix', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
rows, urls, missing = [], [], []
for path in sorted((a.prefix / 'conda-meta').glob('*.json')):
    record = json.loads(path.read_text())
    url = record.get('url', '')
    parsed = urlsplit(url)
    public = (parsed.scheme == 'https' and parsed.hostname in {'conda.anaconda.org', 'repo.anaconda.com'}
              and not parsed.username and not parsed.query and '/t/' not in parsed.path)
    if not public or not record.get('md5'):
        missing.append(record['name'])
    else:
        urls.append(url + '#' + record['md5'])
    rows.append({k: record.get(k, '') for k in ['name', 'version', 'build', 'subdir', 'md5', 'sha256', 'license']})
if not rows:
    raise SystemExit('No installed Conda records found')
with (a.output / 'conda-packages.tsv').open('w') as handle:
    w = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
(a.output / 'conda-explicit-linux-64.txt').write_text(
    '# Observed installed Conda layer only; post-install R overlays require restoration.\n@EXPLICIT\n' + '\n'.join(urls) + '\n')
(a.output / 'conda-capture.json').write_text(json.dumps(dict(platform='linux-64', packages=len(rows),
    explicit_records=len(urls), missing_or_unpublishable_records=missing, restoration_tested=False), indent=2) + '\n')
