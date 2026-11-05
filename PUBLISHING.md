# Publication procedure — currently blocked

This is a local **v0.1.0 development** candidate. No push, tag or public release
has been performed. The project has no approved distribution license; the
[publication gate](RELEASE_STATUS.json) is deliberately false. Public release
requires explicit owner authorization and a compatible grant from the applicable
rights holders. External historical resources remain operator-supplied.

The original Git history contains sequencing files, individual-level research
tables, workbooks, references and unrelated analyses. The source checkpoint and
remote master were inventoried privately. Existing remote history also contains
sequencing paths; a clean branch cannot erase those objects, forks or caches.
The owner must separately review existing exposure and choose any remediation.
Do not assume that the remote repository is safe merely because this candidate
has a clean tree. This task does not authorize remote history rewriting.

## Local candidate inspection

Run in the isolated release worktree:

```bash
git status --short
git log --format=fuller --stat
python verify_release.py --commit HEAD
python verify_release.py --commit HEAD --require-publishable
```

The last command intentionally fails while publication is blocked. The audit
checks every snapshot blob, exact allowlist, hashes, text/size/payload/secret
markers, and a single root commit without development ancestry. Pattern scanning
cannot establish ownership or guarantee detection of every possible identifier.
Human review of the selected code and notices is still required. No ancestral
research payload is approved for publication, so the whole ancestry is excluded.

## After separate clearance and explicit publication authorization

Update the license, notices, authorization status and validation evidence only
when supported by approvals. Regenerate the exact allowlist and checksums and
prepare/review a new isolated root candidate if those files change. The commands
below apply to that cleared candidate; they do not authorize changing this
snapshot's gate or rewriting the development checkout. Keep the development
branch and pilot source untouched. Do not merge source history into the candidate.

Export only the approved root ref into a fresh object database. Use new empty
scratch directories; substitute the reviewed commit SHA and candidate branch:

```bash
CANDIDATE_REF=refs/heads/release/public-v0.1.0-development
CANDIDATE_COMMIT=$(git rev-parse "$CANDIDATE_REF")
python verify_release.py --commit "$CANDIDATE_COMMIT" --require-publishable
git bundle create /mnt/swgs/release-candidate.bundle "$CANDIDATE_REF"
git clone --no-tags --single-branch -b release/public-v0.1.0-development /mnt/swgs/release-candidate.bundle /mnt/swgs/publish-check
cd /mnt/swgs/publish-check
python verify_release.py --commit "$CANDIDATE_COMMIT" --require-publishable
git rev-list --count "$CANDIDATE_COMMIT"
git for-each-ref --format='%(refname) %(objectname)'
git cat-file --batch-all-objects --batch-check='%(objectname) %(objecttype) %(objectsize)'
```

Require one approved root commit, no unexpected refs/tags, and an object inventory
containing exactly its reachable commit, trees and allowlisted blobs. A local
clone of the original repository may reuse its object store, so it is not an
acceptable substitute for this bundle isolation. Keep the bundle private until
clearance; it is not a public release artifact.

After the existing remote history has been separately reviewed/remediated under
owner authorization, inspect the exact target branch and dry run from the fresh
export. Configure the destination there, not in the running pilot checkout:

```bash
git remote set-url origin https://github.com/rcorbett-match/swgs-processing-pipeline.git
git push --dry-run origin "$CANDIDATE_COMMIT":refs/heads/public-v0.1.0-development
```

Review the dry run and obtain the separately required publication authorization.
Then the matching single-ref push command is:

```bash
git push origin "$CANDIDATE_COMMIT":refs/heads/public-v0.1.0-development
```

Do not use --all, --mirror, --tags, force, or merge unrelated histories. A branch
push makes that ref and its contents public; it is not a harmless preview. Do not
create a tag or GitHub release as part of this preparation. End-to-end validation
must remain labelled pending until the independent pilot is reviewed.
