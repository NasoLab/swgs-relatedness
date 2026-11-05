# Runtime specifications and preservation recipes

## Current runtime acquisition

Nextflow selects four public Linux/amd64 OCI manifests pinned in
[runtime_images.json](runtime_images.json). The hosted metrics SIF is acquired
explicitly by `prepare_runtimes.py` with mandatory SHA256 verification and used
from `resource_directory/containers/metrics.sif` (or `image_directory`).
See the [user setup procedure](../../docs/USAGE.md#runtime-setup).
No internal filesystem access is needed to obtain these runtime payloads.
The historical inventories below retain their original evidence scope; matching
software/payload checks are not a completed upstream end-to-end validation.
The metrics archive is supplied unchanged, not reconstructed by these recipes.


Source-restoration Dockerfiles in `containers/` are **unbuilt and unvalidated**.
The inventories below describe the originating environments. Separately, private
installed-prefix preservation SIFs passed the cached metric/isolation checks
recorded in [Phase 4 evidence](../verification/phase4_runtime_summary.json).
Those results do not validate these source-restoration Dockerfiles or establish
cross-host portability. No package, source archive or image is bundled here.

## Observed runtimes

| Role | R | Bioconductor | Key versions | Evidence and limit |
| --- | --- | --- | --- | --- |
| Cached QDNAseq/CGHcall image | 4.4.3 | BiocVersion 3.20.0 | QDNAseq 1.42.0, CGHcall 2.68.0, Biobase 2.66.0, DNAcopy 1.80.0 | Read inside the actual cached SIF; no normalization/calling or numerical image validation performed |
| Host PCC and breakpoint preprocessing | 4.5.3 | BiocVersion 3.22.0 | QDNAseq 1.46.0, CGHcall 2.72.0, Biobase 2.70.0, DNAcopy 1.86.0, utanos 0.1.0.9000 | Existing host environment; PCC 66/66 and breakpoint 38/38 regressions passed |
| Historical host LLR | 4.3.3 | Unknown: BiocVersion absent | QDNAseq 1.36.0, CGHcall 2.62.0, Biobase 2.60.0, DNAcopy 1.74.1, Clonality 1.47.0, QDNAseq.dev 0.1 | Separate existing environment; seeded LLR 62/62 passed; do not infer a coherent Bioconductor release from R alone |

These stacks are deliberately separate. Replacing them with one current R /
Bioconductor installation changes the reproducibility contract. The public
metric task accepts two R executables, so the known host stacks can remain
separate without splitting or parallelizing the ordered LLR pair loop.

Full installed-package/version/dependency/license/source metadata is captured in:

- `qdnaseq-r/r-packages.tsv`: 122 R packages; `runtime.txt`; and
  `system-packages.tsv`: 303 Debian package records from the cached image.
- `general-r/r-packages.tsv`: 373 R packages; `runtime.txt`;
  `conda-packages.tsv` and `conda-explicit-linux-64.txt`: 468 Conda records.
- `llr-r/r-packages.tsv`: 89 R packages; `runtime.txt`;
  `conda-packages.tsv` and `conda-explicit-linux-64.txt`: 178 Conda records.

Conda files retain exact versions, build strings, public artifact URLs and
available MD5/SHA256 metadata. They record the installed Conda layer, **not**
post-install R overlays. They must not be presented as complete rebuilt locks.
Installed R records include `Built`, dependencies, system requirements and
available RemoteSha. Missing archive hashes/commits are not invented. Capture
scripts omit host prefixes and authenticated/private download URLs.

## Upstream executable/image evidence

The cached images were queried with version-only commands:

| Image role | Observed software | OS / Java |
| --- | --- | --- |
| Trimming | Trimmomatic 0.40 | Ubuntu 22.04.5; OpenJDK 11.0.28+6 |
| Alignment | BWA-MEM2 2.2.1, samtools 1.12, HTSlib 1.12 | Ubuntu 20.04.2; samtools/HTSlib compiled with curl, compression, curses and plugin support |
| Duplicate marking | Picard `3.5.0-1-gc2a483d49-SNAPSHOT` | Ubuntu 26.04; Temurin OpenJDK 17.0.19+10 |
| QDNAseq / CGHcall | R/package versions above | Debian trixie/sid; native versions in system inventory |

Nextflow checks used 24.10.3 with Zulu OpenJDK 11.0.1+13-LTS on Rocky Linux 9.2.
The general Conda environment also contains OpenJDK 17.0.18-internal; Java is
not part of the R LLR calculation. Compiler/runtime/BLAS/compression versions
are recorded in native Conda metadata and `runtime.txt`.

[inventory.json](inventory.json) records the four actual SIF SHA256 values,
original declared URIs, OS/runtime evidence and known source commits. A SIF
checksum identifies an existing archive; it is **not an OCI manifest digest**.
The latter was not recovered. The inspected files are not proven byte-identical
to every historical execution merely because their filenames contain `latest`.
The observed Picard snapshot must not be silently replaced with a release.

## Restoration candidates

The explicit Conda files can provision a new Linux x86_64 prefix without solving
for newer scientific versions. After permission review and source-archive
recovery, `restore_r.R` restores mismatched/manual R packages from a **local**
archive manifest. It verifies supplied archive hashes, recorded versions and
permission references, then installs in recorded dependency order without
repository downloads. Missing archives or dependency cycles stop restoration.

The manifest format is `source-archives.example.tsv`. Archive bytes and verified
original archive hashes are not available for every R overlay; QDNAseq.dev's
license is unresolved. Do not fill these gaps with current CRAN/GitHub packages.
Matching version strings alone does not prove source or numerical identity.
The located QDNAseq.dev source checkout is commit
`8714202a7ca90124adba3ecb0d666cadc23f3d11` with a DESCRIPTION indentation fix;
installed packages have no RemoteSha, so complete installed-source identity is
not established. UTANOS records exact RemoteSha
`ae8edc6464ab7bac0939a886dd7f8beae7a7410b`.

`containers/general-r.Dockerfile` and `containers/llr-r.Dockerfile` each require
an independently pinned, permission-cleared micromamba-capable `BASE_IMAGE`, the
appropriate explicit spec, and an external `approved-sources/manifest.tsv` plus
archives. `containers/qdnaseq-r.Dockerfile` preserves an independently recovered
OCI image by digest and checks the recorded R metadata. Its original OCI digest
is unknown. `containers/upstream.def` is an optional local-image preservation
wrapper using a checksum-verified SIF; it does not rebuild upstream tools.

The source-restoration Dockerfiles were not built. No source archives, images
or references are included in this snapshot. Build in a separate private context only after permissions are resolved;
retain license notices and source obligations. Then run `verify_r.R`, all
cached metric gates, and subsequently an authorized small end-to-end validation.
A combined metric container would need both validated R prefixes and regression
checks; this phase does not claim that the separate candidate images already
provide that combined runtime.

Metadata-only checks on existing runtimes:

```bash
/path/to/runtime/bin/Rscript public_relatedness/environments/verify_r.R \
  public_relatedness/environments/llr-r/r-packages.tsv \
  public_relatedness/environments/llr-r/runtime.txt
```

For fresh inventory capture, use `capture_r.R OUTPUT_DIRECTORY` and
`capture_conda.py --prefix PREFIX --output NEW_DIRECTORY`, then review diffs.
Capture is an observation, not permission to update a scientific environment.

## Phase 5 source restoration procedure

The current manifest adds public OCI candidates whose recorded scientific
payloads match the retained upstream images. Original SIF identities remain
baseline/optional local-override identities, not expected hashes of fresh OCI
conversions. Current runtime acquisition uses the four pinned OCI manifests and
the exact hosted metrics SIF. The original source-build receipts remain incomplete. A tag
named latest is not accepted as a reproducibility claim. Images are not included
or uploaded by this candidate. The metrics SIF interface is Rscript-llr and
Rscript-general under /opt/swgs/bin, preserving separate R installations.

The restoration Dockerfiles install the recorded explicit Conda layers into
/opt/swgs/general-r and /opt/swgs/llr-r, restore reviewed local R overlays and
check their versions. metrics.Dockerfile combines those same-prefix artifacts
without relocating either R tree, then exposes the canonical wrappers. Required
external build context: approved-sources/manifest.tsv plus exact source archives,
with archive hashes/terms, and independently pinned base images. Do not fabricate
missing archive hashes or use current packages instead. The original QDNAseq OCI
digest and complete manual R source-archive set have not been recovered. These
are real build inputs still required for a complete public rebuild; recipes are
provided, but a clean-room build has not been completed or validated.

Prospective commands, only with those inputs available, from the environments
build context (do not distribute restricted archives/images):

```bash
docker build -f containers/general-r.Dockerfile --build-arg BASE_IMAGE="$PINNED_BASE" -t local/swgs-general .
docker build -f containers/llr-r.Dockerfile --build-arg BASE_IMAGE="$PINNED_BASE" -t local/swgs-llr .
docker build -f containers/metrics.Dockerfile --build-arg GENERAL_IMAGE="$PINNED_GENERAL" --build-arg LLR_IMAGE="$PINNED_LLR" -t local/swgs-metrics .
```

The input variables must be immutable, independently approved digests. Local
build outputs are not validated merely because versions match. Run verify_r.R
and the 66/62/38 gates inside the newly built runtime, inspect linked dependencies
with cleanenv/containall and no host Conda binds, and test on another host before
claiming portability. A new validated archive hash requires a reviewed runtime
matrix update. No image build, upgrade or publication occurred in Phase 5.
