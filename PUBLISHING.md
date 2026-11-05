# v0.1.1 development candidate — publication is not requested

This candidate is on development/v0.1.1-source-packaging, descending from the
published v0.1.0 commit ec24ca5ba6b9da9239f4069078b9e467df37caa2. No v0.1.1 tag,
push or GitHub release is created in Phase 5. Never move or recreate v0.1.0.
The original research checkout/fork and running four-sample pilot are untouched.

The project MIT license and Huntsman acknowledgement remain in force. The exact
vendored MIT breakclone source carries its upstream notice. The modified LLR
helper, reference payloads, package archives and container images remain external
under their own terms. No individual project-contributor permission record is
required or fabricated. Source readiness is distinct from instruction to publish.

## Candidate audit

```bash
python verify_release.py --commit HEAD --require-ready
PYTHONDONTWRITEBYTECODE=1 PUBLIC_NEXTFLOW=nextflow \
  python -m unittest discover -s public_relatedness/tests -v
```

Check exact allowlist/checksums, bundled source provenance, vendor notice, no
private payloads/secrets/binaries, all numerical gates and v0.1.0 identity.
The history audit checks the independent clean root and every release descendant;
no original research ancestry is imported. The new source packaging identities
remain separate from the original full-file hashes. New runtime recipes are not
claimed to be built, numerically validated or portable.

## Prospective commands after a separate publication instruction

Export only the approved candidate branch into a fresh object database on an
operator-selected scratch volume. Inspect every object, require no alternates,
no unrelated refs and no extra objects. Do not clone the research repository.

```bash
set -euo pipefail
PUBLIC_URL=https://github.com/NasoLab/swgs-relatedness.git
BASE_COMMIT=ec24ca5ba6b9da9239f4069078b9e467df37caa2
CANDIDATE_REF=refs/heads/development/v0.1.1-source-packaging
CANDIDATE_COMMIT=$(git rev-parse "$CANDIDATE_REF^{commit}")
python verify_release.py --commit "$CANDIDATE_COMMIT" --require-ready
git merge-base --is-ancestor "$BASE_COMMIT" "$CANDIDATE_COMMIT"
PUBLISH_ROOT=$(mktemp -d /mnt/swgs/swgs-v011.XXXXXX)
git bundle create "$PUBLISH_ROOT/candidate.bundle" "$CANDIDATE_REF"
git clone --no-tags --single-branch -b development/v0.1.1-source-packaging "$PUBLISH_ROOT/candidate.bundle" "$PUBLISH_ROOT/export"
cd "$PUBLISH_ROOT/export"
python verify_release.py --commit "$CANDIDATE_COMMIT" --require-ready
git fsck --full --no-reflogs
git rev-list --objects "$CANDIDATE_COMMIT"
git cat-file --batch-all-objects --batch-check='%(objectname) %(objecttype) %(objectsize)'
git remote add publication "$PUBLIC_URL"
```

The repository is no longer empty: it contains the approved v0.1.0 main/tag.
Before proposing a new push, verify that main is still BASE_COMMIT, v0.1.0 still
peels to BASE_COMMIT, and v0.1.1 is absent. If another commit/tag has appeared,
stop for review rather than overwriting or silently merging it.

```bash
REMOTE_REFS=$(git ls-remote publication refs/heads/main 'refs/tags/v0.1.0^{}' refs/tags/v0.1.1)
printf '%s\n' "$REMOTE_REFS"
git push --dry-run publication "$CANDIDATE_COMMIT":refs/heads/main
```

Only after approving the exact candidate, object inventory, regression evidence
and dry run would the new annotated tag and atomic publication be performed:

```bash
git tag -a v0.1.1 "$CANDIDATE_COMMIT" -F release/v0.1.1-tag.txt
git push --atomic publication "$CANDIDATE_COMMIT":refs/heads/main refs/tags/v0.1.1:refs/tags/v0.1.1
gh release create v0.1.1 --repo NasoLab/swgs-relatedness --verify-tag \
  --title 'v0.1.1 — Development' --notes-file RELEASE_NOTES.md --prerelease
```

Those mutation commands are documentation only in Phase 5. Do not use force,
--all, --mirror or --tags, and do not publish internal images or historical data.
