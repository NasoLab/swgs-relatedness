# Public workflow — v0.1.1 development candidate

Read the [root README](../README.md), [installation](INSTALL.md),
[metric contract](METRIC_ADAPTERS.md) and [source provenance](scientific_sources.json).
End-to-end and cross-host validation remain pending.

The normal [run configuration](examples/run-params.json) contains only sample
manifest, pair manifest, resource_directory and outdir. Manifest formats remain
unchanged; multiple comparisons may reuse a sample. Pair row order/orientation
and full-cohort membership are preserved. Bundled source paths resolve from the
pipeline directory, not the launch directory. A resource directory may also be
selected by SWGS_RESOURCE_DIR. Optional explicit reference/source/executable
locations are documented in [advanced.config](examples/advanced.config).

The runner is required even for cohort-only sample QC and is now automatic.
The preprocessing and Python core contain only exact expressions/functions used
by existing adapters. The third-party matcher includes its upstream MIT notice.
The inherited modified LLR helper remains external, acquired from its exact
public source and checked against its existing hash. No new scientific method,
classification threshold, package upgrade or model is introduced.

Outputs are sample_results.tsv, pair_results.tsv and native provenance, with
17-digit numeric score precision and an exact rational fraction. Unsupported
both-zero and negative-private cases remain explicit; missing samples fail.
Stub output metrics are NA/stub_not_computed and are not biological fixtures.

## Lightweight checks

```bash
PYTHONDONTWRITEBYTECODE=1 PUBLIC_NEXTFLOW=nextflow \
  python -m unittest discover -s public_relatedness/tests -v
```

The tests create synthetic markers only. No FASTQ alignment or real calling is
performed. Source lookup is exercised from a different working directory and
Nextflow stubs use a resource directory without any source-path arguments.

## Authorized cached regression checks

Historical profiles and fixtures are not redistributed. Copy the
[cached regression template](examples/cached_regression.json) to private storage,
provide authorized called objects/fixtures and the separate validated R runtimes,
then run:

```bash
python public_relatedness/tests/cached_regression.py \
  --config /path/to/private-regression.json --output /path/to/new-regression-output
```

Bundled source paths are automatic here too. Only the external helper/PFREQ
require supplied resources or resource_directory. The harness checks frozen
fixture hashes, all 66 PCC values, the original seeded ordered 62-pair LLR loop,
all 38 historical breakpoint cases, cohort/pair ordering, missing samples and
output schemas. The optional observation-only test remains available with
PUBLIC_HISTORICAL_CONFIG and PUBLIC_HISTORICAL_REGRESSION=1. Historical fixture
SHA256 values and numerical tolerances are unchanged.

For a cached Nextflow run use `-entry CACHED_METRICS` with called_rds,
validated_samples, validated_pairs, resource_directory and a recorded runtime.
No alignment/calling is invoked. A null metrics_container selects the separate
host Rscript-llr/Rscript-general executables; explicit advanced overrides remain
available. The full FASTQ workflow requires validated local SIF selection.
