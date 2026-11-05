# v0.1.0 — Development

Prepared for [NasoLab/swgs-relatedness](https://github.com/NasoLab/swgs-relatedness).
This is a development source release. No push, tag or GitHub release has been
performed. Project licensing remains pending the maintainer's final decision;
MIT is proposed and has not been applied to the unresolved legacy scope.

## Purpose and included components

The Nextflow workflow connects paired FASTQs to Trimmomatic, BWA-MEM2/samtools,
Picard, QDNAseq hg38 PE150 500-kb profiles, complete-cohort CGHcall and ordered
PCC, LLR and historical breakpoint `fraction_shared` adapters. It includes
manifest validation, configuration examples, installation/usage documentation,
environment specifications, reference identities, synthetic tests and cached
regression infrastructure. Work, temporary and published-output storage are
configurable. Sample/pair outputs retain precision, orientation and method status.

## Scientific methods

PCC preserves QDNAseq usable-bin selection, three-decimal segmented values, log2
transformation and Pearson correlation. LLR preserves the frozen TCGA LUSC PFREQ
model, historical chromosome-arm preprocessing and inherited implementations,
with seed 1337 set once and sequential scoring in input pair order. Breakpoint
matching preserves same chromosome, DUP/DEL direction, start/end boundary type,
inclusive 2.5-Mb tolerance and every eligible overlap. Unsupported both-zero or
negative-private cases retain explicit statuses. No new classification thresholds
or alternative algorithms are introduced.

## Validation

Prior contained-runtime cached gates passed: PCC **66/66**, seeded LLR **62/62**
and historical breakpoint counts/fractions **38/38**. A preceding one-pair cached
workflow comparison matched all metric strings, counts and orientation exactly.
These are originating checkpoint results; the full historical gates were not
rerun for this documentation/destination update. See [recorded numerical evidence](public_relatedness/verification/phase4_runtime_summary.json).

Final lightweight results and source-identity checks are recorded in
[release verification](verification/release_tests.json). The history auditor
checks every reachable clean release snapshot and rejects unexpected files,
modified hashes, known secret markers, unrelated ancestry and merges.
**End-to-end FASTQ validation and cross-host reproducibility remain pending.**
This is not a stable or clinically validated release.

## External requirements and known limits

Operators must supply authorized byte-identical hg38/indexes, PE150 annotation,
frozen PFREQ and scientific implementations, together with the recorded runtimes.
No sequencing data, clinical metadata, research workbooks, scientific output
payloads, reference payloads, package source or container images are bundled.
Reference-generation receipts and public acquisition paths are incomplete.
Source-restoration Dockerfiles remain unbuilt/unvalidated. The retained Picard
image requires the documented optional resource-monitoring workaround.

## Attribution and licensing

The exact Huntsman group acknowledgement and original contributor credits are
preserved in the [README](README.md#acknowledgements) and [AUTHORS.md](AUTHORS.md).
Third-party attribution remains in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
The four retained legacy pipeline files still lack a confirmed ownership/MIT
distribution grant. [LICENSE](LICENSE) records the pending decision; the MIT
proposal does not relicense external packages, scientific implementations,
references or images. No copyright holder or approval reference is inferred.

## Release and history preparation

The independent clean root and release-only descendants contain no research
commits. Scientific R files, workflow modules, model/resource identities and
parameters are unchanged from that root. The running internal FASTQ pilot and
the original fork are untouched by this destination preparation.

The selected destination is the existing empty non-fork NasoLab/swgs-relatedness
repository. The planned annotated tag is `v0.1.0`, with title
**v0.1.0 — Development** and a GitHub prerelease designation. Its annotation is
prepared in [release/v0.1.0-tag.txt](release/v0.1.0-tag.txt); no tag exists from
this preparation. [PUBLISHING.md](PUBLISHING.md) contains gated commands for the
maintainer's approval. The original fork's historical exposure is a separate
owner-led issue and is not remediated by this source release.
