# SWGS Relatedness usage guide

This guide describes the v0.1.1 development workflow. Start with the
[project overview](../README.md), then follow the setup and run steps below.
Examples use fictional sample IDs and `/mnt/swgs` as operator-selected mounted
storage. Replace those paths with your own; keep inputs and runtime assets outside Git.

- [Requirements](#requirements)
- [References](#references)
- [Runtime setup](#runtime-setup)
- [Manifests](#manifests)
- [Configure](#configure)
- [Run](#run)
- [Parameters](#parameters)
- [Outputs](#outputs)
- [Troubleshooting](#troubleshooting)
- [Scientific methods and validation](#scientific-methods-and-validation)

## Requirements

Install Nextflow 24.10.3, compatible Java, Python >=3.9 and Apptainer/Singularity
on Linux x86_64. Nextflow uses the `singularity` command interface. The manifest
validator runs with host Python; scientific tasks use the configured containers.
The current process definitions request up to 16 CPUs and 128 GB memory per task.
Ensure your workstation or scheduler can satisfy the requests and has sufficient
storage for FASTQs, BAMs, temporary files and Nextflow work directories.

Clone the repository and copy the examples into your mounted storage:

```bash
git clone https://github.com/NasoLab/swgs-relatedness.git
cd swgs-relatedness
mkdir -p /mnt/swgs/run
cp public_relatedness/examples/{samples.tsv,pairs.tsv,run-params.json,runtime.config,runtime-params.json} /mnt/swgs/run/
```

Full FASTQ runs use four digest-pinned public OCI images and the hosted,
checksum-verified metrics SIF. Nextflow retrieves upstream images as needed;
metrics acquisition is an explicit setup step. The metrics SIF contains both
historical R stacks, so a host R/Conda installation is unnecessary. Reference
assets remain separate inputs. All payloads stay outside the source checkout.
See [installation](../public_relatedness/INSTALL.md) and
[external license scope](../public_relatedness/LICENSING.md); source MIT licensing
does not change image, package or reference terms.

## References

Place these files together in `resource_directory`. The
[reference manifest](../public_relatedness/references/manifest.json) specifies
the full SHA256s; the [reference guide](../public_relatedness/references/README.md)
describes provenance, acquisition and generation limitations.

| File | Requirement |
| --- | --- |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna` | Exact hg38 no-alt analysis-set FASTA |
| FASTA sidecars `.0123`, `.amb`, `.ann`, `.bwt.2bit.64`, `.pac` | Five adjacent BWA-MEM2 indexes, each named using the full FASTA filename plus its suffix |
| `1000g_hg38_bins_500kbp_PE150.rds` | Approved hg38 paired-end PE150, 500-kb annotation; PE50 is not interchangeable |
| `pfreq_lusc_tcga_split.csv` | Frozen TCGA LUSC PFREQ model for pair scoring |
| `clonality_analysis_PFREQ_MOD.R` | Exact external modified clonality helper for pair scoring; source identity in [scientific_sources.json](../public_relatedness/scientific_sources.json) |

The PE150 SHA256 is
`1d62a94b9a88845978c7bf709d00b35b0f3b1243ef894b442c3ac2861a23337c`.
Do not substitute annotations, regenerate indexes or retrain the model to bypass
an identity check. PFREQ and the modified helper are unnecessary for cohort-only
QC when `pairs` is omitted. The full resource-directory verifier nevertheless
checks the complete set, including both pair-scoring assets.

Optional downloads retrieve the exact public upstream PFREQ/helper files and
verify their checksums. Fetching is explicit and subject to upstream terms:

```bash
python public_relatedness/bin/prepare_resources.py --resources /mnt/swgs/resources \
  --fetch pfreq --fetch llr-helper
```

`--fetch hg38` additionally supports the specified NCBI FASTA archive, verifying
the decompressed bytes. The command does not download or regenerate PE150 bins
or BWA-MEM2 indexes. Existing mismatching files are not overwritten.

## Runtime setup

Download the validated metrics SIF once:

```bash
python public_relatedness/bin/prepare_runtimes.py --resources /mnt/swgs/resources --fetch-metrics
```

The fixed source is [metrics-internal.sif](https://bcgsc.ca/downloads/rcorbett/metrics-internal.sif).
Its mandatory SHA256 is
`ae7c40c285c19a6db6d01bb61f839cdd348f4cfd3f7510ae533091e2ed9f7151`.
Setup saves it as `/mnt/swgs/resources/containers/metrics.sif`, which the full
workflow locates automatically from `resource_directory`. Wrong/partial downloads
are not published, valid existing files are reused, and mismatching files are
never overwritten. No checksum override or image rebuilding is performed.

To reuse a local copy without another download, use `--existing-metrics /path/to/metrics.sif`
instead of `--fetch-metrics`. The file is verified and hard-linked on the same
filesystem. Across filesystems, choose a cache on that volume or use the existing
`metrics_container` path override; setup does not silently copy another 3.22 GiB.
`--verify` verifies a cached SIF without network access. For a different cache,
replace `--resources` with `--directory DIRECTORY` and set `image_directory` to
that directory in the runtime configuration and preflight JSON.

The other four runtimes are pulled automatically by Nextflow/Apptainer using
immutable Linux/amd64 manifests from
[runtime_images.json](../public_relatedness/environments/runtime_images.json):

| Runtime | Recorded software | Public source |
| --- | --- | --- |
| Trimming | Trimmomatic 0.40; Java 11.0.28+6 | `staphb/trimmomatic` at the recorded digest |
| Alignment | BWA-MEM2 2.2.1; samtools/HTSlib 1.12 | `blcdsdockerregistry/bwa-mem2_samtools-1.12` at the recorded digest |
| Duplicate marking | Picard 3.5.0-1-gc2a483d49-SNAPSHOT; Java 17.0.19+10 | `broadinstitute/picard` at the recorded digest |
| QDNAseq/CGHcall | R 4.4.3; Bioconductor 3.20.0; QDNAseq 1.42.0; CGHcall 2.68.0 | `huntsmanlab/qdnaseq` at the recorded digest |

Do not replace these with `latest`, Picard's separate 3.5.0 release tag, or a
newer R image. OCI digests identify manifests; SIF SHA256s identify archive bytes
and are not interchangeable. A fresh OCI-to-SIF conversion can have a different
SIF SHA256 while containing the same software. Exact retained local upstream
archives remain optional overrides when their recorded filenames exist in an
explicit `image_directory`; those overrides must match the original SIF hashes.
An invalid local override stops execution instead of silently changing sources.

The metrics SIF provides `/opt/swgs/bin/Rscript-llr` and
`/opt/swgs/bin/Rscript-general`. The historical LLR stack includes QDNAseq 1.36.0,
Clonality 1.47.0 and QDNAseq.dev 0.1. The general stack includes QDNAseq 1.46.0
and UTANOS 0.1.0.9000. Keep the stacks separate. The
[runtime documentation](../public_relatedness/environments/README.md) contains
complete package inventories, unresolved source/license requirements and
unbuilt restoration recipes; it does not provide a validated turnkey rebuild.

Copy the [runtime configuration](../public_relatedness/examples/runtime.config)
to `/mnt/swgs/run/runtime.config` and set its existing parameters:

```groovy
params {
    image_directory = null // metrics defaults to resource_directory/containers
    temp_directory = '/mnt/swgs/tmp'
}
```

Edit those values in the copied example rather than replacing the whole file.
Keep its contained-execution options, queue setting and disabled optional
trace/report/timeline monitoring for the pinned Picard/Nextflow combination.
Create the temporary directory before preflight:

```bash
mkdir -p /mnt/swgs/tmp /mnt/swgs/work
cp public_relatedness/examples/runtime-params.json /mnt/swgs/run/runtime-params.json
```

Set the same optional `image_directory` and chosen `temp_directory` in the copied JSON file.
Keep `image_directory` null for the default resource-directory cache.
Nextflow reads Groovy `runtime.config`; standalone Python preflight reads
`runtime-params.json`. The JSON is only needed for that standalone preflight.

`temp_directory` must be an existing writable absolute path using only letters,
digits, `/`, `.`, `_` and `-`. It is bound at the same path inside containers.
On a cluster, input/reference/image/work/temp/output paths must be accessible
on every relevant worker. Image cache/build storage is separate from task temp
storage; select it with `APPTAINER_CACHEDIR` and `APPTAINER_TMPDIR` as needed.
Set `NXF_SINGULARITY_CACHEDIR` to a persistent writable project-volume directory
for Nextflow's converted upstream images. The first pull requires network access;
subsequent runs can reuse that cache. These three environment variables are
storage settings, not workflow parameters.

The preserved metrics SIF contains absolute R installation prefixes. Keep the
clone, resources and work below one operational storage directory where possible
and avoid broad mounts over runtime paths. Scoring inputs are copied into the
task directory to reduce source-tree binds. A contained-runtime guard rejects
host mounts hiding embedded R libraries instead of silently using host Conda.
If it fails, inspect the task's `.command.run` binds and use a narrower workspace
layout; do not bind a host Conda installation as a workaround. This guard and
one-host checks do not establish cross-host portability. Empty or corrupted caches need
reacquisition from the same pinned digests.

## Manifests

Use UTF-8 tab-separated files with exactly the headers shown below. Examples are
[samples.tsv](../public_relatedness/examples/samples.tsv) and
[pairs.tsv](../public_relatedness/examples/pairs.tsv).

### Samples

```tsv
sample_id	fastq_1	fastq_2
sampleA	reads/sampleA_R1.fastq.gz	reads/sampleA_R2.fastq.gz
sampleB	reads/sampleB_R1.fastq.gz	reads/sampleB_R2.fastq.gz
```

Provide one local R1/R2 file pair per sample. Relative FASTQ paths resolve from
the sample manifest's directory. Supported extensions are `.fastq`, `.fq`,
`.fastq.gz` and `.fq.gz`; paths must identify existing files, not URLs or globs.
Samples cannot reuse a FASTQ across mates or samples. The validator checks file
presence and naming; malformed sequencing contents can still fail trimming.

### Pairs

```tsv
pair_id	sample1	sample2
comparison1	sampleA	sampleB
```

IDs must start with a letter or digit, contain 1–80 letters, digits, underscores
or hyphens, and must not equal `NA`. Sample IDs and pair IDs must be unique.
Pair members must exist in the sample manifest and be different. A sample may
participate in several comparisons; duplicate unordered pairs, including a
reversed duplicate, are rejected. Blank or whitespace-padded fields and extra
columns are rejected. A supplied pair manifest must contain at least one row.

Sample order, pair row order and sample1/sample2 orientation are preserved.
Every manifest sample belongs to the calling cohort, including samples in no
pairs. Pair selection does not restrict the CGHcall cohort. Cohort composition
can affect calls and downstream scores. Omit `pairs` (or set it to JSON `null`)
for cohort-only QC and a header-only pair-results table.

## Configure

Copy [run-params.json](../public_relatedness/examples/run-params.json) to
`/mnt/swgs/run/run-params.json` and edit only these four standard keys:

```json
{
  "samples": "/mnt/swgs/run/samples.tsv",
  "pairs": "/mnt/swgs/run/pairs.tsv",
  "resource_directory": "/mnt/swgs/resources",
  "outdir": "/mnt/swgs/results"
}
```

Use absolute mounted-volume paths for configuration, references and outputs;
choose a fresh output directory. Relative configuration paths resolve from the
launch directory, not from the JSON file. Bundled scientific source resolves
from the pipeline directory automatically and needs no user-supplied code paths.

## Run

Run these commands from the repository root after setup. They verify the full
resource set, source identities and metrics SIF before launching sequencing tasks.
Preflight lists the four pinned OCI identities but does not inspect images that
have not been pulled; Nextflow/Apptainer performs digest-based retrieval:

```bash
python public_relatedness/bin/prepare_resources.py --resources /mnt/swgs/resources --verify
python public_relatedness/bin/validate_setup.py --params /mnt/swgs/run/run-params.json \
  --profiles singularity --check-images --runtime-params /mnt/swgs/run/runtime-params.json
```

Resolve any preflight failure before proceeding:

```bash
nextflow -C public_relatedness/nextflow.config,/mnt/swgs/run/runtime.config \
  run public_relatedness/main.nf -profile singularity \
  -params-file /mnt/swgs/run/run-params.json -work-dir /mnt/swgs/work
```

`-C` selects the public configuration explicitly. `-work-dir` controls Nextflow
intermediates; `outdir` controls published results; `temp_directory` controls task
temporary files. Retain the work directory and `.nextflow.log` when diagnosing
failures. To resume an interrupted run, repeat the command with `-resume`, using
the same launch/work directories and matching inputs/configuration.

| Defined profile | Use in this release |
| --- | --- |
| `singularity` | Required container engine for full FASTQ execution; local executor by default |
| `slurm,singularity` | Selects Slurm execution with the same containers; requires `sbatch`, shared paths and site configuration; cluster execution is not validated |
| `local` | Local executor; alone it is suitable for configured host cached scoring, not full FASTQ execution |
| `docker` | Defined, but full FASTQ execution explicitly rejects it; Docker execution is not validated |

### Cached copy-number scoring

To score an existing compatible called `QDNAseqCopyNumbers` RDS without FASTQ
processing, supply a separate JSON configuration containing `called_rds`,
`validated_samples`, `validated_pairs`, `resource_directory` and `outdir`.
The validated contracts are the `manifest/samples.tsv` and comma-separated
`manifest/pairs.csv` files emitted by manifest preparation, not the original pair TSV.
Called-object sample membership/order must match the validated sample contract.

For example, create `/mnt/swgs/run/cached-params.json` with paths to existing inputs:

```json
{
  "called_rds": "/mnt/swgs/existing/cohort_500kb_noXY_CGHcall.rds",
  "validated_samples": "/mnt/swgs/existing/manifest/samples.tsv",
  "validated_pairs": "/mnt/swgs/existing/manifest/pairs.csv",
  "resource_directory": "/mnt/swgs/resources",
  "outdir": "/mnt/swgs/cached-results"
}
```

Cached scoring automatically uses `resource_directory/containers/metrics.sif`
when it exists and explicit host executable selectors are absent. Use
`-profile singularity` and the same runtime configuration for that route.
For host scoring, omit `image_directory`/`metrics_container`, set
`metrics_rscript` to `Rscript-llr` and `breakpoint_rscript` to `Rscript-general`
in the cached JSON, and provide both validated wrappers on PATH:

```bash
nextflow -C public_relatedness/nextflow.config run public_relatedness/main.nf \
  -entry CACHED_METRICS -profile local \
  -params-file /mnt/swgs/run/cached-params.json -work-dir /mnt/swgs/cached-work
```

This entry point does not align, normalize or call copy number. Alternatively,
use the validated metrics SIF and singularity runtime configuration. A single
current R installation does not replace the historical stacks.

## Parameters

This is the complete set declared in
[nextflow.config](../public_relatedness/nextflow.config), with effective defaults
from [main.nf](../public_relatedness/main.nf). These are Nextflow parameters,
set in JSON or as `--parameter value`; they are distinct from Nextflow options
such as `-profile`, `-entry`, `-params-file`, `-work-dir` and `-resume`.
`null` means unset. Paths below are relative to the repository unless specified.

### Standard run inputs

| Parameter | Declared default | Effective use |
| --- | --- | --- |
| `samples` | `null` | Required local sample TSV for the FASTQ workflow |
| `pairs` | `null` | Optional local pair TSV; omission selects cohort-only QC |
| `resource_directory` | `null` | Directory of frozen assets; falls back to `SWGS_RESOURCE_DIR`; explicit advanced paths override directory-derived paths |
| `outdir` | `public_relatedness_results` | Published output directory; relative to launch directory when not absolute |

### Execution environment

| Parameter | Declared default | Effective use |
| --- | --- | --- |
| `image_directory` | `null` | Optional metrics-cache directory; otherwise the full workflow uses `resource_directory/containers`. Exact retained local upstream files in this directory override OCI retrieval |
| `temp_directory` | `null` | Task TMPDIR and upstream task scratch; defaults to `/tmp` when unset |
| `metrics_container` | `null` | Defaults to `image_directory/metrics.sif`, or `resource_directory/containers/metrics.sif` for full runs. Cached scoring also auto-selects an existing resource-cache SIF unless host R executables are explicitly selected. SHA256 is always enforced before execution |
| `metrics_rscript` | `null` | `/opt/swgs/bin/Rscript-llr` with a metrics container; otherwise `Rscript-llr` on PATH; runs the public PCC/LLR adapter |
| `breakpoint_rscript` | `null` | `/opt/swgs/bin/Rscript-general` with a metrics container; otherwise `Rscript-general` on PATH; runs breakpoint preprocessing/matching |

### Reference and source overrides

Normal runs do not need these paths. Source overrides remain checksum locked;
they do not select alternative scientific implementations. See
[advanced.config](../public_relatedness/examples/advanced.config).

| Parameter | Declared default | Effective default / constraint |
| --- | --- | --- |
| `reference` | `null` | `resource_directory/GCA_000001405.15_GRCh38_no_alt_analysis_set.fna`; all five adjacent index sidecars are required |
| `pe150_bins` | `null` | `resource_directory/1000g_hg38_bins_500kbp_PE150.rds` |
| `pe150_bins_sha256` | `1d62a94b9a88845978c7bf709d00b35b0f3b1243ef894b442c3ac2861a23337c` | Only the approved PE150 identity is accepted |
| `pfreq` | `null` | `resource_directory/pfreq_lusc_tcga_split.csv`; required for pairs |
| `llr_helper` | `null` | `resource_directory/clonality_analysis_PFREQ_MOD.R`; required for pairs |
| `pcc_llr_runner` | `null` | Bundled `public_relatedness/lib/relatedness/run_pcc_llr.R` |
| `breakpoint_preprocessing` | `null` | Bundled `public_relatedness/lib/relatedness/breakpoint_preprocessing.R` |
| `breakpoint_matching` | `null` | Bundled `public_relatedness/vendor/breakclone/copynumber.R` |
| `fraction_implementation` | `null` | Bundled `public_relatedness/lib/relatedness/fraction_shared_historical.py` |

### Fixed settings, cached inputs and internal aliases

| Parameter | Declared default | Effective use |
| --- | --- | --- |
| `paired_end` | `true` | Full workflow requires `true` |
| `crop_50` | `false` | Full workflow requires `false`; PE50 cropping is not supported |
| `called_rds` | `null` | Required called RDS input for `-entry CACHED_METRICS` |
| `validated_samples` | `null` | Required validated sample TSV for cached scoring |
| `validated_pairs` | `null` | Required validated pair CSV for cached scoring; header-only CSV permits sample-only QC |
| `reference_genome_path` | `null` | Internal alignment-module alias supplied from `reference` by the public workflow; configure `reference` instead |
| `output_directory` | `null` | Internal duplicate-marking-module alias supplied from `outdir`; configure `outdir` instead |

Scientific binning, CGHcall method, model identity, LLR seed placement and
breakpoint tolerance are fixed by the implementation, not exposed as run options.
CPU/memory requests are Nextflow process directives, not additional `params` keys.

### Setup utility options

| Utility | Options and defaults |
| --- | --- |
| `prepare_runtimes.py` | Choose `--resources DIRECTORY` or `--directory CACHE`; choose `--fetch-metrics`, `--existing-metrics FILE` or `--verify`. Downloading is opt-in and SHA256 verification is mandatory |
| `prepare_resources.py` | `--resources DIRECTORY` required; repeatable `--fetch hg38`, `--fetch pfreq` or `--fetch llr-helper` defaults to no downloads; `--verify` defaults to off |
| `validate_setup.py` | `--params JSON` required; `--runtime-params JSON` optional; `--profiles` defaults to `singularity`; `--check-images` and `--metadata-only` default to off |

`--metadata-only` checks structure/presence without verifying file contents and
is not an identity-validation substitute. Setting `image_directory` also triggers
image checks, even without `--check-images`. With no requested action,
`prepare_resources.py` does not fetch or verify assets. Both utilities support
`--help`. Do not pass their hyphenated CLI options as Nextflow parameter names.

## Outputs

Final tables are written directly under `outdir`. The full FASTQ workflow also
publishes validated manifests, duplicate-marked alignments, segmented profiles,
and the cohort CGHcall object.

| File or directory under `outdir` | Contents |
| --- | --- |
| `sample_results.tsv` | One row per manifest sample, in manifest order |
| `pair_results.tsv` | One row per ordered comparison; header only for cohort-only QC |
| `manifest/` | Validated sample TSV, pair CSV, expected sample order and cohort metadata |
| `alignment_outputs/` | Duplicate-marked BAMs, indexes and Picard metrics by sample |
| `relative_cn/qdnaseq/pe/500kb/500kb_noXY_copyNumbersSegmented.rds` | Segmented QDNAseq profiles |
| `cghcall/cohort_500kb_noXY_CGHcall.rds` | Called complete-cohort object, with an accompanying provenance text file |
| `metrics/metric_provenance.json` | Scientific asset/profile hashes, method identity, pair ordering, seed/execution metadata and statuses |
| `metrics/intermediate/*environment.txt` | Recorded R environment information when emitted |

Trimmed FASTQs, pre-duplicate-marking alignments and other task intermediates
remain in the Nextflow work directory. Cached scoring publishes the metric
tables/provenance, not newly created upstream alignment/calling outputs.

### Sample columns

`sample_id`, `processing_status`, `qc_status`, `usable_bins`,
`finite_segmented_bins`, `call_states`, `profile_location`, `profile_sha256`,
`method_version`, `provenance_location`.

`processed` indicates processing completion. `qc_status=not_assessed` means no
new QC pass/fail classification is assigned; inspect the raw measurements.
For full runs, profile locations are relative to `outdir`; cached runs record
the input called-object path.

### Pair columns

`pair_id`, `sample1`, `sample2`, `pcc`, `llr`, `shared`, `private_sample1`,
`private_sample2`, `total`, `fraction_shared`, `fraction_shared_rational`,
`method_version`, `processing_status`, `pcc_status`, `llr_status`,
`fraction_shared_status`.

Scores retain numerical precision, and the fraction also has an exact rational
representation. `complete` indicates computed metrics; `failed_metrics` signals
a metric failure; `unsupported_fraction_shared` signals unsupported arithmetic.
Both-zero or negative-private cases retain raw counts and report `NA` for the
fraction with an explicit status. These scores do not impose relatedness thresholds.
Stub runs report `stub_not_computed` and `NA`, never scientific results.

## Troubleshooting

Preflight stops at the first failure. Its explicit file checks include the
configured path and relevant installation documentation; Nextflow, manifest
parsing and third-party tools may report generic errors instead.

| Symptom | Action |
| --- | --- |
| Missing FASTQ or malformed TSV header | Check exact tab-separated headers, local file paths, extensions and manifest-relative FASTQ paths |
| Duplicate sample/pair, self-comparison or missing member | Use unique IDs, remove duplicate unordered comparisons and reference existing samples |
| Missing reference/helper/annotation | Verify `resource_directory` and expected filenames; use the [acquisition guide](../public_relatedness/INSTALL.md); PE150/index files must be supplied separately |
| Reference, source or image checksum mismatch | Obtain the recorded asset; do not replace an expected hash with the hash of an unvalidated substitute |
| Missing metrics image or FASTQ runtime-profile error | Run `prepare_runtimes.py --resources DIRECTORY --fetch-metrics`, check the cache path and use `-profile singularity`; Docker is not a full-workflow alternative |
| OCI download/conversion fails | Check registry/network access, cache space and permissions; retry the unchanged digest with a clean/private cache if needed. Do not switch to a different tag |
| Missing `singularity`, `sbatch` or R executable | Check the selected profile and PATH; cached host scoring needs both validated R wrappers |
| Temporary directory invalid or a bind/mount fails | Create an absolute writable directory with the permitted characters and verify the same path on execution workers |
| Output directory already contains results | Select a fresh `outdir`; use Nextflow `-resume` with the original work directory for interrupted runs |
| Picard timestamp/monitoring failure | Retain disabled trace/report/timeline settings from the runtime example |
| Called-object class, cohort order or high-level CGHcall-state guard fails | Check provenance, calling method and exact cohort membership/order; the inherited guard requires observed high-level states; do not fabricate states or relax the guard |
| `unsupported_both_zero` or `unsupported_negative_private` | Interpret the explicit unsupported status and preserved counts; no replacement fraction is defined |
| Scientific task fails | Preserve `.nextflow.log` and that task's work directory; inspect `.command.sh`, `.command.err`, `.command.out` and `.command.log` before changing configuration |

## Scientific methods and validation

Read the [metric contract](../public_relatedness/METRIC_ADAPTERS.md) for PCC
rounding/log2/bin selection, inherited LLR chromosome-arm/model processing and
the inclusive 2.5-Mb all-overlap breakpoint calculation. LLR consumes randomness
sequentially in one ordered pair loop; it must not be split into independently
seeded or parallel pair tasks. [Scientific source provenance](../public_relatedness/scientific_sources.json)
records the frozen implementations and hashes.

See [cached regression instructions](../public_relatedness/README.md#authorized-cached-regression-checks),
[release validation notes](../RELEASE_NOTES.md) and
[recorded verification](../verification/release_tests.json) for test evidence.
End-to-end and cross-host validation remain pending. Synthetic stub artifacts
test orchestration and are not biological validation data. No sequencing test
dataset is bundled. Project code is covered by [MIT](../LICENSE); external
packages, models, reference assets and images retain their own terms and
[third-party notices](../THIRD_PARTY_NOTICES.md).
