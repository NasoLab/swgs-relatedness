# Publication preparation — v0.1.0 — Development

No push, tag, GitHub release, repository creation or image publication is
performed by this preparation. The content audit and the publication-authorization
gate are distinct. The latter remains blocked by the specific records in
[LICENSE](LICENSE), [the licensing audit](public_relatedness/LICENSING.md) and
[RELEASE_STATUS.json](RELEASE_STATUS.json).

## Required authorization

MIT is selected for project-owned code and contributions the project may lawfully
distribute. The four retained legacy files listed in LICENSE still lack a
confirmed MIT distribution grant. Obtain the relevant rights-holder authority,
confirm ownership of the new contributions, and record accurate copyright
notices. Acknowledgement is not a grant. LICENSE.MIT.proposed is a draft only.
After approval, apply the approved text to LICENSE, remove the proposal, update
the allowlist/checksums, and record non-sensitive approval references. Do not put
private permission correspondence, personal contact details or workbooks in Git.

RELEASE_STATUS.json must then record project_license_status='cleared', an empty
legacy_authorization_required list, ownership_approval_reference,
publication_approval_reference, the approved publication_repository (OWNER/NAME),
and publication_authorized=true. These values represent real approvals; do not
set them merely to pass the tool. Re-test, commit and audit the updated candidate.
External packages, references, images and scientific implementations are outside
the intended project MIT grant and remain user-supplied under their own terms.

## Destination decision

The originally requested rcorbett-match/swgs-processing-pipeline repository is a
public fork containing historical sequencing data. Do not push this candidate
there without an explicit owner decision about that history. A clean branch does
not remove old refs, objects, forks, caches or existing copies. The existing
exposure requires separate owner/PI and appropriate institutional review; this
preparation does not authorize removal, rewriting, renaming or visibility changes.

Recommended route: obtain approval to create a new **empty non-fork repository**
under rcorbett-match, for example swgs-processing-pipeline-public. This proposed
name has not been reserved or verified as available. Use the exact approved name
in the commands and release metadata. Publishing elsewhere does not remediate
the original repository's historical exposure.

## Local inspection and history policy

Run in the clean release worktree:

```bash
git status --short
git log --format=fuller --stat
python verify_release.py --commit HEAD
python verify_release.py --commit HEAD --require-publishable
```

The final command currently fails intentionally. The auditor anchors history at
0582e6ba1ded9c099dacce8f6d3d0786de18f726, rejects merges/unrelated roots, and checks
every reachable release commit's metadata, complete file allowlist, SHA256 set
and contents. Thus a forbidden payload deleted from the tip still fails audit.
The branch contains that independent clean root and release-only descendants;
no research commit is imported. Pattern scanning does not establish ownership
or guarantee detection of every possible identifier. Human content and rights
review remain required. Scientific source stays unchanged during preparation.

## Exact publication commands — only after approval

The following is a future operator procedure, not authorization to run it now.
It uses a new writable directory on an operator-selected mounted storage volume
and exports only the reviewed release ref into a fresh Git object database.
A local clone directly from the shared research object store is not sufficient.
First run in the clean release worktree, substituting the approved destination:

```bash
PUBLIC_REPO=rcorbett-match/swgs-processing-pipeline-public
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
```

Require no alternates, tags or unexpected refs and exactly the approved reachable
objects. The bundle and export must contain only the clean release root and its
audited descendants, never other local branches or automation checkpoint refs.
After explicit approval to create the named public repository, run from that
fresh export; these commands must fail rather than reuse an existing repository:

```bash
gh repo create "$PUBLIC_REPO" --public
test "$(gh api "repos/$PUBLIC_REPO" --jq '.fork')" = false
test -z "$(git ls-remote "https://github.com/$PUBLIC_REPO.git")"
git remote set-url origin "https://github.com/$PUBLIC_REPO.git"
git push --dry-run origin "$CANDIDATE_COMMIT":refs/heads/main
```

Review the destination, object inventory and dry run against the final publication
approval. The final publication command, still not executed here, is:

```bash
git push origin "$CANDIDATE_COMMIT":refs/heads/main
```

Do not use --all, --mirror, --tags or force. Do not merge unrelated histories.
Do not create a tag or GitHub release in this preparation. Maintain the development,
end-to-end-pending and cross-host-pending labels until supported validation is
reviewed. No data, reference or container payload accompanies this source release.
