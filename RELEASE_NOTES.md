# v0.1.1 — Development candidate

Local Phase 5 source-packaging candidate for NasoLab/swgs-relatedness. No push,
new tag or GitHub release has been performed. Published v0.1.0 is unchanged.
End-to-end and cross-host validation remain pending.

## Included scientific source

The PCC/LLR runner and recovered MIT breakpoint matcher are bundled byte-for-byte.
Four internal Huntsman preprocessing expressions and seven production Python
functions are extracted without AST changes; cohort/workbook/old-output drivers
are omitted. scientific_sources.json records original and packaged hashes
separately. Existing adapters, scientific parameters, PFREQ identity, pair order,
seed placement and sequential random-number consumption are preserved. The MIT
matcher includes copyright 2022 The Authors and its full upstream license.

Normal run-params.json now has only sample manifest, pair manifest,
resource_directory and outdir. Bundled source resolves from the repository or
Nextflow project directory. Explicit overrides are advanced and checksum locked.
Standalone/cached scoring and preflight use the same default source locations.

## External setup and runtimes

An opt-in setup command acquires the exact public PFREQ/helper sources and checks
their frozen hashes, or verifies an existing resource directory. Wrong or partial
downloads are not published and existing assets are not overwritten. FASTA gzip
acquisition is supported with decompressed-hash verification. Existing hg38
BWA-MEM2 sidecars and the PE150 annotation must still be supplied; neither is
regenerated or replaced. The modified GPL-3-derived LLR helper remains outside
Git until its modification terms are established; no scientific substitute is
introduced. QDNAseq.dev and reference redistribution limits remain documented.

Nextflow selects the separate trimming, alignment, Picard, QDNAseq/CGHcall and
metrics SIFs by recorded identity. Missing/changed images stop execution. Mutable
registry tags are never silently retrieved; original OCI digests are unknown.
Separate-prefix source-restoration and combined runtime recipes are supplied but
remain unbuilt/unvalidated and require missing external archives/source receipts.
They do not establish a complete public rebuild or cross-host portability.

## Validation

Fresh cached gates using the bundled source in the checksum-verified isolated
metrics SIF passed **PCC 66/66**, **seeded LLR 62/62** and **historical breakpoint
38/38** exact counts and supplied fraction precision. PCC maximum absolute
difference was 4.996003610813204e-16; LLR was 4.973799150320701e-14 (tolerance 1e-12).
Missing cohort members were rejected and pair orientation/output schemas checked.
The R extraction is AST-identical; runner/matcher original byte hashes are intact.
Fixture hashes, model parameters and numerical tolerances are unchanged.

The expanded lightweight suite passed **55 tests with one optional historical
test skipped**; all six Nextflow stubs passed, including a final recheck of
cohort-only execution without the pair model/helper. Six synthetic R matching
checks and seven R cohort-structure checks passed. The suite covers automatic lookup from another working
directory, minimal resource-only Nextflow stubs, negative process failures,
checksum/overwrite handling and actionable missing-resource errors. Final counts
and public-release audit evidence are in verification/release_tests.json.
No FASTQ alignment, full calling, large sequencing analysis, original output
mutation or image publication is part of these checks.

Project MIT licensing, the exact Huntsman acknowledgement, original contributor
credits and third-party terms are preserved. The candidate retains independent
clean release ancestry; the old research fork is not a publication source.
