# Publication preparation — NasoLab/swgs-relatedness

The maintainer selected the existing public repository
[NasoLab/swgs-relatedness](https://github.com/NasoLab/swgs-relatedness).
Read-only GitHub metadata and Git ref inspection verified that it is a non-fork
with no branches or advertised refs. The release worktree's `publication` remote
is https://github.com/NasoLab/swgs-relatedness.git; its existing `origin` is
unchanged. The publication remote uses worktree-specific Git configuration.

No push, tag creation or GitHub release is authorized by this preparation. The
maintainer requested a stop for final approval. The original fork and the running
FASTQ pilot are untouched. Do not use origin or any historical research ref for
publication, and do not treat the old fork as a destination.

## Licensing decision still required

MIT remains proposed for project-owned code/contributions the project may lawfully
distribute. The maintainer has not established a formal copyright-holder
designation or separate written MIT authorization for the four retained legacy
files listed in [LICENSE](LICENSE). A final licensing decision is required before
publication. Do not invent approval references or infer copyright ownership from
Git authorship. The Huntsman acknowledgement and original credits are preserved.
External packages, scientific implementations, references and images retain their
own terms and are not relicensed or bundled here.

After a supported licensing decision, apply the approved license and correct
notices, remove LICENSE.MIT.proposed if MIT is approved, and update release
metadata/checksums in a new clean descendant commit. Record only non-sensitive
approval references; private correspondence must stay outside Git.
RELEASE_STATUS.json must have project_license_status='cleared', an empty
legacy_authorization_required list, ownership_approval_reference,
publication_approval_reference, publication_repository='NasoLab/swgs-relatedness'
and publication_authorized=true. Those fields must represent actual decisions;
never change them merely to bypass the gate. Re-test and audit the resulting
commit. The publication gate intentionally fails on the current candidate.

## Independent history and final audit

```bash
git status --short
git log --format=fuller --stat
python verify_release.py --commit HEAD
python verify_release.py --commit HEAD --require-publishable
```

The audit anchors history at the clean independent root
0582e6ba1ded9c099dacce8f6d3d0786de18f726, rejects merges/unrelated roots and checks
every reachable release commit's complete allowlist, SHA256 set, metadata and
contents. A forbidden payload removed from the tip still fails audit. Research
ancestors, unrelated branches and automation checkpoint refs must never be
exported. The old fork's exposed history remains a separate owner-led issue;
publishing this clean project does not remove old copies or caches.

## Exact commands after final licensing and publication approval

These commands are prepared for a future approved operator session. None of the
push, tag or release commands has been executed. Start in the audited release
worktree, using an operator-selected mounted volume for the new private export:

```bash
set -euo pipefail
PUBLIC_REPO=NasoLab/swgs-relatedness
PUBLIC_URL=https://github.com/NasoLab/swgs-relatedness.git
CANDIDATE_REF=refs/heads/release/public-v0.1.0-development
CANDIDATE_COMMIT=$(git rev-parse "$CANDIDATE_REF^{commit}")
python verify_release.py --commit "$CANDIDATE_COMMIT" --require-publishable
test "$(python -c 'import json; print(json.load(open("RELEASE_STATUS.json"))["publication_repository"])')" = "$PUBLIC_REPO"
PUBLISH_ROOT=$(mktemp -d /mnt/swgs/swgs-publish.XXXXXX)
git bundle create "$PUBLISH_ROOT/release.bundle" "$CANDIDATE_REF"
git clone --no-tags --single-branch -b release/public-v0.1.0-development "$PUBLISH_ROOT/release.bundle" "$PUBLISH_ROOT/export"
cd "$PUBLISH_ROOT/export"
test "$(git rev-parse HEAD)" = "$CANDIDATE_COMMIT"
python verify_release.py --commit "$CANDIDATE_COMMIT" --require-publishable
git fsck --full --no-reflogs
git rev-list --reverse --parents "$CANDIDATE_COMMIT"
git for-each-ref --format='%(refname) %(objectname)'
git cat-file --batch-all-objects --batch-check='%(objectname) %(objecttype) %(objectsize)'
git remote add publication "$PUBLIC_URL"
```

Require exactly the approved reachable commit/tree/blob objects, no alternates,
no tags and no unexpected refs. Use the fresh export rather than cloning directly
from the shared research object store. Recheck the existing destination just
before pushing. If any refs have appeared, stop and review them; do not force-push,
merge, delete or overwrite their history. Do not create another repository:

```bash
test "$(gh api "repos/$PUBLIC_REPO" --jq '.fork')" = false
REMOTE_REFS=$(git ls-remote --symref publication)
test -z "$REMOTE_REFS"
git push --dry-run publication "$CANDIDATE_COMMIT":refs/heads/main
```

After approving the exact commit, destination, annotation and dry run, these are
the tag and atomic branch/tag publication commands. The annotation is prepared
in [release/v0.1.0-tag.txt](release/v0.1.0-tag.txt); it is not a Git tag yet:

```bash
python verify_release.py --commit "$CANDIDATE_COMMIT" --require-publishable
if git show-ref --verify --quiet refs/tags/v0.1.0; then exit 1; fi
git tag -a v0.1.0 "$CANDIDATE_COMMIT" -F release/v0.1.0-tag.txt
test "$(git rev-parse 'v0.1.0^{commit}')" = "$CANDIDATE_COMMIT"
git push --atomic publication "$CANDIDATE_COMMIT":refs/heads/main refs/tags/v0.1.0:refs/tags/v0.1.0
```

Only if GitHub release publication is also explicitly approved, use the existing
verified tag and prepared [release notes](RELEASE_NOTES.md):

```bash
gh release create v0.1.0 --repo NasoLab/swgs-relatedness --verify-tag \
  --title 'v0.1.0 — Development' --notes-file RELEASE_NOTES.md --prerelease
```

The v0.1.0 tag designates a development prerelease. End-to-end and cross-host
validation remain pending. Do not use --all, --mirror, --tags or force; push only
the two named refs. Do not regenerate references, distribute unapproved assets or
modify scientific parameters to simplify publication. Any approved license change
will change CANDIDATE_COMMIT: recompute it and rerun the audits before publication.
