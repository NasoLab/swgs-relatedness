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
their frozen hashes, or verifies an existing resource directory. FASTA gzip
acquisition verifies decompressed bytes. Existing hg38 indexes and the PE150
annotation remain required external assets and are not regenerated.

`prepare_runtimes.py` now acquires the unchanged hosted metrics SIF from the
publisher's HTTPS URL with mandatory SHA256 verification. Valid cached files are
reused; mismatches are not overwritten; an existing same-filesystem SIF can be
verified and hard-linked without another copy. The resource-directory metrics
cache is selected automatically. Four public upstream images are selected by
immutable Linux/amd64 OCI manifests; exact retained local archive overrides remain
supported. Original SIF hashes and OCI identities are recorded separately.
Runtime and temporary-volume settings are evaluated after configuration merging.

The metrics task copies its small inputs to reduce source binds, and an added
runtime guard rejects host mounts hiding the SIF's embedded R libraries. Its
metadata checks use separate R processes and do not alter scoring RNG consumption.
Keep clone/resources/work under a narrow operational workspace. The original
absolute R prefixes remain embedded; cross-host portability is not established.

The source-restoration recipes remain unbuilt/unvalidated and their missing
archives/license receipts remain unresolved. Hosting an image does not change
its dependencies' terms. No image/reference payload is committed or published by
these source changes, and no scientific algorithm, parameter or R package version
is changed.

## Validation

Fresh cached gates using the bundled source in the checksum-verified isolated
metrics SIF passed **PCC 66/66**, **seeded LLR 62/62** and **historical breakpoint
38/38** exact counts and supplied fraction precision. PCC maximum absolute
difference was 4.996003610813204e-16; LLR was 4.973799150320701e-14 (tolerance 1e-12).
Missing cohort members were rejected and pair orientation/output schemas checked.
The R extraction is AST-identical; runner/matcher original byte hashes are intact.
Fixture hashes, model parameters and numerical tolerances are unchanged.

The initial Phase 5 lightweight suite passed **55 tests with one optional historical
test skipped**; all six Nextflow stubs passed, including a final recheck of
cohort-only execution without the pair model/helper. Six synthetic R matching
checks and seven R cohort-structure checks passed. The suite covers automatic lookup from another working
directory, minimal resource-only Nextflow stubs, negative process failures,
checksum/overwrite handling and actionable missing-resource errors. Final counts
and public-release audit evidence are in verification/release_tests.json.
No FASTQ alignment, full calling, large sequencing analysis, original output
mutation or image publication is part of these checks.

The final documentation checkpoint retains the root Quick Start, removes obsolete
permission/user-supplied claims for bundled sources and documents generic error
limitations. Standalone preflight now includes missing file paths and setup
guidance. Four additional checks cover missing FASTA, annotation, index and image
archives. The final suite passed **59 tests with one optional historical test
skipped**, including all six Nextflow stubs. Documentation links, shell examples
and runtime configuration parsing passed. Scientific implementations, parameters,
reference identities and regression fixtures are unchanged; the numerical gates
above were not rerun for these documentation/error-message changes.

Runtime integration verification passed the full 66/62/38 cached gates again,
all seven lightweight Nextflow tests and a 13-task real-image stub graph. A
production cached Nextflow comparison selected the resource-cache SIF automatically,
passed the library mount guard and matched the fresh full-loop first pair exactly.
An actual broad read-only host bind was rejected before scoring. The expanded
suite passed 75 tests with one optional historical test skipped. These checks do
not constitute full FASTQ/QDNAseq/CGHcall or independent-host validation.

Project MIT licensing, the exact Huntsman acknowledgement, original contributor
credits and third-party terms are preserved. The candidate retains independent
clean release ancestry; the old research fork is not a publication source.
