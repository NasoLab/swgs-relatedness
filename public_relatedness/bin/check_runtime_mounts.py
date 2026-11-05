#!/usr/bin/env python3
"""Reject host mounts hiding R libraries embedded in the preserved metrics SIF."""
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


def mount_targets(text):
    targets = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 6:
            raise ValueError('Cannot inspect container mount table')
        targets.append(re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), fields[4]))
    if '/' not in targets:
        raise ValueError('Container root mount was not identified')
    return targets


def check_paths(paths, targets):
    for name in paths:
        path = PurePosixPath(name)
        candidates = [t for t in targets if path == PurePosixPath(t) or PurePosixPath(t) in path.parents]
        covering = max(candidates, key=len) if candidates else None
        if covering != '/':
            raise ValueError('R runtime path is hidden by a host bind: ' + name +
                             '. Keep the clone, scoring inputs and work under a common operational directory '
                             'and avoid broad parent binds. See docs/USAGE.md#runtime-setup')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rscript', action='append', required=True)
    args = p.parse_args()
    try:
        targets = mount_targets(Path('/proc/self/mountinfo').read_text())
        checked = []
        # Metadata queries use separate R processes, never the scoring RNG stream.
        query = 'p<-unique(c(normalizePath(R.home()),.libPaths()));cat(p[dir.exists(p)],sep="\\n")'
        for executable in args.rscript:
            result = subprocess.run([executable, '--vanilla', '-e', query], check=True, text=True, capture_output=True)
            paths = result.stdout.splitlines()
            if not paths:
                raise ValueError('R library-path query returned no paths')
            check_paths(paths, targets)
            checked.append(dict(executable=executable, libraries_on_image_root=True))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        p.exit(2, 'Contained runtime check failed: ' + str(error) + '\n')
    print(json.dumps(dict(runtime_mount_check='passed', runtimes=checked)))


if __name__ == '__main__':
    main()
