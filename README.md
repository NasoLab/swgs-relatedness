# Public shallow-WGS relatedness pipeline — v0.1.0 development

**Development snapshot; end-to-end validation pending. Publication licensing is
not yet cleared.** This local release candidate contains pipeline code, tests,
configuration templates and provenance metadata. It contains no sequencing
reads, clinical tables, research workbooks, reference payloads or images.

The workflow connects paired FASTQs to Trimmomatic, BWA-MEM2/samtools, Picard,
QDNAseq 500-kb hg38 profiles, complete-cohort CGHcall and ordered PCC, LLR and
historical breakpoint `fraction_shared`. Sample and pair manifests are explicit;
multiple comparisons may use the same sample. No new relatedness thresholds or
scientific algorithms are introduced.

## Validation status

Cached numerical regressions passed in the originating development environment:
PCC **66/66**, seeded LLR **62/62**, and historical breakpoint counts/fractions
**38/38**. Isolated runtime checks and container stub orchestration also passed.
These are historical validation results, not a claim that this snapshot's
end-to-end FASTQ workflow or a public container has been validated. The separate
internal pilot remains in progress and is not modified by this snapshot.
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

[LICENSE](LICENSE) records the pending project license; no open-source grant has
been invented. Preserve [author credits](AUTHORS.md) and review
[third-party notices](THIRD_PARTY_NOTICES.md) and the [permissions audit](public_relatedness/LICENSING.md).
The unpublished source-restoration recipes and internal metric snapshots are
not public distribution clearances.

This branch starts with a new root commit. It does not include the development
repository's research history, and it must not be merged with that history.
It also does not remove anything already reachable from existing remote refs.
Publication requires a separate owner review and explicit authorization; see
[PUBLISHING.md](PUBLISHING.md). No push, tag or public release was performed.
