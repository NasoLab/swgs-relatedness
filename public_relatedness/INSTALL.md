# Installation — v0.1.0 — Development

End-to-end validation is pending. Cached numerical gates passed at the originating
checkpoint, but public source-restoration images have not been built/validated.
Project and external-component publication permissions remain unresolved.

## Software and references

Use Nextflow 24.10.3, a compatible Java runtime, Python >=3.9 and the appropriate
Apptainer/Singularity or Docker runtime. The recorded driver used Python 3.12.2,
Zulu Java 11.0.1+13-LTS and Apptainer 1.3.1-1. See the exact
[environment inventories](environments/README.md); keep the QDNAseq and historical
LLR stacks separate, with explicit metric executable selection. Do not upgrade
scientific packages to simplify installation or infer versions from `latest`.

Supply authorized existing hg38 FASTA/BWA-MEM2 indexes and the hg38 PE150 500-kb
annotation. No PE50 substitute is accepted. Required annotation SHA256:

```text
1d62a94b9a88845978c7bf709d00b35b0f3b1243ef894b442c3ac2861a23337c
```

The [reference manifest](references/manifest.json) records all frozen identities;
[acquisition notes](references/README.md) explain gaps. No reference is downloaded,
regenerated or bundled. Obtain separate rights for all external code/models.
The legacy `run_pcc_llr.R` is intentionally external: set `pcc_llr_runner` to the
permission-cleared source with SHA256
`411676813fde9d1f3bd2b74fe08a59970a060e5bff564b561264c7a35b2ea15f`.
Additional pair resources are PFREQ, inherited LLR helper, historical breakpoint
preprocessing, recovered matcher and historical Python fraction implementation.
All existing metric hashes are preserved and checked before scoring.

## Private configuration and storage

Copy [run-params.json](examples/run-params.json) outside the repository. Replace
every placeholder with your own authorized input/resource/runtime path. Supply
fresh `outdir`, explicit sample/pair manifests and the frozen runner. A null
`metrics_container` uses the explicitly selected host R executables. A metrics
image must contain the separate validated LLR and general R library trees plus
Python; internal snapshots are not distributed or licensed by this repository.

Create a writable `temp_directory`, for example `/mnt/swgs/tmp`, before launch.
Only letters, digits, slashes, dots, underscores and hyphens are supported in
that path because of the Nextflow 24.10 scratch launcher. The workflow exports
TMPDIR, uses the directory for upstream task scratch/tool temporary files and
binds it read/write at the same absolute path inside the container. Omission
retains `/tmp`. Select Nextflow intermediates separately with `-work-dir
/mnt/swgs/work` and published results with `outdir`. On Slurm, confirm these
paths and worker permissions independently. The setting does not allocate a
volume or mount a host disk. Set APPTAINER_TMPDIR/APPTAINER_CACHEDIR separately
for image extraction/build caches on suitable storage.

## Check and run

Use approved local byte-identical image archives with
[pinned-images.config](examples/pinned-images.config). Their historical filenames
are checked by SHA256; tags are not resolved. Run preflight first:

```bash
python public_relatedness/bin/validate_setup.py \
  --params /path/to/private_run_params.json --profiles singularity --check-images
```

`--metadata-only` checks structure/presence only and is not content verification.
Preflight does not establish biological validity or end-to-end reproducibility.

```bash
nextflow -C public_relatedness/nextflow.config,public_relatedness/examples/pinned-images.config,public_relatedness/examples/isolated-execution.config \
  run public_relatedness/main.nf -profile singularity \
  -params-file /path/to/private_run_params.json -work-dir /mnt/swgs/work
```

`-C` excludes historical/default configuration. The isolated execution example
serializes stages and disables optional trace/report/timeline monitoring: the
retained Picard image's uutils date returns 19 rather than 13 timestamp digits
for the Nextflow 24.10 wrapper. No scientific image or utility is replaced.
Nextflow logs, task exit codes and native metric provenance remain available.
If site options override container runOptions, preserve the temp_directory bind.

`local`, `singularity`, `docker` and `slurm` profiles are declared; select a
container runtime for FASTQ execution. Docker/Slurm execution has not been
validated here. The SIF pinning example is for Apptainer/Singularity; Docker
requires permission-cleared OCI images and verified digests. Never run production
sequencing using stub outputs or treat the unbuilt recipes as validated images.
