# SWGS Relatedness

**v0.1.1 — Development**

SWGS Relatedness is a shallow whole-genome sequencing pipeline for evaluating
tumour relatedness using copy-number profiles. It processes paired-end sequencing
reads and reports quantitative comparisons between user-defined sample pairs.

## What the software does

The Nextflow workflow trims FASTQs with Trimmomatic, aligns to hg38 with BWA-MEM2,
sorts and indexes alignments with samtools, and marks duplicates with Picard.
QDNAseq produces 500-kb copy-number profiles using the hg38 PE150 annotation;
CGHcall calls copy-number states across the complete input cohort. The pipeline
then calculates Pearson correlation (PCC), log-likelihood ratio (LLR) and
historical breakpoint `fraction_shared` for each ordered comparison.

## Quick Start

Install Nextflow 24.10.3, compatible Java, Python >=3.9 and Apptainer with its
`singularity` command interface. **Obtain and configure the validated runtime
images and frozen reference resources separately** using the
[setup instructions](docs/USAGE.md#requirements). This release does not install
them automatically; full end-to-end and cross-host validation remain pending.

Use your own writable mounted storage in place of `/mnt/swgs`:

```bash
git clone https://github.com/NasoLab/swgs-relatedness.git
cd swgs-relatedness
mkdir -p /mnt/swgs/run
cp public_relatedness/examples/{samples.tsv,pairs.tsv,run-params.json,runtime.config} /mnt/swgs/run/
```

Edit the [sample](public_relatedness/examples/samples.tsv) and
[pair](public_relatedness/examples/pairs.tsv) manifests with your FASTQ paths and
comparisons. Configure the copied `runtime.config` as described in
[runtime setup](docs/USAGE.md#runtime-setup), then set the four standard inputs
in `/mnt/swgs/run/run-params.json`:

```json
{
  "samples": "/mnt/swgs/run/samples.tsv",
  "pairs": "/mnt/swgs/run/pairs.tsv",
  "resource_directory": "/mnt/swgs/resources",
  "outdir": "/mnt/swgs/results"
}
```

After completing [resource verification and preflight](docs/USAGE.md#run), run
from the repository root:

```bash
nextflow -C public_relatedness/nextflow.config,/mnt/swgs/run/runtime.config \
  run public_relatedness/main.nf -profile singularity \
  -params-file /mnt/swgs/run/run-params.json -work-dir /mnt/swgs/work
```

## Outputs

The configured `outdir` contains:

- `sample_results.tsv`: sample processing status, QC measurements and copy-number
  profile locations/provenance.
- `pair_results.tsv`: ordered sample comparisons, PCC, LLR, shared/private
  breakpoint counts, `fraction_shared` and metric status.

Scores do not assign relatedness classifications. See
[output descriptions](docs/USAGE.md#outputs) for columns and status interpretation.

## Documentation

Start with the **[detailed usage guide](docs/USAGE.md)** for installation,
references, runtime configuration, manifests, all workflow parameters and troubleshooting.

- [Scientific methods and metric definitions](public_relatedness/METRIC_ADAPTERS.md)
- [Reference identities and acquisition](public_relatedness/references/README.md)
- [Runtime inventories and restoration requirements](public_relatedness/environments/README.md)

## Acknowledgements and license

This pipeline incorporates and adapts components originally developed by the Huntsman group, including workflows for sequencing-read trimming, alignment, duplicate marking, and QDNAseq copy-number analysis.

We acknowledge the contributions of Maxwell Douglas, Ding Ma, Sheila Nicholson, Branden Lynch, and other contributors to the original pipeline.

The tumour-relatedness analysis and public workflow integration were subsequently developed and extended at Canada’s Michael Smith Genome Sciences Centre.

Project code is available under the [MIT license](LICENSE). External packages,
reference assets and container images retain their own terms; preserve the
[third-party notices](THIRD_PARTY_NOTICES.md) and [contributor credits](AUTHORS.md).
