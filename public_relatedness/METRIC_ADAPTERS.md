# Relatedness metric adapters — development implementation

`PUBLIC_METRICS` connects complete-cohort CGHcall to `SCORE_AND_AGGREGATE`.
One Nextflow task runs two configurable R runtimes sequentially and writes
`sample_results.tsv`, `pair_results.tsv` and metric provenance. Pair IDs,
manifest row order and sample1/sample2 orientation are retained throughout.
The complete manifest cohort is required, including samples in no comparisons.
No alignment, normalization or calling occurs in the cached scoring entry point.

## PCC and LLR

`bin/pcc_llr_adapter.R` parses the unchanged
the operator-supplied, checksum-pinned `pcc_llr_runner` (`run_pcc_llr.R`), evaluates its original imports and
function definitions, and stops before its standalone CLI driver. It calls the
original `validate_called_rds`, `read_pair_metadata`, `make_segment_long`,
`compute_pcc`, `prepare_llr` and `compute_llr` functions. The full source checksum
is pinned; a changed implementation requires an explicit version review.

PCC retains QDNAseq usable-bin selection, segmented values rounded to three
decimals, log2 transformation and Pearson correlation in the original pair
orientation. No alternate profile representation or correlation is introduced.
The called-object guard also retains the inherited requirement for high-level
CGHcall states; cohorts failing that guard stop explicitly.

LLR retains the frozen TCGA LUSC PFREQ model, inherited
`clonality.analysis.mod`, `QDNAseq.dev::clonalityTest`, chromosome-arm splitting,
chr21p exclusion, chromosome ordering and model defaults. The adapter runs
`set.seed(1337)` once after helper/PFREQ loading and immediately before the
original sequential pair loop. There are no per-pair seeds, pair tasks,
parallel scoring or retries. Unavailable LLR packages/models fail the task;
per-pair failures become explicit result statuses.

The seeded regression requires the existing R 4.3.3 environment with
Clonality 1.47.0, QDNAseq.dev 0.1, QDNAseq 1.36.0 and DNAcopy 1.74.1.
Use `--metrics_rscript` to select it. Runtime `sessionInfo()` and RNG kind are
published. These recorded versions are not a newly built portable environment.
The public result tables omit the legacy runner's classification columns;
no new thresholds or classification rules are introduced.

## Historical breakpoint fraction_shared

`bin/breakpoints_adapter.R` loads operator-supplied, checksum-pinned sources.
It evaluates only `rcn_cohort_segs`, `rcn_cohort_calls`, `rcn_cohort_collapse`
and `df_cohort` assignments from historical preprocessing revision
`39a918d2a38a30cc78a90a51a314b7ef83a7813d`, using the entire manifest as
`combined_metadata_usable`. It does not run historical file reads, QC-population
selection, external cohorts, plotting or calling. Export precision, usable-bin
selection, collapsed segments, non-neutral call mapping and boundary extraction
remain the recovered implementation, including `utanos` functions.

The recovered `getHit` and `calculateMaxGap` functions come from matching
revision `712eb202303119588ca10889ca92a721afd0c396`. Only those definitions are
loaded; frequency-weighted scorers are never executed. The modal-bin-derived
tolerance must equal 2,500,000 bp. The supplied Python reconstruction module
`regress_fraction_shared.py` is imported without running its CLI. Its original
`group_observations` and `counts` functions independently score the extracted
observations, and **every pair's counts must agree exactly with recovered R**.
Any discrepancy fails the task before final tables are written.

Matching requires the same chromosome, DUP/DEL direction and start/end boundary
type, within an inclusive 2.5-Mb tolerance. Every eligible overlap counts,
including multiple hits per boundary. With counts nA/nB and overlap count H:

```text
shared = H
private_sample1 = nA - H
private_sample2 = nB - H
total = nA + nB - H
fraction_shared = H / total
```

Both-zero cases produce `unsupported_both_zero`; negative private counts produce
`unsupported_negative_private`. Raw counts are retained and the fraction is
`NA`; no clamp, new denominator or replacement score is used. One present zero
profile paired with a nonzero profile remains a supported zero fraction.
Missing profiles fail the exact cohort guard and are never treated as zero.
Breakpoint Dice, greedy matching and BreakClone `pair_score` are not used.

`utanos` is available in the existing general R environment, separately from
the seeded LLR environment. Use `--breakpoint_rscript` for that executable.
The tested utanos version is 0.1.0.9000, RemoteSha
`ae8edc6464ab7bac0939a886dd7f8beae7a7410b`.

## Resources, precision and statuses

All six authority hashes are in `bin/run_metrics.py::HASHES`, including the
unchanged PCC/LLR runner. Supply these external assets explicitly:

| Parameter | Frozen resource |
| --- | --- |
| `--pfreq` | `pfreq_lusc_tcga_split.csv` |
| `--llr_helper` | `clonality_analysis_PFREQ_MOD.R` |
| `--breakpoint_preprocessing` | Complete historical `test_relatedness_cohort_qc_pass.R` at the revision above |
| `--breakpoint_matching` | Recovered `breakclone_copynumber_712eb202.R` |
| `--fraction_implementation` | Validated `regress_fraction_shared.py` reconstruction |

These are code/model inputs, not patient metadata. No third-party source, model or historical fixture is bundled in this snapshot. Public acquisition and
redistribution permission remain release blockers. All assets are checked
before metric computation; supplied paths are staged into the task.

R exports metric doubles with 17 significant digits; Python carries these
strings unchanged into final TSVs. Fractions also include an exact rational
column. Original three-decimal PCC preprocessing remains unchanged.
`processing_status` is `complete`, `failed_metrics` or
`unsupported_fraction_shared`, with separate PCC/LLR/fraction status columns.
`sample_results.tsv` reports processing completion, raw usable/finite-bin counts,
call states, profile location/hash and provenance. `qc_status=not_assessed`
explicitly avoids claiming a new QC pass/fail policy. Structural failures stop
the workflow; per-pair metric failures remain visible in tables/provenance.

A cohort-only run produces sample results and a header-only pair table. Stub
runs produce `NA` metrics and `stub_not_computed` statuses exclusively.
Cached gate evidence is recorded in [the release notes](../RELEASE_NOTES.md).
