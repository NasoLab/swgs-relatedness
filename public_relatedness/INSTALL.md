# Installation — v0.1.1 development candidate

Project scientific source is bundled; operators supply sequencing inputs,
frozen external assets and an execution environment. No internal research source
directory is needed. End-to-end and cross-host validation remain pending.

## 1. External assets

Create a resource directory outside the checkout. The normal run configuration
has only `samples`, `pairs`, `resource_directory` and `outdir`. FASTQs are resolved
relative to the sample manifest; source paths are resolved relative to the
installed pipeline, independent of the launch directory. A resource-directory
path is resolved from the launch directory; use an absolute mounted-volume path.
`SWGS_RESOURCE_DIR` is an alternative to the JSON resource_directory key.

| Required artifact | Acquisition / validation |
| --- | --- |
| `GCA_000001405.15_GRCh38_no_alt_analysis_set.fna` | Optional `prepare_resources.py --fetch hg38` streams the exact NCBI gzip and verifies the decompressed frozen SHA256; no large FASTA download was repeated during Phase 5 |
| Five adjacent FASTA sidecars `.0123`, `.amb`, `.ann`, `.bwt.2bit.64`, `.pac` | Operator-supplied exact BWA-MEM2 2.2.1 set; historical generation receipt/public download missing; hashes enforced |
| `1000g_hg38_bins_500kbp_PE150.rds` | Operator-supplied approved annotation; no established public acquisition/generation recipe. SHA256 `1d62a94b9a88845978c7bf709d00b35b0f3b1243ef894b442c3ac2861a23337c`; PE50 never substitutes |
| `pfreq_lusc_tcga_split.csv` | Optional direct pinned-upstream `--fetch pfreq`; original hash enforced; not redistributed/retrained |
| `clonality_analysis_PFREQ_MOD.R` | External third-party implementation, not a reference model. Optional direct pinned-upstream `--fetch llr-helper`; hash `fed28e2eca2ae213957c5e382e8e3deee698aae1d9eed0d39b57401e7cdc7f35`; modified-code terms need upstream clarification before vendoring |

All reference filenames, full checksums and provenance are in the unchanged
[reference manifest](references/manifest.json). The helper URL and all bundled
source identities are in [scientific_sources.json](scientific_sources.json).
Public access is not a redistribution grant; users must have lawful access/use
under the applicable terms. Downloading is explicit, never a hidden workflow
side effect. Existing mismatching files are not overwritten; partial or wrong
hash downloads are removed. No indexes or annotations are regenerated. Real FASTQ execution also verifies
reference, source and runtime hashes before launching alignment, so skipping the
standalone preflight does not permit a reference or code substitution.

```bash
python public_relatedness/bin/prepare_resources.py --resources /mnt/swgs/resources \
  --fetch pfreq --fetch llr-helper
python public_relatedness/bin/prepare_resources.py --resources /mnt/swgs/resources --verify
```

The small PFREQ/helper downloads were actually checked against their frozen hashes.
FASTA directory availability was checked previously; full large archive retrieval
was not repeated. The generic gzip/download/checksum path has synthetic tests.
Run standalone `validate_setup.py` before Nextflow. Its explicit file-presence
checks report the resource role, configured path (or that it is not configured)
and this installation guide. Missing reference-file errors point to acquisition/verification help;
missing image errors also point to the runtime inventory. Preflight stops at the
first failure; it does not automatically obtain missing resources.

Nextflow, manifest parsing and third-party tools may instead report generic
filesystem, mount or package errors. Not every failure includes detailed
acquisition instructions. Use the asset table above, the
[reference guide](references/README.md) and the
[runtime setup guide](environments/README.md) to resolve those failures. Missing
PE150/index assets and validated images still require separate acquisition.
No historical cohorts, raw reads or clinical workbooks are distributed.

## 2. Execution environment

Use Nextflow 24.10.3, compatible Java, Python >=3.9 and Apptainer/Singularity.
[Runtime inventories](environments/README.md) preserve the exact scientific
versions. The complete FASTQ path currently requires the singularity profile and
five local byte-identical SIF archives from
[runtime_images.json](environments/runtime_images.json). No approved OCI manifest
digest is known, so automatic registry pulls of mutable tags are disabled.
Docker and cross-host execution are not validated.

Copy [runtime.config](examples/runtime.config) outside Git and set image_directory
and a writable temp_directory. Its images select trimming, alignment, duplicate
marking, QDNAseq/CGHcall and combined metric roles separately. `metrics.sif` must
match the frozen metrics hash and provide `/opt/swgs/bin/Rscript-llr` plus
`/opt/swgs/bin/Rscript-general`; these wrappers keep the validated R 4.3.3 and
R 4.5.3 stacks separate. The QDNAseq stack remains R 4.4.3. The existing validated
image is internal, not published; acquisition/distribution rights are separate.

For operators without those archives, the [source-restoration procedure](environments/README.md#phase-5-source-restoration-procedure)
provides distinct-prefix recipes, explicit Conda locks and checked local R source
archives. It is not yet a complete public rebuild: exact archives/source receipts
for every manual overlay, QDNAseq.dev rights and original upstream OCI digests
remain unresolved. Do not substitute newer packages to fill gaps. Build outputs
must pass all numerical gates before being registered as a new validated runtime;
the recipes themselves remain unbuilt/unvalidated in this phase.

Host/cached scoring may instead use `Rscript-llr` and `Rscript-general` on PATH
(or explicit advanced executable overrides). Install each validated stack in its
own prefix and expose wrappers; verify installed versions and run the cached
66/62/38 gates. One current R installation is not equivalent to the historical
LLR environment. Package source and license obligations remain external.

## 3. Validate and run

```bash
python public_relatedness/bin/validate_setup.py --params /path/to/run-params.json \
  --profiles singularity --check-images --runtime-params /path/to/runtime-params.json
nextflow -C public_relatedness/nextflow.config,/path/to/runtime.config \
  run public_relatedness/main.nf -profile singularity \
  -params-file /path/to/run-params.json -work-dir /mnt/swgs/work
```

For standalone preflight, include image_directory and any executable overrides
in a private merged params JSON or pass `--runtime-params /path/to/runtime-params.json`;
Groovy runtime.config is used by Nextflow, not parsed by Python.

Work, temporary and output storage must be mounted and writable on each worker.
temp_directory retains the same path inside containers; image cache/build storage
is selected separately via APPTAINER_TMPDIR/APPTAINER_CACHEDIR. The tested Picard
optional trace/report/timeline workaround is retained in runtime.config. No
scientific image, utility, parameter or scoring seed is changed to avoid it.
For Slurm, combine `-profile slurm,singularity` and verify shared-worker paths.

## Bundled defaults and advanced overrides

The runner and matcher are copied byte-for-byte; four preprocessing expressions
and seven Python production functions are extracted without AST changes. Their
original full-file hashes and derived-file hashes remain distinct and explicit.
The analysis-only regression CLI and old cohort/workbook reads are not bundled.
Existing adapters still load the same definitions; historical classification
functions in the legacy runner are not exposed as public score thresholds.

[advanced.config](examples/advanced.config) is optional. Overrides must match the
frozen packaged source identities; changing a path never authorizes a changed
scientific implementation. [Cached regression setup](README.md) uses authorized
private fixtures, not public sample data. The v0.1.0 tag and running pilot are
unmodified by this candidate.
