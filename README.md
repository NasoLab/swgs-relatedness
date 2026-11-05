# SWGS Processing Pipeline — v0.1.0 — Development

**Development snapshot; end-to-end validation pending. Publication licensing is
not yet cleared.** This local release candidate contains pipeline code, tests,
configuration templates and provenance metadata. It contains no sequencing
reads, clinical tables, research workbooks, reference payloads or images.

The workflow connects paired FASTQs to Trimmomatic, BWA-MEM2/samtools, Picard,
QDNAseq 500-kb hg38 profiles, complete-cohort CGHcall and ordered PCC, LLR and
historical breakpoint `fraction_shared`. Sample and pair manifests are explicit;
multiple comparisons may use the same sample. No new relatedness thresholds or
scientific algorithms are introduced.

## Required inputs and outputs

Supply paired-end FASTQs through the sample manifest, ordered comparisons through
an optional pair manifest, the frozen hg38/PE150 500-kb references and authorized
software runtimes. The manifests use sample IDs supplied by the operator; the
examples contain fictional IDs only.

The workflow writes `sample_results.tsv` with processing status, QC measurements
and copy-number profile provenance, and `pair_results.tsv` with ordered sample
IDs, PCC, LLR, historical shared/private/total breakpoint counts, `fraction_shared`,
method version and processing status. Alignment, segmented/called copy-number
profiles and execution provenance are also produced. See [output contracts](public_relatedness/METRIC_ADAPTERS.md).

## Validation status

Cached numerical regressions passed in the originating development environment:
PCC **66/66**, seeded LLR **62/62**, and historical breakpoint counts/fractions
**38/38**. Isolated runtime checks and container stub orchestration also passed.
These are historical validation results, not a claim that this snapshot's
end-to-end FASTQ workflow or a public container has been validated. End-to-end validation remains pending; the independently running internal pilot
is not modified by this release preparation.
See [validation evidence](public_relatedness/verification/phase4_runtime_summary.json)
and [release notes](RELEASE_NOTES.md). Stub outputs are explicitly uncomputed.

## Installation and execution

Start with [installation](public_relatedness/INSTALL.md),
[environment specifications](public_relatedness/environments/README.md), and
[reference acquisition](public_relatedness/references/README.md). Scientific
runtimes and permission-cleared frozen resources must be supplied separately.
The legacy PCC/LLR runner is deliberately external and checksum locked.

```bash
python public_relatedness/bin/validate_setup.py \
  --params /path/to/private_run_params.json --profiles singularity --check-images

nextflow -C public_relatedness/nextflow.config,public_relatedness/examples/pinned-images.config,public_relatedness/examples/isolated-execution.config \
  run public_relatedness/main.nf -profile singularity \
  -params-file /path/to/private_run_params.json -work-dir /mnt/swgs/work
```

Configure `outdir` for published results and `temp_directory` for tool temporary
files/task scratch. The container profile binds the temporary directory at the
same absolute path. All directories and inputs must be accessible on workers.
The isolated execution example preserves the tested workaround for the retained
Picard image's incompatibility with Nextflow 24.10 optional resource monitoring.
There is no automatic data download, reference regeneration or image publication.

Examples use fictional `sampleA`/`sampleB` IDs and placeholder paths only. No
public sequencing fixture is bundled; internal study consent must not be
inferred from these examples. Raw and derived study data need separate release
authorization, including apparently de-identified CNV profiles.

## Tests and snapshot audit

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s public_relatedness/tests -v
PUBLIC_NEXTFLOW=nextflow PYTHONDONTWRITEBYTECODE=1 \
  python -m unittest discover -s public_relatedness/tests -p test_nextflow.py -v
python verify_release.py
```

The ordinary tests create only synthetic, non-sequencing markers. The opt-in
historical harness requires separately authorized external fixtures; it is not
an invitation to publish those fixtures. See [test instructions](public_relatedness/README.md).
[RELEASE_FILES.txt](RELEASE_FILES.txt) is the exact publication allowlist;
[RELEASE_SHA256SUMS.txt](RELEASE_SHA256SUMS.txt) records its file identities.

## Licensing and publication

[MIT](LICENSE.MIT.proposed) is the intended license for project-owned code and
contributions the project is authorized to distribute. [LICENSE](LICENSE) keeps
the grant pending because authorization for four retained legacy files remains
unconfirmed. Acknowledgement does not replace that authorization. MIT is not
applied to external packages, scientific implementations, references or images. Preserve [author credits](AUTHORS.md) and review
[third-party notices](THIRD_PARTY_NOTICES.md) and the [permissions audit](public_relatedness/LICENSING.md).
The unpublished source-restoration recipes and internal metric snapshots are
not public distribution clearances.

This branch starts with the audited independent root commit and contains only
its clean release-preparation descendants. It does not include the development
repository's research history, and it must not be merged with that history.
It also does not remove anything already reachable from existing remote refs.
Publication requires a separate owner review and explicit authorization; see
[PUBLISHING.md](PUBLISHING.md). No push, tag or public release was performed.

## Known limitations

Required historical implementations and frozen reference assets are external and
must be obtained with permission. Their complete acquisition/generation records
are not recovered. Source-restoration Dockerfiles are unbuilt; cross-host and
end-to-end validation remain pending. The retained Picard image requires the
documented optional-monitoring workaround. No public sequencing test dataset or
relatedness classification thresholds are supplied. These limits are documented
for this source development release; they do not clear redistribution of any
external dependency.

## Acknowledgements

This pipeline incorporates and adapts components originally developed by the Huntsman group, including workflows for sequencing-read trimming, alignment, duplicate marking, and QDNAseq copy-number analysis.

We acknowledge the contributions of Maxwell Douglas, Ding Ma, Sheila Nicholson, Branden Lynch, and other contributors to the original pipeline.

The tumour-relatedness analysis and public workflow integration were subsequently developed and extended at Canada’s Michael Smith Genome Sciences Centre.
