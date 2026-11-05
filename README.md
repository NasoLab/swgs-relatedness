# SWGS Relatedness — v0.1.1 development candidate

MIT-licensed project source for paired-end shallow-WGS tumour relatedness.
This local candidate follows the published v0.1.0 development release; no v0.1.1
push, tag or GitHub release has been made. End-to-end and cross-host validation
remain pending. [NasoLab/swgs-relatedness](https://github.com/NasoLab/swgs-relatedness)
is the public destination.

## Quick Start

These commands target the v0.1.1 candidate; the public clone will contain these
additions after publication.

**Prerequisites.** Install Nextflow 24.10.3, compatible Java, Python >=3.9 and
Apptainer with its `singularity` command interface. Separately configure the
five validated local SIF archives, including QDNAseq R 4.4.3, general R 4.5.3
and historical LLR R 4.3.3. Supply the exact hg38 FASTA/BWA-MEM2 indexes, hg38
PE150 500-kb annotation, frozen PFREQ model and external clonality helper.
See [installation](public_relatedness/INSTALL.md),
[runtime setup](public_relatedness/environments/README.md) and
[reference identities/acquisition](public_relatedness/references/README.md).
These runtimes and resources are not installed by cloning the repository;
public image retrieval and a complete public rebuild are not yet available.

**Clone and prepare inputs.** Use your own writable mounted storage in place of
`/mnt/swgs`; keep inputs, configuration, work, temporary files and results outside Git.

```bash
git clone https://github.com/NasoLab/swgs-relatedness.git
cd swgs-relatedness
mkdir -p /mnt/swgs/run
cp public_relatedness/examples/{samples.tsv,pairs.tsv,run-params.json,runtime.config,runtime-params.json} /mnt/swgs/run/
```

Edit the tab-separated [sample manifest](public_relatedness/examples/samples.tsv)
to point to paired FASTQs; relative FASTQ paths resolve from the manifest directory:

```tsv
sample_id	fastq_1	fastq_2
sampleA	/path/to/sampleA_R1.fastq.gz	/path/to/sampleA_R2.fastq.gz
sampleB	/path/to/sampleB_R1.fastq.gz	/path/to/sampleB_R2.fastq.gz
```

Define ordered comparisons in the [pair manifest](public_relatedness/examples/pairs.tsv):

```tsv
pair_id	sample1	sample2
comparison1	sampleA	sampleB
```

**Configure.** Set these four keys in `/mnt/swgs/run/run-params.json`:

```json
{
  "samples": "/mnt/swgs/run/samples.tsv",
  "pairs": "/mnt/swgs/run/pairs.tsv",
  "resource_directory": "/mnt/swgs/resources",
  "outdir": "/mnt/swgs/results"
}
```

In both copied runtime files, set the same `image_directory` and an existing,
writable `temp_directory`. Nextflow reads `runtime.config`; Python preflight
reads `runtime-params.json`. Keep the runtime configuration's monitoring workaround.
Bundled scientific scripts are located automatically.

**Verify and run.** After supplying the resources and images above, run from the
repository root. The resource directory must contain the exact files listed in
the reference documentation; optional checksum-verified PFREQ/helper downloads
are described in the installation guide.

```bash
python public_relatedness/bin/prepare_resources.py --resources /mnt/swgs/resources --verify
python public_relatedness/bin/validate_setup.py --params /mnt/swgs/run/run-params.json \
  --profiles singularity --check-images --runtime-params /mnt/swgs/run/runtime-params.json
nextflow -C public_relatedness/nextflow.config,/mnt/swgs/run/runtime.config \
  run public_relatedness/main.nf -profile singularity \
  -params-file /mnt/swgs/run/run-params.json -work-dir /mnt/swgs/work
```

With this configuration, `/mnt/swgs/results/sample_results.tsv` contains sample
status, QC and profile provenance; `/mnt/swgs/results/pair_results.tsv` contains
ordered PCC, LLR and historical breakpoint `fraction_shared` results.
End-to-end and cross-host validation remain pending. See
[advanced configuration](public_relatedness/examples/advanced.config) for optional overrides.

## Pipeline and methods

Nextflow connects Trimmomatic, BWA-MEM2/samtools, Picard, QDNAseq hg38 PE150
500-kb copy-number profiles, complete-cohort CGHcall and ordered PCC, LLR and
historical breakpoint `fraction_shared`. Multiple comparisons may reuse a sample.
The project scientific runner, historical preprocessing, all-overlap calculation
and MIT-licensed recovered matcher are bundled and located automatically.

PCC preserves usable bins, three-decimal segmented values, log2 transformation
and Pearson correlation. LLR preserves the frozen TCGA LUSC PFREQ model, historical
chromosome-arm preprocessing, inherited helper and QDNAseq.dev, and one seeded
sequential pair loop. Breakpoint matching preserves same chromosome, DUP/DEL,
boundary type, inclusive 2.5-Mb tolerance and all eligible overlaps. Unsupported
both-zero/negative-private arithmetic remains explicit. No alternative algorithm,
new classification threshold or scientific package upgrade is introduced.

## Minimal run configuration

Copy [run-params.json](public_relatedness/examples/run-params.json) to a private
location and supply just the sample manifest, pair manifest, frozen-resource
directory and a fresh output directory. Code paths are not user inputs.
[Samples](public_relatedness/examples/samples.tsv) and
[pairs](public_relatedness/examples/pairs.tsv) contain fictional identifiers only.
Read [installation](public_relatedness/INSTALL.md) before execution: the frozen
PE150 annotation/index set and execution images are not generally distributed.

```bash
python public_relatedness/bin/prepare_resources.py --resources /mnt/swgs/resources \
  --fetch pfreq --fetch llr-helper
python public_relatedness/bin/prepare_resources.py --resources /mnt/swgs/resources --verify
python public_relatedness/bin/validate_setup.py --params /path/to/run-params.json \
  --profiles singularity --check-images --runtime-params /path/to/runtime-params.json
nextflow -C public_relatedness/nextflow.config,/path/to/runtime.config \
  run public_relatedness/main.nf -profile singularity \
  -params-file /path/to/run-params.json -work-dir /mnt/swgs/work
```

The first command is optional direct-upstream acquisition under the upstream
terms; downloaded content is hash checked and is not committed or redistributed
by this project. Supply FASTA, five BWA-MEM2 sidecars and the PE150 annotation
before `--verify`. A [runtime configuration](public_relatedness/examples/runtime.config)
selects the validated local image directory and writable temporary volume once
per installation. Keep resource/image/work/result directories outside Git.

`sample_results.tsv` contains sample processing status, raw QC measurements and
profile provenance. `pair_results.tsv` contains ordered sample IDs, PCC, LLR,
shared/private/total breakpoints, fraction/rational, method and status. Numeric
precision and orientation are retained. No new pass/fail classifications are
assigned. [Advanced options](public_relatedness/examples/advanced.config) permit
explicit frozen-identity overrides; normal runs do not need them.

## Validation and limits

The prior cached gates passed PCC 66/66, LLR 62/62 and breakpoint 38/38. Phase 5
reruns those gates against the new bundled source; results are recorded in
[verification](verification/release_tests.json) and [release notes](RELEASE_NOTES.md).
Source extraction preserves the original R expressions/Python functions, and
original full-file hashes remain in [source provenance](public_relatedness/scientific_sources.json).
Stub outputs are uncomputed markers, never scientific evidence.

The inherited modified LLR helper remains external: its original Clonality
functions are GPL-3, but the modification's grant is not established in its
source repository. Its exact public acquisition URL/hash are supplied; no
historical internal directory is needed. QDNAseq.dev has an unresolved license
placeholder. PFREQ/PE150 rights and complete generation receipts remain incomplete.
No reference/model is substituted or regenerated. No public sequencing fixture
is included. [External license scope](public_relatedness/LICENSING.md) explains
these execution/distribution boundaries.

Validated SIF hashes identify retained archives, not public OCI digests. The
pipeline selects each local SIF by stage and verifies its hash; it never silently
pulls `latest`. New source-restoration recipes are unbuilt and need exact external
archives plus numerical validation. Public automatic image retrieval, a complete
public rebuild from scratch, Docker execution and cross-host portability are not
established. See [runtime installation](public_relatedness/environments/README.md).

## Development checks and publication

```bash
PYTHONDONTWRITEBYTECODE=1 PUBLIC_NEXTFLOW=nextflow \
  python -m unittest discover -s public_relatedness/tests -v
python verify_release.py --commit HEAD --require-ready
```

The exact [allowlist](RELEASE_FILES.txt) and [SHA256 manifest](RELEASE_SHA256SUMS.txt)
cover the source snapshot. [LICENSE](LICENSE) covers project code;
[upstream MIT notice](public_relatedness/vendor/breakclone/LICENSE) accompanies
the recovered matcher. Preserve [contributors](AUTHORS.md) and
[third-party notices](THIRD_PARTY_NOTICES.md). External code/data/images retain
their own terms. [Publication instructions](PUBLISHING.md) require a separate
publication instruction; v0.1.0 is never retagged or force-pushed.

## Acknowledgements

This pipeline incorporates and adapts components originally developed by the Huntsman group, including workflows for sequencing-read trimming, alignment, duplicate marking, and QDNAseq copy-number analysis.

We acknowledge the contributions of Maxwell Douglas, Ding Ma, Sheila Nicholson, Branden Lynch, and other contributors to the original pipeline.

The tumour-relatedness analysis and public workflow integration were subsequently developed and extended at Canada’s Michael Smith Genome Sciences Centre.
