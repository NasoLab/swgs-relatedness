# v0.1.1 — Development

This development release packages the validated tumour-relatedness source and
simplifies setup for researchers without access to internal research directories.
Publication is pending final approval and the external-image licensing review
described below. The existing v0.1.0 tag is unchanged.

## Changes

- **Bundled scientific source:** the PCC/LLR runner, internal breakpoint
  preprocessing, MIT-licensed BreakClone matcher and historical all-overlap
  `fraction_shared` implementation resolve automatically from the repository.
  Original and packaged source hashes are recorded separately. The inherited
  clonality helper remains externally acquired and checksum locked.
- **Four standard configuration parameters:** `samples`, `pairs`,
  `resource_directory` and `outdir`. Runtime/storage settings and scientific
  overrides are documented separately for advanced setup.
- **Four automatically retrieved public OCI images:** Trimmomatic,
  BWA-MEM2/samtools, Picard and QDNAseq/CGHcall use immutable Linux/amd64
  manifests. Recorded versions are preserved; mutable `latest` tags are not
  used for selection. Exact retained local archive overrides remain supported.
- **Checksum-verified metrics runtime:** the optional `prepare_runtimes.py`
  command downloads the unchanged hosted SIF with mandatory SHA256
  `ae7c40c285c19a6db6d01bb61f839cdd348f4cfd3f7510ae533091e2ed9f7151`.
  A valid cached file is reused; invalid files are not overwritten. Nextflow
  finds it automatically under `resource_directory/containers/metrics.sif`.
- **Clearer setup documentation:** the root Quick Start and detailed
  [usage guide](docs/USAGE.md) cover manifests, resource acquisition, runtime
  setup, writable cache/work/temp volumes, preflight, outputs and troubleshooting.

## Scientific integrity and validation

PCC usable-bin selection, rounding, log2 transformation and correlation are
unchanged. Historical LLR model parameters, pair order, seed placement and
sequential random-number consumption are preserved. Breakpoint matching retains
same-chromosome, direction and boundary-type rules, inclusive 2.5-Mb tolerance,
all eligible overlaps and historical shared/private arithmetic. Unsupported
cases retain explicit statuses. No new relatedness classification is introduced.

The runtime-integration checkpoint freshly passed cached regressions in the
isolated, checksum-verified metrics SIF: **PCC 66/66**, **seeded LLR 62/62** and
**historical breakpoint 38/38**. Maximum absolute differences were
4.996003610813204e-16 for PCC and 4.973799150320701e-14 for LLR (tolerance 1e-12);
breakpoint counts and supplied fraction precision matched exactly. Final
documentation changes do not change scientific files, reference identities,
runtime digests or fixtures; these numerical gates were not rerun for this
documentation-only finalization.

The final lightweight suite passed **75 tests**, including **seven Nextflow stub
tests**, with one optional historical observation test skipped. The preceding
runtime checkpoint also passed a 13-task real-image stub graph and production
cached scoring with an identical first-pair result. Stub commands do not validate
alignment or copy-number calculations. Detailed evidence is recorded in
[verification/release_tests.json](verification/release_tests.json).

## Remaining limitations and distribution status

- **Hosted image clearance is unresolved.** Availability and a matching checksum
  establish image identity, not redistribution permission. The metrics SIF
  contains QDNAseq.dev with an unresolved license placeholder; image-wide
  notices, source obligations and dependency terms are not established as fully
  satisfied by the recorded audit. Public distribution approval cannot be
  confirmed. Resolve this image review before approving publication of the
  candidate as the proposed public-runtime release; see the
  [licensing audit](public_relatedness/LICENSING.md#hosted-metrics-sif-distribution-status).
  Project MIT licensing does not relicense external packages, images or assets.
- **References remain external:** users must supply the recorded hg38 FASTA and
  indexes and exact PE150 500-kb annotation. Frozen PFREQ/helper acquisition is
  opt-in with checksum checks under upstream terms. Reference-generation and
  redistribution records remain incomplete; PE50 or alternative PFREQ models
  are not substitutes.
- **Cross-host portability is unproven.** The metrics SIF retains absolute R
  prefixes. A runtime guard rejects host mounts hiding its R libraries. Use
  narrow operational workspaces; a successful startup alone is not scientific
  equivalence. Source-restoration recipes remain unbuilt/unvalidated, with
  missing archives and licensing records documented.
- **Full end-to-end validation remains pending.** Cached metric regressions and
  stub tests do not establish full FASTQ-to-QDNAseq/CGHcall equivalence. No new
  sequencing analysis or internal pilot results are part of this release review.

The release contains source, documentation, inventories and approved synthetic
tests only: no sequencing data, clinical metadata, reference payloads, container
binaries or historical research outputs. Project MIT licensing, Huntsman group
acknowledgement, contributor credits and upstream BreakClone notices are retained.
The candidate descends only from the independent audited public release history.
