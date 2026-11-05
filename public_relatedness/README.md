# Public workflow — v0.1.0 development

Read the [root README](../README.md), [installation](INSTALL.md),
[metric contracts](METRIC_ADAPTERS.md), [reference manifest](references/README.md)
and [licensing status](LICENSING.md). End-to-end validation remains pending.

Use the exact three-column TSV headers in [samples.tsv](examples/samples.tsv)
and [pairs.tsv](examples/pairs.tsv). IDs use letters, digits, underscores and
hyphens; reads are paired-end without CROP:50. Relative read paths resolve
against the sample manifest. One mate pair per sample is required; prepare
multi-lane inputs separately. The complete cohort is called once and its input
sample order is checked before scoring. Original pair orientation and order are
retained. Multiple comparisons may involve the same sample.

The legacy scientific runner is not included: supply `pcc_llr_runner` pointing to
an independently authorized file matching its frozen hash. This is required even
for cohort-only execution because the inherited QC adapter loads that runner.
PCC, LLR, historical preprocessing/matching and PFREQ are not replaced with
alternative scientific implementations. Additional frozen resources are required
when pairs are supplied. The [parameter template](examples/run-params.json)
lists all paths.

Outputs are `sample_results.tsv`, `pair_results.tsv` and metric provenance, plus
alignment, copy-number and calling outputs. Scores retain 17-digit numeric
precision; fractions include a rational representation. Unsupported both-zero
or negative-private breakpoint cases retain their counts and explicit status.
No new relatedness classifications or QC thresholds are introduced.

For authorized cached objects, use `-entry CACHED_METRICS` and supply
`called_rds`, `validated_samples`, `validated_pairs`, `pcc_llr_runner`, frozen
resources and the validated runtimes. This mode does not run alignment or calling.

## Lightweight verification

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s public_relatedness/tests -v
PUBLIC_NEXTFLOW=nextflow PYTHONDONTWRITEBYTECODE=1 \
  python -m unittest discover -s public_relatedness/tests -p test_nextflow.py -v
```

Stub tests create tiny artificial markers; they perform no sequencing or
scientific computation. Their outputs must remain `stub_not_computed`/NA.

## Authorized numerical regression inputs

Historical profiles, observation tables and fixtures are not distributed. For
an operator with separate permission, copy [cached_regression.json](examples/cached_regression.json)
to a private file and provide the exact authorized resources, then run:

```bash
python public_relatedness/tests/cached_regression.py \
  --config /path/to/private_regression.json --output /path/to/new_regression_output
```

This checks frozen fixture hashes, the ordered 62-pair LLR loop, 66 PCC values,
38 historical breakpoint cases, cohort membership, pair orientation, precision
and output schemas. The optional local observation-only test also accepts
`PUBLIC_HISTORICAL_CONFIG` plus `PUBLIC_HISTORICAL_REGRESSION=1` when its external
`observations` and `availability` tables are authorized and supplied. No fixture
may be copied into a public commit merely to make this test runnable.
